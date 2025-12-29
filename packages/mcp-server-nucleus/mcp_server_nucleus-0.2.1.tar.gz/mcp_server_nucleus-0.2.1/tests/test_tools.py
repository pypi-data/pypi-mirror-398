"""Tests for mcp-server-nucleus core functions."""

import pytest
import json
import tempfile
import os
from pathlib import Path

# Set up test brain path before importing
TEST_BRAIN = None

@pytest.fixture(autouse=True)
def setup_test_brain(tmp_path):
    """Create a temporary .brain/ structure for testing."""
    global TEST_BRAIN
    
    # Create brain structure
    brain = tmp_path / ".brain"
    brain.mkdir()
    (brain / "ledger").mkdir()
    (brain / "artifacts").mkdir()
    (brain / "artifacts" / "research").mkdir()
    
    # Create initial files
    (brain / "ledger" / "events.jsonl").write_text("")
    (brain / "ledger" / "state.json").write_text(json.dumps({
        "current_sprint": {"name": "Test Sprint", "focus": "Testing"}
    }))
    (brain / "ledger" / "triggers.json").write_text(json.dumps({
        "triggers": [
            {"event_type": "task_completed", "target_agent": "synthesizer"},
            {"event_type": "research_done", "target_agent": "architect"}
        ]
    }))
    
    # Set environment variable
    os.environ["NUCLEAR_BRAIN_PATH"] = str(brain)
    TEST_BRAIN = brain
    
    yield brain
    
    # Cleanup
    del os.environ["NUCLEAR_BRAIN_PATH"]


class TestEventTools:
    """Tests for event emission and reading."""
    
    def test_emit_event(self, setup_test_brain):
        from mcp_server_nucleus import _emit_event
        
        event_id = _emit_event(
            event_type="test_event",
            emitter="pytest",
            data={"key": "value"},
            description="Test description"
        )
        
        assert event_id.startswith("evt-")
        
        # Verify event was written
        events_file = setup_test_brain / "ledger" / "events.jsonl"
        content = events_file.read_text()
        assert "test_event" in content
        assert "pytest" in content
    
    def test_read_events(self, setup_test_brain):
        from mcp_server_nucleus import _emit_event, _read_events
        
        # Emit a few events
        _emit_event("event1", "test", {}, "")
        _emit_event("event2", "test", {}, "")
        _emit_event("event3", "test", {}, "")
        
        events = _read_events(limit=2)
        assert len(events) == 2
        assert events[-1]["type"] == "event3"


class TestStateTools:
    """Tests for state get/update."""
    
    def test_get_state(self, setup_test_brain):
        from mcp_server_nucleus import _get_state
        
        state = _get_state()
        assert "current_sprint" in state
        assert state["current_sprint"]["name"] == "Test Sprint"
    
    def test_get_state_path(self, setup_test_brain):
        from mcp_server_nucleus import _get_state
        
        focus = _get_state("current_sprint.focus")
        assert focus == "Testing"
    
    def test_update_state(self, setup_test_brain):
        from mcp_server_nucleus import _update_state, _get_state
        
        result = _update_state({"new_key": "new_value"})
        assert "success" in result.lower()
        
        state = _get_state()
        assert state["new_key"] == "new_value"


class TestTriggerTools:
    """Tests for trigger functions."""
    
    def test_get_triggers(self, setup_test_brain):
        from mcp_server_nucleus import _get_triggers
        
        triggers = _get_triggers()
        assert len(triggers) == 2
        assert triggers[0]["target_agent"] == "synthesizer"
    
    def test_evaluate_triggers(self, setup_test_brain):
        from mcp_server_nucleus import _evaluate_triggers
        
        agents = _evaluate_triggers("task_completed", "any")
        assert "synthesizer" in agents
        
        agents = _evaluate_triggers("research_done", "any")
        assert "architect" in agents
        
        agents = _evaluate_triggers("unknown_event", "any")
        assert len(agents) == 0


class TestArtifactTools:
    """Tests for artifact read/write/list."""
    
    def test_write_artifact(self, setup_test_brain):
        from mcp_server_nucleus import _write_artifact
        
        result = _write_artifact("research/test.md", "# Test Content")
        # Check the operation succeeded (returns success message or path)
        assert "test.md" in result or "success" in result.lower() or "written" in result.lower()
    
    def test_read_artifact(self, setup_test_brain):
        from mcp_server_nucleus import _write_artifact, _read_artifact
        
        _write_artifact("research/read_test.md", "Hello World")
        content = _read_artifact("research/read_test.md")
        assert content == "Hello World"
    
    def test_list_artifacts(self, setup_test_brain):
        from mcp_server_nucleus import _write_artifact, _list_artifacts
        
        _write_artifact("research/file1.md", "content")
        _write_artifact("research/file2.md", "content")
        
        artifacts = _list_artifacts("research")
        assert "research/file1.md" in artifacts or "file1.md" in str(artifacts)


class TestAgentTools:
    """Tests for agent triggering."""
    
    def test_trigger_agent(self, setup_test_brain):
        from mcp_server_nucleus import _trigger_agent, _read_events
        
        result = _trigger_agent(
            agent="researcher",
            task_description="Test task",
            context_files=None
        )
        
        assert "researcher" in result.lower()
        
        # Verify event was emitted
        events = _read_events(limit=1)
        assert len(events) == 1
        assert events[0]["type"] == "task_assigned"
