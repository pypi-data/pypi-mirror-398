from pygeai.organization.managers import OrganizationManager

manager = OrganizationManager(alias="sdkorg")
# manager = OrganizationManager()


response = manager.get_project_list("full")
print(f"response: {response}")
