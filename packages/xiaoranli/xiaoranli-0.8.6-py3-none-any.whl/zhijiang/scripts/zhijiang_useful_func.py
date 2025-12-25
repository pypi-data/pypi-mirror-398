import os
import sys
import threading
import pdb
from functools import wraps
import atexit
import time
from tempfile import mkdtemp
import inspect
from typing import Any
from termcolor import cprint
from types import MethodType

from .useful_func_for_project import *
from .tracer import PyTracer


def get_torch_module(model):
    if "deepspeed" in str(type(model)):
        return get_torch_module(model.module)
    elif "onnxruntime" in str(type(model)):
        return get_torch_module(model.module)
    else:
        return model


def __zhijiang_is_rank_x(index):
    if index == -1:
        return True
    if os.environ.get("LOCAL_RANK", "0") == str(index):
        return True
    return False


def _zhijiang_only_rank_0(func):
    """
    only rank 0 will run the function, other ranks will not
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        if __zhijiang_is_rank_x(0):
            return func(*args, **kwargs)

    return wrapper


def _zhijiang_run_once(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not wrapper.has_run:
            wrapper.has_run = True
            return func(*args, **kwargs)

    wrapper.has_run = False
    return wrapper


@_zhijiang_run_once
def zhijiang_vscode_attach(sleep_time_sec=3, rank=0, other_ranks_continue=True):
    """
    only rank 0 will wait for vscode debug attach, other rank continue to run
    rank -1 means every rank will compete to be attached
    """
    if __zhijiang_is_rank_x(rank):
        import debugpy
        try:
            debugpy.listen(("localhost", 56789))
            # so the next print can be shown at last line of terminal in multiprocess case
            time.sleep(sleep_time_sec)
            stack = inspect.stack()
            caller_frame = stack[2]
            location = f"{caller_frame.filename}:{caller_frame.lineno}"
            cprint(
                f"\n\nzhijiang, waiting at {location} for debug connect, pid is {os.getpid()} \n\n",
                color="red",
                flush=True,
            )
            debugpy.wait_for_client()
            cprint(
                f"\n\nzhijiang,debug connection done, pid is {os.getpid()} \n\n",
                color="red",
                flush=True,
            )
            #try:
            #    import torch
            #    torch.set_printoptions(profile="full", precision=6, sci_mode=False)
            #except:
            #    pass
        except:
            cprint("zhijiang, debug connection failed", color="red", flush=True)
    elif not other_ranks_continue:
        time.sleep(10000000)


def zhijiang_do_bench(
    fn,
    warmup=25,
    rep=100,
    grad_to_none=None,
    percentiles=(0.5, 0.2, 0.8),
    fast_flush=False,
):
    """
    example call: do_bench(lambda: matmul(a,b))

    time unit is ms
    Benchmark the runtime of the provided function. By default, return the median runtime of :code:`fn` along with
    the 20-th and 80-th performance percentile.

    :param fn: Function to benchmark
    :type fn: Callable
    :param warmup: Warmup time (in ms)
    :type warmup: int
    :param rep: Repetition time (in ms)
    :type rep: int
    :param grad_to_none: Reset the gradient of the provided tensor to None
    :type grad_to_none: torch.tensor, optional
    :param percentiles: Performance percentile to return in addition to the median.
    :type percentiles: list[float]
    :param fast_flush: Use faster kernel to flush L2 between measurements
    :type fast_flush: bool
    """
    # Estimate the runtime of the function
    import torch

    fn()
    torch.cuda.synchronize()
    start_event = torch.cuda.Event(enable_timing=True)
    end_event = torch.cuda.Event(enable_timing=True)
    start_event.record()
    for _ in range(5):
        fn()
    end_event.record()
    torch.cuda.synchronize()
    estimate_ms = start_event.elapsed_time(end_event) / 5
    # compute number of warmup and repeat
    n_warmup = max(1, int(warmup / estimate_ms))
    n_repeat = max(1, int(rep / estimate_ms))
    # We maintain a buffer of 256 MB that we clear
    # before each kernel call to make sure that the L2
    # doesn't contain any input data before the run
    start_event = [torch.cuda.Event(enable_timing=True) for i in range(n_repeat)]
    end_event = [torch.cuda.Event(enable_timing=True) for i in range(n_repeat)]
    if fast_flush:
        cache = torch.empty(int(256e6 // 4), dtype=torch.int, device="cuda")
    else:
        cache = torch.empty(int(256e6), dtype=torch.int8, device="cuda")
    # Warm-up
    for _ in range(n_warmup):
        fn()
    # Benchmark
    for i in range(n_repeat):
        # we don't want `fn` to accumulate gradient values
        # if it contains a backward pass. So we clear the
        # provided gradients
        if grad_to_none is not None:
            for x in grad_to_none:
                x.grad = None
        # we clear the L2 cache before each run
        cache.zero_()
        # record time of `fn`
        start_event[i].record()
        fn()
        end_event[i].record()
    # Record clocks
    torch.cuda.synchronize()
    times = torch.tensor([s.elapsed_time(e) for s, e in zip(start_event, end_event)])
    if percentiles:
        percentiles = torch.quantile(times, torch.tensor(percentiles)).tolist()
        return f"{tuple(percentiles)}   ms"
    else:
        return f"{torch.mean(times).item()} ms"


def zhijiang_cuda_profiling(
    step, file_prefix="trace", start_step=20, STOP_STEP=30, only_rank_0=False, nvtx_msg="",
    model=None, apply_depth=3
):
    """
    used for viztracer, nsys, torch cuda mem prof
    the environment variable and their possible values are:
        - VIZTRACER, 0/1
        - NSYS, 0/1
        - START_STEP, any integer larger than 0
        - STOP_STEP, will force STOP_STEP >= start_step+10, STOP_STEP is excluded from profiling
        - FILE_PREFIX >> used to name the output of viztracer
    if model is given, then will register nvtx hooks for it
    """
    if only_rank_0 and not __zhijiang_is_rank_x(0):
        return

    if model and not hasattr(model, "add_nvtx_hooks"):
        zhijiang_torch_add_nvtx(model, apply_depth=apply_depth, use_class_name=False)
        model.add_nvtx_hooks = True

    import torch
    from viztracer import VizTracer
    start_step = int(os.environ.get("START_STEP", default=start_step))
    STOP_STEP = int(os.environ.get("STOP_STEP", STOP_STEP))
    file_prefix = os.environ.get("FILE_PREFIX", file_prefix)

    if os.environ.get("VIZTRACER", "0") == "1":
        assert (
            os.environ["CUDA_LAUNCH_BLOCKING"] == "1"
        ), "CUDA_LAUNCH_BLOCKING must be set to 1 when using VizTracer to profile CUDA code"
        output_file = f"{file_prefix}_rank_{os.environ.get('LOCAL_RANK', 0)}.json"
        if step == 1:
            global tracer
            tracer = VizTracer(output_file=output_file, tracer_entries=100000000)
        if step == start_step:
            cprint("zhijiang, Start tracing", "red")
            tracer.start()
        if step == STOP_STEP:
            cprint("zhijiang, Stop tracing", "red")
            tracer.stop()
            tracer.save()
            sys.exit(0)

    if os.environ.get("NSYS", "0") == "1":
        assert (
            os.environ.get("CUDA_LAUNCH_BLOCKING", "0") != "1"
        ), "CUDA_LAUNCH_BLOCKING must not be set to 1 when using nsys"

        full_nvtx_msg = f"{step}-{nvtx_msg}"
        if step > start_step and step < STOP_STEP:
            torch.cuda.nvtx.range_pop()
            torch.cuda.nvtx.range_push(full_nvtx_msg)

        if step == start_step:
            cprint("zhijiang, Start tracing", "red")
            torch.cuda.cudart().cudaProfilerStart()
            torch.cuda.nvtx.range_push(full_nvtx_msg)
        if step == STOP_STEP:
            cprint("zhijiang, Stop tracing", "red")
            torch.cuda.nvtx.range_pop()
            torch.cuda.cudart().cudaProfilerStop()
            sys.exit(0)

    if os.environ.get("TORCH_CUDA_MEM_PROFILER", "0") == "1":
        if step == start_step:
            cprint("zhijiang, Start mem-tracing", "red")
            torch.cuda.memory._record_memory_history()
        if step == STOP_STEP:
            output_file = f"{file_prefix}_rank_{os.environ.get('LOCAL_RANK', 0)}.pickle"
            torch.cuda.memory._dump_snapshot(output_file)
            cprint("zhijiang, Stop mem-tracing", "red")
            os.abort()


@_zhijiang_run_once
def zhijiang_pdb(rank=0):
    """
    only rank 0 will enter pdb, other ranks continue execution
    """
    if __zhijiang_is_rank_x(rank):
        cprint(f"zhijiang, i am rank {rank}, enter pdb now", "red")
        pdb.set_trace()


@_zhijiang_run_once
def zhijiang_enter_pdb_at_exception():
    """
    register a hook which will enter pdb when process wants to exit, this will help debugging when process has un-caught exception
    """
    atexit.register(pdb.pm)


def zhijiang_get_obj_source(functor, return_src=False):
    """
    input python function object, will return and print its source code to stdout
    """
    src = inspect.getsource(functor)
    print(src)
    if return_src:
        return src


@_zhijiang_run_once
def zhijiang_stackprinter_at_exception():
    import stackprinter

    stackprinter.set_excepthook(style="darkbg2")


def zhijiang_watch(arg1, **kwargs):
    """
    _zhijiang_watch_function(func, action, ignore_cnt=0)
    _zhijiang_watch_object(variable, deepcopy=True, file=None, cmp=None, alias=None, when=None)
    """

    def _zhijiang_watch_object(
        variable, deepcopy=True, file=None, cmp=None, alias=None, when=None
    ):
        """
        "file" means log file of "watch" output
        "alias" is a string, can be used in "unwatch" function

        compare with calling "watch" directly, only "object" is tracked, it means "x = 8" will not be tracked, while "x[0] = 8" will be tracked
        """
        from watchpoints import watch
        import torch

        if isinstance(variable, torch.Tensor) and cmp is None:

            def tensor_cmp(a, b):
                return not (a == b).all()

            cmp = tensor_cmp
        watch(
            variable,
            deepcopy=deepcopy,
            file=file,
            cmp=cmp,
            alias=alias,
            when=when,
            track="object",
        )

    def _zhijiang_watch_function(func, action=None, ignore_cnt=0):
        """
        track "func"'s return value, if changed then take "action"(by default will print file:line_no)
        "ignore_cnt" is used to ignore the first "ignore_cnt" times of value change

        "func" does not take any argument;
        "action" takes (frame, event, arg); by default it print file:line_no
        """

        class _WatchFunc:
            def __init__(self, func_to_trace, action, ignore_cnt):
                self._func_to_trace = func_to_trace
                self._action = action
                self._ignore_cnt = ignore_cnt

                self._zhijiang_watch = None
                self._zhijiang_watch_cnt = -1
                self._prev_frame = None

            def __call__(self, frame, event, arg=None) -> Any:
                if event == "c_return" or event == "return":
                    return_val = self._func_to_trace()
                    if self._zhijiang_watch != return_val:
                        if self._zhijiang_watch_cnt < self._ignore_cnt:
                            self._zhijiang_watch_cnt += 1
                        else:
                            self._action(frame, event, arg)
                        self._zhijiang_watch = return_val

        if action is None:

            def _func(frame, event, arg=None):
                try:
                    code = frame.f_code
                    file_name = code.co_filename
                    func_name = code.co_name
                    line_no = frame.f_lineno
                    print(f"value changed, after line at {file_name}:{line_no}")
                except Exception as e:
                    print(e)
                    print("exception happened, this is ok during process exit")

            action = _func

        callable_obj = _WatchFunc(func, action, ignore_cnt)
        threading.setprofile(callable_obj)
        sys.setprofile(callable_obj)

    if callable(arg1):
        _zhijiang_watch_function(arg1, **kwargs)
    else:
        _zhijiang_watch_object(arg1, **kwargs)


@_zhijiang_only_rank_0
def _zhijiang_open_onnx_in_tensorboard(model, port):
    """
    give the onnx model path and tensorboard port, then will convert to tensorboard and launch tensorboard automatically for you
    """
    os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
    tmp_dir = mkdtemp(prefix="onnx-tensorboard-")
    cprint(f"converted tensorboard is put at {tmp_dir}", "red")
    os.system(
        f"python /home/zhijiang/onnxruntime/tools/python/onnx2tfevents.py --logdir={tmp_dir} --model {model}"
    )
    os.system(f"tensorboard --logdir={tmp_dir} --port {port} &")
    # auto open local web browser!
    import webbrowser

    webbrowser.open_new_tab(f"http://localhost:{port}")

    time.sleep(3)


def _zhijiang_onnx_to_pbtxt(onnx_file, pbtxt_file):
    """
    convert onnx file to pbtxt file
    _zhijiang_onnx_to_pbtxt onnx_file pbtxt_file
    """
    import onnx
    model = onnx.load(onnx_file)
    print(model, file=open(pbtxt_file, "w"))
    print(f"convert onnx file to pbtxt file {pbtxt_file}")
    os.system(f"code {pbtxt_file}")

def zhijiang_torch_model_view(model, inputs=None, depth=4, expand_nested=True, file_name="model.svg", other_ranks_continue=True):
    """
    the inputs can be list of tensor, or dict of tensor, or None(then will delay graph gen till model.forward called)
    """
    if inputs is None:
        cprint("inputs is None, so model graph generation is delayed till model.forward being called", "red")
        _wrap_model_to_save_graph(model, depth, expand_nested, file_name, other_ranks_continue)
        return

    if not __zhijiang_is_rank_x(0):
        if other_ranks_continue:
            return
        else:
            time.sleep(10000000)

    from torchview import draw_graph
    try:
        model_graph = draw_graph(
            model,
            # .../site-packages/torchview/torchview.py:258, will unpack inputs when inputs is dict, while sometimes we don't need unpack
            input_data=inputs,
            depth=depth,
            expand_nested=expand_nested,
            roll=True,
            hide_module_functions=False,
            device=next(model.parameters()).device,
            mode="train" if model.training else "eval",
        )
    except:
        model_graph = draw_graph(
            model,
            # .../site-packages/torchview/torchview.py:258, will unpack inputs when inputs is dict, while sometimes we don't need unpack
            input_data=[inputs],
            depth=depth,
            expand_nested=expand_nested,
            roll=True,
            hide_module_functions=False,
            device=next(model.parameters()).device,
            mode="train" if model.training else "eval",
        )

    graph_svg = model_graph.visual_graph.pipe(format="svg")
    with open(file_name, "wb") as f:
        f.write(graph_svg)
        os.fsync(f.fileno())
        cprint(f"saving model graph to {file_name}\n, you may need modify svg file to see full graph", "red")

def _wrap_model_to_save_graph(model, depth=4, expand_nested=True, file_name="model.svg", other_ranks_continue=True):
    def args_kwargs_to_new_args(func, *args, **kwargs):
        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
        return list(bound_args.args) + list(bound_args.kwargs.values())

    graph_created = False
    old_forward = model.forward
    def new_forward(model, *args, **kwargs):
        nonlocal graph_created
        if not graph_created:
            graph_created = True
            zhijiang_torch_model_view(model, args_kwargs_to_new_args(old_forward, *args, **kwargs),
                depth, expand_nested, file_name, other_ranks_continue)
        return old_forward(*args, **kwargs)
    model.forward = MethodType(new_forward, model)


def _zhijiang_analyze_onnx_model(onnx_file):
    from zhijiang.scripts._zhijiang_onnx_helper import Analyze_onnx_model

    os.system("reset")
    model = Analyze_onnx_model(onnx_file)
    model.print_info()
    cprint(
        '1. search items by "zhijiang,"\n2. return class object has attribute "constant_registery" to get constant value',
        "red",
    )
    return model


def zhijiang_torch_nccl_profiling():
    '''
        decorate torch nccl ops, so we can get its msg size and IO time
    '''
    from deepspeed.utils import get_msg_size_from_args, timer
    import torch

    def wrapper(nccl_op):
        def _wrapper(*args, **kwargs):
            msg_size = get_msg_size_from_args(nccl_op, *args, **kwargs)
            start_event = torch.cuda.Event(enable_timing=True)
            end_event = torch.cuda.Event(enable_timing=True)
            start_event.record()
            try:
                return nccl_op(*args, **kwargs)
            finally:
                end_event.record()
                torch.cuda.synchronize()
                estimate_ms = start_event.elapsed_time(end_event) / 5
                print(
                    f"zhijiang, {nccl_op.__name__} uses {estimate_ms} ms to send {msg_size} bytes, bandwidth is {msg_size/estimate_ms/1024/1024*1000} MB/s"
                )
            return _wrapper


zhijiang_PyTracer = PyTracer


# settup __all__, so only expose functions prefixed with "zhijiang_"
__all__ = sorted([name for name in dir() if name.startswith("zhijiang_")])
