# MongoDB Atlas Search Index Setup

This guide explains how to set up Atlas Search and Vector Search indexes for the IATP registry collections.

## Overview

Each collection requires two types of indexes:
1. **Atlas Search Index** - For text-based keyword search
2. **Vector Search Index** - For semantic similarity search using embeddings

## Index Naming Convention

All index names include the environment suffix:
- `utility_agency_atlas_search_{env}`
- `utility_agency_vector_search_{env}`
- `mcp_server_atlas_search_{env}`
- `mcp_server_vector_search_{env}`

Where `{env}` is one of: `test`, `staging`, or `prod`

## Collections

Based on your environment (ENV variable), the collections are:
- `iatp-utility-agency-registry-{env}` (where env = test/staging/prod)
- `iatp-mcp-server-registry-{env}`

## Creating Indexes in MongoDB Atlas

### Method 1: Atlas UI

1. Go to your MongoDB Atlas cluster
2. Click on "Search" in the left sidebar
3. Click "Create Search Index"
4. Choose your database (`iatp`)
5. For each collection, create both indexes:

#### Utility Agency Registry - Atlas Search Index
- Collection: `iatp-utility-agency-registry-{env}`
- Index Name: `utility_agency_atlas_search_{env}`
- Use the JSON definition from `atlas_search_indexes.json` under `utility_agency_indexes.atlas_search`

#### Utility Agency Registry - Vector Search Index
- Collection: `iatp-utility-agency-registry-{env}`
- Index Name: `utility_agency_vector_search_{env}`
- Use the JSON definition from `atlas_search_indexes.json` under `utility_agency_indexes.vector_search`

#### MCP Server Registry - Atlas Search Index
- Collection: `iatp-mcp-server-registry-{env}`
- Index Name: `mcp_server_atlas_search_{env}`
- Use the JSON definition from `atlas_search_indexes.json` under `mcp_server_indexes.atlas_search`

#### MCP Server Registry - Vector Search Index
- Collection: `iatp-mcp-server-registry-{env}`
- Index Name: `mcp_server_vector_search_{env}`
- Use the JSON definition from `atlas_search_indexes.json` under `mcp_server_indexes.vector_search`

### Method 2: Atlas Admin API

```bash
# Set your Atlas API credentials
export ATLAS_PUBLIC_KEY="your_public_key"
export ATLAS_PRIVATE_KEY="your_private_key"
export ATLAS_PROJECT_ID="your_project_id"
export ATLAS_CLUSTER_NAME="your_cluster_name"
export ENV="test"  # or staging, prod

# Create indexes using curl (example for one index)
# Note: You'll need to modify the JSON to replace <env> with your actual environment
curl --user "${ATLAS_PUBLIC_KEY}:${ATLAS_PRIVATE_KEY}" --digest \
  --header "Content-Type: application/json" \
  --request POST "https://cloud.mongodb.com/api/atlas/v1.0/groups/${ATLAS_PROJECT_ID}/clusters/${ATLAS_CLUSTER_NAME}/fts/indexes" \
  --data @atlas_search_indexes.json
```

## Example: Creating Indexes for Test Environment

For the `test` environment, you would create:
- `utility_agency_atlas_search_test`
- `utility_agency_vector_search_test`
- `mcp_server_atlas_search_test`
- `mcp_server_vector_search_test`

## Vector Embeddings

The vector search indexes expect the following embedding fields:
- `description_embedding` - 1536-dimensional vector for description text
- `tags_embedding` - 1536-dimensional vector for tags (utility agencies)
- `capabilities_embedding` - 1536-dimensional vector for capabilities (MCP servers)

### Generating Embeddings

To use vector search, you need to generate embeddings when adding documents. Example using OpenAI:

```python
import openai

def generate_embedding(text: str) -> List[float]:
    response = openai.Embedding.create(
        model="text-embedding-ada-002",
        input=text
    )
    return response['data'][0]['embedding']
```

## Using the Indexes

The code automatically uses the correct index name based on your ENV variable:

### Atlas Search (Text Search)
```python
# The atlas_search method automatically uses the correct index name
results = await registry.atlas_search("weather forecast")
```

### Vector Search (Semantic Search)
```python
# The vector_search method automatically uses the correct index name
query_embedding = generate_embedding("meteorological predictions")
results = await registry.vector_search(query_embedding)
```

## Important Notes

1. **Index Status**: After creating indexes, they may take a few minutes to build
2. **Environment Variable**: Make sure your `ENV` environment variable is set correctly
3. **Embedding Dimensions**: The vector indexes are configured for 1536 dimensions (OpenAI's ada-002 model)
4. **Similarity Metric**: Using cosine similarity for vector comparison
5. **Filters**: The vector indexes include `is_active` as a filter field for efficient filtering

## Monitoring

You can monitor index status and usage in the Atlas UI under:
- Search > Index Status
- Search > Query Analytics 