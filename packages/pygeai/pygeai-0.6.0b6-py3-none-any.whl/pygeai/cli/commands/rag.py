import json
from pathlib import Path

from pygeai.assistant.rag.clients import RAGAssistantClient
from pygeai.cli.commands import Command, Option, ArgumentsEnum
from pygeai.cli.commands.builders import build_help_text
from pygeai.cli.commands.common import get_welcome_data, get_search_options, get_boolean_value, \
    get_welcome_data_feature_list, get_welcome_data_example_prompt, get_index_options
from pygeai.cli.texts.help import RAG_ASSISTANT_HELP_TEXT
from pygeai.core.common.exceptions import MissingRequirementException, WrongArgumentError
from pygeai.core.utils.console import Console


def show_help():
    """
    Displays help text in stdout
    """
    help_text = build_help_text(rag_commands, RAG_ASSISTANT_HELP_TEXT)
    Console.write_stdout(help_text)


def get_assistants_from_project():
    client = RAGAssistantClient()
    result = client.get_assistants_from_project()
    Console.write_stdout(f"RAG Assistants in project: \n{result}")


def get_assistant_detail(option_list: list):
    name = None
    for option_flag, option_arg in option_list:
        if option_flag.name == "name":
            name = option_arg

    if not name:
        raise MissingRequirementException("Cannot retrieve assistant detail without name")

    client = RAGAssistantClient()
    result = client.get_assistant_data(name)
    Console.write_stdout(f"Assistant detail: \n{result}")


assistant_detail_options = [
    Option(
        "name",
        ["--name", "-n"],
        "RAG assistant name (required)",
        True
    ),
]


def create_assistant(option_list: list):
    name = None
    description = None
    template = None
    search_options = {}
    history_count = None

    llm_cache = False
    llm_frequency_penalty = None
    llm_max_tokens = None
    llm_model_name = None
    llm_n = None
    llm_presence_penalty = None
    llm_provider = None
    llm_stream = False
    llm_temperature = None
    llm_top_p = None
    llm_type = None
    llm_verbose = False

    search_k = None
    search_type = "similarity"
    search_fetch_k = None  # Valid only when using "mmr" type
    search_lambda = None  # Valid only when using "mmr" type
    search_prompt = None
    search_return_source_documents = False  # Default is False
    search_score_threshold = None
    search_template = None

    retriever_type = None  # Expected values: vectorStore, multiQuery, selfQuery, hyde, contextualCompression
    retriever_search_type = "similarity"  # Default is "similarity". Expected values: similarity, similarity_hybrid, semantic_hybrid
    retriever_step = "all"  # Default is "all". Expected values: all, documents
    retriever_prompt = None  # Not needed when using vectorStore

    index_options = {}

    chunk_overlap = None
    chunk_size = None
    use_parent_document = False
    child_k = None
    child_chunk_size = None
    child_chunk_overlap = None

    welcome_data = {}
    welcome_data_title = None
    welcome_data_description = None
    feature_list = []
    examples_prompt_list = []
    for option_flag, option_arg in option_list:
        if option_flag.name == "name":
            name = option_arg
        if option_flag.name == "description":
            description = option_arg
        if option_flag.name == "template":
            template = option_arg

        # Search Options
        if option_flag.name == "history_count":
            history_count = option_arg

        # Search Options - LLM
        if option_flag.name == "llm_cache":
            if option_arg:
                llm_cache = get_boolean_value(option_arg)
        if option_flag.name == "llm_frequency_penalty":
            llm_frequency_penalty = option_arg
        if option_flag.name == "llm_max_tokens":
            llm_max_tokens = option_arg
        if option_flag.name == "llm_model_name":
            llm_model_name = option_arg
        if option_flag.name == "llm_n":
            llm_n = option_arg
        if option_flag.name == "llm_presence_penalty":
            llm_presence_penalty = option_arg
        if option_flag.name == "llm_provider":
            llm_provider = option_arg
        if option_flag.name == "llm_stream":
            if option_arg:
                llm_stream = get_boolean_value(option_arg)
        if option_flag.name == "llm_temperature":
            llm_temperature = option_arg
        if option_flag.name == "llm_top_p":
            llm_top_p = option_arg
        if option_flag.name == "llm_type":
            llm_type = option_arg
        if option_flag.name == "llm_verbose":
            if option_arg:
                llm_verbose = get_boolean_value(option_arg)

        # Search Options - Search
        if option_flag.name == "search_k":
            search_k = option_arg
        if option_flag.name == "search_type":
            search_type = option_arg
        if option_flag.name == "search_fetch_k":
            search_fetch_k = option_arg
        if option_flag.name == "search_lambda":
            search_lambda = option_arg
        if option_flag.name == "search_prompt":
            search_prompt = option_arg
        if option_flag.name == "search_return_source_documents":
            search_return_source_documents = get_boolean_value(option_arg)
        if option_flag.name == "search_score_threshold":
            search_score_threshold = option_arg
        if option_flag.name == "search_template":
            search_template = option_arg

        # Search Options - Retriever
        if option_flag.name == "retriever_type":
            retriever_type = option_arg
        if option_flag.name == "retriever_search_type":
            retriever_search_type = option_arg
        if option_flag.name == "retriever_step":
            retriever_step = option_arg
        if option_flag.name == "retriever_prompt":
            retriever_prompt = option_arg

        # Index Options
        if option_flag.name == "chunk_overlap":
            chunk_overlap = option_arg
        if option_flag.name == "chunk_size":
            chunk_size = option_arg
        if option_flag.name == "use_parent_document":
            use_parent_document = get_boolean_value(option_arg)
        if option_flag.name == "child_k":
            child_k = option_arg
        if option_flag.name == "child_chunk_size":
            child_chunk_size = option_arg
        if option_flag.name == "child_chunk_overlap":
            child_chunk_overlap = option_arg

        # Welcome Data
        if option_flag.name == "welcome_data_title":
            welcome_data_title = option_arg
        if option_flag.name == "welcome_data_description":
            welcome_data_description = option_arg
        if option_flag.name == "welcome_data_feature":
            feature_list = get_welcome_data_feature_list(feature_list, option_arg)
        if option_flag.name == "welcome_data_example_prompt":
            examples_prompt_list = get_welcome_data_example_prompt(examples_prompt_list, option_arg)

    if not name:
        raise MissingRequirementException("Cannot create RAG assistant without name")

    if search_type != "mmr" and (search_fetch_k or search_lambda):
        raise WrongArgumentError("--fetch-k and --lambda are only valid for --search-type 'mmr'")

    if retriever_type == "vectorStore" and retriever_prompt:
        raise WrongArgumentError("--retriever-prompt is not needed when --retriever-type is vectorStore")

    if use_parent_document and (child_k or child_chunk_size or child_chunk_overlap):
        raise WrongArgumentError("--child-k, --child-chunk-size and --child-chunk-overlap are only valid if "
                                 "--use-parent-document is 1")

    if (
            history_count or llm_cache or llm_frequency_penalty or llm_max_tokens or llm_model_name or llm_n
            or llm_presence_penalty or llm_provider or llm_stream or llm_temperature or llm_top_p or llm_type
            or llm_verbose or search_k or search_type or search_fetch_k or search_lambda or search_prompt
            or search_return_source_documents or search_score_threshold or search_template or retriever_type
            or retriever_search_type or retriever_step or retriever_prompt
    ):
        search_options = get_search_options(
            history_count=history_count,
            llm_cache=llm_cache,
            llm_frequency_penalty=llm_frequency_penalty,
            llm_max_tokens=llm_max_tokens,
            llm_model_name=llm_model_name,
            llm_n=llm_n,
            llm_presence_penalty=llm_presence_penalty,
            llm_provider=llm_provider,
            llm_stream=llm_stream,
            llm_temperature=llm_temperature,
            llm_top_p=llm_top_p,
            llm_type=llm_type,
            llm_verbose=llm_verbose,
            search_k=search_k,
            search_type=search_type,
            search_fetch_k=search_fetch_k,
            search_lambda=search_lambda,
            search_prompt=search_prompt,
            search_return_source_documents=search_return_source_documents,
            search_score_threshold=search_score_threshold,
            search_template=search_template,
            retriever_type=retriever_type,
            retriever_search_type=retriever_search_type,
            retriever_step=retriever_step,
            retriever_prompt=retriever_prompt
        )

    if chunk_overlap or chunk_size or use_parent_document or child_k or child_chunk_size or child_chunk_overlap:
        index_options = get_index_options(
            chunk_overlap=chunk_overlap,
            chunk_size=chunk_size,
            use_parent_document=use_parent_document,
            child_k=child_k,
            child_chunk_size=child_chunk_size,
            child_chunk_overlap=child_chunk_overlap,
        )

    if welcome_data_title or welcome_data_description:
        welcome_data = get_welcome_data(
            welcome_data_title,
            welcome_data_description,
            feature_list,
            examples_prompt_list
        )

    client = RAGAssistantClient()
    result = client.create_assistant(
        name=name,
        description=description,
        template=template,
        search_options=search_options,
        index_options=index_options,
        welcome_data=welcome_data
    )
    Console.write_stdout(f"New RAG Assistant: \n{result}")


create_assistant_options = [
    Option(
        "name",
        ["--name", "-n"],
        "RAG assistant name (required)",
        True
    ),
    Option(
        "description",
        ["--description", "-d"],
        "string: Description of the RAG assistant",
        True
    ),
    Option(
        "template",
        ["--template", "--tpl"],
        "string: Name of an existing RAG to base the configuration (optional), empty by default",
        True
    ),
    Option(
        "history_count",
        ["--history-count", "--hc"],
        "integer: history count",
        True
    ),
    Option(
        "llm_cache",
        ["--cache", "-c"],
        "boolean: cache",
        True
    ),
    Option(
        "llm_frequency_penalty",
        ["--frequency-penalty", "--fp"],
        "decimal: frequency penalty",
        True
    ),
    Option(
        "llm_max_tokens",
        ["--max-tokens", "--mt"],
        "integer: max tokens",
        True
    ),
    Option(
        "llm_model_name",
        ["--model-name", "-m"],
        "string: model name",
        True
    ),
    Option(
        "llm_n",
        ["-n"],
        "integer: n",
        True
    ),
    Option(
        "llm_presence_penalty",
        ["--presence-penalty", "--pp"],
        "decimal: presence penalty",
        True
    ),
    Option(
        "llm_provider",
        ["--provider", "-p"],
        "string: provider",
        True
    ),
    Option(
        "llm_stream",
        ["--stream"],
        "boolean: stream",
        True
    ),
    Option(
        "llm_temperature",
        ["--temperature", "--temp", "-t"],
        "decimal: temperature",
        True
    ),
    Option(
        "llm_top_p",
        ["--top-p"],
        "decimal: top P",
        True
    ),
    Option(
        "llm_type",
        ["--llm-type"],
        "string: /: type* empty value (default) or json_object */",
        True
    ),
    Option(
        "llm_verbose",
        ["--verbose", "-v"],
        "boolean: verbose",
        True
    ),
    Option(
        "search_k",
        ["-k"],
        "integer: k",
        True
    ),
    Option(
        "search_type",
        ["--search-type"],
        "string: /: type* similarity (default) or mmr */",
        True
    ),
    Option(
        "search_fetch_k",
        ["--fetch-k", "--fk"],
        "number: fetchK (valid when using mmr type)",
        True
    ),
    Option(
        "search_lambda",
        ["--lambda", "-l"],
        "decimal: lambda (valid when using mmr type)",
        True
    ),
    Option(
        "search_prompt",
        ["--search-prompt", "--sp"],
        "string: prompt",
        True
    ),
    Option(
        "search_return_source_documents",
        ["--return-source-documents", "--rsd"],
        "boolean: return source documents",
        True
    ),
    Option(
        "search_score_threshold",
        ["--score-threshold", "--st"],
        "decimal: score threshold",
        True
    ),
    Option(
        "search_template",
        ["--search-template", "--stpl"],
        "string: template",
        True
    ),
    Option(
        "retriever_type",
        ["--retriever-type"],
        "string: /: type* vectorStore, multiQuery, selfQuery, hyde, contextualCompression */",
        True
    ),
    Option(
        "retriever_search_type",
        ["--retriever-search-type"],
        "string: searchType (similarity | similarity_hybrid | semantic_hybrid). Azure AISearch specific, defaults to similarity",
        True
    ),
    Option(
        "retriever_step",
        ["--step"],
        "string: /: step* all (default) or documents */",
        True
    ),
    Option(
        "retriever_prompt",
        ["--retriever-prompt", "--rp"],
        "string: prompt (not needed when using vectorStore)",
        True
    ),
    Option(
        "chunk_overlap",
        ["--chunk-overlap"],
        "Overlap size between chunks in the main document.",
        True
    ),
    Option(
        "chunk_size",
        ["--chunk-size"],
        "Size of each chunk in the main document.",
        True
    ),
    Option(
        "use_parent_document",
        ["--use-parent-document"],
        "Whether to enable parent-child document relationships.",
        True
    ),
    Option(
        "child_k",
        ["--child-k"],
        "Parameter to configure child document processing, such as relevance or retrieval count.",
        True
    ),
    Option(
        "child_chunk_size",
        ["--child-chunk-size"],
        "Size of each chunk in the child document.",
        True
    ),
    Option(
        "child_chunk_overlap",
        ["--child-chunk-overlap"],
        "Overlap size between chunks in the child document.",
        True
    ),
    Option(
        "welcome_data_title",
        ["--wd-title"],
        'Title for welcome data',
        True
    ),
    Option(
        "welcome_data_description",
        ["--wd-description"],
        'Description for welcome data',
        True
    ),
    Option(
        "welcome_data_feature",
        ["--wd-feature"],
        'Feature to include in welcome data. Must be in JSON format. It can be passed multiple times with one dictionary'
        'each time or one time with a list of dictionaries. Each dictionary must have exactly two keys: "title" and '
        '"description". Example: \'{"title": "title of feature", "description": "Description of feature"}\'',
        True
    ),
    Option(
        "welcome_data_example_prompt",
        ["--wd-example-prompt"],
        'Example prompt to include in welcome data.  Must be in JSON format. It can be passed multiple times with one dictionary'
        'each time or one time with a list of dictionaries. Each dictionary must have exactly two keys: "title", "description" '
        ' and "prompt_text". Example: \'{"title": "Title of prompt", "description": "Description of prompt", "prompt_text": "Prompt text"}\'',
        True
    ),
]


def update_assistant(option_list: list):
    name = None
    status = True
    description = None
    template = None
    search_options = {}
    history_count = None

    llm_cache = False
    llm_frequency_penalty = None
    llm_max_tokens = None
    llm_model_name = None
    llm_n = None
    llm_presence_penalty = None
    llm_provider = None
    llm_stream = False
    llm_temperature = None
    llm_top_p = None
    llm_type = None
    llm_verbose = False

    search_k = None
    search_type = "similarity"
    search_fetch_k = None
    search_lambda = None
    search_prompt = None
    search_return_source_documents = False
    search_score_threshold = None
    search_template = None

    retriever_type = None
    retriever_search_type = "similarity"
    retriever_step = "all"
    retriever_prompt = None

    welcome_data = {}
    welcome_data_title = None
    welcome_data_description = None
    feature_list = []
    examples_prompt_list = []
    for option_flag, option_arg in option_list:
        if option_flag.name == "name":
            name = option_arg
        if option_flag.name == "status":
            status = option_arg
        if option_flag.name == "description":
            description = option_arg
        if option_flag.name == "template":
            template = option_arg

        # Search Options
        if option_flag.name == "history_count":
            history_count = option_arg

        # Search Options - LLM
        if option_flag.name == "llm_cache":
            if option_arg:
                llm_cache = get_boolean_value(option_arg)
        if option_flag.name == "llm_frequency_penalty":
            llm_frequency_penalty = option_arg
        if option_flag.name == "llm_max_tokens":
            llm_max_tokens = option_arg
        if option_flag.name == "llm_model_name":
            llm_model_name = option_arg
        if option_flag.name == "llm_n":
            llm_n = option_arg
        if option_flag.name == "llm_presence_penalty":
            llm_presence_penalty = option_arg
        if option_flag.name == "llm_provider":
            llm_provider = option_arg
        if option_flag.name == "llm_stream":
            if option_arg:
                llm_stream = get_boolean_value(option_arg)
        if option_flag.name == "llm_temperature":
            llm_temperature = option_arg
        if option_flag.name == "llm_top_p":
            llm_top_p = option_arg
        if option_flag.name == "llm_type":
            llm_type = option_arg
        if option_flag.name == "llm_verbose":
            if option_arg:
                llm_verbose = get_boolean_value(option_arg)

        # Search Options - Search
        if option_flag.name == "search_k":
            search_k = option_arg
        if option_flag.name == "search_type":
            search_type = option_arg
        if option_flag.name == "search_fetch_k":
            search_fetch_k = option_arg
        if option_flag.name == "search_lambda":
            search_lambda = option_arg
        if option_flag.name == "search_prompt":
            search_prompt = option_arg
        if option_flag.name == "search_return_source_documents":
            search_return_source_documents = get_boolean_value(option_arg)
        if option_flag.name == "search_score_threshold":
            search_score_threshold = option_arg
        if option_flag.name == "search_template":
            search_template = option_arg

        # Search Options - Retriever
        if option_flag.name == "retriever_type":
            retriever_type = option_arg
        if option_flag.name == "retriever_search_type":
            retriever_search_type = option_arg
        if option_flag.name == "retriever_step":
            retriever_step = option_arg
        if option_flag.name == "retriever_prompt":
            retriever_prompt = option_arg

        # Welcome Data
        if option_flag.name == "welcome_data_title":
            welcome_data_title = option_arg
        if option_flag.name == "welcome_data_description":
            welcome_data_description = option_arg
        if option_flag.name == "welcome_data_feature":
            feature_list = get_welcome_data_feature_list(feature_list, option_arg)
        if option_flag.name == "welcome_data_example_prompt":
            examples_prompt_list = get_welcome_data_example_prompt(examples_prompt_list, option_arg)

    if not name:
        raise MissingRequirementException("Cannot create RAG assistant without name")

    if search_type != "mmr" and (search_fetch_k or search_lambda):
        raise WrongArgumentError("--fetch-k and --lambda are only valid for --search-type 'mmr'")

    if retriever_type == "vectorStore" and retriever_prompt:
        raise WrongArgumentError("--retriever-prompt is not needed when --retriever-type is vectorStore")

    if (
            history_count or llm_cache or llm_frequency_penalty or llm_max_tokens or llm_model_name or llm_n
            or llm_presence_penalty or llm_provider or llm_stream or llm_temperature or llm_top_p or llm_type
            or llm_verbose or search_k or search_type or search_fetch_k or search_lambda or search_prompt
            or search_return_source_documents or search_score_threshold or search_template or retriever_type
            or retriever_search_type or retriever_step or retriever_prompt
    ):
        search_options = get_search_options(
            history_count=history_count,
            llm_cache=llm_cache,
            llm_frequency_penalty=llm_frequency_penalty,
            llm_max_tokens=llm_max_tokens,
            llm_model_name=llm_model_name,
            llm_n=llm_n,
            llm_presence_penalty=llm_presence_penalty,
            llm_provider=llm_provider,
            llm_stream=llm_stream,
            llm_temperature=llm_temperature,
            llm_top_p=llm_top_p,
            llm_type=llm_type,
            llm_verbose=llm_verbose,
            search_k=search_k,
            search_type=search_type,
            search_fetch_k=search_fetch_k,
            search_lambda=search_lambda,
            search_prompt=search_prompt,
            search_return_source_documents=search_return_source_documents,
            search_score_threshold=search_score_threshold,
            search_template=search_template,
            retriever_type=retriever_type,
            retriever_search_type=retriever_search_type,
            retriever_step=retriever_step,
            retriever_prompt=retriever_prompt
        )

    if welcome_data_title or welcome_data_description:
        welcome_data = get_welcome_data(
            welcome_data_title,
            welcome_data_description,
            feature_list,
            examples_prompt_list
        )

    client = RAGAssistantClient()
    result = client.update_assistant(
        name=name,
        status=status,
        description=description,
        template=template,
        search_options=search_options,
        welcome_data=welcome_data
    )
    Console.write_stdout(f"Updated RAG Assistant: \n{result}")


update_assistant_options = [
    Option(
        "name",
        ["--name", "-n"],
        "RAG assistant name (required)",
        True
    ),
    Option(
        "status",
        ["--status"],
        "RAG assistant status (defaults to 1). 1: enabled; 0: disabled",
        True
    ),
    Option(
        "description",
        ["--description", "-d"],
        "string: Description of the RAG assistant",
        True
    ),
    Option(
        "template",
        ["--template", "--tpl"],
        "string: Name of an existing RAG to base the configuration (optional), empty by default",
        True
    ),
    Option(
        "history_count",
        ["--history-count", "--hc"],
        "integer: history count",
        True
    ),
    Option(
        "llm_cache",
        ["--cache", "-c"],
        "boolean: cache",
        True
    ),
    Option(
        "llm_frequency_penalty",
        ["--frequency-penalty", "--fp"],
        "decimal: frequency penalty",
        True
    ),
    Option(
        "llm_max_tokens",
        ["--max-tokens", "--mt"],
        "integer: max tokens",
        True
    ),
    Option(
        "llm_model_name",
        ["--model-name", "-m"],
        "string: model name",
        True
    ),
    Option(
        "llm_n",
        ["-n"],
        "integer: n",
        True
    ),
    Option(
        "llm_presence_penalty",
        ["--presence-penalty", "--pp"],
        "decimal: presence penalty",
        True
    ),
    Option(
        "llm_provider",
        ["--provider", "-p"],
        "string: provider",
        True
    ),
    Option(
        "llm_stream",
        ["--stream"],
        "boolean: stream",
        True
    ),
    Option(
        "llm_temperature",
        ["--temperature", "--temp", "-t"],
        "decimal: temperature",
        True
    ),
    Option(
        "llm_top_p",
        ["--top-p"],
        "decimal: top P",
        True
    ),
    Option(
        "llm_type",
        ["--llm-type"],
        "string: /: type* empty value (default) or json_object */",
        True
    ),
    Option(
        "llm_verbose",
        ["--verbose", "-v"],
        "boolean: verbose",
        True
    ),
    Option(
        "search_k",
        ["-k"],
        "integer: k",
        True
    ),
    Option(
        "search_type",
        ["--search-type"],
        "string: /: type* similarity (default) or mmr */",
        True
    ),
    Option(
        "search_fetch_k",
        ["--fetch-k", "--fk"],
        "number: fetchK (valid when using mmr type)",
        True
    ),
    Option(
        "search_lambda",
        ["--lambda", "-l"],
        "decimal: lambda (valid when using mmr type)",
        True
    ),
    Option(
        "search_prompt",
        ["--search-prompt", "--sp"],
        "string: prompt",
        True
    ),
    Option(
        "search_return_source_documents",
        ["--return-source-documents", "--rsd"],
        "boolean: return source documents",
        True
    ),
    Option(
        "search_score_threshold",
        ["--score-threshold", "--st"],
        "decimal: score threshold",
        True
    ),
    Option(
        "search_template",
        ["--search-template", "--stpl"],
        "string: template",
        True
    ),
    Option(
        "retriever_type",
        ["--retriever-type"],
        "string: /: type* vectorStore, multiQuery, selfQuery, hyde, contextualCompression */",
        True
    ),
    Option(
        "retriever_search_type",
        ["--retriever-search-type"],
        "string: searchType (similarity | similarity_hybrid | semantic_hybrid). Azure AISearch specific, defaults to similarity",
        True
    ),
    Option(
        "retriever_step",
        ["--step"],
        "string: /: step* all (default) or documents */",
        True
    ),
    Option(
        "retriever_prompt",
        ["--retriever-prompt", "--rp"],
        "string: prompt (not needed when using vectorStore)",
        True
    ),
    Option(
        "welcome_data_title",
        ["--wd-title"],
        'Title for welcome data',
        True
    ),
    Option(
        "welcome_data_description",
        ["--wd-description"],
        'Description for welcome data',
        True
    ),
    Option(
        "welcome_data_feature",
        ["--wd-feature"],
        'Feature to include in welcome data. Must be in JSON format. It can be passed multiple times with one dictionary'
        'each time or one time with a list of dictionaries. Each dictionary must have exactly two keys: "title" and '
        '"description". Example: \'{"title": "title of feature", "description": "Description of feature"}\'',
        True
    ),
    Option(
        "welcome_data_example_prompt",
        ["--wd-example-prompt"],
        'Example prompt to include in welcome data.  Must be in JSON format. It can be passed multiple times with one dictionary'
        'each time or one time with a list of dictionaries. Each dictionary must have exactly two keys: "title", "description" '
        ' and "prompt_text". Example: \'{"title": "Title of prompt", "description": "Description of prompt", "prompt_text": "Prompt text"}\'',
        True
    ),
]


def delete_assistant(option_list: list):
    name = None
    for option_flag, option_arg in option_list:
        if option_flag.name == "name":
            name = option_arg

    if not name:
        raise MissingRequirementException("Cannot delete assistant detail without name")

    client = RAGAssistantClient()
    result = client.delete_assistant(name)
    Console.write_stdout(f"Deleted assistant: \n{result}")


delete_assistant_options = [
    Option(
        "name",
        ["--name", "-n"],
        "RAG assistant name (required)",
        True
    ),
]


def list_documents(option_list: list):
    name = None
    skip = 0
    count = 10
    for option_flag, option_arg in option_list:
        if option_flag.name == "name":
            name = option_arg
        if option_flag.name == "skip":
            skip = int(option_arg) if str(option_arg).isdigit() else 0
        if option_flag.name == "count":
            count = int(option_arg) if str(option_arg).isdigit() else 10

    if not name:
        raise MissingRequirementException("Cannot list documents without assistant name")

    client = RAGAssistantClient()
    result = client.get_documents(
        name=name,
        skip=skip,
        count=count
    )
    Console.write_stdout(f"Assistant's documents: \n{result}")


list_documents_options = [
    Option(
        "name",
        ["--name", "-n"],
        "RAG assistant name (required)",
        True
    ),
    Option(
        "skip",
        ["--skip", "-s"],
        "Number of documents to skip",
        True
    ),
    Option(
        "count",
        ["--count", "-c"],
        "Number of documents to return (defaults to 10)",
        True
    ),
]


def delete_all_documents(option_list: list):
    name = None
    for option_flag, option_arg in option_list:
        if option_flag.name == "name":
            name = option_arg

    if not name:
        raise MissingRequirementException("Cannot delete all documents without assistant name")

    client = RAGAssistantClient()
    result = client.delete_all_documents(
        name=name,
    )
    Console.write_stdout(f"Deleted documents: \n{result}")


delete_all_documents_options = [
    Option(
        "name",
        ["--name", "-n"],
        "RAG assistant name (required)",
        True
    ),
]


def get_document_data(option_list: list):
    name = None
    document_id = None
    for option_flag, option_arg in option_list:
        if option_flag.name == "name":
            name = option_arg
        if option_flag.name == "document_id":
            document_id = option_arg

    if not (name and document_id):
        raise MissingRequirementException("Cannot retrieve document data without assistant name and id")

    client = RAGAssistantClient()
    result = client.retrieve_document(
        name=name,
        document_id=document_id
    )
    Console.write_stdout(f"Document detail: \n{result}")


get_document_data_options = [
    Option(
        "name",
        ["--name", "-n"],
        "RAG assistant name (required)",
        True
    ),
    Option(
        "document_id",
        ["--document-id", "--id"],
        "Document id (required)",
        True
    ),
]


def upload_document(option_list: list):
    name = None
    file_path = None
    upload_type = 'multipart'
    metadata = {}
    content_type = None
    for option_flag, option_arg in option_list:
        if option_flag.name == "name":
            name = option_arg
        if option_flag.name == "file_path":
            file_path = option_arg
        if option_flag.name == "upload_type":
            upload_type = option_arg
        if option_flag.name == "metadata":
            metadata_str = str(option_arg)
            if not Path(metadata_str).is_file():
                try:
                    metadata = json.loads(metadata_str)
                except Exception as e:
                    raise WrongArgumentError(f"Metadata should be either a valid dictionary or a file path.")
            else:
                metadata = metadata_str
        if option_flag.name == "content_type":
            content_type = option_arg

    if not (name and file_path):
        raise MissingRequirementException("Cannot upload document without assistant name and file name")

    client = RAGAssistantClient()
    result = client.upload_document(
        name=name,
        file_path=file_path,
        upload_type=upload_type,
        metadata=metadata,
        content_type=content_type
    )
    Console.write_stdout(f"Uploaded: \n{result}")


upload_document_options = [
    Option(
        "name",
        ["--name", "-n"],
        "RAG assistant name (required)",
        True
    ),
    Option(
        "file_path",
        ["--file-path", "-f"],
        "Path to document file (required)",
        True
    ),
    Option(
        "upload_type",
        ["--upload-type", "-t"],
        "Upload type. Available options: binary or multipart (multipart/form-data). Defaults to multipart",
        True
    ),
    Option(
        "metadata",
        ["--metadata", "-m"],
        "Document metadata (only available for multipart/form-data). Can be valid JSON or a path to metadata file.",
        True
    ),
    Option(
        "content_type",
        ["--content-type", "--ct"],
        "Document content type",
        True
    ),

]


def delete_document(option_list: list):
    name = None
    document_id = None
    for option_flag, option_arg in option_list:
        if option_flag.name == "name":
            name = option_arg
        if option_flag.name == "document_id":
            document_id = option_arg

    if not (name and document_id):
        raise MissingRequirementException("Cannot delete document without assistant name and id")

    client = RAGAssistantClient()
    result = client.delete_document(
        name=name,
        document_id=document_id
    )
    Console.write_stdout(f"Deleted document: \n{result}")


delete_document_options = [
    Option(
        "name",
        ["--name", "-n"],
        "RAG assistant name (required)",
        True
    ),
    Option(
        "document_id",
        ["--document-id", "--id"],
        "Document id (required)",
        True
    ),
]


rag_commands = [
    Command(
        "help",
        ["help", "h"],
        "Display help text",
        show_help,
        ArgumentsEnum.NOT_AVAILABLE,
        [],
        []
    ),
    Command(
        "list_assistants",
        ["list-assistants"],
        "Gets all RAG assistants from a project",
        get_assistants_from_project,
        ArgumentsEnum.NOT_AVAILABLE,
        [],
        []
    ),
    Command(
        "get_assistant",
        ["get-assistant"],
        "Gets a specific RAG assistant",
        get_assistant_detail,
        ArgumentsEnum.REQUIRED,
        [],
        assistant_detail_options
    ),
    Command(
        "create_assistant",
        ["create-assistant"],
        "Create a new RAG assistant",
        create_assistant,
        ArgumentsEnum.REQUIRED,
        [],
        create_assistant_options
    ),
    Command(
        "update_assistant",
        ["update-assistant"],
        "Update existing RAG assistant",
        update_assistant,
        ArgumentsEnum.REQUIRED,
        [],
        update_assistant_options
    ),
    Command(
        "delete_assistant",
        ["delete-assistant"],
        "Delete existing RAG assistant",
        delete_assistant,
        ArgumentsEnum.REQUIRED,
        [],
        delete_assistant_options
    ),
    Command(
        "list_documents",
        ["list-documents"],
        "List documents for RAG assistant",
        list_documents,
        ArgumentsEnum.REQUIRED,
        [],
        list_documents_options
    ),
    Command(
        "delete_all_documents",
        ["delete-all-documents", "del-docs"],
        "Delete all documents for RAG assistant",
        delete_all_documents,
        ArgumentsEnum.REQUIRED,
        [],
        delete_all_documents_options
    ),
    Command(
        "get_document",
        ["get-document", "get-doc"],
        "Get document for RAG assistant",
        get_document_data,
        ArgumentsEnum.REQUIRED,
        [],
        get_document_data_options
    ),
    Command(
        "upload_document",
        ["upload-document", "up-doc"],
        "Upload document for RAG assistant",
        upload_document,
        ArgumentsEnum.REQUIRED,
        [],
        upload_document_options
    ),
    Command(
        "delete_document",
        ["delete-document", "del-doc"],
        "Delete document for RAG assistant by id",
        delete_document,
        ArgumentsEnum.REQUIRED,
        [],
        delete_document_options
    )
]
