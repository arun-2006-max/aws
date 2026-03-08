# AI Builder Copilot - Architecture Documentation

## System Overview

The AI Builder Copilot is a serverless, cloud-native application built on AWS that provides context-aware AI assistance for learning and development. The system uses Retrieval Augmented Generation (RAG) to ground AI responses in a knowledge base and leverages Amazon Bedrock for intelligent model selection and response generation.

## Architecture Diagram

```
┌─────────────┐
│   Frontend  │ (React.js + TypeScript)
│  (Cognito)  │
└──────┬──────┘
       │ HTTPS
       ▼
┌─────────────────────────────────────────┐
│         API Gateway (REST)              │
│  - JWT Authentication                   │
│  - Request Validation                   │
│  - CORS Configuration                   │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│         Lambda Functions                │
│  - Chat Handler                         │
│  - Learning Analysis Handler            │
│  - Debug Assistant Handler              │
│  - User Progress Handler                │
│  - Feedback Handler                     │
│  - Document Indexing Handler            │
└──────┬──────────────────────────────────┘
       │
       ├──────────────┬──────────────┬─────────────┐
       ▼              ▼              ▼             ▼
┌──────────┐   ┌──────────┐   ┌──────────┐  ┌──────────┐
│ DynamoDB │   │    S3    │   │ Bedrock  │  │OpenSearch│
│  Tables  │   │ Buckets  │   │  Models  │  │  Domain  │
└──────────┘   └──────────┘   └──────────┘  └──────────┘
```

## Infrastructure Components

### 1. Storage Stack (storage_stack.py)

**DynamoDB Tables:**
- `Users` - User profile and metadata
- `Sessions` - Active user sessions with TTL
- `InteractionLogs` - Query/response history (partitioned by user_id, sorted by timestamp)
- `LearningProgress` - User learning metrics (partitioned by user_id, sorted by topic)
- `KnowledgeGaps` - Detected knowledge gaps (partitioned by user_id, sorted by gap_id)
- `ResponseCache` - Cached AI responses with TTL (3600 seconds)

**S3 Buckets:**
- `KnowledgeBaseBucket` - Document storage with lifecycle policies (Glacier after 90 days)
- `LogsBucket` - Application logs with lifecycle policies

**Security:**
- KMS encryption for all tables and buckets
- Point-in-time recovery enabled
- Versioning enabled for knowledge base

### 2. Auth Stack (auth_stack.py)

**Cognito User Pool:**
- Email-based authentication
- Password policy enforcement
- JWT token expiration: 1 hour
- Optional MFA (enabled in production)
- Account recovery via email

**App Client:**
- User password and SRP authentication flows
- No client secret (for frontend apps)
- Refresh token validity: 30 days

### 3. Compute Stack (compute_stack.py)

**Lambda Functions:**
- Runtime: Python 3.11
- Memory: 512 MB (default), 1024 MB (document indexing)
- Timeout: 30 seconds (default), 5 minutes (document indexing)
- IAM roles with least privilege
- CloudWatch Logs with configurable retention

**Environment Variables:**
- Table names, bucket names
- Bedrock region
- Environment identifier

### 4. API Stack (api_stack.py)

**API Gateway:**
- REST API with regional endpoint
- Cognito authorizer for JWT validation
- Request validators for all POST endpoints
- CORS enabled
- Throttling: 100 req/sec, burst 200
- CloudWatch logging and metrics

**Endpoints:**
- `POST /chat` - AI chat interface
- `POST /learning-analysis` - Knowledge gap analysis
- `POST /debug-assistant` - Code debugging
- `GET /user-progress` - Progress retrieval
- `POST /store-feedback` - Feedback storage

## Data Flow

### Chat Request Flow

1. User submits query via frontend
2. Frontend sends JWT token + query to API Gateway
3. API Gateway validates JWT with Cognito
4. Lambda handler receives request
5. Query validation (length, format)
6. Cache lookup in DynamoDB
7. If cache miss:
   - Generate embeddings (Titan)
   - Query OpenSearch for relevant documents
   - Augment prompt with context
   - Select appropriate Bedrock model
   - Invoke model and get response
   - Store response in cache
8. Log interaction to DynamoDB
9. Update learning progress
10. Return response to frontend

### Document Indexing Flow

1. Document uploaded to S3 knowledge base bucket
2. S3 event triggers Lambda function
3. Extract text from document (PDF, TXT, MD, DOCX)
4. Chunk document (512 tokens per chunk)
5. Generate embeddings for each chunk (Titan)
6. Store embeddings in OpenSearch with metadata
7. Log indexing status

## Security Architecture

### Authentication & Authorization
- Cognito JWT tokens for user authentication
- API Gateway authorizer validates tokens
- User ID extracted from token for all operations

### Encryption
- Data at rest: KMS encryption for DynamoDB and S3
- Data in transit: TLS 1.2+ enforced
- Key rotation enabled

### IAM Permissions
- Separate IAM role per Lambda function
- Least privilege principle
- No wildcard permissions except Bedrock (service limitation)

### Input Validation
- Query length limits (10,000 characters)
- JSON schema validation at API Gateway
- Input sanitization in Lambda handlers

## Cost Optimization

### Model Selection
- 60%+ queries routed to Claude Haiku (lowest cost)
- Complex queries use Claude Sonnet
- Fallback to Nova Lite

### Caching
- Response cache (1 hour TTL)
- Embedding cache (7 days)
- RAG results cache (24 hours)

### Storage
- S3 lifecycle policies (Glacier after 90 days)
- DynamoDB on-demand billing
- CloudWatch log retention limits

### Compute
- Right-sized Lambda memory
- Connection pooling and client reuse
- Provisioned concurrency only in production

## Monitoring & Observability

### CloudWatch Metrics
- API Gateway: Request count, latency, errors
- Lambda: Invocations, duration, errors, throttles
- DynamoDB: Read/write capacity, throttles
- Custom: Token usage, model selection, cache hit rate

### Logging
- Structured JSON logs
- Request/response logging
- Error logs with stack traces
- Performance metrics

### Alerting
- SNS notifications for critical errors
- Budget alerts for cost thresholds
- Error rate alarms

## Deployment Strategy

### Environments
- **Dev**: Single instance, minimal resources, 7-day log retention
- **Staging**: Multi-instance, moderate resources, 30-day log retention
- **Prod**: High availability, full resources, 90-day log retention, MFA enabled

### CI/CD
- Infrastructure as Code (AWS CDK)
- Automated testing before deployment
- Blue-green deployment for Lambda functions
- Rollback capability

## Scalability

### Horizontal Scaling
- Lambda auto-scales to handle load
- DynamoDB on-demand scales automatically
- API Gateway handles throttling

### Performance Optimization
- Response caching reduces Bedrock calls
- Embedding caching reduces Titan calls
- Connection pooling reduces cold starts
- CloudFront caching for static content

## Disaster Recovery

### Backup Strategy
- DynamoDB point-in-time recovery
- S3 versioning for knowledge base
- Cross-region replication (production only)

### Recovery Objectives
- RTO (Recovery Time Objective): 1 hour
- RPO (Recovery Point Objective): 5 minutes

## Future Enhancements

1. **Multi-region deployment** for global availability
2. **WebSocket support** for streaming responses
3. **CloudFront distribution** for frontend hosting
4. **Step Functions** for complex workflows
5. **EventBridge** for event-driven architecture
6. **X-Ray** for distributed tracing
