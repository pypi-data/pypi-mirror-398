"""
Implmentation of TensorFlow Lite runner for model inference.
"""

from __future__ import annotations

import os
import time
import zipfile
from typing import TYPE_CHECKING, Any, Union

import yaml
import numpy as np

from edgefirst.validator.runners.core import Runner
from edgefirst.validator.publishers.utils.logger import logger

if TYPE_CHECKING:
    from edgefirst.validator.evaluators import ModelParameters, TimerContext


class TFliteRunner(Runner):
    """
    Loads and runs TensorFlow Lite models for inference.

    Parameters
    ----------
    model: Any
        The is typically the path to the model or the loaded TFLite model.
    parameters: ModelParameters
        These are the model parameters set from the command line.
    timer: TimerContext
        A timer object for handling validation timings for the model.

    Raises
    ------
    ImportError
        Raised if tflite_runtime and TensorFlow is not intalled.
    FileNotFoundError
        Raised if the path to the model does not exist.
    """

    def __init__(
        self,
        model: Any,
        parameters: ModelParameters,
        timer: TimerContext
    ):
        super(TFliteRunner, self).__init__(model, parameters, timer=timer)

        try:
            from tflite_runtime.interpreter import Interpreter  # type: ignore
        except ImportError:
            logger("tflite_runtime is not installed. Falling back to TensorFlow.",
                   code="WARNING")
            try:
                import tensorflow as tf  # type: ignore
                Interpreter = tf.lite.Interpreter
            except ImportError as e:
                raise ImportError(
                    "TensorFlow or tflite_runtime is needed to run TFLite models."
                ) from e

        if isinstance(model, str):
            if not os.path.exists(model):
                raise FileNotFoundError(
                    "The model '{}' does not exist.".format(model))

            ext_delegate = self.select_delegates()
            logger(f"Engine: {self.parameters.engine}", code="INFO")

            if ext_delegate:
                self.model = Interpreter(
                    model_path=model,
                    experimental_delegates=[ext_delegate]
                )
            else:
                self.model = Interpreter(model_path=model)
        self.model.allocate_tensors()

        self.input_details = self.model.get_input_details()
        self.output_details = self.model.get_output_details()
        self.parameters.common.input_quantization = self.input_details[0][
            "quantization"]
        metadata = self.load_model_metadata(model)
        self.init_decoder(metadata=metadata, outputs=self.output_details)

        # The model NumPy view object.
        self.parameters.common.input_tensor = self.model.tensor(
            self.input_details[0]["index"])

        if self.parameters.warmup > 0:
            self.warmup()

    def load_model_metadata(self, model_path: str) -> Union[dict, None]:
        """
        Returns the model metadata for decoding the outputs.

        Parameters
        ----------
        model_path: str
            The path to the model.

        Returns
        -------
        Union[dict, None]
            The model metadata if it exists. Otherwise None is returned.
        """
        metadata = None

        if zipfile.is_zipfile(model_path):
            with zipfile.ZipFile(model_path) as zip_ref:
                if "edgefirst.yaml" in zip_ref.namelist():
                    with zip_ref.open("edgefirst.yaml") as f:
                        yaml_text = f.read().decode("utf-8")
                        metadata = yaml.safe_load(yaml_text)
                else:
                    logger(
                        "The model file does not contain the 'edgefirst.yaml' metadata.",
                        code="WARNING")

                if "labels.txt" in zip_ref.namelist():
                    with zip_ref.open("labels.txt") as f:
                        labels_text = f.read().decode("utf-8")
                        labels = [line.rstrip()
                                  for line in labels_text.splitlines()
                                  if line not in ["\n", "", "\t"]]
                        self.parameters.labels = labels
                else:
                    logger(
                        "The model file does not contain the 'labels.txt'.",
                        code="WARNING")

        if ((self.parameters.labels is None
             or len(self.parameters.labels) == 0) and
                self.parameters.labels_path is not None):
            if os.path.exists(self.parameters.labels_path):
                with open(self.parameters.labels_path, 'r', encoding="utf-8") as f:
                    self.parameters.labels = [
                        line.rstrip()
                        for line in f.readlines()
                        if line not in ["\n", "", "\t"]
                    ]

        if metadata is None and self.parameters.config_path is not None:
            if os.path.exists(self.parameters.config_path):
                with open(self.parameters.config_path, encoding="utf-8") as file:
                    metadata = yaml.safe_load(file)
            else:
                logger(
                    f"The model metadata path '{self.parameters.config_path}' does not exist.",
                    code="WARNING")

        self.set_metadata_parameters(metadata)
        return metadata

    def select_delegates(self) -> Any:
        """
        Specify the delegates to load based on
        the type of engine specified.

        Returns
        -------
        Any
            This is either the loaded delegate object or None
            if it doesn't exist.
        """
        try:
            from tflite_runtime.interpreter import load_delegate  # type: ignore
        except ImportError:
            try:
                import tensorflow as tf  # type: ignore
                load_delegate = tf.lite.experimental.load_delegate
            except ImportError as e:
                raise ImportError(
                    "TensorFlow or tflite_runtime is needed to run TFLite models."
                ) from e

        ext_delegate = None
        if (os.path.exists(self.parameters.engine) and
                self.parameters.engine.endswith(".so")):
            ext_delegate = load_delegate(self.parameters.engine, {})
        elif self.parameters.engine.lower() == "npu":
            if os.path.exists("/usr/lib/libvx_delegate.so"):
                self.parameters.engine = "/usr/lib/libvx_delegate.so"
                ext_delegate = load_delegate(self.parameters.engine, {})
                logger("Using '/usr/lib/libvx_delegate.so' for NPU inference.",
                       code="INFO")
            elif os.path.exists("/usr/lib/libneutron_delegate.so"):
                self.parameters.engine = "/usr/lib/libneutron_delegate.so"
                ext_delegate = load_delegate(self.parameters.engine, {})
                logger("Using '/usr/lib/libneutron_delegate.so' for NPU inference.",
                       code="INFO")
            else:
                logger(
                    "Specified NPU, but cannot find '/usr/lib/lib<>_delegate.so'. " +
                    "Specify the path to libvx_delegate.so or libneutron_delegate.so " +
                    "in your system. Falling back to use the CPU instead.", code="WARNING")
                self.parameters.engine = "cpu"
        elif self.parameters.engine.lower() == "gpu":
            logger(
                "Inference with the GPU is currently not supported for TFLite. " +
                "Falling back to use the CPU instead.", code="WARNING")
            self.parameters.engine = "cpu"
        return ext_delegate

    def run_single_instance(self, image: np.ndarray = None) -> Any:
        """
        Run TFLite inference on a single image and record the timings.

        Parameters
        ----------
        image: np.ndarray
            The input image after being preprocessed.
            Typically this is an RGB image array. This is by default None.
            Currently setting the image tensor using the logic below.

            .. code-block:: python

                input_tensor = self.model.tensor(self.input_details[0]["index"])
                np.copyto(input_tensor(), image)

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
            self.model.invoke()

        start = time.perf_counter()
        outputs = [self.model.get_tensor(output["index"])
                   for output in self.output_details]
        elapsed = time.perf_counter() - start

        # Postprocessing
        outputs = self.postprocessing(outputs)

        # Fetching the tensor as part of the postprocess time.
        self.timer.add_time("output", elapsed * 1e3)  # Convert to ms.

        return outputs

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
        return self.input_details[0]["dtype"]

    def get_input_shape(self) -> np.ndarray:
        """
        Grabs the model input shape.

        Returns
        -------
        np.ndarray
            The model input shape (batch size, channels, height, width) or
            (batch size, height, width, channels).
        """
        return self.input_details[0]["shape"]
