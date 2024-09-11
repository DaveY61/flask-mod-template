import os
import subprocess
import requests
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import logging
from packaging import version
import shutil

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
        self.checkbox_frame.pack(fill='x', padx=20, pady=10)

        self.keep_examples_check = ttk.Checkbutton(
            self.checkbox_frame,
            text="Copy FMT 'example' files and folders (may add clutter to your project)", 
            variable=self.keep_examples,
            command=self.toggle_keep_examples
        )
        self.keep_examples_check.pack(anchor='w', pady=5)

        self.keep_readmes_check = ttk.Checkbutton(
            self.checkbox_frame,
            text="Copy FMT 'README' files (may overwrite your files)", 
            variable=self.keep_readmes,
            command=self.toggle_keep_readmes
        )
        self.keep_readmes_check.pack(anchor='w', pady=5)

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
            ("Checking current branch", self.check_current_branch),
            ("Checking for worktrees", self.check_and_remove_worktrees),
            ("Checking current version", self.get_current_version),
            ("Fetching available versions", self.get_github_releases),
            ("Selecting update version", self.select_version),
            ("Updating from template", self.update_from_template)
        ]

        for i, (step_name, step_function) in enumerate(steps, 1):
            self.update_status(f"Step {i}: {step_name}")
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

    def check_current_branch(self):
        current_branch = self.get_current_branch()
        if current_branch != 'main':
            return False, f"Please switch to the 'main' branch before updating. Current branch: {current_branch}"
        return True, "Current branch is 'main'"

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
        output_str = output.decode('utf-8').strip()
        error_str = error.decode('utf-8').strip()
        
        if output_str:
            logging.debug(f"Output: {output_str}")
        if error_str:
            logging.debug(f"Error: {error_str}")
        
        return output_str, error_str, process.returncode

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

    def present_update_summary(self):
        message = "Update Summary:\n\n"
        message += f"Files to be updated: {len(self.changed_files)}\n"
        message += f"Conflicting files: {len(self.conflicting_files)}\n\n"

        if self.conflicting_files:
            message += "Conflicting files:\n"
            for file in self.conflicting_files:
                message += f"- {file}\n"
            message += "\n"

        message += "Do you want to proceed with the update?"
        
        if messagebox.askyesno("Update Summary", message):
            return True, "User chose to proceed with the update"
        else:
            return False, "Update cancelled by user"

    def update_from_template(self):
        template_url = f"https://github.com/{REPO_OWNER}/{REPO_NAME}.git"
        template_tag = self.selected_release['tag_name']
        update_branch_name = f"template-update-{template_tag}"
        backup_dir = os.path.join("fmt_update_backups", template_tag)
        replaced_files = []
        local_changes = []
        special_files = ['.gitignore', 'LICENSE']

        try:
            # Create version-specific backup directory
            os.makedirs(backup_dir, exist_ok=True)

            # Set up the template repo as a remote
            self.run_command('git remote remove template')  # Remove if exists
            self.run_command(f'git remote add template {template_url}')

            # Fetch the template changes
            self.run_command(f'git fetch template {template_tag}')

            # Check for local changes
            output, _, _ = self.run_command('git status --porcelain')
            if output:
                local_changes = [line.split()[1] for line in output.splitlines()]
                changes_msg = "Local changes detected in the following files:\n" + "\n".join(local_changes)
                changes_msg += "\n\nDo you want to proceed? These changes may be overwritten."
                if not messagebox.askyesno("Local Changes Detected", changes_msg):
                    return False, "Update cancelled due to local changes"

            # Create a new branch for the update
            self.run_command(f'git checkout -b {update_branch_name}')

            # Get the list of files changed in the template
            output, _, _ = self.run_command(f'git diff --name-only HEAD..template/{template_tag}')
            changed_files = output.splitlines()

            # Apply template changes
            for file in changed_files:
                # Handle special files
                if file in special_files:
                    if not self.handle_special_file(file, template_tag):
                        continue
                elif file.startswith('README') and not self.keep_readmes.get():
                    continue
                elif file.endswith('.example') and not self.keep_examples.get():
                    continue

                # Backup existing file if it exists
                if os.path.exists(file):
                    backup_path = os.path.join(backup_dir, file)
                    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                    shutil.copy2(file, backup_path)
                    replaced_files.append(file)

                # Copy file from template
                self.run_command(f'git checkout template/{template_tag} -- "{file}"')

            # Update fmt_version.txt
            with open('fmt_version.txt', 'w') as f:
                f.write(template_tag)
            self.run_command('git add fmt_version.txt')

            # Commit the changes
            self.run_command(f'git commit -m "Update to template version {template_tag}"')

            # Switch back to main and cherry-pick the update commit
            self.run_command('git checkout main')
            update_commit_hash, _, _ = self.run_command(f'git rev-parse {update_branch_name}')
            output, error, code = self.run_command(f'git cherry-pick {update_commit_hash}')

            if code != 0:
                return False, f"Failed to apply changes to main: {error}"

            # Clean up
            self.run_command(f'git branch -D {update_branch_name}')
            self.run_command('git remote remove template')

            # Prepare summary message
            summary = f"Template updated to version {template_tag}\n\n"
            summary += f"Files replaced by the template:\n"
            for file in replaced_files:
                summary += f"- {file}\n"
            if local_changes:
                summary += f"\nLocal changes detected in:\n"
                for file in local_changes:
                    summary += f"- {file}\n"
            summary += f"\nBackups of replaced files are stored in:\n{os.path.abspath(backup_dir)}"

            # Show summary to the user
            messagebox.showinfo("Update Summary", summary)

            return True, summary

        except Exception as e:
            return False, f"Unexpected error during update: {str(e)}"

    def handle_special_file(self, file, template_tag):
        if file == '.gitignore':
            # Merge .gitignore files
            with open('.gitignore', 'r') as f:
                current_content = f.readlines()
            self.run_command(f'git show template/{template_tag}:.gitignore > .gitignore.template')
            with open('.gitignore.template', 'r') as f:
                template_content = f.readlines()
            merged_content = list(set(current_content + template_content))
            with open('.gitignore', 'w') as f:
                f.writelines(sorted(merged_content))
            os.remove('.gitignore.template')
            self.run_command('git add .gitignore')
            return True
        elif file == 'LICENSE':
            # Ask user what to do with LICENSE
            response = messagebox.askyesno("Update LICENSE", "Do you want to update the LICENSE file from the template?")
            if response:
                self.run_command(f'git checkout template/{template_tag} -- LICENSE')
                return True
        return False

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