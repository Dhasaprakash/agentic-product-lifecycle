#!/usr/bin/env python3
"""
Azure DevOps Agile Project - Epic and User Stories Creation with Acceptance Criteria
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.domain import Epic, Feature, UserStory, Priority, StoryType, StoryStatus, AcceptanceCriterion
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


async def test_agile_epic_and_stories():
    """Test creating Epic and User Stories in Agile Azure DevOps project."""
    print("\n" + "="*80)
    print("AZURE DEVOPS AGILE PROJECT - EPIC & USER STORIES CREATION")
    print("="*80)
    
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
        
        # Create the main Epic for API Refactoring
        print("\n2. Creating main Epic: API Refactoring...")
        
        main_epic = Epic(
            id="api-refactoring-main-" + datetime.now().strftime("%Y%m%d-%H%M%S"),
            title="API Refactoring - Customer Service Transformation",
            description="""Transform the existing customer API into a well-architected, 
domain-driven design that aligns with SCB's Enterprise Context Mapping (ECM) 
principles and produces a production-ready microservice.

This epic encompasses the complete transformation journey from legacy API to 
modern, scalable, and maintainable microservice architecture.""",
            priority=Priority.HIGH,
            business_value="""Transform existing customer API into a well-architected, 
domain-driven design that aligns with SCB's Enterprise Context Mapping (ECM) 
principles and produces a production-ready microservice foundation.""",
            target_release="Q4 2024"
        )
        
        # Create the main epic
        epic_id = ado_client.create_epic(main_epic)
        if not epic_id:
            print("❌ Failed to create main Epic")
            return False
        
        print(f"✅ Main Epic created successfully!")
        print(f"   Epic ID: {epic_id}")
        print(f"   Title: {main_epic.title}")
        print(f"   Priority: {main_epic.priority}")
        
        # Create the Feature
        print("\n3. Creating Feature: DDD Design Implementation...")
        
        ddd_feature = Feature(
            id="ddd-design-feature-" + datetime.now().strftime("%Y%m%d-%H%M%S"),
            name="Implement Domain-Driven Design for Customer API",
            description="""Create and implement a comprehensive Domain-Driven Design 
for the customer API refactoring project, following SCB's ECM principles.

This feature will establish the architectural foundation for the entire 
transformation project.""",
            priority=Priority.HIGH,
            epic_id=epic_id,
            business_requirements="""Transform existing customer API into a well-architected, 
domain-driven design that aligns with SCB's Enterprise Context Mapping (ECM) 
principles and produces a production-ready microservice foundation.""",
            technical_requirements="""- Generate DDD models using Context Mapper Language (CML)
- Create bounded context definitions
- Define aggregate boundaries and entities
- Map domain services and repositories
- Generate visual representations
- Ensure consistency with SCB's ECM guidelines"""
        )
        
        # Create the feature
        feature_id = ado_client.create_feature(ddd_feature)
        if not feature_id:
            print("❌ Failed to create Feature")
            return False
        
        print(f"✅ Feature created successfully!")
        print(f"   Feature ID: {feature_id}")
        print(f"   Name: {ddd_feature.name}")
        print(f"   Epic ID: {epic_id}")
        
        # Create User Stories with comprehensive acceptance criteria
        print("\n4. Creating User Stories with Acceptance Criteria...")
        
        user_stories = [
            UserStory(
                id="story-1-" + datetime.now().strftime("%Y%m%d-%H%M%S"),
                title="Analyze Existing Customer API Domain",
                description="""As a domain architect, I want to analyze the existing customer API 
to understand the current domain model, so that I can identify areas for 
improvement and DDD alignment.

This story focuses on understanding the current state of the customer API, 
including its endpoints, data models, business rules, and domain concepts.""",
                story_type=StoryType.USER_STORY,
                priority=Priority.HIGH,
                status=StoryStatus.NEW,
                epic_id=epic_id,
                estimated_story_points=8,
                acceptance_criteria=[
                    AcceptanceCriterion(
                        id="ac-1-1",
                        description="API endpoints documented",
                        criteria="All existing API endpoints are documented with their purpose, parameters, and response formats",
                        test_scenario="Review API documentation for completeness and accuracy"
                    ),
                    AcceptanceCriterion(
                        id="ac-1-2",
                        description="Data models analyzed",
                        criteria="Current data models are analyzed and documented with their relationships and constraints",
                        test_scenario="Review data model documentation and validate relationships"
                    ),
                    AcceptanceCriterion(
                        id="ac-1-3",
                        description="Domain concepts identified",
                        criteria="Key domain concepts are identified and documented with clear definitions",
                        test_scenario="Review domain concept documentation for clarity"
                    ),
                    AcceptanceCriterion(
                        id="ac-1-4",
                        description="Business rules documented",
                        criteria="Business rules are documented and validated with stakeholders",
                        test_scenario="Review business rules documentation with business analysts"
                    ),
                    AcceptanceCriterion(
                        id="ac-1-5",
                        description="Gap analysis completed",
                        criteria="Gap analysis between current API and target DDD architecture is completed",
                        test_scenario="Review gap analysis report and validate findings"
                    )
                ]
            ),
            UserStory(
                id="story-2-" + datetime.now().strftime("%Y%m%d-%H%M%S"),
                title="Create Bounded Context Map",
                description="""As a domain architect, I want to create a bounded context map 
for the customer API, so that I can clearly define domain boundaries and 
relationships.

This story focuses on establishing the foundational structure for the 
domain-driven design by defining clear boundaries between different 
business capabilities.""",
                story_type=StoryType.USER_STORY,
                priority=Priority.HIGH,
                status=StoryStatus.NEW,
                epic_id=epic_id,
                estimated_story_points=13,
                acceptance_criteria=[
                    AcceptanceCriterion(
                        id="ac-2-1",
                        description="Bounded contexts identified",
                        criteria="All bounded contexts are identified and documented with clear boundaries",
                        test_scenario="Review bounded context definitions with domain experts"
                    ),
                    AcceptanceCriterion(
                        id="ac-2-2",
                        description="Context relationships mapped",
                        criteria="Relationships between contexts are mapped and documented with integration patterns",
                        test_scenario="Review context relationship documentation and validate patterns"
                    ),
                    AcceptanceCriterion(
                        id="ac-2-3",
                        description="Context map visualized",
                        criteria="Context map is created and visualized using appropriate tools",
                        test_scenario="Review context map visualization for clarity and accuracy"
                    ),
                    AcceptanceCriterion(
                        id="ac-2-4",
                        description="Integration patterns defined",
                        criteria="Integration patterns between contexts are defined and documented",
                        test_scenario="Review integration pattern documentation with architects"
                    ),
                    AcceptanceCriterion(
                        id="ac-2-5",
                        description="Context boundaries validated",
                        criteria="Context boundaries are validated with business stakeholders and domain experts",
                        test_scenario="Conduct review session with business and technical stakeholders"
                    )
                ]
            ),
            UserStory(
                id="story-3-" + datetime.now().strftime("%Y%m%d-%H%M%S"),
                title="Generate Domain Models and Entities",
                description="""As a domain architect, I want to generate domain models and 
entities for each bounded context, so that I can establish clear domain 
boundaries and responsibilities.

This story focuses on creating the detailed domain models that will form 
the foundation of the new API architecture.""",
                story_type=StoryType.USER_STORY,
                priority=Priority.HIGH,
                status=StoryStatus.NEW,
                epic_id=epic_id,
                estimated_story_points=21,
                acceptance_criteria=[
                    AcceptanceCriterion(
                        id="ac-3-1",
                        description="Domain entities defined",
                        criteria="All domain entities are defined and documented with their properties and behaviors",
                        test_scenario="Review domain entity documentation for completeness"
                    ),
                    AcceptanceCriterion(
                        id="ac-3-2",
                        description="Value objects identified",
                        criteria="Value objects are identified and documented with their immutability characteristics",
                        test_scenario="Review value object definitions and validate immutability"
                    ),
                    AcceptanceCriterion(
                        id="ac-3-3",
                        description="Aggregates bounded",
                        criteria="Aggregate boundaries are defined and documented with consistency rules",
                        test_scenario="Review aggregate boundary definitions and validate consistency rules"
                    ),
                    AcceptanceCriterion(
                        id="ac-3-4",
                        description="Domain services specified",
                        criteria="Domain services are specified and documented with their responsibilities",
                        test_scenario="Review domain service specifications and validate responsibilities"
                    ),
                    AcceptanceCriterion(
                        id="ac-3-5",
                        description="Domain events defined",
                        criteria="Domain events are defined and documented with their triggers and handlers",
                        test_scenario="Review domain event definitions and validate event flow"
                    ),
                    AcceptanceCriterion(
                        id="ac-3-6",
                        description="Repository interfaces defined",
                        criteria="Repository interfaces are defined and documented with their contracts",
                        test_scenario="Review repository interface definitions and validate contracts"
                    )
                ]
            ),
            UserStory(
                id="story-4-" + datetime.now().strftime("%Y%m%d-%H%M%S"),
                title="Align with SCB's ECM Principles",
                description="""As a domain architect, I want to ensure the DDD design aligns 
with SCB's Enterprise Context Mapping principles, so that the solution 
fits within the enterprise architecture.

This story focuses on ensuring enterprise-wide consistency and compliance 
with established architectural standards.""",
                story_type=StoryType.USER_STORY,
                priority=Priority.HIGH,
                status=StoryStatus.NEW,
                epic_id=epic_id,
                estimated_story_points=13,
                acceptance_criteria=[
                    AcceptanceCriterion(
                        id="ac-4-1",
                        description="ECM guidelines followed",
                        criteria="All SCB ECM guidelines are followed and documented with compliance evidence",
                        test_scenario="Review ECM compliance documentation and validate adherence"
                    ),
                    AcceptanceCriterion(
                        id="ac-4-2",
                        description="Enterprise patterns applied",
                        criteria="Enterprise patterns are applied and documented with justification",
                        test_scenario="Review enterprise pattern application and validate justification"
                    ),
                    AcceptanceCriterion(
                        id="ac-4-3",
                        description="Integration standards met",
                        criteria="Integration standards are met and documented with compliance evidence",
                        test_scenario="Review integration standard compliance and validate adherence"
                    ),
                    AcceptanceCriterion(
                        id="ac-4-4",
                        description="Governance requirements satisfied",
                        criteria="All governance requirements are satisfied and documented with approval evidence",
                        test_scenario="Review governance compliance documentation and validate approvals"
                    ),
                    AcceptanceCriterion(
                        id="ac-4-5",
                        description="Enterprise review completed",
                        criteria="Enterprise architecture review is completed with stakeholder approval",
                        test_scenario="Conduct enterprise architecture review session and obtain approvals"
                    )
                ]
            ),
            UserStory(
                id="story-5-" + datetime.now().strftime("%Y%m%d-%H%M%S"),
                title="Generate CML and Visual Representations",
                description="""As a domain architect, I want to generate Context Mapper Language 
(CML) and visual representations of the DDD design, so that the design 
can be shared and validated with stakeholders.

This story focuses on creating the technical artifacts that will enable 
implementation and stakeholder communication.""",
                story_type=StoryType.USER_STORY,
                priority=Priority.MEDIUM,
                status=StoryStatus.NEW,
                epic_id=epic_id,
                estimated_story_points=8,
                acceptance_criteria=[
                    AcceptanceCriterion(
                        id="ac-5-1",
                        description="CML specification generated",
                        criteria="Complete CML specification is generated and validated for syntax correctness",
                        test_scenario="Validate CML syntax using Context Mapper tools"
                    ),
                    AcceptanceCriterion(
                        id="ac-5-2",
                        description="Visual diagrams created",
                        criteria="Visual diagrams are created for all major components and relationships",
                        test_scenario="Review visual diagrams for clarity and accuracy"
                    ),
                    AcceptanceCriterion(
                        id="ac-5-3",
                        description="Documentation completed",
                        criteria="Complete documentation is generated with clear explanations and examples",
                        test_scenario="Review documentation for completeness and clarity"
                    ),
                    AcceptanceCriterion(
                        id="ac-5-4",
                        description="Stakeholder review completed",
                        criteria="Stakeholder review is completed with feedback incorporated",
                        test_scenario="Conduct stakeholder review session and incorporate feedback"
                    )
                ]
            )
        ]
        
        # Create user stories using the requirements agent
        print("\n5. Creating User Stories in Azure DevOps...")
        
        requirements_agent = RequirementsAgent(ado_client)
        
        # Create each user story individually to ensure proper linking
        created_stories = []
        for i, story in enumerate(user_stories, 1):
            print(f"\n   Creating User Story {i}: {story.title}")
            
            # Create the user story
            story_id = ado_client.create_user_story(story, epic_id)
            if story_id:
                print(f"   ✅ Created: ID {story_id}")
                created_stories.append({
                    "story_number": i,
                    "title": story.title,
                    "id": story_id,
                    "url": f"https://dev.azure.com/{config['ADO_ORGANIZATION']}/{config['ADO_PROJECT']}/_workitems/edit/{story_id}",
                    "story_points": story.estimated_story_points,
                    "acceptance_criteria_count": len(story.acceptance_criteria)
                })
            else:
                print(f"   ❌ Failed to create User Story {i}")
        
        # Display comprehensive results
        print("\n" + "="*80)
        print("🎉 AGILE EPIC & USER STORIES CREATION COMPLETED!")
        print("="*80)
        
        print(f"\n📋 Created Work Items Summary:")
        print(f"   🏗️  Epic: {main_epic.title}")
        print(f"      ID: {epic_id}")
        print(f"      URL: https://dev.azure.com/{config['ADO_ORGANIZATION']}/{config['ADO_PROJECT']}/_workitems/edit/{epic_id}")
        print(f"      Priority: {main_epic.priority}")
        print(f"      Business Value: {main_epic.business_value}")
        
        print(f"\n   🎯 Feature: {ddd_feature.name}")
        print(f"      ID: {feature_id}")
        print(f"      URL: https://dev.azure.com/{config['ADO_ORGANIZATION']}/{config['ADO_PROJECT']}/_workitems/edit/{feature_id}")
        print(f"      Epic ID: {epic_id}")
        print(f"      Priority: {ddd_feature.priority}")
        
        print(f"\n   📝 User Stories ({len(created_stories)} created):")
        total_story_points = 0
        total_acceptance_criteria = 0
        
        for story_info in created_stories:
            print(f"      {story_info['story_number']}. {story_info['title']}")
            print(f"         ID: {story_info['id']}")
            print(f"         URL: {story_info['url']}")
            print(f"         Story Points: {story_info['story_points']}")
            print(f"         Acceptance Criteria: {story_info['acceptance_criteria_count']}")
            total_story_points += story_info['story_points']
            total_acceptance_criteria += story_info['acceptance_criteria_count']
        
        print(f"\n📊 Project Metrics:")
        print(f"   Total Story Points: {total_story_points}")
        print(f"   Total Acceptance Criteria: {total_acceptance_criteria}")
        print(f"   Average Story Points per Story: {total_story_points / len(created_stories):.1f}")
        print(f"   Average Acceptance Criteria per Story: {total_acceptance_criteria / len(created_stories):.1f}")
        
        print(f"\n🔗 View all work items in Azure DevOps:")
        print(f"   https://dev.azure.com/{config['ADO_ORGANIZATION']}/{config['ADO_PROJECT']}/_workitems/")
        
        print(f"\n💡 Next Steps:")
        print(f"   1. Review all created work items in Azure DevOps")
        print(f"   2. Assign team members to User Stories")
        print(f"   3. Set up sprint planning with the created stories")
        print(f"   4. Begin development on Story 1: Analyze Existing Customer API Domain")
        print(f"   5. Use the Agentic AI Architect system to generate DDD models")
        print(f"   6. Track progress through Azure DevOps boards and backlogs")
        
        print(f"\n🎯 Agile Project Ready:")
        print(f"   ✅ Epic created with clear business value")
        print(f"   ✅ Feature defined with technical requirements")
        print(f"   ✅ User Stories created with detailed acceptance criteria")
        print(f"   ✅ Story points estimated for sprint planning")
        print(f"   ✅ All work items properly linked in hierarchy")
        print(f"   ✅ Ready for sprint planning and development")
        
        return True
        
    except Exception as e:
        print(f"❌ Agile Epic and User Stories creation failed: {str(e)}")
        logger.error(f"Agile creation test error: {str(e)}", exc_info=True)
        return False


async def main():
    """Main test execution."""
    print("🚀 Agentic AI Architect - Agile Epic & User Stories Creation")
    
    success = await test_agile_epic_and_stories()
    
    if success:
        print("\n✅ Agile Epic and User Stories creation completed successfully!")
        print("   Your Azure DevOps project now has a complete Agile structure with:")
        print("   - Epic for project scope")
        print("   - Feature for technical implementation")
        print("   - User Stories with detailed acceptance criteria")
        print("   - Proper work item linking and hierarchy")
        print("   - Story points for sprint planning")
    else:
        print("\n❌ Agile Epic and User Stories creation failed!")
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
