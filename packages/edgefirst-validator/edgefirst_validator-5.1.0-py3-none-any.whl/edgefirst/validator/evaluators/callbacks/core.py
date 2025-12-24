"""
Implementation of callback classes for validation stages.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from edgefirst.validator.publishers import StudioPublisher
    from edgefirst.validator.evaluators import CombinedParameters, StageTracker


class Callback(object):
    """
    A class to handle callback functions during validation.
    Callbacks are used to communicate the progress of the stages
    to EdgeFirst Studio.

    Parameters
    -----------
    studio_publisher: StudioPublisher
        Publishes metrics, timings, plots, and
        progress to EdgeFirst Studio.
    parameters: CombinedParameters
        These are the model, dataset, and validation parameters
        set from the command line.
    stage_tracker: StageTracker
        Tracks the current stage of validation.
    """

    def __init__(
        self,
        studio_publisher: StudioPublisher,
        parameters: CombinedParameters,
        stage_tracker: StageTracker
    ):
        self.studio_publisher = studio_publisher
        self.parameters = parameters
        self.stage_tracker = stage_tracker

    def on_test_begin(self, logs=None):
        """
        Called at the beginning of the test.

        Parameters
        ----------
        logs: dict
            A dictionary containing logs related to the test (default is None).
        """
        return

    def on_test_batch_begin(self, step: int, logs=None):
        """
        Called at the beginning of each test batch.

        Parameters
        ----------
        step : int
            The index of the current test batch.
        logs : dict, optional
            A dictionary containing logs related
            to the test batch (default is None).
        """
        return

    def on_test_batch_end(self, step: int, logs=None):
        """
        Called at the end of each test batch.

        Parameters
        ----------
        step : int
            The index of the current test batch.
        logs : dict, optional
            A dictionary containing logs related
            to the test batch (default is None).
        """
        return

    def on_test_error(self, step: int, error, logs=None):
        """
        Called when the callback raises an error.

        Parameters
        ----------
        step : int
            The index of the current test batch.
        error: Exception
            The error exception.
        logs : dict, optional
            A dictionary containing logs related
            to the test batch (default is None).
        """
        return

    def on_test_end(self, logs=None):
        """
        Called at the end of the test.

        Parameters
        ----------
        logs : dict, optional
            A dictionary containing logs related to the test (default is None).
        """
        return


class CallbacksList(object):
    """
    A list of callbacks that can be triggered during the validation process.

    Parameters
    ----------
    callbacks : List[Callback], optional
        A list of callback objects to be triggered
        during the testing process (default is None).
    """

    def __init__(
        self,
        callbacks: List[Callback] = None
    ):
        self.callbacks = callbacks if callbacks else []

    def on_test_begin(self, logs=None):
        """
        Triggers the `on_test_begin` method of each callback in the list.

        Parameters
        ----------
        logs: dict
            A dictionary containing logs related to the test (default is None).
        """
        for callback in self.callbacks:
            callback.on_test_begin(logs)

    def on_test_batch_begin(self, step: int, logs=None):
        """
        Triggers the `on_test_batch_begin` method of each callback in the list.

        Parameters
        ----------
        step : int
            The index of the current test batch.
        logs : dict, optional
            A dictionary containing logs related
            to the test batch (default is None).
        """
        for callback in self.callbacks:
            callback.on_test_batch_begin(step, logs)

    def on_test_batch_end(self, step: int, logs=None):
        """
        Triggers the `on_test_batch_end` method of each callback in the list.

        Parameters
        ----------
        step : int
            The index of the current test batch.
        logs : dict, optional
            A dictionary containing logs related
            to the test batch (default is None).
        """
        for callback in self.callbacks:
            callback.on_test_batch_end(step, logs)

    def on_test_error(self, step: int, error, logs=None):
        """
        Triggers the `on_test_error` method of each callback in the list.

        Parameters
        ----------
        step : int
            The index of the current test batch.
        error: Exception
            The error exception.
        logs : dict, optional
            A dictionary containing logs related
            to the test batch (default is None).
        """
        for callback in self.callbacks:
            callback.on_test_error(step, error, logs)

    def on_test_end(self, logs=None):
        """
        Triggers the `on_test_end` method of each callback in the list.

        Parameters
        ----------
        logs : dict, optional
            A dictionary containing logs related to the test (default is None).
        """
        for callback in self.callbacks:
            callback.on_test_end(logs)
