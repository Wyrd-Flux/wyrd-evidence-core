# Source provenance

Extraction date: **2026-09-30**. First public commit: see `git log --reverse`
for this repository — the commit that introduced the extracted implementation.

## What this package is

Five files, extracted verbatim from an internal architecture so that public
tooling can depend on them normally instead of binding to a private source tree.

| Public file | Internal source path | SHA-256 of source | Bytes |
|---|---|---|---|
| `wyrd_evidence_core/predicate_semantics.py` | `C:\G1\tools\predicate_semantics.py` | `727bf9701c34236d42711c1dd7ccb33b82fe93510754417d04ef0437f89d871c` | 17,947 |
| `wyrd_evidence_core/writeback_validator.py` | `C:\G1\tools\writeback_validator.py` | `fa33dad42cdbaafeb31783d16aea5d1e5374ab85c33077773b814241af36c1f6` | 18,498 |
| `wyrd_evidence_core/outcome_taxonomy.py` | `C:\G1\tools\outcome_taxonomy.py` | `ff8823cfc281231e6837228a4121634b4c924d03bcfe1dadd29df4df63adf3d3` | 7,795 |
| `wyrd_evidence_core/registry_schema.py` | `C:\Projects\state_registry\schema.py` | `6507e21e1cfd6093c9a9c4aec7c511300feb154aff298de66616b76201693f8f` | 7,095 |
| `wyrd_evidence_core/registry.py` | `C:\Projects\state_registry\registry.py` | `a0f23135d5abb12d0a41780d68c463d00cc1b5ca3a964465c9ee08718cbec8fa` | 17,439 |

Verify the sources still hash as recorded:

```console
$ sha256sum /path/to/predicate_semantics.py
727bf9701c34236d42711c1dd7ccb33b82fe93510754417d04ef0437f89d871c
```

## The only edits made during extraction

Logic was not rewritten. Four mechanical changes:

1. **`writeback_validator.py`** — `import predicate_semantics as ps` became a
   relative import with a script fallback, so the module works both as a package
   member and as the standalone script it has always been.
2. **`registry.py`** — `from .schema import ...` became `from .registry_schema
   import ...`, since the module is no longer named `schema.py`.
3. **`registry.py`** — `WORKSPACE_ROOT` gained a comment and an
   `WYRD_EVIDENCE_CORE_WORKSPACE_ROOT` override. Upstream it was implicitly the
   parent of the installed package directory, which meant relative evidence
   references resolved against wherever the operator happened to keep the
   estate. Behaviour is unchanged when the variable is unset; it is now
   overridable.
4. **`__init__.py`** — new. Package metadata only. No logic.

Everything else is byte-identical to the source, which is why the upstream
self-check suites run here unmodified and are the behavioural specification.

## Provenance facts

**`NO_VCS_HISTORY_AT_SOURCE`** applies to the three modules from `C:\G1\tools`.
That directory is not under version control; there is no commit history, and
none has been fabricated. Their provenance is recorded here instead: source path,
SHA-256, extraction date, and operator attestation.

`C:\Projects\state_registry` *is* under version control — 16 commits, all
authored by `UrukuTelal <urukutelal@users.noreply.github.com>`.

## Operator attestation

> The modules `predicate_semantics.py`, `writeback_validator.py`, and
> `outcome_taxonomy.py` were produced under my direction as part of this
> architecture. Their lack of Git/VCS history is a provenance deficiency, not
> evidence that they are third-party code.

Attested by the operator (`UrukuTelal`) on 2026-09-30.

## Third-party material

None. Every extracted file imports only the Python standard library. No vendored
directories, no embedded copyright headers, no upstream third-party code. The
package declares no runtime dependencies.

## What was not extracted

| Not included | Why |
|---|---|
| `capability_inventory` | structurally requires the private 61-concept G1 graph |
| the G1 concept corpus | private estate data; never published |
| unrelated `C:\G1\tools` tooling | not required by anything here |
| `state_registry/contradiction.py`, `ci_check.py`, `precommit.py` | repository-internal tooling, not part of the registry surface |
| the rest of `state_registry` | Veritas requires only the registry/provenance surface |

## Licensing

**Apache-2.0**, per operator decision. See [`LICENSE`](../LICENSE).

No license file was added to, or modified in, any internal source repository as
part of this extraction. The internal trees remain unlicensed; the grant here
covers the extracted public work.
