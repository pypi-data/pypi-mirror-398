import os
import stat
from pathlib import Path
from time import sleep
from typing import Optional, List, Tuple

import math
import paramiko
import typer
from click import Abort
from paramiko.client import SSHClient
from paramiko.pkey import PKey
from paramiko.sftp_client import SFTPClient

from thestage.entities.file_item import FileItemEntity
from thestage.services.core_files.config_entity import ConfigEntity
from thestage.exceptions.remote_server_exception import RemoteServerException
from thestage.helpers.logger.app_logger import app_logger
from thestage.entities.enums.shell_type import ShellType
from thestage.helpers.ssh_util import parse_private_key
from thestage.i18n.translation import __
from thestage.services.clients.thestage_api.dtos.sftp_path_helper import SftpFileItemEntity
from thestage.services.config_provider.config_provider import ConfigProvider
from thestage.services.filesystem_service import FileSystemService

old_value: int = 0


class RemoteServerService:
    __config_provider: ConfigProvider = None
    __file_system_service: FileSystemService = None

    def __init__(
            self,
            file_system_service: FileSystemService,
            config_provider: ConfigProvider,
    ):
        self.__file_system_service = file_system_service
        self.__config_provider = config_provider

    def __get_client(
            self,
            ip_address: str,
            username: str,
            private_key_path: Optional[str],
    ) -> Optional[SSHClient]:
        pkey: Optional[PKey] = None
        if private_key_path:
            pkey = parse_private_key(private_key_path)
            if pkey is None:
                typer.echo("Could not identify provided private key (expected RSA, ECDSA, ED25519)")
                raise typer.Exit(1)

        client = SSHClient()
        try:
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname=ip_address,
                username=username,
                timeout=6,
                # key_filename=private_key_path, # key_filename is buggy for certain algorithms/systems apparently
                pkey=pkey,
                allow_agent=private_key_path is None,
                look_for_keys=private_key_path is None,
            )
            return client

        except Exception as ex:
            if client:
                client.close()
                typer.echo(f"Error connecting to {ip_address} as {username} ({ex})")
            app_logger.error(f"Error connecting to {ip_address} as {username} ({ex})")
            raise RemoteServerException(
                message=__("Unable to connect to remote server"),
                ip_address=ip_address,
                username=username,
            )


    def get_shell_from_container(
            self,
            ip_address: str,
            username: str,
            container_name: str,
            private_key_path: Optional[str],
    ) -> Optional[ShellType]:
        client: Optional[SSHClient] = self.__get_client(
            ip_address=ip_address,
            username=username,
            private_key_path=private_key_path,
        )
        stdin, stdout, stderr = client.exec_command(f'docker exec -it {container_name} cat /etc/shells', get_pty=True)
        shell: Optional[ShellType] = None
        stdout_lines: List[str] = []

        for line in stdout.readlines():
            stdout_lines.append(line.rstrip())
            if 'bin/bash' in line:
                shell = ShellType.BASH
                break
            if 'bin/sh' in line:
                shell = ShellType.SH
                break
        client.close()

        if shell is None:
            for line_item in stdout_lines:
                typer.echo(line_item)

        return shell


    def connect_to_instance(
            self,
            ip_address: str,
            username: str,
            private_key_path: Optional[str],
    ):
        typer.echo(f"Connecting to {username}@{ip_address}")
        try:
            if private_key_path:
                os.system(f"ssh -o PreferredAuthentications=publickey -o 'IdentitiesOnly=yes' -i {private_key_path} {username}@{ip_address}")
            else:
                os.system(f"ssh -o PreferredAuthentications=publickey {username}@{ip_address}")
        except Abort as e1:
            return
        except Exception as ex:
            app_logger.error(f"Error connecting to {ip_address} as {username} ({ex})")
            raise RemoteServerException(
                message=__("Unable to connect to remote server"),
                ip_address=ip_address,
                username=username,
            )


    def connect_to_container(
            self,
            ip_address: str,
            username: str,
            docker_name: str,
            starting_directory: str,
            shell: ShellType,
            private_key_path: Optional[str],
    ):
        try:
            if private_key_path:
                os.system(f"ssh -tt -o PreferredAuthentications=publickey -o 'IdentitiesOnly=yes' -i {private_key_path} {username}@{ip_address} 'docker exec -it {docker_name} sh -c \"cd {starting_directory} && {shell.value}\"'")
            else:
                os.system(f"ssh -tt {username}@{ip_address} 'docker exec -it {docker_name} sh -c \"cd {starting_directory} && {shell.value}\"'")
        except Exception as ex:
            app_logger.exception(f"Error connecting to {ip_address} as {username} ({ex})")
            raise RemoteServerException(
                message=__("Unable to connect to remote server"),
                ip_address=ip_address,
                username=username,
            )


    def __upload_one_file(
            self,
            sftp: SFTPClient,
            src_path: str,
            dest_path: str,
            file_name: str,
            container_path: str,
            file_size: [int] = 100,
    ) -> bool:
        has_error = False
        try:
            with typer.progressbar(length=file_size, label=__("Uploading %file_name% (%file_size%)", {'file_name': file_name, 'file_size': self.__convert_size(file_size)})) as progress:
                def __show_result_copy(size: int, full_size: int):
                    global old_value
                    progress.update(size - (old_value or 0))
                    old_value = size
                    if old_value == full_size:
                        old_value = 0
                sftp.put(localpath=src_path, remotepath=f"{dest_path}", callback=__show_result_copy)
            typer.echo(__('Uploaded to container as %file_path%', {'file_path': container_path}))
        except FileNotFoundError as err:
            app_logger.exception(f"Error uploading file {file_name} to container (file not found): {err}")
            typer.echo(__("Error uploading file: file not found on server"))
            has_error = True
        except Exception as err2:
            typer.echo(err2)
            app_logger.exception(f"Error uploading file {file_name} to container: {err2}")
            typer.echo(__("Error uploading file: undefined server error"))
            has_error = True

        return has_error

    def __make_dirs_by_sftp(
            self,
            sftp: SFTPClient,
            path: str,
    ):
        full_path = ''
        for item in path.split('/'):
            if item == '':
                continue
            try:
                full_path += f'/{item}'
                sftp.chdir(full_path)  # Test if remote_path exists
            except IOError:
                sftp.mkdir(full_path)  # Create remote_path
                sftp.chdir(full_path)


    def __upload_list_files(
            self,
            sftp: SFTPClient,
            src_item: SftpFileItemEntity,
    ):
        if src_item.is_file:

            get_parent_path = '/'.join(src_item.instance_path.split('/')[0:-1])
            self.__make_dirs_by_sftp(sftp=sftp, path=get_parent_path)

            self.__upload_one_file(
                sftp=sftp,
                src_path=src_item.path,
                dest_path=src_item.instance_path,
                file_name=src_item.name,
                file_size=src_item.file_size,
                container_path=src_item.container_path
            )
        elif src_item.is_folder:
            self.__make_dirs_by_sftp(sftp=sftp, path=src_item.instance_path)
            for item in src_item.children:
                self.__upload_list_files(
                    sftp=sftp,
                    src_item=item,
                )


    def __convert_size(self, size_bytes):
        if size_bytes == 0:
            return "0B"
        size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return "%s %s" % (s, size_name[i])


    def __download_one_file(
            self,
            sftp: SFTPClient,
            src_path: str,
            dest_path: str,
            file_name: str,
            file_size: [int] = 100
    ) -> bool:
        has_error = False
        try:
            with typer.progressbar(length=file_size, label=__("Downloading %file_name% (%file_size%)", {'file_name': file_name, 'file_size': self.__convert_size(file_size)})) as progress:
                def __show_result_copy(size: int, full_size: int):
                    global old_value
                    progress.update(size - (old_value or 0))
                    old_value = size
                    if old_value == full_size:
                        old_value = 0
                sftp.get(remotepath=src_path, localpath=f"{dest_path}", callback=__show_result_copy)
            typer.echo(__('Downloaded as %file_path%', {'file_path': dest_path}))
        except FileNotFoundError as err:
            app_logger.exception(f"Error retrieving file {file_name} from container (file not found): {err}")
            typer.echo(__("Error retrieving file: file not found on server"))
            has_error = True
        except Exception as err2:
            typer.echo(err2)
            app_logger.exception(f"Error retrieving file {file_name} from container: {err2}")
            typer.echo(__("Error retrieving file: undefined server error"))
            has_error = True
        return has_error


    def __download_list_files(
            self,
            sftp: SFTPClient,
            src_item: SftpFileItemEntity,
    ):
        if src_item.is_file:
            self.__file_system_service.get_path('/'.join(src_item.dest_path.split('/')[0:-1]), auto_create=True)
            self.__download_one_file(
                sftp=sftp,
                src_path=src_item.path,
                dest_path=src_item.dest_path,
                file_name=src_item.name,
                file_size=src_item.file_size,
            )
        elif src_item.is_folder:
            self.__file_system_service.get_path(str(Path(src_item.dest_path)), auto_create=True)
            for item in src_item.children:
                self.__download_list_files(
                    sftp=sftp,
                    src_item=item,
                    #dest_path=src_item.dest_path,
                )

    @staticmethod
    def find_sftp_server_path(
            client: SSHClient,
    ) -> Optional[str]:
        stdin, stdout, stderr = client.exec_command(f'whereis sftp-server', get_pty=True)
        for line in stdout.readlines():
            pre_line = line.replace('sftp-server:', '')
            for command in pre_line.strip().split(' '):
                tmp = command.strip()
                if tmp:
                    if tmp.endswith('/sftp-server'):
                        return tmp
        return None

    def copy_data_on_container(
            self,
            client: SSHClient,
            docker_name: str,
            src_path: str,
            dest_path: str,
            is_recursive: bool = False,
    ):
        self.start_command_on_container(
            client=client,
            docker_name=docker_name,
            command=['cp ' + ('-R' if is_recursive else '') + f' {src_path}' + f' {dest_path}'],
        )
        # TODO: dont now how, need check for copy end!!!!
        sleep(3)

    @staticmethod
    def start_command_on_container(
            client: SSHClient,
            docker_name: str,
            command: List[str],
            is_bash: bool = False,
    ):
        if is_bash:
            stdin, stdout, stderr = client.exec_command(f'docker exec -it {docker_name} /bin/bash -c "{";".join(command)}"', get_pty=True)
        else:
            stdin, stdout, stderr = client.exec_command(f'docker exec -it {docker_name}  {command[0]}', get_pty=True)
        for line in stdout.readlines():
            pass


    def __build_sftp_client(
            self,
            ip_address: str,
            username: str,
            private_key_path: Optional[str],
    ) -> Tuple[SSHClient, SFTPClient]:
        client: Optional[SSHClient] = self.__get_client(ip_address=ip_address, username=username, private_key_path=private_key_path)
        sftp_server_path = self.find_sftp_server_path(client=client)

        if not sftp_server_path:
            typer.echo(__('SFTP server is not installed on the server instance'))
            raise typer.Exit(1)

        chan = client.get_transport().open_session()
        # chan.exec_command("sudo su -c /usr/lib/openssh/sftp-server")
        chan.exec_command(f"sudo su -c {sftp_server_path}")
        sftp = paramiko.SFTPClient(chan)

        return client, sftp

    # TODO what the fuck does this method do?
    @staticmethod
    def _check_if_file_name_in_path(path: str, file_template: Optional[str] = None) -> bool:
        # strange logic
        file_name = path.split('/')[-1] if path else None
        if file_name and '.' in file_name:
            if file_template and '.' in file_template:
                extension = file_template.split('.')[-1]
                if extension in file_name:
                    return True
            else:
                return True
        return False

    @staticmethod
    def _get_parent_from_path(path: str) -> str:
        pre_path = '/'.join(path.split('/')[0:-1])
        if not pre_path:
            return '/'
        else:
            return pre_path


    def __build_path_mapping_for_upload(
            self,
            files: List[FileItemEntity],
            instance_path: str,
            container_path: str,
            copy_only_folder_contents: bool,
            has_parent: bool = False,
    ) -> List[SftpFileItemEntity]:
        result = []
        for item in files:
            elem = SftpFileItemEntity.model_validate(item.model_dump())
            if item.is_file:
                # TODO god knows what is happening here
                # if uploading a single file without extension: has_file_name must be true if destination is not a folder
                has_file_name = self._check_if_file_name_in_path(
                    path=instance_path,
                    file_template=item.name,
                )

                if not has_parent and has_file_name:
                    elem.instance_path = instance_path
                    elem.container_path = container_path
                else:
                    elem.instance_path = f"{instance_path}/{item.name}"
                    elem.container_path = f"{container_path}/{item.name}"

                elem.dest_path = elem.instance_path

            else:
                if not has_parent and copy_only_folder_contents:
                    elem.instance_path = instance_path
                    elem.container_path = container_path
                else:
                    elem.instance_path = f"{instance_path}/{item.name}"
                    elem.container_path = f"{container_path}/{item.name}"

                elem.dest_path = elem.instance_path

            if len(item.children) > 0:
                elem.children = []
                elem.children.extend(self.__build_path_mapping_for_upload(
                    files=item.children,
                    instance_path=elem.instance_path,
                    container_path=elem.container_path,
                    copy_only_folder_contents=copy_only_folder_contents,
                    has_parent=True,
                ))

            result.append(elem)

        return result

    def upload_data_to_container(
            self,
            ip_address: str,
            username: str,
            src_path: str,
            dest_path: str,
            instance_path: str,
            container_path: str,
            copy_only_folder_contents: bool,
            private_key_path: Optional[str],
    ):
        has_error = False
        client, sftp = self.__build_sftp_client(username=username, ip_address=ip_address, private_key_path=private_key_path)

        origin_files: List[FileItemEntity] = self.__file_system_service.get_path_items(src_path)

        files: List[SftpFileItemEntity] = self.__build_path_mapping_for_upload(
            files=origin_files,
            instance_path=instance_path,
            container_path=container_path,
            copy_only_folder_contents=copy_only_folder_contents
        )

        try:
            for item in files:
                self.__upload_list_files(
                    sftp=sftp,
                    src_item=item,
                )

            if len(files) == 0:
                typer.echo(__("No source files could be found on the server"))
                raise typer.Exit(1)

            if len(files[0].children) == 0 and files[0].is_folder:
                typer.echo(__("Source directory is empty"))
                raise typer.Exit(1)

        except FileNotFoundError as err:
            app_logger.error(f"Error uploading file to container {ip_address}, user {username} (file not found): {err}")
            typer.echo(__("Error uploading file: file not found on server"))
            has_error = True
        finally:
            sftp.close()

        client.close()
        if has_error:
            raise typer.Exit(1)


    def __read_remote_path_items_for_download(
            self,
            sftp: SFTPClient,
            current_path: str,
            dest_path: str,
            instance_path: str,
            copy_only_folder_contents: bool,
            depth: int = 0,
    ) -> List[SftpFileItemEntity]:
        config = self.__config_provider.get_config()
        path_items = []
        try:
            root_stat = sftp.stat(current_path)
            parent = SftpFileItemEntity(
                name=current_path.split('/')[-1],
                path=current_path,
                is_file=stat.S_ISREG(root_stat.st_mode),
                is_folder=stat.S_ISDIR(root_stat.st_mode),
                file_size=root_stat.st_size,
                instance_path=instance_path,
                dest_path=dest_path,
            )

            if depth == 0 and not copy_only_folder_contents and parent.is_folder:
                parent.dest_path = parent.dest_path.rstrip("/") + "/" + parent.name
            path_items.append(parent)
            if parent.is_file:
                # must be true if destination is file
                # must be false if destination is dir
                # if destination does not exist, destination is file (true)
                treat_as_file = True
                dest_fullpath = Path(config.runtime.working_directory + '/' + dest_path)
                if dest_fullpath.exists() and dest_fullpath.is_dir():
                    treat_as_file = False

                if not treat_as_file:
                    parent.dest_path += f"{parent.name}" if parent.dest_path.endswith('/') else f"/{parent.name}"

            elif parent.is_folder:
                sftp.chdir(current_path)
                if depth > 0:
                    parent.dest_path += f"{parent.name}" if parent.dest_path.endswith('/') else f"/{parent.name}"
                for item in sftp.listdir_attr():
                    next_path = f'{current_path}/{item.filename}'
                    is_dir = stat.S_ISDIR(item.st_mode)
                    is_file = stat.S_ISREG(item.st_mode)
                    if is_file:
                        parent.children.append(SftpFileItemEntity(
                            name=item.filename,
                            path=next_path,
                            is_file=is_file,
                            is_folder=is_dir,
                            file_size=item.st_size,
                            instance_path=f'{instance_path}/{item.filename}',
                            dest_path=f'{parent.dest_path}/{item.filename}',
                        ))
                    elif is_dir:
                        parent.children.extend(self.__read_remote_path_items_for_download(
                            sftp=sftp,
                            current_path=next_path,
                            dest_path=parent.dest_path,
                            instance_path=parent.instance_path,
                            depth=depth + 1,
                            copy_only_folder_contents=copy_only_folder_contents,
                        ))
            return path_items
        except FileNotFoundError as ex:
            app_logger.exception(f"Unable to read remote file list: {ex}")
            typer.echo(__("Could not find the requested object on remote instance: %path%", {'path': current_path}))
            raise typer.Exit(1)
        except Exception as ex:
            app_logger.exception(f"Error occurred: {ex}")
            typer.echo(__('Error occurred while processing the file'))
            raise typer.Exit(1)


    def download_data_from_container(
            self,
            ip_address: str,
            username: str,
            dest_path: str,
            instance_path: str,
            copy_only_folder_contents: bool,
            private_key_path: Optional[str],
    ):
        has_error = False

        client, sftp = self.__build_sftp_client(username=username, ip_address=ip_address, private_key_path=private_key_path)

        try:
            files: List[SftpFileItemEntity] = self.__read_remote_path_items_for_download(
                sftp=sftp,
                current_path=instance_path,
                instance_path=instance_path,
                dest_path=dest_path,
                copy_only_folder_contents=copy_only_folder_contents,
            )

            if len(files) == 0:
                typer.echo(__("No source files could be found on the server"))
                raise typer.Exit(1)

            if len(files[0].children) == 0 and files[0].is_folder:
                typer.echo(__("Source directory is empty"))
                raise typer.Exit(1)

            for item in files:
                self.__download_list_files(
                    sftp=sftp,
                    src_item=item,
                )
        except FileNotFoundError as err:
            print(err)
            app_logger.error(f"Error uploading file to container {ip_address} for user {username} (file not found): {err}")
            typer.echo(__("Error uploading file: file not found on server"))
            has_error = True
        finally:
            sftp.close()

        client.close()
        if has_error:
            raise typer.Exit(1)
