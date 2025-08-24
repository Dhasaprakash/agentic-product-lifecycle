#!/usr/bin/env python3
"""
Test Multi-LLM Providers - Demonstrates support for multiple LLM providers
Tests the refactored IdeationAgent with different LLM providers
"""

import asyncio
import logging
import os
import sys
from typing import Dict, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.ideation import IdeationAgent, LLMFactory, LLMProvider
from models.domain import IdeationRequest, Priority

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config_from_file(config_file: str = "test_config.env") -> Dict[str, str]:
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


def set_environment_variables(config: Dict[str, str]):
    """Set environment variables from config."""
    env_vars = {
        'OPENAI_API_KEY': 'OPENAI_API_KEY',
        'ANTHROPIC_API_KEY': 'ANTHROPIC_API_KEY', 
        'MISTRAL_API_KEY': 'MISTRAL_API_KEY',
        'PERPLEXITY_API_KEY': 'PERPLEXITY_API_KEY',
        'GROQ_API_KEY': 'GROQ_API_KEY'
    }
    
    for env_var, config_key in env_vars.items():
        if config.get(config_key):
            os.environ[env_var] = config[config_key]
            logger.info(f"Set {env_var} from config")
        else:
            logger.warning(f"Missing {env_var} in config")


def test_llm_factory():
    """Test the LLMFactory functionality."""
    print("\n🔧 Testing LLM Factory...")
    print("="*50)
    
    # Test provider detection
    test_models = [
        "gpt-4o-mini",
        "claude-3-haiku-20240307", 
        "mistral-large-latest",
        "llama-3.1-8b-instruct",
        "llama3-8b-8192"
    ]
    
    for model in test_models:
        provider = LLMFactory.get_provider_from_model(model)
        print(f"Model: {model:<25} → Provider: {provider}")
    
    # Show supported models
    print(f"\n📋 Supported Models by Provider:")
    supported_models = LLMFactory.get_supported_models()
    for provider, models in supported_models.items():
        print(f"\n{provider.upper()}:")
        for model in models[:3]:  # Show first 3 models
            print(f"  - {model}")
        if len(models) > 3:
            print(f"  ... and {len(models) - 3} more")


def test_ideation_agent_initialization():
    """Test IdeationAgent initialization with different models."""
    print("\n🤖 Testing IdeationAgent Initialization...")
    print("="*50)
    
    # Test with different model types
    test_configs = [
        {"model": "gpt-4o-mini", "name": "OpenAI GPT-4o-mini"},
        {"model": "claude-3-haiku-20240307", "name": "Anthropic Claude-3-Haiku"},
        {"model": "mistral-large-latest", "name": "Mistral Large"},
        {"model": "llama-3.1-8b-instruct", "name": "Perplexity Llama-3.1"},
        {"model": "llama3-8b-8192", "name": "Grok Llama3-8b"}
    ]
    
    for config in test_configs:
        try:
            print(f"\nTesting: {config['name']}")
            print(f"Model: {config['model']}")
            
            # Try to create agent
            agent = IdeationAgent(
                llm_model=config['model'],
                temperature=0.7
            )
            
            # Get provider info
            info = agent.get_provider_info()
            print(f"✅ Successfully initialized {info['provider']} provider")
            print(f"   Current model: {info['model']}")
            print(f"   Temperature: {info['temperature']}")
            
        except Exception as e:
            print(f"❌ Failed to initialize {config['name']}: {str(e)}")
            if "API key" in str(e):
                print(f"   Reason: Missing API key for {config['name']}")
            else:
                print(f"   Reason: {str(e)}")


async def test_feature_generation():
    """Test feature generation with different LLM providers."""
    print("\n🚀 Testing Feature Generation...")
    print("="*50)
    
    # Create a sample ideation request
    request = IdeationRequest(
        feature_name="AI-Powered Customer Service Enhancement",
        description="Enhance customer service with AI features for better customer experience",
        business_context="Improve customer satisfaction and reduce response times",
        target_users=["Customer service agents", "Team leads"],
        priority=Priority.HIGH,
        success_metrics=["25% improvement in satisfaction", "40% faster response"]
    )
    
    # Test with available models
    available_models = []
    
    # Check which API keys are available
    api_keys = {
        'openai': os.getenv('OPENAI_API_KEY'),
        'anthropic': os.getenv('ANTHROPIC_API_KEY'),
        'mistral': os.getenv('MISTRAL_API_KEY'),
        'perplexity': os.getenv('PERPLEXITY_API_KEY'),
        'groq': os.getenv('GROQ_API_KEY')
    }
    
    for provider, key in api_keys.items():
        if key:
            if provider == 'openai':
                available_models.append('gpt-4o-mini')
            elif provider == 'anthropic':
                available_models.append('claude-3-haiku-20240307')
            elif provider == 'mistral':
                available_models.append('mistral-large-latest')
            elif provider == 'perplexity':
                available_models.append('llama-3.1-8b-instruct')
            elif provider == 'groq':
                available_models.append('llama3-8b-8192')
    
    if not available_models:
        print("❌ No API keys available for testing")
        return
    
    print(f"Available models for testing: {', '.join(available_models)}")
    
    # Test with first available model
    test_model = available_models[0]
    print(f"\n🧪 Testing feature generation with: {test_model}")
    
    try:
        agent = IdeationAgent(llm_model=test_model, temperature=0.7)
        
        print("Generating feature breakdown...")
        response = await agent.generate_feature_breakdown(request)
        
        print("✅ Feature generation successful!")
        print(f"   Epic: {response.epic.title}")
        print(f"   User Stories: {len(response.user_stories)}")
        print(f"   Bounded Contexts: {len(response.bounded_contexts)}")
        print(f"   Estimated Effort: {response.estimated_effort}")
        
        # Show provider info
        info = agent.get_provider_info()
        print(f"   LLM Provider: {info['provider']}")
        print(f"   Model Used: {info['model']}")
        
    except Exception as e:
        print(f"❌ Feature generation failed: {str(e)}")


def test_model_switching():
    """Test switching between different models."""
    print("\n🔄 Testing Model Switching...")
    print("="*50)
    
    # Start with OpenAI
    try:
        agent = IdeationAgent(llm_model="gpt-4o-mini", temperature=0.7)
        initial_info = agent.get_provider_info()
        print(f"Initial provider: {initial_info['provider']}")
        print(f"Initial model: {initial_info['model']}")
        
        # Try to switch to a different model
        available_models = []
        if os.getenv('ANTHROPIC_API_KEY'):
            available_models.append('claude-3-haiku-20240307')
        if os.getenv('MISTRAL_API_KEY'):
            available_models.append('mistral-large-latest')
        
        if available_models:
            new_model = available_models[0]
            print(f"\nSwitching to: {new_model}")
            
            success = agent.switch_model(new_model)
            if success:
                new_info = agent.get_provider_info()
                print(f"✅ Successfully switched to {new_info['provider']}")
                print(f"   New model: {new_info['model']}")
            else:
                print(f"❌ Failed to switch to {new_model}")
        else:
            print("No alternative models available for switching")
            
    except Exception as e:
        print(f"❌ Model switching test failed: {str(e)}")


async def main():
    """Main test execution."""
    print("🚀 Multi-LLM Provider Test Suite")
    print("="*60)
    
    # Load configuration
    config = load_config_from_file()
    set_environment_variables(config)
    
    # Run tests
    test_llm_factory()
    test_ideation_agent_initialization()
    await test_feature_generation()
    test_model_switching()
    
    print("\n🎉 Multi-LLM Provider Test Suite Completed!")
    print("\n📋 Summary:")
    print("✅ LLM Factory tested")
    print("✅ IdeationAgent initialization tested")
    print("✅ Feature generation tested")
    print("✅ Model switching tested")
    
    print("\n🔑 Required API Keys:")
    api_keys = {
        'OpenAI': 'OPENAI_API_KEY',
        'Anthropic': 'ANTHROPIC_API_KEY',
        'Mistral': 'MISTRAL_API_KEY', 
        'Perplexity': 'PERPLEXITY_API_KEY',
        'Groq (Grok)': 'GROQ_API_KEY'
    }
    
    for provider, key in api_keys.items():
        status = "✅ Set" if os.getenv(key) else "❌ Missing"
        print(f"   {provider}: {status}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Test execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Test execution failed with error: {str(e)}")
        sys.exit(1)
