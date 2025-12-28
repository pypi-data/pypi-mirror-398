#!/usr/bin/env python3
import sys
import os
from pathlib import Path


from .services.auth import auth
from .services.server import server
from .services.network import network
from .services.image import image
from .services.ssh import ssh_server as ssh
from .services.setup import setup_instance as setup
from .services.whoami import whoami
from .services.ai import ai

import click
# Vendored cryptography
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

# ------------------ Constants ------------------
BASE_URL = "https://login.redu.cloud/realms/testrealm/protocol/openid-connect"
CLIENT_ID = "ovojenajboljiid"
CONFIG_DIR = Path.home() / ".redu"
CONFIG_FILE = CONFIG_DIR / "config.json"

@click.group()
@click.pass_context
def cli(ctx):
    """Cloud platform CLI"""
    ctx.ensure_object(dict)

cli.add_command(auth)
cli.add_command(server)
cli.add_command(network)
cli.add_command(image)
cli.add_command(ssh)
cli.add_command(setup)
cli.add_command(whoami)
cli.add_command(ai)

# # ------------------ Main ------------------
# if __name__ == "__main__":
#     cli()
