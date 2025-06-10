import os


def is_aws_env() -> bool:
    return 'AWS_LAMBDA_FUNCTION_NAME' in os.environ or 'AWS_EXECUTION_ENV' in os.environ


if is_aws_env():
    from app_layer import *
else:
    from q_business_slack_app_construct.assets.lambda_.layer.python.app_layer import *
