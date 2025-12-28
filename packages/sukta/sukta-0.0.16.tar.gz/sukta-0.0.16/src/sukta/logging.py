import logging
from pathlib import Path
from typing import Literal, Optional, OrderedDict, Union

from rich.logging import RichHandler

LOG_LEVEL = Literal["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Logger(logging.Logger):
    name: Optional[str] = None
    path: Union[str, Path, None] = None

    @classmethod
    def getLogger(
        cls,
        name: str,
        path: Union[str, Path, None] = None,
        level: LOG_LEVEL = "INFO",
    ) -> "Logger":
        logger = Logger(logging.getLogger(name))
        logger.name = name
        logger.path = path
        if not logger.handlers:
            # terminal handler
            xterm_handler = RichHandler(rich_tracebacks=True, markup=True)
            xterm_handler.setLevel(level)
            xterm_handler.setFormatter(
                logging.Formatter(fmt="%(message)s", datefmt="[%c]")
            )
            logger.addHandler(xterm_handler)

            # file handler
            if path is not None:
                log_path = Path(path)
                if log_path.is_dir():
                    log_path = log_path / f"{name}.log"
                file_handler = logging.FileHandler(log_path)
                file_handler.setLevel(level)
                file_handler.setFormatter(
                    logging.Formatter(
                        fmt="[%(asctime)s] [%(levelname)s] %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%SZ",
                    ),
                )
                logger.addHandler(file_handler)
            logger.propagate = False
        logger.setLevel(level)
        return logger

    @classmethod
    def num2pstr(cls, x: int | float, fmt: str = ".3f") -> str:
        """Convert number to pretty string with metric suffixes"""
        if x < 0:
            prefix = "-"
            x = -x
        else:
            prefix = ""
        suffix_table = OrderedDict(
            {
                "1e18": "E",
                "1e15": "P",
                "1e12": "T",
                "1e9": "G",
                "1e6": "M",
                "1e3": "K",
                "1e0": "",
                "1e-3": "m",
                "1e-6": "µ",
                "1e-9": "n",
                "1e-12": "p",
                "1e-15": "f",
                "1e-18": "a",
            }
        )
        suffix = ""
        for k, v in suffix_table.items():
            if x >= float(k):
                x /= max(k, 1e-9)
                suffix = v
                break
        return f"{prefix}{x:{fmt}}{suffix}"

    @classmethod
    def pstr2num(cls, s: str) -> float:
        """Convert pretty string with metric suffixes to number (might be lossy depending on fmt used!)"""
        suffix_table = {
            "E": 1e18,
            "P": 1e15,
            "T": 1e12,
            "G": 1e9,
            "M": 1e6,
            "K": 1e3,
            "": 1e0,
            "m": 1e-3,
            "µ": 1e-6,
            "u": 1e-6,  # allow 'u' as 'µ'
            "n": 1e-9,
            "p": 1e-12,
            "f": 1e-15,
            "a": 1e-18,
        }
        s = s.strip()
        if not s:
            raise ValueError("Empty string")
        # Find the position where the numeric part ends
        num_part = ""
        suffix_part = ""
        for i, char in enumerate(s):
            if char.isdigit() or char in ".-+":
                num_part += char
            else:
                suffix_part = s[i:].strip()
                break
        if not num_part:
            raise ValueError(f"No numeric part found in '{s}'")
        try:
            num_value = float(num_part)
        except ValueError as e:
            raise ValueError(f"Invalid numeric part '{num_part}' in '{s}'") from e
        if suffix_part not in suffix_table:
            raise ValueError(f"Unknown suffix '{suffix_part}' in '{s}'")
        return num_value * suffix_table[suffix_part]
