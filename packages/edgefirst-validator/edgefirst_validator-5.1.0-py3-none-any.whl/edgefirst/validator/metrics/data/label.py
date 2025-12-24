"""
Defines the label data containers for metrics computation per label.
"""

from typing import Union, List, Tuple

import numpy as np

from edgefirst.validator.datasets.utils.annotation_transforms import clamp


class LabelData:
    """
    Base class for the LabelData class that stores the pre-metric
    computations of a specific label in validation.

    Parameters
    ----------
    label: Union[str, int, np.integer]
        The unique string or integer index label to base the container.
    """

    def __init__(self, label: Union[str, int, np.integer]):
        # The label being represented in this class.
        self.__label = label
        # Total number of ground truths of the label.
        self.__ground_truths = 0
        # Total number of predictions of the label.
        self.__predictions = 0

    @property
    def label(self) -> Union[str, int, np.integer]:
        """
        Attribute to access the label stored.

        Returns
        -------
        Union[str, int, np.integer]
            The label stored.
        """
        return self.__label

    @label.setter
    def label(self, this_label: Union[str, int, np.integer]):
        """
        Sets the label.

        Parameters
        ----------
        this_label: Union[str, int, np.integer]
            The label being represented in this container.
        """
        self.__label = this_label

    @property
    def ground_truths(self) -> int:
        """
        Attribute to access the number of ground truths.

        Returns
        -------
        int
            The number of ground truths for this label.
        """
        return self.__ground_truths

    @ground_truths.setter
    def ground_truths(self, gts: int):
        """
        Sets the number of ground truths for this label.

        Parameters
        ----------
        int
            This is the number of ground truths for this label.
        """
        self.__ground_truths = gts

    def add_ground_truths(self, gts: int = 1):
        """
        Adds the number of existing ground truths.

        Parameters
        ----------
        int
            The number of ground truths to add.
        """
        self.__ground_truths += gts

    @property
    def predictions(self) -> int:
        """
        Attribute to access the number of predictions.

        Returns
        -------
        int
            The number of predictions for this label.
        """
        return self.__predictions

    @predictions.setter
    def predictions(self, prd: int):
        """
        Sets the number of predictions for this label.

        Parameters
        ----------
        prd: int
            This is the number of predictions for this label.
        """
        self.__predictions = prd

    def add_predictions(self, prd: int = 1):
        """
        Adds the number of existing predictions.

        Parameters
        ----------
        prd: int
            The number of predictions to add.
        """
        self.__predictions += prd


class DetectionLabelData(LabelData):
    """
    Acts a container that stores the total number of true positives,
    false positives, false negatives per label.

    Parameters
    ----------
    label: Union[str, int, np.integer]
        The unique string or integer index label to base the container.
    """

    def __init__(self, label: Union[str, int, np.integer]):
        super(DetectionLabelData, self).__init__(label)

        # Contains (IoU, score) values for predictions
        # marked as true positives.
        self.__tps = list()
        # Contains (IoU, score) values for predictions marked as
        # classification false positives.
        self.__class_fps = list()
        # Contains score values for predictions captured as
        # localization false positives.
        self.__local_fps = list()

    @property
    def tps(self) -> List[Tuple[float, float]]:
        """
        Attribute to access the true positives data.

        Returns
        -------
        List[Tuple[float, float]]
            This contains the (IoU, score) of each
            true positive for this label.
        """
        return self.__tps

    @tps.setter
    def tps(self, this_tps: List[Tuple[float, float]]):
        """
        Sets the true positives data to a new value.

        Parameters
        ----------
        this_tps: List[Tuple[float, float]]
            These are the true positives data to set.
        """
        self.__tps = this_tps

    def add_tp(self, iou: float, score: float):
        """
        Adds the true positive prediction IoU and confidence score.
        A true positive is when the prediction and the ground truth
        label matches and the IoU is greater than the set IoU threshold.

        Parameters
        ----------
        iou: float
            The IoU of the true positive prediction.
        score: float
            The confidence score of the true positive prediction.
        """
        self.__tps.append((clamp(iou), clamp(score)))

    def get_tp_scores(self, iou_threshold: float) -> np.ndarray:
        """
        Grabs the prediction scores marked as true positives.

        Parameters
        ----------
        iou_threshold: float
            The IoU threshold to consider true positives.

        Returns
        -------
        np.ndarray
            The true positive confidence scores.
        """
        if len(self.tps) > 0:
            tp_iou = np.array(self.tps)[:, 0] >= iou_threshold
            tp_scores = np.array(self.tps)[:, 1] * tp_iou
            return tp_scores[tp_scores != 0]
        return np.array([])

    def get_tp_iou(self, iou_threshold: float) -> np.ndarray:
        """
        Grabs the prediction IoUs marked as true positives.

        Parameters
        ----------
        iou_threshold: float
            The IoU threshold to consider true positives.

        Returns
        -------
        np.ndarray
            The true positive IoU values.
        """
        if len(self.tps) > 0:
            tp_iou = np.array(self.tps)[:, 0] >= iou_threshold
            tp_ious = np.array(self.tps)[:, 0] * tp_iou
            return tp_ious[tp_ious != 0]
        return np.array([])

    def get_tp_count(
        self,
        iou_threshold: float,
        score_threshold: float = 0.0
    ) -> int:
        """
        Grabs the number of true positives at the
        specified IoU threshold and score threshold.

        Parameters
        ----------
        iou_threshold: float
            The IoU threshold to filter the true positives.
        score_threshold: float
            The score threshold to filter the true positives.

        Returns
        -------
        int
            The number of true positives at the specified
            IoU and score threshold.
        """
        if len(self.tps) > 0:
            tp_iou = np.array(self.tps)[:, 0] >= iou_threshold
            tp_score = np.array(self.tps)[:, 1] >= score_threshold
            return np.count_nonzero(tp_iou * tp_score)
        return 0

    @property
    def class_fps(self) -> List[Tuple[float, float]]:
        """
        Attribute to access the classification false positives data.

        Returns
        -------
        List[Tuple[float, float]]
            This contains the (IoU, score) of each classification
            false positive for this label.
        """
        return self.__class_fps

    @class_fps.setter
    def class_fps(self, this_class_fps: List[Tuple[float, float]]):
        """
        Sets the classification false positives data to a new value.

        Parameters
        ----------
        this_class_fp: List[Tuple[float, float]]
            These are the classification false positives data to set.
        """
        self.__class_fps = this_class_fps

    def add_cfp(self, iou: float, score: float):
        """
        Adds the false positive (classification) prediction IoU
        and confidence score. A false positive (classification) is when
        the prediction and the ground truth labels don't match and the
        IoU is greater than the set IoU threshold.

        Parameters
        ----------
        iou: float
            The IoU of the classification false positive prediction.
        score: float
            The confidence score of the classification false
            positive prediction.
        """
        self.class_fps.append((clamp(iou), clamp(score)))

    def get_cfp_scores(self, iou_threshold: float) -> np.ndarray:
        """
        Grabs the prediction scores marked as classification false positives.

        Parameters
        ----------
        iou_threshold: float
            The IoU threshold to consider as classification
            false positives.

        Returns
        -------
        np.ndarray
            The classification false positive scores.
        """
        if len(self.class_fps) > 0:
            cfp_iou = np.array(self.class_fps)[:, 0] >= iou_threshold
            cfp_scores = np.array(self.class_fps)[:, 1] * cfp_iou
            return cfp_scores[cfp_scores != 0]
        return np.array([])

    def get_cfp_iou(self, iou_threshold: float) -> np.ndarray:
        """
        Grabs the prediction IoUs marked as classification false positives.

        Parameters
        ----------
        iou_threshold: float
            The IoU threshold to consider as classification
            false positives.

        Returns
        -------
        np.ndarray
            The classification false positive IoUs.
        """
        if len(self.class_fps) > 0:
            cfp_iou = np.array(self.class_fps)[:, 0] >= iou_threshold
            cfp_ious = np.array(self.class_fps)[:, 0] * cfp_iou
            return cfp_ious[cfp_ious != 0]
        return np.array([])

    def get_cfp_count(
        self,
        iou_threshold: float,
        score_threshold: float = 0.0
    ) -> int:
        """
        Grabs the number of classification false positives at
        the specified IoU and score threshold.

        Parameters
        ----------
        iou_threshold: float
            The IoU threshold to filter classification false positives.
        score_threshold: float
            The score threshold to filter classification false positives.

        Returns
        -------
        int
            The number of classification false positives at the
            specified IoU and score threshold.
        """
        if len(self.class_fps) > 0:
            fp_iou = np.array(self.class_fps)[:, 0] >= iou_threshold
            fp_score = np.array(self.class_fps)[:, 1] >= score_threshold
            return np.count_nonzero(fp_iou * fp_score)
        return 0

    @property
    def local_fps(self) -> List[float]:
        """
        Attribute to access the localization false positives data.

        Returns
        -------
        List[float]
            This contains the score of each localization
            false positive for this label.
        """
        return self.__local_fps

    @local_fps.setter
    def local_fps(self, this_local_fps: List[float]):
        """
        Sets the localization false positives data to a new value.

        Parameters
        ----------
        this_local_fps: List[float]
            These are localization false positives data to set.
        """
        self.__local_fps = this_local_fps

    def add_lfp(self, score: float):
        """
        Adds the number of localization false positive captured.
        A localization false positive is when there is a
        prediction but no ground truth.

        Parameters
        ----------
        score: float
            The confidence score of the localization
            false positive prediction.
        """
        self.local_fps.append(clamp(score))

    def get_lfp_iou(self, iou_threshold: float) -> np.ndarray:
        """
        Grabs the prediction IoUs marked as localization false positives.

        Parameters
        ----------
        iou_threshold: float
            The IoU threshold to consider as false positives.

        Returns
        -------
        np.ndarray
            The false positive IoU values.
        """
        local_fps = []
        if len(self.tps) > 0:
            # Any predictions that are below the IoU thresholds are
            # localization false positives.
            fp_iou = np.array(self.tps)[:, 0] < iou_threshold
            local_fps = np.array(self.tps)[:, 0] * fp_iou
            local_fps = local_fps[local_fps != 0]
            local_fps = local_fps.tolist()

        if len(self.class_fps) > 0:
            class_fp_iou = np.array(self.class_fps)[:, 0] < iou_threshold
            local_cfps = np.array(self.class_fps)[:, 0] * class_fp_iou
            local_cfps = local_cfps[local_cfps != 0]
            local_cfps = local_cfps.tolist()
            local_fps += local_cfps
        return np.array(local_fps)

    def get_lfp_scores(self, iou_threshold: float) -> np.ndarray:
        """
        Grabs the prediction scores marked as localization false positives.

        Parameters
        ----------
        iou_threshold: float
            The IoU threshold to consider true positives as
            localization false positives.

        Returns
        -------
        np.ndarray
            The localization false positive scores.
        """
        local_fps = []
        if len(self.tps) > 0:
            # Any predictions that are below the IoU thresholds are
            # localization false positives.
            fp_iou = np.array(self.tps)[:, 0] < iou_threshold
            local_fps = np.array(self.tps)[:, 1] * fp_iou
            local_fps = local_fps[local_fps != 0]
            local_fps = local_fps.tolist()

        if len(self.class_fps) > 0:
            class_fp_iou = np.array(self.class_fps)[:, 0] < iou_threshold
            local_cfps = np.array(self.class_fps)[:, 1] * class_fp_iou
            local_cfps = local_cfps[local_cfps != 0]
            local_cfps = local_cfps.tolist()
            local_fps += local_cfps

        if len(self.local_fps) > 0:
            local_fps += self.local_fps

        return np.array(local_fps)

    def get_lfp_count(
        self,
        iou_threshold: float,
        score_threshold: float = 0.0
    ) -> int:
        """
        Grabs the number of localization false positives at the specified IoU
        and score threshold. The IoU threshold is needed because true positives
        that have an IoU less than the set IoU threshold will be considered as
        localization false positives.

        Parameters
        ----------
        iou_threshold: float
            The IoU threshold to consider true positives as local
            false positives.
        score_threshold: float
            The score threshold to consider predictions.

        Returns
        -------
        int
            The number of localization false positives at the
            specified IoU and score threshold.
        """
        local_fp = 0
        if len(self.tps) > 0:
            # Any predictions that are below the IoU thresholds are
            # localization false positives.
            fp_iou = np.array(self.tps)[:, 0] < iou_threshold
            tp_score = np.array(self.tps)[:, 1] >= score_threshold
            local_fp += np.count_nonzero(fp_iou * tp_score)

        if len(self.class_fps) > 0:
            class_fp_iou = np.array(self.class_fps)[:, 0] < iou_threshold
            class_fp_score = np.array(self.class_fps)[:, 1] >= score_threshold
            local_fp += np.count_nonzero(class_fp_iou * class_fp_score)

        local_fp += np.count_nonzero(np.array(self.local_fps)
                                     >= score_threshold)
        return local_fp

    def get_fn_count(
        self,
        iou_threshold: float,
        score_threshold: float = 0.0
    ) -> int:
        """
        Grabs the number of false negatives at the specified IoU threshold
        and score threshold. Score threshold is needed because by principle
        fp = gt - tp, and score and IoU threshold is required to find the
        number of true positives.

        Parameters
        ----------
        iou_threshold: float
            The IoU threshold to consider true positives.
        score_threshold: float
            The score threshold to consider predictions.

        Returns
        -------
        int
            The number of false negatives at the specified
            IoU and score threshold.
        """
        return self.ground_truths - self.get_tp_count(
            iou_threshold, score_threshold)


class SegmentationLabelData(LabelData):
    """
    Acts a container that stores the total number of true predictions and
    false predictions for a specific label.

    Parameters
    ----------
    label: Union[str, int, np.integer]
        The unique string or integer index label to base the container.
    """

    def __init__(self, label: Union[str, int, np.integer]):
        super(SegmentationLabelData, self).__init__(label)

        # Total number of both ground truths and predictions of this label.
        self.__union = 0
        # Total number of true prediction pixels.
        self.__true_predictions = 0
        # Total number of false prediction pixels.
        self.__false_predictions = 0

    @property
    def union(self) -> int:
        """
        Attribute to access the number of union pixels.

        Returns
        -------
        int
            The number of union pixels for this label.
        """
        return self.__union

    @union.setter
    def union(self, uni: int):
        """
        Sets the number of union pixels for this label.
        Union pixels is the sum total of both ground truths and
        predictions for this label.

        Parameters
        ----------
        uni: int
            This is the number of union pixels for this label.
        """
        self.__union = uni

    def add_union(self, uni: int = 1):
        """
        Adds the number of existing union pixels.

        Parameters
        ----------
        uni: int
            The number of union pixels to add.
        """
        self.__union += uni

    @property
    def true_predictions(self) -> int:
        """
        Attribute to access the number of true predictions.

        Returns
        -------
        int
            The number of true predictions for this label.
        """
        return self.__true_predictions

    @true_predictions.setter
    def true_predictions(self, tps: int):
        """
        Sets the number of true predictions for this label.

        Parameters
        ----------
        tps: int
            This is the number of true predictions for this label.
        """
        self.__true_predictions = tps

    def add_true_predictions(self, tps: int = 1):
        """
        Adds the number of existing true predictions.

        Parameters
        ----------
        tps: int
            The number of true predictions to add.
        """
        self.__true_predictions += tps

    @property
    def false_predictions(self) -> int:
        """
        Attribute to access the number of false predictions.

        Returns
        -------
        int
            The number of false predictions for this label.
        """
        return self.__false_predictions

    @false_predictions.setter
    def false_predictions(self, fps: int):
        """
        Sets the number of false predictions for this label.

        Parameters
        ----------
        fps: int
            This is the number of false predictions for this label.
        """
        self.__false_predictions = fps

    def add_false_predictions(self, fps: int = 1):
        """
        Adds the number of existing false predictions.

        Parameters
        ----------
        fps: int
            The number of false predictions to add.
        """
        self.__false_predictions += fps
