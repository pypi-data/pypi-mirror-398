from dataclasses import dataclass
from enum import StrEnum


@dataclass
class Metadata:
    name: str


class ModelKind(StrEnum):
    VOLUME = "AvatarVolume"
    SCHEMA = "AvatarSchema"
    AVATARIZATION_PARAMETERS = "AvatarParameters"
    PRIVACY_METRICS_PARAMETERS = "AvatarPrivacyMetricsParameters"
    SIGNAL_METRICS_PARAMETERS = "AvatarSignalMetricsParameters"
    REPORT = "AvatarReportParameters"
    ADVICE = "AvatarAdviceParameters"
    METADATA = "AvatarMetadata"
