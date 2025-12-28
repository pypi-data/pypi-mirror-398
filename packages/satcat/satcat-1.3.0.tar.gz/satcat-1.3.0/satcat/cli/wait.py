import typer
from rich.progress import Progress

from satcat.cli.utils import cli_output_model, screening_await_cli
from satcat.sdk.client import Client
from satcat.sdk.settings import OutputFormat, settings

app = typer.Typer()


@app.command()
def screening(resource_id: str, timeout: int = 3600, poll_interval: int = 5):
    """Await completion of a Screening."""
    with Client() as client:
        screening = client.screening.get_screening(resource_id)
        screening = screening_await_cli(client, screening)
        cli_output_model(screening)


@app.command()
def propagation(resource_id: str, timeout: int = 3600, poll_interval: int = 5):
    """Await completion of a Propagation."""
    with Client() as client:
        propagation = client.propagation.get_propagation(resource_id)
        resource = client.propagation.await_propagation_completion(
            propagation, timeout=timeout, poll_interval=poll_interval
        )
        cli_output_model(resource)
