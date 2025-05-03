import orjson as json
import h5py
import numpy as np
from multiprocessing import Pool, cpu_count

# rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1

def fen_to_tensor(fen):
    tensor = np.zeros((18, 8, 8), dtype=np.float32)
    '''
    White Pawns (occuppied fields marked as 1, others as 0)
    White Knights
    White Bishops
    White Rooks
    White Queens
    White King
    Black Pawns
    Black Knights
    Black Bishops
    Black Rooks
    Black Queens
    Black King
    Move Board (all 1 if white is to move else all 0)
    White Kingside Castling (all 1 if possible else all 0)
    White Queenside Castling
    Black Kingside Castling
    Black Queenside Castling
    En Passant Target Square (marked as 1, all others 0)
    '''

    piece_map = {"P":0, "N":1, "B":2, "R":3, "Q":4, "K":5,
                 "p":6, "n":7, "b":8, "r":9, "q":10, "k":11}
    
    fen_parts = fen.split()
    board_rows = fen_parts[0].split("/")
    side_to_move = fen_parts[1]
    castling_rights = fen_parts[2]
    en_passant_target = fen_parts[3]

    for row_idx, row_str in enumerate(board_rows):
        col_idx = 0

        for char in row_str:
            if char.isdigit():
                col_idx += int(char)
            else:
                tensor[piece_map[char], 7-row_idx, col_idx] = 1
                col_idx += 1

    tensor[12, :, :] = 1 if side_to_move == "w" else 0

    tensor[13, :, :] = 1 if "K" in castling_rights else 0
    tensor[14, :, :] = 1 if "Q" in castling_rights else 0
    tensor[15, :, :] = 1 if "k" in castling_rights else 0
    tensor[16, :, :] = 1 if "q" in castling_rights else 0

    if en_passant_target != "-":
        file_map = {'a': 0, 'b': 1, 'c': 2, 'd': 3,
                    'e': 4, 'f': 5, 'g': 6, 'h': 7}
        col = file_map[en_passant_target[0]]
        row = 8 - int(en_passant_target[1])
        tensor[17, row, col] = 1
    
    return tensor


if __name__ == "__main__":
    fen = "rnb1r1k1/ppp2pbp/5np1/4p1B1/2P1P3/2N2N2/PP2BPPP/2KR3R b Kq -"
    tensor = fen_to_tensor(fen)
    for grid in tensor:
        print(grid)
