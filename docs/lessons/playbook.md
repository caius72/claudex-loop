# Integration lessons

### 2026-09-07: Reconcile old proposals against current behavior

| Field | Value |
|---|---|
| Type | tactic |
| Source | verification-before-completion |
| Helpful | 0 |
| Harmful | 0 |

**Context:** Six open PRs targeted skill files replaced by a shared runner.

**Lesson:** Compare each proposal's intended behavior with the current implementation before applying its patch. Test the remaining behavior at the actual transport and approval boundaries.

**Evidence:** Three fixes already existed; the remaining fallback proposal needed structured validation, redirect refusal and explicit limited-context approval. Local HTTP tests exercise those boundaries without model quota.

**Related:** [PR dispositions](../../ACKNOWLEDGMENTS.md), [validation](../../VALIDATION.md).
