# wyrd-evidence-core

**Evidence has a strength lattice, and most systems that talk about evidence
never define it. This one does — as data, not as commentary.**

A claim is not a boolean. It carries a predicate, and the predicate sits on a
lattice that decides what may be concluded from it. Moving *down* the lattice is
free: losing a claim is admissible. Moving *up* is strengthening, and it requires
evidence. Standing still is free. That asymmetry is the whole rule, and this
package encodes it structurally rather than describing it in a docstring.

```python
>>> from wyrd_evidence_core import predicate_semantics as ps
>>> ps.requires_evidence(before_strength=0, after_strength=1)
True      # strengthening needs evidence
>>> ps.requires_evidence(before_strength=1, after_strength=0)
False     # weakening is admissible loss
>>> ps.STRENGTH_NAME[5]
'AUTHORITY'
```

Twenty-four predicates across six strength classes, from `CORRELATES_WITH` at the
bottom to the predicates that may confer authority at the top.

---

## Contents

- [Install](#install)
- [The four modules](#the-four-modules)
- [predicate_semantics](#predicate_semantics)
- [writeback_validator](#writeback_validator)
- [outcome_taxonomy](#outcome_taxonomy)
- [registry](#registry)
- [Design decisions worth knowing about](#design-decisions-worth-knowing-about)
- [Tests](#tests)
- [Provenance](#provenance)
- [License](#license)

---

## Install

```console
$ git clone https://github.com/Wyrd-Flux/wyrd-evidence-core
$ cd wyrd-evidence-core
$ python -m venv .venv
$ .venv/bin/pip install .
```

No dependencies. Standard library only — a governance primitive that cannot be
installed cleanly is not a primitive anyone will adopt.

Python 3.11 or newer.

---

## The four modules

| Module | Question it answers |
|---|---|
| `predicate_semantics` | what does this evidence permit me to claim? |
| `writeback_validator` | may I write this whole set of relations back over existing state? |
| `outcome_taxonomy` | how should this attempt be classified, given how it ended? |
| `registry` | what is this component's state, who may change it, and can its history be verified? |

They compose. `writeback_validator` consults `predicate_semantics` for the
asymmetry rule. `registry` enforces policy that references operation levels. None
of them knows about the others' storage, and none requires a corpus, a network,
or a machine-specific path.

---

## predicate_semantics

```python
>>> from wyrd_evidence_core import predicate_semantics as ps
>>> sorted(ps.PREDICATES)[:5]
['ASSOCIATED_WITH', 'BRIDGELOGGER_REGISTERS_ROW', 'CAUSES', 'CORRELATES_WITH', 'DEFINES_CONCEPT']
>>> p = ps.get("CAUSES")
>>> p.directional, p.strength_class
(True, 4)
>>> ps.self_check()
[]
```

Every predicate declares its own structural properties: whether it is
directional, whether it is symmetric, whether it may establish identity,
ownership, or causation, and what temporal ordering it implies. Those properties
are checked by `self_check()`, which fails loudly on an incoherent registry.

**`get()` raises on an unknown predicate.** It does not return a default:

```python
>>> ps.get("RELATES_TO")
KeyError: UNREGISTERED_PREDICATE: 'RELATES_TO' is not in the predicate registry;
          refusing to treat an untyped edge as evidence
```

This is deliberate. A permissive fallback is how a universal `RELATES_TO`
primitive creeps back in — the thing a typed evidence registry exists to prevent.
An untyped edge is not a neutral unknown; it is the absence of a claim about what
kind of claim it is.

---

## writeback_validator

Judges a *proposed* relation set against the *current* one, and returns a verdict
that keeps the two apart:

```python
>>> from wyrd_evidence_core import writeback_validator as wv
>>> edge = wv.Edge(subject="a", predicate="CAUSES", obj="b",
...                basis="OBSERVED", evidence=("tests/test_pipeline.py",))
>>> verdict = wv.validate(before=[edge], proposed=[edge])
>>> verdict.refused
[]
>>> len(verdict.accepted)
1
```

Three refusals you will meet early:

| Refusal | Meaning |
|---|---|
| `NEW_EDGE_WITHOUT_EVIDENCE` | a new relation with no evidence behind it |
| `RELATION_STRENGTHENING` | a claim moved up the lattice without a token |
| `UNREGISTERED_PREDICATE` | the edge uses a predicate outside the registry |

**Two separate controls, deliberately not one.** `authorization` is the set of
evidence tokens that permit *strengthening*. `permitted_predicates` restricts
*which relations may be asserted at all*. A token that authorizes recording where
something lives must not also authorize declaring what that something **is**.
Collapsing both into a single token set makes the restriction advisory, which is
the same failure mode as an unenforced permission.

---

## outcome_taxonomy

Ten outcome classes in four families:

| Family | Meaning |
|---|---|
| `RESOLVED` | the attempt reached an answer |
| `REFUSED` | the attempt was correctly refused — **not** a failure |
| `CLOSED` | finished and no longer available |
| `OPEN` | still in progress |

The distinction the taxonomy exists to protect: *"it failed"* and *"it was
correctly refused"* must not share a representation. A governance system that
counts a refusal as a failure will be optimised into admitting everything, because
the number will look terrible.

```python
>>> from wyrd_evidence_core import outcome_taxonomy as ot
>>> counts = {c: 1 for c in ot.ALL_CLASSES}
>>> sorted(ot.REFUSED_CLASSES)
['REFUSED_FALSIFYING_FIX', 'REFUSED_SCOPE_EXCEEDED', 'REFUSED_SEMANTICALLY_UNJUSTIFIED']
>>> ot.family("REFUSED_SCOPE_EXCEEDED")
'REFUSED'
```

---

## registry

Component state, per-operation policy, and hash-chained provenance.

```python
>>> from wyrd_evidence_core import registry, registry_schema as rs
>>> r = registry.StateRegistry(data_dir="/tmp/example")
>>> component = rs.ComponentState(
...     name="example",
...     repository="wyrd-evidence-core",
...     path="wyrd_evidence_core/registry.py",
...     state=rs.State(
...         disposition=rs.Disposition.OPEN,
...         research_state=rs.ResearchState.ACTIVE,
...         established_by="you", established_date="2026-09-30", version=1,
...     ),
...     policy=rs.Policy(
...         modification={},
...         new_experiment=rs.OperationPolicy(level=rs.OperationLevel.ALLOWED),
...         reopening=rs.OperationPolicy(
...             level=rs.OperationLevel.REQUIRES_AUTHORIZATION,
...             reason="reopening requires explicit authorization",
...         ),
...     ),
...     authority=rs.Authority(
...         established_by="you", provenance="registered by hand",
...         evidence=[], requires_for_reopening="Human authorization",
...     ),
...     dependencies=[], metadata={}, history=[],
... )
>>> r.register(component)
>>> r.can_modify("example", "modify").permitted
True
```

**Disposition gates first, policy second.**

| Disposition | Effect |
|---|---|
| `OPEN` | all operations permitted |
| `PRESERVE`, `CLOSED` | per-operation policy is consulted |
| `SUPERSEDED`, `VOIDED` | every operation blocked (terminal) |

`SUPERSEDED` is terminal: `LEGAL_TRANSITIONS[SUPERSEDED]` is empty, and `OPEN`
cannot jump straight to it.

**`unknown != forbidden`.** Asking about a component that is not registered
returns *permitted*, with the reason `"Component not in registry (unknown != 
forbidden)"`. Inventing a refusal for a missing registration would make absence
look like a policy decision, and would hide a component that was never
registered.

**History is verifiable, not merely recorded.**

```python
>>> r.verify_history("example").valid
True
```

Each record carries a `prev_hash`/`hash` pair. Tampering with any record makes
verification fail and reports the first invalid index. Verification that cannot
fail is not verification.

---

## Design decisions worth knowing about

**Evidence resolution has an explicit root.** Relative evidence references are
resolved against `WORKSPACE_ROOT`, which defaults to the distribution root and
can be set with `WYRD_EVIDENCE_CORE_WORKSPACE_ROOT`. Upstream this was implicitly
"wherever the package was installed", which quietly coupled evidence resolution
to the operator's filesystem layout. A reference that does not resolve is
recorded as `exists: False` — never treated as satisfied.

**Commands are inspected, never executed.** A `python script.py --flag` evidence
reference is parsed for its script path. Nothing is run during resolution.

**Stdlib only, no vendored code, no corpus.** `import wyrd_evidence_core` pulls in
nothing from the estate it came from. There is no private graph, no concept
registry, and no filesystem layout this package expects to find.

---

## Tests

```console
$ python -m pytest -q
38 passed
```

The three upstream modules ship their own self-check suites, and this package runs
them **unmodified** as its behavioural specification — `predicate_semantics` has 24
predicates to cross-check, `writeback_validator` has 11 verdict cases, and
`outcome_taxonomy` has 11 self-qualification cases. If extraction had changed a
single rule, they would fail.

The remainder cover the registry surface (which had no upstream test of its own)
and the properties that make this a public dependency: bounded import cost, no
filesystem paths from the extraction environment, overridable evidence root, and
line-anchor verification.

---

## Provenance

Extracted verbatim from an internal architecture. Exact source paths and SHA-256
hashes, the four mechanical edits made during extraction, and the operator
attestation are recorded in [`docs/PROVENANCE.md`](docs/PROVENANCE.md).

One fact worth stating plainly: the three `C:\G1\tools` modules had **no version
control history at source** (`NO_VCS_HISTORY_AT_SOURCE`). No history was
fabricated; the provenance is recorded as paths, hashes, and operator attestation
instead.

## License

**Apache-2.0.** See [`LICENSE`](LICENSE).

Reuse is permitted with an explicit patent grant. No license was added to or
modified in any internal source repository as part of this extraction.
