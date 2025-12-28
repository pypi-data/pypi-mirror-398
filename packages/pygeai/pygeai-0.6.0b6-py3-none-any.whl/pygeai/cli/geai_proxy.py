#!/usr/bin/env python
import json
import asyncio
import sys
from typing import Final
import argparse
import uuid
import yaml
from pygeai import logger
from pygeai.proxy.managers import ServerManager
from pygeai.proxy.config import ProxySettingsManager
from pygeai.admin.clients import AdminClient
from pygeai.core.utils.console import Console, StreamWriter
class CustomProxyStream(StreamWriter):
    """
    Custom stream writer for proxy output with color support for TTY terminals.
    """
    IS_TTY: Final[bool] = sys.stderr.isatty()
    RED: Final[str] = "\033[91m" if IS_TTY else ""
    RESET: Final[str] = "\033[0m" if IS_TTY else ""

    def write_stdout(self, message: str, end: str = "\n"):
        """
        Write message to stdout and log as info.
        """
        sys.stdout.write(f"{message}{end}")
        logger.info(f"{message}{end}")

    def write_stderr(self, message: str, end: str = "\n"):
        """
        Write message to stderr with red color and log as error.
        """
        sys.stderr.write(f"{self.RED}{message}{self.RESET}{end}")
        logger.error(f"{message}{end}")

    def write_exception(self, message: str, exception: Exception, end: str = "\n"):
        """
        Write exception message to stderr with red color and log as exception.
        """
        sys.stderr.write(f"{self.RED}{message}{self.RESET} {str(exception)}{end}")
        logger.exception(f"{message}{end}", exception)

Console.set_writer(CustomProxyStream())

def load_config(path: str) -> list:
    """
    Load server configuration from YAML or JSON file.

    :param path: str - Path to configuration file
    :return: list - List of server configurations
    :raises: FileNotFoundError - If the configuration file doesn't exist
    :raises: ValueError - If the file format is invalid or missing mcpServers key
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) if path.endswith(('.yaml', '.yml')) else json.load(f)
            servers = []
            if 'mcpServers' in config:
                for name, server_cfg in config['mcpServers'].items():
                    server_cfg['name'] = name
                    server_cfg['type'] = 'mcp'
                    servers.append(server_cfg)

            if 'a2aServers' in config:
                for name, server_cfg in config['a2aServers'].items():
                    server_cfg['name'] = name
                    server_cfg['type'] = 'a2a'
                    servers.append(server_cfg)
            
            if not 'a2aServers' in config and not 'mcpServers' in config:
                Console.write_stderr("Error: MCP servers or A2A servers are required")

            return servers
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Configuration file '{path}' not found") from exc


def configure_proxy_settings(settings: ProxySettingsManager, args: argparse.Namespace, only_missing: bool = False):
    """
    Configure proxy settings interactively or from command line arguments.

    :param settings: ProxySettingsManager - Settings manager instance
    :param args: argparse.Namespace - Command line arguments
    :param only_missing: bool - Whether to only configure missing settings
    :return: None
    """
    if not args.alias:
        alias = input("-> Insert alias for settings section (Leave empty for default): ") or ProxySettingsManager.DEFAULT_ALIAS
    else:
        alias = args.alias
    
    current_id = settings.get_proxy_id(alias)
    current_name = settings.get_proxy_name(alias)
    current_description = settings.get_proxy_description(alias)
    #current_affinity = settings.get_proxy_affinity(alias)
    current_api_key = settings.get_api_key(alias)
    current_base_url = settings.get_base_url(alias)

    #first_time = all(not x for x in [ current_id, current_name, current_description, current_api_key, current_base_url])

    if not only_missing or any(not x for x in [current_id, current_name, current_description, current_api_key, current_base_url]):
        Console.write_stdout("# Configuring GEAI proxy settings...")
        
        if not current_id:
            current_id = uuid.uuid4()
            settings.set_proxy_id(current_id, alias)
            Console.write_stdout(f"Generated new proxy ID: {current_id}")
        
        if not only_missing or not current_id:
            server_id = input(f"-> Insert proxy ID (UUID) (Current: {current_id}, Leave empty to keep): ")
            if server_id:
                try:
                    settings.set_proxy_id(uuid.UUID(server_id), alias)
                except ValueError:
                    Console.write_stdout("Error: Invalid UUID format")
                    return
        if not only_missing or not current_api_key:
            if current_api_key:
                server_api_key = input(f"-> Insert proxy API key (Current: {current_api_key}, Leave empty to keep): ")
            else:
                server_api_key = input("-> Insert proxy API key: ")
            if server_api_key:
                settings.set_api_key(server_api_key, alias)

        if not only_missing or not current_base_url:
            if current_base_url:
                server_base_url = input(f"-> Insert proxy base URL (Current: {current_base_url}, Leave empty to keep): ")
            else:
                server_base_url = input("-> Insert proxy base URL: ")
            if server_base_url:
                settings.set_base_url(server_base_url, alias)

        if not only_missing or not current_name:
            if current_name:
                server_name = input(f"-> Insert proxy name (Current: {current_name}, Leave empty to keep): ")
            else:
                server_name = input("-> Insert proxy name: ")
            if server_name:
                settings.set_proxy_name(server_name, alias)

        if not only_missing or not current_description:
            if current_description:
                server_description = input("-> Insert proxy description (Leave empty to keep): ")
            else:
                server_description = input("-> Insert proxy description: ")
            if server_description:
                settings.set_proxy_description(server_description, alias)

       # if not only_missing or (not current_affinity and first_time):
       #     if current_affinity:
       #         server_affinity = input("-> Insert proxy affinity (UUID) (Leave empty to keep): ")
       #     else:
       #         server_affinity = input("-> Insert proxy affinity (UUID): ")
       #     if server_affinity:
       #         try:
       #             settings.set_proxy_affinity(uuid.UUID(server_affinity), alias)
       #         except ValueError:
       #             sys.stderr.write("Error: Invalid UUID format\n")
       #             return
    else:
        # Command line mode
        if args.proxy_id:
            try:
                settings.set_proxy_id(uuid.UUID(args.proxy_id), alias)
            except ValueError:
                Console.write_stderr("Error: Invalid UUID format for proxy ID")
                return
        elif not only_missing or not settings.get_proxy_id(alias):
            # Generate new UUID if no ID is provided
            current_id = settings.get_proxy_id(alias)
            if not current_id:
                current_id = uuid.uuid4()
                settings.set_proxy_id(current_id, alias)
                Console.write_stdout(f"Generated new proxy ID: {current_id}")

        if args.proxy_name:
            settings.set_proxy_name(args.proxy_name, alias)
        elif not only_missing or not settings.get_proxy_name(alias):
            pass  # Name is not requested if not in args and only_missing is True

        if args.proxy_desc:
            settings.set_proxy_description(args.proxy_desc, alias)
        elif not only_missing or not settings.get_proxy_description(alias):
            pass  # Description is not requested if not in args and only_missing is True

        #if args.proxy_affinity:
        #    try:
        #        settings.set_proxy_affinity(uuid.UUID(args.proxy_affinity), alias)
        #    except ValueError:
        #        sys.stderr.write("Error: Invalid UUID format for proxy affinity\n")
        #        return
        #elif not only_missing or not settings.get_proxy_affinity(alias):
        #    pass  # Affinity is not requested if not in args and only_missing is True

    Console.write_stdout(f"Proxy settings for alias '{alias}' saved successfully!")


async def main():
    """
    Main entry point for the GEAI proxy CLI.

    :return: int - Exit code (0 for success, 1 for error)
    """
    
    logger.info("Starting GEAI proxy CLI")
    parser = argparse.ArgumentParser(
        description="Proxy CLI between GEAI and MCP servers",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="INSTALL MAN PAGES:\n  To install the manual pages, run:\n    sudo geai-install-man\n  (requires superuser privileges)"
    )
    parser.add_argument("config", type=str, nargs="?", help="Path to the configuration file (JSON/YAML)")
    parser.add_argument("--list-tools", action="store_true", help="List all available tools")
    parser.add_argument("--invoke", type=str, help="Invoke a specific tool in JSON format")
    parser.add_argument("--configure", action="store_true", help="Configure proxy settings")
    parser.add_argument("--proxy-id", type=str, help="Set proxy server ID (UUID)")
    parser.add_argument("--proxy-name", type=str, help="Set proxy server name")
    parser.add_argument("--proxy-desc", type=str, help="Set proxy server description")
    parser.add_argument("--proxy-affinity", type=str, help="Set proxy server affinity (UUID)")
    parser.add_argument("--alias", type=str, help="Set alias for settings section")
    args = parser.parse_args()

    settings = ProxySettingsManager()
    if not args.alias:
        args.alias = ProxySettingsManager.DEFAULT_ALIAS
    else:
        settings.set_current_alias(args.alias)

    Console.write_stdout(f"Using alias: {args.alias}")
    
    only_configure = args.configure
    while True:
        if args.configure or not all([
            settings.get_proxy_id(args.alias),
            settings.get_proxy_name(args.alias),
            settings.get_proxy_description(args.alias),
            settings.get_api_key(args.alias),
            settings.get_base_url(args.alias)
        ]):
            
            if args.alias not in settings.config:
                Console.write_stdout(f"Created new alias '{args.alias}' in the configuration file.","\n\n")
                settings.config.add_section(args.alias)
            else:
                if not args.configure:
                    Console.write_stdout("\nProxy configuration required. Please complete all required fields.","\n\n")
                else:
                    Console.write_stdout("\nProxy configuration.","\n\n")

                if (key := settings.get_api_key(args.alias)):
                    Console.write_stdout(f"API_KEY: {key}")
                if (url := settings.get_base_url(args.alias)):
                    Console.write_stdout(f"BASE_URL: {url}")

            Console.write_stdout("")
            configure_proxy_settings(settings, args, only_missing=not args.configure)
            args.configure = False
        else:
            break

    if only_configure:
        Console.write_stdout("Proxy configuration completed successfully!")
        return 0

    if not args.config:
        Console.write_stderr("Error: MCP servers Configuration file path is required")
        return 1

    servers_cfg = load_config(args.config)
    server_manager = ServerManager(servers_cfg, settings)

    try:
        Console.write_stdout(f"Contacting Globant Enteprise AI at {settings.get_base_url(args.alias)}...","")
        admin_client = AdminClient(api_key=settings.get_api_key(args.alias), base_url=settings.get_base_url(args.alias))
        result = admin_client.validate_api_token()
        if result.get('errors'):
            Console.write_stdout("Invalid API token")
            for error in result.get('errors'):
                Console.write_stderr(f"{error.get('description')}")

            return 1
        else:
            Console.write_stdout(f" Done!")
            Console.write_stdout(f"Organization: {result.get('organizationName')}")
            Console.write_stdout(f"Project: {result.get('projectName')}")
    except Exception as e:
        Console.write_exception("Error:", e, "\n")
        return 1

    await server_manager.start()

    return 0


def cli_entry() -> int:
    """
    CLI entry point.

    :return: int - Exit code (0 for success, 1 for error)
    """
    try:
        return asyncio.run(main())
    except KeyboardInterrupt:
        Console.write_stdout("\nExiting...")
        return 0
    except (RuntimeError, ConnectionError, ValueError) as e:
        Console.write_exception("Error:", e, "\n")
        return 1


if __name__ == "__main__":
    if len(sys.argv) == 1:
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(os.path.dirname(script_dir), "proxy", "sample-mcp-config.json")
        Console.write_stdout(f"Config file path: {config_path}")
        
        sys.argv.extend([config_path])
    sys.exit(cli_entry())
