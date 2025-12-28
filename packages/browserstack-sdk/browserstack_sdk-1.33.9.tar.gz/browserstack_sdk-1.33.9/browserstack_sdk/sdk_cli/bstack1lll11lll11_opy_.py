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
from bstack_utils.bstack11ll1llll1_opy_ import bstack1lll1ll1l1l_opy_
from bstack_utils.constants import EVENTS
class bstack1ll1llll1l1_opy_(bstack1llll1ll1ll_opy_):
    bstack1l111l1llll_opy_ = bstack1ll_opy_ (u"ࠥࡆࡗࡕࡗࡔࡇࡕࡗ࡙ࡇࡃࡌࡡࡓࡐࡆ࡚ࡆࡐࡔࡐࡣࡎࡔࡄࡆ࡚ࠥᗜ")
    NAME = bstack1ll_opy_ (u"ࠦࡸ࡫࡬ࡦࡰ࡬ࡹࡲࠨᗝ")
    bstack1l11lll1ll1_opy_ = bstack1ll_opy_ (u"ࠧ࡮ࡵࡣࡡࡸࡶࡱࠨᗞ")
    bstack1l11lll1lll_opy_ = bstack1ll_opy_ (u"ࠨࡦࡳࡣࡰࡩࡼࡵࡲ࡬ࡡࡶࡩࡸࡹࡩࡰࡰࡢ࡭ࡩࠨᗟ")
    bstack11lll111ll1_opy_ = bstack1ll_opy_ (u"ࠢࡪࡰࡳࡹࡹࡥࡣࡢࡲࡤࡦ࡮ࡲࡩࡵ࡫ࡨࡷࠧᗠ")
    bstack1l11lllll1l_opy_ = bstack1ll_opy_ (u"ࠣࡥࡤࡴࡦࡨࡩ࡭࡫ࡷ࡭ࡪࡹࠢᗡ")
    bstack1l111lll111_opy_ = bstack1ll_opy_ (u"ࠤ࡬ࡷࡤࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮ࡣ࡭ࡻࡢࠣᗢ")
    bstack11lll111l11_opy_ = bstack1ll_opy_ (u"ࠥࡷࡹࡧࡲࡵࡧࡧࡣࡦࡺࠢᗣ")
    bstack11lll11l1l1_opy_ = bstack1ll_opy_ (u"ࠦࡪࡴࡤࡦࡦࡢࡥࡹࠨᗤ")
    bstack1l1lll1l1ll_opy_ = bstack1ll_opy_ (u"ࠧࡶ࡬ࡢࡶࡩࡳࡷࡳ࡟ࡪࡰࡧࡩࡽࠨᗥ")
    bstack1l11l11lll1_opy_ = bstack1ll_opy_ (u"ࠨ࡮ࡦࡹࡶࡩࡸࡹࡩࡰࡰࠥᗦ")
    bstack11lll11l1ll_opy_ = bstack1ll_opy_ (u"ࠢࡨࡧࡷࠦᗧ")
    bstack1l1ll11l1ll_opy_ = bstack1ll_opy_ (u"ࠣࡵࡦࡶࡪ࡫࡮ࡴࡪࡲࡸࠧᗨ")
    bstack1l111l1ll11_opy_ = bstack1ll_opy_ (u"ࠤࡺ࠷ࡨ࡫ࡸࡦࡥࡸࡸࡪࡹࡣࡳ࡫ࡳࡸࠧᗩ")
    bstack1l111l1l11l_opy_ = bstack1ll_opy_ (u"ࠥࡻ࠸ࡩࡥࡹࡧࡦࡹࡹ࡫ࡳࡤࡴ࡬ࡴࡹࡧࡳࡺࡰࡦࠦᗪ")
    bstack11lll11l111_opy_ = bstack1ll_opy_ (u"ࠦࡶࡻࡩࡵࠤᗫ")
    bstack11lll11ll1l_opy_: Dict[str, List[Callable]] = dict()
    bstack1l11l1l11l1_opy_: str
    platform_index: int
    options: Any
    desired_capabilities: Any
    bstack1ll1l1ll1ll_opy_: Any
    bstack1l111l1lll1_opy_: Dict
    def __init__(
        self,
        bstack1l11l1l11l1_opy_: str,
        platform_index: int,
        framework_name: str,
        framework_version: str,
        classes: List[Type],
        bstack1ll1l1ll1ll_opy_: Dict[str, Any],
        methods=[bstack1ll_opy_ (u"ࠧࡥ࡟ࡪࡰ࡬ࡸࡤࡥࠢᗬ"), bstack1ll_opy_ (u"ࠨࡳࡵࡣࡵࡸࡤࡹࡥࡴࡵ࡬ࡳࡳࠨᗭ"), bstack1ll_opy_ (u"ࠢࡦࡺࡨࡧࡺࡺࡥࠣᗮ"), bstack1ll_opy_ (u"ࠣࡳࡸ࡭ࡹࠨᗯ")],
    ):
        super().__init__(
            framework_name,
            framework_version,
            classes,
        )
        self.bstack1l11l1l11l1_opy_ = bstack1l11l1l11l1_opy_
        self.platform_index = platform_index
        self.bstack1llll111l1l_opy_(methods)
        self.bstack1ll1l1ll1ll_opy_ = bstack1ll1l1ll1ll_opy_
    @staticmethod
    def session_id(target: object, strict=True):
        return bstack1llll1ll1ll_opy_.get_data(bstack1ll1llll1l1_opy_.bstack1l11lll1lll_opy_, target, strict)
    @staticmethod
    def hub_url(target: object, strict=True):
        return bstack1llll1ll1ll_opy_.get_data(bstack1ll1llll1l1_opy_.bstack1l11lll1ll1_opy_, target, strict)
    @staticmethod
    def bstack11lll111l1l_opy_(target: object, strict=True):
        return bstack1llll1ll1ll_opy_.get_data(bstack1ll1llll1l1_opy_.bstack11lll111ll1_opy_, target, strict)
    @staticmethod
    def capabilities(target: object, strict=True):
        return bstack1llll1ll1ll_opy_.get_data(bstack1ll1llll1l1_opy_.bstack1l11lllll1l_opy_, target, strict)
    @staticmethod
    def bstack1l1ll1l11l1_opy_(instance: bstack1llll111ll1_opy_) -> bool:
        return bstack1llll1ll1ll_opy_.bstack1llll1l111l_opy_(instance, bstack1ll1llll1l1_opy_.bstack1l111lll111_opy_, False)
    @staticmethod
    def bstack1l1lllll1l1_opy_(instance: bstack1llll111ll1_opy_, default_value=None):
        return bstack1llll1ll1ll_opy_.bstack1llll1l111l_opy_(instance, bstack1ll1llll1l1_opy_.bstack1l11lll1ll1_opy_, default_value)
    @staticmethod
    def bstack1ll111ll1l1_opy_(instance: bstack1llll111ll1_opy_, default_value=None):
        return bstack1llll1ll1ll_opy_.bstack1llll1l111l_opy_(instance, bstack1ll1llll1l1_opy_.bstack1l11lllll1l_opy_, default_value)
    @staticmethod
    def bstack1l1lll11lll_opy_(hub_url: str, bstack11lll11l11l_opy_=bstack1ll_opy_ (u"ࠤ࠱ࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬࠰ࡦࡳࡲࠨᗰ")):
        try:
            bstack11lll111lll_opy_ = str(urlparse(hub_url).netloc) if hub_url else None
            return bstack11lll111lll_opy_.endswith(bstack11lll11l11l_opy_)
        except:
            pass
        return False
    @staticmethod
    def bstack1ll11l1l111_opy_(method_name: str):
        return method_name == bstack1ll_opy_ (u"ࠥࡩࡽ࡫ࡣࡶࡶࡨࠦᗱ")
    @staticmethod
    def bstack1l1llll11l1_opy_(method_name: str, *args):
        return (
            bstack1ll1llll1l1_opy_.bstack1ll11l1l111_opy_(method_name)
            and bstack1ll1llll1l1_opy_.bstack1l11l111l11_opy_(*args) == bstack1ll1llll1l1_opy_.bstack1l11l11lll1_opy_
        )
    @staticmethod
    def bstack1l1lll1ll1l_opy_(method_name: str, *args):
        if not bstack1ll1llll1l1_opy_.bstack1ll11l1l111_opy_(method_name):
            return False
        if not bstack1ll1llll1l1_opy_.bstack1l111l1ll11_opy_ in bstack1ll1llll1l1_opy_.bstack1l11l111l11_opy_(*args):
            return False
        bstack1l1lll11l1l_opy_ = bstack1ll1llll1l1_opy_.bstack1l1lll111l1_opy_(*args)
        return bstack1l1lll11l1l_opy_ and bstack1ll_opy_ (u"ࠦࡸࡩࡲࡪࡲࡷࠦᗲ") in bstack1l1lll11l1l_opy_ and bstack1ll_opy_ (u"ࠧࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮ࡣࡪࡾࡥࡤࡷࡷࡳࡷࠨᗳ") in bstack1l1lll11l1l_opy_[bstack1ll_opy_ (u"ࠨࡳࡤࡴ࡬ࡴࡹࠨᗴ")]
    @staticmethod
    def bstack1l1llll111l_opy_(method_name: str, *args):
        if not bstack1ll1llll1l1_opy_.bstack1ll11l1l111_opy_(method_name):
            return False
        if not bstack1ll1llll1l1_opy_.bstack1l111l1ll11_opy_ in bstack1ll1llll1l1_opy_.bstack1l11l111l11_opy_(*args):
            return False
        bstack1l1lll11l1l_opy_ = bstack1ll1llll1l1_opy_.bstack1l1lll111l1_opy_(*args)
        return (
            bstack1l1lll11l1l_opy_
            and bstack1ll_opy_ (u"ࠢࡴࡥࡵ࡭ࡵࡺࠢᗵ") in bstack1l1lll11l1l_opy_
            and bstack1ll_opy_ (u"ࠣࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࡟ࡢࡥࡦࡩࡸࡹࡩࡣ࡫࡯࡭ࡹࡿ࡟ࡢࡷࡷࡳࡲࡧࡴࡪࡱࡱࡣࡸࡩࡲࡪࡲࡷࠦᗶ") in bstack1l1lll11l1l_opy_[bstack1ll_opy_ (u"ࠤࡶࡧࡷ࡯ࡰࡵࠤᗷ")]
        )
    @staticmethod
    def bstack1l11l111l11_opy_(*args):
        return str(bstack1ll1llll1l1_opy_.bstack1ll11l1llll_opy_(*args)).lower()
    @staticmethod
    def bstack1ll11l1llll_opy_(*args):
        return args[0] if args and type(args) in [list, tuple] and isinstance(args[0], str) else None
    @staticmethod
    def bstack1l1lll111l1_opy_(*args):
        return args[1] if len(args) > 1 and isinstance(args[1], dict) else None
    @staticmethod
    def bstack111ll1111_opy_(driver):
        command_executor = getattr(driver, bstack1ll_opy_ (u"ࠥࡧࡴࡳ࡭ࡢࡰࡧࡣࡪࡾࡥࡤࡷࡷࡳࡷࠨᗸ"), None)
        if not command_executor:
            return None
        hub_url = str(command_executor) if isinstance(command_executor, (str, bytes)) else None
        hub_url = str(command_executor._url) if not hub_url and getattr(command_executor, bstack1ll_opy_ (u"ࠦࡤࡻࡲ࡭ࠤᗹ"), None) else None
        if not hub_url:
            client_config = getattr(command_executor, bstack1ll_opy_ (u"ࠧࡥࡣ࡭࡫ࡨࡲࡹࡥࡣࡰࡰࡩ࡭࡬ࠨᗺ"), None)
            if not client_config:
                return None
            hub_url = getattr(client_config, bstack1ll_opy_ (u"ࠨࡲࡦ࡯ࡲࡸࡪࡥࡳࡦࡴࡹࡩࡷࡥࡡࡥࡦࡵࠦᗻ"), None)
        return hub_url
    def bstack1l11l1l1l11_opy_(self, instance, driver, hub_url: str):
        result = False
        if not hub_url:
            return result
        command_executor = getattr(driver, bstack1ll_opy_ (u"ࠢࡤࡱࡰࡱࡦࡴࡤࡠࡧࡻࡩࡨࡻࡴࡰࡴࠥᗼ"), None)
        if command_executor:
            if isinstance(command_executor, (str, bytes)):
                setattr(driver, bstack1ll_opy_ (u"ࠣࡥࡲࡱࡲࡧ࡮ࡥࡡࡨࡼࡪࡩࡵࡵࡱࡵࠦᗽ"), hub_url)
                result = True
            elif hasattr(command_executor, bstack1ll_opy_ (u"ࠤࡢࡹࡷࡲࠢᗾ")):
                setattr(command_executor, bstack1ll_opy_ (u"ࠥࡣࡺࡸ࡬ࠣᗿ"), hub_url)
                result = True
        if result:
            self.bstack1l11l1l11l1_opy_ = hub_url
            bstack1ll1llll1l1_opy_.bstack1llll1lll11_opy_(instance, bstack1ll1llll1l1_opy_.bstack1l11lll1ll1_opy_, hub_url)
            bstack1ll1llll1l1_opy_.bstack1llll1lll11_opy_(
                instance, bstack1ll1llll1l1_opy_.bstack1l111lll111_opy_, bstack1ll1llll1l1_opy_.bstack1l1lll11lll_opy_(hub_url)
            )
        return result
    @staticmethod
    def bstack1l111l11ll1_opy_(bstack1lllll11l1l_opy_: Tuple[bstack1llll11l1l1_opy_, bstack1lllll111l1_opy_]):
        return bstack1ll_opy_ (u"ࠦ࠿ࠨᘀ").join((bstack1llll11l1l1_opy_(bstack1lllll11l1l_opy_[0]).name, bstack1lllll111l1_opy_(bstack1lllll11l1l_opy_[1]).name))
    @staticmethod
    def bstack1ll1111l11l_opy_(bstack1lllll11l1l_opy_: Tuple[bstack1llll11l1l1_opy_, bstack1lllll111l1_opy_], callback: Callable):
        bstack1l111l11lll_opy_ = bstack1ll1llll1l1_opy_.bstack1l111l11ll1_opy_(bstack1lllll11l1l_opy_)
        if not bstack1l111l11lll_opy_ in bstack1ll1llll1l1_opy_.bstack11lll11ll1l_opy_:
            bstack1ll1llll1l1_opy_.bstack11lll11ll1l_opy_[bstack1l111l11lll_opy_] = []
        bstack1ll1llll1l1_opy_.bstack11lll11ll1l_opy_[bstack1l111l11lll_opy_].append(callback)
    def bstack1lllll1111l_opy_(self, instance: bstack1llll111ll1_opy_, method_name: str, bstack1llll1lll1l_opy_: timedelta, *args, **kwargs):
        if not instance or method_name in (bstack1ll_opy_ (u"ࠧࡹࡴࡢࡴࡷࡣࡸ࡫ࡳࡴ࡫ࡲࡲࠧᘁ")):
            return
        cmd = args[0] if method_name == bstack1ll_opy_ (u"ࠨࡥࡹࡧࡦࡹࡹ࡫ࠢᘂ") and args and type(args) in [list, tuple] and isinstance(args[0], str) else None
        bstack11lll11ll11_opy_ = bstack1ll_opy_ (u"ࠢ࠻ࠤᘃ").join(map(str, filter(None, [method_name, cmd])))
        instance.bstack11ll11ll1_opy_(bstack1ll_opy_ (u"ࠣࡦࡵ࡭ࡻ࡫ࡲ࠻ࠤᘄ") + bstack11lll11ll11_opy_, bstack1llll1lll1l_opy_)
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
        bstack1l111l11lll_opy_ = bstack1ll1llll1l1_opy_.bstack1l111l11ll1_opy_(bstack1lllll11l1l_opy_)
        self.logger.debug(bstack1ll_opy_ (u"ࠤࡲࡲࡤ࡮࡯ࡰ࡭࠽ࠤࡲ࡫ࡴࡩࡱࡧࡣࡳࡧ࡭ࡦ࠿ࡾࡱࡪࡺࡨࡰࡦࡢࡲࡦࡳࡥࡾࠢ࡫ࡳࡴࡱ࡟ࡪࡰࡩࡳࡂࢁࡨࡰࡱ࡮ࡣ࡮ࡴࡦࡰࡿࠣࡥࡷ࡭ࡳ࠾ࡽࡤࡶ࡬ࡹࡽࠡ࡭ࡺࡥࡷ࡭ࡳ࠾ࠤᘅ") + str(kwargs) + bstack1ll_opy_ (u"ࠥࠦᘆ"))
        if bstack1lllll1l111_opy_ == bstack1llll11l1l1_opy_.QUIT:
            if bstack1l111l1ll1l_opy_ == bstack1lllll111l1_opy_.PRE:
                bstack1ll11l11l1l_opy_ = bstack1lll1ll1l1l_opy_.bstack1ll1111ll11_opy_(EVENTS.bstack1l1ll1l11l_opy_.value)
                bstack1llll1ll1ll_opy_.bstack1llll1lll11_opy_(instance, EVENTS.bstack1l1ll1l11l_opy_.value, bstack1ll11l11l1l_opy_)
                self.logger.debug(bstack1ll_opy_ (u"ࠦ࡮ࡴࡳࡵࡣࡱࡧࡪࡃࡻࡾࠢࡰࡩࡹ࡮࡯ࡥࡡࡱࡥࡲ࡫࠽ࡼࡿࠣࡪࡷࡧ࡭ࡦࡹࡲࡶࡰࡥࡳࡵࡣࡷࡩࡂࢁࡽࠡࡪࡲࡳࡰࡥࡳࡵࡣࡷࡩࡂࢁࡽࠣᘇ").format(instance, method_name, bstack1lllll1l111_opy_, bstack1l111l1ll1l_opy_))
        if bstack1lllll1l111_opy_ == bstack1llll11l1l1_opy_.bstack1llll1l1l1l_opy_:
            if bstack1l111l1ll1l_opy_ == bstack1lllll111l1_opy_.POST and not bstack1ll1llll1l1_opy_.bstack1l11lll1lll_opy_ in instance.data:
                session_id = getattr(target, bstack1ll_opy_ (u"ࠧࡹࡥࡴࡵ࡬ࡳࡳࡥࡩࡥࠤᘈ"), None)
                if session_id:
                    instance.data[bstack1ll1llll1l1_opy_.bstack1l11lll1lll_opy_] = session_id
        elif (
            bstack1lllll1l111_opy_ == bstack1llll11l1l1_opy_.bstack1llll1l1111_opy_
            and bstack1ll1llll1l1_opy_.bstack1l11l111l11_opy_(*args) == bstack1ll1llll1l1_opy_.bstack1l11l11lll1_opy_
        ):
            if bstack1l111l1ll1l_opy_ == bstack1lllll111l1_opy_.PRE:
                hub_url = bstack1ll1llll1l1_opy_.bstack111ll1111_opy_(target)
                if hub_url:
                    instance.data.update(
                        {
                            bstack1ll1llll1l1_opy_.bstack1l11lll1ll1_opy_: hub_url,
                            bstack1ll1llll1l1_opy_.bstack1l111lll111_opy_: bstack1ll1llll1l1_opy_.bstack1l1lll11lll_opy_(hub_url),
                            bstack1ll1llll1l1_opy_.bstack1l1lll1l1ll_opy_: int(
                                os.environ.get(bstack1ll_opy_ (u"ࠨࡂࡓࡑ࡚ࡗࡊࡘࡓࡕࡃࡆࡏࡤࡖࡌࡂࡖࡉࡓࡗࡓ࡟ࡊࡐࡇࡉ࡝ࠨᘉ"), str(self.platform_index))
                            ),
                        }
                    )
                bstack1l1lll11l1l_opy_ = bstack1ll1llll1l1_opy_.bstack1l1lll111l1_opy_(*args)
                bstack11lll111l1l_opy_ = bstack1l1lll11l1l_opy_.get(bstack1ll_opy_ (u"ࠢࡤࡣࡳࡥࡧ࡯࡬ࡪࡶ࡬ࡩࡸࠨᘊ"), None) if bstack1l1lll11l1l_opy_ else None
                if isinstance(bstack11lll111l1l_opy_, dict):
                    instance.data[bstack1ll1llll1l1_opy_.bstack11lll111ll1_opy_] = copy.deepcopy(bstack11lll111l1l_opy_)
                    instance.data[bstack1ll1llll1l1_opy_.bstack1l11lllll1l_opy_] = bstack11lll111l1l_opy_
            elif bstack1l111l1ll1l_opy_ == bstack1lllll111l1_opy_.POST:
                if isinstance(result, dict):
                    framework_session_id = result.get(bstack1ll_opy_ (u"ࠣࡸࡤࡰࡺ࡫ࠢᘋ"), dict()).get(bstack1ll_opy_ (u"ࠤࡶࡩࡸࡹࡩࡰࡰࡌࡨࠧᘌ"), None)
                    if framework_session_id:
                        instance.data.update(
                            {
                                bstack1ll1llll1l1_opy_.bstack1l11lll1lll_opy_: framework_session_id,
                                bstack1ll1llll1l1_opy_.bstack11lll111l11_opy_: datetime.now(tz=timezone.utc),
                            }
                        )
        elif (
            bstack1lllll1l111_opy_ == bstack1llll11l1l1_opy_.bstack1llll1l1111_opy_
            and bstack1ll1llll1l1_opy_.bstack1l11l111l11_opy_(*args) == bstack1ll1llll1l1_opy_.bstack11lll11l111_opy_
            and bstack1l111l1ll1l_opy_ == bstack1lllll111l1_opy_.POST
        ):
            instance.data[bstack1ll1llll1l1_opy_.bstack11lll11l1l1_opy_] = datetime.now(tz=timezone.utc)
        if bstack1l111l11lll_opy_ in bstack1ll1llll1l1_opy_.bstack11lll11ll1l_opy_:
            bstack1l111l1l111_opy_ = None
            for callback in bstack1ll1llll1l1_opy_.bstack11lll11ll1l_opy_[bstack1l111l11lll_opy_]:
                try:
                    bstack1l111l1l1ll_opy_ = callback(self, target, exec, bstack1lllll11l1l_opy_, result, *args, **kwargs)
                    if bstack1l111l1l111_opy_ == None:
                        bstack1l111l1l111_opy_ = bstack1l111l1l1ll_opy_
                except Exception as e:
                    self.logger.error(bstack1ll_opy_ (u"ࠥࡩࡷࡸ࡯ࡳࠢ࡬ࡲࡻࡵ࡫ࡪࡰࡪࠤࡨࡧ࡬࡭ࡤࡤࡧࡰࡀࠠࠣᘍ") + str(e) + bstack1ll_opy_ (u"ࠦࠧᘎ"))
                    traceback.print_exc()
            if bstack1lllll1l111_opy_ == bstack1llll11l1l1_opy_.QUIT:
                if bstack1l111l1ll1l_opy_ == bstack1lllll111l1_opy_.POST:
                    bstack1ll11l11l1l_opy_ = bstack1llll1ll1ll_opy_.bstack1llll1l111l_opy_(instance, EVENTS.bstack1l1ll1l11l_opy_.value)
                    if bstack1ll11l11l1l_opy_!=None:
                        bstack1lll1ll1l1l_opy_.end(EVENTS.bstack1l1ll1l11l_opy_.value, bstack1ll11l11l1l_opy_+bstack1ll_opy_ (u"ࠧࡀࡳࡵࡣࡵࡸࠧᘏ"), bstack1ll11l11l1l_opy_+bstack1ll_opy_ (u"ࠨ࠺ࡦࡰࡧࠦᘐ"), True, None)
            if bstack1l111l1ll1l_opy_ == bstack1lllll111l1_opy_.PRE and callable(bstack1l111l1l111_opy_):
                return bstack1l111l1l111_opy_
            elif bstack1l111l1ll1l_opy_ == bstack1lllll111l1_opy_.POST and bstack1l111l1l111_opy_:
                return bstack1l111l1l111_opy_
    def bstack1llll1111l1_opy_(
        self, method_name, previous_state: bstack1llll11l1l1_opy_, *args, **kwargs
    ) -> bstack1llll11l1l1_opy_:
        if method_name == bstack1ll_opy_ (u"ࠢࡠࡡ࡬ࡲ࡮ࡺ࡟ࡠࠤᘑ") or method_name == bstack1ll_opy_ (u"ࠣࡵࡷࡥࡷࡺ࡟ࡴࡧࡶࡷ࡮ࡵ࡮ࠣᘒ"):
            return bstack1llll11l1l1_opy_.bstack1llll1l1l1l_opy_
        if method_name == bstack1ll_opy_ (u"ࠤࡴࡹ࡮ࡺࠢᘓ"):
            return bstack1llll11l1l1_opy_.QUIT
        if method_name == bstack1ll_opy_ (u"ࠥࡩࡽ࡫ࡣࡶࡶࡨࠦᘔ"):
            if previous_state != bstack1llll11l1l1_opy_.NONE:
                command_name = bstack1ll1llll1l1_opy_.bstack1l11l111l11_opy_(*args)
                if command_name == bstack1ll1llll1l1_opy_.bstack1l11l11lll1_opy_:
                    return bstack1llll11l1l1_opy_.bstack1llll1l1l1l_opy_
            return bstack1llll11l1l1_opy_.bstack1llll1l1111_opy_
        return bstack1llll11l1l1_opy_.NONE