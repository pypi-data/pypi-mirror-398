"""
Defines the ConsolePublisher class for printing validation metrics to the terminal.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Union

import polars as pl

from edgefirst.validator.publishers.utils.table import (segmentation_table,
                                                        multitask_table,
                                                        detection_table)
from edgefirst.validator.publishers.utils.logger import logger

if TYPE_CHECKING:
    from edgefirst.validator.evaluators import CombinedParameters
    from edgefirst.validator.metrics import Metrics, MultitaskMetrics


class ConsolePublisher:
    """
    Prints the metrics on the terminal.

    Parameters
    ----------
    save_path: str
        The path to save the metrics as a text file.
    """

    def __init__(self, save_path: str):
        self.save_path = save_path

    def __call__(
        self,
        metrics: Union[Metrics, MultitaskMetrics],
        parameters: CombinedParameters,
    ) -> str:
        """
        When this is called, it prints the metrics on the console.

        Parameters
        ----------
        metrics: Union[Metrics, MultitaskMetrics]
            This is the metrics computed during validation.
        parameters: CombinedParameters
            This contains the model, validation, and dataset parameters
            set from the command line.

        Returns
        -------
        str
            The formatted validation table showing the metrics, parameters,
            and model timings.
        """
        table = ""
        if parameters.model.common.with_boxes and parameters.model.common.with_masks:
            table = multitask_table(metrics, parameters)
        elif parameters.model.common.with_boxes:
            table = detection_table(metrics, parameters)
        elif parameters.model.common.with_masks:
            table = segmentation_table(metrics, parameters)

        if not parameters.validation.silent:
            print(table)
        return table

    def save_metrics(self, table: str):
        """
        Saves the validation metrics as a text file in disk.

        Parameters
        ----------
        table: str
            The validation metrics formatted as a table.
        """
        with open(os.path.join(self.save_path, 'metrics.txt'),
                  'w', encoding='utf-8') as fp:
            fp.write(table + '\n')
            fp.close()

    @staticmethod
    def save_csv_metrics(
        metrics: Union[Metrics, MultitaskMetrics],
        parameters: CombinedParameters
    ):
        """
        Save a CSV file containing the metrics for this validation
        session. If the file already exists, a new row is added to the
        contents.

        Detection metrics is currently only supported.

        Parameters
        ----------
        metrics: Union[Metrics, MultitaskMetrics]
            This is the metrics computed during validation.
        parameters: CombinedParameters
            This contains the model, validation, and dataset parameters
            set from the command line.
        """

        if parameters.model.common.with_masks:
            logger("CSV output is currently supported for detection metrics.",
                   code="WARNING")

        if parameters.model.common.with_boxes and parameters.model.common.with_masks:
            metrics = metrics.detection_metrics
        elif parameters.model.common.with_masks:
            return

        timings = metrics.timings

        if not os.path.exists(parameters.validation.csv_out):
            with open(parameters.validation.csv_out, "w", encoding='utf-8') as fp:
                fp.write(
                    "model,backend,nms,mAP@0.50,mAP@0.50-0.95,precision,"
                    "recall,f1,preprocess (ms),inference (ms),postprocess (ms)\n")
                fp.write(
                    f"{metrics.model},{parameters.dataset.common.backend},"
                    f"{parameters.model.nms},{metrics.precision['map'].get('0.50')},"
                    f"{metrics.precision['map'].get('0.50:0.95')},"
                    f"{metrics.precision['mean']},{metrics.recall['mean']},"
                    f"{metrics.f1['mean']},"
                    f"{timings.get('avg_input_time')},"
                    f"{timings.get('avg_inference_time')},"
                    f"{timings.get('avg_output_time')}\n"
                )
        else:
            # Load a CSV file with a semicolon separator and print the head
            df = pl.read_csv(parameters.validation.csv_out, separator=",")

            # New row to add
            session = pl.DataFrame({
                "model": [metrics.model],
                "backend": [parameters.dataset.common.backend],
                "nms": [parameters.model.nms],
                "mAP@0.50": [metrics.precision['map'].get('0.50')],
                "mAP@0.50-0.95": [metrics.precision['map'].get('0.50:0.95')],
                "precision": [metrics.precision['mean']],
                "recall": [metrics.recall['mean']],
                "f1": [metrics.f1['mean']],
                "preprocess (ms)": [timings.get('avg_input_time')],
                "inference (ms)": [timings.get('avg_inference_time')],
                "postprocess (ms)": [timings.get('avg_output_time')]
            })
            df = df.vstack(session)
            # Save the DataFrame to a new CSV file with a pipe separator and no
            # header
            df.write_csv(parameters.validation.csv_out,
                         separator=",", include_header=True)
