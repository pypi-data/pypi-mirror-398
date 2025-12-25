from dataclasses import dataclass
from enum import Enum, StrEnum
from typing import Any

from avatar_yaml.models.common import Metadata, ModelKind
from avatar_yaml.yaml_utils import to_yaml


class AugmentationStrategy(StrEnum):
    minority = "minority"
    not_majority = "not_majority"


@dataclass(frozen=False)
class DataAugmentationParameters:
    augmentation_strategy: float | AugmentationStrategy | dict[str, float]
    target_column: str | None


@dataclass(frozen=False)
class AvatarizationParameters:
    k: int
    ncp: int | None = None
    use_categorical_reduction: bool | None = None
    column_weights: dict[str, float] | None = None
    exclude_variables: dict[str, Any] | None = None
    imputation: dict[str, Any] | None = None
    data_augmentation: DataAugmentationParameters | None = None


@dataclass(frozen=False)
class TimeSeriesParameters:
    projection: dict[str, Any] | None = None
    alignment: dict[str, Any] | None = None


@dataclass(frozen=False)
class AvatarizationDPParameters:
    epsilon: float | None = None
    preprocess_budget_ratio: float | None = None
    ncp: int | None = None
    use_categorical_reduction: bool | None = None
    column_weights: dict[str, float] | None = None
    exclude_variables: dict[str, Any] | None = None
    imputation: dict[str, Any] | None = None
    data_augmentation: DataAugmentationParameters | None = None


class AlignmentMethod(str, Enum):
    SPECIFIED = "specified"
    MAX = "max"
    MIN = "min"
    MEAN = "mean"


class ProjectionType(str, Enum):
    FPCA = "fpca"
    FLATTEN = "flatten"


class ImputeMethod(str, Enum):
    KNN = "knn"
    MODE = "mode"
    MEDIAN = "median"
    MEAN = "mean"
    FAST_KNN = "fast_knn"


class ExcludeVariablesMethod(str, Enum):
    """The method to exclude column."""

    ROW_ORDER = "row_order"
    """SENSITIVE The excluded column will be linked to the original row order.
    This is a violation of privacy."""
    COORDINATE_SIMILARITY = "coordinate_similarity"
    """The excluded column will be linked by individual similarity."""


class ReportType(str, Enum):
    BASIC = "basic"
    PIA = "pia"


class OutputFormat(str, Enum):
    PDF = "pdf"
    DOCX = "docx"


@dataclass(frozen=False)
class SignalMetricsParameters:
    ncp: int | None = None
    use_categorical_reduction: bool | None = None
    imputation: dict[str, Any] | None = None
    column_weights: dict[str, float] | None = None
    exclude_variables: dict[str, Any] | None = None


@dataclass(frozen=False)
class PrivacyMetricsParameters:
    ncp: int | None = None
    use_categorical_reduction: bool | None = None
    known_variables: list[str] | None = None
    target: str | None = None
    quantile_threshold: int | None = None
    imputation: dict[str, Any] | None = None
    exclude_variables: dict[str, Any] | None = None
    column_weights: dict[str, float] | None = None


@dataclass(frozen=True)
class Results:
    volume: str | None = None
    path: str | None = None
    format: str | None = None
    name_template: str | None = None
    max_distribution_plots: int | None = None


@dataclass(frozen=True)
class ReportParametersSpec:
    report_type: str = ReportType.BASIC.value
    output_format: str = OutputFormat.PDF.value
    results: Results | None = None


@dataclass(frozen=True)
class Report:
    kind: ModelKind
    metadata: Metadata
    spec: ReportParametersSpec


def get_report_parameters(
    metadata: Metadata,
    report_type: ReportType = ReportType.BASIC,
    results: Results | None = None,
    output_format: OutputFormat = OutputFormat.PDF,
) -> str:
    spec = ReportParametersSpec(
        report_type=report_type.value,
        output_format=output_format.value,
        results=results,
    )

    report = Report(
        kind=ModelKind.REPORT,
        metadata=metadata,
        spec=spec,
    )
    return to_yaml(report)


@dataclass(frozen=True)
class ParametersSpec:
    schema: str
    avatarization: dict[str, AvatarizationParameters] | None = None
    avatarization_dp: dict[str, AvatarizationDPParameters] | None = None
    avatarization_ref: str | None = None
    time_series: dict[str, TimeSeriesParameters] | None = None
    time_series_ref: str | None = None
    privacy_metrics: dict[str, PrivacyMetricsParameters] | None = None
    signal_metrics: dict[str, SignalMetricsParameters] | None = None
    results: Results | None = None
    seed: int | None = None


@dataclass(frozen=True)
class Parameters:
    kind: ModelKind
    metadata: Metadata
    spec: ParametersSpec


def get_avatarization_parameters(
    metadata: Metadata,
    schema_name: str,
    avatarization: dict[str, AvatarizationParameters] | None = None,
    time_series: dict[str, TimeSeriesParameters] | None = None,
    avatarization_dp: dict[str, AvatarizationDPParameters] | None = None,
    seed: int | None = None,
    results=Results(volume="local-temp-results"),
) -> str:
    if not avatarization and not time_series and not avatarization_dp:
        raise ValueError(
            "Expected at least one of avatarization, avatarization_dp, or time_series"
        )

    spec = ParametersSpec(
        seed=seed,
        schema=schema_name,
        avatarization=avatarization,
        time_series=time_series,
        avatarization_dp=avatarization_dp,
        results=results,
    )

    params = Parameters(
        kind=ModelKind.AVATARIZATION_PARAMETERS,
        metadata=metadata,
        spec=spec,
    )
    return to_yaml(params)


def get_privacy_metrics_parameters(
    metadata: Metadata,
    schema_name: str,
    privacy_metrics: dict[str, PrivacyMetricsParameters] | None = None,
    time_series: dict[str, TimeSeriesParameters] | None = None,
    seed: int | None = None,
    avatarization_ref: str | None = None,
    results: Results | None = None,
) -> str:
    spec = ParametersSpec(
        seed=seed,
        schema=schema_name,
        privacy_metrics=privacy_metrics,
        time_series=time_series,
        avatarization_ref=avatarization_ref,
        results=results,
    )

    params = Parameters(
        kind=ModelKind.PRIVACY_METRICS_PARAMETERS,
        metadata=metadata,
        spec=spec,
    )
    return to_yaml(params)


def get_signal_metrics_parameters(
    metadata: Metadata,
    schema_name: str,
    signal_metrics: dict[str, SignalMetricsParameters] | None = None,
    time_series: dict[str, TimeSeriesParameters] | None = None,
    seed: int | None = None,
    avatarization_ref: str | None = None,
    results: Results | None = None,
) -> str:
    spec = ParametersSpec(
        seed=seed,
        schema=schema_name,
        signal_metrics=signal_metrics,
        time_series=time_series,
        avatarization_ref=avatarization_ref,
        results=results,
    )

    params = Parameters(
        kind=ModelKind.SIGNAL_METRICS_PARAMETERS,
        metadata=metadata,
        spec=spec,
    )
    return to_yaml(params)
