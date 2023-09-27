import difflib
import webbrowser
from jinja2 import Template
import os

"""
example file paths
/Users/stevensongerardeustache/Library/Mobile Documents/com~apple~CloudDocs/Software Dev/git_clone/Reveal/Dreamers_Dev_Backend/app_backend/views.py
/Users/stevensongerardeustache/Library/Mobile Documents/com~apple~CloudDocs/Software Dev/git_clone/Reveal/Dreamers_Prod_Backend/app_backend/views.py
"""
# Prompt the user for file paths and names
file1_path = input("Enter the full path to the first file: ")
while not file1_path:
    print("You must enter a file path for the first file.\n")
    file1_path = input("Enter the full path to the first file: ")

file2_path = input("Enter the full path to the second file: ")
while not file2_path:
    print("You must enter a file path for the second file.\n")
    file2_path = input("Enter the full path to the second file: ")

file1_name = input("Enter a name for the first file (or press Enter for default 'File 1'): ") or "File 1"

file2_name = input("Enter a name for the second file (or press Enter for default 'File 2'): ") or "File 2"

# Read the contents of the two files
try:
    with open(file1_path, 'r') as file1:
        file1_content = file1.readlines()

    with open(file2_path, 'r') as file2:
        file2_content = file2.readlines()
except Exception as e:
    print(f"Error reading files: {e}")
    exit(1)

# Calculate the differences
differ = difflib.Differ()
diff = list(differ.compare(file1_content, file2_content))

# Check if there are no differences
if all(line.startswith('  ') for line in diff):
    print("\nNo differences between the files.")
    exit(0)
else:
    # Define the HTML template
    template = Template(
        """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Python File Diff Viewer</title>
        <style>
            body {
                font-family: Arial, sans-serif;
            }
            table {
                border-collapse: collapse;
                width: 100%;
                table-layout: fixed;
            }
            th, td {
                padding: 8px;
                text-align: left;
                vertical-align: top;
                border: 1px solid #ddd;
                word-wrap: break-word;
            }
            .added {
                background-color: #e6ffe6;
                font-weight: bold;
            }
            .removed {
                background-color: #ffe6e6;
                font-weight: bold;
            }
            .divider {
                border-left: 2px solid #ccc;
            }
        </style>
    </head>
    <body>
        <h1>Python File Differences</h1>
        <table>
            <thead>
                <tr>
                    <th>{{ file1_name }}</th>
                    <th>{{ file2_name }}</th>
                </tr>
            </thead>
            <tbody>     
                {% for line in diff %}
                <tr>
                    {% if line.startswith('- ') %}
                    <td class="removed">{{ line }}</td>
                    <td></td>
                        
                    {% elif line.startswith('+ ') %}
                    <td></td>
                    <td class="added">{{ line }}</td>
                    {% else %}
                        
                    <td>{{ line }}</td>
                    <td>{{ line }}</td>
                        
                    {% endif %}
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </body>
    </html>
    """)

    # Render the HTML with the differences
    rendered_html = template.render(diff=diff, file1_name=file1_name, file2_name=file2_name)

    # Save the HTML to a file
    output_html_path = 'diff_viewer.html'
    try:
        with open(output_html_path, 'w') as output_file:
            output_file.write(rendered_html)
    except Exception as e:
        print(f"Error writing HTML file: {e}")
        exit(1)

    # Open the HTML file in the default web browser
    try:
        webbrowser.open_new_tab("file:///" + os.path.abspath(output_html_path))
        exit(0)
    except Exception as e:
        print(f"Error opening web browser: {e}")
        exit(1)
