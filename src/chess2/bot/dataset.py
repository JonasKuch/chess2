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



# import tarfile
# import struct
# import gzip
# import bisect
# import itertools
# import numpy as np
# from torch.utils.data import Dataset


# class ChessDataset(Dataset):
#     def __init__(self, path, length):
#         self.path = path
#         self.length = length

#         # Define the struct for V3 records
#         self.V3_STRUCT = struct.Struct(
#             '<I'      # version
#             '1858f'   # probabilities
#             '104Q'    # bitboard planes
#             '7B'      # 4 castling + side + rule50 + move_count
#             'b'       # result
#         )
#         self.RECORD_SIZE = self.V3_STRUCT.size  # 8276 bytes

#         # Precompute number of records per game file
#         self.game_lengths = []
#         self._count_lines_per_game()
#         # Cumulative sum for fast indexing
#         self.cum_lengths = list(itertools.accumulate(self.game_lengths))

#     def _count_lines_per_game(self):
#         with tarfile.open(self.path, 'r:bz2') as tar:
#             total_count = 0
#             for member in tar:
#                 if not member.isfile() or not member.name.endswith('.gz'):
#                     continue

#                 game_count = 0
#                 gz_stream = tar.extractfile(member)
#                 if gz_stream is None:
#                     continue

#                 with gzip.GzipFile(fileobj=gz_stream, mode='rb') as f:
#                     while True:
#                         chunk = f.read(self.RECORD_SIZE)
#                         if not chunk:
#                             break
#                         if len(chunk) < self.RECORD_SIZE:
#                             raise IOError(f"Incomplete record in {member.name}")
#                         game_count += 1
#                         total_count += 1

#                         if total_count >= self.length:
#                             break

#                 self.game_lengths.append(game_count)
#                 if total_count >= self.length:
#                     break

#     def __len__(self):
#         return self.length

#     def __getitem__(self, idx):
#         # Find which .gz file contains this index
#         file_idx = bisect.bisect_right(self.cum_lengths, idx)
#         prev_count = 0 if file_idx == 0 else self.cum_lengths[file_idx - 1]
#         inner_idx = idx - prev_count

#         # Open only the required member
#         with tarfile.open(self.path, 'r:bz2') as tar:
#             gz_count = 0
#             for member in tar:
#                 if not member.isfile() or not member.name.endswith('.gz'):
#                     continue

#                 if gz_count == file_idx:
#                     gz_stream = tar.extractfile(member)
#                     break

#                 gz_count += 1
#             else:
#                 raise IndexError(f"No .gz file at index {file_idx}")


#         # Iterate records until inner_idx
#             for rec_i, record in enumerate(self._parse_v3_gzip_stream(gz_stream)):
#                 if rec_i == inner_idx:
#                     return record

#         raise IndexError(f"Index {idx} out of range")

#     def _bitboard_to_matrix(self, bb_array):
#         matrices = []
#         for bb in bb_array:
#             # unpack into bits
#             bits = np.unpackbits(
#                 np.array([bb], dtype=np.uint64).view(np.uint8)
#             )
#             bits = np.flip(bits.reshape(8, 8), axis=(0, 1))
#             matrices.append(bits)
#         return np.stack(matrices, axis=0)

#     def _parse_v3_gzip_stream(self, gzip_stream):
#         """
#         Generator yielding one record at a time.
#         Returns: dict with keys version, probs, planes, side, rule50, move_count, result
#         """
#         with gzip.GzipFile(fileobj=gzip_stream, mode='rb') as f:
#             while True:
#                 chunk = f.read(self.RECORD_SIZE)
#                 if not chunk:
#                     return
#                 if len(chunk) < self.RECORD_SIZE:
#                     raise IOError("Incomplete record")

#                 data = self.V3_STRUCT.unpack(chunk)
#                 version = data[0]
#                 probs = np.array(data[1:1 + 1858], dtype=np.float32)
#                 raw_planes = np.array(data[1 + 1858:1 + 1858 + 104], dtype=np.uint64)
#                 bitboard_planes = self._bitboard_to_matrix(raw_planes)

#                 off = 1 + 1858 + 104
#                 cast_us_ooo, cast_us_oo, cast_th_ooo, cast_th_oo, side, rule50, mv_cnt = data[off:off + 7]
#                 result = data[off + 7]

#                 # Extra planes for metadata
#                 extras = np.stack([
#                     np.full((8, 8), side, dtype=np.uint8),
#                     np.full((8, 8), cast_us_oo, dtype=np.uint8),
#                     np.full((8, 8), cast_us_ooo, dtype=np.uint8),
#                     np.full((8, 8), cast_th_oo, dtype=np.uint8),
#                     np.full((8, 8), cast_th_ooo, dtype=np.uint8),
#                 ], axis=0)

#                 planes = np.concatenate([bitboard_planes.astype(np.uint8), extras], axis=0)

#                 yield {
#                     'version': version,
#                     'probs': probs,
#                     'planes': planes,
#                     'side': side,
#                     'rule50': rule50,
#                     'move_count': mv_cnt,
#                     'result': result
#                 }
