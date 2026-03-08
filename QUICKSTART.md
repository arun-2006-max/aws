# Quick Start Guide

This guide will help you get the AI Builder Copilot up and running quickly.

## Prerequisites

Before you begin, ensure you have:

- ✅ Python 3.11 or higher installed
- ✅ Node.js 18 or higher installed
- ✅ AWS CLI installed and configured (`aws configure`)
- ✅ AWS CDK CLI installed (`npm install -g aws-cdk`)
- ✅ AWS account with appropriate permissions

## Step 1: Clone and Setup

### Option A: Automated Setup (Recommended)

**Linux/Mac:**
```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

**Windows (PowerShell):**
```powershell
.\scripts\setup.ps1
```

### Option B: Manual Setup

**1. Setup Infrastructure:**
```bash
cd infrastructure
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

**2. Setup Lambda Functions:**
```bash
cd lambda
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

**3. Setup Frontend:**
```bash
cd frontend
npm install
cd ..
```

## Step 2: Configure AWS

Ensure your AWS credentials are configured:

```bash
aws configure
```

You'll need:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (e.g., us-east-1)
- Output format (json)

## Step 3: Bootstrap CDK (First Time Only)

```bash
cd infrastructure
cdk bootstrap
```

This creates the necessary S3 bucket and IAM roles for CDK deployments.

## Step 4: Deploy Infrastructure

### Deploy to Development Environment

**Linux/Mac:**
```bash
./scripts/deploy.sh dev
```

**Windows (PowerShell):**
```powershell
.\scripts\deploy.ps1 dev
```

**Or manually:**
```bash
cd infrastructure
source venv/bin/activate  # Windows: venv\Scripts\activate
cdk deploy --all --context env=dev
```

This will deploy:
- ✅ DynamoDB tables
- ✅ S3 buckets
- ✅ Cognito User Pool
- ✅ Lambda functions
- ✅ API Gateway

**Note:** The deployment will take approximately 5-10 minutes.

## Step 5: Get API Endpoint

After deployment, CDK will output the API Gateway endpoint URL:

```
Outputs:
AIBuilderCopilot-API-dev.ApiEndpoint = https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/dev/
```

Copy this URL - you'll need it for the frontend configuration.

## Step 6: Configure Frontend

Create a `.env.local` file in the `frontend` directory:

```bash
cd frontend
cat > .env.local << EOF
REACT_APP_API_ENDPOINT=https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/dev
REACT_APP_USER_POOL_ID=us-east-1_xxxxxxxxx
REACT_APP_USER_POOL_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx
REACT_APP_AWS_REGION=us-east-1
EOF
```

Replace the values with your actual outputs from the CDK deployment.

## Step 7: Start Frontend

```bash
cd frontend
npm start
```

The application will open in your browser at `http://localhost:3000`

## Step 8: Create a Test User

You can create a test user via AWS Console or AWS CLI:

**Via AWS CLI:**
```bash
aws cognito-idp sign-up \
  --client-id YOUR_CLIENT_ID \
  --username test@example.com \
  --password TestPassword123! \
  --user-attributes Name=email,Value=test@example.com

# Confirm the user (admin command)
aws cognito-idp admin-confirm-sign-up \
  --user-pool-id YOUR_USER_POOL_ID \
  --username test@example.com
```

## Verification Checklist

After deployment, verify:

- [ ] API Gateway endpoint is accessible
- [ ] Cognito User Pool is created
- [ ] DynamoDB tables exist (6 tables)
- [ ] S3 buckets exist (2 buckets)
- [ ] Lambda functions are deployed (6 functions)
- [ ] Frontend starts without errors
- [ ] Can create and login with test user

## Troubleshooting

### Issue: CDK Bootstrap Fails

**Solution:** Ensure your AWS credentials have sufficient permissions:
- CloudFormation
- S3
- IAM
- SSM Parameter Store

### Issue: Lambda Deployment Fails

**Solution:** Check that the Lambda handler code exists:
```bash
ls -la lambda/handlers/handler.py
```

### Issue: Frontend Won't Start

**Solution:** Clear node_modules and reinstall:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Issue: API Gateway Returns 403

**Solution:** Ensure you're sending a valid JWT token from Cognito in the Authorization header.

## Next Steps

1. **Upload Knowledge Base Documents:** Upload documents to the S3 knowledge base bucket
2. **Test API Endpoints:** Use Postman or curl to test the API
3. **Implement Lambda Handlers:** Continue with Task 2 in the implementation plan
4. **Configure Bedrock:** Ensure Bedrock models are enabled in your AWS account

## Useful Commands

**View CDK Stacks:**
```bash
cd infrastructure
cdk list
```

**View Stack Differences:**
```bash
cdk diff --context env=dev
```

**Destroy Infrastructure:**
```bash
cdk destroy --all --context env=dev
```

**View Lambda Logs:**
```bash
aws logs tail /aws/lambda/AIBuilderCopilot-ChatHandler-dev --follow
```

**List DynamoDB Tables:**
```bash
aws dynamodb list-tables
```

## Support

For issues or questions:
1. Check the [ARCHITECTURE.md](ARCHITECTURE.md) for system design details
2. Review the [README.md](README.md) for general information
3. Check the implementation tasks in `.kiro/specs/ai-builder-copilot/tasks.md`

## Environment-Specific Deployments

**Staging:**
```bash
./scripts/deploy.sh staging
```

**Production:**
```bash
./scripts/deploy.sh prod
```

**Note:** Production deployment enables MFA and uses larger instance types.
