# LLM Threat Hunt

Semantic search for security logs using LLM and RAG.

## Setup

```bash
# Start database
docker compose up -d

# Install
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# Download test data
python scripts/download_mordor.py
```

## Usage

```bash
# Ingest logs
hunt ingest data/

# Check status
hunt status

# Reset database (if needed)
hunt reset
```

## Connect to Database

```bash
docker exec -it threat-hunt-db psql -U threat -d threat_hunt
```

## Requirements

- Python 3.10+
- Docker
