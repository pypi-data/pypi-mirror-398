# coding: UTF-8
import sys
bstack1ll11l_opy_ = sys.version_info [0] == 2
bstack1lll11l_opy_ = 2048
bstack1lllllll_opy_ = 7
def bstack1ll_opy_ (bstack1111ll_opy_):
    global bstack1l11ll1_opy_
    bstack11_opy_ = ord (bstack1111ll_opy_ [-1])
    bstack1111ll1_opy_ = bstack1111ll_opy_ [:-1]
    bstack1111l1l_opy_ = bstack11_opy_ % len (bstack1111ll1_opy_)
    bstack1ll1_opy_ = bstack1111ll1_opy_ [:bstack1111l1l_opy_] + bstack1111ll1_opy_ [bstack1111l1l_opy_:]
    if bstack1ll11l_opy_:
        bstack11ll_opy_ = unicode () .join ([unichr (ord (char) - bstack1lll11l_opy_ - (bstack11111l_opy_ + bstack11_opy_) % bstack1lllllll_opy_) for bstack11111l_opy_, char in enumerate (bstack1ll1_opy_)])
    else:
        bstack11ll_opy_ = str () .join ([chr (ord (char) - bstack1lll11l_opy_ - (bstack11111l_opy_ + bstack11_opy_) % bstack1lllllll_opy_) for bstack11111l_opy_, char in enumerate (bstack1ll1_opy_)])
    return eval (bstack11ll_opy_)
import os
import traceback
from typing import Dict, Tuple, Callable, Type, List, Any
from urllib.parse import urlparse
from browserstack_sdk.sdk_cli.bstack1lll1lll1l1_opy_ import (
    bstack1llll1ll1ll_opy_,
    bstack1llll111ll1_opy_,
    bstack1llll11l1l1_opy_,
    bstack1lllll111l1_opy_,
)
import copy
from datetime import datetime, timezone, timedelta
class bstack1ll1l1l111l_opy_(bstack1llll1ll1ll_opy_):
    bstack1l111l1llll_opy_ = bstack1ll_opy_ (u"ࠢࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡐࡍࡃࡗࡊࡔࡘࡍࡠࡋࡑࡈࡊ࡞ࠢᑴ")
    bstack1l11lll1lll_opy_ = bstack1ll_opy_ (u"ࠣࡨࡵࡥࡲ࡫ࡷࡰࡴ࡮ࡣࡸ࡫ࡳࡴ࡫ࡲࡲࡤ࡯ࡤࠣᑵ")
    bstack1l11lll1ll1_opy_ = bstack1ll_opy_ (u"ࠤ࡫ࡹࡧࡥࡵࡳ࡮ࠥᑶ")
    bstack1l11lllll1l_opy_ = bstack1ll_opy_ (u"ࠥࡧࡦࡶࡡࡣ࡫࡯࡭ࡹ࡯ࡥࡴࠤᑷ")
    bstack1l111l1ll11_opy_ = bstack1ll_opy_ (u"ࠦࡼ࠹ࡣࡦࡺࡨࡧࡺࡺࡥࡴࡥࡵ࡭ࡵࡺࠢᑸ")
    bstack1l111l1l11l_opy_ = bstack1ll_opy_ (u"ࠧࡽ࠳ࡤࡧࡻࡩࡨࡻࡴࡦࡵࡦࡶ࡮ࡶࡴࡢࡵࡼࡲࡨࠨᑹ")
    NAME = bstack1ll_opy_ (u"ࠨࡰ࡭ࡣࡼࡻࡷ࡯ࡧࡩࡶࠥᑺ")
    bstack1l111l1l1l1_opy_: Dict[str, List[Callable]] = dict()
    platform_index: int
    options: Any
    desired_capabilities: Any
    bstack1ll1l1ll1ll_opy_: Any
    bstack1l111l1lll1_opy_: Dict
    def __init__(
        self,
        platform_index: int,
        framework_name: str,
        framework_version: str,
        classes: List[Type],
        methods=[bstack1ll_opy_ (u"ࠢ࡭ࡣࡸࡲࡨ࡮ࠢᑻ"), bstack1ll_opy_ (u"ࠣࡥࡲࡲࡳ࡫ࡣࡵࠤᑼ"), bstack1ll_opy_ (u"ࠤࡱࡩࡼࡥࡰࡢࡩࡨࠦᑽ"), bstack1ll_opy_ (u"ࠥࡧࡱࡵࡳࡦࠤᑾ"), bstack1ll_opy_ (u"ࠦࡩ࡯ࡳࡱࡣࡷࡧ࡭ࠨᑿ")],
    ):
        super().__init__(
            framework_name,
            framework_version,
            classes,
        )
        self.platform_index = platform_index
        self.bstack1llll111l1l_opy_(methods)
    def bstack1lllll1111l_opy_(self, instance: bstack1llll111ll1_opy_, method_name: str, bstack1llll1lll1l_opy_: timedelta, *args, **kwargs):
        pass
    def bstack1llll1ll1l1_opy_(
        self,
        target: object,
        exec: Tuple[bstack1llll111ll1_opy_, str],
        bstack1lllll11l1l_opy_: Tuple[bstack1llll11l1l1_opy_, bstack1lllll111l1_opy_],
        result: Any,
        *args,
        **kwargs,
    ) -> Callable[..., Any]:
        instance, method_name = exec
        bstack1lllll1l111_opy_, bstack1l111l1ll1l_opy_ = bstack1lllll11l1l_opy_
        bstack1l111l11lll_opy_ = bstack1ll1l1l111l_opy_.bstack1l111l11ll1_opy_(bstack1lllll11l1l_opy_)
        if bstack1l111l11lll_opy_ in bstack1ll1l1l111l_opy_.bstack1l111l1l1l1_opy_:
            bstack1l111l1l111_opy_ = None
            for callback in bstack1ll1l1l111l_opy_.bstack1l111l1l1l1_opy_[bstack1l111l11lll_opy_]:
                try:
                    bstack1l111l1l1ll_opy_ = callback(self, target, exec, bstack1lllll11l1l_opy_, result, *args, **kwargs)
                    if bstack1l111l1l111_opy_ == None:
                        bstack1l111l1l111_opy_ = bstack1l111l1l1ll_opy_
                except Exception as e:
                    self.logger.error(bstack1ll_opy_ (u"ࠧ࡫ࡲࡳࡱࡵࠤ࡮ࡴࡶࡰ࡭࡬ࡲ࡬ࠦࡣࡢ࡮࡯ࡦࡦࡩ࡫࠻ࠢࠥᒀ") + str(e) + bstack1ll_opy_ (u"ࠨࠢᒁ"))
                    traceback.print_exc()
            if bstack1l111l1ll1l_opy_ == bstack1lllll111l1_opy_.PRE and callable(bstack1l111l1l111_opy_):
                return bstack1l111l1l111_opy_
            elif bstack1l111l1ll1l_opy_ == bstack1lllll111l1_opy_.POST and bstack1l111l1l111_opy_:
                return bstack1l111l1l111_opy_
    def bstack1llll1111l1_opy_(
        self, method_name, previous_state: bstack1llll11l1l1_opy_, *args, **kwargs
    ) -> bstack1llll11l1l1_opy_:
        if method_name == bstack1ll_opy_ (u"ࠧ࡭ࡣࡸࡲࡨ࡮ࠧᒂ") or method_name == bstack1ll_opy_ (u"ࠨࡥࡲࡲࡳ࡫ࡣࡵࠩᒃ") or method_name == bstack1ll_opy_ (u"ࠩࡱࡩࡼࡥࡰࡢࡩࡨࠫᒄ"):
            return bstack1llll11l1l1_opy_.bstack1llll1l1l1l_opy_
        if method_name == bstack1ll_opy_ (u"ࠪࡨ࡮ࡹࡰࡢࡶࡦ࡬ࠬᒅ"):
            return bstack1llll11l1l1_opy_.bstack1llll1111ll_opy_
        if method_name == bstack1ll_opy_ (u"ࠫࡨࡲ࡯ࡴࡧࠪᒆ"):
            return bstack1llll11l1l1_opy_.QUIT
        return bstack1llll11l1l1_opy_.NONE
    @staticmethod
    def bstack1l111l11ll1_opy_(bstack1lllll11l1l_opy_: Tuple[bstack1llll11l1l1_opy_, bstack1lllll111l1_opy_]):
        return bstack1ll_opy_ (u"ࠧࡀࠢᒇ").join((bstack1llll11l1l1_opy_(bstack1lllll11l1l_opy_[0]).name, bstack1lllll111l1_opy_(bstack1lllll11l1l_opy_[1]).name))
    @staticmethod
    def bstack1ll1111l11l_opy_(bstack1lllll11l1l_opy_: Tuple[bstack1llll11l1l1_opy_, bstack1lllll111l1_opy_], callback: Callable):
        bstack1l111l11lll_opy_ = bstack1ll1l1l111l_opy_.bstack1l111l11ll1_opy_(bstack1lllll11l1l_opy_)
        if not bstack1l111l11lll_opy_ in bstack1ll1l1l111l_opy_.bstack1l111l1l1l1_opy_:
            bstack1ll1l1l111l_opy_.bstack1l111l1l1l1_opy_[bstack1l111l11lll_opy_] = []
        bstack1ll1l1l111l_opy_.bstack1l111l1l1l1_opy_[bstack1l111l11lll_opy_].append(callback)
    @staticmethod
    def bstack1ll11l1l111_opy_(method_name: str):
        return True
    @staticmethod
    def bstack1l1llll11l1_opy_(method_name: str, *args) -> bool:
        return True
    @staticmethod
    def bstack1ll111ll1l1_opy_(instance: bstack1llll111ll1_opy_, default_value=None):
        return bstack1llll1ll1ll_opy_.bstack1llll1l111l_opy_(instance, bstack1ll1l1l111l_opy_.bstack1l11lllll1l_opy_, default_value)
    @staticmethod
    def bstack1l1ll1l11l1_opy_(instance: bstack1llll111ll1_opy_) -> bool:
        return True
    @staticmethod
    def bstack1l1lllll1l1_opy_(instance: bstack1llll111ll1_opy_, default_value=None):
        return bstack1llll1ll1ll_opy_.bstack1llll1l111l_opy_(instance, bstack1ll1l1l111l_opy_.bstack1l11lll1ll1_opy_, default_value)
    @staticmethod
    def bstack1ll11l1llll_opy_(*args):
        return args[0] if args and type(args) in [list, tuple] and isinstance(args[0], str) else None
    @staticmethod
    def bstack1l1lll1ll1l_opy_(method_name: str, *args):
        if not bstack1ll1l1l111l_opy_.bstack1ll11l1l111_opy_(method_name):
            return False
        if not bstack1ll1l1l111l_opy_.bstack1l111l1ll11_opy_ in bstack1ll1l1l111l_opy_.bstack1l11l111l11_opy_(*args):
            return False
        bstack1l1lll11l1l_opy_ = bstack1ll1l1l111l_opy_.bstack1l1lll111l1_opy_(*args)
        return bstack1l1lll11l1l_opy_ and bstack1ll_opy_ (u"ࠨࡳࡤࡴ࡬ࡴࡹࠨᒈ") in bstack1l1lll11l1l_opy_ and bstack1ll_opy_ (u"ࠢࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰࡥࡥࡹࡧࡦࡹࡹࡵࡲࠣᒉ") in bstack1l1lll11l1l_opy_[bstack1ll_opy_ (u"ࠣࡵࡦࡶ࡮ࡶࡴࠣᒊ")]
    @staticmethod
    def bstack1l1llll111l_opy_(method_name: str, *args):
        if not bstack1ll1l1l111l_opy_.bstack1ll11l1l111_opy_(method_name):
            return False
        if not bstack1ll1l1l111l_opy_.bstack1l111l1ll11_opy_ in bstack1ll1l1l111l_opy_.bstack1l11l111l11_opy_(*args):
            return False
        bstack1l1lll11l1l_opy_ = bstack1ll1l1l111l_opy_.bstack1l1lll111l1_opy_(*args)
        return (
            bstack1l1lll11l1l_opy_
            and bstack1ll_opy_ (u"ࠤࡶࡧࡷ࡯ࡰࡵࠤᒋ") in bstack1l1lll11l1l_opy_
            and bstack1ll_opy_ (u"ࠥࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬ࡡࡤࡧࡨ࡫ࡳࡴ࡫ࡥ࡭ࡱ࡯ࡴࡺࡡࡤࡹࡹࡵ࡭ࡢࡶ࡬ࡳࡳࡥࡳࡤࡴ࡬ࡴࡹࠨᒌ") in bstack1l1lll11l1l_opy_[bstack1ll_opy_ (u"ࠦࡸࡩࡲࡪࡲࡷࠦᒍ")]
        )
    @staticmethod
    def bstack1l11l111l11_opy_(*args):
        return str(bstack1ll1l1l111l_opy_.bstack1ll11l1llll_opy_(*args)).lower()