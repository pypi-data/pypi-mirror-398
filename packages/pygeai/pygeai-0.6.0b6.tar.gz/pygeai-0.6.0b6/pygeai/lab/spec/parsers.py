from pygeai.lab.models import Agent, Tool, Task, AgenticProcess


class AgentParser:

    @classmethod
    def get_agent(cls, data: dict):
        agent = Agent.model_validate(data)

        return agent


class ToolParser:

    @classmethod
    def get_tool(cls, data: dict):
        tool = Tool.model_validate(data)

        return tool


class TaskParser:

    @classmethod
    def get_task(cls, data: dict):
        task = Task.model_validate(data)

        return task


class AgenticProcessParser:

    @classmethod
    def get_agentic_process(cls, data: dict):
        proces = AgenticProcess.model_validate(data)

        return proces


