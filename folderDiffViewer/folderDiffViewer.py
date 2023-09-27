import difflib
import os
from jinja2 import Template

def compare_folders(folder1_path, folder2_path):
    differ = difflib.Differ()
    changed_files = {'folder_one': {}, 'folder_two': {}}

    for root, dirs, files in os.walk(folder1_path):
        relative_path = os.path.relpath(root, folder1_path)

        folder2_root = os.path.join(folder2_path, relative_path)
        if not os.path.exists(folder2_root):
            # Folder exists in folder1 but not in folder2
            changed_files['folder_one'][relative_path] = {'added': [], 'removed': []}
            continue

        for file in files:
            file1_path = os.path.join(root, file)
            relative_file_path = os.path.join(relative_path, file)
            file2_path = os.path.join(folder2_path, relative_file_path)

            if os.path.exists(file2_path):
                try:
                    with open(file1_path, 'r', encoding='utf-8') as file1, open(file2_path, 'r', encoding='utf-8') as file2:
                        file1_content = file1.readlines()
                        file2_content = file2.readlines()

                    # Calculate the differences between file contents
                    differ = difflib.Differ()
                    diff = list(differ.compare(file1_content, file2_content))

                    # Check if there are differences
                    if any(line.startswith('- ') or line.startswith('+ ') for line in diff):
                        if relative_path not in changed_files['folder_one']:
                            changed_files['folder_one'][relative_path] = {'added': [], 'removed': []}
                        changed_files['folder_one'][relative_path]['added'].append(file)
                except UnicodeDecodeError as e:
                    print(f"Skipping file due to encoding error: {file1_path} - {e}")
                    continue
                except Exception as e:
                    print(f"Error reading file: {file1_path} - {e}")
            else:
                # File exists in folder1 but not in folder2
                if relative_path not in changed_files['folder_one']:
                    changed_files['folder_one'][relative_path] = {'added': [], 'removed': []}
                changed_files['folder_one'][relative_path]['removed'].append(file)

    for root, dirs, files in os.walk(folder2_path):
        relative_path = os.path.relpath(root, folder2_path)

        folder1_root = os.path.join(folder1_path, relative_path)
        if not os.path.exists(folder1_root):
            # Folder exists in folder2 but not in folder1
            changed_files['folder_two'][relative_path] = {'added': [], 'removed': []}
            continue

        for file in files:
            file2_path = os.path.join(root, file)
            relative_file_path = os.path.join(relative_path, file)
            file1_path = os.path.join(folder1_path, relative_file_path)

            if not os.path.exists(file1_path):
                # File exists in folder2 but not in folder1
                if relative_path not in changed_files['folder_two']:
                    changed_files['folder_two'][relative_path] = {'added': [], 'removed': []}
                changed_files['folder_two'][relative_path]['added'].append(file)

    return changed_files

def generate_html_report(changed_files):
    template = Template(
        """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Folder and File Differences</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    overflow-x: hidden; /* Hide horizontal overflow */
                }
                .container {
                    display: flex;
                }
                .folder {
                    flex: 1;
                    padding: 10px;
                    border: 1px solid #ddd;
                    max-width: 50%;
                }
                .added {
                    background-color: #e6ffe6;
                }
                .removed {
                    background-color: #ffe6e6;
                }
                pre {
                    white-space: pre-wrap;
                }
            </style>
        </head>
        <body>
            <h1>Folder and File Differences</h1>
            <div class="container">
                <div class="folder">
                    <h2>Folder One</h2>
                    <pre>{{ folder_one_tree }}</pre>
                </div>
                <div class="folder">
                    <h2>Folder Two</h2>
                    <pre>{{ folder_two_tree }}</pre>
                </div>
            </div>
        </body>
        </html>
        """
    )

    folder_one_tree = generate_file_tree(changed_files['folder_one'], 'folder_one_tree')
    folder_two_tree = generate_file_tree(changed_files['folder_two'], 'folder_two_tree')

    rendered_html = template.render(
        folder_one_tree=folder_one_tree,
        folder_two_tree=folder_two_tree
    )

    return rendered_html

def generate_file_tree(changed_files, id_prefix):
    tree = []

    def generate_folder_structure(folder_changes):
        folder_structure = []
        for folder, changes in folder_changes.items():
            folder_tree = [f'<b>{folder}</b>']
            if changes['added']:
                folder_tree.append('<ul><b>Added Files:</b>')
                for file in changes['added']:
                    folder_tree.append(f'<li class="added">{file}</li>')
                folder_tree.append('</ul>')
            if changes['removed']:
                folder_tree.append('<ul><b>Removed Files:</b>')
                for file in changes['removed']:
                    folder_tree.append(f'<li class="removed">{file}</li>')
                folder_tree.append('</ul>')
            if folder_changes[folder]:
                folder_structure.append(''.join(folder_tree))
            subfolder_changes = changes.get('subfolders')
            if subfolder_changes:
                folder_structure.append(generate_folder_structure(subfolder_changes))
        return folder_structure

    folder_structure = generate_folder_structure(changed_files)

    tree.append(''.join(folder_structure))

    return f'<div id="{id_prefix}">{"".join(tree)}</div>'

if __name__ == "__main__":
    folder1_path = input("Enter the full path to the first folder: ")
    while not os.path.exists(folder1_path):
        print("The first folder does not exist. Please enter a valid path.\n")
        folder1_path = input("Enter the full path to the first folder: ")

    folder2_path = input("Enter the full path to the second folder: ")
    while not os.path.exists(folder2_path):
        print("The second folder does not exist. Please enter a valid path.\n")
        folder2_path = input("Enter the full path to the second folder: ")

    changed_files = compare_folders(folder1_path, folder2_path)

    if changed_files:
        rendered_html = generate_html_report(changed_files)
        
        output_html_path = 'folder_comparison.html'
        try:
            with open(output_html_path, 'w') as output_file:
                output_file.write(rendered_html)
            print(f"HTML report generated: {output_html_path}")
        except Exception as e:
            print(f"Error writing HTML file: {e}")
    else:
        print("No differences found between the folders and files.")