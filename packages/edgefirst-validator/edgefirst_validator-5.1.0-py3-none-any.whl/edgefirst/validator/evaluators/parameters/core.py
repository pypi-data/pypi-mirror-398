"""
The core and common parameters across the dataset, model, and validation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Union, List, Callable

import numpy as np

from edgefirst.validator.publishers.utils.logger import logger

if TYPE_CHECKING:
    from edgefirst_hal import TensorImage  # type: ignore


class Parameters:
    """
    Parent parameters to contain common parameters between
    the model, dataset, and validation.

    Parameters
    ----------
    labels_path: Optional[str]
        The path to the labels.txt file containing unique string labels
        from the model or the dataset.
    labels: Optional[List[str]]
        A list of unique string labels which is part of the model artifacts
        for converting model output indices into strings.
    label_offset: int
        This is the offset to map the integer labels to string labels.
    box_format: str
        The output bounding box format of the model. Options could be one
        of the following: "xyxy" (PascalVOC), "xywh" (COCO), or "xcycwh" (YOLO).
    """

    def __init__(
        self,
        labels_path: Optional[str] = None,
        labels: Optional[List[str]] = None,
        label_offset: int = 0,
        box_format: str = "xyxy",

    ):
        self.__labels_path = labels_path
        self.__labels = labels
        self.__label_offset = label_offset
        self.__box_format = box_format.lower()

    @property
    def labels_path(self) -> Union[str, None]:
        """
        Attribute to access the labels_path.
        This is the path to the labels.txt file. This contains unique string
        labels from either the dataset or the model.

        Returns
        -------
        Union[str, None]
            The path to the labels.txt file.
        """
        return self.__labels_path

    @labels_path.setter
    def labels_path(self, path: Union[str, None]):
        """
        Set the path to the labels.txt file.

        Parameters
        ----------
        path: Union[str, None]
            The path to the labels.txt file.
        """
        self.__labels_path = path

    @property
    def labels(self) -> Union[List[str], None]:
        """
        Attribute to access the model labels.
        This is used for mapping the prediction integer indices to strings.

        Returns
        -------
        Union[List[str], None]
            The list of unique string labels from the model.
        """
        return self.__labels

    @labels.setter
    def labels(self, this_labels: Union[List[str], None]):
        """
        Sets the string labels for mapping the integer indices to
        string representations.

        Parameters
        ----------
        this_labels: Union[List[str], None]
            The labels to set.
        """
        self.__labels = this_labels

    @property
    def label_offset(self) -> int:
        """
        Attribute to access the label offset for the predictions.
        This is used for mapping the prediction integer labels to strings.

        Returns
        -------
        int
            The label offset to map integer indices to string representations.
        """
        return self.__label_offset

    @label_offset.setter
    def label_offset(self, this_label_offset: int):
        """
        Sets the label offset for mapping the integer indices to
        string representations.

        Parameters
        ----------
        this_label_offset: int
            The label_offset to set.
        """
        self.__label_offset = this_label_offset

    @property
    def box_format(self) -> str:
        """
        Attribute to access the box format.
        The box format can either be: "xyxy", "xywh", "yxyx"

        Returns
        -------
        str
            The box format type.
        """
        return self.__box_format

    @box_format.setter
    def box_format(self, this_box_format: str):
        """
        Sets the box format type.

        Parameters
        ----------
        this_box_format: str
            The box format to set.
        """
        if this_box_format not in ['xcycwh', 'xywh', 'xyxy']:
            raise ValueError(
                f"Unsupported box format provided: {this_box_format}")
        self.__box_format = this_box_format.lower()


class CommonParameters:
    """
    Parameters that are common between all three parameter types
    where each of these parameters should remain consistent across
    the model, dataset, and validation.

    Parameters
    ----------
    with_boxes: bool
        The condition of whether or not the dataset and the model both provide
        bounding box detections.
    with_masks: bool
        The condition of whether or not the dataset and the model both provide
        segmentation mask detections.
    norm: str
        The type of image normalization to match the model input requirements.
        Options could be one of the following: "raw", "unsigned", "signed",
        "imagenet", or "whitening".
    preprocessing: str
        The type of image preprocessing to apply to the image prior to model
        inference. Options could be one of the following: "letterbox", "pad",
        "resize".
    shape: Optional[tuple]
        Specify the input shape of the model which is needed to transform
        the input image to the size requirements.
    dtype: np.dtype
        The input data type of the model.
    input_quantization: Optional[tuple]
        The model input quantization as part of the image preprocessing
        for quantizing float32 outputs to integer types.
    backend: str
        The library to use for image loading and image preprocessing.
    """

    def __init__(
        self,
        with_boxes: bool = False,
        with_masks: bool = False,
        norm: str = "raw",
        preprocessing: str = "letterbox",
        shape: Optional[tuple] = None,
        dtype: np.dtype = np.dtype(np.float32),
        input_quantization: Optional[tuple] = None,
        backend: str = "hal",
    ):

        self.__with_boxes = with_boxes
        self.__with_masks = with_masks
        self.__norm = norm.lower()
        self.__preprocessing = preprocessing.lower()
        self.__shape = shape
        self.__dtype = dtype
        self.__input_quantization = input_quantization
        self.__semantic = True
        self.__input_tensor = None  # NumPy view array for model direct copies.
        self.__input_dst = None  # Input TensorImage destination.
        self.__backend = backend.lower()
        # Condition whether to transpose the input image or not.
        self.__transpose = False

    def check_backend_availability(self):
        """
        Checks the backend availability and falls back on any
        available backends starting from "hal" to "opencv" and then
        to "pillow".
        """
        if self.backend == "hal":
            try:
                import edgefirst_hal  # type: ignore # pylint: disable=unused-import
            except ImportError:
                try:
                    import cv2  # type: ignore # pylint: disable=unused-import
                    self.backend = "opencv"
                    logger("HAL backend is not available. Falling back to OpenCV.",
                           code="WARNING")
                except ImportError:
                    self.backend = "pillow"
                    logger("HAL and OpenCV backends are not available. "
                           "Falling back to Pillow.", code="WARNING")
        elif self.backend == "opencv":
            try:
                import cv2  # type: ignore # pylint: disable=unused-import
            except ImportError:
                self.backend = "pillow"
                logger("OpenCV backend is not available. Falling back to Pillow.",
                       code="WARNING")

    @property
    def with_boxes(self) -> bool:
        """
        Attribute to access with_boxes.
        Specify whether the model or the dataset provides
        bounding box annotations.

        Returns
        -------
        bool
            Condition for object detection (bounding box) validation.
        """
        return self.__with_boxes

    @with_boxes.setter
    def with_boxes(self, boxes: bool):
        """
        Specify condition for object detection (bounding box) validation.

        Parameters
        ----------
        boxes: bool
            The condition to set.
        """
        self.__with_boxes = boxes

    @property
    def with_masks(self) -> bool:
        """
        Attribute to access with_masks.
        Specify whether the model or the dataset provides
        segmentation annotations.

        Returns
        -------
        bool
            Condition for segmentation validation.
        """
        return self.__with_masks

    @with_masks.setter
    def with_masks(self, masks: bool):
        """
        Specify condition for segmentation validation.

        Parameters
        ----------
        masks: bool
            The condition to set.
        """
        self.__with_masks = masks

    @property
    def norm(self) -> str:
        """
        Attribute to access the image normalization type.
        Typically quantized models use "raw" and floating point models
        use "unsigned" or "signed".

        Returns
        -------
        str
            The image normalization type.
        """
        return self.__norm

    @norm.setter
    def norm(self, this_norm: str):
        """
        Sets the image normalization type.

        Parameters
        ----------
        this_norm: str
            The image normalization to set.
        """
        self.__norm = this_norm.lower() if this_norm is not None else this_norm

    @property
    def preprocessing(self) -> str:
        """
        Attribute to access the type of image preprocessing to perform.
        Options can be "letterbox", "pad", or "resize".

        Returns
        -------
        str
            The type of image preprocessing to perform.
        """
        return self.__preprocessing

    @preprocessing.setter
    def preprocessing(self, preprocess: str):
        """
        Sets the type of image preprocessing to perform.

        Parameters
        ----------
        preprocess: str
            The type of image preprocessing to set. Options include
            "letterbox", "pad", or "resize".
        """
        self.__preprocessing = (preprocess.lower() if
                                preprocess is not None else preprocess)

    @property
    def shape(self) -> Union[tuple, None]:
        """
        Attribute to access the model's input shape.

        Returns
        --------
        Union[tuple, None]
            The input shape of the model.
        """
        return self.__shape

    @shape.setter
    def shape(self, size: Union[tuple, None]):
        """
        Sets the input shape of the model.

        Parameters
        ----------
        size: Union[tuple, None]
            The model input shape to set.
        """
        self.__shape = size

    @property
    def dtype(self) -> np.dtype:
        """
        Attribute to access the model dtype.
        By default this is set to "float32". However, possible
        variations include "float16", "int8", "uint8", etc.

        Returns
        -------
        np.dtype
            The model datatype
        """
        return self.__dtype

    @dtype.setter
    def dtype(self, this_dtype: np.dtype):
        """
        Sets the model data type.

        Parameters
        ----------
        this_dtype: np.dtype
            The model data type to set.
        """
        self.__dtype = this_dtype

    @property
    def input_quantization(self) -> Union[tuple, None]:
        """
        Attribute to access the model input quantization.
        This is a tuple that contains the (scale, zero_point) values
        needed for quantizating the input to the model.

        Returns
        -------
        Union[tuple, None]
            The model input quantization (scale, zero_point).
        """
        return self.__input_quantization

    @input_quantization.setter
    def input_quantization(self, quantization: Union[tuple, None]):
        """
        Sets the model input quantization.

        Parameters
        ----------
        quantization: Union[tuple, None]
            The input quantization containing the
            (scale, zero_point) values.
        """
        self.__input_quantization = quantization

    @property
    def semantic(self) -> bool:
        """
        Attribute to access the semantic condition.

        Returns
        -------
        bool
            Specify to True if the model is a semantic segmentation
            model as seen in ModelPack. Otherwise False for instance
            segmentation as seen in Ultralytics.
        """
        return self.__semantic

    @semantic.setter
    def semantic(self, condition: bool):
        """
        Sets the specification if the model being validated
        is semantic segmentation (True) or instance segmentation (False).

        Parameters
        ----------
        condition: bool
            Specify the semantic condition.
        """
        self.__semantic = condition

    @property
    def input_tensor(self) -> Union[Callable, None]:
        """
        Attribute to access the input tensor.

        Returns
        -------
        Union[Callable, None]
            Callable function for retrieving the input view tensor
            from the model for directly copying the input tensor
            into the model such as the case for TFLite.
        """
        return self.__input_tensor

    @input_tensor.setter
    def input_tensor(self, tensor: Union[Callable, None]):
        """
        Sets the input tensor.

        Parameters
        ----------
        tensor: Union[Callable, None]
            Callable function for retrieving the input view tensor
            from the model for directly copying the input tensor
            into the model such as the case for TFLite.
        """
        self.__input_tensor = tensor

    @property
    def input_dst(self) -> Union[TensorImage, None]:
        """
        Attribute to access the input destination.

        Returns
        -------
        Union[TensorImage, None]
            Optimization to initialize the input destination once
            upon model load. This prevents the redundant creation
            of the input destination at each sample. The input destination
            tensor image will contain all the image transformations.
        """
        return self.__input_dst

    @input_dst.setter
    def input_dst(self, dst: Union[TensorImage, None]):
        """
        Sets the input destination.

        Parameters
        ----------
        dst: Union[TensorImage, None]
            Optimization to initialize the input destination once
            upon model load. This prevents the redundant creation
            of the input destination at each sample. The input destination
            tensor image will contain all the image transformations.
        """
        self.__input_dst = dst

    @property
    def backend(self) -> str:
        """
        Attribute to access the backend.
        This is the library to use for running the image
        loading and input preprocessing.

        Returns
        -------
        str
            The library to use "hal", "opencv", "pillow".
        """
        return self.__backend

    @backend.setter
    def backend(self, backend: str):
        """
        Set the library backend to use for input preprocessing.

        Parameters
        ----------
        backend: str
            The backend library to use for input preprocessing
            from the options "hal", "opencv", "pillow".
        """
        self.__backend = backend

    @property
    def transpose(self) -> bool:
        """
        Attribute to access the transpose condition.

        Returns
        -------
        bool
            The condition of whether or not the input
            image is channels first (True) or channels last (False).
        """
        return self.__transpose

    @transpose.setter
    def transpose(self, transpose: bool):
        """
        Set the condition to transpose the input image.

        Parameters
        ----------
        transpose: bool
            If True, the input image will be transposed to
            channels first. Otherwise, the image has
            channels last.
        """
        self.__transpose = transpose
