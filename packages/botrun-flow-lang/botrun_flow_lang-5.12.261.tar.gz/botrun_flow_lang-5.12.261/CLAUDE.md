# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Environment Setup
```bash
# Install dependencies (first time)
uv sync

# Add/remove packages
uv add <package>
uv remove <package>

# Activate virtual environment
source .venv/bin/activate
```

### Development Server
```bash
# Start FastAPI development server
uvicorn botrun_flow_lang.main:app --reload --host 0.0.0.0 --port 8080

# Start LangGraph development server (when needed)
langgraph dev
```

### Testing
```bash
# Run functional tests (uses LLM validation)
python -m pytest botrun_flow_lang/tests/api_functional_tests.py

# Run specific tests
python -m pytest botrun_flow_lang/tests/test_<module>.py
```

### Deployment
```bash
# Deploy to different environments
./sh/deploy_dev.sh     # Development
./sh/deploy_prod.sh    # Production  
./sh/deploy_fast.sh    # Fast deployment variant
```

### Code Quality
```bash
# Export requirements for deployment
uv export --format requirements-txt --output-file requirements.txt --no-hashes
```

## High-Level Architecture

### Core System Components

**botrun_flow_lang** is a multi-tenant LLM agent orchestration platform built on FastAPI and LangGraph, designed for Google Cloud Platform deployment.

#### 1. API Layer (`botrun_flow_lang/api/`)
- **hatch_api.py**: Core workflow management system ("Hatch" represents configured AI assistants)
- **langgraph_api.py**: LangGraph agent invocation with multi-modal support
- **line_bot_api.py**: Line messaging platform integration
- **search_api.py**: Web search via Tavily/Perplexity
- **storage_api.py**: File management with Google Cloud Storage
- **user_setting_api.py**: User preferences and configurations

#### 2. LangGraph Agents (`langgraph_agents/`)
- **ReactAgent**: General-purpose conversational agent with tool access
- **SearchAgent**: Specialized web search and information retrieval
- **Tools**: Web search, Plotly charts, Mermaid diagrams, code execution, PDF/image analysis
- **Checkpointing**: Firestore-backed conversation history persistence

#### 3. Services Layer (`services/`)
Uses factory pattern for service instantiation across environments:
- **hatch_factory.py**: Hatch workflow services
- **storage_factory.py**: Cloud storage services  
- **user_setting_factory.py**: User configuration services

#### 4. Multi-Modal Capabilities
- PDF document analysis with pdfminer-six
- Image processing (up to 20 images per request)
- YouTube transcript extraction
- Google Docs integration for dynamic prompts

### Key Architectural Patterns

#### "Hatch" System
Central abstraction for AI workflow configurations containing:
- `prompt_template`: System prompt
- `enable_search`: Web search capability
- `enable_agent`: LangGraph agent mode  
- `google_doc_link`: Dynamic prompt source
- `model_name`: Specific LLM model (Claude, GPT, Gemini)

#### Factory Pattern
Consistent service instantiation using environment-based configuration:
```python
def hatch_store_factory() -> HatchFsStore:
    env_name = os.getenv("HATCH_ENV_NAME", "botrun-hatch-dev")
    return HatchFsStore(env_name)
```

#### Multi-Tenant Architecture  
- User-scoped data isolation in Firestore
- Environment-based service separation (dev/staging/prod)
- Rate limiting per user via external service

### Technology Stack
- **Python 3.11.9** with UV dependency management
- **FastAPI + uvicorn** for async web services
- **LangGraph 0.4.1** for agent orchestration
- **Google Cloud**: Firestore, Cloud Storage, Cloud Run
- **LLM Providers**: Anthropic Claude, OpenAI, Google Gemini, Perplexity
- **Line Bot SDK** for chatbot integration

### Development Guidelines

#### When modifying APIs:
- Update `CHANGELOG.md` for any changes
- Use factory pattern for service dependencies
- Follow async/await patterns throughout
- Test with both local and deployed endpoints

#### When adding LangGraph tools:
- Place in `langgraph_agents/agents/tools/`
- Follow existing tool patterns for parameter validation
- Add utility functions to `langgraph_agents/agents/util/`

#### When working with multi-modal features:
- Use `img_util.py` for image processing
- Use `pdf_analyzer.py` for document analysis
- Respect file size limits and supported formats

#### GitHub Repository
- Default repository: https://github.com/sebastian-hsu/botrun_flow_lang
- User account: sebastian-hsu

### Environment Configuration
- Uses `.env` files for environment-specific settings
- Separate Google Cloud service accounts per environment
- Dynamic configuration via Google Sheets and Google Docs