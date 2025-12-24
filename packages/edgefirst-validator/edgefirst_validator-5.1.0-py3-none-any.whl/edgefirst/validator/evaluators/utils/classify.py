"""
Implementations for classifying detection and segmentation results.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Tuple

import numpy as np

if TYPE_CHECKING:
    from edgefirst.validator.evaluators import ValidationParameters
    from edgefirst.validator.datasets import DetectionInstance
    from edgefirst.validator.metrics import DetectionStats
    from edgefirst.validator.evaluators import Matcher
    from edgefirst.validator.metrics import Plots


class DetectionClassifier:
    """
    Classifies model predictions into true positives, false positives, or
    false negatives depending on the results of the matching algorithm
    and the labels. Furthermore, the confusion matrix data is also being
    collected in this stage.

    Parameters
    ----------
    parameters: ValidationParameters
        This contains the validation parameters set from the command line.
    detection_stats: DetectionStats
        This stores the number of true positives, false positives, and
        false negatives per label found throughout validation.
    matcher: Matcher
        The matcher object that matches the predictions to the
        ground truth and contains matching results.
    plots: PlotSummary
        This is a container for the data to draw the plots.
    """

    def __init__(
        self,
        parameters: ValidationParameters,
        detection_stats: DetectionStats,
        matcher: Matcher,
        plots: Plots
    ):
        self.parameters = parameters
        self.detection_stats = detection_stats
        self.matcher = matcher
        self.plots = plots

    def classify(
        self,
        gt_instance: DetectionInstance,
        dt_instance: DetectionInstance
    ):
        """
        Classifies the matched, missed, and extra detections
        into true positives, localization and classification false positives,
        and false negatives.

        Parameters
        ----------
        gt_instance: DetectionInstance
            The ground truth instance that contains the
            ground truth boxes and labels.
        dt_instance: DetectionInstance
            The detection instance that contains the model
            prediction boxes, labels, and scores for the image.
        """
        self.classify_matches(gt_instance=gt_instance, dt_instance=dt_instance)
        self.classify_unmatched_dt(dt_instance)
        self.classify_unmatched_gt(gt_instance)

    def classify_matches(
        self,
        gt_instance: DetectionInstance,
        dt_instance: DetectionInstance
    ):
        """
        Classifies the matching ground truth to detection boxes
        into true positives or classification false positives.

        Parameters
        ----------
        gt_instance: DetectionInstance
            The ground truth instance that contains the
            ground truth boxes and labels.
        dt_instance: DetectionInstance
            The detection instance that contains the model
            prediction boxes, labels, and scores for the image.
        """
        for match in self.matcher.index_matches:
            dt_label = dt_instance.labels[match[0]]
            gt_label = gt_instance.labels[match[1]]
            score = dt_instance.scores[match[0]]
            iou = self.matcher.iou_list[match[0]]

            if dt_label != gt_label:
                label_data = self.detection_stats.get_label_data(dt_label)
                if label_data:
                    label_data.add_cfp(iou, score)

            label_data = self.detection_stats.get_label_data(gt_label)
            if label_data:
                label_data.add_ground_truths()
                if dt_label == gt_label:
                    label_data.add_tp(iou, score)

            # Populate confusion matrix
            if isinstance(gt_label, str):
                gt_label = self.plots.confusion_matrix.labels.index(gt_label)
            else:
                gt_label = self.plots.confusion_matrix.labels.index(
                    self.plots.labels[int(gt_label)])

            if isinstance(dt_label, str):
                dt_label = self.plots.confusion_matrix.labels.index(dt_label)
            else:
                dt_label = self.plots.confusion_matrix.labels.index(
                    self.plots.labels[int(dt_label)])

            if iou >= self.parameters.tp_iou:
                self.plots.confusion_matrix.matrix[dt_label, gt_label] += 1
            else:
                # False positive
                self.plots.confusion_matrix.matrix[dt_label, 0] += 1
                # False negative
                self.plots.confusion_matrix.matrix[0, gt_label] += 1

    def classify_unmatched_dt(self, dt_instance: DetectionInstance):
        """
        Classifies the extra predictions into localization false positives.

        Parameters
        ----------
        dt_instance: DetectionInstance
            The detection instance that contains the model
            prediction boxes, labels, and scores for the image.
        """
        for extra in self.matcher.index_unmatched_dt:
            dt_label = dt_instance.labels[extra]
            score = dt_instance.scores[extra]

            label_data = self.detection_stats.get_label_data(dt_label)
            if label_data:
                label_data.add_lfp(score)

            # Populate confusion matrix
            if isinstance(dt_label, str):
                dt_label = self.plots.confusion_matrix.labels.index(dt_label)
            else:
                dt_label = self.plots.confusion_matrix.labels.index(
                    self.plots.labels[int(dt_label)])
            # False positive
            self.plots.confusion_matrix.matrix[dt_label, 0] += 1

    def classify_unmatched_gt(self, gt_instance: DetectionInstance):
        """
        Classifies the missed predictions into false negatives.

        Parameters
        ----------
        gt_instance: DetectionInstance
            The ground truth instance that contains the
            ground truth boxes and labels.
        """
        for miss in self.matcher.index_unmatched_gt:
            gt_label = gt_instance.labels[miss]

            label_data = self.detection_stats.get_label_data(gt_label)
            if label_data:
                label_data.add_ground_truths()

            # Populate confusion matrix
            if isinstance(gt_label, str):
                gt_label = self.plots.confusion_matrix.labels.index(gt_label)
            else:
                gt_label = self.plots.confusion_matrix.labels.index(
                    self.plots.labels[int(gt_label)])
            # False negative
            self.plots.confusion_matrix.matrix[0, gt_label] += 1


def classify_mask(
    gt_class_mask: np.ndarray,
    dt_class_mask: np.ndarray,
    background_index: int,
    exclude_background: np.ndarray = True
) -> Tuple[int, int, int]:
    """
    Classifies if the pixels are either true predictions or false predictions.
    Note the masks provided can also be multiclass, however this function
    is used primarily to find the true predictions and false predictions
    per class.

    Parameters
    ----------
    gt_class_mask: (height, width) np.ndarray
        2D binary array representing pixels forming the image ground truth.
        1 represents the class being classified and 0 are the rest of
        the classes.
    dt_class_mask: (height, width) np.ndarray
        2D binary array representing pixels forming the image prediction.
        1 represents the class being classified and 0 are the rest of
        the classes.
    background_index: int
        The integer representing the background class in the mask.
    exclude_background: bool
        Specify to avoid background to background
        predictions and ground truths as true predictions.

    Returns
    -------
    true_predictions: int
        The number of true predictions pixels in the image.
    false_predictions: int
        The number of false predictions pixels in the image.
    union: int
        The union between ground truths and model predictions occurs
        when both arrays are non-zero. The union is the sum of
        true predictions and false predictions.
    """
    gt_mask_flat = gt_class_mask.flatten()
    dt_mask_flat = dt_class_mask.flatten()

    if exclude_background:
        # Do not consider 0 against 0 as true predictions. 0 means another class
        # not just background. True predictions are 1 against 1 which means this
        # current class.
        true_predictions = np.sum(
            (gt_mask_flat == dt_mask_flat) &
            (gt_mask_flat != background_index) &
            (dt_mask_flat != background_index))

        # The union between ground truths and predictions where both are
        # non-zero.
        union = np.sum((gt_mask_flat != background_index) |
                       (dt_mask_flat != background_index))
    else:
        true_predictions = np.sum(gt_mask_flat == dt_mask_flat)
        union = len(gt_mask_flat)

    false_predictions = np.sum(gt_mask_flat != dt_mask_flat)
    return true_predictions, false_predictions, union
