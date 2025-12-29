"""LDF Git hooks management."""

from pathlib import Path
from typing import Any

import click

from ldf.utils.console import console
from ldf.utils.hooks import (
    detect_project_languages,
    get_default_hooks_config,
    get_git_hooks_dir,
    get_hook_config,
    install_hook,
    is_hook_installed,
    uninstall_hook,
    update_config_with_hooks,
)


def install_hooks(
    detect_linters: bool = True,
    non_interactive: bool = False,
    project_root: Path | None = None,
) -> bool:
    """Install LDF pre-commit hooks.

    Args:
        detect_linters: Whether to auto-detect and suggest language linters
        non_interactive: Skip prompts and use defaults
        project_root: Project root directory

    Returns:
        True if installation was successful
    """
    if project_root is None:
        project_root = Path.cwd()

    # Check if LDF is initialized FIRST (most likely user error)
    ldf_dir = project_root / ".ldf"
    if not ldf_dir.exists():
        console.print("[red]Error: LDF not initialized.[/red]")
        console.print("[dim]Run 'ldf init' first to initialize the project.[/dim]")
        return False

    # Then check if it's a git repo
    git_hooks_dir = get_git_hooks_dir(project_root)
    if git_hooks_dir is None:
        console.print("[red]Error: Not a git repository.[/red]")
        console.print("[dim]Initialize git first with 'git init'[/dim]")
        return False

    # Check if hook is already installed
    if is_hook_installed(project_root):
        if non_interactive:
            console.print("[yellow]Hook already installed, reinstalling...[/yellow]")
        else:
            if not click.confirm(
                "LDF pre-commit hook is already installed. Reinstall?", default=True
            ):
                console.print("[dim]Installation cancelled.[/dim]")
                return False

    # Start with default config
    hook_config = get_default_hooks_config()

    # Detect languages and prompt for linter configuration
    if detect_linters and not non_interactive:
        languages = detect_project_languages(project_root)
        hook_config = _configure_linters_interactive(hook_config, languages)
    elif detect_linters:
        # Non-interactive but with detection - enable detected languages
        languages = detect_project_languages(project_root)
        hook_config = _configure_linters_auto(hook_config, languages)

    # Install the hook
    try:
        install_hook(hook_config, project_root)
    except RuntimeError as e:
        console.print(f"[red]Error: {e}[/red]")
        return False

    # Save configuration
    update_config_with_hooks(hook_config, project_root)

    console.print("\n[green]Pre-commit hook installed successfully![/green]")
    console.print("[dim]The hook will run on every commit.[/dim]")
    console.print("[dim]Bypass with: git commit --no-verify[/dim]")

    # Show what's enabled
    _print_hook_summary(hook_config)

    return True


def uninstall_hooks(project_root: Path | None = None) -> bool:
    """Uninstall LDF pre-commit hooks.

    Args:
        project_root: Project root directory

    Returns:
        True if uninstallation was successful
    """
    if project_root is None:
        project_root = Path.cwd()

    if not is_hook_installed(project_root):
        console.print("[yellow]No LDF pre-commit hook is installed.[/yellow]")
        return False

    if uninstall_hook(project_root):
        console.print("[green]Pre-commit hook uninstalled successfully.[/green]")
        return True
    else:
        console.print("[red]Failed to uninstall hook.[/red]")
        return False


def get_hooks_status(project_root: Path | None = None) -> dict[str, Any]:
    """Get the current hook installation status.

    Args:
        project_root: Project root directory

    Returns:
        Status dictionary with installation and configuration info
    """
    if project_root is None:
        project_root = Path.cwd()

    git_hooks_dir = get_git_hooks_dir(project_root)
    is_git_repo = git_hooks_dir is not None
    hook_installed = is_hook_installed(project_root) if is_git_repo else False
    hook_config = get_hook_config(project_root)
    detected_languages = detect_project_languages(project_root)

    return {
        "is_git_repo": is_git_repo,
        "hook_installed": hook_installed,
        "config": hook_config,
        "detected_languages": detected_languages,
    }


def print_hooks_status(project_root: Path | None = None) -> None:
    """Print the current hook status to console.

    Args:
        project_root: Project root directory
    """
    status = get_hooks_status(project_root)

    console.print("\n[bold]LDF Pre-Commit Hook Status[/bold]\n")

    # Git repo check
    if not status["is_git_repo"]:
        console.print("[red]Not a git repository[/red]")
        return

    # Installation status
    if status["hook_installed"]:
        console.print("[green]✓[/green] Hook installed")
    else:
        console.print("[yellow]✗[/yellow] Hook not installed")
        console.print("[dim]  Run 'ldf hooks install' to install[/dim]")

    # Configuration
    config = status["config"]
    pre_commit = config.get("pre_commit", {})

    console.print("\n[bold]Configuration:[/bold]")
    run_all = pre_commit.get("run_on_all_commits", True)
    console.print(f"  Run on all commits: {'Yes' if run_all else 'No (spec changes only)'}")
    console.print(f"  Strict mode: {'Yes' if pre_commit.get('strict', False) else 'No'}")
    console.print(
        f"  Spec linting: {'Enabled' if pre_commit.get('spec_lint', True) else 'Disabled'}"
    )

    # Language linters
    console.print("\n[bold]Language Linters:[/bold]")
    for lang in ["python", "typescript", "go"]:
        lang_config = pre_commit.get(lang, {})
        enabled = lang_config.get("enabled", False)
        tools = lang_config.get("tools", [])
        detected = status["detected_languages"].get(lang, False)

        status_str = "[green]enabled[/green]" if enabled else "[dim]disabled[/dim]"
        detected_str = " (detected)" if detected else ""
        tools_str = f" [{', '.join(tools)}]" if enabled and tools else ""

        console.print(f"  {lang.capitalize()}: {status_str}{tools_str}{detected_str}")


def _configure_linters_interactive(
    hook_config: dict[str, Any], languages: dict[str, bool]
) -> dict[str, Any]:
    """Interactively configure language linters.

    Args:
        hook_config: Current hook configuration
        languages: Detected languages

    Returns:
        Updated hook configuration
    """
    console.print("\n[bold]Language Linter Configuration[/bold]")
    console.print("[dim]Detected project files. Configure optional linters:[/dim]\n")

    pre_commit = hook_config.get("pre_commit", {})

    # Python
    if languages.get("python"):
        console.print("[cyan]Python[/cyan] project detected (pyproject.toml/setup.py)")
        if click.confirm("  Enable Python linting (ruff)?", default=False):
            pre_commit["python"] = {"enabled": True, "tools": ["ruff"]}
            console.print("  [green]✓[/green] Python linting enabled")
        else:
            console.print("  [dim]✗[/dim] Python linting disabled")
    else:
        console.print("[dim]Python: not detected[/dim]")

    # TypeScript/JavaScript
    if languages.get("typescript"):
        console.print("\n[cyan]TypeScript/JavaScript[/cyan] project detected (package.json)")
        if click.confirm("  Enable TypeScript/JS linting (eslint)?", default=False):
            pre_commit["typescript"] = {"enabled": True, "tools": ["eslint"]}
            console.print("  [green]✓[/green] TypeScript/JS linting enabled")
        else:
            console.print("  [dim]✗[/dim] TypeScript/JS linting disabled")
    else:
        console.print("[dim]TypeScript/JS: not detected[/dim]")

    # Go
    if languages.get("go"):
        console.print("\n[cyan]Go[/cyan] project detected (go.mod)")
        if click.confirm("  Enable Go linting (golangci-lint)?", default=False):
            pre_commit["go"] = {"enabled": True, "tools": ["golangci-lint"]}
            console.print("  [green]✓[/green] Go linting enabled")
        else:
            console.print("  [dim]✗[/dim] Go linting disabled")
    else:
        console.print("[dim]Go: not detected[/dim]")

    # Check if multiple linters are enabled
    enabled_count = sum(
        1
        for lang in ["python", "typescript", "go"]
        if pre_commit.get(lang, {}).get("enabled", False)
    )
    if enabled_count > 1:
        console.print(
            "\n[yellow]Note: Multiple linters enabled. This may slow down commits.[/yellow]"
        )
        console.print("[dim]Consider setting run_on_all_commits: false in config.yaml[/dim]")

    hook_config["pre_commit"] = pre_commit
    return hook_config


def _configure_linters_auto(
    hook_config: dict[str, Any], languages: dict[str, bool]
) -> dict[str, Any]:
    """Automatically configure language linters based on detection.

    For non-interactive mode - enables detected languages.

    Args:
        hook_config: Current hook configuration
        languages: Detected languages

    Returns:
        Updated hook configuration
    """
    pre_commit = hook_config.get("pre_commit", {})

    if languages.get("python"):
        pre_commit["python"] = {"enabled": True, "tools": ["ruff"]}

    if languages.get("typescript"):
        pre_commit["typescript"] = {"enabled": True, "tools": ["eslint"]}

    if languages.get("go"):
        pre_commit["go"] = {"enabled": True, "tools": ["golangci-lint"]}

    hook_config["pre_commit"] = pre_commit
    return hook_config


def _print_hook_summary(hook_config: dict[str, Any]) -> None:
    """Print a summary of enabled hooks.

    Args:
        hook_config: Hook configuration
    """
    pre_commit = hook_config.get("pre_commit", {})

    console.print("\n[bold]Enabled checks:[/bold]")
    console.print("  [green]✓[/green] LDF spec linting")

    for lang, display in [
        ("python", "Python (ruff)"),
        ("typescript", "TypeScript/JS (eslint)"),
        ("go", "Go (golangci-lint)"),
    ]:
        if pre_commit.get(lang, {}).get("enabled", False):
            console.print(f"  [green]✓[/green] {display}")
