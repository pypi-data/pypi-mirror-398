"""
SNS Relay will reformat an alarm messages sent when an alarm triggers and hand
it off to another SNS Topic for delivery.
"""

import logging
import json
import time
from os import environ

import boto3

sns = boto3.client("sns")

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event: dict, context: dict):
    """
    Grabs the current threshold datapoint that breached and replaces the
    <currentvalue> of the alarm description. Also appends the alarm
    link at the end.
    """

    # logger.info(event)

    cloudwatch = boto3.client("cloudwatch")

    region = environ["AWS_DEFAULT_REGION"]
    record = event["Records"][0]

    alarm_message = json.loads(record["Sns"]["Message"])
    alarm_name = alarm_message["AlarmName"]
    alarm_description = alarm_message["AlarmDescription"]
    alarm_link = f"https://console.aws.amazon.com/cloudwatch/home?{region}#alarmsV2:alarm/{alarm_name}"

    # We'll assume that when this lambda is run that the alarm is passed the
    # threshold and that the current alarm data should be in the alarm state.
    describe_alarm_response = cloudwatch.describe_alarms(AlarmNames=[alarm_name])
    state_reason_data = json.loads(describe_alarm_response["MetricAlarms"][0]["StateReasonData"])
    logger.info(state_reason_data)
    recent_datapoint = state_reason_data["recentDatapoints"][0]

    if isinstance(recent_datapoint, float):
        recent_datapoint = round(recent_datapoint, 2)

    alarm_replacement = str(recent_datapoint)
    alarm_description = alarm_description.replace("<currentvalue>", alarm_replacement)

    text = f'🔔 {alarm_description} <a href="{alarm_link}">View alarm</a>'

    logger.info(text)
    message(text)


def message(text: str):
    topic = environ["TOPIC_ARN"]

    try:
        response = sns.publish(TopicArn=topic, Message=text)
        return response
    except Exception as e:
        logger.error(f"SNS messaging failed: Error was: {e}.")
