# PyGEAI - SDK for Globant Enterprise AI

PyGEAI is a Software Development Kit (SDK) for interacting with [Globant Enterprise AI](https://wiki.genexus.com/enterprise-ai/wiki?8,Table+of+contents%3AEnterprise+AI). It comprises libraries, tools, code samples, and documentation to simplify your experience with the platform.

## Terms and conditions

By using the Python SDK to interact with Globant Enterprise AI, you agree with the following Terms and Conditions:

[Terms and Conditions](https://www.globant.com/enterprise-ai/terms-of-use)

## Compatibility
This package is compatible with the Globant Enterprise AI release from November 2025.

## Configuration

Before using the SDK, you need to define `GEAI_API_KEY` (`$SAIA_APITOKEN`) and `GEAI_API_BASE_URL` (`$BASE_URL`). You can achieve this in three ways:

* **Environment variables:** Set `GEAI_API_KEY` and `GEAI_API_BASE_URL` as environment variables in your operating system.
* **Credentials file:** Create a file named credentials in the `.geai` directory within your user home directory (`$USER_HOME/.geai/credentials`) and define `GEAI_API_KEY` and `GEAI_API_BASE_URL` within this file.
* **Client instantiation:** Specify the `api_key` and `base_url` parameters directly when creating an instance of a client class.

**Note:** If you plan to use the [Evaluation Module](https://wiki.genexus.com/enterprise-ai/wiki?896,Evaluation), you must also define `GEAI_API_EVAL_URL`

### Credentials file
The credentials file is organized via profiles, so one can interact with different instances of Globant Enterprise AI by just
referencing which profile one wishes to use. This also applies to different levels of permissions.

The structure of the credentials file is as follows:

```
[default]
geai_api_key = <API_TOKEN>
geai_api_base_url = <GEAI_BASE_URL>
geai_api_evaul_url = <GEAI_EVALUATION_MODULE_URL>

[<another alias>]
geai_api_key = <API_TOKEN>
geai_api_base_url = <GEAI_BASE_URL>
geai_api_evaul_url = <GEAI_EVALUATION_MODULE_URL>

```

After setting the profiles, one can use them with the --alias option, for example:

```bash 
geai --alias test llm list-providers
```

## Modules

The SDK consists of several modules, all accessible through a single package `pygeai`:

- **`pygeai`**: The package encapsulates all components of the SDK.
- **`admin`**: Allows the user to interact with some of the administration endpoints of Globant Enterprise AI.
- **`assistant`**: This module handles interactions with various Assistants, including [Data Analyst Assistants](https://wiki.genexus.com/enterprise-ai/wiki?886,Data+Analyst+Assistant+2.0), [RAG Assistants](https://wiki.genexus.com/enterprise-ai/wiki?44,RAG+Assistants+Introduction), [Chat with Data Assistants](https://wiki.genexus.com/enterprise-ai/wiki?159,Chat+with+Data+Assistant), [Chat with API Assistants](https://wiki.genexus.com/enterprise-ai/wiki?110,API+Assistant), and [Chat Assistants](https://wiki.genexus.com/enterprise-ai/wiki?708,Chat+Assistant [soon to be deprecated]).
- **`chat`**: This module offers facilities to chat with assistants/agents created in Globant Enterprise AI.
- **`core`**: This module handles interactions with the fundamental components of Globant Enterprise.
- **`cli`**: This module provides a command-line tool for interacting with the SDK.
- **`dbg`**: This module includes a debugger to troubleshoot potential SDK issues and gain detailed insights into its operations.
- **`evaluation`**: This module provides functionality for the evaluation module.
- **`flows`**: This module enables interactions with [Flows](https://wiki.genexus.com/enterprise-ai/wiki?321,Flows+in+Globant+Enterprise+AI) [in development]. 
- **`gam`**: This module allows interaction with [GAM] (https://wiki.genexus.com/commwiki/wiki?24746,Table+of+contents%3AGeneXus+Access+Manager+%28GAM%29,).
- **`health`**: Provides an easy way to check the status of the Globant Enterprise AI instance one is using.
- **`lab`**: This module facilitates interactions with [The Lab] (https://docs.globant.ai/en/wiki?1671,The+Lab).
- **`organization`**: This module facilitates interactions with Organizations and [Projects](https://wiki.genexus.com/enterprise-ai/wiki?565,Projects) in Globant Enterprise AI.
- **`migration`**: This module provides functionality to migrate Agents, Tools and Projects between instances and organizations.
- **`proxy`**: This module handles [integrations with MCP and A2A] (https://docs.globant.ai/en/wiki?1179,Importing+Tools+using+MCP+and+A2A+Servers).

## Usage

### Install PyGEAI
Use pip to install the package from PyPI:

```
(venv) ~$ pip install pygeai
```

To install pre-release versions, you can run:
```
(venv) ~$ pip install --pre pygeai
```

### Verify installation
To check the installed PyGEAI version, run:

```
(venv) ~$ geai v
```

### View help

To access the general help menu:

```
(venv) ~$ geai h
```
To view help for a specific command:

```
(venv) ~$ geai <command> h
```

### Debugger

The `pygeai-dbg` package provides a command-line debugger (`geai-dbg`) for troubleshooting and inspecting the `geai` CLI. 
It pauses execution at breakpoints, allowing you to inspect variables, execute Python code, and control program flow interactively.

To debug a `geai` command, replace `geai` with `geai-dbg`. For example:

```bash
(venv) ~$ geai-dbg ail lrs
```

This pauses at the `main` function in `pygeai.cli.geai`, displaying an interactive prompt `(geai-dbg)`. 
You can then use commands like `continue` (resume), `run` (run without pauses), `quit` (exit), or `help` (list commands).


### Man Pages Documentation

The package includes Unix manual pages (man pages) for detailed command-line documentation. 

To install man pages locally:

```bash
geai-install-man
```

To install man pages system-wide:

```bash
sudo geai-install-man --system
```

To access the man pages:

```bash
man geai
```

#### Setting up Man Pages Access

If you're using a virtual environment, you'll need to configure your system to find the man pages. Add the following to your shell configuration file (`.bashrc`, `.zshrc`, etc.):

```bash
# For macOS
if [ -n "$VIRTUAL_ENV" ]; then
    export MANPATH="$VIRTUAL_ENV/share/man:$MANPATH"
fi

# For Linux
if [ -n "$VIRTUAL_ENV" ]; then
    export MANPATH="$VIRTUAL_ENV/man:$MANPATH"
fi
```

After adding this configuration:
1. Reload your shell configuration: `source ~/.bashrc` or `source ~/.zshrc`
2. The man pages will be available when your virtual environment is active

## Bugs and suggestions
To report any bug, request features or make any suggestions, the following email is available:

<geai-sdk@globant.com>

## Authors
Copyright 2025, Globant. All rights reserved
