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
import os
import grpc
from browserstack_sdk import sdk_pb2 as structs
from packaging import version
import traceback
from browserstack_sdk.sdk_cli.bstack1lll11ll1l1_opy_ import bstack1ll1lll1l1l_opy_
from browserstack_sdk.sdk_cli.bstack1lll1lll1l1_opy_ import (
    bstack1llll11l1l1_opy_,
    bstack1lllll111l1_opy_,
    bstack1llll111ll1_opy_,
)
from browserstack_sdk.sdk_cli.bstack1lll11lll11_opy_ import bstack1ll1llll1l1_opy_
from datetime import datetime
from typing import Tuple, Any
from bstack_utils.messages import bstack1l1ll1ll1_opy_
from bstack_utils.measure import measure
from bstack_utils.constants import *
import threading
import os
from bstack_utils.bstack11ll1llll1_opy_ import bstack1lll1ll1l1l_opy_
class bstack1ll11lll111_opy_(bstack1ll1lll1l1l_opy_):
    bstack1l11l111l1l_opy_ = bstack1ll_opy_ (u"ࠧࡸࡥࡨ࡫ࡶࡸࡪࡸ࡟ࡪࡰ࡬ࡸࠧᏊ")
    bstack1l11l1111ll_opy_ = bstack1ll_opy_ (u"ࠨࡲࡦࡩ࡬ࡷࡹ࡫ࡲࡠࡵࡷࡥࡷࡺࠢᏋ")
    bstack1l11l1l1111_opy_ = bstack1ll_opy_ (u"ࠢࡳࡧࡪ࡭ࡸࡺࡥࡳࡡࡶࡸࡴࡶࠢᏌ")
    def __init__(self, bstack1lll111l111_opy_):
        super().__init__()
        bstack1ll1llll1l1_opy_.bstack1ll1111l11l_opy_((bstack1llll11l1l1_opy_.bstack1llll1l1l1l_opy_, bstack1lllll111l1_opy_.PRE), self.bstack1l11l1ll111_opy_)
        bstack1ll1llll1l1_opy_.bstack1ll1111l11l_opy_((bstack1llll11l1l1_opy_.bstack1llll1l1111_opy_, bstack1lllll111l1_opy_.PRE), self.bstack1l1lll111ll_opy_)
        bstack1ll1llll1l1_opy_.bstack1ll1111l11l_opy_((bstack1llll11l1l1_opy_.bstack1llll1l1111_opy_, bstack1lllll111l1_opy_.POST), self.bstack1l11l111ll1_opy_)
        bstack1ll1llll1l1_opy_.bstack1ll1111l11l_opy_((bstack1llll11l1l1_opy_.bstack1llll1l1111_opy_, bstack1lllll111l1_opy_.POST), self.bstack1l11l11l11l_opy_)
        bstack1ll1llll1l1_opy_.bstack1ll1111l11l_opy_((bstack1llll11l1l1_opy_.QUIT, bstack1lllll111l1_opy_.POST), self.bstack1l11l1l1l1l_opy_)
    def is_enabled(self) -> bool:
        return True
    def bstack1l11l1ll111_opy_(
        self,
        f: bstack1ll1llll1l1_opy_,
        driver: object,
        exec: Tuple[bstack1llll111ll1_opy_, str],
        bstack1lllll11l1l_opy_: Tuple[bstack1llll11l1l1_opy_, bstack1lllll111l1_opy_],
        result: Any,
        *args,
        **kwargs,
    ):
        instance, method_name = exec
        if method_name != bstack1ll_opy_ (u"ࠣࡡࡢ࡭ࡳ࡯ࡴࡠࡡࠥᏍ"):
            return
        def wrapped(driver, init, *args, **kwargs):
            url = None
            try:
                if isinstance(kwargs.get(bstack1ll_opy_ (u"ࠤࡦࡳࡲࡳࡡ࡯ࡦࡢࡩࡽ࡫ࡣࡶࡶࡲࡶࠧᏎ")), str):
                    url = kwargs.get(bstack1ll_opy_ (u"ࠥࡧࡴࡳ࡭ࡢࡰࡧࡣࡪࡾࡥࡤࡷࡷࡳࡷࠨᏏ"))
                elif hasattr(kwargs.get(bstack1ll_opy_ (u"ࠦࡨࡵ࡭࡮ࡣࡱࡨࡤ࡫ࡸࡦࡥࡸࡸࡴࡸࠢᏐ")), bstack1ll_opy_ (u"ࠬࡥࡣ࡭࡫ࡨࡲࡹࡥࡣࡰࡰࡩ࡭࡬࠭Ꮡ")):
                    url = kwargs.get(bstack1ll_opy_ (u"ࠨࡣࡰ࡯ࡰࡥࡳࡪ࡟ࡦࡺࡨࡧࡺࡺ࡯ࡳࠤᏒ"))._client_config.remote_server_addr
                else:
                    url = kwargs.get(bstack1ll_opy_ (u"ࠢࡤࡱࡰࡱࡦࡴࡤࡠࡧࡻࡩࡨࡻࡴࡰࡴࠥᏓ"))._url
            except Exception as e:
                url = bstack1ll_opy_ (u"ࠨࠩᏔ")
                self.logger.error(bstack1ll_opy_ (u"ࠤࡈࡶࡷࡵࡲࠡࡹ࡫࡭ࡱ࡫ࠠࡨࡧࡷࡸ࡮ࡴࡧࠡࡷࡵࡰࠥ࡬ࡲࡰ࡯ࠣࡨࡷ࡯ࡶࡦࡴ࠽ࠤࢀࢃࠢᏕ").format(e))
            self.logger.info(bstack1ll_opy_ (u"ࠥࡖࡪࡳ࡯ࡵࡧࠣࡗࡪࡸࡶࡦࡴࠣࡅࡩࡪࡲࡦࡵࡶࠤࡧ࡫ࡩ࡯ࡩࠣࡴࡦࡹࡳࡦࡦࠣࡥࡸࠦ࠺ࠡࡽࢀࠦᏖ").format(str(url)))
            self.bstack1l111llllll_opy_(instance, url, f, kwargs)
            self.logger.info(bstack1ll_opy_ (u"ࠦࡩࡸࡩࡷࡧࡵ࠲ࢀࡳࡥࡵࡪࡲࡨࡤࡴࡡ࡮ࡧࢀࠤࡵࡲࡡࡵࡨࡲࡶࡲࡥࡩ࡯ࡦࡨࡼࡂࢁࡰ࡭ࡣࡷࡪࡴࡸ࡭ࡠ࡫ࡱࡨࡪࡾࡽ࠻ࠢࡤࡶ࡬ࡹ࠽ࡼࡣࡵ࡫ࡸࢃࠠ࡬ࡹࡤࡶ࡬ࡹ࠽ࡼ࡭ࡺࡥࡷ࡭ࡳࡾࠤᏗ").format(method_name=method_name, platform_index=f.platform_index, args=args, kwargs=kwargs))
            threading.current_thread().bstackSessionDriver = driver
            return init(driver, *args, **kwargs)
        return wrapped
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
        instance, method_name = exec
        if f.bstack1llll1l111l_opy_(instance, bstack1ll11lll111_opy_.bstack1l11l111l1l_opy_, False):
            return
        if not f.bstack1llll11ll11_opy_(instance, bstack1ll1llll1l1_opy_.bstack1l1lll1l1ll_opy_):
            return
        platform_index = f.bstack1llll1l111l_opy_(instance, bstack1ll1llll1l1_opy_.bstack1l1lll1l1ll_opy_)
        if f.bstack1l1llll11l1_opy_(method_name, *args) and len(args) > 1:
            bstack11l1l1l1ll_opy_ = datetime.now()
            hub_url = bstack1ll1llll1l1_opy_.hub_url(driver)
            self.logger.warning(bstack1ll_opy_ (u"ࠧ࡮ࡵࡣࡡࡸࡶࡱࡃࠢᏘ") + str(hub_url) + bstack1ll_opy_ (u"ࠨࠢᏙ"))
            bstack1l11l11111l_opy_ = args[1][bstack1ll_opy_ (u"ࠢࡤࡣࡳࡥࡧ࡯࡬ࡪࡶ࡬ࡩࡸࠨᏚ")] if isinstance(args[1], dict) and bstack1ll_opy_ (u"ࠣࡥࡤࡴࡦࡨࡩ࡭࡫ࡷ࡭ࡪࡹࠢᏛ") in args[1] else None
            bstack1l11l111111_opy_ = bstack1ll_opy_ (u"ࠤࡤࡰࡼࡧࡹࡴࡏࡤࡸࡨ࡮ࠢᏜ")
            if isinstance(bstack1l11l11111l_opy_, dict):
                bstack11l1l1l1ll_opy_ = datetime.now()
                r = self.bstack1l11l1l1lll_opy_(
                    instance.ref(),
                    platform_index,
                    f.framework_name,
                    f.framework_version,
                    hub_url
                )
                instance.bstack11ll11ll1_opy_(bstack1ll_opy_ (u"ࠥ࡫ࡷࡶࡣ࠻ࡴࡨ࡫࡮ࡹࡴࡦࡴࡢ࡭ࡳ࡯ࡴࠣᏝ"), datetime.now() - bstack11l1l1l1ll_opy_)
                try:
                    if not r.success:
                        self.logger.info(bstack1ll_opy_ (u"ࠦࡸࡵ࡭ࡦࡶ࡫࡭ࡳ࡭ࠠࡸࡧࡱࡸࠥࡽࡲࡰࡰࡪ࠾ࠥࠨᏞ") + str(r) + bstack1ll_opy_ (u"ࠧࠨᏟ"))
                        return
                    if r.hub_url:
                        f.bstack1l11l1l1l11_opy_(instance, driver, r.hub_url)
                        f.bstack1llll1lll11_opy_(instance, bstack1ll11lll111_opy_.bstack1l11l111l1l_opy_, True)
                except Exception as e:
                    self.logger.error(bstack1ll_opy_ (u"ࠨࡥࡳࡴࡲࡶࠧᏠ"), e)
    def bstack1l11l111ll1_opy_(
        self,
        f: bstack1ll1llll1l1_opy_,
        driver: object,
        exec: Tuple[bstack1llll111ll1_opy_, str],
        bstack1lllll11l1l_opy_: Tuple[bstack1llll11l1l1_opy_, bstack1lllll111l1_opy_],
        result: Any,
        *args,
        **kwargs,
    ):
            session_id = bstack1ll1llll1l1_opy_.session_id(driver)
            if session_id:
                bstack1l11l1l1ll1_opy_ = bstack1ll_opy_ (u"ࠢࡼࡿ࠽ࡷࡹࡧࡲࡵࠤᏡ").format(session_id)
                bstack1lll1ll1l1l_opy_.mark(bstack1l11l1l1ll1_opy_)
    def bstack1l11l11l11l_opy_(
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
        if f.bstack1llll1l111l_opy_(instance, bstack1ll11lll111_opy_.bstack1l11l1111ll_opy_, False):
            return
        ref = instance.ref()
        hub_url = bstack1ll1llll1l1_opy_.hub_url(driver)
        if not hub_url:
            self.logger.warning(bstack1ll_opy_ (u"ࠣࡨࡤ࡭ࡱ࡫ࡤࠡࡶࡲࠤࡵࡧࡲࡴࡧࠣ࡬ࡺࡨ࡟ࡶࡴ࡯ࡁࠧᏢ") + str(hub_url) + bstack1ll_opy_ (u"ࠤࠥᏣ"))
            return
        framework_session_id = bstack1ll1llll1l1_opy_.session_id(driver)
        if not framework_session_id:
            self.logger.warning(bstack1ll_opy_ (u"ࠥࡪࡦ࡯࡬ࡦࡦࠣࡸࡴࠦࡰࡢࡴࡶࡩࠥ࡬ࡲࡢ࡯ࡨࡻࡴࡸ࡫ࡠࡵࡨࡷࡸ࡯࡯࡯ࡡ࡬ࡨࡂࠨᏤ") + str(framework_session_id) + bstack1ll_opy_ (u"ࠦࠧᏥ"))
            return
        if bstack1ll1llll1l1_opy_.bstack1l11l111l11_opy_(*args) == bstack1ll1llll1l1_opy_.bstack1l11l11lll1_opy_:
            bstack1l111llll1l_opy_ = bstack1ll_opy_ (u"ࠧࢁࡽ࠻ࡧࡱࡨࠧᏦ").format(framework_session_id)
            bstack1l11l1l1ll1_opy_ = bstack1ll_opy_ (u"ࠨࡻࡾ࠼ࡶࡸࡦࡸࡴࠣᏧ").format(framework_session_id)
            bstack1lll1ll1l1l_opy_.end(
                label=bstack1ll_opy_ (u"ࠢࡴࡦ࡮࠾ࡩࡸࡩࡷࡧࡵ࠾ࡵࡵࡳࡵ࠯࡬ࡲ࡮ࡺࡩࡢ࡮࡬ࡾࡦࡺࡩࡰࡰࠥᏨ"),
                start=bstack1l11l1l1ll1_opy_,
                end=bstack1l111llll1l_opy_,
                status=True,
                failure=None
            )
            bstack11l1l1l1ll_opy_ = datetime.now()
            r = self.bstack1l11l1111l1_opy_(
                ref,
                f.bstack1llll1l111l_opy_(instance, bstack1ll1llll1l1_opy_.bstack1l1lll1l1ll_opy_, 0),
                f.framework_name,
                f.framework_version,
                framework_session_id,
                hub_url,
            )
            instance.bstack11ll11ll1_opy_(bstack1ll_opy_ (u"ࠣࡩࡵࡴࡨࡀࡲࡦࡩ࡬ࡷࡹ࡫ࡲࡠࡵࡷࡥࡷࡺࠢᏩ"), datetime.now() - bstack11l1l1l1ll_opy_)
            f.bstack1llll1lll11_opy_(instance, bstack1ll11lll111_opy_.bstack1l11l1111ll_opy_, r.success)
    def bstack1l11l1l1l1l_opy_(
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
        if f.bstack1llll1l111l_opy_(instance, bstack1ll11lll111_opy_.bstack1l11l1l1111_opy_, False):
            return
        ref = instance.ref()
        framework_session_id = bstack1ll1llll1l1_opy_.session_id(driver)
        hub_url = bstack1ll1llll1l1_opy_.hub_url(driver)
        bstack11l1l1l1ll_opy_ = datetime.now()
        r = self.bstack1l11l11l111_opy_(
            ref,
            f.bstack1llll1l111l_opy_(instance, bstack1ll1llll1l1_opy_.bstack1l1lll1l1ll_opy_, 0),
            f.framework_name,
            f.framework_version,
            framework_session_id,
            hub_url,
        )
        instance.bstack11ll11ll1_opy_(bstack1ll_opy_ (u"ࠤࡪࡶࡵࡩ࠺ࡳࡧࡪ࡭ࡸࡺࡥࡳࡡࡶࡸࡴࡶࠢᏪ"), datetime.now() - bstack11l1l1l1ll_opy_)
        f.bstack1llll1lll11_opy_(instance, bstack1ll11lll111_opy_.bstack1l11l1l1111_opy_, r.success)
    @measure(event_name=EVENTS.bstack1ll1l111ll_opy_, stage=STAGE.bstack1l1lll1ll1_opy_)
    def bstack1l11lll11l1_opy_(self, platform_index: int, url: str, ref, user_input_params: bytes):
        req = structs.DriverInitRequest()
        req.bin_session_id = self.bin_session_id
        req.platform_index = platform_index
        req.user_input_params = user_input_params
        req.ref = ref
        req.hub_url = url
        self.logger.debug(bstack1ll_opy_ (u"ࠥࡶࡪ࡭ࡩࡴࡶࡨࡶࡤࡽࡥࡣࡦࡵ࡭ࡻ࡫ࡲࡠ࡫ࡱ࡭ࡹࡀࠠࠣᏫ") + str(req) + bstack1ll_opy_ (u"ࠦࠧᏬ"))
        try:
            r = self.bstack1ll1l11lll1_opy_.DriverInit(req)
            if not r.success:
                self.logger.debug(bstack1ll_opy_ (u"ࠧࡸࡥࡤࡧ࡬ࡺࡪࡪࠠࡧࡴࡲࡱࠥࡹࡥࡳࡸࡨࡶ࠿ࠦࡳࡶࡥࡦࡩࡸࡹ࠽ࠣᏭ") + str(r.success) + bstack1ll_opy_ (u"ࠨࠢᏮ"))
            return r
        except grpc.RpcError as e:
            self.logger.error(bstack1ll_opy_ (u"ࠢࡳࡲࡦ࠱ࡪࡸࡲࡰࡴ࠽ࠤࠧᏯ") + str(e) + bstack1ll_opy_ (u"ࠣࠤᏰ"))
            traceback.print_exc()
            raise e
    @measure(event_name=EVENTS.bstack1l11l11llll_opy_, stage=STAGE.bstack1l1lll1ll1_opy_)
    def bstack1l11l1l1lll_opy_(
        self,
        ref: str,
        platform_index: int,
        framework_name: str,
        framework_version: str,
        hub_url: str
    ):
        self.bstack1ll111lll11_opy_()
        req = structs.AutomationFrameworkInitRequest()
        req.ref = ref
        req.bin_session_id = self.bin_session_id
        req.platform_index = platform_index
        req.framework_name = framework_name
        req.framework_version = framework_version
        req.hub_url = hub_url
        self.logger.debug(bstack1ll_opy_ (u"ࠤࡵࡩ࡬࡯ࡳࡵࡧࡵࡣ࡮ࡴࡩࡵ࠼ࠣࠦᏱ") + str(req) + bstack1ll_opy_ (u"ࠥࠦᏲ"))
        try:
            r = self.bstack1ll1l11lll1_opy_.AutomationFrameworkInit(req)
            if not r.success:
                self.logger.debug(bstack1ll_opy_ (u"ࠦࡷ࡫ࡣࡦ࡫ࡹࡩࡩࠦࡦࡳࡱࡰࠤࡸ࡫ࡲࡷࡧࡵ࠾ࠥࡹࡵࡤࡥࡨࡷࡸࡃࠢᏳ") + str(r.success) + bstack1ll_opy_ (u"ࠧࠨᏴ"))
            return r
        except grpc.RpcError as e:
            self.logger.error(bstack1ll_opy_ (u"ࠨࡲࡱࡥ࠰ࡩࡷࡸ࡯ࡳ࠼ࠣࠦᏵ") + str(e) + bstack1ll_opy_ (u"ࠢࠣ᏶"))
            traceback.print_exc()
            raise e
    @measure(event_name=EVENTS.bstack1l11l11l1ll_opy_, stage=STAGE.bstack1l1lll1ll1_opy_)
    def bstack1l11l1111l1_opy_(
        self,
        ref: str,
        platform_index: int,
        framework_name: str,
        framework_version: str,
        framework_session_id: str,
        hub_url: str,
    ):
        self.bstack1ll111lll11_opy_()
        req = structs.AutomationFrameworkStartRequest()
        req.ref = ref
        req.bin_session_id = self.bin_session_id
        req.platform_index = platform_index
        req.framework_name = framework_name
        req.framework_version = framework_version
        req.framework_session_id = framework_session_id
        req.hub_url = hub_url
        self.logger.debug(bstack1ll_opy_ (u"ࠣࡴࡨ࡫࡮ࡹࡴࡦࡴࡢࡷࡹࡧࡲࡵ࠼ࠣࠦ᏷") + str(req) + bstack1ll_opy_ (u"ࠤࠥᏸ"))
        try:
            r = self.bstack1ll1l11lll1_opy_.AutomationFrameworkStart(req)
            if not r.success:
                self.logger.debug(bstack1ll_opy_ (u"ࠥࡶࡪࡩࡥࡪࡸࡨࡨࠥ࡬ࡲࡰ࡯ࠣࡷࡪࡸࡶࡦࡴ࠽ࠤࠧᏹ") + str(r) + bstack1ll_opy_ (u"ࠦࠧᏺ"))
            return r
        except grpc.RpcError as e:
            self.logger.error(bstack1ll_opy_ (u"ࠧࡸࡰࡤ࠯ࡨࡶࡷࡵࡲ࠻ࠢࠥᏻ") + str(e) + bstack1ll_opy_ (u"ࠨࠢᏼ"))
            traceback.print_exc()
            raise e
    @measure(event_name=EVENTS.bstack1l11l111lll_opy_, stage=STAGE.bstack1l1lll1ll1_opy_)
    def bstack1l11l11l111_opy_(
        self,
        ref: str,
        platform_index: int,
        framework_name: str,
        framework_version: str,
        framework_session_id: str,
        hub_url: str,
    ):
        self.bstack1ll111lll11_opy_()
        req = structs.AutomationFrameworkStopRequest()
        req.ref = ref
        req.bin_session_id = self.bin_session_id
        req.platform_index = platform_index
        req.framework_name = framework_name
        req.framework_version = framework_version
        req.framework_session_id = framework_session_id
        req.hub_url = hub_url
        self.logger.debug(bstack1ll_opy_ (u"ࠢࡳࡧࡪ࡭ࡸࡺࡥࡳࡡࡶࡸࡴࡶ࠺ࠡࠤᏽ") + str(req) + bstack1ll_opy_ (u"ࠣࠤ᏾"))
        try:
            r = self.bstack1ll1l11lll1_opy_.AutomationFrameworkStop(req)
            if not r.success:
                self.logger.debug(bstack1ll_opy_ (u"ࠤࡵࡩࡨ࡫ࡩࡷࡧࡧࠤ࡫ࡸ࡯࡮ࠢࡶࡩࡷࡼࡥࡳ࠼ࠣࠦ᏿") + str(r) + bstack1ll_opy_ (u"ࠥࠦ᐀"))
            return r
        except grpc.RpcError as e:
            self.logger.error(bstack1ll_opy_ (u"ࠦࡷࡶࡣ࠮ࡧࡵࡶࡴࡸ࠺ࠡࠤᐁ") + str(e) + bstack1ll_opy_ (u"ࠧࠨᐂ"))
            traceback.print_exc()
            raise e
    @measure(event_name=EVENTS.bstack1l1lllll1_opy_, stage=STAGE.bstack1l1lll1ll1_opy_)
    def bstack1l111llllll_opy_(self, instance: bstack1llll111ll1_opy_, url: str, f: bstack1ll1llll1l1_opy_, kwargs):
        bstack1l11l11ll11_opy_ = version.parse(f.framework_version)
        bstack1l11l1l111l_opy_ = kwargs.get(bstack1ll_opy_ (u"ࠨ࡯ࡱࡶ࡬ࡳࡳࡹࠢᐃ"))
        bstack1l11l11l1l1_opy_ = kwargs.get(bstack1ll_opy_ (u"ࠢࡥࡧࡶ࡭ࡷ࡫ࡤࡠࡥࡤࡴࡦࡨࡩ࡭࡫ࡷ࡭ࡪࡹࠢᐄ"))
        bstack1l11llll1ll_opy_ = {}
        bstack1l111lllll1_opy_ = {}
        bstack1l11l1l11ll_opy_ = None
        bstack1l11l11ll1l_opy_ = {}
        if bstack1l11l11l1l1_opy_ is not None or bstack1l11l1l111l_opy_ is not None: # check top level caps
            if bstack1l11l11l1l1_opy_ is not None:
                bstack1l11l11ll1l_opy_[bstack1ll_opy_ (u"ࠨࡦࡨࡷ࡮ࡸࡥࡥࡡࡦࡥࡵࡧࡢࡪ࡮࡬ࡸ࡮࡫ࡳࠨᐅ")] = bstack1l11l11l1l1_opy_
            if bstack1l11l1l111l_opy_ is not None and callable(getattr(bstack1l11l1l111l_opy_, bstack1ll_opy_ (u"ࠤࡷࡳࡤࡩࡡࡱࡣࡥ࡭ࡱ࡯ࡴࡪࡧࡶࠦᐆ"))):
                bstack1l11l11ll1l_opy_[bstack1ll_opy_ (u"ࠪࡳࡵࡺࡩࡰࡰࡶࡣࡦࡹ࡟ࡤࡣࡳࡥࡧ࡯࡬ࡪࡶ࡬ࡩࡸ࠭ᐇ")] = bstack1l11l1l111l_opy_.to_capabilities()
        response = self.bstack1l11lll11l1_opy_(f.platform_index, url, instance.ref(), json.dumps(bstack1l11l11ll1l_opy_).encode(bstack1ll_opy_ (u"ࠦࡺࡺࡦ࠮࠺ࠥᐈ")))
        if response is not None and response.capabilities:
            bstack1l11llll1ll_opy_ = json.loads(response.capabilities.decode(bstack1ll_opy_ (u"ࠧࡻࡴࡧ࠯࠻ࠦᐉ")))
            if not bstack1l11llll1ll_opy_: # empty caps bstack1l11lllll11_opy_ bstack1l11ll1l1ll_opy_ bstack1l11lll1111_opy_ bstack1lll1l11ll1_opy_ or error in processing
                return
            bstack1l11l1l11ll_opy_ = f.bstack1ll1l1ll1ll_opy_[bstack1ll_opy_ (u"ࠨࡣࡳࡧࡤࡸࡪࡥ࡯ࡱࡶ࡬ࡳࡳࡹ࡟ࡧࡴࡲࡱࡤࡩࡡࡱࡵࠥᐊ")](bstack1l11llll1ll_opy_)
        if bstack1l11l1l111l_opy_ is not None and bstack1l11l11ll11_opy_ >= version.parse(bstack1ll_opy_ (u"ࠧ࠴࠰࠻࠲࠵࠭ᐋ")):
            bstack1l111lllll1_opy_ = None
        if (
                not bstack1l11l1l111l_opy_ and not bstack1l11l11l1l1_opy_
        ) or (
                bstack1l11l11ll11_opy_ < version.parse(bstack1ll_opy_ (u"ࠨ࠵࠱࠼࠳࠶ࠧᐌ"))
        ):
            bstack1l111lllll1_opy_ = {}
            bstack1l111lllll1_opy_.update(bstack1l11llll1ll_opy_)
        self.logger.info(bstack1l1ll1ll1_opy_)
        if os.environ.get(bstack1ll_opy_ (u"ࠤࡅࡖࡔ࡝ࡓࡆࡔࡖࡘࡆࡉࡋࡠࡃࡘࡘࡔࡓࡁࡕࡋࡒࡒࠧᐍ")).lower().__eq__(bstack1ll_opy_ (u"ࠥࡸࡷࡻࡥࠣᐎ")):
            kwargs.update(
                {
                    bstack1ll_opy_ (u"ࠦࡨࡵ࡭࡮ࡣࡱࡨࡤ࡫ࡸࡦࡥࡸࡸࡴࡸࠢᐏ"): f.bstack1l11l1l11l1_opy_,
                }
            )
        if bstack1l11l11ll11_opy_ >= version.parse(bstack1ll_opy_ (u"ࠬ࠺࠮࠲࠲࠱࠴ࠬᐐ")):
            if bstack1l11l11l1l1_opy_ is not None:
                del kwargs[bstack1ll_opy_ (u"ࠨࡤࡦࡵ࡬ࡶࡪࡪ࡟ࡤࡣࡳࡥࡧ࡯࡬ࡪࡶ࡬ࡩࡸࠨᐑ")]
            kwargs.update(
                {
                    bstack1ll_opy_ (u"ࠢࡰࡲࡷ࡭ࡴࡴࡳࠣᐒ"): bstack1l11l1l11ll_opy_,
                    bstack1ll_opy_ (u"ࠣ࡭ࡨࡩࡵࡥࡡ࡭࡫ࡹࡩࠧᐓ"): True,
                    bstack1ll_opy_ (u"ࠤࡩ࡭ࡱ࡫࡟ࡥࡧࡷࡩࡨࡺ࡯ࡳࠤᐔ"): None,
                }
            )
        elif bstack1l11l11ll11_opy_ >= version.parse(bstack1ll_opy_ (u"ࠪ࠷࠳࠾࠮࠱ࠩᐕ")):
            kwargs.update(
                {
                    bstack1ll_opy_ (u"ࠦࡩ࡫ࡳࡪࡴࡨࡨࡤࡩࡡࡱࡣࡥ࡭ࡱ࡯ࡴࡪࡧࡶࠦᐖ"): bstack1l111lllll1_opy_,
                    bstack1ll_opy_ (u"ࠧࡵࡰࡵ࡫ࡲࡲࡸࠨᐗ"): bstack1l11l1l11ll_opy_,
                    bstack1ll_opy_ (u"ࠨ࡫ࡦࡧࡳࡣࡦࡲࡩࡷࡧࠥᐘ"): True,
                    bstack1ll_opy_ (u"ࠢࡧ࡫࡯ࡩࡤࡪࡥࡵࡧࡦࡸࡴࡸࠢᐙ"): None,
                }
            )
        elif bstack1l11l11ll11_opy_ >= version.parse(bstack1ll_opy_ (u"ࠨ࠴࠱࠹࠸࠴࠰ࠨᐚ")):
            kwargs.update(
                {
                    bstack1ll_opy_ (u"ࠤࡧࡩࡸ࡯ࡲࡦࡦࡢࡧࡦࡶࡡࡣ࡫࡯࡭ࡹ࡯ࡥࡴࠤᐛ"): bstack1l111lllll1_opy_,
                    bstack1ll_opy_ (u"ࠥ࡯ࡪ࡫ࡰࡠࡣ࡯࡭ࡻ࡫ࠢᐜ"): True,
                    bstack1ll_opy_ (u"ࠦ࡫࡯࡬ࡦࡡࡧࡩࡹ࡫ࡣࡵࡱࡵࠦᐝ"): None,
                }
            )
        else:
            kwargs.update(
                {
                    bstack1ll_opy_ (u"ࠧࡪࡥࡴ࡫ࡵࡩࡩࡥࡣࡢࡲࡤࡦ࡮ࡲࡩࡵ࡫ࡨࡷࠧᐞ"): bstack1l111lllll1_opy_,
                    bstack1ll_opy_ (u"ࠨ࡫ࡦࡧࡳࡣࡦࡲࡩࡷࡧࠥᐟ"): True,
                    bstack1ll_opy_ (u"ࠢࡧ࡫࡯ࡩࡤࡪࡥࡵࡧࡦࡸࡴࡸࠢᐠ"): None,
                }
            )