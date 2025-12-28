import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List

import json

import boto3
import click
import typer
from git import Commit
from tabulate import tabulate

from thestage.entities.project_inference_simulator import ProjectInferenceSimulatorEntity
from thestage.entities.project_inference_simulator_model import ProjectInferenceSimulatorModelEntity
from thestage.entities.project_task import ProjectTaskEntity
from thestage.services.clients.thestage_api.core.http_client_exception import HttpClientException
from thestage.services.clients.thestage_api.dtos.enums.inference_model_status import InferenceModelStatus
from thestage.services.clients.thestage_api.dtos.enums.inference_simulator_status import InferenceSimulatorStatus
from thestage.color_scheme.color_scheme import ColorScheme
from thestage.entities.enums.yes_no_response import YesOrNoResponse
from thestage.exceptions.git_access_exception import GitAccessException
from thestage.i18n.translation import __
from thestage.services.clients.git.git_client import GitLocalClient
from thestage.services.clients.thestage_api.dtos.container_response import DockerContainerDto
from thestage.services.clients.thestage_api.dtos.enums.container_status import DockerContainerStatus
from thestage.services.clients.thestage_api.dtos.inference_controller.deploy_inference_model_to_instance_response import \
    DeployInferenceModelToInstanceResponse
from thestage.services.clients.thestage_api.dtos.inference_controller.deploy_inference_model_to_sagemaker_response import \
    DeployInferenceModelToSagemakerResponse
from thestage.services.clients.thestage_api.dtos.inference_controller.get_inference_simulator_response import \
    GetInferenceSimulatorResponse
from thestage.services.clients.thestage_api.dtos.paginated_entity_list import PaginatedEntityList
from thestage.services.clients.thestage_api.dtos.project_controller.project_push_inference_simulator_model_response import \
    ProjectPushInferenceSimulatorModelResponse
from thestage.services.clients.thestage_api.dtos.project_controller.project_run_task_response import \
    ProjectRunTaskResponse
from thestage.services.clients.thestage_api.dtos.project_controller.project_start_inference_simulator_response import \
    ProjectStartInferenceSimulatorResponse
from thestage.services.clients.thestage_api.dtos.project_response import ProjectDto
from thestage.services.clients.thestage_api.dtos.task_controller.task_view_response import TaskViewResponse
from thestage.services.filesystem_service import FileSystemService
from thestage.services.project.dto.inference_simulator_dto import InferenceSimulatorDto
from thestage.services.project.dto.inference_simulator_model_dto import InferenceSimulatorModelDto
from thestage.services.project.mapper.project_inference_simulator_mapper import ProjectInferenceSimulatorMapper
from thestage.services.project.mapper.project_inference_simulator_model_mapper import \
    ProjectInferenceSimulatorModelMapper
from thestage.services.task.dto.task_dto import TaskDto
from thestage.services.project.dto.project_config import ProjectConfig
from thestage.services.project.mapper.project_task_mapper import ProjectTaskMapper
from thestage.services.remote_server_service import RemoteServerService
from thestage.services.abstract_service import AbstractService
from thestage.helpers.error_handler import error_handler
from thestage.services.clients.thestage_api.api_client import TheStageApiClient
from thestage.services.config_provider.config_provider import ConfigProvider
from rich import print


class ProjectService(AbstractService):
    __thestage_api_client: TheStageApiClient = None
    __config_provider: ConfigProvider = None

    def __init__(
            self,
            thestage_api_client: TheStageApiClient,
            config_provider: ConfigProvider,
            remote_server_service: RemoteServerService,
            file_system_service: FileSystemService,
            git_local_client: GitLocalClient,
    ):
        self.__thestage_api_client = thestage_api_client
        self.__remote_server_service = remote_server_service
        self.__file_system_service = file_system_service
        self.__git_local_client = git_local_client
        self.__project_task_mapper = ProjectTaskMapper()
        self.__config_provider = config_provider


    @error_handler()
    def init_project(
            self,
            project_slug: Optional[str] = None,
            project_public_id: Optional[str] = None,
    ):
        config = self.__config_provider.get_config()
        project: Optional[ProjectDto] = self.__thestage_api_client.get_project(
            slug=project_slug,
            public_id=project_public_id,
        )

        if not project:
            typer.echo('Project not found')
            raise typer.Exit(1)

        is_git_folder = self.__git_local_client.is_present_local_git(
            path=config.runtime.working_directory,
        )
        if is_git_folder:
            has_remote = self.__git_local_client.has_remote(
                path=config.runtime.working_directory,
            )
            if has_remote:
                typer.echo(__('You have local repo with remote, we can not work with this'))
                raise typer.Exit(1)

        if not project.git_repository_url:
            typer.echo(__('Sketch dont have git repository url'))
            raise typer.Exit(1)

        if project.last_commit_hash or project.last_commit_description:
            continue_with_non_empty_repo: YesOrNoResponse = typer.prompt(
                text=__('Remote repository is probably not empty: latest commit is "{commit_description}" (sha: {commit_hash})\nDo you wish to continue?').format(commit_description=project.last_commit_description, commit_hash=project.last_commit_hash),
                show_choices=True,
                default=YesOrNoResponse.YES.value,
                type=click.Choice([r.value for r in YesOrNoResponse]),
                show_default=True,
            )
            if continue_with_non_empty_repo == YesOrNoResponse.NO:
                typer.echo(__('Project init aborted'))
                raise typer.Exit(0)

        deploy_ssh_key = self.__thestage_api_client.get_project_deploy_ssh_key(
            public_id=project.public_id,
        )

        deploy_key_path = self.__config_provider.save_project_deploy_ssh_key(
            deploy_ssh_key=deploy_ssh_key,
            project_public_id=project.public_id,
        )

        if is_git_folder:
            has_changes = self.__git_local_client.has_changes_with_untracked(
                path=config.runtime.working_directory,
            )
            if has_changes:
                typer.echo(__('You local repo has changes and not empty, please create empty folder'))
                raise typer.Exit(1)
        else:
            repo = self.__git_local_client.init_repository(
                path=config.runtime.working_directory,
            )

        is_remote_added = self.__git_local_client.add_remote_to_repo(
            path=config.runtime.working_directory,
            remote_url=project.git_repository_url,
            remote_name=project.git_repository_name,
        )
        if not is_remote_added:
            typer.echo(__('We can not add remote, something wrong'))
            raise typer.Exit(2)

        self.__git_local_client.git_fetch(path=config.runtime.working_directory, deploy_key_path=deploy_key_path)

        self.__git_local_client.init_gitignore(path=config.runtime.working_directory)

        self.__git_local_client.git_add_all(repo_path=config.runtime.working_directory)

        project_config = ProjectConfig()
        project_config.public_id = project.public_id
        project_config.slug = project.slug
        project_config.git_repository_url = project.git_repository_url
        project_config.deploy_key_path = str(deploy_key_path)
        self.__config_provider.save_project_config(project_config=project_config)

        typer.echo(__("Project successfully initialized at %path%", {"path": config.runtime.working_directory}))


    @error_handler()
    def clone_project(
            self,
            project_slug: str,
            project_public_id: str
    ):
        config = self.__config_provider.get_config()
        project: Optional[ProjectDto] = self.__thestage_api_client.get_project(
            slug=project_slug,
            public_id=project_public_id
        )

        if not project:
            typer.echo('Project not found')
            raise typer.Exit(1)

        if not self.__file_system_service.is_folder_empty(folder=config.runtime.working_directory, auto_create=True):
            typer.echo(__("Cannot clone: the folder is not empty"))
            raise typer.Exit(1)

        is_git_folder = self.__git_local_client.is_present_local_git(
            path=config.runtime.working_directory,
        )

        if is_git_folder:
            typer.echo(__('You have local repo, we can not work with this'))
            raise typer.Exit(1)

        if not project.git_repository_url:
            typer.echo(__("Unexpected Project error, missing Repository"))
            raise typer.Exit(1)

        deploy_ssh_key = self.__thestage_api_client.get_project_deploy_ssh_key(public_id=project.public_id)
        deploy_key_path = self.__config_provider.save_project_deploy_ssh_key(deploy_ssh_key=deploy_ssh_key, project_public_id=project.public_id,)

        try:
            self.__git_local_client.clone(
                url=project.git_repository_url,
                path=config.runtime.working_directory,
                deploy_key_path=deploy_key_path
            )
            self.__git_local_client.init_gitignore(path=config.runtime.working_directory)
        except GitAccessException as ex:
            typer.echo(ex.get_message())
            typer.echo(ex.get_dop_message())
            typer.echo(__(
                "Please check you mail or open this repo url %git_url% and 'Accept invitation'",
                {
                    'git_url': ex.get_url()
                }
            ))
            raise typer.Exit(1)

        project_config = ProjectConfig()
        project_config.public_id = project.public_id
        project_config.slug = project.slug
        project_config.git_repository_url = project.git_repository_url
        project_config.deploy_key_path = str(deploy_key_path)
        self.__config_provider.save_project_config(project_config=project_config)
        typer.echo(__("Project successfully cloned to %path%", {"path": config.runtime.working_directory}))


    @error_handler()
    def project_run_task(
            self,
            run_command: str,
            docker_container_slug: str,
            docker_container_public_id: str,
            task_title: Optional[str] = None,
            commit_hash: Optional[str] = None,
            files_to_add: Optional[str] = None,
            is_skip_auto_commit: Optional[bool] = False,
    ) -> Optional[TaskDto]:
        config = self.__config_provider.get_config()
        project_config: ProjectConfig = self.__get_fixed_project_config()
        if not project_config:
            typer.echo(__("No project found at the path: %path%. Please initialize or clone a project first.", {"path": config.runtime.working_directory}))
            raise typer.Exit(1)

        if not docker_container_public_id and not docker_container_slug and not project_config.default_container_public_id:
            typer.echo(__('Docker container ID or name is required'))
            raise typer.Exit(1)

        final_container_public_id = docker_container_public_id
        final_container_slug = docker_container_slug
        if not final_container_public_id and not final_container_slug:
            final_container_public_id = project_config.default_container_public_id
            typer.echo(f"Using default docker container for this project: '{project_config.default_container_public_id}'")

        container: DockerContainerDto = self.__thestage_api_client.get_container(
            container_slug=final_container_slug,
            container_public_id=final_container_public_id
        )

        if container is None:
            if final_container_slug:
                typer.echo(f"Could not find container with name '{final_container_slug}'")
            if final_container_public_id:
                typer.echo(f"Could not find container with ID '{final_container_public_id}'")
            if project_config.default_container_public_id == final_container_public_id:
                project_config.default_container_public_id = None
                project_config.prompt_for_default_container = True
                self.__config_provider.save_project_config(project_config=project_config)
                typer.echo(f"Default container settings were reset")
            raise typer.Exit(1)

        if container.project.public_id != project_config.public_id:
            typer.echo(f"Provided container '{container.public_id}' is not related to project '{project_config.public_id}'")
            raise typer.Exit(1)

        if (project_config.prompt_for_default_container is None or project_config.prompt_for_default_container) and (docker_container_slug or docker_container_public_id) and (project_config.default_container_public_id != container.public_id):
            set_default_container_answer: str = typer.prompt(
                text=f"Would you like to set the container '{container.slug}' (ID: '{container.public_id}') as default for this project installation?",
                show_choices=True,
                default=YesOrNoResponse.YES.value,
                type=click.Choice([r.value for r in YesOrNoResponse]),
                show_default=True,
            )
            project_config.prompt_for_default_container = False
            if set_default_container_answer == YesOrNoResponse.YES.value:
                project_config.default_container_public_id = container.public_id

            self.__config_provider.save_project_config(project_config=project_config)

        has_wrong_args = files_to_add and commit_hash or is_skip_auto_commit and commit_hash or files_to_add and is_skip_auto_commit

        if has_wrong_args:
            warning_msg = f"[{ColorScheme.WARNING.value}][WARNING] You can provide only one of the following arguments: --commit-hash, --files-add, --skip-autocommit[{ColorScheme.WARNING.value}]"
            print(warning_msg)
            raise typer.Exit(1)

        if not is_skip_auto_commit and not commit_hash:
            is_git_folder = self.__git_local_client.is_present_local_git(path=config.runtime.working_directory)
            if not is_git_folder:
                typer.echo("Error: working directory does not contain git repository")
                raise typer.Exit(1)

            is_commit_allowed: bool = True
            has_changes = self.__git_local_client.has_changes_with_untracked(
                path=config.runtime.working_directory,
            )

            if self.__git_local_client.is_head_detached(path=config.runtime.working_directory):
                is_commit_allowed = False
                print(f"[{ColorScheme.GIT_HEADLESS.value}]HEAD is detached[{ColorScheme.GIT_HEADLESS.value}]")

                is_headless_commits_present = self.__git_local_client.is_head_committed_in_headless_state(path=config.runtime.working_directory)
                if is_headless_commits_present:
                    print(f"[{ColorScheme.GIT_HEADLESS.value}]Current commit was made in detached head state. Cannot use it to run the task. Consider using 'project checkout' command to return to a valid reference.[{ColorScheme.GIT_HEADLESS.value}]")
                    raise typer.Exit(1)

                if has_changes:
                    print(f"[{ColorScheme.GIT_HEADLESS.value}]Local changes detected in detached head state. They will not impact the task execution.[{ColorScheme.GIT_HEADLESS.value}]")
                    response: YesOrNoResponse = typer.prompt(
                        text=__('Continue?'),
                        show_choices=True,
                        default=YesOrNoResponse.YES.value,
                        type=click.Choice([r.value for r in YesOrNoResponse]),
                        show_default=True,
                    )
                    if response == YesOrNoResponse.NO:
                        raise typer.Exit(0)

            if is_commit_allowed:
                if not self.__git_local_client.add_files_with_size_limit_or_warn(config.runtime.working_directory, files_to_add):
                    warning_msg = f"[{ColorScheme.WARNING.value}][WARNING] Task was not started [{ColorScheme.WARNING.value}]"
                    print(warning_msg)
                    raise typer.Exit(1)
                
                diff_stat = self.__git_local_client.git_diff_stat(repo_path=config.runtime.working_directory)

                if has_changes and diff_stat:
                    branch_name = self.__git_local_client.get_active_branch_name(config.runtime.working_directory)

                    typer.echo(__('Active branch [%branch_name%] has uncommitted changes: %diff_stat_bottomline%', {
                        'diff_stat_bottomline': diff_stat,
                        'branch_name': branch_name,
                    }))

                    response: str = typer.prompt(
                        text=__('Commit changes?'),
                        show_choices=True,
                        default=YesOrNoResponse.YES.value,
                        type=click.Choice([r.value for r in YesOrNoResponse]),
                        show_default=True,
                    )
                    if response == YesOrNoResponse.NO.value:
                        typer.echo("Task cannot use uncommitted changes - aborting")
                        raise typer.Exit(0)

                    commit_name = typer.prompt(
                        text=__('Please provide commit message'),
                        show_choices=False,
                        type=str,
                        show_default=False,
                    )

                    if commit_name:
                        commit_result = self.__git_local_client.commit_local_changes(
                            path=config.runtime.working_directory,
                            name=commit_name
                        )

                        if commit_result:
                            # in docs not Commit object, on real - str
                            if isinstance(commit_result, str):
                                typer.echo(commit_result)
                    else:
                        typer.echo(__('Cannot commit with empty commit message'))
                        raise typer.Exit(0)
                else:
                    pass
                    # possible to push new empty branch - only that there's a wrong place to do so

                self.__git_local_client.push_changes(
                    path=config.runtime.working_directory,
                    deploy_key_path=project_config.deploy_key_path
                )
                typer.echo(__("Pushed changes to remote repository"))

        if not commit_hash:
            commit = self.__git_local_client.get_current_commit(path=config.runtime.working_directory)
            if not commit or not isinstance(commit, Commit):
                print('[red]Error: No current commit found in the local repository[/red]')
                raise typer.Exit(0)
            commit_hash = commit.hexsha
        else:
            commit = self.__git_local_client.get_commit_by_hash(path=config.runtime.working_directory, commit_hash=commit_hash)
            if not commit or not isinstance(commit, Commit):
                print(f'[red]Error: commit \'{commit_hash}\' was not found in the local repository[/red]')
                raise typer.Exit(0)

        if not task_title:
            task_title = commit.message.strip() if commit.message else f'Task_{commit_hash}'
            if not commit.message:
                typer.echo(f'Commit message is empty. Task title is set to "{task_title}"')

        run_task_response: ProjectRunTaskResponse = self.__thestage_api_client.execute_project_task(
            project_public_id=project_config.public_id,
            docker_container_public_id=container.public_id,
            run_command=run_command,
            commit_hash=commit_hash,
            task_title=task_title,
        )
        if run_task_response:
            if run_task_response.message:
                print(f"[{ColorScheme.WARNING.value}]{run_task_response.message}[{ColorScheme.WARNING.value}]")
            if run_task_response.is_success and run_task_response.task:
                typer.echo(f"Task '{run_task_response.task.title}' has been scheduled successfully. Task ID: {run_task_response.task.public_id}")
                if run_task_response.tasksInQueue:
                    typer.echo(f"There are tasks in queue ahead of this new task:")
                    for queued_task_item in run_task_response.tasksInQueue:
                        typer.echo(f"{queued_task_item.public_id} - {queued_task_item.frontend_status.status_translation}")
                return run_task_response.task
            else:
                typer.echo(f'The task failed with an error: {run_task_response.message}')
                raise typer.Exit(1)
        else:
            typer.echo("The task failed with an error")
            raise typer.Exit(1)

    @error_handler()
    def cancel_task(self, task_public_id: str):
        cancel_result = self.__thestage_api_client.cancel_task(
            task_public_id=task_public_id,
        )

        if cancel_result.is_success:
            typer.echo(f'Task {task_public_id} has been canceled')
        else:
            typer.echo(f'Task {task_public_id} could not be canceled: {cancel_result.message}')


    @error_handler()
    def project_run_inference_simulator(
            self,
            commit_hash: Optional[str] = None,
            rented_instance_public_id: Optional[str] = None,
            rented_instance_slug: Optional[str] = None,
            self_hosted_instance_public_id: Optional[str] = None,
            self_hosted_instance_slug: Optional[str] = None,
            inference_dir: Optional[str] = None,
            is_skip_installation: Optional[bool] = False,
            files_to_add: Optional[str] = None,
            is_skip_auto_commit: Optional[bool] = False,
    ) -> Optional[InferenceSimulatorDto]:
        config = self.__config_provider.get_config()
        project_config: ProjectConfig = self.__get_fixed_project_config()
        if not project_config:
            typer.echo(__("No project found at the path: %path%. Please initialize or clone a project first. Or provide path to project using --working-directory option.",
                          {"path": config.runtime.working_directory}))
            raise typer.Exit(1)

        instance_args_count = sum(v is not None for v in [rented_instance_public_id, rented_instance_slug, self_hosted_instance_public_id, self_hosted_instance_slug])
        if instance_args_count != 1:
            typer.echo("Please provide a single instance (rented or self-hosted) identifier - name or ID.")
            raise typer.Exit(1)

        has_wrong_args = files_to_add and commit_hash or is_skip_auto_commit and commit_hash or files_to_add and is_skip_auto_commit
        if has_wrong_args:
            warning_msg = f"[{ColorScheme.WARNING.value}][WARNING] You can provide only one of the following arguments: --commit-hash, --files-add, --skip-autocommit[{ColorScheme.WARNING.value}]"
            print(warning_msg)
            raise typer.Exit(1)

        if not is_skip_auto_commit and not commit_hash:
            is_git_folder = self.__git_local_client.is_present_local_git(path=config.runtime.working_directory)
            if not is_git_folder:
                typer.echo("Error: Working directory does not contain git repository.")
                raise typer.Exit(1)

            is_commit_allowed: bool = True
            has_changes = self.__git_local_client.has_changes_with_untracked(
                path=config.runtime.working_directory,
            )

            if self.__git_local_client.is_head_detached(path=config.runtime.working_directory):
                print(f"[{ColorScheme.GIT_HEADLESS.value}]HEAD is detached[{ColorScheme.GIT_HEADLESS.value}]")

                is_headless_commits_present = self.__git_local_client.is_head_committed_in_headless_state(
                    path=config.runtime.working_directory)
                if is_headless_commits_present:
                    print(
                        f"[{ColorScheme.GIT_HEADLESS.value}]Current commit was made in detached head state. Cannot use it to start the inference simulator. Consider using 'project checkout' command to return to a valid reference.[{ColorScheme.GIT_HEADLESS.value}]")
                    raise typer.Exit(1)

                if has_changes:
                    print(
                        f"[{ColorScheme.GIT_HEADLESS.value}]Local changes detected in detached head state. They will not impact the inference simulator.[{ColorScheme.GIT_HEADLESS.value}]")
                    is_commit_allowed = False
                    response: YesOrNoResponse = typer.prompt(
                        text=__('Continue?'),
                        show_choices=True,
                        default=YesOrNoResponse.YES.value,
                        type=click.Choice([r.value for r in YesOrNoResponse]),
                        show_default=True,
                    )
                    if response == YesOrNoResponse.NO:
                        raise typer.Exit(0)

            if is_commit_allowed:
                if not self.__git_local_client.add_files_with_size_limit_or_warn(config.runtime.working_directory, files_to_add):
                    warning_msg = f"[{ColorScheme.WARNING.value}][WARNING] Inference simulator was not started [{ColorScheme.WARNING.value}]"
                    print(warning_msg)
                    raise typer.Exit(1)

                diff_stat = self.__git_local_client.git_diff_stat(repo_path=config.runtime.working_directory)

                if has_changes and diff_stat:
                    branch_name = self.__git_local_client.get_active_branch_name(config.runtime.working_directory)
                    typer.echo(__('Active branch [%branch_name%] has uncommitted changes: %diff_stat_bottomline%', {
                        'diff_stat_bottomline': diff_stat,
                        'branch_name': branch_name,
                    }))

                    response: str = typer.prompt(
                        text=__('Commit changes?'),
                        show_choices=True,
                        default=YesOrNoResponse.YES.value,
                        type=click.Choice([r.value for r in YesOrNoResponse]),
                        show_default=True,
                    )
                    if response == YesOrNoResponse.NO.value:
                        typer.echo("inference simulator cannot use uncommitted changes - aborting")
                        raise typer.Exit(0)

                    commit_name = typer.prompt(
                        text=__('Please provide commit message'),
                        show_choices=False,
                        type=str,
                        show_default=False,
                    )

                    if commit_name:
                        commit_result = self.__git_local_client.commit_local_changes(
                            path=config.runtime.working_directory,
                            name=commit_name
                        )

                        if commit_result:
                            # in docs not Commit object, on real - str
                            if isinstance(commit_result, str):
                                typer.echo(commit_result)

                        self.__git_local_client.push_changes(
                            path=config.runtime.working_directory,
                            deploy_key_path=project_config.deploy_key_path
                        )
                        typer.echo(__("Pushed changes to remote repository"))
                    else:
                        typer.echo(__('Cannot commit with empty commit name, your code will run without last changes.'))
                else:
                    pass
                    # possible to push new empty branch - only that there's a wrong place to do so

        if not commit_hash:
            commit = self.__git_local_client.get_current_commit(path=config.runtime.working_directory)
            if commit and isinstance(commit, Commit):
                commit_hash = commit.hexsha

        start_inference_simulator_response: ProjectStartInferenceSimulatorResponse = self.__thestage_api_client.start_project_inference_simulator(
            project_public_id=project_config.public_id,
            commit_hash=commit_hash,
            rented_instance_public_id=rented_instance_public_id,
            rented_instance_slug=rented_instance_slug,
            self_hosted_instance_public_id=self_hosted_instance_public_id,
            self_hosted_instance_slug=self_hosted_instance_slug,
            inference_dir=inference_dir,
            is_skip_installation=is_skip_installation,
        )
        if start_inference_simulator_response:
            if start_inference_simulator_response.message:
                typer.echo(start_inference_simulator_response.message)
            if start_inference_simulator_response.is_success and start_inference_simulator_response.inferenceSimulator:
                typer.echo("Inference simulator has been scheduled to run successfully.")
                return start_inference_simulator_response.inferenceSimulator
            else:
                typer.echo(__(
                    'Inference simulator failed to run with an error: %server_massage%',
                    {'server_massage': start_inference_simulator_response.message or ""}
                ))
                raise typer.Exit(1)
        else:
            typer.echo(__("Inference simulator failed to run with an error"))
            raise typer.Exit(1)


    @error_handler()
    def project_push_inference_simulator(
            self,
            public_id: Optional[str] = None,
            slug: Optional[str] = None,
    ):

        push_inference_simulator_model_response: ProjectPushInferenceSimulatorModelResponse = self.__thestage_api_client.push_project_inference_simulator_model(
            public_id=public_id,
            slug=slug,
        )
        if push_inference_simulator_model_response:
            if push_inference_simulator_model_response.message:
                typer.echo(push_inference_simulator_model_response.message)
            if push_inference_simulator_model_response.is_success:
                typer.echo("Inference simulator has been successfully scheduled to be pushed to S3 and ECR.")
            else:
                typer.echo(__(
                    'Failed to push inference simulator with an error: %server_massage%',
                    {'server_massage': push_inference_simulator_model_response.message or ""}
                ))
                raise typer.Exit(1)
        else:
            typer.echo(__("Failed to push inference simulator with an error"))
            raise typer.Exit(1)

    @error_handler()
    def project_get_and_save_inference_simulator_metadata(
            self,
            inference_simulator_public_id: Optional[str] = None,
            inference_simulator_slug: Optional[str] = None,
            file_path: Optional[str] = None,
    ):
        get_inference_metadata_response: GetInferenceSimulatorResponse = self.__thestage_api_client.get_inference_simulator(
            public_id=inference_simulator_public_id,
            slug=inference_simulator_slug,
        )

        metadata = get_inference_metadata_response.inferenceSimulator.qlip_serve_metadata

        if metadata:
            typer.echo("qlip_serve_metadata:")
            typer.echo(json.dumps(metadata, indent=4))

            if not file_path:
                file_path = Path(os.getcwd()) / "metadata.json"
                typer.echo(__("No file path provided. Saving metadata to %file_path%", {"file_path": str(file_path)}))

            try:
                parsed_metadata = metadata

                output_file = Path(file_path)
                output_file.parent.mkdir(parents=True, exist_ok=True)
                with output_file.open("w", encoding="utf-8") as file:
                    json.dump(parsed_metadata, file, indent=4)
                typer.echo(__("Metadata successfully saved to %file_path%", {"file_path": str(file_path)}))
            except Exception as e:
                typer.echo(__("Failed to save metadata to %file_path%. Error: %error%",
                              {"file_path": file_path, "error": str(e)}))
                raise typer.Exit(1)
        else:
            typer.echo(__("No qlip_serve_metadata found"))
            raise typer.Exit(1)


    @error_handler()
    def get_project_inference_simulator_list(
            self,
            project_public_id: Optional[str],
            project_slug: Optional[str],
            statuses: List[str],
            row: int = 5,
            page: int = 1,
    ) -> PaginatedEntityList[InferenceSimulatorDto]:
        data: Optional[PaginatedEntityList[InferenceSimulatorDto]] = self.__thestage_api_client.get_inference_simulator_list(
            statuses=statuses,
            project_public_id=project_public_id,
            project_slug=project_slug,
            page=page,
            limit=row,
        )

        return data


    @error_handler()
    def get_project_inference_simulator_model_list(
            self,
            project_public_id: Optional[str],
            project_slug: Optional[str],
            statuses: List[str],
            row: int = 5,
            page: int = 1,
    ) -> PaginatedEntityList[InferenceSimulatorModelDto]:
        data: Optional[
            PaginatedEntityList[InferenceSimulatorModelDto]] = self.__thestage_api_client.get_inference_simulator_model_list_for_project(
            statuses=statuses,
            project_public_id=project_public_id,
            project_slug=project_slug,
            page=page,
            limit=row,
        )

        return data


    @error_handler()
    def checkout_project(
            self,
            task_public_id: Optional[str],
            branch_name: Optional[str],
    ):
        config = self.__config_provider.get_config()
        project_config: ProjectConfig = self.__get_fixed_project_config()
        if not project_config:
            typer.echo(__("This command is only allowed from within an initialized project directory"))
            raise typer.Exit(1)

        target_commit_hash: Optional[str] = None
        if task_public_id:
            task_view_response: Optional[TaskViewResponse] = None
            try:
                task_view_response = self.__thestage_api_client.get_task(task_public_id=task_public_id)
            except HttpClientException as e:
                if e.get_status_code() == 400:
                    typer.echo(f"Task {task_public_id} was not found")
                    # overriding arguments here
                    branch_name = str(task_public_id)
                    task_public_id = None

            if task_view_response and task_view_response.task:
                target_commit_hash = task_view_response.task.commit_hash
                if not target_commit_hash:
                    typer.echo(f"Provided task ({task_public_id}) has no commit hash")  # possible legacy problems
                    raise typer.Exit(1)

        is_commit_allowed: bool = True

        if self.__git_local_client.is_head_detached(path=config.runtime.working_directory):
            is_commit_allowed = False
            if self.__git_local_client.is_head_committed_in_headless_state(path=config.runtime.working_directory):
                commit_message = self.__git_local_client.get_current_commit(path=config.runtime.working_directory).message
                print(f"[{ColorScheme.GIT_HEADLESS.value}]Your current commit '{commit_message.strip()}' was likely created in detached head state. Checking out will discard all changes.[/{ColorScheme.GIT_HEADLESS.value}]")
                response: YesOrNoResponse = typer.prompt(
                    text=__('Continue?'),
                    show_choices=True,
                    default=YesOrNoResponse.YES.value,
                    type=click.Choice([r.value for r in YesOrNoResponse]),
                    show_default=True,
                )
                if response == YesOrNoResponse.NO:
                    raise typer.Exit(0)
        else:
            if self.__git_local_client.get_active_branch_name(path=config.runtime.working_directory) == branch_name:
                typer.echo(f"You are already at branch '{branch_name}'")
                raise typer.Exit(0)
        
        if is_commit_allowed:
            self.__git_local_client.git_add_all(repo_path=config.runtime.working_directory)

            has_changes = self.__git_local_client.has_changes_with_untracked(
                path=config.runtime.working_directory,
            )
            
            if has_changes:
                active_branch_name = self.__git_local_client.get_active_branch_name(config.runtime.working_directory)
                diff_stat = self.__git_local_client.git_diff_stat(repo_path=config.runtime.working_directory)
                typer.echo(__('Active branch [%branch_name%] has uncommitted changes: %diff_stat_bottomline%', {
                    'diff_stat_bottomline': diff_stat,
                    'branch_name': active_branch_name,
                }))

                response: str = typer.prompt(
                    text=__('Commit changes?'),
                    show_choices=True,
                    default=YesOrNoResponse.YES.value,
                    type=click.Choice([r.value for r in YesOrNoResponse]),
                    show_default=True,
                )
                if response == YesOrNoResponse.NO.value:
                    typer.echo(__('Cannot checkout with uncommitted changes'))
                    raise typer.Exit(0)

                commit_name = typer.prompt(
                    text=__('Please provide commit message'),
                    show_choices=False,
                    type=str,
                    show_default=False,
                )

                if commit_name:
                    commit_result = self.__git_local_client.commit_local_changes(
                        path=config.runtime.working_directory,
                        name=commit_name
                    )

                    if commit_result:
                        # in docs not Commit object, on real - str
                        if isinstance(commit_result, str):
                            typer.echo(commit_result)

                    self.__git_local_client.push_changes(
                        path=config.runtime.working_directory,
                        deploy_key_path=project_config.deploy_key_path
                    )
                    typer.echo(__("Pushed changes to remote repository"))
                else:
                    typer.echo(__('Cannot commit with empty commit name'))
                    raise typer.Exit(0)

        if target_commit_hash:
            if self.__git_local_client.get_current_commit(path=config.runtime.working_directory).hexsha != target_commit_hash:
                is_checkout_successful = self.__git_local_client.git_checkout_to_commit(
                    path=config.runtime.working_directory,
                    commit_hash=target_commit_hash
                )

                if is_checkout_successful:
                    print(f"Checked out to commit {target_commit_hash}")
                    print(f"[{ColorScheme.GIT_HEADLESS.value}]HEAD is detached. To be able make changes in repository, checkout to any branch.[/{ColorScheme.GIT_HEADLESS.value}]")
            else:
                typer.echo("HEAD is already at requested commit")
        elif branch_name:
            if self.__git_local_client.is_branch_exists(path=config.runtime.working_directory, branch_name=branch_name):
                self.__git_local_client.git_checkout_to_branch(
                    path=config.runtime.working_directory,
                    branch=branch_name
                )
                typer.echo(f"Checked out to branch '{branch_name}'")
            else:
                typer.echo(f"Branch '{branch_name}' was not found in project repository")
        else:
            main_branch = self.__git_local_client.find_main_branch_name(path=config.runtime.working_directory)
            if main_branch:
                self.__git_local_client.git_checkout_to_branch(
                    path=config.runtime.working_directory,
                    branch=main_branch
                )
                typer.echo(f"Checked out to detected main branch: '{main_branch}'")
            else:
                typer.echo("No main branch found")




    @error_handler()
    def set_default_container(
            self,
            container_public_id: Optional[str],
            container_slug: Optional[str],
    ):
        project_config: ProjectConfig = self.__config_provider.read_project_config()

        if project_config is None:
            typer.echo(f"No project found in working directory")
            raise typer.Exit(1)

        container: Optional[DockerContainerDto] = None
        if container_slug or container_public_id:
            container: DockerContainerDto = self.__thestage_api_client.get_container(
                container_public_id=container_public_id,
                container_slug=container_slug,
            )
            if container is None:
                typer.echo(f"Could not find container '{container_slug or container_public_id}'")
                raise typer.Exit(1)

            if container.project.public_id != project_config.public_id:
                typer.echo(f"Provided container '{container_slug or container_public_id}' is not related to current project '{project_config.public_id}'")
                raise typer.Exit(1)

            if container.frontend_status.status_key != DockerContainerStatus.RUNNING:
                typer.echo(f"Note: provided container '{container_slug or container_public_id}' is in status '{container.frontend_status.status_translation}'")

        project_config.default_container_public_id = container.public_id if container else None
        project_config.prompt_for_default_container = False
        self.__config_provider.save_project_config(project_config=project_config)
        typer.echo("Default container settings were updated")


    @error_handler()
    def print_project_config(self):
        project_config: ProjectConfig = self.__config_provider.read_project_config()

        if project_config is None:
            typer.echo(f"No project found in working directory")
            raise typer.Exit(1)

        is_deploy_key_exists = project_config.deploy_key_path and self.__file_system_service.check_if_path_exist(project_config.deploy_key_path)

        typer.echo(tabulate(
            [
                [
                    "Project ID", project_config.public_id
                ],
                [
                    "Project name", project_config.slug
                ],
                [
                    "Default docker container ID", project_config.default_container_public_id if project_config.default_container_public_id else "<None>"
                ],
                [
                    "Deploy key path", project_config.deploy_key_path if is_deploy_key_exists else "<None>"
                ],
            ],
            showindex=False,
            tablefmt="simple",
        ))

        if is_deploy_key_exists:
            typer.echo("")
            typer.echo(f"You can insert the following text:")
            print(f"[{ColorScheme.USEFUL_INFO.value}]GIT_SSH_COMMAND=\"ssh -o StrictHostKeyChecking=no -o IdentitiesOnly=yes -i {project_config.deploy_key_path}\"[{ColorScheme.USEFUL_INFO.value}]")
            typer.echo(f"before any regular git command to manage your local Project repository directly")

    @error_handler()
    def __get_fixed_project_config(self) -> Optional[ProjectConfig]:
        project_config: ProjectConfig = self.__config_provider.read_project_config()
        if project_config is None:
            return None

        if project_config.public_id is None:
            project = self.__thestage_api_client.get_project(public_id=None, slug=project_config.slug)
            project_config.public_id = project.public_id
            self.__config_provider.save_project_config(project_config=project_config)

        if not Path(project_config.deploy_key_path).is_file():
            deploy_ssh_key = self.__thestage_api_client.get_project_deploy_ssh_key(
                public_id=project_config.public_id,
            )

            deploy_key_path = self.__config_provider.save_project_deploy_ssh_key(
                deploy_ssh_key=deploy_ssh_key,
                project_public_id=project_config.public_id,
            )

            project_config.deploy_key_path = deploy_key_path
            self.__config_provider.save_project_config(project_config=project_config)
            typer.echo(f'Recreated missing deploy key for the project')

        return project_config

    @error_handler()
    def project_deploy_inference_simulator_model_to_instance(
            self,
            model_public_id: Optional[str] = None,
            model_slug: Optional[str] = None,
            rented_instance_public_id: Optional[str] = None,
            rented_instance_slug: Optional[str] = None,
            self_hosted_instance_public_id: Optional[str] = None,
            self_hosted_instance_slug: Optional[str] = None,
    ) -> str:
        config = self.__config_provider.get_config()
        project_config: ProjectConfig = self.__get_fixed_project_config()
        if not project_config:
            typer.echo(
                __("No project found at the path: %path%. Please initialize or clone a project first. Or provide path to project using --working-directory option.",
                   {"path": config.runtime.working_directory}))
            raise typer.Exit(1)

        instance_args_count = sum(v is not None for v in [rented_instance_public_id, rented_instance_slug, self_hosted_instance_public_id, self_hosted_instance_slug])
        if instance_args_count != 1:
            typer.echo("Please provide a single instance (rented or self-hosted) identifier - name or ID.")
            raise typer.Exit(1)

        model_args_count = sum(v is not None for v in [model_public_id, model_slug])
        if model_args_count != 1:
            typer.echo("Please provide a single model identifier - name or ID.")
            raise typer.Exit(1)

        typer.echo(f"Creating inference simulator")
        deploy_model_to_instance_response: DeployInferenceModelToInstanceResponse = self.__thestage_api_client.deploy_inference_model_to_instance(
            model_public_id=model_public_id,
            model_slug=model_slug,
            rented_instance_public_id=rented_instance_public_id,
            rented_instance_slug=rented_instance_slug,
            self_hosted_instance_public_id=self_hosted_instance_public_id,
            self_hosted_instance_slug=self_hosted_instance_slug,
        )
        if deploy_model_to_instance_response:
            if deploy_model_to_instance_response.message:
                typer.echo(deploy_model_to_instance_response.message)
            if deploy_model_to_instance_response.is_success:
                typer.echo(f"Inference simulator '{deploy_model_to_instance_response.inferenceSimulatorPublicId}' has been scheduled to run successfully.")
            else:
                typer.echo(__(
                    'Inference simulator failed to run with an error: %server_massage%',
                    {'server_massage': deploy_model_to_instance_response.message or ""}
                ))
                raise typer.Exit(1)
        else:
            typer.echo(__("Inference simulator failed to run with an error"))
            raise typer.Exit(1)

        return deploy_model_to_instance_response.inferenceSimulatorPublicId


    @error_handler()
    def project_deploy_inference_simulator_model_to_sagemaker(
            self,
            model_public_id: Optional[str] = None,
            model_slug: Optional[str] = None,
            arn: Optional[str] = None,
            instance_type: Optional[str] = None,
            initial_variant_weight: Optional[float] = 1.0,
            initial_instance_count: Optional[int] = None,
    ) -> None:
        config = self.__config_provider.get_config()
        project_config: ProjectConfig = self.__get_fixed_project_config()
        if not project_config:
            typer.echo(
                __("No project found at the path: %path%. Please initialize or clone a project first. Or provide path to project using --working-directory option.",
                   {"path": config.runtime.working_directory}))
            raise typer.Exit(1)

        if not instance_type:
            typer.echo(__("Error: Instance type is required."))
            raise typer.Exit(1)

        if not initial_instance_count:
            typer.echo(__("Error: Initial instance count is required."))
            raise typer.Exit(1)

        if not arn:
            typer.echo(__("Error: ARN is required."))
            raise typer.Exit(1)

        project_config: ProjectConfig = self.__config_provider.read_project_config()
        if not project_config:
            typer.echo(__("No project found at the path: %path%. Please initialize or clone a project first.",
                          {"path": config.runtime.working_directory}))
            raise typer.Exit(1)

        deploy_model_to_sagemaker_response: DeployInferenceModelToSagemakerResponse = self.__thestage_api_client.deploy_inference_model_to_sagemaker(
            model_public_id=model_public_id,
            model_slug=model_slug,
            arn=arn,
        )

        if not deploy_model_to_sagemaker_response.is_success:
            typer.echo(__(
                'Failed to prepare model for deployment with an error: %server_massage%',
                {'server_massage': deploy_model_to_sagemaker_response.message or ""}
            ))
            raise typer.Exit(1)

        model_id = deploy_model_to_sagemaker_response.modelId
        image_uri = deploy_model_to_sagemaker_response.ecrImageUrl
        model_uri = deploy_model_to_sagemaker_response.s3ArtifactsUrl
        region = "us-east-1"
        sm_client = boto3.client('sagemaker', region_name=region)

        try:
            container = {
                "Image": image_uri,
                "ModelDataUrl": model_uri,
                "Environment": {
                    "SAGEMAKER_TRITON_DEFAULT_MODEL_NAME": model_id,
                    "THESTAGE_API_URL": config.main.thestage_api_url,
                    "THESTAGE_AUTH_TOKEN": config.main.thestage_auth_token
                },
            }

            sm_model_name = f"{model_slug}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            create_model_response = sm_client.create_model(
                ModelName=sm_model_name,
                ExecutionRoleArn=arn,
                PrimaryContainer=container,
            )
            typer.echo(f"Model created successfully. Model ARN: {create_model_response['ModelArn']}")

            endpoint_config_name = f"{model_slug}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            create_endpoint_config_response = sm_client.create_endpoint_config(
                EndpointConfigName=endpoint_config_name,
                ProductionVariants=[
                    {
                        "InstanceType": instance_type,
                        "InitialVariantWeight": initial_variant_weight,
                        "InitialInstanceCount": initial_instance_count,
                        "ModelName": sm_model_name,
                        "VariantName": "AllTraffic",
                    }
                ],
            )
            typer.echo(
                f"Endpoint configuration created successfully. Endpoint Config ARN: {create_endpoint_config_response['EndpointConfigArn']}")

            endpoint_name = f"{model_slug}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            create_endpoint_response = sm_client.create_endpoint(
                EndpointName=endpoint_name,
                EndpointConfigName=endpoint_config_name,
            )
            typer.echo(f"Endpoint created successfully. Endpoint ARN: {create_endpoint_response['EndpointArn']}")

            typer.echo("Waiting for the endpoint to become active...")
            while True:
                resp = sm_client.describe_endpoint(EndpointName=endpoint_name)
                status = resp["EndpointStatus"]
                typer.echo(f"Status: {status}")
                if status == "InService":
                    break
                elif status == "Failed":
                    typer.echo(f"Endpoint creation failed. Reason: {resp.get('FailureReason', 'Unknown')}")
                    raise typer.Exit(1)
                time.sleep(60)

            typer.echo(f"Endpoint is ready. ARN: {resp['EndpointArn']} Status: {status}")

        except Exception as e:
            typer.echo(__("Failed to deploy the inference simulator model to SageMaker: %error%", {"error": str(e)}))
            raise typer.Exit(1)


    @error_handler()
    def pull_project(self):
        config = self.__config_provider.get_config()
        project_config: ProjectConfig = self.__get_fixed_project_config()
        if not project_config:
            typer.echo(__("No project found at the path: %path%. Please initialize or clone a project first.", {"path": config.runtime.working_directory}))
            raise typer.Exit(1)

        typer.echo("Pulling code from remote repository...")
        self.__git_local_client.git_pull(
            path=config.runtime.working_directory,
            deploy_key_path=project_config.deploy_key_path,
        )


    @error_handler()
    def reset_project(self):
        config = self.__config_provider.get_config()
        project_config: ProjectConfig = self.__get_fixed_project_config()
        if not project_config:
            typer.echo(__("No project found at the path: %path%. Please initialize or clone a project first.", {"path": config.runtime.working_directory}))
            raise typer.Exit(1)

        typer.echo("Fetching code from remote repository...")
        self.__git_local_client.git_fetch(
            path=config.runtime.working_directory,
            deploy_key_path=project_config.deploy_key_path,
        )
        typer.echo("Resetting local branch...")
        self.__git_local_client.reset_hard(
            path=config.runtime.working_directory,
            deploy_key_path=project_config.deploy_key_path,
            reset_to_origin=True
        )


    @error_handler()
    def print_inference_simulator_list(self, project_public_id, project_slug, statuses, row, page):
        if not project_public_id and not project_slug:
            project_config: ProjectConfig = self.__config_provider.read_project_config()
            if not project_config:
                typer.echo(__("Provide the project identifier or run this command from within an initialized project directory"))
                raise typer.Exit(1)
            project_public_id = project_config.public_id

        inference_simulator_status_map = self.__thestage_api_client.get_inference_simulator_business_status_map()

        if not statuses:
            statuses = ({key: inference_simulator_status_map[key] for key in [
                InferenceSimulatorStatus.SCHEDULED,
                InferenceSimulatorStatus.CREATING,
                InferenceSimulatorStatus.RUNNING,
            ]}).values()

        if "all" in statuses:
            statuses = inference_simulator_status_map.values()

        for input_status_item in statuses:
            if input_status_item not in inference_simulator_status_map.values():
                typer.echo(__("'%invalid_status%' is not one of %valid_statuses%", {
                    'invalid_status': input_status_item,
                    'valid_statuses': str(list(inference_simulator_status_map.values()))
                }))
                raise typer.Exit(1)

        typer.echo(__(
            "Listing inference simulators with the following statuses: %statuses%, to view all inference simulators, use --status all",
            placeholders={
                'statuses': ', '.join([status_item for status_item in statuses])
            }))

        backend_statuses: List[str] = [key for key, value in inference_simulator_status_map.items() if value in statuses]

        self.print(
            func_get_data=self.get_project_inference_simulator_list,
            func_special_params={
                'project_public_id': project_public_id,
                'project_slug': project_slug,
                'statuses': backend_statuses,
            },
            mapper=ProjectInferenceSimulatorMapper(),
            headers=list(map(lambda x: x.alias, ProjectInferenceSimulatorEntity.model_fields.values())),
            row=row,
            page=page,
            max_col_width=[100, 100, 100, 100, 100, 100, 100, 100],
            show_index="never",
        )


    @error_handler()
    def print_inference_simulator_model_list(self, project_public_id, project_slug, statuses, row, page):
        if not project_public_id and not project_slug:
            project_config: ProjectConfig = self.__config_provider.read_project_config()
            if not project_config:
                typer.echo(__("Provide the project identifier or run this command from within an initialized project directory"))
                raise typer.Exit(1)
            project_public_id = project_config.public_id

        inference_simulator_model_status_map = self.__thestage_api_client.get_inference_simulator_model_business_status_map()

        if not statuses:
            statuses = ({key: inference_simulator_model_status_map[key] for key in [
                InferenceModelStatus.SCHEDULED,
                InferenceModelStatus.PROCESSING,
                InferenceModelStatus.PUSH_SUCCEED,
            ]}).values()

        if "all" in statuses:
            statuses = inference_simulator_model_status_map.values()

        for input_status_item in statuses:
            if input_status_item not in inference_simulator_model_status_map.values():
                typer.echo(__("'%invalid_status%' is not one of %valid_statuses%", {
                    'invalid_status': input_status_item,
                    'valid_statuses': str(list(inference_simulator_model_status_map.values()))
                }))
                raise typer.Exit(1)

        typer.echo(__(
            "Listing inference simulator models with the following statuses: %statuses%, to view all inference simulator models, use --status all",
            placeholders={
                'statuses': ', '.join([status_item for status_item in statuses])
            }))

        backend_statuses: List[str] = [key for key, value in inference_simulator_model_status_map.items() if value in statuses]

        self.print(
            func_get_data=self.get_project_inference_simulator_model_list,
            func_special_params={
                'project_public_id': project_public_id,
                'project_slug': project_slug,
                'statuses': backend_statuses,
            },
            mapper=ProjectInferenceSimulatorModelMapper(),
            headers=list(map(lambda x: x.alias, ProjectInferenceSimulatorModelEntity.model_fields.values())),
            row=row,
            page=page,
            max_col_width=[100, 100, 100, 100, 25],
            show_index="never",
        )


    def print_task_list(self, project_public_id: Optional[str], project_slug: Optional[str], row, page):
        if not project_slug and not project_public_id:
            project_config: ProjectConfig = self.__config_provider.read_project_config()
            if not project_config:
                typer.echo(__("Provide the project identifier or run this command from within an initialized project directory"))
                raise typer.Exit(1)
            project_public_id = project_config.public_id

        self.print(
            func_get_data=self.get_project_task_list,
            func_special_params={
                'project_public_id': project_public_id,
                'project_slug': project_slug,
            },
            mapper=ProjectTaskMapper(),
            headers=list(map(lambda x: x.alias, ProjectTaskEntity.model_fields.values())),
            row=row,
            page=page,
            max_col_width=[100, 100, 100, 100, 100, 100, 100, 100],
            show_index="never",
        )

    @error_handler()
    def get_project_task_list(
            self,
            project_public_id: Optional[str],
            project_slug: Optional[str],
            row: int = 5,
            page: int = 1,
    ) -> PaginatedEntityList[TaskDto]:
        data: Optional[PaginatedEntityList[TaskDto]] = self.__thestage_api_client.get_task_list_for_project(
            project_public_id=project_public_id,
            project_slug=project_slug,
            page=page,
            limit=row,
        )

        return data
