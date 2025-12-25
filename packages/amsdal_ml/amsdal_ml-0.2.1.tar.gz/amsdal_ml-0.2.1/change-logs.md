## [v0.2.1](https://pypi.org/project/amsdal_ml/0.2.1/) - 2025-12-23

### New Features

- Upgraded dependencies: 
    "pydantic~=2.12",
    "pydantic-settings~=2.12",

## [v0.2.0](https://pypi.org/project/amsdal_ml/0.2.0/) - 2025-12-16

### New Features

- Added `PythonTool`: Tool for executing Python functions within agents
- Added `FunctionalCallingAgent`: Agent specialized in functional calling with configurable tools
- Added `NLQueryRetriever`: Retriever for natural language queries on AMSDAL querysets
- Added `DefaultIngestionPipeline`: Pipeline for document ingestion including loader, cleaner, splitter, embedder, and store
- Added `ModelIngester`: High-level ingester for processing models with customizable pipelines and metadata
- Added `PdfLoader`: Document loader using pymupdf for PDF processing
- Added `TextCleaner`: Processor for cleaning and normalizing text
- Added `TokenSplitter`: Splitter for dividing text into chunks based on token count
- Added `OpenAIEmbedder`: Embedder for generating embeddings via OpenAI API
- Added `EmbeddingDataStore`: Store for saving embedding data linked to source objects

## [v0.1.4](https://pypi.org/project/amsdal_ml/0.1.4/) - 2025-10-15

### Fixed retriever initialization in K8s environments

- Fixed lazy initialization of OpenAIRetriever to ensure env vars are loaded
- Added missing env parameter to stdio_client for non-persistent sessions
- Environment variables now properly passed to MCP stdio subprocesses
- Updated README.md to be production-ready
- Added RELEASE.md with step-by-step release guide

## [v0.1.3](https://pypi.org/project/amsdal_ml/0.1.3/) - 2025-10-13

### Pass env vars into stdio server

- Pass env vars into stdio server
- cleanup of app.py

## [v0.1.2](https://pypi.org/project/amsdal_ml/0.1.2/) - 2025-10-08

### Changed object_id in EmbeddingModel

- Fix for UserWarning: Field name "object_id" in "EmbeddingModel" shadows an attribute in parent "Model"

## [v0.1.1](https://pypi.org/project/amsdal_ml/0.1.1/) - 2025-10-08

### Interface of BaseFileLoader & OpenAI-based PDF file loader

- BaseFileLoader interface and OpenAI Files API implementation

## [v0.1.0](https://pypi.org/project/amsdal_ml/0.1.0/) - 2025-09-22

### Core * OpenAI-based implementations

- Interfaces and default OpenAI-based implementations