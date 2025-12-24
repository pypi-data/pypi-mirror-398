from __future__ import annotations

import typer

from simple_automated_testing.cli.init_cmd import init_cmd
from simple_automated_testing.cli.list_cmd import list_cmd
from simple_automated_testing.cli.run import run_cmd


app = typer.Typer(add_help_option=True)


app.command("run")(run_cmd)
app.command("list")(list_cmd)
app.command("init")(init_cmd)
