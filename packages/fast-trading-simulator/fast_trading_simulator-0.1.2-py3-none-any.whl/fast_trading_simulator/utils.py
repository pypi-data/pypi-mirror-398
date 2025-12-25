from typing import Callable, Dict

import matplotlib.pyplot as plt
import numpy as np
import talib as ta
from crypto_data_downloader.utils import load_pkl
from pymoo.algorithms.soo.nonconvex.ga import GA
from pymoo.core.problem import ElementwiseProblem
from pymoo.optimize import minimize
from trading_models.utils import D2_TYPE, D_TYPE


class ActMap:
    @staticmethod
    def from_tanh(tanh, low, high):
        return (tanh + 1) / 2 * (high - low) + low

    @staticmethod
    def to_tanh(x, low, high):
        return (x - low) / (high - low) * 2 - 1


def volatility(price: np.ndarray):
    dp = np.diff(price) / price[:-1]
    return np.sqrt(np.mean(dp**2))


def make_market_n_obs(
    path,
    vol_range=[1e-3, 2e-2],
    ref_sym="BTCUSDT",
    price_idx=1,
    # obs:
    MA=ta.KAMA,
    periods=[10, 100],
    add_ref_obs=True,
):
    data: D_TYPE = load_pkl(path, gz=True)
    T = len(data[ref_sym])
    temp: D2_TYPE = {}
    skip = max(periods)
    for sym, v in data.items():
        if len(v) != T:
            continue
        p = v[:, price_idx]
        obs = np.array([p / MA(p, P) - 1 for P in periods]).T
        obs = obs.clip(-1, 1)
        vol = volatility(p)
        ok = vol > vol_range[0] and vol < vol_range[1]
        temp[sym] = {"raw": v[skip:], "obs": obs[skip:], "ok": ok, "vol": vol}
    if add_ref_obs:
        ref_obs = temp[ref_sym]["obs"]
        for sym, d in temp.items():
            d["obs"] = np.concat([d["obs"], ref_obs], axis=1)
    get = lambda key: np.array([d[key] for d in temp.values() if d["ok"]])
    plt.hist(get("vol"), bins=100)
    plt.savefig("volatility_hist")
    return get("raw"), get("obs")


# ======================================


def round_dx(x, dx):
    return round(round(x / dx) * dx, 10)


def pymoo_minimize(func: Callable, conf: Dict, algo=GA()):
    xl = [v[0] for v in conf.values()]
    xu = [v[1] for v in conf.values()]
    dx = [v[2] for v in conf.values()]
    best = np.inf

    class Prob(ElementwiseProblem):
        def __init__(s):
            super().__init__(n_var=len(xl), n_obj=1, xl=xl, xu=xu)

        def _evaluate(s, X: np.ndarray, out, *args, **kwargs):
            X = [round_dx(xi, dxi) for xi, dxi in zip(X, dx)]
            P = dict(zip(conf.keys(), X))
            loss = func(P)
            nonlocal best
            if loss < best:
                best = loss
                print(f"best: {best} {P}")
            out["F"] = loss

    minimize(Prob(), algo, seed=42)
