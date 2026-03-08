# OpenSearch Quick Start Guide

## Overview

This guide provides quick instructions for setting up and using the OpenSearch domain for the AI Builder Copilot knowledge base.

## Prerequisites

- AWS CDK deployed (Storage Stack)
- Python 3.11+ with required dependencies
- AWS credentials configured

## Step 1: Deploy the OpenSearch Domain

The OpenSearch domain is automatically created when you deploy the Storage Stack:

```bash
cd infrastructure
cdk deploy AIBuilderCopilot-Storage-dev
```

This creates:
- VPC with private subnets
- OpenSearch domain (2 t3.small.search nodes)
- Security groups and access policies
- KMS encryption keys

## Step 2: Get the OpenSearch Endpoint

After deployment, retrieve the OpenSearch endpoint:

```bash
# Using AWS CLI
aws cloudformation describe-stacks \
  --stack-name AIBuilderCopilot-Storage-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`OpenSearchEndpoint`].OutputValue' \
  --output text

# Or using CDK
cdk deploy --outputs-file outputs.json
cat outputs.json | grep OpenSearchEndpoint
```

## Step 3: Configure the Index

Run the index configuration script:

```bash
# Set environment variables
export OPENSEARCH_ENDPOINT="your-domain-endpoint.us-east-1.es.amazonaws.com"
export AWS_REGION="us-east-1"

# Run configuration script
python infrastructure/scripts/configure_opensearch_index.py \
  --endpoint $OPENSEARCH_ENDPOINT \
  --region $AWS_REGION
```

Expected output:
```
Connecting to OpenSearch domain: your-domain-endpoint.us-east-1.es.amazonaws.com
Connected to OpenSearch version: 2.11.0
Successfully created index 'knowledge-base'
Index 'knowledge-base' configuration verified successfully
✓ OpenSearch index configuration completed successfully
```

## Step 4: Verify the Configuration

Verify the index was created correctly:

```bash
python infrastructure/scripts/configure_opensearch_index.py \
  --endpoint $OPENSEARCH_ENDPOINT \
  --region $AWS_REGION \
  --verify-only
```

## Step 5: Index Your First Document

Example Python code to index a document:

```python
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

# Create client
credentials = boto3.Session().get_credentials()
auth = AWSV4SignerAuth(credentials, 'us-east-1', 'es')

client = OpenSearch(
    hosts=[{'host': 'your-endpoint.us-east-1.es.amazonaws.com', 'port': 443}],
    http_auth=auth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)

# Index a document
document = {
    "document_id": "doc001_chunk001",
    "content": "AWS Lambda is a serverless compute service...",
    "embedding": [0.1, 0.2, ...],  # 1536-dimensional vector
    "metadata": {
        "source": "aws-lambda-guide.pdf",
        "timestamp": "2024-01-15T10:30:00Z",
        "chunk_id": "chunk001",
        "file_type": "pdf"
    }
}

response = client.index(
    index="knowledge-base",
    id=document["document_id"],
    body=document
)

print(f"Document indexed: {response['result']}")
```

## Step 6: Perform a Vector Search

Example search query:

```python
# Generate embedding for query (using Bedrock Titan Embeddings)
query_embedding = [0.15, 0.25, ...]  # 1536-dimensional vector

# Search for top 5 similar documents
query = {
    "size": 5,
    "query": {
        "knn": {
            "embedding": {
                "vector": query_embedding,
                "k": 5
            }
        }
    },
    "min_score": 0.7
}

response = client.search(
    index="knowledge-base",
    body=query
)

# Process results
for hit in response['hits']['hits']:
    print(f"Score: {hit['_score']}")
    print(f"Content: {hit['_source']['content']}")
    print(f"Source: {hit['_source']['metadata']['source']}")
    print("---")
```

## Common Operations

### Check Index Health

```bash
curl -XGET "https://$OPENSEARCH_ENDPOINT/_cat/indices/knowledge-base?v" \
  --aws-sigv4 "aws:amz:us-east-1:es" \
  --user "$AWS_ACCESS_KEY_ID:$AWS_SECRET_ACCESS_KEY"
```

### Count Documents

```python
count = client.count(index="knowledge-base")
print(f"Total documents: {count['count']}")
```

### Delete Index (Caution!)

```python
client.indices.delete(index="knowledge-base")
```

## Troubleshooting

### Connection Timeout

If you get connection timeouts:
1. Ensure you're running from within the VPC (e.g., Lambda function)
2. Check security group allows HTTPS (port 443)
3. Verify IAM role has necessary permissions

### Index Creation Fails

If index creation fails:
1. Check OpenSearch domain is active: `aws opensearch describe-domain --domain-name <name>`
2. Verify KNN plugin is enabled (default in OpenSearch 2.11)
3. Check CloudWatch logs for detailed errors

### Search Returns No Results

If searches return no results:
1. Verify documents are indexed: `client.count(index="knowledge-base")`
2. Check embedding dimension is 1536
3. Lower similarity threshold (min_score)
4. Verify embeddings are normalized

## Next Steps

- Set up document indexing pipeline (Task 10)
- Implement RAG retrieval engine (Task 9)
- Configure Lambda functions to access OpenSearch
- Set up monitoring and alerts

## Resources

- [Full Documentation](./OPENSEARCH_CONFIGURATION.md)
- [OpenSearch KNN Plugin](https://opensearch.org/docs/latest/search-plugins/knn/index/)
- [AWS OpenSearch Service](https://docs.aws.amazon.com/opensearch-service/)
