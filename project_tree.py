import os
from pathlib import Path

def generate_project_tree(root_dir, output_file, exclude_list):
    def write_tree(dir_path, file, prefix=''):
        contents = sorted(os.listdir(dir_path))
        for i, path in enumerate(contents):
            full_path = os.path.join(dir_path, path)
            if any(exclude in full_path for exclude in exclude_list):
                continue
            
            is_last = (i == len(contents) - 1)
            pointer = '└── ' if is_last else '├── '
            file.write(f'{prefix}{pointer}{path}\n')
            
            if os.path.isdir(full_path):
                extension = '    ' if is_last else '│   '
                write_tree(full_path, file, prefix + extension)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f'{os.path.basename(root_dir)}/\n')
        write_tree(root_dir, f, '')

if __name__ == '__main__':
    # Get the project root directory (assuming this script is in the root)
    project_root = Path(__file__).parent.absolute()

    # Define the output file path
    output_file = project_root / 'project_tree.txt'

    # Define the exclusion list
    exclude_list = [
        'venv',
        '.git',
        '__pycache__',
        '.pytest_cache',
        '.vscode',
        '.idea',
        'node_modules',
        '.DS_Store',
        'project_tree'
    ]

    # Generate the project tree
    generate_project_tree(project_root, output_file, exclude_list)

    print(f"Project tree has been generated and saved to {output_file}")