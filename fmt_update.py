import os
import subprocess
import requests
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import logging
from packaging import version
from datetime import datetime
import shlex

REPO_OWNER = "DaveY61"
REPO_NAME = "flask-mod-template"

# Set up logging
LOG_FILE = 'fmt_update_log.txt'
logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

class UpdateApp(tk.Tk):
    def __init__(self):
        super().__init__()

        style = ttk.Style()
        style.configure('Accent.TButton', foreground='navy', background='#007bff', font=('Helvetica', 10, 'bold'))

        self.title("Template Update Tool")
        self.geometry("600x500")
        self.keep_examples = tk.BooleanVar(value=False)
        self.keep_readmes = tk.BooleanVar(value=False)
        self.create_widgets()

    def create_widgets(self):
        self.progress = ttk.Progressbar(self, length=500, mode='determinate')
        self.progress.pack(pady=10)

        self.status_label = ttk.Label(self, text="Ready to start")
        self.status_label.pack(pady=10)

        self.start_button = ttk.Button(self, text="Start Update", command=self.start_update, style='Accent.TButton')
        self.start_button.pack(pady=10)

        self.checkbox_frame = ttk.Frame(self)
        self.checkbox_frame.pack(fill='x', padx=20, pady=10)  # padx adds left and right margin

        self.keep_examples_check = ttk.Checkbutton(
            self.checkbox_frame,  # Parent is now the checkbox_frame
            text="Copy FMT 'example' files and folders (may add clutter to your project)", 
            variable=self.keep_examples,
            command=self.toggle_keep_examples
        )
        self.keep_examples_check.pack(anchor='w', pady=5)  # 'w' means west (left) alignment

        self.keep_readmes_check = ttk.Checkbutton(
            self.checkbox_frame,  # Parent is now the checkbox_frame
            text="Copy FMT 'README' files (may overwrite your files)", 
            variable=self.keep_readmes,
            command=self.toggle_keep_readmes
        )
        self.keep_readmes_check.pack(anchor='w', pady=5)  # 'w' means west (left) alignment

        self.log_text = tk.Text(self, height=15, width=70)
        self.log_text.pack(pady=10)

    def toggle_keep_examples(self):
        logging.info(f"Keep examples toggled: {self.keep_examples.get()}")

    def toggle_keep_readmes(self):
        logging.info(f"Keep READMEs toggled: {self.keep_readmes.get()}")

    def start_update(self):
        self.start_button.config(state='disabled')
        self.log_text.delete(1.0, tk.END)  # Clear previous log
        threading.Thread(target=self.update_process, daemon=True).start()

    def update_process(self):
        # Clear the log file
        open(LOG_FILE, 'w').close()
        logging.info("Starting new update session")

        steps = [
            ("Checking for worktrees", self.check_and_remove_worktrees),
            ("Checking current version", self.get_current_version),
            ("Fetching available versions", self.get_github_releases),
            ("Selecting update version", self.select_version),
            ("Updating from template", self.update_from_template)
        ]

        total_steps = len(steps)
        for i, (step_name, step_function) in enumerate(steps, 1):
            self.update_status("Update in progress!")
            success, message = step_function()
            self.log_message(f"{i}. {step_name}: {'Success' if success else 'Failed'}")
            self.log_message(f"   - {message}")
            if not success:
                if "Merge conflicts occurred" in message:
                    self.update_status("Merge conflicts detected")
                    messagebox.showinfo("Merge Conflicts", message)
                else:
                    self.update_status("Update failed")
                    messagebox.showerror("Error", f"Failed at step {i}: {step_name}\n{message}")
                break
        else:
            self.update_status("Update completed successfully")
            messagebox.showinfo("Success", "Template update completed successfully")
        
        self.start_button.config(state='normal')

    def update_status(self, message):
        self.status_label.config(text=message)

    def log_message(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        logging.info(message)

    def run_command(self, command):
        logging.debug(f"Running command: {command}")
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        output, error = process.communicate()
        logging.debug(f"Output: {output.decode('utf-8').strip()}")
        logging.debug(f"Error: {error.decode('utf-8').strip()}")
        return output.decode('utf-8').strip(), error.decode('utf-8').strip(), process.returncode

    def get_current_version(self):
        try:
            with open('fmt_version.txt', 'r') as f:
                version = f.read().strip()
            return True, f"Current version: {version}"
        except FileNotFoundError:
            return True, "Current version: 0.0.0"

    def get_github_releases(self):
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                self.releases = response.json()
                return True, f"Found {len(self.releases)} releases"
            else:
                return False, f"Failed to fetch releases: {response.status_code}"
        except Exception as e:
            return False, f"Error fetching releases: {str(e)}"

    def select_version(self):
        current_version = self.get_current_version()[1].split(': ')[1]
        newer_releases = [r for r in self.releases if version.parse(r['tag_name']) > version.parse(current_version)]
        if not newer_releases:
            return False, "No newer versions available"
        
        sorted_releases = sorted(newer_releases, key=lambda r: version.parse(r['tag_name']), reverse=True)
        version_list = [f"{r['tag_name']} - {r['name']}" for r in sorted_releases]
        
        selection = SelectVersionDialog(self, "Select Version", "Choose a version to update to:", version_list)
        if selection.result is None:
            return False, "Version selection cancelled"
        
        selected_version = selection.result.split(' - ')[0]
        self.selected_release = next((r for r in sorted_releases if r['tag_name'] == selected_version), None)
        
        if self.selected_release is None:
            return False, "Invalid version selected"
        
        return True, f"Selected version: {self.selected_release['tag_name']}"

    def check_and_remove_worktrees(self):
        output, error, code = self.run_command('git worktree list')
        if code == 0:
            worktrees = [line.split() for line in output.split('\n') if line.strip()]
            if len(worktrees) > 1:  # More than just the main worktree
                current_dir = os.path.abspath(os.getcwd())
                main_worktree = worktrees[0][0]  # The first worktree is always the main one
                
                if current_dir != main_worktree:
                    return False, f"Please run this script from the main worktree at: {main_worktree}"
                
                message = "Multiple worktrees detected. This may interfere with the update process.\n\n"
                message += "Do you want to remove all additional worktrees?"
                if messagebox.askyesno("Worktrees Detected", message):
                    for worktree in worktrees[1:]:  # Skip the first (main) worktree
                        self.run_command(f'git worktree remove "{worktree[0]}"')
                    return True, "Removed additional worktrees"
                else:
                    return False, "Update cancelled due to existing worktrees"
        return True, "No additional worktrees found or running from main worktree"

    def get_current_branch(self):
        output, _, _ = self.run_command('git rev-parse --abbrev-ref HEAD')
        return output.strip()

    def update_from_template(self):
        template_url = f"https://github.com/{REPO_OWNER}/{REPO_NAME}.git"
        template_tag = self.selected_release['tag_name']
        update_branch_name = f"template-update-{template_tag}"
        backup_files = []

        try:
            current_branch = self.get_current_branch()
            if current_branch != 'main':
                return False, f"Please switch to the 'main' branch before updating. Current branch: {current_branch}"

            # Set up the template repo as a remote
            self.run_command('git remote remove template')  # Remove if exists
            output, error, code = self.run_command(f'git remote add template {template_url}')
            if code != 0:
                return False, f"Failed to add template remote: {error}"

            # Fetch the template changes
            output, error, code = self.run_command(f'git fetch template {template_tag}')
            if code != 0:
                return False, f"Failed to fetch template: {error}"

            # Check if the update branch already exists and delete it if it does
            output, error, code = self.run_command(f'git branch --list {update_branch_name}')
            if output.strip():
                output, error, code = self.run_command(f'git branch -D {update_branch_name}')
                if code != 0:
                    return False, f"Failed to delete existing update branch: {error}"

            # Create a new branch for the update based on the current main
            output, error, code = self.run_command(f'git checkout -b {update_branch_name}')
            if code != 0:
                return False, f"Failed to create update branch: {error}"

            # Get list of files in the template
            output, error, code = self.run_command(f'git ls-tree -r --name-only FETCH_HEAD')
            if code != 0:
                return False, f"Failed to get template file list: {error}"
            template_files = output.splitlines()

            if not template_files:
                return False, "No files found in the template. This is unexpected and may indicate an issue with the template repository."

            # Manually copy each file from the template
            total_files = len(template_files)
            for index, file in enumerate(template_files, 1):
                # Update progress
                self.progress['value'] = (index / total_files) * 100
                self.update_status(f"Copying files: {index}/{total_files}")

                # Skip .gitignore
                if file == '.gitignore':
                    continue
                
                # Skip .example files and folders if keep_examples is False
                if not self.keep_examples.get():
                    if file.endswith('.example') or any(part.endswith('.example') for part in file.split(os.sep)):
                        continue

                # Skip README files if keep_readmes is False
                if not self.keep_readmes.get():
                    if os.path.basename(file).startswith('README'):
                        continue

                # Create directory if it doesn't exist
                dir_name = os.path.dirname(file)
                if dir_name and not os.path.exists(dir_name):
                    os.makedirs(dir_name, exist_ok=True)
                
                # Check if file exists in current branch
                output, error, code = self.run_command(f'git ls-files --error-unmatch "{file}"')
                file_exists = code == 0

                if file_exists:
                    # If file exists, create a backup
                    backup_file = f"{file}.backup"
                    self.run_command(f'git show HEAD:"{file}" > "{backup_file}"')
                    backup_files.append(backup_file)
                
                # Copy file from template
                output, error, code = self.run_command(f'git show FETCH_HEAD:"{file}" > "{file}"')
                if code != 0:
                    return False, f"Failed to copy file {file} from template: {error}"
                
                self.run_command(f'git add "{file}"')

            # Check if there are changes to commit
            status_output, _, _ = self.run_command('git status --porcelain')
            
            # Update fmt_version.txt
            with open('fmt_version.txt', 'w') as f:
                f.write(template_tag)
            self.run_command('git add fmt_version.txt')
            
            if status_output.strip():
                # There are changes to commit
                output, error, code = self.run_command(f'git commit -m "Update to template version {template_tag}"')
                if code != 0:
                    return False, f"Failed to commit changes: {error}"
                commit_message = f"Template updated to version {template_tag}"
            else:
                # No changes to commit except fmt_version.txt
                output, error, code = self.run_command(f'git commit -m "Update fmt_version.txt to {template_tag}"')
                if code != 0:
                    return False, f"Failed to commit version update: {error}"
                commit_message = f"Project already up-to-date. Updated fmt_version.txt to {template_tag}"

            # Switch back to main and merge
            self.run_command('git checkout main')
            output, error, code = self.run_command(f'git merge --no-ff {update_branch_name}')

            if code != 0:
                return False, f"Failed to merge changes: {error}\n\nPlease resolve conflicts manually and then run this script again."

            # Clean up
            self.run_command(f'git branch -D {update_branch_name}')

            # Remove backup files
            for backup_file in backup_files:
                if os.path.exists(backup_file):
                    os.remove(backup_file)

            return True, commit_message

        except Exception as e:
            return False, f"Unexpected error during update: {str(e)}"

        finally:
            # Always remove the template remote
            self.run_command('git remote remove template')
            
            # Clean up any remaining backup files
            for root, dirs, files in os.walk('.'):
                for file in files:
                    if file.endswith('.backup'):
                        os.remove(os.path.join(root, file))

class SelectVersionDialog(tk.Toplevel):
    def __init__(self, parent, title, prompt, choices):
        super().__init__(parent)
        self.title(title)
        self.result = None
        
        tk.Label(self, text=prompt).pack(padx=10, pady=10)
        
        self.combo = ttk.Combobox(self, values=choices, state="readonly")
        self.combo.set(choices[0])  # Set default value
        self.combo.pack(padx=10, pady=10)
        
        tk.Button(self, text="OK", command=self.on_ok).pack(side=tk.LEFT, padx=10, pady=10)
        tk.Button(self, text="Cancel", command=self.on_cancel).pack(side=tk.RIGHT, padx=10, pady=10)
        
        self.transient(parent)
        self.grab_set()
        parent.wait_window(self)

    def on_ok(self):
        self.result = self.combo.get()
        self.destroy()

    def on_cancel(self):
        self.result = None
        self.destroy()

if __name__ == "__main__":
    app = UpdateApp()
    app.mainloop()