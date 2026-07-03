import boto3
import os

ec2 = boto3.client("ec2")
cloudwatch = boto3.client("cloudwatch")
sns = boto3.client("sns")

SNS_TOPIC = os.environ["SNS_TOPIC_ARN"]


def lambda_handler(event, context):

    instances = ec2.describe_instances()

    report = []

    for reservation in instances["Reservations"]:
        for instance in reservation["Instances"]:

            instance_id = instance["InstanceId"]

            metrics = cloudwatch.get_metric_statistics(
                Namespace="AWS/EC2",
                MetricName="CPUUtilization",
                Dimensions=[
                    {
                        "Name": "InstanceId",
                        "Value": instance_id
                    }
                ],
                StartTime=__import__("datetime").datetime.utcnow() - __import__("datetime").timedelta(days=7),
                EndTime=__import__("datetime").datetime.utcnow(),
                Period=86400,
                Statistics=["Average"]
            )

            datapoints = metrics["Datapoints"]

            if datapoints:

                avg_cpu = sum(d["Average"] for d in datapoints) / len(datapoints)

                if avg_cpu < 10:

                    report.append(
                        f"{instance_id} Average CPU = {avg_cpu:.2f}%"
                    )

    if report:

        sns.publish(
            TopicArn=SNS_TOPIC,
            Subject="AWS Cost Optimization Report",
            Message="\n".join(report)
        )

    return {
        "statusCode": 200,
        "body": report
    }
