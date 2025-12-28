import numpy as np

from minlog import logger
import ncnn


def session_ncnn_init(self):
    log = self.log.logger_for("session_ncnn")
    try:
        self.ncnn_net = ncnn.Net()
        self.ncnn_net.opt.use_vulkan_compute = True
        log.debug(f"loading ncnn model: {self.ncnn_model_file}")
        self.ncnn_net.load_param(self.ncnn_param_file)
        self.ncnn_net.load_model(self.ncnn_model_file)
    except Exception as e:
        # ncnn.destroy_gpu_instance()  # cleanup
        raise Exception(f"failed to load ncnn model: {e}")


def session_ncnn_execute(self, inputs, output_names):
    log = self.log.logger_for("session_ncnn")
    try:
        extractor = self.ncnn_net.create_extractor()
        # for each input, we need to call ex.input
        for input_key, input_value in inputs.items():
            log.debug(
                f"input {input_key}: shape={input_value.shape}, dtype={input_value.dtype}"
            )

            input_mat = ncnn.Mat(input_value)

            log.debug(f"  input_mat {input_key} shape: {input_mat.shape}")
            extractor.input(input_key, input_mat)

        # collect outputs into a list
        outputs_list = []
        for output_key in output_names:
            ret, output = extractor.extract(output_key)
            outputs_list.append(output)

        if ret != 0:
            raise Exception(f"failed to execute ncnn: {ret}")
    except Exception as e:
        # ncnn.destroy_gpu_instance()  # cleanup
        raise Exception(f"failed to execute ncnn: {e}")

    return np.array(outputs_list)
