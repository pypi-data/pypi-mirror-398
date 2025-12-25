import re

import pytest

from avatar_yaml.models.advice import AdviceType
from avatar_yaml.models.avatar_metadata import (
    DataRecipient,
    DataSubject,
    DataType,
    SensitivityLevel,
)
from avatar_yaml.models.config import Config
from avatar_yaml.models.parameters import (
    AugmentationStrategy,
    ImputeMethod,
    OutputFormat,
    ReportType,
)
from avatar_yaml.models.schema import ColumnType
from tests.conftest import from_pretty_yaml


def test_config_standard():
    c = Config(seed=1, set_name="set_name")
    c.create_volume(volume_name="test_metadata", url="http://example.com")
    c.create_results_volume(result_volume_name="volume_results", url="http://example.com")
    c.create_metadata(
        pia_datarecipient=DataRecipient.INTERNAL,
    )
    c.create_table(
        table_name="example_data",
        original_volume="test_metadata",
        original_file="iris.csv",
        primary_key="id",
        foreign_keys=["id_1, id_2"],
    )
    c.create_avatarization_parameters(
        table_name="example_data",
        k=3,
    )
    c.create_privacy_metrics_parameters(table_name="example_data")
    c.create_signal_metrics_parameters(table_name="example_data")
    c.create_report()
    c.create_report(ReportType.PIA)

    yaml = c.get_yaml()
    expected_yaml = from_pretty_yaml("""
kind: AvatarMetadata
metadata:
  name: avatar-metadata-set_name
spec:
  display_name: set_name
  pia_metadata:
    datarecipient: internal
    data_type: unknown
    datasubject: unknown
    sensitivity_level: Undefined
annotations: {}

---
kind: AvatarVolume
metadata:
  name: test_metadata
spec:
  url: http://example.com

---
kind: AvatarVolume
metadata:
  name: volume_results
spec:
  url: http://example.com

---
kind: AvatarSchema
metadata:
  name: schema
spec:
  tables:
  - name: example_data
    data:
      volume: test_metadata
      file: iris.csv
    columns:
    - field: id
      primary_key: true
    - field: id_1, id_2
      identifier: true

---
kind: AvatarSchema
metadata:
  name: schema_avatarized
spec:
  tables:
  - name: example_data
    avatars_data:
      auto: true
  schema_ref: schema

---
kind: AvatarParameters
metadata:
  name: standard
spec:
  schema: schema
  avatarization:
    example_data:
      k: 3
  results:
    volume: volume_results
    path: standard
  seed: 1

---
kind: AvatarPrivacyMetricsParameters
metadata:
  name: privacy_metrics
spec:
  schema: schema_avatarized
  avatarization_ref: standard
  results:
    volume: volume_results
    path: privacy_metrics
  seed: 1

---
kind: AvatarSignalMetricsParameters
metadata:
  name: signal_metrics
spec:
  schema: schema_avatarized
  avatarization_ref: standard
  results:
    volume: volume_results
    path: signal_metrics
  seed: 1

---
kind: AvatarReportParameters
metadata:
  name: report
spec:
  report_type: basic
  output_format: pdf
  results:
    volume: volume_results
    path: report

---
kind: AvatarReportParameters
metadata:
  name: report_pia
spec:
  report_type: pia
  output_format: docx
  results:
    volume: volume_results
    path: report_pia
""")
    assert expected_yaml == yaml


def test_config_standard_without_volume():
    c = Config(seed=1, set_name="set_name")
    c.create_table(
        table_name="example_data",
        original_volume="input",
        original_file="iris.csv",
        primary_key="id",
        foreign_keys=["id_1, id_2"],
    )
    c.create_avatarization_parameters(
        table_name="example_data",
        k=3,
    )
    c.create_privacy_metrics_parameters(table_name="example_data")
    c.create_signal_metrics_parameters(table_name="example_data")
    c.create_report()

    yaml = c.get_yaml()
    expected_yaml = from_pretty_yaml("""
kind: AvatarMetadata
metadata:
  name: avatar-metadata-set_name
spec:
  display_name: set_name
annotations: {}

---
kind: AvatarSchema
metadata:
  name: schema
spec:
  tables:
  - name: example_data
    data:
      volume: input
      file: iris.csv
    columns:
    - field: id
      primary_key: true
    - field: id_1, id_2
      identifier: true

---
kind: AvatarSchema
metadata:
  name: schema_avatarized
spec:
  tables:
  - name: example_data
    avatars_data:
      auto: true
  schema_ref: schema

---
kind: AvatarParameters
metadata:
  name: standard
spec:
  schema: schema
  avatarization:
    example_data:
      k: 3
  results:
    volume: results
    path: standard
  seed: 1

---
kind: AvatarPrivacyMetricsParameters
metadata:
  name: privacy_metrics
spec:
  schema: schema_avatarized
  avatarization_ref: standard
  results:
    volume: results
    path: privacy_metrics
  seed: 1

---
kind: AvatarSignalMetricsParameters
metadata:
  name: signal_metrics
spec:
  schema: schema_avatarized
  avatarization_ref: standard
  results:
    volume: results
    path: signal_metrics
  seed: 1

---
kind: AvatarReportParameters
metadata:
  name: report
spec:
  report_type: basic
  output_format: pdf
  results:
    volume: results
    path: report
""")
    assert expected_yaml == yaml


def test_get_advice_yaml():
    c = Config(seed=1, set_name="set_name")
    c.create_volume(volume_name="test_metadata", url="http://example.com")
    c.create_results_volume(result_volume_name="volume_results", url="http://example.com")
    c.create_table(
        table_name="example_data",
        original_volume="test_metadata",
        original_file="iris.csv",
        primary_key="id",
        foreign_keys=["id_1, id_2"],
    )
    c.create_advice(advisor_type=[AdviceType.VARIABLES])
    yaml = c.get_yaml()
    expected_yaml = from_pretty_yaml("""
kind: AvatarMetadata
metadata:
  name: avatar-metadata-set_name
spec:
  display_name: set_name
annotations: {}

---
kind: AvatarVolume
metadata:
  name: test_metadata
spec:
  url: http://example.com

---
kind: AvatarVolume
metadata:
  name: volume_results
spec:
  url: http://example.com

---
kind: AvatarSchema
metadata:
  name: schema
spec:
  tables:
  - name: example_data
    data:
      volume: test_metadata
      file: iris.csv
    columns:
    - field: id
      primary_key: true
    - field: id_1, id_2
      identifier: true

---
kind: AvatarSchema
metadata:
  name: schema_avatarized
spec:
  tables:
  - name: example_data
    avatars_data:
      auto: true
  schema_ref: schema

---
kind: AvatarAdviceParameters
metadata:
  name: advice_variables
spec:
  schema: schema
  advice:
    advisor_type:
    - variables
  results:
    volume: volume_results
    path: advice
""")
    assert expected_yaml == yaml


def test_config_multitable():
    c = Config(seed=1, set_name="set_name")
    c.create_volume("{root:uri}/../", "fixtures")
    c.create_results_volume("file:///tmp/avatar", "local-temp-results")
    c.create_table(
        table_name="patient",
        original_volume="fixtures",
        original_file="multitable/table_patient.csv",
        avatar_volume="fixtures",
        avatar_file="multitable/table_patient_avatar.csv",
        primary_key="patient_id",
        types={"patient_id": "category", "age": "int"},
        individual_level=True,
    )

    c.create_table(
        table_name="doctor",
        original_volume="fixtures",
        original_file="multitable/table_doctor.csv",
        avatar_volume="fixtures",
        avatar_file="multitable/table_doctor_avatar.csv",
        primary_key="id",
        types={"id": "category", "job": "category"},
        individual_level=True,
    )

    c.create_table(
        table_name="visit",
        original_volume="fixtures",
        original_file="multitable/table_visit.csv",
        avatar_volume="fixtures",
        avatar_file="multitable/table_visit_avatar.csv",
        primary_key="visit_id",
        foreign_keys=["patient_id", "doctor_id"],
        types={
            "visit_id": "category",
            "doctor_id": "category",
            "patient_id": "category",
            "weight": "int",
        },
        individual_level=False,
    )

    c.create_link("doctor", "visit", "id", "doctor_id", "sensitive_original_order_assignment")
    c.create_link(
        "patient", "visit", "patient_id", "patient_id", "sensitive_original_order_assignment"
    )

    c.create_avatarization_parameters(
        table_name="patient",
        k=3,
    )
    c.create_signal_metrics_parameters(table_name="patient")
    c.create_avatarization_dp_parameters(
        table_name="doctor",
        epsilon=3,
        use_categorical_reduction=True,
    )
    c.create_signal_metrics_parameters(table_name="doctor", use_categorical_reduction=True)
    c.create_privacy_metrics_parameters(table_name="doctor", use_categorical_reduction=True)
    c.create_avatarization_parameters(
        table_name="visit",
        k=3,
    )
    c.create_signal_metrics_parameters(table_name="visit")
    c.create_privacy_metrics_parameters(table_name="visit")
    c.create_report()

    yaml = c.get_yaml()
    expected_yaml = from_pretty_yaml("""
kind: AvatarMetadata
metadata:
  name: avatar-metadata-set_name
spec:
  display_name: set_name
annotations: {}

---
kind: AvatarVolume
metadata:
  name: fixtures
spec:
  url: '{root:uri}/../'

---
kind: AvatarVolume
metadata:
  name: local-temp-results
spec:
  url: file:///tmp/avatar

---
kind: AvatarSchema
metadata:
  name: schema
spec:
  tables:
  - name: patient
    data:
      volume: fixtures
      file: multitable/table_patient.csv
    individual_level: true
    columns:
    - field: patient_id
      type: category
      primary_key: true
    - field: age
      type: int
    links:
    - field: patient_id
      to:
        table: visit
        field: patient_id
      method: sensitive_original_order_assignment
  - name: doctor
    data:
      volume: fixtures
      file: multitable/table_doctor.csv
    individual_level: true
    columns:
    - field: id
      type: category
      primary_key: true
    - field: job
      type: category
    links:
    - field: id
      to:
        table: visit
        field: doctor_id
      method: sensitive_original_order_assignment
  - name: visit
    data:
      volume: fixtures
      file: multitable/table_visit.csv
    individual_level: false
    columns:
    - field: visit_id
      type: category
      primary_key: true
    - field: patient_id
      type: category
      identifier: true
    - field: doctor_id
      type: category
      identifier: true
    - field: weight
      type: int

---
kind: AvatarSchema
metadata:
  name: schema_avatarized
spec:
  tables:
  - name: patient
    avatars_data:
      volume: fixtures
      file: multitable/table_patient_avatar.csv
  - name: doctor
    avatars_data:
      volume: fixtures
      file: multitable/table_doctor_avatar.csv
  - name: visit
    avatars_data:
      volume: fixtures
      file: multitable/table_visit_avatar.csv
  schema_ref: schema

---
kind: AvatarParameters
metadata:
  name: standard
spec:
  schema: schema
  avatarization:
    patient:
      k: 3
    visit:
      k: 3
  avatarization_dp:
    doctor:
      epsilon: 3
      use_categorical_reduction: true
  results:
    volume: local-temp-results
    path: standard
  seed: 1

---
kind: AvatarPrivacyMetricsParameters
metadata:
  name: privacy_metrics
spec:
  schema: schema_avatarized
  avatarization_ref: standard
  privacy_metrics:
    doctor:
      use_categorical_reduction: true
  results:
    volume: local-temp-results
    path: privacy_metrics
  seed: 1

---
kind: AvatarSignalMetricsParameters
metadata:
  name: signal_metrics
spec:
  schema: schema_avatarized
  avatarization_ref: standard
  signal_metrics:
    doctor:
      use_categorical_reduction: true
  results:
    volume: local-temp-results
    path: signal_metrics
  seed: 1

---
kind: AvatarReportParameters
metadata:
  name: report
spec:
  report_type: basic
  output_format: pdf
  results:
    volume: local-temp-results
    path: report
""")
    assert expected_yaml == yaml


def test_config_schema():
    c = Config(set_name="avat")
    c.create_table(
        "table1",
        original_volume="",
        original_file="iris.csv",
        primary_key="id",
        foreign_keys=["id_2"],
        time_series_time="time",
        types={"id": "category", "id_2": "category", "time": "datetime"},
        individual_level=True,
    )

    expected_yaml = from_pretty_yaml("""
kind: AvatarSchema
metadata:
  name: schema
spec:
  tables:
  - name: table1
    data:
      volume: ''
      file: iris.csv
    individual_level: true
    columns:
    - field: time
      type: datetime
      time_series_time: true
    - field: id
      type: category
      primary_key: true
    - field: id_2
      type: category
      identifier: true
""")
    assert expected_yaml == c.get_schema()


def test_config_get_advice():
    c = Config(set_name="avat")
    c.create_table(
        "table1",
        original_volume="",
        original_file="iris.csv",
    )
    c.create_table(
        "table2",
        original_volume="",
        original_file="iris.csv",
    )
    c.create_advice(advisor_type=[AdviceType.VARIABLES])
    result = c.get_advice()
    expected_yaml = from_pretty_yaml("""
kind: AvatarAdviceParameters
metadata:
  name: advice_variables
spec:
  schema: schema
  advice:
    advisor_type:
    - variables
  results:
    volume: results
    path: advice
""")
    assert expected_yaml == result


def test_config_parameters():
    c = Config(set_name="avat")
    c.create_results_volume("http://example.com", "volume_results")
    c.create_table(
        "table1",
        original_volume="",
        original_file="iris.csv",
    )
    c.create_avatarization_parameters(
        "table1",
        k=5,
        ncp=2,
        use_categorical_reduction=True,
        column_weights={"age": 0.5, "temp": 0.5},
        exclude_variable_names=["id"],
        exclude_variable_method="row_order",
        imputation_method="mean",
        imputation_k=3,
        imputation_training_fraction=0.5,
        imputation_return_data_imputed=True,
        data_augmentation_strategy=AugmentationStrategy.minority,
        data_augmentation_target_column="variety",
    )
    expected_yaml = from_pretty_yaml("""
kind: AvatarParameters
metadata:
  name: avatarization
spec:
  schema: schema
  avatarization:
    table1:
      k: 5
      ncp: 2
      use_categorical_reduction: true
      column_weights:
        age: 0.5
        temp: 0.5
      exclude_variables:
        variable_names:
        - id
        replacement_strategy: row_order
      imputation:
        method: mean
        k: 3
        training_fraction: 0.5
        return_data_imputed: true
      data_augmentation:
        augmentation_strategy: minority
        target_column: variety
  results:
    volume: volume_results
    path: standard
""")
    assert expected_yaml == c.get_avatarization(name="avatarization")


def test_delete_parameters():
    c = Config(set_name="avat")
    c.create_table(
        "table1",
        original_volume="",
        original_file="iris.csv",
    )
    c.create_avatarization_parameters(
        "table1",
        k=5,
        ncp=2,
        use_categorical_reduction=True,
        column_weights={"age": 0.5, "temp": 0.5},
        exclude_variable_names=["id"],
        exclude_variable_method="row_order",
        imputation_method="mean",
        imputation_k=3,
        imputation_training_fraction=0.5,
        data_augmentation_strategy=AugmentationStrategy.minority,
        data_augmentation_target_column="variety",
    )
    assert c.avatarization.keys() == {"table1"}
    c.delete_parameters("table1")
    assert c.avatarization == {}


def test_delete_specific_parameters():
    c = Config(set_name="avat")
    c.create_table(
        "table1",
        original_volume="",
        original_file="iris.csv",
    )
    c.create_avatarization_parameters(
        "table1",
        k=5,
        ncp=2,
        use_categorical_reduction=True,
        column_weights={"age": 0.5, "temp": 0.5},
        exclude_variable_names=["id"],
        exclude_variable_method="row_order",
        imputation_method="mean",
        imputation_k=3,
        imputation_training_fraction=0.5,
    )
    assert c.avatarization.keys() == {"table1"}
    c.delete_parameters("table1", ["column_weights"])
    assert c.avatarization["table1"].column_weights is None


def test_delete_table():
    c = Config(set_name="avat")
    c.create_table(
        "table1",
        original_volume="",
        original_file="iris.csv",
    )
    assert c.tables.keys() == {"table1"}
    c.delete_table("table1")
    assert c.tables == {}


def test_delete_table_link():
    config = Config(set_name="avat")
    config.create_table(
        "parent_table",
        original_volume="",
        original_file="parent.csv",
        primary_key="parent_id",
    )
    config.create_table(
        "child_table_1",
        original_volume="",
        original_file="child1.csv",
        primary_key="child_id",
        foreign_keys=["parent_id"],
    )
    config.create_table(
        "child_table_2",
        original_volume="",
        original_file="child2.csv",
        primary_key="child_id",
        foreign_keys=["parent_id"],
    )

    config.create_link(
        "parent_table", "child_table_1", "parent_id", "parent_id", "linear_sum_assignment"
    )
    config.create_link(
        "parent_table", "child_table_2", "parent_id", "parent_id", "linear_sum_assignment"
    )
    assert config.tables.keys() == {"parent_table", "child_table_1", "child_table_2"}
    assert len(config.tables["parent_table"].links) == 2
    config.delete_link("parent_table", "child_table_1")
    assert len(config.tables["parent_table"].links) == 1


class TestInvalidConfig:
    c = Config(set_name="avat")
    c.create_table(
        "table1",
        original_volume="",
        original_file="iris.csv",
        primary_key="id",
        foreign_keys=["id1", "id2"],
        time_series_time="t",
    )

    def test_create_avatarization_parameters_invalid_table(self):
        with pytest.raises(
            ValueError, match="Expected table `table2` to be created before setting parameters"
        ):
            self.c.create_avatarization_parameters("table2", k=3)

    def test_create_avatarization_parameters_invalid_imputation(self):
        with pytest.raises(
            ValueError,
            match=re.escape(
                "Expected one of ['knn', 'mode', 'median', 'mean', 'fast_knn'], got INVALID_METHOD"
            ),
        ):
            self.c.create_avatarization_parameters(
                "table1", k=3, imputation_method="INVALID_METHOD"
            )

    def test_create_avatarization_parameters_invalid_exclude(self):
        with pytest.raises(
            ValueError,
            match=re.escape(
                "Expected one of ['row_order', 'coordinate_similarity'], got INVALID_METHOD"
            ),
        ):
            self.c.create_avatarization_parameters(
                "table1",
                k=3,
                exclude_variable_names=["id"],
                exclude_variable_method="INVALID_METHOD",
            )

    @pytest.mark.parametrize(
        "method_name",
        [
            pytest.param("create_privacy_metrics_parameters", id="privacy_metrics"),
            pytest.param("create_signal_metrics_parameters", id="signal_metrics"),
        ],
    )
    def test_create_metrics_parameters_invalid_exclude(self, method_name):
        with pytest.raises(
            ValueError,
            match=re.escape(
                "Expected one of ['row_order', 'coordinate_similarity'], got INVALID_METHOD"
            ),
        ):
            method = getattr(self.c, method_name)
            method(
                "table1", exclude_variable_names=["id"], exclude_variable_method="INVALID_METHOD"
            )

    def test_create_table_invalid_primary_key_and_time_series_time(self):
        with pytest.raises(
            ValueError, match="Expected primary_key and time_series_time to be different fields"
        ):
            self.c.create_table(
                table_name="table2",
                original_volume="",
                original_file="table2.csv",
                primary_key="id",
                time_series_time="id",
            )

    def test_create_table_invalid_primary_key_and_foreign_keys(self):
        with pytest.raises(
            ValueError, match="Expected a primary_key and foreign_keys to be different fields"
        ):
            self.c.create_table(
                table_name="table2",
                original_volume="",
                original_file="table2.csv",
                primary_key="id",
                foreign_keys=["id"],
            )

    def test_create_table_invalid_time_series_time_and_foreign_keys(self):
        with pytest.raises(
            ValueError, match="Expected time_series time and foreign_keys to be different fields"
        ):
            self.c.create_table(
                table_name="table2",
                original_volume="",
                original_file="table2.csv",
                time_series_time="id",
                foreign_keys=["id"],
                types={"id": "category"},
            )

    def test_create_link_invalid_parent_field(self):
        self.c.create_table(
            "child",
            original_volume="",
            original_file="child.csv",
            foreign_keys=["parent_id"],
            primary_key="id",
        )
        with pytest.raises(
            ValueError,
            match="Expected field `invalid_field` to be the primary key of the table `table1`",
        ):
            self.c.create_link(
                "table1", "child", "invalid_field", "parent_id", "linear_sum_assignment"
            )

    def test_create_link_invalid_child_field(self):
        self.c.create_table(
            "child",
            original_volume="",
            original_file="child.csv",
            foreign_keys=["parent_id"],
            primary_key="id",
        )
        with pytest.raises(
            ValueError, match="Expected field `invalid_field` to be an identifier in table `child`"
        ):
            self.c.create_link("table1", "child", "id", "invalid_field", "method")

    def test_create_link_invalid_child(self):
        with pytest.raises(
            ValueError,
            match="Expected table `INVALID_CHILD` to be created before setting parameters",
        ):
            self.c.create_link("table1", "INVALID_CHILD", "id", "id", "method")


class TestConfig:
    def setup_method(self):
        """Setup method for each test - creates a basic Config with a test table."""
        self.config = Config(set_name="test_set")
        # Create a test table to use in the tests
        self.config.create_table(
            table_name="test_table",
            original_volume="test_volume",
            original_file="test_file.csv",
            primary_key="id",
            types={
                "id": ColumnType.INT,
                "val1": ColumnType.NUMERIC,
                "val2": ColumnType.CATEGORY,
            },
        )

    def test_create_privacy_metrics_parameters_basic(self):
        """Test creating basic privacy metrics parameters."""
        self.config.create_privacy_metrics_parameters(
            table_name="test_table", ncp=5, use_categorical_reduction=True
        )

        # Verify parameters were correctly set
        assert "test_table" in self.config.privacy_metrics
        assert self.config.privacy_metrics["test_table"].ncp == 5
        assert self.config.privacy_metrics["test_table"].use_categorical_reduction is True

        # These parameters should be None since they weren't provided
        assert self.config.privacy_metrics["test_table"].imputation is None
        assert self.config.privacy_metrics["test_table"].known_variables is None
        assert self.config.privacy_metrics["test_table"].target is None

    def test_create_privacy_metrics_parameters_all_options(self):
        """Test creating privacy metrics parameters with all options."""
        weights = {"val1": 0.6, "val2": 0.4}
        self.config.create_privacy_metrics_parameters(
            table_name="test_table",
            ncp=5,
            use_categorical_reduction=True,
            imputation_method=ImputeMethod.KNN,
            imputation_k=3,
            imputation_training_fraction=0.8,
            exclude_variable_method="row_order",
            exclude_variable_names=["id"],
            known_variables=["val1"],
            target="val2",
            quantile_threshold=80,
            column_weights=weights,
        )

        # Verify all parameters were correctly set
        assert "test_table" in self.config.privacy_metrics
        assert self.config.privacy_metrics["test_table"].ncp == 5
        assert self.config.privacy_metrics["test_table"].use_categorical_reduction is True
        assert self.config.privacy_metrics["test_table"].imputation["method"] == "knn"
        assert self.config.privacy_metrics["test_table"].imputation["k"] == 3
        assert self.config.privacy_metrics["test_table"].imputation["training_fraction"] == 0.8
        assert self.config.privacy_metrics["test_table"].exclude_variables["variable_names"] == [
            "id"
        ]
        assert (
            self.config.privacy_metrics["test_table"].exclude_variables["replacement_strategy"]
            == "row_order"
        )
        assert self.config.privacy_metrics["test_table"].known_variables == ["val1"]
        assert self.config.privacy_metrics["test_table"].target == "val2"
        assert self.config.privacy_metrics["test_table"].quantile_threshold == 80
        assert self.config.privacy_metrics["test_table"].column_weights == weights

    def test_create_privacy_metrics_parameters_no_parameters(self):
        """Test that calling with no parameters doesn't create a privacy metrics."""
        self.config.create_privacy_metrics_parameters(table_name="test_table")

        assert not self.config.privacy_metrics

    def test_create_privacy_metrics_parameters_invalid_imputation_method(self):
        """Test that an invalid imputation method raises a ValueError."""
        with pytest.raises(ValueError, match="Expected one of .*ImputeMethod parameter"):
            self.config.create_privacy_metrics_parameters(
                table_name="test_table", imputation_method="invalid_method"
            )

    def test_create_privacy_metrics_parameters_nonexistent_table(self):
        """Test that specifying a nonexistent table raises a ValueError."""
        with pytest.raises(ValueError, match="Expected table `nonexistent_table` to be created"):
            self.config.create_privacy_metrics_parameters(table_name="nonexistent_table", ncp=5)

    def test_create_privacy_metrics_parameters_when_update_existing_parameters(self):
        """Test create existing privacy metrics parameters."""
        # First create basic parameters
        self.config.create_privacy_metrics_parameters(table_name="test_table", ncp=5)

        # Then create another with different parameters
        self.config.create_privacy_metrics_parameters(
            table_name="test_table", use_categorical_reduction=True, known_variables=["val1"]
        )

        # Verify parameters were correctly updated (old values overwritten)
        assert "test_table" in self.config.privacy_metrics
        assert (
            self.config.privacy_metrics["test_table"].ncp is None
        )  # Should be overwritten to None
        assert self.config.privacy_metrics["test_table"].use_categorical_reduction is True
        assert self.config.privacy_metrics["test_table"].known_variables == ["val1"]

    def test_create_signal_metrics_parameters_all_options(self):
        """Test creating signal metrics parameters with all options."""
        weights = {"val1": 0.7, "val2": 0.3}
        self.config.create_signal_metrics_parameters(
            table_name="test_table",
            ncp=4,
            use_categorical_reduction=False,
            imputation_method=ImputeMethod.MEAN,
            imputation_k=2,
            imputation_training_fraction=0.6,
            exclude_variable_method="coordinate_similarity",
            exclude_variable_names=["val2"],
            column_weights=weights,
        )

        # Verify all parameters were correctly set
        assert "test_table" in self.config.signal_metrics
        assert self.config.signal_metrics["test_table"].ncp == 4
        assert self.config.signal_metrics["test_table"].use_categorical_reduction is False
        assert self.config.signal_metrics["test_table"].exclude_variables["variable_names"] == [
            "val2"
        ]
        assert (
            self.config.signal_metrics["test_table"].exclude_variables["replacement_strategy"]
            == "coordinate_similarity"
        )
        assert self.config.signal_metrics["test_table"].imputation["method"] == "mean"
        assert self.config.signal_metrics["test_table"].imputation["k"] == 2
        assert self.config.signal_metrics["test_table"].imputation["training_fraction"] == 0.6
        assert self.config.signal_metrics["test_table"].column_weights == weights


@pytest.mark.parametrize(
    "max_distribution_plots",
    [
        pytest.param(50, id="custom"),
        pytest.param(-1, id="no_limit"),
        pytest.param(0, id="zero"),
    ],
)
def test_config_max_distribution_plots_in_yaml(max_distribution_plots: int) -> None:
    """Test that max_distribution_plots appears in the generated YAML."""
    c = Config(seed=1, set_name="test")
    c.create_volume(volume_name="test_volume", url="http://example.com")
    c.create_table(
        table_name="test_table",
        original_volume="test_volume",
        original_file="test.csv",
    )
    c.create_avatarization_parameters(table_name="test_table", k=5)
    c.max_distribution_plots = max_distribution_plots

    yaml = c.get_yaml()

    assert f"max_distribution_plots: {max_distribution_plots}" in yaml


def test_config_max_distribution_plots_not_in_yaml_when_none() -> None:
    """Test that max_distribution_plots is not in YAML when not set."""
    c = Config(seed=1, set_name="test")
    c.create_volume(volume_name="test_volume", url="http://example.com")
    c.create_table(
        table_name="test_table",
        original_volume="test_volume",
        original_file="test.csv",
    )
    c.create_avatarization_parameters(table_name="test_table", k=5)

    yaml = c.get_yaml()

    assert "max_distribution_plots" not in yaml


# --- Tests for create_report ---


class TestCreateReport:
    """Test suite for the create_report method."""

    def setup_method(self):
        """Set up a basic config for each test."""
        self.config = Config(seed=1, set_name="test_set")
        self.config.create_volume(volume_name="test_volume", url="http://example.com")
        self.config.create_results_volume(
            result_volume_name="results_volume", url="http://results.com"
        )
        self.config.create_metadata(
            pia_datarecipient=DataRecipient.INTERNAL,
            pia_datatype=DataType.HEALTH,
            pia_datasubject=DataSubject.PATIENTS,
            pia_sensitivitylevel=SensitivityLevel.HIGH,
        )
        self.config.create_table(
            table_name="test_table",
            original_volume="test_volume",
            original_file="test.csv",
            primary_key="id",
        )
        self.config.create_avatarization_parameters(table_name="test_table", k=5)

    @pytest.mark.parametrize(
        "report_type,output_format,expected_format",
        [
            pytest.param(ReportType.BASIC, OutputFormat.PDF, "pdf", id="basic_pdf_default"),
            pytest.param(ReportType.BASIC, OutputFormat.DOCX, "docx", id="basic_docx"),
            pytest.param(
                ReportType.PIA,
                OutputFormat.PDF,
                "docx",
                id="pia_forces_docx",
            ),
        ],
    )
    def test_create_report_formats(self, report_type, output_format, expected_format):
        """Test create_report with different report types and output formats."""
        self.setup_method()
        self.config.create_report(report_type=report_type, output_format=output_format)

        yaml = self.config.get_yaml()

        assert "kind: AvatarReportParameters" in yaml
        assert f"report_type: {report_type.value}" in yaml
        assert f"output_format: {expected_format}" in yaml

    def test_create_report_pia_without_metadat(self):
        """Test that creating PIA report without PIA metadata create a report."""
        self.config.create_metadata()
        self.config.create_report()
        self.config.create_report(report_type=ReportType.PIA)
        assert ReportType.PIA in self.config.report.keys()

    def test_create_report_multiple_times_overwrites(self):
        """Test that calling create_report multiple times overwrites previous config."""
        self.config.create_report(report_type=ReportType.BASIC, output_format=OutputFormat.PDF)
        self.config.create_report(report_type=ReportType.BASIC, output_format=OutputFormat.DOCX)

        yaml = self.config.get_yaml()

        # Should only have docx (the second call)
        assert "output_format: docx" in yaml
        # PDF should not appear in report section
        assert yaml.count("output_format: pdf") == 0

    def test_no_report_when_create_report_not_called(self):
        """Test that no report section appears when create_report is not called."""
        yaml = self.config.get_yaml()

        assert "AvatarReportParameters" not in yaml
        assert "report_type:" not in yaml
