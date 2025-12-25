import time
from typing import Any, Callable, Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import torch as tc
import torch.nn as nn
from PIL import Image
from torch.utils.data import Dataset

DEVICE = tc.device("cuda" if tc.cuda.is_available() else "cpu")


def std_clip(x: np.ndarray, n=3):
    mean, std = x.mean(), x.std() * n
    return x.clip(mean - std, mean + std)


def mlp(sizes, Act=nn.Tanh, out=[]):
    layers = []
    for a, b in zip(sizes[:-1], sizes[1:]):
        layers += [nn.Linear(a, b), Act()]
    return nn.Sequential(*layers[:-1], *out)


def model_size(m: nn.Module):
    a = sum(p.numel() for p in m.parameters())
    b = sum(p.numel() for p in m.parameters() if p.requires_grad)
    return f"trainable: {b}/{a}"


class WindowDataset(Dataset):
    def __init__(s, x, W):
        s.x, s.W = x, W

    def __len__(s):
        return len(s.x) - s.W + 1

    def __getitem__(s, idx):
        return s.x[idx : idx + s.W]


# ==============================

D_TYPE = Dict[str, np.ndarray]
D2_TYPE = Dict[str, D_TYPE]
T2_TYPE = Dict[str, Dict[str, tc.Tensor]]
LOSS_FN_TYPE = Callable[[T2_TYPE, str], Tuple[tc.Tensor, Dict, Dict]]


def train_model(
    net: nn.Module,
    train_data: Any,
    test_data: Any,
    loss_fn: LOSS_FN_TYPE,
    id="train_model",
    lr=1e-3,
    n_epoch=10000,
    f_test=10,
    f_plot=20,
):
    net.to(DEVICE)
    opt = tc.optim.AdamW(net.parameters(), lr=lr)
    records, gif = [], GIFMaker()
    best_score = -np.inf

    for e in range(int(n_epoch)):
        loss_test, info_test = np.nan, {}
        if e % f_test == 0:
            net.eval()
            with tc.no_grad():
                loss_test, info_test, plots_test = loss_fn(test_data, "test")
            score = info_test["SCORE_test"]
            if score > best_score:
                best_score = score
                tc.save(net.state_dict(), f"{id}.tc")
            net.train()
        opt.zero_grad()
        loss_train, info_train, plots_train = loss_fn(train_data, "train")
        loss_train.backward()
        opt.step()
        rec = {"A_loss_train": loss_train, "A_loss_test": loss_test}
        records.append({**rec, **info_train, **info_test})
        if e % f_plot == 0:
            plots = transpose_records(records)
            plots = {**plots, **plots_train, **plots_test}
            plot_general(dict(sorted(plots.items())), f"{id}.png")
            gif.add(f"{id}.png")
    gif.save(id)


def mod_keys(dic: Dict, post):
    return {f"{k}_{post}": v for k, v in dic.items()}


def slice_xy(xy: D2_TYPE, r1, r2, num=None):
    xy2 = {}
    for sym, d in xy.items():
        x, y = d["x"], d["y"]
        n = len(x)
        i1, i2 = int(r1 * n), int(r2 * n)
        step = max(1, (i2 - i1) // num) if num else 1
        x, y = x[i1:i2:step], y[i1:i2:step]
        xy2[sym] = dict(x=x, y=y)
    print(f"slice_xy: n: {n}, i1: {i1}, i2: {i2}, step: {step}, n2: {len(x)}")
    return xy2


def concat_xy(xy: D2_TYPE):
    X = np.concat([d["x"] for d in xy.values()], axis=0)
    Y = np.concat([d["y"] for d in xy.values()], axis=0)
    return {"ALL_SYMBOLS": dict(x=X, y=Y)}


def timer(func):
    def func2(*args, **kwargs):
        t1 = time.time()
        res = func(*args, **kwargs)
        print(f"{func.__name__} took {time.time() - t1:.3f} seconds")
        return res

    return func2


def tensor(x):
    if isinstance(x, np.ndarray):
        return tc.from_numpy(x.copy()).float().to(DEVICE)
    if isinstance(x, dict):
        return {k: tensor(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [tensor(v) for v in x]
    return x


def to_np(x):
    if isinstance(x, tc.Tensor):
        return x.detach().cpu().numpy()
    if isinstance(x, dict):
        return {k: to_np(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [to_np(v) for v in x]
    return x


def shape(x):
    if isinstance(x, (np.ndarray, tc.Tensor)):
        return x.shape
    if isinstance(x, dict):
        return {k: shape(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [shape(v) for v in x]
    return x


def slice_data(x, r1, r2, axis):
    if isinstance(x, (np.ndarray, tc.Tensor)):
        N = x.shape[axis]
        slc = [slice(None)] * x.ndim
        slc[axis] = slice(int(N * r1), int(N * r2))
        return x[tuple(slc)]
    if isinstance(x, dict):
        return {k: slice_data(v, r1, r2, axis) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [slice_data(v, r1, r2, axis) for v in x]
    return x


def l2_norm(x: nn.Module):
    return sum(p.norm(2) for p in x.parameters())


def add_l2_loss(loss: tc.Tensor, net: nn.Module, ratio):
    l2 = l2_norm(net)
    loss += l2 / l2.item() * loss.abs().item() * ratio
    return loss, l2


# ==================================


def plot_general(plots: D_TYPE, id, C=2, bins=100):
    R = int(np.ceil(len(plots) / C))
    plt.figure(figsize=(4 * C, 3 * R))
    i = 0
    for k, v in plots.items():
        v = to_np(v)
        i += 1
        plt.subplot(R, C, i)
        title = k
        if "_hist" in k:
            v = v.flatten()
            if len(v):
                if np.issubdtype(v.dtype, np.number):
                    mean, std = v.mean(), v.std() * 3
                    try:
                        plt.hist(v, bins=bins, range=[mean - std, mean + std])
                    except Exception:
                        pass
                    title = f"{k}\n N={len(v):.1e}, {v.min():.5g} ~ {v.max():.5g}"
                else:
                    plt.hist(v)
                    title = f"{k}\n N={len(v):.1e}"
        elif isinstance(v, dict):
            plt.scatter(v["x"], v["y"], s=3)
            corr = np.corrcoef(v["x"], v["y"])[0, 1]
            title = f"{k}\n corr={corr:.3g}"
        else:
            x = np.arange(len(v))
            if np.any(np.isnan(v)):
                plt.scatter(x, v, s=3)
            else:
                plt.plot(x, v)
        plt.title(title)
    plt.tight_layout()
    plt.savefig(id)
    plt.close()


def transpose_records(records: List[Dict]):
    return {k: np.array([to_np(r.get(k, np.nan)) for r in records]) for k in records[0]}


def plot_records(records: List[Dict], id, C=1):
    dic = transpose_records(records)
    R = int(np.ceil(len(dic) / C))
    plt.figure(figsize=(4 * C, 3 * R))
    i = 0
    for k, v in dic.items():
        i += 1
        plt.subplot(R, C, i)
        plt.title(k)
        x = np.arange(len(v))
        if np.any(np.isnan(v)):
            plt.scatter(x, v, s=3)
        else:
            plt.plot(x, v)
    plt.tight_layout()
    plt.savefig(id)
    plt.close()


def plot_xy(xy: D2_TYPE, id="xy"):
    R, C = 5, 2
    plt.figure(figsize=(4 * C, 3 * R))
    i = 0
    for sym, d in xy.items():
        i += 1
        x, y = d["x"], d["y"]
        plt.subplot(R, C, i)
        plt.title(sym)
        for k in range(x.shape[1]):
            plt.plot(x[:, k], label=f"x[:, {k}]")
        plt.legend()
        i += 1
        plt.subplot(R, C, i)
        plt.plot(y)
        if i == R * C:
            break
    plt.tight_layout()
    plt.savefig(id)
    plt.close()


# =====================


class GIFMaker:
    def __init__(s):
        s.frames: List[Image.Image] = []

    def add(s, path):
        s.frames.append(Image.open(path).copy())

    def save(s, id, fps=10):
        s.frames[0].save(
            f"{id}.gif",
            format="GIF",
            append_images=s.frames[1:],
            save_all=True,
            duration=int(1000 / fps),
            loop=0,
            optimize=True,
        )
