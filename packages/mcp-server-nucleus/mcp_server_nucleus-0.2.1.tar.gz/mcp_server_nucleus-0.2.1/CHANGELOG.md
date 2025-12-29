# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1] - 2025-12-27

### Added
- `nucleus-init` CLI command to bootstrap a new `.brain/` directory
- Sample state.json, triggers.json, and agent template
- Interactive init with next steps guidance

## [0.2.0] - 2025-12-27

### Added
- `brain_get_triggers` - Get all defined neural triggers
- `brain_evaluate_triggers` - Evaluate which agents should activate
- MCP Resources:
  - `brain://state` - Live state.json content
  - `brain://events` - Recent events stream
  - `brain://triggers` - Trigger definitions
- MCP Prompts:
  - `activate_synthesizer` - Orchestrate current sprint
  - `start_sprint` - Initialize a new sprint

### Changed
- Cleaned repo structure (internal files moved out)
- Improved code organization

## [0.1.0] - 2025-12-27
  - `brain_emit_event` - Emit events to the ledger
  - `brain_read_events` - Read recent events
  - `brain_get_state` - Query brain state
  - `brain_update_state` - Update brain state
  - `brain_read_artifact` - Read artifact files
  - `brain_write_artifact` - Write artifact files
  - `brain_list_artifacts` - List all artifacts
  - `brain_trigger_agent` - Trigger agent with task
- FastMCP integration for MCP protocol compliance
- Claude Desktop configuration support
- MIT License
