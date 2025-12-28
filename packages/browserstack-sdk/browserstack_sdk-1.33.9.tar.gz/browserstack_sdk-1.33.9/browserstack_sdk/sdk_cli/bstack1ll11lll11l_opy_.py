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
import json
import time
import os
import threading
import asyncio
from browserstack_sdk.sdk_cli.bstack1lll1lll1l1_opy_ import (
    bstack1llll11l1l1_opy_,
    bstack1lllll111l1_opy_,
    bstack1llll111ll1_opy_,
    bstack1llll11l1ll_opy_,
)
from typing import Tuple, Dict, Any, List, Union
from bstack_utils.helper import bstack1l1ll111lll_opy_, bstack1ll1l1l1ll_opy_
from browserstack_sdk.sdk_cli.bstack1lll11lll11_opy_ import bstack1ll1llll1l1_opy_
from browserstack_sdk.sdk_cli.test_framework import TestFramework, bstack1ll1ll1lll1_opy_, bstack1ll1l1ll11l_opy_, bstack1ll1l1ll111_opy_
from browserstack_sdk.sdk_cli.bstack1ll1llll111_opy_ import bstack1ll1l1l111l_opy_
from browserstack_sdk.sdk_cli.bstack1l1ll1lllll_opy_ import bstack1l1ll1l1ll1_opy_
from typing import Tuple, List, Any
from bstack_utils.bstack11l1llll_opy_ import bstack1l11ll1l1_opy_, bstack11ll11111l_opy_, bstack1l111111ll_opy_
from browserstack_sdk import sdk_pb2 as structs
class bstack1ll1ll1l11l_opy_(bstack1l1ll1l1ll1_opy_):
    bstack1l11l1lll11_opy_ = bstack1ll_opy_ (u"ࠢࡵࡧࡶࡸࡤࡪࡲࡪࡸࡨࡶࡸࠨ፱")
    bstack1l1ll1111ll_opy_ = bstack1ll_opy_ (u"ࠣࡣࡸࡸࡴࡳࡡࡵ࡫ࡲࡲࡤࡹࡥࡴࡵ࡬ࡳࡳࡹࠢ፲")
    bstack1l11l1llll1_opy_ = bstack1ll_opy_ (u"ࠤࡱࡳࡳࡥࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯ࡤࡧࡵࡵࡱࡰࡥࡹ࡯࡯࡯ࡡࡶࡩࡸࡹࡩࡰࡰࡶࠦ፳")
    bstack1l11ll1l11l_opy_ = bstack1ll_opy_ (u"ࠥࡸࡪࡹࡴࡠࡵࡨࡷࡸ࡯࡯࡯ࡵࠥ፴")
    bstack1l11ll1111l_opy_ = bstack1ll_opy_ (u"ࠦࡦࡻࡴࡰ࡯ࡤࡸ࡮ࡵ࡮ࡠ࡫ࡱࡷࡹࡧ࡮ࡤࡧࡢࡶࡪ࡬ࡳࠣ፵")
    bstack1l1ll11l111_opy_ = bstack1ll_opy_ (u"ࠧࡩࡢࡵࡡࡶࡩࡸࡹࡩࡰࡰࡢࡧࡷ࡫ࡡࡵࡧࡧࠦ፶")
    bstack1l11l1ll1ll_opy_ = bstack1ll_opy_ (u"ࠨࡣࡣࡶࡢࡷࡪࡹࡳࡪࡱࡱࡣࡳࡧ࡭ࡦࠤ፷")
    bstack1l11ll1l111_opy_ = bstack1ll_opy_ (u"ࠢࡤࡤࡷࡣࡸ࡫ࡳࡴ࡫ࡲࡲࡤࡹࡴࡢࡶࡸࡷࠧ፸")
    def __init__(self):
        super().__init__(bstack1l1ll1llll1_opy_=self.bstack1l11l1lll11_opy_, frameworks=[bstack1ll1llll1l1_opy_.NAME])
        if not self.is_enabled():
            return
        TestFramework.bstack1ll1111l11l_opy_((bstack1ll1ll1lll1_opy_.BEFORE_EACH, bstack1ll1l1ll11l_opy_.POST), self.bstack1l11ll11111_opy_)
        if bstack1ll1l1l1ll_opy_():
            TestFramework.bstack1ll1111l11l_opy_((bstack1ll1ll1lll1_opy_.TEST, bstack1ll1l1ll11l_opy_.POST), self.bstack1ll1111111l_opy_)
        else:
            TestFramework.bstack1ll1111l11l_opy_((bstack1ll1ll1lll1_opy_.TEST, bstack1ll1l1ll11l_opy_.PRE), self.bstack1ll1111111l_opy_)
        TestFramework.bstack1ll1111l11l_opy_((bstack1ll1ll1lll1_opy_.TEST, bstack1ll1l1ll11l_opy_.POST), self.bstack1ll11111l11_opy_)
    def is_enabled(self) -> bool:
        return True
    def bstack1l11ll11111_opy_(
        self,
        f: TestFramework,
        instance: bstack1ll1l1ll111_opy_,
        bstack1lllll11l1l_opy_: Tuple[bstack1ll1ll1lll1_opy_, bstack1ll1l1ll11l_opy_],
        *args,
        **kwargs,
    ):
        bstack1l11ll1l1l1_opy_ = self.bstack1l11l1ll1l1_opy_(instance.context)
        if not bstack1l11ll1l1l1_opy_:
            self.logger.debug(bstack1ll_opy_ (u"ࠣࡵࡨࡸࡤࡧࡣࡵ࡫ࡹࡩࡤࡶࡡࡨࡧ࠽ࠤࡳࡵࠠࡱࡣࡪࡩࠥ࡬࡯ࡳࠢ࡫ࡳࡴࡱ࡟ࡪࡰࡩࡳࡂࠨ፹") + str(bstack1lllll11l1l_opy_) + bstack1ll_opy_ (u"ࠤࠥ፺"))
            return
        f.bstack1llll1lll11_opy_(instance, bstack1ll1ll1l11l_opy_.bstack1l1ll1111ll_opy_, bstack1l11ll1l1l1_opy_)
    def bstack1l11l1ll1l1_opy_(self, context: bstack1llll11l1ll_opy_, bstack1l11l1lll1l_opy_= True):
        if bstack1l11l1lll1l_opy_:
            bstack1l11ll1l1l1_opy_ = self.bstack1l1ll1lll1l_opy_(context, reverse=True)
        else:
            bstack1l11ll1l1l1_opy_ = self.bstack1l1ll1ll111_opy_(context, reverse=True)
        return [f for f in bstack1l11ll1l1l1_opy_ if f[1].state != bstack1llll11l1l1_opy_.QUIT]
    def bstack1ll1111111l_opy_(
        self,
        f: TestFramework,
        instance: bstack1ll1l1ll111_opy_,
        bstack1lllll11l1l_opy_: Tuple[bstack1ll1ll1lll1_opy_, bstack1ll1l1ll11l_opy_],
        *args,
        **kwargs,
    ):
        self.bstack1l11ll11111_opy_(f, instance, bstack1lllll11l1l_opy_, *args, **kwargs)
        if not bstack1l1ll111lll_opy_:
            self.logger.debug(bstack1ll_opy_ (u"ࠥࡳࡳࡥࡢࡦࡨࡲࡶࡪࡥࡴࡦࡵࡷ࠾ࠥࡴ࡯ࡵࠢࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫ࠡࡵࡨࡷࡸ࡯࡯࡯ࠢࡩࡳࡷࠦࡨࡰࡱ࡮ࡣ࡮ࡴࡦࡰ࠿ࡾ࡬ࡴࡵ࡫ࡠ࡫ࡱࡪࡴࢃࠠࡢࡴࡪࡷࡂࢁࡡࡳࡩࡶࢁࠥࡱࡷࡢࡴࡪࡷࡂࠨ፻") + str(kwargs) + bstack1ll_opy_ (u"ࠦࠧ፼"))
            return
        bstack1l11ll1l1l1_opy_ = f.bstack1llll1l111l_opy_(instance, bstack1ll1ll1l11l_opy_.bstack1l1ll1111ll_opy_, [])
        if not bstack1l11ll1l1l1_opy_:
            self.logger.debug(bstack1ll_opy_ (u"ࠧࡵ࡮ࡠࡤࡨࡪࡴࡸࡥࡠࡶࡨࡷࡹࡀࠠ࡯ࡱࠣࡨࡷ࡯ࡶࡦࡴࡶࠤ࡫ࡵࡲࠡࡪࡲࡳࡰࡥࡩ࡯ࡨࡲࡁࢀ࡮࡯ࡰ࡭ࡢ࡭ࡳ࡬࡯ࡾࠢࡤࡶ࡬ࡹ࠽ࡼࡣࡵ࡫ࡸࢃࠠ࡬ࡹࡤࡶ࡬ࡹ࠽ࠣ፽") + str(kwargs) + bstack1ll_opy_ (u"ࠨࠢ፾"))
            return
        if len(bstack1l11ll1l1l1_opy_) > 1:
            self.logger.debug(
                bstack1ll1ll111ll_opy_ (u"ࠢࡰࡰࡢࡦࡪ࡬࡯ࡳࡧࡢࡸࡪࡹࡴ࠻ࠢࡾࡰࡪࡴࠨࡱࡣࡪࡩࡤ࡯࡮ࡴࡶࡤࡲࡨ࡫ࡳࠪࡿࠣࡨࡷ࡯ࡶࡦࡴࡶࠤ࡫ࡵࡲࠡࡪࡲࡳࡰࡥࡩ࡯ࡨࡲࡁࢀ࡮࡯ࡰ࡭ࡢ࡭ࡳ࡬࡯ࡾࠢࡤࡶ࡬ࡹ࠽ࡼࡣࡵ࡫ࡸࢃࠠ࡬ࡹࡤࡶ࡬ࡹ࠽ࡼ࡭ࡺࡥࡷ࡭ࡳࡾࠤ፿"))
        bstack1l11l1lllll_opy_, bstack1l1l1111l11_opy_ = bstack1l11ll1l1l1_opy_[0]
        page = bstack1l11l1lllll_opy_()
        if not page:
            self.logger.debug(bstack1ll_opy_ (u"ࠣࡱࡱࡣࡧ࡫ࡦࡰࡴࡨࡣࡹ࡫ࡳࡵ࠼ࠣࡲࡴࠦࡰࡢࡩࡨࠤ࡫ࡵࡲࠡࡪࡲࡳࡰࡥࡩ࡯ࡨࡲࡁࢀ࡮࡯ࡰ࡭ࡢ࡭ࡳ࡬࡯ࡾࠢࡤࡶ࡬ࡹ࠽ࡼࡣࡵ࡫ࡸࢃࠠ࡬ࡹࡤࡶ࡬ࡹ࠽ࠣᎀ") + str(kwargs) + bstack1ll_opy_ (u"ࠤࠥᎁ"))
            return
        bstack1l1l11ll_opy_ = getattr(args[0], bstack1ll_opy_ (u"ࠥࡲࡴࡪࡥࡪࡦࠥᎂ"), None)
        from browserstack_sdk.sdk_cli.cli import cli
        if not cli.config.get(bstack1ll_opy_ (u"ࠦࡹ࡫ࡳࡵࡅࡲࡲࡹ࡫ࡸࡵࡑࡳࡸ࡮ࡵ࡮ࡴࠤᎃ")).get(bstack1ll_opy_ (u"ࠧࡹ࡫ࡪࡲࡖࡩࡸࡹࡩࡰࡰࡑࡥࡲ࡫ࠢᎄ")):
            try:
                page.evaluate(bstack1ll_opy_ (u"ࠨ࡟ࠡ࠿ࡁࠤࢀࢃࠢᎅ"),
                            bstack1ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰࡥࡥࡹࡧࡦࡹࡹࡵࡲ࠻ࠢࡾࠦࡦࡩࡴࡪࡱࡱࠦ࠿ࠦࠢࡴࡧࡷࡗࡪࡹࡳࡪࡱࡱࡒࡦࡳࡥࠣ࠮ࠣࠦࡦࡸࡧࡶ࡯ࡨࡲࡹࡹࠢ࠻ࠢࡾࠦࡳࡧ࡭ࡦࠤ࠽ࠫᎆ") + json.dumps(
                                bstack1l1l11ll_opy_) + bstack1ll_opy_ (u"ࠣࡿࢀࠦᎇ"))
            except Exception as e:
                self.logger.debug(bstack1ll_opy_ (u"ࠤࡨࡼࡨ࡫ࡰࡵ࡫ࡲࡲࠥ࡯࡮ࠡࡲ࡯ࡥࡾࡽࡲࡪࡩ࡫ࡸࠥࡹࡥࡴࡵ࡬ࡳࡳࠦ࡮ࡢ࡯ࡨࠤࢀࢃࠢᎈ"), e)
    def bstack1ll11111l11_opy_(
        self,
        f: TestFramework,
        instance: bstack1ll1l1ll111_opy_,
        bstack1lllll11l1l_opy_: Tuple[bstack1ll1ll1lll1_opy_, bstack1ll1l1ll11l_opy_],
        *args,
        **kwargs,
    ):
        self.bstack1l11ll11111_opy_(f, instance, bstack1lllll11l1l_opy_, *args, **kwargs)
        if not bstack1l1ll111lll_opy_:
            self.logger.debug(bstack1ll_opy_ (u"ࠥࡳࡳࡥࡢࡦࡨࡲࡶࡪࡥࡴࡦࡵࡷ࠾ࠥࡴ࡯ࡵࠢࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫ࠡࡵࡨࡷࡸ࡯࡯࡯ࠢࡩࡳࡷࠦࡨࡰࡱ࡮ࡣ࡮ࡴࡦࡰ࠿ࡾ࡬ࡴࡵ࡫ࡠ࡫ࡱࡪࡴࢃࠠࡢࡴࡪࡷࡂࢁࡡࡳࡩࡶࢁࠥࡱࡷࡢࡴࡪࡷࡂࠨᎉ") + str(kwargs) + bstack1ll_opy_ (u"ࠦࠧᎊ"))
            return
        bstack1l11ll1l1l1_opy_ = f.bstack1llll1l111l_opy_(instance, bstack1ll1ll1l11l_opy_.bstack1l1ll1111ll_opy_, [])
        if not bstack1l11ll1l1l1_opy_:
            self.logger.debug(bstack1ll_opy_ (u"ࠧࡵ࡮ࡠࡤࡨࡪࡴࡸࡥࡠࡶࡨࡷࡹࡀࠠ࡯ࡱࠣࡨࡷ࡯ࡶࡦࡴࡶࠤ࡫ࡵࡲࠡࡪࡲࡳࡰࡥࡩ࡯ࡨࡲࡁࢀ࡮࡯ࡰ࡭ࡢ࡭ࡳ࡬࡯ࡾࠢࡤࡶ࡬ࡹ࠽ࡼࡣࡵ࡫ࡸࢃࠠ࡬ࡹࡤࡶ࡬ࡹ࠽ࠣᎋ") + str(kwargs) + bstack1ll_opy_ (u"ࠨࠢᎌ"))
            return
        if len(bstack1l11ll1l1l1_opy_) > 1:
            self.logger.debug(
                bstack1ll1ll111ll_opy_ (u"ࠢࡰࡰࡢࡦࡪ࡬࡯ࡳࡧࡢࡸࡪࡹࡴ࠻ࠢࡾࡰࡪࡴࠨࡱࡣࡪࡩࡤ࡯࡮ࡴࡶࡤࡲࡨ࡫ࡳࠪࡿࠣࡨࡷ࡯ࡶࡦࡴࡶࠤ࡫ࡵࡲࠡࡪࡲࡳࡰࡥࡩ࡯ࡨࡲࡁࢀ࡮࡯ࡰ࡭ࡢ࡭ࡳ࡬࡯ࡾࠢࡤࡶ࡬ࡹ࠽ࡼࡣࡵ࡫ࡸࢃࠠ࡬ࡹࡤࡶ࡬ࡹ࠽ࡼ࡭ࡺࡥࡷ࡭ࡳࡾࠤᎍ"))
        bstack1l11l1lllll_opy_, bstack1l1l1111l11_opy_ = bstack1l11ll1l1l1_opy_[0]
        page = bstack1l11l1lllll_opy_()
        if not page:
            self.logger.debug(bstack1ll_opy_ (u"ࠣࡱࡱࡣࡧ࡫ࡦࡰࡴࡨࡣࡹ࡫ࡳࡵ࠼ࠣࡲࡴࠦࡰࡢࡩࡨࠤ࡫ࡵࡲࠡࡪࡲࡳࡰࡥࡩ࡯ࡨࡲࡁࢀ࡮࡯ࡰ࡭ࡢ࡭ࡳ࡬࡯ࡾࠢࡤࡶ࡬ࡹ࠽ࡼࡣࡵ࡫ࡸࢃࠠ࡬ࡹࡤࡶ࡬ࡹ࠽ࠣᎎ") + str(kwargs) + bstack1ll_opy_ (u"ࠤࠥᎏ"))
            return
        status = f.bstack1llll1l111l_opy_(instance, TestFramework.bstack1l11l1ll11l_opy_, None)
        if not status:
            self.logger.debug(bstack1ll_opy_ (u"ࠥࡲࡴࠦࡳࡵࡣࡷࡹࡸࠦࡦࡰࡴࠣࡸࡪࡹࡴ࠭ࠢ࡫ࡳࡴࡱ࡟ࡪࡰࡩࡳࡂࠨ᎐") + str(bstack1lllll11l1l_opy_) + bstack1ll_opy_ (u"ࠦࠧ᎑"))
            return
        bstack1l11ll11ll1_opy_ = {bstack1ll_opy_ (u"ࠧࡹࡴࡢࡶࡸࡷࠧ᎒"): status.lower()}
        bstack1l11ll11lll_opy_ = f.bstack1llll1l111l_opy_(instance, TestFramework.bstack1l11ll11l11_opy_, None)
        if status.lower() == bstack1ll_opy_ (u"࠭ࡦࡢ࡫࡯ࡩࡩ࠭᎓") and bstack1l11ll11lll_opy_ is not None:
            bstack1l11ll11ll1_opy_[bstack1ll_opy_ (u"ࠧࡳࡧࡤࡷࡴࡴࠧ᎔")] = bstack1l11ll11lll_opy_[0][bstack1ll_opy_ (u"ࠨࡤࡤࡧࡰࡺࡲࡢࡥࡨࠫ᎕")][0] if isinstance(bstack1l11ll11lll_opy_, list) else str(bstack1l11ll11lll_opy_)
        from browserstack_sdk.sdk_cli.cli import cli
        if not cli.config.get(bstack1ll_opy_ (u"ࠤࡷࡩࡸࡺࡃࡰࡰࡷࡩࡽࡺࡏࡱࡶ࡬ࡳࡳࡹࠢ᎖")).get(bstack1ll_opy_ (u"ࠥࡷࡰ࡯ࡰࡔࡧࡶࡷ࡮ࡵ࡮ࡔࡶࡤࡸࡺࡹࠢ᎗")):
            try:
                page.evaluate(
                        bstack1ll_opy_ (u"ࠦࡤࠦ࠽࠿ࠢࡾࢁࠧ᎘"),
                        bstack1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮ࡣࡪࡾࡥࡤࡷࡷࡳࡷࡀࠠࡼࠤࡤࡧࡹ࡯࡯࡯ࠤ࠽ࠤࠧࡹࡥࡵࡕࡨࡷࡸ࡯࡯࡯ࡕࡷࡥࡹࡻࡳࠣ࠮ࠣࠦࡦࡸࡧࡶ࡯ࡨࡲࡹࡹࠢ࠻ࠢࠪ᎙")
                        + json.dumps(bstack1l11ll11ll1_opy_)
                        + bstack1ll_opy_ (u"ࠨࡽࠣ᎚")
                    )
            except Exception as e:
                self.logger.debug(bstack1ll_opy_ (u"ࠢࡦࡺࡦࡩࡵࡺࡩࡰࡰࠣ࡭ࡳࠦࡰ࡭ࡣࡼࡻࡷ࡯ࡧࡩࡶࠣࡷࡪࡹࡳࡪࡱࡱࠤࡸࡺࡡࡵࡷࡶࠤࢀࢃࠢ᎛"), e)
    def bstack1l1ll11llll_opy_(
        self,
        instance: bstack1ll1l1ll111_opy_,
        f: TestFramework,
        bstack1lllll11l1l_opy_: Tuple[bstack1ll1ll1lll1_opy_, bstack1ll1l1ll11l_opy_],
        *args,
        **kwargs,
    ):
        self.bstack1l11ll11111_opy_(f, instance, bstack1lllll11l1l_opy_, *args, **kwargs)
        if not bstack1l1ll111lll_opy_:
            self.logger.debug(
                bstack1ll1ll111ll_opy_ (u"ࠣ࡯ࡤࡶࡰࡥ࡯࠲࠳ࡼࡣࡸࡿ࡮ࡤ࠼ࠣࡲࡴࡺࠠࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰࠦࡳࡦࡵࡶ࡭ࡴࡴࠬࠡࡪࡲࡳࡰࡥࡩ࡯ࡨࡲࡁࢀ࡮࡯ࡰ࡭ࡢ࡭ࡳ࡬࡯ࡾࠢࡤࡶ࡬ࡹ࠽ࡼࡣࡵ࡫ࡸࢃࠠ࡬ࡹࡤࡶ࡬ࡹ࠽ࡼ࡭ࡺࡥࡷ࡭ࡳࡾࠤ᎜"))
            return
        bstack1l11ll1l1l1_opy_ = f.bstack1llll1l111l_opy_(instance, bstack1ll1ll1l11l_opy_.bstack1l1ll1111ll_opy_, [])
        if not bstack1l11ll1l1l1_opy_:
            self.logger.debug(bstack1ll_opy_ (u"ࠤࡲࡲࡤࡨࡥࡧࡱࡵࡩࡤࡺࡥࡴࡶ࠽ࠤࡳࡵࠠࡥࡴ࡬ࡺࡪࡸࡳࠡࡨࡲࡶࠥ࡮࡯ࡰ࡭ࡢ࡭ࡳ࡬࡯࠾ࡽ࡫ࡳࡴࡱ࡟ࡪࡰࡩࡳࢂࠦࡡࡳࡩࡶࡁࢀࡧࡲࡨࡵࢀࠤࡰࡽࡡࡳࡩࡶࡁࠧ᎝") + str(kwargs) + bstack1ll_opy_ (u"ࠥࠦ᎞"))
            return
        if len(bstack1l11ll1l1l1_opy_) > 1:
            self.logger.debug(
                bstack1ll1ll111ll_opy_ (u"ࠦࡴࡴ࡟ࡣࡧࡩࡳࡷ࡫࡟ࡵࡧࡶࡸ࠿ࠦࡻ࡭ࡧࡱࠬࡵࡧࡧࡦࡡ࡬ࡲࡸࡺࡡ࡯ࡥࡨࡷ࠮ࢃࠠࡥࡴ࡬ࡺࡪࡸࡳࠡࡨࡲࡶࠥ࡮࡯ࡰ࡭ࡢ࡭ࡳ࡬࡯࠾ࡽ࡫ࡳࡴࡱ࡟ࡪࡰࡩࡳࢂࠦࡡࡳࡩࡶࡁࢀࡧࡲࡨࡵࢀࠤࡰࡽࡡࡳࡩࡶࡁࢀࡱࡷࡢࡴࡪࡷࢂࠨ᎟"))
        bstack1l11l1lllll_opy_, bstack1l1l1111l11_opy_ = bstack1l11ll1l1l1_opy_[0]
        page = bstack1l11l1lllll_opy_()
        if not page:
            self.logger.debug(bstack1ll_opy_ (u"ࠧࡳࡡࡳ࡭ࡢࡳ࠶࠷ࡹࡠࡵࡼࡲࡨࡀࠠ࡯ࡱࠣࡴࡦ࡭ࡥࠡࡨࡲࡶࠥ࡮࡯ࡰ࡭ࡢ࡭ࡳ࡬࡯࠾ࡽ࡫ࡳࡴࡱ࡟ࡪࡰࡩࡳࢂࠦࡡࡳࡩࡶࡁࢀࡧࡲࡨࡵࢀࠤࡰࡽࡡࡳࡩࡶࡁࠧᎠ") + str(kwargs) + bstack1ll_opy_ (u"ࠨࠢᎡ"))
            return
        timestamp = int(time.time() * 1000)
        data = bstack1ll_opy_ (u"ࠢࡐࡤࡶࡩࡷࡼࡡࡣ࡫࡯࡭ࡹࡿࡓࡺࡰࡦ࠾ࠧᎢ") + str(timestamp)
        try:
            page.evaluate(
                bstack1ll_opy_ (u"ࠣࡡࠣࡁࡃࠦࡻࡾࠤᎣ"),
                bstack1ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫ࡠࡧࡻࡩࡨࡻࡴࡰࡴ࠽ࠤࢀࢃࠧᎤ").format(
                    json.dumps(
                        {
                            bstack1ll_opy_ (u"ࠥࡥࡨࡺࡩࡰࡰࠥᎥ"): bstack1ll_opy_ (u"ࠦࡦࡴ࡮ࡰࡶࡤࡸࡪࠨᎦ"),
                            bstack1ll_opy_ (u"ࠧࡧࡲࡨࡷࡰࡩࡳࡺࡳࠣᎧ"): {
                                bstack1ll_opy_ (u"ࠨࡴࡺࡲࡨࠦᎨ"): bstack1ll_opy_ (u"ࠢࡂࡰࡱࡳࡹࡧࡴࡪࡱࡱࠦᎩ"),
                                bstack1ll_opy_ (u"ࠣࡦࡤࡸࡦࠨᎪ"): data,
                                bstack1ll_opy_ (u"ࠤ࡯ࡩࡻ࡫࡬ࠣᎫ"): bstack1ll_opy_ (u"ࠥࡨࡪࡨࡵࡨࠤᎬ")
                            }
                        }
                    )
                )
            )
        except Exception as e:
            self.logger.debug(bstack1ll_opy_ (u"ࠦࡪࡾࡣࡦࡲࡷ࡭ࡴࡴࠠࡪࡰࠣࡴࡱࡧࡹࡸࡴ࡬࡫࡭ࡺࠠࡰ࠳࠴ࡽࠥࡧ࡮࡯ࡱࡷࡥࡹ࡯࡯࡯ࠢࡰࡥࡷࡱࡩ࡯ࡩࠣࡿࢂࠨᎭ"), e)
    def bstack1l1l1ll1l1l_opy_(
        self,
        instance: bstack1ll1l1ll111_opy_,
        f: TestFramework,
        bstack1lllll11l1l_opy_: Tuple[bstack1ll1ll1lll1_opy_, bstack1ll1l1ll11l_opy_],
        *args,
        **kwargs,
    ):
        self.bstack1l11ll11111_opy_(f, instance, bstack1lllll11l1l_opy_, *args, **kwargs)
        if f.bstack1llll1l111l_opy_(instance, bstack1ll1ll1l11l_opy_.bstack1l1ll11l111_opy_, False):
            return
        self.bstack1ll111lll11_opy_()
        req = structs.TestSessionEventRequest()
        req.bin_session_id = self.bin_session_id
        req.platform_index = TestFramework.bstack1llll1l111l_opy_(instance, TestFramework.bstack1l1lll1l1ll_opy_)
        req.test_framework_name = TestFramework.bstack1llll1l111l_opy_(instance, TestFramework.bstack1l1lll1lll1_opy_)
        req.test_framework_version = TestFramework.bstack1llll1l111l_opy_(instance, TestFramework.bstack1l1l11l11ll_opy_)
        req.test_framework_state = bstack1lllll11l1l_opy_[0].name
        req.test_hook_state = bstack1lllll11l1l_opy_[1].name
        req.test_uuid = TestFramework.bstack1llll1l111l_opy_(instance, TestFramework.bstack1ll111lll1l_opy_)
        for bstack1l11ll111l1_opy_ in bstack1ll1l1l111l_opy_.bstack1lllll111ll_opy_.values():
            session = req.automation_sessions.add()
            session.provider = (
                bstack1ll_opy_ (u"ࠧࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮ࠦᎮ")
                if bstack1l1ll111lll_opy_
                else bstack1ll_opy_ (u"ࠨࡵ࡯࡭ࡱࡳࡼࡴ࡟ࡨࡴ࡬ࡨࠧᎯ")
            )
            session.ref = bstack1l11ll111l1_opy_.ref()
            session.hub_url = bstack1ll1l1l111l_opy_.bstack1llll1l111l_opy_(bstack1l11ll111l1_opy_, bstack1ll1l1l111l_opy_.bstack1l11lll1ll1_opy_, bstack1ll_opy_ (u"ࠢࠣᎰ"))
            session.framework_name = bstack1l11ll111l1_opy_.framework_name
            session.framework_version = bstack1l11ll111l1_opy_.framework_version
            session.framework_session_id = bstack1ll1l1l111l_opy_.bstack1llll1l111l_opy_(bstack1l11ll111l1_opy_, bstack1ll1l1l111l_opy_.bstack1l11lll1lll_opy_, bstack1ll_opy_ (u"ࠣࠤᎱ"))
        req.execution_context.hash = str(instance.context.hash)
        req.execution_context.thread_id = str(instance.context.thread_id)
        req.execution_context.process_id = str(instance.context.process_id)
        return req
    def bstack1ll11l1111l_opy_(
        self,
        f: TestFramework,
        instance: bstack1ll1l1ll111_opy_,
        bstack1lllll11l1l_opy_: Tuple[bstack1ll1ll1lll1_opy_, bstack1ll1l1ll11l_opy_],
        *args,
        **kwargs
    ):
        bstack1l11ll1l1l1_opy_ = f.bstack1llll1l111l_opy_(instance, bstack1ll1ll1l11l_opy_.bstack1l1ll1111ll_opy_, [])
        if not bstack1l11ll1l1l1_opy_:
            self.logger.debug(bstack1ll_opy_ (u"ࠤࡪࡩࡹࡥࡡࡶࡶࡲࡱࡦࡺࡩࡰࡰࡢࡨࡷ࡯ࡶࡦࡴ࠽ࠤࡳࡵࠠࡱࡣࡪࡩࡸࠦࡦࡰࡴࠣ࡬ࡴࡵ࡫ࡠ࡫ࡱࡪࡴࡃࡻࡩࡱࡲ࡯ࡤ࡯࡮ࡧࡱࢀࠤࡦࡸࡧࡴ࠿ࡾࡥࡷ࡭ࡳࡾࠢ࡮ࡻࡦࡸࡧࡴ࠿ࠥᎲ") + str(kwargs) + bstack1ll_opy_ (u"ࠥࠦᎳ"))
            return
        if len(bstack1l11ll1l1l1_opy_) > 1:
            self.logger.debug(bstack1ll_opy_ (u"ࠦ࡬࡫ࡴࡠࡣࡸࡸࡴࡳࡡࡵ࡫ࡲࡲࡤࡪࡲࡪࡸࡨࡶ࠿ࠦࡻ࡭ࡧࡱࠬࡵࡧࡧࡦࡡ࡬ࡲࡸࡺࡡ࡯ࡥࡨࡷ࠮ࢃࠠࡥࡴ࡬ࡺࡪࡸࡳࠡࡨࡲࡶࠥ࡮࡯ࡰ࡭ࡢ࡭ࡳ࡬࡯࠾ࡽ࡫ࡳࡴࡱ࡟ࡪࡰࡩࡳࢂࠦࡡࡳࡩࡶࡁࢀࡧࡲࡨࡵࢀࠤࡰࡽࡡࡳࡩࡶࡁࠧᎴ") + str(kwargs) + bstack1ll_opy_ (u"ࠧࠨᎵ"))
        bstack1l11l1lllll_opy_, bstack1l1l1111l11_opy_ = bstack1l11ll1l1l1_opy_[0]
        page = bstack1l11l1lllll_opy_()
        if not page:
            self.logger.debug(bstack1ll_opy_ (u"ࠨࡧࡦࡶࡢࡥࡺࡺ࡯࡮ࡣࡷ࡭ࡴࡴ࡟ࡥࡴ࡬ࡺࡪࡸ࠺ࠡࡰࡲࠤࡵࡧࡧࡦࠢࡩࡳࡷࠦࡨࡰࡱ࡮ࡣ࡮ࡴࡦࡰ࠿ࡾ࡬ࡴࡵ࡫ࡠ࡫ࡱࡪࡴࢃࠠࡢࡴࡪࡷࡂࢁࡡࡳࡩࡶࢁࠥࡱࡷࡢࡴࡪࡷࡂࠨᎶ") + str(kwargs) + bstack1ll_opy_ (u"ࠢࠣᎷ"))
            return
        return page
    def bstack1ll11l11111_opy_(
        self,
        f: TestFramework,
        instance: bstack1ll1l1ll111_opy_,
        bstack1lllll11l1l_opy_: Tuple[bstack1ll1ll1lll1_opy_, bstack1ll1l1ll11l_opy_],
        *args,
        **kwargs
    ):
        caps = {}
        bstack1l11ll11l1l_opy_ = {}
        for bstack1l11ll111l1_opy_ in bstack1ll1l1l111l_opy_.bstack1lllll111ll_opy_.values():
            caps = bstack1ll1l1l111l_opy_.bstack1llll1l111l_opy_(bstack1l11ll111l1_opy_, bstack1ll1l1l111l_opy_.bstack1l11lllll1l_opy_, bstack1ll_opy_ (u"ࠣࠤᎸ"))
        bstack1l11ll11l1l_opy_[bstack1ll_opy_ (u"ࠤࡥࡶࡴࡽࡳࡦࡴࡑࡥࡲ࡫ࠢᎹ")] = caps.get(bstack1ll_opy_ (u"ࠥࡦࡷࡵࡷࡴࡧࡵࠦᎺ"), bstack1ll_opy_ (u"ࠦࠧᎻ"))
        bstack1l11ll11l1l_opy_[bstack1ll_opy_ (u"ࠧࡶ࡬ࡢࡶࡩࡳࡷࡳࡎࡢ࡯ࡨࠦᎼ")] = caps.get(bstack1ll_opy_ (u"ࠨ࡯ࡴࠤᎽ"), bstack1ll_opy_ (u"ࠢࠣᎾ"))
        bstack1l11ll11l1l_opy_[bstack1ll_opy_ (u"ࠣࡲ࡯ࡥࡹ࡬࡯ࡳ࡯࡙ࡩࡷࡹࡩࡰࡰࠥᎿ")] = caps.get(bstack1ll_opy_ (u"ࠤࡲࡷࡤࡼࡥࡳࡵ࡬ࡳࡳࠨᏀ"), bstack1ll_opy_ (u"ࠥࠦᏁ"))
        bstack1l11ll11l1l_opy_[bstack1ll_opy_ (u"ࠦࡧࡸ࡯ࡸࡵࡨࡶ࡛࡫ࡲࡴ࡫ࡲࡲࠧᏂ")] = caps.get(bstack1ll_opy_ (u"ࠧࡨࡲࡰࡹࡶࡩࡷࡥࡶࡦࡴࡶ࡭ࡴࡴࠢᏃ"), bstack1ll_opy_ (u"ࠨࠢᏄ"))
        return bstack1l11ll11l1l_opy_
    def bstack1ll111111l1_opy_(self, page: object, bstack1l1llll1ll1_opy_, args={}):
        try:
            bstack1l11ll111ll_opy_ = bstack1ll_opy_ (u"ࠢࠣࠤࠫࡪࡺࡴࡣࡵ࡫ࡲࡲࠥ࠮࠮࠯࠰ࡥࡷࡹࡧࡣ࡬ࡕࡧ࡯ࡆࡸࡧࡴࠫࠣࡿࢀࠐࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࡴࡨࡸࡺࡸ࡮ࠡࡰࡨࡻࠥࡖࡲࡰ࡯࡬ࡷࡪ࠮ࠨࡳࡧࡶࡳࡱࡼࡥ࠭ࠢࡵࡩ࡯࡫ࡣࡵࠫࠣࡁࡃࠦࡻࡼࠌࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࡤࡶࡸࡦࡩ࡫ࡔࡦ࡮ࡅࡷ࡭ࡳ࠯ࡲࡸࡷ࡭࠮ࡲࡦࡵࡲࡰࡻ࡫ࠩ࠼ࠌࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࡽࡩࡲࡤࡨ࡯ࡥࡻࢀࠎࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࡽࡾࠫ࠾ࠎࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࢀࢁ࠮࠮ࡻࡢࡴࡪࡣ࡯ࡹ࡯࡯ࡿࠬࠦࠧࠨᏅ")
            bstack1l1llll1ll1_opy_ = bstack1l1llll1ll1_opy_.replace(bstack1ll_opy_ (u"ࠣࡣࡵ࡫ࡺࡳࡥ࡯ࡶࡶࠦᏆ"), bstack1ll_opy_ (u"ࠤࡥࡷࡹࡧࡣ࡬ࡕࡧ࡯ࡆࡸࡧࡴࠤᏇ"))
            script = bstack1l11ll111ll_opy_.format(fn_body=bstack1l1llll1ll1_opy_, arg_json=json.dumps(args))
            return page.evaluate(script)
        except Exception as e:
            self.logger.error(bstack1ll_opy_ (u"ࠥࡥ࠶࠷ࡹࡠࡵࡦࡶ࡮ࡶࡴࡠࡧࡻࡩࡨࡻࡴࡦ࠼ࠣࡉࡷࡸ࡯ࡳࠢࡨࡼࡪࡩࡵࡵ࡫ࡱ࡫ࠥࡺࡨࡦࠢࡤ࠵࠶ࡿࠠࡴࡥࡵ࡭ࡵࡺࠬࠡࠤᏈ") + str(e) + bstack1ll_opy_ (u"ࠦࠧᏉ"))