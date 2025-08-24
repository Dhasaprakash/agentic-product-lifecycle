#!/usr/bin/env python3
"""
Simplified Agentic AI Architect System
Main application entry point without MCP dependencies
"""

import asyncio
import logging
import os
from typing import Dict, Any
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# In-memory storage for demo purposes
workflows = {}
workflow_counter = 0

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    logger.info("Starting Agentic AI Architect system...")
    
    # Check for required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("OPENAI_API_KEY environment variable not set!")
        logger.warning("Some features may not work without proper configuration")
    
    logger.info("Agentic AI Architect system started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Agentic AI Architect system...")
    logger.info("Agentic AI Architect system shut down successfully")

# Initialize FastAPI app
app = FastAPI(
    title="Agentic AI Architect System",
    description="Simplified version without MCP dependencies",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Agentic AI Architect System",
        "version": "1.0.0",
        "status": "running",
        "description": "Simplified version without MCP dependencies"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": asyncio.get_event_loop().time(),
        "version": "1.0.0"
    }

@app.post("/workflow/start")
async def start_workflow(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """Start a new product lifecycle workflow"""
    global workflow_counter
    
    try:
        # Validate request
        if not request.get("feature_name"):
            raise HTTPException(status_code=400, detail="feature_name is required")
        
        # Create workflow
        workflow_id = f"workflow_{workflow_counter}"
        workflow_counter += 1
        
        workflow = {
            "id": workflow_id,
            "status": "started",
            "feature_name": request["feature_name"],
            "feature_description": request.get("feature_description", ""),
            "priority": request.get("priority", "Medium"),
            "created_at": asyncio.get_event_loop().time(),
            "current_step": "ideation",
            "artifacts": {}
        }
        
        workflows[workflow_id] = workflow
        
        # Simulate workflow execution in background
        background_tasks.add_task(simulate_workflow, workflow_id)
        
        logger.info(f"Started workflow {workflow_id} for feature: {request['feature_name']}")
        
        return {
            "workflow_id": workflow_id,
            "status": "started",
            "message": f"Workflow started for feature: {request['feature_name']}"
        }
        
    except Exception as e:
        logger.error(f"Error starting workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def simulate_workflow(workflow_id: str):
    """Simulate workflow execution for demo purposes"""
    try:
        workflow = workflows[workflow_id]
        
        # Simulate ideation step
        await asyncio.sleep(2)
        workflow["current_step"] = "ideation"
        workflow["artifacts"]["ideation"] = {
            "epics": [{"name": "Epic 1", "description": "Generated epic"}],
            "user_stories": [{"title": "Story 1", "description": "Generated story"}],
            "bounded_contexts": [{"name": "Context 1", "description": "Generated context"}]
        }
        
        # Simulate human approval
        await asyncio.sleep(1)
        workflow["current_step"] = "approval"
        workflow["status"] = "waiting_approval"
        
        # Simulate approval and continue
        await asyncio.sleep(2)
        workflow["current_step"] = "requirements"
        workflow["status"] = "in_progress"
        
        # Simulate requirements step
        await asyncio.sleep(2)
        workflow["current_step"] = "design"
        workflow["artifacts"]["requirements"] = {
            "ado_stories": [{"id": "123", "title": "ADO Story"}],
            "epic_links": [{"epic_id": "456", "story_id": "123"}]
        }
        
        # Simulate design step
        await asyncio.sleep(2)
        workflow["current_step"] = "code_generation"
        workflow["artifacts"]["design"] = {
            "ddd_model": "Generated DDD model",
            "context_mapper_dsl": "Generated CML",
            "architecture_diagrams": ["Class diagram", "Sequence diagram"]
        }
        
        # Simulate code generation step
        await asyncio.sleep(3)
        workflow["current_step"] = "deployment"
        workflow["artifacts"]["code"] = {
            "openapi_spec": "Generated OpenAPI spec",
            "spring_boot_service": "Generated Spring Boot service",
            "tests": "Generated unit and integration tests"
        }
        
        # Simulate deployment step
        await asyncio.sleep(2)
        workflow["current_step"] = "completed"
        workflow["status"] = "completed"
        workflow["artifacts"]["deployment"] = {
            "kubernetes_manifests": "Generated K8s manifests",
            "helm_charts": "Generated Helm charts",
            "ci_cd_pipelines": "Generated CI/CD configurations"
        }
        
        logger.info(f"Workflow {workflow_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Error in workflow {workflow_id}: {str(e)}")
        workflow["status"] = "failed"
        workflow["error"] = str(e)

@app.get("/workflow/{workflow_id}/status")
async def get_workflow_status(workflow_id: str):
    """Get the status of a specific workflow"""
    if workflow_id not in workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return workflows[workflow_id]

@app.get("/workflows")
async def list_workflows():
    """List all workflows"""
    return {
        "workflows": list(workflows.values()),
        "total": len(workflows)
    }

@app.post("/workflow/{workflow_id}/approve")
async def approve_workflow(workflow_id: str):
    """Approve a workflow to continue"""
    if workflow_id not in workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = workflows[workflow_id]
    if workflow["status"] != "waiting_approval":
        raise HTTPException(status_code=400, detail="Workflow is not waiting for approval")
    
    workflow["status"] = "approved"
    workflow["approved_at"] = asyncio.get_event_loop().time()
    
    # Continue workflow execution
    asyncio.create_task(simulate_workflow(workflow_id))
    
    return {"message": "Workflow approved", "workflow_id": workflow_id}

@app.post("/workflow/{workflow_id}/reject")
async def reject_workflow(workflow_id: str, reason: str = "No reason provided"):
    """Reject a workflow"""
    if workflow_id not in workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = workflows[workflow_id]
    workflow["status"] = "rejected"
    workflow["rejected_at"] = asyncio.get_event_loop().time()
    workflow["rejection_reason"] = reason
    
    return {"message": "Workflow rejected", "workflow_id": workflow_id}

@app.get("/workflow/{workflow_id}/artifacts")
async def get_workflow_artifacts(workflow_id: str):
    """Get artifacts generated by a workflow"""
    if workflow_id not in workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = workflows[workflow_id]
    return {
        "workflow_id": workflow_id,
        "artifacts": workflow.get("artifacts", {}),
        "status": workflow["status"]
    }

if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "main_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
