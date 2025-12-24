"""
Utilities for decoding model outputs into bounding boxes, scores, and masks.
"""

from typing import Tuple, Union, List

import numpy as np

from edgefirst.validator.datasets.utils.annotation_transforms import xcycwh2xyxy
from edgefirst.validator.metrics.utils.math import sigmoid


def decode_mpk_boxes(
        p: np.ndarray, anchors: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Decodes ModelPack boxes into boxes and scores.

    Parameters
    ----------
    p: np.ndarray
        Raw model output with typical shapes such
        as (1, 9, 15, 21) or (1, 17, 30, 21).
    anchors: np.ndarray
        Model anchors used for decoding the outputs
        sometimes with shape (3, 3).

    Returns
    -------
    boxes: np.ndarray
        The decoded bounding boxes with shape (1, N, 1, 4).
    scores: np.ndarray
        The decoded scores with shape (1, N, nc) where nc is
        the number of classes.
    """
    p = sigmoid(p)

    na = anchors.shape[0]
    nc = p.shape[-1] // na - 5
    _, h, w, _ = p.shape

    p = p.reshape((-1, h, w, na, nc + 5))
    grid = np.meshgrid(np.arange(w), np.arange(h))
    grid = np.expand_dims(np.stack(grid, axis=-1), axis=2)
    grid = np.tile(np.expand_dims(grid, axis=0), [
        1, 1, 1, na, 1])

    # Decoding
    xy = p[..., 0:2]
    wh = p[..., 2:4]
    obj = p[..., 4:5]
    probs = p[..., 5:]

    scores = obj * probs

    xy = (xy * 2.0 + grid - 0.5) / (w, h)
    wh = (wh * 2) ** 2 * anchors * 0.5
    xyxy = np.concatenate([
        xy - wh,
        xy + wh
    ], axis=-1)
    xyxy = xyxy.reshape((1, -1, 1, 4))
    scores = scores.reshape(1, -1, nc)

    return xyxy, scores


def decode_yolo_boxes(
    p: np.ndarray,
    with_masks: bool,
    nc: int
) -> Tuple[np.ndarray, np.ndarray, Union[np.ndarray, None]]:
    """
    Takes the output from Ultralytics models and decodes
    boxes, scores, classes, and mask coefficients (segmentation models).

    Parameters
    ----------
    p: np.ndarray
        The model output tensor with shape (1, nc + 4, 8400) or
        (1, nc + 4 + 32, 8400) for detection and segmentation respectively.
    with_masks: bool
        Slice the last 32 values from the output as the mask
        proto coefficients.
    nc: int
        The number of labels.

    Returns
    -------
    boxes: np.ndarray
        The boxes tensor with shape (8400, 4).
    scores: np.ndarray
        The scores tensor with shape (8400,).
    masks: Union[np.ndarray, None]
        The masks tensor coefficients with shape (8400, 32).
        Otherwise, if the model is detection, this will be None.
    """
    masks = None
    if p.shape[0] == 1:
        p = p[0]
    # Only transpose if shapes are [116, 8400] or [85, 25200]
    if p.shape[0] < p.shape[1]:
        # Transposing shape (116, 8400) -> (8400, 116).
        p = p.transpose((1, 0))
    boxes = xcycwh2xyxy(boxes=p[:, 0:4])
    if with_masks:
        det_i = p.shape[1] - 32
        scores = p[:, 4:det_i]
        masks = p[:, det_i:]  # Additional 32 protos from segmentation models.
    else:
        # YOLOv5 models contains [x, y, x, y, obj_conf, cls_conf] outputs.
        if p.shape[1] == nc + 5:
            scores = p[:, 5:]
            scores *= p[:, 4:5]  # conf = obj_conf * cls_conf # NOSONAR
        # YOLOv8 and YOLOv11
        else:
            scores = p[:, 4:]
    return boxes, scores, masks


def decode_yolox_boxes(
    p: np.ndarray,
    shape: tuple,
    p6: bool = False
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Decodes YOLOx outputs into boxes and scores.

    Parameters
    ----------
    p: np.ndarray
        The raw YOLOx model outputs with shape (1, 8400, 85).
    shape: tuple
        The model input shape (height, width).
    p6: bool
        If True, enables support for YOLOX-P6 with stride 64 detection head.

    Returns
    -------
    boxes: np.ndarray
        The decoded boxes with shape (8400, 4).
    scores: np.ndarray
        The decoded scores with shape (8400, nc).
    """
    h, w = shape

    grids = []
    expanded_strides = []
    strides = [8, 16, 32] if not p6 else [8, 16, 32, 64]

    hsizes = [h // stride for stride in strides]
    wsizes = [w // stride for stride in strides]
    for hsize, wsize, stride in zip(hsizes, wsizes, strides):
        xv, yv = np.meshgrid(np.arange(wsize), np.arange(hsize))
        grid = np.stack((xv, yv), 2).reshape(1, -1, 2)
        grids.append(grid)
        shape = grid.shape[:2]
        expanded_strides.append(np.full((*shape, 1), stride))

    grids = np.concatenate(grids, 1)
    expanded_strides = np.concatenate(expanded_strides, 1)
    p[..., :2] = (p[..., :2] + grids) * expanded_strides
    p[..., 2:4] = np.exp(p[..., 2:4]) * expanded_strides
    predictions = p[0]

    boxes = predictions[:, :4]
    scores = predictions[:, 4:5] * predictions[:, 5:]

    return boxes, scores


def decode_yolo_masks(masks: np.ndarray, protos: np.ndarray) -> np.ndarray:
    """
    Takes the output from Ultralytics segmentation models and
    decodes instance segmentation masks from the model.

    Parameters
    ----------
    masks: np.ndarray
        The mask coefficients with shape (n, 32).
    protos: np.ndarray
        The raw output mask tensor with shape (1, h, w, 32).

    Returns
    -------
    np.ndarray
        The instance mask per object with shape (n, h, w).
    """
    # In case of shape (1, 32, h, w).
    if protos.shape[1] == 32:
        c, h, w = protos[0].shape
    else:
        h, w, c = protos[0].shape
        protos = np.transpose(protos, (0, 3, 1, 2))
    masks = np.matmul(masks, protos.reshape(c, -1)).reshape(-1, h, w)
    return masks


def decode_mpk_masks(masks: np.ndarray) -> np.ndarray:
    """
    Decodes ModelPack masks into semantic segmentation.

    Parameters
    ----------
    masks: np.ndarray
        The raw segmentation masks from the model
        with shape (1, h, w, nc).

    Returns
    -------
    np.ndarray
        The decoded semantic segmentation mask
        with shape (1, h, w).
    """
    if len(masks.shape) == 3:
        return np.array(masks, dtype=np.uint8)
    return np.argmax(masks, axis=-1).astype(np.uint8)


def crop_masks(
    masks: np.ndarray,
    boxes: np.ndarray,
    backend: str = "default"
) -> np.ndarray:
    """
    Crops each instance mask to the bounding box.

    Parameters
    ----------
    masks: np.ndarray
        The instance mask per object with shape (n, h, w).
    boxes: np.ndarray
        Normalized box coordinates in [xmin, ymin, xmax, ymax]
        format with shape (n, 4).
    backend: str
        The backend type ("hal" or "default").
        If "hal", resizes cropped masks to bounding box dimensions.
        Otherwise, returns original mask dimensions.

    Returns
    -------
    np.ndarray
        If backend == "hal": cropped and resized masks with shape
        (n, crop_h, crop_w). Otherwise: cropped masks with shape (n, h, w).
    """

    n, h, w = masks.shape

    if backend == "hal":
        # Convert normalized coords → pixel indices for all n items at once
        px1 = (boxes[:, 0] * w).astype(np.uint32)
        py1 = (boxes[:, 1] * h).astype(np.uint32)
        px2 = (boxes[:, 2] * w).astype(np.uint32)
        py2 = (boxes[:, 3] * h).astype(np.uint32)

        # Clamp in vectorized fashion
        px1 = np.clip(px1, 0, w - 1)
        py1 = np.clip(py1, 0, h - 1)
        px2 = np.clip(px2, 0, w)
        py2 = np.clip(py2, 0, h)
        cropped = [
            np.expand_dims(masks[i, py1[i]:py2[i], px1[i]:px2[i]], axis=-1)
            for i in range(n)
        ]
    else:
        x1, y1, x2, y2 = np.split(  # pylint: disable=unbalanced-tuple-unpacking
            boxes[:, :, np.newaxis], 4, axis=1)  # shape (n, 1, 1)
        r = np.arange(w, dtype=boxes.dtype)[None, None, :]  # rows shape(1,1,w)
        c = np.arange(h, dtype=boxes.dtype)[None, :, None]  # cols shape(1,h,1)

        cropped = masks * ((r >= x1 * w) * (r < x2 * w)
                           * (c >= y1 * h) * (c < y2 * h))
    return cropped


def dequantize(x: np.ndarray, scale: float, zero_point: float) -> np.ndarray:
    """
    Dequantization of the model output tensor based on the scale
    and zero point values.

    Parameters
    ----------
    x: np.ndarray
        Quantized model output tensor typically with uint8 or int8 dtypes.
    scale: float
        Quantization scale factor.
    zero_point: float
        Quantization shift factor for signed tensors.

    Returns
    -------
    np.ndarray
        Dequantized tensors typically float32 dtypes.
    """
    if scale > 0:
        x = (x.astype(np.float32) - zero_point) * scale  # re-scale
    return x


def dequantize_kinara(
    output_dict: dict,
    method: str = "hal"
) -> List[np.ndarray]:
    """
    Dequantize a list of quantized outputs from Kinara models.

    Parameters
    ----------
    output_list : dict
        List of quantized model outputs.
    method: str
        The method to use for performing the dequantization.
        By default "hal" is used. Otherwise, NumPy operations are used.

    Returns
    -------
    list of np.ndarray
        List of dequantized outputs as float arrays.
    """
    num_outputs = len(output_dict)
    dequantized_outputs = []
    for i in range(num_outputs):
        output: np.ndarray = output_dict[i].numpy_data
        out_param = output_dict[i].params

        if (not out_param.postprocess_param.is_struct_format
                and not out_param.postprocess_param.is_float):

            bpp = out_param.bpp
            dtype = np.int8
            if bpp == 1:
                dtype = np.int8 if out_param.postprocess_param.is_signed else np.uint8
            elif bpp == 2:
                dtype = np.int16 if out_param.postprocess_param.is_signed else np.uint16
            elif bpp == 4:
                dtype = np.int32 if out_param.postprocess_param.is_signed else np.uint32

            qn, offset = (out_param.postprocess_param.qn,
                          out_param.postprocess_param.offset)
            buf = output.view(dtype=dtype)

            if method == "hal":
                dst_buffer = buf
            else:
                dst_buffer = (
                    (buf.astype(int) -
                     offset) *
                    qn).astype(
                    np.float32)
            dequantized_outputs.append(dst_buffer)
        else:
            dequantized_outputs.append(output)
    return dequantized_outputs
