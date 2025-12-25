"""
When a ECS task is configured to use automatic deployment of the latest tag
this script will restart the ECS task and send a starting deployment
notification to the SNS topic then send another notification once the ECS
deployment is complete.
"""

import logging
from os import environ

import boto3

sns = boto3.client("sns")

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event: dict, context: dict):
    # logger.info(event)

    client = boto3.client("ecs")

    app = environ["APP"]
    cluster = environ["CLUSTER"]
    service = environ["SERVICE"]
    service_arn = environ["SERVICE_ARN"]
    service_friendly_name = environ["SERVICE_FRIENDLY_NAME"]
    current_tag = environ["CURRENT_TAG"]
    env = environ["ENVIRONMENT_TYPE"]

    logger.info(
        f"App: {app} \r Cluster: {cluster} \r Service: {service_friendly_name} \r Service Name: {service} \r Service ARN: {service_arn} \r Current Tag: {current_tag} \r Environment: {env}"
    )

    if current_tag == "latest":
        client.update_service(
            cluster=cluster,
            service=service_arn,
            forceNewDeployment=True,
        )

        text = f"⚙️ Started deployment of {current_tag} to {service_friendly_name} instance {env}"
        logger.info(text)
        message(text)

        try:
            waiter = client.get_waiter("services_stable")
            waiter.wait(
                cluster=cluster,
                services=[
                    service,
                ],
                WaiterConfig={"Delay": 15, "MaxAttempts": 120},
            )

            text = f"✅ Completed deployment of {current_tag} to {service_friendly_name} instance {env}"

            logger.info(text)
            message(text)

        except Exception as e:
            text = f"🔴 Deploy failed of {current_tag} to {service_friendly_name} instance {env}"
            logger.error(f"{text} \r Error was: {e}.")
            message(text)


def message(text: str):
    topic = environ["TOPIC_ARN"]

    try:
        response = sns.publish(TopicArn=topic, Message=text)
        return response
    except Exception as e:
        logger.error(f"SNS messaging failed: Error was: {e}.")
