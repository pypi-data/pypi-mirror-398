"""Module for display-related classes and functions."""

import datetime

from rich.color import ANSI_COLOR_NAMES, Color
from rich.progress import BarColumn, Progress
from rich.progress_bar import ProgressBar


#####ANCHOR Progress bar control
class ThangBar(Progress):
    """A class to extend functions of the [rich's progress bar](https://rich.readthedocs.io/en/latest/progress.html).

    The same as `rich.progress.Progress`, with additional methods:
        - `hide_bar()`: hide the progress bar.
        - `show_bar()`: show the progress bar.
        - `compute_eta()`: static method to compute estimated time of arrival (ETA) given number of iterations and time taken.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def hide_bar(self):
        """Hide all progress bars in the given Progress object."""
        for t in self.tasks:
            self.update(t.id, visible=False)
        self.refresh()
        return

    def show_bar(self):
        """Show all progress bars in the given Progress object."""
        for t in self.tasks:
            self.update(t.id, visible=True)
        self.refresh()
        return

    def align_etatext(self, width: int):
        """Align the ETA text to the given width for all tasks."""
        for t in self.tasks:
            eta_text = t.fields.get("eta_text", "")
            if eta_text.startswith("[ETA "):
                eta_text = eta_text.replace("[ETA", "").strip()  # remove prefix/spaces
                if width >= len(eta_text):
                    aligned_text = f"{eta_text:>{width}}"
                    self.update(t.id, eta_text=f"[ETA {aligned_text}")
        self.refresh()
        return

    @staticmethod
    def compute_eta(
        num_iters: int,
        iter_index: int,  # start from 0
        old_time: float | None = None,
        new_time: float | None = None,
    ) -> str:
        """Estimate remaining time."""
        text = ""
        if old_time is not None and new_time is not None:
            duration = new_time - old_time
            time_remain = duration * (num_iters - iter_index - 1)
            delta_str = str(datetime.timedelta(seconds=time_remain)).split(".", 2)[0]
            text = delta_str.replace(" days, ", "-").replace(" day, ", "-")
        return f"[ETA {text}]"


class DynamicBarColumn(BarColumn):
    ### Ref: https://github.com/Textualize/rich/blob/master/rich/progress.py#L646
    """Extend `BarColumn` that can read per-task fields 'complete_color', 'finished_color',... to customize colors.

    Args:
        The same as `rich.progress.BarColumn`, and following additional arguments:
        - complete_color (str): the color for completed part of the bar.
        - finished_color (str): the color for finished bar.
        - pulse_color (str): the color for pulsing bar.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def render(self, task) -> ProgressBar:
        """Gets a progress bar widget for a task."""
        complete_color = task.fields.get("complete_color", "bar.complete")
        finished_color = task.fields.get("finished_color", "bar.finished")
        pulse_color = task.fields.get("pulse_color", "bar.pulse")
        self.complete_style = complete_color
        self.finished_style = finished_color
        self.pulse_style = pulse_color
        return ProgressBar(
            total=max(0, task.total) if task.total is not None else None,
            completed=max(0, task.completed),
            width=None if self.bar_width is None else max(1, self.bar_width),
            pulse=not task.started,
            animation_time=task.get_time(),
            style=self.style,
            complete_style=self.complete_style,
            finished_style=self.finished_style,
            pulse_style=self.pulse_style,
        )


#####ANCHOR: Text modifier
class TextDecor:
    """A collection of text decoration utilities."""

    def __init__(self, text: str = "example"):
        self.text = text

    def fill_center(self, fill: str = "-", length: int = 60) -> str:
        """Return the text centered within a line of the given length, filled with `fill`."""
        return self.text.center(length, fill)

    def fill_left(
        self,
        margin: int = 15,
        fill_left: str = "-",
        fill_right: str = " ",
        length: int = 60,
    ) -> str:
        """Return the text left-aligned within a line of the given length, with left and right fills."""
        text = f"{(fill_left * margin)}{self.text}"
        return text.ljust(length, fill_right)

    def fill_box(self, fill: str = " ", sp: str = "\u01c1", length: int = 60) -> str:
        """Return a string centered in a box with side delimiters.

        Example:
        ```python
        TextDecor("hello").fill_box(fill="-", sp="|", length=20)
        "|-------hello-------|"
        ```

        Notes:
            - To input unicode characters, use the unicode escape sequence (e.g., "\u01c1" for a specific character). See [unicode-table]( https://symbl.cc/en/unicode-table) for more details.
                - ║ (Double vertical bar, `u2551`)
                - ‖ (Double vertical line, `u2016`)
                - ǁ (Latin letter lateral click, `u01C1`)
        """
        if len(sp) * 2 >= length:
            raise ValueError("Length must be greater than twice the side padding length")

        inner_width = length - 2 * len(sp)
        centered = self.text.center(inner_width, fill)
        return f"{sp}{centered}{sp}"

    def repeat(self, length: int) -> str:
        """Repeat the input string to a specified length."""
        text = self.text
        text = (text * ((length // len(text)) + 1))[:length]
        return text

    def mkcolor(self, color: str = "blue") -> str:
        """Return ANSI-colored text that works in terminal or Jupyter.

        Args:
            color (str, optional): Color name. Defaults to "blue". Supported string values include:
                - Color names: "black", "red", "green",...See [list here](https://github.com/Textualize/rich/blob/master/rich/color.py#L49)
                - Color ANSI codes: "#ff0000",... See codes [here](https://hexdocs.pm/color_palette/ansi_color_codes.html).
                - RGB codes: "rgb(255,0,0)",... See codes [here](https://en.wikipedia.org/wiki/ANSI_escape_code#8-bit).

        Notes:
            - Refer [rich](https://github.com/Textualize/rich/blob/master/rich/color.py)'s color scheme.
        """
        try:
            code = Color.parse(color).get_ansi_codes()
            if code is not None:
                code = code[0]
            else:
                raise Exception
        except Exception:
            print(f"WARNING: Color '{color}' not recognized — using white.")
            code = str(ANSI_COLOR_NAMES.get("white", 37))

        text = f"\033[{code}m{self.text}\033[0m"
        return text


#####ANCHOR: helper functions
def _index2color(index: int) -> str:
    """Map an integer index to a color name."""
    color_map = {
        0: "blue",
        1: "bright_yellow",
        2: "magenta",
        3: "cyan",
        4: "red",
        5: "green",
        6: "yellow",  # orange-like
    }
    ansi_colors = ANSI_COLOR_NAMES.copy()  # create a local copy
    ansi_colors.pop("black", None)  # remove black to avoid invisible text
    ### Add more colors from ansi_colors
    for idx, key in enumerate(ansi_colors.keys()):
        if key not in color_map.values():
            color_map[idx + 7] = key
    return color_map[int(index)]
