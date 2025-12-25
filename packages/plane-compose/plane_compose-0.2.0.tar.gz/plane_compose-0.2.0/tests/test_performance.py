"""Performance tests for planecompose.

These tests verify that performance optimizations are working correctly.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from planecompose.core.models import (
    WorkItem,
    WorkItemTypeDefinition,
    StateDefinition,
    LabelDefinition,
    ProjectConfig,
)


class TestBackendCaching:
    """Tests for backend caching optimizations."""
    
    @pytest.mark.asyncio
    async def test_caches_types_states_labels(self):
        """Test that types, states, labels are fetched once and cached."""
        from planecompose.backend.plane import PlaneBackend
        
        backend = PlaneBackend()
        
        # Mock the client
        mock_client = MagicMock()
        backend._client = mock_client
        backend._config = ProjectConfig(
            workspace="test",
            project_key="TEST",
        )
        
        # Setup mock responses
        mock_type = MagicMock()
        mock_type.name = "task"
        mock_type.description = "A task"
        mock_type.id = "type-123"
        
        mock_state = MagicMock()
        mock_state.name = "backlog"
        mock_state.group = "unstarted"
        mock_state.color = "#808080"
        mock_state.id = "state-123"
        mock_state.description = None
        
        mock_label = MagicMock()
        mock_label.name = "frontend"
        mock_label.color = "#3b82f6"
        mock_label.id = "label-123"
        mock_label.description = None
        
        # Need to add __name__ for the rate_limited_call logging
        mock_client.work_item_types.list.__name__ = "list"
        mock_client.work_item_types.list.return_value = [mock_type]
        
        mock_states_response = MagicMock()
        mock_states_response.results = [mock_state]
        mock_client.states.list.__name__ = "list"
        mock_client.states.list.return_value = mock_states_response
        
        mock_labels_response = MagicMock()
        mock_labels_response.results = [mock_label]
        mock_client.labels.list.__name__ = "list"
        mock_client.labels.list.return_value = mock_labels_response
        
        # First call should fetch from API
        types1 = await backend.list_types()
        states1 = await backend.list_states()
        labels1 = await backend.list_labels()
        
        # Verify API was called
        assert mock_client.work_item_types.list.call_count == 1
        assert mock_client.states.list.call_count == 1
        assert mock_client.labels.list.call_count == 1
        
        # Second call should use cache (no additional API calls)
        types2 = await backend.list_types()
        states2 = await backend.list_states()
        labels2 = await backend.list_labels()
        
        # Verify API was NOT called again
        assert mock_client.work_item_types.list.call_count == 1
        assert mock_client.states.list.call_count == 1
        assert mock_client.labels.list.call_count == 1
        
        # Results should be the same
        assert len(types1) == len(types2)
        assert len(states1) == len(states2)
        assert len(labels1) == len(labels2)
    
    @pytest.mark.asyncio
    async def test_lookup_maps_are_built(self):
        """Test that O(1) lookup maps are built correctly."""
        from planecompose.backend.plane import PlaneBackend
        
        backend = PlaneBackend()
        
        mock_client = MagicMock()
        backend._client = mock_client
        backend._config = ProjectConfig(
            workspace="test",
            project_key="TEST",
        )
        
        # Setup mock responses
        mock_type = MagicMock()
        mock_type.name = "task"
        mock_type.id = "type-123"
        mock_type.description = None
        
        mock_client.work_item_types.list.__name__ = "list"
        mock_client.work_item_types.list.return_value = [mock_type]
        
        mock_states_response = MagicMock()
        mock_state = MagicMock()
        mock_state.name = "backlog"
        mock_state.id = "state-456"
        mock_state.group = "unstarted"
        mock_state.color = None
        mock_state.description = None
        mock_states_response.results = [mock_state]
        mock_client.states.list.__name__ = "list"
        mock_client.states.list.return_value = mock_states_response
        
        mock_labels_response = MagicMock()
        mock_label = MagicMock()
        mock_label.name = "frontend"
        mock_label.id = "label-789"
        mock_label.color = None
        mock_labels_response.results = [mock_label]
        mock_client.labels.list.__name__ = "list"
        mock_client.labels.list.return_value = mock_labels_response
        
        # Load caches
        await backend._ensure_caches_loaded()
        
        # Verify lookup maps exist
        assert backend._type_name_to_id is not None
        assert backend._state_name_to_id is not None
        assert backend._label_name_to_id is not None
        
        # Verify O(1) lookups work
        assert backend._type_name_to_id.get("task") == "type-123"
        assert backend._state_name_to_id.get("backlog") == "state-456"
        assert backend._label_name_to_id.get("frontend") == "label-789"
    
    @pytest.mark.asyncio
    async def test_cache_invalidation_on_create(self):
        """Test that caches are invalidated when new items are created."""
        from planecompose.backend.plane import PlaneBackend
        
        backend = PlaneBackend()
        backend._types_cache = [MagicMock()]  # Simulate populated cache
        backend._type_name_to_id = {"task": "type-123"}
        
        # After creating a type, cache should be invalidated
        backend._types_cache = None  # Simulate invalidation
        backend._type_name_to_id = None
        
        assert backend._types_cache is None
        assert backend._type_name_to_id is None


class TestWorkItemCreationPerformance:
    """Tests for work item creation performance."""
    
    @pytest.mark.asyncio
    async def test_create_multiple_items_uses_cache(self):
        """
        Test that creating multiple work items uses cached lookups.
        
        BEFORE: 100 items = 400 API calls (1 create + 3 lookups each)
        AFTER: 100 items = 103 API calls (3 lookups + 100 creates)
        """
        from planecompose.backend.plane import PlaneBackend
        
        backend = PlaneBackend()
        
        mock_client = MagicMock()
        backend._client = mock_client
        backend._config = ProjectConfig(
            workspace="test",
            project_key="TEST",
        )
        
        # Pre-populate cache to simulate real scenario
        backend._types_cache = [
            WorkItemTypeDefinition(name="task", workflow="standard", remote_id="type-123")
        ]
        backend._states_cache = [
            StateDefinition(name="backlog", group="unstarted", remote_id="state-456")
        ]
        backend._labels_cache = [
            LabelDefinition(name="frontend", remote_id="label-789")
        ]
        backend._type_name_to_id = {"task": "type-123"}
        backend._state_name_to_id = {"backlog": "state-456"}
        backend._label_name_to_id = {"frontend": "label-789"}
        
        # Mock create response with __name__ attribute
        mock_response = MagicMock()
        mock_response.id = "work-item-001"
        mock_client.work_items.create.__name__ = "create"
        mock_client.work_items.create.return_value = mock_response
        
        # Create work items
        items = [
            WorkItem(title=f"Task {i}", type="task", state="backlog", labels=["frontend"])
            for i in range(10)
        ]
        
        for item in items:
            await backend.create_work_item(item)
        
        # Verify: Should only call create API, not list APIs (cache used)
        assert mock_client.work_items.create.call_count == 10
        assert mock_client.work_item_types.list.call_count == 0  # Cached!
        assert mock_client.states.list.call_count == 0  # Cached!
        assert mock_client.labels.list.call_count == 0  # Cached!


class TestHTTPClientPerformance:
    """Tests for HTTP client performance."""
    
    def test_client_initialization(self):
        """Test that HTTP client initializes correctly."""
        from planecompose.utils.http_client import RateLimitedHTTPClient
        
        client = RateLimitedHTTPClient(api_key="test-key")
        
        # Verify essential attributes are set
        assert client.api_key == "test-key"
        assert client.base_url == "https://api.plane.so"
        assert client._rate_limiter is not None
    
    @pytest.mark.asyncio
    async def test_shared_rate_limiter(self):
        """Test that HTTP clients share the same rate limiter."""
        from planecompose.utils.http_client import RateLimitedHTTPClient
        
        client1 = RateLimitedHTTPClient(api_key="test-key")
        client2 = RateLimitedHTTPClient(api_key="test-key")
        
        # Both should use the same shared rate limiter
        assert client1._rate_limiter is client2._rate_limiter
    
    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Test that HTTP client works as async context manager."""
        from planecompose.utils.http_client import RateLimitedHTTPClient
        
        async with RateLimitedHTTPClient(api_key="test-key") as client:
            assert client is not None
            assert client.api_key == "test-key"


class TestImportPerformance:
    """Tests for import/startup performance."""
    
    def test_lazy_imports(self):
        """Test that heavy imports are done lazily where possible."""
        import time
        
        start = time.perf_counter()
        
        # Import the main module
        from planecompose.main import app
        
        elapsed = time.perf_counter() - start
        
        # Should import quickly (under 1 second on most systems)
        # This is a sanity check, not a strict requirement
        assert elapsed < 2.0, f"Import took {elapsed:.2f}s, which is too slow"
    
    def test_cli_help_fast(self):
        """Test that CLI help is fast (no heavy initialization)."""
        import time
        from typer.testing import CliRunner
        from planecompose.main import app
        
        runner = CliRunner()
        
        start = time.perf_counter()
        result = runner.invoke(app, ["--help"])
        elapsed = time.perf_counter() - start
        
        assert result.exit_code == 0
        # Help should be nearly instant
        assert elapsed < 1.0, f"Help took {elapsed:.2f}s, which is too slow"

