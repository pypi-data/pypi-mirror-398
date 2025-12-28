from pygeai.organization.managers import OrganizationManager

client = OrganizationManager()


response = client.export_request_data()
print(f"response: {response}")
