"""
Defines the model parameters used for running the model.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from edgefirst.validator.evaluators.parameters import Parameters
from edgefirst.validator.datasets.utils.annotation_transforms import clamp
from edgefirst.validator.publishers.utils.logger import logger

if TYPE_CHECKING:
    from edgefirst.validator.evaluators import CommonParameters


class ModelParameters(Parameters):
    """
    Container for model parameters used for running the model.

    Parameters
    ----------
    common_parameters: CommonParameters
        This represents the parameters that are common between
        model, dataset, and validation that should remain consistent across.
    model_path: str
        This is the path to the model file.
    iou_threshold: float
        The NMS IoU threshold. By default 0.60, which follows the
        default set in YOLOv5.
    score_threshold: float
        The NMS score threshold. By default 0.001, which follows the
        default set in YOLOv5.
    max_detections: float
        The NMS maximum number of detections. By default 300, which follows
        the default set in YOLOv5.
    engine: str
        The type of inference engine to deploy the model. Options could
        be one of the following: "cpu", "gpu", or a path to the NPU delegate
        on device such as "/usr/lib/libvx_delegate.so".
    nms: str
        The NMS algorithm to deploy. The default is the "numpy" NMS
        algorithm, a simple case, implemented using NumPy. Other variations
        include 'tensorflow' and 'torch'.
    box_format: str
        The output bounding box format of the model. Options could be one
        of the following: "xyxy" (PascalVOC), "xywh" (COCO), or "xcycwh" (YOLO).
    warmup: int
        The number of warmup iterations to deploy the model for more
        accurate timing benchmarks. Usually the first inferences takes some
        time to run.
    config_path: Optional[str]
        This is the path to the model metadata file in YAML format.
    labels_path: Optional[str]
        This is the path to a text file that contains all the unique string
        labels which is part of the model artifacts for converting model output
        indices into strings.
    labels: Optional[list]
        A list of unique string labels which is part of the model artifacts
        for converting model output indices into strings.
    label_offset: int
        This is the offset to map the integer labels to string labels.
    agnostic_nms: bool
        Specify whether to deploy class agnostic NMS or not. By default,
        class agnostic NMS is set to True.
    override: bool
        When set to True, override parameters set in the command line
        to use the model parameters defined in the model metadata file.
        By default, this is set to False.
    **kwargs: dict
        Define extra arguments as part of the model parameters.
    """

    def __init__(
        self,
        common_parameters: CommonParameters,
        model_path: str = "Model",
        iou_threshold: float = 0.60,
        score_threshold: float = 0.001,
        max_detections: int = 300,
        engine: str = "cpu",
        nms: str = "standard",
        box_format: str = "xyxy",
        warmup: int = 0,
        config_path: Optional[str] = None,
        labels_path: Optional[str] = None,
        labels: Optional[list] = None,
        label_offset: int = 0,
        agnostic_nms: bool = True,
        override: bool = False,
        **kwargs: dict
    ):
        super(ModelParameters, self).__init__(
            labels_path=labels_path,
            labels=labels,
            label_offset=label_offset,
            box_format=box_format,
        )

        self.common = common_parameters
        self.__model_path = model_path
        self.__iou_threshold = clamp(iou_threshold)
        self.__score_threshold = clamp(score_threshold)
        self.__max_detections = max_detections
        self.__engine = engine
        self.__nms = nms.lower()
        self.__warmup = warmup
        self.__config_path = config_path
        self.__agnostic_nms = agnostic_nms
        self.__override = override

    def check_nms_availability(self):
        """
        Checks the NMS library availability and falls back on any
        available NMS libraries starting from "hal" to "tensorflow" and then
        to "torch", and "numpy".
        """
        if self.nms == "hal":
            try:
                import edgefirst_hal  # type: ignore # pylint: disable=unused-import
            except ImportError:
                try:
                    import torch  # type: ignore # pylint: disable=unused-import
                    self.nms = "torch"
                    logger("HAL NMS is not available. Falling back to "
                           "Torch NMS.", code="WARNING")
                except ImportError:
                    try:
                        import tensorflow as tf  # type: ignore # pylint: disable=unused-import
                        self.nms = "tensorflow"
                        logger("HAL and Torch NMS are not available. "
                               "Falling back to TensorFlow NMS.", code="WARNING")
                    except ImportError:
                        self.nms = "numpy"
                        logger("HAL, Torch, and TensorFlow NMS are not "
                               "available. Falling back to NumPy NMS.",
                               code="WARNING")
        elif self.nms == "torch":
            try:
                import torch  # type: ignore # pylint: disable=unused-import
            except ImportError:
                try:
                    import tensorflow as tf  # type: ignore # pylint: disable=unused-import
                    self.nms = "tensorflow"
                    logger("Torch NMS is not available. Falling back to "
                           "TensorFlow NMS.", code="WARNING")
                except ImportError:
                    self.nms = "numpy"
                    logger("Torch and TensorFlow NMS are not available. "
                           "Falling back to NumPy NMS.", code="WARNING")
        elif self.nms == "tensorflow":
            try:
                import tensorflow as tf  # type: ignore # pylint: disable=unused-import
            except ImportError:
                self.nms = "numpy"
                logger("TensorFlow NMS is not available. Falling back to "
                       "NumPy NMS.", code="WARNING")

    @property
    def model_path(self) -> str:
        """
        Attribute to access the model_path.
        This is the path to the model file.

        Returns
        -------
        str
            The path to the model file.
        """
        return self.__model_path

    @model_path.setter
    def model_path(self, path: str):
        """
        Set the path to the model file.

        Parameters
        ----------
        path: str
            The path to the model file.
        """
        self.__model_path = path

    @property
    def iou_threshold(self) -> float:
        """
        Attribute to access the IoU threshold.
        This metric is used for the NMS.

        Returns
        -------
        float
            The IoU threshold.
        """
        return self.__iou_threshold

    @iou_threshold.setter
    def iou_threshold(self, iou: float):
        """
        Sets the IoU threshold.

        Parameters
        ----------
        iou: float
            The IoU threshold to set.
        """
        self.__iou_threshold = clamp(iou) if iou is not None else iou

    @property
    def score_threshold(self) -> float:
        """
        Attribute to access the score threshold.
        This metric is used for the NMS.

        Returns
        -------
        float
            The score threshold.
        """
        return self.__score_threshold

    @score_threshold.setter
    def score_threshold(self, score: float):
        """
        Sets the score threshold.

        Parameters
        ----------
        score: float
            The score threshold to set.
        """
        self.__score_threshold = clamp(score) if score is not None else score

    @property
    def max_detections(self) -> int:
        """
        Attribute to access the max detections.
        This metric is used for the NMS.

        Returns
        -------
        int
            The maximum detections.
        """
        return self.__max_detections

    @max_detections.setter
    def max_detections(self, this_max_detections: int):
        """
        Sets the maximum detections.

        Parameters
        ----------
        this_max_detections: int
            The max_detections to set.
        """
        self.__max_detections = this_max_detections

    @property
    def engine(self) -> str:
        """
        Attribute to access the type of inference engine.
        Options could be one of the following: "cpu", "gpu", or a
        path to the NPU delegate on device such as "/usr/lib/libvx_delegate.so".

        Returns
        -------
        str
            The inference engine.
        """
        return self.__engine

    @engine.setter
    def engine(self, this_engine: str):
        """
        Sets the engine type.

        Parameters
        ----------
        this_engine: str
            The inference engine to set.

        """
        self.__engine = this_engine

    @property
    def nms(self) -> str:
        """
        Attribute to access the NMS type.
        This metric is used to specify the NMS algorithm.

        Returns
        -------
        str
            The NMS type.
        """
        return self.__nms

    @nms.setter
    def nms(self, this_nms: str):
        """
        Sets the NMS type.

        Parameters
        ----------
        this_nms: str
            The NMS to set.
        """
        self.__nms = this_nms.lower() if this_nms is not None else this_nms

    @property
    def warmup(self) -> int:
        """
        Attribute to access the model warmup iterations.

        Returns
        -------
        int
            The number of warmup iterations to deploy the model.
        """
        return self.__warmup

    @warmup.setter
    def warmup(self, this_warmup: int):
        """
        Sets the number of model warmup iterations to deploy the model.

        Parameters
        ----------
        this_warmup: int
            The warmup to set.
        """
        self.__warmup = this_warmup

    @property
    def config_path(self) -> Optional[str]:
        """
        Attribute to access the config_path.
        This is the path to the model metadata file in YAML format.

        Returns
        -------
        Optional[str]
            The path to the model metadata file.
        """
        return self.__config_path

    @config_path.setter
    def config_path(self, path: str):
        """
        Set the path to the model metadata file in YAML format.

        Parameters
        ----------
        path: str
            The path to the model metadata file in YAML format.
        """
        self.__config_path = path

    @property
    def agnostic_nms(self) -> bool:
        """
        Attribute to access the agnostic NMS condition.

        Returns
        -------
        bool
            The agnostic NMS condition.
        """
        return self.__agnostic_nms

    @agnostic_nms.setter
    def agnostic_nms(self, agnostic: bool):
        """
        Sets the condition for the class agnostic NMS specification.

        Parameters
        ----------
        agnostic: bool
            The condition for the class agnostic NMS.
        """
        self.__agnostic_nms = agnostic

    @property
    def override(self) -> bool:
        """
        Attribute to access the override condition.

        Returns
        -------
        bool
            The override condition.
        """
        return self.__override

    @override.setter
    def override(self, condition: bool):
        """
        Sets the condition for overriding parameters set in the command line
        to use the model parameters defined in the model metadata file.

        Parameters
        ----------
        condition: bool
            The override condition.
        """
        self.__override = condition
