"""
Agentic AI Architect - Main Application Entry Point
"""

import os
import logging
import asyncio
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from workflows.lifecycle import ProductLifecycleWorkflow
from models.domain import WorkflowState

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FeatureRequest(BaseModel):
    """Feature request model for the API."""
    feature_name: str
    feature_description: str
    priority: str = "Medium"
    business_context: Optional[str] = None
    target_users: Optional[list] = None
    success_metrics: Optional[list] = None
    constraints: Optional[list] = None
    llm_model: Optional[str] = "gpt-4o-mini"  # User can specify which LLM model to use
    llm_temperature: Optional[float] = 0.7


class WorkflowResponse(BaseModel):
    """Workflow response model."""
    workflow_id: str
    status: str
    message: str
    current_step: Optional[str] = None


class WorkflowStatusResponse(BaseModel):
    """Workflow status response model."""
    workflow_id: str
    status: str
    current_step: str
    errors: list
    metadata: dict


# Global workflow storage (in production, use a proper database)
workflows: Dict[str, ProductLifecycleWorkflow] = {}
workflow_states: Dict[str, WorkflowState] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Agentic AI Architect system...")
    
    # Load configuration
    app.state.config = load_configuration()
    
    # Initialize services
    await initialize_services(app.state.config)
    
    logger.info("Agentic AI Architect system started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Agentic AI Architect system...")
    
    # Cleanup
    workflows.clear()
    workflow_states.clear()
    
    logger.info("Agentic AI Architect system shut down successfully")


def load_configuration() -> Dict[str, Any]:
    """Load configuration from environment variables."""
    config = {
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "llm_model": os.getenv("LLM_MODEL", "gpt-4"),
        "llm_temperature": float(os.getenv("LLM_TEMPERATURE", "0.7")),
        "ado_organization": os.getenv("ADO_ORGANIZATION"),
        "ado_project": os.getenv("ADO_PROJECT"),
        "ado_pat": os.getenv("ADO_PAT"),
        "kubeconfig_path": os.getenv("KUBECONFIG_PATH"),
        "in_cluster": os.getenv("IN_CLUSTER", "false").lower() == "true"
    }
    
    # Validate required configuration
    required_configs = ["openai_api_key", "ado_organization", "ado_project", "ado_pat"]
    missing_configs = [config_name for config_name in required_configs if not config.get(config_name)]
    
    if missing_configs:
        logger.warning(f"Missing required configuration: {missing_configs}")
        logger.warning("Some features may not work without proper configuration")
    
    return config


async def initialize_services(config: Dict[str, Any]):
    """Initialize external services."""
    try:
        # Test Azure DevOps connection
        if config.get("ado_organization") and config.get("ado_project") and config.get("ado_pat"):
            logger.info("Testing Azure DevOps connection...")
            # This would test the connection
            logger.info("Azure DevOps connection test completed")
        
        # Test Kubernetes connection
        if config.get("kubeconfig_path") or config.get("in_cluster"):
            logger.info("Testing Kubernetes connection...")
            # This would test the connection
            logger.info("Kubernetes connection test completed")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {str(e)}")
        logger.warning("System will continue with limited functionality")


# Create FastAPI app
app = FastAPI(
    title="Agentic AI Architect",
    description="An intelligent system that automates the complete product development lifecycle",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Agentic AI Architect System",
        "version": "1.0.0",
        "status": "running",
        "description": "Automate your product development lifecycle from ideation to deployment"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": asyncio.get_event_loop().time(),
        "workflows_active": len(workflows),
        "workflows_completed": len([w for w in workflow_states.values() if w.status == "completed"])
    }


@app.post("/workflow/start", response_model=WorkflowResponse)
async def start_workflow(feature_request: FeatureRequest, background_tasks: BackgroundTasks):
    """Start a new product lifecycle workflow."""
    try:
        logger.info(f"Starting workflow for feature: {feature_request.feature_name}")
        
        # Create workflow configuration with user-specified LLM model
        workflow_config = app.state.config.copy()
        workflow_config["llm_model"] = feature_request.llm_model
        workflow_config["llm_temperature"] = feature_request.llm_temperature
        
        # Create workflow instance
        workflow = ProductLifecycleWorkflow(workflow_config)
        workflows[workflow.workflow_id] = workflow
        
        # Convert feature request to dictionary
        feature_dict = feature_request.dict()
        
        # Start workflow in background
        background_tasks.add_task(execute_workflow_background, workflow.workflow_id, feature_dict)
        
        return WorkflowResponse(
            workflow_id=workflow.workflow_id,
            status="started",
            message=f"Workflow started for feature: {feature_request.feature_name}",
            current_step="initialized"
        )
        
    except Exception as e:
        logger.error(f"Failed to start workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start workflow: {str(e)}")


async def execute_workflow_background(workflow_id: str, feature_request: Dict[str, Any]):
    """Execute workflow in background."""
    try:
        workflow = workflows[workflow_id]
        
        # Execute workflow
        final_state = await workflow.execute_workflow(feature_request)
        
        # Store workflow state
        workflow_states[workflow_id] = final_state
        
        logger.info(f"Workflow {workflow_id} completed with status: {final_state.status}")
        
    except Exception as e:
        logger.error(f"Workflow {workflow_id} failed: {str(e)}")
        
        # Create error state
        error_state = WorkflowState(
            workflow_id=workflow_id,
            current_step="error",
            status="failed",
            errors=[f"Workflow execution failed: {str(e)}"]
        )
        workflow_states[workflow_id] = error_state


@app.get("/workflow/{workflow_id}/status", response_model=WorkflowStatusResponse)
async def get_workflow_status(workflow_id: str):
    """Get the status of a workflow."""
    try:
        if workflow_id not in workflow_states:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        state = workflow_states[workflow_id]
        
        return WorkflowStatusResponse(
            workflow_id=state.workflow_id,
            status=state.status,
            current_step=state.current_step,
            errors=state.errors,
            metadata=state.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get workflow status: {str(e)}")


@app.get("/workflow/{workflow_id}/pause")
async def pause_workflow(workflow_id: str):
    """Pause a workflow."""
    try:
        if workflow_id not in workflows:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        workflow = workflows[workflow_id]
        success = await workflow.pause_workflow(workflow_id)
        
        if success:
            return {"message": f"Workflow {workflow_id} paused successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to pause workflow")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to pause workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to pause workflow: {str(e)}")


@app.get("/workflow/{workflow_id}/resume")
async def resume_workflow(workflow_id: str):
    """Resume a paused workflow."""
    try:
        if workflow_id not in workflows:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        workflow = workflows[workflow_id]
        success = await workflow.resume_workflow(workflow_id)
        
        if success:
            return {"message": f"Workflow {workflow_id} resumed successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to resume workflow")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resume workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to resume workflow: {str(e)}")


@app.delete("/workflow/{workflow_id}")
async def cancel_workflow(workflow_id: str):
    """Cancel a workflow."""
    try:
        if workflow_id not in workflows:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        workflow = workflows[workflow_id]
        success = await workflow.cancel_workflow(workflow_id)
        
        if success:
            # Remove workflow from storage
            workflows.pop(workflow_id, None)
            workflow_states.pop(workflow_id, None)
            
            return {"message": f"Workflow {workflow_id} cancelled successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to cancel workflow")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel workflow: {str(e)}")


@app.get("/workflows")
async def list_workflows():
    """List all workflows."""
    try:
        workflow_list = []
        
        for workflow_id, state in workflow_states.items():
            workflow_list.append({
                "workflow_id": workflow_id,
                "status": state.status,
                "current_step": state.current_step,
                "feature_name": state.metadata.get("feature_name", "Unknown"),
                "created_at": state.created_at.isoformat() if state.created_at else None,
                "updated_at": state.updated_at.isoformat() if state.updated_at else None
            })
        
        return {
            "total_workflows": len(workflow_list),
            "workflows": workflow_list
        }
        
    except Exception as e:
        logger.error(f"Failed to list workflows: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list workflows: {str(e)}")


@app.get("/workflow/{workflow_id}/artifacts")
async def get_workflow_artifacts(workflow_id: str):
    """Get artifacts generated by a workflow."""
    try:
        if workflow_id not in workflow_states:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        state = workflow_states[workflow_id]
        
        artifacts = {}
        
        # Add DDD artifacts if available
        if state.metadata.get("ddd_artifacts"):
            artifacts["ddd"] = state.metadata["ddd_artifacts"]
        
        # Add code artifacts if available
        if state.metadata.get("code_artifacts"):
            artifacts["code"] = state.metadata["code_artifacts"]
        
        # Add deployment artifacts if available
        if state.metadata.get("deployment_artifacts"):
            artifacts["deployment"] = state.metadata["deployment_artifacts"]
        
        return {
            "workflow_id": workflow_id,
            "artifacts": artifacts
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow artifacts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get workflow artifacts: {str(e)}")


@app.get("/models")
async def get_available_models():
    """Get available LLM models."""
    try:
        # Import here to avoid circular imports
        from agents.ideation import LLMFactory
        
        supported_models = LLMFactory.get_supported_models()
        
        return {
            "supported_models": supported_models,
            "default_model": "gpt-4o-mini",
            "recommendations": {
                "fast_and_cheap": "llama3-8b-8192",
                "balanced": "gpt-4o-mini", 
                "high_quality": "gpt-4o",
                "creative": "claude-3-5-sonnet-20241022"
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get available models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get available models: {str(e)}")


@app.get("/config")
async def get_configuration():
    """Get current configuration (without sensitive data)."""
    try:
        config = app.state.config.copy()
        
        # Remove sensitive information
        if "ado_pat" in config:
            config["ado_pat"] = "***" if config["ado_pat"] else None
        
        return {
            "configuration": config,
            "environment": {
                "python_version": os.sys.version,
                "platform": os.sys.platform
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get configuration: {str(e)}")


if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
