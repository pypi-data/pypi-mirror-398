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
    bstack1llll1ll1ll_opy_,
    bstack1llll111ll1_opy_,
)
from browserstack_sdk.sdk_cli.bstack1lll11lll11_opy_ import bstack1ll1llll1l1_opy_
from browserstack_sdk.sdk_cli.bstack1ll1llll111_opy_ import bstack1ll1l1l111l_opy_
from browserstack_sdk.sdk_cli.bstack1llll11l111_opy_ import bstack1llll11l1ll_opy_
from typing import Tuple, Dict, Any, List, Callable
from browserstack_sdk.sdk_cli.bstack1lll11ll1l1_opy_ import bstack1ll1lll1l1l_opy_
import weakref
class bstack1l1ll1l1ll1_opy_(bstack1ll1lll1l1l_opy_):
    bstack1l1ll1llll1_opy_: str
    frameworks: List[str]
    drivers: Dict[str, Tuple[Callable, bstack1llll111ll1_opy_]]
    pages: Dict[str, Tuple[Callable, bstack1llll111ll1_opy_]]
    def __init__(self, bstack1l1ll1llll1_opy_: str, frameworks: List[str]):
        super().__init__()
        self.drivers = dict()
        self.pages = dict()
        self.bstack1l1ll1l11ll_opy_ = dict()
        self.bstack1l1ll1llll1_opy_ = bstack1l1ll1llll1_opy_
        self.frameworks = frameworks
        bstack1ll1l1l111l_opy_.bstack1ll1111l11l_opy_((bstack1llll11l1l1_opy_.bstack1llll1l1l1l_opy_, bstack1lllll111l1_opy_.POST), self.__1l1ll1ll1l1_opy_)
        if any(bstack1ll1llll1l1_opy_.NAME in f.lower().strip() for f in frameworks):
            bstack1ll1llll1l1_opy_.bstack1ll1111l11l_opy_(
                (bstack1llll11l1l1_opy_.bstack1llll1l1111_opy_, bstack1lllll111l1_opy_.PRE), self.__1l1ll1ll1ll_opy_
            )
            bstack1ll1llll1l1_opy_.bstack1ll1111l11l_opy_(
                (bstack1llll11l1l1_opy_.QUIT, bstack1lllll111l1_opy_.POST), self.__1l1ll1ll11l_opy_
            )
    def __1l1ll1ll1l1_opy_(
        self,
        f: bstack1ll1l1l111l_opy_,
        bstack1l1ll1l1lll_opy_: object,
        exec: Tuple[bstack1llll111ll1_opy_, str],
        bstack1lllll11l1l_opy_: Tuple[bstack1llll11l1l1_opy_, bstack1lllll111l1_opy_],
        result: Any,
        *args,
        **kwargs,
    ):
        try:
            instance, method_name = exec
            if method_name != bstack1ll_opy_ (u"ࠧࡴࡥࡸࡡࡳࡥ࡬࡫ࠢካ"):
                return
            contexts = bstack1l1ll1l1lll_opy_.browser.contexts
            if contexts:
                for context in contexts:
                    if context.pages:
                        for page in context.pages:
                            if bstack1ll_opy_ (u"ࠨࡡࡣࡱࡸࡸ࠿ࡨ࡬ࡢࡰ࡮ࠦኬ") in page.url:
                                self.logger.debug(bstack1ll_opy_ (u"ࠢࡔࡶࡲࡶ࡮ࡴࡧࠡࡶ࡫ࡩࠥࡴࡥࡸࠢࡳࡥ࡬࡫ࠠࡪࡰࡶࡸࡦࡴࡣࡦࠤክ"))
                                self.pages[instance.ref()] = weakref.ref(page), instance
                                bstack1llll1ll1ll_opy_.bstack1llll1lll11_opy_(instance, self.bstack1l1ll1llll1_opy_, True)
                                self.logger.debug(bstack1ll_opy_ (u"ࠣࡡࡢࡳࡳࡥࡰࡢࡩࡨࡣ࡮ࡴࡩࡵ࠼ࠣ࡭ࡳࡹࡴࡢࡰࡦࡩࡂࠨኮ") + str(instance.ref()) + bstack1ll_opy_ (u"ࠤࠥኯ"))
        except Exception as e:
            self.logger.debug(bstack1ll_opy_ (u"ࠥࡉࡽࡩࡥࡱࡶ࡬ࡳࡳࠦࡩ࡯ࠢࡶࡸࡴࡸࡩ࡯ࡩࠣࡲࡪࡽࠠࡱࡣࡪࡩࠥࡀࠢኰ"),e)
    def __1l1ll1ll1ll_opy_(
        self,
        f: bstack1ll1llll1l1_opy_,
        driver: object,
        exec: Tuple[bstack1llll111ll1_opy_, str],
        bstack1lllll11l1l_opy_: Tuple[bstack1llll11l1l1_opy_, bstack1lllll111l1_opy_],
        result: Any,
        *args,
        **kwargs,
    ):
        instance, _ = exec
        if instance.ref() in self.drivers or bstack1llll1ll1ll_opy_.bstack1llll1l111l_opy_(instance, self.bstack1l1ll1llll1_opy_, False):
            return
        if not f.bstack1l1lll11lll_opy_(f.hub_url(driver)):
            self.bstack1l1ll1l11ll_opy_[instance.ref()] = weakref.ref(driver), instance
            bstack1llll1ll1ll_opy_.bstack1llll1lll11_opy_(instance, self.bstack1l1ll1llll1_opy_, True)
            self.logger.debug(bstack1ll_opy_ (u"ࠦࡤࡥ࡯࡯ࡡࡶࡩࡱ࡫࡮ࡪࡷࡰࡣ࡮ࡴࡩࡵ࠼ࠣࡲࡴࡴ࡟ࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰࡥࡤࡳ࡫ࡹࡩࡷࠦࡩ࡯ࡵࡷࡥࡳࡩࡥ࠾ࠤ኱") + str(instance.ref()) + bstack1ll_opy_ (u"ࠧࠨኲ"))
            return
        self.drivers[instance.ref()] = weakref.ref(driver), instance
        bstack1llll1ll1ll_opy_.bstack1llll1lll11_opy_(instance, self.bstack1l1ll1llll1_opy_, True)
        self.logger.debug(bstack1ll_opy_ (u"ࠨ࡟ࡠࡱࡱࡣࡸ࡫࡬ࡦࡰ࡬ࡹࡲࡥࡩ࡯࡫ࡷ࠾ࠥ࡯࡮ࡴࡶࡤࡲࡨ࡫࠽ࠣኳ") + str(instance.ref()) + bstack1ll_opy_ (u"ࠢࠣኴ"))
    def __1l1ll1ll11l_opy_(
        self,
        f: bstack1ll1llll1l1_opy_,
        driver: object,
        exec: Tuple[bstack1llll111ll1_opy_, str],
        bstack1lllll11l1l_opy_: Tuple[bstack1llll11l1l1_opy_, bstack1lllll111l1_opy_],
        result: Any,
        *args,
        **kwargs,
    ):
        instance, _ = exec
        if not instance.ref() in self.drivers:
            return
        self.bstack1l1ll1lll11_opy_(instance)
        self.logger.debug(bstack1ll_opy_ (u"ࠣࡡࡢࡳࡳࡥࡳࡦ࡮ࡨࡲ࡮ࡻ࡭ࡠࡳࡸ࡭ࡹࡀࠠࡪࡰࡶࡸࡦࡴࡣࡦ࠿ࠥኵ") + str(instance.ref()) + bstack1ll_opy_ (u"ࠤࠥ኶"))
    def bstack1l1ll1lll1l_opy_(self, context: bstack1llll11l1ll_opy_, reverse=True) -> List[Tuple[Callable, bstack1llll111ll1_opy_]]:
        matches = []
        if self.pages:
            for data in self.pages.values():
                if data[1].bstack1l1ll1l1l1l_opy_(context):
                    matches.append(data)
        if self.drivers:
            for data in self.drivers.values():
                if (
                    bstack1ll1llll1l1_opy_.bstack1l1ll1l11l1_opy_(data[1])
                    and data[1].bstack1l1ll1l1l1l_opy_(context)
                    and getattr(data[0](), bstack1ll_opy_ (u"ࠥࡷࡪࡹࡳࡪࡱࡱࡣ࡮ࡪࠢ኷"), False)
                ):
                    matches.append(data)
        return sorted(matches, key=lambda d: d[1].bstack1llll111111_opy_, reverse=reverse)
    def bstack1l1ll1ll111_opy_(self, context: bstack1llll11l1ll_opy_, reverse=True) -> List[Tuple[Callable, bstack1llll111ll1_opy_]]:
        matches = []
        for data in self.bstack1l1ll1l11ll_opy_.values():
            if (
                data[1].bstack1l1ll1l1l1l_opy_(context)
                and getattr(data[0](), bstack1ll_opy_ (u"ࠦࡸ࡫ࡳࡴ࡫ࡲࡲࡤ࡯ࡤࠣኸ"), False)
            ):
                matches.append(data)
        return sorted(matches, key=lambda d: d[1].bstack1llll111111_opy_, reverse=reverse)
    def bstack1l1ll1l1l11_opy_(self, instance: bstack1llll111ll1_opy_) -> bool:
        return instance and instance.ref() in self.drivers
    def bstack1l1ll1lll11_opy_(self, instance: bstack1llll111ll1_opy_) -> bool:
        if self.bstack1l1ll1l1l11_opy_(instance):
            self.drivers.pop(instance.ref())
            bstack1llll1ll1ll_opy_.bstack1llll1lll11_opy_(instance, self.bstack1l1ll1llll1_opy_, False)
            return True
        return False