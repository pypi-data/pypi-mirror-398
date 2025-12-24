"""
Implementations for reading Darknet datasets.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Optional, Tuple, List

import numpy as np

from edgefirst.validator.datasets import (SegmentationInstance,
                                          DetectionInstance,
                                          MultitaskInstance)
from edgefirst.validator.datasets import Dataset
from edgefirst.validator.datasets.utils.annotation_transforms import (format_segments,
                                                                      scale)
from edgefirst.validator.datasets.utils.image_transforms import (preprocess_native,
                                                                 preprocess_hal)
from edgefirst.validator.publishers.utils.logger import logger
from edgefirst.validator.datasets.utils.readers import (read_segmentation_text_file,
                                                        read_detection_text_file)
from edgefirst.validator.datasets.utils.fetch import (validate_dataset_source,
                                                      get_annotation_files,
                                                      classify_dataset,
                                                      get_image_files,
                                                      get_shape)

if TYPE_CHECKING:
    from edgefirst.validator.evaluators import (DatasetParameters,
                                                TimerContext, StageTracker)


class DarkNetDataset(Dataset):
    """
    Reads Darknet format datasets.
    Dataset format should be the same as coco128 at
    `https://www.kaggle.com/datasets/ultralytics/coco128`.
    Optionally, the images and text annotations can be in the same directory.

    Parameters
    ----------
    source: str
        The path to the source dataset.
    parameters: DatasetParameters
        This contains dataset parameters set from the command line.
    timer: TimerContext
        A timer object for handling validation timings for the model.
    stage_tracker: StageTracker
        The object used for tracking and displaying stages.
    info_dataset: Optional[dict]
        Contains information such as:

            .. code-block:: python

                {
                    "classes": [list of unique labels],
                    "validation":
                    {
                        "images: 'path to the images',
                        "annotations": 'path to the annotations'
                    }
                }

        *Note: the classes are optional and the path to the images
        and annotations can be the same.*

    Raises
    ------
    ValueError
        Raised if the provided path to the images or
        annotations is not a string.
    EmptyDatasetException
        Raised if the provided path to the images or
        text files does not contain any image files or
        text files respectively.
    """

    def __init__(
        self,
        source: str,
        parameters: DatasetParameters,
        timer: TimerContext,
        stage_tracker: StageTracker,
        info_dataset: Optional[dict] = None,
    ):
        super(DarkNetDataset, self).__init__(
            source=source,
            parameters=parameters,
            timer=timer,
            stage_tracker=stage_tracker,
            info_dataset=info_dataset
        )

        if self.info_dataset is None:
            self.info_dataset = classify_dataset(source)

        if self.info_dataset is not None:
            if "dataset" in self.info_dataset.keys():
                images_path = self.info_dataset.get(
                    "dataset", {}).get('validation', {}).get('images', None)
                annotations_path = self.info_dataset.get(
                    "dataset", {}).get('validation', {}).get('annotations', None)
            else:
                images_path = self.info_dataset.get(
                    'validation', {}).get('images', None)
                annotations_path = self.info_dataset.get(
                    'validation', {}).get('annotations', None)
        else:
            raise ValueError(
                "The dataset information could not be parsed. " +
                "Please verify the dataset.yaml has the proper format.")

        self.image_source = validate_dataset_source(images_path)
        self.annotation_source = validate_dataset_source(annotations_path)

        labels = self.info_dataset.get('classes', None)
        if labels is not None:
            self.parameters.labels = [str(label) for label in labels]

        self.images = get_image_files(self.image_source)
        self.annotations = get_annotation_files(self.annotation_source)
        # This is used to map the image name to the annotation file.
        self.annotation_extension = os.path.splitext(self.annotations[0])[1]

    def collect_samples(self) -> List[tuple]:
        """
        Collect all samples in the dataset.

        Returns
        -------
        List[tuple]
            One instance contains the
            (path to the image, path to the annotation).
        """
        missing_annotations = 0
        samples = list()
        for image_path in self.images:
            annotation_path = os.path.join(
                self.annotation_source,
                os.path.splitext(os.path.basename(image_path))[0] +
                self.annotation_extension)

            if os.path.exists(annotation_path):
                samples.append((image_path, annotation_path))
            else:
                samples.append((image_path, None))
                if self.parameters.show_missing_annotations:
                    logger(
                        "Could not find the annotation " +
                        "for this image: {}. ".format(
                            os.path.basename(image_path)) +
                        "Looking for {}".format(
                            os.path.splitext(
                                os.path.basename(image_path))[0] +
                            self.annotation_extension),
                        code="WARNING")
                missing_annotations += 1

        if not self.parameters.show_missing_annotations and missing_annotations > 0:
            logger(
                "There were {} images without annotations. ".format(
                    missing_annotations) + "To see the names of the images, " +
                "enable --show_missing_annotations in the command line.",
                code="WARNING")

        if len(samples) == 0:
            raise ValueError(
                "There are no validation samples found in this dataset.")
        return samples

    def image(self, sample: str) -> Tuple[np.ndarray, np.ndarray, list, tuple]:
        """
        Read and preprocess the image.

        Parameters
        ----------
        sample: str
            The path to the image in the dataset.

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

        # Read the image.
        image = self.load_image(sample,
                                backend=self.parameters.common.backend)

        with self.timer.time("input"):
            if self.parameters.common.backend == "hal":
                image, visual_image, shapes, image_shape = preprocess_hal(
                    image=image,
                    shape=self.parameters.common.shape,
                    input_type=self.parameters.common.dtype,
                    input_buffer=self.parameters.common.input_dst,
                    transpose=self.parameters.common.transpose,
                    input_tensor=self.parameters.common.input_tensor,
                    preprocessing=self.parameters.common.preprocessing,
                    normalization=self.parameters.common.norm,
                    quantization=self.parameters.common.input_quantization,
                    visualize=self.parameters.visualize
                )
            else:
                image, visual_image, shapes, image_shape = preprocess_native(
                    image=image,
                    shape=self.parameters.common.shape,
                    input_type=self.parameters.common.dtype,
                    transpose=self.parameters.common.transpose,
                    input_tensor=self.parameters.common.input_tensor,
                    preprocessing=self.parameters.common.preprocessing,
                    normalization=self.parameters.common.norm,
                    quantization=self.parameters.common.input_quantization,
                    backend=self.parameters.common.backend
                )
        return image, visual_image, shapes, image_shape

    def build_detection_instance(
        self,
        sample: Tuple[str, str]
    ) -> DetectionInstance:
        """
        Builds a 2D detection instance container.

        Parameters
        ----------
        sample: Tuple[str, str]
            This contains the (image path, annotation path).

        Returns
        -------
        DetectionInstance
            The ground truth instance objects contains the 2D bounding boxes
            and the labels representing the ground truth of the image.
        """
        image_path, annotation_path = sample

        image, visual_image, shapes, image_shape = self.image(image_path)
        height, width = get_shape(image.shape)

        annotations = read_detection_text_file(
            annotation_path=annotation_path,
            label_offset=self.parameters.label_offset,
            shape=(height, width),
            normalizer=self.normalizer,
            transformer=self.transformer
        )
        boxes = annotations["boxes"]
        labels = annotations["labels"]

        # Transform the ground truth boxes based on the preprocessed image.
        if len(boxes):
            # Scale ground truth coordinates to center around objects
            # in an image with letterbox transformation.
            if self.parameters.common.preprocessing == "letterbox":
                boxes = scale(
                    boxes=boxes,
                    w=shapes[1][0][1] * image_shape[1],
                    h=shapes[1][0][0] * image_shape[0],
                    padw=shapes[1][1][0],
                    padh=shapes[1][1][1],
                )
            # Scale ground truth coordinates to center around objects
            # in an image with padding transformation.
            elif self.parameters.common.preprocessing == "pad":
                boxes = scale(
                    boxes=boxes,
                    w=shapes[1][0][1] * width,
                    h=shapes[1][0][0] * height,
                )
            # Scale ground truth coordinates to center around objects
            # in an image with resize transformation.
            else:
                # Denormalize boxes
                boxes *= np.array([width, height, width, height])

        instance = DetectionInstance(image_path)
        instance.image = image
        instance.visual_image = visual_image
        instance.height = height
        instance.width = width
        instance.boxes = boxes.astype(np.float32)
        instance.labels = labels.astype(np.uintp)
        instance.shapes = shapes
        instance.image_shape = image_shape
        return instance

    def build_segmentation_instance(
            self, sample: Tuple[str, str]) -> SegmentationInstance:
        """
        Builds a segmentation instance container.

        Parameters
        ----------
        sample: Tuple[str, str]
            This contains the (image path, annotation path).

        Returns
        -------
        SegmentationInstance
            The ground truth instance objects contains the polygon, mask,
            and the labels representing the ground truth of the image.
        """
        image_path, annotation_path = sample

        image, visual_image, shapes, image_shape = self.image(image_path)
        height, width = get_shape(image.shape)

        annotations = read_segmentation_text_file(
            annotation_path=annotation_path,
            label_offset=self.parameters.label_offset,
            shape=image_shape,
            normalizer=self.normalizer,
            transformer=self.transformer
        )
        segments = annotations["segments"]
        labels = annotations["labels"]

        imgsz = shapes[0]
        ratio_pad = shapes[1]

        # Scale ground truth mask to center around objects
        # in an image with padding transformation.
        if self.parameters.common.preprocessing == "pad":
            ratio_pad[1] = [0.0, 0.0]

        # For semantic segmentation,
        # labels should already contain background at the last index.
        masks, _ = format_segments(
            segments=segments,
            shape=imgsz,
            ratio_pad=ratio_pad,
            colors=labels,
            semantic=self.parameters.common.semantic,
            backend=self.parameters.common.backend,
            background_index=len(self.parameters.labels) - 1
        )

        instance = SegmentationInstance(image_path)
        instance.image = image
        instance.visual_image = visual_image
        instance.height = height
        instance.width = width
        instance.mask = masks
        instance.shapes = shapes
        instance.image_shape = image_shape
        return instance

    def build_multitask_instance(
            self, sample: Tuple[str, str]) -> MultitaskInstance:
        """
        Builds a multitask instance container.

        Parameters
        ----------
        sample: Tuple[str, str]
            This contains the (image path, annotation path).

        Returns
        -------
        MultitaskInstance
            The ground truth instance objects contains the bounding boxes
            and the segmentation mask representing the ground truth of
            the image
        """

        image_path, annotation_path = sample

        image, visual_image, shapes, image_shape = self.image(image_path)
        height, width = get_shape(image.shape)

        annotations = read_segmentation_text_file(
            annotation_path=annotation_path,
            label_offset=self.parameters.label_offset,
            shape=image_shape,
            normalizer=self.normalizer,
            transformer=self.transformer
        )
        segments = annotations["segments"]
        labels = annotations["labels"]
        boxes = annotations["boxes"]

        imgsz = shapes[0]
        ratio_pad = shapes[1]

        # Format boxes
        if len(boxes):
            # Transform the ground truth boxes based on the preprocessed image.
            # Scale ground truth coordinates to center around objects
            # in an image with letterbox transformation.
            if self.parameters.common.preprocessing == "letterbox":
                boxes = scale(
                    boxes=boxes,
                    w=shapes[1][0][1] * image_shape[1],
                    h=shapes[1][0][0] * image_shape[0],
                    padw=shapes[1][1][0],
                    padh=shapes[1][1][1],
                )
            # Scale ground truth coordinates to center around objects
            # in an image with padding transformation.
            elif self.parameters.common.preprocessing == "pad":
                boxes = scale(
                    boxes=boxes,
                    w=shapes[1][0][1] * width,
                    h=shapes[1][0][0] * height,
                )
            # Scale ground truth coordinates to center around objects
            # in an image with resize transformation.
            else:
                # Denormalize boxes
                boxes *= np.array([width, height, width, height])

        # Scale ground truth mask to center around objects
        # in an image with padding transformation.
        if self.parameters.common.preprocessing == "pad":
            ratio_pad[1] = [0.0, 0.0]

        # For semantic segmentation,
        # labels should already contain background at the last index.
        masks, sorted_idx = format_segments(
            segments=segments,
            shape=imgsz,
            ratio_pad=ratio_pad,
            colors=labels,
            semantic=self.parameters.common.semantic,
            backend=self.parameters.common.backend,
            background_index=len(self.parameters.labels) - 1
        )

        if sorted_idx is not None and len(sorted_idx) > 0:
            if len(labels):
                labels = labels[sorted_idx]
            if len(boxes):
                boxes = boxes[sorted_idx]

        instance = MultitaskInstance(image_path)
        instance.image = image
        instance.visual_image = visual_image
        instance.height = height
        instance.width = width
        instance.boxes = boxes.astype(np.float32)
        instance.labels = labels.astype(np.uintp)
        instance.mask = masks
        instance.shapes = shapes
        instance.image_shape = image_shape
        return instance
