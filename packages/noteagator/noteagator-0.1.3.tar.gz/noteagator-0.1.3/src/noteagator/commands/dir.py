from __future__ import annotations

import click

from noteagator.config import Config
from noteagator.fsutils import print_directory_structure, resolve_cd_target, verify_path


@click.command(name="ls")
@click.option(
    "-d",
    "--max_depth",
    type=int,
    default=1,
    help="Display subdirectories to level N - 1",
)
@click.option(
    "-R", "--recursive", is_flag=True, help="Display subdirectories recursively"
)
def ls_cmd(max_depth, recursive) -> None:
    """
    List notes and folders in the notebook.
    """
    cfg = Config()
    if recursive:
        max_depth = None

    s = print_directory_structure(
        cfg.notebook_cwd, cfg.notebook_base_dir, max_depth=max_depth
    )
    cfg.display_index = s


@click.command(name="cd")
@click.argument("arg", type=str)
def cd_cmd(arg: str) -> None:
    """\b
    Change directory within the notebook.
    Examples:
        ngt cd 1
        ngt cd ..
        ngt cd /
    """
    cfg = Config()
    entry = (cfg.display_index or {}).get(arg) or {}
    entry_path = entry.get("absolute_path")
    node_type = entry.get("type")

    cfg.notebook_cwd = resolve_cd_target(
        arg=arg,
        entry_path=entry_path,
        node_type=node_type,
        cwd=cfg.notebook_cwd,
        base=cfg.notebook_base_dir,
    )


@click.command(name="set-base")
@click.argument("path")
def set_notebook_base(path):
    """
    Set the notebook base directory.
    """
    p = verify_path(path)
    cfg = Config()
    cfg.notebook_base_dir = p
    cfg.notebook_cwd = p


@click.command(name="show-base")
def show_base():
    """
    Print the current notebook base directory.
    """
    print(Config().notebook_base_dir)
