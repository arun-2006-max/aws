# AI Builder Copilot

A context-aware AI productivity assistant designed to help students and developers learn faster and build smarter. The system detects knowledge gaps, retrieves relevant context using Retrieval Augmented Generation (RAG), and generates intelligent responses using GenAI models via Amazon Bedrock.

## Architecture

The application is built using serverless AWS services:

- **Frontend**: React.js with TypeScript and Material-UI
- **Backend**: AWS Lambda functions (Python 3.11)
- **Infrastructure**: AWS CDK for Infrastructure as Code
- **AI/ML**: Amazon Bedrock (Claude, Titan, Nova models)
- **Storage**: DynamoDB, S3, OpenSearch
- **Authentication**: AWS Cognito
- **API**: API Gateway with REST endpoints

## Project Structure

```
.
├── infrastructure/          # AWS CDK infrastructure code
│   ├── stacks/             # CDK stack definitions
│   ├── app.py              # CDK app entry point
│   └── cdk.json            # CDK configuration
├── lambda/                 # Lambda function code
│   └── handlers/           # Lambda handler implementations
├── frontend/               # React.js frontend application
│   ├── src/                # Source code
│   └── public/             # Static assets
├── config/                 # Environment configuration files
│   ├── dev.env
│   ├── staging.env
│   └── prod.env
└── README.md
```

## Prerequisites

- Python 3.11+
- Node.js 18+
- AWS CLI configured with appropriate credentials
- AWS CDK CLI (`npm install -g aws-cdk`)

## Setup

### 1. Infrastructure Setup

```bash
cd infrastructure

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Bootstrap CDK (first time only)
cdk bootstrap

# Deploy to development environment
cdk deploy --all --context env=dev
```

### 2. Lambda Functions Setup

```bash
cd lambda

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

## Deployment

### Deploy Infrastructure

```bash
cd infrastructure

# Deploy to specific environment
cdk deploy --all --context env=dev     # Development
cdk deploy --all --context env=staging # Staging
cdk deploy --all --context env=prod    # Production
```

### Deploy Lambda Functions

Lambda functions are automatically deployed with the CDK infrastructure.

### Deploy Frontend

```bash
cd frontend

# Build production bundle
npm run build

# Deploy to S3/CloudFront (to be configured)
```

## Environment Configuration

Environment-specific configurations are stored in `config/` directory:

- `dev.env` - Development environment
- `staging.env` - Staging environment
- `prod.env` - Production environment

## API Endpoints

- `POST /chat` - Send queries to AI assistant
- `POST /learning-analysis` - Analyze learning progress and knowledge gaps
- `POST /debug-assistant` - Get AI-powered debugging assistance
- `GET /user-progress` - Retrieve user learning progress
- `POST /store-feedback` - Store user feedback on AI responses

## Security

- All data encrypted at rest using AWS KMS
- TLS 1.2+ enforced for all API connections
- JWT-based authentication via Cognito
- IAM roles with least privilege permissions
- Input sanitization to prevent injection attacks

## Cost Optimization

- Intelligent model routing (60%+ queries to Claude Haiku)
- Response caching with DynamoDB TTL
- S3 lifecycle policies (Glacier after 90 days)
- On-demand billing for unpredictable workloads
- Token limits (4096 max) to control costs

## Development

This project follows a task-based implementation plan. See `.kiro/specs/ai-builder-copilot/tasks.md` for the complete implementation roadmap.

## License

Proprietary - All rights reserved
