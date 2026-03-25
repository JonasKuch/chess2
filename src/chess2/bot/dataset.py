# import torch
# from torch.utils.data import Dataset
# import h5py

# class ChessDataset(Dataset):
#     def __init__(self, h5path):
#         self.h5path = h5path
        
    
#     def _open_file(self):
#         """Opens the file within each worker process."""
#         return h5py.File(self.h5path, "r")

    
#     def __len__(self):
#         with self._open_file() as file: # open file in every method to enable multithreading with h5 files
#             depth = file["depth"]
#             return depth.shape[0]


#     def __getitem__(self, idx):
#         with self._open_file() as file: # open file in every method to enable multithreading with h5 files
#             input_tensor = torch.from_numpy(file["input"][idx])
#             move_tgt_tensor = torch.from_numpy(file["move_target"][idx])
#             val_tgt_tensor = torch.tensor([file["val_target"][idx]], dtype=torch.float32)
#             depth_tensor = torch.tensor(file["depth"][idx])
#             moves_mask = torch.from_numpy(file["moves_mask"][idx])
#         return input_tensor, move_tgt_tensor, val_tgt_tensor, depth_tensor, moves_mask


import torch
from torch.utils.data import Dataset
import joblib
import tarfile
import gzip
import io
import struct
import numpy as np

class ChessDataset(Dataset):
    def __init__(self, path, start, end):
        all_data = joblib.load(path)
        self.data = all_data[start : end]

    def bitboard_to_matrix(self, bb):
        """
        bb: a Python integer 0 <= bb < 2**64
        returns: 8×8 numpy array, row-major with row 0 = rank 1, col 0 = file a
        """
        bits = np.unpackbits(
            np.array([bb], dtype=np.uint64).view(np.uint8)
        )
        bits = np.flip(bits.reshape(8,8), axis=(0,1))
        return bits
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        bitboards, flags, prob_idx = self.data[idx]

        boards = []
        for bb in bitboards:
            board = self.bitboard_to_matrix(bb)
            boards.append(board)
        
        boards = np.array(boards)
        boards_tensor = torch.tensor(boards, dtype=torch.float32)
        flags = torch.tensor(flags, dtype=torch.float32)
        prob_idx = torch.tensor(prob_idx, dtype=torch.long)

        return boards_tensor, flags, prob_idx
    

if __name__ == "__main__":
    from torch.utils.data import DataLoader

    dataset = ChessDataset("/Users/jonas/coding/python/chess2/src/chess2/bot/data_leela/chess_data_list.pkl")
    loader = DataLoader(dataset, batch_size=1, shuffle=False)

    data_iter = iter(loader)
    for i in range(50):
        boards, flags, prob_idx = next(data_iter)
        full_board = boards[0].sum(dim=0)
        print(full_board)
        print(flags)
        print(prob_idx)
