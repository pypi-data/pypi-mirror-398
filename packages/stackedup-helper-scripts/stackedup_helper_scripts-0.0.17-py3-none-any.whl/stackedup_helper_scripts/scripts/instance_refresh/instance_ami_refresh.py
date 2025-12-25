"""
Updates EC2 instances AMIs in ECS clusters with newer AMI recommendation from
AWS.

This script automates the process of updating the Amazon Machine Image (AMI)
used by EC2 instances in an ECS cluster. It checks for the latest recommended
AMI (provided by AWS for ECS-optimized instances), compares it to the AMI
currently used in the CloudFormation stack, and if a newer AMI is available,
triggers a CloudFormation stack update to cycle in the new AMI. This is
intended to be scheduled during a maintenance window (e.g., via EventBridge).

Environment variables:

(needed)
PROJECT
ENVIRONMENT_TYPE
STACK
TOPIC_ARN

(optional)
ECS_LOGICAL_RESOURCE_ID
PLATFORM
ARCH
"""

import logging
import json
import os
import time

from os import environ
from time import sleep

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

cloudformation = boto3.client("cloudformation")
ec2 = boto3.client("ec2")
sns = boto3.client("sns")
ssm = boto3.client("ssm")


def handler(event: dict, context: dict):
    # logger.info(event)

    project = environ["PROJECT"]
    env = environ["ENVIRONMENT_TYPE"]
    stack = environ["STACK"]
    arch = os.getenv("ARCH", "x86_64")
    platform = os.getenv("PLATFORM", "amazon-linux-2023")
    ecs_logical_resource_id = os.getenv("ECS_LOGICAL_RESOURCE_ID", "ECS")

    current_ami = get_ecs_stack_current_ami(stack, ecs_logical_resource_id)
    current_ami_arch = current_ami["Architecture"]
    current_ami_imageid = current_ami["ImageId"]

    recommended_ami = get_recommended_ami(get_ami_parameter_name(arch, platform))
    recommended_ami_arch = recommended_ami["Architecture"]
    recommended_ami_imageid = recommended_ami["ImageId"]

    # Check ECS Stack drift status.
    ecs_stack = get_ecs_stack_information(stack, ecs_logical_resource_id)
    check_stack_drift_status(ecs_stack)

    # Before cloudformation update, see if it's needed.
    if current_ami_arch == recommended_ami_arch and current_ami_imageid != recommended_ami_imageid:
        stack_information = get_stack_information(stack)
        stack_parameters = get_stack_parameters(stack_information)
        update_cloudformation_stack(stack, stack_parameters)
        text = f"✅ Updated the AMI for {project} cluster {env} from {current_ami_imageid} to {recommended_ami_imageid}"
        logger.info(text)
        message(text)
    else:
        text = f"Current AMI {current_ami_imageid} already matched recommended AMI {recommended_ami_imageid} for {project} cluster {env}"
        logger.info(text)


def get_ami_parameter_name(arch: str, platform: str) -> str:
    ami_parameter_name = "/aws/service/ecs/optimized-ami/" + platform
    if arch != "x86_64":
        ami_parameter_name = ami_parameter_name + "/" + arch
    return ami_parameter_name + "/recommended"


def get_ami_details(ami_id: str) -> str:
    try:
        # Include lookups for older AMIs for older stacks.
        ami_data = ec2.describe_images(ImageIds=[ami_id], IncludeDeprecated=True, IncludeDisabled=True)
        return ami_data["Images"][0]
    except Exception as e:
        text = f"Could not retrieve recommended AMI data for {ami_id}. Error was: \r\r {e}."
        logger.error(text)
        exit()


def get_recommended_ami(ami_parameter_name: str) -> dict:
    try:
        recommended = ssm.get_parameters(Names=[ami_parameter_name])
        data = json.loads(recommended["Parameters"][0]["Value"])
        return get_ami_details(data["image_id"])
    except Exception as e:
        text = f"Could not retrieve recommended AMI details. Error was: \r\r {e}."
        logger.error(text)
        exit()


def get_stack_information(stack: str) -> dict:
    try:
        return cloudformation.describe_stacks(StackName=stack)
    except Exception as e:
        text = f"Could not retrieve stack information. Error was: \r\r {e}."
        logger.error(text)
        exit()


def get_stack_resources(stack: str) -> list:
    resources = [stack]
    try:
        # Look for only nested stacks.
        response = cloudformation.describe_stack_resources(StackName=stack)
        for resource in response["StackResources"]:
            if resource["ResourceType"] == "AWS::CloudFormation::Stack":
                resources.append(resource["PhysicalResourceId"])
        return resources
    except Exception as e:
        text = f"Could not retrieve stack resource information. Error was: \r\r {e}."
        logger.error(text)
        exit()


def get_stack_parameters(stack_information: dict) -> dict:
    try:
        return stack_information["Stacks"][0]["Parameters"]
    except Exception as e:
        text = f"Could not retrieve stack parameters. Error was: \r\r {e}."
        logger.error(text)
        exit()


def get_ecs_stack_information(stack: str, ecs_logical_resource_id: str) -> str:
    try:
        response = cloudformation.describe_stack_resource(
            StackName=stack, LogicalResourceId=ecs_logical_resource_id
        )
        return response["StackResourceDetail"]["PhysicalResourceId"]
    except Exception as e:
        text = f"Could not retrieve stack information. Error was: \r\r {e}."
        logger.error(text)
        exit()


def get_ecs_stack_current_ami(stack: str, ecs_logical_resource_id: str) -> dict:
    try:
        ami_id = False
        ecs_stack = get_ecs_stack_information(stack, ecs_logical_resource_id)
        stack_information = get_stack_information(ecs_stack)
        parameters = get_stack_parameters(stack_information)
        for parameter in parameters:
            if parameter["ParameterKey"] == "AmiId":
                # Look for only resolved value if actually specified don't update.
                ami_id = parameter["ResolvedValue"]

        if ami_id:
            response = get_ami_details(ami_id)
            return response
        else:
            text = f"Could not retrieve ECS stack AMI information Error was: \r\r {e}."
            logger.error(text)
            exit()
    except Exception as e:
        text = f"Could not retrieve ECS stack AMI information Error was: \r\r {e}."
        logger.error(text)
        exit()


def check_stack_drift_status(stack: str):
    project = environ["PROJECT"]
    env = environ["ENVIRONMENT_TYPE"]

    resources = get_stack_resources(stack)
    for resource in resources:
        resource_status = get_stack_drift_status(resource)
        if resource_status != "IN_SYNC":
            text = f"{resource} was not IN_SYNC."
            logger.error(text)
            text = f"🔴 Updating the AMI for {project} cluster {env} failed due to {resource} not in sync"
            logger.error(text)
            message(text)
            exit()
        else:
            text = f"{resource} was IN_SYNC."
            logger.info(text)
    text = f"All resources were IN_SYNC."
    logger.info(text)


def get_stack_drift_status(stack: str) -> str:
    """
    Drift status waiter.
    """
    check_timeout = 5
    drift_status = "NOT_CHECKED"
    finished = False

    try:
        response = cloudformation.detect_stack_drift(StackName=stack)
        stack_drift_detection_id = response["StackDriftDetectionId"]
        while finished is False:
            try:
                drift_status_response = cloudformation.describe_stack_drift_detection_status(
                    StackDriftDetectionId=stack_drift_detection_id
                )
                detection_status = drift_status_response["DetectionStatus"]

                if detection_status != "DETECTION_IN_PROGRESS":
                    finished = True
                    drift_status = drift_status_response["StackDriftStatus"]
                sleep(check_timeout)
            except Exception as e:
                text = f"Could not get drift status. Error was: \r\r {e}."
                logger.error(text)
        return drift_status
    except Exception as e:
        text = f"Could not verify drift status. Error was: \r\r {e}."
        logger.error(text)
        exit()


def update_cloudformation_stack(stack: str, stack_parameters: dict):
    try:
        response = cloudformation.update_stack(
            StackName=stack, UsePreviousTemplate=True, Parameters=stack_parameters
        )
        text = f"Issuing a new cloudformation update. \r\r {response}"
        logger.info(text)
    except Exception as e:
        text = f"Could not update cloudformation. Error was: \r\r {e}."
        logger.error(text)
        exit()


def message(text: str):
    topic = environ["TOPIC_ARN"]

    try:
        response = sns.publish(TopicArn=topic, Message=text)
        return response
    except Exception as e:
        text = f"SNS messaging failed: Error was: \r\r {e}"
        logger.error(text)
