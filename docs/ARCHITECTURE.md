# ClawForge Architecture

## Purpose

This document describes the currently accepted architecture of ClawForge.

It is an authoritative summary of the system's architecture rather than a discussion of alternatives.

Active architectural exploration belongs in `BLUEPRINT.md`.

Enduring identity principles belong in `docs/foundation/`.

Permanent architectural decisions belong in the Architecture Decision Records under `docs/decisions/`.

Only architectural conclusions supported by the Foundation and accepted through the appropriate governance process should appear in this document.

---

## Architectural Hierarchy

ClawForge is organized through the following relationship:

```text
Vision
    |
    v
Foundation
    |
    v
Governance and Architectural Decisions
    |
    v
Architecture
    |
    v
Engineering
    |
    v
Implementation
    |
    v
Operation
    |
    v
Observation
    |
    v
Learning
    |
    +------> Foundation Review
```

Each layer has a distinct responsibility:

- **Vision** provides purpose.
- **Foundation** provides identity.
- **Governance and ADRs** provide deliberate decision-making.
- **Architecture** provides accepted structure.
- **Engineering** translates structure into executable design.
- **Implementation** makes the design real.
- **Operation and observation** produce evidence.
- **Learning** informs future improvement.

The return from learning to Foundation review does not imply frequent changes to First Principles. It ensures that no part of ClawForge is exempt from deliberate re-evaluation.

---

## Governed Change Architecture

ClawForge changes through a governed lifecycle that connects Orientation, Integrity evaluation, implementation, verification, finalization, and durable memory.

```text
AUTHORITATIVE CLAWFORGE STATE
            |
            v
        ORIENTATION
            |
            v
   DEFINE PROPOSED CHANGE
            |
            v
      CLASSIFY IMPACT
            |
            +---- NON-MEANINGFUL
            |           |
            |           v
            |   LIGHTWEIGHT REVIEW
            |           |
            |           +---- ESCALATE
            |           |
            |           +---- CONFIRMED NON-MEANINGFUL
            |
            +---- MEANINGFUL OR PROTECTED
                        |
                        v
              INTEGRITY EVALUATION
                        |
                        +---- HOLD
                        |       |
                        |       v
                        |   EXPLAIN, REMEDIATE,
                        |   AND RE-EVALUATE
                        |
                        +---- PROCEED
                                |
                                v
                           IMPLEMENT
                                |
                                v
                         VERIFY RESULT
                                |
                                +---- HOLD
                                |
                                +---- FINALIZE
                                        |
                                        v
                              NEW AUTHORITATIVE STATE
                                        |
                                        v
                                INTEGRITY MEMORY
                                        |
                                        +----> FUTURE ORIENTATION
```

## Current State

ClawForge now has an established Foundation layer containing:

- `FP-000 — Purpose of First Principles`
- `FP-001 — Deliberate Continuity`

These principles establish that ClawForge must preserve enough understanding and historical continuity for successive contributors to evaluate and deliberately improve what came before.

ClawForge also has two accepted architectural lifecycles:

- Orientation establishes sufficient understanding before responsible participation.
- Integrity-Governed Change controls how meaningful proposals move from evaluation through implementation, verification, finalization, and durable memory.

These lifecycles are established through:

- `Build 0.0.4 — Orientation`
- `Build 0.0.5 — Integrity`
- `ADR-0001 — Integrity-Governed Change`

The executable architecture remains intentionally minimal.

ADR-0002 establishes Python as ClawForge's first replaceable reference implementation and `clawforge` as the canonical executable command. The optional `cf` alias and `python -m clawforge` development invocation route to the same command behavior.

The Integrity Record schema and future executable capabilities remain subject to later architectural decisions.
