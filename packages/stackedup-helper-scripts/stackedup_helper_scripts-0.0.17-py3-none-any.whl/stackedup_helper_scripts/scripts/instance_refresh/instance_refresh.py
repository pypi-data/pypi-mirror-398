"""
Initiates a rolling instance refresh for an EC2 Auto Scaling Group, gradually
replacing existing instances with new ones using the current launch
configuration (including the same AMI). This is typically used to replace
potentially degraded instances or to reset OS-level configurations without
changing the overall instance setup.

Environment variables:

(needed)
PROJECT
ENVIRONMENT_TYPE
AUTO_SCALING_GROUP_NAME
TOPIC_ARN

(optional)
REFRESH_INSTANCE_WARMUP
REFRESH_MIN_HEALTHY_PERCENTAGE
REFRESH_SKIP_MATCHING
"""

import logging
import json
import os
import time

from os import environ

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

autoscaling = boto3.client("autoscaling")
sns = boto3.client("sns")


def handler(event: dict, context: dict):
    # logger.info(event)

    project = environ["PROJECT"]
    env = environ["ENVIRONMENT_TYPE"]
    auto_scaling_group_name = environ["AUTO_SCALING_GROUP_NAME"]

    ## Amount of time to wait before replacing instances after new instances
    ## become stable
    refresh_instance_warmup = os.getenv("REFRESH_INSTANCE_WARMUP", 300)

    ## Minimum healthy percentage of the autoscale group before instances get
    ## replaced
    refresh_min_healthy_percentage = os.getenv("REFRESH_MIN_HEALTHY_PERCENTAGE", 100)

    ## Setting to tell autoscale to skip replacing instances that have
    ## matching configurations (mainly the AMI). Since this script is for
    ## forcing a refresh we'll set this to False, to not skip.
    refresh_skip_matching = os.getenv("REFRESH_SKIP_MATCHING", False)

    try:
        refresh_responce = autoscaling.start_instance_refresh(
            AutoScalingGroupName=auto_scaling_group_name,
            Strategy="Rolling",
            Preferences={
                "InstanceWarmup": refresh_instance_warmup,
                "MinHealthyPercentage": refresh_min_healthy_percentage,
                "SkipMatching": refresh_skip_matching,
            },
        )
        text = f"⚙️ Started instance refresh for {project} cluster {env}"
        logger.info(text)
        message(text)
    except Exception as e:
        text = f"Could not start an instance refresh. Error was: \r\r {e}."
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
