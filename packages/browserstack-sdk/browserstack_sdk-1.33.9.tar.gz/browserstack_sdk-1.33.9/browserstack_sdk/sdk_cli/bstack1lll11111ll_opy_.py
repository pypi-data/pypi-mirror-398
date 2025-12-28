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
from browserstack_sdk.sdk_cli.bstack1lll11ll1l1_opy_ import bstack1ll1lll1l1l_opy_
from browserstack_sdk.sdk_cli.bstack1lll1lll1l1_opy_ import (
    bstack1llll11l1l1_opy_,
    bstack1lllll111l1_opy_,
    bstack1llll111ll1_opy_,
)
from browserstack_sdk.sdk_cli.bstack1lll11lll11_opy_ import bstack1ll1llll1l1_opy_
from typing import Tuple, Callable, Any
import grpc
from browserstack_sdk import sdk_pb2 as structs
from browserstack_sdk.sdk_cli.bstack1lll11ll1l1_opy_ import bstack1ll1lll1l1l_opy_
from bstack_utils.measure import measure
from bstack_utils.constants import *
import traceback
import os
import time
class bstack1lll1l1l11l_opy_(bstack1ll1lll1l1l_opy_):
    bstack1ll111l1l1l_opy_ = False
    def __init__(self):
        super().__init__()
        bstack1ll1llll1l1_opy_.bstack1ll1111l11l_opy_((bstack1llll11l1l1_opy_.bstack1llll1l1111_opy_, bstack1lllll111l1_opy_.PRE), self.bstack1l1lll111ll_opy_)
    def is_enabled(self) -> bool:
        return True
    def bstack1l1lll111ll_opy_(
        self,
        f: bstack1ll1llll1l1_opy_,
        driver: object,
        exec: Tuple[bstack1llll111ll1_opy_, str],
        bstack1lllll11l1l_opy_: Tuple[bstack1llll11l1l1_opy_, bstack1lllll111l1_opy_],
        result: Any,
        *args,
        **kwargs,
    ):
        hub_url = f.hub_url(driver)
        if f.bstack1l1lll11lll_opy_(hub_url):
            if not bstack1lll1l1l11l_opy_.bstack1ll111l1l1l_opy_:
                self.logger.warning(bstack1ll_opy_ (u"ࠥࡰࡴࡩࡡ࡭ࠢࡶࡩࡱ࡬࠭ࡩࡧࡤࡰࠥ࡬࡬ࡰࡹࠣࡨ࡮ࡹࡡࡣ࡮ࡨࡨࠥ࡬࡯ࡳࠢࡅࡶࡴࡽࡳࡦࡴࡖࡸࡦࡩ࡫ࠡ࡫ࡱࡪࡷࡧࠠࡴࡧࡶࡷ࡮ࡵ࡮ࡴࠢ࡫ࡹࡧࡥࡵࡳ࡮ࡀࠦኆ") + str(hub_url) + bstack1ll_opy_ (u"ࠦࠧኇ"))
                bstack1lll1l1l11l_opy_.bstack1ll111l1l1l_opy_ = True
            return
        command_name = f.bstack1ll11l1llll_opy_(*args)
        bstack1l1lll11l1l_opy_ = f.bstack1l1lll111l1_opy_(*args)
        if command_name and command_name.lower() == bstack1ll_opy_ (u"ࠧ࡬ࡩ࡯ࡦࡨࡰࡪࡳࡥ࡯ࡶࠥኈ") and bstack1l1lll11l1l_opy_:
            framework_session_id = f.session_id(driver)
            locator_type, locator_value = bstack1l1lll11l1l_opy_.get(bstack1ll_opy_ (u"ࠨࡵࡴ࡫ࡱ࡫ࠧ኉"), None), bstack1l1lll11l1l_opy_.get(bstack1ll_opy_ (u"ࠢࡷࡣ࡯ࡹࡪࠨኊ"), None)
            if not framework_session_id or not locator_type or not locator_value:
                self.logger.warning(bstack1ll_opy_ (u"ࠣࡽࡦࡳࡲࡳࡡ࡯ࡦࡢࡲࡦࡳࡥࡾ࠼ࠣࡱ࡮ࡹࡳࡪࡰࡪࠤ࡫ࡸࡡ࡮ࡧࡺࡳࡷࡱ࡟ࡴࡧࡶࡷ࡮ࡵ࡮ࡠ࡫ࡧࠤࡴࡸࠠࡢࡴࡪࡷ࠳ࡻࡳࡪࡰࡪࡁࢀࡲ࡯ࡤࡣࡷࡳࡷࡥࡴࡺࡲࡨࢁࠥࡵࡲࠡࡣࡵ࡫ࡸ࠴ࡶࡢ࡮ࡸࡩࡂࠨኋ") + str(locator_value) + bstack1ll_opy_ (u"ࠤࠥኌ"))
                return
            def bstack1lll1lllll1_opy_(driver, bstack1l1lll11ll1_opy_, *args, **kwargs):
                from selenium.common.exceptions import NoSuchElementException
                try:
                    result = bstack1l1lll11ll1_opy_(driver, *args, **kwargs)
                    response = self.bstack1l1lll1111l_opy_(
                        framework_session_id=framework_session_id,
                        is_success=True,
                        locator_type=locator_type,
                        locator_value=locator_value,
                    )
                    if response and response.execute_script:
                        driver.execute_script(response.execute_script)
                        self.logger.info(bstack1ll_opy_ (u"ࠥࡷࡺࡩࡣࡦࡵࡶ࠱ࡸࡩࡲࡪࡲࡷ࠾ࠥࡲ࡯ࡤࡣࡷࡳࡷࡥࡴࡺࡲࡨࡁࢀࡲ࡯ࡤࡣࡷࡳࡷࡥࡴࡺࡲࡨࢁࠥࡲ࡯ࡤࡣࡷࡳࡷࡥࡶࡢ࡮ࡸࡩࡂࠨኍ") + str(locator_value) + bstack1ll_opy_ (u"ࠦࠧ኎"))
                    else:
                        self.logger.warning(bstack1ll_opy_ (u"ࠧࡹࡵࡤࡥࡨࡷࡸ࠳࡮ࡰ࠯ࡶࡧࡷ࡯ࡰࡵ࠼ࠣࡰࡴࡩࡡࡵࡱࡵࡣࡹࡿࡰࡦ࠿ࡾࡰࡴࡩࡡࡵࡱࡵࡣࡹࡿࡰࡦࡿࠣࡰࡴࡩࡡࡵࡱࡵࡣࡻࡧ࡬ࡶࡧࡀࡿࡱࡵࡣࡢࡶࡲࡶࡤࡼࡡ࡭ࡷࡨࢁࠥࡸࡥࡴࡲࡲࡲࡸ࡫࠽ࠣ኏") + str(response) + bstack1ll_opy_ (u"ࠨࠢነ"))
                    return result
                except NoSuchElementException as e:
                    locator = (locator_type, locator_value)
                    return self.__1l1lll11111_opy_(
                        driver, bstack1l1lll11ll1_opy_, e, framework_session_id, locator, *args, **kwargs
                    )
            bstack1lll1lllll1_opy_.__name__ = command_name
            return bstack1lll1lllll1_opy_
    def __1l1lll11111_opy_(
        self,
        driver,
        bstack1l1lll11ll1_opy_: Callable,
        exception,
        framework_session_id: str,
        locator: Tuple[str, str],
        *args,
        **kwargs,
    ):
        try:
            locator_type, locator_value = locator
            response = self.bstack1l1lll1111l_opy_(
                framework_session_id=framework_session_id,
                is_success=False,
                locator_type=locator_type,
                locator_value=locator_value,
            )
            if response and response.execute_script:
                driver.execute_script(response.execute_script)
                self.logger.info(bstack1ll_opy_ (u"ࠢࡧࡣ࡬ࡰࡺࡸࡥ࠮ࡪࡨࡥࡱ࡯࡮ࡨ࠯ࡷࡶ࡮࡭ࡧࡦࡴࡨࡨ࠿ࠦ࡬ࡰࡥࡤࡸࡴࡸ࡟ࡵࡻࡳࡩࡂࢁ࡬ࡰࡥࡤࡸࡴࡸ࡟ࡵࡻࡳࡩࢂࠦ࡬ࡰࡥࡤࡸࡴࡸ࡟ࡷࡣ࡯ࡹࡪࡃࠢኑ") + str(locator_value) + bstack1ll_opy_ (u"ࠣࠤኒ"))
                bstack1l1lll1l111_opy_ = self.bstack1l1lll1l1l1_opy_(
                    framework_session_id=framework_session_id,
                    locator_type=locator_type,
                )
                self.logger.info(bstack1ll_opy_ (u"ࠤࡩࡥ࡮ࡲࡵࡳࡧ࠰࡬ࡪࡧ࡬ࡪࡰࡪ࠱ࡷ࡫ࡳࡶ࡮ࡷ࠾ࠥࡲ࡯ࡤࡣࡷࡳࡷࡥࡴࡺࡲࡨࡁࢀࡲ࡯ࡤࡣࡷࡳࡷࡥࡴࡺࡲࡨࢁࠥࡲ࡯ࡤࡣࡷࡳࡷࡥࡶࡢ࡮ࡸࡩࡂࢁ࡬ࡰࡥࡤࡸࡴࡸ࡟ࡷࡣ࡯ࡹࡪࢃࠠࡩࡧࡤࡰ࡮ࡴࡧࡠࡴࡨࡷࡺࡲࡴ࠾ࠤና") + str(bstack1l1lll1l111_opy_) + bstack1ll_opy_ (u"ࠥࠦኔ"))
                if bstack1l1lll1l111_opy_.success and args and len(args) > 1:
                    args[1].update(
                        {
                            bstack1ll_opy_ (u"ࠦࡺࡹࡩ࡯ࡩࠥን"): bstack1l1lll1l111_opy_.locator_type,
                            bstack1ll_opy_ (u"ࠧࡼࡡ࡭ࡷࡨࠦኖ"): bstack1l1lll1l111_opy_.locator_value,
                        }
                    )
                    return bstack1l1lll11ll1_opy_(driver, *args, **kwargs)
                elif os.environ.get(bstack1ll_opy_ (u"ࠨࡂࡓࡑ࡚ࡗࡊࡘࡓࡕࡃࡆࡏࡤࡇࡉࡠࡆࡈࡆ࡚ࡍࠢኗ"), False):
                    self.logger.info(bstack1ll1ll111ll_opy_ (u"ࠢࡧࡣ࡬ࡰࡺࡸࡥ࠮ࡪࡨࡥࡱ࡯࡮ࡨ࠯ࡵࡩࡸࡻ࡬ࡵ࠯ࡰ࡭ࡸࡹࡩ࡯ࡩ࠽ࠤࡸࡲࡥࡦࡲࠫ࠷࠵࠯ࠠ࡭ࡧࡷࡸ࡮ࡴࡧࠡࡻࡲࡹࠥ࡯࡮ࡴࡲࡨࡧࡹࠦࡴࡩࡧࠣࡦࡷࡵࡷࡴࡧࡵࠤࡪࡾࡴࡦࡰࡶ࡭ࡴࡴࠠ࡭ࡱࡪࡷࠧኘ"))
                    time.sleep(300)
            else:
                self.logger.warning(bstack1ll_opy_ (u"ࠣࡨࡤ࡭ࡱࡻࡲࡦ࠯ࡱࡳ࠲ࡹࡣࡳ࡫ࡳࡸ࠿ࠦ࡬ࡰࡥࡤࡸࡴࡸ࡟ࡵࡻࡳࡩࡂࢁ࡬ࡰࡥࡤࡸࡴࡸ࡟ࡵࡻࡳࡩࢂࠦ࡬ࡰࡥࡤࡸࡴࡸ࡟ࡷࡣ࡯ࡹࡪࡃࡻ࡭ࡱࡦࡥࡹࡵࡲࡠࡸࡤࡰࡺ࡫ࡽࠡࡴࡨࡷࡵࡵ࡮ࡴࡧࡀࠦኙ") + str(response) + bstack1ll_opy_ (u"ࠤࠥኚ"))
        except Exception as err:
            self.logger.warning(bstack1ll_opy_ (u"ࠥࡪࡦ࡯࡬ࡶࡴࡨ࠱࡭࡫ࡡ࡭࡫ࡱ࡫࠲ࡸࡥࡴࡷ࡯ࡸ࠿ࠦࡥࡳࡴࡲࡶ࠿ࠦࠢኛ") + str(err) + bstack1ll_opy_ (u"ࠦࠧኜ"))
        raise exception
    @measure(event_name=EVENTS.bstack1l1lll1l11l_opy_, stage=STAGE.bstack1l1lll1ll1_opy_)
    def bstack1l1lll1111l_opy_(
        self,
        framework_session_id: str,
        is_success: bool,
        locator_type: str,
        locator_value: str,
        platform_index=bstack1ll_opy_ (u"ࠧ࠶ࠢኝ"),
    ):
        self.bstack1ll111lll11_opy_()
        req = structs.AISelfHealStepRequest()
        req.bin_session_id = self.bin_session_id
        req.platform_index = platform_index
        req.framework_session_id = framework_session_id
        req.is_success = is_success
        req.test_name = bstack1ll_opy_ (u"ࠨࠢኞ")
        req.locator_type = locator_type
        req.locator_value = locator_value
        try:
            r = self.bstack1ll1l11lll1_opy_.AISelfHealStep(req)
            self.logger.info(bstack1ll_opy_ (u"ࠢࡳࡧࡦࡩ࡮ࡼࡥࡥࠢࡩࡶࡴࡳࠠࡴࡧࡵࡺࡪࡸ࠺ࠡࠤኟ") + str(r) + bstack1ll_opy_ (u"ࠣࠤአ"))
            return r
        except grpc.RpcError as e:
            self.logger.error(bstack1ll_opy_ (u"ࠤࡵࡴࡨ࠳ࡥࡳࡴࡲࡶ࠿ࠦࠢኡ") + str(e) + bstack1ll_opy_ (u"ࠥࠦኢ"))
            traceback.print_exc()
            raise e
    @measure(event_name=EVENTS.bstack1l1lll11l11_opy_, stage=STAGE.bstack1l1lll1ll1_opy_)
    def bstack1l1lll1l1l1_opy_(self, framework_session_id: str, locator_type: str, platform_index=bstack1ll_opy_ (u"ࠦ࠵ࠨኣ")):
        self.bstack1ll111lll11_opy_()
        req = structs.AISelfHealGetRequest()
        req.bin_session_id = self.bin_session_id
        req.platform_index = platform_index
        req.framework_session_id = framework_session_id
        req.locator_type = locator_type
        try:
            r = self.bstack1ll1l11lll1_opy_.AISelfHealGetResult(req)
            self.logger.info(bstack1ll_opy_ (u"ࠧࡸࡥࡤࡧ࡬ࡺࡪࡪࠠࡧࡴࡲࡱࠥࡹࡥࡳࡸࡨࡶ࠿ࠦࠢኤ") + str(r) + bstack1ll_opy_ (u"ࠨࠢእ"))
            return r
        except grpc.RpcError as e:
            self.logger.error(bstack1ll_opy_ (u"ࠢࡳࡲࡦ࠱ࡪࡸࡲࡰࡴ࠽ࠤࠧኦ") + str(e) + bstack1ll_opy_ (u"ࠣࠤኧ"))
            traceback.print_exc()
            raise e