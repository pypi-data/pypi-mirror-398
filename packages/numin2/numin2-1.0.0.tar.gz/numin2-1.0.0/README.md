# numin Package

**numin** is a Python package designed for algorithmic trading and backtesting providing an API called **NuminAPI**.

**numin v1** is out of service as of Dec 2025

**numin v2** is under development; features available are documented below

## Features

- **Data Retrieval:** Download training, round, and validation data.
- **Prediction Submission:**  TBD
- **Real-Time Round Management:** TBD
- **Backtesting:** TBD
- **File Management:** TBD
- **Returns Summary:** TBD

## Supported Methods

- **Data Download:**
    - `get_data_for_month(self,year,month,batch_size=4,window_size=100,target_type='rank'):`
    -   Returns a torch dataloader for the given year and month of Nifty 50 returns
    -   Dimension of each day is 100,50. Returns tensor of shape batch_size,window_size,50 for features.
    -   Targets are next day returns / ranked returns of shape batch_size,50
- **Backtesting:** 
    - `compute_pnl(positions,targets):`
    -  Run backtests - given positions n,50 dimensional 1,0,-1 for each stock per day
       and targets from dataloader for test month.
    -  Returns daily_pnl, Sharpe, total pnl etc.
    
## Installation

Install numin using pip:

```bash
pip install numin

