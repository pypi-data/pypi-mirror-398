"""PDF generation for Bingomatic bingo cards."""

import random
from pathlib import Path

from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas


# Font configuration
FONTS_DIR = Path(__file__).parent / "fonts"
_fonts_registered = False


def register_fonts() -> None:
    """Register custom fonts for use in PDF generation.

    Registers Roboto and Roboto Mono fonts from the bundled fonts directory.
    This function is idempotent - calling it multiple times has no effect.
    """
    global _fonts_registered
    if _fonts_registered:
        return

    # Register Roboto fonts
    roboto_regular = FONTS_DIR / "Roboto-Regular.ttf"
    roboto_bold = FONTS_DIR / "Roboto-Bold.ttf"
    roboto_mono = FONTS_DIR / "RobotoMono-Regular.ttf"

    if roboto_regular.exists():
        pdfmetrics.registerFont(TTFont("Roboto", str(roboto_regular)))
    if roboto_bold.exists():
        pdfmetrics.registerFont(TTFont("Roboto-Bold", str(roboto_bold)))
    if roboto_mono.exists():
        pdfmetrics.registerFont(TTFont("RobotoMono", str(roboto_mono)))

    _fonts_registered = True


# Constants for grid dimensions (in points, 72 points = 1 inch)
SQUARE_SIZE = 72  # 1 inch
GRID_SIZE = 5  # 5x5 grid
GAP = 36  # 0.5 inch gap between grids
GRID_TOTAL = SQUARE_SIZE * GRID_SIZE  # 5 inches total
CENTER_SQUARE_INDEX = 12  # Center of 5x5 grid (row 2, col 2 in 0-indexed)

# Text rendering constants
MIN_FONT_SIZE = 6
MAX_FONT_SIZE = 12
SQUARE_PADDING = 4


def select_random_squares(bingo_squares: list[str], count: int = 24) -> list[str]:
    """Select random unique items from bingo_squares list.

    Args:
        bingo_squares: List of bingo square phrases
        count: Number of items to select (default 24 for 5x5 grid minus center)

    Returns:
        List of randomly selected unique items
    """
    return random.sample(bingo_squares, count)


def _wrap_text(
    text: str, font_name: str, font_size: float, max_width: float
) -> list[str]:
    """Wrap text to fit within a maximum width.

    Args:
        text: Text to wrap
        font_name: Name of the font to use for measurement
        font_size: Font size in points
        max_width: Maximum width in points

    Returns:
        List of lines that fit within max_width
    """
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        test_line = " ".join(current_line + [word])
        width = pdfmetrics.stringWidth(test_line, font_name, font_size)
        if width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]

    if current_line:
        lines.append(" ".join(current_line))

    return lines if lines else [text]


def _fit_text_in_square(
    text: str, max_width: float, max_height: float, font_name: str = "RobotoMono"
) -> tuple[list[str], float]:
    """Fit text within a square by wrapping and shrinking font size.

    Args:
        text: Text to fit
        max_width: Maximum width in points
        max_height: Maximum height in points
        font_name: Font name to use

    Returns:
        Tuple of (wrapped lines, font size used)
    """
    for font_size in range(MAX_FONT_SIZE, MIN_FONT_SIZE - 1, -1):
        lines = _wrap_text(text, font_name, font_size, max_width)
        line_height = font_size * 1.2
        total_height = len(lines) * line_height

        if total_height <= max_height:
            return lines, font_size

    # If we can't fit even at minimum size, return with minimum
    lines = _wrap_text(text, font_name, MIN_FONT_SIZE, max_width)
    return lines, MIN_FONT_SIZE


def _draw_square_text(
    canvas: Canvas, text: str, square_x: float, square_y: float
) -> None:
    """Draw text centered in a square with auto-fitting.

    Args:
        canvas: ReportLab canvas to draw on
        text: Text to draw
        square_x: X coordinate of square's bottom-left corner
        square_y: Y coordinate of square's bottom-left corner
    """
    content_width = SQUARE_SIZE - (SQUARE_PADDING * 2)
    content_height = SQUARE_SIZE - (SQUARE_PADDING * 2)

    lines, font_size = _fit_text_in_square(text, content_width, content_height)

    canvas.setFont("RobotoMono", font_size)
    canvas.setFillColorRGB(0, 0, 0)

    line_height = font_size * 1.2
    total_text_height = len(lines) * line_height

    # Calculate starting Y to center text vertically
    start_y = square_y + (SQUARE_SIZE + total_text_height) / 2 - font_size

    for i, line in enumerate(lines):
        line_y = start_y - (i * line_height)
        line_x = square_x + SQUARE_SIZE / 2
        canvas.drawCentredString(line_x, line_y, line)


def _draw_card_squares(
    canvas: Canvas, grid_x: float, grid_y: float, squares: list[str]
) -> None:
    """Draw text in all squares of a bingo card grid.

    Args:
        canvas: ReportLab canvas to draw on
        grid_x: X coordinate of grid's bottom-left corner
        grid_y: Y coordinate of grid's bottom-left corner
        squares: List of 24 square texts (excluding center)
    """
    square_index = 0
    for grid_pos in range(25):  # 5x5 = 25 positions
        if grid_pos == CENTER_SQUARE_INDEX:
            continue  # Skip center square (logo goes there)

        row = grid_pos // GRID_SIZE
        col = grid_pos % GRID_SIZE

        square_x = grid_x + (col * SQUARE_SIZE)
        square_y = grid_y + (row * SQUARE_SIZE)

        if square_index < len(squares):
            _draw_square_text(canvas, squares[square_index], square_x, square_y)
            square_index += 1


def calculate_grid_positions(
    page_width: float, page_height: float
) -> tuple[float, float, float, float]:
    """Calculate x,y positions for two centered grids with a gap between them.

    Args:
        page_width: Width of the page in points
        page_height: Height of the page in points

    Returns:
        Tuple of (left_x, left_y, right_x, right_y) for grid positions
    """
    # Total width of both grids plus gap
    total_width = (GRID_TOTAL * 2) + GAP

    # Center horizontally
    left_x = (page_width - total_width) / 2
    right_x = left_x + GRID_TOTAL + GAP

    # Center vertically (leaving space for header)
    header_space = 36  # 0.5 inch for event name
    available_height = page_height - header_space
    y = (available_height - GRID_TOTAL) / 2

    return left_x, y, right_x, y


def draw_grid(canvas: Canvas, x: float, y: float) -> None:
    """Draw a 5x5 grid of 1-inch squares at the specified position.

    Args:
        canvas: ReportLab canvas to draw on
        x: X coordinate of bottom-left corner of grid
        y: Y coordinate of bottom-left corner of grid
    """
    canvas.setStrokeColorRGB(0, 0, 0)  # Black lines
    canvas.setLineWidth(1)

    # Draw horizontal lines
    for row in range(GRID_SIZE + 1):
        y_pos = y + (row * SQUARE_SIZE)
        canvas.line(x, y_pos, x + GRID_TOTAL, y_pos)

    # Draw vertical lines
    for col in range(GRID_SIZE + 1):
        x_pos = x + (col * SQUARE_SIZE)
        canvas.line(x_pos, y, x_pos, y + GRID_TOTAL)


def generate_pdf(
    output_path: Path | str,
    card_count: int,
    event_name: str | None = None,
    logo_path: Path | str | None = None,
    bingo_squares: list[str] | None = None,
) -> Path:
    """Generate a PDF with bingo card grids.

    Args:
        output_path: Path where the PDF will be saved
        card_count: Number of bingo cards to generate
        event_name: Optional event name to display above each grid
        logo_path: Optional path to logo image for center square
        bingo_squares: Optional list of bingo square phrases (requires 24+ items)

    Returns:
        Path to the generated PDF file
    """
    output_path = Path(output_path)
    page_width, page_height = landscape(letter)

    # Register custom fonts
    register_fonts()

    canvas = Canvas(str(output_path), pagesize=landscape(letter))

    # Calculate how many pages we need (2 cards per page)
    pages_needed = (card_count + 1) // 2

    for page_num in range(pages_needed):
        # Calculate grid positions
        left_x, left_y, right_x, right_y = calculate_grid_positions(
            page_width, page_height
        )

        # Draw left grid (always present)
        draw_grid(canvas, left_x, left_y)

        # Draw event name above left grid if provided
        if event_name:
            _draw_event_name(canvas, event_name, left_x, left_y)

        # Draw bingo squares for left card
        if bingo_squares:
            left_squares = select_random_squares(bingo_squares)
            _draw_card_squares(canvas, left_x, left_y, left_squares)

        # Draw logo in center square of left grid if provided
        if logo_path:
            _draw_logo(canvas, logo_path, left_x, left_y)

        # Draw name field below left grid
        _draw_name_field(canvas, left_x, left_y)

        # Draw right grid only if we have another card to show
        cards_on_this_page = 2 if (page_num * 2 + 2) <= card_count else 1
        if cards_on_this_page == 2:
            draw_grid(canvas, right_x, right_y)

            # Draw event name above right grid if provided
            if event_name:
                _draw_event_name(canvas, event_name, right_x, right_y)

            # Draw bingo squares for right card
            if bingo_squares:
                right_squares = select_random_squares(bingo_squares)
                _draw_card_squares(canvas, right_x, right_y, right_squares)

            # Draw logo in center square of right grid if provided
            if logo_path:
                _draw_logo(canvas, logo_path, right_x, right_y)

            # Draw name field below right grid
            _draw_name_field(canvas, right_x, right_y)

        # Add new page if not the last one
        if page_num < pages_needed - 1:
            canvas.showPage()

    canvas.save()
    return output_path


def _draw_name_field(canvas: Canvas, grid_x: float, grid_y: float) -> None:
    """Draw participant name field below the grid.

    Args:
        canvas: ReportLab canvas to draw on
        grid_x: X coordinate of grid's bottom-left corner
        grid_y: Y coordinate of grid's bottom-left corner
    """
    # Position name field below grid
    label = "Name:"
    field_y = grid_y - 18  # 0.25 inch below grid

    canvas.setFont("Roboto", 12)
    canvas.setFillColorRGB(0, 0, 0)

    # Draw "Name:" label
    canvas.drawString(grid_x, field_y, label)

    # Draw underline from after label to end of grid
    label_width = pdfmetrics.stringWidth(label, "Roboto", 12)
    line_start_x = grid_x + label_width + 4
    line_end_x = grid_x + GRID_TOTAL
    line_y = field_y - 2

    canvas.setLineWidth(0.5)
    canvas.line(line_start_x, line_y, line_end_x, line_y)


def _draw_event_name(
    canvas: Canvas, event_name: str, grid_x: float, grid_y: float
) -> None:
    """Draw event name centered above the grid.

    Args:
        canvas: ReportLab canvas to draw on
        event_name: Text to display
        grid_x: X coordinate of grid's bottom-left corner
        grid_y: Y coordinate of grid's bottom-left corner
    """
    # Position text above grid
    text_x = grid_x + (GRID_TOTAL / 2)
    text_y = grid_y + GRID_TOTAL + 10  # 10 points above grid

    canvas.setFont("Roboto-Bold", 14)
    canvas.drawCentredString(text_x, text_y, event_name)


def _draw_logo(
    canvas: Canvas, logo_path: Path | str, grid_x: float, grid_y: float
) -> None:
    """Draw logo in the center square of the grid.

    Args:
        canvas: ReportLab canvas to draw on
        logo_path: Path to the logo image file
        grid_x: X coordinate of grid's bottom-left corner
        grid_y: Y coordinate of grid's bottom-left corner
    """
    logo_path = Path(logo_path)

    if not logo_path.exists():
        raise FileNotFoundError(f"Logo file not found: {logo_path}")

    # Center square is at row 2, col 2 (0-indexed), which is row 3, col 3 (1-indexed)
    center_row = 2
    center_col = 2

    # Calculate center square position
    square_x = grid_x + (center_col * SQUARE_SIZE)
    square_y = grid_y + (center_row * SQUARE_SIZE)

    # Add small padding inside the square
    padding = 4
    logo_x = square_x + padding
    logo_y = square_y + padding
    logo_size = SQUARE_SIZE - (padding * 2)

    # Draw the logo, maintaining aspect ratio
    canvas.drawImage(
        str(logo_path),
        logo_x,
        logo_y,
        width=logo_size,
        height=logo_size,
        preserveAspectRatio=True,
        anchor="c",
    )
