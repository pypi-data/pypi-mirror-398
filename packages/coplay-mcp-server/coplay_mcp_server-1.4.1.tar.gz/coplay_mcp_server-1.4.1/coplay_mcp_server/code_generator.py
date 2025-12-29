"""Code generator for MCP tools from JSON schema files."""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class MCPToolCodeGenerator:
    """Generates Python code for MCP tools from JSON schema files."""

    def __init__(self, backend_path: Optional[Path] = None):
        """Initialize the code generator.

        Args:
            backend_path: Path to the Backend directory. If None, will try to find it automatically.
        """
        self.backend_path = backend_path or self._find_backend_path()
        self.generated_tools_path = Path(__file__).parent / "generated_tools"

        # Schema files to process (from Backend/coplay/tool_schemas/)
        self.SCHEMA_FILES = [
            "unity_functions_schema.json",
            "image_tool_schema.json",
            "coplay_tool_schema.json",
            "agent_tool_schema.json",
            "package_tool_schema.json",
            "input_action_tool_schema.json",
            "ui_functions_schema.json",
            "snapping_functions_schema.json",
            "scene_view_functions_schema.json",
            "profiler_functions_schema.json",
            "screenshot_tool_schema.json",
        ]

    def _find_backend_path(self) -> Path:
        """Try to find the Backend directory automatically."""
        current_path = Path(__file__).parent

        # Look for Backend directory in parent directories
        for parent in [current_path] + list(current_path.parents):
            backend_path = parent / "Backend"
            if (
                backend_path.exists()
                and (backend_path / "coplay" / "tool_schemas").exists()
            ):
                return backend_path

        # Fallback to relative path
        return Path("../Backend")

    def generate_all_tools(self) -> None:
        """Generate Python files for all schema files."""
        logger.info("Starting MCP tool code generation")

        tool_schemas_path = self.backend_path / "coplay" / "tool_schemas"
        if not tool_schemas_path.exists():
            logger.error(f"Tool schemas directory not found: {tool_schemas_path}")
            return

        total_tools = 0
        for schema_file in self.SCHEMA_FILES:
            schema_path = tool_schemas_path / schema_file
            if schema_path.exists():
                tools_count = self.generate_tools_from_schema(schema_path)
                total_tools += tools_count
                logger.info(f"Generated {tools_count} tools from {schema_file}")
            else:
                logger.warning(f"Schema file not found: {schema_path}")

        logger.info(f"Total tools generated: {total_tools}")

    def generate_tools_from_schema(self, schema_path: Path) -> int:
        """Generate Python file for a single schema file.

        Args:
            schema_path: Path to the JSON schema file

        Returns:
            Number of tools generated
        """
        try:
            schema_data = json.loads(schema_path.read_text(encoding="utf-8"))

            if not isinstance(schema_data, list):
                logger.error(f"Schema {schema_path.name} is not a list format")
                return 0

            # Generate Python file name from schema file name
            python_file_name = schema_path.stem.replace("_schema", "_tools") + ".py"
            output_path = self.generated_tools_path / python_file_name

            # Generate Python code
            python_code = self._generate_python_file(schema_data, schema_path.stem)

            # Write to file
            output_path.write_text(python_code, encoding="utf-8")

            # Count tools
            tools_count = len(
                [tool for tool in schema_data if tool.get("type") == "function"]
            )
            return tools_count

        except Exception as e:
            logger.error(f"Error generating tools from {schema_path}: {e}")
            return 0

    def _generate_python_file(
        self, schema_data: List[Dict[str, Any]], schema_name: str
    ) -> str:
        """Generate Python code for a schema file.

        Args:
            schema_data: List of tool definitions from schema
            schema_name: Name of the schema file (without extension)

        Returns:
            Generated Python code as string
        """
        lines = []

        # File header
        lines.append(f'"""Generated MCP tools from {schema_name}.json"""')
        lines.append("")
        lines.append("import logging")
        lines.append("from typing import Annotated, Optional, Any, Dict, Literal")
        lines.append("from pydantic import Field")
        lines.append("from fastmcp import FastMCP")
        lines.append("from ..unity_client import UnityRpcClient")
        lines.append("")
        lines.append("logger = logging.getLogger(__name__)")
        lines.append("")
        lines.append("# Global references to be set by register_tools")
        lines.append("_mcp: Optional[FastMCP] = None")
        lines.append("_unity_client: Optional[UnityRpcClient] = None")
        lines.append("")
        lines.append("")

        # Generate function for each tool
        for tool_def in schema_data:
            if tool_def.get("type") != "function":
                continue

            function_def = tool_def.get("function")
            if not function_def:
                continue

            tool_code = self._generate_tool_function(function_def)
            lines.extend(tool_code)
            lines.append("")

        # Registration function
        lines.append(
            "def register_tools(mcp: FastMCP, unity_client: UnityRpcClient) -> None:"
        )
        lines.append(
            f'    """Register all tools from {schema_name} with the MCP server."""'
        )
        lines.append("    global _mcp, _unity_client")
        lines.append("    _mcp = mcp")
        lines.append("    _unity_client = unity_client")
        lines.append("")

        # Register each tool function
        for tool_def in schema_data:
            if tool_def.get("type") != "function":
                continue

            function_def = tool_def.get("function")
            if not function_def:
                continue

            tool_name = function_def.get("name", "")
            lines.append(f"    # Register {tool_name}")
            lines.append(f"    mcp.tool()({tool_name})")

        lines.append("")

        return "\n".join(lines)

    def _generate_tool_function(self, func_def: Dict[str, Any]) -> List[str]:
        """Generate Python function code for a single tool.

        Args:
            func_def: Function definition from schema

        Returns:
            List of code lines
        """
        lines = []

        tool_name = func_def.get("name", "")
        description = func_def.get("description", "")
        parameters = func_def.get("parameters", {})

        properties = parameters.get("properties", {})
        required = parameters.get("required", [])

        # Function signature (no decorator at module level)
        lines.append(f"async def {tool_name}(")

        # Parameters - separate required and optional to avoid syntax errors
        required_params = []
        optional_params = []

        for param_name, param_def in properties.items():
            param_description = param_def.get("description", "")
            is_required = param_name in required

            # Convert JSON schema type to Python type with Annotated description
            python_type = self._get_python_type_annotation(
                param_def, param_description, is_required
            )

            if is_required:
                required_params.append(f"    {param_name}: {python_type},")
            else:
                optional_params.append(f"    {param_name}: {python_type} = None,")

        # Add required parameters first, then optional parameters
        lines.extend(required_params)
        lines.extend(optional_params)
        lines.append(") -> Any:")

        # Docstring
        lines.append(f'    """{description}"""')
        lines.append("    try:")
        lines.append(
            f'        logger.debug(f"Executing {tool_name} with parameters: {{locals()}}")'
        )
        lines.append("")
        lines.append("        # Prepare parameters for Unity RPC call")
        lines.append("        params = {}")

        # Parameter preparation
        for param_name in properties.keys():
            lines.append(f"        if {param_name} is not None:")
            lines.append(f"            params['{param_name}'] = str({param_name})")

        lines.append("")
        lines.append("        # Execute Unity RPC call")
        lines.append(
            f"        result = await _unity_client.execute_request('{tool_name}', params)"
        )
        lines.append(f'        logger.debug(f"{tool_name} completed successfully")')
        lines.append("        return result")
        lines.append("")
        lines.append("    except Exception as e:")
        lines.append(f'        logger.error(f"Failed to execute {tool_name}: {{e}}")')
        lines.append(
            f'        raise RuntimeError(f"Tool execution failed for {tool_name}: {{e}}")'
        )
        lines.append("")

        return lines

    def _get_single_type(self, param_type: str) -> str:
        """Convert a single JSON schema type to Python type.

        Args:
            param_type: JSON schema type string

        Returns:
            Python type string
        """
        type_mapping = {
            "string": "str",
            "integer": "int",
            "number": "float",
            "boolean": "bool",
            "array": "list",
            "object": "dict",
        }
        return type_mapping.get(param_type, "Any")

    def _get_python_union_type(self, param_types: list) -> str:
        """Convert JSON schema union types to Python union syntax.

        Args:
            param_types: List of JSON schema types

        Returns:
            Python union type string using modern | syntax
        """
        python_types = []
        has_null = False

        for param_type in param_types:
            if param_type == "null":
                has_null = True
            else:
                python_types.append(self._get_single_type(param_type))

        # Remove duplicates while preserving order
        seen = set()
        unique_types = []
        for t in python_types:
            if t not in seen:
                seen.add(t)
                unique_types.append(t)

        # Build the union type
        if len(unique_types) == 0:
            return "None" if has_null else "Any"
        elif len(unique_types) == 1:
            base_type = unique_types[0]
            return f"{base_type} | None" if has_null else base_type
        else:
            union_type = " | ".join(unique_types)
            return f"{union_type} | None" if has_null else union_type

    def _get_python_type_annotation(
        self, param_def: Dict[str, Any], description: str, is_required: bool
    ) -> str:
        """Get Python type annotation with description for a parameter.

        Args:
            param_def: Full parameter definition from JSON schema
            description: Parameter description
            is_required: Whether parameter is required

        Returns:
            Python type annotation string
        """
        param_type = param_def.get("type", "string")
        enum_values = param_def.get("enum")

        # Handle enum values - create Literal type
        if enum_values:
            # Create literal values, properly quoted for strings
            literal_values = []
            for value in enum_values:
                if isinstance(value, str):
                    literal_values.append(f"'{value}'")
                else:
                    literal_values.append(str(value))

            base_type = f"Literal[{', '.join(literal_values)}]"

            # Handle union types with enum (e.g., ["string", "null"] with enum)
            if isinstance(param_type, list) and "null" in param_type:
                base_type = f"{base_type} | None"
        else:
            # Handle regular types without enum
            if isinstance(param_type, list):
                base_type = self._get_python_union_type(param_type)
            else:
                base_type = self._get_single_type(param_type)

        # Add | None for optional parameters (not in required list)
        if not is_required and not base_type.endswith("| None"):
            base_type = f"{base_type} | None"

        # Create annotated type with Field(description=...) for proper MCP parameter descriptions
        return f'Annotated[\n        {base_type},\n        Field(\n            description="""{description}"""\n        ),\n    ]'


def main():
    """Main function to generate all MCP tools."""
    logging.basicConfig(level=logging.INFO)

    generator = MCPToolCodeGenerator()
    generator.generate_all_tools()


if __name__ == "__main__":
    main()
