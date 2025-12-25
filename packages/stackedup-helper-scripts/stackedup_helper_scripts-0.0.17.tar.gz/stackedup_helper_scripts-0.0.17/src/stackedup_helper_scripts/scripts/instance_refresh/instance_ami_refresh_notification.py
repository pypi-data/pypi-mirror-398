"""
This script sends a notification to SNS when an ECS cloudformation update is
finished.
"""

import logging
from os import environ

import boto3

sns = boto3.client("sns")

logger = logging.getLogger()
logger.setLevel(logging.INFO)

succeeded_status = [
    "UPDATE_COMPLETE",
]

failed_status = [
    "ROLLBACK_COMPLETE",
    "ROLLBACK_FAILED",
    "UPDATE_FAILED",
    "UPDATE_ROLLBACK_COMPLETE",
    "UPDATE_ROLLBACK_FAILED",
]


def handler(event: dict, context: dict):
    # logger.info(event)

    project = environ["PROJECT"]
    env = environ["ENVIRONMENT_TYPE"]
    stack = environ["STACK"]
    status = event["detail"]["status-details"]["status"]

    if status in succeeded_status:
        text = f"✅ Completed instance refresh for {project} cluster {env}"
        logger.info(text)
        message(text)

    if status in failed_status:
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
