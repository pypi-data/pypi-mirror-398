from typing import List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sb
import torch as tc
import torch.nn as nn
import torch.nn.functional as F
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_squared_error as mse
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR
from statsmodels.nonparametric.smoothers_lowess import lowess

from .utils import mlp, plot_general, tensor, to_np


def sanity_check(
    X: np.ndarray, Y: np.ndarray, models=None, shuffle=True, use_lowess=False
):
    F = X.shape[-1]
    # 1. basic plots
    plots = {}
    for i in range(F):
        x = X[:, i]
        plots[f"x{i}_hist"] = x
        plots[f"x{i}_vs_y"] = {"x": x, "y": Y}
        if use_lowess:
            r = lowess(Y, x).T
            plots[f"x{i}_vs_y_lowess"] = {"x": r[0], "y": r[1]}
    C = 3 if use_lowess else 2
    plots["y_hist"] = Y
    plot_general(plots, "ml_1_basic", C=C)

    # 2. correlation heatmap
    df = pd.DataFrame(X, columns=[f"x{i}" for i in range(F)])
    df["Y"] = Y
    plt.figure(figsize=(10, 10))
    sb.heatmap(df.corr(), annot=True)
    plt.savefig("ml_2_corr_heatmap")
    plt.close()

    # 3. PCA
    pca = PCA(n_components=2)
    x = pca.fit_transform(X).T
    plt.scatter(x[0], x[1], c=Y, s=2)
    plt.colorbar(label="Y")
    plt.xlabel("pca_x0")
    plt.ylabel("pca_x1")
    plt.title("PCA colored by Y")
    plt.savefig("ml_3_pca")
    plt.close()

    X1, X2, Y1, Y2 = train_test_split(X, Y, shuffle=shuffle)
    scaler = StandardScaler()
    X1 = scaler.fit_transform(X1)
    X2 = scaler.transform(X2)
    if models is None:
        models: List[SVR] = [
            LinearRegression(),
            Ridge(alpha=1.0),
            RandomForestRegressor(max_depth=6),
            SVR(epsilon=0.2),
            MLPRegressor(hidden_layer_sizes=[64, 64]),
            MyMLPRegressor(),
            KNeighborsRegressor(n_neighbors=10, weights="distance"),
        ]
    for m in models:
        m.fit(X1, Y1, X2, Y2) if isinstance(m, MyMLPRegressor) else m.fit(X1, Y1)
        name = m.__class__.__name__.replace("Regressor", "")
        parts = [
            f"{name:20} R^2: train {m.score(X1, Y1):.3f}, test {m.score(X2, Y2):.3f}",
            f"MSE: train {mse(Y1, m.predict(X1)):.1e}, test {mse(Y2, m.predict(X2)):.1e}",
        ]
        print("   ".join(parts))


class MyMLPRegressor:
    def __init__(s, hid_sizes=[64, 64], Act=nn.Tanh, lr=1e-3):
        s.hid_sizes, s.Act, s.lr = hid_sizes, Act, lr

    def fit(s, X: np.ndarray, Y: np.ndarray, X2: np.ndarray, Y2: np.ndarray):
        min_steps = 100
        s.net = mlp([X.shape[-1], *s.hid_sizes, 1], s.Act)
        opt = tc.optim.Adam(s.net.parameters(), lr=s.lr)
        X, Y = tensor([X, Y.reshape(-1, 1)])
        X2, Y2 = tensor([X2, Y2.reshape(-1, 1)])
        losses, test_losses = [], []
        while True:
            with tc.no_grad():
                test_loss = F.mse_loss(s.net(X2), Y2).item()
                test_losses.append(test_loss)
            opt.zero_grad()
            loss = F.mse_loss(s.net(X), Y)
            loss.backward()
            opt.step()

            loss = loss.item()
            losses.append(loss)
            # print(f"MyMLP mse_loss: train {loss:.1e}, test {test_loss:.1e}")
            avg = np.mean(losses[-min_steps:])
            if len(losses) > min_steps and loss > 0.95 * avg:
                break
        plot_general({"loss": losses, "test_loss": test_losses}, "MyMLP_loss")

    @tc.no_grad()
    def predict(s, X):
        return to_np(s.net(tensor(X))).squeeze()

    def score(s, X: np.ndarray, Y: np.ndarray):
        return r2_score(Y, s.predict(X))


def checkerboard_data(N=int(3e4), C=10, plot=True, noise=0.5):
    X = np.random.uniform(-1, 1, (N, 2))
    F = np.floor
    mask = (F(C * X[:, 0]) + F(C * X[:, 1])) % 2 == 0
    Y = np.where(mask, 1, -1) + np.random.normal(0, noise, N)
    if plot:
        plt.scatter(X[:, 0], X[:, 1], c=Y, s=3)
        plt.show()
    return X, Y
