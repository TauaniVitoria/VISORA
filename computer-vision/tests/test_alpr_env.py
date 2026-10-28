"""
Test environment configuration and dependencies for Computer Vision module.
"""

import sys
import yaml
import pytest
import numpy as np


def test_python_version():
    """Verify that Python 3.12+ is used."""
    assert sys.version_info.major == 3
    assert sys.version_info.minor == 12


def test_core_cv_imports():
    """Verify that computer vision core packages are importable."""
    import cv2
    import torch
    import torchvision
    import ultralytics
    import PIL

    assert cv2.__version__ is not None
    assert torch.__version__ is not None
    assert torchvision.__version__ is not None
    assert ultralytics.__version__ is not None
    assert PIL.__version__ is not None


def test_pytorch_device_availability():
    """Verify device detection logic (MPS for Apple Silicon, CUDA, or CPU fallback)."""
    import torch

    device_name = "cpu"
    if torch.backends.mps.is_available():
        device_name = "mps"
    elif torch.cuda.is_available():
        device_name = "cuda"

    # Must be capable of allocating a tensor on the selected device
    device = torch.device(device_name)
    x = torch.ones((2, 2), device=device)
    y = x * 2.0
    assert y.sum().item() == 8.0


def test_config_yaml_loading():
    """Verify that alpr_config.yaml loads properly and contains all required keys."""
    from pathlib import Path

    config_path = Path(__file__).resolve().parent.parent / "config" / "alpr_config.yaml"
    assert config_path.exists(), f"Config file not found at {config_path}"

    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    assert "system" in cfg
    assert "video" in cfg
    assert "vehicle_detection" in cfg
    assert "plate_detection" in cfg
    assert "preprocessor" in cfg
    assert "plate_recognition" in cfg
    assert "plate_validator" in cfg
    assert "tracker" in cfg
    assert "visualizer" in cfg
