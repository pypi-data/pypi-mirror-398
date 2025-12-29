#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import anvil.server
import pandas as pd
import torch
import numpy as np
from torch.utils.data import Dataset
from .utils.backtesting import gen_pnl
# from utils.backtesting import gen_pnl


# In[ ]:


ANVIL_CLIENT_KEY="FMQBTGZ2T6DRDZISLDZ3XMIH-BRX4OESLV4HADBHN-CLIENT"
# anvil.server.connect(ANVIL_CLIENT_KEY)


# In[ ]:


class NuminDataset(Dataset):
    def __init__(self, samples, targets):
        self.samples = samples
        self.targets = targets

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        # Perform any necessary transformations here
        x = torch.tensor(self.samples[idx]).float()
        y = torch.tensor(self.targets[idx]).long()
        return x, y


# In[ ]:


class Numin2API():
    def __init__(self, api_key: str = None):
        """
        Initializes the Numin2API instance.

        Parameters:
        - api_key (str, optional): The API key for authenticating requests.
        """
        
        print("importing remotely")

        self.api_key = api_key
        self.uplink_key = ANVIL_CLIENT_KEY # trader uplink key
        
        anvil.server.connect(self.uplink_key) 

    def get_data_for_month(self,year,month,batch_size=4,window_size=100,target_type='rank'):
        XR,YR=anvil.server.call('get_data_for_month',year=2025,month=month,batch_size=batch_size,window_size=window_size,target_type=target_type)
        numin_dataset = NuminDataset(XR, YR)
        return numin_dataset

    def backtest_positions(self,positions,targets):
        if hasattr(positions, 'detach'): positions = positions.detach().cpu().numpy()
        if hasattr(targets, 'detach'): targets = targets.detach().cpu().numpy()
        positions = np.asarray(positions)
        targets = np.asarray(targets)
        if positions.shape[-1] != targets.shape[-1]:
            raise ValueError("Positions and targets must have the same number of columns")
        return gen_pnl(positions,targets)     


# In[ ]:


# backtest_positions(positions,targets)


# In[ ]:




