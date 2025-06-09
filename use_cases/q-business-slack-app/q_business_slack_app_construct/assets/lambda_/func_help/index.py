from libs_finder import *


def handler(event, context):
    body = event['body']
    manager = SlackManager(body=body)

    with open('response_block.json') as fd:
        blocks = json.load(fd)

    manager.post_ephemeral(blocks, text='Application help')
