from pygeai.lab.managers import AILabManager
from pygeai.lab.models import Agent, AgentData, Prompt, LlmConfig, Model, Sampling, PromptExample, PromptOutput

agent = Agent(
    id="f64ba214-152b-4dd4-be0d-2920da415f5d",
    status="active",
    name="Private Translator V25",
    access_scope="private",
    public_name="com.genexus.geai.private_translator_25",
    job_description="Translates",
    avatar_image="https://www.shareicon.net/data/128x128/2016/11/09/851442_logo_512x512.png",
    description="Agent that translates from any language to english.",
    is_draft=False,
    is_readonly=False,
    revision=1,
    version=None,
    agent_data=AgentData(
        prompt=Prompt(
            instructions="the user will provide a text, you must return the same text translated to english",
            inputs=["text", "avoid slang indicator"],
            outputs=[
                PromptOutput(key="translated_text", description="translated text, with slang or not depending on the indication. in plain text."),
                PromptOutput(key="summary", description="a summary in the original language of the text to be translated, also in plain text.")
            ],
            examples=[
                PromptExample(input_data="opitiiiis mundo [no-slang]", output='{"translated_text":"hello world","summary":"saludo"}'),
                PromptExample(input_data="esto es una prueba pincheguey [keep-slang]", output='{"translated_text":"this is a test pal","summary":"prueba"}')
            ]
        ),
        llm_config=LlmConfig(
            max_tokens=5000,
            timeout=0,
            sampling=Sampling(temperature=0.5, top_k=0, top_p=0)
        ),
        models=[Model(name="gpt-4-turbo-preview")]
    )
)


manager = AILabManager()
result = manager.create_agent(
    agent=agent,
    automatic_publish=False
)


print(f"Agent: {agent.to_dict()}")

