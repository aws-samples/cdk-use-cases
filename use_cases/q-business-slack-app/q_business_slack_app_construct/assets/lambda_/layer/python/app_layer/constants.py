from enum import Enum


KEY_USERNAME = 'username'
KEY_CHANNEL_ID = 'channel_id'
KEY_USER_ID = 'user_id'


class Env(Enum):
    PROD = 'prod'
    DEV = 'dev'
