"""
Defines the SegmentationInstance class for storing segmentation masks, labels, and polygons.
"""

from typing import Union

import numpy as np

from edgefirst.validator.datasets.instance import Instance


class SegmentationInstance(Instance):
    """
    Instance for storing segmentation properties from the
    ground truth or model predictions.

    Parameters
    ----------
    image_path: str
        The path to the image for Darknet datasets. Otherwise this is the
        image name for TFRecord datasets. This is required either to
        allow reading the image from file or saving the image results
        in disk with the same file name.
    """

    def __init__(self, image_path: str):
        super(SegmentationInstance, self).__init__(image_path)

        # These are the unique integer labels in the segmentation mask.
        self.__labels = np.array([])
        # These contain the segmentation points to form the
        # polygon shape around the object.
        self.__polygons = np.array([])
        # This is the segmentation mask for the image.
        self.__mask = None

    @property
    def labels(self) -> Union[list, np.ndarray]:
        """
        Attribute to access the labels per bounding box.

        Returns
        -------
        Union[list, np.ndarray]
            This contains the labels per bounding box.
        """
        return self.__labels

    @labels.setter
    def labels(self, new_labels: Union[list, np.ndarray]):
        """
        Sets the labels to a new value.

        Parameters
        ----------
        new_labels: Union[list, np.ndarray]
            These are the labels to set.
        """
        self.__labels = new_labels

    def append_labels(self, label: Union[str, int, np.integer]):
        """
        Appends list or appends NumPy array label.

        Parameters
        ----------
        label: Union[str, int, np.integer]
            This is the label to append to the list.
        """
        if isinstance(self.__labels, np.ndarray):
            self.__labels = np.append(self.__labels, label)
        else:
            self.__labels.append(label)

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
