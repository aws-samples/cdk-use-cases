import boto3

from libs_finder import *
from string import Template


__MAX_SOURCES = 3
client = boto3.client('qbusiness')


# -------------------- BLOCK BUILDING -------------------- #
def __build_divider_block():
    with open('blocks/divider.json') as f:
        return json.loads(f.read())


def __build_sources_block():
    with open('blocks/sources.json') as f:
        return json.loads(f.read())


def __build_source_block(source_name, source_url):
    with open('blocks/source.json') as f:
        block = Template(f.read())
        block = block.substitute({
            'SOURCE_NAME': source_name,
            'SOURCE_URL': source_url
        })

        return json.loads(block)


def __build_response_blocks(source_attributions, system_message, text):
    with open('blocks/response.json') as fd:
        blocks = json.load(fd)

    blocks[0]['text']['text'] = text
    blocks[1]['text']['text'] = system_message

    if source_attributions:
        blocks.append(__build_divider_block())
        blocks.append(__build_sources_block())

        for a in source_attributions:
            blocks[-1]['elements'][1]['elements'].append(
                __build_source_block(a['title'], a['url'])
            )

    return blocks


def __build_error_response_blocks(text, error):
    with open('blocks/error_response.json') as fd:
        blocks = json.load(fd)
        blocks[0]['elements'][0]['elements'][1]['text'] = error
        blocks[0]['elements'][1]['elements'][0]['text'] = text

    return blocks
# -------------------- /BLOCK BUILDING -------------------- #


def __extract_sources(attributions):
    titles = set()
    sources = []

    for a in attributions:
        if not a['url'].startswith(f'https://{os.environ["BUCKET_NAME"]}') and a['title'] not in titles:
            sources.append(a)
            titles.add(a['title'])

    return sources[:__MAX_SOURCES]


def handler(event, context):
    # Retrieve invocation arguments
    text = event['text']
    ts = event['ts']
    channel_id = event['channel_id']

    try:
        # Perform a query to the LLM
        response = client.chat_sync(
            applicationId=os.environ['APP_ID'],
            userMessage=text,
            chatMode='RETRIEVAL_MODE'
        )

        # Extract the source attributions, and keep only those that come from the crawler
        source_attributions = __extract_sources(response['sourceAttributions'])

        response = SlackManager().update_message(
            blocks=__build_response_blocks(source_attributions, response['systemMessage'], text),
            ts=ts,
            channel_id=channel_id,
            text=response['systemMessage']
        )

        if not response['ok']:
            raise KeyError(response['error'])
    except Exception as e:
         SlackManager().update_message(
            blocks=__build_error_response_blocks(text, e.args[0]),
            ts=event['ts'],
            channel_id=channel_id,
            text=e.args[0]
        )
