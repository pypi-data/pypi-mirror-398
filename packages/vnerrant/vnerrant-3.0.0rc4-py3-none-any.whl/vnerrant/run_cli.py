from __future__ import annotations

import os
from warnings import filterwarnings

import click

from vnerrant.cli.convert import convert
from vnerrant.cli.evaluate import evaluate
from vnerrant.config import __version__

filterwarnings("ignore")

PRJ_DIR = os.getcwd()


@click.group()
def entry_point():
    pass


@click.command()
def version():
    print(f"version: {__version__}")
    return __version__


entry_point.add_command(version)
entry_point.add_command(evaluate)
entry_point.add_command(convert)
if __name__ == "__main__":
    entry_point()
