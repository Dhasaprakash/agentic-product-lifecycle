#!/usr/bin/env python3
"""
Verify Acceptance Criteria in Azure DevOps User Stories
Check that acceptance criteria are properly captured in the work items
"""

import os
import sys
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

def verify_acceptance_criteria():
    """Verify that acceptance criteria are properly captured in User Stories."""
    print("🔍 VERIFYING ACCEPTANCE CRITERIA IN AZURE DEVOPS USER STORIES")
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
        
        # Test User Story IDs from the latest test run
        test_story_ids = ["64", "65", "66", "67", "68"]
        
        print(f"📋 Checking {len(test_story_ids)} User Stories for Acceptance Criteria...\n")
        
        for story_id in test_story_ids:
            print(f"📝 User Story {story_id}:")
            
            try:
                # Get the work item details
                story_data = ado_client.get_work_item(story_id)
                
                if story_data:
                    print(f"   Title: {story_data.get('title', 'N/A')}")
                    print(f"   Status: {story_data.get('status', 'N/A')}")
                    print(f"   Type: {story_data.get('work_item_type', 'N/A')}")
                    
                    # Check for acceptance criteria in different possible fields
                    ac_fields = [
                        "Microsoft.VSTS.Common.AcceptanceCriteria",
                        "System.Description",
                        "Microsoft.VSTS.Common.AcceptanceCriteria"
                    ]
                    
                    ac_found = False
                    for field_name in ac_fields:
                        field_value = story_data.get('fields', {}).get(field_name, '')
                        if field_value and "Acceptance Criteria:" in str(field_value):
                            print(f"   ✅ Acceptance Criteria found in field: {field_name}")
                            print(f"   📋 Content preview:")
                            ac_content = str(field_value)
                            # Show first 200 characters
                            preview = ac_content[:200] + "..." if len(ac_content) > 200 else ac_content
                            print(f"      {preview}")
                            ac_found = True
                            break
                    
                    if not ac_found:
                        print(f"   ❌ No acceptance criteria found in expected fields")
                        print(f"   🔍 Available fields:")
                        available_fields = story_data.get('fields', {})
                        for field, value in available_fields.items():
                            if value and len(str(value)) > 10:  # Only show non-empty fields
                                print(f"      {field}: {str(value)[:100]}...")
                    
                    # Check for parent relationship
                    parent_id = story_data.get('fields', {}).get('System.Parent', '')
                    if parent_id:
                        print(f"   🔗 Parent: {parent_id}")
                    else:
                        print(f"   ⚠️  No parent field found")
                    
                    # Check for relations
                    relations = story_data.get('relations', [])
                    if relations:
                        print(f"   🔗 Relations found: {len(relations)}")
                        for relation in relations:
                            rel_type = relation.get('rel', 'Unknown')
                            rel_url = relation.get('url', '')
                            print(f"      {rel_type}: {rel_url}")
                    else:
                        print(f"   ⚠️  No relations found")
                    
                else:
                    print(f"   ❌ Could not retrieve User Story {story_id}")
                
                print("-" * 50)
                
            except Exception as e:
                print(f"   ❌ Error retrieving User Story {story_id}: {str(e)}")
                print("-" * 50)
        
        print("\n🎯 VERIFICATION COMPLETE")
        print("="*70)
        
        # Summary
        print("📊 Summary:")
        print("   - Checked User Stories: 64, 65, 66, 67, 68")
        print("   - Expected: Acceptance criteria in Microsoft.VSTS.Common.AcceptanceCriteria field")
        print("   - Expected: Proper parent-child relationships via relations")
        print("\n💡 If acceptance criteria are not visible:")
        print("   1. Check the Azure DevOps work item directly")
        print("   2. Verify the field name exists in your project template")
        print("   3. Check if the field is visible in the work item form")
        
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = verify_acceptance_criteria()
    sys.exit(0 if success else 1)
