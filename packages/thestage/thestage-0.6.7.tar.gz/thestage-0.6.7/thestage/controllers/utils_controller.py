import os
import pathlib
from typing import Optional

from thestage.helpers.error_handler import error_handler
from thestage.services.service_factory import ServiceFactory


def get_current_directory() -> pathlib.Path:
    return pathlib.Path.cwd()


@error_handler()
def validate_config_and_get_service_factory(
        working_directory: Optional[str] = None,
) -> ServiceFactory:
    local_path = get_current_directory() if not working_directory else os.path.abspath(working_directory)

    service_factory = ServiceFactory()
    config_provider = service_factory.get_config_provider()

    config = config_provider.get_config()
    config.runtime.working_directory = str(local_path)

    config_provider.update_config(updated_config=config)

    validation_service = service_factory.get_validation_service()

    validation_service.check_token()
    config_provider.save_config()

    return service_factory
