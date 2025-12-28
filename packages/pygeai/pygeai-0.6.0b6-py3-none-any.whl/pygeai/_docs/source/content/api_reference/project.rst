Project Management
==================

The API Reference provides a comprehensive set of tools for managing projects within your organization. You can perform the following actions:
* Create project: Creates a new project within your organization.
* Get project data: Retrieves detailed information about a specific project using its Id.
* Delete project: Deletes an existing project.
* List projects: Retrieves a list of all projects within your organization. You can choose to retrieve a summary or detailed information for each project.
* Update project: Updates the name and description of an existing project.

List projects
~~~~~~~~~~~~~~

Lists existing projects within an organization using `PyGEA </pygeai>`_. You can choose to display a summary or the full project information.

To achieve this, you have three options:

* `Command Line </docs/source/content/api_reference.rst#command-line>`_
* `Low-Level Service Layer </docs/source/content/api_reference.rst#low-level-service-layer>`_
* `High-Level Service Layer </docs/source/content/api_reference.rst#high-level-service-layer>`_


Command line
^^^^^^^^^^^^

You can list projects using the following command-line options:


List projects with summary details (default)
############################################

You can list the projects without additional options, as follows:

.. code-block:: shell

    geai org list-projects


List projects with full details
###############################

Use the optional flag "-d" to indicate "full" detail. The default is summary.

.. code-block:: shell

    geai org list-projects -d full


If we need to work with a different API key, we can indicate an alias. Let's suppose we have an 'admin' alias with an
organization API key.

List projects using a different API token (alias)
#################################################

.. code-block:: shell

    geai --alias <alias_name> org list-projects

Replace `<alias_name>` with the actual alias for your `GEAI_API_KEY` (e.g., "admin").

**Note**: Each alias defines a profile with a specific access level. Based on the profile's access level, you will need to use SAIA_ORGANIZATION_APITOKEN or SAIA_PROJECT_APITOKEN as GEAI_API_KEY.


Low level service layer
^^^^^^^^^^^^^^^^^^^^^^^

Use the following code snippet to list projects with the desired detail level:

.. code-block:: python

    from pygeai.organization.clients import OrganizationClient()

    client = OrganizationClient()
    project_list = client.get_project_list(detail="full")  # Use "summary" for less detail
    print(project_list)


High level service layer
^^^^^^^^^^^^^^^^^^^^^^^^

Use the following code snippets to list projects using the high-level service layer:

List projects with default details
##################################

You can get the list of projects by calling the "get_project_list" method from the OrganizationManager manager class.


.. code-block:: python

    from pygeai.organization.managers import OrganizationManager

    manager = OrganizationManager()

    response = manager.get_project_list()
    print(f"response: {response}")


List projects with full details and a specific alias
####################################################

Also, you can indicate the alias for the desired environment to use.

.. code-block:: python

    from pygeai.organization.managers import OrganizationManager

    manager = OrganizationManager(alias="sdkorg")

    response = manager.get_project_list("full")
    print(f"response: {response}")



Create project
~~~~~~~~~~~~~~

Creates a new project in `Globant Enterprise AI <https://wiki.genexus.com/enterprise-ai/wiki?8,Table+of+contents%3AEnterprise+AI>`_ using `PyGEA </pygeai>`_, providing the project name and the administrator's email address. Optionally, you can add a project description and set `usage limits <https://wiki.genexus.com/enterprise-ai/wiki?802,Usage+Limits+API#:~:text=Managing%20quotas%20per%20project>`_.

To achieve this, you have three options:

* `Command Line </docs/source/content/api_reference.rst#command-line>`_
* `Low-Level Service Layer </docs/source/content/api_reference.rst#low-level-service-layer>`_
* `High-Level Service Layer </docs/source/content/api_reference.rst#high-level-service-layer>`_

Command line
^^^^^^^^^^^^

The simplest way to create a project is using the command line:

1. Open your terminal or command prompt.
2. Run the following command, replacing the placeholders with your desired values:

.. code-block:: shell

    geai org create-project \
      -n "Project Name" \
      -e "admin@example.com"  \
      -d "Project Description"

Where:

- `n`: Name of your project.
- `e`: Email address of the project administrator.
- `d`: Optional description for your project.


Low level service layer
^^^^^^^^^^^^^^^^^^^^^^^

For more control, you can use the low-level service layer. To do so:

1.  Import the necessary modules.
2.  Create an instance of the `OrganizationClient` class.
3.  Call the `create_project` method, providing the required information.

.. code-block:: python

    from pygeai.organization.clients import OrganizationClient()

    name="Project Name"
    description="Project Description"
    email="admin@example.com"

    client = OrganizationClient()
    new_project = client.create_project(name=name, email=email, description=description)
    print(new_project)


High level service layer
^^^^^^^^^^^^^^^^^^^^^^^^

The high-level service layer offers a more structured approach:

1. Import the necessary modules.
2. Create an instance of the `OrganizationManager` class.
3. Define the project's usage limits (optional).
4. Create a `Project` object with the necessary information.
5. Call the `create_project` method of the `OrganizationManager` to create the project.

.. code-block:: python

    from pygeai.organization.managers import OrganizationManager
    from pygeai.core.models import ProjectUsageLimit, Project

    manager = OrganizationManager()

    usage_limit = ProjectUsageLimit(
        subscription_type="Monthly",  # Options: Freemium, Daily, Weekly, Monthly
        usage_unit="Requests",        # Options: Cost (Only Cost is allowed for organization limits)
        soft_limit=500.0,             # Recommended usage limit
        hard_limit=1000.0,            # Maximum allowed usage
        renewal_status="Renewable"    # Options: Renewable, NonRenewable
    )

    project = Project(
        name="Project Name",
        description="Project Description",
        email="admin@example.com",
        usage_limit=usage_limit
    )


    created_project = manager.create_project(project)


Update project
~~~~~~~~~~~~~~

Updates an existing project in `Globant Enterprise AI <https://wiki.genexus.com/enterprise-ai/wiki?8,Table+of+contents%3AEnterprise+AI>`_  using `PyGEA </pygeai>`_. You can modify a project's name and description by providing its Id and updated information.

To update usage limits, refer to `Managing quotas per project <https://wiki.genexus.com/enterprise-ai/wiki?71,Managing+quotas+per+project>`_.

To achieve this, you have three options:

* `Command Line </docs/source/content/api_reference.rst#command-line>`_
* `Low-Level Service Layer </docs/source/content/api_reference.rst#low-level-service-layer>`_
* `High-Level Service Layer </docs/source/content/api_reference.rst#high-level-service-layer>`_

Command line
^^^^^^^^^^^^

Use the following command to update a project:


.. code-block:: shell

    geai org update-project \
      -id <project_id> \
      --name "<new_project_name>" \
      --description "<new_project_description>"

Replace the placeholders with the actual values:

* `<project_id>`: Id of the project you want to update.
* `<new_project_name>`: New name for the project.
* `<new_project_description>`: New description for the project.

For example:

.. code-block:: shell
    geai org update-project \
      --id 12345678-90ab-cdef-1234-567890abcdef \
      --name "Updated Project Name" \
      --description "This is the updated project description"


Low level service layer
^^^^^^^^^^^^^^^^^^^^^^^

Use the following code snippet to update a project using the low-level service layer:


.. code-block:: python

    from pygeai.organization.clients import OrganizationClient()

    project_id="<project_id>"
    name="<new_project_name>"
    description="<new_project_description>"

    client = OrganizationClient()
    new_project = client.update_project(
        project_id=project_id,
        name=name,
        description=description
    )
    print(new_project)

Replace the placeholders with the actual values for your project.


High level service layer
^^^^^^^^^^^^^^^^^^^^^^^^

Use the following code snippet to update a project using the high-level service layer:


.. code-block:: python

    from pygeai.organization.managers import OrganizationManager
    from pygeai.core.models import UsageLimit, Project

    client = OrganizationManager()

    project = Project(
        d="<project_id>",
        name="<new_project_name>",
        description="<new_project_description>",
    )


    project = client.update_project(project)
    print(f"project: {project}")


Replace the placeholders with the actual values for your project.


Delete project
~~~~~~~~~~~~~~

Deletes an existing project in `Globant Enterprise AI <https://wiki.genexus.com/enterprise-ai/wiki?8,Table+of+contents%3AEnterprise+AI>`_ using `PyGEA </pygeai>`_. You can delete a project by providing its project Id.

A successful deletion results in an empty response. If the project doesn't exist or if you lack the necessary permissions, an error occurs.

To delete a project, you have three options:

* `Command Line </docs/source/content/api_reference.rst#command-line>`_
* `Low-Level Service Layer </docs/source/content/api_reference.rst#low-level-service-layer>`_
* `High-Level Service Layer </docs/source/content/api_reference.rst#high-level-service-layer>`_

Command line
^^^^^^^^^^^^

Use the following command to delete a project:

.. code-block:: shell

    geai org delete-project \
      --id <project_id>

Replace <`project_id`> with the actual project Id. For example:

.. code-block:: shell
    geai org delete-project \
      --id 12345678-90ab-cdef-1234-567890abcdef


Low level service layer
^^^^^^^^^^^^^^^^^^^^^^^

Use the following code snippet to delete a project using the low-level service layer:


.. code-block:: python

    from pygeai.organization.clients import OrganizationClient()

    project_id = "<project_id>"
    client = OrganizationClient()
    deleted_project = client.delete_project(project_id=project_id)
    print(deleted_project)

Replace <`project_id`> with the actual project Id. For example:

.. code-block:: python

    from pygeai.organization.clients import OrganizationClient()

    project_id="12345678-90ab-cdef-1234-567890abcdef"
    client = OrganizationClient()
    deleted_project = client.delete_project(

High level service layer
^^^^^^^^^^^^^^^^^^^^^^^^

Use the following code snippet to delete a project using the high-level service layer:

.. code-block:: python

    from pygeai.organization.managers import OrganizationManager

    manager = OrganizationManager()

    response = manager.delete_project("<project_id>")
    print(f"response: {response}")

Replace <`project_id`> with the actual project Id. For example:

.. code-block:: python

    from pygeai.core.managers import OrganizationManager

    manager = OrganizationManager()
    response = manager.delete_project("12345678-90ab-cdef-1234-567890abcdef")
    print(f"response: {response}")


Get project data
~~~~~~~~~~~~~~~~

Retrieves project data using `PyGEA </pygeai>`_. You can fetch project details by providing the project Id.

To achieve this, you have three options:

* `Command Line </docs/source/content/api_reference.rst#command-line>`_
* `Low-Level Service Layer </docs/source/content/api_reference.rst#low-level-service-layer>`_
* `High-Level Service Layer </docs/source/content/api_reference.rst#high-level-service-layer>`_


Command line
^^^^^^^^^^^^

Use the following command to retrieve the project:

.. code-block:: shell

    geai org get-project \
    --id <project_id>

Replace `<project_id>` with the actual project Id. For example:

.. code-block:: shell

    geai org get-project \
    --id 12345678-90ab-cdef-1234-567890abcdef


Low level service layer
^^^^^^^^^^^^^^^^^^^^^^^

Use the following code snippet to retrieve project data using the low-level service layer:


.. code-block:: python

    from pygeai.organization.clients import OrganizationClient()

    project_id="<project_id>"
    client = OrganizationClient()
    project_data = client.get_project_data(project_id=project_id)
    print(project_data)

Replace `<project_id>` with the actual project Id. For example:


.. code-block:: python

    from pygeai.organization.clients import OrganizationClient()

    project_id="12345678-90ab-cdef-1234-567890abcdef"
    client = OrganizationClient()
    project_data = client.get_project_data(project_id=project_id)
    print(project_data)


High level service layer
^^^^^^^^^^^^^^^^^^^^^^^^

Use the following code snippet to retrieve project data using the high-level service layer:


.. code-block:: python

    from pygeai.organization.managers import OrganizationManager

    manager = OrganizationManager(alias="sdkorg")

    project = manager.get_project_data(project_id="<project_id>")
    print(f"project: {project}")


Replace `<project_id>` with the actual project Id. For example:

.. code-block:: python

    from pygeai.core.managers import OrganizationManager

    manager = OrganizationManager(alias="sdkorg")
    project = manager.get_project_data(project_id="12345678-90ab-cdef-1234-567890abcdef")
    print(f"project: {project}")


Token Management
================
You can manage project tokens, which are essential for authentication and authorization when interacting with specific projects.

* Get Project Tokens: Retrieves the tokens associated with a specific project.

Get Project Tokens
~~~~~~~~~~~~~~~~~~

Retrieves the tokens associated with a specific project using PyGEA. You can fetch these tokens by providing the project Id.

To achieve this, you have three options:

* `Command Line </docs/source/content/api_reference.rst#command-line>`_
* `Low-Level Service Layer </docs/source/content/api_reference.rst#low-level-service-layer>`_
* `High-Level Service Layer </docs/source/content/api_reference.rst#high-level-service-layer>`_

Command line
^^^^^^^^^^^^

Use the following command to retrieve project tokens:

.. code-block:: shell
    geai org get-tokens --id <project_id>

Replace `<project_id>` with the actual project Id. For example:

.. code-block:: shell
    geai org get-tokens --id 12345678-90ab-cdef-1234-567890abcdef


Low level service layer
^^^^^^^^^^^^^^^^^^^^^^^

Use the following code snippet to retrieve project tokens using the low-level service layer:


.. code-block:: python

    from pygeai.organization.clients import OrganizationClient

    project_id = "<project_id>"

    client = OrganizationClient()
    tokens = client.get_project_tokens(project_id=project_id)
    print(tokens)

Replace `<project_id>` with the actual project Id. For example:

.. code-block:: python

    from pygeai.organization.clients import OrganizationClient

    project_id = "12345678-90ab-cdef-1234-567890abcdef"

    client = OrganizationClient()
    tokens = client.get_project_tokens(project_id=project_id)
    print(tokens)

High level service layer
^^^^^^^^^^^^^^^^^^^^^^^^

Use the following code snippet to retrieve project tokens using the high-level service layer:

.. code-block:: python

    from pygeai.core.managers import OrganizationManager
    from pygeai.core.base.models import ProjectTokensResponse

    client = OrganizationManager()
    project_id = "<project_id>"

    tokens: ProjectTokensResponse = client.get_project_tokens(project_id=project_id)
    print(f"tokens: {tokens}")

Replace `<project_id>` with the actual project Id. For example:

.. code-block:: python

    from pygeai.organization.managers import OrganizationManager
    from pygeai.core.models import ProjectTokensResponse

    client = OrganizationManager()

    project_id = "12345678-90ab-cdef-1234-567890abcdef"

    tokens: ProjectTokensResponse = client.get_project_tokens(project_id=project_id)
    print(f"tokens: {tokens}")
