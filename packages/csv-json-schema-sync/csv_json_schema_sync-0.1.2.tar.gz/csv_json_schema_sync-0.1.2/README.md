# csv-json-schema-sync

A CLI tool for data engineers to manage continuously evolving CSV/JSON schemas.

## Features

- **Infer Schema**: Auto-generate JSON schema from CSV/JSON data files.
- **Validate Data**: Validate data files against a JSON schema.
- **Compare Schemas**: Detect changes between two schemas (new/missing columns).

## Installation

```bash
pip install csv-json-schema-sync
```

## Usage

### Infer Schema

```bash
schema-sync infer users.csv > schema.json
```

### Validate Data

```bash
schema-sync validate users.csv schema.json
```

## Development

```bash
pip install -e ".[dev]"
pytest
```
