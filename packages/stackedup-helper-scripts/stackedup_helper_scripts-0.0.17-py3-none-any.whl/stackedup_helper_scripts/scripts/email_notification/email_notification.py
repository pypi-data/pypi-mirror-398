"""
This script sends email to recipients from an SNS topic.
"""

import logging
from os import environ

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event: dict, context: dict):
    # logger.info(event)

    subject = format_message_text(event["Records"][0]["Sns"]["Subject"]).strip()
    body = format_message_text(event["Records"][0]["Sns"]["Message"]).strip()

    if not subject:
        subject = body
        body = ""

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

    return text


def send_message(subject: str, message: str):
    sender = environ["EMAIL_SENDER"]
    recipients = environ["EMAIL_RECIPIENT"].split(",")

    html_email_content = f"<html><head></head><p>{message}</p></body></html>"

    try:
        client = boto3.client("ses", region_name=environ["AWS_REGION"])
        client.send_email(
            Destination={
                "ToAddresses": recipients,
            },
            Message={
                "Subject": {
                    "Charset": "UTF-8",
                    "Data": subject,
                },
                "Body": {
                    "Html": {
                        "Charset": "UTF-8",
                        "Data": html_email_content,
                    }
                },
            },
            Source=sender,
        )
    except Exception as e:
        logger.error(f"Email messaging failed: Error was: {e}.")
