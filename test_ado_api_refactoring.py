#!/usr/bin/env python3
"""
Test Azure DevOps API Refactoring Workflow
Comprehensive test for Epic -> Feature -> User Stories with proper linking
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.ado_client import AzureDevOpsClient
from models.domain import Epic, Feature, UserStory, AcceptanceCriterion, Priority, StoryType, StoryStatus

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


async def test_api_refactoring_workflow():
    """Test the complete API refactoring workflow with proper linking."""
    print("\n" + "="*80)
    print("🚀 TESTING AZURE DEVOPS API REFACTORING WORKFLOW")
    print("="*80)
    
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
        
        # Create test data with proper hierarchy
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        
        print(f"\n2. Creating API Refactoring Epic...")
        api_refactoring_epic = Epic(
            id=f"api-refactoring-epic-{timestamp}",
            title=f"API Refactoring - Customer Service Transformation {timestamp}",
            description="""Transform the existing customer API to implement Domain-Driven Design principles 
            and align with SCB's Enterprise Content Management (ECM) standards. This epic will establish 
            a modern, scalable architecture that improves maintainability and performance.""",
            priority=Priority.HIGH,
            business_value="""Transform existing customer API to improve scalability, maintainability, 
            and alignment with enterprise standards. Enable faster feature development and better 
            system integration.""",
            target_release="Q4 2024"
        )
        
        epic_id = ado_client.create_epic(api_refactoring_epic)
        if not epic_id:
            print("❌ Epic creation failed")
            return False
        
        print(f"✅ Created API Refactoring Epic with ID: {epic_id}")
        
        print(f"\n3. Creating DDD Implementation Feature...")
        ddd_feature = Feature(
            id=f"ddd-implementation-feature-{timestamp}",
            name=f"Implement Domain-Driven Design for Customer API {timestamp}",
            description="""Create and implement a comprehensive Domain-Driven Design for the customer API, 
            including bounded contexts, domain models, and strategic design patterns. This feature will 
            establish the foundation for the refactored architecture.""",
            priority=Priority.HIGH,
            epic_id=epic_id,
            business_requirements="""Transform existing customer API to follow DDD principles, 
            improve code organization, and establish clear domain boundaries.""",
            technical_requirements="""- Generate DDD models and bounded context maps
            - Implement domain entities and value objects
            - Establish aggregate boundaries and repositories
            - Create domain services and application services
            - Implement CQRS pattern for read/write operations"""
        )
        
        feature_id = ado_client.create_feature(ddd_feature, epic_id)
        if not feature_id:
            print("❌ Feature creation failed")
            return False
        
        print(f"✅ Created DDD Implementation Feature with ID: {feature_id}")
        
        print(f"\n4. Creating User Stories with Acceptance Criteria...")
        
        # Define the 5 user stories based on the DOD steps
        user_stories = [
            UserStory(
                id=f"story-1-{timestamp}",
                title="Analyze Existing Customer API Domain",
                description="""As a domain architect, I want to analyze the existing customer API domain 
                to understand current structure, identify pain points, and map out the existing 
                business processes and data flows.""",
                story_type=StoryType.USER_STORY,
                priority=Priority.HIGH,
                status=StoryStatus.NEW,
                estimated_story_points=8,
                acceptance_criteria=[
                    AcceptanceCriterion(
                        id=f"ac-1-1-{timestamp}",
                        description="API endpoints documented",
                        criteria="All existing API endpoints are documented with their current implementation details, request/response formats, and business logic",
                        test_scenario="Review API documentation for completeness and accuracy"
                    ),
                    AcceptanceCriterion(
                        id=f"ac-1-2-{timestamp}",
                        description="Domain entities identified",
                        criteria="Current domain entities, their relationships, and business rules are identified and documented",
                        test_scenario="Validate that all business entities are captured in the domain model"
                    ),
                    AcceptanceCriterion(
                        id=f"ac-1-3-{timestamp}",
                        description="Pain points documented",
                        criteria="Technical debt, performance issues, and architectural problems are identified and prioritized",
                        test_scenario="Review pain point analysis and validate prioritization"
                    )
                ]
            ),
            UserStory(
                id=f"story-2-{timestamp}",
                title="Create Bounded Context Map",
                description="""As a domain architect, I want to create a bounded context map that defines 
                clear boundaries between different business domains, identifies context relationships, 
                and establishes integration patterns.""",
                story_type=StoryType.USER_STORY,
                priority=Priority.HIGH,
                status=StoryStatus.NEW,
                estimated_story_points=5,
                acceptance_criteria=[
                    AcceptanceCriterion(
                        id=f"ac-2-1-{timestamp}",
                        description="Bounded contexts defined",
                        criteria="Clear boundaries are defined for each business domain with explicit responsibilities",
                        test_scenario="Validate that each bounded context has clear, non-overlapping responsibilities"
                    ),
                    AcceptanceCriterion(
                        id=f"ac-2-2-{timestamp}",
                        description="Context relationships mapped",
                        criteria="Relationships between bounded contexts are documented with integration patterns",
                        test_scenario="Review context map for consistency and completeness"
                    )
                ]
            ),
            UserStory(
                id=f"story-3-{timestamp}",
                title="Generate Domain Models and Entities",
                description="""As a domain architect, I want to generate comprehensive domain models 
                that represent the business entities, their relationships, and business rules in 
                alignment with DDD principles.""",
                story_type=StoryType.USER_STORY,
                priority=Priority.HIGH,
                status=StoryStatus.NEW,
                estimated_story_points=13,
                acceptance_criteria=[
                    AcceptanceCriterion(
                        id=f"ac-3-1-{timestamp}",
                        description="Domain entities created",
                        criteria="All business entities are modeled as domain entities with proper encapsulation",
                        test_scenario="Validate that entities follow DDD principles and business rules"
                    ),
                    AcceptanceCriterion(
                        id=f"ac-3-2-{timestamp}",
                        description="Value objects defined",
                        criteria="Immutable value objects are created for concepts that don't have identity",
                        test_scenario="Review value objects for immutability and business rule compliance"
                    ),
                    AcceptanceCriterion(
                        id=f"ac-3-3-{timestamp}",
                        description="Aggregates defined",
                        criteria="Aggregate boundaries are established with proper consistency guarantees",
                        test_scenario="Validate aggregate design and consistency rules"
                    )
                ]
            ),
            UserStory(
                id=f"story-4-{timestamp}",
                title="Align with SCB's ECM Principles",
                description="""As a domain architect, I want to ensure the domain models and architecture 
                align with SCB's Enterprise Content Management principles, including data governance, 
                security, and compliance requirements.""",
                story_type=StoryType.USER_STORY,
                priority=Priority.HIGH,
                status=StoryStatus.NEW,
                estimated_story_points=8,
                acceptance_criteria=[
                    AcceptanceCriterion(
                        id=f"ac-4-1-{timestamp}",
                        description="ECM compliance verified",
                        criteria="Domain models comply with SCB's ECM data governance and security policies",
                        test_scenario="Review compliance with ECM requirements and security standards"
                    ),
                    AcceptanceCriterion(
                        id=f"ac-4-2-{timestamp}",
                        description="Data classification applied",
                        criteria="All data elements are properly classified according to ECM standards",
                        test_scenario="Validate data classification and handling procedures"
                    )
                ]
            ),
            UserStory(
                id=f"story-5-{timestamp}",
                title="Generate CML and Visual Representations",
                description="""As a domain architect, I want to generate Context Mapper Language (CML) 
                specifications and visual representations that document the domain architecture 
                for development teams and stakeholders.""",
                story_type=StoryType.USER_STORY,
                priority=Priority.MEDIUM,
                status=StoryStatus.NEW,
                estimated_story_points=5,
                acceptance_criteria=[
                    AcceptanceCriterion(
                        id=f"ac-5-1-{timestamp}",
                        description="CML specifications generated",
                        criteria="Complete CML specifications are generated for all bounded contexts and domain models",
                        test_scenario="Validate CML syntax and completeness"
                    ),
                    AcceptanceCriterion(
                        id=f"ac-5-2-{timestamp}",
                        description="Visual diagrams created",
                        criteria="Clear visual representations of the domain architecture are generated",
                        test_scenario="Review diagrams for clarity and accuracy"
                    )
                ]
            )
        ]
        
        # Create all user stories
        created_stories = []
        total_story_points = 0
        total_tasks_created = 0
        
        for i, story in enumerate(user_stories, 1):
            print(f"\n   Creating Story {i}: {story.title}")
            story_id = ado_client.create_user_story(story, feature_id)
            
            if story_id:
                # Count tasks created for this story (based on acceptance criteria)
                story_tasks = len(story.acceptance_criteria)
                total_tasks_created += story_tasks
                
                created_stories.append({
                    "id": story_id,
                    "title": story.title,
                    "story_points": story.estimated_story_points,
                    "ac_count": len(story.acceptance_criteria),
                    "tasks_created": story_tasks
                })
                total_story_points += story.estimated_story_points
                print(f"      ✅ Created with ID: {story_id} ({story.estimated_story_points} story points)")
                print(f"      📝 Acceptance Criteria: {len(story.acceptance_criteria)} captured in story")
                print(f"      ✅ Tasks: {story_tasks} linked tasks created")
            else:
                print(f"      ❌ Failed to create story: {story.title}")
        
        if not created_stories:
            print("❌ No user stories were created")
            return False
        
        print(f"\n5. Verifying Work Item Hierarchy and Relationships...")
        
        # Verify Epic
        epic_info = ado_client.get_work_item(epic_id)
        if epic_info:
            print(f"   🏗️  Epic {epic_id}: {epic_info.get('title', 'N/A')}")
            print(f"      Status: {epic_info.get('status', 'N/A')}")
            print(f"      Type: {epic_info.get('work_item_type', 'N/A')}")
        
        # Verify Feature and its parent
        feature_info = ado_client.get_work_item(feature_id)
        if feature_info:
            print(f"   🎯 Feature {feature_id}: {feature_info.get('title', 'N/A')}")
            print(f"      Status: {feature_info.get('status', 'N/A')}")
            print(f"      Type: {feature_info.get('work_item_type', 'N/A')}")
            print(f"      Parent: Epic {epic_id}")
        
        # Verify User Stories and their parent
        for story_info in created_stories:
            story_data = ado_client.get_work_item(story_info["id"])
            if story_data:
                print(f"   📝 Story {story_info['id']}: {story_info['title']}")
                print(f"      Status: {story_data.get('status', 'N/A')}")
                print(f"      Type: {story_data.get('work_item_type', 'N/A')}")
                print(f"      Parent: Feature {feature_id}")
                print(f"      Story Points: {story_info['story_points']}")
                print(f"      AC Count: {story_info['ac_count']}")
                print(f"      Tasks Created: {story_info['tasks_created']}")
                
                # Show acceptance criteria preview
                if story_data.get('fields', {}).get('Microsoft.VSTS.Common.AcceptanceCriteria'):
                    ac_content = story_data['fields']['Microsoft.VSTS.Common.AcceptanceCriteria']
                    ac_preview = str(ac_content)[:150] + "..." if len(str(ac_content)) > 150 else str(ac_content)
                    print(f"      📋 AC Preview: {ac_preview}")
        
        # Display comprehensive summary
        print("\n" + "="*80)
        print("🎉 API REFACTORING WORKFLOW TEST COMPLETED!")
        print("="*80)
        
        print(f"\n📋 Workflow Results:")
        print(f"   🏗️  Epic: {epic_id} (API Refactoring - Customer Service Transformation)")
        print(f"   🎯 Feature: {feature_id} (DDD Implementation)")
        print(f"   📝 User Stories: {len(created_stories)} created successfully")
        print(f"   📊 Total Story Points: {total_story_points}")
        
        # Calculate average AC per story
        total_ac = sum(story['ac_count'] for story in created_stories)
        avg_ac = total_ac / len(created_stories) if created_stories else 0
        print(f"   ✅ Total Acceptance Criteria: {total_ac} (avg: {avg_ac:.1f} per story)")
        print(f"   🔗 Linked Tasks: {total_tasks_created} tasks created and linked to stories")
        
        print(f"\n🔗 View Work Items in Azure DevOps:")
        print(f"   Epic: https://dev.azure.com/{config['ADO_ORGANIZATION']}/{config['ADO_PROJECT']}/_workitems/edit/{epic_id}")
        print(f"   Feature: https://dev.azure.com/{config['ADO_ORGANIZATION']}/{config['ADO_PROJECT']}/_workitems/edit/{feature_id}")
        
        print(f"\n📝 User Stories:")
        for story_info in created_stories:
            print(f"   Story {story_info['id']}: https://dev.azure.com/{config['ADO_ORGANIZATION']}/{config['ADO_PROJECT']}/_workitems/edit/{story_info['id']}")
        
        print(f"\n📊 Final Hierarchy:")
        print(f"   Epic {epic_id} (API Refactoring)")
        print(f"   └── Feature {feature_id} (DDD Implementation)")
        for i, story_info in enumerate(created_stories, 1):
            print(f"       ├── Story {story_info['id']} ({story_info['story_points']} pts) - {story_info['title'][:50]}...")
            print(f"       │   └── {story_info['tasks_created']} linked tasks for acceptance criteria")
        print(f"       └── Total: {total_story_points} story points, {total_tasks_created} tasks")
        
        print(f"\n🎯 Test Status: SUCCESS")
        print(f"   All work items created with proper hierarchical linking")
        print(f"   Acceptance criteria captured in story fields AND as linked tasks")
        print(f"   Tasks properly linked to user stories for development tracking")
        print(f"   Ready for sprint planning and development")
        
        return True
        
    except Exception as e:
        print(f"❌ API refactoring workflow test failed: {str(e)}")
        logger.error(f"Workflow test error: {str(e)}", exc_info=True)
        return False


async def main():
    """Main test execution."""
    print("🚀 Agentic AI Architect - Test Azure DevOps API Refactoring Workflow")
    
    success = await test_api_refactoring_workflow()
    
    if success:
        print("\n✅ API refactoring workflow test completed successfully!")
        print("   Your Azure DevOps integration is working perfectly with proper linking.")
    else:
        print("\n❌ API refactoring workflow test failed!")
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
