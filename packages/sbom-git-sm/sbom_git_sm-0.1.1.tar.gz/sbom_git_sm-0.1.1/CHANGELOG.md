# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.1] - 2025-12-21
### Fixed
- Fixed PyPi Deploy

## [0.1.0] - 2025-12-21
### Added
- SBOM generator for Git repositories including submodules; outputs CycloneDX 1.4 with Git metadata (branch, commit + short, tags, path/worktree).
- Two hierarchy modes: default dependencies (bom-ref) and optional nested components (`--nested-components`).
- CLI options: `--component-type` (override root repository type), `--pretty`, `--output`.
