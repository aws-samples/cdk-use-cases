import json

from slack_sdk import WebClient
from urllib.parse import unquote
from ..utils.secrets_manager_utils import *


class SlackManager:
    __TOKEN = get_secret_value("SlackToken")

    def __init__(self, body='', channel_id=None, user_id=None, username=None):
        self.__client = WebClient(token=self.__TOKEN)
        self.channel_id = channel_id
        self.user_id = user_id
        self.username = username
        self.__action_payload = {}
        self.__payload = {}

        if body.startswith('payload='):
            body = json.loads(unquote(body[len('payload='):]))

            self.__payload = body
            self.channel_id = body['container']['channel_id']
            self.username = body['user']['username']
            self.user_id = body['user']['id']
        elif body:
            params = body.split('&')

            for param in params:
                key, value = param.split('=')
                self.__payload[key] = unquote(value)

            self.user_id = self.__payload['user_id']
            self.channel_id = self.__payload['channel_id']
            self.username = self.__payload['user_name']
            self.command = self.__payload['command']
            self.text = self.__payload['text'].replace('+', ' ')

            if 'response_url' in self.__payload:
                self.response_url = self.__payload['response_url']

    def get_user_profile(self, user_id):
        return self.__client.users_profile_get(user=user_id)

    def update_app_home(self, user_id, blocks):
        return self.__client.views_publish(user_id=user_id, view=blocks)

    def __send_message(self, blocks, channel_id, user, ephemeral, text=None):
        if text is None:
            text = str(blocks)

        try:
            if ephemeral:
                return self.__client.chat_postEphemeral(
                    channel=channel_id,
                    user=user,
                    blocks=blocks,
                    text=text
                )
            else:
                return self.__client.chat_postMessage(
                    channel=channel_id,
                    blocks=blocks,
                    text=text
                )
        except Exception as e:
            return {
                "ok": False,
                "error": str(e)
            }

    def post_message(self, blocks, text=None, channel_id=None, username=None):
        if channel_id is None:
            channel_id = self.channel_id

        if username is None:
            username = self.username

        return self.__send_message(blocks, channel_id, username, False, text=text)

    def post_ephemeral(self, blocks, text=None, channel_id=None, user_id=None):
        if channel_id is None:
            channel_id = self.channel_id

        if user_id is None:
            user_id = self.user_id

        return self.__send_message(blocks, channel_id, user_id, True, text=text)

    def update_message(self, blocks, ts, text=None, channel_id=None):
        if text is None:
            text = str(blocks)

        if channel_id is None:
            channel_id = self.channel_id

        try:
            return self.__client.chat_update(
                channel=channel_id,
                ts=ts,
                blocks=blocks,
                text=text
            )
        except Exception as e:
            return {
                "ok": False,
                "error": str(e)
            }

    def delete_message(self, ts, channel_id=None):
        if channel_id is None:
            channel_id = self.channel_id

        return self.__client.chat_delete(channel=channel_id, ts=ts)
