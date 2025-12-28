import click
import requests
from pathlib import Path
from .utils import requires_token, CONFIG_DIR
deploy_script_local = Path(__file__).resolve().parent.parent / "deploy_scripts" / "deploy-next.sh"


# ------------------ Setup ------------------
@click.command("setup")
@click.argument("server_name")
@click.argument("local_path", type=click.Path(exists=True))
@requires_token
@click.pass_context
def setup_instance(ctx, server_name, local_path):
    """Copy a project folder to a server over SSH and deploy it."""
    import shutil
    import subprocess

    access_token = ctx.obj["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # 1. Fetch servers
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

    # 5. Copy folder via SCP
    private_key_file = CONFIG_DIR / "id_rsa_redu_cli"
    if not private_key_file.exists():
        click.secho(f"Private key not found: {private_key_file}", fg="red", bold=True)
        return

    # # Copy the project folder
    # scp_cmd = [
    #     "scp",
    #     "-i", str(private_key_file),
    #     "-P", str(port),
    #     "-r",
    #     str(local_path),
    #     f"ubuntu@redu.cloud:~/"
    # ]

    # click.secho(f"Copying {local_path} to {server_name} ({chosen_ip}:{port})...", fg="green", bold=True)
    # try:
    #     subprocess.run(scp_cmd, check=True)
    #     click.secho("Project copy completed successfully!", fg="green", bold=True)
    # except subprocess.CalledProcessError as e:
    #     click.secho(f"Error copying project files: {e}", fg="red", bold=True)
    #     return
    # except FileNotFoundError:
    #     click.secho("SCP command not found. Please ensure OpenSSH is installed.", fg="red", bold=True)
    #     return

    # Copy deploy-next.sh separately
    # deploy_script_local = Path("deploy-next.sh")
    # if not deploy_script_local.exists():
    #     click.secho(f"deploy-next.sh not found locally: {deploy_script_local}", fg="red", bold=True)
    #     return

    if not deploy_script_local.exists():
        click.secho(f"deploy-nodejs.sh not found: {deploy_script_local}", fg="red", bold=True)
        return

    # subprocess.run([
    #     "ssh-keyscan",
    #     "-p", str(port),
    #     "redu.cloud"
    # ], stdout=open(str(CONFIG_DIR / "known_hosts"), "a"))


    with open(CONFIG_DIR / "known_hosts", "a") as known_hosts:
        subprocess.run(
            ["ssh-keyscan", "-p", str(port), "redu.cloud"],
            stdout=known_hosts,
            stderr=subprocess.DEVNULL
        )

    scp_deploy_cmd = [
        "scp",
        "-i", str(private_key_file),
        "-P", str(port),
        "-o", f"UserKnownHostsFile={CONFIG_DIR / 'known_hosts'}",
        str(deploy_script_local),
        f"ubuntu@redu.cloud:~/"
    ]

    click.secho(f"Copying deploy-nodejs.sh to {server_name}...", fg="green", bold=True)
    try:
        subprocess.run(scp_deploy_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        click.secho("deploy-next.sh copy completed successfully!", fg="green", bold=True)
    except subprocess.CalledProcessError as e:
        click.secho(f"Error copying deploy-next.sh: {e}", fg="red", bold=True)
        return

    # 6. Run deploy-next.sh on remote server via SSH
    deploy_script_path = "~/deploy-next.sh"
    ssh_cmd = [
        "ssh",
        "-i", str(private_key_file),
        "-p", str(port),
        "-o", f"UserKnownHostsFile={CONFIG_DIR / 'known_hosts'}",
        f"ubuntu@redu.cloud",
        f"bash -c 'chmod +x {deploy_script_path} && {deploy_script_path}'"
    ]

    # click.secho(f"Running deploy script on {server_name} ({chosen_ip})...", fg="green", bold=True)
    click.secho(f"Running deploy script on {server_name}...", fg="green", bold=True)
    try:
        subprocess.run(ssh_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        click.secho("Deployment script executed successfully!", fg="green", bold=True)
    except subprocess.CalledProcessError as e:
        click.secho("")
        # click.secho(f"Error running deploy script: {e}", fg="red", bold=True)
    except FileNotFoundError:
        # click.secho("SSH command not found. Please ensure OpenSSH is installed.", fg="red", bold=True)
        click.secho("")
