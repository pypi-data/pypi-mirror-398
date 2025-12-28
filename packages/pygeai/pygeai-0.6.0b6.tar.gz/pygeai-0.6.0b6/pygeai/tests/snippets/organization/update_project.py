from pygeai.organization.managers import OrganizationManager
from pygeai.core.models import Project

client = OrganizationManager()

project = Project(
    id="1956c032-3c66-4435-acb8-6a06e52f819f",
    name="AI Project",
    description="An AI project focused on natural language processing and testing",
)


response = client.update_project(project)
print(f"response: {response}")
