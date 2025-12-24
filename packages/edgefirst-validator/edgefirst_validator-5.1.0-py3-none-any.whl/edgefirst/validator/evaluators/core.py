"""
Implementations of the core evaluator class for model validation.
"""

from __future__ import annotations

import os
from copy import deepcopy
from typing import TYPE_CHECKING, Tuple, List

import numpy as np
import matplotlib.figure

from edgefirst.validator.publishers import ConsolePublisher, TensorBoardPublisher
from edgefirst.validator.datasets import InstanceCollection
from edgefirst.validator.datasets.utils.annotation_transforms import labels2string
from edgefirst.validator.publishers.utils.logger import logger
from edgefirst.validator.visualize.utils.plots import (figure2numpy,
                                                       close_figures)

if TYPE_CHECKING:
    from edgefirst.validator.evaluators import CombinedParameters, StageTracker
    from edgefirst.validator.datasets import Dataset
    from edgefirst.validator.metrics import Metrics
    from edgefirst.validator.runners import Runner
    from edgefirst.validator.metrics import Plots


class Evaluator:
    """
    Abstract class that provides a template for the
    Evaluators (detection or segmentation).

    Parameters
    ----------
    parameters: CombinedParameters
        This is a container for the model, dataset, and validation parameters
    stage_tracker: StageTracker
        The object used for tracking and displaying stages.
    runner: Runner
        This object provides methods to run inference on the model provided.
    dataset: Dataset
        A type of dataset object responsible for reading different types
        of datasets such as Darknet, TFRecords, or EdgeFirst Datasets.
    """

    def __init__(
        self,
        parameters: CombinedParameters,
        stage_tracker: StageTracker,
        runner: Runner,
        dataset: Dataset,
    ):
        self.parameters = parameters
        self.stage_tracker = stage_tracker
        self.runner = runner
        self.dataset = dataset

        self.console_writer = ConsolePublisher(
            self.parameters.validation.visualize)
        self.tensorboard_writer = None
        if self.parameters.validation.tensorboard:
            self.tensorboard_writer = TensorBoardPublisher(
                self.parameters.validation.tensorboard)

        self.instances = InstanceCollection(stage_tracker=self.stage_tracker)
        self.model_name = os.path.basename(os.path.normpath(
            self.parameters.model.model_path))
        if os.path.isfile(self.parameters.dataset.dataset_path):
            self.dataset_name = os.path.basename(os.path.normpath(
                os.path.dirname(self.parameters.dataset.dataset_path)))
        else:
            self.dataset_name = os.path.basename(os.path.normpath(
                self.parameters.dataset.dataset_path))

        if self.parameters.validation.tensorboard:
            self.save_path = self.parameters.validation.tensorboard
        elif self.tensorboard_writer:
            self.save_path = self.tensorboard_writer.logdir
        elif self.parameters.validation.visualize:
            self.save_path = self.parameters.validation.visualize
        else:
            self.save_path = None

        self.metrics = None
        self.confusion_matrix = None

        # This counter is used to determine the number of images saved.
        self.counter = 0

    def instance_collector(self):
        """Abstract Method"""
        raise NotImplementedError("This is an abstract method")

    def evaluate(self, instance: dict):
        """Abstract Method"""

    def single_evaluation(self, instance: dict, epoch: int, save_image: bool):
        """
        Run model evaluation on a single image/sample.

        Parameters
        ----------
        instance: dict
            This contains the ground truth and model prediction instances
            with keys "gt_instance", "dt_instance".
        epoch: int
            This is the training epoch number. This
            parameter is internal for ModelPack usage.
            Standalone validation does not use this parameter.
        save_image: bool
            If set to True, this will save the image
            with drawn bounding box results.
        """
        self.evaluate(instance=instance)
        gt_instance = instance.get("gt_instance", None)
        dt_instance = instance.get("dt_instance", None)

        if save_image:
            # Visualization for metrics deployment happens elsewhere.
            # Any mask visualization happens here.
            if (not self.parameters.validation.deploy_metrics or
                    self.parameters.model.common.with_masks):
                # Convert labels from integers to string for detection.
                gt_instance.labels = np.array(labels2string(
                    gt_instance.labels, self.parameters.dataset.labels))
                dt_instance.labels = np.array(labels2string(
                    dt_instance.labels, self.parameters.dataset.labels))
                self.visualize(gt_instance, dt_instance, epoch=epoch)
                # Image has already been saved.
                gt_instance.visual_image = None
        else:
            # Do not store the image if not needed.
            gt_instance.visual_image = None

        # Resetting the image to avoid large instances.
        gt_instance.image = None
        dt_instance.image = None
        dt_instance.visual_image = None
        # Collect gathered instances for deployment metric computations.
        self.instances.append_instance(
            gt_instance=gt_instance,
            dt_instance=dt_instance
        )

    def group_evaluation(self, epoch: int = 0, reset: bool = True):
        """
        Runs model validation on all samples in the dataset.

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
        """
        save_image = bool(self.parameters.validation.visualize or
                          self.parameters.validation.tensorboard)

        for instance in self.instance_collector():
            if self.parameters.validation.display >= 0:
                if self.counter < self.parameters.validation.display:
                    save_image = True
                    self.counter += 1
                else:
                    save_image = False

            if instance.get("dt_instance", None) is None:
                logger(
                    "VisionPack Trial Expired. Please use a licensed version" +
                    " for complete validation. Contact support@au-zone.com" +
                    " for more information.", code="WARNING")
                break

            self.single_evaluation(
                instance=instance, epoch=epoch, save_image=save_image)
        return self.end(epoch=epoch, reset=reset)

    def visualize(self, gt_instance: dict, dt_instance: dict, epoch: int = 0):
        """Absract Method"""
        raise NotImplementedError("This is an abstract method")

    def end(
        self,
        epoch: int = 0,
        reset: bool = True,
        publish: bool = True
    ) -> Tuple[Metrics, Plots]:
        """
        Computes the final metrics and generates the validation plots
        to save the results in disk or publishes to Tensorboard.

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
        publish: bool
            Specify to publish and print the metrics. Default to True.

        Returns
        -------
        metrics: Metrics
            This is a container for the detection metrics.
        plots: Plots
            This is a container for the validation data for plotting.
        """
        if hasattr(self.runner, "stop"):
            self.runner.stop()

        if self.runner:
            self.metrics.metrics.timings = self.runner.timer.to_dict()
        self.metrics.run()

        # Plot Operations
        if self.parameters.validation.plots:
            if self.parameters.model.common.with_boxes:
                self.metrics.plots.curve_labels = labels2string(
                    self.metrics.plots.curve_labels, self.parameters.dataset.labels)

            if self.parameters.validation.visualize or self.tensorboard_writer:
                self.get_plots()

        if publish:
            # Metric Operations
            if self.tensorboard_writer:
                self.tensorboard_writer.publish_metrics(
                    metrics=self.metrics.metrics,
                    parameters=self.parameters,
                    step=epoch,
                )
            else:
                table = self.console_writer(metrics=self.metrics.metrics,
                                            parameters=self.parameters)
                if self.parameters.validation.visualize:
                    self.console_writer.save_metrics(table)

            if self.parameters.validation.csv_out:
                self.console_writer.save_csv_metrics(
                    metrics=self.metrics.metrics, parameters=self.parameters)

        # Prevent the reset from taking effect.
        metrics = deepcopy(self.metrics.metrics)
        plots = deepcopy(self.metrics.plots)
        if reset:
            self.metrics.reset()
        return metrics, plots

    def stop(self):
        """
        Stops any active running processes.
        """
        if hasattr(self.runner, "stop"):
            self.runner.stop()

    def get_plots(self) -> List[matplotlib.figure.Figure]:
        """Absract Method"""

    def save_plots(self, plot_jobs: List, epoch: int = 0):
        """
        Save the validation plots to disk or publish into Tensorboard.

        Parameters
        ----------
        plot_jobs: List
            A list of plot jobs to save or publish. Each plot job is a tuple
            containing the plotting function, its keyword arguments,
            and the filename to save.
        epoch: int
            This is the training epoch number. This
            parameter is internal for ModelPack usage.
            Standalone validation does not use this parameter.
        """
        plots = []
        plot_jobs = self.stage_tracker.stage_generator(
            plot_jobs, stage_name="stage_vfigures", colour="green")
        for plot_job, kwargs, name in plot_jobs:
            fig = plot_job(**kwargs)
            plots.append(fig)

            if self.parameters.validation.visualize:
                fig.savefig(
                    os.path.join(
                        self.parameters.validation.visualize,
                        name),
                    bbox_inches="tight"
                )
            elif self.tensorboard_writer:
                nimage = figure2numpy(fig)
                self.tensorboard_writer(
                    nimage,
                    f"{self.metrics.metrics.model}_{name}",
                    step=epoch
                )
        close_figures(plots)
