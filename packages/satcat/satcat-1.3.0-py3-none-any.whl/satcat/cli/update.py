import json
from typing import List, Optional

import typer
from typer import Abort

from satcat.cli.utils import (
    cli_output,
    cli_output_model,
    validate_model_from_input,
)

from satcat.sdk.client import Client

app = typer.Typer()

