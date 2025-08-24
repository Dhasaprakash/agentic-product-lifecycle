#!/usr/bin/env python3
"""
Test Ideation Workflow - Complete End-to-End Testing
Tests the new ideation agent that creates Azure DevOps work items from user input
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.ideation import IdeationAgent
from services.ado_client import AzureDevOpsClient
from models.domain import IdeationRequest, Priority

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


def get_user_input() -> IdeationRequest:
    """Get feature idea input from user."""
    print("\n🚀 AGENTIC AI ARCHITECT - FEATURE IDEATION WORKFLOW")
    print("="*70)
    print("This workflow will:")
    print("1. Take your feature idea as input")
    print("2. Use AI to groom and structure it")
    print("3. Create Epic, Feature, User Stories, and Tasks in Azure DevOps")
    print("4. Establish proper hierarchical relationships")
    print("="*70)
    
    # Get feature details from user
    feature_name = input("\n📝 Enter your feature name: ").strip()
    if not feature_name:
        feature_name = "AI-Powered Customer Service Enhancement"
        print(f"   Using default: {feature_name}")
    
    description = input("\n📋 Describe your feature idea: ").strip()
    if not description:
        description = """Enhance the customer service system with AI-powered features including:
        - Automated ticket classification and routing
        - Smart response suggestions for agents
        - Customer sentiment analysis
        - Predictive issue resolution
        - Integration with knowledge base for faster solutions"""
        print(f"   Using default description")
    
    business_context = input("\n💼 Business context/justification: ").strip()
    if not business_context:
        business_context = """Improve customer satisfaction scores by 25%, reduce average resolution time by 40%, 
        and increase agent productivity by 30% through AI-assisted workflows."""
        print(f"   Using default business context")
    
    target_users = input("\n👥 Target users: ").strip()
    if not target_users:
        target_users = "Customer service agents, team leads, customer service managers"
        print(f"   Using default target users")
    
    priority_input = input("\n🎯 Priority (Low/Medium/High/Critical): ").strip().lower()
    priority_map = {
        "low": Priority.LOW,
        "medium": Priority.MEDIUM,
        "high": Priority.HIGH,
        "critical": Priority.CRITICAL
    }
    priority = priority_map.get(priority_input, Priority.MEDIUM)
    
    return IdeationRequest(
        feature_name=feature_name,
        description=description,
        business_context=business_context,
        target_users=target_users,
        priority=priority,
        technical_constraints="",
        dependencies=[],
        success_metrics=""
    )


async def test_ideation_workflow():
    """Test the complete ideation workflow."""
    try:
        # Load configuration
        config = load_config_from_file()
        
        print(f"\n🔧 Configuration:")
        print(f"   Organization: {config.get('ADO_ORGANIZATION', 'Not set')}")
        print(f"   Project: {config.get('ADO_PROJECT', 'Not set')}")
        print(f"   LLM Model: {config.get('LLM_MODEL', 'gpt-4o-mini')}")
        
        # Initialize Azure DevOps client
        print(f"\n1. Initializing Azure DevOps client...")
        ado_client = AzureDevOpsClient(
            organization=config["ADO_ORGANIZATION"],
            project=config["ADO_PROJECT"],
            personal_access_token=config["ADO_PAT"]
        )
        print("✅ Azure DevOps client initialized")
        
        # Initialize Ideation Agent with Azure DevOps integration
        print(f"\n2. Initializing Ideation Agent...")
        ideation_agent = IdeationAgent(
            llm_model=config.get("LLM_MODEL", "gpt-4o-mini"),
            temperature=0.7,
            ado_client=ado_client
        )
        print("✅ Ideation Agent initialized with Azure DevOps integration")
        
        # Get user input
        print(f"\n3. Getting feature idea input...")
        ideation_request = get_user_input()
        print("✅ Feature idea captured")
        
        # Validate the feature idea
        print(f"\n4. Validating feature idea...")
        validation_result = await ideation_agent.validate_feature_idea(ideation_request)
        
        if not validation_result["is_valid"]:
            print("❌ Feature idea validation failed:")
            for error in validation_result["errors"]:
                print(f"   - {error}")
            return False
        
        if validation_result["warnings"]:
            print("⚠️  Feature idea has warnings:")
            for warning in validation_result["warnings"]:
                print(f"   - {warning}")
        
        print("✅ Feature idea validated")
        
        # Create the complete Azure DevOps workflow
        print(f"\n5. Creating Azure DevOps workflow...")
        print("   This will:")
        print("   - Generate feature breakdown using AI")
        print("   - Create Epic in Azure DevOps")
        print("   - Create Feature linked to Epic")
        print("   - Create User Stories with Acceptance Criteria")
        print("   - Create linked Tasks for each Acceptance Criterion")
        
        workflow_result = await ideation_agent.create_azure_devops_workflow(ideation_request)
        
        if workflow_result["status"] == "success":
            print("\n🎉 AZURE DEVOPS WORKFLOW CREATED SUCCESSFULLY!")
            print("="*70)
            
            # Display results
            print(f"\n📋 Workflow Results:")
            print(f"   🏗️  Epic: {workflow_result['epic_id']}")
            print(f"   🎯 Feature: {workflow_result['feature_id']}")
            print(f"   📝 User Stories: {workflow_result['stories_created']} created")
            print(f"   ✅ Tasks: {workflow_result['tasks_created']} created")
            print(f"   📊 Total Story Points: {workflow_result['total_story_points']}")
            
            # Display ideation summary
            ideation_summary = workflow_result["ideation_summary"]
            print(f"\n🤖 AI-Generated Ideation Summary:")
            print(f"   Feature: {ideation_summary['feature_name']}")
            print(f"   Epic: {ideation_summary['epic_title']}")
            print(f"   User Stories: {ideation_summary['user_stories_count']}")
            print(f"   Bounded Contexts: {ideation_summary['bounded_contexts_count']}")
            print(f"   Estimated Effort: {ideation_summary['estimated_effort']}")
            
            if ideation_summary['risks']:
                print(f"\n⚠️  Identified Risks:")
                for risk in ideation_summary['risks']:
                    print(f"   - {risk}")
            
            if ideation_summary['recommendations']:
                print(f"\n💡 Recommendations:")
                for rec in ideation_summary['recommendations']:
                    print(f"   - {rec}")
            
            # Display Azure DevOps links
            print(f"\n🔗 View Work Items in Azure DevOps:")
            print(f"   Epic: https://dev.azure.com/{config['ADO_ORGANIZATION']}/{config['ADO_PROJECT']}/_workitems/edit/{workflow_result['epic_id']}")
            print(f"   Feature: https://dev.azure.com/{config['ADO_ORGANIZATION']}/{config['ADO_PROJECT']}/_workitems/edit/{workflow_result['feature_id']}")
            
            print(f"\n🎯 Workflow Status: SUCCESS")
            print(f"   Complete Epic → Feature → Stories → Tasks hierarchy created")
            print(f"   All work items properly linked using Azure DevOps Relations")
            print(f"   Ready for sprint planning and development")
            
            return True
            
        else:
            print(f"\n❌ Azure DevOps workflow creation failed:")
            print(f"   Error: {workflow_result.get('error', 'Unknown error')}")
            return False
        
    except Exception as e:
        print(f"❌ Ideation workflow test failed: {str(e)}")
        logger.error(f"Workflow test error: {str(e)}", exc_info=True)
        return False


async def main():
    """Main test execution."""
    print("🚀 Agentic AI Architect - Test Complete Ideation Workflow")
    
    success = await test_ideation_workflow()
    
    if success:
        print("\n✅ Ideation workflow test completed successfully!")
        print("   Your feature idea has been transformed into a complete Azure DevOps project structure.")
    else:
        print("\n❌ Ideation workflow test failed!")
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
