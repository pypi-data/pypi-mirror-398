"""
This script sends a notification to SNS when an ECS deployment is detected from
a CloudFormation update. A starting deployment notification to the SNS topic
then send another notification once the ECS deployment is complete.
"""

import logging
import time
from os import environ

import boto3

sns = boto3.client("sns")

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event: dict, context: dict):
    # logger.info(event)

    client = boto3.client("ecs")

    cluster = environ["CLUSTER"]
    service = environ["SERVICE"]
    service_arn = environ["SERVICE_ARN"]
    service_friendly_name = environ["SERVICE_FRIENDLY_NAME"]
    env = environ["ENVIRONMENT_TYPE"]

    time.sleep(30)

    try:
        # Get the current metadata of the service.
        response = client.describe_services(
            cluster=cluster,
            services=[
                service,
            ],
        )
        logger.info(response)

        # Get the current deployment status.
        deployment_status = response["services"][0]["deployments"][0]["rolloutState"]
        logger.info(deployment_status)

        if deployment_status == "IN_PROGRESS":
            # Get the current task definition.
            task = response["services"][0]["taskDefinition"]
            task_response = client.describe_task_definition(
                taskDefinition=task,
            )
            logger.info(task_response)

            # Get the current tag that is being deployed based on the image tag.
            current_tag = task_response["taskDefinition"]["containerDefinitions"][0]["image"]
            current_tag = current_tag.split(":")[-1]
            logger.info(current_tag)

            text = f"⚙️ Started deployment of {current_tag} to {service_friendly_name} instance {env}"
            logger.info(text)
            message(text)

            try:
                logger.info("SERVICE WAITER")
                waiter = client.get_waiter("services_stable")
                waiter.wait(
                    cluster=cluster,
                    services=[
                        service,
                    ],
                    WaiterConfig={"Delay": 15, "MaxAttempts": 60},
                )

                text = f"✅ Completed deployment of {current_tag} to {service_friendly_name} instance {env}"
                logger.info(text)
                message(text)

            except Exception as e:
                text = f"🔴 Deploy failed of {current_tag} to {service_friendly_name} instance {env}"
                logger.error(f"{text} \r Error was: {e}.")
                message(text)
        else:
            text = f"Service did not detect a ECS deployment."
            logger.info(text)

    except Exception as e:
        text = f"Service did not detect a ECS deployment."
        logger.error(f"{text} \r Error was: {e}.")


def message(text: str):
    topic = environ["TOPIC_ARN"]

    try:
        response = sns.publish(TopicArn=topic, Message=text)
        return response
    except Exception as e:
        logger.error(f"SNS messaging failed: Error was: {e}.")
