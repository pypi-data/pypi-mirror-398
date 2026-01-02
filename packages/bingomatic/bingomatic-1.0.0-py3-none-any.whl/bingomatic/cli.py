"""Command-line interface for Bingomatic."""

import sys
from datetime import date
from pathlib import Path

import click

from bingomatic.config import (
    ConfigError,
    ConfigFileNotFoundError,
    ConfigValidationError,
    get_card_count,
    load_and_validate_config,
)
from bingomatic.pdf import generate_pdf


@click.group()
@click.version_option()
def main() -> None:
    """Bingomatic - A bingo card generator for conferences like DevOpsDays."""
    pass


@main.command()
def validate() -> None:
    """Validate the configuration file."""
    try:
        load_and_validate_config()
        click.echo("Configuration valid.")
        sys.exit(0)
    except ConfigFileNotFoundError as e:
        click.echo(str(e), err=True)
        sys.exit(1)
    except ConfigValidationError as e:
        click.echo(str(e), err=True)
        sys.exit(1)
    except ConfigError as e:
        click.echo(str(e), err=True)
        sys.exit(1)


@main.command()
def generate() -> None:
    """Generate bingo card PDF."""
    try:
        # Load and validate configuration
        config = load_and_validate_config()

        # Validate logo file exists
        logo_path = Path(config["logo_location"])
        if not logo_path.exists():
            click.echo(f"Logo file not found: {logo_path}", err=True)
            sys.exit(1)

        # Create output directory if needed
        output_dir = Path(config["output_directory"])
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            click.echo(f"Cannot create output directory: {output_dir} - {e}", err=True)
            sys.exit(1)

        # Generate output filename with current date
        today = date.today().isoformat()
        output_path = output_dir / f"bingo-cards-{today}.pdf"

        # Get card count from config
        card_count = get_card_count(config)

        # Generate PDF
        try:
            generate_pdf(
                output_path=output_path,
                card_count=card_count,
                event_name=config["event_name"],
                logo_path=logo_path,
                bingo_squares=config["bingo_squares"],
            )
        except Exception as e:
            click.echo(f"Failed to generate PDF: {e}", err=True)
            sys.exit(1)

        # Success message
        click.echo(f"Generated {card_count} bingo cards: {output_path}")
        sys.exit(0)

    except ConfigFileNotFoundError as e:
        click.echo(str(e), err=True)
        sys.exit(1)
    except ConfigValidationError as e:
        click.echo(str(e), err=True)
        sys.exit(1)
    except ConfigError as e:
        click.echo(str(e), err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
