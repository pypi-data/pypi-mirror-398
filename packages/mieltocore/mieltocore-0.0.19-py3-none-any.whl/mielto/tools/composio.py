"""
Composio Tools Integration for Mielto

Composio is a platform for authenticated tool calling that connects AI agents to real-world actions.
It provides access to 150+ tools including Slack, GitHub, Notion, Gmail, Calendar, and more.

Key Features:
- OAuth authentication flows
- User-specific tool authorization
- Fine-grained access control
- Support for multiple LLM providers

Documentation: https://docs.composio.dev/docs/quickstart
"""

import json
from os import getenv
from typing import Any, Dict, List, Optional

from mielto.tools import Toolkit
from mielto.utils.log import log_debug, log_error, log_info, log_warning

try:
    from composio import Action, App, Composio
except ImportError:
    raise ImportError("`composio` not installed. Please install using `pip install composio-core`")


class ComposioTools(Toolkit):
    """
    Composio Tools Integration for Mielto.
    
    This toolkit provides access to Composio's 150+ authenticated tools including:
    - Communication: Slack, Gmail, Discord, Teams
    - Development: GitHub, GitLab, Bitbucket, Jira
    - Productivity: Notion, Asana, Trello, Calendar
    - And many more...
    
    Usage:
        composio_tools = ComposioTools(api_key="your_api_key")
        
        # Or with environment variable COMPOSIO_API_KEY
        composio_tools = ComposioTools()
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        enable_authorize_toolkit: bool = True,
        enable_list_toolkits: bool = True,
        enable_get_tools: bool = True,
        enable_execute_action: bool = True,
        enable_get_connection_status: bool = True,
        enable_list_connections: bool = True,
        all: bool = False,
        **kwargs,
    ):
        """
        Initialize Composio Tools.
        
        Args:
            api_key: Composio API key. If not provided, will use COMPOSIO_API_KEY env variable.
            enable_authorize_toolkit: Enable toolkit authorization tool.
            enable_list_toolkits: Enable list toolkits tool.
            enable_get_tools: Enable get tools for user tool.
            enable_execute_action: Enable execute action tool.
            enable_get_connection_status: Enable get connection status tool.
            enable_list_connections: Enable list user connections tool.
            all: Enable all tools.
            **kwargs: Additional arguments passed to Toolkit.
        """
        self.api_key = api_key or getenv("COMPOSIO_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "COMPOSIO_API_KEY not set. Please set the COMPOSIO_API_KEY environment variable "
                "or pass api_key parameter. Get your API key from: https://app.composio.dev/settings"
            )
        
        # Initialize Composio client
        self.client = Composio(api_key=self.api_key)
        log_info("Composio client initialized successfully")
        
        # Select tools to enable
        tools: List[Any] = []
        if all or enable_list_toolkits:
            tools.append(self.list_toolkits)
        if all or enable_authorize_toolkit:
            tools.append(self.authorize_toolkit)
        if all or enable_get_tools:
            tools.append(self.get_tools_for_user)
        if all or enable_execute_action:
            tools.append(self.execute_action)
        if all or enable_get_connection_status:
            tools.append(self.get_connection_status)
        if all or enable_list_connections:
            tools.append(self.list_user_connections)
        
        super().__init__(name="composio_tools", tools=tools, **kwargs)
    
    def list_toolkits(self, category: Optional[str] = None) -> str:
        """
        List all available toolkits/apps in Composio.
        
        Composio provides 150+ tools across various categories including:
        - Communication (Slack, Gmail, Discord)
        - Development (GitHub, GitLab, Jira)
        - Productivity (Notion, Calendar, Trello)
        - CRM (Salesforce, HubSpot)
        - And many more...
        
        Args:
            category: Optional category filter (e.g., 'communication', 'development', 'productivity').
        
        Returns:
            JSON string containing list of available toolkits with their details.
        """
        try:
            log_debug("Fetching available toolkits from Composio")
            
            # Get all apps
            apps = self.client.apps.get()
            
            # Format response
            toolkit_list = []
            for app in apps:
                app_info = {
                    "name": app.name if hasattr(app, "name") else str(app),
                    "key": app.key if hasattr(app, "key") else str(app),
                }
                
                # Add optional fields if available
                if hasattr(app, "description"):
                    app_info["description"] = app.description
                if hasattr(app, "categories"):
                    app_info["categories"] = app.categories
                
                # Filter by category if specified
                if category:
                    if hasattr(app, "categories") and category.lower() in [c.lower() for c in app.categories]:
                        toolkit_list.append(app_info)
                else:
                    toolkit_list.append(app_info)
            
            result = {
                "total": len(toolkit_list),
                "toolkits": toolkit_list[:50],  # Limit to first 50 for readability
                "note": "Showing first 50 toolkits. Use category filter for more specific results."
            }
            
            log_info(f"Found {len(toolkit_list)} toolkits")
            return json.dumps(result, indent=2)
            
        except Exception as e:
            log_error(f"Error listing toolkits: {e}", exc_info=True)
            return json.dumps({"error": str(e), "type": type(e).__name__})
    
    def authorize_toolkit(self, user_id: str, toolkit: str) -> str:
        """
        Authorize a toolkit/app for a specific user.
        
        This generates an authorization URL that the user must visit to complete OAuth flow.
        Once authorized, the user will be able to use tools from that toolkit.
        
        Args:
            user_id: Unique identifier for the user (e.g., email, user ID).
            toolkit: Name or key of the toolkit to authorize (e.g., 'gmail', 'GITHUB', 'slack').
        
        Returns:
            JSON string containing authorization URL and connection request details.
            
        Example:
            result = authorize_toolkit("user@example.com", "gmail")
            # Returns: {"redirect_url": "https://...", "connection_id": "..."}
            # User should visit the redirect_url to complete authorization
        """
        try:
            log_info(f"Initiating authorization for toolkit '{toolkit}' for user '{user_id}'")
            
            # Initialize connection request
            connection_request = self.client.toolkits.authorize(
                user_id=user_id,
                toolkit=toolkit
            )
            
            result = {
                "status": "success",
                "message": f"Authorization initiated for {toolkit}",
                "redirect_url": connection_request.redirect_url,
                "user_id": user_id,
                "toolkit": toolkit,
                "instructions": "Please visit the redirect_url to complete the authorization flow."
            }
            
            if hasattr(connection_request, "connection_id"):
                result["connection_id"] = connection_request.connection_id
            
            log_info(f"Authorization URL generated: {connection_request.redirect_url}")
            return json.dumps(result, indent=2)
            
        except Exception as e:
            log_error(f"Error authorizing toolkit '{toolkit}': {e}", exc_info=True)
            return json.dumps({
                "status": "error",
                "error": str(e),
                "type": type(e).__name__,
                "user_id": user_id,
                "toolkit": toolkit
            })
    
    def get_connection_status(self, user_id: str, toolkit: str) -> str:
        """
        Check if a user has an active connection to a specific toolkit.
        
        Args:
            user_id: Unique identifier for the user.
            toolkit: Name or key of the toolkit to check.
        
        Returns:
            JSON string containing connection status information.
        """
        try:
            log_debug(f"Checking connection status for user '{user_id}' and toolkit '{toolkit}'")
            
            # Get user's connections
            connections = self.client.toolkits.get_connections(user_id=user_id)
            
            # Check if toolkit is connected
            toolkit_connection = None
            for conn in connections:
                if hasattr(conn, "app") and conn.app.lower() == toolkit.lower():
                    toolkit_connection = conn
                    break
            
            if toolkit_connection:
                result = {
                    "status": "connected",
                    "user_id": user_id,
                    "toolkit": toolkit,
                    "connection_active": True
                }
                if hasattr(toolkit_connection, "connection_id"):
                    result["connection_id"] = toolkit_connection.connection_id
            else:
                result = {
                    "status": "not_connected",
                    "user_id": user_id,
                    "toolkit": toolkit,
                    "connection_active": False,
                    "message": f"User '{user_id}' has not authorized '{toolkit}' yet."
                }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            log_error(f"Error checking connection status: {e}", exc_info=True)
            return json.dumps({
                "status": "error",
                "error": str(e),
                "type": type(e).__name__
            })
    
    def list_user_connections(self, user_id: str) -> str:
        """
        List all active connections for a user.
        
        Args:
            user_id: Unique identifier for the user.
        
        Returns:
            JSON string containing list of user's active connections.
        """
        try:
            log_debug(f"Fetching connections for user '{user_id}'")
            
            connections = self.client.toolkits.get_connections(user_id=user_id)
            
            connection_list = []
            for conn in connections:
                conn_info = {}
                if hasattr(conn, "app"):
                    conn_info["app"] = conn.app
                if hasattr(conn, "connection_id"):
                    conn_info["connection_id"] = conn.connection_id
                if hasattr(conn, "status"):
                    conn_info["status"] = conn.status
                
                connection_list.append(conn_info)
            
            result = {
                "user_id": user_id,
                "total_connections": len(connection_list),
                "connections": connection_list
            }
            
            log_info(f"User '{user_id}' has {len(connection_list)} active connections")
            return json.dumps(result, indent=2)
            
        except Exception as e:
            log_error(f"Error listing user connections: {e}", exc_info=True)
            return json.dumps({
                "status": "error",
                "error": str(e),
                "type": type(e).__name__
            })
    
    def get_tools_for_user(self, user_id: str, toolkits: Optional[List[str]] = None) -> str:
        """
        Get available tools for a user based on their authorized toolkits.
        
        Args:
            user_id: Unique identifier for the user.
            toolkits: Optional list of toolkit names to filter tools (e.g., ['GMAIL', 'SLACK']).
        
        Returns:
            JSON string containing list of available tools with their schemas.
        """
        try:
            log_debug(f"Fetching tools for user '{user_id}'")
            
            # Get tools for user
            if toolkits:
                tools = self.client.tools.get(user_id=user_id, toolkits=toolkits)
            else:
                tools = self.client.tools.get(user_id=user_id)
            
            # Format tools list
            tool_list = []
            for tool in tools[:20]:  # Limit to first 20 for readability
                tool_info = {}
                if hasattr(tool, "name"):
                    tool_info["name"] = tool.name
                if hasattr(tool, "description"):
                    tool_info["description"] = tool.description
                if hasattr(tool, "parameters"):
                    tool_info["parameters"] = tool.parameters
                
                tool_list.append(tool_info)
            
            result = {
                "user_id": user_id,
                "total_tools": len(tool_list),
                "tools": tool_list,
                "note": "Showing first 20 tools. Specify toolkits parameter to filter results."
            }
            
            log_info(f"Found {len(tool_list)} tools for user '{user_id}'")
            return json.dumps(result, indent=2)
            
        except Exception as e:
            log_error(f"Error fetching tools for user: {e}", exc_info=True)
            return json.dumps({
                "status": "error",
                "error": str(e),
                "type": type(e).__name__,
                "message": "Make sure the user has authorized the required toolkits first."
            })
    
    def execute_action(
        self,
        user_id: str,
        action: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Execute a specific action for a user.
        
        Args:
            user_id: Unique identifier for the user.
            action: Action name/ID to execute (e.g., 'GMAIL_SEND_EMAIL', 'GITHUB_CREATE_ISSUE').
            parameters: Dictionary of parameters required for the action.
        
        Returns:
            JSON string containing the execution result.
            
        Example:
            execute_action(
                user_id="user@example.com",
                action="GMAIL_SEND_EMAIL",
                parameters={
                    "to": "recipient@example.com",
                    "subject": "Hello",
                    "body": "Test email from Composio"
                }
            )
        """
        try:
            log_info(f"Executing action '{action}' for user '{user_id}'")
            
            # Execute the action
            result = self.client.actions.execute(
                action=action,
                user_id=user_id,
                params=parameters or {}
            )
            
            response = {
                "status": "success",
                "action": action,
                "user_id": user_id,
                "result": result
            }
            
            log_info(f"Action '{action}' executed successfully for user '{user_id}'")
            return json.dumps(response, indent=2, default=str)
            
        except Exception as e:
            log_error(f"Error executing action '{action}': {e}", exc_info=True)
            return json.dumps({
                "status": "error",
                "action": action,
                "user_id": user_id,
                "error": str(e),
                "type": type(e).__name__,
                "message": "Make sure the user has authorized the required toolkit and the action name is correct."
            })
