import pytest
import asyncio
import json
import os
from unittest.mock import patch, MagicMock
from AnosysLoggers.utils import (
    get_env_bool, 
    _to_timestamp, 
    safe_serialize, 
    to_str_or_none,
    reassign
)
from AnosysLoggers.decorator import anosys_logger, anosys_raw_logger

# --- Utils Tests ---
def test_get_env_bool():
    with patch.dict(os.environ, {"TEST_BOOL": "true"}):
        assert get_env_bool("TEST_BOOL") is True
    with patch.dict(os.environ, {"TEST_BOOL": "0"}):
        assert get_env_bool("TEST_BOOL") is False
    # Default to True if not set
    assert get_env_bool("NON_EXISTENT") is True

def test_to_timestamp():
    # Use UTC timezone explicitly to avoid local timezone issues
    assert _to_timestamp("2023-01-01T12:00:00+00:00") == 1672574400000
    assert _to_timestamp(None) is None
    assert _to_timestamp("invalid") is None

def test_safe_serialize():
    assert safe_serialize({"a": 1}) == {"a": 1}
    assert safe_serialize([1, 2]) == [1, 2]
    
    class Unserializable:
        pass
    
    # Should serialize to empty dict because of __dict__
    res = safe_serialize(Unserializable())
    assert res == {}

def test_reassign():
    key_map = {}
    indices = {"string": 100, "number": 1, "bool": 1}
    data = {"name": "test", "count": 10, "is_valid": True}
    
    result = reassign(data, key_map, indices)
    
    assert "cvs100" in result
    assert "cvn1" in result
    assert "cvb1" in result
    assert result["cvs100"] == "test"
    assert result["cvn1"] == 10
    assert result["cvb1"] is True
    
    # Check that key_map was updated
    assert key_map["name"] == "cvs100"

# --- Decorator Tests ---

@patch("requests.post")
def test_anosys_logger_sync(mock_post):
    mock_post.return_value.status_code = 200
    
    @anosys_logger(source="test_sync")
    def sync_func(a, b):
        return a + b
        
    result = sync_func(1, 2)
    assert result == 3
    
    assert mock_post.called
    args, kwargs = mock_post.call_args
    payload = kwargs['json']
    
    # Check if source is logged
    assert payload.get("cvs200") == "test_sync"
    
@patch("requests.post")
@pytest.mark.asyncio
async def test_anosys_logger_async(mock_post):
    mock_post.return_value.status_code = 200
    
    @anosys_logger(source="test_async")
    async def async_func(a, b):
        await asyncio.sleep(0.01)
        return a * b
        
    result = await async_func(2, 3)
    assert result == 6
    
    assert mock_post.called
    args, kwargs = mock_post.call_args
    payload = kwargs['json']
    assert payload.get("cvs200") == "test_async"

@patch("requests.post")
@pytest.mark.asyncio
async def test_anosys_logger_streaming(mock_post):
    mock_post.return_value.status_code = 200
    
    @anosys_logger(source="test_streaming")
    async def async_gen_func():
        yield "part1"
        await asyncio.sleep(0.01)
        yield "part2"
        
    # Consume the generator
    result = []
    async for item in async_gen_func():
        result.append(item)
        
    assert result == ["part1", "part2"]
    
    assert mock_post.called
    args, kwargs = mock_post.call_args
    payload = kwargs['json']
    assert payload.get("cvs200") == "test_streaming"
    
    # Check if output was aggregated
    # We need to find the key for "output". In decorator.py: "output": "cvs2"
    # But keys are remapped. Let's check if "part1part2" is in values.
    # Or check if "cvs2" is in payload (if mapped correctly)
    # The key_to_cvs in decorator.py maps "output" -> "cvs2"
    # So payload should have "cvs2"
    
    # Note: reassign might change keys if they are not in key_to_cvs, but "output" is.
    # However, to_json_fallback is used on output.
    # "part1part2" stringified is just "part1part2" (or quoted)
    
    assert payload.get("cvs2") == "part1part2"

@patch("requests.post")
def test_anosys_raw_logger(mock_post):
    mock_post.return_value.status_code = 200
    
    data = {"custom_metric": 123}
    anosys_raw_logger(data)
    
    assert mock_post.called
    args, kwargs = mock_post.call_args
    payload = kwargs['json']
    
    # 'custom_metric' should be mapped to a cvn variable
    assert 123 in payload.values()
