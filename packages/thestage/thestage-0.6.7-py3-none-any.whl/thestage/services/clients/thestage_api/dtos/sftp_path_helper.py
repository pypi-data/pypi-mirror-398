from typing import Optional, List

from pydantic import Field

from thestage.entities.file_item import FileItemEntity


class SftpFileItemEntity(FileItemEntity):

    instance_path: Optional[str] = Field(None)
    container_path: Optional[str] = Field(None)
    children: List['SftpFileItemEntity'] = Field(default=[])
    dest_path: Optional[str] = Field(None)
