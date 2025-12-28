from abc import ABC, abstractmethod
from typing import Any, Optional, Tuple


class AbstractMapper(ABC):

    @abstractmethod
    def build_entity(self, item: Any) -> Optional[Any]:
        raise NotImplementedError()
