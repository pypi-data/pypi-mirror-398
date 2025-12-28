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
import requests
import logging
import threading
import bstack_utils.constants as bstack11ll111111l_opy_
from urllib.parse import urlparse
from bstack_utils.constants import bstack11ll111l1ll_opy_ as bstack11ll111l1l1_opy_, EVENTS
from bstack_utils.bstack1111l1ll1_opy_ import bstack1111l1ll1_opy_
from bstack_utils.helper import bstack1l11l1111_opy_, bstack111l11ll1l_opy_, bstack11111l1l_opy_, bstack11ll11llll1_opy_, \
  bstack11ll11ll1ll_opy_, bstack1ll1ll1l_opy_, get_host_info, bstack11ll11lllll_opy_, bstack1l111111_opy_, error_handler, bstack11ll1111ll1_opy_, bstack11ll1111l11_opy_, bstack1l11l11l_opy_
from browserstack_sdk._version import __version__
from bstack_utils.bstack11l1l1lll1_opy_ import get_logger
from bstack_utils.bstack11ll1llll1_opy_ import bstack1lll1ll1l1l_opy_
from selenium.webdriver.chrome.options import Options as ChromeOptions
from browserstack_sdk.sdk_cli.cli import cli
from bstack_utils.constants import *
logger = get_logger(__name__)
bstack11ll1llll1_opy_ = bstack1lll1ll1l1l_opy_()
@error_handler(class_method=False)
def _11ll11ll11l_opy_(driver, bstack11111l1111_opy_):
  response = {}
  try:
    caps = driver.capabilities
    response = {
        bstack1ll_opy_ (u"ࠧࡰࡵࡢࡲࡦࡳࡥࠨᙺ"): caps.get(bstack1ll_opy_ (u"ࠨࡲ࡯ࡥࡹ࡬࡯ࡳ࡯ࡑࡥࡲ࡫ࠧᙻ"), None),
        bstack1ll_opy_ (u"ࠩࡲࡷࡤࡼࡥࡳࡵ࡬ࡳࡳ࠭ᙼ"): bstack11111l1111_opy_.get(bstack1ll_opy_ (u"ࠪࡳࡸ࡜ࡥࡳࡵ࡬ࡳࡳ࠭ᙽ"), None),
        bstack1ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࡤࡴࡡ࡮ࡧࠪᙾ"): caps.get(bstack1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡔࡡ࡮ࡧࠪᙿ"), None),
        bstack1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸ࡟ࡷࡧࡵࡷ࡮ࡵ࡮ࠨ "): caps.get(bstack1ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡗࡧࡵࡷ࡮ࡵ࡮ࠨᚁ"), None)
    }
  except Exception as error:
    logger.debug(bstack1ll_opy_ (u"ࠨࡇࡻࡧࡪࡶࡴࡪࡱࡱࠤ࡮ࡴࠠࡧࡧࡷࡧ࡭࡯࡮ࡨࠢࡳࡰࡦࡺࡦࡰࡴࡰࠤࡩ࡫ࡴࡢ࡫࡯ࡷࠥࡽࡩࡵࡪࠣࡩࡷࡸ࡯ࡳࠢ࠽ࠤࠬᚂ") + str(error))
  return response
def on():
    if os.environ.get(bstack1ll_opy_ (u"ࠩࡅࡗࡤࡇ࠱࠲࡛ࡢࡎ࡜࡚ࠧᚃ"), None) is None or os.environ[bstack1ll_opy_ (u"ࠪࡆࡘࡥࡁ࠲࠳࡜ࡣࡏ࡝ࡔࠨᚄ")] == bstack1ll_opy_ (u"ࠦࡳࡻ࡬࡭ࠤᚅ"):
        return False
    return True
def bstack1l1lll1lll_opy_(config):
  return config.get(bstack1ll_opy_ (u"ࠬࡧࡣࡤࡧࡶࡷ࡮ࡨࡩ࡭࡫ࡷࡽࠬᚆ"), False) or any([p.get(bstack1ll_opy_ (u"࠭ࡡࡤࡥࡨࡷࡸ࡯ࡢࡪ࡮࡬ࡸࡾ࠭ᚇ"), False) == True for p in config.get(bstack1ll_opy_ (u"ࠧࡱ࡮ࡤࡸ࡫ࡵࡲ࡮ࡵࠪᚈ"), [])])
def bstack1l111lll1l_opy_(config, bstack11l1l1l1_opy_):
  try:
    bstack11ll111l11l_opy_ = config.get(bstack1ll_opy_ (u"ࠨࡣࡦࡧࡪࡹࡳࡪࡤ࡬ࡰ࡮ࡺࡹࠨᚉ"), False)
    if int(bstack11l1l1l1_opy_) < len(config.get(bstack1ll_opy_ (u"ࠩࡳࡰࡦࡺࡦࡰࡴࡰࡷࠬᚊ"), [])) and config[bstack1ll_opy_ (u"ࠪࡴࡱࡧࡴࡧࡱࡵࡱࡸ࠭ᚋ")][bstack11l1l1l1_opy_]:
      bstack11ll11l11ll_opy_ = config[bstack1ll_opy_ (u"ࠫࡵࡲࡡࡵࡨࡲࡶࡲࡹࠧᚌ")][bstack11l1l1l1_opy_].get(bstack1ll_opy_ (u"ࠬࡧࡣࡤࡧࡶࡷ࡮ࡨࡩ࡭࡫ࡷࡽࠬᚍ"), None)
    else:
      bstack11ll11l11ll_opy_ = config.get(bstack1ll_opy_ (u"࠭ࡡࡤࡥࡨࡷࡸ࡯ࡢࡪ࡮࡬ࡸࡾ࠭ᚎ"), None)
    if bstack11ll11l11ll_opy_ != None:
      bstack11ll111l11l_opy_ = bstack11ll11l11ll_opy_
    bstack11ll111lll1_opy_ = os.getenv(bstack1ll_opy_ (u"ࠧࡃࡕࡢࡅ࠶࠷࡙ࡠࡌ࡚ࡘࠬᚏ")) is not None and len(os.getenv(bstack1ll_opy_ (u"ࠨࡄࡖࡣࡆ࠷࠱࡚ࡡࡍ࡛࡙࠭ᚐ"))) > 0 and os.getenv(bstack1ll_opy_ (u"ࠩࡅࡗࡤࡇ࠱࠲࡛ࡢࡎ࡜࡚ࠧᚑ")) != bstack1ll_opy_ (u"ࠪࡲࡺࡲ࡬ࠨᚒ")
    return bstack11ll111l11l_opy_ and bstack11ll111lll1_opy_
  except Exception as error:
    logger.debug(bstack1ll_opy_ (u"ࠫࡊࡾࡣࡦࡲࡷ࡭ࡴࡴࠠࡪࡰࠣࡺࡪࡸࡩࡧࡻ࡬ࡲ࡬ࠦࡴࡩࡧࠣࡅࡨࡩࡥࡴࡵ࡬ࡦ࡮ࡲࡩࡵࡻࠣࡷࡪࡹࡳࡪࡱࡱࠤࡼ࡯ࡴࡩࠢࡨࡶࡷࡵࡲࠡ࠼ࠣࠫᚓ") + str(error))
  return False
def bstack1ll11ll1_opy_(test_tags):
  bstack1l1llll11ll_opy_ = os.getenv(bstack1ll_opy_ (u"ࠬࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣ࡙ࡋࡓࡕࡡࡄࡇࡈࡋࡓࡔࡋࡅࡍࡑࡏࡔ࡚ࡡࡆࡓࡓࡌࡉࡈࡗࡕࡅ࡙ࡏࡏࡏࡡ࡜ࡑࡑ࠭ᚔ"))
  if bstack1l1llll11ll_opy_ is None:
    return True
  bstack1l1llll11ll_opy_ = json.loads(bstack1l1llll11ll_opy_)
  try:
    include_tags = bstack1l1llll11ll_opy_[bstack1ll_opy_ (u"࠭ࡩ࡯ࡥ࡯ࡹࡩ࡫ࡔࡢࡩࡶࡍࡳ࡚ࡥࡴࡶ࡬ࡲ࡬࡙ࡣࡰࡲࡨࠫᚕ")] if bstack1ll_opy_ (u"ࠧࡪࡰࡦࡰࡺࡪࡥࡕࡣࡪࡷࡎࡴࡔࡦࡵࡷ࡭ࡳ࡭ࡓࡤࡱࡳࡩࠬᚖ") in bstack1l1llll11ll_opy_ and isinstance(bstack1l1llll11ll_opy_[bstack1ll_opy_ (u"ࠨ࡫ࡱࡧࡱࡻࡤࡦࡖࡤ࡫ࡸࡏ࡮ࡕࡧࡶࡸ࡮ࡴࡧࡔࡥࡲࡴࡪ࠭ᚗ")], list) else []
    exclude_tags = bstack1l1llll11ll_opy_[bstack1ll_opy_ (u"ࠩࡨࡼࡨࡲࡵࡥࡧࡗࡥ࡬ࡹࡉ࡯ࡖࡨࡷࡹ࡯࡮ࡨࡕࡦࡳࡵ࡫ࠧᚘ")] if bstack1ll_opy_ (u"ࠪࡩࡽࡩ࡬ࡶࡦࡨࡘࡦ࡭ࡳࡊࡰࡗࡩࡸࡺࡩ࡯ࡩࡖࡧࡴࡶࡥࠨᚙ") in bstack1l1llll11ll_opy_ and isinstance(bstack1l1llll11ll_opy_[bstack1ll_opy_ (u"ࠫࡪࡾࡣ࡭ࡷࡧࡩ࡙ࡧࡧࡴࡋࡱࡘࡪࡹࡴࡪࡰࡪࡗࡨࡵࡰࡦࠩᚚ")], list) else []
    excluded = any(tag in exclude_tags for tag in test_tags)
    included = len(include_tags) == 0 or any(tag in include_tags for tag in test_tags)
    return not excluded and included
  except Exception as error:
    logger.debug(bstack1ll_opy_ (u"ࠧࡋࡲࡳࡱࡵࠤࡼ࡮ࡩ࡭ࡧࠣࡺࡦࡲࡩࡥࡣࡷ࡭ࡳ࡭ࠠࡵࡧࡶࡸࠥࡩࡡࡴࡧࠣࡪࡴࡸࠠࡢࡥࡦࡩࡸࡹࡩࡣ࡫࡯࡭ࡹࡿࠠࡣࡧࡩࡳࡷ࡫ࠠࡴࡥࡤࡲࡳ࡯࡮ࡨ࠰ࠣࡉࡷࡸ࡯ࡳࠢ࠽ࠤࠧ᚛") + str(error))
  return False
def bstack11ll11lll11_opy_(config, bstack11ll11ll111_opy_, bstack11ll11111l1_opy_, bstack11ll11l1ll1_opy_):
  bstack11ll11111ll_opy_ = bstack11ll11llll1_opy_(config)
  bstack11ll11l111l_opy_ = bstack11ll11ll1ll_opy_(config)
  if bstack11ll11111ll_opy_ is None or bstack11ll11l111l_opy_ is None:
    logger.error(bstack1ll_opy_ (u"࠭ࡅࡹࡥࡨࡴࡹ࡯࡯࡯ࠢࡺ࡬࡮ࡲࡥࠡࡥࡵࡩࡦࡺࡩ࡯ࡩࠣࡸࡪࡹࡴࠡࡴࡸࡲࠥ࡬࡯ࡳࠢࡅࡶࡴࡽࡳࡦࡴࡖࡸࡦࡩ࡫ࠡࡃࡦࡧࡪࡹࡳࡪࡤ࡬ࡰ࡮ࡺࡹࠡࡃࡸࡸࡴࡳࡡࡵ࡫ࡲࡲ࠿ࠦࡍࡪࡵࡶ࡭ࡳ࡭ࠠࡢࡷࡷ࡬ࡪࡴࡴࡪࡥࡤࡸ࡮ࡵ࡮ࠡࡶࡲ࡯ࡪࡴࠧ᚜"))
    return [None, None]
  try:
    settings = json.loads(os.getenv(bstack1ll_opy_ (u"ࠧࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡔࡆࡕࡗࡣࡆࡉࡃࡆࡕࡖࡍࡇࡏࡌࡊࡖ࡜ࡣࡈࡕࡎࡇࡋࡊ࡙ࡗࡇࡔࡊࡑࡑࡣ࡞ࡓࡌࠨ᚝"), bstack1ll_opy_ (u"ࠨࡽࢀࠫ᚞")))
    data = {
        bstack1ll_opy_ (u"ࠩࡳࡶࡴࡰࡥࡤࡶࡑࡥࡲ࡫ࠧ᚟"): config[bstack1ll_opy_ (u"ࠪࡴࡷࡵࡪࡦࡥࡷࡒࡦࡳࡥࠨᚠ")],
        bstack1ll_opy_ (u"ࠫࡧࡻࡩ࡭ࡦࡑࡥࡲ࡫ࠧᚡ"): config.get(bstack1ll_opy_ (u"ࠬࡨࡵࡪ࡮ࡧࡒࡦࡳࡥࠨᚢ"), os.path.basename(os.getcwd())),
        bstack1ll_opy_ (u"࠭ࡳࡵࡣࡵࡸ࡙࡯࡭ࡦࠩᚣ"): bstack1l11l1111_opy_(),
        bstack1ll_opy_ (u"ࠧࡥࡧࡶࡧࡷ࡯ࡰࡵ࡫ࡲࡲࠬᚤ"): config.get(bstack1ll_opy_ (u"ࠨࡤࡸ࡭ࡱࡪࡄࡦࡵࡦࡶ࡮ࡶࡴࡪࡱࡱࠫᚥ"), bstack1ll_opy_ (u"ࠩࠪᚦ")),
        bstack1ll_opy_ (u"ࠪࡷࡴࡻࡲࡤࡧࠪᚧ"): {
            bstack1ll_opy_ (u"ࠫ࡫ࡸࡡ࡮ࡧࡺࡳࡷࡱࡎࡢ࡯ࡨࠫᚨ"): bstack11ll11ll111_opy_,
            bstack1ll_opy_ (u"ࠬ࡬ࡲࡢ࡯ࡨࡻࡴࡸ࡫ࡗࡧࡵࡷ࡮ࡵ࡮ࠨᚩ"): bstack11ll11111l1_opy_,
            bstack1ll_opy_ (u"࠭ࡳࡥ࡭࡙ࡩࡷࡹࡩࡰࡰࠪᚪ"): __version__,
            bstack1ll_opy_ (u"ࠧ࡭ࡣࡱ࡫ࡺࡧࡧࡦࠩᚫ"): bstack1ll_opy_ (u"ࠨࡲࡼࡸ࡭ࡵ࡮ࠨᚬ"),
            bstack1ll_opy_ (u"ࠩࡷࡩࡸࡺࡆࡳࡣࡰࡩࡼࡵࡲ࡬ࠩᚭ"): bstack1ll_opy_ (u"ࠪࡷࡪࡲࡥ࡯࡫ࡸࡱࠬᚮ"),
            bstack1ll_opy_ (u"ࠫࡹ࡫ࡳࡵࡈࡵࡥࡲ࡫ࡷࡰࡴ࡮࡚ࡪࡸࡳࡪࡱࡱࠫᚯ"): bstack11ll11l1ll1_opy_
        },
        bstack1ll_opy_ (u"ࠬࡹࡥࡵࡶ࡬ࡲ࡬ࡹࠧᚰ"): settings,
        bstack1ll_opy_ (u"࠭ࡶࡦࡴࡶ࡭ࡴࡴࡃࡰࡰࡷࡶࡴࡲࠧᚱ"): bstack11ll11lllll_opy_(),
        bstack1ll_opy_ (u"ࠧࡤ࡫ࡌࡲ࡫ࡵࠧᚲ"): bstack1ll1ll1l_opy_(),
        bstack1ll_opy_ (u"ࠨࡪࡲࡷࡹࡏ࡮ࡧࡱࠪᚳ"): get_host_info(),
        bstack1ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫ࡂࡷࡷࡳࡲࡧࡴࡪࡱࡱࠫᚴ"): bstack11111l1l_opy_(config)
    }
    headers = {
        bstack1ll_opy_ (u"ࠪࡇࡴࡴࡴࡦࡰࡷ࠱࡙ࡿࡰࡦࠩᚵ"): bstack1ll_opy_ (u"ࠫࡦࡶࡰ࡭࡫ࡦࡥࡹ࡯࡯࡯࠱࡭ࡷࡴࡴࠧᚶ"),
    }
    config = {
        bstack1ll_opy_ (u"ࠬࡧࡵࡵࡪࠪᚷ"): (bstack11ll11111ll_opy_, bstack11ll11l111l_opy_),
        bstack1ll_opy_ (u"࠭ࡨࡦࡣࡧࡩࡷࡹࠧᚸ"): headers
    }
    response = bstack1l111111_opy_(bstack1ll_opy_ (u"ࠧࡑࡑࡖࡘࠬᚹ"), bstack11ll111l1l1_opy_ + bstack1ll_opy_ (u"ࠨ࠱ࡹ࠶࠴ࡺࡥࡴࡶࡢࡶࡺࡴࡳࠨᚺ"), data, config)
    bstack11l1lllllll_opy_ = response.json()
    if bstack11l1lllllll_opy_[bstack1ll_opy_ (u"ࠩࡶࡹࡨࡩࡥࡴࡵࠪᚻ")]:
      parsed = json.loads(os.getenv(bstack1ll_opy_ (u"ࠪࡆࡗࡕࡗࡔࡇࡕࡗ࡙ࡇࡃࡌࡡࡗࡉࡘ࡚࡟ࡂࡅࡆࡉࡘ࡙ࡉࡃࡋࡏࡍ࡙࡟࡟ࡄࡑࡑࡊࡎࡍࡕࡓࡃࡗࡍࡔࡔ࡟࡚ࡏࡏࠫᚼ"), bstack1ll_opy_ (u"ࠫࢀࢃࠧᚽ")))
      parsed[bstack1ll_opy_ (u"ࠬࡹࡣࡢࡰࡱࡩࡷ࡜ࡥࡳࡵ࡬ࡳࡳ࠭ᚾ")] = bstack11l1lllllll_opy_[bstack1ll_opy_ (u"࠭ࡤࡢࡶࡤࠫᚿ")][bstack1ll_opy_ (u"ࠧࡴࡥࡤࡲࡳ࡫ࡲࡗࡧࡵࡷ࡮ࡵ࡮ࠨᛀ")]
      os.environ[bstack1ll_opy_ (u"ࠨࡄࡕࡓ࡜࡙ࡅࡓࡕࡗࡅࡈࡑ࡟ࡕࡇࡖࡘࡤࡇࡃࡄࡇࡖࡗࡎࡈࡉࡍࡋࡗ࡝ࡤࡉࡏࡏࡈࡌࡋ࡚ࡘࡁࡕࡋࡒࡒࡤ࡟ࡍࡍࠩᛁ")] = json.dumps(parsed)
      bstack1111l1ll1_opy_.bstack1l111lll_opy_(bstack11l1lllllll_opy_[bstack1ll_opy_ (u"ࠩࡧࡥࡹࡧࠧᛂ")][bstack1ll_opy_ (u"ࠪࡷࡨࡸࡩࡱࡶࡶࠫᛃ")])
      bstack1111l1ll1_opy_.bstack11ll1l11111_opy_(bstack11l1lllllll_opy_[bstack1ll_opy_ (u"ࠫࡩࡧࡴࡢࠩᛄ")][bstack1ll_opy_ (u"ࠬࡩ࡯࡮࡯ࡤࡲࡩࡹࠧᛅ")])
      bstack1111l1ll1_opy_.store()
      return bstack11l1lllllll_opy_[bstack1ll_opy_ (u"࠭ࡤࡢࡶࡤࠫᛆ")][bstack1ll_opy_ (u"ࠧࡢࡥࡦࡩࡸࡹࡩࡣ࡫࡯࡭ࡹࡿࡔࡰ࡭ࡨࡲࠬᛇ")], bstack11l1lllllll_opy_[bstack1ll_opy_ (u"ࠨࡦࡤࡸࡦ࠭ᛈ")][bstack1ll_opy_ (u"ࠩ࡬ࡨࠬᛉ")]
    else:
      logger.error(bstack1ll_opy_ (u"ࠪࡉࡽࡩࡥࡱࡶ࡬ࡳࡳࠦࡷࡩ࡫࡯ࡩࠥࡸࡵ࡯ࡰ࡬ࡲ࡬ࠦࡂࡳࡱࡺࡷࡪࡸࡓࡵࡣࡦ࡯ࠥࡇࡣࡤࡧࡶࡷ࡮ࡨࡩ࡭࡫ࡷࡽࠥࡇࡵࡵࡱࡰࡥࡹ࡯࡯࡯࠼ࠣࠫᛊ") + bstack11l1lllllll_opy_[bstack1ll_opy_ (u"ࠫࡲ࡫ࡳࡴࡣࡪࡩࠬᛋ")])
      if bstack11l1lllllll_opy_[bstack1ll_opy_ (u"ࠬࡳࡥࡴࡵࡤ࡫ࡪ࠭ᛌ")] == bstack1ll_opy_ (u"࠭ࡉ࡯ࡸࡤࡰ࡮ࡪࠠࡤࡱࡱࡪ࡮࡭ࡵࡳࡣࡷ࡭ࡴࡴࠠࡱࡣࡶࡷࡪࡪ࠮ࠨᛍ"):
        for bstack11ll111llll_opy_ in bstack11l1lllllll_opy_[bstack1ll_opy_ (u"ࠧࡦࡴࡵࡳࡷࡹࠧᛎ")]:
          logger.error(bstack11ll111llll_opy_[bstack1ll_opy_ (u"ࠨ࡯ࡨࡷࡸࡧࡧࡦࠩᛏ")])
      return None, None
  except Exception as error:
    logger.error(bstack1ll_opy_ (u"ࠤࡈࡼࡨ࡫ࡰࡵ࡫ࡲࡲࠥࡽࡨࡪ࡮ࡨࠤࡨࡸࡥࡢࡶ࡬ࡲ࡬ࠦࡴࡦࡵࡷࠤࡷࡻ࡮ࠡࡨࡲࡶࠥࡈࡲࡰࡹࡶࡩࡷ࡙ࡴࡢࡥ࡮ࠤࡆࡩࡣࡦࡵࡶ࡭ࡧ࡯࡬ࡪࡶࡼࠤࡆࡻࡴࡰ࡯ࡤࡸ࡮ࡵ࡮࠻ࠢࠥᛐ") +  str(error))
    return None, None
def bstack11ll1l111l1_opy_():
  if os.getenv(bstack1ll_opy_ (u"ࠪࡆࡘࡥࡁ࠲࠳࡜ࡣࡏ࡝ࡔࠨᛑ")) is None:
    return {
        bstack1ll_opy_ (u"ࠫࡸࡺࡡࡵࡷࡶࠫᛒ"): bstack1ll_opy_ (u"ࠬ࡫ࡲࡳࡱࡵࠫᛓ"),
        bstack1ll_opy_ (u"࠭࡭ࡦࡵࡶࡥ࡬࡫ࠧᛔ"): bstack1ll_opy_ (u"ࠧࡃࡷ࡬ࡰࡩࠦࡣࡳࡧࡤࡸ࡮ࡵ࡮ࠡࡪࡤࡨࠥ࡬ࡡࡪ࡮ࡨࡨ࠳࠭ᛕ")
    }
  data = {bstack1ll_opy_ (u"ࠨࡧࡱࡨ࡙࡯࡭ࡦࠩᛖ"): bstack1l11l1111_opy_()}
  headers = {
      bstack1ll_opy_ (u"ࠩࡄࡹࡹ࡮࡯ࡳ࡫ࡽࡥࡹ࡯࡯࡯ࠩᛗ"): bstack1ll_opy_ (u"ࠪࡆࡪࡧࡲࡦࡴࠣࠫᛘ") + os.getenv(bstack1ll_opy_ (u"ࠦࡇ࡙࡟ࡂ࠳࠴࡝ࡤࡐࡗࡕࠤᛙ")),
      bstack1ll_opy_ (u"ࠬࡉ࡯࡯ࡶࡨࡲࡹ࠳ࡔࡺࡲࡨࠫᛚ"): bstack1ll_opy_ (u"࠭ࡡࡱࡲ࡯࡭ࡨࡧࡴࡪࡱࡱ࠳࡯ࡹ࡯࡯ࠩᛛ")
  }
  response = bstack1l111111_opy_(bstack1ll_opy_ (u"ࠧࡑࡗࡗࠫᛜ"), bstack11ll111l1l1_opy_ + bstack1ll_opy_ (u"ࠨ࠱ࡷࡩࡸࡺ࡟ࡳࡷࡱࡷ࠴ࡹࡴࡰࡲࠪᛝ"), data, { bstack1ll_opy_ (u"ࠩ࡫ࡩࡦࡪࡥࡳࡵࠪᛞ"): headers })
  try:
    if response.status_code == 200:
      logger.info(bstack1ll_opy_ (u"ࠥࡆࡷࡵࡷࡴࡧࡵࡗࡹࡧࡣ࡬ࠢࡄࡧࡨ࡫ࡳࡴ࡫ࡥ࡭ࡱ࡯ࡴࡺࠢࡄࡹࡹࡵ࡭ࡢࡶ࡬ࡳࡳࠦࡔࡦࡵࡷࠤࡗࡻ࡮ࠡ࡯ࡤࡶࡰ࡫ࡤࠡࡣࡶࠤࡨࡵ࡭ࡱ࡮ࡨࡸࡪࡪࠠࡢࡶࠣࠦᛟ") + bstack111l11ll1l_opy_().isoformat() + bstack1ll_opy_ (u"ࠫ࡟࠭ᛠ"))
      return {bstack1ll_opy_ (u"ࠬࡹࡴࡢࡶࡸࡷࠬᛡ"): bstack1ll_opy_ (u"࠭ࡳࡶࡥࡦࡩࡸࡹࠧᛢ"), bstack1ll_opy_ (u"ࠧ࡮ࡧࡶࡷࡦ࡭ࡥࠨᛣ"): bstack1ll_opy_ (u"ࠨࠩᛤ")}
    else:
      response.raise_for_status()
  except requests.RequestException as error:
    logger.error(bstack1ll_opy_ (u"ࠤࡈࡼࡨ࡫ࡰࡵ࡫ࡲࡲࠥࡽࡨࡪ࡮ࡨࠤࡲࡧࡲ࡬࡫ࡱ࡫ࠥࡩ࡯࡮ࡲ࡯ࡩࡹ࡯࡯࡯ࠢࡲࡪࠥࡈࡲࡰࡹࡶࡩࡷ࡙ࡴࡢࡥ࡮ࠤࡆࡩࡣࡦࡵࡶ࡭ࡧ࡯࡬ࡪࡶࡼࠤࡆࡻࡴࡰ࡯ࡤࡸ࡮ࡵ࡮ࠡࡖࡨࡷࡹࠦࡒࡶࡰ࠽ࠤࠧᛥ") + str(error))
    return {
        bstack1ll_opy_ (u"ࠪࡷࡹࡧࡴࡶࡵࠪᛦ"): bstack1ll_opy_ (u"ࠫࡪࡸࡲࡰࡴࠪᛧ"),
        bstack1ll_opy_ (u"ࠬࡳࡥࡴࡵࡤ࡫ࡪ࠭ᛨ"): str(error)
    }
def bstack11ll11l1111_opy_(bstack11ll1111l1l_opy_):
    return re.match(bstack1ll_opy_ (u"ࡸࠧ࡟࡞ࡧ࠯࠭ࡢ࠮࡝ࡦ࠮࠭ࡄࠪࠧᛩ"), bstack11ll1111l1l_opy_.strip()) is not None
def bstack11111l1l1_opy_(caps, options, desired_capabilities={}, config=None):
    try:
        if options:
          bstack11ll11lll1l_opy_ = options.to_capabilities()
        elif desired_capabilities:
          bstack11ll11lll1l_opy_ = desired_capabilities
        else:
          bstack11ll11lll1l_opy_ = {}
        bstack1ll11l11l11_opy_ = (bstack11ll11lll1l_opy_.get(bstack1ll_opy_ (u"ࠧࡱ࡮ࡤࡸ࡫ࡵࡲ࡮ࡐࡤࡱࡪ࠭ᛪ"), bstack1ll_opy_ (u"ࠨࠩ᛫")).lower() or caps.get(bstack1ll_opy_ (u"ࠩࡳࡰࡦࡺࡦࡰࡴࡰࡒࡦࡳࡥࠨ᛬"), bstack1ll_opy_ (u"ࠪࠫ᛭")).lower())
        if bstack1ll11l11l11_opy_ == bstack1ll_opy_ (u"ࠫ࡮ࡵࡳࠨᛮ"):
            return True
        if bstack1ll11l11l11_opy_ == bstack1ll_opy_ (u"ࠬࡧ࡮ࡥࡴࡲ࡭ࡩ࠭ᛯ"):
            bstack1l1llll1lll_opy_ = str(float(caps.get(bstack1ll_opy_ (u"࠭ࡰ࡭ࡣࡷࡪࡴࡸ࡭ࡗࡧࡵࡷ࡮ࡵ࡮ࠨᛰ")) or bstack11ll11lll1l_opy_.get(bstack1ll_opy_ (u"ࠧࡣࡵࡷࡥࡨࡱ࠺ࡰࡲࡷ࡭ࡴࡴࡳࠨᛱ"), {}).get(bstack1ll_opy_ (u"ࠨࡱࡶ࡚ࡪࡸࡳࡪࡱࡱࠫᛲ"),bstack1ll_opy_ (u"ࠩࠪᛳ"))))
            if bstack1ll11l11l11_opy_ == bstack1ll_opy_ (u"ࠪࡥࡳࡪࡲࡰ࡫ࡧࠫᛴ") and int(bstack1l1llll1lll_opy_.split(bstack1ll_opy_ (u"ࠫ࠳࠭ᛵ"))[0]) < float(bstack11ll11l11l1_opy_):
                logger.warning(str(bstack11ll1111111_opy_))
                return False
            return True
        bstack1l1llll1l11_opy_ = caps.get(bstack1ll_opy_ (u"ࠬࡨࡳࡵࡣࡦ࡯࠿ࡵࡰࡵ࡫ࡲࡲࡸ࠭ᛶ"), {}).get(bstack1ll_opy_ (u"࠭ࡤࡦࡸ࡬ࡧࡪࡔࡡ࡮ࡧࠪᛷ"), caps.get(bstack1ll_opy_ (u"ࠧࡥࡧࡹ࡭ࡨ࡫ࠧᛸ"), bstack1ll_opy_ (u"ࠨࠩ᛹")))
        if bstack1l1llll1l11_opy_:
            logger.warning(bstack1ll_opy_ (u"ࠤࡄࡧࡨ࡫ࡳࡴ࡫ࡥ࡭ࡱ࡯ࡴࡺࠢࡄࡹࡹࡵ࡭ࡢࡶ࡬ࡳࡳࠦࡷࡪ࡮࡯ࠤࡷࡻ࡮ࠡࡱࡱࡰࡾࠦ࡯࡯ࠢࡇࡩࡸࡱࡴࡰࡲࠣࡦࡷࡵࡷࡴࡧࡵࡷ࠳ࠨ᛺"))
            return False
        browser = caps.get(bstack1ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵࡒࡦࡳࡥࠨ᛻"), bstack1ll_opy_ (u"ࠫࠬ᛼")).lower() or bstack11ll11lll1l_opy_.get(bstack1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡔࡡ࡮ࡧࠪ᛽"), bstack1ll_opy_ (u"࠭ࠧ᛾")).lower()
        if browser != bstack1ll_opy_ (u"ࠧࡤࡪࡵࡳࡲ࡫ࠧ᛿"):
            logger.warning(bstack1ll_opy_ (u"ࠣࡃࡦࡧࡪࡹࡳࡪࡤ࡬ࡰ࡮ࡺࡹࠡࡃࡸࡸࡴࡳࡡࡵ࡫ࡲࡲࠥࡽࡩ࡭࡮ࠣࡶࡺࡴࠠࡰࡰ࡯ࡽࠥࡵ࡮ࠡࡅ࡫ࡶࡴࡳࡥࠡࡤࡵࡳࡼࡹࡥࡳࡵ࠱ࠦᜀ"))
            return False
        browser_version = caps.get(bstack1ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴ࡙ࡩࡷࡹࡩࡰࡰࠪᜁ")) or caps.get(bstack1ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵࡣࡻ࡫ࡲࡴ࡫ࡲࡲࠬᜂ")) or bstack11ll11lll1l_opy_.get(bstack1ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶ࡛࡫ࡲࡴ࡫ࡲࡲࠬᜃ")) or bstack11ll11lll1l_opy_.get(bstack1ll_opy_ (u"ࠬࡨࡳࡵࡣࡦ࡯࠿ࡵࡰࡵ࡫ࡲࡲࡸ࠭ᜄ"), {}).get(bstack1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡖࡦࡴࡶ࡭ࡴࡴࠧᜅ")) or bstack11ll11lll1l_opy_.get(bstack1ll_opy_ (u"ࠧࡣࡵࡷࡥࡨࡱ࠺ࡰࡲࡷ࡭ࡴࡴࡳࠨᜆ"), {}).get(bstack1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡡࡹࡩࡷࡹࡩࡰࡰࠪᜇ"))
        bstack1l1lllll111_opy_ = bstack11ll111111l_opy_.bstack1ll1111ll1l_opy_
        bstack11ll1l11l1l_opy_ = False
        if config is not None:
          bstack11ll1l11l1l_opy_ = bstack1ll_opy_ (u"ࠩࡷࡹࡷࡨ࡯ࡔࡥࡤࡰࡪ࠭ᜈ") in config and str(config[bstack1ll_opy_ (u"ࠪࡸࡺࡸࡢࡰࡕࡦࡥࡱ࡫ࠧᜉ")]).lower() != bstack1ll_opy_ (u"ࠫ࡫ࡧ࡬ࡴࡧࠪᜊ")
        if os.environ.get(bstack1ll_opy_ (u"ࠬࡏࡓࡠࡐࡒࡒࡤࡈࡓࡕࡃࡆࡏࡤࡏࡎࡇࡔࡄࡣࡆ࠷࠱࡚ࡡࡖࡉࡘ࡙ࡉࡐࡐࠪᜋ"), bstack1ll_opy_ (u"࠭ࠧᜌ")).lower() == bstack1ll_opy_ (u"ࠧࡵࡴࡸࡩࠬᜍ") or bstack11ll1l11l1l_opy_:
          bstack1l1lllll111_opy_ = bstack11ll111111l_opy_.bstack1ll1111l111_opy_
        if browser_version and browser_version != bstack1ll_opy_ (u"ࠨ࡮ࡤࡸࡪࡹࡴࠨᜎ") and int(browser_version.split(bstack1ll_opy_ (u"ࠩ࠱ࠫᜏ"))[0]) <= bstack1l1lllll111_opy_:
          logger.warning(bstack1ll1ll111ll_opy_ (u"ࠪࡅࡨࡩࡥࡴࡵ࡬ࡦ࡮ࡲࡩࡵࡻࠣࡅࡺࡺ࡯࡮ࡣࡷ࡭ࡴࡴࠠࡸ࡫࡯ࡰࠥࡸࡵ࡯ࠢࡲࡲࡱࡿࠠࡰࡰࠣࡇ࡭ࡸ࡯࡮ࡧࠣࡦࡷࡵࡷࡴࡧࡵࠤࡻ࡫ࡲࡴ࡫ࡲࡲࠥ࡭ࡲࡦࡣࡷࡩࡷࠦࡴࡩࡣࡱࠤࢀࡳࡩ࡯ࡡࡤ࠵࠶ࡿ࡟ࡴࡷࡳࡴࡴࡸࡴࡦࡦࡢࡧ࡭ࡸ࡯࡮ࡧࡢࡺࡪࡸࡳࡪࡱࡱࢁ࠳࠭ᜐ"))
          return False
        if not options:
          bstack1ll111l1lll_opy_ = caps.get(bstack1ll_opy_ (u"ࠫ࡬ࡵ࡯ࡨ࠼ࡦ࡬ࡷࡵ࡭ࡦࡑࡳࡸ࡮ࡵ࡮ࡴࠩᜑ")) or bstack11ll11lll1l_opy_.get(bstack1ll_opy_ (u"ࠬ࡭࡯ࡰࡩ࠽ࡧ࡭ࡸ࡯࡮ࡧࡒࡴࡹ࡯࡯࡯ࡵࠪᜒ"), {})
          if bstack1ll_opy_ (u"࠭࠭࠮ࡪࡨࡥࡩࡲࡥࡴࡵࠪᜓ") in bstack1ll111l1lll_opy_.get(bstack1ll_opy_ (u"ࠧࡢࡴࡪࡷ᜔ࠬ"), []):
              logger.warning(bstack1ll_opy_ (u"ࠣࡃࡦࡧࡪࡹࡳࡪࡤ࡬ࡰ࡮ࡺࡹࠡࡃࡸࡸࡴࡳࡡࡵ࡫ࡲࡲࠥࡽࡩ࡭࡮ࠣࡲࡴࡺࠠࡳࡷࡱࠤࡴࡴࠠ࡭ࡧࡪࡥࡨࡿࠠࡩࡧࡤࡨࡱ࡫ࡳࡴࠢࡰࡳࡩ࡫࠮ࠡࡕࡺ࡭ࡹࡩࡨࠡࡶࡲࠤࡳ࡫ࡷࠡࡪࡨࡥࡩࡲࡥࡴࡵࠣࡱࡴࡪࡥࠡࡱࡵࠤࡦࡼ࡯ࡪࡦࠣࡹࡸ࡯࡮ࡨࠢ࡫ࡩࡦࡪ࡬ࡦࡵࡶࠤࡲࡵࡤࡦ࠰᜕ࠥ"))
              return False
        return True
    except Exception as error:
        logger.debug(bstack1ll_opy_ (u"ࠤࡈࡼࡨ࡫ࡰࡵ࡫ࡲࡲࠥ࡯࡮ࠡࡸࡤࡰ࡮ࡪࡡࡵࡧࠣࡥ࠶࠷ࡹࠡࡵࡸࡴࡵࡵࡲࡵࠢ࠽ࠦ᜖") + str(error))
        return False
def set_capabilities(caps, config):
  try:
    bstack1ll1ll11lll_opy_ = config.get(bstack1ll_opy_ (u"ࠪࡥࡨࡩࡥࡴࡵ࡬ࡦ࡮ࡲࡩࡵࡻࡒࡴࡹ࡯࡯࡯ࡵࠪ᜗"), {})
    bstack1ll1ll11lll_opy_[bstack1ll_opy_ (u"ࠫࡦࡻࡴࡩࡖࡲ࡯ࡪࡴࠧ᜘")] = os.getenv(bstack1ll_opy_ (u"ࠬࡈࡓࡠࡃ࠴࠵࡞ࡥࡊࡘࡖࠪ᜙"))
    bstack11ll11l1lll_opy_ = json.loads(os.getenv(bstack1ll_opy_ (u"࠭ࡂࡓࡑ࡚ࡗࡊࡘࡓࡕࡃࡆࡏࡤ࡚ࡅࡔࡖࡢࡅࡈࡉࡅࡔࡕࡌࡆࡎࡒࡉࡕ࡛ࡢࡇࡔࡔࡆࡊࡉࡘࡖࡆ࡚ࡉࡐࡐࡢ࡝ࡒࡒࠧ᜚"), bstack1ll_opy_ (u"ࠧࡼࡿࠪ᜛"))).get(bstack1ll_opy_ (u"ࠨࡵࡦࡥࡳࡴࡥࡳࡘࡨࡶࡸ࡯࡯࡯ࠩ᜜"))
    if not config[bstack1ll_opy_ (u"ࠩࡥࡹ࡮ࡲࡤࡑࡴࡲࡨࡺࡩࡴࡎࡣࡳࠫ᜝")].get(bstack1ll_opy_ (u"ࠥࡥࡵࡶ࡟ࡢࡷࡷࡳࡲࡧࡴࡦࠤ᜞")):
      if bstack1ll_opy_ (u"ࠫࡧࡹࡴࡢࡥ࡮࠾ࡴࡶࡴࡪࡱࡱࡷࠬᜟ") in caps:
        caps[bstack1ll_opy_ (u"ࠬࡨࡳࡵࡣࡦ࡯࠿ࡵࡰࡵ࡫ࡲࡲࡸ࠭ᜠ")][bstack1ll_opy_ (u"࠭ࡡࡤࡥࡨࡷࡸ࡯ࡢࡪ࡮࡬ࡸࡾࡕࡰࡵ࡫ࡲࡲࡸ࠭ᜡ")] = bstack1ll1ll11lll_opy_
        caps[bstack1ll_opy_ (u"ࠧࡣࡵࡷࡥࡨࡱ࠺ࡰࡲࡷ࡭ࡴࡴࡳࠨᜢ")][bstack1ll_opy_ (u"ࠨࡣࡦࡧࡪࡹࡳࡪࡤ࡬ࡰ࡮ࡺࡹࡐࡲࡷ࡭ࡴࡴࡳࠨᜣ")][bstack1ll_opy_ (u"ࠩࡶࡧࡦࡴ࡮ࡦࡴ࡙ࡩࡷࡹࡩࡰࡰࠪᜤ")] = bstack11ll11l1lll_opy_
      else:
        caps[bstack1ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬࠰ࡤࡧࡨ࡫ࡳࡴ࡫ࡥ࡭ࡱ࡯ࡴࡺࡑࡳࡸ࡮ࡵ࡮ࡴࠩᜥ")] = bstack1ll1ll11lll_opy_
        caps[bstack1ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭࠱ࡥࡨࡩࡥࡴࡵ࡬ࡦ࡮ࡲࡩࡵࡻࡒࡴࡹ࡯࡯࡯ࡵࠪᜦ")][bstack1ll_opy_ (u"ࠬࡹࡣࡢࡰࡱࡩࡷ࡜ࡥࡳࡵ࡬ࡳࡳ࠭ᜧ")] = bstack11ll11l1lll_opy_
  except Exception as error:
    logger.debug(bstack1ll_opy_ (u"ࠨࡅࡹࡥࡨࡴࡹ࡯࡯࡯ࠢࡺ࡬࡮ࡲࡥࠡࡵࡨࡸࡹ࡯࡮ࡨࠢࡄࡧࡨ࡫ࡳࡴ࡫ࡥ࡭ࡱ࡯ࡴࡺࠢࡄࡹࡹࡵ࡭ࡢࡶ࡬ࡳࡳࠦࡣࡢࡲࡤࡦ࡮ࡲࡩࡵ࡫ࡨࡷ࠳ࠦࡅࡳࡴࡲࡶ࠿ࠦࠢᜨ") +  str(error))
def bstack1l11l111l1_opy_(driver, bstack11ll1l11l11_opy_):
  try:
    setattr(driver, bstack1ll_opy_ (u"ࠧࡣࡵࡷࡥࡨࡱࡁ࠲࠳ࡼࡗ࡭ࡵࡵ࡭ࡦࡖࡧࡦࡴࠧᜩ"), True)
    session = driver.session_id
    if session:
      bstack11ll1l1111l_opy_ = True
      current_url = driver.current_url
      try:
        url = urlparse(current_url)
      except Exception as e:
        bstack11ll1l1111l_opy_ = False
      bstack11ll1l1111l_opy_ = url.scheme in [bstack1ll_opy_ (u"ࠣࡪࡷࡸࡵࠨᜪ"), bstack1ll_opy_ (u"ࠤ࡫ࡸࡹࡶࡳࠣᜫ")]
      if bstack11ll1l1111l_opy_:
        if bstack11ll1l11l11_opy_:
          logger.info(bstack1ll_opy_ (u"ࠥࡗࡪࡺࡵࡱࠢࡩࡳࡷࠦࡁࡤࡥࡨࡷࡸ࡯ࡢࡪ࡮࡬ࡸࡾࠦࡴࡦࡵࡷ࡭ࡳ࡭ࠠࡩࡣࡶࠤࡸࡺࡡࡳࡶࡨࡨ࠳ࠦࡁࡶࡶࡲࡱࡦࡺࡥࠡࡶࡨࡷࡹࠦࡣࡢࡵࡨࠤࡪࡾࡥࡤࡷࡷ࡭ࡴࡴࠠࡸ࡫࡯ࡰࠥࡨࡥࡨ࡫ࡱࠤࡲࡵ࡭ࡦࡰࡷࡥࡷ࡯࡬ࡺ࠰ࠥᜬ"))
      return bstack11ll1l11l11_opy_
  except Exception as e:
    logger.error(bstack1ll_opy_ (u"ࠦࡊࡾࡣࡦࡲࡷ࡭ࡴࡴࠠࡪࡰࠣࡷࡹࡧࡲࡵ࡫ࡱ࡫ࠥࡧࡣࡤࡧࡶࡷ࡮ࡨࡩ࡭࡫ࡷࡽࠥࡧࡵࡵࡱࡰࡥࡹ࡯࡯࡯ࠢࡶࡧࡦࡴࠠࡧࡱࡵࠤࡹ࡮ࡩࡴࠢࡷࡩࡸࡺࠠࡤࡣࡶࡩ࠿ࠦࠢᜭ") + str(e))
    return False
def bstack111111l11_opy_(driver, name, path):
  try:
    bstack1l1llll1l1l_opy_ = {
        bstack1ll_opy_ (u"ࠬࡺࡨࡕࡧࡶࡸࡗࡻ࡮ࡖࡷ࡬ࡨࠬᜮ"): threading.current_thread().current_test_uuid,
        bstack1ll_opy_ (u"࠭ࡴࡩࡄࡸ࡭ࡱࡪࡕࡶ࡫ࡧࠫᜯ"): os.environ.get(bstack1ll_opy_ (u"ࠧࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡔࡆࡕࡗࡌ࡚ࡈ࡟ࡖࡗࡌࡈࠬᜰ"), bstack1ll_opy_ (u"ࠨࠩᜱ")),
        bstack1ll_opy_ (u"ࠩࡷ࡬ࡏࡽࡴࡕࡱ࡮ࡩࡳ࠭ᜲ"): os.environ.get(bstack1ll_opy_ (u"ࠪࡆࡗࡕࡗࡔࡇࡕࡗ࡙ࡇࡃࡌࡡࡗࡉࡘ࡚ࡈࡖࡄࡢࡎ࡜࡚ࠧᜳ"), bstack1ll_opy_ (u"᜴ࠫࠬ"))
    }
    bstack1ll11l11l1l_opy_ = bstack11ll1llll1_opy_.bstack1ll1111ll11_opy_(EVENTS.bstack1l1l1ll1l_opy_.value)
    logger.debug(bstack1ll_opy_ (u"ࠬࡖࡥࡳࡨࡲࡶࡲ࡯࡮ࡨࠢࡶࡧࡦࡴࠠࡣࡧࡩࡳࡷ࡫ࠠࡴࡣࡹ࡭ࡳ࡭ࠠࡳࡧࡶࡹࡱࡺࡳࠨ᜵"))
    try:
      if (bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"࠭ࡩࡴࡃࡳࡴࡆ࠷࠱ࡺࡖࡨࡷࡹ࠭᜶"), None) and bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠧࡢࡲࡳࡅ࠶࠷ࡹࡑ࡮ࡤࡸ࡫ࡵࡲ࡮ࠩ᜷"), None)):
        scripts = {bstack1ll_opy_ (u"ࠨࡵࡦࡥࡳ࠭᜸"): bstack1111l1ll1_opy_.perform_scan}
        bstack11ll1l111ll_opy_ = json.loads(scripts[bstack1ll_opy_ (u"ࠤࡶࡧࡦࡴࠢ᜹")].replace(bstack1ll_opy_ (u"ࠥࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬ࡡࡨࡼࡪࡩࡵࡵࡱࡵ࠾ࠥࠨ᜺"), bstack1ll_opy_ (u"ࠦࠧ᜻")))
        bstack11ll1l111ll_opy_[bstack1ll_opy_ (u"ࠬࡧࡲࡨࡷࡰࡩࡳࡺࡳࠨ᜼")][bstack1ll_opy_ (u"࠭࡭ࡦࡶ࡫ࡳࡩ࠭᜽")] = None
        scripts[bstack1ll_opy_ (u"ࠢࡴࡥࡤࡲࠧ᜾")] = bstack1ll_opy_ (u"ࠣࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࡟ࡦࡺࡨࡧࡺࡺ࡯ࡳ࠼ࠣࠦ᜿") + json.dumps(bstack11ll1l111ll_opy_)
        bstack1111l1ll1_opy_.bstack1l111lll_opy_(scripts)
        bstack1111l1ll1_opy_.store()
        logger.debug(driver.execute_script(bstack1111l1ll1_opy_.perform_scan))
      else:
        logger.debug(driver.execute_async_script(bstack1111l1ll1_opy_.perform_scan, {bstack1ll_opy_ (u"ࠤࡰࡩࡹ࡮࡯ࡥࠤᝀ"): name}))
      bstack11ll1llll1_opy_.end(EVENTS.bstack1l1l1ll1l_opy_.value, bstack1ll11l11l1l_opy_ + bstack1ll_opy_ (u"ࠥ࠾ࡸࡺࡡࡳࡶࠥᝁ"), bstack1ll11l11l1l_opy_ + bstack1ll_opy_ (u"ࠦ࠿࡫࡮ࡥࠤᝂ"), True, None)
    except Exception as error:
      bstack11ll1llll1_opy_.end(EVENTS.bstack1l1l1ll1l_opy_.value, bstack1ll11l11l1l_opy_ + bstack1ll_opy_ (u"ࠧࡀࡳࡵࡣࡵࡸࠧᝃ"), bstack1ll11l11l1l_opy_ + bstack1ll_opy_ (u"ࠨ࠺ࡦࡰࡧࠦᝄ"), False, str(error))
    bstack1ll11l11l1l_opy_ = bstack11ll1llll1_opy_.bstack11l1lllll11_opy_(EVENTS.bstack1ll11l1l11l_opy_.value)
    bstack11ll1llll1_opy_.mark(bstack1ll11l11l1l_opy_ + bstack1ll_opy_ (u"ࠢ࠻ࡵࡷࡥࡷࡺࠢᝅ"))
    try:
      if (bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠨ࡫ࡶࡅࡵࡶࡁ࠲࠳ࡼࡘࡪࡹࡴࠨᝆ"), None) and bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠩࡤࡴࡵࡇ࠱࠲ࡻࡓࡰࡦࡺࡦࡰࡴࡰࠫᝇ"), None)):
        scripts = {bstack1ll_opy_ (u"ࠪࡷࡨࡧ࡮ࠨᝈ"): bstack1111l1ll1_opy_.perform_scan}
        bstack11ll1l111ll_opy_ = json.loads(scripts[bstack1ll_opy_ (u"ࠦࡸࡩࡡ࡯ࠤᝉ")].replace(bstack1ll_opy_ (u"ࠧࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮ࡣࡪࡾࡥࡤࡷࡷࡳࡷࡀࠠࠣᝊ"), bstack1ll_opy_ (u"ࠨࠢᝋ")))
        bstack11ll1l111ll_opy_[bstack1ll_opy_ (u"ࠧࡢࡴࡪࡹࡲ࡫࡮ࡵࡵࠪᝌ")][bstack1ll_opy_ (u"ࠨ࡯ࡨࡸ࡭ࡵࡤࠨᝍ")] = None
        scripts[bstack1ll_opy_ (u"ࠤࡶࡧࡦࡴࠢᝎ")] = bstack1ll_opy_ (u"ࠥࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬ࡡࡨࡼࡪࡩࡵࡵࡱࡵ࠾ࠥࠨᝏ") + json.dumps(bstack11ll1l111ll_opy_)
        bstack1111l1ll1_opy_.bstack1l111lll_opy_(scripts)
        bstack1111l1ll1_opy_.store()
        logger.debug(driver.execute_script(bstack1111l1ll1_opy_.perform_scan))
      else:
        logger.debug(driver.execute_async_script(bstack1111l1ll1_opy_.bstack11ll11l1l1l_opy_, bstack1l1llll1l1l_opy_))
      bstack11ll1llll1_opy_.end(bstack1ll11l11l1l_opy_, bstack1ll11l11l1l_opy_ + bstack1ll_opy_ (u"ࠦ࠿ࡹࡴࡢࡴࡷࠦᝐ"), bstack1ll11l11l1l_opy_ + bstack1ll_opy_ (u"ࠧࡀࡥ࡯ࡦࠥᝑ"),True, None)
    except Exception as error:
      bstack11ll1llll1_opy_.end(bstack1ll11l11l1l_opy_, bstack1ll11l11l1l_opy_ + bstack1ll_opy_ (u"ࠨ࠺ࡴࡶࡤࡶࡹࠨᝒ"), bstack1ll11l11l1l_opy_ + bstack1ll_opy_ (u"ࠢ࠻ࡧࡱࡨࠧᝓ"),False, str(error))
    logger.info(bstack1ll_opy_ (u"ࠣࡃࡦࡧࡪࡹࡳࡪࡤ࡬ࡰ࡮ࡺࡹࠡࡶࡨࡷࡹ࡯࡮ࡨࠢࡩࡳࡷࠦࡴࡩ࡫ࡶࠤࡹ࡫ࡳࡵࠢࡦࡥࡸ࡫ࠠࡩࡣࡶࠤࡪࡴࡤࡦࡦ࠱ࠦ᝔"))
  except Exception as bstack1l1lllll11l_opy_:
    logger.error(bstack1ll_opy_ (u"ࠤࡄࡧࡨ࡫ࡳࡴ࡫ࡥ࡭ࡱ࡯ࡴࡺࠢࡵࡩࡸࡻ࡬ࡵࡵࠣࡧࡴࡻ࡬ࡥࠢࡱࡳࡹࠦࡢࡦࠢࡳࡶࡴࡩࡥࡴࡵࡨࡨࠥ࡬࡯ࡳࠢࡷ࡬ࡪࠦࡴࡦࡵࡷࠤࡨࡧࡳࡦ࠼ࠣࠦ᝕") + str(path) + bstack1ll_opy_ (u"ࠥࠤࡊࡸࡲࡰࡴࠣ࠾ࠧ᝖") + str(bstack1l1lllll11l_opy_))
def bstack11ll11l1l11_opy_(driver):
    caps = driver.capabilities
    if caps.get(bstack1ll_opy_ (u"ࠦࡵࡲࡡࡵࡨࡲࡶࡲࡔࡡ࡮ࡧࠥ᝗")) and str(caps.get(bstack1ll_opy_ (u"ࠧࡶ࡬ࡢࡶࡩࡳࡷࡳࡎࡢ࡯ࡨࠦ᝘"))).lower() == bstack1ll_opy_ (u"ࠨࡡ࡯ࡦࡵࡳ࡮ࡪࠢ᝙"):
        bstack1l1llll1lll_opy_ = caps.get(bstack1ll_opy_ (u"ࠢࡢࡲࡳ࡭ࡺࡳ࠺ࡱ࡮ࡤࡸ࡫ࡵࡲ࡮ࡘࡨࡶࡸ࡯࡯࡯ࠤ᝚")) or caps.get(bstack1ll_opy_ (u"ࠣࡲ࡯ࡥࡹ࡬࡯ࡳ࡯࡙ࡩࡷࡹࡩࡰࡰࠥ᝛"))
        if bstack1l1llll1lll_opy_ and int(str(bstack1l1llll1lll_opy_)) < bstack11ll11l11l1_opy_:
            return False
    return True
def bstack1l1l111lll_opy_(config):
  if bstack1ll_opy_ (u"ࠩࡤࡧࡨ࡫ࡳࡴ࡫ࡥ࡭ࡱ࡯ࡴࡺࠩ᝜") in config:
        return config[bstack1ll_opy_ (u"ࠪࡥࡨࡩࡥࡴࡵ࡬ࡦ࡮ࡲࡩࡵࡻࠪ᝝")]
  for platform in config.get(bstack1ll_opy_ (u"ࠫࡵࡲࡡࡵࡨࡲࡶࡲࡹࠧ᝞"), []):
      if bstack1ll_opy_ (u"ࠬࡧࡣࡤࡧࡶࡷ࡮ࡨࡩ࡭࡫ࡷࡽࠬ᝟") in platform:
          return platform[bstack1ll_opy_ (u"࠭ࡡࡤࡥࡨࡷࡸ࡯ࡢࡪ࡮࡬ࡸࡾ࠭ᝠ")]
  return None
def bstack1l1l1l11l1_opy_(bstack11l111111l_opy_):
  try:
    browser_name = bstack11l111111l_opy_[bstack1ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡠࡰࡤࡱࡪ࠭ᝡ")]
    browser_version = bstack11l111111l_opy_[bstack1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡡࡹࡩࡷࡹࡩࡰࡰࠪᝢ")]
    chrome_options = bstack11l111111l_opy_[bstack1ll_opy_ (u"ࠩࡦ࡬ࡷࡵ࡭ࡦࡡࡲࡴࡹ࡯࡯࡯ࡵࠪᝣ")]
    try:
        bstack11ll111ll11_opy_ = int(browser_version.split(bstack1ll_opy_ (u"ࠪ࠲ࠬᝤ"))[0])
    except ValueError as e:
        logger.error(bstack1ll_opy_ (u"ࠦࡊࡸࡲࡰࡴࠣࡻ࡭࡯࡬ࡦࠢࡦࡳࡳࡼࡥࡳࡶ࡬ࡲ࡬ࠦࡢࡳࡱࡺࡷࡪࡸࠠࡷࡧࡵࡷ࡮ࡵ࡮ࠣᝥ") + str(e))
        return False
    if not (browser_name and browser_name.lower() == bstack1ll_opy_ (u"ࠬࡩࡨࡳࡱࡰࡩࠬᝦ")):
        logger.warning(bstack1ll_opy_ (u"ࠨࡁࡤࡥࡨࡷࡸ࡯ࡢࡪ࡮࡬ࡸࡾࠦࡁࡶࡶࡲࡱࡦࡺࡩࡰࡰࠣࡻ࡮ࡲ࡬ࠡࡴࡸࡲࠥࡵ࡮࡭ࡻࠣࡳࡳࠦࡃࡩࡴࡲࡱࡪࠦࡢࡳࡱࡺࡷࡪࡸࡳ࠯ࠤᝧ"))
        return False
    if bstack11ll111ll11_opy_ < bstack11ll111111l_opy_.bstack1ll1111l111_opy_:
        logger.warning(bstack1ll1ll111ll_opy_ (u"ࠧࡂࡥࡦࡩࡸࡹࡩࡣ࡫࡯࡭ࡹࡿࠠࡂࡷࡷࡳࡲࡧࡴࡪࡱࡱࠤࡷ࡫ࡱࡶ࡫ࡵࡩࡸࠦࡃࡩࡴࡲࡱࡪࠦࡶࡦࡴࡶ࡭ࡴࡴࠠࡼࡅࡒࡒࡘ࡚ࡁࡏࡖࡖ࠲ࡒࡏࡎࡊࡏࡘࡑࡤࡔࡏࡏࡡࡅࡗ࡙ࡇࡃࡌࡡࡌࡒࡋࡘࡁࡠࡃ࠴࠵࡞ࡥࡓࡖࡒࡓࡓࡗ࡚ࡅࡅࡡࡆࡌࡗࡕࡍࡆࡡ࡙ࡉࡗ࡙ࡉࡐࡐࢀࠤࡴࡸࠠࡩ࡫ࡪ࡬ࡪࡸ࠮ࠨᝨ"))
        return False
    if chrome_options and any(bstack1ll_opy_ (u"ࠨ࠯࠰࡬ࡪࡧࡤ࡭ࡧࡶࡷࠬᝩ") in value for value in chrome_options.values() if isinstance(value, str)):
        logger.warning(bstack1ll_opy_ (u"ࠤࡄࡧࡨ࡫ࡳࡴ࡫ࡥ࡭ࡱ࡯ࡴࡺࠢࡄࡹࡹࡵ࡭ࡢࡶ࡬ࡳࡳࠦࡷࡪ࡮࡯ࠤࡳࡵࡴࠡࡴࡸࡲࠥࡵ࡮ࠡ࡮ࡨ࡫ࡦࡩࡹࠡࡪࡨࡥࡩࡲࡥࡴࡵࠣࡱࡴࡪࡥ࠯ࠢࡖࡻ࡮ࡺࡣࡩࠢࡷࡳࠥࡴࡥࡸࠢ࡫ࡩࡦࡪ࡬ࡦࡵࡶࠤࡲࡵࡤࡦࠢࡲࡶࠥࡧࡶࡰ࡫ࡧࠤࡺࡹࡩ࡯ࡩࠣ࡬ࡪࡧࡤ࡭ࡧࡶࡷࠥࡳ࡯ࡥࡧ࠱ࠦᝪ"))
        return False
    return True
  except Exception as e:
    logger.error(bstack1ll_opy_ (u"ࠥࡉࡷࡸ࡯ࡳࠢ࡬ࡲࠥࡩࡨࡦࡥ࡮࡭ࡳ࡭ࠠࡱ࡮ࡤࡸ࡫ࡵࡲ࡮ࠢࡶࡹࡵࡶ࡯ࡳࡶࠣࡪࡴࡸࠠ࡭ࡱࡦࡥࡱࠦࡃࡩࡴࡲࡱࡪࡀࠠࠣᝫ") + str(e))
    return False
def bstack11lll11111_opy_(bstack1ll1l1ll11_opy_, config):
    try:
      bstack1l1llllllll_opy_ = bstack1ll_opy_ (u"ࠫࡦࡩࡣࡦࡵࡶ࡭ࡧ࡯࡬ࡪࡶࡼࠫᝬ") in config and config[bstack1ll_opy_ (u"ࠬࡧࡣࡤࡧࡶࡷ࡮ࡨࡩ࡭࡫ࡷࡽࠬ᝭")] == True
      bstack11ll1l11l1l_opy_ = bstack1ll_opy_ (u"࠭ࡴࡶࡴࡥࡳࡘࡩࡡ࡭ࡧࠪᝮ") in config and str(config[bstack1ll_opy_ (u"ࠧࡵࡷࡵࡦࡴ࡙ࡣࡢ࡮ࡨࠫᝯ")]).lower() != bstack1ll_opy_ (u"ࠨࡨࡤࡰࡸ࡫ࠧᝰ")
      if not (bstack1l1llllllll_opy_ and (not bstack11111l1l_opy_(config) or bstack11ll1l11l1l_opy_)):
        return bstack1ll1l1ll11_opy_
      bstack11l1llll1ll_opy_ = bstack1111l1ll1_opy_.bstack11ll111l111_opy_
      if bstack11l1llll1ll_opy_ is None:
        logger.debug(bstack1ll_opy_ (u"ࠤࡊࡳࡴ࡭࡬ࡦࠢࡦ࡬ࡷࡵ࡭ࡦࠢࡲࡴࡹ࡯࡯࡯ࡵࠣࡥࡷ࡫ࠠࡏࡱࡱࡩࠧ᝱"))
        return bstack1ll1l1ll11_opy_
      bstack11l1llllll1_opy_ = int(str(bstack11ll1111l11_opy_()).split(bstack1ll_opy_ (u"ࠪ࠲ࠬᝲ"))[0])
      logger.debug(bstack1ll_opy_ (u"ࠦࡘ࡫࡬ࡦࡰ࡬ࡹࡲࠦࡶࡦࡴࡶ࡭ࡴࡴࠠࡥࡧࡷࡩࡨࡺࡥࡥ࠼ࠣࠦᝳ") + str(bstack11l1llllll1_opy_) + bstack1ll_opy_ (u"ࠧࠨ᝴"))
      if bstack11l1llllll1_opy_ == 3 and isinstance(bstack1ll1l1ll11_opy_, dict) and bstack1ll_opy_ (u"࠭ࡤࡦࡵ࡬ࡶࡪࡪ࡟ࡤࡣࡳࡥࡧ࡯࡬ࡪࡶ࡬ࡩࡸ࠭᝵") in bstack1ll1l1ll11_opy_ and bstack11l1llll1ll_opy_ is not None:
        if bstack1ll_opy_ (u"ࠧࡨࡱࡲ࡫࠿ࡩࡨࡳࡱࡰࡩࡔࡶࡴࡪࡱࡱࡷࠬ᝶") not in bstack1ll1l1ll11_opy_[bstack1ll_opy_ (u"ࠨࡦࡨࡷ࡮ࡸࡥࡥࡡࡦࡥࡵࡧࡢࡪ࡮࡬ࡸ࡮࡫ࡳࠨ᝷")]:
          bstack1ll1l1ll11_opy_[bstack1ll_opy_ (u"ࠩࡧࡩࡸ࡯ࡲࡦࡦࡢࡧࡦࡶࡡࡣ࡫࡯࡭ࡹ࡯ࡥࡴࠩ᝸")][bstack1ll_opy_ (u"ࠪ࡫ࡴࡵࡧ࠻ࡥ࡫ࡶࡴࡳࡥࡐࡲࡷ࡭ࡴࡴࡳࠨ᝹")] = {}
        if bstack1ll_opy_ (u"ࠫࡦࡸࡧࡴࠩ᝺") in bstack11l1llll1ll_opy_:
          if bstack1ll_opy_ (u"ࠬࡧࡲࡨࡵࠪ᝻") not in bstack1ll1l1ll11_opy_[bstack1ll_opy_ (u"࠭ࡤࡦࡵ࡬ࡶࡪࡪ࡟ࡤࡣࡳࡥࡧ࡯࡬ࡪࡶ࡬ࡩࡸ࠭᝼")][bstack1ll_opy_ (u"ࠧࡨࡱࡲ࡫࠿ࡩࡨࡳࡱࡰࡩࡔࡶࡴࡪࡱࡱࡷࠬ᝽")]:
            bstack1ll1l1ll11_opy_[bstack1ll_opy_ (u"ࠨࡦࡨࡷ࡮ࡸࡥࡥࡡࡦࡥࡵࡧࡢࡪ࡮࡬ࡸ࡮࡫ࡳࠨ᝾")][bstack1ll_opy_ (u"ࠩࡪࡳࡴ࡭࠺ࡤࡪࡵࡳࡲ࡫ࡏࡱࡶ࡬ࡳࡳࡹࠧ᝿")][bstack1ll_opy_ (u"ࠪࡥࡷ࡭ࡳࠨក")] = []
          for arg in bstack11l1llll1ll_opy_[bstack1ll_opy_ (u"ࠫࡦࡸࡧࡴࠩខ")]:
            if arg not in bstack1ll1l1ll11_opy_[bstack1ll_opy_ (u"ࠬࡪࡥࡴ࡫ࡵࡩࡩࡥࡣࡢࡲࡤࡦ࡮ࡲࡩࡵ࡫ࡨࡷࠬគ")][bstack1ll_opy_ (u"࠭ࡧࡰࡱࡪ࠾ࡨ࡮ࡲࡰ࡯ࡨࡓࡵࡺࡩࡰࡰࡶࠫឃ")][bstack1ll_opy_ (u"ࠧࡢࡴࡪࡷࠬង")]:
              bstack1ll1l1ll11_opy_[bstack1ll_opy_ (u"ࠨࡦࡨࡷ࡮ࡸࡥࡥࡡࡦࡥࡵࡧࡢࡪ࡮࡬ࡸ࡮࡫ࡳࠨច")][bstack1ll_opy_ (u"ࠩࡪࡳࡴ࡭࠺ࡤࡪࡵࡳࡲ࡫ࡏࡱࡶ࡬ࡳࡳࡹࠧឆ")][bstack1ll_opy_ (u"ࠪࡥࡷ࡭ࡳࠨជ")].append(arg)
        if bstack1ll_opy_ (u"ࠫࡪࡾࡴࡦࡰࡶ࡭ࡴࡴࡳࠨឈ") in bstack11l1llll1ll_opy_:
          if bstack1ll_opy_ (u"ࠬ࡫ࡸࡵࡧࡱࡷ࡮ࡵ࡮ࡴࠩញ") not in bstack1ll1l1ll11_opy_[bstack1ll_opy_ (u"࠭ࡤࡦࡵ࡬ࡶࡪࡪ࡟ࡤࡣࡳࡥࡧ࡯࡬ࡪࡶ࡬ࡩࡸ࠭ដ")][bstack1ll_opy_ (u"ࠧࡨࡱࡲ࡫࠿ࡩࡨࡳࡱࡰࡩࡔࡶࡴࡪࡱࡱࡷࠬឋ")]:
            bstack1ll1l1ll11_opy_[bstack1ll_opy_ (u"ࠨࡦࡨࡷ࡮ࡸࡥࡥࡡࡦࡥࡵࡧࡢࡪ࡮࡬ࡸ࡮࡫ࡳࠨឌ")][bstack1ll_opy_ (u"ࠩࡪࡳࡴ࡭࠺ࡤࡪࡵࡳࡲ࡫ࡏࡱࡶ࡬ࡳࡳࡹࠧឍ")][bstack1ll_opy_ (u"ࠪࡩࡽࡺࡥ࡯ࡵ࡬ࡳࡳࡹࠧណ")] = []
          for ext in bstack11l1llll1ll_opy_[bstack1ll_opy_ (u"ࠫࡪࡾࡴࡦࡰࡶ࡭ࡴࡴࡳࠨត")]:
            if ext not in bstack1ll1l1ll11_opy_[bstack1ll_opy_ (u"ࠬࡪࡥࡴ࡫ࡵࡩࡩࡥࡣࡢࡲࡤࡦ࡮ࡲࡩࡵ࡫ࡨࡷࠬថ")][bstack1ll_opy_ (u"࠭ࡧࡰࡱࡪ࠾ࡨ࡮ࡲࡰ࡯ࡨࡓࡵࡺࡩࡰࡰࡶࠫទ")][bstack1ll_opy_ (u"ࠧࡦࡺࡷࡩࡳࡹࡩࡰࡰࡶࠫធ")]:
              bstack1ll1l1ll11_opy_[bstack1ll_opy_ (u"ࠨࡦࡨࡷ࡮ࡸࡥࡥࡡࡦࡥࡵࡧࡢࡪ࡮࡬ࡸ࡮࡫ࡳࠨន")][bstack1ll_opy_ (u"ࠩࡪࡳࡴ࡭࠺ࡤࡪࡵࡳࡲ࡫ࡏࡱࡶ࡬ࡳࡳࡹࠧប")][bstack1ll_opy_ (u"ࠪࡩࡽࡺࡥ࡯ࡵ࡬ࡳࡳࡹࠧផ")].append(ext)
        if bstack1ll_opy_ (u"ࠫࡵࡸࡥࡧࡵࠪព") in bstack11l1llll1ll_opy_:
          if bstack1ll_opy_ (u"ࠬࡶࡲࡦࡨࡶࠫភ") not in bstack1ll1l1ll11_opy_[bstack1ll_opy_ (u"࠭ࡤࡦࡵ࡬ࡶࡪࡪ࡟ࡤࡣࡳࡥࡧ࡯࡬ࡪࡶ࡬ࡩࡸ࠭ម")][bstack1ll_opy_ (u"ࠧࡨࡱࡲ࡫࠿ࡩࡨࡳࡱࡰࡩࡔࡶࡴࡪࡱࡱࡷࠬយ")]:
            bstack1ll1l1ll11_opy_[bstack1ll_opy_ (u"ࠨࡦࡨࡷ࡮ࡸࡥࡥࡡࡦࡥࡵࡧࡢࡪ࡮࡬ࡸ࡮࡫ࡳࠨរ")][bstack1ll_opy_ (u"ࠩࡪࡳࡴ࡭࠺ࡤࡪࡵࡳࡲ࡫ࡏࡱࡶ࡬ࡳࡳࡹࠧល")][bstack1ll_opy_ (u"ࠪࡴࡷ࡫ࡦࡴࠩវ")] = {}
          bstack11ll1111ll1_opy_(bstack1ll1l1ll11_opy_[bstack1ll_opy_ (u"ࠫࡩ࡫ࡳࡪࡴࡨࡨࡤࡩࡡࡱࡣࡥ࡭ࡱ࡯ࡴࡪࡧࡶࠫឝ")][bstack1ll_opy_ (u"ࠬ࡭࡯ࡰࡩ࠽ࡧ࡭ࡸ࡯࡮ࡧࡒࡴࡹ࡯࡯࡯ࡵࠪឞ")][bstack1ll_opy_ (u"࠭ࡰࡳࡧࡩࡷࠬស")],
                    bstack11l1llll1ll_opy_[bstack1ll_opy_ (u"ࠧࡱࡴࡨࡪࡸ࠭ហ")])
        os.environ[bstack1ll_opy_ (u"ࠨࡋࡖࡣࡓࡕࡎࡠࡄࡖࡘࡆࡉࡋࡠࡋࡑࡊࡗࡇ࡟ࡂ࠳࠴࡝ࡤ࡙ࡅࡔࡕࡌࡓࡓ࠭ឡ")] = bstack1ll_opy_ (u"ࠩࡷࡶࡺ࡫ࠧអ")
        return bstack1ll1l1ll11_opy_
      else:
        chrome_options = None
        if isinstance(bstack1ll1l1ll11_opy_, ChromeOptions):
          chrome_options = bstack1ll1l1ll11_opy_
        elif isinstance(bstack1ll1l1ll11_opy_, dict):
          for value in bstack1ll1l1ll11_opy_.values():
            if isinstance(value, ChromeOptions):
              chrome_options = value
              break
        if chrome_options is None:
          chrome_options = ChromeOptions()
          if isinstance(bstack1ll1l1ll11_opy_, dict):
            bstack1ll1l1ll11_opy_[bstack1ll_opy_ (u"ࠪࡳࡵࡺࡩࡰࡰࡶࠫឣ")] = chrome_options
          else:
            bstack1ll1l1ll11_opy_ = chrome_options
        if bstack11l1llll1ll_opy_ is not None:
          if bstack1ll_opy_ (u"ࠫࡦࡸࡧࡴࠩឤ") in bstack11l1llll1ll_opy_:
                bstack11ll111ll1l_opy_ = chrome_options.arguments or []
                new_args = bstack11l1llll1ll_opy_[bstack1ll_opy_ (u"ࠬࡧࡲࡨࡵࠪឥ")]
                for arg in new_args:
                    if arg not in bstack11ll111ll1l_opy_:
                        chrome_options.add_argument(arg)
          if bstack1ll_opy_ (u"࠭ࡥࡹࡶࡨࡲࡸ࡯࡯࡯ࡵࠪឦ") in bstack11l1llll1ll_opy_:
                existing_extensions = chrome_options.experimental_options.get(bstack1ll_opy_ (u"ࠧࡦࡺࡷࡩࡳࡹࡩࡰࡰࡶࠫឧ"), [])
                bstack11ll11ll1l1_opy_ = bstack11l1llll1ll_opy_[bstack1ll_opy_ (u"ࠨࡧࡻࡸࡪࡴࡳࡪࡱࡱࡷࠬឨ")]
                for extension in bstack11ll11ll1l1_opy_:
                    if extension not in existing_extensions:
                        chrome_options.add_encoded_extension(extension)
          if bstack1ll_opy_ (u"ࠩࡳࡶࡪ࡬ࡳࠨឩ") in bstack11l1llll1ll_opy_:
                bstack11ll1111lll_opy_ = chrome_options.experimental_options.get(bstack1ll_opy_ (u"ࠪࡴࡷ࡫ࡦࡴࠩឪ"), {})
                bstack11l1lllll1l_opy_ = bstack11l1llll1ll_opy_[bstack1ll_opy_ (u"ࠫࡵࡸࡥࡧࡵࠪឫ")]
                bstack11ll1111ll1_opy_(bstack11ll1111lll_opy_, bstack11l1lllll1l_opy_)
                chrome_options.add_experimental_option(bstack1ll_opy_ (u"ࠬࡶࡲࡦࡨࡶࠫឬ"), bstack11ll1111lll_opy_)
        os.environ[bstack1ll_opy_ (u"࠭ࡉࡔࡡࡑࡓࡓࡥࡂࡔࡖࡄࡇࡐࡥࡉࡏࡈࡕࡅࡤࡇ࠱࠲࡛ࡢࡗࡊ࡙ࡓࡊࡑࡑࠫឭ")] = bstack1ll_opy_ (u"ࠧࡵࡴࡸࡩࠬឮ")
        return bstack1ll1l1ll11_opy_
    except Exception as e:
      logger.error(bstack1ll_opy_ (u"ࠣࡇࡵࡶࡴࡸࠠࡸࡪ࡬ࡰࡪࠦࡡࡥࡦ࡬ࡲ࡬ࠦ࡮ࡰࡰ࠰ࡆࡘࠦࡩ࡯ࡨࡵࡥࠥࡧ࠱࠲ࡻࠣࡧ࡭ࡸ࡯࡮ࡧࠣࡳࡵࡺࡩࡰࡰࡶ࠾ࠥࠨឯ") + str(e))
      return bstack1ll1l1ll11_opy_