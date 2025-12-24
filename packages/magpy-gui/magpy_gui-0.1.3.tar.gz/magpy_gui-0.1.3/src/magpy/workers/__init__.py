"""MagPy workers - QThread workers for long-running operations."""

from magpy.workers.detection_worker import (
    BatchDetectionResult,
    DetectionConfig,
    DetectionResult,
    DetectionWorker,
    DetectorType,
    SingleFileDetectionWorker,
)

__all__ = [
    "DetectionWorker",
    "SingleFileDetectionWorker",
    "DetectionConfig",
    "DetectionResult",
    "BatchDetectionResult",
    "DetectorType",
]
