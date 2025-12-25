# Stacks Helper Scripts

[![main](https://github.com/ombu/stacks-helper-scripts/actions/workflows/main.yml/badge.svg)](https://github.com/ombu/stacks-helper-scripts/actions/workflows/main.yml)

This repository contains various helper scripts for deploying with OMBU
infrastructure Cloudformation packaged templets.

The target Python version of these scripts is documented in `.python-version`.

## Adding to infrastructure

### Add to the `requirements.txt` with:

```
git+ssh://git@github.com/ombu/stacks-helper-scripts.git@<version>
```

### Add to install MakeFile command:

```
	@$(eval PKG_LOCATION := $(shell pip show stackedup-helper-scripts | grep Location | sed -n 's/Location: //p')/stackedup_helper_scripts)
	@ln -s -f -n ${PKG_LOCATION}/scripts scripts
	@ln -s -f -n ${PKG_LOCATION}/tasks tasks
	@ln -s -f -n ${PKG_LOCATION}/templates templates
```

### Add `/infrastructure/scripts` to .gitignore

### Templete changes:

Rehome `CodeUri` in `Properties` sections to refer to the `infrastructure/scripts`
directory.

## Types of scripts

### account_cost

Account cost alam features a lambda that will get the current estimated
costs of an account and alert a specified SNS Topic.

### cloudformation_update

This script sends a notification to SNS when an ECS deployment is detected from
a CloudFormation update. A starting deployment notification to the SNS topic
then send another notification once the ECS deployment is complete.

### cluster_lifecyclehook

Auto Scaling Lifecycle Hook to drain Tasks from your Container Instances
when an Instance is selected for Termination in your Auto Scaling Group.

### deploy_notification

This script sends a notification to SNS when an ECR image is built.

### email_notification

This script sends email to recipients from an SNS topic.

### force_deploy

When a ECS task is configured to have force deployment of the current tag
this script will restart the ECS task and send a starting deployment
notification to the SNS topic then send another notification once the ECS
deployment is complete.

### instance_refresh

This script refreshes the cloudformation stack with a new AMI.

### reset_task_notification

This script sends a SNS notification when the reset task is requested.

### slack_notification

This script sends a Slack notification to a webhook endpoint from an SNS topic.

### sns_relay

SNS Relay will reformat an alarm messages sent when an alarm triggers and hand
it off to another SNS Topic for delivery.

### web_deploy

When a ECS task is configured to use automatic deployment of the latest tag
this script will restart the ECS task and send a starting deployment
notification to the SNS topic then send another notification once the ECS
deployment is complete.
