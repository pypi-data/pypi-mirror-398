from typing import Optional

from thestage.entities.rented_instance import RentedInstanceEntity
from thestage.services.clients.thestage_api.dtos.instance_rented_response import InstanceRentedDto
from thestage.services.abstract_mapper import AbstractMapper


class InstanceMapper(AbstractMapper):

    def build_entity(self, item: InstanceRentedDto) -> Optional[RentedInstanceEntity]:
        if not item:
            return None

        return RentedInstanceEntity(
            slug=item.slug if item.slug else '',
            public_id=item.public_id if item.public_id else '',
            cpu_type=item.cpu_type if item.cpu_type else '',
            gpu_type=item.gpu_type if item.gpu_type else '',
            cpu_cores=str(item.cpu_cores) if item.cpu_cores else '',
            ip_address=item.ip_address if item.ip_address else '',
            status=item.frontend_status.status_translation if item.frontend_status else '',
        )
