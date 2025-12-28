from typing import Callable

import typer

from thestage.cli_command import CliCommand, CliCommandAvailability
from thestage.color_scheme.color_scheme import ColorScheme
from thestage.config import config_storage
from rich import print


def cli_command(command_id: CliCommand):
    def decorator(func: Callable):
        setattr(func, "__cli_command__", command_id)
        return func
    return decorator


def get_command_metadata(command_id: CliCommand) -> dict:
    return {
        "rich_help_panel": get_command_help_panel(command_id),
        "deprecated": is_command_deprecated(command_id),
    }


def get_command_group_help_panel() -> str:
    return "Command Groups"


def get_command_help_panel(command: CliCommand) -> str:
    if config_storage.APP_CONFIG.runtime.allowed_commands.get(command) == CliCommandAvailability.ALLOWED:
        return "Allowed Commands"
    if config_storage.APP_CONFIG.runtime.allowed_commands.get(command) == CliCommandAvailability.RESTRICTED:
        return "Restricted Commands"
    if config_storage.APP_CONFIG.runtime.allowed_commands.get(command) == CliCommandAvailability.DEPRECATED:
        return "Deprecated Commands"


def is_command_deprecated(command: CliCommand) -> bool:
    if config_storage.APP_CONFIG.runtime.allowed_commands.get(command) == CliCommandAvailability.DEPRECATED:
        return True
    return False


def check_command_permission(executed_command: CliCommand):
    if config_storage.APP_CONFIG.runtime.is_token_valid == False and executed_command != CliCommand.CONFIG_SET:
        print(f"[{ColorScheme.WARNING.value}]Your API Token is not valid. You can update the token using 'thestage config set' command[{ColorScheme.WARNING.value}]")

    is_allowed = config_storage.APP_CONFIG.runtime.allowed_commands.get(executed_command) == CliCommandAvailability.ALLOWED
    if not is_allowed:
        typer.echo("Action is not allowed")
        raise typer.Exit(code=1)
