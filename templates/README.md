# Templates Directory

This directory contains code generation templates for the Agentic AI Architect system.

## 📁 **Directory Structure**

```
templates/
├── spring-boot/           # Spring Boot microservice templates
│   ├── pom.xml.j2        # Maven POM template
│   ├── Application.java.j2 # Main application class
│   ├── Controller.java.j2 # REST controller
│   ├── Service.java.j2    # Service layer
│   ├── Repository.java.j2 # Repository interface
│   ├── Entity.java.j2     # JPA entity
│   └── Status.java.j2     # Status enum
├── helm/                  # Kubernetes Helm chart templates
│   ├── Chart.yaml.j2      # Chart metadata
│   ├── values.yaml.j2     # Default values
│   └── templates/         # Kubernetes manifests
│       └── deployment.yaml.j2
└── context-mapper/        # Domain-Driven Design templates
    ├── context-map.cml.j2 # Context Mapper DSL
    └── plantuml-diagram.puml.j2 # Architecture diagrams
```

## 🚀 **Usage**

### **Spring Boot Templates**

These templates generate production-ready Spring Boot microservices with:

- **Clean Architecture**: Controller → Service → Repository pattern
- **JPA Integration**: Entity management with auditing
- **Validation**: Bean validation with custom constraints
- **Documentation**: OpenAPI annotations for API documentation
- **Testing**: Testable service layer with dependency injection

**Template Variables:**
- `{{ service_name }}`: The name of the service (e.g., "UserManagement")
- `{{ service_name_lower }}`: Lowercase service name (e.g., "userManagement")
- `{{ package_name }}`: Java package name (e.g., "com.example.usermanagement")
- `{{ service_description }}`: Service description
- `{{ table_name }}`: Database table name
- `{{ version }}`: Service version

### **Helm Templates**

These templates generate Kubernetes deployment configurations with:

- **Production Ready**: Resource limits, health checks, environment variables
- **Database Integration**: PostgreSQL dependency configuration
- **Scalability**: Horizontal pod autoscaling support
- **Security**: Service accounts and security contexts
- **Monitoring**: Health check endpoints and metrics

**Template Variables:**
- `{{ service_name_lower }}`: Lowercase service name
- `{{ image_repository }}`: Docker image repository
- `{{ image_tag }}`: Docker image tag
- `{{ database_host }}`: Database hostname
- `{{ database_port }}`: Database port
- `{{ database_name }}`: Database name

### **Context Mapper Templates**

These templates generate Domain-Driven Design artifacts with:

- **Bounded Contexts**: Clear domain boundaries
- **Aggregates**: Domain entities with business logic
- **Value Objects**: Immutable domain concepts
- **Domain Services**: Business logic coordination
- **Context Maps**: Inter-context relationships

**Template Variables:**
- `{{ bounded_context_name }}`: Name of the bounded context
- `{{ bounded_context_name_lower }}`: Lowercase context name
- `{{ domain_vision_statement }}`: Domain vision description

## 🔧 **Template Engine**

The system uses **Jinja2** templating engine with:

- **Conditional Logic**: `{% if %}` statements for optional features
- **Loops**: `{% for %}` statements for collections
- **Variables**: `{{ variable }}` syntax for dynamic content
- **Filters**: `{{ value | filter }}` for data transformation
- **Inheritance**: Template extension and composition

## 📝 **Example Usage**

### **Generating a Spring Boot Service**

```python
from jinja2 import Template

# Load template
with open('templates/spring-boot/Controller.java.j2', 'r') as f:
    template = Template(f.read())

# Render with context
context = {
    'service_name': 'UserManagement',
    'service_name_lower': 'userManagement',
    'package_name': 'com.example.usermanagement',
    'service_description': 'User management operations'
}

java_code = template.render(**context)
```

### **Generating a Helm Chart**

```python
# Load values template
with open('templates/helm/values.yaml.j2', 'r') as f:
    template = Template(f.read())

# Render with context
context = {
    'service_name_lower': 'user-management',
    'image_repository': 'myregistry/user-management',
    'image_tag': '1.0.0',
    'database_host': 'postgresql-service',
    'database_port': '5432'
}

helm_values = template.render(**context)
```

## 🎯 **Customization**

### **Adding New Templates**

1. Create a new `.j2` file in the appropriate directory
2. Use Jinja2 syntax for dynamic content
3. Document template variables in this README
4. Test with various input contexts

### **Modifying Existing Templates**

1. Maintain backward compatibility when possible
2. Update this README with new variables
3. Test template rendering with existing code
4. Consider template versioning for major changes

## 🧪 **Testing Templates**

```bash
# Test template rendering
python -c "
from jinja2 import Template
with open('templates/spring-boot/Controller.java.j2', 'r') as f:
    template = Template(f.read())
context = {'service_name': 'TestService', 'service_name_lower': 'testService', 'package_name': 'com.test'}
print(template.render(**context))
"
```

## 📚 **Best Practices**

1. **Consistent Naming**: Use consistent variable naming conventions
2. **Documentation**: Document all template variables and their purpose
3. **Validation**: Validate template variables before rendering
4. **Error Handling**: Provide meaningful error messages for missing variables
5. **Testing**: Test templates with various input combinations
6. **Versioning**: Version templates when making breaking changes

## 🔗 **Related Documentation**

- [Jinja2 Template Engine](https://jinja.palletsprojects.com/)
- [Spring Boot Reference](https://spring.io/projects/spring-boot)
- [Helm Documentation](https://helm.sh/docs/)
- [Context Mapper DSL](https://contextmapper.org/)
- [PlantUML](https://plantuml.com/)
