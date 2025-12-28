from pathlib import Path
from typing import Optional

from thestage.cli_command import CliCommand
from thestage.cli_command_helper import get_command_metadata, check_command_permission
from thestage.i18n.translation import __
from thestage.helpers.logger.app_logger import app_logger
from thestage.controllers.utils_controller import get_current_directory, validate_config_and_get_service_factory
from thestage import __app_name__, __version__

import typer

from thestage.services.connect.connect_service import ConnectService

app = typer.Typer(no_args_is_help=True,)


@app.command(name='version', help="Get application's name and version", no_args_is_help=False, **get_command_metadata(CliCommand.VERSION))
def version():
    command_name = CliCommand.VERSION
    app_logger.info(f'Running {command_name} from {get_current_directory()}')
    check_command_permission(command_name)

    typer.echo(f"{__app_name__} v{__version__}")
    raise typer.Exit(0)


@app.command(name="connect", no_args_is_help=True, help=__("Connect to server instance or container or task"), **get_command_metadata(CliCommand.CONNECT))
def connect(
        entity_identifier: Optional[str] = typer.Argument(
            help="Name or ID of server instance or container or task",
        ),
        username: Optional[str] = typer.Option(
            None,
            '--username',
            '-u',
            help=__("Username for the server instance (required when connecting to self-hosted instance)"),
            is_eager=False,
        ),
        private_ssh_key_path: str = typer.Option(
            None,
            "--private-key-path",
            "-pk",
            help=__("Path to private key that will be accepted by remote server (optional)"),
            is_eager=False,
        ),
):
    command_name = CliCommand.CONNECT
    app_logger.info(f'Running {command_name} from {get_current_directory()}')
    check_command_permission(command_name)

    if private_ssh_key_path and not Path(private_ssh_key_path).is_file():
        typer.echo(f'No file found at provided path {private_ssh_key_path}')
        raise typer.Exit(1)

    service_factory = validate_config_and_get_service_factory()

    connect_service: ConnectService = service_factory.get_connect_service()

    connect_service.connect_to_entity(
        input_entity_identifier=entity_identifier,
        username=username,
        private_key_path=private_ssh_key_path
    )


    app_logger.info(f'Stop connect to entity')
    raise typer.Exit(0)
