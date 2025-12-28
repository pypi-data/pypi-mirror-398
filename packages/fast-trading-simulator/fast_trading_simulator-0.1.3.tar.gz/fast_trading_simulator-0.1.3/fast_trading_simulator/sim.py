from typing import Dict, List

import numba
import numpy as np
from trading_models.utils import plot_general

E_NO_EXIT = 0
E_TIMEOUT = 1
E_TAKE_PROFIT = 2
E_STOP_LOSS = 3
E_LIQ_PROTECT = 4
E_LIQ_TRIGGER = 5

EXIT_REASONS = [
    "no_exit",
    "timeout",
    "take_profit",
    "stop_loss",
    "liq_protect",
    "liq_trigger",
]


@numba.njit
def find_profit(
    price1: float,
    price2: float,
    dt: int,
    action: np.ndarray,
    tot_fee: float,
    liq_fee: float,
    liq_protect=-0.8,
    liq_trigger=-0.9,
    clip_pr: bool = False,
):
    pos, lev, timeout, take_profit, stop_loss = action
    pos, lev, p1, p2 = np.sign(pos), max(1, int(lev)), price1, price2
    pr = lev * (pos * (p2 - p1) / p1 - tot_fee)
    liq_pr = pr - lev * (liq_fee * p2 / p1)
    if clip_pr:
        pr = min(pr, take_profit)
    if liq_pr < liq_trigger:
        return -1.0, E_LIQ_TRIGGER
    if liq_pr < liq_protect:
        return pr, E_LIQ_PROTECT
    if pr < stop_loss:
        return pr, E_STOP_LOSS
    if pr > take_profit:
        return pr, E_TAKE_PROFIT
    if dt >= timeout:
        return pr, E_TIMEOUT
    return pr, E_NO_EXIT


@numba.njit
def find_price2(
    price1: float,
    action: np.ndarray,
    tot_fee: float,
):
    pos, lev, timeout, take_profit, stop_loss = action
    pos, lev, p1 = np.sign(pos), max(1, int(lev)), price1
    # pr = lev * (pos * (p2 - p1) / p1 - tot_fee)
    return (take_profit / lev + tot_fee) * p1 / pos + p1


@numba.njit
def simulate(
    market: np.ndarray,
    action: np.ndarray,
    tot_fee: float,
    liq_fee: np.ndarray,
    liq_protect=-0.8,
    liq_trigger=-0.9,
    clip_pr: bool = False,
    min_pos=0.1,
    use_ratio=0.5,
    alloc_ratio=0.01,
    init_cash=10e3,
    min_cash=10,
    price_idx=1,
):
    max_open = int(use_ratio / alloc_ratio)
    SYMBOL, TIME, _ = market.shape

    worth = cash_left = init_cash
    open_trades: Dict[int, np.ndarray] = {}
    done_trades: List[np.ndarray] = []

    for t in range(TIME):

        for id, x in list(open_trades.items()):
            s1, t1, cash = int(x[0]), int(x[1]), x[2]
            dt = t - t1
            pr, exit = find_profit(
                price1=market[s1, t1, price_idx],
                price2=market[s1, t, price_idx],
                dt=dt,
                action=action[s1, t1],
                tot_fee=tot_fee,
                liq_fee=liq_fee[s1],
                liq_protect=liq_protect,
                liq_trigger=liq_trigger,
                clip_pr=clip_pr,
            )
            if exit:
                worth += cash * pr
                cash_left += cash * (1 + pr)
                x[-4:] = float(dt), pr, float(exit), worth
                del open_trades[id]
                done_trades.append(x)

        for s in range(SYMBOL):
            pos = action[s, t, 0]
            if abs(pos) > min_pos and len(open_trades) < max_open:
                cash = min(cash_left, worth * alloc_ratio * abs(pos))
                id = int(np.sign(pos) * (s + 1))
                if cash > min_cash and id not in open_trades:
                    cash_left -= cash
                    open_trades[id] = np.array([s, t, cash, pos, 0.0, 0.0, 0.0, 0.0])

    return done_trades


def map_trades(trades, to_map=[], plot=True):
    trades = np.array(trades).T
    sym, time = trades[:2].astype(int)
    keys = ["cash", "position", "duration", "profit", "exit", "worth"]
    types = ["_hist", "_hist", "_hist", "_hist", "_hist", ""]
    res: Dict[str, np.ndarray] = {k: v for k, v in zip(keys, trades[2:])}
    res["exit"] = np.array(EXIT_REASONS)[res["exit"].astype(int)]
    to_map = [v[sym, time] for v in to_map]
    if plot:
        plots = {f"{k}{type}": res[k] for k, type in zip(keys, types)}
        plots[f"log10(worth) ({len(sym)} trades)"] = np.log10(res["worth"])
        plot_general(plots, "simulate")
    return (res, to_map) if to_map else res


@numba.njit
def sim_all_points(
    market: np.ndarray,
    action: np.ndarray,
    tot_fee: float,
    liq_fee: np.ndarray,
    liq_protect=-0.8,
    liq_trigger=-0.9,
    clip_pr: bool = False,
    price_idx=1,
):
    SYMBOL, TIME, _ = market.shape
    all_pr = np.zeros((SYMBOL, TIME, 1))
    for s in numba.prange(SYMBOL):
        for t in numba.prange(TIME):
            act = action[s, t]
            if act[0] == 0:
                continue
            for t2 in range(t + 1, TIME):
                pr, exit = find_profit(
                    price1=market[s, t, price_idx],
                    price2=market[s, t2, price_idx],
                    dt=t2 - t,
                    action=act,
                    tot_fee=tot_fee,
                    liq_fee=liq_fee[s],
                    liq_protect=liq_protect,
                    liq_trigger=liq_trigger,
                    clip_pr=clip_pr,
                )
                if exit:
                    all_pr[s, t, 0] = pr
                    break
    return all_pr
