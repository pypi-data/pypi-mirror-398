# OpsBeacon Python SDK

A comprehensive Python SDK for interacting with the OpsBeacon API, including support for command execution, MCP (Model Context Protocol) triggers, policy management, and more.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Authentication](#authentication)
- [Base URLs](#base-urls)
- [REST API Endpoints](#rest-api-endpoints)
  - [Commands](#commands)
  - [Connections](#connections)
  - [Execution Policies](#execution-policies)
  - [MCP Triggers](#mcp-triggers)
  - [Users](#users)
  - [Groups](#groups)
  - [Files](#files)
- [MCP Protocol](#mcp-protocol)
- [Python SDK Usage Examples](#python-sdk-usage-examples)
- [API Reference](#api-reference)
- [Error Handling](#error-handling)

## Installation

To install the OpsBeacon Python client, you can use pip:

```bash
pip install opsbeacon
```

Or install directly from GitHub:

```bash
pip install git+https://github.com/ob2ai/ob-python-sdk.git
```

For development:

```bash
git clone https://github.com/ob2ai/ob-python-sdk.git
cd ob-python-sdk
pip install -e .
```

## Quick Start

```python
from opsbeacon import OpsBeaconClient

# Initialize client
client = OpsBeaconClient(
    api_domain="api.console.opsbeacon.com",
    api_token="your-api-token"
)

# Execute a command
result = client.run(
    command="df",
    connection="devcontroller",
    args=["-h"]
)
print(result["output"])
```

## Authentication

All API requests require authentication using a Bearer token in the Authorization header:

```http
Authorization: Bearer YOUR_API_TOKEN
Content-Type: application/json
```

### Environment Variables

The SDK can use environment variables for configuration:

```bash
export OPSBEACON_API_DOMAIN="api.console.opsbeacon.com"
export OPSBEACON_API_TOKEN="your-api-token"
```

```python
from opsbeacon import OpsBeaconClient

# Client will use environment variables
client = OpsBeaconClient()
```

## Base URLs

```
Production: https://api.console.opsbeacon.com
Development: https://api.console-dev.opsbeacon.com
```

## REST API Endpoints

### Commands

#### List All Commands

**Endpoint:** `GET /workspace/v2/commands`

**Description:** Retrieve all commands available in the workspace

**Response Example:**
```json
{
  "commands": [
    {
      "name": "df",
      "description": "Check disk usage",
      "arguments": [],
      "kind": "shell"
    },
    {
      "name": "ps",
      "description": "List processes",
      "arguments": ["aux"],
      "kind": "shell"
    }
  ]
}
```

#### Execute Command

**Endpoint:** `POST /trigger/v1/api`

**Description:** Execute a command on a specific connection

**Request Body:**
```json
{
  "command": "df",
  "connection": "devcontroller",
  "arguments": ["-h"]
}
```

**Response Example:**
```json
{
  "success": true,
  "output": "Filesystem      Size  Used Avail Use% Mounted on\n/dev/sda1        50G   30G   20G  60% /",
  "exitCode": 0,
  "executionId": "abc123-def456-ghi789"
}
```

### Connections

#### List All Connections

**Endpoint:** `GET /workspace/v2/connections`

**Description:** Retrieve all connections in the workspace

**Response Example:**
```json
{
  "connections": [
    {
      "name": "devcontroller",
      "kind": "ssh",
      "status": "online",
      "lastSeen": "2025-01-06T10:30:00Z"
    },
    {
      "name": "prod-server",
      "kind": "agent",
      "status": "online",
      "lastSeen": "2025-01-06T10:29:45Z"
    }
  ]
}
```

### Execution Policies

#### List All Policies

**Endpoint:** `GET /workspace/v2/policy`

**Description:** Retrieve all execution policies in the workspace

**Response Example:**
```json
{
  "policies": [
    {
      "name": "dev-policy",
      "description": "Development environment policy",
      "commands": ["df", "ps", "free"],
      "connections": ["devcontroller"]
    }
  ]
}
```

#### Create Policy

**Endpoint:** `POST /workspace/v2/policy`

**Description:** Create a new execution policy

**Request Body:**
```json
{
  "name": "mcp-policy",
  "description": "Policy for MCP server operations",
  "commands": ["df", "ps", "free"],
  "connections": ["devcontroller"]
}
```

**Response Example:**
```json
{
  "success": true,
  "name": "mcp-policy"
}
```

#### Delete Policy

**Endpoint:** `DELETE /workspace/v2/policy/{name}`

**Description:** Delete an execution policy

**Response Example:**
```json
{
  "success": true
}
```

### MCP Triggers

#### List All Triggers

**Endpoint:** `GET /workspace/v2/triggers`

**Description:** Retrieve all triggers in the workspace

**Response Example:**
```json
{
  "triggers": [
    {
      "name": "my-mcp-server",
      "kind": "mcp",
      "description": "MCP server for automation",
      "triggerUrl": "https://api.console.opsbeacon.com/trigger/ws/xxx/mcp/yyy/",
      "commands": ["df", "ps"],
      "connections": ["devcontroller"],
      "policies": ["mcp-policy"]
    }
  ]
}
```

#### Create MCP Trigger

**Endpoint:** `POST /workspace/v2/triggers`

**Description:** Create a new MCP trigger with tools

**Request Body:**
```json
{
  "name": "my-mcp-server",
  "description": "MCP server for system monitoring",
  "kind": "mcp",
  "commands": ["df"],
  "connections": ["devcontroller"],
  "policies": ["mcp-policy"],
  "mcpTriggerInfo": {
    "toolInstances": [
      {
        "instanceId": "disk-usage",
        "templateId": "disk-usage",
        "overrides": {
          "name": "disk_usage",
          "description": "Check disk usage on the server",
          "connection": "devcontroller",
          "command": "df",
          "argumentOverrides": {}
        }
      }
    ]
  }
}
```

**Response Example:**
```json
{
  "url": "https://api.console.opsbeacon.com/trigger/ws/xxx/mcp/yyy/",
  "apiToken": "[REDACTED - This token is only shown once during creation]"
}
```

**⚠️ Important:** The API token is only shown once during trigger creation. Save it securely as it cannot be retrieved later.

#### Update MCP Trigger

**Endpoint:** `PUT /workspace/v2/triggers/{name}`

**Description:** Update an existing MCP trigger

**Request Body:**
```json
{
  "name": "my-mcp-server",
  "kind": "mcp",
  "description": "Updated description",
  "commands": ["df", "ps"],
  "connections": ["devcontroller"],
  "policies": ["mcp-policy"],
  "mcpTriggerInfo": {
    "toolInstances": [...]
  }
}
```

#### Delete Trigger

**Endpoint:** `DELETE /workspace/v2/triggers/{name}`

**Description:** Delete a trigger

**Response Example:**
```json
{
  "success": true
}
```

### Users

#### List All Users

**Endpoint:** `GET /workspace/v2/users`

**Description:** Retrieve all users in the workspace

**Response Example:**
```json
{
  "users": [
    {
      "id": "user-123",
      "name": "John Doe",
      "email": "john.doe@example.com",
      "role": "admin"
    }
  ]
}
```

#### Add User

**Endpoint:** `POST /workspace/v2/users`

**Description:** Add a new user to the workspace

**Request Body:**
```json
{
  "name": "Jane Smith",
  "email": "jane.smith@example.com",
  "role": "operator"
}
```

**Response Example:**
```json
{
  "success": true,
  "userId": "user-456"
}
```

### Groups

#### List All Groups

**Endpoint:** `GET /workspace/v2/groups`

**Description:** Retrieve all groups in the workspace

**Response Example:**
```json
{
  "groups": [
    {
      "name": "admins",
      "description": "System administrators",
      "members": ["user-123"],
      "permissions": ["all"]
    }
  ]
}
```

#### Create Group

**Endpoint:** `POST /workspace/v2/groups`

**Description:** Create a new group

**Request Body:**
```json
{
  "name": "developers",
  "description": "Development team",
  "members": ["user-456"],
  "permissions": ["read", "execute"]
}
```

### Files

#### Upload File

**Endpoint:** `POST /workspace/v2/file-upload`

**Description:** Upload a file to the workspace

**Request:** `multipart/form-data` with file content

**Response Example:**
```json
{
  "success": true,
  "fileId": "file-abc123",
  "filename": "data.csv"
}
```

#### Get File Download URL

**Endpoint:** `GET /workspace/v2/file-url/{fileId}`

**Description:** Get a temporary download URL for a file

**Response Example:**
```json
{
  "success": true,
  "url": "https://s3.amazonaws.com/...",
  "expiresIn": 3600
}
```

## MCP Protocol

The Model Context Protocol (MCP) is a JSON-RPC 2.0 based protocol that allows AI applications to interact with OpsBeacon.

### Connection

Connect using the URL and token from trigger creation:
```
URL: https://api.console.opsbeacon.com/trigger/ws/{workspaceId}/mcp/{triggerId}/
Authorization: Bearer YOUR_MCP_TOKEN
```

### Initialize Session

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {
    "protocolVersion": "0.1.0",
    "capabilities": {},
    "clientInfo": {
      "name": "My AI Client",
      "version": "1.0.0"
    }
  },
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "protocolVersion": "0.1.0",
    "capabilities": {
      "tools": {}
    },
    "serverInfo": {
      "name": "OpsBeacon MCP Server",
      "version": "1.0.0"
    }
  },
  "id": 1
}
```

### List Available Tools

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/list",
  "params": {},
  "id": 2
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "tools": [
      {
        "name": "disk_usage",
        "description": "Check disk usage on the server",
        "inputSchema": {
          "type": "object",
          "properties": {},
          "required": []
        }
      }
    ]
  },
  "id": 2
}
```

### Execute Tool

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "disk_usage",
    "arguments": {}
  },
  "id": 3
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Filesystem      Size  Used Avail Use% Mounted on\n/dev/sda1        50G   30G   20G  60% /"
      }
    ]
  },
  "id": 3
}
```

### Error Codes

- `-32700`: Parse error
- `-32600`: Invalid request
- `-32601`: Method not found
- `-32602`: Invalid params
- `-32603`: Internal error

## Python SDK Usage Examples

### Basic Operations

```python
from opsbeacon import OpsBeaconClient

client = OpsBeaconClient(api_domain="api.console.opsbeacon.com", api_token="your-api-token")

# Fetch a list of commands
commands = client.commands()
print(commands)

# Fetch a list of connections
connections = client.connections()
print(connections)

# Execute a command with string arguments (backward compatibility)
result = client.run(command="df", connection="devcontroller", args="-h")
print(result)

# Execute a command with array arguments (recommended)
result = client.run(command="df", connection="devcontroller", args=["-h"])
print(result)
```

### Policy Management

```python
# List all policies
policies = client.policies()

# Create a new policy
policy = client.create_policy(
    name="mcp-policy",
    description="Policy for MCP server",
    commands=["df", "ps", "free"],
    connections=["devcontroller"]
)

# Get policy details
details = client.get_policy("mcp-policy")

# Delete policy
client.delete_policy("mcp-policy")
```

### MCP Trigger Management

```python
# First create a policy
policy = client.create_policy(
    name="mcp-policy",
    description="Policy for MCP server",
    commands=["df", "ps"],
    connections=["devcontroller"]
)

# Create MCP trigger with tools
tool_instances = [
    {
        "instanceId": "disk-usage",
        "templateId": "disk-usage",
        "overrides": {
            "name": "disk_usage",
            "description": "Check disk usage",
            "connection": "devcontroller",
            "command": "df",
            "argumentOverrides": {}
        }
    }
]

result = client.create_mcp_trigger(
    name="my-mcp-server",
    description="MCP server for monitoring",
    tool_instances=tool_instances,
    policies=["mcp-policy"]
)

# IMPORTANT: Save these credentials - token is only shown once!
mcp_url = result["url"]
mcp_token = result["apiToken"]

# Test the MCP server
test = client.test_mcp_protocol(
    mcp_url=mcp_url,
    api_token=mcp_token,
    tool_name="disk_usage"
)

if test["success"]:
    print("MCP server is working!")
```

### User Management

```python
# Fetch a list of users
users = client.users()
print(users)

# Add a new user
new_user = {
    "name": "John Doe",
    "email": "john.doe@example.com"
}
client.add_user(new_user)

# Delete a user
client.delete_user("user-id")
```

### Group Management

```python
# Fetch a list of groups
groups = client.groups()
print(groups)

# Add a new group
new_group = {
    "name": "Admin Group",
    "description": "Group for admin users"
}
client.add_group(new_group)

# Delete a group
client.delete_group("admin-group")
```

### File Operations

```python
# Upload a file
client.file_upload(file_content="some,csv,data", file_name="example.csv")

# Upload from file path
client.file_upload(input_file="/path/to/file.txt", file_name="uploaded.txt")

# Download a file
client.file_download("example.csv", "downloaded_file.csv")

# Get download URL
url_info = client.get_file_download_url("file-id")
print(url_info["url"])
```

## API Reference

### Core Operations
- `commands()`: Fetch a list of available commands in the workspace.
- `connections()`: Retrieve a list of connections in the workspace.
- `run(command_text: str = "", connection: str = "", command: str = "", args: Union[List[str], str] = "")`: Execute a command in the OpsBeacon workspace.

### Policy Management
- `policies()`: Fetch a list of all execution policies in the workspace.
- `create_policy(name: str, description: str = "", commands: List[str] = None, connections: List[str] = None)`: Create a new execution policy.
- `get_policy(name: str)`: Get details of a specific policy by name.
- `delete_policy(name: str)`: Delete an execution policy by name.

### User Management
- `users()`: Fetch a list of users in the workspace.
- `add_user(user: Dict[str, Any])`: Add a new user to the workspace.
- `delete_user(user_id: str)`: Delete a user from the workspace by user ID.

### Group Management
- `groups()`: Fetch a list of groups defined in the workspace.
- `add_group(group: Dict[str, Any])`: Add a new group to the workspace.
- `delete_group(group_name: str)`: Delete a group from the workspace by group name.

### File Operations
- `file_upload(file_content: str = None, file_name: str = None, input_file: str = None)`: Upload a file to the OpsBeacon workspace.
- `get_file_download_url(file_id: str)`: Get a download URL for a specified file.
- `file_download(file_name: str, destination_path: str = None)`: Download a file from OpsBeacon and save it to the specified destination.

### MCP Trigger Management
- `triggers(kind: Optional[str] = None)`: Fetch a list of triggers in the workspace, optionally filtered by kind.
- `mcp_triggers()`: Fetch a list of MCP triggers specifically.
- `get_trigger(name: str)`: Get details of a specific trigger by name.
- `create_mcp_trigger(name: str, description: str = "", tool_instances: Optional[List[Dict]] = None, policies: Optional[List[str]] = None)`: Create a new MCP trigger with tools.
- `update_mcp_trigger(name: str, description: Optional[str] = None, tool_instances: Optional[List[Dict]] = None)`: Update an existing MCP trigger.
- `delete_trigger(name: str)`: Delete a trigger by name.
- `get_mcp_trigger_url(name: str)`: Get the MCP server URL for a specific trigger.
- `add_tool_to_mcp_trigger(trigger_name: str, tool_config: Dict)`: Add a new tool to an existing MCP trigger.
- `remove_tool_from_mcp_trigger(trigger_name: str, tool_name: str)`: Remove a tool from an MCP trigger by tool name.
- `test_mcp_protocol(mcp_url: str, api_token: str, tool_name: Optional[str] = None)`: Test MCP server by initializing, listing tools, and executing a command.

## Error Handling

### HTTP Status Codes
- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Invalid or missing API token
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource already exists
- `500 Internal Server Error`: Server-side error

### Python SDK Error Handling

```python
from opsbeacon import OpsBeaconClient, OpsBeaconError

client = OpsBeaconClient()

try:
    result = client.run(
        command="invalid-command",
        connection="nonexistent",
        args=[]
    )
except OpsBeaconError as e:
    print(f"API Error: {e}")
    # Handle specific error cases
    if "not found" in str(e).lower():
        print("Command or connection not found")
    elif "unauthorized" in str(e).lower():
        print("Check your API token")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Debug Mode

Enable debug mode to see full HTTP requests and responses:

```python
client = OpsBeaconClient(
    api_domain="api.console.opsbeacon.com",
    api_token="your-api-token",
    debug=True
)

# All API calls will now print request/response details
```

## Support

For additional support:
- Documentation: https://docs.opsbeacon.com
- Email: support@opsbeacon.com
- GitHub Issues: https://github.com/ob2ai/ob-python-sdk/issues