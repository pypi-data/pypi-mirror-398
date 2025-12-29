import typer

from amsdal_cli.utils.alias_group import AliasGroup

external_connections_sub_app = typer.Typer(
    help=(
        'Manage external connections for your Cloud Server app. '
        'Without any sub-command, it will list all external connections.'
    ),
    cls=AliasGroup,
)
