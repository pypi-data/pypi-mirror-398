# Copyright (c) . All rights reserved.

from mmyolo.models.backbones import YOLOv8CSPDarknet
from mmyolo.models.utils import make_divisible, make_round
from mmengine.registry import MODELS

from ..layers.yolo_bricks import C3K2, C2PSA, Conv, SPPF



@MODELS.register_module()
class YOLOv11CSPDarknet(YOLOv8CSPDarknet):
    """
    在YOLOv8 backbone基础上, 将csp layer换为C3K2, 最后再加上一个C2PSA
    """
    arch_settings = {
        'P5': [[64, 128, 2, 0.25, False, False], [128, 256, 2, 0.25, False, False],
               [256, 512, 2, 0.5, True, False], [512, None, 2, 0.5, True, True]],
    } # blocks different with v8

    def build_stage_layer(self, stage_idx: int, setting: list) -> list:
        """Build a stage layer.

        Args:
            stage_idx (int): The index of a stage layer.
            setting (list): The architecture setting of a stage layer.
        """
        in_channels, out_channels, num_blocks, expand_ratio, c3k, use_spp = setting

        in_channels = make_divisible(in_channels, self.widen_factor)
        out_channels = make_divisible(out_channels, self.widen_factor)
        num_blocks = make_round(num_blocks, self.deepen_factor)
        stage = []
        conv_layer = Conv(
            in_channels,
            out_channels,
            k=3,
            s=2)
        stage.append(conv_layer)
        csp_layer = C3K2(
            out_channels,
            out_channels,
            num_blocks=num_blocks,
            expand_ratio=expand_ratio,
            c3k=c3k)
        stage.append(csp_layer)
        if use_spp: # last stage
            spp = SPPF(
                out_channels,
                out_channels,
                k=5,)
            stage.append(spp)
            c2psa = C2PSA(out_channels, out_channels)  
            stage.append(c2psa)
        return stage