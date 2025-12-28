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
from datetime import datetime, timezone
from uuid import uuid4
from typing import Dict, List, Any, Tuple
from browserstack_sdk.sdk_cli.bstack1llll11l111_opy_ import bstack1llll1l1lll_opy_
from browserstack_sdk.sdk_cli.utils.bstack1l1111ll11_opy_ import bstack1l1111l1ll1_opy_
from browserstack_sdk.sdk_cli.test_framework import (
    TestFramework,
    bstack1ll1ll1lll1_opy_,
    bstack1ll1l1ll111_opy_,
    bstack1ll1l1ll11l_opy_,
    bstack1l1111l1l1l_opy_,
    bstack1ll1l111111_opy_,
)
from pathlib import Path
import grpc
from browserstack_sdk import sdk_pb2 as structs
from datetime import datetime, timezone
from typing import List, Dict, Any
import traceback
from bstack_utils.helper import bstack1l1l1l1l11l_opy_
from bstack_utils.bstack11ll1llll1_opy_ import bstack1lll1ll1l1l_opy_
from bstack_utils.constants import EVENTS
from browserstack_sdk.sdk_cli.bstack1lllll1ll1l_opy_ import bstack1lllll1l1l1_opy_
from browserstack_sdk.sdk_cli.utils.bstack1lll1ll1ll1_opy_ import bstack1lll1ll1111_opy_
from bstack_utils.bstack111ll1l1l1_opy_ import bstack1l11111lll_opy_
bstack1l1ll1111l1_opy_ = bstack1l1l1l1l11l_opy_()
bstack11llll1l1ll_opy_ = 1.0
bstack1l1l11llll1_opy_ = bstack1ll_opy_ (u"ࠤࡘࡴࡱࡵࡡࡥࡧࡧࡅࡹࡺࡡࡤࡪࡰࡩࡳࡺࡳ࠮ࠤᕁ")
bstack11lll11lll1_opy_ = bstack1ll_opy_ (u"ࠥࡘࡪࡹࡴࡍࡧࡹࡩࡱࠨᕂ")
bstack11lll1l1111_opy_ = bstack1ll_opy_ (u"ࠦࡇࡻࡩ࡭ࡦࡏࡩࡻ࡫࡬ࠣᕃ")
bstack11lll1l11ll_opy_ = bstack1ll_opy_ (u"ࠧࡎ࡯ࡰ࡭ࡏࡩࡻ࡫࡬ࠣᕄ")
bstack11lll1l11l1_opy_ = bstack1ll_opy_ (u"ࠨࡂࡶ࡫࡯ࡨࡑ࡫ࡶࡦ࡮ࡋࡳࡴࡱࡅࡷࡧࡱࡸࠧᕅ")
_1l1ll11111l_opy_ = set()
class bstack1lll1lll11l_opy_(TestFramework):
    bstack1l1111l1l11_opy_ = bstack1ll_opy_ (u"ࠢࡵࡧࡶࡸࡤ࡬ࡩࡹࡶࡸࡶࡪࡹࠢᕆ")
    bstack11llll11lll_opy_ = bstack1ll_opy_ (u"ࠣࡶࡨࡷࡹࡥࡨࡰࡱ࡮ࡷࡤࡹࡴࡢࡴࡷࡩࡩࠨᕇ")
    bstack1l1111llll1_opy_ = bstack1ll_opy_ (u"ࠤࡷࡩࡸࡺ࡟ࡩࡱࡲ࡯ࡸࡥࡦࡪࡰ࡬ࡷ࡭࡫ࡤࠣᕈ")
    bstack11llllll111_opy_ = bstack1ll_opy_ (u"ࠥࡸࡪࡹࡴࡠࡪࡲࡳࡰࡥ࡬ࡢࡵࡷࡣࡸࡺࡡࡳࡶࡨࡨࠧᕉ")
    bstack1l111111l11_opy_ = bstack1ll_opy_ (u"ࠦࡹ࡫ࡳࡵࡡ࡫ࡳࡴࡱ࡟࡭ࡣࡶࡸࡤ࡬ࡩ࡯࡫ࡶ࡬ࡪࡪࠢᕊ")
    bstack11llll1111l_opy_: bool
    bstack1lllll1ll1l_opy_: bstack1lllll1l1l1_opy_  = None
    bstack1ll1l11lll1_opy_ = None
    bstack11llll1llll_opy_ = [
        bstack1ll1ll1lll1_opy_.BEFORE_ALL,
        bstack1ll1ll1lll1_opy_.AFTER_ALL,
        bstack1ll1ll1lll1_opy_.BEFORE_EACH,
        bstack1ll1ll1lll1_opy_.AFTER_EACH,
    ]
    def __init__(
        self,
        bstack1l11111l111_opy_: Dict[str, str],
        bstack1ll1111lll1_opy_: List[str]=[bstack1ll_opy_ (u"ࠧࡶࡹࡵࡧࡶࡸࠧᕋ")],
        bstack1lllll1ll1l_opy_: bstack1lllll1l1l1_opy_=None,
        bstack1ll1l11lll1_opy_=None
    ):
        super().__init__(bstack1ll1111lll1_opy_, bstack1l11111l111_opy_, bstack1lllll1ll1l_opy_)
        self.bstack11llll1111l_opy_ = any(bstack1ll_opy_ (u"ࠨࡰࡺࡶࡨࡷࡹࠨᕌ") in item.lower() for item in bstack1ll1111lll1_opy_)
        self.bstack1ll1l11lll1_opy_ = bstack1ll1l11lll1_opy_
    def track_event(
        self,
        context: bstack1l1111l1l1l_opy_,
        test_framework_state: bstack1ll1ll1lll1_opy_,
        test_hook_state: bstack1ll1l1ll11l_opy_,
        *args,
        **kwargs,
    ):
        super().track_event(self, context, test_framework_state, test_hook_state, *args, **kwargs)
        if test_framework_state == bstack1ll1ll1lll1_opy_.TEST or test_framework_state in bstack1lll1lll11l_opy_.bstack11llll1llll_opy_:
            bstack1l1111l1ll1_opy_(test_framework_state, test_hook_state)
        if test_framework_state == bstack1ll1ll1lll1_opy_.NONE:
            self.logger.warning(bstack1ll_opy_ (u"ࠢࡪࡩࡱࡳࡷ࡫ࡤࠡࡥࡤࡰࡱࡨࡡࡤ࡭ࠣࡸࡪࡹࡴࡠࡨࡵࡥࡲ࡫ࡷࡰࡴ࡮ࡣࡸࡺࡡࡵࡧࡀࡿࡹ࡫ࡳࡵࡡࡩࡶࡦࡳࡥࡸࡱࡵ࡯ࡤࡹࡴࡢࡶࡨࢁࠥࡺࡥࡴࡶࡢ࡬ࡴࡵ࡫ࡠࡵࡷࡥࡹ࡫࠽ࠣᕍ") + str(test_hook_state) + bstack1ll_opy_ (u"ࠣࠤᕎ"))
            return
        if not self.bstack11llll1111l_opy_:
            self.logger.warning(bstack1ll_opy_ (u"ࠤࡷࡶࡦࡩ࡫ࡠࡧࡹࡩࡳࡺ࠺ࠡࡷࡱࡷࡺࡶࡰࡰࡴࡷࡩࡩࠦࡦࡳࡣࡰࡩࡼࡵࡲ࡬࠿ࠥᕏ") + str(str(self.bstack1ll1111lll1_opy_)) + bstack1ll_opy_ (u"ࠥࠦᕐ"))
            return
        if not isinstance(args, tuple) or len(args) == 0:
            self.logger.warning(bstack1ll_opy_ (u"ࠦࡹࡸࡡࡤ࡭ࡢࡩࡻ࡫࡮ࡵ࠼ࠣࡹࡳ࡫ࡸࡱࡧࡦࡸࡪࡪࠠࡢࡴࡪࡷࡂࢁࡡࡳࡩࡶࢁࠥࡱࡷࡢࡴࡪࡷࡂࠨᕑ") + str(kwargs) + bstack1ll_opy_ (u"ࠧࠨᕒ"))
            return
        instance = self.__1l1111l1lll_opy_(context, test_framework_state, test_hook_state, *args, **kwargs)
        if not instance:
            self.logger.debug(bstack1ll_opy_ (u"ࠨࡴࡳࡣࡦ࡯ࡤ࡫ࡶࡦࡰࡷ࠾ࠥࡻ࡮ࡩࡣࡱࡨࡱ࡫ࡤࠡࡧࡹࡩࡳࡺ࠽ࡼࡶࡨࡷࡹࡥࡦࡳࡣࡰࡩࡼࡵࡲ࡬ࡡࡶࡸࡦࡺࡥࡾ࠰ࡾࡸࡪࡹࡴࡠࡪࡲࡳࡰࡥࡳࡵࡣࡷࡩࢂࠦࡡࡳࡩࡶࡁࠧᕓ") + str(args) + bstack1ll_opy_ (u"ࠢࠣᕔ"))
            return
        try:
            if instance!= None and test_framework_state in bstack1lll1lll11l_opy_.bstack11llll1llll_opy_ and test_hook_state == bstack1ll1l1ll11l_opy_.PRE:
                bstack1ll11l11l1l_opy_ = bstack1lll1ll1l1l_opy_.bstack1ll1111ll11_opy_(EVENTS.bstack1ll1llll11_opy_.value)
                name = str(EVENTS.bstack1ll1llll11_opy_.name)+bstack1ll_opy_ (u"ࠣ࠼ࠥᕕ")+str(test_framework_state.name)
                TestFramework.bstack11llll111ll_opy_(instance, name, bstack1ll11l11l1l_opy_)
        except Exception as e:
            self.logger.debug(bstack1ll_opy_ (u"ࠤࡈࡼࡨ࡫ࡰࡵ࡫ࡲࡲࠥ࡯࡮ࠡࡪࡲࡳࡰࠦࡥࡳࡴࡲࡶࠥࡶࡲࡦ࠼ࠣࡿࢂࠨᕖ").format(e))
        try:
            if not TestFramework.bstack1llll11ll11_opy_(instance, TestFramework.bstack11llllll1ll_opy_) and test_hook_state == bstack1ll1l1ll11l_opy_.PRE:
                test = bstack1lll1lll11l_opy_.__1l11111l1ll_opy_(args[0])
                if test:
                    instance.data.update(test)
                    self.logger.debug(bstack1ll_opy_ (u"ࠥࡰࡴࡧࡤࡦࡦࠣ࡭ࡳࡹࡴࡢࡰࡦࡩࡂࢁࡩ࡯ࡵࡷࡥࡳࡩࡥ࠯ࡴࡨࡪ࠭࠯ࡽࠡࡧࡹࡩࡳࡺ࠽ࡼࡶࡨࡷࡹࡥࡦࡳࡣࡰࡩࡼࡵࡲ࡬ࡡࡶࡸࡦࡺࡥࡾ࠰ࠥᕗ") + str(test_hook_state) + bstack1ll_opy_ (u"ࠦࠧᕘ"))
            if test_framework_state == bstack1ll1ll1lll1_opy_.TEST:
                if test_hook_state == bstack1ll1l1ll11l_opy_.PRE and not TestFramework.bstack1llll11ll11_opy_(instance, TestFramework.bstack1l1l1llll11_opy_):
                    TestFramework.bstack1llll1lll11_opy_(instance, TestFramework.bstack1l1l1llll11_opy_, datetime.now(tz=timezone.utc))
                    self.logger.debug(bstack1ll_opy_ (u"ࠧࡹࡥࡵࠢࡷࡩࡸࡺ࠭ࡴࡶࡤࡶࡹࠦࡦࡰࡴࠣ࡭ࡳࡹࡴࡢࡰࡦࡩࡂࢁࡩ࡯ࡵࡷࡥࡳࡩࡥ࠯ࡴࡨࡪ࠭࠯ࡽࠡࡧࡹࡩࡳࡺ࠽ࡼࡶࡨࡷࡹࡥࡦࡳࡣࡰࡩࡼࡵࡲ࡬ࡡࡶࡸࡦࡺࡥࡾ࠰ࠥᕙ") + str(test_hook_state) + bstack1ll_opy_ (u"ࠨࠢᕚ"))
                elif test_hook_state == bstack1ll1l1ll11l_opy_.POST and not TestFramework.bstack1llll11ll11_opy_(instance, TestFramework.bstack1l1ll11l1l1_opy_):
                    TestFramework.bstack1llll1lll11_opy_(instance, TestFramework.bstack1l1ll11l1l1_opy_, datetime.now(tz=timezone.utc))
                    self.logger.debug(bstack1ll_opy_ (u"ࠢࡴࡧࡷࠤࡹ࡫ࡳࡵ࠯ࡨࡲࡩࠦࡦࡰࡴࠣ࡭ࡳࡹࡴࡢࡰࡦࡩࡂࢁࡩ࡯ࡵࡷࡥࡳࡩࡥ࠯ࡴࡨࡪ࠭࠯ࡽࠡࡧࡹࡩࡳࡺ࠽ࡼࡶࡨࡷࡹࡥࡦࡳࡣࡰࡩࡼࡵࡲ࡬ࡡࡶࡸࡦࡺࡥࡾ࠰ࠥᕛ") + str(test_hook_state) + bstack1ll_opy_ (u"ࠣࠤᕜ"))
            elif test_framework_state == bstack1ll1ll1lll1_opy_.LOG and test_hook_state == bstack1ll1l1ll11l_opy_.POST:
                bstack1lll1lll11l_opy_.__1l1111l111l_opy_(instance, *args)
            elif test_framework_state == bstack1ll1ll1lll1_opy_.LOG_REPORT and test_hook_state == bstack1ll1l1ll11l_opy_.POST:
                self.__11llll1lll1_opy_(instance, *args)
                self.__1l111111lll_opy_(instance)
            elif test_framework_state in bstack1lll1lll11l_opy_.bstack11llll1llll_opy_:
                self.__11lll1lll1l_opy_(instance, test_framework_state, test_hook_state, *args)
            self.logger.debug(bstack1ll_opy_ (u"ࠤࡷࡶࡦࡩ࡫ࡠࡧࡹࡩࡳࡺ࠺ࠡࡪࡤࡲࡩࡲࡥࡥࠢࡨࡺࡪࡴࡴ࠾ࡽࡷࡩࡸࡺ࡟ࡧࡴࡤࡱࡪࡽ࡯ࡳ࡭ࡢࡷࡹࡧࡴࡦࡿ࠱ࡿࡹ࡫ࡳࡵࡡ࡫ࡳࡴࡱ࡟ࡴࡶࡤࡸࡪࢃࠠࡪࡰࡶࡸࡦࡴࡣࡦ࠿ࠥᕝ") + str(instance.ref()) + bstack1ll_opy_ (u"ࠥࠦᕞ"))
        except Exception as e:
            self.logger.error(e)
            traceback.print_exc()
        self.bstack11llllll1l1_opy_(instance, (test_framework_state, test_hook_state), *args, **kwargs)
        try:
            if instance!= None and test_framework_state in bstack1lll1lll11l_opy_.bstack11llll1llll_opy_ and test_hook_state == bstack1ll1l1ll11l_opy_.POST:
                name = str(EVENTS.bstack1ll1llll11_opy_.name)+bstack1ll_opy_ (u"ࠦ࠿ࠨᕟ")+str(test_framework_state.name)
                bstack1ll11l11l1l_opy_ = TestFramework.bstack1l1111lllll_opy_(instance, name)
                bstack1lll1ll1l1l_opy_.end(EVENTS.bstack1ll1llll11_opy_.value, bstack1ll11l11l1l_opy_+bstack1ll_opy_ (u"ࠧࡀࡳࡵࡣࡵࡸࠧᕠ"), bstack1ll11l11l1l_opy_+bstack1ll_opy_ (u"ࠨ࠺ࡦࡰࡧࠦᕡ"), True, None, test_framework_state.name)
        except Exception as e:
            self.logger.debug(bstack1ll_opy_ (u"ࠢࡆࡺࡦࡩࡵࡺࡩࡰࡰࠣ࡭ࡳࠦࡨࡰࡱ࡮ࠤࡪࡸࡲࡰࡴ࠽ࠤࢀࢃࠢᕢ").format(e))
    def bstack1l1l11l1l1l_opy_(self):
        return self.bstack11llll1111l_opy_
    def __1l11111l1l1_opy_(self, *args):
        if len(args) > 2 and callable(getattr(args[2], bstack1ll_opy_ (u"ࠣࡩࡨࡸࡤࡸࡥࡴࡷ࡯ࡸࠧᕣ"), None)):
            rep = args[2].get_result()
            if rep:
                return TestFramework.bstack1l1l11lll11_opy_(rep, [bstack1ll_opy_ (u"ࠤࡺ࡬ࡪࡴࠢᕤ"), bstack1ll_opy_ (u"ࠥࡳࡺࡺࡣࡰ࡯ࡨࠦᕥ"), bstack1ll_opy_ (u"ࠦࡵࡧࡳࡴࡧࡧࠦᕦ"), bstack1ll_opy_ (u"ࠧ࡬ࡡࡪ࡮ࡨࡨࠧᕧ"), bstack1ll_opy_ (u"ࠨࡳ࡬࡫ࡳࡴࡪࡪࠢᕨ"), bstack1ll_opy_ (u"ࠢ࡭ࡱࡱ࡫ࡷ࡫ࡰࡳࡶࡨࡼࡹࠨᕩ")])
        return None
    def __11llll1lll1_opy_(self, instance: bstack1ll1l1ll111_opy_, *args):
        result = self.__1l11111l1l1_opy_(*args)
        if not result:
            return
        failure = None
        bstack1llllll1111_opy_ = None
        if result.get(bstack1ll_opy_ (u"ࠣࡱࡸࡸࡨࡵ࡭ࡦࠤᕪ"), None) == bstack1ll_opy_ (u"ࠤࡩࡥ࡮ࡲࡥࡥࠤᕫ") and len(args) > 1 and getattr(args[1], bstack1ll_opy_ (u"ࠥࡩࡽࡩࡩ࡯ࡨࡲࠦᕬ"), None) is not None:
            failure = [{bstack1ll_opy_ (u"ࠫࡧࡧࡣ࡬ࡶࡵࡥࡨ࡫ࠧᕭ"): [args[1].excinfo.exconly(), result.get(bstack1ll_opy_ (u"ࠧࡲ࡯࡯ࡩࡵࡩࡵࡸࡴࡦࡺࡷࠦᕮ"), None)]}]
            bstack1llllll1111_opy_ = bstack1ll_opy_ (u"ࠨࡁࡴࡵࡨࡶࡹ࡯࡯࡯ࡇࡵࡶࡴࡸࠢᕯ") if bstack1ll_opy_ (u"ࠢࡂࡵࡶࡩࡷࡺࡩࡰࡰࠥᕰ") in getattr(args[1].excinfo, bstack1ll_opy_ (u"ࠣࡶࡼࡴࡪࡴࡡ࡮ࡧࠥᕱ"), bstack1ll_opy_ (u"ࠤࠥᕲ")) else bstack1ll_opy_ (u"࡙ࠥࡳ࡮ࡡ࡯ࡦ࡯ࡩࡩࡋࡲࡳࡱࡵࠦᕳ")
        bstack11lll1ll1ll_opy_ = result.get(bstack1ll_opy_ (u"ࠦࡴࡻࡴࡤࡱࡰࡩࠧᕴ"), TestFramework.bstack1l11111111l_opy_)
        if bstack11lll1ll1ll_opy_ != TestFramework.bstack1l11111111l_opy_:
            TestFramework.bstack1llll1lll11_opy_(instance, TestFramework.bstack1l1l1l11ll1_opy_, datetime.now(tz=timezone.utc))
        TestFramework.bstack11llll1l11l_opy_(instance, {
            TestFramework.bstack1l11ll11l11_opy_: failure,
            TestFramework.bstack1l111l11l1l_opy_: bstack1llllll1111_opy_,
            TestFramework.bstack1l11l1ll11l_opy_: bstack11lll1ll1ll_opy_,
        })
    def __1l1111l1lll_opy_(
        self,
        context: bstack1l1111l1l1l_opy_,
        test_framework_state: bstack1ll1ll1lll1_opy_,
        test_hook_state: bstack1ll1l1ll11l_opy_,
        *args,
        **kwargs,
    ):
        instance = None
        if test_framework_state == bstack1ll1ll1lll1_opy_.SETUP_FIXTURE:
            instance = self.__1l111111l1l_opy_(context, test_framework_state, test_hook_state, *args, **kwargs)
        else:
            target = None # bstack11llll1l1l1_opy_ bstack1l11111ll1l_opy_ this to be bstack1ll_opy_ (u"ࠧࡴ࡯ࡥࡧ࡬ࡨࠧᕵ")
            if test_framework_state == bstack1ll1ll1lll1_opy_.INIT_TEST:
                target = args[0] if isinstance(args[0], str) else None
                if target:
                    self.__11lllll1111_opy_(context, test_framework_state, target, *args)
            elif test_framework_state == bstack1ll1ll1lll1_opy_.LOG:
                nodeid = getattr(getattr(args[0], bstack1ll_opy_ (u"ࠨ࡮ࡰࡦࡨࠦᕶ"), None), bstack1ll_opy_ (u"ࠢ࡯ࡱࡧࡩ࡮ࡪࠢᕷ"), None) if args else None
                if isinstance(nodeid, str):
                    target = nodeid
            elif getattr(args[0], bstack1ll_opy_ (u"ࠣࡰࡲࡨࡪ࡯ࡤࠣᕸ"), None):
                target = args[0].nodeid
            instance = TestFramework.bstack1llll11111l_opy_(target) if target else None
        return instance
    def __11lll1lll1l_opy_(
        self,
        instance: bstack1ll1l1ll111_opy_,
        test_framework_state: bstack1ll1ll1lll1_opy_,
        test_hook_state: bstack1ll1l1ll11l_opy_,
        *args,
    ):
        key = test_framework_state.name
        bstack1l1111111l1_opy_ = TestFramework.bstack1llll1l111l_opy_(instance, bstack1lll1lll11l_opy_.bstack11llll11lll_opy_, {})
        if not key in bstack1l1111111l1_opy_:
            bstack1l1111111l1_opy_[key] = []
        bstack11lll1lll11_opy_ = TestFramework.bstack1llll1l111l_opy_(instance, bstack1lll1lll11l_opy_.bstack1l1111llll1_opy_, {})
        if not key in bstack11lll1lll11_opy_:
            bstack11lll1lll11_opy_[key] = []
        bstack11llllllll1_opy_ = {
            bstack1lll1lll11l_opy_.bstack11llll11lll_opy_: bstack1l1111111l1_opy_,
            bstack1lll1lll11l_opy_.bstack1l1111llll1_opy_: bstack11lll1lll11_opy_,
        }
        if test_hook_state == bstack1ll1l1ll11l_opy_.PRE:
            hook = {
                bstack1ll_opy_ (u"ࠤ࡮ࡩࡾࠨᕹ"): key,
                TestFramework.bstack11llll11111_opy_: uuid4().__str__(),
                TestFramework.bstack11lllll1l1l_opy_: TestFramework.bstack11lllll11ll_opy_,
                TestFramework.bstack11lllll1lll_opy_: datetime.now(tz=timezone.utc),
                TestFramework.bstack11lllll11l1_opy_: [],
                TestFramework.bstack1l1111ll111_opy_: args[1] if len(args) > 1 else bstack1ll_opy_ (u"ࠪࠫᕺ"),
                TestFramework.bstack1l111l11l11_opy_: bstack1lll1ll1111_opy_.bstack11lll1ll111_opy_()
            }
            bstack1l1111111l1_opy_[key].append(hook)
            bstack11llllllll1_opy_[bstack1lll1lll11l_opy_.bstack11llllll111_opy_] = key
        elif test_hook_state == bstack1ll1l1ll11l_opy_.POST:
            bstack11lll1l1lll_opy_ = bstack1l1111111l1_opy_.get(key, [])
            hook = bstack11lll1l1lll_opy_.pop() if bstack11lll1l1lll_opy_ else None
            if hook:
                result = self.__1l11111l1l1_opy_(*args)
                if result:
                    bstack1l1111lll1l_opy_ = result.get(bstack1ll_opy_ (u"ࠦࡴࡻࡴࡤࡱࡰࡩࠧᕻ"), TestFramework.bstack11lllll11ll_opy_)
                    if bstack1l1111lll1l_opy_ != TestFramework.bstack11lllll11ll_opy_:
                        hook[TestFramework.bstack11lllll1l1l_opy_] = bstack1l1111lll1l_opy_
                hook[TestFramework.bstack1l1111ll11l_opy_] = datetime.now(tz=timezone.utc)
                hook[TestFramework.bstack1l111l11l11_opy_]= bstack1lll1ll1111_opy_.bstack11lll1ll111_opy_()
                self.bstack11lllllll11_opy_(hook)
                logs = hook.get(TestFramework.bstack11lllllllll_opy_, [])
                if logs: self.bstack1l1l11ll11l_opy_(instance, logs)
                bstack11lll1lll11_opy_[key].append(hook)
                bstack11llllllll1_opy_[bstack1lll1lll11l_opy_.bstack1l111111l11_opy_] = key
        TestFramework.bstack11llll1l11l_opy_(instance, bstack11llllllll1_opy_)
        self.logger.debug(bstack1ll_opy_ (u"ࠧࡺࡲࡢࡥ࡮ࡣ࡭ࡵ࡯࡬ࡡࡨࡺࡪࡴࡴ࠻ࠢࡷࡩࡸࡺ࡟ࡩࡱࡲ࡯ࡤࡹࡴࡢࡶࡨࡁࢀࡱࡥࡺࡿ࠱ࡿࡹ࡫ࡳࡵࡡ࡫ࡳࡴࡱ࡟ࡴࡶࡤࡸࡪࢃࠠࡩࡱࡲ࡯ࡸࡥࡳࡵࡣࡵࡸࡪࡪ࠽ࡼࡪࡲࡳࡰࡹ࡟ࡴࡶࡤࡶࡹ࡫ࡤࡾࠢ࡫ࡳࡴࡱࡳࡠࡨ࡬ࡲ࡮ࡹࡨࡦࡦࡀࠦᕼ") + str(bstack11lll1lll11_opy_) + bstack1ll_opy_ (u"ࠨࠢᕽ"))
    def __1l111111l1l_opy_(
        self,
        context: bstack1l1111l1l1l_opy_,
        test_framework_state: bstack1ll1ll1lll1_opy_,
        test_hook_state: bstack1ll1l1ll11l_opy_,
        *args,
        **kwargs,
    ):
        fixturedef = TestFramework.bstack1l1l11lll11_opy_(args[0], [bstack1ll_opy_ (u"ࠢࡴࡥࡲࡴࡪࠨᕾ"), bstack1ll_opy_ (u"ࠣࡣࡵ࡫ࡳࡧ࡭ࡦࠤᕿ"), bstack1ll_opy_ (u"ࠤࡳࡥࡷࡧ࡭ࡴࠤᖀ"), bstack1ll_opy_ (u"ࠥ࡭ࡩࡹࠢᖁ"), bstack1ll_opy_ (u"ࠦࡺࡴࡩࡵࡶࡨࡷࡹࠨᖂ"), bstack1ll_opy_ (u"ࠧࡨࡡࡴࡧ࡬ࡨࠧᖃ")]) if len(args) > 0 else {}
        request = args[1] if len(args) > 1 else None
        scope = request.scope if hasattr(request, bstack1ll_opy_ (u"ࠨࡳࡤࡱࡳࡩࠧᖄ")) else fixturedef.get(bstack1ll_opy_ (u"ࠢࡴࡥࡲࡴࡪࠨᖅ"), None)
        fixturename = request.fixturename if hasattr(request, bstack1ll_opy_ (u"ࠣࡨ࡬ࡼࡹࡻࡲࡦࡰࡤࡱࡪࠨᖆ")) else None
        node = request.node if hasattr(request, bstack1ll_opy_ (u"ࠤࡱࡳࡩ࡫ࠢᖇ")) else None
        target = request.node.nodeid if hasattr(node, bstack1ll_opy_ (u"ࠥࡲࡴࡪࡥࡪࡦࠥᖈ")) else None
        baseid = fixturedef.get(bstack1ll_opy_ (u"ࠦࡧࡧࡳࡦ࡫ࡧࠦᖉ"), None) or bstack1ll_opy_ (u"ࠧࠨᖊ")
        if (not target or len(baseid) > 0) and hasattr(request, bstack1ll_opy_ (u"ࠨ࡟ࡱࡻࡩࡹࡳࡩࡩࡵࡧࡰࠦᖋ")):
            target = bstack1lll1lll11l_opy_.__1l1111ll1ll_opy_(request._pyfuncitem.location) if hasattr(request._pyfuncitem, bstack1ll_opy_ (u"ࠢ࡭ࡱࡦࡥࡹ࡯࡯࡯ࠤᖌ")) else None
            if target and not TestFramework.bstack1llll11111l_opy_(target):
                self.__11lllll1111_opy_(context, test_framework_state, target, (target, request._pyfuncitem.location))
                node = request._pyfuncitem
                self.logger.debug(bstack1ll_opy_ (u"ࠣࡶࡵࡥࡨࡱ࡟ࡧ࡫ࡻࡸࡺࡸࡥࡠࡧࡹࡩࡳࡺ࠺ࠡࡨࡤࡰࡱࡨࡡࡤ࡭ࠣࡸࡦࡸࡧࡦࡶࡀࡿࡹࡧࡲࡨࡧࡷࢁࠥ࡬ࡩࡹࡶࡸࡶࡪࡴࡡ࡮ࡧࡀࡿ࡫࡯ࡸࡵࡷࡵࡩࡳࡧ࡭ࡦࡿࠣࡲࡴࡪࡥ࠾ࡽࡱࡳࡩ࡫ࡽࠡࡧࡹࡩࡳࡺ࠽ࡼࡶࡨࡷࡹࡥࡦࡳࡣࡰࡩࡼࡵࡲ࡬ࡡࡶࡸࡦࡺࡥࡾ࠰ࠥᖍ") + str(test_hook_state) + bstack1ll_opy_ (u"ࠤࠥᖎ"))
        if not fixturedef or not scope or not target:
            self.logger.warning(bstack1ll_opy_ (u"ࠥࡸࡷࡧࡣ࡬ࡡࡩ࡭ࡽࡺࡵࡳࡧࡢࡩࡻ࡫࡮ࡵ࠼ࠣࡹࡳ࡮ࡡ࡯ࡦ࡯ࡩࡩࠦࡥࡷࡧࡱࡸࡂࢁࡴࡦࡵࡷࡣ࡫ࡸࡡ࡮ࡧࡺࡳࡷࡱ࡟ࡴࡶࡤࡸࡪࢃ࠮ࡼࡶࡨࡷࡹࡥࡨࡰࡱ࡮ࡣࡸࡺࡡࡵࡧࢀࠤ࡫࡯ࡸࡵࡷࡵࡩࡩ࡫ࡦ࠾ࡽࡩ࡭ࡽࡺࡵࡳࡧࡧࡩ࡫ࢃࠠࡴࡥࡲࡴࡪࡃࡻࡴࡥࡲࡴࡪࢃࠠࡵࡣࡵ࡫ࡪࡺ࠽ࠣᖏ") + str(target) + bstack1ll_opy_ (u"ࠦࠧᖐ"))
            return None
        instance = TestFramework.bstack1llll11111l_opy_(target)
        if not instance:
            self.logger.warning(bstack1ll_opy_ (u"ࠧࡺࡲࡢࡥ࡮ࡣ࡫࡯ࡸࡵࡷࡵࡩࡤ࡫ࡶࡦࡰࡷ࠾ࠥࡻ࡮ࡩࡣࡱࡨࡱ࡫ࡤࠡࡧࡹࡩࡳࡺ࠽ࡼࡶࡨࡷࡹࡥࡦࡳࡣࡰࡩࡼࡵࡲ࡬ࡡࡶࡸࡦࡺࡥࡾ࠰ࡾࡸࡪࡹࡴࡠࡪࡲࡳࡰࡥࡳࡵࡣࡷࡩࢂࠦࡦࡪࡺࡷࡹࡷ࡫࡮ࡢ࡯ࡨࡁࢀ࡬ࡩࡹࡶࡸࡶࡪࡴࡡ࡮ࡧࢀࠤࡸࡩ࡯ࡱࡧࡀࡿࡸࡩ࡯ࡱࡧࢀࠤࡧࡧࡳࡦ࡫ࡧࡁࢀࡨࡡࡴࡧ࡬ࡨࢂࠦࡴࡢࡴࡪࡩࡹࡃࠢᖑ") + str(target) + bstack1ll_opy_ (u"ࠨࠢᖒ"))
            return None
        bstack11llll1l111_opy_ = TestFramework.bstack1llll1l111l_opy_(instance, bstack1lll1lll11l_opy_.bstack1l1111l1l11_opy_, {})
        if os.getenv(bstack1ll_opy_ (u"ࠢࡔࡆࡎࡣࡈࡒࡉࡠࡈࡏࡅࡌࡥࡆࡊ࡚ࡗ࡙ࡗࡋࡓࠣᖓ"), bstack1ll_opy_ (u"ࠣ࠳ࠥᖔ")) == bstack1ll_opy_ (u"ࠤ࠴ࠦᖕ"):
            bstack11lll1llll1_opy_ = bstack1ll_opy_ (u"ࠥ࠾ࠧᖖ").join((scope, fixturename))
            bstack11llll1ll11_opy_ = datetime.now(tz=timezone.utc)
            bstack11lllll111l_opy_ = {
                bstack1ll_opy_ (u"ࠦࡰ࡫ࡹࠣᖗ"): bstack11lll1llll1_opy_,
                bstack1ll_opy_ (u"ࠧࡺࡡࡨࡵࠥᖘ"): bstack1lll1lll11l_opy_.__1l111l11111_opy_(request.node),
                bstack1ll_opy_ (u"ࠨࡦࡪࡺࡷࡹࡷ࡫ࠢᖙ"): fixturedef,
                bstack1ll_opy_ (u"ࠢࡴࡥࡲࡴࡪࠨᖚ"): scope,
                bstack1ll_opy_ (u"ࠣࡶࡼࡴࡪࠨᖛ"): None,
            }
            try:
                if test_hook_state == bstack1ll1l1ll11l_opy_.POST and callable(getattr(args[-1], bstack1ll_opy_ (u"ࠤࡪࡩࡹࡥࡲࡦࡵࡸࡰࡹࠨᖜ"), None)):
                    bstack11lllll111l_opy_[bstack1ll_opy_ (u"ࠥࡸࡾࡶࡥࠣᖝ")] = TestFramework.bstack1l1ll111ll1_opy_(args[-1].get_result())
            except Exception as e:
                pass
            if test_hook_state == bstack1ll1l1ll11l_opy_.PRE:
                bstack11lllll111l_opy_[bstack1ll_opy_ (u"ࠦࡺࡻࡩࡥࠤᖞ")] = uuid4().__str__()
                bstack11lllll111l_opy_[bstack1lll1lll11l_opy_.bstack11lllll1lll_opy_] = bstack11llll1ll11_opy_
            elif test_hook_state == bstack1ll1l1ll11l_opy_.POST:
                bstack11lllll111l_opy_[bstack1lll1lll11l_opy_.bstack1l1111ll11l_opy_] = bstack11llll1ll11_opy_
            if bstack11lll1llll1_opy_ in bstack11llll1l111_opy_:
                bstack11llll1l111_opy_[bstack11lll1llll1_opy_].update(bstack11lllll111l_opy_)
                self.logger.debug(bstack1ll_opy_ (u"ࠧࡻࡰࡥࡣࡷࡩࡩࠦࡦࡪࡺࡷࡹࡷ࡫࡮ࡢ࡯ࡨࡁࢀ࡬ࡩࡹࡶࡸࡶࡪࡴࡡ࡮ࡧࢀࠤࡸࡩ࡯ࡱࡧࡀࡿࡸࡩ࡯ࡱࡧࢀࠤ࡫࡯ࡸࡵࡷࡵࡩࡂࠨᖟ") + str(bstack11llll1l111_opy_[bstack11lll1llll1_opy_]) + bstack1ll_opy_ (u"ࠨࠢᖠ"))
            else:
                bstack11llll1l111_opy_[bstack11lll1llll1_opy_] = bstack11lllll111l_opy_
                self.logger.debug(bstack1ll_opy_ (u"ࠢࡴࡣࡹࡩࡩࠦࡦࡪࡺࡷࡹࡷ࡫࡮ࡢ࡯ࡨࡁࢀ࡬ࡩࡹࡶࡸࡶࡪࡴࡡ࡮ࡧࢀࠤࡸࡩ࡯ࡱࡧࡀࡿࡸࡩ࡯ࡱࡧࢀࠤ࡫࡯ࡸࡵࡷࡵࡩࡂࢁࡴࡦࡵࡷࡣ࡫࡯ࡸࡵࡷࡵࡩࢂࠦࡴࡳࡣࡦ࡯ࡪࡪ࡟ࡧ࡫ࡻࡸࡺࡸࡥࡴ࠿ࠥᖡ") + str(len(bstack11llll1l111_opy_)) + bstack1ll_opy_ (u"ࠣࠤᖢ"))
        TestFramework.bstack1llll1lll11_opy_(instance, bstack1lll1lll11l_opy_.bstack1l1111l1l11_opy_, bstack11llll1l111_opy_)
        self.logger.debug(bstack1ll_opy_ (u"ࠤࡶࡥࡻ࡫ࡤࠡࡨ࡬ࡼࡹࡻࡲࡦࡵࡀࡿࡱ࡫࡮ࠩࡶࡵࡥࡨࡱࡥࡥࡡࡩ࡭ࡽࡺࡵࡳࡧࡶ࠭ࢂࠦࡩ࡯ࡵࡷࡥࡳࡩࡥ࠾ࠤᖣ") + str(instance.ref()) + bstack1ll_opy_ (u"ࠥࠦᖤ"))
        return instance
    def __11lllll1111_opy_(
        self,
        context: bstack1l1111l1l1l_opy_,
        test_framework_state: bstack1ll1ll1lll1_opy_,
        target: Any,
        *args,
    ):
        ctx = bstack1llll1l1lll_opy_.create_context(target)
        ob = bstack1ll1l1ll111_opy_(ctx, self.bstack1ll1111lll1_opy_, self.bstack1l11111l111_opy_, test_framework_state)
        TestFramework.bstack11llll1l11l_opy_(ob, {
            TestFramework.bstack1l1lll1lll1_opy_: context.test_framework_name,
            TestFramework.bstack1l1l11l11ll_opy_: context.test_framework_version,
            TestFramework.bstack1l1111lll11_opy_: [],
            bstack1lll1lll11l_opy_.bstack1l1111l1l11_opy_: {},
            bstack1lll1lll11l_opy_.bstack1l1111llll1_opy_: {},
            bstack1lll1lll11l_opy_.bstack11llll11lll_opy_: {},
        })
        if len(args) > 1 and isinstance(args[1], tuple):
            TestFramework.bstack1llll1lll11_opy_(ob, TestFramework.bstack1l111l1111l_opy_, str(args[1][0]))
        if context.platform_index >= 0:
            TestFramework.bstack1llll1lll11_opy_(ob, TestFramework.bstack1l1lll1l1ll_opy_, context.platform_index)
        TestFramework.bstack1lllll111ll_opy_[ctx.id] = ob
        self.logger.debug(bstack1ll_opy_ (u"ࠦࡸࡧࡶࡦࡦࠣ࡭ࡳࡹࡴࡢࡰࡦࡩࠥࡩࡴࡹ࠰࡬ࡨࡂࢁࡣࡵࡺ࠱࡭ࡩࢃࠠࡵࡣࡵ࡫ࡪࡺ࠽ࡼࡶࡤࡶ࡬࡫ࡴࡾࠢࡤࡶ࡬ࡹ࠽ࡼࡣࡵ࡫ࡸࢃࠠࡪࡰࡶࡸࡦࡴࡣࡦࡵࡀࠦᖥ") + str(TestFramework.bstack1lllll111ll_opy_.keys()) + bstack1ll_opy_ (u"ࠧࠨᖦ"))
        return ob
    def bstack1l1l11l1ll1_opy_(self, instance: bstack1ll1l1ll111_opy_, bstack1lllll11l1l_opy_: Tuple[bstack1ll1ll1lll1_opy_, bstack1ll1l1ll11l_opy_]):
        bstack11llll11l11_opy_ = (
            bstack1lll1lll11l_opy_.bstack11llllll111_opy_
            if bstack1lllll11l1l_opy_[1] == bstack1ll1l1ll11l_opy_.PRE
            else bstack1lll1lll11l_opy_.bstack1l111111l11_opy_
        )
        hook = bstack1lll1lll11l_opy_.bstack11lll1l1l11_opy_(instance, bstack11llll11l11_opy_)
        entries = hook.get(TestFramework.bstack11lllll11l1_opy_, []) if isinstance(hook, dict) else []
        entries.extend(TestFramework.bstack1llll1l111l_opy_(instance, TestFramework.bstack1l1111lll11_opy_, []))
        return entries
    def bstack1l1l1ll1111_opy_(self, instance: bstack1ll1l1ll111_opy_, bstack1lllll11l1l_opy_: Tuple[bstack1ll1ll1lll1_opy_, bstack1ll1l1ll11l_opy_]):
        bstack11llll11l11_opy_ = (
            bstack1lll1lll11l_opy_.bstack11llllll111_opy_
            if bstack1lllll11l1l_opy_[1] == bstack1ll1l1ll11l_opy_.PRE
            else bstack1lll1lll11l_opy_.bstack1l111111l11_opy_
        )
        bstack1lll1lll11l_opy_.bstack1l1111111ll_opy_(instance, bstack11llll11l11_opy_)
        TestFramework.bstack1llll1l111l_opy_(instance, TestFramework.bstack1l1111lll11_opy_, []).clear()
    def bstack11lllllll11_opy_(self, hook: Dict[str, Any]) -> None:
        bstack1ll_opy_ (u"ࠨࠢࠣࠌࠣࠤࠥࠦࠠࠡࠢࠣࡔࡷࡵࡣࡦࡵࡶࡩࡸࠦࡴࡩࡧࠣࡌࡴࡵ࡫ࡍࡧࡹࡩࡱࠦࡡࡵࡶࡤࡧ࡭ࡳࡥ࡯ࡶࡶࠤࡸ࡯࡭ࡪ࡮ࡤࡶࠥࡺ࡯ࠡࡶ࡫ࡩࠥࡐࡡࡷࡣࠣ࡭ࡲࡶ࡬ࡦ࡯ࡨࡲࡹࡧࡴࡪࡱࡱ࠲ࠏࠦࠠࠡࠢࠣࠤࠥࠦࡔࡩ࡫ࡶࠤࡲ࡫ࡴࡩࡱࡧ࠾ࠏࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡ࠯ࠣࡇ࡭࡫ࡣ࡬ࡵࠣࡸ࡭࡫ࠠࡉࡱࡲ࡯ࡑ࡫ࡶࡦ࡮ࠣࡨ࡮ࡸࡥࡤࡶࡲࡶࡾࠦࡩ࡯ࡵ࡬ࡨࡪࠦࡾ࠰࠰ࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫࠰ࡗࡳࡰࡴࡧࡤࡦࡦࡄࡸࡹࡧࡣࡩ࡯ࡨࡲࡹࡹ࠮ࠋࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤ࠲ࠦࡆࡰࡴࠣࡩࡦࡩࡨࠡࡨ࡬ࡰࡪࠦࡩ࡯ࠢ࡫ࡳࡴࡱ࡟࡭ࡧࡹࡩࡱࡥࡦࡪ࡮ࡨࡷ࠱ࠦࡲࡦࡲ࡯ࡥࡨ࡫ࡳࠡࠤࡗࡩࡸࡺࡌࡦࡸࡨࡰࠧࠦࡷࡪࡶ࡫ࠤࠧࡎ࡯ࡰ࡭ࡏࡩࡻ࡫࡬ࠣࠢ࡬ࡲࠥ࡯ࡴࡴࠢࡳࡥࡹ࡮࠮ࠋࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤ࠲ࠦࡉࡧࠢࡤࠤ࡫࡯࡬ࡦࠢ࡬ࡲࠥࡺࡨࡦࠢࡧ࡭ࡷ࡫ࡣࡵࡱࡵࡽࠥࡳࡡࡵࡥ࡫ࡩࡸࠦࡡࠡ࡯ࡲࡨ࡮࡬ࡩࡦࡦࠣ࡬ࡴࡵ࡫࠮࡮ࡨࡺࡪࡲࠠࡧ࡫࡯ࡩ࠱ࠦࡩࡵࠢࡦࡶࡪࡧࡴࡦࡵࠣࡥࠥࡒ࡯ࡨࡇࡱࡸࡷࡿࠠࡰࡤ࡭ࡩࡨࡺࠠࡸ࡫ࡷ࡬ࠥࡧࡴࡵࡣࡦ࡬ࡲ࡫࡮ࡵࠢࡧࡩࡹࡧࡩ࡭ࡵ࠱ࠎࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠ࠮ࠢࡖ࡭ࡲ࡯࡬ࡢࡴ࡯ࡽ࠱ࠦࡩࡵࠢࡳࡶࡴࡩࡥࡴࡵࡨࡷࠥࡈࡵࡪ࡮ࡧࡐࡪࡼࡥ࡭ࠢࡤࡸࡹࡧࡣࡩ࡯ࡨࡲࡹࡹࠠ࡭ࡱࡦࡥࡹ࡫ࡤࠡ࡫ࡱࠤࡍࡵ࡯࡬ࡎࡨࡺࡪࡲ࠯ࡃࡷ࡬ࡰࡩࡒࡥࡷࡧ࡯ࡌࡴࡵ࡫ࡆࡸࡨࡲࡹࠦࡢࡺࠢࡵࡩࡵࡲࡡࡤ࡫ࡱ࡫ࠥࠨࡂࡶ࡫࡯ࡨࡑ࡫ࡶࡦ࡮ࠥࠤࡼ࡯ࡴࡩࠢࠥࡌࡴࡵ࡫ࡍࡧࡹࡩࡱ࠵ࡂࡶ࡫࡯ࡨࡑ࡫ࡶࡦ࡮ࡋࡳࡴࡱࡅࡷࡧࡱࡸࠧ࠴ࠊࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣ࠱࡚ࠥࡨࡦࠢࡦࡶࡪࡧࡴࡦࡦࠣࡐࡴ࡭ࡅ࡯ࡶࡵࡽࠥࡵࡢ࡫ࡧࡦࡸࡸࠦࡡࡳࡧࠣࡥࡩࡪࡥࡥࠢࡷࡳࠥࡺࡨࡦࠢ࡫ࡳࡴࡱࠧࡴࠢࠥࡰࡴ࡭ࡳࠣࠢ࡯࡭ࡸࡺ࠮ࠋࠢࠣࠤࠥࠦࠠࠡࠢࡄࡶ࡬ࡹ࠺ࠋࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࡨࡰࡱ࡮࠾࡚ࠥࡨࡦࠢࡨࡺࡪࡴࡴࠡࡦ࡬ࡧࡹ࡯࡯࡯ࡣࡵࡽࠥࡩ࡯࡯ࡶࡤ࡭ࡳ࡯࡮ࡨࠢࡨࡼ࡮ࡹࡴࡪࡰࡪࠤࡱࡵࡧࡴࠢࡤࡲࡩࠦࡨࡰࡱ࡮ࠤ࡮ࡴࡦࡰࡴࡰࡥࡹ࡯࡯࡯࠰ࠍࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࡪࡲࡳࡰࡥ࡬ࡦࡸࡨࡰࡤ࡬ࡩ࡭ࡧࡶ࠾ࠥࡒࡩࡴࡶࠣࡳ࡫ࠦࡐࡢࡶ࡫ࠤࡴࡨࡪࡦࡥࡷࡷࠥ࡬ࡲࡰ࡯ࠣࡸ࡭࡫ࠠࡕࡧࡶࡸࡑ࡫ࡶࡦ࡮ࠣࡱࡴࡴࡩࡵࡱࡵ࡭ࡳ࡭࠮ࠋࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࡢࡶ࡫࡯ࡨࡤࡲࡥࡷࡧ࡯ࡣ࡫࡯࡬ࡦࡵ࠽ࠤࡑ࡯ࡳࡵࠢࡲࡪࠥࡖࡡࡵࡪࠣࡳࡧࡰࡥࡤࡶࡶࠤ࡫ࡸ࡯࡮ࠢࡷ࡬ࡪࠦࡂࡶ࡫࡯ࡨࡑ࡫ࡶࡦ࡮ࠣࡱࡴࡴࡩࡵࡱࡵ࡭ࡳ࡭࠮ࠋࠢࠣࠤࠥࠦࠠࠡࠢࠥࠦࠧᖧ")
        global _1l1ll11111l_opy_
        platform_index = os.environ[bstack1ll_opy_ (u"ࠧࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡐࡍࡃࡗࡊࡔࡘࡍࡠࡋࡑࡈࡊ࡞ࠧᖨ")]
        bstack1l1l111lll1_opy_ = os.path.join(bstack1l1ll1111l1_opy_, (bstack1l1l11llll1_opy_ + str(platform_index)), bstack11lll1l11ll_opy_)
        if not os.path.exists(bstack1l1l111lll1_opy_) or not os.path.isdir(bstack1l1l111lll1_opy_):
            self.logger.debug(bstack1ll_opy_ (u"ࠣࡆ࡬ࡶࡪࡩࡴࡰࡴࡼࠤࡩࡵࡥࡴࠢࡱࡳࡹࠦࡥࡹ࡫ࡶࡸࡸࠦࡴࡰࠢࡳࡶࡴࡩࡥࡴࡵࠣࡿࢂࠨᖩ").format(bstack1l1l111lll1_opy_))
            return
        logs = hook.get(bstack1ll_opy_ (u"ࠤ࡯ࡳ࡬ࡹࠢᖪ"), [])
        with os.scandir(bstack1l1l111lll1_opy_) as entries:
            for entry in entries:
                abs_path = os.path.abspath(entry.path)
                if abs_path in _1l1ll11111l_opy_:
                    self.logger.info(bstack1ll_opy_ (u"ࠥࡔࡦࡺࡨࠡࡣ࡯ࡶࡪࡧࡤࡺࠢࡳࡶࡴࡩࡥࡴࡵࡨࡨࠥࢁࡽࠣᖫ").format(abs_path))
                    continue
                if entry.is_file():
                    try:
                        timestamp = datetime.fromtimestamp(entry.stat().st_mtime, tz=timezone.utc).isoformat()
                    except Exception:
                        timestamp = bstack1ll_opy_ (u"ࠦࠧᖬ")
                    log_entry = bstack1ll1l111111_opy_(
                        kind=bstack1ll_opy_ (u"࡚ࠧࡅࡔࡖࡢࡅ࡙࡚ࡁࡄࡊࡐࡉࡓ࡚ࠢᖭ"),
                        message=bstack1ll_opy_ (u"ࠨࠢᖮ"),
                        level=bstack1ll_opy_ (u"ࠢࠣᖯ"),
                        timestamp=timestamp,
                        fileName=entry.name,
                        bstack1l1l11ll111_opy_=entry.stat().st_size,
                        bstack1l1l1l111l1_opy_=bstack1ll_opy_ (u"ࠣࡏࡄࡒ࡚ࡇࡌࡠࡗࡓࡐࡔࡇࡄࠣᖰ"),
                        bstack111ll1l_opy_=os.path.abspath(entry.path),
                        bstack1l1111l1111_opy_=hook.get(TestFramework.bstack11llll11111_opy_)
                    )
                    logs.append(log_entry)
                    _1l1ll11111l_opy_.add(abs_path)
        platform_index = os.environ[bstack1ll_opy_ (u"ࠩࡅࡖࡔ࡝ࡓࡆࡔࡖࡘࡆࡉࡋࡠࡒࡏࡅ࡙ࡌࡏࡓࡏࡢࡍࡓࡊࡅ࡙ࠩᖱ")]
        bstack1l11111llll_opy_ = os.path.join(bstack1l1ll1111l1_opy_, (bstack1l1l11llll1_opy_ + str(platform_index)), bstack11lll1l11ll_opy_, bstack11lll1l11l1_opy_)
        if not os.path.exists(bstack1l11111llll_opy_) or not os.path.isdir(bstack1l11111llll_opy_):
            self.logger.info(bstack1ll_opy_ (u"ࠥࡒࡴࠦࡂࡶ࡫࡯ࡨࡑ࡫ࡶࡦ࡮ࡋࡳࡴࡱࡅࡷࡧࡱࡸࠥࡧࡴࡵࡣࡦ࡬ࡲ࡫࡮ࡵࡵࠣࡨ࡮ࡸࡥࡤࡶࡲࡶࡾࠦࡦࡰࡷࡱࡨࠥࡧࡴ࠻ࠢࡾࢁࠧᖲ").format(bstack1l11111llll_opy_))
        else:
            self.logger.info(bstack1ll_opy_ (u"ࠦࡕࡸ࡯ࡤࡧࡶࡷ࡮ࡴࡧࠡࡄࡸ࡭ࡱࡪࡌࡦࡸࡨࡰࡍࡵ࡯࡬ࡇࡹࡩࡳࡺࠠࡢࡶࡷࡥࡨ࡮࡭ࡦࡰࡷࡷࠥ࡬ࡲࡰ࡯ࠣࡨ࡮ࡸࡥࡤࡶࡲࡶࡾࡀࠠࡼࡿࠥᖳ").format(bstack1l11111llll_opy_))
            with os.scandir(bstack1l11111llll_opy_) as entries:
                for entry in entries:
                    abs_path = os.path.abspath(entry.path)
                    if abs_path in _1l1ll11111l_opy_:
                        self.logger.info(bstack1ll_opy_ (u"ࠧࡖࡡࡵࡪࠣࡥࡱࡸࡥࡢࡦࡼࠤࡵࡸ࡯ࡤࡧࡶࡷࡪࡪࠠࡼࡿࠥᖴ").format(abs_path))
                        continue
                    if entry.is_file():
                        try:
                            timestamp = datetime.fromtimestamp(entry.stat().st_mtime, tz=timezone.utc).isoformat()
                        except Exception:
                            timestamp = bstack1ll_opy_ (u"ࠨࠢᖵ")
                        log_entry = bstack1ll1l111111_opy_(
                            kind=bstack1ll_opy_ (u"ࠢࡕࡇࡖࡘࡤࡇࡔࡕࡃࡆࡌࡒࡋࡎࡕࠤᖶ"),
                            message=bstack1ll_opy_ (u"ࠣࠤᖷ"),
                            level=bstack1ll_opy_ (u"ࠤࡅࡹ࡮ࡲࡤࡍࡧࡹࡩࡱࠨᖸ"),
                            timestamp=timestamp,
                            fileName=entry.name,
                            bstack1l1l11ll111_opy_=entry.stat().st_size,
                            bstack1l1l1l111l1_opy_=bstack1ll_opy_ (u"ࠥࡑࡆࡔࡕࡂࡎࡢ࡙ࡕࡒࡏࡂࡆࠥᖹ"),
                            bstack111ll1l_opy_=os.path.abspath(entry.path),
                            bstack1l1l11l1l11_opy_=hook.get(TestFramework.bstack11llll11111_opy_)
                        )
                        logs.append(log_entry)
                        _1l1ll11111l_opy_.add(abs_path)
        hook[bstack1ll_opy_ (u"ࠦࡱࡵࡧࡴࠤᖺ")] = logs
    def bstack1l1l11ll11l_opy_(
        self,
        bstack1l1l1ll111l_opy_: bstack1ll1l1ll111_opy_,
        entries: List[bstack1ll1l111111_opy_],
    ):
        req = structs.LogCreatedEventRequest()
        req.bin_session_id = os.environ.get(bstack1ll_opy_ (u"ࠧࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣࡈࡒࡉࡠࡄࡌࡒࡤ࡙ࡅࡔࡕࡌࡓࡓࡥࡉࡅࠤᖻ"))
        req.platform_index = TestFramework.bstack1llll1l111l_opy_(bstack1l1l1ll111l_opy_, TestFramework.bstack1l1lll1l1ll_opy_)
        req.execution_context.hash = str(bstack1l1l1ll111l_opy_.context.hash)
        req.execution_context.thread_id = str(bstack1l1l1ll111l_opy_.context.thread_id)
        req.execution_context.process_id = str(bstack1l1l1ll111l_opy_.context.process_id)
        for entry in entries:
            log_entry = req.logs.add()
            log_entry.test_framework_name = TestFramework.bstack1llll1l111l_opy_(bstack1l1l1ll111l_opy_, TestFramework.bstack1l1lll1lll1_opy_)
            log_entry.test_framework_version = TestFramework.bstack1llll1l111l_opy_(bstack1l1l1ll111l_opy_, TestFramework.bstack1l1l11l11ll_opy_)
            log_entry.uuid = entry.bstack1l1111l1111_opy_
            log_entry.test_framework_state = bstack1l1l1ll111l_opy_.state.name
            log_entry.message = entry.message.encode(bstack1ll_opy_ (u"ࠨࡵࡵࡨ࠰࠼ࠧᖼ"))
            log_entry.kind = entry.kind
            log_entry.timestamp = (
                entry.timestamp.isoformat()
                if isinstance(entry.timestamp, datetime)
                else datetime.now(tz=timezone.utc).isoformat()
            )
            log_entry.level = bstack1ll_opy_ (u"ࠢࠣᖽ")
            if entry.kind == bstack1ll_opy_ (u"ࠣࡖࡈࡗ࡙ࡥࡁࡕࡖࡄࡇࡍࡓࡅࡏࡖࠥᖾ"):
                log_entry.file_name = entry.fileName
                log_entry.file_size = entry.bstack1l1l11ll111_opy_
                log_entry.file_path = entry.bstack111ll1l_opy_
        def bstack1l1l1lll111_opy_():
            bstack11l1l1l1ll_opy_ = datetime.now()
            try:
                self.bstack1ll1l11lll1_opy_.LogCreatedEvent(req)
                bstack1l1l1ll111l_opy_.bstack11ll11ll1_opy_(bstack1ll_opy_ (u"ࠤࡪࡶࡵࡩ࠺ࡴࡧࡱࡨࡤࡲ࡯ࡨࡡࡦࡶࡪࡧࡴࡦࡦࡢࡩࡻ࡫࡮ࡵࡡࡤࡸࡹࡧࡣࡩ࡯ࡨࡲࡹࠨᖿ"), datetime.now() - bstack11l1l1l1ll_opy_)
            except grpc.RpcError as e:
                self.log_error(bstack1ll_opy_ (u"ࠥࡶࡵࡩ࠭ࡦࡴࡵࡳࡷࡀࠠࡴࡧࡱࡨࡤࡲ࡯ࡨࡡࡦࡶࡪࡧࡴࡦࡦࡢࡩࡻ࡫࡮ࡵࡡࡤࡸࡹࡧࡣࡩ࡯ࡨࡲࡹࠦࡻࡾࠤᗀ").format(str(e)))
                traceback.print_exc()
        self.bstack1lllll1ll1l_opy_.enqueue(bstack1l1l1lll111_opy_)
    def __1l111111lll_opy_(self, instance) -> None:
        bstack1ll_opy_ (u"ࠦࠧࠨࠊࠡࠢࠣࠤࠥࠦࠠࠡࡎࡲࡥࡩࡹࠠࡤࡷࡶࡸࡴࡳࠠࡵࡣࡪࡷࠥ࡬࡯ࡳࠢࡷ࡬ࡪࠦࡧࡪࡸࡨࡲࠥࡺࡥࡴࡶࠣࡪࡷࡧ࡭ࡦࡹࡲࡶࡰࠦࡩ࡯ࡵࡷࡥࡳࡩࡥ࠯ࠌࠣࠤࠥࠦࠠࠡࠢࠣࡇࡷ࡫ࡡࡵࡧࡶࠤࡦࠦࡤࡪࡥࡷࠤࡨࡵ࡮ࡵࡣ࡬ࡲ࡮ࡴࡧࠡࡶࡨࡷࡹࠦ࡬ࡦࡸࡨࡰࠥࡩࡵࡴࡶࡲࡱࠥࡳࡥࡵࡣࡧࡥࡹࡧࠠࡳࡧࡷࡶ࡮࡫ࡶࡦࡦࠣࡪࡷࡵ࡭ࠋࠢࠣࠤࠥࠦࠠࠡࠢࡆࡹࡸࡺ࡯࡮ࡖࡤ࡫ࡒࡧ࡮ࡢࡩࡨࡶࠥࡧ࡮ࡥࠢࡸࡴࡩࡧࡴࡦࡵࠣࡸ࡭࡫ࠠࡪࡰࡶࡸࡦࡴࡣࡦࠢࡶࡸࡦࡺࡥࠡࡷࡶ࡭ࡳ࡭ࠠࡴࡧࡷࡣࡸࡺࡡࡵࡧࡢࡩࡳࡺࡲࡪࡧࡶ࠲ࠏࠦࠠࠡࠢࠣࠤࠥࠦࠢࠣࠤᗁ")
        bstack11llllllll1_opy_ = {bstack1ll_opy_ (u"ࠧࡩࡵࡴࡶࡲࡱࡤࡳࡥࡵࡣࡧࡥࡹࡧࠢᗂ"): bstack1lll1ll1111_opy_.bstack11lll1ll111_opy_()}
        from browserstack_sdk.sdk_cli.test_framework import TestFramework
        TestFramework.bstack11llll1l11l_opy_(instance, bstack11llllllll1_opy_)
    @staticmethod
    def bstack11lll1l1l11_opy_(instance: bstack1ll1l1ll111_opy_, bstack11llll11l11_opy_: str):
        bstack1l111111111_opy_ = (
            bstack1lll1lll11l_opy_.bstack1l1111llll1_opy_
            if bstack11llll11l11_opy_ == bstack1lll1lll11l_opy_.bstack1l111111l11_opy_
            else bstack1lll1lll11l_opy_.bstack11llll11lll_opy_
        )
        bstack11lllll1ll1_opy_ = TestFramework.bstack1llll1l111l_opy_(instance, bstack11llll11l11_opy_, None)
        bstack11lllllll1l_opy_ = TestFramework.bstack1llll1l111l_opy_(instance, bstack1l111111111_opy_, None) if bstack11lllll1ll1_opy_ else None
        return (
            bstack11lllllll1l_opy_[bstack11lllll1ll1_opy_][-1]
            if isinstance(bstack11lllllll1l_opy_, dict) and len(bstack11lllllll1l_opy_.get(bstack11lllll1ll1_opy_, [])) > 0
            else None
        )
    @staticmethod
    def bstack1l1111111ll_opy_(instance: bstack1ll1l1ll111_opy_, bstack11llll11l11_opy_: str):
        hook = bstack1lll1lll11l_opy_.bstack11lll1l1l11_opy_(instance, bstack11llll11l11_opy_)
        if isinstance(hook, dict):
            hook.get(TestFramework.bstack11lllll11l1_opy_, []).clear()
    @staticmethod
    def __1l1111l111l_opy_(instance: bstack1ll1l1ll111_opy_, *args):
        if len(args) < 2 or not callable(getattr(args[1], bstack1ll_opy_ (u"ࠨࡧࡦࡶࡢࡶࡪࡩ࡯ࡳࡦࡶࠦᗃ"), None)):
            return
        if os.getenv(bstack1ll_opy_ (u"ࠢࡔࡆࡎࡣࡈࡒࡉࡠࡈࡏࡅࡌࡥࡌࡐࡉࡖࠦᗄ"), bstack1ll_opy_ (u"ࠣ࠳ࠥᗅ")) != bstack1ll_opy_ (u"ࠤ࠴ࠦᗆ"):
            bstack1lll1lll11l_opy_.logger.warning(bstack1ll_opy_ (u"ࠥ࡭࡬ࡴ࡯ࡳ࡫ࡱ࡫ࠥࡩࡡࡱ࡮ࡲ࡫ࠧᗇ"))
            return
        bstack1l111l111l1_opy_ = {
            bstack1ll_opy_ (u"ࠦࡸ࡫ࡴࡶࡲࠥᗈ"): (bstack1lll1lll11l_opy_.bstack11llllll111_opy_, bstack1lll1lll11l_opy_.bstack11llll11lll_opy_),
            bstack1ll_opy_ (u"ࠧࡺࡥࡢࡴࡧࡳࡼࡴࠢᗉ"): (bstack1lll1lll11l_opy_.bstack1l111111l11_opy_, bstack1lll1lll11l_opy_.bstack1l1111llll1_opy_),
        }
        for when in (bstack1ll_opy_ (u"ࠨࡳࡦࡶࡸࡴࠧᗊ"), bstack1ll_opy_ (u"ࠢࡤࡣ࡯ࡰࠧᗋ"), bstack1ll_opy_ (u"ࠣࡶࡨࡥࡷࡪ࡯ࡸࡰࠥᗌ")):
            bstack1l1111ll1l1_opy_ = args[1].get_records(when)
            if not bstack1l1111ll1l1_opy_:
                continue
            records = [
                bstack1ll1l111111_opy_(
                    kind=TestFramework.bstack1l1l11ll1ll_opy_,
                    message=r.message,
                    level=r.levelname if hasattr(r, bstack1ll_opy_ (u"ࠤ࡯ࡩࡻ࡫࡬࡯ࡣࡰࡩࠧᗍ")) and r.levelname else None,
                    timestamp=(
                        datetime.fromtimestamp(r.created, tz=timezone.utc)
                        if hasattr(r, bstack1ll_opy_ (u"ࠥࡧࡷ࡫ࡡࡵࡧࡧࠦᗎ")) and r.created
                        else None
                    ),
                )
                for r in bstack1l1111ll1l1_opy_
                if isinstance(getattr(r, bstack1ll_opy_ (u"ࠦࡲ࡫ࡳࡴࡣࡪࡩࠧᗏ"), None), str) and r.message.strip()
            ]
            if not records:
                continue
            bstack11lll1lllll_opy_, bstack1l111111111_opy_ = bstack1l111l111l1_opy_.get(when, (None, None))
            bstack1l11111l11l_opy_ = TestFramework.bstack1llll1l111l_opy_(instance, bstack11lll1lllll_opy_, None) if bstack11lll1lllll_opy_ else None
            bstack11lllllll1l_opy_ = TestFramework.bstack1llll1l111l_opy_(instance, bstack1l111111111_opy_, None) if bstack1l11111l11l_opy_ else None
            if isinstance(bstack11lllllll1l_opy_, dict) and len(bstack11lllllll1l_opy_.get(bstack1l11111l11l_opy_, [])) > 0:
                hook = bstack11lllllll1l_opy_[bstack1l11111l11l_opy_][-1]
                if isinstance(hook, dict) and TestFramework.bstack11lllll11l1_opy_ in hook:
                    hook[TestFramework.bstack11lllll11l1_opy_].extend(records)
                    continue
            logs = TestFramework.bstack1llll1l111l_opy_(instance, TestFramework.bstack1l1111lll11_opy_, [])
            logs.extend(records)
    @staticmethod
    def __1l11111l1ll_opy_(test) -> Dict[str, Any]:
        bstack11l111l11l_opy_ = bstack1lll1lll11l_opy_.__1l1111ll1ll_opy_(test.location) if hasattr(test, bstack1ll_opy_ (u"ࠧࡲ࡯ࡤࡣࡷ࡭ࡴࡴࠢᗐ")) else getattr(test, bstack1ll_opy_ (u"ࠨ࡮ࡰࡦࡨ࡭ࡩࠨᗑ"), None)
        test_name = test.name if hasattr(test, bstack1ll_opy_ (u"ࠢ࡯ࡣࡰࡩࠧᗒ")) else None
        bstack11llll11ll1_opy_ = test.fspath.strpath if hasattr(test, bstack1ll_opy_ (u"ࠣࡨࡶࡴࡦࡺࡨࠣᗓ")) and test.fspath else None
        if not bstack11l111l11l_opy_ or not test_name or not bstack11llll11ll1_opy_:
            return None
        code = None
        if hasattr(test, bstack1ll_opy_ (u"ࠤࡲࡦ࡯ࠨᗔ")):
            try:
                import inspect
                code = inspect.getsource(test.obj)
            except:
                pass
        bstack11lll1l111l_opy_ = []
        try:
            bstack11lll1l111l_opy_ = bstack1l11111lll_opy_.bstack111l111111_opy_(test)
        except:
            bstack1lll1lll11l_opy_.logger.warning(bstack1ll_opy_ (u"࡙ࠥࡳࡧࡢ࡭ࡧࠣࡸࡴࠦࡦࡪࡰࡧࠤࡹ࡫ࡳࡵࠢࡶࡧࡴࡶࡥࡴ࠮ࠣࡸࡪࡹࡴࠡࡵࡦࡳࡵ࡫ࡳࠡࡹ࡬ࡰࡱࠦࡢࡦࠢࡵࡩࡸࡵ࡬ࡷࡧࡧࠤ࡮ࡴࠠࡄࡎࡌࠦᗕ"))
        return {
            TestFramework.bstack1ll111lll1l_opy_: uuid4().__str__(),
            TestFramework.bstack11llllll1ll_opy_: bstack11l111l11l_opy_,
            TestFramework.bstack1ll111ll111_opy_: test_name,
            TestFramework.bstack1l1l111l11l_opy_: getattr(test, bstack1ll_opy_ (u"ࠦࡳࡵࡤࡦ࡫ࡧࠦᗖ"), None),
            TestFramework.bstack1l1111l11l1_opy_: bstack11llll11ll1_opy_,
            TestFramework.bstack11lllll1l11_opy_: bstack1lll1lll11l_opy_.__1l111l11111_opy_(test),
            TestFramework.bstack1l11111lll1_opy_: code,
            TestFramework.bstack1l11l1ll11l_opy_: TestFramework.bstack1l11111111l_opy_,
            TestFramework.bstack1l111lll11l_opy_: bstack11l111l11l_opy_,
            TestFramework.bstack11lll11llll_opy_: bstack11lll1l111l_opy_
        }
    @staticmethod
    def __1l111l11111_opy_(test) -> List[str]:
        markers = []
        current = test
        while current:
            own_markers = getattr(current, bstack1ll_opy_ (u"ࠧࡵࡷ࡯ࡡࡰࡥࡷࡱࡥࡳࡵࠥᗗ"), [])
            markers.extend([getattr(m, bstack1ll_opy_ (u"ࠨ࡮ࡢ࡯ࡨࠦᗘ"), None) for m in own_markers if getattr(m, bstack1ll_opy_ (u"ࠢ࡯ࡣࡰࡩࠧᗙ"), None)])
            current = getattr(current, bstack1ll_opy_ (u"ࠣࡲࡤࡶࡪࡴࡴࠣᗚ"), None)
        return markers
    @staticmethod
    def __1l1111ll1ll_opy_(location):
        return bstack1ll_opy_ (u"ࠤ࠽࠾ࠧᗛ").join(filter(lambda x: isinstance(x, str), location))