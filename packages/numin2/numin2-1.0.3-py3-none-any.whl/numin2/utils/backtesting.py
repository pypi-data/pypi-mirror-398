import numpy as np
import torch

def compute_pnl(positions, targets, txn_cost=.999):
    """
    Computes PnL for a single day/batch based on positions and raw targets.
    positions: (50,) array of {1, -1, 0}
    """
    targets = targets.cpu().numpy().flatten() # (50,) raw returns
    targets = targets*txn_cost
    
    long_indices = np.where(positions > 0)[0]
    short_indices = np.where(positions < 0)[0]
    
    # Calculate Profit
    daily_pnl = 0.0
    
    total_long = 0.0
    if len(long_indices) > 0:
        total_long = np.sum(targets[long_indices]*positions[long_indices])
        
    total_short = 0.0
    if len(short_indices) > 0:
        total_short = np.sum(targets[short_indices]*positions[short_indices])
    
    total_positions = len(long_indices) + len(short_indices)
    total_positions = sum(positions[long_indices])-sum(positions[short_indices])
    
    if total_positions > 0:
        daily_pnl = (total_long + total_short) / total_positions
    else:
        daily_pnl = 0.0
        
    return daily_pnl

def gen_pnl(positions, targets, txn_cost=.999):
    
    # positions: list of numpy arrays, list of lists, or single numpy array (1D/2D)
    # targets: corresponding targets
    
    # Convert to numpy first to check dims easily
    if isinstance(positions, list):
        positions = np.array(positions)
    if isinstance(targets, list):
        targets = np.array(targets)
        
    # If 1D array provided (e.g. single day), wrap it to make it iterable over days
    if positions.ndim == 1:
        positions = positions[np.newaxis, :] # (1, 50)
    if targets.ndim == 1:
        targets = targets[np.newaxis, :]
        
    daily_profits = []
    
    # Iterate over the days (rows)
    for pos, tgt in zip(positions, targets):
        # pos, tgt are (50,) arrays now
        
        # Convert targets to tensor as required by compute_pnl logic
        tgt_tensor = torch.from_numpy(tgt)
        
        # compute_pnl expects positions as numpy (50,) and targets as tensor
        pnl = compute_pnl(pos, tgt_tensor, txn_cost=txn_cost)
        daily_profits.append(pnl)
        
    daily_profits = np.array(daily_profits)
    total_profit = np.sum(daily_profits)
    mean_profit = np.mean(daily_profits)
    sharpe = mean_profit / (np.std(daily_profits) + 1e-9) * np.sqrt(252)
    
    return {
        'daily_pnl': daily_profits.tolist(),
        'total_profit': float(total_profit),
        'sharpe_ratio': float(sharpe),
        'mean_daily_return': float(mean_profit)
    }