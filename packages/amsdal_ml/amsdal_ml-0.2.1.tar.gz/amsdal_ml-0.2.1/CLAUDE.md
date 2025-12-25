# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

amsdal-ml is a machine learning plugin for the AMSDAL Framework that provides embeddings, vector search, and AI-driven features. It supports both synchronous and asynchronous modes, with primary focus on async operations using OpenAI models.

## Development Commands

### Environment Setup
```bash
# Install dependencies using hatch/uv
pip install --upgrade uv hatch==1.14.2
hatch env create
hatch run sync
```

### Testing
```bash
# Run all tests with coverage
hatch run cov

# Run specific test file
hatch run test tests/test_openai_model.py

# Run tests with pytest directly (after env setup)
pytest tests/
pytest tests/agents_tests/  # Run agent-specific tests
```

### Code Quality
```bash
# Run all checks (style + typing)
hatch run all

# Style checks only
hatch run style

# Format code (fix style issues)
hatch run fmt

# Type checking
hatch run typing
```

### Dependency Management
```bash
# Sync dependencies
hatch run sync

# Update lock file
hatch run lock

# Upgrade all dependencies
hatch run lock-upgrade
```

### AMSDAL CLI Commands
```bash
# Generate new model
amsdal generate model ModelName --format py

# Generate property for model
amsdal generate property --model ModelName property_name

# Generate transaction
amsdal generate transaction TransactionName

# Generate hook
amsdal generate hook --model ModelName on_create
```

## Architecture

### Core Components

**ML Models** (`amsdal_ml/ml_models/`)
- Abstract base class `MLModel` defines the interface for all ML models
- Supports both sync/async invoke and streaming methods
- Primary implementation uses OpenAI API
- All models must implement `setup()`, `teardown()`, `invoke()`, `ainvoke()`, `stream()`, and `astream()`
- Custom error hierarchy: `ModelError`, `ModelConnectionError`, `ModelRateLimitError`, `ModelAPIError`

**ML Ingesting** (`amsdal_ml/ml_ingesting/`)
- `MLIngesting` abstract base handles text generation and embedding creation from data
- Creates `EmbeddingData` records that link embeddings to source objects
- Supports chunk-based processing with configurable depth and token limits
- Both sync/async methods for text generation and embedding

**ML Retrievers** (`amsdal_ml/ml_retrievers/`)
- `MLRetriever` provides semantic search via similarity_search/asimilarity_search
- Returns `RetrievalChunk` objects with object metadata, chunk text, distance, and tags
- Supports filtering by include/exclude tags
- Configurable k parameter for number of results

**Agents** (`amsdal_ml/agents/`)
- Abstract `Agent` base class for Q&A and task-oriented agents
- Async-first design (sync methods raise NotImplementedError)
- Returns `AgentOutput` with answer, used_tools, and citations
- Supports streaming responses via `astream()`
- File attachments supported through `FileAttachment` interface

**MCP Integration**
- **Server** (`amsdal_ml/mcp_server/`): Exposes retriever search as MCP tool via stdio
- **Client** (`amsdal_ml/mcp_client/`): Supports both stdio and HTTP transports for calling MCP tools
- Server accepts base64-encoded AMSDAL config for initialization

**File I/O** (`amsdal_ml/fileio/`)
- `BaseFileLoader` abstract class for uploading files to ML providers
- `FileAttachment` represents processed attachments (types: PLAIN_TEXT, FILE_ID)
- `FileItem` helper for creating attachments from paths, bytes, or strings

### Data Models

**EmbeddingModel** (`amsdal_ml/models/embedding_model.py`)
- Core model storing embeddings in database
- Links to source object via `data_object_class` and `data_object_id`
- Stores 1536-dimensional vectors (OpenAI text-embedding-3-small default)
- Includes chunk_index, raw_text, tags, and ml_metadata fields

### Configuration

**MLConfig** (`amsdal_ml/ml_config.py`)
- Loaded from `.env` file using pydantic-settings
- Key settings:
  - `ml_model_class`: Path to ML model implementation
  - `ml_retriever_class`: Path to retriever implementation
  - `ml_ingesting_class`: Path to ingesting implementation
  - `llm_model_name`: Default 'gpt-4o'
  - `embed_model_name`: Default 'text-embedding-3-small'
  - `embed_max_depth`, `embed_max_chunks`, `embed_max_tokens_per_chunk`: Chunking parameters
  - `retriever_default_k`: Number of results for similarity search
  - `openai_api_key`, `claude_api_key`: API credentials
  - `embedding_targets`: List of models to embed

**Database Config** (`config.yml`)
- Defines AMSDAL connections (sqlite_history, sqlite_state, lock)
- Resources config maps repository and lakehouse to connections
- Set `async_mode: true` for async operations

## Code Style

- Python 3.11+ required
- Uses Ruff for linting and formatting with 120-char line length
- Single quotes enforced (`quote-style = "single"`)
- Import ordering: force-single-line with order-by-type
- Type checking via mypy with strict settings (disallow_any_generics, check_untyped_defs)
- Excludes migrations directory from linting

## Testing

- Uses pytest with pytest-asyncio for async tests
- Test fixtures in `tests/conftest.py` provide mocked OpenAI clients
- `OPENAI_API_KEY` set to dummy value in tests via fixture
- Coverage tracking with coverage.py

## CI/CD

The project uses self-hosted runners with two jobs:
1. **license-check**: Validates third-party licenses using `license_check.py`
2. **test-lint**: Runs on Python 3.11 and 3.12, executes `hatch run all` (style+typing) and `hatch run cov`

## Key Patterns

1. **Async-First**: Most components prioritize async methods; sync methods often raise NotImplementedError
2. **Abstract Base Classes**: Heavy use of ABCs to define interfaces for models, retrievers, ingesters, and agents
3. **Configuration via Pydantic**: Settings loaded from environment with type validation
4. **AMSDAL Integration**: Uses AMSDAL's model system, manager, and connection framework
5. **Chunking Strategy**: Text split into chunks with metadata preservation for better embedding quality
6. **Tag-Based Filtering**: Embeddings tagged for fine-grained retrieval control