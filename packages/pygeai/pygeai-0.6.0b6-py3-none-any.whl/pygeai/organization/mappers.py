from pygeai.core.base.mappers import ModelMapper
from pygeai.core.models import Assistant, Project
from pygeai.organization.responses import AssistantListResponse, ProjectListResponse, ProjectDataResponse, \
    ProjectTokensResponse, ProjectItemListResponse


class OrganizationResponseMapper:

    @classmethod
    def map_to_assistant_list_response(cls, data: dict) -> AssistantListResponse:
        assistant_list = data.get('assistants')
        if "projectName" in data and assistant_list:
            for assistant in assistant_list:
                assistant.update({
                    'projectId': data.get('projectId'),
                    'projectName': data.get('projectName')
                })

        assistant_list = cls.map_to_assistant_list(data)

        return AssistantListResponse(
            assistants=assistant_list,
        )

    @classmethod
    def map_to_assistant_list(cls, data: dict) -> list[Assistant]:
        assistant_list = list()
        assistants = data.get("assistants")
        if assistants is not None and any(assistants):
            for assistant_data in assistants:
                assistant = ModelMapper.map_to_assistant(assistant_data)
                assistant_list.append(assistant)

        return assistant_list

    @classmethod
    def map_to_project_list_response(cls, data: dict) -> ProjectListResponse:
        project_list = cls.map_to_project_list(data)

        return ProjectListResponse(
            projects=project_list
        )

    @classmethod
    def map_to_project_list(cls, data: dict) -> list[Project]:
        project_list = list()
        projects = data.get("projects")
        if projects is not None and any(projects):
            for project_data in projects:
                project = ModelMapper.map_to_project(project_data)
                project_list.append(project)

        return project_list

    @classmethod
    def map_to_project_data(cls, data: dict) -> ProjectDataResponse:
        project = ModelMapper.map_to_project(data)

        return ProjectDataResponse(
            project=project,
        )

    @classmethod
    def map_to_token_list_response(cls, data: dict) -> ProjectTokensResponse:
        token_list = ModelMapper.map_to_token_list(data)

        return ProjectTokensResponse(
            tokens=token_list
        )

    @classmethod
    def map_to_item_list_response(cls, data: dict) -> ProjectItemListResponse:
        item_list = ModelMapper.map_to_item_list(data)

        return ProjectItemListResponse(
            items=item_list
        )

