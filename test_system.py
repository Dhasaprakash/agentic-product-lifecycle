#!/usr/bin/env python3
"""
Test script for the Agentic AI Architect system.
This script demonstrates the basic functionality without requiring external services.
"""

import asyncio
import logging
import os
import sys
from typing import Dict, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.domain import IdeationRequest, Priority
from agents.ideation import IdeationAgent
from agents.design import DesignAgent
from agents.codegen import CodeGenerationAgent
from agents.deployment import DeploymentAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_ideation_agent():
    """Test the Ideation Agent."""
    print("\n" + "="*50)
    print("Testing Ideation Agent")
    print("="*50)
    
    try:
        # Create ideation agent
        agent = IdeationAgent()
        
        # Create test request
        request = IdeationRequest(
            feature_name="User Authentication System",
            description="Implement secure user authentication with OAuth2, JWT tokens, and role-based access control",
            priority=Priority.HIGH,
            business_context="Need to secure our application and provide single sign-on capabilities",
            target_users=["End users", "Administrators", "API consumers"],
            success_metrics=["Reduced security incidents", "Improved user experience", "Compliance with security standards"],
            constraints=["Must integrate with existing identity providers", "Should support multi-factor authentication"]
        )
        
        print(f"Feature Request: {request.feature_name}")
        print(f"Description: {request.description}")
        print(f"Priority: {request.priority}")
        
        # Generate feature breakdown
        print("\nGenerating feature breakdown...")
        response = await agent.generate_feature_breakdown(request)
        
        print(f"\n✅ Ideation completed successfully!")
        print(f"Generated {len(response.user_stories)} user stories")
        print(f"Created {len(response.bounded_contexts)} bounded contexts")
        print(f"Estimated effort: {response.estimated_effort}")
        
        if response.risks:
            print(f"Identified risks: {len(response.risks)}")
        
        if response.recommendations:
            print(f"Recommendations: {len(response.recommendations)}")
        
        return response
        
    except Exception as e:
        print(f"❌ Ideation Agent test failed: {str(e)}")
        return None


async def test_design_agent(ideation_response):
    """Test the Design Agent."""
    print("\n" + "="*50)
    print("Testing Design Agent")
    print("="*50)
    
    if not ideation_response:
        print("❌ Skipping Design Agent test - no ideation response")
        return None
    
    try:
        # Create design agent
        agent = DesignAgent()
        
        print("Generating DDD model...")
        ddd_model = await agent.generate_ddd_model(
            ideation_response.feature,
            ideation_response.bounded_contexts
        )
        
        print(f"\n✅ Design Agent test completed successfully!")
        print(f"Generated DDD model for feature: {ddd_model['feature_name']}")
        print(f"Created {len(ddd_model['bounded_contexts'])} detailed bounded contexts")
        print(f"Generated Context Mapper DSL: {len(ddd_model['context_mapper_dsl'])} characters")
        print(f"Generated {len(ddd_model['domain_diagrams'])} domain diagrams")
        
        # Validate the model
        validation_result = await agent.validate_ddd_model(ddd_model)
        if validation_result["is_valid"]:
            print("✅ DDD model validation passed")
        else:
            print(f"⚠️ DDD model validation warnings: {validation_result['warnings']}")
        
        return ddd_model
        
    except Exception as e:
        print(f"❌ Design Agent test failed: {str(e)}")
        return None


async def test_code_generation_agent(ideation_response, ddd_model):
    """Test the Code Generation Agent."""
    print("\n" + "="*50)
    print("Testing Code Generation Agent")
    print("="*50)
    
    if not ideation_response or not ddd_model:
        print("❌ Skipping Code Generation Agent test - missing required data")
        return None
    
    try:
        # Create code generation agent
        agent = CodeGenerationAgent()
        
        print("Generating Spring Boot microservice...")
        generated_code = await agent.generate_microservice(
            ideation_response.feature,
            ideation_response.user_stories,
            ideation_response.bounded_contexts
        )
        
        print(f"\n✅ Code Generation Agent test completed successfully!")
        print(f"Generated microservice for feature: {generated_code['feature_name']}")
        print(f"Generated OpenAPI spec: {len(str(generated_code['openapi_spec']))} characters")
        print(f"Generated {len(generated_code['domain_models'])} domain models")
        print(f"Generated {len(generated_code['repositories'])} repositories")
        print(f"Generated {len(generated_code['services'])} services")
        print(f"Generated {len(generated_code['controllers'])} controllers")
        print(f"Generated {len(generated_code['tests'])} test classes")
        print(f"Generated {len(generated_code['config_files'])} configuration files")
        
        # Validate the generated code
        validation_result = await agent.validate_generated_code(generated_code)
        if validation_result["is_valid"]:
            print("✅ Generated code validation passed")
        else:
            print(f"⚠️ Generated code validation warnings: {validation_result['warnings']}")
        
        return generated_code
        
    except Exception as e:
        print(f"❌ Code Generation Agent test failed: {str(e)}")
        return None


async def test_deployment_agent(ideation_response, generated_code):
    """Test the Deployment Agent."""
    print("\n" + "="*50)
    print("Testing Deployment Agent")
    print("="*50)
    
    if not ideation_response or not generated_code:
        print("❌ Skipping Deployment Agent test - missing required data")
        return None
    
    try:
        # Create deployment agent (without K8s client for demo)
        from services.kubernetes import KubernetesClient
        
        # Create a mock K8s client
        class MockKubernetesClient:
            def __init__(self):
                pass
            
            def create_namespace(self, namespace):
                return True
            
            def deploy_service(self, deployment_config):
                return True
        
        mock_k8s_client = MockKubernetesClient()
        agent = DeploymentAgent(mock_k8s_client)
        
        print("Generating deployment configuration...")
        deployment_config = await agent.generate_deployment_config(
            ideation_response.feature,
            generated_code['spring_boot_service'],
            generated_code['openapi_spec']
        )
        
        print(f"\n✅ Deployment Agent test completed successfully!")
        print(f"Generated deployment config for service: {deployment_config['deployment_config'].service_name}")
        print(f"Generated {len(deployment_config['kubernetes_manifests'])} Kubernetes manifests")
        print(f"Generated Helm chart with {len(deployment_config['helm_chart']['templates'])} templates")
        print(f"Generated {len(deployment_config['docker_config'])} Docker configuration files")
        print(f"Generated {len(deployment_config['cicd_pipeline'])} CI/CD pipeline configurations")
        print(f"Generated {len(deployment_config['monitoring_config'])} monitoring configurations")
        
        # Validate the deployment configuration
        validation_result = await agent.validate_deployment_config(deployment_config)
        if validation_result["is_valid"]:
            print("✅ Deployment configuration validation passed")
        else:
            print(f"⚠️ Deployment configuration validation warnings: {validation_result['warnings']}")
        
        return deployment_config
        
    except Exception as e:
        print(f"❌ Deployment Agent test failed: {str(e)}")
        return None


async def run_demo_workflow():
    """Run a complete demo workflow."""
    print("\n" + "="*60)
    print("🚀 AGENTIC AI ARCHITECT SYSTEM DEMO")
    print("="*60)
    print("This demo will test all agents in sequence to show the complete workflow.")
    print("Note: This is a demonstration without external service connections.")
    
    try:
        # Test each agent in sequence
        ideation_response = await test_ideation_agent()
        ddd_model = await test_design_agent(ideation_response)
        generated_code = await test_code_generation_agent(ideation_response, ddd_model)
        deployment_config = await test_deployment_agent(ideation_response, generated_code)
        
        # Summary
        print("\n" + "="*60)
        print("📊 DEMO WORKFLOW SUMMARY")
        print("="*60)
        
        if all([ideation_response, ddd_model, generated_code, deployment_config]):
            print("✅ All agents completed successfully!")
            print(f"📝 Generated {len(ideation_response.user_stories)} user stories")
            print(f"🏗️ Created DDD model with {len(ddd_model['bounded_contexts'])} bounded contexts")
            print(f"💻 Generated Spring Boot microservice with {len(generated_code['controllers'])} controllers")
            print(f"🚢 Created deployment configuration with Helm charts and K8s manifests")
            print("\n🎉 The Agentic AI Architect system is working correctly!")
        else:
            print("❌ Some agents failed during the demo")
            print("Check the logs above for specific error details")
        
    except Exception as e:
        print(f"\n❌ Demo workflow failed: {str(e)}")
        logger.exception("Demo workflow error")


def main():
    """Main function to run the demo."""
    print("Starting Agentic AI Architect System Demo...")
    print("Make sure you have set the OPENAI_API_KEY environment variable")
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  WARNING: OPENAI_API_KEY environment variable not set!")
        print("Please set it before running the demo:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        print("\nThe demo will attempt to run but may fail without the API key.")
    
    # Run the demo
    asyncio.run(run_demo_workflow())


if __name__ == "__main__":
    main()
