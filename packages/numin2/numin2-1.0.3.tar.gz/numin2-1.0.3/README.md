# numin2 Package

**numin2** is a Python package designed for algorithmic trading and backtesting providing an API called **Numin2API**.

**numin (v1)** is out of service as of Dec 2025

**numin2** is under development; features available are documented below

## Features

- **Data Retrieval:** Download training, round, and validation data.
- **Prediction Submission:**  TBD
- **Real-Time Round Management:** TBD
- **Backtesting:** Backtesting cross-sectional predictions vs targets for Nifty50
- **File Management:** TBD
- **Returns Summary:** TBD

## Supported Methods

- **Data Download:**
    - `get_data_for_month(self,year,month,batch_size=4,window_size=100,target_type='rank'):`
    -   Returns a torch dataloader for the given year and month of Nifty 50 or n returns
    -   Dimension of each day is 100,n. Returns tensor of shape batch_size,window_size,n for features. Default n=50. (Later n will be a parameter).
    -   Targets are next day returns / ranked returns of shape batch_size,n
    
    - `download_data(outfile,type='daily',features='returns')`
    -   Download data for a given type and features
    -   type can be 'daily','intraday'
    -   features can be 'returns' (close returns),'open_close' (open-close returns), or 'ohlcv'
    -   outfile is the name of the parquet file to save the data   
    - `get_range_dataloader(data_path: str, start_year: int, start_month: int,
                         end_year: int, end_month: int,
                         batch_size: int = 32, window_size: int = 100,
                         target_type: str = 'raw', top_k: int = 10)`
    -   Returns a torch dataloader for the given range of years and months of Nifty 50 or n returns
    -   Dimension of each day is 100,n. Returns tensor of shape batch_size,window_size,n for features. Default n=50. (Later n will be a parameter).
    -   Targets are next day returns / ranked returns of shape batch_size,n 
   
    - `get_dataloader(data_path: str, batch_size: int = 32, window_size: int = 100,
                         target_type: str = 'raw', top_k: int = 10)`
    -   Returns a torch dataloader for the given range of years and months of Nifty 50 or n returns
    -   Dimension of each day is 100,n. Returns tensor of shape batch_size,window_size,n for features. Default n=50. (Later n will be a parameter).
    -   Targets are next day returns / ranked returns of shape batch_size,n 

- **Backytesting**
    - `backtest_positions(positions,targets)`
    - Taks a batch of positions for 50 stocks
    - Returns a dict such as {'daily_pnl','total_profit','sharpe_ratio,'mean_daily_return'}

## Installation

Install numin2 using pip:

```bash
pip install numin2