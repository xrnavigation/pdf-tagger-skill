# Skill installation documentation

## Goal
Refresh the published installation instructions for current agent hosts within Q's approved plan.

## State
PR #1 on docs/skills-installation contains the approved documentation/metadata work and a CI caller pinned to the integrated public shared validator. Q approved the full CI plan and all normal merges after rollout and refreshed bases. Both committed PDF examples run through the existing engine and strict rendering/structure verifier in their own hosted job. No skill behavior or installer changes.

## Decisions and why
Keep one canonical skill tree and preserve current versions. Use direct Antigravity skill locations; do not claim native plugin compatibility. Preserve existing Claude/Codex installation workflows. For CRM, retain its bootstrap, configuration, and credential dependencies; Antigravity support remains unverified.

## Surprises
Antigravity App/IDE and CLI have different user-wide skill locations. Existing repositories already support Codex except MapLibre's missing host manifests. No GitHub Actions workflow files were present in this checkout.

## Next step
Refresh against the current integrated default branch, push the new CI caller, and read hosted checks to completion. Repair scoped failures without weakening checks. Root verifies the evidence and normally merges the PR, then the worker integrates the default branch locally and removes its task branch. Do not run local CI substitute gates.
