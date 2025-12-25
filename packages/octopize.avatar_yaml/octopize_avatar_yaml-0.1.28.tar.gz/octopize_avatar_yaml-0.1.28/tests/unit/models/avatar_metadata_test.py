from avatar_yaml.models.avatar_metadata import (
    AvatarMetadataSpec,
    DataRecipient,
    DataSubject,
    DataType,
    PiaMetadata,
    SensitivityLevel,
    get_metadata,
)


def test_pia_metadata_fields():
    pia = PiaMetadata(
        datarecipient=DataRecipient.INTERNAL,
        data_type=DataType.HEALTH,
        datasubject=DataSubject.PATIENTS,
        sensitivity_level=SensitivityLevel.HIGH,
    )
    assert pia.datarecipient == DataRecipient.INTERNAL
    assert pia.data_type == DataType.HEALTH
    assert pia.datasubject == DataSubject.PATIENTS
    assert pia.sensitivity_level == SensitivityLevel.HIGH


def test_avatar_metadata_spec_with_pia():
    pia = PiaMetadata(
        datarecipient=DataRecipient.OPENDATA,
        data_type=DataType.FINANCE,
        datasubject=DataSubject.CLIENTS,
        sensitivity_level=SensitivityLevel.LOW,
    )
    spec = AvatarMetadataSpec(display_name="Test Avatar", pia_metadata=pia)
    assert spec.display_name == "Test Avatar"
    assert spec.pia_metadata == pia


def test_get_metadata_with_annotations():
    meta = get_metadata(display_name="Test", annotations={"foo": "bar"})
    assert meta.kind.value == "AvatarMetadata"
    assert meta.metadata.name == "avatar-metadata-Test"
    assert meta.spec.display_name == "Test"
    assert meta.annotations["foo"] == "bar"
