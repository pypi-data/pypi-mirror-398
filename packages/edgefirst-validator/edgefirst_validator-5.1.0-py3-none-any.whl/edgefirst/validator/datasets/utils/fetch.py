"""
This module contains functions for fetching dataset artifacts.
"""

import os
import glob
import zipfile
from typing import Optional, Union

from edgefirst.validator.publishers.utils.logger import logger
from edgefirst.validator.datasets.utils.readers import read_labels_file
from edgefirst.validator.datasets.utils.readers import read_yaml_file


def get_image_files(
    directory_path: str,
    check_empty: bool = True,
    extensions: list = ['*.[pP][nN][gG]',
                        '*.[jJ][pP][gG]', '*.[jJ][pP][eE][gG]']
) -> list:
    """
    Gets all the path of the image files within the specified directory.

    Parameters
    ----------
    directory_path: str
        The path to the directory containing the images.
    check_empty: bool
        If this is true, it will raise an error if there are no images
        found at the path provided.
    extensions: list
        A list of image extensions to search.

    Returns
    -------
    list
        The list of all image paths found with various extensions.

    Raises
    ------
    ValueError
        This exception is raised if no images were found in the
        directory.
    """
    images = list()
    for ext in extensions:
        partial = glob.glob(os.path.join(directory_path, ext))
        images += partial

    if check_empty and len(images) == 0:
        raise ValueError(
            f"There are no images found in {directory_path}"
        )
    return sorted(images)


def contains_annotations(annotations: list) -> bool:
    """
    Checks if the detected annotation files are actual Darknet annotations.

    Parameters
    ----------
    annnotations: list
        This contains paths of annotations files.

    Returns
    -------
    bool
        This is true if the annotations are indeed image
        annotations, else it is returned as False.
    """
    non_annotation_files = ["readme.txt", "labels.txt"]

    if len(annotations) == 0:
        return False
    if len(annotations) == 1:
        # For additional, extranneous non annotation files, add it here.
        for non_annotation in non_annotation_files:
            if non_annotation in [os.path.basename(annotations[0]).lower()]:
                return False
        return True
    elif len(annotations) == 2:
        detected_files = sorted(
            [os.path.basename(annotation).lower()
             for annotation in annotations])
        non_annotation_files = sorted(non_annotation_files)
        # For additional, extranneous non annotation files, add it here.
        return non_annotation_files != detected_files
    else:
        return True


def get_annotation_files(
    directory_path: str,
    check_empty: bool = True
) -> list:
    """
    Gets all the path of the annotation files within the specified directory.

    Parameters
    ----------
    directory_path: str
        The path to the directory containing the text or JSON annotations.
    check_empty: bool
        If this is true, it will raise an error if there
        are no annotations found at the path provided.

    Returns
    -------
    list
        The list of annotation paths found as either text or JSON files.

    Raises
    ------
    FileNotFoundError
        Raised if no annotation files were found in the directory.
    """
    annotations = list()
    for ext in ['*.txt', '*.json']:
        annotations = glob.glob(os.path.join(directory_path, ext))
        if contains_annotations(annotations):
            break
        else:
            continue

    if check_empty and len(annotations) == 0:
        raise FileNotFoundError(
            f"There are no text or JSON files found in {directory_path}"
        )
    return annotations


def get_numpy_files(
    directory_path: str,
    check_empty: bool = True
) -> list:
    """
    Gets all the path of the NumPy files within the specified directory.
    These are usually the radar data annotations denoted by (cube.npy).

    Parameters
    ----------
    directory_path: str
        The path to the directory containing the NumPy files.
    check_empty: bool
        If this is true, it will raise an error if there
        are no NumPy files found at the path provided.

    Returns
    -------
    list
        The list of NumPy file paths found.

    Raises
    ------
    FileNotFoundError
        Raised if no NumPy files were found in the directory.
    """
    files = glob.glob(os.path.join(directory_path, "*.cube.npy"))
    if check_empty and len(files) == 0:
        raise FileNotFoundError(
            f"There are no NumPy files found in {directory_path}")
    return files


def get_shape(shape: tuple) -> tuple:
    """
    Returns the (height, width) shape
    of the original image dimensions.

    Parameters
    ----------
    shape: tuple
        The input shape with batch
        size and channels in any order.

    Returns
    -------
    tuple
        The (height, width) shape
        of the image dimensions.
    """
    # This will contain (height, width) already.
    if len(shape) == 2:
        return shape

    # Fetch only (height, width) from the shape.
    # Format channels from YUYV, RGB, RGBA.
    if shape[-1] in [2, 3, 4]:
        # This includes batch size. Format (1, height, width, channels).
        if len(shape) == 4:
            height, width = shape[1:3]
        else:
            height, width = shape[0:2]
    else:
        # This includes batch size. Format (1, channels, height, width).
        if len(shape) == 4:
            height, width = shape[2:4]
        else:
            height, width = shape[1:3]
    return (height, width)


def validate_dataset_source(source: str) -> str:
    """
    Validates the existance of the source path.

    Parameters
    ----------
    source: str
        The path to the dataset.

    Returns
    -------
    str
        The validated path to the dataset.

    Raises
    ------
    ValueError
        Raised if the provided source to the dataset is not a string.
    FileNotFoundError
        Raised if the provided source to the dataset does not exist.
    """
    if not isinstance(source, str):
        raise ValueError(
            "The provided path to the dataset is not a string. " +
            "Received type: {}".format(
                type(source)))

    # Strip for radar datasets, in YAML files containing these characters for
    # their subdirectories.
    if not os.path.exists(source.rstrip("/*/")):
        raise FileNotFoundError(
            "The given dataset path '{}' does not exist.".format(source))
    return source


def find_yaml_file(source: str) -> Union[str, None]:
    """
    Finds YAML files inside a directory. Returns the path to the YAML file
    if it exists, otherwise it returns None.

    Parameters
    ----------
    source: str
        The path to the directory to start to looking.

    Returns
    -------
    Union[str, None]
        str
            The path to the YAML file if it exists.
        None
            There are no YAML files found.
    """
    for root, _, files in os.walk(source):
        for file in files:
            if os.path.splitext(file)[1] == ".yaml":
                return os.path.join(root, file)
    return None


def find_labels_file(
    source: str,
    labels_path: Optional[str] = None,
    labels_file: str = "labels.txt"
) -> list:
    """
    Finds and reads the labels file inside the directory if
    the `source` is provided. Otherwise if the `labels_path` is provided,
    it will check if the file exists. The contents of the labels file is
    returned.

    Parameters
    ----------
    source: str
        The path to the directory to search for `labels.txt`.
    labels_path: Optional[str]
        The path to the `labels.txt` file if known.
    labels_file: str
        The name of the labels file to search.

    Returns
    -------
    list
        This is the list of labels that are the
        contents of the labels file. If the label file is not found,
        it will return an empty list.
    """
    labels = []
    # Check if labels.txt is under /dataset_path (source)/labels.txt.
    if os.path.exists(os.path.join(source, labels_file)):
        labels_path = os.path.join(source, labels_file)
    # Check if labels.txt path is explicitly provided.
    elif labels_path is not None:
        labels_path = validate_dataset_source(labels_path)
    # If labels.txt is not found, then search through the dataset.
    else:
        for root, _, files in os.walk(source):
            if labels_file in files:
                labels_path = os.path.join(root, labels_file)
        # Continue validation without the label file.
        if labels_path is None:
            logger("The dataset 'labels.txt' file could not be found.",
                   code="WARNING")

    if labels_path is not None:
        labels = read_labels_file(labels_path)

    return labels


def create_info(
    image_source: str,
    annotation_source: str,
    dataset_type: Optional[str] = None,
    labels: list = [],
) -> dict:
    """
    This creates the info dataset which is a dictionary
    containing the dataset information. This dictionary is formatted
    based on contents of internal Au-Zone formatted dataset YAML files.

    Parameters
    ----------
    image_source: str
        This is the path to the images.
    annotation_source: str
        This is the path to the annotation files.
    dataset_type: Optional[str]
        This is the type of the dataset ["darknet", "arrow"].
    labels: list
        This contains unique string labels.

    Returns
    -------
    dict
        The info dataset which contains dataset information.
    """
    info_dataset = dict()
    info_dataset["type"] = dataset_type
    info_dataset["classes"] = labels
    info_dataset["validation"] = {
        "images": image_source,
        "annotations": annotation_source
    }
    return info_dataset


def collect_tfrecord_files(
        source: str, labels: list = []) -> Union[dict, None]:
    """
    Searches the source directory provided to gather tfrecord files.

    Parameters
    ----------
    source: str
        The path to the directory to search for tfrecord files.
    labels: list
        The list of string labels to include in the dataset information.

    Returns
    -------
    Union[dict, None]
        This includes the path found for the tfrecord files and the labels.
        If no tfecord files were found, then None is returned.
    """
    tfrecord_files = glob.glob(os.path.join(source, "*.tfrecord"))
    if len(tfrecord_files) > 0:
        # There are no polar yaml representations defined yet.
        info_dataset = dict()
        info_dataset["classes"] = labels
        info_dataset["validation"] = {"path": source}
        return info_dataset
    return None


def collect_darknet_files(source: str, labels: list = []) -> Union[dict, None]:
    """
    Searches the source directory provided to gather images and text or JSON
    files from Darknet datasets.

    Parameters
    ----------
    source: str
        The path to the directory to search for
        images and annotation files.
    labels: list
        The list of string labels to include in the dataset information.

    Returns
    -------
    Union[dict, None]
        This includes the paths found for the images and the annotation
        files and the labels. If no images were found,
        then None is returned.
    """
    for location in ["", "images/validate", "images/validate/**",
                     "images/val", "images/val/**"]:
        image_source = os.path.join(source, location)
        images = get_image_files(image_source, False)
        if len(images) > 0:
            break

    for location in ["", "labels/validate", "labels/validate/**",
                     "labels/val", "labels/val/**"]:
        annotation_source = os.path.join(source, location)
        annotations = get_annotation_files(annotation_source, False)
        if len(annotations) > 0:
            break

    if len(images) == 0:
        return None

    return create_info(
        image_source,
        annotation_source,
        "darknet",
        labels
    )


def collect_edgefirst_files(
        source: str, labels: list = []) -> Union[dict, None]:
    """
    Searches the source directory provided to look for 'dataset.arrow'
    which indicates an edgefirst dataset.

    Parameters
    ----------
    source: str
        The path to the directory to search for 'dataset.arrow'.
    labels: list
        The list of string labels to include in the dataset information.

    Returns
    -------
    Union[dict, None]
        This includes the paths found for the images and the 'dataset.arrow'
        file containing annotations and the labels. If the 'dataset.arrow' file
        was not found, then None is returned.
    """
    images_source = source
    annotation_source = os.path.join(source, "dataset.arrow")

    if os.path.exists(annotation_source):
        return create_info(
            images_source,
            annotation_source,
            "edgefirst",
            labels
        )
    else:
        return None


def download_and_extract(
        url: str, download_path: str, extract_to: Optional[str] = None):
    """
    Downloads a ZIP file from a URL and extracts it to a specified location.

    Parameters
    ----------
    url: str
        URL of the ZIP file to download.
    download_path: str
        Path where the ZIP file will be saved.
    extract_to: Optional[str]
        Directory where the ZIP contents will be extracted. If not specified,
        uses the directory of `download_path`.
    """
    import requests
    os.makedirs(os.path.dirname(download_path), exist_ok=True)

    logger(
        f"Downloading dataset from {url} to {download_path}...", code="INFO")
    response = requests.get(url, stream=True, timeout=30)
    response.raise_for_status()

    with open(download_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    logger("Download complete.", code="SUCCESS")

    extract_path = extract_to or os.path.dirname(download_path)
    logger(f"Extracting to {extract_path}...", code="INFO")

    with zipfile.ZipFile(download_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)

    logger("Extraction complete.", code="SUCCESS")


def download_file(url: str, download_path: str):
    """
    Downloads a file from a URL to the specified path.

    Parameters
    ----------
    url: str
        URL of the file to download.
    download_path: str
        Path to save the downloaded file.
    """
    import requests
    os.makedirs(os.path.dirname(download_path), exist_ok=True)

    logger(f"Downloading model from {url} to {download_path}...", code="INFO")
    response = requests.get(url, stream=True, timeout=30)
    response.raise_for_status()

    with open(download_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    logger("Download complete.", code="SUCCESS")


def classify_directory(
        source: str, labels_path: Optional[str] = None) -> dict:
    """
    Inspects the source path that points to a directory. Returns the
    info dataset which contains dataset information.

    Parameters
    ----------
    source: str
        The validated path to the dataset.
        This can point to a YAML file or a directory containing
        tfrecords or images and text annotations.
    labels_path: Optional[str]
        The path to the labels.txt (optional).

    Returns
    -------
    dict
        This dictionary contains the paths of the dataset files
        either the tfrecords or the images and the annotation files.
        This dictionary also contains the string labels if it exists.

    Raises
    ------
    FileNotFoundError
        Raised if the dataset could not be parsed. Might be due
        to missing dataset file.
    """

    # Handle AuZoneNet and AuZoneTFRecords format.
    # Check if a dataset yaml file is inside the directory.
    yaml_file = find_yaml_file(source)
    if yaml_file:
        return read_yaml_file(yaml_file)

    # Find and read the contents of the labels file.
    labels = find_labels_file(source, labels_path)

    # Handle standard TFRecord datasets.
    info_dataset = collect_tfrecord_files(source, labels)
    if info_dataset:
        return info_dataset

    # Handle standard Darknet datasets.
    info_dataset = collect_darknet_files(source, labels)
    if info_dataset:
        return info_dataset

    # Handle EdgeFirst datasets
    info_dataset = collect_edgefirst_files(source, labels)
    if info_dataset:
        return info_dataset
    else:
        raise FileNotFoundError(
            "The info_dataset returned None. " +
            f"Check if the path provided ({source}) contains " +
            "either tfrecord files or images and annotations files."
        )


def classify_file(source: str) -> dict:
    """
    Inspects the source path that points to a file.

    Parameters
    ----------
    source: str
        The validated path to the dataset.
        This can point to a YAML file or a directory containing
        tfrecords or images and text annotations.

    Returns
    -------
    dict
        This dictionary contains the paths of the dataset files
        either the tfrecords or the images and the annotation files.
        This dictionary also contains the string labels if it exists.

    Raises
    ------
    NotImplementedError
        Reading certain dataset formats are currently not implemented.
    """
    # Darknet dataset YAML file.
    if os.path.splitext(os.path.basename(source))[1] == ".yaml":
        contents = read_yaml_file(source)

        if "dataset" in contents.keys():
            images_path = contents.get(
                "dataset", {}).get('validation', {}).get('images', None)
            if not os.path.isabs(images_path):
                images_path = os.path.join(
                    os.path.dirname(source), images_path)
                contents["dataset"]["validation"]["images"] = images_path

            annotations_path = contents.get(
                "dataset", {}).get('validation', {}).get('annotations', None)
            if not os.path.isabs(annotations_path):
                annotations_path = os.path.join(os.path.dirname(source),
                                                annotations_path)
                contents["dataset"]["validation"]["annotations"] = annotations_path
        else:
            images_path = contents.get('validation', {}).get('images', None)
            if not os.path.isabs(images_path):
                images_path = os.path.join(
                    os.path.dirname(source), images_path)
                contents["validation"]["images"] = images_path

            annotations_path = contents.get(
                'validation', {}).get(
                'annotations', None)
            if not os.path.isabs(annotations_path):
                annotations_path = os.path.join(os.path.dirname(source),
                                                annotations_path)
                contents["validation"]["annotations"] = annotations_path
        return contents
    # Dataset cache LMDB file.
    elif os.path.splitext(os.path.basename(source))[1] == ".db":
        return {"type": "lmdb"}
    elif os.path.splitext(os.path.basename(source))[1] == ".txt":
        raise NotImplementedError(
            "Single text file is not currently supported.")
    elif os.path.splitext(source)[1] == ".deepview":
        raise NotImplementedError(
            "DeepView files are not currently supported.")
    else:
        raise NotImplementedError(
            "Parsing dataset '{}' is currently not supported.".format(source))


def classify_dataset(
    source: str,
    labels_path: Optional[str] = None
) -> Union[dict, None]:
    """
    Inspects the (.yaml) file contents if it exists.
    Otherwise it will search for either images with text
    annotations (Darknet) or tfrecord files (TFRecord Dataset).

    Parameters
    ----------
    source: str
        The validated path to the dataset.
        This can point to a YAML file or a directory containing
        tfrecords or images and text annotations.
    labels_path: Optional[str]
        The path to the labels.txt (optional).

    Returns
    -------
    Union[dict, None]
        This dictionary contains the paths of the dataset files
        either the tfrecords or the images and the annotation files.
        This dictionary also contains the string labels if it exists.

    Raises
    ------
    NotImplementedError
        Reading certain dataset formats are currently not implemented.
    """
    source = validate_dataset_source(source)

    if os.path.isdir(source):
        return classify_directory(source, labels_path)
    if os.path.isfile(source):
        return classify_file(source)
    raise NotImplementedError(
        "Parsing dataset '{}' is currently not supported.".format(source))
