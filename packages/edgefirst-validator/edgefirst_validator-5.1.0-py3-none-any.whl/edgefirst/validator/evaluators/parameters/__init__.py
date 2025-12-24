"""
Initialization module for evaluators parameters.
"""
from edgefirst.validator.evaluators.parameters.core import Parameters, CommonParameters
from edgefirst.validator.evaluators.parameters.model import ModelParameters
from edgefirst.validator.evaluators.parameters.dataset import DatasetParameters
from edgefirst.validator.evaluators.parameters.validation import ValidationParameters


class CombinedParameters:
    """
    Container for both model and validation parameters.

    Parameters
    -----------
    model_parameters: ModelParameters
        This is a container of the model parameters.
    dataset_parameters: DatasetParameters
        This is a container of teh dataset parameters.
    validation_parameters: ValidationParameters
        This is a containter of the validation parameters.
    """

    def __init__(
        self,
        model_parameters: ModelParameters = None,
        dataset_parameters: DatasetParameters = None,
        validation_parameters: ValidationParameters = None
    ):
        common_parameters = CommonParameters()
        if model_parameters is None:
            model_parameters = ModelParameters(
                common_parameters=common_parameters)
        if dataset_parameters is None:
            dataset_parameters = DatasetParameters(
                common_parameters=common_parameters)
        if validation_parameters is None:
            validation_parameters = ValidationParameters()

        self.model = model_parameters
        self.dataset = dataset_parameters
        self.validation = validation_parameters

    def to_dict(self):
        """
        Store the parameters as a dictionary.
        """
        return {
            "nms": self.model.nms,
            "nms_max_detections": self.model.max_detections,
            "nms_iou_threshold": self.model.iou_threshold,
            "nms_score_threshold": self.model.score_threshold,
            "normalization": self.model.common.norm,
            "preprocessing": self.model.common.preprocessing,
        }
