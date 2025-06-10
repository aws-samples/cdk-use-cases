from aws_cdk import (
    NestedStack,
    aws_apigateway as apigateway,
    aws_lambda as _lambda,
)
from constructs import Construct
from ..constants import *


class ApiGatewayStack(NestedStack):
    def __create_api(self, app_name):
        api = apigateway.RestApi(
            self, 'RestAPI',
            rest_api_name=app_name,
            retain_deployments=False,
            deploy=True,
            deploy_options=apigateway.StageOptions(
                stage_name=ENV_DEV,
                variables={'env': ENV_DEV},
            )
        )

        for env in ENVS:
            if env != ENV_DEV:
                apigateway.Stage(
                    self,
                    f"RestApi{env}Stage",
                    deployment=api.latest_deployment,
                    stage_name=env,
                    variables={'env': env},
                )

        return api

    def __create_handle_slack_event_integration(self, lambda_stack):
        func_arn = lambda_stack.func_handle_slack_event.function_arn + ":${stageVariables.env}"

        resource = self.__api.root.add_resource('handle-slack-event')
        resource.add_method(
            'POST',
            apigateway.LambdaIntegration(
                _lambda.Function.from_function_arn(
                    self, f'{lambda_stack.func_handle_slack_event.function_name}-staged',
                    function_arn=func_arn,
                )
            )
        )

    def __create_handle_slash_command_integration(self, lambda_stack):
        func_arn = lambda_stack.func_handle_slash_command.function_arn + ":${stageVariables.env}"

        resource = self.__api.root.add_resource('handle-slash-command')
        resource.add_method(
            'POST',
            apigateway.LambdaIntegration(
                _lambda.Function.from_function_arn(
                    self, f'{lambda_stack.func_handle_slash_command.function_name}-staged',
                    function_arn=func_arn,
                ),
                proxy=False,
                passthrough_behavior=apigateway.PassthroughBehavior.WHEN_NO_TEMPLATES,
                request_templates={
                    'application/x-www-form-urlencoded': '''
                    {
                        "body": $input.json("$"),
                        "headers": {
                            #foreach($header in $input.params().header.keySet())
                                "$header": "$util.escapeJavaScript($input.params().header.get($header))"
                                #if($foreach.hasNext),#end
                            #end
                        }
                    }
                    '''
                },
                integration_responses=[
                    apigateway.IntegrationResponse(
                        status_code='200',
                        response_templates={'application/json': "#set($inputRoot = $input.path('$'))\n$inputRoot.body"}
                    )
                ]
            ),
            method_responses=[
                apigateway.MethodResponse(
                    status_code='200'
                )
            ]
        )

    def __init__(self, scope: Construct, construct_id: str, app_name, lambda_stack) -> None:
        super().__init__(scope, construct_id)

        self.__api = self.__create_api(app_name)
        self.__create_handle_slack_event_integration(lambda_stack)
        self.__create_handle_slash_command_integration(lambda_stack)
