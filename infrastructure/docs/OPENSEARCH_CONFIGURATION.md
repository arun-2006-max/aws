# OpenSearch Configuration Documentation

## Overview

This document describes the OpenSearch domain and index configuration for the AI Builder Copilot knowledge base. The OpenSearch domain provides vector search capabilities for Retrieval Augmented Generation (RAG) using k-nearest neighbors (KNN) algorithm.

**Implements Requirements:** 2.2, 2.3

## Architecture

### OpenSearch Domain

The OpenSearch domain is deployed with the following configuration:

- **Version:** OpenSearch 2.11
- **Instance Type:** t3.small.search (2 data nodes)
- **Storage:** 20 GB GP3 EBS per node (40 GB total)
- **Availability:** Multi-AZ deployment across 2 availability zones
- **Network:** VPC-based deployment in private subnets

### Security Configuration

1. **VPC Isolation**
   - Deployed in private subnets with NAT gateway for outbound connectivity
   - Security group restricts access to HTTPS (port 443) from within VPC only
   - No public internet access

2. **Encryption**
   - Encryption at rest using AWS KMS customer-managed key
   - Node-to-node encryption enabled
   - HTTPS enforcement for all connections (TLS 1.2+)

3. **Access Control**
   - Fine-grained access control enabled
   - IAM-based authentication using AWS Signature V4
   - Lambda functions granted read/write access via IAM roles

### Cost Optimization

- Single NAT gateway for cost savings
- t3.small.search instances (suitable for development/staging)
- 20 GB storage per node (expandable as needed)
- Multi-AZ standby disabled for cost optimization

## Index Configuration

### Knowledge Base Index

**Index Name:** `knowledge-base`

The knowledge base index stores document chunks with their vector embeddings for semantic search.

#### Index Settings

```json
{
  "settings": {
    "index": {
      "knn": true,
      "knn.algo_param.ef_search": 512,
      "number_of_shards": 2,
      "number_of_replicas": 1
    }
  }
}
```

- **knn:** Enables KNN plugin for vector search
- **ef_search:** Search quality parameter (higher = more accurate but slower)
- **shards:** 2 shards for parallel processing
- **replicas:** 1 replica for high availability

#### Index Mapping

```json
{
  "mappings": {
    "properties": {
      "document_id": {
        "type": "keyword"
      },
      "content": {
        "type": "text",
        "analyzer": "standard"
      },
      "embedding": {
        "type": "knn_vector",
        "dimension": 1536,
        "method": {
          "name": "hnsw",
          "space_type": "cosinesim",
          "engine": "nmslib",
          "parameters": {
            "ef_construction": 512,
            "m": 16
          }
        }
      },
      "metadata": {
        "properties": {
          "source": {"type": "keyword"},
          "timestamp": {"type": "date"},
          "chunk_id": {"type": "keyword"},
          "file_type": {"type": "keyword"}
        }
      }
    }
  }
}
```

#### Field Descriptions

1. **document_id** (keyword)
   - Unique identifier for each document chunk
   - Used for deduplication and updates

2. **content** (text)
   - The actual text content of the document chunk
   - Indexed with standard analyzer for full-text search
   - Maximum 512 tokens per chunk (Requirement 7.2)

3. **embedding** (knn_vector)
   - 1536-dimensional vector representation (Titan Embeddings dimension)
   - Uses HNSW (Hierarchical Navigable Small World) algorithm
   - Cosine similarity for semantic search
   - **Implements Requirement 2.2:** Vector embeddings for semantic search
   - **Implements Requirement 16.5:** 1536-dimensional embeddings

4. **metadata** (object)
   - **source:** Original document filename/path
   - **timestamp:** When the document was indexed
   - **chunk_id:** Identifier for the chunk within the document
   - **file_type:** Document format (PDF, TXT, MD, DOCX)

### KNN Algorithm Configuration

The index uses the HNSW (Hierarchical Navigable Small World) algorithm for efficient approximate nearest neighbor search:

- **Algorithm:** HNSW
- **Space Type:** Cosine similarity (cosinesim)
- **Engine:** nmslib (high-performance library)
- **ef_construction:** 512 (build quality parameter)
- **m:** 16 (number of connections per node)

These parameters balance search accuracy with performance and memory usage.

## Usage

### Creating the Index

After deploying the OpenSearch domain via CDK, run the configuration script:

```bash
# Get OpenSearch endpoint from CDK outputs
OPENSEARCH_ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name AIBuilderCopilot-Storage-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`OpenSearchEndpoint`].OutputValue' \
  --output text)

# Run configuration script
python infrastructure/scripts/configure_opensearch_index.py \
  --endpoint $OPENSEARCH_ENDPOINT \
  --region us-east-1
```

### Verifying the Index

To verify the index configuration without creating it:

```bash
python infrastructure/scripts/configure_opensearch_index.py \
  --endpoint $OPENSEARCH_ENDPOINT \
  --region us-east-1 \
  --verify-only
```

### Querying the Index

#### Vector Search Query

To retrieve the top 5 most similar documents (Requirement 2.3):

```python
from opensearchpy import OpenSearch

# Query with embedding vector
query = {
    "size": 5,  # Top 5 results (Requirement 2.3)
    "query": {
        "knn": {
            "embedding": {
                "vector": embedding_vector,  # 1536-dimensional vector
                "k": 5
            }
        }
    },
    "min_score": 0.7  # Similarity threshold (Requirement 2.4)
}

response = client.search(
    index="knowledge-base",
    body=query
)

# Extract results
documents = [hit["_source"] for hit in response["hits"]["hits"]]
```

#### Hybrid Search (Vector + Text)

Combine vector search with text search for better results:

```python
query = {
    "size": 5,
    "query": {
        "bool": {
            "should": [
                {
                    "knn": {
                        "embedding": {
                            "vector": embedding_vector,
                            "k": 5
                        }
                    }
                },
                {
                    "match": {
                        "content": query_text
                    }
                }
            ]
        }
    },
    "min_score": 0.7
}
```

### Indexing Documents

To index a document chunk:

```python
document = {
    "document_id": "doc123_chunk001",
    "content": "This is the text content of the document chunk...",
    "embedding": embedding_vector,  # 1536-dimensional list
    "metadata": {
        "source": "user-guide.pdf",
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
```

### Batch Indexing

For efficient bulk indexing:

```python
from opensearchpy import helpers

actions = [
    {
        "_index": "knowledge-base",
        "_id": doc["document_id"],
        "_source": doc
    }
    for doc in documents
]

helpers.bulk(client, actions)
```

## Monitoring

### Index Statistics

Check index health and statistics:

```bash
# Index health
curl -XGET "https://$OPENSEARCH_ENDPOINT/_cat/indices/knowledge-base?v"

# Index stats
curl -XGET "https://$OPENSEARCH_ENDPOINT/knowledge-base/_stats"
```

### Search Performance

Monitor search latency and throughput:

```bash
# Search stats
curl -XGET "https://$OPENSEARCH_ENDPOINT/knowledge-base/_stats/search"
```

### CloudWatch Metrics

The OpenSearch domain emits metrics to CloudWatch:

- **ClusterStatus.green/yellow/red:** Cluster health
- **SearchLatency:** Average search latency
- **SearchRate:** Number of searches per minute
- **IndexingLatency:** Average indexing latency
- **IndexingRate:** Number of documents indexed per minute
- **CPUUtilization:** CPU usage percentage
- **JVMMemoryPressure:** JVM heap memory usage

## Troubleshooting

### Connection Issues

If unable to connect to OpenSearch:

1. Verify Lambda function is in the same VPC as OpenSearch domain
2. Check security group allows HTTPS (port 443) from Lambda security group
3. Verify IAM role has necessary permissions

### Index Creation Fails

If index creation fails:

1. Check OpenSearch domain is active and healthy
2. Verify KNN plugin is enabled (should be by default in OpenSearch 2.11)
3. Check CloudWatch logs for detailed error messages

### Search Returns No Results

If searches return no results:

1. Verify documents are indexed: `GET /knowledge-base/_count`
2. Check embedding dimension matches (1536)
3. Lower similarity threshold (min_score) if too restrictive
4. Verify embedding vectors are normalized

### Performance Issues

If searches are slow:

1. Increase `ef_search` parameter for better accuracy (but slower)
2. Decrease `ef_search` for faster searches (but less accurate)
3. Consider scaling up instance type or adding more nodes
4. Monitor JVM memory pressure and CPU utilization

## Maintenance

### Reindexing

To reindex all documents (e.g., after changing mapping):

```bash
# Create new index with updated mapping
POST /knowledge-base-v2
{
  "settings": {...},
  "mappings": {...}
}

# Reindex from old to new
POST /_reindex
{
  "source": {"index": "knowledge-base"},
  "dest": {"index": "knowledge-base-v2"}
}

# Update alias
POST /_aliases
{
  "actions": [
    {"remove": {"index": "knowledge-base", "alias": "knowledge-base-current"}},
    {"add": {"index": "knowledge-base-v2", "alias": "knowledge-base-current"}}
  ]
}
```

### Backup and Restore

OpenSearch supports automated snapshots to S3:

1. Configure snapshot repository in S3
2. Create manual or automated snapshots
3. Restore from snapshots when needed

## References

- [OpenSearch KNN Plugin Documentation](https://opensearch.org/docs/latest/search-plugins/knn/index/)
- [HNSW Algorithm](https://arxiv.org/abs/1603.09320)
- [AWS OpenSearch Service](https://docs.aws.amazon.com/opensearch-service/)
- Requirements 2.2, 2.3, 7.2, 16.5
