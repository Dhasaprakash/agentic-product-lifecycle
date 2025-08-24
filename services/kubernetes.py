"""
Kubernetes client for deploying and managing services.
"""

import os
import logging
import yaml
from typing import Dict, Any, List, Optional
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from kubernetes.stream import stream

from models.domain import DeploymentConfig

logger = logging.getLogger(__name__)


class KubernetesClient:
    """Client for interacting with Kubernetes cluster."""
    
    def __init__(self, kubeconfig_path: Optional[str] = None, in_cluster: bool = False):
        """Initialize the Kubernetes client.
        
        Args:
            kubeconfig_path: Path to kubeconfig file
            in_cluster: Whether running inside a Kubernetes cluster
        """
        try:
            if in_cluster:
                config.load_incluster_config()
                logger.info("Using in-cluster configuration")
            elif kubeconfig_path:
                config.load_kube_config(config_file=kubeconfig_path)
                logger.info(f"Loaded kubeconfig from {kubeconfig_path}")
            else:
                config.load_kube_config()
                logger.info("Loaded default kubeconfig")
            
            # Initialize API clients
            self.core_v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            self.networking_v1 = client.NetworkingV1Api()
            self.rbac_v1 = client.RbacAuthorizationV1Api()
            
            # Test connection
            self._test_connection()
            
        except Exception as e:
            logger.error(f"Failed to initialize Kubernetes client: {str(e)}")
            raise
    
    def _test_connection(self):
        """Test the Kubernetes connection."""
        try:
            self.core_v1.list_namespace()
            logger.info("Successfully connected to Kubernetes cluster")
        except Exception as e:
            logger.error(f"Failed to connect to Kubernetes cluster: {str(e)}")
            raise
    
    def create_namespace(self, namespace: str) -> bool:
        """Create a namespace.
        
        Args:
            namespace: Name of the namespace
            
        Returns:
            True if successful, False otherwise
        """
        try:
            namespace_obj = client.V1Namespace(
                metadata=client.V1ObjectMeta(name=namespace)
            )
            
            self.core_v1.create_namespace(namespace_obj)
            logger.info(f"Created namespace: {namespace}")
            return True
            
        except ApiException as e:
            if e.status == 409:  # Already exists
                logger.info(f"Namespace {namespace} already exists")
                return True
            else:
                logger.error(f"Failed to create namespace {namespace}: {str(e)}")
                return False
        except Exception as e:
            logger.error(f"Failed to create namespace {namespace}: {str(e)}")
            return False
    
    def deploy_service(self, deployment_config: DeploymentConfig) -> bool:
        """Deploy a service to Kubernetes.
        
        Args:
            deployment_config: Deployment configuration
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create namespace if it doesn't exist
            if not self.create_namespace(deployment_config.namespace):
                return False
            
            # Create deployment
            if not self._create_deployment(deployment_config):
                return False
            
            # Create service
            if not self._create_service(deployment_config):
                return False
            
            # Create ingress if needed
            if not self._create_ingress(deployment_config):
                return False
            
            logger.info(f"Successfully deployed service {deployment_config.service_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to deploy service {deployment_config.service_name}: {str(e)}")
            return False
    
    def _create_deployment(self, deployment_config: DeploymentConfig) -> bool:
        """Create a Kubernetes deployment.
        
        Args:
            deployment_config: Deployment configuration
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Define container
            container = client.V1Container(
                name=deployment_config.service_name,
                image=deployment_config.image,
                ports=[client.V1ContainerPort(container_port=deployment_config.port)],
                env=[client.V1EnvVar(name=k, value=v) for k, v in deployment_config.environment_variables.items()],
                resources=client.V1ResourceRequirements(
                    limits=deployment_config.resource_limits,
                    requests=deployment_config.resource_requests
                ),
                liveness_probe=client.V1Probe(
                    http_get=client.V1HTTPGetAction(path=deployment_config.liveness_probe_path),
                    initial_delay_seconds=30,
                    period_seconds=10
                ),
                readiness_probe=client.V1Probe(
                    http_get=client.V1HTTPGetAction(path=deployment_config.readiness_probe_path),
                    initial_delay_seconds=5,
                    period_seconds=5
                )
            )
            
            # Define deployment
            deployment = client.V1Deployment(
                metadata=client.V1ObjectMeta(
                    name=deployment_config.service_name,
                    namespace=deployment_config.namespace
                ),
                spec=client.V1DeploymentSpec(
                    replicas=deployment_config.replicas,
                    selector=client.V1LabelSelector(
                        match_labels={"app": deployment_config.service_name}
                    ),
                    template=client.V1PodTemplateSpec(
                        metadata=client.V1ObjectMeta(
                            labels={"app": deployment_config.service_name}
                        ),
                        spec=client.V1PodSpec(containers=[container])
                    )
                )
            )
            
            # Create deployment
            self.apps_v1.create_namespaced_deployment(
                namespace=deployment_config.namespace,
                body=deployment
            )
            
            logger.info(f"Created deployment for {deployment_config.service_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create deployment for {deployment_config.service_name}: {str(e)}")
            return False
    
    def _create_service(self, deployment_config: DeploymentConfig) -> bool:
        """Create a Kubernetes service.
        
        Args:
            deployment_config: Deployment configuration
            
        Returns:
            True if successful, False otherwise
        """
        try:
            service = client.V1Service(
                metadata=client.V1ObjectMeta(
                    name=deployment_config.service_name,
                    namespace=deployment_config.namespace
                ),
                spec=client.V1ServiceSpec(
                    selector={"app": deployment_config.service_name},
                    ports=[client.V1ServicePort(
                        port=deployment_config.port,
                        target_port=deployment_config.port
                    )],
                    type="ClusterIP"
                )
            )
            
            self.core_v1.create_namespaced_service(
                namespace=deployment_config.namespace,
                body=service
            )
            
            logger.info(f"Created service for {deployment_config.service_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create service for {deployment_config.service_name}: {str(e)}")
            return False
    
    def _create_ingress(self, deployment_config: DeploymentConfig) -> bool:
        """Create a Kubernetes ingress.
        
        Args:
            deployment_config: Deployment configuration
            
        Returns:
            True if successful, False otherwise
        """
        try:
            ingress = client.V1Ingress(
                metadata=client.V1ObjectMeta(
                    name=deployment_config.service_name,
                    namespace=deployment_config.namespace,
                    annotations={
                        "nginx.ingress.kubernetes.io/rewrite-target": "/",
                        "kubernetes.io/ingress.class": "nginx"
                    }
                ),
                spec=client.V1IngressSpec(
                    rules=[client.V1IngressRule(
                        host=f"{deployment_config.service_name}.local",
                        http=client.V1HTTPIngressRuleValue(
                            paths=[client.V1HTTPIngressPath(
                                path="/",
                                path_type="Prefix",
                                backend=client.V1IngressBackend(
                                    service=client.V1IngressServiceBackend(
                                        name=deployment_config.service_name,
                                        port=client.V1ServiceBackendPort(
                                            number=deployment_config.port
                                        )
                                    )
                                )
                            )]
                        )
                    )]
                )
            )
            
            self.networking_v1.create_namespaced_ingress(
                namespace=deployment_config.namespace,
                body=ingress
            )
            
            logger.info(f"Created ingress for {deployment_config.service_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create ingress for {deployment_config.service_name}: {str(e)}")
            return False
    
    def get_pod_status(self, service_name: str, namespace: str = "default") -> Dict[str, Any]:
        """Get the status of pods for a service.
        
        Args:
            service_name: Name of the service
            namespace: Namespace of the service
            
        Returns:
            Dictionary containing pod status information
        """
        try:
            pods = self.core_v1.list_namespaced_pod(
                namespace=namespace,
                label_selector=f"app={service_name}"
            )
            
            pod_statuses = []
            for pod in pods.items:
                pod_statuses.append({
                    'name': pod.metadata.name,
                    'status': pod.status.phase,
                    'ready': pod.status.container_statuses[0].ready if pod.status.container_statuses else False,
                    'restarts': pod.status.container_statuses[0].restart_count if pod.status.container_statuses else 0,
                    'age': self._get_age(pod.metadata.creation_timestamp)
                })
            
            return {
                'service_name': service_name,
                'namespace': namespace,
                'pods': pod_statuses,
                'total_pods': len(pod_statuses),
                'ready_pods': sum(1 for p in pod_statuses if p['ready'])
            }
            
        except Exception as e:
            logger.error(f"Failed to get pod status for {service_name}: {str(e)}")
            return {}
    
    def get_service_status(self, service_name: str, namespace: str = "default") -> Dict[str, Any]:
        """Get the status of a service.
        
        Args:
            service_name: Name of the service
            namespace: Namespace of the service
            
        Returns:
            Dictionary containing service status information
        """
        try:
            service = self.core_v1.read_namespaced_service(
                name=service_name,
                namespace=namespace
            )
            
            return {
                'name': service.metadata.name,
                'namespace': service.metadata.namespace,
                'type': service.spec.type,
                'cluster_ip': service.spec.cluster_ip,
                'ports': [{'port': p.port, 'target_port': p.target_port} for p in service.spec.ports],
                'age': self._get_age(service.metadata.creation_timestamp)
            }
            
        except Exception as e:
            logger.error(f"Failed to get service status for {service_name}: {str(e)}")
            return {}
    
    def scale_deployment(self, service_name: str, replicas: int, namespace: str = "default") -> bool:
        """Scale a deployment.
        
        Args:
            service_name: Name of the service
            replicas: Number of replicas
            namespace: Namespace of the service
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.apps_v1.patch_namespaced_deployment_scale(
                name=service_name,
                namespace=namespace,
                body={'spec': {'replicas': replicas}}
            )
            
            logger.info(f"Scaled {service_name} to {replicas} replicas")
            return True
            
        except Exception as e:
            logger.error(f"Failed to scale {service_name}: {str(e)}")
            return False
    
    def delete_service(self, service_name: str, namespace: str = "default") -> bool:
        """Delete a service and its deployment.
        
        Args:
            service_name: Name of the service
            namespace: Namespace of the service
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete deployment
            self.apps_v1.delete_namespaced_deployment(
                name=service_name,
                namespace=namespace
            )
            
            # Delete service
            self.core_v1.delete_namespaced_service(
                name=service_name,
                namespace=namespace
            )
            
            # Delete ingress
            try:
                self.networking_v1.delete_namespaced_ingress(
                    name=service_name,
                    namespace=namespace
                )
            except ApiException:
                pass  # Ingress might not exist
            
            logger.info(f"Deleted service {service_name} from namespace {namespace}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete service {service_name}: {str(e)}")
            return False
    
    def get_logs(self, service_name: str, namespace: str = "default", tail_lines: int = 100) -> str:
        """Get logs from a service.
        
        Args:
            service_name: Name of the service
            namespace: Namespace of the service
            tail_lines: Number of lines to retrieve
            
        Returns:
            Log content as string
        """
        try:
            pods = self.core_v1.list_namespaced_pod(
                namespace=namespace,
                label_selector=f"app={service_name}"
            )
            
            if not pods.items:
                return f"No pods found for service {service_name}"
            
            # Get logs from the first pod
            pod_name = pods.items[0].metadata.name
            logs = self.core_v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                tail_lines=tail_lines
            )
            
            return logs
            
        except Exception as e:
            logger.error(f"Failed to get logs for {service_name}: {str(e)}")
            return f"Error retrieving logs: {str(e)}"
    
    def _get_age(self, creation_timestamp) -> str:
        """Calculate the age of a resource.
        
        Args:
            creation_timestamp: Creation timestamp
            
        Returns:
            Age as a formatted string
        """
        if not creation_timestamp:
            return "Unknown"
        
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        age = now - creation_timestamp.replace(tzinfo=timezone.utc)
        
        if age.days > 0:
            return f"{age.days}d"
        elif age.seconds > 3600:
            return f"{age.seconds // 3600}h"
        elif age.seconds > 60:
            return f"{age.seconds // 60}m"
        else:
            return f"{age.seconds}s"
    
    def apply_yaml(self, yaml_content: str, namespace: str = "default") -> bool:
        """Apply a YAML manifest to the cluster.
        
        Args:
            yaml_content: YAML content to apply
            namespace: Namespace to apply to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Parse YAML
            manifests = yaml.safe_load_all(yaml_content)
            
            for manifest in manifests:
                if manifest is None:
                    continue
                
                kind = manifest.get('kind')
                name = manifest.get('metadata', {}).get('name')
                
                if not kind or not name:
                    continue
                
                # Set namespace if not specified
                if 'namespace' not in manifest.get('metadata', {}):
                    manifest['metadata']['namespace'] = namespace
                
                # Apply based on kind
                if kind == 'Deployment':
                    self.apps_v1.create_namespaced_deployment(
                        namespace=namespace,
                        body=manifest
                    )
                elif kind == 'Service':
                    self.core_v1.create_namespaced_service(
                        namespace=namespace,
                        body=manifest
                    )
                elif kind == 'Ingress':
                    self.networking_v1.create_namespaced_ingress(
                        namespace=namespace,
                        body=manifest
                    )
                elif kind == 'ConfigMap':
                    self.core_v1.create_namespaced_config_map(
                        namespace=namespace,
                        body=manifest
                    )
                elif kind == 'Secret':
                    self.core_v1.create_namespaced_secret(
                        namespace=namespace,
                        body=manifest
                    )
                
                logger.info(f"Applied {kind} {name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply YAML: {str(e)}")
            return False
