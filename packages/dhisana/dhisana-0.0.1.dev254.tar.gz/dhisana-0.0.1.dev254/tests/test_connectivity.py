import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from src.dhisana.utils.test_connect import test_connectivity as run_test_connectivity


class TestConnectivity(unittest.TestCase):
    def test_jinaai_dispatch(self):
        async def runner():
            with patch('src.dhisana.utils.test_connect.test_jinaai', new=AsyncMock(return_value={'success': True, 'status_code': 200, 'error_message': None})):
                tool_config = [
                    {
                        'name': 'jinaai',
                        'configuration': [
                            {'name': 'apiKey', 'value': 'dummy'}
                        ]
                    }
                ]
                result = await run_test_connectivity(tool_config)
                self.assertIn('jinaai', result)
                self.assertTrue(result['jinaai']['success'])
        asyncio.run(runner())

    def test_firecrawl_dispatch(self):
        async def runner():
            with patch('src.dhisana.utils.test_connect.test_firecrawl', new=AsyncMock(return_value={'success': True, 'status_code': 200, 'error_message': None})):
                tool_config = [
                    {
                        'name': 'firecrawl',
                        'configuration': [
                            {'name': 'apiKey', 'value': 'dummy'}
                        ]
                    }
                ]
                result = await run_test_connectivity(tool_config)
                self.assertIn('firecrawl', result)
                self.assertTrue(result['firecrawl']['success'])
        asyncio.run(runner())

    def test_firefliesai_dispatch(self):
        async def runner():
            with patch('src.dhisana.utils.test_connect.test_firefliesai', new=AsyncMock(return_value={'success': True, 'status_code': 200, 'error_message': None})):
                tool_config = [
                    {
                        'name': 'firefliesai',
                        'configuration': [
                            {'name': 'apiKey', 'value': 'dummy'}
                        ]
                    }
                ]
                result = await run_test_connectivity(tool_config)
                self.assertIn('firefliesai', result)
                self.assertTrue(result['firefliesai']['success'])
        asyncio.run(runner())

    def test_theorg_dispatch(self):
        async def runner():
            with patch('src.dhisana.utils.test_connect.test_theorg', new=AsyncMock(return_value={'success': True, 'status_code': 200, 'error_message': None})):
                tool_config = [
                    {
                        'name': 'theorg',
                        'configuration': [
                            {'name': 'apiKey', 'value': 'dummy'}
                        ]
                    }
                ]
                result = await run_test_connectivity(tool_config)
                self.assertIn('theorg', result)
                self.assertTrue(result['theorg']['success'])
        asyncio.run(runner())

    def test_salesforce_dispatch(self):
        async def runner():
            with patch(
                'src.dhisana.utils.test_connect.test_salesforce',
                new=AsyncMock(return_value={'success': True, 'status_code': 200, 'error_message': None})
            ):
                tool_config = [
                    {
                        'name': 'salesforce',
                        'configuration': [
                            {'name': 'username', 'value': 'dummy'},
                            {'name': 'password', 'value': 'dummy'},
                            {'name': 'security_token', 'value': 'dummy'},
                            {'name': 'domain', 'value': 'login'},
                            {'name': 'client_id', 'value': 'dummy'},
                            {'name': 'client_secret', 'value': 'dummy'},
                        ]
                    }
                ]
                result = await run_test_connectivity(tool_config)
                self.assertIn('salesforce', result)
                self.assertTrue(result['salesforce']['success'])
        asyncio.run(runner())

    def test_samgov_dispatch(self):
        async def runner():
            with patch(
                'src.dhisana.utils.test_connect.test_samgov',
                new=AsyncMock(return_value={'success': True, 'status_code': 200, 'error_message': None})
            ):
                tool_config = [
                    {
                        'name': 'samgov',
                        'configuration': [
                            {'name': 'apiKey', 'value': 'dummy'}
                        ]
                    }
                ]
                result = await run_test_connectivity(tool_config)
                self.assertIn('samgov', result)
                self.assertTrue(result['samgov']['success'])
        asyncio.run(runner())


if __name__ == '__main__':
    unittest.main()
