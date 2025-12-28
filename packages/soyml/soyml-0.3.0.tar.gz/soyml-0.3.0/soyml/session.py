from typing import List, Dict, Tuple, Any, Optional

from .backends import SoyMLBackend
from minlog import logger


class SoyMLSession(object):
    def __init__(
        self,
        log: Optional[Any] = None,
        use_ort: bool = False,
        ort_use_cpu_only: bool = False,
        ort_provider_blacklist: List[str] = [],
        ort_model_file: Optional[str] = None,
        use_ncnn: bool = False,
        ncnn_param_file: Optional[str] = None,
        ncnn_model_file: Optional[str] = None,
        use_wonnx: bool = False,
        wonnx_model_file: Optional[str] = None,
        use_torch: bool = False,
        torch_model_file: Optional[str] = None,
    ):
        self.log = log.logger_for("soyml_session") if log else logger

        self.backend = SoyMLBackend.UNKNOWN
        if use_ort:
            self.backend = SoyMLBackend.ONNXRUNTIME
            self.ort_model_file = ort_model_file
            # load the model
            from .session_ort import session_ort_init

            session_ort_init(self, use_cpu_only=ort_use_cpu_only, provider_blacklist=ort_provider_blacklist)
        if use_ncnn:
            self.backend = SoyMLBackend.NCNN
            self.ncnn_param_file = ncnn_param_file
            self.ncnn_model_file = ncnn_model_file
            # load the model
            from .session_ncnn import session_ncnn_init

            session_ncnn_init(self)

        if use_wonnx:
            self.backend = SoyMLBackend.WONNX
            self.wonnx_model_file = wonnx_model_file
            # load the model
            from .session_wonnx import session_wonnx_init

            session_wonnx_init(self)

        if use_torch:
            self.backend = SoyMLBackend.TORCH
            self.torch_model_file = torch_model_file
            # load the model
            from .session_torch import session_torch_init

            session_torch_init(self)

        self.log.trace(f"initialized session with backend {self.backend}")

    def execute(self, inputs: Dict[str, Any], output_names: List[str]):
        inputs_str = [
            f"{input_key}{input_value.shape}"
            for input_key, input_value in inputs.items()
        ]
        self.log.debug(f"executing ({self.backend}): {inputs_str} -> {output_names}")

        if self.backend == SoyMLBackend.ONNXRUNTIME:
            from .session_ort import session_ort_execute

            outputs = session_ort_execute(self, inputs, output_names)
        if self.backend == SoyMLBackend.NCNN:
            from .session_ncnn import session_ncnn_execute

            outputs = session_ncnn_execute(self, inputs, output_names)
        if self.backend == SoyMLBackend.WONNX:
            from .session_wonnx import session_wonnx_execute

            outputs = session_wonnx_execute(self, inputs, output_names)
        if self.backend == SoyMLBackend.TORCH:
            from .session_torch import session_torch_execute

            outputs = session_torch_execute(self, inputs, output_names)

        outputs_str = [
            f"{output_name}@{output_value.dtype}{output_value.shape}"
            for output_name, output_value in zip(output_names, outputs)
        ]
        self.log.debug(f"  outputs: {outputs_str}")

        return outputs
