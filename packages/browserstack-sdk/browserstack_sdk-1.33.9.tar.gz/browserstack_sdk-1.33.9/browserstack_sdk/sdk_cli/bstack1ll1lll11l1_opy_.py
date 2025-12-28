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
from datetime import datetime, timezone
import os
import builtins
from pathlib import Path
from typing import Any, Tuple, Callable, List
from browserstack_sdk.sdk_cli.bstack1lll1lll1l1_opy_ import bstack1llll111ll1_opy_, bstack1llll11l1l1_opy_, bstack1lllll111l1_opy_
from browserstack_sdk.sdk_cli.bstack1lll11ll1l1_opy_ import bstack1ll1lll1l1l_opy_
from browserstack_sdk.sdk_cli.bstack1ll1ll1111l_opy_ import bstack1ll1l1l1lll_opy_
from browserstack_sdk.sdk_cli.bstack1lll11lll11_opy_ import bstack1ll1llll1l1_opy_
from browserstack_sdk.sdk_cli.test_framework import TestFramework, bstack1ll1ll1lll1_opy_, bstack1ll1l1ll111_opy_, bstack1ll1l1ll11l_opy_, bstack1ll1l111111_opy_
from json import dumps, JSONEncoder
import grpc
from browserstack_sdk import sdk_pb2 as structs
import sys
import traceback
import time
import json
from bstack_utils.helper import bstack1l1ll111lll_opy_, bstack1l1l1l1l11l_opy_
from bstack_utils.measure import measure
from bstack_utils.constants import *
bstack1l1l1lll1ll_opy_ = [bstack1ll_opy_ (u"ࠧࡴࡡ࡮ࡧࠥኹ"), bstack1ll_opy_ (u"ࠨࡰࡢࡴࡨࡲࡹࠨኺ"), bstack1ll_opy_ (u"ࠢࡤࡱࡱࡪ࡮࡭ࠢኻ"), bstack1ll_opy_ (u"ࠣࡵࡨࡷࡸ࡯࡯࡯ࠤኼ"), bstack1ll_opy_ (u"ࠤࡳࡥࡹ࡮ࠢኽ")]
bstack1l1ll1111l1_opy_ = bstack1l1l1l1l11l_opy_()
bstack1l1l11llll1_opy_ = bstack1ll_opy_ (u"࡙ࠥࡵࡲ࡯ࡢࡦࡨࡨࡆࡺࡴࡢࡥ࡫ࡱࡪࡴࡴࡴ࠯ࠥኾ")
bstack1l1l1llllll_opy_ = {
    bstack1ll_opy_ (u"ࠦࡵࡿࡴࡦࡵࡷ࠲ࡵࡿࡴࡩࡱࡱ࠲ࡎࡺࡥ࡮ࠤ኿"): bstack1l1l1lll1ll_opy_,
    bstack1ll_opy_ (u"ࠧࡶࡹࡵࡧࡶࡸ࠳ࡶࡹࡵࡪࡲࡲ࠳ࡖࡡࡤ࡭ࡤ࡫ࡪࠨዀ"): bstack1l1l1lll1ll_opy_,
    bstack1ll_opy_ (u"ࠨࡰࡺࡶࡨࡷࡹ࠴ࡰࡺࡶ࡫ࡳࡳ࠴ࡍࡰࡦࡸࡰࡪࠨ዁"): bstack1l1l1lll1ll_opy_,
    bstack1ll_opy_ (u"ࠢࡱࡻࡷࡩࡸࡺ࠮ࡱࡻࡷ࡬ࡴࡴ࠮ࡄ࡮ࡤࡷࡸࠨዂ"): bstack1l1l1lll1ll_opy_,
    bstack1ll_opy_ (u"ࠣࡲࡼࡸࡪࡹࡴ࠯ࡲࡼࡸ࡭ࡵ࡮࠯ࡈࡸࡲࡨࡺࡩࡰࡰࠥዃ"): bstack1l1l1lll1ll_opy_
    + [
        bstack1ll_opy_ (u"ࠤࡲࡶ࡮࡭ࡩ࡯ࡣ࡯ࡲࡦࡳࡥࠣዄ"),
        bstack1ll_opy_ (u"ࠥ࡯ࡪࡿࡷࡰࡴࡧࡷࠧዅ"),
        bstack1ll_opy_ (u"ࠦ࡫࡯ࡸࡵࡷࡵࡩ࡮ࡴࡦࡰࠤ዆"),
        bstack1ll_opy_ (u"ࠧࡱࡥࡺࡹࡲࡶࡩࡹࠢ዇"),
        bstack1ll_opy_ (u"ࠨࡣࡢ࡮࡯ࡷࡵ࡫ࡣࠣወ"),
        bstack1ll_opy_ (u"ࠢࡤࡣ࡯ࡰࡴࡨࡪࠣዉ"),
        bstack1ll_opy_ (u"ࠣࡵࡷࡥࡷࡺࠢዊ"),
        bstack1ll_opy_ (u"ࠤࡶࡸࡴࡶࠢዋ"),
        bstack1ll_opy_ (u"ࠥࡨࡺࡸࡡࡵ࡫ࡲࡲࠧዌ"),
        bstack1ll_opy_ (u"ࠦࡼ࡮ࡥ࡯ࠤው"),
    ],
    bstack1ll_opy_ (u"ࠧࡶࡹࡵࡧࡶࡸ࠳ࡳࡡࡪࡰ࠱ࡗࡪࡹࡳࡪࡱࡱࠦዎ"): [bstack1ll_opy_ (u"ࠨࡳࡵࡣࡵࡸࡵࡧࡴࡩࠤዏ"), bstack1ll_opy_ (u"ࠢࡵࡧࡶࡸࡸ࡬ࡡࡪ࡮ࡨࡨࠧዐ"), bstack1ll_opy_ (u"ࠣࡶࡨࡷࡹࡹࡣࡰ࡮࡯ࡩࡨࡺࡥࡥࠤዑ"), bstack1ll_opy_ (u"ࠤ࡬ࡸࡪࡳࡳࠣዒ")],
    bstack1ll_opy_ (u"ࠥࡴࡾࡺࡥࡴࡶ࠱ࡧࡴࡴࡦࡪࡩ࠱ࡇࡴࡴࡦࡪࡩࠥዓ"): [bstack1ll_opy_ (u"ࠦ࡮ࡴࡶࡰࡥࡤࡸ࡮ࡵ࡮ࡠࡲࡤࡶࡦࡳࡳࠣዔ"), bstack1ll_opy_ (u"ࠧࡧࡲࡨࡵࠥዕ")],
    bstack1ll_opy_ (u"ࠨࡰࡺࡶࡨࡷࡹ࠴ࡦࡪࡺࡷࡹࡷ࡫ࡳ࠯ࡈ࡬ࡼࡹࡻࡲࡦࡆࡨࡪࠧዖ"): [bstack1ll_opy_ (u"ࠢࡴࡥࡲࡴࡪࠨ዗"), bstack1ll_opy_ (u"ࠣࡣࡵ࡫ࡳࡧ࡭ࡦࠤዘ"), bstack1ll_opy_ (u"ࠤࡩࡹࡳࡩࠢዙ"), bstack1ll_opy_ (u"ࠥࡴࡦࡸࡡ࡮ࡵࠥዚ"), bstack1ll_opy_ (u"ࠦࡺࡴࡩࡵࡶࡨࡷࡹࠨዛ"), bstack1ll_opy_ (u"ࠧ࡯ࡤࡴࠤዜ")],
    bstack1ll_opy_ (u"ࠨࡰࡺࡶࡨࡷࡹ࠴ࡦࡪࡺࡷࡹࡷ࡫ࡳ࠯ࡕࡸࡦࡗ࡫ࡱࡶࡧࡶࡸࠧዝ"): [bstack1ll_opy_ (u"ࠢࡧ࡫ࡻࡸࡺࡸࡥ࡯ࡣࡰࡩࠧዞ"), bstack1ll_opy_ (u"ࠣࡲࡤࡶࡦࡳࠢዟ"), bstack1ll_opy_ (u"ࠤࡳࡥࡷࡧ࡭ࡠ࡫ࡱࡨࡪࡾࠢዠ")],
    bstack1ll_opy_ (u"ࠥࡴࡾࡺࡥࡴࡶ࠱ࡶࡺࡴ࡮ࡦࡴ࠱ࡇࡦࡲ࡬ࡊࡰࡩࡳࠧዡ"): [bstack1ll_opy_ (u"ࠦࡼ࡮ࡥ࡯ࠤዢ"), bstack1ll_opy_ (u"ࠧࡸࡥࡴࡷ࡯ࡸࠧዣ")],
    bstack1ll_opy_ (u"ࠨࡰࡺࡶࡨࡷࡹ࠴࡭ࡢࡴ࡮࠲ࡸࡺࡲࡶࡥࡷࡹࡷ࡫ࡳ࠯ࡐࡲࡨࡪࡑࡥࡺࡹࡲࡶࡩࡹࠢዤ"): [bstack1ll_opy_ (u"ࠢ࡯ࡱࡧࡩࠧዥ"), bstack1ll_opy_ (u"ࠣࡲࡤࡶࡪࡴࡴࠣዦ")],
    bstack1ll_opy_ (u"ࠤࡳࡽࡹ࡫ࡳࡵ࠰ࡰࡥࡷࡱ࠮ࡴࡶࡵࡹࡨࡺࡵࡳࡧࡶ࠲ࡒࡧࡲ࡬ࠤዧ"): [bstack1ll_opy_ (u"ࠥࡲࡦࡳࡥࠣየ"), bstack1ll_opy_ (u"ࠦࡦࡸࡧࡴࠤዩ"), bstack1ll_opy_ (u"ࠧࡱࡷࡢࡴࡪࡷࠧዪ")],
}
_1l1ll11111l_opy_ = set()
class bstack1ll1l111l1l_opy_(bstack1ll1lll1l1l_opy_):
    bstack1l1l11lll1l_opy_ = bstack1ll_opy_ (u"ࠨࡴࡦࡵࡷࡣࡩ࡫ࡦࡦࡴࡵࡩࡩࠨያ")
    bstack1l1l111ll1l_opy_ = bstack1ll_opy_ (u"ࠢࡊࡐࡉࡓࠧዬ")
    bstack1l1l1llll1l_opy_ = bstack1ll_opy_ (u"ࠣࡇࡕࡖࡔࡘࠢይ")
    bstack1l1l1ll1l11_opy_: Callable
    bstack1l1l1ll1ll1_opy_: Callable
    def __init__(self, bstack1ll1ll1l111_opy_, bstack1ll1lllllll_opy_):
        super().__init__()
        self.bstack1ll11l1l1l1_opy_ = bstack1ll1lllllll_opy_
        if os.getenv(bstack1ll_opy_ (u"ࠤࡖࡈࡐࡥࡃࡍࡋࡢࡊࡑࡇࡇࡠࡑ࠴࠵࡞ࠨዮ"), bstack1ll_opy_ (u"ࠥ࠵ࠧዯ")) != bstack1ll_opy_ (u"ࠦ࠶ࠨደ") or not self.is_enabled():
            self.logger.warning(bstack1ll_opy_ (u"ࠧࠨዱ") + str(self.__class__.__name__) + bstack1ll_opy_ (u"ࠨࠠࡥ࡫ࡶࡥࡧࡲࡥࡥࠤዲ"))
            return
        TestFramework.bstack1ll1111l11l_opy_((bstack1ll1ll1lll1_opy_.TEST, bstack1ll1l1ll11l_opy_.PRE), self.bstack1ll1111111l_opy_)
        TestFramework.bstack1ll1111l11l_opy_((bstack1ll1ll1lll1_opy_.TEST, bstack1ll1l1ll11l_opy_.POST), self.bstack1ll11111l11_opy_)
        for event in bstack1ll1ll1lll1_opy_:
            for state in bstack1ll1l1ll11l_opy_:
                TestFramework.bstack1ll1111l11l_opy_((event, state), self.bstack1l1l1lllll1_opy_)
        bstack1ll1ll1l111_opy_.bstack1ll1111l11l_opy_((bstack1llll11l1l1_opy_.bstack1llll1l1111_opy_, bstack1lllll111l1_opy_.POST), self.bstack1l1l1l11l11_opy_)
        self.bstack1l1l1ll1l11_opy_ = sys.stdout.write
        sys.stdout.write = self.bstack1l1ll111l1l_opy_(bstack1ll1l111l1l_opy_.bstack1l1l111ll1l_opy_, self.bstack1l1l1ll1l11_opy_)
        self.bstack1l1l1ll1ll1_opy_ = sys.stderr.write
        sys.stderr.write = self.bstack1l1ll111l1l_opy_(bstack1ll1l111l1l_opy_.bstack1l1l1llll1l_opy_, self.bstack1l1l1ll1ll1_opy_)
        self.bstack1l1l11ll1l1_opy_ = builtins.print
        builtins.print = self.bstack1l1l1l1ll11_opy_()
    def is_enabled(self) -> bool:
        return True
    def bstack1l1l1lllll1_opy_(
        self,
        f: TestFramework,
        instance: bstack1ll1l1ll111_opy_,
        bstack1lllll11l1l_opy_: Tuple[bstack1ll1ll1lll1_opy_, bstack1ll1l1ll11l_opy_],
        *args,
        **kwargs,
    ):
        if f.bstack1l1l11l1l1l_opy_() and instance:
            bstack1l1l1ll11l1_opy_ = datetime.now()
            test_framework_state, test_hook_state = bstack1lllll11l1l_opy_
            if test_framework_state == bstack1ll1ll1lll1_opy_.SETUP_FIXTURE:
                return
            elif test_framework_state == bstack1ll1ll1lll1_opy_.LOG:
                bstack11l1l1l1ll_opy_ = datetime.now()
                entries = f.bstack1l1l11l1ll1_opy_(instance, bstack1lllll11l1l_opy_)
                if entries:
                    self.bstack1l1l11ll11l_opy_(instance, entries)
                    instance.bstack11ll11ll1_opy_(bstack1ll_opy_ (u"ࠢࡨࡴࡳࡧ࠿ࡹࡥ࡯ࡦࡢࡰࡴ࡭࡟ࡤࡴࡨࡥࡹ࡫ࡤࡠࡧࡹࡩࡳࡺࠢዳ"), datetime.now() - bstack11l1l1l1ll_opy_)
                    f.bstack1l1l1ll1111_opy_(instance, bstack1lllll11l1l_opy_)
                instance.bstack11ll11ll1_opy_(bstack1ll_opy_ (u"ࠣࡱ࠴࠵ࡾࡀ࡯࡯ࡡࡤࡰࡱࡥࡴࡦࡵࡷࡣࡪࡼࡥ࡯ࡶࡶࠦዴ"), datetime.now() - bstack1l1l1ll11l1_opy_)
                return # bstack1l1l11l11l1_opy_ not send this event with the bstack1l1l1ll1lll_opy_ bstack1l1ll111l11_opy_
            elif (
                test_framework_state == bstack1ll1ll1lll1_opy_.TEST
                and test_hook_state == bstack1ll1l1ll11l_opy_.POST
                and not f.bstack1llll11ll11_opy_(instance, TestFramework.bstack1l1l1l11ll1_opy_)
            ):
                self.logger.warning(bstack1ll_opy_ (u"ࠤࡧࡶࡴࡶࡰࡪࡰࡪࠤࡩࡻࡥࠡࡶࡲࠤࡱࡧࡣ࡬ࠢࡲࡪࠥࡸࡥࡴࡷ࡯ࡸࡸࠦࠢድ") + str(TestFramework.bstack1llll11ll11_opy_(instance, TestFramework.bstack1l1l1l11ll1_opy_)) + bstack1ll_opy_ (u"ࠥࠦዶ"))
                f.bstack1llll1lll11_opy_(instance, bstack1ll1l111l1l_opy_.bstack1l1l11lll1l_opy_, True)
                return # bstack1l1l11l11l1_opy_ not send this event bstack1l1l1l111ll_opy_ bstack1l1l11l111l_opy_
            elif (
                f.bstack1llll1l111l_opy_(instance, bstack1ll1l111l1l_opy_.bstack1l1l11lll1l_opy_, False)
                and test_framework_state == bstack1ll1ll1lll1_opy_.LOG_REPORT
                and test_hook_state == bstack1ll1l1ll11l_opy_.POST
                and f.bstack1llll11ll11_opy_(instance, TestFramework.bstack1l1l1l11ll1_opy_)
            ):
                self.logger.warning(bstack1ll_opy_ (u"ࠦ࡮ࡴࡪࡦࡥࡷ࡭ࡳ࡭ࠠࡕࡧࡶࡸࡋࡸࡡ࡮ࡧࡺࡳࡷࡱࡓࡵࡣࡷࡩ࠳࡚ࡅࡔࡖ࠯ࠤ࡙࡫ࡳࡵࡊࡲࡳࡰ࡙ࡴࡢࡶࡨ࠲ࡕࡕࡓࡕࠢࠥዷ") + str(TestFramework.bstack1llll11ll11_opy_(instance, TestFramework.bstack1l1l1l11ll1_opy_)) + bstack1ll_opy_ (u"ࠧࠨዸ"))
                self.bstack1l1l1lllll1_opy_(f, instance, (bstack1ll1ll1lll1_opy_.TEST, bstack1ll1l1ll11l_opy_.POST), *args, **kwargs)
            bstack11l1l1l1ll_opy_ = datetime.now()
            data = instance.data.copy()
            bstack1l1ll111111_opy_ = sorted(
                filter(lambda x: x.get(bstack1ll_opy_ (u"ࠨࡥࡷࡧࡱࡸࡤࡹࡴࡢࡴࡷࡩࡩࡥࡡࡵࠤዹ"), None), data.pop(bstack1ll_opy_ (u"ࠢࡵࡧࡶࡸࡤ࡬ࡩࡹࡶࡸࡶࡪࡹࠢዺ"), {}).values()),
                key=lambda x: x[bstack1ll_opy_ (u"ࠣࡧࡹࡩࡳࡺ࡟ࡴࡶࡤࡶࡹ࡫ࡤࡠࡣࡷࠦዻ")],
            )
            if bstack1ll1l1l1lll_opy_.bstack1l1ll1111ll_opy_ in data:
                data.pop(bstack1ll1l1l1lll_opy_.bstack1l1ll1111ll_opy_)
            data.update({bstack1ll_opy_ (u"ࠤࡷࡩࡸࡺ࡟ࡧ࡫ࡻࡸࡺࡸࡥࡴࠤዼ"): bstack1l1ll111111_opy_})
            instance.bstack11ll11ll1_opy_(bstack1ll_opy_ (u"ࠥ࡮ࡸࡵ࡮࠻ࡶࡨࡷࡹࡥࡦࡪࡺࡷࡹࡷ࡫ࡳࠣዽ"), datetime.now() - bstack11l1l1l1ll_opy_)
            bstack11l1l1l1ll_opy_ = datetime.now()
            event_json = dumps(data, cls=bstack1l1l11lllll_opy_)
            instance.bstack11ll11ll1_opy_(bstack1ll_opy_ (u"ࠦ࡯ࡹ࡯࡯࠼ࡲࡲࡤࡧ࡬࡭ࡡࡷࡩࡸࡺ࡟ࡦࡸࡨࡲࡹࡹࠢዾ"), datetime.now() - bstack11l1l1l1ll_opy_)
            self.bstack1l1ll111l11_opy_(instance, bstack1lllll11l1l_opy_, event_json=event_json)
            instance.bstack11ll11ll1_opy_(bstack1ll_opy_ (u"ࠧࡵ࠱࠲ࡻ࠽ࡳࡳࡥࡡ࡭࡮ࡢࡸࡪࡹࡴࡠࡧࡹࡩࡳࡺࡳࠣዿ"), datetime.now() - bstack1l1l1ll11l1_opy_)
    def bstack1ll1111111l_opy_(
        self,
        f: TestFramework,
        instance: bstack1ll1l1ll111_opy_,
        bstack1lllll11l1l_opy_: Tuple[bstack1ll1ll1lll1_opy_, bstack1ll1l1ll11l_opy_],
        *args,
        **kwargs,
    ):
        from bstack_utils.bstack11ll1llll1_opy_ import bstack1lll1ll1l1l_opy_
        bstack1ll11l11l1l_opy_ = bstack1lll1ll1l1l_opy_.bstack1ll1111ll11_opy_(EVENTS.bstack111llll111_opy_.value)
        self.bstack1ll11l1l1l1_opy_.bstack1l1ll11llll_opy_(instance, f, bstack1lllll11l1l_opy_, *args, **kwargs)
        req = self.bstack1ll11l1l1l1_opy_.bstack1l1l1ll1l1l_opy_(instance, f, bstack1lllll11l1l_opy_, *args, **kwargs)
        self.bstack1l1ll11l11l_opy_(f, instance, req)
        bstack1lll1ll1l1l_opy_.end(EVENTS.bstack111llll111_opy_.value, bstack1ll11l11l1l_opy_ + bstack1ll_opy_ (u"ࠨ࠺ࡴࡶࡤࡶࡹࠨጀ"), bstack1ll11l11l1l_opy_ + bstack1ll_opy_ (u"ࠢ࠻ࡧࡱࡨࠧጁ"), status=True, failure=None, test_name=None)
    def bstack1ll11111l11_opy_(
        self,
        f: TestFramework,
        instance: bstack1ll1l1ll111_opy_,
        bstack1lllll11l1l_opy_: Tuple[bstack1ll1ll1lll1_opy_, bstack1ll1l1ll11l_opy_],
        *args,
        **kwargs,
    ):
        if not f.bstack1llll1l111l_opy_(instance, self.bstack1ll11l1l1l1_opy_.bstack1l1ll11l111_opy_, False):
            req = self.bstack1ll11l1l1l1_opy_.bstack1l1l1ll1l1l_opy_(instance, f, bstack1lllll11l1l_opy_, *args, **kwargs)
            self.bstack1l1ll11l11l_opy_(f, instance, req)
    @measure(event_name=EVENTS.bstack1l1l1l11lll_opy_, stage=STAGE.bstack1l1lll1ll1_opy_)
    def bstack1l1ll11l11l_opy_(
        self,
        f: TestFramework,
        instance: bstack1ll1l1ll111_opy_,
        req: structs.TestSessionEventRequest
    ):
        if not req:
            self.logger.debug(bstack1ll_opy_ (u"ࠣࡕ࡮࡭ࡵࡶࡩ࡯ࡩࠣࡘࡪࡹࡴࡔࡧࡶࡷ࡮ࡵ࡮ࡆࡸࡨࡲࡹࠦࡧࡓࡒࡆࠤࡨࡧ࡬࡭࠼ࠣࡒࡴࠦࡶࡢ࡮࡬ࡨࠥࡸࡥࡲࡷࡨࡷࡹࠦࡤࡢࡶࡤࠦጂ"))
            return
        bstack11l1l1l1ll_opy_ = datetime.now()
        try:
            r = self.bstack1ll1l11lll1_opy_.TestSessionEvent(req)
            instance.bstack11ll11ll1_opy_(bstack1ll_opy_ (u"ࠤࡪࡶࡵࡩ࠺ࡴࡧࡱࡨࡤࡺࡥࡴࡶࡢࡷࡪࡹࡳࡪࡱࡱࡣࡪࡼࡥ࡯ࡶࠥጃ"), datetime.now() - bstack11l1l1l1ll_opy_)
            f.bstack1llll1lll11_opy_(instance, self.bstack1ll11l1l1l1_opy_.bstack1l1ll11l111_opy_, r.success)
            if not r.success:
                self.logger.info(bstack1ll_opy_ (u"ࠥࡶࡪࡩࡥࡪࡸࡨࡨࠥ࡬ࡲࡰ࡯ࠣࡷࡪࡸࡶࡦࡴ࠽ࠤࠧጄ") + str(r) + bstack1ll_opy_ (u"ࠦࠧጅ"))
        except grpc.RpcError as e:
            self.logger.error(bstack1ll_opy_ (u"ࠧࡸࡰࡤ࠯ࡨࡶࡷࡵࡲ࠻ࠢࠥጆ") + str(e) + bstack1ll_opy_ (u"ࠨࠢጇ"))
            traceback.print_exc()
            raise e
    def bstack1l1l1l11l11_opy_(
        self,
        f: bstack1ll1llll1l1_opy_,
        _driver: object,
        exec: Tuple[bstack1llll111ll1_opy_, str],
        _1l1l1lll11l_opy_: Tuple[bstack1llll11l1l1_opy_, bstack1lllll111l1_opy_],
        result: Any,
        *args,
        **kwargs,
    ):
        instance, method_name = exec
        if not bstack1ll1llll1l1_opy_.bstack1ll11l1l111_opy_(method_name):
            return
        if f.bstack1ll11l1llll_opy_(*args) == bstack1ll1llll1l1_opy_.bstack1l1ll11l1ll_opy_:
            bstack1l1l1ll11l1_opy_ = datetime.now()
            screenshot = result.get(bstack1ll_opy_ (u"ࠢࡷࡣ࡯ࡹࡪࠨገ"), None) if isinstance(result, dict) else None
            if not isinstance(screenshot, str) or len(screenshot) <= 0:
                self.logger.warning(bstack1ll_opy_ (u"ࠣ࡫ࡱࡺࡦࡲࡩࡥࠢࡶࡧࡷ࡫ࡥ࡯ࡵ࡫ࡳࡹࠦࡩ࡮ࡣࡪࡩࠥࡨࡡࡴࡧ࠹࠸ࠥࡹࡴࡳࠤጉ"))
                return
            bstack1l1l1ll111l_opy_ = self.bstack1l1l111ll11_opy_(instance)
            if bstack1l1l1ll111l_opy_:
                entry = bstack1ll1l111111_opy_(TestFramework.bstack1l1l1l11111_opy_, screenshot)
                self.bstack1l1l11ll11l_opy_(bstack1l1l1ll111l_opy_, [entry])
                instance.bstack11ll11ll1_opy_(bstack1ll_opy_ (u"ࠤࡲ࠵࠶ࡿ࠺ࡰࡰࡢࡥ࡫ࡺࡥࡳࡡࡨࡼࡪࡩࡵࡵࡧࠥጊ"), datetime.now() - bstack1l1l1ll11l1_opy_)
            else:
                self.logger.warning(bstack1ll_opy_ (u"ࠥࡹࡳࡧࡢ࡭ࡧࠣࡸࡴࠦࡤࡦࡶࡨࡶࡲ࡯࡮ࡦࠢࡷࡩࡸࡺࠠࡧࡱࡵࠤࡼ࡮ࡩࡤࡪࠣࡸ࡭࡯ࡳࠡࡵࡦࡶࡪ࡫࡮ࡴࡪࡲࡸࠥࡽࡡࡴࠢࡷࡥࡰ࡫࡮ࠡࡤࡼࠤࡩࡸࡩࡷࡧࡵࡁࠥࢁࡽࠣጋ").format(instance.ref()))
        event = {}
        bstack1l1l1ll111l_opy_ = self.bstack1l1l111ll11_opy_(instance)
        if bstack1l1l1ll111l_opy_:
            self.bstack1l1l1lll1l1_opy_(event, bstack1l1l1ll111l_opy_)
            if event.get(bstack1ll_opy_ (u"ࠦࡱࡵࡧࡴࠤጌ")):
                self.bstack1l1l11ll11l_opy_(bstack1l1l1ll111l_opy_, event[bstack1ll_opy_ (u"ࠧࡲ࡯ࡨࡵࠥግ")])
            else:
                self.logger.debug(bstack1ll_opy_ (u"ࠨࡕ࡯ࡣࡥࡰࡪࠦࡴࡰࠢࡧࡩࡹ࡫ࡲ࡮࡫ࡱࡩࠥࡲ࡯ࡨࡵࠣࡪࡴࡸࠠࡢࡶࡷࡥࡨ࡮࡭ࡦࡰࡷࠤࡪࡼࡥ࡯ࡶࠥጎ"))
    @measure(event_name=EVENTS.bstack1l1l1l1l1l1_opy_, stage=STAGE.bstack1l1lll1ll1_opy_)
    def bstack1l1l11ll11l_opy_(
        self,
        bstack1l1l1ll111l_opy_: bstack1ll1l1ll111_opy_,
        entries: List[bstack1ll1l111111_opy_],
    ):
        self.bstack1ll111lll11_opy_()
        req = structs.LogCreatedEventRequest()
        req.bin_session_id = self.bin_session_id
        req.platform_index = TestFramework.bstack1llll1l111l_opy_(bstack1l1l1ll111l_opy_, TestFramework.bstack1l1lll1l1ll_opy_)
        req.execution_context.hash = str(bstack1l1l1ll111l_opy_.context.hash)
        req.execution_context.thread_id = str(bstack1l1l1ll111l_opy_.context.thread_id)
        req.execution_context.process_id = str(bstack1l1l1ll111l_opy_.context.process_id)
        for entry in entries:
            log_entry = req.logs.add()
            log_entry.test_framework_name = TestFramework.bstack1llll1l111l_opy_(bstack1l1l1ll111l_opy_, TestFramework.bstack1l1lll1lll1_opy_)
            log_entry.test_framework_version = TestFramework.bstack1llll1l111l_opy_(bstack1l1l1ll111l_opy_, TestFramework.bstack1l1l11l11ll_opy_)
            log_entry.uuid = TestFramework.bstack1llll1l111l_opy_(bstack1l1l1ll111l_opy_, TestFramework.bstack1ll111lll1l_opy_)
            log_entry.test_framework_state = bstack1l1l1ll111l_opy_.state.name
            log_entry.message = entry.message.encode(bstack1ll_opy_ (u"ࠢࡶࡶࡩ࠱࠽ࠨጏ"))
            log_entry.kind = entry.kind
            log_entry.timestamp = (
                entry.timestamp.isoformat()
                if isinstance(entry.timestamp, datetime)
                else datetime.now(tz=timezone.utc).isoformat()
            )
            if isinstance(entry.level, str) and len(entry.level.strip()) > 0:
                log_entry.level = entry.level.strip()
            if entry.kind == bstack1ll_opy_ (u"ࠣࡖࡈࡗ࡙ࡥࡁࡕࡖࡄࡇࡍࡓࡅࡏࡖࠥጐ"):
                log_entry.file_name = entry.fileName
                log_entry.file_size = entry.bstack1l1l11ll111_opy_
                log_entry.file_path = entry.bstack111ll1l_opy_
        def bstack1l1l1lll111_opy_():
            bstack11l1l1l1ll_opy_ = datetime.now()
            try:
                self.bstack1ll1l11lll1_opy_.LogCreatedEvent(req)
                if entry.kind == TestFramework.bstack1l1l1l11111_opy_:
                    bstack1l1l1ll111l_opy_.bstack11ll11ll1_opy_(bstack1ll_opy_ (u"ࠤࡪࡶࡵࡩ࠺ࡴࡧࡱࡨࡤࡲ࡯ࡨࡡࡦࡶࡪࡧࡴࡦࡦࡢࡩࡻ࡫࡮ࡵࡡࡶࡧࡷ࡫ࡥ࡯ࡵ࡫ࡳࡹࠨ጑"), datetime.now() - bstack11l1l1l1ll_opy_)
                elif entry.kind == TestFramework.bstack1l1ll11ll1l_opy_:
                    bstack1l1l1ll111l_opy_.bstack11ll11ll1_opy_(bstack1ll_opy_ (u"ࠥ࡫ࡷࡶࡣ࠻ࡵࡨࡲࡩࡥ࡬ࡰࡩࡢࡧࡷ࡫ࡡࡵࡧࡧࡣࡪࡼࡥ࡯ࡶࡢࡥࡹࡺࡡࡤࡪࡰࡩࡳࡺࠢጒ"), datetime.now() - bstack11l1l1l1ll_opy_)
                else:
                    bstack1l1l1ll111l_opy_.bstack11ll11ll1_opy_(bstack1ll_opy_ (u"ࠦ࡬ࡸࡰࡤ࠼ࡶࡩࡳࡪ࡟࡭ࡱࡪࡣࡨࡸࡥࡢࡶࡨࡨࡤ࡫ࡶࡦࡰࡷࡣࡱࡵࡧࠣጓ"), datetime.now() - bstack11l1l1l1ll_opy_)
            except grpc.RpcError as e:
                self.log_error(bstack1ll_opy_ (u"ࠧࡸࡰࡤ࠯ࡨࡶࡷࡵࡲ࠻ࠢࠥጔ") + str(e))
                traceback.print_exc()
                raise e
        self.bstack1lllll1ll1l_opy_.enqueue(bstack1l1l1lll111_opy_)
    @measure(event_name=EVENTS.bstack1l1l11l1lll_opy_, stage=STAGE.bstack1l1lll1ll1_opy_)
    def bstack1l1ll111l11_opy_(
        self,
        instance: bstack1ll1l1ll111_opy_,
        bstack1lllll11l1l_opy_: Tuple[bstack1ll1ll1lll1_opy_, bstack1ll1l1ll11l_opy_],
        event_json=None,
    ):
        self.bstack1ll111lll11_opy_()
        req = structs.TestFrameworkEventRequest()
        req.bin_session_id = self.bin_session_id
        req.platform_index = TestFramework.bstack1llll1l111l_opy_(instance, TestFramework.bstack1l1lll1l1ll_opy_)
        req.test_framework_name = TestFramework.bstack1llll1l111l_opy_(instance, TestFramework.bstack1l1lll1lll1_opy_)
        req.test_framework_version = TestFramework.bstack1llll1l111l_opy_(instance, TestFramework.bstack1l1l11l11ll_opy_)
        req.test_framework_state = bstack1lllll11l1l_opy_[0].name
        req.test_hook_state = bstack1lllll11l1l_opy_[1].name
        started_at = TestFramework.bstack1llll1l111l_opy_(instance, TestFramework.bstack1l1l1llll11_opy_, None)
        if started_at:
            req.started_at = started_at.isoformat()
        ended_at = TestFramework.bstack1llll1l111l_opy_(instance, TestFramework.bstack1l1ll11l1l1_opy_, None)
        if ended_at:
            req.ended_at = ended_at.isoformat()
        req.uuid = instance.ref()
        req.event_json = (event_json if event_json else dumps(instance.data, cls=bstack1l1l11lllll_opy_)).encode(bstack1ll_opy_ (u"ࠨࡵࡵࡨ࠰࠼ࠧጕ"))
        req.execution_context.hash = str(instance.context.hash)
        req.execution_context.thread_id = str(instance.context.thread_id)
        req.execution_context.process_id = str(instance.context.process_id)
        def bstack1l1l1lll111_opy_():
            bstack11l1l1l1ll_opy_ = datetime.now()
            try:
                self.bstack1ll1l11lll1_opy_.TestFrameworkEvent(req)
                instance.bstack11ll11ll1_opy_(bstack1ll_opy_ (u"ࠢࡨࡴࡳࡧ࠿ࡹࡥ࡯ࡦࡢࡸࡪࡹࡴࡠࡨࡵࡥࡲ࡫ࡷࡰࡴ࡮ࡣࡪࡼࡥ࡯ࡶࠥ጖"), datetime.now() - bstack11l1l1l1ll_opy_)
            except grpc.RpcError as e:
                self.log_error(bstack1ll_opy_ (u"ࠣࡴࡳࡧ࠲࡫ࡲࡳࡱࡵ࠾ࠥࠨ጗") + str(e))
                traceback.print_exc()
                raise e
        self.bstack1lllll1ll1l_opy_.enqueue(bstack1l1l1lll111_opy_)
    def bstack1l1l111ll11_opy_(self, instance: bstack1llll111ll1_opy_):
        bstack1l1ll11ll11_opy_ = TestFramework.bstack1llll1ll11l_opy_(instance.context)
        for t in bstack1l1ll11ll11_opy_:
            bstack1l1l1l1ll1l_opy_ = TestFramework.bstack1llll1l111l_opy_(t, bstack1ll1l1l1lll_opy_.bstack1l1ll1111ll_opy_, [])
            if any(instance is d[1] for d in bstack1l1l1l1ll1l_opy_):
                return t
    def bstack1l1l1ll11ll_opy_(self, message):
        self.bstack1l1l1ll1l11_opy_(message + bstack1ll_opy_ (u"ࠤ࡟ࡲࠧጘ"))
    def log_error(self, message):
        self.bstack1l1l1ll1ll1_opy_(message + bstack1ll_opy_ (u"ࠥࡠࡳࠨጙ"))
    def bstack1l1ll111l1l_opy_(self, level, original_func):
        def bstack1l1l1l1lll1_opy_(*args):
            try:
                try:
                    return_value = original_func(*args)
                except Exception:
                    return None
                try:
                    if not args or not isinstance(args[0], str) or not args[0].strip():
                        return return_value
                    message = args[0].strip()
                    if bstack1ll_opy_ (u"ࠦࡊࡼࡥ࡯ࡶࡇ࡭ࡸࡶࡡࡵࡥ࡫ࡩࡷࡓ࡯ࡥࡷ࡯ࡩࠧጚ") in message or bstack1ll_opy_ (u"ࠧࡡࡓࡅࡍࡆࡐࡎࡣࠢጛ") in message or bstack1ll_opy_ (u"ࠨ࡛ࡘࡧࡥࡈࡷ࡯ࡶࡦࡴࡐࡳࡩࡻ࡬ࡦ࡟ࠥጜ") in message:
                        return return_value
                    bstack1l1ll11ll11_opy_ = TestFramework.bstack1l1ll1l111l_opy_()
                    if not bstack1l1ll11ll11_opy_:
                        return return_value
                    bstack1l1l1ll111l_opy_ = next(
                        (
                            instance
                            for instance in bstack1l1ll11ll11_opy_
                            if TestFramework.bstack1llll11ll11_opy_(instance, TestFramework.bstack1ll111lll1l_opy_)
                        ),
                        None,
                    )
                    if not bstack1l1l1ll111l_opy_:
                        return return_value
                    entry = bstack1ll1l111111_opy_(TestFramework.bstack1l1l11ll1ll_opy_, message, level)
                    self.bstack1l1l11ll11l_opy_(bstack1l1l1ll111l_opy_, [entry])
                except Exception:
                    pass
                return return_value
            except Exception:
                return None
        return bstack1l1l1l1lll1_opy_
    def bstack1l1l1l1ll11_opy_(self):
        def bstack1l1l1l1l111_opy_(*args, **kwargs):
            try:
                self.bstack1l1l11ll1l1_opy_(*args, **kwargs)
                if not args:
                    return
                message = bstack1ll_opy_ (u"ࠧࠡࠩጝ").join(str(arg) for arg in args)
                if not message.strip():
                    return
                if bstack1ll_opy_ (u"ࠣࡇࡹࡩࡳࡺࡄࡪࡵࡳࡥࡹࡩࡨࡦࡴࡐࡳࡩࡻ࡬ࡦࠤጞ") in message:
                    return
                bstack1l1ll11ll11_opy_ = TestFramework.bstack1l1ll1l111l_opy_()
                if not bstack1l1ll11ll11_opy_:
                    return
                bstack1l1l1ll111l_opy_ = next(
                    (
                        instance
                        for instance in bstack1l1ll11ll11_opy_
                        if TestFramework.bstack1llll11ll11_opy_(instance, TestFramework.bstack1ll111lll1l_opy_)
                    ),
                    None,
                )
                if not bstack1l1l1ll111l_opy_:
                    return
                entry = bstack1ll1l111111_opy_(TestFramework.bstack1l1l11ll1ll_opy_, message, bstack1ll1l111l1l_opy_.bstack1l1l111ll1l_opy_)
                self.bstack1l1l11ll11l_opy_(bstack1l1l1ll111l_opy_, [entry])
            except Exception as e:
                try:
                    self.bstack1l1l11ll1l1_opy_(bstack1ll1ll111ll_opy_ (u"ࠤ࡞ࡉࡻ࡫࡮ࡵࡆ࡬ࡷࡵࡧࡴࡤࡪࡨࡶࡒࡵࡤࡶ࡮ࡨࡡࠥࡒ࡯ࡨࠢࡦࡥࡵࡺࡵࡳࡧࠣࡩࡷࡸ࡯ࡳ࠼ࠣࡿࡪࢃࠢጟ"))
                except:
                    pass
        return bstack1l1l1l1l111_opy_
    def bstack1l1l1lll1l1_opy_(self, event: dict, instance=None) -> None:
        global _1l1ll11111l_opy_
        levels = [bstack1ll_opy_ (u"ࠥࡘࡪࡹࡴࡍࡧࡹࡩࡱࠨጠ"), bstack1ll_opy_ (u"ࠦࡇࡻࡩ࡭ࡦࡏࡩࡻ࡫࡬ࠣጡ")]
        bstack1l1ll1l1111_opy_ = bstack1ll_opy_ (u"ࠧࠨጢ")
        if instance is not None:
            try:
                bstack1l1ll1l1111_opy_ = TestFramework.bstack1llll1l111l_opy_(instance, TestFramework.bstack1ll111lll1l_opy_)
            except Exception as e:
                self.logger.warning(bstack1ll_opy_ (u"ࠨࡅࡳࡴࡲࡶࠥ࡭ࡥࡵࡶ࡬ࡲ࡬ࠦࡵࡶ࡫ࡧࠤ࡫ࡸ࡯࡮ࠢ࡬ࡲࡸࡺࡡ࡯ࡥࡨࠦጣ").format(e))
        bstack1l1l1l11l1l_opy_ = []
        try:
            for level in levels:
                platform_index = os.environ[bstack1ll_opy_ (u"ࠧࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡐࡍࡃࡗࡊࡔࡘࡍࡠࡋࡑࡈࡊ࡞ࠧጤ")]
                bstack1l1l111lll1_opy_ = os.path.join(bstack1l1ll1111l1_opy_, (bstack1l1l11llll1_opy_ + str(platform_index)), level)
                if not os.path.isdir(bstack1l1l111lll1_opy_):
                    self.logger.debug(bstack1ll_opy_ (u"ࠣࡆ࡬ࡶࡪࡩࡴࡰࡴࡼࠤࡳࡵࡴࠡࡲࡵࡩࡸ࡫࡮ࡵࠢࡩࡳࡷࠦࡰࡳࡱࡦࡩࡸࡹࡩ࡯ࡩࠣࡘࡪࡹࡴࠡࡣࡱࡨࠥࡈࡵࡪ࡮ࡧࠤࡱ࡫ࡶࡦ࡮ࠣࡥࡹࡺࡡࡤࡪࡰࡩࡳࡺࡳࠡࡽࢀࠦጥ").format(bstack1l1l111lll1_opy_))
                    continue
                file_names = os.listdir(bstack1l1l111lll1_opy_)
                for file_name in file_names:
                    file_path = os.path.join(bstack1l1l111lll1_opy_, file_name)
                    abs_path = os.path.abspath(file_path)
                    if abs_path in _1l1ll11111l_opy_:
                        self.logger.info(bstack1ll_opy_ (u"ࠤࡓࡥࡹ࡮ࠠࡢ࡮ࡵࡩࡦࡪࡹࠡࡲࡵࡳࡨ࡫ࡳࡴࡧࡧࠤࢀࢃࠢጦ").format(abs_path))
                        continue
                    if os.path.isfile(file_path):
                        try:
                            bstack1l1l111llll_opy_ = os.path.getmtime(file_path)
                            timestamp = datetime.fromtimestamp(bstack1l1l111llll_opy_, tz=timezone.utc).isoformat()
                            file_size = os.path.getsize(file_path)
                            if level == bstack1ll_opy_ (u"ࠥࡘࡪࡹࡴࡍࡧࡹࡩࡱࠨጧ"):
                                entry = bstack1ll1l111111_opy_(
                                    kind=bstack1ll_opy_ (u"࡙ࠦࡋࡓࡕࡡࡄࡘ࡙ࡇࡃࡉࡏࡈࡒ࡙ࠨጨ"),
                                    message=bstack1ll_opy_ (u"ࠧࠨጩ"),
                                    level=level,
                                    timestamp=timestamp,
                                    fileName=file_name,
                                    bstack1l1l11ll111_opy_=file_size,
                                    bstack1l1l1l111l1_opy_=bstack1ll_opy_ (u"ࠨࡍࡂࡐࡘࡅࡑࡥࡕࡑࡎࡒࡅࡉࠨጪ"),
                                    bstack111ll1l_opy_=os.path.abspath(file_path),
                                    bstack11l1l1l1l1_opy_=bstack1l1ll1l1111_opy_
                                )
                            elif level == bstack1ll_opy_ (u"ࠢࡃࡷ࡬ࡰࡩࡒࡥࡷࡧ࡯ࠦጫ"):
                                entry = bstack1ll1l111111_opy_(
                                    kind=bstack1ll_opy_ (u"ࠣࡖࡈࡗ࡙ࡥࡁࡕࡖࡄࡇࡍࡓࡅࡏࡖࠥጬ"),
                                    message=bstack1ll_opy_ (u"ࠤࠥጭ"),
                                    level=level,
                                    timestamp=timestamp,
                                    fileName=file_name,
                                    bstack1l1l11ll111_opy_=file_size,
                                    bstack1l1l1l111l1_opy_=bstack1ll_opy_ (u"ࠥࡑࡆࡔࡕࡂࡎࡢ࡙ࡕࡒࡏࡂࡆࠥጮ"),
                                    bstack111ll1l_opy_=os.path.abspath(file_path),
                                    bstack1l1l11l1l11_opy_=bstack1l1ll1l1111_opy_
                                )
                            bstack1l1l1l11l1l_opy_.append(entry)
                            _1l1ll11111l_opy_.add(abs_path)
                        except Exception as bstack1l1ll11lll1_opy_:
                            self.logger.error(bstack1ll_opy_ (u"ࠦࡊࡾࡣࡦࡲࡷ࡭ࡴࡴࠠࡳࡣ࡬ࡷࡪࡪࠠࡸࡪࡨࡲࠥࡶࡲࡰࡥࡨࡷࡸ࡯࡮ࡨࠢࡤࡸࡹࡧࡣࡩ࡯ࡨࡲࡹࡹࠠࡼࡿࠥጯ").format(bstack1l1ll11lll1_opy_))
        except Exception as e:
            self.logger.error(bstack1ll_opy_ (u"ࠧࡋࡸࡤࡧࡳࡸ࡮ࡵ࡮ࠡࡴࡤ࡭ࡸ࡫ࡤࠡࡹ࡫ࡩࡳࠦࡰࡳࡱࡦࡩࡸࡹࡩ࡯ࡩࠣࡥࡹࡺࡡࡤࡪࡰࡩࡳࡺࡳࠡࡽࢀࠦጰ").format(e))
        event[bstack1ll_opy_ (u"ࠨ࡬ࡰࡩࡶࠦጱ")] = bstack1l1l1l11l1l_opy_
class bstack1l1l11lllll_opy_(JSONEncoder):
    def __init__(self, **kwargs):
        self.bstack1l1l111l1ll_opy_ = set()
        kwargs[bstack1ll_opy_ (u"ࠢࡴ࡭࡬ࡴࡰ࡫ࡹࡴࠤጲ")] = True
        super().__init__(**kwargs)
    def default(self, obj):
        return bstack1l1l1l1llll_opy_(obj, self.bstack1l1l111l1ll_opy_)
def bstack1l1l1l1111l_opy_(obj):
    return isinstance(obj, (str, int, float, bool, type(None)))
def bstack1l1l1l1llll_opy_(obj, bstack1l1l111l1ll_opy_=None, max_depth=3):
    if bstack1l1l111l1ll_opy_ is None:
        bstack1l1l111l1ll_opy_ = set()
    if id(obj) in bstack1l1l111l1ll_opy_ or max_depth <= 0:
        return None
    max_depth -= 1
    bstack1l1l111l1ll_opy_.add(id(obj))
    if isinstance(obj, datetime):
        return obj.isoformat()
    bstack1l1l11l1111_opy_ = TestFramework.bstack1l1ll111ll1_opy_(obj)
    bstack1l1l1l1l1ll_opy_ = next((k.lower() in bstack1l1l11l1111_opy_.lower() for k in bstack1l1l1llllll_opy_.keys()), None)
    if bstack1l1l1l1l1ll_opy_:
        obj = TestFramework.bstack1l1l11lll11_opy_(obj, bstack1l1l1llllll_opy_[bstack1l1l1l1l1ll_opy_])
    if not isinstance(obj, dict):
        keys = []
        if hasattr(obj, bstack1ll_opy_ (u"ࠣࡡࡢࡷࡱࡵࡴࡴࡡࡢࠦጳ")):
            keys = getattr(obj, bstack1ll_opy_ (u"ࠤࡢࡣࡸࡲ࡯ࡵࡵࡢࡣࠧጴ"), [])
        elif hasattr(obj, bstack1ll_opy_ (u"ࠥࡣࡤࡪࡩࡤࡶࡢࡣࠧጵ")):
            keys = getattr(obj, bstack1ll_opy_ (u"ࠦࡤࡥࡤࡪࡥࡷࡣࡤࠨጶ"), {}).keys()
        else:
            keys = dir(obj)
        obj = {k: getattr(obj, k, None) for k in keys if not str(k).startswith(bstack1ll_opy_ (u"ࠧࡥࠢጷ"))}
        if not obj and bstack1l1l11l1111_opy_ == bstack1ll_opy_ (u"ࠨࡰࡢࡶ࡫ࡰ࡮ࡨ࠮ࡑࡱࡶ࡭ࡽࡖࡡࡵࡪࠥጸ"):
            obj = {bstack1ll_opy_ (u"ࠢࡱࡣࡷ࡬ࠧጹ"): str(obj)}
    result = {}
    for key, value in obj.items():
        if not bstack1l1l1l1111l_opy_(key) or str(key).startswith(bstack1ll_opy_ (u"ࠣࡡࠥጺ")):
            continue
        if value is not None and bstack1l1l1l1111l_opy_(value):
            result[key] = value
        elif isinstance(value, dict):
            r = bstack1l1l1l1llll_opy_(value, bstack1l1l111l1ll_opy_, max_depth)
            if r is not None:
                result[key] = r
        elif isinstance(value, (list, tuple, set, frozenset)):
            result[key] = list(filter(None, [bstack1l1l1l1llll_opy_(o, bstack1l1l111l1ll_opy_, max_depth) for o in value]))
    return result or None