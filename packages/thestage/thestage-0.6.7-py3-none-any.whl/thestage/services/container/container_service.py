import re
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from rich import print

import typer

from thestage.color_scheme.color_scheme import ColorScheme
from thestage.entities.container import DockerContainerEntity
from thestage.services.clients.thestage_api.dtos.container_param_request import DockerContainerActionRequestDto
from thestage.services.clients.thestage_api.dtos.enums.container_pending_action import DockerContainerAction
from thestage.services.clients.thestage_api.dtos.enums.container_status import DockerContainerStatus
from thestage.entities.enums.shell_type import ShellType
from thestage.services.clients.thestage_api.dtos.paginated_entity_list import PaginatedEntityList
from thestage.services.container.mapper.container_mapper import ContainerMapper
from thestage.services.filesystem_service import FileSystemService
from thestage.services.remote_server_service import RemoteServerService
from thestage.i18n.translation import __
from thestage.services.abstract_service import AbstractService
from thestage.services.clients.thestage_api.dtos.container_response import DockerContainerDto
from thestage.helpers.error_handler import error_handler
from thestage.services.clients.thestage_api.api_client import TheStageApiClient
from thestage.services.config_provider.config_provider import ConfigProvider


class ContainerService(AbstractService):

    __thestage_api_client: TheStageApiClient = None
    __config_provider: ConfigProvider = None

    def __init__(
            self,
            thestage_api_client: TheStageApiClient,
            config_provider: ConfigProvider,
            remote_server_service: RemoteServerService,
            file_system_service: FileSystemService,
    ):
        self.__config_provider = config_provider
        self.__thestage_api_client = thestage_api_client
        self.__remote_server_service = remote_server_service
        self.__file_system_service = file_system_service


    @error_handler()
    def print_container_list(
            self,
            row: int,
            page: int,
            project_public_id: Optional[str],
            project_slug: Optional[str],
            statuses: List[str],
    ):
        container_status_map = self.__thestage_api_client.get_container_business_status_map()

        if not statuses:
            statuses = ({key: container_status_map[key] for key in [
                DockerContainerStatus.RUNNING,
                DockerContainerStatus.STARTING,
            ]}).values()

        if "all" in statuses:
            statuses = container_status_map.values()

        for input_status_item in statuses:
            if input_status_item not in container_status_map.values():
                typer.echo(__("'%invalid_status%' is not one of %valid_statuses%", {
                    'invalid_status': input_status_item,
                    'valid_statuses': str(list(container_status_map.values()))
                }))
                raise typer.Exit(1)

        typer.echo(__(
            "Listing containers with the following statuses: %statuses%. To list all containers, use --status all",
            placeholders={
                'statuses': ', '.join([input_status_item for input_status_item in statuses])
            }))

        backend_statuses: List[str] = [key for key, value in container_status_map.items() if value in statuses]

        self.print(
            func_get_data=self.get_list,
            func_special_params={
                'statuses': backend_statuses,
                'project_slug': project_slug,
                'project_public_id': project_public_id,
            },
            mapper=ContainerMapper(),
            headers=list(map(lambda x: x.alias, DockerContainerEntity.model_fields.values())),
            row=row,
            page=page,
            max_col_width=[35, 20, 25],
            show_index="never",
        )


    @error_handler()
    def get_list(
            self,
            statuses: List[str],
            row: int = 5,
            page: int = 1,
            project_public_id: Optional[str] = None,
            project_slug: Optional[str] = None,
    ) -> PaginatedEntityList[DockerContainerDto]:

        list = self.__thestage_api_client.get_container_list(
            statuses=statuses,
            page=page,
            limit=row,
            project_public_id=project_public_id,
            project_slug=project_slug
        )

        return list

    # TODO delete this proxy method
    @error_handler()
    def get_container(
            self,
            container_public_id: Optional[str] = None,
            container_slug: Optional[str] = None,
    ) -> Optional[DockerContainerDto]:
        return self.__thestage_api_client.get_container(
            container_public_id=container_public_id,
            container_slug=container_slug,
        )

    def get_server_auth(
            self,
            container: DockerContainerDto,
            username_param: Optional[str],
            private_key_path_override: Optional[str],
    ) -> Tuple[str, str, Optional[str]]:
        username = None
        if container.instance_rented:
            username = container.instance_rented.host_username
            ip_address = container.instance_rented.ip_address
        elif container.selfhosted_instance:
            ip_address = container.selfhosted_instance.ip_address
        else:
            typer.echo(__("Neither rented nor self-hosted server instance found to connect to"))
            raise typer.Exit(1)

        if username_param:
            username = username_param

        if not username:
            username = 'root'
            typer.echo(__("No remote server username provided, using 'root' as username"))

        private_key_path = private_key_path_override
        if not private_key_path:
            private_key_path = self.__config_provider.get_valid_private_key_path_by_ip_address(ip_address)
            if private_key_path:
                typer.echo(f'Using configured private key for {ip_address}: {private_key_path}')
            else:
                typer.echo(f'Using SSH agent to connect to {ip_address} as {username}')
        else:
            self.__config_provider.update_remote_server_config_entry(ip_address, Path(private_key_path))
            typer.echo(f'Updated private key path for {ip_address}: {private_key_path}')

        return username, ip_address, private_key_path

    @error_handler()
    def connect_to_container(
            self,
            container_public_id: Optional[str],
            container_slug: Optional[str],
            username: Optional[str],
            input_ssh_key_path: Optional[str],
    ):
        container: Optional[DockerContainerDto] = self.get_container(
            container_public_id=container_public_id,
            container_slug=container_slug,
        )

        if not container:
            typer.echo(f"Container not found")
            raise typer.Exit(1)

        self.check_if_container_running(
            container=container
        )

        if not container.system_name:
            typer.echo(__("Unable to connect to container: container system_name is missing"))
            raise typer.Exit(1)

        starting_directory: str = '/'
        workspace_mappings = {v for v in container.mappings.directory_mappings.values() if v.startswith('/workspace/') or v == '/workspace'}
        if len(workspace_mappings) > 0:
            starting_directory = '/workspace'

        inference_mappings = {v for v in container.mappings.directory_mappings.values() if v.startswith('/opt/') or v == '/opt'}
        if len(inference_mappings) > 0:
            starting_directory = '/opt/project'

        username, ip_address, private_key_path = self.get_server_auth(
            container=container,
            username_param=username,
            private_key_path_override=input_ssh_key_path
        )

        shell: Optional[ShellType] = self.__remote_server_service.get_shell_from_container(
            ip_address=ip_address,
            username=username,
            container_name=container.system_name,
            private_key_path=private_key_path
        )

        if not shell:
            typer.echo(f"Failed to start shell (bash, sh) in container: ensure user '{username}' has Docker access and compatible shell is available")
            raise typer.Exit(1)

        self.__remote_server_service.connect_to_container(
            ip_address=ip_address,
            username=username,
            docker_name=container.system_name,
            starting_directory=starting_directory,
            shell=shell,
            private_key_path=private_key_path
        )

    @error_handler()
    def check_if_container_stopped(
            self,
            container: DockerContainerDto,
    ) -> DockerContainerDto:
        if container.frontend_status.status_key not in [
            DockerContainerStatus.STOPPED.value,
        ]:
            typer.echo(__(f'Container is not stopped (status: \'{container.frontend_status.status_translation}\')'))
            raise typer.Exit(1)

        return container

    @error_handler()
    def check_if_container_running(
            self,
            container: DockerContainerDto,
    ):
        if container.frontend_status.status_key not in [
            DockerContainerStatus.RUNNING.value,
            DockerContainerStatus.BUSY.value,
        ]:
            typer.echo(__(f'Container is not running (status: \'{container.frontend_status.status_translation}\')'))
            raise typer.Exit(1)


    @staticmethod
    def _get_new_path_from_mapping(
            directory_mapping: Dict[str, str],
            destination_path: str,
    ) -> Tuple[Optional[str], Optional[str]]:

        instance_path: Optional[str] = None
        container_path: Optional[str] = None

        for instance_mapping, container_mapping in directory_mapping.items():
            if destination_path.startswith(f"{container_mapping}/") or destination_path == container_mapping:
                instance_path = destination_path.replace(container_mapping, instance_mapping)
                container_path = destination_path
                # dont break, check all mapping list

        if instance_path and container_path:
            return instance_path, container_path
        else:
            return None, None


    @error_handler()
    def put_file_to_container(
            self,
            source_path: str,
            destination: str,
            username_param: Optional[str],
    ):
        container_args = re.match(r"^([\w\W]+?):([\w\W]+)$", destination)
        if container_args is None:
            typer.echo(__('Container name and source file path are required as the second argument'))
            typer.echo(__('Example: container_name:/path/to/file'))
            raise typer.Exit(1)
        container_identifier = container_args.groups()[0]
        destination_path = container_args.groups()[1].rstrip("/")

        if not container_identifier:
            typer.echo('Container identifier (container_id_or_name) is required')
            raise typer.Exit(1)

        resolved_options = self.__thestage_api_client.resolve_user_input(entity_identifier=container_identifier)
        container_public_id = None
        valid_container_count = 0
        for container_item in resolved_options.dockerContainerMatchData:
            message = f"Found a container with matching {container_item.matchedField} in status: '{container_item.frontendStatus.status_translation}' (ID: {container_item.publicId})"
            line_color = ColorScheme.SUCCESS.value if container_item.canDownloadUploadOnContainer else 'default'
            print(f"[{line_color}]{message}[{line_color}]")
            if container_item.canDownloadUploadOnContainer:
                valid_container_count += 1
                container_public_id = container_item.publicId

        if valid_container_count != 1:
            typer.echo(f"Failed to resolve the container by provided identifier, as total of {valid_container_count} containers are valid options")
            raise typer.Exit(1)

        container: Optional[DockerContainerDto] = self.__thestage_api_client.get_container(
            container_public_id=container_public_id,
        )

        if not container:
            typer.echo(f"Unexpected error: container '{container_public_id}' not found")
            raise typer.Exit(1)

        if not self.__file_system_service.check_if_path_exist(file=source_path):
            typer.echo(__("File not found at specified path"))
            raise typer.Exit(1)

        if not container.mappings or not container.mappings.directory_mappings:
            typer.echo(__("Mapping folders not found"))
            raise typer.Exit(1)

        instance_path, container_path = self._get_new_path_from_mapping(
            directory_mapping=container.mappings.directory_mappings,
            destination_path=destination_path,
        )

        if not instance_path and not container_path:
            typer.echo(__("Cannot find matching container volume mapping for specified file path"))
            raise typer.Exit(1)

        username, ip_address, private_key_path = self.get_server_auth(
            container=container,
            username_param=username_param,
            private_key_path_override=None
        )

        copy_only_folder_contents = source_path.endswith("/")

        self.__remote_server_service.upload_data_to_container(
            ip_address=ip_address,
            username=username,
            src_path=source_path,
            dest_path=destination_path,
            instance_path=instance_path,
            container_path=container_path,
            copy_only_folder_contents=copy_only_folder_contents,
            private_key_path=private_key_path,
        )

    @error_handler()
    def get_file_from_container(
            self,
            source: str,
            destination_path: str,
            username_param: Optional[str] = None,
    ):
        container_args = re.match(r"^([\w\W]+?):([\w\W]+)$", source)

        if container_args is None:
            typer.echo(__('Container name and source directory path are required as the first argument'))
            typer.echo(__('Example: container_name:/path/to/file'))
            raise typer.Exit(1)
        container_identifier = container_args.groups()[0]
        source_path = container_args.groups()[1]

        if not container_identifier:
            typer.echo('Container identifier (container_id_or_name) is required')
            raise typer.Exit(1)

        resolved_options = self.__thestage_api_client.resolve_user_input(entity_identifier=container_identifier)
        container_public_id = None
        valid_container_count = 0
        for container_item in resolved_options.dockerContainerMatchData:
            message = f"Found a container with matching {container_item.matchedField} in status: '{container_item.frontendStatus.status_translation}' (ID: {container_item.publicId})"
            line_color = ColorScheme.SUCCESS.value if container_item.canDownloadUploadOnContainer else 'default'
            print(f"[{line_color}]{message}[{line_color}]")
            if container_item.canDownloadUploadOnContainer:
                valid_container_count += 1
                container_public_id = container_item.publicId

        if valid_container_count != 1:
            typer.echo(f"Failed to resolve the container by provided identifier, as total of {valid_container_count} containers are valid options")
            raise typer.Exit(1)

        container: Optional[DockerContainerDto] = self.__thestage_api_client.get_container(
            container_public_id=container_public_id,
        )

        if not container:
            typer.echo(f"Unexpected error: container '{container_public_id}' not found")
            raise typer.Exit(1)

        if not container.mappings or not container.mappings.directory_mappings:
            typer.echo(__("Mapping folders not found"))
            raise typer.Exit(1)

        instance_path, container_path = self._get_new_path_from_mapping(
            directory_mapping=container.mappings.directory_mappings,
            destination_path=source_path,
        )

        if not instance_path and not container_path:
            typer.echo(__("Cannot find matching container volume mapping for specified file path"))
            raise typer.Exit(1)

        username, ip_address, private_key_path = self.get_server_auth(
            container=container,
            username_param=username_param,
            private_key_path_override=None,
        )

        copy_only_folder_contents=source_path.endswith("/")

        self.__remote_server_service.download_data_from_container(
            ip_address=ip_address,
            username=username,
            dest_path=destination_path,
            instance_path=instance_path,
            copy_only_folder_contents=copy_only_folder_contents,
            private_key_path=private_key_path,
        )


    @error_handler()
    def request_docker_container_action(
            self,
            container_public_id: Optional[str],
            container_slug: Optional[str],
            action: DockerContainerAction,
    ):
        container: Optional[DockerContainerDto] = self.get_container(
            container_public_id=container_public_id,
            container_slug=container_slug,
        )
        if not container:
            typer.echo(f"Container not found")
            raise typer.Exit(1)

        if action == DockerContainerAction.START:
            self.check_if_container_stopped(container=container)

        if action in [DockerContainerAction.STOP, DockerContainerAction.RESTART]:
            self.check_if_container_running(container=container)

        request_params = DockerContainerActionRequestDto(
            dockerContainerPublicId=container.public_id,
            action=action,
        )
        result = self.__thestage_api_client.container_action(
            request_param=request_params,
        )

        if result.is_success:
            typer.echo(f'Docker container action scheduled: {action.value}')
