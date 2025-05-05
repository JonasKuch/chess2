import torch
from torch.utils.data import Dataset
import numpy as np
from diskcache import FanoutCache


class ChessDataset(Dataset):

    def __init__(self, files: list, cache_dir: str = "src/chess2/bot/data/.cache", cache_size_limit: int = 1_000_000_000):
        '''
        all files of my datasets have the same lengths
        '''

        self.files = files

        example = np.load(self.files[0], "r")
        self.file_len = len(example["depth"])
        self.total_samples = self.file_len * len(self.files)

        self.cache = FanoutCache(
            directory=cache_dir,
            size_limit=cache_size_limit,
            eviction_policy='least-recently-used',
        )


    def __len__(self):
        return self.total_samples


    def _load_file(self, file_idx: int) -> dict:
        """
        Load .npz file by index, caching the result on disk.
        If the cache exceeds the size limit, the least-recently-used
        file entries will be evicted automatically.
        """
        # Attempt to retrieve from cache
        data = self.cache.get(file_idx)
        if data is not None:
            return data

        # Otherwise load from disk and store in cache
        path = self.files[file_idx]
        with np.load(path, "r") as npz:
            file_data = {key: npz[key] for key in npz.files}

        self.cache.set(file_idx, file_data)
        return file_data


    def __getitem__(self, idx: int):
        file_idx = idx // self.file_len
        inner_idx = idx % self.file_len

        file_data = self._load_file(file_idx)

        input_tensor = torch.from_numpy(file_data["input"][inner_idx])
        move_tgt_tensor = torch.from_numpy(file_data["move_target"][inner_idx])
        val_tgt_tensor = torch.tensor([file_data["val_target"][inner_idx]], dtype=torch.float32)
        depth_tensor = torch.tensor(file_data["depth"][inner_idx], dtype=torch.int16)

        return input_tensor, move_tgt_tensor, val_tgt_tensor, depth_tensor


    def __del__(self):
        # Ensure the cache closes its database connections
        try:
            self.cache.close()
        except Exception:
            pass
