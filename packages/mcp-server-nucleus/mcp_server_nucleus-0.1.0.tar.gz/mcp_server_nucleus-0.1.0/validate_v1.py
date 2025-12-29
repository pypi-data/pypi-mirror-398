
import os
import sys
from pathlib import Path

# Mock environment
os.environ["NUCLEAR_BRAIN_PATH"] = str(Path("../.brain").resolve())

# Add src to path
sys.path.insert(0, str(Path("src").resolve()))

# Import the CORE functions (underscore-prefixed), not the MCP wrappers
from mcp_server_nucleus import (
    _emit_event, _read_events,
    _get_state, _update_state,
    _read_artifact, _write_artifact, _list_artifacts,
    _trigger_agent
)

def test_events():
    print("Testing Events...")
    eid = _emit_event("test_event", "tester", {"test": True})
    print(f"  Emitted: {eid}")
    assert not eid.startswith("Error")
    
    events = _read_events(1)
    print(f"  Read: {len(events)} events")
    assert len(events) >= 1
    assert events[-1]['type'] == 'test_event'
    print("  Events OK ✓")

def test_state():
    print("Testing State...")
    result = _update_state({"nucleus_test_key": "nucleus_test_value"})
    assert result == "State updated successfully"
    print(f"  Update result: {result}")
    
    state = _get_state()
    assert state.get("nucleus_test_key") == "nucleus_test_value"
    print("  State OK ✓")

def test_artifacts():
    print("Testing Artifacts...")
    result = _write_artifact("test/nucleus_test_doc.md", "# Hello from Nucleus MCP")
    print(f"  Write result: {result}")
    assert "Successfully" in result
    
    content = _read_artifact("test/nucleus_test_doc.md")
    assert "# Hello from Nucleus MCP" in content
    print("  Read OK ✓")
    
    files = _list_artifacts("test")
    assert "test/nucleus_test_doc.md" in files
    print(f"  List: {files[:3]}...")
    print("  Artifacts OK ✓")

def test_trigger():
    print("Testing Trigger Agent...")
    result = _trigger_agent("researcher", "Test task from nucleus")
    print(f"  Result: {result}")
    assert "Triggered researcher" in result
    print("  Trigger OK ✓")

if __name__ == "__main__":
    try:
        test_events()
        test_state()
        test_artifacts()
        test_trigger()
        print("\n✅ ALL TESTS PASSED")
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: Assertion Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
