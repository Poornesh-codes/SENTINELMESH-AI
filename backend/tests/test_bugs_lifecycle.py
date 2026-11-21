"""
Tests for Bug Fixes BUG-001 through BUG-005 in SentinelMesh AI.
Validates the complete incident lifecycle state machine:
DETECTED/SIMULATED -> INVESTIGATING -> AWAITING_APPROVAL -> APPROVED -> VERIFYING -> RECOVERED / FAILED.
"""
import pytest
from app.schemas.incident import IncidentCreate
from app.services import incident_service, patch_service, verification_service
from app.repositories import incident_repo, patch_repo


def test_bug_001_incident_simulation_creation():
    """BUG-001: Incident creation must normalize payload and initialize in detected/investigating."""
    inc_id = "INC-BUG001-TEST"
    payload = IncidentCreate(
        id=inc_id,
        title="Chaos NullPointerException simulation in payment service",
        app="payment-gateway-svc",
        application="payment-gateway-svc",
        version="v2.14",
        description="Chaos fault injected into guest checkout pipeline",
        severity="critical",
        status="investigating",
        rawLogs="NullPointerException in StripeWebhookHandler.java:142",
        pipelineAgent="Investigator Agent (parsing traces)",
        blastRadius="Isolated",
        blastRadiusDetail="Guest invoice webhook pipeline only.",
    )

    created = incident_service.create_incident(payload)
    assert created.id == inc_id
    assert created.application == "payment-gateway-svc"
    assert created.app == "payment-gateway-svc"
    assert created.severity == "critical"
    assert created.status in ["investigating", "detected"]

    # Verify repository storage
    stored = incident_repo.get_by_id(inc_id)
    assert stored is not None
    assert stored["title"] == payload.title
    assert stored["status"] in ["investigating", "detected"]


def test_bug_002_incident_analysis_transitions_to_awaiting_approval():
    """BUG-002: Incident analysis must transition status to awaiting_approval and synthesize patch."""
    inc_id = "INC-BUG002-TEST"
    payload = IncidentCreate(
        id=inc_id,
        title="Redis Socket Leak Simulation",
        application="auth-session-worker",
        severity="high",
        status="investigating",
    )
    incident_service.create_incident(payload)

    # Trigger analysis
    analysis_resp = incident_service.analyze_incident(inc_id)
    assert analysis_resp.status == "awaiting_approval"
    assert "Defensive patch generated" in analysis_resp.message

    # Verify repository state
    stored = incident_repo.get_by_id(inc_id)
    assert stored["status"] == "awaiting_approval"
    assert stored.get("proposed_patch") is not None
    assert stored["proposed_patch"].get("id") is not None

    # Verify patch repository
    patches = patch_repo.list_by_incident(inc_id)
    assert len(patches) >= 1
    assert patches[0]["status"] == "pending"


def test_bug_003_approve_candidate_sets_approved_not_recovered():
    """BUG-003: Approving candidate patch must transition to approved, NEVER recovered."""
    inc_id = "INC-BUG003-TEST"
    payload = IncidentCreate(
        id=inc_id,
        title="PostgreSQL Row Lock Inversion",
        application="inventory-sync-db",
        severity="high",
        status="investigating",
    )
    incident_service.create_incident(payload)
    incident_service.analyze_incident(inc_id)

    # Approve patch
    decision_resp = patch_service.process_patch_decision(
        incident_id=inc_id,
        decision="approve",
        notes="Reviewed and approved by Lead SRE.",
        actor="Elena Vance (Lead SRE)",
    )
    assert decision_resp.status == "approved"

    # Invariant: Status must be 'approved', NOT 'recovered'
    stored = incident_repo.get_by_id(inc_id)
    assert stored["status"] == "approved"
    assert stored["status"] != "recovered"


def test_bug_004_verification_fail_closed_sets_failed():
    """BUG-004: When verification fails (or Docker unavailable), status must fail closed to 'failed'."""
    inc_id = "INC-BUG004-TEST"
    payload = IncidentCreate(
        id=inc_id,
        title="OOMKill Heap Spike Simulation",
        application="order-fulfillment-api",
        severity="medium",
        status="investigating",
    )
    incident_service.create_incident(payload)
    incident_service.analyze_incident(inc_id)
    patch_service.process_patch_decision(
        incident_id=inc_id,
        decision="approve",
        notes="Approved for sandbox verification.",
        actor="Elena Vance",
    )

    # Run verification
    run_resp = verification_service.run_verification(incident_id=inc_id)
    # Since Docker Desktop daemon is not running on test host, verification fails closed
    assert run_resp.status in ["failed", "docker_unavailable"]

    stored = incident_repo.get_by_id(inc_id)
    assert stored["status"] in ["failed", "verification_failed"]
    assert stored["status"] != "recovered"


def test_bug_005_lifecycle_state_machine_consistency():
    """BUG-005: Validate end-to-end state transitions across the full lifecycle."""
    inc_id = "INC-BUG005-TEST"
    # 1. Detected / Simulated
    created = incident_service.create_incident(IncidentCreate(
        id=inc_id,
        title="Multi-SKU Deadlock",
        application="warehouse-service",
        severity="high",
        status="detected",
    ))
    assert created.status in ["detected", "investigating"]

    # 2. Investigating -> Awaiting Approval
    analyzed = incident_service.analyze_incident(inc_id)
    assert analyzed.status == "awaiting_approval"

    # 3. Awaiting Approval -> Approved
    approved = patch_service.process_patch_decision(
        incident_id=inc_id,
        decision="approve",
        notes="SRE signed off.",
        actor="Operator",
    )
    assert approved.status == "approved"
    assert incident_repo.get_by_id(inc_id)["status"] == "approved"

    # 4. Approved -> Verifying / Failed (Fail-closed)
    run = verification_service.run_verification(incident_id=inc_id)
    final_inc = incident_repo.get_by_id(inc_id)
    if run.status == "passed":
        assert final_inc["status"] == "recovered"
    else:
        assert final_inc["status"] in ["failed", "verification_failed"]
