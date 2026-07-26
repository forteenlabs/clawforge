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

## Current State

ClawForge now has an established Foundation layer containing:

- `FP-000 — Purpose of First Principles`
- `FP-001 — Deliberate Continuity`

These principles establish that ClawForge must preserve enough understanding and historical continuity for successive contributors to evaluate and deliberately improve what came before.

The executable architecture remains intentionally minimal while the project prepares to evaluate its first reference implementation.