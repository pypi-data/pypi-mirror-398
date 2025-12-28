from typing import Optional

from thestage.entities.project_inference_simulator import ProjectInferenceSimulatorEntity
from thestage.services.abstract_mapper import AbstractMapper
from thestage.services.project.dto.inference_simulator_dto import InferenceSimulatorDto


class ProjectInferenceSimulatorMapper(AbstractMapper):

    def build_entity(self, item: InferenceSimulatorDto) -> Optional[ProjectInferenceSimulatorEntity]:
        if not item:
            return None

        return ProjectInferenceSimulatorEntity(
            public_id=item.public_id or '',
            slug=item.slug or '',
            status=item.status or '',
            http_endpoint=item.http_endpoint or '',
            grpc_endpoint=item.grpc_endpoint or '',
            metrics_endpoint=item.metrics_endpoint or '',
            started_at=item.created_at or '',
        )
