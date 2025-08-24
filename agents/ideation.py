"""
Ideation Agent - Generates user stories and epics from feature ideas and creates Azure DevOps work items.
Supports multiple LLM providers: OpenAI, Anthropic, Mistral, Perplexity, and Grok.
"""

import logging
import uuid
import os
import re
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from langchain.schema import HumanMessage, SystemMessage, BaseMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_mistralai import ChatMistralAI
from langchain_perplexity import ChatPerplexity
from langchain_groq import ChatGroq
from langchain_core.language_models import BaseChatModel

from models.domain import (
    Feature, Epic, UserStory, AcceptanceCriterion, DefinitionOfDone,
    Priority, StoryType, StoryStatus, BoundedContext, IdeationRequest, IdeationResponse
)
from services.ado_client import AzureDevOpsClient

logger = logging.getLogger(__name__)


class LLMProvider:
    """Enum-like class for LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MISTRAL = "mistral"
    PERPLEXITY = "perplexity"
    GROK = "grok"
    GROQ = "groq"


class GrokClient:
    """Enhanced Grok client with Groq API integration and model mapping."""
    
    def __init__(self, api_key: str, temperature: float = 0.7):
        """Initialize Grok client.
        
        Args:
            api_key: Groq API key
            temperature: Temperature for generation
        """
        self.api_key = api_key
        self.temperature = temperature
        self.groq_client = ChatGroq(
            model="llama3-8b-8192",  # Default model
            temperature=temperature,
            groq_api_key=api_key
        )
        
        # Grok model to Groq model mapping
        self.model_mapping = {
            'grok-1': 'llama3-8b-8192',
            'grok-2': 'llama3-70b-8192', 
            'grok-beta': 'mixtral-8x7b-32768',
            'grok-x': 'llama3.1-405b',
            'grok-fast': 'llama3.1-8b-instruct',
            'grok-pro': 'llama3.1-70b-instruct'
        }
    
    def get_model(self, grok_model: str) -> str:
        """Get Groq model name for Grok model.
        
        Args:
            grok_model: Grok model name
            
        Returns:
            Corresponding Groq model name
        """
        return self.model_mapping.get(grok_model, grok_model)
    
    def switch_model(self, grok_model: str):
        """Switch to a different Grok model.
        
        Args:
            grok_model: Grok model name
        """
        groq_model = self.get_model(grok_model)
        self.groq_client = ChatGroq(
            model=groq_model,
            temperature=self.temperature,
            groq_api_key=self.api_key
        )
        logger.info(f"Switched Grok model from '{grok_model}' to Groq model '{groq_model}'")
    
    def get_client(self) -> ChatGroq:
        """Get the underlying Groq client.
        
        Returns:
            ChatGroq client instance
        """
        return self.groq_client
    
    def get_available_models(self) -> List[str]:
        """Get list of available Grok models.
        
        Returns:
            List of available Grok model names
        """
        return list(self.model_mapping.keys())


class LLMFactory:
    """Factory class for creating LLM instances based on model name."""
    
    @staticmethod
    def create_llm(model: str, temperature: float = 0.7) -> Any:
        """Create LLM instance based on model name.
        
        Args:
            model: Model name (e.g., 'gpt-4', 'claude-3', 'mistral-large', 'llama-3.1', 'grok-1')
            temperature: Temperature for generation
            
        Returns:
            LLM instance
            
        Raises:
            ValueError: If model is not supported or API key is missing
        """
        model_lower = model.lower()
        
        # OpenAI models
        if any(prefix in model_lower for prefix in ['gpt-', 'dall-e', 'text-']):
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required for OpenAI models")
            return ChatOpenAI(
                model=model,
                temperature=temperature,
                openai_api_key=api_key
            )
        
        # Anthropic models
        elif any(prefix in model_lower for prefix in ['claude-', 'sonnet-', 'opus-', 'haiku-']):
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable is required for Anthropic models")
            return ChatAnthropic(
                model=model,
                temperature=temperature,
                anthropic_api_key=api_key
            )
        
        # Mistral models
        elif any(prefix in model_lower for prefix in ['mistral-', 'mixtral-', 'codestral-']):
            api_key = os.getenv("MISTRAL_API_KEY")
            if not api_key:
                raise ValueError("MISTRAL_API_KEY environment variable is required for Mistral models")
            return ChatMistralAI(
                model=model,
                temperature=temperature,
                mistral_api_key=api_key
            )
        
        # Perplexity models
        elif any(prefix in model_lower for prefix in ['llama-', 'codellama-', 'mixtral-', 'pplx-']):
            api_key = os.getenv("PERPLEXITY_API_KEY")
            if not api_key:
                raise ValueError("PERPLEXITY_API_KEY environment variable is required for Perplexity models")
            return ChatPerplexity(
                model=model,
                temperature=temperature,
                perplexity_api_key=api_key
            )
        
        # Grok models (via Groq API)
        elif any(prefix in model_lower for prefix in ['grok-']):
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY environment variable is required for Grok models")
            
            # Use enhanced GrokClient for Grok models
            grok_client = GrokClient(api_key, temperature)
            grok_client.switch_model(model)
            return grok_client.get_client()
        
        # Direct Groq models (llama3-, mixtral-8x7b-, gemma2-)
        elif any(prefix in model_lower for prefix in ['llama3-', 'mixtral-8x7b-', 'gemma2-']):
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY environment variable is required for Groq models")
            
            return ChatGroq(
                model=model,
                temperature=temperature,
                groq_api_key=api_key
            )
        
        else:
            # Default to OpenAI if model type cannot be determined
            logger.warning(f"Model '{model}' not recognized, defaulting to OpenAI")
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required")
            return ChatOpenAI(
                model=model,
                temperature=temperature,
                openai_api_key=api_key
            )
    
    @staticmethod
    def get_provider_from_model(model: str) -> str:
        """Get LLM provider from model name.
        
        Args:
            model: Model name
            
        Returns:
            Provider name
        """
        model_lower = model.lower()
        
        if any(prefix in model_lower for prefix in ['gpt-', 'dall-e', 'text-']):
            return LLMProvider.OPENAI
        elif any(prefix in model_lower for prefix in ['claude-', 'sonnet-', 'opus-', 'haiku-']):
            return LLMProvider.ANTHROPIC
        elif any(prefix in model_lower for prefix in ['mistral-', 'mixtral-', 'codestral-']):
            return LLMProvider.MISTRAL
        elif any(prefix in model_lower for prefix in ['llama-', 'codellama-', 'pplx-']):
            return LLMProvider.PERPLEXITY
        elif any(prefix in model_lower for prefix in ['grok-']):
            return LLMProvider.GROK
        elif any(prefix in model_lower for prefix in ['llama3-', 'mixtral-8x7b-', 'gemma2-']):
            return LLMProvider.GROQ
        else:
            return LLMProvider.OPENAI  # Default
    
    @staticmethod
    def get_supported_models() -> Dict[str, List[str]]:
        """Get list of supported models by provider.
        
        Returns:
            Dictionary mapping provider to list of supported models
        """
        return {
            LLMProvider.OPENAI: [
                "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo",
                "gpt-4-vision-preview", "gpt-4-1106-preview"
            ],
            LLMProvider.ANTHROPIC: [
                "claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-5-opus-20241022",
                "claude-3-sonnet-20240229", "claude-3-haiku-20240307", "claude-3-opus-20240229",
                "claude-2.1", "claude-2.0", "claude-instant-1.2"
            ],
            LLMProvider.MISTRAL: [
                "mistral-large-latest", "mistral-medium-latest", "mistral-small-latest",
                "mixtral-8x7b-instruct", "codestral-22b-v0.1", "mistral-7b-instruct"
            ],
            LLMProvider.PERPLEXITY: [
                "llama-3.1-8b-instruct", "llama-3.1-70b-instruct", "llama-3.1-405b",
                "codellama-34b-instruct", "mixtral-8x7b-instruct", "pplx-7b-online",
                "pplx-70b-online", "pplx-7b-chat", "pplx-70b-chat"
            ],
            LLMProvider.GROK: [
                # Grok-specific models (mapped to Groq equivalents)
                "grok-1", "grok-2", "grok-beta", "grok-x", "grok-fast", "grok-pro"
            ],
            LLMProvider.GROQ: [
                # Direct Groq models
                "llama3-8b-8192", "llama3-70b-8192", "mixtral-8x7b-32768",
                "gemma2-9b-it", "gemma2-27b-it", "llama3.1-8b", "llama3.1-70b",
                # Additional Groq models
                "llama3.1-405b", "llama3.1-8b-instruct", "llama3.1-70b-instruct"
            ]
        }


class IdeationAgent:
    """Agent responsible for generating user stories and epics from feature ideas and creating Azure DevOps work items.
    
    Supports multiple LLM providers:
    - OpenAI (GPT models)
    - Anthropic (Claude models)
    - Mistral (Mistral and Mixtral models)
    - Perplexity (Llama and other models)
    - Grok (via Groq API)
    """
    
    def __init__(self, llm_model: str = "gpt-4o-mini", temperature: float = 0.7, 
                 ado_client: Optional[AzureDevOpsClient] = None):
        """Initialize the Ideation Agent.
        
        Args:
            llm_model: LLM model to use for generation (supports multiple providers)
            temperature: Temperature for LLM generation
            ado_client: Azure DevOps client for work item creation
        """
        self.model_name = llm_model
        self.temperature = temperature
        self.provider = LLMFactory.get_provider_from_model(llm_model)
        
        # Create LLM instance
        try:
            self.llm = LLMFactory.create_llm(llm_model, temperature)
            logger.info(f"Initialized {self.provider} LLM with model: {llm_model}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM {llm_model}: {str(e)}")
            # Fallback to a default model
            fallback_model = "gpt-4o-mini" if self.provider == LLMProvider.OPENAI else "claude-3-haiku-20240307"
            logger.info(f"Falling back to {fallback_model}")
            self.llm = LLMFactory.create_llm(fallback_model, temperature)
            self.model_name = fallback_model
            self.provider = LLMFactory.get_provider_from_model(fallback_model)
        
        self.ado_client = ado_client
        self.system_prompt = self._get_system_prompt()
        
        # Log initialization
        logger.info(f"IdeationAgent initialized with {self.provider} provider, model: {self.model_name}")
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the ideation agent.
        
        Returns:
            System prompt optimized for the current LLM provider
        """
        base_prompt = """You are an expert Product Owner and Business Analyst specializing in Agile development and user story creation.

Your role is to:
1. Analyze feature ideas and break them down into well-structured epics and user stories
2. Create comprehensive acceptance criteria for each story
3. Define clear Definition of Done (DoD) criteria
4. Identify bounded contexts for Domain-Driven Design
5. Estimate story points and prioritize work

Guidelines:
- User stories should follow the format: "As a [user type], I want [goal] so that [benefit]"
- Acceptance criteria should be specific, measurable, and testable
- Definition of Done should cover all quality gates (code review, testing, documentation, etc.)
- Bounded contexts should represent cohesive business domains
- Story points should follow Fibonacci sequence (1, 2, 3, 5, 8, 13, 21)
- Priority should consider business value, dependencies, and technical complexity

Output your response in a structured JSON format that can be parsed by the system.

CRITICAL: You must return ONLY valid JSON. Do not include any explanatory text, markdown formatting, or additional content outside the JSON structure. The response must start with { and end with }. Ensure the JSON is complete and properly closed."""
        
        # Provider-specific optimizations
        if self.provider == LLMProvider.ANTHROPIC:
            base_prompt += "\n\nNote: You are using Claude. Ensure your JSON output is properly formatted and valid."
        elif self.provider == LLMProvider.MISTRAL:
            base_prompt += "\n\nNote: You are using Mistral. Focus on clear, concise responses with well-structured JSON."
        elif self.provider == LLMProvider.PERPLEXITY:
            base_prompt += "\n\nNote: You are using Perplexity. Provide detailed analysis with comprehensive JSON output."
        elif self.provider == LLMProvider.GROK:
            base_prompt += "\n\nNote: You are using Grok. Ensure your JSON is properly formatted and follows the specified structure."
        elif self.provider == LLMProvider.GROQ:
            base_prompt += "\n\nNote: You are using Groq. You MUST return ONLY valid JSON. Do not include any explanatory text before or after the JSON. Keep responses concise to avoid token limits."
        
        return base_prompt
    
    def _optimize_prompt_for_provider(self, prompt: str) -> str:
        """Optimize prompt for specific LLM provider.
        
        Args:
            prompt: Base prompt
            
        Returns:
            Optimized prompt for the current provider
        """
        if self.provider == LLMProvider.ANTHROPIC:
            # Claude works well with clear instructions and examples
            return f"{prompt}\n\nPlease provide a detailed, well-structured response."
        elif self.provider == LLMProvider.MISTRAL:
            # Mistral benefits from concise, direct instructions
            return f"{prompt}\n\nKeep your response focused and structured."
        elif self.provider == LLMProvider.PERPLEXITY:
            # Perplexity models can handle longer, more detailed prompts
            return f"{prompt}\n\nProvide comprehensive analysis with detailed examples."
        elif self.provider == LLMProvider.GROK:
            # Grok works well with clear, structured prompts
            return f"{prompt}\n\nEnsure your response follows the exact format requested."
        elif self.provider == LLMProvider.GROQ:
            # Groq needs very explicit JSON instructions
            return f"{prompt}\n\nCRITICAL: Return ONLY valid JSON. No text before or after. Start with {{ and end with }}."
        else:
            # OpenAI default
            return prompt
    
    async def _generate_with_llm(self, messages: List[BaseMessage]) -> str:
        """Generate response using the configured LLM.
        
        Args:
            messages: List of messages to send to the LLM
            
        Returns:
            LLM response as string
            
        Raises:
            Exception: If LLM generation fails
        """
        try:
            logger.info(f"Generating response using {self.provider} model: {self.model_name}")
            
            # Generate response using the configured LLM
            response = await self.llm.ainvoke(messages)
            
            # Extract content from response
            if hasattr(response, 'content'):
                return response.content
            elif hasattr(response, 'text'):
                return response.text
            elif isinstance(response, str):
                return response
            else:
                return str(response)
                
        except Exception as e:
            logger.error(f"LLM generation failed with {self.provider} model {self.model_name}: {str(e)}")
            raise Exception(f"Failed to generate response using {self.provider} model: {str(e)}")
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the current LLM provider and model.
        
        Returns:
            Dictionary with provider information
        """
        info = {
            "provider": self.provider,
            "model": self.model_name,
            "temperature": self.temperature,
            "supported_models": LLMFactory.get_supported_models(),
            "current_provider_models": LLMFactory.get_supported_models().get(self.provider, [])
        }
        
        # Add Grok-specific information if using Grok provider
        if self.provider == LLMProvider.GROK:
            try:
                groq_api_key = os.getenv("GROQ_API_KEY")
                if groq_api_key:
                    grok_client = GrokClient(groq_api_key, self.temperature)
                    info["grok_models"] = grok_client.get_available_models()
                    info["grok_client"] = "Available"
                else:
                    info["grok_models"] = []
                    info["grok_client"] = "No API key"
            except Exception as e:
                info["grok_models"] = []
                info["grok_client"] = f"Error: {str(e)}"
        
        # Add Groq-specific information if using Groq provider
        elif self.provider == LLMProvider.GROQ:
            try:
                groq_api_key = os.getenv("GROQ_API_KEY")
                if groq_api_key:
                    info["groq_models"] = [
                        "llama3-8b-8192", "llama3-70b-8192", "mixtral-8x7b-32768",
                        "gemma2-9b-it", "gemma2-27b-it", "llama3.1-8b", "llama3.1-70b",
                        "llama3.1-405b", "llama3.1-8b-instruct", "llama3.1-70b-instruct"
                    ]
                    info["groq_client"] = "Available"
                else:
                    info["groq_models"] = []
                    info["groq_client"] = "No API key"
            except Exception as e:
                info["groq_models"] = []
                info["groq_client"] = f"Error: {str(e)}"
        
        return info
    
    def switch_model(self, new_model: str, temperature: Optional[float] = None) -> bool:
        """Switch to a different LLM model.
        
        Args:
            new_model: New model name
            temperature: New temperature (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            new_provider = LLMFactory.get_provider_from_model(new_model)
            new_temp = temperature if temperature is not None else self.temperature
            
            # Create new LLM instance
            new_llm = LLMFactory.create_llm(new_model, new_temp)
            
            # Update instance variables
            self.llm = new_llm
            self.model_name = new_model
            self.provider = new_provider
            self.temperature = new_temp
            self.system_prompt = self._get_system_prompt()
            
            logger.info(f"Successfully switched to {new_provider} model: {new_model}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to switch to model {new_model}: {str(e)}")
            return False
    
    async def generate_feature_breakdown(self, request: IdeationRequest) -> IdeationResponse:
        """Generate a complete feature breakdown including epics, stories, and bounded contexts.
        
        Args:
            request: Ideation request containing feature information
            
        Returns:
            IdeationResponse with generated artifacts
        """
        try:
            logger.info(f"Generating feature breakdown for: {request.feature_name}")
            
            # Create the feature
            feature = self._create_feature(request)
            
            # Generate epic
            epic = await self._generate_epic(request, feature)
            
            # Generate user stories
            user_stories = await self._generate_user_stories(request, feature, epic)
            
            # Generate bounded contexts
            bounded_contexts = await self._generate_bounded_contexts(request, feature)
            
            # Estimate effort
            estimated_effort = self._estimate_effort(user_stories)
            
            # Identify risks and recommendations
            risks = self._identify_risks(request, user_stories)
            recommendations = self._generate_recommendations(request, user_stories)
            
            # Update feature with generated stories
            feature.user_stories = user_stories
            feature.epic_id = epic.id
            
            # Update epic with stories
            epic.stories = user_stories
            
            return IdeationResponse(
                feature=feature,
                epic=epic,
                user_stories=user_stories,
                bounded_contexts=bounded_contexts,
                estimated_effort=estimated_effort,
                risks=risks,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Failed to generate feature breakdown: {str(e)}")
            
            # Generate comprehensive fallback response
            logger.warning("Generating fallback feature breakdown due to generation failure")
            fallback_response = self._generate_fallback_feature_breakdown(request)
            return fallback_response
    
    async def _create_minimal_work_items(self, request: IdeationRequest) -> Dict[str, Any]:
        """Create minimal Azure DevOps work items when full ideation fails.
        
        Args:
            request: Ideation request containing feature information
            
        Returns:
            Dictionary with minimal work item information
        """
        try:
            logger.info("Creating minimal Azure DevOps work items as fallback")
            
            # Create a basic epic
            basic_epic = Epic(
                id=str(uuid.uuid4()),
                title=f"Epic: {request.feature_name}",
                description=f"Basic epic for {request.feature_name} - created due to ideation failure",
                priority=request.priority,
                business_value="To be defined",
                target_release="TBD",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Create a basic feature
            basic_feature = Feature(
                id=str(uuid.uuid4()),
                name=request.feature_name,
                description=request.description,
                priority=request.priority,
                epic_id="",
                business_requirements=request.business_context or "To be defined",
                technical_requirements="To be defined",
                dependencies=[],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Create basic user story
            basic_story = UserStory(
                id=str(uuid.uuid4()),
                title=f"Define requirements for {request.feature_name}",
                description="Manual requirement definition needed due to ideation failure",
                story_type=StoryType.USER_STORY,
                priority=Priority.HIGH,
                epic_id=basic_epic.id,
                estimated_story_points=5,
                tags=["Fallback", "NeedsReview"],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Add basic acceptance criteria
            basic_story.acceptance_criteria = [
                AcceptanceCriterion(
                    id=str(uuid.uuid4()),
                    description="Manual review and requirement definition",
                    criteria="Validate feature requirements",
                    test_scenario="Manual testing and validation"
                )
            ]
            
            # Create work items in Azure DevOps
            epic_id = await self._ensure_epic_exists(basic_epic)
            feature_id = await self._create_feature_in_ado(basic_feature, epic_id)
            story_ids = await self._create_user_stories_in_ado([basic_story], feature_id)
            task_count = await self._create_acceptance_criteria_tasks_with_ado_ids([basic_story], story_ids, feature_id)
            
            logger.info(f"Created minimal work items: Epic {epic_id}, Feature {feature_id}, Story {story_ids[0]}")
            
            return {
                "status": "success",
                "epic_id": epic_id,
                "feature_id": feature_id,
                "stories_created": len(story_ids),
                "tasks_created": task_count,
                "total_story_points": 5,
                "work_items": {
                    "epic": epic_id,
                    "feature": feature_id,
                    "user_stories": story_ids,
                    "tasks": task_count
                },
                "ideation_summary": {
                    "feature_name": request.feature_name,
                    "epic_title": basic_epic.title,
                    "user_stories_count": 1,
                    "bounded_contexts_count": 0,
                    "estimated_effort": "2-4 weeks (estimate)",
                    "risks": ["Manual review and refinement required"],
                    "recommendations": ["Schedule manual review session"]
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to create minimal work items: {str(e)}")
            raise
    
    def _create_feature(self, request: IdeationRequest) -> Feature:
        """Create a feature from the ideation request.
        
        Args:
            request: Ideation request
            
        Returns:
            Feature object
        """
        return Feature(
            id=str(uuid.uuid4()),
            name=request.feature_name,
            description=request.description,
            priority=request.priority,
            epic_id="",  # Will be set after epic creation
            business_requirements=request.business_context,
            technical_requirements="",  # Will be generated later
            dependencies=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    async def _generate_epic(self, request: IdeationRequest, feature: Feature) -> Epic:
        """Generate an epic for the feature.
        
        Args:
            request: Ideation request
            feature: Feature object
            
        Returns:
            Epic object
        """
        prompt = f"""
        Create an epic for the following feature:
        
        Feature Name: {request.feature_name}
        Description: {request.description}
        Priority: {request.priority}
        Business Context: {request.business_context or 'Not specified'}
        
        Generate an epic with:
        - A clear, descriptive title
        - Comprehensive description
        - Business value statement
        - Target release timeline
        
        Return the response as a JSON object with these fields:
        {{
            "title": "Epic title",
            "description": "Epic description",
            "business_value": "Business value statement",
            "target_release": "Target release (e.g., Q1 2024)"
        }}
        """
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = await self._generate_with_llm(messages)
        logger.info(f"LLM response for epic generation: {response[:200]}...")  # Log first 200 chars
        
        epic_data = self._parse_json_response(response)
        logger.info(f"Parsed epic data: {epic_data}")
        
        # Ensure epic_data is a dictionary
        if not isinstance(epic_data, dict):
            logger.error(f"Expected dict for epic_data, got {type(epic_data)}: {epic_data}")
            # Create fallback epic data
            epic_data = {
                "title": f"Epic: {request.feature_name}",
                "description": request.description,
                "business_value": "Business value to be determined",
                "target_release": "TBD"
            }
        
        return Epic(
            id=str(uuid.uuid4()),
            title=epic_data.get("title", f"Epic: {request.feature_name}"),
            description=epic_data.get("description", request.description),
            priority=request.priority,
            business_value=epic_data.get("business_value", ""),
            target_release=epic_data.get("target_release", ""),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    async def _generate_user_stories(self, request: IdeationRequest, feature: Feature, epic: Epic) -> List[UserStory]:
        """Generate user stories for the feature.
        
        Args:
            request: Ideation request
            feature: Feature object
            epic: Epic object
            
        Returns:
            List of UserStory objects
        """
        prompt = f"""
        Create user stories for the following feature:
        
        Feature: {request.feature_name}
        Description: {request.description}
        Priority: {request.priority}
        Epic: {epic.title}
        
        Generate 5-8 user stories that cover:
        1. Core functionality
        2. User interface requirements
        3. Data management
        4. Integration points
        5. Error handling
        6. Performance requirements
        
        For each story, include:
        - Title following the format: "As a [user type], I want [goal] so that [benefit]"
        - Description with detailed requirements
        - 3-5 acceptance criteria
        - Story point estimate (1, 2, 3, 5, 8, 13, 21)
        - Priority (Low, Medium, High, Critical)
        - Tags for categorization
        
        Return the response as a JSON array of stories:
        [
            {{
                "title": "Story title",
                "description": "Story description",
                "acceptance_criteria": [
                    {{
                        "description": "Criterion description",
                        "criteria": "Specific criteria",
                        "test_scenario": "Test scenario description"
                    }}
                ],
                "story_points": 5,
                "priority": "High",
                "tags": ["UI", "Core"]
            }}
        ]
        """
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = await self._generate_with_llm(messages)
        logger.info(f"LLM response for user stories: {response[:200]}...")  # Log first 200 chars
        
        stories_data = self._parse_json_response(response)
        logger.info(f"Parsed user stories data: {stories_data}")
        
        # Ensure stories_data is a list
        if not isinstance(stories_data, list):
            logger.error(f"Expected list for stories_data, got {type(stories_data)}: {stories_data}")
            
            # Handle wrapped response format (e.g., {"stories": [...]})
            if isinstance(stories_data, dict) and "stories" in stories_data:
                logger.info(f"Extracting stories from wrapped response: {stories_data['stories']}")
                stories_data = stories_data["stories"]
            else:
                # Create fallback user story
                stories_data = [{
                    "title": "Default User Story",
                    "description": "Default story description",
                    "acceptance_criteria": [{
                        "description": "Default criterion",
                        "criteria": "Default criteria",
                        "test_scenario": "Default test scenario"
                    }],
                    "story_points": 3,
                    "priority": "Medium",
                    "tags": ["Default"]
                }]
        
        user_stories = []
        for story_data in stories_data:
            story = UserStory(
                id=str(uuid.uuid4()),
                title=story_data.get("title", "Untitled Story"),
                description=story_data.get("description", ""),
                story_type=StoryType.USER_STORY,
                priority=Priority(story_data.get("priority", "Medium")),
                epic_id=epic.id,
                estimated_story_points=story_data.get("story_points", 3),
                tags=story_data.get("tags", []),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Create acceptance criteria
            for criterion_data in story_data.get("acceptance_criteria", []):
                criterion = AcceptanceCriterion(
                    id=str(uuid.uuid4()),
                    description=criterion_data.get("description", ""),
                    criteria=criterion_data.get("criteria", ""),
                    test_scenario=criterion_data.get("test_scenario", "")
                )
                story.acceptance_criteria.append(criterion)
            
            # Create Definition of Done
            story.definition_of_done = self._create_definition_of_done(story)
            
            user_stories.append(story)
        
        return user_stories
    
    async def _generate_bounded_contexts(self, request: IdeationRequest, feature: Feature) -> List[BoundedContext]:
        """Generate bounded contexts for Domain-Driven Design.
        
        Args:
            request: Ideation request
            feature: Feature object
            
        Returns:
            List of BoundedContext objects
        """
        prompt = f"""
        Create bounded contexts for the following feature using Domain-Driven Design principles:
        
        Feature: {request.feature_name}
        Description: {request.description}
        
        Identify 2-4 bounded contexts that represent cohesive business domains. For each context:
        
        1. Name: Clear, business-focused name
        2. Description: What this context is responsible for
        3. Domain Events: Key events that occur in this context
        4. Entities: Core business objects
        5. Value Objects: Immutable objects with no identity
        6. Aggregates: Clusters of entities with clear boundaries
        7. Services: Business logic that doesn't belong to entities
        8. Policies: Business rules and constraints
        
        Return the response as a JSON array of bounded contexts:
        [
            {{
                "name": "Context Name",
                "description": "Context description",
                "domain_events": ["Event1", "Event2"],
                "entities": ["Entity1", "Entity2"],
                "value_objects": ["ValueObject1", "ValueObject2"],
                "aggregates": ["Aggregate1", "Aggregate2"],
                "services": ["Service1", "Service2"],
                "policies": ["Policy1", "Policy2"]
            }}
        ]
        """
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = await self._generate_with_llm(messages)
        logger.info(f"LLM response for bounded contexts: {response[:200]}...")  # Log first 200 chars
        
        contexts_data = self._parse_json_response(response)
        logger.info(f"Parsed bounded contexts data: {contexts_data}")
        
        # Ensure contexts_data is a list
        if not isinstance(contexts_data, list):
            logger.error(f"Expected list for contexts_data, got {type(contexts_data)}: {contexts_data}")
            
            # Handle wrapped response format (e.g., {"boundedContexts": [...]})
            if isinstance(contexts_data, dict) and "boundedContexts" in contexts_data:
                logger.info(f"Extracting bounded contexts from wrapped response: {contexts_data['boundedContexts']}")
                contexts_data = contexts_data["boundedContexts"]
            else:
                # Create fallback bounded context
                contexts_data = [{
                    "name": "Default Context",
                    "description": "Default bounded context",
                    "domain_events": ["DefaultEvent"],
                    "entities": ["DefaultEntity"],
                    "value_objects": ["DefaultValueObject"],
                    "aggregates": ["DefaultAggregate"],
                    "services": ["DefaultService"],
                    "policies": ["DefaultPolicy"]
                }]
        
        bounded_contexts = []
        for context_data in contexts_data:
            context = BoundedContext(
                name=context_data.get("name", "Unknown Context"),
                description=context_data.get("description", ""),
                domain_events=context_data.get("domain_events", []),
                entities=context_data.get("entities", []),
                value_objects=context_data.get("value_objects", []),
                aggregates=context_data.get("aggregates", []),
                services=context_data.get("services", []),
                policies=context_data.get("policies", [])
            )
            bounded_contexts.append(context)
        
        return bounded_contexts
    
    def _create_definition_of_done(self, story: UserStory) -> DefinitionOfDone:
        """Create a Definition of Done for a user story.
        
        Args:
            story: User story
            
        Returns:
            DefinitionOfDone object
        """
        # Base DoD for all stories
        dod = DefinitionOfDone()
        
        # Customize based on story type and complexity
        if story.estimated_story_points and story.estimated_story_points > 8:
            # Complex stories need more thorough DoD
            dod.performance_requirements_met = True
            dod.accessibility_requirements_met = True
        
        if any("security" in tag.lower() for tag in story.tags):
            dod.security_review_completed = True
        
        return dod
    
    def _estimate_effort(self, user_stories: List[UserStory]) -> str:
        """Estimate total effort based on story points.
        
        Args:
            user_stories: List of user stories
            
        Returns:
            Effort estimate string
        """
        total_points = sum(story.estimated_story_points or 0 for story in user_stories)
        
        if total_points <= 13:
            return "1-2 weeks"
        elif total_points <= 34:
            return "3-4 weeks"
        elif total_points <= 55:
            return "6-8 weeks"
        else:
            return "10+ weeks"
    
    def _identify_risks(self, request: IdeationRequest, user_stories: List[UserStory]) -> List[str]:
        """Identify potential risks for the feature.
        
        Args:
            request: Ideation request
            user_stories: List of user stories
            
        Returns:
            List of risk descriptions
        """
        risks = []
        
        # Technical risks
        if any(story.estimated_story_points and story.estimated_story_points > 13 for story in user_stories):
            risks.append("High complexity stories may require additional technical investigation")
        
        # Integration risks
        if any("integration" in story.tags for story in user_stories):
            risks.append("External integrations may have dependencies and rate limits")
        
        # Performance risks
        if any("performance" in story.tags for story in user_stories):
            risks.append("Performance requirements may need load testing and optimization")
        
        # Security risks
        if any("security" in story.tags for story in user_stories):
            risks.append("Security features require thorough testing and compliance review")
        
        return risks
    
    def _generate_recommendations(self, request: IdeationRequest, user_stories: List[UserStory]) -> List[str]:
        """Generate recommendations for the feature.
        
        Args:
            request: Ideation request
            user_stories: List of user stories
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Story splitting recommendations
        complex_stories = [s for s in user_stories if s.estimated_story_points and s.estimated_story_points > 8]
        if complex_stories:
            recommendations.append("Consider splitting complex stories into smaller, more manageable pieces")
        
        # Testing recommendations
        if len(user_stories) > 5:
            recommendations.append("Implement automated testing early to support rapid development")
        
        # Documentation recommendations
        if any("integration" in s.tags for s in user_stories):
            recommendations.append("Create comprehensive API documentation for integration points")
        
        # Performance recommendations
        if any("performance" in s.tags for s in user_stories):
            recommendations.append("Set up performance monitoring and alerting from the start")
        
        return recommendations
    
    def _parse_json_response(self, response_content: str) -> Any:
        """Parse JSON response from LLM with enhanced fallback handling.
        
        Args:
            response_content: Response content from LLM
            
        Returns:
            Parsed JSON data or fallback structure
        """
        import json
        import re
        
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'```json\s*(.*?)\s*```', response_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Look for JSON array or object
                json_match = re.search(r'(\[.*\]|\{.*\})', response_content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_str = response_content
            
            parsed_data = json.loads(json_str)
            logger.info(f"Successfully parsed JSON response: {type(parsed_data)}")
            return parsed_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            logger.error(f"Response content: {response_content}")
            
            # Try to extract partial JSON or provide intelligent fallback
            fallback_data = self._generate_fallback_json(response_content)
            logger.warning(f"Using fallback JSON structure due to parsing failure")
            return fallback_data
    
    def _generate_fallback_json(self, response_content: str) -> Any:
        """Generate intelligent fallback JSON based on response content.
        
        Args:
            response_content: The failed response content
            
        Returns:
            Fallback JSON structure
        """
        # Try to extract partial information from the response
        fallback_data = {}
        
        # Look for common patterns in the response
        if "stories" in response_content.lower() or "story" in response_content.lower():
            fallback_data = {
                "stories": [{
                    "title": "Fallback User Story",
                    "description": "Generated due to parsing failure - needs manual review",
                    "acceptance_criteria": [{
                        "description": "Review and refine this story",
                        "criteria": "Manual review required",
                        "test_scenario": "Validate story requirements"
                    }],
                    "story_points": 3,
                    "priority": "Medium",
                    "tags": ["Fallback", "NeedsReview"]
                }]
            }
            logger.info("Generated fallback user stories structure")
            
        elif "boundedcontexts" in response_content.lower() or "context" in response_content.lower():
            fallback_data = {
                "boundedContexts": [{
                    "name": "Fallback Bounded Context",
                    "description": "Generated due to parsing failure - needs manual review",
                    "domain_events": ["FallbackEvent"],
                    "entities": ["FallbackEntity"],
                    "value_objects": ["FallbackValueObject"],
                    "aggregates": ["FallbackAggregate"],
                    "services": ["FallbackService"],
                    "policies": ["FallbackPolicy"]
                }]
            }
            logger.info("Generated fallback bounded contexts structure")
            
        elif "epic" in response_content.lower() or "title" in response_content.lower():
            fallback_data = {
                "title": "Fallback Epic",
                "description": "Generated due to parsing failure - needs manual review",
                "business_value": "Manual review required",
                "target_release": "TBD"
            }
            logger.info("Generated fallback epic structure")
            
        else:
            # Generic fallback for unknown response types
            fallback_data = {
                "fallback": True,
                "message": "Response parsing failed - manual review required",
                "original_content": response_content[:200] + "..." if len(response_content) > 200 else response_content
            }
            logger.info("Generated generic fallback structure")
        
        return fallback_data
    
    def _generate_fallback_feature_breakdown(self, request: IdeationRequest) -> 'IdeationResponse':
        """Generate a comprehensive fallback feature breakdown when LLM generation fails.
        
        Args:
            request: Ideation request containing feature information
            
        Returns:
            Fallback IdeationResponse with basic structure
        """
        from models.domain import IdeationResponse, Feature, Epic, UserStory, BoundedContext, StoryType, Priority, AcceptanceCriterion
        
        logger.info("Generating fallback feature breakdown")
        
        # Create fallback feature
        fallback_feature = Feature(
            id=str(uuid.uuid4()),
            name=request.feature_name,
            description=request.description,
            priority=request.priority,
            epic_id="",
            business_requirements=request.business_context or "To be defined",
            technical_requirements="To be defined",
            dependencies=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Create fallback epic
        fallback_epic = Epic(
            id=str(uuid.uuid4()),
            title=f"Epic: {request.feature_name}",
            description=f"Fallback epic for {request.feature_name} - needs manual refinement",
            priority=request.priority,
            business_value="To be defined - manual review required",
            target_release="TBD",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Create fallback user stories
        fallback_stories = [
            UserStory(
                id=str(uuid.uuid4()),
                title=f"Define requirements for {request.feature_name}",
                description="Manual review and requirement definition needed",
                story_type=StoryType.USER_STORY,
                priority=Priority.HIGH,
                epic_id=fallback_epic.id,
                estimated_story_points=5,
                tags=["Fallback", "NeedsReview"],
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            UserStory(
                id=str(uuid.uuid4()),
                title=f"Technical design for {request.feature_name}",
                description="Technical architecture and design needed",
                story_type=StoryType.USER_STORY,
                priority=Priority.HIGH,
                epic_id=fallback_epic.id,
                estimated_story_points=8,
                tags=["Fallback", "Technical", "NeedsReview"],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]
        
        # Add acceptance criteria to stories
        for story in fallback_stories:
            story.acceptance_criteria = [
                AcceptanceCriterion(
                    id=str(uuid.uuid4()),
                    description="Manual review and refinement required",
                    criteria="Validate and refine requirements",
                    test_scenario="Manual testing and validation needed"
                )
            ]
        
        # Create fallback bounded contexts
        fallback_contexts = [
            BoundedContext(
                name="Core Domain",
                description="Core business logic for the feature - needs refinement",
                domain_events=["FeatureCreated", "FeatureUpdated"],
                entities=["Feature", "User"],
                value_objects=["Status", "Priority"],
                aggregates=["FeatureAggregate"],
                services=["FeatureService"],
                policies=["FeatureValidationPolicy"]
            )
        ]
        
        # Update feature with epic ID
        fallback_feature.epic_id = fallback_epic.id
        
        # Update epic with stories
        fallback_epic.stories = fallback_stories
        
        logger.info(f"Generated fallback breakdown: {len(fallback_stories)} stories, {len(fallback_contexts)} contexts")
        
        return IdeationResponse(
            feature=fallback_feature,
            epic=fallback_epic,
            user_stories=fallback_stories,
            bounded_contexts=fallback_contexts,
            estimated_effort="2-4 weeks (estimate)",
            risks=["Manual review and refinement required"],
            recommendations=["Schedule manual review session to refine requirements"]
        )
    
    async def validate_feature_idea(self, request: IdeationRequest) -> Dict[str, Any]:
        """Validate a feature idea before processing.
        
        Args:
            request: Ideation request
            
        Returns:
            Validation result
        """
        validation_errors = []
        warnings = []
        
        # Check required fields
        if not request.feature_name.strip():
            validation_errors.append("Feature name is required")
        
        if not request.description.strip():
            validation_errors.append("Feature description is required")
        
        # Check description length
        if len(request.description) < 20:
            warnings.append("Feature description is quite short - consider adding more detail")
        
        if len(request.description) > 1000:
            warnings.append("Feature description is very long - consider breaking it down")
        
        # Check business context
        if not request.business_context:
            warnings.append("No business context provided - this may affect story generation quality")
        
        # Check target users
        if not request.target_users:
            warnings.append("No target users specified - this may affect user story creation")
        
        return {
            "is_valid": len(validation_errors) == 0,
            "errors": validation_errors,
            "warnings": warnings
        }
    
    async def create_azure_devops_workflow(self, request: IdeationRequest) -> Dict[str, Any]:
        """Create a complete Azure DevOps workflow from ideation to work items.
        
        This method:
        1. Generates the feature breakdown using LLM
        2. Creates Epic in Azure DevOps (if not exists)
        3. Creates Feature linked to Epic
        4. Creates User Stories with Acceptance Criteria
        5. Creates linked Tasks for each Acceptance Criterion
        
        Args:
            request: Ideation request containing feature information
            
        Returns:
            Dictionary with created work item IDs and status
        """
        if not self.ado_client:
            raise ValueError("Azure DevOps client is required for work item creation")
        
        try:
            logger.info(f"Creating Azure DevOps workflow for: {request.feature_name}")
            
            # Step 1: Generate feature breakdown using LLM
            logger.info("Step 1: Generating feature breakdown using LLM...")
            ideation_response = await self.generate_feature_breakdown(request)
            
            # Step 2: Check if Epic exists, create if not
            logger.info("Step 2: Checking/Creating Epic...")
            epic_id = await self._ensure_epic_exists(ideation_response.epic)
            
            # Step 3: Create Feature linked to Epic
            logger.info("Step 3: Creating Feature linked to Epic...")
            feature_id = await self._create_feature_in_ado(ideation_response.feature, epic_id)
            
            # Step 4: Create User Stories with Acceptance Criteria
            logger.info("Step 4: Creating User Stories with Acceptance Criteria...")
            stories_created = await self._create_user_stories_in_ado(ideation_response.user_stories, feature_id)
            
            # Step 5: Create linked Tasks for Acceptance Criteria
            logger.info("Step 5: Creating linked Tasks for Acceptance Criteria...")
            # Pass the actual Azure DevOps story IDs, not the domain model stories
            tasks_created = await self._create_acceptance_criteria_tasks_with_ado_ids(
                ideation_response.user_stories, 
                stories_created, 
                feature_id
            )
            
            # Compile results
            workflow_result = {
                "status": "success",
                "epic_id": epic_id,
                "feature_id": feature_id,
                "stories_created": len(stories_created),
                "tasks_created": tasks_created,
                "total_story_points": sum(story.estimated_story_points or 0 for story in ideation_response.user_stories),
                "work_items": {
                    "epic": epic_id,
                    "feature": feature_id,
                    "user_stories": stories_created,
                    "tasks": tasks_created
                },
                "ideation_summary": {
                    "feature_name": ideation_response.feature.name,
                    "epic_title": ideation_response.epic.title,
                    "user_stories_count": len(ideation_response.user_stories),
                    "bounded_contexts_count": len(ideation_response.bounded_contexts),
                    "estimated_effort": ideation_response.estimated_effort,
                    "risks": ideation_response.risks,
                    "recommendations": ideation_response.recommendations
                }
            }
            
            logger.info(f"Azure DevOps workflow completed successfully: {workflow_result}")
            return workflow_result
            
        except Exception as e:
            logger.error(f"Failed to create Azure DevOps workflow: {str(e)}")
            
            # Try to create minimal work items even if ideation fails
            try:
                logger.warning("Attempting to create minimal Azure DevOps work items despite ideation failure")
                minimal_result = await self._create_minimal_work_items(request)
                return minimal_result
            except Exception as fallback_error:
                logger.error(f"Fallback work item creation also failed: {str(fallback_error)}")
                return {
                    "status": "error",
                    "error": f"Primary error: {str(e)}, Fallback error: {str(fallback_error)}",
                    "epic_id": None,
                    "feature_id": None,
                    "stories_created": 0,
                    "tasks_created": 0,
                    "total_story_points": 0,
                    "work_items": {},
                    "ideation_summary": {}
                }
    
    async def _ensure_epic_exists(self, epic: Epic) -> str:
        """Ensure Epic exists in Azure DevOps, create if not.
        
        Args:
            epic: Epic object to create
            
        Returns:
            Epic ID in Azure DevOps
        """
        try:
            # For now, always create a new epic
            # In the future, you could search for existing epics with similar titles
            epic_id = self.ado_client.create_epic(epic)
            if not epic_id:
                raise ValueError("Failed to create Epic in Azure DevOps")
            
            logger.info(f"Created Epic with ID: {epic_id}")
            return epic_id
            
        except Exception as e:
            logger.error(f"Failed to ensure epic exists: {str(e)}")
            raise
    
    async def _create_feature_in_ado(self, feature: Feature, epic_id: str) -> str:
        """Create Feature in Azure DevOps linked to Epic.
        
        Args:
            feature: Feature object to create
            epic_id: ID of the parent Epic
            
        Returns:
            Feature ID in Azure DevOps
        """
        try:
            feature_id = self.ado_client.create_feature(feature, epic_id)
            if not feature_id:
                raise ValueError("Failed to create Feature in Azure DevOps")
            
            logger.info(f"Created Feature with ID: {feature_id}")
            return feature_id
            
        except Exception as e:
            logger.error(f"Failed to create feature in Azure DevOps: {str(e)}")
            raise
    
    async def _create_user_stories_in_ado(self, user_stories: List[UserStory], feature_id: str) -> List[str]:
        """Create User Stories in Azure DevOps linked to Feature.
        
        Args:
            user_stories: List of UserStory objects
            feature_id: ID of the parent Feature
            
        Returns:
            List of created User Story IDs
        """
        try:
            created_story_ids = []
            
            for story in user_stories:
                story_id = self.ado_client.create_user_story(story, feature_id)
                if story_id:
                    created_story_ids.append(story_id)
                    logger.info(f"Created User Story with ID: {story_id}")
                else:
                    logger.warning(f"Failed to create User Story: {story.title}")
            
            logger.info(f"Created {len(created_story_ids)} User Stories")
            return created_story_ids
            
        except Exception as e:
            logger.error(f"Failed to create user stories in Azure DevOps: {str(e)}")
            raise
    
    async def _create_acceptance_criteria_tasks(self, user_stories: List[UserStory], feature_id: str) -> int:
        """Create linked Tasks for Acceptance Criteria.
        
        Args:
            user_stories: List of UserStory objects
            feature_id: ID of the parent Feature
            
        Returns:
            Total number of tasks created
        """
        try:
            total_tasks = 0
            
            for story in user_stories:
                if hasattr(story, 'acceptance_criteria') and story.acceptance_criteria:
                    for i, criterion in enumerate(story.acceptance_criteria, 1):
                        try:
                            task_id = self.ado_client._create_acceptance_criterion_task(
                                criterion, 
                                str(story.id), 
                                i
                            )
                            if task_id:
                                total_tasks += 1
                                logger.info(f"Created Acceptance Criteria Task {task_id} for story {story.id}")
                        except Exception as task_error:
                            logger.warning(f"Failed to create task for criterion {i}: {str(task_error)}")
            
            logger.info(f"Created {total_tasks} Acceptance Criteria Tasks")
            return total_tasks
            
        except Exception as e:
            logger.error(f"Failed to create acceptance criteria tasks: {str(e)}")
            raise
    
    async def _create_acceptance_criteria_tasks_with_ado_ids(self, user_stories: List[UserStory], ado_story_ids: List[str], feature_id: str) -> int:
        """Create linked Tasks for Acceptance Criteria using actual Azure DevOps IDs.
        
        Args:
            user_stories: List of UserStory objects from domain model
            ado_story_ids: List of actual Azure DevOps story IDs
            feature_id: ID of the parent Feature in Azure DevOps
            
        Returns:
            Total number of tasks created
        """
        try:
            total_tasks = 0
            
            # Ensure we have matching lists
            if len(user_stories) != len(ado_story_ids):
                logger.warning(f"Mismatch between user stories ({len(user_stories)}) and ADO IDs ({len(ado_story_ids)})")
                return 0
            
            for story, ado_story_id in zip(user_stories, ado_story_ids):
                if hasattr(story, 'acceptance_criteria') and story.acceptance_criteria:
                    for i, criterion in enumerate(story.acceptance_criteria, 1):
                        try:
                            # Use the actual Azure DevOps story ID, not the domain model UUID
                            task_id = self.ado_client._create_acceptance_criterion_task(
                                criterion, 
                                ado_story_id,  # ← This is the actual Azure DevOps ID
                                i
                            )
                            if task_id:
                                total_tasks += 1
                                logger.info(f"Created Acceptance Criteria Task {task_id} for ADO story {ado_story_id}")
                        except Exception as task_error:
                            logger.warning(f"Failed to create task for criterion {i}: {str(task_error)}")
            
            logger.info(f"Created {total_tasks} Acceptance Criteria Tasks using ADO IDs")
            return total_tasks
            
        except Exception as e:
            logger.error(f"Failed to create acceptance criteria tasks with ADO IDs: {str(e)}")
            raise
