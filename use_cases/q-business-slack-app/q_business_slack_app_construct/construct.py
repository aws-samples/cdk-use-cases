from aws_cdk import (
    aws_secretsmanager as secretsmanager,
    CfnParameter
)
from constructs import Construct
from .stacks import *


class QBusinessSlackApp(Construct):
    @staticmethod
    def __create_app_name_parameter(scope):
        return CfnParameter(
            scope, "AppName",
            type="String",
            default="q-business-slack-app",
            allowed_pattern=r"^[a-z\-]+$"
        )

    @staticmethod
    def __create_slack_token_secret(scope):
        secret_value_param = CfnParameter(
            scope, "SlackToken",
            type="String",
            no_echo=True
         )

        secretsmanager.CfnSecret(
            scope, "SlackTokenSecret",
            name='SlackToken',
            secret_string=secret_value_param.value_as_string
        )

    @staticmethod
    def __create_slack_signing_secret(scope):
        secret_value_param = CfnParameter(
            scope, "SlackSigningSecret",
            type="String",
            no_echo=True
        )

        secretsmanager.CfnSecret(
            scope, "SlackSigningSecretSecret",
            name='SlackSigningSecret',
            secret_string=secret_value_param.value_as_string
        )

    def __init__(self, scope: Construct, construct_id: str) -> None:
        super().__init__(scope, construct_id)

        app_name = self.__create_app_name_parameter(scope)
        self.__create_slack_token_secret(scope)
        self.__create_slack_signing_secret(scope)

        qbusiness_stack = QBusinessStack(scope, "QBusinessStack", app_name.value_as_string)
        s3_stack = S3Stack(scope, "S3Stack", app_name.value_as_string)
        ddb_stack = DdbStack(scope, "DynamoDBStack", app_name.value_as_string)
        lambda_stack = LambdaStack(scope, "LambdaStack", app_name.value_as_string, ddb_stack, qbusiness_stack, s3_stack)
        ApiGatewayStack(scope, "ApiGatewayStack", app_name.value_as_string, lambda_stack)
