from enum import Enum
from typing import NamedTuple, Tuple, List


class ScenarioTemplateType(Enum):
    SCRIPT_EXECUTION = "script_execution"
    COMMAND_EXECUTION = "command_execution"
    DOWNLOAD_TO_MEMORY = "download_to_memory"
    NATIVE_API = "native_api"


SCENARIO_TEMPLATE_IDS = {
    ScenarioTemplateType.SCRIPT_EXECUTION: "b7b0fa6d-5f3c-44b2-b393-3a83d3d32da3",
    ScenarioTemplateType.COMMAND_EXECUTION: "9edec174-908e-4fea-b63d-5303c08fc1d6",
    ScenarioTemplateType.DOWNLOAD_TO_MEMORY: "e4fc679e-45c1-4d15-a938-2030dfbcb836",
    ScenarioTemplateType.NATIVE_API: "2fc3fe6d-d0c1-48a2-91b1-a824d6a06c89",
}


class ScenarioLanguageConfig(NamedTuple):
    name: str
    interpreter: str
    file_ext: str
    allowed_templates: Tuple[ScenarioTemplateType, ...]


SCENARIO_LANGUAGES: List[ScenarioLanguageConfig] = [
    ScenarioLanguageConfig(
        name="Powershell",
        interpreter="powershell.exe",
        file_ext=".ps1",
        allowed_templates=(
            ScenarioTemplateType.SCRIPT_EXECUTION,
            ScenarioTemplateType.COMMAND_EXECUTION,
        ),
    ),
    ScenarioLanguageConfig(
        name="CMD",
        interpreter="cmd.exe",
        file_ext=".bat",
        allowed_templates=(ScenarioTemplateType.COMMAND_EXECUTION,),
    ),
    ScenarioLanguageConfig(
        name="Bash",
        interpreter="/bin/bash",
        file_ext=".sh",
        allowed_templates=(
            ScenarioTemplateType.SCRIPT_EXECUTION,
            ScenarioTemplateType.COMMAND_EXECUTION,
        ),
    ),
    ScenarioLanguageConfig(
        name="Batch",
        interpreter="cmd.exe",
        file_ext=".bat",
        allowed_templates=(ScenarioTemplateType.SCRIPT_EXECUTION,),
    ),
    ScenarioLanguageConfig(
        name="Python",
        interpreter="python.exe",
        file_ext=".py",
        allowed_templates=(ScenarioTemplateType.SCRIPT_EXECUTION,),
    ),
]


class AssetStatus(Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"


class UnifiedMitigationType(Enum):
    """Enum for Unified Mitigation Types used in AttackIQ Platform

    These type IDs correspond to the detection rule formats supported
    by the AttackIQ Detection Rule Manager.
    """

    SIGMA = 1
    YARA = 2
    SNORT = 3
    CATEGORY = 4
    ACTIONABLE = 5
    TECHNIQUE_MITIGATION_GUIDE = 6
    DETAILED_MITIGATION_GUIDE = 7
    SPL = 8  # Splunk Query Language
    KQL = 9  # Kusto Query Language (Microsoft Sentinel)
    ELASTIC_EQL = 10  # Elastic EQL/DSL
    CUSTOM = 11  # Custom format (for other SIEMs)
    XQL = 17  # XQL (Cortex XDR)
    CQL = 18  # CQL (CrowdStrike)


class IntegrationName(Enum):
    """Integration names used by AttackIQ Detection Rule Manager for filtering rules.

    These are the actual integration names found in the integration-monorepo
    and used by the API's integration_name parameter.
    """

    MICROSOFT_SENTINEL = "Microsoft Sentinel"
    GOOGLE_CHRONICLE = "Google Chronicle"
    SPLUNK_ES = "Splunk ES"
    SPLUNK = "Splunk"
    ELASTICSEARCH = "Elasticsearch"
    ELASTICSEARCH_STREAM = "Elasticsearch Stream"
    QRADAR = "QRadar"
    LOGRHYTHM = "LogRhythm"
    ARCSIGHT_LOGGER = "ArcSight Logger"
    DEVO = "Devo"
    RAPID7_INSIGHT_IDR = "Rapid7 InsightIDR"
    SUMO_LOGIC_CLOUD_SIEM = "Sumo Logic Cloud SIEM"
    HUNTERS = "Hunters"
    SINGULARITY_AI_SIEM = "Singularity AI SIEM"
    RSA_NETWITNESS = "RSA NetWitness"
    EXABEAM_FUSION = "Exabeam Fusion"
    SNYPR = "Snypr"
    CROWDSTRIKE_FALCON_NEXT_GEN_SIEM = "CrowdStrike Falcon Next-Gen SIEM"
    CROWDSTRIKE_LOGSCALE = "CrowdStrike LogScale"


# Mapping of detection type names to their corresponding IDs
DETECTION_TYPES = {
    "sigma": UnifiedMitigationType.SIGMA.value,  # 1
    "yara": UnifiedMitigationType.YARA.value,  # 2
    "snort": UnifiedMitigationType.SNORT.value,  # 3
    "spl": UnifiedMitigationType.SPL.value,  # 8 - Splunk (SPL)
    "splunk": UnifiedMitigationType.SPL.value,  # 8 - Splunk (SPL) alias
    "kql": UnifiedMitigationType.KQL.value,  # 9 - KQL (Microsoft Sentinel)
    "sentinel": UnifiedMitigationType.KQL.value,  # 9 - Microsoft Sentinel alias
    "elastic": UnifiedMitigationType.ELASTIC_EQL.value,  # 10 - Elastic EQL/DSL
    "eql": UnifiedMitigationType.ELASTIC_EQL.value,  # 10 - Elastic EQL alias
    "custom": UnifiedMitigationType.CUSTOM.value,  # 11 - Custom format
    "xql": UnifiedMitigationType.XQL.value,  # 17 - XQL (Cortex XDR)
    "cortex": UnifiedMitigationType.XQL.value,  # 17 - Cortex XDR alias
    "cql": UnifiedMitigationType.CQL.value,  # 18 - CQL (CrowdStrike)
    "crowdstrike": UnifiedMitigationType.CQL.value,  # 18 - CrowdStrike alias
}

# Mapping of integration type aliases to their full integration names
INTEGRATION_NAMES = {
    "sentinel": IntegrationName.MICROSOFT_SENTINEL.value,
    "microsoft_sentinel": IntegrationName.MICROSOFT_SENTINEL.value,
    "chronicle": IntegrationName.GOOGLE_CHRONICLE.value,
    "google_chronicle": IntegrationName.GOOGLE_CHRONICLE.value,
    "splunk_es": IntegrationName.SPLUNK_ES.value,
    "splunk": IntegrationName.SPLUNK.value,
    "elasticsearch": IntegrationName.ELASTICSEARCH.value,
    "elastic": IntegrationName.ELASTICSEARCH.value,
    "qradar": IntegrationName.QRADAR.value,
    "ibm_qradar": IntegrationName.QRADAR.value,
    "logrhythm": IntegrationName.LOGRHYTHM.value,
    "arcsight": IntegrationName.ARCSIGHT_LOGGER.value,
    "devo": IntegrationName.DEVO.value,
    "rapid7": IntegrationName.RAPID7_INSIGHT_IDR.value,
    "sumo_logic": IntegrationName.SUMO_LOGIC_CLOUD_SIEM.value,
    "hunters": IntegrationName.HUNTERS.value,
    "singularity": IntegrationName.SINGULARITY_AI_SIEM.value,
    "rsa_netwitness": IntegrationName.RSA_NETWITNESS.value,
    "exabeam": IntegrationName.EXABEAM_FUSION.value,
    "snypr": IntegrationName.SNYPR.value,
    "crowdstrike_siem": IntegrationName.CROWDSTRIKE_FALCON_NEXT_GEN_SIEM.value,
    "crowdstrike_logscale": IntegrationName.CROWDSTRIKE_LOGSCALE.value,
}


class AssessmentExecutionStrategy(Enum):
    """Execution strategy for assessments."""

    WITH_DETECTION = 0  # Run with detection validation
    WITHOUT_DETECTION = 1  # Run without detection validation


class DetectionStatus(Enum):
    """Detection status for unified mitigation rules."""

    PENDING = "pending"
    DETECTED = "detected"
    NOT_DETECTED = "not_detected"
    ERROR = "error"


class DetectionOutcome(Enum):
    """Detection outcome for unified mitigation rules."""

    TRUE_POSITIVE = "true_positive"
    FALSE_POSITIVE = "false_positive"
    TRUE_NEGATIVE = "true_negative"
    FALSE_NEGATIVE = "false_negative"


class AnalystVerdict(Enum):
    """Analyst verdict for detection results - human judgment of detection accuracy.

    This represents the SOC analyst's assessment of whether a detection was correct.
    """

    TRUE_POSITIVE = "true_positive"  # Real threat correctly detected
    FALSE_POSITIVE = "false_positive"  # Benign activity incorrectly flagged
    TRUE_NEGATIVE = "true_negative"  # Benign activity correctly ignored
    FALSE_NEGATIVE = "false_negative"  # Real threat missed
