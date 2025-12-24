"""
This module contains functions for transforming dataset annotations.
"""

import math
import numbers
from typing import Optional, Union, Tuple, Any, List

import numpy as np
from PIL import Image, ImageDraw

from edgefirst.validator.datasets.utils.image_transforms import resize

# Transform label synonyms to a common representation.
COCO_LABEL_SYNC = {
    "motorbike": "motorcycle",
    "aeroplane": "airplane",
    "sofa": "couch",
    "pottedplant": "potted plant",
    "diningtable": "dining table",
    "tvmonitor": "tv"
}


def clamp(
    value: Union[float, int],
    minimum: Union[float, int] = 0,
    maximum: Union[float, int] = 1
) -> Union[float, int]:
    """
    Clamps a given value between 0 and 1 by default.
    If the value is in between the set minimum and maximum, then it is returned.
    Otherwise it returns either minimum or maximum depending on which is the closest.

    Parameters
    ----------
    value: Union[float, int]
        Value to clamp between 0 and 1 (default).
    minimum: Union[float, int]
        Minimum acceptable value. Default to 0.
    maximum: Union[float, int]
        Maximum acceptable value. Default to 1.

    Returns
    -------
    Union[float, int]
        This is the clamped value.
    """
    return minimum if value < minimum else maximum if value > maximum else value


def standardize_coco_labels(labels: Union[list, np.ndarray]) -> list:
    """
    Converts synonyms of COCO labels to standard COCO labels using the
    provided labels mapping "COCO_LABEL_SYNC". This requires that the labels
    provided contain strings.

    Parameters
    ----------
    labels: Union[list, np.ndarray]
        This contains a list of string labels to map to
        standard COCO labels.

    Returns
    -------
    list
        Converted string labels to standard COCO labels.
    """
    synced_labels = []
    for label in labels:
        for key, value in COCO_LABEL_SYNC.items():
            if label == key:
                label = value
        synced_labels.append(label)
    return synced_labels


def labels2string(
    int_labels: Union[list, np.ndarray],
    string_labels: Union[list, np.ndarray]
) -> list:
    """
    Converts label indices into their string represenations.

    Parameters
    ----------
    int_labels: Union[list, np.ndarray]
        A list of integer labels as indices to convert into strings.
    string_labels: Union[list, np.ndarray]
        A list of unique string labels used to map the label
        indices into their string representations.

    Returns
    -------
    list
        A list of string labels.
    """
    labels = []
    for label in int_labels:
        labels.append(string_labels[int(label)] if isinstance(
            label, (numbers.Number, np.ndarray)) else label)
    return labels


def normalize(boxes: np.ndarray,
              shape: Optional[tuple] = None) -> np.ndarray:
    """
    Normalizes the boxes to the width and height
    of the image or model input resolution.

    Parameters
    ----------
    boxes: np.ndarray
        Contains bounding boxes to normalize [[boxes1], [boxes2]].
    shape: Optional[tuple]
        The (height, width) shape of the image to normalize the annotations.

    Returns
    -------
    np.ndarray
        new x-coordinate = old x-coordinate / width
        new y-coordinate = old y-coordinate / height
    """
    if shape is None:
        return boxes

    if isinstance(boxes, list):
        boxes = np.array(boxes)
    boxes[..., 0:1] /= shape[1]
    boxes[..., 1:2] /= shape[0]
    boxes[..., 2:3] /= shape[1]
    boxes[..., 3:4] /= shape[0]
    return boxes


def denormalize(boxes: np.ndarray,
                shape: Optional[tuple] = None) -> np.ndarray:
    """
    Denormalizes the boxes by the width and height of the image
    or model input resolution to get the pixel values of the boxes.

    Parameters
    ----------
    boxes: np.ndarray
        Contains bounding boxes to denormalize [[boxes1], [boxes2]].
    shape: Optional[tuple]
        The (height, width) shape of the image to denormalize the annotations.

    Returns
    -------
    np.ndarray
        Denormalized set of bounding boxes in pixels values.
    """
    if shape is None:
        return boxes

    if isinstance(boxes, list):
        boxes = np.array(boxes)
    boxes[..., 0:1] *= shape[1]
    boxes[..., 1:2] *= shape[0]
    boxes[..., 2:3] *= shape[1]
    boxes[..., 3:4] *= shape[0]
    return boxes.astype(np.int32)


def normalize_polygon(vertex: Union[list, np.ndarray], shape: tuple) -> list:
    """
    Normalizes the vertex coordinate of a polygon.

    Parameters
    ----------
    vertex: Union[list, np.ndarray]
        This contains [x, y] coordinate.
    shape: tuple
        The (height, width) shape of the image to normalize the annotations.

    Returns
    -------
    list
        This contains normalized [x, y] coordinates.
    """
    return [float(vertex[0]) / shape[1], float(vertex[1]) / shape[0]]


def denormalize_polygon(
    vertex: Union[list, np.ndarray],
    shape: Optional[tuple] = None
) -> Union[list, np.ndarray]:
    """
    Denormalizes the vertex coordinate of a polygon.

    Parameters
    ----------
    vertex: Union[list, np.ndarray]
        This contains [x, y] coordinate.
    shape: Optional[tuple]
        The (height, width) shape of the image to denormalize the annotations.

    Returns
    -------
    list
        This contains denormalized [x, y] coordinates.
    """
    if shape is None:
        return vertex
    return [int(float(vertex[0]) * shape[1]), int(float(vertex[1]) * shape[0])]


def check_normalized_boxes(
    boxes: np.ndarray, width: int, height: int
) -> np.ndarray:
    """
    Checks if the boxes are normalized between 0 and 1.
    If not, it normalizes them using the provided width and height.

    Parameters
    ----------
    boxes: np.ndarray
        The bounding boxes with shape (n, 4).
    width: int
        The width of the image to normalize the boxes.
    height: int
        The height of the image to normalize the boxes.

    Returns
    -------
    np.ndarray
        The normalized bounding boxes with shape (n, 4).
    """
    boundary = (boxes >= 0) & (boxes <= 1)
    if boundary.shape[0] > 0:
        normalized_conf = np.mean(boundary)
        if normalized_conf < 0.80 and boxes.shape[0] > 0:
            boxes[:, [0, 2]] /= width
            boxes[:, [1, 3]] /= height
    return boxes


def xcycwh2xyxy(boxes: np.ndarray) -> np.ndarray:
    """
    Converts YOLO (xcycwh) format into PascalVOC (xyxy) format.

    Parameters
    ----------
    boxes: np.ndarray
        Contains lists for each boxes in YOLO format [[boxes1], [boxes2]].

    Returns
    -------
    np.ndarray
        Contains list for each boxes in PascalVOC format.
    """
    return np.concatenate([
        boxes[:, 0:2] - boxes[:, 2:4] / 2,
        boxes[:, 0:2] + boxes[:, 2:4] / 2
    ], axis=1)


def xyxy2xcycwh(boxes: np.ndarray) -> np.ndarray:
    """
    Converts PascalVOC (xyxy) into YOLO (xcycwh) format.

    Parameters
    ----------
    boxes: np.ndarray
        Contains lists for each boxes in PascalVOC format [[boxes1], [boxes2]].

    Returns
    -------
    np.ndarray
        Contains list for each boxes in YOLO format.
    """
    w_c = boxes[..., 2:3] - boxes[..., 0:1]
    h_c = boxes[..., 3:4] - boxes[..., 1:2]
    boxes[..., 0:1] = boxes[..., 0:1] + w_c / 2
    boxes[..., 1:2] = boxes[..., 1:2] + h_c / 2
    boxes[..., 2:3] = w_c
    boxes[..., 3:4] = h_c
    return boxes


def xywh2xyxy(boxes: np.ndarray) -> np.ndarray:
    """
    Converts COCO (xywh) format to PascalVOC (xyxy) format.

    Parameters
    ----------
    boxes: np.ndarray
        Contains lists for each boxes in COCO format [[boxes1], [boxes2]].

    Returns
    -------
    np.ndarray
        Contains list for each boxes in PascalVOC format.
    """
    boxes[..., 2:3] = boxes[..., 2:3] + boxes[..., 0:1]
    boxes[..., 3:4] = boxes[..., 3:4] + boxes[..., 1:2]
    return boxes


def xyxy2xywh(boxes: np.ndarray) -> np.ndarray:
    """
    Converts PascalVOC (xyxy) format to COCO (xywh) format.

    Parameters
    ----------
    boxes: np.ndarray
        Contains lists for each boxes in COCO format [[boxes1], [boxes2]].

    Returns
    -------
    np.ndarray
        Contains list of each boxes in COCO format.
    """
    boxes[..., 2:3] = boxes[..., 2:3] - boxes[..., 0:1]
    boxes[..., 3:4] = boxes[..., 3:4] - boxes[..., 1:2]
    return boxes


def scale(
    boxes: np.ndarray,
    w: int = 640,
    h: int = 640,
    padw: int = 0,
    padh: int = 0,
) -> np.ndarray:
    """
    Scales the bounding boxes to be centered around the objects of an image
    with letterbox transformation.

    Parameters
    ----------
    boxes: np.ndarray (nx4)
        This is already in xyxy format.
    w: int
        This is the width of the image before any letterbox
        transformation.
    h: int
        This is the height of the image before any letterbox
        transformation.
    padw: int
        The width padding in relation to the letterbox.
    padh: int
        The height padding in relation to the letterbox.

    Returns
    -------
    np.ndarray
        The bounding boxes rescaled to be centered around the
        objects of an image with letterbox transformation.
    """
    y = np.copy(boxes)
    y[..., 0] = w * (boxes[..., 0]) + padw  # top left boxes
    y[..., 1] = h * (boxes[..., 1]) + padh  # top left y
    y[..., 2] = w * (boxes[..., 2]) + padw  # bottom right boxes
    y[..., 3] = h * (boxes[..., 3]) + padh  # bottom right y
    return y


def clamp_boxes(boxes: np.ndarray,
                clip: int,
                shape: Optional[tuple] = None) -> np.ndarray:
    """
    Clamps bounding boxes with size less than the provided clamp value to
    the clamp value in pixels. The minimum width and height  (dimensions)
    of the bounding is the clamp value in pixels.

    Parameters
    ----------
    boxes: np.ndarray
        The bounding boxes to clamp. The bounding boxes with dimensions
        larger than the clamp value will be kept, but the smaller boxes will
        be resized to the clamp value.
    clip: int
        The minimum dimensions allowed for the height and width of the
        bounding box. This value is in pixels.
    shape: Optional[tuple]
        If None is provided (by default), it assumes the boxes are in pixels.
        Otherwise, if shape is provided, the boxes are normalized which
        will transform the boxes in pixel representations first to be
        compared to the clamp value provided which is in pixels. The
        shape provided should be the (height, width) of the image.

    Returns
    -------
    np.ndarray
        The bounding boxes where the smaller boxes have been
        sized to the clamp value provided.
    """
    if len(boxes) == 0:
        return boxes

    if shape is None:
        height, width = (1, 1)
    else:
        height, width = shape

    widths = ((boxes[..., 2:3] - boxes[..., 0:1]) * width).flatten()
    heights = ((boxes[..., 3:4] - boxes[..., 1:2]) * height).flatten()
    modify = np.transpose(
        np.nonzero(((widths < clip) + (heights < clip)))).flatten()

    boxes[modify, 2:3] = boxes[modify, 0:1] + clip / width
    boxes[modify, 3:4] = boxes[modify, 1:2] + clip / height
    return boxes


def ignore_boxes(
    ignore: int,
    boxes: np.ndarray,
    labels: np.ndarray,
    scores: Optional[np.ndarray] = None,
    shape: Optional[tuple] = None
) -> Tuple[np.ndarray, np.ndarray, Union[None, np.ndarray]]:
    """
    Removes the boxes, labels, and scores provided if the boxes have dimensions
    less than the provided value set by the ignore parameter in pixels.

    Parameters
    ----------
    ignore: int
        The size of the boxes lower than this value will be removed. This
        value is in pixels.
    boxes: np.ndarray
        The bounding boxes array with shape (n, 4). The bounding boxes with
        dimensions less than the ignore parameter will be removed.
    labels: np.ndarray
        The labels associated to each bounding box. For every bounding box
        that was removed, the labels will also be removed.
    scores: Optional[np.ndarray]
        (Optional) the scores associated to each bounding box. For every
        bounding box that was removed, the scores will also be removed.
    shape: Optional[tuple]
        If None is provided (by default), it assumes the boxes are in pixels.
        Otherwise, if shape is provided, the boxes are normalized which
        will transform the boxes in pixel representations first to be
        compared to the ignore value provided which is in pixels. The
        shape provided should be the (height, width) of the image.

    Returns
    -------
    boxes: np.ndarray
        The bounding boxes where the smaller boxes have been removed.
    labels: np.ndarray
        The labels which contains only the labels of
        the existing bounding boxes.
    scores: Union[None, np.ndarray]
        If scores is not provided, None is returned. Otherwise,
        the scores of the returned bounding boxes are returned.
    """
    if shape is None:
        height, width = (1, 1)
    else:
        height, width = shape

    widths = ((boxes[..., 2:3] - boxes[..., 0:1]) * width).flatten()
    heights = ((boxes[..., 3:4] - boxes[..., 1:2]) * height).flatten()
    keep = np.transpose(
        np.nonzero(((widths >= ignore) * (heights >= ignore)))).flatten()

    boxes = np.take(boxes, keep, axis=0)
    labels = np.take(labels, keep, axis=0)
    if scores is not None:
        scores = np.take(scores, keep, axis=0)

    return boxes, labels, scores

# Functions for Segmentation Transformations


def segments2boxes(segments: list, box_format: str = "xcycwh") -> np.ndarray:
    """
    Convert segment labels to box labels, i.e.
    (xy1, xy2, ...) to (xcycwh).

    Parameters
    ----------
    segments: list
        List of segments where each segment is a list of points,
        each point is [x, y] coordinates.
    box_format: str
        Default output box format is in "xcycwh" (YOLO) format.
        Otherwise, "xywh" (COCO) and "xyxy" (PascalVOC) are also accepted.

    Returns
    -------
    np.ndarray
        Bounding box coordinates in YOLO format.
    """
    boxes = []
    for s in segments:
        x, y = s.T  # segment xy
        boxes.append([x.min(), y.min(), x.max(), y.max()])  # xyxy

    if box_format == "xcycwh":
        return xyxy2xcycwh(np.array(boxes))  # cls, xywh
    elif box_format == "xywh":
        return xyxy2xywh(np.array(boxes))
    else:
        return np.array(boxes)


def resample_segments(segments: list, n: int = 1000) -> list:
    """
    Resample segments to n points each using linear interpolation.
    Source: https://github.com/ultralytics/ultralytics/blob/main/ultralytics/utils/ops.py#L485

    Parameters
    ----------
    segments: list
        List of (N, 2) arrays where N is the number of points in each segment.
    n: int
        Number of points to resample each segment to.

    Returns
    -------
    list
        Resampled segments with n points each.
    """
    for i, s in enumerate(segments):
        if len(s) == n:
            continue
        s = np.concatenate((s, s[0:1, :]), axis=0)
        x = np.linspace(0, len(s) - 1, n - len(s) if len(s) < n else n)
        xp = np.arange(len(s))
        x = np.insert(x, np.searchsorted(x, xp), xp) if len(s) < n else x
        segments[i] = (
            np.concatenate([np.interp(x, xp, s[:, i]).astype(np.float32)
                            for i in range(2)]).reshape(2, -1).T
        )  # segment xy
    return segments


def format_segments(
    segments: np.ndarray,
    shape: tuple,
    ratio_pad: tuple,
    colors: Union[list, np.ndarray],
    mask_ratio: int = 1,
    semantic: bool = False,
    backend: str = "hal",
    background_index: int = 0
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Convert polygon segments to bitmap masks.

    Parameters
    ----------
    segments: np.ndarray
        Mask segments with shape (# polygons, # coordinates, 2)
    shape: tuple
        This represents the (height, width) of the model input shape.
    ratio_pad: tuple
        This contains the scale and the padding factors after letterbox
        transformations in the form ((scale x, scale y), (pad x, pad y)).
    colors: Union[list, np.ndarray]
        The label to specify to each polygon.
    mask_ratio: int, optional
        Masks are downsampled according to mask_ratio. Set to 1 so
        that the output shape of the mask matches the model prediction shape.
    semantic: bool, optional
        Specify if the type of segmentation is semantic segmentation.
        By default this is False and set to instance segmentation as
        seen in Ultralytics. Instance segmentation is where
        each mask is represented separately.
    backend: str
        Specify the backend library for resizing the image from the options
        "hal", "opencv", "pillow".
    background_index: int
        The integer representing the background class in the mask.
        For semantic segmentation this is the last label.

    Returns
    -------
    masks: np.ndarray
        Bitmap masks with shape (N, H, W) or (1, H, W)
        if mask_overlap is True.
    sorted_idx: np.ndarray
        Resorting the ground truth based on these indices.
    """
    scale_h, scale_w = ratio_pad[0]
    padw, padh = ratio_pad[1]

    if len(segments):
        segments[..., 0] *= scale_w
        segments[..., 1] *= scale_h
        segments[..., 0] += padw
        segments[..., 1] += padh

    sorted_idx = None

    if semantic:
        masks = create_mask_image(
            polygons=segments,
            labels=colors,
            shape=shape,
            background_index=background_index
        )
    else:
        masks = polygons2masks(
            imgsz=shape,
            segments=segments,
            downsample_ratio=mask_ratio,
            backend=backend
        )
    return masks, sorted_idx


def polygon2mask(
    imgsz: Tuple[int, int],
    polygons: List[np.ndarray],
    color: int = 1,
    downsample_ratio: int = 1,
    backend: str = "hal"
) -> np.ndarray:
    """
    Convert a list of polygons to a binary mask of the specified image size.

    Parameters
    ----------
    imgsz: Tuple[int, int]
        The size of the image as (height, width).
    polygons: List[np.ndarray]
        A list of polygons. Each polygon is an array with shape (N, M), where
        N is the number of polygons, and M is the number of points
        such that M % 2 = 0.
    color: int, optional
        The color value to fill in the polygons on the mask.
    downsample_ratio: int, optional
        Factor by which to downsample the mask.
    backend: str
        Specify the backend library for resizing the image from the options
        "hal", "opencv", "pillow".

    Returns
    -------
    np.ndarray
        A binary mask of the specified image size with the polygons filled in.
    """
    polygons = np.asarray(polygons, dtype=np.int32)
    polygons = polygons.reshape((polygons.shape[0], -1, 2))
    mask = create_mask_image(
        polygons=polygons,
        labels=color,
        shape=imgsz
    )

    if downsample_ratio > 1:
        nh, nw = (imgsz[0] // downsample_ratio, imgsz[1] // downsample_ratio)
        mask = resize(mask, (nw, nh), backend=backend)
    return mask


def polygons2masks(
    imgsz: Tuple[int, int],
    segments: List[np.ndarray],
    downsample_ratio: int = 1,
    backend: str = "hal"
) -> np.ndarray:
    """
    Convert a list of polygons to a set of binary instance
    segmentation masks at the specified image size.

    Parameters
    ----------
    imgsz: Tuple[int, int]
        The size of the image as (height, width).
    segments: List[np.ndarray]
        A list of polygons. Each polygon is an array with shape (N, M), where
        N is the number of polygons, and M is the number of points
        such that M % 2 = 0.
    colors: Union[list, np.ndarray]
        The color value to fill each polygon in the masks.
    downsample_ratio: int, optional
        Factor by which to downsample each mask.
    backend: str
        Specify the backend library for resizing the image from the options
        "hal", "opencv", "pillow".

    Returns
    -------
    np.ndarray
        A set of binary masks of the specified image size
        with the polygons filled in.
    """
    if len(segments) == 0:
        return np.zeros((1, imgsz[0], imgsz[1]), dtype=np.int32)
    return np.array([polygon2mask(imgsz, [x.reshape(-1)],
                                  downsample_ratio=downsample_ratio,
                                  backend=backend)
                     for x in segments])


def create_mask_image(
    polygons: Union[list, np.ndarray],
    labels: Union[list, np.ndarray, int],
    shape: tuple,
    background_index: int = 0
) -> np.ndarray:
    """
    Creates a NumPy array of masks from a given list of polygons.

    Parameters
    ----------
    polygons: Union[list, np.ndarray]
        This contains the polygon points. Ex.
        [[[x1,y1], [x2,y2], ... ,[xn,yn]], [...], ...]
    labels: Union[list, np.ndarray, int]
        The integer label of each polygon for assigning the mask.
        If an integer is supplied, then a constant label is applied
        for all the polygons.
    shape: tuple
        This is the shape (height, width) of the mask.
    background_index: int
        This is the integer representing the background class in the mask.

    Returns
    -------
    np.ndarray
        The 2D mask image with shape (height, width) specified.
    """
    mask = Image.new('L', (shape[1], shape[0]), background_index)
    canvas = ImageDraw.Draw(mask)
    polygons = polygons.tolist() if isinstance(polygons, np.ndarray) else polygons
    if isinstance(labels, (int, np.ScalarType)):
        labels = np.full(len(polygons), labels, dtype=np.uintp)
    for c, polygon in zip(labels, polygons):
        polygon = [tuple(pt) for pt in polygon]  # requires a list of Tuples.
        if len(polygon) >= 2:
            canvas.polygon(polygon, outline=int(c), fill=int(c))
    # This array contains a mask of the image where the objects are
    # outlined by class number
    return np.array(mask)


def create_mask_class(mask: np.ndarray, cls: int,
                      background_index: int) -> np.ndarray:
    """
    Separates a mask with more than one classes into an individual
    mask of 0's and background index where 0 represents the specified class and
    the background index represents other classes including background.
    This function is used for per class mask evaluation.

    Parameters
    ----------
    mask: np.ndarray
        Multiclass mask of class labels unique to each object.
    cls: int
        The integer representing the class in the mask
        to keep as a value of 0 (starting class).
        The other classes will be treated as the background index.
    background_index: int
        The integer representing the background class in the mask.

    Returns
    -------
    np.ndarray
        Binary 2D mask of 0's and background index.
    """
    temp_mask = np.where(mask != cls, background_index, mask)
    temp_mask[temp_mask == cls] = 0
    return temp_mask


def create_mask_background(mask: np.ndarray,
                           background_index: int) -> np.ndarray:
    """
    Creates a binary mask for the background class with 0's in the
    image and the rest of the objects will have values of the background index.
    This function switches the labels for background to 0 and
    positive classes to the background index. This is used for evaluating
    the background class.

    Parameters
    ----------
    mask: np.ndarray
        Multiclass mask array representing each image pixels.
    background_index: int
        The integer representing the background class in the mask.

    Returns
    -------
    np.ndarray
        Binary mask of 0's and background index, where 0's is background and
        objects are the background index.
    """
    # -1 is a temporary class
    temp_mask = np.where(mask != background_index, -1, mask)
    temp_mask[temp_mask == background_index] = 1
    temp_mask[temp_mask == -1] = background_index
    return temp_mask


def convert_to_serializable(obj: Any):
    """
    Recursively convert NumPy types to
    Python-native types for JSON serialization.

    Parameters
    ----------
    obj: Any
        Any NumPy type.

    Returns
    -------
    obj
        The object with a native
        python type representation.
    """
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.generic):
        return obj.item()  # Convert other NumPy scalars
    elif isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return 0
    elif isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(i) for i in obj]
    else:
        return obj
