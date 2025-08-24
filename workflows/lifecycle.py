"""
Product Lifecycle Workflow - Main orchestration using LangGraph.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from models.domain import (
    WorkflowState, IdeationRequest, IdeationResponse, Feature, Epic, UserStory, BoundedContext, Priority, StoryType
)
from agents.ideation import IdeationAgent
# RequirementsAgent import removed - functionality now integrated into IdeationAgent
from agents.design import DesignAgent
from agents.codegen import CodeGenerationAgent
from agents.deployment import DeploymentAgent
from services.ado_client import AzureDevOpsClient
from services.kubernetes import KubernetesClient

logger = logging.getLogger(__name__)


class ProductLifecycleWorkflow:
    """Main workflow orchestration for the product lifecycle."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the workflow.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Get LLM configuration
        self.llm_model = config.get("llm_model", "gpt-4o-mini")
        self.llm_temperature = config.get("llm_temperature", 0.7)
        
        logger.info(f"Initializing workflow with LLM model: {self.llm_model}, temperature: {self.llm_temperature}")
        
        # Initialize services first
        self.ado_client = AzureDevOpsClient(
            organization=config["ado_organization"],
            project=config["ado_project"],
            personal_access_token=config["ado_pat"]
        )
        
        # Initialize agents with required services - all using the same LLM model
        self.ideation_agent = IdeationAgent(
            llm_model=self.llm_model,
            temperature=self.llm_temperature,
            ado_client=self.ado_client
        )
        
        # Initialize Kubernetes client optionally
        self.k8s_client = None
        try:
            if config.get("kubeconfig_path") or config.get("in_cluster"):
                self.k8s_client = KubernetesClient(
                    kubeconfig_path=config.get("kubeconfig_path"),
                    in_cluster=config.get("in_cluster", False)
                )
                logger.info("Kubernetes client initialized successfully")
            else:
                logger.info("Kubernetes configuration not provided, skipping K8s initialization")
        except Exception as e:
            logger.warning(f"Failed to initialize Kubernetes client: {str(e)}")
            logger.warning("Deployment features will be limited")
            self.k8s_client = None
        
        # Initialize other agents - all using the same LLM model for consistency
        # Note: requirements_agent removed - Azure DevOps creation now handled by ideation_agent
        self.design_agent = DesignAgent(
            llm_model=self.llm_model,
            temperature=self.llm_temperature
        )
        self.codegen_agent = CodeGenerationAgent(
            llm_model=self.llm_model,
            temperature=self.llm_temperature
        )
        self.deployment_agent = DeploymentAgent(
            self.k8s_client,
            llm_model=self.llm_model,
            temperature=self.llm_temperature
        ) if self.k8s_client else None
        
        logger.info(f"All agents initialized with LLM model: {self.llm_model}")
        
        # Initialize checkpoint memory
        self.memory = MemorySaver()
        
        # Simple state storage for workflow management
        self.workflow_states = {}
        
        # Build workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow.
        
        Returns:
            StateGraph workflow
        """
        # Create workflow graph
        workflow = StateGraph(WorkflowState)
        
        # Add nodes
        workflow.add_node("ideation", self._ideation_step)
        workflow.add_node("human_approval", self._human_approval_step)
        workflow.add_node("design", self._design_step)
        workflow.add_node("code_generation", self._code_generation_step)
        workflow.add_node("deployment", self._deployment_step)
        workflow.add_node("validation", self._validation_step)
        
        # Set entry point
        workflow.set_entry_point("ideation")
        
        # Add edges
        workflow.add_edge("ideation", "human_approval")
        workflow.add_conditional_edges(
            "human_approval",
            self._should_proceed,
            {
                "proceed": "design",
                "reject": END
            }
        )
        workflow.add_edge("design", "code_generation")
        workflow.add_edge("code_generation", "deployment")
        workflow.add_edge("deployment", "validation")
        workflow.add_edge("validation", END)
        
        return workflow.compile(checkpointer=self.memory)
    
    async def _ideation_step(self, state: WorkflowState) -> WorkflowState:
        """Execute the ideation step.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        try:
            logger.info(f"Starting ideation step with LLM model: {self.llm_model}")
            
            state.current_step = "ideation"
            state.status = "in_progress"
            
            # Extract feature information from metadata
            feature_name = state.metadata.get("feature_name", "Unknown")
            feature_description = state.metadata.get("feature_description", "")
            priority = state.metadata.get("priority", "Medium")
            business_context = state.metadata.get("business_context", "")
            target_users = state.metadata.get("target_users", [])
            success_metrics = state.metadata.get("success_metrics", [])
            
            logger.info(f"Feature name from actual metadata: {feature_name}")
            
            # Create IdeationRequest object (not Feature object)
            from models.domain import IdeationRequest
            ideation_request = IdeationRequest(
                feature_name=feature_name,
                description=feature_description,
                priority=Priority(priority),
                business_context=business_context,
                target_users=target_users,
                success_metrics=success_metrics
            )
            
            # Generate ideation using Azure DevOps integration
            ideation_result = await self.ideation_agent.create_azure_devops_workflow(ideation_request)
            
            if ideation_result["status"] == "success":
                # Extract stories and bounded contexts from ideation result
                stories = ideation_result.get("work_items", {}).get("user_stories", [])
                
                # Extract bounded contexts from the ideation response, not just the summary
                # The ideation agent generates bounded contexts during feature breakdown
                ideation_response = await self.ideation_agent.generate_feature_breakdown(ideation_request)
                bounded_contexts = ideation_response.bounded_contexts if ideation_response else []
                
                # Create a Feature object for the workflow state
                from models.domain import Feature
                feature = Feature(
                    id=f"feature-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                    name=feature_name,
                    description=feature_description,
                    priority=Priority(priority),
                    epic_id=ideation_result.get("epic_id", "epic-temp"),
                    business_requirements=business_context
                )
                state.feature = feature
                
                # Convert to domain objects with proper IDs
                state.stories = [
                    UserStory(
                        id=str(story_id),
                        title=f"Story {story_id}",
                        description="Generated story",
                        story_type=StoryType.USER_STORY,
                        priority=Priority.HIGH,
                        epic_id="epic-temp"
                    ) for story_id in stories
                ]
                
                state.bounded_contexts = bounded_contexts
                
                # Store ideation results in metadata
                state.metadata["ideation_result"] = ideation_result
                state.metadata["ideation_summary"] = ideation_result.get("ideation_summary", {})
                
                # Update domain objects with actual data
                state.metadata["domain_objects"] = {
                    "feature": feature_name,
                    "epic": ideation_result.get("ideation_summary", {}).get("epic_title", ""),
                    "stories": len(stories),
                    "bounded_contexts": len(bounded_contexts)
                }
                
                logger.info(f"Ideation step completed successfully with {len(stories)} stories and {len(bounded_contexts)} bounded contexts using LLM model: {self.llm_model}")
                logger.info(f"Domain objects populated: feature={feature_name}, epic={ideation_result.get('ideation_summary', {}).get('epic_title', '')}, stories={len(stories)}, bounded_contexts={len(bounded_contexts)}")
            else:
                state.status = "failed"
                state.errors.append(f"Ideation step failed: {ideation_result.get('error', 'Unknown error')}")
                logger.error(f"Ideation step failed: {ideation_result}")
            
        except Exception as e:
            logger.error(f"Error in ideation step: {str(e)}")
            state.errors.append(f"Ideation step failed: {str(e)}")
            state.status = "failed"
        
        return state
    
    async def _human_approval_step(self, state: WorkflowState) -> WorkflowState:
        """Execute the human approval step.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        try:
            logger.info(f"Starting human approval step with LLM model: {self.llm_model}")
            
            state.current_step = "human_approval"
            state.status = "waiting_for_approval"
            
            # Display ideation results for human approval
            ideation_summary = state.metadata.get("ideation_summary", {})
            
            print("\n" + "="*80)
            print("🤖 AI-GENERATED IDEATION RESULTS - HUMAN APPROVAL REQUIRED")
            print("="*80)
            print()
            
            if "epic_title" in ideation_summary:
                print(f"🏗️  Epic Created:")
                print(f"   ID: {state.metadata.get('ideation_result', {}).get('epic_id', 'N/A')}")
                print(f"   Title: {ideation_summary['epic_title']}")
                print()
            
            if "feature_name" in ideation_summary:
                print(f"🎯 Feature Created:")
                print(f"   ID: {state.metadata.get('ideation_result', {}).get('feature_id', 'N/A')}")
                print(f"   Name: {ideation_summary['feature_name']}")
                print()
            
            stories_count = ideation_summary.get("user_stories_count", 0)
            if stories_count > 0:
                print(f"📝 User Stories Created:")
                print(f"   Count: {stories_count}")
                story_ids = state.metadata.get('ideation_result', {}).get('work_items', {}).get('user_stories', [])
                if story_ids:
                    print(f"   IDs: {', '.join(map(str, story_ids))}")
                print()
            
            tasks_count = ideation_summary.get("tasks_created", 0)
            if tasks_count > 0:
                print(f"✅ Acceptance Criteria Tasks Created:")
                print(f"   Count: {tasks_count}")
                print()
            
            story_points = ideation_summary.get("total_story_points", 0)
            if story_points > 0:
                print(f"📊 Story Points:")
                print(f"   Total: {story_points}")
                print()
            
            estimated_effort = ideation_summary.get("estimated_effort", "Unknown")
            if estimated_effort != "Unknown":
                print(f"⏱️  Estimated Effort:")
                print(f"   {estimated_effort}")
                print()
            
            risks = ideation_summary.get("risks", [])
            if risks:
                print(f"⚠️  Identified Risks:")
                for risk in risks:
                    print(f"   - {risk}")
                print()
            
            recommendations = ideation_summary.get("recommendations", [])
            if recommendations:
                print(f"💡 Recommendations:")
                for rec in recommendations:
                    print(f"   - {rec}")
                print()
            
            # Show Azure DevOps links if available
            ado_result = state.metadata.get('ideation_result', {})
            if ado_result.get('epic_id') and ado_result.get('feature_id'):
                print(f"🔗 View in Azure DevOps:")
                org = self.config.get("ado_organization", "your-org")
                project = self.config.get("ado_project", "your-project")
                print(f"   Epic: https://dev.azure.com/{org}/{project}/_workitems/edit/{ado_result['epic_id']}")
                print(f"   Feature: https://dev.azure.com/{org}/{project}/_workitems/edit/{ado_result['feature_id']}")
                print()
            
            print("="*80)
            print("🎯 WORKFLOW STATUS: WAITING FOR HUMAN APPROVAL")
            print("="*80)
            print()
            
            # Get human approval
            approval = input("🤔 Do you approve this ideation and want to continue with the workflow? (yes/no): ").strip().lower()
            
            if approval in ['yes', 'y']:
                print("✅ APPROVED! Continuing with workflow...")
                state.status = "approved"
                state.metadata["human_approval"] = {
                    "status": "approved",
                    "timestamp": datetime.now().isoformat(),
                    "llm_model_used": self.llm_model
                }
                logger.info(f"Human approval step completed with status: approved using LLM model: {self.llm_model}")
            else:
                print("❌ REJECTED! Workflow will terminate.")
                state.status = "rejected"
                state.metadata["human_approval"] = {
                    "status": "rejected",
                    "timestamp": datetime.now().isoformat(),
                    "llm_model_used": self.llm_model
                }
                logger.info(f"Human approval step completed with status: rejected using LLM model: {self.llm_model}")
            
        except Exception as e:
            logger.error(f"Error in human approval step: {str(e)}")
            state.errors.append(f"Human approval step failed: {str(e)}")
            state.status = "failed"
        
        return state
    
    def _should_proceed(self, state: WorkflowState) -> str:
        """Determine if workflow should proceed after human approval.
        
        Args:
            state: Current workflow state
            
        Returns:
            Next step decision
        """
        if state.status == "approved":
            return "proceed"
        else:
            return "reject"
    
    # Requirements step removed - Azure DevOps creation now handled in ideation step
    
    async def _design_step(self, state: WorkflowState) -> WorkflowState:
        """Execute the design step.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        try:
            logger.info(f"Starting design step with LLM model: {self.llm_model}")
            
            state.current_step = "design"
            state.status = "in_progress"
            
            # Get required data from previous steps
            bounded_contexts = state.bounded_contexts
            if not bounded_contexts:
                raise ValueError("No bounded contexts available for design")
            
            # Generate DDD model
            ddd_model = await self.design_agent.generate_ddd_model(
                state.feature,
                bounded_contexts
            )
            
            # Validate DDD model
            validation_result = await self.design_agent.validate_ddd_model(ddd_model)
            
            if validation_result["is_valid"]:
                state.status = "completed"
                state.metadata["ddd_model"] = ddd_model
                state.metadata["ddd_validation"] = validation_result
                
                # Save DDD artifacts
                try:
                    saved_files = self.design_agent.save_ddd_artifacts(ddd_model)
                    state.metadata["ddd_artifacts"] = saved_files
                except Exception as e:
                    logger.warning(f"Failed to save DDD artifacts: {str(e)}")
                
                logger.info(f"Design step completed successfully using LLM model: {self.llm_model}")
            else:
                state.status = "failed"
                state.errors.extend(validation_result["errors"])
                logger.error(f"Design step failed: {validation_result['errors']}")
            
        except Exception as e:
            logger.error(f"Error in design step: {str(e)}")
            state.errors.append(f"Design step failed: {str(e)}")
            state.status = "failed"
        
        return state
    
    async def _code_generation_step(self, state: WorkflowState) -> WorkflowState:
        """Execute the code generation step.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        try:
            logger.info(f"Starting code generation step with LLM model: {self.llm_model}")
            
            state.current_step = "code_generation"
            state.status = "in_progress"
            
            # Get required data from previous steps
            user_stories = state.stories
            bounded_contexts = state.bounded_contexts
            
            if not user_stories:
                raise ValueError("No user stories available for code generation")
            if not bounded_contexts:
                raise ValueError("No bounded contexts available for code generation")
            
            # Generate microservice
            generated_code = await self.codegen_agent.generate_microservice(
                state.feature,
                user_stories,
                bounded_contexts
            )
            
            # Validate generated code
            validation_result = await self.codegen_agent.validate_generated_code(generated_code)
            
            if validation_result["is_valid"]:
                state.status = "completed"
                state.metadata["generated_code"] = generated_code
                state.metadata["code_validation"] = validation_result
                
                # Save generated code
                try:
                    saved_files = self.codegen_agent.save_generated_code(generated_code)
                    state.metadata["code_artifacts"] = saved_files
                except Exception as e:
                    logger.warning(f"Failed to save generated code: {str(e)}")
                
                logger.info(f"Code generation step completed successfully using LLM model: {self.llm_model}")
            else:
                state.status = "failed"
                state.errors.extend(validation_result["errors"])
                logger.error(f"Code generation step failed: {validation_result['errors']}")
            
        except Exception as e:
            logger.error(f"Error in code generation step: {str(e)}")
            state.errors.append(f"Code generation step failed: {str(e)}")
            state.status = "failed"
        
        return state
    
    async def _deployment_step(self, state: WorkflowState) -> WorkflowState:
        """Execute the deployment step.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        try:
            logger.info(f"Starting deployment step with LLM model: {self.llm_model}")
            
            state.current_step = "deployment"
            state.status = "in_progress"
            
            # Check if deployment agent is available
            if not self.deployment_agent:
                logger.warning("Deployment agent not available, skipping deployment step")
                state.status = "completed"
                state.metadata["deployment_config"] = {"status": "skipped", "reason": "No Kubernetes configuration"}
                state.metadata["deployment_validation"] = {"is_valid": True, "warnings": ["Deployment step skipped due to missing K8s config"]}
                state.metadata["deployment_artifacts"] = []
                logger.info("Deployment step skipped successfully")
                return state
            
            # Get required data from previous steps
            generated_code = state.metadata.get("generated_code", {})
            if not generated_code:
                raise ValueError("No generated code available for deployment")
            
            spring_boot_service = generated_code.get("spring_boot_service")
            openapi_spec = generated_code.get("openapi_spec")
            
            if not spring_boot_service or not openapi_spec:
                raise ValueError("Missing Spring Boot service or OpenAPI spec")
            
            # Generate deployment configuration
            deployment_config = await self.deployment_agent.generate_deployment_config(
                state.feature,
                spring_boot_service,
                openapi_spec
            )
            
            # Validate deployment configuration
            validation_result = await self.deployment_agent.validate_deployment_config(deployment_config)
            
            if validation_result["is_valid"]:
                state.status = "completed"
                state.metadata["deployment_config"] = deployment_config
                state.metadata["deployment_validation"] = validation_result
                
                # Save deployment artifacts
                try:
                    saved_files = self.deployment_agent.save_deployment_artifacts(deployment_config)
                    state.metadata["deployment_artifacts"] = []
                except Exception as e:
                    logger.warning(f"Failed to save deployment artifacts: {str(e)}")
                
                logger.info(f"Deployment step completed successfully using LLM model: {self.llm_model}")
            else:
                state.status = "failed"
                state.errors.extend(validation_result["errors"])
                logger.error(f"Deployment step failed: {validation_result['errors']}")
            
        except Exception as e:
            logger.error(f"Error in deployment step: {str(e)}")
            state.errors.append(f"Deployment step failed: {str(e)}")
            state.status = "failed"
        
        return state
    
    async def _validation_step(self, state: WorkflowState) -> WorkflowState:
        """Execute the validation step.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        try:
            logger.info(f"Starting validation step with LLM model: {self.llm_model}")
            
            state.current_step = "validation"
            state.status = "in_progress"
            
            # Check for required artifacts from previous steps
            required_artifacts = []
            
            if not state.metadata.get("ddd_model"):
                required_artifacts.append("ddd_model")
            
            if not state.metadata.get("generated_code"):
                required_artifacts.append("generated_code")
            
            if not state.metadata.get("deployment_config"):
                required_artifacts.append("deployment_config")
            
            if required_artifacts:
                state.status = "failed"
                error_msg = f"Missing required artifact: {', '.join(required_artifacts)}"
                state.errors.append(error_msg)
                logger.error(f"Validation failed: {error_msg}")
                return state
            
            # All required artifacts are present
            state.status = "completed"
            state.metadata["validation_result"] = {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "llm_model_used": self.llm_model,
                "artifacts_validated": ["ddd_model", "generated_code", "deployment_config"]
            }
            
            logger.info(f"Validation step completed successfully using LLM model: {self.llm_model}")
            
        except Exception as e:
            logger.error(f"Error in validation step: {str(e)}")
            state.errors.append(f"Validation step failed: {str(e)}")
            state.status = "failed"
        
        return state
    
    async def execute_workflow(self, feature_request: Union[Dict[str, Any], WorkflowState]) -> WorkflowState:
        """Execute the complete workflow.
        
        Args:
            feature_request: Feature request dictionary or WorkflowState object
            
        Returns:
            Final workflow state
        """
        try:
            # Handle both Dict and WorkflowState inputs
            if isinstance(feature_request, WorkflowState):
                feature_name = feature_request.metadata.get('feature_name', 'Unknown')
                feature_data = feature_request.metadata
                logger.info(f"Received WorkflowState with metadata: {feature_request.metadata}")
            else:
                # Handle dict input - check if it has nested metadata structure
                if isinstance(feature_request, dict) and 'metadata' in feature_request:
                    # This is a workflow state dict with nested metadata
                    feature_name = feature_request['metadata'].get('feature_name', 'Unknown')
                    feature_data = feature_request['metadata']
                    logger.info(f"Received workflow state dict with nested metadata: {feature_request['metadata']}")
                else:
                    # This is a direct feature request dict
                    feature_name = feature_request.get('feature_name', 'Unknown')
                    feature_data = feature_request
                    logger.info(f"Received direct feature request dict with keys: {list(feature_request.keys()) if feature_request else 'None'}")
            
            logger.info(f"Starting workflow execution for feature: {feature_name}")
            logger.info(f"Feature data: {feature_data}")
            logger.info(f"Using LLM model: {self.llm_model} for all workflow steps")
            
            # Initialize workflow state with proper metadata
            initial_state = WorkflowState(
                workflow_id=self.workflow_id,
                current_step="start",
                status="initialized",
                metadata=feature_data.copy() if feature_data else {},
                errors=[],
                stories=[],
                bounded_contexts=[]
            )
            
            # Store initial state in memory
            self.workflow_states[self.workflow_id] = initial_state
            
            # Execute workflow with proper error handling
            try:
                # Configure the workflow execution
                config = {
                    "configurable": {
                        "thread_id": self.workflow_id,
                        "checkpoint_ns": "workflow"
                    }
                }
                
                result = await self.workflow.ainvoke(initial_state, config=config)
                
                # Handle LangGraph result format
                if isinstance(result, dict) and "output" in result:
                    final_state = result["output"]
                elif isinstance(result, WorkflowState):
                    final_state = result
                else:
                    # Convert dict result to WorkflowState if needed
                    if isinstance(result, dict):
                        # Merge with initial state to preserve metadata
                        result.update({
                            "workflow_id": self.workflow_id,
                            "metadata": {**initial_state.metadata, **result.get("metadata", {})}
                        })
                        final_state = WorkflowState(**result)
                    else:
                        final_state = initial_state
                
                # Ensure final state has all required fields
                if not hasattr(final_state, 'metadata') or final_state.metadata is None:
                    final_state.metadata = initial_state.metadata.copy()
                
                # Update final state
                final_state.updated_at = datetime.now()
                if final_state.status == "completed":
                    final_state.metadata["completion_timestamp"] = datetime.now().isoformat()
                
                # Store final state
                self.workflow_states[self.workflow_id] = final_state
                
                logger.info(f"Workflow execution completed using LLM model: {self.llm_model}. Final status: {final_state.status}")
                return final_state
                
            except Exception as workflow_error:
                logger.error(f"Workflow execution error: {str(workflow_error)}")
                # Create error state
                error_state = WorkflowState(
                    workflow_id=self.workflow_id,
                    current_step=initial_state.current_step,
                    status="failed",
                    metadata=initial_state.metadata,
                    errors=[f"Workflow execution failed: {str(workflow_error)}"],
                    created_at=initial_state.created_at,
                    updated_at=datetime.now()
                )
                self.workflow_states[self.workflow_id] = error_state
                return error_state
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}")
            # Create critical error state
            critical_error_state = WorkflowState(
                workflow_id=self.workflow_id,
                current_step="error",
                status="critical_error",
                metadata=feature_request if feature_request else {},
                errors=[f"Critical workflow error: {str(e)}"],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            self.workflow_states[self.workflow_id] = critical_error_state
            return critical_error_state
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[WorkflowState]:
        """Get the status of a workflow.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Workflow state if found, None otherwise
        """
        try:
            # Retrieve the workflow state from memory
            return self.workflow_states.get(workflow_id)
        except Exception as e:
            logger.error(f"Failed to get workflow status: {str(e)}")
            return None
    
    async def pause_workflow(self, workflow_id: str) -> bool:
        """Pause a workflow execution.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current state
            current_state = await self.get_workflow_status(workflow_id)
            if not current_state:
                logger.warning(f"Workflow {workflow_id} not found")
                return False
            
            # Update state to paused
            current_state.status = "paused"
            current_state.metadata["paused_at"] = datetime.now().isoformat()
            current_state.updated_at = datetime.now()
            
            # Store updated state
            self.workflow_states[workflow_id] = current_state
            
            logger.info(f"Workflow {workflow_id} paused successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to pause workflow: {str(e)}")
            return False
    
    async def resume_workflow(self, workflow_id: str) -> bool:
        """Resume a paused workflow.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current state
            current_state = await self.get_workflow_status(workflow_id)
            if not current_state:
                logger.warning(f"Workflow {workflow_id} not found")
                return False
            
            # Update state to resumed
            current_state.status = "in_progress"
            current_state.metadata["resumed_at"] = datetime.now().isoformat()
            current_state.updated_at = datetime.now()
            
            # Store updated state
            self.workflow_states[workflow_id] = current_state
            
            logger.info(f"Workflow {workflow_id} resumed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to resume workflow: {str(e)}")
            return False
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a workflow execution.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current state
            current_state = await self.get_workflow_status(workflow_id)
            if not current_state:
                logger.warning(f"Workflow {workflow_id} not found")
                return False
            
            # Update state to cancelled
            current_state.status = "cancelled"
            current_state.metadata["cancelled_at"] = datetime.now().isoformat()
            current_state.updated_at = datetime.now()
            
            # Store updated state
            self.workflow_states[workflow_id] = current_state
            
            logger.info(f"Workflow {workflow_id} cancelled successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel workflow: {str(e)}")
            return False


# Example usage and configuration
async def main():
    """Example usage of the ProductLifecycleWorkflow."""
    
    # Configuration
    config = {
        "llm_model": "gpt-4",
        "llm_temperature": 0.7,
        "ado_organization": "your-org",
        "ado_project": "your-project",
        "ado_pat": "your-personal-access-token",
        "kubeconfig_path": "/path/to/kubeconfig",
        "in_cluster": False
    }
    
    # Feature request
    feature_request = {
        "feature_name": "User Authentication System",
        "feature_description": "Implement secure user authentication with OAuth2, JWT tokens, and role-based access control",
        "priority": "High",
        "business_context": "Need to secure our application and provide single sign-on capabilities",
        "target_users": ["End users", "Administrators", "API consumers"],
        "success_metrics": ["Reduced security incidents", "Improved user experience", "Compliance with security standards"],
        "constraints": ["Must integrate with existing identity providers", "Should support multi-factor authentication"]
    }
    
    try:
        # Initialize workflow
        workflow = ProductLifecycleWorkflow(config)
        
        # Execute workflow
        final_state = await workflow.execute_workflow(feature_request)
        
        # Print results
        print(f"Workflow completed with status: {final_state.status}")
        if final_state.errors:
            print(f"Errors: {final_state.errors}")
        if final_state.metadata:
            print(f"Metadata: {final_state.metadata}")
            
    except Exception as e:
        print(f"Workflow execution failed: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
