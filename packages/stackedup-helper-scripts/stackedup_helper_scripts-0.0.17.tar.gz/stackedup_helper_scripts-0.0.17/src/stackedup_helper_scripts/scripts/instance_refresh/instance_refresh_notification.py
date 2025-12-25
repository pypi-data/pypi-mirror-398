"""
This script sends a notification to SNS when an instance refresh is finished.
"""

import logging
from os import environ

import boto3

sns = boto3.client("sns")

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event: dict, context: dict):
    # logger.info(event)

    project = environ["PROJECT"]
    env = environ["ENVIRONMENT_TYPE"]
    auto_scaling_group_name = environ["AUTO_SCALING_GROUP_NAME"]
    status = event["detail-type"]

    if status == "EC2 Auto Scaling Instance Refresh Succeeded":
        text = f"✅ Completed instance refresh for {project} cluster {env}"
        logger.info(text)
        message(text)

    if status == "EC2 Auto Scaling Instance Refresh Failed":
        text = f"🔴 Instance refresh failed for {project} cluster {env}"
        logger.error(text)
        message(text)


def message(text: str):
    topic = environ["TOPIC_ARN"]

    try:
        response = sns.publish(TopicArn=topic, Message=text)
        return response
    except Exception as e:
        text = f"SNS messaging failed: Error was: \r\r {e}"
        logger.error(text)
