#!/usr/bin/env python3
"""Test script to fetch destinations from Gateway API"""

import os
import sys
import json

# Add parent directory to path to import from app
sys.path.insert(0, os.path.dirname(__file__))

from app import GatewayAPIClient

def test_destinations():
    # You'll need to provide these
    gateway_token = input("Enter your Gateway Token: ").strip()
    workspace_slug = input("Enter workspace slug (e.g., 'axios'): ").strip()

    print(f"\n🔍 Fetching destinations for workspace: {workspace_slug}\n")

    client = GatewayAPIClient(gateway_token, workspace_slug)

    try:
        result = client.get_all_destinations()
        destinations = result.get('destinations', [])
        spaces = result.get('spaces', [])

        print(f"✅ Found {len(destinations)} destinations")
        print(f"✅ Found {len(spaces)} spaces\n")

        # Count by type
        integrations = [d for d in destinations if d.get('__typename') == 'Integration']
        warehouses = [d for d in destinations if d.get('__typename') == 'Warehouse']

        print(f"📊 Breakdown:")
        print(f"  - Integrations: {len(integrations)}")
        print(f"  - Warehouses: {len(warehouses)}\n")

        # Show sample destinations
        print("📋 Sample Destinations:")
        for i, dest in enumerate(destinations[:5], 1):
            dtype = dest.get('__typename')
            name = dest.get('name', 'Unknown')
            enabled = dest.get('enabled', False)
            status = dest.get('integrationStatus') or dest.get('warehouseStatus')
            created = dest.get('createdAt', '')

            print(f"\n{i}. {name}")
            print(f"   Type: {dtype}")
            print(f"   Enabled: {enabled}")
            print(f"   Status: {status}")
            print(f"   Created: {created}")

            if dtype == 'Integration':
                source = dest.get('source', {})
                if source:
                    print(f"   Connected Source: {source.get('name', 'N/A')}")

        # Save full output
        output_file = 'destinations_test_output.json'
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n💾 Full output saved to: {output_file}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_destinations()
