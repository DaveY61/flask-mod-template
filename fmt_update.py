import os
import subprocess
import requests
from packaging import version
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import logging
import chardet

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

    def update_process(self):
        steps = [
            ("Checking current version", self.get_current_version),
            ("Fetching available versions", self.get_github_releases),
            ("Selecting update version", self.select_version),
            ("Initializing/Updating template", self.initialize_or_update_template),
            ("Finalizing update", self.finalize_update)
        ]

        total_steps = len(steps)
        for i, (step_name, step_function) in enumerate(steps, 1):
            self.update_status(f"Step {i}/{total_steps}: {step_name}")
            self.progress['value'] = ((i - 1) / total_steps) * 100
            success, message = step_function()
            self.log_message(f"{i}. {step_name}: {'Success' if success else 'Failed'}")
            self.log_message(f"   - {message}")
            if not success:
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
        
        # Sort releases from newest to oldest
        sorted_releases = sorted(newer_releases, key=lambda r: version.parse(r['tag_name']), reverse=True)
        
        # Create a list of version strings
        version_list = [f"{r['tag_name']} - {r['name']}" for r in sorted_releases]
        
        # Show a dialog to select the version
        selection = SelectVersionDialog(self, "Select Version", "Choose a version to update to:", version_list)
        if selection.result is None:  # User cancelled
            return False, "Version selection cancelled"
        
        # Find the selected release
        selected_version = selection.result.split(' - ')[0]
        self.selected_release = next((r for r in sorted_releases if r['tag_name'] == selected_version), None)
        
        if self.selected_release is None:
            return False, "Invalid version selected"
        
        return True, f"Selected version: {self.selected_release['tag_name']}"

    def initialize_or_update_template(self):
        release_tag = self.selected_release['tag_name']
        
        if not os.path.isdir('.git'):
            self.run_command("git init")

        _, _, code = self.run_command("git remote get-url template")
        if code != 0:
            self.run_command(f"git remote add template https://github.com/{REPO_OWNER}/{REPO_NAME}.git")

        _, _, code = self.run_command("git fetch template --tags")
        if code != 0:
            return False, "Failed to fetch tags"

        _, _, code = self.run_command(f"git rev-parse --verify refs/tags/{release_tag}")
        if code != 0:
            return False, f"Tag {release_tag} does not exist in the template repository"

        # Fetch the specific tag
        _, error, code = self.run_command(f"git fetch template {release_tag}")
        if code != 0:
            return False, f"Failed to fetch template content: {error}"

        # Check for local modifications
        modified_files = self.get_modified_files(release_tag)
        if modified_files:
            message = "The following files have modifications compared to the template and will be overwritten:\n\n"
            message += "\n".join(modified_files)
            message += "\n\nDo you want to proceed with the update? This will overwrite these changes."
            if not messagebox.askyesno("Warning", message):
                return False, "Update cancelled due to local modifications"

        # Create a temporary branch for the update
        temp_branch = f"temp-template-update-{release_tag}"
        _, _, code = self.run_command(f"git checkout -b {temp_branch}")
        if code != 0:
            return False, f"Failed to create temporary branch: {temp_branch}"

        # Reset the temporary branch to the fetched content
        _, error, code = self.run_command("git reset --hard FETCH_HEAD")
        if code != 0:
            self.run_command(f"git checkout - && git branch -D {temp_branch}")  # Clean up
            return False, f"Failed to reset to template content: {error}"

        # If successful, create or update the template update branch
        branch_name = f"template-update-{release_tag}"
        _, _, code = self.run_command(f"git branch -D {branch_name}")  # Delete if exists
        _, _, code = self.run_command(f"git checkout -b {branch_name}")
        if code != 0:
            self.run_command(f"git checkout - && git branch -D {temp_branch}")  # Clean up
            return False, f"Failed to create update branch: {branch_name}"

        # Clean up the temporary branch
        self.run_command(f"git branch -D {temp_branch}")

        return True, "Template updated successfully"

    def get_modified_files(self, release_tag):
        # Fetch the specific tag
        self.run_command(f"git fetch template {release_tag}")
        
        # Get list of files in the template
        output, _, _ = self.run_command("git ls-tree -r --name-only FETCH_HEAD")
        template_files = set(output.strip().split('\n'))

        modified_files = []
        for file in template_files:
            if os.path.exists(file):
                # Compare local file with template file
                try:
                    with open(file, 'rb') as f:
                        local_content = f.read()
                    local_encoding = chardet.detect(local_content)['encoding']
                    local_content = local_content.decode(local_encoding)
                except Exception as e:
                    print(f"Error reading local file {file}: {str(e)}")
                    continue

                output, _, _ = self.run_command(f"git show FETCH_HEAD:{file}")
                template_content = output

                if local_content.strip() != template_content.strip():
                    modified_files.append(file)

        return modified_files
        
    def finalize_update(self):
        with open('fmt_version.txt', 'w') as f:
            f.write(self.selected_release['tag_name'])
        return True, f"Updated version file to {self.selected_release['tag_name']}"

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