# Migration Guide: v0.2.x → v1.0.0

This document covers all breaking changes, migration steps, and new features in v1.0.0 of the AttackIQ Platform SDK.

---

## Overview

**v1.0.0 is a major release** that migrates the entire SDK from synchronous to asynchronous I/O. This enables better performance for concurrent API calls and aligns with modern Python async patterns.

| Component | Change |
|-----------|--------|
| Python SDK | Sync → Async (httpx) |
| Go CLI | Phase logs endpoint fix |
| HTTP Client | requests → httpx |
| Version | 0.2.42 → 1.0.0 |

---

## Breaking Changes

### 1. Async-Only API

All SDK methods now require `async`/`await`:

```python
# BEFORE (v0.2.x) - Synchronous
from aiq_platform_api import AttackIQRestClient
from aiq_platform_api.common_utils import ScenarioUtils

client = AttackIQRestClient(url, token)
for scenario in ScenarioUtils.list_scenarios(client, limit=10):
    print(scenario["name"])

# AFTER (v1.0.0) - Asynchronous
from aiq_platform_api import AttackIQClient, Scenarios

async def main():
    async with AttackIQClient(url, token) as client:
        async for scenario in Scenarios.list_scenarios(client, limit=10):
            print(scenario["name"])

asyncio.run(main())
```

### 2. Client Class Renamed

| Before | After |
|--------|-------|
| `AttackIQRestClient` | `AttackIQClient` |

### 3. Class Names Changed (Utils Suffix Removed)

All utility classes have been renamed. The `Utils` suffix has been removed:

| Before (v0.2.x) | After (v1.0.0) |
|-----------------|----------------|
| `ScenarioUtils` | `Scenarios` |
| `AssetUtils` | `Assets` |
| `AssessmentUtils` | `Assessments` |
| `ConnectorUtils` | `Connectors` |
| `TagSetUtils` | `TagSets` |
| `TagUtils` | `Tags` |
| `TaggedItemUtils` | `TaggedItems` |
| `ResultsUtils` | `Results` |
| `PhaseResultsUtils` | `PhaseResults` |
| `PhaseLogsUtils` | `PhaseLogs` |
| `FileUploadUtils` | `FileUploads` |
| `FileDownloadUtils` | `FileDownloads` |
| `UnifiedMitigationUtils` | `UnifiedMitigations` |
| `UnifiedMitigationProjectUtils` | `UnifiedMitigationProjects` |
| `UnifiedMitigationWithRelationsUtils` | `UnifiedMitigationWithRelations` |
| `UnifiedMitigationReportingUtils` | `UnifiedMitigationReporting` |

### 4. `common_utils.py` Removed

The `common_utils.py` module has been removed. It was a backward compatibility layer that re-exported symbols from `core/`.

- All domain classes are now imported from `aiq_platform_api` directly
- Test utilities (`require_env`, `parse_test_choice`) moved to `aiq_platform_api.core.testing`

```python
# BEFORE (v0.2.x)
from aiq_platform_api.common_utils import ScenarioUtils, require_env

# AFTER (v1.0.0)
from aiq_platform_api import Scenarios
from aiq_platform_api.core.testing import require_env
```

> **GOTCHA**: When removing `common_utils.py`, check ALL files for imports - including `examples/`, `tests/`, and any other scripts. A grep for `common_utils` across the entire codebase will reveal any missed imports that would cause `ModuleNotFoundError` at runtime.

### 5. Import from Top-Level Only

Import everything from `aiq_platform_api` directly. Do not use `.core` or `.env` submodules:

```python
# BEFORE (v0.2.x) - Mixed imports
from aiq_platform_api import AttackIQRestClient
from aiq_platform_api.common_utils import ScenarioUtils
from aiq_platform_api.core import AssetUtils
from aiq_platform_api.env import ATTACKIQ_PLATFORM_URL

# AFTER (v1.0.0) - Single import location
from aiq_platform_api import (
    AttackIQClient,
    Scenarios,
    Assets,
    ATTACKIQ_PLATFORM_URL,
    ATTACKIQ_PLATFORM_API_TOKEN,
)
```

### 6. Generator → AsyncGenerator

All list/pagination methods now return `AsyncGenerator` instead of `Generator`:

```python
# BEFORE
def list_scenarios(...) -> Generator[Dict[str, Any], None, None]:
    yield from itertools.islice(generator, offset, offset + limit)

# AFTER
async def list_scenarios(...) -> AsyncGenerator[Dict[str, Any], None]:
    async for item in async_islice(generator, offset, offset + limit):
        yield item
```

### 7. Context Manager Required

The client should be used as an async context manager to ensure proper cleanup:

```python
# BEFORE - No context manager needed
client = AttackIQRestClient(url, token)
# ... use client

# AFTER - Use async context manager
async with AttackIQClient(url, token) as client:
    # ... use client
# (httpx connection pool properly closed)
```

---

## Migration Steps

### Step 1: Update Imports

```python
# Old imports
from aiq_platform_api import AttackIQRestClient
from aiq_platform_api.common_utils import ScenarioUtils, AssetUtils
from aiq_platform_api.env import ATTACKIQ_PLATFORM_URL, ATTACKIQ_PLATFORM_API_TOKEN

# New imports (single location, new class names)
from aiq_platform_api import (
    AttackIQClient,
    Scenarios,
    Assets,
    ATTACKIQ_PLATFORM_URL,
    ATTACKIQ_PLATFORM_API_TOKEN,
)
```

### Step 2: Rename Class References

Find and replace all class names:

| Find | Replace |
|------|---------|
| `ScenarioUtils` | `Scenarios` |
| `AssetUtils` | `Assets` |
| `AssessmentUtils` | `Assessments` |
| `ConnectorUtils` | `Connectors` |
| `TagSetUtils` | `TagSets` |
| `TagUtils` | `Tags` |
| `TaggedItemUtils` | `TaggedItems` |
| `ResultsUtils` | `Results` |
| `PhaseResultsUtils` | `PhaseResults` |
| `PhaseLogsUtils` | `PhaseLogs` |
| `FileUploadUtils` | `FileUploads` |
| `FileDownloadUtils` | `FileDownloads` |
| `UnifiedMitigationUtils` | `UnifiedMitigations` |
| `UnifiedMitigationProjectUtils` | `UnifiedMitigationProjects` |
| `UnifiedMitigationWithRelationsUtils` | `UnifiedMitigationWithRelations` |
| `UnifiedMitigationReportingUtils` | `UnifiedMitigationReporting` |

### Step 3: Convert Functions to Async

```python
# Old synchronous function
def fetch_scenarios(client):
    scenarios = []
    for s in ScenarioUtils.list_scenarios(client, limit=10):
        scenarios.append(s)
    return scenarios

# New async function
async def fetch_scenarios(client):
    scenarios = []
    async for s in Scenarios.list_scenarios(client, limit=10):
        scenarios.append(s)
    return scenarios
```

### Step 4: Update Client Instantiation

```python
# Old pattern
client = AttackIQRestClient(url, token)
result = client.get_object("v1/scenarios/123")

# New pattern
async with AttackIQClient(url, token) as client:
    result = await client.get_object("v1/scenarios/123")
```

### Step 5: Update Entry Points

```python
# Old entry point
if __name__ == "__main__":
    client = AttackIQRestClient(url, token)
    main(client)

# New entry point
if __name__ == "__main__":
    import asyncio

    async def main():
        async with AttackIQClient(url, token) as client:
            await run_workflow(client)

    asyncio.run(main())
```

### Step 6: Collect Results from Async Generators

```python
# Old pattern - list() works directly
scenarios = list(ScenarioUtils.list_scenarios(client, limit=10))

# New pattern - use list comprehension with async for
scenarios = [s async for s in Scenarios.list_scenarios(client, limit=10)]
```

---

## Available Top-Level Exports

All imports should come from `aiq_platform_api`:

```python
from aiq_platform_api import (
    # Client
    AttackIQClient,

    # Logger
    AttackIQLogger,

    # Domain classes
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

    # Enums
    AssetStatus,
    UnifiedMitigationType,
    IntegrationName,
    AssessmentExecutionStrategy,
    DetectionStatus,
    DetectionOutcome,
    AnalystVerdict,

    # Constants
    DETECTION_TYPES,
    INTEGRATION_NAMES,
    ScenarioTemplateType,
    SCENARIO_TEMPLATE_IDS,
    ScenarioLanguageConfig,
    SCENARIO_LANGUAGES,

    # Environment
    ATTACKIQ_PLATFORM_URL,
    ATTACKIQ_PLATFORM_API_TOKEN,
)
```

---

## New Features

### 1. Async HTTP Client (httpx)

- **Connection pooling**: Reuses connections for better performance
- **HTTP/2 support**: Automatic protocol negotiation
- **Proper timeouts**: Configurable via `httpx.Timeout`

```python
from httpx import Timeout

# Custom timeout (default: 30s)
client = AttackIQClient(url, token, timeout=Timeout(60.0))
```

### 2. File Operations

```python
from aiq_platform_api import FileUploads, FileDownloads

# Upload a script
result = await FileUploads.upload_script_file(
    client, "test.sh", b"#!/bin/bash\necho hello", "text/plain"
)

# Download a file
content = await FileDownloads.download_file(client, file_id)
```

### 3. Async Utilities Module

New `core/async_utils.py` provides async equivalents of itertools:

```python
from aiq_platform_api.core.async_utils import async_islice, async_take

# Slice an async generator
async for item in async_islice(generator, start=5, stop=15):
    process(item)

# Take first N items
async for item in async_take(generator, limit=10):
    process(item)
```

### 4. Helper Functions for Testing

```python
from aiq_platform_api.core.testing import require_env, parse_test_choice

# Validate environment variables (exits if missing)
require_env(ATTACKIQ_PLATFORM_URL, ATTACKIQ_PLATFORM_API_TOKEN)

# Parse CLI argument for test choice
choice = parse_test_choice(TestChoice)
```

---

## Bug Fixes

### 1. Phase Logs Endpoint (Python + Go)

**Issue**: SDK was using wrong endpoint for phase logs.

| Before | After |
|--------|-------|
| `/v1/phase_logs` | `/v1/logs_api/phase_logs` |

### 2. Phase Logs Primary Filter

**Issue**: `scenario_job_id` was the only filter, but UI uses `node_instance_id`.

```python
# BEFORE - Only scenario_job_id
PhaseLogs.get_phase_logs(client, scenario_job_id="...")

# AFTER - node_instance_id is primary (matches UI)
PhaseLogs.get_phase_logs(
    client,
    node_instance_id="...",      # Primary filter (same as UI)
    scenario_job_id="...",       # Alternative filter
    phase_number=1,              # Optional
    trace_type_id="1,2",         # Optional (comma-separated)
)
```

### 3. Phase Results Parameter Name

**Issue**: Incorrect parameter name for run ID filter.

| Before | After |
|--------|-------|
| `project_run` | `project_run_id` |

---

## Go CLI Changes

### Phase Logs Command Updated

The `aiq phase logs` command now uses the correct endpoint and filters:

```bash
# New flags
aiq phase logs --node-instance-id <id>     # Primary filter (same as UI)
aiq phase logs --scenario-job-id <id>      # Alternative filter
aiq phase logs --phase-number 1            # Optional
aiq phase logs --trace-type-id "1,2"       # Optional
```

### New Test Command

```bash
# Run all domain tests
aiq test all

# Run specific domain tests
aiq test phase
aiq test scenarios
```

---

## Dependency Changes

| Package | Before | After |
|---------|--------|-------|
| `requests` | ^2.31.0 | (removed) |
| `httpx` | (none) | >=0.27,<1.0 |
| `pytest-asyncio` | (none) | ^1.3.0 |

---

## Example Usage

```python
import asyncio
from aiq_platform_api import (
    AttackIQClient,
    Scenarios,
    Assets,
    ATTACKIQ_PLATFORM_URL,
    ATTACKIQ_PLATFORM_API_TOKEN,
)

async def main():
    async with AttackIQClient(ATTACKIQ_PLATFORM_URL, ATTACKIQ_PLATFORM_API_TOKEN) as client:
        # Search scenarios
        result = await Scenarios.search_scenarios(client, query="powershell", limit=10)
        print(f"Found {result['count']} scenarios")

        # List assets
        async for asset in Assets.get_assets(client, limit=5):
            print(asset["hostname"])

asyncio.run(main())
```

---

## Quick Reference

| Task | v0.2.x | v1.0.0 |
|------|--------|--------|
| Import client | `AttackIQRestClient` | `AttackIQClient` |
| Import utils | `from aiq_platform_api.common_utils import ScenarioUtils` | `from aiq_platform_api import Scenarios` |
| Create client | `client = AttackIQRestClient(...)` | `async with AttackIQClient(...) as client:` |
| Make request | `client.get_object(...)` | `await client.get_object(...)` |
| Iterate results | `for item in ScenarioUtils.list_scenarios(...):` | `async for item in Scenarios.list_scenarios(...):` |
| Collect list | `list(generator)` | `[x async for x in generator]` |
