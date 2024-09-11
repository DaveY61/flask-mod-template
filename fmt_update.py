import os
import subprocess
import requests
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import logging
from packaging import version
import shutil
import re

REPO_OWNER = "DaveY61"
REPO_NAME = "flask-mod-template"

# Set up logging
LOG_FILE = 'fmt_update_log.txt'
logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def version_key(v):
    return [int(x) for x in re.findall(r'\d+', v)]

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
            text="Include FMT 'example' changes (may add clutter to your project)", 
            variable=self.keep_examples,
            command=self.toggle_keep_examples
        )
        self.keep_examples_check.pack(anchor='w', pady=5)

        self.keep_readmes_check = ttk.Checkbutton(
            self.checkbox_frame,
            text="Include FMT 'README' changes (may overwrite your README files)", 
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
                releases = response.json()
                # Sort releases using the version_key function
                self.releases = sorted(releases, key=lambda r: version_key(r['tag_name']), reverse=True)
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
        current_version = self.get_current_version()[1].split(': ')[1]
        template_tag = self.selected_release['tag_name']
        update_branch_name = f"template-update-{template_tag}"
        backup_dir = os.path.join("fmt_update_backups", template_tag)
        replaced_files = []
        local_changes = []
        removed_files = []
        ignored_files = ['.gitignore', 'LICENSE']

        try:
            # Create version-specific backup directory
            os.makedirs(backup_dir, exist_ok=True)

            # Set up the template repo as a remote
            self.run_command('git remote remove template')  # Remove if exists
            self.run_command(f'git remote add template {template_url}')

            # Check for local changes
            output, _, _ = self.run_command('git status --porcelain')
            if output:
                local_changes = [line.split()[1] for line in output.splitlines()]
                changes_msg = "Local changes detected in the following files:\n" + "\n".join(local_changes)
                changes_msg += "\n\nDo you want to proceed? These changes may be overwritten."
                if not messagebox.askyesno("Local Changes Detected", changes_msg):
                    return False, "Update cancelled due to local changes"

            # Fetch all content from the template
            self.run_command('git fetch template --tags')

            # Get list of all tags
            output, _, _ = self.run_command('git ls-remote --tags template')
            all_tags = []
            for line in output.splitlines():
                tag = line.split('refs/tags/')[-1]
                if not tag.endswith('^{}'):
                    all_tags.append(tag)

            # Sort tags using version_key
            all_tags.sort(key=version_key)

            self.log_message(f"Available tags: {', '.join(all_tags)}")

            # Determine the range of tags to process
            if current_version == "0.0.0":
                start_index = 0
                self.log_message("No current version detected. Will update from the first available version.")
            else:
                try:
                    start_index = all_tags.index(current_version)
                except ValueError:
                    self.log_message(f"Current version {current_version} not found in tags. Starting from the earliest version.")
                    start_index = 0

            try:
                end_index = all_tags.index(template_tag)
            except ValueError:
                return False, f"Selected version {template_tag} not found in available tags."

            tags_to_process = all_tags[start_index:end_index+1]

            self.log_message(f"Processing tags from {tags_to_process[0]} to {tags_to_process[-1]}")

            files_to_update = set()

            # Get list of changed files for each tag in the range
            for i in range(len(tags_to_process) - 1):
                current_tag = tags_to_process[i]
                next_tag = tags_to_process[i + 1]
                self.log_message(f"Comparing changes between {current_tag} and {next_tag}")
                
                output, error, code = self.run_command(f'git diff --name-only {current_tag} {next_tag}')
                if code != 0:
                    self.log_message(f"Error comparing tags: {error}")
                else:
                    files_to_update.update(output.splitlines())

            # Filter out ignored files and handle README and .example files/folders
            files_to_update = {
                file for file in files_to_update
                if file not in ignored_files
                and not (file.startswith('README') and not self.keep_readmes.get())
                and not ((file.endswith('.example') or '.example/' in file) and not self.keep_examples.get())
            }

            if not files_to_update:
                return False, f"No changes detected between current version and template version ({template_tag})"

            # Create a new branch for the update
            self.run_command(f'git checkout -b {update_branch_name}')

            # Apply template changes
            total_files = len(files_to_update)
            for index, file in enumerate(files_to_update, 1):
                # Update progress
                self.progress['value'] = (index / total_files) * 100
                self.update_status(f"Processing files: {index}/{total_files}")

                # Check if the file exists in the new template version
                result, error, code = self.run_command(f'git ls-tree -r --name-only refs/tags/{template_tag} -- "{file}"')
                file_in_template = (code == 0 and result.strip() == file)

                if file_in_template:
                    # File exists in the template, so update it
                    self.log_message(f"Attempting to checkout file: {file}")
                    result, error, code = self.run_command(f'git checkout refs/tags/{template_tag} -- "{file}"')
                    if code == 0:
                        # Backup existing file if it exists
                        if os.path.exists(file):
                            backup_path = os.path.join(backup_dir, file)
                            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                            shutil.copy2(file, backup_path)
                        replaced_files.append(file)
                    else:
                        self.log_message(f"Checkout result: {result}, Error: {error}, Code: {code}")
                        self.log_message(f"Failed to checkout file: {file}")
                else:
                    # File doesn't exist in the template, so remove it from the project
                    if os.path.exists(file):
                        try:
                            backup_path = os.path.join(backup_dir, file)
                            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                            shutil.move(file, backup_path)
                            self.run_command(f'git rm "{file}"')
                            removed_files.append(file)
                            self.log_message(f"Removed file from project: {file}")
                        except Exception as e:
                            self.log_message(f"Failed to remove file {file}: {str(e)}")
                    else:
                        self.log_message(f"File not found in project, skipping removal: {file}")

            # Update fmt_version.txt
            with open('fmt_version.txt', 'w') as f:
                f.write(template_tag)
            self.run_command('git add fmt_version.txt')

            # After the loop, update the commit message to include removed files
            commit_message = f"Update to template version {template_tag}"
            if removed_files:
                commit_message += "\n\nRemoved files:\n" + "\n".join(removed_files)

            # Use the updated commit message when committing changes
            self.run_command(f'git commit -m "{commit_message}"')

            # Switch back to main and merge the update branch
            self.run_command('git checkout main')
            output, error, code = self.run_command(f'git merge --no-ff {update_branch_name}')

            if code != 0:
                return False, f"Failed to merge changes into main: {error}"

            # Clean up
            self.run_command(f'git branch -D {update_branch_name}')
            self.run_command('git remote remove template')

            # Prepare summary message
            summary = f"Template updated to version {template_tag}\n\n"
            if replaced_files:
                summary += f"Files replaced by the template:\n"
                for file in replaced_files:
                    summary += f"- {file}\n"
            if removed_files:
                summary += f"\nFiles removed (no longer in template):\n"
                for file in removed_files:
                    summary += f"- {file}\n"
            if local_changes:
                summary += f"\nLocal changes detected in:\n"
                for file in local_changes:
                    summary += f"- {file}\n"
            summary += f"\nBackups of replaced and removed files are stored in:\n{os.path.abspath(backup_dir)}"

            # Show summary to the user
            messagebox.showinfo("Update Summary", summary)

            return True, summary

        except Exception as e:
            self.log_message(f"Unexpected error: {str(e)}")
            return False, f"Unexpected error during update: {str(e)}"
        
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