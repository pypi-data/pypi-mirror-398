# Example use cases for Unified Mitigation endpoints
import asyncio
import os
from enum import Enum
from typing import Optional, Dict, Any

from aiq_platform_api import (
    AttackIQClient,
    AttackIQLogger,
    UnifiedMitigations,
    UnifiedMitigationProjects,
    UnifiedMitigationWithRelations,
    UnifiedMitigationReporting,
    DetectionStatus,
    DetectionOutcome,
    ATTACKIQ_PLATFORM_URL,
    ATTACKIQ_PLATFORM_API_TOKEN,
)
from aiq_platform_api.core.testing import parse_test_choice, require_env

logger = AttackIQLogger.get_logger(__name__)


async def list_mitigation_rules(client: AttackIQClient, limit: Optional[int] = 10) -> int:
    """Lists unified mitigation rules."""
    logger.info(f"Listing up to {limit} unified mitigations...")
    count = 0
    async for rule in UnifiedMitigations.list_mitigations(client, limit=limit):
        count += 1
        logger.info(f"Mitigation Rule {count}: ID={rule.get('id')}, Name={rule.get('name')}")
    logger.info(f"Total mitigation rules listed: {count}")
    return count


async def create_and_delete_mitigation_rule(client: AttackIQClient, rule_data: Dict[str, Any]) -> None:
    """Creates a mitigation rule and then deletes it."""
    mitigation_id = None
    try:
        logger.info("Attempting to create a new mitigation rule...")
        created_rule = await UnifiedMitigations.create_mitigation(client, rule_data)
        if created_rule and created_rule.get("id"):
            mitigation_id = created_rule["id"]
            logger.info(f"Successfully created mitigation rule with ID: {mitigation_id}")

            retrieved_rule = await UnifiedMitigations.get_mitigation(client, mitigation_id)
            if retrieved_rule:
                logger.info(f"Retrieved rule: {retrieved_rule.get('name')}")
            else:
                logger.warning("Could not retrieve the newly created rule.")
        else:
            logger.error("Failed to create mitigation rule or ID not found in response.")
            return
    except Exception as e:
        logger.error(f"Error during mitigation rule creation/retrieval: {e}")
    finally:
        if mitigation_id:
            logger.info(f"Attempting to delete mitigation rule: {mitigation_id}")
            deleted = await UnifiedMitigations.delete_mitigation(client, mitigation_id)
            if deleted:
                logger.info(f"Successfully deleted mitigation rule: {mitigation_id}")
            else:
                logger.error(f"Failed to delete mitigation rule: {mitigation_id}")


async def create_sigma_detection_rule(client: AttackIQClient) -> Optional[str]:
    """Creates a Sigma detection rule for PowerShell encoded command detection."""
    sigma_rule_content = """
title: Suspicious PowerShell Encoded Command
status: experimental
description: Detects suspicious PowerShell execution with encoded commands
logsource:
    product: windows
    service: process_creation
detection:
    selection:
        CommandLine|contains:
            - '-EncodedCommand'
            - '-enc'
        Image|endswith: '\\powershell.exe'
    condition: selection
falsepositives:
    - Administrative scripts
level: medium
"""

    rule_data = {
        "name": "Sigma - Suspicious PowerShell Encoded Command",
        "description": "Detects PowerShell execution with encoded commands that may indicate malicious activity",
        "unifiedmitigationtype": 1,
        "content": sigma_rule_content,
    }

    try:
        logger.info("Creating Sigma detection rule...")
        created_rule = await UnifiedMitigations.create_mitigation(client, rule_data)
        if created_rule and created_rule.get("id"):
            rule_id = created_rule["id"]
            logger.info(f"Successfully created Sigma rule with ID: {rule_id}")
            return rule_id
        else:
            logger.error("Failed to create Sigma rule")
            return None
    except Exception as e:
        logger.error(f"Error creating Sigma rule: {e}")
        return None


async def create_yara_detection_rule(client: AttackIQClient) -> Optional[str]:
    """Creates a YARA detection rule for malware detection."""
    yara_rule_content = """
rule Detect_Mimikatz_Patterns {
    meta:
        description = "Detects common Mimikatz patterns and strings"
        author = "Security Team"
        date = "2025-01-20"
    strings:
        $a = "sekurlsa::logonpasswords" nocase
        $b = "privilege::debug" nocase
        $c = "mimikatz" nocase
        $d = "gentilkiwi" nocase
        $e = "lsadump::sam" nocase
    condition:
        2 of them
}
"""

    rule_data = {
        "name": "YARA - Detect Mimikatz Patterns",
        "description": "YARA rule to detect common Mimikatz tool patterns",
        "unifiedmitigationtype": 2,
        "content": yara_rule_content,
    }

    try:
        logger.info("Creating YARA detection rule...")
        created_rule = await UnifiedMitigations.create_mitigation(client, rule_data)
        if created_rule and created_rule.get("id"):
            rule_id = created_rule["id"]
            logger.info(f"Successfully created YARA rule with ID: {rule_id}")
            return rule_id
        else:
            logger.error("Failed to create YARA rule")
            return None
    except Exception as e:
        logger.error(f"Error creating YARA rule: {e}")
        return None


async def delete_detection_rule(client: AttackIQClient, rule_id: str) -> bool:
    """Deletes a detection rule by ID."""
    try:
        logger.info(f"Deleting detection rule: {rule_id}")
        deleted = await UnifiedMitigations.delete_mitigation(client, rule_id)
        if deleted:
            logger.info(f"Successfully deleted rule: {rule_id}")
            return True
        else:
            logger.error(f"Failed to delete rule: {rule_id}")
            return False
    except Exception as e:
        logger.error(f"Error deleting rule: {str(e)}")
        return False


async def list_project_associations(client: AttackIQClient, limit: Optional[int] = 10) -> int:
    """Lists unified mitigation project associations."""
    logger.info(f"Listing up to {limit} unified mitigation project associations...")
    count = 0
    async for assoc in UnifiedMitigationProjects.list_associations(client, limit=limit):
        count += 1
        logger.info(
            f"Association {count}: ID={assoc.get('id')}, RuleID={assoc.get('unified_mitigation')}, ProjectID={assoc.get('project')}"
        )
    logger.info(f"Total associations listed: {count}")
    return count


async def list_mitigations_with_relations(client: AttackIQClient, limit: Optional[int] = 10) -> int:
    """Lists unified mitigations including related project and detection data."""
    logger.info(f"Listing up to {limit} unified mitigations with relations...")
    count = 0
    async for rule in UnifiedMitigationWithRelations.list_mitigations_with_relations(client, limit=limit):
        count += 1
        logger.info(f"Mitigation+Relations {count}: ID={rule.get('id')}, Name={rule.get('name')}")
        if rule.get("project"):
            logger.info(f"  Associated Project: {rule.get('project').get('name')}")
    logger.info(f"Total mitigations with relations listed: {count}")
    return count


async def get_detection_timeline(client: AttackIQClient, params: Optional[Dict[str, Any]] = None):
    """Gets the detection performance timeline data."""
    logger.info(f"Getting detection performance timeline with params: {params}")
    timeline_data = await UnifiedMitigationReporting.get_detection_performance_timeline(client, params)
    if timeline_data:
        logger.info("Successfully retrieved detection timeline data.")
    else:
        logger.warning("No detection timeline data returned.")


async def get_detection_results(client: AttackIQClient, mitigation_id: str, limit: Optional[int] = 10) -> int:
    """Get detection results for a mitigation rule."""
    logger.info(f"Getting detection results for rule {mitigation_id}")
    count = 0
    async for result in UnifiedMitigations.get_detection_results(client, mitigation_id, limit=limit):
        count += 1
        logger.info(f"Result {count}:")
        logger.info(f"  ID: {result.get('id', 'N/A')}")
        logger.info(f"  Status: {result.get('detection_status', 'N/A')}")
        logger.info(f"  Outcome: {result.get('detection_outcome', 'N/A')}")
        logger.info(f"  Run ID: {result.get('project_run_id', 'N/A')}")
        logger.info(f"  Modified: {result.get('modified', 'N/A')}")
        logger.info("---")

    if count == 0:
        logger.info("No detection results found. Assessment may not have been run yet.")
    else:
        logger.info(f"Total results: {count}")
    return count


async def set_detection_detected(client: AttackIQClient, mitigation_id: str) -> Optional[Dict[str, Any]]:
    """Mark a rule as detected (true positive)."""
    logger.info(f"Setting rule {mitigation_id} as DETECTED (TRUE_POSITIVE)")
    result = await UnifiedMitigations.set_detection_status(
        client,
        mitigation_id,
        DetectionStatus.DETECTED.value,
        detection_outcome=DetectionOutcome.TRUE_POSITIVE.value,
        metadata={"updated_by": "manual_test", "reason": "Rule successfully detected the attack"},
    )

    if result:
        logger.info(f"Successfully updated detection status: {result.get('detection_status')}")
        logger.info(f"Outcome: {result.get('detection_outcome')}")
        return result
    else:
        logger.warning("No assessment runs found for this rule")
        return None


async def set_detection_not_detected(client: AttackIQClient, mitigation_id: str) -> Optional[Dict[str, Any]]:
    """Mark a rule as not detected (false negative)."""
    logger.info(f"Setting rule {mitigation_id} as NOT_DETECTED (FALSE_NEGATIVE)")
    result = await UnifiedMitigations.set_detection_status(
        client,
        mitigation_id,
        DetectionStatus.NOT_DETECTED.value,
        detection_outcome=DetectionOutcome.FALSE_NEGATIVE.value,
        metadata={"updated_by": "manual_test", "reason": "Rule failed to detect the attack"},
    )

    if result:
        logger.info(f"Successfully updated detection status: {result.get('detection_status')}")
        logger.info(f"Outcome: {result.get('detection_outcome')}")
        return result
    else:
        logger.warning("No assessment runs found for this rule")
        return None


async def get_latest_detection_status(client: AttackIQClient, mitigation_id: str) -> Optional[Dict[str, Any]]:
    """Get the latest detection status for a rule."""
    logger.info(f"Getting latest detection status for rule {mitigation_id}")
    latest = await UnifiedMitigations.get_latest_detection_result(client, mitigation_id)

    if latest:
        logger.info("Latest Detection Status:")
        logger.info(f"  Status: {latest.get('detection_status', 'N/A')}")
        logger.info(f"  Outcome: {latest.get('detection_outcome', 'N/A')}")
        logger.info(f"  Run ID: {latest.get('project_run_id', 'N/A')}")
        logger.info(f"  Modified: {latest.get('modified', 'N/A')}")
        if latest.get("metadata"):
            logger.info(f"  Metadata: {latest.get('metadata')}")
    else:
        logger.info("No detection results found. Assessment has not been run yet.")

    return latest


async def test_list_rules(client: AttackIQClient):
    """Test listing mitigation rules."""
    await list_mitigation_rules(client, limit=5)


async def test_get_rules_by_integration_name(client: AttackIQClient):
    """Test getting rules filtered by integration name."""
    integration_names = ["sentinel", "chronicle", "splunk_es", "splunk", "elastic", "qradar"]

    for integration_name in integration_names:
        logger.info(f"\n--- Testing rules for integration name: {integration_name} ---")
        count = 0
        async for rule in UnifiedMitigations.get_rules_by_integration_name(client, integration_name, limit=3):
            count += 1
            integration_info = rule.get("integration", {})
            actual_integration_name = integration_info.get("name", "N/A") if integration_info else "N/A"
            logger.info(f"Rule {count}: ID={rule.get('id')}, Name={rule.get('name')}")
            logger.info(f"  Integration: {actual_integration_name}")
            logger.info(f"  Type: {rule.get('unifiedmitigationtype')}")

        if count == 0:
            logger.info(f"No rules found for integration name: {integration_name}")
        else:
            logger.info(f"Total {integration_name} rules found: {count}")


async def test_create_sigma(client: AttackIQClient):
    """Test creating and deleting a Sigma rule."""
    sigma_rule_id = await create_sigma_detection_rule(client)
    if sigma_rule_id:
        logger.info(f"Created Sigma rule: {sigma_rule_id}")
        await delete_detection_rule(client, sigma_rule_id)


async def test_create_yara(client: AttackIQClient):
    """Test creating and deleting a YARA rule."""
    yara_rule_id = await create_yara_detection_rule(client)
    if yara_rule_id:
        logger.info(f"Created YARA rule: {yara_rule_id}")
        await delete_detection_rule(client, yara_rule_id)


async def test_create_minimal(client: AttackIQClient):
    """Test creating and deleting a minimal rule."""
    minimal_rule_data = {
        "name": "Minimal Test Rule - Delete Me",
        "description": "Test rule with minimal required fields",
        "unifiedmitigationtype": 9,
        "content": "Basic rule content",
    }
    await create_and_delete_mitigation_rule(client, minimal_rule_data)


async def test_list_associations(client: AttackIQClient):
    """Test listing project associations."""
    await list_project_associations(client, limit=5)


async def test_integration_options(client: AttackIQClient):
    """Test fetching integration options for unified mitigations."""
    logger.info("--- Testing Unified Mitigation Integration Options ---")
    options = await UnifiedMitigationWithRelations.get_integration_options(client)
    if not options:
        logger.warning("No integration options returned.")
        return
    types = options.get("integration_types") or []
    names = options.get("integration_names") or []
    logger.info(f"Integration types ({len(types)}): {types}")
    logger.info(f"Integration names ({len(names)}): {names}")


async def test_list_with_relations(client: AttackIQClient):
    """Test listing mitigations with relations."""
    await list_mitigations_with_relations(client, limit=5)


async def test_get_timeline(client: AttackIQClient):
    """Test getting detection performance timeline."""
    timeline_params = {"time_interval": "monthly"}
    await get_detection_timeline(client, timeline_params)


async def test_get_detection_results(client: AttackIQClient, mitigation_id: str):
    """Test getting detection results for a rule."""
    if not mitigation_id:
        logger.error("MITIGATION_ID or RULE_ID environment variable required for this test")
        return
    await get_detection_results(client, mitigation_id, limit=5)


async def test_set_detected(client: AttackIQClient, mitigation_id: str):
    """Test setting rule as detected."""
    if not mitigation_id:
        logger.error("MITIGATION_ID or RULE_ID environment variable required for this test")
        return
    await set_detection_detected(client, mitigation_id)


async def test_set_not_detected(client: AttackIQClient, mitigation_id: str):
    """Test setting rule as not detected."""
    if not mitigation_id:
        logger.error("MITIGATION_ID or RULE_ID environment variable required for this test")
        return
    await set_detection_not_detected(client, mitigation_id)


async def test_get_latest_status(client: AttackIQClient, mitigation_id: str):
    """Test getting latest detection status."""
    if not mitigation_id:
        logger.error("MITIGATION_ID or RULE_ID environment variable required for this test")
        return
    await get_latest_detection_status(client, mitigation_id)


async def test_get_associated_assessment(client: AttackIQClient, mitigation_id: str):
    """Test getting associated assessment for a rule."""
    if not mitigation_id:
        logger.error("MITIGATION_ID or RULE_ID environment variable required for this test")
        return

    logger.info(f"Getting associated assessment for rule {mitigation_id}")
    assessment = await UnifiedMitigations.get_associated_assessment(client, mitigation_id)

    if assessment:
        logger.info(f"Found assessment: {assessment['name']} [ID: {assessment['id']}]")
        logger.info(f"  Version: {assessment.get('version', 'N/A')}")
        logger.info(f"  Created: {assessment.get('created', 'N/A')}")
    else:
        logger.info("No assessment associated with this rule")


async def test_get_latest_assessment_run_status(client: AttackIQClient, mitigation_id: str):
    """Test getting latest assessment run status for a rule."""
    if not mitigation_id:
        logger.error("MITIGATION_ID or RULE_ID environment variable required for this test")
        return

    logger.info(f"Getting latest assessment run status for rule {mitigation_id}")
    run_status = await UnifiedMitigations.get_latest_assessment_run_status(client, mitigation_id)

    if run_status:
        logger.info(f"Found run: {run_status['id']}")
        logger.info(f"  Completed: {'Yes' if run_status['completed'] else 'In Progress'}")
        logger.info(f"  Progress: {run_status['done_count']}/{run_status['total_count']}")
        logger.info(f"  Created: {run_status.get('created', 'N/A')}")
    else:
        logger.info("No assessment runs found for this rule")


async def test_analyst_verdicts(client: AttackIQClient, mitigation_id: str):
    """Test analyst verdict functions."""
    if not mitigation_id:
        logger.error("MITIGATION_ID or RULE_ID environment variable required for this test")
        return

    logger.info(f"Testing analyst verdict functions for rule {mitigation_id}")

    current = await UnifiedMitigations.get_analyst_verdict(client, mitigation_id)
    logger.info(f"Current verdict: {current or 'None'}")

    if await UnifiedMitigations.mark_true_positive(client, mitigation_id):
        logger.info("Successfully marked as TRUE_POSITIVE")
        verdict = await UnifiedMitigations.get_analyst_verdict(client, mitigation_id)
        logger.info(f"  New verdict: {verdict}")

    if await UnifiedMitigations.mark_false_positive(client, mitigation_id):
        logger.info("Successfully marked as FALSE_POSITIVE")
        verdict = await UnifiedMitigations.get_analyst_verdict(client, mitigation_id)
        logger.info(f"  New verdict: {verdict}")


async def test_all(client: AttackIQClient, mitigation_id: Optional[str] = None):
    """Run all tests."""
    logger.info("--- Listing Existing Unified Mitigation Rules ---")
    await list_mitigation_rules(client, limit=5)

    logger.info("\n--- Creating Detection Rules Examples ---")

    sigma_rule_id = await create_sigma_detection_rule(client)
    if sigma_rule_id:
        await delete_detection_rule(client, sigma_rule_id)

    yara_rule_id = await create_yara_detection_rule(client)
    if yara_rule_id:
        await delete_detection_rule(client, yara_rule_id)

    logger.info("\n--- Creating Rule with Minimal Required Fields ---")
    minimal_rule_data = {
        "name": "Minimal Test Rule - Delete Me",
        "description": "Test rule with minimal required fields",
        "unifiedmitigationtype": 9,
        "content": "Basic rule content",
    }
    await create_and_delete_mitigation_rule(client, minimal_rule_data)

    logger.info("\n--- Testing Project Associations ---")
    await list_project_associations(client, limit=5)

    logger.info("\n--- Testing Mitigations With Relations ---")
    await list_mitigations_with_relations(client, limit=5)

    logger.info("\n--- Testing Detection Performance Timeline ---")
    timeline_params = {"time_interval": "monthly"}
    await get_detection_timeline(client, timeline_params)


async def run_test(choice: "TestChoice", client: AttackIQClient, mitigation_id: Optional[str] = None):
    """Run the selected test."""
    test_functions = {
        TestChoice.LIST_RULES: lambda: test_list_rules(client),
        TestChoice.GET_RULES_BY_INTEGRATION_NAME: lambda: test_get_rules_by_integration_name(client),
        TestChoice.CREATE_SIGMA: lambda: test_create_sigma(client),
        TestChoice.CREATE_YARA: lambda: test_create_yara(client),
        TestChoice.CREATE_MINIMAL: lambda: test_create_minimal(client),
        TestChoice.LIST_ASSOCIATIONS: lambda: test_list_associations(client),
        TestChoice.GET_INTEGRATION_OPTIONS: lambda: test_integration_options(client),
        TestChoice.LIST_WITH_RELATIONS: lambda: test_list_with_relations(client),
        TestChoice.GET_TIMELINE: lambda: test_get_timeline(client),
        TestChoice.GET_DETECTION_RESULTS: lambda: test_get_detection_results(client, mitigation_id),
        TestChoice.SET_DETECTED: lambda: test_set_detected(client, mitigation_id),
        TestChoice.SET_NOT_DETECTED: lambda: test_set_not_detected(client, mitigation_id),
        TestChoice.GET_LATEST_STATUS: lambda: test_get_latest_status(client, mitigation_id),
        TestChoice.GET_ASSOCIATED_ASSESSMENT: lambda: test_get_associated_assessment(client, mitigation_id),
        TestChoice.GET_LATEST_ASSESSMENT_RUN_STATUS: lambda: test_get_latest_assessment_run_status(
            client, mitigation_id
        ),
        TestChoice.ANALYST_VERDICTS: lambda: test_analyst_verdicts(client, mitigation_id),
        TestChoice.ALL: lambda: test_all(client, mitigation_id),
    }
    await test_functions[choice]()


class TestChoice(Enum):
    LIST_RULES = "list_rules"
    GET_RULES_BY_INTEGRATION_NAME = "get_rules_by_integration_name"
    CREATE_SIGMA = "create_sigma"
    CREATE_YARA = "create_yara"
    CREATE_MINIMAL = "create_minimal"
    LIST_ASSOCIATIONS = "list_associations"
    GET_INTEGRATION_OPTIONS = "get_integration_options"
    LIST_WITH_RELATIONS = "list_with_relations"
    GET_TIMELINE = "get_timeline"
    GET_DETECTION_RESULTS = "get_detection_results"
    SET_DETECTED = "set_detected"
    SET_NOT_DETECTED = "set_not_detected"
    GET_LATEST_STATUS = "get_latest_status"
    GET_ASSOCIATED_ASSESSMENT = "get_associated_assessment"
    GET_LATEST_ASSESSMENT_RUN_STATUS = "get_latest_assessment_run_status"
    ANALYST_VERDICTS = "analyst_verdicts"
    ALL = "all"


async def main():
    require_env(ATTACKIQ_PLATFORM_URL, ATTACKIQ_PLATFORM_API_TOKEN)
    choice = parse_test_choice(TestChoice)

    async with AttackIQClient(ATTACKIQ_PLATFORM_URL, ATTACKIQ_PLATFORM_API_TOKEN) as client:
        mitigation_id = os.environ.get("MITIGATION_ID") or os.environ.get("RULE_ID")
        await run_test(choice, client, mitigation_id)


if __name__ == "__main__":
    asyncio.run(main())
