import click
import getpass
import requests
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from .utils import BASE_URL, CLIENT_ID, CONFIG_DIR, save_tokens

# ------------------ Auth ------------------
@click.command()
@click.option("-u", "--username", required=True, help="Username")
def auth(username):
    password = getpass.getpass("Password: ")
    payload = {
        "grant_type": "password",
        "client_id": CLIENT_ID,
        "username": username,
        "password": password
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    resp = requests.post(f"{BASE_URL}/token", data=payload, headers=headers)
    if resp.status_code != 200:
        click.secho(f"Authentication failed: {resp.text}", fg="red", bold=True)
        return
    tokens = resp.json()
    save_tokens({"auth_token": tokens}, username=username)
    click.secho("Authentication successful.", fg="green", bold=True)

 # ------------------ SSH Key Generation ------------------
    private_key_file = CONFIG_DIR / "id_rsa_redu_cli"
    public_key_file = CONFIG_DIR / "id_rsa_redu_cli.pub"
    if private_key_file.exists() and public_key_file.exists():
        click.secho(f"SSH key already exists: {private_key_file}", fg="green", bold=True)
    else:
        click.secho("SSH key not found. Generating a new keypair...", fg="yellow")
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
        with open(private_key_file, "wb") as f:
            f.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
        pub = key.public_key().public_bytes(
            encoding=serialization.Encoding.OpenSSH,
            format=serialization.PublicFormat.OpenSSH
        )
        with open(public_key_file, "wb") as f:
            f.write(pub)
        click.secho(f"SSH keypair created: {private_key_file} / {public_key_file}", fg="green", bold=True)

    # Upload Key to Cloud
    try:
        access_token = tokens["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        with open(public_key_file, "r") as f:
            new_public_key = f.read().strip()
        resp = requests.get("https://console.redu.cloud/api/cloud/compute/keypairs", headers=headers)
        if resp.status_code != 200:
            click.secho(f"Failed to fetch keypairs: {resp.text}", fg="red", bold=True)
            return
        keypairs = resp.json() if isinstance(resp.json(), list) else resp.json().get("keypairs", [])
        key_exists = any(kp.get("keypair", {}).get("public_key") == new_public_key for kp in keypairs)
        if key_exists:
            click.secho("SSH public key already registered in cloud.", fg="green", bold=True)
        else:
            new_keypair_name = "redu-cli-key"
            add_resp = requests.post(
                "https://console.redu.cloud/api/cloud/compute/keypairs",
                headers={**headers, "Content-Type": "application/json"},
                json={"name": new_keypair_name, "publicKey": new_public_key}
            )
            if add_resp.status_code in [200, 201]:
                click.secho(f"SSH public key uploaded as '{new_keypair_name}'.", fg="green", bold=True)
            else:
                click.secho(f"Failed to upload SSH key: {add_resp.status_code} {add_resp.text}", fg="red", bold=True)
    except Exception as e:
        click.secho(f"Error while syncing SSH key: {e}", fg="red", bold=True)