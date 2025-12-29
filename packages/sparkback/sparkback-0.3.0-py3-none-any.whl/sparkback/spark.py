# -*- coding: utf-8 -*-

"""
This module provides functionalities to visualize numerical data in the terminal.

It includes different styles of visualization, data can be represented in
default, block, ascii, numeric, braille, and arrows styles.

The module can also compute and print basic statistics about the data if required.

Functions included are:
- print_stats: Compute and format basic statistics from the given data.
- scale_data: Scale the data according to the selected ticks style.
- print_ansi_spark: Print the list of data points in the ANSI terminal.
- main: Main function that parses command line arguments and calls the corresponding functions.

Example usage:

    python3 this_file.py 1.0 2.5 3.3 4.7 3.5 --ticks="block" --stats
"""
import argparse
import statistics
from typing import List, Union, Tuple

# ANSI color constants
ANSI_RESET = "\033[0m"

COLOR_CODES = {
    "green": "\033[32m",
    "cyan": "\033[36m",
    "red": "\033[31m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "yellow": "\033[33m",
}

# 256-color codes for gradient (red → yellow → green)
# Red: 196, Orange: 208, Yellow: 220, Light green: 118, Green: 46
GRADIENT_COLORS = [196, 202, 208, 214, 220, 190, 154, 118, 82, 46]


def get_gradient_color(normalized_value: float) -> str:
    """
    Return ANSI 256-color escape code for a normalized value (0.0 to 1.0).

    Maps values from red (low) through yellow (mid) to green (high).

    Args:
        normalized_value: A float between 0.0 and 1.0.

    Returns:
        ANSI escape code string for the corresponding color.
    """
    # Clamp value to valid range
    normalized_value = max(0.0, min(1.0, normalized_value))
    # Map to index in gradient
    index = int(normalized_value * (len(GRADIENT_COLORS) - 1))
    color_code = GRADIENT_COLORS[index]
    return f"\033[38;5;{color_code}m"


def apply_color_to_output(
    data_points: Union[List[str], List[List[str]]],
    original_data: List[float],
    color_scheme: str,
) -> Union[List[str], List[List[str]]]:
    """
    Apply ANSI colors to styled output based on original data values.

    Args:
        data_points: The styled output (1D list for single-line, 2D for multi-line).
        original_data: The original numerical data used to determine colors.
        color_scheme: The color scheme to use ('gradient' or a color name).

    Returns:
        The data_points with ANSI color codes applied.
    """
    if not original_data:
        return data_points

    min_val = min(original_data)
    max_val = max(original_data)
    range_val = max_val - min_val if max_val != min_val else 1.0

    def get_color(value: float) -> str:
        """Get the color code for a given value."""
        if color_scheme == "gradient":
            normalized = (value - min_val) / range_val
            return get_gradient_color(normalized)
        else:
            return COLOR_CODES.get(color_scheme, COLOR_CODES["green"])

    def colorize(char: str, color: str) -> str:
        """Wrap a character with color codes."""
        if char.strip():  # Only colorize non-whitespace
            return f"{color}{char}{ANSI_RESET}"
        return char

    # Check if multi-line (2D list) or single-line (1D list)
    if data_points and isinstance(data_points[0], list):
        # Multi-line graph: color each column based on corresponding data point
        result = []
        for row in data_points:
            colored_row = []
            for col_idx, char in enumerate(row):
                # Map column index to data index
                # For braille-line: each data point maps to one column
                # For line/multiline: same mapping
                if col_idx < len(original_data):
                    color = get_color(original_data[col_idx])
                else:
                    color = get_color(original_data[-1])  # Use last value for overflow
                colored_row.append(colorize(char, color))
            result.append(colored_row)
        return result
    else:
        # Single-line: each character corresponds to a data point
        result = []
        for idx, char in enumerate(data_points):
            if idx < len(original_data):
                color = get_color(original_data[idx])
            else:
                color = get_color(original_data[-1])
            result.append(colorize(char, color))
        return result


def print_stats(data):
    """
    Compute and format basic statistics from the given data.

    Args:
        data (list): A list of numerical data.

    Returns:
        str: A string of formatted statistics.
    """
    if not data or len(data) < 2:
        raise ValueError("At least two data points are required to compute statistics")

    if not all(isinstance(item, (int, float)) for item in data):
        raise ValueError("All data points should be numeric")

    min_data = min(data)
    max_data = max(data)

    stats_str = (
        f"Minimum: {min_data}\n"
        f"Maximum: {max_data}\n"
        f"Mean: {statistics.mean(data)}\n"
        f"Standard Deviation: {statistics.stdev(data)}"
    )
    return stats_str


class AbstractStyle:
    """
    Base class that defines the interface for scaling data into different styles.
    """

    TICKS = None

    def scale_data(self, data, verbose=False):
        """
        Abstract method for scaling data according to the selected style.

        Args:
            data (list): A list of numerical data.
            verbose (bool): Whether to include additional information in the output.

        Returns:
            list: A list of symbols representing the scaled data.
        """
        raise NotImplementedError


class ArrowsStyle(AbstractStyle):
    """
    A style class that represents data using arrows for directionality.
    """

    TICKS = ("↓", "→", "↗", "↑")

    def scale_data(self, data, verbose=False):
        result = [self.TICKS[1]]  # Assumes no change at start
        for i in range(1, len(data)):
            if data[i] > data[i - 1]:
                result.append(self.TICKS[3])  # up arrow
            elif data[i] < data[i - 1]:
                result.append(self.TICKS[0])  # down arrow
            else:
                result.append(self.TICKS[1])  # right arrow for no change
        return result


class DefaultStyle(AbstractStyle):
    """
    A default style class that represents data using a set of unicode blocks.
    """

    TICKS = ("▁", "▂", "▃", "▄", "▅", "▆", "▇", "█")

    def scale_data(self, data, verbose=False):
        min_data = min(data)
        range_data = (max(data) - min_data) / (len(self.TICKS) - 1)
        if range_data == 0:
            return [self.TICKS[0] for _ in data]
        else:
            scaled_data = [self.TICKS[int(round((value - min_data) / range_data))] for value in data]
            return self.verbose_output(scaled_data) if verbose else scaled_data

    @staticmethod
    def verbose_output(scaled_data):
        """
        Constructs verbose output strings for the scaled data.

        Args:
            scaled_data (list): Scaled data points.

        Returns:
            list: Verbose description of the scaled data.
        """
        return [f"Data point {i} is {value}." for i, value in enumerate(scaled_data)]


class BlockStyle(DefaultStyle):
    """
    A style class that represents data using different block symbols.
    """

    TICKS = ("▏", "▎", "▍", "▌", "▋", "▊", "▉", "█")


class AsciiStyle(DefaultStyle):
    """
    A style class that represents data using ASCII characters.
    """

    TICKS = (".", "o", "O", "#", "@")


class NumericStyle(DefaultStyle):
    """
    A style class that represents data using numerical characters.
    """

    TICKS = ("1", "2", "3", "4", "5")


class BrailleStyle(DefaultStyle):
    """
    A style class that represents data using Braille symbols.
    """

    TICKS = ("⣀", "⣤", "⣶", "⣿")


class MultiLineGraphStyle(AbstractStyle):
    """
    A style class that represents data as a multiline graph using Unicode characters.
    """

    def scale_data(self, data, verbose=False):
        min_data = min(data)
        max_data = max(data)
        range_data = max_data - min_data
        graph_height = 10  # Set graph height to 10 lines for better visibility

        if range_data == 0:
            return [["─" * len(data)] * graph_height]  # Uniform line if no variation

        scaled_data = [int((value - min_data) / range_data * (graph_height - 1)) for value in data]

        # Initialize the graph canvas
        graph = [[" " for _ in range(len(data))] for _ in range(graph_height)]

        # Place the points on the graph
        for idx, height in enumerate(scaled_data):
            for y in range(graph_height):
                graph[y][idx] = "█" if y >= graph_height - height else " "

        return graph

    def __str__(self):
        return "Multiline Graph Style"


class LineGraphStyle(AbstractStyle):
    """
    A style class that draws connected line graphs using Unicode box-drawing characters.

    This style connects consecutive data points with lines, supporting horizontal,
    vertical, and diagonal segments. The graph is rendered on a configurable height
    canvas using Unicode characters: ─│╱╲● for different line directions.
    """

    def __init__(self, height: int = 10) -> None:
        """
        Initialize the LineGraphStyle with a specified graph height.

        Args:
            height: The number of rows in the graph canvas. Must be >= 2.

        Raises:
            ValueError: If height is less than 2.
        """
        if height < 2:
            raise ValueError("Graph height must be at least 2")
        self.height = height

    def scale_data(self, data: List[Union[int, float]], verbose: bool = False) -> List[List[str]]:
        """
        Scale data and render as a connected line graph.

        Args:
            data: A list of numerical values to plot.
            verbose: If True, includes additional debug information (currently unused).

        Returns:
            A 2D list of strings representing the graph, with graph[0] as the top row.

        Raises:
            ValueError: If data is empty or contains non-numeric values.
        """
        if not data:
            raise ValueError("Data cannot be empty")

        if len(data) == 1:
            # Single point: draw just a point in the middle
            graph = [[" " for _ in range(1)] for _ in range(self.height)]
            mid_y = self.height // 2
            graph[mid_y][0] = "●"
            return graph

        # Scale data to fit within graph height
        min_val = min(data)
        max_val = max(data)
        range_val = max_val - min_val

        if range_val == 0:
            # All values are the same: draw horizontal line at midpoint
            y_pos = self.height // 2
            graph = [[" " for _ in range(len(data))] for _ in range(self.height)]
            for x in range(len(data)):
                graph[y_pos][x] = "─"
            # Mark endpoints
            graph[y_pos][0] = "●"
            graph[y_pos][len(data) - 1] = "●"
            return graph

        # Scale each value to [0, height-1], inverted so top of graph is max value
        scaled_points: List[int] = [int((val - min_val) / range_val * (self.height - 1)) for val in data]

        # Initialize the graph canvas
        graph: List[List[str]] = [[" " for _ in range(len(data))] for _ in range(self.height)]

        # Draw lines between consecutive points
        for i in range(len(scaled_points) - 1):
            x1, y1 = i, scaled_points[i]
            x2, y2 = i + 1, scaled_points[i + 1]

            # Invert y-coordinates so 0 is at top of graph
            y1_inv = self.height - 1 - y1
            y2_inv = self.height - 1 - y2

            self._draw_line(graph, x1, y1_inv, x2, y2_inv)

        # Mark endpoints
        first_y = self.height - 1 - scaled_points[0]
        last_y = self.height - 1 - scaled_points[-1]
        graph[first_y][0] = "●"
        graph[last_y][len(data) - 1] = "●"

        return graph

    def _draw_line(self, graph: List[List[str]], x1: int, y1: int, x2: int, y2: int) -> None:
        """
        Draw a line between two points on the graph canvas.

        Uses Unicode box-drawing characters to represent different line directions:
        - ─ for horizontal lines
        - │ for vertical lines
        - ╱ for diagonal up-right lines
        - ╲ for diagonal down-right lines

        Args:
            graph: The 2D graph canvas to draw on (modified in place).
            x1: Starting x-coordinate.
            y1: Starting y-coordinate.
            x2: Ending x-coordinate.
            y2: Ending y-coordinate.
        """
        dx = x2 - x1
        dy = y2 - y1

        # For adjacent x coordinates (dx=1), determine the character
        if dx == 1:
            if dy == 0:
                # Horizontal line
                if graph[y1][x1] == " ":
                    graph[y1][x1] = "─"
                if graph[y2][x2] == " ":
                    graph[y2][x2] = "─"
            elif dy > 0:
                # Going down (down-right diagonal)
                steps = abs(dy)
                for step in range(steps + 1):
                    y = y1 + step
                    if 0 <= y < len(graph):
                        if step == 0 or step == steps:
                            if graph[y][x1] == " ":
                                graph[y][x1] = "╲" if dy == 1 else "│"
                        else:
                            if graph[y][x1] == " ":
                                graph[y][x1] = "│"
            else:
                # Going up (up-right diagonal)
                steps = abs(dy)
                for step in range(steps + 1):
                    y = y1 - step
                    if 0 <= y < len(graph):
                        if step == 0 or step == steps:
                            if graph[y][x1] == " ":
                                graph[y][x1] = "╱" if dy == -1 else "│"
                        else:
                            if graph[y][x1] == " ":
                                graph[y][x1] = "│"

    def __str__(self) -> str:
        """Return a string representation of this style."""
        return f"Line Graph Style (height={self.height})"


class BrailleLineGraphStyle(AbstractStyle):
    """
    A style class that draws high-resolution line graphs using Unicode braille characters.

    Each braille character is a 2x4 dot matrix, providing 4x vertical resolution
    compared to regular character-based graphs. This creates smooth, btop-style
    visualizations suitable for terminal dashboards.

    The braille pattern (U+2800-U+28FF) uses this dot layout:
        1 4     bit 0  bit 3
        2 5  →  bit 1  bit 4
        3 6     bit 2  bit 5
        7 8     bit 6  bit 7
    """

    BRAILLE_BASE = 0x2800
    # Dot position to bit mapping for 2x4 braille grid [row][col]
    DOT_BITS = [
        [0x01, 0x08],  # row 0: dots 1,4
        [0x02, 0x10],  # row 1: dots 2,5
        [0x04, 0x20],  # row 2: dots 3,6
        [0x40, 0x80],  # row 3: dots 7,8
    ]

    def __init__(self, height: int = 10, filled: bool = False) -> None:
        """
        Initialize the BrailleLineGraphStyle with a specified graph height.

        Args:
            height: The number of braille character rows. Each row provides
                   4 pixels of vertical resolution. Must be >= 1.
            filled: If True, fills the area below the line (area chart style).
                   If False, draws only the line (default).

        Raises:
            ValueError: If height is less than 1.
        """
        if height < 1:
            raise ValueError("Graph height must be at least 1")
        self.height = height
        self.filled = filled

    def scale_data(self, data: List[Union[int, float]], verbose: bool = False) -> List[List[str]]:
        """
        Scale data and render as a high-resolution braille line graph.

        Args:
            data: A list of numerical values to plot.
            verbose: If True, includes additional debug information (currently unused).

        Returns:
            A 2D list of braille characters representing the graph,
            with graph[0] as the top row.

        Raises:
            ValueError: If data is empty.
        """
        if not data:
            raise ValueError("Data cannot be empty")

        # Pixel dimensions: each braille char is 2 wide x 4 tall
        # Use 1 pixel per data point for smooth, natural-looking graphs
        pixel_height = self.height * 4
        pixel_width = len(data)

        # Create pixel canvas (False = empty, True = filled)
        canvas: List[List[bool]] = [[False for _ in range(pixel_width)] for _ in range(pixel_height)]

        # Scale data to pixel y-coordinates
        min_val = min(data)
        max_val = max(data)
        range_val = max_val - min_val

        if range_val == 0:
            # All values are the same: draw horizontal line at midpoint
            mid_y = pixel_height // 2
            for x in range(pixel_width):
                if self.filled:
                    # Fill from midpoint to bottom
                    for fill_y in range(mid_y, pixel_height):
                        canvas[fill_y][x] = True
                else:
                    canvas[mid_y][x] = True
        else:
            # Scale each value to pixel coordinates
            # Map to [0, pixel_height-1], then invert so top = max
            scaled_points: List[Tuple[int, int]] = []
            for i, val in enumerate(data):
                # x-coordinate: 1 pixel per data point
                x = i
                # y-coordinate: scaled and inverted
                y_normalized = (val - min_val) / range_val
                y = int((1 - y_normalized) * (pixel_height - 1))
                scaled_points.append((x, y))

            if self.filled:
                # Fill area below each data point
                for x, y in scaled_points:
                    for fill_y in range(y, pixel_height):
                        if 0 <= fill_y < pixel_height and 0 <= x < pixel_width:
                            canvas[fill_y][x] = True
            else:
                # Draw lines between consecutive points
                for i in range(len(scaled_points) - 1):
                    x1, y1 = scaled_points[i]
                    x2, y2 = scaled_points[i + 1]
                    self._draw_line(canvas, x1, y1, x2, y2)

                # For single point, just draw the dot
                if len(scaled_points) == 1:
                    x, y = scaled_points[0]
                    if 0 <= y < pixel_height and 0 <= x < pixel_width:
                        canvas[y][x] = True

        return self._canvas_to_braille(canvas)

    def _draw_line(self, canvas: List[List[bool]], x1: int, y1: int, x2: int, y2: int) -> None:
        """
        Draw a line between two points on the pixel canvas using Bresenham's algorithm.

        Args:
            canvas: The 2D pixel canvas (modified in place).
            x1: Starting x-coordinate.
            y1: Starting y-coordinate.
            x2: Ending x-coordinate.
            y2: Ending y-coordinate.
        """
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        x, y = x1, y1
        while True:
            # Set pixel if within bounds
            if 0 <= y < len(canvas) and 0 <= x < len(canvas[0]):
                canvas[y][x] = True

            if x == x2 and y == y2:
                break

            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def _canvas_to_braille(self, canvas: List[List[bool]]) -> List[List[str]]:
        """
        Convert a pixel canvas to braille characters.

        Groups pixels into 2x4 blocks and maps each block to the corresponding
        braille character based on which dots are filled.

        Args:
            canvas: 2D boolean array of pixels.

        Returns:
            2D list of braille character strings.
        """
        pixel_height = len(canvas)
        pixel_width = len(canvas[0]) if canvas else 0

        # Output dimensions in braille characters
        char_height = (pixel_height + 3) // 4  # Ceiling division
        char_width = (pixel_width + 1) // 2

        result: List[List[str]] = []

        for char_row in range(char_height):
            row_chars: List[str] = []
            for char_col in range(char_width):
                # Calculate the braille character for this 2x4 block
                bits = 0
                for dot_row in range(4):
                    for dot_col in range(2):
                        pixel_y = char_row * 4 + dot_row
                        pixel_x = char_col * 2 + dot_col
                        if pixel_y < pixel_height and pixel_x < pixel_width:
                            if canvas[pixel_y][pixel_x]:
                                bits |= self.DOT_BITS[dot_row][dot_col]
                row_chars.append(chr(self.BRAILLE_BASE + bits))
            result.append(row_chars)

        return result

    def __str__(self) -> str:
        """Return a string representation of this style."""
        return f"Braille Line Graph Style (height={self.height})"


STYLES = {
    "default": DefaultStyle,
    "block": BlockStyle,
    "ascii": AsciiStyle,
    "numeric": NumericStyle,
    "braille": BrailleStyle,
    "arrows": ArrowsStyle,
    "multiline": MultiLineGraphStyle,
    "line": LineGraphStyle,
    "braille-line": BrailleLineGraphStyle,
}


def print_ansi_spark(data_points, verbose=False, style=None):
    """
    Print the list of data points in the ANSI terminal, formatted according to the specified style.

    Args:
        data_points (list or list of lists): A list of data points or a list of lists for multiline graphs.
        verbose (bool): Whether to print verbose output.
        style (str): The style of the graph, which could influence formatting details.
    """
    if isinstance(data_points[0], list):
        if verbose:
            for index, line in enumerate(data_points):
                print(f"Line {index+1}: {''.join(line)}")
        else:
            for line in data_points:
                print("".join(line))
    else:
        if verbose:
            for index, point in enumerate(data_points):
                print(f"Point {index+1}: {point}")
        else:
            print("".join(data_points))


def get_style_instance(style):
    """
    Returns an instance of the appropriate style class based on the given style name.

    Args:
        style (str): The name of the style to use.

    Returns:
        AbstractStyle: An instance of the corresponding style class.

    Raises:
        ValueError: If the given style name is not found in the available STYLES.
    """
    if style in STYLES:
        return STYLES[style]()
    else:
        raise ValueError(f"Invalid style: {style}")


def get_args():
    """
    Parses command line arguments for the script.

    Returns:
        argparse.Namespace: Parsed command line arguments.

    Command line options:
        numbers (float): Series of data to plot.
        --ticks (str): The style of ticks to use (default, block, ascii, numeric, braille, arrows).
        --stats (bool): Show statistics about the data.
        --verbose (bool): Show verbose representation of the data.
    """
    parser = argparse.ArgumentParser(description="Process numbers")
    parser.add_argument("numbers", metavar="N", type=float, nargs="+", help="series of data to plot")
    parser.add_argument(
        "--ticks",
        choices=STYLES.keys(),
        default="default",
        help="the style of ticks to use",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="show statistics about the data",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="show verbose representation of the data",
    )
    parser.add_argument(
        "--color",
        choices=["gradient", "green", "cyan", "red", "blue", "magenta", "yellow"],
        help="colorize output with specified color scheme",
    )
    return parser.parse_args()


def main():
    """
    Main function that parses command line arguments and calls the corresponding functions.
    """
    args = get_args()
    style_instance = get_style_instance(args.ticks)
    scaled_data = style_instance.scale_data(args.numbers, verbose=args.verbose)

    if args.color:
        scaled_data = apply_color_to_output(scaled_data, args.numbers, args.color)

    if args.stats:
        print(print_stats(args.numbers))

    print_ansi_spark(scaled_data, verbose=args.verbose)


if __name__ == "__main__":
    main()
