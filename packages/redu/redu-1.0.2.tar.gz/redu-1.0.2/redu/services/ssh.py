import click
import requests
import subprocess
from pathlib import Path
from .utils import requires_token, CONFIG_DIR

# ------------------ SSH ------------------
@click.command("ssh")
@click.argument("server_name")
@requires_token
@click.pass_context
def ssh_server(ctx, server_name):
    """SSH into a server by name."""
    access_token = ctx.obj["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # 1. Fetch all servers
    list_url = "https://console.redu.cloud/api/cloud/compute/instances/list"
    try:
        resp = requests.get(list_url, headers=headers)
        resp.raise_for_status()
        instances = resp.json() if isinstance(resp.json(), list) else resp.json().get("instances", [])
    except requests.RequestException as e:
        click.secho(f"Error fetching instances: {e}", fg="red", bold=True)
        return

    # 2. Find server
    server = next((inst for inst in instances if inst.get("name") == server_name), None)
    if not server:
        click.secho(f"Server '{server_name}' not found.", fg="red", bold=True)
        return

    # 3. Pick IP
    chosen_ip = None
    for net_addrs in server.get("addresses", {}).values():
        for addr_info in net_addrs:
            if addr_info.get("version") == 4:
                ip_addr = addr_info.get("addr")
                if ip_addr.startswith("203.0.113."):
                    chosen_ip = ip_addr
                    break
        if chosen_ip:
            break

    if not chosen_ip:
        for net_addrs in server.get("addresses", {}).values():
            for addr_info in net_addrs:
                if addr_info.get("version") == 4:
                    chosen_ip = addr_info.get("addr")
                    break
            if chosen_ip:
                break

    if not chosen_ip:
        click.secho("No IP address found for this server.", fg="red", bold=True)
        return

    # 4. Get port mapping
    ports_url = "https://console.redu.cloud/api/cloud/nginx/used-ports"
    try:
        port_resp = requests.get(ports_url, headers=headers)
        port_resp.raise_for_status()
        routes = port_resp.json().get("routes", [])
    except requests.RequestException as e:
        click.secho(f"Error fetching port mapping: {e}", fg="red", bold=True)
        return

    mapping = next((r for r in routes if r.get("targetIp") == chosen_ip), None)
    if not mapping or not mapping.get("port"):
        click.secho(f"No port mapping found for IP {chosen_ip}", fg="red", bold=True)
        return

    port = mapping["port"]

    # 5. SSH directly
    private_key_file = CONFIG_DIR / "id_rsa_redu_cli"
    if not private_key_file.exists():
        click.secho(f"Private key not found: {private_key_file}", fg="red", bold=True)
        return


    subprocess.run([
        "ssh-keyscan",
        "-p", str(port),
        "redu.cloud"
    ], stdout=open(str(CONFIG_DIR / "known_hosts"), "a"))

    ssh_cmd = [
        "ssh",
        "-i", str(private_key_file),
        "-p", str(port),
        "-o", f"UserKnownHostsFile={CONFIG_DIR / 'known_hosts'}",
        "ubuntu@redu.cloud"
    ]

    click.secho(f"Connecting to {server_name} ({chosen_ip}:{port})...", fg="green", bold=True)
    try:
        subprocess.run(ssh_cmd)
    except FileNotFoundError:
        click.secho("SSH command not found. Please ensure OpenSSH is installed.", fg="red", bold=True)
