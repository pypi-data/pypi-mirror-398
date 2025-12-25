"""
This script sends a notification to SNS when an ECR image is built.
"""

import logging
from os import environ

import boto3

sns = boto3.client("sns")

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event: dict, context: dict):
    # logger.info(event)

    account_friendly_name = environ["ACCOUNT_FRIENDLY_NAME"]
    repository_name = event["detail"]["repository-name"]
    image_tag = event["detail"]["image-tag"]

    text = f"✅ Built {account_friendly_name} image {repository_name}:{image_tag}"

    logger.info(text)
    message(text)


def message(text: str):
    topic = environ["TOPIC_ARN"]

    try:
        response = sns.publish(TopicArn=topic, Message=text)
        return response
    except Exception as e:
        logger.error(f"SNS messaging failed: Error was: {e}.")
