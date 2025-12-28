from pygeai.organization.managers import OrganizationManager

manager = OrganizationManager()


response = manager.get_assistant_list("full")
print(f"response: {response}")
