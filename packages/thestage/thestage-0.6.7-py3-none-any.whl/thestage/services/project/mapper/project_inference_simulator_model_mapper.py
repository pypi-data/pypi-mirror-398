from typing import Optional

from thestage.entities.project_inference_simulator_model import ProjectInferenceSimulatorModelEntity
from thestage.services.abstract_mapper import AbstractMapper
from thestage.services.project.dto.inference_simulator_model_dto import InferenceSimulatorModelDto


class ProjectInferenceSimulatorModelMapper(AbstractMapper):
    def build_entity(self, item: InferenceSimulatorModelDto) -> Optional[ProjectInferenceSimulatorModelEntity]:
        if not item:
            return None

        return ProjectInferenceSimulatorModelEntity(
            public_id=item.public_id,
            slug=item.slug,
            status=item.status or '',
            commit_hash=item.commit_hash or '',
            environment_metadata=item.environment_metadata or {},
            started_at=item.created_at or '',
            finished_at=item.updated_at or ''  # TODO updated_at cannot be finished_at
        )
