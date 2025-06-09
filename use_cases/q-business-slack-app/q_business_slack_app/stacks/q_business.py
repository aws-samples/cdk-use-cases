from aws_cdk import (
    aws_qbusiness as qbusiness,
    NestedStack
)
from constructs import Construct


class QBusinessStack(NestedStack):
    def __create_application(self, app_name):
        app = qbusiness.CfnApplication(
            self,'QBusinessApplication',
            display_name=app_name,
            identity_type='ANONYMOUS',
            auto_subscription_configuration=qbusiness.CfnApplication.AutoSubscriptionConfigurationProperty(
                default_subscription_type="Q_BUSINESS",
                auto_subscribe='DISABLED'
            )
        )

        return app

    def __init__(self, scope: Construct, construct_id: str, app_name) -> None:
        super().__init__(scope, construct_id)

        self.app = self.__create_application(app_name)
