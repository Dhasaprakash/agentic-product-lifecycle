#!/usr/bin/env python3
"""
Run Ideation Workflow - Simple Command Line Interface
Quick way to run the ideation workflow with minimal input
"""

import asyncio
import os
import sys
from agents.ideation import IdeationAgent
from services.ado_client import AzureDevOpsClient
from models.domain import IdeationRequest, Priority

def load_config():
    """Load configuration from environment."""
    config = {}
    
    # Try to load from test_config.env first
    if os.path.exists("test_config.env"):
        with open("test_config.env", 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key] = value
    
    # Override with environment variables
    for key in ['ADO_ORGANIZATION', 'ADO_PROJECT', 'ADO_PAT', 'OPENAI_API_KEY', 'LLM_MODEL']:
        env_value = os.getenv(key)
        if env_value:
            config[key] = env_value
    
    # Set environment variables for OpenAI
    if config.get('OPENAI_API_KEY'):
        os.environ['OPENAI_API_KEY'] = config['OPENAI_API_KEY']
    
    return config

async def quick_ideation():
    """Run a quick ideation workflow with predefined input."""
    try:
        # Load configuration
        config = load_config()
        
        # Check required configuration
        required = ['ADO_ORGANIZATION', 'ADO_PROJECT', 'ADO_PAT', 'OPENAI_API_KEY']
        missing = [key for key in required if not config.get(key)]
        
        if missing:
            print(f"❌ Missing required configuration: {missing}")
            print("Please set these environment variables or create test_config.env")
            return False
        
        print("🚀 Quick Ideation Workflow - AI-Powered Customer Service Enhancement")
        print("="*70)
        
        # Initialize Azure DevOps client
        ado_client = AzureDevOpsClient(
            organization=config["ADO_ORGANIZATION"],
            project=config["ADO_PROJECT"],
            personal_access_token=config["ADO_PAT"]
        )
        
        # Initialize Ideation Agent
        ideation_agent = IdeationAgent(
            llm_model=config.get("LLM_MODEL", "gpt-4o-mini"),
            temperature=0.7,
            ado_client=ado_client
        )
        
        # Create predefined ideation request
        ideation_request = IdeationRequest(
            feature_name="AI-Powered Customer Service Enhancement",
            description="""Enhance the customer service system with AI-powered features including:
            - Automated ticket classification and routing
            - Smart response suggestions for agents
            - Customer sentiment analysis
            - Predictive issue resolution
            - Integration with knowledge base for faster solutions""",
            business_context="""Improve customer satisfaction scores by 25%, reduce average resolution time by 40%, 
            and increase agent productivity by 30% through AI-assisted workflows.""",
            target_users=["Customer service agents", "Team leads", "Customer service managers"],
            priority=Priority.HIGH,
            success_metrics=["25% improvement in customer satisfaction", "40% reduction in resolution time", "30% increase in agent productivity"]
        )
        
        print("✅ Configuration loaded and agents initialized")
        print("🤖 Running AI-powered ideation workflow...")
        
        # Run the workflow
        workflow_result = await ideation_agent.create_azure_devops_workflow(ideation_request)
        
        if workflow_result["status"] == "success":
            print("\n🎉 WORKFLOW COMPLETED SUCCESSFULLY!")
            print("="*50)
            print(f"🏗️  Epic: {workflow_result['epic_id']}")
            print(f"🎯 Feature: {workflow_result['feature_id']}")
            print(f"📝 Stories: {workflow_result['stories_created']}")
            print(f"✅ Tasks: {workflow_result['tasks_created']}")
            print(f"📊 Story Points: {workflow_result['total_story_points']}")
            
            print(f"\n🔗 View in Azure DevOps:")
            print(f"   Epic: https://dev.azure.com/{config['ADO_ORGANIZATION']}/{config['ADO_PROJECT']}/_workitems/edit/{workflow_result['epic_id']}")
            print(f"   Feature: https://dev.azure.com/{config['ADO_ORGANIZATION']}/{config['ADO_PROJECT']}/_workitems/edit/{workflow_result['feature_id']}")
            
            return True
        else:
            print(f"❌ Workflow failed: {workflow_result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Quick ideation failed: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(quick_ideation())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Failed: {str(e)}")
        sys.exit(1)
