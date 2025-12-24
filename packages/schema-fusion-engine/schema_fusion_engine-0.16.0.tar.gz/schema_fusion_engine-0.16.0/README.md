# SchemaFusion Engine

A middleware implementation of the **EasyBDI 2.0** architecture, focusing on Data Virtualization and Federation. SchemaFusion provides a headless interface for orchestrating distributed queries across heterogeneous data sources using Trino as the query engine.

## Architecture

SchemaFusion acts as a middleware layer that:

- **Federates** queries across multiple data sources (PostgreSQL, MongoDB, CSV files, etc.)
- **Virtualizes** data access through Trino's distributed query engine
- **Orchestrates** query planning and execution via Python-based FastAPI middleware
- **Manages** configuration through a Typer-based CLI

See [Architecture Documentation](docs/architecture.md) for detailed architecture diagrams and component descriptions.

## Components

### Infrastructure (Docker)

The project uses Docker Compose to orchestrate:

- **Trino** (port 8080): Distributed query engine
- **PostgreSQL** (port 5432): Relational data source
- **MongoDB** (port 27017): NoSQL data source
- **Kafka** (port 9092): Streaming data source
- **CSV Files**: CSV files imported into PostgreSQL (example files in `docker/trino/csv-data/`)
- **Google Sheets**: Query Google Sheets as tables (requires OAuth2 credentials)
- **Redis** (port 6379): Caching layer
- **Gateway** (port 80): Single entrypoint reverse proxy that serves the UI and forwards `/api` requests to FastAPI

### Middleware (Python)

- **FastAPI Application** (`src/main.py`): Headless REST API interface
- **Typer CLI** (`src/cli.py`): Configuration management interface
- **Verification Script** (`scripts/check_fusion.py`): Validates Trino connectivity and catalog visibility

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- pip

### Setup

1. **Start the infrastructure:**

   ```bash
   docker compose up -d
   ```

  Once the stack is healthy, the gateway exposes the UI at `http://localhost/` and proxies all `/api/*` calls to FastAPI, so you no longer need to remember separate ports in the browser. (The UI container remains reachable on `http://localhost:3000/` if you prefer to bypass the proxy while developing.)

2. **Install Python dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Verify connectivity:**

   ```bash
   python scripts/check_fusion.py
   ```

   This script connects to Trino and runs `SHOW CATALOGS` to verify that all configured connectors (PostgreSQL, MongoDB, Kafka, etc.) are visible.

4. **Start the FastAPI server:**

   ```bash
   uvicorn src.main:app --reload
   ```

   The API will be available at `http://localhost:8000`
   - Interactive API docs: `http://localhost:8000/docs`
   - OpenAPI schema: `http://localhost:8000/openapi.json`

5. **Use the CLI:**

   ```bash
   python -m src.cli check
   python -m src.cli version
   ```

## Project Structure

```
schema-fusion-engine/
├── docker/
├── docker-compose.yml      # Infrastructure orchestration
│   └── trino/
│       ├── catalog/
│       │   ├── postgres.properties # Trino PostgreSQL connector config
│       │   ├── mongo.properties    # Trino MongoDB connector config
│       │   └── csv.properties      # Trino CSV connector config
│       └── csv-data/              # CSV files directory
├── src/
│   ├── main.py                 # FastAPI headless API
│   ├── cli.py                  # Typer CLI configuration manager
│   ├── api/                    # API modules
│   ├── cli/                    # CLI modules
│   └── core/                   # Core business logic
├── docs/                       # Documentation
│   └── architecture.md         # Architecture diagrams and design
├── scripts/
│   └── check_fusion.py         # Trino connectivity verification
├── tests/                      # Test suite
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## API Reference

### Query Execution

Execute SQL queries across federated data sources:

```bash
curl -X POST "http://localhost:8000/fusion/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SELECT * FROM postgres.public.users LIMIT 10",
    "catalog": "postgres",
    "schema": "public",
    "max_rows": 100
  }'
```

**Response:**
```json
{
  "query": "SELECT * FROM postgres.public.users LIMIT 10",
  "columns": ["id", "name", "email"],
  "rows": [[1, "Alice", "alice@example.com"], [2, "Bob", "bob@example.com"]],
  "row_count": 2,
  "execution_time_ms": 45.23,
  "error": null
}
```

### Schema Discovery

Discover available catalogs, schemas, and tables:

```bash
# List catalogs
curl "http://localhost:8000/fusion/catalogs"

# List schemas
curl "http://localhost:8000/fusion/catalogs/postgres/schemas"

# List tables
curl "http://localhost:8000/fusion/catalogs/postgres/schemas/public/tables"

# Get table info
curl "http://localhost:8000/fusion/catalogs/postgres/schemas/public/tables/users"
```

### Schema Matching

Automatically match columns between tables:

```bash
curl -X POST "http://localhost:8000/fusion/match" \
  -H "Content-Type: application/json" \
  -d '{
    "source_catalog": "postgres",
    "source_schema": "public",
    "source_table": "users",
    "target_catalog": "mongo",
    "target_schema": "testdb",
    "target_table": "customers",
    "threshold": 0.8
  }'
```

**Response:**
```json
{
  "source": {
    "catalog": "postgres",
    "schema": "public",
    "table": "users",
    "columns": ["id", "name", "email"]
  },
  "target": {
    "catalog": "mongo",
    "schema": "testdb",
    "table": "customers",
    "columns": ["_id", "name", "email"]
  },
  "matches": [
    {"source_col": "name", "target_col": "name", "confidence": 1.0},
    {"source_col": "email", "target_col": "email", "confidence": 1.0}
  ],
  "match_count": 2,
  "threshold": 0.8
}
```

### Fusion Views

Create federated views that combine data from multiple sources:

```bash
curl -X POST "http://localhost:8000/fusion/create-view" \
  -H "Content-Type: application/json" \
  -d '{
    "view_name": "global_customers",
    "source_a": {"catalog": "postgres", "schema": "public", "table": "users"},
    "source_b": {"catalog": "mongo", "schema": "testdb", "table": "customers"},
    "matches": [
      {"source_col": "name", "target_col": "name", "confidence": 1.0},
      {"source_col": "email", "target_col": "email", "confidence": 1.0}
    ],
    "join_key_a": "id",
    "join_key_b": "_id"
  }'
```

**Response:**
```json
{
  "status": "success",
  "message": "View created successfully",
  "view_name": "global_customers",
  "sql": "CREATE OR REPLACE VIEW memory.default.global_customers AS ..."
}
```

**List views:**
```bash
curl "http://localhost:8000/fusion/views?catalog=memory&schema=default"
```

**Delete view:**
```bash
curl -X DELETE "http://localhost:8000/fusion/views/global_customers?catalog=memory&schema=default"
```

### Multi-Source Fusion (3+ Sources)

Create fusion views that combine data from 3 or more sources:

```bash
curl -X POST "http://localhost:8000/fusion/create-multi-view" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "view_name": "unified_customers",
    "sources": [
      {"catalog": "postgres", "schema": "public", "table": "users", "alias": "p"},
      {"catalog": "mongo", "schema": "testdb", "table": "customers", "alias": "m"},
      {"catalog": "postgres", "schema": "public", "table": "clients", "alias": "c"}
    ],
    "matches": [
      {
        "global": "customer_id",
        "mappings": [
          {"source": "p", "column": "id"},
          {"source": "m", "column": "_id"},
          {"source": "c", "column": "client_id"}
        ]
      },
      {
        "global": "name",
        "mappings": [
          {"source": "p", "column": "name"},
          {"source": "m", "column": "full_name"},
          {"source": "c", "column": "name"}
        ]
      }
    ],
    "fusion_type": "join",
    "join_keys": [
      {"source": "p", "column": "id"},
      {"source": "m", "column": "_id"},
      {"source": "c", "column": "client_id"}
    ]
  }'
```

**Response:**
```json
{
  "status": "success",
  "message": "View created successfully",
  "view_name": "unified_customers",
  "sql": "CREATE OR REPLACE VIEW memory.default.unified_customers AS ..."
}
```

For UNION ALL (horizontal partitioning):
```bash
curl -X POST "http://localhost:8000/fusion/create-multi-view" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "view_name": "all_customers",
    "sources": [
      {"catalog": "postgres", "schema": "public", "table": "customers", "alias": "p"},
      {"catalog": "mongo", "schema": "testdb", "table": "clients", "alias": "m"}
    ],
    "matches": [
      {
        "global": "id",
        "mappings": [
          {"source": "p", "column": "id"},
          {"source": "m", "column": "_id"}
        ]
      }
    ],
    "fusion_type": "union",
    "enable_type_coercion": true
  }'
```

See [Multi-Source Fusion Guide](docs/multi-source-fusion.md) for detailed documentation.

### Health Check

```bash
curl "http://localhost:8000/health"
```

## Configuration

### Trino Connectors

Trino connectors are configured in `docker/trino/catalog/`:

- **PostgreSQL**: Connects to `postgres:5432` using JDBC
- **MongoDB**: Connects to `mongo:27017` using MongoDB native protocol
- **Kafka**: Connects to `kafka:29092` for streaming data (see [Kafka Setup](docs/kafka-setup.md))
- **Google Sheets**: Query Google Sheets as tables (requires OAuth2, see [Google Sheets Setup](docs/google-sheets-setup.md))
- **CSV**: Import CSV files into PostgreSQL (see [CSV Support](docs/csv-support-options.md))

### Environment Variables

Configuration is managed via environment variables or a `.env` file. See [Configuration Guide](docs/configuration.md) for all available options.

**Quick reference:**
- `TRINO_HOST` - Trino coordinator host (default: `localhost`)
- `TRINO_PORT` - Trino coordinator port (default: `8080`)
- `TRINO_USER` - Trino user (default: `schemafusion`)
- `LOG_LEVEL` - Logging level (default: `INFO`)
- `LOG_FORMAT` - Log format: `text` or `json` (default: `text`)
- `VIEW_CATALOG` - Catalog for fusion views (default: `memory`)
- `VIEW_SCHEMA` - Schema for fusion views (default: `default`)

## Development

### Running Tests

```bash
pytest tests/
pytest tests/ --cov=src --cov-report=html
```

### Code Quality

```bash
# Linting
ruff check src/
ruff check src/ --fix

# Formatting
black src/ tests/

# Type checking
mypy src/

# Pre-commit hooks (runs automatically on commit)
pre-commit run --all-files
```

## Documentation

- [Architecture](docs/architecture.md) - System architecture and design
- [Deployment Guide](docs/deployment.md) - Production deployment instructions
- [Configuration](docs/configuration.md) - Environment variables and settings
- [Multi-Source Fusion](docs/multi-source-fusion.md) - Guide for 3+ source fusion views
- [Kafka Setup](docs/kafka-setup.md) - Kafka connector configuration
- [Google Sheets Setup](docs/google-sheets-setup.md) - Google Sheets connector setup
- [CSV Support](docs/csv-support-options.md) - CSV file import options
- [Troubleshooting](docs/troubleshooting.md) - Common issues and solutions
- [Security Guide](docs/security.md) - Security considerations and best practices
- [Release Guide](docs/release.md) - How to create releases
- [Monitoring Setup](docs/monitoring-setup.md) - Prometheus, Grafana, and AlertManager setup

## References

- [Trino Documentation](https://trino.io/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [EasyBDI 2.0 Architecture](https://github.com/easybdi/easybdi)
