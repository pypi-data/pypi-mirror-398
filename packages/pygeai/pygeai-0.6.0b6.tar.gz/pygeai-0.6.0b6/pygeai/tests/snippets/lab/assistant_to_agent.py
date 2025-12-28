from typing import Union
from uuid import uuid4
from pydantic import ValidationError
import logging
from pygeai.core.common.exceptions import MissingRequirementException
from pygeai.core.models import Assistant
from pygeai.lab.models import Agent, AgentData, Prompt, LlmConfig, Sampling, Model, ModelList
from pygeai.core.base.responses import ErrorListResponse
from pygeai.assistant.managers import AssistantManager
from pygeai.lab.managers import AILabManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def transform_assistant_to_agent(assistant: Assistant) -> Agent:
    """
    Transform an Assistant object into an Agent object, using Assistant.name as Agent.name.
    """
    try:
        if not assistant.name:
            raise ValueError("Assistant.name cannot be None or empty")

        # Map status
        status_map = {1: "active", 2: "inactive"}
        agent_status = status_map.get(assistant.status, "active")

        # Map LLM settings to LlmConfig
        llm_config = None
        if assistant.llm_settings:
            sampling = Sampling(
                temperature=assistant.llm_settings.temperature or 0.7,  # Default from Assistant example
                top_k=50,  # Default, as Agent example uses top_k=0 which may not be suitable
                top_p=assistant.llm_settings.top_p or 1.0
            )
            llm_config = LlmConfig(
                max_tokens=assistant.llm_settings.max_tokens or 1000,  # Default from Assistant example
                timeout=60,  # Default, as Agent example uses 0 which may not be suitable
                sampling=sampling
            )

        # Map revisions to models
        models = []
        if assistant.revisions:
            for revision in assistant.revisions:
                model_prompt = {"instructions": revision.prompt} if revision.prompt else None
                model = Model(
                    name=revision.model_name or f"model_{revision.revision_id or uuid4().hex}",
                    llm_config=llm_config,
                    prompt=model_prompt
                )
                models.append(model)
        else:
            # Use llm_settings.model_name if no revisions, aligning with Assistant example
            if assistant.llm_settings and assistant.llm_settings.model_name:
                models.append(Model(
                    name=str(assistant.llm_settings.model_name),  # e.g., "gpt-4"
                    llm_config=llm_config,
                    prompt=None
                ))
        models = ModelList(models=models) if models else ModelList(models=[])

        # Create Prompt
        prompt = Prompt(
            instructions=assistant.prompt or "Default instructions for the agent",
            inputs=[],  # Assistant doesn't provide inputs, unlike Agent example
            outputs=[],  # Assistant doesn't provide outputs, unlike Agent example
            context=None,
            examples=None
        )

        # Create AgentData
        agent_data = AgentData(
            prompt=prompt,
            llm_config=llm_config or LlmConfig(
                max_tokens=1000,  # Default from Assistant example
                timeout=60,
                sampling=Sampling(temperature=0.7, top_k=50, top_p=1.0)  # Defaults from Assistant example
            ),
            models=models,
            resource_pools=None
        )

        # Use welcome_data.description for job_description if available, else fallback to description
        job_description = (
            assistant.welcome_data.description
            if assistant.welcome_data and assistant.welcome_data.description
            else assistant.description
        )

        # Create Agent
        agent = Agent(
            id=assistant.id or str(uuid4()),
            status=agent_status,
            name=assistant.name,  # Use Assistant.name directly
            access_scope="private",  # Default from Agent example
            public_name=None,  # Agent example uses a specific format, but Assistant doesn't provide this
            avatar_image=None,  # Agent example has a URL, but Assistant doesn't provide this
            description=assistant.description,
            job_description=job_description,
            is_draft=True,  # Default, unlike Agent example's False
            is_readonly=False,
            revision=assistant.revisions[0].revision_id if assistant.revisions else None,
            version=None,
            agent_data=agent_data
        )

        return agent

    except ValidationError as e:
        logger.error(f"Validation error while transforming assistant {assistant.id}: {e}")
        raise
    except ValueError as e:
        logger.error(f"Value error while transforming assistant {assistant.id}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while transforming assistant {assistant.id}: {e}")
        raise

def fetch_transform_create_agent(
    assistant_id: str,
    project_id: str,
    detail: str = "full",
    automatic_publish: bool = False
) -> Union[Agent, ErrorListResponse]:
    """
    Fetch an Assistant by ID, transform it to an Agent, and create it in the specified project.

    Args:
        assistant_id (str): The ID of the Assistant to fetch.
        project_id (str): The ID of the project where the Agent will be created.
        detail (str, optional): The detail level for fetching Assistant ("summary" or "full"). Defaults to "full".
        automatic_publish (bool, optional): Whether to automatically publish the created Agent. Defaults to False.

    Returns:
        Union[Agent, ErrorListResponse]: The created Agent or an error response.
    """
    try:
        # Initialize managers
        assistant_manager = AssistantManager()
        ailab_manager = AILabManager()

        # Fetch Assistant
        logger.info(f"Fetching Assistant with ID: {assistant_id}")
        assistant = assistant_manager.get_assistant_data(assistant_id=assistant_id, detail=detail)
        if isinstance(assistant, ErrorListResponse):
            logger.error(f"Failed to fetch Assistant: {assistant}")
            return assistant

        # Transform to Agent
        logger.info(f"Transforming Assistant {assistant_id} to Agent")
        agent = transform_assistant_to_agent(assistant)

        # Create Agent
        logger.info(f"Creating Agent in project {project_id}")
        result = ailab_manager.create_agent(
            project_id=project_id,
            agent=agent,
            automatic_publish=automatic_publish
        )

        logger.info(f"Successfully created Agent with ID: {result.id}, Name: {result.name}")
        return result

    except MissingRequirementException as e:
        logger.error(f"Missing requirement: {e}")
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
    except ValueError as e:
        logger.error(f"Value error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    try:
        ASSISTANT_ID = "3806a85f-cb06-4724-8dba-da19b0a702eb"
        PROJECT_ID = "1956c032-3c66-4435-acb8-6a06e52f819f"

        result = fetch_transform_create_agent(
            assistant_id=ASSISTANT_ID,
            project_id=PROJECT_ID,
            detail="full",
            automatic_publish=True
        )
        if isinstance(result, Agent):
            print(f"Created Agent: ID={result.id}, Name={result.name}")
        else:
            print(f"Error: {result}")
    except Exception as e:
        print(f"Error in main: {e}")