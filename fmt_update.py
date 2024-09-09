import os
import subprocess
import requests
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import logging
from packaging import version

REPO_OWNER = "DaveY61"
REPO_NAME = "UpdateTestRepo"

# Set up logging
logging.basicConfig(filename='fmt_update_log.txt', level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

class UpdateApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Template Update Tool")
        self.geometry("600x400")
        self.create_widgets()

    def create_widgets(self):
        self.progress = ttk.Progressbar(self, length=500, mode='determinate')
        self.progress.pack(pady=10)

        self.status_label = ttk.Label(self, text="Ready to start")
        self.status_label.pack(pady=10)

        self.start_button = ttk.Button(self, text="Start Update", command=self.start_update)
        self.start_button.pack(pady=10)

        self.log_text = tk.Text(self, height=15, width=70)
        self.log_text.pack(pady=10)

    def start_update(self):
        self.start_button.config(state='disabled')
        self.log_text.delete(1.0, tk.END)  # Clear previous log
        threading.Thread(target=self.update_process, daemon=True).start()

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

    def update_process(self):
        steps = [
            ("Checking for worktrees", self.check_and_remove_worktrees),
            ("Checking current version", self.get_current_version),
            ("Fetching available versions", self.get_github_releases),
            ("Selecting update version", self.select_version),
            ("Updating from template", self.update_from_template)
        ]

        total_steps = len(steps)
        for i, (step_name, step_function) in enumerate(steps, 1):
            self.update_status(f"Step {i}/{total_steps}: {step_name}")
            self.progress['value'] = ((i - 1) / total_steps) * 100
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
            self.progress['value'] = 100
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

    def update_from_template(self):
        template_url = f"https://github.com/{REPO_OWNER}/{REPO_NAME}.git"
        template_tag = self.selected_release['tag_name']
        update_branch_name = f"template-update-{template_tag}"

        try:
            # Set up the template repo as a remote
            self.run_command('git remote remove template')  # Remove if exists
            output, error, code = self.run_command(f'git remote add template {template_url}')
            if code != 0:
                return False, f"Failed to add template remote: {error}"

            # Fetch the template changes
            output, error, code = self.run_command(f'git fetch template {template_tag}')
            if code != 0:
                return False, f"Failed to fetch template: {error}"

            # Create a new branch for the update based on the fetched tag
            output, error, code = self.run_command(f'git checkout -b {update_branch_name} FETCH_HEAD')
            if code != 0:
                return False, f"Failed to create update branch: {error}"

            # Switch back to the main branch
            output, error, code = self.run_command('git checkout main')
            if code != 0:
                return False, f"Failed to switch back to main branch: {error}"

            # Attempt to merge the update branch
            output, error, code = self.run_command(f'git merge {update_branch_name} --allow-unrelated-histories')
            if code != 0:
                # Merge conflict occurred
                conflicted_files = self.get_conflicted_files()
                conflict_message = "Merge conflicts occurred in the following files:\n\n"
                conflict_message += "\n".join(conflicted_files)
                conflict_message += "\n\nPlease resolve these conflicts manually and then:\n"
                conflict_message += "1. Stage the resolved files using 'git add <file>'\n"
                conflict_message += "2. Commit the changes using 'git commit -m \"Merge template update\"'\n"
                conflict_message += "3. Run this update script again to complete the process"

                # Abort the merge to leave the repository in a clean state
                self.run_command('git merge --abort')

                return False, conflict_message

            # Update fmt_version.txt after successful merge
            with open('fmt_version.txt', 'w') as f:
                f.write(template_tag)
            
            # Commit the version update
            self.run_command('git add fmt_version.txt')
            self.run_command(f'git commit -m "Update fmt_version.txt to {template_tag}"')

            return True, "Template update completed successfully"

        except Exception as e:
            return False, f"Unexpected error during update: {str(e)}"

        finally:
            # Clean up: delete the temporary branch and remote
            self.run_command(f'git branch -D {update_branch_name}')
            self.run_command('git remote remove template')

    def get_conflicted_files(self):
        output, error, code = self.run_command('git diff --name-only --diff-filter=U')
        if code == 0:
            return output.split('\n')
        return []

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