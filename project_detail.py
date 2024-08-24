import os
import json
from pathlib import Path

class ReadableJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, FileContent):
            return obj.__dict__
        return super().default(obj)

class FileContent:
    def __init__(self, content):
        self.content = content
    
def should_exclude(path, exclude_list):
    # Normalize the path to use forward slashes
    norm_path = str(Path(path)).replace('\\', '/')
    return any(
        exclude.replace('\\', '/') in norm_path
        for exclude in exclude_list
    )

def generate_project_tree(root_dir, output_file, exclude_list):
    def tree(dir_path, prefix=""):
        contents = list(os.scandir(dir_path))
        folders = [item for item in contents if item.is_dir() and item.name not in exclude_list]
        files = [item for item in contents if item.is_file() and item.name not in exclude_list]
        
        folders.sort(key=lambda x: x.name.lower())
        files.sort(key=lambda x: x.name.lower())
        
        tree_str = ""
        items = folders + files
        for i, item in enumerate(items):
            if i == len(items) - 1:
                tree_str += f"{prefix}└── {item.name}\n"
                if item.is_dir():
                    tree_str += tree(item.path, prefix + "    ")
            else:
                tree_str += f"{prefix}├── {item.name}\n"
                if item.is_dir():
                    tree_str += tree(item.path, prefix + "│   ")
        
        return tree_str

    project_tree = f"{os.path.basename(root_dir)}/\n" + tree(root_dir)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(project_tree)
    
    print(f"Project tree has been generated and saved to {output_file}")


def read_file_content(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def generate_project_code(root_dir, output_file, exclude_list, skip_extensions, skip_files):
    project_structure = {}

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Apply exclusions
        dirnames[:] = [d for d in dirnames if not should_exclude(os.path.join(dirpath, d), exclude_list)]

        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            relative_path = os.path.relpath(full_path, root_dir)

            if (should_exclude(full_path, exclude_list) or 
                any(filename.endswith(ext) for ext in skip_extensions) or
                filename in skip_files):
                continue

            try:
                # Try to open the file in text mode
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                project_structure[relative_path] = FileContent(content)
            except UnicodeDecodeError:
                # If we can't decode it as UTF-8, it's probably a binary file
                print(f"Skipping binary file: {relative_path}")
            except Exception as e:
                print(f"Error reading {relative_path}: {str(e)}")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(project_structure, f, cls=ReadableJSONEncoder, indent=2)

    print(f"Project code has been written to {output_file}")

if __name__ == '__main__':
    # Get the project root directory (assuming this script is in the root)
    project_root = Path(__file__).parent.absolute()

    # Define the output file paths
    tree_file = project_root / 'project_tree.txt'
    code_file = project_root / 'project_code.txt'

    # Define the exclusion list for tree generation
    tree_exclude_list = [
        'venv',
        '.git',
        '__pycache__',
        '.pytest_cache',
        '.vscode',
        '.idea',
        'node_modules',
        '.DS_Store',
        'project_tree.txt',
        'project_code.txt',
        'example'
    ]

    # Define additional exclusions for code generation
    code_exclude_list = tree_exclude_list + [
        'app_logs',
        'app_data',
        'test_results',
        'static/libs',
        'static/js/libs',
        'static/webfonts',
        'static/img',
        'static/css/bootstrap',
        'static/css/fontawesome'
    ]

    # Define file extensions to skip for code extraction
    skip_extensions = ['.pyc', '.pyo', '.pyd', '.db', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.ttf', '.eot']

    # Define specific files to skip for code extraction
    skip_files = ['LICENSE', '__init__.py', '.env', 'project_detail.py']

    # Generate the project tree
    generate_project_tree(project_root, tree_file, tree_exclude_list)

    # Generate the project code
    generate_project_code(project_root, code_file, code_exclude_list, skip_extensions, skip_files)