# {Feature Name} - Implementation Tasks

## Per-Task Guardrail Checklist
**Reference:** `.ldf/guardrails.yaml` | **Macro:** `.ldf/macros/task-guardrails.md`

Before implementing each task, verify applicable guardrails:

- [ ] **1. Testing Coverage:** Unit tests for business logic; integration tests for APIs; coverage ≥80%
- [ ] **2. Security Basics:** Input validation; parameterized queries; auth/authz checks; no secrets in code
- [ ] **3. Error Handling:** Consistent error responses; proper exception hierarchy; user-friendly messages
- [ ] **4. Logging & Observability:** Structured logging; correlation IDs; appropriate log levels
- [ ] **5. API Design:** Versioned endpoints (/v1/); cursor pagination; consistent error format
- [ ] **6. Data Validation:** Request schema validation; business rule validation; output sanitization
- [ ] **7. Database Migrations:** Reversible migrations; rollback tested; backfills separate from schema
- [ ] **8. Documentation:** API docs updated; inline comments for complex logic; README current

**Mark N/A if not applicable to the task.**

---

## Task Numbering Convention
- Major phase: X.0
- Tasks: X.1, X.2, X.3...
- Subtasks: X.1.1, X.1.2... (use for complex tasks requiring breakdown)

**Note:** Both 2-level (1.1) and 3-level (1.1.1) task IDs are supported.

## Phase 1: Foundation & Setup

<!-- Example: Completed and in-progress tasks shown for reference -->

- [x] **Task 1.1:** Project setup
  - [x] Create directory structure
  - [x] Install dependencies
  - [x] Configure environment
  - **Dependencies:** None
  - **Tests:** N/A (setup task)
  - **Completed:** 2025-01-10 | **Commit:** `abc1234`

- [x] **Task 1.2:** Database schema
  - [x] Create migration file
  - [x] Define models
  - [x] Add indexes
  - [x] Write migration tests
  - **Dependencies:** Task 1.1
  - **Tests:** Migration up/down tests (✅ passing)
  - **Completed:** 2025-01-11 | **Commit:** `def5678`

## Phase 2: Core Business Logic

<!-- Example: In-progress task with some subtasks completed -->

- [ ] **Task 2.1:** Implement {ServiceName}
  - [x] Create service class
  - [x] Implement core methods
  - [ ] Add error handling           <!-- ⬅️ Currently working on this -->
  - [ ] Write unit tests
  - **Dependencies:** Task 1.2
  - **Tests:** Unit tests with mocked dependencies (≥80% coverage)
  - **Status:** IN PROGRESS

- [ ] **Task 2.2:** Implement {HelperService}
  - [ ] Create helper class
  - [ ] Implement utility methods
  - [ ] Write unit tests
  - **Dependencies:** Task 2.1
  - **Tests:** Unit tests

## Phase 3: API Layer
- [ ] **Task 3.1:** Create API endpoints
  - [ ] Define routes
  - [ ] Add request/response schemas
  - [ ] Wire up to services
  - [ ] Add authentication
  - **Dependencies:** Task 2.1, Task 2.2
  - **Tests:** API integration tests

- [ ] **Task 3.2:** Add validation and error handling
  - [ ] Request validation
  - [ ] Error responses
  - [ ] Rate limiting (if applicable)
  - **Dependencies:** Task 3.1
  - **Tests:** Error case tests

## Phase 4: Frontend (if applicable)
- [ ] **Task 4.1:** Create UI components
  - [ ] Build form components
  - [ ] Add validation
  - [ ] Apply styling
  - **Dependencies:** Task 3.1
  - **Tests:** Component tests

- [ ] **Task 4.2:** Implement API integration
  - [ ] Create API client functions
  - [ ] Add error handling
  - [ ] Implement loading states
  - **Dependencies:** Task 4.1
  - **Tests:** Integration tests

## Phase 5: Testing & Documentation
- [ ] **Task 5.1:** E2E tests
  - [ ] Write user flow tests
  - [ ] Test happy paths
  - [ ] Test error scenarios
  - **Dependencies:** All previous tasks
  - **Tests:** E2E test suite

- [ ] **Task 5.2:** Documentation
  - [ ] Update API documentation
  - [ ] Add inline code comments
  - [ ] Update README
  - **Dependencies:** All previous tasks
  - **Tests:** Documentation review

## Summary
**Total Tasks:** {N}
**Critical Path:** Tasks {list}

## Notes
- Each task should be completable in <4 hours
- Mark dependencies clearly to prevent blocked work
- Update this file as tasks are completed
- If task takes >4 hours, break into subtasks

---
**Status:** Not Started | In Progress | Complete
**Started:** YYYY-MM-DD
**Completed:** YYYY-MM-DD
