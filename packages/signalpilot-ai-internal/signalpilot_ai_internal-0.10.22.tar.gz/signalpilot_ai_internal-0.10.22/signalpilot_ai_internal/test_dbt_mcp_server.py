"""
Test script to run the dbt-mcp server with enhanced visibility.

This script provides detailed logging and output to help debug
and understand what's happening when the MCP server runs.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the dbt-mcp src directory to Python path
dbt_mcp_src = Path(__file__).parent / "dbt-mcp" / "src"
sys.path.insert(0, str(dbt_mcp_src))

from dbt_mcp.config.config import load_config
from dbt_mcp.config.transport import validate_transport
from dbt_mcp.mcp.server import create_dbt_mcp


def setup_logging():
    """Configure detailed logging for debugging."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('dbt_mcp_test.log', mode='w')
        ]
    )
    
    # Set specific loggers to DEBUG
    logging.getLogger('dbt_mcp').setLevel(logging.DEBUG)
    logging.getLogger('mcp').setLevel(logging.DEBUG)
    
    return logging.getLogger(__name__)


async def test_server_creation():
    """Test creating the dbt-mcp server."""
    logger = setup_logging()
    
    logger.info("=" * 80)
    logger.info("Starting dbt-mcp Server Test")
    logger.info("=" * 80)
    
    try:
        # Load configuration
        logger.info("\n--- Loading Configuration ---")
        logger.info(f"Current working directory: {os.getcwd()}")
        logger.info(f"Environment variables (DBT related):")
        for key, value in os.environ.items():
            if 'DBT' in key.upper() or 'MCP' in key.upper():
                logger.info(f"  {key}: {value}")
        
        config = load_config()
        logger.info(f"Config loaded successfully")
        logger.info(f"  Enabled toolsets: {config.enabled_toolsets}")
        logger.info(f"  Disabled toolsets: {config.disabled_toolsets}")
        logger.info(f"  Enabled tools: {config.enable_tools}")
        logger.info(f"  Disabled tools: {config.disable_tools}")
        
        # Create server
        logger.info("\n--- Creating MCP Server ---")
        server = await create_dbt_mcp(config)
        logger.info(f"Server created: {server}")
        logger.info(f"Server name: {server.name}")
        
        # List registered tools
        logger.info("\n--- Registered Tools ---")
        if hasattr(server, '_tool_manager') and hasattr(server._tool_manager, 'tools'):
            tools = server._tool_manager.tools
            logger.info(f"Total tools registered: {len(tools)}")
            for tool_name in sorted(tools.keys()):
                logger.info(f"  - {tool_name}")
        else:
            logger.warning("Could not access tool manager to list tools")
        
        # List registered prompts (if any)
        logger.info("\n--- Registered Prompts ---")
        if hasattr(server, '_prompt_manager') and hasattr(server._prompt_manager, 'prompts'):
            prompts = server._prompt_manager.prompts
            logger.info(f"Total prompts registered: {len(prompts)}")
            for prompt_name in sorted(prompts.keys()):
                logger.info(f"  - {prompt_name}")
        else:
            logger.info("No prompts registered")
        
        # Get transport type
        logger.info("\n--- Transport Configuration ---")
        transport_type = os.environ.get("MCP_TRANSPORT", "stdio")
        transport = validate_transport(transport_type)
        logger.info(f"Transport type: {transport}")
        
        logger.info("\n" + "=" * 80)
        logger.info("Server initialization complete!")
        logger.info("=" * 80)
        logger.info("\nTo run the server, uncomment the server.run() line below")
        logger.info("Note: server.run() will block and wait for MCP client connections")
        
        # Uncomment the line below to actually run the server
        # logger.info("\n--- Running Server (blocking) ---")
        # server.run(transport=transport)
        
        return server
        
    except Exception as e:
        logger.error(f"\n!!! Error occurred: {e}", exc_info=True)
        raise


async def test_tool_call():
    """Test calling a specific tool if available."""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("\n" + "=" * 80)
        logger.info("Testing Tool Call")
        logger.info("=" * 80)
        
        config = load_config()
        server = await create_dbt_mcp(config)
        
        # Try to call a simple tool (e.g., list or search)
        # This is just an example - adjust based on available tools
        if hasattr(server, '_tool_manager') and hasattr(server._tool_manager, 'tools'):
            tools = server._tool_manager.tools
            
            # Look for a simple tool to test
            test_tools = ['search', 'list', 'get_all_models']
            for tool_name in test_tools:
                if tool_name in tools:
                    logger.info(f"\nTesting tool: {tool_name}")
                    try:
                        # Call with minimal arguments
                        result = await server.call_tool(tool_name, {})
                        logger.info(f"Tool call successful!")
                        logger.info(f"Result type: {type(result)}")
                        logger.info(f"Result: {result}")
                        break
                    except Exception as tool_error:
                        logger.warning(f"Tool call failed (expected if missing config): {tool_error}")
            else:
                logger.info("No testable tools found in the expected list")
        
    except Exception as e:
        logger.error(f"Error in tool test: {e}", exc_info=True)


def main():
    """Main entry point."""
    logger = setup_logging()
    
    try:
        # Test 1: Create server and inspect
        logger.info("\n### TEST 1: Server Creation and Inspection ###\n")
        server = asyncio.run(test_server_creation())
        
        # Test 2: Try calling a tool (optional)
        logger.info("\n\n### TEST 2: Tool Call Test (Optional) ###\n")
        try:
            asyncio.run(test_tool_call())
        except Exception as e:
            logger.info(f"Tool test skipped or failed: {e}")
        
        logger.info("\n\n" + "=" * 80)
        logger.info("All tests complete! Check dbt_mcp_test.log for full output.")
        logger.info("=" * 80)
        
    except KeyboardInterrupt:
        logger.info("\n\nInterrupted by user")
    except Exception as e:
        logger.error(f"\n\nFatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
