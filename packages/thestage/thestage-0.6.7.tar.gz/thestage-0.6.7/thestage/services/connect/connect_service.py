from typing import Optional
import typer

from thestage.cli_command import CliCommand
from thestage.cli_command_helper import check_command_permission
from thestage.color_scheme.color_scheme import ColorScheme
from thestage.i18n.translation import __
from thestage.services.clients.thestage_api.core.http_client_exception import HttpClientException
from thestage.services.clients.thestage_api.dtos.enums.instance_rented_status import InstanceRentedBusinessStatus
from thestage.services.abstract_service import AbstractService
from thestage.helpers.error_handler import error_handler
from thestage.services.clients.thestage_api.api_client import TheStageApiClient
from thestage.services.clients.thestage_api.dtos.instance_rented_response import InstanceRentedDto
from thestage.services.container.container_service import ContainerService
from thestage.services.instance.instance_service import InstanceService
from thestage.services.logging.logging_service import LoggingService
from rich import print


class ConnectService(AbstractService):
    __thestage_api_client: TheStageApiClient = None
    __instance_service: InstanceService = None
    __container_service: ContainerService = None
    __logging_service: LoggingService = None

    def __init__(
            self,
            thestage_api_client: TheStageApiClient,
            instance_service: InstanceService,
            container_service: ContainerService,
            logging_service: LoggingService,
    ):
        super(ConnectService, self).__init__(
        )
        self.__thestage_api_client = thestage_api_client
        self.__instance_service = instance_service
        self.__container_service = container_service
        self.__logging_service = logging_service


    @error_handler()
    def connect_to_entity(
            self,
            input_entity_identifier: str,
            username: Optional[str],
            private_key_path: Optional[str],
    ):
        resolved_options = self.__thestage_api_client.resolve_user_input(entity_identifier=input_entity_identifier)
        entities_available_for_connect_count = 0
        task_presence = False
        container_presence = False
        rented_presence = False
        selfhosted_presence = False
        resolved_entity_public_id = None

        if resolved_options.taskMatchData:
            for task_item in resolved_options.taskMatchData:
                message = f"Found a task with with matching {task_item.matchedField} in status: '{task_item.frontendStatus.status_translation}' (ID: {task_item.publicId})"
                line_color = ColorScheme.SUCCESS.value if task_item.canConnect else 'default'
                print(f"[{line_color}]{message}[{line_color}]")
                if task_item.canConnect:
                    task_presence = True
                    resolved_entity_public_id = task_item.publicId
                    entities_available_for_connect_count += 1

        if resolved_options.dockerContainerMatchData:
            for container_item in resolved_options.dockerContainerMatchData:
                message = f"Found a container with matching {container_item.matchedField} in status: '{container_item.frontendStatus.status_translation}' (ID: {container_item.publicId})"
                line_color = ColorScheme.SUCCESS.value if container_item.canConnect else 'default'
                print(f"[{line_color}]{message}[{line_color}]")
                if container_item.canConnect:
                    container_presence = True
                    resolved_entity_public_id = container_item.publicId
                    entities_available_for_connect_count += 1

        if resolved_options.instanceRentedMatchData:
            for instance_rented_item in resolved_options.instanceRentedMatchData:
                message = f"Found a rented instance with matching {instance_rented_item.matchedField} in status: '{instance_rented_item.frontendStatus.status_translation}'  (ID: {instance_rented_item.publicId})"
                line_color = ColorScheme.SUCCESS.value if instance_rented_item.canConnect else 'default'
                print(f"[{line_color}]{message}[{line_color}]")

                if instance_rented_item.canConnect:
                    rented_presence = True
                    resolved_entity_public_id = instance_rented_item.publicId
                    entities_available_for_connect_count += 1

        if resolved_options.selfhostedInstanceMatchData:
            for selfhosted_item in resolved_options.selfhostedInstanceMatchData:
                message = f"Found a self-hosted instance with matching {selfhosted_item.matchedField} in status: '{selfhosted_item.frontendStatus.status_translation}' (ID: {selfhosted_item.publicId})"
                line_color = ColorScheme.SUCCESS.value if selfhosted_item.canConnect else 'default'
                print(f"[{line_color}]{message}[{line_color}]")

                if selfhosted_item.canConnect:
                    selfhosted_presence = True
                    resolved_entity_public_id = selfhosted_item.publicId
                    entities_available_for_connect_count += 1

        if entities_available_for_connect_count > 1:
            typer.echo("Provided identifier caused ambiguity")
            typer.echo("Consider running a dedicated command to connect to the entity you need")
            raise typer.Exit(code=1)

        if entities_available_for_connect_count == 0:
            typer.echo("There is nothing to connect to with the provided identifier")
            raise typer.Exit(code=1)

        if rented_presence:
            check_command_permission(CliCommand.INSTANCE_RENTED_CONNECT)
            typer.echo(f"Connecting to rented instance '{resolved_entity_public_id}'...")
            self.__instance_service.connect_to_rented_instance(
                instance_rented_public_id=resolved_entity_public_id,
                instance_rented_slug=None,
                input_ssh_key_path=private_key_path
            )

        if container_presence:
            check_command_permission(CliCommand.CONTAINER_CONNECT)
            typer.echo(f"Connecting to docker container '{resolved_entity_public_id}'...")
            self.__container_service.connect_to_container(
                container_public_id=resolved_entity_public_id,
                container_slug=None,
                username=username,
                input_ssh_key_path=private_key_path
            )

        if selfhosted_presence:
            check_command_permission(CliCommand.INSTANCE_SELF_HOSTED_CONNECT)
            typer.echo(f"Connecting to self-hosted instance '{resolved_entity_public_id}'...")

            self.__instance_service.connect_to_selfhosted_instance(
                selfhosted_instance_public_id=resolved_entity_public_id,
                selfhosted_instance_slug=None,
                username=username,
                input_ssh_key_path=private_key_path
            )

        if task_presence:
            typer.echo(f"Connecting to task '{resolved_entity_public_id}'...")
            self.__logging_service.stream_task_logs_with_controls(task_public_id=resolved_entity_public_id)


    @error_handler()
    def upload_ssh_key(self, public_key_contents: str, instance_public_id: Optional[str], instance_slug: Optional[str]):
        instance_rented: Optional[InstanceRentedDto] = None
        if instance_slug or instance_public_id:
            try:
                instance_rented = self.__thestage_api_client.get_rented_instance(
                    instance_public_id=instance_public_id,
                    instance_slug=instance_slug
                )
            except HttpClientException as e:
                instance_rented = None

            # if no instances found - exit 1
            if instance_rented is None:
                typer.echo(f"No rented instance found with matching identifier")
                raise typer.Exit(1)

        note_to_send: Optional[str] = None

        is_user_already_has_key_response = self.__thestage_api_client.is_user_has_ssh_public_key(
            public_key=public_key_contents
        )

        ssh_key_pair_public_id = is_user_already_has_key_response.sshKeyPairPublicId
        is_adding_key_to_user = not is_user_already_has_key_response.isUserHasPublicKey

        if is_adding_key_to_user and not note_to_send:
            note_to_send: str = typer.prompt(
                text=__('SSH key will be added to your profile. Please provide a title for this key'),
                show_choices=False,
                type=str,
                show_default=False,
            )

        if not is_adding_key_to_user and not instance_rented:
            typer.echo("Key already exists on your profile")

        if is_adding_key_to_user:
            add_ssh_key_to_user_response = self.__thestage_api_client.add_public_ssh_key_to_user(
                public_key=public_key_contents,
                note=note_to_send
            )
            typer.echo(f"Public key '{note_to_send}' added to your profile")
            ssh_key_pair_public_id = add_ssh_key_to_user_response.sshKeyPairPublicId

        if instance_rented:
            self.__thestage_api_client.add_public_ssh_key_to_instance_rented(
                instance_rented_public_id=instance_rented.public_id,
                ssh_key_pair_public_id=ssh_key_pair_public_id
            )

            if instance_rented.frontend_status.status_key != InstanceRentedBusinessStatus.ONLINE:
                typer.echo(f"Rented instance '{instance_rented.slug}' status is '{instance_rented.frontend_status.status_translation}'. Key will be added as soon as it is back online.")
            else:
                typer.echo(f"Public key added to rented instance '{instance_rented.slug}'")
