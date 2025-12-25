# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),  
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.2] - 2025-12-23

### Added

- Multiple summary modes: General, Documentation, Features, and Breaking Changes
- Time-based diff analysis via `summary-by-time` command
- Optional contributors information with `--contributors` flag
- Token count estimation before summarization to help users understand API usage
- Improved error handling with clear messages for API connection, authentication, and rate limit errors
- Markdown-formatted output for better readability

### Changed

- Improved summary prompts for better focus and clarity based on selected mode
- Enhanced CLI user experience with interactive mode selection

## [0.1.1] - 2025-12-07

### Added

- Added functionality for customized LLM use - clients can now connect their personal LLM tokens to use their desired LLM. GigaChat was kept as the standard choice
- Configurable API credentials via `configure` command with secure keyring storage
- Support for multiple LLM providers (OpenAI-compatible APIs)

## [0.1.0] - 2025-12-02

### Added

- Initial MVP release
- CLI command for summarizing git diffs between commits

## _Sprint-3: 22-11-2025_

### Added

- Implemented MVP version of the CLI, including repository cloning and diff analysis pipeline
- Added unit tests covering core CLI functionality (`add unit tests`, `add testing coverage`)
- Added integration tests, including staging test workflow (`fix test-staging`)
- Added Continuous Integration workflow with Codecov reporting (`add Continuous Integration workflow`, `add Codecov to CI`, `add codecov to readme`)
- Added model credential handling (`add Model credentials`)
- Added quality assurance test cases (`Example: QAST001-1`)

### Changed

- Updated documentation and project files (`Update docs`)

## _Sprint-2: 15-11-2025_

### Added

- CLI prototype with basic repository analysis command (`cb127a3`)
- Support for analyzing public GitHub repositories via CLI
- Initial project structure with `docs/`, `Quality Requirements/`, and architecture planning

### Fixed

- Corrected broken link in documentation site (`4e76b50`)

---

## _Sprint-1: 8-11-2025_

### Added

- **Documentation Site** powered by MkDocs and GitHub Pages (`1d5844e`)
  - Automatic deployment on push to `main`
  - Live at: https://autoreporeviewitpd.github.io/AutoRepoReview/
- **Strategic Plan** for project vision and goals (`cda61e0`)
- **Tech Stack Documentation** (`64f1a32`)
- **Architecture Overview** (`c1fe279`)
- **Quality Requirements** folder with initial constraints and standards (`eb35dce`)
- Enhanced `README.md` with project overview and usage (`acf2bdc`, `11d3fb2`)

### Changed

- Improved documentation structure and navigation (`2b8aed3`, `8248850`)

---

_Note: Internal sprint planning, meeting notes, and minor documentation tweaks are not included as they do not affect end-user functionality._
