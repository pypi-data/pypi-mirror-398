import copy
from typing import Optional, Dict, Any, AsyncGenerator, List

from aiq_platform_api.core.async_utils import async_islice
from aiq_platform_api.core.client import AttackIQClient
from aiq_platform_api.core.constants import ScenarioTemplateType, SCENARIO_TEMPLATE_IDS
from aiq_platform_api.core.logger import AttackIQLogger
from aiq_platform_api.core.tags import Tags

logger = AttackIQLogger.get_logger(__name__)


class Scenarios:
    """Utilities for interacting with Scenario models.

    API Endpoint: /v1/scenarios
    """

    ENDPOINT = "v1/scenarios"

    @staticmethod
    async def list_scenarios(
        client: AttackIQClient,
        params: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = 10,
        offset: Optional[int] = 0,
        ordering: Optional[str] = "-modified",
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """List scenarios with minimal fields, ordering, and offset support.

        Args:
            ordering: Sort order (default: -modified for most recent first)
                     Use '-' prefix for descending (e.g., '-modified', '-created')
                     Omit '-' for ascending (e.g., 'modified', 'created', 'name')
        """
        request_params = params.copy() if params else {}
        request_params["minimal"] = "true"
        if "ordering" not in request_params and ordering:
            request_params["ordering"] = ordering
        logger.info(f"Listing scenarios with params: {request_params}, limit: {limit}, offset: {offset}")
        generator = client.get_all_objects(Scenarios.ENDPOINT, params=request_params)
        stop = offset + limit if limit is not None else None
        async for scenario in async_islice(generator, offset, stop):
            yield scenario

    @staticmethod
    async def get_scenario(client: AttackIQClient, scenario_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific scenario by its ID."""
        endpoint = f"{Scenarios.ENDPOINT}/{scenario_id}"
        logger.info(f"Getting scenario: {scenario_id}")
        return await client.get_object(endpoint)

    @staticmethod
    async def get_scenario_requirements(client: AttackIQClient, scenario_id: str) -> Dict[str, Any]:
        """Extract scenario requirements for planning purposes.

        Returns:
            dict with:
            - scenario_id: The scenario UUID
            - name: Scenario name
            - supported_platforms: List of platform keys (windows, osx, centos, etc.)
            - is_multi_asset: Whether scenario requires multiple assets
            - runnable: Whether scenario can be executed
            - model_json_keys: List of config keys in model_json (for debugging)
        """
        logger.info(f"Getting scenario requirements: {scenario_id}")
        scenario = await Scenarios.get_scenario(client, scenario_id)

        platforms_dict = scenario.get("supported_platforms") or {}
        platform_list = list(platforms_dict.keys())

        return {
            "scenario_id": scenario_id,
            "name": scenario.get("name", ""),
            "supported_platforms": platform_list,
            "is_multi_asset": scenario.get("is_multi_asset", False),
            "runnable": scenario.get("runnable", True),
            "model_json_keys": list((scenario.get("model_json") or {}).keys()),
        }

    @staticmethod
    async def analyze_scenario_requirements(client: AttackIQClient, scenario_ids: List[str]) -> Dict[str, Any]:
        """Bulk analyze scenarios to determine requirements.

        Returns:
            dict with:
            - scenarios: List of scenario requirements
            - by_platform: Scenarios grouped by required platform
            - multi_asset: List of multi-asset scenarios (excluded from simple workflows)
            - scenarios_need_configuration: Scenarios that need setup (look at SCENARIO)
            - summary: Counts and quick stats
        """
        logger.info(f"Analyzing requirements for {len(scenario_ids)} scenarios")
        results = []
        by_platform: Dict[str, List[str]] = {}
        multi_asset = []
        scenarios_need_configuration = []
        errors = []

        for sid in scenario_ids:
            try:
                req = await Scenarios.get_scenario_requirements(client, sid)
                results.append(req)

                if req["is_multi_asset"]:
                    multi_asset.append({"id": sid, "name": req["name"]})

                if not req["runnable"]:
                    scenarios_need_configuration.append(
                        {
                            "id": sid,
                            "name": req["name"],
                            "reason": "Scenario is not runnable (needs configuration)",
                        }
                    )

                # Empty supported_platforms means "all platforms" - add to universal bucket
                platforms = req["supported_platforms"]
                if not platforms:
                    by_platform.setdefault("universal", []).append(sid)
                else:
                    for platform in platforms:
                        by_platform.setdefault(platform, []).append(sid)

            except Exception as e:
                logger.warning(f"Error analyzing scenario {sid}: {e}")
                errors.append({"id": sid, "error": str(e)})

        return {
            "scenarios": results,
            "by_platform": by_platform,
            "multi_asset": multi_asset,
            "scenarios_need_configuration": scenarios_need_configuration,
            "errors": errors,
            "summary": {
                "total": len(scenario_ids),
                "analyzed": len(results),
                "multi_asset_count": len(multi_asset),
                "need_configuration_count": len(scenarios_need_configuration),
                "error_count": len(errors),
                "platforms": list(by_platform.keys()),
            },
        }

    @staticmethod
    async def update_scenario(
        client: AttackIQClient,
        scenario_id: str,
        data: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Update a scenario by its ID."""
        endpoint = f"{Scenarios.ENDPOINT}/{scenario_id}"
        logger.info(f"Updating scenario {scenario_id} with data: {data}")
        return await client.patch_object(endpoint, data)

    @staticmethod
    async def save_copy(client: AttackIQClient, scenario_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a copy of an existing scenario."""
        endpoint = f"{Scenarios.ENDPOINT}/{scenario_id}/save_copy"
        logger.info(f"Creating copy of scenario {scenario_id} with data: {data}")
        return await client.post_object(endpoint, data=data)

    @staticmethod
    async def delete_scenario(client: AttackIQClient, scenario_id: str) -> bool:
        """Delete a specific scenario by its ID."""
        endpoint = f"{Scenarios.ENDPOINT}/{scenario_id}"
        logger.info(f"Deleting scenario: {scenario_id}")
        response = await client.delete_object(endpoint)
        if response is not None and 200 <= response["status_code"] < 300:
            logger.info(f"Successfully deleted scenario: {scenario_id}")
            return True
        logger.error(f"Failed to delete scenario: {scenario_id}")
        return False

    @staticmethod
    async def search_scenarios(
        client: AttackIQClient,
        query: Optional[str] = None,
        limit: Optional[int] = 20,
        offset: Optional[int] = 0,
        ordering: Optional[str] = "-modified",
    ) -> dict:
        """Search or list scenarios.
        - With query: Search by keyword, MITRE technique ID, or tag
        - Without query: List all scenarios (paginated)
        Returns {"count": total, "results": [...]}

        Args:
            ordering: Sort order (default: -modified for most recent first)
                     Use '-' prefix for descending (e.g., '-modified', '-created')
                     Omit '-' for ascending (e.g., 'modified', 'created', 'name')
        """
        logger.info(
            f"Searching scenarios with query: '{query}', limit: {limit}, offset: {offset}, ordering: {ordering}"
        )
        params = {"minimal": "true", "limit": limit, "offset": offset}
        if query:
            params["search"] = query
        if "ordering" not in params and ordering:
            params["ordering"] = ordering
        url = client._build_url(Scenarios.ENDPOINT, params)
        data = await client._make_request(url, method="get", json=None)
        total_count = data.get("count", 0)
        results = data.get("results", [])
        logger.info(f"Found {total_count} total scenarios matching '{query}', returning {len(results)}")
        return {"count": total_count, "results": results}

    @staticmethod
    async def list_scenarios_by_tag(
        client: AttackIQClient,
        tag_id: str,
        limit: Optional[int] = 20,
        offset: Optional[int] = 0,
        ordering: Optional[str] = "-modified",
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {"minimal": "true", "limit": limit, "offset": offset, "tag": tag_id}
        if ordering:
            params["ordering"] = ordering
        logger.info(f"Listing scenarios by tag {tag_id} with params: {params}")
        url = client._build_url(Scenarios.ENDPOINT, params)
        data = await client._make_request(url, method="get", json=None)
        response = {"count": data["count"], "results": data["results"]}
        if "detail" in data:
            response["detail"] = data["detail"]
        return response

    @staticmethod
    async def search_scenarios_by_tag(
        client: AttackIQClient,
        tag_query: str,
        limit: Optional[int] = 20,
        offset: Optional[int] = 0,
        ordering: Optional[str] = "-modified",
    ) -> Dict[str, Any]:
        query = tag_query
        normalized_detail = None
        if "." in tag_query:
            normalized = tag_query.replace(".", "")
            normalized_detail = f"Normalized MITRE ID {tag_query} -> {normalized} due to platform storage format"
            query = normalized

        logger.info(f"Searching scenarios for tag query '{query}'")
        tag_search = await Tags.search_tags(client, search=query, limit=limit, offset=0)
        tags = tag_search["results"]
        detail = tag_search.get("detail")
        if not detail and normalized_detail:
            detail = normalized_detail

        scenarios = []
        seen_ids = set()
        for tag in tags:
            tag_id = tag["id"]
            tag_scenarios = await Scenarios.list_scenarios_by_tag(
                client, tag_id, limit=limit + offset, offset=0, ordering=ordering
            )
            for scenario in tag_scenarios["results"]:
                sid = scenario["id"]
                if sid not in seen_ids:
                    seen_ids.add(sid)
                    scenarios.append(scenario)

        scenarios = scenarios[offset : offset + limit]

        response = {"count": len(seen_ids), "tags": tags, "scenarios": scenarios}
        if detail:
            response["detail"] = detail
        return response

    @staticmethod
    async def search_scenarios_by_mitre(
        client: AttackIQClient,
        technique_id: str,
        limit: Optional[int] = 20,
        offset: Optional[int] = 0,
        ordering: Optional[str] = "-modified",
    ) -> Dict[str, Any]:
        logger.info(f"search_scenarios_by_mitre is an alias for search_scenarios_by_tag with query '{technique_id}'")
        return await Scenarios.search_scenarios_by_tag(
            client=client,
            tag_query=technique_id,
            limit=limit,
            offset=offset,
            ordering=ordering,
        )

    @staticmethod
    async def get_scenario_details(client: AttackIQClient, scenario_id: str) -> Optional[Dict[str, Any]]:
        """Get complete details for a specific scenario."""
        return await Scenarios.get_scenario(client, scenario_id)

    @staticmethod
    def validate_zip_payload(zip_path: str, password: str) -> bool:
        """Validate ZIP password using testzip() - no full extraction.

        Security: Uses in-memory validation, no disk writes.
        Returns: True if password valid and ZIP intact, False otherwise.
        """
        import pyzipper

        try:
            with pyzipper.AESZipFile(zip_path, "r") as zf:
                zf.setpassword(password.encode())
                # testzip() returns None if OK, filename of first bad file otherwise
                return zf.testzip() is None
        except (RuntimeError, pyzipper.BadZipFile):
            return False

    @staticmethod
    def _validate_download_to_memory_model(model_json: Dict[str, Any]) -> None:
        target_system = model_json.get("target_system")
        if target_system != "provided_protected_zip_file":
            raise ValueError(
                f"Unsupported target_system '{target_system}'. This SDK only supports 'provided_protected_zip_file'"
            )

        sha256_hash = model_json.get("sha256_hash")
        missing_fields = []
        if not sha256_hash:
            missing_fields.append("sha256_hash")
        if not model_json.get("zip_file"):
            missing_fields.append("zip_file")
        if not model_json.get("zip_file_password"):
            missing_fields.append("zip_file_password")

        if missing_fields:
            missing = ", ".join(missing_fields)
            raise ValueError(f"Missing required fields for download-to-memory scenario: {missing}")

    @staticmethod
    def build_download_to_memory_model_json(
        base_model_json: Dict[str, Any],
        *,
        zip_file: str,
        zip_file_password: str,
        sha256_hash: str,
        download_method: Optional[str] = None,
        check_if_executable: Optional[bool] = None,
        http_proxy_conf: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build a validated model_json payload for Download File to Memory scenarios.
        """
        model_json = copy.deepcopy(base_model_json) if base_model_json else {}

        model_json["target_system"] = "provided_protected_zip_file"
        model_json["zip_file"] = zip_file
        model_json["zip_file_password"] = zip_file_password
        model_json["sha256_hash"] = sha256_hash

        if download_method is not None:
            model_json["download_method"] = download_method
        if check_if_executable is not None:
            model_json["check_if_executable"] = check_if_executable
        if http_proxy_conf is not None:
            model_json["http_proxy_conf"] = http_proxy_conf

        Scenarios._validate_download_to_memory_model(model_json)
        return model_json

    @staticmethod
    def _merge_value(provided: Optional[Any], existing: Optional[Any]) -> Optional[Any]:
        return existing if provided is None else provided

    @staticmethod
    def _build_description_payload(
        summary: Optional[str],
        existing_description: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        # Early return for no-op case
        if not summary:
            return None
        # Merge: preserve existing fields, update summary only
        base = existing_description.copy() if existing_description else {}
        base["summary"] = summary
        return {"description_json": base}

    @staticmethod
    async def create_download_to_memory_scenario(
        client: AttackIQClient,
        name: str,
        *,
        zip_file: str,
        zip_file_password: str,
        sha256_hash: str,
        download_method: str = "python_requests",
        check_if_executable: bool = False,
        http_proxy_conf: str = "no_proxy",
        fork_template: bool = False,
        summary: Optional[str] = None,
        extras: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a Download File to Memory scenario from its template."""
        template_id = SCENARIO_TEMPLATE_IDS[ScenarioTemplateType.DOWNLOAD_TO_MEMORY]
        logger.info(f"Creating Download File to Memory scenario '{name}' from template {template_id}")
        template = await Scenarios.get_scenario(client, template_id)
        if not template:
            raise ValueError(
                f"Template scenario {template_id} not found. "
                f"Ensure the Download File to Memory template is installed on the platform."
            )

        model_json = Scenarios.build_download_to_memory_model_json(
            base_model_json=template.get("model_json") or {},
            zip_file=zip_file,
            zip_file_password=zip_file_password,
            sha256_hash=sha256_hash,
            download_method=download_method,
            check_if_executable=check_if_executable,
            http_proxy_conf=http_proxy_conf,
        )

        created = await Scenarios.save_copy(
            client,
            template_id,
            {
                "name": name,
                "model_json": model_json,
                "fork_template": fork_template,
            },
        )
        if not created:
            raise ValueError("Failed to create download-to-memory scenario")

        patch_payload: Dict[str, Any] = {}
        description_payload = Scenarios._build_description_payload(summary, template.get("description_json"))
        if description_payload:
            patch_payload.update(description_payload)
        if extras:
            patch_payload["extras"] = extras
        if patch_payload:
            logger.info(f"Patching created scenario {created['id']} with description/extras")
            await Scenarios.update_scenario(client, created["id"], patch_payload)

        return created

    @staticmethod
    async def update_download_to_memory_scenario(
        client: AttackIQClient,
        scenario_id: str,
        *,
        zip_file: Optional[str] = None,
        zip_file_password: Optional[str] = None,
        sha256_hash: Optional[str] = None,
        download_method: Optional[str] = None,
        check_if_executable: Optional[bool] = None,
        http_proxy_conf: Optional[str] = None,
        summary: Optional[str] = None,
        extras: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Update an existing Download File to Memory scenario."""
        scenario = await Scenarios.get_scenario(client, scenario_id)
        if not scenario:
            raise ValueError(f"Scenario not found: {scenario_id}")

        existing_model = scenario.get("model_json") or {}
        model_json = Scenarios.build_download_to_memory_model_json(
            base_model_json=existing_model,
            zip_file=Scenarios._merge_value(zip_file, existing_model.get("zip_file")),
            zip_file_password=Scenarios._merge_value(zip_file_password, existing_model.get("zip_file_password")),
            sha256_hash=Scenarios._merge_value(sha256_hash, existing_model.get("sha256_hash")),
            download_method=Scenarios._merge_value(download_method, existing_model.get("download_method")),
            check_if_executable=Scenarios._merge_value(check_if_executable, existing_model.get("check_if_executable")),
            http_proxy_conf=Scenarios._merge_value(http_proxy_conf, existing_model.get("http_proxy_conf")),
        )

        payload: Dict[str, Any] = {"model_json": model_json}
        description_payload = Scenarios._build_description_payload(summary, scenario.get("description_json"))
        if description_payload:
            payload.update(description_payload)
        if extras:
            payload["extras"] = extras

        if not payload:
            raise ValueError("No updates specified for scenario")

        logger.info(f"Updating Download File to Memory scenario {scenario_id}")
        updated = await Scenarios.update_scenario(client, scenario_id, payload)
        return updated or await Scenarios.get_scenario(client, scenario_id)

    @staticmethod
    def _extract_native_api_whitelist(template: Dict[str, Any]) -> List[str]:
        """Extract the supported API whitelist from the template's descriptor_json."""
        descriptor = (template.get("scenario_template") or {}).get("descriptor_json")
        if not descriptor:
            template_id = SCENARIO_TEMPLATE_IDS[ScenarioTemplateType.NATIVE_API]
            raise ValueError(f"Could not find descriptor_json in template {template_id}")

        def find_apis_api_title_map(obj):
            if isinstance(obj, dict):
                if obj.get("key") == "apis[].api" and "titleMap" in obj:
                    return obj["titleMap"]
                for v in obj.values():
                    res = find_apis_api_title_map(v)
                    if res:
                        return res
            elif isinstance(obj, list):
                for v in obj:
                    res = find_apis_api_title_map(v)
                    if res:
                        return res
            return None

        title_map = find_apis_api_title_map(descriptor)
        if title_map:
            return [m["value"] for m in title_map if "value" in m]

        template_id = SCENARIO_TEMPLATE_IDS[ScenarioTemplateType.NATIVE_API]
        raise ValueError(f"Could not find API whitelist in descriptor_json of template {template_id}")

    @staticmethod
    def _validate_native_api_model(model_json: Dict[str, Any], whitelist: List[str]) -> None:
        apis = model_json.get("apis")
        if not apis or not isinstance(apis, list):
            raise ValueError("apis list is required for native_api scenarios")
        for idx, api in enumerate(apis):
            if not isinstance(api, dict):
                raise ValueError(f"apis[{idx}] must be an object")
            api_name = api.get("api")
            if not api_name:
                raise ValueError(f"apis[{idx}]['api'] is required")
            if api_name not in whitelist:
                suggestions = [v for v in whitelist if api_name.lower() in v.lower() or v.lower() in api_name.lower()]
                msg = f"Invalid API Identifier '{api_name}'."
                if suggestions:
                    msg += f" Did you mean one of: {', '.join(suggestions[:3])}?"
                else:
                    template_id = SCENARIO_TEMPLATE_IDS[ScenarioTemplateType.NATIVE_API]
                    msg += f" Must be one of the supported Native APIs. See descriptor_json of template {template_id} for full list."
                raise ValueError(msg)

    @staticmethod
    def build_native_api_model_json(
        base_model_json: Dict[str, Any],
        *,
        apis: List[Dict[str, Any]],
        whitelist: List[str],
    ) -> Dict[str, Any]:
        """Build validated model_json for Native API scenarios."""
        model_json = copy.deepcopy(base_model_json) if base_model_json else {}
        model_json["apis"] = apis
        Scenarios._validate_native_api_model(model_json, whitelist=whitelist)
        return model_json

    @staticmethod
    async def create_native_api_scenario(
        client: AttackIQClient,
        name: str,
        *,
        apis: List[Dict[str, Any]],
        fork_template: bool = False,
        summary: Optional[str] = None,
        extras: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        template_id = SCENARIO_TEMPLATE_IDS[ScenarioTemplateType.NATIVE_API]
        logger.info(f"Creating Native API scenario '{name}' from template {template_id}")
        template = await Scenarios.get_scenario(client, template_id)
        if not template:
            raise ValueError(
                f"Template scenario {template_id} not found. "
                f"Ensure the Native API template is installed on the platform."
            )

        whitelist = Scenarios._extract_native_api_whitelist(template)
        model_json = Scenarios.build_native_api_model_json(
            base_model_json=template.get("model_json") or {},
            apis=apis,
            whitelist=whitelist,
        )

        created = await Scenarios.save_copy(
            client,
            template_id,
            {
                "name": name,
                "model_json": model_json,
                "fork_template": fork_template,
            },
        )
        if not created:
            raise ValueError("Failed to create native_api scenario")

        patch_payload: Dict[str, Any] = {}
        description_payload = Scenarios._build_description_payload(summary, template.get("description_json"))
        if description_payload:
            patch_payload.update(description_payload)
        if extras:
            patch_payload["extras"] = extras
        if patch_payload:
            logger.info(f"Patching created scenario {created['id']} with description/extras")
            await Scenarios.update_scenario(client, created["id"], patch_payload)

        return created

    @staticmethod
    async def update_native_api_scenario(
        client: AttackIQClient,
        scenario_id: str,
        *,
        apis: Optional[List[Dict[str, Any]]] = None,
        summary: Optional[str] = None,
        extras: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        scenario = await Scenarios.get_scenario(client, scenario_id)
        if not scenario:
            raise ValueError(f"Scenario not found: {scenario_id}")

        template_id = SCENARIO_TEMPLATE_IDS[ScenarioTemplateType.NATIVE_API]
        template = await Scenarios.get_scenario(client, template_id)
        if not template:
            raise ValueError(f"Native API template not found: {template_id}")
        whitelist = Scenarios._extract_native_api_whitelist(template)

        existing_model = scenario.get("model_json") or {}
        model_json = Scenarios.build_native_api_model_json(
            base_model_json=existing_model,
            apis=apis if apis is not None else existing_model.get("apis") or [],
            whitelist=whitelist,
        )

        payload: Dict[str, Any] = {"model_json": model_json}
        description_payload = Scenarios._build_description_payload(summary, scenario.get("description_json"))
        if description_payload:
            payload.update(description_payload)
        if extras:
            payload["extras"] = extras
        if not payload:
            raise ValueError("No updates specified for scenario")

        logger.info(f"Updating Native API scenario {scenario_id}")
        updated = await Scenarios.update_scenario(client, scenario_id, payload)
        return updated or await Scenarios.get_scenario(client, scenario_id)

    @staticmethod
    async def list_native_apis(client: AttackIQClient) -> List[str]:
        """Return the full list of supported Native API identifiers from the platform."""
        template_id = SCENARIO_TEMPLATE_IDS[ScenarioTemplateType.NATIVE_API]
        template = await Scenarios.get_scenario(client, template_id)
        return Scenarios._extract_native_api_whitelist(template)

    @staticmethod
    async def validate_and_filter_native_apis(client: AttackIQClient, apis: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate a list of Native APIs against the platform whitelist.
        Returns a dict with 'valid' APIs, 'invalid' APIs, 'skipped' entries, and 'suggestions'.
        """
        whitelist = await Scenarios.list_native_apis(client)
        results = {"valid": [], "invalid": [], "skipped": [], "suggestions": {}}

        for idx, api in enumerate(apis):
            if not isinstance(api, dict):
                results["skipped"].append({"index": idx, "reason": "entry is not an object", "data": api})
                continue

            name = api.get("api")
            if not name:
                results["skipped"].append({"index": idx, "reason": "missing 'api' key", "data": api})
                continue

            if name in whitelist:
                results["valid"].append(api)
            else:
                results["invalid"].append(name)
                suggestions = [v for v in whitelist if name.lower() in v.lower() or v.lower() in name.lower()]
                if suggestions:
                    results["suggestions"][name] = suggestions[:3]

        return results
