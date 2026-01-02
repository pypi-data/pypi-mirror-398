import asyncio
import unittest
import os
from unittest.mock import AsyncMock, MagicMock, patch

# Test imports
from src.dhisana.utils.mailreach_tools import (
    get_mailreach_api_key,
    get_mailreach_headers,
    ping_mailreach
)
from src.dhisana.utils.test_connect import test_mailreach


class TestMailReachTools(unittest.TestCase):
    """Test suite for MailReach integration tools."""
    
    def test_get_mailreach_api_key_from_config(self):
        """Test retrieving API key from tool configuration."""
        tool_config = [
            {
                'name': 'mailreach',
                'configuration': [
                    {'name': 'apiKey', 'value': 'test_api_key_123'}
                ]
            }
        ]
        api_key = get_mailreach_api_key(tool_config)
        self.assertEqual(api_key, 'test_api_key_123')
    
    def test_get_mailreach_api_key_from_env(self):
        """Test retrieving API key from environment variable."""
        with patch.dict(os.environ, {'MAILREACH_API_KEY': 'env_api_key_456'}):
            api_key = get_mailreach_api_key()
            self.assertEqual(api_key, 'env_api_key_456')
    
    def test_get_mailreach_api_key_missing(self):
        """Test that missing API key raises ValueError."""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError) as context:
                get_mailreach_api_key()
            self.assertIn('not configured', str(context.exception))
    
    def test_get_mailreach_headers(self):
        """Test that headers are properly formatted."""
        tool_config = [
            {
                'name': 'mailreach',
                'configuration': [
                    {'name': 'apiKey', 'value': 'test_key'}
                ]
            }
        ]
        headers = get_mailreach_headers(tool_config)
        self.assertEqual(headers['x-api-key'], 'test_key')
        self.assertEqual(headers['Content-Type'], 'application/json')
    
    def test_ping_mailreach_success(self):
        """Test successful ping to MailReach API."""
        async def runner():
            tool_config = [
                {
                    'name': 'mailreach',
                    'configuration': [
                        {'name': 'apiKey', 'value': 'test_api_key'}
                    ]
                }
            ]
            
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={'message': 'pong', 'status': 'ok'})
            
            mock_get = AsyncMock()
            mock_get.__aenter__.return_value = mock_response
            
            with patch('aiohttp.ClientSession') as mock_session:
                mock_session.return_value.__aenter__.return_value.get = MagicMock(return_value=mock_get)
                
                result = await ping_mailreach(tool_config)
                
                self.assertIsInstance(result, dict)
                self.assertEqual(result.get('message'), 'pong')
        
        asyncio.run(runner())
    
    def test_ping_mailreach_rate_limit(self):
        """Test rate limit handling in ping."""
        async def runner():
            tool_config = [
                {
                    'name': 'mailreach',
                    'configuration': [
                        {'name': 'apiKey', 'value': 'test_api_key'}
                    ]
                }
            ]
            
            mock_response = AsyncMock()
            mock_response.status = 429
            mock_response.text = AsyncMock(return_value='Rate limit exceeded')
            mock_response.request_info = MagicMock()
            mock_response.history = []
            mock_response.headers = {}
            
            mock_get = AsyncMock()
            mock_get.__aenter__.return_value = mock_response
            
            with patch('aiohttp.ClientSession') as mock_session:
                mock_session.return_value.__aenter__.return_value.get = MagicMock(return_value=mock_get)
                
                with self.assertRaises(Exception):
                    await ping_mailreach(tool_config)
        
        asyncio.run(runner())


class TestMailReachConnectivity(unittest.TestCase):
    """Test suite for MailReach connectivity check."""
    
    def test_mailreach_connection_success(self):
        """Test successful MailReach connection."""
        async def runner():
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={'message': 'pong'})
            
            mock_get = AsyncMock()
            mock_get.__aenter__.return_value = mock_response
            
            with patch('aiohttp.ClientSession') as mock_session:
                mock_session.return_value.__aenter__.return_value.get = MagicMock(return_value=mock_get)
                
                result = await test_mailreach('test_api_key')
                
                self.assertTrue(result['success'])
                self.assertEqual(result['status_code'], 200)
                self.assertIsNone(result['error_message'])
        
        asyncio.run(runner())
    
    def test_mailreach_connection_invalid_key(self):
        """Test MailReach connection with invalid API key."""
        async def runner():
            mock_response = AsyncMock()
            mock_response.status = 401
            mock_response.json = AsyncMock(return_value={'error': 'Invalid API key'})
            
            mock_get = AsyncMock()
            mock_get.__aenter__.return_value = mock_response
            
            with patch('aiohttp.ClientSession') as mock_session:
                mock_session.return_value.__aenter__.return_value.get = MagicMock(return_value=mock_get)
                
                result = await test_mailreach('invalid_key')
                
                self.assertFalse(result['success'])
                self.assertEqual(result['status_code'], 401)
                self.assertIsNotNone(result['error_message'])
        
        asyncio.run(runner())
    
    def test_mailreach_connection_timeout(self):
        """Test MailReach connection timeout."""
        async def runner():
            with patch('aiohttp.ClientSession') as mock_session:
                mock_session.return_value.__aenter__.return_value.get.side_effect = asyncio.TimeoutError()
                
                result = await test_mailreach('test_api_key')
                
                self.assertFalse(result['success'])
                self.assertEqual(result['status_code'], 0)
                self.assertIsNotNone(result['error_message'])
        
        asyncio.run(runner())


if __name__ == '__main__':
    unittest.main()
