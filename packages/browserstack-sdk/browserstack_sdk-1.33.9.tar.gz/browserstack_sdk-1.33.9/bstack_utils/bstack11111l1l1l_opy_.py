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
def bstack1lllllll1ll_opy_(package_name):
    bstack1ll_opy_ (u"ࠦࠧࠨࡃࡩࡧࡦ࡯ࠥ࡯ࡦࠡࡣࠣࡴࡦࡩ࡫ࡢࡩࡨࠤ࡮ࡹࠠࡪࡰࡶࡸࡦࡲ࡬ࡦࡦࠣ࡭ࡳࠦࡴࡩࡧࠣࡩࡳࡼࡩࡳࡱࡱࡱࡪࡴࡴࠋࠢࠣࠤࠥࡇࡲࡨࡵ࠽ࠎࠥࠦࠠࠡࠢࠣࠤࠥࡶࡡࡤ࡭ࡤ࡫ࡪࡥ࡮ࡢ࡯ࡨ࠾ࠥࡔࡡ࡮ࡧࠣࡳ࡫ࠦࡴࡩࡧࠣࡴࡦࡩ࡫ࡢࡩࡨࠤࡹࡵࠠࡤࡪࡨࡧࡰࠦࠨࡦ࠰ࡪ࠲࠱ࠦࠧࡱࡻࡷࡩࡸࡺ࡟ࡱࡣࡵࡥࡱࡲࡥ࡭ࠩࠬࠎࠥࠦࠠࠡࡔࡨࡸࡺࡸ࡮ࡴ࠼ࠍࠤࠥࠦࠠࠡࠢࠣࠤࡧࡵ࡯࡭࠼ࠣࡘࡷࡻࡥࠡ࡫ࡩࠤࡵࡧࡣ࡬ࡣࡪࡩࠥ࡯ࡳࠡ࡫ࡱࡷࡹࡧ࡬࡭ࡧࡧ࠰ࠥࡌࡡ࡭ࡵࡨࠤࡴࡺࡨࡦࡴࡺ࡭ࡸ࡫ࠊࠡࠢࠣࠤࠧࠨࠢὅ")
    try:
        import importlib
        import importlib.util
        if hasattr(importlib.util, bstack1ll_opy_ (u"ࠬ࡬ࡩ࡯ࡦࡢࡷࡵ࡫ࡣࠨ὆")):
            bstack11111lll111_opy_ = importlib.util.find_spec(package_name)
            return bstack11111lll111_opy_ is not None and bstack11111lll111_opy_.loader is not None
        elif hasattr(importlib, bstack1ll_opy_ (u"࠭ࡦࡪࡰࡧࡣࡱࡵࡡࡥࡧࡵࠫ὇")):
            bstack11111ll1lll_opy_ = importlib.find_loader(package_name)
            return bstack11111ll1lll_opy_ is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        pass
    return False