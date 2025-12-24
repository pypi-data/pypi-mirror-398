from __future__ import annotations

"""Typer-based command-line interface for praevisio.

Commands map to application services. Run `python -m praevisio --help` to see
available commands.
"""

import json
import stat
from pathlib import Path
from typing import Optional
import typer

from abductio_core.application.use_cases.replay_session import replay_session

from ..application.engine import PraevisioEngine
from ..application.evaluation_service import EvaluationService
from ..application.installation_service import InstallationService
from ..infrastructure.filesystem import LocalFileSystemService
from ..infrastructure.config import YamlConfigLoader


app = typer.Typer(add_completion=False, no_args_is_help=True)


def build_evaluation_service() -> EvaluationService:
    return EvaluationService()


def build_engine() -> PraevisioEngine:
    loader = YamlConfigLoader()
    fs = LocalFileSystemService()
    return PraevisioEngine(loader, fs, evaluation_service=build_evaluation_service())


def load_configuration(engine: PraevisioEngine, path: str):
    try:
        return engine.load_config(path)
    except FileNotFoundError:
        typer.echo(f"[praevisio] Config not found: {path}")
        raise typer.Exit(code=2)


@app.command()
def install(config_path: str = ".praevisio.yaml") -> None:
    fs = LocalFileSystemService()
    installer = InstallationService(fs, config_path)
    path = installer.install()
    typer.echo(f"Installed default config at {path}")


@app.command("pre-commit")
def pre_commit(
    path: str = typer.Argument(".", help="Path to the repository/commit to evaluate."),
    threshold: Optional[float] = typer.Option(
        None, "--threshold", help="Credence threshold required to pass the pre-commit gate."
    ),
    config_path: str = typer.Option(
        ".praevisio.yaml", "--config", help="Path to Praevisio configuration file."
    ),
) -> None:
    """Local governance gate to block commits when credence is below threshold."""
    engine = build_engine()
    config = load_configuration(engine, config_path)
    evaluation = config.evaluation
    gate = engine.pre_commit_gate(path, evaluation, threshold_override=threshold)
    result = gate.evaluation
    if result.verdict == "error":
        typer.echo("[praevisio][pre-commit] ❌ Evaluation error. Commit aborted.")
        raise typer.Exit(code=1)
    if gate.should_fail:
        typer.echo("[praevisio][pre-commit] ❌ Critical promises not satisfied. Commit aborted.")
        raise typer.Exit(code=1)
    typer.echo("[praevisio][pre-commit] ✅ All critical promises satisfied.")


@app.command("evaluate-commit")
def evaluate_commit_cmd(
    path: str,
    json_output: bool = typer.Option(
        False,
        "--json-output",
        "--json",
        help="Print structured JSON output instead of plain text.",
    ),
    threshold: Optional[float] = typer.Option(
        None, "--threshold", help="Credence threshold required to pass the evaluation."
    ),
    config_path: str = typer.Option(
        ".praevisio.yaml", "--config", help="Path to Praevisio configuration file."
    ),
) -> None:
    """Evaluate a single commit directory and print credence and verdict."""
    engine = build_engine()
    config = load_configuration(engine, config_path)
    evaluation = config.evaluation
    evaluation = engine.apply_threshold(evaluation, threshold, evaluation.severity)
    result = engine.evaluate(path, evaluation)
    if json_output:
        typer.echo(json.dumps({
            "credence": result.credence,
            "verdict": result.verdict,
            "details": result.details,
        }, indent=2))
    else:
        credence_display = "n/a" if result.credence is None else f"{result.credence:.3f}"
        typer.echo(f"Credence: {credence_display}")
        typer.echo(f"Verdict: {result.verdict}")


@app.command("ci-gate")
def ci_gate(
    path: str = typer.Argument(".", help="Path to the target repository/commit."),
    severity: Optional[str] = typer.Option(
        None, "--severity", help="Severity level to enforce."
    ),
    fail_on_violation: bool = typer.Option(
        False, "--fail-on-violation", help="Exit with error on violations."
    ),
    output: str = typer.Option(
        "logs/ci-gate-report.json",
        "--output",
        help="Where to write JSON report of evaluated promises.",
    ),
    threshold: Optional[float] = typer.Option(
        None, "--threshold", help="Credence threshold for passing high-severity promises."
    ),
    config_path: str = typer.Option(
        ".praevisio.yaml", "--config", help="Path to Praevisio configuration file."
    ),
) -> None:
    """Run Praevisio as a CI governance gate."""
    engine = build_engine()
    config = load_configuration(engine, config_path)
    evaluation = config.evaluation
    gate = engine.ci_gate(
        path,
        evaluation,
        severity=severity,
        threshold_override=threshold,
        fail_on_violation=fail_on_violation,
    )
    report = [gate.report_entry]

    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    if gate.should_fail:
        typer.echo("[praevisio][ci-gate] ❌ GATE FAILED")
        raise typer.Exit(code=1)

    typer.echo("[praevisio][ci-gate] ✅ GATE PASSED")


@app.command("install-hooks")
def install_hooks(
    git_dir: str = typer.Option(
        ".", "--git-dir", help="Root of the git repository where hooks should be installed."
    )
) -> None:
    """Install a git pre-commit hook that runs `praevisio pre-commit`."""
    repo_root = Path(git_dir).resolve()
    hooks_dir = repo_root / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    hook_path = hooks_dir / "pre-commit"
    script = """#!/usr/bin/env sh
# Praevisio governance pre-commit hook

praevisio pre-commit
STATUS=$?
if [ "$STATUS" -ne 0 ]; then
  echo "[praevisio][pre-commit] ❌ Critical promises not satisfied. Commit aborted."
  exit "$STATUS"
fi
exit 0
"""
    hook_path.write_text(script, encoding="utf-8")
    mode = hook_path.stat().st_mode
    hook_path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    typer.echo(f"Installed pre-commit hook at {hook_path}")


@app.command("replay-audit")
def replay_audit(
    audit_path: Optional[str] = typer.Argument(
        None, help="Path to an Abductio audit JSON file."
    ),
    latest: bool = typer.Option(
        False, "--latest", help="Replay the most recent audit under the runs directory."
    ),
    runs_dir: str = typer.Option(
        ".praevisio/runs", "--runs-dir", help="Base directory for run artifacts."
    ),
    json_output: bool = typer.Option(
        False,
        "--json-output",
        "--json",
        help="Print structured JSON output instead of plain text.",
    ),
) -> None:
    """Replay an Abductio audit trace and print the reconstructed ledger."""
    audit_file = Path(audit_path) if audit_path else None
    if latest:
        audit_file = _latest_audit_file(Path(runs_dir))
        if audit_file is None:
            typer.echo("[praevisio] No audits found.")
            raise typer.Exit(code=2)
    if audit_file is None:
        typer.echo("[praevisio] audit_path is required unless --latest is used.")
        raise typer.Exit(code=2)
    audit = json.loads(audit_file.read_text(encoding="utf-8"))
    result = replay_session(audit)
    if json_output:
        typer.echo(json.dumps(result.to_dict_view(), indent=2))
        return
    typer.echo(f"Stop reason: {result.stop_reason}")
    typer.echo(f"Ledger: {result.ledger}")
    roots = result.roots or {}
    for rid, root in roots.items():
        k_root = root.get("k_root")
        if k_root is not None:
            typer.echo(f"Root {rid} k_root: {k_root}")


@app.command("show-run")
def show_run(
    run_id: str = typer.Argument(..., help="Run identifier under the runs directory."),
    runs_dir: str = typer.Option(
        ".praevisio/runs", "--runs-dir", help="Base directory for run artifacts."
    ),
) -> None:
    """Show a summary of a stored run (manifest + audit paths)."""
    run_root = Path(runs_dir) / run_id
    manifest_path = run_root / "manifest.json"
    audit_path = run_root / "audit.json"
    if not manifest_path.exists():
        typer.echo(f"[praevisio] manifest not found: {manifest_path}")
        raise typer.Exit(code=2)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    typer.echo(f"Run: {run_id}")
    metadata = manifest.get("metadata", {})
    if metadata:
        typer.echo(f"Timestamp: {metadata.get('timestamp_utc')}")
        typer.echo(f"Praevisio: {metadata.get('praevisio_version')}")
        typer.echo(f"Abductio: {metadata.get('abductio_core_version')}")
    typer.echo(f"Manifest: {manifest_path}")
    if audit_path.exists():
        typer.echo(f"Audit: {audit_path}")
    artifacts = manifest.get("artifacts", [])
    if artifacts:
        typer.echo("Artifacts:")
        for item in artifacts:
            kind = item.get("kind")
            path = item.get("path")
            sha = item.get("sha256")
            typer.echo(f"- {kind}: {path} ({sha})")


def _latest_audit_file(runs_dir: Path) -> Path | None:
    if not runs_dir.exists():
        return None
    candidates = []
    for entry in runs_dir.iterdir():
        if not entry.is_dir():
            continue
        audit_path = entry / "audit.json"
        if audit_path.exists():
            candidates.append(audit_path)
    if not candidates:
        return None
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def main() -> None:
    app()
