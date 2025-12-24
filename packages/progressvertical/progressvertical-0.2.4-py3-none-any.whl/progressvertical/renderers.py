import sys
import math
from .color_manager import ColorManager


class VerticalProgressRenderer:
    """
    A vertical progress bar renderer for terminal display.
    
    This class draws multiple vertical progress bars side by side in the terminal,
    allowing visualization of different processes' progress simultaneously.

    Attributes:
        height (int): Maximum height of progress bars in terminal lines.
        spacing (int): Horizontal spacing between bars.
        bar_width (int): Width of each bar (fixed at 3 characters).
        _first_render (bool): Flag indicating if it's the first rendering.
        _lines_rendered (int): Number of lines rendered in the last update.

    Example:
        >>> renderer = VerticalProgressRenderer(height=5, spacing=2)
        >>> data = [
        ...     {"progress": 3.5, "label": "Task A", "fore_color": "\033[31m"},
        ...     {"progress": 2.0, "label": "Task B", "fore_color": "\033[32m"}
        ... ]
        >>> renderer.render(data)
    """

    def __init__(self, height=3, spacing=3):
        """
        Initializes the vertical progress bar renderer.

        Args:
            height (int, optional): Height of bars in terminal lines. 
                                   Default is 3.
            spacing (int, optional): Horizontal spacing between bars in characters.
                                    Default is 3.
        """
        self.height = height            
        self.spacing = spacing
        self.bar_width = 3
        self._first_render = True
        self._lines_rendered = 0

    def _move_cursor_up(self, lines):
        """Moves the terminal cursor up by the specified number of lines."""
        sys.stdout.write(f"\033[{lines}A")

    def _clear_rendered_lines(self):
        """Clears previously rendered lines from the terminal."""
        if self._lines_rendered > 0:
            self._move_cursor_up(self._lines_rendered)
            sys.stdout.write("\033[J")
            self._lines_rendered = 0

    def _align_element(self, text, width):
        """
        Centers text within a specified width.

        Args:
            text (str): Text to be centered.
            width (int): Total field width.

        Returns:
            str: Centered text with appropriate padding.
        """
        text = str(text)
        if len(text) > width:
            text = text[:width]
        padding = (width - len(text)) // 2
        return " " * padding + text + " " * (width - len(text) - padding)

    def render(self, progress_data):
        """
        Renders vertical progress bars in the terminal.

        The method draws three components for each bar:
        1. The vertical progress bar (filled with "▓▓▓" blocks)
        2. The label centered below the bar
        3. The progress percentage centered below the label

        Args:
            progress_data (list): List of dictionaries containing progress data.
                                 Each dictionary should contain:
                                    - "progress" (int/float): Progress value (0 to height)
                                    - "label" (str): Bar label
                                    - "fore_color" (str, optional): ANSI code for text color
                                    - "back_color" (str, optional): ANSI code for background color
                                    - "style" (str, optional): ANSI code for text style

        Notes:
            - Progress is normalized to the range [0, height]
            - Bars are drawn from bottom to top
            - Colors and styles are automatically reset after each element
            - Output is optimized to avoid flickering in the terminal
        """
        normalized_progress = [
            max(0, min(self.height, int(math.ceil(data["progress"]))))
            for data in progress_data
        ]

        max_progress = max(normalized_progress)
        lines_to_render = int(max_progress) + 2 

        if self._first_render:
            print("\n" * lines_to_render, end="")
            self._move_cursor_up(lines_to_render)
            self._first_render = False
        else:
            self._clear_rendered_lines()

    
        for line in range(max_progress, 0, -1):
            line_str = ""
            for i, data in enumerate(progress_data):
                prefix = " " * (self.spacing if i > 0 else 1)

                block = "▓▓▓" if line <= normalized_progress[i] else "   "
                color = (
                    f"{data.get('fore_color', '')}"
                    f"{data.get('back_color', '')}"
                    f"{data.get('style', '')}"
                )

                line_str += f"{prefix}{color}{block}{ColorManager.RESET}"

            print(line_str)

        
        labels_line = ""
        for i, data in enumerate(progress_data):
            prefix = " " * (self.spacing if i > 0 else 1)
            labels_line += f"{prefix}{self._align_element(data['label'], self.bar_width)}"
        print(labels_line)

        
        percent_line = ""
        for i, data in enumerate(progress_data):
            prefix = " " * (self.spacing if i > 0 else 1)

            pct = min(100, (data["progress"] / self.height) * 100)
            pct_text = f"{pct:.0f}%"
            aligned_pct = self._align_element(pct_text, self.bar_width)

            color = f"{data.get('fore_color', '')}{data.get('style', '')}"
            percent_line += f"{prefix}{color}{aligned_pct}{ColorManager.RESET}"

        print(percent_line)

        sys.stdout.flush()
        self._lines_rendered = lines_to_render
