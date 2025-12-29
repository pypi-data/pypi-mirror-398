import json
import tempfile
import typing
from pathlib import Path
from typing import Annotated

import typer
from rich import print as rprint
from rich.table import Table
from typer import Option

from amsdal_cli.commands.cloud.enums import OutputFormat
from amsdal_cli.commands.cloud.external_connections.app import external_connections_sub_app


def connection_list_command(
    ctx: typer.Context,
    output: Annotated[OutputFormat, typer.Option('--output', '-o')] = OutputFormat.default,
    env_name: typing.Annotated[
        typing.Optional[str],  # noqa: UP007
        Option('--env', help='Environment name. Default is the current environment from configuration.'),
    ] = None,
    *,
    sync: bool = Option(
        False,
        '--sync',
        help='Sync the external connections from the Cloud Server to ".external_connections".',
    ),
) -> None:
    """
    List the app external connections on the Cloud Server.

    Args:
        ctx (typer.Context): The Typer context object.
        output (Annotated[OutputFormat, typer.Option]): The output format for the list.
            Defaults to OutputFormat.default.
        env_name (typing.Annotated[typing.Optional[str], Option]): The name of the environment. Defaults to the current
            environment from configuration.
        sync (bool): Whether to sync the external connections from the Cloud Server to ".external_connections".
            Defaults to False.

    Returns:
        None
    """
    from amsdal.errors import AmsdalCloudError
    from amsdal.manager import AmsdalManager
    from amsdal.manager import AsyncAmsdalManager
    from amsdal_utils.config.manager import AmsdalConfigManager

    from amsdal_cli.commands.build.services.builder import AppBuilder
    from amsdal_cli.commands.cloud.environments.utils import get_current_env
    from amsdal_cli.utils.cli_config import CliConfig
    from amsdal_cli.utils.text import rich_error
    from amsdal_cli.utils.text import rich_highlight
    from amsdal_cli.utils.text import rich_info

    cli_config: CliConfig = ctx.meta['config']
    env_name = env_name or get_current_env(cli_config)

    if cli_config.verbose:
        rprint(rich_info(f'Listing external connections for environment: {rich_highlight(env_name)}'))

    with tempfile.TemporaryDirectory() as _temp_dir:
        output_path: Path = Path(_temp_dir)
        app_builder = AppBuilder(
            cli_config=cli_config,
            config_path=cli_config.config_path,
        )
        app_builder.build(output_path, is_silent=True)
        manager: AsyncAmsdalManager | AmsdalManager

        manager = AsyncAmsdalManager() if AmsdalConfigManager().get_config().async_mode else AmsdalManager()

        manager.authenticate()

    try:
        list_response = manager.cloud_actions_manager.list_external_connections(
            env_name=env_name,
            application_uuid=cli_config.application_uuid,
            application_name=cli_config.application_name,
        )
    except AmsdalCloudError as e:
        rprint(rich_error(str(e)))
        raise typer.Exit(1) from e

    if not list_response or not list_response.details:
        return

    if sync and list_response.details.connections:
        config_dir: Path = cli_config.app_directory / '.amsdal'
        config_dir.mkdir(exist_ok=True, parents=True)
        _connections_path: Path = config_dir / '.external_connections'
        _connections_path.touch(exist_ok=True)
        _connections_path.write_text(
            '\n'.join([connection.name for connection in list_response.details.connections]),
        )

    if output == OutputFormat.json:
        rprint(json.dumps(list_response.model_dump(), indent=4))
        return

    if not list_response.details.connections:
        rprint('No external connections found.')
        return

    data_table = Table()
    data_table.add_column('Connection Name', justify='center')
    data_table.add_column('Backend', justify='center')
    data_table.add_column('Credentials', justify='center')

    for connection in list_response.details.connections:
        # Show only credential keys, not values for security
        credential_keys = ', '.join(connection.credentials.keys()) if connection.credentials else ''
        data_table.add_row(connection.name, connection.backend, credential_keys)

    rprint(data_table)


@external_connections_sub_app.callback(invoke_without_command=True)
def connection_list_callback(
    ctx: typer.Context,
    output: Annotated[OutputFormat, typer.Option('--output', '-o')] = OutputFormat.default,
    env_name: typing.Annotated[
        typing.Optional[str],  # noqa: UP007
        Option('--env', help='Environment name. Default is the current environment from configuration.'),
    ] = None,
    *,
    sync: bool = Option(
        False,
        '--sync',
        help='Sync the external connections from the Cloud Server to ".external_connections".',
    ),
) -> None:
    """
    Lists the app external connections on the Cloud Server.
    """

    if ctx.invoked_subcommand is not None:
        return

    connection_list_command(
        ctx=ctx,
        output=output,
        env_name=env_name,
        sync=sync,
    )
