from pygeai.organization.managers import OrganizationManager

manager = OrganizationManager()


response = manager.get_project_tokens("1956c032-3c66-4435-acb8-6a06e52f819f")
print(f"response: {response}")
