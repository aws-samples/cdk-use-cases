import boto3

from libs_finder import *


client = boto3.client('lambda')


@verify_slack_request
@validate_command
def handler(event, context):
    opp_to_function_mapping = {
        OP_ASK: os.environ['FUNC_ASK'],
        OP_HELP: os.environ['FUNC_HELP'],
    }

    manager = SlackManager(body=event['body'])
    operation, _, _ = parse_slash_command(manager.text)

    # Invoke the target Lambda function asynchronously using the Slack environment set by the user
    client.invoke(
        FunctionName=opp_to_function_mapping[operation] + f':{get_slack_env()}',
        InvocationType='Event',
        Payload=json.dumps({'body': event['body']}).encode('utf-8')
    )

    return {
        'statusCode': 200
    }
