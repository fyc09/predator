import torch
import torch.nn as nn
import torch.nn.functional as F

from .encoder import NUM_CHANNELS

BOARD_SIZE = 11


class ResidualBlock(nn.Module):
    def __init__(self, channels):
        super().__init__()
        self.conv1 = nn.Conv2d(channels, channels, 3, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(channels)
        self.conv2 = nn.Conv2d(channels, channels, 3, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(channels)

    def forward(self, x):
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out = F.relu(out + x)
        return out


class PredatorNetwork(nn.Module):
    def __init__(self, num_blocks=6, channels=64):
        super().__init__()

        self.conv_input = nn.Conv2d(NUM_CHANNELS, channels, 3, padding=1, bias=False)
        self.bn_input = nn.BatchNorm2d(channels)

        self.blocks = nn.Sequential(*[
            ResidualBlock(channels) for _ in range(num_blocks)
        ])

        self.policy_conv = nn.Conv2d(channels, 32, 1, bias=False)
        self.policy_bn = nn.BatchNorm2d(32)
        self.policy_fc = nn.Linear(32 * BOARD_SIZE * BOARD_SIZE, BOARD_SIZE * BOARD_SIZE)

        self.value_conv = nn.Conv2d(channels, 32, 1, bias=False)
        self.value_bn = nn.BatchNorm2d(32)
        self.value_fc1 = nn.Linear(32 * BOARD_SIZE * BOARD_SIZE, 64)
        self.value_fc2 = nn.Linear(64, 1)

    def forward(self, x):
        x = F.relu(self.bn_input(self.conv_input(x)))
        x = self.blocks(x)

        policy = F.relu(self.policy_bn(self.policy_conv(x)))
        policy = policy.reshape(policy.size(0), -1)
        policy = self.policy_fc(policy)
        policy = F.log_softmax(policy, dim=1)

        value = F.relu(self.value_bn(self.value_conv(x)))
        value = value.reshape(value.size(0), -1)
        value = F.relu(self.value_fc1(value))
        value = torch.tanh(self.value_fc2(value))

        return policy, value

    @torch.no_grad()
    def predict(self, encoded, device="cpu"):
        tensor = torch.from_numpy(encoded).float().unsqueeze(0)
        tensor = tensor.permute(0, 3, 1, 2).contiguous().to(device)
        policy_log, value = self.forward(tensor)
        policy = torch.exp(policy_log).squeeze(0).cpu().numpy()
        value = value.squeeze().cpu().item()
        return policy, value

    def save(self, path):
        torch.save(self.state_dict(), path)

    def load(self, path, device="cpu"):
        self.load_state_dict(torch.load(path, map_location=device, weights_only=True))
