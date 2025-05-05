from torch import nn


'''
Input: 8×8×18
→ Conv3×3, 64 filters, stride 1, BN, ReLU
→ [ Residual block  × 4 ]    ← very small!
     ├ Conv3×3, 64 filters, BN, ReLU
     ├ Conv3×3, 64 filters, BN
     └ Add → ReLU
→ Policy head:
     ├ Conv1×1, 73 filters, BN, ReLU
     └ Flatten → Softmax(4672)
→ Value head:
     ├ Conv1×1, 1 filter, BN, ReLU
     ├ FC 128, ReLU
     └ FC 1, tanh → v
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
                in_channels=18,
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
            nn.Flatten(),
            nn.Softmax()
        )


        # Value Head
        self.value_head = nn.Sequential(
            nn.Conv2d(
                in_channels=64,
                out_channels=1,
                kernel_size=1,
                stride=1,
                bias=False
            ),
            nn.BatchNorm2d(
                num_features=1
            ),
            nn.ReLU(inplace=True),
            nn.Flatten(),
            nn.Linear(
                in_features=64,
                out_features=128
            ),
            nn.Linear(
                in_features=128,
                out_features=1
            ),
            nn.Tanh()
        )


    def forward(self, x):
        x = self.initial_conv_block(x)
        x = self.residual_layers(x)
        out1 = self.policy_head(x)
        out2 = self.value_head(x)
        return out1, out2

