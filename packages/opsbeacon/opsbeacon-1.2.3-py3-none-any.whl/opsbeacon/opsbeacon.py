import requests
from typing import List, Dict, Any, Optional, Union
import shlex
import uuid
import time
import json

class OpsBeaconClient:
    """
    Client library to interact with the OpsBeacon API for managing commands, connections, users, groups, files, and apps.

    Attributes:
        api_domain (str): The domain of the OpsBeacon API.
        api_token (str): The token used for authenticating API requests.
        headers (dict): The default headers for API requests, including the authorization token.
    """
    
    def __init__(self, api_domain: str, api_token: str, debug: bool = False):
        """
        Initializes the OpsBeaconClient with the specified API domain and token.

        Args:
            api_domain (str): The domain of the OpsBeacon API.
            api_token (str): The API token for authenticating requests.
            debug (bool): Enable debug mode to print HTTP requests/responses.
        """
        self.api_domain = api_domain
        self.api_token = api_token
        self.debug = debug
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
    
    def _debug_request(self, method: str, url: str, headers: dict = None, json_data: dict = None):
        """Print debug information for HTTP request."""
        if self.debug:
            print(f"\n=== HTTP Request ===")
            print(f"{method} {url}")
            print(f"Headers: {headers}")
            if json_data:
                print(f"Body: {json.dumps(json_data, indent=2)}")
    
    def _debug_response(self, response):
        """Print debug information for HTTP response."""
        if self.debug:
            print(f"\n=== HTTP Response ===")
            print(f"Status: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            try:
                print(f"Body: {json.dumps(response.json(), indent=2)}")
            except:
                print(f"Body: {response.text}")

    def commands(self) -> List[Dict[str, Any]]:
        """
        Fetch a list of available commands in the workspace.

        Returns:
            List[Dict[str, Any]]: A list of command objects containing fields like:
                - id: Unique identifier (UUID) for the command
                - kind: Command type (e.g., 'ssh', 'script', 'rest', 'sql', etc.)
                - name: Human-readable command name
                - description: Command description
                - scriptCommandInfo: For script commands, contains 'command' (script path) and 'arguments'
                - sshCommandInfo: For SSH commands, contains 'command' and 'arguments'
                - And other type-specific info fields
        """
        url = f'https://{self.api_domain}/workspace/v2/commands'
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json().get("commands", [])
        except requests.RequestException as e:
            print(f"Error fetching commands: {e}")
            return []

    def get_command(self, command_id: str) -> Dict[str, Any]:
        """
        Get details of a specific command by its ID.

        Args:
            command_id (str): The UUID of the command.

        Returns:
            Dict[str, Any]: The command details or empty dict if not found.
        """
        url = f'https://{self.api_domain}/workspace/v2/commands/{command_id}'
        try:
            self._debug_request("GET", url, self.headers)
            response = requests.get(url, headers=self.headers)
            self._debug_response(response)
            response.raise_for_status()
            result = response.json()
            # API wraps the command in a 'command' key
            return result.get("command", result)
        except requests.RequestException as e:
            print(f"Error fetching command {command_id}: {e}")
            return {}

    def update_command(self, command_id: str, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing command by its ID.

        Args:
            command_id (str): The UUID of the command to update.
            command_data (Dict[str, Any]): The updated command data. Should include the full
                command structure with fields like:
                - name: Command name
                - description: Command description
                - kind: Command type
                - scriptCommandInfo/sshCommandInfo/etc: Type-specific configuration

        Returns:
            Dict[str, Any]: The updated command object or error response with 'error' key.
        """
        url = f'https://{self.api_domain}/workspace/v2/commands/{command_id}'

        try:
            self._debug_request("PUT", url, self.headers, command_data)
            response = requests.put(url, headers=self.headers, json=command_data)
            self._debug_response(response)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error updating command {command_id}: {e}")
            if hasattr(e, 'response') and e.response:
                return {"error": str(e), "details": e.response.text}
            return {"error": str(e)}

    def connections(self) -> List[Dict[str, Any]]:
        """
        Retrieve a list of connections in the workspace.

        Returns:
            List[Dict[str, Any]]: A list of connection objects.
        """
        url = f'https://{self.api_domain}/workspace/v2/connections'
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json().get("connections", [])
        except requests.RequestException as e:
            print(f"Failed to fetch connections: {e}")
            return []
        
    def users(self) -> List[Dict[str, Any]]:
        """
        Fetch a list of users in the workspace.

        Returns:
            List[Dict[str, Any]]: A list of user objects.
        """
        url = f'https://{self.api_domain}/workspace/v2/users'
        try: 
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json().get("users", [])
        except requests.RequestException as e:
            print(f"Failed to fetch users: {e}")
            return []
    
    def add_user(self, user: Dict[str, Any]) -> bool:
        """
        Add a new user to the workspace.

        Args:
            user (Dict[str, Any]): User details to be added.

        Returns:
            bool: True if the user was successfully added, False otherwise.
        """
        url = f'https://{self.api_domain}/workspace/v2/users'
        try:
            response = requests.post(url, headers=self.headers, json=user)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Failed to add user: {e}")
            return False

    def delete_user(self, user_id: str) -> bool:
        """
        Delete a user from the workspace by user ID.

        Args:
            user_id (str): The ID of the user to delete.

        Returns:
            bool: True if the user was successfully deleted, False otherwise.
        """
        url = f'https://{self.api_domain}/workspace/v2/users/{user_id}'
        try:
            response = requests.delete(url, headers=self.headers)
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"Failed to delete user: {e}")
            return False
        
    def groups(self) -> List[Dict[str, Any]]:
        """
        Fetch a list of groups defined in the workspace.

        Returns:
            List[Dict[str, Any]]: A list of group objects.
        """
        url = f'https://{self.api_domain}/workspace/v2/policy/group'
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json().get("groups", [])
        except requests.RequestException as e:
            print(f"Failed to fetch groups: {e}")
            return []
    
    def add_group(self, group: Dict[str, Any]) -> bool:
        """
        Add a new group to the workspace.

        Args:
            group (Dict[str, Any]): Group details to be added.

        Returns:
            bool: True if the group was successfully added, False otherwise.
        """
        url = f'https://{self.api_domain}/workspace/v2/policy/group'
        try:
            response = requests.post(url, headers=self.headers, json=group)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Failed to add group: {e}")
            return False
    
    def delete_group(self, group_name: str) -> bool:
        """
        Delete a group from the workspace by group name.

        Args:
            group_name (str): The name of the group to delete.

        Returns:
            bool: True if the group was successfully deleted, False otherwise.
        """
        url = f'https://{self.api_domain}/workspace/v2/policy/group/{group_name}'
        try:
            response = requests.delete(url, headers=self.headers)
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"Failed to delete group: {e}")
            return False

    def file_upload(self, file_content: str = None, file_name: str = None, input_file: str = None) -> bool:
        """
        Upload a file to the OpsBeacon workspace.

        Args:
            file_content (str, optional): Content of the file as a string.
            file_name (str, optional): Name of the file.
            input_file (str, optional): Path to the file for uploading.

        Returns:
            bool: True if the file was uploaded successfully, False otherwise.
        """
        url = f'https://{self.api_domain}/workspace/v2/files'
        self.headers.pop("Content-Type", None)

        if file_content:
            if not file_name:
                raise ValueError("File name is required for file upload")
            files = {
                'file': (file_name, file_content, 'text/csv')
            }
            body = {"filename": file_name}
            try:
                response = requests.post(url, headers=self.headers, files=files, data=body)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                print(f"Failed to upload file: {e}")
                return False
        elif input_file:
            if not file_name:
                file_name = input_file.split("/")[-1]

            files = {
                'file': (file_name, open(input_file, "rb"), "application/octet-stream")
            }
            
            body = {"filename": file_name}
            try:
                response = requests.post(url, headers=self.headers, files=files, data=body)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                print(f"Failed to upload file: {e}")
                return False
        else:
            raise ValueError("Invalid input for file upload")
    
    def get_file_download_url(self, file_id: str) -> str:
        """
        Get a download URL for a specified file.

        Args:
            file_id (str): The ID of the file.

        Returns:
            str: The download URL for the file.
        """
        url = f'https://{self.api_domain}/workspace/v2/file-url/{file_id}'
        response = requests.get(url, headers=self.headers)
        success = response.json().get("success", False)
        if not success:
            raise ValueError(response.json().get("err"))
        
        return response.json().get("url")
    
    def file_download(self, file_name: str, destination_path: str = None) -> bool:
        """
        Download a file from OpsBeacon and save it to the specified destination.

        Args:
            file_name (str): Name of the file to download.
            destination_path (str, optional): Path to save the file.

        Returns:
            bool: True if the file was successfully downloaded, False otherwise.
        """
        download_url = self.get_file_download_url(file_name)
        response = requests.get(download_url)
        if not destination_path:
            destination_path = file_name

        with open(destination_path, "wb") as f:
            f.write(response.content)

        return True

    def run(self, command_text: str = "", connection: str = "", command: str = "", 
            args: Union[List[str], str] = "", debug: bool = False) -> Dict[str, Any]:
        """
        Execute a command in the OpsBeacon workspace.

        Args:
            command_text (str, optional): The command line text.
            connection (str, optional): Connection identifier.
            command (str, optional): Command name.
            args (Union[List[str], str], optional): Arguments for the command. Can be a list of strings or a space-separated string.
            debug (bool, optional): Enable debug output.

        Returns:
            Dict[str, Any]: The command execution response.
        """
        if command_text:
            body = {"commandLine": command_text}
        elif command and connection:
            # Convert string args to list if needed
            if isinstance(args, str):
                # Split by spaces but respect quoted arguments
                args_list = shlex.split(args) if args else []
            else:
                args_list = args
                
            body = {"command": command, "connection": connection, "arguments": args_list}
        else:
            raise ValueError("Invalid input for command execution")
        
        url = f'https://{self.api_domain}/trigger/v1/api'

        try:
            if debug:
                print(f"Debug: POST {url}")
                print(f"Debug: Headers: {self.headers}")
                print(f"Debug: Body: {body}")
            
            response = requests.post(url, headers=self.headers, json=body)
            
            if debug:
                print(f"Debug: Status Code: {response.status_code}")
                print(f"Debug: Response Headers: {dict(response.headers)}")
                print(f"Debug: Response Text: {response.text}")
            
            response.raise_for_status()
            return response.json()
        except requests.json.JSONDecodeError as e:
            print(f"Failed to decode JSON response: {e}")
            return {"error": f"JSON decode error: {str(e)}", "response": response.text}
        except requests.RequestException as e:
            print(f"Failed to execute command: {e}")
            return {"error": str(e)}
    
    def triggers(self, kind: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch a list of triggers in the workspace.

        Args:
            kind (str, optional): Filter by trigger kind (e.g., 'mcp', 'webHook', 'cron', 'link')

        Returns:
            List[Dict[str, Any]]: A list of trigger objects.
        """
        url = f'https://{self.api_domain}/workspace/v2/triggers'
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            triggers = response.json().get("triggers", [])
            
            # Filter by kind if specified
            if kind:
                triggers = [t for t in triggers if t.get("kind") == kind]
            
            return triggers
        except requests.RequestException as e:
            print(f"Error fetching triggers: {e}")
            return []
    
    def mcp_triggers(self) -> List[Dict[str, Any]]:
        """
        Fetch a list of MCP triggers in the workspace.

        Returns:
            List[Dict[str, Any]]: A list of MCP trigger objects.
        """
        return self.triggers(kind='mcp')
    
    def get_trigger(self, name: str) -> Dict[str, Any]:
        """
        Get details of a specific trigger by name.

        Args:
            name (str): The name of the trigger.

        Returns:
            Dict[str, Any]: The trigger details or empty dict if not found.
        """
        # First try to get the specific trigger
        url = f'https://{self.api_domain}/workspace/v2/triggers/{name}'
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            # If direct fetch fails, try listing all triggers and finding by name
            try:
                all_triggers = self.triggers()
                for trigger in all_triggers:
                    if trigger.get('name') == name:
                        return trigger
            except:
                pass
            return {}
    
    def create_mcp_trigger(self, name: str, description: str = "", 
                           tool_instances: Optional[List[Dict[str, Any]]] = None,
                           policies: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Create a new MCP trigger.
        
        IMPORTANT: The API token is only returned during creation and cannot be retrieved later.
        Save it immediately as it's required for AI clients to authenticate with the MCP server.

        Args:
            name (str): The name of the MCP trigger.
            description (str, optional): Description of the trigger.
            tool_instances (List[Dict], optional): List of tool instances with their configurations.
                Each tool instance should have:
                - instanceId: Unique identifier for the instance
                - templateId: ID of the tool template (or use same as instanceId)
                - overrides: Configuration overrides including:
                    - name: Tool name visible to AI
                    - description: Tool description for AI understanding
                    - connection: Connection to use
                    - command: Command to execute
                    - argumentOverrides: Dict of argument configurations

        Returns:
            Dict[str, Any]: Response containing:
                - success: True if created successfully
                - name: The trigger name
                - url: The MCP server URL
                - apiToken: The API token (ONLY shown once - save it!)
                - message: Success message
            Or error response with 'error' key.
        """
        url = f'https://{self.api_domain}/workspace/v2/triggers'
        
        # Build the trigger payload
        # Extract commands and connections from tool instances to ensure they're available
        commands = []
        connections = []
        for tool in (tool_instances or []):
            if 'overrides' in tool:
                if tool['overrides'].get('command'):
                    commands.append(tool['overrides']['command'])
                if tool['overrides'].get('connection'):
                    connections.append(tool['overrides']['connection'])
        
        # Remove duplicates
        commands = list(set(commands))
        connections = list(set(connections))
        
        payload = {
            "name": name,
            "description": description,
            "kind": "mcp",
            "commands": commands,      # Add commands that tools will use
            "connections": connections,  # Add connections that tools will use
            "policies": policies or [],  # Add policies for execution permissions
            "mcpTriggerInfo": {
                "toolInstances": tool_instances or []
            }
        }
        
        try:
            self._debug_request("POST", url, self.headers, payload)
            response = requests.post(url, headers=self.headers, json=payload)
            self._debug_response(response)
            response.raise_for_status()
            
            # The API returns url and apiToken for MCP triggers
            result = response.json()
            
            # Check for successful creation with URL and token
            if result.get('url'):
                # Return the creation response with URL and token
                return {
                    'success': True,
                    'name': name,
                    'url': result.get('url'),
                    'apiToken': result.get('apiToken'),
                    'message': f"MCP trigger '{name}' created successfully"
                }
            
            # If no URL in response, there might be an error
            if result.get('err'):
                return {'error': result.get('err')}
            
            return result
        except requests.RequestException as e:
            print(f"Error creating MCP trigger: {e}")
            if hasattr(e, 'response') and e.response:
                return {"error": str(e), "details": e.response.text}
            return {"error": str(e)}
    
    def update_mcp_trigger(self, name: str, description: Optional[str] = None,
                           tool_instances: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Update an existing MCP trigger.

        Args:
            name (str): The name of the MCP trigger to update.
            description (str, optional): New description for the trigger.
            tool_instances (List[Dict], optional): Updated list of tool instances.

        Returns:
            Dict[str, Any]: The updated trigger object or error response.
        """
        url = f'https://{self.api_domain}/workspace/v2/triggers/{name}'
        
        # Get existing trigger first
        existing = self.get_trigger(name)
        if not existing or existing.get("kind") != "mcp":
            return {"error": f"MCP trigger '{name}' not found"}
        
        # Extract commands and connections from tool instances if provided
        if tool_instances is not None:
            commands = []
            connections = []
            for tool in tool_instances:
                if 'overrides' in tool:
                    if tool['overrides'].get('command'):
                        commands.append(tool['overrides']['command'])
                    if tool['overrides'].get('connection'):
                        connections.append(tool['overrides']['connection'])
            
            # Remove duplicates
            commands = list(set(commands))
            connections = list(set(connections))
        else:
            # Keep existing commands and connections
            commands = existing.get("commands", [])
            connections = existing.get("connections", [])
        
        # Build update payload
        payload = {
            "name": name,
            "kind": "mcp",
            "description": description if description is not None else existing.get("description", ""),
            "commands": commands,
            "connections": connections,
            "mcpTriggerInfo": existing.get("mcpTriggerInfo", {})
        }
        
        # Update tool instances if provided
        if tool_instances is not None:
            payload["mcpTriggerInfo"]["toolInstances"] = tool_instances
        
        try:
            response = requests.put(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error updating MCP trigger: {e}")
            if hasattr(e, 'response') and e.response:
                return {"error": str(e), "details": e.response.text}
            return {"error": str(e)}
    
    def delete_trigger(self, name: str) -> bool:
        """
        Delete a trigger by name.

        Args:
            name (str): The name of the trigger to delete.

        Returns:
            bool: True if successfully deleted, False otherwise.
        """
        url = f'https://{self.api_domain}/workspace/v2/triggers/{name}'
        try:
            response = requests.delete(url, headers=self.headers)
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"Error deleting trigger {name}: {e}")
            return False
    
    def get_mcp_trigger_url(self, name: str) -> Optional[str]:
        """
        Get the MCP server URL for a specific trigger.

        Args:
            name (str): The name of the MCP trigger.

        Returns:
            str: The MCP server URL or None if not found.
        """
        trigger = self.get_trigger(name)
        if trigger and trigger.get("kind") == "mcp":
            return trigger.get("triggerUrl")
        return None
    
    def add_tool_to_mcp_trigger(self, trigger_name: str, tool_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a new tool to an existing MCP trigger.

        Args:
            trigger_name (str): The name of the MCP trigger.
            tool_config (Dict): Tool configuration with:
                - name: Tool name visible to AI
                - description: Tool description for AI understanding
                - connection: Connection to use
                - command: Command to execute
                - arguments: Optional dict of argument configurations

        Returns:
            Dict[str, Any]: The updated trigger object or error response.
        """
        # Get existing trigger
        trigger = self.get_trigger(trigger_name)
        if not trigger or trigger.get("kind") != "mcp":
            return {"error": f"MCP trigger '{trigger_name}' not found"}
        
        # Get existing tool instances
        mcp_info = trigger.get("mcpTriggerInfo", {})
        tool_instances = mcp_info.get("toolInstances", [])
        
        # Create new tool instance
        instance_id = str(uuid.uuid4())
        new_tool = {
            "instanceId": instance_id,
            "templateId": instance_id,  # Use same as instanceId for now
            "overrides": {
                "name": tool_config.get("name", f"tool_{len(tool_instances) + 1}"),
                "description": tool_config.get("description", ""),  # Include description
                "connection": tool_config.get("connection", ""),
                "command": tool_config.get("command", ""),
                "argumentOverrides": tool_config.get("arguments", {})
            }
        }
        
        # Add to list
        tool_instances.append(new_tool)
        
        # Make sure we have the commands and connections from the new tool
        existing_commands = trigger.get("commands", [])
        existing_connections = trigger.get("connections", [])
        
        if tool_config.get("command") and tool_config["command"] not in existing_commands:
            existing_commands.append(tool_config["command"])
        if tool_config.get("connection") and tool_config["connection"] not in existing_connections:
            existing_connections.append(tool_config["connection"])
        
        # Update trigger with new tool instances and updated commands/connections
        return self.update_mcp_trigger(trigger_name, tool_instances=tool_instances)
    
    def test_mcp_protocol(self, mcp_url: str, api_token: str, tool_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Test an MCP server by initializing, listing tools, and optionally executing a tool.
        
        Args:
            mcp_url (str): The MCP server URL
            api_token (str): The API token for authentication
            tool_name (str, optional): Name of a specific tool to execute. If None, executes the first tool.
        
        Returns:
            Dict[str, Any]: Test results including initialization, tools list, and execution result
        """
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
        results = {
            "initialize": None,
            "tools": None,
            "execution": None,
            "success": False
        }
        
        # 1. Initialize
        init_request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "0.1.0",
                "capabilities": {},
                "clientInfo": {
                    "name": "OpsBeacon Python SDK",
                    "version": "1.2.0"
                }
            },
            "id": 1
        }
        
        try:
            self._debug_request("POST", mcp_url, headers, init_request)
            response = requests.post(mcp_url, json=init_request, headers=headers)
            self._debug_response(response)
            response.raise_for_status()
            results["initialize"] = response.json()
        except Exception as e:
            results["initialize"] = {"error": str(e)}
            return results
        
        # 2. List tools
        list_request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": 2
        }
        
        try:
            self._debug_request("POST", mcp_url, headers, list_request)
            response = requests.post(mcp_url, json=list_request, headers=headers)
            self._debug_response(response)
            response.raise_for_status()
            tools_response = response.json()
            results["tools"] = tools_response
            
            # Extract tools list
            tools = []
            if 'result' in tools_response and 'tools' in tools_response['result']:
                tools = tools_response['result']['tools']
        except Exception as e:
            results["tools"] = {"error": str(e)}
            return results
        
        # 3. Execute a tool (if tools are available)
        if tools:
            # Find the tool to execute
            tool_to_execute = None
            if tool_name:
                tool_to_execute = next((t for t in tools if t['name'] == tool_name), None)
            if not tool_to_execute and tools:
                tool_to_execute = tools[0]  # Default to first tool
            
            if tool_to_execute:
                exec_request = {
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": tool_to_execute['name'],
                        "arguments": {}
                    },
                    "id": 3
                }
                
                try:
                    self._debug_request("POST", mcp_url, headers, exec_request)
                    response = requests.post(mcp_url, json=exec_request, headers=headers)
                    self._debug_response(response)
                    response.raise_for_status()
                    results["execution"] = response.json()
                    results["success"] = 'result' in results["execution"]
                except Exception as e:
                    results["execution"] = {"error": str(e)}
        else:
            results["execution"] = {"message": "No tools available to execute"}
        
        return results
    
    def policies(self) -> List[Dict[str, Any]]:
        """
        Fetch a list of execution policies in the workspace.

        Returns:
            List[Dict[str, Any]]: A list of policy objects.
        """
        url = f'https://{self.api_domain}/workspace/v2/policy'
        try:
            self._debug_request("GET", url, self.headers)
            response = requests.get(url, headers=self.headers)
            self._debug_response(response)
            response.raise_for_status()
            return response.json().get("policies", [])
        except requests.RequestException as e:
            print(f"Error fetching policies: {e}")
            return []
    
    def create_policy(self, name: str, description: str = "", 
                     commands: Optional[List[str]] = None,
                     connections: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Create a new execution policy.

        Args:
            name (str): The name of the policy.
            description (str, optional): Description of the policy.
            commands (List[str], optional): List of command names allowed by this policy.
            connections (List[str], optional): List of connection names allowed by this policy.

        Returns:
            Dict[str, Any]: The created policy object or error response.
        """
        url = f'https://{self.api_domain}/workspace/v2/policy'
        
        payload = {
            "name": name,
            "description": description,
            "commands": commands or [],
            "connections": connections or []
        }
        
        try:
            self._debug_request("POST", url, self.headers, payload)
            response = requests.post(url, headers=self.headers, json=payload)
            self._debug_response(response)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error creating policy: {e}")
            if hasattr(e, 'response') and e.response:
                return {"error": str(e), "details": e.response.text}
            return {"error": str(e)}
    
    def get_policy(self, name: str) -> Dict[str, Any]:
        """
        Get details of a specific policy by name.

        Args:
            name (str): The name of the policy.

        Returns:
            Dict[str, Any]: The policy details or empty dict if not found.
        """
        url = f'https://{self.api_domain}/workspace/v2/policy/{name}'
        try:
            self._debug_request("GET", url, self.headers)
            response = requests.get(url, headers=self.headers)
            self._debug_response(response)
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            # Try listing all policies and finding by name
            try:
                all_policies = self.policies()
                for policy in all_policies:
                    if policy.get('name') == name:
                        return policy
            except:
                pass
            return {}
    
    def delete_policy(self, name: str) -> bool:
        """
        Delete a policy by name.

        Args:
            name (str): The name of the policy to delete.

        Returns:
            bool: True if successfully deleted, False otherwise.
        """
        url = f'https://{self.api_domain}/workspace/v2/policy/{name}'
        try:
            self._debug_request("DELETE", url, self.headers)
            response = requests.delete(url, headers=self.headers)
            self._debug_response(response)
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"Error deleting policy {name}: {e}")
            return False
    
    def remove_tool_from_mcp_trigger(self, trigger_name: str, tool_name: str) -> Dict[str, Any]:
        """
        Remove a tool from an MCP trigger by tool name.

        Args:
            trigger_name (str): The name of the MCP trigger.
            tool_name (str): The name of the tool to remove.

        Returns:
            Dict[str, Any]: The updated trigger object or error response.
        """
        # Get existing trigger
        trigger = self.get_trigger(trigger_name)
        if not trigger or trigger.get("kind") != "mcp":
            return {"error": f"MCP trigger '{trigger_name}' not found"}
        
        # Get existing tool instances
        mcp_info = trigger.get("mcpTriggerInfo", {})
        tool_instances = mcp_info.get("toolInstances", [])
        
        # Filter out the tool to remove
        updated_tools = [
            t for t in tool_instances 
            if t.get("overrides", {}).get("name") != tool_name
        ]
        
        if len(updated_tools) == len(tool_instances):
            return {"error": f"Tool '{tool_name}' not found in trigger '{trigger_name}'"}
        
        # Update trigger
        return self.update_mcp_trigger(trigger_name, tool_instances=updated_tools)
