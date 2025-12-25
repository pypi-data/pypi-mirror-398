"""
django-vtasks - High-performance task queue for Django.

This package provides a task queue system that extends Django's built-in
task framework with additional features like unique tasks, throttling,
and enhanced backend support.
"""

from .tasks import VTask, task

__all__ = ["task", "VTask"]
