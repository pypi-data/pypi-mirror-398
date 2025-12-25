"""
This script sends a Slack notification to a Webhook endpoint from an SNS topic.
"""

import json
import logging
import re
from os import environ
from urllib import request

import boto3

ssm = boto3.client("ssm")

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event: dict, context: dict):
    # logger.info(event)

    subject = format_message_text(event["Records"][0]["Sns"]["Subject"])
    body = format_message_text(event["Records"][0]["Sns"]["Message"])

    try:
        logger.info({"subject": subject, "body": body})
        send_message(subject, body)
    except TypeError as e:
        logger.exception("Unable to retrieve message from event", repr(e))
        return


def format_message_text(text: str | None) -> str:
    if text is None:
        text = " "

    """
    Reformat emojis from commandline to their respected utf-8.
    """
    mapping = [
        ("gear_icon", "⚙️"),
        ("white_check_mark_icon", "✅"),
        ("rocket_icon", "🚀"),
        ("large_green_circle_icon", "🟢"),
        ("red_circle_icon", "🔴"),
    ]

    for k, v in mapping:
        text = text.replace(k, v)

    """
    Reformat html links to Slack markdown formatted links.
    """
    convert_links_pattern = '<a href="(.*)">(.*)</a>'
    convert_links_replacement = r"<\1|\2>"
    text = re.sub(convert_links_pattern, convert_links_replacement, text)

    return text


def send_message(subject: str, message: str):
    slack_uri_parameter = environ["SLACK_URI_PARAMETER"]
    slack_uri = ssm.get_parameter(Name=slack_uri_parameter, WithDecryption=True)
    webhook = slack_uri["Parameter"]["Value"]

    post = {"text": f"{message}"}
    json_data = json.dumps(post)

    try:
        req = request.Request(
            webhook,
            data=json_data.encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        request.urlopen(req)
    except Exception as e:
        logger.error(f"Slack messaging failed: Error was: {e}.")
