"""
Training script for the chess move-prediction policy net.

Replaces the stale src/chess2/bot/training.py (which still called the removed
value head). Edit the CONFIG block, run, read the per-epoch top-1/top-5, then
change ONE knob and rerun. Checkpoints are named after the config so a given
.pth is traceable to the settings that produced it.

Run from the repo root:
    .venv/bin/python -m chess2.bot.train
or directly:
    .venv/bin/python src/chess2/bot/train.py
"""

import os
import time

import joblib
import numpy as np
import torch
from torch import nn
from torch.nn.utils import clip_grad_norm_

from chess2.bot import NeuralNetwork

# --------------------------------------------------------------------------- #
# CONFIG
# --------------------------------------------------------------------------- #
DATA_PATH = os.path.join(os.path.dirname(__file__), "data_leela", "chess_data_list.pkl")
SAVE_DIR = os.path.join(os.path.dirname(__file__), "saved_models")

# Contiguous split. CCRL records are sequential by game, so slicing by index
# keeps whole games out of validation. Do NOT shuffle the raw list before
# splitting -- that leaks positions from the same game into val.
TRAIN_RANGE = (0, 900_000)
VAL_RANGE = (900_000, 1_000_000)

DEVICE = "mps"           # Apple Silicon GPU; falls back to cpu if unavailable
OPTIMIZER = "adamw"      # "sgd" (Leela/AlphaZero style) or "adamw" (faster convergence)

BATCH_SIZE = 256         # 64 was tiny; 256-512 keeps the MPS GPU fed
EPOCHS = 20
WEIGHT_DECAY = 1e-4
GRAD_CLIP = 1.0          # max_norm; good hygiene, keep it

# Learning rate. Linear scaling rule: lr scales with batch size. The old run
# used 1e-3 @ batch 64, so ~4e-3 @ batch 256 for SGD. Adam is far less
# batch-size sensitive, so 1e-3 is fine there regardless of batch.
SGD_LR = 4e-3
ADAMW_LR = 1e-3

# Architecture. Capacity now lives in the conv tower, not a huge FC head; flags
# are fed as input planes (handled inside the model).
NUM_RESIDUAL_BLOCKS = 6
CHANNELS = 96            # tower width
POLICY_CHANNELS = 16     # 1×1 policy-head width; keeps the final FC small


# --------------------------------------------------------------------------- #
# SETUP
# --------------------------------------------------------------------------- #
def get_device(name):
    if name == "mps" and torch.backends.mps.is_available():
        return torch.device("mps")
    if name == "cuda" and torch.cuda.is_available():
        return torch.device("cuda")
    if name != "cpu":
        print(f"[warn] device '{name}' unavailable, falling back to cpu")
    return torch.device("cpu")


def load_decoded(path):
    """Load the pickle and decode every position ONCE (vectorized).

    The old DataLoader path re-decoded 12 bitboards per sample on every access,
    every epoch (~34s/epoch, single-threaded), starving the GPU. Here we do the
    whole decode in one numpy pass (~1s) and return resident tensors:
        boards uint8 (N,12,8,8), flags float32 (N,5), labels int64 (N,)
    Stored as uint8 (~768 MB for 1M) and cast to float per-batch on-device.
    """
    raw = joblib.load(path)
    n = len(raw)

    bb = np.stack([np.asarray(p, dtype=np.uint64) for p, _, _ in raw])  # (N,12)
    bits = np.unpackbits(bb.view(np.uint8).reshape(-1, 8), axis=1)      # per-bitboard bits
    boards = np.flip(bits.reshape(n, 12, 8, 8), axis=(2, 3)).copy()     # matches bitboard_to_matrix

    flags = np.stack([np.asarray(f, dtype=np.float32) for _, f, _ in raw])
    labels = np.array([lbl for _, _, lbl in raw], dtype=np.int64)

    return (
        torch.from_numpy(boards),                 # uint8
        torch.from_numpy(flags),                  # float32
        torch.from_numpy(labels),                 # int64
    )


def iter_batches(n, batch_size, device, shuffle):
    idx = torch.randperm(n, device=device) if shuffle else torch.arange(n, device=device)
    for i in range(0, n, batch_size):
        yield idx[i:i + batch_size]


def build_optimizer(model):
    if OPTIMIZER == "sgd":
        return SGD_LR, torch.optim.SGD(
            model.parameters(),
            lr=SGD_LR,
            momentum=0.9,
            nesterov=True,
            weight_decay=WEIGHT_DECAY,
        )
    if OPTIMIZER == "adamw":
        return ADAMW_LR, torch.optim.AdamW(
            model.parameters(),
            lr=ADAMW_LR,
            weight_decay=WEIGHT_DECAY,
        )
    raise ValueError(f"unknown OPTIMIZER: {OPTIMIZER!r}")


# --------------------------------------------------------------------------- #
# TRAIN / VAL LOOPS
# --------------------------------------------------------------------------- #
def train_loop(boards, flags, labels, model, loss_fn, optimizer, device):
    model.train()
    n = boards.shape[0]
    running = 0.0
    nb = 0

    for b, bidx in enumerate(iter_batches(n, BATCH_SIZE, device, shuffle=True)):
        xb = boards[bidx].float()       # uint8 -> float on-device, no host copy
        fb = flags[bidx]
        yb = labels[bidx]

        logits = model(xb, fb)
        loss = loss_fn(logits, yb)

        optimizer.zero_grad()
        loss.backward()
        clip_grad_norm_(model.parameters(), max_norm=GRAD_CLIP)
        optimizer.step()

        running += loss.item()
        nb += 1
        if b % 200 == 0:
            print(f"  loss: {loss.item():>7f}  [{b*BATCH_SIZE:>6d}/{n:>6d}]", flush=True)

    return running / nb


@torch.no_grad()
def validation_loop(boards, flags, labels, model, loss_fn, device):
    model.eval()
    n = boards.shape[0]
    val_loss = 0.0
    top1 = 0
    top5 = 0
    nb = 0

    for bidx in iter_batches(n, BATCH_SIZE, device, shuffle=False):
        xb = boards[bidx].float()
        logits = model(xb, flags[bidx])
        yb = labels[bidx]

        val_loss += loss_fn(logits, yb).item()
        nb += 1
        top1 += (logits.argmax(dim=1) == yb).sum().item()
        top5_idx = logits.topk(5, dim=1).indices
        top5 += (top5_idx == yb.unsqueeze(1)).any(dim=1).sum().item()

    val_loss /= nb
    print(f"  val loss: {val_loss:>7f} | top-1: {100*top1/n:>4.1f}% | "
          f"top-5: {100*top5/n:>4.1f}%", flush=True)
    return val_loss, top1 / n


# --------------------------------------------------------------------------- #
# MAIN
# --------------------------------------------------------------------------- #
def main():
    device = get_device(DEVICE)
    print(f"device: {device} | optimizer: {OPTIMIZER} | batch: {BATCH_SIZE} | "
          f"epochs: {EPOCHS}", flush=True)

    # Decode the whole dataset once, then keep it resident on the device so the
    # training loop is pure GPU work (no per-sample decode, no host->device copy).
    t0 = time.time()
    boards, flags, labels = load_decoded(DATA_PATH)
    boards, flags, labels = boards.to(device), flags.to(device), labels.to(device)
    tr0, tr1 = TRAIN_RANGE
    va0, va1 = VAL_RANGE
    tr_b, tr_f, tr_y = boards[tr0:tr1], flags[tr0:tr1], labels[tr0:tr1]
    va_b, va_f, va_y = boards[va0:va1], flags[va0:va1], labels[va0:va1]
    mem = boards.element_size() * boards.nelement() / 1e6
    print(f"decoded {boards.shape[0]:,} positions in {time.time()-t0:.1f}s "
          f"({mem:.0f} MB on {device}) | train: {tr_b.shape[0]:,} | val: {va_b.shape[0]:,}",
          flush=True)

    model = NeuralNetwork(
        num_residual_blocks=NUM_RESIDUAL_BLOCKS,
        channels=CHANNELS,
        policy_channels=POLICY_CHANNELS,
    ).to(device)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"model: {NUM_RESIDUAL_BLOCKS} blocks x {CHANNELS}ch | "
          f"{n_params/1e6:.1f}M params", flush=True)
    loss_fn = nn.CrossEntropyLoss()
    lr, optimizer = build_optimizer(model)

    # Cosine decay over the whole run -- reliable for a fixed epoch budget,
    # unlike the plateau scheduler that never fired on the broken data.
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)

    os.makedirs(SAVE_DIR, exist_ok=True)
    tag = f"{OPTIMIZER}_b{BATCH_SIZE}_e{EPOCHS}_lr{lr:g}_rb{NUM_RESIDUAL_BLOCKS}_c{CHANNELS}"
    best_path = os.path.join(SAVE_DIR, f"model_{tag}_best.pth")
    last_path = os.path.join(SAVE_DIR, f"model_{tag}_last.pth")
    best_top1 = 0.0

    for epoch in range(1, EPOCHS + 1):
        t0 = time.time()
        print(f"\nEpoch {epoch}/{EPOCHS}  (lr={optimizer.param_groups[0]['lr']:.2e})\n"
              f"-------------------------------", flush=True)

        train_loss = train_loop(tr_b, tr_f, tr_y, model, loss_fn, optimizer, device)
        val_loss, val_top1 = validation_loop(va_b, va_f, va_y, model, loss_fn, device)
        scheduler.step()

        torch.save(model.state_dict(), last_path)
        if val_top1 > best_top1:
            best_top1 = val_top1
            torch.save(model.state_dict(), best_path)
            print(f"  ** new best top-1: {100*best_top1:.1f}% -> saved {best_path}", flush=True)

        print(f"  train loss: {train_loss:.4f} | {time.time()-t0:.0f}s", flush=True)

    print(f"\nDone. Best val top-1: {100*best_top1:.1f}%", flush=True)
    print(f"Best checkpoint: {best_path}", flush=True)
    print("Point MoveGenerator / game.py at that path to play-test it.", flush=True)


if __name__ == "__main__":
    main()
