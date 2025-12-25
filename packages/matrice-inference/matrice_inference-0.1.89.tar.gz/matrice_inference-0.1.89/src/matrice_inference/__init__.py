"""Module providing __init__ functionality."""

import os
import sys
import platform
import subprocess

from matrice_common.utils import dependencies_check

base = [
    "httpx",
    "fastapi",
    "uvicorn",
    "pillow",
    "confluent_kafka[snappy]",
    "aiokafka",
    "aiohttp",
    "filterpy",
    "scipy",
    "scikit-learn",
    "matplotlib",
    "scikit-image",
    "python-snappy",
    "pyyaml",
    "imagehash",
    "Pillow",
    "transformers"
]

# Helper to attempt installation and verify importability
def _install_and_verify(pkg: str, import_name: str):
    """Install a package expression and return True if the import succeeds."""
    try:
        if pkg=='onnxruntime-gpu':
            pkg = 'onnxruntime'
        __import__(pkg)
        return True
    except:
        if dependencies_check([pkg]):
            try:
                __import__(import_name)
                return True
            except ImportError:
                return False
        return False

# Runtime gating for optional OCR bootstrap (default OFF), and never on Jetson
_ENABLE_OCR_BOOTSTRAP = os.getenv("MATRICE_ENABLE_OCR_BOOTSTRAP", "0")
_IS_JETSON = (platform.machine().lower() in ("aarch64", "arm64"))

print("*******************************Deployment ENV Info**********************************")
print(f"ENABLE_JETSON_PIP_SETTINGS: {_ENABLE_OCR_BOOTSTRAP}") #0 if OFF, 1 if ON, this will be set to 1 in jetson byom codebase.
print(f"IS_JETSON_ARCH?: {_IS_JETSON}") #True if Jetson, False otherwise
print("*************************************************************************************")

if not int(_ENABLE_OCR_BOOTSTRAP) and not _IS_JETSON:
    # Install base dependencies first
    dependencies_check(base)

    if not dependencies_check(["opencv-python"]):
        dependencies_check(["opencv-python-headless"])

    # Attempt GPU-specific dependencies first
    _gpu_ok = _install_and_verify("onnxruntime-gpu", "onnxruntime") and _install_and_verify(
        "fast-plate-ocr[onnx-gpu]", "fast_plate_ocr"
    )

    if not _gpu_ok:
        # Fallback to CPU variants
        _cpu_ok = _install_and_verify("onnxruntime", "onnxruntime") and _install_and_verify(
            "fast-plate-ocr[onnx]", "fast_plate_ocr"
        )
        if not _cpu_ok:
            # Last-chance fallback without extras tag (PyPI sometimes lacks them)
            _install_and_verify("fast-plate-ocr", "fast_plate_ocr")

# matrice_deps = ["matrice_common", "matrice_analytics", "matrice"]

# dependencies_check(matrice_deps)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from server.server import MatriceDeployServer  # noqa: E402
from server.server import MatriceDeployServer as MatriceDeploy  # noqa: E402 # Keep this for backwards compatibility
from server.inference_interface import InferenceInterface  # noqa: E402
from server.proxy_interface import MatriceProxyInterface  # noqa: E402

__all__ = [
    "MatriceDeploy",
    "MatriceDeployServer",
    "InferenceInterface",
    "MatriceProxyInterface",
]