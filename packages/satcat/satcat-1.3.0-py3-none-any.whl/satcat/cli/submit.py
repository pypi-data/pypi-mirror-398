import typer
from rich.progress import Progress

from satcat.cli.utils import cli_output_model, screening_await_cli
from satcat.sdk.client import Client
from satcat.sdk.settings import OutputFormat, settings

app = typer.Typer()


@app.command()
def screening(
    resource_id: str,
    wait: bool = typer.Option(
        False,
        "--wait",
        "-w",
        help=(
            "Whether to wait for the screening to complete or return after creating and"
            " submitting the asynchronous screening job."
        ),
    ),
):
    """Submit a Screening by ID."""

    with Client() as client:
        screening = client.screening.get_screening(resource_id)
        screening = client.screening.submit_screening(screening)
        screening = screening_await_cli(client, screening)
        cli_output_model(screening)


@app.command()
def propagation(
    resource_id: str,
    wait: bool = typer.Option(
        False,
        "--wait",
        "-w",
        help=(
            "Whether to wait for the screening to complete or return after creating and"
            " submitting the asynchronous screening job."
        ),
    ),
):
    """Submit a Propagation by ID."""
    with Client() as client:
        propagation = client.propagation.get_propagation(resource_id)
        resource = client.propagation.submit_propagation(propagation)
        if wait:
            resource = client.propagation.await_propagation_completion(propagation)
        cli_output_model(resource)
