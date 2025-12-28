from pygeai.core.models import Project, Organization
from pygeai.organization.limits.managers import UsageLimitManager


organization = Organization(id="4aa15b61-d3c7-4a5c-99b8-052d18a04ff2")
project = Project(id="1956c032-3c66-4435-acb8-6a06e52f819f")

limit_id = "6d95069b-bab5-4281-b432-a7f5b4290227"

manager = UsageLimitManager(alias="sdkorg", organization_id=organization.id)

response = manager.delete_usage_limit_from_organization(
    limit_id=limit_id
)

print(f"response: {response}")