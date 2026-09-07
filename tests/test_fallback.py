"""Fallback contracts against a local HTTP server; no paid endpoints or model calls."""
import contextlib
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/claudex-loop/scripts"))
import codex_usage
import fallback_review as fallback
from runner import RunError, check_approval

GOOD = {"verdict": "APPROVED", "summary": "The plan is consistent.", "findings": [],
        "coverage": ["Supplied plan"], "limitations": []}


class FallbackTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.plan = self.repo / "PLAN.md"
        self.plan.write_text("Keep the original until the copy is verified.")
        self.calls = []
        self.case = "ok"
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                owner.calls.append((self.path, json.loads(self.rfile.read(int(self.headers["Content-Length"])))))
                if owner.case == "bad_status":
                    self.connection.sendall(b"invalid HTTP status\r\n\r\n")
                    return
                if self.path.startswith("/unavailable/"):
                    self.send_response(402)
                    self.end_headers()
                    return
                if isinstance(owner.case, int):
                    self.send_response(owner.case)
                    self.send_header("Location", owner.url + "/leak/chat/completions")
                    self.end_headers()
                    return
                if owner.case == "rate_limit":
                    self.send_response(429)
                    self.end_headers()
                    return
                review = dict(GOOD)
                if owner.case == "bare":
                    review = {"verdict": "APPROVED"}
                if owner.case == "material":
                    review["findings"] = [{"id": "1", "severity": "high", "path": "plan",
                                           "evidence": "Data loss", "fix": "Retain original"}]
                if owner.case == "mutate":
                    owner.plan.write_text("Different plan")
                result = {"model": "observed-model", "choices": [{
                    "finish_reason": "length" if owner.case == "truncated" else "stop",
                    "message": {"content": json.dumps(review)}}]}
                if owner.case == "shape":
                    result["choices"] = [None]
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
        thread.start()
        self.addCleanup(lambda: (server.shutdown(), server.server_close(), thread.join()))
        self.url = f"http://127.0.0.1:{server.server_port}"
        self.env = {"CLAUDEX_REVIEWER_LOCAL_BASE_URL": self.url + "/v1",
                    "CLAUDEX_REVIEWER_LOCAL_MODEL": "requested-model",
                    "CLAUDEX_REVIEWER_LOCAL_API_KEY_ENV": "TEST_FALLBACK_KEY",
                    "TEST_FALLBACK_KEY": "private-test-key",
                    "CLAUDEX_REVIEWER_DOWN_BASE_URL": self.url + "/unavailable",
                    "CLAUDEX_REVIEWER_DOWN_MODEL": "unavailable-model"}

    def invoke(self, *selection):
        output = io.StringIO()
        runs = self.root / "runs"
        with patch.dict(os.environ, self.env, clear=True), contextlib.redirect_stdout(output):
            code = fallback.main(["--repo", str(self.repo), "--artifacts", str(runs),
                                  *(selection or ("--reviewer", "local"))])
        paths = list(runs.glob("*/result.json"))
        record = json.loads(max(paths, key=lambda p: p.stat().st_mtime_ns).read_text())
        self.assertNotIn("private-test-key", output.getvalue())
        self.assertNotIn("private-test-key", json.dumps(record))
        return code, record

    def test_approval_requires_explicit_limited_context_consent_and_current_plan(self):
        code, record = self.invoke()
        self.assertEqual(code, 0, record)
        self.assertEqual(record["observed_model"], "observed-model")
        self.assertIn(fallback.LIMITATION, record["response"]["limitations"])
        self.assertNotIn("tools", self.calls[0][1])
        with self.assertRaises(RunError):
            check_approval(record, self.plan, self.repo)
        check_approval(record, self.plan, self.repo, allow_limited=True)
        self.plan.write_text("Revised")
        with self.assertRaises(RunError):
            check_approval(record, self.plan, self.repo, allow_limited=True)

    def test_invalid_truncated_and_changed_plan_results_never_approve(self):
        for self.case in ("bare", "material", "truncated", "shape", "bad_status", "mutate"):
            with self.subTest(case=self.case):
                code, record = self.invoke()
                self.assertEqual(code, 1, record)
                self.assertEqual(record["status"], "failed")
                with self.assertRaises(RunError):
                    check_approval(record, self.plan, self.repo, allow_limited=True)

    def test_redirect_does_not_forward_plan_or_key(self):
        for self.case in (301, 302, 303, 307, 308):
            with self.subTest(status=self.case):
                self.calls.clear()
                code, record = self.invoke()
                self.assertEqual(code, 1, record)
                self.assertEqual(len(self.calls), 1)

    def test_only_explicit_chain_advances_on_auth_or_payment_rejection(self):
        code, record = self.invoke("--chain", "down,local")
        self.assertEqual(code, 0, record)
        self.assertEqual(len(record["attempts"]), 2)
        self.assertEqual(record["attempts"][0]["error"], "HTTP 402")
        self.case = "rate_limit"
        self.calls.clear()
        code, record = self.invoke("--chain", "local,down")
        self.assertEqual(code, 1)
        self.assertEqual(len(self.calls), 1)
        self.assertIn("429", record["error"])

    def test_profile_rejects_unsafe_urls_and_missing_keys(self):
        for url in ("http://example.com/v1", "https://user:secret@example.com/v1",
                    "https://example.com/v1?key=secret", "file:///tmp/model"):
            with patch.dict(os.environ, {**self.env, "CLAUDEX_REVIEWER_LOCAL_BASE_URL": url}, clear=True):
                with self.assertRaises(RunError):
                    fallback.profile("local")
        with patch.dict(os.environ, {**self.env, "TEST_FALLBACK_KEY": ""}, clear=True):
            with self.assertRaises(RunError):
                fallback.profile("local")


class QuotaTests(unittest.TestCase):
    def test_rollout_selection_uses_event_time_and_tolerates_partial_events(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / "2026/09/07"
            folder.mkdir(parents=True)
            now = time.time()
            for index in range(12):
                event = {"timestamp": datetime.fromtimestamp(now-index, timezone.utc).isoformat(),
                         "payload": {"rate_limits": {"primary": {"used_percent": index}}}}
                (folder / f"rollout-{index}.jsonl").write_text(
                    '[]\n{"payload": null, "rate_limits": null}\n{"rate_limits":\n' + json.dumps(event) + '\n')
            latest = codex_usage.latest_snapshot(root)
            self.assertEqual(latest[1]["primary"]["used_percent"], 0)
            snap = (now, {key: {"used_percent": 96, "resets_at": now+1000}
                          for key in ("primary", "secondary")}, "unused")
            self.assertEqual(codex_usage.quota_status(snap, 95, 3600, now), 1)
            self.assertEqual(codex_usage.quota_status(snap, 99, 3600, now), 0)
            self.assertEqual(codex_usage.quota_status(snap, 95, 3600, now+4000), 2)
            for malformed in (None, {}, {"used_percent": "96", "resets_at": now+1000},
                              {"used_percent": 96, "resets_at": now-1}):
                snap[1]["primary"] = malformed
                self.assertEqual(codex_usage.quota_status(snap, 95, 3600, now), 2)
