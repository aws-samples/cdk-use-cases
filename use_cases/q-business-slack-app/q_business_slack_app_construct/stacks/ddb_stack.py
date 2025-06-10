from aws_cdk import (
    aws_dynamodb as ddb,
    NestedStack,
    RemovalPolicy
)
from constructs import Construct
from ..constants import *


class DdbStack(NestedStack):
    def __create_users_table(self, app_name):
        return {
            env: ddb.Table(
                self, f'UsersTable{env}',
                table_name=f'{app_name}-UsersTable_{env}',
                removal_policy=RemovalPolicy.DESTROY,
                billing_mode=ddb.BillingMode.PAY_PER_REQUEST,
                partition_key=ddb.Attribute(
                    type=ddb.AttributeType.STRING,
                    name='username'
                )
            )

            for env in ENVS
        }

    def __init__(self, scope: Construct, construct_id: str, app_name) -> None:
        super().__init__(scope, construct_id)

        self.users_table = self.__create_users_table(app_name)
