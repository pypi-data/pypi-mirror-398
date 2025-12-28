import pytest
from grucli.stats import SessionStats

def test_session_stats_tracking():
    stats = SessionStats()
    
    # Record tool calls
    stats.record_tool_call(success=True)
    stats.record_tool_call(success=False)
    assert stats.tool_calls_total == 2
    assert stats.tool_calls_success == 1
    assert stats.tool_calls_failed == 1
    
    # Record requests
    stats.record_request("gpt-4o", api_duration=1.5)
    stats.record_request("gpt-4o", api_duration=2.5)
    assert stats.model_usage["gpt-4o"]["reqs"] == 2
    assert stats.api_time_total == 4.0
    
    # Record tokens
    stats.record_tokens("gpt-4o", input_tokens=10, output_tokens=20)
    assert stats.model_usage["gpt-4o"]["input_tokens"] == 10
    assert stats.model_usage["gpt-4o"]["output_tokens"] == 20

def test_formatted_summary():
    stats = SessionStats()
    stats.record_request("model-a", api_duration=1.0)
    summary = stats.get_formatted_summary()
    assert "Session Summary" in summary
    assert "model-a" in summary
    assert "1.0s" in summary
