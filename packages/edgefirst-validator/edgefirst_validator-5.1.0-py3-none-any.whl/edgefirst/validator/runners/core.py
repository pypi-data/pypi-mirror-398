"""
Implementation of the base Runner class for model execution and postprocessing.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional, Union, Tuple, List
import time
import os

import yaml
import numpy as np
import numpy.typing as npt

from edgefirst.validator.runners.processing.outputs import Outputs
from edgefirst.validator.datasets.utils.annotation_transforms import (check_normalized_boxes,
                                                                      xyxy2xcycwh,
                                                                      xcycwh2xyxy,
                                                                      xyxy2xywh)
from edgefirst.validator.datasets.utils.image_transforms import (preprocess_native,
                                                                 preprocess_hal,
                                                                 resize)
from edgefirst.validator.runners.processing.decode import (decode_mpk_boxes,
                                                           decode_mpk_masks,
                                                           decode_yolo_boxes,
                                                           decode_yolo_masks,
                                                           decode_yolox_boxes,
                                                           crop_masks,
                                                           dequantize)
from edgefirst.validator.publishers.utils.logger import logger
from edgefirst.validator.runners.processing.nms import nms, multiclass_nms
from edgefirst.validator.datasets.utils.fetch import get_shape

if TYPE_CHECKING:
    from edgefirst.validator.evaluators import ModelParameters, TimerContext

DetOutput = Tuple[npt.NDArray[np.float32],
                  npt.NDArray[np.uintp], npt.NDArray[np.float32]]
SegDetOutput = Tuple[npt.NDArray[np.float32],
                     npt.NDArray[np.uintp],
                     npt.NDArray[np.float32],
                     Union[None, npt.NDArray[np.uint8],
                           List[npt.NDArray[np.uint8]]]]


class Runner:
    """
    Abstract class that provides a template for the other runner classes.

    Parameters
    ----------
    model: Any
        This is typically the path to the model file or a loaded model.
    parameters: Parameters
        These are the model parameters set from the command line.
    timer: TimerContext
        A timer object for handling validation timings for the model.

    Raises
    ------
    FileNotFoundError
        Raised if the path to the model does not exist.
    """

    def __init__(self, model: Any, parameters: ModelParameters,
                 timer: TimerContext):
        self.model = model
        self.parameters = parameters
        self.timer = timer

        self.num_boxes = 0  # The number of boxes in the model output shape.
        self.graph_name = "main_graph"
        self.outputs = None
        self.decoder = None
        self.shape = None
        self.type = None
        self.height, self.width = 0, 0

    def init_decoder(
            self, metadata: dict, outputs: Union[List[dict], List[np.ndarray]]):
        """
        Parse the model metadata and initialize the HAL decoder.

        Parameters
        ----------
        metadata: dict
            The contents of the model metadata for decoding the outputs.
        outputs: Union[List[dict], List[np.ndarray]]
            This is either a List[dict] from a TFLite output details
            or a List[np.ndarray] containing the shapes from the model outputs.
        """
        self.type = self.get_input_type()
        shape = self.get_input_shape()
        # Avoid shape [None, height, width, 3]
        self.shape = np.array([d if d is not None else 1 for d in shape])
        self.height, self.width = get_shape(self.shape)

        # Transpose the image to meet requirements of the channel order.
        if shape[-1] in [2, 3, 4]:
            height, width = shape[1:3]
            channels = shape[-1]
        else:
            height, width = shape[2:4]
            channels = shape[1]
            self.parameters.common.transpose = True

        self.parameters.common.dtype = self.type
        self.parameters.common.shape = self.shape

        # Parse the model output details in the metadata.
        self.outputs = Outputs(
            metadata=metadata,
            parameters=self.parameters,
            outputs=outputs
        )

        if self.parameters.nms == "hal":
            try:
                import edgefirst_hal  # type: ignore
                self.decoder = edgefirst_hal.Decoder(
                    self.outputs.metadata,
                    score_threshold=self.parameters.score_threshold,
                    iou_threshold=self.parameters.iou_threshold
                )
            except ImportError as e:
                raise ImportError(
                    "EdgeFirst HAL is needed to perform decoding using hal."
                ) from e

        if self.parameters.common.backend == "hal":
            # This buffer input_dst conforms with the input requirements
            # of the model.
            try:
                import edgefirst_hal  # type: ignore
                if self.parameters.common.transpose:
                    if channels == 2:
                        fourcc = edgefirst_hal.FourCC.NV16
                    elif channels == 4:
                        fourcc = edgefirst_hal.FourCC.PLANAR_RGBA
                    else:
                        fourcc = edgefirst_hal.FourCC.PLANAR_RGB
                else:
                    if channels == 2:
                        fourcc = edgefirst_hal.FourCC.YUYV
                    elif channels == 4:
                        fourcc = edgefirst_hal.FourCC.RGBA
                    else:
                        fourcc = edgefirst_hal.FourCC.RGB
                self.parameters.common.input_dst = edgefirst_hal.TensorImage(
                    width, height, fourcc
                )
            except ImportError as e:
                raise ImportError(
                    "EdgeFirst HAL is needed to perform preprocessing using hal."
                ) from e

    def load_model_metadata(self) -> Union[dict, None]:
        """
        Returns the model metadata for decoding the outputs.

        Parameters
        ----------
        model_path: str
            The path to the model.
        """
        logger(
            "Reading the metadata for this model is not yet fully implemented.",
            code="WARNING")

        if self.parameters.config_path is not None:
            if os.path.exists(self.parameters.config_path):
                with open(self.parameters.config_path, encoding="utf-8") as file:
                    metadata = yaml.safe_load(file)
            else:
                logger(
                    f"The model metadata path '{self.parameters.config_path}' does not exist.",
                    code="WARNING")

        if self.parameters.labels_path is not None:
            if os.path.exists(self.parameters.labels_path):
                with open(self.parameters.labels_path, 'r', encoding="utf-8") as f:
                    self.parameters.labels = [
                        line.rstrip()
                        for line in f.readlines()
                        if line not in ["\n", "", "\t"]
                    ]
            else:
                logger(
                    f"The labels file path '{self.parameters.labels_path}' does not exist.",
                    code="WARNING")

        self.set_metadata_parameters(metadata)
        return metadata

    def set_metadata_parameters(self, metadata: Union[dict, None]):
        """
        Sets the parameters specified in the model metadata.
        Validate with the model metadata parameters.
        By default in the command line override is set to False to use
        the command line parameters. Otherwise it will use
        model meta parameters.

        Parameters
        ----------
        metadata: Union[dict, None]
            The contents of the model metadata for decoding the outputs.
        """

        if self.parameters.override and metadata is not None:
            self.parameters.score_threshold = metadata\
                .get("validation", {}).get("score",
                                           self.parameters.score_threshold)
            self.parameters.iou_threshold = metadata\
                .get("validation", {}).get("iou",
                                           self.parameters.iou_threshold)
            self.parameters.common.norm = metadata\
                .get("validation", {}).get("normalization",
                                           self.parameters.common.norm)
            self.parameters.common.preprocessing = metadata\
                .get("validation", {}).get("preprocessing",
                                           self.parameters.common.preprocessing)

    def warmup(self):
        """
        Run model warmup.
        """

        logger("Running model warmup...", code="INFO")

        times = []

        for _ in range(self.parameters.warmup):
            start = time.perf_counter()
            # Warmup input preprocessing.
            if self.parameters.common.backend == "hal":
                import edgefirst_hal  # type: ignore
                image, _, _, _ = preprocess_hal(
                    image=edgefirst_hal.TensorImage(self.width, self.height),
                    shape=self.shape,
                    input_type=self.type,
                    input_buffer=self.parameters.common.input_dst,
                    input_tensor=self.parameters.common.input_tensor,
                    transpose=self.parameters.common.transpose,
                    preprocessing=self.parameters.common.preprocessing,
                    normalization=self.parameters.common.norm,
                    quantization=self.parameters.common.input_quantization,
                )
            else:
                image, _, _, _ = preprocess_native(
                    image=np.zeros(
                        (self.height, self.width, 3), dtype=np.uint8),
                    shape=self.shape,
                    input_type=self.type,
                    input_tensor=self.parameters.common.input_tensor,
                    transpose=self.parameters.common.transpose,
                    preprocessing=self.parameters.common.preprocessing,
                    normalization=self.parameters.common.norm,
                    quantization=self.parameters.common.input_quantization,
                    backend=self.parameters.common.backend,
                )
            self.run_single_instance(image)

            elapsed = time.perf_counter() - start
            times.append(elapsed * 1e3)  # Convert to ms

        message = "model warmup took %f ms (%f ms avg)" % (np.sum(times),
                                                           np.average(times))
        logger(message, code="INFO")
        self.timer.reset()

    def run_single_instance(self, image: Union[str, np.ndarray]) -> Any:
        """Abstract Method"""

    def postprocessing(self, outputs: Union[list, np.ndarray]) -> Any:
        """
        Postprocess outputs into boxes, scores, labels or masks.
        This method will perform NMS operations where the outputs
        will be transformed into the following format.

        Models trained using ModelPack separates the outputs and
        directly return the NMS bounding boxes, scores, and
        labels as described below.

        Models converted in YOLOv5 will be a list of length 1 which
        has a shape of (1, number of boxes, 6) and formatted as
        [[[xmin, ymin, xmax, ymax, confidence, label], [...], ...]].

        Models converted in YOLOv7 will directly extract the
        bounding boxes, scores, and labels from the outputs.

        Parameters
        ----------
        outputs: Union[list, np.ndarray]
            ModelPack outputs will be a list with varying lengths
            which could either contain bounding boxes, labels, scores,
            or masks (encoded and decoded).

            Models converted in YOLOv5 has the following shape
            (batch size, number of boxes, number of classes).

            Models converted in YOLOv7 will already have NMS embedded. The
            output has a shape of (number of boxes, 7) and formatted as
            [[batch_id, xmin, ymin, xmax, ymax, cls, score], ...].

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

        masks = None
        # MobileNet SSD
        if self.outputs.classes["index"] is not None:
            with self.timer.time("output"):
                outputs = outputs[0] if len(outputs) == 1 else outputs
                outputs = outputs.numpy() if not isinstance(
                    outputs, (np.ndarray, list)) else outputs

                masks = None
                boxes, classes, scores, _ = outputs
                boxes = np.squeeze(boxes)
                classes = np.squeeze(classes).astype(np.uintp)
                scores = np.squeeze(scores)
        # ModelPack or Kinara
        elif len(self.outputs.mpk_types) > 0 or (None not in
                                                 [self.outputs.boxes["index"],
                                                  self.outputs.scores["index"]]):
            with self.timer.time("output"):
                # Kinara
                if self.outputs.boxes["decoder"] == "yolov8":
                    if self.parameters.nms == "hal":
                        boxes, scores, classes, masks = self.decoder.decode(
                            outputs)
                        # Normalize bounding boxes if not already.
                        boxes = check_normalized_boxes(boxes,
                                                       width=self.width,
                                                       height=self.height)
                    else:
                        outputs = np.concatenate(outputs, axis=1)
                        # Process YOLOv8 detection with shape [1, 84, 8400].
                        boxes, classes, scores, masks = self.process_yolo(
                            [outputs])

                # ModelPack
                else:
                    if self.parameters.nms == "hal":
                        boxes, classes, scores, masks = self.process_mpk_hal(
                            outputs)
                    else:
                        boxes, classes, scores, masks = self.process_mpk(
                            outputs)
        else:
            # YOLOx
            if (self.graph_name not in ["main_graph", "torch_jit", "tf2onnx"]
                    and outputs[0].shape[-1] == 85):

                # HAL decoder/NMS is not yet supported and fallback to NumPy.
                if self.parameters.nms == "hal":
                    self.parameters.nms = "numpy"

                with self.timer.time("output"):
                    boxes, classes, scores = self.process_yolox(
                        outputs=outputs)
                    masks = None

            # YOLOv5, YOLOv8, YOLOv11 models.
            else:
                with self.timer.time("output"):
                    # Decoded outputs.
                    if len(outputs) == 1 and outputs[0].shape == (1, 300, 6):
                        outputs = outputs[0].squeeze()
                        scores = outputs[:, 4]
                        classes = outputs[:, 5]
                        boxes = outputs[:, 0:4]

                        # Filter out all zero rows.
                        filt = ~np.all(boxes[:, 0:4] == 0, axis=1)
                        boxes = boxes[filt]
                        scores = scores[filt]
                        classes = classes[filt]
                        # Normalize bounding boxes if not already.
                        boxes = check_normalized_boxes(
                            boxes, width=self.width, height=self.height)
                        # No masks from this output shape.
                        masks = None
                    elif self.parameters.nms == "hal":
                        boxes, classes, scores, masks = self.process_yolo_hal(
                            outputs)
                    else:
                        boxes, classes, scores, masks = self.process_yolo(
                            outputs)

        if self.parameters.common.with_boxes:
            if self.parameters.box_format == "xcycwh":
                boxes = xyxy2xcycwh(boxes)
            elif self.parameters.box_format == "xywh":
                boxes = xyxy2xywh(boxes)

            if self.parameters.label_offset != 0:
                classes += self.parameters.label_offset

            if self.parameters.common.with_masks:
                return boxes, classes, scores, masks
            else:
                return boxes, classes, scores
        else:
            return masks

    def process_mpk_hal(self, outputs: List[np.ndarray]):
        """
        ModelPack output decoding and postprocessing using the HAL decoder.

        Parameters
        ----------
        outputs: List[np.ndarray]
            ModelPack outputs will be a list with varying lengths
            which could either contain bounding boxes, labels, scores,
            or masks (encoded and decoded).

        Returns
        -------
        boxes : np.ndarray
            This contains decoded and valid bounding boxes post NMS.
        classes : np.ndarray
            This contains decoded and valid classes post NMS.
        scores : np.ndarray
            This contains decoded and valid scores post NMS.
        masks: np.ndarray
            This is the semantic segmentation mask output from
            ModelPack. If the model is not a segmentation model,
            None is returned.
        """

        # The decode function in HAL returns a 3D array for the masks.
        # Needs an argmax to convert to semantic segmentation.
        boxes, scores, classes, masks = self.decoder.decode(
            outputs, max_boxes=self.parameters.max_detections)

        # Decoded masks.
        if self.outputs.masks["index"] is not None:
            masks = np.squeeze(
                outputs[self.outputs.masks["index"]]).astype(np.uint8)
            # Resize the mask to the model input shape.
            masks = resize(masks, size=(self.width, self.height))
        # Deploy argmax to the mask and convert to semantic segmentation.
        elif len(masks):
            masks = self.decoder.segmentation_to_mask(masks[0])
            # Resize the mask to the model input shape.
            masks = resize(masks, size=(self.width, self.height))

        return boxes, classes, scores, masks

    def process_mpk(self, outputs: List[np.ndarray]) -> SegDetOutput:
        """
        ModelPack output decoding and postprocessing.

        Parameters
        ----------
        outputs: List[np.ndarray]
            ModelPack outputs will be a list with varying lengths
            which could either contain bounding boxes, labels, scores,
            or masks (encoded and decoded).

        Returns
        -------
        boxes : np.ndarray
            This contains decoded and valid bounding boxes post NMS.
        classes : np.ndarray
            This contains decoded and valid classes post NMS.
        scores : np.ndarray
            This contains decoded and valid scores post NMS.
        masks: np.ndarray
            This is the semantic segmentation mask output from
            ModelPack. If the model is not a segmentation model,
            None is returned.
        """

        outputs = outputs[0] if len(outputs) == 1 else outputs
        outputs = outputs.numpy() if not isinstance(
            outputs, (np.ndarray, list)) else outputs

        boxes, scores = [], []
        classes, masks = None, None

        # Masks Already Decoded
        if self.outputs.masks["index"] is not None:
            masks = np.squeeze(
                outputs[self.outputs.masks["index"]]).astype(np.uint8)
            masks = resize(masks, size=(self.width, self.height),
                           backend=self.parameters.common.backend)

        # Outputs Already Decoded
        if None not in [self.outputs.boxes["index"],
                        self.outputs.scores["index"]]:

            # Dequantize Outputs
            boxes = outputs[self.outputs.boxes["index"]]
            if (self.outputs.boxes["quantization"] is not None and
                    boxes.dtype != np.float32):
                boxes = dequantize(boxes, *self.outputs.boxes["quantization"])

            scores = outputs[self.outputs.scores["index"]]
            if (self.outputs.scores["quantization"] is not None and
                    scores.dtype != np.float32):
                scores = dequantize(
                    scores, *self.outputs.scores["quantization"])

        # Decode and Dequantize Outputs
        elif len(self.outputs.mpk_types) > 0:
            for context in self.outputs.mpk_types:
                x = outputs[context["index"]]
                if context["quantization"] is not None and x.dtype != np.float32:
                    x = dequantize(x, *context["quantization"])

                if context["type"] == "detection":
                    box, score = decode_mpk_boxes(
                        p=x, anchors=context["anchors"])
                    boxes.append(box)
                    scores.append(score)

                elif context["type"] == "segmentation" and masks is None:
                    masks = np.squeeze(decode_mpk_masks(masks=x))
                    masks = resize(masks, size=(self.width, self.height),
                                   backend=self.parameters.common.backend)

            if 0 not in [len(boxes), len(scores)]:
                scores = np.concatenate(scores, axis=1).astype(np.float32)
                boxes = np.concatenate(boxes, axis=1).astype(np.float32)

        # Postprocess Outputs
        if 0 not in [len(boxes), len(scores)]:
            boxes = np.squeeze(boxes, axis=0)
            scores = np.squeeze(scores, axis=0)

            boxes, classes, scores, _ = nms(
                boxes=boxes,
                scores=scores,
                iou_threshold=self.parameters.iou_threshold,
                score_threshold=self.parameters.score_threshold,
                max_detections=self.parameters.max_detections,
                class_agnostic=self.parameters.agnostic_nms,
                nms_type=self.parameters.nms
            )
            # Normalize bounding boxes if not already.
            boxes = check_normalized_boxes(
                boxes, width=self.width, height=self.height)
        return boxes, classes, scores, masks

    def process_yolo_hal(self, outputs: List[np.ndarray]) -> SegDetOutput:
        """
        Utralytics YOLO output decoding and postprocessing using the
        HAL decoder.

        Parameters
        ----------
        outputs: List[np.ndarray]
            Models converted in YOLOv5 has the following shape
            (batch size, number of boxes, number of classes) for detection.

            Models converted in YOLOv7 will already have NMS embedded. The
            output has a shape of (number of boxes, 7) and formatted as
            [[batch_id, xmin, ymin, xmax, ymax, cls, score], ...].

            For segmentation models, this will contain two arrays containing
            the detection and segmentation outputs.

        Returns
        -------
        boxes : np.ndarray
            This contains decoded and valid bounding boxes post NMS.
        classes : np.ndarray
            This contains decoded and valid classes post NMS.
        scores : np.ndarray
            This contains decoded and valid scores post NMS.
        masks: np.ndarray
            This is the instance segmentation mask outputs from
            Ultralytics. If the model is not a segmentation model,
            None is returned.
        """

        x = outputs[self.outputs.scores["index"]]
        # NOTE: HAL Decoder requires normalized bounding boxes.
        if x.dtype in [np.float32, np.float16]:
            x[:, :4, :] = check_normalized_boxes(
                x[:, :4, :], width=self.width, height=self.height)
            outputs[self.outputs.scores["index"]] = x

        # Decode Outputs
        boxes, scores, classes, masks = self.decoder.decode(
            outputs, max_boxes=self.parameters.max_detections
        )

        # Filter invalid 0-dimension boxes.
        valid = np.where((boxes[..., 0] < boxes[..., 2]) &
                         (boxes[..., 1] < boxes[..., 3]))[0]
        boxes = boxes[valid]
        scores = scores[valid]
        classes = classes[valid]
        if len(masks) > 0:
            masks = [masks[i] for i in valid]

        # Paint masks onto a fixed shape NumPy array canvas.
        full_masks = []
        for b, m in zip(boxes, masks):
            # Resize the mask into the input shape of the model.
            mask_width = round((b[2] - b[0]) * self.width)
            mask_height = round((b[3] - b[1]) * self.height)
            m = resize(m, size=(mask_width, mask_height))
            mask = np.zeros((self.width, self.height, 1), dtype=np.uint8)
            left = round(b[0] * self.width)
            top = round(b[1] * self.height)
            mask[top:(top + mask_height), left:(left + mask_width), 0] = m

            # Run Argmax on the masks.
            mask = self.decoder.segmentation_to_mask(mask)
            full_masks.append(mask)

        if len(full_masks) > 0:
            masks = np.stack(full_masks, axis=0)
        return boxes, classes, scores, masks

    def process_yolo(self, outputs: List[np.ndarray]) -> SegDetOutput:
        """
        Utralytics YOLO output decoding and postprocessing.

        Parameters
        ----------
        outputs: List[np.ndarray]
            Models converted in YOLOv5 has the following shape
            (batch size, number of boxes, number of classes) for detection.

            Models converted in YOLOv7 will already have NMS embedded. The
            output has a shape of (number of boxes, 7) and formatted as
            [[batch_id, xmin, ymin, xmax, ymax, cls, score], ...].

            For segmentation models, this will contain two arrays containing
            the detection and segmentation outputs.

        Returns
        -------
        boxes : np.ndarray
            This contains decoded and valid bounding boxes post NMS.
        classes : np.ndarray
            This contains decoded and valid classes post NMS.
        scores : np.ndarray
            This contains decoded and valid scores post NMS.
        masks: np.ndarray
            This is the instance segmentation mask outputs from
            Ultralytics. If the model is not a segmentation model,
            None is returned.
        """
        outputs = outputs[0] if len(outputs) == 1 else outputs
        outputs = outputs.numpy() if not isinstance(
            outputs, (np.ndarray, list)) else outputs

        # Dequantize Outputs
        x = outputs[self.outputs.scores["index"]]
        x = x.astype(np.float32) if x.dtype == np.float16 else x
        if (self.outputs.scores["quantization"] is not None and
                x.dtype != np.float32):
            x = dequantize(x, *self.outputs.scores["quantization"])

        # Decode Outputs
        boxes, scores, masks = decode_yolo_boxes(
            p=x,
            with_masks=self.parameters.common.with_masks,
            nc=(len(self.parameters.labels)
                if self.parameters.labels is not None else 0)
        )

        # Run NMS
        boxes, classes, scores, masks = nms(
            boxes=boxes,
            scores=scores,
            masks=masks,
            iou_threshold=self.parameters.iou_threshold,
            score_threshold=self.parameters.score_threshold,
            max_detections=self.parameters.max_detections,
            class_agnostic=self.parameters.agnostic_nms,
            nms_type=self.parameters.nms
        )

        # Normalize bounding boxes if not already.
        boxes = check_normalized_boxes(
            boxes, width=self.width, height=self.height)

        # Decode Masks.
        if masks is not None:
            protos = outputs[self.outputs.masks["index"]]
            protos = protos.astype(
                np.float32) if protos.dtype == np.float16 else protos

            if (self.outputs.masks["quantization"] is not None and
                    protos.dtype != np.float32):
                protos = dequantize(
                    protos, *self.outputs.masks["quantization"])
            masks = decode_yolo_masks(masks, protos=protos)

            # Mask postprocessing: resize + crop.
            if masks.shape[0] > 0:
                masks = (masks > 0).astype(np.uint8)
                masks = [resize(mask, size=(self.width, self.height),
                                backend=self.parameters.common.backend)
                         for mask in masks]
                masks = np.stack(masks, axis=0)
                masks = crop_masks(masks, boxes,
                                   backend=self.parameters.common.backend)

        return boxes, classes, scores, masks

    def process_yolox(self, outputs: List[np.ndarray]) -> DetOutput:
        """
        YOLOx output decoding and postprocessing.

        Parameters
        ----------
        outputs: List[np.ndarray]
            YOLOx raw output to postprocess into
            bounding boxes, classes, scores after NMS. This
            typically has the shape (1, 8400, 85).

        Returns
        -------
        Tuple[np.ndarray, np.ndarray, np.ndarray]
            np.ndarray
                The prediction bounding boxes.. [[box1], [box2], ...].
            np.ndarray
                The prediction labels.. [cl1, cl2, ...].
            np.ndarray
                The prediction confidence scores.. [score, score, ...]
                normalized between 0 and 1.
        """

        outputs = outputs[0] if len(outputs) == 1 else outputs
        outputs = outputs.numpy() if not isinstance(
            outputs, (np.ndarray, list)) else outputs

        if (self.outputs.scores["quantization"] is not None and
                outputs.dtype != np.float32):
            outputs = dequantize(outputs, *self.outputs.scores["quantization"])

        boxes, scores = decode_yolox_boxes(
            p=outputs,
            shape=(self.height, self.width)
        )
        boxes = xcycwh2xyxy(boxes=boxes)

        # Typical: nms_thr=0.45, score_thr=0.1
        dets = multiclass_nms(
            boxes=boxes,
            scores=scores,
            iou_threshold=self.parameters.iou_threshold,
            score_threshold=self.parameters.score_threshold,
            max_detections=self.parameters.max_detections,
            class_agnostic=self.parameters.agnostic_nms,
            nms_type=self.parameters.nms
        )
        if dets is None:
            return np.array([]), np.array([]), np.array([])

        boxes = dets[:, :4]
        scores = dets[:, 4]
        classes = dets[:, 5]

        # Normalize the bounding boxes.
        boxes = check_normalized_boxes(
            boxes, width=self.width, height=self.height)
        return boxes, classes, scores

    def get_input_type(self) -> np.dtype:
        """Abstract Method"""
        return np.float32

    def get_input_shape(self) -> np.ndarray:
        """Abstract Method"""
        return np.array([1, 640, 640, 3])
