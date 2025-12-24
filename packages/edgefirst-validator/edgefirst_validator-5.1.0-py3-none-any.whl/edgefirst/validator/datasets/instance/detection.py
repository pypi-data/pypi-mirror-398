"""
Defines the DetectionInstance class for storing bounding boxes, labels, and scores.
"""

from typing import Union

import numpy as np

from edgefirst.validator.datasets.instance import Instance


class DetectionInstance(Instance):
    """
    Instance for storing ground truth and
    model bounding boxes, labels, and scores.

    Parameters
    ----------
    image_path: str
        The path to the image for Darknet datasets. Otherwise this is the
        image name for TFRecord datasets. This is required either to
        allow reading the image from file or saving the image results
        in disk with the same file name.
    """

    def __init__(self, image_path: str):
        super(DetectionInstance, self).__init__(image_path)

        # These are the 2D bounding boxes in either YOLO, COCO, or PascalVoc.
        self.__boxes = np.array([])
        # These contain either string or integer labels per bounding box.
        self.__labels = np.array([])
        # These contain the prediction scores per bounding box. Empty if gt.
        self.__scores = np.array([])

    @property
    def boxes(self) -> Union[list, np.ndarray]:
        """
        Attribute to access the 2D bounding boxes for detection.

        Returns
        -------
        Union[list, np.ndarray]
            This contains the 2D normalized bounding boxes.
        """
        return self.__boxes

    @boxes.setter
    def boxes(self, boxes_2d: Union[list, np.ndarray]):
        """
        Sets the 2D bounding boxes to a new value.

        Parameters
        ----------
        boxes_2d: Union[list, np.ndarray]
            These are the 2D bounding boxes to set.
        """
        self.__boxes = boxes_2d

    def append_boxes(self, box: Union[list, np.ndarray]):
        """
        Appends list or stacks NumPy array 2D bounding boxes.

        Parameters
        ----------
        box: Union[list, np.ndarray]
            This is the 2D normalized bounding box in either
            YOLO, COCO, or PascalVoc.
        """
        if isinstance(self.__boxes, np.ndarray):
            self.__boxes = np.vstack([self.__boxes, box])
        else:
            self.__boxes.append(box)

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
    def scores(self) -> Union[list, np.ndarray]:
        """
        Attribute to access the scores per bounding box.

        Returns
        -------
        Union[list, np.ndarray]
            This contains the scores per bounding box.
        """
        return self.__scores

    @scores.setter
    def scores(self, new_scores: Union[list, np.ndarray]):
        """
        Sets the scores to a new value.

        Parameters
        ----------
        new_scores: Union[list, np.ndarray]
            These are the scores to set.
        """
        self.__scores = new_scores

    def append_scores(self, score: float):
        """
        Appends list or appends NumPy array scores.

        Parameters
        ----------
        score: float
            This is the score to append to the list.
        """
        if isinstance(self.__scores, np.ndarray):
            self.__scores = np.append(self.__scores, score)
        else:
            self.__scores.append(score)
