import boto3
import cfnresponse
import time


def is_association_started(association_id):
    client = boto3.client('ssm')

    # Retrieve the execution history of the association
    response = client.describe_association_executions(
        AssociationId=association_id,
        Filters=[
            {
                'Key': 'Status',
                'Value': 'Success',
                'Type': 'EQUAL'
            }
        ]
    )

    # There are no executions yet
    if 'AssociationExecutions' not in response or not response['AssociationExecutions']:
        return False

    # Retrieve the targets of the execution to see if the SSM agent has picked up the EC2 instance yet
    response = client.describe_association_execution_targets(
        AssociationId=association_id,
        ExecutionId=response['AssociationExecutions'][0]['ExecutionId']
    )

    return 'AssociationExecutionTargets' in response and response['AssociationExecutionTargets']


def handler(event, context):
    if event['RequestType'] == 'Create':
        # Extract context variables
        stack_id = event['ResourceProperties']['stack_id']
        profile_arn = event['ResourceProperties']['profile_arn']
        association_id = event['ResourceProperties']['association_id']

        try:
            client = boto3.client('ec2')

            # Retrieve EC2 instance's identifier
            print('Retrieving EC2 instance Id')

            instance_id = client.describe_instances(
                Filters=[{'Name': 'tag:stack-id', 'Values': [stack_id]}]
            )['Reservations'][0]['Instances'][0]['InstanceId']

            # Associate the SSM instance profile
            print('Associating the SSM instance profile to the instance')

            client.associate_iam_instance_profile(
                IamInstanceProfile={'Arn': profile_arn},
                InstanceId=instance_id
            )

            # Reboot the instance to restart the SSM agent
            print('Rebooting the instance so that the SSM agent picks up the association')

            client.reboot_instances(
                InstanceIds=[instance_id]
            )

            # Wait for the SSM association to be started
            while True:
                print('Waiting for the association to be started')

                if is_association_started(association_id):
                    break
                else:
                    time.sleep(5)
        except Exception as e:
            cfnresponse.send(event, context, cfnresponse.FAILED, {'Error': e.args[0]})
            return

    cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
