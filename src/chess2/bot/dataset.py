import torch
from torch.utils.data import Dataset

class ChessDataset(Dataset):
    def __init__(self, transform, target_transform):
        self.transform = transform
        self.target_transform = target_transform


    def __getitem__(self, index):
        pass
