import orjson as json
import zstandard as zstd
from multiprocessing import Pool, cpu_count


def filter_positions(args):
    line, min_depth = args

    data = json.loads(line)
    
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
                continue
            line_str = var.get("line","")
            best_move = line_str.split()[0] if line_str else None
            if best_move:
                pvs_candidates.append((cp, best_move))
        
        if not pvs_candidates:
            continue

        cp_val, move = max(pvs_candidates, key=lambda x: x[0])
        candidates.append((depth, cp_val, move))
    
    if not candidates:
        return None
    
    best_depth, best_cp, best_move = max(candidates, key=lambda x: x[0])
    out = {"fen":fen, "cp":best_cp, "best_move":best_move, "depth":best_depth}

    return json.dumps(out).decode("utf-8")


def stream(in_path, out_path, min_depth, workers):
    zst_decompressor = zstd.ZstdDecompressor()
    pool = Pool(workers)

    with open(in_path, "rb") as in_file, \
         zst_decompressor.stream_reader(in_file) as reader, \
         open(out_path, "w") as out_file:
        
        CHUNK_SIZE = 256 * 1024
        buffer = b""
        tasks = []

        while True:
            chunk = reader.read(CHUNK_SIZE)
            if not chunk:
                break
            buffer += chunk
            *lines, buffer = buffer.split(b"\n")

            for raw_line in lines:
                tasks.append((raw_line, min_depth))
            
            if len(tasks) >= workers*10:
                for res in pool.map(filter_positions, tasks):
                    if res:
                        out_file.write(res + "\n")
                tasks.clear()
        
        if buffer:
            tasks.append((buffer.decode("utf-8"), min_depth))
            for res in pool.map(filter_positions, tasks):
                if res:
                    out_file.write(res + "\n")
            tasks.clear()
        
    pool.close()
    pool.join()


if __name__ == "__main__":
    in_path = "src/chess2/bot/data/lichess_db_eval.jsonl.zst"
    out_path = "src/chess2/bot/data/lichess_filtered.jsonl"
    min_depth = 34
    workers = 6

    stream(in_path=in_path, out_path=out_path, min_depth=min_depth, workers=workers)