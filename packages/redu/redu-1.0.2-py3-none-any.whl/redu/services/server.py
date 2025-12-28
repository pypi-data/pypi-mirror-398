import click
import requests
import json
from .utils import requires_token, decode_jwt, load_tokens


# ------------------ Server ------------------
@click.group()
def server():
    """Server related commands"""
    pass

@server.command("list")
@requires_token
@click.pass_context
def server_list(ctx):
    access_token = ctx.obj["access_token"]
    url = "https://console.redu.cloud/api/cloud/compute/instances/list"
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            click.secho(f"Failed to fetch instances: {resp.status_code} {resp.text}", fg="red", bold=True)
            return

        data = resp.json()
        instances = data if isinstance(data, list) else data.get("instances", [])
        click.secho(json.dumps(instances, indent=2), fg="yellow")
        if not instances:
            click.secho("No instances found.", fg="yellow")
            return

        click.echo("Instances:")
        for inst in instances:
            click.echo(f"- {inst.get('name', 'unknown')} ({inst.get('id', 'no-id')}): status={inst.get('status', 'unknown')}")

    except requests.RequestException as e:
        click.secho(f"")
        # click.secho(f"Error fetching instances: {e}", fg="red", bold=True)


@server.command("create")
@requires_token
@click.pass_context
def server_create(ctx):
    """Create a new server interactively"""
    access_token = ctx.obj["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    def fetch_json(url):
        try:
            resp = requests.get(url, headers=headers)
            if resp.status_code != 200:
                click.secho(f"Failed to fetch from {url}: {resp.status_code} {resp.text}", fg="red", bold=True)
                return None
            try:
                return resp.json()
            except ValueError:
                click.secho(f"Invalid JSON from {url}: {resp.text}", fg="red", bold=True)
                return None
        except requests.RequestException as e:
            click.secho(f"Request error: {e}", fg="red", bold=True)
            return None

    server_name = click.prompt("Enter server name", type=str)

    img_data = fetch_json("https://console.redu.cloud/api/cloud/image/images/list")
    if not img_data:
        return
    images = img_data.get("images", []) if isinstance(img_data, dict) else img_data
    if not images:
        click.secho("No images available.", fg="red", bold=True)
        return

    img_choices = {str(i+1): img for i, img in enumerate(images)}
    click.secho("Available images:", fg="green")
    for idx, img in img_choices.items():
        click.secho(f"{idx}) {img['name']}", fg="yellow")
    img_idx = click.prompt("Select image number", type=click.Choice(list(img_choices.keys())))
    image_id = img_choices[img_idx]["id"]

    flavor_data = fetch_json("https://console.redu.cloud/api/cloud/compute/instances/flavors")
    if not flavor_data:
        return
    flavors = flavor_data.get("flavors", []) if isinstance(flavor_data, dict) else flavor_data
    if not flavors:
        click.secho("No flavors available.", fg="red", bold=True)
        return

    flavor_choices = {str(i+1): f for i, f in enumerate(flavors)}
    click.secho("Available flavors:", fg="green")
    for idx, f in flavor_choices.items():
        click.secho(f"{idx}) {f['name']}", fg="yellow")
    flavor_idx = click.prompt("Select flavor number", type=click.Choice(list(flavor_choices.keys())))
    flavor_id = flavor_choices[flavor_idx]["id"]

    sg_data = fetch_json("https://console.redu.cloud/api/cloud/network/security_groups/list")
    sgs = sg_data.get("security_groups", []) if isinstance(sg_data, dict) else sg_data if sg_data else []
    sg_choices = {str(i+1): sg for i, sg in enumerate(sgs)} if sgs else []
    selected_sgs = []
    if sg_choices:
        click.secho("Available security groups:", fg="green")
        for idx, sg in sg_choices.items():
            click.secho(f"{idx}) {sg['name']}", fg="yellow")
        sg_input = click.prompt("Select security groups (comma separated numbers)", default="")
        for num in sg_input.split(","):
            num = num.strip()
            if num in sg_choices:
                selected_sgs.append(sg_choices[num]["id"])

    net_data = fetch_json("https://console.redu.cloud/api/cloud/network/private_networks")
    networks = net_data.get("networks", []) if isinstance(net_data, dict) else net_data if net_data else []
    net_choices = {str(i+1): n for i, n in enumerate(networks)} if networks else {}
    network_id = None
    if net_choices:
        click.secho("Available networks:", fg="green")
        for idx, n in net_choices.items():
            click.secho(f"{idx}) {n['name']}", fg="yellow")
        net_idx = click.prompt("Select network number", type=click.Choice(list(net_choices.keys())))
        network_id = net_choices[net_idx]["id"]

    payload = {
        "name": server_name,
        "image": image_id,
        "flavor": flavor_id,
        "securityGroups": selected_sgs,
        "key_name": "redu-cli-key",
        "network": network_id,
        "is_public": "shouldbetrue",
        "dname": "",
        "enable_ssh": True,
        "volume": None,
    }

    click.secho("Server creation payload:", fg="green")
    click.secho(json.dumps(payload, indent=2), fg="yellow")

    try:
        create_resp = requests.post(
            "https://console.redu.cloud/api/cloud/compute/instances/create",
            headers={**headers, "Content-Type": "application/json"},
            json=payload
        )
        if create_resp.status_code != 200:
            click.secho(f"Failed to create server: {create_resp.status_code} {create_resp.text}", fg="red", bold=True)
            return
        server = create_resp.json()
        click.secho(f"Server created: {server.get('name', 'unknown')}", fg="green", bold=True)
    except requests.RequestException as e:
        click.secho(f"Error creating server: {e}", fg="red", bold=True)


@click.option("-d", "--domain", default="", help="Domain name for the server")
@server.command("create-smart")
@requires_token
@click.pass_context
def server_create_smart(ctx,domain):
    """Create a new server using smart defaults based on username"""
    access_token = ctx.obj["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    tokens = load_tokens()
    username = tokens.get("username", "unknown")

    description = click.prompt("Please explain what you would like to build", default="", show_default=False)
    server_name = click.prompt("Enter server name", type=str)

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

    click.secho("Server creation payload:", fg="green")
    click.secho(json.dumps(payload, indent=2), fg="yellow")

    try:
        create_resp = requests.post(
            "https://console.redu.cloud/api/cloud/compute/instances/create",
            headers={**headers, "Content-Type": "application/json"},
            json=payload
        )
        if create_resp.status_code not in (200, 201):
            click.secho(f"Failed to create server: {create_resp.status_code} {create_resp.text}", fg="red", bold=True)
            return
        server = create_resp.json()
        click.secho(f"Server created)", fg="green", bold=True)
    except requests.RequestException as e:
        click.secho(f"Error creating server: {e}", fg="red", bold=True)



@server.command("flavors")
@requires_token
@click.pass_context
def flavor_list(ctx):
    access_token = ctx.obj["access_token"]
    url = "https://console.redu.cloud/api/cloud/compute/instances/flavors"
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            click.secho(f"Failed to fetch flavors: {resp.status_code} {resp.text}", fg="red", bold=True)
            return

        data = resp.json()
        flavors = data if isinstance(data, list) else data.get("flavors", [])

        if not flavors:
            click.secho("No flavors found.", fg="yellow")
            return

        click.secho("Available flavors:", fg="green", bold=True)
        for flav in flavors:
            click.secho(f"- {flav.get('name', 'unknown')}", fg="yellow")

    except requests.RequestException as e:
        click.secho(f"Error fetching flavors: {e}", fg="red", bold=True)


@server.command("make-public")
@click.argument("instance_id")
@requires_token
@click.pass_context
def make_public(ctx, instance_id):
    """Make a server instance publicly accessible"""
    access_token = ctx.obj["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        url = "https://console.redu.cloud/api/cloud/compute/instance/make-public"
        resp = requests.post(url, headers=headers, json={"instanceId": instance_id})
        if resp.status_code != 200:
            click.secho(f"Failed to make instance public: {resp.status_code} {resp.text}", fg="red")
        else:
            click.secho(f"Instance {instance_id} is now public.", fg="green", bold=True)
    except requests.RequestException as e:
        click.secho(f"Error making instance public: {e}", fg="red")


# @server.command("create-dns")
# @click.argument("instance_id")
# @click.argument("domain")
# @click.option("-p", "--port", default=3000, help="Port to forward traffic to (default: 3000)")
# @requires_token
# @click.pass_context
# def create_dns(ctx, instance_id, domain, port):
#     """Create a DNS entry for a server instance"""
#     access_token = ctx.obj["access_token"]
#     headers = {"Authorization": f"Bearer {access_token}"}

#     try:
#         dns_url = "https://console.redu.cloud/api/cloud/dns/create"
#         resp = requests.post(dns_url, headers=headers, json={
#             "instanceId": instance_id,
#             "forwardPort": port,
#             "domain": domain,
#         })
#         if resp.status_code != 200:
#             click.secho(f"Failed to create DNS: {resp.status_code} {resp.text}", fg="red")
#         else:
#             click.secho(f"DNS created successfully for domain: {domain}", fg="green", bold=True)
#     except requests.RequestException as e:
#         click.secho(f"Error creating DNS: {e}", fg="red")

