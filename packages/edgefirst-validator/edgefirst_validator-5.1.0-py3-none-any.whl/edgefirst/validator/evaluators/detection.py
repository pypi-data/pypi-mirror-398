"""
Implementations of the detection evaluator class for model validation.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import numpy as np

from edgefirst.validator.evaluators import Evaluator, Matcher, DetectionClassifier
from edgefirst.validator.publishers import TensorBoardPublisher
from edgefirst.validator.visualize import DetectionDrawer
from edgefirst.validator.datasets import DetectionInstance
from edgefirst.validator.metrics import DetectionStats, DetectionMetrics
from edgefirst.validator.runners import OfflineRunner, DeepViewRTRunner
from edgefirst.validator.datasets.utils.annotation_transforms import labels2string
from edgefirst.validator.datasets.utils.annotation_transforms import (ignore_boxes,
                                                                      clamp_boxes)
from edgefirst.validator.visualize.utils.plots import (plot_classification_detection,
                                                       plot_confusion_matrix,
                                                       plot_score_histogram,
                                                       plot_pr_curve,
                                                       plot_mc_curve,
                                                       plot_boxplot)
from edgefirst.validator.datasets.utils.fetch import get_shape
from edgefirst.validator.metrics.utils.math import (batch_distance_similarity,
                                                    batch_iou)

if TYPE_CHECKING:
    from edgefirst.validator.evaluators import (CombinedParameters,
                                                ValidationParameters,
                                                StageTracker)
    from edgefirst.validator.datasets import Dataset, InstanceCollection
    from edgefirst.validator.runners import Runner
    from edgefirst.validator.metrics import Metrics, Plots


class DetectionValidator(Evaluator):
    """
    Reproduce the validation methods implemented in Ultralytics and other
    variations such as YOLOv7 for detection. Reproduces the metrics in
    Ultralytics to allow comparable metrics between EdgeFirst models
    and Ultralytics models.

    Parameters
    ----------
    parameters: CombinedParameters
        This is a container for the model, dataset, and validation parameters
        set from the command line.
    stage_tracker: StageTracker
        The object used for tracking and displaying stages.
    runner: Runner
        A type of model runner object responsible for running the model
        for inference provided with an input image to produce bounding boxes.
    dataset: Dataset
        A type of dataset object responsible for reading different types
        of datasets such as Darknet, TFRecords, or EdgeFirst Datasets.
    """

    def __init__(
        self,
        parameters: CombinedParameters,
        stage_tracker: StageTracker,
        runner: Runner = None,
        dataset: Dataset = None,
    ):
        super(DetectionValidator, self).__init__(
            parameters=parameters, stage_tracker=stage_tracker,
            runner=runner, dataset=dataset)

        self.detection_stats = DetectionStats()
        self.metrics = DetectionMetrics(
            parameters=self.parameters.validation,
            detection_stats=self.detection_stats,
            instances=self.instances,
            model_name=self.model_name,
            dataset_name=self.dataset_name,
            save_path=self.save_path,
            labels=self.parameters.dataset.labels
        )
        self.drawer = DetectionDrawer()
        self.matcher = None

    def instance_collector(self):
        """
        Collects the instances from the ground truth and runs
        model inference on a single image to collect the instance for
        the model predictions.

        Yields
        ------
        dict
            This yields one image instance from the ground truth
            and model predictions with keys "gt_instance" and "dt_instance".
        """

        gt_instance: DetectionInstance
        for gt_instance in self.dataset:
            if isinstance(self.runner, (OfflineRunner, DeepViewRTRunner)):
                detections = self.runner.run_single_instance(
                    image=gt_instance.image_path
                )
            else:
                detections = self.runner.run_single_instance(
                    image=gt_instance.image
                )
            self.filter_gt(gt_instance)

            if detections is None:
                yield {
                    "gt_instance": gt_instance,
                    "dt_instance": None
                }

            dt_instance = DetectionInstance(gt_instance.image_path)
            boxes, labels, scores = detections
            dt_instance.height = gt_instance.height
            dt_instance.width = gt_instance.width
            dt_instance.boxes = boxes
            dt_instance.labels = labels
            dt_instance.scores = scores
            self.filter_dt(dt_instance)

            yield {
                "gt_instance": gt_instance,
                "dt_instance": dt_instance,
            }

    def filter_dt(self, dt_instance: DetectionInstance):
        """
        Apply validation filters to the prediction bounding boxes.

        Parameters
        ----------
        dt_instance: DetectionInstance
            The model detections container of the bounding boxes, labels,
            and scores for a single image/sample.
        """
        if self.parameters.validation.ignore_boxes:
            boxes, labels, scores = ignore_boxes(
                ignore=self.parameters.validation.ignore_boxes,
                boxes=dt_instance.boxes,
                labels=dt_instance.labels,
                scores=dt_instance.scores,
                shape=(dt_instance.height, dt_instance.width)
            )
            dt_instance.boxes = boxes
            dt_instance.labels = labels
            dt_instance.scores = scores
        if self.parameters.validation.clamp_boxes:
            dt_instance.boxes = clamp_boxes(
                boxes=dt_instance.boxes,
                clip=self.parameters.validation.clamp_boxes,
                shape=(dt_instance.height, dt_instance.width)
            )

        # Prediction bounding boxes are already centered around objects
        # in images with letterbox, padding, or resize transformations.
        # This operation will only denormalize the bounding box coordinates.
        if len(dt_instance.boxes) and dt_instance.shapes is not None:
            # The model input shape.
            height, width = get_shape(self.parameters.model.common.shape)
            dt_instance.boxes *= np.array([width, height, width, height])

        # If the model and dataset labels are not equal, it is required
        # to map the indices properly to match the ground truth and the
        # detections.
        if self.parameters.model.labels != self.parameters.dataset.labels:
            try:
                dt_instance.labels = np.array([
                    self.parameters.dataset.labels.index(
                        self.parameters.model.labels[int(cls)])
                    if self.parameters.model.labels[int(cls)]
                    in self.parameters.dataset.labels else cls for cls in
                    dt_instance.labels])
            except IndexError as exc:
                raise IndexError(
                    "Model index out of range. Try specifying the path " +
                    "to the model's labels via `--model-labels <path to labels.txt>`."
                ) from exc

    def filter_gt(self, gt_instance: DetectionInstance):
        """
        Apply validation filters for the ground truth bounding boxes.

        Parameters
        ----------
        gt_instance: DetectionInstance
            The ground truth container for the bounding boxes, labels
            for a single image instance.
        """

        if self.parameters.validation.ignore_boxes:
            boxes, labels, scores = ignore_boxes(
                ignore=self.parameters.validation.ignore_boxes,
                boxes=gt_instance.boxes,
                labels=gt_instance.labels,
                scores=gt_instance.scores,
                shape=(gt_instance.height, gt_instance.width)
            )
            gt_instance.boxes = boxes
            gt_instance.labels = labels
            gt_instance.scores = scores
        if self.parameters.validation.clamp_boxes:
            gt_instance.boxes = clamp_boxes(
                boxes=gt_instance.boxes,
                clip=self.parameters.validation.clamp_boxes,
                shape=(gt_instance.height, gt_instance.width)
            )

    def match_predictions(
        self,
        pred_classes: np.ndarray,
        true_classes: np.ndarray,
        iou: np.ndarray
    ) -> np.ndarray:
        """
        Match predictions to ground truth using IoU.
        Function implementation was taken from Ultralytics::
        https://github.com/ultralytics/ultralytics/blob/main/ultralytics/engine/validator.py#L251

        Parameters
        ----------
        pred_classes: np.ndarray
            Predicted class indices of shape (N,).
        true_classes: np.ndarray
            Target class indices of shape (M,).
        iou: np.ndarray
            An NxM tensor containing the pairwise IoU
            values for predictions and ground truth.

        Returns
        -------
        np.ndarray
            Correct tensor of shape (N, 10) for 10 IoU thresholds.
        """
        correct = np.zeros(
            (pred_classes.shape[0], self.detection_stats.ious.shape[0]),
            dtype=bool
        )

        correct_class = (true_classes[:, None] == pred_classes).astype(
            np.float32)  # shape (N, M)
        iou = iou * correct_class

        for i, threshold in enumerate(self.detection_stats.ious):
            # IoU > threshold and classes match
            matches = np.nonzero(iou >= threshold)
            matches = np.array(matches).T
            if matches.shape[0]:
                if matches.shape[0] > 1:
                    matches = matches[iou[matches[:, 0],
                                          matches[:, 1]].argsort()[::-1]]
                    matches = matches[np.unique(
                        matches[:, 1], return_index=True)[1]]
                    matches = matches[np.unique(
                        matches[:, 0], return_index=True)[1]]
                correct[matches[:, 1].astype(int), i] = True
        return correct

    def process_batch_v5(
        self,
        dt_instance: DetectionInstance,
        gt_instance: DetectionInstance
    ) -> np.ndarray:
        """
        Return the correct prediction matrix. Function implementation was taken
        from YOLOv5: https://github.com/ultralytics/yolov5/blob/master/val.py#L94.

        Parameters
        -----------
        dt_instance: DetectionInstance
            A prediction instance container of the boxes, labels, and scores.
        gt_instance: DetectionInstance
            A ground truth instance container of the boxes and the labels.

        Returns
        -------
        np.ndarray
            (array[n, 10]) where n denotes the classes for 10 IoU levels. This
            is a true positive array.
        """
        # Using the IoU as the metric for matching predictions.
        if self.parameters.validation.metric == "iou":
            iou = batch_iou(gt_instance.boxes, dt_instance.boxes)
        # Using centerpoint distance as the metric for matching predictions.
        else:
            iou = batch_distance_similarity(
                gt_instance.boxes, dt_instance.boxes)

        return self.match_predictions(
            pred_classes=dt_instance.labels,
            true_classes=gt_instance.labels if len(
                gt_instance.boxes) else np.array([]),
            iou=iou
        )

    def process_batch_v7(
        self,
        dt_instance: DetectionInstance,
        gt_instance: DetectionInstance
    ) -> np.ndarray:
        """
        Return the correct prediction matrix. Function implementation was taken
        from YOLOv7: https://github.com/WongKinYiu/yolov7/blob/main/test.py#L179

        Parameters
        -----------
        dt_instance: DetectionInstance
            A prediction instance container of the boxes, labels, and scores.
        gt_instance: DetectionInstance
            A ground truth instance container of the boxes and the labels.

        Returns
        -------
        np.ndarray
            (array[N, 10]) where n denotes the classes for 10 IoU levels. This
            is a true positive array..
        """
        correct = np.zeros(
            (dt_instance.boxes.shape[0],
             self.detection_stats.ious.shape[0])).astype(bool)
        gt_labels = gt_instance.labels if len(
            gt_instance.boxes) else np.array([])
        detected = []  # target indices
        # Generate a similar format to YOLOv5 for visualization purposes.
        matches = []
        for cls in np.unique(gt_labels):
            ti = np.flatnonzero(cls == gt_labels)  # target indices
            # prediction indices
            pi = np.flatnonzero(cls == dt_instance.labels)

            # Search for detections
            if pi.shape[0]:
                # Using the IoU as the metric for matching predictions.
                if self.parameters.validation.metric == "iou":
                    ious = batch_iou(
                        dt_instance.boxes[pi],
                        gt_instance.boxes[ti])
                # Using centerpoint distance as the metric
                # for matching predictions.
                else:
                    ious = batch_distance_similarity(
                        dt_instance.boxes[pi], gt_instance.boxes[ti])
                i = ious.argmax(1)
                ious = ious.max(axis=1)
                detected_set = set()
                for j in np.flatnonzero(ious > self.detection_stats.ious[0]):
                    d = ti[i[j]]  # detected target
                    # The ious[j] is always a tensor of 1 value.
                    matches.append([ti[i[j]], pi[j], ious[j]])
                    if d.item() not in detected_set:
                        detected_set.add(d.item())
                        detected.append(d)
                        # iou_thres is 1xn
                        correct[pi[j]] = ious[j] > self.detection_stats.ious
                        # all targets already located in image
                        if len(detected) == len(gt_instance.boxes):
                            break
        return correct

    def evaluate(self, instance: dict):
        """
        Run model evaluation using Ultralytics or YOLOv7 validation methods.

        Parameters
        ----------
        instance: dict
            This contains the ground truth and model prediction instances
            with keys "gt_instance", "dt_instance".
        """
        gt_instance: DetectionInstance = instance.get("gt_instance")
        dt_instance: DetectionInstance = instance.get("dt_instance")

        niou = len(self.detection_stats.ious)
        nl = len(gt_instance.labels)  # The number of ground truths.
        nd = len(dt_instance.labels)  # The number of predictions.
        tcls = gt_instance.labels.tolist() if nl else []  # target class.

        self.metrics.metrics.add_ground_truths(nl)
        self.metrics.metrics.add_predictions(nd)
        correct = []

        if nl:
            if nd == 0:
                # By default the confusion matrix is built
                # based on the deployment metrics.
                if (self.parameters.validation.plots
                        and not self.parameters.validation.deploy_metrics):
                    self.metrics.plots.confusion_matrix.process_batch(
                        dt_instance=None, gt_instance=gt_instance)
                self.detection_stats.stats["tp"].append(
                    np.zeros((0, niou), dtype=bool))
                self.detection_stats.stats["conf"].append(np.array([]))
                self.detection_stats.stats["pred_cls"].append(np.array([]))
                self.detection_stats.stats["target_cls"].append(tcls)
                return

            # Ultralytics method.
            if self.parameters.validation.method == "ultralytics":
                correct = self.process_batch_v5(dt_instance=dt_instance,
                                                gt_instance=gt_instance)
            # YOLOv7 method.
            elif self.parameters.validation.method == "yolov7":
                correct = self.process_batch_v7(dt_instance=dt_instance,
                                                gt_instance=gt_instance)
            # By default the confusion matrix is built
            # based on the deployment metrics.
            if (self.parameters.validation.plots and
                    not self.parameters.validation.deploy_metrics):
                self.metrics.plots.confusion_matrix.process_batch(
                    dt_instance=dt_instance, gt_instance=gt_instance)
        else:
            correct = np.zeros((dt_instance.boxes.shape[0], niou)).astype(bool)

        if nd:
            self.detection_stats.stats["tp"].append(correct)
            self.detection_stats.stats["conf"].append(dt_instance.scores)
            self.detection_stats.stats["pred_cls"].append(dt_instance.labels)
            self.detection_stats.stats["target_cls"].append(tcls)
        else:
            self.detection_stats.stats["tp"].append(
                np.zeros((0, niou), dtype=bool))
            self.detection_stats.stats["conf"].append(np.array([]))
            self.detection_stats.stats["pred_cls"].append(np.array([]))
            self.detection_stats.stats["target_cls"].append(tcls)

    def visualize(
        self,
        gt_instance: DetectionInstance,
        dt_instance: DetectionInstance,
        epoch: int = 0
    ):
        """
        Draw bounding box results on the image and save the results in disk
        or publish into Tensorboard.

        Parameters
        ----------
        gt_instance: DetectionInstance
            This is the ground truth instance which contains bounding
            boxes and labels to draw.
        dt_instance: DetectionInstance
            This is the model detection instance which contains the
            bounding boxes, labels, and confidence scores to draw.
        epoch: int
            This is the training epoch number. This
            parameter is internal for ModelPack usage.
            Standalone validation does not use this parameter.
        """

        image = self.drawer.draw_2d_bounding_boxes(
            gt_instance=gt_instance,
            dt_instance=dt_instance,
            matcher=self.matcher,
            validation_iou=self.parameters.validation.tp_iou,
            validation_score=self.parameters.validation.score_threshold,
            method="ultralytics",
            labels=self.parameters.dataset.labels
        )
        if self.parameters.validation.visualize:
            image.save(os.path.join(self.parameters.validation.visualize,
                                    os.path.basename(gt_instance.image_path)))
        elif self.tensorboard_writer:
            self.tensorboard_writer(
                np.asarray(image), gt_instance.image_path, step=epoch)

    def get_plots(self):
        """
        Reproduces the validation charts from Ultralytics and
        includes additional charts for deployment metrics.
        """
        plot_jobs = [
            (plot_confusion_matrix, dict(
                confusion_data=self.metrics.plots.confusion_matrix.matrix,
                labels=self.metrics.plots.confusion_matrix.labels,
                model=self.metrics.metrics.model), "confusion_matrix.png"),
            (plot_pr_curve, dict(
                precision=self.metrics.plots.py,
                recall=self.metrics.plots.px,
                ap=self.metrics.plots.average_precision,
                names=self.parameters.dataset.labels,
                model=self.metrics.metrics.model), "prec_rec_curve.png"),
            (plot_mc_curve, dict(
                px=self.metrics.plots.px,
                py=self.metrics.plots.f1,
                names=self.parameters.dataset.labels,
                model=self.metrics.metrics.model,
                ylabel="F1"), "F1_curve.png"),
            (plot_mc_curve, dict(
                px=self.metrics.plots.px,
                py=self.metrics.plots.precision,
                names=self.parameters.dataset.labels,
                model=self.metrics.metrics.model,
                ylabel="Precision"), "P_curve.png"),
            (plot_mc_curve, dict(
                px=self.metrics.plots.px,
                py=self.metrics.plots.recall,
                names=self.parameters.dataset.labels,
                model=self.metrics.metrics.model,
                ylabel="Recall"), "R_curve.png"),
            (plot_boxplot, dict(
                iou_candidates=self.metrics.plots.iou_candidates,
                score_candidates=self.metrics.plots.score_candidates,
                iou_stats=self.metrics.plots.iou_stats,
                score_stats=self.metrics.plots.score_stats), "optimal_thresholds.png"),
        ]

        if self.parameters.validation.deploy_metrics:
            plot_jobs.append(
                (plot_classification_detection, dict(
                    class_histogram_data=self.metrics.plots.class_histogram_data,
                    model=self.metrics.metrics.model), "class_scores.png")
            )
            plot_jobs.append(
                (plot_score_histogram, dict(
                    tp_scores=np.concatenate(
                        self.metrics.plots.tp_scores, axis=0),
                    fp_scores=np.concatenate(
                        self.metrics.plots.fp_scores, axis=0),
                    model=self.metrics.metrics.model), "histogram_scores.png")
            )
            plot_jobs.append(
                (plot_score_histogram, dict(
                    tp_scores=np.concatenate(
                        self.metrics.plots.tp_ious, axis=0),
                    fp_scores=np.concatenate(
                        self.metrics.plots.fp_ious, axis=0),
                    model=self.metrics.metrics.model,
                    title="Histogram of TP vs FP IoUs",
                    xlabel="IoU"), "histogram_ious.png")
            )
        self.save_plots(plot_jobs)


class DeploymentValidator:
    """
    Evaluator class for deployment metrics for object detection.

    Parameters
    ----------
    parameters: ValidationParameters
        This is a container for the validation parameters
        set from the command line.
    metrics: Metrics
        This is a container for the detection metrics.
    plots: Plots
        This is a container for the detection plots.
    instances: InstanceCollection
        This is a container for the ground truth and prediction instances.
    detection_stats: DetectionStats
        This is container of the pre-metrics computations per class.
    labels: list
        This is a list of class labels for the dataset.
    """

    def __init__(
        self,
        parameters: ValidationParameters,
        metrics: Metrics,
        plots: Plots,
        instances: InstanceCollection,
        detection_stats: DetectionStats,
        labels: list = []
    ):
        self.parameters = parameters
        self.metrics = metrics
        self.instances = instances
        self.detection_stats = detection_stats
        self.labels = labels
        self.matcher = Matcher(parameters=parameters)
        self.classifier = DetectionClassifier(
            parameters=parameters,
            detection_stats=self.detection_stats,
            matcher=self.matcher,
            plots=plots
        )
        self.drawer = DetectionDrawer()

        if self.parameters.tensorboard:
            self.tensorboard_writer = TensorBoardPublisher(
                self.parameters.tensorboard)

    def evaluate(self, instance: dict):
        """
        Run model evaluation using EdgeFirst validation methods.

        Parameters
        ----------
        instance: dict
            This contains the ground truth and model predictions instances
            with keys "gt_instance" and "dt_instance".
        """
        gt_instance: DetectionInstance = instance.get("gt_instance")
        dt_instance: DetectionInstance = instance.get("dt_instance")

        # For deployment metrics, filter predictions by score threshold.
        filt = dt_instance.scores >= self.parameters.score_threshold
        dt_instance.boxes = dt_instance.boxes[filt]
        dt_instance.labels = dt_instance.labels[filt]
        dt_instance.scores = dt_instance.scores[filt]

        self.detection_stats.capture_class(dt_instance.labels)
        self.detection_stats.capture_class(gt_instance.labels)

        self.matcher.match(
            gt_boxes=gt_instance.boxes,
            gt_labels=gt_instance.labels,
            dt_boxes=dt_instance.boxes,
            dt_labels=dt_instance.labels,
        )
        self.classifier.classify(
            gt_instance=gt_instance,
            dt_instance=dt_instance
        )

    def single_evaluation(self, instance: dict, save_image: bool):
        """
        Run model evaluation using EdgeFirst validation methods.

        Parameters
        ----------
        instance: dict
            This contains the ground truth and model predictions instances
            with keys "gt_instance" and "dt_instance".
        save_image: bool
            If set to True, this will save the image
            with drawn bounding box results.
        """
        self.evaluate(instance)
        gt_instance = instance.get("gt_instance", None)
        dt_instance = instance.get("dt_instance", None)

        if save_image and gt_instance.visual_image is not None:
            # Convert labels from integers to string for detection.
            gt_instance.labels = np.array(labels2string(
                gt_instance.labels, self.labels))
            dt_instance.labels = np.array(labels2string(
                dt_instance.labels, self.labels))
            self.visualize(gt_instance, dt_instance,)

    def visualize(
        self,
        gt_instance: DetectionInstance,
        dt_instance: DetectionInstance,
    ):
        """
        Draw bounding box results on the image and save the results in disk
        or publish into Tensorboard.

        Parameters
        ----------
        gt_instance: DetectionInstance
            This is the ground truth instance which contains bounding
            boxes and labels to draw.
        dt_instance: DetectionInstance
            This is the model detection instance which contains the
            bounding boxes, labels, and confidence scores to draw.
        """
        image = self.drawer.draw_2d_bounding_boxes(
            gt_instance=gt_instance,
            dt_instance=dt_instance,
            matcher=self.matcher,
            validation_iou=self.parameters.tp_iou,
            validation_score=self.parameters.score_threshold,
            method="edgefirst",
            labels=self.labels
        )
        if self.parameters.visualize:
            image.save(os.path.join(self.parameters.visualize,
                                    os.path.basename(gt_instance.image_path)))
        elif self.tensorboard_writer:
            self.tensorboard_writer(
                np.asarray(image), gt_instance.image_path, step=0)

    def group_evaluation(self):
        """
        Run model evaluation using EdgeFirst validation methods.
        """
        save_image = bool(self.parameters.visualize or
                          self.parameters.tensorboard)

        for instance in self.instances:
            if self.parameters.display >= 0:
                if self.counter < self.parameters.display:
                    save_image = True
                    self.counter += 1
                else:
                    save_image = False

            self.single_evaluation(instance, save_image=save_image)
