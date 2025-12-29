# Changelog

All notable changes to LDF (LLM Development Framework) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-12-26

### Added

#### Core CLI Commands
- **`ldf init`** - Initialize LDF in a project with presets, question-packs, and MCP servers
- **`ldf status`** - Show project state and framework version
- **`ldf lint`** - Validate specs with optional strict mode and CI-friendly output
- **`ldf create-spec`** - Create new specs interactively or with templates
- **`ldf audit`** - Generate and import multi-agent audit prompts
- **`ldf coverage`** - Report test coverage mapped to specs
- **`ldf convert`** - Convert existing codebases to LDF methodology
- **`ldf update`** - Update framework files with conflict resolution
- **`ldf hooks`** - Install/remove git pre-commit hooks for spec validation
- **`ldf doctor`** - Run project health checks
- **`ldf mcp-config`** - Generate MCP server configuration for Claude/Cursor/Gemini
- **`ldf export-docs`** - Export documentation for review

#### Guardrails System
- **8 Core Guardrails** - Testing, Security, Error Handling, Logging, API Design, Data Validation, Database Migrations, Documentation
- **4 Domain Presets** - saas, fintech, healthcare, api-only
- **Custom Guardrails** - Define project-specific guardrails in YAML
- **Guardrail Coverage Matrix** - Track coverage across requirements, design, and tasks

#### Question-Packs
- **security** - Authentication, authorization, data protection decisions
- **testing** - Test strategy, coverage requirements, mocking approaches
- **api-design** - Versioning, pagination, error format decisions
- **data-model** - Schema design, relationships, migration strategy

#### Template System
- **Jinja2 Macros** - clarify-first, coverage-gate, task-guardrails
- **Template Import/Export** - Share configurations across projects
- **Markdown Templates** - requirements.md, design.md, tasks.md formats

#### MCP Server Integration
- **spec_inspector** - Query spec status and guardrail coverage (90% token savings)
- **coverage_reporter** - Report test coverage metrics per spec
- **db_inspector** - Database schema inspection template

#### Multi-Agent Audit Workflow
- **ChatGPT Integration** - Generate prompts and import feedback via API
- **Gemini Integration** - Architecture review and gap analysis
- **Audit Types** - spec-review, security-check, gap-analysis, edge-cases
- **Audit History** - Track and compare audits over time

#### Security Hardening
- **Path Traversal Prevention** - Validates all spec names and paths
- **Symlink Escape Protection** - Prevents symlink-based directory escapes
- **Safe Template Import** - Validates zip archives before extraction
- **Input Validation** - Comprehensive validation at all entry points

#### Cross-Platform Support
- **Windows** - Full support including batch file handling
- **macOS** - Native support with Homebrew compatibility
- **Linux** - Tested on Ubuntu, Fedora, and derivatives

### Commands Reference

| Command | Description |
|---------|-------------|
| `ldf init` | Initialize LDF in a project |
| `ldf status` | Show project state |
| `ldf lint [SPEC]` | Validate spec(s) |
| `ldf create-spec NAME` | Create a new spec |
| `ldf audit --type TYPE --spec SPEC` | Run multi-agent audit |
| `ldf coverage` | Report test coverage |
| `ldf convert` | Convert existing codebase |
| `ldf update` | Update framework files |
| `ldf hooks install` | Install git hooks |
| `ldf doctor` | Check project health |
| `ldf mcp-config` | Generate MCP config |

### Dependencies
- Python 3.10+
- click >= 8.0.0
- pyyaml >= 6.0
- rich >= 13.0.0
- jinja2 >= 3.0.0
- questionary >= 2.0.0

### Optional Dependencies
- **mcp**: MCP server support (mcp >= 0.9.0, coverage >= 7.0.0)
- **automation**: API integration (openai >= 1.0.0, google-generativeai >= 0.3.0)
- **s3**: S3 template storage (boto3 >= 1.26.0)
