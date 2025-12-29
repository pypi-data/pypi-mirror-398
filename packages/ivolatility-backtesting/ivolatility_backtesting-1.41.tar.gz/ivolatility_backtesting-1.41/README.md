# IVolatility Backtesting
A universal backtesting framework for financial strategies using the IVolatility API.

## Installation
```bash
pip install ivolatility_backtesting
```

## Usage
```python
from ivolatility_backtesting import run_backtest, init_api

# Initialize API
init_api("your-api-key")

# Define your strategy
def my_strategy(config):
    # Strategy logic
    return BacktestResults(
        equity_curve=[100000, 110000],
        equity_dates=["2023-01-01", "2023-01-02"],
        trades=[{"pnl": 1000, "entry_date": "2023-01-01", "exit_date": "2023-01-02"}],
        initial_capital=100000,
        config=config
    )

# Run backtest
CONFIG = {
    "initial_capital": 100000,
    "start_date": "2023-01-01",
    "end_date": "2024-01-01",
    "strategy_name": "My Strategy"
}
analyzer = run_backtest(my_strategy, CONFIG)

# Access metrics
print(f"Sharpe Ratio: {analyzer.metrics['sharpe']:.2f}")
```

## Requirements
- Python >= 3.8
- pandas >= 1.5.0
- numpy >= 1.21.0
- matplotlib >= 3.5.0
- seaborn >= 0.11.0
- ivolatility >= 1.8.2
