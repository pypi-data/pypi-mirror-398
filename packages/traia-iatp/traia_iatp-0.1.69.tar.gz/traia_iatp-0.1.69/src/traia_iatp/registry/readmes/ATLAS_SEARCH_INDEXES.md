# MongoDB Atlas Search Indexes for IATP Registry

This document describes the MongoDB Atlas Search and Vector Search indexes required for the IATP utility agent registry.

## Prerequisites

1. MongoDB Atlas cluster (M10 or higher for Vector Search)
2. Access to Atlas UI or Atlas Admin API
3. OpenAI API key for generating embeddings (set as `OPENAI_API_KEY` environment variable)

## Index Configuration

### 1. Utility Agent Atlas Search Index

Create this index on the `utility_agents` collection (or `utility_agents_test`/`utility_agents_prod` based on environment).

**Index Name**: `utility_agent_atlas_search` (or `utility_agent_atlas_search_test`/`utility_agent_atlas_search_prod`)

**Index Definition**:
```json
{
  "mappings": {
    "dynamic": false,
    "fields": {
      "name": {
        "type": "string",
        "analyzer": "lucene.standard"
      },
      "description": {
        "type": "string",
        "analyzer": "lucene.standard"
      },
      "tags": {
        "type": "string",
        "analyzer": "lucene.standard"
      },
      "capabilities": {
        "type": "string",
        "analyzer": "lucene.standard"
      },
      "search_text": {
        "type": "string",
        "analyzer": "lucene.standard"
      },
      "skills": {
        "type": "document",
        "fields": {
          "name": {
            "type": "string",
            "analyzer": "lucene.standard"
          },
          "description": {
            "type": "string",
            "analyzer": "lucene.standard"
          },
          "examples": {
            "type": "string",
            "analyzer": "lucene.standard"
          }
        }
      },
      "agent_card": {
        "type": "document",
        "fields": {
          "name": {
            "type": "string",
            "analyzer": "lucene.standard"
          },
          "description": {
            "type": "string",
            "analyzer": "lucene.standard"
          }
        }
      }
    }
  }
}
```

### 2. Utility Agent Vector Search Index

Create this index for semantic search using embeddings.

**Index Name**: `utility_agent_vector_search` (or `utility_agent_vector_search_test`/`utility_agent_vector_search_prod`)

**Index Definition**:
```json
{
  "type": "vectorSearch",
  "fields": [
    {
      "type": "vector",
      "path": "embeddings.search_text",
      "numDimensions": 1536,
      "similarity": "cosine"
    },
    {
      "type": "vector",
      "path": "embeddings.description",
      "numDimensions": 1536,
      "similarity": "cosine"
    },
    {
      "type": "vector",
      "path": "embeddings.capabilities",
      "numDimensions": 1536,
      "similarity": "cosine"
    },
    {
      "type": "vector",
      "path": "embeddings.skills",
      "numDimensions": 1536,
      "similarity": "cosine"
    },
    {
      "type": "filter",
      "path": "is_active"
    },
    {
      "type": "filter",
      "path": "tags"
    }
  ]
}
```

### 3. MCP Server Atlas Search Index

Create this index on the `mcp_servers` collection.

**Index Name**: `mcp_server_atlas_search` (or `mcp_server_atlas_search_test`/`mcp_server_atlas_search_prod`)

**Index Definition**:
```json
{
  "mappings": {
    "dynamic": false,
    "fields": {
      "name": {
        "type": "string",
        "analyzer": "lucene.standard"
      },
      "description": {
        "type": "string",
        "analyzer": "lucene.standard"
      },
      "capabilities": {
        "type": "string",
        "analyzer": "lucene.standard"
      }
    }
  }
}
```

### 4. MCP Server Vector Search Index

**Index Name**: `mcp_server_vector_search` (or `mcp_server_vector_search_test`/`mcp_server_vector_search_prod`)

**Index Definition**:
```json
{
  "type": "vectorSearch",
  "fields": [
    {
      "type": "vector",
      "path": "description_embedding",
      "numDimensions": 1536,
      "similarity": "cosine"
    },
    {
      "type": "vector",
      "path": "capabilities_embedding",
      "numDimensions": 1536,
      "similarity": "cosine"
    },
    {
      "type": "filter",
      "path": "is_active"
    }
  ]
}
```

## Creating Indexes

### Via Atlas UI

1. Navigate to your cluster in MongoDB Atlas
2. Go to "Search" tab
3. Click "Create Search Index"
4. Choose "JSON Editor"
5. Select the appropriate database and collection
6. Paste the index definition
7. Name the index according to the pattern above
8. Click "Create Search Index"

### Via Atlas Admin API

```bash
# Set your API credentials
export ATLAS_PUBLIC_KEY="your-public-key"
export ATLAS_PRIVATE_KEY="your-private-key"
export ATLAS_PROJECT_ID="your-project-id"
export ATLAS_CLUSTER_NAME="your-cluster-name"

# Create utility agent Atlas Search index
curl --user "${ATLAS_PUBLIC_KEY}:${ATLAS_PRIVATE_KEY}" --digest \
  --header "Content-Type: application/json" \
  --request POST "https://cloud.mongodb.com/api/atlas/v2/groups/${ATLAS_PROJECT_ID}/clusters/${ATLAS_CLUSTER_NAME}/search/indexes" \
  --data '{
    "collectionName": "utility_agents",
    "database": "iatp",
    "name": "utility_agent_atlas_search",
    "mappings": { ... }
  }'
```

## Index Naming Convention

The indexes follow environment-specific naming:
- Test environment: `*_test` suffix
- Production environment: `*_prod` suffix
- Default/development: No suffix

## Required Embedding Dimensions

All vector fields use OpenAI's `text-embedding-3-small` model which produces 1536-dimensional vectors.

## Monitoring Index Creation

Index creation can take several minutes. Monitor progress:
1. In Atlas UI: Check the "Search" tab for index status
2. Via API: Query the index endpoint to check status

## Testing Indexes

After creation, test the indexes using the registry methods:

```python
# Test Atlas Search
results = await registry.atlas_search("trading hyperliquid")

# Test Vector Search
results = await registry.vector_search_text("find me a trading agent for crypto")
```

## Maintenance

- Indexes are automatically maintained by Atlas
- No manual optimization required
- Monitor index performance in Atlas UI under "Search Metrics" 