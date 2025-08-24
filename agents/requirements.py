"""
Requirements Agent - Manages Azure DevOps integration and story lifecycle.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from models.domain import (
    UserStory, Epic, Feature, StoryStatus, Priority, StoryType,
    AcceptanceCriterion, DefinitionOfDone
)
from services.ado_client import AzureDevOpsClient

logger = logging.getLogger(__name__)


class RequirementsAgent:
    """Agent responsible for managing requirements in Azure DevOps."""
    
    def __init__(self, ado_client: AzureDevOpsClient):
        """Initialize the Requirements Agent.
        
        Args:
            ado_client: Azure DevOps client instance
        """
        self.ado_client = ado_client
    
    async def create_requirements_in_ado(self, feature: Feature, epic: Epic, user_stories: List[UserStory]) -> Dict[str, Any]:
        """Create all requirements in Azure DevOps.
        
        Args:
            feature: Feature object
            epic: Epic object
            user_stories: List of user stories
            
        Returns:
            Dictionary with created work item IDs and status
        """
        try:
            logger.info(f"Creating requirements in Azure DevOps for feature: {feature.name}")
            
            result = {
                "feature_id": None,
                "epic_id": None,
                "story_ids": [],
                "success": True,
                "errors": []
            }
            
            # Create epic first
            epic_id = self.ado_client.create_epic(epic)
            if not epic_id:
                error_msg = f"Failed to create epic: {epic.title}"
                logger.error(error_msg)
                result["errors"].append(error_msg)
                result["success"] = False
                return result
            
            result["epic_id"] = epic_id
            logger.info(f"Created epic with ID: {epic_id}")
            
            # Try to create feature, but continue if it fails (some projects don't have Feature work item type)
            feature_id = self.ado_client.create_feature(feature, epic_id)
            if feature_id:
                result["feature_id"] = feature_id
                logger.info(f"Created feature with ID: {feature_id}")
            else:
                logger.warning(f"Could not create feature (work item type may not exist): {feature.name}")
                result["feature_id"] = None
            
            # Create user stories - link to feature if it exists, otherwise to epic
            parent_id = feature_id if feature_id else epic_id
            for story in user_stories:
                story_id = self.ado_client.create_user_story(story, parent_id)
                if story_id:
                    result["story_ids"].append({
                        "story_id": story_id,
                        "title": story.title,
                        "status": "Created"
                    })
                    logger.info(f"Created user story: {story.title} with ID: {story_id}")
                else:
                    error_msg = f"Failed to create user story: {story.title}"
                    logger.error(error_msg)
                    result["errors"].append(error_msg)
                    result["success"] = False
            
            # No need for separate linking since parent relationships are set during creation
            logger.info("Work item hierarchy created successfully with proper parent-child relationships")
            
            return result
            
        except Exception as e:
            error_msg = f"Unexpected error creating requirements: {str(e)}"
            logger.error(error_msg)
            return {
                "feature_id": None,
                "epic_id": None,
                "story_ids": [],
                "success": False,
                "errors": [error_msg]
            }
    
    def _create_work_item_links(self, result: Dict[str, Any]):
        """Create links between work items in Azure DevOps.
        
        Args:
            result: Result dictionary with work item IDs
        """
        try:
            # Link feature to epic
            if result["epic_id"] and result["feature_id"]:
                self.ado_client.create_work_item_link(
                    source_id=result["epic_id"],
                    target_id=result["feature_id"],
                    link_type="Child"
                )
            
            # Link stories to feature
            for story_info in result["story_ids"]:
                if result["feature_id"]:
                    self.ado_client.create_work_item_link(
                        source_id=result["feature_id"],
                        target_id=story_info["story_id"],
                        link_type="Child"
                    )
            
            logger.info("Created work item links successfully")
            
        except Exception as e:
            logger.error(f"Failed to create work item links: {str(e)}")
    
    async def update_story_status(self, story_id: str, new_status: StoryStatus) -> bool:
        """Update the status of a user story.
        
        Args:
            story_id: ID of the story to update
            new_status: New status to set
            
        Returns:
            True if successful, False otherwise
        """
        try:
            success = self.ado_client.update_story_status(story_id, new_status)
            if success:
                logger.info(f"Updated story {story_id} status to {new_status}")
            else:
                logger.error(f"Failed to update story {story_id} status")
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating story {story_id} status: {str(e)}")
            return False
    
    async def get_story_status(self, story_id: str) -> Optional[Dict[str, Any]]:
        """Get the current status of a user story.
        
        Args:
            story_id: ID of the story
            
        Returns:
            Story status information or None if not found
        """
        try:
            return self.ado_client.get_work_item(story_id)
        except Exception as e:
            logger.error(f"Error getting story {story_id} status: {str(e)}")
            return None
    
    async def search_stories_by_epic(self, epic_id: str) -> List[Dict[str, Any]]:
        """Search for stories belonging to a specific epic.
        
        Args:
            epic_id: ID of the epic
            
        Returns:
            List of stories in the epic
        """
        try:
            # WIQL query to find stories under the epic
            query = f"""
            SELECT [System.Id], [System.Title], [System.State], [System.AssignedTo]
            FROM WorkItems
            WHERE [System.Parent] = {epic_id}
            AND [System.WorkItemType] = 'User Story'
            ORDER BY [System.CreatedDate] DESC
            """
            
            return self.ado_client.search_work_items(query)
            
        except Exception as e:
            logger.error(f"Error searching stories for epic {epic_id}: {str(e)}")
            return []
    
    async def get_epic_progress(self, epic_id: str) -> Dict[str, Any]:
        """Get progress information for an epic.
        
        Args:
            epic_id: ID of the epic
            
        Returns:
            Epic progress information
        """
        try:
            # Get epic details
            epic_info = self.ado_client.get_work_item(epic_id)
            if not epic_info:
                return {"error": "Epic not found"}
            
            # Get all stories in the epic
            stories = await self.search_stories_by_epic(epic_id)
            
            # Calculate progress
            total_stories = len(stories)
            completed_stories = sum(1 for s in stories if s.get('status') == 'Closed')
            in_progress_stories = sum(1 for s in stories if s.get('status') in ['Active', 'Resolved'])
            
            progress_percentage = (completed_stories / total_stories * 100) if total_stories > 0 else 0
            
            return {
                "epic_id": epic_id,
                "epic_title": epic_info.get('title', ''),
                "total_stories": total_stories,
                "completed_stories": completed_stories,
                "in_progress_stories": in_progress_stories,
                "not_started_stories": total_stories - completed_stories - in_progress_stories,
                "progress_percentage": round(progress_percentage, 2),
                "stories": stories
            }
            
        except Exception as e:
            logger.error(f"Error getting epic progress for {epic_id}: {str(e)}")
            return {"error": str(e)}
    
    async def validate_story_ready_for_development(self, story_id: str) -> Dict[str, Any]:
        """Validate if a story is ready for development.
        
        Args:
            story_id: ID of the story to validate
            
        Returns:
            Validation result with readiness status and issues
        """
        try:
            story_info = self.ado_client.get_work_item(story_id)
            if not story_info:
                return {
                    "ready": False,
                    "issues": ["Story not found"],
                    "missing_items": []
                }
            
            issues = []
            missing_items = []
            
            # Check if story has acceptance criteria
            # This would require additional API calls to get child work items
            # For now, we'll check basic requirements
            
            # Check if story is in correct state
            if story_info.get('status') not in ['New', 'Approved']:
                issues.append(f"Story is in '{story_info.get('status')}' state, should be 'New' or 'Approved'")
            
            # Check if story has title and description
            if not story_info.get('title'):
                missing_items.append("Story title")
            
            if not story_info.get('description'):
                missing_items.append("Story description")
            
            # Check if story is assigned
            if not story_info.get('assigned_to'):
                missing_items.append("Story assignment")
            
            # Check if story has tags
            if not story_info.get('tags'):
                missing_items.append("Story tags")
            
            ready = len(issues) == 0 and len(missing_items) == 0
            
            return {
                "ready": ready,
                "issues": issues,
                "missing_items": missing_items,
                "story_info": story_info
            }
            
        except Exception as e:
            logger.error(f"Error validating story {story_id}: {str(e)}")
            return {
                "ready": False,
                "issues": [f"Validation error: {str(e)}"],
                "missing_items": []
            }
    
    async def create_story_template(self, template_name: str, template_data: Dict[str, Any]) -> bool:
        """Create a story template for reuse.
        
        Args:
            template_name: Name of the template
            template_data: Template data structure
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # This would create a template work item in Azure DevOps
            # For now, we'll log the template creation
            logger.info(f"Created story template: {template_name}")
            logger.debug(f"Template data: {template_data}")
            
            # In a real implementation, you would:
            # 1. Create a template work item type
            # 2. Store template data in ADO
            # 3. Allow reuse of templates for similar stories
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating story template {template_name}: {str(e)}")
            return False
    
    async def get_story_metrics(self, epic_id: str = None, time_range: str = "30d") -> Dict[str, Any]:
        """Get metrics for stories.
        
        Args:
            epic_id: Optional epic ID to filter by
            time_range: Time range for metrics (e.g., "7d", "30d", "90d")
            
        Returns:
            Story metrics
        """
        try:
            # Build WIQL query based on parameters
            if epic_id:
                query = f"""
                SELECT [System.Id], [System.Title], [System.State], [System.CreatedDate], [System.ChangedDate]
                FROM WorkItems
                WHERE [System.Parent] = {epic_id}
                AND [System.WorkItemType] = 'User Story'
                AND [System.CreatedDate] >= @startOfDay('-{time_range}')
                """
            else:
                query = f"""
                SELECT [System.Id], [System.Title], [System.State], [System.CreatedDate], [System.ChangedDate]
                FROM WorkItems
                WHERE [System.WorkItemType] = 'User Story'
                AND [System.CreatedDate] >= @startOfDay('-{time_range}')
                """
            
            stories = self.ado_client.search_work_items(query)
            
            # Calculate metrics
            total_stories = len(stories)
            completed_stories = sum(1 for s in stories if s.get('status') == 'Closed')
            in_progress_stories = sum(1 for s in stories if s.get('status') in ['Active', 'Resolved'])
            
            # Calculate cycle time (simplified)
            cycle_times = []
            for story in stories:
                if story.get('status') == 'Closed' and story.get('created_date') and story.get('changed_date'):
                    # This would require parsing dates and calculating actual cycle time
                    cycle_times.append(1)  # Placeholder
            
            avg_cycle_time = sum(cycle_times) / len(cycle_times) if cycle_times else 0
            
            return {
                "total_stories": total_stories,
                "completed_stories": completed_stories,
                "in_progress_stories": in_progress_stories,
                "not_started_stories": total_stories - completed_stories - in_progress_stories,
                "completion_rate": (completed_stories / total_stories * 100) if total_stories > 0 else 0,
                "average_cycle_time": round(avg_cycle_time, 2),
                "time_range": time_range,
                "epic_filter": epic_id
            }
            
        except Exception as e:
            logger.error(f"Error getting story metrics: {str(e)}")
            return {"error": str(e)}
    
    async def create_story_dependencies(self, story_id: str, dependency_ids: List[str]) -> bool:
        """Create dependencies between stories.
        
        Args:
            story_id: ID of the source story
            dependency_ids: List of dependent story IDs
            
        Returns:
            True if successful, False otherwise
        """
        try:
            for dep_id in dependency_ids:
                # Create "Depends On" relationship
                success = self.ado_client.create_work_item_link(
                    source_id=story_id,
                    target_id=dep_id,
                    link_type="Depends On"
                )
                
                if not success:
                    logger.error(f"Failed to create dependency from {story_id} to {dep_id}")
                    return False
            
            logger.info(f"Created {len(dependency_ids)} dependencies for story {story_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating dependencies for story {story_id}: {str(e)}")
            return False
    
    async def get_story_dependencies(self, story_id: str) -> Dict[str, Any]:
        """Get dependencies for a story.
        
        Args:
            story_id: ID of the story
            
        Returns:
            Dependency information
        """
        try:
            # This would require additional ADO API calls to get relationship information
            # For now, we'll return a placeholder structure
            
            return {
                "story_id": story_id,
                "dependencies": [],
                "dependents": [],
                "blocks": [],
                "blocked_by": []
            }
            
        except Exception as e:
            logger.error(f"Error getting dependencies for story {story_id}: {str(e)}")
            return {"error": str(e)}
