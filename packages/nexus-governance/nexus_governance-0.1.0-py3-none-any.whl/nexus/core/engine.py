from __future__ import annotations

import hashlib
import hmac
import json
import re
import sqlite3
import threading
import time
import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from nexus.schemas import Verdict


class NexusEngine:
    def __init__(
        self,
        db_path: str = ":memory:",
        secret_key: str = "change_me_in_prod",
        redact_keys: Optional[Set[str]] = None,
        redact_patterns: Optional[List[str]] = None,
        require_scopes: bool = True,
    ):
        self._lock = threading.Lock()
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.secret_key = secret_key.encode()
        self.require_scopes = require_scopes

        if db_path != ":memory:":
            self.conn.execute("PRAGMA journal_mode=WAL;")
            self.conn.execute("PRAGMA synchronous=NORMAL;")
            self.conn.execute("PRAGMA busy_timeout=5000;")

        default_keys = {
            "password",
            "token",
            "secret",
            "key",
            "auth",
            "credential",
            "email",
            "ssn",
        }
        self.redact_keys = {k.lower() for k in (redact_keys or default_keys)}
        self.redact_patterns = [re.compile(p) for p in (redact_patterns or [])]

        self._init_db()

    def _init_db(self) -> None:
        with self._lock:
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS governance_requests (
                    request_id TEXT PRIMARY KEY,
                    principal_id TEXT NOT NULL,
                    tenant_id TEXT,
                    tool_name TEXT NOT NULL,
                    tool_version TEXT NOT NULL,
                    danger TEXT NOT NULL,
                    fingerprint TEXT NOT NULL,
                    args_redacted TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('PENDING', 'APPROVED', 'DENIED', 'EXECUTING', 'EXECUTED', 'EXPIRED')),
                    created_at INTEGER NOT NULL,
                    expires_at INTEGER NOT NULL,
                    processed_by TEXT,
                    processed_at INTEGER,
                    denied_reason TEXT
                );
                """
            )
            self.conn.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS uq_active_fingerprint
                ON governance_requests(fingerprint)
                WHERE status IN ('PENDING', 'APPROVED', 'EXECUTING', 'DENIED');
                """
            )
            self.conn.commit()

    def _smart_serializer(self, obj: Any) -> Any:
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, tuple):
            return list(obj)
        if isinstance(obj, set):
            return sorted(list(obj), key=str)
        if isinstance(obj, (bytes, bytearray)):
            digest = hashlib.sha256(bytes(obj)).hexdigest()
            return f"<BYTES_SHA256:{digest}>"
        return str(obj)

    def _json_dump(self, data: Any) -> str:
        return json.dumps(
            data, sort_keys=True, separators=(",", ":"), default=self._smart_serializer
        )

    def _scrub(self, obj: Any) -> Any:
        if isinstance(obj, str):
            for pattern in self.redact_patterns:
                if pattern.search(obj):
                    return "[REDACTED_PATTERN]"
            return obj
        if isinstance(obj, dict):
            return {
                k: ("[REDACTED]" if k.lower() in self.redact_keys else self._scrub(v))
                for k, v in obj.items()
            }
        if isinstance(obj, list):
            return [self._scrub(i) for i in obj]
        if isinstance(obj, tuple):
            return tuple(self._scrub(i) for i in obj)
        if isinstance(obj, set):
            return {self._scrub(i) for i in obj}
        return obj

    def _compute_hmac(
        self,
        tool_name: str,
        tool_version: str,
        canonical_scrubbed_args: str,
        principal: str,
        tenant: str,
        danger: str,
    ) -> str:
        payload = f"{tool_name}|{tool_version}|{danger}|{canonical_scrubbed_args}|{principal}|{str(tenant)}"
        return hmac.new(self.secret_key, payload.encode(), hashlib.sha256).hexdigest()

    def _check_scope_policy(
        self, scopes: List[str], tool_name: str, danger: str
    ) -> Tuple[bool, Optional[str]]:
        if not scopes:
            if self.require_scopes:
                return False, f"Policy: Missing required scopes for {danger} action."
            return True, None

        if danger == "critical":
            required = {f"critical:{tool_name}", "critical:*"}
        else:
            required = {f"write:{tool_name}", "write:*"}

        if not any(s in required for s in scopes):
            return False, "Policy: Missing required scope for tool."

        return True, None

    def evaluate(
        self,
        tool_name: str,
        tool_version: str,
        args: Dict[str, Any],
        principal_id: str,
        principal_role: str,
        principal_scopes: Optional[List[str]],
        tenant_id: str,
        danger: str,
    ) -> Tuple[Verdict, Optional[Dict[str, Any]]]:
        principal_scopes = principal_scopes or []

        if danger == "read":
            return Verdict.ALLOW, None

        if principal_role == "viewer":
            return Verdict.DENY, {
                "error": "Policy: Viewers cannot perform write actions."
            }

        is_allowed, reason = self._check_scope_policy(
            principal_scopes, tool_name, danger
        )
        if not is_allowed:
            return Verdict.DENY, {"error": reason}

        scrubbed_args = self._scrub(args)
        canonical_scrubbed_str = self._json_dump(scrubbed_args)

        fingerprint = self._compute_hmac(
            tool_name,
            tool_version,
            canonical_scrubbed_str,
            principal_id,
            tenant_id,
            danger,
        )
        now_epoch = int(time.time())

        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT request_id, status, expires_at, denied_reason
                FROM governance_requests
                WHERE fingerprint = ?
                  AND status IN ('PENDING', 'APPROVED', 'EXECUTING', 'DENIED')
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (fingerprint,),
            )
            row = cursor.fetchone()

            expired_update_pending = False
            if row and now_epoch > row["expires_at"]:
                self.conn.execute(
                    "UPDATE governance_requests SET status='EXPIRED' WHERE request_id=?",
                    (row["request_id"],),
                )
                expired_update_pending = True
                row = None

            if not row:
                if danger == "critical":
                    return self._create_pending(
                        tool_name,
                        tool_version,
                        danger,
                        fingerprint,
                        canonical_scrubbed_str,
                        principal_id,
                        tenant_id,
                        now_epoch,
                    )

                if expired_update_pending:
                    self.conn.commit()
                return Verdict.ALLOW, None

            status = row["status"]
            req_id = row["request_id"]

            if status == "PENDING":
                return Verdict.REQUIRE_APPROVAL, self._build_envelope(req_id, "PENDING")

            if status == "EXECUTING":
                return Verdict.THROTTLE, {
                    "error": "Request is currently executing. Please wait.",
                    "retry_after": 5,
                    "request_id": req_id,
                    "status": status,
                }

            if status == "DENIED":
                reason = row["denied_reason"] or "Denied by operator"
                return Verdict.DENY, {"error": f"Request was denied: {reason}"}

            if status == "APPROVED":
                cursor.execute(
                    "UPDATE governance_requests SET status='EXECUTING' WHERE request_id=? AND status='APPROVED'",
                    (req_id,),
                )
                self.conn.commit()
                if cursor.rowcount == 1:
                    return Verdict.ALLOW, {"request_id": req_id}
                return Verdict.THROTTLE, {
                    "error": "Race condition: Claimed by another thread."
                }

            return Verdict.DENY, {"error": f"Unexpected state: {status}"}

    def _create_pending(
        self,
        tool: str,
        version: str,
        danger: str,
        fingerprint: str,
        args_redacted_str: str,
        principal: str,
        tenant: str,
        now_epoch: int,
    ) -> Tuple[Verdict, Optional[Dict[str, Any]]]:
        req_id = f"req_{uuid.uuid4().hex[:8]}"
        expires = now_epoch + (24 * 3600)

        self.conn.execute("SAVEPOINT sp_create_pending")
        try:
            self.conn.execute(
                """
                INSERT INTO governance_requests
                (request_id, principal_id, tenant_id, tool_name, tool_version, danger, fingerprint, args_redacted, status, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', ?, ?)
                """,
                (
                    req_id,
                    principal,
                    tenant,
                    tool,
                    version,
                    danger,
                    fingerprint,
                    args_redacted_str,
                    now_epoch,
                    expires,
                ),
            )
            self.conn.execute("RELEASE SAVEPOINT sp_create_pending")
            self.conn.commit()
            return Verdict.REQUIRE_APPROVAL, self._build_envelope(req_id, "PENDING")

        except sqlite3.IntegrityError:
            self.conn.execute("ROLLBACK TO SAVEPOINT sp_create_pending")
            self.conn.execute("RELEASE SAVEPOINT sp_create_pending")
            self.conn.commit()

            row = self.conn.execute(
                """
                SELECT request_id, status, denied_reason, expires_at
                FROM governance_requests
                WHERE fingerprint = ?
                  AND status IN ('PENDING', 'APPROVED', 'EXECUTING', 'DENIED')
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (fingerprint,),
            ).fetchone()

            if row and now_epoch <= row["expires_at"]:
                if row["status"] == "PENDING":
                    return Verdict.REQUIRE_APPROVAL, self._build_envelope(
                        row["request_id"], "PENDING"
                    )
                if row["status"] == "DENIED":
                    reason = row["denied_reason"] or "Denied by operator"
                    return Verdict.DENY, {"error": f"Request was denied: {reason}"}
                return Verdict.THROTTLE, {
                    "error": "Request already active in another worker.",
                    "request_id": row["request_id"],
                    "status": row["status"],
                    "retry_after": 5,
                }

            return Verdict.THROTTLE, {"error": "Request contention. Please retry."}

        except Exception:
            self.conn.execute("ROLLBACK TO SAVEPOINT sp_create_pending")
            self.conn.execute("RELEASE SAVEPOINT sp_create_pending")
            self.conn.rollback()
            raise

    def _build_envelope(self, req_id: str, status: str) -> Dict[str, Any]:
        return {
            "nexus": {
                "type": "approval_required",
                "request_id": req_id,
                "status": status,
                "instruction": "retry_same_call",
            },
            "message": f"Approval required. Request ID: {req_id}",
        }

    def approve_request(self, req_id: str, operator: str) -> Tuple[bool, str]:
        with self._lock:
            now_epoch = int(time.time())
            cur = self.conn.execute(
                """
                UPDATE governance_requests
                SET status='APPROVED', processed_by=?, processed_at=?
                WHERE request_id=? AND status='PENDING' AND expires_at > ?
                """,
                (operator, now_epoch, req_id, now_epoch),
            )
            self.conn.commit()
            ok = cur.rowcount > 0
            return ok, ("Approved" if ok else "Failed")

    def deny_request(
        self, req_id: str, operator: str, reason: str = "Denied by operator"
    ) -> Tuple[bool, str]:
        with self._lock:
            now_epoch = int(time.time())
            cur = self.conn.execute(
                """
                UPDATE governance_requests
                SET status='DENIED', processed_by=?, processed_at=?, denied_reason=?
                WHERE request_id=? AND status IN ('PENDING', 'APPROVED') AND expires_at > ?
                """,
                (operator, now_epoch, reason, req_id, now_epoch),
            )
            self.conn.commit()
            ok = cur.rowcount > 0
            return ok, ("Denied" if ok else "Failed")

    def mark_executed(self, req_id: str) -> Tuple[bool, str]:
        with self._lock:
            now_epoch = int(time.time())
            cur = self.conn.execute(
                """
                UPDATE governance_requests
                SET status='EXECUTED', processed_at=?
                WHERE request_id=? AND status='EXECUTING'
                """,
                (now_epoch, req_id),
            )
            self.conn.commit()
            ok = cur.rowcount > 0
            return ok, ("Marked" if ok else "Failed")
