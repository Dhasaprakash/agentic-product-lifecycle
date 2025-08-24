#!/usr/bin/env python3
"""
Validate Work Items in Azure DevOps Project
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.ado_client import AzureDevOpsClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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


async def validate_work_items():
    """Validate what work items exist in the Azure DevOps project."""
    print("\n" + "="*70)
    print("VALIDATING WORK ITEMS IN AZURE DEVOPS PROJECT")
    print("="*70)
    
    try:
        # Load configuration
        config = load_config_from_file()
        
        print(f"Organization: {config.get('ADO_ORGANIZATION', 'Not set')}")
        print(f"Project: {config.get('ADO_PROJECT', 'Not set')}")
        print(f"PAT: {'*' * 20}...")
        
        # Initialize Azure DevOps client
        print("\n1. Initializing Azure DevOps client...")
        ado_client = AzureDevOpsClient(
            organization=config["ADO_ORGANIZATION"],
            project=config["ADO_PROJECT"],
            personal_access_token=config["ADO_PAT"]
        )
        print("✅ Azure DevOps client initialized")
        
        # Test retrieving specific work items that should exist
        print("\n2. Testing retrieval of specific work items...")
        
        # Test Epic retrieval
        print("\n   Testing Epic retrieval...")
        epic_ids_to_test = [13, 14, 15, 16, 17, 18, 19, 20]  # IDs from our tests
        
        existing_epics = []
        for epic_id in epic_ids_to_test:
            try:
                epic_info = ado_client.get_work_item(str(epic_id))
                if epic_info:
                    print(f"   ✅ Epic ID {epic_id}: {epic_info.get('title', 'N/A')} - Type: {epic_info.get('work_item_type', 'N/A')}")
                    existing_epics.append({
                        'id': epic_id,
                        'title': epic_info.get('title', 'N/A'),
                        'type': epic_info.get('work_item_type', 'N/A'),
                        'status': epic_info.get('status', 'N/A')
                    })
                else:
                    print(f"   ❌ Epic ID {epic_id}: Not found")
            except Exception as e:
                print(f"   ❌ Epic ID {epic_id}: Error - {str(e)}")
        
        # Test Feature retrieval
        print("\n   Testing Feature retrieval...")
        feature_ids_to_test = [14]  # Feature ID from our test
        
        existing_features = []
        for feature_id in feature_ids_to_test:
            try:
                feature_info = ado_client.get_work_item(str(feature_id))
                if feature_info:
                    print(f"   ✅ Feature ID {feature_id}: {feature_info.get('title', 'N/A')} - Type: {feature_info.get('work_item_type', 'N/A')}")
                    existing_features.append({
                        'id': feature_id,
                        'title': feature_info.get('title', 'N/A'),
                        'type': feature_info.get('work_item_type', 'N/A'),
                        'status': feature_info.get('status', 'N/A')
                    })
                else:
                    print(f"   ❌ Feature ID {feature_id}: Not found")
            except Exception as e:
                print(f"   ❌ Feature ID {feature_id}: Error - {str(e)}")
        
        # Test User Story retrieval
        print("\n   Testing User Story retrieval...")
        story_ids_to_test = [15, 16, 17, 18, 19]  # Story IDs from our test
        
        existing_stories = []
        for story_id in story_ids_to_test:
            try:
                story_info = ado_client.get_work_item(str(story_id))
                if story_info:
                    print(f"   ✅ Story ID {story_id}: {story_info.get('title', 'N/A')} - Type: {story_info.get('work_item_type', 'N/A')}")
                    existing_stories.append({
                        'id': story_id,
                        'title': story_info.get('title', 'N/A'),
                        'type': story_info.get('work_item_type', 'N/A'),
                        'status': story_info.get('status', 'N/A')
                    })
                else:
                    print(f"   ❌ Story ID {story_id}: Not found")
            except Exception as e:
                print(f"   ❌ Story ID {story_id}: Error - {str(e)}")
        
        # Test creating a simple User Story to see if the type is available
        print("\n3. Testing User Story creation...")
        try:
            from models.domain import UserStory, StoryType, Priority, StoryStatus, AcceptanceCriterion
            
            test_story = UserStory(
                id="test-story-validation-" + datetime.now().strftime("%Y%m%d-%H%M%S"),
                title="Test User Story for Validation",
                description="This is a test user story to validate that the User Story work item type is available.",
                story_type=StoryType.USER_STORY,
                priority=Priority.LOW,
                status=StoryStatus.NEW,
                estimated_story_points=1,
                acceptance_criteria=[
                    AcceptanceCriterion(
                        id="ac-test-1",
                        description="Test acceptance criterion",
                        criteria="This is a test acceptance criterion",
                        test_scenario="Verify the test works"
                    )
                ]
            )
            
            # Try to create the user story
            story_id = ado_client.create_user_story(test_story)
            if story_id:
                print(f"   ✅ Test User Story created successfully! ID: {story_id}")
                
                # Verify it was created
                created_story = ado_client.get_work_item(str(story_id))
                if created_story:
                    print(f"   ✅ Created story verified: {created_story.get('title', 'N/A')} - Type: {created_story.get('work_item_type', 'N/A')}")
                else:
                    print(f"   ❌ Created story not found after creation")
            else:
                print(f"   ❌ Test User Story creation failed")
                
        except Exception as e:
            print(f"   ❌ Test User Story creation error: {str(e)}")
        
        # Display summary
        print("\n" + "="*70)
        print("🎉 WORK ITEM VALIDATION COMPLETED!")
        print("="*70)
        
        print(f"\n📋 Work Items Found:")
        print(f"   🏗️  Epics: {len(existing_epics)}")
        for epic in existing_epics:
            print(f"      - ID {epic['id']}: {epic['title']} ({epic['type']}) - Status: {epic['status']}")
        
        print(f"\n   🎯 Features: {len(existing_features)}")
        for feature in existing_features:
            print(f"      - ID {feature['id']}: {feature['title']} ({feature['type']}) - Status: {feature['status']}")
        
        print(f"\n   📝 User Stories: {len(existing_stories)}")
        for story in existing_stories:
            print(f"      - ID {story['id']}: {story['title']} ({story['type']}) - Status: {story['status']}")
        
        print(f"\n🔗 View all work items in Azure DevOps:")
        print(f"   https://dev.azure.com/{config['ADO_ORGANIZATION']}/{config['ADO_PROJECT']}/_workitems/")
        
        if existing_epics:
            print(f"\n🔗 View specific Epic:")
            print(f"   Epic ID 13: https://dev.azure.com/{config['ADO_ORGANIZATION']}/{config['ADO_PROJECT']}/_workitems/edit/13")
        
        if existing_features:
            print(f"\n🔗 View specific Feature:")
            print(f"   Feature ID 14: https://dev.azure.com/{config['ADO_ORGANIZATION']}/{config['ADO_PROJECT']}/_workitems/edit/14")
        
        if existing_stories:
            print(f"\n🔗 View specific User Stories:")
            for story in existing_stories[:3]:  # Show first 3
                print(f"   Story ID {story['id']}: https://dev.azure.com/{config['ADO_ORGANIZATION']}/{config['ADO_PROJECT']}/_workitems/edit/{story['id']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Work item validation failed: {str(e)}")
        logger.error(f"Work item validation error: {str(e)}", exc_info=True)
        return False


async def main():
    """Main test execution."""
    print("🚀 Agentic AI Architect - Work Item Validation")
    
    success = await validate_work_items()
    
    if success:
        print("\n✅ Work item validation completed successfully!")
        print("   You now have a clear picture of what work items exist in your project.")
    else:
        print("\n❌ Work item validation failed!")
        print("   Please check your configuration and try again.")
    
    return success


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Test execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Test execution failed with error: {str(e)}")
        sys.exit(1)
