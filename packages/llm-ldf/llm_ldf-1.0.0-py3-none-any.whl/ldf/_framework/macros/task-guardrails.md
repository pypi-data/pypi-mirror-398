# Task-Guardrails Macro

## Purpose
Verify all applicable guardrails are addressed before implementing each task.

## When to Use
- Before starting implementation of any task
- During code review

## Process

### Step 1: Load Task Context

For the task being implemented:
1. Read task description from `tasks.md`
2. Identify what the task involves:
   - Database changes?
   - API endpoints?
   - Business logic?
   - Frontend components?

### Step 2: Load Active Guardrails

From `.ldf/guardrails.yaml`:
1. Core guardrails (8)
2. Preset guardrails (if applicable)
3. Custom guardrails

### Step 3: Determine Applicable Guardrails

Based on task scope, determine which guardrails apply:

| Task Type | Applicable Guardrails |
|-----------|----------------------|
| Database schema | Migrations, Data Validation |
| API endpoint | API Design, Security, Error Handling, Logging |
| Business logic | Testing, Error Handling, Logging |
| Auth changes | Security, Testing (critical path) |
| All tasks | Documentation |

### Step 4: Present Checklist

Display the checklist for the task:

```markdown
## Guardrail Checklist for Task 2.1

Before implementing, verify:

- [ ] **1. Testing Coverage:** Unit tests for business logic; coverage ≥80%
- [ ] **2. Security Basics:** Input validation; auth checks where needed
- [ ] **3. Error Handling:** Proper error responses; exception handling
- [ ] **4. Logging:** Structured logs; correlation IDs
- [x] **5. API Design:** N/A - No API changes in this task
- [ ] **6. Data Validation:** Schema validation for inputs
- [x] **7. Migrations:** N/A - No schema changes
- [ ] **8. Documentation:** Update inline comments for complex logic
```

### Step 5: Verify Each Guardrail

For each applicable guardrail, confirm:
1. How will this guardrail be addressed?
2. What specific implementation is needed?
3. What tests will verify this?

**Example verification:**
```
Guardrail #2 (Security Basics):
  ✅ Input validation: Using Pydantic model for request body
  ✅ Auth check: @require_auth decorator on endpoint
  ✅ SQL injection: Using parameterized queries via SQLAlchemy
  ⚠️ Rate limiting: TODO - add after core implementation
```

### Step 6: Block or Proceed

**Proceed if:**
- All applicable guardrails have plan or N/A justification
- No critical guardrails unaddressed

**Block if:**
- Any critical guardrail applicable but not addressed
- N/A claimed without valid justification

### Blocking Output

```
🚫 BLOCKED: Guardrails Not Addressed

Task 2.1: Implement user registration

Unaddressed guardrails:
  - #2 Security Basics (Critical): No input validation plan
  - #1 Testing Coverage (Critical): No test plan specified

Please address these before starting implementation.
```

### Success Output

```
✅ Guardrails Verified for Task 2.1

Applicable guardrails: 6/8
Addressed: 6/6
N/A (justified): 2/8

Guardrail plan:
  #1 Testing: Unit tests for UserService, >80% coverage
  #2 Security: Pydantic validation, @require_auth, parameterized SQL
  #3 Errors: UserNotFoundError, ValidationError classes
  #4 Logging: Structured logs with user_id, correlation_id
  #6 Validation: Pydantic EmailStr, password strength validator
  #8 Docs: Update docstrings for new methods

You may proceed with implementation.
```

## Per-Task Checklist Template

Include at the start of each task in `tasks.md`:

```markdown
## Per-Task Guardrail Checklist

- [ ] **1. Testing Coverage:** [How will this be tested?]
- [ ] **2. Security Basics:** [What security measures?]
- [ ] **3. Error Handling:** [What errors and how handled?]
- [ ] **4. Logging:** [What to log?]
- [ ] **5. API Design:** [API patterns followed?]
- [ ] **6. Data Validation:** [How validated?]
- [ ] **7. Migrations:** [Schema changes safe?]
- [ ] **8. Documentation:** [What to document?]

Mark N/A with justification if not applicable.
```

## Integration with Implementation

When implementing a task:
1. Run this macro first
2. Address each guardrail as you code
3. Check off items as completed
4. Run `ldf lint` to verify

## Notes

- Don't skip this for "small" tasks - small tasks add up
- The checklist should be reviewed, not just checked off
- If a guardrail is frequently N/A, consider if it's configured correctly
- Use this macro in code reviews to verify compliance
