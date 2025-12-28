from typing import Optional

from thestage.entities.project_task import ProjectTaskEntity
from thestage.services.abstract_mapper import AbstractMapper
from thestage.services.task.dto.task_dto import TaskDto


class ProjectTaskMapper(AbstractMapper):

    def build_entity(self, item: TaskDto) -> Optional[ProjectTaskEntity]:
        if not item:
            return None

        return ProjectTaskEntity(
            public_id=item.public_id or '',
            title=item.title or '',
            status=item.frontend_status.status_translation or '',
            docker_container_public_id=item.docker_container_public_id,
            started_at=item.started_at or '',
            finished_at=item.finished_at or '',
        )
