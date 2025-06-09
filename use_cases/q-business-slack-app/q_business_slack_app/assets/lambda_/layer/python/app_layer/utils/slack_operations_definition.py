from ..constants import Env


# TODO: replace this with your slash command
SLASH_COMMAND = '/my-slash-command'

OP_ASK = 'ask'
OP_HELP = 'help'

OPTION_DEV = '--dev'

# TODO: add allowed users
OP_DEFINITION = {
    Env.DEV.value: {
        OP_HELP: {
            'requiredOptions': [],
            'acceptedOptions': [OPTION_DEV],
            'allowedUsers': [],
        },
        OP_ASK:  {
            'minQuestionLength': 15,
            'requiredOptions': [],
            'acceptedOptions': [OPTION_DEV],
            'allowedUsers': [],
        }
    },
    Env.PROD.value: {
        OP_HELP: {
            'requiredOptions': [],
            'acceptedOptions': [OPTION_DEV],
            'allowedUsers': [],
        },
        OP_ASK: {
            'minQuestionLength': 15,
            'requiredOptions': [],
            'acceptedOptions': [OPTION_DEV],
            'allowedUsers': [],
        }
    }
}