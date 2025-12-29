#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MCP utility functions.

This module provides utility functions for MCP integration.
"""

import json
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel


def pydantic_to_json_schema(model: Type[BaseModel]) -> Dict[str, Any]:
    """Convert Pydantic model to JSON Schema for MCP.

    :param model: Pydantic model class
    :type model: Type[BaseModel]
    :return: JSON Schema dictionary
    :rtype: Dict[str, Any]
    """
    schema = model.model_json_schema()

    # MCP expects a specific format
    mcp_schema = {
        "type": "object",
        "properties": schema.get("properties", {}),
    }

    if "required" in schema:
        mcp_schema["required"] = schema["required"]

    if "description" in schema:
        mcp_schema["description"] = schema["description"]

    return mcp_schema


def json_schema_to_pydantic_fields(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Convert JSON Schema to Pydantic field definitions.

    This is a simplified conversion for basic types.

    :param schema: JSON Schema dictionary
    :type schema: Dict[str, Any]
    :return: Dictionary of field definitions
    :rtype: Dict[str, Any]
    """
    from pydantic import Field

    properties = schema.get("properties", {})
    required = schema.get("required", [])
    fields = {}

    for prop_name, prop_schema in properties.items():
        field_type = _json_type_to_python_type(prop_schema)
        is_required = prop_name in required

        description = prop_schema.get("description")

        if is_required:
            if description:
                fields[prop_name] = (field_type, Field(description=description))
            else:
                fields[prop_name] = (field_type, ...)
        else:
            if description:
                fields[prop_name] = (Optional[field_type], Field(default=None, description=description))
            else:
                fields[prop_name] = (Optional[field_type], None)

    return fields


def _json_type_to_python_type(schema: Dict[str, Any]) -> Type:
    """Convert JSON Schema type to Python type.

    :param schema: JSON Schema for a property
    :type schema: Dict[str, Any]
    :return: Python type
    :rtype: Type
    """
    from typing import Any, Dict, List

    json_type = schema.get("type")

    if json_type == "string":
        if "enum" in schema:
            # For enums, use str
            return str
        return str
    elif json_type == "number":
        return float
    elif json_type == "integer":
        return int
    elif json_type == "boolean":
        return bool
    elif json_type == "array":
        items_schema = schema.get("items", {})
        if items_schema:
            item_type = _json_type_to_python_type(items_schema)
            return List[item_type]
        return List[Any]
    elif json_type == "object":
        additional_props = schema.get("additionalProperties")
        if additional_props:
            value_type = _json_type_to_python_type(additional_props) if isinstance(additional_props, dict) else Any
            return Dict[str, value_type]
        return Dict[str, Any]
    else:
        return Any


def create_dynamic_model(name: str, schema: Dict[str, Any]) -> Type[BaseModel]:
    """Create a dynamic Pydantic model from JSON Schema.

    :param name: Model name
    :type name: str
    :param schema: JSON Schema dictionary
    :type schema: Dict[str, Any]
    :return: Pydantic model class
    :rtype: Type[BaseModel]
    """
    from pydantic import create_model

    fields = json_schema_to_pydantic_fields(schema)

    # Create model with description if available
    model_config = {}
    if "description" in schema:
        model_config["json_schema_extra"] = {"description": schema["description"]}

    return create_model(name, **fields, __config__=model_config)


def format_tool_name(server_id: str, tool_name: str, separator: str = "_") -> str:
    """Format tool name with server prefix.

    :param server_id: Server identifier
    :type server_id: str
    :param tool_name: Original tool name
    :type tool_name: str
    :param separator: Separator between server_id and tool_name
    :type separator: str
    :return: Formatted tool name
    :rtype: str
    """
    return f"{server_id}{separator}{tool_name}"


def parse_tool_name(formatted_name: str, separator: str = "_") -> tuple[str, str]:
    """Parse formatted tool name to extract server_id and tool_name.

    Note: The default separator is "_" to match format_tool_name.
    If the formatted_name doesn't contain the separator, it's assumed to be
    a tool name without server_id prefix.

    :param formatted_name: Formatted tool name
    :type formatted_name: str
    :param separator: Separator used in formatting (default: "_")
    :type separator: str
    :return: Tuple of (server_id, tool_name)
    :rtype: tuple[str, str]
    """
    if separator in formatted_name:
        parts = formatted_name.split(separator, 1)
        return parts[0], parts[1]
    return "", formatted_name


def safe_json_dumps(obj: Any, **kwargs) -> str:
    """Safely serialize object to JSON string.

    :param obj: Object to serialize
    :type obj: Any
    :param kwargs: Additional arguments for json.dumps
    :return: JSON string
    :rtype: str
    """
    try:
        return json.dumps(obj, **kwargs)
    except (TypeError, ValueError):
        # Fallback to string representation
        return str(obj)


def safe_json_loads(s: str, default: Any = None) -> Any:
    """Safely deserialize JSON string.

    :param s: JSON string
    :type s: str
    :param default: Default value if parsing fails
    :type default: Any
    :return: Parsed object or default
    :rtype: Any
    """
    try:
        return json.loads(s)
    except (TypeError, ValueError, json.JSONDecodeError):
        return default


def merge_schemas(base_schema: Dict[str, Any], override_schema: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two JSON schemas.

    :param base_schema: Base schema
    :type base_schema: Dict[str, Any]
    :param override_schema: Schema to merge in
    :type override_schema: Dict[str, Any]
    :return: Merged schema
    :rtype: Dict[str, Any]
    """
    result = base_schema.copy()

    for key, value in override_schema.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_schemas(result[key], value)
        else:
            result[key] = value

    return result


__all__ = [
    "pydantic_to_json_schema",
    "json_schema_to_pydantic_fields",
    "create_dynamic_model",
    "format_tool_name",
    "parse_tool_name",
    "safe_json_dumps",
    "safe_json_loads",
    "merge_schemas",
]
