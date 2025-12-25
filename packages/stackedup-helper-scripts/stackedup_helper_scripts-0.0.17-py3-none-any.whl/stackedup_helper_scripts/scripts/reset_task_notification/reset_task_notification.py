"""
This script sends a SNS notification when the reset task is requested.
"""

import logging
from os import environ

import boto3

sns = boto3.client("sns")

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event: dict, context: dict):
    # logger.info(event)

    app = environ["APP"]
    env = environ["ENVIRONMENT_TYPE"]
    task_name = environ["TASK_NAME"]

    text = f"Ran task *{task_name}* on {app} environment *{env}* 🚀"

    logger.info(text)
    message(text)


def message(text: str):
    topic = environ["TOPIC_ARN"]

    try:
        response = sns.publish(TopicArn=topic, Message=text)
        return response
    except Exception as e:
        logger.error(f"SNS messaging failed: Error was: {e}.")
