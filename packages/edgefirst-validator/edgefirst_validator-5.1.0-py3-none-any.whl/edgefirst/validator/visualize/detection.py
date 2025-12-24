"""
Defines the DetectionDrawer class for visualizing detection bounding boxes
on images, indicating validation results such as true positives,
false positives, and false negatives.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple, Union

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from edgefirst.validator.visualize import Colors

if TYPE_CHECKING:
    from edgefirst.validator.datasets import DetectionInstance
    from edgefirst.validator.evaluators import Matcher


class DetectionDrawer:
    """
    This class draws detection bounding boxes on the image showing
    the validation results from the ground truth and model prediction
    matches.
    """

    def __init__(self):

        self.messages = {
            "Match": "%s %.2f%% %.2f",  # Format (label, score, IoU)
            "Match Loc": "LOC: %s %.2f%% %.2f",  # Format (label, score, IoU)
            "Loc": "LOC: %s %.2f%%",  # Format (label, score)
            "Clf": "CLF: %s %.2f%% %.2f",  # Format (label, score, IoU)
            "Basic": "%s %.2f%%",  # Format (label, score)
        }

        self.font = ImageFont.load_default()
        self.image_draw: ImageDraw.ImageDraw = None
        self.colors = Colors()

    def draw_2d_gt_boxes(
        self,
        image: Union[Image.Image, np.ndarray],
        gt_instance: DetectionInstance,
        method: str = "edgefirst",
        labels: Optional[list] = None,
    ) -> Image.Image:
        """
        Draw the 2D ground truth bounding boxes on the image.

        Parameters
        ----------
        image: Union[Image.Image, np.ndarray]
            The image to overlay with boxes and texts.
        gt_instance: DetectionInstance
            This is the ground truth instance containing the
            bounding boxes and their labels as normalized (xyxy) format.
        method: str
            The type of visualization method. By default, visualization
            of "edgefirst" validation results are used. Otherwise,
            "ultralytics" visualizations are used.
        labels: Optional[list]
            A list of unique string labels to designate
            a specific color for the label.

        Returns
        -------
        Image.Image
            The image with 2D ground truth boxes.
        """
        if isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        self.image_draw = ImageDraw.Draw(image)

        # Draw ground truths
        for label, bounding_box in zip(gt_instance.labels, gt_instance.boxes):
            if method == "edgefirst":
                box_position = self.format_box_position(
                    box_position=bounding_box
                )
                self.draw_2d_bounding_box(box_position)
                color = "RoyalBlue"
            else:
                if labels is not None:
                    color = self.colors(labels.index(label))
                else:
                    color = self.colors(0)
                box_position = self.format_box_position(
                    box_position=bounding_box
                )
                self.draw_2d_bounding_box(
                    box_position=box_position,
                    color=color
                )

            text = str(label)
            background_position, text_position =\
                self.position_2d_text_background(
                    text,
                    (box_position[0][0], box_position[1][1]),
                    box_position,
                    portion=0.10
                )
            self.draw_text(
                text,
                text_position,
                background_position=background_position,
                background_color=color
            )

        return image

    def draw_2d_dt_boxes(
        self,
        image: Union[Image.Image, np.ndarray],
        dt_instance: DetectionInstance,
        gt_instance: Optional[DetectionInstance] = None,
        matcher: Optional[Matcher] = None,
        validation_iou: float = 0.50,
        validation_score: float = 0.25,
        method: str = "edgefirst",
        labels: Optional[list] = None
    ) -> Image.Image:
        """
        Draw the 2D detection bounding boxes on the image.

        Parameters
        ----------
        image: Union[Image.Image, np.ndarray]
            The image to overlay with boxes and texts.
        dt_instance: Instance
            This is the prediction instance containing the bounding boxes
            and their scores and labels.
        gt_instance: Optional[DetectionInstance]
            This is the ground truth instance containing the
            bounding boxes and their labels as normalized (xyxy) format.
        matcher: Optional[Matcher]
            This contains the bounding box matches from EdgeFirst validation
            for assigning colors to true positives, false positives, and
            false negatives.
        validation_iou: float
            This is the validation IoU threshold which determines the point
            between classifying a prediction bounding box as either a
            true positive or a localization false positive.
        validation_score: float
            Filter to visualize the predictions with confident scores
            only, score greater than this threshold set.
        method: str
            The type of visualization method. By default, visualization
            of "edgefirst" validation results are used. Otherwise,
            "ultralytics" visualizations are used.
        labels: Optional[list]
            A list of unique string labels to designate
            a specific color for the label.

        Returns
        -------
        Image.Image
            The image with 2D prediction boxes.
        """
        if isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        self.image_draw = ImageDraw.Draw(image)

        # Visualize EdgeFirst results.
        if method == "edgefirst":
            # Draw extra predictions
            for extra in matcher.index_unmatched_dt:
                dt_label = dt_instance.labels[extra]
                score = dt_instance.scores[extra]
                if score < validation_score:
                    continue

                score *= 100
                text = self.messages["Loc"] % (dt_label, score)

                bounding_box = dt_instance.boxes[extra]
                box_position = self.format_box_position(bounding_box)
                self.draw_2d_bounding_box(box_position, "OrangeRed")

                background_position, text_position = self.position_2d_text_background(
                    text,
                    (box_position[0][0], box_position[0][1]),
                    box_position
                )
                self.draw_text(
                    text,
                    text_position,
                    background_position=background_position,
                    background_color="OrangeRed"
                )

            # Draw matches
            for match in matcher.index_matches:
                dt_label = dt_instance.labels[match[0]]
                gt_label = gt_instance.labels[match[1]]
                iou = matcher.iou_list[match[0]]
                score = dt_instance.scores[match[0]]
                if score < validation_score:
                    continue

                score *= 100
                text, color = self.classify_text(
                    gt_label, dt_label, score, iou, validation_iou)

                bounding_box = dt_instance.boxes[match[0]]
                box_position = self.format_box_position(bounding_box)
                self.draw_2d_bounding_box(box_position, color)

                background_position, text_position = self.position_2d_text_background(
                    text,
                    (box_position[0][0], box_position[0][1]),
                    box_position
                )
                self.draw_text(
                    text,
                    text_position,
                    background_position=background_position,
                    background_color=color
                )

        # Visualize Ultralytics results.
        else:
            if len(dt_instance.boxes):
                filt = dt_instance.scores >= validation_score
                dt_boxes = dt_instance.boxes[filt]
                dt_labels = dt_instance.labels[filt]
                dt_scores = dt_instance.scores[filt]
            else:
                dt_boxes = []
                dt_labels = []
                dt_scores = []

            # Draw ground truths
            for box, label, score in zip(dt_boxes, dt_labels, dt_scores):
                if labels is not None:
                    color = self.colors(labels.index(label))
                else:
                    color = self.colors(0)

                box_position = self.format_box_position(box_position=box)
                self.draw_2d_bounding_box(
                    box_position=box_position,
                    color=color
                )

                text = f"{label} {score:.2f}"
                background_position, text_position =\
                    self.position_2d_text_background(
                        text,
                        (box_position[0][0], box_position[1][1]),
                        box_position,
                        portion=0.10
                    )
                self.draw_text(
                    text,
                    text_position,
                    background_position=background_position,
                    background_color=color
                )

        return image

    def draw_2d_bounding_boxes(
        self,
        gt_instance: DetectionInstance,
        dt_instance: DetectionInstance,
        matcher: Optional[Matcher] = None,
        validation_iou: float = 0.50,
        validation_score: float = 0.25,
        method: str = "edgefirst",
        labels: Optional[list] = None
    ) -> Image.Image:
        """
        This is the process for drawing all the 2D bounding boxes in an image.
        This includes the ground truth and the prediction bounding boxes with
        respective colors based on their classifications as true positives,
        false positives, or false negatives.

        Parameters
        ----------
        gt_instance: DetectionInstance
            This is the ground truth instance containing the
            bounding boxes and their labels as normalized (xyxy) format.
        dt_instance: DetectionInstance
            This is the prediction instance containing the bounding boxes
            and their scores and labels.
        matcher: Optional[Matcher]
            This contains the bounding box matches from EdgeFirst validation
            for assigning colors to true positives, false positives, and
            false negatives.
        validation_iou: float
            This is the validation IoU threshold which determines the point
            between classifying a prediction bounding box as either a
            true positive or a localization false positive.
        validation_score: float
            Filter to visualize the predictions with confident scores
            only, score greater than this threshold set.
        method: str
            The type of visualization method. By default, visualization
            of "edgefirst" validation results are used. Otherwise,
            "ultralytics" visualizations are used.
        labels: Optional[list]
            A list of unique string labels to designate
            a specific color for the label.

        Returns
        -------
        Image.Image
            The image with 2D prediction and ground truth boxes.
        """
        if method == "edgefirst":
            image = Image.fromarray(gt_instance.visual_image)
            image = self.draw_2d_gt_boxes(
                image=image,
                gt_instance=gt_instance
            )
            image = self.draw_2d_dt_boxes(
                image=image,
                dt_instance=dt_instance,
                gt_instance=gt_instance,
                matcher=matcher,
                validation_iou=validation_iou,
                validation_score=validation_score,
            )
        else:
            image = gt_instance.visual_image
            gt_image = self.draw_2d_gt_boxes(
                image=image.copy(),
                gt_instance=gt_instance,
                method="ultralytics",
                labels=labels
            )
            dt_image = self.draw_2d_dt_boxes(
                image=image.copy(),
                dt_instance=dt_instance,
                validation_score=validation_score,
                method="ultralytics",
                labels=labels
            )

            image = Image.new(
                'RGB',
                (gt_image.width + dt_image.width, dt_image.height))
            image.paste(gt_image, (0, 0))
            image.paste(dt_image, (dt_image.width, 0))

            draw_text = ImageDraw.Draw(image)
            draw_text.text(
                (0, 0),
                "GROUND TRUTH",
                font=self.font,
                align='left',
                fill=(0, 0, 0)
            )
            draw_text.text(
                (dt_image.width, 0),
                "MODEL PREDICTION",
                font=self.font,
                align='left',
                fill=(0, 0, 0)
            )
        return image

    def draw_rect(
        self,
        selected_corners: np.ndarray,
        color: str,
        width: int = 2
    ):
        """
        This is primarily used for drawing 3D bounding boxes which
        consists of two rectangles and four lines.

        Parameters
        ----------
        selected_corners: np.ndarray
            This contains the corners of the 3D bounding box with shape
            (3,8) representing the (x,y,z) eight corners of a 3D box.
        color: str
            The color to use for the line.
        width: int
            This is the width of the line forming the rectangle.
        """
        prev = selected_corners[-1]
        for corner in selected_corners:
            self.image_draw.line(
                ((int(prev[0]), int(prev[1])),
                 (int(corner[0]), int(corner[1]))),
                fill=color,
                width=width
            )
            prev = corner

    def draw_2d_bounding_box(
        self,
        box_position: tuple,
        color: str = "RoyalBlue",
        width: int = 3
    ):
        """
        Draws a 2D bounding box on the image.

        Parameters
        ----------
        box_position: tuple
            ((x1, y1), (x2, y2)) position of the box.
        color: str
            The color of the bounding box. Typically,
            ground truth/false negatives are set to "RoyalBlue",
            false positives are set to "OrangeRed",
            true positives are set to "LimeGreen".
        width: int
            The width of the line to draw the bounding boxes.
        """
        self.image_draw.rectangle(
            box_position,
            outline=color,
            width=width
        )

    def draw_text(
        self,
        text: str,
        text_position: tuple,
        color: str = "black",
        align: str = "left",
        background_position: Optional[tuple] = None,
        background_color: str = "RoyalBlue"
    ):
        """
        Write text on the image and will also optionally
        draw a 2D box overlay as the background of the text
        to make it more visible.

        Parameters
        ----------
        text: str
            The text to write on the image.
        text_position: tuple
            This is the (x, y) position on the image to write the text.
        color: str
            This is the color of the text.
        align: str
            This is the text alignment.
        background_position: Optional[tuple]
            This is the ((x1, y1), (x2, y2)) position to draw the
            background box of the text.
        background_color: str
            This is the color of the background. It is recommended to align the
            colors with the bounding boxes to make it clear which text
            corresponds to which.
        """
        if background_position:
            self.image_draw.rectangle(
                background_position,
                fill=background_color
            )
        self.image_draw.text(
            text_position,
            text,
            font=self.font,
            align=align,
            fill=color
        )

    def get_text_dimensions(self, text: str) -> Tuple[int, int]:
        """
        Retrieve the text dimensions which varies
        based on the Pillow version used.

        Parameters
        ----------
        text: str
            This is the text being drawn.

        Returns
        -------
        width: int
            The width of the text in pixels.
        height: int
            The height of the text in pixels.
        """
        if hasattr(self.font, 'getsize'):  # works on older Pillow versions < 10.
            text_width, text_height = self.font.getsize(text)
        else:
            # newer Pillow versions >= 10.
            (text_width, text_height), _ = self.font.font.getsize(text)
        return (text_width, text_height)

    def position_2d_text_background(
        self,
        text: str,
        text_position: tuple,
        box_position: tuple,
        portion: float = 0.25
    ) -> Tuple[tuple, tuple]:
        """
        This positions the background of the text to make
        it aligned with the 2D bounding box.

        Parameters
        ----------
        text: str
            The text that will be drawn on the image.
        text_position: tuple
            This contains the (x, y) position of the text.
        box_position: tuple
            This contain the ((x1, y1), (x2, y2)) position
            of the 2D bounding box.
        portion: float
            This is the percentage of the bounding box width to
            resize the font.

        Returns
        -------
        box_position: tuple
            This is the ((x1, y1), (x2, y2)) position
            of the text background.
        text_position: tuple
            This is the (x,y) position of the text
            aligned to the background.
        """
        text_width, text_height = self.get_text_dimensions(text)

        # font_size = 10
        # while (text_width < int(portion*(box_position[1][1] - box_position[0][1]))):
        #     self.font = ImageFont.load_default(size=font_size)
        #     text_width, text_height = self.get_text_dimensions(text)
        #     font_size += 1

        box_text_x1 = box_position[0][0]
        box_text_x2 = box_text_x1 + text_width

        # This suggests a ground truth text is being drawn where the label is
        # located in the bottom left of the bounding box.
        if text_position[1] > box_position[0][1]:
            # Keep the text within the bounding box.
            box_text_y1 = box_position[1][1] - text_height
            # The larger the text height, the large the offset to center.
            text_position = (
                text_position[0], text_position[1] - int(1.2 * text_height))
        # A prediction text is being drawn where the labels is located
        # in the top left of the bounding box.
        else:
            box_text_y1 = box_position[0][1]
            text_position = (
                text_position[0], text_position[1] - int(0.2 * text_height))

        box_text_y2 = box_text_y1 + text_height
        return ((box_text_x1, box_text_y1),
                (box_text_x2, box_text_y2)), text_position

    def classify_text(
        self,
        gt_label: str,
        dt_label: str,
        score: float,
        iou: float,
        validation_iou: float
    ) -> Tuple[str, str]:
        """
        Determine the appropriate text to display and the color
        to use based on the parameters provided.

        Parameters
        ----------
        gt_label: str
            This is the ground truth label.
        dt_label: str
            This is the prediction label.
        score: float
            This is the prediction score.
        iou: float
            This is the IoU between the ground truth and the prediction.
        validation_iou: float
            This IoU is the threshold of classifying predictions as either
            true positives or localization false positives.

        Returns
        -------
        text: str
            This is the chosen formatted text to display.
        color: str
            This is the chosen color to use for the bounding box.
        """
        # True Positives.
        if dt_label == gt_label:
            text = self.messages["Match"] % (dt_label, score, iou)
            color = "LimeGreen"
        # Classification False Positives.
        else:
            text = self.messages["Clf"] % (dt_label, score, iou)
            color = "OrangeRed"

        # Localization False Positives.
        if iou <= validation_iou:
            text = self.messages["Match Loc"] % (dt_label, score, iou)
            color = "OrangeRed"

        # Any unmatched or sole ground truths are false negatives.
        return text, color

    @staticmethod
    def format_box_position(
        box_position, width: int = 1, height: int = 1
    ) -> tuple:
        """
        This denormalizes the bounding box coordinates
        and formats it into a tuple.

        Parameters
        ----------
        box_position: list or np.ndarray
            This is a normalized bounding box [xmin, ymin, xmax, ymax].
        width: int
            This is the width of the image to denormalize the box.
        height: int
            This is the height of the image to denormalize the box.

        Returns
        -------
        tuple
            Non normalized (pixels) ((xmin, ymin), (xmax, ymax)).
        """
        p1 = (box_position[0] * width, box_position[1] * height)
        p2 = (box_position[2] * width, box_position[3] * height)
        return (p1, p2)
