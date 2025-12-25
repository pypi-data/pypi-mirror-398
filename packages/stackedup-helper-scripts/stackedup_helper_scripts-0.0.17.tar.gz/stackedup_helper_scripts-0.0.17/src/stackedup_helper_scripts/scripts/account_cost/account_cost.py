"""
Account cost alam features a lambda that will get the current estimated
costs of an account and alert a specified SNS Topic.
"""

import logging
from datetime import date, datetime, timedelta, timezone
from os import environ

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

NAMESPACE = "Billing"
METRIC = "MonthlyForecastCost"


def handler(event: dict, context: dict):
    """
    Get the current forecasted cost of the month and put them into cloudwatch.
    This bypasses the need to deploy in us-east-1 and turn on billing cloudwatch
    metrics which APN accounts and child accounts might not have accessed to.
    """

    # logger.info(event)

    ce = boto3.client("ce")
    cloudwatch = boto3.client("cloudwatch")

    AWS_ACCOUNT = environ["AWS_ACCOUNT"]

    # For get_cost_forecast you must provide a start and end date. However for
    # montly the start date actually has to be the current date regardless of
    # the month granularity.
    start_date = date.today()
    next_month = (start_date.replace(day=28) + timedelta(days=4)).replace(day=1)
    end_date = next_month - timedelta(days=1)

    try:
        forecast = ce.get_cost_forecast(
            TimePeriod={"Start": start_date.strftime("%Y-%m-%d"), "End": end_date.strftime("%Y-%m-%d")},
            Metric="UNBLENDED_COST",
            Granularity="MONTHLY",
        )

        forecast_amount = forecast["ForecastResultsByTime"][0]["MeanValue"]

        if isinstance(forecast_amount, str):
            forecast_amount = float(forecast_amount)

        if isinstance(forecast_amount, float):
            forecast_amount = round(forecast_amount, 2)

        dimensions = [
            {"Name": "Account", "Value": AWS_ACCOUNT},
        ]

        try:
            responce = cloudwatch.put_metric_data(
                Namespace=NAMESPACE,
                MetricData=[
                    {
                        "MetricName": METRIC,
                        "Dimensions": dimensions,
                        "Timestamp": datetime.now(timezone.utc),
                        "Value": forecast_amount,
                    }
                ],
            )
        except Exception as e:
            logger.error(f"Was unable to put cloudwatch metric data: Error was: {e}.")
    except Exception as e:
        logger.error(f"Was unable to get forecast: Error was: {e}.")
