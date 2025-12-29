"""Build hooks for Hatchling to run code generation before building."""

import logging
import sys
from pathlib import Path
from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    """Custom build hook to run code generation before building."""
    
    PLUGIN_NAME = 'custom'
    
    def initialize(self, version, build_data):
        """Initialize build hook - run code generation before building."""
        print("Running MCP tool code generation as pre-build step...")
        
        try:
            # Import and run the code generator
            sys.path.insert(0, str(Path(__file__).parent))
            from coplay_mcp_server.code_generator import MCPToolCodeGenerator
            
            # Set up logging for the build process
            logging.basicConfig(level=logging.INFO, format="[BUILD] %(message)s")
            
            # Run code generation
            generator = MCPToolCodeGenerator()
            generator.generate_all_tools()
            
            print("MCP tool code generation completed successfully!")
            
        except Exception as e:
            print(f"Error during code generation: {e}")
            # Don't fail the build if code generation fails, just warn
            print("Warning: Code generation failed, using existing generated files if available")
    
    def finalize(self, version, build_data, artifact_path):
        """Finalize build hook - cleanup if needed."""
        pass
