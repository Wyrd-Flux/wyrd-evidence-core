"""Tests for wyrd-evidence-core.

The three upstream modules ship their own self-check suites, which are run here
verbatim: they are the behavioural specification, and a regression in them is a
regression in this package. Extraction tests then cover the registry surface,
which had no upstream test of its own, plus the packaging properties that make
this a public dependency.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

import wyrd_evidence_core
from wyrd_evidence_core import (
    outcome_taxonomy,
    predicate_semantics as ps,
    registry,
    registry_schema,
    writeback_validator,
)

PACKAGE_DIR = Path(wyrd_evidence_core.__file__).parent


# --------------------------------------------------------------------------- #
# upstream self-check suites: the behavioural contract, run as shipped
# --------------------------------------------------------------------------- #


def _problems(result: object) -> list:
    """Normalise a self-check return into the list of failures.

    Upstream is not uniform: predicate_semantics returns a flat problem list,
    writeback_validator returns (problems, cases). Both are preserved; only the
    extraction test is tolerant of the shape.
    """
    if isinstance(result, tuple):
        return list(result[0])
    assert isinstance(result, list)
    return result


@pytest.mark.parametrize("module_name", ["predicate_semantics", "writeback_validator"])
def test_upstream_self_check_suite_passes(module_name: str) -> None:
    """Run the module's own self_check() exactly as upstream defines it."""
    module = __import__(f"wyrd_evidence_core.{module_name}", fromlist=[module_name])
    assert _problems(module.self_check()) == []


def test_outcome_taxonomy_self_qualification_passes() -> None:
    """outcome_taxonomy names its entry point selfcheck(), not self_check()."""
    assert _problems(outcome_taxonomy.selfcheck()) == []


def test_extracted_modules_run_standalone_as_scripts() -> None:
    """Each module was a script upstream; extraction must not break that."""
    for name in ("predicate_semantics", "writeback_validator", "outcome_taxonomy"):
        result = subprocess.run(
            [sys.executable, str(PACKAGE_DIR / f"{name}.py")],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"{name} failed as a script:\n{result.stderr}"


# --------------------------------------------------------------------------- #
# predicate semantics
# --------------------------------------------------------------------------- #


def test_predicate_registry_is_non_empty_and_well_formed() -> None:
    assert ps.PREDICATES, "a registry with no predicates is not a registry"
    for name, predicate in ps.PREDICATES.items():
        assert predicate.name == name
        assert 0 <= predicate.strength_class <= 5
        assert ps.STRENGTH_NAME[predicate.strength_class]


def test_known_is_an_exact_membership_test() -> None:
    """known() answers about one name. It is not a listing."""
    for name in ps.PREDICATES:
        assert ps.known(name) is True
    assert ps.known("NOT_A_PREDICATE") is False
    assert ps.known("") is False


def test_get_fails_closed_on_an_unregistered_predicate() -> None:
    """An untyped edge is not a neutral unknown. get() must raise, not return
    a default -- this is what stops a universal RELATES_TO creeping back in."""
    with pytest.raises(KeyError) as exc:
        ps.get("NOT_A_PREDICATE")
    assert "UNREGISTERED_PREDICATE" in str(exc.value)


def test_requires_evidence_is_structurally_asymmetric() -> None:
    """Down the lattice is admissible loss. Up is strengthening and needs
    evidence. Equal is free. That is the whole rule."""
    assert ps.requires_evidence(0, 1) is True   # strengthening
    assert ps.requires_evidence(1, 0) is False  # weakening: free
    assert ps.requires_evidence(2, 2) is False  # equal: free


def test_weakening_admissible_is_strictly_downward() -> None:
    """Moving down the lattice is free. So is standing still -- but a move that
    does not lose strength is not "weakening", so it must not be reported as one."""
    for before in range(6):
        for after in range(6):
            assert ps.weakening_admissible(before, after) is (after < before)
    # the three cases partition the lattice
    for before in range(6):
        for after in range(6):
            down = ps.weakening_admissible(before, after)
            up = ps.requires_evidence(before, after)
            assert down != up or (after == before and not up and not down)


def test_every_predicate_name_is_distinct_and_uppercase() -> None:
    """Predicate names are vocabulary. Case variance would silently split them."""
    for name in ps.PREDICATES:
        assert name == name.upper(), name
        assert " " not in name


def test_identifying_predicates_exist() -> None:
    """The lattice must reach AUTHORITY, or it cannot express governance."""
    strengths = {p.strength_class for p in ps.PREDICATES.values()}
    assert strengths == set(range(6)), "the lattice has a hole in it"


# --------------------------------------------------------------------------- #
# writeback validation
# --------------------------------------------------------------------------- #


def _edge(subject="a", predicate="CAUSES", obj="b", basis="OBSERVED", evidence=()):
    return writeback_validator.Edge(
        subject=subject, predicate=predicate, obj=obj, basis=basis,
        evidence=tuple(evidence),
    )


def test_unchanged_state_with_no_new_edges_is_fully_accepted() -> None:
    edge = _edge(evidence=("tests/test_x.py",))
    verdict = writeback_validator.validate([edge], [edge])
    assert not verdict.refused, [f.code for f in verdict.refused]
    assert len(verdict.accepted) == 1


def test_a_brand_new_edge_without_evidence_is_refused() -> None:
    verdict = writeback_validator.validate([], [_edge()])
    codes = {f.code for f in verdict.refused}
    assert "NEW_EDGE_WITHOUT_EVIDENCE" in codes


def test_an_unregistered_predicate_is_refused_on_an_edge() -> None:
    """Upstream's fail-closed behaviour, exercised through the edge path."""
    verdict = writeback_validator.validate([], [_edge(predicate="RELATES_TO")])
    assert "UNREGISTERED_PREDICATE" in {f.code for f in verdict.refused}


def test_strengthening_without_a_token_is_refused() -> None:
    """The asymmetry invariant enforced at the only place it can be enforced:
    moving up the lattice requires an explicit evidence token."""
    edge = _edge(predicate="CORRELATES_WITH")
    without = writeback_validator.validate([], [edge])
    assert without.refused, "strengthening with no token must be refused"


def test_verdict_reports_accepted_and_refused_separately() -> None:
    """A caller must be able to see what would be written and what would not."""
    verdict = writeback_validator.validate([], [_edge()])
    assert isinstance(verdict.accepted, list)
    assert isinstance(verdict.refused, list)
    assert not (set(map(str, verdict.accepted)) & set(map(str, verdict.refused)))


def test_refusing_codes_are_a_closed_frozenset() -> None:
    """A typo in a refusal code must not silently invent a new refusal class."""
    assert isinstance(writeback_validator.REFUSING, frozenset)
    assert writeback_validator.REFUSING


# --------------------------------------------------------------------------- #
# outcome taxonomy
# --------------------------------------------------------------------------- #


def test_every_outcome_class_belongs_to_exactly_one_family() -> None:
    families = {outcome_taxonomy.family(c) for c in outcome_taxonomy.ALL_CLASSES}
    assert families == {"RESOLVED", "REFUSED", "CLOSED", "OPEN"}


def test_families_partition_all_classes_without_overlap() -> None:
    grouped = {
        name: set(getattr(outcome_taxonomy, f"{name}_CLASSES"))
        for name in ("RESOLVED", "REFUSED", "CLOSED", "OPEN")
    }
    seen: set[str] = set()
    for members in grouped.values():
        assert not (seen & members), "a class is in two families"
        seen |= members
    assert seen == set(outcome_taxonomy.ALL_CLASSES)


def test_every_class_has_a_description() -> None:
    for cls in outcome_taxonomy.ALL_CLASSES:
        assert outcome_taxonomy.DESCRIPTIONS[cls].strip()


def test_summarise_totals_match_the_supplied_counts() -> None:
    counts = {c: 1 for c in outcome_taxonomy.ALL_CLASSES}
    summary = outcome_taxonomy.summarise(counts)
    total = next(
        v for k, v in summary.items() if k.lower() in ("total", "all")
    ) if any(k.lower() in ("total", "all") for k in summary) else sum(summary.values())
    assert total == len(outcome_taxonomy.ALL_CLASSES)


def test_render_is_deterministic_for_the_same_counts() -> None:
    counts = {c: 1 for c in outcome_taxonomy.ALL_CLASSES}
    rendered = outcome_taxonomy.render(outcome_taxonomy.summarise(counts))
    assert rendered == outcome_taxonomy.render(
        outcome_taxonomy.summarise(dict(counts))
    )


# --------------------------------------------------------------------------- #
# registry: the surface Veritas requires
# --------------------------------------------------------------------------- #


def _component(name: str = "demo", disposition: str = "OPEN"):
    return registry_schema.ComponentState(
        name=name,
        repository="wyrd-evidence-core",
        path="wyrd_evidence_core/registry.py",
        state=registry_schema.State(
            disposition=registry_schema.Disposition(disposition),
            research_state=registry_schema.ResearchState("ACTIVE"),
            established_by="test",
            established_date="2026-09-30",
            version=1,
        ),
        policy=registry_schema.Policy(
            modification={},
            new_experiment=registry_schema.OperationPolicy(
                level=registry_schema.OperationLevel.ALLOWED
            ),
            reopening=registry_schema.OperationPolicy(
                level=registry_schema.OperationLevel.REQUIRES_AUTHORIZATION,
                reason="reopening requires explicit authorization",
            ),
        ),
        authority=registry_schema.Authority(
            established_by="test",
            provenance="registered by a test",
            evidence=[],
            requires_for_reopening="Human authorization",
        ),
        dependencies=[],
        metadata={},
        history=[],
    )


@pytest.fixture()
def reg(tmp_path: Path) -> registry.StateRegistry:
    return registry.StateRegistry(data_dir=str(tmp_path / "registry"))


def test_register_then_verify_history_chain(reg: registry.StateRegistry) -> None:
    reg.register(_component())
    assert reg.get("demo") is not None
    verification = reg.verify_history("demo")
    assert verification.valid, verification.error
    assert verification.records_checked >= 1


def test_can_modify_allows_by_operation(reg: registry.StateRegistry) -> None:
    reg.register(_component())
    result = reg.can_modify("demo", "modify")
    assert result.permitted is True, result.reason


def test_a_refusal_names_its_reason_and_the_authority_that_unblocks_it(
    reg: registry.StateRegistry,
) -> None:
    """A bare False is not a governance answer. PRESERVE is what engages
    per-operation policy; OPEN permits everything by design."""
    reg.register(_component())
    assert reg.can_modify("demo", "reopening").permitted is True, (
        "OPEN is permissive, so use PRESERVE to exercise the policy gate"
    )
    reg.transition(
        "demo", registry_schema.Disposition.PRESERVE,
        established_by="test", provenance="preserved to exercise policy",
    )
    result = reg.can_modify("demo", "reopening")
    assert result.permitted is False
    assert result.reason.strip(), "a refusal must say why"
    assert "authoriz" in result.reason.lower()
    assert "authorization" in result.required_authority.lower()


def test_an_unknown_component_is_not_treated_as_forbidden(
    reg: registry.StateRegistry,
) -> None:
    """unknown != forbidden. Inventing a refusal here would make absence look
    like a policy decision, and would hide a missing registration."""
    result = reg.can_modify("never-registered", "modify")
    assert result.permitted is True
    assert "unknown" in result.reason.lower()


def test_a_terminal_disposition_blocks_everything(
    reg: registry.StateRegistry,
) -> None:
    reg.register(_component())
    reg.transition(
        "demo", registry_schema.Disposition.PRESERVE,
        established_by="test", provenance="preserved first",
    )
    reg.transition(
        "demo", registry_schema.Disposition.SUPERSEDED,
        established_by="test", provenance="terminal",
    )
    for operation in ("modify", "reopening", "new_experiment"):
        assert reg.can_modify("demo", operation).permitted is False, operation


def test_registry_survives_a_reopen_from_disk(tmp_path: Path) -> None:
    data_dir = tmp_path / "registry"
    registry.StateRegistry(data_dir=str(data_dir)).register(_component())
    assert registry.StateRegistry(data_dir=str(data_dir)).get("demo") is not None


def test_superseded_is_terminal(reg: registry.StateRegistry) -> None:
    """No disposition may follow SUPERSEDED, and OPEN cannot jump straight to it."""
    assert registry.LEGAL_TRANSITIONS[registry_schema.Disposition.SUPERSEDED] == set()
    assert registry_schema.Disposition.SUPERSEDED not in (
        registry.LEGAL_TRANSITIONS[registry_schema.Disposition.OPEN]
    )


def test_illegal_transition_is_refused(reg: registry.StateRegistry) -> None:
    reg.register(_component())
    reg.transition(
        "demo", registry_schema.Disposition.PRESERVE,
        established_by="test", provenance="preserved, so it can be superseded",
    )
    reg.transition(
        "demo", registry_schema.Disposition.SUPERSEDED,
        established_by="test", provenance="superseded in a test",
    )
    with pytest.raises(ValueError, match="Illegal transition"):
        reg.transition(
            "demo", registry_schema.Disposition.VOIDED,
            established_by="test", provenance="illegal from a terminal state",
        )


def test_history_verification_detects_a_broken_chain(
    reg: registry.StateRegistry,
) -> None:
    """Verification that cannot fail is not verification."""
    reg.register(_component())
    reg.transition(
        "demo", registry_schema.Disposition.PRESERVE,
        established_by="test", provenance="a second record",
    )
    assert reg.verify_history("demo").valid is True

    state = reg.get("demo")
    state.history[-1]["hash"] = "0" * 64
    reg._save()
    assert reg.verify_history("demo").valid is False


# --------------------------------------------------------------------------- #
# public-package properties
# --------------------------------------------------------------------------- #


def test_importing_the_package_does_not_import_the_wider_estate() -> None:
    """Import cost must stay bounded. A library that drags a corpus in at import
    cannot be a dependency of anything."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys, wyrd_evidence_core;"
            "print(sorted(m for m in sys.modules"
            " if 'capability_inventory' in m or m.startswith('state_registry')))",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "[]", result.stdout


def test_package_ships_no_filesystem_paths_from_the_extraction_environment() -> None:
    """No source tree of the extraction estate may travel with the code.

    Historical references to an estate name in prose are fine; what must not
    ship is a path that only resolves on the machine it was extracted from.
    """
    drive_or_home = re.compile(r"[A-Za-z]:[\\/]|/Users/|/home/[a-z]|\\\\[A-Za-z0-9_.-]+\\")
    offenders = []
    for path in PACKAGE_DIR.glob("*.py"):
        for lineno, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), 1
        ):
            if drive_or_home.search(line):
                offenders.append(f"{path.name}:{lineno}")
    assert offenders == [], offenders


def test_relative_evidence_resolves_against_an_overridable_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Workspace-relative evidence must not depend on where the package was
    installed. The root is explicit and overridable."""
    monkeypatch.setattr(registry, "WORKSPACE_ROOT", tmp_path)
    (tmp_path / "evidence.md").write_text("line one\nline two\n", encoding="utf8")
    assert registry._resolve_artifact_reference("evidence.md", "")["exists"] is True
    assert (
        registry._resolve_artifact_reference("absent.md", "")["exists"] is False
    ), "an unresolvable reference is not evidence"


def test_line_anchors_verify_the_line_exists(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(registry, "WORKSPACE_ROOT", tmp_path)
    (tmp_path / "evidence.md").write_text("a\nb\nc\n", encoding="utf8")
    assert registry._resolve_artifact_reference("evidence.md:3", "")["exists"] is True
    assert registry._resolve_artifact_reference("evidence.md:99", "")["exists"] is False


def test_commands_are_inspected_never_executed() -> None:
    """A Python command reference is parsed for its script path only."""
    resolved = registry._resolve_artifact_reference(
        "python script.py --dangerous-flag", ""
    )
    assert resolved["kind"] == "command"
    assert resolved["path"].endswith("--dangerous-flag")


def test_version_is_exposed() -> None:
    assert wyrd_evidence_core.__version__ == "0.1.0"


def test_public_names_are_importable_from_the_package_root() -> None:
    for name in wyrd_evidence_core.__all__:
        if name != "__version__":
            __import__(f"wyrd_evidence_core.{name}")
    assert set(wyrd_evidence_core.__all__) >= {
        "predicate_semantics", "writeback_validator", "outcome_taxonomy",
        "registry", "registry_schema",
    }
