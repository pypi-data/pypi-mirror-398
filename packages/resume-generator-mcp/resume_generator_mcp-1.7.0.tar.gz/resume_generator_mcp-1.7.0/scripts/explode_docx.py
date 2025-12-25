import zipfile
import os
from pathlib import Path

def explode_docx(docx_path, output_dir):
    # Create the output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Open the .docx file as a zip archive
    with zipfile.ZipFile(docx_path, 'r') as docx:
        # Extract all contents to the output directory
        docx.extractall(output_dir)

    print(f"DOCX file exploded successfully into: {output_dir}")

# Usage
docx_file = 'resume.docx'
output_directory = 'resume'

explode_docx(docx_file, output_directory)