"""The CLI of kthutils"""

import logging
import typer
import typerconf as config
import kthutils.ug
import kthutils.participants
import kthutils.iprange
import kthutils.forms

cli = typer.Typer(name="kthutils",
                  help="A collection of tools useful at KTH")

logging.basicConfig(format="kthutils: %(levelname)s: %(message)s")

config.add_config_cmd(cli)
cli.add_typer(kthutils.ug.cli)
cli.add_typer(kthutils.participants.cli)
kthutils.iprange.add_command(cli)
cli.add_typer(kthutils.forms.cli)

if __name__ == "__main__":
    cli()
