# GEAI Proxy Documentation

## NAME
`geai-proxy` – proxy service for managing Model Context Protocol (MCP) servers with GEAI

## SYNOPSIS
```bash
geai-proxy [OPTIONS] CONFIG_FILE
```

## DESCRIPTION
The GEAI Proxy is a Python-based tool that acts as an intermediary between the GEAI API and various tool servers. It manages the registration, execution, and result handling of tool operations through a proxy service.

To install:

```bash
pip install pygeai
```

## CONFIGURATION

The GEAI Proxy requires two distinct types of configuration:

### 1. MCP Servers Configuration

This section declares the Model Context Protocol (MCP) servers that this proxy will link with GEAI. The configuration follows the Claude Desktop standard format and supports multiple servers in one file.

#### Configuration File Format

```json
{
  "mcpServers": {
    "serverName1": {
      "command": "command-to-launch-server",
      "args": ["arg1", "arg2", "..."]
    },
    "serverName2": {
      "command": "command-to-launch-server",
      "args": ["arg1", "arg2", "..."]
    }
  }
}
```

#### Example: Puppeteer Server

```json
{
  "mcpServers": {
    "puppeteer": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-puppeteer"]
    }
  }
}
```

#### Example: Filesystem Server

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "~/mcp-shared-folder"]
    }
  }
}
```

#### Example: HTTP+SSE Server

```json
{
  "mcpServers": {
    "markitdown": {
      "uri": "http://localhost:5000/sse"
    }
  }
}
```

#### Example: Multiple Servers Combined

```json
{
  "mcpServers": {
    "puppeteer": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-puppeteer"]
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "~/mcp-shared-folder"]
    },
    "markitdown": {
      "uri": "http://localhost:5000/sse"
    },
    "custom-server": {
      "command": "python",
      "args": ["path/to/your/custom_mcp_server.py"]
    }
  }
}
```

## PUBLIC TOOL REGISTRATION

Tools provided by both MCP and A2A servers can be published to GEAI under a public namespace by including the `public_prefix` field in their configuration entry.

This allows tools to be registered under a well-defined global identifier, making them discoverable and shareable across proxies and clients.

### MCP Server Example with Public Prefix

Registers tools from the `puppeteer` MCP server under the prefix `com.globant.puppeteer`:

```json
{
  "mcpServers": {
    "public_prefix": "com.globant.puppeteer",
    "puppeteer": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-puppeteer"]
    }
  }
}
```

### A2A Server Example with Public Prefix

Registers tools from the `hello-world` A2A agent under the prefix `com.genexus.a2a.sampleagent`:

```json
{
  "a2aServers": {
    "hello-world": {
      "public_prefix": "com.genexus.a2a.sampleagent",
      "url": "http://localhost:9999",
      "headers": {
        "Authorization": "Bearer fh84ff...."
      }
    }
  }
}
```

### Resulting Tool Identifiers

For example, a tool named `translate_text` would be available as:

```text
com.genexus.a2a.sampleagent.translate_text
```

### 2. Proxy Authentication Configuration

This section establishes the connection between the proxy and GEAI and manages user aliases.

#### Automatic Configuration (First Run)

```bash
geai-proxy sample-mcp-config.json --alias myalias
```

#### Manual Configuration (Reconfiguration)

```bash
geai-proxy --configure --alias myalias
```

During interactive setup, the CLI will prompt:

```
# Configuring GEAI proxy settings...
Generated new proxy ID: 37bae96b-bc99-4110-bb61-b912b28f9e32
-> Insert proxy ID (UUID) (Current: 37bae96b-bc99-4110-bb61-b912b28f9e32, Leave empty to keep):
-> Insert proxy API key:
-> Insert proxy base URL:
-> Insert proxy name:
-> Insert proxy description:
```

## PROXY CONFIGURATION PARAMETERS

During interactive setup, the following parameters are requested:

- **proxy ID (UUID)**  
  A unique identifier for this proxy instance. If left empty, the automatically generated UUID will be used.

- **proxy API key**  
  The API key used to authenticate the proxy with the GEAI backend. Must be a token from GEAI for a specific project.

- **proxy base URL**  
  The base URL of the GEAI installation to connect to.  
  Example: `https://api.beta.saia.ai`

- **proxy name**  
  Human-readable name for this proxy instance, stored under the alias.

- **proxy description**  
  Optional. Helps identify this proxy instance when using multiple aliases.

### Environment Variables

All of the above configuration parameters can also be set via environment variables:

- `GEAI_API_KEY`  
- `GEAI_API_BASE_URL`  
- `PROXY_ID`  
- `PROXY_NAME`  
- `PROXY_DESCRIPTION`  

These environment variables override or represent the configuration of the **default alias**. Therefore, they will only be taken into account if the proxy is invoked with `--alias default`. When using a different alias, these variables are ignored.

## USAGE

To start the proxy server with a config and alias:

```bash
geai-proxy sample-mcp-config.json --alias myalias
```

### Command Line Arguments

- **config_file**: Path to the MCP servers configuration file (JSON).
- **--alias ALIAS**: Alias for the proxy settings.
- **--configure**: Reconfigure proxy authentication settings.

## FILES

- `pygeai/proxy/sample-mcp-config.json` – Sample configuration file for MCP servers.

## SEE ALSO

- `pygeai (1)`

## THIRD-PARTY COMPONENTS

This software includes code from the `a2a-python` project by Google LLC, licensed under the Apache License 2.0.

Only the vendored component in `pygeai/vendor/a2a/` is Apache-licensed. The rest is MIT-licensed.

License sources:

- https://github.com/google/a2a-python
- `pygeai/vendor/a2a/LICENSE`

## AUTHOR

Written by the GEAI development team.

## COPYRIGHT

Copyright © 2025 GEAI development team.

This is free software; see the source for copying conditions. There is NO warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

##Architecture

```mermaidAdd commentMore actions
graph TD
    user["User \nClient interacting with the GEAI"]
    geai["GEAI \nGlobant Enterprise AI"]
    proxy["MCP / A2A Proxy \nProxy that connects to multiple MCP Servers / A2A Agents to call tools"]

    mcpA["MCP Server A \nTool server for search functionality"]
    mcpB["MCP Server B \nTool server for code execution"]
    A2A["A2A Agent  \nAi Agent for database queries"]

    
    user -->|Interacts/Calls tools via| geai
    geai -->|Returns tool responses| user
    geai -->|Calls tools via| proxy
    proxy -->|Returns tool responses| geai

    user -->|Calls Search Tool| proxy
    proxy -->|Calls Search Tool| mcpA
    mcpA -->|Returns search results| proxy

    proxy -->|Calls Code Tool| mcpB
    mcpB -->|Returns code output| proxy

    proxy -->|Calls DB Agent| A2A
    A2A -->|Returns sql query| proxy
```
