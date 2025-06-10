import boto3

from libs_finder import *


client = boto3.client('lambda')


@validate_command
def handler(event, context):
    manager = SlackManager(body=event['body'])

    # Trim the text until the first space (which is after the operation) and remove double quotes
    index = manager.text.index(" ") + 2
    text = manager.text[index:-1]

    with open('response_block.json') as fd:
        blocks = json.load(fd)
        blocks[0]['elements'][1]['elements'][0]['text'] = text

    response = manager.post_message(blocks, text='Processing...')

    # Asynchronously invoke the Lambda function that queries the model
    if response['ok']:
        payload = {
            'text': text,
            'ts': response['ts'],
            'channel_id': manager.channel_id
        }

        client.invoke(
            FunctionName=os.environ['FUNC_CHAT_SYNC'] + f':{get_slack_env()}',
            InvocationType='Event',
            Payload=json.dumps(payload).encode('utf-8'),
        )
