# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-12-20

### Added

- Initial release
- `mutta startproject` command to initialize agent projects
  - Creates `agents_sdk/` directory with README
  - Installs Mutta convention rules to IDE rules folder
  - Supports `.cursor/rules/`, `.claude/rules/`, and `.github/rules/`
- `mutta startservice <name>` command to scaffold new services
  - Creates service directory structure
  - Generates `manager.py`, `tools.py`, `utilities.py` templates
  - Creates `agents/` folder with example agent
- Bundled Mutta convention rules:
  - `openai-agents-sdk.mdc` - SDK overview
  - `agent-services.mdc` - Service conventions
  - `agent-additional.mdc` - Advanced patterns
  - `mutta-cli.mdc` - CLI usage guide

