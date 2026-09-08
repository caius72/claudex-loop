# Validation — bidirectional loop

## PR #18 integration, 2026-09-09

Integrated upstream PR #18 at `f765ab25` on this fork. On macOS with Python 3.14, **36 tests passed**, `scripts/validate.py` passed with the existing PyYAML development dependency in a temporary virtual environment, and `git diff --check` passed.

Before applying the runtime fix, `test_inspection_refuses_divergent_index` failed because inspection accepted a staged change hidden by restored working-tree content. It passes after the fix. The five imported tests cover hidden staged content, staged deletion/addition, staging-only fingerprint changes, refusal of divergent staged changes, and Codex configuration isolation flags for fresh/resumed calls while preserving build configuration. Existing tests cover the shared build-resumption and inspection-invalidation paths.

The integration also corrects model/effort defaults and inspection guidance across the active skill and English, Chinese and Japanese guides. Codex reviews skip user configuration, so specific model/effort choices require explicit arguments. Stage intended content before inspection: later staging changes the fingerprint even when working-tree bytes remain identical.

No live model calls were made for this integration. The contributor's live Codex tool-inventory probe in PR #18 was not repeated locally; fake CLI tests verify argument construction, not the external CLI's enforcement. Translated guidance has not had independent native-speaker review.

## Community integration, 2026-09-07

Validated on macOS with Python 3.14: metadata/reference validation and **31 tests passed**. The suite retains the 23 existing runner contracts, adds failed version-probe diagnostics and explicit limited-context check/build acceptance, and exercises fallback transport and approval against a real loopback HTTP server plus synthetic quota rollouts. The local sandbox initially denied socket binding; rerunning with local networking enabled passed. No model/API quota was consumed.

New coverage includes normal text-only approval with explicit acceptance, changed-plan invalidation, malformed/contradictory/truncated replies, redirect refusal, explicit auth/payment chains, no switch on 429, unsafe endpoint/missing-key rejection, and stale/malformed quota data. The non-Git review flag is checked on both initial and resumed calls and excluded from builds. Translated README links are part of metadata validation.

The first Python 3.10 CI run exposed an overly specific test assertion: urllib rejects HTTP 308 through a different exception path than Python 3.14, while both refuse the redirect. The test now checks the required behavior (failed review and no forwarded request), not version-dependent error wording. Malformed HTTP status lines also produce a durable failed result.

The Chinese/Japanese guides were updated and checked against current paths, roles and commands, but have not received independent native-speaker review. No live fallback endpoint compatibility or comparative model-quality claim follows from the local fake endpoint. The historical live tests below were run by upstream, not repeated for this integration.

## Upstream validation record

Development date: 2026-09-06. Tests run in disposable fixtures; production repositories were not built or modified by live smoke tests.

## Automated checks

- `python scripts/validate.py`: active skill frontmatter, local references, both provider manifests and shared-runner presence.
- `python -m unittest discover -s tests -v`: **23 passing tests** with fake CLI executables and real temporary Git repositories, without model calls.
- Codex Skill Creator validator: all three active skills.
- Codex Plugin Creator validator: `.codex-plugin/plugin.json`.
- `git diff --check`.

The contract suite covers both host directions, explicit model selection, read-only reviewer argument construction, success/failure parsing, malformed/empty/incomplete output, a failed turn following successful output, session identity on resume, timeout handling, plan hash invalidation, staged/untracked/deleted change coverage, inspection invalidation and preservation of unrelated work during build resumption.

GitHub Actions is configured for Windows, macOS and Linux. Local results establish Windows behavior; cross-platform CI results must be checked on the PR before merge.

## Live model checks

| Check | Result |
|---|---|
| Fable 5.1 reviews a deliberately broken backup plan through the Codex-host route | REVISE; identified deletion-before-read data loss; valid structured output, coverage and session UUID |
| Same Fable session reviews the revised plan | APPROVED with low-priority advice; exact UUID preserved and new plan hash recorded |
| Astra through npm Codex CLI 0.144.5 | Correctly failed, preserving the server error that this model needs a newer CLI |
| Astra through app-bundled Codex CLI 0.153.4 | REVISE; independently identified the seeded data-loss defect; valid structured output |
| Same Astra session reviews the revised plan | APPROVED with zero findings; exact UUID preserved and new plan hash recorded |
| Approval checks on both revised plans | Passed against the actual plan path and current content |
| Fable and Astra separately implement a tiny addition work order | Each created only addition.py; existing acceptance-check file unchanged |
| Host independently runs `python -B check.py` on both implementations | All three acceptance checks passed for each implementation |
| Fresh Astra inspects Fable's code | APPROVED; new untracked addition.py included in the inspected snapshot |
| Fresh Fable inspects Astra's code | APPROVED; new untracked addition.py included in the inspected snapshot |

Fable runs used Claude Code 2.1.261. The Astra test used an explicit CLI executable path rather than changing the user's global installation. The model selection was explicit in both adapters.

Both delegated builders reported that their proof commands were blocked locally: Claude needed approval in headless mode; Codex's Windows sandbox could not access the Python executable. Neither denial was bypassed. The coordinating host ran the proof independently and observed passing results. A completed build turn is not a verified build; the mandatory host proof step resolved these gaps before final inspection.

The fixture checks exercise transport and obvious-defect detection, not comparative model quality. No claim is made that one pairing is better or that an APPROVED response proves exhaustive correctness. A future benchmark should compare defect recall, false positives, proof results, time and usage on the same tasks, including sound plans.

## Limits

- Live review tests were run on Windows. Automated fake-CLI coverage is configured for all three operating systems.
- CLI versions, account access and permission behavior can change; diagnostics identify the selected executable and requested model.
- Codex's shell sandbox does not constrain external MCP side effects. The PR #18 integration now ignores user configuration and disables web search for Codex reviews; see the runtime reference. Claude's adapter removes non-reading tools and MCP from the reviewer.
- Structured-output validation can reject broken transport and inconsistent verdicts, but cannot prove a model's findings or claimed coverage.
