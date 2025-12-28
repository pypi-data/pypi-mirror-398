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
import threading
import logging
import bstack_utils.accessibility as bstack1llll1l11_opy_
from bstack_utils.helper import bstack1l11l11l_opy_
logger = logging.getLogger(__name__)
def bstack1l1lllll1l_opy_(bstack1lll11l1ll_opy_):
  return True if bstack1lll11l1ll_opy_ in threading.current_thread().__dict__.keys() else False
def bstack1lll1l1lll_opy_(context, *args):
    tags = getattr(args[0], bstack1ll_opy_ (u"ࠪࡸࡦ࡭ࡳࠨ៛"), [])
    bstack1lllll11_opy_ = bstack1llll1l11_opy_.bstack1ll11ll1_opy_(tags)
    threading.current_thread().isA11yTest = bstack1lllll11_opy_
    try:
      bstack1l1l11l1_opy_ = threading.current_thread().bstackSessionDriver if bstack1l1lllll1l_opy_(bstack1ll_opy_ (u"ࠫࡧࡹࡴࡢࡥ࡮ࡗࡪࡹࡳࡪࡱࡱࡈࡷ࡯ࡶࡦࡴࠪៜ")) else context.browser
      if bstack1l1l11l1_opy_ and bstack1l1l11l1_opy_.session_id and bstack1lllll11_opy_ and bstack1l11l11l_opy_(
              threading.current_thread(), bstack1ll_opy_ (u"ࠬࡧ࠱࠲ࡻࡓࡰࡦࡺࡦࡰࡴࡰࠫ៝"), None):
          threading.current_thread().isA11yTest = bstack1llll1l11_opy_.bstack1l11l111l1_opy_(bstack1l1l11l1_opy_, bstack1lllll11_opy_)
    except Exception as e:
       logger.debug(bstack1ll_opy_ (u"࠭ࡆࡢ࡫࡯ࡩࡩࠦࡴࡰࠢࡶࡸࡦࡸࡴࠡࡣ࠴࠵ࡾࠦࡩ࡯ࠢࡥࡩ࡭ࡧࡶࡦ࠼ࠣࡿࢂ࠭៞").format(str(e)))
def bstack1l1lll111_opy_(bstack1l1l11l1_opy_):
    if bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠧࡪࡵࡄ࠵࠶ࡿࡔࡦࡵࡷࠫ៟"), None) and bstack1l11l11l_opy_(
      threading.current_thread(), bstack1ll_opy_ (u"ࠨࡣ࠴࠵ࡾࡖ࡬ࡢࡶࡩࡳࡷࡳࠧ០"), None) and not bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠩࡤ࠵࠶ࡿ࡟ࡴࡶࡲࡴࠬ១"), False):
      threading.current_thread().a11y_stop = True
      bstack1llll1l11_opy_.bstack111111l11_opy_(bstack1l1l11l1_opy_, name=bstack1ll_opy_ (u"ࠥࠦ២"), path=bstack1ll_opy_ (u"ࠦࠧ៣"))