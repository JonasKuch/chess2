import orjson as json
import numpy as np
from multiprocessing import Pool, cpu_count
import warnings

# rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1

class TrainingSetProcessor:

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


    def best_move_one_hot(self, best_move):
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


    def index_to_uci(self, idx: int) -> str:
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

        # split into move_type (0–72) and from-square (0–63)
        move_type = idx // 64
        from_sq   = idx % 64
        fx = from_sq % 8
        fy = from_sq // 8

        # default: no promotion
        promo = ""

        # sliding moves
        if move_type < 56:
            dir_idx  = move_type // 7
            distance = (move_type % 7) + 1
            dx, dy = _SLIDE_DIRS[dir_idx]
            tx = fx + dx * distance
            ty = fy + dy * distance

        # knight moves
        elif move_type < 64:
            k_idx = move_type - 56
            dx, dy = _KNIGHT_DIRS[k_idx]
            tx = fx + dx
            ty = fy + dy

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
            ty = fy + dy
            promo = {0:'n',1:'n',2:'n', 3:'b',4:'b',5:'b', 6:'r',7:'r',8:'r'}[up]

        # convert coords back to UCI
        def square(x,y):
            return _FILE_LETTERS[x] + _RANK_LETTERS[y]

        return square(fx, fy) + square(tx, ty) + promo


    def decode_policy_vector(self, vec):
        """
        Given a length-4672 policy vector (logits or probs or one-hot),
        pick the highest entry and return its UCI move.
        """
        idx = int(np.argmax(vec))
        return self.index_to_uci(idx)


    def reformat(self, line):
        data = json.loads(line)

        fen = data.get("fen")
        best_move = data.get("best_move")
        val = data.get("val")
        depth = data.get("depth")

        in_tensor = self.fen_to_tensor(fen)
        move_target = self.best_move_one_hot(best_move)
        val_target = np.float32(val)
        depth = np.float32(depth)

        return in_tensor, move_target, val_target, depth


    def jsonl_to_npz_stream(self, in_path, out_path, filename, desired_len, file_size=10000, start_line=0):

        files_total = desired_len // file_size
        real_len = files_total*file_size
        if real_len != desired_len:
            warnings.warn(
                f"The desired dataset length is {desired_len}, but only {real_len} possible with file size {file_size}",
                category=UserWarning,
                stacklevel=2
            )

        with open(in_path, "r") as in_file:

            in_tensor_list, move_target_list, val_target_list, depth_list = [], [], [], []
            line_num = 0
            set_len = 0
            file_num = 0

            for line in in_file:
                line_num += 1
                if line_num < start_line:
                    continue
                set_len += 1
                if set_len > desired_len:
                    break
                if set_len % 100000 == 0:
                    print(f"Processed {set_len}/{desired_len} lines...")

                in_tensor, move_target, val_target, depth = self.reformat(line)

                in_tensor_list.append(in_tensor)
                move_target_list.append(move_target)
                val_target_list.append(val_target)
                depth_list.append(depth)

                if len(in_tensor_list) >= file_size:
                    np.savez_compressed(
                        f"{out_path}/{filename}_{file_num}.npz",
                        input=np.asarray(in_tensor_list,          dtype=np.float32),
                        move_target=np.asarray(move_target_list,  dtype=np.int8),
                        val_target=np.asarray(val_target_list,    dtype=np.float32),
                        depth=np.asarray(depth_list,              dtype=np.int16)
                    )
                        
                    file_num += 1

                    in_tensor_list, move_target_list, val_target_list, depth_list = [], [], [], []

            # To make every file the same length this following part is commented out
                
            # if in_tensor_list:
            #     np.savez_compressed(
            #         f"{out_path}/{filename}_{file_num}.npz",
            #         input=np.asarray(in_tensor_list,          dtype=np.float32),
            #         move_target=np.asarray(move_target_list,  dtype=np.int8),
            #         val_target=np.asarray(val_target_list,    dtype=np.float32),
            #         depth=np.asarray(depth_list,              dtype=np.int16)
            #     )
                    
            #     file_num += 1

            #     in_tensor_list, move_target_list, val_target_list, depth_list = [], [], [], []


if __name__ == "__main__":
    in_path = "src/chess2/bot/data/lichess_filtered.jsonl"
    out_path_training = "src/chess2/bot/data/train"
    out_path_validation = "src/chess2/bot/data/validation"
    out_path_testing = "src/chess2/bot/data/test"
    processor = TrainingSetProcessor()


    # processor.jsonl_to_npz_stream(in_path, out_path_training, "train", 2_000_000, start_line=0)
    # processor.jsonl_to_npz_stream(in_path, out_path_validation, "val", 200_000, start_line=2_000_000)
    # processor.jsonl_to_npz_stream(in_path, out_path_testing, "test", 200_000, start_line=2_200_000)


    # with np.load(out_path_training+"/train_0.npz", "r") as file:
    #     print(type(file))
    #     count = 0
    #     for i in range(file["input"].shape[0]):
    #         count += 1
    #         if count%10_000 == 0:
    #             print(file["depth"][i], "\n", "-----------------------------\n")
            
    #     print(count)

    from glob import glob

    print(len(glob("src/chess2/bot/data/train/*.npz")))