#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tsdbpy - Python TimescaleDB SDK
"""

__version__ = "0.3.3"
__author__ = "TaijiControl"

def get_version():
    return __version__

try:
    from loguru import logger as _logger
    _USING_LOGURU = True
except ImportError:
    import logging
    _logger = logging.getLogger("tsdbpy")
    if not _logger.handlers:
        import sys
        handler = logging.StreamHandler(sys.stderr)
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        _logger.addHandler(handler)
        _logger.setLevel(logging.INFO)
    _USING_LOGURU = False

logger = _logger
