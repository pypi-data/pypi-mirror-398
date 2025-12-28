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
from datetime import datetime, timezone
from browserstack_sdk.sdk_cli.bstack1lll1lll1l1_opy_ import (
    bstack1llll11l1l1_opy_,
    bstack1lllll111l1_opy_,
    bstack1llll1ll1ll_opy_,
    bstack1llll111ll1_opy_,
    bstack1llll11l1ll_opy_,
)
from browserstack_sdk.sdk_cli.bstack1lll11lll11_opy_ import bstack1ll1llll1l1_opy_
from browserstack_sdk.sdk_cli.test_framework import TestFramework, bstack1ll1ll1lll1_opy_, bstack1ll1l1ll11l_opy_, bstack1ll1l1ll111_opy_
from browserstack_sdk.sdk_cli.bstack1l1ll1lllll_opy_ import bstack1l1ll1l1ll1_opy_
from typing import Tuple, Dict, Any, List, Union
from bstack_utils.helper import bstack1l1ll111lll_opy_
from browserstack_sdk import sdk_pb2 as structs
from bstack_utils.measure import measure
from bstack_utils.constants import *
from typing import Tuple, List, Any
class bstack1ll1l1l1lll_opy_(bstack1l1ll1l1ll1_opy_):
    bstack1l11l1lll11_opy_ = bstack1ll_opy_ (u"ࠣࡶࡨࡷࡹࡥࡤࡳ࡫ࡹࡩࡷࡹࠢᐡ")
    bstack1l1ll1111ll_opy_ = bstack1ll_opy_ (u"ࠤࡤࡹࡹࡵ࡭ࡢࡶ࡬ࡳࡳࡥࡳࡦࡵࡶ࡭ࡴࡴࡳࠣᐢ")
    bstack1l11l1llll1_opy_ = bstack1ll_opy_ (u"ࠥࡲࡴࡴ࡟ࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰࡥࡡࡶࡶࡲࡱࡦࡺࡩࡰࡰࡢࡷࡪࡹࡳࡪࡱࡱࡷࠧᐣ")
    bstack1l11ll1l11l_opy_ = bstack1ll_opy_ (u"ࠦࡹ࡫ࡳࡵࡡࡶࡩࡸࡹࡩࡰࡰࡶࠦᐤ")
    bstack1l11ll1111l_opy_ = bstack1ll_opy_ (u"ࠧࡧࡵࡵࡱࡰࡥࡹ࡯࡯࡯ࡡ࡬ࡲࡸࡺࡡ࡯ࡥࡨࡣࡷ࡫ࡦࡴࠤᐥ")
    bstack1l1ll11l111_opy_ = bstack1ll_opy_ (u"ࠨࡣࡣࡶࡢࡷࡪࡹࡳࡪࡱࡱࡣࡨࡸࡥࡢࡶࡨࡨࠧᐦ")
    bstack1l11l1ll1ll_opy_ = bstack1ll_opy_ (u"ࠢࡤࡤࡷࡣࡸ࡫ࡳࡴ࡫ࡲࡲࡤࡴࡡ࡮ࡧࠥᐧ")
    bstack1l11ll1l111_opy_ = bstack1ll_opy_ (u"ࠣࡥࡥࡸࡤࡹࡥࡴࡵ࡬ࡳࡳࡥࡳࡵࡣࡷࡹࡸࠨᐨ")
    def __init__(self):
        super().__init__(bstack1l1ll1llll1_opy_=self.bstack1l11l1lll11_opy_, frameworks=[bstack1ll1llll1l1_opy_.NAME])
        if not self.is_enabled():
            return
        TestFramework.bstack1ll1111l11l_opy_((bstack1ll1ll1lll1_opy_.BEFORE_EACH, bstack1ll1l1ll11l_opy_.POST), self.bstack1l111ll1l1l_opy_)
        TestFramework.bstack1ll1111l11l_opy_((bstack1ll1ll1lll1_opy_.TEST, bstack1ll1l1ll11l_opy_.PRE), self.bstack1ll1111111l_opy_)
        TestFramework.bstack1ll1111l11l_opy_((bstack1ll1ll1lll1_opy_.TEST, bstack1ll1l1ll11l_opy_.POST), self.bstack1ll11111l11_opy_)
    def is_enabled(self) -> bool:
        return True
    def bstack1l111ll1l1l_opy_(
        self,
        f: TestFramework,
        instance: bstack1ll1l1ll111_opy_,
        bstack1lllll11l1l_opy_: Tuple[bstack1ll1ll1lll1_opy_, bstack1ll1l1ll11l_opy_],
        *args,
        **kwargs,
    ):
        bstack1l1l1l1ll1l_opy_ = self.bstack1l111ll1l11_opy_(instance.context)
        if not bstack1l1l1l1ll1l_opy_:
            self.logger.debug(bstack1ll_opy_ (u"ࠤࡶࡩࡹࡥࡡࡤࡶ࡬ࡺࡪࡥࡤࡳ࡫ࡹࡩࡷࡹ࠺ࠡࡰࡲࠤࡩࡸࡩࡷࡧࡵࠤ࡫ࡵࡲࠡࡪࡲࡳࡰࡥࡩ࡯ࡨࡲࡁࠧᐩ") + str(bstack1lllll11l1l_opy_) + bstack1ll_opy_ (u"ࠥࠦᐪ"))
        f.bstack1llll1lll11_opy_(instance, bstack1ll1l1l1lll_opy_.bstack1l1ll1111ll_opy_, bstack1l1l1l1ll1l_opy_)
        bstack1l111ll1111_opy_ = self.bstack1l111ll1l11_opy_(instance.context, bstack1l111ll11l1_opy_=False)
        f.bstack1llll1lll11_opy_(instance, bstack1ll1l1l1lll_opy_.bstack1l11l1llll1_opy_, bstack1l111ll1111_opy_)
    def bstack1ll1111111l_opy_(
        self,
        f: TestFramework,
        instance: bstack1ll1l1ll111_opy_,
        bstack1lllll11l1l_opy_: Tuple[bstack1ll1ll1lll1_opy_, bstack1ll1l1ll11l_opy_],
        *args,
        **kwargs,
    ):
        self.bstack1l111ll1l1l_opy_(f, instance, bstack1lllll11l1l_opy_, *args, **kwargs)
        if not f.bstack1llll1l111l_opy_(instance, bstack1ll1l1l1lll_opy_.bstack1l11l1ll1ll_opy_, False):
            self.__1l111ll1ll1_opy_(f,instance,bstack1lllll11l1l_opy_)
    def bstack1ll11111l11_opy_(
        self,
        f: TestFramework,
        instance: bstack1ll1l1ll111_opy_,
        bstack1lllll11l1l_opy_: Tuple[bstack1ll1ll1lll1_opy_, bstack1ll1l1ll11l_opy_],
        *args,
        **kwargs,
    ):
        self.bstack1l111ll1l1l_opy_(f, instance, bstack1lllll11l1l_opy_, *args, **kwargs)
        if not f.bstack1llll1l111l_opy_(instance, bstack1ll1l1l1lll_opy_.bstack1l11l1ll1ll_opy_, False):
            self.__1l111ll1ll1_opy_(f, instance, bstack1lllll11l1l_opy_)
        if not f.bstack1llll1l111l_opy_(instance, bstack1ll1l1l1lll_opy_.bstack1l11ll1l111_opy_, False):
            self.__1l111llll11_opy_(f, instance, bstack1lllll11l1l_opy_)
    def bstack1l111lll1l1_opy_(
        self,
        f: bstack1ll1llll1l1_opy_,
        driver: object,
        exec: Tuple[bstack1llll111ll1_opy_, str],
        bstack1lllll11l1l_opy_: Tuple[bstack1llll11l1l1_opy_, bstack1lllll111l1_opy_],
        result: Any,
        *args,
        **kwargs,
    ):
        instance = exec[0]
        if not f.bstack1l1ll1l11l1_opy_(instance):
            return
        if f.bstack1llll1l111l_opy_(instance, bstack1ll1l1l1lll_opy_.bstack1l11ll1l111_opy_, False):
            return
        driver.execute_script(
            bstack1ll_opy_ (u"ࠦࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭ࡢࡩࡽ࡫ࡣࡶࡶࡲࡶ࠿ࠦࡻࡾࠤᐫ").format(
                json.dumps(
                    {
                        bstack1ll_opy_ (u"ࠧࡧࡣࡵ࡫ࡲࡲࠧᐬ"): bstack1ll_opy_ (u"ࠨࡳࡦࡶࡖࡩࡸࡹࡩࡰࡰࡖࡸࡦࡺࡵࡴࠤᐭ"),
                        bstack1ll_opy_ (u"ࠢࡢࡴࡪࡹࡲ࡫࡮ࡵࡵࠥᐮ"): {bstack1ll_opy_ (u"ࠣࡵࡷࡥࡹࡻࡳࠣᐯ"): result},
                    }
                )
            )
        )
        f.bstack1llll1lll11_opy_(instance, bstack1ll1l1l1lll_opy_.bstack1l11ll1l111_opy_, True)
    def bstack1l111ll1l11_opy_(self, context: bstack1llll11l1ll_opy_, bstack1l111ll11l1_opy_= True):
        if bstack1l111ll11l1_opy_:
            bstack1l1l1l1ll1l_opy_ = self.bstack1l1ll1lll1l_opy_(context, reverse=True)
        else:
            bstack1l1l1l1ll1l_opy_ = self.bstack1l1ll1ll111_opy_(context, reverse=True)
        return [f for f in bstack1l1l1l1ll1l_opy_ if f[1].state != bstack1llll11l1l1_opy_.QUIT]
    @measure(event_name=EVENTS.bstack11ll1ll1l1_opy_, stage=STAGE.bstack1l1lll1ll1_opy_)
    def __1l111llll11_opy_(
        self,
        f: TestFramework,
        instance: bstack1ll1l1ll111_opy_,
        bstack1lllll11l1l_opy_: Tuple[bstack1ll1ll1lll1_opy_, bstack1ll1l1ll11l_opy_],
    ):
        from browserstack_sdk.sdk_cli.cli import cli
        if not cli.config.get(bstack1ll_opy_ (u"ࠤࡷࡩࡸࡺࡃࡰࡰࡷࡩࡽࡺࡏࡱࡶ࡬ࡳࡳࡹࠢᐰ")).get(bstack1ll_opy_ (u"ࠥࡷࡰ࡯ࡰࡔࡧࡶࡷ࡮ࡵ࡮ࡔࡶࡤࡸࡺࡹࠢᐱ")):
            bstack1l1l1l1ll1l_opy_ = f.bstack1llll1l111l_opy_(instance, bstack1ll1l1l1lll_opy_.bstack1l1ll1111ll_opy_, [])
            if not bstack1l1l1l1ll1l_opy_:
                self.logger.debug(bstack1ll_opy_ (u"ࠦࡸ࡫ࡴࡠࡣࡦࡸ࡮ࡼࡥࡠࡦࡵ࡭ࡻ࡫ࡲࡴ࠼ࠣࡲࡴࠦࡤࡳ࡫ࡹࡩࡷࠦࡦࡰࡴࠣ࡬ࡴࡵ࡫ࡠ࡫ࡱࡪࡴࡃࠢᐲ") + str(bstack1lllll11l1l_opy_) + bstack1ll_opy_ (u"ࠧࠨᐳ"))
                return
            driver = bstack1l1l1l1ll1l_opy_[0][0]()
            status = f.bstack1llll1l111l_opy_(instance, TestFramework.bstack1l11l1ll11l_opy_, None)
            if not status:
                self.logger.debug(bstack1ll_opy_ (u"ࠨࡳࡦࡶࡢࡥࡨࡺࡩࡷࡧࡢࡨࡷ࡯ࡶࡦࡴࡶ࠾ࠥࡴ࡯ࠡࡵࡷࡥࡹࡻࡳࠡࡨࡲࡶࠥࡺࡥࡴࡶ࠯ࠤ࡭ࡵ࡯࡬ࡡ࡬ࡲ࡫ࡵ࠽ࠣᐴ") + str(bstack1lllll11l1l_opy_) + bstack1ll_opy_ (u"ࠢࠣᐵ"))
                return
            bstack1l11ll11ll1_opy_ = {bstack1ll_opy_ (u"ࠣࡵࡷࡥࡹࡻࡳࠣᐶ"): status.lower()}
            bstack1l11ll11lll_opy_ = f.bstack1llll1l111l_opy_(instance, TestFramework.bstack1l11ll11l11_opy_, None)
            if status.lower() == bstack1ll_opy_ (u"ࠩࡩࡥ࡮ࡲࡥࡥࠩᐷ") and bstack1l11ll11lll_opy_ is not None:
                bstack1l11ll11ll1_opy_[bstack1ll_opy_ (u"ࠪࡶࡪࡧࡳࡰࡰࠪᐸ")] = bstack1l11ll11lll_opy_[0][bstack1ll_opy_ (u"ࠫࡧࡧࡣ࡬ࡶࡵࡥࡨ࡫ࠧᐹ")][0] if isinstance(bstack1l11ll11lll_opy_, list) else str(bstack1l11ll11lll_opy_)
            driver.execute_script(
                bstack1ll_opy_ (u"ࠧࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮ࡣࡪࡾࡥࡤࡷࡷࡳࡷࡀࠠࡼࡿࠥᐺ").format(
                    json.dumps(
                        {
                            bstack1ll_opy_ (u"ࠨࡡࡤࡶ࡬ࡳࡳࠨᐻ"): bstack1ll_opy_ (u"ࠢࡴࡧࡷࡗࡪࡹࡳࡪࡱࡱࡗࡹࡧࡴࡶࡵࠥᐼ"),
                            bstack1ll_opy_ (u"ࠣࡣࡵ࡫ࡺࡳࡥ࡯ࡶࡶࠦᐽ"): bstack1l11ll11ll1_opy_,
                        }
                    )
                )
            )
            f.bstack1llll1lll11_opy_(instance, bstack1ll1l1l1lll_opy_.bstack1l11ll1l111_opy_, True)
    @measure(event_name=EVENTS.bstack111l1ll1l_opy_, stage=STAGE.bstack1l1lll1ll1_opy_)
    def __1l111ll1ll1_opy_(
        self,
        f: TestFramework,
        instance: bstack1ll1l1ll111_opy_,
        bstack1lllll11l1l_opy_: Tuple[bstack1ll1ll1lll1_opy_, bstack1ll1l1ll11l_opy_]
    ):
        from browserstack_sdk.sdk_cli.cli import cli
        if not cli.config.get(bstack1ll_opy_ (u"ࠤࡷࡩࡸࡺࡃࡰࡰࡷࡩࡽࡺࡏࡱࡶ࡬ࡳࡳࡹࠢᐾ")).get(bstack1ll_opy_ (u"ࠥࡷࡰ࡯ࡰࡔࡧࡶࡷ࡮ࡵ࡮ࡏࡣࡰࡩࠧᐿ")):
            test_name = f.bstack1llll1l111l_opy_(instance, TestFramework.bstack1l111lll11l_opy_, None)
            if not test_name:
                self.logger.debug(bstack1ll_opy_ (u"ࠦࡴࡴ࡟ࡣࡧࡩࡳࡷ࡫࡟ࡵࡧࡶࡸ࠿ࠦ࡭ࡪࡵࡶ࡭ࡳ࡭ࠠࡵࡧࡶࡸࠥࡴࡡ࡮ࡧࠥᑀ"))
                return
            bstack1l1l1l1ll1l_opy_ = f.bstack1llll1l111l_opy_(instance, bstack1ll1l1l1lll_opy_.bstack1l1ll1111ll_opy_, [])
            if not bstack1l1l1l1ll1l_opy_:
                self.logger.debug(bstack1ll_opy_ (u"ࠧࡹࡥࡵࡡࡤࡧࡹ࡯ࡶࡦࡡࡧࡶ࡮ࡼࡥࡳࡵ࠽ࠤࡳࡵࠠࡴࡶࡤࡸࡺࡹࠠࡧࡱࡵࠤࡹ࡫ࡳࡵ࠮ࠣ࡬ࡴࡵ࡫ࡠ࡫ࡱࡪࡴࡃࠢᑁ") + str(bstack1lllll11l1l_opy_) + bstack1ll_opy_ (u"ࠨࠢᑂ"))
                return
            for bstack1l1l11111ll_opy_, bstack1l111ll111l_opy_ in bstack1l1l1l1ll1l_opy_:
                if not bstack1ll1llll1l1_opy_.bstack1l1ll1l11l1_opy_(bstack1l111ll111l_opy_):
                    continue
                driver = bstack1l1l11111ll_opy_()
                if not driver:
                    continue
                driver.execute_script(
                    bstack1ll_opy_ (u"ࠢࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰࡥࡥࡹࡧࡦࡹࡹࡵࡲ࠻ࠢࡾࢁࠧᑃ").format(
                        json.dumps(
                            {
                                bstack1ll_opy_ (u"ࠣࡣࡦࡸ࡮ࡵ࡮ࠣᑄ"): bstack1ll_opy_ (u"ࠤࡶࡩࡹ࡙ࡥࡴࡵ࡬ࡳࡳࡔࡡ࡮ࡧࠥᑅ"),
                                bstack1ll_opy_ (u"ࠥࡥࡷ࡭ࡵ࡮ࡧࡱࡸࡸࠨᑆ"): {bstack1ll_opy_ (u"ࠦࡳࡧ࡭ࡦࠤᑇ"): test_name},
                            }
                        )
                    )
                )
            f.bstack1llll1lll11_opy_(instance, bstack1ll1l1l1lll_opy_.bstack1l11l1ll1ll_opy_, True)
    def bstack1l1ll11llll_opy_(
        self,
        instance: bstack1ll1l1ll111_opy_,
        f: TestFramework,
        bstack1lllll11l1l_opy_: Tuple[bstack1ll1ll1lll1_opy_, bstack1ll1l1ll11l_opy_],
        *args,
        **kwargs,
    ):
        self.bstack1l111ll1l1l_opy_(f, instance, bstack1lllll11l1l_opy_, *args, **kwargs)
        bstack1l1l1l1ll1l_opy_ = [d for d, _ in f.bstack1llll1l111l_opy_(instance, bstack1ll1l1l1lll_opy_.bstack1l1ll1111ll_opy_, [])]
        if not bstack1l1l1l1ll1l_opy_:
            self.logger.debug(bstack1ll_opy_ (u"ࠧࡵ࡮ࡠࡣࡩࡸࡪࡸ࡟ࡵࡧࡶࡸ࠿ࠦ࡮ࡰࠢࡶࡩࡸࡹࡩࡰࡰࡶࠤࡹࡵࠠ࡭࡫ࡱ࡯ࠧᑈ"))
            return
        if not bstack1l1ll111lll_opy_():
            self.logger.debug(bstack1ll_opy_ (u"ࠨ࡯࡯ࡡࡤࡪࡹ࡫ࡲࡠࡶࡨࡷࡹࡀࠠ࡯ࡱࡷࠤࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭ࠣࡷࡪࡹࡳࡪࡱࡱࠦᑉ"))
            return
        for bstack1l111ll1lll_opy_ in bstack1l1l1l1ll1l_opy_:
            driver = bstack1l111ll1lll_opy_()
            if not driver:
                continue
            timestamp = int(time.time() * 1000)
            data = bstack1ll_opy_ (u"ࠢࡐࡤࡶࡩࡷࡼࡡࡣ࡫࡯࡭ࡹࡿࡓࡺࡰࡦ࠾ࠧᑊ") + str(timestamp)
            driver.execute_script(
                bstack1ll_opy_ (u"ࠣࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࡟ࡦࡺࡨࡧࡺࡺ࡯ࡳ࠼ࠣࡿࢂࠨᑋ").format(
                    json.dumps(
                        {
                            bstack1ll_opy_ (u"ࠤࡤࡧࡹ࡯࡯࡯ࠤᑌ"): bstack1ll_opy_ (u"ࠥࡥࡳࡴ࡯ࡵࡣࡷࡩࠧᑍ"),
                            bstack1ll_opy_ (u"ࠦࡦࡸࡧࡶ࡯ࡨࡲࡹࡹࠢᑎ"): {
                                bstack1ll_opy_ (u"ࠧࡺࡹࡱࡧࠥᑏ"): bstack1ll_opy_ (u"ࠨࡁ࡯ࡰࡲࡸࡦࡺࡩࡰࡰࠥᑐ"),
                                bstack1ll_opy_ (u"ࠢࡥࡣࡷࡥࠧᑑ"): data,
                                bstack1ll_opy_ (u"ࠣ࡮ࡨࡺࡪࡲࠢᑒ"): bstack1ll_opy_ (u"ࠤࡧࡩࡧࡻࡧࠣᑓ")
                            }
                        }
                    )
                )
            )
    def bstack1l1l1ll1l1l_opy_(
        self,
        instance: bstack1ll1l1ll111_opy_,
        f: TestFramework,
        bstack1lllll11l1l_opy_: Tuple[bstack1ll1ll1lll1_opy_, bstack1ll1l1ll11l_opy_],
        *args,
        **kwargs,
    ):
        self.bstack1l111ll1l1l_opy_(f, instance, bstack1lllll11l1l_opy_, *args, **kwargs)
        keys = [
            bstack1ll1l1l1lll_opy_.bstack1l1ll1111ll_opy_,
            bstack1ll1l1l1lll_opy_.bstack1l11l1llll1_opy_,
        ]
        bstack1l1l1l1ll1l_opy_ = []
        for key in keys:
            bstack1l1l1l1ll1l_opy_.extend(f.bstack1llll1l111l_opy_(instance, key, []))
        if not bstack1l1l1l1ll1l_opy_:
            self.logger.debug(bstack1ll_opy_ (u"ࠥࡳࡳࡥࡡࡧࡶࡨࡶࡤࡺࡥࡴࡶ࠽ࠤࡺࡴࡡࡣ࡮ࡨࠤࡹࡵࠠࡧ࡫ࡱࡨࠥࡧ࡮ࡺࠢࡶࡩࡸࡹࡩࡰࡰࡶࠤࡹࡵࠠ࡭࡫ࡱ࡯ࠧᑔ"))
            return
        if f.bstack1llll1l111l_opy_(instance, bstack1ll1l1l1lll_opy_.bstack1l1ll11l111_opy_, False):
            self.logger.debug(bstack1ll_opy_ (u"ࠦࡴࡴ࡟ࡢࡨࡷࡩࡷࡥࡴࡦࡵࡷ࠾ࠥࡉࡂࡕࠢࡤࡰࡷ࡫ࡡࡥࡻࠣࡧࡷ࡫ࡡࡵࡧࡧࠦᑕ"))
            return
        self.bstack1ll111lll11_opy_()
        bstack11l1l1l1ll_opy_ = datetime.now()
        req = structs.TestSessionEventRequest()
        req.bin_session_id = self.bin_session_id
        req.platform_index = TestFramework.bstack1llll1l111l_opy_(instance, TestFramework.bstack1l1lll1l1ll_opy_)
        req.test_framework_name = TestFramework.bstack1llll1l111l_opy_(instance, TestFramework.bstack1l1lll1lll1_opy_)
        req.test_framework_version = TestFramework.bstack1llll1l111l_opy_(instance, TestFramework.bstack1l1l11l11ll_opy_)
        req.test_framework_state = bstack1lllll11l1l_opy_[0].name
        req.test_hook_state = bstack1lllll11l1l_opy_[1].name
        req.test_uuid = TestFramework.bstack1llll1l111l_opy_(instance, TestFramework.bstack1ll111lll1l_opy_)
        for bstack1l1l11111ll_opy_, driver in bstack1l1l1l1ll1l_opy_:
            try:
                webdriver = bstack1l1l11111ll_opy_()
                if webdriver is None:
                    self.logger.debug(bstack1ll_opy_ (u"ࠧ࡝ࡥࡣࡆࡵ࡭ࡻ࡫ࡲࠡ࡫ࡱࡷࡹࡧ࡮ࡤࡧࠣ࡭ࡸࠦࡎࡰࡰࡨࠤ࠭ࡸࡥࡧࡧࡵࡩࡳࡩࡥࠡࡧࡻࡴ࡮ࡸࡥࡥࠫࠥᑖ"))
                    continue
                session = req.automation_sessions.add()
                session.provider = (
                    bstack1ll_opy_ (u"ࠨࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯ࠧᑗ")
                    if bstack1ll1llll1l1_opy_.bstack1llll1l111l_opy_(driver, bstack1ll1llll1l1_opy_.bstack1l111lll111_opy_, False)
                    else bstack1ll_opy_ (u"ࠢࡶࡰ࡮ࡲࡴࡽ࡮ࡠࡩࡵ࡭ࡩࠨᑘ")
                )
                session.ref = driver.ref()
                session.hub_url = bstack1ll1llll1l1_opy_.bstack1llll1l111l_opy_(driver, bstack1ll1llll1l1_opy_.bstack1l11lll1ll1_opy_, bstack1ll_opy_ (u"ࠣࠤᑙ"))
                session.framework_name = driver.framework_name
                session.framework_version = driver.framework_version
                session.framework_session_id = bstack1ll1llll1l1_opy_.bstack1llll1l111l_opy_(driver, bstack1ll1llll1l1_opy_.bstack1l11lll1lll_opy_, bstack1ll_opy_ (u"ࠤࠥᑚ"))
                caps = None
                if hasattr(webdriver, bstack1ll_opy_ (u"ࠥࡧࡦࡶࡡࡣ࡫࡯࡭ࡹ࡯ࡥࡴࠤᑛ")):
                    try:
                        caps = webdriver.capabilities
                        self.logger.debug(bstack1ll_opy_ (u"ࠦࡘࡻࡣࡤࡧࡶࡷ࡫ࡻ࡬࡭ࡻࠣࡶࡪࡺࡲࡪࡧࡹࡩࡩࠦࡣࡢࡲࡤࡦ࡮ࡲࡩࡵ࡫ࡨࡷࠥࡪࡩࡳࡧࡦࡸࡱࡿࠠࡧࡴࡲࡱࠥࡪࡲࡪࡸࡨࡶ࠳ࡩࡡࡱࡣࡥ࡭ࡱ࡯ࡴࡪࡧࡶࠦᑜ"))
                    except Exception as e:
                        self.logger.debug(bstack1ll_opy_ (u"ࠧࡌࡡࡪ࡮ࡨࡨࠥࡺ࡯ࠡࡩࡨࡸࠥࡩࡡࡱࡣࡥ࡭ࡱ࡯ࡴࡪࡧࡶࠤ࡫ࡸ࡯࡮ࠢࡧࡶ࡮ࡼࡥࡳ࠰ࡦࡥࡵࡧࡢࡪ࡮࡬ࡸ࡮࡫ࡳ࠻ࠢࠥᑝ") + str(e) + bstack1ll_opy_ (u"ࠨࠢᑞ"))
                try:
                    bstack1l111lll1ll_opy_ = json.dumps(caps).encode(bstack1ll_opy_ (u"ࠢࡶࡶࡩ࠱࠽ࠨᑟ")) if caps else bstack1l111ll11ll_opy_ (u"ࠣࡽࢀࠦᑠ")
                    req.capabilities = bstack1l111lll1ll_opy_
                except Exception as e:
                    self.logger.debug(bstack1ll_opy_ (u"ࠤࡪࡩࡹࡥࡣࡣࡶࡢࡩࡻ࡫࡮ࡵ࠼ࠣࡪࡦ࡯࡬ࡦࡦࠣࡸࡴࠦࡳࡦࡰࡧࠤࡸ࡫ࡲࡪࡣ࡯࡭ࡿ࡫ࠠࡤࡣࡳࡷࠥ࡬࡯ࡳࠢࡵࡩࡶࡻࡥࡴࡶ࠽ࠤࠧᑡ") + str(e) + bstack1ll_opy_ (u"ࠥࠦᑢ"))
            except Exception as e:
                self.logger.error(bstack1ll_opy_ (u"ࠦࡊࡸࡲࡰࡴࠣࡴࡷࡵࡣࡦࡵࡶ࡭ࡳ࡭ࠠࡥࡴ࡬ࡺࡪࡸࠠࡪࡶࡨࡱ࠿ࠦࠢᑣ") + str(str(e)) + bstack1ll_opy_ (u"ࠧࠨᑤ"))
        req.execution_context.hash = str(instance.context.hash)
        req.execution_context.thread_id = str(instance.context.thread_id)
        req.execution_context.process_id = str(instance.context.process_id)
        return req
    def bstack1ll11l11111_opy_(
        self,
        f: TestFramework,
        instance: bstack1ll1l1ll111_opy_,
        bstack1lllll11l1l_opy_: Tuple[bstack1ll1ll1lll1_opy_, bstack1ll1l1ll11l_opy_],
        *args,
        **kwargs
    ):
        bstack1l1l1l1ll1l_opy_ = f.bstack1llll1l111l_opy_(instance, bstack1ll1l1l1lll_opy_.bstack1l1ll1111ll_opy_, [])
        if not bstack1l1ll111lll_opy_() and len(bstack1l1l1l1ll1l_opy_) == 0:
            bstack1l1l1l1ll1l_opy_ = f.bstack1llll1l111l_opy_(instance, bstack1ll1l1l1lll_opy_.bstack1l11l1llll1_opy_, [])
        if not bstack1l1l1l1ll1l_opy_:
            self.logger.debug(bstack1ll_opy_ (u"ࠨ࡯࡯ࡡࡥࡩ࡫ࡵࡲࡦࡡࡷࡩࡸࡺ࠺ࠡࡰࡲࠤࡩࡸࡩࡷࡧࡵࡷࠥ࡬࡯ࡳࠢ࡫ࡳࡴࡱ࡟ࡪࡰࡩࡳࡂࢁࡨࡰࡱ࡮ࡣ࡮ࡴࡦࡰࡿࠣࡥࡷ࡭ࡳ࠾ࡽࡤࡶ࡬ࡹࡽࠡ࡭ࡺࡥࡷ࡭ࡳ࠾ࠤᑥ") + str(kwargs) + bstack1ll_opy_ (u"ࠢࠣᑦ"))
            return {}
        if len(bstack1l1l1l1ll1l_opy_) > 1:
            self.logger.debug(bstack1ll_opy_ (u"ࠣࡱࡱࡣࡧ࡫ࡦࡰࡴࡨࡣࡹ࡫ࡳࡵ࠼ࠣࡿࡱ࡫࡮ࠩࡦࡵ࡭ࡻ࡫ࡲࡠ࡫ࡱࡷࡹࡧ࡮ࡤࡧࡶ࠭ࢂࠦࡤࡳ࡫ࡹࡩࡷࡹࠠࡧࡱࡵࠤ࡭ࡵ࡯࡬ࡡ࡬ࡲ࡫ࡵ࠽ࡼࡪࡲࡳࡰࡥࡩ࡯ࡨࡲࢁࠥࡧࡲࡨࡵࡀࡿࡦࡸࡧࡴࡿࠣ࡯ࡼࡧࡲࡨࡵࡀࠦᑧ") + str(kwargs) + bstack1ll_opy_ (u"ࠤࠥᑨ"))
            return {}
        bstack1l1l11111ll_opy_, bstack1l1l1111l11_opy_ = bstack1l1l1l1ll1l_opy_[0]
        driver = bstack1l1l11111ll_opy_()
        if not driver:
            self.logger.debug(bstack1ll_opy_ (u"ࠥࡳࡳࡥࡢࡦࡨࡲࡶࡪࡥࡴࡦࡵࡷ࠾ࠥࡴ࡯ࠡࡦࡵ࡭ࡻ࡫ࡲࠡࡨࡲࡶࠥ࡮࡯ࡰ࡭ࡢ࡭ࡳ࡬࡯࠾ࡽ࡫ࡳࡴࡱ࡟ࡪࡰࡩࡳࢂࠦࡡࡳࡩࡶࡁࢀࡧࡲࡨࡵࢀࠤࡰࡽࡡࡳࡩࡶࡁࠧᑩ") + str(kwargs) + bstack1ll_opy_ (u"ࠦࠧᑪ"))
            return {}
        capabilities = f.bstack1llll1l111l_opy_(bstack1l1l1111l11_opy_, bstack1ll1llll1l1_opy_.bstack1l11lllll1l_opy_)
        if not capabilities:
            self.logger.debug(bstack1ll_opy_ (u"ࠧࡵ࡮ࡠࡤࡨࡪࡴࡸࡥࡠࡶࡨࡷࡹࡀࠠ࡯ࡱࠣࡧࡦࡶࡡࡣ࡫࡯࡭ࡹ࡯ࡥࡴࠢࡩࡳࡺࡴࡤࠡࡨࡲࡶࠥ࡮࡯ࡰ࡭ࡢ࡭ࡳ࡬࡯࠾ࡽ࡫ࡳࡴࡱ࡟ࡪࡰࡩࡳࢂࠦࡡࡳࡩࡶࡁࢀࡧࡲࡨࡵࢀࠤࡰࡽࡡࡳࡩࡶࡁࠧᑫ") + str(kwargs) + bstack1ll_opy_ (u"ࠨࠢᑬ"))
            return {}
        return capabilities.get(bstack1ll_opy_ (u"ࠢࡢ࡮ࡺࡥࡾࡹࡍࡢࡶࡦ࡬ࠧᑭ"), {})
    def bstack1ll11l1111l_opy_(
        self,
        f: TestFramework,
        instance: bstack1ll1l1ll111_opy_,
        bstack1lllll11l1l_opy_: Tuple[bstack1ll1ll1lll1_opy_, bstack1ll1l1ll11l_opy_],
        *args,
        **kwargs
    ):
        bstack1l1l1l1ll1l_opy_ = f.bstack1llll1l111l_opy_(instance, bstack1ll1l1l1lll_opy_.bstack1l1ll1111ll_opy_, [])
        if not bstack1l1ll111lll_opy_() and len(bstack1l1l1l1ll1l_opy_) == 0:
            bstack1l1l1l1ll1l_opy_ = f.bstack1llll1l111l_opy_(instance, bstack1ll1l1l1lll_opy_.bstack1l11l1llll1_opy_, [])
        if not bstack1l1l1l1ll1l_opy_:
            self.logger.debug(bstack1ll_opy_ (u"ࠣࡩࡨࡸࡤࡧࡵࡵࡱࡰࡥࡹ࡯࡯࡯ࡡࡧࡶ࡮ࡼࡥࡳ࠼ࠣࡲࡴࠦࡤࡳ࡫ࡹࡩࡷࡹࠠࡧࡱࡵࠤ࡭ࡵ࡯࡬ࡡ࡬ࡲ࡫ࡵ࠽ࡼࡪࡲࡳࡰࡥࡩ࡯ࡨࡲࢁࠥࡧࡲࡨࡵࡀࡿࡦࡸࡧࡴࡿࠣ࡯ࡼࡧࡲࡨࡵࡀࠦᑮ") + str(kwargs) + bstack1ll_opy_ (u"ࠤࠥᑯ"))
            return
        if len(bstack1l1l1l1ll1l_opy_) > 1:
            self.logger.debug(bstack1ll_opy_ (u"ࠥ࡫ࡪࡺ࡟ࡢࡷࡷࡳࡲࡧࡴࡪࡱࡱࡣࡩࡸࡩࡷࡧࡵ࠾ࠥࢁ࡬ࡦࡰࠫࡨࡷ࡯ࡶࡦࡴࡢ࡭ࡳࡹࡴࡢࡰࡦࡩࡸ࠯ࡽࠡࡦࡵ࡭ࡻ࡫ࡲࡴࠢࡩࡳࡷࠦࡨࡰࡱ࡮ࡣ࡮ࡴࡦࡰ࠿ࡾ࡬ࡴࡵ࡫ࡠ࡫ࡱࡪࡴࢃࠠࡢࡴࡪࡷࡂࢁࡡࡳࡩࡶࢁࠥࡱࡷࡢࡴࡪࡷࡂࠨᑰ") + str(kwargs) + bstack1ll_opy_ (u"ࠦࠧᑱ"))
        bstack1l1l11111ll_opy_, bstack1l1l1111l11_opy_ = bstack1l1l1l1ll1l_opy_[0]
        driver = bstack1l1l11111ll_opy_()
        if not driver:
            self.logger.debug(bstack1ll_opy_ (u"ࠧ࡭ࡥࡵࡡࡤࡹࡹࡵ࡭ࡢࡶ࡬ࡳࡳࡥࡤࡳ࡫ࡹࡩࡷࡀࠠ࡯ࡱࠣࡨࡷ࡯ࡶࡦࡴࠣࡪࡴࡸࠠࡩࡱࡲ࡯ࡤ࡯࡮ࡧࡱࡀࡿ࡭ࡵ࡯࡬ࡡ࡬ࡲ࡫ࡵࡽࠡࡣࡵ࡫ࡸࡃࡻࡢࡴࡪࡷࢂࠦ࡫ࡸࡣࡵ࡫ࡸࡃࠢᑲ") + str(kwargs) + bstack1ll_opy_ (u"ࠨࠢᑳ"))
            return
        return driver