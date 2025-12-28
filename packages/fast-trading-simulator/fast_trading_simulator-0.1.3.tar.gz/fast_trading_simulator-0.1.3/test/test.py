import numpy as np
import talib as ta
from crypto_data_downloader.utils import load_pkl
from trading_models.utils import D_TYPE

from fast_trading_simulator.sim import map_trades, simulate

path = "./futures_data_2025-08-01_2025-11-20.pkl"
data: D_TYPE = load_pkl(path, gz=True)

ref_sym = "BTCUSDT"
price_idx = 1
delta = 0.05

T = len(data[ref_sym])
data = {k: v for k, v in data.items() if len(v) == T}
all_act = []
for sym, v in data.items():
    p = v[:, price_idx]
    obs = p / ta.KAMA(p, 20) - 1
    pos = np.where(obs < -delta, 1, 0)
    pos = np.where(obs > delta, -1, pos)
    lev = np.full(T, 20)
    timeout = np.full(T, 10)
    take_profit = np.full(T, 0.01)
    stop_loss = np.full(T, -0.9)
    act = np.array([pos, lev, timeout, take_profit, stop_loss]).T
    all_act.append(act)
market = np.array(list(data.values()))
action = np.array(all_act)
tot_fee = 1e-3
liq_fee = np.full(len(data), 0.02)

trades = simulate(market, action, tot_fee, liq_fee, use_ratio=0.2, alloc_ratio=0.01)
map_trades(trades, plot=True)
