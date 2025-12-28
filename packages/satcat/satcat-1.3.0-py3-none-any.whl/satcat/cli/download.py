from pathlib import Path

import typer

from satcat.cli.utils import cli_output_model
from satcat.sdk.client import Client

app = typer.Typer()


@app.command()
def ephemeris(
    resource_id: str,
    file_format: str = typer.Option(
        "OEM", "--file-format", "-f", help="One of OEM, NASA, HDF5, or ORIGINAL"
    ),
    output_file: Path = typer.Option(None, "--output-file", "-o"),
):
    """Download an Ephemeris by ID."""
    with Client() as client:
        file_content = client.screening.download_ephemeris(resource_id, file_format)
    if output_file is None:
        typer.echo(file_content.read())
    else:
        with open(output_file, "w+") as outf:
            outf.write(file_content.read())


@app.command()
def plan(
    scenario_id: str,
    tradespace_id: str,
    plan_id: str,
    file_name: str,
    file_format: str = typer.Option("opm", "--file-format", "-f"),
    output_file: Path = typer.Option(None, "--output-file", "-o"),
):
    """Download an Avoidance Maneuver Plan by ID."""
    with Client() as client:
        file_content = client.avoidance.download_maneuver_plan(
            scenario_id, tradespace_id, plan_id, file_format, file_name
        )
    if output_file is None:
        typer.echo(file_content.read())
    else:
        with open(output_file, "w+") as outf:
            outf.write(file_content.read())
