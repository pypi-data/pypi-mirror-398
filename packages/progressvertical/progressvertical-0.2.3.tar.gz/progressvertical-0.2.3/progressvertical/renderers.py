import sys
from .color_manager import ColorManager

class VerticalProgressRenderer:
    def __init__(self, height=10, spacing=3):
        self.height = height
        self.spacing = spacing
        self.bar_width = 3  
        self._first_render = True
        self._lines_rendered = 0

    def _move_cursor_up(self, lines):
        sys.stdout.write(f"\033[{lines}A")

    def _clear_rendered_lines(self):
        if self._lines_rendered > 0:
            self._move_cursor_up(self._lines_rendered)
            sys.stdout.write("\033[J")
            self._lines_rendered = 0

    def _align_element(self, text, width):
        text = str(text)
        if len(text) > width:
            text = text[:width]
        padding = (width - len(text)) // 2
        return " " * padding + text + " " * (width - len(text) - padding)

    def render(self, progress_data):
        lines_to_render = self.height + 2  # barras + labels + porcentagens
        
        if self._first_render:
            print("\n" * lines_to_render)
            self._move_cursor_up(lines_to_render)
            self._first_render = False
        else:
            self._clear_rendered_lines()
        
        for line in range(self.height, 0, -1):
            line_str = ""
            for i, data in enumerate(progress_data):
                prefix = " " * (self.spacing if i > 0 else 1)
                block = '▓▓▓' if line <= data['progress'] else '   '
                color = f"{data.get('fore_color','')}{data.get('back_color','')}{data.get('style','')}"
                line_str += f"{prefix}{color}{block}{ColorManager.RESET}"
            print(line_str)
        labels_line = ""
        for i, data in enumerate(progress_data):
            prefix = " " * (self.spacing if i > 0 else 1)
            aligned_label = self._align_element(data['label'], self.bar_width)
            labels_line += f"{prefix}{aligned_label}"
        print(labels_line)
        percent_line = ""
        for i, data in enumerate(progress_data):
            prefix = " " * (self.spacing if i > 0 else 1)
            pct = min(100, (data['progress']/self.height)*100)
            color = f"{data.get('fore_color','')}{data.get('style','')}"
            pct_text = f"{pct:.0f}%"
            aligned_pct = self._align_element(pct_text, self.bar_width)
            percent_line += f"{prefix}{color}{aligned_pct}{ColorManager.RESET}"
        print(percent_line)
        sys.stdout.flush()
        self._lines_rendered = lines_to_render
