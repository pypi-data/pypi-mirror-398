from pygeai import logger
from pygeai.admin.clients import AdminClient
from pygeai.core.common.exceptions import APIError


def get_project_id():
    response = None
    try:
        response = AdminClient().validate_api_token()
        return response.get("projectId")
    except Exception as e:
        logger.error(f"Error retrieving project_id from GEAI. Response: {response}: {e}")
        raise APIError(f"Error retrieving project_id from GEAI: {e}")