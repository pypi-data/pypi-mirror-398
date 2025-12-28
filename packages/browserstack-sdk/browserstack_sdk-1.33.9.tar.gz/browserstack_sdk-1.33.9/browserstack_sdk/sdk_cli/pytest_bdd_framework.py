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
from pathlib import Path
import grpc
from browserstack_sdk import sdk_pb2 as structs
from browserstack_sdk.sdk_cli.test_framework import (
    TestFramework,
    bstack1ll1ll1lll1_opy_,
    bstack1ll1l1ll111_opy_,
    bstack1ll1l1ll11l_opy_,
    bstack1l1111l1l1l_opy_,
    bstack1ll1l111111_opy_,
)
import traceback
from bstack_utils.helper import bstack1l1l1l1l11l_opy_
from bstack_utils.bstack11ll1llll1_opy_ import bstack1lll1ll1l1l_opy_
from bstack_utils.constants import EVENTS
from browserstack_sdk.sdk_cli.utils.bstack1lll1ll1ll1_opy_ import bstack1lll1ll1111_opy_
from browserstack_sdk.sdk_cli.bstack1lllll1ll1l_opy_ import bstack1lllll1l1l1_opy_
bstack1l1ll1111l1_opy_ = bstack1l1l1l1l11l_opy_()
bstack1l1l11llll1_opy_ = bstack1ll_opy_ (u"࡛ࠧࡰ࡭ࡱࡤࡨࡪࡪࡁࡵࡶࡤࡧ࡭ࡳࡥ࡯ࡶࡶ࠱ࠧᒎ")
bstack1l11111ll11_opy_ = bstack1ll_opy_ (u"ࠨࡈࡰࡱ࡮ࡐࡪࡼࡥ࡭ࠤᒏ")
bstack1l111l111ll_opy_ = bstack1ll_opy_ (u"ࠢࡃࡷ࡬ࡰࡩࡒࡥࡷࡧ࡯ࡌࡴࡵ࡫ࡆࡸࡨࡲࡹࠨᒐ")
bstack11llll1l1ll_opy_ = 1.0
_1l1ll11111l_opy_ = set()
class PytestBDDFramework(TestFramework):
    bstack1l1111l1l11_opy_ = bstack1ll_opy_ (u"ࠣࡶࡨࡷࡹࡥࡦࡪࡺࡷࡹࡷ࡫ࡳࠣᒑ")
    bstack11llll11lll_opy_ = bstack1ll_opy_ (u"ࠤࡷࡩࡸࡺ࡟ࡩࡱࡲ࡯ࡸࡥࡳࡵࡣࡵࡸࡪࡪࠢᒒ")
    bstack1l1111llll1_opy_ = bstack1ll_opy_ (u"ࠥࡸࡪࡹࡴࡠࡪࡲࡳࡰࡹ࡟ࡧ࡫ࡱ࡭ࡸ࡮ࡥࡥࠤᒓ")
    bstack11llllll111_opy_ = bstack1ll_opy_ (u"ࠦࡹ࡫ࡳࡵࡡ࡫ࡳࡴࡱ࡟࡭ࡣࡶࡸࡤࡹࡴࡢࡴࡷࡩࡩࠨᒔ")
    bstack1l111111l11_opy_ = bstack1ll_opy_ (u"ࠧࡺࡥࡴࡶࡢ࡬ࡴࡵ࡫ࡠ࡮ࡤࡷࡹࡥࡦࡪࡰ࡬ࡷ࡭࡫ࡤࠣᒕ")
    bstack11llll1111l_opy_: bool
    bstack1lllll1ll1l_opy_: bstack1lllll1l1l1_opy_  = None
    bstack11llll1llll_opy_ = [
        bstack1ll1ll1lll1_opy_.BEFORE_ALL,
        bstack1ll1ll1lll1_opy_.AFTER_ALL,
        bstack1ll1ll1lll1_opy_.BEFORE_EACH,
        bstack1ll1ll1lll1_opy_.AFTER_EACH,
    ]
    def __init__(
        self,
        bstack1l11111l111_opy_: Dict[str, str],
        bstack1ll1111lll1_opy_: List[str]=[bstack1ll_opy_ (u"ࠨࡰࡺࡶࡨࡷࡹ࠳ࡢࡥࡦࠥᒖ")],
        bstack1lllll1ll1l_opy_: bstack1lllll1l1l1_opy_ = None,
        bstack1ll1l11lll1_opy_=None
    ):
        super().__init__(bstack1ll1111lll1_opy_, bstack1l11111l111_opy_, bstack1lllll1ll1l_opy_)
        self.bstack11llll1111l_opy_ = any(bstack1ll_opy_ (u"ࠢࡱࡻࡷࡩࡸࡺ࠭ࡣࡦࡧࠦᒗ") in item.lower() for item in bstack1ll1111lll1_opy_)
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
        if test_framework_state == bstack1ll1ll1lll1_opy_.TEST or test_framework_state in PytestBDDFramework.bstack11llll1llll_opy_:
            bstack1l1111l1ll1_opy_(test_framework_state, test_hook_state)
        if test_framework_state == bstack1ll1ll1lll1_opy_.NONE:
            self.logger.warning(bstack1ll_opy_ (u"ࠣ࡫ࡪࡲࡴࡸࡥࡥࠢࡦࡥࡱࡲࡢࡢࡥ࡮ࠤࡹ࡫ࡳࡵࡡࡩࡶࡦࡳࡥࡸࡱࡵ࡯ࡤࡹࡴࡢࡶࡨࡁࢀࡺࡥࡴࡶࡢࡪࡷࡧ࡭ࡦࡹࡲࡶࡰࡥࡳࡵࡣࡷࡩࢂࠦࡴࡦࡵࡷࡣ࡭ࡵ࡯࡬ࡡࡶࡸࡦࡺࡥ࠾ࠤᒘ") + str(test_hook_state) + bstack1ll_opy_ (u"ࠤࠥᒙ"))
            return
        if not self.bstack11llll1111l_opy_:
            self.logger.warning(bstack1ll_opy_ (u"ࠥࡸࡷࡧࡣ࡬ࡡࡨࡺࡪࡴࡴ࠻ࠢࡸࡲࡸࡻࡰࡱࡱࡵࡸࡪࡪࠠࡧࡴࡤࡱࡪࡽ࡯ࡳ࡭ࡀࠦᒚ") + str(str(self.bstack1ll1111lll1_opy_)) + bstack1ll_opy_ (u"ࠦࠧᒛ"))
            return
        if not isinstance(args, tuple) or len(args) == 0:
            self.logger.warning(bstack1ll_opy_ (u"ࠧࡺࡲࡢࡥ࡮ࡣࡪࡼࡥ࡯ࡶ࠽ࠤࡺࡴࡥࡹࡲࡨࡧࡹ࡫ࡤࠡࡣࡵ࡫ࡸࡃࡻࡢࡴࡪࡷࢂࠦ࡫ࡸࡣࡵ࡫ࡸࡃࠢᒜ") + str(kwargs) + bstack1ll_opy_ (u"ࠨࠢᒝ"))
            return
        instance = self.__1l1111l1lll_opy_(context, test_framework_state, test_hook_state, *args, **kwargs)
        if not instance:
            self.logger.debug(bstack1ll_opy_ (u"ࠢࡵࡴࡤࡧࡰࡥࡥࡷࡧࡱࡸ࠿ࠦࡵ࡯ࡪࡤࡲࡩࡲࡥࡥࠢࡨࡺࡪࡴࡴ࠾ࡽࡷࡩࡸࡺ࡟ࡧࡴࡤࡱࡪࡽ࡯ࡳ࡭ࡢࡷࡹࡧࡴࡦࡿ࠱ࡿࡹ࡫ࡳࡵࡡ࡫ࡳࡴࡱ࡟ࡴࡶࡤࡸࡪࢃࠠࡢࡴࡪࡷࡂࠨᒞ") + str(args) + bstack1ll_opy_ (u"ࠣࠤᒟ"))
            return
        try:
            if instance!= None and test_framework_state in PytestBDDFramework.bstack11llll1llll_opy_ and test_hook_state == bstack1ll1l1ll11l_opy_.PRE:
                bstack1ll11l11l1l_opy_ = bstack1lll1ll1l1l_opy_.bstack1ll1111ll11_opy_(EVENTS.bstack1ll1llll11_opy_.value)
                name = str(EVENTS.bstack1ll1llll11_opy_.name)+bstack1ll_opy_ (u"ࠤ࠽ࠦᒠ")+str(test_framework_state.name)
                TestFramework.bstack11llll111ll_opy_(instance, name, bstack1ll11l11l1l_opy_)
        except Exception as e:
            self.logger.debug(bstack1ll_opy_ (u"ࠥࡉࡽࡩࡥࡱࡶ࡬ࡳࡳࠦࡩ࡯ࠢ࡫ࡳࡴࡱࠠࡦࡴࡵࡳࡷࠦࡰࡳࡧ࠽ࠤࢀࢃࠢᒡ").format(e))
        try:
            if test_framework_state == bstack1ll1ll1lll1_opy_.TEST:
                if not TestFramework.bstack1llll11ll11_opy_(instance, TestFramework.bstack11llllll1ll_opy_) and test_hook_state == bstack1ll1l1ll11l_opy_.PRE:
                    if not (len(args) >= 3):
                        return
                    test = PytestBDDFramework.__1l11111l1ll_opy_(args)
                    if test:
                        instance.data.update(test)
                        self.logger.debug(bstack1ll_opy_ (u"ࠦࡱࡵࡡࡥࡧࡧࠤ࡮ࡴࡳࡵࡣࡱࡧࡪࡃࡻࡪࡰࡶࡸࡦࡴࡣࡦ࠰ࡵࡩ࡫࠮ࠩࡾࠢࡨࡺࡪࡴࡴ࠾ࡽࡷࡩࡸࡺ࡟ࡧࡴࡤࡱࡪࡽ࡯ࡳ࡭ࡢࡷࡹࡧࡴࡦࡿ࠱ࠦᒢ") + str(test_hook_state) + bstack1ll_opy_ (u"ࠧࠨᒣ"))
                if test_hook_state == bstack1ll1l1ll11l_opy_.PRE and not TestFramework.bstack1llll11ll11_opy_(instance, TestFramework.bstack1l1l1llll11_opy_):
                    TestFramework.bstack1llll1lll11_opy_(instance, TestFramework.bstack1l1l1llll11_opy_, datetime.now(tz=timezone.utc))
                    PytestBDDFramework.__11llll1ll1l_opy_(instance, args)
                    self.logger.debug(bstack1ll_opy_ (u"ࠨࡳࡦࡶࠣࡸࡪࡹࡴ࠮ࡵࡷࡥࡷࡺࠠࡧࡱࡵࠤ࡮ࡴࡳࡵࡣࡱࡧࡪࡃࡻࡪࡰࡶࡸࡦࡴࡣࡦ࠰ࡵࡩ࡫࠮ࠩࡾࠢࡨࡺࡪࡴࡴ࠾ࡽࡷࡩࡸࡺ࡟ࡧࡴࡤࡱࡪࡽ࡯ࡳ࡭ࡢࡷࡹࡧࡴࡦࡿ࠱ࠦᒤ") + str(test_hook_state) + bstack1ll_opy_ (u"ࠢࠣᒥ"))
                elif test_hook_state == bstack1ll1l1ll11l_opy_.POST and not TestFramework.bstack1llll11ll11_opy_(instance, TestFramework.bstack1l1ll11l1l1_opy_):
                    TestFramework.bstack1llll1lll11_opy_(instance, TestFramework.bstack1l1ll11l1l1_opy_, datetime.now(tz=timezone.utc))
                    self.logger.debug(bstack1ll_opy_ (u"ࠣࡵࡨࡸࠥࡺࡥࡴࡶ࠰ࡩࡳࡪࠠࡧࡱࡵࠤ࡮ࡴࡳࡵࡣࡱࡧࡪࡃࡻࡪࡰࡶࡸࡦࡴࡣࡦ࠰ࡵࡩ࡫࠮ࠩࡾࠢࡨࡺࡪࡴࡴ࠾ࡽࡷࡩࡸࡺ࡟ࡧࡴࡤࡱࡪࡽ࡯ࡳ࡭ࡢࡷࡹࡧࡴࡦࡿ࠱ࠦᒦ") + str(test_hook_state) + bstack1ll_opy_ (u"ࠤࠥᒧ"))
            elif test_framework_state == bstack1ll1ll1lll1_opy_.STEP:
                if test_hook_state == bstack1ll1l1ll11l_opy_.PRE:
                    PytestBDDFramework.__1l111111ll1_opy_(instance, args)
                elif test_hook_state == bstack1ll1l1ll11l_opy_.POST:
                    PytestBDDFramework.__11lll1ll1l1_opy_(instance, args)
            elif test_framework_state == bstack1ll1ll1lll1_opy_.LOG and test_hook_state == bstack1ll1l1ll11l_opy_.POST:
                PytestBDDFramework.__1l1111l111l_opy_(instance, *args)
            elif test_framework_state == bstack1ll1ll1lll1_opy_.LOG_REPORT and test_hook_state == bstack1ll1l1ll11l_opy_.POST:
                self.__11llll1lll1_opy_(instance, *args)
                self.__1l111111lll_opy_(instance)
            elif test_framework_state in PytestBDDFramework.bstack11llll1llll_opy_:
                self.__11lll1lll1l_opy_(instance, test_framework_state, test_hook_state, *args)
            self.logger.debug(bstack1ll_opy_ (u"ࠥࡸࡷࡧࡣ࡬ࡡࡨࡺࡪࡴࡴ࠻ࠢ࡫ࡥࡳࡪ࡬ࡦࡦࠣࡩࡻ࡫࡮ࡵ࠿ࡾࡸࡪࡹࡴࡠࡨࡵࡥࡲ࡫ࡷࡰࡴ࡮ࡣࡸࡺࡡࡵࡧࢀ࠲ࢀࡺࡥࡴࡶࡢ࡬ࡴࡵ࡫ࡠࡵࡷࡥࡹ࡫ࡽࠡ࡫ࡱࡷࡹࡧ࡮ࡤࡧࡀࠦᒨ") + str(instance.ref()) + bstack1ll_opy_ (u"ࠦࠧᒩ"))
        except Exception as e:
            self.logger.error(e)
            traceback.print_exc()
        self.bstack11llllll1l1_opy_(instance, (test_framework_state, test_hook_state), *args, **kwargs)
        try:
            if instance!= None and test_framework_state in PytestBDDFramework.bstack11llll1llll_opy_ and test_hook_state == bstack1ll1l1ll11l_opy_.POST:
                name = str(EVENTS.bstack1ll1llll11_opy_.name)+bstack1ll_opy_ (u"ࠧࡀࠢᒪ")+str(test_framework_state.name)
                bstack1ll11l11l1l_opy_ = TestFramework.bstack1l1111lllll_opy_(instance, name)
                bstack1lll1ll1l1l_opy_.end(EVENTS.bstack1ll1llll11_opy_.value, bstack1ll11l11l1l_opy_+bstack1ll_opy_ (u"ࠨ࠺ࡴࡶࡤࡶࡹࠨᒫ"), bstack1ll11l11l1l_opy_+bstack1ll_opy_ (u"ࠢ࠻ࡧࡱࡨࠧᒬ"), True, None, test_framework_state.name)
        except Exception as e:
            self.logger.debug(bstack1ll_opy_ (u"ࠣࡇࡻࡧࡪࡶࡴࡪࡱࡱࠤ࡮ࡴࠠࡩࡱࡲ࡯ࠥ࡫ࡲࡳࡱࡵ࠾ࠥࢁࡽࠣᒭ").format(e))
    def bstack1l1l11l1l1l_opy_(self):
        return self.bstack11llll1111l_opy_
    def __1l11111l1l1_opy_(self, *args):
        if len(args) > 2 and callable(getattr(args[2], bstack1ll_opy_ (u"ࠤࡪࡩࡹࡥࡲࡦࡵࡸࡰࡹࠨᒮ"), None)):
            rep = args[2].get_result()
            if rep:
                return TestFramework.bstack1l1l11lll11_opy_(rep, [bstack1ll_opy_ (u"ࠥࡻ࡭࡫࡮ࠣᒯ"), bstack1ll_opy_ (u"ࠦࡴࡻࡴࡤࡱࡰࡩࠧᒰ"), bstack1ll_opy_ (u"ࠧࡶࡡࡴࡵࡨࡨࠧᒱ"), bstack1ll_opy_ (u"ࠨࡦࡢ࡫࡯ࡩࡩࠨᒲ"), bstack1ll_opy_ (u"ࠢࡴ࡭࡬ࡴࡵ࡫ࡤࠣᒳ"), bstack1ll_opy_ (u"ࠣ࡮ࡲࡲ࡬ࡸࡥࡱࡴࡷࡩࡽࡺࠢᒴ")])
        return None
    def __11llll1lll1_opy_(self, instance: bstack1ll1l1ll111_opy_, *args):
        result = self.__1l11111l1l1_opy_(*args)
        if not result:
            return
        failure = None
        bstack1llllll1111_opy_ = None
        if result.get(bstack1ll_opy_ (u"ࠤࡲࡹࡹࡩ࡯࡮ࡧࠥᒵ"), None) == bstack1ll_opy_ (u"ࠥࡪࡦ࡯࡬ࡦࡦࠥᒶ") and len(args) > 1 and getattr(args[1], bstack1ll_opy_ (u"ࠦࡪࡾࡣࡪࡰࡩࡳࠧᒷ"), None) is not None:
            failure = [{bstack1ll_opy_ (u"ࠬࡨࡡࡤ࡭ࡷࡶࡦࡩࡥࠨᒸ"): [args[1].excinfo.exconly(), result.get(bstack1ll_opy_ (u"ࠨ࡬ࡰࡰࡪࡶࡪࡶࡲࡵࡧࡻࡸࠧᒹ"), None)]}]
            bstack1llllll1111_opy_ = bstack1ll_opy_ (u"ࠢࡂࡵࡶࡩࡷࡺࡩࡰࡰࡈࡶࡷࡵࡲࠣᒺ") if bstack1ll_opy_ (u"ࠣࡃࡶࡷࡪࡸࡴࡪࡱࡱࠦᒻ") in getattr(args[1].excinfo, bstack1ll_opy_ (u"ࠤࡷࡽࡵ࡫࡮ࡢ࡯ࡨࠦᒼ"), bstack1ll_opy_ (u"ࠥࠦᒽ")) else bstack1ll_opy_ (u"࡚ࠦࡴࡨࡢࡰࡧࡰࡪࡪࡅࡳࡴࡲࡶࠧᒾ")
        bstack11lll1ll1ll_opy_ = result.get(bstack1ll_opy_ (u"ࠧࡵࡵࡵࡥࡲࡱࡪࠨᒿ"), TestFramework.bstack1l11111111l_opy_)
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
            target = None # bstack11llll1l1l1_opy_ bstack1l11111ll1l_opy_ this to be bstack1ll_opy_ (u"ࠨ࡮ࡰࡦࡨ࡭ࡩࠨᓀ")
            if test_framework_state == bstack1ll1ll1lll1_opy_.INIT_TEST:
                target = args[0] if isinstance(args[0], str) else None
                if target:
                    self.__11lllll1111_opy_(context, test_framework_state, target, *args)
            elif test_framework_state == bstack1ll1ll1lll1_opy_.LOG:
                nodeid = getattr(getattr(args[0], bstack1ll_opy_ (u"ࠢ࡯ࡱࡧࡩࠧᓁ"), None), bstack1ll_opy_ (u"ࠣࡰࡲࡨࡪ࡯ࡤࠣᓂ"), None) if args else None
                if isinstance(nodeid, str):
                    target = nodeid
            elif getattr(args[0], bstack1ll_opy_ (u"ࠤࡱࡳࡩ࡫ࠢᓃ"), None):
                target = args[0].node.nodeid
            elif getattr(args[0], bstack1ll_opy_ (u"ࠥࡲࡴࡪࡥࡪࡦࠥᓄ"), None):
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
        bstack1l1111111l1_opy_ = TestFramework.bstack1llll1l111l_opy_(instance, PytestBDDFramework.bstack11llll11lll_opy_, {})
        if not key in bstack1l1111111l1_opy_:
            bstack1l1111111l1_opy_[key] = []
        bstack11lll1lll11_opy_ = TestFramework.bstack1llll1l111l_opy_(instance, PytestBDDFramework.bstack1l1111llll1_opy_, {})
        if not key in bstack11lll1lll11_opy_:
            bstack11lll1lll11_opy_[key] = []
        bstack11llllllll1_opy_ = {
            PytestBDDFramework.bstack11llll11lll_opy_: bstack1l1111111l1_opy_,
            PytestBDDFramework.bstack1l1111llll1_opy_: bstack11lll1lll11_opy_,
        }
        if test_hook_state == bstack1ll1l1ll11l_opy_.PRE:
            hook_name = args[1] if len(args) > 1 else None
            hook = {
                bstack1ll_opy_ (u"ࠦࡰ࡫ࡹࠣᓅ"): key,
                TestFramework.bstack11llll11111_opy_: uuid4().__str__(),
                TestFramework.bstack11lllll1l1l_opy_: TestFramework.bstack11lllll11ll_opy_,
                TestFramework.bstack11lllll1lll_opy_: datetime.now(tz=timezone.utc),
                TestFramework.bstack11lllll11l1_opy_: [],
                TestFramework.bstack1l1111ll111_opy_: hook_name,
                TestFramework.bstack1l111l11l11_opy_: bstack1lll1ll1111_opy_.bstack11lll1ll111_opy_()
            }
            bstack1l1111111l1_opy_[key].append(hook)
            bstack11llllllll1_opy_[PytestBDDFramework.bstack11llllll111_opy_] = key
        elif test_hook_state == bstack1ll1l1ll11l_opy_.POST:
            bstack11lll1l1lll_opy_ = bstack1l1111111l1_opy_.get(key, [])
            hook = bstack11lll1l1lll_opy_.pop() if bstack11lll1l1lll_opy_ else None
            if hook:
                result = self.__1l11111l1l1_opy_(*args)
                if result:
                    bstack1l1111lll1l_opy_ = result.get(bstack1ll_opy_ (u"ࠧࡵࡵࡵࡥࡲࡱࡪࠨᓆ"), TestFramework.bstack11lllll11ll_opy_)
                    if bstack1l1111lll1l_opy_ != TestFramework.bstack11lllll11ll_opy_:
                        hook[TestFramework.bstack11lllll1l1l_opy_] = bstack1l1111lll1l_opy_
                hook[TestFramework.bstack1l1111ll11l_opy_] = datetime.now(tz=timezone.utc)
                hook[TestFramework.bstack1l111l11l11_opy_] = bstack1lll1ll1111_opy_.bstack11lll1ll111_opy_()
                self.bstack11lllllll11_opy_(hook)
                logs = hook.get(TestFramework.bstack11lllllllll_opy_, [])
                self.bstack1l1l11ll11l_opy_(instance, logs)
                bstack11lll1lll11_opy_[key].append(hook)
                bstack11llllllll1_opy_[PytestBDDFramework.bstack1l111111l11_opy_] = key
        TestFramework.bstack11llll1l11l_opy_(instance, bstack11llllllll1_opy_)
        self.logger.debug(bstack1ll_opy_ (u"ࠨࡴࡳࡣࡦ࡯ࡤ࡮࡯ࡰ࡭ࡢࡩࡻ࡫࡮ࡵ࠼ࠣࡸࡪࡹࡴࡠࡪࡲࡳࡰࡥࡳࡵࡣࡷࡩࡂࢁ࡫ࡦࡻࢀ࠲ࢀࡺࡥࡴࡶࡢ࡬ࡴࡵ࡫ࡠࡵࡷࡥࡹ࡫ࡽࠡࡪࡲࡳࡰࡹ࡟ࡴࡶࡤࡶࡹ࡫ࡤ࠾ࡽ࡫ࡳࡴࡱࡳࡠࡵࡷࡥࡷࡺࡥࡥࡿࠣ࡬ࡴࡵ࡫ࡴࡡࡩ࡭ࡳ࡯ࡳࡩࡧࡧࡁࠧᓇ") + str(bstack11lll1lll11_opy_) + bstack1ll_opy_ (u"ࠢࠣᓈ"))
    def __1l111111l1l_opy_(
        self,
        context: bstack1l1111l1l1l_opy_,
        test_framework_state: bstack1ll1ll1lll1_opy_,
        test_hook_state: bstack1ll1l1ll11l_opy_,
        *args,
        **kwargs,
    ):
        fixturedef = TestFramework.bstack1l1l11lll11_opy_(args[0], [bstack1ll_opy_ (u"ࠣࡵࡦࡳࡵ࡫ࠢᓉ"), bstack1ll_opy_ (u"ࠤࡤࡶ࡬ࡴࡡ࡮ࡧࠥᓊ"), bstack1ll_opy_ (u"ࠥࡴࡦࡸࡡ࡮ࡵࠥᓋ"), bstack1ll_opy_ (u"ࠦ࡮ࡪࡳࠣᓌ"), bstack1ll_opy_ (u"ࠧࡻ࡮ࡪࡶࡷࡩࡸࡺࠢᓍ"), bstack1ll_opy_ (u"ࠨࡢࡢࡵࡨ࡭ࡩࠨᓎ")]) if len(args) > 0 else {}
        request = args[1] if len(args) > 1 else None
        scenario = args[2] if len(args) == 3 else None
        scope = request.scope if hasattr(request, bstack1ll_opy_ (u"ࠢࡴࡥࡲࡴࡪࠨᓏ")) else fixturedef.get(bstack1ll_opy_ (u"ࠣࡵࡦࡳࡵ࡫ࠢᓐ"), None)
        fixturename = request.fixturename if hasattr(request, bstack1ll_opy_ (u"ࠤࡩ࡭ࡽࡺࡵࡳࡧࡱࡥࡲ࡫ࠢᓑ")) else None
        node = request.node if hasattr(request, bstack1ll_opy_ (u"ࠥࡲࡴࡪࡥࠣᓒ")) else None
        target = request.node.nodeid if hasattr(node, bstack1ll_opy_ (u"ࠦࡳࡵࡤࡦ࡫ࡧࠦᓓ")) else None
        baseid = fixturedef.get(bstack1ll_opy_ (u"ࠧࡨࡡࡴࡧ࡬ࡨࠧᓔ"), None) or bstack1ll_opy_ (u"ࠨࠢᓕ")
        if (not target or len(baseid) > 0) and hasattr(request, bstack1ll_opy_ (u"ࠢࡠࡲࡼࡪࡺࡴࡣࡪࡶࡨࡱࠧᓖ")):
            target = PytestBDDFramework.__1l1111ll1ll_opy_(request._pyfuncitem.location) if hasattr(request._pyfuncitem, bstack1ll_opy_ (u"ࠣ࡮ࡲࡧࡦࡺࡩࡰࡰࠥᓗ")) else None
            if target and not TestFramework.bstack1llll11111l_opy_(target):
                self.__11lllll1111_opy_(context, test_framework_state, target, (target, request._pyfuncitem.location))
                node = request._pyfuncitem
                self.logger.debug(bstack1ll_opy_ (u"ࠤࡷࡶࡦࡩ࡫ࡠࡨ࡬ࡼࡹࡻࡲࡦࡡࡨࡺࡪࡴࡴ࠻ࠢࡩࡥࡱࡲࡢࡢࡥ࡮ࠤࡹࡧࡲࡨࡧࡷࡁࢀࡺࡡࡳࡩࡨࡸࢂࠦࡦࡪࡺࡷࡹࡷ࡫࡮ࡢ࡯ࡨࡁࢀ࡬ࡩࡹࡶࡸࡶࡪࡴࡡ࡮ࡧࢀࠤࡳࡵࡤࡦ࠿ࡾࡲࡴࡪࡥࡾࠢࡨࡺࡪࡴࡴ࠾ࡽࡷࡩࡸࡺ࡟ࡧࡴࡤࡱࡪࡽ࡯ࡳ࡭ࡢࡷࡹࡧࡴࡦࡿ࠱ࠦᓘ") + str(test_hook_state) + bstack1ll_opy_ (u"ࠥࠦᓙ"))
        if not fixturedef or not scope or not target:
            self.logger.warning(bstack1ll_opy_ (u"ࠦࡹࡸࡡࡤ࡭ࡢࡪ࡮ࡾࡴࡶࡴࡨࡣࡪࡼࡥ࡯ࡶ࠽ࠤࡺࡴࡨࡢࡰࡧࡰࡪࡪࠠࡦࡸࡨࡲࡹࡃࡻࡵࡧࡶࡸࡤ࡬ࡲࡢ࡯ࡨࡻࡴࡸ࡫ࡠࡵࡷࡥࡹ࡫ࡽ࠯ࡽࡷࡩࡸࡺ࡟ࡩࡱࡲ࡯ࡤࡹࡴࡢࡶࡨࢁࠥ࡬ࡩࡹࡶࡸࡶࡪࡪࡥࡧ࠿ࡾࡪ࡮ࡾࡴࡶࡴࡨࡨࡪ࡬ࡽࠡࡵࡦࡳࡵ࡫࠽ࡼࡵࡦࡳࡵ࡫ࡽࠡࡶࡤࡶ࡬࡫ࡴ࠾ࠤᓚ") + str(target) + bstack1ll_opy_ (u"ࠧࠨᓛ"))
            return None
        instance = TestFramework.bstack1llll11111l_opy_(target)
        if not instance:
            self.logger.warning(bstack1ll_opy_ (u"ࠨࡴࡳࡣࡦ࡯ࡤ࡬ࡩࡹࡶࡸࡶࡪࡥࡥࡷࡧࡱࡸ࠿ࠦࡵ࡯ࡪࡤࡲࡩࡲࡥࡥࠢࡨࡺࡪࡴࡴ࠾ࡽࡷࡩࡸࡺ࡟ࡧࡴࡤࡱࡪࡽ࡯ࡳ࡭ࡢࡷࡹࡧࡴࡦࡿ࠱ࡿࡹ࡫ࡳࡵࡡ࡫ࡳࡴࡱ࡟ࡴࡶࡤࡸࡪࢃࠠࡧ࡫ࡻࡸࡺࡸࡥ࡯ࡣࡰࡩࡂࢁࡦࡪࡺࡷࡹࡷ࡫࡮ࡢ࡯ࡨࢁࠥࡹࡣࡰࡲࡨࡁࢀࡹࡣࡰࡲࡨࢁࠥࡨࡡࡴࡧ࡬ࡨࡂࢁࡢࡢࡵࡨ࡭ࡩࢃࠠࡵࡣࡵ࡫ࡪࡺ࠽ࠣᓜ") + str(target) + bstack1ll_opy_ (u"ࠢࠣᓝ"))
            return None
        bstack11llll1l111_opy_ = TestFramework.bstack1llll1l111l_opy_(instance, PytestBDDFramework.bstack1l1111l1l11_opy_, {})
        if os.getenv(bstack1ll_opy_ (u"ࠣࡕࡇࡏࡤࡉࡌࡊࡡࡉࡐࡆࡍ࡟ࡇࡋ࡛ࡘ࡚ࡘࡅࡔࠤᓞ"), bstack1ll_opy_ (u"ࠤ࠴ࠦᓟ")) == bstack1ll_opy_ (u"ࠥ࠵ࠧᓠ"):
            bstack11lll1llll1_opy_ = bstack1ll_opy_ (u"ࠦ࠿ࠨᓡ").join((scope, fixturename))
            bstack11llll1ll11_opy_ = datetime.now(tz=timezone.utc)
            bstack11lllll111l_opy_ = {
                bstack1ll_opy_ (u"ࠧࡱࡥࡺࠤᓢ"): bstack11lll1llll1_opy_,
                bstack1ll_opy_ (u"ࠨࡴࡢࡩࡶࠦᓣ"): PytestBDDFramework.__1l111l11111_opy_(request.node, scenario),
                bstack1ll_opy_ (u"ࠢࡧ࡫ࡻࡸࡺࡸࡥࠣᓤ"): fixturedef,
                bstack1ll_opy_ (u"ࠣࡵࡦࡳࡵ࡫ࠢᓥ"): scope,
                bstack1ll_opy_ (u"ࠤࡷࡽࡵ࡫ࠢᓦ"): None,
            }
            try:
                if test_hook_state == bstack1ll1l1ll11l_opy_.POST and callable(getattr(args[-1], bstack1ll_opy_ (u"ࠥ࡫ࡪࡺ࡟ࡳࡧࡶࡹࡱࡺࠢᓧ"), None)):
                    bstack11lllll111l_opy_[bstack1ll_opy_ (u"ࠦࡹࡿࡰࡦࠤᓨ")] = TestFramework.bstack1l1ll111ll1_opy_(args[-1].get_result())
            except Exception as e:
                pass
            if test_hook_state == bstack1ll1l1ll11l_opy_.PRE:
                bstack11lllll111l_opy_[bstack1ll_opy_ (u"ࠧࡻࡵࡪࡦࠥᓩ")] = uuid4().__str__()
                bstack11lllll111l_opy_[PytestBDDFramework.bstack11lllll1lll_opy_] = bstack11llll1ll11_opy_
            elif test_hook_state == bstack1ll1l1ll11l_opy_.POST:
                bstack11lllll111l_opy_[PytestBDDFramework.bstack1l1111ll11l_opy_] = bstack11llll1ll11_opy_
            if bstack11lll1llll1_opy_ in bstack11llll1l111_opy_:
                bstack11llll1l111_opy_[bstack11lll1llll1_opy_].update(bstack11lllll111l_opy_)
                self.logger.debug(bstack1ll_opy_ (u"ࠨࡵࡱࡦࡤࡸࡪࡪࠠࡧ࡫ࡻࡸࡺࡸࡥ࡯ࡣࡰࡩࡂࢁࡦࡪࡺࡷࡹࡷ࡫࡮ࡢ࡯ࡨࢁࠥࡹࡣࡰࡲࡨࡁࢀࡹࡣࡰࡲࡨࢁࠥ࡬ࡩࡹࡶࡸࡶࡪࡃࠢᓪ") + str(bstack11llll1l111_opy_[bstack11lll1llll1_opy_]) + bstack1ll_opy_ (u"ࠢࠣᓫ"))
            else:
                bstack11llll1l111_opy_[bstack11lll1llll1_opy_] = bstack11lllll111l_opy_
                self.logger.debug(bstack1ll_opy_ (u"ࠣࡵࡤࡺࡪࡪࠠࡧ࡫ࡻࡸࡺࡸࡥ࡯ࡣࡰࡩࡂࢁࡦࡪࡺࡷࡹࡷ࡫࡮ࡢ࡯ࡨࢁࠥࡹࡣࡰࡲࡨࡁࢀࡹࡣࡰࡲࡨࢁࠥ࡬ࡩࡹࡶࡸࡶࡪࡃࡻࡵࡧࡶࡸࡤ࡬ࡩࡹࡶࡸࡶࡪࢃࠠࡵࡴࡤࡧࡰ࡫ࡤࡠࡨ࡬ࡼࡹࡻࡲࡦࡵࡀࠦᓬ") + str(len(bstack11llll1l111_opy_)) + bstack1ll_opy_ (u"ࠤࠥᓭ"))
        TestFramework.bstack1llll1lll11_opy_(instance, PytestBDDFramework.bstack1l1111l1l11_opy_, bstack11llll1l111_opy_)
        self.logger.debug(bstack1ll_opy_ (u"ࠥࡷࡦࡼࡥࡥࠢࡩ࡭ࡽࡺࡵࡳࡧࡶࡁࢀࡲࡥ࡯ࠪࡷࡶࡦࡩ࡫ࡦࡦࡢࡪ࡮ࡾࡴࡶࡴࡨࡷ࠮ࢃࠠࡪࡰࡶࡸࡦࡴࡣࡦ࠿ࠥᓮ") + str(instance.ref()) + bstack1ll_opy_ (u"ࠦࠧᓯ"))
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
            PytestBDDFramework.bstack1l1111l1l11_opy_: {},
            PytestBDDFramework.bstack1l1111llll1_opy_: {},
            PytestBDDFramework.bstack11llll11lll_opy_: {},
        })
        if len(args) > 1 and isinstance(args[1], tuple):
            TestFramework.bstack1llll1lll11_opy_(ob, TestFramework.bstack1l111l1111l_opy_, str(args[1][0]))
        if context.platform_index >= 0:
            TestFramework.bstack1llll1lll11_opy_(ob, TestFramework.bstack1l1lll1l1ll_opy_, context.platform_index)
        TestFramework.bstack1lllll111ll_opy_[ctx.id] = ob
        self.logger.debug(bstack1ll_opy_ (u"ࠧࡹࡡࡷࡧࡧࠤ࡮ࡴࡳࡵࡣࡱࡧࡪࠦࡣࡵࡺ࠱࡭ࡩࡃࡻࡤࡶࡻ࠲࡮ࡪࡽࠡࡶࡤࡶ࡬࡫ࡴ࠾ࡽࡷࡥࡷ࡭ࡥࡵࡿࠣࡥࡷ࡭ࡳ࠾ࡽࡤࡶ࡬ࡹࡽࠡ࡫ࡱࡷࡹࡧ࡮ࡤࡧࡶࡁࠧᓰ") + str(TestFramework.bstack1lllll111ll_opy_.keys()) + bstack1ll_opy_ (u"ࠨࠢᓱ"))
        return ob
    @staticmethod
    def __11llll1ll1l_opy_(instance, args):
        request, feature, scenario = args
        steps = []
        for step in scenario.steps:
            steps.append({
                bstack1ll_opy_ (u"ࠧࡪࡦࠪᓲ"): id(step),
                bstack1ll_opy_ (u"ࠨࡶࡨࡼࡹ࠭ᓳ"): step.name,
                bstack1ll_opy_ (u"ࠩ࡮ࡩࡾࡽ࡯ࡳࡦࠪᓴ"): step.keyword,
            })
        meta = {
            bstack1ll_opy_ (u"ࠪࡪࡪࡧࡴࡶࡴࡨࠫᓵ"): {
                bstack1ll_opy_ (u"ࠫࡳࡧ࡭ࡦࠩᓶ"): feature.name,
                bstack1ll_opy_ (u"ࠬࡶࡡࡵࡪࠪᓷ"): feature.filename,
                bstack1ll_opy_ (u"࠭ࡤࡦࡵࡦࡶ࡮ࡶࡴࡪࡱࡱࠫᓸ"): feature.description
            },
            bstack1ll_opy_ (u"ࠧࡴࡥࡨࡲࡦࡸࡩࡰࠩᓹ"): {
                bstack1ll_opy_ (u"ࠨࡰࡤࡱࡪ࠭ᓺ"): scenario.name
            },
            bstack1ll_opy_ (u"ࠩࡶࡸࡪࡶࡳࠨᓻ"): steps,
            bstack1ll_opy_ (u"ࠪࡩࡽࡧ࡭ࡱ࡮ࡨࡷࠬᓼ"): PytestBDDFramework.__11llll11l1l_opy_(request.node)
        }
        instance.data.update(
            {
                TestFramework.bstack11llllll11l_opy_: meta
            }
        )
    def bstack11lllllll11_opy_(self, hook: Dict[str, Any]) -> None:
        bstack1ll_opy_ (u"ࠦࠧࠨࠊࠡࠢࠣࠤࠥࠦࠠࠡࡒࡵࡳࡨ࡫ࡳࡴࡧࡶࠤࡹ࡮ࡥࠡࡊࡲࡳࡰࡒࡥࡷࡧ࡯ࠤࡦࡺࡴࡢࡥ࡫ࡱࡪࡴࡴࡴࠢࡶ࡭ࡲ࡯࡬ࡢࡴࠣࡸࡴࠦࡴࡩࡧࠣࡎࡦࡼࡡࠡ࡫ࡰࡴࡱ࡫࡭ࡦࡰࡷࡥࡹ࡯࡯࡯࠰ࠍࠤࠥࠦࠠࠡࠢࠣࠤ࡙࡮ࡩࡴࠢࡰࡩࡹ࡮࡯ࡥ࠼ࠍࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦ࠭ࠡࡅ࡫ࡩࡨࡱࡳࠡࡶ࡫ࡩࠥࡎ࡯ࡰ࡭ࡏࡩࡻ࡫࡬ࠡࡦ࡬ࡶࡪࡩࡴࡰࡴࡼࠤ࡮ࡴࡳࡪࡦࡨࠤࢃ࠵࠮ࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰ࠵ࡕࡱ࡮ࡲࡥࡩ࡫ࡤࡂࡶࡷࡥࡨ࡮࡭ࡦࡰࡷࡷ࠳ࠐࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢ࠰ࠤࡋࡵࡲࠡࡧࡤࡧ࡭ࠦࡦࡪ࡮ࡨࠤ࡮ࡴࠠࡩࡱࡲ࡯ࡤࡲࡥࡷࡧ࡯ࡣ࡫࡯࡬ࡦࡵ࠯ࠤࡷ࡫ࡰ࡭ࡣࡦࡩࡸࠦࠢࡕࡧࡶࡸࡑ࡫ࡶࡦ࡮ࠥࠤࡼ࡯ࡴࡩࠢࠥࡌࡴࡵ࡫ࡍࡧࡹࡩࡱࠨࠠࡪࡰࠣ࡭ࡹࡹࠠࡱࡣࡷ࡬࠳ࠐࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢ࠰ࠤࡎ࡬ࠠࡢࠢࡩ࡭ࡱ࡫ࠠࡪࡰࠣࡸ࡭࡫ࠠࡥ࡫ࡵࡩࡨࡺ࡯ࡳࡻࠣࡱࡦࡺࡣࡩࡧࡶࠤࡦࠦ࡭ࡰࡦ࡬ࡪ࡮࡫ࡤࠡࡪࡲࡳࡰ࠳࡬ࡦࡸࡨࡰࠥ࡬ࡩ࡭ࡧ࠯ࠤ࡮ࡺࠠࡤࡴࡨࡥࡹ࡫ࡳࠡࡣࠣࡐࡴ࡭ࡅ࡯ࡶࡵࡽࠥࡵࡢ࡫ࡧࡦࡸࠥࡽࡩࡵࡪࠣࡥࡹࡺࡡࡤࡪࡰࡩࡳࡺࠠࡥࡧࡷࡥ࡮ࡲࡳ࠯ࠌࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥ࠳ࠠࡔ࡫ࡰ࡭ࡱࡧࡲ࡭ࡻ࠯ࠤ࡮ࡺࠠࡱࡴࡲࡧࡪࡹࡳࡦࡵࠣࡆࡺ࡯࡬ࡥࡎࡨࡺࡪࡲࠠࡢࡶࡷࡥࡨ࡮࡭ࡦࡰࡷࡷࠥࡲ࡯ࡤࡣࡷࡩࡩࠦࡩ࡯ࠢࡋࡳࡴࡱࡌࡦࡸࡨࡰ࠴ࡈࡵࡪ࡮ࡧࡐࡪࡼࡥ࡭ࡊࡲࡳࡰࡋࡶࡦࡰࡷࠤࡧࡿࠠࡳࡧࡳࡰࡦࡩࡩ࡯ࡩࠣࠦࡇࡻࡩ࡭ࡦࡏࡩࡻ࡫࡬ࠣࠢࡺ࡭ࡹ࡮ࠠࠣࡊࡲࡳࡰࡒࡥࡷࡧ࡯࠳ࡇࡻࡩ࡭ࡦࡏࡩࡻ࡫࡬ࡉࡱࡲ࡯ࡊࡼࡥ࡯ࡶࠥ࠲ࠏࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡ࠯ࠣࡘ࡭࡫ࠠࡤࡴࡨࡥࡹ࡫ࡤࠡࡎࡲ࡫ࡊࡴࡴࡳࡻࠣࡳࡧࡰࡥࡤࡶࡶࠤࡦࡸࡥࠡࡣࡧࡨࡪࡪࠠࡵࡱࠣࡸ࡭࡫ࠠࡩࡱࡲ࡯ࠬࡹࠠࠣ࡮ࡲ࡫ࡸࠨࠠ࡭࡫ࡶࡸ࠳ࠐࠠࠡࠢࠣࠤࠥࠦࠠࡂࡴࡪࡷ࠿ࠐࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤ࡭ࡵ࡯࡬࠼ࠣࡘ࡭࡫ࠠࡦࡸࡨࡲࡹࠦࡤࡪࡥࡷ࡭ࡴࡴࡡࡳࡻࠣࡧࡴࡴࡴࡢ࡫ࡱ࡭ࡳ࡭ࠠࡦࡺ࡬ࡷࡹ࡯࡮ࡨࠢ࡯ࡳ࡬ࡹࠠࡢࡰࡧࠤ࡭ࡵ࡯࡬ࠢ࡬ࡲ࡫ࡵࡲ࡮ࡣࡷ࡭ࡴࡴ࠮ࠋࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࡨࡰࡱ࡮ࡣࡱ࡫ࡶࡦ࡮ࡢࡪ࡮ࡲࡥࡴ࠼ࠣࡐ࡮ࡹࡴࠡࡱࡩࠤࡕࡧࡴࡩࠢࡲࡦ࡯࡫ࡣࡵࡵࠣࡪࡷࡵ࡭ࠡࡶ࡫ࡩ࡚ࠥࡥࡴࡶࡏࡩࡻ࡫࡬ࠡ࡯ࡲࡲ࡮ࡺ࡯ࡳ࡫ࡱ࡫࠳ࠐࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࡧࡻࡩ࡭ࡦࡢࡰࡪࡼࡥ࡭ࡡࡩ࡭ࡱ࡫ࡳ࠻ࠢࡏ࡭ࡸࡺࠠࡰࡨࠣࡔࡦࡺࡨࠡࡱࡥ࡮ࡪࡩࡴࡴࠢࡩࡶࡴࡳࠠࡵࡪࡨࠤࡇࡻࡩ࡭ࡦࡏࡩࡻ࡫࡬ࠡ࡯ࡲࡲ࡮ࡺ࡯ࡳ࡫ࡱ࡫࠳ࠐࠠࠡࠢࠣࠤࠥࠦࠠࠣࠤࠥᓽ")
        global _1l1ll11111l_opy_
        platform_index = os.environ[bstack1ll_opy_ (u"ࠬࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣࡕࡒࡁࡕࡈࡒࡖࡒࡥࡉࡏࡆࡈ࡜ࠬᓾ")]
        bstack1l1l111lll1_opy_ = os.path.join(bstack1l1ll1111l1_opy_, (bstack1l1l11llll1_opy_ + str(platform_index)), bstack1l11111ll11_opy_)
        if not os.path.exists(bstack1l1l111lll1_opy_) or not os.path.isdir(bstack1l1l111lll1_opy_):
            return
        logs = hook.get(bstack1ll_opy_ (u"ࠨ࡬ࡰࡩࡶࠦᓿ"), [])
        with os.scandir(bstack1l1l111lll1_opy_) as entries:
            for entry in entries:
                abs_path = os.path.abspath(entry.path)
                if abs_path in _1l1ll11111l_opy_:
                    self.logger.info(bstack1ll_opy_ (u"ࠢࡑࡣࡷ࡬ࠥࡧ࡬ࡳࡧࡤࡨࡾࠦࡰࡳࡱࡦࡩࡸࡹࡥࡥࠢࡾࢁࠧᔀ").format(abs_path))
                    continue
                if entry.is_file():
                    try:
                        timestamp = datetime.fromtimestamp(entry.stat().st_mtime, tz=timezone.utc).isoformat()
                    except Exception:
                        timestamp = bstack1ll_opy_ (u"ࠣࠤᔁ")
                    log_entry = bstack1ll1l111111_opy_(
                        kind=bstack1ll_opy_ (u"ࠤࡗࡉࡘ࡚࡟ࡂࡖࡗࡅࡈࡎࡍࡆࡐࡗࠦᔂ"),
                        message=bstack1ll_opy_ (u"ࠥࠦᔃ"),
                        level=bstack1ll_opy_ (u"ࠦࠧᔄ"),
                        timestamp=timestamp,
                        fileName=entry.name,
                        bstack1l1l11ll111_opy_=entry.stat().st_size,
                        bstack1l1l1l111l1_opy_=bstack1ll_opy_ (u"ࠧࡓࡁࡏࡗࡄࡐࡤ࡛ࡐࡍࡑࡄࡈࠧᔅ"),
                        bstack111ll1l_opy_=os.path.abspath(entry.path),
                        bstack1l1111l1111_opy_=hook.get(TestFramework.bstack11llll11111_opy_)
                    )
                    logs.append(log_entry)
                    _1l1ll11111l_opy_.add(abs_path)
        platform_index = os.environ[bstack1ll_opy_ (u"࠭ࡂࡓࡑ࡚ࡗࡊࡘࡓࡕࡃࡆࡏࡤࡖࡌࡂࡖࡉࡓࡗࡓ࡟ࡊࡐࡇࡉ࡝࠭ᔆ")]
        bstack1l11111llll_opy_ = os.path.join(bstack1l1ll1111l1_opy_, (bstack1l1l11llll1_opy_ + str(platform_index)), bstack1l11111ll11_opy_, bstack1l111l111ll_opy_)
        if not os.path.exists(bstack1l11111llll_opy_) or not os.path.isdir(bstack1l11111llll_opy_):
            self.logger.info(bstack1ll_opy_ (u"ࠢࡏࡱࠣࡆࡺ࡯࡬ࡥࡎࡨࡺࡪࡲࡈࡰࡱ࡮ࡉࡻ࡫࡮ࡵࠢࡤࡸࡹࡧࡣࡩ࡯ࡨࡲࡹࡹࠠࡥ࡫ࡵࡩࡨࡺ࡯ࡳࡻࠣࡪࡴࡻ࡮ࡥࠢࡤࡸ࠿ࠦࡻࡾࠤᔇ").format(bstack1l11111llll_opy_))
        else:
            self.logger.info(bstack1ll_opy_ (u"ࠣࡒࡵࡳࡨ࡫ࡳࡴ࡫ࡱ࡫ࠥࡈࡵࡪ࡮ࡧࡐࡪࡼࡥ࡭ࡊࡲࡳࡰࡋࡶࡦࡰࡷࠤࡦࡺࡴࡢࡥ࡫ࡱࡪࡴࡴࡴࠢࡩࡶࡴࡳࠠࡥ࡫ࡵࡩࡨࡺ࡯ࡳࡻ࠽ࠤࢀࢃࠢᔈ").format(bstack1l11111llll_opy_))
            with os.scandir(bstack1l11111llll_opy_) as entries:
                for entry in entries:
                    abs_path = os.path.abspath(entry.path)
                    if abs_path in _1l1ll11111l_opy_:
                        self.logger.info(bstack1ll_opy_ (u"ࠤࡓࡥࡹ࡮ࠠࡢ࡮ࡵࡩࡦࡪࡹࠡࡲࡵࡳࡨ࡫ࡳࡴࡧࡧࠤࢀࢃࠢᔉ").format(abs_path))
                        continue
                    if entry.is_file():
                        try:
                            timestamp = datetime.fromtimestamp(entry.stat().st_mtime, tz=timezone.utc).isoformat()
                        except Exception:
                            timestamp = bstack1ll_opy_ (u"ࠥࠦᔊ")
                        log_entry = bstack1ll1l111111_opy_(
                            kind=bstack1ll_opy_ (u"࡙ࠦࡋࡓࡕࡡࡄࡘ࡙ࡇࡃࡉࡏࡈࡒ࡙ࠨᔋ"),
                            message=bstack1ll_opy_ (u"ࠧࠨᔌ"),
                            level=bstack1ll_opy_ (u"ࠨࡂࡶ࡫࡯ࡨࡑ࡫ࡶࡦ࡮ࠥᔍ"),
                            timestamp=timestamp,
                            fileName=entry.name,
                            bstack1l1l11ll111_opy_=entry.stat().st_size,
                            bstack1l1l1l111l1_opy_=bstack1ll_opy_ (u"ࠢࡎࡃࡑ࡙ࡆࡒ࡟ࡖࡒࡏࡓࡆࡊࠢᔎ"),
                            bstack111ll1l_opy_=os.path.abspath(entry.path),
                            bstack1l1l11l1l11_opy_=hook.get(TestFramework.bstack11llll11111_opy_)
                        )
                        logs.append(log_entry)
                        _1l1ll11111l_opy_.add(abs_path)
        hook[bstack1ll_opy_ (u"ࠣ࡮ࡲ࡫ࡸࠨᔏ")] = logs
    def bstack1l1l11ll11l_opy_(
        self,
        bstack1l1l1ll111l_opy_: bstack1ll1l1ll111_opy_,
        entries: List[bstack1ll1l111111_opy_],
    ):
        req = structs.LogCreatedEventRequest()
        req.bin_session_id = os.environ.get(bstack1ll_opy_ (u"ࠤࡅࡖࡔ࡝ࡓࡆࡔࡖࡘࡆࡉࡋࡠࡅࡏࡍࡤࡈࡉࡏࡡࡖࡉࡘ࡙ࡉࡐࡐࡢࡍࡉࠨᔐ"))
        req.platform_index = TestFramework.bstack1llll1l111l_opy_(bstack1l1l1ll111l_opy_, TestFramework.bstack1l1lll1l1ll_opy_)
        req.execution_context.hash = str(bstack1l1l1ll111l_opy_.context.hash)
        req.execution_context.thread_id = str(bstack1l1l1ll111l_opy_.context.thread_id)
        req.execution_context.process_id = str(bstack1l1l1ll111l_opy_.context.process_id)
        for entry in entries:
            log_entry = req.logs.add()
            log_entry.test_framework_name = TestFramework.bstack1llll1l111l_opy_(bstack1l1l1ll111l_opy_, TestFramework.bstack1l1lll1lll1_opy_)
            log_entry.test_framework_version = TestFramework.bstack1llll1l111l_opy_(bstack1l1l1ll111l_opy_, TestFramework.bstack1l1l11l11ll_opy_)
            log_entry.uuid = entry.bstack1l1111l1111_opy_ if entry.bstack1l1111l1111_opy_ else TestFramework.bstack1llll1l111l_opy_(bstack1l1l1ll111l_opy_, TestFramework.bstack1ll111lll1l_opy_)
            log_entry.test_framework_state = bstack1l1l1ll111l_opy_.state.name
            log_entry.message = entry.message.encode(bstack1ll_opy_ (u"ࠥࡹࡹ࡬࠭࠹ࠤᔑ"))
            log_entry.kind = entry.kind
            log_entry.timestamp = (
                entry.timestamp.isoformat()
                if isinstance(entry.timestamp, datetime)
                else datetime.now(tz=timezone.utc).isoformat()
            )
            if isinstance(entry.level, str) and len(entry.level.strip()) > 0:
                log_entry.level = entry.level.strip()
            if entry.kind == bstack1ll_opy_ (u"࡙ࠦࡋࡓࡕࡡࡄࡘ࡙ࡇࡃࡉࡏࡈࡒ࡙ࠨᔒ"):
                log_entry.file_name = entry.fileName
                log_entry.file_size = entry.bstack1l1l11ll111_opy_
                log_entry.file_path = entry.bstack111ll1l_opy_
        def bstack1l1l1lll111_opy_():
            bstack11l1l1l1ll_opy_ = datetime.now()
            try:
                self.bstack1ll1l11lll1_opy_.LogCreatedEvent(req)
                bstack1l1l1ll111l_opy_.bstack11ll11ll1_opy_(bstack1ll_opy_ (u"ࠧ࡭ࡲࡱࡥ࠽ࡷࡪࡴࡤࡠ࡮ࡲ࡫ࡤࡩࡲࡦࡣࡷࡩࡩࡥࡥࡷࡧࡱࡸࡤࡧࡴࡵࡣࡦ࡬ࡲ࡫࡮ࡵࠤᔓ"), datetime.now() - bstack11l1l1l1ll_opy_)
            except grpc.RpcError as e:
                self.log_error(bstack1ll_opy_ (u"ࠨࡲࡱࡥ࠰ࡩࡷࡸ࡯ࡳ࠼ࠣࡷࡪࡴࡤࡠ࡮ࡲ࡫ࡤࡩࡲࡦࡣࡷࡩࡩࡥࡥࡷࡧࡱࡸࡤࡧࡴࡵࡣࡦ࡬ࡲ࡫࡮ࡵࠢࡾࢁࠧᔔ").format(str(e)))
                traceback.print_exc()
        self.bstack1lllll1ll1l_opy_.enqueue(bstack1l1l1lll111_opy_)
    def __1l111111lll_opy_(self, instance) -> None:
        bstack1ll_opy_ (u"ࠢࠣࠤࠍࠤࠥࠦࠠࠡࠢࠣࠤࡑࡵࡡࡥࡵࠣࡧࡺࡹࡴࡰ࡯ࠣࡸࡦ࡭ࡳࠡࡨࡲࡶࠥࡺࡨࡦࠢࡪ࡭ࡻ࡫࡮ࠡࡶࡨࡷࡹࠦࡦࡳࡣࡰࡩࡼࡵࡲ࡬ࠢ࡬ࡲࡸࡺࡡ࡯ࡥࡨ࠲ࠏࠦࠠࠡࠢࠣࠤࠥࠦࡃࡳࡧࡤࡸࡪࡹࠠࡢࠢࡧ࡭ࡨࡺࠠࡤࡱࡱࡸࡦ࡯࡮ࡪࡰࡪࠤࡹ࡫ࡳࡵࠢ࡯ࡩࡻ࡫࡬ࠡࡥࡸࡷࡹࡵ࡭ࠡ࡯ࡨࡸࡦࡪࡡࡵࡣࠣࡶࡪࡺࡲࡪࡧࡹࡩࡩࠦࡦࡳࡱࡰࠎࠥࠦࠠࠡࠢࠣࠤࠥࡉࡵࡴࡶࡲࡱ࡙ࡧࡧࡎࡣࡱࡥ࡬࡫ࡲࠡࡣࡱࡨࠥࡻࡰࡥࡣࡷࡩࡸࠦࡴࡩࡧࠣ࡭ࡳࡹࡴࡢࡰࡦࡩࠥࡹࡴࡢࡶࡨࠤࡺࡹࡩ࡯ࡩࠣࡷࡪࡺ࡟ࡴࡶࡤࡸࡪࡥࡥ࡯ࡶࡵ࡭ࡪࡹ࠮ࠋࠢࠣࠤࠥࠦࠠࠡࠢࠥࠦࠧᔕ")
        bstack11llllllll1_opy_ = {bstack1ll_opy_ (u"ࠣࡥࡸࡷࡹࡵ࡭ࡠ࡯ࡨࡸࡦࡪࡡࡵࡣࠥᔖ"): bstack1lll1ll1111_opy_.bstack11lll1ll111_opy_()}
        TestFramework.bstack11llll1l11l_opy_(instance, bstack11llllllll1_opy_)
    @staticmethod
    def __1l111111ll1_opy_(instance, args):
        request, bstack11lll1l1l1l_opy_ = args
        bstack1l1111l11ll_opy_ = id(bstack11lll1l1l1l_opy_)
        bstack11lll1ll11l_opy_ = instance.data[TestFramework.bstack11llllll11l_opy_]
        step = next(filter(lambda st: st[bstack1ll_opy_ (u"ࠩ࡬ࡨࠬᔗ")] == bstack1l1111l11ll_opy_, bstack11lll1ll11l_opy_[bstack1ll_opy_ (u"ࠪࡷࡹ࡫ࡰࡴࠩᔘ")]), None)
        step.update({
            bstack1ll_opy_ (u"ࠫࡸࡺࡡࡳࡶࡨࡨࡤࡧࡴࠨᔙ"): datetime.now(tz=timezone.utc)
        })
        index = next((i for i, st in enumerate(bstack11lll1ll11l_opy_[bstack1ll_opy_ (u"ࠬࡹࡴࡦࡲࡶࠫᔚ")]) if st[bstack1ll_opy_ (u"࠭ࡩࡥࠩᔛ")] == step[bstack1ll_opy_ (u"ࠧࡪࡦࠪᔜ")]), None)
        if index is not None:
            bstack11lll1ll11l_opy_[bstack1ll_opy_ (u"ࠨࡵࡷࡩࡵࡹࠧᔝ")][index] = step
        instance.data[TestFramework.bstack11llllll11l_opy_] = bstack11lll1ll11l_opy_
    @staticmethod
    def __11lll1ll1l1_opy_(instance, args):
        bstack1ll_opy_ (u"ࠤࠥࠦࠏࠦࠠࠡࠢࠣࠤࠥࠦࡷࡩࡧࡱࠤࡱ࡫࡮ࠡࡣࡵ࡫ࡸࠦࡩࡴࠢ࠵࠰ࠥ࡯ࡴࠡࡵ࡬࡫ࡳ࡯ࡦࡪࡧࡶࠤࡹ࡮ࡥࡳࡧࠣ࡭ࡸࠦ࡮ࡰࠢࡨࡼࡨ࡫ࡰࡵ࡫ࡲࡲࠏࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࡥࡷ࡭ࡳࠡࡣࡵࡩࠥ࠳ࠠ࡜ࡴࡨࡵࡺ࡫ࡳࡵ࠮ࠣࡷࡹ࡫ࡰ࡞ࠌࠣࠤࠥࠦࠠࠡࠢࠣ࡭࡫ࠦࡡࡳࡩࡶࠤࡦࡸࡥࠡ࠵ࠣࡸ࡭࡫࡮ࠡࡶ࡫ࡩࠥࡲࡡࡴࡶࠣࡺࡦࡲࡵࡦࠢ࡬ࡷࠥ࡫ࡸࡤࡧࡳࡸ࡮ࡵ࡮ࠋࠢࠣࠤࠥࠦࠠࠡࠢࠥࠦࠧᔞ")
        bstack11llll111l1_opy_ = datetime.now(tz=timezone.utc)
        request = args[0]
        bstack11lll1l1l1l_opy_ = args[1]
        bstack1l1111l11ll_opy_ = id(bstack11lll1l1l1l_opy_)
        bstack11lll1ll11l_opy_ = instance.data[TestFramework.bstack11llllll11l_opy_]
        step = None
        if bstack1l1111l11ll_opy_ is not None and bstack11lll1ll11l_opy_.get(bstack1ll_opy_ (u"ࠪࡷࡹ࡫ࡰࡴࠩᔟ")):
            step = next(filter(lambda st: st[bstack1ll_opy_ (u"ࠫ࡮ࡪࠧᔠ")] == bstack1l1111l11ll_opy_, bstack11lll1ll11l_opy_[bstack1ll_opy_ (u"ࠬࡹࡴࡦࡲࡶࠫᔡ")]), None)
            step.update({
                bstack1ll_opy_ (u"࠭ࡦࡪࡰ࡬ࡷ࡭࡫ࡤࡠࡣࡷࠫᔢ"): bstack11llll111l1_opy_,
            })
        if len(args) > 2:
            exception = args[2]
            step.update({
                bstack1ll_opy_ (u"ࠧࡳࡧࡶࡹࡱࡺࠧᔣ"): bstack1ll_opy_ (u"ࠨࡨࡤ࡭ࡱ࡫ࡤࠨᔤ"),
                bstack1ll_opy_ (u"ࠩࡩࡥ࡮ࡲࡵࡳࡧࠪᔥ"): str(exception)
            })
        else:
            if step is not None:
                step.update({
                    bstack1ll_opy_ (u"ࠪࡶࡪࡹࡵ࡭ࡶࠪᔦ"): bstack1ll_opy_ (u"ࠫࡵࡧࡳࡴࡧࡧࠫᔧ"),
                })
        index = next((i for i, st in enumerate(bstack11lll1ll11l_opy_[bstack1ll_opy_ (u"ࠬࡹࡴࡦࡲࡶࠫᔨ")]) if st[bstack1ll_opy_ (u"࠭ࡩࡥࠩᔩ")] == step[bstack1ll_opy_ (u"ࠧࡪࡦࠪᔪ")]), None)
        if index is not None:
            bstack11lll1ll11l_opy_[bstack1ll_opy_ (u"ࠨࡵࡷࡩࡵࡹࠧᔫ")][index] = step
        instance.data[TestFramework.bstack11llllll11l_opy_] = bstack11lll1ll11l_opy_
    @staticmethod
    def __11llll11l1l_opy_(node):
        try:
            examples = []
            if hasattr(node, bstack1ll_opy_ (u"ࠩࡦࡥࡱࡲࡳࡱࡧࡦࠫᔬ")):
                examples = list(node.callspec.params[bstack1ll_opy_ (u"ࠪࡣࡵࡿࡴࡦࡵࡷࡣࡧࡪࡤࡠࡧࡻࡥࡲࡶ࡬ࡦࠩᔭ")].values())
            return examples
        except:
            return []
    def bstack1l1l11l1ll1_opy_(self, instance: bstack1ll1l1ll111_opy_, bstack1lllll11l1l_opy_: Tuple[bstack1ll1ll1lll1_opy_, bstack1ll1l1ll11l_opy_]):
        bstack11llll11l11_opy_ = (
            PytestBDDFramework.bstack11llllll111_opy_
            if bstack1lllll11l1l_opy_[1] == bstack1ll1l1ll11l_opy_.PRE
            else PytestBDDFramework.bstack1l111111l11_opy_
        )
        hook = PytestBDDFramework.bstack11lll1l1l11_opy_(instance, bstack11llll11l11_opy_)
        entries = hook.get(TestFramework.bstack11lllll11l1_opy_, []) if isinstance(hook, dict) else []
        entries.extend(TestFramework.bstack1llll1l111l_opy_(instance, TestFramework.bstack1l1111lll11_opy_, []))
        return entries
    def bstack1l1l1ll1111_opy_(self, instance: bstack1ll1l1ll111_opy_, bstack1lllll11l1l_opy_: Tuple[bstack1ll1ll1lll1_opy_, bstack1ll1l1ll11l_opy_]):
        bstack11llll11l11_opy_ = (
            PytestBDDFramework.bstack11llllll111_opy_
            if bstack1lllll11l1l_opy_[1] == bstack1ll1l1ll11l_opy_.PRE
            else PytestBDDFramework.bstack1l111111l11_opy_
        )
        PytestBDDFramework.bstack1l1111111ll_opy_(instance, bstack11llll11l11_opy_)
        TestFramework.bstack1llll1l111l_opy_(instance, TestFramework.bstack1l1111lll11_opy_, []).clear()
    @staticmethod
    def bstack11lll1l1l11_opy_(instance: bstack1ll1l1ll111_opy_, bstack11llll11l11_opy_: str):
        bstack1l111111111_opy_ = (
            PytestBDDFramework.bstack1l1111llll1_opy_
            if bstack11llll11l11_opy_ == PytestBDDFramework.bstack1l111111l11_opy_
            else PytestBDDFramework.bstack11llll11lll_opy_
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
        hook = PytestBDDFramework.bstack11lll1l1l11_opy_(instance, bstack11llll11l11_opy_)
        if isinstance(hook, dict):
            hook.get(TestFramework.bstack11lllll11l1_opy_, []).clear()
    @staticmethod
    def __1l1111l111l_opy_(instance: bstack1ll1l1ll111_opy_, *args):
        if len(args) < 2 or not callable(getattr(args[1], bstack1ll_opy_ (u"ࠦ࡬࡫ࡴࡠࡴࡨࡧࡴࡸࡤࡴࠤᔮ"), None)):
            return
        if os.getenv(bstack1ll_opy_ (u"࡙ࠧࡄࡌࡡࡆࡐࡎࡥࡆࡍࡃࡊࡣࡑࡕࡇࡔࠤᔯ"), bstack1ll_opy_ (u"ࠨ࠱ࠣᔰ")) != bstack1ll_opy_ (u"ࠢ࠲ࠤᔱ"):
            PytestBDDFramework.logger.warning(bstack1ll_opy_ (u"ࠣ࡫ࡪࡲࡴࡸࡩ࡯ࡩࠣࡧࡦࡶ࡬ࡰࡩࠥᔲ"))
            return
        bstack1l111l111l1_opy_ = {
            bstack1ll_opy_ (u"ࠤࡶࡩࡹࡻࡰࠣᔳ"): (PytestBDDFramework.bstack11llllll111_opy_, PytestBDDFramework.bstack11llll11lll_opy_),
            bstack1ll_opy_ (u"ࠥࡸࡪࡧࡲࡥࡱࡺࡲࠧᔴ"): (PytestBDDFramework.bstack1l111111l11_opy_, PytestBDDFramework.bstack1l1111llll1_opy_),
        }
        for when in (bstack1ll_opy_ (u"ࠦࡸ࡫ࡴࡶࡲࠥᔵ"), bstack1ll_opy_ (u"ࠧࡩࡡ࡭࡮ࠥᔶ"), bstack1ll_opy_ (u"ࠨࡴࡦࡣࡵࡨࡴࡽ࡮ࠣᔷ")):
            bstack1l1111ll1l1_opy_ = args[1].get_records(when)
            if not bstack1l1111ll1l1_opy_:
                continue
            records = [
                bstack1ll1l111111_opy_(
                    kind=TestFramework.bstack1l1l11ll1ll_opy_,
                    message=r.message,
                    level=r.levelname if hasattr(r, bstack1ll_opy_ (u"ࠢ࡭ࡧࡹࡩࡱࡴࡡ࡮ࡧࠥᔸ")) and r.levelname else None,
                    timestamp=(
                        datetime.fromtimestamp(r.created, tz=timezone.utc)
                        if hasattr(r, bstack1ll_opy_ (u"ࠣࡥࡵࡩࡦࡺࡥࡥࠤᔹ")) and r.created
                        else None
                    ),
                )
                for r in bstack1l1111ll1l1_opy_
                if isinstance(getattr(r, bstack1ll_opy_ (u"ࠤࡰࡩࡸࡹࡡࡨࡧࠥᔺ"), None), str) and r.message.strip()
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
    def __1l11111l1ll_opy_(args) -> Dict[str, Any]:
        request, feature, scenario = args
        bstack11l111l11l_opy_ = request.node.nodeid
        test_name = PytestBDDFramework.__11lll1l1ll1_opy_(request.node, scenario)
        bstack11llll11ll1_opy_ = feature.filename
        if not bstack11l111l11l_opy_ or not test_name or not bstack11llll11ll1_opy_:
            return None
        code = None
        return {
            TestFramework.bstack1ll111lll1l_opy_: uuid4().__str__(),
            TestFramework.bstack11llllll1ll_opy_: bstack11l111l11l_opy_,
            TestFramework.bstack1ll111ll111_opy_: test_name,
            TestFramework.bstack1l1l111l11l_opy_: bstack11l111l11l_opy_,
            TestFramework.bstack1l1111l11l1_opy_: bstack11llll11ll1_opy_,
            TestFramework.bstack11lllll1l11_opy_: PytestBDDFramework.__1l111l11111_opy_(feature, scenario),
            TestFramework.bstack1l11111lll1_opy_: code,
            TestFramework.bstack1l11l1ll11l_opy_: TestFramework.bstack1l11111111l_opy_,
            TestFramework.bstack1l111lll11l_opy_: test_name
        }
    @staticmethod
    def __11lll1l1ll1_opy_(node, scenario):
        if hasattr(node, bstack1ll_opy_ (u"ࠪࡧࡦࡲ࡬ࡴࡲࡨࡧࠬᔻ")):
            parts = node.nodeid.rsplit(bstack1ll_opy_ (u"ࠦࡠࠨᔼ"))
            params = parts[-1]
            return bstack1ll_opy_ (u"ࠧࢁࡽࠡ࡝ࡾࢁࠧᔽ").format(scenario.name, params)
        return scenario.name
    @staticmethod
    def __1l111l11111_opy_(feature, scenario) -> List[str]:
        return (list(feature.tags) if hasattr(feature, bstack1ll_opy_ (u"࠭ࡴࡢࡩࡶࠫᔾ")) else []) + (list(scenario.tags) if hasattr(scenario, bstack1ll_opy_ (u"ࠧࡵࡣࡪࡷࠬᔿ")) else [])
    @staticmethod
    def __1l1111ll1ll_opy_(location):
        return bstack1ll_opy_ (u"ࠣ࠼࠽ࠦᕀ").join(filter(lambda x: isinstance(x, str), location))