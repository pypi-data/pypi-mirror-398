"""
Defines the StudioPublisher class for publishing validation plots and metrics
to EdgeFirst Studio.
"""

import os
import glob
import json
from typing import Union

from edgefirst_client import Client  # pylint: disable=no-name-in-module


class StudioPublisher:
    """
    Publishes the plots to EdgeFirst Studio.

    Parameters
    ----------
    json_path: str
        The path to store the ApexCharts JSON files.
    session_id: Union[int, str]
        The validation session ID in EdgeFirst Studio.
    client: Client
        The client interface to post requests to
        the EdgeFirst Studio API.
    """

    def __init__(
        self,
        json_path: str,
        session_id: Union[int, str],
        client: Client
    ):
        self.json_path = json_path
        self.session_id = session_id
        self.client = client
        try:
            self.session = self.client.validation_session(
                session_id=session_id)
        except RuntimeError as e:
            if "no rows" in str(e):
                raise PermissionError(
                    f"Could not find session {session_id}. " +
                    "Login with the right server `edgefirst-client --server <server> login` " +
                    "or set the user credentials using " +
                    "`--server=<server> --username=<username> --password=<password>`."
                ) from e
            elif "EmptyToken" in str(e):
                raise PermissionError(
                    "Could not find EdgeFirst Studio token. Try to login using " +
                    "`edgefirst-client login` or provide user credentials using " +
                    "`--server=<server> --username=<username> --password=<password>`."
                ) from e
            elif "MaxRetriesExceeded" in str(e):
                raise ValueError(
                    f"Got an invalid URL: {client.url}. " +
                    "Check that the right server is set. Otherwise, verify " +
                    f"that {session_id} is a valid validation ID."
                ) from e
            raise e

    def update_stage(
        self,
        stage: str,
        status: str,
        message: str,
        percentage: int
    ):
        """
        Sets the stage reported in EdgeFirst Studio.

        Parameters
        ----------
        stage: str
            This is the current stage of the progress.
        status: str
            The status of the runtime. This can be set to
            'complete', 'error', or 'running'.
        message: str
            Any message for more description on the stage.
        percentage: int
            The percentage of the stage with a total of 100.
        """
        self.client.update_stage(
            task_id=self.session.task.id,
            stage=stage,
            status=status,
            message=message,
            percentage=percentage
        )

    def save_json(self, filename: str, plot: dict):
        """
        Save the JSON file containing data
        for the validation plots.

        Parameters
        ----------
        filename: str
            The name of the file.
        plot: dict
            The dictionary with the data
            for the plots.
        """
        with open(os.path.join(self.json_path, filename),
                  'w', encoding='utf-8') as fp:
            json.dump(plot, fp)

    def post_plots(self):
        """
        Post the JSON files with the validation metrics
        to EdgeFirst Studio.
        """

        files = glob.glob(os.path.join(self.json_path, "*.json"))
        files = [(os.path.basename(file), file) for file in files]

        self.session.upload(files)

    def post_metrics(self, metrics: dict):
        """
        Post the final metrics reported in validator.

        Parameters
        ----------
        metrics: dict
            This is a container for the metrics.
        """
        self.session.set_metrics(metrics)
