# BUG INVESTIGATION & FIX WORKFLOW — SENTINELMESH AI

## Objective

Investigate, document, fix, and verify the existing bugs in SentinelMesh AI.

**Do not immediately start modifying code.** First inspect the existing architecture, trace the failing workflows, identify root causes, and document your findings in `BUG.md`.

The goal is to fix the actual underlying issues—not just modify the UI to make it appear that the bugs are fixed.

---

## Phase 1 — Pre-Fix Code Inspection (MANDATORY)

Before changing any code:

1. Inspect the frontend incident dashboard and related components.
2. Inspect API service functions and state-management logic.
3. Inspect the backend incident routes.
4. Inspect IncidentService, PatchService, and VerificationService.
5. Inspect database repositories and incident persistence.
6. Inspect authentication dependencies for relevant endpoints.
7. Inspect frontend/backend status enums and lifecycle transitions.
8. Inspect existing tests.
9. Trace every problematic workflow from the UI to the database and back.

Do not assume the frontend or backend is responsible. Determine the actual root cause using the existing code.

### Investigate the following bugs

#### BUG-001: Incident simulation does not properly create/update dashboard incidents

Current behavior:
- Clicking Simulate Incident produces console output.
- The incident is not properly displayed or updated in the dashboard.
- Incident metrics may not refresh.

Investigate:
- Is the API actually being called?
- Is an incident created in the backend?
- Is the incident persisted?
- Is the API response correctly returned?
- Is the frontend using the response?
- Are frontend state updates missing?
- Is the dashboard reading stale mock data?
- Is the API response structure inconsistent with the frontend expectations?

Expected behavior:
- Simulation creates a real incident through the backend.
- The incident is persisted.
- The frontend receives the created incident.
- The incident immediately appears in the dashboard.
- Dashboard metrics update correctly.
- Duplicate incidents are not accidentally created by repeated requests.

---

#### BUG-002: Incident analysis does not transition to Pending Approval

Current behavior:
- Analysis is triggered.
- Analysis/patch generation may finish.
- The incident does not reliably move to Pending Approval.

Investigate:
- Analysis endpoint behavior.
- Investigator and Repair service execution.
- Patch creation and persistence.
- Incident status transitions.
- Response models.
- Frontend status mapping.
- Async request handling.
- Whether patch creation succeeds but incident status is not updated.

Expected behavior:

1. Analysis starts.
2. Investigation completes.
3. Candidate patch is generated.
4. Patch is persisted and linked to the incident.
5. The incident transitions to `PENDING_APPROVAL`.
6. The dashboard displays the correct state.
7. Approval controls become available only when a valid candidate exists.

The incident must not transition to Pending Approval if patch generation or persistence fails.

---

#### BUG-003: Approve Candidate does not properly advance the workflow

Current behavior:
- Clicking Approve Candidate may display an approval indication.
- The backend workflow does not reliably advance.

Investigate:
- Approve button event handler.
- API request.
- Authentication token.
- Incident ID and patch ID.
- Backend approval endpoint.
- Database persistence.
- Patch status.
- Incident status.
- Frontend optimistic updates.
- Error handling.

Expected behavior:

1. User approves a valid patch.
2. The frontend sends the approval request.
3. The backend validates the incident and patch.
4. The approval is persisted.
5. The patch status is updated.
6. The incident status is updated consistently.
7. The verification action becomes available.
8. The frontend reflects the actual backend response.

Do not show approval success if the backend request fails.

---

#### BUG-004: Run Verifier does not properly execute or complete verification

Current behavior:
- Run Verifier does not reliably execute or complete.
- Verification status may be stale or incorrect.

Investigate:
- Verifier button handler.
- API request.
- Incident and patch IDs.
- Verification service.
- Docker execution.
- Test execution.
- Timeout handling.
- Verification response.
- Frontend loading state.
- Status refresh.

Expected behavior:

1. Verification is allowed only after approval.
2. The backend starts a verification run.
3. The UI displays a running state.
4. The verifier executes the actual tests in the intended sandbox.
5. The backend records the result.
6. The frontend displays the result.
7. The incident is marked recovered only if genuine verification succeeds.

**Docker fail-closed rule:**

- Docker unavailable = verification failure.
- Docker execution error = verification failure.
- Timeout = verification failure.
- No fabricated passing results.
- No host execution of untrusted patches.
- No incident marked recovered without genuine successful verification.

---

#### BUG-005: Dashboard state and metrics are stale

Current behavior:
- Incident status does not update immediately.
- Metrics may display outdated values.
- UI components may disagree about the current incident state.

Investigate:
- Multiple sources of truth.
- Mock data fallback.
- React state.
- API cache.
- Query invalidation.
- Polling.
- Async requests.
- Race conditions.
- Incorrect response mapping.

Expected behavior:
- Backend is the source of truth for persisted incident states.
- Mutations update or invalidate relevant dashboard data.
- Incident details refresh after every lifecycle action.
- Dashboard metrics are derived from current data.
- Old requests cannot overwrite newer state.
- No conflicting mock/live data sources.

---

## Phase 2 — Create BUG.md Before Fixing

After inspecting the code, create or update `BUG.md` in the repository root.

For every bug, document:

- Bug ID
- Bug title
- Severity
- Current behavior
- Expected behavior
- Files and functions involved
- Root cause
- Evidence supporting the root cause
- Proposed fix
- Tests required
- Status

Use the following statuses:

- `INVESTIGATING`
- `CONFIRMED`
- `FIX IN PROGRESS`
- `FIXED`
- `VERIFIED`
- `BLOCKED`

Do not guess root causes. Root causes must be based on code inspection or reproducible test results.

Do not mark a bug FIXED or VERIFIED at this stage.

---

## Phase 3 — Pre-Fix Baseline

Before implementing fixes:

1. Run the existing backend tests.
2. Run the frontend build.
3. Reproduce the reported bugs where possible.
4. Record existing failures.
5. Record test results.
6. Record any environment limitations.

Document the baseline in `BUG.md`.

Do not confuse pre-existing failures with failures introduced by your changes.

---

## Phase 4 — Fix Planning

Before writing implementation code, add a fix plan to `BUG.md`.

For each bug include:

- Root cause
- Planned code changes
- Backend changes
- Frontend changes
- Database changes, if needed
- Regression tests
- Risks
- Dependencies on other fixes

Ensure the incident lifecycle follows a valid state machine.

Expected lifecycle:

SIMULATED / DETECTED
        ↓
INVESTIGATING
        ↓
PENDING_APPROVAL
        ↓
APPROVED
        ↓
VERIFYING
        ↓
RECOVERED  — only if verification genuinely passes

If verification fails:

        ↓
VERIFICATION_FAILED

Ensure the lifecycle is consistent across:

- Backend
- Database
- API responses
- Frontend
- Audit trail

Do not introduce UI-only status transitions.

---

## Phase 5 — Implement the Fixes

After the code inspection, baseline tests, and fix plan are documented, implement the fixes.

Rules:

- Fix root causes.
- Preserve existing architecture where possible.
- Avoid unnecessary refactoring.
- Do not remove authentication.
- Do not weaken authorization.
- Do not introduce mock success responses.
- Do not fabricate verifier results.
- Do not bypass Docker fail-closed protections.
- Do not silently fall back to fake production data.
- Do not make the UI report success before the backend confirms success.
- Handle errors properly.
- Prevent duplicate actions.
- Prevent race conditions.
- Maintain consistent backend/database/frontend status values.

---

## Phase 6 — Regression Testing

Add or update tests for:

### Incident Simulation
- Incident is created.
- Incident is persisted.
- API returns the correct incident.
- Dashboard updates.
- Metrics update.
- Duplicate submission behavior is handled.

### Analysis
- Analysis is triggered.
- Patch is generated.
- Patch is persisted.
- Patch is linked to the incident.
- Incident transitions to Pending Approval.
- Failed patch generation does not transition the incident.

### Approval
- Approval request reaches backend.
- Approval is persisted.
- Incident and patch states are consistent.
- Invalid approval is rejected.
- Failed API request does not display false success.

### Verification
- Verifier can only run after approval.
- Verification enters a running state.
- Successful genuine verification produces the correct result.
- Failed tests produce failure.
- Docker unavailable produces failure.
- Timeout produces failure.
- Fake verification results cannot mark an incident recovered.

### Dashboard
- State refreshes after every mutation.
- Metrics reflect backend data.
- Stale requests do not overwrite newer data.
- UI and backend statuses remain consistent.

---

## Phase 7 — Post-Fix Code Inspection

After implementation, do not immediately declare success.

Re-inspect the modified code.

Verify:

- The original root cause was actually addressed.
- No disconnected code was added.
- No API endpoint is bypassed.
- The frontend uses real backend responses.
- Status transitions are valid.
- Database persistence is correct.
- Authentication is preserved.
- Docker fail-closed behavior remains intact.
- No fake success paths were introduced.
- No existing functionality was unintentionally broken.

Review every changed file.

---

## Phase 8 — Final Verification

Run:

1. Full backend test suite.
2. Frontend production build.
3. Relevant integration tests.
4. Incident lifecycle tests.
5. Docker sandbox tests.
6. Static checks, if available.

Perform a complete lifecycle test wherever the environment allows:

Simulate Incident
→ Incident Appears
→ Analyze
→ Patch Generated
→ Pending Approval
→ Approve Candidate
→ Verification Running
→ Genuine Test Execution
→ Verified Result
→ Final Incident Status

If an end-to-end test cannot be executed, clearly state why.

Never claim that a live Docker execution occurred if only mocked tests were run.

---

## Phase 9 — Final Bug Report

Update `BUG.md` after completing all work.

The final report must contain:

### 1. Executive Summary
What was broken and what was fixed.

### 2. Root Cause Analysis
Actual root cause for every bug.

### 3. Files Changed
List each modified file and explain why it was changed.

### 4. Fixes Implemented
Describe the actual implementation changes.

### 5. Test Results
Include:

- Backend tests passed
- Backend tests failed
- Frontend build status
- Integration tests
- Docker verification tests
- Live verification performed or not performed

### 6. Before vs After

| Workflow | Before | After |
|---|---|---|
| Incident simulation | | |
| Incident dashboard | | |
| Analysis | | |
| Patch generation | | |
| Pending approval | | |
| Candidate approval | | |
| Verification | | |
| Final incident state | | |

### 7. Verification Evidence

Provide evidence for each bug fix.

Evidence should include:
- Test name
- Test result
- Relevant API response
- Status transition
- Relevant logs, where available

### 8. Remaining Issues

List anything that is:
- Not fixed
- Not tested
- Blocked by environment
- Requires manual verification
- Potentially risky

### 9. Final Status

Assign each bug one of:

- VERIFIED
- FIXED — NOT FULLY VERIFIED
- PARTIALLY FIXED
- BLOCKED
- OPEN

Do not label a bug VERIFIED merely because the code was changed.

---

## Final Deliverables

Produce:

1. Updated `BUG.md` in the repository root.
2. Actual code fixes.
3. Regression tests.
4. Pre-fix baseline results.
5. Post-fix test results.
6. Final summary of the investigation and implementation.

---

## Final Instruction

**Investigate first. Document the evidence. Plan the fix. Implement. Test. Re-inspect. Verify. Report.**

Do not skip phases.

Do not make cosmetic UI changes and claim the bugs are fixed.

Do not declare completion until the final report is updated and the test results are honestly recorded.
