geai - cli examples
===================

In this section, you can find examples of commands using the geai utility to perform basic tasks in GEAI.

# Display help

.. code-block:: shell

    geai h

.. code-block:: shell

    geai org h

.. code-block:: shell

    geai ast h


.. code-block:: shell

    geai chat h


# Create project

.. code-block:: shell

    geai org create-project \
      -n "SDKTest2" \
      -e "geai-sdk@globant.com" \
      -d "Test project for SDK"

# Update project

.. code-block:: shell

     geai org update-project \
      --id 12345678-1234-1234-1234-123456789abc \
      --name "SDK Test 3" \
      --description "Test description"

# List projects

.. code-block:: shell

    geai org list-projects

.. code-block:: shell

    geai org list-projects -d full

# Get tokens from organization

.. code-block:: shell

    geai org get-tokens --id aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee

# List assistants

.. code-block:: shell

    geai org list-assistants

# Get assistant information

.. code-block:: shell

    geai ast get-assistant --id 11111111-2222-3333-4444-555555555555

# Chat with assistant

.. code-block:: shell

    geai ast chat \
      --name "Welcome data Assistant" \
      --msg '[{"role": "user", "content": "Translate the phrase free software is the software that protects users freedoms"}, {"role": "user", "content": "now translate to french"]'


# Create assistant

.. code-block:: shell

    geai ast create-assistant \
      --type chat \
      --name "Welcome data Assistant 3" \
      --prompt "Translate to French" \
      --wd-title "Assistant with WelcomeData" \
      --wd-description "It is to test WelcomeData" \
      --wd-feature '[{"title": "First Feature", "description": "First Feature Description"}, {"title": "Second Feature", "description": "Second Feature Description"}]' \
      --wd-example-prompt '{"title": "First Prompt Example", "description": "First Prompt Example Description", "prompt_text": "You are an assistant specialized in translating"}'


# Update assistant

.. code-block:: shell

    geai ast update-assistant \
      --assistant-id 99999999-8888-7777-6666-555555555555 \
      --action savePublishNewRevision \
      --prompt "translate the following text to Latin" \
      --provider-name "openai" \
      --model-name "gpt-3.5-turbo" \
      --temperature 0.0 \\n  --wd-title "Assistant with WelcomeData" \
      --wd-description "It is to test WelcomeData" \
      --wd-feature "Second Feature: Second Feature Description" \
      --wd-feature "First Feature: First Feature Description" \
      --wd-example-prompt "First Prompt Example: First Prompt Example Description: You are an assistant specialized in translating"

# Delete assistant

.. code-block:: shell

    geai ast delete-assistant --id 99999999-8888-7777-6666-555555555555


# Chat completion

.. code-block:: shell

    geai chat completion \
      --model "saia:assistant:Welcome data Assistant 3" \
      --msg '[{"role": "user", "content": "Translate the phrase free software is the software that protects users freedoms"}, {"role": "user", "content": "now translate to french and italian"}]' \
      --stream 0

