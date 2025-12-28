import unittest
from unittest.mock import MagicMock, patch
from pygeai.core.common.exceptions import APIError, MissingRequirementException
from pygeai.lab.models import FilterSettings, Agent, AgentList, SharingLink, Tool, ToolList, ToolParameter, \
    ReasoningStrategyList, ReasoningStrategy, AgenticProcess, AgenticProcessList, ProcessInstanceList, Task, TaskList, \
    ProcessInstance, VariableList, KnowledgeBase, KnowledgeBaseList, JobList, Prompt, LlmConfig, Sampling, ModelList, \
    Model, AgentData, AgenticActivity, Event, SequenceFlow, Variable, ArtifactSignal, UserSignal, ArtifactTypeList, \
    ArtifactType, JobParameter
from pygeai.lab.managers import AILabManager


class TestAILabManager(unittest.TestCase):
    """
    python -m unittest pygeai.tests.lab.test_managers.TestAILabManager
    """

    def setUp(self):
        self.manager = AILabManager(api_key="test_key", base_url="test_url", alias="test_alias", project_id="test_project")
        self.agent_id = "test_agent"
        self.tool_id = "test_tool"
        self.process_id = "test_process"
        self.instance_id = "test_instance"
        self.task_id = "test_task"
        self.kb_id = "test_kb"
        self.revision = "1"
        self.filter_settings = FilterSettings()

    @patch('pygeai.lab.agents.clients.AgentClient.list_agents')
    @patch('pygeai.lab.agents.mappers.AgentMapper.map_to_agent_list')
    def test_get_agent_list_success(self, mock_map_to_agent_list, mock_list_agents):
        mock_list_agents.return_value = {"data": "test_data"}
        mock_map_to_agent_list.return_value = AgentList(agents=[])

        result = self.manager.get_agent_list(self.filter_settings)

        mock_list_agents.assert_called_once()
        mock_map_to_agent_list.assert_called_once_with({"data": "test_data"})
        self.assertIsInstance(result, AgentList)

    @patch('pygeai.lab.agents.clients.AgentClient.list_agents')
    def test_get_agent_list_api_error(self, mock_list_agents):
        mock_list_agents.return_value = {"error": {"id": 1, "message": "API error"}}

        with self.assertRaises(APIError):
            self.manager.get_agent_list(self.filter_settings)

    @patch('pygeai.lab.agents.clients.AgentClient.create_agent')
    @patch('pygeai.lab.agents.mappers.AgentMapper.map_to_agent')
    def test_create_agent_success(self, mock_map_to_agent, mock_create_agent):
        mock_create_agent.return_value = {"data": "test_data"}
        mock_map_to_agent.return_value = Agent(id=self.agent_id, name="test_agent")
        agent = Agent(name="test_agent")

        result = self.manager.create_agent(agent, automatic_publish=False)

        mock_create_agent.assert_called_once()
        mock_map_to_agent.assert_called_once_with({"data": "test_data"})
        self.assertIsInstance(result, Agent)

    @patch('pygeai.lab.agents.clients.AgentClient.update_agent')
    @patch('pygeai.lab.agents.mappers.AgentMapper.map_to_agent')
    def test_update_agent_success(self, mock_map_to_agent, mock_update_agent):
        mock_update_agent.return_value = {"data": "test_data"}
        mock_map_to_agent.return_value = Agent(id=self.agent_id, name="test_agent")
        agent = Agent(id=self.agent_id, name="test_agent")

        result = self.manager.update_agent(agent, automatic_publish=False, upsert=False)

        mock_update_agent.assert_called_once()
        mock_map_to_agent.assert_called_once_with({"data": "test_data"})
        self.assertIsInstance(result, Agent)

    @patch('pygeai.lab.agents.clients.AgentClient.get_agent')
    @patch('pygeai.lab.agents.mappers.AgentMapper.map_to_agent')
    def test_get_agent_success(self, mock_map_to_agent, mock_get_agent):
        mock_get_agent.return_value = {"data": "test_data"}
        mock_map_to_agent.return_value = Agent(id=self.agent_id, name="test_agent")

        result = self.manager.get_agent(self.agent_id, self.filter_settings)

        mock_get_agent.assert_called_once()
        mock_map_to_agent.assert_called_once_with({"data": "test_data"})
        self.assertIsInstance(result, Agent)

    @patch('pygeai.lab.agents.clients.AgentClient.create_sharing_link')
    @patch('pygeai.lab.agents.mappers.AgentMapper.map_to_sharing_link')
    def test_create_sharing_link_success(self, mock_map_to_sharing_link, mock_create_sharing_link):
        mock_create_sharing_link.return_value = {"data": "test_data"}
        mock_map_to_sharing_link.return_value = SharingLink(agent_id="test_agent", api_token="test_token", shared_link="test_link")

        result = self.manager.create_sharing_link(self.agent_id)

        mock_create_sharing_link.assert_called_once()
        mock_map_to_sharing_link.assert_called_once_with({"data": "test_data"})
        self.assertIsInstance(result, SharingLink)

    @patch('pygeai.lab.agents.clients.AgentClient.publish_agent_revision')
    @patch('pygeai.lab.agents.mappers.AgentMapper.map_to_agent')
    def test_publish_agent_revision_success(self, mock_map_to_agent, mock_publish_agent_revision):
        mock_publish_agent_revision.return_value = {"data": "test_data"}
        mock_map_to_agent.return_value = Agent(id=self.agent_id, name="test_agent")

        result = self.manager.publish_agent_revision(self.agent_id, self.revision)

        mock_publish_agent_revision.assert_called_once()
        mock_map_to_agent.assert_called_once_with({"data": "test_data"})
        self.assertIsInstance(result, Agent)

    @patch('pygeai.lab.agents.clients.AgentClient.delete_agent')
    @patch('pygeai.core.base.mappers.ResponseMapper.map_to_empty_response')
    def test_delete_agent_success(self, mock_map_to_empty_response, mock_delete_agent):
        mock_delete_agent.return_value = {"data": "test_data"}
        mock_map_to_empty_response.return_value = {"status": "success"}

        result = self.manager.delete_agent(self.agent_id)

        mock_delete_agent.assert_called_once()
        mock_map_to_empty_response.assert_called_once()
        self.assertIsInstance(result, dict)

    @patch('pygeai.lab.tools.clients.ToolClient.create_tool')
    @patch('pygeai.lab.tools.mappers.ToolMapper.map_to_tool')
    def test_create_tool_success(self, mock_map_to_tool, mock_create_tool):
        mock_create_tool.return_value = {"data": "test_data"}
        mock_map_to_tool.return_value = Tool(id=self.tool_id, name="test_tool", description="test_desc")
        tool = Tool(name="test_tool", description="test_desc")

        result = self.manager.create_tool(tool, automatic_publish=False)

        mock_create_tool.assert_called_once()
        mock_map_to_tool.assert_called_once_with({"data": "test_data"})
        self.assertIsInstance(result, Tool)

    @patch('pygeai.lab.tools.clients.ToolClient.update_tool')
    @patch('pygeai.lab.tools.mappers.ToolMapper.map_to_tool')
    def test_update_tool_success(self, mock_map_to_tool, mock_update_tool):
        mock_update_tool.return_value = {"data": "test_data"}
        mock_map_to_tool.return_value = Tool(id=self.tool_id, name="test_tool", description="test_desc")
        tool = Tool(id=self.tool_id, name="test_tool", description="test_desc")

        result = self.manager.update_tool(tool, automatic_publish=False, upsert=False)

        mock_update_tool.assert_called_once()
        mock_map_to_tool.assert_called_once_with({"data": "test_data"})
        self.assertIsInstance(result, Tool)

    @patch('pygeai.lab.tools.clients.ToolClient.get_tool')
    @patch('pygeai.lab.tools.mappers.ToolMapper.map_to_tool')
    def test_get_tool_success(self, mock_map_to_tool, mock_get_tool):
        mock_get_tool.return_value = {"data": "test_data"}
        mock_map_to_tool.return_value = Tool(id=self.tool_id, name="test_tool", description="test_desc")

        result = self.manager.get_tool(self.tool_id, self.filter_settings)

        mock_get_tool.assert_called_once()
        mock_map_to_tool.assert_called_once_with({"data": "test_data"})
        self.assertIsInstance(result, Tool)

    @patch('pygeai.lab.tools.clients.ToolClient.delete_tool')
    @patch('pygeai.core.base.mappers.ResponseMapper.map_to_empty_response')
    def test_delete_tool_success(self, mock_map_to_empty_response, mock_delete_tool):
        mock_delete_tool.return_value = {"data": "test_data"}
        mock_map_to_empty_response.return_value = {"status": "success"}

        result = self.manager.delete_tool(tool_id=self.tool_id)

        mock_delete_tool.assert_called_once()
        mock_map_to_empty_response.assert_called_once()
        self.assertIsInstance(result, dict)

    @patch('pygeai.lab.tools.clients.ToolClient.list_tools')
    @patch('pygeai.lab.tools.mappers.ToolMapper.map_to_tool_list')
    def test_list_tools_success(self, mock_map_to_tool_list, mock_list_tools):
        mock_list_tools.return_value = {"data": "test_data"}
        mock_map_to_tool_list.return_value = ToolList(tools=[])

        result = self.manager.list_tools(self.filter_settings)

        mock_list_tools.assert_called_once()
        mock_map_to_tool_list.assert_called_once_with({"data": "test_data"})
        self.assertIsInstance(result, ToolList)

    @patch('pygeai.lab.tools.clients.ToolClient.publish_tool_revision')
    @patch('pygeai.lab.tools.mappers.ToolMapper.map_to_tool')
    def test_publish_tool_revision_success(self, mock_map_to_tool, mock_publish_tool_revision):
        mock_publish_tool_revision.return_value = {"data": "test_data"}
        mock_map_to_tool.return_value = Tool(id=self.tool_id, name="test_tool", description="test_desc")

        result = self.manager.publish_tool_revision(self.tool_id, self.revision)

        mock_publish_tool_revision.assert_called_once()
        mock_map_to_tool.assert_called_once_with({"data": "test_data"})
        self.assertIsInstance(result, Tool)

    @patch('pygeai.lab.tools.clients.ToolClient.get_parameter')
    @patch('pygeai.lab.tools.mappers.ToolMapper.map_to_parameter_list')
    def test_get_parameter_success(self, mock_map_to_parameter_list, mock_get_parameter):
        mock_get_parameter.return_value = {"data": "test_data"}
        mock_map_to_parameter_list.return_value = [ToolParameter(key="test_key", data_type="String", description="test_desc", is_required=True)]

        result = self.manager.get_parameter(tool_id=self.tool_id, filter_settings=self.filter_settings)

        mock_get_parameter.assert_called_once()
        mock_map_to_parameter_list.assert_called_once_with({"data": "test_data"})
        self.assertIsInstance(result, list)

    @patch('pygeai.lab.tools.clients.ToolClient.set_parameter')
    def test_set_parameter_success(self, mock_set_parameter):
        mock_set_parameter.return_value = {"status": "success"}
        parameters = [ToolParameter(key="test_key", data_type="String", description="test_desc", is_required=True)]

        result = self.manager.set_parameter(tool_id=self.tool_id, parameters=parameters)

        mock_set_parameter.assert_called_once()
        self.assertIsNotNone(result)

    @patch('pygeai.lab.strategies.clients.ReasoningStrategyClient.list_reasoning_strategies')
    @patch('pygeai.lab.strategies.mappers.ReasoningStrategyMapper.map_to_reasoning_strategy_list')
    def test_list_reasoning_strategies_success(self, mock_map_to_strategy_list, mock_list_strategies):
        mock_list_strategies.return_value = {"data": "test_data"}
        mock_map_to_strategy_list.return_value = ReasoningStrategyList(strategies=[])

        result = self.manager.list_reasoning_strategies(self.filter_settings)

        mock_list_strategies.assert_called_once()
        mock_map_to_strategy_list.assert_called_once_with({"data": "test_data"})
        self.assertIsInstance(result, ReasoningStrategyList)

    @patch('pygeai.lab.strategies.clients.ReasoningStrategyClient.create_reasoning_strategy')
    @patch('pygeai.lab.strategies.mappers.ReasoningStrategyMapper.map_to_reasoning_strategy')
    def test_create_reasoning_strategy_success(self, mock_map_to_strategy, mock_create_strategy):
        mock_create_strategy.return_value = {"data": "test_data"}
        mock_map_to_strategy.return_value = ReasoningStrategy(id="test_strategy", name="test_strategy", access_scope="private", type="addendum")
        strategy = ReasoningStrategy(name="test_strategy", access_scope="private", type="addendum", localized_descriptions=[])

        result = self.manager.create_reasoning_strategy(strategy, automatic_publish=False)

        mock_create_strategy.assert_called_once()
        mock_map_to_strategy.assert_called_once_with({"data": "test_data"})
        self.assertIsInstance(result, ReasoningStrategy)

    @patch('pygeai.lab.strategies.clients.ReasoningStrategyClient.update_reasoning_strategy')
    @patch('pygeai.lab.strategies.mappers.ReasoningStrategyMapper.map_to_reasoning_strategy')
    def test_update_reasoning_strategy_success(self, mock_map_to_strategy, mock_update_strategy):
        mock_update_strategy.return_value = {"data": "test_data"}
        mock_map_to_strategy.return_value = ReasoningStrategy(id="test_strategy", name="test_strategy", access_scope="private", type="addendum")
        strategy = ReasoningStrategy(id="test_strategy", name="test_strategy", access_scope="private", type="addendum", localized_descriptions=[])

        result = self.manager.update_reasoning_strategy(strategy, automatic_publish=False, upsert=False)

        mock_update_strategy.assert_called_once()
        mock_map_to_strategy.assert_called_once_with({"data": "test_data"})
        self.assertIsInstance(result, ReasoningStrategy)

    @patch('pygeai.lab.strategies.clients.ReasoningStrategyClient.get_reasoning_strategy')
    @patch('pygeai.lab.strategies.mappers.ReasoningStrategyMapper.map_to_reasoning_strategy')
    def test_get_reasoning_strategy_success(self, mock_map_to_strategy, mock_get_strategy):
        mock_get_strategy.return_value = {"data": "test_data"}
        mock_map_to_strategy.return_value = ReasoningStrategy(id="test_strategy", name="test_strategy", access_scope="private", type="addendum")

        result = self.manager.get_reasoning_strategy(reasoning_strategy_id="test_strategy")

        mock_get_strategy.assert_called_once()
        mock_map_to_strategy.assert_called_once_with({"data": "test_data"})
        self.assertIsInstance(result, ReasoningStrategy)

    @patch('pygeai.lab.processes.clients.AgenticProcessClient.create_process')
    @patch('pygeai.lab.processes.mappers.AgenticProcessMapper.map_to_agentic_process')
    def test_create_process_success(self, mock_map_to_process, mock_create_process):
        mock_create_process.return_value = {"data": "test_data"}
        mock_map_to_process.return_value = AgenticProcess(id=self.process_id, name="test_process")
        process = AgenticProcess(name="test_process", key="test_key")

        result = self.manager.create_process(process, automatic_publish=False)

        mock_create_process.assert_called_once()
        mock_map_to_process.assert_called_once_with({"data": "test_data"})
        self.assertIsInstance(result, AgenticProcess)

    @patch('pygeai.lab.processes.clients.AgenticProcessClient.update_process')
    @patch('pygeai.lab.processes.mappers.AgenticProcessMapper.map_to_agentic_process')
    def test_update_process_success(self, mock_map_to_process, mock_update_process):
        mock_update_process.return_value = {"data": "test_data"}
        mock_map_to_process.return_value = AgenticProcess(id=self.process_id, name="test_process")
        process = AgenticProcess(id=self.process_id, name="test_process", key="test_key")

        result = self.manager.update_process(process, automatic_publish=False, upsert=False)

        mock_update_process.assert_called_once()
        mock_map_to_process.assert_called_once_with({"data": "test_data"})
        self.assertIsInstance(result, AgenticProcess)

    @patch('pygeai.lab.processes.clients.AgenticProcessClient.get_process')
    @patch('pygeai.lab.processes.mappers.AgenticProcessMapper.map_to_agentic_process')
    def test_get_process_success(self, mock_map_to_process, mock_get_process):
        mock_get_process.return_value = {"data": "test_data"}
        mock_map_to_process.return_value = AgenticProcess(id=self.process_id, name="test_process")

        result = self.manager.get_process(process_id=self.process_id, filter_settings=self.filter_settings)

        mock_get_process.assert_called_once()
        mock_map_to_process.assert_called_once_with({"data": "test_data"})
        self.assertIsInstance(result, AgenticProcess)

    @patch('pygeai.lab.processes.clients.AgenticProcessClient.list_processes')
    @patch('pygeai.lab.processes.mappers.AgenticProcessMapper.map_to_agentic_process_list')
    def test_list_processes_success(self, mock_map_to_process_list, mock_list_processes):
        mock_list_processes.return_value = {"data": "test_data"}
        mock_map_to_process_list.return_value = AgenticProcessList(processes=[])

        result = self.manager.list_processes(self.filter_settings)

        mock_list_processes.assert_called_once()
        mock_map_to_process_list.assert_called_once_with({"data": "test_data"})
        self.assertIsInstance(result, AgenticProcessList)

    @patch('pygeai.lab.processes.clients.AgenticProcessClient.list_process_instances')
    @patch('pygeai.lab.processes.mappers.ProcessInstanceMapper.map_to_process_instance_list')
    def test_list_process_instances_success(self, mock_map_to_instance_list, mock_list_instances):
        mock_list_instances.return_value = {"data": "test_data"}
        mock_map_to_instance_list.return_value = ProcessInstanceList(instances=[])

        result = self.manager.list_process_instances(self.process_id, self.filter_settings)

        mock_list_instances.assert_called_once()
        mock_map_to_instance_list.assert_called_once_with({"data": "test_data"})
        self.assertIsInstance(result, ProcessInstanceList)

    @patch('pygeai.lab.processes.clients.AgenticProcessClient.delete_process')
    @patch('pygeai.core.base.mappers.ResponseMapper.map_to_empty_response')
    def test_delete_process_success(self, mock_map_to_empty_response, mock_delete_process):
        mock_delete_process.return_value = {"data": "test_data"}
        mock_map_to_empty_response.return_value = {"status": "success"}

        result = self.manager.delete_process(process_id=self.process_id)

        mock_delete_process.assert_called_once()
        mock_map_to_empty_response.assert_called_once()
        self.assertIsInstance(result, dict)

    @patch('pygeai.lab.processes.clients.AgenticProcessClient.publish_process_revision')
    @patch('pygeai.lab.processes.mappers.AgenticProcessMapper.map_to_agentic_process')
    def test_publish_process_revision_success(self, mock_map_to_process, mock_publish_process_revision):
        mock_publish_process_revision.return_value = {"data": "test_data"}
        mock_map_to_process.return_value = AgenticProcess(id=self.process_id, name="test_process")

        result = self.manager.publish_process_revision(process_id=self.process_id, revision=self.revision)

        mock_publish_process_revision.assert_called_once()
        mock_map_to_process.assert_called_once_with({"data": "test_data"})
        self.assertIsInstance(result, AgenticProcess)

    @patch('pygeai.lab.processes.clients.AgenticProcessClient.create_task')
    @patch('pygeai.lab.processes.mappers.TaskMapper.map_to_task')
    def test_create_task_success(self, mock_map_to_task, mock_create_task):
        mock_create_task.return_value = {"data": "test_data"}
        mock_map_to_task.return_value = Task(id=self.task_id, name="test_task")
        task = Task(name="test_task")

        result = self.manager.create_task(task, automatic_publish=False)

        mock_create_task.assert_called_once()
        mock_map_to_task.assert_called_once_with({"data": "test_data"})
        self.assertIsInstance(result, Task)

    @patch('pygeai.lab.processes.clients.AgenticProcessClient.get_task')
    @patch('pygeai.lab.processes.mappers.TaskMapper.map_to_task')
    def test_get_task_success(self, mock_map_to_task, mock_get_task):
        mock_get_task.return_value = {"data": "test_data"}
        mock_map_to_task.return_value = Task(id=self.task_id, name="test_task")

        result = self.manager.get_task(task_id=self.task_id)

        mock_get_task.assert_called_once()
        mock_map_to_task.assert_called_once_with({"data": "test_data"})
        self.assertIsInstance(result, Task)

    @patch('pygeai.lab.processes.clients.AgenticProcessClient.list_tasks')
    @patch('pygeai.lab.processes.mappers.TaskMapper.map_to_task_list')
    def test_list_tasks_success(self, mock_map_to_task_list, mock_list_tasks):
        mock_list_tasks.return_value = {"data": "test_data"}
        mock_map_to_task_list.return_value = TaskList(tasks=[])

        result = self.manager.list_tasks(self.filter_settings)

        mock_list_tasks.assert_called_once()
        mock_map_to_task_list.assert_called_once_with({"data": "test_data"})
        self.assertIsInstance(result, TaskList)

    @patch('pygeai.lab.processes.clients.AgenticProcessClient.update_task')
    @patch('pygeai.lab.processes.mappers.TaskMapper.map_to_task')
    def test_update_task_success(self, mock_map_to_task, mock_update_task):
        mock_update_task.return_value = {"data": "test_data"}
        mock_map_to_task.return_value = Task(id=self.task_id, name="test_task")
        task = Task(id=self.task_id, name="test_task")

        result = self.manager.update_task(task, automatic_publish=False, upsert=False)

        mock_update_task.assert_called_once()
        mock_map_to_task.assert_called_once_with({"data": "test_data"})
        self.assertIsInstance(result, Task)

    @patch('pygeai.lab.processes.clients.AgenticProcessClient.delete_task')
    @patch('pygeai.core.base.mappers.ResponseMapper.map_to_empty_response')
    def test_delete_task_success(self, mock_map_to_empty_response, mock_delete_task):
        mock_delete_task.return_value = {"data": "test_data"}
        mock_map_to_empty_response.return_value = {"status": "success"}

        result = self.manager.delete_task(task_id=self.task_id)

        mock_delete_task.assert_called_once()
        mock_map_to_empty_response.assert_called_once()
        self.assertIsInstance(result, dict)

    @patch('pygeai.lab.processes.clients.AgenticProcessClient.publish_task_revision')
    @patch('pygeai.lab.processes.mappers.TaskMapper.map_to_task')
    def test_publish_task_revision_success(self, mock_map_to_task, mock_publish_task_revision):
        mock_publish_task_revision.return_value = {"data": "test_data"}
        mock_map_to_task.return_value = Task(id=self.task_id, name="test_task")

        result = self.manager.publish_task_revision(task_id=self.task_id, revision=self.revision)

        mock_publish_task_revision.assert_called_once()
        mock_map_to_task.assert_called_once_with({"data": "test_data"})
        self.assertIsInstance(result, Task)

    @patch('pygeai.lab.processes.clients.AgenticProcessClient.start_instance')
    @patch('pygeai.lab.processes.mappers.ProcessInstanceMapper.map_to_process_instance')
    def test_start_instance_success(self, mock_map_to_instance, mock_start_instance):
        mock_start_instance.return_value = {"data": "test_data"}
        mock_map_to_instance.return_value = ProcessInstance(id=self.instance_id, subject="test_subject", process=AgenticProcess(name="test_process"))

        result = self.manager.start_instance("test_process", subject="test_subject", variables=VariableList())

        mock_start_instance.assert_called_once()
        mock_map_to_instance.assert_called_once_with({"data": "test_data"})
        self.assertIsInstance(result, ProcessInstance)

    @patch('pygeai.lab.processes.clients.AgenticProcessClient.abort_instance')
    @patch('pygeai.core.base.mappers.ResponseMapper.map_to_empty_response')
    def test_abort_instance_success(self, mock_map_to_empty_response, mock_abort_instance):
        mock_abort_instance.return_value = {"data": "test_data"}
        mock_map_to_empty_response.return_value = {"status": "success"}

        result = self.manager.abort_instance(self.instance_id)

        mock_abort_instance.assert_called_once()
        mock_map_to_empty_response.assert_called_once()
        self.assertIsInstance(result, dict)

    @patch('pygeai.lab.processes.clients.AgenticProcessClient.get_instance')
    @patch('pygeai.lab.processes.mappers.ProcessInstanceMapper.map_to_process_instance')
    def test_get_instance_success(self, mock_map_to_instance, mock_get_instance):
        mock_get_instance.return_value = {"data": "test_data"}
        mock_map_to_instance.return_value = ProcessInstance(id=self.instance_id, subject="test_subject", process=AgenticProcess(name="test_process"))

        result = self.manager.get_instance(self.instance_id)

        mock_get_instance.assert_called_once()
        mock_map_to_instance.assert_called_once_with({"data": "test_data"})
        self.assertIsInstance(result, ProcessInstance)

    @patch('pygeai.lab.processes.clients.AgenticProcessClient.get_instance_history')
    def test_get_instance_history_success(self, mock_get_instance_history):
        mock_get_instance_history.return_value = {"history": "test_history"}

        result = self.manager.get_instance_history(self.instance_id)

        mock_get_instance_history.assert_called_once()
        self.assertIsInstance(result, dict)

    @patch('pygeai.lab.processes.clients.AgenticProcessClient.get_thread_information')
    def test_get_thread_information_success(self, mock_get_thread_information):
        mock_get_thread_information.return_value = {"info": "test_info"}

        result = self.manager.get_thread_information("test_thread")

        mock_get_thread_information.assert_called_once()
        self.assertIsInstance(result, dict)

    @patch('pygeai.lab.processes.clients.AgenticProcessClient.send_user_signal')
    @patch('pygeai.core.base.mappers.ResponseMapper.map_to_empty_response')
    def test_send_user_signal_success(self, mock_map_to_empty_response, mock_send_user_signal):
        mock_send_user_signal.return_value = {"data": "test_data"}
        mock_map_to_empty_response.return_value = {"status": "success"}

        result = self.manager.send_user_signal(self.instance_id, "test_signal")

        mock_send_user_signal.assert_called_once()
        mock_map_to_empty_response.assert_called_once()
        self.assertIsInstance(result, dict)

    @patch('pygeai.lab.processes.clients.AgenticProcessClient.create_kb')
    @patch('pygeai.lab.processes.mappers.KnowledgeBaseMapper.map_to_knowledge_base')
    def test_create_knowledge_base_success(self, mock_map_to_kb, mock_create_kb):
        mock_create_kb.return_value = {"data": "test_data"}
        mock_map_to_kb.return_value = KnowledgeBase(id=self.kb_id, name="test_kb")
        kb = KnowledgeBase(name="test_kb")

        result = self.manager.create_knowledge_base(kb)

        mock_create_kb.assert_called_once()
        mock_map_to_kb.assert_called_once_with({"data": "test_data"})
        self.assertIsInstance(result, KnowledgeBase)

    @patch('pygeai.lab.processes.clients.AgenticProcessClient.list_kbs')
    @patch('pygeai.lab.processes.mappers.KnowledgeBaseMapper.map_to_knowledge_base_list')
    def test_list_knowledge_bases_success(self, mock_map_to_kb_list, mock_list_kbs):
        mock_list_kbs.return_value = {"data": "test_data"}
        mock_map_to_kb_list.return_value = KnowledgeBaseList(knowledge_bases=[])

        result = self.manager.list_knowledge_bases(start=0, count=10)

        mock_list_kbs.assert_called_once()
        mock_map_to_kb_list.assert_called_once_with({"data": "test_data"})
        self.assertIsInstance(result, KnowledgeBaseList)

    @patch('pygeai.lab.processes.clients.AgenticProcessClient.get_kb')
    @patch('pygeai.lab.processes.mappers.KnowledgeBaseMapper.map_to_knowledge_base')
    def test_get_knowledge_base_success(self, mock_map_to_kb, mock_get_kb):
        mock_get_kb.return_value = {"data": "test_data"}
        mock_map_to_kb.return_value = KnowledgeBase(id=self.kb_id, name="test_kb")

        result = self.manager.get_knowledge_base(kb_id=self.kb_id)

        mock_get_kb.assert_called_once()
        mock_map_to_kb.assert_called_once_with({"data": "test_data"})
        self.assertIsInstance(result, KnowledgeBase)

    @patch('pygeai.lab.processes.clients.AgenticProcessClient.delete_kb')
    @patch('pygeai.core.base.mappers.ResponseMapper.map_to_empty_response')
    def test_delete_knowledge_base_success(self, mock_map_to_empty_response, mock_delete_kb):
        mock_delete_kb.return_value = {"data": "test_data"}
        mock_map_to_empty_response.return_value = {"status": "success"}

        result = self.manager.delete_knowledge_base(kb_id=self.kb_id)

        mock_delete_kb.assert_called_once()
        mock_map_to_empty_response.assert_called_once()
        self.assertIsInstance(result, dict)

    @patch('pygeai.lab.processes.clients.AgenticProcessClient.list_jobs')
    @patch('pygeai.lab.processes.mappers.JobMapper.map_to_job_list')
    def test_list_jobs_success(self, mock_map_to_job_list, mock_list_jobs):
        mock_list_jobs.return_value = {"data": "test_data"}
        mock_map_to_job_list.return_value = JobList(jobs=[])

        result = self.manager.list_jobs(self.filter_settings)

        mock_list_jobs.assert_called_once()
        mock_map_to_job_list.assert_called_once_with({"data": "test_data"})
        self.assertIsInstance(result, JobList)

