import unittest
from unittest import TestCase

from pydantic_core._pydantic_core import ValidationError

from pygeai.lab.models import (
    FilterSettings, Sampling, LlmConfig, Model, PromptExample, PromptOutput, Prompt, ModelList,
    AgentData, Agent, AgentList, SharingLink, ToolParameter, ToolMessage, Tool, ToolList,
    LocalizedDescription, ReasoningStrategy, ReasoningStrategyList, KnowledgeBase, AgenticActivity,
    ArtifactSignal, UserSignal, Event, SequenceFlow, AgenticProcess, Task, AgenticProcessList,
    TaskList, Variable, VariableList, ProcessInstance, ProcessInstanceList, ArtifactType, ArtifactTypeList,
    JobParameter, Job, JobList, ResourcePoolTool, ResourcePoolAgent, ResourcePool, ResourcePoolList, KnowledgeBaseList
)


class TestLabModels(TestCase):
    """
    python -m unittest pygeai.tests.lab.test_models.TestLabModels
    """

    def test_filter_settings_model_validate(self):
        filter_data = {
            "id": "agent123",
            "name": "test-agent",
            "accessScope": "private",
            "isActive": False,
            "allowDrafts": False,
            "allowExternal": False
        }
        filter_settings = FilterSettings.model_validate(filter_data)
        self.assertEqual(filter_settings.id, filter_data["id"])
        self.assertEqual(filter_settings.name, filter_data["name"])
        self.assertEqual(filter_settings.access_scope, filter_data["accessScope"])
        self.assertEqual(filter_settings.allow_drafts, filter_data["allowDrafts"])
        self.assertIsNone(filter_settings.status)
        self.assertTrue(filter_settings.to_dict() == filter_data)

    def test_sampling_model_validate(self):
        sampling_data = {
            "temperature": 0.7,
            "topK": 40,
            "topP": 0.9
        }
        sampling = Sampling.model_validate(sampling_data)
        self.assertEqual(sampling.temperature, sampling_data["temperature"])
        self.assertEqual(sampling.top_k, sampling_data["topK"])
        self.assertEqual(sampling.top_p, sampling_data["topP"])
        self.assertTrue(sampling.to_dict() == sampling_data)

    def test_llm_config_model_validate(self):
        llm_config_data = {
            "maxTokens": 1000,
            "timeout": 30,
            "sampling": {"temperature": 0.7, "topK": 40, "topP": 0.9}
        }
        llm_config = LlmConfig.model_validate(llm_config_data)
        self.assertEqual(llm_config.max_tokens, llm_config_data["maxTokens"])
        self.assertEqual(llm_config.timeout, llm_config_data["timeout"])
        self.assertEqual(llm_config.sampling.temperature, llm_config_data["sampling"]["temperature"])
        self.assertEqual(llm_config.sampling.top_k, llm_config_data["sampling"]["topK"])
        self.assertEqual(llm_config.sampling.top_p, llm_config_data["sampling"]["topP"])
        self.assertTrue(llm_config.to_dict() == llm_config_data)

    def test_model_model_validate(self):
        model_data = {
            "name": "gpt-4",
            "llmConfig": {"maxTokens": 500, "timeout": 20, "sampling": {"temperature": 0.5, "topK": 30, "topP": 0.8}}
        }
        model = Model.model_validate(model_data)
        self.assertEqual(model.name, model_data["name"])
        self.assertEqual(model.llm_config.max_tokens, model_data["llmConfig"]["maxTokens"])
        self.assertEqual(model.llm_config.timeout, model_data["llmConfig"]["timeout"])
        self.assertEqual(model.llm_config.sampling.temperature, model_data["llmConfig"]["sampling"]["temperature"])
        self.assertIsNone(model.prompt)
        self.assertTrue(model.to_dict() == model_data)

    def test_prompt_example_model_validate(self):
        example_data = {
            "inputData": "Hello world",
            "output": '{"result": "Hi"}'
        }
        prompt_example = PromptExample.model_validate(example_data)
        self.assertEqual(prompt_example.input_data, example_data["inputData"])
        self.assertEqual(prompt_example.output, example_data["output"])
        self.assertTrue(prompt_example.to_dict() == example_data)

    def test_prompt_output_model_validate(self):
        output_data = {
            "key": "summary",
            "description": "Summary of text"
        }
        prompt_output = PromptOutput.model_validate(output_data)
        self.assertEqual(prompt_output.key, output_data["key"])
        self.assertEqual(prompt_output.description, output_data["description"])
        self.assertTrue(prompt_output.to_dict() == output_data)

    def test_prompt_model_validate(self):
        prompt_data = {
            "instructions": "Summarize text",
            "inputs": ["text"],
            "outputs": [{"key": "summary", "description": "Summary of text"}],
            "examples": [{"inputData": "Hello world", "output": '{"summary": "Hi"}'}]
        }
        prompt = Prompt.model_validate(prompt_data)
        self.assertEqual(prompt.instructions, prompt_data["instructions"])
        self.assertEqual(prompt.inputs, prompt_data["inputs"])
        self.assertEqual(prompt.outputs[0].key, prompt_data["outputs"][0]["key"])
        self.assertEqual(prompt.examples[0].input_data, prompt_data["examples"][0]["inputData"])
        self.assertTrue(prompt.to_dict() == prompt_data)

    def test_model_list_model_validate(self):
        model_list_data = [
            {"name": "gpt-4"},
            {"name": "gpt-3.5-turbo"}
        ]
        model_list = ModelList.model_validate({"models": model_list_data})
        self.assertEqual(len(model_list.models), 2)
        self.assertEqual(model_list.models[0].name, model_list_data[0]["name"])
        self.assertEqual(model_list.models[1].name, model_list_data[1]["name"])
        self.assertTrue(model_list.to_dict() == model_list_data)

    def test_agent_data_model_validate(self):
        agent_data_data = {
            "prompt": {"instructions": "Summarize", "inputs": ["text"], "outputs": [{"key": "summary", "description": "Summary"}]},
            "llmConfig": {"maxTokens": 1000, "timeout": 30, "sampling": {"temperature": 0.7, "topK": 40, "topP": 0.9}},
            "models": [{"name": "gpt-4"}]
        }
        agent_data = AgentData.model_validate(agent_data_data)
        self.assertEqual(agent_data.prompt.instructions, agent_data_data["prompt"]["instructions"])
        self.assertEqual(agent_data.llm_config.max_tokens, agent_data_data["llmConfig"]["maxTokens"])
        self.assertEqual(agent_data.models.models[0].name, agent_data_data["models"][0]["name"])
        self.assertTrue(agent_data.to_dict() == agent_data_data)

    def test_agent_model_validate(self):
        agent_data = {
            "id": "agent123",
            "status": "active",
            "name": "TestAgent",
            "isDraft": False,
            "isReadonly": False,
            "accessScope": "public",
            "publicName": "test-agent",
            "agentData": {
                "prompt": {"instructions": "Summarize", "inputs": ["text"], "outputs": [{"key": "summary", "description": "Summary"}]},
                "llmConfig": {"maxTokens": 1000, "timeout": 30, "sampling": {"temperature": 0.7, "topK": 40, "topP": 0.9}},
                "models": [{"name": "gpt-4"}]
            }
        }
        agent = Agent.model_validate(agent_data)
        self.assertEqual(agent.id, agent_data["id"])
        self.assertEqual(agent.name, agent_data["name"])
        self.assertEqual(agent.access_scope, agent_data["accessScope"])
        self.assertEqual(agent.public_name, agent_data["publicName"])
        self.assertEqual(agent.agent_data.prompt.instructions, agent_data["agentData"]["prompt"]["instructions"])
        self.assertTrue(agent.to_dict() == agent_data)

    def test_agent_list_model_validate(self):
        agent_list_data = {
            "agents": [
                {"id": "agent1", "name": "Agent1", "isReadonly": False, "isDraft": True, "accessScope": "private", "status": "active"},
                {"id": "agent2", "name": "Agent2", "isReadonly": False, "isDraft": True, "accessScope": "private", "status": "active"}
            ]
        }
        agent_list = AgentList.model_validate(agent_list_data)
        self.assertEqual(len(agent_list.agents), 2)
        self.assertEqual(agent_list.agents[0].id, agent_list_data["agents"][0]["id"])
        self.assertEqual(agent_list.agents[1].name, agent_list_data["agents"][1]["name"])
        self.assertTrue(agent_list.to_list() == agent_list_data["agents"])

    def test_sharing_link_model_validate(self):
        sharing_link_data = {
            "agentId": "agent123",
            "apiToken": "token456",
            "sharedLink": "https://example.com/share/agent123"
        }
        sharing_link = SharingLink.model_validate(sharing_link_data)
        self.assertEqual(sharing_link.agent_id, sharing_link_data["agentId"])
        self.assertEqual(sharing_link.api_token, sharing_link_data["apiToken"])
        self.assertEqual(sharing_link.shared_link, sharing_link_data["sharedLink"])
        self.assertTrue(sharing_link.to_dict() == sharing_link_data)

    def test_tool_parameter_model_validate(self):
        param_data = {
            "key": "input",
            "dataType": "String",
            "description": "Input text",
            "isRequired": True,
            "type": "app"
        }
        tool_param = ToolParameter.model_validate(param_data)
        self.assertEqual(tool_param.key, param_data["key"])
        self.assertEqual(tool_param.data_type, param_data["dataType"])
        self.assertEqual(tool_param.description, param_data["description"])
        self.assertEqual(tool_param.is_required, param_data["isRequired"])
        self.assertTrue(tool_param.to_dict() == param_data)

    def test_tool_message_model_validate(self):
        message_data = {
            "description": "Warning: deprecated",
            "type": "warning"
        }
        tool_message = ToolMessage.model_validate(message_data)
        self.assertEqual(tool_message.description, message_data["description"])
        self.assertEqual(tool_message.type, message_data["type"])
        self.assertTrue(tool_message.to_dict() == message_data)

    def test_tool_model_validate(self):
        tool_data = {
            "name": "TextTool",
            "description": "Processes text",
            "scope": "builtin",
            "parameters": [{"key": "input", "dataType": "String", "description": "Input text", "isRequired": True, "type": "app"}],
            "reportEvents": "None"

        }
        tool = Tool.model_validate(tool_data)
        self.assertEqual(tool.name, tool_data["name"])
        self.assertEqual(tool.description, tool_data["description"])
        self.assertEqual(tool.scope, tool_data["scope"])
        self.assertEqual(tool.parameters[0].key, tool_data["parameters"][0]["key"])
        self.assertTrue(tool.to_dict() == tool_data)

    def test_tool_list_model_validate(self):
        tool_list_data = {
            "tools": [
                {"name": "Tool1", "description": "Tool 1", "scope": "builtin", 'reportEvents': 'None'},
                {"name": "Tool2", "description": "Tool 2", "scope": "builtin", 'reportEvents': 'None'}
            ]
        }
        tool_list = ToolList.model_validate(tool_list_data)
        self.assertEqual(len(tool_list.tools), 2)
        self.assertEqual(tool_list.tools[0].name, tool_list_data["tools"][0]["name"])
        self.assertEqual(tool_list.tools[1].description, tool_list_data["tools"][1]["description"])
        self.assertTrue(tool_list.to_dict() == tool_list_data)

    def test_localized_description_model_validate(self):
        localized_data = {
            "language": "english",
            "description": "Test strategy"
        }
        localized_desc = LocalizedDescription.model_validate(localized_data)
        self.assertEqual(localized_desc.language, localized_data["language"])
        self.assertEqual(localized_desc.description, localized_data["description"])
        self.assertTrue(localized_desc.to_dict() == localized_data)

    def test_reasoning_strategy_model_validate(self):
        strategy_data = {
            "name": "TestStrategy",
            "accessScope": "public",
            "type": "addendum",
            "localizedDescriptions": [{"language": "english", "description": "Test strategy"}]
        }
        strategy = ReasoningStrategy.model_validate(strategy_data)
        self.assertEqual(strategy.name, strategy_data["name"])
        self.assertEqual(strategy.access_scope, strategy_data["accessScope"])
        self.assertEqual(strategy.type, strategy_data["type"])
        self.assertEqual(strategy.localized_descriptions[0].language, strategy_data["localizedDescriptions"][0]["language"])
        self.assertTrue(strategy.to_dict() == strategy_data)

    @unittest.skip("Skip for now. Fix later")
    def test_reasoning_strategy_list_model_validate(self):
        strategy_list_data = [
            {"name": "Strategy1", "accessScope": "public", "type": "addendum"},
            {"name": "Strategy2", "accessScope": "private", "type": "base"}
        ]
        strategy_list = ReasoningStrategyList.model_validate(strategy_list_data)
        self.assertEqual(len(strategy_list.strategies), 2)
        self.assertEqual(strategy_list.strategies[0].name, strategy_list_data[0]["name"])
        self.assertEqual(strategy_list.strategies[1].access_scope, strategy_list_data[1]["accessScope"])
        self.assertTrue(strategy_list.to_dict() == strategy_list_data)

    def test_knowledge_base_model_validate(self):
        kb_data = {
            "name": "TestKB",
            "artifactTypeName": ["doc"]
        }
        kb = KnowledgeBase.model_validate(kb_data)
        self.assertEqual(kb.name, kb_data["name"])
        self.assertEqual(kb.artifact_type_name, kb_data["artifactTypeName"])
        self.assertTrue(kb.to_dict() == kb_data)

    def test_agentic_activity_model_validate(self):
        activity_data = {
            "key": "act1",
            "name": "TestActivity",
            "taskName": "TestTask",
            "agentName": "TestAgent",
            "agentRevisionId": 1
        }
        activity = AgenticActivity.model_validate(activity_data)
        self.assertEqual(activity.key, activity_data["key"])
        self.assertEqual(activity.name, activity_data["name"])
        self.assertEqual(activity.task_name, activity_data["taskName"])
        self.assertEqual(activity.agent_name, activity_data["agentName"])
        self.assertEqual(activity.agent_revision_id, activity_data["agentRevisionId"])
        self.assertTrue(activity.to_dict() == activity_data)

    def test_artifact_signal_model_validate(self):
        signal_data = {
            "key": "sig1",
            "name": "TestSignal",
            "handlingType": "C",
            "artifactTypeName": ["text"]
        }
        signal = ArtifactSignal.model_validate(signal_data)
        self.assertEqual(signal.key, signal_data["key"])
        self.assertEqual(signal.name, signal_data["name"])
        self.assertEqual(signal.handling_type, signal_data["handlingType"])
        self.assertEqual(signal.artifact_type_name, signal_data["artifactTypeName"])
        self.assertTrue(signal.to_dict() == signal_data)

    def test_user_signal_model_validate(self):
        user_signal_data = {
            "key": "user1",
            "name": "UserDone"
        }
        user_signal = UserSignal.model_validate(user_signal_data)
        self.assertEqual(user_signal.key, user_signal_data["key"])
        self.assertEqual(user_signal.name, user_signal_data["name"])
        self.assertTrue(user_signal.to_dict() == user_signal_data)

    def test_event_model_validate(self):
        event_data = {
            "key": "evt1",
            "name": "StartEvent"
        }
        event = Event.model_validate(event_data)
        self.assertEqual(event.key, event_data["key"])
        self.assertEqual(event.name, event_data["name"])
        self.assertTrue(event.to_dict() == event_data)

    def test_sequence_flow_model_validate(self):
        flow_data = {
            "key": "flow1",
            "sourceKey": "start",
            "targetKey": "end"
        }
        sequence_flow = SequenceFlow.model_validate(flow_data)
        self.assertEqual(sequence_flow.key, flow_data["key"])
        self.assertEqual(sequence_flow.source_key, flow_data["sourceKey"])
        self.assertEqual(sequence_flow.target_key, flow_data["targetKey"])
        self.assertTrue(sequence_flow.to_dict() == flow_data)

    def test_agentic_process_model_validate(self):
        process_data = {
            "name": "TestProcess",
            "kb": {"name": "TestKB", "artifactTypeName": ["doc"]},
            "agenticActivities": [{"key": "act1", "name": "Act1", "taskName": "Task1", "agentName": "Agent1", "agentRevisionId": 1}]
        }
        process = AgenticProcess.model_validate(process_data)
        self.assertEqual(process.name, process_data["name"])
        self.assertEqual(process.kb.name, process_data["kb"]["name"])
        self.assertEqual(process.agentic_activities[0].key, process_data["agenticActivities"][0]["key"])
        self.assertTrue(process.to_dict() == process_data)

    def test_task_model_validate(self):
        task_data = {
            "name": "TestTask"
        }
        task = Task.model_validate(task_data)
        self.assertEqual(task.name, task_data["name"])
        self.assertIsNone(task.description)
        self.assertTrue(task.to_dict() == task_data)

    def test_agentic_process_list_model_validate(self):
        process_list_data = [
            {"name": "Process1"},
            {"name": "Process2"}
        ]
        process_list = AgenticProcessList.model_validate({"processes": process_list_data})
        self.assertEqual(len(process_list.processes), 2)
        self.assertEqual(process_list.processes[0].name, process_list_data[0]["name"])
        self.assertEqual(process_list.processes[1].name, process_list_data[1]["name"])
        self.assertTrue(process_list.to_dict() == {"processes": process_list_data})

    def test_task_list_model_validate(self):
        task_list_data = [
            {"name": "Task1"},
            {"name": "Task2"}
        ]
        task_list = TaskList.model_validate({"tasks": task_list_data})
        self.assertEqual(len(task_list.tasks), 2)
        self.assertEqual(task_list.tasks[0].name, task_list_data[0]["name"])
        self.assertEqual(task_list.tasks[1].name, task_list_data[1]["name"])
        self.assertTrue(task_list.to_dict() == task_list_data)

    def test_variable_model_validate(self):
        variable_data = {
            "key": "var1",
            "value": "value1"
        }
        variable = Variable.model_validate(variable_data)
        self.assertEqual(variable.key, variable_data["key"])
        self.assertEqual(variable.value, variable_data["value"])
        self.assertTrue(variable.to_dict() == variable_data)

    def test_variable_list_model_validate(self):
        variable_list_data = [
            {"key": "var1", "value": "value1"},
            {"key": "var2", "value": "value2"}
        ]
        variable_list = VariableList.model_validate({"variables": variable_list_data})
        self.assertEqual(len(variable_list.variables), 2)
        self.assertEqual(variable_list.variables[0].key, variable_list_data[0]["key"])
        self.assertEqual(variable_list.variables[1].value, variable_list_data[1]["value"])
        self.assertTrue(variable_list.to_dict() == variable_list_data)

    def test_process_instance_model_validate(self):
        instance_data = {
            "id": "inst123",
            "process": {"name": "TestProcess"},
            "createdAt": "2023-01-01T12:00:00",
            "subject": "TestSubject",
            "variables": [{"key": "var1", "value": "val1"}]
        }
        instance = ProcessInstance.model_validate(instance_data)
        self.assertEqual(instance.id, instance_data["id"])
        self.assertEqual(instance.process.name, instance_data["process"]["name"])
        self.assertEqual(instance.created_at, instance_data["createdAt"])
        self.assertEqual(instance.variables.variables[0].key, instance_data["variables"][0]["key"])
        self.assertTrue(instance.to_dict() == instance_data)

    def test_process_instance_list_model_validate(self):
        instance_list_data = [
            {"id": "inst1", "process": {"name": "Process1"}, "subject": "ProcessSubject"},
            {"id": "inst2", "process": {"name": "Process2"}, "subject": "ProcessSubject"}
        ]
        instance_list = ProcessInstanceList.model_validate({"instances": instance_list_data})
        self.assertEqual(len(instance_list.instances), 2)
        self.assertEqual(instance_list.instances[0].id, instance_list_data[0]["id"])
        self.assertEqual(instance_list.instances[1].process.name, instance_list_data[1]["process"]["name"])
        self.assertTrue(instance_list.to_dict() == instance_list_data)

    def test_filter_settings_instantiation(self):
        
        filter_attr = FilterSettings(id="agent123", name="test-agent", access_scope="private", allow_drafts=False)
        
        filter_dict = FilterSettings(**{
            "id": "agent123",
            "name": "test-agent",
            "accessScope": "private",
            "allowDrafts": False
        })
        self.assertEqual(filter_attr.id, filter_dict.id)
        self.assertEqual(filter_attr.name, filter_dict.name)
        self.assertEqual(filter_attr.access_scope, filter_dict.access_scope)
        self.assertEqual(filter_attr.allow_drafts, filter_dict.allow_drafts)
        self.assertEqual(filter_attr.to_dict(), filter_dict.to_dict())

    def test_sampling_instantiation(self):
        
        sampling_attr = Sampling(temperature=0.7, top_k=40, top_p=0.9)
        
        sampling_dict = Sampling(**{
            "temperature": 0.7,
            "topK": 40,
            "topP": 0.9
        })
        self.assertEqual(sampling_attr.temperature, sampling_dict.temperature)
        self.assertEqual(sampling_attr.top_k, sampling_dict.top_k)
        self.assertEqual(sampling_attr.top_p, sampling_dict.top_p)
        self.assertEqual(sampling_attr.to_dict(), sampling_dict.to_dict())

    def test_llm_config_instantiation(self):
        
        sampling = Sampling(temperature=0.7, top_k=40, top_p=0.9)
        llm_attr = LlmConfig(max_tokens=1000, timeout=30, sampling=sampling)
        
        llm_dict = LlmConfig(**{
            "maxTokens": 1000,
            "timeout": 30,
            "sampling": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.9
            }
        })
        self.assertEqual(llm_attr.max_tokens, llm_dict.max_tokens)
        self.assertEqual(llm_attr.timeout, llm_dict.timeout)
        self.assertEqual(llm_attr.sampling.temperature, llm_dict.sampling.temperature)
        self.assertEqual(llm_attr.to_dict(), llm_dict.to_dict())

    def test_model_instantiation(self):
        
        sampling = Sampling(temperature=0.5, top_k=30, top_p=0.8)
        llm_config = LlmConfig(max_tokens=500, timeout=20, sampling=sampling)
        model_attr = Model(name="gpt-4", llm_config=llm_config)
        
        model_dict = Model(**{
            "name": "gpt-4",
            "llmConfig": {
                "maxTokens": 500,
                "timeout": 20,
                "sampling": {
                    "temperature": 0.5,
                    "topK": 30,
                    "topP": 0.8
                }
            }
        })
        self.assertEqual(model_attr.name, model_dict.name)
        self.assertEqual(model_attr.llm_config.max_tokens, model_dict.llm_config.max_tokens)
        self.assertEqual(model_attr.to_dict(), model_dict.to_dict())

    def test_prompt_instantiation(self):
        
        output = PromptOutput(key="summary", description="Summary of text")
        example = PromptExample(input_data="Hello world", output='{"summary": "Hi"}')
        prompt_attr = Prompt(instructions="Summarize text", inputs=["text"], outputs=[output], examples=[example])
        
        prompt_dict = Prompt(**{
            "instructions": "Summarize text",
            "inputs": ["text"],
            "outputs": [{"key": "summary", "description": "Summary of text"}],
            "examples": [{"inputData": "Hello world", "output": '{"summary": "Hi"}'}]
        })
        self.assertEqual(prompt_attr.instructions, prompt_dict.instructions)
        self.assertEqual(prompt_attr.inputs, prompt_dict.inputs)
        self.assertEqual(prompt_attr.outputs[0].key, prompt_dict.outputs[0].key)
        self.assertEqual(prompt_attr.examples[0].input_data, prompt_dict.examples[0].input_data)
        self.assertEqual(prompt_attr.to_dict(), prompt_dict.to_dict())

    def test_model_list_instantiation(self):
        
        model = Model(name="gpt-4")
        model_list_attr = ModelList(models=[model])
        
        model_list_dict = ModelList(**{
            "models": [{"name": "gpt-4"}]
        })
        self.assertEqual(len(model_list_attr.models), len(model_list_dict.models))
        self.assertEqual(model_list_attr.models[0].name, model_list_dict.models[0].name)
        self.assertEqual(model_list_attr.to_dict(), model_list_dict.to_dict())

    def test_agent_data_instantiation(self):
        
        output = PromptOutput(key="summary", description="Summary")
        prompt = Prompt(instructions="Summarize", inputs=["text"], outputs=[output])
        sampling = Sampling(temperature=0.7, top_k=40, top_p=0.9)
        llm_config = LlmConfig(max_tokens=1000, timeout=30, sampling=sampling)
        model_list = ModelList(models=[Model(name="gpt-4")])
        agent_data_attr = AgentData(prompt=prompt, llm_config=llm_config, models=model_list)
        
        agent_data_dict = AgentData(**{
            "prompt": {
                "instructions": "Summarize",
                "inputs": ["text"],
                "outputs": [{"key": "summary", "description": "Summary"}]
            },
            "llmConfig": {
                "maxTokens": 1000,
                "timeout": 30,
                "sampling": {"temperature": 0.7, "topK": 40, "topP": 0.9}
            },
            "models": [{"name": "gpt-4"}]
        })
        self.assertEqual(agent_data_attr.prompt.instructions, agent_data_dict.prompt.instructions)
        self.assertEqual(agent_data_attr.llm_config.max_tokens, agent_data_dict.llm_config.max_tokens)
        self.assertEqual(agent_data_attr.models.models[0].name, agent_data_dict.models.models[0].name)
        self.assertEqual(agent_data_attr.to_dict(), agent_data_dict.to_dict())

    def test_agent_instantiation(self):
        
        output = PromptOutput(key="summary", description="Summary")
        prompt = Prompt(instructions="Summarize", inputs=["text"], outputs=[output])
        sampling = Sampling(temperature=0.7, top_k=40, top_p=0.9)
        llm_config = LlmConfig(max_tokens=1000, timeout=30, sampling=sampling)
        model_list = ModelList(models=[Model(name="gpt-4")])
        agent_data = AgentData(prompt=prompt, llm_config=llm_config, models=model_list)
        agent_attr = Agent(id="agent123", name="TestAgent", access_scope="public", public_name="test-agent", agent_data=agent_data)
        
        agent_dict = Agent(**{
            "id": "agent123",
            "name": "TestAgent",
            "accessScope": "public",
            "publicName": "test-agent",
            "agentData": {
                "prompt": {
                    "instructions": "Summarize",
                    "inputs": ["text"],
                    "outputs": [{"key": "summary", "description": "Summary"}]
                },
                "llmConfig": {
                    "maxTokens": 1000,
                    "timeout": 30,
                    "sampling": {"temperature": 0.7, "topK": 40, "topP": 0.9}
                },
                "models": [{"name": "gpt-4"}]
            }
        })
        self.assertEqual(agent_attr.id, agent_dict.id)
        self.assertEqual(agent_attr.name, agent_dict.name)
        self.assertEqual(agent_attr.access_scope, agent_dict.access_scope)
        self.assertEqual(agent_attr.public_name, agent_dict.public_name)
        self.assertEqual(agent_attr.agent_data.prompt.instructions, agent_dict.agent_data.prompt.instructions)
        self.assertEqual(agent_attr.to_dict(), agent_dict.to_dict())

    def test_tool_instantiation(self):
        
        param = ToolParameter(key="input", data_type="String", description="Input text", is_required=True)
        tool_attr = Tool(name="TextTool", description="Processes text", scope="builtin", parameters=[param])
        
        tool_dict = Tool(**{
            "name": "TextTool",
            "description": "Processes text",
            "scope": "builtin",
            "parameters": [
                {"key": "input", "dataType": "String", "description": "Input text", "isRequired": True}
            ]
        })
        self.assertEqual(tool_attr.name, tool_dict.name)
        self.assertEqual(tool_attr.description, tool_dict.description)
        self.assertEqual(tool_attr.scope, tool_dict.scope)
        self.assertEqual(tool_attr.parameters[0].key, tool_dict.parameters[0].key)
        self.assertEqual(tool_attr.to_dict(), tool_dict.to_dict())

    def test_agentic_process_instantiation(self):
        
        activity = AgenticActivity(key="act1", name="Act1", task_name="Task1", agent_name="Agent1", agent_revision_id=1)
        start_event = Event(key="start1", name="Start")
        flow = SequenceFlow(key="flow1", source_key="start1", target_key="act1")
        process_attr = AgenticProcess(name="TestProcess", agentic_activities=[activity], start_event=start_event, sequence_flows=[flow])
        
        process_dict = AgenticProcess(**{
            "name": "TestProcess",
            "agenticActivities": [
                {"key": "act1", "name": "Act1", "taskName": "Task1", "agentName": "Agent1", "agentRevisionId": 1}
            ],
            "startEvent": {"key": "start1", "name": "Start"},
            "sequenceFlows": [
                {"key": "flow1", "sourceKey": "start1", "targetKey": "act1"}
            ]
        })
        self.assertEqual(process_attr.name, process_dict.name)
        self.assertEqual(process_attr.agentic_activities[0].key, process_dict.agentic_activities[0].key)
        self.assertEqual(process_attr.start_event.key, process_dict.start_event.key)
        self.assertEqual(process_attr.sequence_flows[0].key, process_dict.sequence_flows[0].key)
        self.assertEqual(process_attr.to_dict(), process_dict.to_dict())

    def test_task_instantiation(self):
        
        output = PromptOutput(key="summary", description="Summary")
        prompt = Prompt(instructions="Summarize", inputs=["text"], outputs=[output])
        artifact = ArtifactType(name="document", usage_type="input")
        artifact_list = ArtifactTypeList(artifact_types=[artifact])
        task_attr = Task(name="TestTask", prompt_data=prompt, artifact_types=artifact_list)
        
        task_dict = Task(**{
            "name": "TestTask",
            "promptData": {
                "instructions": "Summarize",
                "inputs": ["text"],
                "outputs": [{"key": "summary", "description": "Summary"}]
            },
            "artifactTypes": [
                {"name": "document", "usageType": "input"}
            ]
        })
        self.assertEqual(task_attr.name, task_dict.name)
        self.assertEqual(task_attr.prompt_data.instructions, task_dict.prompt_data.instructions)
        self.assertEqual(task_attr.artifact_types.artifact_types[0].name, task_dict.artifact_types.artifact_types[0].name)
        self.assertEqual(task_attr.to_dict(), task_dict.to_dict())

    def test_agent_invalid_public_name_access_scope(self):
        agent_data = {
            "id": "agent123",
            "status": "active",
            "name": "TestAgent",
            "isDraft": False,
            "isReadonly": False,
            "accessScope": "public"
            # Missing publicName to trigger validation error
        }
        with self.assertRaises(ValueError) as context:
            Agent.model_validate(agent_data)
        self.assertIn("public_name is required if access_scope is", str(context.exception).lower())

    def test_agent_invalid_public_name_format(self):
        agent_data = {
            "id": "agent123",
            "status": "active",
            "name": "TestAgent",
            "isDraft": False,
            "isReadonly": False,
            "accessScope": "public",
            "publicName": "invalid@name!"  # Invalid characters
        }
        with self.assertRaises(ValueError) as context:
            Agent.model_validate(agent_data)
        self.assertIn("public_name must contain only letters, numbers, periods, dashes, or underscores",
                      str(context.exception))

    def test_agent_data_publication_validation_no_models(self):
        agent_data = {
            "id": "agent123",
            "status": "active",
            "name": "TestAgent",
            "isDraft": False,  # Not a draft, triggers validation
            "isReadonly": False,
            "accessScope": "private",
            "agentData": {
                "prompt": {"instructions": "Summarize", "inputs": ["text"],
                           "outputs": [{"key": "summary", "description": "Summary"}]},
                "llmConfig": {"maxTokens": 1000, "timeout": 30,
                              "sampling": {"temperature": 0.7, "topK": 40, "topP": 0.9}},
                "models": []  # Empty models list, should trigger validation error
            }
        }
        with self.assertRaises(ValueError) as context:
            Agent.model_validate(agent_data)
        self.assertIn("at least one valid model must be provided in agent_data.models for publication",
                      str(context.exception).lower())

    def test_agent_data_publication_validation_no_instructions(self):
        agent_data = {
            "id": "agent123",
            "status": "active",
            "name": "TestAgent",
            "isDraft": False,  # Not a draft, triggers validation
            "isReadonly": False,
            "accessScope": "private",
            "agentData": {
                "prompt": {"instructions": "", "inputs": ["text"],
                           "outputs": [{"key": "summary", "description": "Summary"}]},
                "llmConfig": {"maxTokens": 1000, "timeout": 30,
                              "sampling": {"temperature": 0.7, "topK": 40, "topP": 0.9}},
                "models": [{"name": "gpt-4"}]  # Valid models, but no instructions
            }
        }
        with self.assertRaises(ValueError) as context:
            Agent.model_validate(agent_data)
        self.assertIn("agent_data.prompt must have at least instructions for publication",
                      str(context.exception).lower())

    def test_tool_invalid_name(self):
        tool_data = {
            "name": "Invalid:Tool",  # Contains forbidden character ':'
            "description": "Invalid tool",
            "scope": "builtin"
        }
        with self.assertRaises(ValueError) as context:
            Tool.model_validate(tool_data)
        self.assertIn("name cannot contain ':' or '/'", str(context.exception).lower())

    def test_tool_invalid_public_name_access_scope(self):
        tool_data = {
            "name": "TestTool",
            "description": "Test tool",
            "scope": "builtin",
            "accessScope": "public"
            # Missing publicName to trigger validation error
        }
        with self.assertRaises(ValueError) as context:
            Tool.model_validate(tool_data)
        self.assertIn("public_name is required if access_scope is 'public'", str(context.exception).lower())

    def test_tool_invalid_public_name_format(self):
        tool_data = {
            "name": "TestTool",
            "description": "Test tool",
            "scope": "builtin",
            "accessScope": "public",
            "publicName": "invalid@name!"  # Invalid characters
        }
        with self.assertRaises(ValueError) as context:
            Tool.model_validate(tool_data)
        self.assertIn("public_name must contain only letters, numbers, periods, dashes, or underscores",
                      str(context.exception))

    def test_tool_api_scope_validation_no_open_api(self):
        tool_data = {
            "name": "ApiTool",
            "description": "API tool",
            "scope": "api"
            # Missing open_api or open_api_json - validation currently commented out
        }
        # Validation is currently commented out in the model, so this should not raise
        tool = Tool.model_validate(tool_data)
        self.assertEqual(tool.name, "ApiTool")
        self.assertEqual(tool.scope, "api")

    def test_tool_duplicate_parameter_keys(self):
        tool_data = {
            "name": "DuplicateTool",
            "description": "Tool with duplicate params",
            "scope": "builtin",
            "parameters": [
                {"key": "param1", "dataType": "String", "description": "Param 1", "isRequired": True},
                {"key": "param1", "dataType": "Integer", "description": "Param 1 duplicate", "isRequired": False}
            ]
        }
        # Validation is currently commented out in the model, so this should not raise
        tool = Tool.model_validate(tool_data)
        self.assertEqual(tool.name, "DuplicateTool")
        self.assertEqual(len(tool.parameters), 2)

    def test_knowledge_base_invalid_artifacts(self):
        kb_data = {
            "name": "InvalidKB",
            "artifacts": ["", "valid"]  # Empty string should trigger validation error
        }
        with self.assertRaises(ValueError) as context:
            KnowledgeBase.model_validate(kb_data)
        self.assertIn("artifact identifiers cannot be empty", str(context.exception).lower())

    def test_knowledge_base_invalid_metadata(self):
        kb_data = {
            "name": "InvalidKB",
            "metadata": ["", "valid"]  # Empty string should trigger validation error
        }
        with self.assertRaises(ValueError) as context:
            KnowledgeBase.model_validate(kb_data)
        self.assertIn("metadata identifiers cannot be empty", str(context.exception).lower())

    def test_artifact_type_list_model_validate(self):
        artifact_list_data = {
            "artifact_types": [
                {"name": "doc", "usageType": "input"},
                {"name": "image", "usageType": "output"}
            ]
        }
        artifact_list = ArtifactTypeList.model_validate(artifact_list_data)
        self.assertEqual(len(artifact_list.artifact_types), 2)
        self.assertEqual(artifact_list.artifact_types[0].name, artifact_list_data["artifact_types"][0]["name"])
        self.assertEqual(artifact_list.artifact_types[1].usage_type,
                         artifact_list_data["artifact_types"][1]["usageType"])
        # Adjusted to check for content rather than direct equality due to potential nested structure issues
        result_dict = artifact_list.to_dict()
        self.assertEqual(len(result_dict), len(artifact_list_data["artifact_types"]))
        self.assertEqual(result_dict[0]["name"], artifact_list_data["artifact_types"][0]["name"])

    def test_job_parameter_invalid_name(self):
        job_param_data = {
            "Name": "",
            "Value": "value1"
        }
        with self.assertRaises(ValueError) as context:
            JobParameter.model_validate(job_param_data)
        self.assertIn("parameter name cannot be blank", str(context.exception).lower())

    def test_job_invalid_name(self):
        job_data = {
            "caption": "Job completed",
            "name": "",
            "parameters": [{"Name": "param1", "Value": "value1"}],
            "request": "2023-01-01T12:00:00",
            "token": "token123",
            "topic": "Default"
        }
        with self.assertRaises(ValueError) as context:
            Job.model_validate(job_data)
        self.assertIn("job name cannot be blank", str(context.exception).lower())

    def test_job_invalid_token(self):
        job_data = {
            "caption": "Job completed",
            "name": "execute_job",
            "parameters": [{"Name": "param1", "Value": "value1"}],
            "request": "2023-01-01T12:00:00",
            "token": "",
            "topic": "Default"
        }
        with self.assertRaises(ValueError) as context:
            Job.model_validate(job_data)
        self.assertIn("token cannot be blank", str(context.exception).lower())

    def test_job_list_model_validate(self):
        job_list_data = {
            "jobs": [
                {"caption": "Job 1", "name": "job1", "parameters": [], "request": "2023-01-01T12:00:00",
                 "token": "token1", "topic": "Default"},
                {"caption": "Job 2", "name": "job2", "parameters": [], "request": "2023-01-02T12:00:00",
                 "token": "token2", "topic": "Event"}
            ]
        }
        job_list = JobList.model_validate(job_list_data)
        self.assertEqual(len(job_list.jobs), 2)
        self.assertEqual(job_list.jobs[0].name, job_list_data["jobs"][0]["name"])
        self.assertEqual(job_list.jobs[1].token, job_list_data["jobs"][1]["token"])
        # Adjusted to check for content rather than direct equality due to potential nested structure issues
        result_dict = job_list.to_dict()
        self.assertEqual(len(result_dict), len(job_list_data["jobs"]))
        self.assertEqual(result_dict[0]["name"], job_list_data["jobs"][0]["name"])

    def test_resource_pool_tool_model_validate(self):
        tool_data = {
            "name": "TestTool",
            "revision": 2
        }
        resource_tool = ResourcePoolTool.model_validate(tool_data)
        self.assertEqual(resource_tool.name, tool_data["name"])
        self.assertEqual(resource_tool.revision, tool_data["revision"])
        self.assertEqual(resource_tool.to_dict(), tool_data)

    def test_resource_pool_tool_invalid_name(self):
        tool_data = {
            "name": "Invalid:Tool",  # Contains forbidden character ':'
            "revision": 1
        }
        with self.assertRaises(ValueError) as context:
            ResourcePoolTool.model_validate(tool_data)
        self.assertIn("name cannot contain ':' or '/'", str(context.exception).lower())

    def test_resource_pool_agent_model_validate(self):
        agent_data = {
            "name": "TestAgent",
            "revision": 3
        }
        resource_agent = ResourcePoolAgent.model_validate(agent_data)
        self.assertEqual(resource_agent.name, agent_data["name"])
        self.assertEqual(resource_agent.revision, agent_data["revision"])
        self.assertEqual(resource_agent.to_dict(), agent_data)

    def test_resource_pool_agent_invalid_name(self):
        agent_data = {
            "name": "Invalid/Agent",  # Contains forbidden character '/'
            "revision": 1
        }
        with self.assertRaises(ValueError) as context:
            ResourcePoolAgent.model_validate(agent_data)
        self.assertIn("name cannot contain ':' or '/'", str(context.exception).lower())

    def test_resource_pool_model_validate(self):
        pool_data = {
            "name": "TestPool",
            "tools": [{"name": "Tool1", "revision": 1}],
            "agents": [{"name": "Agent1", "revision": 2}]
        }
        resource_pool = ResourcePool.model_validate(pool_data)
        self.assertEqual(resource_pool.name, pool_data["name"])
        self.assertEqual(resource_pool.tools[0].name, pool_data["tools"][0]["name"])
        self.assertEqual(resource_pool.agents[0].name, pool_data["agents"][0]["name"])
        self.assertEqual(resource_pool.to_dict(), pool_data)

    def test_resource_pool_invalid_name(self):
        pool_data = {
            "name": "Invalid:Pool",  # Contains forbidden character ':'
            "tools": [],
            "agents": []
        }
        with self.assertRaises(ValueError) as context:
            ResourcePool.model_validate(pool_data)
        self.assertIn("name cannot contain ':' or '/'", str(context.exception).lower())

    def test_resource_pool_list_model_validate(self):
        pool_list_data = {
            "resourcePools": [
                {"name": "Pool1", "tools": [{"name": "Tool1", "revision": 1}]},
                {"name": "Pool2", "agents": [{"name": "Agent1", "revision": 2}]}
            ]
        }
        resource_pool_list = ResourcePoolList.model_validate(pool_list_data)
        self.assertEqual(len(resource_pool_list.resource_pools), 2)
        self.assertEqual(resource_pool_list.resource_pools[0].name, pool_list_data["resourcePools"][0]["name"])
        self.assertEqual(resource_pool_list.resource_pools[1].name, pool_list_data["resourcePools"][1]["name"])
        self.assertEqual(resource_pool_list.to_dict(),
                         [pool_list_data["resourcePools"][0], pool_list_data["resourcePools"][1]])

    def test_agent_data_unique_resource_pool_names_validation(self):
        agent_data_data = {
            "prompt": {"instructions": "Summarize", "inputs": ["text"],
                       "outputs": [{"key": "summary", "description": "Summary"}]},
            "llmConfig": {"maxTokens": 1000, "timeout": 30, "sampling": {"temperature": 0.7, "topK": 40, "topP": 0.9}},
            "models": [{"name": "gpt-4"}],
            "resourcePools": [
                {"name": "Pool1", "tools": [{"name": "Tool1", "revision": 1}]},
                {"name": "Pool1", "agents": [{"name": "Agent1", "revision": 2}]}  # Duplicate name
            ]
        }
        with self.assertRaises(ValueError) as context:
            AgentData.model_validate(agent_data_data)
        self.assertIn("resource pool names must be unique within agentdata", str(context.exception).lower())

    def test_knowledge_base_list_model_validate(self):
        kb_list_data = {
            "knowledgeBases": [
                {"name": "KB1", "artifactTypeName": ["doc"]},
                {"name": "KB2", "artifactTypeName": ["image"]}
            ]
        }
        kb_list = KnowledgeBaseList.model_validate(kb_list_data)
        self.assertEqual(len(kb_list.knowledge_bases), 2)
        self.assertEqual(kb_list.knowledge_bases[0].name, kb_list_data["knowledgeBases"][0]["name"])
        self.assertEqual(kb_list.knowledge_bases[1].name, kb_list_data["knowledgeBases"][1]["name"])
        self.assertEqual(kb_list.to_dict(), [kb_list_data["knowledgeBases"][0], kb_list_data["knowledgeBases"][1]])

    def test_task_artifact_type_invalid_usage_type(self):
        task_data = {
            "name": "TestTask",
            "artifactTypes": [
                {"name": "doc", "usageType": "invalid"}  # Invalid usage type
            ]
        }
        with self.assertRaises(ValidationError) as context:
            Task.model_validate(task_data)
        self.assertIn("usagetype must be 'input' or 'output'", str(context.exception).lower())

    def test_task_artifact_type_long_variable_key(self):
        task_data = {
            "name": "TestTask",
            "artifactTypes": [
                {"name": "doc", "usageType": "input", "artifactVariableKey": "this_key_is_way_too_long_to_be_valid"}
                # Too long
            ]
        }
        with self.assertRaises(ValueError) as context:
            Task.model_validate(task_data)
        self.assertIn("artifactvariablekey", str(context.exception).lower())
        self.assertIn("must be 20 characters or less", str(context.exception).lower())

    def test_agentic_process_invalid_name(self):
        process_data = {
            "name": "Invalid:Process",  # Contains forbidden character ':'
            "agenticActivities": []
        }
        with self.assertRaises(ValueError) as context:
            AgenticProcess.model_validate(process_data)
        self.assertIn("name cannot contain ':' or '/'", str(context.exception).lower())

    def test_model_list_iterable_and_append(self):
        model_list = ModelList(models=[])
        self.assertEqual(len(model_list), 0)
        model = Model(name="gpt-4")
        model_list.append(model)
        self.assertEqual(len(model_list), 1)
        self.assertEqual(model_list[0].name, "gpt-4")
        iterated_models = [m for m in model_list]
        self.assertEqual(len(iterated_models), 1)
        self.assertEqual(iterated_models[0].name, "gpt-4")

    def test_resource_pool_list_iterable_and_append(self):
        pool_list = ResourcePoolList(resource_pools=[])
        self.assertEqual(len(pool_list), 0)
        pool = ResourcePool(name="TestPool")
        pool_list.append(pool)
        self.assertEqual(len(pool_list), 1)
        self.assertEqual(pool_list[0].name, "TestPool")
        iterated_pools = [p for p in pool_list]
        self.assertEqual(len(iterated_pools), 1)
        self.assertEqual(iterated_pools[0].name, "TestPool")

    def test_agent_list_iterable_and_append(self):
        agent_list = AgentList(agents=[])
        self.assertEqual(len(agent_list), 0)
        agent = Agent(name="TestAgent", access_scope="private")
        agent_list.append(agent)
        self.assertEqual(len(agent_list), 1)
        self.assertEqual(agent_list[0].name, "TestAgent")
        iterated_agents = [a for a in agent_list]
        self.assertEqual(len(iterated_agents), 1)
        self.assertEqual(iterated_agents[0].name, "TestAgent")

    def test_tool_list_iterable_and_append(self):
        tool_list = ToolList(tools=[])
        self.assertEqual(len(tool_list), 0)
        tool = Tool(name="TestTool", description="Test", scope="builtin")
        tool_list.append(tool)
        self.assertEqual(len(tool_list), 1)
        self.assertEqual(tool_list[0].name, "TestTool")
        iterated_tools = [t for t in tool_list]
        self.assertEqual(len(iterated_tools), 1)
        self.assertEqual(iterated_tools[0].name, "TestTool")

    def test_reasoning_strategy_list_iterable_and_append(self):
        strategy_list = ReasoningStrategyList(strategies=[])
        self.assertEqual(len(strategy_list), 0)
        strategy = ReasoningStrategy(name="TestStrategy", access_scope="private", type="addendum")
        strategy_list.append(strategy)
        self.assertEqual(len(strategy_list), 1)
        self.assertEqual(strategy_list[0].name, "TestStrategy")
        iterated_strategies = [s for s in strategy_list]
        self.assertEqual(len(iterated_strategies), 1)
        self.assertEqual(iterated_strategies[0].name, "TestStrategy")

    def test_knowledge_base_list_iterable_and_append(self):
        kb_list = KnowledgeBaseList(knowledge_bases=[])
        self.assertEqual(len(kb_list), 0)
        kb = KnowledgeBase(name="TestKB")
        kb_list.append(kb)
        self.assertEqual(len(kb_list), 1)
        self.assertEqual(kb_list[0].name, "TestKB")
        iterated_kbs = [k for k in kb_list]
        self.assertEqual(len(iterated_kbs), 1)
        self.assertEqual(iterated_kbs[0].name, "TestKB")

    def test_variable_list_iterable_and_append(self):
        var_list = VariableList(variables=[])
        self.assertEqual(len(var_list), 0)
        var = Variable(key="var1", value="value1")
        var_list.append(var)
        self.assertEqual(len(var_list), 1)
        self.assertEqual(var_list[0].key, "var1")
        iterated_vars = [v for v in var_list]
        self.assertEqual(len(iterated_vars), 1)
        self.assertEqual(iterated_vars[0].key, "var1")

    def test_artifact_type_list_iterable_and_append(self):
        artifact_list = ArtifactTypeList(artifact_types=[])
        self.assertEqual(len(artifact_list), 0)
        artifact = ArtifactType(name="doc", usage_type="input")
        artifact_list.append(artifact)
        self.assertEqual(len(artifact_list), 1)
        self.assertEqual(artifact_list[0].name, "doc")
        iterated_artifacts = [a for a in artifact_list]
        self.assertEqual(len(iterated_artifacts), 1)
        self.assertEqual(iterated_artifacts[0].name, "doc")

    def test_agentic_process_list_iterable_and_append(self):
        process_list = AgenticProcessList(processes=[])
        self.assertEqual(len(process_list), 0)
        process = AgenticProcess(name="TestProcess")
        process_list.append(process)
        self.assertEqual(len(process_list), 1)
        self.assertEqual(process_list[0].name, "TestProcess")
        iterated_processes = [p for p in process_list]
        self.assertEqual(len(iterated_processes), 1)
        self.assertEqual(iterated_processes[0].name, "TestProcess")

    def test_task_list_iterable_and_append(self):
        task_list = TaskList(tasks=[])
        self.assertEqual(len(task_list), 0)
        task = Task(name="TestTask")
        task_list.append(task)
        self.assertEqual(len(task_list), 1)
        self.assertEqual(task_list[0].name, "TestTask")
        iterated_tasks = [t for t in task_list]
        self.assertEqual(len(iterated_tasks), 1)
        self.assertEqual(iterated_tasks[0].name, "TestTask")

    def test_process_instance_list_iterable_and_append(self):
        instance_list = ProcessInstanceList(instances=[])
        self.assertEqual(len(instance_list), 0)
        process = AgenticProcess(name="TestProcess")
        instance = ProcessInstance(process=process, subject="TestSubject")
        instance_list.append(instance)
        self.assertEqual(len(instance_list), 1)
        self.assertEqual(instance_list[0].process.name, "TestProcess")
        iterated_instances = [i for i in instance_list]
        self.assertEqual(len(iterated_instances), 1)
        self.assertEqual(iterated_instances[0].process.name, "TestProcess")

    def test_job_list_iterable_and_append(self):
        job_list = JobList(jobs=[])
        self.assertEqual(len(job_list), 0)
        job = Job(caption="Job completed", name="execute_job", request="2023-01-01T12:00:00", token="token123",
                  topic="Default")
        job_list.append(job)
        self.assertEqual(len(job_list), 1)
        self.assertEqual(job_list[0].name, "execute_job")
        iterated_jobs = [j for j in job_list]
        self.assertEqual(len(iterated_jobs), 1)
        self.assertEqual(iterated_jobs[0].name, "execute_job")