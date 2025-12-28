# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""CLI command to start AII API server."""


import asyncio
import sys
from typing import List

from aii.api.server import APIServer, server as global_server_var
from aii.api.utils import generate_api_key
from aii.core.engine import AIIEngine
from aii.config.manager import ConfigManager
import aii.api.server as server_module


async def start_api_server(host: str, port: int, api_keys: List[str], verbose: bool = False):
    """
    Start AII API server.

    Args:
        host: Server host (0.0.0.0 for all interfaces)
        port: Server port (8080 default)
        api_keys: List of API keys (auto-generates if empty)
        verbose: Enable verbose logging
    """

    # Set process name for better visibility in Activity Monitor
    try:
        import setproctitle
        setproctitle.setproctitle(f"aii-server [{host}:{port}]")
    except ImportError:
        pass  # Optional dependency - gracefully degrade

    print("🚀 Initializing AII API server...")

    # Initialize config and engine
    from pathlib import Path
    from aii.config.output_config import OutputConfig
    from aii.functions import register_all_functions
    from aii.functions.system.system_functions import HelpFunction, ClarificationFunction

    config_manager = ConfigManager()
    config = config_manager.get_all_config()
    storage_path = Path.home() / ".aii"

    # Create output config
    output_config = OutputConfig()

    # Create engine
    engine = AIIEngine(
        config=config,
        storage_path=storage_path,
        output_config=output_config,
        config_manager=config_manager
    )

    # Register all built-in functions
    register_all_functions(engine.function_registry)
    engine.register_function(HelpFunction())
    engine.register_function(ClarificationFunction())

    # Track initialization status for client guidance
    initialization_status = {
        "llm_provider": False,
        "llm_error": None,
        "web_search": False,
        "web_error": None,
        "mcp_client": False,
        "mcp_error": None
    }

    # Configure LLM provider (same as main.py) with graceful degradation
    try:
        from aii.data.providers.llm_provider import create_llm_provider

        llm_provider_name = config_manager.get("llm.provider")
        llm_model = config_manager.get("llm.model")
        use_pydantic_ai = True  # Use Pydantic AI by default

        # Check if provider is configured
        if not llm_provider_name:
            initialization_status["llm_error"] = "No LLM provider configured. Run 'aii config init' to set up."
        elif llm_provider_name == "gemini":
            api_key = config_manager.get_secret("gemini_api_key")
            if api_key:
                llm_provider = create_llm_provider(
                    "gemini", api_key, llm_model, use_pydantic_ai
                )
                engine.configure(llm_provider=llm_provider)
                initialization_status["llm_provider"] = True
            else:
                initialization_status["llm_error"] = f"Gemini API key not found. Set GEMINI_API_KEY environment variable or run 'aii config provider gemini'."
        elif llm_provider_name == "openai":
            api_key = config_manager.get_secret("openai_api_key")
            if api_key:
                llm_provider = create_llm_provider(
                    "openai", api_key, llm_model, use_pydantic_ai
                )
                engine.configure(llm_provider=llm_provider)
                initialization_status["llm_provider"] = True
            else:
                initialization_status["llm_error"] = f"OpenAI API key not found. Set OPENAI_API_KEY environment variable or run 'aii config provider openai'."
        elif llm_provider_name == "anthropic":
            api_key = config_manager.get_secret("anthropic_api_key")
            if api_key:
                llm_provider = create_llm_provider(
                    "anthropic", api_key, llm_model, use_pydantic_ai
                )
                engine.configure(llm_provider=llm_provider)
                initialization_status["llm_provider"] = True
            else:
                initialization_status["llm_error"] = f"Anthropic API key not found. Set ANTHROPIC_API_KEY environment variable or run 'aii config provider anthropic'."
        elif llm_provider_name == "moonshot":
            api_key = config_manager.get_secret("moonshot_api_key")
            if api_key:
                llm_provider = create_llm_provider(
                    "moonshot", api_key, llm_model, use_pydantic_ai
                )
                engine.configure(llm_provider=llm_provider)
                initialization_status["llm_provider"] = True
            else:
                initialization_status["llm_error"] = f"Moonshot API key not found. Set MOONSHOT_API_KEY environment variable or run 'aii config provider moonshot'."
        elif llm_provider_name == "deepseek":
            api_key = config_manager.get_secret("deepseek_api_key")
            if api_key:
                llm_provider = create_llm_provider(
                    "deepseek", api_key, llm_model, use_pydantic_ai
                )
                engine.configure(llm_provider=llm_provider)
                initialization_status["llm_provider"] = True
            else:
                initialization_status["llm_error"] = f"DeepSeek API key not found. Set DEEPSEEK_API_KEY environment variable or run 'aii config provider deepseek'."

        # Configure web search if enabled
        if config_manager.get("web_search.enabled"):
            try:
                from aii.data.integrations.web_search import create_web_search_client_from_config
                web_client = create_web_search_client_from_config(config_manager)
                engine.configure(web_client=web_client)
                initialization_status["web_search"] = True
            except Exception as e:
                print(f"Warning: Web search disabled: {e}")
                initialization_status["web_error"] = str(e)

        # MCP Configuration (v0.6.0 - Cloud-Compatible Architecture)
        # Server does NOT initialize MCP client (client-side execution only)
        # MCP tools are executed on client, server only does tool selection
        initialization_status["mcp_client"] = False
        initialization_status["mcp_mode"] = "client"  # Client executes tools

        if verbose:
            print("✓ MCP configured (cloud mode - client-side execution)")

    except Exception as e:
        initialization_status["llm_error"] = str(e)
        print(f"⚠️  Warning: Could not initialize all integrations: {e}")
        print("    Some features may not be available.")
        print("    Server will continue with limited functionality.\n")

    # Configure API keys
    if not api_keys:
        # Use default development API key
        default_key = generate_api_key()
        print(f"\n🔑 Using default API key: {default_key}")
        print(f"   (To use custom key: aii serve --api-key YOUR_KEY)")
        print(f"   Example: curl -H 'Aii-API-Key: {default_key}' http://{host if host != '0.0.0.0' else 'localhost'}:{port}/api/status\n")
        api_keys = [default_key]
    else:
        print(f"🔑 Using {len(api_keys)} configured API key(s)\n")

    config_manager.set("api.keys", api_keys)

    # Create server with initialization status
    api_server = APIServer(engine, config_manager, initialization_status)

    # Set global server instance
    server_module.server = api_server

    # Print startup info
    print(f"🚀 AII API server starting...")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   OpenAPI docs: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/docs")
    print(f"   Status: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/api/status")
    print(f"\n✅ Server ready - Press Ctrl+C to stop\n")

    try:
        # Start server
        await api_server.start_server(host, port)
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down server...")
        await api_server.shutdown()
        await engine.shutdown()
        print("✅ Server stopped")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        await api_server.shutdown()
        await engine.shutdown()
        sys.exit(1)


def serve_command_sync(host: str, port: int, api_key: tuple, verbose: bool):
    """Synchronous wrapper for async serve command."""
    try:
        asyncio.run(start_api_server(host, port, list(api_key), verbose))
    except KeyboardInterrupt:
        # Already handled in async function
        pass
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    """Allow running as: python -m aii.cli.serve"""
    import argparse

    parser = argparse.ArgumentParser(description="Start Aii API server")
    parser.add_argument("--host", default="0.0.0.0", help="Server host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=16169, help="Server port (default: 16169)")
    parser.add_argument("--api-key", action="append", dest="api_keys", help="API key (can specify multiple times)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Run server in foreground
    serve_command_sync(
        host=args.host,
        port=args.port,
        api_key=tuple(args.api_keys) if args.api_keys else (),
        verbose=args.verbose
    )
