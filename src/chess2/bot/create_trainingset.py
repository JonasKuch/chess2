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


def best_move_one_hot(best_move):
    vector = np.zeros(4672)
    """
    queen-like moves:

    1 step forwards
    2 steps forwards
    ...
    7 steps forwards
    1 step diagonally right forwards
    ...
    7 steps diagonally right forwards
    1 step right
    ...
    7 steps right
    1 step diagonally right backwards
    ...
    1 step backwards
    ...
    1 step diagonally left backwards
    ...
    1 step left
    ...
    1 step diagonally left forwards
    ...

    
    knight moves:

    top top right
    top right right
    bottom right right
    bottom bottom right
    bottom bottom left
    bottom left left
    top left left
    top top left

    
    underpromotions:

    take left and promote to knight
    step and promote to knight
    take right and promote to knight

    take left and promote to bishop
    step and promote to bishop
    take right and promote to bishop

    take left and promote to rook
    step and promote to rook
    take right and promote to rook



    every one of these steps takes up 64 entries of the array (8x8 possible start locations, sweeping bottom to top, left to right):

    0th entry is 1 step ahead from a1 (bottom left), 
    1st entry is 1 step ahead from b1, 
    ...
    63rd entry is 1 step ahead from h8 (always illegal but doesnt matter here),
    64th entry is 2 steps ahead from a1,
    ...

    """

    # Initialize one-hot vector
    vector = np.zeros(4672, dtype=np.int8)

    # Map files and ranks to 0-based indices
    file_map = {f: i for i, f in enumerate('abcdefgh')}
    rank_map = {r: i for i, r in enumerate('12345678')}

    # Direction vectors for sliding (queen-like) moves
    slide_dirs = [(0, 1), (1, 1), (1, 0), (1, -1),
                  (0, -1), (-1, -1), (-1, 0), (-1, 1)]

    # Knight move vectors
    knight_dirs = [(1, 2), (2, 1), (2, -1), (1, -2),
                   (-1, -2), (-2, -1), (-2, 1), (-1, 2)]

    # Parse UCI string
    frm, to = best_move[0:2], best_move[2:4]
    prom = best_move[4] if len(best_move) == 5 else None

    sx, sy = file_map[frm[0]], rank_map[frm[1]]
    ex, ey = file_map[to[0]], rank_map[to[1]]
    dx, dy = ex - sx, ey - sy

    # Compute from-square index: a1=0, b1=1, ..., h8=63
    from_index = sy * 8 + sx

    move_type = None

    # Handle underpromotions (non-queen)
    if prom in ('n', 'b', 'r'):
        # Determine capture vs step
        if dx == -1:
            move_offset = 0  # left capture
        elif dx == 0:
            move_offset = 1  # step
        elif dx == 1:
            move_offset = 2  # right capture
        else:
            raise ValueError(f"Invalid promotion move: {best_move}")

        # Promotion piece blocks: knight=0, bishop=3, rook=6
        piece_block = {'n': 0, 'b': 3, 'r': 6}[prom]
        move_type = 64 + piece_block + move_offset

    # Handle knight moves
    elif (dx, dy) in knight_dirs:
        k_idx = knight_dirs.index((dx, dy))
        move_type = 56 + k_idx

    # Handle sliding moves (including queen promotions)
    else:
        # Find direction index
        try:
            dir_idx = slide_dirs.index((np.sign(dx), np.sign(dy)))
        except ValueError:
            raise ValueError(f"Illegal sliding move: {best_move}")

        distance = max(abs(dx), abs(dy))
        if distance < 1 or distance > 7:
            raise ValueError(f"Invalid slide distance: {best_move}")

        move_type = dir_idx * 7 + (distance - 1)

    # Global index in one-hot vector
    idx = move_type * 64 + from_index
    vector[idx] = 1
    return vector


def reformat(line):
    data = json.loads(line)

    fen = data.get("fen")
    best_move = data.get("best_move")
    val = data.get("val")
    depth = data.get("depth")

    in_tensor = fen_to_tensor(fen)
    move_target = best_move_one_hot(best_move)
    val_target = np.float32(val)
    depth = np.float32(depth)

    return in_tensor, move_target, val_target, depth


def append_block(file, in_tensor_block, move_target_block, val_target_block, depth_block):

    for name, block in [
        ("input", in_tensor_block),
        ("move_target", move_target_block),
        ("val_target", val_target_block),
        ("depth", depth_block)
    ]:
        dataset = file[name]
        old_len = dataset.len()
        block_len = block.shape[0]
        new_len = old_len + block_len
        dataset.resize((new_len, ) + dataset.shape[1:])
        dataset[old_len:new_len, ...] = block



def stream(in_path, out_path, workers):

    pool = Pool(workers)

    with open(in_path, "r") as in_file, \
         h5py.File(out_path, "w") as out_file:
        
        out_file.create_dataset("input", (0, 18, 8, 8), dtype=np.float32, maxshape=(None, 18, 8, 8), chunks=(1, 18, 8, 8), compression="gzip")
        out_file.create_dataset("move_target", (0, 4672), dtype=np.int8, maxshape = (None, 4672), chunks = (1, 4672), compression="gzip")
        out_file.create_dataset("val_target", (0, 1), dtype = np.float32, maxshape=(None, 1), chunks=(1, 1), compression="gzip")
        out_file.create_dataset("depth", (0, 1), dtype=np.int8, maxshape=(None, 1), chunks=(1, 1), compression="gzip")
        
        tasks = []

        for line in in_file:
            tasks.append(line)

            if len(tasks) >= 10*workers:
                out_list = list(pool.imap_unordered(reformat, tasks, chunksize=workers))
                in_tensor_list, move_target_list, val_target_list, depth_list = zip(*out_list)
                append_block(
                    out_file, 
                    np.stack(in_tensor_list), 
                    np.stack(move_target_list), 
                    np.stack(val_target_list)[:, None], 
                    np.stack(depth_list)[:, None]
                )
                tasks.clear()
            
        if tasks:
            out_list = list(pool.map(reformat, tasks))
            in_tensor_list, move_target_list, val_target_list, depth_list = zip(*out_list)
            append_block(
                out_file, 
                np.stack(in_tensor_list), 
                np.stack(move_target_list), 
                np.stack(val_target_list)[:, None], 
                np.stack(depth_list)[:, None]
            )
            tasks.clear()


    pool.close()
    pool.join()


if __name__ == "__main__":
    in_path = "src/chess2/bot/data/lichess_filtered.jsonl"
    out_path = "src/chess2/bot/data/training_data.h5"
    workers = cpu_count()

    stream(in_path, out_path, workers)
