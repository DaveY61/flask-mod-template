# PythonAnywhere Deployment Guide

This guide provides step-by-step instructions for deploying the Flask Modular Template application on PythonAnywhere, a platform that makes it easy to host, run, and code Python in the cloud.

## Table of Contents
1. [Setting up PythonAnywhere Account](#1-setting-up-pythonanywhere-account)
2. [Creating a New Web App](#2-creating-a-new-web-app)
3. [Setting Up Your Project](#3-setting-up-your-project)
4. [Configuring the Web App](#4-configuring-the-web-app)
5. [Setting Up Environment Variables](#5-setting-up-environment-variables)
6. [Database Setup](#6-database-setup)
7. [Final Configuration and Deployment](#7-final-configuration-and-deployment)
8. [Troubleshooting](#8-troubleshooting)

## 1. Setting up PythonAnywhere Account

1. Go to [PythonAnywhere](https://www.pythonanywhere.com/) and sign up for an account if you don't have one.
2. Choose a plan that suits your needs. The free tier is sufficient for testing and small projects.

## 2. Creating a New Web App

1. After logging in, go to the Web tab on your dashboard.
2. Click on "Add a new web app".
3. Choose "Manual configuration" (not "Flask").
4. Select the Python version that matches your project (e.g., Python 3.8).

## 3. Setting Up Your Project

1. Open a Bash console from your PythonAnywhere dashboard.
2. Clone your repository:
   ```
   git clone https://github.com/yourusername/flask-mod-template.git
   ```
3. Create a virtual environment:
   ```
   mkvirtualenv --python=/usr/bin/python3.8 mysite-virtualenv
   ```
4. Install the required packages:
   ```
   cd flask-mod-template
   pip install -r requirements.txt
   ```

## 4. Configuring the Web App

1. Go back to the Web tab on your dashboard.
2. In the Code section, set the following:
   - Source code: `/home/yourusername/flask-mod-template`
   - Working directory: `/home/yourusername/flask-mod-template`
3. In the WSGI configuration file section, click on the link to edit the WSGI file.
4. Replace the content with:
   ```python
   import sys
   path = '/home/yourusername/flask-mod-template'
   if path not in sys.path:
       sys.path.append(path)

   from app.app import app as application
   ```

## 5. Setting Up Environment Variables

1. In the Web tab, go to the "Environment variables" section.
2. Add each variable from your `.env` file

## 6. Database Setup

1. If you're using SQLite, ensure the database path is writable:
   ```
   mkdir -p /home/yourusername/flask-mod-template/app_data/users
   ```
2. For other databases, update your configuration accordingly.

## 7. Final Configuration and Deployment

1. In the Web tab, go to the "Static files" section.
2. Add an entry:
   - URL: /static/
   - Directory: /home/yourusername/flask-mod-template/app/static
3. Click the "Reload" button at the top of the Web tab.

Your application should now be live at `yourusername.pythonanywhere.com`.

## 8. Troubleshooting

- Check the error logs in the Web tab if your application doesn't work as expected.
- Ensure all required environment variables are set correctly.
- Make sure your virtual environment is activated when installing packages or running scripts.
- If you make changes to your code, remember to reload the web app.

For more detailed information, refer to the [PythonAnywhere help pages](https://help.pythonanywhere.com/).
```

Now, let's update the "Deployment" section in the main `README.md` file to include a link to this new PythonAnywhere deployment guide: