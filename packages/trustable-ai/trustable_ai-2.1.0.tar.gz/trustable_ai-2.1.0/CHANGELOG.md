# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2024-12-20

### Added
- **Azure DevOps REST API Adapter**: Complete rewrite using Azure DevOps REST API v7.1
  - Direct HTTP requests (no subprocess overhead)
  - PAT token authentication (no Azure CLI dependency)
  - Automatic markdown format support for description fields
  - Single-step work item creation with all fields
  - Comprehensive error handling with HTTP status codes
- **External Enforcement Architecture**: Scripts for genuine workflow compliance
  - `scripts/sprint_review_v2.py`: Sprint review with blocking approval gate
  - `scripts/sprint_execution_interactive.py`: Interactive task implementation
  - Genuine terminal I/O for blocking approval gates
  - Comprehensive audit trails
  - Three execution modes: Pure script, Automated AI, Interactive AI
- **Documentation**:
  - `docs/AZURE_DEVOPS_SETUP.md`: Complete PAT token setup guide
  - `docs/QUICKSTART.md`: 5-minute getting started guide
  - `scripts/INTERACTIVE_MODE_PATTERN.md`: Reusable pattern for interactive workflows
  - `.claude/reports/deployments/external-enforcement-redesign.md`: Architecture details

### Changed
- **Authentication**: Azure DevOps now uses PAT tokens instead of Azure CLI
  - Set `AZURE_DEVOPS_EXT_PAT` environment variable
  - Configure `credentials_source: "env:AZURE_DEVOPS_EXT_PAT"` in config.yaml
  - See docs/AZURE_DEVOPS_SETUP.md for setup instructions
- **Work Item Operations**: All operations now use REST API v7.1
  - Faster execution (no subprocess overhead)
  - Better error messages
  - Structured JSON responses
- **Field Mapping**: Improved field name handling
  - Automatic mapping of generic fields to Azure DevOps-specific fields
  - Support for custom field mappings in config.yaml

### Fixed
- Data parsing bugs in sprint review workflow (work item state/type extraction)
- Markdown formatting in work item descriptions
- Iteration path handling (team vs project paths)
- Authentication error messages and validation

### Deprecated
- Azure CLI requirement for Azure DevOps integration
  - No longer need `az login`
  - Use PAT token authentication instead

### Removed
- `credentials_source: "cli"` option (replaced with PAT token authentication)

### Security
- PAT token authentication is more secure than Azure CLI credentials
- Tokens can be scoped to specific permissions
- Tokens are revocable and rotatable
- Environment variable storage keeps tokens out of config files

## [2.0.5] - 2024-12-07

### Added
- Re-entrant initialization with value preservation
- Context generation with hierarchical CLAUDE.md files
- Agent slash command rendering

### Changed
- Improved agent selection in init wizard
- Enhanced workflow state management

## [2.0.4] - 2024-12-06

### Added
- Multi-agent orchestration with 7 context-driven agents
- Hierarchical context management
- Skills system for reusable capabilities
- Learnings capture system

### Changed
- Consolidated specialized agents into context-driven agents
- Improved workflow templates

## [2.0.0] - 2024-11-15

### Added
- Initial public release
- Azure DevOps integration
- File-based work tracking
- State management and re-entrancy
- Multi-agent system
- Workflow templates

[2.1.0]: https://github.com/keychain-io/trustable-ai/compare/v2.0.5...v2.1.0
[2.0.5]: https://github.com/keychain-io/trustable-ai/compare/v2.0.4...v2.0.5
[2.0.4]: https://github.com/keychain-io/trustable-ai/compare/v2.0.0...v2.0.4
[2.0.0]: https://github.com/keychain-io/trustable-ai/releases/tag/v2.0.0
