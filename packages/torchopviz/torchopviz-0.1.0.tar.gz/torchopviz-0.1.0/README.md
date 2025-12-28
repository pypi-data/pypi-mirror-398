TorchOpViz
=======

A small package to create visualizations of PyTorch operation execution.

## Install

Install PyTorch with CUDA support like:

```
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu126
```

Note torch>=2.1.0.

Install torchopviz:

```
pip3 install torchopviz
```

## Usage

Offline mode:

```
from torchopviz import offline_viz
offline_viz(file="./complex_graph.json")
```

Online mode:

```
from torchopviz import online_viz
from torch import nn
model = nn.Sequential()
model.add_module('W0', nn.Linear(8, 16))
model.add_module('tanh', nn.Tanh())
model.add_module('W1', nn.Linear(16, 1))
data = torch.randn(1,8)
online_viz(model, data, save_dir="./sample_data")
```

![example](example.png)

## TODO

Display distributed computation

Combine memory usage info

Optmization