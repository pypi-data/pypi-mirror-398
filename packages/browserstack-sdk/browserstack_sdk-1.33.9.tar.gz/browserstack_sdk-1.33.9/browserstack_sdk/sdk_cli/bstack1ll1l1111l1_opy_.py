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
import copy
import asyncio
import threading
from browserstack_sdk import sdk_pb2 as structs
from packaging import version
import traceback
from browserstack_sdk.sdk_cli.bstack1lll11ll1l1_opy_ import bstack1ll1lll1l1l_opy_
from browserstack_sdk.sdk_cli.bstack1lll1lll1l1_opy_ import (
    bstack1llll11l1l1_opy_,
    bstack1lllll111l1_opy_,
    bstack1llll111ll1_opy_,
)
from bstack_utils.constants import *
from typing import Any, List, Union, Dict
from pathlib import Path
from browserstack_sdk.sdk_cli.bstack1ll1llll111_opy_ import bstack1ll1l1l111l_opy_
from datetime import datetime
from typing import Tuple, Any
from bstack_utils.messages import bstack1l1ll1ll1_opy_
from bstack_utils.helper import bstack1l1ll111lll_opy_
import threading
import os
import urllib.parse
class bstack1lll1l11111_opy_(bstack1ll1lll1l1l_opy_):
    def __init__(self, bstack1ll1lllllll_opy_):
        super().__init__()
        bstack1ll1l1l111l_opy_.bstack1ll1111l11l_opy_((bstack1llll11l1l1_opy_.bstack1llll1l1l1l_opy_, bstack1lllll111l1_opy_.PRE), self.bstack1l11lll1l11_opy_)
        bstack1ll1l1l111l_opy_.bstack1ll1111l11l_opy_((bstack1llll11l1l1_opy_.bstack1llll1l1l1l_opy_, bstack1lllll111l1_opy_.PRE), self.bstack1l11llll11l_opy_)
        bstack1ll1l1l111l_opy_.bstack1ll1111l11l_opy_((bstack1llll11l1l1_opy_.bstack1llll1111ll_opy_, bstack1lllll111l1_opy_.PRE), self.bstack1l11lll1l1l_opy_)
        bstack1ll1l1l111l_opy_.bstack1ll1111l11l_opy_((bstack1llll11l1l1_opy_.bstack1llll1l1111_opy_, bstack1lllll111l1_opy_.PRE), self.bstack1l11ll1ll11_opy_)
        bstack1ll1l1l111l_opy_.bstack1ll1111l11l_opy_((bstack1llll11l1l1_opy_.bstack1llll1l1l1l_opy_, bstack1lllll111l1_opy_.PRE), self.bstack1l11ll1lll1_opy_)
        bstack1ll1l1l111l_opy_.bstack1ll1111l11l_opy_((bstack1llll11l1l1_opy_.QUIT, bstack1lllll111l1_opy_.PRE), self.on_close)
        self.bstack1ll1lllllll_opy_ = bstack1ll1lllllll_opy_
    def is_enabled(self) -> bool:
        return True
    def bstack1l11lll1l11_opy_(
        self,
        f: bstack1ll1l1l111l_opy_,
        bstack1l11lll11ll_opy_: object,
        exec: Tuple[bstack1llll111ll1_opy_, str],
        bstack1lllll11l1l_opy_: Tuple[bstack1llll11l1l1_opy_, bstack1lllll111l1_opy_],
        result: Any,
        *args,
        **kwargs,
    ):
        instance, method_name = exec
        if method_name != bstack1ll_opy_ (u"ࠦࡱࡧࡵ࡯ࡥ࡫ࠦፒ"):
            return
        if not bstack1l1ll111lll_opy_():
            self.logger.debug(bstack1ll_opy_ (u"ࠧࡘࡥࡵࡷࡵࡲ࡮ࡴࡧࠡ࡫ࡱࠤࡱࡧࡵ࡯ࡥ࡫ࠤࡲ࡫ࡴࡩࡱࡧ࠰ࠥࡴ࡯ࡵࠢࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫ࠡࡵࡨࡷࡸ࡯࡯࡯ࠤፓ"))
            return
        def wrapped(bstack1l11lll11ll_opy_, launch, *args, **kwargs):
            response = self.bstack1l11lll11l1_opy_(f.platform_index, instance.ref(), json.dumps({bstack1ll_opy_ (u"࠭ࡩࡴࡒ࡯ࡥࡾࡽࡲࡪࡩ࡫ࡸࠬፔ"): True}).encode(bstack1ll_opy_ (u"ࠢࡶࡶࡩ࠱࠽ࠨፕ")))
            if response is not None and response.capabilities:
                if not bstack1l1ll111lll_opy_():
                    browser = launch(bstack1l11lll11ll_opy_)
                    return browser
                bstack1l11llll1ll_opy_ = json.loads(response.capabilities.decode(bstack1ll_opy_ (u"ࠣࡷࡷࡪ࠲࠾ࠢፖ")))
                if not bstack1l11llll1ll_opy_: # empty caps bstack1l11lllll11_opy_ bstack1l11ll1l1ll_opy_ bstack1l11lll1111_opy_ bstack1lll1l11ll1_opy_ or error in processing
                    return
                bstack1l11llll111_opy_ = PLAYWRIGHT_HUB_URL + urllib.parse.quote(json.dumps(bstack1l11llll1ll_opy_))
                f.bstack1llll1lll11_opy_(instance, bstack1ll1l1l111l_opy_.bstack1l11lll1ll1_opy_, bstack1l11llll111_opy_)
                f.bstack1llll1lll11_opy_(instance, bstack1ll1l1l111l_opy_.bstack1l11lllll1l_opy_, bstack1l11llll1ll_opy_)
                browser = bstack1l11lll11ll_opy_.connect(bstack1l11llll111_opy_)
                return browser
        return wrapped
    def bstack1l11lll1l1l_opy_(
        self,
        f: bstack1ll1l1l111l_opy_,
        Connection: object,
        exec: Tuple[bstack1llll111ll1_opy_, str],
        bstack1lllll11l1l_opy_: Tuple[bstack1llll11l1l1_opy_, bstack1lllll111l1_opy_],
        result: Any,
        *args,
        **kwargs,
    ):
        instance, method_name = exec
        if method_name != bstack1ll_opy_ (u"ࠤࡧ࡭ࡸࡶࡡࡵࡥ࡫ࠦፗ"):
            self.logger.debug(bstack1ll_opy_ (u"ࠥࡖࡪࡺࡵࡳࡰ࡬ࡲ࡬ࠦࡩ࡯ࠢࡧ࡭ࡸࡶࡡࡵࡥ࡫ࠤࡲ࡫ࡴࡩࡱࡧ࠰ࠥࡴ࡯ࡵࠢࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫ࠡࡵࡨࡷࡸ࡯࡯࡯ࠤፘ"))
            return
        if not bstack1l1ll111lll_opy_():
            return
        def wrapped(Connection, dispatch, *args, **kwargs):
            data = args[0]
            try:
                if args and args[0].get(bstack1ll_opy_ (u"ࠫࡵࡧࡲࡢ࡯ࡶࠫፙ"), {}).get(bstack1ll_opy_ (u"ࠬࡨࡳࡑࡣࡵࡥࡲࡹࠧፚ")):
                    bstack1l11llll1l1_opy_ = args[0][bstack1ll_opy_ (u"ࠨࡰࡢࡴࡤࡱࡸࠨ፛")][bstack1ll_opy_ (u"ࠢࡣࡵࡓࡥࡷࡧ࡭ࡴࠤ፜")]
                    session_id = bstack1l11llll1l1_opy_.get(bstack1ll_opy_ (u"ࠣࡵࡨࡷࡸ࡯࡯࡯ࡋࡧࠦ፝"))
                    f.bstack1llll1lll11_opy_(instance, bstack1ll1l1l111l_opy_.bstack1l11lll1lll_opy_, session_id)
            except Exception as e:
                self.logger.debug(bstack1ll_opy_ (u"ࠤࡈࡼࡨ࡫ࡰࡵ࡫ࡲࡲࠥ࡯࡮ࠡࡦ࡬ࡷࡵࡧࡴࡤࡪࠣࡱࡪࡺࡨࡰࡦ࠽ࠤࠧ፞"), e)
            dispatch(Connection, *args)
        return wrapped
    def bstack1l11ll1lll1_opy_(
        self,
        f: bstack1ll1l1l111l_opy_,
        bstack1l11lll11ll_opy_: object,
        exec: Tuple[bstack1llll111ll1_opy_, str],
        bstack1lllll11l1l_opy_: Tuple[bstack1llll11l1l1_opy_, bstack1lllll111l1_opy_],
        result: Any,
        *args,
        **kwargs,
    ):
        instance, method_name = exec
        if method_name != bstack1ll_opy_ (u"ࠥࡧࡴࡴ࡮ࡦࡥࡷࠦ፟"):
            return
        if not bstack1l1ll111lll_opy_():
            self.logger.debug(bstack1ll_opy_ (u"ࠦࡗ࡫ࡴࡶࡴࡱ࡭ࡳ࡭ࠠࡪࡰࠣࡧࡴࡴ࡮ࡦࡥࡷࠤࡲ࡫ࡴࡩࡱࡧ࠰ࠥࡴ࡯ࡵࠢࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫ࠡࡵࡨࡷࡸ࡯࡯࡯ࠤ፠"))
            return
        def wrapped(bstack1l11lll11ll_opy_, connect, *args, **kwargs):
            response = self.bstack1l11lll11l1_opy_(f.platform_index, instance.ref(), json.dumps({bstack1ll_opy_ (u"ࠬ࡯ࡳࡑ࡮ࡤࡽࡼࡸࡩࡨࡪࡷࠫ፡"): True}).encode(bstack1ll_opy_ (u"ࠨࡵࡵࡨ࠰࠼ࠧ።")))
            if response is not None and response.capabilities:
                bstack1l11llll1ll_opy_ = json.loads(response.capabilities.decode(bstack1ll_opy_ (u"ࠢࡶࡶࡩ࠱࠽ࠨ፣")))
                if not bstack1l11llll1ll_opy_:
                    return
                bstack1l11llll111_opy_ = PLAYWRIGHT_HUB_URL + urllib.parse.quote(json.dumps(bstack1l11llll1ll_opy_))
                if bstack1l11llll1ll_opy_.get(bstack1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࠮ࡢࡥࡦࡩࡸࡹࡩࡣ࡫࡯࡭ࡹࡿࠧ፤")):
                    browser = bstack1l11lll11ll_opy_.bstack1l11lll111l_opy_(bstack1l11llll111_opy_)
                    return browser
                else:
                    args = list(args)
                    args[0] = bstack1l11llll111_opy_
                    return connect(bstack1l11lll11ll_opy_, *args, **kwargs)
        return wrapped
    def bstack1l11llll11l_opy_(
        self,
        f: bstack1ll1l1l111l_opy_,
        bstack1l1ll1l1lll_opy_: object,
        exec: Tuple[bstack1llll111ll1_opy_, str],
        bstack1lllll11l1l_opy_: Tuple[bstack1llll11l1l1_opy_, bstack1lllll111l1_opy_],
        result: Any,
        *args,
        **kwargs,
    ):
        instance, method_name = exec
        if method_name != bstack1ll_opy_ (u"ࠤࡱࡩࡼࡥࡰࡢࡩࡨࠦ፥"):
            return
        if not bstack1l1ll111lll_opy_():
            self.logger.debug(bstack1ll_opy_ (u"ࠥࡖࡪࡺࡵࡳࡰ࡬ࡲ࡬ࠦࡩ࡯ࠢࡱࡩࡼࡥࡰࡢࡩࡨࠤࡲ࡫ࡴࡩࡱࡧ࠰ࠥࡴ࡯ࡵࠢࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫ࠡࡵࡨࡷࡸ࡯࡯࡯ࠤ፦"))
            return
        def wrapped(bstack1l1ll1l1lll_opy_, bstack1l11ll1ll1l_opy_, *args, **kwargs):
            contexts = bstack1l1ll1l1lll_opy_.browser.contexts
            if contexts:
                for context in contexts:
                    if context.pages:
                        for page in context.pages:
                            if bstack1ll_opy_ (u"ࠦࡦࡨ࡯ࡶࡶ࠽ࡦࡱࡧ࡮࡬ࠤ፧") in page.url:
                                return page
                            else:
                                return bstack1l11ll1ll1l_opy_(bstack1l1ll1l1lll_opy_)
                    else:
                        return bstack1l11ll1ll1l_opy_(bstack1l1ll1l1lll_opy_)
        return wrapped
    def bstack1l11lll11l1_opy_(self, platform_index: int, ref, user_input_params: bytes):
        req = structs.DriverInitRequest()
        req.bin_session_id = self.bin_session_id
        req.platform_index = platform_index
        req.user_input_params = user_input_params
        req.ref = ref
        self.logger.debug(bstack1ll_opy_ (u"ࠧࡸࡥࡨ࡫ࡶࡸࡪࡸ࡟ࡸࡧࡥࡨࡷ࡯ࡶࡦࡴࡢ࡭ࡳ࡯ࡴ࠻ࠢࠥ፨") + str(req) + bstack1ll_opy_ (u"ࠨࠢ፩"))
        try:
            r = self.bstack1ll1l11lll1_opy_.DriverInit(req)
            if not r.success:
                self.logger.debug(bstack1ll_opy_ (u"ࠢࡳࡧࡦࡩ࡮ࡼࡥࡥࠢࡩࡶࡴࡳࠠࡴࡧࡵࡺࡪࡸ࠺ࠡࡵࡸࡧࡨ࡫ࡳࡴ࠿ࠥ፪") + str(r.success) + bstack1ll_opy_ (u"ࠣࠤ፫"))
            return r
        except grpc.RpcError as e:
            self.logger.error(bstack1ll_opy_ (u"ࠤࡵࡴࡨ࠳ࡥࡳࡴࡲࡶ࠿ࠦࠢ፬") + str(e) + bstack1ll_opy_ (u"ࠥࠦ፭"))
            traceback.print_exc()
            raise e
    def bstack1l11ll1ll11_opy_(
        self,
        f: bstack1ll1l1l111l_opy_,
        Connection: object,
        exec: Tuple[bstack1llll111ll1_opy_, str],
        bstack1lllll11l1l_opy_: Tuple[bstack1llll11l1l1_opy_, bstack1lllll111l1_opy_],
        result: Any,
        *args,
        **kwargs,
    ):
        instance, method_name = exec
        if method_name != bstack1ll_opy_ (u"ࠦࡤࡹࡥ࡯ࡦࡢࡱࡪࡹࡳࡢࡩࡨࡣࡹࡵ࡟ࡴࡧࡵࡺࡪࡸࠢ፮"):
            return
        if not bstack1l1ll111lll_opy_():
            return
        def wrapped(Connection, bstack1l11ll1llll_opy_, *args, **kwargs):
            return bstack1l11ll1llll_opy_(Connection, *args, **kwargs)
        return wrapped
    def on_close(
        self,
        f: bstack1ll1l1l111l_opy_,
        bstack1l11lll11ll_opy_: object,
        exec: Tuple[bstack1llll111ll1_opy_, str],
        bstack1lllll11l1l_opy_: Tuple[bstack1llll11l1l1_opy_, bstack1lllll111l1_opy_],
        result: Any,
        *args,
        **kwargs,
    ):
        instance, method_name = exec
        if method_name != bstack1ll_opy_ (u"ࠧࡩ࡬ࡰࡵࡨࠦ፯"):
            return
        if not bstack1l1ll111lll_opy_():
            self.logger.debug(bstack1ll_opy_ (u"ࠨࡒࡦࡶࡸࡶࡳ࡯࡮ࡨࠢ࡬ࡲࠥࡩ࡬ࡰࡵࡨࠤࡲ࡫ࡴࡩࡱࡧ࠰ࠥࡴ࡯ࡵࠢࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫ࠡࡵࡨࡷࡸ࡯࡯࡯ࠤ፰"))
            return
        def wrapped(Connection, close, *args, **kwargs):
            return close(Connection)
        return wrapped