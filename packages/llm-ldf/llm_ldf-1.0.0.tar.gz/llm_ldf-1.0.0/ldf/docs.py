"""LDF export-docs - Generate framework documentation."""

from pathlib import Path
from typing import Any

import yaml

from ldf.utils.descriptions import (
    get_all_mcp_servers,
    get_mcp_server_info,
    get_pack_info,
    get_preset_info,
)
from ldf.utils.guardrail_loader import get_active_guardrails


def export_docs(
    project_root: Path | None = None,
    output_format: str = "markdown",
    include_sections: tuple[str, ...] | None = None,
) -> str:
    """Generate framework documentation.

    Args:
        project_root: Project root directory
        output_format: Output format (currently only 'markdown' supported)
        include_sections: Tuple of section names to include (preset, guardrails, packs, mcp).
                         If None, all sections are included.

    Returns:
        Generated documentation string
    """
    if project_root is None:
        project_root = Path.cwd()

    ldf_dir = project_root / ".ldf"
    config_path = ldf_dir / "config.yaml"

    # Load project configuration
    config: dict[str, Any] = {}
    if config_path.exists():
        with open(config_path) as f:
            config = yaml.safe_load(f) or {}

    # Default to all sections if not specified
    if include_sections is None:
        include_sections = ("preset", "guardrails", "packs", "mcp")

    # Build documentation
    sections = []

    # Header
    project_name = config.get("project", {}).get("name", project_root.name)
    sections.append(f"# {project_name} - LDF Framework Documentation\n")
    sections.append(
        "This document describes the LLM Development Framework configuration for this project.\n"
    )

    # Preset section
    if "preset" in include_sections:
        sections.append(_generate_preset_section(config))

    # Guardrails section
    if "guardrails" in include_sections:
        sections.append(_generate_guardrails_section(project_root))

    # Question packs section
    if "packs" in include_sections:
        sections.append(_generate_packs_section(config, ldf_dir))

    # MCP servers section
    if "mcp" in include_sections:
        sections.append(_generate_mcp_section(config))

    # Footer
    sections.append(_generate_footer())

    return "\n".join(sections)


def _generate_preset_section(config: dict[str, Any]) -> str:
    """Generate preset documentation section."""
    preset = config.get("guardrails", {}).get("preset", "custom")
    preset_info = get_preset_info(preset)

    lines = [
        "## Project Preset\n",
        f"**Preset:** `{preset}`\n",
    ]

    if preset_info:
        short = preset_info.get("short", "")
        description = preset_info.get("description", "")
        if short:
            lines.append(f"**Summary:** {short}\n")
        if description:
            lines.append(f"{description}\n")

        # Extra guardrails
        extra = preset_info.get("extra_guardrails", "")
        if extra:
            lines.append(f"**Additional Guardrails:** {extra}\n")

        # Recommended packs
        recommended = preset_info.get("recommended_packs", [])
        if recommended:
            lines.append(f"**Recommended Question Packs:** {', '.join(recommended)}\n")

    return "\n".join(lines)


def _generate_guardrails_section(project_root: Path) -> str:
    """Generate guardrails documentation section."""
    guardrails = get_active_guardrails(project_root)

    lines = [
        "## Active Guardrails\n",
        f"This project has **{len(guardrails)}** active guardrails.\n",
    ]

    for g in guardrails:
        lines.append(f"### #{g.id}: {g.name}\n")
        lines.append(f"{g.description}\n")

        # Checklist items
        if g.checklist:
            lines.append("**Checklist:**\n")
            for item in g.checklist:
                lines.append(f"- [ ] {item}")
            lines.append("")

        # Configuration
        if g.config:
            lines.append("**Configuration:**\n")
            for key, value in g.config.items():
                lines.append(f"- `{key}`: {value}")
            lines.append("")

    return "\n".join(lines)


def _generate_packs_section(config: dict[str, Any], ldf_dir: Path) -> str:
    """Generate question packs documentation section."""
    enabled_packs = config.get("question_packs", [])

    lines = [
        "## Question Packs\n",
        f"This project uses **{len(enabled_packs)}** question packs.\n",
    ]

    for pack_name in enabled_packs:
        pack_info = get_pack_info(pack_name)
        short = pack_info.get("short", "")
        is_core = pack_info.get("is_core", False)
        pack_type = "Core" if is_core else "Domain"

        lines.append(f"### {pack_name} ({pack_type})\n")
        if short:
            lines.append(f"{short}\n")

        # Try to load questions from pack file
        pack_path = ldf_dir / "question-packs" / f"{pack_name}.yaml"
        if pack_path.exists():
            try:
                with open(pack_path) as f:
                    pack_data = yaml.safe_load(f) or {}

                questions_data = pack_data.get("questions", {})
                # Questions can be organized by category (dict) or flat (list)
                all_questions: list[dict[str, Any]] = []
                if isinstance(questions_data, dict):
                    # Organized by category
                    for category, category_questions in questions_data.items():
                        if isinstance(category_questions, list):
                            all_questions.extend(category_questions)
                elif isinstance(questions_data, list):
                    all_questions = questions_data

                if all_questions:
                    lines.append(f"**Questions ({len(all_questions)}):**\n")
                    for i, q in enumerate(all_questions[:5], 1):
                        if isinstance(q, dict):
                            q_text = str(q.get("question") or q.get("text") or q)
                        else:
                            q_text = str(q)
                        # Truncate long questions
                        if len(q_text) > 80:
                            q_text = q_text[:77] + "..."
                        lines.append(f"{i}. {q_text}")

                    if len(all_questions) > 5:
                        lines.append(f"\n*... and {len(all_questions) - 5} more questions*")
                    lines.append("")
            except yaml.YAMLError:
                pass

    return "\n".join(lines)


def _generate_mcp_section(config: dict[str, Any]) -> str:
    """Generate MCP servers documentation section."""
    enabled_servers = config.get("mcp_servers", [])

    lines = [
        "## MCP Servers\n",
        f"This project has **{len(enabled_servers)}** MCP servers configured.\n",
    ]

    for server_name in enabled_servers:
        server_info = get_mcp_server_info(server_name)
        short = server_info.get("short", "")
        description = server_info.get("description", "")
        is_default = server_info.get("default", False)

        lines.append(f"### {server_name}")
        if is_default:
            lines.append(" (default)")
        lines.append("\n")

        if short:
            lines.append(f"**Summary:** {short}\n")
        if description:
            lines.append(f"{description}\n")

        # Why it matters
        why = server_info.get("why_matters", "")
        if why:
            lines.append(f"**Why it matters:** {why}\n")

    # List available but not enabled servers
    all_servers = get_all_mcp_servers()
    available = [s for s in all_servers if s not in enabled_servers]
    if available:
        lines.append("### Available (Not Enabled)\n")
        for server_name in available:
            server_info = get_mcp_server_info(server_name)
            short = server_info.get("short", "")
            lines.append(f"- **{server_name}**: {short}")
        lines.append("")

    return "\n".join(lines)


def _generate_footer() -> str:
    """Generate documentation footer."""
    return """
---

*Generated by LDF (LLM Development Framework)*

For more information, see the [LDF documentation](https://github.com/LLMdotInfo/ldf).
"""
