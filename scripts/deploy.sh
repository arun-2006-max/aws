#!/bin/bash
# Deployment script for AI Builder Copilot

set -e

# Default to dev environment
ENV=${1:-dev}

echo "Deploying AI Builder Copilot to $ENV environment..."

# Navigate to infrastructure directory
cd infrastructure

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Creating virtual environment..."
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi

# Deploy CDK stacks
echo "Deploying CDK stacks..."
cdk deploy --all --context env=$ENV --require-approval never

echo "Deployment complete!"
