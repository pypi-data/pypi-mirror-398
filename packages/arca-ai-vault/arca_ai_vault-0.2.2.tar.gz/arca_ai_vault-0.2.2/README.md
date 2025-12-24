# Arca Python SDK

Python SDK for [Arca](https://arca.build) - A private data vault for personal AI assistants.

## Overview

Arca provides two main APIs:
- **Tables API**: Store structured data with SQL-like queries (powered by DuckDB and Parquet)
- **Vectors API**: Store and search unstructured data semantically (powered by vector embeddings)

## Installation

```bash
pip install arca-ai-vault
```

Or install from GitHub:

```bash
pip install git+https://github.com/xbora/arca-python-sdk.git
```

Or install from source:

```bash
git clone https://github.com/xbora/arca-python-sdk.git
cd arca-python-sdk
pip install -e .
```

## Quick Start

### Authentication

Get your API key from [https://arca.build](https://arca.build)

```python
from arca import ArcaTableClient, ArcaVectorClient

# Initialize clients
table_client = ArcaTableClient(user_id="your-api-key")
vector_client = ArcaVectorClient(user_id="your-api-key")
```

### Tables API - Store Structured Data

```python
from arca import ArcaTableClient, TableColumn, SkillMetadata

client = ArcaTableClient(user_id="your-api-key")

# Create a table and insert data
response = client.upsert(
    table_name="meals",
    columns=[
        TableColumn("food", "VARCHAR"),
        TableColumn("calories", "INTEGER"),
        TableColumn("protein", "DOUBLE")
    ],
    data={
        "food": "Grilled Chicken",
        "calories": 165,
        "protein": 31.0
    },
    skill=SkillMetadata(
        description="Tracks daily meals and nutrition",
        examples=["SELECT * FROM meals WHERE calories > 200"]
    )
)

# Query data
results = client.query(
    table_name="meals",
    filters={"daysAgo": 7},
    order_by="calories DESC",
    limit=10
)

# Add new columns to existing table
client.alter_schema(
    table_name="meals",
    add_columns=[
        TableColumn("meal_type", "VARCHAR"),
        TableColumn("rating", "INTEGER")
    ],
    default_values={
        "meal_type": "snack",
        "rating": 3
    }
)

# List all tables
tables = client.list_tables()

# Get table schemas
schemas = client.get_schemas()
```

### Vectors API - Semantic Search

```python
from arca import ArcaVectorClient, VectorSkillMetadata, MetadataField

client = ArcaVectorClient(user_id="your-api-key")

# Add entries with automatic embedding generation
response = client.add(
    table_name="journal_entries",
    text="Today was incredibly productive. Finished the big project ahead of schedule.",
    metadata={
        "category": "personal",
        "mood": "positive",
        "date": "2024-01-15"
    },
    skill=VectorSkillMetadata(
        description="Personal journal entries with mood tracking",
        metadata_fields=[
            MetadataField("category", "string", "Entry category", ["personal", "work", "health"]),
            MetadataField("mood", "string", "Emotional state", ["positive", "neutral", "negative"])
        ],
        search_examples=["Find days when I felt accomplished"],
        filter_examples=["category = 'personal' AND mood = 'positive'"]
    )
)

# Search semantically
results = client.search(
    table_name="journal_entries",
    query="productive and successful days",
    limit=5,
    filter="category = 'personal'"
)

# List all vector tables
tables = client.list_tables()
```

### Combined Skills - Get All Skills at Once

```python
from arca import get_all_skills

# Fetch all skills (both table and vector) in one API call
all_skills = get_all_skills(user_id="your-api-key")

# Returns:
# {
#   "success": true,
#   "userId": "user_01...",
#   "skills": [
#     {"tableName": "favorites", "skill": "...", "type": "vector", "success": true},
#     {"tableName": "meals", "skill": "...", "type": "table", "success": true}
#   ],
#   "tableSkillCount": 2,
#   "vectorSkillCount": 1
# }

print(f"Total skills: {len(all_skills['skills'])}")
print(f"Tables: {all_skills['tableSkillCount']}, Vectors: {all_skills['vectorSkillCount']}")

# Filter by type if needed
table_skills = [s for s in all_skills['skills'] if s['type'] == 'table']
vector_skills = [s for s in all_skills['skills'] if s['type'] == 'vector']
```

This is especially useful for AI assistants that need complete context about all available data sources.

## API Reference

### ArcaTableClient

#### `__init__(user_id: str, base_url: str = "https://arca.build")`
Initialize the table client with your API key.

#### `upsert(table_name, data, columns=None, skill=None)`
Create or append to a table. This is the recommended method for inserting data.

**Parameters:**
- `table_name` (str): Name of the table
- `data` (dict): Dictionary of data to insert
- `columns` (list[TableColumn], optional): Column definitions (required on first insert)
- `skill` (SkillMetadata, optional): Metadata to help AI understand the table

#### `query(table_name, query=None, filters=None, limit=None, offset=None, order_by=None, select=None, group_by=None, having=None)`
Query a table with filters and aggregations.

**Parameters:**
- `table_name` (str): Name of the table to query
- `query` (str, optional): Raw SQL WHERE clause for comparisons (e.g., `"calories > 500"`, `"protein > 20 AND carbs < 50"`)
- `filters` (dict, optional): Dictionary of filters (e.g., `{"daysAgo": 7}`)
- `limit` (int, optional): Maximum number of results
- `offset` (int, optional): Number of results to skip
- `order_by` (str, optional): Column to order by (e.g., `"created_at DESC"`)
- `select` (list[str], optional): List of columns to select
- `group_by` (str, optional): Column to group by
- `having` (str, optional): HAVING clause for aggregations

**Examples:**
```python
# Query with comparison operators
results = client.query(
    table_name="meals",
    query="calories > 500",
    order_by="calories DESC"
)

# Query with time-based filters
results = client.query(
    table_name="meals",
    filters={"daysAgo": 7},
    limit=10
)

# Combine custom WHERE clause with other filters
results = client.query(
    table_name="meals",
    query="protein > 20",
    filters={"daysAgo": 30},
    limit=5
)
```

#### `update(table_name, data, where=None)`
Update rows in a table.

**Parameters:**
- `table_name` (str): Name of the table
- `data` (dict): Dictionary of column:value pairs to update
- `where` (dict, optional): Dictionary specifying which rows to update (e.g., `{"id": 5}`)

**Examples:**
```python
# Update specific row by ID
result = client.update(
    table_name="meals",
    data={"calories": 910, "meal_type": "dinner"},
    where={"id": 5}
)

# Update row by exact column match
result = client.update(
    table_name="meals",
    data={"calories": 170},
    where={"food": "Grilled Chicken Breast"}
)
```

#### `alter_schema(table_name, add_columns, default_values=None)`
Add new columns to an existing table while preserving all existing data.

**Parameters:**
- `table_name` (str): Name of the table to alter
- `add_columns` (list[TableColumn]): List of new columns to add
- `default_values` (dict, optional): Dictionary mapping column names to default values for existing rows

**Returns:**
Dictionary with success status, message, tableName, changes summary, and newSchema.

**Examples:**
```python
# Add new columns with default values
result = client.alter_schema(
    table_name="meals",
    add_columns=[
        TableColumn("category", "VARCHAR"),
        TableColumn("rating", "INTEGER"),
        TableColumn("is_favorite", "BOOLEAN")
    ],
    default_values={
        "category": "General",
        "rating": 0,
        "is_favorite": False
    }
)

# Add nullable columns without defaults
result = client.alter_schema(
    table_name="meals",
    add_columns=[
        TableColumn("notes", "VARCHAR", nullable=True)
    ]
)
```

**Note:** This operation preserves all existing data and only adds new columns. You cannot remove or modify existing columns.

#### `delete(table_name)`
Delete an entire table.

#### `list_tables()`
List all tables for the authenticated user.

#### `get_schemas()`
Get schemas for all tables.

#### `get_skill(table_name)`
Get the SKILL.md file for a specific table.

#### `update_skill(table_name, skill)`
Update the SKILL.md file for a table.

#### `get_all_skills()`
Get all table skills in one request.

#### `export(table_name)`
Export a table as a Parquet file (returns bytes).

### ArcaVectorClient

#### `__init__(user_id: str, base_url: str = "https://arca.build")`
Initialize the vector client with your API key.

#### `add(table_name, text, metadata=None, generate_embedding=True, embedding=None, skill=None)`
Add a vector entry with automatic embedding generation.

**Parameters:**
- `table_name` (str): Name of the vector table
- `text` (str): Text content to embed and store
- `metadata` (dict, optional): Optional metadata dictionary
- `generate_embedding` (bool): Whether to auto-generate embedding (default: True)
- `embedding` (list[float], optional): Pre-computed embedding vector
- `skill` (VectorSkillMetadata, optional): Metadata to help AI understand the table

#### `search(table_name, query, limit=5, generate_embedding=True, embedding=None, filter=None)`
Search vectors semantically.

**Parameters:**
- `table_name` (str): Name of the vector table to search
- `query` (str): Search query text
- `limit` (int): Maximum number of results (default: 5)
- `generate_embedding` (bool): Whether to auto-generate query embedding (default: True)
- `embedding` (list[float], optional): Pre-computed query embedding vector
- `filter` (str, optional): SQL-like filter expression (e.g., `"category = 'personal'"`)

#### `delete(table_name)`
Delete an entire vector table.

#### `list_tables()`
List all vector tables for the authenticated user.

#### `get_skill(table_name)`
Get the SKILL.md file for a specific vector table.

#### `update_skill(table_name, skill)`
Update the SKILL.md file for a vector table.

#### `get_all_skills()`
Get all vector skills in one request.

#### `export(table_name)`
Export a vector table as a CSV file (returns bytes).

### get_all_skills()

#### `get_all_skills(user_id: str, base_url: str = "https://arca.build")`
Get all skills (both table and vector) in one request. This is a standalone function (not a client method).

**Parameters:**
- `user_id` (str): Your Arca API key
- `base_url` (str): Base URL for Arca API (default: "https://arca.build")

**Returns:**
Dictionary with `success`, `userId`, `skills` array (each skill has `tableName`, `skill`, `type`, `success`), `tableSkillCount`, and `vectorSkillCount`.

**Example:**
```python
from arca import get_all_skills

all_skills = get_all_skills(user_id="your-api-key")
# Access skills: all_skills['skills']
# Each skill has: tableName, skill, type ('table' or 'vector'), success
```

## Data Models

### TableColumn

Represents a column in an Arca table.

```python
TableColumn(name: str, type: str, nullable: bool = True)
```

**Supported types:** `VARCHAR`, `INTEGER`, `BIGINT`, `DOUBLE`, `BOOLEAN`, `TIMESTAMP`, `DATE`, `JSON`

### SkillMetadata

Metadata for table skills - helps AI understand how to use the table.

```python
SkillMetadata(
    description: str = None,
    examples: list[str] = None,
    relationships: list[str] = None,
    notes: str = None
)
```

### VectorSkillMetadata

Metadata for vector skills - helps AI understand how to search the vector table.

```python
VectorSkillMetadata(
    description: str = None,
    metadata_fields: list[MetadataField] = None,
    search_examples: list[str] = None,
    filter_examples: list[str] = None,
    notes: str = None
)
```

### MetadataField

Metadata field definition for vector tables.

```python
MetadataField(
    name: str,
    type: str,
    description: str,
    examples: list[str] = None
)
```

## Error Handling

The SDK provides custom exceptions for different error scenarios:

```python
from arca import ArcaAPIError, ArcaAuthError, ArcaValidationError

try:
    response = client.query(table_name="meals")
except ArcaAuthError as e:
    print(f"Authentication failed: {e}")
except ArcaAPIError as e:
    print(f"API error: {e.message} (status: {e.status_code})")
except ArcaValidationError as e:
    print(f"Validation error: {e}")
```

## Examples

See the [examples/](examples/) directory for more comprehensive examples:
- `table_examples.py` - Tables API usage examples
- `vector_examples.py` - Vectors API usage examples

## Development

Install development dependencies:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

## License

MIT License

## Links

- [Documentation](https://docs.arca.build)
- [API Reference](https://docs.arca.build/api)
- [GitHub Repository](https://github.com/xbora/arca-python-sdk)
- [Arca Homepage](https://arca.build)
