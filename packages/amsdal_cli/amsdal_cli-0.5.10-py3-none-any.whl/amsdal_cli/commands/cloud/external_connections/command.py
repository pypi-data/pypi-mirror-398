from amsdal_cli.commands.cloud.app import cloud_sub_app
from amsdal_cli.commands.cloud.external_connections.app import external_connections_sub_app
from amsdal_cli.commands.cloud.external_connections.sub_commands import *  # noqa

cloud_sub_app.add_typer(external_connections_sub_app, name='external-connections, ext-conn, ec')
