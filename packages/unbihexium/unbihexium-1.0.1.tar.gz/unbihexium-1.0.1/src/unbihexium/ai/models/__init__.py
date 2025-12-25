"""AI models module providing architecture definitions."""

from unbihexium.ai.models.heads import (
    ClassificationHead,
    DetectionHead,
    DetectionHeadConfig,
    SegmentationHead,
    SegmentationHeadConfig,
)
from unbihexium.ai.models.registry import ModelEntry, ModelRegistry
from unbihexium.ai.models.resnet import BasicBlock, Bottleneck, ResNet, ResNetConfig
from unbihexium.ai.models.unet import DoubleConv, Down, UNet, UNetConfig, Up

__all__ = [
    # UNet
    "UNet",
    "UNetConfig",
    "DoubleConv",
    "Down",
    "Up",
    # ResNet
    "ResNet",
    "ResNetConfig",
    "BasicBlock",
    "Bottleneck",
    # Heads
    "DetectionHead",
    "DetectionHeadConfig",
    "SegmentationHead",
    "SegmentationHeadConfig",
    "ClassificationHead",
    # Registry
    "ModelRegistry",
    "ModelEntry",
]
