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