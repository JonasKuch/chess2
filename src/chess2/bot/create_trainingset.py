import orjson as json
import h5py
import numpy as np
from multiprocessing import Pool, cpu_count
import chess
import copy

# rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1

class TrainingSetProcessor:
    def __init__(self):
        # move_index_map = { self.index_to_uci(i):i for i in range(4672) }
        pass
    

    def flip_coords(self, col, row):
        return 7-col, 7-row 


    def fen_to_tensor(self, fen):
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


        always from perspective of player to move
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
                    c, r = col_idx, row_idx

                    if side_to_move == "b":
                        c, r = self.flip_coords(c, r)

                    tensor[piece_map[char], r, c] = 1
                    col_idx += 1

        tensor[12, :, :] = 1 if side_to_move == "w" else 0

        tensor[13, 7, 7] = 1 if "K" in castling_rights else 0
        tensor[14, 7, 0] = 1 if "Q" in castling_rights else 0
        tensor[15, 0, 7] = 1 if "k" in castling_rights else 0
        tensor[16, 0, 0] = 1 if "q" in castling_rights else 0
        
        if side_to_move == "b":
            castling_tensors = [copy.deepcopy(tensor[i]) for i in range(13, 17)]
            tensor[13] = np.flip(castling_tensors[2], axis=(0, 1))
            tensor[14] = np.flip(castling_tensors[3], axis=(0, 1))
            tensor[15] = np.flip(castling_tensors[0], axis=(0, 1))
            tensor[16] = np.flip(castling_tensors[1], axis=(0, 1))

        if en_passant_target != "-":
            file_map = {'a': 0, 'b': 1, 'c': 2, 'd': 3,
                        'e': 4, 'f': 5, 'g': 6, 'h': 7}
            col, row = file_map[en_passant_target[0]], 8 - int(en_passant_target[1])
            if side_to_move == "b":
                col, row = self.flip_coords(col, row)
            tensor[17, row, col] = 1
        
        return tensor, side_to_move


    def best_move_one_hot(self, best_move, side_to_move):

        """
        queen-like moves:

        1 step forward
        2 steps forward
        ...
        7 steps forward
        1 step diagonally right forward
        ...
        7 steps diagonally right forward
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
        1 step diagonally left forward
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

        Total: 4672 entries

        always from perspective of player to move

        """

        # Initialize one-hot vector
        vector = np.zeros(4672, dtype=np.int8)

        # Map files and ranks to 0-based indices
        file_map = {f: i for i, f in enumerate('abcdefgh')} if side_to_move == "w" else {f: 7-i for i, f in enumerate('abcdefgh')}
        rank_map = {r: 7-i for i, r in enumerate('12345678')} if side_to_move == "w" else {r: i for i, r in enumerate('12345678')}

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
        dx, dy = ex - sx, sy - ey                           # dy > 0 --> forward, dx > 0 --> right

        # Compute from-square index: a1=0, b1=1, ..., h8=63
        from_index = (7-sy) * 8 + sx

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


    def index_to_uci(self, idx: int, side_to_move) -> str:
        """
        Decode a single move-index in [0,4671] to UCI string.
        """

        # directions for sliding moves (queen‑like), in (dx,dy)
        _SLIDE_DIRS = [
            ( 0, 1),  # north
            ( 1, 1),  # north‑east
            ( 1, 0),  # east
            ( 1,-1),  # south‑east
            ( 0,-1),  # south
            (-1,-1),  # south‑west
            (-1, 0),  # west
            (-1, 1),  # north‑west
        ]

        # knight jumps
        _KNIGHT_DIRS = [
            ( 1, 2), ( 2, 1), ( 2,-1), ( 1,-2),
            (-1,-2), (-2,-1), (-2, 1), (-1, 2),
        ]

        _FILE_LETTERS = "abcdefgh"
        _RANK_LETTERS = "12345678"

        file_map = {i: f for i, f in enumerate('abcdefgh')} if side_to_move == "w" else {7-i: f for i, f in enumerate('abcdefgh')}
        rank_map = {7-i: r for i, r in enumerate('12345678')} if side_to_move == "w" else {i: r for i, r in enumerate('12345678')}

        # split into move_type (0–72) and from-square (0–63)
        move_type = idx // 64
        from_sq   = idx % 64
        fx = from_sq % 8
        fy = 7 - from_sq // 8

        # default: no promotion
        promo = ""

        # sliding moves
        if move_type < 56:
            dir_idx  = move_type // 7
            distance = (move_type % 7) + 1
            dx, dy = _SLIDE_DIRS[dir_idx]
            tx = fx + dx * distance
            ty = fy - dy * distance

        # knight moves
        elif move_type < 64:
            k_idx = move_type - 56
            dx, dy = _KNIGHT_DIRS[k_idx]
            tx = fx + dx
            ty = fy - dy

        # underpromotions (non‑queen)
        else:
            # move_type 64–72
            up = move_type - 64
            piece_block = (up // 3)  # 0=knight,1=bishop,2=rook
            move_offset = up % 3     # 0=capture-left,1=step,2=capture-right
            # direction: always one step forward (dy=+1)
            dy = 1
            if move_offset == 0:
                dx = -1
            elif move_offset == 1:
                dx = 0
            else:
                dx = 1
            tx = fx + dx
            ty = fy - dy
            promo = {0:'n',1:'n',2:'n', 3:'b',4:'b',5:'b', 6:'r',7:'r',8:'r'}[up]

        # convert coords back to UCI
        def square(x,y):
            return file_map[x] + rank_map[y]

        return square(fx, fy) + square(tx, ty) + promo


    def decode_policy_vector(self, vec, side_to_move):
        """
        Given a length-4672 policy vector (logits or probs or one-hot),
        pick the highest entry and return its UCI move.
        """
        idx = int(np.argmax(vec))
        return self.index_to_uci(idx, side_to_move)
    

    def legal_moves_mask(self, fen):
        vector = np.zeros(4672, dtype=np.int8)
        board = chess.Board(fen)
        # side_to_move = fen.split()[1]
        side_to_move = "w" if board.turn else "b"

        for move in board.legal_moves:
            uci = move.uci()
            idx = np.argmax(self.best_move_one_hot(uci, side_to_move))
            vector[idx] = 1
        
        return vector

    def correct_castling_move(self, fen: str, move_uci: str) -> str:
        """
        Corrects incorrect castling UCI strings (like 'e1h1') into standard ones (like 'e1g1'),
        using only FEN castling rights for verification.
        """
        castling_rights = fen.split()[2]  # e.g., "KQkq"
        corrections = {
            "e1h1": ("K", "e1g1"),  # White king-side
            "e1a1": ("Q", "e1c1"),  # White queen-side
            "e8h8": ("k", "e8g8"),  # Black king-side
            "e8a8": ("q", "e8c8"),  # Black queen-side
        }

        required_flag, corrected_move = corrections.get(move_uci, (None, move_uci))

        if required_flag and required_flag in castling_rights:
            return corrected_move

        return move_uci

    def reformat(self, line):
        data = json.loads(line)

        fen = data.get("fen")
        best_move = data.get("best_move")

        if best_move in ["e1h1", "e1a1", "e8h8", "e8a8"]:
            best_move = self.correct_castling_move(fen, best_move)

        val = data.get("val")
        depth = data.get("depth")

        in_tensor, side_to_move = self.fen_to_tensor(fen)
        move_target = self.best_move_one_hot(best_move, side_to_move)
        val_target = np.float32(val)
        depth = np.float32(depth)
        moves_mask = self.legal_moves_mask(fen)

        return in_tensor, move_target, val_target, depth, moves_mask


    def append_block(self, file, in_tensor_block, move_target_block, val_target_block, depth_block, moves_mask_block):

        for name, block in [
            ("input", in_tensor_block),
            ("move_target", move_target_block),
            ("val_target", val_target_block),
            ("depth", depth_block),
            ("moves_mask", moves_mask_block)
        ]:
            dataset = file[name]
            old_len = dataset.shape[0]
            block_len = block.shape[0]
            new_len = old_len + block_len
            dataset.resize((new_len, ) + dataset.shape[1:])
            dataset[old_len:new_len, ...] = block


    def jsonl_to_h5_stream(self, in_path, out_path, desired_len, chunk_size=1000, start_line=0):

        with open(in_path, "r") as in_file, \
            h5py.File(out_path, "w") as out_file:
            
            out_file.create_dataset("input", (0, 18, 8, 8), dtype=np.float32, maxshape=(None, 18, 8, 8), chunks=(chunk_size, 18, 8, 8), compression="gzip")
            out_file.create_dataset("move_target", (0, 4672), dtype=np.int8, maxshape = (None, 4672), chunks = (chunk_size, 4672), compression="gzip")
            out_file.create_dataset("val_target", (0, ), dtype = np.float32, maxshape=(None, ), chunks=(chunk_size, ), compression="gzip")
            out_file.create_dataset("depth", (0, ), dtype=np.int8, maxshape=(None, ), chunks=(chunk_size, ), compression="gzip")
            out_file.create_dataset("moves_mask", (0, 4672), dtype=np.int8, maxshape = (None, 4672), chunks = (chunk_size, 4672), compression="gzip")


            in_tensor_list, move_target_list, val_target_list, depth_list, moves_mask_list = [], [], [], [], []
            line_num = 0
            set_len = 0

            for line in in_file:
                line_num += 1
                if line_num < start_line:
                    continue
                set_len += 1
                if set_len > desired_len:
                    break
                if (set_len-1)%10000 == 0:
                    print(f"{set_len-1} / {desired_len}")

                in_tensor, move_target, val_target, depth, moves_mask = self.reformat(line)





                in_tensor_list.append(in_tensor)
                move_target_list.append(move_target)
                val_target_list.append(val_target)
                depth_list.append(depth)
                moves_mask_list.append(moves_mask)

                if len(in_tensor_list) >= chunk_size:
                    self.append_block(
                        out_file,
                        np.asarray(in_tensor_list,    dtype=np.float32),
                        np.asarray(move_target_list,  dtype=np.int8),
                        np.asarray(val_target_list,   dtype=np.float32),
                        np.asarray(depth_list,        dtype=np.int16),
                        np.asarray(moves_mask_list,  dtype=np.int8)
                    )
                    in_tensor_list.clear()
                    move_target_list.clear()
                    val_target_list.clear()
                    depth_list.clear()
                    moves_mask_list.clear()
                
            if in_tensor_list:
                self.append_block(
                    out_file,
                    np.asarray(in_tensor_list,    dtype=np.float32),
                    np.asarray(move_target_list,  dtype=np.int8),
                    np.asarray(val_target_list,   dtype=np.float32),
                    np.asarray(depth_list,        dtype=np.int16),
                    np.asarray(moves_mask_list,  dtype=np.int8)
                )
                in_tensor_list.clear()
                move_target_list.clear()
                val_target_list.clear()
                depth_list.clear()
                moves_mask_list.clear()



if __name__ == "__main__":
    in_path = "src/chess2/bot/data/lichess_filtered.jsonl"
    out_path_training = "src/chess2/bot/data/training_data.h5"
    out_path_validation = "src/chess2/bot/data/validation_data.h5"
    out_path_testing = "src/chess2/bot/data/testing_data.h5"
    processor = TrainingSetProcessor()


    # processor.jsonl_to_h5_stream(in_path, out_path_training, 200_000, start_line=0)
    # processor.jsonl_to_h5_stream(in_path, out_path_validation, 50_000, start_line=200_000) 
    # processor.jsonl_to_h5_stream(in_path, out_path_testing, 200_000, start_line=250_000)


    # with h5py.File(out_path_testing, "r") as file:
    #     count = 0
    #     for i in range(file["input"].shape[0]):
    #         count += 1
    #         if count%10_000 == 0:
    #             print(file["depth"][i], "\n", "-----------------------------\n")
            
    #     print(count)
    

    # with h5py.File(out_path_training, "r") as file, open(in_path, "r") as jsonfile:
    #     for idx, line in enumerate(jsonfile):
    #         if idx > 1000:
    #             break
    #         move_vec = file["move_target"][idx]
    #         side_to_move = "w" if file["input"][idx, 12, 0, 0] == 1 else "b"
    #         predicted_move = processor.decode_policy_vector(move_vec, side_to_move)
    #         real_move = json.loads(line)["best_move"]
    #         print(real_move == predicted_move, f"        move: {real_move}   pred: {predicted_move}")


        # print(np.argmax(move_vec))



    # with h5py.File("src/chess2/bot/data/training_data.h5", "r") as file:
    #     idx = 2848
    #     move_vec = file["move_target"][idx]
    #     side_to_move = "w" if file["input"][idx, 12, 0, 0] == 1 else "b"
    #     predicted_move = processor.decode_policy_vector(move_vec, side_to_move)
    #     print(predicted_move)
    #     for i in range(18):
    #         print(file["input"][idx, i])



    with h5py.File(out_path_testing, "r") as file:
        move_mask = file["moves_mask"][:]
        move_pred = file["move_target"][:]
        in_tens = file["input"][:]

    counter = 0
    for idx in range(200000):
        move_mask_i = move_mask[idx]
        move_pred_i = move_pred[idx]
        side_to_move = "w" if in_tens[idx, 12, 0, 0] == 1 else "b"

        move_idx = np.argmax(move_pred_i)
        if move_mask_i[move_idx] == 0:
            print("\n", idx)
            print(move_idx)
            print(processor.decode_policy_vector(move_pred_i, side_to_move))
            counter += 1
        if idx % 1000 == 0:
            print(f"\n{idx}/200000")
            print(counter)

    print(counter)

    print(move_mask.shape[0])


        # test if shape of mask and move_tgt are the same