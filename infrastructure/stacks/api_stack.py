"""
API Stack - API Gateway REST API
Implements Requirements 11.1-11.7, 19.4
"""
from aws_cdk import (
    Stack,
    aws_apigateway as apigw,
    aws_cognito as cognito,
)
from constructs import Construct


class ApiStack(Stack):
    """Stack for API Gateway resources"""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_name: str,
        env_config: dict,
        compute_stack,
        auth_stack,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.env_name = env_name
        self.env_config = env_config
        self.compute_stack = compute_stack
        self.auth_stack = auth_stack

        # Create API Gateway
        self.api = apigw.RestApi(
            self,
            "AIBuilderCopilotAPI",
            rest_api_name=f"ai-builder-copilot-api-{env_name}",
            description=f"AI Builder Copilot API - {env_name}",
            deploy_options=apigw.StageOptions(
                stage_name=env_name,
                throttling_rate_limit=100,
                throttling_burst_limit=200,
                logging_level=apigw.MethodLoggingLevel.INFO,
                data_trace_enabled=True,
                metrics_enabled=True
            ),
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "Authorization"],
                allow_credentials=True
            ),
            endpoint_types=[apigw.EndpointType.REGIONAL]
        )

        # Create Cognito authorizer
        self.authorizer = apigw.CognitoUserPoolsAuthorizer(
            self,
            "CognitoAuthorizer",
            cognito_user_pools=[auth_stack.user_pool]
        )

        # Create API endpoints
        self._create_endpoints()

    def _create_endpoints(self):
        """Create API Gateway endpoints"""
        
        # POST /chat
        chat_resource = self.api.root.add_resource("chat")
        chat_resource.add_method(
            "POST",
            apigw.LambdaIntegration(self.compute_stack.chat_handler),
            authorizer=self.authorizer,
            authorization_type=apigw.AuthorizationType.COGNITO,
            request_validator=self._create_request_validator("ChatRequestValidator")
        )

        # POST /learning-analysis
        learning_analysis_resource = self.api.root.add_resource("learning-analysis")
        learning_analysis_resource.add_method(
            "POST",
            apigw.LambdaIntegration(self.compute_stack.learning_analysis_handler),
            authorizer=self.authorizer,
            authorization_type=apigw.AuthorizationType.COGNITO,
            request_validator=self._create_request_validator("LearningAnalysisRequestValidator")
        )

        # POST /debug-assistant
        debug_assistant_resource = self.api.root.add_resource("debug-assistant")
        debug_assistant_resource.add_method(
            "POST",
            apigw.LambdaIntegration(self.compute_stack.debug_assistant_handler),
            authorizer=self.authorizer,
            authorization_type=apigw.AuthorizationType.COGNITO,
            request_validator=self._create_request_validator("DebugAssistantRequestValidator")
        )

        # GET /user-progress
        user_progress_resource = self.api.root.add_resource("user-progress")
        user_progress_resource.add_method(
            "GET",
            apigw.LambdaIntegration(self.compute_stack.user_progress_handler),
            authorizer=self.authorizer,
            authorization_type=apigw.AuthorizationType.COGNITO
        )

        # POST /store-feedback
        store_feedback_resource = self.api.root.add_resource("store-feedback")
        store_feedback_resource.add_method(
            "POST",
            apigw.LambdaIntegration(self.compute_stack.feedback_handler),
            authorizer=self.authorizer,
            authorization_type=apigw.AuthorizationType.COGNITO,
            request_validator=self._create_request_validator("FeedbackRequestValidator")
        )

    def _create_request_validator(self, validator_id: str) -> apigw.RequestValidator:
        """Create request validator for API Gateway"""
        return apigw.RequestValidator(
            self,
            validator_id,
            rest_api=self.api,
            validate_request_body=True,
            validate_request_parameters=True
        )
