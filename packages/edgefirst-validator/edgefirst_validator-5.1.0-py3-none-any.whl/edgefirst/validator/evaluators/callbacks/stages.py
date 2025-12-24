"""
Implementation for the callback that manages stages of the validation process.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generator, Iterable, Optional, Union, Tuple, List

from tqdm import tqdm

if TYPE_CHECKING:
    from edgefirst.validator.publishers import StudioPublisher


class StageTracker:
    """
    Class to manage and display different stages of the validation process.
    """

    def __init__(self, studio_publisher: StudioPublisher = None):
        self.studio_publisher = studio_publisher
        self.stages = {
            "stage_fetch_im": "Download Validation Images",
            "stage_fetch_as": "Download Image Annotations",
            "stage_validate": "Start Inference Validation",
            "stage_vmetrics": "Compute Validation Metrics",
            "stage_optimals": "Compute Optimal Thresholds",
            "stage_dmetrics": "Compute Deployment Metrics",
            "stage_vfigures": "Compute Validation Figures",
        }
        self.current_stage = "stage_fetch_im"

    def add_stage(self, stage: Tuple[str, str], index: Optional[int] = None):
        """
        Adds a new stage to the stages list.

        Parameters
        ----------
        stage_name: str
            The name of the stage.
        index: Optional[int]
            The index to insert the stage at. If None, appends to the end.
        """
        if index is not None:
            stages = list(self.stages.items())
            stages.insert(index, stage)
            self.stages = dict(stages)
        else:
            self.stages[stage[0]] = stage[1]

    def get_stage(self, stage_name: str) -> Tuple[str, str]:
        """
        Retrieves the description of a stage by its name.

        Parameters
        ----------
        stage_name: str
            The name of the stage.

        Returns
        -------
        Tuple[str, str]
            The description of the stage.
        """
        return (stage_name, self.stages.get(stage_name, "Stage not found."))

    def set_stage(self, stage_name: str):
        """
        Sets the current stage.

        Parameters
        ----------
        stage_name: str
            The name of the stage to set as current.

        Raises
        -------
        ValueError
            If the stage name is not found in the stages.
        """
        if stage_name in self.stages.keys():  # pylint: disable=consider-iterating-dictionary
            self.current_stage = stage_name
        else:
            raise ValueError(f"Stage '{stage_name}' not found in stages.")

    def current(self) -> Tuple[str, str]:
        """
        Returns the current stage.

        Returns
        -------
        tuple[str, str]
            The current stage name and description.
        """
        return (self.current_stage, self.stages[self.current_stage])

    def tolist(self) -> List[Tuple[str, str]]:
        """
        Returns the stages as a list of tuples.

        Returns
        -------
        list[tuple[str, str]]
            The list of stages.
        """
        return list(self.stages.items())

    def display_stages(self):
        """
        Displays all the stages in order.
        """
        for stage_name, description in self.stages.items():
            print(f"Stage: {stage_name} - {description}")

    def stage_iterator(
            self, iterable: Iterable, stage_name: str, **tqdm_kwargs) -> tqdm:
        """
        Wrap an iterable with tqdm using the current stage description.

        Parameters
        ----------
        iterable: Iterable
            The iterable to wrap.
        stage_name: str
            The name of the stage to set as current.
        tqdm_kwargs: dict
            Additional keyword arguments for tqdm.

        Returns
        -------
        tqdm.tqdm
            The tqdm-wrapped iterable.
        """
        self.current_stage = stage_name
        return tqdm(iterable, desc=self.stages[stage_name], **tqdm_kwargs)

    def stage_generator(
        self,
        generator: Union[Generator, List],
        stage_name: str,
        **tqdm_kwargs
    ) -> Generator:
        """
        Wrap a generator with tqdm using the current stage description.

        Parameters
        ----------
        generator: Generator
            The generator to wrap.
        stage_name: str
            The name of the stage to set as current.
        tqdm_kwargs: dict
            Additional keyword arguments for tqdm.

        Returns
        -------
        Generator
            The tqdm-wrapped generator.
        """
        self.current_stage = stage_name
        samples = tqdm(generator, desc=self.stages[stage_name], **tqdm_kwargs)
        total = len(samples)
        for sample in samples:
            if self.studio_publisher is not None:
                percentage = round(
                    (samples.n / total) * 100) if total > 0 else 0
                if percentage % 5 == 0:
                    self.studio_publisher.update_stage(
                        stage=stage_name,
                        status="in_progress",
                        message=self.stages[stage_name],
                        percentage=percentage
                    )
            yield sample
