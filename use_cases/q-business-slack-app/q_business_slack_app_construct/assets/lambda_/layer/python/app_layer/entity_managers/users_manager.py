import boto3
import os

from ..utils.lambda_utils import get_lambda_env
from ..constants import *


boto3_client = boto3.client('dynamodb')
boto3_resource = boto3.resource('dynamodb')


def __get_users_table():
    return os.environ[f'TABLE_USERS_{get_lambda_env()}']


def add_user(username: str, channel_id: str, user_id: str):
    boto3_client.put_item(
        TableName=__get_users_table(),
        Item={
            KEY_USERNAME: {'S': username},
            KEY_CHANNEL_ID: {'S': channel_id},
            KEY_USER_ID: {'S': user_id}
        }
    )


def get_user(username: str):
    table = boto3_resource.Table(__get_users_table())

    response = table.get_item(
        Key={KEY_USERNAME: username}
    )

    return None if 'Item' not in response else response['Item']
