from .cli import vap


def register(cli):
    cli.add_command(vap, name="vap")
