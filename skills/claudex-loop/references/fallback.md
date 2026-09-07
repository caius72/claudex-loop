# Reviewer outages

The default review remains the other provider's CLI. On failure, preserve the result directory and all completed rounds in `LOG_FILE`. An empty reply, HTTP 429, or a failed version probe is not enough to diagnose exhausted credits. Inspect the retained diagnostics; do not retry blindly or count a failed attempt as a round.

Present three choices when the selected reviewer is unavailable:

1. **Wait:** retry once the cause is resolved; resume the last successful CLI result with current dispositions. Failed attempts remain in the log. A missing session requires a fresh review with the prior findings supplied as feedback.
2. **Switch:** use an explicitly selected text-only endpoint, naming the provider/model and disclosing exactly which plan and history will be sent. Choose a provider independent of the planner where possible; same-provider reviews are not cross-provider verification. Existing explicit authorization can cover a named chain, but a repository's configuration never supplies consent.
3. **Skip:** only on the user's explicit choice; log the reason and mark the plan not independently approved. Use the existing `--unreviewed-spec` build path if implementation is authorized. Final inspection has its own opt-out.

## Optional quota hint

Resolve `USAGE` as `../scripts/codex_usage.py` relative to this installed reference:

```text
python USAGE --json
python USAGE --sessions PATH_TO_SESSIONS --max-age 3600 --threshold 95
```

This reads only local rollout snapshots; no API or model call. It honors `CODEX_HOME`. Exit 0 means recent primary/secondary windows below the threshold, 1 means a recent window at/above it, and 2 means unknown, stale or incomplete data. Output includes the snapshot timestamp and reset epochs. Expired resets are unknown, not evidence of renewed quota. Treat all values as advisory and never block a review solely on cached data. Credits and other accounts/models may have different limits.

## Text-only fallback

Resolve `FALLBACK` as `../scripts/fallback_review.py` beside the installed runner. It uses an OpenAI-compatible `/chat/completions` JSON response, without tools or repository access. No model or endpoint is chosen by default.

Set a profile in the **process environment** using a trusted shell or secret manager. The adapter never loads a repository `.env`:

```bash
export CLAUDEX_REVIEWER_LOCAL_BASE_URL=http://127.0.0.1:1234/v1
export CLAUDEX_REVIEWER_LOCAL_MODEL=your-loaded-model-id
# For a remote HTTPS profile, point at an existing secret-manager variable:
# export CLAUDEX_REVIEWER_REMOTE_API_KEY_ENV=MY_REVIEW_API_KEY
```

In PowerShell use `$env:CLAUDEX_REVIEWER_LOCAL_BASE_URL = 'http://127.0.0.1:1234/v1'` and `$env:CLAUDEX_REVIEWER_LOCAL_MODEL = 'your-loaded-model-id'`. A remote profile also needs its own `BASE_URL` and `MODEL`.

```text
python FALLBACK --reviewer local --repo PROJECT --plan docs/plan.md
python FALLBACK --reviewer local --repo PROJECT --plan docs/plan.md --log HOST_APPROVED_HISTORY
python FALLBACK --chain first,second --repo PROJECT --plan docs/plan.md
```

`--chain` is an explicit ordered selection for this invocation. It advances only on HTTP 401/402/403, recording each failed attempt. A 429, timeout, network failure, malformed reply or truncation stops the chain for diagnosis; it does not prove terminal exhaustion. There is no separate balance/preflight probe and no automatic retry. `--timeout` (600 seconds) and `--max-tokens` (8192) are configurable positive limits. Local endpoints must support this response format; no live provider compatibility is promised by the automated tests.

Remote endpoints require HTTPS; HTTP is allowed only on loopback. Redirects are refused even between local endpoints, so credentials and plan text cannot follow a redirect. The selected service receives the plan and optional history; do not send private content to an unapproved service. No configuration alone authorizes a network call.

Each invocation creates a private, unique directory outside the checkout with `prompt.txt`, the received `response.json` when available, and `result.json`. Preserve the full result and its path in `LOG_FILE`, labeling every attempt with reviewer, model, verdict and **text-only, no repository access**. Supply the host-approved history via `--log` on later calls: API calls have no session memory. Round limits still apply across provider changes. Diagnostics are private staging artifacts, not repository deliverables.

The adapter reuses the runner's structured validation. Empty findings are valid; a bare verdict, incomplete response, material findings paired with APPROVED, or a plan changed during the call cannot approve. The record binds the exact plan path, repository path and SHA256. An unchanged approved fallback result is accepted for building **only with explicit acceptance of its limited coverage**:

```text
python RUNNER check --host claude --repo PROJECT --plan docs/plan.md --approval FALLBACK_RESULT --allow-limited-review
python RUNNER build --host claude --builder codex --repo PROJECT --plan docs/plan.md --approval FALLBACK_RESULT --allow-limited-review --proof "python -m unittest discover"
```

Use the actual host and builder. Without `--allow-limited-review`, the runner rejects fallback approval. It does not resume a fallback as a CLI session or accept it as final code inspection. A later repository-reading review is advisable when missing code context matters; do not describe a text-only approval as equivalent coverage.
