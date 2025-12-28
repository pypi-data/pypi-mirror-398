from enum import Enum


class ProviderNameEnumDto(str, Enum):
    Amazon: str = 'Amazon'
    DigitalOcean: str = 'DigitalOcean' # old
    Exoscale: str = 'Exoscale'  # old
    Vultr: str = 'Vultr'    # old
    Nebius: str = 'Nebius'
    Azure: str = 'Azure'
    UNKNOWN: str = 'UNKNOWN'
