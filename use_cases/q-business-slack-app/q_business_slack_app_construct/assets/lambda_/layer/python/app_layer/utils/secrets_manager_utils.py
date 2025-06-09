import boto3


client = boto3.client('secretsmanager')


def get_secret_value(secret_name):
    return client.get_secret_value(
        SecretId=secret_name
    )['SecretString']
