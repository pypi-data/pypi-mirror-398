# 🧵 StackWeaver - Weave Production-Ready Docker Stacks with AI

**Turn natural language into production-ready infrastructure.**

> "I need a CRM + Project Management + Chat"
> → `stackweaver init`
> → Working stack in 5 minutes ⚡

[![CI Pipeline](https://github.com/stackweaver-io/stackweaver/actions/workflows/ci.yml/badge.svg)](https://github.com/stackweaver-io/stackweaver/actions/workflows/ci.yml)
[![GitHub](https://img.shields.io/badge/github-stackweaver--io%2Fstackweaver-blue)](https://github.com/stackweaver-io/stackweaver)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![codecov](https://codecov.io/gh/stackweaver-io/stackweaver/branch/master/graph/badge.svg)](https://codecov.io/gh/stackweaver-io/stackweaver)

---

## 🎯 What is StackWeaver?

StackWeaver is an AI-powered CLI that transforms natural language into production-ready Docker stacks:

- **🔍 Search** 50+ curated OSS tools via AI semantic search
- **⚙️ Generate** production-ready `docker-compose.yml` with 100% validation
- **🚀 Deploy** locally with automatic Traefik reverse proxy (SSL + subdomains)
- **🔐 Manage** secrets, volumes, and dependency isolation automatically

**Target User:** Technical solopreneurs who know Docker basics but hate infrastructure configuration.

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** (Check: `python --version`)
- **Docker Desktop** (Check: `docker --version`)
- **Git** (Check: `git --version`)

### Installation

#### Option 1: pip + venv (Recommended for Windows)

```bash
# Clone repository
git clone https://github.com/stackweaver-io/stackweaver.git
cd stackweaver

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.\.venv\Scripts\Activate.ps1

# Activate (Linux/Mac)
source .venv/bin/activate

# Install
pip install -e .

# Verify installation
stackweaver --version
```

#### Option 2: Poetry

```bash
# Clone repository
git clone https://github.com/stackweaver-io/stackweaver.git
cd stackweaver

# Install dependencies
poetry install

# Verify installation
poetry run stackweaver --version
```

### First Run

```bash
# Initialize configuration
stackweaver version

# This creates ~/.stackweaver/config.yaml
# Edit it to add your LLM API key (optional, not needed for Ollama)

# Ingest tool catalog
python -m stackweaver.search.ingest

# You're ready!
stackweaver init
```

---

## 📖 Usage

### Search for Tools

```bash
stackweaver search "project management tool"
# Returns: Taiga, Kanboard, OpenProject

stackweaver search "I need a CRM"
# Returns: EspoCRM, SuiteCRM, Monica
```

### Initialize and Deploy a Stack

```bash
# Initialize project
stackweaver init --query "CRM for small business"

# Review generated files
ls stack/
# docker-compose.yml, .env

# Deploy the stack
stackweaver deploy

# Access your services
open http://espocrm.localhost
```

### Manage Deployments

```bash
stackweaver status      # Check running services
stackweaver logs        # View service logs
stackweaver rollback    # Stop and remove stack
```

**📚 For detailed usage, see [USER-GUIDE.md](docs/USER-GUIDE.md)**

---

## 🏗️ Architecture

### Technology Stack

- **AI/ML:** ChromaDB (vector search), LiteLLM (multi-LLM support)
- **CLI:** Click, Rich (beautiful terminal UI)
- **Docker:** Docker SDK, python-on-whales
- **Templates:** Jinja2
- **Validation:** Pydantic v2

### Project Structure

```
stackweaver/
├── cli/              # Command-line interface
├── search/           # Semantic tool search
│   ├── schemas.py    # Pydantic models
│   ├── vector_store.py  # ChromaDB wrapper
│   ├── llm_ranker.py    # LLM re-ranking
│   ├── tool_search.py   # Search API
│   └── ingest.py     # Catalog ingestion
├── generator/        # docker-compose generation (Epic 2)
├── deployer/         # Docker deployment (Epic 3)
├── knowledge_base/   # Tool catalog (55 tools)
└── utils/            # Config, helpers

tests/
├── unit/             # Unit tests (108 tests)
└── integration/      # Integration tests
```

---

## 🗂️ Configuration

Edit `~/.stackweaver/config.yaml`:

```yaml
# LLM Provider (openai, anthropic, ollama)
llm_provider: openai
llm_model: gpt-4o
llm_api_key: sk-your-key-here  # Not needed for Ollama

# Docker Settings
docker_socket: unix:///var/run/docker.sock

# Deployment Settings
traefik_domain: localhost

# Search Settings
search_top_k: 3
use_llm_rerank: true
```

**📚 For complete configuration reference, see [CONFIGURATION.md](docs/CONFIGURATION.md)**

---

## 🧪 Development

### Setup

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run tests with coverage
pytest --cov=stackweaver --cov-report=html

# Lint and format
black .
ruff check .
mypy stackweaver
```

### Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Specific module
pytest tests/unit/search/

# With coverage report
pytest --cov=stackweaver --cov-report=term-missing
```

---

## 📦 Tool Catalog

StackWeaver includes 55 production-ready OSS tools across 15 categories:

| Category | Examples |
|----------|----------|
| **Project Management** | Taiga, Kanboard, OpenProject, Wekan, Focalboard |
| **CRM** | EspoCRM, SuiteCRM, Monica, Twenty |
| **Chat** | Rocket.Chat, Mattermost, Zulip |
| **Analytics** | Metabase, Superset, Redash, Plausible, Umami |
| **Database** | PostgreSQL, MySQL, MongoDB, Redis, ClickHouse |
| **Storage** | Nextcloud, Seafile, MinIO, Pydio |
| **Automation** | n8n, Huginn, Automatisch |
| **Monitoring** | Grafana, Prometheus, Uptime Kuma |
| **Development** | Gitea, GitLab, Jenkins |
| **Security** | Vaultwarden, Authentik, Keycloak |
| **Infrastructure** | Traefik, Nginx, Caddy, Portainer |
| **Email** | Mailcow, Mailu, Docker Mailserver |
| **Wiki** | BookStack, Wiki.js, Outline |
| **CMS** | WordPress, Ghost, Strapi, Directus |
| **Marketing** | Listmonk, Mautic, Chatwoot |

All tools are:
- ✅ Actively maintained (last updated < 6 months)
- ✅ Production-ready (quality score > 5/10)
- ✅ Docker-ready (official images)
- ✅ Well-documented

---

## 🛣️ Roadmap

### Epic 1: Knowledge Base Foundation ✅ (COMPLETE)
- [x] Project structure & CLI scaffolding
- [x] Tool schema & catalog (55 tools)
- [x] ChromaDB vector store
- [x] Tool ingestion pipeline
- [x] LiteLLM multi-provider integration
- [x] Semantic search (vector + LLM hybrid)
- [x] Configuration management

### Epic 2: Stack Generation ✅ (COMPLETE)
- [x] Jinja2 template engine
- [x] docker-compose.yml generation
- [x] 3-stage validation pipeline
- [x] Conflict resolution (Isolation strategy)
- [x] Secret generation

### Epic 3: Deployer & CLI ✅ (COMPLETE)
- [x] Docker SDK integration
- [x] Traefik reverse proxy setup
- [x] CLI commands (init, deploy, status, rollback)
- [x] Health checks & monitoring

### Epic 4: Core Engine & Testing ✅ (COMPLETE)
- [x] ResourceManager (Singleton DI)
- [x] StackWeaverCore (Central orchestration)
- [x] Config & State Management
- [x] Structured Logging
- [x] Agent Interfaces (Phase 2 prep)
- [x] CI/CD Pipeline
- [x] Comprehensive Documentation
- [x] 520+ Unit & Integration Tests
- [x] 88% Code Coverage

### Phase 2: LangGraph Agents (2026)
- [ ] Curator Agent (Intelligent tool search)
- [ ] Architect Agent (Smart stack design)
- [ ] Deployer Agent (Self-healing deployment)
- [ ] Monitor Agent (Proactive monitoring)

---

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Quick Contribution Guide

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Run linters (`black . && ruff check . && mypy stackweaver`)
6. Commit (`git commit -m 'Add amazing feature'`)
7. Push (`git push origin feature/amazing-feature`)
8. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📚 Documentation

- **[User Guide](docs/USER-GUIDE.md)** - Complete usage instructions
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[Examples](docs/EXAMPLES.md)** - Real-world deployment scenarios
- **[Configuration](docs/CONFIGURATION.md)** - Detailed configuration reference
- **[Phase 2 Migration](docs/PHASE2-MIGRATION.md)** - LangGraph integration guide

## 🔗 Links

- **GitHub:** [github.com/stackweaver-io/stackweaver](https://github.com/stackweaver-io/stackweaver)
- **Issues:** [github.com/stackweaver-io/stackweaver/issues](https://github.com/stackweaver-io/stackweaver/issues)
- **Discussions:** [github.com/stackweaver-io/stackweaver/discussions](https://github.com/stackweaver-io/stackweaver/discussions)

---

## 🙏 Acknowledgments

Built with love by Ahmed and powered by:
- [ChromaDB](https://www.trychroma.com/) - Vector database
- [LiteLLM](https://github.com/BerriAI/litellm) - Multi-LLM interface
- [Click](https://click.palletsprojects.com/) + [Rich](https://rich.readthedocs.io/) - CLI framework
- [Docker](https://www.docker.com/) - Container platform
- [Pydantic](https://docs.pydantic.dev/) - Data validation

---

**Made with 🧵 by the StackWeaver team**
