"""
Implements object detection metrics for validation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple

import numpy as np

from edgefirst.validator.metrics.utils.math import batch_iou
from edgefirst.validator.metrics import Metrics, Plots

if TYPE_CHECKING:
    from edgefirst.validator.datasets import InstanceCollection
    from edgefirst.validator.evaluators import ValidationParameters
    from edgefirst.validator.metrics import DetectionLabelData, DetectionStats


def compute_precision(tp: int, fp: int) -> float:
    """
    Calculates the precision = tp / (tp + fp).

    Parameters
    ----------
    tp: int
        The number of true positives.
    fp: int
        The number of false positives.

    Returns
    -------
    float
        Resulting value is the result of tp / (tp + fp).
    """
    if tp + fp == 0:
        return 0.0
    return tp / (tp + fp)


def compute_recall(tp: int, fn: int) -> float:
    """
    Calculates recall = tp / (tp + fn).

    Parameters
    ----------
    tp: int
        The number of true positives.
    fn: int
        The number of false negatives.

    Returns
    -------
    float
        Resulting value is the result of tp / (tp + fn).
    """
    if tp + fn == 0:
        return 0.0
    return tp / (tp + fn)


def compute_accuracy(tp: int, fp: int, fn: int) -> float:
    """
    Calculates the accuracy = tp / (tp + fp + fn).

    Parameters
    ----------
    tp: int
        The number of true positives.
    fp: int
        The number of false positives.
    fn: int
        The number of false negatives.

    Returns
    -------
    float
        Resulting value is the result of tp / (tp + fp + fn).
    """
    if tp + fp + fn == 0:
        return 0.0
    return tp / (tp + fp + fn)


def compute_ap(
    recall: list,
    precision: list,
    v5_metric: bool = True,
    method: str = "interp"
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute the average precision, given the recall and precision curves.

    Parameters
    ----------
    recall: list
        The recall curve.
    precision: list
        The precision curve.
    v5_metric: bool
        Assume maximum recall to be 1.0, as in YOLOv5, MMDetetion etc.
    method: str
        Type of area integration to perform, other forms
        include 'continuous', by default use 'interp'.

    Returns
    -------
    ap: np.ndarray
        The average precision values based on the area under the curve.
    mpre: np.ndarray
        Mean precision from the precision curve.
    mrec: np.ndarray
        Mean recall from the recall curve.
    """
    # Append sentinel values to beginning and end
    if v5_metric:  # New YOLOv5 metric, same as MMDetection and Detectron2 repositories
        mrec = np.concatenate(([0.0], recall, [1.0]))
    else:  # Old YOLOv5 metric, i.e. default YOLOv7 metric
        mrec = np.concatenate(([0.0], recall, [recall[-1] + 0.01]))
    mpre = np.concatenate(([1.0], precision, [0.0]))

    # Compute the precision envelope
    mpre = np.flip(np.maximum.accumulate(np.flip(mpre)))

    # Integrate area under curve
    # methods: 'continuous', 'interp'
    if method.lower() == "interp":
        x = np.linspace(0, 1, 101)  # 101-point interp (COCO)
        ap = np.trapz(np.interp(x, mrec, mpre), x)  # integrate
    else:  # 'continuous'
        # points where x axis (recall) changes
        i = np.nonzero(mrec[1:] != mrec[:-1])[0]
        ap = np.sum((mrec[i + 1] - mrec[i]) * mpre[i + 1])  # area under curve
    return ap, mpre, mrec


def smooth(y: np.ndarray, f: float = 0.05) -> np.ndarray:
    """
    Applies box filter smoothing to array `y`
    with fraction `f`, yielding a smoothed array.

    Parameters
    ----------
    y: np.ndarray
        The array to apply a smoothening effect.
    f: float
        Smooth fraction.

    Returns
    -------
    np.ndarray
        The array with a smoothening effect.
    """
    nf = round(len(y) * f * 2) // 2 + \
        1  # number of filter elements (must be odd)
    p = np.ones(nf // 2)  # ones padding
    yp = np.concatenate((p * y[0], y, p * y[-1]), 0)  # y padded
    return np.convolve(yp, np.ones(nf) / nf, mode="valid")  # y-smoothed


class DetectionMetrics:
    """
    Runs the metric computations for object detection. The resulting
    metrics will be populated in the `Metrics` object that is created once
    initialized.

    Parameters
    ----------
    parameters: ValidationParameters
        This contains validation parameters set from the command line.
    detection_stats: DetectionStats
        This is container of the pre-metrics computations per class.
    model_name: str
        The base name of the model being validated.
    dataset_name: str
        The base name of the validation dataset.
    save_path: str
        The path to save the metrics on disk.
    """

    def __init__(
        self,
        parameters: ValidationParameters,
        detection_stats: DetectionStats,
        instances: InstanceCollection,
        model_name: str = "Model",
        dataset_name: str = "Dataset",
        save_path: Optional[str] = None,
        labels: Optional[list] = None
    ):
        self.parameters = parameters
        self.detection_stats = detection_stats
        self.instances = instances
        self.labels = labels

        self.plots = Plots(labels=labels)
        self.metrics = Metrics(model=model_name, dataset=dataset_name)
        self.metrics.save_path = save_path

        from edgefirst.validator.evaluators import DeploymentValidator
        self.deployment_validator = DeploymentValidator(
            parameters=parameters,
            metrics=self.metrics,
            plots=self.plots,
            instances=instances,
            detection_stats=detection_stats,
            labels=labels
        )

    def run(self, full_computation: bool = True):
        """
        Method process for gathering all metrics used for the detection
        validation. Methods to reproduce metrics in Ultralytics and deployment
        metrics at the optimal thresholds.

        Parameters
        ----------
        full_computation: bool
            If true, compute the optimal score and IoU thresholds and
            the deployment metrics. If false, only compute the Ultralytics
            metrics.
        """

        self.compute_metrics()
        if full_computation:
            self.compute_optimal_thresholds()
            if self.parameters.deploy_metrics:
                self.deployment_validator.group_evaluation()
                self.compute_deployment_metrics()

    def ap_per_class(
        self,
        tp: np.ndarray,
        conf: np.ndarray,
        pred_cls: np.ndarray,
        target_cls: np.ndarray,
        eps: float = 1e-16,
        v5_metric: bool = True
    ):
        """
        Compute the average precision, given the recall and precision curves.
        Source:: https://github.com/rafaelpadilla/Object-Detection-Metrics.
        Source:: https://github.com/ultralytics/yolov5/blob/master/utils/metrics.py#L29

        Parameters
        ----------
        tp:  np.ndarray
            True positives (nparray, nx1 or nx10).
        conf:  np.ndarray
            Objectness value from 0-1 (nparray).
        pred_cls: np.ndarray
            Predicted object classes (nparray).
        target_cls: np.ndarray
            True object classes (nparray).
        eps: float
            Minimum value to avoid division by zero.
        v5_metrc: bool
            Assume maximum recall to be 1.0, as in YOLOv5, MMDetetion etc.

        Returns
        -------
        Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]
            The average precision as computed in py-faster-rcnn.
        """
        # Sort by objectness
        i = np.argsort(-conf)
        tp, conf, pred_cls = tp[i], conf[i], pred_cls[i]

        # Find unique classes
        unique_classes, nt = np.unique(target_cls, return_counts=True)
        nc = unique_classes.shape[0]  # number of classes, number of detections

        # Create Precision-Recall curve and compute AP for each class
        px, py = np.linspace(0, 1, 1000), []  # for plotting
        ap, p, r = np.zeros((nc, 10)), np.zeros(
            (nc, 1000)), np.zeros((nc, 1000))

        classes = self.instances.stage_tracker.stage_generator(
            unique_classes, stage_name="stage_vmetrics", colour="green")
        for ci, c in enumerate(classes):
            # NOTE: Do not use np.nonzero, otherwise i.sum() will fail.
            i = pred_cls == c
            n_l = nt[ci]  # number of labels
            n_p = i.sum()  # number of predictions

            if n_p == 0 or n_l == 0:
                continue

            # Accumulate FPs and TPs
            fpc = (1 - tp[i]).cumsum(0)
            tpc = tp[i].cumsum(0)

            # Recall
            recall = tpc / (n_l + eps)  # recall curve
            # negative x, xp because xp decreases
            r[ci] = np.interp(-px, -conf[i], recall[:, 0], left=0)

            # Precision
            precision = tpc / (tpc + fpc)  # precision curve
            p[ci] = np.interp(-px, -conf[i], precision[:, 0],
                              left=1)  # p at pr_score

            # AP from recall-precision curve
            for j in range(tp.shape[1]):
                ap[ci, j], mpre, mrec = compute_ap(recall[:, j],
                                                   precision[:, j],
                                                   v5_metric=v5_metric)
                if j == 0:
                    # precision at mAP@0.5
                    py.append(np.interp(px, mrec, mpre))

        # Compute F1 (harmonic mean of precision and recall)
        f1 = 2 * p * r / (p + r + eps)

        # Used for plotting precision recall curve.
        self.plots.px = px
        self.plots.py = py
        self.plots.precision = p
        self.plots.recall = r
        self.plots.average_precision = ap
        self.plots.curve_labels = unique_classes
        self.plots.f1 = f1

        if v5_metric:
            i = smooth(f1.mean(0), 0.1).argmax()  # max F1 index YOLOv5
        else:
            i = f1.mean(0).argmax()  # max F1 index # YOLOv7
        return p[:, i], r[:, i], ap, f1[:, i]

    def compute_optimal_thresholds(self):
        """
        Calculate the optimal score and IoU thresholds.
        The score threshold is based on the threshold that yields the
        highest F1 score.

        The IoU threshold is calculated from the ground truth bounding boxes
        which takes the IoUs between the boxes. The IoU value in the upper
        quartile is the maximum IoU value found. This maximum IoU is the
        tolerance and taken as the optimal IoU threshold. Any IoU greater
        than this maximum would be considered a duplicate.
        """

        # Computing the optimal score threshold.
        i = self.plots.recall.mean(0).argmax()
        p0 = round(self.plots.px[i], 2)
        i = self.plots.precision.mean(0).argmax()
        p100 = round(self.plots.px[i], 2)

        # Optimal score threshold at max F1 score
        i = self.plots.f1.mean(0).argmax()
        p50 = round(self.plots.px[i], 3)
        self.parameters.score_threshold = p50

        self.plots.score_candidates = np.array([p0, p50, p100],
                                               dtype=np.float32)
        self.plots.score_stats = {
            "Low (Max Recall)": p0,
            "Q2 (Max F1 - Optimal score threshold)": p50,
            "High (Max Precision)": p100,
        }

        # An array of IoU candidates are used to analyze the ground truth
        # intersections for finding the optimal IoU threshold.
        # The IoU candidates are built by removing the IoUs along the diagonal
        # which are always 1's indicating the same object and the IoUs of
        # 0's are also removed to consider only intersecting ground truth
        # objects.
        iou_candidates = []
        instances = self.instances.stage_tracker.stage_generator(
            self.instances.gt_instances, stage_name="stage_optimals",
            colour="green")
        for gt_instance in instances:
            ious = batch_iou(gt_instance.boxes, gt_instance.boxes)
            filt_ones = ~np.eye(ious.shape[0], dtype=bool)
            ious = ious[filt_ones]
            ious = ious[ious > 0]
            iou_candidates.extend(ious.tolist())

        if len(iou_candidates) > 0:
            self.plots.iou_candidates = np.array(
                iou_candidates, dtype=np.float32)
            p0, p25, p50, p75, p100 = np.percentile(iou_candidates,
                                                    [0, 25, 50, 75, 100])
            iqr = p75 - p25
            # Whiskers following Tukey boxplot rule, clipped to data min/max
            lower_whisker = max(p0, p25 - 1.5 * iqr)
            upper_whisker = min(p100, p75 + 1.5 * iqr)

            # Extract the boxplot statistics directly
            self.plots.iou_stats = {
                "Low": lower_whisker,
                "Q1": p25,
                "Q2 (median)": p50,
                "Q3": p75,
                "High (Optimal IoU Threshold)": upper_whisker,
            }

            # Optimal IoU threshold
            self.parameters.iou_threshold = round(upper_whisker, 3)

    def compute_metrics(self):
        """
        Calculates metrics based on YOLO (Ultralytics and YOLOv7)
        validation methods.
        """
        p, r, ap, f1 = self.ap_per_class(
            tp=np.concatenate(self.detection_stats.stats["tp"], axis=0),
            conf=np.concatenate(self.detection_stats.stats["conf"], axis=0),
            pred_cls=np.concatenate(
                self.detection_stats.stats["pred_cls"], axis=0),
            target_cls=np.concatenate(
                self.detection_stats.stats["target_cls"], axis=0),
        )
        ap50, ap75, ap = ap[:, 0], ap[:, 5], ap.mean(1)  # AP@0.5, AP@0.5:0.95

        self.metrics.precision["map"] = {"0.50": ap50.mean(),
                                         "0.75": ap75.mean(),
                                         "0.50:0.95": ap.mean()}
        self.metrics.precision["mean"] = p.mean()
        self.metrics.recall["mean"] = r.mean()
        self.metrics.f1["mean"] = f1.mean()

    def compute_deployment_metrics(self):
        """
        Calculates the EdgeFirst Deployment metrics based on the
        ideal hyperparameters for the IoU and score thresholds. Populates the
        results in the `Metrics` object.
        """
        nc = len(self.deployment_validator.detection_stats.labeldata)
        # These arrays contain the metrics for each class where the rows
        # represent the class and the columns represent the IoU thresholds:
        # 0.50 to 0.95 in 0.05 intervals.
        mpre, mrec, macc = np.zeros(
            (nc, 10)), np.zeros(
            (nc, 10)), np.zeros(
            (nc, 10))

        if nc > 0:
            for ic, label_data in enumerate(
                    self.deployment_validator.detection_stats.labeldata):
                self.metrics.tp += label_data.get_tp_count(
                    self.parameters.tp_iou)
                self.metrics.cfp += label_data.get_cfp_count(
                    self.parameters.tp_iou)
                self.metrics.lfp += label_data.get_lfp_count(
                    self.parameters.tp_iou)

                # Build TP vs FP scores.
                self.plots.tp_scores.append(
                    label_data.get_tp_scores(
                        self.parameters.tp_iou))
                self.plots.fp_scores.append(
                    label_data.get_lfp_scores(
                        self.parameters.tp_iou))

                # Build TP vs FP IoUs.
                self.plots.tp_ious.append(
                    label_data.get_tp_iou(
                        self.parameters.tp_iou))
                self.plots.fp_ious.append(
                    label_data.get_lfp_iou(
                        self.parameters.tp_iou))
                class_metrics, class_truth_values = self.compute_class_metrics(
                    label_data, iou_threshold=self.parameters.tp_iou)

                data = {
                    'precision': class_metrics[0],
                    'recall': class_metrics[1],
                    'accuracy': class_metrics[2],
                    'tp': class_truth_values[0],
                    'fn': class_truth_values[3],
                    'fp': class_truth_values[1] + class_truth_values[2],
                    'gt': label_data.ground_truths
                }

                # Convert labels to string
                cls = str(label_data.label)
                if self.labels is not None and len(self.labels) > 0:
                    if not isinstance(cls, str) or (
                            isinstance(cls, str) and cls.isdigit()):
                        cls = self.labels[int(cls)]

                self.plots.append_class_histogram_data(cls, data)

                for it, iou_threshold in enumerate(self.detection_stats.ious):
                    class_metrics, _ = self.compute_class_metrics(
                        label_data,
                        iou_threshold
                    )

                    # The index of the class ic and the index of the IoU
                    # threshold will contain the metric: precision, recall,
                    # and accuracy of the class.
                    mpre[ic][it] = class_metrics[0]
                    mrec[ic][it] = class_metrics[1]
                    macc[ic][it] = class_metrics[2]

            mean_metrics = self.compute_mean_average_metrics(
                mpre, mrec, macc, nc)
            self.metrics.precision["class"] = mean_metrics[0][0]
            self.metrics.recall["class"] = mean_metrics[1][0]
            self.metrics.accuracy["class"] = mean_metrics[2][0]

            overall_metrics = self.compute_overall_metrics()
            self.metrics.precision["overall"] = overall_metrics[0]
            self.metrics.recall["overall"] = overall_metrics[1]
            self.metrics.accuracy["overall"] = overall_metrics[2]

        else:
            data = {
                'precision': 0,
                'recall': 0,
                'accuracy': 0,
                'tp': 0,
                'fn': 0,
                'fp': 0,
                'gt': 0
            }
            self.plots.append_class_histogram_data("No label", data)

    def compute_class_metrics(
        self,
        label_data: DetectionLabelData,
        iou_threshold: float,
    ) -> Tuple[np.ndarray, list]:
        """
        This is an EdgeFirst validation method.

        Returns the precision, recall, and accuracy metrics of a
        specific class at the specified validation IoU threshold.

        Parameters
        ----------
        label_data: DetectionLabelData
            This is a container of the truth values of a specific class.
        iou_threshold: float
            The validation IoU threshold to consider as true positives.

        Returns
        -------
        class_metrics: np.ndarray (1, 3)
            This contains the values for precision, recall, and accuracy
            of the class representing the label data container.
        class_truth_values: list
            This contains the values for true positives, classification
            false positives, localization false positives, and
            false negatives for the class representing the label data
            container.
        """
        # These are the truth values just for the specified class in the
        # data container: true positives, false positives, and false negatives.
        tp = label_data.get_tp_count(iou_threshold=iou_threshold)
        cfp = label_data.get_cfp_count(iou_threshold=iou_threshold)
        lfp = label_data.get_lfp_count(iou_threshold=iou_threshold)
        fn = label_data.get_fn_count(iou_threshold=iou_threshold)

        class_metrics = np.zeros(3)
        class_truth_values = [tp, cfp, lfp, fn]

        if tp == 0:
            if cfp + lfp == 0:
                class_metrics[0] = np.nan
            if fn == 0:
                class_metrics[1] = np.nan
            if cfp + lfp + fn == 0:
                class_metrics[2] = np.nan
        else:
            class_metrics[0] = compute_precision(tp, cfp + lfp)
            class_metrics[1] = compute_recall(tp, fn)
            class_metrics[2] = compute_accuracy(tp, cfp + lfp, fn)

        return class_metrics, class_truth_values

    def compute_mean_average_metrics(
        self,
        mpre: np.ndarray,
        mrec: np.ndarray,
        macc: np.ndarray,
        nc: int
    ) -> Tuple[list, list, list]:
        """
        This is an EdgeFirst validation method.

        Given an array of precision, recall, and accuracy at 0.50 to 0.95 IoU
        thresholds, this will return values only at IoU thresholds,
        0.50, 0.75, and 0.50-0.95 averages.

        Parameters
        ----------
        mpre: np.ndarray (1,20)
            precision values from different IoU thresholds.
        mrec: np.ndarray (1,20)
            recall values from different IoU thresholds.
        macc: np.ndarray (1,20)
            accuracy values from different IoU thresholds.
        nc: int
            The number of classes.

        Returns
        -------
        metric_map: list
            This contains the precision values at IoU thresholds
            0.50, 0.75, 0.50-0.95
        metric_mar: list
            This contains the recall values at IoU thresholds
            0.50, 0.75, 0.50-0.95
        metric_maccuracy: list
            This contains the accuracy values at IoU thresholds
            0.50, 0.75, 0.50-0.95
        """
        # These arrays are essentially the mAP, mAR, and mACC across the
        # IoU thresholds 0.00 to 1.00 in 0.05 intervals with shape (1, 20).
        mpre = np.nansum(mpre, axis=0) / nc
        mrec = np.nansum(mrec, axis=0) / nc
        macc = np.nansum(macc, axis=0) / nc

        # These are the mAP, mAR, and mACC 0.5-0.95 IoU thresholds.
        mpre_5095 = np.sum(mpre) / 10
        mrec_5095 = np.sum(mrec) / 10
        macc_5095 = np.sum(macc) / 10

        # This list contains mAP, mAR, mACC 0.50, 0.75, and 0.5-0.95.
        mpre = [mpre[0], mpre[5], mpre_5095]
        mrec = [mrec[0], mrec[5], mrec_5095]
        macc = [macc[0], macc[5], macc_5095]
        return mpre, mrec, macc

    def compute_overall_metrics(self) -> Tuple[float, float, float]:
        """
        This is an EdgeFirst Validation method.

        Computes the overall metrics.

        Returns
        -------
        precision: float
            overall precision = sum tp /
            (sum tp + sum fp (localization + classification)).
        recall: float
            overall recall = sum tp /
            (sum tp + sum fn + sum fp (localization)).
        accuracy: float
            overall accuracy  = sum tp /
            (sum tp + sum fn + sum fp (localization + classification)).
        """
        precision, recall, accuracy = 0., 0., 0.

        if self.metrics.tp > 0:
            precision = compute_precision(
                self.metrics.tp,
                self.metrics.cfp + self.metrics.lfp
            )
            recall = compute_recall(
                self.metrics.tp,
                self.metrics.fn + self.metrics.cfp
            )
            accuracy = compute_accuracy(
                self.metrics.tp,
                self.metrics.cfp + self.metrics.lfp,
                self.metrics.fn
            )
        return precision, recall, accuracy

    def reset(self):
        """
        Reset the metric containers.
        """
        self.plots.reset()
        self.detection_stats.reset()
        self.deployment_validator.detection_stats.reset()
        self.metrics.reset()
