# ORQ CLI

Command line interface for the orq.ai LLM Ops platform.

## Installation

```bash
pip install orq-cli
```

## Quick Start

### Configure API Key

Set your API key using one of these methods:

```bash
# Using the CLI
orq config set api_key YOUR_API_KEY

# Using environment variable
export ORQ_API_KEY=YOUR_API_KEY
```

### Basic Usage

```bash
# List deployments
orq deployments list

# Invoke a deployment with a message
orq invoke my-deployment -m "Hello, world!"

# Invoke with variables (for prompt templates)
orq invoke my-deployment -v firstname=John -v city=Paris

# Combine variables and message
orq invoke my-deployment -v customer=John -m "Help me with my order"

# Stream a response
orq invoke my-deployment -v topic=AI --stream

# Interactive mode
orq --interactive
```

## Passing Variables

When your deployment has prompt templates with placeholders like `{{firstname}}` or `{{city}}`, pass them using `-v` or `--var`:

```bash
# Using --var (recommended)
orq invoke customer-service -v firstname=John -v city=Paris -v language=English

# Multiple variables
orq deployments invoke my-key -v name=Alice -v topic="machine learning" -v format=markdown

# Using JSON (alternative)
orq deployments invoke my-key --inputs '{"firstname": "John", "city": "Paris"}'
```

## Commands

### Deployments

```bash
orq deployments list                              # List all deployments
orq deployments invoke KEY -v name=value          # Invoke with variables
orq deployments stream KEY -v name=value          # Stream with variables
orq deployments get-config KEY                    # Get deployment configuration
```

### Datasets

```bash
orq datasets list                       # List datasets
orq datasets create --name "My Dataset" # Create a dataset
orq datasets get DATASET_ID             # Get dataset details
orq datasets delete DATASET_ID          # Delete a dataset

# Datapoints
orq datasets datapoints list DATASET_ID
orq datasets datapoints create DATASET_ID --inputs '{"key": "value"}'
```

### Files

```bash
orq files list                          # List files
orq files upload path/to/file.txt       # Upload a file
orq files get FILE_ID                   # Get file details
orq files delete FILE_ID                # Delete a file
```

### Knowledge Bases

```bash
orq knowledge list                      # List knowledge bases
orq knowledge search KB_ID --query "search term"
orq knowledge datasources list KB_ID    # List datasources
orq knowledge chunks list KB_ID DS_ID   # List chunks
```

### Prompts

```bash
orq prompts list                        # List prompts
orq prompts get PROMPT_ID               # Get prompt details
```

### Contacts

```bash
orq contacts create EXTERNAL_ID --name "John Doe" --email "john@example.com"
```

### Feedback

```bash
orq feedback create TRACE_ID --field rating --value 5
```

### Configuration

```bash
orq config show                         # Show configuration
orq config set KEY VALUE                # Set a config value
orq config get KEY                      # Get a config value
orq config path                         # Show config file path
```

## Quick Shortcuts

```bash
# Quick list any resource
orq list deployments
orq list datasets
orq list files

# Quick invoke with message
orq invoke DEPLOYMENT_KEY -m "message"

# Quick invoke with variables
orq invoke DEPLOYMENT_KEY -v firstname=John -v city=Paris

# Quick invoke with streaming
orq invoke DEPLOYMENT_KEY -v topic=AI -m "Explain this" --stream
```

## Interactive Mode

Run the CLI in interactive mode for a guided experience:

```bash
orq --interactive
# or
orq -i
```

## Output Formats

All commands support different output formats:

```bash
orq deployments list --output table   # Default, pretty table
orq deployments list --output json    # JSON output
orq deployments list --output yaml    # YAML output
```

## Configuration File

Configuration is stored in `~/.orq/config.yaml`:

```yaml
api_key: your-api-key
environment: production
output_format: table
```

## Environment Variables

- `ORQ_API_KEY`: API key for authentication
- `ORQ_ENVIRONMENT`: Default environment (production, staging, etc.)

## Development

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=orq
```
