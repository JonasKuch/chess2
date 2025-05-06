import torch
from torch.utils.data import Dataset
import h5py

class ChessDataset(Dataset):
    def __init__(self, h5path):
        self.h5path = h5path
        
    
    def _open_file(self):
        """Opens the file within each worker process."""
        return h5py.File(self.h5path, "r")

    
    def __len__(self):
        with self._open_file() as file: # open file in every method to enable multithreading with h5 files
            depth = file["depth"]
            return depth.shape[0]


    def __getitem__(self, idx):
        with self._open_file() as file: # open file in every method to enable multithreading with h5 files
            input_tensor = torch.from_numpy(file["input"][idx])
            move_tgt_tensor = torch.from_numpy(file["move_target"][idx])
            val_tgt_tensor = torch.tensor([file["val_target"][idx]], dtype=torch.float32)
            depth_tensor = torch.tensor(file["depth"][idx])
            moves_mask = torch.from_numpy(file["moves_mask"][idx])
        return input_tensor, move_tgt_tensor, val_tgt_tensor, depth_tensor, moves_mask