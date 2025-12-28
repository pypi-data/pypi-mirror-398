import typer

from satcat.cli.utils import cli_output, cli_output_model
from satcat.sdk.client import Client

app = typer.Typer()


# Screening


@app.command()
def ephemeris(resource_id: str):
    """Retrieve an Ephemeris by ID."""
    with Client() as client:
        resource = client.screening.get_ephemeris(resource_id)
        cli_output_model(resource)


@app.command()
def screening(resource_id: str):
    """Retrieve a Screening by ID."""
    with Client() as client:
        resource = client.screening.get_screening(resource_id)
        cli_output_model(resource)


@app.command()
def catalog(resource_id: str):
    """Retrieve a Catalog by ID."""
    with Client() as client:
        resource = client.screening.get_catalog(resource_id)
        cli_output_model(resource)


@app.command()
def conjunction_ccsds(screening_id: str, conjunction_id: str):
    """Retrieve a single CCSDS formatted Conjunction by Screening ID."""
    with Client() as client:
        resource = client.screening.get_conjunction_ccsds(screening_id, conjunction_id)
        cli_output(resource)


# Propagation


@app.command()
def propagation(resource_id: str):
    """Retrieve a Propagation by ID."""
    with Client() as client:
        resource = client.propagation.get_propagation(resource_id)
        cli_output_model(resource)

