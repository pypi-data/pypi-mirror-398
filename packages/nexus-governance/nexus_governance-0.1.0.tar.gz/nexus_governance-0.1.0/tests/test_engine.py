from nexus.core.engine import NexusEngine
from nexus.schemas import Verdict


def test_read_is_allowed():
    eng = NexusEngine()
    v, info = eng.evaluate(
        tool_name="t",
        tool_version="1",
        args={"a": 1},
        principal_id="u",
        principal_role="viewer",
        principal_scopes=None,
        tenant_id="t1",
        danger="read",
    )
    assert v == Verdict.ALLOW
    assert info is None


def test_viewer_cannot_write_or_critical():
    eng = NexusEngine(require_scopes=False)
    v, info = eng.evaluate(
        tool_name="t",
        tool_version="1",
        args={"a": 1},
        principal_id="u",
        principal_role="viewer",
        principal_scopes=[],
        tenant_id="t1",
        danger="write",
    )
    assert v == Verdict.DENY
    assert "Viewers" in info["error"]


def test_scopes_required_when_configured():
    eng = NexusEngine(require_scopes=True)
    v, info = eng.evaluate(
        tool_name="refund_user",
        tool_version="1",
        args={"a": 1},
        principal_id="u",
        principal_role="admin",
        principal_scopes=[],
        tenant_id="t1",
        danger="critical",
    )
    assert v == Verdict.DENY
    assert "Missing required scopes" in info["error"]


def test_critical_creates_pending_and_is_stable_for_sets():
    eng = NexusEngine(require_scopes=False)

    args1 = {"ids": {"b", "a"}, "token": "SECRET1"}
    v1, info1 = eng.evaluate(
        tool_name="tool",
        tool_version="1",
        args=args1,
        principal_id="u",
        principal_role="admin",
        principal_scopes=[],
        tenant_id="t1",
        danger="critical",
    )
    assert v1 == Verdict.REQUIRE_APPROVAL
    req1 = info1["nexus"]["request_id"]

    # Different insertion order + different secret value should still collide to same approval.
    args2 = {"token": "SECRET2", "ids": set(["a", "b"])}
    v2, info2 = eng.evaluate(
        tool_name="tool",
        tool_version="1",
        args=args2,
        principal_id="u",
        principal_role="admin",
        principal_scopes=[],
        tenant_id="t1",
        danger="critical",
    )
    assert v2 == Verdict.REQUIRE_APPROVAL
    req2 = info2["nexus"]["request_id"]
    assert req2 == req1


def test_tuple_order_changes_fingerprint():
    eng = NexusEngine(require_scopes=False)

    v1, info1 = eng.evaluate(
        tool_name="tool",
        tool_version="1",
        args={"t": (1, 2)},
        principal_id="u",
        principal_role="admin",
        principal_scopes=[],
        tenant_id="t1",
        danger="critical",
    )
    assert v1 == Verdict.REQUIRE_APPROVAL

    v2, info2 = eng.evaluate(
        tool_name="tool",
        tool_version="1",
        args={"t": (2, 1)},
        principal_id="u",
        principal_role="admin",
        principal_scopes=[],
        tenant_id="t1",
        danger="critical",
    )
    assert v2 == Verdict.REQUIRE_APPROVAL

    assert info1["nexus"]["request_id"] != info2["nexus"]["request_id"]


def test_execution_claim_and_mark_executed():
    eng = NexusEngine(require_scopes=False)

    # Create pending
    v, info = eng.evaluate(
        tool_name="tool",
        tool_version="1",
        args={"x": 1},
        principal_id="u",
        principal_role="admin",
        principal_scopes=[],
        tenant_id="t1",
        danger="critical",
    )
    req_id = info["nexus"]["request_id"]

    # Approve
    ok, _ = eng.approve_request(req_id, operator="op")
    assert ok

    # Evaluate should claim EXECUTING and allow
    v2, info2 = eng.evaluate(
        tool_name="tool",
        tool_version="1",
        args={"x": 1},
        principal_id="u",
        principal_role="admin",
        principal_scopes=[],
        tenant_id="t1",
        danger="critical",
    )
    assert v2 == Verdict.ALLOW
    assert info2["request_id"] == req_id

    # Mark executed
    ok2, _ = eng.mark_executed(req_id)
    assert ok2

    # Further evaluations should create a new pending (EXECUTED not in active set)
    v3, info3 = eng.evaluate(
        tool_name="tool",
        tool_version="1",
        args={"x": 1},
        principal_id="u",
        principal_role="admin",
        principal_scopes=[],
        tenant_id="t1",
        danger="critical",
    )
    assert v3 == Verdict.REQUIRE_APPROVAL
    assert info3["nexus"]["request_id"] != req_id
