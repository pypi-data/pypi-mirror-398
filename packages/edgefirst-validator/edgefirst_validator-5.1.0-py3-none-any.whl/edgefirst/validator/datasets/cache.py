"""
Implementations for downloading and caching the dataset.
"""

from __future__ import annotations

import os
import json
import glob
from typing import TYPE_CHECKING, Optional

import tqdm
import lmdb
import numpy as np

from edgefirst_client import Client, FileType, AnnotationType  # pylint: disable=no-name-in-module

from edgefirst.validator.datasets import LMDBDatabase
from edgefirst.validator.publishers.utils.logger import logger

if TYPE_CHECKING:
    from edgefirst.validator.evaluators import DatasetParameters, StageTracker
    from edgefirst.validator.datasets import Dataset


class StudioCache:
    """
    Communicate with EdgeFirst Studio for
    fetching and caching the dataset and post the progress.

    Parameters
    ----------
    parameters: DatasetParameters
        This contains dataset parameters set from the command line.
    stage_tracker: StageTracker
        This contains the stages that tracks each progress in Studio.
        A stage contains ("stage identifier", "stage description").
    client: Optional[Client]
        EdgeFirst Client object.
    session_id: Optional[str]
        This is the validation session ID in EdgeFirst Studio for
        posting validation metrics.
    val_group: str
        The dataset validation group set in EdgeFirst Studio.
    """

    def __init__(
        self,
        parameters: DatasetParameters,
        stage_tracker: StageTracker,
        client: Optional[Client] = None,
        session_id: Optional[str] = None,
        val_group: str = "val"
    ):
        self.parameters = parameters
        self.stage_tracker = stage_tracker
        self.client = client
        self.val_session = None
        self.val_group = val_group

        if self.client is not None and session_id is not None:
            self.val_session = self.client.validation_session(session_id)

    def complete_stage(self, stage: str, message: str):
        """
        Completes the stage on studio at the end of the task.

        Parameters
        ----------
        stage: str
            The stage identifier.
        message: str
            The message to project in the Studio GUI.
        """
        if self.client is not None:
            self.client.update_stage(
                self.val_session.task.id,
                stage=stage,
                status="Running",
                message=message,
                percentage=100
            )

    def download(self, dataset: str):
        """
        Download the dataset from EdgeFirst Studio into the device.

        Parameters
        ----------
        dataset: str
            The path to directory to save the dataset.

        Returns
        -------
        pl.DataFrame
            This is the polars dataframe of the annotations.
        """

        if self.client is None:
            raise ValueError(
                "EdgeFirst Client needs to be defined to download the dataset.")

        if self.val_session is None:
            raise ValueError(
                "Validation session ID needs to be defined to download the dataset.")

        annotation_types = [AnnotationType.Box2d, AnnotationType.Mask]
        os.makedirs(dataset, exist_ok=True)

        dataset_id = self.val_session.dataset_id
        annotation_id = self.val_session.annotation_set_id

        # Download Images
        self.stage_tracker.set_stage("stage_fetch_im")
        stage, message = self.stage_tracker.current()

        with tqdm.tqdm(
            total=0,
            desc=f"Downloading Images from Dataset ID: ds-{dataset_id.value:x}"
        ) as pbar:
            def image_progress(current, total):
                if total != pbar.total:
                    pbar.reset(total)
                pbar.update(current - pbar.n)
                self.client.update_stage(
                    self.val_session.task.id,
                    stage=stage,
                    status="Running",
                    message=message,
                    percentage=int(100 * current / total)
                )

            self.client.download_dataset(
                dataset_id=dataset_id,
                groups=[self.val_group],
                types=[FileType.Image],
                output=os.path.join(dataset, "images"),
                progress=image_progress,
            )

        total_images = len(glob.glob(os.path.join(dataset, "images", "*"),
                                     recursive=True))
        logger(f"Downloaded a total of {total_images} images.", code="INFO")

        # Download Annotations
        self.stage_tracker.set_stage("stage_fetch_as")
        stage, message = self.stage_tracker.current()

        with tqdm.tqdm(
            total=0,
            desc=f"Downloading Annotations from Annotation ID: as-{annotation_id.value:x}"
        ) as pbar:
            def annotation_progress(current, total):
                if total != pbar.total:
                    pbar.reset(total)
                pbar.update(current - pbar.n)
                self.client.update_stage(
                    self.val_session.task.id,
                    stage=stage,
                    status="Running",
                    message=message,
                    percentage=int(100 * current / total)
                )

            dataframe = self.client.annotations_dataframe(
                annotation_set_id=annotation_id,
                groups=[self.val_group],
                annotation_types=annotation_types,
                progress=annotation_progress
            )
            dataframe.write_ipc(os.path.join(dataset, "dataset.arrow"))

        logger(f"Downloaded a total of {dataframe.shape[0]} annotations.",
               code="INFO")

        return dataframe

    def cache(self, dataset: Dataset,
              cache: str = "cache/val.db") -> LMDBDatabase:
        """
        Cache the dataset provided into an LMDB file.

        Parameters
        ----------
        dataset: Dataset
            This can either be a DarkNet or EdgeFirst Dataset object.
        cache: str
            The path to the cache file to save the cache.

        Returns
        -------
        LMDBDatabase
            The instantiated cached dataset.
        """

        # Remove existing cache file.
        if os.path.exists(cache):
            os.remove(cache)
        os.makedirs(os.path.dirname(cache), exist_ok=True)

        dbenv = lmdb.open(
            cache,
            map_size=1024 ** 4,
            max_dbs=10,
            subdir=False,
            lock=False
        )

        classes_db = dbenv.open_db(b'classes')  # Unique labels in the dataset.
        # Name of each image in the dataset.
        names_db = dbenv.open_db(b'names')
        # All preprocessed images in the dataset.
        images_db = dbenv.open_db(b'images')
        # Images used for visualization.
        visual_images_db = dbenv.open_db(b'visual')
        boxes_db = dbenv.open_db(b'box2d')  # 2D box annotations.
        # Integer labels for each boxes or masks.
        labels_db = dbenv.open_db(b'labels')
        masks_db = dbenv.open_db(b'masks')  # 2D masks annotations.

        # Store the unique labels in the dataset.
        with dbenv.begin(write=True) as txn:
            txn.put(
                b'classes',
                json.dumps(self.parameters.labels).encode(),
                db=classes_db
            )

        samples = self.stage_tracker.stage_generator(
            dataset.collect_samples(), stage_name="stage_ds_cache", colour="green")
        stage, message = self.stage_tracker.current()
        for i, sample in enumerate(samples):
            gt_instance = dataset.read_sample(sample)

            with dbenv.begin(write=True) as txn:
                image_path = gt_instance.image_path
                image = gt_instance.image
                visual_image = gt_instance.visual_image
                shapes = gt_instance.shapes
                image_shape = gt_instance.image_shape
                labels = gt_instance.labels

                if self.parameters.common.with_boxes:
                    boxes = gt_instance.boxes
                else:
                    boxes = np.array([], dtype=np.float32)

                if self.parameters.common.with_masks:
                    masks = gt_instance.mask
                else:
                    masks = np.zeros(shapes[0], dtype=np.uint8)

                name = os.path.basename(image_path)
                txn.put(name.encode(), None, db=names_db)
                txn.put(name.encode(), image.tobytes(), db=images_db)
                # Place the current shape of the image.
                txn.put(f'{name}/shape'.encode(),
                        np.array(image.shape, dtype=np.int32).tobytes(),
                        db=images_db)

                if visual_image is not None:
                    txn.put(
                        name.encode(),
                        visual_image.tobytes(),
                        db=visual_images_db)
                    # Place the current shape of the visualization image.
                    txn.put(f'{name}/shape'.encode(),
                            np.array(visual_image.shape,
                                     dtype=np.int32).tobytes(),
                            db=visual_images_db)

                # Place the label transformation shapes after letterboxing.
                txn.put(f'{name}/shapes'.encode(),
                        json.dumps(shapes).encode(),
                        db=images_db)
                # Place the original shape of the image.
                txn.put(f'{name}/im_shape'.encode(),
                        np.array(image_shape, dtype=np.int32).tobytes(),
                        db=images_db)
                txn.put(name.encode(), boxes.tobytes(), db=boxes_db)
                txn.put(name.encode(), labels.tobytes(), db=labels_db)
                txn.put(name.encode(), masks.tobytes(), db=masks_db)
                txn.put(f'{name}/mask_shape'.encode(),
                        np.array(masks.shape, dtype=np.int32).tobytes(),
                        db=masks_db)

            if self.client is not None:
                self.client.update_stage(
                    self.val_session.task.id,
                    stage=stage,
                    status="Running",
                    message=message,
                    percentage=int(100 * i / len(dataset))
                )

        dbenv.close()
        if self.client is not None:
            self.complete_stage(
                stage=stage,
                message=message
            )

        return LMDBDatabase(
            source=cache,
            parameters=self.parameters,
            timer=dataset.timer,
            stage_tracker=self.stage_tracker,
        )
