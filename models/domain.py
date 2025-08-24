"""
Domain models for the Agentic AI Architect system.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class Priority(str, Enum):
    """Priority levels for features and stories."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class StoryType(str, Enum):
    """Types of user stories."""
    EPIC = "Epic"
    FEATURE = "Feature"
    USER_STORY = "User Story"
    TASK = "Task"
    BUG = "Bug"


class StoryStatus(str, Enum):
    """Status of user stories."""
    NEW = "New"
    APPROVED = "Approved"
    IN_PROGRESS = "In Progress"
    IN_REVIEW = "In Review"
    DONE = "Done"
    REJECTED = "Rejected"


class AcceptanceCriterion(BaseModel):
    """Acceptance criterion for a user story."""
    id: str
    description: str
    criteria: str
    test_scenario: str
    is_met: bool = False


class DefinitionOfDone(BaseModel):
    """Definition of Done for a user story."""
    code_review_required: bool = True
    unit_tests_passing: bool = False
    integration_tests_passing: bool = False
    documentation_updated: bool = False
    security_review_completed: bool = False
    performance_requirements_met: bool = False
    accessibility_requirements_met: bool = False
    deployment_ready: bool = False


class UserStory(BaseModel):
    """User story model."""
    id: str
    title: str
    description: str
    story_type: StoryType
    priority: Priority
    status: StoryStatus = StoryStatus.NEW
    acceptance_criteria: List[AcceptanceCriterion] = []
    definition_of_done: DefinitionOfDone = Field(default_factory=DefinitionOfDone)
    epic_id: Optional[str] = None
    parent_story_id: Optional[str] = None
    estimated_story_points: Optional[int] = None
    actual_story_points: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    tags: List[str] = []
    assignee: Optional[str] = None
    reporter: Optional[str] = None

    @validator('updated_at', pre=True, always=True)
    def set_updated_at(cls, v):
        return datetime.now()


class Epic(BaseModel):
    """Epic model for grouping related stories."""
    id: str
    title: str
    description: str
    priority: Priority
    status: StoryStatus = StoryStatus.NEW
    stories: List[UserStory] = []
    business_value: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    target_release: Optional[str] = None


class Feature(BaseModel):
    """Feature model representing a product feature."""
    id: str
    name: str
    description: str
    priority: Priority
    epic_id: str
    user_stories: List[UserStory] = []
    acceptance_criteria: List[AcceptanceCriterion] = []
    definition_of_done: DefinitionOfDone = Field(default_factory=DefinitionOfDone)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    business_requirements: Optional[str] = None
    technical_requirements: Optional[str] = None
    dependencies: List[str] = []


class BoundedContext(BaseModel):
    """Domain-Driven Design bounded context."""
    name: str
    description: str
    domain_events: List[str] = []
    entities: List[str] = []
    value_objects: List[str] = []
    aggregates: List[str] = []
    services: List[str] = []
    policies: List[str] = []
    relationships: Dict[str, str] = {}


class OpenAPISpec(BaseModel):
    """OpenAPI 3.0 specification."""
    openapi: str = "3.0.3"
    info: Dict[str, Any] = {}
    paths: Dict[str, Any] = {}
    components: Dict[str, Any] = {}
    servers: List[Dict[str, str]] = []
    tags: List[Dict[str, str]] = []


class SpringBootService(BaseModel):
    """Spring Boot service configuration."""
    name: str
    package_name: str
    description: str
    version: str = "1.0.0"
    java_version: str = "17"
    spring_boot_version: str = "3.2.0"
    dependencies: List[str] = []
    endpoints: List[str] = []
    database_config: Optional[Dict[str, Any]] = None
    security_config: Optional[Dict[str, Any]] = None


class DeploymentConfig(BaseModel):
    """Deployment configuration."""
    service_name: str
    namespace: str = "default"
    replicas: int = 1
    image: str
    port: int = 8080
    environment_variables: Dict[str, str] = {}
    resource_limits: Dict[str, str] = {}
    resource_requests: Dict[str, str] = {}
    health_check_path: str = "/actuator/health"
    readiness_probe_path: str = "/actuator/health/readiness"
    liveness_probe_path: str = "/actuator/health/liveness"


class WorkflowState(BaseModel):
    """State of the workflow execution."""
    workflow_id: str
    current_step: str
    status: str
    feature: Optional[Feature] = None
    epic: Optional[Epic] = None
    stories: List[UserStory] = []
    bounded_contexts: List[BoundedContext] = []
    openapi_spec: Optional[OpenAPISpec] = None
    spring_boot_service: Optional[SpringBootService] = None
    deployment_config: Optional[DeploymentConfig] = None
    errors: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('updated_at', pre=True, always=True)
    def set_updated_at(cls, v):
        return datetime.now()
    
    @validator('metadata', pre=True, always=True)
    def ensure_metadata(cls, v):
        if v is None:
            return {}
        return v


class IdeationRequest(BaseModel):
    """Request for feature ideation."""
    feature_name: str
    description: str
    priority: Priority
    business_context: Optional[str] = None
    target_users: Optional[List[str]] = None
    success_metrics: Optional[List[str]] = None
    constraints: Optional[List[str]] = None


class IdeationResponse(BaseModel):
    """Response from ideation agent."""
    feature: Feature
    epic: Epic
    user_stories: List[UserStory]
    bounded_contexts: List[BoundedContext]
    estimated_effort: str
    risks: List[str] = []
    recommendations: List[str] = []
