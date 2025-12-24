"""
Defines the parameter settings used for validation.
"""

import os
from typing import Optional, Union

from edgefirst.validator.datasets.utils.annotation_transforms import clamp
from edgefirst.validator.publishers.utils.logger import set_silent_condition


class ValidationParameters:
    """
    Container for validation parameters used for
    specifying additional settings for validation.

    Parameters
    ----------
    method: str
        Reproducing validation results reported by Ultralytics by default. Specify
        validation method seen in other sources such as YOLOv7. Options could
        be "ultralytics" for the official validator from Ultralytics which
        supports YOLOv5, YOLOv8, and YOLOv11. However, there are variations
        such as "yolov7" for YOLOv7 and "edgefirst" for internal Au-Zone implementations.
    metric: str
        The type of metric to use in the matching algorithm. Options could
        be one of the following: "iou" or "centerpoint". Using either the
        intersection over union with highest overlap as being the best matches
        or centerpoint distance with the closest distance being the best matches.
        Default is set to "iou".
    matching_leniency: int
        Distance metric to be considered a valid match when using the "centerpoint"
        metric. Default is 2 where the distance is no more than twice the
        size of the bounding box.
    clamp_boxes: Optional[int]
        Clamp bounding boxes for the minimum size as this value set. By default
        this setting is not specified.
    ignore_boxes: Optional[int]
        Ignore bounding boxes with sizes less than this value set. By default
        this setting is not specified.
    display: int
        Specify the limit of the number of visualization results to display.
        By default it is set to -1 which means all samples in the dataset.
    plots: bool
        Specify whether to save the validation plots. This is only effective
        when setting the visualization or the tensorboard parameters to a path.
        By default it is set to True which means to save the plots.
    silent: bool
        Specify whether to suppress validation updates on the terminal. This is
        useful when using the validator as an API to prevent any output messages.
    visualize: Optional[str]
        Specify the path to store the validation results in disk.
    tensorboard: Optional[str]
        Specify the path to output the tensorboard file for visualization
        using tensorboar.d
    json_out: Optional[str]
        Specify the path to output the JSON files storing the validation results.
    csv_out: Optional[str]
        Specify the path to output a CSV file containing the metrics. If the
        path already exists, then a new row is added to the contents of
        the CSV file.
    include_background: bool
        For segmentation validation, specifying to True includes the background
        class in the metrics which will ultimately increase the metric outcomes
        since most of the pixels in the image are from the background class.
    deploy_metrics: bool
        Also calculate deployment metrics to see how the model would
        perform at the optimal thresholds.
    **kwargs: dict
        Define extra arguments as part of the validation parameters.
    """

    def __init__(
        self,
        method: str = "ultralytics",
        metric: str = "iou",
        matching_leniency: int = 2,
        clamp_boxes: Optional[int] = None,
        ignore_boxes: Optional[int] = None,
        display: int = -1,
        plots: bool = True,
        silent: bool = False,
        visualize: Optional[str] = None,
        tensorboard: Optional[str] = None,
        json_out: Optional[str] = None,
        csv_out: Optional[str] = None,
        include_background: bool = False,
        deploy_metrics: bool = True,
        **kwargs: dict
    ):
        self.__method = method.lower()
        self.__metric = metric.lower()
        self.__matching_leniency = matching_leniency
        self.__clamp_boxes = clamp_boxes
        self.__ignore_boxes = ignore_boxes
        self.__display = display
        self.__plots = plots
        self.__silent = silent
        self.__visualize = visualize
        self.__tensorboard = tensorboard
        self.__json_out = json_out
        self.__csv_out = csv_out
        self.__include_background = include_background
        self.__deploy_metrics = deploy_metrics
        self.__iou_threshold = 0.50
        self.__score_threshold = 0.50
        self.__tp_iou = 0.50

        if visualize:
            os.makedirs(visualize, exist_ok=True)

        if tensorboard:
            os.makedirs(tensorboard, exist_ok=True)

        if json_out:
            os.makedirs(json_out, exist_ok=True)

        if csv_out:
            dir_path = os.path.dirname(csv_out)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)

    @property
    def method(self) -> str:
        """
        Attribute to access validation methods.
        Specifies the validation method to
        reproduce in EdgeFirst Validator. By default the "ultralytics" methods
        seen in YOLOv5, YOLOv8, and YOLOv11 are used. However, other variations
        such as "yolov7" from YOLOv7 and "edgefirst" for internal Au-Zone
        implementations are also possible.
        """
        return self.__method

    @method.setter
    def method(self, methods: str):
        """
        Sets the validation method.

        Parameters
        ----------
        methods: str
            The validation method to reproduce.
            Options include "ultralytics", "yolov7", or "edgefirst".
        """
        self.__method = methods.lower() if methods is not None else methods

    @property
    def metric(self) -> str:
        """
        Attribute to access the metric type.
        This parameter is used to define which metric ("iou", "centerpoint")
        to use to match the predictions to ground truth.

        Returns
        -------
        str
            The metric type.
        """
        return self.__metric

    @metric.setter
    def metric(self, this_metric: str):
        """
        Sets the metric type.

        Parameters
        ----------
        this_metric: str
            The metric to set.
        """
        self.__metric = (this_metric.lower() if
                         this_metric is not None else this_metric)

    @property
    def matching_leniency(self) -> int:
        """
        Attribute to access the leniency factor
        for center distance calculations.

        Returns
        -------
        int
            The leniency factor. This is a criteria to consider
            center distances if the number of times the diagonal
            (center to corner) of the smallest bounding box fits within the
            box to box center distance does not exceed the leniency factor.

        """
        return self.__matching_leniency

    @matching_leniency.setter
    def matching_leniency(self, leniency_factor: int):
        """
        Sets the leniency factor. This is a criteria to consider
        center distances if the number of times the diagonal
        (center to corner) of the smallest bounding box fits within the
        box to box center distance does not exceed the leniency factor.

        Parameters
        ----------
        leniency_factor: int
            The leniency_factor to set.
        """
        self.__matching_leniency = leniency_factor

    @property
    def clamp_boxes(self) -> Union[int, None]:
        """
        Attribute to access clamp boxes.
        This is used to specify the lowest limit for the
        box dimensions in pixels. Any box dimensions (height or width)
        lower than this setting will be resized to this setting.

        Returns
        -------
        Union[int, None]
            The pixel dimension to clamp.
        """
        return self.__clamp_boxes

    @clamp_boxes.setter
    def clamp_boxes(self, this_clamp_boxes: Union[int, None]):
        """
        Sets the clamp boxes.

        Parameters
        ----------
        this_clamp_boxes: Union[int, None]
            The clamp_boxes to set.
        """
        self.__clamp_boxes = this_clamp_boxes

    @property
    def ignore_boxes(self) -> Union[int, None]:
        """
        Attribute to access ignore boxes.
        Any box dimension (width or height) lower than this limit
        will be ignored from validation.

        Returns
        -------
        Union[int, None]
            The pixel dimension to ignore.
        """
        return self.__ignore_boxes

    @ignore_boxes.setter
    def ignore_boxes(self, this_ignore_boxes: int):
        """
        Sets the ignore boxes.

        Parameters
        ----------
        this_ignore_boxes: int
            The ignore_boxes to set.
        """
        self.__ignore_boxes = this_ignore_boxes

    @property
    def display(self) -> int:
        """
        Attribute to access display.
        Set the number of images to display showing results for validation.

        Returns
        -------
        int
            The number of images to display.
        """
        return self.__display

    @display.setter
    def display(self, this_display: int):
        """
        Sets the number of images to display.

        Parameters
        ----------
        this_display: int
            The display to set.
        """
        self.__display = this_display

    @property
    def plots(self) -> bool:
        """
        Attribute to access plots.
        Specify whether to draw validation plots or not.
        Validation plots include: Confusion Matrix, PR-curve, and
        classification histogram.

        Returns
        -------
        bool
            Condition to include plots.
        """
        return self.__plots

    @plots.setter
    def plots(self, this_plots: bool):
        """
        Specify to include validation plots.

        Parameters
        ----------
        this_plots: bool
            The plots to set.
        """
        self.__plots = this_plots

    @property
    def silent(self) -> bool:
        """
        Attribute to access the display flag.
        This is a flag to determine whether messages
        are printed to console. Does not print when silent is True.

        Returns
        -------
        bool
            Condition to disable validation logging.
        """
        return self.__silent

    @silent.setter
    def silent(self, silent: bool):
        """
        Sets a flag to determine whether messages are printed to console.
        Does not print when silent is True.

        Parameters
        ----------
        silent: bool
            This is the condition to disable validation logging.
        """
        self.__silent = silent
        set_silent_condition(silent)

    @property
    def visualize(self) -> Union[str, None]:
        """
        Attribute to access the visualize.
        This is the path to store the validation results which
        includes images.

        Returns
        -------
        Union[str, None]
            The path to save validation results.
        """
        return self.__visualize

    @visualize.setter
    def visualize(self, this_visualize: Union[str, None]):
        """
        Sets the path to save the validation results in disk.

        Parameters
        ----------
        this_visualize: Union[str, None]
            The visualize to set.
        """
        if this_visualize is not None:
            os.makedirs(this_visualize, exist_ok=True)
        self.__visualize = this_visualize

    @property
    def tensorboard(self) -> Union[str, None]:
        """
        Attribute to access the tensorboard.
        This is the path to store the validation results which includes
        tfevent files to be loaded using tensorboard.

        Returns
        -------
        Union[str, None]
            The path to save validation results.
        """
        return self.__tensorboard

    @tensorboard.setter
    def tensorboard(self, this_tensorboard: Union[str, None]):
        """
        Sets the path to save the validation results in a tfevents file.

        Parameters
        ----------
        this_tensorboard: Union[str, None]
            The tensorboard to set.
        """
        if this_tensorboard is not None:
            os.makedirs(this_tensorboard, exist_ok=True)
        self.__tensorboard = this_tensorboard

    @property
    def json_out(self) -> Union[str, None]:
        """
        Attribute to access the json_out.
        This is the path to save the JSON files containing
        validation metrics and raw data to draw the plots.

        Returns
        -------
        Union[str, None]
            The path to save JSON files.
        """
        return self.__json_out

    @json_out.setter
    def json_out(self, this_json_out: Union[str, None]):
        """
        Sets the path to save the JSON files in disk.

        Parameters
        ----------
        this_json_out: Union[str, None]
            The path to the JSON files to set.
        """
        if this_json_out is not None:
            os.makedirs(this_json_out, exist_ok=True)
        self.__json_out = this_json_out

    @property
    def csv_out(self) -> Union[str, None]:
        """
        Attribute to access the csv_out.
        This is the path to save the metrics as a CSV.

        Returns
        -------
        Union[str, None]
            The path to save the CSV file containing the metrics.
        """
        return self.__csv_out

    @csv_out.setter
    def csv_out(self, csv: Union[str, None]):
        """
        Sets the path to save the CSV file in disk

        Parameters
        ----------
        csv: Union[str, None]
            The path to the CSV file containing the metrics.
            If the file exists, then a new row is added to
            the existing contents. Otherwise a new file is created.
        """
        if csv is not None:
            dir_path = os.path.dirname(csv)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
        self.__csv_out = csv

    @property
    def include_background(self) -> bool:
        """
        Attribute to access include_background.
        Specify whether to include background as
        part of segmentation validation.

        Returns
        -------
        bool
            Condition to include background for segmentation validation.
        """
        return self.__include_background

    @include_background.setter
    def include_background(self, this_include_background: bool):
        """
        Specify to include background class for segmentation validation.

        Parameters
        ----------
        this_include_background: bool
            The include_background to set.
        """
        self.__include_background = this_include_background

    @property
    def deploy_metrics(self) -> bool:
        """
        Attribute to access the deploy metrics.

        Returns
        -------
        bool
            The condition to include the calculation
            of the deployment metrics.
        """
        return self.__deploy_metrics

    @deploy_metrics.setter
    def deploy_metrics(self, deploy: bool):
        """
        Set the deploy metrics condition. When specified
        to True deployment metrics are calculated based on the
        optimal thresholds found.

        Parameters
        ----------
        deploy: bool
            The condition to set.
        """
        self.__deploy_metrics = deploy

    @property
    def iou_threshold(self) -> float:
        """
        Attribute to access the optimal IoU threshold.
        This threshold is calculated based on the highest ground truth
        bounding box intersections which indicates that bounding boxes will
        be considered a duplicate if the IoU is larger than this threshold.

        Returns
        -------
        float:
             The optimal IoU threshold for NMS.
        """
        return self.__iou_threshold

    @iou_threshold.setter
    def iou_threshold(self, iou: float):
        """
        Sets the optimal IoU threshold for NMS.

        Parameters
        ----------
        iou: float
            The optimal IoU threshold to set.
        """
        self.__iou_threshold = clamp(iou)

    @property
    def score_threshold(self) -> float:
        """
        Attribute to access the optimal score threshold.
        This score threshold is calculated based on the threshold
        that yields the maximum F1 score.

        Returns
        -------
        float:
            The optimal score threshold.
        """
        return self.__score_threshold

    @score_threshold.setter
    def score_threshold(self, score: float):
        """
        Sets the optimal score threshold for NMS.

        Parameters
        ----------
        iou: float
            The optimal score threshold to set.
        """
        self.__score_threshold = clamp(score)

    @property
    def tp_iou(self) -> float:
        """
        Attribute to access the TP IoU threshold.
        This metric is used to classify matched detections as either
        true positives or false positives. Detections with IoUs below this
        threshold will be classified as localization false positives.

        Returns
        -------
        float:
             The validation IoU threshold.
        """
        return self.__tp_iou

    @tp_iou.setter
    def tp_iou(self, iou: float):
        """
        Sets the validation IoU threshold.

        Parameters
        ----------
        iou: float
            The validation IoU threshold to set.
        """
        self.__tp_iou = clamp(iou)
