
## Intro

- Neural Network models for trading: MLP, CNN, Transformer
- Below shows the training process of my private model

![](https://raw.githubusercontent.com/SerenaTradingResearch/trading-models/main/test/train_model.gif)

## Usage

```bash
pip install trading-models
```

```py
import torch as tc
from torch.utils.data import DataLoader

from trading_models.simple_models import CNN, MLP, Transformer
from trading_models.utils import WindowDataset, model_size

"""
trading models

input: x.shape = (T, F)
output: a.shape = (T-W+1, A)

T: time
F: features
W: window length
A: actions

at each time step t in range(W-1, T),
the model looks at data in the window
x[t+1-W : t+1, :]
to make A actions
"""

T, F, W, A = 100, 2, 50, 1
device = tc.device("cuda" if tc.cuda.is_available() else "cpu")
x = tc.randn(T, F).to(device)

dataset = WindowDataset(x, W)
dataloader = DataLoader(dataset, batch_size=32, shuffle=False)

net1 = MLP([W * F, 64, 64, A]).to(device)
net2 = CNN([F, 64, 64, A]).to(device)
net3 = Transformer(W, F, A, d_model=64, d_ff=64, n_head=2, n_layer=2).to(device)

for net in [net1, net2, net3]:
    outputs = []
    for batch in dataloader:
        outputs.append(net(batch.to(device)).detach())
    output = tc.cat(outputs, dim=0)
    print(net, output.shape, model_size(net), "\n")

```

- Output

```bash
MLP(
  (mlp): Sequential(
    (0): Linear(in_features=100, out_features=64, bias=True)
    (1): SiLU()
    (2): Linear(in_features=64, out_features=64, bias=True)
    (3): SiLU()
    (4): Linear(in_features=64, out_features=1, bias=True)
  )
) torch.Size([51, 1]) trainable: 10689/10689 

CNN(
  (cnn): Sequential(
    (0): Conv1d(2, 64, kernel_size=(3,), stride=(1,), padding=(1,))
    (1): SiLU()
    (2): Conv1d(64, 64, kernel_size=(3,), stride=(1,), padding=(1,))
    (3): SiLU()
    (4): AdaptiveAvgPool1d(output_size=1)
  )
  (fc): Linear(in_features=64, out_features=1, bias=True)
) torch.Size([51, 1]) trainable: 12865/12865 

Transformer(
  (proj): Linear(in_features=2, out_features=64, bias=True)
  (trans): TransformerEncoder(
    (layers): ModuleList(
      (0-1): 2 x TransformerEncoderLayer(
        (self_attn): MultiheadAttention(
          (out_proj): NonDynamicallyQuantizableLinear(in_features=64, out_features=64, bias=True)
        )
        (linear1): Linear(in_features=64, out_features=64, bias=True)
        (dropout): Dropout(p=0.1, inplace=False)
        (linear2): Linear(in_features=64, out_features=64, bias=True)
        (norm1): LayerNorm((64,), eps=1e-05, elementwise_affine=True)
        (norm2): LayerNorm((64,), eps=1e-05, elementwise_affine=True)
        (dropout1): Dropout(p=0.1, inplace=False)
        (dropout2): Dropout(p=0.1, inplace=False)
      )
    )
  )
  (fc): Linear(in_features=64, out_features=1, bias=True)
) torch.Size([51, 1]) trainable: 50689/50689 
```
