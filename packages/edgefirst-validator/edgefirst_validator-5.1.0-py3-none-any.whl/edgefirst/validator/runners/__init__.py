"""
Initializes all available model runners.
"""
from edgefirst.validator.runners.deepviewrt import DeepViewRTRunner
from edgefirst.validator.runners.tensorrt import TensorRTRunner
from edgefirst.validator.runners.offline import OfflineRunner
from edgefirst.validator.runners.tflite import TFliteRunner
from edgefirst.validator.runners.kinara import KinaraRunner
from edgefirst.validator.runners.keras import KerasRunner
from edgefirst.validator.runners.onnx import ONNXRunner
from edgefirst.validator.runners.core import Runner
