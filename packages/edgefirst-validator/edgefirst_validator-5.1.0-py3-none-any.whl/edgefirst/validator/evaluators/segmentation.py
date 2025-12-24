"""
Implementation of segmentation evaluation methods.
"""

from __future__ import annotations

import os
from copy import deepcopy
from typing import TYPE_CHECKING, List, Tuple

import numpy as np
import matplotlib.figure

from edgefirst.validator.evaluators import Evaluator, DetectionValidator
from edgefirst.validator.visualize import SegmentationDrawer, DetectionDrawer
from edgefirst.validator.datasets import SegmentationInstance, MultitaskInstance
from edgefirst.validator.metrics import (SegmentationStats, SegmentationMetrics,
                                         MultitaskMetrics, MultitaskPlots,
                                         DetectionStats, DetectionMetrics)
from edgefirst.validator.datasets.utils.annotation_transforms import (create_mask_background,
                                                                      create_mask_class,
                                                                      labels2string)
from edgefirst.validator.evaluators.utils.classify import classify_mask
from edgefirst.validator.publishers.utils.logger import logger
from edgefirst.validator.visualize.utils.plots import (plot_classification_segmentation,
                                                       plot_confusion_matrix,
                                                       plot_mc_curve,
                                                       plot_pr_curve)
from edgefirst.validator.metrics.utils.math import mask_iou

if TYPE_CHECKING:
    from edgefirst.validator.evaluators import CombinedParameters, StageTracker
    from edgefirst.validator.datasets import Dataset
    from edgefirst.validator.runners import Runner


class InstanceSegmentationValidator(DetectionValidator):
    """
    Reproduce the validation methods implemented in Ultralytics for
    instance segmentation which involves both bounding boxex and instance
    masks.

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
        dataset: Dataset = None
    ):
        super(InstanceSegmentationValidator, self).__init__(
            parameters=parameters, stage_tracker=stage_tracker,
            runner=runner, dataset=dataset)

        self.segmentation_stats = DetectionStats()
        # Segmentation in Ultralytics uses base detection metrics.
        self.segmentation_metrics = DetectionMetrics(
            parameters=self.parameters.validation,
            detection_stats=self.segmentation_stats,
            instances=self.instances,
            model_name=self.model_name,
            dataset_name=self.dataset_name,
            save_path=self.save_path,
            labels=self.parameters.dataset.labels
        )

        self.detection_drawer = DetectionDrawer()
        self.segmentation_drawer = SegmentationDrawer()

        # Store both detection and segmentation metric results.
        self.multi_metrics = MultitaskMetrics(
            detection_metrics=self.metrics.metrics,
            segmentation_metrics=self.segmentation_metrics.metrics
        )
        self.multi_plots = MultitaskPlots(
            detection_plots=self.metrics.plots,
            segmentation_plots=self.segmentation_metrics.plots
        )

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

        gt_instance: MultitaskInstance
        for gt_instance in self.dataset:
            detections = self.runner.run_single_instance(
                image=gt_instance.image,
            )
            self.filter_gt(gt_instance)

            if detections is None:
                yield {
                    "gt_instance": gt_instance,
                    "dt_instance": None
                }

            dt_instance = MultitaskInstance(gt_instance.image_path)
            boxes, labels, scores, mask = detections
            dt_instance.height = gt_instance.height
            dt_instance.width = gt_instance.width
            dt_instance.boxes = boxes
            dt_instance.labels = labels
            dt_instance.scores = scores
            dt_instance.mask = mask
            self.filter_dt(dt_instance)

            yield {
                "gt_instance": gt_instance,
                "dt_instance": dt_instance,
            }

    def process_seg_batch_v5(
        self,
        dt_instance: MultitaskInstance,
        gt_instance: MultitaskInstance,
    ) -> np.ndarray:
        """
        Processes predicted and ground truth masks to compute IoU matches.

        Parameters
        ----------
        dt_instance : MultitaskInstance
            A prediction instance container with predicted
            bounding boxes and masks.
        gt_instance : MultitaskInstance
            A ground truth instance contaienr with ground truth
            bounding boxes and masks.

        Returns
        -------
        np.ndarray
            Boolean array indicating correct matches per IoU threshold.
        """
        niou = len(self.segmentation_stats.ious)
        gt_cls = gt_instance.labels
        pred_cls = dt_instance.labels

        gt_masks = gt_instance.mask
        pred_masks = dt_instance.mask

        if len(gt_cls) == 0 or len(pred_cls) == 0:
            correct = np.zeros((len(pred_cls), niou), dtype=bool)
        else:
            # Handle 2-dimension masks, but typically this is
            # 3D with shape (n, h, w).
            gt_masks = (gt_masks.reshape(1, -1).astype(np.float32)
                        if gt_masks.ndim == 2 else
                        gt_masks.reshape(gt_masks.shape[0], -1).astype(
                            np.float32))
            pred_masks = (pred_masks.reshape(1, -1).astype(np.float32)
                          if pred_masks.ndim == 2 else
                          pred_masks.reshape(pred_masks.shape[0], -1).astype(
                              np.float32))
            iou = mask_iou(gt_masks, pred_masks)
            correct = self.match_predictions(pred_classes=pred_cls,
                                             true_classes=gt_cls,
                                             iou=iou)
        return correct

    def process_seg_batch_v7(
        self,
        dt_instance: MultitaskInstance,
        gt_instance: MultitaskInstance
    ) -> np.ndarray:
        """
        Placeholder for YOLOv7 segmentation evaluation support.

        Parameters
        ----------
        dt_instance : MultitaskInstance
            A prediction instance container with predicted
            bounding boxes and masks.
        gt_instance : MultitaskInstance
            A ground truth instance contaienr with ground truth
            bounding boxes and masks.

        Returns
        -------
        np.ndarray
            Boolean array indicating correct matches per IoU threshold.
        """
        logger("Validation with YOLOv7 is not yet supported for segmentation. " +
               "Falling back to use Ultralytics.", code="WARNING")
        return self.process_seg_batch_v5(
            dt_instance=dt_instance,
            gt_instance=gt_instance
        )

    def evaluate(self, instance: dict):
        """
        Evaluates a segmentation prediction instance and updates metrics.

        Parameters
        ----------
        instance: dict
            This contains the ground truth and model prediction instances
            with keys "gt_instance", "dt_instance".
        """
        super().evaluate(instance=instance)

        gt_instance: MultitaskInstance = instance.get("gt_instance")
        dt_instance: MultitaskInstance = instance.get("dt_instance")

        if self.parameters.validation.method == "ultralytics":
            correct = self.process_seg_batch_v5(dt_instance=dt_instance,
                                                gt_instance=gt_instance)
        elif self.parameters.validation.method == "yolov7":
            correct = self.process_seg_batch_v7(dt_instance=dt_instance,
                                                gt_instance=gt_instance)
        else:
            correct = np.zeros((0, len(self.segmentation_stats.ious)),
                               dtype=bool)

        self.segmentation_stats.stats["tp"].append(correct)
        self.segmentation_stats.stats["conf"].append(dt_instance.scores)
        self.segmentation_stats.stats["pred_cls"].append(dt_instance.labels)
        self.segmentation_stats.stats["target_cls"].append(gt_instance.labels)

    def visualize(
        self,
        gt_instance: MultitaskInstance,
        dt_instance: MultitaskInstance,
        epoch: int = 0
    ):
        """
        Visualizes predicted and ground truth bounding
        boxes and masks on an image.

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
        # Separate results for the ground truth and detection.
        dt_instance.visual_image = gt_instance.visual_image.copy()

        # Draw the ground truth boxes on the image.
        image = self.detection_drawer.draw_2d_gt_boxes(
            image=gt_instance.visual_image,
            gt_instance=gt_instance,
            method="ultralytics",
            labels=self.parameters.dataset.labels,
        )
        gt_instance.visual_image = np.asarray(image)

        # Filter to visualize only confident scores.
        filt = dt_instance.scores >= 0.25
        dt_instance.boxes = dt_instance.boxes[filt]
        dt_instance.labels = dt_instance.labels[filt]
        dt_instance.scores = dt_instance.scores[filt]

        if (len(dt_instance.mask.shape) >= len(filt) and
                not self.parameters.model.common.semantic):
            dt_instance.mask = dt_instance.mask[filt]

        # Draw the prediction boxes on the image.
        image = self.detection_drawer.draw_2d_dt_boxes(
            image=dt_instance.visual_image,
            dt_instance=dt_instance,
            method="ultralytics",
            labels=self.parameters.dataset.labels,
        )
        dt_instance.visual_image = np.asarray(image)

        # Converting string back to indices.
        gt_instance.labels = np.array([
            self.parameters.dataset.labels.index(label)
            for label in gt_instance.labels], dtype=np.uintp)
        dt_instance.labels = np.array([
            self.parameters.dataset.labels.index(label)
            for label in dt_instance.labels], dtype=np.uintp)

        # Draw the masks prediction and ground truth boxes on the image.
        image = self.segmentation_drawer.mask2maskimage(
            gt_instance=gt_instance,
            dt_instance=dt_instance,
            semantic=self.parameters.model.common.semantic,
        )

        if self.parameters.validation.visualize:
            image.save(os.path.join(self.parameters.validation.visualize,
                                    os.path.basename(gt_instance.image_path)))
        elif self.tensorboard_writer:
            self.tensorboard_writer(
                np.asarray(image), gt_instance.image_path, step=epoch)

    def end(  # pylint: disable=arguments-differ
        self,
        epoch: int = 0,
        reset: bool = True
    ) -> Tuple[MultitaskMetrics, MultitaskPlots]:
        """
        Computes the final metrics from Ultralytics for detection and
        segmentation and generates the validation plots to save the
        results in disk or publishes to Tensorboard.

        Parameters
        ----------
        epoch: int
            This is the training epoch number. This
            parameter is internal for ModelPack usage.
            Standalone validation does not use this parameter.
        reset: bool
            This is an optional parameter that controls the reset state.
            By default, it will reset at the end of validation to erase
            the data in the containers.

        Returns
        -------
        metrics: MultitaskMetrics
            This is a container for the detection and segmentation metrics.
        plots: MultitaskPlots
            This is a container for the validation data for plotting.
        """
        metrics, plots = super().end(epoch=epoch, reset=reset, publish=False)

        logger(
            "Computing instance segmentation metrics...",
            code="INFO"
        )

        self.multi_metrics.detection_metrics = metrics
        self.multi_plots.detection_plots = plots
        self.multi_metrics.timings = metrics.timings

        self.segmentation_metrics.run(full_computation=False)
        self.multi_metrics.segmentation_metrics = deepcopy(
            self.segmentation_metrics.metrics)
        self.multi_plots.segmentation_plots = deepcopy(
            self.segmentation_metrics.plots)

        # Plot Operations
        if self.parameters.validation.plots:
            self.segmentation_metrics.plots.curve_labels = labels2string(
                self.segmentation_metrics.plots.curve_labels,
                self.parameters.dataset.labels
            )

            if self.parameters.validation.visualize or self.tensorboard_writer:
                self.get_seg_plots()

        if self.tensorboard_writer:
            self.tensorboard_writer.publish_metrics(
                metrics=self.multi_metrics,
                parameters=self.parameters,
                step=epoch,
            )
        else:
            table = self.console_writer(metrics=self.multi_metrics,
                                        parameters=self.parameters)

            if self.parameters.validation.visualize:
                self.console_writer.save_metrics(table)

        if reset:
            self.segmentation_metrics.reset()
        return self.multi_metrics, self.multi_plots

    def get_seg_plots(self):
        """
        Reproduces the validation charts from Ultralytics.
        """
        plot_jobs = [
            (plot_confusion_matrix, dict(
                confusion_data=self.metrics.plots.confusion_matrix.matrix,
                labels=self.metrics.plots.confusion_matrix.labels,
                model=self.metrics.metrics.model), "seg_confusion_matrix.png"),
            (plot_pr_curve, dict(
                precision=self.segmentation_metrics.plots.py,
                recall=self.segmentation_metrics.plots.px,
                ap=self.segmentation_metrics.plots.average_precision,
                names=self.parameters.dataset.labels,
                model=self.segmentation_metrics.metrics.model), "seg_pr_curve.png"),
            (plot_mc_curve, dict(
                px=self.segmentation_metrics.plots.px,
                py=self.segmentation_metrics.plots.f1,
                names=self.parameters.dataset.labels,
                model=self.segmentation_metrics.metrics.model,
                ylabel='F1'), "seg_f1_curve.png"),
            (plot_mc_curve, dict(
                px=self.segmentation_metrics.plots.px,
                py=self.segmentation_metrics.plots.precision,
                names=self.parameters.dataset.labels,
                model=self.segmentation_metrics.metrics.model,
                ylabel='Precision'), "seg_precision_curve.png"),
            (plot_mc_curve, dict(
                px=self.segmentation_metrics.plots.px,
                py=self.segmentation_metrics.plots.recall,
                names=self.parameters.dataset.labels,
                model=self.segmentation_metrics.metrics.model,
                ylabel='Recall'), "seg_recall_curve.png"),
        ]
        self.save_plots(plot_jobs)


class SemanticSegmentationValidator(Evaluator):
    """
    Define the validation methods for semantic segmentation valdiation.
    Reproduces EdgeFirst metrics for semantic segmentation::

        1. Grab the ground truth and the model prediction instances per image.
        2. Create semantic masks for both ground truth and model prediction.
        3. Classify the mask pixels as either true predictions or false predictions.
        4. Calculate the mask IoU as the overlap between ground truth and prediction.
        5. Overlay the ground truth and predictions masks on the image.
        6. Calculate the segmentation metrics.

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
        super(SemanticSegmentationValidator, self).__init__(
            parameters=parameters, stage_tracker=stage_tracker,
            runner=runner, dataset=dataset)

        self.segmentation_stats = SegmentationStats()
        self.metrics = SegmentationMetrics(
            parameters=self.parameters.validation,
            segmentation_stats=self.segmentation_stats,
            model_name=self.model_name,
            dataset_name=self.dataset_name,
            save_path=self.save_path
        )
        self.drawer = SegmentationDrawer()
        # The background index is the last label in the labels.
        self.background_index = len(self.parameters.model.labels) - 1

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

        Raises
        ------
        ValueError
            Raised if the model labels and the
            dataset labels are not matching.
        """

        gt_instance: SegmentationInstance
        for gt_instance in self.dataset:
            mask = self.runner.run_single_instance(
                image=gt_instance.image
            )

            if mask is None:
                yield {
                    'gt_instance': gt_instance,
                    'dt_instance': None
                }

            dt_instance = SegmentationInstance(gt_instance.image_path)
            dt_instance.height = gt_instance.height
            dt_instance.width = gt_instance.width
            dt_instance.mask = self.calibrate_mask(mask,
                                                   dt_labels=dt_instance.labels)

            yield {
                'gt_instance': gt_instance,
                'dt_instance': dt_instance
            }

    def calibrate_mask(self, mask: np.ndarray,
                       dt_labels: np.ndarray) -> np.ndarray:
        """
        Map the labels of the mask to the label order of the ground
        truth labels. This ensures the prediction mask and the ground
        truth mask are matching.
        Furthermore, if the model outputs instance segmentation,
        convert it to semantic segmentation.

        Parameters
        ----------
        mask: np.ndarray
            The prediction mask output from the model.
        dt_labels: np.ndarray
            A list of labels for each mask to convert instance
            segmentation to semantic which is needed for
            semantic validation.

        Returns
        -------
        np.ndarray
            The calibrated prediction mask.
        """
        mask = np.squeeze(mask)

        model_labels = self.parameters.model.labels
        dataset_labels = self.parameters.dataset.labels

        # If the mask is instance segmentation, convert to semantic.
        if mask.ndim == 3:
            _, height, width = mask.shape
            semantic_mask = np.zeros((height, width), dtype=np.int32)
            for m, cls in zip(mask, dt_labels):
                semantic_mask[m > 0] = cls
            mask = semantic_mask

        # If the label orders does not match between prediction and dataset,
        # map the prediction indices to the dataset indices.
        if model_labels != dataset_labels:
            # -1 means unmapped/missing
            index_map = np.full(len(model_labels), -1, dtype=int)
            for model_idx, label in enumerate(model_labels):
                if label in dataset_labels:
                    index_map[model_idx] = dataset_labels.index(label)
                else:
                    raise ValueError(
                        f"Label '{label}' not found in dataset labels.")
            mask = index_map[mask]
        return mask

    def evaluate(self, instance: dict):
        """
        Run model evaluation using EdgeFirst validation methods
        for segmentation.

        Parameters
        ----------
        instance: dict
            This contains the ground truth and model predictions instances
            with keys "gt_instance" and "dt_instance".
        """
        gt_instance: SegmentationInstance = instance.get("gt_instance")
        dt_instance: SegmentationInstance = instance.get("dt_instance")

        class_labels = np.unique(np.append(np.unique(gt_instance.mask),
                                           np.unique(dt_instance.mask)))
        gt_mask = gt_instance.mask
        dt_mask = dt_instance.mask

        predictions = dt_mask.flatten()
        ground_truths = gt_mask.flatten()

        if not self.parameters.validation.include_background:
            class_labels = class_labels[class_labels != self.background_index]
            predictions = predictions[predictions != self.background_index]
            ground_truths = ground_truths[ground_truths !=
                                          self.background_index]
            true_predictions, false_predictions, union_gt_dt = classify_mask(
                gt_mask, dt_mask, background_index=self.background_index)
        else:
            true_predictions, false_predictions, union_gt_dt = classify_mask(
                gt_mask, dt_mask, background_index=self.background_index,
                exclude_background=False)

        self.segmentation_stats.capture_class(class_labels,
                                              self.parameters.dataset.labels)
        self.metrics.metrics.add_ground_truths(len(ground_truths))
        self.metrics.metrics.add_predictions(len(predictions))
        self.metrics.metrics.add_true_predictions(true_predictions)
        self.metrics.metrics.add_false_predictions(false_predictions)
        self.metrics.metrics.add_union(union_gt_dt)

        for cl in class_labels:
            # Compute the mask IoU for this class
            m1 = (dt_mask == cl).astype(np.float32).reshape(1, -1)
            m2 = (gt_mask == cl).astype(np.float32).reshape(1, -1)
            if cl not in self.segmentation_stats.ious.keys():
                self.segmentation_stats.ious[cl] = []
            self.segmentation_stats.ious[cl].append(mask_iou(m1, m2))

            gt_class_mask = create_mask_class(
                gt_mask, cl, background_index=self.background_index)
            dt_class_mask = create_mask_class(
                dt_mask, cl, background_index=self.background_index)

            # Evaluate background class
            if cl == self.background_index:
                gt_class_mask = create_mask_background(
                    gt_mask, background_index=self.background_index)
                dt_class_mask = create_mask_background(
                    dt_mask, background_index=self.background_index)

            class_ground_truths = np.sum(gt_mask == cl)
            class_predictions = np.sum(dt_mask == cl)

            # Under classify_mask always exclude background because we are
            # only concerned with this class.
            class_true_predictions, class_false_predictions, union_gt_dt = \
                classify_mask(gt_class_mask, dt_class_mask,
                              background_index=self.background_index)

            datalabel = self.segmentation_stats.get_label_data(
                self.parameters.dataset.labels[cl]
            )

            datalabel.add_true_predictions(class_true_predictions)
            datalabel.add_false_predictions(class_false_predictions)
            datalabel.add_ground_truths(class_ground_truths)
            datalabel.add_predictions(class_predictions)
            datalabel.add_union(union_gt_dt)

    def visualize(
        self,
        gt_instance: SegmentationInstance,
        dt_instance: SegmentationInstance,
        epoch: int = 0
    ):
        """
        Draw segmentation mask results on the image and save
        the results in disk or publish into Tensorboard.

        Parameters
        ----------
        gt_instance: DetectionInstance
            This is the ground truth instance which contains masks
            and labels to draw.
        dt_instance: DetectionInstance
            This is the model detection instance which contains the
            masks and labels to draw.
        epoch: int
            This is the training epoch number. This
            parameter is internal for ModelPack usage.
            Standalone validation does not use this parameter.
        """
        image = self.drawer.mask2maskimage(
            gt_instance, dt_instance, background_index=self.background_index)

        if self.parameters.validation.visualize:
            image.save(os.path.join(self.parameters.validation.visualize,
                                    os.path.basename(gt_instance.image_path)))
        elif self.tensorboard_writer:
            self.tensorboard_writer(
                np.asarray(image), gt_instance.image_path, step=epoch)

    def get_plots(self) -> List[matplotlib.figure.Figure]:
        """
        Generatte EdgeFirst validation plots.

        Returns
        -------
        List[matplotlib.figure.Figure]
            This contains matplotlib figures of the plots.
        """
        plot_jobs = [
            (plot_classification_segmentation, dict(
                class_histogram_data=self.metrics.plots.class_histogram_data,
                model=self.metrics.metrics.model), "class_scores.png"),
        ]
        self.save_plots(plot_jobs)
