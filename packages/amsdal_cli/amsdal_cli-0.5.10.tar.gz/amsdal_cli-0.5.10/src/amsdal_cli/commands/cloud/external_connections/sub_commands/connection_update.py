import tempfile
import typing
from pathlib import Path

import typer
from rich import print as rprint
from typer import Option

from amsdal_cli.commands.cloud.external_connections.app import external_connections_sub_app
from amsdal_cli.commands.cloud.external_connections.sub_commands.connection_add import parse_credentials


@external_connections_sub_app.command(name='update, u')
def connection_update_command(
    ctx: typer.Context,
    connection_name: str,
    backend: typing.Annotated[
        typing.Optional[str],  # noqa: UP007
        Option('--backend', '-b', help='New backend type for the connection.'),
    ] = None,
    credentials: typing.Annotated[
        typing.Optional[list[str]],  # noqa: UP007
        Option('--credential', '-c', help='Credential in key=value format. Can be specified multiple times.'),
    ] = None,
    env_name: typing.Annotated[
        typing.Optional[str],  # noqa: UP007
        Option('--env', help='Environment name. Default is the current environment from configuration.'),
    ] = None,
) -> None:
    """
    Updates an existing external connection in your Cloud Server app.
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
    from amsdal_cli.utils.text import rich_success

    cli_config: CliConfig = ctx.meta['config']
    env_name = env_name or get_current_env(cli_config)

    # Validate that at least one update parameter is provided
    if not backend and (not credentials or len(credentials) == 0):
        rprint(rich_error('No updates specified. Provide --backend or --credential.'))
        raise typer.Exit(1)

    # Parse credentials if provided
    credentials_dict = None
    if credentials:
        try:
            credentials_dict = parse_credentials(credentials)
        except typer.BadParameter as e:
            rprint(rich_error(str(e)))
            raise typer.Exit(1) from e

    if cli_config.verbose:
        update_info = []
        if backend:
            update_info.append(f'backend to {rich_highlight(backend)}')
        if credentials_dict:
            update_info.append('credentials')
        rprint(
            rich_info(
                f'Updating external connection {rich_highlight(connection_name)} '
                f'({", ".join(update_info)}) '
                f'in environment: {rich_highlight(env_name)}'
            )
        )

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
        manager.cloud_actions_manager.update_external_connection(
            connection_name=connection_name,
            env_name=env_name,
            backend=backend,
            credentials=credentials_dict,
            application_uuid=cli_config.application_uuid,
            application_name=cli_config.application_name,
        )
    except AmsdalCloudError as e:
        rprint(rich_error(str(e)))
        raise typer.Exit(1) from e

    rprint(rich_success(f'External connection {rich_highlight(connection_name)} updated successfully.'))
