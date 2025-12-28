import unittest
from unittest.mock import Mock, patch, MagicMock
import uuid
import requests
from pygeai.proxy.clients import (
    ProxyClient, ToolProxyData, ToolProxyJob, 
    ToolProxyJobResult
)
from pygeai.proxy.tool import ProxiedTool


class TestToolProxyData(unittest.TestCase):
    """
    python -m unittest pygeai.tests.proxy.test_clients.TestToolProxyData
    """

    def setUp(self):
        """Set up test fixtures."""
        self.test_uuid = uuid.uuid4()
        self.test_affinity = uuid.uuid4()
        self.tool = ProxiedTool(
            server_name="test_server",
            name="test_tool",
            description="Test tool",
            public_prefix="public.prefix",
            input_schema={"type": "object"}
        )

    def test_initialization_with_defaults(self):
        """Test initialization with default values."""
        data = ToolProxyData()
        self.assertIsNone(data.id)
        self.assertIsNone(data.name)
        self.assertIsNone(data.description)
        self.assertIsNone(data.affinity)
        self.assertIsNone(data.tools)

    def test_initialization_with_values(self):
        """Test initialization with provided values."""
        data = ToolProxyData(
            id=self.test_uuid,
            name="Test Proxy",
            description="Test Description",
            affinity=self.test_affinity,
            tools=[self.tool]
        )
        self.assertEqual(data.id, self.test_uuid)
        self.assertEqual(data.name, "Test Proxy")
        self.assertEqual(data.description, "Test Description")
        self.assertEqual(data.affinity, self.test_affinity)
        self.assertEqual(data.tools, [self.tool])

    def test_to_dict_with_all_values(self):
        """Test converting to dictionary with all values."""
        data = ToolProxyData(
            id=self.test_uuid,
            name="Test Proxy",
            description="Test Description",
            affinity=self.test_affinity,
            tools=[self.tool]
        )
        result = data.to_dict()
        
        expected = {
            "id": str(self.test_uuid),
            "name": "Test Proxy",
            "description": "Test Description",
            "affinity": str(self.test_affinity),
            "tools": [
                {
                    "name": self.tool.get_full_name(),
                    "publicName": self.tool.get_public_name(),
                    "server": self.tool.server_name,
                    "description": self.tool.description,
                    "inputSchema": self.tool.format_for_llm()
                }
            ]
        }
        self.assertEqual(result, expected)

    def test_to_dict_with_none_values(self):
        """Test converting to dictionary with None values."""
        data = ToolProxyData()
        result = data.to_dict()
        
        expected = {
            "id": None,
            "name": None,
            "description": None,
            "affinity": str(uuid.UUID(int=0)),
            "tools": []
        }
        self.assertEqual(result, expected)

    def test_to_dict_with_private_tool(self):
        """Test converting to dictionary with private tool."""
        private_tool = ProxiedTool(
            server_name="server",
            name="tool",
            description="desc",
            public_prefix=None,
            input_schema={}
        )
        data = ToolProxyData(tools=[private_tool])
        result = data.to_dict()
        
        tool_dict = result["tools"][0]
        self.assertNotIn("publicName", tool_dict)


class TestToolProxyJob(unittest.TestCase):
    """
    python -m unittest pygeai.tests.proxy.test_clients.TestToolProxyJob
    """

    def setUp(self):
        """Set up test fixtures."""
        self.test_uuid = uuid.uuid4()
        self.proxy_uuid = uuid.uuid4()

    def test_initialization(self):
        """Test job initialization."""
        job = ToolProxyJob(
            id=self.test_uuid,
            proxy_id=self.proxy_uuid,
            proxy_status="active",
            job_status="pending",
            input="test input",
            output="test output",
            server="test_server"
        )
        self.assertEqual(job.id, self.test_uuid)
        self.assertEqual(job.proxy_id, self.proxy_uuid)
        self.assertEqual(job.proxy_status, "active")
        self.assertEqual(job.job_status, "pending")
        self.assertEqual(job.input, "test input")
        self.assertEqual(job.output, "test output")
        self.assertEqual(job.server, "test_server")

    def test_from_dict(self):
        """Test creating job from dictionary."""
        data = {
            "id": str(self.test_uuid),
            "proxyId": str(self.proxy_uuid),
            "proxyStatus": "active",
            "jobStatus": "pending",
            "input": "test input",
            "output": "test output",
            "server": "test_server"
        }
        job = ToolProxyJob.from_dict(data)
        
        self.assertEqual(job.id, self.test_uuid)
        self.assertEqual(job.proxy_id, self.proxy_uuid)
        self.assertEqual(job.proxy_status, "active")
        self.assertEqual(job.job_status, "pending")
        self.assertEqual(job.input, "test input")
        self.assertEqual(job.output, "test output")
        self.assertEqual(job.server, "test_server")

    def test_from_dict_with_optional_fields(self):
        """Test creating job from dictionary with optional fields."""
        data = {
            "id": str(self.test_uuid),
            "proxyId": str(self.proxy_uuid),
            "proxyStatus": "active",
            "jobStatus": "pending"
        }
        job = ToolProxyJob.from_dict(data)
        
        self.assertEqual(job.id, self.test_uuid)
        self.assertEqual(job.proxy_id, self.proxy_uuid)
        self.assertEqual(job.proxy_status, "active")
        self.assertEqual(job.job_status, "pending")
        self.assertIsNone(job.input)
        self.assertIsNone(job.output)
        self.assertIsNone(job.server)


class TestToolProxyJobResult(unittest.TestCase):
    """
    python -m unittest pygeai.tests.proxy.test_clients.TestToolProxyJobResult
    """

    def setUp(self):
        """Set up test fixtures."""
        self.test_uuid = uuid.uuid4()
        self.proxy_uuid = uuid.uuid4()
        self.job = ToolProxyJob(
            id=self.test_uuid,
            proxy_id=self.proxy_uuid,
            proxy_status="active",
            job_status="completed",
            input="test input",
            output="test output",
            server="test_server"
        )

    def test_initialization(self):
        """Test result initialization."""
        result = ToolProxyJobResult(success=True, job=self.job)
        self.assertTrue(result.success)
        self.assertEqual(result.job, self.job)

    def test_to_dict(self):
        """Test converting result to dictionary."""
        result = ToolProxyJobResult(success=True, job=self.job)
        result_dict = result.to_dict()
        
        expected = {
            "success": True,
            "job": {
                "id": str(self.test_uuid),
                "jobStatus": "completed",
                "output": "test output"
            }
        }
        self.assertEqual(result_dict, expected)


class TestProxyClient(unittest.TestCase):
    """
    python -m unittest pygeai.tests.proxy.test_clients.TestProxyClient
    """

    def setUp(self):
        """Set up test fixtures."""
        self.api_key = "test_api_key"
        self.base_url = "https://api.example.com"
        self.proxy_id = uuid.uuid4()
        self.client = ProxyClient(self.api_key, self.base_url, self.proxy_id)

    def test_initialization(self):
        """Test client initialization."""
        self.assertEqual(self.client.proxy_id, self.proxy_id)
        self.assertEqual(self.client.base_url, "https://api.example.com/v2/tool-proxy")
        self.assertEqual(self.client.session.headers["Authorization"], f"Bearer {self.api_key}")
        self.assertEqual(self.client.session.timeout, (5, 30))

    def test_initialization_with_trailing_slash(self):
        """Test client initialization with trailing slash in base URL."""
        client = ProxyClient(self.api_key, "https://api.example.com/", self.proxy_id)
        self.assertEqual(client.base_url, "https://api.example.com/v2/tool-proxy")

    @patch('requests.Session')
    def test_make_request_success(self, mock_session):
        """Test successful request."""
        mock_response = Mock()
        mock_response.json.return_value = {"status": "success"}
        mock_response.raise_for_status.return_value = None
        mock_session.return_value.request.return_value = mock_response
        
        client = ProxyClient(self.api_key, self.base_url, self.proxy_id)
        result = client._make_request("GET", "/test")
        
        self.assertEqual(result, {"status": "success"})

    @patch('requests.Session')
    def test_make_request_timeout(self, mock_session):
        """Test request timeout."""
        mock_session.return_value.request.side_effect = requests.exceptions.Timeout()
        
        client = ProxyClient(self.api_key, self.base_url, self.proxy_id)
        
        with self.assertRaises(TimeoutError):
            client._make_request("GET", "/test")

    @patch('requests.Session')
    def test_make_request_http_error(self, mock_session):
        """Test HTTP error."""
        mock_session.return_value.request.side_effect = requests.exceptions.HTTPError("404 Not Found")
        
        client = ProxyClient(self.api_key, self.base_url, self.proxy_id)
        
        with self.assertRaises(requests.exceptions.HTTPError):
            client._make_request("GET", "/test")

    @patch('requests.Session')
    def test_make_request_connection_error(self, mock_session):
        """Test connection error."""
        mock_session.return_value.request.side_effect = requests.exceptions.ConnectionError()
        
        client = ProxyClient(self.api_key, self.base_url, self.proxy_id)
        
        with self.assertRaises(ConnectionError):
            client._make_request("GET", "/test")

    @patch('requests.Session')
    def test_make_request_ssl_error(self, mock_session):
        """Test SSL error."""
        mock_session.return_value.request.side_effect = requests.exceptions.SSLError()
        
        client = ProxyClient(self.api_key, self.base_url, self.proxy_id)
        
        with self.assertRaises(requests.exceptions.SSLError):
            client._make_request("GET", "/test")

    @patch('requests.Session')
    def test_make_request_proxy_error(self, mock_session):
        """Test proxy error."""
        mock_session.return_value.request.side_effect = requests.exceptions.ProxyError()
        
        client = ProxyClient(self.api_key, self.base_url, self.proxy_id)
        
        with self.assertRaises(requests.exceptions.ProxyError):
            client._make_request("GET", "/test")

    @patch('requests.Session')
    def test_make_request_json_decode_error(self, mock_session):
        """Test JSON decode error."""
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.text = "plain text response"
        mock_response.raise_for_status.return_value = None
        mock_session.return_value.request.return_value = mock_response
        
        client = ProxyClient(self.api_key, self.base_url, self.proxy_id)
        result = client._make_request("GET", "/test")
        
        self.assertEqual(result, "plain text response")

    @patch.object(ProxyClient, '_make_request')
    def test_register(self, mock_make_request):
        """Test proxy registration."""
        mock_make_request.return_value = {"status": "registered"}
        
        tool = ProxiedTool(
            server_name="test_server",
            name="test_tool",
            description="Test tool",
            public_prefix="public.prefix",
            input_schema={"type": "object"}
        )
        
        proxy_data = ToolProxyData(
            name="Test Proxy",
            description="Test Description",
            tools=[tool]
        )
        
        result = self.client.register(proxy_data)
        
        self.assertEqual(result, {"status": "registered"})
        self.assertEqual(proxy_data.id, self.proxy_id)
        mock_make_request.assert_called_once_with(
            'POST', '/register', 
            json={"server": proxy_data.to_dict()}
        )

    @patch.object(ProxyClient, '_make_request')
    def test_dequeue(self, mock_make_request):
        """Test job dequeuing."""
        mock_jobs = [
            {
                "id": str(uuid.uuid4()),
                "proxyId": str(self.proxy_id),
                "proxyStatus": "active",
                "jobStatus": "pending",
                "input": "test input",
                "output": None,
                "server": "test_server"
            }
        ]
        mock_make_request.return_value = mock_jobs
        
        result = self.client.dequeue()
        
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], ToolProxyJob)
        mock_make_request.assert_called_once_with('GET', f'/dequeue/{self.proxy_id}')

    @patch.object(ProxyClient, '_make_request')
    def test_send_result(self, mock_make_request):
        """Test sending job result."""
        job = ToolProxyJob(
            id=uuid.uuid4(),
            proxy_id=self.proxy_id,
            proxy_status="active",
            job_status="completed",
            input="test input",
            output="test output",
            server="test_server"
        )
        result = ToolProxyJobResult(success=True, job=job)
        
        self.client.send_result(result)
        
        mock_make_request.assert_called_once_with(
            'POST', f'/result/{self.proxy_id}',
            json={"jobResult": result.to_dict()}
        )


if __name__ == '__main__':
    unittest.main() 