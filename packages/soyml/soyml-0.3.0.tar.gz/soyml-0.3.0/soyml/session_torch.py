import numpy as np
import onnx
import torch
from minlog import logger


def session_torch_init(self):
    log = self.log.logger_for("session_torch")
    # load torch model from file
    try:
        log.debug(f"loading torch model: {self.torch_model_file}")
        self.torch_model = torch.load(self.torch_model_file)
        self.torch_model.eval()
    except Exception as e:
        raise Exception(f"failed to load torch model: {e}")


def session_torch_execute(self, inputs, output_names):
    log = self.log.logger_for("session_torch")
    try:
        torch_inputs = []
        for input_key, input_value in inputs.items():
            torch_inputs.append(torch.from_numpy(input_value))

        # print(self.torch_model)
        torch_outputs = self.torch_model(*torch_inputs)

        output_list = []

        if isinstance(torch_outputs, torch.Tensor):
            single_output = torch_outputs.detach().numpy()
            output_list.append(single_output)
        elif isinstance(torch_outputs, tuple):
            for output in torch_outputs:
                single_output = output.detach().numpy()
                output_list.append(single_output)

    except Exception as e:
        raise Exception(f"failed to execute torch: {e}")

    return output_list
