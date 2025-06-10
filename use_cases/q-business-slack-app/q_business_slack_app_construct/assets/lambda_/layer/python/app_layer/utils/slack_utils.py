import json
import shlex
import hmac
import hashlib
import time

from .slack_operations_definition import *
from ..entity_managers import SlackManager
from ..constants import *
from ..utils.secrets_manager_utils import *


__ENV = Env.PROD

__INPUT_ERROR_MESSAGE = f'Invalid input. To view the list of available operations, type {SLASH_COMMAND} {OP_HELP}.'
__PERMISSIONS_ERROR_MESSAGE = "You don't have permission to access this resource."
__UNRECOGNISED_OPTION_ERROR_MESSAGE = "Unrecognized option \"{}\" for operation \"{}\"."
__MISSING_OPTION_ERROR_MESSAGE = "Missing required option \"{}\" for operation \"{}\"."
__OP_HELP_ERROR_MESSAGE = f'The "{OP_HELP}" operation does not accept any arguments. Simply type {SLASH_COMMAND} {OP_HELP}.'
__OP_ASK_ERROR_MESSAGE = f'The "{OP_ASK}" operation accepts a single argument, which is the question you want to ask wrapped in double quotes. For instance, {SLASH_COMMAND} {OP_ASK} "[Your question]".'
__OP_ASK_LENGTH_ERROR_MESSAGE = 'The input text is too short.'

__SIGNING_SECRET = get_secret_value("SlackSigningSecret")


def __validate_operation_args(operation, args, options):
    if operation == OP_HELP:
        if args:
            raise ValueError(__OP_HELP_ERROR_MESSAGE)
    elif operation == OP_ASK:
        if len(args) != 1:
            raise ValueError(__OP_ASK_ERROR_MESSAGE)
        elif len(args[0]) < OP_DEFINITION[__ENV.value][OP_ASK]['minQuestionLength'] + 2:
            raise ValueError(__OP_ASK_LENGTH_ERROR_MESSAGE)

    for key in options:
        if key not in OP_DEFINITION[__ENV.value][operation]['acceptedOptions']:
            raise ValueError(__UNRECOGNISED_OPTION_ERROR_MESSAGE.format(key, operation))

    for req_option in OP_DEFINITION[__ENV.value][operation]['requiredOptions']:
        if req_option not in options:
            raise ValueError(__MISSING_OPTION_ERROR_MESSAGE.format(req_option, operation))


def __set_env(options):
    global __ENV

    if OPTION_DEV in options:
        __ENV = Env.DEV


def get_slack_env() -> str:
    return __ENV.value


def parse_slash_command(text):
    tokens = shlex.split(text)

    args = [arg for arg in tokens if not arg.startswith('--')]
    operation = args.pop(0) if args else None

    # Build key-value pairs with the options
    options = [arg for arg in tokens if arg.startswith('--')]
    options = {
        op if '=' not in op else op.split('=')[0]: '' if '=' not in op else op.split('=')[1]
        for op in options
    }

    return operation, args, options


def validate_command(func):
    def inner_function(*args, **kwargs):
        manager = SlackManager(body=args[0]['body'])

        try:
            operation, op_args, options = parse_slash_command(manager.text)
            __set_env(options)

            if operation is None or operation not in OP_DEFINITION[__ENV.value]:
                raise ValueError(__INPUT_ERROR_MESSAGE)

            if (OP_DEFINITION[__ENV.value][operation]['allowedUsers'][0] != '*' and
                    manager.username not in OP_DEFINITION[__ENV.value][operation]['allowedUsers']):
                raise ValueError(__PERMISSIONS_ERROR_MESSAGE)

            __validate_operation_args(operation, op_args, options)
        except ValueError as e:
            return {
                'statusCode': 200,
                "headers": {
                    "Content-Type": "application/json"
                },
                "body": json.dumps({
                    'text': e.args[0],
                    "response_type": "ephemeral"
                })
            }

        return func(*args, **kwargs)

    return inner_function


def verify_slack_request(func):
    def inner_function(*args, **kwargs):
        headers = args[0]['headers']
        body = args[0]['body']

        request_timestamp = headers.get('X-Slack-Request-Timestamp', headers.get('x-slack-request-timestamp'))
        slack_signature = headers.get('X-Slack-Signature', headers.get('x-slack-signature'))

        try:
            if not request_timestamp or not slack_signature:
                raise ValueError()

            # The request timestamp is more than five minutes from local time.
            # It could be a replay attack, so let's ignore it.
            if abs(time.time() - int(request_timestamp)) > 60 * 5:
                raise ValueError()

            sig_basestring = f"v0:{request_timestamp}:{body}".encode('utf-8')

            my_signature = 'v0=' + hmac.new(
                __SIGNING_SECRET.encode('utf-8'),
                sig_basestring,
                hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(my_signature, slack_signature):
                raise ValueError()

            return func(*args, **kwargs)
        except ValueError:
            return {
                'statusCode': 401,
                'body': 'Invalid Slack signature.'
            }

    return inner_function
