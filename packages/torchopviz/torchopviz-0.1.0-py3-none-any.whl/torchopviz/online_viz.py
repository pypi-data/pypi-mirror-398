import time
import os

import torch
import torch.profiler as profiler

from .launch_server import launch_visualizer
from .memory_profile import memory_profile_monkey_patch
from .comm import complex_graph_file
from .utils import load_data
from .log import logger


def generate_data(model, data):
    if not torch.cuda.is_available():
        logger.error(f"CUDA is not available, can not use online mode.")
        return
    device_str = "cuda:0"
    device = torch.device(device_str)
    logger.info(f"Using device: {device}")

    model = model.to(device)

    def trace_handler(prof: torch.profiler.profile):
        prof._memory_profile()

    # Profiler 配置
    prof = profiler.profile(
        activities=[
            profiler.ProfilerActivity.CPU,
            profiler.ProfilerActivity.CUDA
        ],
        on_trace_ready=trace_handler,
        record_shapes=True,
        with_stack=True,
        profile_memory=True,
    )

    # warmup
    outputs = model(data.to(device))
    torch.cuda.synchronize()

    # 推理并采集数据
    prof.start()
    outputs = model(data.to(device))
    torch.cuda.synchronize()
    prof.stop()


def online_viz(model, data, save_dir: str):
    save_dir = os.path.abspath(save_dir)
    memory_profile_monkey_patch(save_dir)
    generate_data(model, data)

    file = os.path.join(save_dir, complex_graph_file)
    json_data = load_data(file)

    launch_visualizer(json_data)
    logger.info(f"visualizer start, stop by Ctrl+C.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("stopped")


if __name__ == '__main__':
    # from torchvision.models import resnet18
    # model = resnet18(pretrained=False)
    # data = torch.rand(1, 3, 224, 224)

    from torch import nn
    model = nn.Sequential()
    model.add_module('W0', nn.Linear(8, 16))
    model.add_module('tanh', nn.Tanh())
    model.add_module('W1', nn.Linear(16, 1))
    data = torch.randn(1,8)

    online_viz(model, data, save_dir="./sample_data")