"""
Implementations for the Kinara model runner.
"""

from __future__ import annotations

import os
import time
import threading
from typing import TYPE_CHECKING, Any

import numpy as np

from edgefirst.validator.runners.core import Runner
from edgefirst.validator.runners.processing.decode import dequantize_kinara

if TYPE_CHECKING:
    from edgefirst.validator.evaluators import ModelParameters, TimerContext


class KinaraRunner(Runner):
    """
    Loads and runs Kinara models for inference.

    Parameters
    ----------
    model: Any
        This is typically the path to the model (.dvm)
        or the loaded Kinara model.
    parameters: ModelParameters
        These are the model parameters set from the command line.
    timer: TimerContext
        A timer object for handling validation timings for the model.
    socket_path : str, optional
                Path to the UNIX socket for DVSession.

    Raises
    ------
    ImportError
        Missing Kinara library.
    FileNotFoundError
        Raised if the path to the model does not exist.
    """

    def __init__(
        self,
        model: Any,
        parameters: ModelParameters,
        timer: TimerContext,
        socket_path: str = "/var/run/ara2.sock"
    ):
        super(KinaraRunner, self).__init__(model, parameters, timer)

        self.socket_path = socket_path
        self.conn = None
        self.endpoints = None
        self.loaded_model = None
        self._lock = threading.Lock()
        self.start()

        if isinstance(model, str):
            if not os.path.exists(model):
                raise FileNotFoundError(
                    "The model '{}' does not exist.".format(model))
            self.load_model(model)

        self.input_param = self.model.input_param[0]
        self.preprocess_param = self.input_param.preprocess_param
        self.parameters.common.input_quantization = (
            self.preprocess_param.qn, self.preprocess_param.offset)

        outputs = []
        for output_param in self.model.output_param:
            bpp = output_param.bpp
            dtype = np.int8
            if bpp == 1:
                dtype = (np.int8 if output_param.postprocess_param.is_signed
                         else np.uint8)
            elif bpp == 2:
                dtype = (np.int16 if output_param.postprocess_param.is_signed
                         else np.uint16)
            elif bpp == 4:
                dtype = (np.int32 if output_param.postprocess_param.is_signed
                         else np.uint32)

            outputs.append(
                {
                    "shape": np.array([1, output_param.nch,
                                       output_param.height]),
                    "quantization": [output_param.postprocess_param.qn,
                                     output_param.postprocess_param.offset],
                    "channels_first": False,
                    "dtype": dtype
                }
            )

        metadata = self.load_model_metadata()
        self.init_decoder(metadata=metadata, outputs=outputs)
        if self.parameters.warmup > 0:
            self.warmup()

    def start(self):
        """
        Start DVSession and fetch available endpoints.

        Raises
        ------
        RuntimeError
            If session creation or endpoint retrieval fails.
        """
        from edgefirst.validator.runners.processing.dvapi import DVSession

        ret, self.conn = DVSession.create_via_unix_socket(self.socket_path)
        if ret != 0:
            raise RuntimeError("Failed to create DVSession")
        ret, self.endpoints = self.conn.get_endpoint_list()
        if ret != 0:
            raise RuntimeError("Failed to get endpoints")

    def load_model(self, model_path: str):
        """
        Load model from file into DVM endpoint.

        Parameters
        ----------
        model_path : str
            Path to the model file to load.

        Raises
        ------
        RuntimeError
            If model loading fails.
        """
        with self._lock:
            ret, self.model = self.conn.load_model_from_file(
                endpoint=self.endpoints[0], model_path=model_path)
            if ret != 0:
                raise RuntimeError("Failed to load model")

    def infer(self, input_tensor, timeout: int = 50000):
        """
        Run synchronous inference on input tensor.

        Parameters
        ----------
        image : DVTensor
            Input tensor for inference.
        timeout : int, optional
            Timeout in milliseconds for inference.

        Returns
        -------
        List[DVTensor]
                Inference response outputs from the model.

        Raises
        ------
        RuntimeError
                If inference execution fails.
        """
        # thread-safe single-call wrapper
        with self._lock:
            ret, response = self.model.infer_sync(
                [input_tensor], timeout=timeout, endpoint=self.endpoints[0])
        if ret != 0:
            raise RuntimeError("Inference failed")
        return response

    def run_single_instance(self, image: np.ndarray) -> Any:
        """
        Run Kinara inference on a single image and record the timings.

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
        from edgefirst.validator.runners.processing.dvapi import DVTensor

        start = time.perf_counter()
        input_tensor = DVTensor(image.flatten(), self.input_param)
        elapsed = time.perf_counter() - start
        # Converting the tensor as part of the preprocess time.
        self.timer.add_time("input", elapsed * 1e3)  # Convert to ms.

        # Inference
        with self.timer.time("inference"):
            response = self.infer(input_tensor)

        start = time.perf_counter()
        output = dequantize_kinara(
            response.get_output_tensors(),
            method=self.parameters.nms)

        outputs = []
        for meta in self.outputs.metadata["outputs"]:
            outputs.append(
                output[meta["index"]].reshape(meta["shape"])
            )
        elapsed = time.perf_counter() - start

        # Postprocessing
        outputs = self.postprocessing(outputs)

        # Fetching the tensor as part of the postprocess time.
        self.timer.add_time("output", elapsed * 1e3)  # Convert to ms.

        return outputs

    def stop(self):
        """
        Close DVSession connection gracefully.
        Attempts to close the session and suppresses any exceptions.
        """
        try:
            self.conn.close()
        except Exception:  # pylint: disable=broad-exception-caught
            try:
                self.conn.__exit__(None, None, None)
            except Exception:  # pylint: disable=broad-exception-caught
                pass

    def get_input_type(self):
        """
        This returns the input type of the model. Kinara models
        are always quantized in either INT8 or UINT8 datatypes.

        Returns
        -------
        np.dtype
            The input type of the model.
        """
        if self.preprocess_param.is_signed:
            return np.int8
        return np.uint8

    def get_input_shape(self):
        """
        This fetches the model input shape. Kinara models are
        always channels first.

        Returns
        -------
        np.ndarray
            The model input shape (batch size, channels, height, width).
        """
        input_shape = (self.input_param.batch_size,
                       self.input_param.nch,
                       self.input_param.height,
                       self.input_param.width)
        return input_shape
