import traceback
from typing import Any, Callable

import requests
import typer
from click.exceptions import Exit, Abort
from git import GitCommandError
from paramiko.ssh_exception import PasswordRequiredException

from thestage.config import THESTAGE_API_URL
from thestage.exceptions.file_system_exception import FileSystemException
from thestage.exceptions.remote_server_exception import RemoteServerException
from thestage.i18n.translation import __
from thestage.exceptions.git_access_exception import GitAccessException
from thestage.exceptions.auth_exception import AuthException
from thestage.exceptions.business_logic_exception import BusinessLogicException
from thestage.exceptions.config_exception import ConfigException
from thestage.helpers.logger.app_logger import app_logger
from thestage.services.clients.thestage_api.core.http_client_exception import HttpClientException


def error_handler() -> Callable:
    def wrap(f):
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                result = f(*args, **kwargs)
                return result
            except AuthException as e1:
                typer.echo(__('Authentication failed: update API token'))
                app_logger.error(f'{traceback.format_exc()}')
                raise typer.Exit(1)
            except BusinessLogicException as e2:
                typer.echo(__('Business logic error encountered: contact TheStage AI team'))
                app_logger.error(f'{traceback.format_exc()}')
                raise typer.Exit(1)
            except ConfigException as e3:
                typer.echo(__(
                    'Configuration error encountered: %error_message%',
                    {
                        'error_message': e3.get_message()
                    }
                ))
                app_logger.error(f'{traceback.format_exc()}')
                raise typer.Exit(1)
            except FileSystemException as e4:
                typer.echo(__(
                    "File system error encountered: %error_message%",
                    {
                        'error_message': e4.get_message()
                    }
                ))
                app_logger.error(f'{traceback.format_exc()}')
                raise typer.Exit(1)
            except HttpClientException as e5:
                typer.echo(__(
                    f"TheStage server error: %error_message%",

                    {
                        'stage_url': THESTAGE_API_URL,
                        'error_message': e5.get_message()
                    }
                ))
                app_logger.error(f"Connection error to {THESTAGE_API_URL} - {e5}")
                app_logger.error(f'{traceback.format_exc()}')
                raise typer.Exit(1)
            except GitAccessException as e6:
                typer.echo(e6.get_message())
                typer.echo(e6.get_dop_message())
                typer.echo(__(
                    "Visit %git_url% to accept the invitation or check your access to the repository",
                    {
                        'git_url': e6.get_url(),
                    }
                ))
                app_logger.error(f'{traceback.format_exc()}')
                raise typer.Exit(1)
            except GitCommandError as e7:
                typer.echo(f'Git command error encountered: {e7.stdout} \n {e7.stderr} (status: {e7.status})')
                app_logger.error(f'{traceback.format_exc()}')
                raise typer.Exit(1)
            except RemoteServerException as e8:
                typer.echo(__(
                    'Error connecting to server or Docker container at %ip_address% as %username%',
                    {
                        'ip_address': e8.ip_address,
                        'username': e8.username,
                    }))
                app_logger.error(f'Error connecting to server or Docker container at {e8.ip_address} as {e8.username} - {e8}')
                app_logger.error(f'{traceback.format_exc()}')
                raise typer.Exit(1)
            except Abort as e9:
                app_logger.error(f'{traceback.format_exc()}')
                raise typer.Exit(1)
            except requests.exceptions.ConnectionError as e10:
                # TODO we don't know for sure if it is Thestage connection error - throw appropriate exception (on token validation?)
                typer.echo("Connection error")
                app_logger.error(f'{traceback.format_exc()}')
                raise typer.Exit(1)
            except PasswordRequiredException as e11:
                # technically we can use encrypted keys but dealing with passwords is big bs
                typer.echo("Provided key requires password. Please use non-encrypted key.")
                app_logger.error(f'{traceback.format_exc()}')
                raise typer.Exit(1)
            except Exception as e100:
                if isinstance(e100, Exit):
                    raise e100
                else:
                    typer.echo(__('Undefined error occurred'))
                    # typer.echo(e100.__class__.__name__)
                    # print(traceback.format_exc())
                    # TODO send all exceptions to backend?
                    app_logger.error(f'{traceback.format_exc()}')
                    raise typer.Exit(1)
        return wrapper
    return wrap
