# Changelog

All notable changes to StackWeaver will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### 🚀 In Progress
- Epic 4: Core Engine & Testing
- Story 4.11: Comprehensive Documentation

### ✅ Completed
- Epic 1: Knowledge Base Foundation (100%)
- Semantic tool search with ChromaDB
- LiteLLM multi-provider support
- Configuration management
- Tool catalog (55 tools)

### 📝 Planned
- Epic 2: Stack Configuration & Generation
- Epic 3: CLI & Deployment
- Complete documentation suite

---

## [0.1.0] - 2025-12-23

### 🎉 Initial Release (MVP)

#### Added
- **Knowledge Base Foundation**
  - Tool schema with Pydantic v2
  - 55 curated OSS tools catalog
  - ChromaDB vector store integration
  - Semantic search (vector + LLM hybrid)
  - LiteLLM support (OpenAI, Anthropic, Ollama)
  - Configuration management system

- **Project Infrastructure**
  - Project structure and scaffolding
  - Poetry and setuptools configuration
  - Pre-commit hooks (black, ruff, mypy)
  - Unit test suite (pytest)
  - CI/CD pipeline (GitHub Actions)
  - Windows installation guide

#### 🔧 Technical Details
- Python 3.11+ required
- Docker Desktop required
- ChromaDB for vector search
- Click + Rich for CLI
- Pydantic v2 for validation

#### 📚 Documentation
- README with quick start
- config.yaml.example
- INSTALL_WINDOWS.md
- Epic and story documentation

---

## [0.0.1] - 2025-12-23

### 🏷️ PyPI Placeholder Release

#### Added
- Reserved `stackweaver` package name on PyPI
- Placeholder installation for early adopters
- Basic project information

---

## Release Notes Guidelines

### Categories
- **Added:** New features
- **Changed:** Changes in existing functionality
- **Deprecated:** Soon-to-be removed features
- **Removed:** Removed features
- **Fixed:** Bug fixes
- **Security:** Security fixes

### Version Format
- **Major (X.0.0):** Breaking changes
- **Minor (0.X.0):** New features, backwards compatible
- **Patch (0.0.X):** Bug fixes, backwards compatible

---

**Project:** StackWeaver - Weave Production-Ready Docker Stacks
**Repository:** https://github.com/stackweaver-io/stackweaver
**License:** MIT

---

[Unreleased]: https://github.com/stackweaver-io/stackweaver/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/stackweaver-io/stackweaver/releases/tag/v0.1.0
[0.0.1]: https://github.com/stackweaver-io/stackweaver/releases/tag/v0.0.1
