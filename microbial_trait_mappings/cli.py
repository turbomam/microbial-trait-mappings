"""Click CLI commands for microbial-trait-mappings.

All commands are prefixed with ``mtm-`` when installed via pyproject.toml.
"""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from microbial_trait_mappings.normalize import normalize_text
from microbial_trait_mappings.validate_mappings import validate_directory
from microbial_trait_mappings.verify import (
    build_validation_schema,
    verify_curies_via_oak,
    write_validation_schema,
)

console = Console(stderr=True)


# ── mtm-normalize ───────────────────────────────────────────────────────────


@click.command("mtm-normalize")
@click.option("--input-dir", "-i", type=click.Path(exists=True), help="Data directory to check.")
@click.option("--text", "-t", type=str, help="Single text value to normalize.")
@click.option("--check", is_flag=True, help="Check normalization consistency (exit non-zero on mismatch).")
@click.option("--strict", is_flag=True, help="Treat warnings as errors.")
@click.option("--no-lowercase", is_flag=True, help="Disable lowercasing.")
@click.option("--no-strip-stereo", is_flag=True, help="Disable stereochemistry stripping.")
def normalize_cmd(
    input_dir: str | None,
    text: str | None,
    check: bool,
    strict: bool,
    no_lowercase: bool,
    no_strip_stereo: bool,
) -> None:
    """Normalize trait labels or check normalization consistency in TSV files."""
    if text:
        result = normalize_text(text, lowercase=not no_lowercase, strip_stereo=not no_strip_stereo)
        click.echo(result)
        return

    if not input_dir:
        click.echo("Error: provide --input-dir or --text", err=True)
        raise SystemExit(1)

    import pandas as pd

    data_path = Path(input_dir)
    errors = 0

    for tsv_path in sorted(data_path.rglob("*.tsv")):
        if "negative" in tsv_path.stem:
            continue
        try:
            df = pd.read_csv(tsv_path, sep="\t", dtype=str, keep_default_na=False)
        except Exception:
            continue
        if "subject_label" not in df.columns:
            continue

        for idx, row in df.iterrows():
            label = row["subject_label"].strip()
            if not label:
                continue

            expected = normalize_text(label, lowercase=not no_lowercase, strip_stereo=not no_strip_stereo)
            existing = row.get("subject_label_normalized", "").strip()

            if check and existing and existing != expected:
                console.print(
                    f"[red]MISMATCH[/red] {tsv_path.name}:{int(idx) + 2} "
                    f"label={label!r} expected={expected!r} got={existing!r}"
                )
                errors += 1

    if check:
        if errors:
            console.print(f"\n[red]{errors} normalization mismatches found.[/red]")
            raise SystemExit(1)
        else:
            console.print("[green]All normalizations consistent.[/green]")


# ── mtm-build-schema ────────────────────────────────────────────────────────


@click.command("mtm-build-schema")
@click.option("--input-dir", "-i", required=True, type=click.Path(exists=True), help="Data directory.")
@click.option("--output", "-o", required=True, type=click.Path(), help="Output YAML path.")
def build_schema_cmd(input_dir: str, output: str) -> None:
    """Generate a LinkML validation schema from mapping TSVs."""
    schema = build_validation_schema(Path(input_dir))
    write_validation_schema(schema, Path(output))
    console.print(f"[green]Schema written to {output}[/green]")


# ── mtm-verify ──────────────────────────────────────────────────────────────


@click.command("mtm-verify")
@click.option("--input-dir", "-i", required=True, type=click.Path(exists=True), help="Data directory.")
@click.option("--oak-config", "-c", required=True, type=click.Path(exists=True), help="OAK config YAML.")
def verify_cmd(input_dir: str, oak_config: str) -> None:
    """Verify all CURIEs in mapping TSVs against source ontologies via OAK."""
    report = verify_curies_via_oak(Path(input_dir), Path(oak_config))

    table = Table(title="CURIE Verification Results")
    table.add_column("CURIE", style="cyan")
    table.add_column("Expected Label")
    table.add_column("Actual Label")
    table.add_column("Status")
    table.add_column("Message")

    for r in report.results:
        style = {"ok": "green", "warning": "yellow", "error": "red"}.get(r.severity, "white")
        table.add_row(r.curie, r.expected_label, r.actual_label or "", f"[{style}]{r.status}[/{style}]", r.message)

    console.print(table)
    console.print(f"\nSummary: {report.summary}")

    if not report.ok:
        raise SystemExit(1)


# ── mtm-validate ────────────────────────────────────────────────────────────


@click.command("mtm-validate")
@click.option("--input-dir", "-i", required=True, type=click.Path(exists=True), help="Data directory.")
def validate_cmd(input_dir: str) -> None:
    """Validate mapping TSV column schemas."""
    report = validate_directory(Path(input_dir))

    for err in report.errors:
        style = "red" if err.severity == "error" else "yellow"
        loc = f"{err.file}"
        if err.row is not None:
            loc += f":{err.row}"
        if err.column:
            loc += f" [{err.column}]"
        console.print(f"[{style}]{err.severity.upper()}[/{style}] {loc}: {err.message}")

    if report.ok:
        console.print("[green]All TSV schemas valid.[/green]")
    else:
        error_count = sum(1 for e in report.errors if e.severity == "error")
        console.print(f"\n[red]{error_count} validation errors found.[/red]")
        raise SystemExit(1)


# ── mtm-audit ───────────────────────────────────────────────────────────────


@click.command("mtm-audit")
@click.option("--input-dir", "-i", required=True, type=click.Path(exists=True), help="Data directory.")
@click.option("--oak-config", "-c", required=True, type=click.Path(exists=True), help="OAK config YAML.")
@click.option("--output", "-o", type=click.Path(), default="generated/validation_schema.yaml", help="Schema output.")
def audit_cmd(input_dir: str, oak_config: str, output: str) -> None:
    """Full audit: validate schemas + check normalization + build schema + verify CURIEs."""
    data_path = Path(input_dir)
    has_errors = False

    # Step 1: Validate TSV schemas
    console.rule("[bold]Step 1: Validate TSV column schemas[/bold]")
    val_report = validate_directory(data_path)
    for err in val_report.errors:
        style = "red" if err.severity == "error" else "yellow"
        console.print(f"  [{style}]{err.severity.upper()}[/{style}] {err.file}: {err.message}")
    if val_report.ok:
        console.print("  [green]OK[/green]")
    else:
        has_errors = True

    # Step 2: Check normalization
    console.rule("[bold]Step 2: Normalization consistency[/bold]")
    import pandas as pd

    norm_errors = 0
    for tsv_path in sorted(data_path.rglob("*.tsv")):
        if "negative" in tsv_path.stem:
            continue
        try:
            df = pd.read_csv(tsv_path, sep="\t", dtype=str, keep_default_na=False)
        except Exception:
            continue
        if "subject_label" not in df.columns:
            continue
        for idx, row in df.iterrows():
            label = row["subject_label"].strip()
            if not label:
                continue
            expected = normalize_text(label)
            existing = row.get("subject_label_normalized", "").strip()
            if existing and existing != expected:
                console.print(f"  [red]MISMATCH[/red] {tsv_path.name}:{int(idx) + 2}")
                norm_errors += 1
    if norm_errors:
        has_errors = True
    else:
        console.print("  [green]OK[/green]")

    # Step 3: Build schema
    console.rule("[bold]Step 3: Build validation schema[/bold]")
    schema = build_validation_schema(data_path)
    write_validation_schema(schema, Path(output))
    console.print(f"  [green]Schema written to {output}[/green]")

    # Step 4: Verify CURIEs (only if there are mappings)
    console.rule("[bold]Step 4: Verify CURIEs via OAK[/bold]")
    import pandas as pd

    has_mappings = False
    for tsv_path in sorted(data_path.rglob("*.tsv")):
        if "negative" not in tsv_path.stem:
            try:
                df = pd.read_csv(tsv_path, sep="\t", dtype=str, keep_default_na=False)
                if not df.empty and "object_id" in df.columns and df["object_id"].str.strip().any():
                    has_mappings = True
                    break
            except Exception:
                pass

    if has_mappings:
        verify_report = verify_curies_via_oak(data_path, Path(oak_config))
        for r in verify_report.results:
            if r.severity != "ok":
                console.print(f"  [red]{r.status}[/red] {r.curie}: {r.message}")
        if verify_report.ok:
            console.print("  [green]OK[/green]")
        else:
            has_errors = True
    else:
        console.print("  [dim]No positive mappings to verify (empty data files).[/dim]")

    # Summary
    console.rule("[bold]Audit Summary[/bold]")
    if has_errors:
        console.print("[red]FAIL — audit found errors.[/red]")
        raise SystemExit(1)
    else:
        console.print("[green]PASS — all checks passed.[/green]")


# ── mtm-sri-normalize ───────────────────────────────────────────────────────


@click.command("mtm-sri-normalize")
@click.option("--curie", "-c", type=str, multiple=True, help="CURIE(s) to normalize.")
@click.option("--input-file", "-i", type=click.Path(exists=True), help="File with one CURIE per line.")
def sri_normalize_cmd(curie: tuple[str, ...], input_file: str | None) -> None:
    """Normalize CURIEs via the SRI Node Normalizer (for non-OBO prefixes)."""
    from microbial_trait_mappings.sri_normalize import normalize_curies

    curies = list(curie)
    if input_file:
        with open(input_file, encoding="utf-8") as f:
            curies.extend(line.strip() for line in f if line.strip())

    if not curies:
        click.echo("Error: provide --curie or --input-file", err=True)
        raise SystemExit(1)

    results = normalize_curies(curies)

    table = Table(title="SRI Node Normalizer Results")
    table.add_column("Input CURIE", style="cyan")
    table.add_column("Normalized CURIE")
    table.add_column("Label")
    table.add_column("Category")
    table.add_column("Found")

    for r in results:
        found_style = "green" if r.found else "red"
        table.add_row(
            r.input_curie,
            r.normalized_curie or "",
            r.label or "",
            r.category or "",
            f"[{found_style}]{r.found}[/{found_style}]",
        )

    console.print(table)
