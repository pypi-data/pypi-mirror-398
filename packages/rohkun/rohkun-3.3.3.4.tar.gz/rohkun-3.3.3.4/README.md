# Rohkun CLI v2

Client-side code analysis tool that finds API connections in your codebase.

## Features

- 🚀 **Fast** - All analysis happens locally on your machine
- 🔒 **Private** - Your code never leaves your computer
- 🎯 **Accurate** - Finds endpoints and API calls across multiple languages
- 📊 **Detailed Reports** - Saved locally in `.rohkun/reports/`
- 💥 **Blast Radius** - See impact of code changes
- 📈 **Confidence Scoring** - Know how reliable each connection is
- 🔄 **Diff Over Time** - Compare reports to track changes
- ⚡ **High Impact Detection** - Find critical nodes in your codebase

## Installation

```bash
pip install rohkun
```

## Quick Start

1. Get your API key from [rohkun.com/dashboard](https://rohkun.com/dashboard)

2. Configure the CLI:
```bash
rohkun config --api-key YOUR_API_KEY
```

3. Run analysis on your project:
```bash
rohkun run
```

Or run on a specific directory:
```bash
rohkun run /path/to/project
```

> **Note:** `rohkun scan` is still available as an alias for backward compatibility.

## How It Works

1. **Authorization Check** - CLI checks with server if you have credits
2. **Local Analysis** - All code analysis happens on your machine
3. **Snapshot Creation** - Each scan automatically creates a snapshot (like Git commits)
4. **Automatic Comparison** - Starting from your second scan, automatically compares with previous snapshot
5. **Report Generation** - Results saved to `.rohkun/reports/`
6. **Usage Tracking** - CLI reports completion to server for billing

**Your code is never uploaded to our servers.**

### Snapshot Workflow

Think of it like Git commits for your architecture:
- **First scan:** Creates Snapshot #1 (baseline)
- **Second scan:** Creates Snapshot #2, automatically compares with #1
- **Third scan:** Creates Snapshot #3, automatically compares with #2
- And so on...

Each scan shows you exactly what changed—new endpoints, removed API calls, broken connections, and more.

## Commands Reference

### Quick Reference Table

| Command | Description |
|---------|-------------|
| `rohkun run [path]` | Scan codebase and generate report |
| `rohkun run [path] --visualize` | Scan + open 3D visualization |
| `rohkun config --api-key KEY` | Set API key |
| `rohkun --version` | Show version |
| `rohkun --help` | Show all commands |

---

### `rohkun run` - Analyze Codebase

```bash
rohkun run [path] [options]
```

Scans your codebase for API endpoints, connections, and dependencies.

**Arguments:**
- `path` - Directory to scan (default: current directory)

**Options:**
- `--visualize` - Generate and open interactive 3D knowledge graph
- `-v, --verbose` - Show detailed output (blast radius, confidence scores)

**Examples:**
```bash
# Scan current directory
rohkun run

# Scan specific folder
rohkun run ./my-project

# Scan with visualization
rohkun run ./my-project --visualize

# Verbose output
rohkun run -v
```

> **Note:** `rohkun scan` is an alias for backward compatibility.

---

### `rohkun config` - Configure CLI

```bash
rohkun config --api-key YOUR_KEY
```

Saves API key to `.rohkun/config.json` in your project.

**Environment Variables (alternative):**
```bash
export ROHKUN_API_KEY=your_key_here
export ROHKUN_API_URL=https://custom-api.com  # For self-hosted
```

---

### `rohkun --version`

```bash
rohkun --version
```

Shows current CLI version (e.g., `Rohkun CLI v2.2.2`).

---

### `rohkun --help`

```bash
rohkun --help
```

Shows all available commands and options.

## Supported Languages

- Python (Flask, FastAPI, Django)
- JavaScript/TypeScript (Express, Next.js, React)
- Go (net/http, Gin, Echo)
- Java (Spring Boot)
- And more...

## Report Format

Reports are saved as JSON in `.rohkun/reports/`:

```json
{
  "version": "2.0.0",
  "generated_at": "2024-01-15T10:30:00Z",
  "summary": {
    "total_endpoints": 25,
    "total_api_calls": 18,
    "total_connections": 15,
    "high_confidence_connections": 12,
    "medium_confidence_connections": 2,
    "low_confidence_connections": 1,
    "estimated_accuracy": "High (80%+)",
    "high_impact_nodes": 3
  },
  "endpoints": [...],
  "api_calls": [...],
  "connections": [
    {
      "endpoint": {...},
      "api_call": {...},
      "confidence": "high",
      "confidence_score": 85,
      "confidence_reasons": ["HTTP method matches", "Path matches exactly"]
    }
  ],
  "blast_radius": [
    {
      "target": "GET:/api/users",
      "severity": "high",
      "total_dependents": 15,
      "affected_files": [...],
      "impact_description": "..."
    }
  ],
  "high_impact_nodes": [...],
  "accuracy": {...}
}
```

## Configuration

### API Key

Set via command:
```bash
rohkun config --api-key YOUR_KEY
```

Or environment variable:
```bash
export ROHKUN_API_KEY=your_key_here
```

### Custom API URL

For self-hosted instances:
```bash
export ROHKUN_API_URL=https://your-api.com
```

## Troubleshooting

### "No API key found"
```bash
rohkun config --api-key YOUR_KEY
```

### "Invalid or expired API key"
Get a new key at [rohkun.com/dashboard](https://rohkun.com/dashboard)

### "Insufficient credits"
Upgrade your plan at [rohkun.com/pricing](https://rohkun.com/pricing)

## Privacy

- Your code is analyzed **locally** on your machine
- Only authorization requests are sent to our servers
- No code content is ever uploaded
- Reports are saved locally in your project

## Support

- Website: [rohkun.com](https://rohkun.com)
- Dashboard: [rohkun.com/dashboard](https://rohkun.com/dashboard)
- Email: support@rohkun.com

## License

Proprietary - Copyright (c) 2025 Rohkun Labs. All rights reserved.

This is proprietary software. See LICENSE file for full terms and conditions.
