"""
Defines the TensorBoardPublisher class for publishing images
and metrics to TensorBoard.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Optional

import numpy as np

from edgefirst.validator.publishers.utils.table import (segmentation_table,
                                                        detection_table,
                                                        multitask_table)

if TYPE_CHECKING:
    from edgefirst.validator.evaluators import CombinedParameters
    from edgefirst.validator.metrics import Metrics


class TensorBoardPublisher:
    """
    Used to publish the images and the metrics into TensorBoard.

    Parameters
    ----------
    logdir: str
        This is the path to save the tfevents file.
    writer: TensorboardWriter
        If this is provided, then a writer will be declared in this class.
    """

    def __init__(
        self,
        logdir: Optional[str] = None,
        writer: Optional[TensorBoardPublisher] = None
    ):
        self.error_message = (
            "TensorFlow library is needed to use Tensorboard.")

        try:
            os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
            import tensorflow as tf
        except ImportError as e:
            raise ImportError(self.error_message) from e

        self.logdir = logdir
        self.writer = writer

        if logdir:
            self.writer = tf.summary.create_file_writer(self.logdir)

    def __call__(self, image: np.ndarray, image_path: str, step: int = 0):
        """
        When it is called, it publishes the image results into Tensorboard.

        Parameters
        ----------
        image: np.ndarray
            The image array with shape (height, width, 3)
            to display to Tensorboard.
        image_path: str
            The path to the image in disk.
        step: int
            This represents the epoch number when training a model.
            For standalone validation, set as 0.
        """
        try:
            os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
            import tensorflow as tf
        except ImportError as e:
            raise ImportError(self.error_message) from e

        with self.writer.as_default():
            nimage = np.expand_dims(image, 0)
            tf.summary.image(os.path.basename(image_path), nimage, step=step)
            self.writer.flush()

    def publish_metrics(
        self,
        metrics: Metrics,
        parameters: CombinedParameters,
        step: int = 0
    ) -> str:
        """
        Publishes the validation metrics into Tensorboard.

        Parameters
        ----------
        metrics: Metrics
            This is the metrics computed during validation.
        parameters: CombinedParameters
            This contains the model, validation, and dataset parameters
            set from the command line.
        step: int
            This is the iteration number which represents the
            epoch number when training a model.

        Returns
        -------
        str
            The formatted validation table showing the metrics, parameters,
            and model timings.
        """
        try:
            os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
            import tensorflow as tf
        except ImportError as e:
            raise ImportError(self.error_message) from e

        with self.writer.as_default():
            table = ""
            if parameters.model.common.with_boxes and parameters.model.common.with_masks:
                table = multitask_table(metrics, parameters)
            elif parameters.model.common.with_boxes:
                table = detection_table(metrics, parameters)
            elif parameters.model.common.with_masks:
                table = segmentation_table(metrics, parameters)

            tf.summary.text("", table, step=step)
            self.writer.flush()

        return table
