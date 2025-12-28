from json import JSONDecodeError
from typing import Optional, List, Dict

from pygeai import logger
from pygeai.core.base.clients import BaseClient
from pygeai.core.common.exceptions import InvalidAPIResponseException
from pygeai.core.plugins.endpoints import LIST_ASSISTANTS_PLUGINS_V1


class PluginClient(BaseClient):
    """
    Client for interacting with plugin endpoints of the API.
    """

    def list_assistants(
        self,
        organization_id: str,
        project_id: str
    ) -> dict:
        params = {
            "organization": organization_id,
            "project": project_id,
        }

        response = self.api_service.get(
            endpoint=LIST_ASSISTANTS_PLUGINS_V1,
            params=params
        )
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to list assistants for organization {organization_id} and project {project_id}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to list assistants for organization {organization_id} and project {project_id}: {response.text}")

