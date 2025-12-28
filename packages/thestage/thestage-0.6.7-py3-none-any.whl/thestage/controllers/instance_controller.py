from pathlib import Path
from typing import Optional, List

from thestage.cli_command import CliCommand
from thestage.cli_command_helper import get_command_group_help_panel, get_command_metadata, check_command_permission
from thestage.helpers.logger.app_logger import app_logger
from thestage.services.instance.instance_service import InstanceService
from thestage.i18n.translation import __
from thestage.controllers.utils_controller import \
    validate_config_and_get_service_factory, get_current_directory

import typer


app = typer.Typer(no_args_is_help=True, help=__("Manage server instances"))

rented = typer.Typer(no_args_is_help=True, help=__("Manage rented server instances"))
self_hosted = typer.Typer(no_args_is_help=True, help=__("Manage self-hosted instances"))

app.add_typer(rented, name="rented", rich_help_panel=get_command_group_help_panel())
app.add_typer(self_hosted, name="self-hosted", rich_help_panel=get_command_group_help_panel())


@rented.command(name="ls", help=__("List rented server instances"), **get_command_metadata(CliCommand.INSTANCE_RENTED_LS))
def rented_list(
        row: int = typer.Option(
            5,
            '--row',
            '-r',
            help=__("Set number of rows displayed per page"),
            is_eager=False,
        ),
        page: int = typer.Option(
            1,
            '--page',
            '-p',
            help=__("Set starting page for displaying output"),
            is_eager=False,
        ),
        statuses: List[str] = typer.Option(
            None,
            '--status',
            '-s',
            help=__("Filter by status, use --status all to list all rented server instances"),
            is_eager=False,
        ),
):
    command_name = CliCommand.INSTANCE_RENTED_LS
    app_logger.info(f'Running {command_name} from {get_current_directory()}')
    check_command_permission(command_name)

    service_factory = validate_config_and_get_service_factory()
    instance_service: InstanceService = service_factory.get_instance_service()

    instance_service.print_rented_instance_list(
        statuses=statuses,
        row=row,
        page=page
    )

    typer.echo(__("Rented server instances listing complete"))
    raise typer.Exit(0)


@rented.command(name="connect", no_args_is_help=True, help=__("Connect to rented server instance"), **get_command_metadata(CliCommand.INSTANCE_RENTED_CONNECT))
def instance_connect(
        public_id: Optional[str] = typer.Option(
            None,
            '--rented-instance-id',
            '-rid',
            help="Rented instance ID",
            is_eager=False,
        ),
        slug: Optional[str] = typer.Option(
            None,
            '--rented-instance-name',
            '-rn',
            help="Rented instance name",
            is_eager=False,
        ),
        private_ssh_key_path: str = typer.Option(
            None,
            "--private-key-path",
            "-pk",
            help=__("Path to private key that will be accepted by remote server (optional)"),
            is_eager=False,
        )
):
    command_name = CliCommand.INSTANCE_RENTED_CONNECT
    app_logger.info(f'Running {command_name} from {get_current_directory()}')
    check_command_permission(command_name)

    if sum(v is not None for v in [public_id, slug]) != 1:
        typer.echo("Please provide a single identifier for rented instance - ID or name.")
        raise typer.Exit(1)

    if private_ssh_key_path and not Path(private_ssh_key_path).is_file():
        typer.echo(f'No file found at provided path {private_ssh_key_path}')
        raise typer.Exit(1)

    service_factory = validate_config_and_get_service_factory()
    instance_service: InstanceService = service_factory.get_instance_service()

    instance_service.connect_to_rented_instance(
        instance_rented_public_id=public_id,
        instance_rented_slug=slug,
        input_ssh_key_path=private_ssh_key_path
    )

    app_logger.info(f'Stop connecting to rented server instance')
    raise typer.Exit(0)


@self_hosted.command(name="ls", help=__("List self-hosted instances"), **get_command_metadata(CliCommand.INSTANCE_SELF_HOSTED_LS))
def self_hosted_list(
        row: int = typer.Option(
            5,
            '--row',
            '-r',
            help=__("Set number of rows displayed per page"),
            is_eager=False,
        ),
        page: int = typer.Option(
            1,
            '--page',
            '-p',
            help=__("Set starting page for displaying output"),
            is_eager=False,
        ),
        statuses: List[str] = typer.Option(
            None,
            '--status',
            '-s',
            help=__("Filter by status, use --status all to list all self-hosted server instances"),
            is_eager=False,
        ),
):
    command_name = CliCommand.INSTANCE_SELF_HOSTED_LS
    app_logger.info(f'Running {command_name} from {get_current_directory()}')
    check_command_permission(command_name)

    service_factory = validate_config_and_get_service_factory()
    instance_service: InstanceService = service_factory.get_instance_service()

    instance_service.print_self_hosted_instance_list(
        statuses=statuses,
        row=row,
        page=page
    )

    typer.echo(__("Self-hosted instances listing complete"))
    raise typer.Exit(0)


@self_hosted.command(name="connect", no_args_is_help=True, help=__("Connect to self-hosted instance"), **get_command_metadata(CliCommand.INSTANCE_SELF_HOSTED_CONNECT))
def self_hosted_connect(
        public_id: Optional[str] = typer.Option(
            None,
            '--self-hosted-instance-id',
            '-sid',
            help="Self-hosted instance ID",
            is_eager=False,
        ),
        slug: Optional[str] = typer.Option(
            None,
            '--self-hosted-instance-name',
            '-sn',
            help="Self-hosted instance name",
            is_eager=False,
        ),
        username: Optional[str] = typer.Option(
            None,
            '--username',
            '-u',
            help=__("Username for server instance (required when connecting to self-hosted instance)"),
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
    command_name = CliCommand.INSTANCE_SELF_HOSTED_CONNECT
    app_logger.info(f'Running {command_name} from {get_current_directory()}')
    check_command_permission(command_name)

    if sum(v is not None for v in [public_id, slug]) != 1:
        typer.echo("Please provide a single identifier for self-hosted instance - ID or name.")
        raise typer.Exit(1)

    if private_ssh_key_path and not Path(private_ssh_key_path).is_file():
        typer.echo(f'No file found at provided path {private_ssh_key_path}')
        raise typer.Exit(1)

    service_factory = validate_config_and_get_service_factory()
    instance_service: InstanceService = service_factory.get_instance_service()

    instance_service.connect_to_selfhosted_instance(
        selfhosted_instance_public_id=public_id,
        selfhosted_instance_slug=slug,
        username=username,
        input_ssh_key_path=private_ssh_key_path
    )

    app_logger.info(f'Stop connecting to self-hosted instance')
    raise typer.Exit(0)
