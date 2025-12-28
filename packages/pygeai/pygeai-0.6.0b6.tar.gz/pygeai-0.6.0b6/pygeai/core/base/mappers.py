from pygeai.core.models import Organization, AssistantIntent, AssistantRevision, \
    AssistantRevisionMetadata, Project, UsageLimit, SearchProfile, ProjectToken, RequestItem, \
    Assistant, TextAssistant, ChatAssistant, LlmSettings, WelcomeData, WelcomeDataFeature, WelcomeDataExamplePrompt, \
    GuardrailSettings
from pygeai.core.base.models import Error
from pygeai.core.base.responses import ErrorListResponse, EmptyResponse


class ErrorMapper:
    """
    A utility class for mapping error-related data structures.

    This class provides methods to convert raw error data from API responses into structured
    `Error` objects, `ErrorListResponse`, or a list of `Error` objects.
    """
    @classmethod
    def map_to_error(cls, data: dict) -> Error:
        """
        Maps a single error dictionary to an `Error` object.

        :param data: dict - The dictionary containing error details.
        :return: Error - An `Error` object with extracted error details.
        """
        identifier = data.get('id') or data.get('code')
        description = data.get('description') or data.get('message')
        return Error(
            id=identifier,
            description=description
        )

    @classmethod
    def map_to_error_list_response(cls, data: dict) -> ErrorListResponse:
        """
       Maps an API response dictionary to an `ErrorListResponse` object.

       This method extracts errors from the given data, converts them into a list of `Error` objects,
       and returns an `ErrorListResponse` containing the list.

       :param data: dict - The dictionary containing error response data.
       :return: ErrorListResponse - A structured response containing a list of errors.
       """
        error_list = cls.map_to_error_list(data)

        return ErrorListResponse(
            errors=error_list
        )

    @classmethod
    def map_to_error_list(cls, data: dict) -> list[Error]:
        """
        Extracts and maps a list of errors from an API response dictionary.

        This method iterates through the `errors` field in the given data and converts
        each error entry into an `Error` object.

        :param data: dict - The dictionary containing error response data.
        :return: list[Error] - A list of `Error` objects.
        """
        error_list = list()
        errors = data.get('errors')
        if errors is not None and any(errors):
            for error_data in errors:
                error = cls.map_to_error(error_data)
                error_list.append(error)

        return error_list


class ResponseMapper:

    @classmethod
    def map_to_empty_response(cls, data: dict) -> EmptyResponse:
        return EmptyResponse(
            content=data
        )


class ModelMapper:

    @classmethod
    def map_to_organization(cls, data: dict) -> Organization:
        """
        Maps a dictionary to an `Organization` object.

        :param data: dict - The dictionary containing organization details.
        :return: Organization - The mapped `Organization` object.
        """
        return Organization(
            id=data.get('organizationId'),
            name=data.get('organizationName')
        )

    @classmethod
    def map_to_assistant(cls, data: dict) -> Assistant:
        """
        Maps a dictionary to an `Assistant` object, including associated intents.

        :param data: dict - The dictionary containing assistant details.
        :return: Assistant - The mapped `Assistant` object.
        """
        intent_data = data.get('intents')[0] if 'intents' in data and len(data.get('intents')) > 0 else {}
        revision_list = cls.map_to_revision_list(intent_data)
        project = cls.map_to_project(data) if 'projectId' in data and 'projectName' in data else None
        welcome_data = cls.map_to_welcome_data(data.get('welcomeData')) if 'welcomeData' in data else None
        llm_settings = cls.map_to_llm_settings(data.get('llmSettings')) if 'llmSettings' in data else None

        return Assistant(
            id=data.get("assistantId"),
            name=data.get("assistantName"),
            type=data.get("assistantType"),
            status=data.get("assistantStatus"),
            priority=data.get("assistantPriority"),
            description=data.get("assistantDescription"),
            prompt=data.get("prompt"),
            default_revision=intent_data.get('assistantIntentDefaultRevision'),
            intent_description=intent_data.get('assistantIntentDescription'),
            intent_id=intent_data.get('assistantIntentId'),
            intent_name=intent_data.get('assistantIntentName'),
            revisions=revision_list,
            project=project,
            welcome_data=welcome_data,
            llm_settings=llm_settings
        )

    @classmethod
    def map_to_intent_list(cls, data: dict) -> list[AssistantIntent]:
        """
        Maps a list of intent dictionaries to `AssistantIntent` objects.

        :param data: dict - The dictionary containing the list of intents.
        :return: list[AssistantIntent] - A list of mapped `AssistantIntent` objects.
        """
        intent_list = list()
        intents = data.get('intents')
        if intents is not None and any(intents):
            for intent_data in intents:
                intent = cls.map_to_intent(intent_data)
                intent_list.append(intent)

        return intent_list

    @classmethod
    def map_to_intent(cls, data: dict) -> AssistantIntent:
        """
        Maps a dictionary to an `AssistantIntent` object, including revisions.

        :param data: dict - The dictionary containing intent details.
        :return: AssistantIntent - The mapped `AssistantIntent` object.
        """
        revision_list = cls.map_to_revision_list(data)

        return AssistantIntent(
            default_revision=data.get("assistantIntentDefaultRevision"),
            description=data.get("assistantIntentDescription"),
            id=data.get("assistantIntentId"),
            name=data.get("assistantIntentName"),
            revisions=revision_list,
        )

    @classmethod
    def map_to_revision_list(cls, data: dict) -> list[AssistantRevision]:
        """
        Maps a list of revision dictionaries to `AssistantRevision` objects.

        :param data: dict - The dictionary containing the list of revisions.
        :return: list[AssistantRevision] - A list of mapped `AssistantRevision` objects.
        """
        revision_list = list()
        revisions = data.get("revisions")
        if revisions is not None and any(revisions):
            for revision_data in revisions:
                revision = cls.map_to_revision(revision_data)
                revision_list.append(revision)

        return revision_list

    @classmethod
    def map_to_revision(cls, data: dict) -> AssistantRevision:
        """
        Maps a dictionary to an `AssistantRevision` object, including metadata.

        :param data: dict - The dictionary containing revision details.
        :return: AssistantRevision - The mapped `AssistantRevision` object.
        """
        metadata_list = cls.map_to_metadata_list(data)

        return AssistantRevision(
            metadata=metadata_list,
            model_id=data.get("modelId"),
            model_name=data.get("modelName"),
            prompt=data.get("prompt"),
            provider_name=data.get("providerName"),
            revision_description=data.get("revisionDescription"),
            revision_id=data.get("revisionId"),
            revision_name=data.get("revisionName"),
            timestamp=data.get("timestamp"),
        )

    @classmethod
    def map_to_metadata_list(cls, data: dict) -> list[AssistantRevisionMetadata]:
        """
       Maps a list of metadata dictionaries to `AssistantRevisionMetadata` objects.

       :param data: dict - The dictionary containing metadata information.
       :return: list[AssistantRevisionMetadata] - A list of mapped `AssistantRevisionMetadata` objects.
       """
        metadata_list = list()
        metadata = data.get('metadata')
        if metadata is not None and any(metadata):
            for metadata_data in metadata:
                metadata = cls.map_to_metadata(metadata_data)
                metadata_list.append(metadata)

        return metadata_list

    @classmethod
    def map_to_metadata(cls, data: dict) -> AssistantRevisionMetadata:
        """
       Maps a dictionary to an `AssistantRevisionMetadata` object.

       :param data: dict - The dictionary containing metadata details.
       :return: AssistantRevisionMetadata - The mapped `AssistantRevisionMetadata` object.
       """
        return AssistantRevisionMetadata(
            key=data.get("key"),
            type=data.get("type"),
            value=data.get("value")
        )

    @classmethod
    def map_to_project(cls, data: dict) -> Project:
        """
        Maps a dictionary to a `Project` object.

        :param data: dict - The dictionary containing project details.
        :return: Project - The mapped `Project` object.
        """
        organization = cls.map_to_organization(data) if "organizationId" in data and "organizationName" in data else None
        # search_profiles = cls.map_to_search_profile_list(data)
        tokens = cls.map_to_token_list(data)
        usage_limit = cls.map_to_usage_limit(data.get('usageLimit')) if "usageLimit" in data else None

        return Project(
            organization=organization,
            id=data.get('projectId'),
            name=data.get('projectName'),
            active=data.get('projectActive'),
            description=data.get('projectDescription'),
            status=data.get('projectStatus'),
            # search_profiles=search_profiles,
            tokens=tokens,
            usage_limit=usage_limit
        )

    @classmethod
    def map_to_search_profile_list(cls, data: dict) -> list[SearchProfile]:
        search_profile_list = list()
        search_profiles = data.get('searchProfiles')
        if search_profiles is not None and any(search_profiles):
            for search_profile_data in search_profiles:
                search_profile = cls.map_to_search_profile(search_profile_data)
                search_profile_list.append(search_profile)

        return search_profile_list

    @classmethod
    def map_to_search_profile(cls, data: dict) -> SearchProfile:
        """
       Maps a dictionary to a `SearchProfile` object.

       :param data: dict - The dictionary containing search profile details.
       :return: SearchProfile - The mapped `SearchProfile` object.
       """
        return SearchProfile(
            name=data.get('name'),
            description=data.get('description'),
        )

    @classmethod
    def map_to_token_list(cls, data: dict) -> list[ProjectToken]:
        token_list = list()
        tokens = data.get('tokens')
        if tokens is not None and any(tokens):
            for token_data in tokens:
                token = cls.map_to_token(token_data)
                token_list.append(token)

        return token_list

    @classmethod
    def map_to_token(cls, data: dict) -> ProjectToken:
        """
       Maps a dictionary to a `ProjectToken` object.

       :param data: dict - The dictionary containing token details.
       :return: ProjectToken - The mapped `ProjectToken` object.
       """
        return ProjectToken(
            description=data.get('description'),
            token_id=data.get('id'),
            name=data.get('name'),
            status=data.get('status'),
            timestamp=data.get('timestamp'),
        )

    @classmethod
    def map_to_usage_limit_list(cls, data: dict) -> list[UsageLimit]:
        usage_limit_list = list()
        usage_limits = data.get('usageLimits')
        if usage_limits is not None and any(usage_limits):
            for usage_limit_data in usage_limits:
                usage_limit = cls.map_to_usage_limit(usage_limit_data)
                usage_limit_list.append(usage_limit)

        return usage_limit_list

    @classmethod
    def map_to_usage_limit(cls, data: dict) -> UsageLimit:
        """
        Maps a dictionary to a `UsageLimit` object.

        :param data: dict - The dictionary containing usage limit details.
        :return: UsageLimit - The mapped `UsageLimit` object.
        """
        return UsageLimit(
            hard_limit=data.get("hardLimit"),
            id=data.get("id"),
            related_entity_name=data.get("relatedEntityName"),
            remaining_usage=data.get("remainingUsage"),
            renewal_status=data.get("renewalStatus"),
            soft_limit=data.get("softLimit"),
            status=data.get("status"),
            subscription_type=data.get("subscriptionType"),
            usage_unit=data.get("usageUnit"),
            used_amount=data.get("usedAmount"),
            valid_from=data.get("validFrom"),
            valid_until=data.get("validUntil"),
        )

    @classmethod
    def map_to_item_list(cls, data: dict) -> list[RequestItem]:
        item_list = list()
        items = data.get('items')
        if items is not None and any(items):
            for item_data in items:
                item = cls.map_to_item(item_data)
                item_list.append(item)

        return item_list

    @classmethod
    def map_to_item(cls, data: dict) -> RequestItem:
        return RequestItem(
            api_token=data.get('apiToken'),
            assistant=data.get('assistant'),
            cost=data.get('cost'),
            elapsed_time_ms=data.get('elapsedTimeMs'),
            end_timestamp=data.get('endTimestamp'),
            feedback=data.get('feedback'),
            intent=data.get('intent'),
            module=data.get('module'),
            prompt=data.get('prompt'),
            output=data.get('output'),
            input_text=data.get('inputText'),
            rag_sources_consulted=data.get('ragSourcesConsulted'),
            session_id=data.get('sessionId'),
            start_timestamp=data.get('startTimestamp'),
            status=data.get('status'),
            timestamp=data.get('timestamp')
        )

    @classmethod
    def map_to_base_assistant(cls, data: dict) -> Assistant:
        assistant_type = data.get('type')
        if assistant_type is not None and assistant_type == "text":
            return TextAssistant(
                id=data.get("assistantId"),
                name=data.get("assistantName"),
                status=bool(data.get("assistantStatus")), # TODO -> Validar casting
            )
        elif assistant_type is not None and assistant_type == "chat":
            return ChatAssistant(
                id=data.get("assistantId"),
                name=data.get("assistantName"),
                status=bool(data.get("assistantStatus")),  # TODO -> Validar casting
            )

    @classmethod
    def map_to_llm_settings(cls, data: dict) -> LlmSettings:
        guardrail_settings = cls.map_to_guardrail_settings(data)
        return LlmSettings(
            provider_name=data.get("providerName") or data.get("provider"),
            model_name=data.get("modelName"),
            temperature=data.get("temperature"),
            frequency_penalty=data.get("frequencyPenalty"),
            presence_penalty=data.get("presencePenalty"),
            max_tokens=data.get("maxTokens"),
            upload_files=data.get("uploadFiles"),
            guardrail_settings=guardrail_settings,
            cache=data.get("cache"),
            n=data.get("n"),
            stream=data.get("stream"),
            topP=data.get("topP"),
            type=data.get("type", ""),
            verbose=data.get("verbose")
        )

    @classmethod
    def map_to_guardrail_settings(cls, data: dict) -> GuardrailSettings:
        return GuardrailSettings(
            llm_output=data.get("llmOutputGuardrail"),
            input_moderation=data.get("inputModerationGuardrail"),
            prompt_injection=data.get("promptInjectionGuardrail")
        )

    @classmethod
    def map_to_welcome_data(cls, data: dict) -> WelcomeData:
        feature_list = cls.map_to_feature_list(data)
        example_prompt_list = cls.map_to_example_prompt_list(data)

        return WelcomeData(
            title=data.get('title'),
            description=data.get('description'),
            features=feature_list,
            examples_prompt=example_prompt_list
        )

    @classmethod
    def map_to_feature_list(cls, data: dict) -> list[WelcomeDataFeature]:
        feature_list = list()
        features = data.get("features")
        if features is not None and any(features):
            for feature_data in features:
                feature = cls.map_to_feature(feature_data)
                feature_list.append(feature)

        return feature_list

    @classmethod
    def map_to_feature(cls, data: dict) -> WelcomeDataFeature:
        return WelcomeDataFeature(
            title=data.get("title"),
            description=data.get("description"),
        )

    @classmethod
    def map_to_example_prompt_list(cls, data: dict) -> list[WelcomeDataExamplePrompt]:
        example_prompt_list = list()
        examples_prompt = data.get("examplesPrompt")
        if examples_prompt is not None and any(examples_prompt):
            for example_prompt_data in examples_prompt:
                example_prompt = cls.map_to_example_prompt(example_prompt_data)
                example_prompt_list.append(example_prompt)

        return example_prompt_list

    @classmethod
    def map_to_example_prompt(cls, data: dict) -> WelcomeDataExamplePrompt:
        return WelcomeDataExamplePrompt(
            title=data.get("title"),
            description=data.get("description"),
            prompt_text=data.get("promptText")
        )

