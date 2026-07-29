# ClawForge Governance

## Purpose

Governance defines how ClawForge evolves.

It protects the project's mission while allowing continuous improvement.

The objective is not to prevent change.

The objective is to ensure that change is thoughtful, documented, and accountable.

---

# Foundational Rule

No idea is above question.

No contributor is above correction.

No document is beyond improvement.

Respect is mandatory.

Evidence is expected.

Curiosity is encouraged.

---

# Decision Principles

Every significant change should answer:

1. What problem does this solve?
2. Why is this change needed?
3. What alternatives were considered?
4. What are the tradeoffs?
5. How will success be measured?
6. Can this decision be reversed?
7. What documentation must be updated?

---

# Change Classification and Integrity Review

ClawForge classifies proposed changes according to their effect, not merely the artifact changed, the contributor involved, or the label applied to the work.

A documentation edit, bug fix, implementation change, or correction may be meaningful when it changes ClawForge's interpretation, behavior, authority, architecture, history, or future decision-making.

When impact is uncertain, the proposal must receive the more protective review path.

## Lightweight Review

Lightweight Review applies only to demonstrably non-meaningful corrections.

A correction may use the lightweight path when ClawForge can establish that it does not alter:

- meaning or interpretation
- behavior or implementation
- authority, permission, or governance
- architecture or required process
- authoritative precedence
- historical understanding
- the basis for future decisions

Lightweight Review produces:

- `CONFIRMED NON-MEANINGFUL`
- `ESCALATE`

Uncertain, disputed, unsupported, or expanded impact requires `ESCALATE` to the full Integrity process.

## Meaningful Changes

A proposed change is meaningful when it could alter ClawForge's:

- identity
- governing interpretation
- authority
- obligations
- architecture
- behavior
- historical record
- basis for future decisions

Every meaningful change must pass the Integrity process defined by `ADR-0001 — Integrity-Governed Change`.

The evaluation must consider:

1. Orientation
2. Intent
3. Governance
4. Consistency
5. Process
6. Traceability
7. Consequence
8. Authority

Every applicable check must be supported by evidence.

The decision must be `HOLD` when required evidence, governance, authority, consistency, or understanding is insufficient.

A `PROCEED` authorizes only the specific next step evaluated.

Implementation must be verified before the result may be deliberately finalized into ClawForge's authoritative state.

## Protected Changes

A meaningful change is protected when it alters or could alter ClawForge's foundational commitments or the mechanisms that protect its integrity.

Protected Changes include changes affecting:

- the Foundation
- First Principles
- governance
- authority and approval structures
- override rules
- the Integrity process
- authoritative sources or their precedence
- the conditions of `HOLD`, `PROCEED`, verification, or finalization
- the mechanisms used to classify, evaluate, verify, or finalize change

Protected Changes require:

- evaluation against the authoritative pre-change state
- the full Integrity process
- a distinct Challenge Review
- heightened verification
- preservation of the prior authoritative state
- explicit finalization under authority established before the proposal

A proposal must not define the rules, authority, evidence, or standards by which it approves itself.

Any proposal to weaken, remove, bypass, or redefine these protections is itself a Protected Change.

## Integrity Memory

Every Integrity decision must produce a durable and inspectable record sufficient for future participants to understand:

- what was proposed
- which authoritative state governed the evaluation
- what evidence and governing artifacts applied
- why the result was reached
- what action was authorized
- what was implemented
- how the result was verified
- why and under whose authority it was finalized
- what new authoritative state resulted

Earlier reasoning must not be silently rewritten.

Corrections, superseding decisions, implementation differences, uncertainty, and disagreement must remain traceable.

* * *

---

# Human Responsibility

ClawForge performs the governed Integrity evaluation.

Humans, artificial intelligence, agents, implementations, and other participants may:

- propose
- provide evidence
- recommend
- critique
- simulate
- operate defined evaluation roles
- implement authorized work
- verify results when governance permits

No participant may substitute personal assertion, ownership, status, or technical capability for an Integrity decision.

Under the governance currently in effect, artificial intelligence does not independently possess consequential approval or finalization authority over ClawForge.

Human contributors remain responsible for consequential approval and finalization.

Any future delegation or expansion of that authority requires separate evaluation as a Protected Change.

* * *

---

# Evidence Standards

When possible:

- distinguish fact from opinion
- distinguish observation from inference
- distinguish confidence from certainty
- distinguish evidence from speculation

Clarity is preferred over persuasion.

---

# Correction Policy

Mistakes are expected.

Hidden mistakes are dangerous.

Corrections should be:

- documented
- explained
- preserved in project history

The goal is learning, not blame.

---

# Build Discipline

Every meaningful change should produce:

- documentation updates
- a Git commit
- a build log entry
- version history

Major architectural changes should also include a rationale.

---

# Stewardship

Each generation of contributors inherits ClawForge from the previous one.

The responsibility of every contributor is to leave the project more understandable than they found it.

Build systems.

Preserve knowledge.

Invite future builders.