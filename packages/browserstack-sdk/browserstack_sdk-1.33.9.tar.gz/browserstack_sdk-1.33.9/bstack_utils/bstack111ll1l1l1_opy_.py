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
import threading
from bstack_utils.helper import bstack11l11lllll_opy_
from bstack_utils.constants import bstack11l11lllll1_opy_, EVENTS, STAGE
from bstack_utils.bstack11l1l1lll1_opy_ import get_logger
logger = get_logger(__name__)
class bstack1l11111lll_opy_:
    bstack1lllll111ll1_opy_ = None
    @classmethod
    def bstack111111lll_opy_(cls):
        if cls.on() and os.getenv(bstack1ll_opy_ (u"ࠦࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡘࡊ࡙ࡔࡉࡗࡅࡣ࡚࡛ࡉࡅࠤ⊔")):
            logger.info(
                bstack1ll_opy_ (u"ࠬ࡜ࡩࡴ࡫ࡷࠤ࡭ࡺࡴࡱࡵ࠽࠳࠴ࡧࡵࡵࡱࡰࡥࡹ࡯࡯࡯࠰ࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫࠯ࡥࡲࡱ࠴ࡨࡵࡪ࡮ࡧࡷ࠴ࢁࡽࠡࡶࡲࠤࡻ࡯ࡥࡸࠢࡥࡹ࡮ࡲࡤࠡࡴࡨࡴࡴࡸࡴ࠭ࠢ࡬ࡲࡸ࡯ࡧࡩࡶࡶ࠰ࠥࡧ࡮ࡥࠢࡰࡥࡳࡿࠠ࡮ࡱࡵࡩࠥࡪࡥࡣࡷࡪ࡫࡮ࡴࡧࠡ࡫ࡱࡪࡴࡸ࡭ࡢࡶ࡬ࡳࡳࠦࡡ࡭࡮ࠣࡥࡹࠦ࡯࡯ࡧࠣࡴࡱࡧࡣࡦࠣ࡟ࡲࠬ⊕").format(os.getenv(bstack1ll_opy_ (u"ࠨࡂࡓࡑ࡚ࡗࡊࡘࡓࡕࡃࡆࡏࡤ࡚ࡅࡔࡖࡋ࡙ࡇࡥࡕࡖࡋࡇࠦ⊖"))))
    @classmethod
    def on(cls):
        if os.environ.get(bstack1ll_opy_ (u"ࠧࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡔࡆࡕࡗࡌ࡚ࡈ࡟ࡋ࡙ࡗࠫ⊗"), None) is None or os.environ[bstack1ll_opy_ (u"ࠨࡄࡕࡓ࡜࡙ࡅࡓࡕࡗࡅࡈࡑ࡟ࡕࡇࡖࡘࡍ࡛ࡂࡠࡌ࡚ࡘࠬ⊘")] == bstack1ll_opy_ (u"ࠤࡱࡹࡱࡲࠢ⊙"):
            return False
        return True
    @classmethod
    def bstack1lll1ll111l1_opy_(cls, bs_config, framework=bstack1ll_opy_ (u"ࠥࠦ⊚")):
        bstack11l1ll1111l_opy_ = False
        for fw in bstack11l11lllll1_opy_:
            if fw in framework:
                bstack11l1ll1111l_opy_ = True
        return bstack11l11lllll_opy_(bs_config.get(bstack1ll_opy_ (u"ࠫࡹ࡫ࡳࡵࡑࡥࡷࡪࡸࡶࡢࡤ࡬ࡰ࡮ࡺࡹࠨ⊛"), bstack11l1ll1111l_opy_))
    @classmethod
    def bstack1lll1l1llll1_opy_(cls, framework):
        return framework in bstack11l11lllll1_opy_
    @classmethod
    def bstack1lll1llllll1_opy_(cls, bs_config, framework):
        return cls.bstack1lll1ll111l1_opy_(bs_config, framework) is True and cls.bstack1lll1l1llll1_opy_(framework)
    @staticmethod
    def current_hook_uuid():
        return getattr(threading.current_thread(), bstack1ll_opy_ (u"ࠬࡩࡵࡳࡴࡨࡲࡹࡥࡨࡰࡱ࡮ࡣࡺࡻࡩࡥࠩ⊜"), None)
    @staticmethod
    def bstack111l1lllll_opy_():
        if getattr(threading.current_thread(), bstack1ll_opy_ (u"࠭ࡣࡶࡴࡵࡩࡳࡺ࡟ࡵࡧࡶࡸࡤࡻࡵࡪࡦࠪ⊝"), None):
            return {
                bstack1ll_opy_ (u"ࠧࡵࡻࡳࡩࠬ⊞"): bstack1ll_opy_ (u"ࠨࡶࡨࡷࡹ࠭⊟"),
                bstack1ll_opy_ (u"ࠩࡷࡩࡸࡺ࡟ࡳࡷࡱࡣࡺࡻࡩࡥࠩ⊠"): getattr(threading.current_thread(), bstack1ll_opy_ (u"ࠪࡧࡺࡸࡲࡦࡰࡷࡣࡹ࡫ࡳࡵࡡࡸࡹ࡮ࡪࠧ⊡"), None)
            }
        if getattr(threading.current_thread(), bstack1ll_opy_ (u"ࠫࡨࡻࡲࡳࡧࡱࡸࡤ࡮࡯ࡰ࡭ࡢࡹࡺ࡯ࡤࠨ⊢"), None):
            return {
                bstack1ll_opy_ (u"ࠬࡺࡹࡱࡧࠪ⊣"): bstack1ll_opy_ (u"࠭ࡨࡰࡱ࡮ࠫ⊤"),
                bstack1ll_opy_ (u"ࠧࡩࡱࡲ࡯ࡤࡸࡵ࡯ࡡࡸࡹ࡮ࡪࠧ⊥"): getattr(threading.current_thread(), bstack1ll_opy_ (u"ࠨࡥࡸࡶࡷ࡫࡮ࡵࡡ࡫ࡳࡴࡱ࡟ࡶࡷ࡬ࡨࠬ⊦"), None)
            }
        return None
    @staticmethod
    def bstack1lll1ll11111_opy_(func):
        def wrap(*args, **kwargs):
            if bstack1l11111lll_opy_.on():
                return func(*args, **kwargs)
            return
        return wrap
    @staticmethod
    def bstack111l111111_opy_(test, hook_name=None):
        bstack1lll1l1lll1l_opy_ = test.parent
        if hook_name in [bstack1ll_opy_ (u"ࠩࡶࡩࡹࡻࡰࡠࡥ࡯ࡥࡸࡹࠧ⊧"), bstack1ll_opy_ (u"ࠪࡸࡪࡧࡲࡥࡱࡺࡲࡤࡩ࡬ࡢࡵࡶࠫ⊨"), bstack1ll_opy_ (u"ࠫࡸ࡫ࡴࡶࡲࡢࡱࡴࡪࡵ࡭ࡧࠪ⊩"), bstack1ll_opy_ (u"ࠬࡺࡥࡢࡴࡧࡳࡼࡴ࡟࡮ࡱࡧࡹࡱ࡫ࠧ⊪")]:
            bstack1lll1l1lll1l_opy_ = test
        scope = []
        while bstack1lll1l1lll1l_opy_ is not None:
            scope.append(bstack1lll1l1lll1l_opy_.name)
            bstack1lll1l1lll1l_opy_ = bstack1lll1l1lll1l_opy_.parent
        scope.reverse()
        return scope[2:]
    @staticmethod
    def bstack1lll1l1lllll_opy_(hook_type):
        if hook_type == bstack1ll_opy_ (u"ࠨࡂࡆࡈࡒࡖࡊࡥࡅࡂࡅࡋࠦ⊫"):
            return bstack1ll_opy_ (u"ࠢࡔࡧࡷࡹࡵࠦࡨࡰࡱ࡮ࠦ⊬")
        elif hook_type == bstack1ll_opy_ (u"ࠣࡃࡉࡘࡊࡘ࡟ࡆࡃࡆࡌࠧ⊭"):
            return bstack1ll_opy_ (u"ࠤࡗࡩࡦࡸࡤࡰࡹࡱࠤ࡭ࡵ࡯࡬ࠤ⊮")
    @staticmethod
    def bstack1lll1l1lll11_opy_(bstack1ll11l111_opy_):
        try:
            if not bstack1l11111lll_opy_.on():
                return bstack1ll11l111_opy_
            if os.environ.get(bstack1ll_opy_ (u"ࠥࡆࡗࡕࡗࡔࡇࡕࡗ࡙ࡇࡃࡌࡡࡕࡉࡗ࡛ࡎࠣ⊯"), None) == bstack1ll_opy_ (u"ࠦࡹࡸࡵࡦࠤ⊰"):
                tests = os.environ.get(bstack1ll_opy_ (u"ࠧࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣࡗࡋࡒࡖࡐࡢࡘࡊ࡙ࡔࡔࠤ⊱"), None)
                if tests is None or tests == bstack1ll_opy_ (u"ࠨ࡮ࡶ࡮࡯ࠦ⊲"):
                    return bstack1ll11l111_opy_
                bstack1ll11l111_opy_ = tests.split(bstack1ll_opy_ (u"ࠧ࠭ࠩ⊳"))
                return bstack1ll11l111_opy_
        except Exception as exc:
            logger.debug(bstack1ll_opy_ (u"ࠣࡇࡻࡧࡪࡶࡴࡪࡱࡱࠤ࡮ࡴࠠࡳࡧࡵࡹࡳࠦࡨࡢࡰࡧࡰࡪࡸ࠺ࠡࠤ⊴") + str(str(exc)) + bstack1ll_opy_ (u"ࠤࠥ⊵"))
        return bstack1ll11l111_opy_