# FP-000 — Purpose of First Principles

**Status:** Established

## Purpose

First Principles define the enduring foundations from which ClawForge derives its governance, architecture, engineering decisions, and implementations.

They exist above Architecture Decision Records.

Where Architecture Decision Records answer:

> "What decision was made?"

First Principles answer:

> "Why should that kind of decision exist at all?"

---

## Characteristics

A First Principle:

- describes enduring identity rather than implementation;
- remains applicable across technologies and generations;
- allows future architectural decisions to be derived from it;
- exists independently of any specific programming language, repository, contributor, or implementation.

First Principles are intentionally rare.

Adding, removing, or substantially revising a First Principle should be considered one of the most significant architectural events within ClawForge.

---

## Evolution

Because understanding evolves, First Principles are not considered absolutely immutable.

They are, however, expected to remain exceptionally stable.

Any revision must:

- preserve the historical lineage of the principle,
- explain why previous reasoning became insufficient,
- document the evidence supporting the revision,
- demonstrate that the revision better fulfills ClawForge's enduring purpose.

The rarity of such revisions is a feature rather than a limitation.

---

## Relationship to ClawForge

The governance of ClawForge is layered.

Each layer derives from the one above it.

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
Governance
    │
    ▼
Architecture
    │
    ▼
Engineering
    │
    ▼
Implementation
    │
    ▼
Observation
    │
    ▼
Learning
```

Vision establishes purpose.

Foundation establishes enduring identity.

Orientation establishes sufficient understanding.

First Principles establish enduring truths from which governance and architecture are derived.

Every subsequent layer should remain consistent with the layers above it.