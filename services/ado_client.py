"""
Azure DevOps client for managing work items and projects.
"""

import os
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import requests
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication
from msrest.exceptions import ClientRequestError

from models.domain import UserStory, Epic, Feature, StoryType, Priority, StoryStatus

logger = logging.getLogger(__name__)


class AzureDevOpsClient:
    """Client for interacting with Azure DevOps REST API."""
    
    def __init__(self, organization: str, project: str, personal_access_token: str):
        """Initialize the Azure DevOps client.
        
        Args:
            organization: Azure DevOps organization name
            project: Project name
            personal_access_token: Personal access token for authentication
        """
        self.organization = organization
        self.project = project
        self.pat = personal_access_token
        self.base_url = f"https://dev.azure.com/{organization}"
        self.project_url = f"{self.base_url}/{project}"
        
        # Initialize connection
        credentials = BasicAuthentication('', personal_access_token)
        self.connection = Connection(base_url=self.base_url, creds=credentials)
        self.wit_client = self.connection.clients.get_work_item_tracking_client()
        
        # Headers for REST API calls
        self.headers = {
            'Authorization': f'Basic {personal_access_token}',
            'Content-Type': 'application/json-patch+json'
        }
    
    def create_epic(self, epic: Epic) -> Optional[str]:
        """Create an epic in Azure DevOps.
        
        Args:
            epic: Epic model to create
            
        Returns:
            Work item ID if successful, None otherwise
        """
        try:
            # Prepare work item fields as JSON Patch operations
            document = []
            
            # Add required fields
            document.append({
                "op": "add",
                "path": "/fields/System.Title",
                "value": epic.title
            })
            
            document.append({
                "op": "add",
                "path": "/fields/System.Description",
                "value": epic.description
            })
            
            document.append({
                "op": "add",
                "path": "/fields/System.AreaPath",
                "value": self.project
            })
            
            document.append({
                "op": "add",
                "path": "/fields/System.IterationPath",
                "value": self.project
            })
            
            document.append({
                "op": "add",
                "path": "/fields/Microsoft.VSTS.Common.Priority",
                "value": self._map_priority(epic.priority)
            })
            
            # Skip optional fields that may not be available in all Azure DevOps configurations
            # Focus on creating basic work items for testing
            
            # Create work item
            work_item = self.wit_client.create_work_item(
                document=document,
                project=self.project,
                type='Epic'
            )
            
            # Add additional epic fields after creation
            additional_fields = []
            
            if hasattr(epic, 'business_value') and epic.business_value:
                additional_fields.append({
                    "op": "add",
                    "path": "/fields/Microsoft.VSTS.Common.BusinessValue",
                    "value": epic.business_value
                })
            
            if hasattr(epic, 'target_release') and epic.target_release:
                additional_fields.append({
                    "op": "add",
                    "path": "/fields/Microsoft.VSTS.Common.TargetResolvedDate",
                    "value": epic.target_release
                })
            
            # Update epic with additional fields if any
            if additional_fields:
                try:
                    self.wit_client.update_work_item(
                        document=additional_fields,
                        id=int(work_item.id)
                    )
                    logger.info(f"Added additional fields to epic {work_item.id}")
                except Exception as field_error:
                    logger.debug(f"Failed to add additional fields to epic: {str(field_error)}")
            
            logger.info(f"Created epic '{epic.title}' with ID: {work_item.id}")
            return str(work_item.id)
            
        except Exception as e:
            logger.error(f"Failed to create epic '{epic.title}': {str(e)}")
            return None
    
    def create_user_story(self, story: UserStory, parent_id: Optional[str] = None) -> Optional[str]:
        """Create a user story in Azure DevOps.
        
        Args:
            story: User story model to create
            parent_id: ID of the parent work item (Epic or Feature)
            
        Returns:
            Work item ID if successful, None otherwise
        """
        try:
            # Prepare work item fields as JSON Patch operations
            document = []
            
            # Add required fields
            document.append({
                "op": "add",
                "path": "/fields/System.Title",
                "value": story.title
            })
            
            document.append({
                "op": "add",
                "path": "/fields/System.Description",
                "value": story.description
            })
            
            document.append({
                "op": "add",
                "path": "/fields/System.AreaPath",
                "value": self.project
            })
            
            document.append({
                "op": "add",
                "path": "/fields/System.IterationPath",
                "value": self.project
            })
            
            document.append({
                "op": "add",
                "path": "/fields/Microsoft.VSTS.Common.Priority",
                "value": self._map_priority(story.priority)
            })
            
            # Add story points if available
            if hasattr(story, 'estimated_story_points') and story.estimated_story_points:
                document.append({
                    "op": "add",
                    "path": "/fields/Microsoft.VSTS.Scheduling.StoryPoints",
                    "value": story.estimated_story_points
                })
            
            # Create work item first
            work_item = self.wit_client.create_work_item(
                document=document,
                project=self.project,
                type='User Story'
            )
            
            # Add parent link using relations if provided
            if parent_id:
                try:
                    # Create parent-child relationship using relations
                    relation_document = [{
                        "op": "add",
                        "path": "/relations/-",
                        "value": {
                            "rel": "System.LinkTypes.Hierarchy-Reverse",
                            "url": f"{self.base_url}/_apis/wit/workItems/{parent_id}"
                        }
                    }]
                    
                    # Update the user story with the relation
                    self.wit_client.update_work_item(
                        document=relation_document,
                        id=int(work_item.id)
                    )
                    
                    logger.info(f"Linked user story {work_item.id} to parent {parent_id} using relations")
                except Exception as relation_error:
                    logger.warning(f"Failed to link user story to parent using relations: {str(relation_error)}")
                    # Fallback: try using parent field update
                    try:
                        parent_document = [{
                            "op": "add",
                            "path": "/fields/System.Parent",
                            "value": int(parent_id)
                        }]
                        
                        self.wit_client.update_work_item(
                            document=parent_document,
                            id=int(work_item.id)
                        )
                        
                        logger.info(f"Linked user story {work_item.id} to parent {parent_id} using parent field")
                    except Exception as parent_error:
                        logger.error(f"Failed to link user story to parent using parent field: {str(parent_error)}")
            
            # Add acceptance criteria directly to the user story AND create linked tasks
            if hasattr(story, 'acceptance_criteria') and story.acceptance_criteria:
                # Format acceptance criteria as a structured text field
                ac_text = "Acceptance Criteria:\n\n"
                for i, criterion in enumerate(story.acceptance_criteria, 1):
                    ac_text += f"{i}. {criterion.description}\n"
                    ac_text += f"   Criteria: {criterion.criteria}\n"
                    if criterion.test_scenario:
                        ac_text += f"   Test: {criterion.test_scenario}\n"
                    ac_text += "\n"
                
                # Update the user story with acceptance criteria
                ac_document = [{
                    "op": "add",
                    "path": "/fields/Microsoft.VSTS.Common.AcceptanceCriteria",
                    "value": ac_text.strip()
                }]
                
                try:
                    self.wit_client.update_work_item(
                        document=ac_document,
                        id=int(work_item.id)
                    )
                    logger.info(f"Added acceptance criteria to user story {work_item.id}")
                except Exception as ac_error:
                    logger.warning(f"Failed to add acceptance criteria to user story: {str(ac_error)}")
                    # Try alternative field names if the primary one fails
                    alternative_fields = [
                        "System.Description",
                        "Microsoft.VSTS.Common.AcceptanceCriteria"
                    ]
                    
                    for field_name in alternative_fields:
                        try:
                            ac_document = [{
                                "op": "add",
                                "path": f"/fields/{field_name}",
                                "value": ac_text.strip()
                            }]
                            
                            self.wit_client.update_work_item(
                                document=ac_document,
                                id=int(work_item.id)
                            )
                            logger.info(f"Added acceptance criteria to field {field_name} for user story {work_item.id}")
                            break
                        except Exception as alt_error:
                            logger.debug(f"Failed to add acceptance criteria to field {field_name}: {str(alt_error)}")
                            continue
                
                # Create linked tasks for each acceptance criterion
                created_tasks = []
                for i, criterion in enumerate(story.acceptance_criteria, 1):
                    try:
                        task_id = self._create_acceptance_criterion_task(criterion, str(work_item.id), i)
                        if task_id:
                            created_tasks.append(task_id)
                            logger.info(f"Created acceptance criterion task {task_id} for user story {work_item.id}")
                        else:
                            logger.warning(f"Failed to create acceptance criterion task for criterion {i}")
                    except Exception as task_error:
                        logger.error(f"Error creating acceptance criterion task: {str(task_error)}")
                
                if created_tasks:
                    logger.info(f"Created {len(created_tasks)} acceptance criterion tasks for user story {work_item.id}")
            
            logger.info(f"Created user story '{story.title}' with ID: {work_item.id}")
            return str(work_item.id)
            
        except Exception as e:
            logger.error(f"Failed to create user story '{story.title}': {str(e)}")
            return None
    
    def create_feature(self, feature: Feature, epic_id: Optional[str] = None) -> Optional[str]:
        """Create a feature in Azure DevOps.
        
        Args:
            feature: Feature model to create
            epic_id: ID of the parent epic
            
        Returns:
            Work item ID if successful, None otherwise
        """
        try:
            # Prepare work item fields as JSON Patch operations
            document = []
            
            # Add required fields
            document.append({
                "op": "add",
                "path": "/fields/System.Title",
                "value": feature.name
            })
            
            document.append({
                "op": "add",
                "path": "/fields/System.Description",
                "value": feature.description
            })
            
            document.append({
                "op": "add",
                "path": "/fields/System.AreaPath",
                "value": self.project
            })
            
            document.append({
                "op": "add",
                "path": "/fields/System.IterationPath",
                "value": self.project
            })
            
            document.append({
                "op": "add",
                "path": "/fields/Microsoft.VSTS.Common.Priority",
                "value": self._map_priority(feature.priority)
            })
            
            # Create work item first
            work_item = self.wit_client.create_work_item(
                document=document,
                project=self.project,
                type='Feature'
            )
            
            # Add parent epic link using relations if provided
            if epic_id:
                try:
                    # Create parent-child relationship using relations
                    relation_document = [{
                        "op": "add",
                        "path": "/relations/-",
                        "value": {
                            "rel": "System.LinkTypes.Hierarchy-Reverse",
                            "url": f"{self.base_url}/_apis/wit/workItems/{epic_id}"
                        }
                    }]
                    
                    # Update the feature with the relation
                    self.wit_client.update_work_item(
                        document=relation_document,
                        id=int(work_item.id)
                    )
                    
                    logger.info(f"Linked feature {work_item.id} to epic {epic_id} using relations")
                except Exception as relation_error:
                    logger.warning(f"Failed to link feature to epic using relations: {str(relation_error)}")
                    # Fallback: try using parent field update
                    try:
                        parent_document = [{
                            "op": "add",
                            "path": "/fields/System.Parent",
                            "value": int(epic_id)
                        }]
                        
                        self.wit_client.update_work_item(
                            document=parent_document,
                            id=int(work_item.id)
                        )
                        
                        logger.info(f"Linked feature {work_item.id} to epic {epic_id} using parent field")
                    except Exception as parent_error:
                        logger.error(f"Failed to link feature to epic using parent field: {str(parent_error)}")
            
            # Add acceptance criteria to feature if available
            if hasattr(feature, 'business_requirements') and feature.business_requirements:
                # Update feature with business requirements
                req_document = [{
                    "op": "add",
                    "path": "/fields/Microsoft.VSTS.Common.BusinessValue",
                    "value": feature.business_requirements
                }]
                
                try:
                    self.wit_client.update_work_item(
                        document=req_document,
                        id=int(work_item.id)
                    )
                    logger.info(f"Added business requirements to feature {work_item.id}")
                except Exception as req_error:
                    logger.debug(f"Failed to add business requirements to feature: {str(req_error)}")
            
            logger.info(f"Created feature '{feature.name}' with ID: {work_item.id}")
            return str(work_item.id)
            
        except Exception as e:
            logger.error(f"Failed to create feature '{feature.name}': {str(e)}")
            return None
    
    def update_story_status(self, story_id: str, new_status: str) -> bool:
        """Update the status of a user story.
        
        Args:
            story_id: ID of the story to update
            new_status: New status to set
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Prepare update fields
            update_data = {
                "op": "replace",
                "path": "/fields/System.State",
                "value": new_status
            }
            
            # Update work item
            self.wit_client.update_work_item(
                document=[update_data],
                id=int(story_id)
            )
            
            logger.info(f"Updated story {story_id} status to {new_status}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update story {story_id} status: {str(e)}")
            return False
    
    def get_work_item(self, work_item_id: str) -> Optional[Dict[str, Any]]:
        """Get a work item by ID.
        
        Args:
            work_item_id: ID of the work item
            
        Returns:
            Work item data if found, None otherwise
        """
        try:
            work_item = self.wit_client.get_work_item(int(work_item_id))
            
            # Convert to dictionary format with complete data
            result = {
                "id": str(work_item.id),
                "title": work_item.fields.get("System.Title", ""),
                "description": work_item.fields.get("System.Description", ""),
                "status": work_item.fields.get("System.State", ""),
                "assigned_to": work_item.fields.get("System.AssignedTo", ""),
                "tags": work_item.fields.get("System.Tags", ""),
                "created_date": work_item.fields.get("System.CreatedDate", ""),
                "changed_date": work_item.fields.get("System.ChangedDate", ""),
                "work_item_type": work_item.fields.get("System.WorkItemType", ""),
                # Include all fields for comprehensive access
                "fields": work_item.fields,
                # Include relations if available
                "relations": getattr(work_item, 'relations', []),
                # Include links if available
                "_links": getattr(work_item, '_links', {})
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get work item {work_item_id}: {str(e)}")
            return None
    
    def search_work_items(self, wiql_query: str) -> List[Dict[str, Any]]:
        """Search for work items using WIQL.
        
        Args:
            wiql_query: WIQL query string
            
        Returns:
            List of work items matching the query
        """
        try:
            # Execute WIQL query
            query_result = self.wit_client.query_by_wiql(wiql_query)
            
            work_items = []
            for work_item_reference in query_result.work_items:
                work_item = self.get_work_item(str(work_item_reference.id))
                if work_item:
                    work_items.append(work_item)
            
            logger.info(f"Found {len(work_items)} work items matching query")
            return work_items
            
        except Exception as e:
            logger.error(f"Failed to search work items: {str(e)}")
            return []
    
    def _create_acceptance_criterion(self, criterion, parent_id: str) -> Optional[str]:
        """Create an acceptance criterion as a child work item.
        
        Args:
            criterion: Acceptance criterion model
            parent_id: ID of the parent work item
            
        Returns:
            Work item ID if successful, None otherwise
        """
        try:
            # Prepare work item fields as JSON Patch operations
            document = []
            
            # Add required fields
            document.append({
                "op": "add",
                "path": "/fields/System.Title",
                "value": criterion.description
            })
            
            document.append({
                "op": "add",
                "path": "/fields/System.Description",
                "value": criterion.criteria
            })
            
            document.append({
                "op": "add",
                "path": "/fields/System.AreaPath",
                "value": self.project
            })
            
            document.append({
                "op": "add",
                "path": "/fields/System.IterationPath",
                "value": self.project
            })
            
            document.append({
                "op": "add",
                "path": "/fields/System.Parent",
                "value": int(parent_id)
            })
            
            document.append({
                "op": "add",
                "path": "/fields/System.Tags",
                "value": "Acceptance Criterion"
            })
            
            # Create work item
            work_item = self.wit_client.create_work_item(
                document=document,
                project=self.project,
                type='Task'
            )
            
            logger.info(f"Created acceptance criterion '{criterion.description}' with ID: {work_item.id}")
            return str(work_item.id)
            
        except Exception as e:
            logger.error(f"Failed to create acceptance criterion: {str(e)}")
            return None
    
    def _create_acceptance_criterion_task(self, criterion, parent_id: str, criterion_number: int) -> Optional[str]:
        """Create an acceptance criterion as a linked task work item.
        
        Args:
            criterion: Acceptance criterion model
            parent_id: ID of the parent user story
            criterion_number: Sequential number of the acceptance criterion
            
        Returns:
            Work item ID if successful, None otherwise
        """
        try:
            # Prepare work item fields as JSON Patch operations
            document = []
            
            # Add required fields
            document.append({
                "op": "add",
                "path": "/fields/System.Title",
                "value": f"AC-{criterion_number}: {criterion.description}"
            })
            
            document.append({
                "op": "add",
                "path": "/fields/System.Description",
                "value": f"Acceptance Criterion {criterion_number}\n\nCriteria: {criterion.criteria}\n\nTest Scenario: {criterion.test_scenario if criterion.test_scenario else 'To be defined'}"
            })
            
            document.append({
                "op": "add",
                "path": "/fields/System.AreaPath",
                "value": self.project
            })
            
            document.append({
                "op": "add",
                "path": "/fields/System.IterationPath",
                "value": self.project
            })
            
            document.append({
                "op": "add",
                "path": "/fields/Microsoft.VSTS.Common.Priority",
                "value": 2  # Medium priority
            })
            
            document.append({
                "op": "add",
                "path": "/fields/System.Tags",
                "value": "Acceptance Criterion;User Story Task"
            })
            
            # Create work item
            work_item = self.wit_client.create_work_item(
                document=document,
                project=self.project,
                type='Task'
            )
            
            # Link the task to the parent user story using relations
            try:
                relation_document = [{
                    "op": "add",
                    "path": "/relations/-",
                    "value": {
                        "rel": "System.LinkTypes.Hierarchy-Reverse",
                        "url": f"{self.base_url}/_apis/wit/workItems/{parent_id}"
                    }
                }]
                
                # Update the task with the relation
                self.wit_client.update_work_item(
                    document=relation_document,
                    id=int(work_item.id)
                )
                
                logger.info(f"Linked acceptance criterion task {work_item.id} to user story {parent_id} using relations")
            except Exception as relation_error:
                logger.warning(f"Failed to link acceptance criterion task to user story using relations: {str(relation_error)}")
                # Fallback: try using parent field update
                try:
                    parent_document = [{
                        "op": "add",
                        "path": "/fields/System.Parent",
                        "value": int(parent_id)
                    }]
                    
                    self.wit_client.update_work_item(
                        document=parent_document,
                        id=int(work_item.id)
                    )
                    
                    logger.info(f"Linked acceptance criterion task {work_item.id} to user story {parent_id} using parent field")
                except Exception as parent_error:
                    logger.error(f"Failed to link acceptance criterion task to user story using parent field: {str(parent_error)}")
            
            logger.info(f"Created acceptance criterion task '{criterion.description}' with ID: {work_item.id}")
            return str(work_item.id)
            
        except Exception as e:
            logger.error(f"Failed to create acceptance criterion task '{criterion.description}': {str(e)}")
            return None
    
    def _map_priority(self, priority: Priority) -> int:
        """Map priority enum to Azure DevOps priority values.
        
        Args:
            priority: Priority enum value
            
        Returns:
            Azure DevOps priority integer
        """
        priority_map = {
            Priority.LOW: 4,
            Priority.MEDIUM: 3,
            Priority.HIGH: 2,
            Priority.CRITICAL: 1
        }
        return priority_map.get(priority, 3)
    
    def _map_status(self, status: StoryStatus) -> str:
        """Map status enum to Azure DevOps state values.
        
        Args:
            status: Status enum value
            
        Returns:
            Azure DevOps state string
        """
        status_map = {
            StoryStatus.NEW: 'New',
            StoryStatus.APPROVED: 'Approved',
            StoryStatus.IN_PROGRESS: 'Active',
            StoryStatus.IN_REVIEW: 'Resolved',
            StoryStatus.DONE: 'Closed',
            StoryStatus.REJECTED: 'Removed'
        }
        return status_map.get(status, 'New')
    
    def update_work_item_parent(self, work_item_id: str, parent_id: str) -> bool:
        """Update the parent of a work item to create hierarchical relationships.
        
        Args:
            work_item_id: ID of the work item to update
            parent_id: ID of the new parent work item
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create JSON Patch operation to set the parent
            document = [{
                "op": "add",
                "path": "/fields/System.Parent",
                "value": int(parent_id)
            }]
            
            # Update the work item with the new parent
            self.wit_client.update_work_item(
                document=document,
                id=int(work_item_id)
            )
            
            logger.info(f"Updated work item {work_item_id} parent to {parent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update work item {work_item_id} parent to {parent_id}: {str(e)}")
            return False
    
    def create_work_item_link(self, source_id: str, target_id: str, link_type: str) -> bool:
        """Create a link between work items.
        
        Args:
            source_id: Source work item ID
            target_id: Target work item ID
            link_type: Type of link (e.g., "Child", "Depends On")
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create work item link
            link_data = {
                "op": "add",
                "path": "/relations/-",
                "value": {
                    "rel": link_type,
                    "url": f"{self.base_url}/_apis/wit/workItems/{target_id}"
                }
            }
            
            # Update the source work item with the link
            self.wit_client.update_work_item(
                document=[link_data],
                id=int(source_id)
            )
            
            logger.info(f"Created {link_type} link from {source_id} to {target_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create {link_type} link from {source_id} to {target_id}: {str(e)}")
            return False
    
    def get_project_info(self) -> Optional[Dict[str, Any]]:
        """Get project information.
        
        Returns:
            Project data if successful, None otherwise
        """
        try:
            # Use REST API to get project info
            url = f"{self.base_url}/_apis/projects/{self.project}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to get project info: {str(e)}")
            return None
