"""
Python logger settings.
Uses ENV variables to control the log level:
from simple_logging import make_logger
my_logger = make_logger("MY_KEY")
my_logger.trace2("message")
run with:
MY_KEY=4 python blabla.py

"""
from __future__ import annotations
import os
import sys
import logging
from pathlib import Path
from colorama import Fore, Back, Style

T1 = logging.TRACE = logging.DEBUG - 1
T2 = logging.TRACE2 = logging.DEBUG - 2
logging.addLevelName(T1, "TRACE")
logging.addLevelName(T2, "DGB3")

STR_LEVELS = ["DEBUG", "TRACE", "TRACE2", "INFO", "WARNING", "ERROR", "CRITICAL"]
_PRE_FILE = "[%(asctime)s %(name)s-%(levelname)s]" # for files we always put everything as there's no colors :)
_PRE = "[%(asctime)s %(name)s]" # don't put levelname in printed prefix as we ahave colors.
_POST = "(%(filename)s:%(funcName)s:%(lineno)d)"

def _colorize(msg: str) -> str:
    _colors = {
        "cyan": Fore.CYAN,
        "magenta": Fore.MAGENTA,
        "red": Fore.RED,
        "green": Fore.GREEN,
        "yellow": Fore.YELLOW,
        "back_red": Back.RED,
        "back_cyan": Back.CYAN,
    }
    def _get_next(msg: str, replacements: dict[str, str]) -> str:
        for replacement in replacements.keys():
            if msg[0: len(replacement)] == replacement:
                return replacement
        raise RuntimeError(f"Found no next color in {msg} out of {list(replacements)}")

    active_color = None
    new_message = []
    i = 0
    while i < len(msg):
        if msg[i] == "<":
            assert active_color is None or msg[i + 1] == "/", f"Use </color> before starting a new color: {msg}"
            _color = _get_next(msg[i + 2:], _colors) if active_color else _get_next(msg[i + 1:], _colors)
            assert active_color is None or _color == active_color, f"Active color: {active_color}. Got: {_color}"
            skip = len(_color) + 1 + (active_color is not None)
            assert msg[i + skip] == ">", f"Expected <color>(ch {i}), got: {msg}"
            new_message.append((_colors[_color] if active_color is None else Style.RESET_ALL))
            active_color = None if active_color is not None else _color
            i += skip + 1
        else:
            new_message.append(msg[i])
            i += 1
    return "".join(new_message)

def _get_default_formats(pre: str, post: str):
    return {
        "DEBUG": _colorize(f"<cyan>{pre}</cyan> %(message)s <yellow>{post}</yellow>"),
        "TRACE": _colorize(f"<back_cyan>{pre}</back_cyan> %(message)s <yellow>{post}</yellow>"),
        "TRACE2": _colorize(f"<magenta>{pre}</magenta> %(message)s <yellow>{post}</yellow>"),
        "INFO": _colorize(f"<green>{pre}</green> %(message)s <yellow>{post}</yellow>"),
        "WARNING": _colorize(f"<yellow>{pre}</yellow> %(message)s <yellow>{post}</yellow>"),
        "ERROR": _colorize(f"<red>{pre}</red> %(message)s <yellow>{post}</yellow>"),
        "CRITICAL": _colorize(f"<back_red>{pre}</back_red> %(message)s <yellow>{post}</yellow>"),
    }

class LoggezLogger(logging.Logger):
    """small interface-like class on top of the default logger for the extra methods"""
    def add_file_handler(self, path: str):
        """adds file handler"""
    def remove_file_handler(self):
        """Removes file handler"""
    def get_file_handler(self) -> logging.FileHandler:
        """Gets the file handler. Must be called after add_file_handler"""

class _FileHandler(logging.FileHandler):
    """same as filehandler but create the file on emit so we don't end up with empty files"""
    def emit(self, record):
        Path(self.baseFilename).parent.mkdir(exist_ok=True, parents=True)
        return super().emit(record)

def _add_file_handler(_logger: logging.Logger, path: str):
    if any(isinstance(handler, logging.FileHandler) for handler in _logger.handlers):
        _logger.trace("File handler exists already. Removing and replacing.")
        _remove_file_handler(_logger)
    _logger.trace(f"Adding file handler to this logger ({_logger.name}) to '{path}'")
    _logger.addHandler(logging.FileHandler(path))

def _remove_file_handler(_logger: logging.Logger):
    fh = [handler for handler in _logger.handlers if isinstance(handler, logging.FileHandler)]
    assert len(fh) == 1, _logger.handlers
    _logger.trace(f"Removing FileHandler: {fh[0]}")
    _logger.removeHandler(fh[0])

def _get_file_handler(_logger: logging.LoggerAdapter) -> logging.FileHandler:
    fh = [handler for handler in _logger.handlers if isinstance(handler, logging.FileHandler)]
    assert len(fh) == 1, _logger.handlers
    return fh[0]

class CustomFormatter(logging.Formatter):
    """Custom formatting for logger."""
    def __init__(self, formats, *args, **kwargs):
        self.formats = formats
        super().__init__(*args, **kwargs)

    def format(self, record):
        log_fmt = self.formats[record.levelno]
        formatter = logging.Formatter(log_fmt)
        formatter.formatTime = self.formatTime
        return formatter.format(record)

    # here we define the time format.
    def formatTime(self, record, datefmt=None):
        return super().formatTime(record, "%Y-%m-%dT%H:%M:%S")

def make_logger(key: str, exists_ok: bool=False, log_file: Path | str | None=None) -> LoggezLogger:
    ENV_KEY = f"{key}_LOGLEVEL"
    # defaults to -1 (no logger!).
    env_var = int(os.environ[ENV_KEY]) if ENV_KEY in os.environ else 1

    # we need numbers below 5 (last logging module used number)
    try:
        log_levels = {
            0: logging.NOTSET,
            1: logging.INFO,
            2: logging.DEBUG,
            3: logging.TRACE,
            4: logging.TRACE2,
        }
        loglvl = log_levels[env_var]
    except KeyError:
        sys.stderr.write(f"You tried to use {key}_LOGLEVEL={env_var}. You need to set it between -1 and 4\n")
        sys.exit(1)

    # add the custom ones in the logger
    if key in (X := logging.Logger.manager.loggerDict):
        if not exists_ok:
            raise ValueError(f"'{key}' exists in {list(X.keys())} already.\n")
        else:
            del logging.Logger.manager.loggerDict[key]

    # instantiate logger and set log level
    new_logger: logging.Logger = logging.getLogger(key)
    new_logger.setLevel(loglvl)
    new_logger.trace = lambda msg, *args: (new_logger._log(T1, msg, args=args) if loglvl > 0 and loglvl <= T1 else "")
    new_logger.trace2 = lambda msg, *args: (new_logger._log(T2, msg, args=args) if loglvl > 0 and loglvl <= T2 else "")
    # add custom formatter to logger
    handler = logging.StreamHandler()

    # [TIME:LEVEL] Message [FILE:FUNC:LINE]. We can update some other format here easily:
    # LOGGEZ_PRE=stuff ./app or even LOGGEZ_INFO_MESSAGE=[custom pre]msg[custom post]. Change LOGGEZ with ur name.
    default_formats = _get_default_formats(os.getenv(f"{key}_PRE", _PRE), os.getenv(f"{key}_POST", _POST))
    formats = {getattr(logging, k): os.getenv(f"{key}_{k}_MESSAGE", default_formats[k]) for k in STR_LEVELS}
    handler.setFormatter(CustomFormatter(formats))
    new_logger.addHandler(handler)
    new_logger.add_file_handler = lambda path: _add_file_handler(new_logger, path)
    new_logger.remove_file_handler = lambda: _remove_file_handler(new_logger)
    new_logger.get_file_handler = lambda: _get_file_handler(new_logger)

    if log_file is not None:
        file_handler = _FileHandler(log_file, mode="a", delay=True) # delay=True doesn't open the file yet.
        file_handler.setLevel(logging.DEBUG) # log everything to file if provided.
        pre_file, post_file = os.getenv(f"{key}_PRE_FILE", _PRE_FILE), os.getenv(f"{key}_POST_FILE", _POST)
        file_default_format = (f"{pre_file} %(message)s {post_file}")
        file_formats = {getattr(logging, k): file_default_format for k in STR_LEVELS}
        file_handler.setFormatter(CustomFormatter(file_formats))
        new_logger.addHandler(file_handler)

    return new_logger

loggez_logger = make_logger("LOGGEZ")
