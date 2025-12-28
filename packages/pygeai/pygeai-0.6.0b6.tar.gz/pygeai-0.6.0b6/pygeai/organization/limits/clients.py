from json import JSONDecodeError

from pygeai import logger
from pygeai.core.base.clients import BaseClient
from pygeai.core.common.exceptions import InvalidAPIResponseException
from pygeai.organization.limits.endpoints import SET_ORGANIZATION_USAGE_LIMIT_V2, GET_ORGANIZATION_LATEST_USAGE_LIMIT_V2, \
    GET_ALL_ORGANIZATION_USAGE_LIMITS_V2, DELETE_ORGANIZATION_USAGE_LIMIT_V2, SET_ORGANIZATION_HARD_LIMIT_V2, \
    SET_ORGANIZATION_SOFT_LIMIT_V2, SET_ORGANIZATION_RENEWAL_STATUS_V2, SET_PROJECT_USAGE_LIMIT_V2, \
    GET_ALL_PROJECT_USAGE_LIMIT_V2, GET_LATEST_PROJECT_USAGE_LIMIT_V2, GET_PROJECT_ACTIVE_USAGE_LIMIT_V2, \
    DELETE_PROJECT_USAGE_LIMIT_V2, SET_PROJECT_HARD_LIMIT_V2, SET_PROJECT_SOFT_LIMIT_V2, \
    SET_PROJECT_RENEWAL_STATUS_V2


class UsageLimitClient(BaseClient):

    def set_organization_usage_limit(self, organization: str, usage_limit: dict) -> dict:
        """
        Defines a new usage limit for an organization.

        :param organization: str - The unique identifier of the organization. (Required)
        :param usage_limit: dict - A dictionary containing the usage limit configuration. Example structure:
            {
                "subscriptionType": "Freemium" | "Daily" | "Weekly" | "Monthly",
                "usageUnit": "Requests" | "Cost",
                "softLimit": number,
                "hardLimit": number,  # Must be greater than or equal to softLimit
                "renewalStatus": "Renewable" | "NonRenewable"
            } (Required)
        :return: dict - The API response as a JSON object containing details about the created usage limit.
        """
        endpoint = SET_ORGANIZATION_USAGE_LIMIT_V2.format(organization=organization)
        response = self.api_service.post(
            endpoint=endpoint,
            data=usage_limit
        )
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to set usage limit for organization '{organization}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to set usage limit for organization '{organization}': {response.text}")

    def get_organization_latest_usage_limit(self, organization: str) -> dict:
        """
        Retrieves the latest usage limit defined for a given organization.

        :param organization: str - The unique identifier of the organization. (Required)
        :return: dict - The API response as a JSON object containing details of the latest usage limit.
        """
        endpoint = GET_ORGANIZATION_LATEST_USAGE_LIMIT_V2.format(organization=organization)
        response = self.api_service.get(endpoint=endpoint)
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to get latest usage limit for organization '{organization}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to get latest usage limit for organization '{organization}': {response.text}")

    def get_all_usage_limits_from_organization(self, organization: str) -> dict:
        """
        Retrieves all usage limits defined for a given organization.

        :param organization: str - The unique identifier of the organization. (Required)
        :return: dict - The API response as a JSON object containing a list of all usage limits.
        """
        endpoint = GET_ALL_ORGANIZATION_USAGE_LIMITS_V2.format(organization=organization)
        response = self.api_service.get(endpoint=endpoint)
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to get all usage limits for organization '{organization}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to get all usage limits for organization '{organization}': {response.text}")

    def delete_usage_limit_from_organization(self, organization: str, limit_id: str) -> dict:
        """
        Deletes a specific usage limit from an organization.

        :param organization: str - The unique identifier of the organization. (Required)
        :param limit_id: str - The unique identifier of the usage limit to be deleted. (Required)
        :return: dict - The API response as a JSON object indicating the result of the delete operation.
        """
        endpoint = DELETE_ORGANIZATION_USAGE_LIMIT_V2.format(organization=organization, id=limit_id)
        response = self.api_service.delete(endpoint=endpoint)
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to delete usage limit with ID '{limit_id}' from organization '{organization}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to delete usage limit with ID '{limit_id}' from organization '{organization}': {response.text}")

    def set_organization_hard_limit(self, organization: str, limit_id: str, hard_limit: float) -> dict:
        """
        Updates the hard limit for a specific usage limit in an organization.

        :param organization: str - The unique identifier of the organization. (Required)
        :param limit_id: str - The unique identifier of the usage limit to be updated. (Required)
        :param hard_limit: float - The new hard limit value. Must be greater than or equal to the soft limit. (Required)
        :return: dict - The API response as a JSON object confirming the update.
        """
        endpoint = SET_ORGANIZATION_HARD_LIMIT_V2.format(organization=organization, id=limit_id)
        response = self.api_service.put(
            endpoint=endpoint,
            data={
                "hardLimit": hard_limit
            }
        )
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to set hard limit for usage limit ID '{limit_id}' in organization '{organization}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to set hard limit for usage limit ID '{limit_id}' in organization '{organization}': {response.text}")

    def set_organization_soft_limit(self, organization: str, limit_id: str, soft_limit: float) -> dict:
        """
        Updates the soft limit for a specific usage limit in an organization.

        :param organization: str - The unique identifier of the organization. (Required)
        :param limit_id: str - The unique identifier of the usage limit to be updated. (Required)
        :param soft_limit: float - The new soft limit value. Must be less than or equal to the hard limit. (Required)
        :return: dict - The API response as a JSON object confirming the update.
        """
        endpoint = SET_ORGANIZATION_SOFT_LIMIT_V2.format(organization=organization, id=limit_id)
        response = self.api_service.put(
            endpoint=endpoint,
            data={
                "softLimit": soft_limit
            }
        )
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to set soft limit for usage limit ID '{limit_id}' in organization '{organization}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to set soft limit for usage limit ID '{limit_id}' in organization '{organization}': {response.text}")

    def set_organization_renewal_status(self, organization: str, limit_id: str, renewal_status: str) -> dict:
        """
        Updates the renewal status for a specific usage limit in an organization.

        :param organization: str - The unique identifier of the organization. (Required)
        :param limit_id: str - The unique identifier of the usage limit to be updated. (Required)
        :param renewal_status: str - The new renewal status. Must be either "Renewable" or "NonRenewable". (Required)
        :return: dict - The API response as a JSON object confirming the update.
        """
        endpoint = SET_ORGANIZATION_RENEWAL_STATUS_V2.format(organization=organization, id=limit_id)
        response = self.api_service.put(
            endpoint=endpoint,
            data={
                "renewalStatus": renewal_status
            }
        )
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to set renewal status for usage limit ID '{limit_id}' in organization '{organization}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to set renewal status for usage limit ID '{limit_id}' in organization '{organization}': {response.text}")

    def set_project_usage_limit(self, organization: str, project: str, usage_limit: dict) -> dict:
        """
        Defines a new usage limit for a specific project within an organization.

        :param organization: str - The unique identifier of the organization. (Required)
        :param project: str - The unique identifier of the project. (Required)
        :param usage_limit: dict - A dictionary containing usage limit details. Example structure:
            {
                "subscriptionType": "Freemium" | "Daily" | "Weekly" | "Monthly",
                "usageUnit": "Requests" | "Cost",
                "softLimit": float,
                "hardLimit": float,
                "renewalStatus": "Renewable" | "NonRenewable"
            } (Required)
        :return: dict - The API response as a JSON object containing details about the created project usage limit.
        """
        endpoint = SET_PROJECT_USAGE_LIMIT_V2.format(organization=organization, project=project)
        response = self.api_service.post(
            endpoint=endpoint,
            data=usage_limit
        )
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to set usage limit for project '{project}' in organization '{organization}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to set usage limit for project '{project}' in organization '{organization}': {response.text}")

    def get_all_usage_limits_from_project(self, organization: str, project: str) -> dict:
        """
        Retrieves all usage limits associated with a specific project within an organization.

        :param organization: str - The unique identifier of the organization. (Required)
        :param project: str - The unique identifier of the project. (Required)
        :return: dict - A JSON object containing details of all usage limits set for the specified project.
        """
        endpoint = GET_ALL_PROJECT_USAGE_LIMIT_V2.format(organization=organization, project=project)
        response = self.api_service.get(endpoint=endpoint)
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to get all usage limits for project '{project}' in organization '{organization}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to get all usage limits for project '{project}' in organization '{organization}': {response.text}")

    def get_latest_usage_limit_from_project(self, organization: str, project: str) -> dict:
        """
        Retrieves the most recent usage limit configured for a specific project within an organization.

        :param organization: str - The unique identifier of the organization. (Required)
        :param project: str - The unique identifier of the project. (Required)
        :return: dict - A JSON object containing details of the latest usage limit for the specified project.
        """
        endpoint = GET_LATEST_PROJECT_USAGE_LIMIT_V2.format(organization=organization, project=project)
        response = self.api_service.get(endpoint=endpoint)
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to get latest usage limit for project '{project}' in organization '{organization}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to get latest usage limit for project '{project}' in organization '{organization}': {response.text}")

    def get_active_usage_limit_from_project(self, organization: str, project: str) -> dict:
        """
        Retrieves the currently active usage limit for a specific project within an organization.

        :param organization: str - The unique identifier of the organization. (Required)
        :param project: str - The unique identifier of the project. (Required)
        :return: dict - A JSON object containing details of the active usage limit for the specified project.
        """
        endpoint = GET_PROJECT_ACTIVE_USAGE_LIMIT_V2.format(organization=organization, project=project)
        response = self.api_service.get(endpoint=endpoint)
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to get active usage limit for project '{project}' in organization '{organization}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to get active usage limit for project '{project}' in organization '{organization}': {response.text}")

    def delete_usage_limit_from_project(self, organization: str, project: str, limit_id: str) -> dict:
        """
        Deletes a specific usage limit for a given project within an organization.

        :param organization: str - The unique identifier of the organization. (Required)
        :param project: str - The unique identifier of the project. (Required)
        :param limit_id: str - The unique identifier of the usage limit to be deleted. (Required)
        :return: dict - A JSON object containing the response of the delete operation.
        """
        endpoint = DELETE_PROJECT_USAGE_LIMIT_V2.format(organization=organization, project=project, id=limit_id)
        response = self.api_service.delete(endpoint=endpoint)
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to delete usage limit with ID '{limit_id}' for project '{project}' in organization '{organization}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to delete usage limit with ID '{limit_id}' for project '{project}' in organization '{organization}': {response.text}")

    def set_hard_limit_for_active_usage_limit_from_project(
            self,
            organization: str,
            project: str,
            limit_id: str,
            hard_limit: float
    ) -> dict:
        """
        Sets the hard limit for an active usage limit of a project within an organization.

        :param organization: str - The unique identifier of the organization. (Required)
        :param project: str - The unique identifier of the project. (Required)
        :param limit_id: str - The unique identifier of the usage limit. (Required)
        :param hard_limit: float - The new hard limit value to be set. (Required)
        :return: dict - A JSON object containing the response of the update operation.
        """
        endpoint = SET_PROJECT_HARD_LIMIT_V2.format(organization=organization, project=project, id=limit_id)
        response = self.api_service.put(
            endpoint=endpoint,
            data={
                "hardLimit": hard_limit
            }
        )
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to set hard limit for usage limit ID '{limit_id}' for project '{project}' in organization '{organization}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to set hard limit for usage limit ID '{limit_id}' for project '{project}' in organization '{organization}': {response.text}")

    def set_soft_limit_for_active_usage_limit_from_project(
            self,
            organization: str,
            project: str,
            limit_id: str,
            soft_limit: float
    ) -> dict:
        """
        Sets the soft limit for an active usage limit of a project within an organization.

        :param organization: str - The unique identifier of the organization. (Required)
        :param project: str - The unique identifier of the project. (Required)
        :param limit_id: str - The unique identifier of the usage limit. (Required)
        :param soft_limit: float - The new soft limit value to be set. (Required)
        :return: dict - A JSON object containing the response of the update operation.
        """
        endpoint = SET_PROJECT_SOFT_LIMIT_V2.format(organization=organization, project=project, id=limit_id)
        response = self.api_service.put(
            endpoint=endpoint,
            data={
                "softLimit": soft_limit
            }
        )
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to set soft limit for usage limit ID '{limit_id}' for project '{project}' in organization '{organization}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to set soft limit for usage limit ID '{limit_id}' for project '{project}' in organization '{organization}': {response.text}")

    def set_project_renewal_status(self, organization: str, project: str, limit_id: str, renewal_status: str) -> dict:
        """
        Updates the renewal status of a project's usage limit within an organization.

        :param organization: str - The unique identifier of the organization. (Required)
        :param project: str - The unique identifier of the project. (Required)
        :param limit_id: str - The unique identifier of the usage limit. (Required)
        :param renewal_status: str - The new renewal status to be set. Options: "Renewable", "NonRenewable". (Required)
        :return: dict - A JSON object containing the response of the update operation.
        """
        endpoint = SET_PROJECT_RENEWAL_STATUS_V2.format(organization=organization, project=project, id=limit_id)
        response = self.api_service.put(
            endpoint=endpoint,
            data={
                "renewalStatus": renewal_status
            }
        )
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to set renewal status for usage limit ID '{limit_id}' for project '{project}' in organization '{organization}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to set renewal status for usage limit ID '{limit_id}' for project '{project}' in organization '{organization}': {response.text}")
