"""
Initialization of metrics data module.
"""
from edgefirst.validator.metrics.data.label import (DetectionLabelData,
                                                    SegmentationLabelData)
from edgefirst.validator.metrics.data.stats import (DetectionStats,
                                                    SegmentationStats)
from edgefirst.validator.metrics.data.metrics import Metrics, MultitaskMetrics
from edgefirst.validator.metrics.data.plots import Plots, MultitaskPlots
