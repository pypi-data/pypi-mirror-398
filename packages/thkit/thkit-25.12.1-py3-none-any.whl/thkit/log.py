import logging
import time
from pathlib import Path

from thkit.markup import TextDecor


#####ANCHOR: Customize Logger with colors
class ColorLogger(logging.Logger):
    """Logger subclass that supports `color` argument for console output."""

    def _log_with_color(self, level, msg, *args, color: str | None = None, **kwargs):
        ### Log plain text (for file handler only)
        super().log(level, msg, *args, **kwargs)

        ### Print Colored message to console
        theme = {
            "info": "white",
            "warning": "yellow",
            "error": "red",
            "critical": "red",
            "debug": "green",
        }
        if color is not None:
            colored_msg = TextDecor(msg).mkcolor(color)
        elif level >= logging.ERROR:
            colored_msg = TextDecor(msg).mkcolor(theme["error"])
        elif level >= logging.WARNING:
            colored_msg = TextDecor(msg).mkcolor(theme["warning"])
        elif level >= logging.INFO:
            colored_msg = TextDecor(msg).mkcolor(theme["info"])
        else:
            colored_msg = msg  # no color

        time_str = TextDecor(time.strftime("%b%d %H:%M")).mkcolor("bright_black")

        for key, color in zip(theme.keys(), ["green", "yellow", "red", "red", "green"]):
            if level == getattr(logging, key.upper()):
                level_str = TextDecor(f"{key.upper()}").mkcolor(color)
                break
        print(f"{time_str} {level_str}: {colored_msg}")  # type: ignore[unbound]
        return

    def info(self, msg, *args, color: str | None = None, **kwargs):
        self._log_with_color(logging.INFO, msg, *args, color=color, **kwargs)

    def warning(self, msg, *args, color: str | None = None, **kwargs):
        self._log_with_color(logging.WARNING, msg, *args, color=color, **kwargs)

    def error(self, msg, *args, color: str | None = None, **kwargs):
        self._log_with_color(logging.ERROR, msg, *args, color=color, **kwargs)


def create_logger(
    name: str | None = None,
    logfile: str | None = None,
    level: str = "INFO",
    level_logfile: str | None = None,
) -> ColorLogger:
    """Create a logger that supports `color` argument per message, to colorize console output and plain-text logfile."""
    logging.setLoggerClass(ColorLogger)
    logger = logging.getLogger(name or __name__)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    if not logger.hasHandlers():
        ### File handler only (no console handler, as ColorLogger prints to console directly)
        if logfile is not None:
            Path(logfile).parent.mkdir(parents=True, exist_ok=True)
            fh = logging.FileHandler(logfile, mode="a")
            fh.setLevel(getattr(logging, (level_logfile or level).upper(), logging.INFO))
            fmt = logging.Formatter("%(asctime)s | %(levelname)s: %(message)s", "%Y%b%d %H:%M:%S")
            fh.setFormatter(fmt)
            logger.addHandler(fh)
    return logger  # type: ignore


def write_to_logfile(logger: logging.Logger, text: str):
    """Retrieve logfile name from logger and write text to it. Useful when want to write unformat text to the same logfile used by logger."""
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            logfile = handler.baseFilename
            with open(logfile, "a") as f:
                f.write(text)
    return
