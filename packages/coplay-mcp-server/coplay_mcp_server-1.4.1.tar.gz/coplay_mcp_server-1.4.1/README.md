# Coplay MCP Server

A Model Context Protocol (MCP) server for Coplay, providing Unity Editor integration capabilities through MCP tools.

## Features

- **Schema-Based Tool Registration**: Dynamically registers tools from JSON schema files, ensuring compatibility with Backend's AssistantMode.NORMAL
- **Unity Project Discovery**: Automatically discover running Unity Editor instances and their project roots
- **Unity Editor State**: Retrieve current Unity Editor state and scene hierarchy information
- **Script Execution**: Execute arbitrary C# scripts within the Unity Editor
- **Log Management**: Access and filter Unity console logs
- **GameObject Hierarchy**: List and filter GameObjects in the scene hierarchy
- **Task Creation**: Create new Coplay tasks directly from MCP clients
- **Parameter Validation**: Automatic parameter validation and type conversion based on tool schemas
- **Version Compatibility**: Tools are locked to specific schema versions, ensuring compatibility with Unity plugin versions

## Usage

### As an MCP server

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "coplay-mcp": {
      "autoApprove": [],
      "disabled": false,
      "timeout": 60,
      "type": "stdio",
      "command": "uvx",
      "args": [
        "coplay-mcp-server@latest"
      ]
    }
  }
}
```


