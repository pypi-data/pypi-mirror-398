# {Feature Name} - Requirements

<!-- Replace {Feature Name} with your feature name, e.g., "user-authentication" -->

## Overview

<!-- Example: User authentication system with email/password login and optional MFA support.
     Include the main purpose and 2-3 key capabilities. Keep it to 2-3 sentences. -->

## Question-Pack Answers
**Domains covered:** [List applicable domains from: security, testing, api-design, data-model, billing, multi-tenancy, provisioning, webhooks]
**Answerpack location:** `.ldf/answerpacks/{feature}/*.yaml`

### Key Decisions from Question Packs
- **Security:** [Summary or "N/A"]
- **Testing:** [Summary or "N/A"]
- **API Design:** [Summary or "N/A"]
- **Data Model:** [Summary or "N/A"]
- **[Optional Pack]:** [Add rows for any optional packs used, e.g., billing, multi-tenancy]

### Outstanding Questions / Blocked Items
- [List any questions that couldn't be answered, with assigned owner]
- [Or write "None - all questions resolved"]

## Guardrail Coverage Matrix
**Reference:** `.ldf/guardrails.yaml`

| Guardrail | Requirements | Design | Tasks/Tests | Owner | Status |
|-----------|--------------|---------|-------------|-------|--------|
| 1. Testing Coverage | [Link to US/AC] | [Design section] | [Task #s] | [Name] | TODO |
| 2. Security Basics | | | | | TODO |
| 3. Error Handling | | | | | TODO |
| 4. Logging & Observability | | | | | TODO |
| 5. API Design | | | | | TODO |
| 6. Data Validation | | | | | TODO |
| 7. Database Migrations | | | | | TODO |
| 8. Documentation | | | | | TODO |

**Note:** Mark as "N/A - [reason]" if guardrail not applicable to this feature.
Add rows for any preset-specific guardrails (saas, fintech, healthcare).

## User Stories

<!-- Example user story structure. The WHEN/THE SYSTEM SHALL format (EARS syntax)
     provides unambiguous requirements. Add as many user stories as needed. -->

### US-1: {Story Title}
<!-- Example title: "User Login" -->

**As a** [role]          <!-- e.g., "registered user" -->
**I want to** [action]   <!-- e.g., "log in with my email and password" -->
**So that** [benefit]    <!-- e.g., "I can access my account" -->

**WHEN** [condition/event]           <!-- e.g., "a valid email and password are submitted" -->
**THE SYSTEM SHALL** [expected behavior]  <!-- e.g., "return JWT tokens and set HttpOnly cookies" -->

**WHEN** [error condition]           <!-- e.g., "invalid credentials are submitted" -->
**THE SYSTEM SHALL** [error handling behavior]  <!-- e.g., "return 401 with generic error message" -->

**Acceptance Criteria:**
<!-- Specific, testable criteria. Each should map to at least one test case. -->
- [ ] Criterion 1  <!-- e.g., "AC-1.1: Valid credentials return 200 with user data" -->
- [ ] Criterion 2  <!-- e.g., "AC-1.2: Invalid password returns 401 Unauthorized" -->
- [ ] Criterion 3  <!-- e.g., "AC-1.3: Account locks after 5 failed attempts" -->

### US-2: {Story Title}
<!-- Repeat format for additional stories -->

## Non-Functional Requirements

### Performance
- Response time: < Xms (p95)
- Throughput: X requests/second
- Concurrent users: X

### Security
- Authentication: Required/Optional
- Authorization: [RBAC/ABAC/Custom]
- Data encryption: At rest / In transit / Both
- Sensitive data: [handling requirements]

### Scalability
- Expected growth: [metrics]
- Scaling strategy: Horizontal/Vertical

## Dependencies

### External Services
- [Service Name]: [purpose]

### Database Changes
- New tables: [list]
- Modified tables: [list]

### API Changes
- New endpoints: [list]
- Modified endpoints: [list]

## Open Questions
1. [Question 1]
2. [Question 2]

---
**Status:** Draft | Approved | Implemented
**Created:** YYYY-MM-DD
**Last Updated:** YYYY-MM-DD
