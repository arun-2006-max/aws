#!/usr/bin/env python3
"""
AI Builder Copilot CDK Application
Main entry point for AWS CDK infrastructure deployment
"""
import os
import aws_cdk as cdk
from stacks.storage_stack import StorageStack
from stacks.auth_stack import AuthStack
from stacks.api_stack import ApiStack
from stacks.compute_stack import ComputeStack

app = cdk.App()

# Get environment from context or default to dev
env_name = app.node.try_get_context("env") or "dev"
env_config = app.node.try_get_context(env_name) or {}

# AWS environment configuration
aws_env = cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1")
)

# Storage Stack - DynamoDB, S3, OpenSearch
storage_stack = StorageStack(
    app,
    f"AIBuilderCopilot-Storage-{env_name}",
    env=aws_env,
    env_name=env_name,
    env_config=env_config
)

# Auth Stack - Cognito User Pool
auth_stack = AuthStack(
    app,
    f"AIBuilderCopilot-Auth-{env_name}",
    env=aws_env,
    env_name=env_name,
    env_config=env_config
)

# Compute Stack - Lambda Functions
compute_stack = ComputeStack(
    app,
    f"AIBuilderCopilot-Compute-{env_name}",
    env=aws_env,
    env_name=env_name,
    env_config=env_config,
    storage_stack=storage_stack,
    auth_stack=auth_stack
)

# API Stack - API Gateway
api_stack = ApiStack(
    app,
    f"AIBuilderCopilot-API-{env_name}",
    env=aws_env,
    env_name=env_name,
    env_config=env_config,
    compute_stack=compute_stack,
    auth_stack=auth_stack
)

# Add tags to all resources
for stack in [storage_stack, auth_stack, compute_stack, api_stack]:
    cdk.Tags.of(stack).add("Project", "AIBuilderCopilot")
    cdk.Tags.of(stack).add("Environment", env_name)

app.synth()
