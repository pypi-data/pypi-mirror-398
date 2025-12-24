"""
This module contains functions for transforming sensors data.
"""

from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING, Optional, Union, Tuple, Callable

import numpy as np
from PIL import Image, ExifTags

try:
    import edgefirst_hal  # type: ignore
    CONVERTER = edgefirst_hal.ImageProcessor()
except ImportError:
    CONVERTER = None

if TYPE_CHECKING:
    from edgefirst_hal import TensorImage  # type: ignore


def bgr2rgb(image: np.ndarray) -> np.ndarray:
    """
    Converts BGR image to RGB image.

    Parameters
    ----------
    image: (height, width, 3) np.ndarray
        The BGR image NumPy array.

    Returns
    -------
    np.ndarray
        The RGB image NumPy array.
    """
    return image[:, :, ::-1]


def rgb2bgr(image: np.ndarray) -> np.ndarray:
    """
    Converts RGB image to BGR image.

    Parameters
    ----------
    image: (height, width, 3) np.ndarray
        The RGB image NumPy array.

    Returns
    -------
    np.ndarray
        The BGR image NumPy array.
    """
    return bgr2rgb(image)


def rgb2yuyv(image: np.ndarray, backend: str = "hal") -> np.ndarray:
    """
    Convert an RGB image to YUYV format using the EdgeFirst Tensor API.

    Parameters
    ----------
    image: np.ndarray
        The 3-channel RGB image NumPy array.
    backend: str
        The backend library to use for this conversion.

    Returns
    -------
    np.ndarray
        The 2-channel YUYV image array.
    """

    if backend == "hal":
        try:
            import edgefirst_hal  # type: ignore # pylint: disable=redefined-outer-name
        except ImportError as exc:
            raise ImportError(
                "EdgeFirst HAL is needed to perform RGB to YUYV conversion."
            ) from exc

        height, width, _ = image.shape
        src = edgefirst_hal.TensorImage(
            width, height, fourcc=edgefirst_hal.FourCC.RGB)
        src.copy_from_numpy(image)

        dst = edgefirst_hal.TensorImage(
            width, height, fourcc=edgefirst_hal.FourCC.YUYV)
        if CONVERTER is None:
            raise ImportError(
                "EdgeFirst HAL converter is not available for RGB to YUYV conversion.")
        CONVERTER.convert(src, dst)

        im = np.zeros((dst.height, dst.width, 2), dtype=np.uint8)
        dst.normalize_to_numpy(im)
        return im
    else:
        try:
            import cv2  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "OpenCV is needed to perform RGB to YUYV conversion."
            ) from exc

        height, width, _ = image.shape
        yuv = cv2.cvtColor(image, cv2.COLOR_RGB2YUV)

        # Extract Y, U, V components
        Y = yuv[:, :, 0]
        U = yuv[:, :, 1]
        V = yuv[:, :, 2]

        # Subsample U and V horizontally (take every second column)
        U_subsampled = U[:, ::2]
        V_subsampled = V[:, ::2]

        # Prepare Y0, Y1 pairs from the original Y channel
        Y0 = Y[:, ::2]
        Y1 = Y[:, 1::2]

        # Combine the channels into a packed YUYV structure using numpy
        # The shape is (height, width/2, 4) temporarily before reshaping
        yuyv_packed = np.stack((Y0, U_subsampled, Y1, V_subsampled), axis=-1)

        # Reshape to the final YUYV buffer format (height, width, 2 channels ( interleaved YUV pairs))
        # The final data type should be CV_8UC2 (numpy uint8 with 2 channels
        # implicitly by reshape/stack)
        height, width = image.shape[0], image.shape[1]
        return yuyv_packed.reshape(height, width, 2)


def yuyv2rgb(image: np.ndarray, backend: str = "hal") -> np.ndarray:
    """
    Convert a YUYV image to RGB format using the EdgeFirst Tensor API.

    Parameters
    ----------
    image: np.ndarray
        The input 2-channel YUYV image.
    backend: str
        The backend library to use for this conversion.

    Returns
    -------
    np.ndarray
        The output 3-channel RGB image.
    """

    if backend == "hal":
        try:
            import edgefirst_hal  # type: ignore # pylint: disable=redefined-outer-name
        except ImportError as exc:
            raise ImportError(
                "EdgeFirst HAL is needed to perform YUYV to RGB conversion."
            ) from exc

        height, width, _ = image.shape
        src = edgefirst_hal.TensorImage(
            width, height, fourcc=edgefirst_hal.FourCC.YUYV)
        src.copy_from_numpy(image)

        dst = edgefirst_hal.TensorImage(
            width, height, fourcc=edgefirst_hal.FourCC.RGB)
        if CONVERTER is None:
            raise ImportError(
                "EdgeFirst HAL converter is not available for YUYV to RGB conversion.")
        CONVERTER.convert(src, dst)

        im = np.zeros((dst.height, dst.width, 3), dtype=np.uint8)
        dst.normalize_to_numpy(im)
        return im
    else:
        try:
            import cv2  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "OpenCV is needed to perform YUYV to RGB conversion."
            ) from exc
        return cv2.cvtColor(image, cv2.COLOR_YUV2RGB_YUY2)


def rgb2rgba(image: np.ndarray, backend: str = "hal") -> np.ndarray:
    """
    Convert a 3-channel RGB image to 4-channel RGBA image.

    Parameters
    ----------
    image: np.ndarray
        The 3-channel RGB image array.
    backend: str
        The backend library to use for this conversion.

    Returns
    -------
    np.ndarray
        The 4-channel RGBA image array with the alpha value set to 255.
    """

    if image.shape[0] == 3:
        _, height, width = image.shape
    elif image.shape[-1] == 3:
        height, width, _ = image.shape
    else:
        return image

    if backend == "hal":
        try:
            import edgefirst_hal  # type: ignore # pylint: disable=redefined-outer-name
        except ImportError as exc:
            raise ImportError(
                "EdgeFirst HAL is needed to perform RGB to RGBA conversion."
            ) from exc

        src = edgefirst_hal.TensorImage(
            width, height, fourcc=edgefirst_hal.FourCC.RGB)
        src.copy_from_numpy(image)

        dst = edgefirst_hal.TensorImage(
            width, height, fourcc=edgefirst_hal.FourCC.RGBA)
        if CONVERTER is None:
            raise ImportError(
                "EdgeFirst HAL converter is not available for RGB to RGBA conversion.")
        CONVERTER.convert(src, dst)

        im = np.zeros((dst.height, dst.width, 4), dtype=np.uint8)
        dst.normalize_to_numpy(im)
        return im
    else:
        alpha_channel = np.full((height, width, 1), 255, dtype=np.uint8)
        return np.concatenate((image, alpha_channel), axis=-1)


def imagenet(image: np.ndarray) -> np.ndarray:
    """
    Normalize the image with imagenet normalization.

    Parameters
    ----------
    image: np.ndarray
        The image RGB array with shape
        (3, height, width) or (height, width, 3).

    Returns
    -------
    np.ndarray
        The image with imagenet normalization.
    """
    mean = np.array([0.079, 0.05, 0]) + 0.406
    std = np.array([0.005, 0, 0.001]) + 0.224

    if image.shape[0] == 3:
        for channel in range(image.shape[0]):
            image[channel, :, :] = (image[channel, :, :] / 255
                                    - mean[channel]) / std[channel]
    else:
        for channel in range(image.shape[2]):
            image[:, :, channel] = (image[:, :, channel] / 255
                                    - mean[channel]) / std[channel]
    return image


def image_normalization(
    image: np.ndarray,
    normalization: str,
    input_type: np.dtype = np.dtype(np.float32)
):
    """
    Performs image normalizations (signed, unsigned, raw).

    Parameters
    ----------
    image: np.ndarray
        The image to perform normalization.
    normalization: str
        This is the type of normalization to perform
        ("signed", "unsigned", "raw", "imagenet").
    input_type: np.dtype
        This is the NumPy datatype to convert. Ex. "uint8"

    Returns
    -------
    np.ndarray
        Depending on the normalization, the image will be returned.
    """
    if normalization.lower() == 'signed':
        return ((image.astype(np.float32) / 127.5) - 1.0).astype(input_type)
    elif normalization.lower() == 'unsigned':
        return (image.astype(np.float32) /
                255.0).astype(input_type)
    elif normalization.lower() == 'imagenet':
        return (imagenet(image.astype(np.float32))).astype(input_type)
    else:
        return (image).astype(input_type)


def crop_image(image: np.ndarray, box: Union[list, np.ndarray]) -> np.ndarray:
    """
    Crops the image to only the area that is covered by
    the box provided. This is primarily used in pose validation.

    Parameters
    ----------
    image: np.ndarray
        The frame to crop before feeding to the model.
    box: Union[list, np.ndarray]
        This contains non-normalized [xmin, ymin, xmax, ymax].

    Returns
    -------
    np.ndarray
        The image cropped to the area of the bounding box.
    """
    x1, y1, x2, y2 = box
    box_area = image[y1:y2, x1:x2, ...]
    return box_area


def rotate_image(data: Union[bytes, str]) -> Image.Image:
    """
    Read from the ImageExif to apply rotation on the image.

    Parameters
    ----------
    data: Union[bytes, str]
        Read image file as a bytes object or a string path
        to the image file.

    Returns
    -------
    Image.Image
        The pillow Image with rotation applied.
    """
    img_file = BytesIO(data) if isinstance(data, bytes) else data
    image = Image.open(img_file)

    # Get EXIF data safely
    exif_data = image.getexif()  # returns Exif object, behaves like dict
    if exif_data:
        # Find Orientation tag key
        orientation_key = next(
            (k for k, v in ExifTags.TAGS.items() if v == 'Orientation'),
            None
        )

        orientation = 1  # Default orientation
        if orientation_key and orientation_key in exif_data:
            orientation = exif_data[orientation_key]

        # Apply rotation based on orientation
        if orientation == 3:
            image = image.rotate(180, expand=True)
        elif orientation == 6:
            image = image.rotate(270, expand=True)
        elif orientation == 8:
            image = image.rotate(90, expand=True)
    return image


def resize(
    image: Union[TensorImage, np.ndarray],
    size: Optional[tuple] = None,
    backend: str = "hal"
) -> Union[TensorImage, np.ndarray]:
    """
    Resizes the images with the specified dimension using
    the EdgeFirst Tensor API. The original aspect ratio is not maintained.
    Image needs to be uint8.

    Parameters
    ----------
    image: Union[edgefirst_hal.TensorImage, np.ndarray]
        The image (RGB, RGBA, Gray) tensor with uint8 dtype.
    size: Optional[tuple]
        Specify the (width, height) size of the new image.
    backend: str
        Specify the backend library for resizing the image from the options
        "hal", "opencv", "pillow".

    Returns
    -------
    Union[TensorImage, np.ndarray]
        Resized image.
    """
    if size is None:
        return image

    if backend == "hal":
        try:
            import edgefirst_hal  # type: ignore # pylint: disable=redefined-outer-name
        except ImportError as exc:
            raise ImportError(
                "EdgeFirst HAL is needed to resize using hal."
            ) from exc

        if isinstance(image, np.ndarray):
            # Array without any channels is assumed to be grey.
            if len(image.shape) == 2:
                fourcc = edgefirst_hal.FourCC.GREY
                fourc = fourcc
                image = np.expand_dims(image, axis=-1)
                channels = 1
            else:
                # Currently OpenGL in x86_64 only supports RGBA.
                channels = 4
                fourcc = edgefirst_hal.FourCC.RGBA
                if image.shape[-1] == 4:
                    fourc = edgefirst_hal.FourCC.RGBA
                elif image.shape[-1] == 1:
                    fourcc = edgefirst_hal.FourCC.GREY
                    fourc = fourcc
                    channels = 1
                else:
                    fourc = edgefirst_hal.FourCC.RGB
            height, width, _ = image.shape
            src = edgefirst_hal.TensorImage(width, height, fourcc=fourc)
            src.copy_from_numpy(image)
        else:
            src = image
            # Currently OpenGL in x86_64 only supports RGBA.
            fourcc = (edgefirst_hal.FourCC.RGBA if
                      src.format == edgefirst_hal.FourCC.RGB else src.format)
            channels = 1 if fourcc == edgefirst_hal.FourCC.GREY else 4

        dst = edgefirst_hal.TensorImage(size[0], size[1], fourcc=fourcc)
        if CONVERTER is None:
            raise ImportError(
                "EdgeFirst HAL converter is not available for resizing.")
        CONVERTER.convert(src, dst)

        im = np.zeros((dst.height, dst.width, channels), dtype=np.uint8)
        dst.normalize_to_numpy(im)

        if src.format == edgefirst_hal.FourCC.GREY:
            return im.squeeze()
        elif src.format == edgefirst_hal.FourCC.RGB:
            return im[:, :, 0:3]
        return im
    elif backend == "opencv":
        try:
            import cv2  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "OpenCV is needed to resize using opencv.") from exc

        if isinstance(image, np.ndarray):
            return cv2.resize(image, size, interpolation=cv2.INTER_LINEAR)
    else:
        if isinstance(image, np.ndarray):
            im = Image.fromarray(image.astype(np.uint8))
            im = im.resize(size)
            return np.array(im)
    return image


def pad(
    image: np.ndarray,
    input_size: tuple,
    backend: str = "hal"
) -> Tuple[np.ndarray, list]:
    """
    Performs image padding based on the implementation provided in YOLOx:\
    https://github.com/Megvii-BaseDetection/YOLOX/blob/main/yolox/data/data_augment.py#L142

    The image is always padded on the right and at the bottom portions.

    Parameters
    ----------
    image: np.ndarray
        This is the input image to pad.
    input_size: tuple
        This is the model input size (generally) or the output image
        resolution after padding in the order (height, width).
    backend: str
        Specify the backend library for resizing the image from the options
        "hal", "opencv", "pillow".

    Returns
    --------
    image: np.ndarray
        This is the padded image.
    shapes: list
        This is used to scale the bounding boxes of the ground
        truth and the model detections based on the letterbox
        transformation.
        [[pad image height, pad image width],
        [[scale_y, scale_x], [pad x, pad y]].
    """
    height, width = image.shape[:2]  # current shape [height, width]
    if len(image.shape) == 3:
        padded_image = np.ones(
            (input_size[0], input_size[1], 3), dtype=np.uint8) * 114
    else:
        padded_image = np.ones(input_size, dtype=np.uint8) * 114

    r = min(input_size[0] / height, input_size[1] / width)
    resized_image = resize(
        image, (int(width * r), int(height * r)), backend=backend
    )
    padded_image[: int(height * r),
                 : int(width * r)] = resized_image
    padded_image = rgb2bgr(padded_image)  # RGB2BGR
    padded_image = np.ascontiguousarray(padded_image)

    # The bounding box offset to add due to image padding.
    # Requires normalization due to the bounding boxes are already normalized.
    new_unpad = int(round(height * r)), int(round(width * r))
    dw = padded_image.shape[1] - new_unpad[1]  # / new_unpad[1]
    dh = padded_image.shape[0] - new_unpad[0]  # / new_unpad[0]

    # The image was not rescaled, so default to 1.0.
    shapes = [
        # imgsz (model input shape) [height, width]
        [padded_image.shape[0], padded_image.shape[1]],
        [[resized_image.shape[0] / input_size[0],
          resized_image.shape[1] / input_size[1]],
         [dw, dh]]  # ratio_pad [[scale y, scale x], [pad w, pad h]]
    ]
    return padded_image, shapes


def letterbox_native(
    image: np.ndarray,
    new_shape: tuple = (640, 640),
    constant: int = 114,
    backend: str = "hal"
) -> Tuple[np.ndarray, list]:
    """
    Applies the letterbox image transformations based in YOLOv5 and YOLOv7.

    Parameters
    ----------
    image : np.ndarray
        Input image array (HWC format).
    new_shape : tuple, optional
        Target shape (height, width) for output image, by default (640, 640).
    constant : int, optional
        Padding pixel value (0–255), by default 114 (gray).
    backend: str
        Specify the backend library for letterboxing the
        image from the options "opencv", "pillow".

    Returns
    -------
    image: np.ndarray
        The resized and padded image in HWC format.
    shapes: list
        This is used to scale the bounding boxes of the ground
        truth and the model detections based on the letterbox
        transformation. Tuple containing padded image size, scale ratio,
        and padding offsets.
        [[pad image height, pad image width],
        [[scale_y, scale_x], [pad x, pad y]]].
    """
    height, width = image.shape[:2]
    scale = min(new_shape[1] / width, new_shape[0] /
                height)  # pylint: disable=redefined-outer-name
    new_width = int(round(width * scale))
    new_height = int(round(height * scale))

    if scale != 1.0:
        image = resize(image, (new_width, new_height), backend=backend)

    # Compute padding
    dw, dh = new_shape[1] - new_width, new_shape[0] - new_height  # wh padding
    top = round(dh / 2)
    bottom = dh - top
    left = round(dw / 2)
    right = dw - left

    if backend == "opencv":
        try:
            import cv2  # type: ignore
        except ImportError as exc:
            raise ImportError("OpenCV is needed for letterbox.") from exc
        padded_image = cv2.copyMakeBorder(
            image, top, bottom, left, right, cv2.BORDER_CONSTANT,
            value=(constant, constant, constant))  # add border
    else:
        padded_image = np.zeros(
            (3, new_height + top + bottom, new_width + left + right))

        for i, _ in enumerate(padded_image):
            padded_image[i, :, :] = np.pad(
                image[:, :, i], ((top, bottom), (left, right)),
                mode='constant', constant_values=constant)
        padded_image = np.transpose(
            padded_image, axes=(1, 2, 0)).astype(np.uint8)

    shapes = [
        # imgsz (model input shape) [height, width]
        [padded_image.shape[0], padded_image.shape[1]],
        # ratio_pad [[scale y, scale x], [pad w, pad h]]
        [[scale, scale], [left, top]]
    ]
    return padded_image, shapes


def letterbox_hal(
    image: TensorImage,
    dst: TensorImage,
) -> list:
    """
    Applies the letterbox image transformations using HAL.

    Parameters
    ----------
    image: TensorImage
        An RGBA tensor image loaded using the HAL.
    dst: TensorImage
        The destination tensor image after letterbox transformation.

    Returns
    -------
    label_ratio: list
        Scaling factors (width, height) applied to original boxes.
    shapes: list
        This is used to scale the bounding boxes of the ground
        truth and the model detections based on the letterbox
        transformation. Tuple containing padded image size, scale ratio,
        and padding offsets.
        [[pad image height, pad image width],
        [[scale_y, scale_x], [pad x, pad y]]].
    """

    try:
        import edgefirst_hal  # type: ignore  # pylint: disable=redefined-outer-name
    except ImportError as exc:
        raise ImportError(
            "EdgeFirst HAL is needed to perform letterbox using hal."
        ) from exc

    ratio = min(dst.height / image.height, dst.width / image.width)
    height = image.height * ratio
    width = image.width * ratio
    top = round((dst.height - height) / 2)
    left = round((dst.width - width) / 2)
    height = round(height)
    width = round(width)

    if CONVERTER is None:
        raise ImportError(
            "EdgeFirst HAL converter is not available for letterbox.")
    CONVERTER.convert(image, dst,
                      dst_crop=edgefirst_hal.Rect(left, top, width, height),
                      dst_color=[114, 114, 114, 255])

    shapes = [
        # imgsz (model input shape) [height, width]
        [dst.height, dst.width],
        # ratio_pad [[scale y, scale x], [pad w, pad h]]
        [[ratio, ratio], [left, top]]
    ]

    return shapes


def preprocess_hal(
    image: TensorImage,
    shape: tuple,
    input_type: np.dtype,
    input_buffer: TensorImage,
    transpose: bool = False,
    input_tensor: Optional[Callable] = None,
    preprocessing: str = "letterbox",
    normalization: str = "unsigned",
    quantization: Optional[tuple] = None,
    visualize: bool = False
) -> Tuple[np.ndarray, np.ndarray, list, tuple]:
    """
    Optimized input preprocessing using the HAL.

    Parameters
    ----------
    image: TensorImage
        The image input to preprocess.
    shape: tuple
        The model input shape. This can either be formatted as
        (batch size, channels, height, width) or
        (batch size, height, width, channels).
    input_type: np.dtype
        The input datatype of the model.
    input_buffer: TensorImage
        Destination tensor for placing the image transformations.
    transpose: bool
        Condition of whether to transpose the image or not. This
        is True for input shapes with channels first. Otherwise it is False.
    input_tensor: Optional[Callable]
        Callable function for retrieving the input view tensor
        from the model for directly copying the input tensor
        into the model such as the case for TFLite.
    preprocessing: str
        The type of image preprocessing to apply. By default 'letterbox'
        is used. However, 'resize' or 'pad' are possible variations.
    normalization: str
        The type of image normalization to apply. Default is set to
        'unsigned'. However 'signed', 'raw', and 'imagenet' are possible
        values.
    quantization: Optional[tuple]
        The quantization parameters of the input containing
        the (scale, zero point) values.
    visualize: bool
        When visualizing the model outputs, this requires a second
        copy of the transformed image. By default,
        visualization is set to False.

    Returns
    -------
    image: np.ndarray
        The image input after being preprocessed.
    visual_image: np.ndarray
        The image that is used for visualization post
        letterbox, padding, resize transformations.
    shapes: list
        This is used to scale the bounding boxes of the ground
        truth and the model detections based on the letterbox/padding
        transformation.

        .. code-block:: python

            [[input_height, input_width],
            [[scale_y, scale_x], [pad_w, pad_h]]]
    image_shape: tuple
        The original image dimensions.
    """

    try:
        import edgefirst_hal  # type: ignore # pylint: disable=redefined-outer-name
    except ImportError as exc:
        raise ImportError(
            "EdgeFirst HAL is needed to perform preprocessing using hal."
        ) from exc

    # Fetch only (height, width) from the shape.
    # Format for YUYV, RGB, and RGBA
    if shape[-1] in [2, 3, 4]:
        channels = shape[-1]
        input_height, input_width = shape[1:3]
    else:
        channels = shape[1]
        input_height, input_width = shape[2:4]

    height, width = image.height, image.width
    shapes = [
        # imgsz (model input shape) [height, width]
        [int(input_height), int(input_width)],
        [[float(input_height / height), float(input_width / width)],
         [0.0, 0.0]]  # ratio_pad [image_scale, [pad w, pad h]]
    ]

    if preprocessing == "letterbox":
        shapes = letterbox_hal(image, input_buffer)
    elif preprocessing == "pad":
        raise NotImplementedError("Padding with HAL is not yet implemented.")
    else:
        if CONVERTER is None:
            raise ImportError(
                "EdgeFirst HAL converter is not available for resizing.")
        CONVERTER.convert(image, input_buffer)

    if transpose:
        image = np.zeros(
            (channels,
             input_buffer.height,
             input_buffer.width),
            dtype=input_type)
    else:
        image = np.zeros(
            (input_buffer.height,
             input_buffer.width,
             channels),
            dtype=input_type)

    if input_type in [np.float16, np.float32]:
        if normalization == "unsigned":
            normalization = edgefirst_hal.Normalization.UNSIGNED
        elif normalization == "signed":
            normalization = edgefirst_hal.Normalization.SIGNED
        elif normalization == "raw":
            normalization = edgefirst_hal.Normalization.RAW
        elif normalization == "imagenet":
            raise NotImplementedError(
                "ImageNet normalization is currently not implemented in HAL.")
        else:
            normalization = edgefirst_hal.Normalization.DEFAULT
    else:
        normalization = edgefirst_hal.Normalization.DEFAULT

    zero_point = None
    if quantization is not None:
        if input_type == np.int8:
            zero_point = abs(quantization[-1])
    # Directly copy the input tensor into the model for TFLite.
    if input_tensor is not None:
        input_buffer.normalize_to_numpy(input_tensor()[0, :, :, :],
                                        normalization=normalization,
                                        zero_point=zero_point)
    else:
        input_buffer.normalize_to_numpy(image,
                                        normalization=normalization,
                                        zero_point=zero_point)
    visual_image = None
    if visualize:
        if transpose:
            visual_image = np.zeros(
                (channels, input_buffer.height, input_buffer.width),
                dtype=np.uint8)
            input_buffer.normalize_to_numpy(visual_image)
            visual_image = np.transpose(visual_image, axes=[1, 2, 0])
        else:
            visual_image = np.zeros(
                (input_buffer.height, input_buffer.width, channels),
                dtype=np.uint8)
            input_buffer.normalize_to_numpy(visual_image)
    image = image[None]
    return image, visual_image, shapes, (height, width)


def preprocess_native(
    image: np.ndarray,
    shape: tuple,
    input_type: np.dtype,
    transpose: bool = False,
    input_tensor: Optional[Callable] = None,
    preprocessing: str = "letterbox",
    normalization: str = "unsigned",
    quantization: Optional[tuple] = None,
    backend: str = "hal",
) -> Tuple[np.ndarray, np.ndarray, list, tuple]:
    """
    Standard preprocessing method. Default parameters are based on
    Ultralytics defaults.

    Parameters
    ----------
    image: np.ndarray
        The image input to preprocess.
    shape: tuple
        The model input shape. This can either be formatted as
        (batch size, channels, height, width) or
        (batch size, height, width, channels).
    input_type: np.dtype
        The input datatype of the model.
    transpose: bool
        Condition of whether to transpose the image or not. This
        is True for input shapes with channels first. Otherwise it is False.
    input_tensor: Optional[Callable]
        Callable function for retrieving the input view tensor
        from the model for directly copying the input tensor
        into the model such as the case for TFLite.
    preprocessing: str
        The type of image preprocessing to apply. By default 'letterbox'
        is used. However, 'resize' or 'pad' are possible variations.
    normalization: str
        The type of image normalization to apply. Default is set to
        'unsigned'. However 'signed', 'raw', and 'imagenet' are possible
        values.
    quantization: Optional[tuple]
        The quantization parameters of the input containing
        the (scale, zero point) values.
    backend: str
        Specify the backend library for letterboxing the
        image from the options "opencv", "pillow".

    Returns
    -------
    image: np.ndarray
        The image input after being preprocessed.
    visual_image: np.ndarray
        The image that is used for visualization post
        letterbox, padding, resize transformations.
    shapes: list
        This is used to scale the bounding boxes of the ground
        truth and the model detections based on the letterbox/padding
        transformation.

        .. code-block:: python

            [[input_height, input_width],
            [[scale_y, scale_x], [pad_w, pad_h]]]
    image_shape: tuple
        The original image dimensions.
    """

    # Fetch only (height, width) from the shape.
    # Format for YUYV, RGB, and RGBA
    if shape[-1] in [2, 3, 4]:
        channel = shape[-1]
        shape = shape[1:3]
    else:
        channel = shape[1]
        shape = shape[2:4]
        # Transpose the image to meet requirements of the channel order.

    transformer = None  # Function that transforms image formats.
    if channel == 2:
        transformer = rgb2yuyv
    elif channel == 4:
        transformer = rgb2rgba

    height, width = image.shape[0:2]

    shapes = [
        shape,  # imgsz (model input shape) [height, width]
        [[shape[0] / height, shape[1] / width],
         [0.0, 0.0]]  # ratio_pad [image_scale, [pad w, pad h]]
    ]

    if backend == "opencv":
        # OpenCV reads images into BGR by default.
        image = bgr2rgb(image)

    if preprocessing == "letterbox":
        image, shapes = letterbox_native(
            image, new_shape=shape, backend=backend)
    elif preprocessing == "pad":
        image, shapes = pad(image, shape, backend=backend)
    else:
        image = resize(image, (shape[1], shape[0]), backend=backend)

    visual_image = image
    if preprocessing == "pad":
        visual_image = bgr2rgb(visual_image)

    # Convert image format to either YUYV, RGBA or keep as RGB.
    image = transformer(image, backend=backend) if transformer else image

    # Expects batch size, channel, height, width.
    if transpose:
        image = np.transpose(image, axes=[2, 0, 1])

    # Handle full/half precision input types.
    if input_type in [np.float16, np.float32]:
        image = image_normalization(image, normalization, input_type)

    # For quantized models, run input quantization parameters.
    if quantization is not None:
        if input_type == np.int8:
            zero_point = abs(quantization[-1])
            image = (image.astype(np.int16) - zero_point).astype(np.int8)

    image = image[None]
    # Directly copy the input tensor into the model for TFLite.
    if input_tensor is not None:
        np.copyto(input_tensor(), image)

    return image, visual_image, shapes, (height, width)
