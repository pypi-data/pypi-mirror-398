# nijigen-backtrader

[![PyPI Version](https://img.shields.io/pypi/v/nijigen-backtrader.svg)](https://pypi.python.org/pypi/nijigen-backtrader/)
[![License](https://img.shields.io/pypi/l/nijigen-backtrader.svg)](https://github.com/nijigen-trading/nijigen-backtrader/blob/master/LICENSE)
[![Python versions](https://img.shields.io/pypi/pyversions/nijigen-backtrader.svg)](https://pypi.python.org/pypi/nijigen-backtrader/)

A feature-rich Python framework for backtesting and trading.

> **Note**: This is a maintained fork of the original [backtrader](https://github.com/mementum/backtrader) project.

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

Including a full featured chart. Give it a try! This is included in the samples as `sigsmacross/sigsmacross2.py`. Along it is `sigsmacross.py` which can be parametrized from the command line.

## Features

Live Trading and backtesting platform written in Python.

- **Live Data Feed and Trading with**
  - Interactive Brokers (needs `IbPy` and benefits greatly from an installed `pytz`)
  - *Visual Chart* (needs a fork of `comtypes` until a pull request is integrated in the release and benefits from `pytz`)
  - *Oanda* (needs `oandapy`) (REST API Only - v20 did not support streaming when implemented)

- **Data feeds** from csv/files, online sources or from *pandas* and *blaze*
- **Filters** for datas, like breaking a daily bar into chunks to simulate intraday or working with Renko bricks
- **Multiple data feeds and multiple strategies** supported
- **Multiple timeframes** at once
- **Integrated Resampling and Replaying**
- **Step by Step backtesting** or at once (except in the evaluation of the Strategy)
- **Integrated battery of indicators**
- **TA-Lib** indicator support (needs python *ta-lib* / check the docs)
- **Easy development** of custom indicators
- **Analyzers** (for example: TimeReturn, Sharpe Ratio, SQN) and `pyfolio` integration (**deprecated**)
- **Flexible definition** of commission schemes
- **Integrated broker simulation** with *Market*, *Close*, *Limit*, *Stop*, *StopLimit*, *StopTrail*, *StopTrailLimit* and *OCO* orders, bracket order, slippage, volume filling strategies and continuous cash adjustment for future-like instruments
- **Sizers** for automated staking
- **Cheat-on-Close** and **Cheat-on-Open** modes
- **Schedulers**
- **Trading Calendars**
- **Plotting** (requires matplotlib)

## Documentation

- [Blog](http://www.backtrader.com/blog)
- [Documentation](http://www.backtrader.com/docu)
- [Indicators Reference](http://www.backtrader.com/docu/indautoref.html) (122 built-in indicators)

## Python Support

- Python >= `3.9`
- It also works with `pypy` and `pypy3` (no plotting - `matplotlib` is not supported under *pypy*)

## Installation

`nijigen-backtrader` is self-contained with no external dependencies (except if you want to plot)

From *pypi*:

```bash
pip install nijigen-backtrader
```

With plotting support:

```bash
pip install nijigen-backtrader[plotting]
```

> **Note**: The minimum matplotlib version is `1.4.1`

### Optional Dependencies

An example for *IB* Data Feeds/Trading:

- `IbPy` doesn't seem to be in PyPi. Do either:

  ```bash
  pip install git+https://github.com/blampe/IbPy.git
  ```

  or (if `git` is not available in your system):

  ```bash
  pip install https://github.com/blampe/IbPy/archive/master.zip
  ```

For other functionalities like: `Visual Chart`, `Oanda`, `TA-Lib`, check the dependencies in the documentation.

From source:

- Place the *backtrader* directory found in the sources inside your project

## Version Numbering

`X.Y.Z`

- **X**: Major version number. Should stay stable unless something big is changed like an overhaul to use `numpy`
- **Y**: Minor version number. To be changed upon adding a complete new feature or (god forbids) an incompatible API change.
- **Z**: Revision version number. To be changed for documentation updates, small changes, small bug fixes

## License

GNU General Public License v3.0 or later (GPLv3+)
