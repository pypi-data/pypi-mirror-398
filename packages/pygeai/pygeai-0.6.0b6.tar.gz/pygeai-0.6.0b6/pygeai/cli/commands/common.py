import json

from pygeai.core.common.exceptions import WrongArgumentError


def get_llm_settings(
        provider_name: str,
        model_name: str,
        temperature: float,
        max_tokens: int
) -> dict:
    """
    Constructs a dictionary containing the settings for a language model (LLM).

    :param provider_name: str - The name of the LLM provider (e.g., "OpenAI", "Azure").
    :param model_name: str - The name of the specific model to be used (e.g., "gpt-3.5-turbo").
    :param temperature: float - The temperature setting for the LLM, controlling randomness in output.
    :param max_tokens: int - The maximum number of tokens for the LLM's response.
    :return: dict - A dictionary containing the provided LLM settings with keys "providerName", "modelName", "temperature", and "maxTokens".
                    Keys are only included if their corresponding parameters are provided.
    """
    llm_settings = {}

    if provider_name:
        llm_settings["providerName"] = provider_name
    if model_name:
        llm_settings["modelName"] = model_name
    if temperature:
        llm_settings["temperature"] = temperature
    if max_tokens:
        llm_settings["maxTokens"] = max_tokens

    return llm_settings


def get_welcome_data(
        welcome_data_title: str,
        welcome_data_description: str,
        feature_list: list,
        examples_prompt_list: list
) -> dict:
    """
    Constructs a structured dictionary for welcome data using provided title, description, features, and examples.

    :param welcome_data_title: str - The title for the welcome data.
    :param welcome_data_description: str - A description for the welcome data.
    :param feature_list: list - A list of dictionaries, where each dictionary must contain the keys "title" and "description".
    :param examples_prompt_list: list - A list of dictionaries, where each dictionary must contain the keys "title", "description", and "prompt_text".
    :return: dict - A dictionary containing the "title", "description", "features", and "examplesPrompt" fields.
    :raises WrongArgumentError: If a dictionary in `feature_list` does not contain the required keys "title" and "description",
                                or if a dictionary in `examples_prompt_list` does not contain the required keys "title", "description", and "prompt_text".
    """
    features = []
    examples_prompt = []
    if any(feature_list):
        try:
            for feature_dict in feature_list:
                features.append({
                    "title": feature_dict['title'],
                    "description": feature_dict['description']
                })
        except ValueError as e:
            raise WrongArgumentError(
                "Each feature must have exactly two keys: \"title\" and \"description\"")

    if any(examples_prompt_list):
        try:
            for example in examples_prompt_list:
                examples_prompt.append({
                    "title": example['title'],
                    "description": example['description'],
                    "promptText": example['prompt_text']
                })
        except ValueError as e:
            raise WrongArgumentError(
                "Each example prompt must have exactly three keys: \"title\", \"description\", and \"prompt_text\"")

    welcome_data = {
        "title": welcome_data_title,
        "description": welcome_data_description,
        "features": features,
        "examplesPrompt": examples_prompt
    }

    return welcome_data


def get_messages(message_list: list):
    """
    Processes a list of message dictionaries and extracts the "role" and "content" fields.

    :param message_list: list - A list of dictionaries, where each dictionary must contain the keys "role" and "content".
    :return: list - A list of dictionaries, each containing the "role" and "content" fields extracted from the input.
    :raises WrongArgumentError: If a dictionary in the list is not in the expected format or missing the required keys.
    """
    messages = []
    if any(message_list):
        try:
            for message_dict in message_list:
                messages.append({
                    "role": message_dict['role'],
                    "content": message_dict['content']
                })
        except ValueError as e:
            raise WrongArgumentError(
                "Each message must be in JSON format: '{\"role\": \"user\", \"content\": \"message content\"}' "
                "Each dictionary must contain role and content")

    return messages


def get_boolean_value(option_arg: str):
    """
   Converts a string argument into a boolean value.

   :param option_arg: str - A string representation of an integer (e.g., "0" or "1") to be converted to a boolean.
                          "0" is interpreted as `False`, and "1" is interpreted as `True`.
   :return: bool - The boolean value corresponding to the input.
   :raises WrongArgumentError: If the input is not a valid integer or is not "0" or "1".
                               Possible values for `option_arg` are "0" (off) or "1" (on).
   """
    try:
        return bool(int(option_arg))
    except ValueError as e:
        raise WrongArgumentError("Possible values are 0 or 1, for off and on, respectively.")


def get_penalty_float_value(option_arg: str):
    """
   Converts a string argument into a float value representing a penalty and validates its range.

   :param option_arg: str - A string representation of a float to be converted to a penalty value.
                            The value must be between -2.0 and 2.0 (inclusive).
   :return: float - The float value corresponding to the input, if valid.
   :raises WrongArgumentError: If the input is not a valid float or if the value is outside the range [-2.0, 2.0].
                               The penalty must be a number between -2.0 and 2.0.
   """
    try:
        penalty = float(option_arg)
        if penalty < -2.0 or 2.0 < penalty:
            raise ValueError("Penalty out of range")
        return penalty
    except Exception as e:
        raise WrongArgumentError("If defined, penalty must be a number between -2.0 and 2.0")


def _build_llm_options(
        llm_cache: bool,
        llm_frequency_penalty: float,
        llm_max_tokens: int,
        llm_model_name: str,
        llm_n: int,
        llm_presence_penalty: float,
        llm_provider: str,
        llm_stream: bool,
        llm_temperature: float,
        llm_top_p: float,
        llm_type: dict,
        llm_verbose: bool
) -> dict:
    """
    Constructs a dictionary for LLM-specific options.

    :return: dict - LLM configuration options.
    """
    llm_options = {}
    if llm_cache is not None:
        llm_options["cache"] = llm_cache
    if llm_frequency_penalty:
        llm_options["frequencyPenalty"] = llm_frequency_penalty
    if llm_max_tokens:
        llm_options["maxTokens"] = llm_max_tokens
    if llm_model_name:
        llm_options["modelName"] = llm_model_name
    if llm_n:
        llm_options["n"] = llm_n
    if llm_presence_penalty:
        llm_options["presencePenalty"] = llm_presence_penalty
    if llm_provider:
        llm_options["provider"] = llm_provider
    if llm_stream is not None:
        llm_options["stream"] = llm_stream
    if llm_temperature:
        llm_options["temperature"] = llm_temperature
    if llm_top_p:
        llm_options["topP"] = llm_top_p
    if llm_type:
        llm_options["type"] = llm_type
    if llm_verbose is not None:
        llm_options["verbose"] = llm_verbose

    return llm_options


def _build_search_options(
        search_k: int,
        search_type: str,
        search_fetch_k: int,
        search_lambda: float,
        search_prompt: str,
        search_return_source_documents: bool,
        search_score_threshold: float,
        search_template: str
) -> dict:
    """
    Constructs a dictionary for search-specific options.

    :return: dict - Search configuration options.
    """
    search_options = {}
    if search_k:
        search_options["k"] = search_k
    if search_type:
        search_options["type"] = search_type
    if search_fetch_k:
        search_options["fetchK"] = search_fetch_k
    if search_lambda:
        search_options["lambda"] = search_lambda
    if search_prompt:
        search_options["prompt"] = search_prompt
    if search_return_source_documents is not None:
        search_options["returnSourceDocuments"] = search_return_source_documents
    if search_score_threshold:
        search_options["scoreThreshold"] = search_score_threshold
    if search_template:
        search_options["template"] = search_template

    return search_options


def _build_retriever_options(
        retriever_type: str,
        retriever_search_type: str,
        retriever_step: str,
        retriever_prompt: str
) -> dict:
    """
    Constructs a dictionary for retriever-specific options.

    :return: dict - Retriever configuration options.
    """
    retriever_options = {}
    if retriever_type:
        retriever_options["type"] = retriever_type
    if retriever_search_type:
        retriever_options["searchType"] = retriever_search_type
    if retriever_step:
        retriever_options["step"] = retriever_step
    if retriever_prompt:
        retriever_options["prompt"] = retriever_prompt

    return retriever_options


def get_search_options(
        history_count: int,
        llm_cache: bool,
        llm_frequency_penalty: float,
        llm_max_tokens: int,
        llm_model_name: str,
        llm_n: int,
        llm_presence_penalty: float,
        llm_provider: str,
        llm_stream: bool,
        llm_temperature: float,
        llm_top_p: float,
        llm_type: dict,
        llm_verbose: bool,
        search_k: int,
        search_type: str,
        search_fetch_k: int,
        search_lambda: float,
        search_prompt: str,
        search_return_source_documents: bool,
        search_score_threshold: float,
        search_template: str,
        retriever_type: str,
        retriever_search_type: str,
        retriever_step: str,
        retriever_prompt: str
) -> dict:
    """
    Constructs a dictionary of search options for configuring LLM, search, and retriever settings.

    :param history_count: int - Number of historical interactions to include in the search context.
    :param llm_cache: bool - Whether to enable caching for the LLM.
    :param llm_frequency_penalty: float - Frequency penalty parameter for LLM responses.
    :param llm_max_tokens: int - Maximum number of tokens to generate in the LLM response.
    :param llm_model_name: str - Name of the LLM model to use.
    :param llm_n: int - Number of completions to generate for each prompt.
    :param llm_presence_penalty: float - Presence penalty parameter for LLM responses.
    :param llm_provider: str - Provider of the LLM service.
    :param llm_stream: bool - Whether to enable streaming for the LLM responses.
    :param llm_temperature: float - Sampling temperature for LLM responses.
    :param llm_top_p: float - Top-p sampling value for LLM responses.
    :param llm_type: dict - Configuration type for the LLM, such as an empty value (default) or JSON object.
    :param llm_verbose: bool - Whether to enable verbose mode for the LLM responses.
    :param search_k: int - Number of documents to retrieve during the search phase.
    :param search_type: str - Type of search to execute (e.g., similarity or mmr).
    :param search_fetch_k: int - Number of documents to fetch when using MMR search type.
    :param search_lambda: float - Lambda parameter for MMR search type.
    :param search_prompt: str - Custom search prompt (not required when using vectorStore).
    :param search_return_source_documents: bool - Whether to return source documents with the search results.
    :param search_score_threshold: float - Minimum score threshold for documents to be included in results.
    :param search_template: str - Template to use for the search process.
    :param retriever_type: str - Type of retriever to use (e.g., vectorStore, multiQuery, selfQuery).
    :param retriever_search_type: str - Specific search type for the retriever (e.g., similarity, similarity_hybrid).
    :param retriever_step: str - Step type for the retriever (e.g., all or documents).
    :param retriever_prompt: str - Custom prompt for the retriever.

    :return: dict - A dictionary containing the configured options for LLM, search, and retriever.
    """
    return {
        "history_count": history_count if history_count else None,
        "llm": _build_llm_options(
            llm_cache, llm_frequency_penalty, llm_max_tokens, llm_model_name,
            llm_n, llm_presence_penalty, llm_provider, llm_stream,
            llm_temperature, llm_top_p, llm_type, llm_verbose
        ),
        "search": _build_search_options(
            search_k, search_type, search_fetch_k, search_lambda,
            search_prompt, search_return_source_documents,
            search_score_threshold, search_template
        ),
        "retriever": _build_retriever_options(
            retriever_type, retriever_search_type, retriever_step, retriever_prompt
        )
    }


def get_index_options(
    chunk_overlap: int,
    chunk_size: int,
    use_parent_document: bool,
    child_k: float,
    child_chunk_size: float,
    child_chunk_overlap: float
) -> dict:
    """
    Constructs a dictionary of index options for configuring document chunking and parent-child document relationships.

    :param chunk_overlap: int - Overlap size between chunks in the main document.
    :param chunk_size: int - Size of each chunk in the main document.
    :param use_parent_document: bool - Whether to enable parent-child document relationships.
    :param child_k: float - Parameter to configure child document processing, such as relevance or retrieval count.
    :param child_chunk_size: float - Size of each chunk in the child document.
    :param child_chunk_overlap: float - Overlap size between chunks in the child document.

    :return: dict - A dictionary containing configuration options for chunking and parent-child relationships.
        - "chunks": Contains chunk configuration for the main document, including "chunkOverlap" and "chunkSize".
        - "useParentDocument": Indicates if parent-child relationships are enabled.
        - "childDocument": Contains configuration for child documents, including "childK", "chunkSize", and "chunkOverlap" if applicable.
    """
    index_options = {
        "chunks": {},
        "useParentDocument": use_parent_document,
        "childDocument": {}
    }
    if chunk_overlap is not None:
        index_options["chunks"]["chunkOverlap"] = chunk_overlap
    if chunk_size is not None:
        index_options["chunks"]["chunkSize"] = chunk_size

    if use_parent_document:
        index_options["childDocument"]["child"] = {}
        if child_k:
            index_options["childDocument"]["childK"] = child_k
        if child_chunk_size:
            index_options["childDocument"]["child"]["chunkSize"] = child_chunk_size
        if child_chunk_overlap:
            index_options["childDocument"]["child"]["chunkOverlap"] = child_chunk_overlap

    return index_options


def get_welcome_data_feature_list(feature_list: list, option_arg: str):
    try:
        feature_json = json.loads(option_arg)
        if isinstance(feature_json, list):
            feature_list = feature_json
        elif isinstance(feature_json, dict):
            feature_list.append(feature_json)
    except Exception as e:
        raise WrongArgumentError(
            "Features must be a JSON string. It can be either a dictionary or a list or dictionaries. "
            "Each feature must be a dictionary with exactly two keys: 'title' and 'description'")

    return feature_list


def get_welcome_data_example_prompt(examples_prompt_list: list, option_arg: str):
    try:
        examples_prompt_json = json.loads(option_arg)
        if isinstance(examples_prompt_json, list):
            examples_prompt_list = examples_prompt_json
        elif isinstance(examples_prompt_json, dict):
            examples_prompt_list.append(examples_prompt_json)
    except Exception as e:
        raise WrongArgumentError(
            "Example prompt text must be a JSON string. It can be either a dictionary or a list or dictionaries. "
            "Each example_prompt must be a dictionary with exactly three keys: 'title', 'description' and 'prompt_text'")

    return examples_prompt_list
