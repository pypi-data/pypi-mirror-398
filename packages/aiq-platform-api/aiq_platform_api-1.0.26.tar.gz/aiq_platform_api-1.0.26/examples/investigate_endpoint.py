#!/usr/bin/env python3
"""
ENDPOINT INVESTIGATION TOOL

Discover what any AttackIQ API endpoint returns and whether it supports minimal fields.

USAGE:
1. Edit ENDPOINT below (line 27)
2. Run: poetry run python examples/investigate_endpoint.py
3. Review output to decide minimal strategy

DECISION CRITERIA:
- Field reduction >50% → Use minimal=true by default
- Field reduction <50% → Skip minimal, just add offset
"""
import asyncio
import json
import sys

from aiq_platform_api import AttackIQClient, ATTACKIQ_PLATFORM_URL, ATTACKIQ_PLATFORM_API_TOKEN

# =============================================================================
# CONFIGURATION: Change this for different endpoints
# =============================================================================
ENDPOINT = "v1/assets"  # Examples: v1/scenarios, v1/assets, v1/assessments


# =============================================================================


async def fetch_endpoint_data(client: AttackIQClient, endpoint: str, use_minimal: bool):
    """Fetch single item from endpoint with or without minimal parameter."""
    params = {"limit": 1}
    if use_minimal:
        params["minimal"] = "true"

    data = await client.get_object(endpoint, params=params)

    if isinstance(data, dict) and "results" in data:
        return data["results"][0] if data["results"] else None
    if isinstance(data, list):
        return data[0] if data else None
    return data


async def test_search_support(client: AttackIQClient, endpoint: str):
    """Test if endpoint supports search parameter."""
    params = {"search": "test", "limit": 3}

    try:
        data = await client.get_object(endpoint, params=params)

        if isinstance(data, dict) and "results" in data:
            return True, len(data["results"])
        if isinstance(data, list):
            return True, len(data)
        return True, 0
    except Exception as e:
        return False, str(e)


async def test_ordering_support(client: AttackIQClient, endpoint: str):
    """Test if endpoint supports ordering parameter."""
    params = {"minimal": "true", "limit": 3, "ordering": "-modified"}

    try:
        data = await client.get_object(endpoint, params=params)

        if isinstance(data, dict) and "results" in data:
            return True, len(data["results"])
        if isinstance(data, list):
            return True, len(data)
        return True, 0
    except Exception as e:
        return False, str(e)


def display_item_summary(item, label):
    """Display summary of item fields and size."""
    print(f"\n{label}")
    print(f"Item ID: {item.get('id')}")
    print(f"Item Name: {item.get('name')}")
    print(f"\nTotal fields: {len(item.keys())}")


def display_field_list(fields):
    """Display sorted list of field names."""
    print("\nField names:")
    for idx, key in enumerate(sorted(fields), 1):
        print(f"  {idx:2d}. {key}")


def display_item_json(item, max_chars):
    """Display JSON representation of item, truncated if needed."""
    full_json = json.dumps(item, indent=2)
    data_size = len(full_json)

    print(f"\nData size: {data_size:,} bytes ({data_size / 1024:.1f} KB)")

    if data_size <= max_chars:
        print("\nFull object:")
        print(full_json)
    else:
        print(f"\nSample (first {max_chars} chars):")
        print(full_json[:max_chars])
        print(f"... (truncated, full size: {data_size:,} bytes)")


def calculate_reduction_percentage(original, reduced):
    """Calculate percentage reduction."""
    if original == 0:
        return 0
    return ((original - reduced) / original) * 100


def display_comparison(default_fields, minimal_fields):
    """Display field comparison and recommendation."""
    default_count = len(default_fields)
    minimal_count = len(minimal_fields)
    reduction_pct = calculate_reduction_percentage(default_count, minimal_count)

    print("\n📊 COMPARISON:")
    print(f"  Default fields: {default_count}")
    print(f"  Minimal fields: {minimal_count}")
    print(f"  Reduction: {default_count - minimal_count} fields ({reduction_pct:.1f}%)")

    only_in_default = set(default_fields) - set(minimal_fields)
    if only_in_default:
        print("\n🔍 FIELDS REMOVED BY MINIMAL:")
        for field in sorted(only_in_default):
            print(f"  - {field}")

    print("\n✓ FIELDS KEPT BY MINIMAL:")
    for field in sorted(minimal_fields):
        print(f"  - {field}")

    print("\n" + "=" * 80)
    print("💡 RECOMMENDATION")
    print("=" * 80)

    if reduction_pct >= 50:
        print("✅ USE minimal=true BY DEFAULT")
        print(f"   Reason: {reduction_pct:.1f}% field reduction (≥50% threshold)")
        print("\n   Implementation:")
        print(f'   request_params = params.copy() if params else {"{}"} ')
        print('   request_params["minimal"] = "true"')
    elif reduction_pct > 0:
        print("⚠️  MINIMAL SUPPORTED BUT LOW IMPACT")
        print(f"   Reason: Only {reduction_pct:.1f}% reduction (<50%)")
        print("   Decision: Skip minimal, just add offset")
    else:
        print("❌ NO REDUCTION")
        print("   Action: Skip minimal, just add offset")


async def run_investigation(client: AttackIQClient, endpoint: str):
    """Run complete endpoint investigation."""
    print("=" * 80)
    print(f"INVESTIGATING: {endpoint}")
    print("=" * 80)

    print("\nTEST 1: Fetch with DEFAULT params (no minimal)")
    print("-" * 80)
    default_item = await fetch_endpoint_data(client, endpoint, use_minimal=False)

    if not default_item:
        print("✗ No data returned from endpoint")
        sys.exit(1)

    display_item_summary(default_item, "✓ Successfully fetched")
    default_fields = list(default_item.keys())
    display_field_list(default_fields)
    display_item_json(default_item, max_chars=2000)

    print("\n" + "=" * 80)
    print("TEST 2: Fetch with minimal=true")
    print("-" * 80)
    minimal_item = await fetch_endpoint_data(client, endpoint, use_minimal=True)

    if not minimal_item:
        print("✗ Endpoint does not support minimal=true")
        print("   Action: Skip minimal, just add offset pagination")
        sys.exit(0)

    display_item_summary(minimal_item, "✓ Successfully fetched with minimal")
    minimal_fields = list(minimal_item.keys())
    display_field_list(minimal_fields)
    display_item_json(minimal_item, max_chars=5000)

    print("\n" + "=" * 80)
    print("TEST 3: Check if search parameter is supported")
    print("-" * 80)
    search_supported, search_result = await test_search_support(client, endpoint)

    if search_supported:
        print("✅ SEARCH SUPPORTED")
        print(f"   Test query 'search=test' returned {search_result} items")
        print("   Can implement search_* methods for this endpoint")
    else:
        print("❌ SEARCH NOT SUPPORTED")
        print(f"   Error: {search_result}")
        print("   Skip search methods, only implement list methods")

    print("\n" + "=" * 80)
    print("TEST 4: Check if ordering parameter is supported")
    print("-" * 80)
    ordering_supported, ordering_result = await test_ordering_support(client, endpoint)

    if ordering_supported:
        print("✅ ORDERING SUPPORTED")
        print(f"   Test query 'ordering=-modified' returned {ordering_result} items")
        print("   Recommend default: ordering=-modified (most recent first)")
    else:
        print("❌ ORDERING NOT SUPPORTED")
        print(f"   Error: {ordering_result}")
        print("   Results will be in database order")

    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    display_comparison(default_fields, minimal_fields)

    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print("1. Review recommendation above")
    print("2. See: ADDING_PAGINATION_AND_MINIMAL_SUPPORT.md")
    print("=" * 80)


async def main():
    if not ATTACKIQ_PLATFORM_URL or not ATTACKIQ_PLATFORM_API_TOKEN:
        print("ERROR: Missing credentials in environment")
        sys.exit(1)

    async with AttackIQClient(ATTACKIQ_PLATFORM_URL, ATTACKIQ_PLATFORM_API_TOKEN) as client:
        await run_investigation(client, ENDPOINT)


if __name__ == "__main__":
    asyncio.run(main())
