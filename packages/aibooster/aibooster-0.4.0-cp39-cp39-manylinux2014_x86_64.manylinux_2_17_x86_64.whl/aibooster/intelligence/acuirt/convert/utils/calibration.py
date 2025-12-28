import os.path
from typing import Sequence, Union

import tensorrt as trt


class Calibrator(trt.IInt8Calibrator):
    def __init__(
        self,
        data: Sequence[tuple],
        algorithm=trt.CalibrationAlgoType.ENTROPY_CALIBRATION_2,
        cache_file: Union[str, None] = None,
    ):
        super().__init__()
        self.algorithm = algorithm
        self.idx = 0
        self.cache_file = cache_file

        self.onnx_inputs_list = data
        self.num_calibration = len(data)

    def get_batch(self, names):
        if self.idx < len(self.onnx_inputs_list):
            args, kwargs = self.onnx_inputs_list[self.idx]
            bindings = [int(input.cuda().data_ptr()) for input in args] + [
                int(input.cuda().data_ptr) for input in kwargs.values()
            ]
            self.idx += 1
            return bindings
        else:
            return []

    def get_batch_size(self):
        return 1

    def get_algorithm(self):
        return self.algorithm

    def read_calibration_cache(self):
        if (self.cache_file is not None) and os.path.exists(self.cache_file):
            with open(self.cache_file, "rb") as fd:
                return fd.read()

    def write_calibration_cache(self, cache):
        if self.cache_file is not None:
            with open(self.cache_file, "wb") as fd:
                fd.write(cache)
