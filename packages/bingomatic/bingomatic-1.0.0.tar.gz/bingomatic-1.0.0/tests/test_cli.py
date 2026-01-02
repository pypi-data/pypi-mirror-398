"""Integration tests for the CLI module."""

import pytest
from click.testing import CliRunner

from bingomatic.cli import main


@pytest.fixture
def runner():
    """Create a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def valid_config(tmp_path):
    """Create a valid config file for testing."""
    config_content = f"""
event_name: "Test Event 2025"
logo_location: "{tmp_path / "logo.png"}"
output_directory: "{tmp_path / "output"}"
bingo_squares:
  - "Item 1"
  - "Item 2"
card_count: 2
"""
    config_dir = tmp_path / ".bingomatic"
    config_dir.mkdir()
    config_file = config_dir / "config.yaml"
    config_file.write_text(config_content)

    # Create test logo
    from PIL import Image

    logo = tmp_path / "logo.png"
    img = Image.new("RGB", (100, 100), color="blue")
    img.save(logo)

    return config_file


class TestValidateCommand:
    """Tests for the validate command."""

    def test_validate_shows_help(self, runner):
        """validate --help shows usage."""
        result = runner.invoke(main, ["validate", "--help"])
        assert result.exit_code == 0
        assert "Validate the configuration file" in result.output


class TestGenerateCommand:
    """Tests for the generate command."""

    def test_generate_shows_help(self, runner):
        """generate --help shows usage."""
        result = runner.invoke(main, ["generate", "--help"])
        assert result.exit_code == 0
        assert "Generate bingo card PDF" in result.output

    def test_generate_with_missing_config(self, runner, tmp_path, monkeypatch):
        """generate fails gracefully with missing config."""
        # Point to non-existent config
        monkeypatch.setattr(
            "bingomatic.config.get_config_path",
            lambda: tmp_path / "nonexistent" / "config.yaml",
        )

        result = runner.invoke(main, ["generate"])

        assert result.exit_code == 1
        assert "Config file missing" in result.output

    def test_generate_with_missing_logo(self, runner, tmp_path, monkeypatch):
        """generate fails gracefully with missing logo file."""
        bingo_items = "\n".join([f'  - "Item {i}"' for i in range(24)])
        config_content = f"""
event_name: "Test Event"
logo_location: "{tmp_path / "nonexistent.png"}"
output_directory: "{tmp_path / "output"}"
bingo_squares:
{bingo_items}
"""
        config_dir = tmp_path / ".bingomatic"
        config_dir.mkdir()
        config_file = config_dir / "config.yaml"
        config_file.write_text(config_content)

        monkeypatch.setattr("bingomatic.config.get_config_path", lambda: config_file)

        result = runner.invoke(main, ["generate"])

        assert result.exit_code == 1
        assert "Logo file not found" in result.output


class TestMainGroup:
    """Tests for the main CLI group."""

    def test_main_shows_help(self, runner):
        """main --help shows available commands."""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "validate" in result.output
        assert "generate" in result.output

    def test_version_option(self, runner):
        """--version shows version info."""
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "version" in result.output.lower()
