#!/usr/bin/env python3
"""
Test DDD Generation for API Refactoring using Agentic AI Architect
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.domain import Feature, Priority, UserStory, StoryType, StoryStatus, AcceptanceCriterion
from workflows.lifecycle import ProductLifecycleWorkflow

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


async def test_ddd_generation():
    """Test DDD generation for the API refactoring project."""
    print("\n" + "="*70)
    print("TESTING DDD GENERATION FOR API REFACTORING")
    print("="*70)
    
    try:
        # Load configuration
        config = load_config_from_file()
        
        # Set environment variables for the agents
        for key, value in config.items():
            if key == "OPENAI_API_KEY":
                os.environ[key] = value
            elif key.startswith("ADO_"):
                os.environ[key] = value
            elif key.startswith("LLM_"):
                os.environ[key] = value
        
        print("1. Loading configuration...")
        print(f"   OpenAI API Key: {'*' * 20}...")
        print(f"   Environment: {config.get('ENVIRONMENT', 'Not set')}")
        print(f"   Log Level: {config.get('LOG_LEVEL', 'Not set')}")
        
        # Create the feature for DDD generation
        print("\n2. Creating feature for DDD generation...")
        
        ddd_feature = Feature(
            id="ddd-generation-feature-" + datetime.now().strftime("%Y%m%d-%H%M%S"),
            name="Create DDD Design for Customer API Refactoring",
            description="""Generate a comprehensive Domain-Driven Design for the customer API refactoring project.

This feature will:
- Analyze the existing customer API domain
- Identify bounded contexts and aggregates
- Create domain models and entities
- Define domain services and repositories
- Map relationships between contexts
- Align with SCB's Enterprise Context Mapping (ECM) principles

The output will include:
- Bounded Context Map
- Domain Model Diagrams
- Aggregate Definitions
- Domain Service Specifications
- Context Relationship Matrix

This is DOD Step 1 of the API Refactoring project.""",
            priority=Priority.HIGH,
            epic_id="6",  # Link to the DOD Step 1 Epic we created
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
        
        # Create user stories for the DDD generation
        ddd_stories = [
            UserStory(
                id="ddd-story-1-" + datetime.now().strftime("%Y%m%d-%H%M%S"),
                title="Analyze Existing Customer API Domain",
                description="As a domain architect, I want to analyze the existing customer API to understand the current domain model, so that I can identify areas for improvement and DDD alignment.",
                story_type=StoryType.USER_STORY,
                priority=Priority.HIGH,
                status=StoryStatus.NEW,
                acceptance_criteria=[
                    AcceptanceCriterion(
                        id="ac-1",
                        description="API endpoints documented",
                        criteria="All existing API endpoints are documented with their purpose and usage",
                        test_scenario="Review API documentation for completeness"
                    ),
                    AcceptanceCriterion(
                        id="ac-2",
                        description="Data models analyzed",
                        criteria="Current data models are analyzed and documented",
                        test_scenario="Review data model documentation"
                    ),
                    AcceptanceCriterion(
                        id="ac-3",
                        description="Domain concepts identified",
                        criteria="Key domain concepts are identified and documented",
                        test_scenario="Review domain concept documentation"
                    ),
                    AcceptanceCriterion(
                        id="ac-4",
                        description="Business rules documented",
                        criteria="Business rules are documented and validated",
                        test_scenario="Review business rules documentation"
                    )
                ]
            ),
            UserStory(
                id="ddd-story-2-" + datetime.now().strftime("%Y%m%d-%H%M%S"),
                title="Create Bounded Context Map",
                description="As a domain architect, I want to create a bounded context map for the customer API, so that I can clearly define domain boundaries and relationships.",
                story_type=StoryType.USER_STORY,
                priority=Priority.HIGH,
                status=StoryStatus.NEW,
                acceptance_criteria=[
                    AcceptanceCriterion(
                        id="ac-5",
                        description="Bounded contexts identified",
                        criteria="All bounded contexts are identified and documented",
                        test_scenario="Review bounded context documentation"
                    ),
                    AcceptanceCriterion(
                        id="ac-6",
                        description="Context relationships mapped",
                        criteria="Relationships between contexts are mapped and documented",
                        test_scenario="Review context relationship documentation"
                    ),
                    AcceptanceCriterion(
                        id="ac-7",
                        description="Context map visualized",
                        criteria="Context map is created and visualized",
                        test_scenario="Review context map visualization"
                    ),
                    AcceptanceCriterion(
                        id="ac-8",
                        description="Integration patterns defined",
                        criteria="Integration patterns between contexts are defined",
                        test_scenario="Review integration pattern documentation"
                    )
                ]
            ),
            UserStory(
                id="ddd-story-3-" + datetime.now().strftime("%Y%m%d-%H%M%S"),
                title="Generate Domain Models and Entities",
                description="As a domain architect, I want to generate domain models and entities for each bounded context, so that I can establish clear domain boundaries and responsibilities.",
                story_type=StoryType.USER_STORY,
                priority=Priority.HIGH,
                status=StoryStatus.NEW,
                acceptance_criteria=[
                    AcceptanceCriterion(
                        id="ac-9",
                        description="Domain entities defined",
                        criteria="All domain entities are defined and documented",
                        test_scenario="Review domain entity documentation"
                    ),
                    AcceptanceCriterion(
                        id="ac-10",
                        description="Value objects identified",
                        criteria="Value objects are identified and documented",
                        test_scenario="Review value object documentation"
                    ),
                    AcceptanceCriterion(
                        id="ac-11",
                        description="Aggregates bounded",
                        criteria="Aggregate boundaries are defined and documented",
                        test_scenario="Review aggregate boundary documentation"
                    ),
                    AcceptanceCriterion(
                        id="ac-12",
                        description="Domain services specified",
                        criteria="Domain services are specified and documented",
                        test_scenario="Review domain service documentation"
                    )
                ]
            ),
            UserStory(
                id="ddd-story-4-" + datetime.now().strftime("%Y%m%d-%H%M%S"),
                title="Align with SCB's ECM Principles",
                description="As a domain architect, I want to ensure the DDD design aligns with SCB's Enterprise Context Mapping principles, so that the solution fits within the enterprise architecture.",
                story_type=StoryType.USER_STORY,
                priority=Priority.HIGH,
                status=StoryStatus.NEW,
                acceptance_criteria=[
                    AcceptanceCriterion(
                        id="ac-13",
                        description="ECM guidelines followed",
                        criteria="All SCB ECM guidelines are followed and documented",
                        test_scenario="Review ECM compliance documentation"
                    ),
                    AcceptanceCriterion(
                        id="ac-14",
                        description="Enterprise patterns applied",
                        criteria="Enterprise patterns are applied and documented",
                        test_scenario="Review enterprise pattern documentation"
                    ),
                    AcceptanceCriterion(
                        id="ac-15",
                        description="Integration standards met",
                        criteria="Integration standards are met and documented",
                        test_scenario="Review integration standard compliance"
                    ),
                    AcceptanceCriterion(
                        id="ac-16",
                        description="Governance requirements satisfied",
                        criteria="All governance requirements are satisfied and documented",
                        test_scenario="Review governance compliance documentation"
                    )
                ]
            )
        ]
        
        print(f"   ✅ Feature created: {ddd_feature.name}")
        print(f"   ✅ User stories created: {len(ddd_stories)} stories")
        
        # Initialize the workflow
        print("\n3. Initializing Product Lifecycle Workflow...")
        
        # Create configuration for the workflow
        workflow_config = {
            "llm_model": config.get("LLM_MODEL", "gpt-4o-mini"),
            "llm_temperature": float(config.get("LLM_TEMPERATURE", "0.7")),
            "ado_organization": config.get("ADO_ORGANIZATION", ""),
            "ado_project": config.get("ADO_PROJECT", ""),
            "ado_pat": config.get("ADO_PAT", ""),
            "kubeconfig_path": config.get("KUBECONFIG_PATH", ""),
            "in_cluster": config.get("IN_CLUSTER", "false").lower() == "true"
        }
        
        workflow = ProductLifecycleWorkflow(workflow_config)
        print("   ✅ Workflow initialized")
        
        # Execute the workflow for DDD generation
        print("\n4. Executing workflow for DDD generation...")
        
        workflow_id = f"ddd_generation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Start the workflow
        feature_request = {
            "feature_name": ddd_feature.name,
            "feature_description": ddd_feature.description,
            "feature_priority": ddd_feature.priority.value,
            "feature_business_requirements": ddd_feature.business_requirements,
            "feature_technical_requirements": ddd_feature.technical_requirements,
            "user_stories": [
                {
                    "title": story.title,
                    "description": story.description,
                    "priority": story.priority.value,
                    "acceptance_criteria": [ac.description for ac in story.acceptance_criteria]
                }
                for story in ddd_stories
            ],
            "workflow_id": workflow_id
        }
        
        result = await workflow.execute_workflow(feature_request)
        
        if result:
            print("   ✅ Workflow execution started")
            print(f"   Workflow ID: {workflow_id}")
            
            # Get workflow status
            status = await workflow.get_workflow_status(workflow_id)
            if status:
                print(f"   Current Status: {status.status}")
                print(f"   Current Step: {status.current_step}")
                print(f"   Created At: {status.created_at}")
                
                if status.errors:
                    print(f"   Errors: {len(status.errors)}")
                    for error in status.errors[:3]:  # Show first 3 errors
                        print(f"     - {error}")
                
                if status.bounded_contexts:
                    print(f"   Bounded Contexts: {len(status.bounded_contexts)}")
                    for ctx in status.bounded_contexts:
                        print(f"     - {ctx.name}: {ctx.description[:100]}...")
                
                if status.openapi_spec:
                    print(f"   OpenAPI Spec: Generated")
                    print(f"     - Title: {status.openapi_spec.title}")
                    print(f"     - Version: {status.openapi_spec.version}")
                    print(f"     - Endpoints: {len(status.openapi_spec.paths) if status.openapi_spec.paths else 0}")
                
                if status.spring_boot_service:
                    print(f"   Spring Boot Service: Generated")
                    print(f"     - Service Name: {status.spring_boot_service.service_name}")
                    print(f"     - Package: {status.spring_boot_service.package_name}")
                
            else:
                print("   ⚠️  Could not retrieve workflow status")
        else:
            print("   ❌ Workflow execution failed")
            return False
        
        print("\n" + "="*70)
        print("🎉 DDD GENERATION TEST COMPLETED!")
        print("="*70)
        
        print(f"\n📋 Test Results Summary:")
        print(f"   ✅ Feature Creation: SUCCESS")
        print(f"   ✅ User Stories: {len(ddd_stories)} created")
        print(f"   ✅ Workflow Execution: STARTED")
        print(f"   ✅ Workflow ID: {workflow_id}")
        
        print(f"\n🔗 View Workflow in Azure DevOps:")
        print(f"   DOD Step 1 Epic: https://dev.azure.com/ddhasaprakash/agentic-test/_workitems/edit/6")
        
        print(f"\n💡 Next Steps:")
        print(f"   1. Monitor workflow progress in the system")
        print(f"   2. Review generated DDD models and bounded contexts")
        print(f"   3. Validate the design against SCB's ECM principles")
        print(f"   4. Proceed to DOD Step 2: Generate CML from Existing API Spec")
        print(f"   5. Use the generated DDD design as foundation for CML generation")
        
        return True
        
    except Exception as e:
        print(f"❌ DDD generation test failed: {str(e)}")
        logger.error(f"DDD generation test error: {str(e)}", exc_info=True)
        return False


async def main():
    """Main test execution."""
    print("🚀 Agentic AI Architect - DDD Generation Test for API Refactoring")
    
    success = await test_ddd_generation()
    
    if success:
        print("\n✅ DDD generation test completed successfully!")
        print("   The workflow has been started to generate DDD design for your API refactoring project.")
        print("   You can now monitor progress and review the generated artifacts.")
    else:
        print("\n❌ DDD generation test failed!")
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
