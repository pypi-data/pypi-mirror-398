# How LDF Works

LDF (LLM Development Framework) is a spec-driven development methodology designed for AI-assisted software engineering.

## Core Philosophy

**No code before spec approval.** Every feature goes through three phases:

1. **Requirements** - What to build (user stories, acceptance criteria)
2. **Design** - How to build it (architecture, APIs, data models)
3. **Tasks** - Step-by-step implementation plan with guardrail checklists

## The Three Phases

### Phase 1: Requirements (`requirements.md`)

Before writing requirements, answer relevant **question-packs**:
- Security questions (auth, validation, secrets)
- Testing questions (coverage, strategies)
- API design questions (versioning, pagination)
- Data model questions (schema, migrations)
- Domain-specific questions (billing, multi-tenancy, etc.)

The requirements document includes:
- Overview and business purpose
- Question-pack answers (captured in answerpacks)
- Guardrail coverage matrix
- User stories in EARS format
- Non-functional requirements
- Dependencies

**Approval gate:** Requirements must be approved before design.

### Phase 2: Design (`design.md`)

The design document maps requirements to implementation:
- Architecture diagrams (Mermaid)
- Guardrail mapping (how each guardrail is addressed)
- Component specifications
- Data models
- API endpoint definitions
- Sequence diagrams
- Security considerations
- Testing strategy

**Approval gate:** Design must be approved before tasks.

### Phase 3: Tasks (`tasks.md`)

The tasks document breaks work into implementable units:
- Per-task guardrail checklist (verify before coding)
- Numbered tasks with dependencies
- Test requirements per task
- Phase organization (setup, logic, API, frontend, testing)

**Implementation gate:** Each task verified against guardrails.

## Guardrails

Guardrails are constraints that must be satisfied. LDF includes 8 core guardrails:

1. **Testing Coverage** - Minimum coverage thresholds (≥80%, ≥90% for critical)
2. **Security Basics** - OWASP Top 10 prevention
3. **Error Handling** - Consistent error responses
4. **Logging & Observability** - Structured logging, correlation IDs
5. **API Design** - Versioning, pagination, error format
6. **Data Validation** - Input validation at boundaries
7. **Database Migrations** - Reversible, separate from backfills
8. **Documentation** - API docs, inline comments

Add more guardrails with presets (saas, fintech, healthcare) or custom definitions.

## Question-Packs

Question-packs ensure critical decisions are made upfront:

```yaml
# security.yaml
domain: security
questions:
  - question: "What authentication method will be used?"
    critical: true
    options: ["JWT", "OAuth", "Session", "API Key"]
  - question: "What authorization strategy?"
    critical: true
    options: ["RBAC", "ABAC", "Resource-based"]
```

Answers are captured in **answerpacks** (YAML files) for traceability.

## Enforcement Macros

Three macros enforce the workflow:

### 1. Clarify-First (`clarify-first.md`)
- Blocks requirements until all critical questions answered
- Loads relevant question-packs
- Generates answerpack files

### 2. Coverage-Gate (`coverage-gate.md`)
- Blocks approval until guardrail coverage matrix complete
- Validates all guardrails mapped to requirements/design
- Ensures no gaps

### 3. Task-Guardrails (`task-guardrails.md`)
- Prepends guardrail checklist to each task
- Blocks implementation until applicable guardrails verified
- Ensures consistent code quality

## MCP Servers

LDF includes MCP servers for real-time validation:

### spec_inspector
Query spec status without reading full files:
- `get_spec_status` - Overall spec metadata
- `get_guardrail_coverage` - Coverage matrix
- `get_tasks` - Task list with status
- `lint_spec` - Run validation

### coverage_reporter
Check test coverage:
- `get_coverage_summary` - Overall metrics
- `get_service_coverage` - Per-service coverage
- `validate_coverage` - Check against thresholds

**Token savings:** 90% reduction vs reading full spec files.

## Multi-Agent Workflow

Use multiple AI agents to audit each other's work:

1. Primary AI drafts spec
2. Run `ldf audit --type spec-review`
3. Copy to ChatGPT/Gemini with audit prompt
4. Import feedback: `ldf audit --import feedback.md`
5. Primary AI incorporates feedback
6. Repeat until approved

## CLI Commands

```bash
ldf init --preset saas          # Initialize LDF
ldf lint                        # Validate specs
ldf audit --type spec-review    # Generate audit request
ldf coverage                    # Check test coverage
```

## Directory Structure

```
.ldf/
├── config.yaml           # Project configuration
├── guardrails.yaml       # Active guardrails
├── question-packs/       # Question templates
├── answerpacks/          # Captured answers
└── specs/
    └── {feature}/
        ├── requirements.md
        ├── design.md
        └── tasks.md
```

## Workflow Summary

```
1. ldf init                    # Setup LDF
2. /project:create-spec {name} # Start new feature
   ↓
   Answer question-packs       # Clarify-first macro
   ↓
   Generate requirements.md    # With guardrail matrix
   ↓
   APPROVAL GATE
   ↓
   Generate design.md          # With guardrail mapping
   ↓
   APPROVAL GATE
   ↓
   Generate tasks.md           # With per-task checklists
   ↓
3. ldf lint                    # Validate spec
4. /project:implement-task     # Implement tasks
   ↓
   Task-guardrails macro       # Verify before coding
   ↓
   Write code + tests
   ↓
   Update task status
5. ldf coverage                # Verify coverage
6. Multi-agent audit           # Final review
```

## Benefits

- **Reduced rework:** Catch issues in requirements, not code
- **Consistent quality:** Guardrails enforce standards
- **Token efficiency:** MCP queries vs file reads
- **Traceability:** Decisions captured in answerpacks
- **Multi-agent validation:** Multiple AI perspectives

## Getting Started

1. Run `ldf init` in your project
2. Review generated `.ldf/` directory
3. Create your first spec with `/project:create-spec`
4. Follow the three-phase workflow
5. Use `ldf lint` to validate before implementation
