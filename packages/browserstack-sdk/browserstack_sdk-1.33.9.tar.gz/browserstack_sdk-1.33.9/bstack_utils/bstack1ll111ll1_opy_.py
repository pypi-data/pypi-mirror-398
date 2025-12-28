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
import json
import logging
import datetime
import threading
from bstack_utils.helper import bstack11ll11lllll_opy_, bstack1ll1ll1l_opy_, get_host_info, bstack11l1111llll_opy_, \
 bstack11111l1l_opy_, bstack1l11l11l_opy_, error_handler, bstack11l111llll1_opy_, bstack1l11l1111_opy_
import bstack_utils.accessibility as bstack1llll1l11_opy_
from bstack_utils.bstack1l11l1lll_opy_ import bstack11llll11l1_opy_
from bstack_utils.bstack111ll1l1l1_opy_ import bstack1l11111lll_opy_
from bstack_utils.percy import bstack1lll1lllll_opy_
from bstack_utils.config import Config
bstack1ll1l1l111_opy_ = Config.bstack11lll1111_opy_()
logger = logging.getLogger(__name__)
percy = bstack1lll1lllll_opy_()
@error_handler(class_method=False)
def bstack1lll1lllllll_opy_(bs_config, bstack1l1llll111_opy_):
  try:
    data = {
        bstack1ll_opy_ (u"࠭ࡦࡰࡴࡰࡥࡹ࠭≉"): bstack1ll_opy_ (u"ࠧ࡫ࡵࡲࡲࠬ≊"),
        bstack1ll_opy_ (u"ࠨࡲࡵࡳ࡯࡫ࡣࡵࡡࡱࡥࡲ࡫ࠧ≋"): bs_config.get(bstack1ll_opy_ (u"ࠩࡳࡶࡴࡰࡥࡤࡶࡑࡥࡲ࡫ࠧ≌"), bstack1ll_opy_ (u"ࠪࠫ≍")),
        bstack1ll_opy_ (u"ࠫࡳࡧ࡭ࡦࠩ≎"): bs_config.get(bstack1ll_opy_ (u"ࠬࡨࡵࡪ࡮ࡧࡒࡦࡳࡥࠨ≏"), os.path.basename(os.path.abspath(os.getcwd()))),
        bstack1ll_opy_ (u"࠭ࡢࡶ࡫࡯ࡨࡤ࡯ࡤࡦࡰࡷ࡭࡫࡯ࡥࡳࠩ≐"): bs_config.get(bstack1ll_opy_ (u"ࠧࡣࡷ࡬ࡰࡩࡏࡤࡦࡰࡷ࡭࡫࡯ࡥࡳࠩ≑")),
        bstack1ll_opy_ (u"ࠨࡦࡨࡷࡨࡸࡩࡱࡶ࡬ࡳࡳ࠭≒"): bs_config.get(bstack1ll_opy_ (u"ࠩࡥࡹ࡮ࡲࡤࡅࡧࡶࡧࡷ࡯ࡰࡵ࡫ࡲࡲࠬ≓"), bstack1ll_opy_ (u"ࠪࠫ≔")),
        bstack1ll_opy_ (u"ࠫࡸࡺࡡࡳࡶࡨࡨࡤࡧࡴࠨ≕"): bstack1l11l1111_opy_(),
        bstack1ll_opy_ (u"ࠬࡺࡡࡨࡵࠪ≖"): bstack11l1111llll_opy_(bs_config),
        bstack1ll_opy_ (u"࠭ࡨࡰࡵࡷࡣ࡮ࡴࡦࡰࠩ≗"): get_host_info(),
        bstack1ll_opy_ (u"ࠧࡤ࡫ࡢ࡭ࡳ࡬࡯ࠨ≘"): bstack1ll1ll1l_opy_(),
        bstack1ll_opy_ (u"ࠨࡤࡸ࡭ࡱࡪ࡟ࡳࡷࡱࡣ࡮ࡪࡥ࡯ࡶ࡬ࡪ࡮࡫ࡲࠨ≙"): os.environ.get(bstack1ll_opy_ (u"ࠩࡅࡖࡔ࡝ࡓࡆࡔࡖࡘࡆࡉࡋࡠࡄࡘࡍࡑࡊ࡟ࡓࡗࡑࡣࡎࡊࡅࡏࡖࡌࡊࡎࡋࡒࠨ≚")),
        bstack1ll_opy_ (u"ࠪࡪࡦ࡯࡬ࡦࡦࡢࡸࡪࡹࡴࡴࡡࡵࡩࡷࡻ࡮ࠨ≛"): os.environ.get(bstack1ll_opy_ (u"ࠫࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡖࡊࡘࡕࡏࠩ≜"), False),
        bstack1ll_opy_ (u"ࠬࡼࡥࡳࡵ࡬ࡳࡳࡥࡣࡰࡰࡷࡶࡴࡲࠧ≝"): bstack11ll11lllll_opy_(),
        bstack1ll_opy_ (u"࠭ࡡࡤࡥࡨࡷࡸ࡯ࡢࡪ࡮࡬ࡸࡾ࠭≞"): bstack1lll1ll1l1l1_opy_(bs_config),
        bstack1ll_opy_ (u"ࠧࡧࡴࡤࡱࡪࡽ࡯ࡳ࡭ࡢࡨࡪࡺࡡࡪ࡮ࡶࠫ≟"): bstack1lll1ll111ll_opy_(bstack1l1llll111_opy_),
        bstack1ll_opy_ (u"ࠨࡲࡵࡳࡩࡻࡣࡵࡡࡰࡥࡵ࠭≠"): bstack1lll1ll11l1l_opy_(bs_config, bstack1l1llll111_opy_.get(bstack1ll_opy_ (u"ࠩࡩࡶࡦࡳࡥࡸࡱࡵ࡯ࡤࡻࡳࡦࡦࠪ≡"), bstack1ll_opy_ (u"ࠪࠫ≢"))),
        bstack1ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭ࡄࡹࡹࡵ࡭ࡢࡶ࡬ࡳࡳ࠭≣"): bstack11111l1l_opy_(bs_config),
        bstack1ll_opy_ (u"ࠬࡺࡥࡴࡶࡢࡳࡷࡩࡨࡦࡵࡷࡶࡦࡺࡩࡰࡰࠪ≤"): bstack1lll1ll1l111_opy_(bs_config)
    }
    return data
  except Exception as error:
    logger.error(bstack1ll_opy_ (u"ࠨࡅࡹࡥࡨࡴࡹ࡯࡯࡯ࠢࡺ࡬࡮ࡲࡥࠡࡥࡵࡩࡦࡺࡩ࡯ࡩࠣࡴࡦࡿ࡬ࡰࡣࡧࠤ࡫ࡵࡲࠡࡖࡨࡷࡹࡎࡵࡣ࠼ࠣࠤࢀࢃࠢ≥").format(str(error)))
    return None
def bstack1lll1ll111ll_opy_(framework):
  return {
    bstack1ll_opy_ (u"ࠧࡧࡴࡤࡱࡪࡽ࡯ࡳ࡭ࡑࡥࡲ࡫ࠧ≦"): framework.get(bstack1ll_opy_ (u"ࠨࡨࡵࡥࡲ࡫ࡷࡰࡴ࡮ࡣࡳࡧ࡭ࡦࠩ≧"), bstack1ll_opy_ (u"ࠩࡓࡽࡹ࡫ࡳࡵࠩ≨")),
    bstack1ll_opy_ (u"ࠪࡪࡷࡧ࡭ࡦࡹࡲࡶࡰ࡜ࡥࡳࡵ࡬ࡳࡳ࠭≩"): framework.get(bstack1ll_opy_ (u"ࠫ࡫ࡸࡡ࡮ࡧࡺࡳࡷࡱ࡟ࡷࡧࡵࡷ࡮ࡵ࡮ࠨ≪")),
    bstack1ll_opy_ (u"ࠬࡹࡤ࡬ࡘࡨࡶࡸ࡯࡯࡯ࠩ≫"): framework.get(bstack1ll_opy_ (u"࠭ࡳࡥ࡭ࡢࡺࡪࡸࡳࡪࡱࡱࠫ≬")),
    bstack1ll_opy_ (u"ࠧ࡭ࡣࡱ࡫ࡺࡧࡧࡦࠩ≭"): bstack1ll_opy_ (u"ࠨࡲࡼࡸ࡭ࡵ࡮ࠨ≮"),
    bstack1ll_opy_ (u"ࠩࡷࡩࡸࡺࡆࡳࡣࡰࡩࡼࡵࡲ࡬ࠩ≯"): framework.get(bstack1ll_opy_ (u"ࠪࡸࡪࡹࡴࡇࡴࡤࡱࡪࡽ࡯ࡳ࡭ࠪ≰"))
  }
def bstack1lll1ll1l111_opy_(bs_config):
  bstack1ll_opy_ (u"ࠦࠧࠨࠊࠡࠢࡕࡩࡹࡻࡲ࡯ࡵࠣࡸ࡭࡫ࠠࡵࡧࡶࡸࠥࡵࡲࡤࡪࡨࡷࡹࡸࡡࡵ࡫ࡲࡲࠥࡪࡡࡵࡣࠣࡪࡴࡸࠠࡣࡷ࡬ࡰࡩࠦࡳࡵࡣࡵࡸ࠳ࠐࠠࠡࠤࠥࠦ≱")
  if not bs_config:
    return {}
  bstack1111l1l1ll1_opy_ = bstack11llll11l1_opy_(bs_config).bstack1111l1l11l1_opy_(bs_config)
  return bstack1111l1l1ll1_opy_
def bstack1ll1111ll1_opy_(bs_config, framework):
  bstack1l111l1lll_opy_ = False
  bstack1ll1ll1l1l_opy_ = False
  bstack1lll1ll1lll1_opy_ = False
  if bstack1ll_opy_ (u"ࠬࡺࡵࡳࡤࡲࡗࡨࡧ࡬ࡦࠩ≲") in bs_config:
    bstack1lll1ll1lll1_opy_ = True
  elif bstack1ll_opy_ (u"࠭ࡡࡱࡲࠪ≳") in bs_config:
    bstack1l111l1lll_opy_ = True
  else:
    bstack1ll1ll1l1l_opy_ = True
  bstack11l1l111ll_opy_ = {
    bstack1ll_opy_ (u"ࠧࡰࡤࡶࡩࡷࡼࡡࡣ࡫࡯࡭ࡹࡿࠧ≴"): bstack1l11111lll_opy_.bstack1lll1ll111l1_opy_(bs_config, framework),
    bstack1ll_opy_ (u"ࠨࡣࡦࡧࡪࡹࡳࡪࡤ࡬ࡰ࡮ࡺࡹࠨ≵"): bstack1llll1l11_opy_.bstack1l1lll1lll_opy_(bs_config),
    bstack1ll_opy_ (u"ࠩࡳࡩࡷࡩࡹࠨ≶"): bs_config.get(bstack1ll_opy_ (u"ࠪࡴࡪࡸࡣࡺࠩ≷"), False),
    bstack1ll_opy_ (u"ࠫࡦࡻࡴࡰ࡯ࡤࡸࡪ࠭≸"): bstack1ll1ll1l1l_opy_,
    bstack1ll_opy_ (u"ࠬࡧࡰࡱࡡࡤࡹࡹࡵ࡭ࡢࡶࡨࠫ≹"): bstack1l111l1lll_opy_,
    bstack1ll_opy_ (u"࠭ࡴࡶࡴࡥࡳࡸࡩࡡ࡭ࡧࠪ≺"): bstack1lll1ll1lll1_opy_
  }
  return bstack11l1l111ll_opy_
@error_handler(class_method=False)
def bstack1lll1ll1l1l1_opy_(bs_config):
  try:
    bstack1lll1ll1111l_opy_ = json.loads(os.getenv(bstack1ll_opy_ (u"ࠧࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡔࡆࡕࡗࡣࡆࡉࡃࡆࡕࡖࡍࡇࡏࡌࡊࡖ࡜ࡣࡈࡕࡎࡇࡋࡊ࡙ࡗࡇࡔࡊࡑࡑࡣ࡞ࡓࡌࠨ≻"), bstack1ll_opy_ (u"ࠨࡽࢀࠫ≼")))
    bstack1lll1ll1111l_opy_ = bstack1lll1ll1ll11_opy_(bs_config, bstack1lll1ll1111l_opy_)
    return {
        bstack1ll_opy_ (u"ࠩࡶࡩࡹࡺࡩ࡯ࡩࡶࠫ≽"): bstack1lll1ll1111l_opy_
    }
  except Exception as error:
    logger.error(bstack1ll_opy_ (u"ࠥࡉࡽࡩࡥࡱࡶ࡬ࡳࡳࠦࡷࡩ࡫࡯ࡩࠥࡩࡲࡦࡣࡷ࡭ࡳ࡭ࠠࡨࡧࡷࡣࡦࡩࡣࡦࡵࡶ࡭ࡧ࡯࡬ࡪࡶࡼࡣࡸ࡫ࡴࡵ࡫ࡱ࡫ࡸࠦࡦࡰࡴࠣࡘࡪࡹࡴࡉࡷࡥ࠾ࠥࠦࡻࡾࠤ≾").format(str(error)))
    return {}
def bstack1lll1ll1ll11_opy_(bs_config, bstack1lll1ll1111l_opy_):
  if ((bstack1ll_opy_ (u"ࠫࡹࡻࡲࡣࡱࡖࡧࡦࡲࡥࠨ≿") in bs_config or not bstack11111l1l_opy_(bs_config)) and bstack1llll1l11_opy_.bstack1l1lll1lll_opy_(bs_config)):
    bstack1lll1ll1111l_opy_[bstack1ll_opy_ (u"ࠧ࡯࡮ࡤ࡮ࡸࡨࡪࡋ࡮ࡤࡱࡧࡩࡩࡋࡸࡵࡧࡱࡷ࡮ࡵ࡮ࠣ⊀")] = True
  return bstack1lll1ll1111l_opy_
def bstack1llll11111ll_opy_(array, bstack1lll1ll1ll1l_opy_, bstack1lll1ll1l11l_opy_):
  result = {}
  for o in array:
    key = o[bstack1lll1ll1ll1l_opy_]
    result[key] = o[bstack1lll1ll1l11l_opy_]
  return result
def bstack1lll1llll11l_opy_(bstack1111l111_opy_=bstack1ll_opy_ (u"࠭ࠧ⊁")):
  bstack1lll1ll11l11_opy_ = bstack1llll1l11_opy_.on()
  bstack1lll1ll11ll1_opy_ = bstack1l11111lll_opy_.on()
  bstack1lll1ll1l1ll_opy_ = percy.bstack11ll11lll1_opy_()
  if bstack1lll1ll1l1ll_opy_ and not bstack1lll1ll11ll1_opy_ and not bstack1lll1ll11l11_opy_:
    return bstack1111l111_opy_ not in [bstack1ll_opy_ (u"ࠧࡄࡄࡗࡗࡪࡹࡳࡪࡱࡱࡇࡷ࡫ࡡࡵࡧࡧࠫ⊂"), bstack1ll_opy_ (u"ࠨࡎࡲ࡫ࡈࡸࡥࡢࡶࡨࡨࠬ⊃")]
  elif bstack1lll1ll11l11_opy_ and not bstack1lll1ll11ll1_opy_:
    return bstack1111l111_opy_ not in [bstack1ll_opy_ (u"ࠩࡋࡳࡴࡱࡒࡶࡰࡖࡸࡦࡸࡴࡦࡦࠪ⊄"), bstack1ll_opy_ (u"ࠪࡌࡴࡵ࡫ࡓࡷࡱࡊ࡮ࡴࡩࡴࡪࡨࡨࠬ⊅"), bstack1ll_opy_ (u"ࠫࡑࡵࡧࡄࡴࡨࡥࡹ࡫ࡤࠨ⊆")]
  return bstack1lll1ll11l11_opy_ or bstack1lll1ll11ll1_opy_ or bstack1lll1ll1l1ll_opy_
@error_handler(class_method=False)
def bstack1llll1111l1l_opy_(bstack1111l111_opy_, test=None):
  bstack1lll1ll11lll_opy_ = bstack1llll1l11_opy_.on()
  if not bstack1lll1ll11lll_opy_ or bstack1111l111_opy_ not in [bstack1ll_opy_ (u"࡚ࠬࡥࡴࡶࡕࡹࡳࡌࡩ࡯࡫ࡶ࡬ࡪࡪࠧ⊇")] or test == None:
    return None
  return {
    bstack1ll_opy_ (u"࠭ࡡࡤࡥࡨࡷࡸ࡯ࡢࡪ࡮࡬ࡸࡾ࠭⊈"): bstack1lll1ll11lll_opy_ and bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠧࡢ࠳࠴ࡽࡕࡲࡡࡵࡨࡲࡶࡲ࠭⊉"), None) == True and bstack1llll1l11_opy_.bstack1ll11ll1_opy_(test[bstack1ll_opy_ (u"ࠨࡶࡤ࡫ࡸ࠭⊊")])
  }
def bstack1lll1ll11l1l_opy_(bs_config, framework):
  bstack1l111l1lll_opy_ = False
  bstack1ll1ll1l1l_opy_ = False
  bstack1lll1ll1lll1_opy_ = False
  if bstack1ll_opy_ (u"ࠩࡷࡹࡷࡨ࡯ࡔࡥࡤࡰࡪ࠭⊋") in bs_config:
    bstack1lll1ll1lll1_opy_ = True
  elif bstack1ll_opy_ (u"ࠪࡥࡵࡶࠧ⊌") in bs_config:
    bstack1l111l1lll_opy_ = True
  else:
    bstack1ll1ll1l1l_opy_ = True
  bstack11l1l111ll_opy_ = {
    bstack1ll_opy_ (u"ࠫࡴࡨࡳࡦࡴࡹࡥࡧ࡯࡬ࡪࡶࡼࠫ⊍"): bstack1l11111lll_opy_.bstack1lll1ll111l1_opy_(bs_config, framework),
    bstack1ll_opy_ (u"ࠬࡧࡣࡤࡧࡶࡷ࡮ࡨࡩ࡭࡫ࡷࡽࠬ⊎"): bstack1llll1l11_opy_.bstack1l1l111lll_opy_(bs_config),
    bstack1ll_opy_ (u"࠭ࡰࡦࡴࡦࡽࠬ⊏"): bs_config.get(bstack1ll_opy_ (u"ࠧࡱࡧࡵࡧࡾ࠭⊐"), False),
    bstack1ll_opy_ (u"ࠨࡣࡸࡸࡴࡳࡡࡵࡧࠪ⊑"): bstack1ll1ll1l1l_opy_,
    bstack1ll_opy_ (u"ࠩࡤࡴࡵࡥࡡࡶࡶࡲࡱࡦࡺࡥࠨ⊒"): bstack1l111l1lll_opy_,
    bstack1ll_opy_ (u"ࠪࡸࡺࡸࡢࡰࡵࡦࡥࡱ࡫ࠧ⊓"): bstack1lll1ll1lll1_opy_
  }
  return bstack11l1l111ll_opy_