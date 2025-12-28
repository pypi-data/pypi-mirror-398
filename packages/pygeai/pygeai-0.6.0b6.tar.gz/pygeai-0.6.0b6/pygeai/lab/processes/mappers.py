from typing import List, Dict, Any

from pygeai.lab.models import AgenticProcess, KnowledgeBase, AgenticActivity, ArtifactSignal, UserSignal, Event, \
    SequenceFlow, Task, AgenticProcessList, TaskList, ProcessInstance, ProcessInstanceList, Variable, Prompt, \
    PromptOutput, PromptExample, ArtifactType, ArtifactTypeList, KnowledgeBaseList, JobParameter, Job, JobList


class AgenticProcessMapper:
    @classmethod
    def _map_knowledge_base(cls, kb_data: dict) -> KnowledgeBase:
        return KnowledgeBase(
            name=kb_data.get("name"),
            artifact_type_name=kb_data.get("artifactTypeName"),
            id=kb_data.get("id")
        )

    @classmethod
    def _map_agentic_activities(cls, activities_data: List[dict]) -> List[AgenticActivity]:
        return [
            AgenticActivity(
                key=activity.get("key"),
                name=activity.get("name"),
                task_name=activity.get("taskName"),
                agent_name=activity.get("agentName"),
                agent_revision_id=activity.get("agentRevisionId"),
                agent_id=activity.get("agentId"),
                task_id=activity.get("taskId"),
                task_revision_id=activity.get("taskRevisionId")
            )
            for activity in activities_data
        ]

    @classmethod
    def _map_artifact_signals(cls, signals_data: List[dict]) -> List[ArtifactSignal]:
        return [
            ArtifactSignal(
                key=signal.get("key"),
                name=signal.get("name"),
                handling_type=signal.get("handlingType"),
                artifact_type_name=signal.get("artifactTypeName")
            )
            for signal in signals_data
        ]

    @classmethod
    def _map_user_signals(cls, signals_data: List[dict]) -> List[UserSignal]:
        return [
            UserSignal(
                key=signal.get("key"),
                name=signal.get("name")
            )
            for signal in signals_data
        ]

    @classmethod
    def _map_event(cls, event_data: dict) -> Event:
        return Event(
            key=event_data.get("key"),
            name=event_data.get("name")
        )

    @classmethod
    def _map_sequence_flows(cls, flows_data: List[dict]) -> List[SequenceFlow]:
        return [
            SequenceFlow(
                key=flow.get("key"),
                source_key=flow.get("sourceKey"),
                target_key=flow.get("targetKey")
            )
            for flow in flows_data
        ]

    @classmethod
    def map_to_agentic_process(cls, data: dict) -> AgenticProcess:
        process_data = data.get("processDefinition", data)
        kb_data = process_data.get("kb")
        agentic_activities_data = process_data.get("agenticActivities")
        artifacts_data = process_data.get("artifactSignals")
        signals_data = process_data.get("userSignals")
        start_event_data = process_data.get("startEvent")
        end_event_data = process_data.get("endEvent")
        sequence_flows_data = process_data.get("sequenceFlows")
        variables_data = process_data.get("variables")
        return AgenticProcess(
            key=process_data.get("key"),
            name=process_data.get("name"),
            description=process_data.get("description"),
            kb=cls._map_knowledge_base(kb_data) if kb_data else None,
            agentic_activities=cls._map_agentic_activities(agentic_activities_data) if agentic_activities_data else None,
            artifact_signals=cls._map_artifact_signals(artifacts_data) if artifacts_data else None,
            user_signals=cls._map_user_signals(signals_data) if signals_data else None,
            start_event=cls._map_event(start_event_data) if start_event_data else None,
            end_event=cls._map_event(end_event_data) if end_event_data else None,
            sequence_flows=cls._map_sequence_flows(sequence_flows_data) if sequence_flows_data else None,
            variables=cls._map_to_variables(variables_data) if variables_data else None,
            id=process_data.get("id"),
            status=process_data.get("status") or process_data.get("Status"),
            version_id=process_data.get("versionId") or process_data.get("VersionId"),
            is_draft=process_data.get("isDraft"),
            revision=process_data.get("revision")
        )

    @classmethod
    def _map_to_variables(cls, data: List[dict]) -> List[Variable]:
        """
        Maps a list of dictionaries to a list of Variable objects.

        :param data: List[dict] - List of dictionaries containing variable data (key, value).
        :return: List[Variable] - List of mapped Variable objects.
        """
        return [
            Variable(
                key=var.get("key"),
                value=var.get("value")
            )
            for var in data
        ]

    @classmethod
    def map_to_agentic_process_list(cls, data: dict) -> AgenticProcessList:
        process_list = []
        processes = data.get("processes", data if isinstance(data, list) else [])
        if processes and any(processes):
            for process_data in processes:
                process = cls.map_to_agentic_process(process_data)
                process_list.append(process)
        return AgenticProcessList(processes=process_list)


class TaskMapper:
    @classmethod
    def map_to_task(cls, data: dict) -> Task:
        """
        Maps a dictionary to a Task object with explicit field mapping.

        :param data: dict - The raw data, either input (under 'taskDefinition' key) or output (flat structure).
            Expected fields include name, description, titleTemplate, id, promptData, artifactTypes,
            isDraft, revision, and status.
        :return: Task - A Task object representing the task configuration.
        """
        task_data = data.get("taskDefinition", data)
        prompt_data_data = task_data.get("promptData") or task_data.get('prompt')
        artifact_type_list = task_data.get("artifactTypes")
        return Task(
            name=task_data.get("name"),
            description=task_data.get("description"),
            title_template=task_data.get("titleTemplate"),
            id=task_data.get("id"),
            prompt_data=cls._map_to_prompt_data(prompt_data_data) if prompt_data_data else None,
            artifact_types=cls._map_to_artifact_type_list(artifact_type_list) if artifact_type_list else None,
            is_draft=task_data.get("isDraft"),
            revision=task_data.get("revision"),
            status=task_data.get("status")
        )

    @classmethod
    def _map_to_prompt_data(cls, data: dict) -> Prompt:
        """
        Maps a dictionary to a `Prompt` object.

        :param data: dict - The dictionary containing prompt details.
        :return: Prompt - The mapped `Prompt` object.
        """
        outputs_list = data.get("outputs", [])
        examples_list = data.get("examples", [])
        return Prompt(
            instructions=data.get("instructions"),
            inputs=data.get("inputs", []),
            outputs=cls._map_to_prompt_output_list(outputs_list) if outputs_list else [],
            examples=cls._map_to_prompt_example_list(examples_list) if examples_list else []
        )

    @classmethod
    def _map_to_prompt_output_list(cls, data: List[dict]) -> List[PromptOutput]:
        """
        Maps a list of dictionaries to a list of `PromptOutput` objects.

        :param data: List[dict] - The list of dictionaries containing prompt output details.
        :return: List[PromptOutput] - The mapped list of `PromptOutput` objects.
        """
        return [cls._map_to_prompt_output(output) for output in data]

    @classmethod
    def _map_to_prompt_output(cls, data: dict) -> PromptOutput:
        """
        Maps a dictionary to a `PromptOutput` object.

        :param data: dict - The dictionary containing prompt output details.
        :return: PromptOutput - The mapped `PromptOutput` object.
        """
        return PromptOutput(
            key=data.get("key"),
            description=data.get("description")
        )

    @classmethod
    def _map_to_prompt_example_list(cls, data: List[dict]) -> List[PromptExample]:
        """
        Maps a list of dictionaries to a list of `PromptExample` objects.

        :param data: List[dict] - The list of dictionaries containing prompt example details.
        :return: List[PromptExample] - The mapped list of `PromptExample` objects.
        """
        return [cls._map_to_prompt_example(example) for example in data]

    @classmethod
    def _map_to_prompt_example(cls, data: dict) -> PromptExample:
        """
        Maps a dictionary to a `PromptExample` object.

        :param data: dict - The dictionary containing prompt example details.
        :return: PromptExample - The mapped `PromptExample` object.
        """
        return PromptExample(
            input_data=data.get("inputData"),
            output=data.get("output")
        )

    @classmethod
    def _map_to_artifact_type(cls, data: Dict[str, Any]) -> ArtifactType:
        """
        Maps a dictionary to an ArtifactType object.

        :param data: Dict[str, Any] - The dictionary containing artifact type details.
        :return: ArtifactType - The mapped ArtifactType object.
        """
        return ArtifactType(
            name=data.get("name"),
            description=data.get("description"),
            is_required=data.get("isRequired"),
            usage_type=data.get("usageType"),
            artifact_variable_key=data.get("artifactVariableKey")
        )

    @classmethod
    def _map_to_artifact_type_list(cls, data: List[Dict[str, Any]]) -> ArtifactTypeList:
        """
        Maps a list of dictionaries to an ArtifactTypeList object.

        :param data: List[Dict[str, Any]] - The list of dictionaries containing artifact type details.
        :return: ArtifactTypeList - The mapped ArtifactTypeList object containing ArtifactType instances.
        """
        artifact_types = [cls._map_to_artifact_type(artifact) for artifact in data]
        return ArtifactTypeList(artifact_types=artifact_types)

    @classmethod
    def map_to_task_list(cls, data: dict) -> TaskList:
        task_list = []
        tasks = data.get("tasks", data if isinstance(data, list) else [])
        if tasks and any(tasks):
            for task_data in tasks:
                task = cls.map_to_task(task_data)
                task_list.append(task)
        return TaskList(tasks=task_list)


class ProcessInstanceMapper:
    @classmethod
    def _map_variables(cls, variables_data: List[dict]) -> List[Variable]:
        return [
            Variable(
                key=var.get("key"),
                value=var.get("value")
            )
            for var in variables_data
        ] if variables_data else []

    @classmethod
    def map_to_process_instance(cls, data: dict) -> ProcessInstance:
        process_data = data.get("process", {})
        process = AgenticProcess(
            id=process_data.get("id"),
            is_draft=process_data.get("isDraft"),
            name=process_data.get("name"),
            revision=process_data.get("revision"),
            version_id=process_data.get("version")
        ) if isinstance(process_data, dict) else AgenticProcess(name=process_data)

        variable_data = data.get("variables")
        variables = cls._map_variables(variable_data)
        return ProcessInstance(
            id=data.get("id"),
            process=process,
            created_at=data.get("createdAt"),
            subject=data.get("subject"),
            variables=variables,
            status=data.get("status")
        )

    @classmethod
    def map_to_process_instance_list(cls, data: dict) -> ProcessInstanceList:
        instance_list = []
        instances = data.get("instances", data if isinstance(data, list) else [])
        if instances and any(instances):
            for instance_data in instances:
                instance = cls.map_to_process_instance(instance_data)
                instance_list.append(instance)
        return ProcessInstanceList(instances=instance_list)


class KnowledgeBaseMapper:

    @classmethod
    def map_to_knowledge_base(cls, data: Dict[str, Any]) -> KnowledgeBase:
        """
        Maps a dictionary to a KnowledgeBase object.

        :param data: Dict[str, Any] - The dictionary containing knowledge base details.
        :return: KnowledgeBase - The mapped KnowledgeBase object.
        """
        return KnowledgeBase(
            name=data.get("name"),
            artifact_type_name=data.get("artifactTypeName"),
            id=data.get("id"),
            artifacts=data.get("artifacts"),
            metadata=data.get("metadata"),
        )

    @classmethod
    def map_to_knowledge_base_list(cls, data: Dict[str, Any]) -> KnowledgeBaseList:
        """
        Maps a dictionary to a KnowledgeBaseList object.

        :param data: Dict[str, Any] - The dictionary containing a list of knowledge base details.
        :return: KnowledgeBaseList - The mapped KnowledgeBaseList object containing KnowledgeBase instances.
        """
        kb_list = []
        knowledge_bases = data.get("knowledgeBases", data if isinstance(data, list) else [])
        if knowledge_bases and any(knowledge_bases):
            for kb_data in knowledge_bases:
                kb = cls.map_to_knowledge_base(kb_data)
                kb_list.append(kb)
        return KnowledgeBaseList(knowledge_bases=kb_list)


class JobMapper:
    @classmethod
    def _map_to_job_parameter(cls, data: Dict[str, Any]) -> JobParameter:
        """
        Maps a dictionary to a JobParameter object.

        :param data: Dict[str, Any] - The dictionary containing job parameter details.
        :return: JobParameter - The mapped JobParameter object.
        """
        return JobParameter(
            Name=data.get("Name"),
            Value=data.get("Value")
        )

    @classmethod
    def _map_to_job_parameters(cls, data: List[Dict[str, Any]]) -> List[JobParameter]:
        """
        Maps a list of dictionaries to a list of JobParameter objects.

        :param data: List[Dict[str, Any]] - The list of dictionaries containing job parameter details.
        :return: List[JobParameter] - The mapped list of JobParameter objects.
        """
        return [cls._map_to_job_parameter(param) for param in data] if data else []

    @classmethod
    def map_to_job(cls, data: Dict[str, Any]) -> Job:
        """
        Maps a dictionary to a Job object with explicit field mapping.

        :param data: Dict[str, Any] - The raw data containing job details.
            Expected fields include caption, name, parameters, request, token, topic, and info.
        :return: Job - A Job object representing the job configuration.
        """
        parameters_data = data.get("parameters")
        return Job(
            caption=data.get("caption"),
            name=data.get("name"),
            parameters=cls._map_to_job_parameters(parameters_data) if parameters_data else [],
            request=data.get("request"),
            token=data.get("token"),
            topic=data.get("topic"),
            info=data.get("info")
        )

    @classmethod
    def map_to_job_list(cls, data: List[Dict[str, Any]]) -> JobList:
        """
        Maps a dictionary to a JobList object.

        :param data: Dict[str, Any] - The dictionary containing a list of job details.
        :return: JobList - The mapped JobList object containing Job instances.
        """
        job_list = []
        jobs = data
        if jobs and any(jobs):
            for job_data in jobs:
                job = cls.map_to_job(job_data)
                job_list.append(job)

        return JobList(jobs=job_list)