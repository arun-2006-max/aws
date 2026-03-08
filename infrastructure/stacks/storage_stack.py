"""
Storage Stack - DynamoDB Tables, S3 Buckets, OpenSearch Domain
Implements Requirements 10.1, 19.2, 19.3, 7.1, 10.4, 19.3, 20.4, 2.2, 2.3
"""
from aws_cdk import (
    Stack,
    RemovalPolicy,
    Duration,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_s3_notifications as s3n,
    aws_kms as kms,
    aws_ec2 as ec2,
    aws_opensearchservice as opensearch,
    aws_iam as iam,
)
from constructs import Construct


class StorageStack(Stack):
    """Stack for data storage resources"""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_name: str,
        env_config: dict,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.env_name = env_name
        self.env_config = env_config

        # Create KMS key for encryption
        self.kms_key = kms.Key(
            self,
            "EncryptionKey",
            description=f"AI Builder Copilot encryption key - {env_name}",
            enable_key_rotation=True,
            removal_policy=RemovalPolicy.RETAIN if env_name == "prod" else RemovalPolicy.DESTROY
        )

        # Create DynamoDB tables
        self._create_dynamodb_tables()

        # Create S3 buckets
        self._create_s3_buckets()
        
        # Create folder structure in knowledge base bucket
        self._create_knowledge_base_folders()
        
        # Create VPC for OpenSearch
        self._create_vpc()
        
        # Create OpenSearch domain
        self._create_opensearch_domain()

    def _create_dynamodb_tables(self):
        """Create DynamoDB tables for the application"""
        
        # Users table
        self.users_table = dynamodb.Table(
            self,
            "UsersTable",
            partition_key=dynamodb.Attribute(
                name="user_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.RETAIN if self.env_name == "prod" else RemovalPolicy.DESTROY
        )

        # Sessions table
        self.sessions_table = dynamodb.Table(
            self,
            "SessionsTable",
            partition_key=dynamodb.Attribute(
                name="session_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
            point_in_time_recovery=True,
            time_to_live_attribute="ttl",
            removal_policy=RemovalPolicy.RETAIN if self.env_name == "prod" else RemovalPolicy.DESTROY
        )

        # Add GSI for user_id lookups (query all sessions for a user)
        self.sessions_table.add_global_secondary_index(
            index_name="UserIdIndex",
            partition_key=dynamodb.Attribute(
                name="user_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="created_at",
                type=dynamodb.AttributeType.NUMBER
            )
        )

        # InteractionLogs table
        self.interaction_logs_table = dynamodb.Table(
            self,
            "InteractionLogsTable",
            partition_key=dynamodb.Attribute(
                name="user_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.NUMBER
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.RETAIN if self.env_name == "prod" else RemovalPolicy.DESTROY
        )

        # Add GSI for interaction_id lookups
        self.interaction_logs_table.add_global_secondary_index(
            index_name="InteractionIdIndex",
            partition_key=dynamodb.Attribute(
                name="interaction_id",
                type=dynamodb.AttributeType.STRING
            )
        )

        # LearningProgress table
        self.learning_progress_table = dynamodb.Table(
            self,
            "LearningProgressTable",
            partition_key=dynamodb.Attribute(
                name="user_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="topic",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.RETAIN if self.env_name == "prod" else RemovalPolicy.DESTROY
        )

        # KnowledgeGaps table
        self.knowledge_gaps_table = dynamodb.Table(
            self,
            "KnowledgeGapsTable",
            partition_key=dynamodb.Attribute(
                name="user_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="gap_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
            point_in_time_recovery=True,
            removal_policy=RemovalPolicy.RETAIN if self.env_name == "prod" else RemovalPolicy.DESTROY
        )

        # Add GSI for timestamp-based queries (query recent gaps)
        self.knowledge_gaps_table.add_global_secondary_index(
            index_name="TimestampIndex",
            partition_key=dynamodb.Attribute(
                name="user_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.NUMBER
            )
        )

        # ResponseCache table
        self.response_cache_table = dynamodb.Table(
            self,
            "ResponseCacheTable",
            partition_key=dynamodb.Attribute(
                name="query_hash",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
            time_to_live_attribute="ttl",
            removal_policy=RemovalPolicy.DESTROY
        )

    def _create_s3_buckets(self):
        """Create S3 buckets for knowledge base and logs"""
        
        # Knowledge base bucket
        self.knowledge_base_bucket = s3.Bucket(
            self,
            "KnowledgeBaseBucket",
            encryption=s3.BucketEncryption.KMS,
            encryption_key=self.kms_key,
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.RETAIN if self.env_name == "prod" else RemovalPolicy.DESTROY,
            auto_delete_objects=False if self.env_name == "prod" else True,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="MoveToGlacier",
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(90)
                        )
                    ]
                )
            ]
        )

        # Logs bucket
        self.logs_bucket = s3.Bucket(
            self,
            "LogsBucket",
            encryption=s3.BucketEncryption.KMS,
            encryption_key=self.kms_key,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.RETAIN if self.env_name == "prod" else RemovalPolicy.DESTROY,
            auto_delete_objects=False if self.env_name == "prod" else True,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="MoveLogsToGlacier",
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(90)
                        )
                    ]
                )
            ]
        )

    def _create_knowledge_base_folders(self):
        """
        Create folder structure in knowledge base bucket
        Implements Requirements 7.1, 10.4, 19.3, 20.4
        
        Creates the following folders:
        - documents/: For storing uploaded knowledge base documents
        - embeddings-cache/: For caching generated embeddings
        - logs/: For storing processing logs
        """
        # Deploy folder structure using S3 deployment
        # Note: S3 doesn't have true folders, but we create placeholder objects
        # to establish the folder structure
        s3deploy.BucketDeployment(
            self,
            "KnowledgeBaseFolderStructure",
            sources=[s3deploy.Source.data("documents/.keep", "")],
            destination_bucket=self.knowledge_base_bucket,
            destination_key_prefix="documents/",
            prune=False
        )
        
        s3deploy.BucketDeployment(
            self,
            "EmbeddingsCacheFolderStructure",
            sources=[s3deploy.Source.data("embeddings-cache/.keep", "")],
            destination_bucket=self.knowledge_base_bucket,
            destination_key_prefix="embeddings-cache/",
            prune=False
        )
        
        s3deploy.BucketDeployment(
            self,
            "LogsFolderStructure",
            sources=[s3deploy.Source.data("logs/.keep", "")],
            destination_bucket=self.knowledge_base_bucket,
            destination_key_prefix="logs/",
            prune=False
        )
    
    def add_document_upload_notification(self, target):
        """
        Configure S3 event notifications for document uploads
        Implements Requirement 7.1
        
        Args:
            target: Lambda function or SNS topic to notify on document uploads
        """
        # Add notification for new documents uploaded to documents/ folder
        self.knowledge_base_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            target,
            s3.NotificationKeyFilter(prefix="documents/")
        )

    def _create_vpc(self):
        """
        Create VPC for OpenSearch domain
        Implements Requirements 2.2, 2.3
        
        Creates a VPC with:
        - 2 availability zones for high availability
        - Private subnets for OpenSearch nodes
        - NAT gateways for outbound connectivity
        """
        self.vpc = ec2.Vpc(
            self,
            "OpenSearchVPC",
            max_azs=2,
            nat_gateways=1,  # Cost optimization: use 1 NAT gateway
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                )
            ]
        )

        # Security group for OpenSearch domain
        self.opensearch_security_group = ec2.SecurityGroup(
            self,
            "OpenSearchSecurityGroup",
            vpc=self.vpc,
            description="Security group for OpenSearch domain",
            allow_all_outbound=True
        )

        # Allow HTTPS access from within VPC
        self.opensearch_security_group.add_ingress_rule(
            peer=ec2.Peer.ipv4(self.vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(443),
            description="Allow HTTPS from VPC"
        )

    def _create_opensearch_domain(self):
        """
        Create OpenSearch domain with knn_vector index configuration
        Implements Requirements 2.2, 2.3
        
        Creates an OpenSearch domain with:
        - VPC configuration for security
        - KNN plugin enabled for vector search
        - Encryption at rest and in transit
        - Fine-grained access control
        """
        # Create service-linked role for OpenSearch (if not exists)
        # This is required for VPC-based OpenSearch domains
        
        # OpenSearch domain configuration
        self.opensearch_domain = opensearch.Domain(
            self,
            "KnowledgeBaseSearchDomain",
            version=opensearch.EngineVersion.OPENSEARCH_2_11,
            
            # Capacity configuration - using small instances for cost optimization
            capacity=opensearch.CapacityConfig(
                data_node_instance_type="t3.small.search",
                data_nodes=2,  # 2 nodes for high availability
                multi_az_with_standby_enabled=False  # Cost optimization
            ),
            
            # EBS storage configuration
            ebs=opensearch.EbsOptions(
                volume_size=20,  # 20 GB per node
                volume_type=ec2.EbsDeviceVolumeType.GP3
            ),
            
            # VPC configuration
            vpc=self.vpc,
            vpc_subnets=[ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            )],
            security_groups=[self.opensearch_security_group],
            
            # Encryption configuration
            encryption_at_rest=opensearch.EncryptionAtRestOptions(
                enabled=True,
                kms_key=self.kms_key
            ),
            node_to_node_encryption=True,
            enforce_https=True,
            
            # Fine-grained access control
            fine_grained_access_control=opensearch.AdvancedSecurityOptions(
                master_user_arn=None,  # Will be set via IAM role
            ),
            
            # Logging configuration
            logging=opensearch.LoggingOptions(
                slow_search_log_enabled=True,
                app_log_enabled=True,
                slow_index_log_enabled=True
            ),
            
            # Removal policy
            removal_policy=RemovalPolicy.RETAIN if self.env_name == "prod" else RemovalPolicy.DESTROY,
            
            # Enable advanced options for KNN
            advanced_options={
                "rest.action.multi.allow_explicit_index": "true",
                "override_main_response_version": "true"
            }
        )

        # Grant access to Lambda functions (will be configured in compute stack)
        # Store domain endpoint for use by other stacks
        self.opensearch_endpoint = self.opensearch_domain.domain_endpoint
        self.opensearch_domain_arn = self.opensearch_domain.domain_arn

    def grant_opensearch_access(self, grantee: iam.IGrantable):
        """
        Grant read/write access to OpenSearch domain
        
        Args:
            grantee: IAM principal (e.g., Lambda execution role) to grant access to
        """
        # Grant permissions to access OpenSearch domain
        self.opensearch_domain.grant_read_write(grantee)
