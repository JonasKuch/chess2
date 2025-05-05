import torch
from torch.utils.data import Dataset
import h5py

class ChessDataset(Dataset):
    def __init__(self, h5path):
        file = h5py.File(h5path, "r")
        self.inputs = file["input"]
        self.move_tgts = file["move_target"]
        self.val_tgts = file["val_target"]
        self.depth = file["depth"]

    
    def __len__(self):
        return self.depth.shape[0]


    def __getitem__(self, idx):
        input_tensor = torch.from_numpy(self.inputs[idx])
        move_tgt_tensor = torch.from_numpy(self.move_tgts[idx])
        val_tgt_tensor = torch.tensor(self.val_tgts[idx])
        depth_tensor = torch.tensor(self.depth[idx])
        return input_tensor, move_tgt_tensor, val_tgt_tensor, depth_tensor