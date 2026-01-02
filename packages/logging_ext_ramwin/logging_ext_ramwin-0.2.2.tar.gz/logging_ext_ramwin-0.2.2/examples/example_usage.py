#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Xiang Wang <ramwin@qq.com>

"""
Example usage of DateBasedFileHandler
"""

import logging
import time
from logging_ext import DateBasedFileHandler


def setup_daily_logging():
    """Set up daily log rotation."""
    handler = DateBasedFileHandler(
        filename_pattern="logs/daily-%Y-%m-%d.log",
        backup_count=7  # Keep last 7 days
    )

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)

    logger = logging.getLogger("daily_app")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    return logger, handler


def setup_hourly_logging():
    """Set up hourly log rotation."""
    handler = DateBasedFileHandler(
        filename_pattern="logs/hourly-%Y-%m-%d_%H.log",
        backup_count=24  # Keep last 24 hours
    )

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)

    logger = logging.getLogger("hourly_app")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    return logger, handler


def main():
    """Demonstrate usage of DateBasedFileHandler."""

    print("=== Daily Logging Example ===")
    logger, handler = setup_daily_logging()

    # Log some messages
    logger.info("Application started")
    logger.debug("This is a debug message")
    logger.warning("This is a warning")
    logger.error("This is an error")

    # Simulate some time passing
    print("Logging some messages...")
    for i in range(5):
        logger.info(f"Working on task {i}")
        time.sleep(0.1)

    logger.info("Application finished")
    handler.close()

    print("\n=== Hourly Logging Example ===")
    logger2, handler2 = setup_hourly_logging()

    logger2.debug("Debug message from hourly logger")
    logger2.info("Info message from hourly logger")

    handler2.close()

    print("\n=== Concurrent Logging Example ===")
    from logging_ext import ConcurrentDateBasedFileHandler

    concurrent_handler = ConcurrentDateBasedFileHandler(
        filename_pattern="logs/concurrent-%Y-%m-%d_%H-%M.log",
        backup_count=3
    )

    concurrent_formatter = logging.Formatter(
        '%(asctime)s - %(process)d - %(thread)d - %(message)s'
    )
    concurrent_handler.setFormatter(concurrent_formatter)

    concurrent_logger = logging.getLogger("concurrent_app")
    concurrent_logger.setLevel(logging.INFO)
    concurrent_logger.addHandler(concurrent_handler)

    concurrent_logger.info("This is a concurrent log message")
    concurrent_handler.close()

    print("Examples completed. Check the 'logs' directory for output files.")


if __name__ == "__main__":
    main()
