from libs_finder import *


def __onboard_user(user_id, channel_id):
    slack = SlackManager()

    response = slack.get_user_profile(user_id)
    username = response['profile']['email'].split('@')[0]
    response = users_manager.get_user(username)

    # New user
    if response is None:
        users_manager.add_user(username, channel_id, user_id)

        # Send welcome message
        with open('blocks/onboarding.json') as fd:
            blocks = json.load(fd)
            slack.post_message(blocks, blocks[0]['text']['text'], channel_id)

        # Configure app home
        with open('blocks/home.json') as fd:
            blocks = fd.read()
            slack.update_app_home(user_id, blocks)


@verify_slack_request
def handler(event, context):
    body = json.loads(event['body'])

    if 'type' in body and body['type'] == 'url_verification':
        return {
            'statusCode': 200,
            'body': json.dumps({'challenge': body['challenge']})
        }
    elif body['event']['type'] == 'app_home_opened':
        user_id = body['event']['user']
        channel = body['event']['channel']

        if channel and user_id:
            __onboard_user(user_id, channel)

    return {'statusCode': 200}
