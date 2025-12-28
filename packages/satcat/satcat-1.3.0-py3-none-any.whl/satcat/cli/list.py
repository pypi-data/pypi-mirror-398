from typing import Optional

import typer

from satcat.cli import utils
from satcat.sdk.client import Client

app = typer.Typer()
count_option = typer.Option(10, "-n", "--count")

# Screening


@app.command()
def ephemerides(count: Optional[int] = count_option, catalog_id: Optional[str] = None):
    with Client() as client:
        if catalog_id:
            resources = client.screening.list_catalog_ephemerides(
                catalog_id, count=count, sort_field='usable_time_end'
            )
            utils.cli_output_list(resources)
        else:
            resources = client.screening.list_ephemerides(count=count)
            utils.cli_output_list(resources)

@app.command()
def events(count: Optional[int] = count_option):
    with Client() as client:
        resources = client.events.list_events(count=count)
        utils.cli_output_list(resources)


@app.command()
def screenings(count: Optional[int] = count_option, show_archived: bool = False):
    with Client() as client:
        resources = client.screening.list_screenings(
            count=count, show_archived=show_archived
        )
        utils.cli_output_list(resources)


@app.command()
def catalogs(count: Optional[int] = count_option, latest: bool = False):
    with Client() as client:
        resources = client.screening.list_catalogs(count=count, latest=latest)
        utils.cli_output_list(resources)


@app.command()
def conjunctions(screening_id: Optional[str]=None, count: Optional[int] = count_option):
    with Client() as client:
        if screening_id is None:
            resources = client.events.list_conjunctions(count=count)
        else:
            resources = client.screening.list_conjunctions(
                screening_id=screening_id, count=count
            )
        utils.cli_output_list(resources)


@app.command()
def screening_primaries(screening_id: str, count: Optional[int] = count_option):
    with Client() as client:
        resources = client.screening.list_screening_primaries(
            screening_id=screening_id, count=count
        )
        utils.cli_output_list(resources)


@app.command()
def screening_secondaries(screening_id: str, count: Optional[int] = count_option):
    with Client() as client:
        resources = client.screening.list_screening_secondaries(
            screening_id=screening_id, count=count
        )
        utils.cli_output_list(resources)


@app.command()
def ephemeris_formats():
    with Client() as client:
        resources = client.screening.list_ephemeris_formats()
        utils.cli_output(resources)


@app.command()
def conjunctions_ccsds(resource_id: str, count: Optional[int] = count_option):
    with Client() as client:
        resources = client.screening.list_conjunctions_ccsds(resource_id, count)
        utils.cli_output(resources)
