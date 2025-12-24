# Universal Pandoc GUI Converter

A lightweight, platform-independent desktop application that provides a graphical user interface (GUI) for the [Pandoc](https://pandoc.org/) universal document converter. Built with Python's standard `tkinter` library, this tool allows users to convert documents between dozens of formats without using the command line.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

## Features

*   **Zero Dependencies**: Uses standard Python libraries (`tkinter`, `subprocess`, `threading`). No `pip install` required for the script itself.
*   **Platform Independent**: Works seamlessly on Windows, macOS, and Linux.
*   **Dynamic Format Detection**: Automatically queries your installed version of Pandoc to populate input and output formats (supports `docx`, `pdf`, `html`, `markdown`, `latex`, `epub`, and more).
*   **Non-Blocking UI**: Runs conversions in a background thread so the interface remains responsive during large file operations.
*   **Scrollable Log**: Built-in status console to view conversion details and error messages.

## Prerequisites

1.  **Python 3.12+**: Ensure Python is installed on your system.
2.  **Pandoc**: The application relies on the `pandoc` command-line tool.
    *   **Windows**: `winget install pandoc` or download from [pandoc.org](https://pandoc.org/installing.html)
    *   **macOS**: `brew install pandoc`
    *   **Linux**: `sudo apt-get install pandoc`

## Installation & Usage

### Running from Source
1.  Clone the repository:
    ```
    git clone https://github.com/yourusername/pandoc-gui.git
    cd pandoc-gui
    ```
2.  Run the script:
    ```
    python gui.py
    ```

### Install pandoc-gui directly
If you want to use pandoc-gui directly:

1.  Install pandoc-gui:
    ```
    pip install pandoc-gui
    ```
2.  Build the executable:
    ```
    pandoc_gui
    ```

## How to Use

1.  **Launch the App**: Open the application via Python or the executable.
2.  **Select File**: Click "Browse..." to choose the document you want to convert.
3.  **Select Format**: 
    *   *From Format*: Leave as "Auto-detect" (recommended) or specify manually.
    *   *To Format*: Select your desired output format (e.g., `pdf`, `docx`).
4.  **Convert**: Click "Convert Document". The status log will update when the process is complete.
5.  **Output**: The converted file is saved in the same directory as the original input file.

## Troubleshooting

*   **"Pandoc not found"**: Ensure Pandoc is installed and added to your system's PATH. Restart the application after installing Pandoc.
*   **PDF Conversion Errors**: Converting to PDF via Pandoc requires a PDF engine (like `pdflatex` or `wkhtmltopdf`). If you receive an error, ensure you have a LaTeX distribution (like MiKTeX or TeX Live) installed.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

