import click

from pantoqa_bridge.config import EXT_VERSION, SERVER_HOST, SERVER_PORT
from pantoqa_bridge.server import start_bridge_server


@click.group(help="PantoAI QA Extension CLI", invoke_without_command=True)
@click.option("--version", is_flag=True, help="Show version and exit")
@click.pass_context
def cli(ctx: click.Context, version: bool) -> None:
  if version:
    click.echo(EXT_VERSION)
    ctx.exit(0)

  if ctx.invoked_subcommand is None:
    ctx.invoke(serve)


@cli.command()
@click.option("--host", default=SERVER_HOST, show_default=True, help="Bind address")
@click.option("--port", default=SERVER_PORT, show_default=True, type=int, help="Port to listen on")
def serve(host: str, port: int) -> None:
  start_bridge_server(host, port)


if __name__ == "__main__":
  cli()
