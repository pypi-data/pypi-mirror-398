"""LDF API integration for automated audits.

Provides integration with OpenAI (ChatGPT) and Google (Gemini) APIs
for automated spec auditing.
"""

import asyncio
import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from ldf.utils.console import console


@dataclass
class AuditConfig:
    """Configuration for API-based audits."""

    provider: str  # "chatgpt" or "gemini"
    api_key: str
    model: str
    timeout: int = 120
    max_tokens: int = 4096


@dataclass
class AuditResponse:
    """Response from an API audit."""

    success: bool
    provider: str
    audit_type: str
    spec_name: str | None
    content: str
    timestamp: str
    errors: list[str] = field(default_factory=list)
    usage: dict[str, Any] = field(default_factory=dict)


class BaseAuditor(ABC):
    """Abstract base class for audit providers."""

    def __init__(self, config: AuditConfig):
        self.config = config

    @abstractmethod
    async def audit(
        self, prompt: str, audit_type: str, spec_name: str | None = None
    ) -> AuditResponse:
        """Run an audit with the given prompt.

        Args:
            prompt: The audit prompt content
            audit_type: Type of audit being performed
            spec_name: Optional name of specific spec being audited

        Returns:
            AuditResponse with the audit results
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name for logging."""
        pass


class ChatGPTAuditor(BaseAuditor):
    """OpenAI ChatGPT auditor implementation."""

    @property
    def provider_name(self) -> str:
        return "chatgpt"

    async def audit(
        self, prompt: str, audit_type: str, spec_name: str | None = None
    ) -> AuditResponse:
        """Run an audit using OpenAI's ChatGPT API."""
        timestamp = datetime.now().isoformat()
        errors: list[str] = []

        try:
            # Import openai only when needed (optional dependency)
            try:
                import openai  # type: ignore[import-not-found]
            except ImportError:
                return AuditResponse(
                    success=False,
                    provider=self.provider_name,
                    audit_type=audit_type,
                    spec_name=spec_name,
                    content="",
                    timestamp=timestamp,
                    errors=[
                        "OpenAI package not installed. Install with: pip install 'ldf[automation]'"
                    ],
                )

            client = openai.AsyncOpenAI(api_key=self.config.api_key)

            system_prompt = self._get_system_prompt(audit_type)

            response = await asyncio.wait_for(
                client.chat.completions.create(
                    model=self.config.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=self.config.max_tokens,
                ),
                timeout=self.config.timeout,
            )

            content = response.choices[0].message.content or ""
            usage = {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            }

            return AuditResponse(
                success=True,
                provider=self.provider_name,
                audit_type=audit_type,
                spec_name=spec_name,
                content=content,
                timestamp=timestamp,
                usage=usage,
            )

        except asyncio.TimeoutError:
            errors.append(f"Request timed out after {self.config.timeout} seconds")
        except Exception as e:
            errors.append(f"API error: {str(e)}")

        return AuditResponse(
            success=False,
            provider=self.provider_name,
            audit_type=audit_type,
            spec_name=spec_name,
            content="",
            timestamp=timestamp,
            errors=errors,
        )

    def _get_system_prompt(self, audit_type: str) -> str:
        """Get the system prompt for the audit type."""
        base = (
            "You are an expert software architect and security reviewer. "
            "You are reviewing specifications for a software project. "
            "Provide thorough, actionable feedback in markdown format."
        )

        type_specifics = {
            "spec-review": "Focus on requirements completeness, clarity, and guardrail coverage.",
            "code-audit": "Focus on code quality, security vulnerabilities, and best practices.",
            "security": "Focus on security vulnerabilities, OWASP Top 10, and secure coding.",
            "pre-launch": "Focus on production readiness, monitoring, and incident response.",
            "gap-analysis": "Focus on missing requirements, untested scenarios, and coverage gaps.",
            "edge-cases": "Focus on boundary conditions, error handling, and edge case scenarios.",
            "architecture": "Focus on system design, scalability, and component interactions.",
            "full": "Provide a comprehensive review covering all aspects.",
        }

        return f"{base}\n\n{type_specifics.get(audit_type, type_specifics['spec-review'])}"


class GeminiAuditor(BaseAuditor):
    """Google Gemini auditor implementation."""

    @property
    def provider_name(self) -> str:
        return "gemini"

    async def audit(
        self, prompt: str, audit_type: str, spec_name: str | None = None
    ) -> AuditResponse:
        """Run an audit using Google's Gemini API."""
        timestamp = datetime.now().isoformat()
        errors: list[str] = []

        try:
            # Import google.generativeai only when needed (optional dependency)
            try:
                import google.generativeai as genai  # type: ignore[import-not-found]
            except ImportError:
                return AuditResponse(
                    success=False,
                    provider=self.provider_name,
                    audit_type=audit_type,
                    spec_name=spec_name,
                    content="",
                    timestamp=timestamp,
                    errors=[
                        "Google Generative AI package not installed. "
                        "Install with: pip install 'ldf[automation]'"
                    ],
                )

            genai.configure(api_key=self.config.api_key)
            model = genai.GenerativeModel(self.config.model)

            system_prompt = self._get_system_prompt(audit_type)
            full_prompt = f"{system_prompt}\n\n---\n\n{prompt}"

            # Gemini doesn't have native async, so run in executor
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: model.generate_content(full_prompt),
                ),
                timeout=self.config.timeout,
            )

            content = response.text if response.text else ""

            return AuditResponse(
                success=True,
                provider=self.provider_name,
                audit_type=audit_type,
                spec_name=spec_name,
                content=content,
                timestamp=timestamp,
            )

        except asyncio.TimeoutError:
            errors.append(f"Request timed out after {self.config.timeout} seconds")
        except Exception as e:
            errors.append(f"API error: {str(e)}")

        return AuditResponse(
            success=False,
            provider=self.provider_name,
            audit_type=audit_type,
            spec_name=spec_name,
            content="",
            timestamp=timestamp,
            errors=errors,
        )

    def _get_system_prompt(self, audit_type: str) -> str:
        """Get the system prompt for the audit type."""
        # Same as ChatGPT
        base = (
            "You are an expert software architect and security reviewer. "
            "You are reviewing specifications for a software project. "
            "Provide thorough, actionable feedback in markdown format."
        )

        type_specifics = {
            "spec-review": "Focus on requirements completeness, clarity, and guardrail coverage.",
            "code-audit": "Focus on code quality, security vulnerabilities, and best practices.",
            "security": "Focus on security vulnerabilities, OWASP Top 10, and secure coding.",
            "pre-launch": "Focus on production readiness, monitoring, and incident response.",
            "gap-analysis": "Focus on missing requirements, untested scenarios, and coverage gaps.",
            "edge-cases": "Focus on boundary conditions, error handling, and edge case scenarios.",
            "architecture": "Focus on system design, scalability, and component interactions.",
            "full": "Provide a comprehensive review covering all aspects.",
        }

        return f"{base}\n\n{type_specifics.get(audit_type, type_specifics['spec-review'])}"


def load_api_config(project_root: Path | None = None) -> dict[str, AuditConfig]:
    """Load API configuration from .ldf/config.yaml.

    Args:
        project_root: Project root directory (defaults to cwd)

    Returns:
        Dict mapping provider names to AuditConfig objects
    """
    if project_root is None:
        project_root = Path.cwd()

    config_path = project_root / ".ldf" / "config.yaml"
    if not config_path.exists():
        return {}

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f) or {}
    except Exception:
        return {}

    audit_api_config = config.get("audit_api", {})
    configs: dict[str, AuditConfig] = {}

    # ChatGPT config
    if "chatgpt" in audit_api_config:
        chatgpt = audit_api_config["chatgpt"]
        api_key = _resolve_env_var(chatgpt.get("api_key", ""))
        if api_key:
            configs["chatgpt"] = AuditConfig(
                provider="chatgpt",
                api_key=api_key,
                model=chatgpt.get("model", "gpt-4"),
                timeout=chatgpt.get("timeout", 120),
                max_tokens=chatgpt.get("max_tokens", 4096),
            )

    # Gemini config
    if "gemini" in audit_api_config:
        gemini = audit_api_config["gemini"]
        api_key = _resolve_env_var(gemini.get("api_key", ""))
        if api_key:
            configs["gemini"] = AuditConfig(
                provider="gemini",
                api_key=api_key,
                model=gemini.get("model", "gemini-pro"),
                timeout=gemini.get("timeout", 120),
                max_tokens=gemini.get("max_tokens", 4096),
            )

    return configs


def _resolve_env_var(value: str) -> str:
    """Resolve environment variable references in config values.

    Supports ${VAR_NAME} syntax.
    """
    if not value:
        return value

    # Match ${VAR_NAME} pattern
    pattern = r"\$\{([^}]+)\}"
    matches = re.findall(pattern, value)

    result = value
    for var_name in matches:
        env_value = os.environ.get(var_name, "")
        result = result.replace(f"${{{var_name}}}", env_value)

    return result


def get_auditor(provider: str, configs: dict[str, AuditConfig] | None = None) -> BaseAuditor | None:
    """Get an auditor instance for the specified provider.

    Args:
        provider: Provider name ("chatgpt" or "gemini")
        configs: Optional pre-loaded configs (loads from config.yaml if not provided)

    Returns:
        Auditor instance or None if not configured
    """
    if configs is None:
        configs = load_api_config()

    if provider not in configs:
        return None

    config = configs[provider]

    if provider == "chatgpt":
        return ChatGPTAuditor(config)
    elif provider == "gemini":
        return GeminiAuditor(config)

    return None


async def run_api_audit(
    provider: str,
    audit_type: str,
    prompt: str,
    spec_name: str | None = None,
) -> AuditResponse:
    """Run an API-based audit.

    Args:
        provider: Provider to use ("chatgpt" or "gemini")
        audit_type: Type of audit
        prompt: Audit prompt content
        spec_name: Optional specific spec name

    Returns:
        AuditResponse with results
    """
    auditor = get_auditor(provider)

    if auditor is None:
        return AuditResponse(
            success=False,
            provider=provider,
            audit_type=audit_type,
            spec_name=spec_name,
            content="",
            timestamp=datetime.now().isoformat(),
            errors=[
                f"Provider '{provider}' not configured. "
                f"Add audit_api.{provider} to .ldf/config.yaml"
            ],
        )

    console.print(f"[blue]Running {audit_type} audit with {provider}...[/blue]")

    response = await auditor.audit(prompt, audit_type, spec_name)

    if response.success:
        console.print(f"[green]Audit complete ({response.provider})[/green]")
        if response.usage:
            console.print(f"[dim]Tokens used: {response.usage.get('total_tokens', 'N/A')}[/dim]")
    else:
        console.print(f"[red]Audit failed: {', '.join(response.errors)}[/red]")

    return response


def _sanitize_filename_component(s: str) -> str:
    """Remove path separators and traversal sequences from filename component.

    Prevents path traversal attacks when user-provided values are used in filenames.

    Args:
        s: String to sanitize

    Returns:
        Sanitized string safe for use in filenames
    """
    # Replace path separators and parent directory references with underscores
    return s.replace("/", "_").replace("\\", "_").replace("..", "_")


def save_audit_response(response: AuditResponse, project_root: Path | None = None) -> Path:
    """Save an audit response to the audit history.

    Args:
        response: The audit response to save
        project_root: Project root (defaults to cwd)

    Returns:
        Path to the saved file
    """
    if project_root is None:
        project_root = Path.cwd()

    audit_dir = project_root / ".ldf" / "audit-history"
    audit_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    # Sanitize user-provided components to prevent path traversal attacks
    safe_audit_type = _sanitize_filename_component(response.audit_type)
    safe_spec_name = _sanitize_filename_component(response.spec_name) if response.spec_name else ""
    safe_provider = _sanitize_filename_component(response.provider)
    spec_suffix = f"-{safe_spec_name}" if safe_spec_name else ""
    filename = f"{safe_audit_type}{spec_suffix}-{safe_provider}-{timestamp}.md"

    output_path = audit_dir / filename

    # Build content with metadata header
    content = f"""# Audit Response: {response.audit_type}

**Provider:** {response.provider}
**Timestamp:** {response.timestamp}
**Spec:** {response.spec_name or "all"}
**Status:** {"Success" if response.success else "Failed"}

---

{response.content}
"""

    if response.errors:
        content += "\n\n## Errors\n\n"
        for error in response.errors:
            content += f"- {error}\n"

    output_path.write_text(content)
    return output_path
