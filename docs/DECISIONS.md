# ClawForge Architecture Decisions

## Purpose

This document is the official index of ClawForge Architecture Decision Records (ADRs).

Architecture Decision Records preserve significant architectural decisions, the reasoning that led to them, and the consequences of adopting them.

This document does not contain the decisions themselves.

Its purpose is to record which Architecture Decision Records have been accepted and where they fit within the governance of ClawForge.

---

# Relationship to ClawForge Governance

Architecture Decision Records exist within the broader governance of ClawForge.

They do not establish ClawForge's identity.

They apply and interpret that identity.

The relationship is:

```text
Vision
    │
    ▼
Foundation
    │
    ▼
Orientation
    │
    ▼
First Principles
    │
    ▼
Architecture Decision Records
    │
    ▼
Authoritative Architecture
    │
    ▼
Implementation
```

Each layer builds upon the one above it.

Architecture Decision Records should never redefine Vision, Foundation, Orientation, or accepted First Principles.

Instead, they preserve important architectural decisions made in service of those governing documents.

---

# Creating Architecture Decisions

New Architecture Decision Records should be created only after sufficient architectural understanding has been established.

Active exploration, questions, alternatives, and provisional ideas belong within the current build documentation until an architectural decision has been accepted.

Once accepted, the decision is preserved as an ADR and becomes part of ClawForge's permanent architectural history.

The rules governing the Architecture Decision Record process are defined by ADR-0000.

---

# Architecture Decision Record Index

## ADR-0000 — Architecture Decision Records

**Status:** Frozen

Defines:

- what an Architecture Decision Record is,
- when an ADR is required,
- how ADRs are accepted,
- how ADRs are maintained,
- and how future ADRs supersede earlier architectural decisions without rewriting history.

---

## ADR-0001 — Integrity-Governed Change

**Status:** Accepted

Defines:

- how ClawForge classifies proposed changes
- the eight checks used to evaluate meaningful changes
- the requirements for `HOLD` and scoped `PROCEED` results
- verification and deliberate finalization
- Lightweight Review for demonstrably non-meaningful corrections
- heightened protection and Challenge Review for Protected Changes
- ClawForge's role as the governed Integrity evaluator
- the Integrity Memory required to preserve how and why ClawForge changes

---

# Superseded Architecture Decisions

None.

---

# Future Decisions

This index intentionally records only accepted Architecture Decision Records.

Candidate decisions, architectural discussions, and exploratory work belong within active build documentation until they become accepted architectural decisions.