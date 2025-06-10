import os

from ..constants import *


__ENV = Env.PROD


def __is_aws_env() -> bool:
    return 'AWS_LAMBDA_FUNCTION_NAME' in os.environ or 'AWS_EXECUTION_ENV' in os.environ


def __executed_lambda_test() -> bool:
    return 'AWS_LAMBDA_FUNCTION_VERSION' in os.environ and \
        os.environ['AWS_LAMBDA_FUNCTION_VERSION'] == '$LATEST'


def __in_dev_environment() -> bool:
    return not __is_aws_env() or __executed_lambda_test()


def __set_env(env: Env) -> None:
    global __ENV
    __ENV = env


def get_lambda_env() -> str:
    return __ENV.value


if __in_dev_environment():
    __set_env(__ENV.DEV)
else:
    __set_env(__ENV.PROD)