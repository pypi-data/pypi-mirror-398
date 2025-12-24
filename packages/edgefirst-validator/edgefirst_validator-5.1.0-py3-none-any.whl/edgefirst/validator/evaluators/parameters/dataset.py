"""
Defines the dataset parameters used for reading, fetching, and processing the dataset.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, List

from edgefirst.validator.evaluators.parameters import Parameters

if TYPE_CHECKING:
    from edgefirst.validator.evaluators import CommonParameters


class DatasetParameters(Parameters):
    """
    Container for dataset parameters used for reading and fetching
    the validation dataset.

    Parameters
    ----------
    common_parameters: CommonParameters
        This represents the parameters that are common between
        model, dataset, and validation that should remain consistent across.
    dataset_path: str
        This is the path to the dataset directory or file (YAML or cache file).
    show_missing_annotations: bool
        Specify to print on the terminal the images without any ground truth
        annotations. Default to False.
    normalized: bool
        Specify whether the ground truth annotations are normalized to the
        image dimensions or not. Default to True.
    box_format: str
        The output bounding box format of the model. Options could be one
        of the following: "xyxy" (PascalVOC), "xywh" (COCO), or "xcycwh" (YOLO).
    labels_path: Optional[str]
        This is the path to a text file that contains all the unique string
        labels which is part of the model artifacts for converting model output
        indices into strings.
    labels: Optional[List[str]]
        A list of unique string labels which is part of the model artifacts
        for converting model output indices into strings.
    label_offset: int
        This is the offset to map the integer labels to string labels.
    silent: bool
        Specify whether to suppress validation updates on the terminal. This is
        useful when using the validator as an API to prevent any output messages.
    cache: bool
        Specify to cache the dataset which preprocesses images with resizing,
        letterbox, or padding transformations and other specifications such as
        to YUYV or RGBA and stores these transformed assets inside an LMDB cache.
        Defaults to False, but if this is True, the preprocessing steps
        in the Runner will be skipped as it is already done in the dataset.
    **kwargs: dict
        Define extra arguments as part of the dataset parameters.
    """

    def __init__(
        self,
        common_parameters: CommonParameters,
        dataset_path: str = "Dataset",
        show_missing_annotations: bool = False,
        normalized: bool = True,
        box_format: str = "xyxy",
        labels_path: Optional[str] = None,
        labels: Optional[List[str]] = None,
        label_offset: int = 0,
        silent: bool = False,
        cache: bool = False,
        **kwargs: dict
    ):
        super(DatasetParameters, self).__init__(
            labels_path=labels_path,
            labels=labels,
            label_offset=label_offset,
            box_format=box_format,
        )

        self.common = common_parameters
        self.__dataset_path = dataset_path
        self.__show_missing_annotations = show_missing_annotations
        self.__normalized = normalized
        self.__silent = silent
        self.__cache = cache
        self.__visualize = False

    @property
    def dataset_path(self) -> str:
        """
        Attribute to access the dataset_path.
        This is the path to the dataset directory or a dataset.yaml file.

        Returns
        -------
        str
            The path to the dataset.
        """
        return self.__dataset_path

    @dataset_path.setter
    def dataset_path(self, path: str):
        """
        Set the path to the dataset.

        Parameters
        ----------
        path: str
            The path to the dataset directory or dataset.yaml file.
        """
        self.__dataset_path = path

    @property
    def show_missing_annotations(self) -> bool:
        """
        Attribute to access show_missing_annotations.
        Specify whether to print on the terminal the images without
        any ground truth annotations. By default set to False.

        Returns
        -------
        bool
            Condition for printing the images without any
            ground truth annotations. .
        """
        return self.__show_missing_annotations

    @show_missing_annotations.setter
    def show_missing_annotations(self, show: bool):
        """
        Specify condition for printing the images without
        any ground truth annotations.

        Parameters
        ----------
        show: bool
            The condition to set.
        """
        self.__show_missing_annotations = show

    @property
    def normalized(self) -> bool:
        """
        Attribute to access normalized.
        Specify whether the ground truth annotations are
        normalized to the image dimensions. Default to True.

        Returns
        -------
        bool
            Condition for printing the images without any
            ground truth annotations. .
        """
        return self.__normalized

    @normalized.setter
    def normalized(self, normalize: bool):
        """
        Specify condition of whether or not the ground truth
        annotations are normalized to the image dimensions.

        Parameters
        ----------
        normalize: bool
            The condition to set.
        """
        self.__normalized = normalize

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

    @property
    def cache(self) -> bool:
        """
        Attribute to access the cache condition.
        This specifies whether or not to cache the dataset. Caching
        the dataset includes preprocessing the images and annotations
        to run only once during the validation sessions to speed up the process.

        Returns
        -------
        bool
            Condition to cache the dataset.
        """
        return self.__cache

    @cache.setter
    def cache(self, to_cache: bool):
        """
        Sets the caching condition.

        Parameters
        ----------
        to_cache: bool
            The condition for cache to set.
        """
        self.__cache = to_cache

    @property
    def visualize(self) -> bool:
        """
        Attribute to access the visualize property.

        Returns
        -------
        bool
            If this is set to True, image copy
            is performed during the preprocess
            to save the image with letterbox or resizing
            transformations.
        """
        return self.__visualize

    @visualize.setter
    def visualize(self, visual: bool):
        """
        Sets the visualize parameter.

        Parameters
        -----------
        visual: bool
            The visualize condition to set.
        """
        self.__visualize = visual
