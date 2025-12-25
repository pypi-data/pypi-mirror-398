"""Plane SDK backend implementation with performance optimizations.

Architecture:
    ALL Plane API calls go through this backend via _rate_limited_call().
    CLI code should NEVER use PlaneClient directly - it calls Backend methods.
    
    This centralizes:
    - Rate limiting (automatic, no manual acquire() needed)
    - Error handling (consistent error messages)
    - Caching (types, states, labels)
    - Type conversions (SDK objects -> our models)

Usage:
    # In CLI code - clean and simple:
    backend = PlaneBackend()
    await backend.connect(config, api_key)
    types = await backend.list_types()
    
    # DON'T do this in CLI code:
    # client = PlaneClient(...)  # ❌ No direct client usage
    # await rate_limiter.acquire()  # ❌ No manual rate limiting
"""
import asyncio
from typing import AsyncIterator, Any
from plane import PlaneClient, HttpError
from planecompose.backend.base import Backend
from planecompose.exceptions import (
    APIError,
    AuthenticationError,
    PermissionError,
    NotFoundError,
    RateLimitError,
)
from planecompose.utils.logger import get_logger

logger = get_logger()
from planecompose.core.models import (
    WorkItemTypeDefinition,
    StateDefinition,
    LabelDefinition,
    WorkItem,
    ProjectConfig,
)
from planecompose.utils.rate_limit import RateLimiter, RateLimitError


class PlaneBackend(Backend):
    """
    Plane SDK implementation of the backend interface.
    
    Performance optimizations:
    - Caches types, states, labels to avoid N+1 API calls
    - Pre-builds lookup maps for O(1) name→ID resolution
    - Shared rate limiter across all instances
    """
    
    # Shared rate limiter across all backend instances
    _rate_limiter = RateLimiter(requests_per_minute=50)
    
    def __init__(self):
        self._client: PlaneClient | None = None
        self._config: ProjectConfig | None = None
        self._project_id: str | None = None
        self._api_key: str | None = None
        
        # Performance: Cache for types, states, labels
        self._types_cache: list[WorkItemTypeDefinition] | None = None
        self._states_cache: list[StateDefinition] | None = None
        self._labels_cache: list[LabelDefinition] | None = None
        
        # Performance: Pre-built lookup maps for O(1) access
        self._type_name_to_id: dict[str, str] | None = None
        self._state_name_to_id: dict[str, str] | None = None
        self._label_name_to_id: dict[str, str] | None = None
    
    async def connect(self, config: ProjectConfig, api_key: str) -> None:
        """Establish connection to Plane."""
        self._config = config
        self._api_key = api_key
        self._project_id = config.project_uuid or config.project_key
        self._client = PlaneClient(
            base_url=config.api_url,
            api_key=api_key,
        )
        
        # Clear caches on new connection
        self._invalidate_cache()
    
    @classmethod
    def create_client(cls, api_url: str, api_key: str) -> "PlaneBackend":
        """
        Create a backend instance without full project context.
        
        Use this for operations that don't require a project (e.g., listing projects).
        For project-specific operations, use connect() instead.
        """
        backend = cls()
        backend._api_key = api_key
        backend._client = PlaneClient(base_url=api_url, api_key=api_key)
        return backend
    
    def _invalidate_cache(self):
        """Invalidate all caches."""
        self._types_cache = None
        self._states_cache = None
        self._labels_cache = None
        self._type_name_to_id = None
        self._state_name_to_id = None
        self._label_name_to_id = None
    
    async def _ensure_caches_loaded(self):
        """
        Load and cache types, states, labels in a single batch.
        
        This is the KEY performance optimization - instead of making
        3 API calls per work item, we make 3 calls total upfront.
        """
        if self._types_cache is None:
            # Load all three in parallel for maximum speed
            self._types_cache, self._states_cache, self._labels_cache = await asyncio.gather(
                self._fetch_types(),
                self._fetch_states(),
                self._fetch_labels(),
            )
            
            # Build lookup maps for O(1) access
            self._type_name_to_id = {t.name: t.remote_id for t in self._types_cache}
            self._state_name_to_id = {s.name: s.remote_id for s in self._states_cache}
            self._label_name_to_id = {l.name: l.remote_id for l in self._labels_cache}
            
            logger.debug(f"Cached {len(self._types_cache)} types, {len(self._states_cache)} states, {len(self._labels_cache)} labels")
    
    async def _fetch_types(self) -> list[WorkItemTypeDefinition]:
        """Fetch types from API (internal, no caching)."""
        try:
            types_data = await self._rate_limited_call(
                self._client.work_item_types.list,
                workspace_slug=self._config.workspace,
                project_id=self._project_id,
            )
            
            result = []
            for t in types_data:
                result.append(WorkItemTypeDefinition(
                    name=t.name,
                    description=t.description if hasattr(t, 'description') else None,
                    workflow='standard',
                    remote_id=str(t.id),
                ))
            return result
        except HttpError:
            return []
    
    async def list_types_raw(self, workspace: str = None, project_id: str = None) -> list:
        """
        Fetch work item types with FULL metadata using SDK.
        
        Args:
            workspace: Optional workspace slug (uses self._config.workspace if not provided)
            project_id: Optional project ID (uses self._project_id if not provided)
        
        Returns raw SDK response objects with all fields:
        - id, name, description
        - logo_props (icon, emoji, colors)
        - is_epic, level, is_default
        
        Use this for clone/pull operations that need full metadata.
        """
        try:
            ws = workspace or (self._config.workspace if self._config else None)
            pid = project_id or self._project_id
            
            types_data = await self._rate_limited_call(
                self._client.work_item_types.list,
                workspace_slug=ws,
                project_id=pid,
            )
            return list(types_data)
        except HttpError:
            return []
    
    async def list_type_properties(self, type_id: str) -> list:
        """
        Fetch all properties for a work item type using SDK.
        
        Returns raw SDK response objects with all property fields.
        """
        try:
            properties = await self._rate_limited_call(
                self._client.work_item_properties.list,
                workspace_slug=self._config.workspace,
                project_id=self._project_id,
                type_id=type_id,
            )
            return list(properties)
        except HttpError:
            return []
    
    async def list_property_options(self, property_id: str) -> list:
        """
        Fetch all options for an OPTION type property using SDK.
        
        Returns raw SDK response objects with option fields.
        """
        try:
            options = await self._rate_limited_call(
                self._client.work_item_properties.options.list,
                workspace_slug=self._config.workspace,
                project_id=self._project_id,
                property_id=property_id,
            )
            return list(options)
        except HttpError:
            return []
    
    async def _fetch_states(self) -> list[StateDefinition]:
        """Fetch states from API using SDK (internal, no caching)."""
        try:
            response = await self._rate_limited_call(
                self._client.states.list,
                workspace_slug=self._config.workspace,
                project_id=self._project_id,
            )
            
            result = []
            states_data = response.results if hasattr(response, 'results') else response
            for s in states_data:
                result.append(StateDefinition(
                    name=s.name,
                    description=s.description if hasattr(s, 'description') else None,
                    color=s.color if hasattr(s, 'color') else None,
                    group=s.group if hasattr(s, 'group') else 'unstarted',
                    remote_id=str(s.id),
                ))
            return result
        except Exception as e:
            # Log the error and return empty list
            # Known issue: Plane API sometimes returns float for sequence field
            # which causes SDK validation to fail
            logger.warning(f"Failed to fetch states via SDK: {e}")
            logger.debug("This may be due to Plane API returning invalid data (e.g., float sequence)")
            return []
    
    async def _fetch_labels(self) -> list[LabelDefinition]:
        """Fetch labels from API (internal, no caching)."""
        try:
            response = await self._rate_limited_call(
                self._client.labels.list,
                workspace_slug=self._config.workspace,
                project_id=self._project_id,
            )
            
            result = []
            labels_data = response.results if hasattr(response, 'results') else response
            for l in labels_data:
                result.append(LabelDefinition(
                    name=l.name,
                    color=l.color if hasattr(l, 'color') else None,
                    remote_id=str(l.id),
                ))
            return result
        except HttpError:
            return []
    
    async def _rate_limited_call(self, func, *args, **kwargs):
        """
        Execute an API call with rate limiting and retry logic.
        """
        await self._rate_limiter.acquire()
        
        try:
            func_name = getattr(func, '__name__', str(func))
            logger.debug(f"API call: {func_name}")
            
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            logger.debug(f"API call successful: {func_name}")
            return result
            
        except HttpError as e:
            status_code = e.status_code if hasattr(e, 'status_code') else 500
            
            error_detail = str(e)
            if hasattr(e, 'response') and e.response:
                try:
                    response_data = e.response.json() if hasattr(e.response, 'json') else None
                    if response_data:
                        if isinstance(response_data, dict):
                            error_detail = (
                                response_data.get('detail') or
                                response_data.get('error') or
                                response_data.get('message') or
                                str(response_data)
                            )
                except Exception:
                    pass
            
            logger.error(f"API error {status_code}: {error_detail}")
            
            if status_code == 401:
                raise AuthenticationError() from e
            elif status_code == 403:
                raise PermissionError() from e
            elif status_code == 404:
                raise NotFoundError(resource="Resource") from e
            elif status_code == 429:
                retry_after = None
                if hasattr(e, 'response') and e.response:
                    retry_after = e.response.headers.get('Retry-After')
                    if retry_after:
                        retry_after = int(retry_after)
                raise RateLimitError(retry_after=retry_after) from e
            else:
                raise APIError(
                    message=error_detail,
                    status_code=status_code,
                ) from e
    
    async def disconnect(self) -> None:
        """Close connection and clear caches."""
        self._client = None
        self._invalidate_cache()
    
    # -------------------------------------------------------------------------
    # Public API methods (use caching)
    # -------------------------------------------------------------------------
    
    async def list_types(self) -> list[WorkItemTypeDefinition]:
        """List all work item types (cached)."""
        await self._ensure_caches_loaded()
        return self._types_cache
    
    async def list_states(self) -> list[StateDefinition]:
        """List all states (cached)."""
        await self._ensure_caches_loaded()
        return self._states_cache
    
    async def list_labels(self) -> list[LabelDefinition]:
        """List all labels (cached)."""
        await self._ensure_caches_loaded()
        return self._labels_cache
    
    async def create_type(self, type_def: WorkItemTypeDefinition) -> str:
        """Create a work item type with metadata and custom properties."""
        from plane.models.work_item_types import CreateWorkItemType
        
        logger.info(f"Creating work item type: {type_def.name}")
        
        data = CreateWorkItemType(
            name=type_def.name,
            description=type_def.description or "",
            is_epic=type_def.is_epic if hasattr(type_def, 'is_epic') else None,
            is_active=True,
        )
        
        response = await self._rate_limited_call(
            self._client.work_item_types.create,
            workspace_slug=self._config.workspace,
            project_id=self._project_id,
            data=data,
        )
        
        type_id = str(response.id)
        logger.debug(f"Created type '{type_def.name}' with ID: {type_id}")
        
        # Invalidate type cache since we added a new type
        self._types_cache = None
        self._type_name_to_id = None
        
        # Update with logo_props if provided
        if hasattr(type_def, 'logo_props') and type_def.logo_props:
            await self._update_type_logo_props(type_id, type_def.logo_props)
        
        # Create custom properties
        if hasattr(type_def, 'fields') and type_def.fields:
            await self._create_type_properties_sdk(type_id, type_def.fields)
        
        return type_id
    
    async def update_type(self, type_id: str, type_def: WorkItemTypeDefinition) -> None:
        """Update a work item type."""
        from plane.models.work_item_types import UpdateWorkItemType
        
        logger.info(f"Updating work item type: {type_def.name}")
        
        data = UpdateWorkItemType(
            description=type_def.description or "",
        )
        
        await self._rate_limited_call(
            self._client.work_item_types.update,
            workspace_slug=self._config.workspace,
            project_id=self._project_id,
            type_id=type_id,
            data=data,
        )
        
        # Invalidate type cache
        self._types_cache = None
        self._type_name_to_id = None
        
        logger.debug(f"Updated type '{type_def.name}'")
    
    async def _update_type_logo_props(self, type_id: str, logo_props):
        """Update work item type with logo props using SDK."""
        from plane.models.work_item_types import UpdateWorkItemType
        
        try:
            logger.debug(f"Updating logo_props for type {type_id}")
            
            # Build logo_props dict from the object
            logo_props_dict = {}
            if hasattr(logo_props, 'icon') and logo_props.icon:
                logo_props_dict['icon'] = logo_props.icon
            if hasattr(logo_props, 'background_color') and logo_props.background_color:
                logo_props_dict['background_color'] = logo_props.background_color
            if hasattr(logo_props, 'color') and logo_props.color:
                logo_props_dict['color'] = logo_props.color
            if hasattr(logo_props, 'emoji') and logo_props.emoji:
                logo_props_dict['emoji'] = logo_props.emoji
            
            if not logo_props_dict:
                return
            
            # Use SDK to update the type with logo_props
            data = UpdateWorkItemType(logo_props=logo_props_dict)
            
            await self._rate_limited_call(
                self._client.work_item_types.update,
                workspace_slug=self._config.workspace,
                project_id=self._project_id,
                type_id=type_id,
                data=data,
            )
            
            logger.debug(f"Updated logo_props for type {type_id}")
        except Exception as e:
            logger.warning(f"Failed to update logo_props for type {type_id}: {e}")
    
    async def _create_type_properties_sdk(self, type_id: str, fields: list):
        """Create custom properties for a work item type."""
        from plane.models.work_item_properties import CreateWorkItemProperty, CreateWorkItemPropertyOption
        from plane.models.work_item_property_configurations import TextAttributeSettings, DateAttributeSettings
        from plane.models.enums import PropertyType, RelationType
        
        logger.info(f"Creating {len(fields)} custom properties for type {type_id}")
        
        for field in fields:
            try:
                property_type_enum = self._map_field_type(field.type)
                
                property_kwargs = {
                    "display_name": field.display_name or field.name,
                    "description": "",
                    "property_type": property_type_enum.value,
                    "is_required": field.required,
                    "is_active": field.is_active if hasattr(field, 'is_active') else True,
                }
                
                if property_type_enum == PropertyType.TEXT:
                    property_kwargs["settings"] = TextAttributeSettings(display_format="multi-line")
                elif property_type_enum == PropertyType.DATETIME:
                    property_kwargs["settings"] = DateAttributeSettings(display_format="MM/dd/yyyy")
                
                if property_type_enum == PropertyType.RELATION:
                    # Default to USER for member picker, unless specified otherwise
                    relation_type_str = getattr(field, 'relation_type', 'user')
                    if relation_type_str and relation_type_str.lower() == 'issue':
                        property_kwargs["relation_type"] = RelationType.ISSUE.value
                    else:
                        property_kwargs["relation_type"] = RelationType.USER.value
                
                if hasattr(field, 'is_multi') and field.is_multi:
                    property_kwargs["is_multi"] = field.is_multi
                
                if property_type_enum == PropertyType.OPTION and hasattr(field, 'options') and field.options:
                    property_kwargs["options"] = [
                        CreateWorkItemPropertyOption(name=opt) for opt in field.options
                    ]
                
                property_data = CreateWorkItemProperty(**property_kwargs)
                
                await self._rate_limited_call(
                    self._client.work_item_properties.create,
                    workspace_slug=self._config.workspace,
                    project_id=self._project_id,
                    type_id=type_id,
                    data=property_data,
                )
                
                logger.debug(f"✓ Created property '{field.name}'")
                
            except Exception as e:
                logger.error(f"Failed to create property '{field.name}': {e}")

    def _map_field_type(self, field_type):
        """Map our FieldType to Plane's PropertyType enum."""
        from planecompose.core.models import FieldType
        from plane.models.enums import PropertyType
        
        if hasattr(field_type, 'value'):
            field_type_str = field_type.value
        else:
            field_type_str = str(field_type).lower()
        
        # Normalize aliases
        if field_type_str in ("string",):
            field_type_str = "text"
        elif field_type_str in ("enum",):
            field_type_str = "option"
        elif field_type_str in ("user",):
            field_type_str = "relation"
        elif field_type_str in ("number",):
            field_type_str = "decimal"
        
        mapping = {
            "text": PropertyType.TEXT,
            "decimal": PropertyType.DECIMAL,
            "date": PropertyType.DATETIME,
            "datetime": PropertyType.DATETIME,
            "option": PropertyType.OPTION,
            "relation": PropertyType.RELATION,
            "boolean": PropertyType.BOOLEAN,
            "url": PropertyType.URL,
            "email": PropertyType.EMAIL,
            "file": PropertyType.FILE,
        }
        
        return mapping.get(field_type_str, PropertyType.TEXT)
    
    async def create_state(self, state: StateDefinition) -> str:
        """Create a state. Returns remote ID."""
        from plane.models.states import CreateState
        
        data = CreateState(
            name=state.name,
            group=state.group,
            color=state.color or "#858585",
            description=state.description or "",
        )
        
        response = await self._rate_limited_call(
            self._client.states.create,
            workspace_slug=self._config.workspace,
            project_id=self._project_id,
            data=data,
        )
        
        # Invalidate cache
        self._states_cache = None
        self._state_name_to_id = None
        
        return str(response.id)
    
    async def update_state(self, state_id: str, state: StateDefinition) -> None:
        """Update a state."""
        from plane.models.states import UpdateState
        
        data = UpdateState(
            name=state.name,
            group=state.group,
            color=state.color or "#858585",
            description=state.description or "",
        )
        
        await self._rate_limited_call(
            self._client.states.update,
            workspace_slug=self._config.workspace,
            project_id=self._project_id,
            state_id=state_id,
            data=data,
        )
        
        # Invalidate cache
        self._states_cache = None
        self._state_name_to_id = None
    
    async def create_label(self, label: LabelDefinition) -> str:
        """Create a label. Returns remote ID."""
        from plane.models.labels import CreateLabel
        
        data = CreateLabel(
            name=label.name,
            color=label.color or "#858585",
        )
        
        response = await self._rate_limited_call(
            self._client.labels.create,
            workspace_slug=self._config.workspace,
            project_id=self._project_id,
            data=data,
        )
        
        # Invalidate cache
        self._labels_cache = None
        self._label_name_to_id = None
        
        return str(response.id)
    
    async def update_label(self, label_id: str, label: LabelDefinition) -> None:
        """Update a label."""
        from plane.models.labels import UpdateLabel
        
        data = UpdateLabel(
            name=label.name,
            color=label.color or "#858585",
        )
        
        await self._rate_limited_call(
            self._client.labels.update,
            workspace_slug=self._config.workspace,
            project_id=self._project_id,
            label_id=label_id,
            data=data,
        )
        
        # Invalidate cache
        self._labels_cache = None
        self._label_name_to_id = None
    
    async def create_work_item(self, work_item: WorkItem) -> str:
        """
        Create a work item. Returns remote ID.
        
        PERFORMANCE: Uses cached lookups instead of fetching types/states/labels
        for each work item. This reduces API calls from O(4n) to O(n+3).
        """
        from plane.models.work_items import CreateWorkItem
        
        # PERFORMANCE: Ensure caches are loaded (one-time cost)
        await self._ensure_caches_loaded()
        
        # PERFORMANCE: O(1) lookups using pre-built maps
        type_id = self._type_name_to_id.get(work_item.type) if work_item.type else None
        if work_item.type and not type_id:
            logger.warning(f"Work item type '{work_item.type}' not found. Using default.")
        
        state_id = self._state_name_to_id.get(work_item.state) if work_item.state else None
        
        label_ids = []
        if work_item.labels:
            label_ids = [
                self._label_name_to_id[name]
                for name in work_item.labels
                if name in self._label_name_to_id
            ]
        
        # Build request
        kwargs = {"name": work_item.title}
        
        if work_item.description:
            kwargs["description_html"] = work_item.description
        if type_id:
            kwargs["type_id"] = type_id
        if state_id:
            kwargs["state"] = state_id
        if work_item.priority:
            kwargs["priority"] = work_item.priority
        if label_ids:
            kwargs["labels"] = label_ids
        
        # Dates
        if work_item.start_date:
            kwargs["start_date"] = work_item.start_date
        if work_item.due_date:
            kwargs["target_date"] = work_item.due_date  # Plane API uses "target_date"
        
        # Parent relationship
        if work_item.parent:
            kwargs["parent_id"] = work_item.parent
        
        # Assignees (supports multiple)
        if work_item.assignees:
            # TODO: Resolve emails to user IDs
            kwargs["assignees"] = work_item.assignees
        
        # Dependencies & Relationships
        if work_item.blocked_by:
            kwargs["blocked_issues"] = work_item.blocked_by
        if work_item.blocking:
            kwargs["blocker_issues"] = work_item.blocking
        if work_item.duplicate_of:
            kwargs["duplicate_to"] = work_item.duplicate_of
        if work_item.relates_to:
            kwargs["related_issues"] = work_item.relates_to
        
        data = CreateWorkItem(**kwargs)
        
        response = await self._rate_limited_call(
            self._client.work_items.create,
            workspace_slug=self._config.workspace,
            project_id=self._project_id,
            data=data,
        )
        work_item_id = str(response.id)
        
        # Set custom properties if any
        if work_item.properties and type_id:
            logger.info(f"Work item has {len(work_item.properties)} custom properties to set")
            await self._set_work_item_properties(work_item_id, type_id, work_item.properties)
        elif work_item.properties and not type_id:
            logger.warning(f"Work item has properties but no type_id - cannot set properties")
        else:
            logger.debug(f"No custom properties to set for work item {work_item_id}")
        
        return work_item_id
    
    async def update_work_item(self, remote_id: str, work_item: WorkItem) -> None:
        """
        Update an existing work item.
        
        PERFORMANCE: Uses cached lookups.
        """
        from plane.models.work_items import UpdateWorkItem
        
        # PERFORMANCE: Ensure caches are loaded
        await self._ensure_caches_loaded()
        
        # PERFORMANCE: O(1) lookups
        type_id = self._type_name_to_id.get(work_item.type) if work_item.type else None
        state_id = self._state_name_to_id.get(work_item.state) if work_item.state else None
        
        label_ids = []
        if work_item.labels:
            label_ids = [
                self._label_name_to_id[name]
                for name in work_item.labels
                if name in self._label_name_to_id
            ]
        
        kwargs = {"name": work_item.title}
        
        if work_item.description:
            kwargs["description_html"] = work_item.description
        if type_id:
            kwargs["type_id"] = type_id
        if state_id:
            kwargs["state"] = state_id
        if work_item.priority:
            kwargs["priority"] = work_item.priority
        if label_ids:
            kwargs["labels"] = label_ids
        
        # Dates
        if work_item.start_date:
            kwargs["start_date"] = work_item.start_date
        if work_item.due_date:
            kwargs["target_date"] = work_item.due_date  # Plane API uses "target_date"
        
        # Parent relationship
        if work_item.parent:
            kwargs["parent_id"] = work_item.parent
        
        # Assignees (supports multiple)
        if work_item.assignees:
            kwargs["assignees"] = work_item.assignees
        
        # Dependencies & Relationships
        if work_item.blocked_by:
            kwargs["blocked_issues"] = work_item.blocked_by
        if work_item.blocking:
            kwargs["blocker_issues"] = work_item.blocking
        if work_item.duplicate_of:
            kwargs["duplicate_to"] = work_item.duplicate_of
        if work_item.relates_to:
            kwargs["related_issues"] = work_item.relates_to
        
        data = UpdateWorkItem(**kwargs)
        
        await self._rate_limited_call(
            self._client.work_items.update,
            workspace_slug=self._config.workspace,
            project_id=self._project_id,
            id=remote_id,
            data=data,
        )
        
        if work_item.properties and type_id:
            await self._set_work_item_properties(remote_id, type_id, work_item.properties)
    
    async def _set_work_item_properties(self, work_item_id: str, type_id: str, properties: dict):
        """Set custom property values for a work item."""
        from plane.models.work_item_properties import CreateWorkItemPropertyValue
        
        if not properties:
            return
        
        logger.debug(f"Setting {len(properties)} custom properties for work item {work_item_id}")
        
        try:
            properties_response = await self._rate_limited_call(
                self._client.work_item_properties.list,
                workspace_slug=self._config.workspace,
                project_id=self._project_id,
                type_id=type_id,
            )
            
            property_map = {}
            for prop in properties_response:
                prop_name = prop.display_name or getattr(prop, 'name', None)
                if prop_name:
                    prop_type_raw = getattr(prop, 'property_type', None)
                    # Convert enum to string
                    if hasattr(prop_type_raw, 'value'):
                        prop_type_str = str(prop_type_raw.value).lower()
                    else:
                        prop_type_str = str(prop_type_raw).lower() if prop_type_raw else 'text'
                    
                    property_map[prop_name] = {
                        'property_id': str(prop.id),
                        'is_multi': getattr(prop, 'is_multi', False),
                        'property_type': prop_type_str,
                    }
            
            logger.info(f"Setting {len(properties)} properties for work item {work_item_id}")
            
            for property_name, property_value in properties.items():
                if property_name not in property_map:
                    logger.warning(f"Property '{property_name}' not found in type {type_id}. Available: {list(property_map.keys())}")
                    continue
                
                property_info = property_map[property_name]
                property_id = property_info['property_id']
                property_type = property_info['property_type']
                
                logger.debug(f"Setting property '{property_name}' (type: {property_type}) = {property_value}")
                
                if 'option' in property_type:
                    await self._set_option_property_value(
                        work_item_id, property_id, property_value,
                        property_info['is_multi'], property_name
                    )
                else:
                    value_data = CreateWorkItemPropertyValue(value=property_value)
                    await self._rate_limited_call(
                        self._client.work_item_properties.values.create,
                        workspace_slug=self._config.workspace,
                        project_id=self._project_id,
                        work_item_id=work_item_id,
                        property_id=property_id,
                        data=value_data,
                    )
                    
        except Exception as e:
            logger.error(f"Failed to set properties for work item {work_item_id}: {e}")
    
    async def _set_option_property_value(self, work_item_id: str, property_id: str, value, is_multi: bool, property_name: str):
        """Set an OPTION type property value."""
        from plane.models.work_item_properties import CreateWorkItemPropertyValue
        
        try:
            options_response = await self._rate_limited_call(
                self._client.work_item_properties.options.list,
                workspace_slug=self._config.workspace,
                project_id=self._project_id,
                property_id=property_id,
            )
            
            # Build option name -> option ID map
            # Note: Options have .name attribute (not .value)
            option_map = {}
            for opt in options_response:
                opt_name = (getattr(opt, 'value', None) or 
                           getattr(opt, 'name', None) or
                           getattr(opt, 'label', None) or
                           getattr(opt, 'display_name', None))
                if opt_name:
                    option_map[opt_name] = str(opt.id)
            
            if is_multi:
                if not isinstance(value, list):
                    value = [value]
                
                option_ids = [option_map[v] for v in value if v in option_map]
                
                if option_ids:
                    value_data = CreateWorkItemPropertyValue(value=option_ids)
                    await self._rate_limited_call(
                        self._client.work_item_properties.values.create,
                        workspace_slug=self._config.workspace,
                        project_id=self._project_id,
                        work_item_id=work_item_id,
                        property_id=property_id,
                        data=value_data,
                    )
            else:
                if isinstance(value, list):
                    value = value[0] if value else None
                
                if value and value in option_map:
                    option_id = option_map[value]
                    value_data = CreateWorkItemPropertyValue(value=option_id)
                    await self._rate_limited_call(
                        self._client.work_item_properties.values.create,
                        workspace_slug=self._config.workspace,
                        project_id=self._project_id,
                        work_item_id=work_item_id,
                        property_id=property_id,
                        data=value_data,
                    )
                    
        except Exception as e:
            logger.error(f"Failed to set option property '{property_name}': {e}")
    
    async def list_work_items(self) -> list[WorkItem]:
        """
        List all work items from Plane.
        
        PERFORMANCE: Uses cached state/label maps for reverse lookups.
        """
        # Fetch work items
        response = await self._rate_limited_call(
            self._client.work_items.list,
            workspace_slug=self._config.workspace,
            project_id=self._project_id,
        )
        
        # PERFORMANCE: Use cached data
        await self._ensure_caches_loaded()
        
        # Build reverse maps
        state_id_to_name = {s.remote_id: s.name for s in self._states_cache}
        label_id_to_name = {l.remote_id: l.name for l in self._labels_cache}
        type_id_to_name = {t.remote_id: t.name for t in self._types_cache}
        
        work_items = []
        for item in response.results:
            state_name = None
            if hasattr(item, 'state') and item.state:
                state_name = state_id_to_name.get(str(item.state))
            
            label_names = []
            if hasattr(item, 'labels') and item.labels:
                for label_id in item.labels:
                    if str(label_id) in label_id_to_name:
                        label_names.append(label_id_to_name[str(label_id)])
            
            item_id = None
            if hasattr(item, 'sequence_id') and item.sequence_id:
                item_id = f"{self._config.project_key}-{item.sequence_id}"
            
            # Map type_id (UUID) to type name
            item_type = 'task'
            if hasattr(item, 'type_id') and item.type_id:
                item_type = type_id_to_name.get(str(item.type_id), 'task')
            elif hasattr(item, 'type'):
                # Fallback if type_id doesn't exist
                type_val = item.type
                if isinstance(type_val, str) and not type_val.count('-') > 3:
                    item_type = type_val
            
            # Extract dates
            start_date = getattr(item, 'start_date', None)
            due_date = getattr(item, 'target_date', None)  # Plane API uses "target_date"
            
            # Extract parent
            parent_id = None
            if hasattr(item, 'parent_id') and item.parent_id:
                parent_id = str(item.parent_id)
            
            # Extract assignees
            assignees = []
            if hasattr(item, 'assignees') and item.assignees:
                assignees = [str(a) for a in item.assignees]
            
            # Extract relationships
            blocked_by = []
            if hasattr(item, 'blocked_issues') and item.blocked_issues:
                blocked_by = [str(b) for b in item.blocked_issues]
            
            blocking = []
            if hasattr(item, 'blocker_issues') and item.blocker_issues:
                blocking = [str(b) for b in item.blocker_issues]
            
            duplicate_of = None
            if hasattr(item, 'duplicate_to') and item.duplicate_to:
                duplicate_of = str(item.duplicate_to)
            
            relates_to = []
            if hasattr(item, 'related_issues') and item.related_issues:
                relates_to = [str(r) for r in item.related_issues]
            
            work_item = WorkItem(
                id=item_id,
                title=item.name,
                description=getattr(item, 'description_html', None) or getattr(item, 'description', None),
                type=item_type,
                state=state_name,
                priority=getattr(item, 'priority', None),
                labels=label_names,
                start_date=start_date,
                due_date=due_date,
                parent=parent_id,
                assignees=assignees,
                blocked_by=blocked_by,
                blocking=blocking,
                duplicate_of=duplicate_of,
                relates_to=relates_to,
            )
            work_items.append(work_item)
        
        return work_items
    
    async def list_work_items_raw(self, workspace: str = None, project_id: str = None) -> list:
        """
        List work items returning raw SDK response objects.
        
        Args:
            workspace: Optional workspace slug (uses self._config.workspace if not provided)
            project_id: Optional project ID (uses self._project_id if not provided)
        
        Use this when you need full metadata (type_id, etc.) for property fetching.
        For normal use, prefer list_work_items() which returns WorkItem models.
        """
        ws = workspace or (self._config.workspace if self._config else None)
        pid = project_id or self._project_id
        
        response = await self._rate_limited_call(
            self._client.work_items.list,
            workspace_slug=ws,
            project_id=pid,
        )
        return response.results if hasattr(response, 'results') else list(response)
    
    # -------------------------------------------------------------------------
    # Project Operations (for clone/init without full context)
    # -------------------------------------------------------------------------
    
    async def retrieve_project(self, workspace: str, project_id: str):
        """Retrieve a project by UUID. Returns raw SDK project object."""
        return await self._rate_limited_call(
            self._client.projects.retrieve,
            workspace_slug=workspace,
            project_id=project_id,
        )
    
    async def list_projects(self, workspace: str) -> list:
        """List all projects in a workspace. Returns raw SDK response."""
        response = await self._rate_limited_call(
            self._client.projects.list,
            workspace_slug=workspace,
        )
        return response.results if hasattr(response, 'results') else list(response)
    
    async def create_project(self, workspace: str, name: str, identifier: str, description: str = "") -> Any:
        """
        Create a new project.
        
        Args:
            workspace: Workspace slug
            name: Project display name
            identifier: Short identifier (e.g., "MYPROJ")
            description: Optional description
            
        Returns: Raw SDK project object with .id attribute
        """
        from plane.models.projects import CreateProject
        
        data = CreateProject(
            name=name,
            identifier=identifier.upper(),
            description=description or "Created via plane-cli",
        )
        
        return await self._rate_limited_call(
            self._client.projects.create,
            workspace_slug=workspace,
            data=data,
        )
    
    # -------------------------------------------------------------------------
    # States Operations (for clone - returns raw SDK objects)
    # -------------------------------------------------------------------------
    
    async def list_states_raw(self, workspace: str, project_id: str) -> list:
        """
        List states returning raw SDK response objects.
        
        Use this for clone operations that need full metadata.
        Falls back to default states if SDK validation fails.
        """
        try:
            response = await self._rate_limited_call(
                self._client.states.list,
                workspace_slug=workspace,
                project_id=project_id,
            )
            return response.results if hasattr(response, 'results') else list(response)
        except Exception as e:
            # SDK validation may fail due to Plane API returning invalid data
            logger.warning(f"Failed to fetch states via SDK: {e}")
            return []
    
    async def list_labels_raw(self, workspace: str, project_id: str) -> list:
        """
        List labels returning raw SDK response objects.
        
        Use this for clone operations that need full metadata.
        """
        try:
            response = await self._rate_limited_call(
                self._client.labels.list,
                workspace_slug=workspace,
                project_id=project_id,
            )
            return response.results if hasattr(response, 'results') else list(response)
        except HttpError:
            return []
    
    # -------------------------------------------------------------------------
    # Property Value Operations (for clone/pull with properties)
    # -------------------------------------------------------------------------
    
    async def get_property_value(self, work_item_id: str, property_id: str) -> Any:
        """
        Get a property value for a work item.
        
        Returns raw SDK response (single value or list for multi-value properties).
        Returns None if property is not set or on error.
        """
        try:
            return await self._rate_limited_call(
                self._client.work_item_properties.values.retrieve,
                workspace_slug=self._config.workspace,
                project_id=self._project_id,
                work_item_id=work_item_id,
                property_id=property_id,
            )
        except NotFoundError:
            # 404 is expected when property has no value set
            return None
        except Exception:
            return None
    
    async def build_property_maps(self, types_data: list[dict]) -> dict:
        """
        Build maps of properties and options for all work item types.
        
        Options are included in the list response (no extra API calls needed).
        
        Args:
            types_data: List of type dicts with 'id' and 'name' keys
            
        Returns:
            {
                type_id: {
                    property_id: {
                        'name': str,
                        'type': str,
                        'is_multi': bool,
                        'relation_type': str | None,
                        'options': {option_id: option_value, ...}
                    }
                }
            }
        """
        property_maps = {}
        
        for type_info in types_data:
            type_id = type_info.get('id')
            if not type_id:
                continue
            
            property_maps[type_id] = {}
            
            try:
                properties = await self.list_type_properties(type_id)
                
                for prop in properties:
                    prop_id = str(prop.id)
                    prop_name = prop.display_name if hasattr(prop, 'display_name') else getattr(prop, 'name', None)
                    prop_type_raw = getattr(prop, 'property_type', None)
                    is_multi = getattr(prop, 'is_multi', False)
                    relation_type_raw = getattr(prop, 'relation_type', None)
                    
                    # Convert enums to strings
                    prop_type = str(prop_type_raw.value).lower() if hasattr(prop_type_raw, 'value') else str(prop_type_raw).lower() if prop_type_raw else 'text'
                    relation_type = str(relation_type_raw.value).lower() if hasattr(relation_type_raw, 'value') else str(relation_type_raw).lower() if relation_type_raw else None
                    
                    if not prop_name:
                        continue
                    
                    # Build option map from included options
                    options_map = {}
                    if 'option' in prop_type and hasattr(prop, 'options') and prop.options:
                        for opt in prop.options:
                            opt_id = str(opt.id) if hasattr(opt, 'id') else None
                            opt_value = (getattr(opt, 'value', None) or 
                                        getattr(opt, 'name', None) or
                                        getattr(opt, 'label', None) or
                                        getattr(opt, 'display_name', None))
                            if opt_id and opt_value:
                                options_map[opt_id] = opt_value
                    
                    property_maps[type_id][prop_id] = {
                        'name': prop_name,
                        'type': prop_type,
                        'is_multi': is_multi,
                        'relation_type': relation_type,
                        'options': options_map,
                    }
                    
            except Exception as e:
                logger.warning(f"Failed to fetch properties for type {type_id}: {e}")
        
        return property_maps
    
    async def fetch_work_item_properties_batch(
        self,
        work_items: list,
        property_maps: dict,
    ) -> dict[str, dict]:
        """
        Fetch custom property values for multiple work items efficiently.
        
        Args:
            work_items: Raw SDK work item objects (must have .id and .type_id)
            property_maps: Property maps from build_property_maps()
            
        Returns:
            {work_item_uuid: {property_name: value, ...}, ...}
        """
        results = {}
        
        # Group work items by type for efficient processing
        items_by_type: dict[str, list] = {}
        for item in work_items:
            if hasattr(item, 'type_id') and item.type_id:
                type_id = str(item.type_id)
                if type_id not in items_by_type:
                    items_by_type[type_id] = []
                items_by_type[type_id].append(item)
        
        # Process each type's items
        for type_id, items in items_by_type.items():
            if type_id not in property_maps or not property_maps[type_id]:
                continue
            
            for item in items:
                item_id = str(item.id)
                results[item_id] = {}
                
                for prop_id, prop_info in property_maps[type_id].items():
                    value_response = await self.get_property_value(item_id, prop_id)
                    
                    if value_response is None:
                        continue
                    
                    prop_type = str(prop_info['type']).lower()
                    
                    if isinstance(value_response, list):
                        # Multi-value response
                        values = []
                        for val_item in value_response:
                            val = getattr(val_item, 'value', None)
                            if val is not None:
                                val_str = str(val)
                                if 'option' in prop_type and val_str in prop_info.get('options', {}):
                                    values.append(prop_info['options'][val_str])
                                else:
                                    values.append(val)
                        if values:
                            results[item_id][prop_info['name']] = values
                    else:
                        # Single value response
                        val = getattr(value_response, 'value', None)
                        if val is not None:
                            val_str = str(val)
                            if 'option' in prop_type and val_str in prop_info.get('options', {}):
                                results[item_id][prop_info['name']] = [prop_info['options'][val_str]]
                            else:
                                results[item_id][prop_info['name']] = val
        
        return results
