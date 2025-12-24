# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.3] - 2025-01-15

### Added
- **Auto-update system**: Background update installation with automatic restart
  - New `updates.auto_update` config option (default: false)
  - Non-blocking background installation using threading
  - Smart restart mechanism with user confirmation
  - Error logging to `~/.claux/update_error.log`
  - Restart flag system (`~/.claux/.needs_restart`)
  - Localized messages in English and Russian

### Changed
- Enhanced update workflow for better user experience
  - Auto-update checks PyPI once per 24h when enabled
  - User can work while update downloads in background
  - Graceful fallback if user declines restart

## [0.3.2] - 2024-12-20

### Documentation
- Added explicit instruction to never suggest manual PyPI publishing
- GitHub Actions workflow handles automatic publishing on release

## [0.3.1] - 2024-12-20

### Added
- **mcp**: added "None" mode for zero-token MCP configuration
  - Allows running Claude Code without any MCP servers
  - Useful for minimal overhead scenarios
  - Added `.mcp.none.json` template

### Changed
- **ui**: moved language settings to Settings menu
  - Language switching now accessible via Settings → Change Language
  - Improved navigation flow - no more language selection loop
  - Users return to Settings menu after changing language instead of staying in language menu

## [0.3.0] - 2024-12-19

### Changed
- **refactor(interactive)**: split 1067-line module into 6 focused modules
  - Created specialized modules: interactive_ui, interactive_menus, interactive_launcher, interactive_install, interactive_builder
  - Reduced main file by 71% (1067 → 310 lines)
  - Improved maintainability and testability
  - Backward compatibility via re-exports

- **refactor(wizard)**: extract project detection and discovery to core modules
  - Created `core/detection.py` for project type detection and MCP recommendations
  - Created `core/discovery.py` for directory scanning and project discovery
  - Reduced wizard.py by 41% (405 → 237 lines)

- **refactor(agents)**: move MCP profile detection to core/mcp module
  - Moved business logic from command layer to core layer
  - Added `detect_profile_from_active()` method to MCPManager class
  - Better separation of concerns

### Added
- Context-aware interactive menu with smart installation
- Setup wizard for uninitialized projects
- Auto-detection of project context and intelligent recommendations

### Fixed
- Fixed 'claux upgrade' to work without subcommand

## [1.4.4] - 2025-12-11

### Added
- **skills**: update skill implementations (06ad51c)

## [1.4.3] - 2025-12-11

### Added
- **skills**: add SKILL.md skill (3ea7076)

## [1.4.2] - 2025-12-10

## [1.4.1] - 2025-12-08

### Added
- **commands**: update slash commands (66f839a)

## [1.4.0] - 2025-12-08

### Added
- **commands**: add speckit.taskstoissues command (d3e994b)

## [1.3.1] - 2025-12-03

## [1.3.0] - 2025-11-28

### Added
- **commands**: update slash commands (7ca6888)

## [1.2.5] - 2025-11-27

### Added
- add Serena MCP and DeksdenFlow integration (8bb40b2)
- **rules**: add LIBRARY-FIRST approach to orchestration rules (cbafa9a)
- **agents**: add reuse-hunting workflow agents (92e8a7a)

## [1.2.4] - 2025-11-22

## [1.2.3] - 2025-11-21

## [1.2.2] - 2025-11-21

## [1.2.1] - 2025-11-21

## [1.2.0] - 2025-11-21

### Added
- **ci**: add automatic npm publish on tag push (94cfc33)

## [1.1.11] - 2025-11-21

## [1.1.10] - 2025-11-19

### Added
- **release**: enhanced auto-commit type detection with priorities (222af75)

## [1.1.9] - 2025-11-19

### Added
- **release**: smart auto-commit type detection (49af988)

## [1.1.8] - 2025-11-19

### Fixed
- **release**: clean up backup files before git add (af19d7e)

## [1.1.7] - 2025-11-19

## [1.1.6] - 2025-11-19

## [1.1.5] - 2025-11-17

## [1.1.4] - 2025-11-17

## [1.1.3] - 2025-11-17

### Fixed
- **speckit**: correct Phase 0 format and execution order (a7025f7)

## [1.1.2] - 2025-11-14

## [1.1.1] - 2025-11-11
