from pygeai.core.models import UsageLimit, Project, Organization
from pygeai.organization.limits.managers import UsageLimitManager


organization = Organization(id="4aa15b61-d3c7-4a5c-99b8-052d18a04ff2")
project = Project(id="1956c032-3c66-4435-acb8-6a06e52f819f")

usage_limit = UsageLimit(
    id="4bb78b5a-07ea-4d15-84d6-e0baee53ff61",
    subscription_type="Monthly",
    usage_unit="Cost",
    soft_limit=1000.0,
    hard_limit=2000.0,
    renewal_status="Renewable"
)

manager = UsageLimitManager(alias="sdkorg", organization_id=organization.id)

response = manager.update_organization_usage_limit(
    usage_limit=usage_limit,
)

print(f"response: {response}")