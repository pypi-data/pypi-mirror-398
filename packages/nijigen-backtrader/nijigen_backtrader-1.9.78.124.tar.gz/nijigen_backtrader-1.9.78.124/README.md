# nijigen-backtrader

[![PyPI Version](https://img.shields.io/pypi/v/nijigen-backtrader.svg)](https://pypi.python.org/pypi/nijigen-backtrader/)
[![License](https://img.shields.io/pypi/l/nijigen-backtrader.svg)](https://github.com/nijigen-trading/nijigen-backtrader/blob/master/LICENSE)
[![Python versions](https://img.shields.io/pypi/pyversions/nijigen-backtrader.svg)](https://pypi.python.org/pypi/nijigen-backtrader/)

A fork of [backtrader](https://github.com/mementum/backtrader) - Live Trading and backtesting platform written in Python.

## Quick Start

Here's a snippet of a Simple Moving Average CrossOver. It can be done in several different ways. Use the docs (and examples) Luke!

```python
from datetime import datetime
import backtrader as bt

class SmaCross(bt.SignalStrategy):
    def __init__(self):
        sma1, sma2 = bt.ind.SMA(period=10), bt.ind.SMA(period=30)
        crossover = bt.ind.CrossOver(sma1, sma2)
        self.signal_add(bt.SIGNAL_LONG, crossover)

cerebro = bt.Cerebro()
cerebro.addstrategy(SmaCross)

data0 = bt.feeds.YahooFinanceData(dataname='MSFT', fromdate=datetime(2011, 1, 1),
                                  todate=datetime(2012, 12, 31))
cerebro.adddata(data0)

cerebro.run()
cerebro.plot()
```

## Features

- **Live Data Feed and Trading** with:
  - Interactive Brokers (needs `IbPy` and benefits greatly from an installed `pytz`)
  - Visual Chart (needs a fork of `comtypes`)
  - Oanda (needs `oandapy`) (REST API Only)

- **Data feeds** from csv/files, online sources or from pandas and blaze

- **Filters** for datas, like breaking a daily bar into chunks to simulate intraday or working with Renko bricks

- **Multiple data feeds and multiple strategies** supported

- **Multiple timeframes** at once

- **Integrated Resampling and Replaying**

- **Step by Step backtesting** or at once

- **Integrated battery of indicators**

- **TA-Lib indicator support** (needs python ta-lib)

- **Easy development of custom indicators**

- **Analyzers** (e.g., TimeReturn, Sharpe Ratio, SQN) and `pyfolio` integration

- **Flexible definition of commission schemes**

- **Integrated broker simulation** with Market, Close, Limit, Stop, StopLimit, StopTrail, StopTrailLimit and OCO orders, bracket order, slippage, volume filling strategies

- **Sizers** for automated staking

- **Cheat-on-Close and Cheat-on-Open** modes

- **Schedulers and Trading Calendars**

- **Plotting** (requires matplotlib)

## Documentation

- [Blog](http://www.backtrader.com/blog)
- [Documentation](http://www.backtrader.com/docu)
- [Indicators Reference](http://www.backtrader.com/docu/indautoref.html) (122 built-in indicators)

## Python Support

- Python >= 3.9
- Also works with `pypy` and `pypy3` (no plotting - matplotlib is not supported under pypy)

## Installation

`backtrader` is self-contained with no external dependencies (except if you want to plot).

From PyPI:

```bash
pip install nijigen-backtrader

# With plotting support
pip install nijigen-backtrader[plotting]
```

> **Note:** The minimum matplotlib version is 1.4.1

### Optional Dependencies

For IB Data Feeds/Trading:

```bash
pip install git+https://github.com/blampe/IbPy.git
```

For other functionalities like Visual Chart, Oanda, TA-Lib, check the dependencies in the documentation.

## Version Numbering

`X.Y.Z.I`

- **X**: Major version number
- **Y**: Minor version number (new features or API changes)
- **Z**: Revision version number (docs, small changes, bug fixes)
- **I**: Number of Indicators built into the platform

## License

GPL-3.0-or-later
