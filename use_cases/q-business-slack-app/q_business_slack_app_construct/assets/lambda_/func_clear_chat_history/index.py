import time

from slack_sdk.errors import SlackApiError
from libs_finder import *


def handler(event, context):
    manager = SlackManager(channel_id='D090UUNS000')
    message_urls = [
        'https://amzn-aws.slack.com/archives/D090UUNS000/p1749383429772189'
    ]

    for url in message_urls:
        ts = url.split('/')[-1][1:]
        ts = ts[:-6] + '.' + ts[-6:]

        try:
            manager.delete_message(ts)
        except SlackApiError:
            continue
        finally:
            time.sleep(1)


if __name__ == '__main__':
    handler({}, None)
