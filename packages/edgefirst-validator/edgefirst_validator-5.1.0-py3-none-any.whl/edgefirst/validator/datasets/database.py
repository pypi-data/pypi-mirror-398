"""
Implementations for reading EdgeFirst dataset and LMDB cache.
"""

from __future__ import annotations

import os
import json
import glob
from typing import TYPE_CHECKING, Optional, Union, Tuple

import lmdb
import numpy as np
import polars as pl

from edgefirst.validator.datasets import (SegmentationInstance,
                                          DetectionInstance,
                                          MultitaskInstance)
from edgefirst.validator.datasets import Dataset
from edgefirst.validator.datasets.utils.annotation_transforms import (resample_segments,
                                                                      format_segments,
                                                                      scale)
from edgefirst.validator.datasets.utils.image_transforms import (preprocess_native,
                                                                 preprocess_hal)
from edgefirst.validator.publishers.utils.logger import logger
from edgefirst.validator.datasets.utils.fetch import get_shape

if TYPE_CHECKING:
    from edgefirst.validator.evaluators import (DatasetParameters,
                                                TimerContext, StageTracker)


class EdgeFirstDatabase(Dataset):
    """
    Reads EdgeFirst Database/Datasets.

    Parameters
    ----------
    source: str
        This is the path to the Arrow file containing the
        annotations of EdgeFirst Datasets.
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
    sessions: Optional[Union[list, tuple]]
        Filter to only use the specified sessions. By default, use
        all the sessions.

    Raises
    ------
    FileNotFoundError
        Raised if the source provided does not exist.
    ValueError
        Raised if the dataset does not contain any files.
    """

    def __init__(
        self,
        source: str,
        parameters: DatasetParameters,
        timer: TimerContext,
        stage_tracker: StageTracker,
        info_dataset: Optional[dict] = None,
        sessions: Optional[Union[list, tuple]] = None,
    ):
        # Locate the arrow file.
        source = glob.glob(source if source.endswith(
            "*.arrow") else os.path.join(source, "*.arrow"))[0]

        super(EdgeFirstDatabase, self).__init__(
            source=source,
            parameters=parameters,
            timer=timer,
            stage_tracker=stage_tracker,
            info_dataset=info_dataset
        )

        if not os.path.exists(self.source):
            raise FileNotFoundError("The dataset *.arrow file does not exist.")

        self.root_folder = os.path.dirname(self.source)
        if not os.path.exists(self.root_folder):
            raise FileNotFoundError(
                "Dataset folder was not found at: ", self.root_folder)

        # Find all images.
        self.all_images = glob.glob(
            os.path.join(self.root_folder, "**", "*"),
            recursive=True)

        self.all_images_dict = {}
        for image in self.all_images:
            if not os.path.isfile(image) or \
                    image.endswith(".txt") or \
                    image.endswith(".mask.png") or \
                    image.endswith(".depth.png") or \
                    image.endswith(".radar.png") or \
                    image.endswith(".radar.pcd") or \
                    image.endswith(".lidar.png") or \
                    image.endswith(".lidar.pcd") or \
                    image.endswith(".lidar.reflect") or \
                    image.endswith(".lidar.jpeg"):
                continue

            name = os.path.splitext(os.path.basename(image))[0]
            if name.endswith(".camera"):
                name = name[:-7]
            self.all_images_dict[name] = image

        # Read the dataframe.
        self.dataframe = pl.scan_ipc(self.source)

        if sessions is not None:
            self.dataframe = self.dataframe.filter(
                pl.col("name").is_in(sessions))
        self.dataframe = self.dataframe.with_row_index().collect()

        self.samples = self.dataframe.group_by(["name", "frame"]) \
            .agg(pl.col("index")) \
            .get_column("index").to_list()

        if len(self.samples) == 0:
            raise ValueError(
                "There are no validation samples found in this dataset.")

        if self.dataframe["label"].null_count() == len(
                self.dataframe["label"]):
            raise ValueError("There are no annotations in this dataset.")

        # List the classes based on the label column of the dataframe.
        if self.parameters.labels is None:
            if "label_index" in self.dataframe.columns:
                pairs = (self.dataframe
                         .filter(pl.col("label").is_not_null())
                         .select(["label", "label_index"])
                         .unique())
                # Not every label is annotated in the dataset. In place with
                # Null.
                labels = ["Null"] * (max(pairs["label_index"]) + 1)

                for label, index in zip(pairs["label"], pairs["label_index"]):
                    labels[index] = label
                self.parameters.labels = labels
            else:
                # Fallback: unique labels sorted alphabetically (previous
                # behavior)
                self.parameters.labels = (
                    self.dataframe
                    .filter(pl.col("label").is_not_null())
                    .select(pl.col("label"))
                    .unique()
                    .get_column("label")
                    .to_list()
                )
                self.parameters.labels.sort()

    def verify_dataset(self):
        """
        Verify that the dataset contains ground truth annotations.
        """
        mask_col = self.dataframe["mask"]
        box_col = self.dataframe["box2d"]
        is_all_mask_null = mask_col.null_count() == len(mask_col)
        is_all_box_null = box_col.null_count() == len(box_col)

        if is_all_mask_null and is_all_box_null:
            raise ValueError("There are no annotations in this dataset.")
        elif (self.parameters.common.with_masks and
              not self.parameters.common.with_boxes):
            if is_all_mask_null:
                raise ValueError("There are no mask annotations in the dataset " +
                                 "to validate the segmentation model.")
        elif (self.parameters.common.with_boxes and
              not self.parameters.common.with_masks):
            if is_all_box_null:
                raise ValueError("There are no box annotations in the dataset " +
                                 "to validate the detection model.")
        else:
            if is_all_mask_null:
                logger("There were no mask annotations found in this dataset.",
                       code="WARNING")

            if is_all_box_null:
                logger("There were no box annotations found in this dataset.",
                       code="WARNING")

    def collect_samples(self) -> list:
        """
        Collect all samples in the dataset.

        Returns
        -------
        list
            A sample contains the indices in
            the dataframe that points to all the annotations
            for the sample image.
        """
        return self.samples

    def name(self, sample: list) -> str:
        """
        Fetch the name of the dataset sample.

        Parameters
        ----------
        sample: list
            A single dataset sample contains the indices
            in the dataframe pointing to all the annotations
            in the dataset for this sample.

        Returns
        -------
        str
            The name of the sample. This is typically
            the basename of the image.
        """
        index = sample[0]
        name = self.dataframe.item(index, "name")
        frame = self.dataframe.item(index, "frame")
        if frame is None:
            return name
        return f"{name}_{frame}"

    def image(self,
              sample: list) -> Tuple[np.ndarray, np.ndarray, list, tuple]:
        """
        Reads the image file from the dataset. This method should
        also handle any image preprocessing specified when caching is
        required. Image preprocessing will include image resizing, letterbox,
        or padding and transformations to either YUYV or RGBA.

        Parameters
        ----------
        sample: list
            A single dataset sample contains the indices
            in the dataframe pointing to all the annotations
            in the dataset for this sample.

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

        Raises
        ------
        FileNotFoundError
            Raised if the image file does not exist in the dataset.
        """
        name = self.name(sample)
        image = self.all_images_dict.get(name)

        if image is None:
            raise FileNotFoundError(f"Image '{name}' was not found")

        # Read the image.
        image = self.load_image(image, backend=self.parameters.common.backend)

        with self.timer.time("input"):
            # Preprocess the image.
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

    def labels(self, sample: list) -> np.ndarray:
        """
        Fetch the labels at the specified sample.

        Parameters
        ----------
        sample: list
            A single dataset sample contains the indices
            in the dataframe pointing to all the annotations
            in the dataset for this sample.

        Returns
        -------
        np.ndarray
            The labels in the sample containing np.uintp elements.
        """
        if "label_index" in self.dataframe.columns:
            col = "label_index"
        else:
            col = "label"

        labels = (
            self.dataframe.lazy()
            .filter(pl.col(col).is_not_null())
            .filter(pl.col("index").is_in(sample))
            .select(col)
            .collect()
            .get_column(col)
            .to_list()
        )

        if col == "label":
            labels = np.array([
                self.parameters.labels.index(label) for label in labels],
                dtype=np.uintp
            )
        else:
            labels = (np.array(labels, dtype=np.uintp) +
                      self.parameters.label_offset)
        return labels

    def boxes(self, sample: list) -> np.ndarray:
        """
        Fetches the bounding box annotations at the specified sample.

        Parameters
        ----------
        sample: list
            A single dataset sample contains the indices
            in the dataframe pointing to all the annotations
            in the dataset for this sample.

        Returns
        -------
        np.ndarray
            The bounding box array. This array is formatted
            as [xmin, ymin, xmax, ymax, label].
        """
        boxes = self.dataframe.lazy()
        boxes = boxes.filter(pl.col("box2d").is_not_null())
        boxes = boxes.filter(pl.col("index").is_in(sample))

        if "label_index" in self.dataframe.columns:
            col = "label_index"
        else:
            col = "label"
        boxes = boxes.select([pl.col(col), "box2d"])
        data = boxes.collect()
        boxes = data.get_column("box2d").to_numpy()

        if col == "label_index":
            labels = (data.get_column(col).to_numpy().astype(np.float32) +
                      self.parameters.label_offset)
        else:
            labels = data.get_column(col)
            labels = labels.to_list()
            labels = np.array([
                self.parameters.labels.index(label) for label in labels],
                dtype=np.float32
            )
        return np.hstack([boxes, labels[:, None]])

    def segments(
        self,
        sample: list,
        image_shape: tuple,
        resample: int = 1000
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Fetches the mask annotations as polygons.

        Parameters
        ----------
        sample: list
            A single dataset sample contains the indices
            in the dataframe pointing to all the annotations
            in the dataset for this sample.
        image_shape: tuple
            The original dimensions of the image as (height, width).
        resample: int
            The number of points to resample the segments.

        Returns
        -------
        segments: np.ndarray
            A flattened array containing [x, y, x, y, ... nan, ...]
            coordinates for the mask polygons where each mask
            is separated by NaN to indicate a separate object.
        labels: np.ndarray
            Returns the labels for each mask.
        """
        polygons = self.dataframe.lazy()
        polygons = polygons.filter(pl.col("mask").is_not_null())
        polygons = polygons.filter(pl.col("index").is_in(sample))

        if "label_index" in self.dataframe.columns:
            col = "label_index"
        else:
            col = "label"
        polygons = polygons.filter(
            pl.col('label').is_in(self.parameters.labels))
        polygons = polygons.select([pl.col(col), "mask"])
        polygons = polygons.collect()

        if col == "label_index":
            labels = (polygons.get_column(col).to_numpy().astype(np.uintp) +
                      self.parameters.label_offset)
        else:
            labels = polygons.get_column(col).to_list()
            # Conversion to integer.
            labels = np.array([self.parameters.labels.index(label)
                               for label in labels], dtype=np.uintp)
        polygons = polygons.get_column("mask").to_numpy()

        segments = []
        for polygon in polygons:
            if len(polygon) == 0:
                continue
            # Use numpy operations to speed up the process
            valid_indices = np.ma.clump_unmasked(
                np.ma.masked_invalid(polygon))
            # Contours is a single object with multiple masks, the length
            # of the contours is the number of masks of this object.
            contours = [polygon[s] for s in valid_indices]
            # A weak solution as it combines masks of the same object, but
            # it reproduces the format from Ultralytics as polygons (n, p, 2)
            # where n is the number of object, p is the number of points,
            # and 2 (x, y) coordinate points.
            contours = np.concatenate(contours).reshape(-1, 2)
            segments.append(contours)

        # Get the original shape of the image.
        height, width = image_shape
        # Segments are being resampled.
        # https://github.com/ultralytics/ultralytics/blob/main/ultralytics/data/dataset.py#L274
        # NOTE: do NOT resample oriented boxes.
        if len(segments) > 0:
            # make sure segments interpolate correctly if
            # original length is greater than resample.
            max_len = max(len(s) for s in segments)
            resample = (max_len + 1) if resample < max_len else resample
            # list[np.array(resample, 2)] * num_samples
            segments = np.stack(resample_segments(
                segments, n=resample), axis=0)
            # Denormalize segments.
            segments[..., 0] *= width
            segments[..., 1] *= height
        else:
            segments = np.zeros((0, resample, 2), dtype=np.float32)

        return segments, labels

    def mask(
        self,
        sample: list,
        shapes: list,
        image_shape: tuple
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Fetches the mask annotations at the specified sample.

        Parameters
        ----------
        sample: list
            A single dataset sample contains the indices
            in the dataframe pointing to all the annotations
            in the dataset for this sample.
        shapes: list
            This is used to scale the bounding boxes of the ground
            truth and the model detections based on the letterbox/padding
            transformation.

            .. code-block:: python

                [[input_height, input_width],
                [[scale_y, scale_x], [pad_w, pad_h]]]
        image_shape: tuple
            This contains the original image dimensions (height, width).

        Returns
        -------
        masks: np.ndarray
            The mask array in the shape (n, height, width) if its
            an instance segmentation. Otherwise for semantic segmentation
            n = 1.
        sorted_idx: np.ndarray
            Resorting the ground truth based on these indices.
        """
        segments, labels = self.segments(sample, image_shape=image_shape)

        imgsz = shapes[0]
        ratio_pad = shapes[1]

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
        return masks, sorted_idx

    def build_detection_instance(self, sample: list) -> DetectionInstance:
        """
        Builds a 2D detection instance container.

        Parameters
        ----------
        sample: list
            A single dataset sample contains the indices
            in the dataframe pointing to all the annotations
            in the dataset for this sample.

        Returns
        -------
        DetectionInstance
            The ground truth instance objects contains the 2D bounding boxes
            and the labels representing the ground truth of the image.
        """
        image, visual_image, shapes, image_shape = self.image(sample)
        height, width = get_shape(image.shape)
        name = self.name(sample)
        name = os.path.basename(self.all_images_dict.get(name))

        boxes = self.boxes(sample)
        # Transform the ground truth boxes based on the preprocessed image.
        if len(boxes):
            labels = boxes[..., 4]
            boxes = boxes[..., 0:4]
            # If the boxes are denormalized, normalize the boxes.
            boxes = (self.normalizer(boxes, image_shape)
                     if self.normalizer else boxes)
            # Transform the boxes to xyxy format if required.
            boxes = self.transformer(boxes) if self.transformer else boxes

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
        else:
            labels = np.array([])

        instance = DetectionInstance(name)
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
            self, sample: list) -> SegmentationInstance:
        """
        Builds a segmentation instance container.

        Parameters
        ----------
        sample: list
            A single dataset sample contains the indices
            in the dataframe pointing to all the annotations
            in the dataset for this sample.

        Returns
        -------
        SegmentationInstance
            The ground truth instance objects contains the polygon, mask,
            and the labels representing the ground truth of the image.
        """

        image, visual_image, shapes, image_shape = self.image(sample)
        height, width = get_shape(image.shape)
        name = self.name(sample)
        name = os.path.basename(self.all_images_dict.get(name))

        masks, _ = self.mask(sample, shapes, image_shape)

        instance = SegmentationInstance(name)
        instance.image = image
        instance.visual_image = visual_image
        instance.height = height
        instance.width = width
        instance.mask = masks
        instance.shapes = shapes
        instance.image_shape = image_shape
        return instance

    def build_multitask_instance(self, sample: list) -> MultitaskInstance:
        """
        Builds a multitask instance container.

        Parameters
        ----------
        sample: list
            A single dataset sample contains the indices
            in the dataframe pointing to all the annotations
            in the dataset for this sample.

        Returns
        -------
        MultitaskInstance
            The ground truth instance objects contains the bounding boxes
            and the segmentation mask representing the ground truth of
            the image
        """

        image, visual_image, shapes, image_shape = self.image(sample)
        height, width = get_shape(image.shape)
        name = self.name(sample)
        name = os.path.basename(self.all_images_dict.get(name))

        # Transform the ground truth boxes based on the preprocessed image.
        boxes = self.boxes(sample)
        if len(boxes):
            labels = boxes[..., 4]
            boxes = boxes[..., 0:4]
            boxes = (self.normalizer(boxes, image_shape)
                     if self.normalizer else boxes)
            boxes = self.transformer(boxes) if self.transformer else boxes

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
        else:
            labels = self.labels(sample)

        masks, sorted_idx = self.mask(sample, shapes, image_shape)
        if sorted_idx is not None and len(sorted_idx) > 0:
            if len(labels):
                labels = labels[sorted_idx]
            if len(boxes):
                boxes = boxes[sorted_idx]

        instance = MultitaskInstance(name)
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


class LMDBDatabase(Dataset):
    """
    Reads from LMDB database cache. This is the cache file.
    It should already store preprocessed images and annotations. The
    shape for the images across all samples remains consistent to the
    input shape of the model.

    Parameters
    ----------
    MAP_SIZE : int
        The maximum size of the LMDB database.
    source: str
        This is the path to the LMDB Database file.
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
    FileNotFoundError
        Raised if the source provided does not exist.
    """

    MAP_SIZE = 32 * 1024 * 1024 * 1024

    def __init__(
        self,
        source: str,
        parameters: DatasetParameters,
        timer: TimerContext,
        stage_tracker: StageTracker,
        info_dataset: Optional[dict] = None,
    ):
        super(LMDBDatabase, self).__init__(
            source=source,
            parameters=parameters,
            timer=timer,
            stage_tracker=stage_tracker,
            info_dataset=info_dataset
        )

        if not os.path.isfile(self.source):
            raise FileNotFoundError("The cache was not found at: ", source)

        self.db = lmdb.open(
            str(self.source).encode(),
            map_size=LMDBDatabase.MAP_SIZE,
            max_dbs=10,
            subdir=False,
            lock=False
        )
        self.classes_db = self.db.open_db(b'classes')
        self.names_db = self.db.open_db(b'names')
        self.images_db = self.db.open_db(b'images')
        self.visual_images_db = self.db.open_db(b'visual')
        self.boxes_db = self.db.open_db(b'box2d')
        self.labels_db = self.db.open_db(b'labels')
        self.masks_db = self.db.open_db(b'masks')

        with self.db.begin() as txn:
            classes = txn.get(b'classes', db=self.classes_db)
            if classes is not None:
                classes = json.loads(classes.decode())
                self.parameters.labels = [str(c) for c in classes]

        with self.db.begin() as txn:
            cur = txn.cursor(self.names_db)
            keys = [key.decode() for key, _ in cur]
        self.samples = keys

        if len(self.samples) == 0:
            raise ValueError(
                "There are no validation samples found in this dataset.")

    def __del__(self):
        """
        Closes the database.
        """
        self.db.close()

    def collect_samples(self) -> list:
        """
        Collect all samples in the dataset.

        Returns
        -------
        list
            A sample contains the indices in
            the dataframe that points to all the annotations
            for the sample image.
        """
        return self.samples

    def name(self, sample: int) -> str:
        """
        Fetch the name of the dataset sample.

        Parameters
        ----------
        sample: int
            The dataset sample index.

        Returns
        -------
        str
            The name of the sample.
            This is typically the basename of the image.
        """
        return self.samples[sample]

    def image(self, sample: str) -> Tuple[np.ndarray, np.ndarray, list, tuple]:
        """
        Fetches the preprocessed image stored in the cache.

        Parameters
        ----------
        sample: str
            The image name to fetch the sample.

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
        with self.db.begin(buffers=True) as txn:
            image_shape_tx = txn.get(
                f'{sample}/im_shape'.encode(), db=self.images_db)
            image_shape = tuple(np.frombuffer(image_shape_tx, dtype=np.int32))

            shapes_tx = txn.get(f'{sample}/shapes'.encode(), db=self.images_db)
            shapes = json.loads(bytes(shapes_tx).decode())

            shape_tx = txn.get(
                f'{sample}/shape'.encode(), db=self.images_db)
            shape = tuple(np.frombuffer(shape_tx, dtype=np.int32))
            image_tx = txn.get(sample.encode(), db=self.images_db)
            image = np.frombuffer(
                image_tx, dtype=self.parameters.common.dtype).reshape(shape)

            shape_tx = txn.get(
                f'{sample}/shape'.encode(), db=self.visual_images_db)
            if shape_tx is not None:
                shape = tuple(np.frombuffer(shape_tx, dtype=np.int32))
            visual_image = None
            visual_tx = txn.get(sample.encode(), db=self.visual_images_db)
            if visual_tx is not None:
                visual_image = np.frombuffer(
                    visual_tx, dtype=np.uint8).reshape(shape)
        return image, visual_image, shapes, image_shape

    def labels(self, sample: str) -> np.ndarray:
        """
        Fetch the labels stored in the cache.

        Parameters
        ----------
        sample: str
            The image name to fetch the sample.

        Returns
        -------
        np.ndarray
            The labels in the sample containing np.uintp elements.
        """
        with self.db.begin(buffers=True) as txn:
            labels_tx = txn.get(sample.encode(), db=self.labels_db)
            labels = np.frombuffer(labels_tx, dtype=np.uintp)
        return labels

    def boxes(self, sample: str) -> np.ndarray:
        """
        Fetches the boxes stored in the cache.

        Parameters
        -----------
        sample: str
            The image name to fetch the sample.

        Returns
        -------
        np.ndarray
            The bounding box array.
            This array is formatted as [xmin, ymin, xmax, ymax]
            normalized FP32 coordinates.
        """
        with self.db.begin(buffers=True) as txn:
            boxes_tx = txn.get(sample.encode(), db=self.boxes_db)
            boxes = np.frombuffer(boxes_tx, dtype=np.float32)
            boxes = boxes.reshape(-1, 4)
        return boxes

    def mask(self, sample: str) -> np.ndarray:  # pylint: disable=arguments-differ
        """
        Fetches the masks stored in the cache.

        Parameters
        -----------
        sample: str
            The image name to fetch the sample.

        Returns
        -------
        np.ndarray
            The masks array.
        """
        with self.db.begin(buffers=True) as txn:
            mask_shape_tx = txn.get(f'{sample}/mask_shape'.encode(),
                                    db=self.masks_db)
            mask_shape = tuple(
                np.frombuffer(mask_shape_tx, dtype=np.int32))

            masks_tx = txn.get(sample.encode(), db=self.masks_db)
            mask = np.frombuffer(masks_tx, dtype=np.uint8)
            mask = mask.reshape(mask_shape)
        return mask

    def build_detection_instance(self, sample: str) -> DetectionInstance:
        """
        Builds a 2D detection instance container.

        Parameters
        ----------
        sample: str
            The image name to fetch the sample.

        Returns
        -------
        DetectionInstance
            The ground truth instance objects contains the 2D bounding boxes
            and the labels representing the ground truth of the image.
        """
        image, visual_image, shapes, image_shape = self.image(sample)
        height, width = get_shape(image.shape)

        boxes = self.boxes(sample)
        labels = self.labels(sample)
        instance = DetectionInstance(sample)
        instance.image = image
        instance.visual_image = visual_image
        instance.height = height
        instance.width = width
        instance.boxes = boxes
        instance.labels = labels
        instance.shapes = shapes
        instance.image_shape = image_shape
        return instance

    def build_segmentation_instance(self, sample: str) -> SegmentationInstance:
        """
        Builds a segmentation instance container.

        Parameters
        ----------
        sample: str
            The image name to fetch the sample.

        Returns
        -------
        SegmentationInstance
            The ground truth instance objects contains the polygon, mask,
            and the labels representing the ground truth of the image.
        """
        image, visual_image, shapes, image_shape = self.image(sample)
        height, width = get_shape(image.shape)
        masks = self.mask(sample)

        instance = SegmentationInstance(sample)
        instance.image = image
        instance.visual_image = visual_image
        instance.height = height
        instance.width = width
        instance.mask = masks
        instance.shapes = shapes
        instance.image_shape = image_shape
        return instance

    def build_multitask_instance(self, sample: str) -> MultitaskInstance:
        """
        Builds a multitask instance container.

        Parameters
        ----------
        sample: str
            The image name to fetch the sample.

        Returns
        -------
        MultitaskInstance
            The ground truth instance objects contains the bounding boxes
            and the segmentation mask representing the ground truth of
            the image
        """

        image, visual_image, shapes, image_shape = self.image(sample)
        height, width = get_shape(image.shape)

        boxes = self.boxes(sample)
        labels = self.labels(sample)
        masks = self.mask(sample)

        instance = MultitaskInstance(sample)
        instance.image = image
        instance.visual_image = visual_image
        instance.height = height
        instance.width = width
        instance.boxes = boxes
        instance.labels = labels
        instance.mask = masks
        instance.shapes = shapes
        instance.image_shape = image_shape
        return instance
