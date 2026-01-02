# Changelog

All notable changes to StackWeaver will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### 🚀 In Progress
- Epic 7: Pre-Launch Preparation
- Landing page and announcement posts

### ✅ Completed
- Epic 5: PyPI Publication (100%)
- Epic 6: MVP Improvements (100%)

### 📝 Planned
- Epic 7: Pre-Launch Preparation
- Complete documentation suite
- Launch announcement

---

## [0.1.3] - 2025-12-27

### Fixed
- **CLI Version Display** - Fix `stackweaver --version` to display correct version from package metadata
  - Previously showed hardcoded `0.1.0` instead of actual installed version
  - Now dynamically reads version from `stackweaver.__version__`
  - Users can verify they have the correct version installed

---

## [0.1.2] - 2025-12-27

### Added
- **Secret Management** 🔒
  - New `stackweaver secrets` command group with 4 subcommands:
    - `secrets init`: Create env.example template with secure placeholders
    - `secrets generate`: Generate cryptographically secure random secrets (32+ chars)
    - `secrets validate`: Check secret strength (length, character diversity)
    - `secrets check`: Verify required secrets before deployment
  - Pre-deployment secret validation integrated in `stackweaver deploy`
  - Comprehensive security guide (`docs/SECURITY.md`)
  - 21 new unit tests for secrets functionality (94% coverage)

- **New Tools** 🔧
  - PostgreSQL 16 (industry-standard relational database)
  - RabbitMQ 3 (reliable message broker with AMQP/MQTT/STOMP)
  - Elasticsearch 8.11 (distributed search and analytics engine)
  - Total tools: 58 (was 55)

- **Examples** 📚
  - Blog Stack example (WordPress + MySQL + Redis + Traefik)
  - Complete setup guide with architecture documentation
  - Environment variable templates

### Changed
- Tool categories reorganized:
  - RabbitMQ: Message Queue → Infrastructure
  - Elasticsearch: Search → Analytics
- Added 'security' emoji 🔒 to UI helpers

### Documentation
- Added comprehensive `docs/SECURITY.md` (536 lines)
  - Secret management best practices
  - Docker security hardening
  - Network security configuration
  - Production deployment checklist
  - Incident response plan
  - Compliance guidelines (GDPR, HIPAA, PCI DSS)

### Testing
- All 550 tests passing
- Secret management: 21 new tests
- Coverage: 80% overall, 94% for secrets module

---

## [0.1.1] - 2025-12-27

### Fixed
- **Dependencies:** Add `numpy<2.0` constraint for chromadb compatibility
  - ChromaDB 0.4.x not yet compatible with NumPy 2.0
  - Resolves `AttributeError: np.float_` installation error
  - Users can now install without manual numpy downgrade

### Documentation
- Add comprehensive installation tests documentation (`docs/INSTALLATION-TESTS.md`)
- Document numpy compatibility issue and solution

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
