"""
Implementation for the callback that generates plots for EdgeFirst Studio.
"""

from __future__ import annotations

import collections.abc
from typing import TYPE_CHECKING, Optional

import numpy as np

from edgefirst.validator.evaluators.callbacks import Callback
from edgefirst.validator.datasets.utils.annotation_transforms import convert_to_serializable

if TYPE_CHECKING:
    from edgefirst.validator.evaluators import CombinedParameters, StageTracker
    from edgefirst.validator.publishers import StudioPublisher
    from edgefirst.validator.metrics import Metrics, Plots


class PlotsCallback(Callback):
    """
    Generates the plots compatible for ApexCharts
    and saves as JSON files to be published to EdgeFirst Studio.

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
        super(PlotsCallback, self).__init__(studio_publisher=studio_publisher,
                                            parameters=parameters,
                                            stage_tracker=stage_tracker)

    def create_apexchart_bar(
        self,
        series: list,
        title: str,
        categories: list,
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
        enabled_labels: bool = True
    ) -> dict:
        """
        Create a bar chart config dictionary for ApexCharts.

        Parameters
        ----------
        series : list
            Data series for the bar chart.
        title : str
            Title of the chart.
        categories : list
            X-axis categories.
        xlabel : Optional[str]
            Label for the x-axis.
        ylabel : Optional[str]
            Label for the y-axis.
        enabled_labels : bool, default=True
            Whether to show data labels.

        Returns
        -------
        dict
            Configuration dictionary for an ApexCharts bar chart.
        """
        chart = {
            "series": series,
            "chart": {"type": "bar"},
            "title": {"text": title},
            "dataLabels": {
                "enabled": enabled_labels,
                "style": {
                    "colors": ['#000000']
                },
            },
        }

        if xlabel is not None:
            chart["xaxis"] = {
                "categories": categories,
                "title": {
                    "text": xlabel
                }
            }
        else:
            chart["xaxis"] = {"categories": categories}

        if ylabel is not None:
            chart["yaxis"] = {
                "title": {
                    "text": ylabel
                }
            }
        return chart

    def create_apexchart_pie(
        self,
        series: list,
        title: str,
        categories: list
    ) -> dict:
        """
        Creates a pie chart config dictionary for ApexCharts.

        Parameters
        ----------
        series: list
            A list of values to display as a pie chart. These
            values will automatically be converted into percentages.
        title: str
            Specify the title for the chart.
        categories: list
            Specify the categories for each value in the series.

        Returns
        -------
        dict
            Configuration dictionary for an ApexCharts pie chart.
        """
        chart = {
            "series": series,
            "chart": {"type": "pie"},
            "title": {"text": title},
            "labels": categories,
        }
        return chart

    def create_apexchart_grid(
        self,
        data: dict,
        labels: list,
        title: str
    ) -> dict:
        """
        Create a heatmap chart config for ApexCharts from grid data.

        Parameters
        ----------
        data : dict
            Mapping of label to data rows (2D array-like).
        labels : list
            Class labels for axes.
        title : str
            Title of the chart.

        Returns
        -------
        dict
            Configuration dictionary for an ApexCharts heatmap chart.
        """
        chart = {
            "series": [{"name": label, "data": row.tolist()}
                       for row, label in zip(data, labels)],
            "chart": {"type": "heatmap"},
            "xaxis": {
                "categories": labels,
                "title": {"text": "Ground Truth"}
            },
            "yaxis": {
                "categories": labels,
                "title": {"text": "Predictions"}
            },
            "title": {"text": title}
        }

        return chart

    def create_apexchart_lines(
        self,
        x: np.ndarray,
        data: np.ndarray,
        labels: list,
        title: str,
        xlabel: str = "Recall",
        ylabel: str = "Precision"
    ) -> dict:
        """
        Create a line chart config for precision-recall visualization.

        Parameters
        ----------
        x : np.ndarray
            X-axis values (e.g., recall).
        data : np.ndarray
            Y-axis values (e.g., precision) per label.
        labels : list
            List of label names for the lines.
        title : str
            Title of the chart.
        xlabel : str
            The x-axis label.
        ylabel : str
            The y-axis label.

        Returns
        -------
        dict
            Configuration dictionary for an ApexCharts line chart.
        """
        lines = []
        labels = labels.tolist() if isinstance(labels, np.ndarray) else labels
        if len(x):
            for i, row in enumerate(data):
                if isinstance(row, collections.abc.Iterable):
                    lines.append({
                        "name": labels[i],
                        "data": np.concatenate([np.round(x[:, None], 2),
                                                np.round(row[:, None], 2)],
                                               axis=1).tolist()
                    })

        chart = {
            "series": lines,
            "chart": {"type": "line"},
            "xaxis": {
                "type": "numeric",
                "title": {"text": xlabel},
                "min": 0.0,
                "max": 1.0
            },
            "yaxis": {
                "type": "numeric",
                "title": {"text": ylabel},
                "min": 0.0,
                "max": 1.0
            },
            "title": {"text": title}
        }

        return chart

    def create_apexchart_radar(
        self,
        series: list,
        title: str,
        categories: list
    ) -> dict:
        """
        Create a radar chart config dictionary for ApexCharts.

        Parameters
        ----------
        series : list
            Data series for the radar chart.
        title : str
            Title of the chart.
        categories : list
            Categories for the radar axes.

        Returns
        -------
        dict
            Configuration dictionary for an ApexCharts radar chart.
        """
        chart = {
            "series": series,
            "chart": {"type": "radar"},
            "title": {"text": title},
            "labels": categories,
        }
        return chart

    def create_apexchart_box(
        self,
        series: list,
        title: str,
    ) -> dict:
        """
        Create a box plot chart config dictionary for ApexCharts.

        Parameters
        ----------
        series : list
            Data series for the box plot chart.
        title : str
            Title of the chart.

        Returns
        -------
        dict
            Configuration dictionary for an ApexCharts box plot chart.
        """
        chart = {
            "series": series,
            "chart": {"type": "boxPlot"},
            "title": {"text": title},
            "xaxis": {
                "type": "category",
                "categories": ["IoU Threshold", "Score Threshold"]
            }
        }
        return chart

    def create_apexchart_radialbar(
        self,
        series: list,
        title: str,
        categories: list
    ) -> dict:
        """
        Create a radial bar chart config dictionary for ApexCharts.

        Parameters
        ----------
        series : list
            Data series for the radial bar chart.
        title : str
            Title of the chart.
        categories : list
            Categories for the radial bars.

        Returns
        -------
        dict
            Configuration dictionary for an ApexCharts radial bar chart.
        """
        chart = {
            "series": series,
            "chart": {"type": "radialBar", "height": 350},
            "plotOptions": {
                "radialBar": {
                    "dataLabels": {
                        "name": {"show": True},
                        "value": {"show": True},
                    },
                    "distributed": True,  # multiple bars
                    "startAngle": 0,
                    "endAngle": 360,
                }
            },
            "labels": categories,
            "colors": ["#1ab7ea", "#ff4560"],
            "title": {"text": title},
            "legend": {          # show legend for all categories
                "show": True,
                "position": "bottom",
                "horizontalAlign": "center",
                "floating": False,
                "labels": {"useSeriesColors": True}
            },
            # Important: tooltip will always show 0 if you enable it
            "tooltip": {
                "enabled": True,
            }
        }
        return chart

    def save_detection_metrics(self, metrics: Metrics, plots: Plots):
        """
        Save detection charts and metrics as ApexChart JSON files.

        Order of plots:
        1. Optimal NMS Thresholds - Box Plot
        2. mAP - Bar Chart
        3. Detection Metrics - Radar Plot
        4. Deployment Classifications - Bar Chart
        5. Confusion Matrix - Heatmap
        6. Precision vs. Recall Curve - Line Chart
        7. F1 vs. Confidence Curve - Line Chart
        8. Precision vs. Confidence Curve - Line Chart
        9. Recall vs. Confidence Curve - Line Chart
        10. Class Histogram - Bar Chart
        11. TP and FP Scores Histogram - Bar Chart
        12. TP and FP IoUs Histogram - Bar Chart

        Parameters
        ----------
        metrics : Metrics
            Detection evaluation metrics.
        plots : Plots
            Curves and confusion matrix data for plotting.
        """

        # Save Optimal NMS Thresholds - Box Plot
        series = [round(self.parameters.validation.iou_threshold * 100, 3),
                  round(self.parameters.validation.score_threshold * 100, 3)]
        chart = self.create_apexchart_radialbar(
            series=series,
            title="Optimal NMS Thresholds [Detection]",
            categories=["IoU Threshold", "Score Threshold"]
        )
        self.studio_publisher.save_json(
            filename="a_optimal_nms_thresholds.json",
            plot=chart
        )

        # Save mAP - Bar Chart
        categories = ["mAP@0.50", "mAP@0.75", "mAP@0.50:0.95"]
        series = [{"name": "Score",
                   "data": [round(metrics.precision["map"]["0.50"], 4),
                            round(metrics.precision["map"]["0.75"], 4),
                            round(metrics.precision["map"]["0.50:0.95"], 4)]}]
        chart = self.create_apexchart_bar(
            series=series,
            title="Mean Average Precision [Detection]",
            categories=categories
        )
        self.studio_publisher.save_json(
            filename="da_detection_mean_average_precision.json",
            plot=chart
        )

        # Save Detection Metrics - Radar Plot
        categories = ["mAP@0.50-0.95", "Mean F1", "Mean Precision",
                      "Mean Recall", "Deployment Class Accuracy",
                      "Deployment Class Precision", "Deployment Class Recall"]
        series = [{"name": "Radar Series 1",
                   "data": [round(metrics.precision["map"]["0.50:0.95"], 4),
                            round(metrics.f1["mean"], 4),
                            round(metrics.precision["mean"], 4),
                            round(metrics.recall["mean"], 4),
                            round(metrics.accuracy["class"], 4),
                            round(metrics.precision["class"], 4),
                            round(metrics.recall["class"], 4)]}]
        chart = self.create_apexchart_radar(
            series=series,
            title="Detection Metrics",
            categories=categories
        )
        self.studio_publisher.save_json(
            filename="db_detection_metrics.json",
            plot=chart
        )

        # Save Deployment Classifications - Bar Chart
        categories = ["Ground Truths", "True Positives", "False Negatives",
                      "Classification False Positives",
                      "Localization False Positives"]
        series = [{"data": [metrics.ground_truths,
                            metrics.tp,
                            metrics.fn,
                            metrics.cfp,
                            metrics.lfp]}]
        chart = self.create_apexchart_bar(
            series=series,
            title="Deployment Classifications",
            categories=categories
        )
        self.studio_publisher.save_json(
            filename="dc_deployment_classifications.json",
            plot=chart
        )

        # Save Confusion Matrix - Heatmap
        chart = self.create_apexchart_grid(plots.confusion_matrix.matrix,
                                           plots.confusion_matrix.labels,
                                           title="Confusion Matrix [Detection]")
        self.studio_publisher.save_json(
            filename="dd_detection_confusion_matrix.json",
            plot=chart
        )

        # Save Precision vs. Recall Curve - Line Chart
        precision = plots.py
        recall = plots.px

        x = np.linspace(0.0, 1.0, recall.shape[0])
        x_downsampled = np.linspace(0.0, 1.0, 100)
        r_downsampled = np.interp(x_downsampled, x, recall)
        p_downsampled = []

        for p in precision:
            p = np.interp(x_downsampled, x, p)
            p_downsampled.append(p)

        p_downsampled = np.array(p_downsampled)

        chart = self.create_apexchart_lines(
            r_downsampled,
            p_downsampled,
            plots.curve_labels,
            title="Precision vs. Recall [Detection]"
        )

        p_mean = p_downsampled.mean(0) if len(p_downsampled) else None
        if p_mean is not None:
            chart["series"].append({
                "name": "all classes",
                "data": np.concatenate(
                    [np.round(r_downsampled[:, None], 2),
                     np.round(p_mean[:, None], 2)], axis=1).tolist()
            })

        self.studio_publisher.save_json(
            filename="de_detection_precision_recall.json",
            plot=chart
        )

        # Save F1 Curve - Line Chart
        f1_downsampled = []
        for f1 in plots.f1:
            f1 = np.interp(x_downsampled, x, f1)
            f1_downsampled.append(f1)
        f1_downsampled = np.array(f1_downsampled)

        chart = self.create_apexchart_lines(
            r_downsampled,
            f1_downsampled,
            plots.curve_labels,
            title="F1 vs. Confidence [Detection]",
            xlabel="Confidence",
            ylabel="F1"
        )
        self.studio_publisher.save_json(
            filename="df_detection_f1_curve.json",
            plot=chart
        )

        # Save Precision Curve - Line Chart
        precision_downsampled = []
        for p in plots.precision:
            p = np.interp(x_downsampled, x, p)
            precision_downsampled.append(p)
        precision_downsampled = np.array(precision_downsampled)

        chart = self.create_apexchart_lines(
            r_downsampled,
            precision_downsampled,
            plots.curve_labels,
            title="Precision vs. Confidence [Detection]",
            xlabel="Confidence",
        )
        self.studio_publisher.save_json(
            filename="dg_detection_precision_curve.json",
            plot=chart
        )

        # Save Recall Curve - Line Chart
        recall_downsampled = []
        for r in plots.recall:
            r = np.interp(x_downsampled, x, r)
            recall_downsampled.append(r)
        recall_downsampled = np.array(recall_downsampled)

        chart = self.create_apexchart_lines(
            r_downsampled,
            recall_downsampled,
            plots.curve_labels,
            title="Recall vs. Confidence [Detection]",
            xlabel="Confidence",
            ylabel="Recall"
        )
        self.studio_publisher.save_json(
            filename="dh_detection_recall_curve.json",
            plot=chart
        )

        # Save Class Histogram - Bar Chart
        if len(plots.class_histogram_data.keys()) > 1:
            # Only save this chart if there are multiple classes.
            series = []
            categories = ["accuracy", "precision", "recall"]
            for key, item in plots.class_histogram_data.items():
                series.append({"data": [round(item.get('accuracy', 0), 4),
                                        round(item.get('precision', 0), 4),
                                        round(item.get('recall', 0), 4),
                                        ], "name": key})

            chart = self.create_apexchart_bar(
                series=series,
                title="Class Metrics @ Optimal Thresholds[Detection]",
                categories=categories,
                enabled_labels=False
            )
            self.studio_publisher.save_json(
                filename="di_detection_class_metrics.json",
                plot=chart
            )

        # Save TP and FP scores Histogram - Bar Chart
        bins = np.arange(0, 1.05, 0.05)  # 0.0 to 1.0 with step 0.05
        tp_scores = np.concatenate(plots.tp_scores, axis=0)
        fp_scores = np.concatenate(plots.fp_scores, axis=0)

        tp_hist, _ = np.histogram(tp_scores, bins=bins)
        fp_hist, _ = np.histogram(fp_scores, bins=bins)

        # Convert bin ranges to readable category labels
        categories = [
            f"{bins[i]:.2f}-{bins[i+1]:.2f}" for i in range(len(bins) - 1)]

        series = [
            {
                "name": "True Positives",
                "data": tp_hist.tolist(),
                "color": "#00FF00"  # Green
            },
            {
                "name": "False Positives",
                "data": fp_hist.tolist(),
                "color": "#FF0000"  # Red
            }
        ]

        chart = self.create_apexchart_bar(
            series=series,
            title="Histogram of True Positive vs False Positive Scores",
            categories=categories,
            xlabel="Score",
            ylabel="Count",
            enabled_labels=True
        )

        self.studio_publisher.save_json(
            filename="dj_tp_fp_scores.json",
            plot=chart
        )

        # Save TP and FP IoU Histogram - Bar Chart
        tp_ious = np.concatenate(plots.tp_ious, axis=0)
        fp_ious = np.concatenate(plots.fp_ious, axis=0)

        tp_hist, _ = np.histogram(tp_ious, bins=bins)
        fp_hist, _ = np.histogram(fp_ious, bins=bins)

        series = [
            {
                "name": "True Positives",
                "data": tp_hist.tolist(),
                "color": "#00FF00"  # Green
            },
            {
                "name": "False Positives",
                "data": fp_hist.tolist(),
                "color": "#FF0000"  # Red
            }
        ]

        chart = self.create_apexchart_bar(
            series=series,
            title="Histogram of True Positive vs False Positive IoUs",
            categories=categories,
            xlabel="IoU",
            ylabel="Count",
            enabled_labels=True
        )

        self.studio_publisher.save_json(
            filename="dk_tp_fp_ious.json",
            plot=chart
        )

    def save_segmentation_metrics(self, metrics: Metrics, plots: Plots):
        """
        Save segmentation metrics and class-wise histogram charts.

        Instance Segmentation Order of Plots:
        1. mAP - Bar Chart
        2. Instance Segmentation Metrics - Radar Plot
        3. Precision vs. Recall Curve - Line Chart
        4. F1 vs. Confidence Curve - Line Chart
        5. Precision vs. Confidence Curve - Line Chart
        6. Recall vs. Confidence Curve - Line Chart

        Parameters
        ----------
        metrics : Metrics
            Segmentation evaluation metrics.
        plots : Plots
            Class histogram and plot data.
        """
        if self.parameters.model.common.semantic:
            # Save Semantic Segmentation Metrics - Radar Plot
            categories = ["Accuracy", "F1", "Mean IoU",
                          "Mean Precision", "Mean Recall"]
            series = [{"name": "Radar Series 1",
                       "data": [round(metrics.accuracy["overall"], 4),
                                round(metrics.f1["overall"], 4),
                                round(metrics.iou["mean"], 4),
                                round(metrics.precision["mean"], 4),
                                round(metrics.recall["mean"], 4)]}]
            chart = self.create_apexchart_radar(
                series=series,
                title="Semantic Segmentation Metrics",
                categories=categories
            )
            self.studio_publisher.save_json(
                filename="sa_semantic_segmentation_metrics.json",
                plot=chart
            )

            # Save Class Histogram - Bar Chart
            if len(plots.class_histogram_data.keys()) > 1:
                # Only save this chart if there are multiple classes.
                categories = ["accuracy", "precision", "recall"]
                series = []
                for key, item in plots.class_histogram_data.items():
                    series.append({"data": [round(item.get('accuracy', 0), 4),
                                            round(item.get('precision', 0), 4),
                                            round(item.get('recall', 0), 4),
                                            ], "name": key})

                chart = self.create_apexchart_bar(
                    series=series,
                    title="Segmentation Class Metrics",
                    categories=categories,
                    enabled_labels=False
                )
                self.studio_publisher.save_json(
                    filename="sb_segmentation_class_metrics.json",
                    plot=chart
                )

        # Instance Segmentation
        else:
            # Save mAP - Bar Chart
            categories = ["mAP@0.50", "mAP@0.75", "mAP@0.50:0.95"]
            series = [{"name": "Score",
                       "data": [round(metrics.precision["map"]["0.50"], 4),
                                round(metrics.precision["map"]["0.75"], 4),
                                round(metrics.precision["map"]["0.50:0.95"], 4)]}]
            chart = self.create_apexchart_bar(
                series=series,
                title="Mean Average Precision [Segmentation]",
                categories=categories
            )
            self.studio_publisher.save_json(
                filename="sa_segmentation_mean_average_precision.json",
                plot=chart
            )

            # Save Instance Segmentation Metrics - Radar Plot
            categories = ["mAP@0.50-0.95", "Mean F1",
                          "Mean Precision", "Mean Recall"]
            series = [{"name": "Radar Series 1",
                       "data": [round(metrics.precision["map"]["0.50:0.95"], 4),
                                round(metrics.f1["mean"], 4),
                                round(metrics.precision["mean"], 4),
                                round(metrics.recall["mean"], 4)]}]
            chart = self.create_apexchart_radar(
                series=series,
                title="Instance Segmentation Metrics",
                categories=categories
            )
            self.studio_publisher.save_json(
                filename="sb_instance_segmentation_metrics.json",
                plot=chart
            )

            # Save Precision vs. Recall Curve - Line Chart
            precision = plots.py
            recall = plots.px

            x = np.linspace(0.0, 1.0, recall.shape[0])
            x_downsampled = np.linspace(0.0, 1.0, 100)
            if len(recall):
                r_downsampled = np.interp(x_downsampled, x, recall)
            else:
                r_downsampled = []
            p_downsampled = []

            for p in precision:
                p = np.interp(x_downsampled, x, p)
                p_downsampled.append(p)

            p_downsampled = np.array(p_downsampled)

            chart = self.create_apexchart_lines(
                r_downsampled,
                p_downsampled,
                plots.curve_labels,
                title="Precision vs. Recall [Segmentation]"
            )

            p_mean = p_downsampled.mean(0) if len(p_downsampled) else None
            if p_mean is not None:
                chart["series"].append({
                    "name": "all classes",
                    "data": np.concatenate(
                        [np.round(r_downsampled[:, None], 2),
                         np.round(p_mean[:, None], 2)], axis=1).tolist()
                })

            self.studio_publisher.save_json(
                filename="sc_segmentation_precision_recall.json",
                plot=chart
            )

            # Save F1 Curve - Line Chart
            f1_downsampled = []
            for f1 in plots.f1:
                f1 = np.interp(x_downsampled, x, f1)
                f1_downsampled.append(f1)
            f1_downsampled = np.array(f1_downsampled)

            chart = self.create_apexchart_lines(
                r_downsampled,
                f1_downsampled,
                plots.curve_labels,
                title="F1 vs. Confidence [Segmentation]",
                xlabel="Confidence",
                ylabel="F1"
            )
            self.studio_publisher.save_json(
                filename="sd_segmentation_f1_curve.json",
                plot=chart
            )

            # Save Precision Curve - Line Chart
            precision_downsampled = []
            for p in plots.precision:
                p = np.interp(x_downsampled, x, p)
                precision_downsampled.append(p)
            precision_downsampled = np.array(precision_downsampled)

            chart = self.create_apexchart_lines(
                r_downsampled,
                precision_downsampled,
                plots.curve_labels,
                title="Precision vs. Confidence [Segmentation]",
                xlabel="Confidence"
            )
            self.studio_publisher.save_json(
                filename="se_segmentation_precision_curve.json",
                plot=chart
            )

            # Save Recall Curve - Line Chart
            recall_downsampled = []
            for r in plots.recall:
                r = np.interp(x_downsampled, x, r)
                recall_downsampled.append(r)
            recall_downsampled = np.array(recall_downsampled)

            chart = self.create_apexchart_lines(
                r_downsampled,
                recall_downsampled,
                plots.curve_labels,
                title="Recall vs. Confidence [Segmentation]",
                xlabel="Confidence",
                ylabel="Recall"
            )
            self.studio_publisher.save_json(
                filename="sf_segmentation_recall_curve.json",
                plot=chart
            )

    def save_timings(self, timings: dict):
        """
        Save model timing metrics for input, inference, and output stages.

        Parameters
        ----------
        timings : dict
            Timing stats (min, max, avg) in milliseconds.
        """
        categories = ["Input Time", "Inference Time", "Output Time"]
        keys = ["input_time", "inference_time", "output_time"]

        # Create a bar chart of the timings.
        series = []
        for name in ["Min", "Max", "Avg"]:
            data = []
            for key in keys:
                data.append(
                    round(float(timings.get(f"{name.lower()}_{key}")), 2))
            series.append({"data": data, "name": name})

        chart = self.create_apexchart_bar(
            series=series,
            title='Timings (ms)',
            categories=categories
        )

        self.studio_publisher.save_json(
            filename="sa_timings.json",
            plot=chart
        )

        # Create a pie chart of the timings.
        series = []
        for key in ["avg_input_time", "avg_inference_time",
                    "avg_output_time"]:
            series.append(round(float(timings.get(key, 2))))

        chart = self.create_apexchart_pie(
            series=series,
            title="Distribution of the Average Timings",
            categories=categories
        )

        self.studio_publisher.save_json(
            filename="sb_average_timings.json",
            plot=chart
        )

    def post_metrics(self, logs=None):
        """
        Post the final metrics to EdgeFirst Studio.

        Parameters
        ----------
        logs: dict, optional
            This is a container of the final metrics.
        """
        metrics = dict()
        if "multitask" in logs.keys():
            metrics = logs.get("multitask")
            metrics = metrics.to_dict()

        elif "detection" in logs.keys():
            metrics = logs.get("detection")
            metrics = metrics.to_dict(with_boxes=True)

        elif "segmentation" in logs.keys():
            metrics = logs.get("segmentation")
            metrics = metrics.to_dict(with_boxes=False)

        parameters = self.parameters.to_dict()
        metrics["parameters"] = parameters

        self.studio_publisher.post_metrics(convert_to_serializable(metrics))

    def on_test_error(self, step: int, error, logs=None):
        """
        Report an error during validation and update the progress.

        Parameters
        ----------
        step : int
            Batch step at which the error occurred.
        error : Exception
            The exception raised during validation.
        logs : dict, optional
            Contains total number of steps for percentage calculation.
        """
        percentage = 0
        if logs is not None:
            total = logs.get("total")
            if total > 0:
                percentage = int((step / total) * 100)

        self.studio_publisher.update_stage(
            stage=self.stage_tracker.current()[0],
            status="error",
            message=str(error),
            percentage=percentage
        )

    def on_test_end(self, logs=None):
        """
        Report the final stages of validation
        and post the metrics.

        Parameters
        ----------
        logs : dict, optional
            Contains the metrics.
        """
        plots = logs.get("plots")
        timings = logs.get("timings")

        if "multitask" in logs.keys():
            self.save_detection_metrics(
                logs.get("multitask").detection_metrics, plots.detection_plots)
            self.save_segmentation_metrics(
                logs.get("multitask").segmentation_metrics, plots.segmentation_plots)
        elif "detection" in logs.keys():
            self.save_detection_metrics(logs.get("detection"), plots)
        elif "segmentation" in logs.keys():
            self.save_segmentation_metrics(logs.get("segmentation"), plots)
        self.save_timings(timings)
        self.post_metrics(logs)

        stage_name, stage_description = self.stage_tracker.current()
        self.studio_publisher.update_stage(
            stage=stage_name,
            status="complete",
            message=stage_description,
            percentage=100
        )
        self.studio_publisher.post_plots()
