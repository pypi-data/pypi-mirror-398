"""AI-friendly output formatter for machine-readable responses"""

import json
from datetime import datetime
from typing import Any, Dict, List, Union


class AIFormatter:
    """Formats CLI output for AI agent consumption"""

    @staticmethod
    def success_response(data: Any, message: str = "Operation successful", command: str = "") -> Dict[str, Any]:
        """Format successful operation response"""
        return {
            "status": "success",
            "message": message,
            "data": data,
            "command": command,
            "timestamp": datetime.utcnow().isoformat(),
            "ai_friendly": True
        }

    @staticmethod
    def error_response(error: str, command: str = "", error_code: str = "GENERAL_ERROR") -> Dict[str, Any]:
        """Format error response for AI agents"""
        return {
            "status": "error",
            "error": error,
            "error_code": error_code,
            "command": command,
            "timestamp": datetime.utcnow().isoformat(),
            "ai_friendly": True,
            "suggestions": AIFormatter._get_error_suggestions(error_code)
        }

    @staticmethod
    def list_response(items: List[Dict[str, Any]], total: int = None, command: str = "") -> Dict[str, Any]:
        """Format list response with metadata"""
        return {
            "status": "success",
            "message": f"Retrieved {len(items)} items",
            "data": items,
            "metadata": {
                "total": total or len(items),
                "count": len(items),
                "has_more": total and total > len(items)
            },
            "command": command,
            "timestamp": datetime.utcnow().isoformat(),
            "ai_friendly": True
        }

    @staticmethod
    def create_response(created_item: Dict[str, Any], item_type: str = "item", command: str = "") -> Dict[str, Any]:
        """Format creation response"""
        return {
            "status": "success",
            "message": f"Successfully created {item_type}",
            "data": created_item,
            "created_id": created_item.get("id"),
            "item_type": item_type,
            "command": command,
            "timestamp": datetime.utcnow().isoformat(),
            "ai_friendly": True
        }

    @staticmethod
    def update_response(updated_item: Dict[str, Any], item_type: str = "item", command: str = "") -> Dict[str, Any]:
        """Format update response"""
        return {
            "status": "success",
            "message": f"Successfully updated {item_type}",
            "data": updated_item,
            "updated_id": updated_item.get("id"),
            "item_type": item_type,
            "command": command,
            "timestamp": datetime.utcnow().isoformat(),
            "ai_friendly": True
        }

    @staticmethod
    def delete_response(deleted_id: Union[str, int], item_type: str = "item", command: str = "") -> Dict[str, Any]:
        """Format deletion response"""
        return {
            "status": "success",
            "message": f"Successfully deleted {item_type}",
            "deleted_id": deleted_id,
            "item_type": item_type,
            "command": command,
            "timestamp": datetime.utcnow().isoformat(),
            "ai_friendly": True
        }

    @staticmethod
    def help_response(command_info: Dict[str, Any], examples: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """Format help response for AI agents"""
        return {
            "status": "success",
            "message": "Command help information",
            "data": {
                "command": command_info.get("command", ""),
                "description": command_info.get("description", ""),
                "usage": command_info.get("usage", ""),
                "options": command_info.get("options", []),
                "subcommands": command_info.get("subcommands", []),
                "examples": examples or [],
                "notes": command_info.get("notes", [])
            },
            "timestamp": datetime.utcnow().isoformat(),
            "ai_friendly": True
        }

    @staticmethod
    def _get_error_suggestions(error_code: str) -> List[str]:
        """Get AI-friendly suggestions for common errors"""
        suggestions = {
            "CONNECTION_ERROR": [
                "Check SSH connection and server configuration",
                "Verify server is accessible and credentials are correct",
                "Try using --server flag with correct server name"
            ],
            "PERMISSION_ERROR": [
                "Check user permissions on WordPress site",
                "Verify SSH user has sufficient privileges",
                "Check file system permissions"
            ],
            "VALIDATION_ERROR": [
                "Check parameter formats and values",
                "Verify required parameters are provided",
                "Check data types match expected formats"
            ],
            "NOT_FOUND": [
                "Verify the item exists",
                "Check spelling and case sensitivity",
                "Use list command to see available items"
            ],
            "WPCLI_ERROR": [
                "Check WP-CLI installation on remote server",
                "Verify WordPress installation is accessible",
                "Check WP-CLI command syntax and permissions"
            ]
        }
        return suggestions.get(error_code, ["Check command syntax and parameters", "Verify server connection and permissions"])

    @staticmethod
    def format_output(output: Dict[str, Any], pretty: bool = False) -> str:
        """Convert response to JSON string"""
        if pretty:
            return json.dumps(output, indent=2, default=str)
        return json.dumps(output, default=str)


# AI-friendly command schemas for validation
AI_COMMAND_SCHEMAS = {
    "create": {
        "description": "Create WordPress posts, pages, or custom post types",
        "parameters": {
            "title": {"type": "string", "required": True, "description": "Post title"},
            "content": {"type": "string", "required": False, "description": "HTML content or Gutenberg blocks"},
            "status": {"type": "string", "enum": ["publish", "draft", "private"], "default": "publish"},
            "type": {"type": "string", "enum": ["post", "page"], "default": "post"},
            "category": {"type": "string", "description": "Comma-separated category names or slugs"},
            "author": {"type": "string", "description": "User ID or login"},
            "server": {"type": "string", "description": "Server name from config"}
        },
        "examples": [
            {"command": 'praisonaiwp create "My Post" --content "<p>Hello world</p>"', "description": "Create a simple post"},
            {"command": 'praisonaiwp create "About Us" --content "<p>About page</p>" --type page', "description": "Create a page"},
            {"command": 'praisonaiwp create "News" --content "<h2>Latest news</h2><p>Content here</p>" --category "News,Blog"', "description": "Create post with categories"}
        ]
    },
    "list": {
        "description": "List WordPress posts, pages, or custom post types",
        "parameters": {
            "type": {"type": "string", "enum": ["post", "page"], "default": "post"},
            "status": {"type": "string", "enum": ["publish", "draft", "pending"], "default": "publish"},
            "limit": {"type": "integer", "default": 10, "description": "Maximum number of items to return"},
            "server": {"type": "string", "description": "Server name from config"}
        },
        "examples": [
            {"command": "praisonaiwp list", "description": "List latest published posts"},
            {"command": "praisonaiwp list --type page --limit 5", "description": "List 5 latest pages"},
            {"command": "praisonaiwp list --status draft", "description": "List draft posts"}
        ]
    },
    "config": {
        "description": "Manage WordPress configuration",
        "subcommands": {
            "get": {"parameters": {"param": {"type": "string", "required": True}}},
            "set": {"parameters": {"param": {"type": "string", "required": True}, "value": {"type": "string", "required": True}}},
            "list": {"parameters": {}},
            "create": {"parameters": {"dbname": {"type": "string"}, "dbuser": {"type": "string"}, "dbpass": {"type": "string"}}}
        }
    },
    "role": {
        "description": "Manage WordPress user roles",
        "subcommands": {
            "list": {"parameters": {}},
            "get": {"parameters": {"role": {"type": "string", "required": True}}},
            "create": {"parameters": {"role_key": {"type": "string", "required": True}, "role_name": {"type": "string", "required": True}, "capabilities": {"type": "string"}}},
            "delete": {"parameters": {"role": {"type": "string", "required": True}}}
        }
    },
    "scaffold": {
        "description": "Generate WordPress code and boilerplate",
        "subcommands": {
            "post-type": {"parameters": {"slug": {"type": "string", "required": True}, "label": {"type": "string"}, "supports": {"type": "string"}}},
            "taxonomy": {"parameters": {"slug": {"type": "string", "required": True}, "label": {"type": "string"}, "post_types": {"type": "string"}}},
            "plugin": {"parameters": {"slug": {"type": "string", "required": True}, "plugin_name": {"type": "string"}, "author": {"type": "string"}}},
            "theme": {"parameters": {"slug": {"type": "string", "required": True}, "theme_name": {"type": "string"}, "author": {"type": "string"}}}
        }
    }
}
