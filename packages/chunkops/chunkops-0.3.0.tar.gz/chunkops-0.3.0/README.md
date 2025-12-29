# ChunkOps CLI

**The CI/CD Pipeline for RAG.** Detect conflicts before they become hallucinations.

## Installation

```bash
pip install chunkops
```

## Quick Start

### 1. Initialize ChunkOps

```bash
chunkops init
```

This creates a `chunkops.yaml` config file in your project root.

### 2. Scan Your Documents

```bash
chunkops scan
```

**Level 1 (Free)**: Detects exact duplicates and empty files  
**Level 2 (Cloud)**: Semantic conflict detection (requires authentication)

### 3. Enable Cloud Features

```bash
chunkops login
```

Opens browser for authentication. Enables semantic conflict detection.

### 4. Add to CI/CD

Add to your `.github/workflows/rag-test.yml`:

```yaml
- name: Run ChunkOps CI Check
  run: chunkops ci
  env:
    CHUNKOPS_API_KEY: ${{ secrets.CHUNKOPS_API_KEY }}
```

## Commands

### `chunkops init`

Initialize ChunkOps in your project. Creates `chunkops.yaml` config file.

```bash
chunkops init --docs-path ./data --output-path ./reports
```

### `chunkops scan`

Scan documents for duplicates and conflicts.

```bash
chunkops scan                    # Use config defaults
chunkops scan ./docs            # Scan specific directory
chunkops scan -o report.json    # Custom output file
chunkops scan --verbose         # Verbose output
```

**Output:**
- ✅ Valid chunks count
- ⚠️ Exact duplicates (with estimated space saved)
- 🟡 Near duplicates
- 🚨 Semantic conflicts (requires authentication)

### `chunkops login` / `chunkops auth`

Authenticate with ChunkOps Cloud to enable semantic conflict detection.

```bash
chunkops login                  # Opens browser
chunkops auth --api-key chk_... # Use API key directly
```

### `chunkops ci`

CI/CD mode: Runs silently, outputs JSON, exits with error code on failures.

```bash
chunkops ci                     # Use config defaults
chunkops ci ./docs              # Scan specific directory
chunkops ci --no-fail-on-critical  # Don't exit on critical conflicts
```

**Exit Codes:**
- `0`: No critical conflicts
- `1`: Critical conflicts detected (blocks PR merge)

## Configuration

The `chunkops.yaml` file:

```yaml
docs_path: ./data
output_path: ./chunkops-reports
exact_threshold: 1.0
near_threshold: 0.90
enable_cloud: false
api_url: https://console.chunkops.ai
```

## CI/CD Integration

### GitHub Actions

```yaml
name: RAG Quality Check

on:
  pull_request:
    paths:
      - 'docs/**'
      - 'data/**'

jobs:
  chunkops-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install chunkops
      - run: chunkops ci
        env:
          CHUNKOPS_API_KEY: ${{ secrets.CHUNKOPS_API_KEY }}
```

### GitLab CI

```yaml
chunkops-check:
  image: python:3.11
  script:
    - pip install chunkops
    - chunkops ci
  variables:
    CHUNKOPS_API_KEY: $CHUNKOPS_API_KEY
```

## Output Format

### Interactive Mode (`chunkops scan`)

Beautiful terminal output with colors, progress bars, and summary tables.

### CI Mode (`chunkops ci`)

JSON output only:

```json
{
  "scan_date": "2024-01-15T10:30:00Z",
  "total_files": 14,
  "total_chunks": 245,
  "exact_duplicates": 2,
  "near_duplicates": 5,
  "semantic_conflicts": 3,
  "critical_conflicts": 1,
  "summary": {
    "valid_chunks": 240,
    "exact_duplicates": 2,
    "near_duplicates": 5,
    "conflicts": 3
  }
}
```

## The Two-Tier Model

**Level 1 (Free/Local):**
- Exact duplicate detection (MD5 hash)
- Empty file detection
- Fast, runs entirely locally

**Level 2 (Cloud/Upsell):**
- Semantic conflict detection
- Policy contradiction detection
- Requires authentication (`chunkops login`)

## License

MIT

## Support

Visit [chunkops.ai](https://chunkops.ai) for more information.
