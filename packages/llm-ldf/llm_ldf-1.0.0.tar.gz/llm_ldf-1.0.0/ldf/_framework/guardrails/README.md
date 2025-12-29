# LDF Guardrails

Guardrails are constraints that must be satisfied for every feature. They ensure consistent quality across your codebase.

## Core Guardrails

The 8 core guardrails in `core.yaml` apply to most software projects:

| ID | Name | Severity | Description |
|----|------|----------|-------------|
| 1 | Testing Coverage | Critical | ≥80% coverage, ≥90% for critical paths |
| 2 | Security Basics | Critical | OWASP Top 10 prevention |
| 3 | Error Handling | High | Consistent error responses |
| 4 | Logging & Observability | High | Structured logging, correlation IDs |
| 5 | API Design | High | Versioning, pagination, error format |
| 6 | Data Validation | Critical | Input validation at boundaries |
| 7 | Database Migrations | High | Reversible, separate backfills |
| 8 | Documentation | Medium | API docs, inline comments |

## Presets

Presets add domain-specific guardrails:

### SaaS (`presets/saas.yaml`)
- Row-Level Security (RLS)
- Multi-tenancy isolation
- Subscription billing
- Audit logging
- Data isolation

### Fintech (`presets/fintech.yaml`)
- Double-entry ledger
- Money precision (NUMERIC)
- Audit trails
- Compliance logging
- Idempotency everywhere
- Reconciliation
- Rate limiting

### Healthcare (`presets/healthcare.yaml`)
- HIPAA compliance
- PHI handling
- Access logging
- Encryption at rest
- Consent management
- Data retention

### API-Only (`presets/api-only.yaml`)
- API versioning
- Rate limiting tiers
- Webhook signatures

## Configuration

### Project Configuration

In `.ldf/guardrails.yaml`:

```yaml
preset: "saas"   # Preset: core (default), saas, fintech, healthcare, api-only, custom

# Override specific guardrails by string ID
overrides:
  "1":
    enabled: true
    config:
      default_threshold: 85  # Increase from 80%

# Disable guardrails by ID or name
disabled:
  - 8                          # By numeric ID
  - "Documentation"            # By name

# Add custom guardrails
custom:
  - id: 101
    name: "Custom Guardrail"
    description: "Project-specific requirement"
    severity: high
    enabled: true
```

### Severity Levels

| Level | Meaning | Enforcement |
|-------|---------|-------------|
| Critical | Must be addressed | Blocks approval |
| High | Should be addressed | Warning, blocks launch |
| Medium | Recommended | Warning only |
| Low | Nice to have | Informational |

## Guardrail Coverage Matrix

Every spec must include a guardrail coverage matrix in `requirements.md`:

```markdown
| Guardrail | Requirements | Design | Tasks/Tests | Owner | Status |
|-----------|--------------|--------|-------------|-------|--------|
| 1. Testing Coverage | [US-1.2] | [§3.1] | [T-4.1] | Alice | TODO |
| 2. Security Basics | [US-2.1] | [§4.2] | [T-5.1] | Bob | IN PROGRESS |
| 3. Error Handling | N/A | N/A | N/A | N/A | N/A - No errors |
```

- Link to specific requirements (US-X.Y)
- Link to design sections (§X.Y)
- Link to task numbers (T-X.Y)
- Mark N/A with justification if not applicable

## Per-Task Checklist

Every task in `tasks.md` should verify applicable guardrails:

```markdown
- [ ] **1. Testing Coverage:** Unit tests; coverage ≥80%
- [ ] **2. Security Basics:** Input validation; auth checks
- [ ] **3. Error Handling:** Proper error responses
- [ ] **4. Logging:** Structured logs; correlation IDs
- [ ] **5. API Design:** Versioned endpoints
- [ ] **6. Data Validation:** Schema validation
- [ ] **7. Migrations:** Reversible; rollback tested
- [ ] **8. Documentation:** API docs updated
```

## Creating Custom Guardrails

Add custom guardrails in `.ldf/guardrails.yaml`:

```yaml
custom:
  - id: 101
    name: "Feature Flags"
    description: "All new features behind flags"
    severity: high
    enabled: true
    checklist:
      - "Feature flag created in config"
      - "Flag checked before feature code"
      - "Rollback plan documented"
    config:
      flag_prefix: "feature_"
```

## Validation

Run `ldf lint` to validate guardrail coverage:

```bash
ldf lint                    # Lint all specs
ldf lint user-auth          # Lint single spec
```

The linter checks:
1. Guardrail coverage matrix exists
2. All active guardrails have entries
3. No guardrail marked TODO without owner
4. Per-task checklists present

## Best Practices

1. **Don't disable without justification** - Document why in `.ldf/guardrails.yaml`
2. **Be specific in coverage matrix** - Link to actual requirements, not "see design"
3. **Update status promptly** - Mark DONE when implemented
4. **Custom guardrails for patterns** - If you check something repeatedly, make it a guardrail
