#!/usr/bin/env python

import subprocess
import time
from multiprocessing import Process
import numpy as np


def get_gpus_util():
    def percentage_to_float(data):
        return float(data.replace("%", "e-2"))

    cmd = "nvidia-smi --query-gpu=utilization.gpu  --format=csv"
    output = subprocess.run(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ).stdout.decode("utf-8")
    gpus_util = output.replace(" ", "").split("\n")[1:-1]
    return [percentage_to_float(gpu_util) for gpu_util in gpus_util]


def has_gpu_util():
    # gpu_util > 0.1 means gpu is utilized
    gpus_util = get_gpus_util()
    print(f"time is {time.ctime()}, gpu utils is {gpus_util}")
    return np.any(gpus_util > np.array(0.1))


def make_gpu_util(timeout=60):
    def dummy_all_gpus():
        import torch

        def dummy_matmul_per_device(device):
            a = torch.randn(
                (torch.randint(256, 1024, (1,)).item(), 1024 * 1024),
                dtype=torch.float32,
                device=device,
            )
            b = torch.randn(
                (1024 * 1024, torch.randint(256, 1024, (1,)).item() * 2),
                dtype=torch.float32,
                device=device,
            )
            c = torch.matmul(torch.sin(a), torch.cos(b))
            d = torch.nn.Dropout(0.5)(c)
            return d

        now = time.time()
        while time.time() - now < timeout:
            for i in range(torch.cuda.device_count()):
                try:
                    dummy_matmul_per_device(f"cuda:{i}")
                except torch.cuda.OutOfMemoryError:
                    pass

    print(f"run dummy gpu util for {timeout}sec")
    p = Process(target=dummy_all_gpus)
    p.start()
    p.join()
    print(f"{time.ctime()}, dummy run done")


def make_gpu_no_idle():
    make_gpu_util(60) # make sure script is runnable
    # check gpu util every 300s, if gpu is idle for 30 minutes, run dummy.py for 60s
    gpu_idle_cnt = 0
    while 1:
        time.sleep(120)
        if has_gpu_util():
            gpu_idle_cnt = 0
        else:
            gpu_idle_cnt += 1
        if gpu_idle_cnt > 15:
            print(
                f"--------------at {time.ctime()}, detect gpu is idle for 30 minutes, run dummy.py for 300s(3600s at china night), ----------"
            )
            make_gpu_util(3600)
            gpu_idle_cnt = 0


make_gpu_no_idle()
