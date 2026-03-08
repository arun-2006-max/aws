"""
Unit tests for Storage Stack
Tests S3 bucket configuration, encryption, and lifecycle policies
Implements Requirements 19.3, 20.4
"""
import aws_cdk as cdk
from aws_cdk import assertions
from stacks.storage_stack import StorageStack


def test_knowledge_base_bucket_encryption():
    """
    Test that knowledge base bucket has KMS encryption enabled
    Validates Requirement 19.3: S3 SHALL enforce encryption at rest
    """
    app = cdk.App()
    stack = StorageStack(
        app,
        "TestStorageStack",
        env_name="test",
        env_config={}
    )
    template = assertions.Template.from_stack(stack)
    
    # Verify bucket has KMS encryption
    template.has_resource_properties(
        "AWS::S3::Bucket",
        {
            "BucketEncryption": {
                "ServerSideEncryptionConfiguration": [
                    {
                        "ServerSideEncryptionByDefault": {
                            "SSEAlgorithm": "aws:kms"
                        }
                    }
                ]
            }
        }
    )


def test_knowledge_base_bucket_lifecycle_policy():
    """
    Test that knowledge base bucket has lifecycle policy to move to Glacier
    Validates Requirement 20.4: S3 SHALL implement lifecycle policies moving logs to Glacier after 90 days
    """
    app = cdk.App()
    stack = StorageStack(
        app,
        "TestStorageStack",
        env_name="test",
        env_config={}
    )
    template = assertions.Template.from_stack(stack)
    
    # Verify bucket has lifecycle rule for Glacier transition
    template.has_resource_properties(
        "AWS::S3::Bucket",
        {
            "LifecycleConfiguration": {
                "Rules": assertions.Match.array_with([
                    assertions.Match.object_like({
                        "Id": "MoveToGlacier",
                        "Status": "Enabled",
                        "Transitions": [
                            {
                                "StorageClass": "GLACIER",
                                "TransitionInDays": 90
                            }
                        ]
                    })
                ])
            }
        }
    )


def test_knowledge_base_bucket_versioning():
    """
    Test that knowledge base bucket has versioning enabled
    Validates Requirement 10.4: Data storage with versioning for recovery
    """
    app = cdk.App()
    stack = StorageStack(
        app,
        "TestStorageStack",
        env_name="test",
        env_config={}
    )
    template = assertions.Template.from_stack(stack)
    
    # Verify bucket has versioning enabled
    template.has_resource_properties(
        "AWS::S3::Bucket",
        {
            "VersioningConfiguration": {
                "Status": "Enabled"
            }
        }
    )


def test_knowledge_base_bucket_public_access_blocked():
    """
    Test that knowledge base bucket blocks all public access
    Validates Requirement 19.3: Secure S3 bucket configuration
    """
    app = cdk.App()
    stack = StorageStack(
        app,
        "TestStorageStack",
        env_name="test",
        env_config={}
    )
    template = assertions.Template.from_stack(stack)
    
    # Verify bucket blocks all public access
    template.has_resource_properties(
        "AWS::S3::Bucket",
        {
            "PublicAccessBlockConfiguration": {
                "BlockPublicAcls": True,
                "BlockPublicPolicy": True,
                "IgnorePublicAcls": True,
                "RestrictPublicBuckets": True
            }
        }
    )


def test_knowledge_base_folder_structure_created():
    """
    Test that folder structure is created in knowledge base bucket
    Validates Requirement 7.1: Knowledge base bucket with folder structure
    """
    app = cdk.App()
    stack = StorageStack(
        app,
        "TestStorageStack",
        env_name="test",
        env_config={}
    )
    template = assertions.Template.from_stack(stack)
    
    # Verify BucketDeployment resources exist for folder structure
    # documents/ folder
    template.has_resource_properties(
        "Custom::CDKBucketDeployment",
        assertions.Match.object_like({
            "DestinationBucketKeyPrefix": "documents/"
        })
    )
    
    # embeddings-cache/ folder
    template.has_resource_properties(
        "Custom::CDKBucketDeployment",
        assertions.Match.object_like({
            "DestinationBucketKeyPrefix": "embeddings-cache/"
        })
    )
    
    # logs/ folder
    template.has_resource_properties(
        "Custom::CDKBucketDeployment",
        assertions.Match.object_like({
            "DestinationBucketKeyPrefix": "logs/"
        })
    )


def test_ssl_enforcement():
    """
    Test that S3 bucket enforces SSL/TLS connections
    Validates Requirement 19.4: API Gateway SHALL enforce TLS 1.2 or higher
    """
    app = cdk.App()
    stack = StorageStack(
        app,
        "TestStorageStack",
        env_name="test",
        env_config={}
    )
    template = assertions.Template.from_stack(stack)
    
    # Verify bucket policy enforces SSL
    # CDK's enforce_ssl=True creates a bucket policy that denies non-SSL requests
    template.has_resource_properties(
        "AWS::S3::BucketPolicy",
        {
            "PolicyDocument": {
                "Statement": assertions.Match.array_with([
                    assertions.Match.object_like({
                        "Effect": "Deny",
                        "Condition": {
                            "Bool": {
                                "aws:SecureTransport": "false"
                            }
                        }
                    })
                ])
            }
        }
    )


def test_kms_key_rotation_enabled():
    """
    Test that KMS key has automatic rotation enabled
    Validates Requirement 19.2: Encryption with key rotation
    """
    app = cdk.App()
    stack = StorageStack(
        app,
        "TestStorageStack",
        env_name="test",
        env_config={}
    )
    template = assertions.Template.from_stack(stack)
    
    # Verify KMS key has rotation enabled
    template.has_resource_properties(
        "AWS::KMS::Key",
        {
            "EnableKeyRotation": True
        }
    )
