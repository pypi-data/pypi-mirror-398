import pytest

from avatar_yaml.models.common import Metadata, ModelKind
from avatar_yaml.models.volume import Volume, VolumeSpec, get_volume
from tests.conftest import from_pretty_yaml


@pytest.fixture
def volume():
    return Volume(
        kind=ModelKind.VOLUME,
        metadata=Metadata(name="test_metadata"),
        spec=VolumeSpec(url="http://example.com"),
    )


def test_volume_to_yaml(volume: Volume):
    expected_yaml = from_pretty_yaml("""
kind: AvatarVolume
metadata:
  name: test_metadata
spec:
  url: http://example.com
""")
    output = get_volume(name="test_metadata", url="http://example.com")
    assert output == expected_yaml
