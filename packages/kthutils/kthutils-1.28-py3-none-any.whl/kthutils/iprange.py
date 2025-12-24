import typer
try:
  from typing import Annotated, List
except ImportError:
  from typing_extensions import Annotated, List

import pkgutil
import pathlib
import subprocess

rooms_arg = typer.Argument(help="The lab rooms to generate IP ranges for. "
                                "The lab room is the hostname prefix, eg red "
                                "(for Röd) or toke (for Toker).")

def add_command(cli):
  """
  Adds the [[iprange]] command to the given [[cli]].
  """
  @cli.command()
  def iprange(rooms: Annotated[List[str], rooms_arg]):
    """
    Generate the IP ranges for the given lab rooms. The lab rooms have the 
    following prefixes that can be used:

    ARCPLAN BALT BILBO BURE BUTT BYVPROJ CADLAB CHRIS COS-LAB
    DELL DFL FAGG FRODO FYLKE GLAD HALLF ITM-C13 ITM-C30 ITM-C45
    ITM-C46 ITSC KA-209 KA-309 KLOK KTHB LABB305 M102 M122 MACL
    MAT MAX MERRY NILS PIPPIN PROS RB33 REMOTE SAM T41 T65 TOKE
    TROT XQ23 XQ25 XQ32 XW343 XW344 XW41 XW50
    """
    package_path = pathlib.Path(pkgutil.get_loader(__name__).path).parent
    iprange_sh = package_path / "iprange.sh"
    subprocess.run([iprange_sh, *rooms], check=True)

if __name__ == "__main__":
  cli = typer.Typer()
  add_command(cli)
  cli()
