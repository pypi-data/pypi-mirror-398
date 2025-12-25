"""Generate ExternalModel classes from external database connections."""

from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any

import typer

from amsdal_cli.commands.generate.app import sub_app

if TYPE_CHECKING:
    from amsdal_cli.utils.cli_config import CliConfig


@sub_app.command(name='external-models, ext-models, em')
def generate_external_models(
    ctx: typer.Context,
    connection_name: str = typer.Argument(
        ...,
        help='The name of the external connection configured in config',
    ),
    output_dir: Path = typer.Option(  # noqa: B008
        None,
        '--output',
        '-o',
        help='Output directory for generated models (defaults to models/external/)',
    ),
    tables: list[str] = typer.Option(  # noqa: B008
        None,
        '--table',
        '-t',
        help='Specific table names to generate models for (generates all if not specified)',
    ),
    format_type: str = typer.Option(  # noqa: B008
        'python',
        '--format',
        '-f',
        help='Output format: "python" or "json"',
    ),
    schema: str | None = typer.Option(  # noqa: B008, ARG001
        None,
        '--schema',
        '-s',
        help='Database schema name (for databases that support schemas like PostgreSQL)',
    ),
) -> None:
    """Generate ExternalModel classes from external database connections.

    This command introspects an external database connection and generates
    ExternalModel classes for the tables. The generated models can be used
    immediately to query the external database.

    **Examples:**

    Generate models for all tables in an external connection:

    ```bash
    amsdal generate external-models my_external_db
    ```

    Generate models for specific tables only:

    ```bash
    amsdal generate external-models my_external_db -t users -t posts -t comments
    ```

    Generate models in JSON format:

    ```bash
    amsdal generate external-models my_external_db --format json
    ```

    Specify custom output directory:

    ```bash
    amsdal generate external-models my_external_db -o src/external_models
    ```

    Generate models for a specific PostgreSQL schema:

    ```bash
    amsdal generate external-models pg_db --schema public
    ```

    **Prerequisites:**

    1. The external connection must be configured in your AMSDAL config
    2. The connection must support schema introspection (SQLite, PostgreSQL)
    3. The ExternalConnectionManager must be properly set up

    **Generated Output:**

    For Python format:
    - Creates a module for each model: `models/external/{table_name}.py`
    - Each module contains an ExternalModel class ready to use

    For JSON format:
    - Creates JSON schema files: `models/external/{table_name}/model.json`
    - Can be loaded dynamically by AMSDAL framework
    """
    from amsdal.services.external_connections import ExternalConnectionManager
    from amsdal.services.external_model_generator import ExternalModelGenerator
    from amsdal_data.application import DataApplication
    from amsdal_utils.config.manager import AmsdalConfigManager
    from amsdal_utils.utils.text import to_snake_case

    from amsdal_cli.utils.cli_config import CliConfig

    cli_config: CliConfig = ctx.meta['config']

    # Validate format
    if format_type not in ('python', 'json'):
        typer.echo(f"Error: Invalid format '{format_type}'. Must be 'python' or 'json'.", err=True)
        raise typer.Exit(1)

    # Set default output directory
    if output_dir is None:
        output_dir = Path.cwd() / 'models' / 'external'

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize AMSDAL components
    config_manager = AmsdalConfigManager()
    config = config_manager.get_config()

    # Verify connection exists in config
    if connection_name not in config.connections:
        typer.echo(
            f"Error: Connection '{connection_name}' not found in configuration.\n"
            f'Available connections: {", ".join(config.connections.keys())}',
            err=True,
        )
        raise typer.Exit(1)

    # Initialize DataApplication
    app = DataApplication()
    app.setup(config)

    # Initialize ExternalConnectionManager
    manager = ExternalConnectionManager()
    manager.setup(data_application=app)

    # Initialize ExternalModelGenerator
    generator = ExternalModelGenerator()

    try:
        # Generate models
        typer.echo(f"Generating external models from connection '{connection_name}'...")

        if tables:
            typer.echo(f'Tables: {", ".join(tables)}')
        else:
            typer.echo('Generating models for all tables...')

        models_dict = generator.generate_models_for_connection(
            connection_name=connection_name,
            table_names=tables if tables else None,
        )

        if not models_dict:
            typer.echo('No tables found or no models generated.', err=True)
            raise typer.Exit(1)

        typer.echo(f'Successfully generated {len(models_dict)} model(s)')

        # Write models to files
        if format_type == 'python':
            _write_python_models(models_dict, output_dir, cli_config)
        else:
            _write_json_models(models_dict, output_dir, cli_config, connection_name)

        typer.echo(f'\nGenerated models written to: {output_dir}')
        typer.echo('\nYou can now import and use these models:')
        typer.echo('```python')
        first_model = next(iter(models_dict.keys()))
        typer.echo(f'from models.external.{to_snake_case(first_model)} import {first_model}')
        typer.echo(f'{first_model}.objects.all().execute()')
        typer.echo('```')

    except ValueError as e:
        typer.echo(f'Error: {e}', err=True)
        raise typer.Exit(1) from e
    except ConnectionError as e:
        typer.echo(f'Connection error: {e}', err=True)
        raise typer.Exit(1) from e
    except Exception as e:
        typer.echo(f'Unexpected error: {e}', err=True)
        raise typer.Exit(1) from e
    finally:
        # Clean up
        app.teardown()
        ExternalConnectionManager.invalidate()
        AmsdalConfigManager.invalidate()
        DataApplication.invalidate()


def _write_python_models(
    models_dict: dict[str, type],
    output_dir: Path,
    cli_config: 'CliConfig',  # noqa: F821
) -> None:
    """Write generated models as Python files."""
    from amsdal_utils.utils.text import to_snake_case

    # Create __init__.py for the package
    init_file = output_dir / '__init__.py'
    init_file.touch(exist_ok=True)

    # Write each model to a separate file
    for model_name, model_class in models_dict.items():
        module_name = to_snake_case(model_name)
        file_path = output_dir / f'{module_name}.py'

        # Generate the model file content
        content = _generate_python_model_content(model_class, cli_config)

        # Write to file
        file_path.write_text(content)
        typer.echo(f'  ✓ {module_name}.py')


def _generate_python_model_content(model_class: type, cli_config: 'CliConfig') -> str:  # noqa: F821
    """Generate Python code for an ExternalModel class."""
    model_name = model_class.__name__
    table_name = model_class.__table_name__  # type: ignore[attr-defined]
    connection = model_class.__connection__  # type: ignore[attr-defined]

    # Get annotations
    annotations = getattr(model_class, '__annotations__', {})

    # Build imports
    imports = {'from amsdal_models.classes.external_model import ExternalModel'}

    # Build field definitions
    field_lines = []
    indent = ' ' * cli_config.indent

    for field_name, field_type in annotations.items():
        type_str = _get_type_annotation(field_type)
        field_lines.append(f'{indent}{field_name}: {type_str}')

    # Build class definition
    lines = [
        '"""',
        f'External model for {table_name} table.',
        '',
        f'Generated from external connection: {connection}',
        '"""',
        '',
        *sorted(imports),
        '',
        '',
        f'class {model_name}(ExternalModel):',
        f'{indent}"""External model for {table_name}."""',
        '',
        f"{indent}__table_name__ = '{table_name}'",
        f"{indent}__connection__ = '{connection}'",
    ]

    # Add primary key if present
    if hasattr(model_class, '__primary_key__'):
        pk = model_class.__primary_key__
        if isinstance(pk, list):
            lines.append(f'{indent}__primary_key__ = {pk!r}')
        else:
            lines.append(f"{indent}__primary_key__ = '{pk}'")

    # Add field definitions
    if field_lines:
        lines.append('')
        lines.extend(field_lines)

    return '\n'.join(lines) + '\n'


def _get_type_annotation(python_type: type) -> str:
    """Convert Python type to string annotation."""
    type_mapping = {
        str: 'str',
        int: 'int',
        float: 'float',
        bool: 'bool',
        bytes: 'bytes',
        list: 'list',
        dict: 'dict',
    }

    return type_mapping.get(python_type, 'str')


def _write_json_models(
    models_dict: dict[str, type],
    output_dir: Path,
    cli_config: 'CliConfig',  # noqa: F821
    connection_name: str,
) -> None:
    """Write generated models as JSON schema files."""
    import json

    from amsdal_utils.utils.text import to_snake_case

    for model_name, model_class in models_dict.items():
        module_name = to_snake_case(model_name)
        model_dir = output_dir / module_name
        model_dir.mkdir(exist_ok=True, parents=True)

        json_file = model_dir / 'model.json'

        # Build JSON schema
        schema = _generate_json_schema(model_class, connection_name)

        # Write to file
        json_file.write_text(json.dumps(schema, indent=cli_config.indent, ensure_ascii=False))
        typer.echo(f'  ✓ {module_name}/model.json')


def _generate_json_schema(model_class: type, connection_name: str) -> dict[str, Any]:
    """Generate JSON schema for an ExternalModel class."""
    model_name = model_class.__name__
    table_name = model_class.__table_name__  # type: ignore[attr-defined]
    annotations = getattr(model_class, '__annotations__', {})

    # Build properties
    properties = {}
    for field_name, field_type in annotations.items():
        properties[field_name] = {
            'type': _python_type_to_json_type(field_type),
            'title': field_name,
        }

    schema: dict[str, Any] = {
        'title': model_name,
        'type': 'object',
        'properties': properties,
        '__table_name__': table_name,
        '__connection__': connection_name,
    }

    # Add primary key if present
    if hasattr(model_class, '__primary_key__'):
        pk = model_class.__primary_key__
        if isinstance(pk, str):
            schema['__primary_key__'] = [pk]
        else:
            schema['__primary_key__'] = list(pk)

    return schema


def _python_type_to_json_type(python_type: type) -> str:
    """Convert Python type to JSON schema type string."""
    from amsdal_utils.models.data_models.enums import CoreTypes

    type_mapping = {
        str: CoreTypes.STRING.value,
        int: CoreTypes.INTEGER.value,
        float: CoreTypes.NUMBER.value,
        bool: CoreTypes.BOOLEAN.value,
        bytes: CoreTypes.BINARY.value,
        list: CoreTypes.ARRAY.value,
        dict: CoreTypes.DICTIONARY.value,
    }

    return type_mapping.get(python_type, CoreTypes.STRING.value)
