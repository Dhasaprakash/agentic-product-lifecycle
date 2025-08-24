# Agentic AI Architect - Project Structure

## Overview
This document describes the complete project structure of the Agentic AI Architect system, which automates the product development lifecycle from ideation to deployment.

## Root Directory Structure
```
agentic-product-lifecycle/
├── README.md                           # Main project documentation
├── PROJECT_STRUCTURE.md                # This file - detailed project structure
├── requirements.txt                    # Python dependencies
├── build.gradle                       # Java/Gradle dependencies
├── config.env.example                 # Environment configuration template
├── main.py                            # FastAPI application entry point
├── test_system.py                     # Demo/test script
├── .gitignore                         # Git ignore patterns
├── LICENSE                            # Project license
│
├── models/                            # Domain models and data structures
│   └── domain.py                     # Core domain models (Pydantic)
│
├── agents/                            # AI agents for each lifecycle stage
│   ├── ideation.py                   # Ideation agent (generates stories/epics)
│   ├── requirements.py                # Requirements agent (ADO integration)
│   ├── design.py                     # Design agent (DDD + Context Mapper)
│   ├── codegen.py                    # Code generation agent (Spring Boot)
│   └── deployment.py                 # Deployment agent (Kubernetes + Helm)
│
├── workflows/                         # LangGraph workflow orchestration
│   └── lifecycle.py                  # Main workflow orchestration
│
├── services/                          # External service integrations
│   ├── ado_client.py                 # Azure DevOps client
│   ├── mcp_client.py                 # MCP (Model Context Protocol) client
│   └── kubernetes.py                 # Kubernetes client
│
├── templates/                         # Code generation templates
│   ├── spring-boot/                  # Spring Boot templates
│   │   ├── entity.java.j2            # Entity template
│   │   ├── repository.java.j2        # Repository template
│   │   ├── service.java.j2           # Service template
│   │   ├── controller.java.j2        # Controller template
│   │   └── test.java.j2              # Test template
│   │
│   ├── helm/                         # Helm chart templates
│   │   ├── deployment.yaml.j2        # Deployment template
│   │   ├── service.yaml.j2           # Service template
│   │   ├── ingress.yaml.j2           # Ingress template
│   │   └── values.yaml.j2            # Values template
│   │
│   └── context-mapper/               # Context Mapper DSL templates
│       ├── bounded-context.cml.j2    # Bounded context template
│       ├── entity.cml.j2             # Entity template
│       └── context-map.cml.j2        # Context map template
│
├── output/                            # Generated artifacts (created at runtime)
│   ├── ddd/                          # DDD model artifacts
│   │   ├── *.cml                     # Context Mapper DSL files
│   │   ├── diagrams/                 # PlantUML diagrams
│   │   │   ├── class_diagram.puml    # Class diagram
│   │   │   ├── sequence_diagram.puml # Sequence diagram
│   │   │   └── component_diagram.puml # Component diagram
│   │   ├── architecture.md           # Architecture documentation
│   │   └── ddd_model.json            # DDD model summary
│   │
│   ├── microservice/                 # Generated Spring Boot code
│   │   ├── openapi.json              # OpenAPI specification
│   │   ├── spring_boot_config.json   # Spring Boot configuration
│   │   ├── src/                      # Java source code
│   │   │   ├── main/java/            # Main source code
│   │   │   │   ├── *.java            # Generated Java classes
│   │   │   │   └── ...               # Package structure
│   │   │   └── test/java/            # Test source code
│   │   │       ├── *.java            # Generated test classes
│   │   │       └── ...               # Test package structure
│   │   ├── build.gradle              # Gradle build file
│   │   ├── application.yml           # Spring Boot configuration
│   │   ├── Dockerfile                # Docker configuration
│   │   └── generated_code_summary.json # Code generation summary
│   │
│   └── deployment/                   # Deployment configuration
│       ├── kubernetes/                # Kubernetes manifests
│       │   ├── namespace.yaml        # Namespace definition
│       │   ├── deployment.yaml       # Deployment manifest
│       │   ├── service.yaml          # Service manifest
│       │   ├── ingress.yaml          # Ingress manifest
│       │   ├── configmap.yaml        # ConfigMap manifest
│       │   ├── secret.yaml           # Secret manifest
│       │   ├── hpa.yaml              # HPA manifest
│       │   └── networkpolicy.yaml    # NetworkPolicy manifest
│       │
│       ├── helm/                     # Helm chart
│       │   ├── Chart.yaml            # Chart metadata
│       │   ├── values.yaml           # Default values
│       │   ├── values-prod.yaml      # Production values
│       │   ├── values-dev.yaml       # Development values
│       │   └── templates/            # Helm templates
│       │       ├── deployment.yaml   # Deployment template
│       │       ├── service.yaml      # Service template
│       │       ├── ingress.yaml      # Ingress template
│       │       ├── configmap.yaml    # ConfigMap template
│       │       ├── secret.yaml       # Secret template
│       │       ├── hpa.yaml          # HPA template
│       │       ├── networkpolicy.yaml # NetworkPolicy template
│       │       ├── namespace.yaml    # Namespace template
│       │       ├── notes.txt         # Installation notes
│       │       └── _helpers.tpl      # Template helpers
│       │
│       ├── docker/                   # Docker configuration
│       │   ├── Dockerfile            # Multi-stage Dockerfile
│       │   ├── docker-compose.yml    # Local development
│       │   ├── docker-compose.prod.yml # Production setup
│       │   └── .dockerignore         # Docker ignore patterns
│       │
│       ├── cicd/                     # CI/CD pipeline configuration
│       │   ├── github-actions.yml    # GitHub Actions workflow
│       │   ├── gitlab-ci.yml         # GitLab CI/CD pipeline
│       │   ├── jenkins.groovy        # Jenkins pipeline script
│       │   └── argocd.yaml           # ArgoCD application
│       │
│       ├── monitoring/               # Monitoring configuration
│       │   ├── prometheus.yml        # Prometheus configuration
│       │   ├── grafana.json          # Grafana dashboard
│       │   ├── jaeger.yml            # Jaeger configuration
│       │   ├── elk.yml               # ELK stack configuration
│       │   └── alerting.yml          # Alert rules
│       │
│       └── deployment_summary.json   # Deployment configuration summary
│
├── tests/                             # Test files
│   ├── test_agents/                  # Agent tests
│   │   ├── test_ideation.py          # Ideation agent tests
│   │   ├── test_requirements.py      # Requirements agent tests
│   │   ├── test_design.py            # Design agent tests
│   │   ├── test_codegen.py           # Code generation agent tests
│   │   └── test_deployment.py        # Deployment agent tests
│   │
│   ├── test_services/                # Service tests
│   │   ├── test_ado_client.py        # Azure DevOps client tests
│   │   ├── test_mcp_client.py        # MCP client tests
│   │   └── test_kubernetes.py        # Kubernetes client tests
│   │
│   ├── test_workflows/                # Workflow tests
│   │   └── test_lifecycle.py         # Lifecycle workflow tests
│   │
│   ├── test_models/                   # Model tests
│   │   └── test_domain.py            # Domain model tests
│   │
│   ├── conftest.py                    # Pytest configuration
│   └── integration/                   # Integration tests
│       └── test_full_workflow.py     # End-to-end workflow test
│
├── docs/                              # Documentation
│   ├── api/                          # API documentation
│   │   ├── openapi.json              # OpenAPI specification
│   │   └── api.md                    # API usage guide
│   │
│   ├── architecture/                  # Architecture documentation
│   │   ├── system-overview.md        # System overview
│   │   ├── agent-architecture.md     # Agent architecture
│   │   ├── workflow-design.md        # Workflow design
│   │   └── deployment-architecture.md # Deployment architecture
│   │
│   ├── user-guide/                    # User guides
│   │   ├── getting-started.md        # Getting started guide
│   │   ├── configuration.md           # Configuration guide
│   │   ├── usage-examples.md         # Usage examples
│   │   └── troubleshooting.md        # Troubleshooting guide
│   │
│   └── developer/                     # Developer documentation
│       ├── development-setup.md       # Development setup
│       ├── contributing.md            # Contributing guidelines
│       ├── testing.md                 # Testing guide
│       └── deployment.md              # Deployment guide
│
├── scripts/                           # Utility scripts
│   ├── setup.sh                       # Environment setup script
│   ├── install-dependencies.sh        # Dependency installation
│   ├── run-tests.sh                   # Test execution script
│   ├── deploy.sh                      # Deployment script
│   └── cleanup.sh                     # Cleanup script
│
├── config/                            # Configuration files
│   ├── logging.conf                   # Logging configuration
│   ├── app.conf                       # Application configuration
│   └── environments/                  # Environment-specific configs
│       ├── development.yml            # Development configuration
│       ├── staging.yml                # Staging configuration
│       └── production.yml             # Production configuration
│
└── docker/                            # Docker configuration
    ├── Dockerfile                     # Application Dockerfile
    ├── docker-compose.yml             # Local development
    ├── docker-compose.prod.yml        # Production setup
    └── .dockerignore                  # Docker ignore patterns
```

## Key Components

### 1. Models (`models/`)
- **domain.py**: Core domain models using Pydantic
- Defines data structures for features, stories, epics, bounded contexts, etc.
- Provides type safety and validation

### 2. Agents (`agents/`)
- **ideation.py**: Generates user stories and epics from feature ideas
- **requirements.py**: Manages Azure DevOps integration and story lifecycle
- **design.py**: Creates DDD models and Context Mapper DSL
- **codegen.py**: Generates Spring Boot microservices and OpenAPI specs
- **deployment.py**: Manages Kubernetes deployment and Helm charts

### 3. Workflows (`workflows/`)
- **lifecycle.py**: Main LangGraph workflow orchestration
- Coordinates all agents in sequence
- Manages workflow state and transitions

### 4. Services (`services/`)
- **ado_client.py**: Azure DevOps REST API client
- **mcp_client.py**: Model Context Protocol client for tool calling
- **kubernetes.py**: Kubernetes API client for deployment management

### 5. Templates (`templates/`)
- **spring-boot/**: Java code generation templates
- **helm/**: Kubernetes manifest templates
- **context-mapper/**: Context Mapper DSL templates

### 6. Output (`output/`)
- Generated artifacts organized by type
- DDD models, Spring Boot code, deployment configs
- Created at runtime during workflow execution

## File Naming Conventions

- **Python files**: snake_case (e.g., `ideation_agent.py`)
- **Java files**: PascalCase (e.g., `UserService.java`)
- **Configuration files**: lowercase with extensions (e.g., `values.yaml`)
- **Template files**: descriptive names with `.j2` extension
- **Generated files**: descriptive names in appropriate directories

## Dependencies

### Python Dependencies (`requirements.txt`)
- **Core**: LangGraph, LangChain, FastAPI, Pydantic
- **Azure DevOps**: azure-devops, requests
- **Kubernetes**: kubernetes, pyyaml
- **Testing**: pytest, pytest-asyncio
- **Utilities**: python-dotenv, rich, typer

### Java Dependencies (`build.gradle`)
- **Spring Boot**: 3.2.0 with Java 17
- **Data**: Spring Data JPA, H2, PostgreSQL
- **Security**: Spring Security
- **Testing**: JUnit 5, Mockito, Testcontainers
- **Documentation**: SpringDoc OpenAPI

## Configuration

### Environment Variables (`config.env.example`)
- **OpenAI**: API key for LLM integration
- **Azure DevOps**: Organization, project, and PAT
- **Kubernetes**: Kubeconfig path and cluster settings
- **Application**: Logging, environment, and feature flags

### Application Configuration
- **main.py**: FastAPI application with API endpoints
- **workflows/lifecycle.py**: Workflow configuration and orchestration
- **config/**: Environment-specific configuration files

## Testing Strategy

### Test Organization
- **Unit tests**: Individual component testing
- **Integration tests**: Component interaction testing
- **End-to-end tests**: Complete workflow testing
- **Mock services**: External service simulation

### Test Execution
- **pytest**: Python test framework
- **Gradle**: Java test execution
- **Test containers**: Database and service testing
- **CI/CD integration**: Automated testing pipeline

## Deployment

### Local Development
- **Docker Compose**: Local service orchestration
- **Hot reload**: FastAPI development server
- **Mock services**: External service simulation

### Production Deployment
- **Kubernetes**: Container orchestration
- **Helm charts**: Deployment templating
- **CI/CD pipelines**: Automated deployment
- **Monitoring**: Health checks and observability

## Security Considerations

- **Environment variables**: Sensitive configuration management
- **API authentication**: Secure endpoint access
- **Kubernetes RBAC**: Role-based access control
- **Secret management**: Secure credential storage
- **Network policies**: Service-to-service communication control

## Monitoring and Observability

- **Health checks**: Application and service health monitoring
- **Logging**: Structured logging with correlation IDs
- **Metrics**: Prometheus metrics collection
- **Tracing**: Distributed tracing with Jaeger
- **Alerting**: Automated alerting and notification

## Development Workflow

1. **Setup**: Install dependencies and configure environment
2. **Development**: Implement features with TDD approach
3. **Testing**: Run unit, integration, and E2E tests
4. **Validation**: Verify generated artifacts and configurations
5. **Deployment**: Deploy to target environment
6. **Monitoring**: Monitor system health and performance

## Contributing

- **Code style**: Follow PEP 8 for Python, Google style for Java
- **Documentation**: Maintain comprehensive docstrings and README files
- **Testing**: Ensure adequate test coverage for new features
- **Review process**: Submit pull requests for code review
- **CI/CD**: Automated testing and validation pipeline

This project structure provides a comprehensive foundation for the Agentic AI Architect system, enabling automated product development lifecycle management with proper separation of concerns, testing, and deployment capabilities.
