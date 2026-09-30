"""wyrd-evidence-core: public evidence-governance primitives.

Four independently useful pieces, extracted from an internal architecture so
that public tooling can depend on them normally:

``predicate_semantics``
    A lattice of evidence strength. Every claim carries a predicate, and the
    lattice decides whether a given transition is permitted by the evidence
    available. Stronger evidence is not a larger number; it is a narrower set of
    claims that may be made without further support.

``writeback_validator``
    Whether a proposed set of relations may be written back over existing state.
    Encodes the same evidence rules at the level of a whole relation set, so a
    batch write is judged rather than each edge in isolation.

``outcome_taxonomy``
    How an attempt is classified when it ends. Three families -- resolved,
    refused, open -- so "it failed" and "it was correctly refused" do not share a
    representation.

``registry``
    Component state, per-operation policy, and hash-chained provenance. A
    component is registered, moves through a disposition under policy, and its
    history is verifiable after the fact.

These are primitives, not a framework. Nothing here requires an estate, a
private corpus, or a machine-specific path.
"""

from __future__ import annotations

__all__ = [
    "__version__",
    "outcome_taxonomy",
    "predicate_semantics",
    "registry",
    "registry_schema",
    "writeback_validator",
]

__version__ = "0.1.0"
