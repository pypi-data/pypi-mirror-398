import pytest

from avatar_yaml.models.common import Metadata
from avatar_yaml.models.parameters import (
    AvatarizationDPParameters,
    AvatarizationParameters,
    PrivacyMetricsParameters,
    Results,
    SignalMetricsParameters,
    TimeSeriesParameters,
    get_avatarization_parameters,
    get_privacy_metrics_parameters,
    get_signal_metrics_parameters,
)
from avatar_yaml.yaml_utils import aggregate_yamls
from tests.conftest import from_pretty_yaml


def test_avatarization_parameters_to_yaml() -> None:
    avat1 = AvatarizationParameters(k=5, use_categorical_reduction=True, ncp=2)

    yaml = get_avatarization_parameters(
        metadata=Metadata(name="simple"),
        avatarization={"iris": avat1},
        schema_name="simple_iris",
        results=Results(volume="local-temp-results"),
        seed=1234,
    )

    expected = from_pretty_yaml("""
kind: AvatarParameters
metadata:
  name: simple
spec:
  schema: simple_iris
  avatarization:
    iris:
      k: 5
      ncp: 2
      use_categorical_reduction: true
  results:
    volume: local-temp-results
  seed: 1234
""")
    assert yaml == expected


def test_multi_table_and_ts_avatarization_parameters_to_yaml() -> None:
    avat1 = AvatarizationParameters(k=5)
    avat2 = AvatarizationParameters(k=2)
    avat3_ts = TimeSeriesParameters(
        projection={"nf": 2, "projection_type": "fpca"},
        alignment={"method": "mean", "nb_points": 3},
    )
    yaml = get_avatarization_parameters(
        metadata=Metadata(name="multi_table"),
        avatarization={
            "parent": avat1,
            "child": avat2,
        },
        time_series={"child_ts": avat3_ts},
        schema_name="multi_table",
        results=Results(volume="local-temp-results"),
        seed=123,
    )

    expected = from_pretty_yaml("""
kind: AvatarParameters
metadata:
  name: multi_table
spec:
  schema: multi_table
  avatarization:
    parent:
      k: 5
    child:
      k: 2
  time_series:
    child_ts:
      projection:
        nf: 2
        projection_type: fpca
      alignment:
        method: mean
        nb_points: 3
  results:
    volume: local-temp-results
  seed: 123
""")
    assert yaml == expected


def test_privacy_metrics_parameters_to_yaml():
    pm = PrivacyMetricsParameters(ncp=5)

    yaml = get_privacy_metrics_parameters(
        metadata=Metadata(name="simple"),
        privacy_metrics={"iris": pm},
        schema_name="simple",
        results=Results(volume="local-temp-results"),
        seed=123,
    )

    expected = from_pretty_yaml("""
kind: AvatarPrivacyMetricsParameters
metadata:
  name: simple
spec:
  schema: simple
  privacy_metrics:
    iris:
      ncp: 5
  results:
    volume: local-temp-results
  seed: 123
""")
    assert yaml == expected


def test_signal_metrics_parameters_to_yaml():
    sm = SignalMetricsParameters(ncp=5)
    yaml = get_signal_metrics_parameters(
        metadata=Metadata(name="simple"),
        avatarization_ref="simple",
        signal_metrics={"iris": sm},
        schema_name="simple",
        results=Results(volume="local-temp-results"),
        seed=123,
    )

    expected = from_pretty_yaml("""
kind: AvatarSignalMetricsParameters
metadata:
  name: simple
spec:
  schema: simple
  avatarization_ref: simple
  signal_metrics:
    iris:
      ncp: 5
  results:
    volume: local-temp-results
  seed: 123
""")
    assert yaml == expected


def test_metrics_parameters_to_yaml():
    sm = PrivacyMetricsParameters(ncp=5)
    yaml_signal = get_signal_metrics_parameters(
        metadata=Metadata(name="simple"),
        avatarization_ref="simple",
        signal_metrics={"iris": sm},
        schema_name="simple",
        results=Results(volume="local-temp-results"),
        seed=123,
    )
    pm = PrivacyMetricsParameters(ncp=10)
    yaml_privacy = get_privacy_metrics_parameters(
        metadata=Metadata(name="simple"),
        avatarization_ref="simple",
        privacy_metrics={"iris": pm},
        schema_name="simple",
        results=Results(volume="local-temp-results"),
        seed=123,
    )
    yaml = aggregate_yamls(yaml_signal, yaml_privacy)

    expected = from_pretty_yaml("""
kind: AvatarSignalMetricsParameters
metadata:
  name: simple
spec:
  schema: simple
  avatarization_ref: simple
  signal_metrics:
    iris:
      ncp: 5
  results:
    volume: local-temp-results
  seed: 123

---
kind: AvatarPrivacyMetricsParameters
metadata:
  name: simple
spec:
  schema: simple
  avatarization_ref: simple
  privacy_metrics:
    iris:
      ncp: 10
  results:
    volume: local-temp-results
  seed: 123
""")
    assert yaml == expected


def test_avatarization_parameters_with_dp() -> None:
    avat1 = AvatarizationDPParameters(epsilon=5, use_categorical_reduction=True, ncp=2)

    yaml = get_avatarization_parameters(
        metadata=Metadata(name="simple"),
        schema_name="simple_iris",
        avatarization_dp={"iris": avat1},
        results=Results(volume="local-temp-results"),
        seed=1234,
    )

    expected = from_pretty_yaml("""
kind: AvatarParameters
metadata:
  name: simple
spec:
  schema: simple_iris
  avatarization_dp:
    iris:
      epsilon: 5
      ncp: 2
      use_categorical_reduction: true
  results:
    volume: local-temp-results
  seed: 1234
""")
    assert yaml == expected


def test_avatarization_parameters_fail_with_no_parameters() -> None:
    with pytest.raises(
        ValueError,
        match="Expected at least one of avatarization, avatarization_dp, or time_series",
    ):
        get_avatarization_parameters(
            metadata=Metadata(name="simple"),
            schema_name="simple_iris",
            results=Results(volume="local-temp-results"),
            seed=1234,
        )


def test_avatarization_parameters_with_max_distribution_plots() -> None:
    avat1 = AvatarizationParameters(k=5)

    yaml = get_avatarization_parameters(
        metadata=Metadata(name="simple"),
        avatarization={"iris": avat1},
        schema_name="simple_iris",
        results=Results(volume="local-temp-results", max_distribution_plots=50),
        seed=1234,
    )

    expected = from_pretty_yaml("""
kind: AvatarParameters
metadata:
  name: simple
spec:
  schema: simple_iris
  avatarization:
    iris:
      k: 5
  results:
    volume: local-temp-results
    max_distribution_plots: 50
  seed: 1234
""")
    assert yaml == expected


@pytest.mark.parametrize(
    "max_distribution_plots",
    [
        pytest.param(-1, id="no_limit"),
        pytest.param(0, id="zero"),
        pytest.param(100, id="custom"),
    ],
)
def test_results_max_distribution_plots_values(max_distribution_plots: int) -> None:
    results = Results(volume="test-volume", max_distribution_plots=max_distribution_plots)
    assert results.max_distribution_plots == max_distribution_plots
