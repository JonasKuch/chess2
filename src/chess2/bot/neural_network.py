from torch import nn
import torch


'''
Input: piece planes (12×8×8) + flags broadcast to planes (5×8×8) = 17×8×8
  -> Conv3×3, `channels` filters, BN, ReLU
  -> [ Residual block × num_residual_blocks ]
       ├ Conv3×3, `channels`, BN, ReLU
       ├ Conv3×3, `channels`, BN
       └ Add -> ReLU
  -> Policy head:
       ├ Conv1×1, `policy_channels`, BN, ReLU
       ├ Flatten
       └ FC -> 1858 move logits

Design notes:
- Flags (4 castling + side-to-move) are broadcast to 8×8 input PLANES and fed in
  before the conv tower, so the convolutions can condition on whose turn it is
  and on castling rights (the old design only injected them at the FC layer,
  after all spatial reasoning was done).
- Capacity lives in the conv tower (deep/wide) rather than a huge FC head: the
  old head held ~6.7M of 7M params in FC(4677->1024->1858). Here a small 1×1
  policy conv reduces channels, then a single Linear maps to the 1858 moves.
'''


class ResidualBlock(nn.Module):
    def __init__(self, channels):
        super().__init__()
        # no biases is standard when followed by batchnorm
        self.conv1 = nn.Conv2d(channels, channels, kernel_size=3, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(channels)
        self.conv2 = nn.Conv2d(channels, channels, kernel_size=3, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(channels)
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x):
        identity = x

        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)

        out = self.conv2(out)
        out = self.bn2(out)

        out += identity
        out = self.relu(out)
        return out


class NeuralNetwork(nn.Module):
    def __init__(
        self,
        num_residual_blocks=10,
        channels=128,
        policy_channels=16,
        num_piece_planes=12,
        num_flags=5,
        num_moves=1858,
    ):
        super().__init__()
        self.num_flags = num_flags
        in_channels = num_piece_planes + num_flags  # piece planes + flag planes

        # Initial convolution of the input tensor
        self.initial_conv_block = nn.Sequential(
            nn.Conv2d(in_channels, channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(channels),
            nn.ReLU(inplace=True),
        )

        # Residual tower
        self.residual_layers = nn.Sequential(
            *[ResidualBlock(channels) for _ in range(num_residual_blocks)]
        )

        # Policy head: 1×1 conv reduces channels, then a single FC to the moves
        self.policy_head = nn.Sequential(
            nn.Conv2d(channels, policy_channels, kernel_size=1, bias=False),
            nn.BatchNorm2d(policy_channels),
            nn.ReLU(inplace=True),
            nn.Flatten(),
        )
        self.fc = nn.Linear(policy_channels * 8 * 8, num_moves)

    def forward(self, board, flags):
        # Broadcast each flag to a full 8×8 plane and stack onto the piece planes.
        h, w = board.shape[2], board.shape[3]
        flag_planes = flags[:, :, None, None].expand(-1, -1, h, w)
        x = torch.cat([board, flag_planes], dim=1)

        x = self.initial_conv_block(x)
        x = self.residual_layers(x)
        x = self.policy_head(x)
        x = self.fc(x)
        return x
