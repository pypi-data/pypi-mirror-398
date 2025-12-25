import pdb
from termcolor import cprint
try:
    import torch
    import torch.cuda.nvtx as nvtx
except ImportError:
    print("# import torch or nvtx error, so skip the following code")


def zhijiang_torch_add_nvtx(
    torch_module, nvtx_prefix="", use_class_name=False, apply_depth=3
):
    """
    add nvtx range to torch module
    if use_class_name then nvtx_prefix will be module's class name otherwise its name

    if not all submodules called in forward, then submodules's hook may called before the parent module's
    """
    if apply_depth <= 0:
        return

    def forward_start_hook(module, args, kwargs=None):
        if getattr(module, "forward_id", None) is None:
            module.forward_id = nvtx.range_start((module.nvtx_prefix + ".forward").lstrip("."))
            # print(f"forward_start_hook: {nvtx_prefix}.forward, id is {module.forward_id}, module id is {id(module)}")

    def forward_end_hook(module, args, kwargs=None):
        if getattr(module, "forward_id", None):
            nvtx.range_end(module.forward_id)
            # print(f"forward_end_hook: {nvtx_prefix}.forward, id is {module.forward_id}, module id is {id(module)}")
            module.forward_id = None

    def backward_start_hook(module, args, kwargs=None):
        if getattr(module, "backward_id", None) is None:
            module.backward_id = nvtx.range_start((module.nvtx_prefix + ".backward").lstrip("."))
            # print(f"backward_start_hook: {nvtx_prefix}.backward, id is {module.backward_id}, module id is {id(module)}")

    def backward_end_hook(module, args, kwargs=None):
        if getattr(module, "backward_id", None):
            nvtx.range_end(module.backward_id)
            # print(f"backward_end_hook: {nvtx_prefix}.backward, id is {module.backward_id}, module id is {id(module)}")
            module.backward_id = None

    if use_class_name:
        nvtx_prefix = torch_module._get_name()

    torch_module.nvtx_prefix = nvtx_prefix
    torch_module.register_forward_pre_hook(forward_start_hook)
    torch_module.register_forward_hook(forward_end_hook)
    torch_module.register_full_backward_pre_hook(backward_start_hook)
    torch_module.register_full_backward_hook(backward_end_hook)

    for name, module in torch_module.named_children():
        new_nvtx_prefix = f"{nvtx_prefix}.{name}".lstrip(".").rstrip(".")
        zhijiang_torch_add_nvtx(
            module, nvtx_prefix=new_nvtx_prefix, apply_depth=apply_depth - 1
        )


def zhijiang_torch_find_nan(torch_module):
    def check_nan(module, inputs, output):
        for i in inputs:
            if not isinstance(i, torch.Tensor):
                continue
            if torch.isnan(i).any() or torch.isinf(i).any():
                pdb.set_trace()
        for i in output:
            if not isinstance(i, torch.Tensor):
                continue
            if torch.isnan(i).any() or torch.isinf(i).any():
                pdb.set_trace()

    def register_nan_hook(module):
        module.register_forward_hook(check_nan)

    torch_module.apply(register_nan_hook)


def zhijiang_torch_output_module_inputs_outputs(module, max_depth=None, num_elems=0):
    def _tensor_value_id(x, k=0):
        """
            max, min, sum, numel, selected first k and last k elements
        """
        max_value = x.max()
        min_value = x.min()
        sum_value = x.sum()
        numel = torch.tensor(x.numel(), dtype=max_value.dtype)
        res = [max_value, min_value, sum_value, numel]
        if k>0:
            separator = torch.tensor([88888], dtype=max_value.dtype)
            num_elems = min(k, x.numel())
            selected_index = [i for i in range(num_elems)] + [-i for i in range(num_elems)]
            selected_elems = x.flatten()[selected_index]
            res += [separator]
            res += selected_elems.tolist()
        return torch.tensor(res)

    def _register_forward_hook(module, hook_fn, max_depth=None, current_depth=0, module_name=""):
        """
            register hook to all leaf modules if the depth is less than max_depth
        """
        if max_depth is not None and current_depth > max_depth:
            return

        module.register_forward_hook(hook_fn, with_kwargs=True)
        module.zhijiang_module_name = module_name
        for name, child_module in module.named_children():
            name = name if module_name == "" else module_name + "." + name
            _register_forward_hook(child_module, hook_fn, max_depth, current_depth + 1, name)

    def print_model_input(module, args, kwargs, outputs):
        assert isinstance(args, tuple), f"args should be a tuple, but got {type(args)}"
        assert isinstance(kwargs, dict), f"kwargs should be a dict, but got {type(kwargs)}"
        input_tensors_id = [_tensor_value_id(x, k=num_elems) for x in args if isinstance(x, torch.Tensor)]
        input_tensors_id += [_tensor_value_id(x, k=num_elems) for x in kwargs.values() if isinstance(x, torch.Tensor)]

        if isinstance(outputs, torch.Tensor):
            outputs = [outputs]
        output_tensors_id = [_tensor_value_id(x, k=num_elems) for x in outputs if isinstance(x, torch.Tensor)]
        if module.zhijiang_module_name == "":
            cprint("zhijiang, this is the top module", "red")
            cprint("only hook the module, if torch.function is called, then the tensor id may not matched", "red")
        else:
            print(f"zhijiang, module name: {module.zhijiang_module_name}")
        print("the tensor id(max, min, sum, numel, k elems) of inputs/outputs are:")
        print(input_tensors_id)
        print(output_tensors_id)

    _register_forward_hook(module, print_model_input, max_depth)

class _zhijiang_ORT_print(torch.autograd.Function):
    """
    a python op to print tensor
    """

    @staticmethod
    def forward(ctx, input_tensor):
        print("", end="", flush=True)
        print(f"zhijiang, input_tensor: {input_tensor}", flush=True)
        return input_tensor

    @staticmethod
    def backward(ctx, grad_output):
        return grad_output
