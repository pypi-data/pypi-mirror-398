# Example use cases for Scenario endpoints
import asyncio
import os
import time
from enum import Enum
from typing import Optional, Dict, Any

from aiq_platform_api import (
    AttackIQClient,
    AttackIQLogger,
    Scenarios,
    FileUploads,
    ATTACKIQ_PLATFORM_URL,
    ATTACKIQ_PLATFORM_API_TOKEN,
)
from aiq_platform_api.core.testing import parse_test_choice, require_env

logger = AttackIQLogger.get_logger(__name__)

SCRIPT_EXECUTION_TEMPLATE_ID = "b7b0fa6d-5f3c-44b2-b393-3a83d3d32da3"
COMMAND_EXECUTION_TEMPLATE_ID = "9edec174-908e-4fea-b63d-5303c08fc1d6"

LANGUAGE_CONFIG = {
    "bash": {
        "interpreter": "/bin/bash",
        "ext": ".sh",
        "sample_body": "#!/bin/bash\necho 'Hello from bash scenario'",
        "allowed_templates": {"script_execution", "command_execution"},
    },
    "powershell": {
        "interpreter": "powershell.exe",
        "ext": ".ps1",
        "sample_body": "Write-Host 'Hello from PowerShell scenario'",
        "allowed_templates": {"script_execution", "command_execution"},
    },
    "python": {
        "interpreter": "python.exe",
        "ext": ".py",
        "sample_body": "print('Hello from Python scenario')",
        "allowed_templates": {"script_execution"},
    },
    "batch": {
        "interpreter": "cmd.exe",
        "ext": ".bat",
        "sample_body": "@echo off\necho Hello from Batch scenario",
        "allowed_templates": {"script_execution"},
    },
    "cmd": {
        "interpreter": "cmd.exe",
        "ext": ".bat",
        "sample_body": "@echo off\necho Hello from CMD scenario",
        "allowed_templates": {"command_execution"},
    },
}


def _build_description_payload(summary: Optional[str]) -> Optional[Dict[str, Any]]:
    if not summary:
        return None
    return {
        "description_json": {
            "summary": summary,
            "prerequisites": "",
            "failure_criteria": "",
            "prevention_criteria": "",
            "additional_information": "",
        }
    }


async def list_scenarios(
    client: AttackIQClient, limit: Optional[int] = 10, filter_params: Optional[Dict[str, Any]] = None
) -> int:
    filter_params = filter_params or {}
    logger.info(f"Listing up to {limit} scenarios with params: {filter_params}")
    count = 0
    async for scenario in Scenarios.list_scenarios(client, params=filter_params, limit=limit):
        count += 1
        logger.info(f"Scenario {count}: ID={scenario['id']}, Name={scenario['name']}")
    logger.info(f"Total scenarios listed: {count}")
    return count


async def save_scenario_copy(
    client: AttackIQClient,
    scenario_id: str,
    new_name: str,
    model_json: Optional[Dict[str, Any]] = None,
    fork_template: bool = True,
) -> Dict[str, Any]:
    logger.info(f"Creating a copy of scenario {scenario_id} with name '{new_name}'")
    copy_data = {"name": new_name, "fork_template": fork_template}
    if model_json:
        copy_data["model_json"] = model_json
    new_scenario = await Scenarios.save_copy(client, scenario_id, copy_data)
    if not new_scenario:
        raise ValueError("Failed to create scenario copy")
    logger.info(f"Successfully created scenario copy with ID: {new_scenario['id']}")
    return new_scenario


async def delete_scenario_use_case(client: AttackIQClient, scenario_id: str):
    logger.info(f"--- Attempting to delete scenario: {scenario_id} ---")
    success = await Scenarios.delete_scenario(client, scenario_id)
    if success:
        logger.info(f"Successfully initiated deletion of scenario: {scenario_id}")
    else:
        logger.error(f"Failed to initiate deletion of scenario: {scenario_id}")


async def test_list_scenarios(client: AttackIQClient, search_term: Optional[str] = None):
    logger.info("--- Testing Scenario Listing ---")
    filter_params = {"search": search_term} if search_term else {}
    await list_scenarios(client, limit=5, filter_params=filter_params)


async def test_list_mimikatz_scenarios(client: AttackIQClient):
    logger.info("--- Testing Scenario Listing with Mimikatz filter ---")
    await test_list_scenarios(client, "Mimikatz")


async def test_list_scenarios_by_tag(client: AttackIQClient, tag_id: Optional[str] = None, limit: int = 10):
    logger.info("--- Testing Scenario Listing by Tag ID ---")
    tag_id = tag_id or os.environ.get("ATTACKIQ_TAG_ID")
    if not tag_id:
        logger.error("Tag ID is required. Set ATTACKIQ_TAG_ID or pass tag_id directly.")
        return

    result = await Scenarios.list_scenarios_by_tag(client, tag_id=tag_id, limit=limit)
    scenarios = result.get("results", [])
    logger.info(f"Tag {tag_id}: {result.get('count', len(scenarios))} total, showing {len(scenarios)}")
    for idx, scenario in enumerate(scenarios, 1):
        logger.info(f"{idx}. {scenario.get('name')} (ID: {scenario.get('id')})")
    if result.get("detail"):
        logger.info(f"Detail: {result['detail']}")


async def test_copy_scenario(client: AttackIQClient, scenario_id: Optional[str] = None):
    logger.info("--- Testing Scenario Copy ---")

    if not scenario_id:
        scenario_id = os.environ.get("ATTACKIQ_SCENARIO_ID", "5417db5e-569f-4660-86ae-9ea7b73452c5")

    scenario = await Scenarios.get_scenario(client, scenario_id)
    old_name = scenario["name"]
    old_model_json = scenario["model_json"]
    if old_model_json:
        old_model_json["domain"] = "example.com"

    timestamp = int(time.time())
    new_scenario_name = f"aiq_platform_api created {old_name} - {timestamp}"
    new_scenario = await save_scenario_copy(
        client,
        scenario_id=scenario_id,
        new_name=new_scenario_name,
        model_json=old_model_json,
    )

    logger.info(f"New scenario created: {new_scenario['name']} ({new_scenario['id']})")
    return new_scenario["id"]


async def test_upload_and_patch_script_scenario(
    client: AttackIQClient,
    script_body: Optional[str] = None,
    file_name: Optional[str] = None,
):
    """Upload a script file and patch an existing script-execution scenario to reference it."""
    logger.info("--- Testing Script Upload + Patch Scenario ---")
    scenario = await Scenarios.get_scenario(client, SCRIPT_EXECUTION_TEMPLATE_ID)

    model_json = scenario["model_json"]
    scripts = model_json["scripts"]

    body = script_body or os.environ.get("ATTACKIQ_SCRIPT_BODY") or "#!/bin/bash\necho hello from aiq-platform-api"
    name = file_name or f"uploaded_script_{int(time.time())}.sh"

    upload = await FileUploads.upload_script_file(
        client=client,
        file_name=name,
        file_content=body.encode(),
        content_type="text/plain",
    )
    scripts[0]["script_files"] = upload["file_path"]
    scripts[0]["success_type"] = "with_exit_code"
    scripts[0]["interpreter"] = "/bin/bash"

    template_instance = await Scenarios.save_copy(
        client,
        SCRIPT_EXECUTION_TEMPLATE_ID,
        {"name": f"SDK Script Upload {int(time.time())}", "model_json": model_json, "fork_template": False},
    )
    scenario_id = template_instance["id"]
    updated = await Scenarios.update_scenario(client, scenario_id, {"model_json": model_json})
    if updated:
        logger.info(f"Patched scenario {scenario_id} with uploaded file {upload['file_path']}")


async def test_create_native_api_and_delete(client: AttackIQClient):
    """Create a Native API scenario and delete it to avoid clutter."""
    logger.info("--- Testing Native API Create (Positive Case) ---")
    apis = [
        {"api": "Kernel32_listprocesses"},
    ]
    scenario_name = f"Native API SDK Test {int(time.time())}"
    created = await Scenarios.create_native_api_scenario(
        client,
        name=scenario_name,
        apis=apis,
        fork_template=False,
        summary="Native API scenario created via SDK use case",
    )
    scenario_id = created["id"]
    logger.info(f"Created Native API scenario: {scenario_name} ({scenario_id})")
    await delete_scenario_use_case(client, scenario_id)


async def test_update_native_api_and_delete(client: AttackIQClient):
    """Create, update, and delete a Native API scenario to exercise update path."""
    logger.info("--- Testing Native API Update (Positive Case) ---")
    apis = [
        {"api": "Kernel32_GetSystemInfo"},
    ]
    scenario_name = f"Native API SDK Update {int(time.time())}"
    created = await Scenarios.create_native_api_scenario(
        client,
        name=scenario_name,
        apis=apis,
        fork_template=False,
        summary="Native API scenario created via SDK use case",
    )
    scenario_id = created["id"]
    logger.info(f"Created Native API scenario: {scenario_name} ({scenario_id})")

    updated_apis = [
        {"api": "Kernel32_GetSystemInfo"},
        {"api": "Advapi32_GetUserNameW"},
    ]
    updated = await Scenarios.update_native_api_scenario(
        client,
        scenario_id,
        apis=updated_apis,
        summary="Updated via SDK use case",
    )
    if updated:
        logger.info(f"Updated Native API scenario {scenario_id} with {len(updated_apis)} APIs")
    await delete_scenario_use_case(client, scenario_id)


async def test_native_api_validation_failure(client: AttackIQClient):
    """Test that invalid Native API identifiers raise a clear ValueError with suggestions."""
    logger.info("--- Testing Native API Validation (Negative Case) ---")
    invalid_apis = [
        {"api": "CreateProcess"},  # Missing Kernel32_ prefix, should suggest Kernel32_CreateProcessA
    ]
    try:
        await Scenarios.create_native_api_scenario(
            client,
            name="Should Fail Validation",
            apis=invalid_apis,
        )
        logger.error("FAILED: create_native_api_scenario should have raised ValueError")
    except ValueError as e:
        logger.info(f"SUCCESS: Caught expected validation error: {e}")


async def create_script_execution_scenario(
    client: AttackIQClient,
    scenario_name: str,
    script_body: str,
    language: str = "bash",
) -> Dict[str, Any]:
    language_key = language.lower()
    if language_key not in LANGUAGE_CONFIG:
        raise ValueError(f"Unsupported language: {language}")
    config = LANGUAGE_CONFIG[language_key]
    if "script_execution" not in config["allowed_templates"]:
        raise ValueError(f"Language {language} not allowed for script execution template")
    template = await Scenarios.get_scenario(client, SCRIPT_EXECUTION_TEMPLATE_ID)
    model_json = template["model_json"]
    scripts = model_json["scripts"]
    file_name = f"{scenario_name.lower().replace(' ', '_')}{config['ext']}"
    upload = await FileUploads.upload_script_file(
        client=client,
        file_name=file_name,
        file_content=script_body.encode(),
        content_type="text/plain",
    )
    scripts[0]["script_files"] = upload["file_path"]
    scripts[0]["success_type"] = "with_exit_code"
    scripts[0]["interpreter"] = config["interpreter"]
    created = await Scenarios.save_copy(
        client,
        SCRIPT_EXECUTION_TEMPLATE_ID,
        {
            "name": scenario_name,
            "model_json": model_json,
            "fork_template": False,
        },
    )
    if not created:
        raise ValueError("Failed to create script execution scenario")
    return created


async def create_command_execution_scenario(
    client: AttackIQClient,
    scenario_name: str,
    command: str,
) -> Dict[str, Any]:
    template = await Scenarios.get_scenario(client, COMMAND_EXECUTION_TEMPLATE_ID)
    model_json = template["model_json"]
    commands = model_json["commands"]
    commands[0]["command"] = command
    commands[0]["success_type"] = "with_exit_code"
    created = await Scenarios.save_copy(
        client,
        COMMAND_EXECUTION_TEMPLATE_ID,
        {
            "name": scenario_name,
            "model_json": model_json,
            "fork_template": False,
        },
    )
    if not created:
        raise ValueError("Failed to create command execution scenario")
    return created


async def update_script_execution_scenario(
    client: AttackIQClient,
    scenario_id: str,
    new_script_body: Optional[str] = None,
    language: Optional[str] = None,
    summary: Optional[str] = None,
) -> Dict[str, Any]:
    scenario = await Scenarios.get_scenario(client, scenario_id)
    model_json = scenario["model_json"]
    scripts = model_json["scripts"]
    payload: Dict[str, Any] = {}
    extras = scenario.get("extras") or {}

    if new_script_body:
        if not language:
            raise ValueError("language is required when uploading a new script")
        language_key = language.lower()
        if language_key not in LANGUAGE_CONFIG:
            raise ValueError(f"Unsupported language: {language}")
        config = LANGUAGE_CONFIG[language_key]
        upload = await FileUploads.upload_script_file(
            client=client,
            file_name=f"{scenario['name'].lower().replace(' ', '_')}{config['ext']}",
            file_content=new_script_body.encode(),
            content_type="text/plain",
        )
        scripts[0]["script_files"] = upload["file_path"]
        scripts[0]["success_type"] = "with_exit_code"
        scripts[0]["interpreter"] = config["interpreter"]
        payload["model_json"] = model_json
        extras = {**extras, "language": language}

    description_payload = _build_description_payload(summary)
    if description_payload:
        payload.update(description_payload)
    if extras:
        payload["extras"] = extras
    if not payload:
        raise ValueError("No updates specified for script execution scenario")
    return await Scenarios.update_scenario(client, scenario_id, payload)


async def update_command_execution_scenario(
    client: AttackIQClient,
    scenario_id: str,
    command: Optional[str] = None,
    summary: Optional[str] = None,
) -> Dict[str, Any]:
    scenario = await Scenarios.get_scenario(client, scenario_id)
    model_json = scenario["model_json"]
    commands = model_json["commands"]
    payload: Dict[str, Any] = {}

    if command:
        commands[0]["command"] = command
        commands[0]["success_type"] = "with_exit_code"
        payload["model_json"] = model_json

    description_payload = _build_description_payload(summary)
    if description_payload:
        payload.update(description_payload)
    if not payload:
        raise ValueError("No updates specified for command execution scenario")
    return await Scenarios.update_scenario(client, scenario_id, payload)


async def test_create_and_delete_script_execution(
    client: AttackIQClient,
    languages: Optional[list[str]] = None,
    script_body: Optional[str] = None,
):
    if languages is None:
        env_value = os.environ.get("ATTACKIQ_SCRIPT_LANGUAGES")
        if env_value:
            languages = [lang.strip() for lang in env_value.split(",") if lang.strip()]
        else:
            languages = ["bash"]

    for language in languages:
        scenario_name = f"SDK Script {language} {int(time.time())}"
        config = LANGUAGE_CONFIG[language.lower()]
        body = script_body or config["sample_body"]
        created = await create_script_execution_scenario(client, scenario_name, body, language)
        scenario_id = created["id"]
        logger.info(f"Created script execution scenario {scenario_id} ({language})")
        await Scenarios.delete_scenario(client, scenario_id)
        logger.info(f"Deleted script execution scenario {scenario_id} ({language})")


async def test_create_and_delete_command_execution(
    client: AttackIQClient,
    command: Optional[str] = None,
):
    scenario_name = f"SDK Command {int(time.time())}"
    command_text = command or os.environ.get("ATTACKIQ_COMMAND_TEXT", "whoami && hostname && date")
    created = await create_command_execution_scenario(client, scenario_name, command_text)
    scenario_id = created["id"]
    logger.info(f"Created command execution scenario {scenario_id}")
    await Scenarios.delete_scenario(client, scenario_id)
    logger.info(f"Deleted command execution scenario {scenario_id}")


async def test_update_script_execution(
    client: AttackIQClient,
    language: str = "bash",
):
    language_key = language.lower()
    created = await create_script_execution_scenario(
        client,
        scenario_name=f"SDK Script Update {int(time.time())}",
        script_body=LANGUAGE_CONFIG[language_key]["sample_body"],
        language=language,
    )
    scenario_id = created["id"]
    try:
        updated = await update_script_execution_scenario(
            client,
            scenario_id=scenario_id,
            new_script_body=f"#!/bin/bash\necho 'updated {time.time()}'",
            language=language,
            summary="Updated via scenario_use_cases",
        )
        logger.info(f"Updated script scenario: {updated}")
    finally:
        await Scenarios.delete_scenario(client, scenario_id)
        logger.info(f"Deleted script scenario {scenario_id}")


async def test_update_command_execution(
    client: AttackIQClient,
):
    created = await create_command_execution_scenario(
        client,
        scenario_name=f"SDK Command Update {int(time.time())}",
        command="whoami",
    )
    scenario_id = created["id"]
    try:
        updated = await update_command_execution_scenario(
            client,
            scenario_id=scenario_id,
            command="hostname && date",
            summary="Updated via scenario_use_cases",
        )
        logger.info(f"Updated command scenario: {updated}")
    finally:
        await Scenarios.delete_scenario(client, scenario_id)
        logger.info(f"Deleted command scenario {scenario_id}")


async def test_verify_fix_in_ui(client: AttackIQClient, language: str = "powershell"):
    """Create and update a script execution scenario for manual UI verification.

    This test demonstrates the fixed file_path handling:
    1. Creates scenario with script (tests CREATE path)
    2. Updates scenario with new script (tests UPDATE path)
    3. Prints scenario ID for manual UI verification
    4. Does NOT delete - allows manual inspection
    """
    timestamp = int(time.time())

    logger.info("=" * 80)
    logger.info("VERIFY SDK FIX IN UI - CREATE + UPDATE TEST")
    logger.info("=" * 80)

    # Step 1: Create scenario with initial script
    logger.info(f"\n[1/4] Creating {language} script execution scenario...")
    initial_script = f"""# SDK Fix Verification Test
Write-Host "=== Created via SDK at {timestamp} ==="
Write-Host "Testing file_path format fix"
Write-Host "Created by: Rajesh Sharma"
Write-Host "Date: $(Get-Date)"
"""

    created = await create_script_execution_scenario(
        client=client,
        scenario_name=f"SDK Fix Verification {timestamp}",
        script_body=initial_script,
        language=language,
    )

    scenario_id = created["id"]
    initial_file_path = created["model_json"]["scripts"][0]["script_files"]

    logger.info(f"Created scenario ID: {scenario_id}")
    logger.info(f"Initial script_files: '{initial_file_path}'")

    # Step 2: Verify format
    logger.info("\n[2/4] Verifying file_path format...")
    has_prefix = initial_file_path.startswith("files/") or initial_file_path.startswith("downloads/")
    has_slash = "/" in initial_file_path

    if has_prefix:
        logger.error(f"FAILED: file_path has unwanted prefix: '{initial_file_path}'")
    elif not has_slash:
        logger.error(f"FAILED: file_path missing uuid/filename format: '{initial_file_path}'")
    else:
        logger.info(f"Format correct: {initial_file_path} (uuid/filename)")

    # Step 3: Update scenario with new script
    logger.info("\n[3/4] Updating scenario with new script...")
    updated_script = f"""# SDK Fix Verification Test - UPDATED
Write-Host "=== UPDATED via SDK at {int(time.time())} ==="
Write-Host "Testing UPDATE path file_path format"
Write-Host "Updated by: Rajesh Sharma"
Write-Host "Update timestamp: $(Get-Date)"
Write-Host "This script was modified after creation!"
"""

    updated = await update_script_execution_scenario(
        client=client,
        scenario_id=scenario_id,
        new_script_body=updated_script,
        language=language,
        summary="Updated via SDK use case - testing file_path fix",
    )

    updated_file_path = updated["model_json"]["scripts"][0]["script_files"]
    logger.info(f"Updated scenario ID: {scenario_id}")
    logger.info(f"OLD script_files: '{initial_file_path}'")
    logger.info(f"NEW script_files: '{updated_file_path}'")

    # Step 4: Print manual verification instructions
    logger.info("\n[4/4] Manual UI Verification Instructions:")
    logger.info("=" * 80)
    logger.info(f"Scenario ID: {scenario_id}")
    logger.info(f"Scenario Name: SDK Fix Verification {timestamp}")
    logger.info(f"URL: https://ultimate.warrior.attackiq.net/content_library/scenarios?scenario={scenario_id}")
    logger.info("")
    logger.info("Steps to verify:")
    logger.info("1. Open the URL above in your browser")
    logger.info("2. Click on the scenario to open it")
    logger.info("3. Go to the 'Parameters' tab")
    logger.info("4. Click the eye icon next to 'Script File'")
    logger.info("")
    logger.info("Expected Results:")
    logger.info("- Script content displays (not 'invalid uuid format')")
    logger.info("- Script shows 'UPDATED via SDK' message")
    logger.info("- Script shows 'Updated by: Rajesh Sharma'")
    logger.info("- No 'FILE NOT SHOWN' error")
    logger.info("")
    logger.info("File paths used:")
    logger.info(f"  CREATE: {initial_file_path}")
    logger.info(f"  UPDATE: {updated_file_path}")
    logger.info("")
    logger.info("NOTE: Scenario NOT deleted - verify manually, then delete if needed")
    logger.info("=" * 80)

    return scenario_id


async def test_delete_scenario(client: AttackIQClient, scenario_id: str):
    logger.info("--- Testing Scenario Deletion ---")
    if not scenario_id:
        logger.warning("No scenario ID provided for deletion")
        return
    await delete_scenario_use_case(client, scenario_id)


async def search_scenarios_use_case(
    client: AttackIQClient,
    query: Optional[str] = None,
    limit: Optional[int] = 20,
    offset: Optional[int] = 0,
    ordering: Optional[str] = "-modified",
) -> dict:
    logger.info(
        f"--- Searching scenarios with query: '{query}', limit: {limit}, offset: {offset}, ordering: {ordering} ---"
    )
    try:
        result = await Scenarios.search_scenarios(client, query, limit, offset, ordering)
        logger.info(f"Found {result['count']} total, returning {len(result['results'])}")
        for idx, scenario in enumerate(result["results"], 1):
            logger.info(f"{idx}. {scenario['name']} (ID: {scenario['id']})")
        return result
    except Exception as e:
        logger.error(f"Failed to search scenarios: {e}")
        raise


async def get_scenario_details_use_case(
    client: AttackIQClient,
    scenario_id: str,
) -> Optional[Dict[str, Any]]:
    logger.info(f"--- Getting details for scenario: {scenario_id} ---")
    details = await Scenarios.get_scenario_details(client, scenario_id)
    if details:
        logger.info(f"Scenario: {details['name']}")
        logger.info(f"Description: {details.get('description', 'N/A')}")
        logger.info(f"Created: {details.get('created_at', 'N/A')}")
        return details
    logger.warning(f"No details found for scenario: {scenario_id}")
    return None


async def test_search_scenarios(client: AttackIQClient):
    logger.info("--- Testing Scenario Search ---")

    # Search by keyword
    logger.info("\n1. Searching by keyword 'LSASS':")
    await search_scenarios_use_case(client, "LSASS", limit=5)

    # Search by MITRE technique
    logger.info("\n2. Searching by MITRE technique 'T1003':")
    await search_scenarios_use_case(client, "T1003", limit=5)

    # Search by tag
    logger.info("\n3. Searching by tag 'ransomware':")
    await search_scenarios_use_case(client, "ransomware", limit=5)

    # List all scenarios
    logger.info("\n4. Listing all scenarios (no query):")
    await search_scenarios_use_case(client, query=None, limit=5)


async def test_search_scenarios_by_tag_query(client: AttackIQClient, tag_query: Optional[str] = None, limit: int = 10):
    logger.info("--- Testing Scenario Search by Tag Query (MITRE IDs allowed) ---")
    tag_query = tag_query or os.environ.get("ATTACKIQ_TAG_QUERY", "T1055")
    result = await Scenarios.search_scenarios_by_tag(client, tag_query=tag_query, limit=limit)
    tags = result.get("tags", [])
    scenarios = result.get("scenarios", [])
    logger.info(f"Query '{tag_query}': found {len(tags)} tag(s), {len(scenarios)} scenario(s)")
    for idx, tag in enumerate(tags, 1):
        logger.info(f"Tag {idx}: {tag.get('display_name') or tag.get('name')} (ID: {tag.get('id')})")
    for idx, scenario in enumerate(scenarios, 1):
        logger.info(f"{idx}. {scenario.get('name')} (ID: {scenario.get('id')})")
    if result.get("detail"):
        logger.info(f"Detail: {result['detail']}")


async def test_search_scenarios_by_mitre(client: AttackIQClient, technique_id: Optional[str] = None, limit: int = 10):
    logger.info("--- Testing Scenario Search by MITRE ID (normalizes dotted IDs) ---")
    technique_id = technique_id or os.environ.get("ATTACKIQ_MITRE_ID", "T1055")
    result = await Scenarios.search_scenarios_by_mitre(client, technique_id=technique_id, limit=limit)
    tags = result.get("tags", [])
    scenarios = result.get("scenarios", [])
    logger.info(f"Technique {technique_id}: found {len(tags)} tag(s), {len(scenarios)} scenario(s)")
    for idx, tag in enumerate(tags, 1):
        logger.info(f"Tag {idx}: {tag.get('display_name') or tag.get('name')} (ID: {tag.get('id')})")
    for idx, scenario in enumerate(scenarios, 1):
        logger.info(f"{idx}. {scenario.get('name')} (ID: {scenario.get('id')})")
    if result.get("detail"):
        logger.info(f"Detail: {result['detail']}")
    return result


async def test_get_scenario_details(client: AttackIQClient, scenario_id: Optional[str] = None):
    logger.info("--- Testing Get Scenario Details ---")

    if not scenario_id:
        # First search for a scenario, then get its details
        scenarios = await search_scenarios_use_case(client, "Mimikatz", limit=1)
        if not scenarios["results"]:
            logger.warning("No scenarios found to get details for")
            return
        scenario_id = scenarios["results"][0]["id"]

    await get_scenario_details_use_case(client, scenario_id)


async def test_copy_and_delete(client: AttackIQClient, scenario_id: Optional[str] = None):
    logger.info("--- Testing Scenario Copy and Delete Workflow ---")

    if not scenario_id:
        scenario_id = os.environ.get("ATTACKIQ_SCENARIO_ID", "5417db5e-569f-4660-86ae-9ea7b73452c5")

    new_scenario_id = await test_copy_scenario(client, scenario_id)
    if new_scenario_id:
        logger.info(f"--- Proceeding to delete the created scenario: {new_scenario_id} ---")
        await test_delete_scenario(client, new_scenario_id)
    else:
        logger.warning("Could not get ID of newly created scenario, skipping deletion.")


async def test_pagination_workflow(client: AttackIQClient):
    """
    Test pagination with offset to demonstrate fetching batches.

    This validates:
    1. minimal=true reduces fields (23 -> 7)
    2. offset pagination works correctly
    3. No duplicate scenarios across batches

    Use this pattern for other endpoints (assets, assessments, attack graphs).
    """
    logger.info("--- Testing Pagination Workflow ---")

    batch_size = 5
    max_batches = 3
    all_ids = []

    for batch_num in range(1, max_batches + 1):
        offset = (batch_num - 1) * batch_size
        logger.info(f"\n--- Batch {batch_num}: offset={offset}, limit={batch_size} ---")

        scenarios = [
            s
            async for s in Scenarios.list_scenarios(
                client, params={"search": "powershell"}, limit=batch_size, offset=offset
            )
        ]

        if not scenarios:
            logger.info("No more scenarios. Stopping.")
            break

        logger.info(f"Retrieved {len(scenarios)} scenarios:")
        for idx, scenario in enumerate(scenarios, 1):
            scenario_id = scenario["id"]
            scenario_name = scenario["name"]
            logger.info(f"  {idx}. {scenario_name}")
            all_ids.append(scenario_id)

        logger.info(f"Fields in scenario: {list(scenarios[0].keys())}")
        logger.info(f"Field count: {len(scenarios[0].keys())} (7 with minimal=true)")

    logger.info("\n--- Summary ---")
    logger.info(f"Total fetched: {len(all_ids)}")
    logger.info(f"Unique: {len(set(all_ids))}")
    logger.info(f"Duplicates: {len(all_ids) - len(set(all_ids))}")

    if len(all_ids) == len(set(all_ids)):
        logger.info("SUCCESS: No duplicates, pagination working correctly!")
    else:
        logger.error("FAILED: Duplicates detected!")


async def test_create_and_delete_download_to_memory(client: AttackIQClient):
    """Test the complete ZIP-only Download to Memory scenario flow."""
    logger.info("--- Testing Download to Memory Scenario Create + Delete ---")

    # We use a dummy ZIP path and password for validation testing
    scenario_name = f"SDK DTM Test {int(time.time())}"
    created = await Scenarios.create_download_to_memory_scenario(
        client,
        name=scenario_name,
        zip_file="uuid/file.zip",
        zip_file_password="infected",
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        summary="Secure ZIP flow created via SDK use case",
    )

    scenario_id = created["id"]
    logger.info(f"Created DTM scenario: {scenario_name} ({scenario_id})")
    await Scenarios.delete_scenario(client, scenario_id)
    logger.info(f"Deleted DTM scenario {scenario_id}")


async def test_update_download_to_memory_and_delete(client: AttackIQClient):
    """Test updating a Download to Memory scenario."""
    logger.info("--- Testing Download to Memory Scenario Update + Delete ---")

    created = await Scenarios.create_download_to_memory_scenario(
        client,
        name=f"SDK DTM Update Test {int(time.time())}",
        zip_file="uuid/old.zip",
        zip_file_password="old_password",
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    )
    scenario_id = created["id"]

    try:
        updated = await Scenarios.update_download_to_memory_scenario(
            client,
            scenario_id,
            zip_file="uuid/new.zip",
            zip_file_password="new_password",
            summary="Updated via SDK use case",
        )
        if updated:
            logger.info(f"Updated DTM scenario {scenario_id}")
    finally:
        await Scenarios.delete_scenario(client, scenario_id)
        logger.info(f"Deleted DTM scenario {scenario_id}")


async def test_all(client: AttackIQClient):
    # Test listing without filter
    await test_list_scenarios(client)

    # Test listing with filter
    await test_list_mimikatz_scenarios(client)

    # Test listing by tag (requires ATTACKIQ_TAG_ID)
    await test_list_scenarios_by_tag(client, limit=3)

    # Test search scenarios
    await test_search_scenarios(client)

    # Test tag query search (MITRE IDs allowed)
    await test_search_scenarios_by_tag_query(client, limit=5)

    # Test MITRE search with normalization
    await test_search_scenarios_by_mitre(client, limit=5)

    # Test get scenario details
    await test_get_scenario_details(client)

    # Test pagination workflow
    await test_pagination_workflow(client)

    # Test copy and delete workflow
    scenario_id = os.environ.get("ATTACKIQ_SCENARIO_ID")
    if scenario_id:
        await test_copy_and_delete(client, scenario_id)
    else:
        logger.warning("ATTACKIQ_SCENARIO_ID not set. Skipping copy/delete tests.")

    # Test upload + patch workflow (requires separate scenario id)
    await test_upload_and_patch_script_scenario(client)
    await test_create_and_delete_script_execution(client)
    await test_create_and_delete_command_execution(client)
    await test_update_script_execution(client)
    await test_update_command_execution(client)
    await test_create_and_delete_download_to_memory(client)
    await test_update_download_to_memory_and_delete(client)
    await test_create_native_api_and_delete(client)
    await test_update_native_api_and_delete(client)
    await test_native_api_validation_failure(client)


async def test_analyze_scenario_requirements(client: AttackIQClient) -> Dict[str, Any]:
    """Test scenario requirements analysis.

    Run: python aiq_platform_api/scenario_use_cases.py analyze_requirements
    """
    logger.info("=== Testing analyze_scenario_requirements ===")
    results = {"passed": 0, "failed": 0, "checks": []}

    def check(name: str, condition: bool, detail: str = ""):
        status = "✅" if condition else "❌"
        results["passed" if condition else "failed"] += 1
        results["checks"].append({"name": name, "passed": condition, "detail": detail})
        logger.info(f"{status} {name}: {detail}")

    # Get some scenarios to analyze
    search_result = await Scenarios.search_scenarios(client, limit=5)
    scenario_ids = [s["id"] for s in search_result["results"]]
    check("Found scenarios", len(scenario_ids) > 0, f"Got {len(scenario_ids)} scenarios")

    # Test single scenario requirements
    if scenario_ids:
        req = await Scenarios.get_scenario_requirements(client, scenario_ids[0])
        check("Single requirements - has scenario_id", "scenario_id" in req, f"scenario_id={req.get('scenario_id')}")
        check("Single requirements - has name", "name" in req, f"name={req.get('name', '')[:30]}")
        check(
            "Single requirements - has supported_platforms",
            "supported_platforms" in req,
            f"platforms={req.get('supported_platforms')}",
        )
        check(
            "Single requirements - has is_multi_asset",
            "is_multi_asset" in req,
            f"is_multi_asset={req.get('is_multi_asset')}",
        )
        check("Single requirements - has runnable", "runnable" in req, f"runnable={req.get('runnable')}")

    # Test bulk analysis
    analysis = await Scenarios.analyze_scenario_requirements(client, scenario_ids)
    check(
        "Bulk analysis - has summary", "summary" in analysis, f"summary keys={list(analysis.get('summary', {}).keys())}"
    )
    check(
        "Bulk analysis - has by_platform",
        "by_platform" in analysis,
        f"platforms={list(analysis.get('by_platform', {}).keys())}",
    )
    check(
        "Bulk analysis - analyzed count",
        analysis["summary"]["analyzed"] == len(scenario_ids),
        f"analyzed {analysis['summary']['analyzed']} of {len(scenario_ids)}",
    )

    # Summary
    total = results["passed"] + results["failed"]
    logger.info(f"\n=== Test Results: {results['passed']}/{total} passed ===")
    return results


async def run_test(choice: "TestChoice", client: AttackIQClient, scenario_id: Optional[str] = None):
    """Run the selected test."""
    test_functions = {
        TestChoice.LIST_ALL: lambda: test_list_scenarios(client),
        TestChoice.LIST_MIMIKATZ: lambda: test_list_mimikatz_scenarios(client),
        TestChoice.SEARCH_SCENARIOS: lambda: test_search_scenarios(client),
        TestChoice.SEARCH_BY_TAG_QUERY: lambda: test_search_scenarios_by_tag_query(client),
        TestChoice.SEARCH_BY_MITRE: lambda: test_search_scenarios_by_mitre(client),
        TestChoice.LIST_BY_TAG: lambda: test_list_scenarios_by_tag(client),
        TestChoice.GET_SCENARIO_DETAILS: lambda: test_get_scenario_details(client, scenario_id),
        TestChoice.PAGINATION_WORKFLOW: lambda: test_pagination_workflow(client),
        TestChoice.COPY_SCENARIO: lambda: test_copy_scenario(client, scenario_id),
        TestChoice.DELETE_SCENARIO: lambda: (
            test_delete_scenario(client, scenario_id)
            if scenario_id
            else logger.error("Scenario ID required for delete test")
        ),
        TestChoice.COPY_AND_DELETE: lambda: test_copy_and_delete(client, scenario_id),
        TestChoice.UPLOAD_AND_PATCH: lambda: test_upload_and_patch_script_scenario(client),
        TestChoice.CREATE_SCRIPT_AND_DELETE: lambda: test_create_and_delete_script_execution(client),
        TestChoice.CREATE_COMMAND_AND_DELETE: lambda: test_create_and_delete_command_execution(client),
        TestChoice.UPDATE_SCRIPT_AND_DELETE: lambda: test_update_script_execution(client),
        TestChoice.UPDATE_COMMAND_AND_DELETE: lambda: test_update_command_execution(client),
        TestChoice.CREATE_NATIVE_API_AND_DELETE: lambda: test_create_native_api_and_delete(client),
        TestChoice.UPDATE_NATIVE_API_AND_DELETE: lambda: test_update_native_api_and_delete(client),
        TestChoice.CREATE_DTM_AND_DELETE: lambda: test_create_and_delete_download_to_memory(client),
        TestChoice.UPDATE_DTM_AND_DELETE: lambda: test_update_download_to_memory_and_delete(client),
        TestChoice.NATIVE_API_VALIDATION_FAILURE: lambda: test_native_api_validation_failure(client),
        TestChoice.VERIFY_FIX_IN_UI: lambda: test_verify_fix_in_ui(client),
        TestChoice.ANALYZE_REQUIREMENTS: lambda: test_analyze_scenario_requirements(client),
        TestChoice.ALL: lambda: test_all(client),
    }
    await test_functions[choice]()


class TestChoice(Enum):
    LIST_ALL = "list_all"
    LIST_MIMIKATZ = "list_mimikatz"
    SEARCH_SCENARIOS = "search_scenarios"
    SEARCH_BY_TAG_QUERY = "search_by_tag_query"
    SEARCH_BY_MITRE = "search_by_mitre"
    LIST_BY_TAG = "list_by_tag"
    GET_SCENARIO_DETAILS = "get_scenario_details"
    PAGINATION_WORKFLOW = "pagination_workflow"
    COPY_SCENARIO = "copy_scenario"
    DELETE_SCENARIO = "delete_scenario"
    COPY_AND_DELETE = "copy_and_delete"
    UPLOAD_AND_PATCH = "upload_and_patch"
    CREATE_SCRIPT_AND_DELETE = "create_script_and_delete"
    CREATE_COMMAND_AND_DELETE = "create_command_and_delete"
    UPDATE_SCRIPT_AND_DELETE = "update_script_and_delete"
    UPDATE_COMMAND_AND_DELETE = "update_command_and_delete"
    CREATE_NATIVE_API_AND_DELETE = "create_native_api_and_delete"
    UPDATE_NATIVE_API_AND_DELETE = "update_native_api_and_delete"
    CREATE_DTM_AND_DELETE = "create_dtm_and_delete"
    UPDATE_DTM_AND_DELETE = "update_dtm_and_delete"
    NATIVE_API_VALIDATION_FAILURE = "native_api_validation_failure"
    VERIFY_FIX_IN_UI = "verify_fix_in_ui"
    ANALYZE_REQUIREMENTS = "analyze_requirements"
    ALL = "all"


async def main():
    require_env(ATTACKIQ_PLATFORM_URL, ATTACKIQ_PLATFORM_API_TOKEN)
    choice = parse_test_choice(TestChoice)

    async with AttackIQClient(ATTACKIQ_PLATFORM_URL, ATTACKIQ_PLATFORM_API_TOKEN) as client:
        scenario_id = os.environ.get("ATTACKIQ_SCENARIO_ID", "5417db5e-569f-4660-86ae-9ea7b73452c5")
        await run_test(choice, client, scenario_id)


if __name__ == "__main__":
    asyncio.run(main())
