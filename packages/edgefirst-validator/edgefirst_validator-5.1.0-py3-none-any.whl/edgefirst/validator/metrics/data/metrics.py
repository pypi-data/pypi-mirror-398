"""
Defines the container for the validation metrics.
"""

from typing import Union


class Metrics:
    """
    Container used to store the validation metrics of the model.

    Parameters
    ----------
    model: str
        The path or name of the model.
    dataset: str
        The path or name of the validation dataset.
    """

    def __init__(
        self,
        model: str = "Model",
        dataset: str = "Dataset",
    ):
        self.__model = model
        self.__dataset = dataset
        self.__save_path = None
        self.reset()

    @property
    def model(self) -> str:
        """
        Attribute to access the model path/name.

        Returns
        -------
        str
            The model path/name.
        """
        return self.__model

    @model.setter
    def model(self, model_path: str):
        """
        Sets the model path/name.

        Parameters
        ----------
        model_path: str
            The model path/name.
        """
        self.__model = model_path

    @property
    def dataset(self) -> str:
        """
        Attribute to access the dataset path/name.

        Returns
        -------
        str
            The dataset path/name.
        """
        return self.__dataset

    @dataset.setter
    def dataset(self, dataset_path: str):
        """
        Sets the dataset path/name.

        Parameters
        ----------
        dataset_path: str
            The dataset path/name
        """
        self.__dataset = dataset_path

    @property
    def save_path(self) -> str:
        """
        Attribute to access the path to save the results.

        Returns
        -------
        str
            The path to save the results.
        """
        return self.__save_path

    @save_path.setter
    def save_path(self, this_save_path: str):
        """
        Sets the path to save the results.

        Parameters
        ----------
        this_save_path: str
            The path to save the results
        """
        self.__save_path = this_save_path

    @property
    def ground_truths(self) -> int:
        """
        Attribute to access the number of ground truths.

        Returns
        -------
        int
            The number of ground truths in the dataset.
        """
        return self.__ground_truths

    @ground_truths.setter
    def ground_truths(self, gts: int):
        """
        Sets the number of ground truths in the dataset.

        Parameters
        ----------
        gts: int
            This is the number of ground truths in the dataset.
        """
        self.__ground_truths = gts

    def add_ground_truths(self, gts: int):
        """
        Adds the number of existing ground truths.

        Parameters
        ----------
        gts: int
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
            The total number of predictions.
        """
        return self.__predictions

    @predictions.setter
    def predictions(self, prd: int):
        """
        Sets the total number of predictions.

        Parameters
        ----------
        prd: int
            This is the total number of predictions.
        """
        self.__predictions = prd

    def add_predictions(self, prd: int):
        """
        Adds the number of existing predictions.

        Parameters
        ----------
        prd: int
            The number of predictions to add.
        """
        self.__predictions += prd

    @property
    def tp(self) -> int:
        """
        Attribute to access the number of true positives.

        Returns
        -------
        int
            The total number of true positives.
        """
        return self.__tp

    @tp.setter
    def tp(self, tps: int):
        """
        Sets the total number of true positives.

        Parameters
        ----------
        tps: int
            This is the total number of true positives.
        """
        self.__tp = tps

    @property
    def fn(self) -> int:
        """
        Attribute to access the number of false negatives.

        Returns
        -------
        int
            The total number of false negatives.
        """
        self.__fn = self.ground_truths - (self.tp + self.cfp)
        return self.__fn

    @fn.setter
    def fn(self, fns: int):
        """
        Sets the total number of false negatives.

        Parameters
        ----------
        fns: int
            This is the total number of false negatives.
        """
        self.__fn = fns

    @property
    def cfp(self) -> int:
        """
        Attribute to access the number of classification false positives.

        Returns
        -------
        int
            The total number of classification false positives.
        """
        return self.__cfp

    @cfp.setter
    def cfp(self, fps: int):
        """
        Sets the total number of classification false positives.

        Parameters
        ----------
        fps: int
            This is the total number of classification false positives.
        """
        self.__cfp = fps

    @property
    def lfp(self) -> int:
        """
        Attribute to access the number of localization false positives.

        Returns
        -------
        int
            The total number of localization false positives.
        """
        return self.__lfp

    @lfp.setter
    def lfp(self, fps: int):
        """
        Sets the total number of localization false positives.

        Parameters
        ----------
        fps: int
            This is the total number of localization false positives.
        """
        self.__lfp = fps

    @property
    def precision(self) -> dict:
        """
        Attribute to access the precision metric.

        Returns
        -------
        dict:
            The precision scores which contains "overall", "mean", and
            "map" keys.
        """
        return self.__precision

    @precision.setter
    def precision(self, this_precision: dict):
        """
        Sets the precision metric.

        Parameters
        ----------
        this_precision: dict
            The precision dictionary to set which contains
            the keys "overall", "mean", and "map".
        """
        self.__precision = this_precision

    @property
    def recall(self) -> dict:
        """
        Attribute to access the recall metric.

        Returns
        -------
        dict
            The recall scores which contains keys "overall", "mean", and "mar".
        """
        return self.__recall

    @recall.setter
    def recall(self, this_recall: dict):
        """
        Sets the recall metric.

        Parameters
        ----------
        this_recall: dict
            The recall to set which contains keys "overall", "mean", and "mar".
        """
        self.__recall = this_recall

    @property
    def accuracy(self) -> dict:
        """
        Attribute to access the accuracy metric.

        Returns
        -------
        dict
            The accuracy to set which contains keys "overall", "mean", and "macc".
        """
        return self.__accuracy

    @accuracy.setter
    def accuracy(self, this_accuracy: dict):
        """
        Sets the accuracy metric.

        Parameters
        ----------
        this_accuracy: dict
            The accuracy to set which contains keys: "overall", "mean", "macc".
        """
        self.__accuracy = this_accuracy

    @property
    def f1(self) -> dict:
        """
        Attribute to access the F1 metric.

        Returns
        -------
        dict
            The F1 to set which contains keys: "overall", "mean", "mf1".
        """
        return self.__f1

    @f1.setter
    def f1(self, this_f1: dict):
        """
        Sets the F1 metric.

        Parameters
        ----------
        this_f1: dict
            The F1 to set which contains keys: "overall", "mean", "mf1".
        """
        self.__f1 = this_f1

    @property
    def iou(self) -> dict:
        """
        Attribute to access the IoU metric.

        Returns
        -------
        dict
            The IoU to set which contains keys: "overall", "mean".
        """
        return self.__iou

    @iou.setter
    def iou(self, this_iou: dict):
        """
        Sets the IoU metric.

        Parameters
        ----------
        this_iou: dict
            The IoU to set which contains keys: "overall", "mean".
        """
        self.__iou = this_iou

    @property
    def true_predictions(self) -> int:
        """
        Attribute to access the total number of true predictions.

        Returns
        -------
        int
            The total number of true predictions for segmentation.
        """
        return self.__true_predictions

    @true_predictions.setter
    def true_predictions(self, tps: int):
        """
        Sets the total number of true predictions for segmentation.

        Parameters
        ----------
        tps: int
            This is the total number of true predictions for segmentation.
        """
        self.__true_predictions = tps

    def add_true_predictions(self, tps: int = 1):
        """
        Adds the number of true predictions for segmentation.

        Parameters
        ----------
        tps: int
            The number of true predictions to add for segmentation.
        """
        self.__true_predictions += tps

    @property
    def false_predictions(self) -> int:
        """
        Attribute to access the total number of false
        predictions for segmentation.

        Returns
        -------
        int
            The total number of false predictions for segmentation.
        """
        return self.__false_predictions

    @false_predictions.setter
    def false_predictions(self, fps: int):
        """
        Sets the total total number of false predictions for segmentation.

        Parameters
        ----------
        fps: int
            This is the total number of false prediction for segmentation.
        """
        self.__false_predictions = fps

    def add_false_predictions(self, fps: int = 1):
        """
        Adds the number of false predictions for segmentation.

        Parameters
        ----------
        fps: int
            The number of false predictions to add for segmentation.
        """
        self.__false_predictions += fps

    @property
    def union(self) -> int:
        """
        Attribute to access the number of union pixels.

        Returns
        -------
        int
            The number of ground truths and prediction pixels for the dataset.
        """
        return self.__union

    @union.setter
    def union(self, uni: int):
        """
        Sets the number of ground truths and
        prediction pixels for the dataset.

        Parameters
        ----------
        uni: int
            This is the number of union for this dataset.
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
    def timings(self) -> dict:
        """
        Attribute to access the model timings.

        Returns
        -------
        dict
            The model timings.
        """
        return self.__timings

    @timings.setter
    def timings(self, this_timings: Union[dict, None]):
        """
        Sets the timings of the model.

        Parameters
        ----------
        this_timings: Union[dict, None]
            The model timings.
        """
        self.__timings = this_timings

    def reset(self):
        """
        Resets the data for the metrics to the default state.
        """
        self.__ground_truths = 0
        # This is used for segmentation to contain
        # total number of prediction pixels.
        self.__predictions = 0

        # Detection Metrics
        self.__tp = 0   # True Positives
        self.__fn = 0   # False Negatives
        self.__cfp = 0  # Classification False Positives
        self.__lfp = 0  # Localization False Positives

        self.__precision = {
            "overall": 0,
            # Storing YOLO mean precision or segmentation precision here.
            "mean": 0,  # Mean Precision
            "map": {
                "0.50": 0,
                "0.75": 0,
                "0.50:0.95": 0,
            },
            "class": 0  # Mean Class Precision
        }

        self.__recall = {
            "overall": 0,
            "mean": 0,  # Storing YOLO mean recall or segmentation recall here.
            "mar": {
                "0.50": 0,
                "0.75": 0,
                "0.50:0.95": 0,
            },
            "class": 0  # Mean Class Recall
        }

        self.__accuracy = {
            "overall": 0,
            "mean": 0,  # Storing segmentation accuracy here.
            "macc": {
                "0.50": 0,
                "0.75": 0,
                "0.50:0.95": 0,
            },
            "class": 0  # Mean Class Accuracy
        }

        self.__f1 = {
            "overall": 0,
            "mean": 0,  # Storing YOLO mean F1 score.
            "maf1": {
                "0.50": 0,
                "0.75": 0,
                "0.50:0.95": 0,
            }
        }

        self.__iou = {
            "overall": 0,
            "mean": 0
        }

        # Segmentation Metrics
        self.__true_predictions = 0
        self.__false_predictions = 0
        self.__union = 0

        self.__timings = {
            'min_read_time': 0,
            'max_read_time': 0,
            'min_load_time': 0,
            'max_load_time': 0,
            'min_backbone_time': 0,
            'max_backbone_time': 0,
            'min_decode_time': 0,
            'max_decode_time': 0,
            'min_box_time': 0,
            'max_box_time': 0,
            'avg_read_time': 0,
            'avg_load_time': 0,
            'avg_backbone_time': 0,
            'avg_decode_time': 0,
            'avg_box_time': 0,
        }

    def to_dict(
        self,
        with_boxes: bool = True,
    ) -> dict:
        """
        Convert the metrics container into a dictionary.

        Parameters
        ----------
        with_boxes: bool
            If this is set to True, the dictionary
            will only contain bounding box metrics.
            If set to False, the dictionary
            will contain segmentation metrics.

        Returns
        -------
        dict
            The metrics as a dictionary.
        """
        metrics = dict()

        if with_boxes:
            metrics["ground_truth"] = self.ground_truths
            metrics["true_positives"] = self.tp
            metrics["false_negatives"] = self.fn
            metrics["classification_false_positives"] = self.cfp
            metrics["localization_false_positives"] = self.lfp
            metrics["precision"] = self.precision
            metrics["recall"] = self.recall
            metrics["accuracy"] = self.accuracy
            metrics["F1"] = self.f1
        else:
            metrics["ground_truth"] = self.ground_truths
            metrics["true_predictions"] = self.true_predictions
            metrics["false_predictions"] = self.false_predictions
            metrics["union"] = self.union
            metrics["precision"] = {k: v for k, v in self.precision.items()
                                    if k not in ["map", "class"]}
            metrics["recall"] = {k: v for k, v in self.recall.items()
                                 if k not in ["mar", "class"]}
            metrics["accuracy"] = {k: v for k, v in self.accuracy.items()
                                   if k not in ["macc", "class"]}
            metrics["F1"] = {k: v for k, v in self.f1.items()
                             if k not in ["mean", "maf1"]}
            metrics["iou"] = {k: v for k, v in self.iou.items()
                              if k != "overall"}
        metrics["timings"] = self.timings
        return metrics


class MultitaskMetrics:
    """
    Container for Multitask validation metrics
    for segmentation and detection.

    Parameters
    ----------
    detection_metrics: Metrics
        A container for detection metrics.
    segmentation_metrics: Metrics
        A container for segmentation metrics.
    """

    def __init__(
        self,
        detection_metrics: Metrics,
        segmentation_metrics: Metrics
    ):
        self.detection_metrics = detection_metrics
        self.segmentation_metrics = segmentation_metrics

        self.__timings = {
            'min_read_time': 0,
            'max_read_time': 0,
            'min_load_time': 0,
            'max_load_time': 0,
            'min_backbone_time': 0,
            'max_backbone_time': 0,
            'min_decode_time': 0,
            'max_decode_time': 0,
            'min_box_time': 0,
            'max_box_time': 0,
            'avg_read_time': 0,
            'avg_load_time': 0,
            'avg_backbone_time': 0,
            'avg_decode_time': 0,
            'avg_box_time': 0,
        }

    @property
    def timings(self) -> dict:
        """
        Attribute to access the model timings.

        Returns
        -------
        dict
            The model timings.
        """
        return self.__timings

    @timings.setter
    def timings(self, this_timings: Union[dict, None]):
        """
        Sets the timings of the model.

        Parameters
        ----------
        this_timings: Union[dict, None]
            The model timings.
        """
        self.__timings = this_timings

    def to_dict(self) -> dict:
        """
        Conver the metrics container into a dictionary.

        Returns
        -------
        dict
            The metrics as a dictionary.
        """

        metrics = {}
        detection = self.detection_metrics.to_dict(with_boxes=True)
        detection.pop("timings")

        segmentation = self.segmentation_metrics.to_dict(with_boxes=False)
        segmentation.pop("timings")

        metrics["detection_metrics"] = detection
        metrics["segmentation_metrics"] = segmentation
        metrics["timings"] = self.timings
        return metrics
