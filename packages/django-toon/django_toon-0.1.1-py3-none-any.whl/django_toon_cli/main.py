import os
import tomllib
import typer
import requests
import json

from toon.encoder import encode
from toon.decoder import decode

from typing import Annotated


app = typer.Typer()


@app.command()
def version():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    pyproject_path = os.path.abspath(
        os.path.join(base_dir, "..", "..", "pyproject.toml")
    )

    with open(pyproject_path, "rb") as f:
        pyproject = tomllib.load(f)

    print(pyproject["project"]["version"])


@app.command()
def get(url: str):
    headers = {
        "Accept": "application/x-toon"
    }

    response = requests.get(url, headers=headers)
    content_type = response.headers.get("Content-Type", "")

    if content_type.startswith("application/x-toon"):
        typer.echo("Toon response received")
        typer.echo(decode(response.content))
    else:
        typer.echo("Server does not send Toon")
        typer.echo(f"Content-Type: {content_type}")


@app.command()
def post(
    url: str,
    payload: Annotated[str, typer.Option(help="JSON payload for POST request")] = '{"key": "value"}',
):
    data = json.loads(payload)

    headers = {
        "Content-Type": "application/x-toon",
        "Accept": "application/x-toon",
    }

    response = requests.post(
        url,
        data=encode(data),
        headers=headers,
    )

    typer.echo(f"Status: {response.status_code}")

    if response.headers.get("Content-Type", "").startswith("application/x-toon"):
        typer.echo(decode(response.content))
    else:
        typer.echo("Server does not accept Toon")


def main():
    app()
