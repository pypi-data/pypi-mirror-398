from dataclasses import dataclass, field
from enum import Enum

from avatar_yaml.models.common import Metadata, ModelKind


# --- Enums for PIA metadata (align with avatar) ---
class SensitivityLevel(str, Enum):
    """Evaluation of the sensitivity level of the personal data being processed.

    This assessment is based on factors such as the nature of the data and potential
    risks to data subjects. It applies to three categories of data:

    - **Sensitive personal data** (GDPR Art. 9): Special categories including health,
      racial/ethnic origin, political opinions, religious beliefs, trade union
      membership, genetic data, biometric data, sex life, or sexual orientation.
      These typically require VERY_HIGH or HIGH sensitivity levels.
    - **Personal data** (GDPR Art. 4): Any information relating to an identified or
      identifiable natural person (e.g., name, identification number, location data,
      online identifiers). Sensitivity level varies based on context and combination with
      other data.
    - **Demographic data**: Non-sensitive characteristics such as age, gender,
      geographic location, education level. These are typically LOW to MEDIUM sensitivity,
      but can increase when combined with other identifying information.

    The sensitivity level should reflect potential harm to data subjects if the data were
    compromised or re-identified.
    """

    VERY_HIGH = "Very High"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    VERY_LOW = "Very Low"
    NEGLIGIBLE = "Negligible"
    UNDEFINED = "Undefined"


class DataRecipient(str, Enum):
    """Categories of recipients for the anonymised data, based on their relationship to the Data
    Controller and the context of data sharing."""

    UNKNOWN = "unknown"
    """The recipients of the anonymized data have not been specifically identified at this stage.
    The data recipient category will need to be determined to properly assess the privacy risks
    associated with data sharing and ensure appropriate safeguards are in place."""
    OPENDATA = "opendata"
    """The recipients of the anonymised data are the general public, through publication in an open
    data repository or public research platform. Such dissemination aims to promote scientific
    collaboration, innovation, or public transparency. To guarantee full compliance with data
    protection requirements, the datasets released as open data have undergone an anonymisation
    process. """
    CONTRACTUAL_THIRDPARTY = "contractual_thirdparty"
    """The recipients of the anonymised data are third parties with whom the Data Controller
    maintains a contractual relationship, such as research partners, insurers, data analytics
    firms, or other commercial entities. These transfers occur within a controlled legal framework
    ensuring compliance with the principles of confidentiality, data minimisation, and purpose
    limitation"""
    INTERNAL = "internal"
    """The recipients of the anonymised data are exclusively internal stakeholders of the Data
    Controller, such as authorised employees, researchers, or analysts operating within the same
    organisation. The synthetic datasets are used for internal analytical, research, or operational
    purposes, in strict compliance with the principles of data protection by design and by
    default"""
    OUTSIDE_EU = "outside_eu"
    """The recipients of the anonymised data are entities established outside the European Union,
    including international research institutions or commercial partners."""
    TRUSTED_THIRDPARTY = "trusted_thirdparty"
    """The recipients of the anonymised data are trusted third parties operating under a
    contractual or institutional framework that ensures compliance with data protection and ethical
    standards. These may include subcontractors providing technical services, scientific
    publishers, or data repositories managing peer-reviewed research outputs. The sharing of
    anonymised datasets with such entities is governed by confidentiality agreements and data
    processing clauses that explicitly prohibit any attempt at re-identification. """


class DataSubject(str, Enum):
    """Categories of individuals whose personal data are being processed, based on the context and
    purpose of the data processing activity."""

    UNKNOWN = "unknown"
    PATIENTS = "patients"
    """The data subjects are patients whose personal data are processed in the context of medical
    research, healthcare provision, or clinical trials. Such data may include information directly
    or indirectly identifying individuals, together with health-related or demographic
    variables."""
    EMPLOYEES = "employees"
    """The data subjects are employees, job applicants, or contractors whose personal data are
    processed for human resources management, organisational analysis, or workforce studies. Such
    data may encompass professional identifiers, career trajectories, remuneration details,
    performance indicators, and training records."""
    CLIENTS = "clients"
    """The data subjects are clients, customers, or insured persons whose personal data are
    processed for the purposes of service provision, product analysis, or contractual performance.
    These data may include identifying information, transaction or claim histories, contact
    details, and, in some contexts, financial or health-related information."""
    USERS = "users"
    """The data subjects are users of digital, public, or mobility services whose personal data are
    processed for analytical, operational, or optimisation purposes. The data may include
    identifiers, behavioural indicators, service usage patterns, or geolocation data."""
    STUDENTS = "students"
    """The data subjects are students enrolled in educational institutions whose personal data are
      processed for pedagogical, administrative, or research purposes. The datasets may include
      demographic information, academic performance, attendance records, or socio-economic
      indicators. """


class DataType(str, Enum):
    """Categories of personal data being processed, based on the context and sector of the data
    processing activity."""

    UNKNOWN = "unknown"
    """The processing involves personal data of an unspecified type. The exact nature of the data
    has not been determined or categorized at this stage. """
    HEALTH = "health"
    """The data processed originate from health-related datasets containing information on patients
    or study participants. These datasets typically include demographic, clinical, and behavioural
    variables, such as age, gender, diagnosis codes, treatment details, medical outcomes, and
    follow-up data."""
    HR = "hr"
    """The personal data processed concern employees, job applicants, contractors, or trainees. The
     datasets generally include professional information such as identification data, employment
     history, remuneration details, performance evaluations, and training records. Certain datasets
     may also include information relating to health or diversity monitoring."""
    MOBILITY = "mobility"
    """The personal data processed typically relate to users of transport systems, vehicle
    operators, or mobility service subscribers. These datasets may include identifiers, geolocation
    traces, timestamps, usage frequency, travel routes, and behavioural metrics. Depending on the
    context, they may also contain information derived from connected vehicles or smart ticketing
    systems."""
    INSURANCE = "insurance"
    """The personal data processed typically relate to policyholders, beneficiaries, or claimants.
    The datasets may include demographic characteristics, contract details, claim histories,
    financial indicators, and, in some cases, health-related information."""
    FINANCE = "finance"
    """The personal data processed concern clients, investors, account holders, or financial
    service users. Typical datasets may include identification data, transaction histories, account
    balances, income levels, credit ratings, and investment portfolios.In certain contexts, they
    may also contain data classified as sensitive, such as information revealing financial hardship
    or vulnerability."""
    EDUCATION = "education"
    """The personal data processed relate to students, teachers, or administrative staff within
    educational institutions. The datasets may include demographic information, academic
    performance records, attendance logs, course enrolments, and, where relevant, special
    educational needs or socio-economic indicators."""


@dataclass(frozen=True)
class PiaMetadata:
    datarecipient: str = DataRecipient.UNKNOWN.value
    data_type: str = DataType.UNKNOWN.value
    datasubject: str = DataSubject.UNKNOWN.value
    sensitivity_level: str = SensitivityLevel.UNDEFINED.value


@dataclass(frozen=True)
class AvatarMetadataSpec:
    display_name: str | None
    pia_metadata: PiaMetadata | None = None


@dataclass(frozen=True)
class AvatarMetadata:
    kind: ModelKind
    metadata: Metadata
    spec: AvatarMetadataSpec | None = None
    annotations: dict[str, str] = field(default_factory=dict)


def get_metadata(
    display_name: str | None = None,
    annotations: dict[str, str] = {},
    pia_metadata: PiaMetadata | None = None,
) -> AvatarMetadata:
    return AvatarMetadata(
        kind=ModelKind.METADATA,
        metadata=Metadata(name=f"avatar-metadata-{display_name}"),
        spec=AvatarMetadataSpec(display_name=display_name, pia_metadata=pia_metadata),
        annotations=annotations,
    )
