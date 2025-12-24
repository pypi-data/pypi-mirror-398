"""
Implementations for storing and parsing the model output metadata.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Union, List

import numpy as np

if TYPE_CHECKING:
    from edgefirst.validator.evaluators import ModelParameters


class Outputs:
    """
    Store the metadata output details needed for decoding the model outputs.

    If the metadata exists, then parse the metadata to store the output details.
    Otherwise, rely on a separate logic to define the output types based on shape.

    If the metadata exists, reinitialize the index based on the existing
    output tensors, as we cannot rely on the current output index stored in
    the metadata.

    Prioritize decoding the variant types such as "detection" and "segmentation".
    Otherwise, decode the known types such as "boxes", "scores", and "masks".

    Parameters
    ----------
    metadata: dict
        The contents of the model metadata for decoding the outputs.
    parameters: ModelParameters
        These are the model parameters set from the command line.
    outputs: Union[List[dict], List[np.ndarray]]
        This is either a List[dict] from a TFLite output details
        or a List[np.ndarray] containing the shapes from the model outputs.
    """

    def __init__(self,
                 metadata: dict,
                 parameters: ModelParameters,
                 outputs: Union[List[dict], List[np.ndarray]]):

        self.metadata = metadata
        self.parameters = parameters
        self.outputs = outputs

        self.boxes = {
            "anchors": None,
            "decode": False,
            "decoder": None,
            "index": None,
            "shape": None,
            "type": "boxes",
            "dtype": None,
            "quantization": None
        }

        self.scores = {
            "anchors": None,
            "decode": False,
            "decoder": None,
            "index": None,
            "shape": None,
            "type": "scores",
            "dtype": None,
            "quantization": None
        }

        self.classes = {
            "anchors": None,
            "decode": False,
            "decoder": None,
            "index": None,
            "shape": None,
            "type": "classes",
            "dtype": None,
            "quantization": None
        }

        self.masks = {
            "anchors": None,
            "decode": False,
            "decoder": None,
            "index": None,
            # Store index of raw masks used for HAL visualization.
            "raw_mask_index": None,
            "shape": None,
            "type": "masks",
            "dtype": None,
            "quantization": None
        }

        # Variant types from the metadata to decode modelpack.
        # Currently contains types such as "detection" or "segmentation"
        # which can appear common for multiple outputs.
        self.mpk_types = []
        self.num_boxes = 0  # The number of boxes in the model output shape.

        # Parse the metadata if it exists to determine the output types.
        # Otherwise check the output shapes to automatically determine the
        # types.
        if self.metadata is not None and "outputs" in self.metadata.keys():
            self.parse_metadata()
        else:
            self.create_metadata()

    def parse_metadata(self):
        """
        Parses the contents of the metadata and redefines the output
        index based on the existing output as we cannot rely on the
        output index stored in the metadata.
        """

        for output_details in self.metadata["outputs"]:
            config_shape = output_details["shape"]
            output_index = output_details["output_index"]
            decoder = output_details["decoder"]
            output_type = output_details["type"]
            dtype = output_details["dtype"]
            anchors = output_details["anchors"]
            anchors = np.array(anchors) if anchors is not None else None
            quantization = None

            # Redefine the output index based on the actual model outputs.
            for i, output in enumerate(self.outputs):
                if isinstance(output, dict):
                    shape = output["shape"].tolist()
                    quantization = output["quantization"]
                else:
                    shape = list(output.shape)

                # Pattern matching for the output shapes.
                if config_shape == shape:
                    output_index = i
                    break

            context = {
                "index": output_index,
                "decode": output_details["decode"],
                "decoder": decoder,
                "anchors": anchors,
                "shape": config_shape,
                "type": output_type,
                "dtype": dtype,
                "quantization": quantization
            }

            if output_type == "boxes":
                self.boxes = context
                self.parameters.common.with_boxes = True
            elif output_type == "scores":
                self.scores = context
                self.parameters.common.with_boxes = True
            elif output_type == "masks":
                context["raw_mask_index"] = self.masks["raw_mask_index"]
                self.masks = context
                # Segmentation models from Ultralytics are multitask.
                if decoder in ["ultralytics", "yolov8"]:
                    self.parameters.common.with_boxes = True
                    self.parameters.common.semantic = False
                self.parameters.common.with_masks = True
            else:
                if decoder in ["ultralytics", "yolov8"]:
                    self.parameters.common.with_boxes = True
                    self.parameters.common.semantic = False
                    # shape [1, 160, 160, 32] are the mask protos outputs.
                    if (len(config_shape) > 3 or output_type == "protos"):
                        self.masks = context
                        self.parameters.common.with_masks = True
                    # shape [1, 116, 8400], [1, 85, 115200] are the score
                    # and/or mask outputs.
                    else:
                        self.scores = context
                else:
                    context["type"] = output_type
                    if output_type == "detection":
                        self.parameters.common.with_boxes = True
                    elif output_type == "segmentation":
                        self.parameters.common.with_masks = True
                        self.masks["raw_mask_index"] = output_index
                    self.mpk_types.append(context)

    def create_metadata(self):
        """
        Defines the output types based on the output shape
        as either a boxes, scores, classes, or masks tensors.
        This is called when the model metadata does not exist. The model
        metadata is created here based on the logic for specifying the
        model outputs.

        This method currently only supports finding decoded output types
        for ModelPack.
        """
        # Get the model output types.
        self.boxes["index"] = self.get_boxes_index()
        self.masks["index"] = self.get_masks_index()
        self.scores["index"] = self.get_scores_index()
        self.masks["raw_mask_index"] = self.masks["index"]
        decoded_masks_index = self.get_decoded_masks_index()

        if decoded_masks_index is not None:
            self.masks["index"] = decoded_masks_index
            self.masks["decode"] = False
            self.masks["type"] = "masks"
        else:
            self.masks["decode"] = True
            self.masks["type"] = "segmentation"

        self.classes["index"] = self.get_classes_index()

        # Get the model tasks.
        if (self.boxes["index"] is not None or
            self.scores["index"] is not None or
                self.classes["index"] is not None):
            self.parameters.common.with_boxes = True
        else:
            self.parameters.common.with_boxes = False

        if self.masks["index"] is not None:
            self.parameters.common.with_masks = True
        else:
            self.parameters.common.with_masks = False

        # MobileNet SSD has embedded NMS.
        if self.classes["index"] is not None:
            self.parameters.nms = "embedded"

        # Formulate model metadata format.
        self.metadata = {"outputs": []}
        # ModelPack or Kinara
        if (None not in [self.boxes["index"], self.scores["index"]]):
            boxes = self.outputs[self.boxes["index"]]
            if isinstance(boxes, dict):
                shape = boxes["shape"].tolist()
                dtype = np.dtype(boxes["dtype"]).name
                self.boxes["quantization"] = boxes["quantization"]
            else:
                shape = list(boxes.shape)
                dtype = boxes.dtype.name if hasattr(
                    boxes, "dtype") and hasattr(
                        boxes.dtype, "name") else boxes.dtype if hasattr(
                            boxes, "dtype") else boxes.type
            self.boxes["shape"] = shape
            self.boxes["dtype"] = dtype

            scores = self.outputs[self.scores["index"]]
            if isinstance(scores, dict):
                shape = scores["shape"].tolist()
                dtype = np.dtype(scores["dtype"]).name
                self.scores["quantization"] = scores["quantization"]
            else:
                shape = list(scores.shape)
                dtype = scores.dtype.name if hasattr(
                    scores, "dtype") and hasattr(
                        scores.dtype, "name") else scores.dtype if hasattr(
                            scores, "dtype") else scores.type
            self.scores["shape"] = shape
            self.scores["dtype"] = dtype

            # Kinara YOLOv8
            if len(self.boxes["shape"]) == 3:
                self.boxes["decode"] = True
                self.scores["decode"] = True
                self.boxes["decoder"] = "ultralytics"
                self.scores["decoder"] = "ultralytics"
                self.boxes["channels_first"] = False
                self.scores["channels_first"] = False
            else:
                # Creating metadata assumes ModelPack already has decoded
                # outputs.
                self.boxes["decode"] = False
                self.scores["decode"] = False
                self.boxes["decoder"] = "modelpack"
                self.scores["decoder"] = "modelpack"

            self.metadata["outputs"].append(self.boxes)
            self.metadata["outputs"].append(self.scores)

            if self.masks["index"] is not None:
                self.masks["decoder"] = "modelpack"

                masks = self.outputs[self.masks["index"]]
                if isinstance(masks, dict):
                    shape = masks["shape"].tolist()
                    dtype = np.dtype(masks["dtype"]).name
                    self.masks["quantization"] = masks["quantization"]
                else:
                    shape = list(masks.shape)
                    dtype = masks.dtype.name if hasattr(
                        masks, "dtype") and hasattr(
                            masks.dtype, "name") else masks.dtype if hasattr(
                                masks, "dtype") else masks.type
                self.masks["shape"] = shape
                self.masks["dtype"] = dtype
                self.metadata["outputs"].append(self.masks)

        # YOLOv5, YOLOv8, YOLOv11
        elif self.scores["index"] is not None:
            self.scores["decode"] = True
            self.scores["decoder"] = "ultralytics"
            self.scores["type"] = "detection"

            scores = self.outputs[self.scores["index"]]
            if isinstance(scores, dict):
                shape = scores["shape"].tolist()
                dtype = np.dtype(scores["dtype"]).name
                self.scores["quantization"] = scores["quantization"]
            else:
                shape = list(scores.shape)
                dtype = scores.dtype.name if hasattr(
                    scores, "dtype") and hasattr(
                        scores.dtype, "name") else scores.dtype if hasattr(
                            scores, "dtype") else scores.type
            self.scores["shape"] = shape
            self.scores["dtype"] = dtype

            if self.masks["index"] is not None:
                self.parameters.common.semantic = False
                self.masks["decoder"] = "ultralytics"

                masks = self.outputs[self.masks["index"]]
                if isinstance(masks, dict):
                    shape = masks["shape"].tolist()
                    dtype = np.dtype(masks["dtype"]).name
                    self.masks["quantization"] = masks["quantization"]
                else:
                    shape = list(masks.shape)
                    dtype = masks.dtype.name if hasattr(
                        masks, "dtype") and hasattr(
                            masks.dtype, "name") else masks.dtype if hasattr(
                                masks, "dtype") else masks.type
                # NOTE: HAL decoder requires shape [1, 160, 160, 32]
                if shape[1] == 32:
                    shape = [shape[0], shape[2], shape[3], shape[1]]
                self.masks["shape"] = shape
                self.masks["dtype"] = dtype
                self.masks["type"] = "protos"

                self.metadata["outputs"].append(self.masks)
            self.metadata["outputs"].append(self.scores)

        # ModelPack segmentation
        else:
            if self.masks["index"] is not None:
                self.masks["decoder"] = "modelpack"

                masks = self.outputs[self.masks["index"]]
                if isinstance(masks, dict):
                    shape = masks["shape"].tolist()
                    dtype = np.dtype(masks["dtype"]).name
                    self.masks["quantization"] = masks["quantization"]
                else:
                    shape = list(masks.shape)
                    dtype = masks.dtype.name if hasattr(
                        masks, "dtype") and hasattr(
                            masks.dtype, "name") else masks.dtype if hasattr(
                                masks, "dtype") else masks.type
                self.masks["shape"] = shape
                self.masks["dtype"] = dtype
                self.metadata["outputs"].append(self.masks)

    def get_boxes_index(self) -> Union[int, None]:
        """
        Get the index of the bounding box outputs from the model.
        Checking for Ultralytics and ModelPack variations.
        Box output shapes can be in these variations:
        [1, 6000, 1, 4], [1, 6000, 4], [1, 4, 8400]

        Returns
        -------
        Union[int, None]
            The index is returned if the bounding box output shape exists.
            Otherwise None is returned.
        """

        for i, output in enumerate(self.outputs):
            if isinstance(output, dict):
                shape = output["shape"]
            else:
                shape = output.shape

            if (len(shape) == 4 and shape[-1] == 4):
                self.num_boxes = shape[1]
                return i
            elif len(shape) == 3:
                if shape[1] == 4:
                    self.num_boxes = shape[-1]
                    return i
                elif shape[-1] == 4:
                    self.num_boxes = shape[1]
                    return i
        return None

    def get_masks_index(self) -> Union[int, None]:
        """
        Get the index of the encoded mask outputs from the model.
        Checking for ModelPack variations only.
        Mask shapes are typically [1, h, w, nc].

        Returns
        -------
        Union[int, None]
            The index is returned if the mask output shape exists.
            Otherwise None is returned.
        """
        for i, output in enumerate(self.outputs):
            if isinstance(output, dict):
                shape = output["shape"]
            else:
                shape = output.shape
            if len(shape) == 4 and shape[-2] != 1:  # Avoid shape of the boxes.
                return i
        return None

    def get_scores_index(self) -> Union[int, None]:
        """
        Get the index of the score outputs from the model.
        Checking for ModelPack and Ultralytics variations.
        Score output shapes can be in these variations:
        [1, 6000, 14], [1, 37, 8400], [1, 25200, 85], [1, 80, 8400]

        Returns
        -------
        Union[int, None]
            The index is returned if the score output shape exists.
            Otherwise None is returned.
        """
        for i, output in enumerate(self.outputs):
            if isinstance(output, dict):
                shape = output["shape"]
            else:
                shape = output.shape
            if self.num_boxes != 0:
                if len(shape) == 3 and self.num_boxes in [shape[1], shape[-1]]:
                    return i
                # MobileNet SSD [1, 10]
                elif len(shape) == 2 and i == 2 and shape[1] == self.num_boxes:
                    return i
            else:
                if len(shape) == 3:
                    if (((shape[1] > shape[2]) and (shape[1] / shape[2] > 5))
                        or ((shape[1] < shape[2]) and (shape[2] / shape[1] > 5))
                            and i != self.boxes["index"]):
                        return i
        return None

    def get_decoded_masks_index(self) -> Union[dict, None]:
        """
        Get the index of the decoded mask outputs from the model.
        Checking for ModelPack variations only.

        Returns
        -------
        Union[int, None]
            The index is returned if the decoded mask output shape exists.
            Otherwise None is returned.
        """
        # Segmentation will contain both encoded and decoded masks.
        if len(self.outputs) > 1:
            for i, output in enumerate(self.outputs):
                if isinstance(output, dict):
                    shape = output["shape"]
                else:
                    shape = output.shape
                if self.num_boxes != 0:
                    if len(shape) == 3 and self.num_boxes not in [
                            shape[1], shape[-1]]:
                        return i
                else:
                    if len(shape) == 3:
                        if ((shape[1] >= shape[2]) and (shape[1] / shape[2] < 5)) or (
                                (shape[1] <= shape[2]) and (shape[2] / shape[1] < 5)):
                            return i
        return None

    def get_classes_index(self) -> Union[int, None]:
        """
        Get the index of the class outputs. This is primarily seen
        in MobileNet SSD models.
        Score outputs are in these variations: [1, 10].

        Returns
        -------
        Union[int, None]
            The index is returned if the class output shape exists.
            Otherwise None is returned.
        """

        for i, output in enumerate(self.outputs):
            if isinstance(output, dict):
                shape = output["shape"]
            else:
                shape = output.shape
            if self.num_boxes != 0:
                # MobileNet SSD [1, 10]
                if len(shape) == 2 and i == 1 and shape[1] == self.num_boxes:
                    return i
        return None
