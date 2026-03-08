#!/bin/bash
# Setup script for AI Builder Copilot development environment

set -e

echo "Setting up AI Builder Copilot development environment..."

# Setup infrastructure
echo "Setting up infrastructure..."
cd infrastructure
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

# Setup Lambda functions
echo "Setting up Lambda functions..."
cd lambda
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

# Setup frontend
echo "Setting up frontend..."
cd frontend
npm install
cd ..

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Configure AWS credentials: aws configure"
echo "2. Bootstrap CDK: cd infrastructure && cdk bootstrap"
echo "3. Deploy infrastructure: ./scripts/deploy.sh dev"
echo "4. Start frontend: cd frontend && npm start"
