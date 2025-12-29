"""Description loader for CLI and documentation.

Loads descriptions from framework/descriptions.yaml and provides
formatted access for different contexts (CLI, documentation, etc.).
"""

from functools import lru_cache
from pathlib import Path
from typing import Any, cast

import yaml

# Framework path (relative to package)
FRAMEWORK_DIR = Path(__file__).parent.parent / "_framework"
DESCRIPTIONS_PATH = FRAMEWORK_DIR / "descriptions.yaml"


@lru_cache(maxsize=1)
def load_descriptions() -> dict[str, Any]:
    """Load descriptions from YAML file.

    Returns:
        Dictionary containing all descriptions.

    Raises:
        FileNotFoundError: If descriptions.yaml doesn't exist.
    """
    if not DESCRIPTIONS_PATH.exists():
        raise FileNotFoundError(f"Descriptions file not found: {DESCRIPTIONS_PATH}")

    with open(DESCRIPTIONS_PATH) as f:
        return cast(dict[str, Any], yaml.safe_load(f) or {})


def get_preset_info(preset_name: str) -> dict[str, Any]:
    """Get information about a preset.

    Args:
        preset_name: Name of the preset (saas, fintech, healthcare, api-only, custom)

    Returns:
        Dictionary with short, description, extra_guardrails, recommended_packs, why_matters
    """
    descriptions = load_descriptions()
    presets = cast(dict[str, dict[str, Any]], descriptions.get("presets", {}))
    return presets.get(preset_name, {})


def get_preset_short(preset_name: str) -> str:
    """Get short description for a preset.

    Args:
        preset_name: Name of the preset

    Returns:
        Short description string
    """
    info = get_preset_info(preset_name)
    return str(info.get("short", preset_name))


def get_preset_extra_guardrails(preset_name: str) -> str:
    """Get extra guardrails string for a preset.

    Args:
        preset_name: Name of the preset

    Returns:
        Extra guardrails string (e.g., "+5 (RLS, tenancy, billing, audit, export)")
    """
    info = get_preset_info(preset_name)
    return str(info.get("extra_guardrails", "+0"))


def get_preset_recommended_packs(preset_name: str) -> list[str]:
    """Get recommended question packs for a preset.

    Args:
        preset_name: Name of the preset

    Returns:
        List of recommended question pack names
    """
    info = get_preset_info(preset_name)
    return cast(list[str], info.get("recommended_packs", []))


def get_all_presets() -> list[str]:
    """Get list of all preset names.

    Returns:
        List of preset names
    """
    descriptions = load_descriptions()
    return list(descriptions.get("presets", {}).keys())


def get_pack_info(pack_name: str) -> dict[str, Any]:
    """Get information about a question pack.

    Args:
        pack_name: Name of the question pack

    Returns:
        Dictionary with short, description, is_core, critical, use_when
    """
    descriptions = load_descriptions()
    packs = cast(dict[str, dict[str, Any]], descriptions.get("question_packs", {}))
    return packs.get(pack_name, {})


def get_pack_short(pack_name: str) -> str:
    """Get short description for a question pack.

    Args:
        pack_name: Name of the question pack

    Returns:
        Short description string
    """
    info = get_pack_info(pack_name)
    return str(info.get("short", pack_name))


def is_core_pack(pack_name: str) -> bool:
    """Check if a question pack is a core pack.

    Args:
        pack_name: Name of the question pack

    Returns:
        True if core pack (always included), False otherwise
    """
    info = get_pack_info(pack_name)
    return bool(info.get("is_core", False))


def get_core_packs() -> list[str]:
    """Get list of core question pack names.

    Returns:
        List of core pack names
    """
    descriptions = load_descriptions()
    packs = descriptions.get("question_packs", {})
    return [name for name, info in packs.items() if info.get("is_core", False)]


def get_optional_packs() -> list[str]:
    """Get list of optional (non-core) question pack names.

    Returns:
        List of optional pack names
    """
    descriptions = load_descriptions()
    packs = descriptions.get("question_packs", {})
    return [name for name, info in packs.items() if not info.get("is_core", False)]


def get_domain_packs() -> list[str]:
    """Get list of domain (non-core) question pack names.

    Deprecated: Use get_optional_packs() instead.

    Returns:
        List of optional pack names
    """
    return get_optional_packs()


def get_mcp_server_info(server_name: str) -> dict[str, Any]:
    """Get information about an MCP server.

    Args:
        server_name: Name of the MCP server

    Returns:
        Dictionary with short, description, default, why_matters
    """
    descriptions = load_descriptions()
    servers = cast(dict[str, dict[str, Any]], descriptions.get("mcp_servers", {}))
    return servers.get(server_name, {})


def get_mcp_server_short(server_name: str) -> str:
    """Get short description for an MCP server.

    Args:
        server_name: Name of the MCP server

    Returns:
        Short description string
    """
    info = get_mcp_server_info(server_name)
    return str(info.get("short", server_name))


def is_mcp_server_default(server_name: str) -> bool:
    """Check if an MCP server is enabled by default.

    Args:
        server_name: Name of the MCP server

    Returns:
        True if default enabled, False otherwise
    """
    info = get_mcp_server_info(server_name)
    return bool(info.get("default", False))


def get_all_mcp_servers() -> list[str]:
    """Get list of all MCP server names.

    Returns:
        List of MCP server names
    """
    descriptions = load_descriptions()
    return list(descriptions.get("mcp_servers", {}).keys())


def get_term_info(term: str) -> dict[str, Any]:
    """Get information about a technical term.

    Args:
        term: Technical term (e.g., "RLS", "PHI", "HIPAA")

    Returns:
        Dictionary with full_name, short, description, example, why_matters
    """
    descriptions = load_descriptions()
    glossary = cast(dict[str, dict[str, Any]], descriptions.get("glossary", {}))
    return glossary.get(term, {})


def get_term_explanation(term: str) -> str:
    """Get a brief explanation of a technical term.

    Args:
        term: Technical term

    Returns:
        Short explanation string, or the term itself if not found
    """
    info = get_term_info(term)
    if not info:
        return term
    full_name = str(info.get("full_name", ""))
    short = str(info.get("short", ""))
    if full_name and short:
        return f"{term} ({full_name}) - {short}"
    return str(info.get("short", term))


def format_preset_choice(preset_name: str) -> str:
    """Format a preset for display in selection UI.

    Args:
        preset_name: Name of the preset

    Returns:
        Formatted string like "saas - Multi-tenant SaaS (+5 guardrails)"
    """
    short = get_preset_short(preset_name)
    extra = get_preset_extra_guardrails(preset_name)
    return f"{preset_name} - {short} ({extra})"


def format_pack_choice(pack_name: str) -> str:
    """Format a question pack for display in selection UI.

    Args:
        pack_name: Name of the question pack

    Returns:
        Formatted string like "billing - Payment processing, subscriptions"
    """
    short = get_pack_short(pack_name)
    return f"{pack_name} - {short}"


def format_mcp_server_choice(server_name: str) -> str:
    """Format an MCP server for display in selection UI.

    Args:
        server_name: Name of the MCP server

    Returns:
        Formatted string like "spec_inspector - Query spec status"
    """
    short = get_mcp_server_short(server_name)
    return f"{server_name} - {short}"


# Guardrail helpers


def get_guardrail_info(guardrail_id: int) -> dict[str, Any]:
    """Get information about a guardrail by ID.

    Args:
        guardrail_id: Numeric ID of the guardrail (1-30)

    Returns:
        Dictionary with name, short, is_core, severity, preset (optional)
    """
    descriptions = load_descriptions()
    guardrails = descriptions.get("guardrails", {})
    # YAML may parse keys as int or str depending on format
    return guardrails.get(guardrail_id) or guardrails.get(str(guardrail_id)) or {}


def get_core_guardrails() -> list[dict[str, Any]]:
    """Get all core guardrails (always included with any preset).

    Returns:
        List of guardrail info dicts with 'id' field added
    """
    descriptions = load_descriptions()
    guardrails = descriptions.get("guardrails", {})
    result = []
    for gid, info in guardrails.items():
        if isinstance(info, dict) and info.get("is_core", False):
            result.append({"id": int(gid), **info})
    return sorted(result, key=lambda x: x["id"])


def get_preset_guardrails(preset_name: str) -> list[dict[str, Any]]:
    """Get guardrails specific to a preset (not including core).

    Args:
        preset_name: Name of the preset (saas, fintech, healthcare, api-only)

    Returns:
        List of guardrail info dicts with 'id' field added
    """
    descriptions = load_descriptions()
    guardrails = descriptions.get("guardrails", {})
    result = []
    for gid, info in guardrails.items():
        if isinstance(info, dict) and info.get("preset") == preset_name:
            result.append({"id": int(gid), **info})
    return sorted(result, key=lambda x: x["id"])


def get_all_guardrails() -> list[dict[str, Any]]:
    """Get all guardrails (core and preset-specific).

    Returns:
        List of all guardrail info dicts with 'id' field added, sorted by ID
    """
    descriptions = load_descriptions()
    guardrails = descriptions.get("guardrails", {})
    result = []
    for gid, info in guardrails.items():
        if isinstance(info, dict):
            result.append({"id": int(gid), **info})
    return sorted(result, key=lambda x: x["id"])


def format_guardrail_choice(guardrail: dict[str, Any]) -> str:
    """Format a guardrail for display in selection UI.

    Args:
        guardrail: Guardrail info dict with id, name, short

    Returns:
        Formatted string like "1. Testing Coverage - Minimum test coverage"
    """
    gid = guardrail.get("id", 0)
    name = guardrail.get("name", "Unknown")
    short = guardrail.get("short", "")
    return f"{gid}. {name} - {short}"
