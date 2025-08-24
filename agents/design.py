"""
Design Agent - Generates DDD models and Context Mapper DSL.
"""

import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from langchain.schema import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel

from models.domain import BoundedContext, Feature, UserStory

logger = logging.getLogger(__name__)


class DesignAgent:
    """Agent responsible for generating DDD models and Context Mapper DSL."""
    
    def __init__(self, llm_model: str = "gpt-4", temperature: float = 0.7):
        """Initialize the Design Agent.
        
        Args:
            llm_model: LLM model to use for generation
            temperature: Temperature for LLM generation
        """
        # Import LLMFactory here to avoid circular imports
        from agents.ideation import LLMFactory
        
        try:
            self.llm = LLMFactory.create_llm(llm_model, temperature)
            logger.info(f"DesignAgent initialized with {llm_model} model")
        except Exception as e:
            logger.error(f"Failed to initialize LLM for DesignAgent: {str(e)}")
            # Fallback to OpenAI if available
            try:
                from langchain_openai import ChatOpenAI
                api_key = os.getenv("OPENAI_API_KEY")
                if api_key:
                    self.llm = ChatOpenAI(
                        model="gpt-4o-mini",
                        temperature=temperature,
                        openai_api_key=api_key
                    )
                    logger.warning(f"DesignAgent fallback to OpenAI gpt-4o-mini due to: {str(e)}")
                else:
                    raise ValueError("No fallback LLM available")
            except Exception as fallback_error:
                logger.error(f"DesignAgent fallback also failed: {str(fallback_error)}")
                raise
        
        self.system_prompt = self._get_system_prompt()
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the design agent."""
        return """You are an expert Domain-Driven Design (DDD) architect and software designer specializing in Context Mapper DSL.

Your role is to:
1. Analyze business domains and create bounded contexts
2. Generate Context Mapper DSL (CML) specifications
3. Design domain models with entities, value objects, and aggregates
4. Create architecture diagrams and documentation
5. Ensure proper separation of concerns and domain boundaries

Guidelines:
- Bounded contexts should represent cohesive business domains
- Entities should have clear identity and lifecycle
- Value objects should be immutable and side-effect free
- Aggregates should enforce consistency boundaries
- Domain services should contain business logic not belonging to entities
- Context maps should show relationships between bounded contexts
- Use Context Mapper DSL syntax correctly

Output your response in a structured format that can be parsed by the system."""
    
    async def generate_ddd_model(self, feature: Feature, bounded_contexts: List[BoundedContext]) -> Dict[str, Any]:
        """Generate a complete DDD model for a feature.
        
        Args:
            feature: Feature object
            bounded_contexts: List of bounded contexts
            
        Returns:
            Dictionary containing DDD model artifacts
        """
        try:
            logger.info(f"Generating DDD model for feature: {feature.name}")
            
            # Generate detailed bounded contexts
            detailed_contexts = await self._generate_detailed_bounded_contexts(feature, bounded_contexts)
            
            # Generate Context Mapper DSL
            cml_spec = await self._generate_context_mapper_dsl(feature, detailed_contexts)
            
            # Generate domain model diagrams
            domain_diagrams = await self._generate_domain_diagrams(feature, detailed_contexts)
            
            # Generate context map
            context_map = await self._generate_context_map(detailed_contexts)
            
            # Generate architecture documentation
            architecture_doc = await self._generate_architecture_documentation(feature, detailed_contexts)
            
            return {
                "feature_name": feature.name,
                "bounded_contexts": detailed_contexts,
                "context_mapper_dsl": cml_spec,
                "domain_diagrams": domain_diagrams,
                "context_map": context_map,
                "architecture_documentation": architecture_doc,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate DDD model: {str(e)}")
            raise
    
    async def _generate_detailed_bounded_contexts(self, feature: Feature, bounded_contexts: List[BoundedContext]) -> List[Dict[str, Any]]:
        """Generate detailed bounded contexts with full domain model.
        
        Args:
            feature: Feature object
            bounded_contexts: List of bounded contexts
            
        Returns:
            List of detailed bounded context specifications
        """
        detailed_contexts = []
        
        for context in bounded_contexts:
            try:
                detailed_context = await self._generate_single_bounded_context(feature, context)
                detailed_contexts.append(detailed_context)
            except Exception as e:
                logger.error(f"Failed to generate detailed context for {context.name}: {str(e)}")
                # Add basic context if detailed generation fails
                detailed_contexts.append(self._create_basic_context(context))
        
        return detailed_contexts
    
    async def _generate_single_bounded_context(self, feature: Feature, context: BoundedContext) -> Dict[str, Any]:
        """Generate detailed specification for a single bounded context.
        
        Args:
            feature: Feature object
            context: Bounded context
            
        Returns:
            Detailed bounded context specification
        """
        prompt = f"""Create a detailed Domain-Driven Design specification for the bounded context: {context.name}

Feature: {feature.name}
Context Description: {context.description}

IMPORTANT: Respond ONLY with valid JSON. Do not include any markdown formatting, code blocks, or additional text.

Generate a comprehensive DDD specification with:
1. Entities (core business objects with identity)
2. Value Objects (immutable objects without identity)
3. Aggregates (consistency boundaries)
4. Domain Services (business logic)
5. Domain Events (significant occurrences)
6. Policies (business rules)
7. Repositories (data access)
8. Factories (object creation)

Return this exact JSON structure:
{{
    "name": "{context.name}",
    "description": "Detailed description of the bounded context",
    "entities": [
        {{
            "name": "EntityName",
            "description": "Clear description of the entity",
            "attributes": ["id", "attribute1", "attribute2"],
            "methods": ["method1", "method2"],
            "business_rules": ["rule description"],
            "relationships": ["relationship description"]
        }}
    ],
    "value_objects": [
        {{
            "name": "ValueObjectName",
            "description": "Value object description",
            "attributes": ["value", "property"],
            "methods": ["equals", "toString"],
            "business_rules": ["immutability rule"]
        }}
    ],
    "aggregates": [
        {{
            "name": "AggregateName",
            "description": "Aggregate description",
            "entities": ["EntityName"],
            "business_rules": ["consistency rule"]
        }}
    ],
    "domain_services": [
        {{
            "name": "ServiceName",
            "description": "Service description",
            "methods": ["businessMethod"],
            "business_rules": ["service rule"]
        }}
    ],
    "domain_events": [
        {{
            "name": "EventName",
            "description": "Event description",
            "attributes": ["eventId", "timestamp", "data"]
        }}
    ],
    "policies": [
        {{
            "name": "PolicyName",
            "description": "Policy description",
            "business_rules": ["policy rule"]
        }}
    ],
    "repositories": [
        {{
            "name": "RepositoryName",
            "description": "Repository description",
            "methods": ["save", "findById", "delete"]
        }}
    ],
    "factories": [
        {{
            "name": "FactoryName",
            "description": "Factory description",
            "methods": ["create", "rebuild"]
        }}
    ]
}}"""
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        context_data = self._parse_json_response(response.content, context.name)
        
        # Merge with original context data
        detailed_context = {
            "name": context.name,
            "description": context.description,
            "domain_events": context.domain_events,
            "entities": context.entities,
            "value_objects": context.value_objects,
            "aggregates": context.aggregates,
            "services": context.services,
            "policies": context.policies,
            "relationships": context.relationships,
            **context_data  # Override with detailed data
        }
        
        return detailed_context
    
    def _create_basic_context(self, context: BoundedContext) -> Dict[str, Any]:
        """Create a basic context specification if detailed generation fails.
        
        Args:
            context: Bounded context
            
        Returns:
            Basic context specification
        """
        return {
            "name": context.name,
            "description": context.description,
            "domain_events": context.domain_events,
            "entities": context.entities,
            "value_objects": context.value_objects,
            "aggregates": context.aggregates,
            "services": context.services,
            "policies": context.policies,
            "relationships": context.relationships,
            "repositories": [],
            "factories": []
        }
    
    async def _generate_context_mapper_dsl(self, feature: Feature, bounded_contexts: List[Dict[str, Any]]) -> str:
        """Generate Context Mapper DSL specification.
        
        Args:
            feature: Feature object
            bounded_contexts: List of detailed bounded contexts
            
        Returns:
            Context Mapper DSL specification
        """
        prompt = f"""
        Generate a Context Mapper DSL (CML) specification for the following feature and bounded contexts:
        
        Feature: {feature.name}
        Description: {feature.description}
        
        Bounded Contexts:
        {self._format_contexts_for_prompt(bounded_contexts)}
        
        Create a complete CML specification that includes:
        
        1. **Bounded Contexts**: Define each context with its domain model
        2. **Entities**: Define entities with attributes and methods
        3. **Value Objects**: Define value objects
        4. **Aggregates**: Define aggregates and their boundaries
        5. **Domain Services**: Define domain services
        6. **Context Map**: Define relationships between contexts
        7. **Use Cases**: Define key use cases for the feature
        
        Use proper CML syntax:
        - Context: name { ... }
        - Entity: name { ... }
        - ValueObject: name { ... }
        - Aggregate: name { ... }
        - Service: name { ... }
        - UseCase: name { ... }
        
        Return the complete CML specification as a code block.
        """
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content
    
    def _format_contexts_for_prompt(self, bounded_contexts: List[Dict[str, Any]]) -> str:
        """Format bounded contexts for the prompt.
        
        Args:
            bounded_contexts: List of bounded contexts
            
        Returns:
            Formatted string for prompt
        """
        formatted = []
        for context in bounded_contexts:
            formatted.append(f"""
            Context: {context['name']}
            Description: {context['description']}
            Entities: {', '.join(context.get('entities', []))}
            Value Objects: {', '.join(context.get('value_objects', []))}
            Aggregates: {', '.join(context.get('aggregates', []))}
            """)
        
        return '\n'.join(formatted)
    
    async def _generate_domain_diagrams(self, feature: Feature, bounded_contexts: List[Dict[str, Any]]) -> Dict[str, str]:
        """Generate domain model diagrams.
        
        Args:
            feature: Feature object
            bounded_contexts: List of bounded contexts
            
        Returns:
            Dictionary containing different types of diagrams
        """
        diagrams = {}
        
        # Generate PlantUML class diagram
        class_diagram = await self._generate_class_diagram(feature, bounded_contexts)
        diagrams["class_diagram"] = class_diagram
        
        # Generate PlantUML sequence diagram
        sequence_diagram = await self._generate_sequence_diagram(feature, bounded_contexts)
        diagrams["sequence_diagram"] = sequence_diagram
        
        # Generate PlantUML component diagram
        component_diagram = await self._generate_component_diagram(feature, bounded_contexts)
        diagrams["component_diagram"] = component_diagram
        
        return diagrams
    
    async def _generate_class_diagram(self, feature: Feature, bounded_contexts: List[Dict[str, Any]]) -> str:
        """Generate PlantUML class diagram.
        
        Args:
            feature: Feature object
            bounded_contexts: List of bounded contexts
            
        Returns:
            PlantUML class diagram
        """
        prompt = f"""
        Generate a PlantUML class diagram for the following feature and bounded contexts:
        
        Feature: {feature.name}
        Description: {feature.description}
        
        Bounded Contexts:
        {self._format_contexts_for_prompt(bounded_contexts)}
        
        Create a PlantUML class diagram that shows:
        
        1. **Entities**: As classes with attributes and methods
        2. **Value Objects**: As classes marked as <<value object>>
        3. **Aggregates**: As classes with aggregate boundaries
        4. **Domain Services**: As classes marked as <<service>>
        5. **Relationships**: Between entities (composition, association, etc.)
        6. **Context Boundaries**: Group related classes by bounded context
        
        Use PlantUML syntax:
        - @startuml and @enduml
        - package for bounded contexts
        - class for entities and value objects
        - <<stereotype>> for special types
        - relationships with proper arrows
        
        Return only the PlantUML code, no explanations.
        """
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content
    
    async def _generate_sequence_diagram(self, feature: Feature, bounded_contexts: List[Dict[str, Any]]) -> str:
        """Generate PlantUML sequence diagram.
        
        Args:
            feature: Feature object
            bounded_contexts: List of bounded contexts
            
        Returns:
            PlantUML sequence diagram
        """
        prompt = f"""
        Generate a PlantUML sequence diagram for the following feature and bounded contexts:
        
        Feature: {feature.name}
        Description: {feature.description}
        
        Bounded Contexts:
        {self._format_contexts_for_prompt(bounded_contexts)}
        
        Create a PlantUML sequence diagram that shows:
        
        1. **Key Use Cases**: Main user interactions
        2. **System Actors**: Users and external systems
        3. **Bounded Contexts**: As participants in the sequence
        4. **Domain Events**: Key events that occur
        5. **Message Flow**: Between different contexts and services
        6. **Business Logic**: Key business operations
        
        Use PlantUML syntax:
        - @startuml and @enduml
        - participant for bounded contexts
        - actor for users
        - -> for synchronous messages
        - --> for asynchronous messages
        - note for explanations
        
        Return only the PlantUML code, no explanations.
        """
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content
    
    async def _generate_component_diagram(self, feature: Feature, bounded_contexts: List[Dict[str, Any]]) -> str:
        """Generate PlantUML component diagram.
        
        Args:
            feature: Feature object
            bounded_contexts: List of bounded contexts
            
        Returns:
            PlantUML component diagram
        """
        prompt = f"""
        Generate a PlantUML component diagram for the following feature and bounded contexts:
        
        Feature: {feature.name}
        Description: {feature.description}
        
        Bounded Contexts:
        {self._format_contexts_for_prompt(bounded_contexts)}
        
        Create a PlantUML component diagram that shows:
        
        1. **Bounded Contexts**: As components
        2. **Interfaces**: APIs and contracts between contexts
        3. **Dependencies**: How contexts depend on each other
        4. **External Systems**: External dependencies
        5. **Data Stores**: Databases and repositories
        6. **Communication Patterns**: Synchronous vs asynchronous
        
        Use PlantUML syntax:
        - @startuml and @enduml
        - component for bounded contexts
        - interface for APIs
        - database for data stores
        - arrows for dependencies
        
        Return only the PlantUML code, no explanations.
        """
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content
    
    async def _generate_context_map(self, bounded_contexts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate context map showing relationships between bounded contexts.
        
        Args:
            bounded_contexts: List of bounded contexts
            
        Returns:
            Context map specification
        """
        prompt = f"""
        Generate a context map for the following bounded contexts:
        
        Bounded Contexts:
        {self._format_contexts_for_prompt(bounded_contexts)}
        
        Create a context map that shows:
        
        1. **Context Relationships**: How contexts relate to each other
        2. **Integration Patterns**: Shared kernel, customer-supplier, etc.
        3. **Dependencies**: Which contexts depend on others
        4. **Communication**: How contexts communicate
        5. **Boundaries**: Clear separation between contexts
        
        Return the response as a JSON object with this structure:
        {{
            "contexts": [
                {{
                    "name": "ContextName",
                    "relationships": [
                        {{
                            "target": "OtherContext",
                            "type": "relationship_type",
                            "description": "Description of relationship"
                        }}
                    ]
                }}
            ],
            "integration_patterns": [
                {{
                    "name": "PatternName",
                    "description": "Pattern description",
                    "contexts": ["Context1", "Context2"]
                }}
            ]
        }}
        """
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return self._parse_json_response(response.content, "ContextMap")
    
    async def _generate_architecture_documentation(self, feature: Feature, bounded_contexts: List[Dict[str, Any]]) -> str:
        """Generate architecture documentation.
        
        Args:
            feature: Feature object
            bounded_contexts: List of bounded contexts
            
        Returns:
            Architecture documentation
        """
        prompt = f"""
        Generate comprehensive architecture documentation for the following feature and bounded contexts:
        
        Feature: {feature.name}
        Description: {feature.description}
        
        Bounded Contexts:
        {self._format_contexts_for_prompt(bounded_contexts)}
        
        Create architecture documentation that covers:
        
        1. **Overview**: High-level architecture description
        2. **Bounded Contexts**: Detailed description of each context
        3. **Domain Model**: Key entities, value objects, and aggregates
        4. **Integration Patterns**: How contexts communicate
        5. **Data Architecture**: Data flow and storage
        6. **Security Considerations**: Security aspects
        7. **Performance Considerations**: Performance aspects
        8. **Deployment**: Deployment considerations
        
        Return the documentation in Markdown format with proper headings and structure.
        """
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return response.content
    
    def _parse_json_response(self, response_content: str, context_name: str = "Unknown") -> Any:
        """Parse JSON response from LLM with improved error handling and fallbacks.
        
        Args:
            response_content: Response content from LLM
            context_name: Name of the context for fallback generation
            
        Returns:
            Parsed JSON data or fallback data
        """
        import json
        import re
        
        try:
            # Clean the response content first
            cleaned_content = response_content.strip()
            
            # Try multiple extraction strategies
            json_str = None
            
            # Strategy 1: Extract from ```json blocks
            json_match = re.search(r'```json\s*(.*?)\s*```', cleaned_content, re.DOTALL | re.IGNORECASE)
            if json_match:
                json_str = json_match.group(1).strip()
            
            # Strategy 2: Extract from ``` blocks (any language)
            if not json_str:
                json_match = re.search(r'```\w*\s*(.*?)\s*```', cleaned_content, re.DOTALL)
                if json_match:
                    potential_json = json_match.group(1).strip()
                    if potential_json.startswith('{') or potential_json.startswith('['):
                        json_str = potential_json
            
            # Strategy 3: Look for JSON objects/arrays
            if not json_str:
                # Find the first complete JSON object or array
                json_patterns = [
                    r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})',  # Simple nested objects
                    r'(\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\])',  # Simple nested arrays
                    r'(\{.*\})',  # Any object (greedy)
                    r'(\[.*\])'   # Any array (greedy)
                ]
                
                for pattern in json_patterns:
                    json_match = re.search(pattern, cleaned_content, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(1)
                        break
            
            # Strategy 4: Try the entire content if it looks like JSON
            if not json_str:
                if cleaned_content.startswith(('{', '[')):
                    json_str = cleaned_content
            
            # Attempt to parse the extracted JSON
            if json_str:
                # Clean common issues in JSON
                json_str = self._clean_json_string(json_str)
                return json.loads(json_str)
            
            raise ValueError("No valid JSON found in response")
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse JSON response for {context_name}: {str(e)}")
            logger.error(f"Response content: {response_content[:500]}...")
            
            # Return fallback JSON structure based on context
            return self._get_fallback_json_response(context_name)
    
    def _clean_json_string(self, json_str: str) -> str:
        """Clean common issues in JSON strings.
        
        Args:
            json_str: Raw JSON string
            
        Returns:
            Cleaned JSON string
        """
        import re
        
        # Fix common JSON issues
        json_str = json_str.replace('\n', ' ')  # Remove newlines
        json_str = re.sub(r',\s*}', '}', json_str)  # Remove trailing commas before }
        json_str = re.sub(r',\s*]', ']', json_str)  # Remove trailing commas before ]
        json_str = re.sub(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'"\1":', json_str)  # Quote unquoted keys
        json_str = re.sub(r':\s*([a-zA-Z_][a-zA-Z0-9_]*)', r': "\1"', json_str)  # Quote unquoted string values
        
        return json_str
    
    def _get_fallback_json_response(self, context_name: str) -> Dict[str, Any]:
        """Generate fallback JSON response when parsing fails.
        
        Args:
            context_name: Name of the context
            
        Returns:
            Fallback JSON structure
        """
        logger.warning(f"Using fallback JSON response for context: {context_name}")
        
        return {
            "name": context_name,
            "description": f"Bounded context for {context_name} domain",
            "entities": [
                {
                    "name": f"{context_name}Entity",
                    "description": f"Main entity for {context_name} context",
                    "attributes": ["id", "name", "createdAt", "updatedAt"],
                    "methods": ["create", "update", "delete", "findById"],
                    "business_rules": [f"{context_name} entity must have unique identifier"],
                    "relationships": []
                }
            ],
            "value_objects": [
                {
                    "name": f"{context_name}Id",
                    "description": f"Unique identifier for {context_name}",
                    "attributes": ["value"],
                    "methods": ["toString", "equals"],
                    "business_rules": ["ID must be non-null and unique"]
                }
            ],
            "aggregates": [
                {
                    "name": f"{context_name}Aggregate",
                    "description": f"Aggregate root for {context_name} context",
                    "entities": [f"{context_name}Entity"],
                    "business_rules": [f"Maintains consistency for {context_name} operations"]
                }
            ],
            "domain_services": [
                {
                    "name": f"{context_name}Service",
                    "description": f"Domain service for {context_name} business logic",
                    "methods": ["process", "validate", "calculate"],
                    "business_rules": [f"Encapsulates {context_name} business operations"]
                }
            ],
            "domain_events": [
                {
                    "name": f"{context_name}Created",
                    "description": f"Event triggered when {context_name} is created",
                    "attributes": ["id", "timestamp", "data"]
                },
                {
                    "name": f"{context_name}Updated",
                    "description": f"Event triggered when {context_name} is updated",
                    "attributes": ["id", "timestamp", "changes"]
                }
            ],
            "policies": [
                {
                    "name": f"{context_name}ValidationPolicy",
                    "description": f"Validation rules for {context_name}",
                    "business_rules": [f"All {context_name} operations must be validated"]
                }
            ],
            "repositories": [
                {
                    "name": f"{context_name}Repository",
                    "description": f"Data access for {context_name} entities",
                    "methods": ["save", "findById", "findAll", "delete"]
                }
            ],
            "factories": [
                {
                    "name": f"{context_name}Factory",
                    "description": f"Factory for creating {context_name} objects",
                    "methods": ["create", "createFrom", "rebuild"]
                }
            ]
        }
    
    async def validate_ddd_model(self, ddd_model: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the generated DDD model.
        
        Args:
            ddd_model: Generated DDD model
            
        Returns:
            Validation result
        """
        validation_errors = []
        warnings = []
        
        # Check required fields
        if not ddd_model.get("bounded_contexts"):
            validation_errors.append("No bounded contexts defined")
        
        if not ddd_model.get("context_mapper_dsl"):
            validation_errors.append("No Context Mapper DSL generated")
        
        # Check bounded contexts
        for context in ddd_model.get("bounded_contexts", []):
            if not context.get("name"):
                validation_errors.append("Bounded context missing name")
            
            if not context.get("entities") and not context.get("value_objects"):
                warnings.append(f"Context {context.get('name', 'Unknown')} has no domain objects")
        
        # Check CML syntax (basic validation)
        cml_content = ddd_model.get("context_mapper_dsl", "")
        if "Context:" not in cml_content:
            warnings.append("Context Mapper DSL may not contain proper Context definitions")
        
        return {
            "is_valid": len(validation_errors) == 0,
            "errors": validation_errors,
            "warnings": warnings
        }
    
    def save_ddd_artifacts(self, ddd_model: Dict[str, Any], output_dir: str = "output/ddd") -> Dict[str, str]:
        """Save DDD artifacts to files.
        
        Args:
            ddd_model: Generated DDD model
            output_dir: Output directory
            
        Returns:
            Dictionary mapping artifact types to file paths
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            saved_files = {}
            
            # Save Context Mapper DSL
            cml_file = os.path.join(output_dir, f"{ddd_model['feature_name'].lower().replace(' ', '_')}.cml")
            with open(cml_file, 'w') as f:
                f.write(ddd_model['context_mapper_dsl'])
            saved_files['cml'] = cml_file
            
            # Save PlantUML diagrams
            diagrams_dir = os.path.join(output_dir, "diagrams")
            os.makedirs(diagrams_dir, exist_ok=True)
            
            for diagram_type, diagram_content in ddd_model.get('domain_diagrams', {}).items():
                diagram_file = os.path.join(diagrams_dir, f"{diagram_type}.puml")
                with open(diagram_file, 'w') as f:
                    f.write(diagram_content)
                saved_files[diagram_type] = diagram_file
            
            # Save architecture documentation
            doc_file = os.path.join(output_dir, "architecture.md")
            with open(doc_file, 'w') as f:
                f.write(ddd_model['architecture_documentation'])
            saved_files['documentation'] = doc_file
            
            # Save DDD model as JSON
            model_file = os.path.join(output_dir, "ddd_model.json")
            import json
            with open(model_file, 'w') as f:
                json.dump(ddd_model, f, indent=2, default=str)
            saved_files['model'] = model_file
            
            logger.info(f"Saved DDD artifacts to {output_dir}")
            return saved_files
            
        except Exception as e:
            logger.error(f"Failed to save DDD artifacts: {str(e)}")
            raise
