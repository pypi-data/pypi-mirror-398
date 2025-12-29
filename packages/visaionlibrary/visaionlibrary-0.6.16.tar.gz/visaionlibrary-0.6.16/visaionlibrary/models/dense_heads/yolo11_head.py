
from ..layers.yolo_bricks import DWConv, Conv
from mmyolo.models.dense_heads.yolov8_head import YOLOv8Head
from mmengine.registry import MODELS

@MODELS.register_module()
class YOLO11Head(YOLOv8Head):
    def _init_layers(self):
        """initialize conv layers in YOLOv8 head."""
        # Init decouple head
        self.cls_preds = nn.ModuleList()
        self.reg_preds = nn.ModuleList()

        reg_out_channels = max(
            (16, self.in_channels[0] // 4, self.reg_max * 4))
        cls_out_channels = max(self.in_channels[0], self.num_classes)

        for i in range(self.num_levels):
            self.reg_preds.append(
                nn.Sequential(
                    ConvModule(
                        in_channels=self.in_channels[i],
                        out_channels=reg_out_channels,
                        kernel_size=3,
                        stride=1,
                        padding=1,
                        norm_cfg=self.norm_cfg,
                        act_cfg=self.act_cfg),
                    ConvModule(
                        in_channels=reg_out_channels,
                        out_channels=reg_out_channels,
                        kernel_size=3,
                        stride=1,
                        padding=1,
                        norm_cfg=self.norm_cfg,
                        act_cfg=self.act_cfg),
                    nn.Conv2d(
                        in_channels=reg_out_channels,
                        out_channels=4 * self.reg_max,
                        kernel_size=1)))
            self.cls_preds.append(
                nn.Sequential(
                    DWConv(
                        c1=self.in_channels[i],
                        c2=self.in_channels[i],
                        k=3),
                    Conv(
                        c1=self.in_channels[i],
                        c2=cls_out_channels,
                        k=1
                    ),
                    DWConv(
                        c1=cls_out_channels,
                        c2=cls_out_channels,
                        k=3),
                    Conv(
                        c1=self.in_channels[i],
                        c2=cls_out_channels,
                        k=1
                    ),
                    nn.Conv2d(
                        in_channels=cls_out_channels,
                        out_channels=self.num_classes,
                        kernel_size=1)))

        proj = torch.arange(self.reg_max, dtype=torch.float)
        self.register_buffer('proj', proj, persistent=False)