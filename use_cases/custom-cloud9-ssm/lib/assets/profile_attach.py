import boto3
import cfnresponse


def handler(event, context):
    if event['RequestType'] == 'Create':
        # Extract context variables
        c9_env_id = event['ResourceProperties']['cloud9_env_id']
        profile_arn = event['ResourceProperties']['profile_arn']

        try:
            client = boto3.client('ec2')

            # Retrieve EC2 instance's identifier
            instance_id = client.describe_instances(
                Filters=[{'Name': 'tag:aws:cloud9:environment', 'Values': [c9_env_id]}]
            )['Reservations'][0]['Instances'][0]['InstanceId']

            # Associate the SSM instance profile
            client.associate_iam_instance_profile(
                IamInstanceProfile={'Arn': profile_arn},
                InstanceId=instance_id
            )

            # Reboot the instance to restart the SSM agent
            client.reboot_instances(
                InstanceIds=[instance_id]
            )
        except Exception as e:
            cfnresponse.send(event, context, cfnresponse.FAILED, {'Error': e.args[0]})
            return

    cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
