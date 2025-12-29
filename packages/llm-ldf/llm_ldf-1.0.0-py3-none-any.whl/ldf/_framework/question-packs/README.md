# LDF Question-Packs

Question-packs ensure critical design decisions are made before writing requirements.

## What are Question-Packs?

Question-packs are YAML files containing domain-specific questions that must be answered before writing a spec. They:

1. **Surface critical decisions early** - Don't discover issues during implementation
2. **Ensure consistency** - Same questions asked for similar features
3. **Create documentation** - Answers captured in answerpacks for reference
4. **Enable automation** - Linter validates questions are answered

## Core Question-Packs

Always included in every project:

| Pack | Domain | Questions |
|------|--------|-----------|
| `security.yaml` | Authentication, authorization, secrets | 12 questions |
| `testing.yaml` | Coverage, strategies, mocking | 8 questions |
| `api-design.yaml` | Versioning, pagination, errors | 10 questions |
| `data-model.yaml` | Schema, migrations, indexes | 9 questions |

## Optional Domain Packs

Create custom packs for your project's domain needs:

| Domain | When to Use | Create as |
|--------|-------------|-----------|
| Billing | Payment processing, invoicing | `.ldf/question-packs/billing.yaml` |
| Multi-tenancy | RLS, tenant isolation for SaaS | `.ldf/question-packs/multi-tenancy.yaml` |
| Provisioning | Async jobs, queues | `.ldf/question-packs/provisioning.yaml` |
| Webhooks | Inbox/outbox, signatures | `.ldf/question-packs/webhooks.yaml` |

See [Creating Custom Question-Packs](#creating-custom-question-packs) below.

## Structure

```yaml
domain: security
description: "Authentication, authorization, and secrets management"
critical: true  # Block if unanswered

questions:
  authentication:
    - question: "What authentication method will be used?"
      critical: true
      options:
        - "JWT with Bearer token"
        - "OAuth 2.0"
        - "Session cookies"
        - "API keys"
      follow_ups:
        - "What is the token expiry time?"
        - "Where are tokens stored?"

    - question: "Is multi-factor authentication required?"
      critical: false
      options:
        - "Required for all users"
        - "Optional, user choice"
        - "Required for sensitive operations"
        - "Not needed"
```

## Answerpacks

Answers are captured in `.ldf/answerpacks/{feature}/{pack}.yaml`:

```yaml
feature_name: "user-auth"
pack: "security"
answered_at: "2025-01-15T10:00:00Z"

answers:
  authentication:
    method: "JWT with Bearer token"
    token_expiry: "15 minutes access, 8 hours refresh"
    storage: "HttpOnly cookies for refresh, memory for access"
    mfa: "Required for sensitive operations"
```

## Usage in Workflow

### During `/project:create-spec`

1. Clarify-first macro loads relevant question-packs
2. Questions asked based on feature scope
3. Answers captured in answerpacks
4. Summary included in requirements.md

### During `ldf lint`

1. Check answerpacks exist for declared packs
2. Validate critical questions are answered
3. Warn on missing optional answers

## Creating Custom Question-Packs

Add custom packs in `.ldf/question-packs/`:

```yaml
# .ldf/question-packs/custom-domain.yaml
domain: custom-domain
description: "Project-specific questions"
critical: false

questions:
  category:
    - question: "Your question here?"
      critical: true
      options:
        - "Option 1"
        - "Option 2"
      examples:
        - "Example answer 1"
        - "Example answer 2"
```

## Best Practices

1. **Critical = blocking** - Only mark critical if the feature can't proceed without answer
2. **Provide options** - Help guide decision-making
3. **Include examples** - Show what good answers look like
4. **Add follow-ups** - Dig deeper when needed
5. **Keep packs focused** - One domain per pack
