from mcp.server.fastmcp import FastMCP
from govuk_design_system_mcp.data_fetcher import (
    get_component_list,
    get_pattern_list,
    get_style_list,
    get_component_docs,
    get_pattern_docs,
    get_style_docs,
)

mcp = FastMCP("govuk-design-system")


@mcp.tool()
def list_components() -> list[str]:
    """List all available GOV.UK Design System components."""
    return get_component_list()


@mcp.tool()
def list_patterns() -> list[str]:
    """List all available GOV.UK Design System patterns."""
    return get_pattern_list()


@mcp.tool()
def list_styles() -> list[str]:
    """List all available GOV.UK Design System styles."""
    return get_style_list()


@mcp.tool()
def get_component_guidance(name: str) -> dict:
    """
    Get usage guidance for a GOV.UK component.
    
    Args:
        name: Component name (e.g., 'button', 'text-input', 'radios')
    
    Returns when to use, how it works, and accessibility considerations.
    """
    docs = get_component_docs(name)
    if docs is None:
        return {"error": f"Component '{name}' not found"}
    return {"component": name, "documentation": docs}


@mcp.tool()
def get_pattern(name: str) -> dict:
    """
    Get a GOV.UK design pattern.
    
    Args:
        name: Pattern name (e.g., 'addresses', 'check-answers', 'question-pages')
    
    Returns full pattern documentation including when to use and examples.
    """
    docs = get_pattern_docs(name)
    if docs is None:
        return {"error": f"Pattern '{name}' not found"}
    return {"pattern": name, "documentation": docs}


@mcp.tool()
def get_style(name: str) -> dict:
    """
    Get a GOV.UK style guide.
    
    Args:
        name: Style name (e.g., 'colour', 'spacing', 'typography', 'layout')
    
    Returns style documentation including usage guidelines and examples.
    """
    docs = get_style_docs(name)
    if docs is None:
        return {"error": f"Style '{name}' not found"}
    return {"style": name, "documentation": docs}


def main():
    """Entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()