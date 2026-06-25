"""
Standalone regeneration of the training pickle from the raw Leela ccrl-v3 archive.

Produces a list of (planes, flags, label) tuples and dumps it to
chess_data_list.pkl.

Performance: records are parsed with a single vectorized ``np.frombuffer`` over
each decompressed .gz member rather than a per-record ``struct.unpack``. The
per-record unpack built a ~1971-element Python tuple each time and dominated
runtime (~70s for 1M); the vectorized parse does the same work in C in ~5s.
Decompression itself is cheap (~6s for 1M) and sequential, so multiprocessing
would only add IPC overhead here.

Key correctness detail (see plan / git history): the Leela plane order is
[P,N,B,R,Q,K] but the model expects [P,N,B,R,K,Q]. The K/Q swap (planes 4<->5
and 10<->11) is therefore applied to EVERY record, not just side_to_move==1.

Run from the repo root:
    .venv/bin/python -m chess2.bot.regenerate_dataset
"""

import os
import sys
import gzip
import tarfile
import time

import joblib
import numpy as np

ARCHIVE = os.path.join(os.path.dirname(__file__), "data_leela", "ccrl-v3.tar.bz2")
OUT_PATH = os.path.join(os.path.dirname(__file__), "data_leela", "chess_data_list.pkl")
NUM_RECORDS = 2_500_000
RECORD_SIZE = 8276

# Packed binary layout of a v3 record (matches struct '<I 1858f 104Q 7B b').
RECORD_DTYPE = np.dtype([
    ("version", "<u4"),
    ("probs",   "<f4", (1858,)),
    ("planes",  "<u8", (104,)),
    # 7 uint8: us_ooo, us_oo, them_ooo, them_oo, side, rule50, move_count
    ("cast",    "u1",  (7,)),
    ("result",  "i1"),
])
assert RECORD_DTYPE.itemsize == RECORD_SIZE


def build(num_records=NUM_RECORDS, archive=ARCHIVE, out_path=OUT_PATH):
    print(f"Reading up to {num_records:,} records from {archive}", flush=True)
    data_list = []
    cnt = 0
    start = time.time()

    with tarfile.open(archive, "r:bz2") as tar:
        for member in tar:
            if not member.isfile() or not member.name.endswith(".gz"):
                continue
            stream = tar.extractfile(member)
            if stream is None:
                continue

            buf = gzip.decompress(stream.read())
            k = len(buf) // RECORD_SIZE
            arr = np.frombuffer(buf[:k * RECORD_SIZE], dtype=RECORD_DTYPE)

            labels = arr["probs"].argmax(axis=1).astype(np.int64)

            planes = arr["planes"][:, :12].copy()  # own + opp [P,N,B,R,Q,K]
            # Convert Leela order [P,N,B,R,Q,K] -> model order [P,N,B,R,K,Q].
            # Fixed reordering, NOT side-dependent: apply to every record.
            planes[:, [4, 5]] = planes[:, [5, 4]]
            planes[:, [10, 11]] = planes[:, [11, 10]]

            # flags = [us_ooo, us_oo, them_ooo, them_oo, side]
            flags = arr["cast"][:, :5].astype(np.int8).copy()

            # game result from the side-to-move's perspective (-1 / 0 / +1),
            # used as the value-head target
            results = arr["result"].astype(np.int8)

            data_list.extend(zip(planes, flags, labels.tolist(), results.tolist()))
            cnt += k

            if cnt >= num_records:
                break

    data_list = data_list[:num_records]
    print(f"Collected {len(data_list):,} records in {time.time() - start:.1f}s", flush=True)

    # quick sanity check before dumping
    labels = np.array([d[2] for d in data_list])
    results = np.array([d[3] for d in data_list])
    rvals, rcounts = np.unique(results, return_counts=True)
    print(f"Sanity: frac label==0 = {(labels == 0).mean():.4f}, "
          f"distinct labels = {len(np.unique(labels))}", flush=True)
    print(f"Sanity: result distribution = {dict(zip(rvals.tolist(), rcounts.tolist()))}", flush=True)

    print(f"Dumping to {out_path} ...", flush=True)
    joblib.dump(data_list, out_path, compress=3)
    print("Done.", flush=True)


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else NUM_RECORDS
    build(num_records=n)
