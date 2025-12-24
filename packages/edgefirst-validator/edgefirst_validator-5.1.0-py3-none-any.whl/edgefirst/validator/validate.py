"""
Validation module for the EdgeFirst validator.
"""

from __future__ import annotations

import os
import datetime
import traceback
from typing import TYPE_CHECKING, Union

from edgefirst_client import Client  # pylint: disable=no-name-in-module

from edgefirst.validator.evaluators import (CombinedParameters, CommonParameters,
                                            ModelParameters, DatasetParameters,
                                            ValidationParameters, TimerContext)
from edgefirst.validator.evaluators import (DetectionValidator,
                                            InstanceSegmentationValidator,
                                            SemanticSegmentationValidator,
                                            MultitaskValidator,
                                            StudioProgress, StageTracker)
from edgefirst.validator.publishers import StudioPublisher
from edgefirst.validator.datasets import StudioCache
from edgefirst.validator.runners import (TFliteRunner, ONNXRunner, KerasRunner,
                                         TensorRTRunner, OfflineRunner,
                                         DeepViewRTRunner, KinaraRunner)
from edgefirst.validator.publishers.utils.logger import (logger,
                                                         set_symbol_condition)
from edgefirst.validator.datasets.utils.readers import read_labels_file
from edgefirst.validator.datasets.utils.fetch import (classify_dataset,
                                                      download_file)
from edgefirst.validator.datasets import instantiate_dataset

if TYPE_CHECKING:
    from edgefirst.validator.runners import Runner
    from edgefirst.validator.datasets import Dataset
    from edgefirst.validator.evaluators import Evaluator


def build_parameters(args) -> CombinedParameters:
    """
    Store command line arguments inside the `Parameters` object.

    Parameters
    ----------
    args: argsparse.NameSpace
        The command line arguments.

    Returns
    -------
    CombinedParameters
        This object is a container for both the model
        and validation parameters set from the command line.
    """
    # Time of validation
    today = datetime.datetime.now().strftime(
        '%Y-%m-%d--%H:%M:%S').replace(":", "_")
    tensorboard, visualize, json_out = None, None, None
    if args.visualize:
        visualize = os.path.join(
            args.visualize,
            f"{os.path.basename(os.path.normpath(args.model))}_{today}")
    elif args.tensorboard:
        tensorboard = os.path.join(
            args.tensorboard,
            f"{os.path.basename(os.path.normpath(args.model))}_{today}"
        )

    json_out = args.json_out
    if args.session_id is not None:
        if json_out is None:
            json_out = "apex_charts"

    if json_out:
        json_out = os.path.join(
            json_out,
            f"{os.path.basename(os.path.normpath(args.model))}_{today}"
        )

    validation_parameters = ValidationParameters(
        metric=args.metric,
        matching_leniency=args.matching_leniency,
        clamp_boxes=args.clamp_boxes,
        ignore_boxes=args.ignore_boxes,
        display=args.display,
        plots=args.suppress_plots,
        visualize=visualize,
        tensorboard=tensorboard,
        json_out=json_out,
        csv_out=args.csv,
        include_background=args.include_background,
        deploy_metrics=args.suppress_deployment_metrics
    )

    common_parameters = CommonParameters(
        norm=args.norm,
        preprocessing=args.preprocessing,
        backend=args.backend
    )
    common_parameters.check_backend_availability()

    model_parameters = ModelParameters(
        common_parameters=common_parameters,
        model_path=args.model,
        iou_threshold=args.nms_iou_threshold,
        score_threshold=args.nms_score_threshold,
        max_detections=args.max_detections,
        engine=args.engine,
        nms=args.nms,
        box_format=args.box_format,
        warmup=args.warmup,
        config_path=args.config,
        labels_path=args.model_labels,
        label_offset=args.label_offset,
        agnostic_nms=not args.class_nms,
        override=args.override
    )
    model_parameters.check_nms_availability()

    dataset_parameters = DatasetParameters(
        common_parameters=common_parameters,
        dataset_path=args.dataset,
        show_missing_annotations=args.show_missing_annotations,
        normalized=args.absolute_annotations,
        box_format=args.annotation_format,
        labels_path=args.dataset_labels,
        label_offset=args.gt_label_offset,
    )
    dataset_parameters.silent = validation_parameters.silent
    dataset_parameters.visualize = bool(validation_parameters.visualize or
                                        validation_parameters.tensorboard)

    parameters = CombinedParameters(
        model_parameters=model_parameters,
        dataset_parameters=dataset_parameters,
        validation_parameters=validation_parameters
    )

    if (model_parameters.nms in ["hal", "numpy", "torch"] and
            not model_parameters.agnostic_nms):
        logger(
            "Class-based NMS is currently not supported for the {} NMS.".format(
                model_parameters.nms), code="INFO"
        )

    if validation_parameters.visualize or validation_parameters.tensorboard:
        if validation_parameters.deploy_metrics:
            logger(
                "Storing images for all samples in the dataset to allow deployment visualizations.",
                code="WARNING"
            )
    return parameters


def build_dataset(
    args,
    parameters: DatasetParameters,
    timer: TimerContext,
    studio_cache: StudioCache,
    stage_tracker: StageTracker
) -> Dataset:
    """
    Instantiate the Dataset Reader.

    Parameters
    ----------
    args: argsparse.NameSpace
        The command line arguments.
    parameters: DatasetParameters
        Contains the dataset parameters set from the command line.
    timer: TimerContext
        A timer object for handling validation timings in
        the dataset input preprocessing.
    studio_cache: StudioCache
        The object used for downloading and caching the dataset.
    stage_tracker: StageTracker
        The object used for tracking and displaying stages.

    Returns
    -------
    Dataset
        This can be any dataset reader such as a DarkNetDataset,
        EdgeFirstDatabase, etc. depending on the dataset format that
        was specified.
    """

    if args.session_id is not None:
        # Avoid the default dataset path for studio validation.
        if args.dataset == "samples/coco128.yaml":
            args.dataset = "dataset"
            parameters.dataset_path = args.dataset

        if parameters.labels_path and os.path.exists(parameters.labels_path):
            parameters.labels = read_labels_file(parameters.labels_path)

        # Download the dataset if it doesn't exist.
        if not (os.path.exists(args.dataset) and os.listdir(args.dataset)):
            logger("The dataset does not exist. " +
                   f"Attempting to download the dataset to '{args.dataset}'",
                   code="INFO")
            studio_cache.download(args.dataset)
        else:
            # If the dataset download is skipped, mark the stages as complete.
            stage, message = stage_tracker.get_stage("stage_fetch_im")
            studio_cache.complete_stage(
                stage=stage,
                message=message
            )
            stage, message = stage_tracker.get_stage("stage_fetch_as")
            studio_cache.complete_stage(
                stage=stage,
                message=message
            )

    # Use the dataset cache if specified and it exists.
    if args.cache is not None:
        parameters.cache = True
        # If the cache exists, use it directly and marked the stage as
        # complete.
        if os.path.exists(args.cache):
            parameters.dataset_path = args.cache
            stage, message = stage_tracker.get_stage("stage_ds_cache")
            studio_cache.complete_stage(
                stage=stage,
                message=message
            )

    # Determine the dataset type.
    info_dataset = classify_dataset(
        source=parameters.dataset_path,
        labels_path=parameters.labels_path
    )

    # Build the dataset class depending on the type.
    return instantiate_dataset(
        info_dataset=info_dataset,
        parameters=parameters,
        timer=timer,
        stage_tracker=stage_tracker,
    )


def build_runner(parameters: ModelParameters, timer: TimerContext) -> Runner:
    """
    Instantiate the model runners.

    Parameters
    ----------
    parameters: ModelParameters
        Contains the model parameters set from the command line.
    timer: TimerContext
        A timer object for handling validation timings in the model.

    Returns
    -------
    Runner
        This can be any model runner depending on the model passed
        such as ONNX, TFLite, Keras, RTM, etc.

    Raises
    ------
    NotImplementedError
        Certain runner implementations are not yet implemented.
    """
    if (not os.path.exists(parameters.model_path) and
            parameters.model_path == "yolov5s.onnx"):
        download_file(
            url="https://github.com/ultralytics/yolov5/releases/download/v7.0/yolov5s.onnx",
            download_path=os.path.join(os.getcwd(), "yolov5s.onnx")
        )

    # KERAS
    if os.path.splitext(parameters.model_path)[1].lower() in [".h5", ".keras"]:
        runner = KerasRunner(parameters.model_path,
                             parameters=parameters,
                             timer=timer)
    # TFLITE
    elif os.path.splitext(parameters.model_path)[1].lower() == ".tflite":
        runner = TFliteRunner(parameters.model_path,
                              parameters=parameters,
                              timer=timer)
    # ONNX
    elif os.path.splitext(parameters.model_path)[1].lower() == ".onnx":
        runner = ONNXRunner(parameters.model_path,
                            parameters=parameters,
                            timer=timer)
    # TENSORRT
    elif os.path.splitext(parameters.model_path)[1].lower() in [".engine", ".trt"]:
        runner = TensorRTRunner(parameters.model_path,
                                parameters=parameters,
                                timer=timer)
    # KINARA
    elif os.path.splitext(parameters.model_path)[1].lower() == ".dvm":
        runner = KinaraRunner(
            parameters.model_path,
            parameters=parameters,
            timer=timer
        )
    # HAILO
    elif os.path.splitext(parameters.model_path)[1].lower() == ".hef":
        raise NotImplementedError(
            "Running Hailo models is not implemented.")
    # DEEPVIEWRT EVALUATION
    elif os.path.splitext(parameters.model_path)[1].lower() == ".rtm":
        runner = DeepViewRTRunner(
            model=parameters.model_path,
            parameters=parameters,
            timer=timer
        )
    # OFFLINE (TEXT FILES) or SAVED MODEL Directory
    elif os.path.splitext(parameters.model_path)[1].lower() == "":
        runner = find_keras_pb_model(parameters=parameters,
                                     timer=timer)

        if runner is None:
            logger("Model extension does not exist, running offline validation.",
                   code='INFO')

            runner = OfflineRunner(
                annotation_source=parameters.model_path,
                parameters=parameters,
                timer=timer
            )
    else:
        raise NotImplementedError(
            "Running the model '{}' is currently not supported".format(
                parameters.model_path)
        )
    return runner


def build_evaluator(
    args,
    parameters: CombinedParameters,
    client: Client,
    stage_tracker: StageTracker
) -> Evaluator:
    """
    Intantiate the evaluator object depending on the task.

    Parameters
    ----------
    args: argsparse.NameSpace
        The command line arguments.
    parameters: CombinedParameters
        This object is a container for both model, dataset, and validation
        parameters set from the command line.
    client: Client
        The EdgeFirst Client object.
    stage_tracker: StageTracker
        This contains the stages that tracks each progress in Studio.
        A stage contains ("stage identifier", "stage description").

    Returns
    -------
    Evaluator
        This can be any evaluator object depending on the task such
        as segmentation, detection, multitask, or pose.

    Raises
    ------
    ValueError
        Dataset labels were not found.
    NotImplementedError
        Certain validation types are not yet implemented.
    """
    timer = TimerContext()
    studio_cache = StudioCache(
        parameters=parameters.dataset,
        stage_tracker=stage_tracker,
        client=client,
        session_id=args.session_id,
    )

    dataset = build_dataset(
        args, parameters=parameters.dataset, timer=timer,
        studio_cache=studio_cache, stage_tracker=stage_tracker
    )

    if parameters.dataset.labels is None or len(
            parameters.dataset.labels) == 0:
        raise ValueError(
            "The unique set of string labels from the dataset was not found. " +
            "Try setting --dataset-labels=path/to/labels.txt")

    # Builds the runner and assigns conditions for with_masks or with_boxes.
    runner = build_runner(parameters=parameters.model, timer=timer)

    if parameters.model.labels is None or len(parameters.model.labels) == 0:
        logger("Model labels was not found. " +
               "Falling back to use the dataset labels for the model.",
               code="WARNING")
        # During validation, all model indices will be translated
        # to the dataset indices for a 1-to-1 match.
        parameters.model.labels = parameters.dataset.labels

    # Add the background class in the last index for semantic segmentation.
    if parameters.model.common.with_masks and parameters.model.common.semantic:
        parameters.model.labels += ["background"]
        parameters.dataset.labels += ["background"]

    # Cache the dataset if it doesn't exist.
    # This block is placed after the building the runner object to initialize
    # with_masks and with_boxes conditions needed for iterating the dataset.
    if args.cache is not None and not os.path.exists(args.cache):
        logger("The dataset cache does not exist. " +
               f"Attempting to cache existing dataset to {args.cache}",
               code="INFO")
        dataset = instantiate_dataset(
            info_dataset=dataset.info_dataset,
            parameters=parameters.dataset,
            timer=timer,
            stage_tracker=stage_tracker,
        )
        dataset = studio_cache.cache(dataset, args.cache)
        parameters.dataset.dataset_path = args.cache

    dataset.verify_dataset()

    # If the labels in the dataset and the model do not match,
    # this could be the wrong dataset is being used. Warn the user.
    if abs(len(parameters.dataset.labels) - len(parameters.model.labels)) > 1:
        logger(
            "The model contains {} labels and the dataset contains {} labels. ".format(
                len(parameters.model.labels),
                len(parameters.dataset.labels)
            ) + "Double check that the right dataset '{}' is being used.".format(
                parameters.dataset.dataset_path),
            code="WARNING")

        dataset_labels = parameters.dataset.labels
        model_labels = parameters.model.labels
        if len(dataset_labels) < len(model_labels):
            offset = len(model_labels) - len(dataset_labels)
            parameters.dataset.labels += ["unknown"] * offset
        else:
            offset = len(dataset_labels) - len(model_labels)
            parameters.model.labels += ["unknown"] * offset

    # Multitask Validation
    if parameters.model.common.with_boxes and parameters.model.common.with_masks:
        if parameters.model.common.semantic:
            logger("Detected semantic segmentation model.", code="INFO")
            evaluator = MultitaskValidator(
                parameters=parameters,
                stage_tracker=stage_tracker,
                runner=runner,
                dataset=dataset,
            )
        else:
            # Ultralytics segmentation models are always multitask models.
            evaluator = InstanceSegmentationValidator(
                parameters=parameters,
                stage_tracker=stage_tracker,
                runner=runner,
                dataset=dataset,
            )
    # Segmentation Validation - Always semantic segmentation models.
    elif parameters.model.common.with_masks:
        logger("Detected semantic segmentation model. ", code="INFO")
        evaluator = SemanticSegmentationValidator(
            parameters=parameters,
            stage_tracker=stage_tracker,
            runner=runner,
            dataset=dataset
        )
    # Detection Validation
    elif parameters.model.common.with_boxes:
        evaluator = DetectionValidator(
            parameters=parameters,
            stage_tracker=stage_tracker,
            runner=runner,
            dataset=dataset
        )
    else:
        raise RuntimeError(
            "Both values for `with_boxes` and `with_masks` were set to False.")

    return evaluator


def find_keras_pb_model(
    parameters: ModelParameters,
    timer: TimerContext
) -> Union[KerasRunner, None]:
    """
    Instantiate Keras runners based on pb model extension.

    Parameters
    ----------
    parameters: Parameters
        These are the model parameters loaded by the command line.
    timer: TimerContext
        A timer object handling validation timings in the model.

    Returns
    -------
    Union[KerasRunner, None]
        If 'keras_metadata.pb' or 'saved_model.pb' files exists, then
        the KerasRunner is instantiated. This is the runner object for
        deploying Keras models for inference. Otherwise, None is returned.
    """
    runner = None
    for root, _, files in os.walk(parameters.model_path):
        for file in files:
            if (os.path.basename(file) == "keras_metadata.pb" or
                    os.path.basename(file) == "saved_model.pb"):
                runner = KerasRunner(
                    model=root,
                    parameters=parameters,
                    timer=timer
                )
                break
    return runner


def download_model_artifacts(args, client: Client):
    """
    Download model artifacts in EdgeFirst Studio.

    Parameters
    ----------
    args: argsparse.NameSpace
        The command line arguments.
    client: Client
        The EdgeFirst Studio client object to
        communicate with EdgeFirst Studio.
    """
    session = client.validation_session(session_id=args.session_id)

    train_session_id = session.training_session_id
    model = session.params["model"]

    logger("Downloading model artifacts from train session ID " +
           f"'t-{train_session_id.value:x}'.", code="INFO")

    # Do not auto-download the model, in case offline validation is specified.
    if not os.path.exists(args.model):
        model = str(model)

        try:
            client.download_artifact(
                training_session_id=train_session_id,
                modelname=model,
                filename=model
            )
        except RuntimeError as e:
            if "Status(404" in str(e):
                raise FileNotFoundError(
                    f"The artifact '{model}' does not exist.") from e
            raise e
        args.model = os.path.join(os.path.dirname(args.model), model)

    if args.model_labels is None:
        args.model_labels = "labels.txt"

    if args.config is None:
        args.config = "edgefirst.yaml"

    try:
        client.download_artifact(
            training_session_id=train_session_id,
            modelname=args.model_labels,
            filename=args.model_labels
        )
    except RuntimeError as e:
        if "Status(404" in str(e):
            raise FileNotFoundError(
                "The artifact 'labels.txt' does not exist.") from e
        raise e

    try:
        client.download_artifact(
            training_session_id=train_session_id,
            modelname=args.config,
            filename=args.config
        )
    except RuntimeError as e:
        if "Status(404" in str(e):
            raise FileNotFoundError(
                "The artifact 'edgefirst.yaml' does not exist.") from e
        raise e


def update_parameters(args, client: Client):
    """
    Updates the parameters specified by EdgeFirst Studio.

    Parameters
    ----------
    args: argsparse.NameSpace
        The command line arguments.
    client: Client
        The EdgeFirst Client object.
    """
    session = client.validation_session(args.session_id)

    # If "override" is present, then use the command line parameters.
    # Otherwise, use the parameters specified in the model metadata.
    args.override = "override" not in session.params.keys()
    args.nms_score_threshold = session.params.get("nms_score_threshold",
                                                  args.nms_score_threshold)
    args.nms_iou_threshold = session.params.get("nms_iou_threshold",
                                                args.nms_iou_threshold)


def initialize_studio_client(args) -> Union[Client, None]:
    """
    Initialize the EdgeFirst Client if the validation session ID is set.
    Downloads the model artifacts if it doesn't exist.

    Parameters
    ----------
    args: argsparse.NameSpace
        The command line arguments.

    Returns
    -------
    Union[Client, None]
        The EdgeFirst client object is a bridge of communication between
        EdgeFirst Studio and the applications. Otherwise None is
        returned if the validation session ID is not specified.
    """
    client = None
    if args.session_id is not None:
        if args.session_id.isdigit():
            args.session_id = int(args.session_id)
        logger(f"Detected EdgeFirst Studio validation ID: '{args.session_id}'.",
               code="INFO")

        try:
            client = Client(
                token=args.token,
                username=args.username,
                password=args.password,
                server=args.server
            )
        except RuntimeError as e:
            if "MaxRetries" in str(e):
                raise ValueError(
                    f"Got an invalid server: {args.server}. " +
                    "Check that the right server is set.") from e
            raise e
    return client


def validate(args):
    """
    Instantiates the runners and readers to deploy the model for validation.

    Parameters
    ----------
    args: argsparse.NameSpace
        The command line arguments set.
    """
    set_symbol_condition(args.exclude_symbols)

    client = initialize_studio_client(args)
    studio_publisher = None
    evaluator = None

    if client is not None:
        studio_publisher = StudioPublisher(
            json_path=args.json_out,
            session_id=args.session_id,
            client=client
        )

    # Progress stages are defined in the order inside the `StageTracker` class.
    stage_tracker = StageTracker(studio_publisher=studio_publisher)
    if args.cache is not None:
        stage_tracker.add_stage(
            ("stage_ds_cache", "Caching Validation Dataset"), index=2)

    try:
        if studio_publisher is not None:
            session = client.validation_session(session_id=args.session_id)
            client.set_stages(session.task.id, stage_tracker.tolist())

            download_model_artifacts(args, client=client)
            # Update parameters set from the validation session in studio.
            update_parameters(args=args, client=client)

            parameters = build_parameters(args)
            studio_publisher.json_path = parameters.validation.json_out
        else:
            parameters = build_parameters(args)
        evaluator = build_evaluator(args,
                                    parameters=parameters,
                                    client=client,
                                    stage_tracker=stage_tracker)
    except Exception as e:
        if studio_publisher is not None:
            studio_publisher.update_stage(
                stage="stage_validate",
                status="error",
                message=str(e),
                percentage=0
            )
        if evaluator is not None:
            evaluator.stop()
        error = traceback.format_exc()
        print(error)
        raise e

    if args.session_id is not None:
        studio_progress = StudioProgress(evaluator=evaluator)
        try:
            studio_progress.group_evaluation()
        except Exception as e:
            evaluator.stop()
            raise e
    else:
        try:
            evaluator.group_evaluation()
        except Exception as e:
            evaluator.stop()
            raise e
