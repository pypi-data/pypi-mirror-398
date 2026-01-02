# Embeddings Setup for Vector Search

This guide explains how to enable automatic embedding generation for vector search in IATP.

## Important Note

MongoDB Atlas does **not** automatically generate embeddings. The IATP application handles embedding generation:
- When documents are added, IATP generates embeddings using your chosen provider (OpenAI, Cohere, etc.)
- When searching, IATP converts your text query to embeddings before sending to MongoDB
- This happens transparently when `ENABLE_EMBEDDINGS=true`

## Overview

IATP can automatically generate embeddings when adding documents to the registry, enabling semantic vector search. This is optional - the system works without embeddings, but you won't be able to use vector search.

## Environment Variables

To enable embeddings, set the following environment variables:

```bash
# Enable embedding generation
export ENABLE_EMBEDDINGS=true

# Choose your embedding provider (default: openai)
# Options: openai, cohere
export EMBEDDING_PROVIDER=openai

# Provider-specific API keys
export OPENAI_API_KEY=your_openai_api_key      # For OpenAI
export COHERE_API_KEY=your_cohere_api_key      # For Cohere
```

## How It Works

### 1. Document Storage with Embeddings

When `ENABLE_EMBEDDINGS=true`, the system automatically generates embeddings:

**For Utility Agencies:**
- `description_embedding`: Vector embedding of the description text
- `tags_embedding`: Vector embedding of concatenated tags

**For MCP Servers:**
- `description_embedding`: Vector embedding of the description text
- `capabilities_embedding`: Vector embedding of concatenated capabilities

### 2. Search Methods

**Without Embeddings (Always Available):**
```python
# Basic keyword search (requires MongoDB text index)
results = await registry.query_agencies(query="weather")

# Atlas Search (requires Atlas Search index)
results = await registry.atlas_search("weather forecast")
```

**With Embeddings (Requires ENABLE_EMBEDDINGS=true):**
```python
# Vector search with text query (auto-converts to embedding)
results = await registry.vector_search_text("meteorological predictions")

# Vector search with specific field
results = await registry.vector_search_text("api integration", search_field="tags")

# Vector search with pre-computed embedding
embedding = await embedding_service.generate_embedding("weather")
results = await registry.vector_search(embedding)
```

## Embedding Providers

### OpenAI (Default)
- Model: `text-embedding-ada-002` (1536 dimensions)
- Best for: General-purpose semantic search
- Cost: ~$0.0001 per 1K tokens

### Cohere
- Model: `embed-english-v3.0` (1024 dimensions)
- Best for: Multilingual support
- Note: Update vector index dimensions to 1024 if using Cohere

## Installation

IATP includes optional dependencies for embeddings support. Install using uv:

```bash
# Install IATP with embeddings support (includes all providers)
uv sync --extra embeddings

# Or add specific providers to your project
uv add openai      # For OpenAI embeddings
uv add cohere      # For Cohere embeddings
```

The embedding providers are defined as optional dependencies in `pyproject.toml`:
```toml
[project.optional-dependencies]
embeddings = [
    "openai>=1.0.0",
    "cohere>=5.0.0",
]
```

### Development Note

When developing with uv:
- Use `uv sync --extra embeddings` to install optional dependencies
- Use `uv add <package>` to add new dependencies to your project
- Dependencies added with `uv add` will be added to the main dependencies in `pyproject.toml`

## Example Usage

```python
import os
os.environ["ENABLE_EMBEDDINGS"] = "true"
os.environ["OPENAI_API_KEY"] = "your-key"

from traia_iatp.registry.mongodb_registry import UtilityAgencyRegistry

# Create registry (embeddings will be auto-generated)
registry = UtilityAgencyRegistry()

# Add agency - embeddings generated automatically
await registry.add_agency(agency, endpoint, tags=["weather", "api"])

# Search using semantic similarity
results = await registry.vector_search_text("climate data analysis")
```

## Performance Considerations

1. **Embedding Generation Time**: ~100-500ms per text
2. **Batch Processing**: Use `generate_embeddings()` for multiple texts
3. **Caching**: Consider caching embeddings for frequently searched queries
4. **Cost**: Monitor API usage, especially for large datasets

## Troubleshooting

### "Failed to generate embeddings" Warning
- Check that `ENABLE_EMBEDDINGS=true`
- Verify API key is set correctly
- Check network connectivity
- Verify provider package is installed

### Vector Search Returns No Results
- Ensure documents have embeddings (added after enabling embeddings)
- Verify Vector Search index exists in Atlas
- Check that embedding dimensions match (1536 for OpenAI)

### Re-indexing Existing Data
If you have existing data without embeddings:

```python
# Script to add embeddings to existing documents
async def reindex_with_embeddings():
    registry = UtilityAgencyRegistry()
    
    # Get all agencies
    all_agencies = await registry.query_agencies(limit=1000)
    
    for agency in all_agencies:
        # Re-add to generate embeddings
        await registry.add_agency(agency, agency.endpoint, agency.tags)
```

## Security Notes

1. **API Keys**: Never commit API keys to version control
2. **Rate Limits**: Implement rate limiting for production
3. **Error Handling**: System continues without embeddings if generation fails
4. **Data Privacy**: Be aware that text is sent to external APIs for embedding 