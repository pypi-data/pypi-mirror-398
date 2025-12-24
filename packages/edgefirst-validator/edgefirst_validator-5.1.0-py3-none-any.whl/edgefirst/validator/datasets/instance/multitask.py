"""
Defines the MultitaskInstance class for storing bounding boxes, labels, scores, and masks.
"""

from typing import Union

import numpy as np

from edgefirst.validator.datasets.instance import DetectionInstance


class MultitaskInstance(DetectionInstance):
    """
    Instance for storing Multitask ground truth and model predictions
    for Vision which has bounding boxes, labels, scores, and masks.

    Parameters
    ----------
    image_path: str
        The path to the image for Darknet datasets. Otherwise this is the
        image name for TFRecord datasets. This is required either to
        allow reading the image from file or saving the image results
        in disk with the same file name.
    """

    def __init__(self, image_path: str):
        super(MultitaskInstance, self).__init__(image_path)

        # These contain the segmentation points to form the
        # polygon shape around the object.
        self.__polygons = np.array([])
        # This is the segmentation mask for the image.
        self.__mask = None

    @property
    def polygons(self) -> Union[list, np.ndarray]:
        """
        Attribute to access the 2D points that form the polygon to shape
        around the object to form segmentation masks.

        Returns
        -------
        Union[list, np.ndarray]
            This contains the polygon points. Ex.
            [[[x1,y1], [x2,y2], ... ,[xn,yn]], [...], ...]
        """
        return self.__polygons

    @polygons.setter
    def polygons(self, new_polygons: Union[list, np.ndarray]):
        """
        Sets the polygons to a new value.

        Parameters
        ----------
        new_polygons: Union[list, np.ndarray]
            This is the polygons to set.
        """
        self.__polygons = new_polygons

    @property
    def mask(self) -> Union[np.ndarray, None]:
        """
        Attribute to access the segmentation mask of the image.

        Returns
        -------
        Union[np.ndarray, None]
            This contains the mask with the same dimensions as the image
            providing an integer label per pixel to represent the mask.
        """
        return self.__mask

    @mask.setter
    def mask(self, new_mask: Union[np.ndarray, None]):
        """
        Sets the mask to a new value.

        Parameters
        ----------
        new_mask: Union[np.ndarray, None]
            This is the mask to set.
        """
        self.__mask = new_mask
