from pydantic.main import BaseModel

from pygeai.core.models import Assistant, Project, ProjectToken, \
    RequestItem


class AssistantListResponse(BaseModel):
    assistants: list[Assistant]


class ProjectListResponse(BaseModel):
    projects: list[Project]


class ProjectDataResponse(BaseModel):
    project: Project


class ProjectTokensResponse(BaseModel):
    tokens: list[ProjectToken]


class ProjectItemListResponse(BaseModel):
    items: list[RequestItem]

    def to_list(self):
        return [item.to_dict() for item in self.items] if self.items else []

    def __getitem__(self, index: int) -> RequestItem:
        if self.items is None:
            raise IndexError("ProjectItemListResponse is empty")
        return self.items[index]

    def __len__(self) -> int:
        return len(self.items) if self.items else 0

    def __iter__(self):
        """Make ProjectItemListResponse iterable over its items."""
        if self.items is None:
            return iter([])
        return iter(self.items)

    def append(self, item: RequestItem) -> None:
        """Append an Agent instance to the items list."""
        if self.items is None:
            self.items = []
        self.items.append(item)
