"""
Implementation for the TensorRT model runner.
"""

from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING, Any, Tuple

import numpy as np

from edgefirst.validator.runners.core import Runner

if TYPE_CHECKING:
    from edgefirst.validator.evaluators import ModelParameters, TimerContext


class TensorRTRunner(Runner):
    """
    Loads and runs TensorRT Engines (.engine, .trt).  These models
    are intended to be deployed on a device with a dedicated GPU.
    This implementation was taken from the following sources:
    https://github.com/NVIDIA/TensorRT/blob/main/samples/python/efficientdet/infer.py
    https://github.com/ultralytics/ultralytics/blob/main/ultralytics/nn/autobackend.py#L326

    Parameters
    ----------
    model: Any
        This is typically the path to the model or the loaded TensorRT model.
    parameters: ModelParameters
        These are the model parameters set from the command line.
    timer: TimerContext
        A timer object for handling validation timings for the model.

    Raises
    ------
    ImportError
        Missing tensorrt library.
    FileNotFoundError
        Raised if the path to the model does not exist.
    """

    def __init__(
        self,
        model: Any,
        parameters: ModelParameters,
        timer: TimerContext
    ):
        super(TensorRTRunner, self).__init__(model, parameters, timer=timer)

        try:
            import tensorrt as trt
        except ImportError as e:
            raise ImportError(
                "tensorrt is needed to run TensorRT models.") from e
        try:
            import pycuda.driver as cuda  # type: ignore
        except ImportError as e:
            raise ImportError(
                "pycuda is needed to perform memory allocations for TensorRT."
            ) from e

        # Use autoprimaryctx if available (pycuda >= 2021.1) to
        # prevent issues with other modules that rely on the primary
        # device context.
        try:
            import pycuda.autoprimaryctx  # type: ignore # pylint: disable=unused-import
        except ModuleNotFoundError:
            try:
                import pycuda.autoinit  # type: ignore
            except ImportError as e:
                raise ImportError(
                    "supported NVIDIA GPU device is needed.") from e

        # TensorRT are intended to run on the GPU.
        self.parameters.engine = "gpu"
        self.logger = trt.Logger(trt.Logger.INFO)
        trt.init_libnvinfer_plugins(self.logger, namespace="")

        # Read file
        if isinstance(model, str):
            with open(model, "rb") as f, trt.Runtime(self.logger) as runtime:
                assert runtime
                try:
                    meta_len = int.from_bytes(
                        f.read(4), byteorder="little")  # read metadata length
                    metadata = json.loads(
                        f.read(meta_len).decode("utf-8"))  # read metadata
                    dla = metadata.get("dla", None)
                    if dla is not None:
                        runtime.DLA_core = int(dla)
                except UnicodeDecodeError:
                    # engine file may lack embedded Ultralytics metadata
                    f.seek(0)
                self.model = runtime.deserialize_cuda_engine(
                    f.read())  # read engine
                assert self.model

        self.context = self.model.create_execution_context()
        assert self.context

        self.output_names = []
        self.output = []
        self.input = []
        self.allocations = []
        self.scales = []  # Float values for dequantizing INT8 outputs.

        num = range(self.model.num_bindings if hasattr(self.model, "num_bindings")
                    else self.model.num_io_tensors)

        for i in num:
            name = self.model.get_tensor_name(i)
            dtype = np.dtype(trt.nptype(self.model.get_tensor_dtype(name)))
            shape = tuple(self.context.get_tensor_shape(name))
            is_input = self.model.get_tensor_mode(
                name) == trt.TensorIOMode.INPUT
            if is_input:
                if -1 in tuple(self.model.get_tensor_shape(name)):
                    self.context.set_input_shape(
                        name, tuple(self.model.get_tensor_profile_shape(name, 0)[1]))
            else:
                self.output_names.append(name)

                dyn_range = None
                if hasattr(self.model, "get_tensor_dynamic_range"):
                    dyn_range = self.model.get_tensor_dynamic_range(i)
                elif hasattr(self.model, "get_binding_dynamic_range"):
                    dyn_range = self.model.get_binding_dynamic_range(i)

                if dyn_range and dyn_range > 0:
                    scale = float(dyn_range) / 127.0
                    self.scales.append(scale)

            shape = tuple(self.context.get_tensor_shape(name))
            size = dtype.itemsize
            for s in shape:
                size *= s
            allocation = cuda.mem_alloc(size)
            host_allocation = None if is_input else np.zeros(shape, dtype)

            binding = {
                "index": i,
                "name": name,
                "dtype": dtype,
                "shape": list(shape),
                "allocation": allocation,
                "host_allocation": host_allocation,
            }

            self.allocations.append(allocation)
            if is_input:
                self.input.append(binding)
            else:
                self.output.append(binding)

        assert len(self.input) > 0
        assert len(self.output) > 0
        assert len(self.allocations) > 0

        metadata = self.load_model_metadata()
        outputs = [np.zeros(out["shape"], np.dtype(out["dtype"]))
                   for out in self.output]
        self.init_decoder(metadata=metadata, outputs=outputs)

        if self.parameters.warmup > 0:
            self.warmup()

    def infer(self, image: np.ndarray) -> list:
        """
        Executes inference on a batch of images.

        Parameters
        ----------
        image: np.ndarray
            The image input after being preprocessed.
            Typically this is an RGB image array with the same
            input shape as the model.

        Returns
        -------
        list
            Raw model outputs stored inside a list.

        Raises
        ------
        ImportError
            Raised if the pycuda library is not installed.
        """
        try:
            import pycuda.driver as cuda  # type: ignore
        except ImportError as e:
            raise ImportError(
                "pycuda driver is needed for TensorRT inference.") from e

        start = time.perf_counter()
        # Copy I/O and Execute.
        image = np.ascontiguousarray(image)
        cuda.memcpy_htod(self.input[0]['allocation'], image)
        elapsed = time.perf_counter() - start
        # Setting the tensor as part of the preprocess time.
        self.timer.add_time("input", elapsed * 1e3)  # Convert to ms.

        with self.timer.time("inference"):
            self.context.execute_v2(self.allocations)

    def run_single_instance(self, image: np.ndarray) -> Any:
        """
        Run TensorRT inference on a single image and record the timings.
        Memory copying to and from the GPU device be performed here.

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
        try:
            import pycuda.driver as cuda  # type: ignore
        except ImportError as e:
            raise ImportError(
                "pycuda driver is needed for TensorRT inference.") from e

        # Inference
        self.infer(image)

        start = time.perf_counter()
        for output in self.output:
            cuda.memcpy_dtoh(output['host_allocation'], output['allocation'])

        # Dequantize INT8 outputs if engine provides dynamic ranges.
        if len(self.scales) > 0:
            outputs = []
            for i, out in enumerate(self.output):
                o = out['host_allocation']
                # only handle integer types here
                if o.dtype in [np.int8, np.uint8]:
                    o = o.astype(np.float32) * self.scales[i]
                outputs.append(o)
        else:
            outputs = [o['host_allocation'] for o in self.output]
        elapsed = time.perf_counter() - start

        # Postprocessing
        outputs = self.postprocessing(outputs)

        # Fetching the tensor as part of the postprocess time.
        self.timer.add_time("output", elapsed * 1e3)  # Convert to ms.

        return outputs

    def input_spec(self) -> Tuple[tuple, np.dtype]:
        """
        Grabs the specs for the input tensor
        of the network. Useful to prepare memory allocations.

        Returns
        -------
        shape: tuple
            The shape of the input tensor.
        dtype: np.dtype
            The input datatype.
        """
        return self.input[0]['shape'], self.input[0]['dtype']

    def output_spec(self) -> list:
        """
        Grabs the specs for the output tensors of the network.
        Useful to prepare memory allocations.

        Returns
        -------
        list
            A list with two items per element, the shape and (numpy)
            datatype of each output tensor.
        """
        specs = list()
        for o in self.output:
            specs.append((o['shape'], o['dtype']))
        return specs

    def get_input_type(self) -> np.dtype:
        """
        This returns the input type of the model for the
        input with shape in the form
        (batch size, channels, height, width) or
        (batch size, height, width, channels).

        Returns
        -------
        np.dtype
            The input type of the model.
        """
        return self.input[0]['dtype']

    def get_input_shape(self) -> list:
        """
        This fetches the model input shape.

        Returns
        -------
        list
            The model input shape
            [batch size, channels, height, width] or
            [batch size, height, width, channels].
        """
        return self.input[0]['shape']
