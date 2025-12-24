"""
Defines the containers for the data needed for plotting validation charts.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

import numpy as np

from edgefirst.validator.metrics.utils.math import batch_iou

if TYPE_CHECKING:
    from edgefirst.validator.datasets import DetectionInstance


class ConfusionMatrix:
    """
    Confusion matrix for detection metrics.

    Parameters
    ----------
    labels: list
        A list of unique string labels to
        initialize the confusion matrix.
    iou_threshold: float
        The IoU threshold to use when populating
        the confusion matrix. This threshold defines
        the minimum IoU required for a detection to be
        considered a true positive.
    score_threshold: float
        The score threshold to use when populating
        the confusion matrix.
    """

    def __init__(
        self,
        labels: list = [],
        iou_threshold: float = 0.50,
        score_threshold: float = 0.50
    ):
        self.labels = labels
        self.iou_threshold = iou_threshold
        self.score_threshold = score_threshold
        self.offset = 0
        if "background" not in self.labels:
            self.labels = ["background"] + self.labels
            self.offset = 1
        self.nc = len(self.labels)
        self.matrix = np.zeros((self.nc, self.nc), dtype=np.int32)

    def set_thresholds(
        self,
        iou_threshold: float,
        score_threshold: float
    ):
        """
        Sets the IoU and score thresholds to new values.

        Parameters
        ----------
        iou_threshold: float
            The IoU threshold to set.
        score_threshold: float
            The score threshold to set.
        """
        self.iou_threshold = iou_threshold
        self.score_threshold = score_threshold

    def process_batch(
        self,
        dt_instance: DetectionInstance,
        gt_instance: DetectionInstance
    ):
        """
        Populates the confusion matrix using Ultralytics matching
        strategies. The confusion matrix for deployment metrics are
        populated using the DetectionClassifier class.

        Parameters
        ----------
        dt_instance: DetectionInstance
            A prediction instance container of the boxes, labels, and scores.
        gt_instance: DetectionInstance
            A ground truth instance container of the boxes and the labels.
        """

        # No detections means all false negatives.
        if dt_instance is None:
            gt_classes = gt_instance.labels.astype(np.uintp)
            for gc in gt_classes:
                self.matrix[0, gc + self.offset] += 1  # background FN
            return

        filt = dt_instance.scores > self.score_threshold
        dt_boxes = dt_instance.boxes[filt]
        dt_classes = dt_instance.labels[filt]
        dt_classes = dt_classes.astype(np.uintp)

        gt_boxes = gt_instance.boxes
        gt_classes = gt_instance.labels
        gt_classes = gt_classes.astype(np.uintp)

        iou = batch_iou(gt_boxes, dt_boxes)
        x = np.where(iou > self.iou_threshold)
        if x[0].shape[0]:
            matches = np.concatenate(
                (np.stack(x, 1), iou[x[0], x[1]][:, None]), 1)
            if x[0].shape[0] > 1:
                matches = matches[matches[:, 2].argsort()[::-1]]
                matches = matches[np.unique(
                    matches[:, 1], return_index=True)[1]]
                matches = matches[matches[:, 2].argsort()[::-1]]
                matches = matches[np.unique(
                    matches[:, 0], return_index=True)[1]]
        else:
            matches = np.zeros((0, 3))

        n = matches.shape[0] > 0
        m0, m1, _ = matches.transpose().astype(int)
        for i, gc in enumerate(gt_classes):
            j = m0 == i
            # Asserting a unique match.
            if n and sum(j) == 1:
                self.matrix[dt_classes[m1[j]] + self.offset,
                            gc + self.offset] += 1  # correct
            else:
                self.matrix[0, gc + self.offset] += 1  # true background

        matched_detections = m1 if n else np.array([], dtype=int)
        for i, dc in enumerate(dt_classes):
            if i not in matched_detections:
                # false positive (predicted something not matched to GT)
                self.matrix[dc + self.offset, 0] += 1

    def reset(self):
        """
        Resets the confusion matrix to all zeros.
        """
        self.matrix = np.zeros((self.nc, self.nc), dtype=np.int32)


class Plots:
    """
    Container used to store the data needed for
    plotting the validation charts.

    Parameters
    ----------
    labels: list
        A list of unique string labels to
        initialize the confusion matrix.
    """

    def __init__(self, labels: list = []):
        self.labels = labels
        self.confusion_matrix = ConfusionMatrix(labels=labels)
        self.reset()

    @property
    def class_histogram_data(self) -> dict:
        """
        Attribute to access the class histogram data.

        Returns
        -------
        dict
            This contains the data for the class histogram.
        """
        return self.__class_histogram_data

    @class_histogram_data.setter
    def class_histogram_data(self, data: dict):
        """
        Sets the data for the class histogram to a new value.

        Parameters
        ----------
        data: dict
            This is the class histogram data to set.
            This should be a dictionary with the following keys.

                .. code-block:: python

                    {
                        "precision": precision,
                        "recall": recall,
                        "accuracy": accuracy,
                        "tp": tp,
                        "fn": fn,
                        "fp": fp,
                        "gt": gt
                    }
        """
        self.__class_histogram_data = data

    def append_class_histogram_data(self, label: str, data: dict):
        """
        This adds another key to the class histogram data indicated as the
        class label and data contains the metrics of that label.

        Parameters
        ----------
        label: str
            This is the key of the dictionary that is the class label.
        data: dict
            This contains the metrics of the label. This should
            be a dictionary with the following keys.

                .. code-block:: python

                    {
                        "precision": precision,
                        "recall": recall,
                        "accuracy": accuracy,
                        "tp": tp,
                        "fn": fn,
                        "fp": fp,
                        "gt": gt
                    }
        """
        self.__class_histogram_data[label] = data

    @property
    def px(self) -> np.ndarray:
        """
        Attribute to access px.

        Returns
        -------
        np.ndarray
            Precision vs Recall Curve 1000-point interpolated px values
            representing recall.
        """
        return self.__px

    @px.setter
    def px(self, this_px: np.ndarray):
        """
        Sets px to a new value.

        Parameters
        ----------
        px: np.ndarray
            The px values to set.
        """
        self.__px = this_px

    @property
    def py(self) -> np.ndarray:
        """
        Attribute to access py.

        Returns
        -------
        np.ndarray
            Precision vs Recall Curve 1000-point interpolated py values
            representing precision.
        """
        return self.__py

    @py.setter
    def py(self, this_py: np.ndarray):
        """
        Sets py to a new value.

        Parameters
        ----------
        py: np.ndarray
            The py values to set.
        """
        self.__py = this_py

    @property
    def precision(self) -> np.ndarray:
        """
        Attribute to access the array of precision values.

        Returns
        -------
        np.ndarray
            This contains the data for the precision recall curve.
        """
        return self.__precision

    @precision.setter
    def precision(self, data: np.ndarray):
        """
        Sets the data for the precision values.

        Parameters
        ----------
        data: :py:class:`np.ndarray`
            These are the precision values to set.

            This data should be formatted as the following:
            (nc x thresholds) so each row are for a unique class and
            each column is the precision value for each score threshold.
        """
        self.__precision = data

    @property
    def recall(self) -> np.ndarray:
        """
        Attribute to access the array of recall values.

        Returns
        -------
        np.ndarray
            This contains the data for the precision recall curve.
        """
        return self.__recall

    @recall.setter
    def recall(self, data: np.ndarray):
        """
        Sets the data for the recall values.

        Parameters
        ----------
        data: np.ndarray
            These are the recall values to set.

            This data should be formatted as the following:
            (nc x thresholds) so each row are for a unique class and
            each column is the recall value for each score threshold.
        """
        self.__recall = data

    @property
    def f1(self) -> np.ndarray:
        """
        Attribute to access the array of F1 values.

        Returns
        -------
        np.ndarray
            This contains the data for the precision-f1 curve.
        """
        return self.__f1

    @f1.setter
    def f1(self, data: np.ndarray):
        """
        Sets the data for the F1 values.

        Parameters
        ----------
        data: np.ndarray
            These are the F1 values to set.

            This data should be formatted as the following:
            (nc x thresholds) so each row are for a unique class and
            each column is the F1 value for each score threshold.
        """
        self.__f1 = data

    @property
    def average_precision(self) -> np.ndarray:
        """
        Attribute to access the array of average precision values.

        Returns
        -------
        np.ndarray
            This contains the data for the precision recall curve.
        """
        return self.__average_precision

    @average_precision.setter
    def average_precision(self, data: np.ndarray):
        """
        Sets the data for the average precision values.

        Parameters
        ----------
        data: np.ndarray
            These are the average precision values to set.

            This data should be formatted as the following:
            (nc x 10) so each row are for a unique class and
            each column is the precision at 10 different IoU threshold from
            0.50 to 0.95 in 0.05 intervals with a static score threshold
            set from the command line.
        """
        self.__average_precision = data

    @property
    def curve_labels(self) -> list:
        """
        Attribute to access the precision recall curve unique labels.

        Returns
        -------
        list
            This contains the labels for the precision recall curve.
        """
        return self.__curve_labels

    @curve_labels.setter
    def curve_labels(self, labels: list):
        """
        Sets the labels for the precision recall curve to a new value.

        Parameters
        ----------
        labels: list
            These are the precision recall curve labels to set.
        """
        self.__curve_labels = labels

    @property
    def tp_scores(self) -> list:
        """
        Attribute to access the confidence scores of true positive detections.

        Returns
        -------
        list
            A list containing the scores assigned to true positive detections.
        """
        return self.__tp_scores

    @tp_scores.setter
    def tp_scores(self, scores: list):
        """
        Sets the confidence scores for true positive detections.

        Parameters
        ----------
        scores: list
            A list of confidence scores to assign to true positive detections.
        """
        self.__tp_scores = scores

    @property
    def fp_scores(self) -> list:
        """
        Attribute to access the confidence scores of false positive detections.

        Returns
        -------
        list
            A list containing the scores assigned to false positive detections.
        """
        return self.__fp_scores

    @fp_scores.setter
    def fp_scores(self, scores: list):
        """
        Sets the confidence scores for false positive detections.

        Parameters
        ----------
        scores: list
            A list of confidence scores to assign to false positive detections.
        """
        self.__fp_scores = scores

    @property
    def tp_ious(self):
        """
        Attribute to access the IoU values for true positive detections.

        Returns
        -------
        list
            A list containing Intersection-over-Union (IoU)
            values for true positives.
        """
        return self.__tp_ious

    @tp_ious.setter
    def tp_ious(self, ious: list):
        """
        Sets the IoU values for true positive detections.

        Parameters
        ----------
        ious: list
            A list of IoU values to assign to true positive detections.
        """
        self.__tp_ious = ious

    @property
    def fp_ious(self):
        """
        Attribute to access the IoU values for false positive detections.

        Returns
        -------
        list
            A list containing Intersection-over-Union (IoU) values
            for false positives.
        """
        return self.__fp_ious

    @fp_ious.setter
    def fp_ious(self, ious: list):
        """
        Sets the IoU values for false positive detections.

        Parameters
        ----------
        ious: list
            A list of IoU values to assign to false positive detections.
        """
        self.__fp_ious = ious

    @property
    def iou_candidates(self) -> np.ndarray:
        """
        Attribute to access the IoU candidates.

        Returns
        -------
        np.ndarray
            A list of IoU from the ground truth box
            intersections used for finding a suitable candidate
            for the optimal IoU threshold.
        """
        return self.__iou_candidates

    @iou_candidates.setter
    def iou_candidates(self, ious: np.ndarray):
        """
        Sets the IoU candidates to a new value.

        Parameters
        ----------
        ious: np.ndarray
            An array of IoUs from the ground truth
            box intersections.
        """
        self.__iou_candidates = ious

    @property
    def iou_stats(self) -> dict:
        """
        Attribute to access the IoU stats.

        Returns
        -------
        dict
            This contains the values to label the
            IoU distribution chart.

            .. code-block:: python

                stats = {
                    "Low": lower_whisker,
                    "Q1": p25,
                    "Q2 (median)": p50,
                    "Q3": p75,
                    "High (Optimal IoU Threshold)": upper_whisker,
                }
        """
        return self.__iou_stats

    @iou_stats.setter
    def iou_stats(self, stats: dict):
        """
        Sets the IoU stats for the IoU distribution plot
        to a new value.

        Parameters
        ----------
        stats: dict
            This contains the values to label the
            IoU distribution chart.

            .. code-block:: python

                stats = {
                    "Low": lower_whisker,
                    "Q1": p25,
                    "Q2 (median)": p50,
                    "Q3": p75,
                    "High (Optimal IoU Threshold)": upper_whisker,
                }
        """
        self.__iou_stats = stats

    @property
    def score_candidates(self) -> np.ndarray:
        """
        Attribute to access the score candidates.

        Returns
        -------
        np.ndarray
            A list of score values from the detections
            used for finding a suitable candidate
            for the optimal score threshold.
        """
        return self.__score_candidates

    @score_candidates.setter
    def score_candidates(self, scores: np.ndarray):
        """
        Sets the score candidates to a new value.

        Parameters
        ----------
        scores: np.ndarray
            An array of scores from the detections.
        """
        self.__score_candidates = scores

    @property
    def score_stats(self) -> dict:
        """
        Attribute to access the score stats.

        Returns
        -------
        dict
            This contains the values to label the
            Score distribution chart.

            .. code-block:: python

                stats = {
                    "Low": p0,
                    "Q1 (Max Recall)": p25,
                    "Q2 (Optimal Score Threshold)": p50,
                    "Q3 (Max Precision)": p75,
                    "High ": p100,
                }
        """
        return self.__score_stats

    @score_stats.setter
    def score_stats(self, stats: dict):
        """
        Sets the score stats for the score distribution plot
        to a new value.

        Parameters
        ----------
        stats: dict
            This contains the values to label the
            Score distribution chart.

            .. code-block:: python

                stats = {
                    "Low (Max Recall)": p0,
                    "Q2 (Max F1 - Optimal score threshold)": p50,
                    "High (Max Precision)": p100,
                }
        """
        self.__score_stats = stats

    def reset(self):
        """
        Resets the containers for the data use to plot.
        """
        self.confusion_matrix.reset()

        self.__class_histogram_data = dict()

        # Precision Recall Curve
        self.__px = np.array([])
        self.__py = np.array([])
        self.__precision = list()
        self.__recall = list()
        self.__f1 = list()
        self.__average_precision = list()
        self.__curve_labels = list()

        # TP vs FP scores
        self.__tp_scores = list()
        self.__fp_scores = list()

        # TP vs FP IoUs
        self.__tp_ious = list()
        self.__fp_ious = list()

        # IoU Distribution
        self.__iou_candidates = np.array([])
        self.__iou_stats = dict()

        # Score Distribution
        self.__score_candidates = np.array([])
        self.__score_stats = dict()


class MultitaskPlots:
    """
    A container for both detection and segmentation
    plots for Multitask validation.

    Parameters
    -----------
    detection_plots: Plots
        Detection plots container.
    segmentation_plots: Plots
        Segmentation plots container.
    """

    def __init__(self, detection_plots: Plots, segmentation_plots: Plots):
        self.detection_plots = detection_plots
        self.segmentation_plots = segmentation_plots
