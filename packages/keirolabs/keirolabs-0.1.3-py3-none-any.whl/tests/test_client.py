"""
Unit tests for KEIRO SDK
"""
import pytest
from unittest.mock import Mock, patch
from keiro import Keiro
from keiro.exceptions import (
    KeiroAuthError,
    KeiroRateLimitError,
    KeiroValidationError,
    KeiroConnectionError,
)


class TestKeiroClient:
    """Test suite for Keiro client"""
    
    def test_initialization(self):
        """Test client initialization"""
        client = Keiro(api_key="test-key")
        assert client.api_key == "test-key"
        assert client.base_url == "http://localhost:8000/api"
    
    def test_initialization_with_custom_url(self):
        """Test client initialization with custom base URL"""
        client = Keiro(
            api_key="test-key",
            base_url="https://api.example.com/api"
        )
        assert client.base_url == "https://api.example.com/api"
    
    def test_initialization_without_api_key(self):
        """Test that initialization fails without API key"""
        with pytest.raises(KeiroValidationError):
            Keiro(api_key="")
    
    def test_set_base_url(self):
        """Test setting base URL"""
        client = Keiro(api_key="test-key")
        client.set_base_url("https://new-url.com/api/")
        assert client.base_url == "https://new-url.com/api"
    
    @patch('requests.Session.post')
    def test_search_success(self, mock_post):
        """Test successful search"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {'results': []},
            'creditsRemaining': 99
        }
        mock_post.return_value = mock_response
        
        client = Keiro(api_key="test-key")
        result = client.search("test query")
        
        assert result['creditsRemaining'] == 99
        mock_post.assert_called_once()
    
    @patch('requests.Session.post')
    def test_search_invalid_api_key(self, mock_post):
        """Test search with invalid API key"""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 401
        mock_post.return_value = mock_response
        
        client = Keiro(api_key="invalid-key")
        
        with pytest.raises(KeiroAuthError):
            client.search("test query")
    
    @patch('requests.Session.post')
    def test_search_out_of_credits(self, mock_post):
        """Test search when out of credits"""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 402
        mock_post.return_value = mock_response
        
        client = Keiro(api_key="test-key")
        
        with pytest.raises(KeiroRateLimitError):
            client.search("test query")
    
    def test_search_without_query(self):
        """Test search with empty query"""
        client = Keiro(api_key="test-key")
        
        with pytest.raises(KeiroValidationError):
            client.search("")
    
    @patch('requests.Session.post')
    def test_answer_success(self, mock_post):
        """Test successful answer generation"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {'answer': 'Test answer'},
            'creditsRemaining': 95
        }
        mock_post.return_value = mock_response
        
        client = Keiro(api_key="test-key")
        result = client.answer("test question")
        
        assert result['creditsRemaining'] == 95
        assert result['data']['answer'] == 'Test answer'
    
    @patch('requests.Session.get')
    def test_health_check(self, mock_get):
        """Test health check"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {'status': 'healthy'}
        mock_get.return_value = mock_response
        
        client = Keiro(api_key="test-key")
        health = client.health_check()
        
        assert health['status'] == 'healthy'
    
    def test_context_manager(self):
        """Test context manager usage"""
        with Keiro(api_key="test-key") as client:
            assert client.api_key == "test-key"
    
    @patch('requests.Session.post')
    def test_web_crawler(self, mock_post):
        """Test web crawler"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': {'content': 'test'}}
        mock_post.return_value = mock_response
        
        client = Keiro(api_key="test-key")
        result = client.web_crawler("https://example.com")
        
        assert 'data' in result
    
    def test_web_crawler_without_url(self):
        """Test web crawler with empty URL"""
        client = Keiro(api_key="test-key")
        
        with pytest.raises(KeiroValidationError):
            client.web_crawler("")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
