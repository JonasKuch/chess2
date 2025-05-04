import orjson as json
import zstandard as zstd
from multiprocessing import Pool, cpu_count
import numpy as np
import matplotlib.pyplot as plt



def filter_positions(args):
    line, min_depth = args

    data = json.loads(line.decode("utf-8"))
    
    fen = data.get("fen")

    candidates = []

    for ev in data.get("evals", []):
        depth = ev.get("depth", 0)

        if depth < min_depth:
            continue
        
        pvs = ev.get("pvs", [{}])
        pvs_candidates = []
        for var in pvs:
            cp = var.get("cp")

            if cp is None:
                mate = var.get("mate")
                if mate is None:
                    continue
                side_to_move = fen.split()[1]
                validation = float(np.sign(mate) if side_to_move == "w" else -np.sign(mate))
            
            else:
                validation = float(np.tanh(cp/400))

            line_str = var.get("line","")
            best_move = line_str.split()[0] if line_str else None
            if best_move:
                pvs_candidates.append((validation, best_move))
        
        if not pvs_candidates:
            continue

        val, move = max(pvs_candidates, key=lambda x: x[0])
        candidates.append((depth, val, move))
    
    if not candidates:
        return None
    
    best_depth, best_val, best_move = max(candidates, key=lambda x: x[0])
    out = {"fen":fen, "val":best_val, "best_move":best_move, "depth":best_depth}

    return json.dumps(out).decode("utf-8")


def stream(in_path, out_path, min_depth, workers, desired_data):
    zst_decompressor = zstd.ZstdDecompressor()
    pool = Pool(workers)

    with open(in_path, "rb") as in_file, \
         zst_decompressor.stream_reader(in_file) as reader, \
         open(out_path, "w") as out_file:
        
        CHUNK_SIZE = 256 * 1024
        buffer = b""
        tasks = []

        data_len = 0
        while True:
            chunk = reader.read(CHUNK_SIZE)
            if not chunk:
                break
            buffer += chunk
            *lines, buffer = buffer.split(b"\n")

            for raw_line in lines:
                tasks.append((raw_line, min_depth))
            
            if len(tasks) >= workers*10:
                for res in pool.imap_unordered(filter_positions, tasks, chunksize=workers):
                    if res:
                        out_file.write(res + "\n")
                        data_len += 1
                        if data_len >= desired_data:
                            pool.close()
                            pool.join()
                            return
                tasks.clear()
        
        if buffer:
            leftover_lines = buffer.split(b"\n")
            for raw_line in leftover_lines:
                if raw_line:
                    tasks.append((raw_line, min_depth))

            for res in pool.imap_unordered(filter_positions, tasks, chunksize=workers):
                if res:
                    out_file.write(res + "\n")
                    data_len += 1
                    if data_len >= desired_data:
                        pool.close()
                        pool.join()
                        return

            tasks.clear()
        
    pool.close()
    pool.join()


if __name__ == "__main__":
    in_path = "src/chess2/bot/data/lichess_db_eval.jsonl.zst"
    out_path = "src/chess2/bot/data/lichess_filtered.jsonl"
    min_depth = 20
    workers = cpu_count()
    desired_data = 3_000_000

    stream(in_path=in_path, out_path=out_path, min_depth=min_depth, workers=workers, desired_data=desired_data)




    # with open(out_path, "r") as file:
    #     num = 0
    #     val_list = []
    #     for line in file:
    #         data = json.loads(line)
    #         val = data.get("val")
    #         val_list.append(val)
    #         num += 1
    #         if num > 100_000:
    #             break

    # plt.hist(val_list, bins=100)
    # plt.yscale("log")
    # plt.show()
    # print(np.mean(val_list))
