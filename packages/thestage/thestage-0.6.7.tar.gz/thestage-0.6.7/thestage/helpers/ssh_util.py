from typing import Optional, List

import typer
from paramiko.dsskey import DSSKey
from paramiko.ecdsakey import ECDSAKey
from paramiko.ed25519key import Ed25519Key
from paramiko.pkey import PKey
from paramiko.rsakey import RSAKey
from paramiko.ssh_exception import SSHException, PasswordRequiredException


def parse_private_key(filename: str) -> Optional[PKey]:
    error_output: List[str] = []
    pkey: Optional[PKey] = None
    pkey_class: Optional[str] = None

    for pkey_class_item in (RSAKey, ECDSAKey, DSSKey, Ed25519Key):
        try:
            key = pkey_class_item.from_private_key_file(filename=filename)
            pkey = key
            pkey_class = pkey_class_item.__name__
            break
        except PasswordRequiredException as e1:
            raise e1
        except SSHException as e2:
            error_output.append(f'[{pkey_class_item.__name__}]: {str(e2)}')
        except Exception as e3:
            error_output.append(f'[{pkey_class_item.__name__}]: Unexpected error: {e3.__class__.__name__}: {str(e3)}')

    if pkey is None:
        for line in error_output:
            typer.echo(line)

    if pkey_class and pkey_class == 'DSSKey':
        typer.echo('DSA keys are not supported')
        return None

    return pkey
