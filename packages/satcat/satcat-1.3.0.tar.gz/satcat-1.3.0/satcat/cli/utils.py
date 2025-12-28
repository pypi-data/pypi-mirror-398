import inspect
import json
import sys
import rich
import typer

from enum import Enum
from typing import TYPE_CHECKING, Callable, List, Optional, TextIO, Type, Union
try:
    from pydantic.v1 import BaseModel
except ImportError:
    from pydantic import BaseModel

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from satcat.sdk.propagation import models as propagation_models
from satcat.sdk.screening import models as screening_models

if TYPE_CHECKING:
    from satcat.sdk.client import Client

from satcat.sdk.settings import OutputFormat, settings


class FetchingSpinner:
    global_enable = True

    def __init__(self, message: str = "Fetching data..."):
        self.message = message

    def __enter__(self):
        self.progress = None
        if (
            settings.cli.show_progress
            and settings.cli.is_cli
            and FetchingSpinner.global_enable
        ):
            self.progress = Progress(
                SpinnerColumn(),
                TextColumn(f"[progress.description]{self.message}"),
                transient=True,
            )
            self.progress.__enter__()
            self.progress.add_task(description=self.message, total=None)

        return self

    def __exit__(self, *exc_args):
        if self.progress is not None:
            self.progress.__exit__(*exc_args)


def screening_await_cli(client: "Client", screening: screening_models.Screening):
    if settings.cli.output_format == OutputFormat.RICH and settings.cli.show_progress:
        FetchingSpinner.global_enable = False
        gen = client.screening.await_screening_completion_percent_generator(screening)

        with Progress() as progress:
            task = progress.add_task("Running screening...", total=100)
            try:
                while True:
                    pct = next(gen)
                    progress.update(task, completed=pct)
            except StopIteration as stop:
                screening = stop.value
        FetchingSpinner.global_enable = True
    else:
        screening = client.screening.await_screening_completion(screening)
    return screening


def attribute_seek(base: BaseModel, path: str):
    try:
        for key in path.split("."):
            base = getattr(base, key)
        if isinstance(base, Enum):
            base = base.value
        return base
    except AttributeError:
        return None
    except TypeError:
        return None


def rich_hyperlink_field(path: str, url_format: str) -> str:
    class _hyperlink:
        def __call__(self, base: BaseModel):
            value = attribute_seek(base, path)
            url = url_format.format(value)
            return f"[link={url}]{value}[/link]"

        @property
        def field_name(self):
            return path

    return _hyperlink()


def resolve_field(
    base: BaseModel, operator: Union[str, Callable[[BaseModel], str]]
) -> str:
    if isinstance(operator, str):
        value = attribute_seek(base, operator)
    else:
        value = operator(base)
    if value is None:
        return "N/A"
    return str(value)


def resolve_field_name(field):
    def fmt(n):
        return n.replace("_", " ").replace(".", " ").title()

    try:
        return fmt(field)
    except AttributeError:
        return fmt(field.field_name)


def cli_output(
    d: Union[BaseModel, dict],
    out: TextIO = sys.stdout,
    indent: int = 2,
):
    if settings.cli.output_format == OutputFormat.JSON:
        rich.print(f"{json.dumps(d, indent=indent)}", file=out)
    elif settings.cli.output_format == OutputFormat.RICH:
        rich.print(d, file=out)


def cli_output_list(
    d: List[BaseModel],
    out: TextIO = sys.stdout,
    indent=2,
    fields: Optional[List[str]] = None,
):
    ds = [json.loads(i.json()) for i in d]

    if fields is None:
        try:
            fields = FIELDS[type(d[0])]
        except KeyError:
            try:
                fields = ds[0].keys()
            except IndexError:
                fields = []

    if settings.cli.output_format == OutputFormat.JSON:
        rich.print(json.dumps(ds, indent=indent), file=out)
    elif settings.cli.output_format == OutputFormat.RICH:
        console = Console(file=out)

        if len(d) == 0:
            rich.print("[bold red]No results found.[/bold red]", file=out)
        else:
            fields_pretty = [resolve_field_name(f) for f in fields]
            table = Table(*fields_pretty)
            # Formatting for UUIDs
            table.columns[0].width = 36
            for item in d:
                table.add_row(*[resolve_field(item, f) for f in fields])
            console.print(table)


def cli_output_model(
    model: BaseModel,
    out: TextIO = sys.stdout,
    indent=2,
    exclude_none=True,
    fields: Optional[List[str]] = None,
):
    if fields is None:
        try:
            fields = FIELDS[type(model)]
        except KeyError:
            try:
                fields = model.__fields__.keys()
            except IndexError:
                fields = []

    if settings.cli.output_format == OutputFormat.JSON:
        rich.print(model.json(indent=indent, exclude_none=exclude_none), file=out)
    elif settings.cli.output_format == OutputFormat.RICH:
        console = Console(file=out)

        fields_pretty = [resolve_field_name(f) for f in fields]
        table = Table(*fields_pretty)
        table.add_row(*[resolve_field(model, f) for f in fields])
        console.print(table)


def display_class_keys_and_values(cls_or_module):
    help_text = f"\n{cls_or_module.__name__} Keys and Allowed Values:\n\n"

    if inspect.isclass(cls_or_module):
        if hasattr(cls_or_module, "__annotations__"):
            for attr_name, attr_value in cls_or_module.__annotations__.items():
                default_value = getattr(cls_or_module, attr_name, None)
                if default_value:
                    help_text += (
                        f"  {attr_name}: {attr_value} (Default: {default_value})\n\n"
                    )
                else:
                    help_text += f"  {attr_name}: {attr_value}\n\n"
        else:
            help_text += "  (No type annotations found)\n\n"
    elif inspect.ismodule(cls_or_module):
        for name, obj in inspect.getmembers(cls_or_module):
            if inspect.isclass(obj):
                help_text += f"\nClass {name}:\n"
                help_text += display_class_keys_and_values(obj)
    else:
        help_text += "Not a class or module.\n"

    return help_text


def validate_model_from_input(
    ctx: typer.Context, model: Type[BaseModel], flag_prefix: str
):
    validation_data = {}

    for arg_idx, extra_arg in enumerate(ctx.args):
        if extra_arg.startswith(flag_prefix):
            key_value_pair = extra_arg[len(flag_prefix) :].replace("-", "_")

            if "=" in key_value_pair:
                key, value = key_value_pair.split("=", 1)
                validation_data[key] = value
            else:
                if arg_idx + 1 < len(ctx.args):
                    validation_data[key_value_pair] = ctx.args[arg_idx + 1]

    try:
        validated_model = model.parse_obj(validation_data)
        return validated_model
    except Exception:
        raise ValueError(f"Invalid values provided for {model}")


FIELDS = {
    screening_models.Ephemeris: [
        "id",
        "norad_id",
        "solution_time",
        "has_covariance",
        "notes",
        "hbr_m",
        "context",
        "designation",
    ],
    screening_models.Screening: [
        rich_hyperlink_field("id", settings.satcat_base_url + "screenings/{}"),
        "title",
        "status",
        "created_at",
        "conjunctions_count",
        "primaries_count",
        "secondaries_count",
        "percent_complete",
        "coverage_level",
    ],
    screening_models.Conjunction: [
        "primary.norad_id",
        "secondary.norad_id",
        "tca",
        "miss_distance_km",
        "collision_probability",
    ],
    screening_models.Screenable: [
        "ephemeris.id",
        "ephemeris.norad_id",
        "catalog_id",
        "norad_id",
        "coverage_level",
    ],
    screening_models.Catalog: [
        "id",
        "catalog_type",
        "epoch",
        "ready",
        "archived",
    ],
    propagation_models.Propagation: [
        "id",
        "status",
        "created_at",
        "start_time",
        "end_time",
        "target_duration",
        "timestep",
        "ephemeris_id",
    ],
}
