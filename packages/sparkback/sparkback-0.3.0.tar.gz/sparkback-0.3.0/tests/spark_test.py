# flake8: noqa
# pylint: skip-file
# mypy: ignore-errors

import pytest
import sparkback.spark as spark


def test_scale_data_default():
    data = [1, 2, 3, 4, 5, 6, 7, 8]
    style_instance = spark.DefaultStyle()
    expected_output = ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
    assert style_instance.scale_data(data) == expected_output


def test_scale_data_block():
    data = [1, 2, 3, 4, 5, 6, 7, 8]
    style_instance = spark.BlockStyle()
    expected_output = ["▏", "▎", "▍", "▌", "▋", "▊", "▉", "█"]
    assert style_instance.scale_data(data) == expected_output


def test_scale_data_arrows():
    data = [1, 2, 3, 2, 2, 7, 6]
    style_instance = spark.ArrowsStyle()
    expected_output = ["→", "↑", "↑", "↓", "→", "↑", "↓"]
    assert style_instance.scale_data(data) == expected_output


def test_print_stats():
    data = [1, 2, 3, 4, 5, 6, 7, 8]
    expected_output = "Minimum: 1\nMaximum: 8\nMean: 4.5\nStandard Deviation: 2.449489742783178"
    assert spark.print_stats(data) == expected_output


# LineGraphStyle Tests

class TestLineGraphStyle:
    """Comprehensive tests for LineGraphStyle class."""

    def test_init_default_height(self):
        """Test initialization with default height."""
        style = spark.LineGraphStyle()
        assert style.height == 10

    def test_init_custom_height(self):
        """Test initialization with custom height."""
        style = spark.LineGraphStyle(height=15)
        assert style.height == 15

    def test_init_invalid_height(self):
        """Test initialization with invalid height raises ValueError."""
        with pytest.raises(ValueError, match="Graph height must be at least 2"):
            spark.LineGraphStyle(height=1)

    def test_empty_data_raises_error(self):
        """Test that empty data raises ValueError."""
        style = spark.LineGraphStyle()
        with pytest.raises(ValueError, match="Data cannot be empty"):
            style.scale_data([])

    def test_single_data_point(self):
        """Test rendering a single data point."""
        style = spark.LineGraphStyle(height=5)
        result = style.scale_data([42])

        # Should have a point (●) in the middle row
        assert len(result) == 5
        assert len(result[0]) == 1

        # Find the point
        point_found = False
        for row in result:
            if row[0] == "●":
                point_found = True
                break
        assert point_found, "Single point should be marked with ●"

    def test_two_points_horizontal(self):
        """Test rendering two points at the same value (horizontal line)."""
        style = spark.LineGraphStyle(height=5)
        result = style.scale_data([5, 5])

        # Should draw a horizontal line
        assert len(result) == 5
        assert len(result[0]) == 2

        # Find the row with the line
        line_row = None
        for i, row in enumerate(result):
            if "●" in row or "─" in row:
                line_row = i
                break

        assert line_row is not None, "Should have a line row"
        assert result[line_row][0] == "●", "Start should be marked"
        assert result[line_row][1] == "●", "End should be marked"

    def test_flat_line_all_same_values(self):
        """Test rendering when all values are the same."""
        style = spark.LineGraphStyle(height=5)
        result = style.scale_data([10, 10, 10, 10])

        # Should draw a horizontal line in the middle
        assert len(result) == 5
        assert len(result[0]) == 4

        # Find the line (should be at y_pos = height // 2 = 2)
        line_chars = set()
        for row in result:
            for char in row:
                if char != " ":
                    line_chars.add(char)

        # Should only have horizontal line characters
        assert "─" in line_chars, "Should contain horizontal line character"

    def test_increasing_line(self):
        """Test rendering an increasing line."""
        style = spark.LineGraphStyle(height=10)
        result = style.scale_data([1, 2, 3, 4, 5])

        assert len(result) == 10
        assert len(result[0]) == 5

        # Should have endpoint markers
        endpoints_found = 0
        for row in result:
            endpoints_found += row.count("●")
        assert endpoints_found == 2, "Should have 2 endpoint markers"

        # Should have some diagonal or vertical characters
        chars_used = set()
        for row in result:
            for char in row:
                if char != " ":
                    chars_used.add(char)

        # Should contain line drawing characters
        assert len(chars_used) > 0, "Should use line drawing characters"

    def test_decreasing_line(self):
        """Test rendering a decreasing line."""
        style = spark.LineGraphStyle(height=10)
        result = style.scale_data([5, 4, 3, 2, 1])

        assert len(result) == 10
        assert len(result[0]) == 5

        # Should have endpoint markers
        endpoints_found = 0
        for row in result:
            endpoints_found += row.count("●")
        assert endpoints_found == 2, "Should have 2 endpoint markers"

    def test_zigzag_pattern(self):
        """Test rendering a zigzag pattern."""
        style = spark.LineGraphStyle(height=10)
        result = style.scale_data([1, 5, 2, 6, 3])

        assert len(result) == 10
        assert len(result[0]) == 5

        # Should have various line characters
        chars_used = set()
        for row in result:
            for char in row:
                if char != " ":
                    chars_used.add(char)

        # Should use multiple types of characters for zigzag
        assert len(chars_used) >= 2, "Zigzag should use multiple character types"

    def test_diagonal_up_character(self):
        """Test that diagonal up lines use ╱ character."""
        style = spark.LineGraphStyle(height=10)
        # Two points with difference of 1 in y (scaled)
        result = style.scale_data([1, 2])

        # Check if diagonal character is present
        chars_used = set()
        for row in result:
            for char in row:
                if char not in (" ", "●"):
                    chars_used.add(char)

        # Should contain either ╱ for diagonal or │ for vertical
        assert "╱" in chars_used or "│" in chars_used, "Should use diagonal or vertical character"

    def test_diagonal_down_character(self):
        """Test that diagonal down lines use ╲ character."""
        style = spark.LineGraphStyle(height=10)
        # Two points with difference of -1 in y (scaled)
        result = style.scale_data([2, 1])

        # Check if diagonal character is present
        chars_used = set()
        for row in result:
            for char in row:
                if char not in (" ", "●"):
                    chars_used.add(char)

        # Should contain either ╲ for diagonal or │ for vertical
        assert "╲" in chars_used or "│" in chars_used, "Should use diagonal or vertical character"

    def test_vertical_character(self):
        """Test that steep lines use │ character."""
        style = spark.LineGraphStyle(height=10)
        # Two points with large y difference
        result = style.scale_data([1, 10])

        # Should contain vertical line character
        chars_used = set()
        for row in result:
            for char in row:
                if char not in (" ", "●"):
                    chars_used.add(char)

        assert "│" in chars_used, "Steep line should use vertical character │"

    def test_graph_dimensions(self):
        """Test that graph has correct dimensions."""
        style = spark.LineGraphStyle(height=8)
        result = style.scale_data([1, 2, 3, 4, 5, 6])

        assert len(result) == 8, "Graph should have correct height"
        assert all(len(row) == 6 for row in result), "All rows should have correct width"

    def test_endpoints_marked(self):
        """Test that first and last points are marked with ●."""
        style = spark.LineGraphStyle(height=10)
        result = style.scale_data([5, 3, 7, 2, 8])

        # Check first column for ●
        first_col_has_endpoint = any(row[0] == "●" for row in result)
        # Check last column for ●
        last_col_has_endpoint = any(row[-1] == "●" for row in result)

        assert first_col_has_endpoint, "First data point should be marked with ●"
        assert last_col_has_endpoint, "Last data point should be marked with ●"

    def test_str_representation(self):
        """Test string representation of the style."""
        style = spark.LineGraphStyle(height=12)
        assert str(style) == "Line Graph Style (height=12)"

    def test_verbose_parameter(self):
        """Test that verbose parameter is accepted (even if unused)."""
        style = spark.LineGraphStyle()
        # Should not raise an error
        result = style.scale_data([1, 2, 3], verbose=True)
        assert result is not None


# BrailleLineGraphStyle Tests

class TestBrailleLineGraphStyle:
    """Comprehensive tests for BrailleLineGraphStyle class."""

    def test_init_default_height(self):
        """Test initialization with default height."""
        style = spark.BrailleLineGraphStyle()
        assert style.height == 10

    def test_init_custom_height(self):
        """Test initialization with custom height."""
        style = spark.BrailleLineGraphStyle(height=5)
        assert style.height == 5

    def test_init_invalid_height(self):
        """Test initialization with invalid height raises ValueError."""
        with pytest.raises(ValueError, match="Graph height must be at least 1"):
            spark.BrailleLineGraphStyle(height=0)

    def test_empty_data_raises_error(self):
        """Test that empty data raises ValueError."""
        style = spark.BrailleLineGraphStyle()
        with pytest.raises(ValueError, match="Data cannot be empty"):
            style.scale_data([])

    def test_single_data_point(self):
        """Test rendering a single data point."""
        style = spark.BrailleLineGraphStyle(height=3)
        result = style.scale_data([42])

        # Should have height rows
        assert len(result) == 3
        # Width should be 1 (1 data point = 2 pixels, but ceiling(2/2) = 1 char)
        assert len(result[0]) == 1

        # All characters should be braille (U+2800-U+28FF)
        for row in result:
            for char in row:
                assert 0x2800 <= ord(char) <= 0x28FF, f"Character {char} should be braille"

    def test_flat_line_all_same_values(self):
        """Test rendering when all values are the same."""
        style = spark.BrailleLineGraphStyle(height=4)
        result = style.scale_data([5, 5, 5, 5])

        assert len(result) == 4

        # All characters should be braille
        for row in result:
            for char in row:
                assert 0x2800 <= ord(char) <= 0x28FF

        # Should have some non-empty braille characters (not all U+2800)
        non_empty_count = sum(1 for row in result for char in row if ord(char) != 0x2800)
        assert non_empty_count > 0, "Flat line should have some filled dots"

    def test_increasing_line(self):
        """Test rendering an increasing line."""
        style = spark.BrailleLineGraphStyle(height=5)
        result = style.scale_data([1, 2, 3, 4, 5])

        assert len(result) == 5

        # All characters should be braille
        for row in result:
            for char in row:
                assert 0x2800 <= ord(char) <= 0x28FF

        # Should have filled dots (non-empty chars)
        non_empty_count = sum(1 for row in result for char in row if ord(char) != 0x2800)
        assert non_empty_count > 0, "Increasing line should have filled dots"

    def test_decreasing_line(self):
        """Test rendering a decreasing line."""
        style = spark.BrailleLineGraphStyle(height=5)
        result = style.scale_data([5, 4, 3, 2, 1])

        assert len(result) == 5

        # All characters should be braille
        for row in result:
            for char in row:
                assert 0x2800 <= ord(char) <= 0x28FF

    def test_zigzag_pattern(self):
        """Test rendering a zigzag pattern."""
        style = spark.BrailleLineGraphStyle(height=5)
        result = style.scale_data([1, 10, 1, 10, 1])

        assert len(result) == 5

        # Should have non-empty characters
        non_empty_count = sum(1 for row in result for char in row if ord(char) != 0x2800)
        assert non_empty_count > 0, "Zigzag should have filled dots"

    def test_graph_dimensions(self):
        """Test that graph has correct dimensions."""
        style = spark.BrailleLineGraphStyle(height=4)
        result = style.scale_data([1, 2, 3, 4, 5, 6])

        # Height should match
        assert len(result) == 4, "Graph should have correct height"

        # Width is ceil(len(data) / 2) since each braille char is 2 pixels wide
        # and we use 1 pixel per data point
        expected_width = 3  # ceil(6 / 2) = 3
        assert all(len(row) == expected_width for row in result), "All rows should have correct width"

    def test_braille_range(self):
        """Test that all output characters are valid braille."""
        style = spark.BrailleLineGraphStyle(height=10)
        result = style.scale_data([1, 5, 2, 8, 3, 7, 4, 9, 2, 6])

        for row in result:
            for char in row:
                code = ord(char)
                assert 0x2800 <= code <= 0x28FF, f"Character U+{code:04X} is not a braille pattern"

    def test_str_representation(self):
        """Test string representation of the style."""
        style = spark.BrailleLineGraphStyle(height=8)
        assert str(style) == "Braille Line Graph Style (height=8)"

    def test_verbose_parameter(self):
        """Test that verbose parameter is accepted (even if unused)."""
        style = spark.BrailleLineGraphStyle()
        result = style.scale_data([1, 2, 3], verbose=True)
        assert result is not None

    def test_two_points(self):
        """Test rendering two points."""
        style = spark.BrailleLineGraphStyle(height=3)
        result = style.scale_data([1, 10])

        assert len(result) == 3

        # Should have non-empty characters drawing the line
        non_empty_count = sum(1 for row in result for char in row if ord(char) != 0x2800)
        assert non_empty_count > 0, "Two-point graph should have filled dots"

    def test_returns_2d_list(self):
        """Test that scale_data returns a 2D list."""
        style = spark.BrailleLineGraphStyle(height=5)
        result = style.scale_data([1, 2, 3, 4, 5])

        assert isinstance(result, list)
        assert all(isinstance(row, list) for row in result)
        assert all(isinstance(char, str) for row in result for char in row)

    def test_minimum_height(self):
        """Test that height=1 works correctly."""
        style = spark.BrailleLineGraphStyle(height=1)
        result = style.scale_data([1, 2, 3])

        assert len(result) == 1
        # Width is ceil(3 / 2) = 2 braille characters
        assert len(result[0]) == 2


# Color Support Tests

class TestColorSupport:
    """Tests for ANSI color support functionality."""

    def test_get_gradient_color_low_value(self):
        """Test gradient returns red-ish color for low values."""
        color = spark.get_gradient_color(0.0)
        assert "\033[38;5;196m" in color  # Red

    def test_get_gradient_color_high_value(self):
        """Test gradient returns green-ish color for high values."""
        color = spark.get_gradient_color(1.0)
        assert "\033[38;5;46m" in color  # Green

    def test_get_gradient_color_mid_value(self):
        """Test gradient returns yellow-ish color for mid values."""
        color = spark.get_gradient_color(0.5)
        assert "\033[38;5;" in color  # Should be in yellow range

    def test_get_gradient_color_clamps_below_zero(self):
        """Test gradient clamps values below 0."""
        color = spark.get_gradient_color(-0.5)
        assert "\033[38;5;196m" in color  # Should be red (0.0)

    def test_get_gradient_color_clamps_above_one(self):
        """Test gradient clamps values above 1."""
        color = spark.get_gradient_color(1.5)
        assert "\033[38;5;46m" in color  # Should be green (1.0)

    def test_apply_color_single_line_gradient(self):
        """Test applying gradient color to single-line output."""
        data_points = ["▁", "▃", "▅", "▆", "█"]
        original_data = [1, 3, 5, 7, 9]
        result = spark.apply_color_to_output(data_points, original_data, "gradient")

        assert len(result) == 5
        # Each character should contain ANSI codes
        for char in result:
            assert "\033[" in char
            assert spark.ANSI_RESET in char

    def test_apply_color_single_line_solid_color(self):
        """Test applying solid color to single-line output."""
        data_points = ["▁", "▃", "▅"]
        original_data = [1, 5, 9]
        result = spark.apply_color_to_output(data_points, original_data, "cyan")

        assert len(result) == 3
        for char in result:
            assert spark.COLOR_CODES["cyan"] in char
            assert spark.ANSI_RESET in char

    def test_apply_color_multi_line(self):
        """Test applying color to multi-line output."""
        data_points = [["a", "b"], ["c", "d"]]
        original_data = [1, 9]
        result = spark.apply_color_to_output(data_points, original_data, "gradient")

        assert len(result) == 2
        assert len(result[0]) == 2
        # First column should be red-ish (low value)
        assert "\033[38;5;196m" in result[0][0]
        # Second column should be green-ish (high value)
        assert "\033[38;5;46m" in result[0][1]

    def test_apply_color_preserves_whitespace(self):
        """Test that whitespace characters are not colorized."""
        data_points = [" ", "▁", " "]
        original_data = [1, 5, 9]
        result = spark.apply_color_to_output(data_points, original_data, "cyan")

        # Whitespace should not have color codes
        assert result[0] == " "
        assert result[2] == " "
        # Non-whitespace should have color
        assert spark.COLOR_CODES["cyan"] in result[1]

    def test_apply_color_empty_data(self):
        """Test that empty data returns unchanged output."""
        data_points = ["a", "b"]
        result = spark.apply_color_to_output(data_points, [], "gradient")
        assert result == data_points

    def test_all_color_schemes_valid(self):
        """Test that all defined color schemes work."""
        data_points = ["▁", "█"]
        original_data = [1, 9]

        for scheme in ["gradient", "green", "cyan", "red", "blue", "magenta", "yellow"]:
            result = spark.apply_color_to_output(data_points, original_data, scheme)
            assert len(result) == 2
            # Should have ANSI codes
            assert "\033[" in result[1]

    def test_gradient_produces_different_colors(self):
        """Test that gradient produces different colors for different values."""
        data_points = ["▁", "█"]
        original_data = [1, 100]
        result = spark.apply_color_to_output(data_points, original_data, "gradient")

        # The two characters should have different color codes
        assert result[0] != result[1]
