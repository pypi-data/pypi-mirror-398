"""
Defines the core Instance object for holding ground truth dataset instances.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Union, Tuple, List

import numpy as np

if TYPE_CHECKING:
    from edgefirst.validator.evaluators import StageTracker


class Instance:
    """
    Base Instance object for containing the ground truth dataset instance.

    Parameters
    ----------
    image_path: str
        The path to the image for Darknet datasets. Otherwise this is the
        image name for TFRecord datasets. This is required either to
        allow reading the image from file or saving the image results
        in disk with the same file name.
    """

    def __init__(self, image_path: str):
        self.__image_path = image_path
        # This is the NumPy array image.
        self.__image = None
        self.__visual_image = None
        self.__height = 0
        self.__width = 0

        # Same property used in YOLOv5 and YOLOv7 for the shapes.
        self.__shapes = [
            [
                [0, 0],  # imgsz (model input shape) [height, width]
                # ratio_pad [[scale y, scale x], [pad w, pad h]]
                [(1.0, 1.0), (0.0, 0.0)]
            ],
            [1.0, 1.0]  # label ratio [x, y]
        ]
        # The original image dimensions.
        self.__image_shape = None

    @property
    def image_path(self) -> str:
        """
        Attribute to access the image path/name.

        Returns
        -------
        str
            The image path/name.
        """
        return self.__image_path

    @image_path.setter
    def image_path(self, path: str):
        """
        Sets the image path/name.

        Parameters
        ----------
        path: str
            The image path/name.
        """
        self.__image_path = path

    @property
    def image(self) -> Union[np.ndarray, None]:
        """
        Attribute to access the image.

        Returns
        -------
        Union[np.ndarray, None]
            The image as a NumPy array.
        """
        return self.__image

    @image.setter
    def image(self, this_image: Union[np.ndarray, None]):
        """
        Sets the image array.

        Parameters
        ----------
        this_image: Union[np.ndarray, None]
            The image array.
        """
        self.__image = this_image

    @property
    def visual_image(self) -> Union[np.ndarray, None]:
        """
        Attribute to access the image.

        Returns
        -------
        Union[np.ndarray, None]
            The image as a NumPy array.
        """
        return self.__visual_image

    @visual_image.setter
    def visual_image(self, this_image: Union[np.ndarray, None]):
        """
        Sets the image array.

        Parameters
        ----------
        this_image: Union[np.ndarray, None]
            The image array.
        """
        self.__visual_image = this_image

    @property
    def height(self) -> int:
        """
        Attribute to access the image height in pixels.

        Returns
        -------
        int
            The image height in pixels. 0 means uninitialized.
        """
        return self.__height

    @height.setter
    def height(self, image_height: int):
        """
        Sets the image height dimension to a new value.

        Parameters
        ----------
        image_height: int
            This is the new image height to set.
        """
        self.__height = image_height

    @property
    def width(self) -> int:
        """
        Attribute to access the image width in pixels.

        Returns
        -------
        int:
            The image width in pixels. 0 means uninitialized.
        """
        return self.__width

    @width.setter
    def width(self, image_width: int):
        """
        Sets the image width dimension to a new value.

        Parameters
        ----------
        image_width: int
            This is the new image width to set.
        """
        self.__width = image_width

    @property
    def shapes(self) -> list:
        """
        Attribute to access the inference shapes which includes
        the image shape after letterbox operation and aswell as padding
        and ratio which are variables that mirrors YOLOv5 and YOLOv7
        implementation of the letterbox image processing.
        This attribute is used for bounding box rescaling for both the
        ground truth and detections.

        Returns
        -------
        list
            .. code-block:: python

                [
                    [image height, image width]],
                    [[ratio y, ratio x], [pad x, pad y]],
                    label_ratio
                ]
        """
        return self.__shapes

    @shapes.setter
    def shapes(self, shape: list):
        """
        Sets the shapes attribute to a new value.

        Parameters
        ----------
        shape: list
            .. code-block:: python

                [
                    [image height, image width]],
                    [[ratio y, ratio x], [pad x, pad y]],
                    label_ratio
                ]
        """
        self.__shapes = shape

    @property
    def image_shape(self) -> Union[tuple, None]:
        """
        Attribute to access the image shape.
        This is the original image dimensions prior
        to image preprocessing.

        Returns
        -------
        Union[tuple, None]
            This contains the image (height, width) dimensions.
        """
        return self.__image_shape

    @image_shape.setter
    def image_shape(self, shape: Union[tuple, None]):
        """
        Sets the image shape.

        Parameters
        ----------
        shape: Union[tuple, None]
            Sets the original image dimensions.
        """
        self.__image_shape = shape


class InstanceCollection:
    """
    Collect all ground truth and prediction
    instances for further postprocessing.

    Ground truth and predictions must have the same length and
    in the same order.

    Parameters
    ----------
    stage_tracker: StageTracker
        The object used for tracking and displaying stages.
    """

    def __init__(self, stage_tracker: StageTracker):
        self.stage_tracker = stage_tracker
        self.__gt_instances = []
        self.__dt_instances = []

    def __iter__(self):
        """
        Iterator to loop through both the ground truth and prediction instances.
        """

        instances = self.stage_tracker.stage_generator(
            self.get_instances(), stage_name="stage_dmetrics", colour="green")
        for gt_instance, dt_instance in instances:
            yield {
                "gt_instance": gt_instance,
                "dt_instance": dt_instance
            }

    @property
    def gt_instances(self) -> List[Instance]:
        """
        Attribute to access the ground truth instance list.

        Returns
        -------
        List[Instance]
            A list of instances for the ground truth.
        """
        return self.__gt_instances

    @property
    def dt_instances(self) -> List[Instance]:
        """
        Attribute to access the detection instance list.

        Returns
        -------
        List[Instance]
            A list of instances for the model predictions.
        """
        return self.__dt_instances

    def append_instance(self, gt_instance: Instance, dt_instance: Instance):
        """
        Appends a single instance to the list for both the ground truth
        and the predictions.

        Parameters
        ----------
        gt_instance: Instance
            A ground truth instance to append.
        dt_instance: Instance
            A prediction instance to append.
        """
        self.gt_instances.append(gt_instance)
        self.dt_instances.append(dt_instance)

    def get_instances(self) -> List[Tuple[Instance, Instance]]:
        """
        Returns both the ground truth and prediction instance lists.

        Returns
        -------
        Tuple[List[Instance], List[Instance]]
            A tuple containing both the ground truth and prediction
            instance lists.
        """
        return list(zip(self.gt_instances, self.dt_instances))
