import click
from .utils import requires_token, decode_jwt
# ------------------ Whoami ------------------
@click.command("whoami")
@requires_token
@click.pass_context
def whoami(ctx):
    access_token = ctx.obj["access_token"]
    claims = decode_jwt(access_token)
    # click.secho(f"Access token: {access_token[:40]}... (truncated)", fg="yellow")
    click.secho(f"Access token: {access_token}", fg="yellow")
    click.secho("Token claims:", fg="yellow")
    for k, v in claims.items():
        click.echo(f"  {k}: {v}")