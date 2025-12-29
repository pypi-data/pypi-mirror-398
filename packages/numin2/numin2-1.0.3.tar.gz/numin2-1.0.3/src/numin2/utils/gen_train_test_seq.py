import os
import glob
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
import numpy as np

def consolidate_data(data_dir: str, output_file: str, columns=['timestamp', 'ticker', 'close_returns']) -> pd.DataFrame:
    """
    Reads all parquet files in data_dir, consolidates them into a single 
    DataFrame (index=Date, columns=Ticker), fills NaNs with 0, and saves to output_file.
    Handles duplicates if the same data appears in multiple files.
    """
    print(f"Scanning {data_dir} for parquet files...")
    files = glob.glob(os.path.join(data_dir, "*.parquet"))
    
    if not files:
        raise FileNotFoundError(f"No parquet files found in {data_dir}")
        
    print(f"Found {len(files)} files. Reading and consolidating...")
    
    all_dfs = []
    
    for f in files:
        try:
            # We must read ticker column now because file name isn't reliable source of truth for single ticker
            df = pd.read_parquet(f, columns=columns)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            all_dfs.append(df)
        except Exception as e:
            print(f"Error reading {f}: {e}")
            
    if not all_dfs:
        raise ValueError("No data could be read.")
        
    # Concatenate all raw data
    full_df = pd.concat(all_dfs, ignore_index=True)
    
    # Drop exact duplicates or duplicates on keys
    # We trust that (timestamp, ticker) should be unique.
    # If there are conflicts, we keep the last one/first one. 
    # Since we can't easily validate which source is "better", we just dedup.
    full_df = full_df.drop_duplicates(subset=['timestamp', 'ticker'], keep='last')
    
    # Pivot with multiple value columns is possible: result will be a "wide" DataFrame with a MultiIndex on columns
    print(f"Pivoting data with {len(full_df)} rows (multiple values: {columns})...")
    if len(columns)>3:
        consolidated_df = full_df.pivot(index='timestamp', columns='ticker', values=columns[2:])
    else:
        consolidated_df = full_df.pivot(index='timestamp', columns='ticker', values=columns[2])
    
    # Sort index
    consolidated_df = consolidated_df.sort_index()
    
    # Fill NaN with 0
    consolidated_df = consolidated_df.fillna(0.0)
    
    print(f"Consolidated data shape: {consolidated_df.shape}")
    print("Saving to parquet...")
    consolidated_df.to_parquet(output_file)
    print("Done.")
    
    return consolidated_df

class StockDataset(Dataset):
    def __init__(self, data_path: str, window_size: int = 30, 
                 target_type: str = 'raw', 
                 start_date: str = None, 
                 end_date: str = None,
                 top_k: int = 10):
        """
        Args:
            data_path: Path to the consolidated parquet file.
            window_size: Number of past days to use for prediction.
            target_type: 'raw' (returns floats) or 'rank' (returns 0..49 integers).
            start_date: Filter for targets on or after this date (ISO string YYYY-MM-DD).
            end_date: Filter for targets on or before this date (ISO string YYYY-MM-DD).
            top_k: k for 3-class classification (Top k, Bottom k).
        """
        self.window_size = window_size
        self.target_type = target_type
        self.top_k = top_k
        
        # Load data
        if not os.path.exists(data_path):
             raise FileNotFoundError(f"Data file not found at {data_path}")

        self.data_df = pd.read_parquet(data_path)
        # Ensure index is sorted datetime and remove timezone if present
        self.data_df.index = pd.to_datetime(self.data_df.index)
        if self.data_df.index.tz is not None:
             self.data_df.index = self.data_df.index.tz_localize(None)
        self.data_df = self.data_df.sort_index()
        
        # DataValues: (TotalDays, NumStocks)
        self.data_values = self.data_df.values.astype(np.float32)
        
        self.num_days, self.num_stocks = self.data_values.shape
        
        # Determine valid target indices based on date range
        # Indices are 0..num_days-1
        # We need to map dataset_idx -> valid_global_idx
        
        all_dates = self.data_df.index
        
        if start_date:
            start_mask = all_dates >= pd.to_datetime(start_date)
        else:
            start_mask = np.ones(len(all_dates), dtype=bool)
            
        if end_date:
            end_mask = all_dates <= pd.to_datetime(end_date)
        else:
            end_mask = np.ones(len(all_dates), dtype=bool)
            
        self.valid_indices = np.where(start_mask & end_mask)[0]
        print(self.valid_indices)
        
    def __len__(self):
        return len(self.valid_indices)
    
    def __getitem__(self, idx):
        if idx < 0 or idx >= len(self):
            raise IndexError("Index out of bounds")
            
        # Get the global index of the target
        target_idx = self.valid_indices[idx]
        
        # TARGET
        raw_target = self.data_values[target_idx]
        if self.target_type == 'rank' or self.target_type == '3class':
            # Compute ranks 0..N-1
            
            # First compute ranks for everyone
            ranks = np.argsort(np.argsort(raw_target)).astype(np.int64)
            
            # Mask out 0 returns with -1
            mask_zero = (raw_target == 0)
            
            if self.target_type == 'rank':
                ranks[mask_zero] = -1
                target = torch.from_numpy(ranks)
            else:
                # 3class
                # 0: Bottom k
                # 1: Middle
                # 2: Top k
                
                # Ranks: 0..49.
                # Bottom k: ranks < top_k
                # Top k: ranks >= 50 - top_k
                # Middle: rest
                
                # Create output array with default class 1 (Middle)
                classes = np.ones_like(ranks)
                
                classes[ranks < self.top_k] = 0 # Bottom k
                classes[ranks >= (self.num_stocks - self.top_k)] = 2 # Top k
                
                classes[mask_zero] = -1 # Invalid
                
                target = torch.from_numpy(classes)
        else:
            target = torch.from_numpy(raw_target)

        # INPUT SEQUENCE
        # We need [target_idx - window_size : target_idx]
        # But we must handle target_idx < window_size by padding
        
        start_seq_idx = target_idx - self.window_size
        
        if start_seq_idx >= 0:
            input_seq = self.data_values[start_seq_idx : target_idx]
        else:
            # We need padding
            # available history is [0 : target_idx]
            available_data = self.data_values[0 : target_idx]
            pad_len = self.window_size - target_idx
            # Pad with zeros at the beginning
            padding = np.zeros((pad_len, self.num_stocks), dtype=np.float32)
            input_seq = np.concatenate([padding, available_data], axis=0)
            
        return torch.from_numpy(input_seq), target

def get_month_dataloader(data_path: str, year: int, month: int, 
                         batch_size: int = 32, window_size: int = 100, 
                         target_type: str = 'raw', top_k: int = 10):
    """
    Returns a DataLoader for a specific month.
    """
    # Construct start and end dates
    start_date = f"{year}-{month:02d}-01"
    # To find end date, go to next month day 1 and subtract 1 day, or just use pandas to check
    # Easier: use pandas Period or MonthEnd (but we want simple string logic if possible)
    # Let's rely on pandas flexibility in Dataset or just calculate end date.
    # Simple trick: start of next month
    if month == 12:
        next_val = f"{year+1}-01-01"
    else:
        next_val = f"{year}-{month+1:02d}-01"
        
    end_date_ts = pd.to_datetime(next_val) - pd.Timedelta(days=1)
    end_date = end_date_ts.strftime('%Y-%m-%d')
    
    print(f"Creating DataLoader for {start_date} to {end_date}...")
    
    dataset = StockDataset(data_path, window_size=window_size, 
                           target_type=target_type,
                           start_date=start_date, end_date=end_date, top_k=top_k)
    
    return DataLoader(dataset, batch_size=batch_size, shuffle=True)

def get_range_dataloader(data_path: str, start_year: int, start_month: int,
                         end_year: int, end_month: int,
                         batch_size: int = 32, window_size: int = 100,
                         target_type: str = 'raw', top_k: int = 10):
    """
    Returns a DataLoader for a specific date range [start_date, end_date].
    Range includes end_month.
    """
    start_date = f"{start_year}-{start_month:02d}-01"
    
    # Calculate end date: 1st of (end_month + 1) - 1 day
    if end_month == 12:
        next_val = f"{end_year+1}-01-01"
    else:
        next_val = f"{end_year}-{end_month+1:02d}-01"
        
    end_date_ts = pd.to_datetime(next_val) - pd.Timedelta(days=1)
    end_date = end_date_ts.strftime('%Y-%m-%d')
    
    print(f"Creating DataLoader for {start_date} to {end_date}...")
    
    dataset = StockDataset(data_path, window_size=window_size, 
                           target_type=target_type,
                           start_date=start_date, end_date=end_date, top_k=top_k)
    
    return DataLoader(dataset, batch_size=batch_size, shuffle=True)

if __name__ == "__main__":
    # Configuration
    DATA_DIR = "/Users/gautamshroff/Code/MyCode/ai_fin/data/equity/daily"
    OUTPUT_FILE = "/Users/gautamshroff/Code/MyCode/ai_fin/data/equity/consolidated_returns.parquet"
    WINDOW_SIZE = 100
    
    # 1. Consolidate Data (if needed)
    if not os.path.exists(OUTPUT_FILE):
        print("Consolidating data...")
        consolidate_data(DATA_DIR, OUTPUT_FILE)

    # 2. Verify 'Rank' Targets and Padding
    print("\n--- Verifying Rank Targets ---")
    # Use a small window to force potential padding if we pick early date
    # Pick a date range at the start of the file: 2003-01
    
    # 3. Verify 'Rank' Targets and Padding
    print("\n--- Verifying Rank Targets ---")
    
    dl_jan_2007 = get_month_dataloader(OUTPUT_FILE, 2007, 1, batch_size=4, window_size=WINDOW_SIZE, target_type='rank')
    rl_jan_2020 = get_month_dataloader(OUTPUT_FILE, 2020, 1, batch_size=4, window_size=WINDOW_SIZE, target_type='rank')
    
    print(f"Jan 2007 Dataset length: {len(dl_jan_2007.dataset)}")
    
    for inputs, targets, inputs1, targets1 in zip(dl_jan_2007,rl_jan_2020):
        print(f"Input batch shape: {inputs.shape}")
        print(f"Target batch shape: {targets.shape}")
        print(f"Input batch shape: {inputs1.shape}")
        print(f"Target batch shape: {targets1.shape}")
        
        # Check for -1 ranks
        invalid_ranks = (targets == -1).sum()
        print(f"Number of -1 ranks in batch: {invalid_ranks}")
        
        if invalid_ranks > 0:
             print("Verified: -1 ranks present for zero returns.")
        else:
             print("Note: No zero returns found in this batch (or logic failed if zeros existed).")
             
        # Check ranges
        valid_targets = targets[targets != -1]
        if len(valid_targets) > 0:
            print("Valid Target min/max:", valid_targets.min().item(), valid_targets.max().item())
        
        break
        
    # 3. Verify Normal Month (No Padding)
    print("\n--- Verifying Normal Month (2020-01) ---")
    dl_jan_2020 = get_month_dataloader(OUTPUT_FILE, 2020, 1, batch_size=4, window_size=WINDOW_SIZE, target_type='raw')
    rl_jan_2020 = get_month_dataloader(OUTPUT_FILE, 2020, 1, batch_size=4, window_size=WINDOW_SIZE, target_type='rank')
    print(len(rl_jan_2020.dataset))
     
    for inputs, targets in rl_jan_2020: 
        print(f"Input batch shape: {inputs.shape}")
        print(f"Target batch shape: {targets[0]}")
        print("First sample input sum (should not be 0):", inputs[0])
        break