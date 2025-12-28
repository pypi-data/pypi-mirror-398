import numpy as np
import onnx
import wonnx as wonnx
from minlog import logger


def session_wonnx_init(self):
    log = self.log.logger_for("session_wonnx")
    try:
        log.debug(f"loading wonnx model: {self.wonnx_model_file}")
        self.wonnx_session = wonnx.Session.from_path(self.wonnx_model_file)
        onnx_model = onnx.load(self.wonnx_model_file)
        # get input/output names and shapes
        self.input_shapes = {}
        self.output_shapes = {}

        def get_dim_shape(dim):
            if dim.HasField("dim_value"):
                return dim.dim_value
            if dim.HasField("dim_param"):
                return dim.dim_param
            raise Exception("invalid dimension")

        for input in onnx_model.graph.input:
            self.input_shapes[input.name] = [
                get_dim_shape(dim) for dim in input.type.tensor_type.shape.dim
            ]
        for output in onnx_model.graph.output:
            self.output_shapes[output.name] = [
                get_dim_shape(dim) for dim in output.type.tensor_type.shape.dim
            ]
        log.debug(f"wonnx input shapes: {self.input_shapes}")
        log.debug(f"wonnx output shapes: {self.output_shapes}")
        del onnx_model
    except Exception as e:
        raise Exception(f"failed to load wonnx model: {e}")


def session_wonnx_execute(self, inputs, output_names):
    log = self.log.logger_for("session_wonnx")
    try:
        # outputs = self.wonnx_session.run(inputs)
        # wonnx python is stupid, and requires you to completely flatten the input
        flat_inputs = {}
        for input_key, input_value in inputs.items():
            flat_inputs[input_key] = input_value.flatten()
            log.trace(
                f"wonnx input {input_key} shape: {input_value.shape} -> flattening to {flat_inputs[input_key].shape}"
            )

        raw_outputs = self.wonnx_session.run(flat_inputs)

        # reshape the outputs
        outputs = {}
        for output_key, output_value in raw_outputs.items():
            this_output_shape = self.output_shapes[output_key]
            np_output_value = np.array(output_value)
            log.trace(
                f"wonnx output {output_key} shape: {np_output_value.shape} -> reshaping to {this_output_shape}"
            )
            outputs[output_key] = np_output_value.reshape(this_output_shape)

        # collect outputs into a list
        outputs_list = []

        for output_name in output_names:
            outputs_list.append(outputs[output_name])

    except Exception as e:
        raise Exception(f"failed to execute wonnx: {e}")
    return np.array(outputs_list)
