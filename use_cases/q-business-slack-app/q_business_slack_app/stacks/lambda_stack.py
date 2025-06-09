from aws_cdk import (
    aws_lambda as _lambda,
    aws_iam as iam,
    NestedStack, Duration, RemovalPolicy,
)
from constructs import Construct
from ..constants import *


class LambdaStack(NestedStack):
    __ARCH = _lambda.Architecture.ARM_64
    __RUNTIME = _lambda.Runtime.PYTHON_3_13
    __ASSETS_PATH = 'q_business_slack_app/assets/lambda_'

    @staticmethod
    def __add_secret_retrieval_permissions(func):
        func.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=['secretsmanager:GetSecretValue'],
                resources=['*'],
            )
        )

    def __create_layer(self, app_name):
        return _lambda.LayerVersion(
            self, 'Layer',
            layer_version_name=app_name,
            compatible_runtimes=[self.__RUNTIME],
            compatible_architectures=[self.__ARCH],
            code=_lambda.Code.from_asset(f'{self.__ASSETS_PATH}/layer'),
            removal_policy=RemovalPolicy.DESTROY
        )

    def __create_aliases(self, func: _lambda.Function) -> dict:
        return {
            ENV_DEV: _lambda.Alias(
                self,
                f'{func.node.id}{ENV_DEV}Alias',
                alias_name=ENV_DEV,
                version=func.latest_version
            ),
            ENV_PROD: _lambda.Alias(
                self,
                f'{func.node.id}{ENV_PROD}Alias',
                alias_name=ENV_PROD,
                version=func.current_version
            )
        }

    def __create_func_handle_slack_event(self, app_name, users_table):
        func = _lambda.Function(
            self, 'FuncHandleSlackEvent',
            code=_lambda.Code.from_asset(f'{self.__ASSETS_PATH}/func_handle_slack_event'),
            handler='index.handler',
            timeout=Duration.minutes(1),
            runtime=self.__RUNTIME,
            architecture=self.__ARCH,
            function_name=f'{app_name}HandleSlackEvent',
            environment={
                f'TABLE_USERS_{ENV_DEV}': users_table[ENV_DEV].table_name,
                f'TABLE_USERS_{ENV_PROD}': users_table[ENV_PROD].table_name
            },
            layers=[self.__layer]
        )

        self.__add_secret_retrieval_permissions(func)
        aliases = self.__create_aliases(func)

        for env in users_table:
            users_table[env].grant_read_write_data(aliases[env])
            aliases[env].grant_invoke(iam.ServicePrincipal('apigateway.amazonaws.com'))

        return func

    def __create_func_handle_slash_command(self, app_name, func_ask, func_help):
        func = _lambda.Function(
            self, 'FuncHandleSlashCommand',
            code=_lambda.Code.from_asset(f'{self.__ASSETS_PATH}/func_handle_slash_command'),
            handler='index.handler',
            timeout=Duration.seconds(20),
            runtime=self.__RUNTIME,
            architecture=self.__ARCH,
            function_name=f'{app_name}HandleSlashCommand',
            environment={
                f'FUNC_ASK': func_ask.function_name,
                f'FUNC_HELP': func_help.function_name,
            },
            layers=[self.__layer]
        )

        self.__add_secret_retrieval_permissions(func)
        aliases = self.__create_aliases(func)

        for env in ENVS:
            aliases[env].grant_invoke(iam.ServicePrincipal('apigateway.amazonaws.com'))

        return func

    def __create_ask_func(self, app_name, func_chat_sync):
        func = _lambda.Function(
            self, 'FuncAsk',
            function_name=f'{app_name}Ask',
            architecture=self.__ARCH,
            runtime=self.__RUNTIME,
            handler='index.handler',
            timeout=Duration.minutes(1),
            code=_lambda.Code.from_asset(f'{self.__ASSETS_PATH}/func_ask'),
            layers=[self.__layer],
            environment={
                'FUNC_CHAT_SYNC': func_chat_sync.function_name,
            }
        )

        self.__add_secret_retrieval_permissions(func)
        aliases = self.__create_aliases(func)

        for env in ENVS:
            aliases[env].grant_invoke(iam.ServicePrincipal('apigateway.amazonaws.com'))

        return func

    def __create_chat_sync_func(self, app_name, q_app, bucket):
        func = _lambda.Function(
            self, 'FuncChatSync',
            function_name=f'{app_name}ChatSync',
            architecture=self.__ARCH,
            runtime=self.__RUNTIME,
            handler='index.handler',
            timeout=Duration.minutes(1),
            code=_lambda.Code.from_asset(f'{self.__ASSETS_PATH}/func_chat_sync'),
            layers=[self.__layer],
            environment={
                'APP_ID': q_app.attr_application_id,
                'BUCKET_NAME': bucket.bucket_name
            }
        )

        func.add_to_role_policy(
            iam.PolicyStatement(
                actions=['qbusiness:*'],
                effect=iam.Effect.ALLOW,
                resources=['*'],
            )
        )

        self.__add_secret_retrieval_permissions(func)
        self.__create_aliases(func)

        return func

    def __create_help_func(self, app_name):
        func = _lambda.Function(
            self, 'FuncHelp',
            function_name=f'{app_name}DisplayHelp',
            architecture=self.__ARCH,
            runtime=self.__RUNTIME,
            handler='index.handler',
            timeout=Duration.seconds(10),
            code=_lambda.Code.from_asset(f'{self.__ASSETS_PATH}/func_help'),
            layers=[self.__layer]
        )

        self.__add_secret_retrieval_permissions(func)
        self.__create_aliases(func)

        return func

    def __init__(self, scope: Construct, construct_id: str, app_name, ddb_stack, qbusiness_stack, s3_stack) -> None:
        super().__init__(scope, construct_id)

        self.__layer = self.__create_layer(app_name)

        self.func_handle_slack_event = self.__create_func_handle_slack_event(app_name, ddb_stack.users_table)
        func_chat_sync = self.__create_chat_sync_func(app_name, qbusiness_stack.app, s3_stack.bucket)
        func_ask = self.__create_ask_func(app_name, func_chat_sync)
        func_help = self.__create_help_func(app_name)
        self.func_handle_slash_command = self.__create_func_handle_slash_command(app_name, func_ask, func_help)

        func_ask.grant_invoke(self.func_handle_slash_command)
        func_help.grant_invoke(self.func_handle_slash_command)
        func_chat_sync.grant_invoke(func_ask)
