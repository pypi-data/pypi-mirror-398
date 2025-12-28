from enum import Enum


class SoyMLBackend(Enum):
    UNKNOWN = 0
    ONNXRUNTIME = 1
    NCNN = 2
    WONNX = 3
    TORCH = 4


def parse_backend_id(id: str) -> SoyMLBackend:
    if id == "ort":
        return SoyMLBackend.ONNXRUNTIME
    elif id == "ncnn":
        return SoyMLBackend.NCNN
    elif id == "wonnx":
        return SoyMLBackend.WONNX
    elif id == "torch":
        return SoyMLBackend.TORCH
    else:
        return SoyMLBackend.UNKNOWN
