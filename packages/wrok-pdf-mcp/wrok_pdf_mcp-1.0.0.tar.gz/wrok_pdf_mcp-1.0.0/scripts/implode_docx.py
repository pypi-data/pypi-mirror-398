import os
import zipfile
from pathlib import Path

def create_docx(source_dir, output_docx):
    # Create a ZipFile object
    with zipfile.ZipFile(output_docx, 'w', zipfile.ZIP_DEFLATED) as docx:
        # [Content_Types].xml MUST be the first file for valid DOCX
        content_types_path = os.path.join(source_dir, '[Content_Types].xml')
        if os.path.exists(content_types_path):
            docx.write(content_types_path, '[Content_Types].xml')

        # Walk through all files and subdirectories in the source directory
        for root, _, files in os.walk(source_dir):
            for file in files:
                # Skip [Content_Types].xml since we already added it
                if file == '[Content_Types].xml':
                    continue

                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_dir)

                # Ensure correct path separator for zip
                arcname = arcname.replace(os.path.sep, '/')

                # Add file to zip
                docx.write(file_path, arcname)

    print(f"DOCX file created successfully: {output_docx}")

# Usage
source_directory = 'resume'
output_docx_file = 'resume_modified.docx'

create_docx(source_directory, output_docx_file)