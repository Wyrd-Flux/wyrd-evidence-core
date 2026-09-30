# wyrd-evidence-core — ARCHIVED

> **This repository is archived and is no longer an active dependency.**
>
> Its implementation was folded into
> [`Wyrd-Flux/veritas`](https://github.com/Wyrd-Flux/veritas), which is now
> self-contained and declares **no dependencies at all**. The modules in
> `wyrd_evidence_core/` live there as
> [`veritas_demo/evidence/`](https://github.com/Wyrd-Flux/veritas/tree/main/veritas_demo/evidence).

## Why it was archived

This repository had exactly one consumer.

That is not by itself a reason to publish a package boundary — it is a reason to
*stop* publishing one. A reusable-looking implementation is not automatically a
reusable subsystem, and extraction should follow demonstrated reuse rather than
precede it.

Shipping it as a dependency also carried a shape I would not choose twice: a git
URL with a single consumer pins to a *branch*, not a version, so `pip install`
resolved whatever `main` happened to be at that moment.

## What to use instead

```console
$ git clone https://github.com/Wyrd-Flux/veritas
$ cd veritas
$ python -m venv .venv
$ .venv/bin/pip install .
$ .venv/bin/veritas-demo selftest
```

Nothing else is required. No dependency on this repository, no environment
variables, no source-tree bindings.

**Do not depend on this repository.** It receives no further work, and the
archived code is not released as a version.

## What is retained, and why

This repository is **not deleted**. It is kept so that:

- the extraction record stays readable — source paths, SHA-256 hashes, the
  operator attestation, and the mechanical edits made during extraction
- the commit the code passed through before being folded into Veritas remains
  navigable: [`7c11c45`](https://github.com/Wyrd-Flux/wyrd-evidence-core/tree/7c11c45756e2f61df6d32cf7f961806ae410e335)
- anyone auditing where Veritas' evidence primitives came from can follow the
  chain back to the internal source trees

Nothing here is the active implementation. It is a provenance record with a
readme attached.

## If a second consumer appears

That is the concrete condition for re-extracting a shared library, and it would
be a genuine reason rather than a speculative one. If a second independent
project needs the evidence lattice, the relation-set validator, the outcome
taxonomy or the component registry, the extraction becomes justified and this
code has a home again.

Until then: use Veritas, or copy the five modules — they are MIT there and
Apache-2.0 here, and both licences permit that with attribution.

## Provenance

Full extraction provenance remains in
[`docs/PROVENANCE.md`](docs/PROVENANCE.md), including the
`NO_VCS_HISTORY_AT_SOURCE` fact for the three modules taken from a directory that
was never under version control.

## License

Apache-2.0, unchanged. The same code is MIT inside
[`Wyrd-Flux/veritas`](https://github.com/Wyrd-Flux/veritas) — a strictly more
permissive grant of the same code by the same rights holder.
