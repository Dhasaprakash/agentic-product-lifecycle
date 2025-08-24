#!/usr/bin/env python3
"""
Test Complete Workflow - End-to-End Testing
Tests the complete workflow from ideation to human approval
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from workflows.lifecycle import ProductLifecycleWorkflow
from models.domain import IdeationRequest, Priority
from agents.ideation import LLMFactory, LLMProvider

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
    
    # Set environment variables for all LLM providers
    api_keys = {
        'OPENAI_API_KEY': 'OPENAI_API_KEY',
        'ANTHROPIC_API_KEY': 'ANTHROPIC_API_KEY',
        'MISTRAL_API_KEY': 'MISTRAL_API_KEY',
        'PERPLEXITY_API_KEY': 'PERPLEXITY_API_KEY',
        'GROQ_API_KEY': 'GROQ_API_KEY'  # For Grok models
    }
    
    for env_var, config_key in api_keys.items():
        if config.get(config_key):
            os.environ[env_var] = config[config_key]
            logger.info(f"Set {env_var} from config")
        else:
            logger.warning(f"Missing {env_var} in config")
    
    return config


def display_available_models():
    """Display all available models for quick reference."""
    print("\n📚 AVAILABLE LLM MODELS QUICK REFERENCE")
    print("="*60)
    
    supported_models = LLMFactory.get_supported_models()
    
    for provider, models in supported_models.items():
        print(f"\n{provider.upper()}:")
        for i, model in enumerate(models, 1):
            print(f"   {i:2d}. {model}")
    
    print("\n💡 Tips:")
    print("   • OpenAI: Best quality, higher cost")
    print("   • Anthropic: Safety-focused, balanced cost")
    print("   • Mistral: Fast, cost-effective")
    print("   • Perplexity: Research-focused, variable pricing")
    print("   • Grok: Fastest, most cost-effective")
    print("   • Groq: Fast, very cost-effective, direct access")


def get_user_model_selection() -> str:
    """Get LLM model selection from user."""
    print("\n🤖 LLM MODEL SELECTION")
    print("="*50)
    print("Choose your preferred LLM provider and model:")
    print("This will be used for AI-powered ideation and feature breakdown.")
    print("="*50)
    
    # Ask if user wants to see all available models
    show_models = input("\n📚 Would you like to see all available models? (y/n): ").strip().lower()
    if show_models in ['y', 'yes']:
        display_available_models()
    
    # Get supported models by provider
    supported_models = LLMFactory.get_supported_models()
    
    # Display available providers
    providers = list(supported_models.keys())
    for i, provider in enumerate(providers, 1):
        print(f"{i}. {provider.upper()}")
    
    # Quick selection for common models
    print(f"\n🚀 Quick Selection (Common Models):")
    print(f"   q1. OpenAI GPT-4o-mini (Fast, cost-effective)")
    print(f"   q2. Anthropic Claude-3-Haiku (Balanced)")
    print(f"   q3. Mistral Large (Fast, multilingual)")
    print(f"   q4. Grok-1 (Fastest, most cost-effective)")
    print(f"   q5. Groq Llama3-8b (Fast, cost-effective)")
    
    # Get provider selection
    while True:
        try:
            choice = input(f"\n🎯 Select provider (1-{len(providers)}) or quick selection (q1-q5): ").strip().lower()
            
            # Handle quick selections
            if choice == 'q1':
                selected_provider = 'openai'
                selected_model = 'gpt-4o-mini'
                print(f"\n✅ Quick selection: OpenAI - {selected_model}")
                break
            elif choice == 'q2':
                selected_provider = 'anthropic'
                selected_model = 'claude-3-haiku-20240307'
                print(f"\n✅ Quick selection: Anthropic - {selected_model}")
                break
            elif choice == 'q3':
                selected_provider = 'mistral'
                selected_model = 'mistral-large-latest'
                print(f"\n✅ Quick selection: Mistral - {selected_model}")
                break
            elif choice == 'q4':
                selected_provider = 'grok'
                selected_model = 'grok-1'
                print(f"\n✅ Quick selection: Grok - {selected_model}")
                break
            elif choice == 'q5':
                selected_provider = 'groq'
                selected_model = 'llama3-8b-8192'
                print(f"\n✅ Quick selection: Groq - {selected_model}")
                break
            
            # Handle regular provider selection
            provider_idx = int(choice) - 1
            if 0 <= provider_idx < len(providers):
                selected_provider = providers[provider_idx]
                break
            else:
                print(f"❌ Please enter a valid choice")
        except ValueError:
            print("❌ Please enter a valid choice")
    
    # If quick selection was used, return the model directly
    if 'selected_model' in locals():
        # Check if API key is available for selected provider
        api_key_env = f"{selected_provider.upper()}_API_KEY"
        if selected_provider == "grok":
            api_key_env = "GROQ_API_KEY"
        
        api_key = os.getenv(api_key_env)
        if not api_key:
            print(f"⚠️  Warning: {api_key_env} not set. The workflow may fail.")
            print(f"   Please add {api_key_env} to your test_config.env file")
        
        return selected_model
    
    # Display models for selected provider
    print(f"\n📋 Available {selected_provider.upper()} models:")
    provider_models = supported_models[selected_provider]
    
    for i, model in enumerate(provider_models, 1):
        print(f"   {i:2d}. {model}")
    
    # Get model selection
    while True:
        try:
            model_choice = input(f"\n🎯 Select model (1-{len(provider_models)}): ").strip()
            model_idx = int(model_choice) - 1
            
            if 0 <= model_idx < len(provider_models):
                selected_model = provider_models[model_idx]
                break
            else:
                print(f"❌ Please enter a number between 1 and {len(provider_models)}")
        except ValueError:
            print("❌ Please enter a valid number")
    
    print(f"\n✅ Selected: {selected_provider.upper()} - {selected_model}")
    
    # Check if API key is available for selected provider
    api_key_env = f"{selected_provider.upper()}_API_KEY"
    if selected_provider == "grok":
        api_key_env = "GROQ_API_KEY"
    
    api_key = os.getenv(api_key_env)
    if not api_key:
        print(f"⚠️  Warning: {api_key_env} not set. The workflow may fail.")
        print(f"   Please add {api_key_env} to your test_config.env file")
    
    return selected_model


def get_user_feature_input() -> IdeationRequest:
    """Get feature idea input from user."""
    print("\n🚀 AGENTIC AI ARCHITECT - COMPLETE WORKFLOW TEST")
    print("="*70)
    print("This will test the complete workflow:")
    print("1. AI-powered ideation with Azure DevOps integration")
    print("2. Human approval step with user input")
    print("3. Complete workflow execution")
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
    
    target_users = input("\n👥 Target users (comma-separated): ").strip()
    if not target_users:
        target_users = ["Customer service agents", "Team leads", "Customer service managers"]
        print(f"   Using default target users")
    else:
        target_users = [user.strip() for user in target_users.split(",")]
    
    priority_input = input("\n🎯 Priority (Low/Medium/High/Critical): ").strip().lower()
    priority_map = {
        "low": Priority.LOW,
        "medium": Priority.MEDIUM,
        "high": Priority.HIGH,
        "critical": Priority.CRITICAL
    }
    priority = priority_map.get(priority_input, Priority.MEDIUM)
    
    success_metrics = input("\n📊 Success metrics (comma-separated): ").strip()
    if not success_metrics:
        success_metrics = ["25% improvement in customer satisfaction", "40% reduction in resolution time", "30% increase in agent productivity"]
        print(f"   Using default success metrics")
    else:
        success_metrics = [metric.strip() for metric in success_metrics.split(",")]
    
    return IdeationRequest(
        feature_name=feature_name,
        description=description,
        business_context=business_context,
        target_users=target_users,
        priority=priority,
        success_metrics=success_metrics
    )


async def test_complete_workflow():
    """Test the complete workflow from ideation to human approval."""
    try:
        # Load configuration
        config = load_config_from_file()
        
        print(f"\n🔧 Configuration:")
        print(f"   Organization: {config.get('ADO_ORGANIZATION', 'Not set')}")
        print(f"   Project: {config.get('ADO_PROJECT', 'Not set')}")
        
        # Check required configuration
        required = ['ADO_ORGANIZATION', 'ADO_PROJECT', 'ADO_PAT']
        missing = [key for key in required if not config.get(key)]
        
        if missing:
            print(f"❌ Missing required configuration: {missing}")
            print("Please set these environment variables or create test_config.env")
            return False
        
        # Get user model selection
        selected_model = get_user_model_selection()
        
        # Get user feature input
        ideation_request = get_user_feature_input()
        print("✅ Feature idea captured")
        
        # Initialize workflow
        print(f"\n1. Initializing Product Lifecycle Workflow...")
        workflow_config = {
            "llm_model": selected_model,
            "llm_temperature": 0.7,
            "ado_organization": config["ADO_ORGANIZATION"],
            "ado_project": config["ADO_PROJECT"],
            "ado_pat": config["ADO_PAT"]
        }
        
        # Add API key based on selected model provider and set environment variables
        provider = LLMFactory.get_provider_from_model(selected_model)
        print(f"   Provider detected: {provider}")
        
        if provider == LLMProvider.OPENAI:
            api_key = config.get("OPENAI_API_KEY")
            workflow_config["openai_api_key"] = api_key
            if api_key:
                os.environ["OPENAI_API_KEY"] = api_key
                print(f"   ✅ Set OPENAI_API_KEY environment variable")
            else:
                print(f"   ⚠️  OPENAI_API_KEY not found in config")
        elif provider == LLMProvider.ANTHROPIC:
            api_key = config.get("ANTHROPIC_API_KEY")
            workflow_config["anthropic_api_key"] = api_key
            if api_key:
                os.environ["ANTHROPIC_API_KEY"] = api_key
                print(f"   ✅ Set ANTHROPIC_API_KEY environment variable")
            else:
                print(f"   ⚠️  ANTHROPIC_API_KEY not found in config")
        elif provider == LLMProvider.MISTRAL:
            api_key = config.get("MISTRAL_API_KEY")
            workflow_config["mistral_api_key"] = api_key
            if api_key:
                os.environ["MISTRAL_API_KEY"] = api_key
                print(f"   ✅ Set MISTRAL_API_KEY environment variable")
            else:
                print(f"   ⚠️  MISTRAL_API_KEY not found in config")
        elif provider == LLMProvider.PERPLEXITY:
            api_key = config.get("PERPLEXITY_API_KEY")
            workflow_config["perplexity_api_key"] = api_key
            if api_key:
                os.environ["PERPLEXITY_API_KEY"] = api_key
                print(f"   ✅ Set PERPLEXITY_API_KEY environment variable")
            else:
                print(f"   ⚠️  PERPLEXITY_API_KEY not found in config")
        elif provider == LLMProvider.GROK:
            api_key = config.get("GROQ_API_KEY")
            workflow_config["groq_api_key"] = api_key
            if api_key:
                os.environ["GROQ_API_KEY"] = api_key
                print(f"   ✅ Set GROQ_API_KEY environment variable")
            else:
                print(f"   ⚠️  GROQ_API_KEY not found in config")
        elif provider == LLMProvider.GROQ:
            api_key = config.get("GROQ_API_KEY")
            workflow_config["groq_api_key"] = api_key
            if api_key:
                os.environ["GROQ_API_KEY"] = api_key
                print(f"   ✅ Set GROQ_API_KEY environment variable")
            else:
                print(f"   ⚠️  GROQ_API_KEY not found in config")
        
        # Show current environment variable status for debugging
        print(f"\n🔍 Environment Variable Status:")
        if provider in [LLMProvider.GROK, LLMProvider.GROQ]:
            groq_key = os.getenv("GROQ_API_KEY")
            if groq_key:
                print(f"   ✅ GROQ_API_KEY: {groq_key[:10]}...{groq_key[-4:]}")
            else:
                print(f"   ❌ GROQ_API_KEY: Not set")
        elif provider == LLMProvider.OPENAI:
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key:
                print(f"   ✅ OPENAI_API_KEY: {openai_key[:10]}...{openai_key[-4:]}")
            else:
                print(f"   ❌ OPENAI_API_KEY: Not set")
        
        workflow = ProductLifecycleWorkflow(workflow_config)
        print("✅ Workflow initialized")
        print(f"   Provider detected: {provider}")
        print(f"   ✅ Set {provider.upper()}_API_KEY environment variable")
        
        # Show environment variable status
        print(f"\n🔍 Environment Variable Status:")
        if provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                print(f"   ✅ OPENAI_API_KEY: {api_key[:20]}...{api_key[-4:]}")
            else:
                print(f"   ❌ OPENAI_API_KEY: Not set")
        elif provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                print(f"   ✅ ANTHROPIC_API_KEY: {api_key[:20]}...{api_key[-4:]}")
            else:
                print(f"   ❌ ANTHROPIC_API_KEY: Not set")
        elif provider == "mistral":
            api_key = os.getenv("MISTRAL_API_KEY")
            if api_key:
                print(f"   ✅ MISTRAL_API_KEY: {api_key[:20]}...{api_key[-4:]}")
            else:
                print(f"   ❌ MISTRAL_API_KEY: Not set")
        elif provider == "perplexity":
            api_key = os.getenv("PERPLEXITY_API_KEY")
            if api_key:
                print(f"   ✅ PERPLEXITY_API_KEY: {api_key[:20]}...{api_key[-4:]}")
            else:
                print(f"   ❌ PERPLEXITY_API_KEY: Not set")
        elif provider == "grok":
            api_key = os.getenv("GROQ_API_KEY")
            if api_key:
                print(f"   ✅ GROQ_API_KEY: {api_key[:20]}...{api_key[-4:]}")
            else:
                print(f"   ❌ GROQ_API_KEY: Not set")
        elif provider == "groq":
            api_key = os.getenv("GROQ_API_KEY")
            if api_key:
                print(f"   ✅ GROQ_API_KEY: {api_key[:20]}...{api_key[-4:]}")
            else:
                print(f"   ❌ GROQ_API_KEY: Not set")
        else:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                print(f"   ✅ OPENAI_API_KEY: {api_key[:20]}...{api_key[-4:]}")
            else:
                print(f"   ❌ OPENAI_API_KEY: Not set")
        
        # Create workflow state
        print(f"\n2. Creating workflow state...")
        workflow_state = {
            "workflow_id": f"test-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "current_step": "ideation",
            "status": "new",
            "metadata": {
                "feature_name": ideation_request.feature_name,
                "feature_description": ideation_request.description,
                "priority": ideation_request.priority.value,
                "business_context": ideation_request.business_context,
                "target_users": ideation_request.target_users,
                "success_metrics": ideation_request.success_metrics
            },
            "errors": [],
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        print("✅ Workflow state created")
        
        # Execute workflow
        print(f"\n3. Executing complete workflow...")
        print(f"   Using LLM Model: {selected_model}")
        print(f"   Provider: {provider.upper()}")
        print(f"   This will:")
        print(f"   - Generate AI-powered ideation")
        print(f"   - Create Azure DevOps work items")
        print(f"   - Wait for your approval")
        print(f"   - Continue with design and code generation")
        print(f"   - All steps will use the same LLM model: {selected_model}")
        
        # Execute the workflow
        result = await workflow.execute_workflow(workflow_state)
        
        print(f"\n🎉 WORKFLOW EXECUTION COMPLETED!")
        print("="*70)
        print(f"Final Status: {result.status}")
        print(f"Current Step: {result.current_step}")
        print(f"LLM Model Used: {selected_model}")
        print(f"LLM Provider: {provider.upper()}")
        
        if result.errors:
            print(f"\n❌ Errors encountered:")
            for error in result.errors:
                print(f"   - {error}")
        
        # Show LLM model usage in metadata if available
        if result.metadata.get("human_approval", {}).get("llm_model_used"):
            print(f"\n🤖 LLM Model Usage:")
            print(f"   Model: {result.metadata['human_approval']['llm_model_used']}")
            print(f"   Provider: {provider.upper()}")
        
        if result.metadata.get("ado_epic_id"):
            print(f"\n🔗 Azure DevOps Work Items Created:")
            print(f"   Epic: {result.metadata['ado_epic_id']}")
            print(f"   Feature: {result.metadata.get('ado_feature_id', 'N/A')}")
            print(f"   Stories: {len(result.metadata.get('ado_story_ids', []))}")
            print(f"   Tasks: {result.metadata.get('ado_task_count', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Complete workflow test failed: {str(e)}")
        logger.error(f"Workflow test error: {str(e)}", exc_info=True)
        return False


async def main():
    """Main test execution."""
    print("🚀 Agentic AI Architect - Enhanced Complete Workflow Test")
    print("="*70)
    print("This enhanced workflow test now supports:")
    print("• Multiple LLM providers (OpenAI, Anthropic, Mistral, Perplexity, Grok, Groq)")
    print("• User-selected models for ideation")
    print("• Complete Azure DevOps integration")
    print("• Human approval workflow")
    print("• End-to-end product lifecycle management")
    print("="*70)
    
    success = await test_complete_workflow()
    
    if success:
        print("\n✅ Complete workflow test completed successfully!")
        print("   The system has demonstrated end-to-end functionality with your chosen LLM.")
    else:
        print("\n❌ Complete workflow test failed!")
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
