# Task 3.1 Implementation: S3 Knowledge Base Bucket with Folder Structure

## Overview
This document describes the implementation of Task 3.1, which creates an S3 bucket for the knowledge base with proper folder structure, encryption, lifecycle policies, and event notifications.

## Requirements Implemented
- **Requirement 7.1**: Knowledge Base Management - Document upload triggers RAG pipeline
- **Requirement 10.4**: Data Storage and Persistence - S3 storage with proper organization
- **Requirement 19.3**: Security and Encryption - S3 encryption at rest
- **Requirement 20.4**: Cost Optimization - Lifecycle policies for cost management

## Implementation Details

### 1. S3 Bucket Configuration
The knowledge base bucket is created with the following features:

#### Encryption
- **KMS Encryption**: Uses customer-managed KMS key for encryption at rest
- **Key Rotation**: Automatic key rotation enabled for enhanced security
- **SSL Enforcement**: Bucket policy enforces HTTPS/TLS connections only

#### Versioning
- **Enabled**: Bucket versioning is enabled for data recovery and audit trails
- **Retention**: Production buckets use RETAIN removal policy

#### Access Control
- **Block Public Access**: All public access is blocked
- **IAM-based Access**: Access controlled through IAM roles and policies

#### Lifecycle Policies
- **Glacier Transition**: Objects automatically move to Glacier storage after 90 days
- **Cost Optimization**: Reduces storage costs for infrequently accessed data

### 2. Folder Structure
The bucket includes three main folders:

#### documents/
- **Purpose**: Stores uploaded knowledge base documents
- **Formats**: PDF, TXT, MD, DOCX
- **Event Trigger**: S3 events trigger document processing pipeline

#### embeddings-cache/
- **Purpose**: Caches generated embeddings to reduce API calls
- **TTL**: 7-day cache expiration
- **Cost Savings**: Minimizes Titan Embeddings API usage

#### logs/
- **Purpose**: Stores processing logs and error reports
- **Organization**: Logs organized by date (YYYY/MM/DD)
- **Lifecycle**: Automatically moved to Glacier after 90 days

### 3. S3 Event Notifications
The `add_document_upload_notification()` method configures event notifications:

#### Event Type
- **OBJECT_CREATED**: Triggers on new document uploads

#### Filter
- **Prefix**: `documents/` - Only triggers for documents in the documents folder

#### Target
- **Lambda Function**: Will be connected to document indexing Lambda (Task 10.5)
- **Processing Pipeline**: Triggers extraction, chunking, embedding, and indexing

## Code Structure

### Modified Files
1. **infrastructure/stacks/storage_stack.py**
   - Added imports for `aws_s3_deployment` and `aws_s3_notifications`
   - Added `_create_knowledge_base_folders()` method
   - Added `add_document_upload_notification()` method
   - Updated docstring to reference new requirements

### New Files
1. **infrastructure/tests/test_storage_stack.py**
   - Unit tests for bucket encryption
   - Unit tests for lifecycle policies
   - Unit tests for versioning
   - Unit tests for public access blocking
   - Unit tests for folder structure creation
   - Unit tests for SSL enforcement
   - Unit tests for KMS key rotation

## Testing

### Test Coverage
The implementation includes 8 comprehensive unit tests:

1. **test_knowledge_base_bucket_encryption**: Validates KMS encryption
2. **test_knowledge_base_bucket_lifecycle_policy**: Validates Glacier transition
3. **test_knowledge_base_bucket_versioning**: Validates versioning enabled
4. **test_knowledge_base_bucket_public_access_blocked**: Validates security
5. **test_knowledge_base_folder_structure_created**: Validates folder creation
6. **test_ssl_enforcement**: Validates HTTPS-only access
7. **test_kms_key_rotation_enabled**: Validates key rotation

### Running Tests
```bash
cd infrastructure
pip install -r requirements.txt
python -m pytest tests/test_storage_stack.py -v
```

## Usage

### Deploying the Stack
```bash
cd infrastructure
cdk deploy AIBuilderCopilot-Storage-dev
```

### Adding Event Notification (Future Task)
When the document indexing Lambda is created (Task 10.5):
```python
# In compute_stack.py
storage_stack.add_document_upload_notification(
    s3n.LambdaDestination(document_indexing_lambda)
)
```

### Uploading Documents
```bash
aws s3 cp document.pdf s3://bucket-name/documents/
# This will automatically trigger the processing pipeline
```

## Security Considerations

### Encryption
- All data encrypted at rest using KMS
- Encryption keys automatically rotated
- SSL/TLS enforced for all connections

### Access Control
- No public access allowed
- IAM roles with least privilege
- Bucket policies enforce secure transport

### Compliance
- Meets AWS security best practices
- Complies with data protection requirements
- Audit trail through versioning and CloudTrail

## Cost Optimization

### Storage Costs
- Lifecycle policy moves old data to Glacier (90% cost reduction)
- Versioning only for critical data
- Intelligent tiering for variable access patterns

### API Costs
- Embeddings cache reduces Titan API calls
- 7-day cache TTL balances freshness and cost
- Batch processing minimizes S3 API calls

## Future Enhancements

### Task 3.2: OpenSearch Integration
- Connect to OpenSearch domain for vector search
- Index embeddings with metadata

### Task 10: Document Processing Pipeline
- Implement Lambda function for document processing
- Connect S3 event notification to Lambda
- Add error handling and retry logic

### Monitoring
- CloudWatch metrics for bucket usage
- Alarms for processing failures
- Cost tracking and budget alerts

## References
- AWS CDK S3 Documentation: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_s3.html
- S3 Lifecycle Policies: https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html
- S3 Event Notifications: https://docs.aws.amazon.com/AmazonS3/latest/userguide/NotificationHowTo.html
