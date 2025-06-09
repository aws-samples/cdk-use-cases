from aws_cdk import (
    Stack,
)
from constructs import Construct
from q_business_slack_app_construct import QBusinessSlackApp


class MainStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        QBusinessSlackApp(self, "QBusinessSlackApp")
