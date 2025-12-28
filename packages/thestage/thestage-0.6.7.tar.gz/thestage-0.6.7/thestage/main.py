from thestage.helpers import exception_hook
import traceback

from thestage.cli_command_helper import get_command_group_help_panel
from thestage.helpers.logger.app_logger import app_logger, get_log_path_from_os
from thestage.services.service_factory import ServiceFactory
from rich import print


def main():
    service_factory = ServiceFactory()
    config_provider = service_factory.get_config_provider()
    config = config_provider.build_config()

    try:
        try:
            api_client = service_factory.get_thestage_api_client()
            token_info = api_client.validate_token(config.main.thestage_auth_token)
            config_provider.update_allowed_commands_and_is_token_valid(validate_token_response=token_info)
        except Exception as e:
            app_logger.error(f'{traceback.format_exc()}')
            print('Error connecting to TheStage servers')  # TODO inquire what we want here if backend is offline
            print(f'Application logs path: {str(get_log_path_from_os())}')
            return

        from thestage.controllers import base_controller, container_controller, instance_controller, project_controller, \
            config_controller

        base_controller.app.add_typer(project_controller.app, name="project", rich_help_panel=get_command_group_help_panel())
        base_controller.app.add_typer(container_controller.app, name="container", rich_help_panel=get_command_group_help_panel())
        base_controller.app.add_typer(instance_controller.app, name="instance", rich_help_panel=get_command_group_help_panel())
        base_controller.app.add_typer(config_controller.app, name="config", rich_help_panel=get_command_group_help_panel())

        base_controller.app()
    except KeyboardInterrupt:
        print('THESTAGE: Keyboard Interrupt')
