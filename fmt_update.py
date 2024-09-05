import os
import sys
import subprocess
import requests
import json
from packaging import version

# GitHub repository details
REPO_OWNER = "your_github_username"
REPO_NAME = "flask-mod-template"

def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    return output.decode('utf-8'), error.decode('utf-8'), process.returncode

def get_github_releases():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch releases: {response.status_code}")
        return None

def get_current_version():
    # You might want to store the current version in a file or use git tags
    # For this example, we'll assume it's stored in a version.txt file
    try:
        with open('version.txt', 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return "0.0.0"

def create_branch(branch_name):
    output, error, code = run_command(f"git checkout -b {branch_name}")
    if code != 0:
        print(f"Failed to create branch: {error}")
        return False
    return True

def pull_subtree(release_tag):
    output, error, code = run_command(f"git subtree pull --prefix=. https://github.com/{REPO_OWNER}/{REPO_NAME}.git {release_tag} --squash")
    if code != 0:
        print(f"Failed to pull subtree: {error}")
        return False
    return True

def merge_branch(branch_name):
    output, error, code = run_command(f"git checkout main && git merge {branch_name}")
    if code != 0:
        print(f"Failed to merge branch: {error}")
        return False
    return True

def main():
    current_version = get_current_version()
    print(f"Current version: {current_version}")

    releases = get_github_releases()
    if not releases:
        sys.exit(1)

    newer_releases = [r for r in releases if version.parse(r['tag_name']) > version.parse(current_version)]
    if not newer_releases:
        print("You are already on the latest version.")
        sys.exit(0)

    print("Available newer versions:")
    for i, release in enumerate(newer_releases):
        print(f"{i+1}. {release['tag_name']} - {release['name']}")

    choice = int(input("Enter the number of the version you want to update to: ")) - 1
    selected_release = newer_releases[choice]

    branch_name = f"update-to-{selected_release['tag_name']}"
    if not create_branch(branch_name):
        sys.exit(1)

    if not pull_subtree(selected_release['tag_name']):
        sys.exit(1)

    # Check for conflicts
    output, error, code = run_command("git status")
    if "Unmerged paths:" in output:
        print("Conflicts detected. Please resolve them manually and then run:")
        print(f"git add . && git commit -m 'Resolve conflicts for {selected_release['tag_name']}' && git checkout main && git merge {branch_name}")
    else:
        if merge_branch(branch_name):
            print(f"Successfully updated to version {selected_release['tag_name']}")
            with open('version.txt', 'w') as f:
                f.write(selected_release['tag_name'])
        else:
            print("Failed to merge. Please merge manually.")

if __name__ == "__main__":
    main()