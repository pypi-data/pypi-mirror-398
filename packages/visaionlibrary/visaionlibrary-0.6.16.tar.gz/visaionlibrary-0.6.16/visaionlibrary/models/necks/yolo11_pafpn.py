from ..layers.yolo_bricks import C3K2
from mmyolo.models.necks import YOLOv8PAFPN
from mmyolo.models.utils import make_divisible, make_round
from mmengine.registry import MODELS

@MODELS.register_module()
class YOLO11PAFPN(YOLOv8PAFPN):
    def __init__(self,
                 in_channels: List[int],
                 out_channels: Union[List[int], int],
                 deepen_factor: float = 1.0,
                 widen_factor: float = 1.0,
                 num_csp_blocks: int = 2,
                 freeze_all: bool = False,
                 norm_cfg: ConfigType = dict(
                     type='BN', momentum=0.03, eps=0.001),
                 act_cfg: ConfigType = dict(type='SiLU', inplace=True),
                 init_cfg: OptMultiConfig = None):
        super().__init__(
            in_channels=in_channels,
            out_channels=out_channels,
            deepen_factor=deepen_factor,
            widen_factor=widen_factor,
            num_csp_blocks=num_csp_blocks,
            freeze_all=freeze_all,
            norm_cfg=norm_cfg,
            act_cfg=act_cfg,
            init_cfg=init_cfg)

    def build_top_down_layer(self, idx: int) -> nn.Module:
        
        return C3K2(
            make_divisible((self.in_channels[idx - 1] + self.in_channels[idx]),
                           self.widen_factor),
            make_divisible(self.out_channels[idx - 1], self.widen_factor),
            num_blocks=make_round(self.num_csp_blocks, self.deepen_factor),
            c3k=False,
            add_identity=False,
        )

    def build_bottom_up_layer(self, idx: int) -> nn.Module:
        if idx == 1:
            c3k = True
        else:
            c3k = False
        return C3K2(
            make_divisible((self.in_channels[idx - 1] + self.in_channels[idx]),
                           self.widen_factor),
            make_divisible(self.out_channels[idx - 1], self.widen_factor),
            num_blocks=make_round(self.num_csp_blocks, self.deepen_factor),
            c3k=c3k,
            add_identity=False,
        )