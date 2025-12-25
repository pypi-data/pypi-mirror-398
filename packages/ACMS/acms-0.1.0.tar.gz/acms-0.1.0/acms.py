#!/usr/bin/env python3
"""
This MCP server provides programmatic access to Apple's container CLI tool on macOS.
It wraps the `container` command-line tool and exposes it through the MCP protocol.

Usage:
  python3 acms.py --port 8765              # HTTP server on port 8765
  python3 acms.py --ssl --port 8443        # HTTPS server with SSL on port 8443
"""

from typing import Optional, List
import argparse
import logging
import asyncio
import shutil
import sys
import os

from fastmcp.server.auth.providers.azure import AzureProvider
from dotenv import load_dotenv
import uvicorn
import fastmcp

from tools.registry import registry

# Load environment variables
load_dotenv()

# Configure enhanced logging to stderr to avoid interfering with stdio communication
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - [PID:%(process)d] [%(funcName)s:%(lineno)d] - %(message)s",
    stream=sys.stderr,
    force=True,  # Ensure our config overrides any existing config
)
logger = logging.getLogger("ACMS")

# Set up logging levels - reduce noise from third-party libraries
logging.getLogger("uvicorn").setLevel(logging.INFO)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("uvicorn.error").setLevel(logging.INFO)
logging.getLogger("uvicorn.asgi").setLevel(logging.WARNING)
logging.getLogger("uvicorn.protocols").setLevel(logging.WARNING)
logging.getLogger("uvicorn.protocols.http").setLevel(logging.WARNING)
logging.getLogger("fastmcp").setLevel(logging.INFO)
logging.getLogger("mcp").setLevel(logging.INFO)
logging.getLogger("mcp.server.lowlevel.server").setLevel(logging.WARNING)
logging.getLogger("mcp.server.streamable_http").setLevel(logging.WARNING)
logging.getLogger("mcp.server.streamable_http_manager").setLevel(logging.INFO)
logging.getLogger("starlette").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)
logging.getLogger("sse_starlette").setLevel(logging.WARNING)
logging.getLogger("sse_starlette.sse").setLevel(logging.WARNING)

# Force all loggers to use our stderr handler with consistent format
for logger_name in [
    "uvicorn",
    "uvicorn.access",
    "uvicorn.error",
    "uvicorn.asgi",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "fastmcp",
    "mcp",
    "mcp.server.lowlevel.server",
    "mcp.server.streamable_http",
    "mcp.server.streamable_http_manager",
    "starlette",
    "sse_starlette",
    "sse_starlette.sse",
]:
    specific_logger = logging.getLogger(logger_name)
    specific_logger.handlers.clear()
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - [PID:%(process)d] - %(message)s"
        )
    )
    specific_logger.addHandler(stderr_handler)
    specific_logger.propagate = False


def check_container_available() -> bool:
    """
    Check if the container CLI tool is available.
    """
    available: bool = shutil.which("container") is not None
    logger.info(f"Container CLI availability check: {available}")

    return available


def create_fastmcp_server(
    enable_auth: bool = False,
    resource_server_url: Optional[str] = None,
    required_scopes: Optional[List[str]] = None,
) -> fastmcp.FastMCP:
    """
    Create a FastMCP server with container tools.

    Args:
        enable_auth: Enable OAuth 2.1 authentication with Microsoft Entra ID
        resource_server_url: URL of this MCP server
        required_scopes: List of OAuth scopes required for authentication

    Returns:
        FastMCP server instance with optional OAuth authentication
    """

    logger.info("Creating FastMCP server instance...")

    # Configure OAuth authentication if enabled
    if enable_auth:
        try:
            # Get Azure configuration from environment variables
            tenant_id = os.getenv("ENTRA_TENANT_ID")
            client_id = os.getenv("ENTRA_CLIENT_ID")
            client_secret = os.getenv("ENTRA_CLIENT_SECRET")
            env_scopes = os.getenv("ENTRA_REQUIRED_SCOPES")

            if not tenant_id:
                raise ValueError("ENTRA_TENANT_ID environment variable is required")
            if not client_id:
                raise ValueError("ENTRA_CLIENT_ID environment variable is required")
            if not client_secret:
                raise ValueError("ENTRA_CLIENT_SECRET environment variable is required")
            if not env_scopes:
                raise ValueError("ENTRA_REQUIRED_SCOPES environment variable is required")

            if env_scopes:
                # Parse scopes from environment (comma or space separated)
                scopes_list = [s.strip() for s in env_scopes.replace(",", " ").split() if s.strip()]
            elif required_scopes:
                scopes_list = required_scopes
            else:
                raise ValueError(
                    "At least one scope must be specified via ENTRA_REQUIRED_SCOPES or --required-scopes"
                )
            logger.info(client_id)
            # Create AzureProvider with configuration
            auth_provider = AzureProvider(
                client_id=client_id,
                client_secret=client_secret,
                tenant_id=tenant_id,
                base_url=resource_server_url
                or os.getenv("MCP_SERVER_BASE_URL", "http://localhost:8765"),
                required_scopes=scopes_list,
            )

            logger.info(f"  Resource Server URL: {resource_server_url or 'http://localhost:8765'}")
            logger.info(f"  Required Scopes: {required_scopes or []}")

            # Create FastMCP with OAuth
            mcp = fastmcp.FastMCP("ACMS", auth=auth_provider)

            logger.info("FastMCP server created with OAuth authentication")

        except Exception as e:
            logger.error(f"Failed to initialize OAuth authentication: {e}", exc_info=True)
            logger.critical("Cannot start server without valid OAuth configuration. Exiting.")
            sys.exit(1)
    else:
        mcp = fastmcp.FastMCP("ACMS")

    # Register all tools from the modular structure
    tool_count = registry.register_all(mcp)
    logger.info(f"Registered {tool_count} tools from modular structure")

    # Create a custom connection logger that will track all MCP connections
    connection_logger = logging.getLogger("mcp-connections")
    connection_logger.info("Connection logger initialized")

    return mcp


def parse_arguments():
    """Parse command line arguments for ACMS server configuration."""
    parser = argparse.ArgumentParser(
        description="Apple Container MCP Server (ACMS)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 acms.py --ssl --port 8443        # HTTPS server with SSL on port 8443
  python3 acms.py --host 127.0.0.1   # HTTP server on localhost""",
    )

    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=8765,
        help="Port to bind the server to (default: 8765)",
    )

    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host/IP to bind the server to (default: 127.0.0.1)",
    )

    parser.add_argument(
        "--ssl",
        action="store_true",
        help="Enable SSL/TLS (HTTPS) mode. Requires server.crt and server.key in current directory",
    )

    parser.add_argument(
        "--cert-file",
        type=str,
        default="server.crt",
        help="Path to SSL certificate file (default: server.crt)",
    )

    parser.add_argument(
        "--key-file",
        type=str,
        default="server.key",
        help="Path to SSL private key file (default: server.key)",
    )

    parser.add_argument(
        "--http",
        type=int,
        dest="port",
        help="Legacy: specify port for HTTP mode (same as --port)",
    )

    parser.add_argument(
        "--enable-auth",
        action="store_true",
        help="Enable OAuth 2.1 authentication with Microsoft Entra ID (requires .env configuration)",
    )

    parser.add_argument(
        "--resource-url",
        type=str,
        help="Resource server URL for OAuth identification (default: http://127.0.0.1:PORT)",
    )

    parser.add_argument(
        "--required-scopes",
        type=str,
        nargs="*",
        help="Required OAuth scopes for authentication (space-separated)",
    )

    return parser.parse_args()


async def main() -> None:
    logger.info("=" * 50)
    logger.info("Starting Apple Container MCP Server (ACMS)")
    logger.info("=" * 50)

    # Parse command line arguments
    args = parse_arguments()

    port = args.port
    host = args.host
    use_ssl = args.ssl
    cert_file = args.cert_file
    key_file = args.key_file
    enable_auth = args.enable_auth
    required_scopes = args.required_scopes if args.required_scopes else []

    # Determine resource server URL
    protocol = "https" if use_ssl else "http"
    resource_url = args.resource_url if args.resource_url else f"{protocol}://{host}:{port}"

    # Log environment info
    if not check_container_available():
        logger.critical("container CLI not found. Please install Apple's container tool.")
        logger.critical("See: https://github.com/apple/container for installation instructions.")

    # Validate SSL configuration if SSL is enabled
    if use_ssl:
        if not os.path.isfile(cert_file):
            logger.critical(f"SSL certificate file not found: {cert_file}")
            logger.critical(
                "Please ensure the certificate file exists or use --cert-file to specify the correct path"
            )
            sys.exit(1)

        if not os.path.isfile(key_file):
            logger.critical(f"SSL private key file not found: {key_file}")
            logger.critical(
                "Please ensure the private key file exists or use --key-file to specify the correct path"
            )
            sys.exit(1)

        logger.info(f"SSL enabled - using cert: {cert_file}, key: {key_file}")

    logger.info(f"ACMS: {resource_url}/mcp")

    try:
        # Create FastMCP server with optional OAuth authentication
        mcp = create_fastmcp_server(
            enable_auth=enable_auth,
            resource_server_url=resource_url,
            required_scopes=required_scopes,
        )

        # Get the HTTP app
        app = mcp.http_app()

        # Uvicorn config with consistent logging
        config_kwargs = {
            "app": app,
            "host": host,
            "port": port,
            "log_level": "info",
            "access_log": True,
            "use_colors": True,
            "loop": "asyncio",
            "ws": "websockets-sansio",
        }

        # Add SSL configuration if enabled
        if use_ssl:
            config_kwargs.update({"ssl_certfile": cert_file, "ssl_keyfile": key_file})
            logger.info(f"SSL configuration: certfile={cert_file}, keyfile={key_file}")

        config = uvicorn.Config(**config_kwargs)

        # Create and run server
        server = uvicorn.Server(config)

        # Run the server (this blocks until shutdown)
        await server.serve()

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down gracefully")
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        raise
    finally:
        logger.info("ACMS shutdown complete")


def cli_main():
    """Entry point for the pip-installed acms command."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server stopped by user", file=sys.stderr)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        raise


if __name__ == "__main__":
    cli_main()
