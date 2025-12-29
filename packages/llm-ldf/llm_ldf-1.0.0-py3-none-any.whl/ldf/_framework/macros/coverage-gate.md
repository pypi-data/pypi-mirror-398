# Coverage-Gate Macro

## Purpose
Block spec approval until the guardrail coverage matrix is complete and all guardrails are mapped.

## When to Use
- Before approving `requirements.md`
- During spec review

## Process

### Step 1: Load Active Guardrails

Read from `.ldf/guardrails.yaml`:
1. Load core guardrails (always 8)
2. Load preset guardrails (if preset configured)
3. Load custom guardrails (if defined)

**Example for SaaS project:**
```
Core: 8 guardrails (#1-8)
Preset (saas): 5 guardrails (#9-13)
Custom: 0 guardrails
Total: 13 guardrails to cover
```

### Step 2: Validate Coverage Matrix Exists

Check `requirements.md` contains:
```markdown
## Guardrail Coverage Matrix
```

If missing → BLOCK

### Step 3: Validate Matrix Structure

The matrix must have these columns:
| Guardrail | Requirements | Design | Tasks/Tests | Owner | Status |

If columns missing → BLOCK

### Step 4: Validate All Guardrails Present

For each active guardrail, verify a row exists:
- Row must include guardrail ID and name
- Missing rows → BLOCK

### Step 5: Validate Row Completeness

For each row:
1. **Requirements** - Must have value or "N/A"
2. **Design** - Must have value or "N/A"
3. **Tasks/Tests** - Can be empty if Status is TODO
4. **Owner** - Must have value if Status is not N/A
5. **Status** - Must be: TODO, IN PROGRESS, DONE, or N/A

**Valid statuses:**
- `TODO` - Not started
- `IN PROGRESS` - Being worked on
- `DONE` or `COMPLETE` - Finished
- `N/A - [reason]` - Not applicable (requires justification)

### Step 6: Validate N/A Justifications

If Status is "N/A", must include justification:
- ❌ "N/A" alone
- ✅ "N/A - No database changes"
- ✅ "N/A - Feature is read-only"

### Step 7: Report Findings

**Success:**
```
✅ Guardrail Coverage Matrix Complete

Active guardrails: 13
- Covered: 10
- N/A (justified): 3
- Missing: 0

Matrix is complete. You may approve requirements.
```

**Failure:**
```
🚫 BLOCKED: Guardrail Coverage Incomplete

Issues found:
  - Row 5 (API Design): Missing Requirements link
  - Row 9 (Multi-Tenancy): Status "N/A" needs justification
  - Row 12 (Audit Logging): Owner not specified

Please address these issues before approval.
```

## Matrix Template

```markdown
## Guardrail Coverage Matrix
**Reference:** `.ldf/guardrails.yaml`

| Guardrail | Requirements | Design | Tasks/Tests | Owner | Status |
|-----------|--------------|--------|-------------|-------|--------|
| 1. Testing Coverage | [US-1.3] | [§5.1] | [T-5.1, T-5.2] | Alice | TODO |
| 2. Security Basics | [US-2.1, US-2.2] | [§4.1] | [T-4.1] | Bob | TODO |
| 3. Error Handling | [US-3.1] | [§3.4] | [T-3.4] | Alice | TODO |
| 4. Logging | [NFR-1] | [§3.5] | [T-3.5] | Bob | TODO |
| 5. API Design | [US-1.1] | [§2.1] | [T-2.1] | Alice | TODO |
| 6. Data Validation | [US-2.3] | [§3.2] | [T-3.2] | Bob | TODO |
| 7. Migrations | [US-1.2] | [§2.2] | [T-1.2] | Alice | TODO |
| 8. Documentation | [NFR-2] | [§6.1] | [T-6.1] | Bob | TODO |
| 9. Multi-Tenancy | N/A - single tenant | N/A | N/A | N/A | N/A |
```

## Blocking Conditions

**BLOCKED if:**
- "## Guardrail Coverage Matrix" section missing
- Required columns missing
- Any active guardrail has no row
- Any cell empty without N/A justification
- Any row missing Owner (except N/A rows)

## Notes

- Run after requirements are drafted, before approval
- Re-run after design is drafted
- Can be automated via `ldf lint`
- Critical severity guardrails cannot be marked N/A without strong justification
