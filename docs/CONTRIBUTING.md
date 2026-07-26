# Contributing to ClawForge

## Welcome

Thank you for contributing to ClawForge.

This project values thoughtful engineering, honest reasoning, and continuous learning above speed or complexity.

Every contribution should make the project easier to understand, maintain, and improve.

---

# Before You Build

Before writing code, ask:

- Does this solve a real problem?
- Is there a simpler solution?
- Does it align with the project's principles?
- Have I documented my reasoning?
- Will someone understand this a year from now?

If the answer to any of these is "no," improve the design before continuing.

---

# Documentation First

Documentation is part of the product.

When making significant changes, update the relevant documents before or alongside the implementation.

Examples include:

- Architecture
- Principles
- Governance
- Build Log
- Roadmap

Code and documentation should evolve together.

---

# Communication

When proposing changes:

1. Describe the problem.
2. Explain the proposed solution.
3. Discuss tradeoffs.
4. Identify risks.
5. Recommend testing.
6. Update documentation.

Clear communication is as valuable as clear code.

---

# Coding Philosophy

Prefer:

- readability over cleverness
- modularity over duplication
- explicitness over hidden behavior
- maintainability over optimization
- consistency over novelty

Optimize only when there is evidence that optimization is needed.

---

# Testing

Every meaningful feature should answer:

- Does it work?
- Can it fail safely?
- Is it understandable?
- Can another contributor verify it?

Testing should increase confidence, not merely increase coverage.

---

# Versioning

Meaningful work should produce:

- a Git commit
- an updated build log
- relevant documentation changes

History is part of the project.

---

# Community Standards

Assume good intent.

Challenge ideas respectfully.

Support claims with reasoning and evidence.

Accept correction gracefully.

Offer correction constructively.

Learning is the shared objective.

---

# Leave It Better

Every contribution should leave ClawForge more understandable than it was before.

Future contributors should benefit from today's work.

That is the standard.
---

## Decision and Documentation Flow

Major changes should follow this sequence:

1. Vision establishes why ClawForge exists.
2. Principles establish how ClawForge approaches its work.
3. The Blueprint records active questions, exploration, alternatives, and provisional decisions.
4. Architecture Decision Records preserve accepted engineering decisions and their reasoning.
5. Architecture documents describe what is currently true about the system.
6. Implementation expresses the accepted architecture in code.
7. Build logs preserve completed historical progress.

The expected working flow is:

```text
Vision
    |
    v
Principles
    |
    v
Blueprint Discussion
    |
    v
Provisional Decision
    |
    v
Architecture Decision Record
    |
    v
Authoritative Architecture
    |
    v
Implementation
    |
    v
Observation and Improvement