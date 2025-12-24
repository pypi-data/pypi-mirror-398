"""MagPy screens - multi-view workspace screens."""

from .base import BaseScreen
from .terminal import TerminalScreen
from .pipeline_screen import PipelineScreen
from .training_screen import TrainingScreen
from .batch_screen import BatchScreen

__all__ = [
    "BaseScreen",
    "TerminalScreen",
    "PipelineScreen",
    "TrainingScreen",
    "BatchScreen",
]