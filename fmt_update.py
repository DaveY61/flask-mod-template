import os
import sys
import subprocess
import requests
from packaging import version
import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.simpledialog as simpledialog
import threading
import logging

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
        for i, (step_name, step_function) in enumerate(steps):
            self.update_status(f"Step {i+1}/{total_steps}: {step_name}")
            self.progress['value'] = (i / total_steps) * 100
            success, message = step_function()
            self.log_message(f"{step_name}: {'Success' if success else 'Failed'}")
            self.log_message(message)
            if not success:
                self.update_status("Update failed")
                messagebox.showerror("Error", f"Failed at step: {step_name}\n{message}")
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
        
        # Create a list of version strings
        version_list = [f"{r['tag_name']} - {r['name']}" for r in newer_releases]
        
        # Show a dialog to select the version
        choice = simpledialog.askstring(
            "Select Version",
            "Choose a version to update to:",
            parent=self,
            initialvalue=version_list[0]
        )
        
        if choice is None:  # User cancelled
            return False, "Version selection cancelled"
        
        # Find the selected release
        selected_version = choice.split(' - ')[0]
        self.selected_release = next((r for r in newer_releases if r['tag_name'] == selected_version), None)
        
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

        branch_name = f"template-update-{release_tag}"
        _, _, code = self.run_command(f"git checkout -b {branch_name} {release_tag}")
        if code != 0:
            if "already exists" in _:
                self.run_command(f"git checkout {branch_name}")
            else:
                return False, f"Failed to create or switch to branch: {branch_name}"

        _, _, code = self.run_command(f"git reset --hard {release_tag}")
        if code != 0:
            return False, f"Failed to reset to tag: {release_tag}"

        return True, "Template updated successfully"

    def finalize_update(self):
        with open('fmt_version.txt', 'w') as f:
            f.write(self.selected_release['tag_name'])
        return True, f"Updated version file to {self.selected_release['tag_name']}"

if __name__ == "__main__":
    app = UpdateApp()
    app.mainloop()