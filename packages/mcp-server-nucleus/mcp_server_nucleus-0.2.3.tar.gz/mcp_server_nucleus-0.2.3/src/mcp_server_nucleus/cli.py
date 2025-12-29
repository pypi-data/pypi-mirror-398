#!/usr/bin/env python3
"""CLI commands for mcp-server-nucleus."""

import os
import json
import sys
from pathlib import Path

SAMPLE_STATE = {
    "version": "1.0.0",
    "current_sprint": {
        "name": "Sprint 1",
        "focus": "Getting Started with Nucleus",
        "started_at": None
    },
    "top_3_leverage_actions": [
        "Set up your first agent",
        "Configure triggers",
        "Connect to Claude Desktop"
    ]
}

SAMPLE_TRIGGERS = {
    "version": "1.0.0",
    "triggers": [
        {
            "event_type": "task_completed",
            "target_agent": "synthesizer",
            "emitter_filter": None
        },
        {
            "event_type": "research_done",
            "target_agent": "architect",
            "emitter_filter": ["researcher"]
        }
    ]
}

SAMPLE_AGENT = '''# {agent_name} Agent

## Role
Define what this agent does.

## Responsibilities
- Task 1
- Task 2

## Triggers
Activated when: [define trigger conditions]

## Output Format
Describe expected output format.
'''

def init_brain(path: str = ".brain"):
    """Initialize a new .brain directory structure."""
    brain_path = Path(path)
    
    if brain_path.exists():
        print(f"⚠️  Directory {path} already exists.")
        response = input("Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Aborted.")
            return False
    
    print(f"🧠 Initializing Nuclear Brain at {path}/...")
    
    # Create directory structure
    dirs = [
        brain_path / "ledger",
        brain_path / "artifacts" / "research",
        brain_path / "artifacts" / "strategy",
        brain_path / "agents",
        brain_path / "memory",
    ]
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"  📁 Created {d}")
    
    # Create initial files
    (brain_path / "ledger" / "state.json").write_text(
        json.dumps(SAMPLE_STATE, indent=2)
    )
    print(f"  📄 Created ledger/state.json")
    
    (brain_path / "ledger" / "triggers.json").write_text(
        json.dumps(SAMPLE_TRIGGERS, indent=2)
    )
    print(f"  📄 Created ledger/triggers.json")
    
    (brain_path / "ledger" / "events.jsonl").write_text("")
    print(f"  📄 Created ledger/events.jsonl")
    
    # Create sample agent
    (brain_path / "agents" / "synthesizer.md").write_text(
        SAMPLE_AGENT.format(agent_name="Synthesizer")
    )
    print(f"  🤖 Created agents/synthesizer.md")
    
    # Create context file
    (brain_path / "memory" / "context.md").write_text(
        "# Project Context\n\nDescribe your project here.\n"
    )
    print(f"  📝 Created memory/context.md")
    
    print(f"\n✅ Nuclear Brain initialized!")
    
    # Generate config dictionary
    abs_path = str(brain_path.absolute())
    nucleus_config = {
        "command": "python3",
        "args": ["-m", "mcp_server_nucleus"],
        "env": {"NUCLEAR_BRAIN_PATH": abs_path}
    }
    
    # Attempt auto-configuration for Claude Desktop
    claude_config_path = Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    auto_configured = False
    
    if claude_config_path.exists():
        try:
            print(f"\n🔍 Found Claude Desktop config...")
            # Create backup
            backup_path = claude_config_path.with_suffix(".json.bak")
            if not backup_path.exists():
                import shutil
                shutil.copy2(claude_config_path, backup_path)
                print(f"  📦 Created backup at {backup_path}")
            
            # Read and parse
            with open(claude_config_path, 'r') as f:
                config_data = json.load(f)
            
            # Update config
            if "mcpServers" not in config_data:
                config_data["mcpServers"] = {}
            
            if "nucleus" not in config_data["mcpServers"]:
                config_data["mcpServers"]["nucleus"] = nucleus_config
                
                with open(claude_config_path, 'w') as f:
                    json.dump(config_data, f, indent=2)
                
                print(f"  ✅ Auto-configured 'nucleus' in Claude Desktop settings!")
                auto_configured = True
            else:
                print(f"  ℹ️  'nucleus' already configured in Claude Desktop.")
                auto_configured = True
                
        except Exception as e:
            print(f"  ⚠️  Could not auto-configure: {e}")
            print(f"  (Don't worry, just copy the snippet below)")

    if not auto_configured:
        config_snippet = f'''"nucleus": {{
    "command": "python3",
    "args": ["-m", "mcp_server_nucleus"],
    "env": {{
      "NUCLEAR_BRAIN_PATH": "{abs_path}"
    }}
  }}'''
        
        print(f"\n" + "="*60)
        print(f"📋 COPY THIS into your AI client's config:")
        print(f"="*60)
        print()
        print(config_snippet)
        print()
        print(f"="*60)
        print(f"\n📍 Config file locations:")
        print(f"   Claude Desktop: ~/Library/Application Support/Claude/claude_desktop_config.json")
        print(f"   Cursor:         ~/.cursor/mcp.json") 
        print(f"   Windsurf:       ~/.codeium/windsurf/mcp_config.json")
    
    print(f"\n💡 Next Step: Restart your AI Client and ask:")
    print(f"   'What's my current sprint focus?'")
    
    return True


def main():
    """CLI entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        path = sys.argv[2] if len(sys.argv) > 2 else ".brain"
        init_brain(path)
    else:
        # Default: run MCP server
        from mcp_server_nucleus import mcp
        mcp.run()


if __name__ == "__main__":
    main()
