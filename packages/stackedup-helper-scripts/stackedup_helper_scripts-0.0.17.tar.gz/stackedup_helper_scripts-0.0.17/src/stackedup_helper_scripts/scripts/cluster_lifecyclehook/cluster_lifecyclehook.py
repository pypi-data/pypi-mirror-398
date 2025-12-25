"""
Auto Scaling Lifecycle Hook to drain Tasks from your Container Instances
when an Instance is selected for Termination in your Auto Scaling Group.
"""

import boto3, json, logging, os, time

ec2Client = boto3.client("ec2")
ecsClient = boto3.client("ecs")
autoscalingClient = boto3.client("autoscaling")
snsClient = boto3.client("sns")
lambdaClient = boto3.client("lambda")

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    # logger.info(event)

    ecsClusterName = os.environ["CLUSTER"]
    snsTopicArn = event["Records"][0]["Sns"]["TopicArn"]
    snsMessage = json.loads(event["Records"][0]["Sns"]["Message"])

    if "LifecycleHookName" in snsMessage:
        lifecycleHookName = snsMessage["LifecycleHookName"]
        lifecycleActionToken = snsMessage["LifecycleActionToken"]
        asgName = snsMessage["AutoScalingGroupName"]
        ec2InstanceId = snsMessage["EC2InstanceId"]
        checkTasks = tasksRunning(ecsClusterName, ec2InstanceId)

        if checkTasks == 0:
            try:
                response = autoscalingClient.complete_lifecycle_action(
                    LifecycleHookName=lifecycleHookName,
                    AutoScalingGroupName=asgName,
                    LifecycleActionToken=lifecycleActionToken,
                    LifecycleActionResult="CONTINUE",
                )
            except BaseException as e:
                print(str(e))

        elif checkTasks == 1:
            logger.info("Tasks still draining.")


def setContainerInstanceStatusToDraining(ecsClusterName, containerInstanceArn):
    response = ecsClient.update_container_instances_state(
        cluster=ecsClusterName, containerInstances=[containerInstanceArn], status="DRAINING"
    )


def tasksRunning(ecsClusterName, ec2InstanceId):
    ecsContainerInstances = ecsClient.describe_container_instances(
        cluster=ecsClusterName,
        containerInstances=ecsClient.list_container_instances(cluster=ecsClusterName)[
            "containerInstanceArns"
        ],
    )["containerInstances"]

    for i in ecsContainerInstances:
        if i["ec2InstanceId"] == ec2InstanceId:
            if i["status"] == "ACTIVE":
                setContainerInstanceStatusToDraining(ecsClusterName, i["containerInstanceArn"])
                return 1
            if i["status"] == "IMPARED":
                return 0
            if (i["runningTasksCount"] > 0) or (i["pendingTasksCount"] > 0):
                return 1
            return 0
        return 0
    return 0
