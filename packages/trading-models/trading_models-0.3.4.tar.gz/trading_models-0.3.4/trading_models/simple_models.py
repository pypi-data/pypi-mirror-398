import math

import torch as tc
import torch.nn as nn


class MLP(nn.Module):
    def __init__(s, sizes, Act=nn.ReLU):
        super().__init__()
        layers = []
        for a, b in zip(sizes[:-2], sizes[1:-1]):
            layers += [nn.Linear(a, b), Act()]
        layers += [nn.Linear(sizes[-2], sizes[-1])]
        s.mlp = nn.Sequential(*layers)

    def forward(s, x: tc.Tensor):
        *B, F = x.shape
        return s.mlp(x.reshape(-1, F)).reshape(*B, -1)


class CNN(nn.Module):
    def __init__(s, sizes, Act=nn.ReLU, kernel=3, pad=1):
        super().__init__()
        layers = []
        for a, b in zip(sizes[:-2], sizes[1:-1]):
            layers += [nn.Conv1d(a, b, kernel, padding=pad)]
            layers += [Act()]
        layers += [nn.AdaptiveAvgPool1d(1)]
        s.cnn = nn.Sequential(*layers)
        s.fc = nn.Linear(sizes[-2], sizes[-1])

    def forward(s, x: tc.Tensor):
        x = s.cnn(x.permute(0, 2, 1))
        return s.fc(x.squeeze(-1))


class Transformer(nn.Module):
    def __init__(s, W, F, A, d_model, d_ff, n_head, n_layer):
        super().__init__()
        s.proj = nn.Linear(F, d_model)
        s.pe = s.make_pe(W, d_model)
        layer = nn.TransformerEncoderLayer(d_model, n_head, d_ff, batch_first=True)
        s.trans = nn.TransformerEncoder(layer, n_layer)
        s.fc = nn.Linear(d_model, A)

    def make_pe(s, W, d_model):
        pe = tc.zeros(W, d_model)
        pos = tc.arange(0, W).float().unsqueeze(1)
        div = tc.exp(tc.arange(0, d_model, 2).float() * (-math.log(1e4) / d_model))
        pe[:, 0::2] = tc.sin(pos * div)
        pe[:, 1::2] = tc.cos(pos * div)
        return pe.unsqueeze(0)

    def forward(s, x: tc.Tensor):
        x = s.proj(x) + s.pe.to(x.device)
        x = s.trans(x)
        return s.fc(x[:, -1, :])
