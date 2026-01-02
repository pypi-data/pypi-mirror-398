"""AttackIQ Platform API SDK

Example:
    from aiq_platform_api import AttackIQClient, Scenarios, Assets

    async with AttackIQClient(url, token) as client:
        async for scenario in Scenarios.list_scenarios(client, limit=10):
            print(scenario["name"])
"""

__version__ = "1.0.26"

__all__ = [
    # Client
    "AttackIQClient",
    # Logger
    "AttackIQLogger",
    # Domain classes
    "Scenarios",
    "Assets",
    "Assessments",
    "Connectors",
    "TagSets",
    "Tags",
    "TaggedItems",
    "Results",
    "PhaseResults",
    "PhaseLogs",
    "FileUploads",
    "FileDownloads",
    "UnifiedMitigations",
    "UnifiedMitigationProjects",
    "UnifiedMitigationWithRelations",
    "UnifiedMitigationReporting",
    # Enums
    "AssetStatus",
    "UnifiedMitigationType",
    "IntegrationName",
    "AssessmentExecutionStrategy",
    "DetectionStatus",
    "DetectionOutcome",
    "AnalystVerdict",
    # Constants
    "DETECTION_TYPES",
    "INTEGRATION_NAMES",
    "ScenarioTemplateType",
    "SCENARIO_TEMPLATE_IDS",
    "ScenarioLanguageConfig",
    "SCENARIO_LANGUAGES",
    # Environment
    "ATTACKIQ_PLATFORM_URL",
    "ATTACKIQ_PLATFORM_API_TOKEN",
]

from .core import (
    AttackIQClient,
    AttackIQLogger,
    Scenarios,
    Assets,
    Assessments,
    Connectors,
    TagSets,
    Tags,
    TaggedItems,
    Results,
    PhaseResults,
    PhaseLogs,
    FileUploads,
    FileDownloads,
    UnifiedMitigations,
    UnifiedMitigationProjects,
    UnifiedMitigationWithRelations,
    UnifiedMitigationReporting,
    AssetStatus,
    UnifiedMitigationType,
    IntegrationName,
    AssessmentExecutionStrategy,
    DetectionStatus,
    DetectionOutcome,
    AnalystVerdict,
    DETECTION_TYPES,
    INTEGRATION_NAMES,
    ScenarioTemplateType,
    SCENARIO_TEMPLATE_IDS,
    ScenarioLanguageConfig,
    SCENARIO_LANGUAGES,
)

from .env import (
    ATTACKIQ_PLATFORM_URL,
    ATTACKIQ_PLATFORM_API_TOKEN,
)
