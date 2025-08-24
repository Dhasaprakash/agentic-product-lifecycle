"""
Deployment Agent - Manages Kubernetes deployment and Helm charts.
"""

import logging
import os
import yaml
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from langchain.schema import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel

from models.domain import (
    Feature, SpringBootService, DeploymentConfig, OpenAPISpec
)
from services.kubernetes import KubernetesClient

logger = logging.getLogger(__name__)


class DeploymentAgent:
    """Agent responsible for managing Kubernetes deployment and Helm charts."""
    
    def __init__(self, k8s_client: KubernetesClient, llm_model: str = "gpt-4", temperature: float = 0.7):
        """Initialize the Deployment Agent.
        
        Args:
            k8s_client: Kubernetes client instance
            llm_model: LLM model to use for generation
            temperature: Temperature for LLM generation
        """
        self.k8s_client = k8s_client
        
        # Import LLMFactory here to avoid circular imports
        from agents.ideation import LLMFactory
        
        try:
            self.llm = LLMFactory.create_llm(llm_model, temperature)
            logger.info(f"DeploymentAgent initialized with {llm_model} model")
        except Exception as e:
            logger.error(f"Failed to initialize LLM for DeploymentAgent: {str(e)}")
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
                    logger.warning(f"DeploymentAgent fallback to OpenAI gpt-4o-mini due to: {str(e)}")
                else:
                    raise ValueError("No fallback LLM available")
            except Exception as fallback_error:
                logger.error(f"DeploymentAgent fallback also failed: {str(fallback_error)}")
                raise
        
        self.system_prompt = self._get_system_prompt()
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the deployment agent."""
        return """You are an expert DevOps engineer and Kubernetes specialist specializing in microservices deployment.

Your role is to:
1. Generate Kubernetes manifests and Helm charts
2. Configure deployment strategies and scaling
3. Set up monitoring, logging, and health checks
4. Implement security best practices
5. Create CI/CD pipeline configurations
6. Ensure production-ready deployment configurations

Guidelines:
- Use Kubernetes best practices and patterns
- Implement proper resource limits and requests
- Configure health checks and readiness probes
- Set up proper networking and service discovery
- Include monitoring and observability
- Follow security best practices
- Create scalable and maintainable configurations
- Use Helm for templating and deployment management

Output your response in a structured format that can be parsed by the system."""
    
    async def generate_deployment_config(self, feature: Feature, spring_boot_service: SpringBootService, openapi_spec: OpenAPISpec) -> Dict[str, Any]:
        """Generate complete deployment configuration.
        
        Args:
            feature: Feature object
            spring_boot_service: Spring Boot service configuration
            openapi_spec: OpenAPI specification
            
        Returns:
            Dictionary containing deployment configuration artifacts
        """
        try:
            logger.info(f"Generating deployment configuration for feature: {feature.name}")
            
            # Generate Kubernetes manifests
            k8s_manifests = await self._generate_kubernetes_manifests(feature, spring_boot_service)
            
            # Generate Helm chart
            helm_chart = await self._generate_helm_chart(feature, spring_boot_service, k8s_manifests)
            
            # Generate Docker configuration
            docker_config = await self._generate_docker_config(feature, spring_boot_service)
            
            # Generate CI/CD pipeline
            cicd_pipeline = await self._generate_cicd_pipeline(feature, spring_boot_service)
            
            # Generate monitoring configuration
            monitoring_config = await self._generate_monitoring_config(feature, spring_boot_service)
            
            # Create deployment configuration
            deployment_config = self._create_deployment_config(feature, spring_boot_service)
            
            return {
                "feature_name": feature.name,
                "deployment_config": deployment_config,
                "kubernetes_manifests": k8s_manifests,
                "helm_chart": helm_chart,
                "docker_config": docker_config,
                "cicd_pipeline": cicd_pipeline,
                "monitoring_config": monitoring_config,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate deployment configuration: {str(e)}")
            raise
    
    def _create_deployment_config(self, feature: Feature, spring_boot_service: SpringBootService) -> DeploymentConfig:
        """Create deployment configuration object.
        
        Args:
            feature: Feature object
            spring_boot_service: Spring Boot service configuration
            
        Returns:
            Deployment configuration
        """
        service_name = feature.name.lower().replace(' ', '-')
        
        return DeploymentConfig(
            service_name=service_name,
            namespace=f"{service_name}-ns",
            replicas=2,
            image=f"{service_name}:latest",
            port=8080,
            environment_variables={
                "SPRING_PROFILES_ACTIVE": "prod",
                "SERVER_PORT": "8080",
                "LOGGING_LEVEL": "INFO"
            },
            resource_limits={
                "cpu": "500m",
                "memory": "512Mi"
            },
            resource_requests={
                "cpu": "250m",
                "memory": "256Mi"
            }
        )
    
    async def _generate_kubernetes_manifests(self, feature: Feature, spring_boot_service: SpringBootService) -> Dict[str, Any]:
        """Generate Kubernetes manifests.
        
        Args:
            feature: Feature object
            spring_boot_service: Spring Boot service configuration
            
        Returns:
            Dictionary containing Kubernetes manifests
        """
        prompt = f"""
        Generate Kubernetes manifests for the following Spring Boot service:
        
        Feature: {feature.name}
        Service: {spring_boot_service.name}
        Package: {spring_boot_service.package_name}
        Port: {spring_boot_service.endpoints}
        
        Create comprehensive Kubernetes manifests that include:
        
        1. **Namespace**: Dedicated namespace for the service
        2. **Deployment**: Application deployment with proper replicas and strategy
        3. **Service**: ClusterIP service for internal communication
        4. **Ingress**: External access configuration
        5. **ConfigMap**: Configuration management
        6. **Secret**: Sensitive data management
        7. **HorizontalPodAutoscaler**: Auto-scaling configuration
        8. **NetworkPolicy**: Network security policies
        
        For each manifest, include:
        - Proper labels and annotations
        - Resource limits and requests
        - Health checks and readiness probes
        - Security context and policies
        - Environment-specific configurations
        
        Return the response as a JSON object with this structure:
        {{
            "namespace": "YAML content",
            "deployment": "YAML content",
            "service": "YAML content",
            "ingress": "YAML content",
            "configmap": "YAML content",
            "secret": "YAML content",
            "hpa": "YAML content",
            "networkpolicy": "YAML content"
        }}
        """
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return self._parse_json_response(response.content)
    
    async def _generate_helm_chart(self, feature: Feature, spring_boot_service: SpringBootService, k8s_manifests: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Helm chart structure.
        
        Args:
            feature: Feature object
            spring_boot_service: Spring Boot service configuration
            k8s_manifests: Kubernetes manifests
            
        Returns:
            Dictionary containing Helm chart artifacts
        """
        prompt = f"""
        Generate a Helm chart for the following Spring Boot service:
        
        Feature: {feature.name}
        Service: {spring_boot_service.name}
        Package: {spring_boot_service.package_name}
        
        Create a complete Helm chart structure that includes:
        
        1. **Chart.yaml**: Chart metadata and dependencies
        2. **values.yaml**: Default configuration values
        3. **values-prod.yaml**: Production configuration
        4. **values-dev.yaml**: Development configuration
        5. **templates/**: Kubernetes manifest templates
        6. **templates/deployment.yaml**: Deployment template
        7. **templates/service.yaml**: Service template
        8. **templates/ingress.yaml**: Ingress template
        9. **templates/configmap.yaml**: ConfigMap template
        10. **templates/secret.yaml**: Secret template
        11. **templates/hpa.yaml**: HPA template
        12. **templates/networkpolicy.yaml**: NetworkPolicy template
        13. **templates/namespace.yaml**: Namespace template
        14. **templates/notes.txt**: Installation notes
        15. **templates/_helpers.tpl**: Template helpers
        
        For each template, include:
        - Proper Helm templating syntax
        - Conditional logic for different environments
        - Value substitution and defaults
        - Proper indentation and structure
        
        Return the response as a JSON object with this structure:
        {{
            "chart_yaml": "Chart.yaml content",
            "values_yaml": "values.yaml content",
            "values_prod_yaml": "values-prod.yaml content",
            "values_dev_yaml": "values-dev.yaml content",
            "templates": {{
                "deployment_yaml": "deployment.yaml template",
                "service_yaml": "service.yaml template",
                "ingress_yaml": "ingress.yaml template",
                "configmap_yaml": "configmap.yaml template",
                "secret_yaml": "secret.yaml template",
                "hpa_yaml": "hpa.yaml template",
                "networkpolicy_yaml": "networkpolicy.yaml template",
                "namespace_yaml": "namespace.yaml template",
                "notes_txt": "notes.txt content",
                "helpers_tpl": "_helpers.tpl content"
            }}
        }}
        """
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return self._parse_json_response(response.content)
    
    async def _generate_docker_config(self, feature: Feature, spring_boot_service: SpringBootService) -> Dict[str, Any]:
        """Generate Docker configuration files.
        
        Args:
            feature: Feature object
            spring_boot_service: Spring Boot service configuration
            
        Returns:
            Dictionary containing Docker configuration
        """
        prompt = f"""
        Generate Docker configuration for the following Spring Boot service:
        
        Feature: {feature.name}
        Service: {spring_boot_service.name}
        Package: {spring_boot_service.package_name}
        Java Version: {spring_boot_service.java_version}
        Spring Boot Version: {spring_boot_service.spring_boot_version}
        
        Create Docker configuration that includes:
        
        1. **Dockerfile**: Multi-stage build for production
        2. **docker-compose.yml**: Local development setup
        3. **docker-compose.prod.yml**: Production setup
        4. **.dockerignore**: Files to exclude from build context
        
        For the Dockerfile, include:
        - Multi-stage build (build + runtime)
        - Proper base images for Java 17
        - Layer optimization for caching
        - Security best practices
        - Health check configuration
        
        For docker-compose files, include:
        - Service definition with proper ports
        - Environment variables
        - Volume mounts
        - Network configuration
        - Health checks
        
        Return the response as a JSON object with this structure:
        {{
            "dockerfile": "Dockerfile content",
            "docker_compose_yml": "docker-compose.yml content",
            "docker_compose_prod_yml": "docker-compose.prod.yml content",
            "dockerignore": ".dockerignore content"
        }}
        """
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return self._parse_json_response(response.content)
    
    async def _generate_cicd_pipeline(self, feature: Feature, spring_boot_service: SpringBootService) -> Dict[str, Any]:
        """Generate CI/CD pipeline configuration.
        
        Args:
            feature: Feature object
            spring_boot_service: Spring Boot service configuration
            
        Returns:
            Dictionary containing CI/CD pipeline configuration
        """
        prompt = f"""
        Generate CI/CD pipeline configuration for the following Spring Boot service:
        
        Feature: {feature.name}
        Service: {spring_boot_service.name}
        Package: {spring_boot_service.package_name}
        
        Create CI/CD pipeline configuration that includes:
        
        1. **GitHub Actions**: GitHub Actions workflow
        2. **GitLab CI**: GitLab CI/CD pipeline
        3. **Jenkins**: Jenkins pipeline script
        4. **ArgoCD**: GitOps deployment configuration
        
        For each pipeline, include:
        - Build and test stages
        - Security scanning
        - Docker image building
        - Kubernetes deployment
        - Environment promotion
        - Rollback procedures
        
        Return the response as a JSON object with this structure:
        {{
            "github_actions": "GitHub Actions workflow YAML",
            "gitlab_ci": "GitLab CI/CD pipeline YAML",
            "jenkins": "Jenkins pipeline script",
            "argocd": "ArgoCD application YAML"
        }}
        """
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return self._parse_json_response(response.content)
    
    async def _generate_monitoring_config(self, feature: Feature, spring_boot_service: SpringBootService) -> Dict[str, Any]:
        """Generate monitoring and observability configuration.
        
        Args:
            feature: Feature object
            spring_boot_service: Spring Boot service configuration
            
        Returns:
            Dictionary containing monitoring configuration
        """
        prompt = f"""
        Generate monitoring and observability configuration for the following Spring Boot service:
        
        Feature: {feature.name}
        Service: {spring_boot_service.name}
        Package: {spring_boot_service.package_name}
        
        Create monitoring configuration that includes:
        
        1. **Prometheus**: Service monitoring and metrics
        2. **Grafana**: Dashboard configuration
        3. **Jaeger**: Distributed tracing
        4. **ELK Stack**: Logging configuration
        5. **Alerting**: Alert rules and notifications
        
        For each component, include:
        - Configuration files
        - Dashboard definitions
        - Alert rules
        - Service discovery
        - Data retention policies
        
        Return the response as a JSON object with this structure:
        {{
            "prometheus": "Prometheus configuration",
            "grafana": "Grafana dashboard JSON",
            "jaeger": "Jaeger configuration",
            "elk": "ELK stack configuration",
            "alerting": "Alert rules configuration"
        }}
        """
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        return self._parse_json_response(response.content)
    
    async def deploy_service(self, deployment_config: DeploymentConfig, k8s_manifests: Dict[str, Any]) -> bool:
        """Deploy the service to Kubernetes.
        
        Args:
            deployment_config: Deployment configuration
            k8s_manifests: Kubernetes manifests
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Deploying service {deployment_config.service_name} to Kubernetes")
            
            # Create namespace
            if not self.k8s_client.create_namespace(deployment_config.namespace):
                logger.error(f"Failed to create namespace {deployment_config.namespace}")
                return False
            
            # Apply Kubernetes manifests
            for manifest_type, manifest_content in k8s_manifests.items():
                if manifest_content and manifest_type != "namespace":  # Namespace already created
                    success = self.k8s_client.apply_yaml(manifest_content, deployment_config.namespace)
                    if not success:
                        logger.error(f"Failed to apply {manifest_type} manifest")
                        return False
                    logger.info(f"Applied {manifest_type} manifest successfully")
            
            # Deploy using the deployment configuration
            success = self.k8s_client.deploy_service(deployment_config)
            if not success:
                logger.error(f"Failed to deploy service {deployment_config.service_name}")
                return False
            
            logger.info(f"Successfully deployed service {deployment_config.service_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deploying service: {str(e)}")
            return False
    
    async def deploy_with_helm(self, helm_chart: Dict[str, Any], values: Dict[str, Any], release_name: str, namespace: str) -> bool:
        """Deploy the service using Helm.
        
        Args:
            helm_chart: Helm chart configuration
            values: Values to override
            release_name: Helm release name
            namespace: Target namespace
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Deploying Helm release {release_name} to namespace {namespace}")
            
            # Save Helm chart to temporary directory
            chart_dir = f"/tmp/helm-chart-{release_name}"
            os.makedirs(chart_dir, exist_ok=True)
            
            # Create Chart.yaml
            chart_yaml_path = os.path.join(chart_dir, "Chart.yaml")
            with open(chart_yaml_path, 'w') as f:
                f.write(helm_chart['chart_yaml'])
            
            # Create values.yaml
            values_yaml_path = os.path.join(chart_dir, "values.yaml")
            with open(values_yaml_path, 'w') as f:
                f.write(helm_chart['values_yaml'])
            
            # Create templates directory
            templates_dir = os.path.join(chart_dir, "templates")
            os.makedirs(templates_dir, exist_ok=True)
            
            # Create template files
            for template_name, template_content in helm_chart['templates'].items():
                if template_content:
                    template_path = os.path.join(templates_dir, template_name)
                    with open(template_path, 'w') as f:
                        f.write(template_content)
            
            # Create custom values file
            custom_values_path = os.path.join(chart_dir, "custom-values.yaml")
            with open(custom_values_path, 'w') as f:
                yaml.dump(values, f, default_flow_style=False)
            
            # Deploy using Helm
            # Note: This would require Helm CLI to be available
            # For now, we'll simulate the deployment
            logger.info(f"Helm chart prepared at {chart_dir}")
            logger.info(f"To deploy: helm install {release_name} {chart_dir} -f {custom_values_path} -n {namespace}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error deploying with Helm: {str(e)}")
            return False
    
    async def get_deployment_status(self, service_name: str, namespace: str) -> Dict[str, Any]:
        """Get the deployment status of a service.
        
        Args:
            service_name: Name of the service
            namespace: Namespace of the service
            
        Returns:
            Deployment status information
        """
        try:
            # Get pod status
            pod_status = self.k8s_client.get_pod_status(service_name, namespace)
            
            # Get service status
            service_status = self.k8s_client.get_service_status(service_name, namespace)
            
            # Get logs
            logs = self.k8s_client.get_logs(service_name, namespace)
            
            return {
                "service_name": service_name,
                "namespace": namespace,
                "pod_status": pod_status,
                "service_status": service_status,
                "logs": logs,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting deployment status: {str(e)}")
            return {"error": str(e)}
    
    async def scale_service(self, service_name: str, replicas: int, namespace: str) -> bool:
        """Scale a service deployment.
        
        Args:
            service_name: Name of the service
            replicas: Number of replicas
            namespace: Namespace of the service
            
        Returns:
            True if successful, False otherwise
        """
        try:
            success = self.k8s_client.scale_deployment(service_name, replicas, namespace)
            if success:
                logger.info(f"Scaled service {service_name} to {replicas} replicas")
            else:
                logger.error(f"Failed to scale service {service_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error scaling service: {str(e)}")
            return False
    
    async def rollback_deployment(self, service_name: str, namespace: str, revision: int = None) -> bool:
        """Rollback a deployment to a previous revision.
        
        Args:
            service_name: Name of the service
            namespace: Namespace of the service
            revision: Revision to rollback to (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # This would require additional Kubernetes API calls
            # For now, we'll log the rollback request
            logger.info(f"Rollback requested for service {service_name} in namespace {namespace}")
            if revision:
                logger.info(f"Rolling back to revision {revision}")
            
            # In a real implementation, you would:
            # 1. Get deployment history
            # 2. Rollback to specified revision
            # 3. Monitor rollback progress
            
            return True
            
        except Exception as e:
            logger.error(f"Error rolling back deployment: {str(e)}")
            return False
    
    def _parse_json_response(self, response_content: str) -> Any:
        """Parse JSON response from LLM.
        
        Args:
            response_content: Response content from LLM
            
        Returns:
            Parsed JSON data
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
            
            return json.loads(json_str)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            logger.error(f"Response content: {response_content}")
            raise ValueError(f"Invalid JSON response from LLM: {str(e)}")
    
    async def validate_deployment_config(self, deployment_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the generated deployment configuration.
        
        Args:
            deployment_config: Generated deployment configuration
            
        Returns:
            Validation result
        """
        validation_errors = []
        warnings = []
        
        # Check required components
        if not deployment_config.get("kubernetes_manifests"):
            validation_errors.append("No Kubernetes manifests generated")
        
        if not deployment_config.get("helm_chart"):
            validation_errors.append("No Helm chart generated")
        
        if not deployment_config.get("docker_config"):
            validation_errors.append("No Docker configuration generated")
        
        # Check Kubernetes manifests
        k8s_manifests = deployment_config.get("kubernetes_manifests", {})
        required_manifests = ["deployment", "service", "namespace"]
        for manifest in required_manifests:
            if not k8s_manifests.get(manifest):
                validation_errors.append(f"Missing required Kubernetes manifest: {manifest}")
        
        # Check Helm chart
        helm_chart = deployment_config.get("helm_chart", {})
        if not helm_chart.get("chart_yaml"):
            validation_errors.append("Missing Chart.yaml in Helm chart")
        
        if not helm_chart.get("values_yaml"):
            validation_errors.append("Missing values.yaml in Helm chart")
        
        return {
            "is_valid": len(validation_errors) == 0,
            "errors": validation_errors,
            "warnings": warnings
        }
    
    def save_deployment_artifacts(self, deployment_config: Dict[str, Any], output_dir: str = "output/deployment") -> Dict[str, str]:
        """Save deployment artifacts to files.
        
        Args:
            deployment_config: Generated deployment configuration
            output_dir: Output directory
            
        Returns:
            Dictionary mapping artifact types to file paths
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            saved_files = {}
            
            # Save Kubernetes manifests
            k8s_dir = os.path.join(output_dir, "kubernetes")
            os.makedirs(k8s_dir, exist_ok=True)
            
            for manifest_type, manifest_content in deployment_config.get("kubernetes_manifests", {}).items():
                if manifest_content:
                    manifest_file = os.path.join(k8s_dir, f"{manifest_type}.yaml")
                    with open(manifest_file, 'w') as f:
                        f.write(manifest_content)
                    saved_files[f"k8s_{manifest_type}"] = manifest_file
            
            # Save Helm chart
            helm_dir = os.path.join(output_dir, "helm")
            os.makedirs(helm_dir, exist_ok=True)
            
            helm_chart = deployment_config.get("helm_chart", {})
            if helm_chart.get("chart_yaml"):
                chart_file = os.path.join(helm_dir, "Chart.yaml")
                with open(chart_file, 'w') as f:
                    f.write(helm_chart["chart_yaml"])
                saved_files['helm_chart'] = chart_file
            
            if helm_chart.get("values_yaml"):
                values_file = os.path.join(helm_dir, "values.yaml")
                with open(values_file, 'w') as f:
                    f.write(helm_chart["values_yaml"])
                saved_files['helm_values'] = values_file
            
            # Save Docker configuration
            docker_dir = os.path.join(output_dir, "docker")
            os.makedirs(docker_dir, exist_ok=True)
            
            docker_config = deployment_config.get("docker_config", {})
            for config_type, config_content in docker_config.items():
                if config_content:
                    config_file = os.path.join(docker_dir, config_type)
                    with open(config_file, 'w') as f:
                        f.write(config_content)
                    saved_files[f"docker_{config_type}"] = config_file
            
            # Save CI/CD pipeline
            cicd_dir = os.path.join(output_dir, "cicd")
            os.makedirs(cicd_dir, exist_ok=True)
            
            cicd_pipeline = deployment_config.get("cicd_pipeline", {})
            for pipeline_type, pipeline_content in cicd_pipeline.items():
                if pipeline_content:
                    pipeline_file = os.path.join(cicd_dir, f"{pipeline_type}.yml")
                    with open(pipeline_file, 'w') as f:
                        f.write(pipeline_content)
                    saved_files[f"cicd_{pipeline_type}"] = pipeline_file
            
            # Save monitoring configuration
            monitoring_dir = os.path.join(output_dir, "monitoring")
            os.makedirs(monitoring_dir, exist_ok=True)
            
            monitoring_config = deployment_config.get("monitoring_config", {})
            for config_type, config_content in monitoring_config.items():
                if config_content:
                    config_file = os.path.join(monitoring_dir, f"{config_type}.yml")
                    with open(config_file, 'w') as f:
                        f.write(config_content)
                    saved_files[f"monitoring_{config_type}"] = config_file
            
            # Save deployment configuration summary
            summary_file = os.path.join(output_dir, "deployment_summary.json")
            with open(summary_file, 'w') as f:
                json.dump(deployment_config, f, indent=2, default=str)
            saved_files['summary'] = summary_file
            
            logger.info(f"Saved deployment artifacts to {output_dir}")
            return saved_files
            
        except Exception as e:
            logger.error(f"Failed to save deployment artifacts: {str(e)}")
            raise
