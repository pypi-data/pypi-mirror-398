# MCP Tool Code Generation

This document explains the automated code generation system for MCP tools from JSON schema files.

## Overview

The Coplay MCP Server uses an automated code generation approach to expose tool functions with proper parameter descriptions. Instead of manually defining each tool, we generate Python functions from JSON schema files located in the Backend project.

## How It Works

1. **Schema Source**: Tool schemas are read from `Backend/coplay/tool_schemas/` directory
2. **Code Generation**: The `code_generator.py` script processes these schemas and generates Python files
3. **Parameter Descriptions**: Each parameter gets proper `Annotated` type hints with descriptions from the schema
4. **MCP Registration**: Generated functions are automatically registered with the MCP server

## Generated Files

Generated files are located in `coplay_mcp_server/generated_tools/` and include:

- `unity_functions_tools.py` - Unity Editor manipulation tools (34 tools)
- `image_tool_tools.py` - Image generation and editing tools (1 tool)
- `coplay_tool_tools.py` - Coplay-specific tools (1 tool)
- `agent_tool_tools.py` - Agent management tools (6 tools)
- `package_tool_tools.py` - Unity package management (7 tools)
- `input_action_tool_tools.py` - Unity Input System tools (13 tools)
- `ui_functions_tools.py` - Unity UI tools (6 tools)
- `snapping_functions_tools.py` - Object snapping tools (4 tools)
- `scene_view_functions_tools.py` - Scene view controls (1 tool)
- `profiler_functions_tools.py` - Unity Profiler tools (2 tools)
- `screenshot_tool_tools.py` - Screenshot capture tools (2 tools)

**Total: 85 tools generated**

## Automatic Code Generation

### Pre-Build Hook

Code generation runs automatically during the build process via a Hatchling build hook:

```bash
# When building the package, tools are automatically generated
uv build
```

### Manual Generation

You can also run code generation manually:

```bash
# Using the script command
uv run coplay-generate-tools

# Or directly
uv run python -m coplay_mcp_server.code_generator
```

## Generated Code Structure

Each generated tool function follows this pattern:

```python
async def create_gameobject(
    name: Annotated[str, """The name of the new GameObject."""],
    primitive_type: Annotated[Optional[str], """Optional. Type of primitive to create."""] = None,
    position: Annotated[str, """Comma-separated position coordinates (e.g., 'x,y,z')."""],
    # ... more parameters
) -> Any:
    """Creates a new GameObject in the Unity scene."""
    try:
        # Parameter validation and Unity RPC call
        params = {}
        if name is not None:
            params['name'] = str(name)
        # ... prepare other parameters
        
        result = await _unity_client.execute_request('create_gameobject', params)
        return result
    except Exception as e:
        raise RuntimeError(f"Tool execution failed for create_gameobject: {e}")
```

## Key Features

### Parameter Descriptions
- Each parameter uses `Annotated[Type, """description"""]` for rich type information
- Descriptions come directly from the JSON schema files
- Required vs optional parameters are properly handled
- Parameter ordering ensures required parameters come before optional ones

### Error Handling
- Comprehensive try/catch blocks for each tool
- Detailed error messages with tool name and context
- Graceful fallback if Unity client is unavailable

### Logging
- Debug logging for tool execution
- Parameter logging for troubleshooting
- Build-time logging for code generation process

## Schema File Format

The code generator expects JSON schema files in this format:

```json
[
  {
    "type": "function",
    "function": {
      "name": "create_gameobject",
      "description": "Creates a new GameObject in the Unity scene.",
      "parameters": {
        "type": "object",
        "properties": {
          "name": {
            "type": "string",
            "description": "The name of the new GameObject."
          },
          "position": {
            "type": "string", 
            "description": "Comma-separated position coordinates (e.g., 'x,y,z')."
          }
        },
        "required": ["name", "position"]
      }
    }
  }
]
```

## Adding New Tools

To add new tools:

1. **Update Schema**: Add your tool definition to the appropriate JSON schema file in `Backend/coplay/tool_schemas/`
2. **Regenerate**: Run `uv run coplay-generate-tools` or build the package
3. **Test**: The new tool will be automatically available in the MCP server

## Configuration

The code generator can be configured by modifying `coplay_mcp_server/code_generator.py`:

- `SCHEMA_FILES`: List of schema files to process
- `_find_backend_path()`: Logic for finding the Backend directory
- Type mapping in `_get_python_type_annotation()`

## Benefits

1. **Single Source of Truth**: Schema files in Backend project define all tools
2. **Rich Parameter Descriptions**: MCP clients can show detailed parameter help
3. **Type Safety**: Proper Python type hints for better IDE support
4. **Automatic Updates**: Tools stay in sync with schema changes
5. **Build Integration**: No manual steps required for deployment
6. **Maintainability**: Centralized tool definitions reduce duplication

## Troubleshooting

### Code Generation Fails
- Check that Backend directory exists and contains `coplay/tool_schemas/`
- Verify schema files are valid JSON
- Check build logs for specific error messages

### Missing Tools
- Ensure the schema file is listed in `SCHEMA_FILES`
- Verify the schema follows the expected format
- Check that `register_tools()` is called in `server.py`

### Parameter Issues
- Verify parameter types in schema match expected Python types
- Check required vs optional parameter definitions
- Ensure parameter descriptions don't contain problematic characters
