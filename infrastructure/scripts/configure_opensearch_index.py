"""
OpenSearch Index Configuration Script
Implements Requirements 2.2, 2.3

This script creates the OpenSearch index with knn_vector mapping for embeddings.
It should be run after the OpenSearch domain is deployed.

Usage:
    python configure_opensearch_index.py --endpoint <opensearch-endpoint> --region <aws-region>
"""
import argparse
import json
import sys
from typing import Dict, Any
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth


def get_opensearch_client(endpoint: str, region: str) -> OpenSearch:
    """
    Create OpenSearch client with AWS authentication
    
    Args:
        endpoint: OpenSearch domain endpoint (without https://)
        region: AWS region
        
    Returns:
        OpenSearch client instance
    """
    credentials = boto3.Session().get_credentials()
    auth = AWSV4SignerAuth(credentials, region, 'es')
    
    client = OpenSearch(
        hosts=[{'host': endpoint, 'port': 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=30
    )
    
    return client


def create_knowledge_base_index(client: OpenSearch, index_name: str = "knowledge-base") -> bool:
    """
    Create knowledge base index with knn_vector mapping
    Implements Requirements 2.2, 2.3
    
    Index structure:
    - document_id: Unique identifier for the document chunk
    - content: The actual text content
    - embedding: 1536-dimensional vector for semantic search (Titan Embeddings dimension)
    - metadata: Additional information (source, timestamp, chunk_id)
    
    Args:
        client: OpenSearch client
        index_name: Name of the index to create
        
    Returns:
        True if successful, False otherwise
    """
    # Index configuration with knn_vector mapping
    index_body = {
        "settings": {
            "index": {
                "knn": True,  # Enable KNN plugin
                "knn.algo_param.ef_search": 512,  # Search quality parameter
                "number_of_shards": 2,
                "number_of_replicas": 1
            }
        },
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
                    "dimension": 1536,  # Titan Embeddings dimension (Requirement 16.5)
                    "method": {
                        "name": "hnsw",  # Hierarchical Navigable Small World algorithm
                        "space_type": "cosinesim",  # Cosine similarity for semantic search
                        "engine": "nmslib",
                        "parameters": {
                            "ef_construction": 512,
                            "m": 16
                        }
                    }
                },
                "metadata": {
                    "properties": {
                        "source": {
                            "type": "keyword"
                        },
                        "timestamp": {
                            "type": "date"
                        },
                        "chunk_id": {
                            "type": "keyword"
                        },
                        "file_type": {
                            "type": "keyword"
                        }
                    }
                }
            }
        }
    }
    
    try:
        # Check if index already exists
        if client.indices.exists(index=index_name):
            print(f"Index '{index_name}' already exists")
            return True
        
        # Create the index
        response = client.indices.create(
            index=index_name,
            body=index_body
        )
        
        print(f"Successfully created index '{index_name}'")
        print(f"Response: {json.dumps(response, indent=2)}")
        return True
        
    except Exception as e:
        print(f"Error creating index: {str(e)}", file=sys.stderr)
        return False


def verify_index_configuration(client: OpenSearch, index_name: str = "knowledge-base") -> bool:
    """
    Verify that the index was created with correct configuration
    
    Args:
        client: OpenSearch client
        index_name: Name of the index to verify
        
    Returns:
        True if configuration is correct, False otherwise
    """
    try:
        # Get index mapping
        mapping = client.indices.get_mapping(index=index_name)
        
        # Verify knn_vector field exists with correct dimension
        properties = mapping[index_name]['mappings']['properties']
        
        if 'embedding' not in properties:
            print("Error: 'embedding' field not found in index mapping", file=sys.stderr)
            return False
        
        embedding_config = properties['embedding']
        
        if embedding_config.get('type') != 'knn_vector':
            print("Error: 'embedding' field is not of type 'knn_vector'", file=sys.stderr)
            return False
        
        if embedding_config.get('dimension') != 1536:
            print(f"Error: 'embedding' dimension is {embedding_config.get('dimension')}, expected 1536", file=sys.stderr)
            return False
        
        print(f"Index '{index_name}' configuration verified successfully")
        print(f"Mapping: {json.dumps(mapping, indent=2)}")
        return True
        
    except Exception as e:
        print(f"Error verifying index: {str(e)}", file=sys.stderr)
        return False


def main():
    """Main function to configure OpenSearch index"""
    parser = argparse.ArgumentParser(
        description="Configure OpenSearch index for AI Builder Copilot knowledge base"
    )
    parser.add_argument(
        "--endpoint",
        required=True,
        help="OpenSearch domain endpoint (without https://)"
    )
    parser.add_argument(
        "--region",
        required=True,
        help="AWS region"
    )
    parser.add_argument(
        "--index-name",
        default="knowledge-base",
        help="Name of the index to create (default: knowledge-base)"
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify existing index configuration"
    )
    
    args = parser.parse_args()
    
    # Create OpenSearch client
    print(f"Connecting to OpenSearch domain: {args.endpoint}")
    client = get_opensearch_client(args.endpoint, args.region)
    
    # Test connection
    try:
        info = client.info()
        print(f"Connected to OpenSearch version: {info['version']['number']}")
    except Exception as e:
        print(f"Error connecting to OpenSearch: {str(e)}", file=sys.stderr)
        sys.exit(1)
    
    # Create or verify index
    if args.verify_only:
        success = verify_index_configuration(client, args.index_name)
    else:
        success = create_knowledge_base_index(client, args.index_name)
        if success:
            success = verify_index_configuration(client, args.index_name)
    
    if success:
        print("\n✓ OpenSearch index configuration completed successfully")
        sys.exit(0)
    else:
        print("\n✗ OpenSearch index configuration failed", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
