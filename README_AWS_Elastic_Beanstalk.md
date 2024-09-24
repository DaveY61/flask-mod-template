# AWS Elastic Beanstalk Deployment Guide

This guide provides step-by-step instructions for deploying the Flask Modular Template application using AWS Elastic Beanstalk, including setting up AWS, configuring Elastic Beanstalk, ensuring sufficient storage, and establishing automatic deployment from GitHub.

## Table of Contents
1. [Setting up AWS Account](#1-setting-up-aws-account)
2. [Installing AWS CLI and EB CLI](#2-installing-aws-cli-and-eb-cli)
3. [Configuring AWS Elastic Beanstalk](#3-configuring-aws-elastic-beanstalk)
4. [AWS Elastic Beanstalk Application Files](#4-aws-elastic-beanstalk-application-files)
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

3. Set up IAM User and Policy:

   a. Log in to the AWS Management Console and navigate to the IAM service.

   b. Create a new policy named "ElasticBeanstalkCLI_Policy":
      - Go to "Policies" and click "Create policy"
      - Switch to the JSON tab and paste the following policy:

   <details>
   <summary><strong>📋 Click to view/copy the JSON Policy</strong></summary>

   ```json
   {
      "Version": "2012-10-17",
      "Statement": [
         {
               "Effect": "Allow",
               "Action": [
                  "elasticbeanstalk:*",
                  "ec2:*",
                  "ecs:*",
                  "ecr:*",
                  "elasticloadbalancing:*",
                  "autoscaling:*",
                  "cloudwatch:*",
                  "s3:*",
                  "sns:*",
                  "cloudformation:*",
                  "rds:*",
                  "sqs:*",
                  "logs:*"
               ],
               "Resource": "*"
         },
         {
               "Effect": "Allow",
               "Action": [
                  "iam:ListRoles",
                  "iam:ListInstanceProfiles",
                  "iam:ListInstanceProfilesForRole",
                  "iam:GetInstanceProfile",
                  "iam:GetRole",
                  "iam:CreateRole",
                  "iam:CreateInstanceProfile",
                  "iam:DeleteInstanceProfile",
                  "iam:AddRoleToInstanceProfile",
                  "iam:RemoveRoleFromInstanceProfile",
                  "iam:AttachRolePolicy",
                  "iam:PutRolePolicy",
                  "iam:DeleteRolePolicy"
               ],
               "Resource": [
                  "arn:aws:iam::*:role/aws-elasticbeanstalk-*",
                  "arn:aws:iam::*:role/service-role/aws-elasticbeanstalk-*",
                  "arn:aws:iam::*:instance-profile/aws-elasticbeanstalk-*"
               ]
         },
         {
               "Effect": "Allow",
               "Action": "iam:CreateServiceLinkedRole",
               "Resource": "arn:aws:iam::*:role/aws-service-role/elasticloadbalancing.amazonaws.com/*",
               "Condition": {
                  "StringLike": {
                     "iam:AWSServiceName": "elasticloadbalancing.amazonaws.com"
                  }
               }
         },
         {
               "Effect": "Allow",
               "Action": "iam:PassRole",
               "Resource": [
                  "arn:aws:iam::*:role/aws-elasticbeanstalk-*",
                  "arn:aws:iam::*:role/service-role/aws-elasticbeanstalk-*"
               ],
               "Condition": {
                  "StringEquals": {
                     "iam:PassedToService": [
                           "ec2.amazonaws.com",
                           "elasticbeanstalk.amazonaws.com",
                           "elasticloadbalancing.amazonaws.com",
                           "autoscaling.amazonaws.com"
                     ]
                  }
               }
         }
      ]
   }
   ```
   </details>

      - Click 'Next'
      - Fill in 'Policy name' as "ElasticBeanstalkCLI_Policy"
      - Click 'Create policy'

   c. Create a new IAM user named "ElasticBeanstalkCLI_User":
      - Go to "Users" page and click "Create user"
      - Set the user name to "ElasticBeanstalkCLI_User"
      - Click 'Next'
      - Select "Attach policies directly"
      - Set 'Filter by Type' to 'Customer managed'
      - Select the "ElasticBeanstalkCLI_Policy" policy
      - Click 'Next'
      - Click 'Create user'

   d. Retrieve the AWS access keys:
      - Go to the "Users" page and click to open the "ElasticBeanstalkCLI_User" user page
      - At the top in the "Summary" section, click "Create access key"
      - For Use case, select "Command Line Interface (CLI)"
      - Check the confirmation checkbox (bottom of form)
      - Click 'Next'
      - Click 'Create access key'
      - Download or copy the "Access key" and "Secret access Key"

4. Configure the AWS CLI with your credentials:
   ```
   aws configure
   ```
   Enter your AWS Access Key ID, Secret Access Key, default region, and output format when prompted. Use the access keys you obtained in step 3d.

By following these steps, you'll have set up the necessary IAM user with the appropriate permissions for using the Elastic Beanstalk CLI. The provided policy grants the required permissions for managing Elastic Beanstalk environments and related AWS services.

## 3. Configuring AWS Elastic Beanstalk

1. In the AWS Management Console, go to the IAM service.

2. Create an EC2 policy named "ElasticBeanstalkEC2_Policy":
   - Go to "Policies" and click "Create policy"
   - Switch to the JSON tab and paste the following policy:

   <details>
   <summary><strong>📋 Click to view/copy JSON Policy</strong></summary>

   ```json
   {
      "Version": "2012-10-17",
      "Statement": [
         {
               "Effect": "Allow",
               "Action": [
                  "ec2:DescribeInstances",
                  "ec2:DescribeInstanceStatus",
                  "ec2:GetConsoleOutput",
                  "ec2:AssociateAddress",
                  "ec2:DescribeAddresses",
                  "ec2:DescribeSecurityGroups",
                  "s3:ListBucket",
                  "s3:GetObject",
                  "s3:PutObject",
                  "cloudwatch:PutMetricData",
                  "cloudwatch:GetMetricStatistics",
                  "cloudwatch:DescribeAlarms",
                  "sns:Publish",
                  "sqs:GetQueueAttributes",
                  "sqs:GetQueueUrl",
                  "logs:CreateLogGroup",
                  "logs:CreateLogStream",
                  "logs:PutLogEvents",
                  "elasticloadbalancing:DescribeInstanceHealth",
                  "elasticloadbalancing:DescribeLoadBalancers",
                  "elasticloadbalancing:DescribeTargetHealth",
                  "autoscaling:DescribeAutoScalingGroups",
                  "autoscaling:DescribeAutoScalingInstances",
                  "autoscaling:DescribeScalingActivities",
                  "autoscaling:DescribeNotificationConfigurations"
               ],
               "Resource": "*"
         },
         {
               "Effect": "Allow",
               "Action": "iam:PassRole",
               "Resource": "*",
               "Condition": {
                  "StringEquals": {
                     "iam:PassedToService": "elasticbeanstalk.amazonaws.com"
                  }
               }
         }
      ]
   }
   ```
   </details>

   - Click 'Next'
   - Fill in 'Policy name' as "ElasticBeanstalkEC2_Policy"
   - Click 'Create policy'

3. Create two roles:

   a. Create an EC2 Role named "aws-elasticbeanstalk-ec2-role":
      - Go to "Roles" and click "Create role"
      - Choose AWS service and EC2 as the use case
      - Click 'Next'
      - Set 'Filter by Type' to 'Customer managed'
      - Select the "ElasticBeanstalkEC2_Policy" policy
      - Click 'Next'
      - Fill in role name: "aws-elasticbeanstalk-ec2-role"
      - Click 'Create role'

   b. Create a Service Role named "aws-elasticbeanstalk-service-role":
      - Go to "Roles" and click "Create role"
      - Choose AWS service and Elastic Beanstalk as the use case
      - Keep the default choice of "Elastic Beanstalk - Customizable"
      - Click 'Next'
      - Keep the selected default permissions
      - Click 'Next'
      - Fill in role name: "aws-elasticbeanstalk-service-role"
      - Click 'Create role'

4. In the AWS Management Console, go to the Elastic Beanstalk service.

5. Click "Create application".

6. Step 1: Configure environment:
   - Keep the selected 'Web server environment' 
   - Fill in the Application name: `flask-mod-template`
   - Keep the auto-filled Environment name: `Flask-mod-template-env` (automatically filled)
   - For Platform, choose "Python" and select the appropriate Python version.
   - For Application code, keep the "Sample application" (for now)
   - Click 'Next'

10. Step 2: Configure service access:
    - Ensure "Use an existing service role" is selected
    - Select the "aws-elasticbeanstalk-service-role" you created earlier
    - For EC2 instance profile, select the "aws-elasticbeanstalk-ec2-role" you created earlier
    - Click 'Next'

12. On the next page, click 'Skip to review'.

13. On the review page, review all the settings and click 'Submit' to create the application and the environment for the "flask-mod-application".

These steps will set up the necessary policies and roles, and guide you through the process of creating an Elastic Beanstalk environment with the appropriate permissions and configurations.

## 4. AWS Elastic Beanstalk Application Files

To prepare your Flask Modular Template application for deployment on AWS Elastic Beanstalk, you need to ensure the following files are in place:

1. `requirements.txt` (root directory)
   - Lists all Python dependencies
   - Create this file if it doesn't exist:
     ```
     pip freeze > requirements.txt
     ```

   **NOTE:** Be sure you include "gunicorn==20.1.0" in the requirements.txt which is needed by Elastic Beanstalk.

2. `.ebextensions/01_flask.config` (in .ebextensions folder)
   - Contains AWS Elastic Beanstalk configuration
   - Create this file with the following content:
     ```yaml
     option_settings:
       aws:elasticbeanstalk:container:python:
         WSGIPath: run_aws:application
       aws:elasticbeanstalk:application:environment:
         PYTHONPATH: "/var/app/current:$PYTHONPATH"
     ```

3. `Procfile` (root directory)
   - Specifies the command to run your application
   - Content:
     ```
     web: gunicorn --bind 0.0.0.0:8000 run_aws:application
     ```

4. `run_aws.py` (root directory)
   - Entry point for your application on AWS
   - Content:
     ```python
     from app.app import app as application

     if __name__ == "__main__":
         application.run()
     ```

5. `.elasticbeanstalk/config.yml` (in .elasticbeanstalk folder)
   - Contains EB CLI configuration (optional, but useful for deployment settings)
   - This file is typically created when you run `eb init`

6. `.ebignore` (root directory, if needed)
   - Specifies files to ignore during deployment (similar to .gitignore)
   - Create this file if you need to exclude certain files from deployment

Ensure your project structure looks like this:

```
your_project/
├── .ebextensions/
│   └── 01_flask.config
├── .elasticbeanstalk/
│   └── config.yml
├── app/
│   └── app.py (and other application files)
├── .gitignore
├── .ebignore (if needed)
├── requirements.txt
├── Procfile
└── run_aws.py
```

All of these files, except for any local-only configuration files, should be committed to your repository and will be used during the Elastic Beanstalk deployment process.

Remember:
- The `.elasticbeanstalk/config.yml` file is created when you initialize your EB environment with `eb init`. It's useful to commit this file as it stores your EB environment settings.
- If you have sensitive information (like API keys), use environment variables in Elastic Beanstalk instead of hardcoding them in your files.
- Make sure your `.gitignore` file is set up to exclude any local-only files or directories (like virtual environments, `.env` files, etc.).

When you run `eb deploy`, Elastic Beanstalk will use these files to set up and run your application in the cloud environment.

## 5. Deploying Your Application

1. Initialize your EB CLI repository:
   ```
   eb init -p python-3.11 flask-mod-template
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