#!/usr/bin/env python3


"""
@author: xi
@since: 2023-11-27
"""

import json
import os.path
from dataclasses import field, dataclass, asdict
from typing import Sequence

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F
from torch.optim import AdamW
from tqdm import tqdm

import visioncube as cube

__all__ = [
    'LightSegment2dConfig',
    'LightSegment2d'
]


class Network(nn.Module):

    def __init__(
            self,
            num_classes: int,  # 2
            ch_hid: int,  # 16, 32, 64
            kernel_size: int,  # 5, 7
            num_layers: int,  # 3, 4, 5
    ) -> None:
        super().__init__()
        self.num_classes = num_classes
        self.ch_hid = ch_hid
        self.kernel_size = kernel_size
        self.num_layers = num_layers

        self.layers = nn.ModuleList()
        for i in range(num_layers):
            self.layers.append(nn.Sequential(
                nn.Conv2d(
                    3 if i == 0 else ch_hid,
                    ch_hid,
                    kernel_size=kernel_size,
                    stride=1 if i == 0 else 2,
                    padding=kernel_size // 2,
                    bias=False
                ),
                nn.GroupNorm(4, ch_hid),
                nn.SiLU(inplace=True),
            ))

        self.out_layer = nn.Conv2d(ch_hid, num_classes, kernel_size=1, stride=1, padding=0, bias=True)

    def forward(self, x: torch.Tensor):
        n, c, h, w = x.shape

        feat = None
        layer_in = x
        for layer in self.layers:
            layer_out = layer(layer_in)
            layer_out1 = F.interpolate(layer_out, (h, w), mode='nearest')
            feat = layer_out1 if feat is None else feat + layer_out1
            layer_in = layer_out
        feat = F.dropout(feat, 0.2, self.training, inplace=True)

        return self.out_layer(feat)


@dataclass
class LightSegment2dConfig:
    num_classes: int = field(default=2)
    ch_hid: int = field(default=16)
    kernel_size: int = field(default=5)
    num_layers: int = field(default=4)
    morph_open_size: int = field(default=11)
    class_weight: Sequence[float] = field(default=None)
    max_lr: float = field(default=1e-3)
    weight_decay: float = field(default=0.3)
    num_epochs: int = field(default=300)
    device: str = field(default=None)


class LightSegment2d(nn.Module):

    def __init__(self, config: LightSegment2dConfig):
        super().__init__()
        self.config = config

        self.network = Network(
            num_classes=self.config.num_classes,
            ch_hid=self.config.ch_hid,
            kernel_size=self.config.kernel_size,
            num_layers=self.config.num_layers
        )
        self.network.to(self.config.device)
        self.network.eval()

    def forward(self, image: np.ndarray, label: np.ndarray = None) -> np.ndarray:
        return self.inference(image) if label is None else self.update(image, label)

    def _image_to_tensor(self, image: np.ndarray) -> torch.Tensor:
        x = cube.normalize_image(image, transpose=True)
        x = torch.tensor(x, device=self.config.device)
        return x

    def _label_to_tensor(self, label: np.ndarray) -> torch.Tensor:
        return torch.tensor(label, dtype=torch.long, device=self.config.device)

    @torch.no_grad()
    def inference(self, image: np.ndarray) -> np.ndarray:
        x = self._image_to_tensor(image)
        output = self.network(x[None, ...])[0]  # (c, h, w)
        mask = output.argmax(0)  # (h, w)
        mask = mask.cpu().numpy().astype(np.uint8)
        mask = cube.morph_open(mask, kernel=self.config.morph_open_size, iterations=3)
        return mask

    def update(self, image: np.ndarray, label: np.ndarray):
        if isinstance(image, (list, tuple)):
            x_list, target_list = [], []
            for image_i, label_i in zip(image, label):
                x_list.append(self._image_to_tensor(image_i))
                target_list.append(self._label_to_tensor(label_i))
            x = torch.stack(x_list)
            target = torch.stack(target_list)
        else:
            x = self._image_to_tensor(image)[None, ...]
            target = self._label_to_tensor(label)[None, ...]

        self.network.train()
        optimizer = AdamW(
            [*self.network.parameters()],
            lr=self.config.max_lr,
            betas=(0.93, 0.999),
            weight_decay=self.config.weight_decay
        )
        num_loops = self.config.num_epochs
        lr_decay = self.config.max_lr / num_loops
        loop = tqdm(range(num_loops), dynamic_ncols=True)
        for i in loop:
            output = self.network(x)  # (n, c, h, w)
            loss = F.cross_entropy(
                output,
                target,
                weight=torch.tensor(
                    self.config.class_weight,
                    device=output.device
                ) if self.config.class_weight else None
            )
            loss.backward()
            optimizer.step()
            optimizer.zero_grad(set_to_none=True)
            optimizer.param_groups[0]['lr'] = self.config.max_lr - i * lr_decay
            loop.set_description(f'L={float(loss):.06f}', False)
        self.network.eval()

    @staticmethod
    def from_pretrained(path: str, device=None):
        assert os.path.isdir(path)
        with open(os.path.join(path, 'config.json'), 'r') as f:
            config = LightSegment2dConfig(**json.load(f))
        config.device = device
        model = LightSegment2d(config)
        state_dict = torch.load(os.path.join(path, 'model.pth'), map_location='cpu')
        model.load_state_dict(state_dict)
        return model

    def save_pretrained(self, path: str):
        os.makedirs(path, exist_ok=True)
        assert os.path.isdir(path)
        with open(os.path.join(path, 'config.json'), 'w') as f:
            json.dump(asdict(self.config), f, indent=4)
        torch.save(self.state_dict(), os.path.join(path, 'model.pth'))
