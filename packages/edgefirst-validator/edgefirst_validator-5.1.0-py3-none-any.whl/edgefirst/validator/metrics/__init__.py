"""
Initialization of metrics module.
"""
from edgefirst.validator.metrics.data.label import (DetectionLabelData,
                                                    SegmentationLabelData)
from edgefirst.validator.metrics.data.stats import (DetectionStats,
                                                    SegmentationStats)
from edgefirst.validator.metrics.data.plots import Plots, MultitaskPlots
from edgefirst.validator.metrics.data.metrics import Metrics, MultitaskMetrics
from edgefirst.validator.metrics.detection import DetectionMetrics
from edgefirst.validator.metrics.segmentation import SegmentationMetrics
