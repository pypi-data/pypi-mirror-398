import tempfile
import typing
from pathlib import Path

import typer
from rich import print as rprint
from typer import Option

from amsdal_cli.commands.cloud.external_connections.app import external_connections_sub_app


@external_connections_sub_app.command(name='remove, rm, r')
def connection_remove_command(
    ctx: typer.Context,
    connection_name: str,
    env_name: typing.Annotated[
        typing.Optional[str],  # noqa: UP007
        Option('--env', help='Environment name. Default is the current environment from configuration.'),
    ] = None,
) -> None:
    """
    Removes an external connection from the Cloud Server app.
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

    if cli_config.verbose:
        rprint(
            rich_info(
                f'Removing external connection {rich_highlight(connection_name)} '
                f'from environment: {rich_highlight(env_name)}'
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
        manager.cloud_actions_manager.remove_external_connection(
            connection_name=connection_name,
            env_name=env_name,
            application_uuid=cli_config.application_uuid,
            application_name=cli_config.application_name,
        )
    except AmsdalCloudError as e:
        rprint(rich_error(str(e)))
        raise typer.Exit(1) from e
    else:
        config_dir: Path = cli_config.app_directory / '.amsdal'
        config_dir.mkdir(exist_ok=True, parents=True)
        _connections_path: Path = config_dir / '.external_connections'
        _connections_path.touch(exist_ok=True)
        _connections = set(_connections_path.read_text().split('\n'))

        if connection_name in _connections:
            _connections.remove(connection_name)
            _connections_path.write_text('\n'.join(_connections))

    rprint(rich_success(f'External connection {rich_highlight(connection_name)} removed successfully.'))
