from setuptools import setup, find_packages

setup(
    name="pandoc_gui",  # This is the name used for 'pip install'
    version="1.0.4",
    author="Jian Tao",
    author_email="jtao@tamu.edu",
    description="('A Universal Pandoc GUI Converter',)",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/jtao/pandoc_gui",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.12',
    entry_points={
        'console_scripts': [
            # This allows the user to type 'pandoc_gui' in the terminal
            'pandoc_gui=pandoc_gui.gui:main',
        ],
    },
)
