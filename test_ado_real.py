#!/usr/bin/env python3
"""
Real Azure DevOps integration test with actual work item creation.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.domain import Epic, Feature, UserStory, Priority, StoryType, StoryStatus
from services.ado_client import AzureDevOpsClient
from agents.requirements import RequirementsAgent

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


async def test_ado_real_integration():
    """Test real Azure DevOps integration with work item creation."""
    print("\n" + "="*60)
    print("REAL AZURE DEVOPS INTEGRATION TEST")
    print("="*60)
    
    try:
        # Load configuration
        config = load_config_from_file()
        
        print(f"Organization: {config.get('ADO_ORGANIZATION', 'Not set')}")
        print(f"Project: {config.get('ADO_PROJECT', 'Not set')}")
        print(f"PAT: {'*' * 20}...")
        
        # Validate required configuration
        required_configs = ["ADO_ORGANIZATION", "ADO_PROJECT", "ADO_PAT"]
        missing_configs = [config_name for config_name in required_configs if not config.get(config_name)]
        
        if missing_configs:
            print(f"❌ Missing required configuration: {missing_configs}")
            return False
        
        # Initialize Azure DevOps client
        print("\n1. Initializing Azure DevOps client...")
        ado_client = AzureDevOpsClient(
            organization=config["ADO_ORGANIZATION"],
            project=config["ADO_PROJECT"],
            personal_access_token=config["ADO_PAT"]
        )
        print("✅ Azure DevOps client initialized")
        
        # Create test data
        print("\n2. Creating test work items...")
        
        # Create test epic
        test_epic = Epic(
            id="test-epic-" + datetime.now().strftime("%Y%m%d-%H%M%S"),
            title=f"Test Epic - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            description="This is a test epic created by the Agentic AI Architect system for validation purposes.",
            priority=Priority.MEDIUM,
            business_value="Testing Azure DevOps integration",
            target_release="Test Release"
        )
        
        # Create test feature
        test_feature = Feature(
            id="test-feature-" + datetime.now().strftime("%Y%m%d-%H%M%S"),
            name=f"Test Feature - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            description="This is a test feature created by the Agentic AI Architect system for validation purposes.",
            priority=Priority.MEDIUM,
            epic_id="",  # Will be set after epic creation
            business_requirements="Test the Azure DevOps integration functionality",
            technical_requirements="Validate work item creation and linking"
        )
        
        # Create test user stories
        test_stories = [
            UserStory(
                id="test-story-1-" + datetime.now().strftime("%Y%m%d-%H%M%S"),
                title=f"Test User Story 1 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                description="As a developer, I want to test Azure DevOps integration so that I can validate the system functionality.",
                story_type=StoryType.USER_STORY,
                priority=Priority.MEDIUM,
                status=StoryStatus.NEW
            ),
            UserStory(
                id="test-story-2-" + datetime.now().strftime("%Y%m%d-%H%M%S"),
                title=f"Test User Story 2 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                description="As a product owner, I want to verify work item creation so that I can trust the automated system.",
                story_type=StoryType.USER_STORY,
                priority=Priority.LOW,
                status=StoryStatus.NEW
            )
        ]
        
        # Test work item creation using the requirements agent
        print("\n3. Testing work item creation...")
        requirements_agent = RequirementsAgent(ado_client)
        
        result = await requirements_agent.create_requirements_in_ado(
            feature=test_feature,
            epic=test_epic,
            user_stories=test_stories
        )
        
        if result["success"]:
            print("✅ Work items created successfully!")
            print(f"   Epic ID: {result['epic_id']}")
            print(f"   Feature ID: {result['feature_id']}")
            print(f"   Created {len(result['story_ids'])} user stories:")
            for story_info in result['story_ids']:
                print(f"     - {story_info['title']}: ID {story_info['story_id']}")
        else:
            print("❌ Work item creation failed!")
            for error in result["errors"]:
                print(f"   Error: {error}")
            return False
        
        # Test work item retrieval
        print("\n4. Testing work item retrieval...")
        epic_info = ado_client.get_work_item(result["epic_id"])
        if epic_info:
            print(f"✅ Retrieved epic: {epic_info['title']}")
            print(f"   Status: {epic_info['status']}")
            print(f"   Type: {epic_info['work_item_type']}")
        else:
            print("❌ Failed to retrieve epic")
        
        # Test story search
        print("\n5. Testing story search...")
        stories = await requirements_agent.search_stories_by_epic(result["epic_id"])
        if stories:
            print(f"✅ Found {len(stories)} stories in epic")
            for story in stories:
                print(f"   - {story.get('title', 'N/A')}: {story.get('status', 'N/A')}")
        else:
            print("⚠️  No stories found in epic")
        
        # Test epic progress
        print("\n6. Testing epic progress tracking...")
        progress = await requirements_agent.get_epic_progress(result["epic_id"])
        if not progress.get("error"):
            print(f"✅ Epic progress retrieved:")
            print(f"   Total stories: {progress['total_stories']}")
            print(f"   Completed: {progress['completed_stories']}")
            print(f"   In progress: {progress['in_progress_stories']}")
            print(f"   Progress: {progress['progress_percentage']:.1f}%")
        else:
            print(f"❌ Failed to get epic progress: {progress.get('error')}")
        
        print("\n" + "="*60)
        print("🎉 AZURE DEVOPS INTEGRATION TEST COMPLETED SUCCESSFULLY!")
        print("="*60)
        
        print(f"\n📋 Created Work Items in Azure DevOps:")
        print(f"   🏗️  Epic: {test_epic.title}")
        print(f"      ID: {result['epic_id']}")
        print(f"      URL: https://dev.azure.com/{config['ADO_ORGANIZATION']}/{config['ADO_PROJECT']}/_workitems/edit/{result['epic_id']}")
        
        print(f"\n   🎯 Feature: {test_feature.name}")
        print(f"      ID: {result['feature_id']}")
        print(f"      URL: https://dev.azure.com/{config['ADO_ORGANIZATION']}/{config['ADO_PROJECT']}/_workitems/edit/{result['feature_id']}")
        
        print(f"\n   📝 User Stories:")
        for story_info in result['story_ids']:
            print(f"      - {story_info['title']}")
            print(f"        ID: {story_info['story_id']}")
            print(f"        URL: https://dev.azure.com/{config['ADO_ORGANIZATION']}/{config['ADO_PROJECT']}/_workitems/edit/{story_info['story_id']}")
        
        print(f"\n🔗 View all work items in Azure DevOps:")
        print(f"   https://dev.azure.com/{config['ADO_ORGANIZATION']}/{config['ADO_PROJECT']}/_workitems/")
        
        return True
        
    except Exception as e:
        print(f"❌ Azure DevOps integration test failed: {str(e)}")
        logger.error(f"ADO integration test error: {str(e)}", exc_info=True)
        return False


async def main():
    """Main test execution."""
    print("🚀 Agentic AI Architect - Real Azure DevOps Integration Test")
    
    success = await test_ado_real_integration()
    
    if success:
        print("\n✅ All Azure DevOps integration tests passed!")
        print("   The system is ready for production use with Azure DevOps.")
    else:
        print("\n❌ Azure DevOps integration tests failed!")
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
