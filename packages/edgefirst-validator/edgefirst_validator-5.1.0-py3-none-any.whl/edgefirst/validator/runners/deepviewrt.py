"""
Implements the DeepViewRT model runner using the VAAL API.
"""

from __future__ import annotations

import os
from time import monotonic_ns as clock_now
from typing import TYPE_CHECKING, Any

import numpy as np

from edgefirst.validator.runners.processing.outputs import Outputs
from edgefirst.validator.runners.core import Runner
from edgefirst.validator.publishers.utils.logger import logger

if TYPE_CHECKING:
    from edgefirst.validator.evaluators import ModelParameters, TimerContext


class DeepViewRTRunner(Runner):
    """
    Loads and runs DeepViewRT models using the VAAL API.

    Parameters
    ----------
    model: str
        This is typically the path to the model backbone and decoder.
    parameters: ModelParameters
        These are the model parameters set from the command line.
    timer: TimerContext
        A timer object for handling validation timings for the model.

    Raises
    ------
    ImportError
        Raised if the deepview.vaal library is not found.
    EnvironmentError
        Raised if VAAL Context is not found.
    FileNotFoundError
        Raised if the path to the model does not exist.
    NotImplementedError
        Some methods have not been implemented yet.
    """

    def __init__(
        self,
        model: str,
        parameters: ModelParameters,
        timer: TimerContext
    ):
        super(DeepViewRTRunner, self).__init__(model, parameters, timer=timer)

        try:
            import deepview.vaal as vaal  # type: ignore
        except ImportError as e:
            raise ImportError(
                "VAAL library is needed to run DeepViewRT models.") from e

        try:
            self.ctx = vaal.Context(self.parameters.engine)
        except AttributeError as e:
            raise EnvironmentError(
                'Did not find Vaal Context. Try setting the environment \
                    variable VAAL_LIBRARY to the VAAL library.') from e

        # Change because VAAL automatically uses CPU if NPU is unavailable.
        self.parameters.engine = self.ctx.device

        if self.parameters.max_detections is not None:
            self.ctx['max_detection'] = self.parameters.max_detections
        self.ctx['score_threshold'] = self.parameters.score_threshold
        self.ctx['iou_threshold'] = self.parameters.iou_threshold

        if (self.parameters.nms in ['standard', 'fast', 'matrix']):
            self.ctx['nms_type'] = self.parameters.nms

        if self.parameters.common.norm == 'raw':
            self.ctx['proc'] = vaal.ImageProc.RAW
        elif self.parameters.common.norm == 'signed':
            self.ctx['proc'] = vaal.ImageProc.SIGNED_NORM
        elif self.parameters.common.norm == 'unsigned':
            self.ctx['proc'] = vaal.ImageProc.UNSIGNED_NORM
        elif self.parameters.common.norm == 'whitening':
            self.ctx['proc'] = vaal.ImageProc.WHITENING
        elif self.parameters.common.norm == 'imagenet':
            self.ctx['proc'] = vaal.ImageProc.IMAGENET
        else:
            logger(f"Unsupported normalization method: {self.parameters.common.norm}",
                   code="ERROR")

        if not os.path.exists(model):
            raise FileNotFoundError(
                "The model '{}' does not exist.".format(model))

        self.ctx.load_model(model)

        if len(self.ctx.labels) > 0:
            self.parameters.labels = self.ctx.labels

        outputs = [{"quantization": [out.scales, out.zeros],
                    "shape": out.shape} for out in self.ctx.outputs]
        metadata = self.load_model_metadata()
        # Parse the model output details in the metadata.
        self.outputs = Outputs(
            metadata=metadata,
            parameters=parameters,
            outputs=outputs
        )

        if self.parameters.warmup > 0:
            self.warmup()

    def warmup(self):
        """
        Run model warmup.
        """
        logger("Running model warmup...", code="INFO")

        times = []
        for _ in range(self.parameters.warmup):
            start = clock_now()
            self.ctx.run_model()
            stop = clock_now() - start
            times.append(stop * 1e-6)

        outputs = []
        for x in self.ctx.outputs:
            outputs.append(x.array())

        # Warmup output postprocessing.
        if len(outputs) > 0:
            self.postprocessing(outputs)

        message = "model warmup took %f ms (%f ms avg)" % (np.sum(times),
                                                           np.average(times))
        logger(message, code="INFO")
        self.timer.reset()

    def run_single_instance(self, image: str) -> Any:
        """
        Run two stage DeepViewRT inference
        on a single image and record the timings.

        Parameters
        ----------
        image: str
            The path to the image. This is used to match the
            annotation to be read.

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
        # Preprocessing
        with self.timer.time("input"):
            self.ctx.load_image(image)

        # Inference
        with self.timer.time("inference"):
            self.ctx.run_model()

        outputs = []
        for x in self.ctx.outputs:
            outputs.append(x.array())

        # Postprocessing
        return self.postprocessing(outputs)
