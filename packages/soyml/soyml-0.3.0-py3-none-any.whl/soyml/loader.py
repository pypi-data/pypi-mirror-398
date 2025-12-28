import os
from .backends import SoyMLBackend
from .session import SoyMLSession
from minlog import logger


class SoyMLLoader(object):
    def __init__(self, model_dir: str, log=None, use_cpu_only=False):
        self.model_dir = model_dir
        self.log = log.logger_for("soyml_loader") if log else logger
        self.use_cpu_only = use_cpu_only

    def load_session(self, model_basename, backend, device_blacklist=[]):
        """
        Load a model session from model file in the model directory.
        :param model_basename: the base name of the model file (without extension/suffix)
        :param backend: the inference backend to use for the model
        :param device_blacklist: a list of devices to blacklist for inference of this model
        """
        model_fnames = self.resolve_model_files(model_basename, backend)
        self.log.debug(f"loading model files: {model_fnames}")

        if backend == SoyMLBackend.ONNXRUNTIME:
            return SoyMLSession(
                log=self.log,
                use_ort=True,
                ort_use_cpu_only=self.use_cpu_only,
                ort_provider_blacklist=device_blacklist,
                ort_model_file=model_fnames[0],
            )
        if backend == SoyMLBackend.NCNN:
            return SoyMLSession(
                log=self.log,
                use_ncnn=True,
                ncnn_param_file=model_fnames[0],
                ncnn_model_file=model_fnames[1],
            )
        if backend == SoyMLBackend.WONNX:
            return SoyMLSession(
                log=self.log,
                use_wonnx=True,
                wonnx_model_file=model_fnames[0],
            )
        if backend == SoyMLBackend.TORCH:
            return SoyMLSession(
                log=self.log,
                use_torch=True,
                torch_model_file=model_fnames[0],
            )

    def resolve_model_files(self, model_basename, backend):
        """
        Resolve model files with fallback support.
        Returns the first existing set of model files.
        Raises FileNotFoundError if no valid files found.
        """
        model_basename = os.path.join(self.model_dir, model_basename)

        if backend == SoyMLBackend.ONNXRUNTIME:
            # try primary path first
            primary = f"{model_basename}.sim.onnx"
            if os.path.exists(primary):
                return [primary]
            # try fallback
            fallback = f"{model_basename}.onnx"
            if os.path.exists(fallback):
                self.log.debug(f"using fallback model path: {fallback}")
                return [fallback]
            raise FileNotFoundError(f"model file {primary} does not exist")

        if backend == SoyMLBackend.NCNN:
            paths = [f"{model_basename}.ncnn.param", f"{model_basename}.ncnn.bin"]
            if all(os.path.exists(p) for p in paths):
                return paths
            raise FileNotFoundError(f"model file {paths[0]} does not exist")

        if backend == SoyMLBackend.WONNX:
            path = f"{model_basename}.web.onnx"
            if os.path.exists(path):
                return [path]
            raise FileNotFoundError(f"model file {path} does not exist")

        if backend == SoyMLBackend.TORCH:
            path = f"{model_basename}.pt"
            if os.path.exists(path):
                return [path]
            raise FileNotFoundError(f"model file {path} does not exist")

        return []
