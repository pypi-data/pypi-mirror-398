from urllib.parse import urljoin

import typer

from satcat import __app_name__, __version__
from satcat.cli.create import app as create_app
from satcat.cli.delete import app as delete_app
from satcat.cli.download import app as download_app
from satcat.cli.get import app as get_app
from satcat.cli.list import app as list_app
from satcat.cli.submit import app as submit_app
from satcat.cli.update import app as update_app
from satcat.cli.wait import app as await_app
from satcat.sdk.client import Client
from satcat.sdk.settings import OutputFormat, settings

VERSION = __version__
SERVICE_NAME = __app_name__

app = typer.Typer()
app.add_typer(await_app, name="await")
app.add_typer(create_app, name="create")
app.add_typer(delete_app, name="delete")
app.add_typer(download_app, name="download")
app.add_typer(get_app, name="get")
app.add_typer(list_app, name="list")
app.add_typer(submit_app, name="submit")
app.add_typer(update_app, name="update")


@app.command()
def version():
    typer.echo(f"{SERVICE_NAME} version {VERSION}")


@app.command()
def health_api():
    with Client() as client:
        res = client.request(urljoin(settings.satcat_rest_api_url, "health"))
    typer.echo(res.text)


@app.callback()
def main(
    output: OutputFormat = typer.Option(None, "-o", "--output"),
    no_progress: bool = typer.Option(False, "--no-progress"),
):
    settings.cli.is_cli = True
    if output is not None:
        settings.cli.output_format = output

    settings.cli.show_progress = not no_progress


if __name__ == "__main__":
    app()
