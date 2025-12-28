import click
import requests
import json
from .utils import requires_token

# ------------------ Image ------------------
@click.group()
def image():
    """Image related commands"""
    pass

@image.command("list")
@requires_token
@click.pass_context
def image_list(ctx):
    access_token = ctx.obj["access_token"]
    url = "https://console.redu.cloud/api/cloud/image/images/list"
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            click.secho(f"Failed to fetch images: {resp.status_code} {resp.text}", fg="red", bold=True)
            return

        data = resp.json()
        images = data if isinstance(data, list) else data.get("images", [])

        if not images:
            click.secho("No images found.", fg="yellow")
            return

        click.secho("Available images:", fg="green", bold=True)
        for img in images:
            click.secho(f"- {img.get('name', 'unknown')} ({img.get('id', 'no-id')})", fg="yellow")

    except requests.RequestException as e:
        click.secho(f"Error fetching images: {e}", fg="red", bold=True)
