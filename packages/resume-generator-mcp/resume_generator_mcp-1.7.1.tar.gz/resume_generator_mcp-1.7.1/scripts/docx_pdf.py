import sys
from docx2pdf import convert
import os

def convert_docx_to_pdf(input_file):
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found.")
        return

    # Generate output file name
    output_file = os.path.splitext(input_file)[0] + '.pdf'

    try:
        # Convert DOCX to PDF
        convert(input_file, output_file)
        print(f"Successfully converted '{input_file}' to '{output_file}'")
    except Exception as e:
        print(f"Error converting file: {str(e)}")

if __name__ == "__main__":
    # Check if the DOCX file name is provided as an argument
    if len(sys.argv) != 2:
        print("Usage: python docx_to_pdf.py <docx_file>")
        sys.exit(1)

    docx_file = sys.argv[1]
    convert_docx_to_pdf(docx_file)