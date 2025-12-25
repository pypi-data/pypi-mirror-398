"""Abstract backend interface."""
from abc import ABC, abstractmethod
from typing import AsyncIterator
from planecompose.core.models import (
    WorkItemTypeDefinition,
    StateDefinition,
    LabelDefinition,
    WorkItem,
    ProjectConfig,
)


class Backend(ABC):
    """Abstract interface for project management backends."""
    
    @abstractmethod
    async def connect(self, config: ProjectConfig, api_key: str) -> None:
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        pass
    
    @abstractmethod
    async def list_types(self) -> list[WorkItemTypeDefinition]:
        pass
    
    @abstractmethod
    async def create_type(self, type_def: WorkItemTypeDefinition) -> str:
        pass
    
    @abstractmethod
    async def list_states(self) -> list[StateDefinition]:
        pass
    
    @abstractmethod
    async def create_state(self, state: StateDefinition) -> str:
        pass
    
    @abstractmethod
    async def list_labels(self) -> list[LabelDefinition]:
        pass
    
    @abstractmethod
    async def create_label(self, label: LabelDefinition) -> str:
        pass
    
    @abstractmethod
    async def create_work_item(self, work_item: WorkItem) -> str:
        pass
    
    @abstractmethod
    async def update_work_item(self, remote_id: str, work_item: WorkItem) -> None:
        pass
    
    @abstractmethod
    async def list_work_items(self) -> list[WorkItem]:
        """List all work items from remote."""
        pass