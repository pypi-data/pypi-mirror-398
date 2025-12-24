"""
Implementations for the timing measurements used in validation.
"""

import time
from contextlib import contextmanager

import numpy as np


class TimerContext:
    """
    This class provides methods for timing measurements of the
    validation process and acts as a container of the measured timings.
    The stages of timings are as follows:

    * input => Image read and preprocessing
    * inference => Inference Timings
    * output => Output decoding and postprocessing
    """

    def __init__(self):
        self.stages = ["input", "inference", "output"]
        self.__timings = {stage: [] for stage in self.stages}
        self.__start_time = None
        self.to_ms = 1e3

    @contextmanager
    def time(self, stage: str):
        """
        Context manager to time a section
        and store duration in list.

        Parameters
        ----------
        stage: str
            The key to store the timing measurement
            for a specific stage such as "input", "inference",
            or "output".
        """
        self.__start_time = time.perf_counter()
        yield
        elapsed = time.perf_counter() - self.__start_time
        self.__timings[stage].append(elapsed * self.to_ms)
        self.__start_time = None

    def add_time(self, stage: str, ds_ms: float):
        """
        Add time to the last timining measurement
        of the current stage in the timings.

        Parameters
        ----------
        stage: str
            The key to store the timing measurement
            for a specific stage such as "input", "inference",
            or "output".
        ds_ms: float
            The time duration in milli seconds to add.
        """
        if len(self.__timings[stage]):
            self.__timings[stage][-1] += ds_ms

    def get_average_time(self, stage: str) -> float:
        """
        Returns the average time for the specific stage.

        Parameters
        ----------
        stage: str
            The key to fetch the timing measurements
            for a specific stage such as "input", "inference",
            or "output".

        Returns
        -------
        float
            The average timings for a given stage.
        """
        times = self.__timings.get(stage, [])
        return np.mean(times) if len(times) else 0.0

    def get_max_time(self, stage: str) -> float:
        """
        Returns the maximum time for the specific stage.

        Parameters
        ----------
        stage: str
            The key to fetch the timing measurements
            for a specific stage such as "input", "inference",
            or "output".

        Returns
        -------
        float
            The maximum timing for a given stage.
        """
        times = self.__timings.get(stage, [])
        return np.max(times) if len(times) else 0.0

    def get_min_time(self, stage: str) -> float:
        """
        Returns the minimum time for the specific stage.

        Parameters
        ----------
        stage: str
            The key to fetch the timing measurements
            for a specific stage such as "input", "inference",
            or "output".

        Returns
        -------
        float
            The minimum timing for a given stage.
        """
        times = self.__timings.get(stage, [])
        return np.min(times) if len(times) else 0.0

    def to_dict(self) -> dict:
        """
        Grabs the timing summary such as the average, max, min
        for each stages and stores it as a dictionary.
        """
        timings = {}
        for stage in ["input", "inference", "output"]:
            timings[f"min_{stage}_time"] = self.get_min_time(stage)
            timings[f"max_{stage}_time"] = self.get_max_time(stage)
            timings[f"avg_{stage}_time"] = self.get_average_time(stage)
        return timings

    def reset(self):
        """Clears all stored timings."""
        self.__timings = {stage: [] for stage in self.stages}
        self.__start_time = None
