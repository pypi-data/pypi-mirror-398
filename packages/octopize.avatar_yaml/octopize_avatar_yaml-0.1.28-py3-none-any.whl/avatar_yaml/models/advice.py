from dataclasses import dataclass
from enum import StrEnum

from avatar_yaml.models.common import Metadata
from avatar_yaml.models.parameters import Results
from avatar_yaml.yaml_utils import to_yaml


class AdviceType(StrEnum):
    VARIABLES = "variables"
    PARAMETERS = "parameters"
    TABLES_LINKS = "tables_links"


@dataclass(frozen=True)
class AdviceParameters:
    advisor_type: list[AdviceType]


@dataclass(frozen=True)
class AdviceSpec:
    schema: str
    advice: AdviceParameters
    results: Results


@dataclass(frozen=True)
class Advice:
    kind: str
    metadata: Metadata
    spec: AdviceSpec


def get_advice(
    metadata_name: str,
    schema_name: str,
    advice_parameters: AdviceParameters,
    results: Results,
) -> str:
    advice = Advice(
        kind="AvatarAdviceParameters",
        metadata=Metadata(name=metadata_name),
        spec=AdviceSpec(
            schema=schema_name,
            advice=advice_parameters,
            results=results,
        ),
    )

    return to_yaml(advice)
