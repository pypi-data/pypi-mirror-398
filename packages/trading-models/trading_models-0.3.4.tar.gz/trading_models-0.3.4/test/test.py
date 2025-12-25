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
