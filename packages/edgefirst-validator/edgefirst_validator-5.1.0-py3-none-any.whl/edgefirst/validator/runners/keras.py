"""
Implementations for the Keras model runner.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

import numpy as np

from edgefirst.validator.runners.core import Runner

if TYPE_CHECKING:
    from edgefirst.validator.evaluators import ModelParameters, TimerContext


class KerasRunner(Runner):
    """
    Loads and runs the Keras (.h5, .keras) models using the TensorFlow library.

    Parameters
    ----------
    model: str or tf.keras.Model
        The path to the model or the loaded keras model.
    parameters: ModelParameters
        These are the model parameters set from the command line.
    timer: TimerContext
        A timer object for handling validation timings for the model.

    Raises
    ------
    ImportError
        Raised if the TensorFlow library is not installed.
    FileNotFoundError
        Raised if the path to the model does not exist.
    """

    def __init__(
        self,
        model: Any,
        parameters: ModelParameters,
        timer: TimerContext
    ):
        super(KerasRunner, self).__init__(model, parameters, timer=timer)

        # Load Argmax dependency needed for keras
        try:
            from deepview.modelpack.utils.argmax import Argmax  # pylint: disable=unused-import
        except ImportError:
            pass

        try:
            os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
            import tensorflow as tf  # type: ignore
        except ImportError as e:
            raise ImportError(
                "TensorFlow is needed to run keras models.") from e

        if isinstance(model, str):
            if not os.path.exists(model):
                raise FileNotFoundError(
                    "The model '{}' does not exist.".format(model))

            if os.path.exists(os.path.join(model, "saved_model.pb")):
                self.model = tf.saved_model.load(model)
                self.input = self.model.signatures["serving_default"].inputs
                outputs = self.model.signatures["serving_default"].outputs
            else:
                self.model = tf.keras.models.load_model(model, compile=False)
                outputs = self.model.output
                self.input = self.model.input

        metadata = self.load_model_metadata()

        # Removing the None for batch size, so that
        # the shapes match inside the metadata.
        outputs = [np.zeros((1, *out.shape[1:])) for out in outputs]

        self.init_decoder(
            metadata=metadata,
            outputs=outputs)  # pylint: disable=E0606

        if self.parameters.warmup > 0:
            self.warmup()

    def run_single_instance(self, image: np.ndarray) -> Any:
        """
        Run Keras inference on a single image and record the timings.

        Parameters
        ----------
        image: np.ndarray
            The input image after being preprocessed.
            Typically this is an RGB image array.

        Returns
        -------
        Any
            This could either return detection outputs after NMS.
                np.ndarray
                    The prediction bounding boxes.. [[box1], [box2], ...].
                np.ndarray
                    The prediction labels.. [cl1, cl2, ...].
                np.ndarray
                    The prediction confidence scores.. [score, score, ...]
                    normalized between 0 and 1.
            This could also return segmentation masks.
                np.ndarray
        """
        # Inference
        with self.timer.time("inference"):
            outputs = self.model(image)

        # Postprocessing
        return self.postprocessing(outputs)

    def get_input_type(self) -> np.dtype:
        """
        This returns the input type of the model with shape
        (batch size, channels, height, width) or
        (batch size, height, width, channels).

        Returns
        -------
        np.dtype
            The input type of the model.
        """
        try:
            try:
                return self.model.input.dtype.as_numpy_dtype
            except AttributeError:
                return np.dtype(self.model.input.dtype)
        except AttributeError:
            return np.dtype(self.input[0].dtype)

    def get_input_shape(self) -> np.ndarray:
        """
        Grabs the model input shape.

        Returns
        -------
        np.ndarray
            The model input shape (batch size, channels, height, width) or
            (batch size, height, width, channels).
        """
        try:
            return self.model.input.shape
        except AttributeError:
            return self.input[0].shape
