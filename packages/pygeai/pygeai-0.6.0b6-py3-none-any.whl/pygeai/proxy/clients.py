from dataclasses import dataclass
from typing import Optional, Dict, Any, List
import uuid
import requests
from urllib3.exceptions import MaxRetryError
from pygeai.proxy.tool import ProxiedTool


@dataclass
class ToolProxyData:
    """
    Data class representing a tool proxy registration.

    :param id: Optional[uuid.UUID] - Unique identifier for the proxy. Defaults to None.
    :param name: Optional[str] - Name of the proxy. Defaults to None.
    :param description: Optional[str] - Description of the proxy. Defaults to None.
    :param affinity: Optional[uuid.UUID] - Affinity UUID. Defaults to None.
    :param tools: Optional[List[Tool]] - List of tools. Defaults to None.
    """
    id: Optional[uuid.UUID] = None
    name: Optional[str] = None
    description: Optional[str] = None
    affinity: Optional[uuid.UUID] = None
    tools: Optional[List[ProxiedTool]] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the data to a dictionary for API requests.

        :return: Dict[str, Any] - Dictionary containing proxy data
        """
        return {
            "id": str(self.id) if self.id else None,
            "name": self.name,
            "description": self.description,
            "affinity": str(self.affinity) if self.affinity else str(uuid.UUID(int=0)),
            "tools": [
                {
                    "name": tool.get_full_name(),
                    **({"publicName": tool.get_public_name()} if tool.is_public() else {}),
                    "server": tool.server_name,
                    "description": tool.description,
                    "inputSchema": tool.format_for_llm()
                } for tool in self.tools
            ] if self.tools else []
        }

@dataclass
class ToolProxyJob:
    """
    Represents a Tool Proxy Job.

    :param id: uuid.UUID - Unique identifier for the job
    :param proxy_id: uuid.UUID - ID of the proxy handling the job
    :param proxy_status: str - Status of the proxy
    :param job_status: str - Status of the job
    :param input: Optional[str] - Input data for the job. Defaults to None.
    :param output: Optional[str] - Output data from the job. Defaults to None.
    :param server: Optional[str] - Server handling the job. Defaults to None.
    """
    id: uuid.UUID
    proxy_id: uuid.UUID
    proxy_status: str
    job_status: str
    input: Optional[str] = None
    output: Optional[str] = None
    server: Optional[str] = None

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'ToolProxyJob':
        """
        Create a ToolProxyJob from a dictionary.

        :param data: Dict[str, Any] - Dictionary containing job data
        :return: ToolProxyJob - New ToolProxyJob instance
        """
        return ToolProxyJob(
            id=uuid.UUID(data['id']),
            proxy_id=uuid.UUID(data['proxyId']),
            proxy_status=data['proxyStatus'],
            job_status=data['jobStatus'],
            input=data.get('input'),
            output=data.get('output'),
            server=data.get('server')
        )

@dataclass
class ToolProxyJobResult:
    """
    Represents the result of a Tool Proxy Job.

    :param success: bool - Whether the job was successful
    :param job: ToolProxyJob - The job that was executed
    """
    success: bool
    job: ToolProxyJob

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the result to a dictionary for API requests.

        :return: Dict[str, Any] - Dictionary containing job result
        """
        return {
            "success": self.success,
            "job": {
                "id": str(self.job.id),
                "jobStatus": self.job.job_status,
                "output": self.job.output
            }
        }


class ProxyClient:
    """
    Client for interacting with the GEAI API proxy.

    :param base_url: str - Base URL of the GEAI API
    :param api_key: str - API key for authentication
    :param proxy_id: uuid.UUID - ID of the proxy
    """

    def __init__(self, api_key: str, base_url: str, proxy_id: uuid.UUID ):
        """
        Initialize a new proxy client.

        :param base_url: str - Base URL of the GEAI API
        :param api_key: str - API key for authentication
        :param proxy_id: uuid.UUID - ID of the proxy
        """
        self.proxy_id = proxy_id
        self.base_url =  base_url.rstrip('/') + '/v2/tool-proxy'
        self.session = requests.Session()
        self.session.headers.update({'Authorization': f'Bearer {api_key}'})
        # Configurar el timeout
        self.session.timeout = (5, 30)  # (connect timeout, read timeout)

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make a request to the proxy service.
        
        :param method: str - HTTP method (GET, POST, etc.)
        :param endpoint: str - API endpoint
        :param **kwargs: Additional arguments for requests
        :return: Dict[str, Any] - Response data as dictionary
        :raises: RequestException - For any request-related error
        """
        url = self.base_url + endpoint
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            try:
                return response.json()
            except ValueError:
                return response.text
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Request timed out for {url}")
        except requests.exceptions.HTTPError as e:
            raise requests.exceptions.HTTPError(f"HTTP error for {url}: {e}") from e
        except requests.exceptions.SSLError as e:
            raise requests.exceptions.SSLError(f"SSL error for {url}: {e}") from e
        except requests.exceptions.ProxyError as e:
            raise requests.exceptions.ProxyError(f"Proxy error for {url}: {e}") from e
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(f"Failed to connect to {url}") from e
        except MaxRetryError:
            raise
        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(f"Request failed for {url}: {e}") from e
        except ValueError:
            return {"response": response.text}

    def register(self, proxy_data: ToolProxyData) -> Dict[str, Any]:
        """
        Register a new tool proxy.
        
        :param proxy_data: ToolProxyData - Object containing the proxy configuration and metadata
        :return: Dict[str, Any] - Dictionary with the registration response
        :raises: ConnectionError - If connection fails
        :raises: MaxRetryError - If max retries are exceeded
        :raises: requests.exceptions.RequestException - For other request errors
        """
        proxy_data.id = self.proxy_id
        data = {
            "server": proxy_data.to_dict()
        }
        return self._make_request('POST', '/register', json=data)
    
    def dequeue(self) -> List[ToolProxyJob]:
        """
        Dequeue a job from the proxy.

        :return: List[ToolProxyJob] - List of ToolProxyJob instances
        :raises: RequestException - For any request-related error
        """
        endpoint = f'/dequeue/{self.proxy_id}'
        response_data = self._make_request('GET', endpoint)
        return [ToolProxyJob.from_dict(job) for job in response_data]

    
    def send_result(self, result: ToolProxyJobResult):
        """
        Send the result of a tool proxy job.

        :param result: ToolProxyJobResult - Result object containing the job outcome
        :return: None
        :raises: RequestException - For any request-related error
        """
        endpoint = f'/result/{self.proxy_id}'
        data = {
            "jobResult": result.to_dict()
        }
        self._make_request('POST', endpoint, json=data)