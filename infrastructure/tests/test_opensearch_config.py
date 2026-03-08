"""
Unit tests for OpenSearch index configuration
Tests Requirements 2.2, 2.3
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import json

# Mock opensearchpy before importing the script
sys.modules['opensearchpy'] = MagicMock()

from infrastructure.scripts.configure_opensearch_index import (
    get_opensearch_client,
    create_knowledge_base_index,
    verify_index_configuration
)


class TestOpenSearchConfiguration(unittest.TestCase):
    """Test OpenSearch index configuration"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_client = Mock()
        self.test_endpoint = "search-test-domain.us-east-1.es.amazonaws.com"
        self.test_region = "us-east-1"
        self.test_index_name = "knowledge-base"

    @patch('infrastructure.scripts.configure_opensearch_index.boto3.Session')
    @patch('infrastructure.scripts.configure_opensearch_index.OpenSearch')
    def test_get_opensearch_client(self, mock_opensearch, mock_session):
        """Test OpenSearch client creation with AWS authentication"""
        # Mock credentials
        mock_credentials = Mock()
        mock_session.return_value.get_credentials.return_value = mock_credentials
        
        # Call function
        client = get_opensearch_client(self.test_endpoint, self.test_region)
        
        # Verify OpenSearch client was created with correct parameters
        mock_opensearch.assert_called_once()
        call_kwargs = mock_opensearch.call_args[1]
        
        self.assertEqual(call_kwargs['hosts'][0]['host'], self.test_endpoint)
        self.assertEqual(call_kwargs['hosts'][0]['port'], 443)
        self.assertTrue(call_kwargs['use_ssl'])
        self.assertTrue(call_kwargs['verify_certs'])
        self.assertEqual(call_kwargs['timeout'], 30)

    def test_create_knowledge_base_index_success(self):
        """Test successful index creation"""
        # Mock client responses
        self.mock_client.indices.exists.return_value = False
        self.mock_client.indices.create.return_value = {
            "acknowledged": True,
            "shards_acknowledged": True,
            "index": self.test_index_name
        }
        
        # Call function
        result = create_knowledge_base_index(self.mock_client, self.test_index_name)
        
        # Verify
        self.assertTrue(result)
        self.mock_client.indices.exists.assert_called_once_with(index=self.test_index_name)
        self.mock_client.indices.create.assert_called_once()
        
        # Verify index configuration
        create_call_args = self.mock_client.indices.create.call_args
        index_body = create_call_args[1]['body']
        
        # Verify KNN is enabled
        self.assertTrue(index_body['settings']['index']['knn'])
        
        # Verify embedding field configuration (Requirement 2.2)
        embedding_config = index_body['mappings']['properties']['embedding']
        self.assertEqual(embedding_config['type'], 'knn_vector')
        self.assertEqual(embedding_config['dimension'], 1536)  # Titan Embeddings dimension
        self.assertEqual(embedding_config['method']['name'], 'hnsw')
        self.assertEqual(embedding_config['method']['space_type'], 'cosinesim')

    def test_create_knowledge_base_index_already_exists(self):
        """Test index creation when index already exists"""
        # Mock client responses
        self.mock_client.indices.exists.return_value = True
        
        # Call function
        result = create_knowledge_base_index(self.mock_client, self.test_index_name)
        
        # Verify
        self.assertTrue(result)
        self.mock_client.indices.exists.assert_called_once_with(index=self.test_index_name)
        self.mock_client.indices.create.assert_not_called()

    def test_create_knowledge_base_index_failure(self):
        """Test index creation failure"""
        # Mock client responses
        self.mock_client.indices.exists.return_value = False
        self.mock_client.indices.create.side_effect = Exception("Connection error")
        
        # Call function
        result = create_knowledge_base_index(self.mock_client, self.test_index_name)
        
        # Verify
        self.assertFalse(result)

    def test_verify_index_configuration_success(self):
        """Test successful index verification"""
        # Mock mapping response
        mock_mapping = {
            self.test_index_name: {
                'mappings': {
                    'properties': {
                        'document_id': {'type': 'keyword'},
                        'content': {'type': 'text'},
                        'embedding': {
                            'type': 'knn_vector',
                            'dimension': 1536,
                            'method': {
                                'name': 'hnsw',
                                'space_type': 'cosinesim'
                            }
                        },
                        'metadata': {
                            'properties': {
                                'source': {'type': 'keyword'},
                                'timestamp': {'type': 'date'},
                                'chunk_id': {'type': 'keyword'}
                            }
                        }
                    }
                }
            }
        }
        
        self.mock_client.indices.get_mapping.return_value = mock_mapping
        
        # Call function
        result = verify_index_configuration(self.mock_client, self.test_index_name)
        
        # Verify
        self.assertTrue(result)
        self.mock_client.indices.get_mapping.assert_called_once_with(index=self.test_index_name)

    def test_verify_index_configuration_missing_embedding_field(self):
        """Test verification fails when embedding field is missing"""
        # Mock mapping without embedding field
        mock_mapping = {
            self.test_index_name: {
                'mappings': {
                    'properties': {
                        'document_id': {'type': 'keyword'},
                        'content': {'type': 'text'}
                    }
                }
            }
        }
        
        self.mock_client.indices.get_mapping.return_value = mock_mapping
        
        # Call function
        result = verify_index_configuration(self.mock_client, self.test_index_name)
        
        # Verify
        self.assertFalse(result)

    def test_verify_index_configuration_wrong_embedding_type(self):
        """Test verification fails when embedding field has wrong type"""
        # Mock mapping with wrong type
        mock_mapping = {
            self.test_index_name: {
                'mappings': {
                    'properties': {
                        'embedding': {
                            'type': 'dense_vector',  # Wrong type
                            'dimension': 1536
                        }
                    }
                }
            }
        }
        
        self.mock_client.indices.get_mapping.return_value = mock_mapping
        
        # Call function
        result = verify_index_configuration(self.mock_client, self.test_index_name)
        
        # Verify
        self.assertFalse(result)

    def test_verify_index_configuration_wrong_dimension(self):
        """Test verification fails when embedding dimension is incorrect"""
        # Mock mapping with wrong dimension
        mock_mapping = {
            self.test_index_name: {
                'mappings': {
                    'properties': {
                        'embedding': {
                            'type': 'knn_vector',
                            'dimension': 768  # Wrong dimension
                        }
                    }
                }
            }
        }
        
        self.mock_client.indices.get_mapping.return_value = mock_mapping
        
        # Call function
        result = verify_index_configuration(self.mock_client, self.test_index_name)
        
        # Verify
        self.assertFalse(result)

    def test_index_supports_vector_search(self):
        """Test that index configuration supports vector search (Requirement 2.2)"""
        # Mock client
        self.mock_client.indices.exists.return_value = False
        self.mock_client.indices.create.return_value = {"acknowledged": True}
        
        # Create index
        create_knowledge_base_index(self.mock_client, self.test_index_name)
        
        # Get the index body that was passed to create
        create_call_args = self.mock_client.indices.create.call_args
        index_body = create_call_args[1]['body']
        
        # Verify KNN settings
        self.assertTrue(index_body['settings']['index']['knn'])
        self.assertIn('knn.algo_param.ef_search', index_body['settings']['index'])
        
        # Verify embedding field supports vector search
        embedding = index_body['mappings']['properties']['embedding']
        self.assertEqual(embedding['type'], 'knn_vector')
        self.assertEqual(embedding['method']['name'], 'hnsw')
        self.assertEqual(embedding['method']['space_type'], 'cosinesim')

    def test_index_supports_top_k_retrieval(self):
        """Test that index configuration supports top-k retrieval (Requirement 2.3)"""
        # Mock client
        self.mock_client.indices.exists.return_value = False
        self.mock_client.indices.create.return_value = {"acknowledged": True}
        
        # Create index
        create_knowledge_base_index(self.mock_client, self.test_index_name)
        
        # Get the index body
        create_call_args = self.mock_client.indices.create.call_args
        index_body = create_call_args[1]['body']
        
        # Verify HNSW algorithm parameters support efficient top-k search
        method = index_body['mappings']['properties']['embedding']['method']
        self.assertEqual(method['name'], 'hnsw')
        self.assertIn('ef_construction', method['parameters'])
        self.assertIn('m', method['parameters'])
        
        # HNSW with these parameters efficiently supports top-k retrieval
        self.assertGreater(method['parameters']['ef_construction'], 0)
        self.assertGreater(method['parameters']['m'], 0)

    def test_index_has_required_fields(self):
        """Test that index has all required fields"""
        # Mock client
        self.mock_client.indices.exists.return_value = False
        self.mock_client.indices.create.return_value = {"acknowledged": True}
        
        # Create index
        create_knowledge_base_index(self.mock_client, self.test_index_name)
        
        # Get the index body
        create_call_args = self.mock_client.indices.create.call_args
        index_body = create_call_args[1]['body']
        properties = index_body['mappings']['properties']
        
        # Verify required fields exist
        self.assertIn('document_id', properties)
        self.assertIn('content', properties)
        self.assertIn('embedding', properties)
        self.assertIn('metadata', properties)
        
        # Verify metadata subfields
        metadata_props = properties['metadata']['properties']
        self.assertIn('source', metadata_props)
        self.assertIn('timestamp', metadata_props)
        self.assertIn('chunk_id', metadata_props)

    def test_embedding_dimension_matches_titan(self):
        """Test that embedding dimension matches Titan Embeddings (1536)"""
        # Mock client
        self.mock_client.indices.exists.return_value = False
        self.mock_client.indices.create.return_value = {"acknowledged": True}
        
        # Create index
        create_knowledge_base_index(self.mock_client, self.test_index_name)
        
        # Get the index body
        create_call_args = self.mock_client.indices.create.call_args
        index_body = create_call_args[1]['body']
        
        # Verify dimension is 1536 (Titan Embeddings dimension)
        embedding_dimension = index_body['mappings']['properties']['embedding']['dimension']
        self.assertEqual(embedding_dimension, 1536)


if __name__ == '__main__':
    unittest.main()
