"""Unit tests for the pdf module."""

from pathlib import Path

import pytest

from bingomatic.pdf import (
    FONTS_DIR,
    GRID_SIZE,
    GRID_TOTAL,
    GAP,
    SQUARE_SIZE,
    calculate_grid_positions,
    generate_pdf,
    register_fonts,
    select_random_squares,
)


class TestFontRegistration:
    """Tests for font registration."""

    def test_fonts_directory_exists(self):
        """Font directory exists in the package."""
        assert FONTS_DIR.exists()
        assert FONTS_DIR.is_dir()

    def test_roboto_regular_font_exists(self):
        """Roboto-Regular.ttf exists in fonts directory."""
        font_path = FONTS_DIR / "Roboto-Regular.ttf"
        assert font_path.exists()

    def test_roboto_bold_font_exists(self):
        """Roboto-Bold.ttf exists in fonts directory."""
        font_path = FONTS_DIR / "Roboto-Bold.ttf"
        assert font_path.exists()

    def test_roboto_mono_font_exists(self):
        """RobotoMono-Regular.ttf exists in fonts directory."""
        font_path = FONTS_DIR / "RobotoMono-Regular.ttf"
        assert font_path.exists()

    def test_register_fonts_does_not_raise(self):
        """register_fonts() completes without error."""
        register_fonts()

    def test_register_fonts_is_idempotent(self):
        """register_fonts() can be called multiple times without error."""
        register_fonts()
        register_fonts()


class TestSelectRandomSquares:
    """Tests for random square selection."""

    def test_returns_24_items_by_default(self):
        """select_random_squares returns 24 items by default."""
        squares = [f"Item {i}" for i in range(30)]
        result = select_random_squares(squares)
        assert len(result) == 24

    def test_returns_unique_items(self):
        """select_random_squares returns unique items (no duplicates)."""
        squares = [f"Item {i}" for i in range(30)]
        result = select_random_squares(squares)
        assert len(result) == len(set(result))

    def test_returns_different_results_on_multiple_calls(self):
        """select_random_squares returns different results on multiple calls."""
        squares = [f"Item {i}" for i in range(30)]
        results = [tuple(select_random_squares(squares)) for _ in range(10)]
        unique_results = set(results)
        assert len(unique_results) > 1

    def test_respects_custom_count(self):
        """select_random_squares respects custom count parameter."""
        squares = [f"Item {i}" for i in range(30)]
        result = select_random_squares(squares, count=10)
        assert len(result) == 10


class TestConstants:
    """Tests for PDF constants."""

    def test_square_size_is_one_inch(self):
        """SQUARE_SIZE is 72 points (1 inch)."""
        assert SQUARE_SIZE == 72

    def test_grid_size_is_five(self):
        """GRID_SIZE is 5 for 5x5 grid."""
        assert GRID_SIZE == 5

    def test_gap_is_half_inch(self):
        """GAP is 36 points (0.5 inch)."""
        assert GAP == 36

    def test_grid_total_is_five_inches(self):
        """GRID_TOTAL is 360 points (5 inches)."""
        assert GRID_TOTAL == 360


class TestCalculateGridPositions:
    """Tests for calculate_grid_positions function."""

    def test_returns_four_values(self):
        """calculate_grid_positions returns left_x, left_y, right_x, right_y."""
        result = calculate_grid_positions(792, 612)  # Letter landscape
        assert len(result) == 4

    def test_grids_are_horizontally_centered(self):
        """Grids are centered horizontally on the page."""
        page_width = 792  # Letter landscape width
        page_height = 612
        left_x, _, right_x, _ = calculate_grid_positions(page_width, page_height)

        # Left margin should equal right margin
        left_margin = left_x
        right_margin = page_width - (right_x + GRID_TOTAL)

        assert abs(left_margin - right_margin) < 1  # Allow small floating point diff

    def test_grids_have_correct_gap(self):
        """Grids have 0.5 inch (36 point) gap between them."""
        left_x, _, right_x, _ = calculate_grid_positions(792, 612)

        actual_gap = right_x - (left_x + GRID_TOTAL)
        assert actual_gap == GAP

    def test_grids_have_same_y_position(self):
        """Both grids have the same vertical position."""
        _, left_y, _, right_y = calculate_grid_positions(792, 612)
        assert left_y == right_y


class TestGeneratePdf:
    """Tests for generate_pdf function."""

    def test_generates_pdf_file(self, tmp_path):
        """generate_pdf creates a PDF file at the specified path."""
        output_path = tmp_path / "test.pdf"

        result = generate_pdf(output_path, card_count=2)

        assert result == output_path
        assert output_path.exists()

    def test_generates_correct_page_count_even(self, tmp_path):
        """generate_pdf creates correct number of pages for even card count."""
        output_path = tmp_path / "test.pdf"

        generate_pdf(output_path, card_count=4)

        # Read PDF and check page count
        with open(output_path, "rb") as f:
            content = f.read()
            # Count page objects in PDF (simple check)
            page_count = content.count(b"/Type /Page") - content.count(b"/Type /Pages")
            assert page_count == 2  # 4 cards = 2 pages

    def test_generates_correct_page_count_odd(self, tmp_path):
        """generate_pdf creates correct number of pages for odd card count."""
        output_path = tmp_path / "test.pdf"

        generate_pdf(output_path, card_count=3)

        with open(output_path, "rb") as f:
            content = f.read()
            page_count = content.count(b"/Type /Page") - content.count(b"/Type /Pages")
            assert page_count == 2  # 3 cards = 2 pages (1 page with 2, 1 page with 1)

    def test_generates_single_page_for_two_cards(self, tmp_path):
        """generate_pdf creates single page for 2 cards."""
        output_path = tmp_path / "test.pdf"

        generate_pdf(output_path, card_count=2)

        with open(output_path, "rb") as f:
            content = f.read()
            page_count = content.count(b"/Type /Page") - content.count(b"/Type /Pages")
            assert page_count == 1

    def test_generates_single_page_for_one_card(self, tmp_path):
        """generate_pdf creates single page for 1 card."""
        output_path = tmp_path / "test.pdf"

        generate_pdf(output_path, card_count=1)

        with open(output_path, "rb") as f:
            content = f.read()
            page_count = content.count(b"/Type /Page") - content.count(b"/Type /Pages")
            assert page_count == 1

    def test_accepts_path_object(self, tmp_path):
        """generate_pdf accepts Path object for output_path."""
        output_path = tmp_path / "test.pdf"

        result = generate_pdf(Path(output_path), card_count=2)

        assert isinstance(result, Path)
        assert result.exists()

    def test_accepts_string_path(self, tmp_path):
        """generate_pdf accepts string for output_path."""
        output_path = str(tmp_path / "test.pdf")

        result = generate_pdf(output_path, card_count=2)

        assert isinstance(result, Path)
        assert result.exists()

    def test_generates_pdf_with_event_name(self, tmp_path):
        """generate_pdf creates PDF when event name is provided."""
        output_path = tmp_path / "test.pdf"

        result = generate_pdf(output_path, card_count=2, event_name="Test Event 2025")

        assert result.exists()
        # PDF content is compressed; visual verification done via proof artifacts

    def test_generates_pdf_with_logo(self, tmp_path):
        """generate_pdf includes logo when provided."""
        output_path = tmp_path / "test.pdf"

        # Create a simple test logo
        logo_path = tmp_path / "logo.png"
        _create_test_image(logo_path)

        result = generate_pdf(output_path, card_count=2, logo_path=logo_path)

        assert result.exists()

    def test_raises_error_for_missing_logo(self, tmp_path):
        """generate_pdf raises FileNotFoundError for missing logo."""
        output_path = tmp_path / "test.pdf"
        missing_logo = tmp_path / "nonexistent.png"

        with pytest.raises(FileNotFoundError) as exc_info:
            generate_pdf(output_path, card_count=2, logo_path=missing_logo)

        assert "Logo file not found" in str(exc_info.value)


def _create_test_image(path: Path) -> None:
    """Create a simple test PNG image."""
    from PIL import Image

    img = Image.new("RGB", (100, 100), color="red")
    img.save(path)
