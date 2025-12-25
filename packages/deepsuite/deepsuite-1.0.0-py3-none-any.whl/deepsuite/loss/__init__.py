"""Init   module."""

from deepsuite.loss.bbox import BboxLoss
from deepsuite.loss.centernet import CenterNetLoss
from deepsuite.loss.detection import DetectionLoss
from deepsuite.loss.dfl import DFLoss
from deepsuite.loss.distill import Distill
from deepsuite.loss.focal import BinaryFocalLoss, FocalLoss, MulticlassFocalLoss
from deepsuite.loss.heat import KeypointHeatmapLoss
from deepsuite.loss.keypoint import KeypointLoss
from deepsuite.loss.language_modeling import (
    LanguageModelingLoss,
    MultiTokenPredictionLoss,
    PerplexityMetric,
    TokenAccuracyMetric,
)
from deepsuite.loss.lwf import LwF
from deepsuite.loss.mel import MelLoss
from deepsuite.loss.rmse import RMSE
from deepsuite.loss.segmentation import SegmentationLoss
from deepsuite.loss.snr import (
    ScaleInvariantSignal2DistortionRatio,
    ScaleInvariantSignal2NoiseRatio,
    Signal2NoiseRatio,
)
from deepsuite.loss.varifocal import VarifocalLoss


def get_loss(name: str, **kwargs):
    loss_map = {
        "bbox": BboxLoss,
        "keypoint": KeypointLoss,
        "focal": FocalLoss,
        "binaryfocal": BinaryFocalLoss,
        "multiclassfocal": MulticlassFocalLoss,
        "detection": DetectionLoss,
        "distill": Distill,
        "dfl": DFLoss,
        "lwf": LwF,
        "mel": MelLoss,
        "rmse": RMSE,
        "segmentation": SegmentationLoss,
        "sdr": Signal2NoiseRatio,
        "si_snr": ScaleInvariantSignal2NoiseRatio,
        "si_sdr": ScaleInvariantSignal2DistortionRatio,
        "varfocal": VarifocalLoss,
        "centernet": CenterNetLoss,
        "keypointhearmap": KeypointHeatmapLoss,
        "languagemodeling": LanguageModelingLoss,
        "mtp": MultiTokenPredictionLoss,
    }
    if name not in loss_map:
        raise ValueError(f"Loss '{name}' nicht gefunden. Verfügbare: {list(loss_map.keys())}")
    return loss_map[name](**kwargs)
