import click
import requests
import json
from .utils import requires_token

# ------------------ Network ------------------
@click.group()
def network():
    """Network related commands"""
    pass

@network.command("list")
@requires_token
@click.pass_context
def network_list(ctx):
    access_token = ctx.obj["access_token"]
    url = "https://console.redu.cloud/api/cloud/network/private_networks"
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            click.secho(f"Failed to fetch networks: {resp.status_code} {resp.text}", fg="red", bold=True)
            return

        data = resp.json()
        if isinstance(data, list):
            networks = data
        elif isinstance(data, dict):
            networks = data.get("networks", [data])
        else:
            networks = []

        if not networks:
            click.secho("No networks found.", fg="yellow")
            return

        click.secho("Available networks:", fg="green", bold=True)
        for net in networks:
            click.secho(f"- {net.get('name', 'unknown')} ({net.get('id', 'no-id')})", fg="yellow")

    except requests.RequestException as e:
        click.secho(f"Error fetching networks: {e}", fg="red", bold=True)



@network.group("security-group")
def security_group():
    """Security group related commands"""
    pass



@security_group.command("list")
@requires_token
@click.pass_context
def security_group_list(ctx):
    access_token = ctx.obj["access_token"]
    url = "https://console.redu.cloud/api/cloud/network/security_groups/list"
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            click.secho(f"Failed to fetch security groups: {resp.status_code} {resp.text}", fg="red", bold=True)
            return

        data = resp.json()
        if isinstance(data, list):
            groups = data
        elif isinstance(data, dict):
            groups = data.get("security_groups", [data])
        else:
            groups = []

        if not groups:
            click.secho("No security groups found.", fg="yellow")
            return

        click.secho("Available security groups:", fg="green", bold=True)
        for sg in groups:
            click.secho(f"- {sg.get('name', 'unknown')} ({sg.get('id', 'no-id')}) - {sg.get('description', '')}", fg="yellow")

    except requests.RequestException as e:
        click.secho(f"Error fetching security groups: {e}", fg="red", bold=True)
