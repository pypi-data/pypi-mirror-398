from dataclasses import dataclass

from avatar_yaml.models.common import Metadata, ModelKind
from avatar_yaml.yaml_utils import to_yaml


@dataclass(frozen=True)
class VolumeSpec:
    url: str


@dataclass(frozen=True)
class Volume:
    kind: ModelKind
    metadata: Metadata
    spec: VolumeSpec


def get_volume(name: str, url: str) -> str:
    """Get the yaml from a volume."""
    volume = Volume(
        kind=ModelKind.VOLUME,
        metadata=Metadata(name=name),
        spec=VolumeSpec(url=url),
    )

    return to_yaml(volume)
