"""
Defines the Colors and SegmentationDrawer classes for visualizing
segmentation masks on images, using the Ultralytics color palette.
"""

from typing import Optional

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from edgefirst.validator.datasets import SegmentationInstance


class Colors:
    """
    Ultralytics color palette for visualization and plotting.
    Source: https://github.com/ultralytics/ultralytics/blob/main/ultralytics/utils/plotting.py#L19

    This class provides methods to work with the Ultralytics color palette,
    including converting hex color codes to RGB values and accessing predefined
    color schemes for object detection and pose estimation.

    Attributes
    ----------
    palette: List[tuple]
        List of RGB color tuples for general use.
    n: int
        The number of colors in the palette.
    pose_palette: np.ndarray
        A specific color palette array for pose estimation with dtype np.uint8.

    Examples
    --------
    >>> from ultralytics.utils.plotting import Colors
    >>> colors = Colors()
    >>> colors(5, True)  # Returns BGR format: (221, 111, 255)
    >>> colors(5, False)  # Returns RGB format: (255, 111, 221)
    """

    def __init__(self):
        """
        Initialize colors as hex = matplotlib.colors.TABLEAU_COLORS.values().
        """
        hexs = (
            "042AFF",
            "0BDBEB",
            "F3F3F3",
            "00DFB7",
            "111F68",
            "FF6FDD",
            "FF444F",
            "CCED00",
            "00F344",
            "BD00FF",
            "00B4FF",
            "DD00BA",
            "00FFFF",
            "26C000",
            "01FFB3",
            "7D24FF",
            "7B0068",
            "FF1B6C",
            "FC6D2F",
            "A2FF0B",
        )
        self.palette = [self.hex2rgb(f"#{c}") for c in hexs]
        self.n = len(self.palette)
        self.pose_palette = np.array(
            [
                [255, 128, 0],
                [255, 153, 51],
                [255, 178, 102],
                [230, 230, 0],
                [255, 153, 255],
                [153, 204, 255],
                [255, 102, 255],
                [255, 51, 255],
                [102, 178, 255],
                [51, 153, 255],
                [255, 153, 153],
                [255, 102, 102],
                [255, 51, 51],
                [153, 255, 153],
                [102, 255, 102],
                [51, 255, 51],
                [0, 255, 0],
                [0, 0, 255],
                [255, 0, 0],
                [255, 255, 255],
            ],
            dtype=np.uint8,
        )

    def __call__(self, i: int, bgr: bool = False) -> tuple:
        """
        Convert hex color codes to RGB values.

        Parameters
        ----------
        i : int
            Index of the color in the palette.
        bgr : bool, optional
            If True, return color in BGR format. Default is False.

        Returns
        -------
        tuple
            A 3-element tuple representing the RGB or BGR color.
        """
        c = self.palette[int(i) % self.n]
        return (c[2], c[1], c[0]) if bgr else c

    @staticmethod
    def hex2rgb(h: str) -> tuple:
        """
        Convert hex color codes to RGB values (i.e. default PIL order).

        Parameters
        ----------
        h : str
            Hex color string (e.g. "#FF00AA").

        Returns
        -------
        tuple
            A 3-element tuple representing the RGB color.
        """
        return tuple(int(h[1 + i: 1 + i + 2], 16) for i in (0, 2, 4))


class SegmentationDrawer:
    """
    This class draws segmentation masks from the ground truth and
    model predictions on the image.
    """

    def __init__(self):
        self.font = ImageFont.load_default()
        self.colors = Colors()

    def mask2maskimage(
        self,
        gt_instance: SegmentationInstance,
        dt_instance: SegmentationInstance,
        semantic: bool = True,
        background_index: int = 0
    ) -> Image.Image:
        """
        Masks the original image and returns the original image
        with mask prediction on the left and mask ground truth on the right.
        This method is used for drawing semantic segmentation masks as
        the input.

        Parameters
        ----------
        gt_instance: SegmentationInstance
            This object contains the ground truth mask.
        dt_instance: SegmentationInstance
            This object contains the predictions mask.
        semantic: bool
            The condition that specifies whether or not the
            segmentation masks are semantic or instance.
        background_index: int
            The integer representing the background class in the mask.

        Returns
        -------
        Image.Image
            The image with drawn masks where on the right pane
            shows the ground truth mask and on the left pane shows
            the prediction mask.
        """

        gt_image = Image.fromarray(np.uint8(gt_instance.visual_image))
        if dt_instance.visual_image is not None:
            dt_image = Image.fromarray(np.uint8(dt_instance.visual_image))
        else:
            dt_image = gt_image

        gt_mask = gt_instance.mask
        dt_mask = dt_instance.mask

        # Create image from numpy masks.
        mask_gt = self.mask2image(gt_mask,
                                  labels=gt_instance.labels,
                                  semantic=semantic,
                                  background_index=background_index)
        mask_dt = self.mask2image(dt_mask,
                                  labels=dt_instance.labels,
                                  semantic=semantic,
                                  background_index=background_index)

        image_gt = gt_image.convert("RGBA")
        image_dt = dt_image.convert("RGBA")
        mask_image_gt = Image.alpha_composite(image_gt, mask_gt).convert("RGB")
        mask_image_dt = Image.alpha_composite(image_dt, mask_dt).convert("RGB")

        dst = Image.new(
            'RGB',
            (mask_image_dt.width + mask_image_gt.width, mask_image_dt.height))
        dst.paste(mask_image_gt, (0, 0))
        dst.paste(mask_image_dt, (mask_image_dt.width, 0))

        draw_text = ImageDraw.Draw(dst)
        draw_text.text(
            (0, 0),
            "GROUND TRUTH",
            font=self.font,
            align='left',
            fill=(0, 0, 0)
        )
        draw_text.text(
            (mask_image_dt.width, 0),
            "MODEL PREDICTION",
            font=self.font,
            align='left',
            fill=(0, 0, 0)
        )
        return dst

    def mask2image(
        self,
        mask: np.ndarray,
        labels: Optional[list] = None,
        constant: Optional[int] = None,
        semantic: bool = True,
        alpha: int = 130,
        background_index: int = 0
    ) -> Image.Image:
        """
        Transform a NumPy array of mask into an RGBA image.

        Parameter
        ---------
        mask: np.ndarray
            Array (height, width) representing the mask.
        labels: Optional[list]
            For instance segmentation, provides the integer label
            for each mask.
        constant: Optional[int]
            Specify a constant to color the mask with a single color
            based on the constant specified which is the index to the
            list of colors. By default, None is provided and colors
            the masks based on the unique values in the mask.
        semantic: bool
            The condition that specifies whether or not the
            segmentation masks are semantic or instance.
        alpha: int
            The constant value for the alpha channel.
        background_index: int
            The integer representing the background class in the mask.
            This is typically used for semantic segmentation.

        Returns
        -------
        Image.Image
            The masked image.
        """
        # Transform dimension of masks from a 2D numpy array to 4D into RGBA.
        if len(mask.shape) > 2:
            _, height, width = mask.shape
        else:
            height, width = mask.shape
        mask_4_channels = np.zeros((height, width, 4), dtype=np.uint8)

        # Used for drawing an instance segmentation mask on the image
        # based on the constance assigned for the mask label.
        if constant:
            # Assign all classes with color white. An instance segmentation
            # mask is binary which has 0 and 1 values.
            mask_4_channels[mask != background_index] = 255
            # Temporarily unpack the bands for readability.
            red, green, blue, _ = mask_4_channels.T
            # Areas of all classes.
            u_areas = (red == 255) & (blue == 255) & (green == 255)
            # Color all classes with the constant value.
            mask_4_channels[..., :][u_areas.T] = np.append(
                self.colors(constant), alpha)
        else:
            # For instance segmentation, the labels should be provided.
            # Otherwise, the labels are taken from the unique values
            # in the mask for semantic segmentation.
            if semantic:
                labels = np.sort(np.unique(mask))
                for label in labels:
                    if label != background_index:
                        # Designate a color for each class.
                        mask_4_channels[mask == label] = \
                            np.append(self.colors(label), alpha)
            else:
                for label, m in zip(labels, mask):
                    # Designate a color for each class.
                    mask_4_channels[m > background_index] = np.append(
                        self.colors(label), alpha)

        # Convert array to image object for image processing.
        return Image.fromarray(mask_4_channels.astype(np.uint8))
