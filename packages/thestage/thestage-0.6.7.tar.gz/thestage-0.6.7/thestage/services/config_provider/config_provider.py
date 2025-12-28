import typer

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

from thestage.cli_command import CliCommand, CliCommandAvailability, ALWAYS_AVAILABLE_COMMANDS
from thestage.services.clients.thestage_api.dtos.validate_token_response import ValidateTokenResponse
from thestage.services.core_files.config_entity import ConfigEntity
from thestage.helpers.ssh_util import parse_private_key
from thestage.services.connect.dto.remote_server_config import RemoteServerConfig
from thestage.services.filesystem_service import FileSystemService
from thestage.services.project.dto.project_config import ProjectConfig
from thestage.config import THESTAGE_CONFIG_DIR, THESTAGE_CONFIG_FILE, THESTAGE_AUTH_TOKEN, THESTAGE_API_URL, \
    config_storage


class ConfigProvider:
    _file_system_service = FileSystemService


    def __init__(
            self,
            file_system_service: FileSystemService,
    ):
        self._file_system_service = file_system_service

        global_config_path = self.get_global_config_path()
        if not global_config_path.exists():
            self._file_system_service.create_if_not_exists_dir(global_config_path)

        global_config_file = self.get_global_config_file()
        self._file_system_service.create_if_not_exists_file(global_config_file)


    # must be called right after the app is started
    def build_config(self) -> ConfigEntity:
        config_values = {}

        config_from_env = {}
        config_from_env['main'] = {}
        if THESTAGE_AUTH_TOKEN:
            config_from_env['main']['thestage_auth_token'] = THESTAGE_AUTH_TOKEN
        if THESTAGE_API_URL:
            config_from_env['main']['thestage_api_url'] = THESTAGE_API_URL

        if config_from_env:
            self.__update_config_values_dict(values_to_update=config_values, new_values=config_from_env)

        config_from_file = self._file_system_service.read_config_file(self.get_global_config_file())
        if config_from_file:
            self.__update_config_values_dict(values_to_update=config_values, new_values=config_from_file)

        config = ConfigEntity.model_validate(config_values)
        config.runtime.config_global_path = str(self.get_global_config_path())

        config_storage.APP_CONFIG = config

        return config


    def get_config(self) -> ConfigEntity:
        if not config_storage.APP_CONFIG:
            raise Exception('Config storage was not initialized')
        return config_storage.APP_CONFIG


    def save_project_config(self, project_config: ProjectConfig):
        project_data_dirpath = self.__get_project_config_path(with_file=False)
        self._file_system_service.create_if_not_exists_dir(project_data_dirpath)

        project_data_filepath = self.__get_project_config_path(with_file=True)
        self._file_system_service.create_if_not_exists_file(project_data_filepath)

        self.__save_config_file(data=project_config.model_dump(), file_path=project_data_filepath)


    def save_project_deploy_ssh_key(self, deploy_ssh_key: str, project_public_id: str) -> str:
        deploy_key_dirpath = self.get_global_config_path().joinpath('project_deploy_keys')
        self._file_system_service.create_if_not_exists_dir(deploy_key_dirpath)

        deploy_key_filepath = deploy_key_dirpath.joinpath(f'project_deploy_key__{project_public_id}')
        self._file_system_service.create_if_not_exists_file(deploy_key_filepath)

        text_file = open(deploy_key_filepath, "w")
        text_file.write(deploy_ssh_key)
        text_file.close()
        os.chmod(deploy_key_filepath, 0o600)

        return str(deploy_key_filepath)


    def read_project_config(self) -> Optional[ProjectConfig]:
        project_data_dirpath = self.__get_project_config_path()
        if not project_data_dirpath.exists():
            return None

        project_data_filepath = self.__get_project_config_path(with_file=True)
        if not project_data_filepath.exists():
            return None

        config_data = self._file_system_service.read_config_file(project_data_filepath) if project_data_filepath and project_data_filepath.exists() else {}
        return ProjectConfig.model_validate(config_data)


    def __get_project_config_path(self, with_file: bool = False) -> Path:
        if with_file:
            return Path(self.get_config().runtime.working_directory).joinpath(THESTAGE_CONFIG_DIR).joinpath('project.json')
        else:
            return Path(self.get_config().runtime.working_directory).joinpath(THESTAGE_CONFIG_DIR)


    def __get_remote_server_config_path(self) -> Path:
        return self.get_global_config_path().joinpath('remote_server_config.json')


    def update_remote_server_config_entry(self, ip_address: str, ssh_key_path: Optional[Path]):
        # double checking if key is parseable (fails if key is encrypted)
        # see remote_server_service for similar check
        if ssh_key_path:
            pkey = parse_private_key(str(ssh_key_path))

            if pkey is None:
                typer.echo("Could not identify provided private key (expected RSA, ECDSA, ED25519)")
                raise typer.Exit(1)

        config = self.__read_remote_server_config()
        remote_server_config_filepath = self.__get_remote_server_config_path()
        if config:
            if not config.ip_address_to_ssh_key_map:
                config.ip_address_to_ssh_key_map = {}

            existing_path = config.ip_address_to_ssh_key_map.get(ip_address)
            if ssh_key_path and existing_path != str(ssh_key_path):
                config.ip_address_to_ssh_key_map.update({ip_address: str(ssh_key_path)})
                typer.echo(f'Updated ssh key for {ip_address}: {ssh_key_path}')

            if not ssh_key_path and existing_path:
                typer.echo(f"Private key at path {existing_path} was not found")
                config.ip_address_to_ssh_key_map.pop(ip_address, None)
        else:
            self._file_system_service.create_if_not_exists_file(remote_server_config_filepath)
            config = RemoteServerConfig(ip_address_to_ssh_key_map={ip_address: str(ssh_key_path)})

        self.__save_config_file(data=config.model_dump(), file_path=remote_server_config_filepath)

        return str(remote_server_config_filepath)


    def __read_remote_server_config(self) -> Optional[RemoteServerConfig]:
        config_filepath = self.__get_remote_server_config_path()
        if not config_filepath.is_file():
            return None

        config_data = self._file_system_service.read_config_file(config_filepath) if config_filepath and config_filepath.exists() else {}
        return RemoteServerConfig.model_validate(config_data)


    def get_valid_private_key_path_by_ip_address(self, ip_address: str) -> Optional[str]:
        remote_server_config = self.__read_remote_server_config()
        if remote_server_config and remote_server_config.ip_address_to_ssh_key_map:
            private_key_path = remote_server_config.ip_address_to_ssh_key_map.get(ip_address)
            if private_key_path and Path(private_key_path).is_file():
                return private_key_path
            elif private_key_path:
                self.update_remote_server_config_entry(ip_address, None)
        return None


    @staticmethod
    def __update_config_values_dict(values_to_update: Dict, new_values: Dict):
        if 'main' in new_values:
            if 'main' in values_to_update:
                values_to_update['main'].update(new_values['main'])
            else:
                values_to_update['main'] = new_values['main']

    @staticmethod
    def __save_config_file(data: Dict, file_path: Path):
        with open(file_path, 'w') as configfile:
            json.dump(data, configfile, indent=1)


    def save_config(self):
        config = self.get_config()
        global_config_file = self.get_global_config_file()
        data: Dict[str, Any] = self._file_system_service.read_config_file(global_config_file)
        data.update(config.model_dump(exclude_none=True, by_alias=True, exclude={'runtime', 'RUNTIME', 'daemon', 'DAEMON'}))
        self.__save_config_file(data=data, file_path=global_config_file)


    def clear_config(self, ):
        global_config_path = self.get_global_config_path()
        if global_config_path.exists():
            self._file_system_service.remove_folder(str(global_config_path))

        os.unsetenv('THESTAGE_CONFIG_DIR')
        os.unsetenv('THESTAGE_CONFIG_FILE')
        os.unsetenv('THESTAGE_CLI_ENV')
        os.unsetenv('THESTAGE_API_URL')
        os.unsetenv('THESTAGE_LOG_FILE')
        os.unsetenv('THESTAGE_AUTH_TOKEN')


    def update_config(self, updated_config: ConfigEntity):
        config_storage.APP_CONFIG = updated_config

    def get_global_config_path(self) -> Path:
        home_dir = self._file_system_service.get_home_path()
        return home_dir.joinpath(THESTAGE_CONFIG_DIR)

    def get_global_config_file(self) -> Path:
        return self.get_global_config_path().joinpath(THESTAGE_CONFIG_FILE)


    def update_allowed_commands_and_is_token_valid(self, validate_token_response: ValidateTokenResponse):
        config = self.get_config()
        for cli_command_item in CliCommand:
            is_command_available = validate_token_response.allowedCliCommands.get(cli_command_item)
            command_availability = CliCommandAvailability.DEPRECATED

            if cli_command_item in ALWAYS_AVAILABLE_COMMANDS:
                command_availability = CliCommandAvailability.ALLOWED
            else:
                if is_command_available is True:
                    command_availability = CliCommandAvailability.ALLOWED
                if is_command_available is False:
                    command_availability = CliCommandAvailability.RESTRICTED
            config.runtime.allowed_commands.update({cli_command_item: command_availability})
            config.runtime.is_token_valid = validate_token_response.is_success
        self.update_config(config)


    def is_cli_command_allowed(self, cli_command: CliCommand) -> bool:
        config = self.get_config()
        return True if config.runtime.allowed_commands.get(cli_command) == CliCommandAvailability.ALLOWED else False
