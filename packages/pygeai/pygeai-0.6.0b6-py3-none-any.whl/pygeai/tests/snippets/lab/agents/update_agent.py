from pygeai.lab.managers import AILabManager
from pygeai.lab.models import Agent, AgentData, Prompt, LlmConfig, Model, Sampling, PromptExample, PromptOutput, ModelList

updated_agent = Agent(
    id="9716a0a1-5eab-4cc9-a611-fa2c3237c511",
    status="active",
    name="Public Translator V21 Updated",
    access_scope="public",
    public_name="com.genexus.geai.public_translator_21",
    job_description="Translates updated",
    avatar_image="https://www.shareicon.net/data/128x128/2016/11/09/851442_logo_512x512.png",
    description="Updated agent that translates from any language to English.",
    is_draft=True,
    is_readonly=False,
    revision=1,
    version=None,
    agent_data=AgentData(
        prompt=Prompt(
            instructions="the user will provide a text, you must return the same text translated to English with updates",
            inputs=["text", "avoid slang indicator"],
            outputs=[
                PromptOutput(key="translated_text", description="translated text, updated version"),
                PromptOutput(key="summary", description="summary in original language, updated")
            ],
            examples=[
                PromptExample(input_data="opitiiiis mundo [no-slang]", output='{"translated_text":"hello world","summary":"saludo"}'),
                PromptExample(input_data="esto es una prueba [keep-slang]", output='{"translated_text":"this is a test","summary":"prueba"}')
            ]
        ),
        llm_config=LlmConfig(
            max_tokens=6000,
            timeout=0,
            sampling=Sampling(temperature=0.6, top_k=0, top_p=0.0)
        ),
        models=ModelList(models=[
            Model(name="gpt-4-turbo-preview"),
            Model(name="xlm-roberta-large")
        ])
    )
)

manager = AILabManager()

result = manager.update_agent(
    agent=updated_agent,
    automatic_publish=False,
    upsert=False
)

print(f"Updated agent: {result.to_dict()}")
