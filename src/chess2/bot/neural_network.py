from torch import nn
import torch 


'''
Input: 8×8×12
→ Conv3×3, 64 filters, stride 1, BN, ReLU
→ [ Residual block  × 4 ]
     ├ Conv3×3, 64 filters, BN, ReLU
     ├ Conv3×3, 64 filters, BN
     └ Add → ReLU
→ Policy head:
     ├ Conv1×1, 73 filters, BN, ReLU
     ├ Flatten + Flags
     └ FC (1024, 1858) → Softmax(1858)
'''


class ResidualBlock(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(
            in_channels=64,
            out_channels=64,
            kernel_size=3,
            stride=1,
            padding=1,
            bias=False # no biases is standart when followed by batchnorm
        )
        self.bn1= nn.BatchNorm2d(
            num_features=64
        )
        self.conv2 = nn.Conv2d(
            in_channels=64,
            out_channels=64,
            kernel_size=3,
            stride=1,
            padding=1,
            bias=False
        )
        self.bn2= nn.BatchNorm2d(
            num_features=64
        )
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
    def __init__(self, num_residual_blocks=4):
        super().__init__()

        # Initial Convolition of the Input Tensors
        self.initial_conv_block = nn.Sequential(
            nn.Conv2d(
                in_channels=12,
                out_channels=64,
                kernel_size=3,
                stride=1,
                padding=1,
                bias=False
            ),
            nn.BatchNorm2d(
                num_features=64
            ),
            nn.ReLU(inplace=True)
        )


        # Residual Blocks
        blocks = []

        for _ in range(num_residual_blocks):
            blocks.append(ResidualBlock())
        
        self.residual_layers = nn.Sequential(*blocks)

        
        # Policy Head
        self.policy_head = nn.Sequential(
            nn.Conv2d(
                in_channels=64,
                out_channels=73,
                kernel_size=1,
                stride=1,
                bias=False
            ),
            nn.BatchNorm2d(
                num_features=73
            ),
            nn.ReLU(inplace=True),
            nn.Flatten()
        )

        self.fc_layers = nn.Sequential(
            nn.Linear(4677, 1024),
            nn.ReLU(inplace=True),
            nn.Linear(1024, 1858)
        )

    def forward(self, board, flags):
        out = self.initial_conv_block(board)
        out = self.residual_layers(out)
        out = self.policy_head(out)
        out = torch.cat([out, flags], dim=1)
        out = self.fc_layers(out)
        return out


