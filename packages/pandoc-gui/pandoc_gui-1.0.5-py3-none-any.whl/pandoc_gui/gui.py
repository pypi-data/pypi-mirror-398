import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import threading
import shutil
import os
import sys

class PandocConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Universal Document Converter (Pandoc GUI)")
        self.root.geometry("500x400")

        # Use 'clam' theme on non-Mac systems for a cleaner look.
        style = ttk.Style()
        style.theme_use('clam')

        # State variables
        self.input_file_path = tk.StringVar()
        self.output_format = tk.StringVar()
        self.input_format = tk.StringVar(value="Auto-detect")
        
        # Check for Pandoc
        self.pandoc_path = shutil.which("pandoc")
        
        self.create_widgets()
        self.load_formats()

    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="20 20 20 20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Input Section ---
        input_group = ttk.LabelFrame(main_frame, text="Input", padding="10 10 10 10")
        input_group.pack(fill=tk.X, pady=5)

        # File Row
        file_row = ttk.Frame(input_group)
        file_row.pack(fill=tk.X, pady=5)
        
        self.entry_file = ttk.Entry(file_row, textvariable=self.input_file_path)
        self.entry_file.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        btn_browse = ttk.Button(file_row, text="Browse...", command=self.browse_file)
        btn_browse.pack(side=tk.RIGHT)

        # Format Row
        fmt_in_row = ttk.Frame(input_group)
        fmt_in_row.pack(fill=tk.X, pady=5)
        
        ttk.Label(fmt_in_row, text="From Format:").pack(side=tk.LEFT, padx=(0, 10))
        self.combo_input = ttk.Combobox(fmt_in_row, textvariable=self.input_format, state="readonly", width=15)
        self.combo_input.pack(side=tk.LEFT)

        # --- Output & Action Section ---
        output_group = ttk.LabelFrame(main_frame, text="Output", padding="10 10 10 10")
        output_group.pack(fill=tk.X, pady=10)

        action_row = ttk.Frame(output_group)
        action_row.pack(fill=tk.X)

        ttk.Label(action_row, text="To Format:").pack(side=tk.LEFT)
        self.combo_output = ttk.Combobox(action_row, textvariable=self.output_format, state="readonly", width=15)
        self.combo_output.pack(side=tk.LEFT, padx=(10, 20))

        # Convert Button (standard ttk button matches system theme)
        self.btn_convert = ttk.Button(action_row, text="Convert Document", command=self.start_conversion)
        self.btn_convert.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # --- Status Section ---
        status_group = ttk.LabelFrame(main_frame, text="Status Log", padding="10 10 10 10")
        status_group.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        # Frame for Text + Scrollbar
        txt_frame = ttk.Frame(status_group)
        txt_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(txt_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Standard Text widget with default font
        self.txt_status = tk.Text(txt_frame, height=8, width=50, state='disabled',
                                  yscrollcommand=scrollbar.set)
        self.txt_status.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=self.txt_status.yview)

        # Progress Bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        
        self.log_message("Ready.")

    def log_message(self, message):
        self.txt_status.config(state=tk.NORMAL)
        self.txt_status.insert(tk.END, message + "\n")
        self.txt_status.see(tk.END)
        self.txt_status.config(state=tk.DISABLED)

    def load_formats(self):
        if not self.pandoc_path:
            self.log_message("Error: Pandoc not found in system path.")
            self.btn_convert.config(state=tk.DISABLED)
            return

        try:
            # Inputs
            in_res = subprocess.run([self.pandoc_path, "--list-input-formats"], capture_output=True, text=True)
            inputs = in_res.stdout.strip().splitlines()
            inputs.insert(0, "Auto-detect")
            self.combo_input['values'] = inputs
            self.combo_input.current(0)
            
            # Outputs
            out_res = subprocess.run([self.pandoc_path, "--list-output-formats"], capture_output=True, text=True)
            outputs = out_res.stdout.strip().splitlines()
            self.combo_output['values'] = outputs
            
            if "docx" in outputs:
                self.combo_output.set("docx")
            elif outputs:
                self.combo_output.current(0)
                
        except Exception as e:
            self.log_message(f"Error loading formats: {e}")

    def browse_file(self):
        filename = filedialog.askopenfilename()
        if filename:
            self.input_file_path.set(filename)
            self.log_message(f"Selected: {filename}")

    def start_conversion(self):
        input_path = self.input_file_path.get()
        output_fmt = self.output_format.get()
        input_fmt = self.input_format.get()

        if not input_path:
            messagebox.showwarning("Warning", "Please select a file.")
            return
        if not output_fmt:
            messagebox.showwarning("Warning", "Please select an output format.")
            return

        base, _ = os.path.splitext(input_path)
        output_path = f"{base}.{output_fmt}"
        
        self.btn_convert.config(state=tk.DISABLED)
        self.progress.pack(fill=tk.X, pady=(10, 0))
        self.progress.start(10)
        self.log_message(f"Converting to {output_fmt}...")
        
        self.root.update_idletasks()

        thread = threading.Thread(target=self.run_pandoc, args=(input_path, output_path, input_fmt, output_fmt))
        thread.daemon = True
        thread.start()

    def run_pandoc(self, infile, outfile, infmt, outfmt):
        try:
            cmd = [self.pandoc_path, infile, "-o", outfile]
            if infmt != "Auto-detect":
                cmd.extend(["-f", infmt])
            cmd.extend(["-t", outfmt])
            cmd.append("-s")

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                self.root.after(0, lambda: self.conversion_complete(True, outfile))
            else:
                self.root.after(0, lambda: self.conversion_complete(False, result.stderr.strip()))

        except Exception as e:
            self.root.after(0, lambda: self.conversion_complete(False, str(e)))

    def conversion_complete(self, success, payload):
        self.progress.stop()
        self.progress.pack_forget()
        self.btn_convert.config(state=tk.NORMAL)
        
        if success:
            self.log_message(f"SUCCESS: Saved to {payload}")
            messagebox.showinfo("Success", "Conversion successful!")
        else:
            self.log_message(f"FAILED: {payload}")
            messagebox.showerror("Error", "Conversion failed.")

if __name__ == "__main__":
    root = tk.Tk()
    app = PandocConverterApp(root)
    root.mainloop()



def main():
    root = tk.Tk()
    app = PandocConverterApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
