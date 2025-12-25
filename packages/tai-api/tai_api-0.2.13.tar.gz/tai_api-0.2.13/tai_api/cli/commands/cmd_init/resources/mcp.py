from fastapi import FastAPI
from typing import Dict, Any, Optional, Set

def set_mcp(app: FastAPI, operations: list[str] = None, tags: list[str] = None) -> None:
    """
    Configura el MCP (Model Context Protocol) para la aplicación FastAPI.
    
    Args:
        app (FastAPI): La instancia de la aplicación FastAPI.
    """
    from fastapi_mcp import FastApiMCP
    # Monkey patch the problematic function with our implementation
    # Remove when https://github.com/tadata-org/fastapi_mcp/pull/156 is merged
    import fastapi_mcp.openapi.utils
    fastapi_mcp.openapi.utils.resolve_schema_references = temp_resolve_schema_references

    mcp = FastApiMCP(
        app,
        name="mcp-server",
        description="Server para el MCP de la aplicación",
        include_operations=operations,
        include_tags=tags
    )

    mcp.mount_http()

def temp_resolve_schema_references(
    schema_part: Dict[str, Any],
    reference_schema: Dict[str, Any],
    seen: Optional[Set[str]] = None,
) -> Dict[str, Any]:
    """
    Resolve schema references in OpenAPI schemas.

    Args:
        schema_part: The part of the schema being processed that may contain references
        reference_schema: The complete schema used to resolve references from
        seen: A set of already seen references to avoid infinite recursion

    Returns:
        The schema with references resolved
    """
    seen = seen or set()

    # Make a copy to avoid modifying the input schema
    schema_part = schema_part.copy()

    # Handle $ref directly in the schema
    if "$ref" in schema_part:
        ref_path: str = schema_part["$ref"]
        # Standard OpenAPI references are in the format "#/components/schemas/ModelName"
        if ref_path.startswith("#/components/schemas/"):
            if ref_path in seen:
                return {"$ref": ref_path}
            seen.add(ref_path)
            model_name = ref_path.split("/")[-1]
            if "components" in reference_schema and "schemas" in reference_schema["components"]:
                if model_name in reference_schema["components"]["schemas"]:
                    # Replace with the resolved schema
                    ref_schema = reference_schema["components"]["schemas"][model_name].copy()
                    # Remove the $ref key and merge with the original schema
                    schema_part.pop("$ref")
                    schema_part.update(ref_schema)

    # Recursively resolve references in all dictionary values
    for key, value in schema_part.items():
        if isinstance(value, dict):
            schema_part[key] = temp_resolve_schema_references(value, reference_schema, seen)
        elif isinstance(value, list):
            # Only process list items that are dictionaries since only they can contain refs
            schema_part[key] = [
                temp_resolve_schema_references(item, reference_schema, seen) if isinstance(item, dict) else item
                for item in value
            ]

    return schema_part