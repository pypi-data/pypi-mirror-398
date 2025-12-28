from typing import Optional, Tuple

from thestage.services.clients.thestage_api.dtos.container_response import DockerContainerDto
from thestage.entities.container import DockerContainerEntity
from thestage.services.abstract_mapper import AbstractMapper


class ContainerMapper(AbstractMapper):

    def build_entity(self, item: DockerContainerDto) -> Optional[DockerContainerEntity]:
        if not item:
            return None

        instance_type = ''
        instance_slug = ''
        if item.instance_rented:
            instance_type = 'RENTED'
            instance_slug = item.instance_rented.slug
        if item.selfhosted_instance:
            instance_type = 'SELF-HOSTED'
            instance_slug = item.selfhosted_instance.slug

        return DockerContainerEntity(
            status=item.frontend_status.status_translation if item.frontend_status else '',
            public_id=item.public_id or '',
            slug=item.slug or '',
            project_slug=item.project.slug if item.project else '',
            instance_type=instance_type,
            instance_slug=instance_slug,
            docker_image=item.docker_image or '',
        )
