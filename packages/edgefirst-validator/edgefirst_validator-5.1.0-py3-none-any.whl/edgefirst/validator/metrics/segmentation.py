"""
Implements segmentation metrics for validation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple

import numpy as np

from edgefirst.validator.metrics import Metrics, Plots

if TYPE_CHECKING:
    from edgefirst.validator.evaluators import ValidationParameters
    from edgefirst.validator.metrics import (SegmentationStats,
                                             SegmentationLabelData)


class SegmentationMetrics:
    """
    Runs the metric computations for segmentation. The resulting metrics
    will be populated in the `Metrics` object that is created once initialized.

    This provides methods to calculate::

        1. precision = true predictions / all predictions.
        2. recall = true predictions / all ground truths.
        3. accuracy = true predictions / all ground truths and all predictions.

    Parameters
    ----------
    parameters: ValidationParameters
        This contains validation parameters set from the command line.
    segmentation_stats: SegmentationStats
        This is container of the pre-metrics computations per class.
    model_name: str
        The base name of the model being validated.
    dataset_name: str
        The base name of the validation dataset.
    save_path: Optional[str]
        The path to save the metrics on disk.
    """

    def __init__(
        self,
        parameters: ValidationParameters,
        segmentation_stats: SegmentationStats,
        model_name: str = "Model",
        dataset_name: str = "Dataset",
        save_path: Optional[str] = None
    ):
        self.parameters = parameters
        self.plots = Plots()
        self.segmentation_stats = segmentation_stats
        self.metrics = Metrics(model=model_name, dataset=dataset_name)
        self.metrics.save_path = save_path

    def run(self):
        """
        Method process for gathering all metrics used
        for the segmentation validation. Currently only supports
        EdgeFirst methods for computing the metrics. Future work will
        include reproduction of Ultralytics metrics for segmentation.
        """

        nc = len(self.segmentation_stats.stats)
        ap, ar, aacc, miou = 0., 0., 0., 0.

        for label_data in self.segmentation_stats.stats:
            precision, recall, accuracy = self.compute_class_metrics(
                label_data)
            ap += precision
            ar += recall
            aacc += accuracy

            data = {
                'precision': precision,
                'recall': recall,
                'accuracy': accuracy,
                'true_predictions': label_data.true_predictions,
                'false_predictions': label_data.false_predictions,
                'gt': label_data.ground_truths
            }

            self.plots.append_class_histogram_data(label_data.label, data)

        if nc > 0:
            for iou_list in self.segmentation_stats.ious.values():
                class_iou = float(
                    np.average(iou_list) if len(iou_list) > 0 else 0.0)
                miou += class_iou
            self.metrics.precision["mean"] = ap / nc
            self.metrics.recall["mean"] = ar / nc
            self.metrics.accuracy["mean"] = aacc / nc
            self.metrics.iou["mean"] = miou / nc

            accuracy, f1 = self.compute_overall_metrics()
            self.metrics.accuracy["overall"] = accuracy
            self.metrics.f1["overall"] = f1
        else:
            data = {
                'precision': np.nan,
                'recall': np.nan,
                'accuracy': np.nan,
                'true_predictions': 0,
                'false_predictions': 0,
                'gt': 0
            }
            self.plots.append_class_histogram_data("No label", data)

    def compute_class_metrics(
        self,
        label_data: SegmentationLabelData
    ) -> Tuple[float, float, float]:
        """
        This is an EdgeFirst validation method.

        Returns the precision, recall, and accuracy metrics of a specific class.

        Parameters
        ----------
        label_data: SegmentationLabelData
            This object contains the true predictions and false predictions
            of a specific class.

        Returns
        -------
        precision: float
            This is the true predictions / all predictions for this class.
        recall: float
            This is the true predictions / all ground truths for this class.
        accuracy: float
            This is the true predictions / all ground truths and predictions
            for this class.
        """
        precision, recall, accuracy = 0., 0., 0.
        if label_data.true_predictions > 0:
            precision = label_data.true_predictions / label_data.predictions
            recall = label_data.true_predictions / label_data.ground_truths
            accuracy = label_data.true_predictions / label_data.union
        return precision, recall, accuracy

    def compute_overall_metrics(self) -> Tuple[float, float]:
        """
        This is an EdgeFirst validation method.

        Computes the overall segmentation accuracy.
        Overall segmentation accuracy  = true predictions pixels / union pixels.

        Returns
        -------
        accuracy: float
            This is the true prediction pixels / union pixels. The union
            pixels is the number of ground truths | predictions.
        f1: float
            The F1 score based on
            2 * precision * recall / (precision + recall).
        """
        precision, recall, accuracy, f1 = 0., 0., 0., 0.
        precision = self.metrics.true_predictions / self.metrics.predictions
        recall = self.metrics.true_predictions / self.metrics.ground_truths
        accuracy = self.metrics.true_predictions / self.metrics.union

        if precision + recall > 0:
            f1 = 2 * precision * recall / (precision + recall)
        return accuracy, f1

    def reset(self):
        """
        Reset the metric containers.
        """
        self.plots.reset()
        self.segmentation_stats.reset()
        self.metrics.reset()
