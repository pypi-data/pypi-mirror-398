from collections import defaultdict
from packaging import version
import onnx
from onnx.helper import tensor_dtype_to_string
from termcolor import cprint



class Analyze_onnx_model():
    def __init__(self, onnx_file):
        self.model = onnx.load(onnx_file)
        self.constant_registery = dict()

    def print_dict_one_by_one(self, input_dict):
        for key, value in input_dict.items():
            print(key, value)

    def get_node_dict(self):
        def sort_by_cnt(input_dict):
            tmp = sorted(input_dict.items(), key=lambda x: x[1], reverse=True)
            return dict(tmp)
        nodes = self.model.graph.node
        node_dict = defaultdict(int)
        for node in nodes:
            node_dict[node.op_type] += 1
        return sort_by_cnt(node_dict)

    def get_constant_dict(self):
        def sort_by_size(input_dict):
            tmp = sorted(input_dict.items(), key=lambda x: x[1][0], reverse=True)
            return dict(tmp)
        constants = self.model.graph.initializer
        constant_dict = {}
        for constant in constants:
            val = onnx.numpy_helper.to_array(constant)
            self.constant_registery[constant.name] = val
            constant_dict[constant.name] = [val.size, val.shape, tensor_dtype_to_string(constant.data_type).lstrip("TensorProto.")]
        return sort_by_size(constant_dict)

    def get_value_info_dict(self):
        value_infos = self.model.graph.value_info
        value_info_dict = {}
        for value_info in value_infos:
            value_info_dict[value_info.name] = [[i.dim_value for i in value_info.type.tensor_type.shape.dim], tensor_dtype_to_string(value_info.type.tensor_type.elem_type).lstrip("TensorProto.")]
        return value_info_dict

    def print_info(self):
        cprint("zhijiang, node op info:", "red")
        print(self.print_dict_one_by_one(self.get_node_dict()))

        cprint("zhijiang, constant info:", "red")
        print(self.print_dict_one_by_one(self.get_constant_dict()))

        cprint("zhijiang, value info:", "red")
        print(self.print_dict_one_by_one(self.get_value_info_dict()))
