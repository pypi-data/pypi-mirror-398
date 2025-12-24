"""
Implementation for the Offline model runner.
"""

from __future__ import annotations

import os
import json
import warnings
from typing import TYPE_CHECKING, Any

import numpy as np

from edgefirst.validator.runners.core import Runner
from edgefirst.validator.datasets.utils.annotation_transforms import (xcycwh2xyxy,
                                                                      xywh2xyxy)
from edgefirst.validator.datasets.utils.fetch import get_shape

if TYPE_CHECKING:
    from edgefirst.validator.evaluators import ModelParameters, TimerContext


class OfflineRunner(Runner):
    """
    This class reads model detection annotations stored in text files
    that are in YOLO format. For more information on the YOLO format visit:
    https://support.deepviewml.com/hc/en-us/articles/10869801702029

    *Note: These text files should also include the model prediction scores
    which adds to the YOLO format: [cls score xc yc width height]*

    Use Case: PT models are ran using https://github.com/ultralytics/yolov5
    repository. These model predictions will be stored in TXT files that
    are in YOLO format. This class will read the text files to be validated.

    Parameters
    ----------
    annotation_source: str
        This is the path to the model prediction annotations
        stored in text files with YOLO format annotations.
        [cls score xc yc width height].
    parameters: ModelParameters
        These are the model parameters set from the command line.
    annotation_extension: str
        This represents the extension of the files that store
        the prediction annotations. Only text files is supported
        at the moment.
    timer: TimerContext
        A timer object for handling validation timings for the model.
    """

    def __init__(
        self,
        annotation_source: str,
        parameters: ModelParameters,
        timer: TimerContext,
        annotation_extension='txt'
    ):
        super(OfflineRunner, self).__init__(
            annotation_source, parameters, timer=timer)

        self.annotation_extension = annotation_extension
        if self.parameters.box_format not in ['xcycwh', 'xywh', 'xyxy']:
            raise ValueError(
                f"Unknown annotation format provided {self.parameters.box_format}.")

        self.transformer = None
        if self.parameters.box_format == 'xcycwh':
            self.transformer = xcycwh2xyxy
        elif self.parameters.box_format == 'xywh':
            self.transformer = xywh2xyxy
        else:
            self.transformer = None

        self.parameters.common.with_boxes = True
        self.parameters.common.with_masks = False

        self.__timings = {
            'min_read_time': 0,
            'max_read_time': 0,
            'min_load_time': 0,
            'max_load_time': 0,
            'min_backbone_time': 0,
            'max_backbone_time': 0,
            'min_decode_time': 0,
            'max_decode_time': 0,
            'min_box_time': 0,
            'max_box_time': 0,
            'avg_read_time': 0,
            'avg_load_time': 0,
            'avg_backbone_time': 0,
            'avg_decode_time': 0,
            'avg_box_time': 0,
        }
        timings_path = os.path.join(annotation_source, "timings.json")
        if os.path.exists(timings_path):
            timings = {}
            with open(timings_path, encoding="utf-8") as file:
                timings: dict = json.load(file)
            self.parameters.engine = timings.get("engine", "cpu")
            self.parameters.max_detections = timings.get("max_boxes", None)
            self.parameters.iou_threshold = timings.get("iou", None)
            self.parameters.score_threshold = timings.get("threshold", None)
            self.parameters.common.shape = timings.get(
                "shape", (1, 640, 640, 3))
            self.parameters.common.dtype = timings.get("dtype", "float32")
            self.parameters.warmup = None
            self.__timings = timings.get("timings", {})
        else:
            # OFfline validation is not concerned with these parameters.
            self.parameters.engine = "cpu"
            self.parameters.nms = None
            self.parameters.max_detections = None
            self.parameters.iou_threshold = None
            self.parameters.score_threshold = None
            self.parameters.warmup = None
            self.parameters.common.shape = (1, 640, 640, 3)
            self.parameters.common.dtype = "float32"
        timer.to_dict = self.get_timings

        height, width = get_shape(self.parameters.common.shape)
        try:
            import edgefirst_hal  # type: ignore
            self.parameters.common.input_dst = edgefirst_hal.TensorImage(
                width, height, edgefirst_hal.FourCC.RGBA
            )
        except ImportError as e:
            if self.parameters.common.backend == "hal":
                raise ImportError(
                    "EdgeFirst HAL is needed to create a TensorImage destination."
                ) from e

    def run_single_instance(self, image: str) -> Any:
        """
        This method reads one prediction annotation file based on the
        image name and returns the bounding boxes and labels.

        Parameters
        ----------
        image: str
            The path to the image. This is used to match the
            annotation to be read.

        Returns
        -------
        Any:
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
        annotation_path = os.path.join(self.model, "{}.{}".format(
            os.path.splitext(os.path.basename(image))[0],
            self.annotation_extension
        ))

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                annotation = np.genfromtxt(annotation_path)
        except FileNotFoundError:
            return np.array([], dtype=np.float32), \
                np.array([], dtype=np.uintp), np.array([], dtype=np.float32)

        if len(annotation):
            annotation = annotation.reshape(-1, 6)
            boxes = annotation[:, 2:6]
            boxes = self.transformer(boxes) if self.transformer else boxes
        else:
            return np.array([], dtype=np.float32), \
                np.array([], dtype=np.uintp), np.array([], dtype=np.float32)

        scores = annotation[:, 1:2].flatten().astype(np.float32)
        labels = annotation[:, 0:1].flatten().astype(
            np.uintp) + self.parameters.label_offset
        return boxes, labels, scores

    def get_timings(self) -> dict:
        """
        Returns a summary of all the timings:
        (mean, avg, max) of (load, inference, box).

        Returns
        -------
        dict
            The timings in milliseconds.

            .. code-block:: python

                {
                    'min_read_time': minimum time to read the input,
                    'max_read_time': maximum time to read the input,
                    'min_load_time': minimum time to preprocess the input,
                    'max_load_time': maximum time to preprocess the input,
                    'min_backbone_time': minimum time to run the model,
                    'max_backbone_time': maximum time to run the model,
                    'min_decode_time': minimum time to decode the outputs,
                    'max_decode_time': maximum time to decode the outputs,
                    'min_box_time': minimum time to process the outputs,
                    'max_box_time': maximum time to process the outputs,
                    'avg_read_time': average time to read the input,
                    'avg_load_time': average time to preprocess the input,
                    'avg_backbone_time': average time to run the model,
                    'avg_decode_time': average time to decode the outputs,
                    'avg_box_time': average time to process the outputs,
                }
        """
        # Convert timings to ms.
        return {
            'min_read_time': self.__timings.get("min_read_time", 0) * 1e3,
            'max_read_time': self.__timings.get("max_read_time", 0) * 1e3,
            'min_load_time': self.__timings.get("min_load_time", 0) * 1e3,
            'max_load_time': self.__timings.get("max_load_time", 0) * 1e3,
            'min_backbone_time': self.__timings.get("min_backbone_time", 0) * 1e3,
            'max_backbone_time': self.__timings.get("max_backbone_time", 0) * 1e3,
            'min_decode_time': self.__timings.get("min_decode_time", 0) * 1e3,
            'max_decode_time': self.__timings.get("max_decode_time", 0) * 1e3,
            'min_box_time': self.__timings.get("min_box_time", 0) * 1e3,
            'max_box_time': self.__timings.get("max_box_time", 0) * 1e3,
            'avg_read_time': self.__timings.get("avg_read_time", 0) * 1e3,
            'avg_load_time': self.__timings.get("avg_load_time", 0) * 1e3,
            'avg_backbone_time': self.__timings.get("avg_backbone_time", 0) * 1e3,
            'avg_decode_time': self.__timings.get("avg_decode_time", 0) * 1e3,
            'avg_box_time': self.__timings.get("avg_box_time", 0) * 1e3,
        }
