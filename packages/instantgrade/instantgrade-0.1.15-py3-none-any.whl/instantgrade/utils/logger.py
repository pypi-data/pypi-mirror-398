import logging
from pathlib import Path


class ColorFormatter(logging.Formatter):
    """Adds colored output for Jupyter and terminal readability."""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[37m",  # White
        "SUCCESS": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[41m",  # Red background
    }
    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        msg = super().format(record)
        return f"{color}{msg}{self.RESET}"


def setup_logger(level="normal", log_dir="./logs"):
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "instantgrade.log"

    logger = logging.getLogger("instantgrade")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    # prevent duplicate handlers during multiple runs
    if not logger.handlers:
        # console handler
        ch = logging.StreamHandler()
        if level == "debug":
            ch.setLevel(logging.DEBUG)
        elif level == "silent":
            ch.setLevel(logging.ERROR)
        else:
            ch.setLevel(logging.INFO)
        logger.addHandler(ch)

        # file handler
        fh = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger
