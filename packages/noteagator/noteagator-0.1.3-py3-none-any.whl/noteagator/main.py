from __future__ import annotations

import click

from noteagator.commands.dir import cd_cmd, ls_cmd, set_notebook_base, show_base
from noteagator.commands.notes import daily_note, prt, search, set_print_mode


class OrderedGroup(click.Group):
    def list_commands(self, ctx):
        return list(self.commands.keys())


@click.group(
    cls=OrderedGroup,
    context_settings={"help_option_names": ["-h", "--help"]},
    epilog="""\b
Examples:
  ngt set-base ~/notes
  ngt show-base
  cd "$(ngt show-base)"; ls; code -n .
  ngt jot "standup: shipped auth refactor"
  ngt print 3
  ngt search k8s
  ngt cd 1
  ngt ls
""",
)
def main() -> None:
    """noteagator CLI."""


main.add_command(set_notebook_base)
main.add_command(show_base)
main.add_command(ls_cmd)
main.add_command(prt)
main.add_command(cd_cmd)
main.add_command(search)
main.add_command(daily_note)
main.add_command(set_print_mode)


if __name__ == "__main__":
    main()
