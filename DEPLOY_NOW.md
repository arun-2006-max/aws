# Quick Deployment Guide - AI Builder Copilot

## 🚀 Deploy to AWS in 10 Minutes

This guide will get your AI Builder Copilot infrastructure deployed to AWS quickly.

---

## Prerequisites Check

```powershell
# 1. Check Python version (need 3.11+)
python --version

# 2. Check if AWS CLI is configured
aws sts get-caller-identity

# 3. Check if you have AWS CDK installed
cdk --version
```

If any of these fail, see "Install Prerequisites" section below.

---

## Quick Deploy Steps

### Step 1: Install Dependencies

```powershell
# Navigate to infrastructure directory
cd infrastructure

# Install Python dependencies
pip install -r requirements.txt
```

### Step 2: Bootstrap CDK (First Time Only)

```powershell
# Bootstrap CDK in your AWS account
cdk bootstrap aws://ACCOUNT-ID/REGION

# Example:
# cdk bootstrap aws://123456789012/us-east-1
```

### Step 3: Deploy Infrastructure

```powershell
# Deploy all stacks at once
cdk deploy --all --require-approval never

# This will create:
# - DynamoDB tables (6 tables)
# - S3 buckets (2 buckets)
# - OpenSearch domain (takes ~15 minutes)
# - Cognito User Pool
# - Lambda functions (6 functions)
# - API Gateway
```

**Note:** OpenSearch domain creation takes 10-15 minutes. Grab a coffee! ☕

### Step 4: Configure OpenSearch Index

```powershell
# Get the OpenSearch endpoint from outputs
$ENDPOINT = aws cloudformation describe-stacks `
  --stack-name AIBuilderCopilot-Storage-dev `
  --query 'Stacks[0].Outputs[?OutputKey==``OpenSearchEndpoint``].OutputValue' `
  --output text

# Configure the index
python scripts/configure_opensearch_index.py --endpoint $ENDPOINT --region us-east-1
```

### Step 5: Verify Deployment

```powershell
# Check all stacks are deployed
cdk list

# Expected output:
# AIBuilderCopilot-Storage-dev
# AIBuilderCopilot-Auth-dev
# AIBuilderCopilot-Compute-dev
# AIBuilderCopilot-API-dev

# Get API Gateway URL
aws cloudformation describe-stacks `
  --stack-name AIBuilderCopilot-API-dev `
  --query 'Stacks[0].Outputs[?OutputKey==``ApiUrl``].OutputValue' `
  --output text
```

---

## Install Prerequisites (If Needed)

### Install Python 3.11

**Windows:**
```powershell
# Download from python.org or use winget
winget install Python.Python.3.11
```

### Install AWS CLI

**Windows:**
```powershell
# Download MSI installer from:
# https://aws.amazon.com/cli/

# Or use winget
winget install Amazon.AWSCLI
```

### Configure AWS Credentials

```powershell
aws configure

# Enter:
# AWS Access Key ID: YOUR_ACCESS_KEY
# AWS Secret Access Key: YOUR_SECRET_KEY
# Default region: us-east-1
# Default output format: json
```

### Install AWS CDK

```powershell
npm install -g aws-cdk

# Verify installation
cdk --version
```

---

## What Gets Deployed

### DynamoDB Tables
- Users
- Sessions
- InteractionLogs
- LearningProgress
- KnowledgeGaps
- ResponseCache

### S3 Buckets
- Knowledge Base Bucket (with folders: documents/, embeddings-cache/, logs/)
- Logs Bucket

### OpenSearch
- 2-node cluster (t3.small.search)
- VPC-based deployment
- KNN plugin enabled
- knowledge-base index

### Cognito
- User Pool for authentication
- App Client for frontend

### Lambda Functions
- chatHandler
- learningAnalysisHandler
- debugAssistantHandler
- userProgressHandler
- feedbackHandler
- documentIndexingHandler

### API Gateway
- REST API with 5 endpoints
- Cognito authorizer
- CORS enabled

---

## Estimated Deployment Time

- **CDK Bootstrap:** 2-3 minutes (first time only)
- **Storage Stack:** 15-20 minutes (OpenSearch takes longest)
- **Auth Stack:** 2-3 minutes
- **Compute Stack:** 3-5 minutes
- **API Stack:** 2-3 minutes
- **OpenSearch Index:** 1 minute

**Total:** ~25-35 minutes

---

## Estimated Monthly Cost

### Development Environment
- OpenSearch: ~$70
- DynamoDB: ~$5
- S3: ~$2
- Lambda: ~$5
- NAT Gateway: ~$32
- Bedrock: ~$10-50 (usage-based)

**Total:** ~$130-170/month

### Cost Optimization Tips
1. Delete the stack when not in use: `cdk destroy --all`
2. Use smaller OpenSearch instances for testing
3. Enable S3 lifecycle policies (already configured)
4. Use on-demand DynamoDB billing (already configured)

---

## Troubleshooting

### CDK Bootstrap Fails
```powershell
# Make sure you have admin permissions
aws sts get-caller-identity

# Try with explicit account and region
cdk bootstrap aws://YOUR_ACCOUNT_ID/us-east-1
```

### OpenSearch Deployment Fails
- Check VPC limits in your account
- Ensure you have available Elastic IPs
- Verify service quotas for OpenSearch

### Lambda Deployment Fails
- Check IAM permissions
- Verify Lambda service quotas
- Check CloudWatch logs for errors

### Can't Access API Gateway
- Verify Cognito user pool is created
- Check API Gateway authorizer configuration
- Ensure CORS is enabled

---

## Testing the Deployment

### Test DynamoDB
```powershell
# List tables
aws dynamodb list-tables

# Describe a table
aws dynamodb describe-table --table-name AIBuilderCopilot-Users-dev
```

### Test S3
```powershell
# List buckets
aws s3 ls | Select-String "aibuildercopilot"

# Upload a test document
aws s3 cp test.pdf s3://YOUR-BUCKET-NAME/documents/
```

### Test OpenSearch
```powershell
# Check domain status
aws opensearch describe-domain --domain-name aibuildercopilot-dev

# Verify index (after configuration)
python infrastructure/scripts/configure_opensearch_index.py `
  --endpoint $ENDPOINT --region us-east-1 --verify-only
```

### Test Lambda
```powershell
# List functions
aws lambda list-functions | Select-String "AIBuilderCopilot"

# Invoke a function (after implementation)
aws lambda invoke --function-name chatHandler-dev response.json
```

---

## Next Steps After Deployment

1. **Upload Knowledge Base Documents**
   ```powershell
   aws s3 cp ./docs/ s3://YOUR-BUCKET/documents/ --recursive
   ```

2. **Create a Test User**
   ```powershell
   aws cognito-idp admin-create-user `
     --user-pool-id YOUR_POOL_ID `
     --username testuser `
     --user-attributes Name=email,Value=test@example.com
   ```

3. **Test the API**
   ```powershell
   # Get API URL
   $API_URL = aws cloudformation describe-stacks `
     --stack-name AIBuilderCopilot-API-dev `
     --query 'Stacks[0].Outputs[?OutputKey==``ApiUrl``].OutputValue' `
     --output text
   
   # Test health endpoint
   curl "$API_URL/health"
   ```

4. **Deploy Frontend**
   ```powershell
   cd frontend
   npm install
   npm run build
   # Deploy to S3 + CloudFront (optional)
   ```

---

## Cleanup (Delete Everything)

```powershell
# Delete all stacks
cdk destroy --all

# Confirm deletion when prompted
# This will delete all resources and stop billing
```

**Warning:** This will permanently delete all data!

---

## Getting Help

### Check Logs
```powershell
# CloudWatch logs
aws logs tail /aws/lambda/chatHandler-dev --follow

# CDK synthesis
cdk synth > template.yaml
```

### Common Issues
1. **"Stack already exists"** - Run `cdk deploy` again, it will update
2. **"Insufficient permissions"** - Check IAM role has admin access
3. **"Resource limit exceeded"** - Request quota increase in AWS Console
4. **"OpenSearch timeout"** - Wait 15-20 minutes, it's still creating

### Documentation
- Full docs: `infrastructure/docs/`
- Architecture: `ARCHITECTURE.md`
- Project status: `PROJECT_STATUS.md`
- OpenSearch guide: `infrastructure/docs/OPENSEARCH_QUICKSTART.md`

---

## Success Checklist

- [ ] AWS CLI configured
- [ ] CDK installed and bootstrapped
- [ ] All 4 stacks deployed successfully
- [ ] OpenSearch index configured
- [ ] Can list DynamoDB tables
- [ ] Can access S3 buckets
- [ ] API Gateway URL obtained
- [ ] Lambda functions visible in console

---

## 🎉 You're Done!

Your AI Builder Copilot infrastructure is now deployed on AWS!

**What you have:**
- ✅ Serverless backend infrastructure
- ✅ Vector database for RAG
- ✅ User authentication system
- ✅ API Gateway ready for requests
- ✅ Secure, encrypted data storage
- ✅ Cost-optimized configuration

**Next:** Implement the Lambda function handlers and deploy the frontend!

---

## Quick Reference Commands

```powershell
# Deploy
cdk deploy --all

# Update a single stack
cdk deploy AIBuilderCopilot-Storage-dev

# Check what will change
cdk diff

# View CloudFormation template
cdk synth

# Destroy everything
cdk destroy --all

# List all stacks
cdk list

# Get stack outputs
aws cloudformation describe-stacks --stack-name STACK_NAME
```

---

**Happy Deploying! 🚀**
