"""
Compute Stack - Lambda Functions
Implements Requirements 19.1
"""
from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_logs as logs,
    aws_ec2 as ec2,
)
from constructs import Construct


class ComputeStack(Stack):
    """Stack for Lambda compute resources"""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_name: str,
        env_config: dict,
        storage_stack,
        auth_stack,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.env_name = env_name
        self.env_config = env_config
        self.storage_stack = storage_stack
        self.auth_stack = auth_stack

        # Common Lambda environment variables
        self.common_env = {
            "ENV": env_name,
            "USERS_TABLE": storage_stack.users_table.table_name,
            "SESSIONS_TABLE": storage_stack.sessions_table.table_name,
            "INTERACTION_LOGS_TABLE": storage_stack.interaction_logs_table.table_name,
            "LEARNING_PROGRESS_TABLE": storage_stack.learning_progress_table.table_name,
            "KNOWLEDGE_GAPS_TABLE": storage_stack.knowledge_gaps_table.table_name,
            "RESPONSE_CACHE_TABLE": storage_stack.response_cache_table.table_name,
            "KNOWLEDGE_BASE_BUCKET": storage_stack.knowledge_base_bucket.bucket_name,
            "LOGS_BUCKET": storage_stack.logs_bucket.bucket_name,
            "BEDROCK_REGION": env_config.get("bedrockRegion", "us-east-1"),
            "OPENSEARCH_ENDPOINT": storage_stack.opensearch_endpoint,
            "OPENSEARCH_INDEX": "knowledge_vectors",
        }

        # Create Lambda functions
        self._create_lambda_functions()

    def _create_lambda_functions(self):
        """Create Lambda function placeholders"""
        
        # Chat Handler Lambda
        self.chat_handler = self._create_lambda(
            "ChatHandler",
            "handlers/chat_handler.py",
            "Chat endpoint handler",
            additional_policies=[
                iam.PolicyStatement(
                    actions=[
                        "bedrock:InvokeModel",
                        "bedrock:InvokeModelWithResponseStream"
                    ],
                    resources=["*"]
                )
            ]
        )

        # Learning Analysis Handler Lambda
        self.learning_analysis_handler = self._create_lambda(
            "LearningAnalysisHandler",
            "handlers/learning_analysis_handler.py",
            "Learning analysis endpoint handler",
            additional_policies=[
                iam.PolicyStatement(
                    actions=[
                        "bedrock:InvokeModel"
                    ],
                    resources=["*"]
                )
            ]
        )

        # Debug Assistant Handler Lambda
        self.debug_assistant_handler = self._create_lambda(
            "DebugAssistantHandler",
            "handlers/debug_assistant_handler.py",
            "Debug assistant endpoint handler",
            additional_policies=[
                iam.PolicyStatement(
                    actions=[
                        "bedrock:InvokeModel"
                    ],
                    resources=["*"]
                )
            ]
        )

        # User Progress Handler Lambda
        self.user_progress_handler = self._create_lambda(
            "UserProgressHandler",
            "handlers/user_progress_handler.py",
            "User progress endpoint handler"
        )

        # Feedback Handler Lambda
        self.feedback_handler = self._create_lambda(
            "FeedbackHandler",
            "handlers/feedback_handler.py",
            "Feedback storage endpoint handler"
        )

        # Document Indexing Handler Lambda
        self.document_indexing_handler = self._create_lambda(
            "DocumentIndexingHandler",
            "handlers/document_indexing_handler.py",
            "Document indexing pipeline handler",
            timeout=Duration.minutes(5),
            memory_size=1024,
            additional_policies=[
                iam.PolicyStatement(
                    actions=[
                        "bedrock:InvokeModel"
                    ],
                    resources=["*"]
                )
            ]
        )

    def _create_lambda(
        self,
        function_id: str,
        handler_path: str,
        description: str,
        timeout: Duration = Duration.seconds(30),
        memory_size: int = 512,
        additional_policies: list = None
    ) -> lambda_.Function:
        """Create a Lambda function with common configuration"""
        
        # Create IAM role with least privilege
        role = iam.Role(
            self,
            f"{function_id}Role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            description=f"Role for {function_id}",
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaVPCAccessExecutionRole"
                ),
            ]
        )

        # Grant DynamoDB permissions
        for table in [
            self.storage_stack.users_table,
            self.storage_stack.sessions_table,
            self.storage_stack.interaction_logs_table,
            self.storage_stack.learning_progress_table,
            self.storage_stack.knowledge_gaps_table,
            self.storage_stack.response_cache_table,
        ]:
            table.grant_read_write_data(role)

        # Grant S3 permissions
        self.storage_stack.knowledge_base_bucket.grant_read_write(role)
        self.storage_stack.logs_bucket.grant_write(role)

        # Grant KMS permissions
        self.storage_stack.kms_key.grant_encrypt_decrypt(role)

        # Grant OpenSearch permissions
        self.storage_stack.grant_opensearch_access(role)

        # Add additional policies if provided
        if additional_policies:
            for policy in additional_policies:
                role.add_to_policy(policy)

        # Create Lambda function (with VPC access for OpenSearch)
        function = lambda_.Function(
            self,
            function_id,
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset(f"../lambda/{handler_path.split('/')[0]}"),
            role=role,
            environment=self.common_env,
            timeout=timeout,
            memory_size=memory_size,
            description=description,
            vpc=self.storage_stack.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            security_groups=[self.storage_stack.opensearch_security_group],
            log_retention=logs.RetentionDays.ONE_WEEK,
        )

        return function
