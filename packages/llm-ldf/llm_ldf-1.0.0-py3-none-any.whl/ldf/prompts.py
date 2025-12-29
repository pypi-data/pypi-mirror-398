"""Interactive prompts for LDF CLI using questionary.

Provides checkbox-style selection for presets, question packs, and MCP servers
with descriptions displayed inline for better user experience.
"""

from pathlib import Path
from typing import cast

import questionary
from questionary import Choice, Style
from rich.console import Console
from rich.panel import Panel

from ldf.utils.descriptions import (
    format_guardrail_choice,
    format_mcp_server_choice,
    format_pack_choice,
    format_preset_choice,
    get_all_guardrails,
    get_all_mcp_servers,
    get_all_presets,
    get_core_guardrails,
    get_core_packs,
    get_optional_packs,
    get_pack_short,
    get_preset_recommended_packs,
    is_mcp_server_default,
)

console = Console()

# Custom style for questionary to match Rich aesthetics
CUSTOM_STYLE = Style(
    [
        ("qmark", "fg:cyan bold"),
        ("question", "bold"),
        ("answer", "fg:cyan"),
        ("pointer", "fg:cyan bold"),
        ("highlighted", "fg:cyan bold"),
        ("selected", "fg:green"),
        ("instruction", "fg:gray"),
    ]
)


def prompt_project_path() -> Path:
    """Prompt for project path with intelligent defaults and validation.

    Returns:
        Path object for the project directory

    Raises:
        KeyboardInterrupt: If user cancels the prompt
    """
    cwd = Path.cwd()

    # Check if we're inside the LDF package directory
    is_in_ldf = (cwd / "ldf" / "_framework").is_dir() and (cwd / "ldf").is_dir()

    if is_in_ldf:
        # User is in LDF directory, suggest creating project elsewhere
        default_path = str(cwd.parent / "my-project")
        console.print("\n[yellow]Note:[/yellow] You appear to be in the LDF package directory.")
        console.print("Projects should be created in a separate directory.\n")
    else:
        # User is in their own directory, suggest creating subdirectory
        default_path = str(cwd / "my-project")

    def validate_path(path_str: str) -> bool | str:
        """Validate the project path."""
        if not path_str.strip():
            return "Path cannot be empty"

        path = Path(path_str).expanduser().resolve()

        # Check if parent directory exists or can be created
        if not path.parent.exists():
            # Allow if grandparent exists (we'll create parent)
            if not path.parent.parent.exists():
                return f"Parent directory does not exist: {path.parent}"

        # Check if path is a file
        if path.exists() and path.is_file():
            return f"Path is a file, not a directory: {path}"

        return True

    path_str = questionary.text(
        "Enter project path (will be created if needed):",
        default=default_path,
        validate=validate_path,
        style=CUSTOM_STYLE,
    ).ask()

    if path_str is None:
        raise KeyboardInterrupt("User cancelled")

    return Path(path_str).expanduser().resolve()


def prompt_preset() -> str:
    """Prompt user to select a guardrail preset.

    Returns:
        Selected preset name

    Raises:
        KeyboardInterrupt: If user cancels the prompt
    """
    presets = get_all_presets()
    choices = [Choice(title=format_preset_choice(preset), value=preset) for preset in presets]

    console.print("\n[bold]Select a guardrail preset:[/bold]")
    console.print("[dim]Use arrow keys to navigate, Enter to select[/dim]\n")

    result = questionary.select(
        "Preset:",
        choices=choices,
        default="custom",
        style=CUSTOM_STYLE,
        instruction="",
    ).ask()

    if result is None:
        raise KeyboardInterrupt("User cancelled")

    return cast(str, result)


def prompt_question_packs(preset: str) -> list[str]:
    """Prompt user to select question packs with preset-based pre-selection.

    Core packs are always included and shown as informational.
    Optional packs are selectable with preset recommendations pre-checked.

    Args:
        preset: Selected preset name for determining recommendations

    Returns:
        List of selected question pack names (core + selected optional)

    Raises:
        KeyboardInterrupt: If user cancels the prompt
    """
    core_packs = get_core_packs()
    optional_packs = get_optional_packs()
    recommended = get_preset_recommended_packs(preset)

    # Display core packs as always included
    console.print("\n[bold]Core question packs (always included):[/bold]")
    for pack in core_packs:
        description = get_pack_short(pack)
        console.print(f"  [green]\u2713[/green] [cyan]{pack}[/cyan] - {description}")

    # If no optional packs available, just return core packs
    if not optional_packs:
        console.print("\n[dim]No additional question packs available.[/dim]")
        return core_packs

    # Build choices for optional packs
    choices = [
        Choice(
            title=format_pack_choice(pack),
            value=pack,
            checked=pack in recommended,
        )
        for pack in optional_packs
    ]

    console.print("\n[bold]Select additional question packs:[/bold]")
    if recommended:
        console.print(
            f"[dim]Based on [cyan]{preset}[/cyan] preset, "
            f"[green]{', '.join(recommended)}[/green] are pre-selected[/dim]"
        )
    console.print("[dim]Use arrow keys to navigate, Space to toggle, Enter to confirm[/dim]\n")

    selected_optional = questionary.checkbox(
        "Optional packs:",
        choices=choices,
        style=CUSTOM_STYLE,
        instruction="",
    ).ask()

    if selected_optional is None:
        raise KeyboardInterrupt("User cancelled")

    return core_packs + cast(list[str], selected_optional)


def prompt_mcp_servers() -> list[str]:
    """Prompt user to select MCP servers.

    Returns:
        List of selected MCP server names

    Raises:
        KeyboardInterrupt: If user cancels the prompt
    """
    servers = get_all_mcp_servers()

    choices = [
        Choice(
            title=format_mcp_server_choice(server),
            value=server,
            checked=is_mcp_server_default(server),
        )
        for server in servers
    ]

    console.print("\n[bold]Select MCP servers to enable:[/bold]")
    console.print("[dim]MCP servers provide efficient AI access to spec data[/dim]")
    console.print("[dim]Use arrow keys to navigate, Space to toggle, Enter to confirm[/dim]\n")

    result = questionary.checkbox(
        "MCP servers:",
        choices=choices,
        style=CUSTOM_STYLE,
        instruction="",
    ).ask()

    if result is None:
        raise KeyboardInterrupt("User cancelled")

    return cast(list[str], result)


def prompt_install_hooks() -> bool:
    """Prompt whether to install pre-commit hooks.

    Returns:
        True if user wants to install hooks, False otherwise

    Raises:
        KeyboardInterrupt: If user cancels the prompt
    """
    result = questionary.confirm(
        "Install pre-commit hooks for spec validation?",
        default=False,
        style=CUSTOM_STYLE,
    ).ask()

    if result is None:
        raise KeyboardInterrupt("User cancelled")

    return cast(bool, result)


def confirm_initialization(
    project_path: Path,
    preset: str,
    question_packs: list[str],
    mcp_servers: list[str],
    install_hooks: bool = False,
) -> bool:
    """Show configuration summary and confirm initialization.

    Args:
        project_path: Project directory path
        preset: Selected preset name
        question_packs: List of question pack names
        mcp_servers: List of MCP server names
        install_hooks: Whether hooks will be installed

    Returns:
        True if user confirms, False otherwise

    Raises:
        KeyboardInterrupt: If user cancels the prompt
    """
    # Build summary panel
    summary_lines = [
        f"[bold]Project:[/bold] [cyan]{project_path}[/cyan]",
        f"[bold]Preset:[/bold] [cyan]{preset}[/cyan]",
        f"[bold]Question packs:[/bold] [cyan]{', '.join(question_packs)}[/cyan]",
        f"[bold]MCP servers:[/bold] [cyan]{', '.join(mcp_servers) or 'None'}[/cyan]",
        f"[bold]Install hooks:[/bold] [cyan]{'Yes' if install_hooks else 'No'}[/cyan]",
    ]

    console.print()
    console.print(
        Panel(
            "\n".join(summary_lines),
            title="[bold]Configuration Summary[/bold]",
            border_style="cyan",
        )
    )

    result = questionary.confirm(
        "Proceed with initialization?",
        default=True,
        style=CUSTOM_STYLE,
    ).ask()

    if result is None:
        raise KeyboardInterrupt("User cancelled")

    return cast(bool, result)


def prompt_guardrail_mode() -> str:
    """Prompt user to choose between preset or custom guardrail selection.

    Returns:
        "preset" or "custom"

    Raises:
        KeyboardInterrupt: If user cancels the prompt
    """
    choices = [
        Choice(
            title="Use a preset (recommended) - Auto-includes guardrails for your use case",
            value="preset",
        ),
        Choice(
            title="Customize - Cherry-pick individual guardrails",
            value="custom",
        ),
    ]

    console.print("\n[bold]How would you like to configure guardrails?[/bold]")
    console.print("[dim]Use arrow keys to navigate, Enter to select[/dim]\n")

    result = questionary.select(
        "Configuration mode:",
        choices=choices,
        default="preset",
        style=CUSTOM_STYLE,
        instruction="",
    ).ask()

    if result is None:
        raise KeyboardInterrupt("User cancelled")

    return cast(str, result)


def prompt_custom_guardrails() -> list[int]:
    """Prompt user to select individual guardrails.

    Core guardrails are always included and shown as informational.
    Preset-specific guardrails are selectable.

    Returns:
        List of selected guardrail IDs (core + selected optional)

    Raises:
        KeyboardInterrupt: If user cancels the prompt
    """
    core_guardrails = get_core_guardrails()
    all_guardrails = get_all_guardrails()

    # Display core guardrails as always included
    console.print("\n[bold]Core guardrails (always included):[/bold]")
    for g in core_guardrails:
        console.print(f"  [green]✓[/green] [cyan]{g['id']}. {g['name']}[/cyan] - {g['short']}")

    # Get non-core guardrails for selection
    optional_guardrails = [g for g in all_guardrails if not g.get("is_core", False)]

    if not optional_guardrails:
        console.print("\n[dim]No additional guardrails available.[/dim]")
        return [g["id"] for g in core_guardrails]

    # Build choices for optional guardrails, grouped by preset
    current_preset = None
    choices: list[Choice] = []

    for g in optional_guardrails:
        preset = g.get("preset", "other")
        if preset != current_preset:
            current_preset = preset
            # Add a separator/header (using disabled choice)
            choices.append(
                Choice(
                    title=f"── {preset.upper()} ──",
                    value=None,
                    disabled="section header",
                )
            )
        choices.append(
            Choice(
                title=format_guardrail_choice(g),
                value=g["id"],
                checked=False,
            )
        )

    console.print("\n[bold]Select additional guardrails:[/bold]")
    console.print("[dim]Use arrow keys to navigate, Space to toggle, Enter to confirm[/dim]\n")

    selected = questionary.checkbox(
        "Additional guardrails:",
        choices=choices,
        style=CUSTOM_STYLE,
        instruction="",
    ).ask()

    if selected is None:
        raise KeyboardInterrupt("User cancelled")

    # Combine core IDs with selected optional IDs
    core_ids = [g["id"] for g in core_guardrails]
    selected_ids = cast(list[int], [s for s in selected if s is not None])

    return core_ids + selected_ids
