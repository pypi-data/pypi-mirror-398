"""Tests for utility modules."""
import pytest
from datetime import datetime

from planecompose.core.models import WorkItem
from planecompose.utils.work_items import (
    generate_id_from_title,
    calculate_content_hash,
    get_tracking_key,
    make_work_item_state,
)
from planecompose.utils.rate_limit import RateLimiter


class TestWorkItemUtils:
    """Tests for work item utilities."""
    
    def test_generate_id_from_title_basic(self):
        """Test basic ID generation from title."""
        title = "Implement user authentication"
        id_ = generate_id_from_title(title)
        
        assert id_ == "implement-user-authentication"
        assert " " not in id_
        assert id_.islower()
    
    def test_generate_id_from_title_special_chars(self):
        """Test ID generation removes special characters."""
        title = "Fix bug #123 - CSS issue!"
        id_ = generate_id_from_title(title)
        
        assert "#" not in id_
        assert "!" not in id_
        assert "-" in id_
    
    def test_generate_id_from_title_long(self):
        """Test ID generation truncates long titles."""
        title = "This is a very long title that should be truncated because it exceeds the maximum length"
        id_ = generate_id_from_title(title)
        
        assert len(id_) <= 50
    
    def test_generate_id_from_title_empty(self):
        """Test ID generation with empty/weird title."""
        assert generate_id_from_title("") == "item"
        assert generate_id_from_title("!!!") == "item"
    
    def test_calculate_content_hash_deterministic(self, sample_work_item):
        """Test that content hash is deterministic."""
        hash1 = calculate_content_hash(sample_work_item)
        hash2 = calculate_content_hash(sample_work_item)
        
        assert hash1 == hash2
        assert len(hash1) == 16  # SHA256 truncated to 16 chars
    
    def test_calculate_content_hash_changes_with_content(self):
        """Test that hash changes when content changes."""
        item1 = WorkItem(title="Task A", type="task")
        item2 = WorkItem(title="Task B", type="task")
        
        hash1 = calculate_content_hash(item1)
        hash2 = calculate_content_hash(item2)
        
        assert hash1 != hash2
    
    def test_get_tracking_key_with_id(self, sample_work_item):
        """Test tracking key uses user-provided ID."""
        key = get_tracking_key(sample_work_item, "work/inbox.yaml", 0)
        
        assert key == "test-item-001"
    
    def test_get_tracking_key_without_id(self):
        """Test tracking key uses content hash when no ID."""
        item = WorkItem(title="Task without ID", type="task")
        key = get_tracking_key(item, "work/inbox.yaml", 0)
        
        assert key.startswith("hash:")
        assert len(key) > 5
    
    def test_make_work_item_state(self, sample_work_item):
        """Test creating work item state."""
        state = make_work_item_state(
            remote_id="remote-123",
            item=sample_work_item,
            source="work/inbox.yaml",
            index=0,
        )
        
        assert state.remote_id == "remote-123"
        assert state.source == "work/inbox.yaml:0"
        assert state.content_hash is not None
        assert "Z" in state.last_synced  # ISO format with Z


class TestRateLimiter:
    """Tests for rate limiter."""
    
    def test_rate_limiter_init(self):
        """Test rate limiter initialization."""
        limiter = RateLimiter(requests_per_minute=60)
        
        assert limiter.requests_per_minute == 60
        assert limiter.total_requests == 0
    
    def test_rate_limiter_stats_initial(self):
        """Test initial stats are zero."""
        limiter = RateLimiter()
        stats = limiter.get_stats()
        
        assert stats['total_requests'] == 0
        assert stats['requests_last_minute'] == 0
    
    def test_rate_limiter_reset(self):
        """Test reset clears counters."""
        limiter = RateLimiter()
        limiter.total_requests = 100
        limiter.total_wait_time = 10.0
        
        limiter.reset()
        
        assert limiter.total_requests == 0
        assert limiter.total_wait_time == 0.0
    
    @pytest.mark.asyncio
    async def test_rate_limiter_acquire(self):
        """Test acquiring a slot."""
        limiter = RateLimiter(requests_per_minute=60)
        
        await limiter.acquire()
        
        assert limiter.total_requests == 1
        assert len(limiter.request_times) == 1


class TestExceptions:
    """Tests for custom exceptions."""
    
    def test_api_error(self):
        """Test APIError creation."""
        from planecompose.exceptions import APIError
        
        error = APIError(message="Test error", status_code=500)
        
        assert error.status_code == 500
        assert error.message == "Test error"
        assert error.is_server_error()
        assert not error.is_client_error()
    
    def test_rate_limit_error(self):
        """Test RateLimitError creation."""
        from planecompose.exceptions import RateLimitError
        
        error = RateLimitError(retry_after=60)
        
        assert error.status_code == 429
        assert error.retry_after == 60
        assert error.is_rate_limit_error()
    
    def test_authentication_error(self):
        """Test AuthenticationError creation."""
        from planecompose.exceptions import AuthenticationError
        
        error = AuthenticationError()
        
        assert error.status_code == 401
        assert "authentication" in error.message.lower() or "api key" in error.message.lower()
    
    def test_not_found_error(self):
        """Test NotFoundError creation."""
        from planecompose.exceptions import NotFoundError
        
        error = NotFoundError(resource="Project")
        
        assert error.status_code == 404
        assert "Project" in error.message

