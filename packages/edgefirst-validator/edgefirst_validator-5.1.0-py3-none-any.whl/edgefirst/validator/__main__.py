"""
Entry point for the EdgeFirst Validator CLI.
"""

import argparse

try:
    import ctypes
    import inspect
    from pathlib import Path

    import nvidia  # type: ignore

    nvpath = Path(inspect.getfile(nvidia)).parent
    cudnn = nvpath / 'cudnn' / 'lib' / 'libcudnn.so.9'
    if cudnn.exists():
        ctypes.CDLL(cudnn.as_posix(), mode=ctypes.RTLD_GLOBAL)
except ImportError:
    pass

from edgefirst.validator import __version__
from edgefirst.validator.validate import validate


def main():
    """
    Main function for the EdgeFirst Validator CLI.
    Parses command-line arguments and initiates the validation process.
    """
    parser = argparse.ArgumentParser(
        description=('EdgeFirst Validator'),
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '-V', '--version',
        help="Print the package version.",
        action='version',
        version=__version__
    )
    parser.add_argument(
        'model',
        help=("The path to the model: \n"
              "- TensorFlow or Keras (**/*.pb), (.h5), (.keras) \n"
              "- TFLite (.tflite) \n"
              "- ONNX (.onnx) \n"
              "- DeepViewRT (.rtm) \n"
              "- Offline (directory of model annotations)."),
        metavar='model.onnx',
        nargs="?",
        type=str,
        default="yolov5s.onnx"
    )
    parser.add_argument(
        'dataset',
        help=("The absolute or relative path "
              "to the dataset folder or YAML file."),
        metavar='dataset.yaml',
        nargs="?",
        type=str,
        default='samples/coco128.yaml'
    )

    studio_parser = parser.add_argument_group(
        title="EdgeFirst Studio Parameters",
        description=("Specify the interface parameters "
                     "for a direct communication with EdgeFirst Studio.")
    )
    studio_parser.add_argument(
        '--token',
        help="EdgeFirst Studio authentication token.",
        type=str,
    )
    studio_parser.add_argument(
        '--server',
        help="EdgeFirst Studio server.",
        type=str,
    )
    studio_parser.add_argument(
        '--username',
        help="EdgeFirst Studio username.",
        type=str,
    )
    studio_parser.add_argument(
        '--password',
        help="EdgeFirst Studio password.",
        type=str,
    )
    studio_parser.add_argument(
        '--session-id',
        help="Specify the validator session ID from EdgeFirst Studio.",
        type=str,
    )

    model_parser = parser.add_argument_group(
        title="Model Parameters",
        description="Specify how the model should be run with these parameters."
    )
    model_parser.add_argument(
        '--config',
        help=("Specify the path to 'edgefirst.yaml' "
              "containing the model metadata. This overrides "
              "the metadata embedded in the model."),
        type=str
    )
    model_parser.add_argument(
        '--model-labels',
        help=("Specify the path to the model labels file. This artifact is a "
              "labels.txt file containing model string labels. This is "
              "used to align model output indices to the ground truth indices."),
        type=str,
    )
    model_parser.add_argument(
        '-i', '--nms-iou-threshold',
        help="NMS IoU threshold for valid predictions.",
        default=0.70,
        type=float
    )
    model_parser.add_argument(
        '-t', '--nms-score-threshold',
        help="Set the NMS score threshold for valid scores.",
        default=0.001,
        type=float
    )
    model_parser.add_argument(
        '-m', '--max-detections',
        help="Number of maximum detections for NMS.",
        default=300,
        type=int
    )
    model_parser.add_argument(
        '-e', '--engine',
        help=("Inference Engine. Options include 'cpu', 'gpu', "
              "or a path to the NPU delegate '/usr/lib/libvx_delegate.so'."),
        default='npu',
        type=str
    )
    model_parser.add_argument(
        '-s', '--nms',
        help=("Specify the NMS algorithm. "
              "Default to use the NMS from the HAL decoder."),
        choices=['hal', 'numpy', 'tensorflow', 'torch'],
        default='numpy',
        type=str
    )
    model_parser.add_argument(
        '-n', '--norm',
        help=("Normalization method applied to input images.\n "
              "- raw (default, no processing)\n "
              "- unsigned (0...1)\n "
              "- signed (-1...1)\n "
              "- imagenet (standardization using imagenet)\n "),
        choices=['raw', 'unsigned', 'signed', 'imagenet'],
        default='unsigned',
        type=str
    )
    model_parser.add_argument(
        '-p', '--preprocessing',
        help=("The type of image preprocessing to perform. \n"
              "- letterbox: YOLOv5, YOLOv7 implementation. \n"
              "- pad: Image padding based on YOLOx implementation. \n"
              "- resize: Does not maintain aspect ratio."),
        choices=['letterbox', 'pad', 'resize'],
        default='letterbox',
        type=str
    )
    model_parser.add_argument(
        '-b', '--box-format',
        help=("box format to reorient the bounding box "
              "coordinates: 'xcycwh' (yolo), 'xywh' (coco), "
              "'xyxy' (pascalvoc)."),
        choices=['xcycwh', 'xywh', 'xyxy'],
        default='xyxy',
        type=str
    )
    model_parser.add_argument(
        '-w', '--warmup',
        help="The number of model warmup iterations.",
        default=5,
        type=int
    )
    model_parser.add_argument(
        '-l', '--label-offset',
        help="Label offset when mapping index to string representations.",
        default=0,
        type=int
    )
    model_parser.add_argument(
        '--class-nms',
        help=("By default class-agnostic NMS is deployed. "
              "Specify this option to deploy class-based NMS. "),
        action='store_true'
    )
    model_parser.add_argument(
        '--override',
        help=("This parameter is set to False by default. "
              "When True, this will use the model "
              "parameters specified in the model metadata "
              "to validate the model. Otherwise, the "
              "command line parameters set are applied."),
        action='store_true'
    )

    dataset_parser = parser.add_argument_group(
        title="Dataset Parameters",
        description="Specify how the dataset should be read with these parameters."
    )
    dataset_parser.add_argument(
        '--cache',
        help=("Specify the path to cache the dataset "
              "or an existing dataset cache. A dataset cache is an LMDB file."),
        metavar="cache/val.db",
        type=str,
    )
    dataset_parser.add_argument(
        '--dataset-labels',
        help=("Specify the path to the dataset labels.txt file. \n"
              "This can be stored inside the dataset folder "
              "to avoid having to specify this path. \n"
              "Otherwise, the YAML file can embed the labels. \n"
              "This is used to map dataset indices to strings representations."),
        type=str
    )
    dataset_parser.add_argument(
        '--annotation-format',
        help=("Specify the format of the annotations: "
              "'xcycwh' (yolo), 'xywh' (coco), 'xyxy' (pascalvoc)."),
        choices=['xcycwh', 'xywh', 'xyxy'],
        default='xcycwh',
        type=str
    )
    dataset_parser.add_argument(
        '--absolute-annotations',
        help=("This specifies that the annotations "
              "are not normalized to the image dimensions. "
              "Otherwise, by default the annotations "
              "are normalized."),
        action='store_false'
    )
    dataset_parser.add_argument(
        '--gt-label-offset',
        help=("The label offset to use for the ground truth "
              "mapping integer labels to string labels."),
        default=0,
        type=int
    )
    dataset_parser.add_argument(
        '--backend',
        help="Specify the library to use for input preprocessing",
        choices=["hal", "opencv", "pillow"],
        default="pillow",
        type=str
    )
    dataset_parser.add_argument(
        '--show-missing-annotations',
        help="List the images without annotations on the terminal",
        action='store_true'
    )

    val_parser = parser.add_argument_group(
        title="Validation Parameters",
        description=("Specify additional validation settings "
                     "for metric computations and visualizations.")
    )
    val_parser.add_argument(
        '--suppress-deployment-metrics',
        help=("Deployment metrics are not calculated/reported. Conventional "
              "metrics as seen in Ultralytics will only be reported."),
        action="store_false"
    )
    val_parser.add_argument(
        '--metric',
        help=("Specify the metric to use when "
              "matching model predictions to ground truth."),
        choices=['iou', 'centerpoint'],
        default='iou',
        type=str
    )
    val_parser.add_argument(
        '--matching-leniency',
        help=("Distance metric to be considered a valid match "
              "when using the 'centerpoint' metric. "
              "Default is 2 where the distance is no "
              "more than twice the size of the bounding box. \n"),
        default=2,
        type=int
    )
    val_parser.add_argument(
        '--clamp-boxes',
        help=("The value to clamp the minimum width or height "
              "of the bounding boxes of the ground truth and "
              "predictions in pixels."),
        type=int
    )
    val_parser.add_argument(
        '--ignore-boxes',
        help=("Ignore the bounding boxes "
              "of the detections and the ground truth with "
              "height or width less than this value in pixels."),
        type=int
    )
    val_parser.add_argument(
        '--display',
        help=("How many images to display into tensorboard "
              "or to save in disk. By default it is (-1) all "
              "the images are saved. but any integer can be passed."),
        default=-1,
        type=int
    )
    val_parser.add_argument(
        '--suppress-plots',
        help=("Specify to exclude the plots data in the "
              "JSON summary and/or save the plots as images if "
              "visualize or tensorboard parameter is set."),
        action="store_false"
    )
    val_parser.add_argument(
        '--visualize',
        help=("Path to store visualizations "
              "(images with bounding boxes "
              "or segmentation masks) in disk."),
        type=str
    )
    val_parser.add_argument(
        '--tensorboard',
        help="Path to store *.tfevents files in disk needed for Tensorboard.",
        type=str
    )
    val_parser.add_argument(
        '--json-out',
        help=("Path to save the validation JSON files in disk. These files "
              "are typically formatted as ApexCharts for EdgeFirst Studio "
              "visualizations."),
        type=str
    )
    val_parser.add_argument(
        '--csv',
        help=("Path to save a CSV file to store the metrics into a table. "
              "If the CSV file already exists, it appends a new row to "
              "the contents. Otherwise the CSV file is created."),
        metavar="metrics.csv",
        type=str
    )
    val_parser.add_argument(
        '--include-background',
        help=("This is used for segmentation. "
              "This allows evaluation of the "
              "background class as part of validation."),
        action="store_true"
    )
    val_parser.add_argument(
        '--exclude-symbols',
        help=("Specify whether to exclude symbols when "
              "logging messages on the terminal."),
        action="store_false"
    )
    args = parser.parse_args()

    validate(args)


if __name__ == '__main__':
    main()
