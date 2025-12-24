# -*- coding: utf-8 -*-


from mod.client.ui.controls.baseUIControl import BaseUIControl
from typing import Literal, overload


class StackPanelUIControl(BaseUIControl):
    @overload
    def SetOrientation(self, orientation):
        # type: (Literal["horizontal", "vertical"]) -> bool
        """
        设置stackPanel的排列方向
        """
        pass

    @overload
    def SetOrientation(self, orientation):
        # type: (str) -> bool
        pass

    @overload
    def GetOrientation(self):
        # type: () -> Literal["horizontal", "vertical"]
        """
        获取stackPanel的排列方向
        """
        pass

    @overload
    def GetOrientation(self):
        # type: () -> str
        pass

