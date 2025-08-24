"""
Code Generation Agent - Generates Spring Boot microservices and OpenAPI specifications.
"""

import logging
import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from langchain.schema import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel

from models.domain import (
    Feature, UserStory, BoundedContext, OpenAPISpec, SpringBootService
)

logger = logging.getLogger(__name__)


class CodeGenerationAgent:
    """Agent responsible for generating Spring Boot microservices and OpenAPI specifications."""
    
    def __init__(self, llm_model: str = "gpt-4", temperature: float = 0.7):
        """Initialize the Code Generation Agent.
        
        Args:
            llm_model: LLM model to use for generation
            temperature: Temperature for LLM generation
        """
        # Import LLMFactory here to avoid circular imports
        from agents.ideation import LLMFactory
        
        try:
            self.llm = LLMFactory.create_llm(llm_model, temperature)
            logger.info(f"CodeGenerationAgent initialized with {llm_model} model")
        except Exception as e:
            logger.error(f"Failed to initialize LLM for CodeGenerationAgent: {str(e)}")
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
                    logger.warning(f"CodeGenerationAgent fallback to OpenAI gpt-4o-mini due to: {str(e)}")
                else:
                    raise ValueError("No fallback LLM available")
            except Exception as fallback_error:
                logger.error(f"CodeGenerationAgent fallback also failed: {str(fallback_error)}")
                raise
        
        self.system_prompt = self._get_system_prompt()
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the code generation agent."""
        return """You are an expert Spring Boot developer and software architect specializing in microservices and clean architecture.

Your role is to:
1. Generate OpenAPI 3.0 specifications from user stories
2. Scaffold Spring Boot microservices with clean architecture
3. Implement domain models, repositories, and services
4. Create REST controllers and endpoints
5. Write comprehensive unit and integration tests
6. Follow Spring Boot best practices and patterns

Guidelines:
- Use Spring Boot 3.x with Java 17+
- Follow clean architecture principles (Domain, Application, Infrastructure layers)
- Implement proper error handling and validation
- Use Spring Data JPA for persistence
- Include comprehensive testing with JUnit 5 and Mockito
- Follow REST API best practices
- Use proper dependency injection and configuration
- Include health checks and monitoring endpoints
- Generate production-ready, deployable code

Output your response in a structured format that can be parsed by the system."""
    
    async def generate_microservice(self, feature: Feature, user_stories: List[UserStory], bounded_contexts: List[BoundedContext]) -> Dict[str, Any]:
        """Generate a complete Spring Boot microservice.
        
        Args:
            feature: Feature object
            user_stories: List of user stories
            bounded_contexts: List of bounded contexts
            
        Returns:
            Dictionary containing generated microservice artifacts
        """
        try:
            logger.info(f"Generating microservice for feature: {feature.name}")
            
            # Generate OpenAPI specification
            openapi_spec = await self._generate_openapi_spec(feature, user_stories)
            
            # Generate Spring Boot service configuration
            spring_boot_config = await self._generate_spring_boot_config(feature, openapi_spec)
            
            # Generate domain models
            domain_models = await self._generate_domain_models(feature, bounded_contexts)
            
            # Generate repositories
            repositories = await self._generate_repositories(feature, domain_models)
            
            # Generate services
            services = await self._generate_services(feature, domain_models, repositories)
            
            # Generate controllers
            controllers = await self._generate_controllers(feature, openapi_spec, services)
            
            # Generate tests
            tests = await self._generate_tests(feature, controllers, services, repositories)
            
            # Generate configuration files
            config_files = await self._generate_config_files(feature, spring_boot_config)
            
            return {
                "feature_name": feature.name,
                "openapi_spec": openapi_spec,
                "spring_boot_config": spring_boot_config,
                "domain_models": domain_models,
                "repositories": repositories,
                "services": services,
                "controllers": controllers,
                "tests": tests,
                "config_files": config_files,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate microservice: {str(e)}")
            raise
    
    async def _generate_openapi_spec(self, feature: Feature, user_stories: List[UserStory]) -> OpenAPISpec:
        """Generate OpenAPI 3.0 specification from user stories.
        
        Args:
            feature: Feature object
            user_stories: List of user stories
            
        Returns:
            OpenAPI specification
        """
        prompt = f"""
        Generate an OpenAPI 3.0 specification for the following feature and user stories:
        
        Feature: {feature.name}
        Description: {feature.description}
        
        User Stories:
        {self._format_stories_for_prompt(user_stories)}
        
        Create a comprehensive OpenAPI 3.0 specification that includes:
        
        1. **Info**: API metadata (title, version, description)
        2. **Servers**: API server configurations
        3. **Paths**: REST endpoints based on user stories
        4. **Components**: Reusable schemas, parameters, and responses
        5. **Tags**: API endpoint grouping
        6. **Security**: Authentication and authorization schemes
        
        For each endpoint, include:
        - HTTP method and path
        - Request/response schemas
        - Parameters and validation
        - Response codes and examples
        - Security requirements
        
        Return the complete OpenAPI 3.0 specification in JSON format.
        """
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        openapi_data = self._parse_json_response(response.content, "OpenAPI")
        
        return OpenAPISpec(**openapi_data)
    
    def _format_stories_for_prompt(self, user_stories: List[UserStory]) -> str:
        """Format user stories for the prompt.
        
        Args:
            user_stories: List of user stories
            
        Returns:
            Formatted string for prompt
        """
        formatted = []
        for story in user_stories:
            formatted.append(f"""
            Story: {story.title}
            Description: {story.description}
            Acceptance Criteria: {', '.join([ac.criteria for ac in story.acceptance_criteria])}
            """)
        
        return '\n'.join(formatted)
    
    async def _generate_spring_boot_config(self, feature: Feature, openapi_spec: OpenAPISpec) -> SpringBootService:
        """Generate Spring Boot service configuration.
        
        Args:
            feature: Feature object
            openapi_spec: OpenAPI specification
            
        Returns:
            Spring Boot service configuration
        """
        prompt = f"""
        Generate Spring Boot service configuration for the following feature:
        
        Feature: {feature.name}
        Description: {feature.description}
        
        OpenAPI Endpoints: {len(openapi_spec.paths)} endpoints
        
        Create a Spring Boot service configuration that includes:
        
        1. **Service Name**: Descriptive service name
        2. **Package Name**: Java package structure
        3. **Dependencies**: Required Spring Boot starters and libraries
        4. **Configuration**: Application properties and settings
        5. **Database**: Database configuration and JPA settings
        6. **Security**: Security configuration if needed
        7. **Monitoring**: Health checks and metrics
        
        Return the response as a JSON object with this structure:
        {{
            "name": "ServiceName",
            "package_name": "com.example.service",
            "description": "Service description",
            "version": "1.0.0",
            "java_version": "17",
            "spring_boot_version": "3.2.0",
            "dependencies": ["spring-boot-starter-web", "spring-boot-starter-data-jpa"],
            "endpoints": ["endpoint1", "endpoint2"],
            "database_config": {{"type": "postgresql", "url": "jdbc:postgresql://localhost:5432/db"}},
            "security_config": {{"enabled": true, "type": "oauth2"}}
        }}
        """
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        config_data = self._parse_json_response(response.content, "SpringBootConfig")
        
        return SpringBootService(**config_data)
    
    async def _generate_domain_models(self, feature: Feature, bounded_contexts: List[BoundedContext]) -> List[Dict[str, Any]]:
        """Generate domain models based on bounded contexts.
        
        Args:
            feature: Feature object
            bounded_contexts: List of bounded contexts
            
        Returns:
            List of domain model specifications
        """
        prompt = f"""
        Generate domain models for the following feature and bounded contexts:
        
        Feature: {feature.name}
        Description: {feature.description}
        
        Bounded Contexts:
        {self._format_contexts_for_prompt(bounded_contexts)}
        
        Create comprehensive domain models that include:
        
        1. **Entities**: Core business objects with JPA annotations
        2. **Value Objects**: Immutable objects with proper validation
        3. **Aggregates**: Entity clusters with consistency boundaries
        4. **Domain Events**: Events that occur in the domain
        5. **Enums**: Business enums and constants
        
        For each model, include:
        - Java class with proper annotations
        - Fields and getters/setters
        - Business logic methods
        - Validation annotations
        - JPA mappings
        
        Return the response as a JSON array of domain models:
        [
            {{
                "name": "ModelName",
                "type": "Entity|ValueObject|Aggregate|Event|Enum",
                "package": "com.example.domain",
                "java_code": "public class ModelName {{ ... }}",
                "description": "Model description"
            }}
        ]
        """
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return self._parse_json_response(response.content, "DomainModels")
    
    def _format_contexts_for_prompt(self, bounded_contexts: List[BoundedContext]) -> str:
        """Format bounded contexts for the prompt.
        
        Args:
            bounded_contexts: List of bounded contexts
            
        Returns:
            Formatted string for prompt
        """
        formatted = []
        for context in bounded_contexts:
            formatted.append(f"""
            Context: {context.name}
            Description: {context.description}
            Entities: {', '.join(context.entities)}
            Value Objects: {', '.join(context.value_objects)}
            Aggregates: {', '.join(context.aggregates)}
            """)
        
        return '\n'.join(formatted)
    
    async def _generate_repositories(self, feature: Feature, domain_models: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate repository interfaces and implementations.
        
        Args:
            feature: Feature object
            domain_models: List of domain models
            
        Returns:
            List of repository specifications
        """
        prompt = f"""
        Generate repository interfaces and implementations for the following domain models:
        
        Feature: {feature.name}
        
        Domain Models:
        {self._format_models_for_prompt(domain_models)}
        
        Create Spring Data JPA repositories that include:
        
        1. **Repository Interfaces**: Extending JpaRepository or custom interfaces
        2. **Custom Queries**: Using @Query annotations for complex queries
        3. **Specifications**: For dynamic querying if needed
        4. **Implementation Classes**: Custom repository implementations if required
        
        For each repository, include:
        - Interface extending appropriate Spring Data repository
        - Custom query methods
        - Query annotations and specifications
        - Proper package structure
        
        Return the response as a JSON array of repositories:
        [
            {{
                "name": "RepositoryName",
                "type": "interface|implementation",
                "package": "com.example.repository",
                "java_code": "public interface RepositoryName extends JpaRepository<Entity, Long> {{ ... }}",
                "description": "Repository description"
            }}
        ]
        """
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return self._parse_json_response(response.content, "Repositories")
    
    def _format_models_for_prompt(self, domain_models: List[Dict[str, Any]]) -> str:
        """Format domain models for the prompt.
        
        Args:
            domain_models: List of domain models
            
        Returns:
            Formatted string for prompt
        """
        formatted = []
        for model in domain_models:
            formatted.append(f"""
            Model: {model['name']}
            Type: {model['type']}
            Package: {model['package']}
            Description: {model['description']}
            """)
        
        return '\n'.join(formatted)
    
    async def _generate_services(self, feature: Feature, domain_models: List[Dict[str, Any]], repositories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate service layer classes.
        
        Args:
            feature: Feature object
            domain_models: List of domain models
            repositories: List of repositories
            
        Returns:
            List of service specifications
        """
        prompt = f"""
        Generate service layer classes for the following feature:
        
        Feature: {feature.name}
        
        Domain Models:
        {self._format_models_for_prompt(domain_models)}
        
        Repositories:
        {self._format_repositories_for_prompt(repositories)}
        
        Create service classes that include:
        
        1. **Application Services**: Orchestrating use cases
        2. **Domain Services**: Business logic not belonging to entities
        3. **Infrastructure Services**: External integrations
        
        For each service, include:
        - Service interface and implementation
        - Business logic methods
        - Transaction management
        - Error handling
        - Proper dependency injection
        
        Return the response as a JSON array of services:
        [
            {{
                "name": "ServiceName",
                "type": "ApplicationService|DomainService|InfrastructureService",
                "package": "com.example.service",
                "java_code": "public class ServiceName {{ ... }}",
                "description": "Service description"
            }}
        ]
        """
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return self._parse_json_response(response.content, "Services")
    
    def _format_repositories_for_prompt(self, repositories: List[Dict[str, Any]]) -> str:
        """Format repositories for the prompt.
        
        Args:
            repositories: List of repositories
            
        Returns:
            Formatted string for prompt
        """
        formatted = []
        for repo in repositories:
            formatted.append(f"""
            Repository: {repo['name']}
            Type: {repo['type']}
            Package: {repo['package']}
            Description: {repo['description']}
            """)
        
        return '\n'.join(formatted)
    
    async def _generate_controllers(self, feature: Feature, openapi_spec: OpenAPISpec, services: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate REST controllers.
        
        Args:
            feature: Feature object
            openapi_spec: OpenAPI specification
            services: List of services
            
        Returns:
            List of controller specifications
        """
        prompt = f"""
        Generate REST controllers for the following feature and OpenAPI specification:
        
        Feature: {feature.name}
        
        OpenAPI Paths:
        {json.dumps(openapi_spec.paths, indent=2)}
        
        Services:
        {self._format_services_for_prompt(services)}
        
        Create REST controllers that include:
        
        1. **Controller Classes**: REST endpoints with proper annotations
        2. **Request/Response DTOs**: Data transfer objects
        3. **Validation**: Input validation using Bean Validation
        4. **Error Handling**: Proper HTTP status codes and error responses
        5. **Documentation**: OpenAPI annotations for Swagger
        
        For each controller, include:
        - REST endpoint mappings
        - Request/response handling
        - Validation annotations
        - Error handling
        - OpenAPI documentation
        
        Return the response as a JSON array of controllers:
        [
            {{
                "name": "ControllerName",
                "package": "com.example.controller",
                "java_code": "@RestController public class ControllerName {{ ... }}",
                "description": "Controller description",
                "endpoints": ["GET /api/resource", "POST /api/resource"]
            }}
        ]
        """
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return self._parse_json_response(response.content, "Controllers")
    
    def _format_services_for_prompt(self, services: List[Dict[str, Any]]) -> str:
        """Format services for the prompt.
        
        Args:
            services: List of services
            
        Returns:
            Formatted string for prompt
        """
        formatted = []
        for service in services:
            formatted.append(f"""
            Service: {service['name']}
            Type: {service['type']}
            Package: {service['package']}
            Description: {service['description']}
            """)
        
        return '\n'.join(formatted)
    
    async def _generate_tests(self, feature: Feature, controllers: List[Dict[str, Any]], services: List[Dict[str, Any]], repositories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate comprehensive test suites.
        
        Args:
            feature: Feature object
            controllers: List of controllers
            services: List of services
            repositories: List of repositories
            
        Returns:
            List of test specifications
        """
        prompt = f"""
        Generate comprehensive test suites for the following feature:
        
        Feature: {feature.name}
        
        Controllers:
        {self._format_controllers_for_prompt(controllers)}
        
        Services:
        {self._format_services_for_prompt(services)}
        
        Repositories:
        {self._format_repositories_for_prompt(repositories)}
        
        Create test classes that include:
        
        1. **Unit Tests**: Testing individual components in isolation
        2. **Integration Tests**: Testing component interactions
        3. **Controller Tests**: Testing REST endpoints
        4. **Service Tests**: Testing business logic
        5. **Repository Tests**: Testing data access
        
        For each test class, include:
        - Test methods for all public methods
        - Mocking of dependencies
        - Test data setup and teardown
        - Assertions for expected behavior
        - Edge case and error scenario testing
        
        Use JUnit 5 and Mockito for testing.
        
        Return the response as a JSON array of test classes:
        [
            {{
                "name": "TestClassName",
                "type": "UnitTest|IntegrationTest|ControllerTest|ServiceTest|RepositoryTest",
                "package": "com.example.test",
                "java_code": "@Test public class TestClassName {{ ... }}",
                "description": "Test description",
                "test_methods": ["testMethod1", "testMethod2"]
            }}
        ]
        """
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return self._parse_json_response(response.content, "TestCode")
    
    def _format_controllers_for_prompt(self, controllers: List[Dict[str, Any]]) -> str:
        """Format controllers for the prompt.
        
        Args:
            controllers: List of controllers
            
        Returns:
            Formatted string for prompt
        """
        formatted = []
        for controller in controllers:
            formatted.append(f"""
            Controller: {controller['name']}
            Package: {controller['package']}
            Description: {controller['description']}
            Endpoints: {', '.join(controller['endpoints'])}
            """)
        
        return '\n'.join(formatted)
    
    async def _generate_config_files(self, feature: Feature, spring_boot_config: SpringBootService) -> List[Dict[str, Any]]:
        """Generate configuration files.
        
        Args:
            feature: Feature object
            spring_boot_config: Spring Boot configuration
            
        Returns:
            List of configuration file specifications
        """
        prompt = f"""
        Generate configuration files for the following Spring Boot service:
        
        Feature: {feature.name}
        
        Spring Boot Config:
        {json.dumps(spring_boot_config.dict(), indent=2)}
        
        Create configuration files that include:
        
        1. **build.gradle**: Gradle build configuration
        2. **application.yml**: Spring Boot application properties
        3. **Dockerfile**: Docker container configuration
        4. **docker-compose.yml**: Local development setup
        5. **.gitignore**: Git ignore patterns
        
        For each file, include:
        - Proper configuration and dependencies
        - Environment-specific settings
        - Security and monitoring configuration
        - Database and external service configuration
        
        Return the response as a JSON array of configuration files:
        [
            {{
                "filename": "filename.ext",
                "content": "File content here",
                "description": "File description"
            }}
        ]
        """
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return self._parse_json_response(response.content, "ApplicationProperties")
    
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
        logger.warning(f"Using fallback JSON response for code generation context: {context_name}")
        
        if context_name == "OpenAPI":
            return {
                "openapi": "3.0.3",
                "info": {
                    "title": "Generated API",
                    "version": "1.0.0",
                    "description": "Auto-generated API specification"
                },
                "paths": {
                    "/api/v1/items": {
                        "get": {
                            "summary": "Get items",
                            "responses": {
                                "200": {
                                    "description": "Successful response",
                                    "content": {
                                        "application/json": {
                                            "schema": {
                                                "type": "array",
                                                "items": {"type": "object"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "components": {
                    "schemas": {
                        "Item": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "name": {"type": "string"}
                            }
                        }
                    }
                }
            }
        elif context_name == "SpringBootConfig":
            return {
                "group_id": "com.example",
                "artifact_id": "generated-service",
                "name": "Generated Service",
                "description": "Auto-generated Spring Boot service",
                "package_name": "com.example.service",
                "version": "1.0.0",
                "java_version": "17",
                "spring_boot_version": "3.2.0",
                "dependencies": [
                    "spring-boot-starter-web",
                    "spring-boot-starter-data-jpa",
                    "spring-boot-starter-validation"
                ],
                "database": "h2",
                "profiles": ["dev", "prod"]
            }
        else:
            return {
                "name": context_name,
                "description": f"Fallback response for {context_name}",
                "components": [],
                "configuration": {}
            }
    
    async def validate_generated_code(self, generated_code: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the generated code.
        
        Args:
            generated_code: Generated code artifacts
            
        Returns:
            Validation result
        """
        validation_errors = []
        warnings = []
        
        # Check required components
        if not generated_code.get("openapi_spec"):
            validation_errors.append("No OpenAPI specification generated")
        
        if not generated_code.get("spring_boot_config"):
            validation_errors.append("No Spring Boot configuration generated")
        
        if not generated_code.get("domain_models"):
            validation_errors.append("No domain models generated")
        
        if not generated_code.get("controllers"):
            validation_errors.append("No controllers generated")
        
        if not generated_code.get("tests"):
            warnings.append("No tests generated")
        
        # Check code quality indicators
        for model in generated_code.get("domain_models", []):
            if "java_code" not in model:
                warnings.append(f"Domain model {model.get('name', 'Unknown')} missing Java code")
        
        for controller in generated_code.get("controllers", []):
            if "java_code" not in controller:
                warnings.append(f"Controller {controller.get('name', 'Unknown')} missing Java code")
        
        return {
            "is_valid": len(validation_errors) == 0,
            "errors": validation_errors,
            "warnings": warnings
        }
    
    def save_generated_code(self, generated_code: Dict[str, Any], output_dir: str = "output/microservice") -> Dict[str, str]:
        """Save generated code to files.
        
        Args:
            generated_code: Generated code artifacts
            output_dir: Output directory
            
        Returns:
            Dictionary mapping artifact types to file paths
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            saved_files = {}
            
            # Save OpenAPI specification
            openapi_file = os.path.join(output_dir, "openapi.json")
            with open(openapi_file, 'w') as f:
                json.dump(generated_code['openapi_spec'].dict(), f, indent=2, default=str)
            saved_files['openapi'] = openapi_file
            
            # Save Spring Boot configuration
            config_file = os.path.join(output_dir, "spring_boot_config.json")
            with open(config_file, 'w') as f:
                json.dump(generated_code['spring_boot_config'].dict(), f, indent=2, default=str)
            saved_files['config'] = config_file
            
            # Save Java source files
            java_dir = os.path.join(output_dir, "src/main/java")
            os.makedirs(java_dir, exist_ok=True)
            
            # Save domain models
            for model in generated_code.get("domain_models", []):
                if "java_code" in model:
                    model_file = os.path.join(java_dir, f"{model['name']}.java")
                    with open(model_file, 'w') as f:
                        f.write(model['java_code'])
                    saved_files[f"model_{model['name']}"] = model_file
            
            # Save repositories
            for repo in generated_code.get("repositories", []):
                if "java_code" in repo:
                    repo_file = os.path.join(java_dir, f"{repo['name']}.java")
                    with open(repo_file, 'w') as f:
                        f.write(repo['java_code'])
                    saved_files[f"repo_{repo['name']}"] = repo_file
            
            # Save services
            for service in generated_code.get("services", []):
                if "java_code" in service:
                    service_file = os.path.join(java_dir, f"{service['name']}.java")
                    with open(service_file, 'w') as f:
                        f.write(service['java_code'])
                    saved_files[f"service_{service['name']}"] = service_file
            
            # Save controllers
            for controller in generated_code.get("controllers", []):
                if "java_code" in controller:
                    controller_file = os.path.join(java_dir, f"{controller['name']}.java")
                    with open(controller_file, 'w') as f:
                        f.write(controller['java_code'])
                    saved_files[f"controller_{controller['name']}"] = controller_file
            
            # Save tests
            test_dir = os.path.join(output_dir, "src/test/java")
            os.makedirs(test_dir, exist_ok=True)
            
            for test in generated_code.get("tests", []):
                if "java_code" in test:
                    test_file = os.path.join(test_dir, f"{test['name']}.java")
                    with open(test_file, 'w') as f:
                        f.write(test['java_code'])
                    saved_files[f"test_{test['name']}"] = test_file
            
            # Save configuration files
            for config_file in generated_code.get("config_files", []):
                if "filename" in config_file and "content" in config_file:
                    file_path = os.path.join(output_dir, config_file['filename'])
                    with open(file_path, 'w') as f:
                        f.write(config_file['content'])
                    saved_files[config_file['filename']] = file_path
            
            # Save generated code summary
            summary_file = os.path.join(output_dir, "generated_code_summary.json")
            with open(summary_file, 'w') as f:
                json.dump(generated_code, f, indent=2, default=str)
            saved_files['summary'] = summary_file
            
            logger.info(f"Saved generated code to {output_dir}")
            return saved_files
            
        except Exception as e:
            logger.error(f"Failed to save generated code: {str(e)}")
            raise
