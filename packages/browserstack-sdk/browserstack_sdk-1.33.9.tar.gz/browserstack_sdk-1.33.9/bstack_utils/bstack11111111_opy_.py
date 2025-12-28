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
from browserstack_sdk.bstack11ll1ll111_opy_ import bstack1l111ll1l_opy_
from browserstack_sdk.bstack111l11l1ll_opy_ import RobotHandler
def bstack111111l1_opy_(framework):
    if framework.lower() == bstack1ll_opy_ (u"ࠪࡴࡾࡺࡥࡴࡶࠪ᭩"):
        return bstack1l111ll1l_opy_.version()
    elif framework.lower() == bstack1ll_opy_ (u"ࠫࡷࡵࡢࡰࡶࠪ᭪"):
        return RobotHandler.version()
    elif framework.lower() == bstack1ll_opy_ (u"ࠬࡨࡥࡩࡣࡹࡩࠬ᭫"):
        import behave
        return behave.__version__
    else:
        return bstack1ll_opy_ (u"࠭ࡵ࡯࡭ࡱࡳࡼࡴ᭬ࠧ")
def bstack11ll1111_opy_():
    import importlib.metadata
    framework_name = []
    framework_version = []
    try:
        from selenium import webdriver
        framework_name.append(bstack1ll_opy_ (u"ࠧࡴࡧ࡯ࡩࡳ࡯ࡵ࡮ࠩ᭭"))
        framework_version.append(importlib.metadata.version(bstack1ll_opy_ (u"ࠣࡵࡨࡰࡪࡴࡩࡶ࡯ࠥ᭮")))
    except:
        pass
    try:
        import playwright
        framework_name.append(bstack1ll_opy_ (u"ࠩࡳࡰࡦࡿࡷࡳ࡫ࡪ࡬ࡹ࠭᭯"))
        framework_version.append(importlib.metadata.version(bstack1ll_opy_ (u"ࠥࡴࡱࡧࡹࡸࡴ࡬࡫࡭ࡺࠢ᭰")))
    except:
        pass
    return {
        bstack1ll_opy_ (u"ࠫࡳࡧ࡭ࡦࠩ᭱"): bstack1ll_opy_ (u"ࠬࡥࠧ᭲").join(framework_name),
        bstack1ll_opy_ (u"࠭ࡶࡦࡴࡶ࡭ࡴࡴࠧ᭳"): bstack1ll_opy_ (u"ࠧࡠࠩ᭴").join(framework_version)
    }