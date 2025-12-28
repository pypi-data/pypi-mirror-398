from pygeai.organization.managers import OrganizationManager

manager = OrganizationManager()


response = manager.delete_project("b91a21f1-0e5f-4aaf-bef5-e3cefd029d87")
print(f"response: {response}")
