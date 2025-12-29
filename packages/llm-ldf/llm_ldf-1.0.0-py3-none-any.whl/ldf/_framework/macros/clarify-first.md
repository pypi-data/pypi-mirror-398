# Clarify-First Macro

## Purpose
Block spec drafting until all critical questions from relevant question-packs are answered.

## When to Use
- Before writing `requirements.md`
- When creating a new feature spec

## Process

### Step 1: Identify Relevant Question-Packs

Based on the feature description, load relevant packs:

**Always include (core packs):**
- `security.yaml` - Every feature touches security
- `testing.yaml` - Every feature needs tests
- `api-design.yaml` - If feature has API endpoints
- `data-model.yaml` - If feature touches database

**Include if applicable (optional packs):**
- `billing.yaml` - If money flows
- `multi-tenancy.yaml` - If tenant isolation needed
- `provisioning.yaml` - If async/background jobs
- `webhooks.yaml` - If events/webhooks involved

### Step 2: Ask Questions

For each loaded question-pack:
1. Present questions in order
2. Mark critical questions with ⚠️
3. Capture answers in structured format
4. Note any blocked/unanswered questions

**Question Format:**
```
⚠️ [CRITICAL] What authentication method will be used?
   Options: JWT, OAuth, Session, API Key
   Your answer: _____________

[OPTIONAL] Is multi-factor authentication required?
   Options: Required, Optional, Sensitive ops only, Not needed
   Your answer: _____________
```

### Step 3: Validate Critical Questions

Check that all critical questions have answers:
- If any critical question is unanswered → BLOCK
- If all critical questions answered → PROCEED

### Step 4: Generate Answerpacks

Create YAML files capturing decisions:

```yaml
# .ldf/answerpacks/{feature}/security.yaml
feature_name: "user-auth"
pack: "security"
answered_at: "2025-01-15T10:00:00Z"

answers:
  authentication:
    method: "JWT with Bearer token"
    provider: "Auth0"
    mfa: "Required for sensitive operations"
  authorization:
    strategy: "RBAC"
    multi_tenancy: "Yes - organization-based"
```

### Step 5: Output Summary

Include in requirements.md:

```markdown
## Question-Pack Answers
**Domains covered:** security, testing, api-design, data-model
**Answerpack location:** `.ldf/answerpacks/user-auth/`

### Key Decisions from Question Packs
- **Security:** JWT auth via Auth0, RBAC authorization, MFA for sensitive ops
- **Testing:** 80% coverage, 90% for auth; pytest with pytest-cov
- **API Design:** REST, /v1/ versioning, cursor pagination, RFC 7807 errors
- **Data Model:** PostgreSQL 15, SQLAlchemy 2.0, UUID v4 IDs, UTC timestamps

### Outstanding Questions / Blocked Items
- None - all questions resolved ✅
```

## Blocking Conditions

**BLOCKED if:**
- Any critical question marked as "unanswered"
- Any critical question answered with "TODO" or "TBD"
- Question-pack file missing for declared domain

**Output when blocked:**
```
🚫 BLOCKED: The following critical questions must be answered:

From security.yaml:
  - What authentication method will be used?
  - What authorization strategy will be used?

Please answer these questions before proceeding with requirements.
```

## Success Output

```
✅ All guardrail clarifications captured

Question-packs completed:
  - security.yaml (12/12 questions)
  - testing.yaml (8/8 questions)
  - api-design.yaml (10/10 questions)
  - data-model.yaml (9/9 questions)

Answerpacks saved to: .ldf/answerpacks/user-auth/

You may now proceed with writing requirements.md
```

## Notes

- Run this macro interactively with the user
- Don't guess answers - ask explicitly
- It's okay to answer "Not applicable" with justification
- Critical questions cannot be skipped
