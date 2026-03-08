# AI Builder Copilot – AWS Deployment Guide

## Prerequisites

- **AWS CLI** v2 configured with credentials
- **Node.js** 18+ and **npm**
- **Python** 3.11+ and **pip**
- **AWS CDK** CLI: `npm install -g aws-cdk`

## 1. Bootstrap CDK (first time only)

```bash
cdk bootstrap aws://ACCOUNT_ID/us-east-1
```

## 2. Configure Environment

Edit `config/dev.env` (or `staging.env` / `prod.env`) with your values:

```env
ENV=dev
AWS_REGION=us-east-1
BEDROCK_REGION=us-east-1
LOG_LEVEL=DEBUG
LOG_RETENTION_DAYS=7
ENABLE_MFA=false
OPENSEARCH_INSTANCE_TYPE=t3.small.search
OPENSEARCH_INSTANCE_COUNT=1
LAMBDA_MEMORY_SIZE=512
ENABLE_PROVISIONED_CONCURRENCY=false
```

## 3. Install Dependencies

```bash
# Infrastructure
cd infrastructure
pip install -r requirements.txt

# Lambda layer
cd ../lambda
pip install -r requirements.txt -t ./package/

# Frontend
cd ../frontend
npm install
```

## 4. Deploy Stacks (order matters)

```bash
cd infrastructure

# All stacks at once
cdk deploy --all -c env=dev

# Or individually in order:
cdk deploy AIBuilderCopilot-Storage-dev
cdk deploy AIBuilderCopilot-Auth-dev
cdk deploy AIBuilderCopilot-Compute-dev
cdk deploy AIBuilderCopilot-API-dev
```

## 5. Post-Deployment Setup

### Create OpenSearch Index

After the OpenSearch domain is active, run:

```bash
python scripts/setup.sh  # or setup.ps1 on Windows
```

Or manually invoke the index creation by uploading any `.keep` file to the knowledge base bucket.

### Configure Frontend Environment

Create `frontend/.env`:

```env
REACT_APP_API_URL=https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/dev
REACT_APP_USER_POOL_ID=us-east-1_XXXXXXX
REACT_APP_CLIENT_ID=YOUR_CLIENT_ID
REACT_APP_AWS_REGION=us-east-1
```

Get these values from CDK outputs after deployment.

### Build & Host Frontend

```bash
cd frontend
npm run build
# Upload build/ to S3 + CloudFront, or serve locally:
npm start
```

## 6. Upload Knowledge Base Documents

Upload PDF, TXT, MD, or DOCX files to the S3 knowledge base bucket under `documents/`:

```bash
aws s3 cp ./my-docs/ s3://BUCKET_NAME/documents/ --recursive
```

The document indexing Lambda will automatically process and index them.

## 7. Verify Deployment

| Check | Command |
|---|---|
| API Gateway | `curl https://API_URL/dev/chat -H "Authorization: Bearer TOKEN"` |
| Lambda logs | `aws logs tail /aws/lambda/ChatHandler --follow` |
| DynamoDB tables | `aws dynamodb list-tables` |
| OpenSearch | `curl https://OPENSEARCH_ENDPOINT/_cat/indices` |

## 8. Cost Monitoring

- Set up **AWS Budgets** with alerts at $50, $100, $200
- Bedrock pricing: Haiku ~$0.25/M tokens, Sonnet ~$3/M tokens
- Monitor with `aws ce get-cost-and-usage`

## Teardown

```bash
cd infrastructure
cdk destroy --all -c env=dev
```

> ⚠️ Production stacks have `RETAIN` removal policies. Delete resources manually.
