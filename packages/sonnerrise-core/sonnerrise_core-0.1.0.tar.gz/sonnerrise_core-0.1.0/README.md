# sonnerrise-core

Core module for the Sonnerrise suite - Suno track management and promotion planning.

## Features

- **YAML Configuration**: Load configuration from YAML files with environment variable overrides
- **Database Abstraction**: Plugin-based database interface supporting MySQL and SQLite
- **Base Models**: SQLAlchemy base models with common fields and timestamps

## Installation

```bash
pip install sonnerrise-core
```

## Usage

### Configuration

```python
from sonnerrise_core import load_config

# Load from default locations or environment
config = load_config()

# Load from specific file
config = load_config("path/to/config.yaml")
```

### Environment Variables

- `SONNERRISE_DB_PLUGIN`: Database plugin (mysql, sqlite)
- `SONNERRISE_DB_HOST`: Database host
- `SONNERRISE_DB_PORT`: Database port
- `SONNERRISE_DB_USER`: Database user
- `SONNERRISE_DB_PASSWORD`: Database password
- `SONNERRISE_DB_NAME`: Database name
- `SONNERRISE_WEB_HOST`: Web server host
- `SONNERRISE_WEB_PORT`: Web server port
- `SONNERRISE_WEB_DEBUG`: Enable debug mode
- `SONNERRISE_WEB_SECRET_KEY`: Flask secret key

### Database

```python
from sonnerrise_core import load_config, get_database

config = load_config()
db = get_database(config)

# Test connection
if db.test_connection():
    print("Connected!")

# Use sessions
with db.session() as session:
    # Perform database operations
    pass
```

### CLI

```bash
# Create default configuration
sonnerrise-core init-config

# Test database connection
sonnerrise-core test-db

# Initialize database tables
sonnerrise-core init-db

# Show current configuration
sonnerrise-core show-config
```

## Configuration File Example

```yaml
database:
  plugin: mysql
  host: localhost
  port: 3306
  user: sonnerrise
  password: secret
  database: sonnerrise
  charset: utf8mb4

web:
  host: 0.0.0.0
  port: 5000
  debug: false
  secret_key: change-me-in-production
```
