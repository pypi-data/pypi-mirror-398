from typing import Optional

from thestage.services.config_provider.config_provider import ConfigProvider
from thestage.services.connect.connect_service import ConnectService
from thestage.services.filesystem_service import FileSystemService
from thestage.services.logging.logging_service import LoggingService
from thestage.services.project.project_service import ProjectService
from thestage.services.remote_server_service import RemoteServerService
from thestage.services.container.container_service import ContainerService
from thestage.services.instance.instance_service import InstanceService
from thestage.services.app_config_service import AppConfigService
from thestage.services.clients.git.git_client import GitLocalClient
from thestage.services.clients.thestage_api.api_client import TheStageApiClient
from thestage.services.validation_service import ValidationService


class ServiceFactory:
    __thestage_api_client: Optional[TheStageApiClient] = None
    __git_local_client: Optional[GitLocalClient] = None
    __file_system_service: Optional[FileSystemService] = None
    __config_provider: Optional[ConfigProvider] = None


    def get_validation_service(self) -> ValidationService:
        return ValidationService(
                thestage_api_client=self.get_thestage_api_client(),
                config_provider=self.get_config_provider(),
            )

    def get_instance_service(self) -> InstanceService:
        return InstanceService(
                thestage_api_client=self.get_thestage_api_client(),
                remote_server_service=self.get_remote_server_service(),
                config_provider=self.get_config_provider(),
            )

    def get_container_service(self) -> ContainerService:
        return ContainerService(
                thestage_api_client=self.get_thestage_api_client(),
                remote_server_service=self.get_remote_server_service(),
                file_system_service=self.get_file_system_service(),
                config_provider=self.get_config_provider(),
            )

    def get_connect_service(self) -> ConnectService:
        return ConnectService(
            thestage_api_client=self.get_thestage_api_client(),
            instance_service=self.get_instance_service(),
            container_service=self.get_container_service(),
            logging_service=self.get_logging_service(),
        )

    def get_project_service(self) -> ProjectService:
        return ProjectService(
            thestage_api_client=self.get_thestage_api_client(),
            remote_server_service=self.get_remote_server_service(),
            file_system_service=self.get_file_system_service(),
            git_local_client=self.get_git_local_client(),
            config_provider=self.get_config_provider(),
        )

    def get_remote_server_service(self) -> RemoteServerService:
        return RemoteServerService(
            file_system_service=self.get_file_system_service(),
            config_provider=self.get_config_provider(),
        )

    def get_thestage_api_client(self) -> TheStageApiClient:
        if not self.__thestage_api_client:
            self.__thestage_api_client = TheStageApiClient(config_provider=self.get_config_provider())
        return self.__thestage_api_client

    def get_git_local_client(self):
        if not self.__git_local_client:
            self.__git_local_client = GitLocalClient(file_system_service=self.get_file_system_service())
        return self.__git_local_client

    def get_file_system_service(self) -> FileSystemService:
        if not self.__file_system_service:
            self.__file_system_service = FileSystemService()
        return self.__file_system_service

    def get_app_config_service(self) -> AppConfigService:
        return AppConfigService(
            config_provider=self.get_config_provider(),
            validation_service=self.get_validation_service(),
        )

    def get_logging_service(self) -> LoggingService:
        return LoggingService(
            thestage_api_client=self.get_thestage_api_client(),
        )

    def get_config_provider(self) -> ConfigProvider:
        if not self.__config_provider:
            self.__config_provider = ConfigProvider(self.get_file_system_service())
        return self.__config_provider
