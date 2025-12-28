import os
import time
import json
import base64
from pathlib import Path

import click
import requests

BASE_URL = "https://login.redu.cloud/realms/testrealm/protocol/openid-connect"
CLIENT_ID = "ovojenajboljiid"
CONFIG_DIR = Path.home() / ".redu"
CONFIG_FILE = CONFIG_DIR / "config.json"
# ------------------ Token Storage ------------------
def save_tokens(data, username=None):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if username:
        data["username"] = username
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_tokens():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {}
# ------------------ JWT & Token Utils ------------------
def decode_jwt(token):
    try:
        payload_b64 = token.split('.')[1]
        rem = len(payload_b64) % 4
        if rem > 0:
            payload_b64 += '=' * (4 - rem)
        decoded_bytes = base64.urlsafe_b64decode(payload_b64)
        return json.loads(decoded_bytes)
    except Exception as e:
        raise ValueError(f"Failed to decode JWT: {e}")

def is_token_expired(token, buffer_sec=30):
    claims = decode_jwt(token)
    exp = claims.get("exp")
    if not exp:
        return True
    return time.time() > (exp - buffer_sec)

def refresh_access_token(refresh_token):
    payload = {
        "grant_type": "refresh_token",
        "client_id": CLIENT_ID,
        "refresh_token": refresh_token
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    resp = requests.post(f"{BASE_URL}/token", data=payload, headers=headers)
    if resp.status_code != 200:
        raise RuntimeError(f"Failed to refresh token: {resp.text}")
    return resp.json()

def get_valid_access_token():
    tokens = load_tokens()
    if not tokens or "auth_token" not in tokens:
        raise RuntimeError("Not logged in. Run `auth` first.")
    access_token = tokens["auth_token"].get("access_token")
    refresh_token = tokens["auth_token"].get("refresh_token")
    username = tokens.get("username")
    if not access_token:
        raise RuntimeError("Access token not found.")
    if is_token_expired(access_token) and refresh_token:
        # click.secho("Access token expired, refreshing...", fg="yellow")
        new_tokens = refresh_access_token(refresh_token)
        tokens["auth_token"] = new_tokens
        save_tokens(tokens, username=username)
        access_token = new_tokens["access_token"]
        # click.secho("Token refreshed.", fg="green", bold=True)
    return access_token, username
# ------------------ Decorator ------------------
def requires_token(f):
    @click.pass_context
    def wrapper(ctx, *args, **kwargs):
        try:
            ctx.obj = ctx.obj or {}
            access_token, username = get_valid_access_token()
            ctx.obj["access_token"] = access_token
            ctx.obj["username"] = username
        except RuntimeError as e:
            click.secho(str(e), fg="red", bold=True)
            ctx.exit(1)
        return ctx.invoke(f, *args, **kwargs)
    return wrapper