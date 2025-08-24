#!/usr/bin/env python3
"""
Debug Azure DevOps Work Item Fields
Comprehensive examination of all available fields and data
"""

import os
import sys
import json
from services.ado_client import AzureDevOpsClient

def load_config_from_file(config_file: str = "test_config.env"):
    """Load configuration from environment file."""
    config = {}
    
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key] = value
    
    return config

def debug_work_item_fields():
    """Debug all available fields and data in Azure DevOps work items."""
    print("🔍 DEBUGGING AZURE DEVOPS WORK ITEM FIELDS")
    print("="*70)
    
    try:
        # Load configuration
        config = load_config_from_file()
        
        # Initialize Azure DevOps client
        ado_client = AzureDevOpsClient(
            organization=config["ADO_ORGANIZATION"],
            project=config["ADO_PROJECT"],
            personal_access_token=config["ADO_PAT"]
        )
        
        # Test work item IDs from the latest test run
        test_ids = {
            "Epic": "62",
            "Feature": "63", 
            "User Story 1": "64",
            "User Story 2": "65",
            "User Story 3": "66"
        }
        
        print(f"📋 Examining {len(test_ids)} work items for field structure...\n")
        
        for work_item_type, work_item_id in test_ids.items():
            print(f"🏷️  {work_item_type} (ID: {work_item_id}):")
            
            try:
                # Get the work item details with all fields
                work_item_data = ado_client.get_work_item(work_item_id)
                
                if work_item_data:
                    print(f"   Title: {work_item_data.get('title', 'N/A')}")
                    print(f"   Status: {work_item_data.get('status', 'N/A')}")
                    print(f"   Type: {work_item_data.get('work_item_type', 'N/A')}")
                    print(f"   ID: {work_item_data.get('id', 'N/A')}")
                    
                    # Examine all available fields
                    fields = work_item_data.get('fields', {})
                    print(f"   📊 Total fields available: {len(fields)}")
                    
                    if fields:
                        print(f"   🔍 Field details:")
                        for field_name, field_value in fields.items():
                            if field_value is not None:
                                field_str = str(field_value)
                                if len(field_str) > 100:
                                    field_str = field_str[:100] + "..."
                                print(f"      {field_name}: {field_str}")
                    
                    # Check for relations
                    relations = work_item_data.get('relations', [])
                    if relations is not None:
                        print(f"   🔗 Relations: {len(relations)} found")
                        if relations:
                            for i, relation in enumerate(relations):
                                print(f"      Relation {i+1}:")
                                for key, value in relation.items():
                                    print(f"        {key}: {value}")
                    else:
                        print(f"   🔗 Relations: None (not available)")
                    
                    # Check for links
                    links = work_item_data.get('_links', {})
                    if links is not None:
                        print(f"   🔗 Links: {len(links)} found")
                        if links:
                            for link_name, link_data in links.items():
                                print(f"      {link_name}: {link_data.get('href', 'N/A')}")
                    else:
                        print(f"   🔗 Links: None (not available)")
                    
                    # Check for specific important fields
                    important_fields = [
                        "System.Title",
                        "System.Description", 
                        "System.State",
                        "System.WorkItemType",
                        "System.Parent",
                        "Microsoft.VSTS.Common.AcceptanceCriteria",
                        "Microsoft.VSTS.Common.BusinessValue",
                        "Microsoft.VSTS.Common.Priority",
                        "Microsoft.VSTS.Common.StoryPoints"
                    ]
                    
                    print(f"   🎯 Important fields check:")
                    for field_name in important_fields:
                        field_value = fields.get(field_name, 'NOT_FOUND')
                        if field_value != 'NOT_FOUND':
                            print(f"      ✅ {field_name}: {str(field_value)[:100]}")
                        else:
                            print(f"      ❌ {field_name}: Not available")
                    
                else:
                    print(f"   ❌ Could not retrieve work item {work_item_id}")
                
                print("-" * 70)
                
            except Exception as e:
                print(f"   ❌ Error examining {work_item_type} {work_item_id}: {str(e)}")
                print("-" * 70)
        
        print("\n🎯 FIELD ANALYSIS COMPLETE")
        print("="*70)
        
        # Recommendations
        print("💡 Recommendations:")
        print("   1. Check if 'Microsoft.VSTS.Common.AcceptanceCriteria' field exists in your project")
        print("   2. Verify the exact field names in Azure DevOps Project Settings")
        print("   3. Check if relations are being created but not retrieved properly")
        print("   4. Consider using 'System.Description' as fallback for acceptance criteria")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = debug_work_item_fields()
    sys.exit(0 if success else 1)
