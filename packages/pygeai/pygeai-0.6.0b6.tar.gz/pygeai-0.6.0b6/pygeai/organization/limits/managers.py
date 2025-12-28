from pygeai import logger
from pygeai.core.base.mappers import ErrorMapper, ModelMapper
from pygeai.core.models import UsageLimit
from pygeai.organization.limits.clients import UsageLimitClient
from pygeai.core.handlers import ErrorHandler
from pygeai.core.common.exceptions import APIError
import logging




class UsageLimitManager:
    """
    Manages usage limits for an organization and its projects.

    This class provides methods to set, retrieve, update, and delete usage limits
    at both the organization and project levels. It interacts with the `UsageLimitClient`
    to perform API operations.

    Attributes:
        __client (UsageLimitClient): Client for making API requests.
        __organization_id (str): The organization ID for which usage limits are managed.
    """

    def __init__(
            self,
            api_key: str = None,
            base_url: str = None,
            alias: str = "default",
            organization_id: str = None
    ):
        self.__client = UsageLimitClient(api_key, base_url, alias)
        self.__organization_id = organization_id

    def set_organization_usage_limit(self, usage_limit: UsageLimit) -> UsageLimit:
        """
        Sets a new usage limit for the organization.

        This method sends a request to the usage limit client to set a new usage limit
        for the specified organization.

        :param usage_limit: UsageLimit object containing the limit details.
        :return: UsageLimit object with the created usage limit details.
        :raises APIError: If the API returns errors.
        """
        response_data = self.__client.set_organization_usage_limit(
            organization=self.__organization_id,
            usage_limit=usage_limit.to_dict()
        )

        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while setting organization usage limit: {error}")
            raise APIError(f"Error received while setting organization usage limit: {error}")

        result = ModelMapper.map_to_usage_limit(response_data)
        return result

    def get_latest_usage_limit_from_organization(self) -> UsageLimit:
        """
        Retrieves the latest usage limit set for the organization.

        This method queries the usage limit client to fetch the latest usage limit
        for the specified organization.

        :return: UsageLimit object containing the latest usage limit details.
        :raises APIError: If the API returns errors.
        """
        response_data = self.__client.get_organization_latest_usage_limit(
            organization=self.__organization_id
        )

        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving latest organization usage limit: {error}")
            raise APIError(f"Error received while retrieving latest organization usage limit: {error}")

        result = ModelMapper.map_to_usage_limit(response_data)
        return result

    def get_all_usage_limits_from_organization(self) -> list[UsageLimit]:
        """
        Retrieves all usage limits associated with the organization.

        This method queries the usage limit client to fetch all usage limits
        for the specified organization.

        :return: list[UsageLimit] - A list of UsageLimit objects containing all usage limits for the organization.
        :raises APIError: If the API returns errors.
        """
        response_data = self.__client.get_all_usage_limits_from_organization(
            organization=self.__organization_id
        )

        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving all organization usage limits: {error}")
            raise APIError(f"Error received while retrieving all organization usage limits: {error}")

        result = ModelMapper.map_to_usage_limit_list(response_data)
        return result

    def update_organization_usage_limit(self, usage_limit: UsageLimit) -> UsageLimit:
        """
        Updates the usage limits for an organization, including hard limit, soft limit, and renewal status.

        This method sends requests to the usage limit client to update specific attributes
        of the usage limit for the specified organization.

        :param usage_limit: UsageLimit object containing the updated limit values.
        :return: UsageLimit object with updated usage limit details.
        :raises APIError: If the API returns errors.
        """
        response_data = {}
        if usage_limit.hard_limit:
            response_data = self.__client.set_organization_hard_limit(
                organization=self.__organization_id,
                limit_id=usage_limit.id,
                hard_limit=usage_limit.hard_limit
            )
        if usage_limit.soft_limit:
            response_data = self.__client.set_organization_soft_limit(
                organization=self.__organization_id,
                limit_id=usage_limit.id,
                soft_limit=usage_limit.soft_limit
            )
        if usage_limit.renewal_status:
            response_data = self.__client.set_organization_renewal_status(
                organization=self.__organization_id,
                limit_id=usage_limit.id,
                renewal_status=usage_limit.renewal_status
            )

        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while updating organization usage limit: {error}")
            raise APIError(f"Error received while updating organization usage limit: {error}")

        result = ModelMapper.map_to_usage_limit(response_data)
        return result

    def delete_usage_limit_from_organization(self, limit_id: str) -> UsageLimit:
        """
        Deletes a usage limit from the organization.

        This method sends a request to the usage limit client to delete a usage limit
        identified by `limit_id` for the specified organization.

        :param limit_id: The ID of the usage limit to be deleted.
        :return: UsageLimit object representing the deleted limit details.
        :raises APIError: If the API returns errors.
        """
        response_data = self.__client.delete_usage_limit_from_organization(
            organization=self.__organization_id,
            limit_id=limit_id,
        )

        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while deleting organization usage limit: {error}")
            raise APIError(f"Error received while deleting organization usage limit: {error}")

        result = ModelMapper.map_to_usage_limit(response_data)
        return result

    def set_project_usage_limit(self, project_id: str, usage_limit: UsageLimit) -> UsageLimit:
        """
        Sets a new usage limit for a specific project within the organization.

        This method sends a request to the usage limit client to set a new usage limit
        for the specified project.

        :param project_id: The unique identifier of the project.
        :param usage_limit: UsageLimit object containing the limit details.
        :return: UsageLimit object with the created project usage limit details.
        :raises APIError: If the API returns errors.
        """
        response_data = self.__client.set_project_usage_limit(
            organization=self.__organization_id,
            project=project_id,
            usage_limit=usage_limit.to_dict()
        )

        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while setting project usage limit: {error}")
            raise APIError(f"Error received while setting project usage limit: {error}")

        result = ModelMapper.map_to_usage_limit(response_data)
        return result

    def get_all_usage_limits_from_project(self, project_id: str) -> UsageLimit:
        """
        Retrieves all usage limits associated with a specific project.

        This method queries the usage limit client to fetch all usage limits
        for the specified project.

        :param project_id: The unique identifier of the project.
        :return: UsageLimit object containing all usage limits for the project.
        :raises APIError: If the API returns errors.
        """
        response_data = self.__client.get_all_usage_limits_from_project(
            organization=self.__organization_id,
            project=project_id,
        )

        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving all project usage limits: {error}")
            raise APIError(f"Error received while retrieving all project usage limits: {error}")

        result = ModelMapper.map_to_usage_limit(response_data)
        return result

    def get_latest_usage_limit_from_project(self, project_id: str) -> UsageLimit:
        """
        Retrieves the latest usage limit set for a specific project.

        This method queries the usage limit client to fetch the latest usage limit
        for the specified project.

        :param project_id: The unique identifier of the project.
        :return: UsageLimit object containing the latest usage limit details.
        :raises APIError: If the API returns errors.
        """
        response_data = self.__client.get_latest_usage_limit_from_project(
            organization=self.__organization_id,
            project=project_id,
        )

        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving latest project usage limit: {error}")
            raise APIError(f"Error received while retrieving latest project usage limit: {error}")

        result = ModelMapper.map_to_usage_limit(response_data)
        return result

    def get_active_usage_limit_from_project(self, project_id: str) -> UsageLimit:
        """
        Retrieves the currently active usage limit for a specific project.

        This method queries the usage limit client to fetch the active usage limit
        for the specified project.

        :param project_id: The unique identifier of the project.
        :return: UsageLimit object containing the active usage limit details.
        :raises APIError: If the API returns errors.
        """
        response_data = self.__client.get_active_usage_limit_from_project(
            organization=self.__organization_id,
            project=project_id,
        )

        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving active project usage limit: {error}")
            raise APIError(f"Error received while retrieving active project usage limit: {error}")

        result = ModelMapper.map_to_usage_limit(response_data)
        return result

    def delete_usage_limit_from_project(self, project_id: str, usage_limit: UsageLimit) -> UsageLimit:
        """
        Deletes a specified usage limit from a project.

        This method sends a request to the usage limit client to delete a usage limit
        identified by `usage_limit.id` for the specified project.

        :param project_id: The unique identifier of the project.
        :param usage_limit: The UsageLimit object representing the limit to be deleted.
        :return: UsageLimit object representing the deleted usage limit details.
        :raises APIError: If the API returns errors.
        """
        response_data = self.__client.delete_usage_limit_from_project(
            organization=self.__organization_id,
            project=project_id,
            limit_id=usage_limit.id
        )

        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while deleting project usage limit: {error}")
            raise APIError(f"Error received while deleting project usage limit: {error}")

        result = ModelMapper.map_to_usage_limit(response_data)
        return result

    def update_project_usage_limit(self, project_id: str, usage_limit: UsageLimit) -> UsageLimit:
        """
        Updates the usage limits for a specific project, including hard limit, soft limit, and renewal status.

        This method sends requests to the usage limit client to update specific attributes
        of the usage limit for the specified project.

        :param project_id: The unique identifier of the project.
        :param usage_limit: UsageLimit object containing the updated limit values.
        :return: UsageLimit object with updated usage limit details.
        :raises APIError: If the API returns errors.
        """
        response_data = {}
        if usage_limit.hard_limit:
            response_data = self.__client.set_hard_limit_for_active_usage_limit_from_project(
                organization=self.__organization_id,
                project=project_id,
                limit_id=usage_limit.id,
                hard_limit=usage_limit.hard_limit
            )
        if usage_limit.soft_limit:
            response_data = self.__client.set_soft_limit_for_active_usage_limit_from_project(
                organization=self.__organization_id,
                project=project_id,
                limit_id=usage_limit.id,
                soft_limit=usage_limit.soft_limit
            )
        if usage_limit.renewal_status:
            response_data = self.__client.set_project_renewal_status(
                organization=self.__organization_id,
                project=project_id,
                limit_id=usage_limit.id,
                renewal_status=usage_limit.renewal_status
            )

        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while updating project usage limit: {error}")
            raise APIError(f"Error received while updating project usage limit: {error}")

        result = ModelMapper.map_to_usage_limit(response_data)
        return result
