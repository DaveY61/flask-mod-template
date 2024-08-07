# AWS Elastic Beanstalk Deployment Guide

This guide provides step-by-step instructions for deploying the Flask Modular Template application using AWS Elastic Beanstalk, including setting up AWS, configuring Elastic Beanstalk, ensuring sufficient storage, and establishing automatic deployment from GitHub.

## Table of Contents
1. [Setting up AWS Account](#1-setting-up-aws-account)
2. [Installing AWS CLI and EB CLI](#2-installing-aws-cli-and-eb-cli)
3. [Configuring AWS Elastic Beanstalk](#3-configuring-aws-elastic-beanstalk)
4. [Preparing Your Application](#4-preparing-your-application)
5. [Deploying Your Application](#5-deploying-your-application)
6. [Ensuring Sufficient Storage](#6-ensuring-sufficient-storage)
7. [Setting Up Automatic Deployment from GitHub](#7-setting-up-automatic-deployment-from-github)
8. [Monitoring and Maintaining Your Application](#8-monitoring-and-maintaining-your-application)

## 1. Setting up AWS Account

1. Go to the [AWS homepage](https://aws.amazon.com/) and click "Create an AWS Account".
2. Follow the sign-up process, providing the required information and payment method.
3. Once your account is created, log in to the AWS Management Console.

## 2. Installing AWS CLI and EB CLI

1. Install the AWS CLI by following the instructions for your operating system: [AWS CLI Installation Guide](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html)

2. Install the Elastic Beanstalk CLI:
   ```
   pip install awsebcli
   ```

3. Configure the AWS CLI with your credentials:
   ```
   aws configure
   ```
   Enter your AWS Access Key ID, Secret Access Key, default region, and output format when prompted.

## 3. Configuring AWS Elastic Beanstalk

1. In the AWS Management Console, go to the Elastic Beanstalk service.
2. Click "Create a new environment".
3. Choose "Web server environment".
4. Fill in the application details:
   - Application name: `flask-mod-template`
   - Environment name: `flask-mod-template-env`
5. For Platform, choose "Python" and select the appropriate Python version.
6. For Application code, choose "Sample application" for now.
7. Click "Create environment".

## 4. Preparing Your Application

1. In your local Flask Modular Template project directory, create a file named `.ebextensions/01_flask.config` with the following content:
   ```yaml
   option_settings:
     aws:elasticbeanstalk:container:python:
       WSGIPath: run:app
     aws:elasticbeanstalk:application:environment:
       PYTHONPATH: "/var/app/current:$PYTHONPATH"
   ```

2. Create a `requirements.txt` file in your project root if it doesn't exist already:
   ```
   pip freeze > requirements.txt
   ```

3. Ensure your `.gitignore` file includes:
   ```
   *.pyc
   __pycache__/
   instance/
   .env
   ```

## 5. Deploying Your Application

1. Initialize your EB CLI repository:
   ```
   eb init -p python-3.8 flask-mod-template
   ```

2. Create an Elastic Beanstalk environment:
   ```
   eb create flask-mod-template-env
   ```

3. Deploy your application:
   ```
   eb deploy
   ```

4. Open your deployed application:
   ```
   eb open
   ```

## 6. Ensuring Sufficient Storage

1. In the AWS Management Console, go to the EC2 service.
2. Click on "Volumes" in the left sidebar.
3. Find the volume associated with your Elastic Beanstalk environment.
4. Select the volume and click "Actions" > "Modify Volume".
5. Increase the size as needed (e.g., to 20 GB).
6. Click "Modify" to apply the changes.

## 7. Setting Up Automatic Deployment from GitHub

1. In the AWS Management Console, go to the CodePipeline service.
2. Click "Create pipeline".
3. Enter a pipeline name and click "Next".
4. For the source provider, choose "GitHub" and connect your GitHub account.
5. Select your repository and branch, then click "Next".
6. For the build provider, choose "AWS CodeBuild" and create a new build project.
7. For the deploy provider, choose "AWS Elastic Beanstalk" and select your application and environment.
8. Review and create the pipeline.

Now, whenever you push changes to your specified GitHub branch, CodePipeline will automatically deploy the updates to your Elastic Beanstalk environment.

## 8. Monitoring and Maintaining Your Application

1. Use the AWS Elastic Beanstalk console to monitor your application's health, logs, and metrics.
2. Set up CloudWatch alarms for important metrics like CPU usage, memory usage, and request count.
3. Regularly review and update your application's security groups and IAM roles.
4. Keep your application and its dependencies up to date by periodically updating your `requirements.txt` and redeploying.

By following these steps, you should have a fully functional Flask Modular Template application deployed on AWS Elastic Beanstalk with automatic deployment from GitHub and sufficient storage for your needs.