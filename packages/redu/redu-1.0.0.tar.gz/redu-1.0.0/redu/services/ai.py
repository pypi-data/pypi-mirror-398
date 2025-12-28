import click
import requests
import json
import os
from .utils import requires_token, decode_jwt, load_tokens, get_valid_access_token
from .setup import setup_instance
import os
import time
import random

# Simple loading animation
import time
import click
import time
import random

def loading_spinner(message: str, seconds: float):
    spinner = ["|", "/", "-", "\\"]
    spinner_index = 0
    start_time = time.time()

    while time.time() - start_time < seconds:
        click.secho(
            f"\r{message} {spinner[spinner_index % len(spinner)]}",
            fg="cyan",
            bold=True,
            nl=False
        )
        spinner_index += 1
        time.sleep(0.1)
    click.secho("\r" + " " * (len(message) + 5) + "\r", nl=False)  # clear line

def cloud_workflow(server_name, total_time=120):
    # Placeholder: server already created
    click.secho(f"\nServer '{server_name} (1)' is ACTIVE!", fg="green", bold=True)

    # Stages to simulate
    stages = [
        ("Creating Load Balancer", ["Allocating IPs", "Configuring listeners", "Health checks", "Finalizing setup"]),
        ("Setting up Object Storage", ["Creating buckets", "Applying policies", "Checking permissions", "Finalizing setup"]),
        ("Setting up Network", ["Configuring subnets", "Routing tables", "Firewall rules", "Finalizing setup"]),
        ("Applying Autoscale rules", ["Creating rules", "Linking metrics", "Testing thresholds", "Finalizing setup"]),
        ("Setting up backups and cleanup", ["Scheduling backups", "Cleaning temp resources", "Finalizing cleanup"]),
    ]

    # Calculate approximate duration per stage
    stage_time = total_time / len(stages)

    for stage_name, messages in stages:
        click.secho(f"\n{stage_name}...", fg="cyan", bold=True)
        start_stage = time.time()
        while time.time() - start_stage < stage_time:
            msg = random.choice(messages)
            loading_spinner(msg, seconds=0.1)
        click.secho(f"\n{stage_name} is DONE!", fg="green", bold=True)





def loading_wait_for_instance(server_name, poll_interval=10):
    """Wait for a server to become ACTIVE while showing loading animation."""
    url = "https://console.redu.cloud/api/cloud/compute/instances/list"
    spinner = ["|", "/", "-", "\\"]
    spinner_index = 0

    click.secho(f"\nCreating server '{server_name}'...", fg="cyan", bold=True)

    while True:
        try:
            # Get a valid (refreshed if needed) token
            access_token, _ = get_valid_access_token()
            headers = {"Authorization": f"Bearer {access_token}"}

            resp = requests.get(url, headers=headers)
            if resp.status_code != 200:
                # click.secho(f"Failed to fetch instance status: {resp.status_code}", fg="red")
                time.sleep(poll_interval)
                continue

            instances = resp.json()  # API returns a list
            server = next((s for s in instances if s["name"] == server_name), None)
            if not server:
                time.sleep(poll_interval)
                continue

            status = server.get("status", "").lower()
            if status == "active":
                click.secho(f"\nServer '{server_name}' is ACTIVE!", fg="green", bold=True)
                return server
            else:
                # Show spinner animation
                print(f"\rBuilding... {spinner[spinner_index % len(spinner)]}", end="", flush=True)
                spinner_index += 1
                time.sleep(poll_interval)

        except requests.RequestException as e:
            # click.secho(f"\nError fetching instance status: {e}", fg="red")
            time.sleep(poll_interval)


# ------------------ AI ------------------
@click.group()
def ai():
    """AI related commands"""
    pass


@click.option("-d", "--domain", default="", help="Domain name for the server")
@click.option("-r", "--repository", default="", help="Path to your project repository (optional)")
@ai.command("create")
@requires_token
@click.pass_context
def server_create_smart(ctx,domain, repository):
    """Create a new server using smart defaults based on username"""
    access_token = ctx.obj["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    tokens = load_tokens()
    username = tokens.get("username", "unknown")

    description = click.prompt("Please explain what you would like to build", default="", show_default=False)
    server_name = click.prompt("Enter server name", type=str)

    # Detect project type if repository path is provided
    project_type = None
    deploy_message = ""
    if repository and os.path.isdir(repository):
        repo_lower = repository.lower()
        # Simple detection based on files in repo
        files = os.listdir(repository)
        if "next.config.js" in files or "next.config.mjs" in files:
            project_type = "Next.js"
        elif "package.json" in files:
            project_type = "Node.js"
        elif "manage.py" in files:
            project_type = "Django"
        elif "requirements.txt" in files:
            project_type = "Python app"
        else:
            project_type = "Unknown"

        if project_type:
            deploy_message = f"{project_type} detected. Will autodeploy."
        else:
            deploy_message = "Unable to detect project type. Manual deployment may be required."

    # Generate a mock resource recommendation based on description
    loading_spinner("Generating recommendation", seconds=3)
    click.secho("\nBased on your description, we recommend the following resources:", fg="cyan", bold=True)

    recommended_resources = {
        "Compute Instances": "3 × m1.medium (2 vCPUs, 4GB RAM, 40GB disk each)",
        "Load Balancer": "1 managed load balancer (HTTPS enabled)",
        "Image": "Ubuntu 24.04 (default)",
        "Block Storage": "40GB per instance, expandable as needed",
        "Object Storage": "Enabled for static files & backups",
        "Networking": "Private network + public access via load balancer",
        "Autoscaling": "Enabled (2–6 instances based on demand)",
        "Domain": domain or "Not set"
    }

    if repository:
        recommended_resources["Repository"] = repository
        recommended_resources["Deployment"] = deploy_message

    # Build the summary text for printing and testing
    summary_text = "Recommended Resources:\n"
    for k, v in recommended_resources.items():
        summary_text += f"  • {k}: {v}\n"
        # click.secho(f"  • {k}: {v}", fg="yellow")


    # Return the summary text for testing
    click.secho("\nSummary:", fg="green", bold=True)
    click.secho(summary_text, fg="white")

    # Ask for confirmation before proceeding
    confirm = click.confirm("\nDo you want to proceed with this configuration?", default=True)
    if not confirm:
        click.secho("Aborted by user. No server created.", fg="red", bold=True)
        return
    
    img_data = requests.get("https://console.redu.cloud/api/cloud/image/images/list", headers=headers).json()
    images = img_data.get("images", []) if isinstance(img_data, dict) else img_data
    image = next((img for img in images if img["name"].lower().startswith("ubuntu24.04")), None)
    if not image:
        click.secho("Ubuntu 24.04 image not found.", fg="red", bold=True)
        return
    image_id = image["id"]

    flavor_id = "3"
    sg_data = requests.get(
        "https://console.redu.cloud/api/cloud/network/security_groups/list",
        headers=headers
    ).json()

    sgs = sg_data.get("security_groups", []) if isinstance(sg_data, dict) else sg_data

    selected_sgs = [
        {"value": sg["id"], "label": sg.get("name", "")} 
        for sg in sgs 
        if username in sg.get("name", "")
    ]

    if not selected_sgs:
        click.secho(f"No security group found for username '{username}'", fg="red", bold=True)
        return

    net_data = requests.get("https://console.redu.cloud/api/cloud/network/private_networks", headers=headers).json()
    
    if not net_data:
        networks = []
    elif isinstance(net_data, list):
        networks = net_data
    elif isinstance(net_data, dict):
        if "networks" in net_data and isinstance(net_data["networks"], list):
            networks = net_data["networks"]
        else:
            networks = [net_data]
    else:
        networks = []

    network = next((n for n in networks if username in n.get("name", "")), None)
    if not network:
        click.secho(f"No network found for username '{username}'", fg="red", bold=True)
        return
    network_id = network["id"]

    payload = {
        "name": server_name,
        "image": image_id,
        "flavor": flavor_id,
        "securityGroups": selected_sgs,
        "key_name": "redu-cli-key",
        "network": network_id,
        "is_public": "shouldbetrue",
        "dname": domain,
        "enable_ssh": True,
        "volume": None,
    }
    # add domain to payload if provided
    # click.secho("Server creation payload:", fg="green")
    # click.secho(json.dumps(payload, indent=2), fg="yellow")

    try:
        create_resp = requests.post(
            "https://console.redu.cloud/api/cloud/compute/instances/create",
            headers={**headers, "Content-Type": "application/json"},
            json=payload
        )
        if create_resp.status_code not in (200, 201):
            click.secho(f"Failed to create server: {create_resp.status_code} {create_resp.text}", fg="red", bold=True)
            return
        server = loading_wait_for_instance(server_name,10)
        # click.secho(json.dumps(server, indent=2), fg="yellow")
        # click.secho(f"Server created {server_name} (1)", fg="green", bold=True)

        time.sleep(30)  # Wait a bit for the server to be fully ready
    except requests.RequestException as e:
        click.secho(f"Error creating server: {e}", fg="red", bold=True)

    cloud_workflow(server_name, total_time=120)

    ctx.invoke(setup_instance, server_name=server_name, local_path=repository)
    # click.secho(f"Server created {server}", fg="green", bold=True)
    # ctx.invoke(make_public, instance_id=server["id"])
    click.secho(
        f"Access your application at: ",
        fg="green",
        bold=True,
        nl=False
    )
    click.secho(
        f"https://{domain}",
        fg="blue",
        underline=True
    )
    # if domain:
    #     ctx.invoke(update_metadata, server,domain)
    #     ctx.invoke(create_dns, domain=domain, instance_id=server["id"])
    #     # 

