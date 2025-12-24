"""
Utility functions for plotting evaluation metrics using matplotlib.
"""

import io
from typing import List

import numpy as np
import matplotlib
import matplotlib.figure
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.patches import Rectangle

matplotlib.use('Agg')


def figure2numpy(figure: matplotlib.figure.Figure) -> np.ndarray:
    """
    Converts a matplotlib.figure.Figure into a NumPy
    array so that it can be published to Tensorboard.

    Parameters
    ----------
    figure: matplotlib.figure.Figure
        This is the figure to convert to a numpy array.

    Returns
    -------
    np.ndarray
        The figure that is represented as a numpy array.
    """
    io_buf = io.BytesIO()
    figure.savefig(io_buf, format='raw')
    io_buf.seek(0)
    nimage = np.reshape(
        np.frombuffer(io_buf.getvalue(), dtype=np.uint8),
        newshape=(int(figure.bbox.bounds[3]), int(figure.bbox.bounds[2]), -1))
    io_buf.close()
    return nimage


def plot_classification_detection(
    class_histogram_data: dict,
    model: str = "Model",
) -> matplotlib.figure.Figure:
    """
    Plots the bar charts showing the precision, recall, and accuracy per class.
    It also shows the number of true positives, false positives,
    and false negatives per class.

    Parameters
    ----------
    class_histogram_data: dict.
        This contains information about the metrics per class.

        .. code-block:: python

            {
                'label_1': {
                    'precision': "The calculated precision at
                            IoU threshold 0.5 for the class",
                    'recall': "The calculated recall at
                            IoU threshold 0.5 for the class",
                    'accuracy': "The calculated accuracy at
                            IoU threshold 0.5 for the class",
                    'tp': "The number of true positives for the class",
                    'fn': "The number of false negatives for the class",
                    'fp': "The number of localization and
                            classification false positives for the class",
                    'gt': "The number of grounds truths for the class"
                },
                'label_2': ...
            }

    model: str
        The name of the model.

    Returns
    -------
    matplotlib.figure.Figure
        This shows two histograms on the left that compares
        the precision, recall, and accuracy and on the right
        compares the number of true positives, false positives,
        and false negatives for each class.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 10))
    # Score = [[prec c1, prec c2, prec c3], [rec c1, rec c2, rec c3], [acc c1,
    # acc c2, acc c3]]
    x_values = np.arange(len(class_histogram_data))
    labels, precision, recall, accuracy = list(), list(), list(), list()
    tp, fp, fn = list(), list(), list()

    for cls, value, in class_histogram_data.items():
        labels.append(cls)
        precision.append(round(value.get('precision') * 100, 2))
        recall.append(round(value.get('recall') * 100, 2))
        accuracy.append(round(value.get('accuracy') * 100, 2))
        tp.append(value.get('tp'))
        fn.append(value.get('fn'))
        fp.append(value.get('fp'))

    ax1.bar(x_values + 0.0, precision, color='m', width=0.25)
    ax1.bar(x_values + 0.25, recall, color='y', width=0.25)
    ax1.bar(x_values + 0.5, accuracy, color='c', width=0.25)

    ax2.bar(x_values + 0.0, tp, color='LimeGreen', width=0.25)
    ax2.bar(x_values + 0.25, fn, color='RoyalBlue', width=0.25)
    ax2.bar(x_values + 0.5, fp, color='OrangeRed', width=0.25)

    ax1.set_ylim(0, 100)

    ax1.set_ylabel('Score (%)')
    ax2.set_ylabel("Total Number")
    fig.suptitle(f"{model} Evaluation Table")

    ax1.xaxis.set_ticks(range(len(labels)), labels, rotation='vertical')
    ax2.xaxis.set_ticks(range(len(labels)), labels, rotation='vertical')

    colors = {'precision': 'm', 'recall': 'y', 'accuracy': 'c'}
    labels = list(colors.keys())
    handles = [Rectangle((0, 0), 1, 1, color=colors[label])
               for label in labels]
    ax1.legend(handles, labels)
    colors = {'true positives': 'green',
              'false negatives': 'blue',
              'false positives': 'red'}
    labels = list(colors.keys())
    handles = [Rectangle((0, 0), 1, 1, color=colors[label])
               for label in labels]
    ax2.legend(handles, labels)
    return fig


def plot_classification_segmentation(
    class_histogram_data: dict,
    model: str = "Model"
) -> matplotlib.figure.Figure:
    """
    Plots the bar charts showing the precision,
    recall, and accuracy per class.
    It also shows the number of true predictions
    and false predictions per class.

    Parameters
    ----------
    class_histogram_data: dict.
        This contains information about the metrics per class.

        .. code-block:: python

            {
                'label_1': {
                    'precision': "The calculated precision for the class",
                    'recall': "The calculated recall for the class",
                    'accuracy': "The calculated accuracy for the class",
                    'true_predictions': "The number of true prediction
                                        pixels of the class",
                    'false_predictions': "The number of false prediction
                                        pixels of the class",
                    'gt': "The number of grounds truths for the class"
                },
                'label_2': ...
            }

    model: str
        The name of the model.

    Returns
    -------
    matplotlib.figure.Figure
        This shows two histograms on the left that compares
        the precision, recall, and accuracy and on the right
        compares the number of true prediction and
        false prediction pixels for each class.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 10))
    # Score = [[prec c1, prec c2, prec c3], [rec c1, rec c2, rec c3], [acc c1,
    # acc c2, acc c3]]
    x_values = np.arange(len(class_histogram_data))
    labels, precision, recall, accuracy = list(), list(), list(), list()
    true_predictions, false_predictions = list(), list()

    for cls, value, in class_histogram_data.items():
        labels.append(cls)
        precision.append(round(value.get('precision') * 100, 2))
        recall.append(round(value.get('recall') * 100, 2))
        accuracy.append(round(value.get('accuracy') * 100, 2))
        true_predictions.append(value.get('true_predictions'))
        false_predictions.append(value.get('false_predictions'))

    ax1.bar(x_values + 0.0, precision, color='m', width=0.25)
    ax1.bar(x_values + 0.25, recall, color='y', width=0.25)
    ax1.bar(x_values + 0.5, accuracy, color='c', width=0.25)

    ax2.bar(x_values + 0.0, true_predictions, color='LimeGreen', width=0.25)
    ax2.bar(x_values + 0.25, false_predictions, color='OrangeRed', width=0.25)

    ax1.set_ylim(0, 100)

    ax1.set_ylabel('Score (%)')
    ax2.set_ylabel("Total Number")
    fig.suptitle(f"{model} Evaluation Table")

    ax1.xaxis.set_ticks(range(len(labels)), labels, rotation='vertical')
    ax2.xaxis.set_ticks(range(len(labels)), labels, rotation='vertical')

    colors = {'precision': 'm', 'recall': 'y', 'accuracy': 'c'}
    labels = list(colors.keys())
    handles = [Rectangle((0, 0), 1, 1, color=colors[label])
               for label in labels]
    ax1.legend(handles, labels)
    colors = {'true predictions': 'green',
              'false predictions': 'red'}
    labels = list(colors.keys())
    handles = [Rectangle((0, 0), 1, 1, color=colors[label])
               for label in labels]
    ax2.legend(handles, labels)
    return fig


def plot_score_histogram(
    tp_scores: np.ndarray,
    fp_scores: np.ndarray,
    model: str = "Model",
    title: str = "Histogram of TP vs FP Scores",
    xlabel: str = "Score",
    ylabel: str = "Count"
):
    """
    Create a score histogram to compare the number of true positives
    and false positives based on the scores. This provides insight
    on the optimal thresholds to use. Also draws count labels
    on each histogram bar.

    Parameters
    ----------
    tp_scores: np.ndarray
        All the scores for the true positives.
    fp_scores: np.ndarray
        All the scores for the false positives.
    model: str
        The name of the model evaluated.
    title: str
        Provide the title for the plot.
    xlabel: str
        The x-axis label.
    ylabel: str
        The y-axis label.

    Returns
    -------
    matplotlib.figure.Figure
        This shows the histogram comparing the scores of the
        true positives and false positives.
    """
    # Define histogram bins: 0.0 to 1.0 with step of 0.05
    bins = np.arange(0, 1.05, 0.05)

    # Compute histograms (counts only)
    tp_hist, _ = np.histogram(tp_scores, bins=bins)
    fp_hist, _ = np.histogram(fp_scores, bins=bins)

    # Plot histograms
    fig, ax = plt.subplots(1, 1, figsize=(10, 5), tight_layout=True)
    bin_centers = (bins[:-1] + bins[1:]) / 2

    tp_bars = ax.bar(bin_centers - 0.01,
                     tp_hist,
                     width=0.02,
                     label='True Positives',
                     alpha=0.7, color='green')
    fp_bars = ax.bar(bin_centers + 0.01,
                     fp_hist,
                     width=0.02,
                     label='False Positives',
                     alpha=0.7, color='red')

    # Annotate each bar with count
    for i, (tp_bar, fp_bar) in enumerate(zip(tp_bars, fp_bars)):
        tp_count = tp_hist[i]
        fp_count = fp_hist[i]
        if tp_count > 0:
            ax.text(tp_bar.get_x() + tp_bar.get_width() / 2,
                    tp_bar.get_height() + 0.5,
                    str(tp_count),
                    ha='center', va='bottom', fontsize=8, color='green')
        if fp_count > 0:
            ax.text(fp_bar.get_x() + fp_bar.get_width() / 2,
                    fp_bar.get_height() + 0.5,
                    str(fp_count),
                    ha='center', va='bottom', fontsize=8, color='red')

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(f'{model} {title}')
    ax.set_xticks(bins)
    ax.legend()
    ax.grid(True)
    return fig


def plot_pr_curve(
    precision: List[np.ndarray],
    recall: List[np.ndarray],
    ap: np.ndarray,
    names: list = [],
    model: str = "Model",
) -> matplotlib.figure.Figure:
    """
    Version 2 Ploting precision and recall per class and the average metric.
    Use this method for YoloV5 implementation of precision recall
    curve.

    Parameters
    ----------
    precision: (NxM) List[np.ndarray]
        N => number of classes and M is the number of precision values.
    recall: (NxM) List[np.ndarray]
        N => number of classes and M is the number of recall values.
    ap: (NxM) np.ndarray
        N => number of classes, M => 10 denoting each IoU threshold
        from (0.5 to 0.95 at 0.05 intervals).
    names: list
        This contains the unique string labels captured in the order
        that respects the data for precision and recall.
    model: str
        The name of the model evaluated.

    Returns
    -------
    matplotlib.figure.Figure
        The precision recall plot where recall is denoted
        on the x-axis and precision is denoted
        on the y-axis.
    """
    # Precision-recall curve
    fig, ax = plt.subplots(1, 1, figsize=(9, 6), tight_layout=True)
    if len(precision) == 0:
        ax.set_xlabel("Recall")
        ax.set_ylabel("Precision")
        ax.legend(bbox_to_anchor=(1.04, 1), loc="upper left")
        ax.set_title(f'{model} Precision-Recall Curve')
        return fig

    p = np.stack(precision, axis=1)
    if 0 < len(names) < 21:  # display per-class legend if < 21 classes
        for i, y in enumerate(p.T):
            # plot(recall, precision)
            ax.plot(recall, y, linewidth=1, label=f"{names[i]} {ap[i, 0]:.3f}")
    else:
        # plot(recall, precision)
        ax.plot(recall, p.mean(1), linewidth=1, color="grey")

    ax.plot(
        recall,
        p.mean(1),
        linewidth=3,
        color="blue",
        label="all classes %.3f mAP@0.50" % (ap[:, 0].mean()))
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.legend(bbox_to_anchor=(1.04, 1), loc="upper left")
    ax.set_title(f'{model} Precision-Recall Curve')
    return fig


def plot_mc_curve(
    px: np.ndarray,
    py: np.ndarray,
    names: list = [],
    model: str = "Model",
    xlabel: str = 'Confidence',
    ylabel: str = 'Metric'
) -> matplotlib.figure.Figure:
    """
    This function is used for plotting either the F1-curve or the
    precision/recall versus confidence curves.

    Parameters
    ----------
    px: (NxM) np.ndarray
        N => number of classes.
    py: (NxM) np.ndarray
        This could be values for the F1, precision, or recall.
    names: list
        This contains the unique string labels captured in the order
        that respects the data for precision and recall.
    model: str
        The name of the model evaluated.
    xlabel: str
        The metric on the x-axis.
    ylabel: str
        The metric on the y-axis.

    Returns
    -------
    matplotlib.figure.Figure
        The plot where recall is denoted
        on the x-axis and either  is denoted
        on the y-axis.
    """
    # Metric-confidence curve
    fig, ax = plt.subplots(1, 1, figsize=(9, 6), tight_layout=True)

    if 0 < len(names) < 21:  # display per-class legend if < 21 classes
        for i, y in enumerate(py):
            # plot(confidence, metric)
            ax.plot(px, y, linewidth=1, label=f'{names[i]}')
    else:
        # plot(confidence, metric)
        ax.plot(px, py.T, linewidth=1, color='grey')

    y = py.mean(0)
    ax.plot(px, y, linewidth=3, color='blue',
            label=f'all classes {y.max():.2f} at {px[y.argmax()]:.3f}')
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title(f'{model} {ylabel}-{xlabel} Curve')
    plt.legend(bbox_to_anchor=(1.04, 1), loc="upper left")
    return fig


def plot_confusion_matrix(
    confusion_data: np.ndarray,
    labels: list,
    model: str = "Model"
) -> matplotlib.figure.Figure:
    """
    Plots the confusion matrix using the method defined below:
    https://stackoverflow.com/questions/5821125/how-to-plot-confusion-matrix-with-string-axis-rather-than-integer-in-python/74152927#74152927

    Parameters
    ----------
    confusion_data: np.ndarray
        This is a square matrix representing the confusion matrix data
        where the rows are the predictions and the columns are the
        ground truth.
    labels: list
        This contains the unique string labels in the dataset.
    model: str
        The name of the model being validated.

    Returns
    --------
    matplotlib.figure.Figure
        The confusion matrix plot.
    """
    norm_conf = confusion_data / (confusion_data.sum(1).reshape(-1, 1) + 1e-6)

    fig = plt.figure()
    plt.clf()
    ax = fig.add_subplot(111)
    ax.set_aspect(1)
    res = ax.imshow(np.array(norm_conf), cmap=cm.get_cmap("jet"),
                    interpolation='nearest')
    width, height = confusion_data.shape

    for x, y in np.ndindex(confusion_data.shape):
        ax.text(y, x, f"{confusion_data[x, y]}", ha="center", va="center")

    fig.colorbar(res)
    plt.xticks(range(width), labels[:width], rotation="vertical")
    plt.yticks(range(height), labels[:height])
    plt.ylabel("Prediction")
    plt.xlabel("Ground Truth")
    plt.title(f"{model} Confusion Matrix")
    return fig


def plot_boxplot(
    iou_candidates: np.ndarray,
    score_candidates: np.ndarray,
    iou_stats: dict,
    score_stats: dict
) -> matplotlib.figure.Figure:
    """
    Plot the IoU and score box plot of the ground truth bounding boxes.
    This distribution finds the optimal IoU and score thresholds for deploying
    the model based on the higher limit of the plot which is the
    threshold for considering duplicate boxes.

    Parameters
    ----------
    iou_candidates: np.ndarray
        A 1D array containing IoU values throughout the dataset.
    score_candidates: np.ndarray
        A 1D array containing score values throughout the dataset.
    iou_stats: dict
        The quartile values to project onto the plot.

        .. code-block:: python

            stats = {
                "Low": lower_whisker,
                "Q1": p25,
                "Q2 (median)": p50,
                "Q3": p75,
                "High (Optimal IoU Threshold)": upper_whisker,
            }
    score_stats: dict
        The quartile values to project onto the plot.

        .. code-block:: python

            stats = {
                "Low (Max Recall)": p0,
                "Q2 (Max F1 - Optimal score threshold)": p50,
                "High (Max Precision)": p100,
            }

    Returns
    --------
    matplotlib.figure.Figure
        The IoU distribution box plot.
    """

    fig, axs = plt.subplots(1, 2, figsize=(12, 6), tight_layout=True)

    # ------------------------------------------------------------
    # 1. IoU Box Plot (Top)
    # ------------------------------------------------------------
    ax = axs[0]

    ax.boxplot(
        iou_candidates, showfliers=False, patch_artist=True,
        boxprops=dict(facecolor="#66c2a5", color="#1f78b4"),
        medianprops=dict(color="white")
    )

    # Get the x position of the single box
    xpos = 1  # single box plotted at x=1
    # Add text labels (now in data coordinates, not normalized)
    for i, (label, value) in enumerate(iou_stats.items()):
        if i == 4:
            fontweight = "bold"
        else:
            fontweight = "normal"

        ax.text(
            xpos + 0.1,  # offset a bit to the right of the box
            value,
            f"{label} {value:.2f}",
            ha="left", va="center",
            fontsize=8,
            color="black",
            fontweight=fontweight
        )

    # Style
    ax.set_xticks([])
    ax.set_ylabel("IoU Value")
    ax.set_title("Optimal IoU Threshold")

    # ------------------------------------------------------------
    # 2. Score Threshold Pseudo-Boxplot (Bottom)
    # ------------------------------------------------------------
    ax = axs[1]
    low, mid, high = score_candidates

    # Represent thresholds as a “whisker” errorbar plot
    ax.errorbar(
        [1], [mid],
        yerr=[[mid - low], [high - mid]],
        fmt='o',
        capsize=10,
        color="#1f78b4",
        label="Optimal thresholds",
    )

    # Get the x position of the single box
    xpos = 1  # single box plotted at x=1
    # Add text labels (now in data coordinates, not normalized)
    for i, (label, value) in enumerate(score_stats.items()):
        if i == 1:
            fontweight = "bold"
        else:
            fontweight = "normal"

        ax.text(
            xpos + 0.01,  # offset a bit to the right of the box
            value,
            f"{label} {value:.3f}",
            ha="left", va="center",
            fontsize=8,
            color="black",
            fontweight=fontweight
        )

    ax.set_xticks([])
    ax.set_ylabel("Score Value")
    ax.set_title("Optimal Score Threshold")

    return fig


def close_figures(figures: List[matplotlib.figure.Figure]):
    """
    Closes the matplotlib figures opened to prevent
    errors such as "Fail to allocate bitmap."

    Parameters
    ----------
    figures: List[matplotlib.figure.Figure]
        Contains matplotlib.pyplot figures to close.
    """
    if len(figures) > 0:
        for figure in figures:
            plt.close(figure)
