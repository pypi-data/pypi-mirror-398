from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import List, Optional

import shutil
import typer

from satcat.cli.utils import (
    cli_output_model,
    screening_await_cli,
    validate_model_from_input,
)

from satcat.sdk.client import Client
from satcat.sdk.propagation import models as prop_models
from satcat.sdk.screening import models as screening_models

app = typer.Typer()

# Screening


@app.command()
def ephemeris(
    file: Path,
    file_format: str = typer.Argument(...),
    norad_id: Optional[int] = None,
    comments: Optional[str] = None,
    hbr_m: Optional[float] = None,
    context: Optional[screening_models.EphemerisContext] = None,
    designation: Optional[screening_models.EphemerisDesignation] = None,
):

    with Client() as client:
        resource = client.screening.create_ephemeris(
            file,
            file_format=file_format,
            filename=file.name,
            norad_id=norad_id,
            comments=comments,
            hbr_m=hbr_m,
            context=context,
            designation=designation,
        )
        cli_output_model(resource)


@app.command()
def ephemeris_from_maneuver_plan(
    scenario_id: str = typer.Option(None, "--scenario-id", "--sid"),
    tradespace_id: str = typer.Option(None, "--tradespace-id", "--tid"),
    plan_id: str = typer.Option(None, "--plan-id", "--pid"),
    designation: Optional[screening_models.EphemerisDesignation] = typer.Option(
        None, "--designation", "--d"
    ),
):

    with Client() as client:
        resource = client.avoidance.create_ephemeris_from_maneuver_plan(
            scenario_id, tradespace_id, plan_id, designation
        )
        cli_output_model(resource)


@app.command()
def screening(
    primary_ephemeris_file: Optional[Path] = typer.Option(
        None, "--primary-ephemeris-file", "--pef"
    ),
    primary_ephemeris_format: str = typer.Option(
        "AUTOMATIC", "--primary-ephemeris-format", "--pfmt"
    ),
    primary_norad_id: Optional[int] = typer.Option(
        None, "--primary-norad-cat-id", "--pid"
    ),
    primary_ephemeris_ids: Optional[List[str]] = None,
    secondary_ephemeris_ids: Optional[List[str]] = None,
    primary_opm_file: Optional[Path] = typer.Option(None, "--opm"),
    catalog_id: Optional[str] = None,
    threshold_radius_km: float = 15.0,
    threshold_radius_active_km: Optional[float] = None,
    threshold_radius_manned_km: Optional[float] = None,
    threshold_radius_debris_km: Optional[float] = None,
    default_secondary_hbr_m: float = 5.0,
    propagation_start_time: Optional[datetime] = None,
    propagation_duration: Optional[float] = None,
    propagation_timestep: Optional[float] = None,
    launch_window_start: Optional[datetime] = None,
    launch_window_end: Optional[datetime] = None,
    launch_window_cadence_s: Optional[float] = None,
    type: screening_models.ScreeningType = screening_models.ScreeningType.ON_ORBIT,
    auto_archive: bool = False,
    include_primary_vs_primary: bool = False,
    title: Optional[str] = None,
    notes: Optional[str] = None,
    submit: bool = typer.Option(False, "--submit", "-s"),
    use_best_catalog: bool = True,
    use_ephemeris_repository: bool = False,
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

    if wait and not submit:
        # Cannot wait without submitting
        submit = True

    with Client() as client:
        if primary_ephemeris_ids is None:
            primary_ephemeris_ids = []
        if secondary_ephemeris_ids is None:
            secondary_ephemeris_ids = []
        primaries = [
            screening_models.Screenable(ephemeris_id=i) for i in primary_ephemeris_ids
        ]
        secondaries = [
            screening_models.Screenable(ephemeris_id=i) for i in secondary_ephemeris_ids
        ]

        if primary_opm_file is not None:
            with open(primary_opm_file) as opm_f:
                propagation = client.propagation.create_propagation(opm_file=opm_f)
            primaries.append(screening_models.Screenable(propagation_id=propagation.id))

        catalog = None

        if use_best_catalog:
            catalog = client.screening.get_latest_catalog()
            secondaries.append(screening_models.Screenable(catalog_id=catalog.id))

        elif catalog_id is not None:
            catalog = client.screening.get_catalog(catalog_id)

        if use_ephemeris_repository:
            secondaries.append(
                screening_models.Screenable(
                    ephemeris_group=screening_models.EphemerisGroup.OPERATOR_REPOSITORY
                )
            )

        if primary_ephemeris_file:
            primary_ephemeris = client.screening.create_ephemeris(
                primary_ephemeris_file,
                file_format=primary_ephemeris_format,
                norad_id=primary_norad_id,
            )
            primaries.append(
                screening_models.Screenable(ephemeris_id=primary_ephemeris.id)
            )
        elif primary_norad_id:
            if catalog:
                primaries.append(
                    screening_models.Screenable(
                        catalog_id=catalog.id, norad_id=primary_norad_id
                    )
                )
            else:
                raise ValueError(
                    "primary_norad_id can only be used if"
                    "primary_ephemeris_file or catalog_id is set"
                )

        if title is None:
            now = datetime.now()
            title = f"{now.strftime('%Y-J%j')} - SDK Screening"

        config = screening_models.ScreeningConfiguration(
            threshold_radius_km=threshold_radius_km,
            threshold_radius_active_km=threshold_radius_active_km,
            threshold_radius_manned_km=threshold_radius_manned_km,
            threshold_radius_debris_km=threshold_radius_debris_km,
            default_secondary_hbr_m=default_secondary_hbr_m,
            submit=submit,
            notes=notes,
            propagation_duration=propagation_duration,
            propagation_start_time=propagation_start_time,
            propagation_timestep=propagation_timestep,
            auto_archive=auto_archive,
            title=title,
            include_primary_vs_primary=include_primary_vs_primary,
            screening_type=type.upper(),
            launch_window_start=launch_window_start,
            launch_window_end=launch_window_end,
            launch_window_cadence_s=launch_window_cadence_s,
        )

        screening = client.screening.create_screening(
            config,
            primaries=primaries,
            submit=submit,
            secondaries=secondaries,
        )

        screening = client.screening.get_screening(screening.id)

        if wait:
            screening = screening_await_cli(client, screening)

        cli_output_model(screening)


@app.command()
def propagation(
    opm_file: Optional[Path] = typer.Option(None, "--opm-file", "--opm"),
    submit: bool = typer.Option(False, "--submit", "-s"),
    target_duration_s: Optional[float] = typer.Option(None, "--duration-sec", "-d"),
    timestep_s: Optional[float] = typer.Option(None, "--timestep-sec", "-t"),
    purpose: Optional[str] = typer.Option(None),
    wait: bool = typer.Option(
        False,
        "--wait",
        "-w",
        help=(
            "Whether to wait for the propagation to complete or return after creating"
            " and submitting the asynchronous propagation job."
        ),
    ),
):
    configuration = prop_models.PropagationConfiguration(
        timestep=timestep_s, target_duration=target_duration_s, purpose=purpose
    )

    opm_file_content = StringIO()
    if opm_file is not None:
        with open(opm_file) as f:
            shutil.copyfileobj(f, opm_file_content)
            opm_file_content.seek(0)
    else:
        opm_file_content = None

    with Client() as client:
        propagation = client.propagation.create_propagation(
            configuration, opm_file=opm_file_content, submit=submit
        )

        if wait:
            propagation = client.propagation.await_propagation_completion(propagation)

    cli_output_model(propagation)
