import yaml
from jinja2 import Environment, FileSystemLoader
import os
import sys

# Check if the YAML file name is provided as an argument
if len(sys.argv) != 2:
    print("Usage: python process_template.py <yaml_file>")
    sys.exit(1)

yaml_file = sys.argv[1]

# Load the YAML data
try:
    with open(yaml_file, 'r') as file:
        resume_data = yaml.safe_load(file)
except FileNotFoundError:
    print(f"Error: File '{yaml_file}' not found.")
    sys.exit(1)

# Set up Jinja2 environment
env = Environment(loader=FileSystemLoader('.'))

# Load the template
template = env.get_template('doc_template_roles.xml')

# Render the template with the resume data
rendered_xml = template.render(resume_data)

# Save the rendered XML to a file
output_file = 'resume/word/document.xml'
with open(output_file, 'w', encoding='utf-8') as file:
    file.write(rendered_xml)

print(f"Resume XML generated successfully: {os.path.abspath(output_file)}")