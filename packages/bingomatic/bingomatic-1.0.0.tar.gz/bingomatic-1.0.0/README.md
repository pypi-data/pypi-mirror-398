[![CI](https://github.com/richardboydii/bingomatic/actions/workflows/ci.yml/badge.svg)](https://github.com/richardboydii/bingomatic/actions/workflows/ci.yml)

<p align="center">
  <img src="images/bingomatic_logo.png" alt="Bingomatic Logo" width="300" height="300">
</p>

# Bingomatic

A bingo card generator for conferences like DevOpsDays. This is a simple Python CLI that will generate 5" x 5" bingo cards, two to a landscape page, for use at events and conferences.

## Installation

### Prerequisites

- Python 3.12 or higher
- [uv](https://docs.astral.sh/uv/) package manager

### Install from source

```bash
git clone https://github.com/yourusername/bingomatic.git
cd bingomatic
uv sync
```

## Usage

### Validate Configuration

Before generating bingo cards, validate your configuration file:

```bash
uv run bingomatic validate
```

**Success output:**

```
Configuration valid.
```

**Error output (missing config):**

```
Config file missing, please create it using the template and README instructions.
```

### Generate Bingo Cards

Generate PDF bingo cards using your configuration:

```bash
uv run bingomatic generate
```

**Success output:**

```
Generated 2 bingo cards: /path/to/output/bingo-cards-2025-12-25.pdf
```

The generated PDF will contain:
- Two 5×5 bingo card grids per landscape page
- Each square measuring 1" × 1"
- Event name centered above each grid
- Event logo in the center square
- Name of participant below each grid

## Configuration

Bingomatic uses a YAML configuration file located at `~/.bingomatic/config.yaml`.

### Setup

1. Create the configuration directory:

```bash
mkdir -p ~/.bingomatic
```

2. Copy the template to create your config file:

```bash
cp config_template.yaml ~/.bingomatic/config.yaml
```

3. Edit the config file with your event details.

### Configuration Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_name` | string | Yes | Name of your event (e.g., "DevOpsDays Austin 2026") |
| `logo_location` | string | Yes | Path to your event logo image |
| `output_directory` | string | Yes | Directory where generated cards will be saved |
| `bingo_squares` | array | Yes | List of phrases/terms for bingo squares |
| `card_count` | integer | No | Number of bingo cards to generate (default: 2) |

### Example Configuration

```yaml
event_name: "DevOpsDays Austin 2026"
logo_location: "/path/to/logo.png"
output_directory: "/path/to/output"
card_count: 2
bingo_squares:
  - "Kubernetes"
  - "CI/CD"
  - "Infrastructure as Code"
  - "Observability"
  - "GitOps"
  - "Platform Engineering"
  # Add at least 24 items for a 5x5 card with a free space
```

## Development

### Running Tests

```bash
uv run pytest tests/ -v
```

## License

See [LICENSE](LICENSE) for details.

