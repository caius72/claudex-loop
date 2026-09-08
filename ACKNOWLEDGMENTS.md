# Community contributions and integration record

Reviewed on 2026-09-07 against upstream `8cf5e2c` (the bidirectional runner from PR #16 plus standalone Route from #17). This fork reconciles all six open contributor PRs. Their original patches target older skills, so useful behavior was verified or adapted into the shared runtime instead of replacing the newer implementation. This is a record of integration in **caius72/claudex-loop**, not a claim that upstream PRs or issues have been closed.

## Pull requests

Follow-up on 2026-09-09: integrated PR #18 at `f765ab25`, preserving the earlier adaptations below. Model-default guidance was also corrected across the active skill and English, Chinese and Japanese guides.

| Upstream PR and reviewed head | Contributor | Disposition in this fork |
|---|---|---|
| [#18: Git index fingerprint and Codex reviewer isolation](https://github.com/chaseai-yt/claudex-loop/pull/18), `f765ab25` | [Brian Busch / @buschbrian](https://github.com/buschbrian) | Integrated the index-aware snapshot, divergent-index inspection gate, Codex review/inspection configuration isolation and disabled web search, with five regression tests. Builds keep normal configuration. Codex review model/effort choices must be supplied explicitly to override built-in defaults. |
| [#6: Chinese/Japanese guides](https://github.com/chaseai-yt/claudex-loop/pull/6), `0038e087` | [@tura-ai-agent](https://github.com/tura-ai-agent) | Adapted into [Chinese](README.zh-CN.md) and [Japanese](README.ja.md) guides covering both hosts, Route, current installation, model/executable overrides, approval limits and fallback. They are labeled concise guides rather than verbatim translations. Removed the old unrestricted-build instructions and obsolete skill names from active usage. Local links are validated. |
| [#9: fallback and quota](https://github.com/chaseai-yt/claudex-loop/pull/9), `76fd039b` | [Uwe Jörk / @ujconsulting](https://github.com/ujconsulting) | Adapted the text-only endpoint/profile approach and local quota reader into scripts shipped with the installed skill. [The protocol](skills/claudex-loop/references/fallback.md) supports wait/switch/skip, explicit profiles/chains, retained history, and plan-bound approval with explicit limited-context acceptance. See the review findings below for changes to the proposal. |
| [#11: YAML quoting](https://github.com/chaseai-yt/claudex-loop/pull/11), `e73d9d66` | [@darian033](https://github.com/darian033) | Already implemented by #16: all four current skills have valid quoted descriptions and pass the actual YAML parser in `scripts/validate.py`. Reapplying the old descriptions would undo newer work. |
| [#12: build gates/review scope](https://github.com/chaseai-yt/claudex-loop/pull/12), `8fb2534e` | [Bray / @Dwodgaming](https://github.com/Dwodgaming) | Existing clean-worktree and source-path rules retained. Added explicit writer enumeration, unopened-file limitations, code-comment guarantee checks, cumulative review coverage, and verification of builder self-QA/deviation claims. Test review accepts real regression scenarios as well as new acceptance criteria. |
| [#13: prompt provenance/private output](https://github.com/chaseai-yt/claudex-loop/pull/13), `1fd362a2` | [Uwe Jörk / @ujconsulting](https://github.com/ujconsulting) | Already implemented by #16: installed runner authors the prompt, supplies stdin through `communicate`, and allocates private unique artifact directories. No arbitrary `REVIEW_PROMPT` file or fixed verdict path is used in active skills. Retained and verified through runner tests. |
| [#15: non-Git reviews](https://github.com/chaseai-yt/claudex-loop/pull/15), `b40941f7` | [@mraol08831](https://github.com/mraol08831) | Already implemented by #16 for both initial and resumed read-only reviews. Added explicit argument checks for both, and for keeping the flag absent on builds. Delegated builds still require a clean Git baseline for diff verification. The Git startup guard is not the sandbox boundary. |

## Findings that changed the fallback implementation

The proposal solves a useful problem, but importing its 523-line adapter unchanged would introduce a second, incompatible approval format and these defects:

- `run_review` warns on `finish_reason=length` and then still calls its permissive verdict validator. A truncated reply can therefore carry a passing verdict. The integrated adapter requires normal completion and the existing structured review schema, rejecting incomplete and contradictory results.
- `validate` accepts a verdict anywhere in a response while its error promises a final-line check. Counting three numbered lines does not establish a sound review and rejects legitimate zero-defect plans. The integrated adapter uses the current structured validator with evidence, coverage and limitations; zero findings remain valid.
- Default `urllib` redirect handling can forward authorization headers to another destination. The integrated transport refuses redirects and requires HTTPS for remote endpoints, even without a key because plan text is sensitive too.
- Automatically reading the reviewed repository's `.env` could choose the destination of the plan and borrow a key from the operator's environment. Profiles now come only from the process environment, and each invocation requires a named reviewer or explicit chain. Endpoint selection still requires user authorization.
- The quota reader's newest-file/first-ten heuristic and permissive missing-window handling can mistake old or incomplete data for available quota. The integrated reader uses event timestamps across rollout files and marks stale, expired or incomplete snapshots unknown. It never uses cached data as an authorization or availability gate.

Deliberate omissions: no mandatory finding count, automatic repository `.env` loading, separate provider-balance probes, or silent switch after HTTP 429/network/format failures. The explicit chain advances on authentication/payment rejection (401/402/403); other failures stop for diagnosis. Generic compatible endpoints are supported without promising live compatibility with every vendor. A same-provider endpoint is not advertised as cross-provider verification. Text-only approval never substitutes for final code inspection.

## Reported issues

| Issue | Outcome in this fork |
|---|---|
| [#5: maintenance and silent stdin hang](https://github.com/chaseai-yt/claudex-loop/issues/5) | The hang is already fixed: the shared runner sends its prompt and closes stdin using `communicate`. Fake CLI processes read through EOF in the tests. The project's maintenance/ownership question belongs to the upstream owner; this fork cannot appoint upstream maintainers. |
| [#7: reviewer exhaustion](https://github.com/chaseai-yt/claudex-loop/issues/7) | Implemented explicit text-only fallback, history continuation, advisory local quota visibility, and wait/switch/skip guidance. Missing repository context is disclosed and requires explicit acceptance before build approval. Final code inspection remains independent. |
| [#8: YAML parse error](https://github.com/chaseai-yt/claudex-loop/issues/8) | Verified the current frontmatter with PyYAML for all four active skills. The corresponding quoting defect was already repaired upstream. |
| [#10: macOS executable, scratch paths and Git guard](https://github.com/chaseai-yt/claudex-loop/issues/10) | Added version-probe exit code/stdout/stderr capture and SIGKILL guidance. Existing per-run private output and non-Git read-only support retained. Avoided the report's unsupported general claim that standalone Codex is discontinued and its suggested global install changes. Do not delete the live Codex data directory. |
| [#14: wrapper approval and review evidence](https://github.com/chaseai-yt/claudex-loop/issues/14) | Added explicit guidance against broad shell-prefix allowlisting and trailing sandbox overrides. Current argument-list execution, retained stderr, structured completion validation, private artifacts, and custom plan-path binding address the in-repository defects. External host permission hooks remain the operator's responsibility; a wrapper alone cannot secure an unsafe surrounding shell command. |

## Verification and limits

`python scripts/validate.py` checks active YAML, manifest metadata and local links, including both translated guides. `python -m unittest discover -s tests -v` covers fake CLI processes, disposable Git repositories, and a loopback HTTP endpoint. See [VALIDATION.md](VALIDATION.md) for results and platform limits. No paid model calls are needed. These checks establish transport and approval invariants, not model review quality or exhaustive repository coverage.

The legacy skills in `legacy/` remain explicitly superseded and are not installed by the active plugin. Original licenses and contributor attribution are preserved. Upstream discussions remain available at the linked PRs/issues.
