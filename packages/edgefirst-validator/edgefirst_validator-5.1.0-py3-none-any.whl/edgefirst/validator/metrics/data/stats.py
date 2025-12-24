"""
Defines the statistics containers needed for calculating metrics.
"""

from typing import List, Union

import numpy as np

from edgefirst.validator.metrics.data import (DetectionLabelData,
                                              SegmentationLabelData)


class DetectionStats:
    """
    Storing the pre-calculation statistics needed for the Ultralytics metrics.
    The statistics are formatted in the same manner as Ultralytics which
    contains the correction matrix, the prediction class,
    the prediction confidence, and the ground truth class all of which
    are used to calculate the metrics.

    The labeldata object contains DetectionLabelData containers for each
    label found during validation. A label container will store the
    number of ground truths, true positives, false positives, false negatives
    of the specific label. This will be used to calculate the
    deployment metrics.
    """

    def __init__(self):
        # Listing various IoU thresholds to evaluate the model.
        self.__ious = np.array([
            0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95])
        # This is used for the Ultralytics metrics calculation.
        self.__stats = {
            "tp": [],
            "conf": [],
            "pred_cls": [],
            "target_cls": [],
            "target_img": [],
            "tp_m": []
        }
        # A list containing the strings or integers of unique labels.
        self.__labels = list()
        # A list containing the DetectionLabelData objects for each label.
        # This is used for the computation of deployment metrics.
        self.__labeldata = list()

    @property
    def ious(self) -> np.ndarray:
        """
        Attribute to access the ious which contains the IoU steps for validation.
        By default set from 0.50 to 0.95 in 0.05 steps.

        Returns
        -------
        np.ndarray
            The list of IoUs to evaluate the model.
        """
        return self.__ious

    @ious.setter
    def ious(self, iou: np.ndarray):
        """
        Sets the IoU steps to a new value.

        Parameters
        ----------
        iou: np.ndarray
            These are the various IoU levels to evaluate the model.
        """
        self.__ious = iou

    @property
    def stats(self) -> dict:
        """
        Attribute to access the stats required for
        computing Ultralytics metrics.

        Returns
        -------
        dict
            This list contains the keys (['tp', 'conf', 'pred_cls',
            'target_cls', 'target_img', 'tp_m']) with the
            following items [tp (n, 10), conf (n, 1), pred_cls (n, 1),
            target_cls (n, 1), target_img (nc, ), tp_m (n, 10)].

            The tp/tp_m matrix contains True or False values for each IoU
            step of all n predictions. The conf contains the confidence
            scores of each prediction. The pred_cls contains the labels
            of each prediction. The target_cls contains the labels
            of each ground truth.
        """
        return self.__stats

    @stats.setter
    def stats(self, stat: dict):
        """
        Sets the stats to a new value.

        Parameters
        ----------
        stat: dict
            These are the stats to set.
        """
        self.__stats = stat

    @property
    def labels(self) -> list:
        """
        Attribute to access the list of unique labels found.

        Returns
        -------
        list
            This contains unique labels found during validation.
        """
        return self.__labels

    @labels.setter
    def labels(self, new_labels: list):
        """
        Sets the list of unique labels found during validation.

        Parameters
        ----------
        new_labels: list
            This is the list of unique labels found during validation.
        """
        self.__labels = new_labels

    @property
    def labeldata(self) -> List[DetectionLabelData]:
        """
        Attribute to access the labeldata which contains DetectionLabelData
        objects needed to compute deployment metrics.

        Returns
        -------
        List[DetectionLabelData]
            This list contains DetectionLabelData objects where each
            object tracks the metrics of a specific label.
        """
        return self.__labeldata

    @labeldata.setter
    def labeldata(self, data: List[DetectionLabelData]):
        """
        Sets the labeldata to a new value.

        Parameters
        ----------
        data: List[DetectionLabelData]
            This is the labeldata list to set.
        """
        self.__labeldata = data

    def get_label_data(
        self,
        label: Union[str, int, np.integer]
    ) -> Union[DetectionLabelData, None]:
        """
        Grabs the DetectionLabelData object by the label.

        Parameters
        ----------
        label: Union[str, int, np.integer]
            A unique string label or integer index to
            fetch the LabelData container.

        Returns
        -------
        Union[DetectionLabelData, None]
            The data container of the label specified if
            it exists. None if the label does not exist.
        """
        for label_data in self.labeldata:
            if label_data.label == label:
                return label_data
        return None

    def add_label_data(self, label: Union[str, int, np.integer]):
        """
        Adds a DetectionLabelData object for the label.

        Parameters
        ----------
        label: Union[str, int, np.integer]
            The string label or the integer index
            to place as a data container.
        """
        self.labeldata.append(DetectionLabelData(label))

    def capture_class(self, labels: Union[list, np.ndarray]):
        """
        Records the unique labels encountered from the prediction and
        ground truth and creates a DetectionLabelData container
        for each unique label found. Ignores 'background' or empty string
        labels.

        Parameters
        ----------
        labels: Union[list, np.ndarray]
            This list contains labels for one image from either the
            ground truth or the predictions.
        """
        for label in labels:
            if isinstance(label, str):
                if label.lower() in ["background", " ", ""]:
                    continue
            if label not in self.labels:
                self.add_label_data(label)
                self.labels.append(label)

    def reset(self):
        """
        Resets the container back to an empty list.
        """
        self.labeldata = list()
        self.labels = list()
        self.stats = {
            "tp": [],
            "conf": [],
            "pred_cls": [],
            "target_cls": [],
            "target_img": [],
            "tp_m": []
        }


class SegmentationStats:
    """
    Acts as a container of SegmentationLabelData objects for each label
    and provides methods to capture the total number of true predictions
    and false predictions pixels.
    """

    def __init__(self):

        # A list containing the strings or integers of unique labels.
        self.__labels = list()
        # A list containing the SegmentationLabelData objects for each label.
        self.__stats = list()
        # A list containing the IoU values between the ground truth
        # and the prediction masks throughout the datasety.
        self.__ious = {}

    @property
    def labels(self) -> list:
        """
        Attribute to access the list of unique labels found.

        Returns
        -------
        list
            This contains unique labels found during validation.
        """
        return self.__labels

    @labels.setter
    def labels(self, new_labels: list):
        """
        Sets the list of unique labels found during validation.

        Parameters
        ----------
        new_labels: list
            This is the list of unique labels found during validation.
        """
        self.__labels = new_labels

    @property
    def stats(self) -> List[SegmentationLabelData]:
        """
        Attribute to access the stats which contains SegmentationLabelData
        objects needed to compute EdgeFirst metrics.

        Returns
        -------
        List[SegmentationLabelData]
            This list contains SegmentationLabelData objects where each
            object tracks the metrics of a specific label.
        """
        return self.__stats

    @stats.setter
    def stats(self, stat: List[SegmentationLabelData]):
        """
        Sets the stats to a new value.

        Parameters
        ----------
        stat: List[SegmentationLabelData]
            These are the stats to set.
        """
        self.__stats = stat

    @property
    def ious(self) -> dict:
        """
        Attribute to access the dictionary of IoUs between the
        ground truth and the prediction masks per class.

        Returns
        -------
        dict
            This contains the mask IoU values during validation.
        """
        return self.__ious

    @ious.setter
    def ious(self, this_ious: dict):
        """
        Sets the dictionary of mask IoU values during validation.

        Parameters
        ----------
        this_ious: dict
            This is the dictionary of IoU values during validation
            per class.

            .. code-block:: python

                {
                    'label_1': [iou_1, iou_2, ...],
                    'label_2': [iou_1, iou_2, ...],
                    ...
                }
        """
        self.__ious = this_ious

    def get_label_data(
        self,
        label: Union[str, int, np.integer]
    ) -> Union[SegmentationLabelData, None]:
        """
        Grabs the SegmentationLabelData object by the label.

        Parameters
        ----------
        label: Union[str, int, np.integer]
            A unique string label or integer index to
            fetch the LabelData container.

        Returns
        -------
        Union[SegmentationLabelData, None]
            The data container of the label specified if
            it exists. None if the label does not exist.
        """
        for label_data in self.stats:
            if label_data.label == label:
                return label_data
        return None

    def add_label_data(self, label: Union[str, int, np.integer]):
        """
        Adds a SegmentationLabelData object for the label.

        Parameters
        ----------
        label: Union[str, int, np.integer]
            The string label or the integer index
            to place as a data container.
        """
        self.stats.append(SegmentationLabelData(label))

    def capture_class(
        self,
        class_labels: Union[list, np.ndarray],
        labels: List[str] = None
    ):
        """
        Records the unique labels encountered in the prediction and
        ground truth and creates a container (SegmentationLabelData)
        for the label found in the model predictions and ground truth.

        Parameters
        ----------
        class_labels: list of int.
            All unique indices for the classes found from the ground
            truth and the model prediction masks.
        labels: list
            This list contains unique string labels for the classes found.
            This is optional to convert the integer labels into string
            labels.
        """
        for label in class_labels:
            if labels is not None:
                label: str = labels[label]
                if label.lower() in [" ", ""]:
                    continue
            if label not in self.labels:
                self.add_label_data(label)
                self.labels.append(label)

    def reset(self):
        """
        Resets the containers to an empty list
        and resets the labels captured to an empty list.
        """
        self.stats, self.labels = list(), list()
        self.ious = list()
