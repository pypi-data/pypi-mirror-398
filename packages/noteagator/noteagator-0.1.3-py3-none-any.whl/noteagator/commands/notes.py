from __future__ import annotations

import click
import yaml

from noteagator.config import Config
from noteagator.fsutils import append_jot, search_files
from noteagator.note import Note
from noteagator.print_utils import (
    format_note_body,
    get_fmt,
    print_note_markdown,
    print_note_slim,
)


@click.command(name="search")
@click.argument("search_term")
@click.option(
    "-c",
    "--from-cwd",
    is_flag=True,
    help="Search from the current working directory instead of the notebook base.",
)
@click.option(
    "-t",
    "--tag",
    "tags_all",
    multiple=True,
    help="Require notes to have ALL of these tags. May be repeated.",
)
@click.option(
    "-T",
    "--tag-any",
    "tags_any",
    multiple=True,
    help="Match notes that have ANY of these tags. May be repeated.",
)
def search(search_term, from_cwd, tags_all, tags_any):
    """
    Search notes for a term, optionally filtered by tags.
    """
    cfg = Config()
    base_dir = cfg.notebook_cwd if from_cwd else cfg.notebook_base_dir

    tags_all = tuple(t.strip().lower() for t in tags_all if t.strip())
    tags_any = tuple(t.strip().lower() for t in tags_any if t.strip())

    s = search_files(
        base_dir,
        search_term,
        tags_all=tags_all,
        tags_any=tags_any,
    )
    if s:
        cfg.display_index = s


@click.command(name="jot")
@click.argument("note")
def daily_note(note):
    """
    Append text to jots/MM-DD-YYYY.md (creates if missing).
    """
    cfg = Config()
    append_jot(cfg.notebook_base_dir, note)


@click.command(name="print-mode")
@click.argument("mode", type=click.Choice(["markdown", "slim"], case_sensitive=False))
def set_print_mode(mode: str):
    """Set default print mode (markdown or slim)."""
    cfg = Config()
    mode = mode.lower()
    cfg.print_mode = mode
    click.echo(f"Default print mode set to: {mode}")


@click.command(
    name="print",
    help="""\b
Render a note by INDEX using the chosen output format, applying any replacement 
values specified via the -i/-j/-k/-u/-d/-p options.
Replacements:
  Notes can declare placeholder keys in YAML front matter:
    ---
    description: My note
    placeholder:
      i: keyWord
    ---
  When you run `ngt print NUM -i newWord`, any occurrence of the placeholder value
  associated with i (e.g., 'keyWord') is replaced with 'newWord' for output.
""",
)
@click.argument("index", type=str)
@click.option("-c", "--copy", "copy", type=click.IntRange(1, None), default=None)
@click.option("-i", "i", help="Replacement value for the 'i' placeholder.")
@click.option("-j", "j", help="Replacement value for the 'j' placeholder.")
@click.option("-k", "k", help="Replacement value for the 'k' placeholder.")
@click.option("-u", "u", help="Replacement value for the 'u' placeholder.")
@click.option("-d", "d", help="Replacement value for the 'd' placeholder.")
@click.option("-p", "p", help="Replacement value for the 'p' placeholder.")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["markdown", "slim"]),
    default=None,
    show_default=True,
)
def prt(index, copy, i, j, k, u, d, p, fmt):
    """
    Render a note (markdown or slim).
    """
    cfg = Config()
    n = Note(cfg.return_file_path(index))
    body = format_note_body(n.body, n.metadata, i, j, k, u, d, p)
    print_fmt = get_fmt(fmt, cfg.print_mode, n.metadata.get("format"))
    print(yaml.dump(n.metadata, default_flow_style=False).strip())
    print("---")
    if print_fmt == "slim":
        print_note_slim(body, copy)
    else:
        print_note_markdown(body, copy)
