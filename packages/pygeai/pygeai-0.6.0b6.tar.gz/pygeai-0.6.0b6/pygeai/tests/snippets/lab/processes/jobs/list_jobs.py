from pygeai.lab.managers import AILabManager
from pygeai.lab.models import FilterSettings

manager = AILabManager()

response = manager.list_jobs(
    filter_settings=FilterSettings(start="0", count="100"),
    topic=None,
    token=None
)

jobs = response
print("Jobs retrieved successfully:")
for job in jobs:
    print(f"- Job: {job.name}, Token: {job.token}, Topic: {job.topic}, Caption: {job.caption}")
    if job.parameters:
        print("  Parameters:")
        for param in job.parameters:
            print(f"    - {param.Name}: {param.Value}")
    if job.info:
        print(f"  Info: {job.info}")