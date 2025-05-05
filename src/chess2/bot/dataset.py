import torch
from torch.utils.data import Dataset
import numpy as np


class ChessDataset(Dataset):

    def __init__(self, files: list):
        '''
        all files of my datasets have the same lengths
        '''

        self.files = files

        example = np.load(self.files[0], "r")
        self.file_len = len(example["depth"])
        self.total_samples = self.file_len * len(self.files)


    def __len__(self):
        return self.total_samples


    def __getitem__(self, idx: int):
        file_idx = idx // self.file_len
        inner_idx = idx % self.file_len

        with np.load(self.files[file_idx]) as file_data:

            input_tensor = torch.from_numpy(file_data["input"][inner_idx])
            move_tgt_tensor = torch.from_numpy(file_data["move_target"][inner_idx])
            val_tgt_tensor = torch.tensor([file_data["val_target"][inner_idx]], dtype=torch.float32)
            depth_tensor = torch.tensor(file_data["depth"][inner_idx], dtype=torch.int16)

        return input_tensor, move_tgt_tensor, val_tgt_tensor, depth_tensor
