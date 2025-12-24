"""
This implementation is currently deprecated!
"""

from __future__ import annotations

from timeit import timeit
from time import monotonic_ns as clock_now
from typing import TYPE_CHECKING, Optional, Tuple, Union

import numpy as np

from edgefirst.validator.runners.core import Runner
from edgefirst.validator.publishers.utils.logger import logger

if TYPE_CHECKING:
    from edgefirst.validator.evaluators import Parameters


class HailoRunner(Runner):
    """
    Runs Hailo models.

    Parameters
    ----------
        model: str
            The path to the model or the loaded Hailo model.

        parameters: Parameters
            These are the model parameters set from the command line.

        labels: list
            Unique string labels.

    Raises
    ------
    ImportError
        Raised if hailo_platform library is not intalled.
    """

    def __init__(
        self,
        model,
        parameters: Parameters,
        labels: Optional[list] = None
    ):
        super(HailoRunner, self).__init__(model, parameters, labels)

        try:
            from hailo_platform import (  # type: ignore
                HEF, Device, VDevice, HailoStreamInterface, ConfigureParams,
                InputVStreamParams, OutputVStreamParams, FormatType,
                InferVStreams)
        except ImportError as e:
            raise ImportError(
                "hailo_platform library is needed to run Hailo models.") from e

        if isinstance(model, str):
            model = self.validate_model_path(model)
            devices = Device.scan()
            self.hef = HEF(model)
            self.target = VDevice(device_ids=devices)
            configure_params = ConfigureParams.create_from_hef(
                self.hef, interface=HailoStreamInterface.PCIe)
            self.network_group = self.target.configure(
                self.hef, configure_params)[0]
            self.network_group_params = self.network_group.create_params()

            self.input_vstreams_params = InputVStreamParams.make_from_network_group(
                self.network_group, quantized=False, format_type=FormatType.FLOAT32)
            self.output_vstreams_params = OutputVStreamParams.make_from_network_group(
                self.network_group, quantized=False, format_type=FormatType.FLOAT32)
        else:
            raise ValueError("Only string filepaths are supported")

        self.parameters.engine = "hailo"

        if self.parameters.warmup > 0:
            input_vstream_info = self.hef.get_input_vstream_infos()[0]
            with InferVStreams(self.network_group, self.input_vstreams_params, self.output_vstreams_params) as infer_pipeline:
                # Produce a sample image of zeros.
                input_type = "float32" if "float" in self.get_input_type() else "uint32"
                height, width = self.get_input_shape()[1:3]
                image = np.expand_dims(np.zeros((height, width, 3)), 0).astype(
                    np.dtype(input_type))
                input_data = {input_vstream_info.name: np.expand_dims(
                    image, axis=0).astype(np.float32)}

                with self.network_group.activate(self.network_group_params):
                    logger("Loading model and warmup...", code="INFO")
                    t = timeit(lambda: infer_pipeline.infer(input_data),
                               number=self.parameters.warmup)
                    logger("model warmup took %f seconds (%f ms avg)" %
                           (t, t * 1000 / self.parameters.warmup), code="INFO")

    def run_single_instance(
        self,
        image: Union[str, np.ndarray]
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Produce Hailo inference on one image and records the timings.

        Parameters
        ----------
            image: str or np.ndarray
                The path to the image or NumPy array image.

        Returns
        -------
            nmsed_boxes: np.ndarray
                The prediction bounding boxes.. [[box1], [box2], ...].

            nmsed_classes: np.ndarray
                The prediction labels.. [cl1, cl2, ...].

            nmsed_scores: np.ndarray
                The prediction confidence scores.. [score, score, ...]
                normalized between 0 and 1.
        """
        try:
            from hailo_platform import InferVStreams  # type: ignore
        except ImportError as e:
            raise ImportError(
                "hailo_platform library is needed to run Hailo models.") from e
        input_vstream_info = self.hef.get_input_vstream_infos()[0]
        output_name = self.hef.get_output_vstream_infos()[0].name

        with InferVStreams(
            self.network_group,
            self.input_vstreams_params,
            self.output_vstreams_params
        ) as infer_pipeline:
            infer_pipeline.set_nms_iou_threshold(self.parameters.iou_threshold)
            infer_pipeline.set_nms_score_threshold(
                self.parameters.score_threshold)

            start = clock_now()
            input_data = {
                input_vstream_info.name: image
            }
            with self.network_group.activate(self.network_group_params):
                raw_detections = infer_pipeline.infer(input_data)
            infer_ns = clock_now() - start
            self.backbone_timings.append(infer_ns * 1e-6)

            # An output with 7 columns refers to batch_id, xmin, ymin, xmax, ymax, cls, score.
            # Otherwise it is batch_size, number of boxes, number of classes
            # which needs external NMS.
            # Decoder and box timings are measured in this function.
            nmsed_boxes, nmsed_classes, nmsed_scores = self.postprocessing(
                raw_detections[output_name][0])

        return nmsed_boxes, nmsed_classes, nmsed_scores

    def postprocessing(
            self, output: list) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Retrieves the boxes, scores and labels.

        Parameters
        ----------
            outputs:
                This contains bounding boxes, scores, labels in the format.
                [[xmin, ymin, xmax, ymax, confidence, label], [...], ...].

        Returns
        -------
            nmsed_boxes: np.ndarray
                The prediction bounding boxes.. [[box1], [box2], ...].

            nmsed_classes: np.ndarray
                The prediction labels.. [cl1, cl2, ...].

            nmsed_scores: np.ndarray
                The prediction confidence scores.. [score, score, ...]
                normalized between 0 and 1.
        """
        boxes, classes, scores = list(), list(), list()
        num_detections = 0

        for i, detection in enumerate(output):
            if len(detection) == 0:
                continue
            for j in range(len(detection)):
                bbox = np.array(detection)[j][:4]
                score = np.array(detection)[j][4]
                xyxy_bbox = np.asarray([bbox[1], bbox[0], bbox[3], bbox[2]])
                boxes.append(xyxy_bbox)
                scores.append(score)
                classes.append(i)
                num_detections = num_detections + 1

        nmsed_classes = np.asarray(classes)
        if self.parameters.label_offset != 0:
            nmsed_classes += self.parameters.label_offset
        return np.asarray(boxes), nmsed_classes, np.asarray(scores)

    def get_input_type(self) -> str:
        """
        This returns the input type of the model.

        Returns
        -------
            type: str
                The input type of the model.
        """
        inputs = self.hef.get_input_vstream_infos()
        base_format = str(inputs[0].format.type)
        return base_format[base_format.find('.') + 1:].lower()

    def get_input_shape(self) -> np.ndarray:
        """
        Grabs the model input shape.

        Returns
        -------
            shape: np.ndarray
                The model input shape.
                (batch size, channels, height, width).
        """
        inputs = self.hef.get_input_vstream_infos()
        return tuple([1] + list(inputs[0].shape))

    def get_output_type(self) -> str:
        """
        This returns the output type of the model.

        Returns
        -------
            type: str
                The output type of the model.
        """
        outputs = self.hef.get_output_vstream_infos()
        base_format = str(outputs[0].format.type)
        return base_format[base_format.find('.') + 1:].lower()

    def get_output_shape(self) -> np.ndarray:
        """
        Grabs the model output shape.

        Returns
        --------
            shape: np.ndarray
                The model output shape.
                (batch size, boxes, classes).
        """
        outputs = self.hef.get_output_vstream_infos()
        return outputs[0].shape

    def get_image_shape(self) -> tuple:
        """
        Returns the input image shape passed to the model.

        Returns
        -------
            shape: tuple
                The shape as (height, width).
        """
        _, _, height, width = self.get_input_shape()
        return (height, width)
