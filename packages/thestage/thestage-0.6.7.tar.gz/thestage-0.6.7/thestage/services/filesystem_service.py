import json
import os
import shutil
from json import JSONDecodeError
from pathlib import Path
from typing import Optional, List, Dict, Any

from thestage.entities.file_item import FileItemEntity
from thestage.exceptions.file_system_exception import FileSystemException


class FileSystemService:

    def get_ssh_path(self) -> Optional[Path]:
        home_path = self.get_home_path()
        ssh_path = home_path.joinpath('.ssh')
        if not ssh_path.exists():
            raise FileSystemException(f"Path does not exist: {ssh_path}")
        return ssh_path

    def get_home_path(self) -> Optional[Path]:
        try:
            return Path.home()
        except RuntimeError | OSError as ex1:
            raise FileSystemException("Error getting user home path") from ex1

    def create_if_not_exists_dir(self, path: Path) -> Path:
        if not path.exists():
            try:
                path.mkdir(exist_ok=True, parents=True)
            except FileNotFoundError as ex1:
                raise FileSystemException(message=f"FileNotFoundError (dir): {path}") from ex1
            except OSError as ex2:
                raise FileSystemException(message=f"Could not create directory: {path}") from ex2
        return path

    def create_if_not_exists_file(self, path: Path) -> Path:
        if not path.exists():
            try:
                path.touch(exist_ok=True)
            except FileNotFoundError as ex1:
                raise FileSystemException(message=f"FileNotFoundError (file): {path}") from ex1
            except OSError as ex2:
                raise FileSystemException(message=f"Could not create file: {path}") from ex2
        return path

    def get_path(self, directory: str, auto_create: bool = True) -> Path:
        path = Path(directory)
        if auto_create:
            self.create_if_not_exists_dir(path)
        return path

    def is_folder_empty(self, folder: str, auto_create: bool) -> bool:
        path = self.get_path(folder, auto_create)
        if not path.exists():
            return True
        if not path.is_dir():
            raise FileSystemException(message=f"Expected directory but found a file: {path}")
        objects = os.listdir(path)
        if len(objects) == 0:
            return True
        else:
            return False

    def is_folder_exists(self, folder: str, auto_create: bool = True) -> bool:
        path = self.get_path(folder, auto_create=auto_create)
        if path.exists():
            return True
        else:
            return False

    def find_line_in_text_file(self, file: str, find: str) -> bool:
        path = self.get_path(file, auto_create=False)
        if path and path.exists():
            with open(path, 'r') as file:
                for line in file.readlines():
                    if (find + "\n") == line:
                        return True
        return False

    def add_line_to_text_file(self, file: str, new_line: str):
        path = self.get_path(file, auto_create=False)
        if path and path.exists():
            with open(path, 'a') as file:
                file.write(new_line)
                file.write('\n')

    # TODO remove this fucking useless shit
    def check_if_path_exist(self, file: str) -> bool:
        path = self.get_path(file, auto_create=False)
        if path.exists():
            return True
        else:
            return False

    def get_path_items(self, folder: str) -> List[FileItemEntity]:
        path = self.get_path(folder, auto_create=False)
        path_items = []
        if not path.exists():
            return path_items

        parent = FileItemEntity.build_from_path(path=path)
        path_items.append(parent)
        if path.is_dir():
            objects = os.listdir(path)
            if objects:
                for item in objects:
                    elem = path.joinpath(item)
                    if elem.is_dir():
                        parent.children.extend(self.get_path_items(folder=str(elem)))
                    else:
                        parent.children.append(FileItemEntity.build_from_path(path=elem))
        return path_items

    def remove_folder(self, path: str):
        real_path = self.get_path(directory=path, auto_create=False)
        if real_path and real_path.exists():
            shutil.rmtree(real_path)


    def read_config_file(self, path: Path) -> Dict[str, Any]:
        result = {}
        try:
            if path and path.exists():
                with path.open("r") as file:
                    try:
                        if os.stat(path).st_size != 0:
                            result = json.load(file)
                    except JSONDecodeError as e:
                        raise Exception(f"Config file is malformed: {path}") from e
        except OSError:
            raise FileSystemException(f"Could not open config file: {path}")
        return result
