"""
Common parent dataset implementations.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Union, Tuple

import numpy as np

from edgefirst.validator.datasets.utils.annotation_transforms import (denormalize_polygon,
                                                                      xcycwh2xyxy,
                                                                      xywh2xyxy,
                                                                      normalize)
from edgefirst.validator.datasets.utils.readers import read_image

if TYPE_CHECKING:
    from edgefirst.validator.evaluators import (DatasetParameters,
                                                TimerContext, StageTracker)
    from edgefirst_hal import TensorImage  # type: ignore
    from edgefirst.validator.datasets import (
        SegmentationInstance, DetectionInstance, MultitaskInstance)


class Dataset:
    """
    Abstract dataset class for providing template methods in the dataset.

    Parameters
    ----------
    source: str
        The path to the source dataset.
    parameters: DatasetParameters
        This contains dataset parameters set from the command line.
    timer: TimerContext
        A timer object for handling validation timings for the model.
    info_dataset: Union[dict, None]
        Contains information such as:

            .. code-block:: python

                {
                    "classes": [list of unique labels],
                    "validation":
                    {
                        "images: 'path to the images',
                        "annotations": 'path to the annotations'
                    }
                }

        *Note: the classes are optional and the path to the images
        and annotations can be the same.*

    Raises
    ------
    ValueError
        Raised if the provided parameters in certain methods
        does not conform to the specified data type.
    """

    def __init__(
        self,
        source: str,
        parameters: DatasetParameters,
        timer: TimerContext,
        stage_tracker: StageTracker,
        info_dataset: Union[dict, None] = None
    ):
        self.source = source
        self.parameters = parameters
        self.timer = timer
        self.stage_tracker = stage_tracker
        self.info_dataset = info_dataset
        self.samples = []

        self.transformer = None
        if self.parameters.box_format == 'xcycwh':
            self.transformer = xcycwh2xyxy
        elif self.parameters.box_format == 'xywh':
            self.transformer = xywh2xyxy
        else:
            self.transformer = None

        self.normalizer = None
        self.denormalizer = None
        if self.parameters.normalized:
            if self.parameters.common.with_masks:
                self.denormalizer = denormalize_polygon
        else:
            if self.parameters.common.with_boxes:
                self.normalizer = normalize

    def __len__(self) -> int:
        """
        Returns the number of samples in the dataset.
        """
        return len(self.samples)

    def __iter__(self):
        """
        Reads all the samples in the dataset.

        Yields
        -------
        Instance
            Yields one sample of the ground truth
            instance which contains information on the image
            as a NumPy array, boxes, labels, and image path.
        """
        if self.parameters.silent:
            samples = self.collect_samples()
            for sample in samples:
                yield self.read_sample(sample)
        else:
            samples = self.stage_tracker.stage_generator(
                self.collect_samples(), stage_name="stage_validate",
                colour="green")
            for sample in samples:
                yield self.read_sample(sample)

    def verify_dataset(self):
        """Abstract Method"""

    def read_sample(
        self,
        sample: Union[list, Tuple[str, str], str]
    ) -> Union[DetectionInstance, SegmentationInstance, MultitaskInstance, None]:
        """
        Reads one sample from the dataset.

        Parameters
        -----------
        sample: Union[list, Tuple[str, str], str]
            For EdgeFirstDatabase, this is a list. For Darknet datasets,
            this is a Tuple[str, str] containing the path to the image
            and annotations. For dataset cache, this is a string
            as the image name.

            A single dataset sample contains the indices
            in the dataframe pointing to all the annotations
            in the dataset for this sample.

        Returns
        -------
        Union[DetectionInstance, SegmentationInstance, MultitaskInstance]
            The ground truth instance objects contains the annotations
            representing the ground truth of the image.
        """
        if self.parameters.common.with_boxes and self.parameters.common.with_masks:
            return self.build_multitask_instance(sample)
        elif self.parameters.common.with_boxes:
            return self.build_detection_instance(sample)
        elif self.parameters.common.with_masks:
            return self.build_segmentation_instance(sample)
        else:
            raise ValueError(
                "Could not determine model task as detection or segmentation.")

    def load_image(
        self,
        image_path: str,
        backend: str = "hal"
    ) -> Union[TensorImage, np.ndarray]:
        """
        Load the image into memory using various libraries: "hal", "opencv",
        or "pillow".

        Parameters
        ----------
        image_path: str
            The path to the image.
        backend: str
            Specify the backend library for resizing the image
            from the options "hal", "opencv", "pillow".

        Returns
        -------
        Union[edgefirst_hal.TensorImage, np.ndarray]
            TensorImage is returned when using "hal". Otherwise, a
            NumPy array is returned.

        Raises
        ------
        ImportError
            Raised if the required library for reading the image is not installed.
        FileNotFoundError
            Raised if the image path does not exist or unable to load.
        """

        if backend == "hal":
            try:
                import edgefirst_hal  # type: ignore
            except ImportError as exc:
                raise ImportError(
                    "EdgeFirst HAL is needed to read the image."
                ) from exc
            # Read the image.
            return edgefirst_hal.TensorImage.load(
                image_path, fourcc=edgefirst_hal.FourCC.RGBA)
        elif backend == "opencv":
            try:
                import cv2  # type: ignore
            except ImportError as exc:
                raise ImportError(
                    "OpenCV is needed to read the image."
                ) from exc

            image = cv2.imread(image_path)
            if image is None:
                raise FileNotFoundError(
                    f"Image not found or unable to load: {image_path}")
            return image
        else:
            return read_image(image_path, rotate=True)

    def image(self, sample: Union[tuple, list]):
        """Abstract Method"""
        raise NotImplementedError("Abstract Method")

    def boxes(self, sample: list) -> np.ndarray:
        """Abstract Method"""
        raise NotImplementedError("Abstract Method")

    def mask(
            self, sample: list,
            shapes: list,
            image_shape: tuple) -> np.ndarray:
        """Abstract Method"""
        raise NotImplementedError("Abstract Method")

    def segments(
            self, sample: list,
            image_shape: tuple,
            resample: int = 1000) -> np.ndarray:
        """Abstract Method"""
        raise NotImplementedError("Absract Method")

    def name(self, sample: list) -> str:
        """Abstract Method"""
        raise NotImplementedError("Abstract Method")

    def collect_samples(self):
        """Abstract Method"""
        raise NotImplementedError("This is an abstract method.")

    def build_detection_instance(
            self, sample: Union[list, Tuple[str, str], str]):
        """Abstract Method"""

    def build_segmentation_instance(
            self, sample: Union[list, Tuple[str, str], str]):
        """Abstract Method"""

    def build_multitask_instance(
            self, sample: Union[list, Tuple[str, str], str]):
        """Abstract Method"""
