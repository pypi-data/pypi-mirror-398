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
import atexit
import shlex
import signal
import yaml
import socket
import datetime
import string
import random
import collections.abc
import traceback
import copy
import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import json
from packaging import version
from browserstack.local import Local
from urllib.parse import urlparse
from dotenv import load_dotenv
from browserstack_sdk.bstack1ll11l1l1_opy_ import bstack1l1lll111l_opy_
from browserstack_sdk.bstack1l11l11l1_opy_ import *
import time
import requests
from bstack_utils.constants import EVENTS, STAGE, bstack1l11ll111_opy_
from bstack_utils.messages import bstack111ll1llll_opy_, bstack11l1l111_opy_, bstack11ll1l111_opy_, bstack11llll1ll1_opy_, bstack1lll1ll11_opy_, bstack1ll1l1l1_opy_
from bstack_utils.measure import measure
from bstack_utils.bstack11l1l1lll1_opy_ import get_logger
from bstack_utils.helper import bstack11ll11llll_opy_
from browserstack_sdk.bstack1l1111lll_opy_ import bstack111ll1l1l_opy_
logger = get_logger(__name__)
def bstack11l1l11lll_opy_():
  global CONFIG
  headers = {
        bstack1ll_opy_ (u"ࠪࡇࡴࡴࡴࡦࡰࡷ࠱ࡹࡿࡰࡦࠩࡶ"): bstack1ll_opy_ (u"ࠫࡦࡶࡰ࡭࡫ࡦࡥࡹ࡯࡯࡯࠱࡭ࡷࡴࡴࠧࡷ"),
      }
  proxies = bstack11ll11llll_opy_(CONFIG, bstack1l11ll111_opy_)
  try:
    response = requests.get(bstack1l11ll111_opy_, headers=headers, proxies=proxies, timeout=5)
    if response.json():
      bstack1lll1l1ll1_opy_ = response.json()[bstack1ll_opy_ (u"ࠬ࡮ࡵࡣࡵࠪࡸ")]
      logger.debug(bstack111ll1llll_opy_.format(response.json()))
      return bstack1lll1l1ll1_opy_
    else:
      logger.debug(bstack11l1l111_opy_.format(bstack1ll_opy_ (u"ࠨࡒࡦࡵࡳࡳࡳࡹࡥࠡࡌࡖࡓࡓࠦࡰࡢࡴࡶࡩࠥ࡫ࡲࡳࡱࡵࠤࠧࡹ")))
  except Exception as e:
    logger.debug(bstack11l1l111_opy_.format(e))
def bstack1ll1lll11_opy_(hub_url):
  global CONFIG
  url = bstack1ll_opy_ (u"ࠢࡩࡶࡷࡴࡸࡀ࠯࠰ࠤࡺ")+  hub_url + bstack1ll_opy_ (u"ࠣ࠱ࡦ࡬ࡪࡩ࡫ࠣࡻ")
  headers = {
        bstack1ll_opy_ (u"ࠩࡆࡳࡳࡺࡥ࡯ࡶ࠰ࡸࡾࡶࡥࠨࡼ"): bstack1ll_opy_ (u"ࠪࡥࡵࡶ࡬ࡪࡥࡤࡸ࡮ࡵ࡮࠰࡬ࡶࡳࡳ࠭ࡽ"),
      }
  proxies = bstack11ll11llll_opy_(CONFIG, url)
  try:
    start_time = time.perf_counter()
    requests.get(url, headers=headers, proxies=proxies, timeout=5)
    latency = time.perf_counter() - start_time
    logger.debug(bstack11ll1l111_opy_.format(hub_url, latency))
    return dict(hub_url=hub_url, latency=latency)
  except Exception as e:
    logger.debug(bstack11llll1ll1_opy_.format(hub_url, e))
@measure(event_name=EVENTS.bstack1l111l11l1_opy_, stage=STAGE.bstack1l1lll1ll1_opy_)
def bstack1lllll111l_opy_():
  try:
    global bstack1ll111lll_opy_
    global CONFIG
    if bstack1ll_opy_ (u"ࠫ࡭ࡻࡢࡓࡧࡪ࡭ࡴࡴࠧࡾ") in CONFIG and CONFIG[bstack1ll_opy_ (u"ࠬ࡮ࡵࡣࡔࡨ࡫࡮ࡵ࡮ࠨࡿ")]:
      from bstack_utils.constants import bstack11lll1lll1_opy_
      bstack1111ll111_opy_ = CONFIG[bstack1ll_opy_ (u"࠭ࡨࡶࡤࡕࡩ࡬࡯࡯࡯ࠩࢀ")]
      if bstack1111ll111_opy_ in bstack11lll1lll1_opy_:
        bstack1ll111lll_opy_ = bstack11lll1lll1_opy_[bstack1111ll111_opy_]
        logger.debug(bstack1lll1ll11_opy_.format(bstack1ll111lll_opy_))
        return
      else:
        logger.debug(bstack1ll_opy_ (u"ࠢࡉࡷࡥࠤࡰ࡫ࡹࠡࠩࡾࢁࠬࠦ࡮ࡰࡶࠣࡪࡴࡻ࡮ࡥࠢ࡬ࡲࠥࡎࡕࡃࡡࡘࡖࡑࡥࡍࡂࡒ࠯ࠤ࡫ࡧ࡬࡭࡫ࡱ࡫ࠥࡨࡡࡤ࡭ࠣࡸࡴࠦ࡯ࡱࡶ࡬ࡱࡦࡲࠠࡩࡷࡥࠤࡩ࡫ࡴࡦࡥࡷ࡭ࡴࡴࠢࢁ").format(bstack1111ll111_opy_))
    bstack1lll1l1ll1_opy_ = bstack11l1l11lll_opy_()
    bstack1l111llll_opy_ = []
    results = []
    for bstack11l11l11_opy_ in bstack1lll1l1ll1_opy_:
      bstack1l111llll_opy_.append(bstack111ll1l1l_opy_(target=bstack1ll1lll11_opy_,args=(bstack11l11l11_opy_,)))
    for t in bstack1l111llll_opy_:
      t.start()
    for t in bstack1l111llll_opy_:
      results.append(t.join())
    bstack1lllllll1_opy_ = {}
    for item in results:
      hub_url = item[bstack1ll_opy_ (u"ࠨࡪࡸࡦࡤࡻࡲ࡭ࠩࢂ")]
      latency = item[bstack1ll_opy_ (u"ࠩ࡯ࡥࡹ࡫࡮ࡤࡻࠪࢃ")]
      bstack1lllllll1_opy_[hub_url] = latency
    bstack1ll1l11ll1_opy_ = min(bstack1lllllll1_opy_, key= lambda x: bstack1lllllll1_opy_[x])
    bstack1ll111lll_opy_ = bstack1ll1l11ll1_opy_
    logger.debug(bstack1lll1ll11_opy_.format(bstack1ll1l11ll1_opy_))
  except Exception as e:
    logger.debug(bstack1ll1l1l1_opy_.format(e))
from browserstack_sdk.bstack11ll1ll111_opy_ import *
from browserstack_sdk.bstack1l1111lll_opy_ import *
from browserstack_sdk.bstack1111111l_opy_ import *
import logging
import requests
from bstack_utils.constants import *
from bstack_utils.bstack11l1l1lll1_opy_ import get_logger
from bstack_utils.measure import measure
logger = get_logger(__name__)
@measure(event_name=EVENTS.bstack111l1lll_opy_, stage=STAGE.bstack1l1lll1ll1_opy_)
def bstack1111ll1l_opy_():
    global bstack1ll111lll_opy_
    try:
        bstack1l11111l11_opy_ = bstack11l1lllll1_opy_()
        bstack11l11ll11l_opy_(bstack1l11111l11_opy_)
        hub_url = bstack1l11111l11_opy_.get(bstack1ll_opy_ (u"ࠥࡹࡷࡲࠢࢄ"), bstack1ll_opy_ (u"ࠦࠧࢅ"))
        if hub_url.endswith(bstack1ll_opy_ (u"ࠬ࠵ࡷࡥ࠱࡫ࡹࡧ࠭ࢆ")):
            hub_url = hub_url.rsplit(bstack1ll_opy_ (u"࠭࠯ࡸࡦ࠲࡬ࡺࡨࠧࢇ"), 1)[0]
        if hub_url.startswith(bstack1ll_opy_ (u"ࠧࡩࡶࡷࡴ࠿࠵࠯ࠨ࢈")):
            hub_url = hub_url[7:]
        elif hub_url.startswith(bstack1ll_opy_ (u"ࠨࡪࡷࡸࡵࡹ࠺࠰࠱ࠪࢉ")):
            hub_url = hub_url[8:]
        bstack1ll111lll_opy_ = hub_url
    except Exception as e:
        raise RuntimeError(e)
def bstack11l1lllll1_opy_():
    global CONFIG
    bstack1l1ll1llll_opy_ = CONFIG.get(bstack1ll_opy_ (u"ࠩࡷࡹࡷࡨ࡯ࡔࡥࡤࡰࡪࡕࡰࡵ࡫ࡲࡲࡸ࠭ࢊ"), {}).get(bstack1ll_opy_ (u"ࠪ࡫ࡷ࡯ࡤࡏࡣࡰࡩࠬࢋ"), bstack1ll_opy_ (u"ࠫࡓࡕ࡟ࡈࡔࡌࡈࡤࡔࡁࡎࡇࡢࡔࡆ࡙ࡓࡆࡆࠪࢌ"))
    if not isinstance(bstack1l1ll1llll_opy_, str):
        raise ValueError(bstack1ll_opy_ (u"ࠧࡇࡔࡔࠢ࠽ࠤࡌࡸࡩࡥࠢࡱࡥࡲ࡫ࠠ࡮ࡷࡶࡸࠥࡨࡥࠡࡣࠣࡺࡦࡲࡩࡥࠢࡶࡸࡷ࡯࡮ࡨࠤࢍ"))
    try:
        bstack1l11111l11_opy_ = bstack11lllll11l_opy_(bstack1l1ll1llll_opy_)
        return bstack1l11111l11_opy_
    except Exception as e:
        logger.error(bstack1ll_opy_ (u"ࠨࡁࡕࡕࠣ࠾ࠥࡋࡲࡳࡱࡵࠤ࡮ࡴࠠࡨࡧࡷࡸ࡮ࡴࡧࠡࡩࡵ࡭ࡩࠦࡤࡦࡶࡤ࡭ࡱࡹࠠ࠻ࠢࡾࢁࠧࢎ").format(str(e)))
        return {}
def bstack11lllll11l_opy_(bstack1l1ll1llll_opy_):
    global CONFIG
    try:
        if not CONFIG[bstack1ll_opy_ (u"ࠧࡶࡵࡨࡶࡓࡧ࡭ࡦࠩ࢏")] or not CONFIG[bstack1ll_opy_ (u"ࠨࡣࡦࡧࡪࡹࡳࡌࡧࡼࠫ࢐")]:
            raise ValueError(bstack1ll_opy_ (u"ࠤࡐ࡭ࡸࡹࡩ࡯ࡩࠣࡆࡷࡵࡷࡴࡧࡵࡗࡹࡧࡣ࡬ࠢࡸࡷࡪࡸ࡮ࡢ࡯ࡨࠤࡴࡸࠠࡢࡥࡦࡩࡸࡹࠠ࡬ࡧࡼࠦ࢑"))
        url = bstack11l1ll1lll_opy_ + bstack1l1ll1llll_opy_
        auth = (CONFIG[bstack1ll_opy_ (u"ࠪࡹࡸ࡫ࡲࡏࡣࡰࡩࠬ࢒")], CONFIG[bstack1ll_opy_ (u"ࠫࡦࡩࡣࡦࡵࡶࡏࡪࡿࠧ࢓")])
        response = requests.get(url, auth=auth)
        if response.status_code == 200 and response.text:
            bstack111l1l1ll_opy_ = json.loads(response.text)
            return bstack111l1l1ll_opy_
    except ValueError as ve:
        logger.error(bstack1ll_opy_ (u"ࠧࡇࡔࡔࠢ࠽ࠤࡊࡸࡲࡰࡴࠣ࡭ࡳࠦࡦࡦࡶࡦ࡬࡮ࡴࡧࠡࡩࡵ࡭ࡩࠦࡤࡦࡶࡤ࡭ࡱࡹࠠ࠻ࠢࡾࢁࠧ࢔").format(str(ve)))
        raise ValueError(ve)
    except Exception as e:
        logger.error(bstack1ll_opy_ (u"ࠨࡁࡕࡕࠣ࠾ࠥࡋࡲࡳࡱࡵࠤ࡮ࡴࠠࡧࡧࡷࡧ࡭࡯࡮ࡨࠢࡪࡶ࡮ࡪࠠࡥࡧࡷࡥ࡮ࡲࡳࠡ࠼ࠣࡿࢂࠨ࢕").format(str(e)))
        raise RuntimeError(e)
    return {}
def bstack11l11ll11l_opy_(bstack1ll11111l1_opy_):
    global CONFIG
    if bstack1ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰࡒ࡯ࡤࡣ࡯ࠫ࢖") not in CONFIG or str(CONFIG[bstack1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱࡌࡰࡥࡤࡰࠬࢗ")]).lower() == bstack1ll_opy_ (u"ࠩࡩࡥࡱࡹࡥࠨ࢘"):
        CONFIG[bstack1ll_opy_ (u"ࠪࡰࡴࡩࡡ࡭࢙ࠩ")] = False
    elif bstack1ll_opy_ (u"ࠫ࡮ࡹࡔࡳ࡫ࡤࡰࡌࡸࡩࡥ࢚ࠩ") in bstack1ll11111l1_opy_:
        bstack11l1llll11_opy_ = CONFIG.get(bstack1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷ࡙ࡴࡢࡥ࡮ࡐࡴࡩࡡ࡭ࡑࡳࡸ࡮ࡵ࡮ࡴ࢛ࠩ"), {})
        logger.debug(bstack1ll_opy_ (u"ࠨࡁࡕࡕࠣ࠾ࠥࡋࡸࡪࡵࡷ࡭ࡳ࡭ࠠ࡭ࡱࡦࡥࡱࠦ࡯ࡱࡶ࡬ࡳࡳࡹ࠺ࠡࠧࡶࠦ࢜"), bstack11l1llll11_opy_)
        bstack11l111l111_opy_ = bstack1ll11111l1_opy_.get(bstack1ll_opy_ (u"ࠢࡤࡷࡶࡸࡴࡳࡒࡦࡲࡨࡥࡹ࡫ࡲࡴࠤ࢝"), [])
        bstack1llll1l1l_opy_ = bstack1ll_opy_ (u"ࠣ࠮ࠥ࢞").join(bstack11l111l111_opy_)
        logger.debug(bstack1ll_opy_ (u"ࠤࡄࡘࡘࠦ࠺ࠡࡅࡸࡷࡹࡵ࡭ࠡࡴࡨࡴࡪࡧࡴࡦࡴࠣࡷࡹࡸࡩ࡯ࡩ࠽ࠤࠪࡹࠢ࢟"), bstack1llll1l1l_opy_)
        bstack1lllll1l1_opy_ = {
            bstack1ll_opy_ (u"ࠥࡰࡴࡩࡡ࡭ࡋࡧࡩࡳࡺࡩࡧ࡫ࡨࡶࠧࢠ"): bstack1ll_opy_ (u"ࠦࡦࡺࡳ࠮ࡴࡨࡴࡪࡧࡴࡦࡴࠥࢡ"),
            bstack1ll_opy_ (u"ࠧ࡬࡯ࡳࡥࡨࡐࡴࡩࡡ࡭ࠤࢢ"): bstack1ll_opy_ (u"ࠨࡴࡳࡷࡨࠦࢣ"),
            bstack1ll_opy_ (u"ࠢࡤࡷࡶࡸࡴࡳ࠭ࡳࡧࡳࡩࡦࡺࡥࡳࠤࢤ"): bstack1llll1l1l_opy_
        }
        bstack11l1llll11_opy_.update(bstack1lllll1l1_opy_)
        logger.debug(bstack1ll_opy_ (u"ࠣࡃࡗࡗࠥࡀࠠࡖࡲࡧࡥࡹ࡫ࡤࠡ࡮ࡲࡧࡦࡲࠠࡰࡲࡷ࡭ࡴࡴࡳ࠻ࠢࠨࡷࠧࢥ"), bstack11l1llll11_opy_)
        CONFIG[bstack1ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡖࡸࡦࡩ࡫ࡍࡱࡦࡥࡱࡕࡰࡵ࡫ࡲࡲࡸ࠭ࢦ")] = bstack11l1llll11_opy_
        logger.debug(bstack1ll_opy_ (u"ࠥࡅ࡙࡙ࠠ࠻ࠢࡉ࡭ࡳࡧ࡬ࠡࡅࡒࡒࡋࡏࡇ࠻ࠢࠨࡷࠧࢧ"), CONFIG)
def bstack11lll11ll1_opy_():
    bstack1l11111l11_opy_ = bstack11l1lllll1_opy_()
    if not bstack1l11111l11_opy_[bstack1ll_opy_ (u"ࠫࡵࡲࡡࡺࡹࡵ࡭࡬࡮ࡴࡖࡴ࡯ࠫࢨ")]:
      raise ValueError(bstack1ll_opy_ (u"ࠧࡶ࡬ࡢࡻࡺࡶ࡮࡭ࡨࡵࡗࡵࡰࠥ࡯ࡳࠡ࡯࡬ࡷࡸ࡯࡮ࡨࠢࡩࡶࡴࡳࠠࡨࡴ࡬ࡨࠥࡪࡥࡵࡣ࡬ࡰࡸ࠴ࠢࢩ"))
    return bstack1l11111l11_opy_[bstack1ll_opy_ (u"࠭ࡰ࡭ࡣࡼࡻࡷ࡯ࡧࡩࡶࡘࡶࡱ࠭ࢪ")] + bstack1ll_opy_ (u"ࠧࡀࡥࡤࡴࡸࡃࠧࢫ")
@measure(event_name=EVENTS.bstack111l1l11_opy_, stage=STAGE.bstack1l1lll1ll1_opy_)
def bstack11l1l1l111_opy_() -> list:
    global CONFIG
    result = []
    if CONFIG:
        auth = (CONFIG[bstack1ll_opy_ (u"ࠨࡷࡶࡩࡷࡔࡡ࡮ࡧࠪࢬ")], CONFIG[bstack1ll_opy_ (u"ࠩࡤࡧࡨ࡫ࡳࡴࡍࡨࡽࠬࢭ")])
        url = bstack1l11l1ll_opy_
        logger.debug(bstack1ll_opy_ (u"ࠥࡅࡹࡺࡥ࡮ࡲࡷ࡭ࡳ࡭ࠠࡵࡱࠣࡪࡪࡺࡣࡩࠢࡥࡹ࡮ࡲࡤࡴࠢࡩࡶࡴࡳࠠࡃࡴࡲࡻࡸ࡫ࡲࡔࡶࡤࡧࡰࠦࡔࡶࡴࡥࡳࡘࡩࡡ࡭ࡧࠣࡅࡕࡏࠢࢮ"))
        try:
            response = requests.get(url, auth=auth, headers={bstack1ll_opy_ (u"ࠦࡈࡵ࡮ࡵࡧࡱࡸ࠲࡚ࡹࡱࡧࠥࢯ"): bstack1ll_opy_ (u"ࠧࡧࡰࡱ࡮࡬ࡧࡦࡺࡩࡰࡰ࠲࡮ࡸࡵ࡮ࠣࢰ")})
            if response.status_code == 200:
                bstack1111llll1_opy_ = json.loads(response.text)
                bstack1lll11l111_opy_ = bstack1111llll1_opy_.get(bstack1ll_opy_ (u"࠭ࡢࡶ࡫࡯ࡨࡸ࠭ࢱ"), [])
                if bstack1lll11l111_opy_:
                    bstack1ll1l1ll1_opy_ = bstack1lll11l111_opy_[0]
                    build_hashed_id = bstack1ll1l1ll1_opy_.get(bstack1ll_opy_ (u"ࠧࡩࡣࡶ࡬ࡪࡪ࡟ࡪࡦࠪࢲ"))
                    bstack1l111lll1_opy_ = bstack1l1l1l1111_opy_ + build_hashed_id
                    result.extend([build_hashed_id, bstack1l111lll1_opy_])
                    logger.info(bstack1l1lllll11_opy_.format(bstack1l111lll1_opy_))
                    bstack11ll1lllll_opy_ = CONFIG[bstack1ll_opy_ (u"ࠨࡤࡸ࡭ࡱࡪࡎࡢ࡯ࡨࠫࢳ")]
                    if bstack1ll_opy_ (u"ࠩࡥࡹ࡮ࡲࡤࡊࡦࡨࡲࡹ࡯ࡦࡪࡧࡵࠫࢴ") in CONFIG:
                      bstack11ll1lllll_opy_ += bstack1ll_opy_ (u"ࠪࠤࠬࢵ") + CONFIG[bstack1ll_opy_ (u"ࠫࡧࡻࡩ࡭ࡦࡌࡨࡪࡴࡴࡪࡨ࡬ࡩࡷ࠭ࢶ")]
                    if bstack11ll1lllll_opy_ != bstack1ll1l1ll1_opy_.get(bstack1ll_opy_ (u"ࠬࡴࡡ࡮ࡧࠪࢷ")):
                      logger.debug(bstack11111l1ll_opy_.format(bstack1ll1l1ll1_opy_.get(bstack1ll_opy_ (u"࠭࡮ࡢ࡯ࡨࠫࢸ")), bstack11ll1lllll_opy_))
                    return result
                else:
                    logger.debug(bstack1ll_opy_ (u"ࠢࡂࡖࡖࠤ࠿ࠦࡎࡰࠢࡥࡹ࡮ࡲࡤࡴࠢࡩࡳࡺࡴࡤࠡ࡫ࡱࠤࡹ࡮ࡥࠡࡴࡨࡷࡵࡵ࡮ࡴࡧ࠱ࠦࢹ"))
            else:
                logger.debug(bstack1ll_opy_ (u"ࠣࡃࡗࡗࠥࡀࠠࡇࡣ࡬ࡰࡪࡪࠠࡵࡱࠣࡪࡪࡺࡣࡩࠢࡥࡹ࡮ࡲࡤࡴ࠰ࠥࢺ"))
        except Exception as e:
            logger.error(bstack1ll_opy_ (u"ࠤࡄࡘࡘࠦ࠺ࠡࡇࡵࡶࡴࡸࠠࡪࡰࠣ࡫ࡪࡺࡴࡪࡰࡪࠤࡧࡻࡩ࡭ࡦࡶࠤ࠿ࠦࡻࡾࠤࢻ").format(str(e)))
    else:
        logger.debug(bstack1ll_opy_ (u"ࠥࡅ࡙࡙ࠠ࠻ࠢࡆࡓࡓࡌࡉࡈࠢ࡬ࡷࠥࡴ࡯ࡵࠢࡶࡩࡹ࠴ࠠࡖࡰࡤࡦࡱ࡫ࠠࡵࡱࠣࡪࡪࡺࡣࡩࠢࡥࡹ࡮ࡲࡤࡴ࠰ࠥࢼ"))
    return [None, None]
from browserstack_sdk.sdk_cli.cli import cli
from browserstack_sdk.sdk_cli.bstack111lll1l_opy_ import bstack111lll1l_opy_, bstack1lll1lll_opy_, bstack11ll1l1l1_opy_, bstack11ll111l11_opy_
from bstack_utils.measure import bstack11ll1llll1_opy_
from bstack_utils.measure import measure
from bstack_utils.percy import *
from bstack_utils.percy_sdk import PercySDK
from bstack_utils.bstack1l1l1l1l11_opy_ import bstack1l1lll11l1_opy_
from bstack_utils.messages import *
from bstack_utils import bstack11l1l1lll1_opy_
from bstack_utils.constants import *
from bstack_utils.helper import bstack1ll1l111_opy_, bstack1l111111_opy_, bstack11l1111l1_opy_, bstack1l11l11l_opy_, \
  bstack11111l1l_opy_, \
  Notset, bstack1l1111l11l_opy_, \
  bstack1l11lll1ll_opy_, bstack1l1l1l1ll1_opy_, bstack1ll111l1_opy_, bstack1ll1ll1l_opy_, bstack1ll1l1l1ll_opy_, bstack11ll1l11l1_opy_, \
  bstack1111l1l1l_opy_, \
  bstack1l1lll11_opy_, bstack1ll11111ll_opy_, bstack1l11l1lll1_opy_, bstack1ll1l11111_opy_, \
  bstack1l1lll1l_opy_, bstack11l111ll1l_opy_, bstack11l11lllll_opy_, bstack111ll1l1_opy_, bstack11111l111_opy_
from bstack_utils.bstack1llllllll_opy_ import bstack1l1lll11ll_opy_
from bstack_utils.bstack11111111_opy_ import bstack111111l1_opy_, bstack11ll1111_opy_
from bstack_utils.bstack1l1llll1l_opy_ import bstack111l1ll1_opy_
from bstack_utils.bstack11l1llll_opy_ import bstack11ll11111l_opy_, bstack1l111111ll_opy_
from bstack_utils.bstack1111l1ll1_opy_ import bstack1111l1ll1_opy_
from bstack_utils.bstack11l1l1l1l_opy_ import bstack11l1l11l1_opy_
from bstack_utils.proxy import bstack1ll1ll11l_opy_, bstack11ll11llll_opy_, bstack1ll11ll11l_opy_, bstack111l1l11l_opy_
from bstack_utils.bstack1l111ll1l1_opy_ import bstack1l1111l1l1_opy_, bstack1lll1l1l1l_opy_
import bstack_utils.bstack1ll111ll1_opy_ as bstack1ll1l1l1l_opy_
import bstack_utils.bstack11l1111ll1_opy_ as bstack11l1l1111_opy_
from browserstack_sdk.sdk_cli.cli import cli
from browserstack_sdk.sdk_cli.utils.bstack1l1111ll11_opy_ import bstack1l11l11ll_opy_
from bstack_utils.bstack1l11l1lll_opy_ import bstack11llll11l1_opy_
from bstack_utils.bstack1l1ll1111l_opy_ import bstack1lll1111l1_opy_
if os.getenv(bstack1ll_opy_ (u"ࠫࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡇࡑࡏ࡟ࡉࡑࡒࡏࡘ࠭ࢽ")):
  cli.bstack1lll11111l_opy_()
else:
  os.environ[bstack1ll_opy_ (u"ࠬࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣࡈࡒࡉࡠࡊࡒࡓࡐ࡙ࠧࢾ")] = bstack1ll_opy_ (u"࠭ࡴࡳࡷࡨࠫࢿ")
bstack11l11lll1_opy_ = bstack1ll_opy_ (u"ࠧࠡࠢ࠲࠮ࠥࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾ࠢ࠭࠳ࡡࡴࠠࠡ࡫ࡩࠬࡵࡧࡧࡦࠢࡀࡁࡂࠦࡶࡰ࡫ࡧࠤ࠵࠯ࠠࡼ࡞ࡱࠤࠥࠦࡴࡳࡻࡾࡠࡳࠦࡣࡰࡰࡶࡸࠥ࡬ࡳࠡ࠿ࠣࡶࡪࡷࡵࡪࡴࡨࠬࡡ࠭ࡦࡴ࡞ࠪ࠭ࡀࡢ࡮ࠡࠢࠣࠤࠥ࡬ࡳ࠯ࡣࡳࡴࡪࡴࡤࡇ࡫࡯ࡩࡘࡿ࡮ࡤࠪࡥࡷࡹࡧࡣ࡬ࡡࡳࡥࡹ࡮ࠬࠡࡌࡖࡓࡓ࠴ࡳࡵࡴ࡬ࡲ࡬࡯ࡦࡺࠪࡳࡣ࡮ࡴࡤࡦࡺࠬࠤ࠰ࠦࠢ࠻ࠤࠣ࠯ࠥࡐࡓࡐࡐ࠱ࡷࡹࡸࡩ࡯ࡩ࡬ࡪࡾ࠮ࡊࡔࡑࡑ࠲ࡵࡧࡲࡴࡧࠫࠬࡦࡽࡡࡪࡶࠣࡲࡪࡽࡐࡢࡩࡨ࠶࠳࡫ࡶࡢ࡮ࡸࡥࡹ࡫ࠨࠣࠪࠬࠤࡂࡄࠠࡼࡿࠥ࠰ࠥࡢࠧࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰࡥࡥࡹࡧࡦࡹࡹࡵࡲ࠻ࠢࡾࠦࡦࡩࡴࡪࡱࡱࠦ࠿ࠦࠢࡨࡧࡷࡗࡪࡹࡳࡪࡱࡱࡈࡪࡺࡡࡪ࡮ࡶࠦࢂࡢࠧࠪࠫࠬ࡟ࠧ࡮ࡡࡴࡪࡨࡨࡤ࡯ࡤࠣ࡟ࠬࠤ࠰ࠦࠢ࠭࡞࡟ࡲࠧ࠯࡜࡯ࠢࠣࠤࠥࢃࡣࡢࡶࡦ࡬࠭࡫ࡸࠪࡽ࡟ࡲࠥࠦࠠࠡࡿ࡟ࡲࠥࠦࡽ࡝ࡰࠣࠤ࠴࠰ࠠ࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࠤ࠯࠵ࠧࣀ")
bstack1l111111l_opy_ = bstack1ll_opy_ (u"ࠨ࡞ࡱ࠳࠯ࠦ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࠣ࠮࠴ࡢ࡮ࡤࡱࡱࡷࡹࠦࡢࡴࡶࡤࡧࡰࡥࡰࡢࡶ࡫ࠤࡂࠦࡰࡳࡱࡦࡩࡸࡹ࠮ࡢࡴࡪࡺࡠࡶࡲࡰࡥࡨࡷࡸ࠴ࡡࡳࡩࡹ࠲ࡱ࡫࡮ࡨࡶ࡫ࠤ࠲ࠦ࠳࡞࡞ࡱࡧࡴࡴࡳࡵࠢࡥࡷࡹࡧࡣ࡬ࡡࡦࡥࡵࡹࠠ࠾ࠢࡳࡶࡴࡩࡥࡴࡵ࠱ࡥࡷ࡭ࡶ࡜ࡲࡵࡳࡨ࡫ࡳࡴ࠰ࡤࡶ࡬ࡼ࠮࡭ࡧࡱ࡫ࡹ࡮ࠠ࠮ࠢ࠴ࡡࡡࡴࡣࡰࡰࡶࡸࠥࡶ࡟ࡪࡰࡧࡩࡽࠦ࠽ࠡࡲࡵࡳࡨ࡫ࡳࡴ࠰ࡤࡶ࡬ࡼ࡛ࡱࡴࡲࡧࡪࡹࡳ࠯ࡣࡵ࡫ࡻ࠴࡬ࡦࡰࡪࡸ࡭ࠦ࠭ࠡ࠴ࡠࡠࡳࡶࡲࡰࡥࡨࡷࡸ࠴ࡡࡳࡩࡹࠤࡂࠦࡰࡳࡱࡦࡩࡸࡹ࠮ࡢࡴࡪࡺ࠳ࡹ࡬ࡪࡥࡨࠬ࠵࠲ࠠࡱࡴࡲࡧࡪࡹࡳ࠯ࡣࡵ࡫ࡻ࠴࡬ࡦࡰࡪࡸ࡭ࠦ࠭ࠡ࠵ࠬࡠࡳࡩ࡯࡯ࡵࡷࠤ࡮ࡳࡰࡰࡴࡷࡣࡵࡲࡡࡺࡹࡵ࡭࡬࡮ࡴ࠵ࡡࡥࡷࡹࡧࡣ࡬ࠢࡀࠤࡷ࡫ࡱࡶ࡫ࡵࡩ࠭ࠨࡰ࡭ࡣࡼࡻࡷ࡯ࡧࡩࡶࠥ࠭ࡀࡢ࡮ࡪ࡯ࡳࡳࡷࡺ࡟ࡱ࡮ࡤࡽࡼࡸࡩࡨࡪࡷ࠸ࡤࡨࡳࡵࡣࡦ࡯࠳ࡩࡨࡳࡱࡰ࡭ࡺࡳ࠮࡭ࡣࡸࡲࡨ࡮ࠠ࠾ࠢࡤࡷࡾࡴࡣࠡࠪ࡯ࡥࡺࡴࡣࡩࡑࡳࡸ࡮ࡵ࡮ࡴࠫࠣࡁࡃࠦࡻ࡝ࡰ࡯ࡩࡹࠦࡣࡢࡲࡶ࠿ࡡࡴࡴࡳࡻࠣࡿࡡࡴࡣࡢࡲࡶࠤࡂࠦࡊࡔࡑࡑ࠲ࡵࡧࡲࡴࡧࠫࡦࡸࡺࡡࡤ࡭ࡢࡧࡦࡶࡳࠪ࡞ࡱࠤࠥࢃࠠࡤࡣࡷࡧ࡭࠮ࡥࡹࠫࠣࡿࡡࡴࠠࠡࠢࠣࢁࡡࡴࠠࠡࡴࡨࡸࡺࡸ࡮ࠡࡣࡺࡥ࡮ࡺࠠࡪ࡯ࡳࡳࡷࡺ࡟ࡱ࡮ࡤࡽࡼࡸࡩࡨࡪࡷ࠸ࡤࡨࡳࡵࡣࡦ࡯࠳ࡩࡨࡳࡱࡰ࡭ࡺࡳ࠮ࡤࡱࡱࡲࡪࡩࡴࠩࡽ࡟ࡲࠥࠦࠠࠡࡹࡶࡉࡳࡪࡰࡰ࡫ࡱࡸ࠿ࠦࡠࡸࡵࡶ࠾࠴࠵ࡣࡥࡲ࠱ࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬࠰ࡦࡳࡲ࠵ࡰ࡭ࡣࡼࡻࡷ࡯ࡧࡩࡶࡂࡧࡦࡶࡳ࠾ࠦࡾࡩࡳࡩ࡯ࡥࡧࡘࡖࡎࡉ࡯࡮ࡲࡲࡲࡪࡴࡴࠩࡌࡖࡓࡓ࠴ࡳࡵࡴ࡬ࡲ࡬࡯ࡦࡺࠪࡦࡥࡵࡹࠩࠪࡿࡣ࠰ࡡࡴࠠࠡࠢࠣ࠲࠳࠴࡬ࡢࡷࡱࡧ࡭ࡕࡰࡵ࡫ࡲࡲࡸࡢ࡮ࠡࠢࢀ࠭ࡡࡴࡽ࡝ࡰ࠲࠮ࠥࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾ࠢ࠭࠳ࡡࡴࠧࣁ")
from ._version import __version__
bstack1l111111l1_opy_ = None
CONFIG = {}
bstack111lll11l1_opy_ = {}
bstack11lll11l1_opy_ = {}
bstack1111l1l11_opy_ = None
bstack11l111l1ll_opy_ = None
bstack1llll1111l_opy_ = None
bstack11l1l111l_opy_ = -1
bstack11l1lll1l1_opy_ = 0
bstack1ll1111l1_opy_ = bstack11ll11l1ll_opy_
bstack1ll111lll1_opy_ = 1
bstack11lllllll1_opy_ = False
bstack11l1l1111l_opy_ = False
bstack11l11ll111_opy_ = bstack1ll_opy_ (u"ࠩࠪࣂ")
bstack1l1l1ll1l1_opy_ = bstack1ll_opy_ (u"ࠪࠫࣃ")
bstack11l11l11ll_opy_ = False
bstack11l111llll_opy_ = True
bstack111l11l11_opy_ = bstack1ll_opy_ (u"ࠫࠬࣄ")
bstack1llll11lll_opy_ = []
bstack1lll11l1l_opy_ = threading.Lock()
bstack11llll1l_opy_ = threading.Lock()
bstack1ll111lll_opy_ = bstack1ll_opy_ (u"ࠬ࠭ࣅ")
bstack111lllll_opy_ = False
bstack111llll11_opy_ = None
bstack1lll111l_opy_ = None
bstack1ll1l1ll_opy_ = None
bstack1l1l1l1l1l_opy_ = -1
bstack1l11lllll1_opy_ = os.path.join(os.path.expanduser(bstack1ll_opy_ (u"࠭ࡾࠨࣆ")), bstack1ll_opy_ (u"ࠧ࠯ࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱࠧࣇ"), bstack1ll_opy_ (u"ࠨ࠰ࡵࡳࡧࡵࡴ࠮ࡴࡨࡴࡴࡸࡴ࠮ࡪࡨࡰࡵ࡫ࡲ࠯࡬ࡶࡳࡳ࠭ࣈ"))
bstack1llll1ll11_opy_ = 0
bstack1ll11l11_opy_ = 0
bstack1lll11ll_opy_ = []
bstack1111ll11l_opy_ = []
bstack11l1l11l11_opy_ = []
bstack1l11l1ll11_opy_ = []
bstack1ll11l111l_opy_ = bstack1ll_opy_ (u"ࠩࠪࣉ")
bstack1l1lll1l1_opy_ = bstack1ll_opy_ (u"ࠪࠫ࣊")
bstack1111l11ll_opy_ = False
bstack1lll111111_opy_ = False
bstack111l11111_opy_ = {}
bstack1lll1l111l_opy_ = {}
bstack11ll1l1lll_opy_ = None
bstack1l1111ll1_opy_ = None
bstack1l1l11ll1l_opy_ = None
bstack111l11l1l_opy_ = None
bstack11ll1ll11_opy_ = None
bstack1ll11l1lll_opy_ = None
bstack11l1ll1111_opy_ = None
bstack11ll111ll_opy_ = None
bstack11111ll1_opy_ = None
bstack1ll11l1l_opy_ = None
bstack1l111l111_opy_ = None
bstack1ll11l1111_opy_ = None
bstack111ll111l_opy_ = None
bstack1ll11l11l1_opy_ = None
bstack1l1l111l1_opy_ = None
bstack1l11lll111_opy_ = None
bstack1l111l1ll_opy_ = None
bstack1llll11ll1_opy_ = None
bstack11lll1l111_opy_ = None
bstack1ll1l11ll_opy_ = None
bstack1lll1llll1_opy_ = None
bstack111lll1l1l_opy_ = None
bstack1l1l11l111_opy_ = None
thread_local = threading.local()
bstack11l1l1l11_opy_ = False
bstack111lllllll_opy_ = bstack1ll_opy_ (u"ࠦࠧ࣋")
logger = bstack11l1l1lll1_opy_.get_logger(__name__, bstack1ll1111l1_opy_)
bstack1ll1l1l111_opy_ = Config.bstack11lll1111_opy_()
percy = bstack1lll1lllll_opy_()
bstack11l11l1111_opy_ = bstack1l1lll11l1_opy_()
bstack1l1111l1ll_opy_ = bstack1111111l_opy_()
def bstack1l111l11ll_opy_():
  global CONFIG
  global bstack1111l11ll_opy_
  global bstack1ll1l1l111_opy_
  testContextOptions = bstack1lll111lll_opy_(CONFIG)
  if bstack11111l1l_opy_(CONFIG):
    if (bstack1ll_opy_ (u"ࠬࡹ࡫ࡪࡲࡖࡩࡸࡹࡩࡰࡰࡑࡥࡲ࡫ࠧ࣌") in testContextOptions and str(testContextOptions[bstack1ll_opy_ (u"࠭ࡳ࡬࡫ࡳࡗࡪࡹࡳࡪࡱࡱࡒࡦࡳࡥࠨ࣍")]).lower() == bstack1ll_opy_ (u"ࠧࡵࡴࡸࡩࠬ࣎")):
      bstack1111l11ll_opy_ = True
    bstack1ll1l1l111_opy_.bstack11lll1111l_opy_(testContextOptions.get(bstack1ll_opy_ (u"ࠨࡵ࡮࡭ࡵ࡙ࡥࡴࡵ࡬ࡳࡳ࡙ࡴࡢࡶࡸࡷ࣏ࠬ"), False))
  else:
    bstack1111l11ll_opy_ = True
    bstack1ll1l1l111_opy_.bstack11lll1111l_opy_(True)
def bstack11l11ll1l_opy_():
  from appium.version import version as appium_version
  return version.parse(appium_version)
def bstack11l11111l1_opy_():
  from selenium import webdriver
  return version.parse(webdriver.__version__)
def bstack11l11ll1_opy_():
  global bstack1lll1l111l_opy_
  args = sys.argv
  for i in range(len(args)):
    if bstack1ll_opy_ (u"ࠤ࠰࠱ࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭ࡦࡳࡳ࡬ࡩࡨࡨ࡬ࡰࡪࠨ࣐") == args[i].lower() or bstack1ll_opy_ (u"ࠥ࠱࠲ࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮࠲ࡨࡵ࡮ࡧ࡫ࡪ࣑ࠦ") == args[i].lower():
      path = args[i + 1]
      sys.argv.remove(args[i])
      sys.argv.remove(path)
      bstack1lll1l111l_opy_[bstack1ll_opy_ (u"ࠫࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡇࡔࡔࡆࡊࡉࡢࡊࡎࡒࡅࠨ࣒")] = path
      return path
  return None
bstack1lll111ll_opy_ = re.compile(bstack1ll_opy_ (u"ࡷࠨ࠮ࠫࡁ࡟ࠨࢀ࠮࠮ࠫࡁࠬࢁ࠳࠰࠿࣓ࠣ"))
def bstack1l11l1llll_opy_(loader, node):
  value = loader.construct_scalar(node)
  for group in bstack1lll111ll_opy_.findall(value):
    if group is not None and os.environ.get(group) is not None:
      value = value.replace(bstack1ll_opy_ (u"ࠨࠤࡼࠤࣔ") + group + bstack1ll_opy_ (u"ࠢࡾࠤࣕ"), os.environ.get(group))
  return value
def bstack1l111l11l_opy_():
  global bstack1l1l11l111_opy_
  if bstack1l1l11l111_opy_ is None:
        bstack1l1l11l111_opy_ = bstack11l11ll1_opy_()
  bstack1l11lllll_opy_ = bstack1l1l11l111_opy_
  if bstack1l11lllll_opy_ and os.path.exists(os.path.abspath(bstack1l11lllll_opy_)):
    fileName = bstack1l11lllll_opy_
  if bstack1ll_opy_ (u"ࠨࡄࡕࡓ࡜࡙ࡅࡓࡕࡗࡅࡈࡑ࡟ࡄࡑࡑࡊࡎࡍ࡟ࡇࡋࡏࡉࠬࣖ") in os.environ and os.path.exists(
          os.path.abspath(os.environ[bstack1ll_opy_ (u"ࠩࡅࡖࡔ࡝ࡓࡆࡔࡖࡘࡆࡉࡋࡠࡅࡒࡒࡋࡏࡇࡠࡈࡌࡐࡊ࠭ࣗ")])) and not bstack1ll_opy_ (u"ࠪࡪ࡮ࡲࡥࡏࡣࡰࡩࠬࣘ") in locals():
    fileName = os.environ[bstack1ll_opy_ (u"ࠫࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡇࡔࡔࡆࡊࡉࡢࡊࡎࡒࡅࠨࣙ")]
  if bstack1ll_opy_ (u"ࠬ࡬ࡩ࡭ࡧࡑࡥࡲ࡫ࠧࣚ") in locals():
    bstack111ll1l_opy_ = os.path.abspath(fileName)
  else:
    bstack111ll1l_opy_ = bstack1ll_opy_ (u"࠭ࠧࣛ")
  bstack1llll1llll_opy_ = os.getcwd()
  bstack1l11l11lll_opy_ = bstack1ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰ࠴ࡹ࡮࡮ࠪࣜ")
  bstack111l1l1l1_opy_ = bstack1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࠮ࡺࡣࡰࡰࠬࣝ")
  while (not os.path.exists(bstack111ll1l_opy_)) and bstack1llll1llll_opy_ != bstack1ll_opy_ (u"ࠤࠥࣞ"):
    bstack111ll1l_opy_ = os.path.join(bstack1llll1llll_opy_, bstack1l11l11lll_opy_)
    if not os.path.exists(bstack111ll1l_opy_):
      bstack111ll1l_opy_ = os.path.join(bstack1llll1llll_opy_, bstack111l1l1l1_opy_)
    if bstack1llll1llll_opy_ != os.path.dirname(bstack1llll1llll_opy_):
      bstack1llll1llll_opy_ = os.path.dirname(bstack1llll1llll_opy_)
    else:
      bstack1llll1llll_opy_ = bstack1ll_opy_ (u"ࠥࠦࣟ")
  bstack1l1l11l111_opy_ = bstack111ll1l_opy_ if os.path.exists(bstack111ll1l_opy_) else None
  return bstack1l1l11l111_opy_
def bstack1llll1ll1l_opy_(config):
    if bstack1ll_opy_ (u"ࠫࡹ࡫ࡳࡵࡔࡨࡴࡴࡸࡴࡪࡰࡪࠫ࣠") in config:
      config[bstack1ll_opy_ (u"ࠬࡺࡥࡴࡶࡒࡦࡸ࡫ࡲࡷࡣࡥ࡭ࡱ࡯ࡴࡺࠩ࣡")] = config[bstack1ll_opy_ (u"࠭ࡴࡦࡵࡷࡖࡪࡶ࡯ࡳࡶ࡬ࡲ࡬࠭࣢")]
    if bstack1ll_opy_ (u"ࠧࡵࡧࡶࡸࡗ࡫ࡰࡰࡴࡷ࡭ࡳ࡭ࡏࡱࡶ࡬ࡳࡳࡹࣣࠧ") in config:
      config[bstack1ll_opy_ (u"ࠨࡶࡨࡷࡹࡕࡢࡴࡧࡵࡺࡦࡨࡩ࡭࡫ࡷࡽࡔࡶࡴࡪࡱࡱࡷࠬࣤ")] = config[bstack1ll_opy_ (u"ࠩࡷࡩࡸࡺࡒࡦࡲࡲࡶࡹ࡯࡮ࡨࡑࡳࡸ࡮ࡵ࡮ࡴࠩࣥ")]
def bstack11ll1111l1_opy_():
  bstack111ll1l_opy_ = bstack1l111l11l_opy_()
  if not os.path.exists(bstack111ll1l_opy_):
    bstack1ll1l1lll_opy_(
      bstack111lll1111_opy_.format(os.getcwd()))
  try:
    with open(bstack111ll1l_opy_, bstack1ll_opy_ (u"ࠪࡶࣦࠬ")) as stream:
      yaml.add_implicit_resolver(bstack1ll_opy_ (u"ࠦࠦࡶࡡࡵࡪࡨࡼࠧࣧ"), bstack1lll111ll_opy_)
      yaml.add_constructor(bstack1ll_opy_ (u"ࠧࠧࡰࡢࡶ࡫ࡩࡽࠨࣨ"), bstack1l11l1llll_opy_)
      config = yaml.load(stream, yaml.FullLoader)
      bstack1llll1ll1l_opy_(config)
      return config
  except:
    with open(bstack111ll1l_opy_, bstack1ll_opy_ (u"࠭ࡲࠨࣩ")) as stream:
      try:
        config = yaml.safe_load(stream)
        bstack1llll1ll1l_opy_(config)
        return config
      except yaml.YAMLError as exc:
        bstack1ll1l1lll_opy_(bstack1lll11l1_opy_.format(str(exc)))
def bstack1lll11ll1l_opy_(config):
  bstack111lll111_opy_ = bstack11lllll1_opy_(config)
  for option in list(bstack111lll111_opy_):
    if option.lower() in bstack11l11l111_opy_ and option != bstack11l11l111_opy_[option.lower()]:
      bstack111lll111_opy_[bstack11l11l111_opy_[option.lower()]] = bstack111lll111_opy_[option]
      del bstack111lll111_opy_[option]
  return config
def bstack1llll11111_opy_():
  global bstack11lll11l1_opy_
  for key, bstack11lllll1l1_opy_ in bstack11111l11l_opy_.items():
    if isinstance(bstack11lllll1l1_opy_, list):
      for var in bstack11lllll1l1_opy_:
        if var in os.environ and os.environ[var] and str(os.environ[var]).strip():
          bstack11lll11l1_opy_[key] = os.environ[var]
          break
    elif bstack11lllll1l1_opy_ in os.environ and os.environ[bstack11lllll1l1_opy_] and str(os.environ[bstack11lllll1l1_opy_]).strip():
      bstack11lll11l1_opy_[key] = os.environ[bstack11lllll1l1_opy_]
  if bstack1ll_opy_ (u"ࠧࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡌࡐࡅࡄࡐࡤࡏࡄࡆࡐࡗࡍࡋࡏࡅࡓࠩ࣪") in os.environ:
    bstack11lll11l1_opy_[bstack1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡕࡷࡥࡨࡱࡌࡰࡥࡤࡰࡔࡶࡴࡪࡱࡱࡷࠬ࣫")] = {}
    bstack11lll11l1_opy_[bstack1ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡖࡸࡦࡩ࡫ࡍࡱࡦࡥࡱࡕࡰࡵ࡫ࡲࡲࡸ࠭࣬")][bstack1ll_opy_ (u"ࠪࡰࡴࡩࡡ࡭ࡋࡧࡩࡳࡺࡩࡧ࡫ࡨࡶ࣭ࠬ")] = os.environ[bstack1ll_opy_ (u"ࠫࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡐࡔࡉࡁࡍࡡࡌࡈࡊࡔࡔࡊࡈࡌࡉࡗ࣮࠭")]
def bstack1ll1l1l11l_opy_():
  global bstack111lll11l1_opy_
  global bstack111l11l11_opy_
  global bstack1lll1l111l_opy_
  bstack11lll111ll_opy_ = []
  for idx, val in enumerate(sys.argv):
    if idx < len(sys.argv) - 1 and bstack1ll_opy_ (u"ࠬ࠳࠭ࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰ࠴࡬ࡰࡥࡤࡰࡎࡪࡥ࡯ࡶ࡬ࡪ࡮࡫ࡲࠨ࣯").lower() == val.lower():
      bstack111lll11l1_opy_[bstack1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡓࡵࡣࡦ࡯ࡑࡵࡣࡢ࡮ࡒࡴࡹ࡯࡯࡯ࡵࣰࠪ")] = {}
      bstack111lll11l1_opy_[bstack1ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡔࡶࡤࡧࡰࡒ࡯ࡤࡣ࡯ࡓࡵࡺࡩࡰࡰࡶࣱࠫ")][bstack1ll_opy_ (u"ࠨ࡮ࡲࡧࡦࡲࡉࡥࡧࡱࡸ࡮࡬ࡩࡦࡴࣲࠪ")] = sys.argv[idx + 1]
      bstack11lll111ll_opy_.extend([idx, idx + 1])
      break
  for key, bstack1ll111llll_opy_ in bstack1ll1ll1l1_opy_.items():
    if isinstance(bstack1ll111llll_opy_, list):
      for idx, val in enumerate(sys.argv):
        if idx >= len(sys.argv) - 1:
          continue
        for var in bstack1ll111llll_opy_:
          if bstack1ll_opy_ (u"ࠩ࠰࠱ࠬࣳ") + var.lower() == val.lower() and key not in bstack111lll11l1_opy_:
            bstack111lll11l1_opy_[key] = sys.argv[idx + 1]
            bstack111l11l11_opy_ += bstack1ll_opy_ (u"ࠪࠤ࠲࠳ࠧࣴ") + var + bstack1ll_opy_ (u"ࠫࠥ࠭ࣵ") + shlex.quote(sys.argv[idx + 1])
            bstack11111l111_opy_(bstack1lll1l111l_opy_, key, sys.argv[idx + 1])
            bstack11lll111ll_opy_.extend([idx, idx + 1])
            break
    else:
      for idx, val in enumerate(sys.argv):
        if idx >= len(sys.argv) - 1:
          continue
        if bstack1ll_opy_ (u"ࠬ࠳࠭ࠨࣶ") + bstack1ll111llll_opy_.lower() == val.lower() and key not in bstack111lll11l1_opy_:
          bstack111lll11l1_opy_[key] = sys.argv[idx + 1]
          bstack111l11l11_opy_ += bstack1ll_opy_ (u"࠭ࠠ࠮࠯ࠪࣷ") + bstack1ll111llll_opy_ + bstack1ll_opy_ (u"ࠧࠡࠩࣸ") + shlex.quote(sys.argv[idx + 1])
          bstack11111l111_opy_(bstack1lll1l111l_opy_, key, sys.argv[idx + 1])
          bstack11lll111ll_opy_.extend([idx, idx + 1])
  for idx in sorted(set(bstack11lll111ll_opy_), reverse=True):
    if idx < len(sys.argv):
      del sys.argv[idx]
def bstack11l1ll1l1l_opy_(config):
  bstack11ll1l1ll_opy_ = config.keys()
  for bstack11llll1l1_opy_, bstack11l11ll11_opy_ in bstack11l11111ll_opy_.items():
    if bstack11l11ll11_opy_ in bstack11ll1l1ll_opy_:
      config[bstack11llll1l1_opy_] = config[bstack11l11ll11_opy_]
      del config[bstack11l11ll11_opy_]
  for bstack11llll1l1_opy_, bstack11l11ll11_opy_ in bstack1ll11ll1l1_opy_.items():
    if isinstance(bstack11l11ll11_opy_, list):
      for bstack1ll11ll1ll_opy_ in bstack11l11ll11_opy_:
        if bstack1ll11ll1ll_opy_ in bstack11ll1l1ll_opy_:
          config[bstack11llll1l1_opy_] = config[bstack1ll11ll1ll_opy_]
          del config[bstack1ll11ll1ll_opy_]
          break
    elif bstack11l11ll11_opy_ in bstack11ll1l1ll_opy_:
      config[bstack11llll1l1_opy_] = config[bstack11l11ll11_opy_]
      del config[bstack11l11ll11_opy_]
  for bstack1ll11ll1ll_opy_ in list(config):
    for bstack1ll1l111l1_opy_ in bstack1l1111111l_opy_:
      if bstack1ll11ll1ll_opy_.lower() == bstack1ll1l111l1_opy_.lower() and bstack1ll11ll1ll_opy_ != bstack1ll1l111l1_opy_:
        config[bstack1ll1l111l1_opy_] = config[bstack1ll11ll1ll_opy_]
        del config[bstack1ll11ll1ll_opy_]
  bstack1111ll1ll_opy_ = [{}]
  if not config.get(bstack1ll_opy_ (u"ࠨࡲ࡯ࡥࡹ࡬࡯ࡳ࡯ࡶࣹࠫ")):
    config[bstack1ll_opy_ (u"ࠩࡳࡰࡦࡺࡦࡰࡴࡰࡷࣺࠬ")] = [{}]
  bstack1111ll1ll_opy_ = config[bstack1ll_opy_ (u"ࠪࡴࡱࡧࡴࡧࡱࡵࡱࡸ࠭ࣻ")]
  for platform in bstack1111ll1ll_opy_:
    for bstack1ll11ll1ll_opy_ in list(platform):
      for bstack1ll1l111l1_opy_ in bstack1l1111111l_opy_:
        if bstack1ll11ll1ll_opy_.lower() == bstack1ll1l111l1_opy_.lower() and bstack1ll11ll1ll_opy_ != bstack1ll1l111l1_opy_:
          platform[bstack1ll1l111l1_opy_] = platform[bstack1ll11ll1ll_opy_]
          del platform[bstack1ll11ll1ll_opy_]
  for bstack11llll1l1_opy_, bstack11l11ll11_opy_ in bstack1ll11ll1l1_opy_.items():
    for platform in bstack1111ll1ll_opy_:
      if isinstance(bstack11l11ll11_opy_, list):
        for bstack1ll11ll1ll_opy_ in bstack11l11ll11_opy_:
          if bstack1ll11ll1ll_opy_ in platform:
            platform[bstack11llll1l1_opy_] = platform[bstack1ll11ll1ll_opy_]
            del platform[bstack1ll11ll1ll_opy_]
            break
      elif bstack11l11ll11_opy_ in platform:
        platform[bstack11llll1l1_opy_] = platform[bstack11l11ll11_opy_]
        del platform[bstack11l11ll11_opy_]
  for bstack1ll11l1ll_opy_ in bstack11llllllll_opy_:
    if bstack1ll11l1ll_opy_ in config:
      if not bstack11llllllll_opy_[bstack1ll11l1ll_opy_] in config:
        config[bstack11llllllll_opy_[bstack1ll11l1ll_opy_]] = {}
      config[bstack11llllllll_opy_[bstack1ll11l1ll_opy_]].update(config[bstack1ll11l1ll_opy_])
      del config[bstack1ll11l1ll_opy_]
  for platform in bstack1111ll1ll_opy_:
    for bstack1ll11l1ll_opy_ in bstack11llllllll_opy_:
      if bstack1ll11l1ll_opy_ in list(platform):
        if not bstack11llllllll_opy_[bstack1ll11l1ll_opy_] in platform:
          platform[bstack11llllllll_opy_[bstack1ll11l1ll_opy_]] = {}
        platform[bstack11llllllll_opy_[bstack1ll11l1ll_opy_]].update(platform[bstack1ll11l1ll_opy_])
        del platform[bstack1ll11l1ll_opy_]
  config = bstack1lll11ll1l_opy_(config)
  return config
def bstack11lll1l1l_opy_(config):
  global bstack1l1l1ll1l1_opy_
  bstack11lll1ll_opy_ = False
  if bstack1ll_opy_ (u"ࠫࡹࡻࡲࡣࡱࡖࡧࡦࡲࡥࠨࣼ") in config and str(config[bstack1ll_opy_ (u"ࠬࡺࡵࡳࡤࡲࡗࡨࡧ࡬ࡦࠩࣽ")]).lower() != bstack1ll_opy_ (u"࠭ࡦࡢ࡮ࡶࡩࠬࣾ"):
    if bstack1ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰࡒ࡯ࡤࡣ࡯ࠫࣿ") not in config or str(config[bstack1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱࡌࡰࡥࡤࡰࠬऀ")]).lower() == bstack1ll_opy_ (u"ࠩࡩࡥࡱࡹࡥࠨँ"):
      config[bstack1ll_opy_ (u"ࠪࡰࡴࡩࡡ࡭ࠩं")] = False
    else:
      bstack1l11111l11_opy_ = bstack11l1lllll1_opy_()
      if bstack1ll_opy_ (u"ࠫ࡮ࡹࡔࡳ࡫ࡤࡰࡌࡸࡩࡥࠩः") in bstack1l11111l11_opy_:
        if not bstack1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷ࡙ࡴࡢࡥ࡮ࡐࡴࡩࡡ࡭ࡑࡳࡸ࡮ࡵ࡮ࡴࠩऄ") in config:
          config[bstack1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡓࡵࡣࡦ࡯ࡑࡵࡣࡢ࡮ࡒࡴࡹ࡯࡯࡯ࡵࠪअ")] = {}
        config[bstack1ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡔࡶࡤࡧࡰࡒ࡯ࡤࡣ࡯ࡓࡵࡺࡩࡰࡰࡶࠫआ")][bstack1ll_opy_ (u"ࠨ࡮ࡲࡧࡦࡲࡉࡥࡧࡱࡸ࡮࡬ࡩࡦࡴࠪइ")] = bstack1ll_opy_ (u"ࠩࡤࡸࡸ࠳ࡲࡦࡲࡨࡥࡹ࡫ࡲࠨई")
        bstack11lll1ll_opy_ = True
        bstack1l1l1ll1l1_opy_ = config[bstack1ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵࡗࡹࡧࡣ࡬ࡎࡲࡧࡦࡲࡏࡱࡶ࡬ࡳࡳࡹࠧउ")].get(bstack1ll_opy_ (u"ࠫࡱࡵࡣࡢ࡮ࡌࡨࡪࡴࡴࡪࡨ࡬ࡩࡷ࠭ऊ"))
  if bstack11111l1l_opy_(config) and bstack1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮ࡐࡴࡩࡡ࡭ࠩऋ") in config and str(config[bstack1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯ࡑࡵࡣࡢ࡮ࠪऌ")]).lower() != bstack1ll_opy_ (u"ࠧࡧࡣ࡯ࡷࡪ࠭ऍ") and not bstack11lll1ll_opy_:
    if not bstack1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡕࡷࡥࡨࡱࡌࡰࡥࡤࡰࡔࡶࡴࡪࡱࡱࡷࠬऎ") in config:
      config[bstack1ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡖࡸࡦࡩ࡫ࡍࡱࡦࡥࡱࡕࡰࡵ࡫ࡲࡲࡸ࠭ए")] = {}
    if not config[bstack1ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵࡗࡹࡧࡣ࡬ࡎࡲࡧࡦࡲࡏࡱࡶ࡬ࡳࡳࡹࠧऐ")].get(bstack1ll_opy_ (u"ࠫࡸࡱࡩࡱࡄ࡬ࡲࡦࡸࡹࡊࡰ࡬ࡸ࡮ࡧ࡬ࡪࡵࡤࡸ࡮ࡵ࡮ࠨऑ")) and not bstack1ll_opy_ (u"ࠬࡲ࡯ࡤࡣ࡯ࡍࡩ࡫࡮ࡵ࡫ࡩ࡭ࡪࡸࠧऒ") in config[bstack1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡓࡵࡣࡦ࡯ࡑࡵࡣࡢ࡮ࡒࡴࡹ࡯࡯࡯ࡵࠪओ")]:
      bstack1l11l1111_opy_ = datetime.datetime.now()
      bstack1l11ll1ll_opy_ = bstack1l11l1111_opy_.strftime(bstack1ll_opy_ (u"ࠧࠦࡦࡢࠩࡧࡥࠥࡉࠧࡐࠫऔ"))
      hostname = socket.gethostname()
      bstack1l11l111l_opy_ = bstack1ll_opy_ (u"ࠨࠩक").join(random.choices(string.ascii_lowercase + string.digits, k=4))
      identifier = bstack1ll_opy_ (u"ࠩࡾࢁࡤࢁࡽࡠࡽࢀࠫख").format(bstack1l11ll1ll_opy_, hostname, bstack1l11l111l_opy_)
      config[bstack1ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵࡗࡹࡧࡣ࡬ࡎࡲࡧࡦࡲࡏࡱࡶ࡬ࡳࡳࡹࠧग")][bstack1ll_opy_ (u"ࠫࡱࡵࡣࡢ࡮ࡌࡨࡪࡴࡴࡪࡨ࡬ࡩࡷ࠭घ")] = identifier
    bstack1l1l1ll1l1_opy_ = config[bstack1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷ࡙ࡴࡢࡥ࡮ࡐࡴࡩࡡ࡭ࡑࡳࡸ࡮ࡵ࡮ࡴࠩङ")].get(bstack1ll_opy_ (u"࠭࡬ࡰࡥࡤࡰࡎࡪࡥ࡯ࡶ࡬ࡪ࡮࡫ࡲࠨच"))
  return config
def bstack11l1ll111_opy_():
  bstack11llll1111_opy_ =  bstack1ll1ll1l_opy_()[bstack1ll_opy_ (u"ࠧࡣࡷ࡬ࡰࡩࡥ࡮ࡶ࡯ࡥࡩࡷ࠭छ")]
  return bstack11llll1111_opy_ if bstack11llll1111_opy_ else -1
def bstack11llll11_opy_(bstack11llll1111_opy_):
  global CONFIG
  if not bstack1ll_opy_ (u"ࠨࠦࡾࡆ࡚ࡏࡌࡅࡡࡑ࡙ࡒࡈࡅࡓࡿࠪज") in CONFIG[bstack1ll_opy_ (u"ࠩࡥࡹ࡮ࡲࡤࡊࡦࡨࡲࡹ࡯ࡦࡪࡧࡵࠫझ")]:
    return
  CONFIG[bstack1ll_opy_ (u"ࠪࡦࡺ࡯࡬ࡥࡋࡧࡩࡳࡺࡩࡧ࡫ࡨࡶࠬञ")] = CONFIG[bstack1ll_opy_ (u"ࠫࡧࡻࡩ࡭ࡦࡌࡨࡪࡴࡴࡪࡨ࡬ࡩࡷ࠭ट")].replace(
    bstack1ll_opy_ (u"ࠬࠪࡻࡃࡗࡌࡐࡉࡥࡎࡖࡏࡅࡉࡗࢃࠧठ"),
    str(bstack11llll1111_opy_)
  )
def bstack11l11l11l1_opy_():
  global CONFIG
  if not bstack1ll_opy_ (u"࠭ࠤࡼࡆࡄࡘࡊࡥࡔࡊࡏࡈࢁࠬड") in CONFIG[bstack1ll_opy_ (u"ࠧࡣࡷ࡬ࡰࡩࡏࡤࡦࡰࡷ࡭࡫࡯ࡥࡳࠩढ")]:
    return
  bstack1l11l1111_opy_ = datetime.datetime.now()
  bstack1l11ll1ll_opy_ = bstack1l11l1111_opy_.strftime(bstack1ll_opy_ (u"ࠨࠧࡧ࠱ࠪࡨ࠭ࠦࡊ࠽ࠩࡒ࠭ण"))
  CONFIG[bstack1ll_opy_ (u"ࠩࡥࡹ࡮ࡲࡤࡊࡦࡨࡲࡹ࡯ࡦࡪࡧࡵࠫत")] = CONFIG[bstack1ll_opy_ (u"ࠪࡦࡺ࡯࡬ࡥࡋࡧࡩࡳࡺࡩࡧ࡫ࡨࡶࠬथ")].replace(
    bstack1ll_opy_ (u"ࠫࠩࢁࡄࡂࡖࡈࡣ࡙ࡏࡍࡆࡿࠪद"),
    bstack1l11ll1ll_opy_
  )
def bstack11l11l1lll_opy_():
  global CONFIG
  if bstack1ll_opy_ (u"ࠬࡨࡵࡪ࡮ࡧࡍࡩ࡫࡮ࡵ࡫ࡩ࡭ࡪࡸࠧध") in CONFIG and not bool(CONFIG[bstack1ll_opy_ (u"࠭ࡢࡶ࡫࡯ࡨࡎࡪࡥ࡯ࡶ࡬ࡪ࡮࡫ࡲࠨन")]):
    del CONFIG[bstack1ll_opy_ (u"ࠧࡣࡷ࡬ࡰࡩࡏࡤࡦࡰࡷ࡭࡫࡯ࡥࡳࠩऩ")]
    return
  if not bstack1ll_opy_ (u"ࠨࡤࡸ࡭ࡱࡪࡉࡥࡧࡱࡸ࡮࡬ࡩࡦࡴࠪप") in CONFIG:
    CONFIG[bstack1ll_opy_ (u"ࠩࡥࡹ࡮ࡲࡤࡊࡦࡨࡲࡹ࡯ࡦࡪࡧࡵࠫफ")] = bstack1ll_opy_ (u"ࠪࠧࠩࢁࡂࡖࡋࡏࡈࡤࡔࡕࡎࡄࡈࡖࢂ࠭ब")
  if bstack1ll_opy_ (u"ࠫࠩࢁࡄࡂࡖࡈࡣ࡙ࡏࡍࡆࡿࠪभ") in CONFIG[bstack1ll_opy_ (u"ࠬࡨࡵࡪ࡮ࡧࡍࡩ࡫࡮ࡵ࡫ࡩ࡭ࡪࡸࠧम")]:
    bstack11l11l11l1_opy_()
    os.environ[bstack1ll_opy_ (u"࠭ࡂࡔࡖࡄࡇࡐࡥࡃࡐࡏࡅࡍࡓࡋࡄࡠࡄࡘࡍࡑࡊ࡟ࡊࡆࠪय")] = CONFIG[bstack1ll_opy_ (u"ࠧࡣࡷ࡬ࡰࡩࡏࡤࡦࡰࡷ࡭࡫࡯ࡥࡳࠩर")]
  if not bstack1ll_opy_ (u"ࠨࠦࡾࡆ࡚ࡏࡌࡅࡡࡑ࡙ࡒࡈࡅࡓࡿࠪऱ") in CONFIG[bstack1ll_opy_ (u"ࠩࡥࡹ࡮ࡲࡤࡊࡦࡨࡲࡹ࡯ࡦࡪࡧࡵࠫल")]:
    return
  bstack11llll1111_opy_ = bstack1ll_opy_ (u"ࠪࠫळ")
  bstack11l1111ll_opy_ = bstack11l1ll111_opy_()
  if bstack11l1111ll_opy_ != -1:
    bstack11llll1111_opy_ = bstack1ll_opy_ (u"ࠫࡈࡏࠠࠨऴ") + str(bstack11l1111ll_opy_)
  if bstack11llll1111_opy_ == bstack1ll_opy_ (u"ࠬ࠭व"):
    bstack1l1llll11l_opy_ = bstack1l1ll11l_opy_(CONFIG[bstack1ll_opy_ (u"࠭ࡢࡶ࡫࡯ࡨࡓࡧ࡭ࡦࠩश")])
    if bstack1l1llll11l_opy_ != -1:
      bstack11llll1111_opy_ = str(bstack1l1llll11l_opy_)
  if bstack11llll1111_opy_:
    bstack11llll11_opy_(bstack11llll1111_opy_)
    os.environ[bstack1ll_opy_ (u"ࠧࡃࡕࡗࡅࡈࡑ࡟ࡄࡑࡐࡆࡎࡔࡅࡅࡡࡅ࡙ࡎࡒࡄࡠࡋࡇࠫष")] = CONFIG[bstack1ll_opy_ (u"ࠨࡤࡸ࡭ࡱࡪࡉࡥࡧࡱࡸ࡮࡬ࡩࡦࡴࠪस")]
def bstack1llll111l_opy_(bstack1llll1lll1_opy_, bstack1ll11lll1_opy_, path):
  bstack1l1l11ll1_opy_ = {
    bstack1ll_opy_ (u"ࠩ࡬ࡨࡪࡴࡴࡪࡨ࡬ࡩࡷ࠭ह"): bstack1ll11lll1_opy_
  }
  if os.path.exists(path):
    bstack11lllll111_opy_ = json.load(open(path, bstack1ll_opy_ (u"ࠪࡶࡧ࠭ऺ")))
  else:
    bstack11lllll111_opy_ = {}
  bstack11lllll111_opy_[bstack1llll1lll1_opy_] = bstack1l1l11ll1_opy_
  with open(path, bstack1ll_opy_ (u"ࠦࡼ࠱ࠢऻ")) as outfile:
    json.dump(bstack11lllll111_opy_, outfile)
def bstack1l1ll11l_opy_(bstack1llll1lll1_opy_):
  bstack1llll1lll1_opy_ = str(bstack1llll1lll1_opy_)
  bstack1l11l11l1l_opy_ = os.path.join(os.path.expanduser(bstack1ll_opy_ (u"ࠬࢄ़ࠧ")), bstack1ll_opy_ (u"࠭࠮ࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰ࠭ऽ"))
  try:
    if not os.path.exists(bstack1l11l11l1l_opy_):
      os.makedirs(bstack1l11l11l1l_opy_)
    file_path = os.path.join(os.path.expanduser(bstack1ll_opy_ (u"ࠧࡿࠩा")), bstack1ll_opy_ (u"ࠨ࠰ࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫ࠨि"), bstack1ll_opy_ (u"ࠩ࠱ࡦࡺ࡯࡬ࡥ࠯ࡱࡥࡲ࡫࠭ࡤࡣࡦ࡬ࡪ࠴ࡪࡴࡱࡱࠫी"))
    if not os.path.isfile(file_path):
      with open(file_path, bstack1ll_opy_ (u"ࠪࡻࠬु")):
        pass
      with open(file_path, bstack1ll_opy_ (u"ࠦࡼ࠱ࠢू")) as outfile:
        json.dump({}, outfile)
    with open(file_path, bstack1ll_opy_ (u"ࠬࡸࠧृ")) as bstack11l11l111l_opy_:
      bstack1lllll1111_opy_ = json.load(bstack11l11l111l_opy_)
    if bstack1llll1lll1_opy_ in bstack1lllll1111_opy_:
      bstack11l1ll1l11_opy_ = bstack1lllll1111_opy_[bstack1llll1lll1_opy_][bstack1ll_opy_ (u"࠭ࡩࡥࡧࡱࡸ࡮࡬ࡩࡦࡴࠪॄ")]
      bstack1ll11llll_opy_ = int(bstack11l1ll1l11_opy_) + 1
      bstack1llll111l_opy_(bstack1llll1lll1_opy_, bstack1ll11llll_opy_, file_path)
      return bstack1ll11llll_opy_
    else:
      bstack1llll111l_opy_(bstack1llll1lll1_opy_, 1, file_path)
      return 1
  except Exception as e:
    logger.warning(bstack1l1lll1111_opy_.format(str(e)))
    return -1
def bstack1l11l1ll1_opy_(config):
  if not config[bstack1ll_opy_ (u"ࠧࡶࡵࡨࡶࡓࡧ࡭ࡦࠩॅ")] or not config[bstack1ll_opy_ (u"ࠨࡣࡦࡧࡪࡹࡳࡌࡧࡼࠫॆ")]:
    return True
  else:
    return False
def bstack11l1ll1ll1_opy_(config, index=0):
  global bstack11l11l11ll_opy_
  bstack1lll1ll1_opy_ = {}
  caps = bstack11l11l1ll_opy_ + bstack1l1l1l111l_opy_
  if config.get(bstack1ll_opy_ (u"ࠩࡷࡹࡷࡨ࡯ࡔࡥࡤࡰࡪ࠭े"), False):
    bstack1lll1ll1_opy_[bstack1ll_opy_ (u"ࠪࡸࡺࡸࡢࡰࡵࡦࡥࡱ࡫ࠧै")] = True
    bstack1lll1ll1_opy_[bstack1ll_opy_ (u"ࠫࡹࡻࡲࡣࡱࡖࡧࡦࡲࡥࡐࡲࡷ࡭ࡴࡴࡳࠨॉ")] = config.get(bstack1ll_opy_ (u"ࠬࡺࡵࡳࡤࡲࡗࡨࡧ࡬ࡦࡑࡳࡸ࡮ࡵ࡮ࡴࠩॊ"), {})
  if bstack11l11l11ll_opy_:
    caps += bstack1l111l1l1_opy_
  for key in config:
    if key in caps + [bstack1ll_opy_ (u"࠭ࡰ࡭ࡣࡷࡪࡴࡸ࡭ࡴࠩो")]:
      continue
    bstack1lll1ll1_opy_[key] = config[key]
  if bstack1ll_opy_ (u"ࠧࡱ࡮ࡤࡸ࡫ࡵࡲ࡮ࡵࠪौ") in config:
    for bstack111ll1ll_opy_ in config[bstack1ll_opy_ (u"ࠨࡲ࡯ࡥࡹ࡬࡯ࡳ࡯ࡶ्ࠫ")][index]:
      if bstack111ll1ll_opy_ in caps:
        continue
      bstack1lll1ll1_opy_[bstack111ll1ll_opy_] = config[bstack1ll_opy_ (u"ࠩࡳࡰࡦࡺࡦࡰࡴࡰࡷࠬॎ")][index][bstack111ll1ll_opy_]
  bstack1lll1ll1_opy_[bstack1ll_opy_ (u"ࠪ࡬ࡴࡹࡴࡏࡣࡰࡩࠬॏ")] = socket.gethostname()
  if bstack1ll_opy_ (u"ࠫࡻ࡫ࡲࡴ࡫ࡲࡲࠬॐ") in bstack1lll1ll1_opy_:
    del (bstack1lll1ll1_opy_[bstack1ll_opy_ (u"ࠬࡼࡥࡳࡵ࡬ࡳࡳ࠭॑")])
  return bstack1lll1ll1_opy_
def bstack1lll1l11l1_opy_(config):
  global bstack11l11l11ll_opy_
  bstack1l11lll1_opy_ = {}
  caps = bstack1l1l1l111l_opy_
  if bstack11l11l11ll_opy_:
    caps += bstack1l111l1l1_opy_
  for key in caps:
    if key in config:
      bstack1l11lll1_opy_[key] = config[key]
  return bstack1l11lll1_opy_
def bstack1l11lll1l_opy_(bstack1lll1ll1_opy_, bstack1l11lll1_opy_):
  bstack1lll1ll111_opy_ = {}
  for key in bstack1lll1ll1_opy_.keys():
    if key in bstack11l11111ll_opy_:
      bstack1lll1ll111_opy_[bstack11l11111ll_opy_[key]] = bstack1lll1ll1_opy_[key]
    else:
      bstack1lll1ll111_opy_[key] = bstack1lll1ll1_opy_[key]
  for key in bstack1l11lll1_opy_:
    if key in bstack11l11111ll_opy_:
      bstack1lll1ll111_opy_[bstack11l11111ll_opy_[key]] = bstack1l11lll1_opy_[key]
    else:
      bstack1lll1ll111_opy_[key] = bstack1l11lll1_opy_[key]
  return bstack1lll1ll111_opy_
def bstack1l1111llll_opy_(config, index=0):
  global bstack11l11l11ll_opy_
  caps = {}
  config = copy.deepcopy(config)
  bstack1llll1ll_opy_ = bstack1ll1l111_opy_(bstack11lllll1l_opy_, config, logger)
  bstack1l11lll1_opy_ = bstack1lll1l11l1_opy_(config)
  bstack11ll1111ll_opy_ = bstack1l1l1l111l_opy_
  bstack11ll1111ll_opy_ += bstack1l1ll111l1_opy_
  bstack1l11lll1_opy_ = update(bstack1l11lll1_opy_, bstack1llll1ll_opy_)
  if bstack11l11l11ll_opy_:
    bstack11ll1111ll_opy_ += bstack1l111l1l1_opy_
  if bstack1ll_opy_ (u"࠭ࡰ࡭ࡣࡷࡪࡴࡸ࡭ࡴ॒ࠩ") in config:
    if bstack1ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡏࡣࡰࡩࠬ॓") in config[bstack1ll_opy_ (u"ࠨࡲ࡯ࡥࡹ࡬࡯ࡳ࡯ࡶࠫ॔")][index]:
      caps[bstack1ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡑࡥࡲ࡫ࠧॕ")] = config[bstack1ll_opy_ (u"ࠪࡴࡱࡧࡴࡧࡱࡵࡱࡸ࠭ॖ")][index][bstack1ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࡓࡧ࡭ࡦࠩॗ")]
    if bstack1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷ࡜ࡥࡳࡵ࡬ࡳࡳ࠭क़") in config[bstack1ll_opy_ (u"࠭ࡰ࡭ࡣࡷࡪࡴࡸ࡭ࡴࠩख़")][index]:
      caps[bstack1ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡗࡧࡵࡷ࡮ࡵ࡮ࠨग़")] = str(config[bstack1ll_opy_ (u"ࠨࡲ࡯ࡥࡹ࡬࡯ࡳ࡯ࡶࠫज़")][index][bstack1ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴ࡙ࡩࡷࡹࡩࡰࡰࠪड़")])
    bstack11l1lll1l_opy_ = bstack1ll1l111_opy_(bstack11lllll1l_opy_, config[bstack1ll_opy_ (u"ࠪࡴࡱࡧࡴࡧࡱࡵࡱࡸ࠭ढ़")][index], logger)
    bstack11ll1111ll_opy_ += list(bstack11l1lll1l_opy_.keys())
    for bstack11lll111_opy_ in bstack11ll1111ll_opy_:
      if bstack11lll111_opy_ in config[bstack1ll_opy_ (u"ࠫࡵࡲࡡࡵࡨࡲࡶࡲࡹࠧफ़")][index]:
        if bstack11lll111_opy_ == bstack1ll_opy_ (u"ࠬࡶ࡬ࡢࡶࡩࡳࡷࡳࡖࡦࡴࡶ࡭ࡴࡴࠧय़"):
          try:
            bstack11l1lll1l_opy_[bstack11lll111_opy_] = str(config[bstack1ll_opy_ (u"࠭ࡰ࡭ࡣࡷࡪࡴࡸ࡭ࡴࠩॠ")][index][bstack11lll111_opy_] * 1.0)
          except:
            bstack11l1lll1l_opy_[bstack11lll111_opy_] = str(config[bstack1ll_opy_ (u"ࠧࡱ࡮ࡤࡸ࡫ࡵࡲ࡮ࡵࠪॡ")][index][bstack11lll111_opy_])
        else:
          bstack11l1lll1l_opy_[bstack11lll111_opy_] = config[bstack1ll_opy_ (u"ࠨࡲ࡯ࡥࡹ࡬࡯ࡳ࡯ࡶࠫॢ")][index][bstack11lll111_opy_]
        del (config[bstack1ll_opy_ (u"ࠩࡳࡰࡦࡺࡦࡰࡴࡰࡷࠬॣ")][index][bstack11lll111_opy_])
    bstack1l11lll1_opy_ = update(bstack1l11lll1_opy_, bstack11l1lll1l_opy_)
  bstack1lll1ll1_opy_ = bstack11l1ll1ll1_opy_(config, index)
  for bstack1ll11ll1ll_opy_ in bstack1l1l1l111l_opy_ + list(bstack1llll1ll_opy_.keys()):
    if bstack1ll11ll1ll_opy_ in bstack1lll1ll1_opy_:
      bstack1l11lll1_opy_[bstack1ll11ll1ll_opy_] = bstack1lll1ll1_opy_[bstack1ll11ll1ll_opy_]
      del (bstack1lll1ll1_opy_[bstack1ll11ll1ll_opy_])
  if bstack1l1111l11l_opy_(config):
    bstack1lll1ll1_opy_[bstack1ll_opy_ (u"ࠪࡹࡸ࡫ࡗ࠴ࡅࠪ।")] = True
    caps.update(bstack1l11lll1_opy_)
    caps[bstack1ll_opy_ (u"ࠫࡧࡹࡴࡢࡥ࡮࠾ࡴࡶࡴࡪࡱࡱࡷࠬ॥")] = bstack1lll1ll1_opy_
  else:
    bstack1lll1ll1_opy_[bstack1ll_opy_ (u"ࠬࡻࡳࡦ࡙࠶ࡇࠬ०")] = False
    caps.update(bstack1l11lll1l_opy_(bstack1lll1ll1_opy_, bstack1l11lll1_opy_))
    if bstack1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡎࡢ࡯ࡨࠫ१") in caps:
      caps[bstack1ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࠨ२")] = caps[bstack1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡐࡤࡱࡪ࠭३")]
      del (caps[bstack1ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡑࡥࡲ࡫ࠧ४")])
    if bstack1ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵ࡚ࡪࡸࡳࡪࡱࡱࠫ५") in caps:
      caps[bstack1ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࡤࡼࡥࡳࡵ࡬ࡳࡳ࠭६")] = caps[bstack1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷ࡜ࡥࡳࡵ࡬ࡳࡳ࠭७")]
      del (caps[bstack1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡖࡦࡴࡶ࡭ࡴࡴࠧ८")])
  return caps
def bstack111ll1111_opy_():
  global bstack1ll111lll_opy_
  global CONFIG
  if bstack11l11111l1_opy_() <= version.parse(bstack1ll_opy_ (u"ࠧ࠴࠰࠴࠷࠳࠶ࠧ९")):
    if bstack1ll111lll_opy_ != bstack1ll_opy_ (u"ࠨࠩ॰"):
      return bstack1ll_opy_ (u"ࠤ࡫ࡸࡹࡶ࠺࠰࠱ࠥॱ") + bstack1ll111lll_opy_ + bstack1ll_opy_ (u"ࠥ࠾࠽࠶࠯ࡸࡦ࠲࡬ࡺࡨࠢॲ")
    return bstack1l11lll11_opy_
  if bstack1ll111lll_opy_ != bstack1ll_opy_ (u"ࠫࠬॳ"):
    return bstack1ll_opy_ (u"ࠧ࡮ࡴࡵࡲࡶ࠾࠴࠵ࠢॴ") + bstack1ll111lll_opy_ + bstack1ll_opy_ (u"ࠨ࠯ࡸࡦ࠲࡬ࡺࡨࠢॵ")
  return bstack1lll111l11_opy_
def bstack1ll11111_opy_(options):
  return hasattr(options, bstack1ll_opy_ (u"ࠧࡴࡧࡷࡣࡨࡧࡰࡢࡤ࡬ࡰ࡮ࡺࡹࠨॶ"))
def update(d, u):
  for k, v in u.items():
    if isinstance(v, collections.abc.Mapping):
      d[k] = update(d.get(k, {}), v)
    else:
      if isinstance(v, list):
        d[k] = d.get(k, []) + v
      else:
        d[k] = v
  return d
def bstack1l1l11l1l1_opy_(options, bstack1llll1111_opy_):
  for bstack1llllll11_opy_ in bstack1llll1111_opy_:
    if bstack1llllll11_opy_ in [bstack1ll_opy_ (u"ࠨࡣࡵ࡫ࡸ࠭ॷ"), bstack1ll_opy_ (u"ࠩࡨࡼࡹ࡫࡮ࡴ࡫ࡲࡲࡸ࠭ॸ")]:
      continue
    if bstack1llllll11_opy_ in options._experimental_options:
      options._experimental_options[bstack1llllll11_opy_] = update(options._experimental_options[bstack1llllll11_opy_],
                                                         bstack1llll1111_opy_[bstack1llllll11_opy_])
    else:
      options.add_experimental_option(bstack1llllll11_opy_, bstack1llll1111_opy_[bstack1llllll11_opy_])
  if bstack1ll_opy_ (u"ࠪࡥࡷ࡭ࡳࠨॹ") in bstack1llll1111_opy_:
    for arg in bstack1llll1111_opy_[bstack1ll_opy_ (u"ࠫࡦࡸࡧࡴࠩॺ")]:
      options.add_argument(arg)
    del (bstack1llll1111_opy_[bstack1ll_opy_ (u"ࠬࡧࡲࡨࡵࠪॻ")])
  if bstack1ll_opy_ (u"࠭ࡥࡹࡶࡨࡲࡸ࡯࡯࡯ࡵࠪॼ") in bstack1llll1111_opy_:
    for ext in bstack1llll1111_opy_[bstack1ll_opy_ (u"ࠧࡦࡺࡷࡩࡳࡹࡩࡰࡰࡶࠫॽ")]:
      try:
        options.add_extension(ext)
      except OSError:
        options.add_encoded_extension(ext)
    del (bstack1llll1111_opy_[bstack1ll_opy_ (u"ࠨࡧࡻࡸࡪࡴࡳࡪࡱࡱࡷࠬॾ")])
def bstack111111111_opy_(options, bstack1l11ll1lll_opy_):
  if bstack1ll_opy_ (u"ࠩࡳࡶࡪ࡬ࡳࠨॿ") in bstack1l11ll1lll_opy_:
    for bstack1llll111_opy_ in bstack1l11ll1lll_opy_[bstack1ll_opy_ (u"ࠪࡴࡷ࡫ࡦࡴࠩঀ")]:
      if bstack1llll111_opy_ in options._preferences:
        options._preferences[bstack1llll111_opy_] = update(options._preferences[bstack1llll111_opy_], bstack1l11ll1lll_opy_[bstack1ll_opy_ (u"ࠫࡵࡸࡥࡧࡵࠪঁ")][bstack1llll111_opy_])
      else:
        options.set_preference(bstack1llll111_opy_, bstack1l11ll1lll_opy_[bstack1ll_opy_ (u"ࠬࡶࡲࡦࡨࡶࠫং")][bstack1llll111_opy_])
  if bstack1ll_opy_ (u"࠭ࡡࡳࡩࡶࠫঃ") in bstack1l11ll1lll_opy_:
    for arg in bstack1l11ll1lll_opy_[bstack1ll_opy_ (u"ࠧࡢࡴࡪࡷࠬ঄")]:
      options.add_argument(arg)
def bstack11l1l111l1_opy_(options, bstack11ll111111_opy_):
  if bstack1ll_opy_ (u"ࠨࡹࡨࡦࡻ࡯ࡥࡸࠩঅ") in bstack11ll111111_opy_:
    options.use_webview(bool(bstack11ll111111_opy_[bstack1ll_opy_ (u"ࠩࡺࡩࡧࡼࡩࡦࡹࠪআ")]))
  bstack1l1l11l1l1_opy_(options, bstack11ll111111_opy_)
def bstack1l11ll1l11_opy_(options, bstack1llll1l111_opy_):
  for bstack11l1lll1ll_opy_ in bstack1llll1l111_opy_:
    if bstack11l1lll1ll_opy_ in [bstack1ll_opy_ (u"ࠪࡸࡪࡩࡨ࡯ࡱ࡯ࡳ࡬ࡿࡐࡳࡧࡹ࡭ࡪࡽࠧই"), bstack1ll_opy_ (u"ࠫࡦࡸࡧࡴࠩঈ")]:
      continue
    options.set_capability(bstack11l1lll1ll_opy_, bstack1llll1l111_opy_[bstack11l1lll1ll_opy_])
  if bstack1ll_opy_ (u"ࠬࡧࡲࡨࡵࠪউ") in bstack1llll1l111_opy_:
    for arg in bstack1llll1l111_opy_[bstack1ll_opy_ (u"࠭ࡡࡳࡩࡶࠫঊ")]:
      options.add_argument(arg)
  if bstack1ll_opy_ (u"ࠧࡵࡧࡦ࡬ࡳࡵ࡬ࡰࡩࡼࡔࡷ࡫ࡶࡪࡧࡺࠫঋ") in bstack1llll1l111_opy_:
    options.bstack1lll111l1l_opy_(bool(bstack1llll1l111_opy_[bstack1ll_opy_ (u"ࠨࡶࡨࡧ࡭ࡴ࡯࡭ࡱࡪࡽࡕࡸࡥࡷ࡫ࡨࡻࠬঌ")]))
def bstack1ll11ll11_opy_(options, bstack1ll1llll1l_opy_):
  for bstack1l111l1l11_opy_ in bstack1ll1llll1l_opy_:
    if bstack1l111l1l11_opy_ in [bstack1ll_opy_ (u"ࠩࡤࡨࡩ࡯ࡴࡪࡱࡱࡥࡱࡕࡰࡵ࡫ࡲࡲࡸ࠭঍"), bstack1ll_opy_ (u"ࠪࡥࡷ࡭ࡳࠨ঎")]:
      continue
    options._options[bstack1l111l1l11_opy_] = bstack1ll1llll1l_opy_[bstack1l111l1l11_opy_]
  if bstack1ll_opy_ (u"ࠫࡦࡪࡤࡪࡶ࡬ࡳࡳࡧ࡬ࡐࡲࡷ࡭ࡴࡴࡳࠨএ") in bstack1ll1llll1l_opy_:
    for bstack11lll1l1ll_opy_ in bstack1ll1llll1l_opy_[bstack1ll_opy_ (u"ࠬࡧࡤࡥ࡫ࡷ࡭ࡴࡴࡡ࡭ࡑࡳࡸ࡮ࡵ࡮ࡴࠩঐ")]:
      options.bstack11lll1l1_opy_(
        bstack11lll1l1ll_opy_, bstack1ll1llll1l_opy_[bstack1ll_opy_ (u"࠭ࡡࡥࡦ࡬ࡸ࡮ࡵ࡮ࡢ࡮ࡒࡴࡹ࡯࡯࡯ࡵࠪ঑")][bstack11lll1l1ll_opy_])
  if bstack1ll_opy_ (u"ࠧࡢࡴࡪࡷࠬ঒") in bstack1ll1llll1l_opy_:
    for arg in bstack1ll1llll1l_opy_[bstack1ll_opy_ (u"ࠨࡣࡵ࡫ࡸ࠭ও")]:
      options.add_argument(arg)
def bstack11llll111_opy_(options, caps):
  if not hasattr(options, bstack1ll_opy_ (u"ࠩࡎࡉ࡞࠭ঔ")):
    return
  if options.KEY == bstack1ll_opy_ (u"ࠪ࡫ࡴࡵࡧ࠻ࡥ࡫ࡶࡴࡳࡥࡐࡲࡷ࡭ࡴࡴࡳࠨক"):
    options = bstack1llll1l11_opy_.bstack11lll11111_opy_(bstack1ll1l1ll11_opy_=options, config=CONFIG)
  if options.KEY == bstack1ll_opy_ (u"ࠫ࡬ࡵ࡯ࡨ࠼ࡦ࡬ࡷࡵ࡭ࡦࡑࡳࡸ࡮ࡵ࡮ࡴࠩখ") and options.KEY in caps:
    bstack1l1l11l1l1_opy_(options, caps[bstack1ll_opy_ (u"ࠬ࡭࡯ࡰࡩ࠽ࡧ࡭ࡸ࡯࡮ࡧࡒࡴࡹ࡯࡯࡯ࡵࠪগ")])
  elif options.KEY == bstack1ll_opy_ (u"࠭࡭ࡰࡼ࠽ࡪ࡮ࡸࡥࡧࡱࡻࡓࡵࡺࡩࡰࡰࡶࠫঘ") and options.KEY in caps:
    bstack111111111_opy_(options, caps[bstack1ll_opy_ (u"ࠧ࡮ࡱࡽ࠾࡫࡯ࡲࡦࡨࡲࡼࡔࡶࡴࡪࡱࡱࡷࠬঙ")])
  elif options.KEY == bstack1ll_opy_ (u"ࠨࡵࡤࡪࡦࡸࡩ࠯ࡱࡳࡸ࡮ࡵ࡮ࡴࠩচ") and options.KEY in caps:
    bstack1l11ll1l11_opy_(options, caps[bstack1ll_opy_ (u"ࠩࡶࡥ࡫ࡧࡲࡪ࠰ࡲࡴࡹ࡯࡯࡯ࡵࠪছ")])
  elif options.KEY == bstack1ll_opy_ (u"ࠪࡱࡸࡀࡥࡥࡩࡨࡓࡵࡺࡩࡰࡰࡶࠫজ") and options.KEY in caps:
    bstack11l1l111l1_opy_(options, caps[bstack1ll_opy_ (u"ࠫࡲࡹ࠺ࡦࡦࡪࡩࡔࡶࡴࡪࡱࡱࡷࠬঝ")])
  elif options.KEY == bstack1ll_opy_ (u"ࠬࡹࡥ࠻࡫ࡨࡓࡵࡺࡩࡰࡰࡶࠫঞ") and options.KEY in caps:
    bstack1ll11ll11_opy_(options, caps[bstack1ll_opy_ (u"࠭ࡳࡦ࠼࡬ࡩࡔࡶࡴࡪࡱࡱࡷࠬট")])
def bstack1l1ll111_opy_(caps):
  global bstack11l11l11ll_opy_
  if isinstance(os.environ.get(bstack1ll_opy_ (u"ࠧࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡉࡔࡡࡄࡔࡕࡥࡁࡖࡖࡒࡑࡆ࡚ࡅࠨঠ")), str):
    bstack11l11l11ll_opy_ = eval(os.getenv(bstack1ll_opy_ (u"ࠨࡄࡕࡓ࡜࡙ࡅࡓࡕࡗࡅࡈࡑ࡟ࡊࡕࡢࡅࡕࡖ࡟ࡂࡗࡗࡓࡒࡇࡔࡆࠩড")))
  if bstack11l11l11ll_opy_:
    if bstack11l11ll1l_opy_() < version.parse(bstack1ll_opy_ (u"ࠩ࠵࠲࠸࠴࠰ࠨঢ")):
      return None
    else:
      from appium.options.common.base import AppiumOptions
      options = AppiumOptions().load_capabilities(caps)
      return options
  else:
    browser = bstack1ll_opy_ (u"ࠪࡧ࡭ࡸ࡯࡮ࡧࠪণ")
    if bstack1ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࡓࡧ࡭ࡦࠩত") in caps:
      browser = caps[bstack1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡔࡡ࡮ࡧࠪথ")]
    elif bstack1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࠧদ") in caps:
      browser = caps[bstack1ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࠨধ")]
    browser = str(browser).lower()
    if browser == bstack1ll_opy_ (u"ࠨ࡫ࡳ࡬ࡴࡴࡥࠨন") or browser == bstack1ll_opy_ (u"ࠩ࡬ࡴࡦࡪࠧ঩"):
      browser = bstack1ll_opy_ (u"ࠪࡷࡦ࡬ࡡࡳ࡫ࠪপ")
    if browser == bstack1ll_opy_ (u"ࠫࡸࡧ࡭ࡴࡷࡱ࡫ࠬফ"):
      browser = bstack1ll_opy_ (u"ࠬࡩࡨࡳࡱࡰࡩࠬব")
    if browser not in [bstack1ll_opy_ (u"࠭ࡣࡩࡴࡲࡱࡪ࠭ভ"), bstack1ll_opy_ (u"ࠧࡦࡦࡪࡩࠬম"), bstack1ll_opy_ (u"ࠨ࡫ࡨࠫয"), bstack1ll_opy_ (u"ࠩࡶࡥ࡫ࡧࡲࡪࠩর"), bstack1ll_opy_ (u"ࠪࡪ࡮ࡸࡥࡧࡱࡻࠫ঱")]:
      return None
    try:
      package = bstack1ll_opy_ (u"ࠫࡸ࡫࡬ࡦࡰ࡬ࡹࡲ࠴ࡷࡦࡤࡧࡶ࡮ࡼࡥࡳ࠰ࡾࢁ࠳ࡵࡰࡵ࡫ࡲࡲࡸ࠭ল").format(browser)
      name = bstack1ll_opy_ (u"ࠬࡕࡰࡵ࡫ࡲࡲࡸ࠭঳")
      browser_options = getattr(__import__(package, fromlist=[name]), name)
      options = browser_options()
      if not bstack1ll11111_opy_(options):
        return None
      for bstack1ll11ll1ll_opy_ in caps.keys():
        options.set_capability(bstack1ll11ll1ll_opy_, caps[bstack1ll11ll1ll_opy_])
      bstack11llll111_opy_(options, caps)
      return options
    except Exception as e:
      logger.debug(str(e))
      return None
def bstack1lll1ll1l1_opy_(options, bstack1l1l111ll1_opy_):
  if not bstack1ll11111_opy_(options):
    return
  for bstack1ll11ll1ll_opy_ in bstack1l1l111ll1_opy_.keys():
    if bstack1ll11ll1ll_opy_ in bstack1l1ll111l1_opy_:
      continue
    if bstack1ll11ll1ll_opy_ in options._caps and type(options._caps[bstack1ll11ll1ll_opy_]) in [dict, list]:
      options._caps[bstack1ll11ll1ll_opy_] = update(options._caps[bstack1ll11ll1ll_opy_], bstack1l1l111ll1_opy_[bstack1ll11ll1ll_opy_])
    else:
      options.set_capability(bstack1ll11ll1ll_opy_, bstack1l1l111ll1_opy_[bstack1ll11ll1ll_opy_])
  bstack11llll111_opy_(options, bstack1l1l111ll1_opy_)
  if bstack1ll_opy_ (u"࠭࡭ࡰࡼ࠽ࡨࡪࡨࡵࡨࡩࡨࡶࡆࡪࡤࡳࡧࡶࡷࠬ঴") in options._caps:
    if options._caps[bstack1ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡏࡣࡰࡩࠬ঵")] and options._caps[bstack1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡐࡤࡱࡪ࠭শ")].lower() != bstack1ll_opy_ (u"ࠩࡩ࡭ࡷ࡫ࡦࡰࡺࠪষ"):
      del options._caps[bstack1ll_opy_ (u"ࠪࡱࡴࢀ࠺ࡥࡧࡥࡹ࡬࡭ࡥࡳࡃࡧࡨࡷ࡫ࡳࡴࠩস")]
def bstack11lll111l1_opy_(proxy_config):
  if bstack1ll_opy_ (u"ࠫ࡭ࡺࡴࡱࡵࡓࡶࡴࡾࡹࠨহ") in proxy_config:
    proxy_config[bstack1ll_opy_ (u"ࠬࡹࡳ࡭ࡒࡵࡳࡽࡿࠧ঺")] = proxy_config[bstack1ll_opy_ (u"࠭ࡨࡵࡶࡳࡷࡕࡸ࡯ࡹࡻࠪ঻")]
    del (proxy_config[bstack1ll_opy_ (u"ࠧࡩࡶࡷࡴࡸࡖࡲࡰࡺࡼ়ࠫ")])
  if bstack1ll_opy_ (u"ࠨࡲࡵࡳࡽࡿࡔࡺࡲࡨࠫঽ") in proxy_config and proxy_config[bstack1ll_opy_ (u"ࠩࡳࡶࡴࡾࡹࡕࡻࡳࡩࠬা")].lower() != bstack1ll_opy_ (u"ࠪࡨ࡮ࡸࡥࡤࡶࠪি"):
    proxy_config[bstack1ll_opy_ (u"ࠫࡵࡸ࡯ࡹࡻࡗࡽࡵ࡫ࠧী")] = bstack1ll_opy_ (u"ࠬࡳࡡ࡯ࡷࡤࡰࠬু")
  if bstack1ll_opy_ (u"࠭ࡰࡳࡱࡻࡽࡆࡻࡴࡰࡥࡲࡲ࡫࡯ࡧࡖࡴ࡯ࠫূ") in proxy_config:
    proxy_config[bstack1ll_opy_ (u"ࠧࡱࡴࡲࡼࡾ࡚ࡹࡱࡧࠪৃ")] = bstack1ll_opy_ (u"ࠨࡲࡤࡧࠬৄ")
  return proxy_config
def bstack111llll1ll_opy_(config, proxy):
  from selenium.webdriver.common.proxy import Proxy
  if not bstack1ll_opy_ (u"ࠩࡳࡶࡴࡾࡹࠨ৅") in config:
    return proxy
  config[bstack1ll_opy_ (u"ࠪࡴࡷࡵࡸࡺࠩ৆")] = bstack11lll111l1_opy_(config[bstack1ll_opy_ (u"ࠫࡵࡸ࡯ࡹࡻࠪে")])
  if proxy == None:
    proxy = Proxy(config[bstack1ll_opy_ (u"ࠬࡶࡲࡰࡺࡼࠫৈ")])
  return proxy
def bstack11ll111ll1_opy_(self):
  global CONFIG
  global bstack1ll11l1111_opy_
  try:
    proxy = bstack1ll11ll11l_opy_(CONFIG)
    if proxy:
      if proxy.endswith(bstack1ll_opy_ (u"࠭࠮ࡱࡣࡦࠫ৉")):
        proxies = bstack1ll1ll11l_opy_(proxy, bstack111ll1111_opy_())
        if len(proxies) > 0:
          protocol, bstack11l1ll111l_opy_ = proxies.popitem()
          if bstack1ll_opy_ (u"ࠢ࠻࠱࠲ࠦ৊") in bstack11l1ll111l_opy_:
            return bstack11l1ll111l_opy_
          else:
            return bstack1ll_opy_ (u"ࠣࡪࡷࡸࡵࡀ࠯࠰ࠤো") + bstack11l1ll111l_opy_
      else:
        return proxy
  except Exception as e:
    logger.error(bstack1ll_opy_ (u"ࠤࡈࡶࡷࡵࡲࠡ࡫ࡱࠤࡸ࡫ࡴࡵ࡫ࡱ࡫ࠥࡶࡲࡰࡺࡼࠤࡺࡸ࡬ࠡ࠼ࠣࡿࢂࠨৌ").format(str(e)))
  return bstack1ll11l1111_opy_(self)
def bstack111l1111_opy_():
  global CONFIG
  return bstack111l1l11l_opy_(CONFIG) and bstack11ll1l11l1_opy_() and bstack11l11111l1_opy_() >= version.parse(bstack1l11111ll1_opy_)
def bstack1ll1lllll_opy_():
  global CONFIG
  return (bstack1ll_opy_ (u"ࠪ࡬ࡹࡺࡰࡑࡴࡲࡼࡾ্࠭") in CONFIG or bstack1ll_opy_ (u"ࠫ࡭ࡺࡴࡱࡵࡓࡶࡴࡾࡹࠨৎ") in CONFIG) and bstack1111l1l1l_opy_()
def bstack11lllll1_opy_(config):
  bstack111lll111_opy_ = {}
  if bstack1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷ࡙ࡴࡢࡥ࡮ࡐࡴࡩࡡ࡭ࡑࡳࡸ࡮ࡵ࡮ࡴࠩ৏") in config:
    bstack111lll111_opy_ = config[bstack1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡓࡵࡣࡦ࡯ࡑࡵࡣࡢ࡮ࡒࡴࡹ࡯࡯࡯ࡵࠪ৐")]
  if bstack1ll_opy_ (u"ࠧ࡭ࡱࡦࡥࡱࡕࡰࡵ࡫ࡲࡲࡸ࠭৑") in config:
    bstack111lll111_opy_ = config[bstack1ll_opy_ (u"ࠨ࡮ࡲࡧࡦࡲࡏࡱࡶ࡬ࡳࡳࡹࠧ৒")]
  proxy = bstack1ll11ll11l_opy_(config)
  if proxy:
    if proxy.endswith(bstack1ll_opy_ (u"ࠩ࠱ࡴࡦࡩࠧ৓")) and os.path.isfile(proxy):
      bstack111lll111_opy_[bstack1ll_opy_ (u"ࠪ࠱ࡵࡧࡣ࠮ࡨ࡬ࡰࡪ࠭৔")] = proxy
    else:
      parsed_url = None
      if proxy.endswith(bstack1ll_opy_ (u"ࠫ࠳ࡶࡡࡤࠩ৕")):
        proxies = bstack11ll11llll_opy_(config, bstack111ll1111_opy_())
        if len(proxies) > 0:
          protocol, bstack11l1ll111l_opy_ = proxies.popitem()
          if bstack1ll_opy_ (u"ࠧࡀ࠯࠰ࠤ৖") in bstack11l1ll111l_opy_:
            parsed_url = urlparse(bstack11l1ll111l_opy_)
          else:
            parsed_url = urlparse(protocol + bstack1ll_opy_ (u"ࠨ࠺࠰࠱ࠥৗ") + bstack11l1ll111l_opy_)
      else:
        parsed_url = urlparse(proxy)
      if parsed_url and parsed_url.hostname: bstack111lll111_opy_[bstack1ll_opy_ (u"ࠧࡱࡴࡲࡼࡾࡎ࡯ࡴࡶࠪ৘")] = str(parsed_url.hostname)
      if parsed_url and parsed_url.port: bstack111lll111_opy_[bstack1ll_opy_ (u"ࠨࡲࡵࡳࡽࡿࡐࡰࡴࡷࠫ৙")] = str(parsed_url.port)
      if parsed_url and parsed_url.username: bstack111lll111_opy_[bstack1ll_opy_ (u"ࠩࡳࡶࡴࡾࡹࡖࡵࡨࡶࠬ৚")] = str(parsed_url.username)
      if parsed_url and parsed_url.password: bstack111lll111_opy_[bstack1ll_opy_ (u"ࠪࡴࡷࡵࡸࡺࡒࡤࡷࡸ࠭৛")] = str(parsed_url.password)
  return bstack111lll111_opy_
def bstack1lll111lll_opy_(config):
  if bstack1ll_opy_ (u"ࠫࡹ࡫ࡳࡵࡅࡲࡲࡹ࡫ࡸࡵࡑࡳࡸ࡮ࡵ࡮ࡴࠩড়") in config:
    return config[bstack1ll_opy_ (u"ࠬࡺࡥࡴࡶࡆࡳࡳࡺࡥࡹࡶࡒࡴࡹ࡯࡯࡯ࡵࠪঢ়")]
  return {}
def bstack1l1l1111ll_opy_(caps):
  global bstack1l1l1ll1l1_opy_
  if bstack1ll_opy_ (u"࠭ࡢࡴࡶࡤࡧࡰࡀ࡯ࡱࡶ࡬ࡳࡳࡹࠧ৞") in caps:
    caps[bstack1ll_opy_ (u"ࠧࡣࡵࡷࡥࡨࡱ࠺ࡰࡲࡷ࡭ࡴࡴࡳࠨয়")][bstack1ll_opy_ (u"ࠨ࡮ࡲࡧࡦࡲࠧৠ")] = True
    if bstack1l1l1ll1l1_opy_:
      caps[bstack1ll_opy_ (u"ࠩࡥࡷࡹࡧࡣ࡬࠼ࡲࡴࡹ࡯࡯࡯ࡵࠪৡ")][bstack1ll_opy_ (u"ࠪࡰࡴࡩࡡ࡭ࡋࡧࡩࡳࡺࡩࡧ࡫ࡨࡶࠬৢ")] = bstack1l1l1ll1l1_opy_
  else:
    caps[bstack1ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭࠱ࡰࡴࡩࡡ࡭ࠩৣ")] = True
    if bstack1l1l1ll1l1_opy_:
      caps[bstack1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮࠲ࡱࡵࡣࡢ࡮ࡌࡨࡪࡴࡴࡪࡨ࡬ࡩࡷ࠭৤")] = bstack1l1l1ll1l1_opy_
@measure(event_name=EVENTS.bstack1ll1l1llll_opy_, stage=STAGE.bstack1l1lll1ll1_opy_, bstack1l1l11ll_opy_=bstack1llll1111l_opy_)
def bstack1ll1l1l11_opy_():
  global CONFIG
  if not bstack11111l1l_opy_(CONFIG) or cli.is_enabled(CONFIG):
    return
  if bstack1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯ࡑࡵࡣࡢ࡮ࠪ৥") in CONFIG and bstack11l11lllll_opy_(CONFIG[bstack1ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰࡒ࡯ࡤࡣ࡯ࠫ০")]):
    if (
      bstack1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡕࡷࡥࡨࡱࡌࡰࡥࡤࡰࡔࡶࡴࡪࡱࡱࡷࠬ১") in CONFIG
      and bstack11l11lllll_opy_(CONFIG[bstack1ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡖࡸࡦࡩ࡫ࡍࡱࡦࡥࡱࡕࡰࡵ࡫ࡲࡲࡸ࠭২")].get(bstack1ll_opy_ (u"ࠪࡷࡰ࡯ࡰࡃ࡫ࡱࡥࡷࡿࡉ࡯࡫ࡷ࡭ࡦࡲࡩࡴࡣࡷ࡭ࡴࡴࠧ৩")))
    ):
      logger.debug(bstack1ll_opy_ (u"ࠦࡑࡵࡣࡢ࡮ࠣࡦ࡮ࡴࡡࡳࡻࠣࡲࡴࡺࠠࡴࡶࡤࡶࡹ࡫ࡤࠡࡣࡶࠤࡸࡱࡩࡱࡄ࡬ࡲࡦࡸࡹࡊࡰ࡬ࡸ࡮ࡧ࡬ࡪࡵࡤࡸ࡮ࡵ࡮ࠡ࡫ࡶࠤࡪࡴࡡࡣ࡮ࡨࡨࠧ৪"))
      return
    bstack111lll111_opy_ = bstack11lllll1_opy_(CONFIG)
    bstack1ll1ll1l11_opy_(CONFIG[bstack1ll_opy_ (u"ࠬࡧࡣࡤࡧࡶࡷࡐ࡫ࡹࠨ৫")], bstack111lll111_opy_)
def bstack1ll1ll1l11_opy_(key, bstack111lll111_opy_):
  global bstack1l111111l1_opy_
  logger.info(bstack1llll111ll_opy_)
  try:
    bstack1l111111l1_opy_ = Local()
    bstack11lll1llll_opy_ = {bstack1ll_opy_ (u"࠭࡫ࡦࡻࠪ৬"): key}
    bstack11lll1llll_opy_.update(bstack111lll111_opy_)
    logger.debug(bstack11l1l1ll11_opy_.format(str(bstack11lll1llll_opy_)).replace(key, bstack1ll_opy_ (u"ࠧ࡜ࡔࡈࡈࡆࡉࡔࡆࡆࡠࠫ৭")))
    bstack1l111111l1_opy_.start(**bstack11lll1llll_opy_)
    if bstack1l111111l1_opy_.isRunning():
      logger.info(bstack1l11l1111l_opy_)
  except Exception as e:
    bstack1ll1l1lll_opy_(bstack11l1111l1l_opy_.format(str(e)))
def bstack111l1llll_opy_():
  global bstack1l111111l1_opy_
  if bstack1l111111l1_opy_.isRunning():
    logger.info(bstack1ll1lll1ll_opy_)
    bstack1l111111l1_opy_.stop()
  bstack1l111111l1_opy_ = None
def bstack111ll11l_opy_(bstack11ll111l1l_opy_=[]):
  global CONFIG
  bstack1lll11111_opy_ = []
  bstack111l1l1l_opy_ = [bstack1ll_opy_ (u"ࠨࡱࡶࠫ৮"), bstack1ll_opy_ (u"ࠩࡲࡷ࡛࡫ࡲࡴ࡫ࡲࡲࠬ৯"), bstack1ll_opy_ (u"ࠪࡨࡪࡼࡩࡤࡧࡑࡥࡲ࡫ࠧৰ"), bstack1ll_opy_ (u"ࠫࡵࡲࡡࡵࡨࡲࡶࡲ࡜ࡥࡳࡵ࡬ࡳࡳ࠭ৱ"), bstack1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡔࡡ࡮ࡧࠪ৲"), bstack1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡖࡦࡴࡶ࡭ࡴࡴࠧ৳")]
  try:
    for err in bstack11ll111l1l_opy_:
      bstack11llll1l1l_opy_ = {}
      for k in bstack111l1l1l_opy_:
        val = CONFIG[bstack1ll_opy_ (u"ࠧࡱ࡮ࡤࡸ࡫ࡵࡲ࡮ࡵࠪ৴")][int(err[bstack1ll_opy_ (u"ࠨ࡫ࡱࡨࡪࡾࠧ৵")])].get(k)
        if val:
          bstack11llll1l1l_opy_[k] = val
      if(err[bstack1ll_opy_ (u"ࠩࡨࡶࡷࡵࡲࠨ৶")] != bstack1ll_opy_ (u"ࠪࠫ৷")):
        bstack11llll1l1l_opy_[bstack1ll_opy_ (u"ࠫࡹ࡫ࡳࡵࡵࠪ৸")] = {
          err[bstack1ll_opy_ (u"ࠬࡴࡡ࡮ࡧࠪ৹")]: err[bstack1ll_opy_ (u"࠭ࡥࡳࡴࡲࡶࠬ৺")]
        }
        bstack1lll11111_opy_.append(bstack11llll1l1l_opy_)
  except Exception as e:
    logger.debug(bstack1ll_opy_ (u"ࠧࡆࡴࡵࡳࡷࠦࡩ࡯ࠢࡩࡳࡷࡳࡡࡵࡶ࡬ࡲ࡬ࠦࡤࡢࡶࡤࠤ࡫ࡵࡲࠡࡧࡹࡩࡳࡺ࠺ࠡࠩ৻") + str(e))
  finally:
    return bstack1lll11111_opy_
def bstack11l1l1lll_opy_(file_name):
  bstack1lll1l11l_opy_ = []
  try:
    bstack11ll111lll_opy_ = os.path.join(tempfile.gettempdir(), file_name)
    if os.path.exists(bstack11ll111lll_opy_):
      with open(bstack11ll111lll_opy_) as f:
        bstack1lll1lll1l_opy_ = json.load(f)
        bstack1lll1l11l_opy_ = bstack1lll1lll1l_opy_
      os.remove(bstack11ll111lll_opy_)
    return bstack1lll1l11l_opy_
  except Exception as e:
    logger.debug(bstack1ll_opy_ (u"ࠨࡇࡵࡶࡴࡸࠠࡪࡰࠣࡪ࡮ࡴࡤࡪࡰࡪࠤࡪࡸࡲࡰࡴࠣࡰ࡮ࡹࡴ࠻ࠢࠪৼ") + str(e))
    return bstack1lll1l11l_opy_
def bstack1lll1l1l_opy_():
  try:
      from bstack_utils.constants import bstack11l11l11l_opy_, EVENTS
      from bstack_utils.helper import bstack1l111111_opy_, get_host_info, bstack1ll1l1l111_opy_
      from datetime import datetime
      from filelock import FileLock
      bstack1lll11l11l_opy_ = os.path.join(os.getcwd(), bstack1ll_opy_ (u"ࠩ࡯ࡳ࡬࠭৽"), bstack1ll_opy_ (u"ࠪ࡯ࡪࡿ࠭࡮ࡧࡷࡶ࡮ࡩࡳ࠯࡬ࡶࡳࡳ࠭৾"))
      lock = FileLock(bstack1lll11l11l_opy_+bstack1ll_opy_ (u"ࠦ࠳ࡲ࡯ࡤ࡭ࠥ৿"))
      def bstack1ll1ll111l_opy_():
          try:
              with lock:
                  with open(bstack1lll11l11l_opy_, bstack1ll_opy_ (u"ࠧࡸࠢ਀"), encoding=bstack1ll_opy_ (u"ࠨࡵࡵࡨ࠰࠼ࠧਁ")) as file:
                      data = json.load(file)
                      config = {
                          bstack1ll_opy_ (u"ࠢࡩࡧࡤࡨࡪࡸࡳࠣਂ"): {
                              bstack1ll_opy_ (u"ࠣࡅࡲࡲࡹ࡫࡮ࡵ࠯ࡗࡽࡵ࡫ࠢਃ"): bstack1ll_opy_ (u"ࠤࡤࡴࡵࡲࡩࡤࡣࡷ࡭ࡴࡴ࠯࡫ࡵࡲࡲࠧ਄"),
                          }
                      }
                      bstack1lll1l1111_opy_ = datetime.utcnow()
                      bstack1l11l1111_opy_ = bstack1lll1l1111_opy_.strftime(bstack1ll_opy_ (u"ࠥࠩ࡞࠳ࠥ࡮࠯ࠨࡨ࡙ࠫࡈ࠻ࠧࡐ࠾࡙ࠪ࠮ࠦࡨ࡙࡙ࠣࡉࠢਅ"))
                      bstack11l111l11l_opy_ = os.environ.get(bstack1ll_opy_ (u"ࠫࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡘࡊ࡙ࡔࡉࡗࡅࡣ࡚࡛ࡉࡅࠩਆ")) if os.environ.get(bstack1ll_opy_ (u"ࠬࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣ࡙ࡋࡓࡕࡊࡘࡆࡤ࡛ࡕࡊࡆࠪਇ")) else bstack1ll1l1l111_opy_.get_property(bstack1ll_opy_ (u"ࠨࡳࡥ࡭ࡕࡹࡳࡏࡤࠣਈ"))
                      payload = {
                          bstack1ll_opy_ (u"ࠢࡦࡸࡨࡲࡹࡥࡴࡺࡲࡨࠦਉ"): bstack1ll_opy_ (u"ࠣࡵࡧ࡯ࡤ࡫ࡶࡦࡰࡷࡷࠧਊ"),
                          bstack1ll_opy_ (u"ࠤࡧࡥࡹࡧࠢ਋"): {
                              bstack1ll_opy_ (u"ࠥࡸࡪࡹࡴࡩࡷࡥࡣࡺࡻࡩࡥࠤ਌"): bstack11l111l11l_opy_,
                              bstack1ll_opy_ (u"ࠦࡨࡸࡥࡢࡶࡨࡨࡤࡪࡡࡺࠤ਍"): bstack1l11l1111_opy_,
                              bstack1ll_opy_ (u"ࠧ࡫ࡶࡦࡰࡷࡣࡳࡧ࡭ࡦࠤ਎"): bstack1ll_opy_ (u"ࠨࡓࡅࡍࡉࡩࡦࡺࡵࡳࡧࡓࡩࡷ࡬࡯ࡳ࡯ࡤࡲࡨ࡫ࠢਏ"),
                              bstack1ll_opy_ (u"ࠢࡦࡸࡨࡲࡹࡥࡪࡴࡱࡱࠦਐ"): {
                                  bstack1ll_opy_ (u"ࠣ࡯ࡨࡥࡸࡻࡲࡦࡵࠥ਑"): data,
                                  bstack1ll_opy_ (u"ࠤࡶࡨࡰࡘࡵ࡯ࡋࡧࠦ਒"): bstack1ll1l1l111_opy_.get_property(bstack1ll_opy_ (u"ࠥࡷࡩࡱࡒࡶࡰࡌࡨࠧਓ"))
                              },
                              bstack1ll_opy_ (u"ࠦࡺࡹࡥࡳࡡࡧࡥࡹࡧࠢਔ"): bstack1ll1l1l111_opy_.get_property(bstack1ll_opy_ (u"ࠧࡻࡳࡦࡴࡑࡥࡲ࡫ࠢਕ")),
                              bstack1ll_opy_ (u"ࠨࡨࡰࡵࡷࡣ࡮ࡴࡦࡰࠤਖ"): get_host_info()
                          }
                      }
                      bstack1lllllll1l_opy_ = bstack11l1111l1_opy_(cli.config, [bstack1ll_opy_ (u"ࠢࡢࡲ࡬ࡷࠧਗ"), bstack1ll_opy_ (u"ࠣࡧࡧࡷࡎࡴࡳࡵࡴࡸࡱࡪࡴࡴࡢࡶ࡬ࡳࡳࠨਘ"), bstack1ll_opy_ (u"ࠤࡤࡴ࡮ࠨਙ")], bstack11l11l11l_opy_)
                      response = bstack1l111111_opy_(bstack1ll_opy_ (u"ࠥࡔࡔ࡙ࡔࠣਚ"), bstack1lllllll1l_opy_, payload, config)
                      if(response.status_code >= 200 and response.status_code < 300):
                          logger.debug(bstack1ll_opy_ (u"ࠦࡉࡧࡴࡢࠢࡶࡩࡳࡺࠠࡴࡷࡦࡧࡪࡹࡳࡧࡷ࡯ࡰࡾࠦࡴࡰࠢࡾࢁࠥࡽࡩࡵࡪࠣࡨࡦࡺࡡࠡࡽࢀࠦਛ").format(bstack11l11l11l_opy_, payload))
                      else:
                          logger.debug(bstack1ll_opy_ (u"ࠧࡘࡥࡲࡷࡨࡷࡹࠦࡦࡢ࡫࡯ࡩࡩࠦࡦࡰࡴࠣࡿࢂࠦࡷࡪࡶ࡫ࠤࡩࡧࡴࡢࠢࡾࢁࠧਜ").format(bstack11l11l11l_opy_, payload))
          except Exception as e:
              logger.debug(bstack1ll_opy_ (u"ࠨࡆࡢ࡫࡯ࡩࡩࠦࡴࡰࠢࡶࡩࡳࡪࠠ࡬ࡧࡼࠤࡲ࡫ࡴࡳ࡫ࡦࡷࠥࡪࡡࡵࡣࠣࡻ࡮ࡺࡨࠡࡧࡵࡶࡴࡸࠠࡼࡿࠥਝ").format(e))
      bstack1ll1ll111l_opy_()
      bstack1l1l1l1ll1_opy_(bstack1lll11l11l_opy_, logger)
  except:
    pass
def bstack11lll1l11_opy_():
  global bstack111lllllll_opy_
  global bstack1llll11lll_opy_
  global bstack1lll11ll_opy_
  global bstack1111ll11l_opy_
  global bstack11l1l11l11_opy_
  global bstack1l1lll1l1_opy_
  global CONFIG
  bstack11ll11l11l_opy_ = os.environ.get(bstack1ll_opy_ (u"ࠧࡇࡔࡄࡑࡊ࡝ࡏࡓࡍࡢ࡙ࡘࡋࡄࠨਞ"))
  if bstack11ll11l11l_opy_ in [bstack1ll_opy_ (u"ࠨࡴࡲࡦࡴࡺࠧਟ"), bstack1ll_opy_ (u"ࠩࡳࡥࡧࡵࡴࠨਠ")]:
    bstack1lllll111_opy_()
  percy.shutdown()
  if bstack111lllllll_opy_:
    logger.warning(bstack11l1ll1l_opy_.format(str(bstack111lllllll_opy_)))
  else:
    try:
      bstack11lllll111_opy_ = bstack1l11lll1ll_opy_(bstack1ll_opy_ (u"ࠪ࠲ࡧࡹࡴࡢࡥ࡮࠱ࡨࡵ࡮ࡧ࡫ࡪ࠲࡯ࡹ࡯࡯ࠩਡ"), logger)
      if bstack11lllll111_opy_.get(bstack1ll_opy_ (u"ࠫࡳࡻࡤࡨࡧࡢࡰࡴࡩࡡ࡭ࠩਢ")) and bstack11lllll111_opy_.get(bstack1ll_opy_ (u"ࠬࡴࡵࡥࡩࡨࡣࡱࡵࡣࡢ࡮ࠪਣ")).get(bstack1ll_opy_ (u"࠭ࡨࡰࡵࡷࡲࡦࡳࡥࠨਤ")):
        logger.warning(bstack11l1ll1l_opy_.format(str(bstack11lllll111_opy_[bstack1ll_opy_ (u"ࠧ࡯ࡷࡧ࡫ࡪࡥ࡬ࡰࡥࡤࡰࠬਥ")][bstack1ll_opy_ (u"ࠨࡪࡲࡷࡹࡴࡡ࡮ࡧࠪਦ")])))
    except Exception as e:
      logger.error(e)
  if cli.is_running():
    bstack111lll1l_opy_.invoke(bstack1lll1lll_opy_.bstack11llll1ll_opy_)
  logger.info(bstack1l1ll1l1ll_opy_)
  global bstack1l111111l1_opy_
  if bstack1l111111l1_opy_:
    bstack111l1llll_opy_()
  try:
    with bstack1lll11l1l_opy_:
      bstack1ll1llllll_opy_ = bstack1llll11lll_opy_.copy()
    for driver in bstack1ll1llllll_opy_:
      driver.quit()
  except Exception as e:
    pass
  logger.info(bstack1111llll_opy_)
  if bstack1l1lll1l1_opy_ == bstack1ll_opy_ (u"ࠩࡵࡳࡧࡵࡴࠨਧ"):
    bstack11l1l11l11_opy_ = bstack11l1l1lll_opy_(bstack1ll_opy_ (u"ࠪࡶࡴࡨ࡯ࡵࡡࡨࡶࡷࡵࡲࡠ࡮࡬ࡷࡹ࠴ࡪࡴࡱࡱࠫਨ"))
  if bstack1l1lll1l1_opy_ == bstack1ll_opy_ (u"ࠫࡵࡿࡴࡦࡵࡷࠫ਩") and len(bstack1111ll11l_opy_) == 0:
    bstack1111ll11l_opy_ = bstack11l1l1lll_opy_(bstack1ll_opy_ (u"ࠬࡶࡷࡠࡲࡼࡸࡪࡹࡴࡠࡧࡵࡶࡴࡸ࡟࡭࡫ࡶࡸ࠳ࡰࡳࡰࡰࠪਪ"))
    if len(bstack1111ll11l_opy_) == 0:
      bstack1111ll11l_opy_ = bstack11l1l1lll_opy_(bstack1ll_opy_ (u"࠭ࡰࡺࡶࡨࡷࡹࡥࡰࡱࡲࡢࡩࡷࡸ࡯ࡳࡡ࡯࡭ࡸࡺ࠮࡫ࡵࡲࡲࠬਫ"))
  bstack11l111111_opy_ = bstack1ll_opy_ (u"ࠧࠨਬ")
  if len(bstack1lll11ll_opy_) > 0:
    bstack11l111111_opy_ = bstack111ll11l_opy_(bstack1lll11ll_opy_)
  elif len(bstack1111ll11l_opy_) > 0:
    bstack11l111111_opy_ = bstack111ll11l_opy_(bstack1111ll11l_opy_)
  elif len(bstack11l1l11l11_opy_) > 0:
    bstack11l111111_opy_ = bstack111ll11l_opy_(bstack11l1l11l11_opy_)
  elif len(bstack1l11l1ll11_opy_) > 0:
    bstack11l111111_opy_ = bstack111ll11l_opy_(bstack1l11l1ll11_opy_)
  if bool(bstack11l111111_opy_):
    bstack1111111ll_opy_(bstack11l111111_opy_)
  else:
    bstack1111111ll_opy_()
  bstack1l1l1l1ll1_opy_(bstack11ll1ll1_opy_, logger)
  if bstack11ll11l11l_opy_ not in [bstack1ll_opy_ (u"ࠨࡴࡲࡦࡴࡺ࠭ࡪࡰࡷࡩࡷࡴࡡ࡭ࠩਭ")]:
    bstack1lll1l1l_opy_()
  bstack11l1l1lll1_opy_.bstack11ll1111l_opy_(CONFIG)
  if len(bstack11l1l11l11_opy_) > 0:
    sys.exit(len(bstack11l1l11l11_opy_))
def bstack1lll11lll1_opy_(bstack1l11ll1l_opy_, frame):
  global bstack1ll1l1l111_opy_
  logger.error(bstack1l1ll1ll_opy_)
  bstack1ll1l1l111_opy_.bstack111ll1ll1_opy_(bstack1ll_opy_ (u"ࠩࡶࡨࡰࡑࡩ࡭࡮ࡑࡳࠬਮ"), bstack1l11ll1l_opy_)
  if hasattr(signal, bstack1ll_opy_ (u"ࠪࡗ࡮࡭࡮ࡢ࡮ࡶࠫਯ")):
    bstack1ll1l1l111_opy_.bstack111ll1ll1_opy_(bstack1ll_opy_ (u"ࠫࡸࡪ࡫ࡌ࡫࡯ࡰࡘ࡯ࡧ࡯ࡣ࡯ࠫਰ"), signal.Signals(bstack1l11ll1l_opy_).name)
  else:
    bstack1ll1l1l111_opy_.bstack111ll1ll1_opy_(bstack1ll_opy_ (u"ࠬࡹࡤ࡬ࡍ࡬ࡰࡱ࡙ࡩࡨࡰࡤࡰࠬ਱"), bstack1ll_opy_ (u"࠭ࡓࡊࡉࡘࡒࡐࡔࡏࡘࡐࠪਲ"))
  if cli.is_running():
    bstack111lll1l_opy_.invoke(bstack1lll1lll_opy_.bstack11llll1ll_opy_)
  bstack11ll11l11l_opy_ = os.environ.get(bstack1ll_opy_ (u"ࠧࡇࡔࡄࡑࡊ࡝ࡏࡓࡍࡢ࡙ࡘࡋࡄࠨਲ਼"))
  if bstack11ll11l11l_opy_ == bstack1ll_opy_ (u"ࠨࡲࡼࡸࡪࡹࡴࠨ਴") and not cli.is_enabled(CONFIG):
    bstack1lll1111l_opy_.stop(bstack1ll1l1l111_opy_.get_property(bstack1ll_opy_ (u"ࠩࡶࡨࡰࡑࡩ࡭࡮ࡖ࡭࡬ࡴࡡ࡭ࠩਵ")))
  bstack11lll1l11_opy_()
  sys.exit(1)
def bstack1ll1l1lll_opy_(err):
  logger.critical(bstack11l1lll11l_opy_.format(str(err)))
  bstack1111111ll_opy_(bstack11l1lll11l_opy_.format(str(err)), True)
  atexit.unregister(bstack11lll1l11_opy_)
  bstack1lllll111_opy_()
  sys.exit(1)
def bstack1llll1ll1_opy_(error, message):
  logger.critical(str(error))
  logger.critical(message)
  bstack1111111ll_opy_(message, True)
  atexit.unregister(bstack11lll1l11_opy_)
  bstack1lllll111_opy_()
  sys.exit(1)
def bstack1l11l1ll1l_opy_():
  global CONFIG
  global bstack111lll11l1_opy_
  global bstack11lll11l1_opy_
  global bstack11l111llll_opy_
  CONFIG = bstack11ll1111l1_opy_()
  load_dotenv(CONFIG.get(bstack1ll_opy_ (u"ࠪࡩࡳࡼࡆࡪ࡮ࡨࠫਸ਼")))
  bstack1llll11111_opy_()
  bstack1ll1l1l11l_opy_()
  CONFIG = bstack11l1ll1l1l_opy_(CONFIG)
  update(CONFIG, bstack11lll11l1_opy_)
  update(CONFIG, bstack111lll11l1_opy_)
  if not cli.is_enabled(CONFIG):
    CONFIG = bstack11lll1l1l_opy_(CONFIG)
  bstack11l111llll_opy_ = bstack11111l1l_opy_(CONFIG)
  os.environ[bstack1ll_opy_ (u"ࠫࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡅ࡚࡚ࡏࡎࡃࡗࡍࡔࡔࠧ਷")] = bstack11l111llll_opy_.__str__().lower()
  bstack1ll1l1l111_opy_.bstack111ll1ll1_opy_(bstack1ll_opy_ (u"ࠬࡨࡳࡵࡣࡦ࡯ࡤࡹࡥࡴࡵ࡬ࡳࡳ࠭ਸ"), bstack11l111llll_opy_)
  if (bstack1ll_opy_ (u"࠭ࡢࡶ࡫࡯ࡨࡓࡧ࡭ࡦࠩਹ") in CONFIG and bstack1ll_opy_ (u"ࠧࡣࡷ࡬ࡰࡩࡔࡡ࡮ࡧࠪ਺") in bstack111lll11l1_opy_) or (
          bstack1ll_opy_ (u"ࠨࡤࡸ࡭ࡱࡪࡎࡢ࡯ࡨࠫ਻") in CONFIG and bstack1ll_opy_ (u"ࠩࡥࡹ࡮ࡲࡤࡏࡣࡰࡩ਼ࠬ") not in bstack11lll11l1_opy_):
    if os.getenv(bstack1ll_opy_ (u"ࠪࡆࡘ࡚ࡁࡄࡍࡢࡇࡔࡓࡂࡊࡐࡈࡈࡤࡈࡕࡊࡎࡇࡣࡎࡊࠧ਽")):
      CONFIG[bstack1ll_opy_ (u"ࠫࡧࡻࡩ࡭ࡦࡌࡨࡪࡴࡴࡪࡨ࡬ࡩࡷ࠭ਾ")] = os.getenv(bstack1ll_opy_ (u"ࠬࡈࡓࡕࡃࡆࡏࡤࡉࡏࡎࡄࡌࡒࡊࡊ࡟ࡃࡗࡌࡐࡉࡥࡉࡅࠩਿ"))
    else:
      if not CONFIG.get(bstack1ll_opy_ (u"ࠨࡦࡳࡣࡰࡩࡼࡵࡲ࡬ࠤੀ"), bstack1ll_opy_ (u"ࠢࠣੁ")) in bstack111l11ll1_opy_:
        bstack11l11l1lll_opy_()
  elif (bstack1ll_opy_ (u"ࠨࡤࡸ࡭ࡱࡪࡎࡢ࡯ࡨࠫੂ") not in CONFIG and bstack1ll_opy_ (u"ࠩࡥࡹ࡮ࡲࡤࡊࡦࡨࡲࡹ࡯ࡦࡪࡧࡵࠫ੃") in CONFIG) or (
          bstack1ll_opy_ (u"ࠪࡦࡺ࡯࡬ࡥࡐࡤࡱࡪ࠭੄") in bstack11lll11l1_opy_ and bstack1ll_opy_ (u"ࠫࡧࡻࡩ࡭ࡦࡑࡥࡲ࡫ࠧ੅") not in bstack111lll11l1_opy_):
    del (CONFIG[bstack1ll_opy_ (u"ࠬࡨࡵࡪ࡮ࡧࡍࡩ࡫࡮ࡵ࡫ࡩ࡭ࡪࡸࠧ੆")])
  if bstack1l11l1ll1_opy_(CONFIG):
    bstack1ll1l1lll_opy_(bstack1l11lll11l_opy_)
  Config.bstack11lll1111_opy_().bstack111ll1ll1_opy_(bstack1ll_opy_ (u"ࠨࡵࡴࡧࡵࡒࡦࡳࡥࠣੇ"), CONFIG[bstack1ll_opy_ (u"ࠧࡶࡵࡨࡶࡓࡧ࡭ࡦࠩੈ")])
  bstack1l1llll1l1_opy_()
  bstack1l1l1111_opy_()
  if bstack11l11l11ll_opy_ and not CONFIG.get(bstack1ll_opy_ (u"ࠣࡨࡵࡥࡲ࡫ࡷࡰࡴ࡮ࠦ੉"), bstack1ll_opy_ (u"ࠤࠥ੊")) in bstack111l11ll1_opy_:
    CONFIG[bstack1ll_opy_ (u"ࠪࡥࡵࡶࠧੋ")] = bstack1ll1llll_opy_(CONFIG)
    logger.info(bstack111lllll11_opy_.format(CONFIG[bstack1ll_opy_ (u"ࠫࡦࡶࡰࠨੌ")]))
  if not bstack11l111llll_opy_:
    CONFIG[bstack1ll_opy_ (u"ࠬࡶ࡬ࡢࡶࡩࡳࡷࡳࡳࠨ੍")] = [{}]
def bstack1l1111lll1_opy_(config, bstack11ll11ll1l_opy_):
  global CONFIG
  global bstack11l11l11ll_opy_
  CONFIG = config
  bstack11l11l11ll_opy_ = bstack11ll11ll1l_opy_
def bstack1l1l1111_opy_():
  global CONFIG
  global bstack11l11l11ll_opy_
  if bstack1ll_opy_ (u"࠭ࡡࡱࡲࠪ੎") in CONFIG:
    try:
      from appium import version
    except Exception as e:
      bstack1llll1ll1_opy_(e, bstack11l1111lll_opy_)
    bstack11l11l11ll_opy_ = True
    bstack1ll1l1l111_opy_.bstack111ll1ll1_opy_(bstack1ll_opy_ (u"ࠧࡢࡲࡳࡣࡦࡻࡴࡰ࡯ࡤࡸࡪ࠭੏"), True)
def bstack1ll1llll_opy_(config):
  bstack1llllll1l_opy_ = bstack1ll_opy_ (u"ࠨࠩ੐")
  app = config[bstack1ll_opy_ (u"ࠩࡤࡴࡵ࠭ੑ")]
  if isinstance(app, str):
    if os.path.splitext(app)[1] in bstack11ll1l111l_opy_:
      if os.path.exists(app):
        bstack1llllll1l_opy_ = bstack1ll111l1ll_opy_(config, app)
      elif bstack1l1ll1lll_opy_(app):
        bstack1llllll1l_opy_ = app
      else:
        bstack1ll1l1lll_opy_(bstack11ll11ll11_opy_.format(app))
    else:
      if bstack1l1ll1lll_opy_(app):
        bstack1llllll1l_opy_ = app
      elif os.path.exists(app):
        bstack1llllll1l_opy_ = bstack1ll111l1ll_opy_(app)
      else:
        bstack1ll1l1lll_opy_(bstack1ll111ll_opy_)
  else:
    if len(app) > 2:
      bstack1ll1l1lll_opy_(bstack111l1ll11_opy_)
    elif len(app) == 2:
      if bstack1ll_opy_ (u"ࠪࡴࡦࡺࡨࠨ੒") in app and bstack1ll_opy_ (u"ࠫࡨࡻࡳࡵࡱࡰࡣ࡮ࡪࠧ੓") in app:
        if os.path.exists(app[bstack1ll_opy_ (u"ࠬࡶࡡࡵࡪࠪ੔")]):
          bstack1llllll1l_opy_ = bstack1ll111l1ll_opy_(config, app[bstack1ll_opy_ (u"࠭ࡰࡢࡶ࡫ࠫ੕")], app[bstack1ll_opy_ (u"ࠧࡤࡷࡶࡸࡴࡳ࡟ࡪࡦࠪ੖")])
        else:
          bstack1ll1l1lll_opy_(bstack11ll11ll11_opy_.format(app))
      else:
        bstack1ll1l1lll_opy_(bstack111l1ll11_opy_)
    else:
      for key in app:
        if key in bstack1l11ll111l_opy_:
          if key == bstack1ll_opy_ (u"ࠨࡲࡤࡸ࡭࠭੗"):
            if os.path.exists(app[key]):
              bstack1llllll1l_opy_ = bstack1ll111l1ll_opy_(config, app[key])
            else:
              bstack1ll1l1lll_opy_(bstack11ll11ll11_opy_.format(app))
          else:
            bstack1llllll1l_opy_ = app[key]
        else:
          bstack1ll1l1lll_opy_(bstack111l111l1_opy_)
  return bstack1llllll1l_opy_
def bstack1l1ll1lll_opy_(bstack1llllll1l_opy_):
  import re
  bstack111l11l1_opy_ = re.compile(bstack1ll_opy_ (u"ࡴࠥࡢࡠࡧ࠭ࡻࡃ࠰࡞࠵࠳࠹࡝ࡡ࠱ࡠ࠲ࡣࠪࠥࠤ੘"))
  bstack1l1ll11ll_opy_ = re.compile(bstack1ll_opy_ (u"ࡵࠦࡣࡡࡡ࠮ࡼࡄ࠱࡟࠶࠭࠺࡞ࡢ࠲ࡡ࠳࡝ࠫ࠱࡞ࡥ࠲ࢀࡁ࠮࡜࠳࠱࠾ࡢ࡟࠯࡞࠰ࡡ࠯ࠪࠢਖ਼"))
  if bstack1ll_opy_ (u"ࠫࡧࡹ࠺࠰࠱ࠪਗ਼") in bstack1llllll1l_opy_ or re.fullmatch(bstack111l11l1_opy_, bstack1llllll1l_opy_) or re.fullmatch(bstack1l1ll11ll_opy_, bstack1llllll1l_opy_):
    return True
  else:
    return False
@measure(event_name=EVENTS.bstack1111lll11_opy_, stage=STAGE.bstack1l1lll1ll1_opy_, bstack1l1l11ll_opy_=bstack1llll1111l_opy_)
def bstack1ll111l1ll_opy_(config, path, bstack1ll1111l1l_opy_=None):
  import requests
  from requests_toolbelt.multipart.encoder import MultipartEncoder
  import hashlib
  md5_hash = hashlib.md5(open(os.path.abspath(path), bstack1ll_opy_ (u"ࠬࡸࡢࠨਜ਼")).read()).hexdigest()
  bstack1ll1l1l1l1_opy_ = bstack1lllll1ll_opy_(md5_hash)
  bstack1llllll1l_opy_ = None
  if bstack1ll1l1l1l1_opy_:
    logger.info(bstack1l1111l1l_opy_.format(bstack1ll1l1l1l1_opy_, md5_hash))
    return bstack1ll1l1l1l1_opy_
  bstack11l1l1l1ll_opy_ = datetime.datetime.now()
  bstack1l1ll1l1l_opy_ = MultipartEncoder(
    fields={
      bstack1ll_opy_ (u"࠭ࡦࡪ࡮ࡨࠫੜ"): (os.path.basename(path), open(os.path.abspath(path), bstack1ll_opy_ (u"ࠧࡳࡤࠪ੝")), bstack1ll_opy_ (u"ࠨࡶࡨࡼࡹ࠵ࡰ࡭ࡣ࡬ࡲࠬਫ਼")),
      bstack1ll_opy_ (u"ࠩࡦࡹࡸࡺ࡯࡮ࡡ࡬ࡨࠬ੟"): bstack1ll1111l1l_opy_
    }
  )
  response = requests.post(bstack1l111lll11_opy_, data=bstack1l1ll1l1l_opy_,
                           headers={bstack1ll_opy_ (u"ࠪࡇࡴࡴࡴࡦࡰࡷ࠱࡙ࡿࡰࡦࠩ੠"): bstack1l1ll1l1l_opy_.content_type},
                           auth=(config[bstack1ll_opy_ (u"ࠫࡺࡹࡥࡳࡐࡤࡱࡪ࠭੡")], config[bstack1ll_opy_ (u"ࠬࡧࡣࡤࡧࡶࡷࡐ࡫ࡹࠨ੢")]))
  try:
    res = json.loads(response.text)
    bstack1llllll1l_opy_ = res[bstack1ll_opy_ (u"࠭ࡡࡱࡲࡢࡹࡷࡲࠧ੣")]
    logger.info(bstack1l11ll1l1l_opy_.format(bstack1llllll1l_opy_))
    bstack1111111l1_opy_(md5_hash, bstack1llllll1l_opy_)
    cli.bstack11ll11ll1_opy_(bstack1ll_opy_ (u"ࠢࡩࡶࡷࡴ࠿ࡻࡰ࡭ࡱࡤࡨࡤࡧࡰࡱࠤ੤"), datetime.datetime.now() - bstack11l1l1l1ll_opy_)
  except ValueError as err:
    bstack1ll1l1lll_opy_(bstack111ll11l1_opy_.format(str(err)))
  return bstack1llllll1l_opy_
def bstack1l1llll1l1_opy_(framework_name=None, args=None):
  global CONFIG
  global bstack1ll111lll1_opy_
  bstack1l111l1l1l_opy_ = 1
  bstack1l1lll11l_opy_ = 1
  if bstack1ll_opy_ (u"ࠨࡲࡤࡶࡦࡲ࡬ࡦ࡮ࡶࡔࡪࡸࡐ࡭ࡣࡷࡪࡴࡸ࡭ࠨ੥") in CONFIG:
    bstack1l1lll11l_opy_ = CONFIG[bstack1ll_opy_ (u"ࠩࡳࡥࡷࡧ࡬࡭ࡧ࡯ࡷࡕ࡫ࡲࡑ࡮ࡤࡸ࡫ࡵࡲ࡮ࠩ੦")]
  else:
    bstack1l1lll11l_opy_ = bstack1l1ll11l1_opy_(framework_name, args) or 1
  if bstack1ll_opy_ (u"ࠪࡴࡱࡧࡴࡧࡱࡵࡱࡸ࠭੧") in CONFIG:
    bstack1l111l1l1l_opy_ = len(CONFIG[bstack1ll_opy_ (u"ࠫࡵࡲࡡࡵࡨࡲࡶࡲࡹࠧ੨")])
  bstack1ll111lll1_opy_ = int(bstack1l1lll11l_opy_) * int(bstack1l111l1l1l_opy_)
def bstack1l1ll11l1_opy_(framework_name, args):
  if framework_name == bstack1l11l1l11l_opy_ and args and bstack1ll_opy_ (u"ࠬ࠳࠭ࡱࡴࡲࡧࡪࡹࡳࡦࡵࠪ੩") in args:
      bstack1l11l111_opy_ = args.index(bstack1ll_opy_ (u"࠭࠭࠮ࡲࡵࡳࡨ࡫ࡳࡴࡧࡶࠫ੪"))
      return int(args[bstack1l11l111_opy_ + 1]) or 1
  return 1
def bstack1lllll1ll_opy_(md5_hash):
  try:
    from filelock import FileLock
  except ImportError:
    logger.debug(bstack1ll_opy_ (u"ࠧࡧ࡫࡯ࡩࡱࡵࡣ࡬ࠢࡱࡳࡹࠦࡡࡷࡣ࡬ࡰࡦࡨ࡬ࡦ࠮ࠣࡹࡸ࡯࡮ࡨࠢࡥࡥࡸ࡯ࡣࠡࡨ࡬ࡰࡪࠦ࡯ࡱࡧࡵࡥࡹ࡯࡯࡯ࡵࠪ੫"))
    bstack1l11111l1l_opy_ = os.path.join(os.path.expanduser(bstack1ll_opy_ (u"ࠨࢀࠪ੬")), bstack1ll_opy_ (u"ࠩ࠱ࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬ࠩ੭"), bstack1ll_opy_ (u"ࠪࡥࡵࡶࡕࡱ࡮ࡲࡥࡩࡓࡄ࠶ࡊࡤࡷ࡭࠴ࡪࡴࡱࡱࠫ੮"))
    if os.path.exists(bstack1l11111l1l_opy_):
      try:
        bstack1ll1l1ll1l_opy_ = json.load(open(bstack1l11111l1l_opy_, bstack1ll_opy_ (u"ࠫࡷࡨࠧ੯")))
        if md5_hash in bstack1ll1l1ll1l_opy_:
          bstack1111l1ll_opy_ = bstack1ll1l1ll1l_opy_[md5_hash]
          bstack1lllll1l1l_opy_ = datetime.datetime.now()
          bstack1ll111l111_opy_ = datetime.datetime.strptime(bstack1111l1ll_opy_[bstack1ll_opy_ (u"ࠬࡺࡩ࡮ࡧࡶࡸࡦࡳࡰࠨੰ")], bstack1ll_opy_ (u"࠭ࠥࡥ࠱ࠨࡱ࠴࡙ࠫࠡࠧࡋ࠾ࠪࡓ࠺ࠦࡕࠪੱ"))
          if (bstack1lllll1l1l_opy_ - bstack1ll111l111_opy_).days > 30:
            return None
          elif version.parse(str(__version__)) > version.parse(bstack1111l1ll_opy_[bstack1ll_opy_ (u"ࠧࡴࡦ࡮ࡣࡻ࡫ࡲࡴ࡫ࡲࡲࠬੲ")]):
            return None
          return bstack1111l1ll_opy_[bstack1ll_opy_ (u"ࠨ࡫ࡧࠫੳ")]
      except Exception as e:
        logger.debug(bstack1ll_opy_ (u"ࠩࡈࡶࡷࡵࡲࠡࡴࡨࡥࡩ࡯࡮ࡨࠢࡐࡈ࠺ࠦࡨࡢࡵ࡫ࠤ࡫࡯࡬ࡦ࠼ࠣࡿࢂ࠭ੴ").format(str(e)))
    return None
  bstack1l11111l1l_opy_ = os.path.join(os.path.expanduser(bstack1ll_opy_ (u"ࠪࢂࠬੵ")), bstack1ll_opy_ (u"ࠫ࠳ࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮ࠫ੶"), bstack1ll_opy_ (u"ࠬࡧࡰࡱࡗࡳࡰࡴࡧࡤࡎࡆ࠸ࡌࡦࡹࡨ࠯࡬ࡶࡳࡳ࠭੷"))
  lock_file = bstack1l11111l1l_opy_ + bstack1ll_opy_ (u"࠭࠮࡭ࡱࡦ࡯ࠬ੸")
  try:
    with FileLock(lock_file, timeout=10):
      if os.path.exists(bstack1l11111l1l_opy_):
        with open(bstack1l11111l1l_opy_, bstack1ll_opy_ (u"ࠧࡳࠩ੹")) as f:
          content = f.read().strip()
          if content:
            bstack1ll1l1ll1l_opy_ = json.loads(content)
            if md5_hash in bstack1ll1l1ll1l_opy_:
              bstack1111l1ll_opy_ = bstack1ll1l1ll1l_opy_[md5_hash]
              bstack1lllll1l1l_opy_ = datetime.datetime.now()
              bstack1ll111l111_opy_ = datetime.datetime.strptime(bstack1111l1ll_opy_[bstack1ll_opy_ (u"ࠨࡶ࡬ࡱࡪࡹࡴࡢ࡯ࡳࠫ੺")], bstack1ll_opy_ (u"ࠩࠨࡨ࠴ࠫ࡭࠰ࠧ࡜ࠤࠪࡎ࠺ࠦࡏ࠽ࠩࡘ࠭੻"))
              if (bstack1lllll1l1l_opy_ - bstack1ll111l111_opy_).days > 30:
                return None
              elif version.parse(str(__version__)) > version.parse(bstack1111l1ll_opy_[bstack1ll_opy_ (u"ࠪࡷࡩࡱ࡟ࡷࡧࡵࡷ࡮ࡵ࡮ࠨ੼")]):
                return None
              return bstack1111l1ll_opy_[bstack1ll_opy_ (u"ࠫ࡮ࡪࠧ੽")]
      return None
  except Exception as e:
    logger.debug(bstack1ll_opy_ (u"ࠬࡋࡲࡳࡱࡵࠤࡼ࡯ࡴࡩࠢࡩ࡭ࡱ࡫ࠠ࡭ࡱࡦ࡯࡮ࡴࡧࠡࡨࡲࡶࠥࡓࡄ࠶ࠢ࡫ࡥࡸ࡮࠺ࠡࡽࢀࠫ੾").format(str(e)))
    return None
def bstack1111111l1_opy_(md5_hash, bstack1llllll1l_opy_):
  try:
    from filelock import FileLock
  except ImportError:
    logger.debug(bstack1ll_opy_ (u"࠭ࡦࡪ࡮ࡨࡰࡴࡩ࡫ࠡࡰࡲࡸࠥࡧࡶࡢ࡫࡯ࡥࡧࡲࡥ࠭ࠢࡸࡷ࡮ࡴࡧࠡࡤࡤࡷ࡮ࡩࠠࡧ࡫࡯ࡩࠥࡵࡰࡦࡴࡤࡸ࡮ࡵ࡮ࡴࠩ੿"))
    bstack1l11l11l1l_opy_ = os.path.join(os.path.expanduser(bstack1ll_opy_ (u"ࠧࡿࠩ઀")), bstack1ll_opy_ (u"ࠨ࠰ࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫ࠨઁ"))
    if not os.path.exists(bstack1l11l11l1l_opy_):
      os.makedirs(bstack1l11l11l1l_opy_)
    bstack1l11111l1l_opy_ = os.path.join(os.path.expanduser(bstack1ll_opy_ (u"ࠩࢁࠫં")), bstack1ll_opy_ (u"ࠪ࠲ࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭ࠪઃ"), bstack1ll_opy_ (u"ࠫࡦࡶࡰࡖࡲ࡯ࡳࡦࡪࡍࡅ࠷ࡋࡥࡸ࡮࠮࡫ࡵࡲࡲࠬ઄"))
    bstack11llll1lll_opy_ = {
      bstack1ll_opy_ (u"ࠬ࡯ࡤࠨઅ"): bstack1llllll1l_opy_,
      bstack1ll_opy_ (u"࠭ࡴࡪ࡯ࡨࡷࡹࡧ࡭ࡱࠩઆ"): datetime.datetime.strftime(datetime.datetime.now(), bstack1ll_opy_ (u"ࠧࠦࡦ࠲ࠩࡲ࠵࡚ࠥࠢࠨࡌ࠿ࠫࡍ࠻ࠧࡖࠫઇ")),
      bstack1ll_opy_ (u"ࠨࡵࡧ࡯ࡤࡼࡥࡳࡵ࡬ࡳࡳ࠭ઈ"): str(__version__)
    }
    try:
      bstack1ll1l1ll1l_opy_ = {}
      if os.path.exists(bstack1l11111l1l_opy_):
        bstack1ll1l1ll1l_opy_ = json.load(open(bstack1l11111l1l_opy_, bstack1ll_opy_ (u"ࠩࡵࡦࠬઉ")))
      bstack1ll1l1ll1l_opy_[md5_hash] = bstack11llll1lll_opy_
      with open(bstack1l11111l1l_opy_, bstack1ll_opy_ (u"ࠥࡻ࠰ࠨઊ")) as outfile:
        json.dump(bstack1ll1l1ll1l_opy_, outfile)
    except Exception as e:
      logger.debug(bstack1ll_opy_ (u"ࠫࡊࡸࡲࡰࡴࠣࡹࡵࡪࡡࡵ࡫ࡱ࡫ࠥࡓࡄ࠶ࠢ࡫ࡥࡸ࡮ࠠࡧ࡫࡯ࡩ࠿ࠦࡻࡾࠩઋ").format(str(e)))
    return
  bstack1l11l11l1l_opy_ = os.path.join(os.path.expanduser(bstack1ll_opy_ (u"ࠬࢄࠧઌ")), bstack1ll_opy_ (u"࠭࠮ࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰ࠭ઍ"))
  if not os.path.exists(bstack1l11l11l1l_opy_):
    os.makedirs(bstack1l11l11l1l_opy_)
  bstack1l11111l1l_opy_ = os.path.join(os.path.expanduser(bstack1ll_opy_ (u"ࠧࡿࠩ઎")), bstack1ll_opy_ (u"ࠨ࠰ࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫ࠨએ"), bstack1ll_opy_ (u"ࠩࡤࡴࡵ࡛ࡰ࡭ࡱࡤࡨࡒࡊ࠵ࡉࡣࡶ࡬࠳ࡰࡳࡰࡰࠪઐ"))
  lock_file = bstack1l11111l1l_opy_ + bstack1ll_opy_ (u"ࠪ࠲ࡱࡵࡣ࡬ࠩઑ")
  bstack11llll1lll_opy_ = {
    bstack1ll_opy_ (u"ࠫ࡮ࡪࠧ઒"): bstack1llllll1l_opy_,
    bstack1ll_opy_ (u"ࠬࡺࡩ࡮ࡧࡶࡸࡦࡳࡰࠨઓ"): datetime.datetime.strftime(datetime.datetime.now(), bstack1ll_opy_ (u"࠭ࠥࡥ࠱ࠨࡱ࠴࡙ࠫࠡࠧࡋ࠾ࠪࡓ࠺ࠦࡕࠪઔ")),
    bstack1ll_opy_ (u"ࠧࡴࡦ࡮ࡣࡻ࡫ࡲࡴ࡫ࡲࡲࠬક"): str(__version__)
  }
  try:
    with FileLock(lock_file, timeout=10):
      bstack1ll1l1ll1l_opy_ = {}
      if os.path.exists(bstack1l11111l1l_opy_):
        with open(bstack1l11111l1l_opy_, bstack1ll_opy_ (u"ࠨࡴࠪખ")) as f:
          content = f.read().strip()
          if content:
            bstack1ll1l1ll1l_opy_ = json.loads(content)
      bstack1ll1l1ll1l_opy_[md5_hash] = bstack11llll1lll_opy_
      with open(bstack1l11111l1l_opy_, bstack1ll_opy_ (u"ࠤࡺࠦગ")) as outfile:
        json.dump(bstack1ll1l1ll1l_opy_, outfile)
  except Exception as e:
    logger.debug(bstack1ll_opy_ (u"ࠪࡉࡷࡸ࡯ࡳࠢࡺ࡭ࡹ࡮ࠠࡧ࡫࡯ࡩࠥࡲ࡯ࡤ࡭࡬ࡲ࡬ࠦࡦࡰࡴࠣࡑࡉ࠻ࠠࡩࡣࡶ࡬ࠥࡻࡰࡥࡣࡷࡩ࠿ࠦࡻࡾࠩઘ").format(str(e)))
def bstack1l1l11l11_opy_(self):
  return
def bstack11111111l_opy_(self):
  return
def bstack1ll11lll_opy_():
  global bstack1ll1l1ll_opy_
  bstack1ll1l1ll_opy_ = True
@measure(event_name=EVENTS.bstack1l1ll1l11l_opy_, stage=STAGE.bstack1l1lll1ll1_opy_, bstack1l1l11ll_opy_=bstack1llll1111l_opy_)
def bstack1ll1lll1_opy_(self):
  global bstack11l11ll111_opy_
  global bstack1111l1l11_opy_
  global bstack1l1111ll1_opy_
  try:
    if bstack1ll_opy_ (u"ࠫࡵࡿࡴࡦࡵࡷࠫઙ") in bstack11l11ll111_opy_ and self.session_id != None and bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠬࡺࡥࡴࡶࡖࡸࡦࡺࡵࡴࠩચ"), bstack1ll_opy_ (u"࠭ࠧછ")) != bstack1ll_opy_ (u"ࠧࡴ࡭࡬ࡴࡵ࡫ࡤࠨજ"):
      bstack1l1ll1l111_opy_ = bstack1ll_opy_ (u"ࠨࡲࡤࡷࡸ࡫ࡤࠨઝ") if len(threading.current_thread().bstackTestErrorMessages) == 0 else bstack1ll_opy_ (u"ࠩࡩࡥ࡮ࡲࡥࡥࠩઞ")
      if bstack1l1ll1l111_opy_ == bstack1ll_opy_ (u"ࠪࡪࡦ࡯࡬ࡦࡦࠪટ"):
        bstack1l1lll1l_opy_(logger)
      if self != None:
        bstack11ll11111l_opy_(self, bstack1l1ll1l111_opy_, bstack1ll_opy_ (u"ࠫ࠱ࠦࠧઠ").join(threading.current_thread().bstackTestErrorMessages))
    threading.current_thread().testStatus = bstack1ll_opy_ (u"ࠬ࠭ડ")
    if bstack1ll_opy_ (u"࠭ࡰࡺࡶࡨࡷࡹ࠭ઢ") in bstack11l11ll111_opy_ and getattr(threading.current_thread(), bstack1ll_opy_ (u"ࠧࡢ࠳࠴ࡽࡕࡲࡡࡵࡨࡲࡶࡲ࠭ણ"), None):
      bstack1l111ll1l_opy_.bstack1l1l11111_opy_(self, bstack111l11111_opy_, logger, wait=True)
    if bstack1ll_opy_ (u"ࠨࡤࡨ࡬ࡦࡼࡥࠨત") in bstack11l11ll111_opy_:
      if not threading.currentThread().behave_test_status:
        bstack11ll11111l_opy_(self, bstack1ll_opy_ (u"ࠤࡳࡥࡸࡹࡥࡥࠤથ"))
      bstack11l1l1111_opy_.bstack1l1lll111_opy_(self)
  except Exception as e:
    logger.debug(bstack1ll_opy_ (u"ࠥࡉࡷࡸ࡯ࡳࠢࡺ࡬࡮ࡲࡥࠡ࡯ࡤࡶࡰ࡯࡮ࡨࠢࡶࡸࡦࡺࡵࡴ࠼ࠣࠦદ") + str(e))
  bstack1l1111ll1_opy_(self)
  self.session_id = None
def bstack1lllll11l1_opy_(self, *args, **kwargs):
  try:
    from selenium.webdriver.remote.remote_connection import RemoteConnection
    from bstack_utils.helper import bstack11111ll1l_opy_
    global bstack11l11ll111_opy_
    command_executor = kwargs.get(bstack1ll_opy_ (u"ࠫࡨࡵ࡭࡮ࡣࡱࡨࡤ࡫ࡸࡦࡥࡸࡸࡴࡸࠧધ"), bstack1ll_opy_ (u"ࠬ࠭ન"))
    bstack1ll1ll1ll_opy_ = False
    if type(command_executor) == str and bstack1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯࠳ࡩ࡯࡮ࠩ઩") in command_executor:
      bstack1ll1ll1ll_opy_ = True
    elif isinstance(command_executor, RemoteConnection) and bstack1ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰ࠴ࡣࡰ࡯ࠪપ") in str(getattr(command_executor, bstack1ll_opy_ (u"ࠨࡡࡸࡶࡱ࠭ફ"), bstack1ll_opy_ (u"ࠩࠪબ"))):
      bstack1ll1ll1ll_opy_ = True
    else:
      kwargs = bstack1llll1l11_opy_.bstack11lll11111_opy_(bstack1ll1l1ll11_opy_=kwargs, config=CONFIG)
      return bstack11ll1l1lll_opy_(self, *args, **kwargs)
    if bstack1ll1ll1ll_opy_:
      bstack11l1l111ll_opy_ = bstack1ll1l1l1l_opy_.bstack1ll1111ll1_opy_(CONFIG, bstack11l11ll111_opy_)
      if kwargs.get(bstack1ll_opy_ (u"ࠪࡳࡵࡺࡩࡰࡰࡶࠫભ")):
        kwargs[bstack1ll_opy_ (u"ࠫࡴࡶࡴࡪࡱࡱࡷࠬમ")] = bstack11111ll1l_opy_(kwargs[bstack1ll_opy_ (u"ࠬࡵࡰࡵ࡫ࡲࡲࡸ࠭ય")], bstack11l11ll111_opy_, CONFIG, bstack11l1l111ll_opy_)
      elif kwargs.get(bstack1ll_opy_ (u"࠭ࡤࡦࡵ࡬ࡶࡪࡪ࡟ࡤࡣࡳࡥࡧ࡯࡬ࡪࡶ࡬ࡩࡸ࠭ર")):
        kwargs[bstack1ll_opy_ (u"ࠧࡥࡧࡶ࡭ࡷ࡫ࡤࡠࡥࡤࡴࡦࡨࡩ࡭࡫ࡷ࡭ࡪࡹࠧ઱")] = bstack11111ll1l_opy_(kwargs[bstack1ll_opy_ (u"ࠨࡦࡨࡷ࡮ࡸࡥࡥࡡࡦࡥࡵࡧࡢࡪ࡮࡬ࡸ࡮࡫ࡳࠨલ")], bstack11l11ll111_opy_, CONFIG, bstack11l1l111ll_opy_)
  except Exception as e:
    logger.error(bstack1ll_opy_ (u"ࠤࡈࡶࡷࡵࡲࠡࡹ࡫ࡩࡳࠦࡰࡳࡱࡦࡩࡸࡹࡩ࡯ࡩࠣࡗࡉࡑࠠࡤࡣࡳࡷ࠿ࠦࡻࡾࠤળ").format(str(e)))
  return bstack11ll1l1lll_opy_(self, *args, **kwargs)
@measure(event_name=EVENTS.bstack11l111lll_opy_, stage=STAGE.bstack1l1lll1ll1_opy_, bstack1l1l11ll_opy_=bstack1llll1111l_opy_)
def bstack1ll11l1ll1_opy_(self, command_executor=bstack1ll_opy_ (u"ࠥ࡬ࡹࡺࡰ࠻࠱࠲࠵࠷࠽࠮࠱࠰࠳࠲࠶ࡀ࠴࠵࠶࠷ࠦ઴"), *args, **kwargs):
  global bstack1111l1l11_opy_
  global bstack1llll11lll_opy_
  bstack1ll111111l_opy_ = bstack1lllll11l1_opy_(self, command_executor=command_executor, *args, **kwargs)
  if not bstack1l11111lll_opy_.on():
    return bstack1ll111111l_opy_
  try:
    logger.debug(bstack1ll_opy_ (u"ࠫࡈࡵ࡭࡮ࡣࡱࡨࠥࡋࡸࡦࡥࡸࡸࡴࡸࠠࡸࡪࡨࡲࠥࡈࡲࡰࡹࡶࡩࡷ࡙ࡴࡢࡥ࡮ࠤࡆࡻࡴࡰ࡯ࡤࡸ࡮ࡵ࡮ࠡ࡫ࡶࠤ࡫ࡧ࡬ࡴࡧࠣ࠱ࠥࢁࡽࠨવ").format(str(command_executor)))
    logger.debug(bstack1ll_opy_ (u"ࠬࡎࡵࡣࠢࡘࡖࡑࠦࡩࡴࠢ࠰ࠤࢀࢃࠧશ").format(str(command_executor._url)))
    from selenium.webdriver.remote.remote_connection import RemoteConnection
    if isinstance(command_executor, RemoteConnection) and bstack1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯࠳ࡩ࡯࡮ࠩષ") in command_executor._url:
      bstack1ll1l1l111_opy_.bstack111ll1ll1_opy_(bstack1ll_opy_ (u"ࠧࡣࡵࡷࡥࡨࡱ࡟ࡴࡧࡶࡷ࡮ࡵ࡮ࠨસ"), True)
  except:
    pass
  if (isinstance(command_executor, str) and bstack1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࠮ࡤࡱࡰࠫહ") in command_executor):
    bstack1ll1l1l111_opy_.bstack111ll1ll1_opy_(bstack1ll_opy_ (u"ࠩࡥࡷࡹࡧࡣ࡬ࡡࡶࡩࡸࡹࡩࡰࡰࠪ઺"), True)
  threading.current_thread().bstackSessionDriver = self
  bstack11ll11lll_opy_ = getattr(threading.current_thread(), bstack1ll_opy_ (u"ࠪࡦࡸࡺࡡࡤ࡭ࡗࡩࡸࡺࡍࡦࡶࡤࠫ઻"), None)
  bstack11l111111l_opy_ = {}
  if self.capabilities is not None:
    bstack11l111111l_opy_[bstack1ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࡤࡴࡡ࡮ࡧ઼ࠪ")] = self.capabilities.get(bstack1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡔࡡ࡮ࡧࠪઽ"))
    bstack11l111111l_opy_[bstack1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸ࡟ࡷࡧࡵࡷ࡮ࡵ࡮ࠨા")] = self.capabilities.get(bstack1ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡗࡧࡵࡷ࡮ࡵ࡮ࠨિ"))
    bstack11l111111l_opy_[bstack1ll_opy_ (u"ࠨࡥ࡫ࡶࡴࡳࡥࡠࡱࡳࡸ࡮ࡵ࡮ࡴࠩી")] = self.capabilities.get(bstack1ll_opy_ (u"ࠩࡪࡳࡴ࡭࠺ࡤࡪࡵࡳࡲ࡫ࡏࡱࡶ࡬ࡳࡳࡹࠧુ"))
  if CONFIG.get(bstack1ll_opy_ (u"ࠪࡥࡨࡩࡥࡴࡵ࡬ࡦ࡮ࡲࡩࡵࡻࠪૂ"), False) and bstack1llll1l11_opy_.bstack1l1l1l11l1_opy_(bstack11l111111l_opy_):
    threading.current_thread().a11yPlatform = True
  if bstack1ll_opy_ (u"ࠫࡧ࡫ࡨࡢࡸࡨࠫૃ") in bstack11l11ll111_opy_ or bstack1ll_opy_ (u"ࠬࡸ࡯ࡣࡱࡷࠫૄ") in bstack11l11ll111_opy_:
    bstack1lll1111l_opy_.bstack11ll1l1ll1_opy_(self)
  if bstack1ll_opy_ (u"࠭ࡰࡺࡶࡨࡷࡹ࠭ૅ") in bstack11l11ll111_opy_ and bstack11ll11lll_opy_ and bstack11ll11lll_opy_.get(bstack1ll_opy_ (u"ࠧࡴࡶࡤࡸࡺࡹࠧ૆"), bstack1ll_opy_ (u"ࠨࠩે")) == bstack1ll_opy_ (u"ࠩࡳࡩࡳࡪࡩ࡯ࡩࠪૈ"):
    bstack1lll1111l_opy_.bstack11ll1l1ll1_opy_(self)
  bstack1111l1l11_opy_ = self.session_id
  with bstack1lll11l1l_opy_:
    bstack1llll11lll_opy_.append(self)
  return bstack1ll111111l_opy_
def bstack111111l1l_opy_(args):
  return bstack1ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬ࡡࡨࡼࡪࡩࡵࡵࡱࡵࠫૉ") in str(args)
def bstack1l11l1l11_opy_(self, driver_command, *args, **kwargs):
  global bstack1ll1l11ll_opy_
  global bstack11l1l1l11_opy_
  bstack11lll11l_opy_ = bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠫ࡮ࡹࡁ࠲࠳ࡼࡘࡪࡹࡴࠨ૊"), None) and bstack1l11l11l_opy_(
          threading.current_thread(), bstack1ll_opy_ (u"ࠬࡧ࠱࠲ࡻࡓࡰࡦࡺࡦࡰࡴࡰࠫો"), None)
  bstack1111lllll_opy_ = bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"࠭ࡩࡴࡃࡳࡴࡆ࠷࠱ࡺࡖࡨࡷࡹ࠭ૌ"), None) and bstack1l11l11l_opy_(
          threading.current_thread(), bstack1ll_opy_ (u"ࠧࡢࡲࡳࡅ࠶࠷ࡹࡑ࡮ࡤࡸ࡫ࡵࡲ࡮્ࠩ"), None)
  bstack111llllll_opy_ = getattr(self, bstack1ll_opy_ (u"ࠨࡤࡶࡸࡦࡩ࡫ࡂ࠳࠴ࡽࡘ࡮࡯ࡶ࡮ࡧࡗࡨࡧ࡮ࠨ૎"), None) != None and getattr(self, bstack1ll_opy_ (u"ࠩࡥࡷࡹࡧࡣ࡬ࡃ࠴࠵ࡾ࡙ࡨࡰࡷ࡯ࡨࡘࡩࡡ࡯ࠩ૏"), None) == True
  if not bstack11l1l1l11_opy_ and bstack1ll_opy_ (u"ࠪࡥࡨࡩࡥࡴࡵ࡬ࡦ࡮ࡲࡩࡵࡻࠪૐ") in CONFIG and CONFIG[bstack1ll_opy_ (u"ࠫࡦࡩࡣࡦࡵࡶ࡭ࡧ࡯࡬ࡪࡶࡼࠫ૑")] == True and bstack1111l1ll1_opy_.bstack111llll1l1_opy_(driver_command) and (bstack111llllll_opy_ or bstack11lll11l_opy_ or bstack1111lllll_opy_) and not bstack111111l1l_opy_(args):
    try:
      bstack11l1l1l11_opy_ = True
      logger.debug(bstack1ll_opy_ (u"ࠬࡖࡥࡳࡨࡲࡶࡲ࡯࡮ࡨࠢࡶࡧࡦࡴࠠࡧࡱࡵࠤࢀࢃࠧ૒").format(driver_command))
      logger.debug(perform_scan(self, driver_command=driver_command))
    except Exception as err:
      logger.debug(bstack1ll_opy_ (u"࠭ࡆࡢ࡫࡯ࡩࡩࠦࡴࡰࠢࡳࡩࡷ࡬࡯ࡳ࡯ࠣࡷࡨࡧ࡮ࠡࡽࢀࠫ૓").format(str(err)))
    bstack11l1l1l11_opy_ = False
  response = bstack1ll1l11ll_opy_(self, driver_command, *args, **kwargs)
  if (bstack1ll_opy_ (u"ࠧࡳࡱࡥࡳࡹ࠭૔") in str(bstack11l11ll111_opy_).lower() or bstack1ll_opy_ (u"ࠨࡤࡨ࡬ࡦࡼࡥࠨ૕") in str(bstack11l11ll111_opy_).lower()) and bstack1l11111lll_opy_.on():
    try:
      if driver_command == bstack1ll_opy_ (u"ࠩࡶࡧࡷ࡫ࡥ࡯ࡵ࡫ࡳࡹ࠭૖"):
        bstack1lll1111l_opy_.bstack1l1l1ll111_opy_({
            bstack1ll_opy_ (u"ࠪ࡭ࡲࡧࡧࡦࠩ૗"): response[bstack1ll_opy_ (u"ࠫࡻࡧ࡬ࡶࡧࠪ૘")],
            bstack1ll_opy_ (u"ࠬࡺࡥࡴࡶࡢࡶࡺࡴ࡟ࡶࡷ࡬ࡨࠬ૙"): bstack1lll1111l_opy_.current_test_uuid() if bstack1lll1111l_opy_.current_test_uuid() else bstack1l11111lll_opy_.current_hook_uuid()
        })
    except:
      pass
  return response
@measure(event_name=EVENTS.bstack1l1lllll1_opy_, stage=STAGE.bstack1l1lll1ll1_opy_, bstack1l1l11ll_opy_=bstack1llll1111l_opy_)
def bstack1l1l1l111_opy_(self, command_executor,
             desired_capabilities=None, browser_profile=None, proxy=None,
             keep_alive=True, file_detector=None, options=None, *args, **kwargs):
  global CONFIG
  global bstack1111l1l11_opy_
  global bstack11l1l111l_opy_
  global bstack1llll1111l_opy_
  global bstack11lllllll1_opy_
  global bstack11l1l1111l_opy_
  global bstack11l11ll111_opy_
  global bstack11ll1l1lll_opy_
  global bstack1llll11lll_opy_
  global bstack1l1l1l1l1l_opy_
  global bstack111l11111_opy_
  if os.getenv(bstack1ll_opy_ (u"࠭ࡂࡔࡡࡄ࠵࠶࡟࡟ࡋ࡙ࡗࠫ૚")) is not None and bstack1llll1l11_opy_.bstack1l1l111lll_opy_(CONFIG) is None:
    CONFIG[bstack1ll_opy_ (u"ࠧࡢࡥࡦࡩࡸࡹࡩࡣ࡫࡯࡭ࡹࡿࠧ૛")] = True
  CONFIG[bstack1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱࡓࡅࡍࠪ૜")] = str(bstack11l11ll111_opy_) + str(__version__)
  bstack1111l1lll_opy_ = os.environ[bstack1ll_opy_ (u"ࠩࡅࡖࡔ࡝ࡓࡆࡔࡖࡘࡆࡉࡋࡠࡖࡈࡗ࡙ࡎࡕࡃࡡࡘ࡙ࡎࡊࠧ૝")]
  bstack11l1l111ll_opy_ = bstack1ll1l1l1l_opy_.bstack1ll1111ll1_opy_(CONFIG, bstack11l11ll111_opy_)
  CONFIG[bstack1ll_opy_ (u"ࠪࡸࡪࡹࡴࡩࡷࡥࡆࡺ࡯࡬ࡥࡗࡸ࡭ࡩ࠭૞")] = bstack1111l1lll_opy_
  CONFIG[bstack1ll_opy_ (u"ࠫࡧࡻࡩ࡭ࡦࡓࡶࡴࡪࡵࡤࡶࡐࡥࡵ࠭૟")] = bstack11l1l111ll_opy_
  if CONFIG.get(bstack1ll_opy_ (u"ࠬࡧࡣࡤࡧࡶࡷ࡮ࡨࡩ࡭࡫ࡷࡽࡔࡶࡴࡪࡱࡱࡷࠬૠ"),bstack1ll_opy_ (u"࠭ࠧૡ")) and bstack1ll_opy_ (u"ࠧࡳࡱࡥࡳࡹ࠭ૢ") in bstack11l11ll111_opy_:
    CONFIG[bstack1ll_opy_ (u"ࠨࡣࡦࡧࡪࡹࡳࡪࡤ࡬ࡰ࡮ࡺࡹࡐࡲࡷ࡭ࡴࡴࡳࠨૣ")].pop(bstack1ll_opy_ (u"ࠩ࡬ࡲࡨࡲࡵࡥࡧࡗࡥ࡬ࡹࡉ࡯ࡖࡨࡷࡹ࡯࡮ࡨࡕࡦࡳࡵ࡫ࠧ૤"), None)
    CONFIG[bstack1ll_opy_ (u"ࠪࡥࡨࡩࡥࡴࡵ࡬ࡦ࡮ࡲࡩࡵࡻࡒࡴࡹ࡯࡯࡯ࡵࠪ૥")].pop(bstack1ll_opy_ (u"ࠫࡪࡾࡣ࡭ࡷࡧࡩ࡙ࡧࡧࡴࡋࡱࡘࡪࡹࡴࡪࡰࡪࡗࡨࡵࡰࡦࠩ૦"), None)
  command_executor = bstack111ll1111_opy_()
  logger.debug(bstack11l1llllll_opy_.format(command_executor))
  proxy = bstack111llll1ll_opy_(CONFIG, proxy)
  bstack11l1l1l1_opy_ = 0 if bstack11l1l111l_opy_ < 0 else bstack11l1l111l_opy_
  try:
    if bstack11lllllll1_opy_ is True:
      bstack11l1l1l1_opy_ = int(multiprocessing.current_process().name)
    elif bstack11l1l1111l_opy_ is True:
      bstack11l1l1l1_opy_ = int(threading.current_thread().name)
  except:
    bstack11l1l1l1_opy_ = 0
  bstack1l1l111ll1_opy_ = bstack1l1111llll_opy_(CONFIG, bstack11l1l1l1_opy_)
  logger.debug(bstack11ll1l1l_opy_.format(str(bstack1l1l111ll1_opy_)))
  if bstack1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮ࡐࡴࡩࡡ࡭ࠩ૧") in CONFIG and bstack11l11lllll_opy_(CONFIG[bstack1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯ࡑࡵࡣࡢ࡮ࠪ૨")]):
    bstack1l1l1111ll_opy_(bstack1l1l111ll1_opy_)
  if bstack1llll1l11_opy_.bstack1l111lll1l_opy_(CONFIG, bstack11l1l1l1_opy_) and bstack1llll1l11_opy_.bstack11111l1l1_opy_(bstack1l1l111ll1_opy_, options, desired_capabilities, CONFIG):
    threading.current_thread().a11yPlatform = True
    if (cli.accessibility is None or not cli.accessibility.is_enabled()):
      bstack1llll1l11_opy_.set_capabilities(bstack1l1l111ll1_opy_, CONFIG)
  if desired_capabilities:
    bstack1l11llll_opy_ = bstack11l1ll1l1l_opy_(desired_capabilities)
    bstack1l11llll_opy_[bstack1ll_opy_ (u"ࠧࡶࡵࡨ࡛࠸ࡉࠧ૩")] = bstack1l1111l11l_opy_(CONFIG)
    bstack1l11llll1_opy_ = bstack1l1111llll_opy_(bstack1l11llll_opy_)
    if bstack1l11llll1_opy_:
      bstack1l1l111ll1_opy_ = update(bstack1l11llll1_opy_, bstack1l1l111ll1_opy_)
    desired_capabilities = None
  if options:
    bstack1lll1ll1l1_opy_(options, bstack1l1l111ll1_opy_)
  if not options:
    options = bstack1l1ll111_opy_(bstack1l1l111ll1_opy_)
  bstack111l11111_opy_ = CONFIG.get(bstack1ll_opy_ (u"ࠨࡲ࡯ࡥࡹ࡬࡯ࡳ࡯ࡶࠫ૪"))[bstack11l1l1l1_opy_]
  if proxy and bstack11l11111l1_opy_() >= version.parse(bstack1ll_opy_ (u"ࠩ࠷࠲࠶࠶࠮࠱ࠩ૫")):
    options.proxy(proxy)
  if options and bstack11l11111l1_opy_() >= version.parse(bstack1ll_opy_ (u"ࠪ࠷࠳࠾࠮࠱ࠩ૬")):
    desired_capabilities = None
  if (
          not options and not desired_capabilities
  ) or (
          bstack11l11111l1_opy_() < version.parse(bstack1ll_opy_ (u"ࠫ࠸࠴࠸࠯࠲ࠪ૭")) and not desired_capabilities
  ):
    desired_capabilities = {}
    desired_capabilities.update(bstack1l1l111ll1_opy_)
  logger.info(bstack1l1ll1ll1_opy_)
  bstack11ll1llll1_opy_.end(EVENTS.bstack11ll1l11ll_opy_.value, EVENTS.bstack11ll1l11ll_opy_.value + bstack1ll_opy_ (u"ࠧࡀࡳࡵࡣࡵࡸࠧ૮"), EVENTS.bstack11ll1l11ll_opy_.value + bstack1ll_opy_ (u"ࠨ࠺ࡦࡰࡧࠦ૯"), status=True, failure=None, test_name=bstack1llll1111l_opy_)
  if bstack1ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡠࡲࡵࡳ࡫࡯࡬ࡦࠩ૰") in kwargs:
    del kwargs[bstack1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡡࡳࡶࡴ࡬ࡩ࡭ࡧࠪ૱")]
  try:
    if bstack11l11111l1_opy_() >= version.parse(bstack1ll_opy_ (u"ࠩ࠷࠲࠶࠶࠮࠱ࠩ૲")):
      bstack11ll1l1lll_opy_(self, command_executor=command_executor,
                options=options, keep_alive=keep_alive, file_detector=file_detector, *args, **kwargs)
    elif bstack11l11111l1_opy_() >= version.parse(bstack1ll_opy_ (u"ࠪ࠷࠳࠾࠮࠱ࠩ૳")):
      bstack11ll1l1lll_opy_(self, command_executor=command_executor,
                desired_capabilities=desired_capabilities, options=options,
                browser_profile=browser_profile, proxy=proxy,
                keep_alive=keep_alive, file_detector=file_detector)
    elif bstack11l11111l1_opy_() >= version.parse(bstack1ll_opy_ (u"ࠫ࠷࠴࠵࠴࠰࠳ࠫ૴")):
      bstack11ll1l1lll_opy_(self, command_executor=command_executor,
                desired_capabilities=desired_capabilities,
                browser_profile=browser_profile, proxy=proxy,
                keep_alive=keep_alive, file_detector=file_detector)
    else:
      bstack11ll1l1lll_opy_(self, command_executor=command_executor,
                desired_capabilities=desired_capabilities,
                browser_profile=browser_profile, proxy=proxy,
                keep_alive=keep_alive)
  except Exception as bstack1l1111l111_opy_:
    logger.error(bstack1111ll1l1_opy_.format(bstack1ll_opy_ (u"ࠬࡈࡲࡰࡹࡶࡩࡷ࡙ࡴࡢࡥ࡮ࠫ૵"), str(bstack1l1111l111_opy_)))
    raise bstack1l1111l111_opy_
  if bstack1llll1l11_opy_.bstack1l111lll1l_opy_(CONFIG, bstack11l1l1l1_opy_) and bstack1llll1l11_opy_.bstack11111l1l1_opy_(self.caps, options, desired_capabilities):
    if CONFIG[bstack1ll_opy_ (u"࠭ࡢࡶ࡫࡯ࡨࡕࡸ࡯ࡥࡷࡦࡸࡒࡧࡰࠨ૶")][bstack1ll_opy_ (u"ࠧࡢࡲࡳࡣࡦࡻࡴࡰ࡯ࡤࡸࡪ࠭૷")] == True:
      threading.current_thread().appA11yPlatform = True
      if cli.accessibility is None or not cli.accessibility.is_enabled():
        bstack1llll1l11_opy_.set_capabilities(bstack1l1l111ll1_opy_, CONFIG)
  try:
    bstack1l1llllll_opy_ = bstack1ll_opy_ (u"ࠨࠩ૸")
    if bstack11l11111l1_opy_() >= version.parse(bstack1ll_opy_ (u"ࠩ࠷࠲࠵࠴࠰ࡣ࠳ࠪૹ")):
      if self.caps is not None:
        bstack1l1llllll_opy_ = self.caps.get(bstack1ll_opy_ (u"ࠥࡳࡵࡺࡩ࡮ࡣ࡯ࡌࡺࡨࡕࡳ࡮ࠥૺ"))
    else:
      if self.capabilities is not None:
        bstack1l1llllll_opy_ = self.capabilities.get(bstack1ll_opy_ (u"ࠦࡴࡶࡴࡪ࡯ࡤࡰࡍࡻࡢࡖࡴ࡯ࠦૻ"))
    if bstack1l1llllll_opy_:
      bstack1l11l1lll1_opy_(bstack1l1llllll_opy_)
      if bstack11l11111l1_opy_() <= version.parse(bstack1ll_opy_ (u"ࠬ࠹࠮࠲࠵࠱࠴ࠬૼ")):
        self.command_executor._url = bstack1ll_opy_ (u"ࠨࡨࡵࡶࡳ࠾࠴࠵ࠢ૽") + bstack1ll111lll_opy_ + bstack1ll_opy_ (u"ࠢ࠻࠺࠳࠳ࡼࡪ࠯ࡩࡷࡥࠦ૾")
      else:
        self.command_executor._url = bstack1ll_opy_ (u"ࠣࡪࡷࡸࡵࡹ࠺࠰࠱ࠥ૿") + bstack1l1llllll_opy_ + bstack1ll_opy_ (u"ࠤ࠲ࡻࡩ࠵ࡨࡶࡤࠥ଀")
      logger.debug(bstack1ll11lllll_opy_.format(bstack1l1llllll_opy_))
    else:
      logger.debug(bstack1ll1l11l1_opy_.format(bstack1ll_opy_ (u"ࠥࡓࡵࡺࡩ࡮ࡣ࡯ࠤࡍࡻࡢࠡࡰࡲࡸࠥ࡬࡯ࡶࡰࡧࠦଁ")))
  except Exception as e:
    logger.debug(bstack1ll1l11l1_opy_.format(e))
  if bstack1ll_opy_ (u"ࠫࡷࡵࡢࡰࡶࠪଂ") in bstack11l11ll111_opy_:
    bstack11l1111111_opy_(bstack11l1l111l_opy_, bstack1l1l1l1l1l_opy_)
  bstack1111l1l11_opy_ = self.session_id
  if bstack1ll_opy_ (u"ࠬࡶࡹࡵࡧࡶࡸࠬଃ") in bstack11l11ll111_opy_ or bstack1ll_opy_ (u"࠭ࡢࡦࡪࡤࡺࡪ࠭଄") in bstack11l11ll111_opy_ or bstack1ll_opy_ (u"ࠧࡳࡱࡥࡳࡹ࠭ଅ") in bstack11l11ll111_opy_:
    threading.current_thread().bstackSessionId = self.session_id
    threading.current_thread().bstackSessionDriver = self
    threading.current_thread().bstackTestErrorMessages = []
  bstack11ll11lll_opy_ = getattr(threading.current_thread(), bstack1ll_opy_ (u"ࠨࡤࡶࡸࡦࡩ࡫ࡕࡧࡶࡸࡒ࡫ࡴࡢࠩଆ"), None)
  if bstack1ll_opy_ (u"ࠩࡥࡩ࡭ࡧࡶࡦࠩଇ") in bstack11l11ll111_opy_ or bstack1ll_opy_ (u"ࠪࡶࡴࡨ࡯ࡵࠩଈ") in bstack11l11ll111_opy_:
    bstack1lll1111l_opy_.bstack11ll1l1ll1_opy_(self)
  if bstack1ll_opy_ (u"ࠫࡵࡿࡴࡦࡵࡷࠫଉ") in bstack11l11ll111_opy_ and bstack11ll11lll_opy_ and bstack11ll11lll_opy_.get(bstack1ll_opy_ (u"ࠬࡹࡴࡢࡶࡸࡷࠬଊ"), bstack1ll_opy_ (u"࠭ࠧଋ")) == bstack1ll_opy_ (u"ࠧࡱࡧࡱࡨ࡮ࡴࡧࠨଌ"):
    bstack1lll1111l_opy_.bstack11ll1l1ll1_opy_(self)
  with bstack1lll11l1l_opy_:
    bstack1llll11lll_opy_.append(self)
  if bstack1ll_opy_ (u"ࠨࡲ࡯ࡥࡹ࡬࡯ࡳ࡯ࡶࠫ଍") in CONFIG and bstack1ll_opy_ (u"ࠩࡶࡩࡸࡹࡩࡰࡰࡑࡥࡲ࡫ࠧ଎") in CONFIG[bstack1ll_opy_ (u"ࠪࡴࡱࡧࡴࡧࡱࡵࡱࡸ࠭ଏ")][bstack11l1l1l1_opy_]:
    bstack1llll1111l_opy_ = CONFIG[bstack1ll_opy_ (u"ࠫࡵࡲࡡࡵࡨࡲࡶࡲࡹࠧଐ")][bstack11l1l1l1_opy_][bstack1ll_opy_ (u"ࠬࡹࡥࡴࡵ࡬ࡳࡳࡔࡡ࡮ࡧࠪ଑")]
  logger.debug(bstack11llll1l11_opy_.format(bstack1111l1l11_opy_))
try:
  try:
    import Browser
    from subprocess import Popen
    from browserstack_sdk.__init__ import bstack11lll11ll1_opy_
    def bstack1ll111l1l_opy_(self, args, bufsize=-1, executable=None,
              stdin=None, stdout=None, stderr=None,
              preexec_fn=None, close_fds=True,
              shell=False, cwd=None, env=None, universal_newlines=None,
              startupinfo=None, creationflags=0,
              restore_signals=True, start_new_session=False,
              pass_fds=(), *, user=None, group=None, extra_groups=None,
              encoding=None, errors=None, text=None, umask=-1, pipesize=-1):
      global CONFIG
      global bstack111lllll_opy_
      if(bstack1ll_opy_ (u"ࠨࡩ࡯ࡦࡨࡼ࠳ࡰࡳࠣ଒") in args[1]):
        with open(os.path.join(os.path.expanduser(bstack1ll_opy_ (u"ࠧࡿࠩଓ")), bstack1ll_opy_ (u"ࠨ࠰ࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫ࠨଔ"), bstack1ll_opy_ (u"ࠩ࠱ࡷࡪࡹࡳࡪࡱࡱ࡭ࡩࡹ࠮ࡵࡺࡷࠫକ")), bstack1ll_opy_ (u"ࠪࡻࠬଖ")) as fp:
          fp.write(bstack1ll_opy_ (u"ࠦࠧଗ"))
        if(not os.path.exists(os.path.join(os.path.dirname(args[1]), bstack1ll_opy_ (u"ࠧ࡯࡮ࡥࡧࡻࡣࡧࡹࡴࡢࡥ࡮࠲࡯ࡹࠢଘ")))):
          with open(args[1], bstack1ll_opy_ (u"࠭ࡲࠨଙ")) as f:
            lines = f.readlines()
            index = next((i for i, line in enumerate(lines) if bstack1ll_opy_ (u"ࠧࡢࡵࡼࡲࡨࠦࡦࡶࡰࡦࡸ࡮ࡵ࡮ࠡࡡࡱࡩࡼࡖࡡࡨࡧࠫࡧࡴࡴࡴࡦࡺࡷ࠰ࠥࡶࡡࡨࡧࠣࡁࠥࡼ࡯ࡪࡦࠣ࠴࠮࠭ଚ") in line), None)
            if index is not None:
                lines.insert(index+2, bstack11l11lll1_opy_)
            if bstack1ll_opy_ (u"ࠨࡶࡸࡶࡧࡵࡓࡤࡣ࡯ࡩࠬଛ") in CONFIG and str(CONFIG[bstack1ll_opy_ (u"ࠩࡷࡹࡷࡨ࡯ࡔࡥࡤࡰࡪ࠭ଜ")]).lower() != bstack1ll_opy_ (u"ࠪࡪࡦࡲࡳࡦࠩଝ"):
                bstack11l1111l_opy_ = bstack11lll11ll1_opy_()
                bstack1l111111l_opy_ = bstack1ll_opy_ (u"ࠫࠬ࠭ࠊ࠰ࠬࠣࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃࠠࠫ࠱ࠍࡧࡴࡴࡳࡵࠢࡥࡷࡹࡧࡣ࡬ࡡࡳࡥࡹ࡮ࠠ࠾ࠢࡳࡶࡴࡩࡥࡴࡵ࠱ࡥࡷ࡭ࡶ࡜ࡲࡵࡳࡨ࡫ࡳࡴ࠰ࡤࡶ࡬ࡼ࠮࡭ࡧࡱ࡫ࡹ࡮ࠠ࠮ࠢ࠶ࡡࡀࠐࡣࡰࡰࡶࡸࠥࡨࡳࡵࡣࡦ࡯ࡤࡩࡡࡱࡵࠣࡁࠥࡶࡲࡰࡥࡨࡷࡸ࠴ࡡࡳࡩࡹ࡟ࡵࡸ࡯ࡤࡧࡶࡷ࠳ࡧࡲࡨࡸ࠱ࡰࡪࡴࡧࡵࡪࠣ࠱ࠥ࠷࡝࠼ࠌࡦࡳࡳࡹࡴࠡࡲࡢ࡭ࡳࡪࡥࡹࠢࡀࠤࡵࡸ࡯ࡤࡧࡶࡷ࠳ࡧࡲࡨࡸ࡞ࡴࡷࡵࡣࡦࡵࡶ࠲ࡦࡸࡧࡷ࠰࡯ࡩࡳ࡭ࡴࡩࠢ࠰ࠤ࠷ࡣ࠻ࠋࡲࡵࡳࡨ࡫ࡳࡴ࠰ࡤࡶ࡬ࡼࠠ࠾ࠢࡳࡶࡴࡩࡥࡴࡵ࠱ࡥࡷ࡭ࡶ࠯ࡵ࡯࡭ࡨ࡫ࠨ࠱࠮ࠣࡴࡷࡵࡣࡦࡵࡶ࠲ࡦࡸࡧࡷ࠰࡯ࡩࡳ࡭ࡴࡩࠢ࠰ࠤ࠸࠯࠻ࠋࡥࡲࡲࡸࡺࠠࡪ࡯ࡳࡳࡷࡺ࡟ࡱ࡮ࡤࡽࡼࡸࡩࡨࡪࡷ࠸ࡤࡨࡳࡵࡣࡦ࡯ࠥࡃࠠࡳࡧࡴࡹ࡮ࡸࡥࠩࠤࡳࡰࡦࡿࡷࡳ࡫ࡪ࡬ࡹࠨࠩ࠼ࠌ࡬ࡱࡵࡵࡲࡵࡡࡳࡰࡦࡿࡷࡳ࡫ࡪ࡬ࡹ࠺࡟ࡣࡵࡷࡥࡨࡱ࠮ࡤࡪࡵࡳࡲ࡯ࡵ࡮࠰࡯ࡥࡺࡴࡣࡩࠢࡀࠤࡦࡹࡹ࡯ࡥࠣࠬࡱࡧࡵ࡯ࡥ࡫ࡓࡵࡺࡩࡰࡰࡶ࠭ࠥࡃ࠾ࠡࡽࡾࠎࠥࠦ࡬ࡦࡶࠣࡧࡦࡶࡳ࠼ࠌࠣࠤࡹࡸࡹࠡࡽࡾࠎࠥࠦࠠࠡࡥࡤࡴࡸࠦ࠽ࠡࡌࡖࡓࡓ࠴ࡰࡢࡴࡶࡩ࠭ࡨࡳࡵࡣࡦ࡯ࡤࡩࡡࡱࡵࠬ࠿ࠏࠦࠠࡾࡿࠣࡧࡦࡺࡣࡩࠢࠫࡩࡽ࠯ࠠࡼࡽࠍࠤࠥࠦࠠࡤࡱࡱࡷࡴࡲࡥ࠯ࡧࡵࡶࡴࡸࠨࠣࡈࡤ࡭ࡱ࡫ࡤࠡࡶࡲࠤࡵࡧࡲࡴࡧࠣࡧࡦࡶࡡࡣ࡫࡯࡭ࡹ࡯ࡥࡴ࠼ࠥ࠰ࠥ࡫ࡸࠪ࠽ࠍࠤࠥࢃࡽࠋࠢࠣࡶࡪࡺࡵࡳࡰࠣࡥࡼࡧࡩࡵࠢ࡬ࡱࡵࡵࡲࡵࡡࡳࡰࡦࡿࡷࡳ࡫ࡪ࡬ࡹ࠺࡟ࡣࡵࡷࡥࡨࡱ࠮ࡤࡪࡵࡳࡲ࡯ࡵ࡮࠰ࡦࡳࡳࡴࡥࡤࡶࠫࡿࢀࠐࠠࠡࠢࠣࡻࡸࡋ࡮ࡥࡲࡲ࡭ࡳࡺ࠺ࠡࠩࡾࡧࡩࡶࡕࡳ࡮ࢀࠫࠥ࠱ࠠࡦࡰࡦࡳࡩ࡫ࡕࡓࡋࡆࡳࡲࡶ࡯࡯ࡧࡱࡸ࠭ࡐࡓࡐࡐ࠱ࡷࡹࡸࡩ࡯ࡩ࡬ࡪࡾ࠮ࡣࡢࡲࡶ࠭࠮࠲ࠊࠡࠢࠣࠤ࠳࠴࠮࡭ࡣࡸࡲࡨ࡮ࡏࡱࡶ࡬ࡳࡳࡹࠊࠡࠢࢀࢁ࠮ࡁࠊࡾࡿ࠾ࠎ࠴࠰ࠠ࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࡁࡂࡃ࠽࠾࠿ࡀࠤ࠯࠵ࠊࠨࠩࠪଞ").format(bstack11l1111l_opy_=bstack11l1111l_opy_)
            lines.insert(1, bstack1l111111l_opy_)
            f.seek(0)
            with open(os.path.join(os.path.dirname(args[1]), bstack1ll_opy_ (u"ࠧ࡯࡮ࡥࡧࡻࡣࡧࡹࡴࡢࡥ࡮࠲࡯ࡹࠢଟ")), bstack1ll_opy_ (u"࠭ࡷࠨଠ")) as bstack1l1l111l11_opy_:
              bstack1l1l111l11_opy_.writelines(lines)
        CONFIG[bstack1ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰ࡙ࡄࡌࠩଡ")] = str(bstack11l11ll111_opy_) + str(__version__)
        bstack1111l1lll_opy_ = os.environ[bstack1ll_opy_ (u"ࠨࡄࡕࡓ࡜࡙ࡅࡓࡕࡗࡅࡈࡑ࡟ࡕࡇࡖࡘࡍ࡛ࡂࡠࡗࡘࡍࡉ࠭ଢ")]
        bstack11l1l111ll_opy_ = bstack1ll1l1l1l_opy_.bstack1ll1111ll1_opy_(CONFIG, bstack11l11ll111_opy_)
        CONFIG[bstack1ll_opy_ (u"ࠩࡷࡩࡸࡺࡨࡶࡤࡅࡹ࡮ࡲࡤࡖࡷ࡬ࡨࠬଣ")] = bstack1111l1lll_opy_
        CONFIG[bstack1ll_opy_ (u"ࠪࡦࡺ࡯࡬ࡥࡒࡵࡳࡩࡻࡣࡵࡏࡤࡴࠬତ")] = bstack11l1l111ll_opy_
        bstack11l1l1l1_opy_ = 0 if bstack11l1l111l_opy_ < 0 else bstack11l1l111l_opy_
        try:
          if bstack11lllllll1_opy_ is True:
            bstack11l1l1l1_opy_ = int(multiprocessing.current_process().name)
          elif bstack11l1l1111l_opy_ is True:
            bstack11l1l1l1_opy_ = int(threading.current_thread().name)
        except:
          bstack11l1l1l1_opy_ = 0
        CONFIG[bstack1ll_opy_ (u"ࠦࡺࡹࡥࡘ࠵ࡆࠦଥ")] = False
        CONFIG[bstack1ll_opy_ (u"ࠧ࡯ࡳࡑ࡮ࡤࡽࡼࡸࡩࡨࡪࡷࠦଦ")] = True
        bstack1l1l111ll1_opy_ = bstack1l1111llll_opy_(CONFIG, bstack11l1l1l1_opy_)
        logger.debug(bstack11ll1l1l_opy_.format(str(bstack1l1l111ll1_opy_)))
        if CONFIG.get(bstack1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯ࡑࡵࡣࡢ࡮ࠪଧ")):
          bstack1l1l1111ll_opy_(bstack1l1l111ll1_opy_)
        if bstack1ll_opy_ (u"ࠧࡱ࡮ࡤࡸ࡫ࡵࡲ࡮ࡵࠪନ") in CONFIG and bstack1ll_opy_ (u"ࠨࡵࡨࡷࡸ࡯࡯࡯ࡐࡤࡱࡪ࠭଩") in CONFIG[bstack1ll_opy_ (u"ࠩࡳࡰࡦࡺࡦࡰࡴࡰࡷࠬପ")][bstack11l1l1l1_opy_]:
          bstack1llll1111l_opy_ = CONFIG[bstack1ll_opy_ (u"ࠪࡴࡱࡧࡴࡧࡱࡵࡱࡸ࠭ଫ")][bstack11l1l1l1_opy_][bstack1ll_opy_ (u"ࠫࡸ࡫ࡳࡴ࡫ࡲࡲࡓࡧ࡭ࡦࠩବ")]
        args.append(os.path.join(os.path.expanduser(bstack1ll_opy_ (u"ࠬࢄࠧଭ")), bstack1ll_opy_ (u"࠭࠮ࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰ࠭ମ"), bstack1ll_opy_ (u"ࠧ࠯ࡵࡨࡷࡸ࡯࡯࡯࡫ࡧࡷ࠳ࡺࡸࡵࠩଯ")))
        args.append(str(threading.get_ident()))
        args.append(json.dumps(bstack1l1l111ll1_opy_))
        args[1] = os.path.join(os.path.dirname(args[1]), bstack1ll_opy_ (u"ࠣ࡫ࡱࡨࡪࡾ࡟ࡣࡵࡷࡥࡨࡱ࠮࡫ࡵࠥର"))
      bstack111lllll_opy_ = True
      return bstack1l1l111l1_opy_(self, args, bufsize=bufsize, executable=executable,
                    stdin=stdin, stdout=stdout, stderr=stderr,
                    preexec_fn=preexec_fn, close_fds=close_fds,
                    shell=shell, cwd=cwd, env=env, universal_newlines=universal_newlines,
                    startupinfo=startupinfo, creationflags=creationflags,
                    restore_signals=restore_signals, start_new_session=start_new_session,
                    pass_fds=pass_fds, user=user, group=group, extra_groups=extra_groups,
                    encoding=encoding, errors=errors, text=text, umask=umask, pipesize=pipesize)
  except Exception as e:
    pass
  import playwright._impl._api_structures
  import playwright._impl._helper
  def bstack1l11ll11_opy_(self,
        executablePath = None,
        channel = None,
        args = None,
        ignoreDefaultArgs = None,
        handleSIGINT = None,
        handleSIGTERM = None,
        handleSIGHUP = None,
        timeout = None,
        env = None,
        headless = None,
        devtools = None,
        proxy = None,
        downloadsPath = None,
        slowMo = None,
        tracesDir = None,
        chromiumSandbox = None,
        firefoxUserPrefs = None
        ):
    global CONFIG
    global bstack11l1l111l_opy_
    global bstack1llll1111l_opy_
    global bstack11lllllll1_opy_
    global bstack11l1l1111l_opy_
    global bstack11l11ll111_opy_
    CONFIG[bstack1ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫ࡔࡆࡎࠫ଱")] = str(bstack11l11ll111_opy_) + str(__version__)
    bstack1111l1lll_opy_ = os.environ[bstack1ll_opy_ (u"ࠪࡆࡗࡕࡗࡔࡇࡕࡗ࡙ࡇࡃࡌࡡࡗࡉࡘ࡚ࡈࡖࡄࡢ࡙࡚ࡏࡄࠨଲ")]
    bstack11l1l111ll_opy_ = bstack1ll1l1l1l_opy_.bstack1ll1111ll1_opy_(CONFIG, bstack11l11ll111_opy_)
    CONFIG[bstack1ll_opy_ (u"ࠫࡹ࡫ࡳࡵࡪࡸࡦࡇࡻࡩ࡭ࡦࡘࡹ࡮ࡪࠧଳ")] = bstack1111l1lll_opy_
    CONFIG[bstack1ll_opy_ (u"ࠬࡨࡵࡪ࡮ࡧࡔࡷࡵࡤࡶࡥࡷࡑࡦࡶࠧ଴")] = bstack11l1l111ll_opy_
    bstack11l1l1l1_opy_ = 0 if bstack11l1l111l_opy_ < 0 else bstack11l1l111l_opy_
    try:
      if bstack11lllllll1_opy_ is True:
        bstack11l1l1l1_opy_ = int(multiprocessing.current_process().name)
      elif bstack11l1l1111l_opy_ is True:
        bstack11l1l1l1_opy_ = int(threading.current_thread().name)
    except:
      bstack11l1l1l1_opy_ = 0
    CONFIG[bstack1ll_opy_ (u"ࠨࡩࡴࡒ࡯ࡥࡾࡽࡲࡪࡩ࡫ࡸࠧଵ")] = True
    bstack1l1l111ll1_opy_ = bstack1l1111llll_opy_(CONFIG, bstack11l1l1l1_opy_)
    logger.debug(bstack11ll1l1l_opy_.format(str(bstack1l1l111ll1_opy_)))
    if CONFIG.get(bstack1ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰࡒ࡯ࡤࡣ࡯ࠫଶ")):
      bstack1l1l1111ll_opy_(bstack1l1l111ll1_opy_)
    if bstack1ll_opy_ (u"ࠨࡲ࡯ࡥࡹ࡬࡯ࡳ࡯ࡶࠫଷ") in CONFIG and bstack1ll_opy_ (u"ࠩࡶࡩࡸࡹࡩࡰࡰࡑࡥࡲ࡫ࠧସ") in CONFIG[bstack1ll_opy_ (u"ࠪࡴࡱࡧࡴࡧࡱࡵࡱࡸ࠭ହ")][bstack11l1l1l1_opy_]:
      bstack1llll1111l_opy_ = CONFIG[bstack1ll_opy_ (u"ࠫࡵࡲࡡࡵࡨࡲࡶࡲࡹࠧ଺")][bstack11l1l1l1_opy_][bstack1ll_opy_ (u"ࠬࡹࡥࡴࡵ࡬ࡳࡳࡔࡡ࡮ࡧࠪ଻")]
    import urllib
    import json
    if bstack1ll_opy_ (u"࠭ࡴࡶࡴࡥࡳࡘࡩࡡ࡭ࡧ଼ࠪ") in CONFIG and str(CONFIG[bstack1ll_opy_ (u"ࠧࡵࡷࡵࡦࡴ࡙ࡣࡢ࡮ࡨࠫଽ")]).lower() != bstack1ll_opy_ (u"ࠨࡨࡤࡰࡸ࡫ࠧା"):
        bstack11llllll_opy_ = bstack11lll11ll1_opy_()
        bstack11l1111l_opy_ = bstack11llllll_opy_ + urllib.parse.quote(json.dumps(bstack1l1l111ll1_opy_))
    else:
        bstack11l1111l_opy_ = bstack1ll_opy_ (u"ࠩࡺࡷࡸࡀ࠯࠰ࡥࡧࡴ࠳ࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮࠲ࡨࡵ࡭࠰ࡲ࡯ࡥࡾࡽࡲࡪࡩ࡫ࡸࡄࡩࡡࡱࡵࡀࠫି") + urllib.parse.quote(json.dumps(bstack1l1l111ll1_opy_))
    browser = self.connect(bstack11l1111l_opy_)
    return browser
except Exception as e:
    pass
def bstack1l11l1l1_opy_():
    global bstack111lllll_opy_
    global bstack11l11ll111_opy_
    global CONFIG
    try:
        from playwright._impl._browser_type import BrowserType
        from bstack_utils.helper import bstack111lllll1_opy_
        global bstack1ll1l1l111_opy_
        if not bstack11l111llll_opy_:
          global bstack111lll1l1l_opy_
          if not bstack111lll1l1l_opy_:
            from bstack_utils.helper import bstack1l1111l11_opy_, bstack11l1lllll_opy_, bstack111ll1l11_opy_
            bstack111lll1l1l_opy_ = bstack1l1111l11_opy_()
            bstack11l1lllll_opy_(bstack11l11ll111_opy_)
            bstack11l1l111ll_opy_ = bstack1ll1l1l1l_opy_.bstack1ll1111ll1_opy_(CONFIG, bstack11l11ll111_opy_)
            bstack1ll1l1l111_opy_.bstack111ll1ll1_opy_(bstack1ll_opy_ (u"ࠥࡔࡑࡇ࡙ࡘࡔࡌࡋࡍ࡚࡟ࡑࡔࡒࡈ࡚ࡉࡔࡠࡏࡄࡔࠧୀ"), bstack11l1l111ll_opy_)
          BrowserType.connect = bstack111lllll1_opy_
          return
        BrowserType.launch = bstack1l11ll11_opy_
        bstack111lllll_opy_ = True
    except Exception as e:
        pass
    try:
      import Browser
      from subprocess import Popen
      Popen.__init__ = bstack1ll111l1l_opy_
      bstack111lllll_opy_ = True
    except Exception as e:
      pass
def bstack1lll111ll1_opy_(context, bstack1llllll1ll_opy_):
  try:
    context.page.evaluate(bstack1ll_opy_ (u"ࠦࡤࠦ࠽࠿ࠢࡾࢁࠧୁ"), bstack1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮ࡣࡪࡾࡥࡤࡷࡷࡳࡷࡀࠠࡼࠤࡤࡧࡹ࡯࡯࡯ࠤ࠽ࠤࠧࡹࡥࡵࡕࡨࡷࡸ࡯࡯࡯ࡐࡤࡱࡪࠨࠬࠡࠤࡤࡶ࡬ࡻ࡭ࡦࡰࡷࡷࠧࡀࠠࡼࠤࡱࡥࡲ࡫ࠢ࠻ࠩୂ")+ json.dumps(bstack1llllll1ll_opy_) + bstack1ll_opy_ (u"ࠨࡽࡾࠤୃ"))
  except Exception as e:
    logger.debug(bstack1ll_opy_ (u"ࠢࡦࡺࡦࡩࡵࡺࡩࡰࡰࠣ࡭ࡳࠦࡰ࡭ࡣࡼࡻࡷ࡯ࡧࡩࡶࠣࡷࡪࡹࡳࡪࡱࡱࠤࡳࡧ࡭ࡦࠢࡾࢁ࠿ࠦࡻࡾࠤୄ").format(str(e), traceback.format_exc()))
def bstack1l111ll11l_opy_(context, message, level):
  try:
    context.page.evaluate(bstack1ll_opy_ (u"ࠣࡡࠣࡁࡃࠦࡻࡾࠤ୅"), bstack1ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫ࡠࡧࡻࡩࡨࡻࡴࡰࡴ࠽ࠤࢀࠨࡡࡤࡶ࡬ࡳࡳࠨ࠺ࠡࠤࡤࡲࡳࡵࡴࡢࡶࡨࠦ࠱ࠦࠢࡢࡴࡪࡹࡲ࡫࡮ࡵࡵࠥ࠾ࠥࢁࠢࡥࡣࡷࡥࠧࡀࠧ୆") + json.dumps(message) + bstack1ll_opy_ (u"ࠪ࠰ࠧࡲࡥࡷࡧ࡯ࠦ࠿࠭େ") + json.dumps(level) + bstack1ll_opy_ (u"ࠫࢂࢃࠧୈ"))
  except Exception as e:
    logger.debug(bstack1ll_opy_ (u"ࠧ࡫ࡸࡤࡧࡳࡸ࡮ࡵ࡮ࠡ࡫ࡱࠤࡵࡲࡡࡺࡹࡵ࡭࡬࡮ࡴࠡࡣࡱࡲࡴࡺࡡࡵ࡫ࡲࡲࠥࢁࡽ࠻ࠢࡾࢁࠧ୉").format(str(e), traceback.format_exc()))
@measure(event_name=EVENTS.bstack1ll1l111ll_opy_, stage=STAGE.bstack1l1lll1ll1_opy_, bstack1l1l11ll_opy_=bstack1llll1111l_opy_)
def bstack1l11l11111_opy_(self, url):
  global bstack1ll11l11l1_opy_
  try:
    bstack111llll1l_opy_(url)
  except Exception as err:
    logger.debug(bstack1llll1l1l1_opy_.format(str(err)))
  try:
    bstack1ll11l11l1_opy_(self, url)
  except Exception as e:
    try:
      bstack11lllll1ll_opy_ = str(e)
      if any(err_msg in bstack11lllll1ll_opy_ for err_msg in bstack1ll11ll111_opy_):
        bstack111llll1l_opy_(url, True)
    except Exception as err:
      logger.debug(bstack1llll1l1l1_opy_.format(str(err)))
    raise e
def bstack1l11l111ll_opy_(self):
  global bstack1lll111l_opy_
  bstack1lll111l_opy_ = self
  return
def bstack1llll1l1_opy_(self):
  global bstack111llll11_opy_
  bstack111llll11_opy_ = self
  return
def bstack11l11ll1ll_opy_(test_name, bstack111l1lll1_opy_):
  global CONFIG
  if percy.bstack11ll11lll1_opy_() == bstack1ll_opy_ (u"ࠨࡴࡳࡷࡨࠦ୊"):
    bstack1llll11l_opy_ = os.path.relpath(bstack111l1lll1_opy_, start=os.getcwd())
    suite_name, _ = os.path.splitext(bstack1llll11l_opy_)
    bstack1l1l11ll_opy_ = suite_name + bstack1ll_opy_ (u"ࠢ࠮ࠤୋ") + test_name
    threading.current_thread().percySessionName = bstack1l1l11ll_opy_
def bstack1l1l11ll11_opy_(self, test, *args, **kwargs):
  global bstack1l1l11ll1l_opy_
  test_name = None
  bstack111l1lll1_opy_ = None
  if test:
    test_name = str(test.name)
    bstack111l1lll1_opy_ = str(test.source)
  bstack11l11ll1ll_opy_(test_name, bstack111l1lll1_opy_)
  bstack1l1l11ll1l_opy_(self, test, *args, **kwargs)
@measure(event_name=EVENTS.bstack111llll111_opy_, stage=STAGE.bstack1l1lll1ll1_opy_, bstack1l1l11ll_opy_=bstack1llll1111l_opy_)
def bstack1l1l11lll_opy_(driver, bstack1l1l11ll_opy_):
  if not bstack1111l11ll_opy_ and bstack1l1l11ll_opy_:
      bstack1l1lll1l1l_opy_ = {
          bstack1ll_opy_ (u"ࠨࡣࡦࡸ࡮ࡵ࡮ࠨୌ"): bstack1ll_opy_ (u"ࠩࡶࡩࡹ࡙ࡥࡴࡵ࡬ࡳࡳࡔࡡ࡮ࡧ୍ࠪ"),
          bstack1ll_opy_ (u"ࠪࡥࡷ࡭ࡵ࡮ࡧࡱࡸࡸ࠭୎"): {
              bstack1ll_opy_ (u"ࠫࡳࡧ࡭ࡦࠩ୏"): bstack1l1l11ll_opy_
          }
      }
      bstack1llll11l11_opy_ = bstack1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮ࡣࡪࡾࡥࡤࡷࡷࡳࡷࡀࠠࡼࡿࠪ୐").format(json.dumps(bstack1l1lll1l1l_opy_))
      driver.execute_script(bstack1llll11l11_opy_)
  if bstack11l111l1ll_opy_:
      bstack11l111ll_opy_ = {
          bstack1ll_opy_ (u"࠭ࡡࡤࡶ࡬ࡳࡳ࠭୑"): bstack1ll_opy_ (u"ࠧࡢࡰࡱࡳࡹࡧࡴࡦࠩ୒"),
          bstack1ll_opy_ (u"ࠨࡣࡵ࡫ࡺࡳࡥ࡯ࡶࡶࠫ୓"): {
              bstack1ll_opy_ (u"ࠩࡧࡥࡹࡧࠧ୔"): bstack1l1l11ll_opy_ + bstack1ll_opy_ (u"ࠪࠤࡵࡧࡳࡴࡧࡧࠥࠬ୕"),
              bstack1ll_opy_ (u"ࠫࡱ࡫ࡶࡦ࡮ࠪୖ"): bstack1ll_opy_ (u"ࠬ࡯࡮ࡧࡱࠪୗ")
          }
      }
      if bstack11l111l1ll_opy_.status == bstack1ll_opy_ (u"࠭ࡐࡂࡕࡖࠫ୘"):
          bstack1111l1l1_opy_ = bstack1ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰࡥࡥࡹࡧࡦࡹࡹࡵࡲ࠻ࠢࡾࢁࠬ୙").format(json.dumps(bstack11l111ll_opy_))
          driver.execute_script(bstack1111l1l1_opy_)
          bstack11ll11111l_opy_(driver, bstack1ll_opy_ (u"ࠨࡲࡤࡷࡸ࡫ࡤࠨ୚"))
      elif bstack11l111l1ll_opy_.status == bstack1ll_opy_ (u"ࠩࡉࡅࡎࡒࠧ୛"):
          reason = bstack1ll_opy_ (u"ࠥࠦଡ଼")
          bstack1l1l1l1l1_opy_ = bstack1l1l11ll_opy_ + bstack1ll_opy_ (u"ࠫࠥ࡬ࡡࡪ࡮ࡨࡨࠬଢ଼")
          if bstack11l111l1ll_opy_.message:
              reason = str(bstack11l111l1ll_opy_.message)
              bstack1l1l1l1l1_opy_ = bstack1l1l1l1l1_opy_ + bstack1ll_opy_ (u"ࠬࠦࡷࡪࡶ࡫ࠤࡪࡸࡲࡰࡴ࠽ࠤࠬ୞") + reason
          bstack11l111ll_opy_[bstack1ll_opy_ (u"࠭ࡡࡳࡩࡸࡱࡪࡴࡴࡴࠩୟ")] = {
              bstack1ll_opy_ (u"ࠧ࡭ࡧࡹࡩࡱ࠭ୠ"): bstack1ll_opy_ (u"ࠨࡧࡵࡶࡴࡸࠧୡ"),
              bstack1ll_opy_ (u"ࠩࡧࡥࡹࡧࠧୢ"): bstack1l1l1l1l1_opy_
          }
          bstack1111l1l1_opy_ = bstack1ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬ࡡࡨࡼࡪࡩࡵࡵࡱࡵ࠾ࠥࢁࡽࠨୣ").format(json.dumps(bstack11l111ll_opy_))
          driver.execute_script(bstack1111l1l1_opy_)
          bstack11ll11111l_opy_(driver, bstack1ll_opy_ (u"ࠫ࡫ࡧࡩ࡭ࡧࡧࠫ୤"), reason)
          bstack11l111ll1l_opy_(reason, str(bstack11l111l1ll_opy_), str(bstack11l1l111l_opy_), logger)
@measure(event_name=EVENTS.bstack1l1l1ll1_opy_, stage=STAGE.bstack1l1lll1ll1_opy_, bstack1l1l11ll_opy_=bstack1llll1111l_opy_)
def bstack1ll1ll1lll_opy_(driver, test):
  if percy.bstack11ll11lll1_opy_() == bstack1ll_opy_ (u"ࠧࡺࡲࡶࡧࠥ୥") and percy.bstack1l1l1111l1_opy_() == bstack1ll_opy_ (u"ࠨࡴࡦࡵࡷࡧࡦࡹࡥࠣ୦"):
      bstack1111lll1l_opy_ = bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠧࡱࡧࡵࡧࡾ࡙ࡥࡴࡵ࡬ࡳࡳࡔࡡ࡮ࡧࠪ୧"), None)
      bstack11l111ll11_opy_(driver, bstack1111lll1l_opy_, test)
  if (bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠨ࡫ࡶࡅ࠶࠷ࡹࡕࡧࡶࡸࠬ୨"), None) and
      bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠩࡤ࠵࠶ࡿࡐ࡭ࡣࡷࡪࡴࡸ࡭ࠨ୩"), None)) or (
      bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠪ࡭ࡸࡇࡰࡱࡃ࠴࠵ࡾ࡚ࡥࡴࡶࠪ୪"), None) and
      bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠫࡦࡶࡰࡂ࠳࠴ࡽࡕࡲࡡࡵࡨࡲࡶࡲ࠭୫"), None)):
      logger.info(bstack1ll_opy_ (u"ࠧࡇࡵࡵࡱࡰࡥࡹ࡫ࠠࡵࡧࡶࡸࠥࡩࡡࡴࡧࠣࡩࡽ࡫ࡣࡶࡶ࡬ࡳࡳࠦࡨࡢࡵࠣࡩࡳࡪࡥࡥ࠰ࠣࡔࡷࡵࡣࡦࡵࡶ࡭ࡳ࡭ࠠࡧࡱࡵࠤࡦࡩࡣࡦࡵࡶ࡭ࡧ࡯࡬ࡪࡶࡼࠤࡹ࡫ࡳࡵ࡫ࡱ࡫ࠥ࡯ࡳࠡࡷࡱࡨࡪࡸࡷࡢࡻ࠱ࠤࠧ୬"))
      bstack1llll1l11_opy_.bstack111111l11_opy_(driver, name=test.name, path=test.source)
def bstack11l11ll1l1_opy_(test, bstack1l1l11ll_opy_):
    try:
      bstack11l1l1l1ll_opy_ = datetime.datetime.now()
      data = {}
      if test:
        data[bstack1ll_opy_ (u"࠭࡮ࡢ࡯ࡨࠫ୭")] = bstack1l1l11ll_opy_
      if bstack11l111l1ll_opy_:
        if bstack11l111l1ll_opy_.status == bstack1ll_opy_ (u"ࠧࡑࡃࡖࡗࠬ୮"):
          data[bstack1ll_opy_ (u"ࠨࡵࡷࡥࡹࡻࡳࠨ୯")] = bstack1ll_opy_ (u"ࠩࡳࡥࡸࡹࡥࡥࠩ୰")
        elif bstack11l111l1ll_opy_.status == bstack1ll_opy_ (u"ࠪࡊࡆࡏࡌࠨୱ"):
          data[bstack1ll_opy_ (u"ࠫࡸࡺࡡࡵࡷࡶࠫ୲")] = bstack1ll_opy_ (u"ࠬ࡬ࡡࡪ࡮ࡨࡨࠬ୳")
          if bstack11l111l1ll_opy_.message:
            data[bstack1ll_opy_ (u"࠭ࡲࡦࡣࡶࡳࡳ࠭୴")] = str(bstack11l111l1ll_opy_.message)
      user = CONFIG[bstack1ll_opy_ (u"ࠧࡶࡵࡨࡶࡓࡧ࡭ࡦࠩ୵")]
      key = CONFIG[bstack1ll_opy_ (u"ࠨࡣࡦࡧࡪࡹࡳࡌࡧࡼࠫ୶")]
      host = bstack11l1111l1_opy_(cli.config, [bstack1ll_opy_ (u"ࠤࡤࡴ࡮ࡹࠢ୷"), bstack1ll_opy_ (u"ࠥࡥࡺࡺ࡯࡮ࡣࡷࡩࠧ୸"), bstack1ll_opy_ (u"ࠦࡦࡶࡩࠣ୹")], bstack1ll_opy_ (u"ࠧ࡮ࡴࡵࡲࡶ࠾࠴࠵ࡡࡱ࡫࠱ࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬࠰ࡦࡳࡲࠨ୺"))
      url = bstack1ll_opy_ (u"࠭ࡻࡾ࠱ࡤࡹࡹࡵ࡭ࡢࡶࡨ࠳ࡸ࡫ࡳࡴ࡫ࡲࡲࡸ࠵ࡻࡾ࠰࡭ࡷࡴࡴࠧ୻").format(host, bstack1111l1l11_opy_)
      headers = {
        bstack1ll_opy_ (u"ࠧࡄࡱࡱࡸࡪࡴࡴ࠮ࡶࡼࡴࡪ࠭୼"): bstack1ll_opy_ (u"ࠨࡣࡳࡴࡱ࡯ࡣࡢࡶ࡬ࡳࡳ࠵ࡪࡴࡱࡱࠫ୽"),
      }
      if bool(data):
        requests.put(url, json=data, headers=headers, auth=(user, key))
        cli.bstack11ll11ll1_opy_(bstack1ll_opy_ (u"ࠤ࡫ࡸࡹࡶ࠺ࡶࡲࡧࡥࡹ࡫࡟ࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰࡥࡳࡵࡣࡷࡹࡸࠨ୾"), datetime.datetime.now() - bstack11l1l1l1ll_opy_)
    except Exception as e:
      logger.error(bstack111llll11l_opy_.format(str(e)))
def bstack11l1ll11_opy_(test, bstack1l1l11ll_opy_):
  global CONFIG
  global bstack111llll11_opy_
  global bstack1lll111l_opy_
  global bstack1111l1l11_opy_
  global bstack11l111l1ll_opy_
  global bstack1llll1111l_opy_
  global bstack111l11l1l_opy_
  global bstack11ll1ll11_opy_
  global bstack1ll11l1lll_opy_
  global bstack1lll1llll1_opy_
  global bstack1llll11lll_opy_
  global bstack111l11111_opy_
  global bstack11llll1l_opy_
  try:
    if not bstack1111l1l11_opy_:
      with bstack11llll1l_opy_:
        bstack11lll1l1l1_opy_ = os.path.join(os.path.expanduser(bstack1ll_opy_ (u"ࠪࢂࠬ୿")), bstack1ll_opy_ (u"ࠫ࠳ࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮ࠫ஀"), bstack1ll_opy_ (u"ࠬ࠴ࡳࡦࡵࡶ࡭ࡴࡴࡩࡥࡵ࠱ࡸࡽࡺࠧ஁"))
        if os.path.exists(bstack11lll1l1l1_opy_):
          with open(bstack11lll1l1l1_opy_, bstack1ll_opy_ (u"࠭ࡲࠨஂ")) as f:
            content = f.read().strip()
            if content:
              bstack11l111l1l1_opy_ = json.loads(bstack1ll_opy_ (u"ࠢࡼࠤஃ") + content + bstack1ll_opy_ (u"ࠨࠤࡻࠦ࠿ࠦࠢࡺࠤࠪ஄") + bstack1ll_opy_ (u"ࠤࢀࠦஅ"))
              bstack1111l1l11_opy_ = bstack11l111l1l1_opy_.get(str(threading.get_ident()))
  except Exception as e:
    logger.debug(bstack1ll_opy_ (u"ࠪࡉࡷࡸ࡯ࡳࠢࡵࡩࡦࡪࡩ࡯ࡩࠣࡷࡪࡹࡳࡪࡱࡱࠤࡎࡊࡳࠡࡨ࡬ࡰࡪࡀࠠࠨஆ") + str(e))
  if bstack1llll11lll_opy_:
    with bstack1lll11l1l_opy_:
      bstack1l11l11ll1_opy_ = bstack1llll11lll_opy_.copy()
    for driver in bstack1l11l11ll1_opy_:
      if bstack1111l1l11_opy_ == driver.session_id:
        if test:
          bstack1ll1ll1lll_opy_(driver, test)
        bstack1l1l11lll_opy_(driver, bstack1l1l11ll_opy_)
  elif bstack1111l1l11_opy_:
    bstack11l11ll1l1_opy_(test, bstack1l1l11ll_opy_)
  if bstack111llll11_opy_:
    bstack11ll1ll11_opy_(bstack111llll11_opy_)
  if bstack1lll111l_opy_:
    bstack1ll11l1lll_opy_(bstack1lll111l_opy_)
  if bstack1ll1l1ll_opy_:
    bstack1lll1llll1_opy_()
def bstack1l111l1ll1_opy_(self, test, *args, **kwargs):
  bstack1l1l11ll_opy_ = None
  if test:
    bstack1l1l11ll_opy_ = str(test.name)
  bstack11l1ll11_opy_(test, bstack1l1l11ll_opy_)
  bstack111l11l1l_opy_(self, test, *args, **kwargs)
def bstack1ll1l111l_opy_(self, parent, test, skip_on_failure=None, rpa=False):
  global bstack11l1ll1111_opy_
  global CONFIG
  global bstack1llll11lll_opy_
  global bstack1111l1l11_opy_
  global bstack11llll1l_opy_
  bstack1l1l11l1_opy_ = None
  try:
    if bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠫࡦ࠷࠱ࡺࡒ࡯ࡥࡹ࡬࡯ࡳ࡯ࠪஇ"), None) or bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠬࡧࡰࡱࡃ࠴࠵ࡾࡖ࡬ࡢࡶࡩࡳࡷࡳࠧஈ"), None):
      try:
        if not bstack1111l1l11_opy_:
          bstack11lll1l1l1_opy_ = os.path.join(os.path.expanduser(bstack1ll_opy_ (u"࠭ࡾࠨஉ")), bstack1ll_opy_ (u"ࠧ࠯ࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱࠧஊ"), bstack1ll_opy_ (u"ࠨ࠰ࡶࡩࡸࡹࡩࡰࡰ࡬ࡨࡸ࠴ࡴࡹࡶࠪ஋"))
          with bstack11llll1l_opy_:
            if os.path.exists(bstack11lll1l1l1_opy_):
              with open(bstack11lll1l1l1_opy_, bstack1ll_opy_ (u"ࠩࡵࠫ஌")) as f:
                content = f.read().strip()
                if content:
                  bstack11l111l1l1_opy_ = json.loads(bstack1ll_opy_ (u"ࠥࡿࠧ஍") + content + bstack1ll_opy_ (u"ࠫࠧࡾࠢ࠻ࠢࠥࡽࠧ࠭எ") + bstack1ll_opy_ (u"ࠧࢃࠢஏ"))
                  bstack1111l1l11_opy_ = bstack11l111l1l1_opy_.get(str(threading.get_ident()))
      except Exception as e:
        logger.debug(bstack1ll_opy_ (u"࠭ࡅࡳࡴࡲࡶࠥࡸࡥࡢࡦ࡬ࡲ࡬ࠦࡳࡦࡵࡶ࡭ࡴࡴࠠࡊࡆࡶࠤ࡫࡯࡬ࡦࠢ࡬ࡲࠥࡺࡥࡴࡶࠣࡷࡹࡧࡴࡶࡵ࠽ࠤࠬஐ") + str(e))
      if bstack1llll11lll_opy_:
        with bstack1lll11l1l_opy_:
          bstack1l11l11ll1_opy_ = bstack1llll11lll_opy_.copy()
        for driver in bstack1l11l11ll1_opy_:
          if bstack1111l1l11_opy_ == driver.session_id:
            bstack1l1l11l1_opy_ = driver
    bstack1lllll11_opy_ = bstack1llll1l11_opy_.bstack1ll11ll1_opy_(test.tags)
    if bstack1l1l11l1_opy_:
      threading.current_thread().isA11yTest = bstack1llll1l11_opy_.bstack1l11l111l1_opy_(bstack1l1l11l1_opy_, bstack1lllll11_opy_)
      threading.current_thread().isAppA11yTest = bstack1llll1l11_opy_.bstack1l11l111l1_opy_(bstack1l1l11l1_opy_, bstack1lllll11_opy_)
    else:
      threading.current_thread().isA11yTest = bstack1lllll11_opy_
      threading.current_thread().isAppA11yTest = bstack1lllll11_opy_
  except:
    pass
  bstack11l1ll1111_opy_(self, parent, test, skip_on_failure=skip_on_failure, rpa=rpa)
  global bstack11l111l1ll_opy_
  try:
    bstack11l111l1ll_opy_ = self._test
  except:
    bstack11l111l1ll_opy_ = self.test
def bstack1lll1llll_opy_():
  global bstack1l11lllll1_opy_
  try:
    if os.path.exists(bstack1l11lllll1_opy_):
      os.remove(bstack1l11lllll1_opy_)
  except Exception as e:
    logger.debug(bstack1ll_opy_ (u"ࠧࡆࡴࡵࡳࡷࠦࡩ࡯ࠢࡧࡩࡱ࡫ࡴࡪࡰࡪࠤࡷࡵࡢࡰࡶࠣࡶࡪࡶ࡯ࡳࡶࠣࡪ࡮ࡲࡥ࠻ࠢࠪ஑") + str(e))
def bstack1ll11llll1_opy_():
  global bstack1l11lllll1_opy_
  bstack11lllll111_opy_ = {}
  lock_file = bstack1l11lllll1_opy_ + bstack1ll_opy_ (u"ࠨ࠰࡯ࡳࡨࡱࠧஒ")
  try:
    from filelock import FileLock
  except ImportError:
    logger.debug(bstack1ll_opy_ (u"ࠩࡩ࡭ࡱ࡫࡬ࡰࡥ࡮ࠤࡳࡵࡴࠡࡣࡹࡥ࡮ࡲࡡࡣ࡮ࡨ࠰ࠥࡻࡳࡪࡰࡪࠤࡧࡧࡳࡪࡥࠣࡪ࡮ࡲࡥࠡࡱࡳࡩࡷࡧࡴࡪࡱࡱࡷࠬஓ"))
    try:
      if not os.path.isfile(bstack1l11lllll1_opy_):
        with open(bstack1l11lllll1_opy_, bstack1ll_opy_ (u"ࠪࡻࠬஔ")) as f:
          json.dump({}, f)
      if os.path.exists(bstack1l11lllll1_opy_):
        with open(bstack1l11lllll1_opy_, bstack1ll_opy_ (u"ࠫࡷ࠭க")) as f:
          content = f.read().strip()
          if content:
            bstack11lllll111_opy_ = json.loads(content)
    except Exception as e:
      logger.debug(bstack1ll_opy_ (u"ࠬࡋࡲࡳࡱࡵࠤ࡮ࡴࠠࡳࡧࡤࡨ࡮ࡴࡧࠡࡴࡲࡦࡴࡺࠠࡳࡧࡳࡳࡷࡺࠠࡧ࡫࡯ࡩ࠿ࠦࠧ஖") + str(e))
    return bstack11lllll111_opy_
  try:
    os.makedirs(os.path.dirname(bstack1l11lllll1_opy_), exist_ok=True)
    with FileLock(lock_file, timeout=10):
      if not os.path.isfile(bstack1l11lllll1_opy_):
        with open(bstack1l11lllll1_opy_, bstack1ll_opy_ (u"࠭ࡷࠨ஗")) as f:
          json.dump({}, f)
      if os.path.exists(bstack1l11lllll1_opy_):
        with open(bstack1l11lllll1_opy_, bstack1ll_opy_ (u"ࠧࡳࠩ஘")) as f:
          content = f.read().strip()
          if content:
            bstack11lllll111_opy_ = json.loads(content)
  except Exception as e:
    logger.debug(bstack1ll_opy_ (u"ࠨࡇࡵࡶࡴࡸࠠࡪࡰࠣࡶࡪࡧࡤࡪࡰࡪࠤࡷࡵࡢࡰࡶࠣࡶࡪࡶ࡯ࡳࡶࠣࡪ࡮ࡲࡥ࠻ࠢࠪங") + str(e))
  finally:
    return bstack11lllll111_opy_
def bstack11l1111111_opy_(platform_index, item_index):
  global bstack1l11lllll1_opy_
  lock_file = bstack1l11lllll1_opy_ + bstack1ll_opy_ (u"ࠩ࠱ࡰࡴࡩ࡫ࠨச")
  try:
    from filelock import FileLock
  except ImportError:
    logger.debug(bstack1ll_opy_ (u"ࠪࡪ࡮ࡲࡥ࡭ࡱࡦ࡯ࠥࡴ࡯ࡵࠢࡤࡺࡦ࡯࡬ࡢࡤ࡯ࡩ࠱ࠦࡵࡴ࡫ࡱ࡫ࠥࡨࡡࡴ࡫ࡦࠤ࡫࡯࡬ࡦࠢࡲࡴࡪࡸࡡࡵ࡫ࡲࡲࡸ࠭஛"))
    try:
      bstack11lllll111_opy_ = {}
      if os.path.exists(bstack1l11lllll1_opy_):
        with open(bstack1l11lllll1_opy_, bstack1ll_opy_ (u"ࠫࡷ࠭ஜ")) as f:
          content = f.read().strip()
          if content:
            bstack11lllll111_opy_ = json.loads(content)
      bstack11lllll111_opy_[item_index] = platform_index
      with open(bstack1l11lllll1_opy_, bstack1ll_opy_ (u"ࠧࡽࠢ஝")) as outfile:
        json.dump(bstack11lllll111_opy_, outfile)
    except Exception as e:
      logger.debug(bstack1ll_opy_ (u"࠭ࡅࡳࡴࡲࡶࠥ࡯࡮ࠡࡹࡵ࡭ࡹ࡯࡮ࡨࠢࡷࡳࠥࡸ࡯ࡣࡱࡷࠤࡷ࡫ࡰࡰࡴࡷࠤ࡫࡯࡬ࡦ࠼ࠣࠫஞ") + str(e))
    return
  try:
    os.makedirs(os.path.dirname(bstack1l11lllll1_opy_), exist_ok=True)
    with FileLock(lock_file, timeout=10):
      bstack11lllll111_opy_ = {}
      if os.path.exists(bstack1l11lllll1_opy_):
        with open(bstack1l11lllll1_opy_, bstack1ll_opy_ (u"ࠧࡳࠩட")) as f:
          content = f.read().strip()
          if content:
            bstack11lllll111_opy_ = json.loads(content)
      bstack11lllll111_opy_[item_index] = platform_index
      with open(bstack1l11lllll1_opy_, bstack1ll_opy_ (u"ࠣࡹࠥ஠")) as outfile:
        json.dump(bstack11lllll111_opy_, outfile)
  except Exception as e:
    logger.debug(bstack1ll_opy_ (u"ࠩࡈࡶࡷࡵࡲࠡ࡫ࡱࠤࡼࡸࡩࡵ࡫ࡱ࡫ࠥࡺ࡯ࠡࡴࡲࡦࡴࡺࠠࡳࡧࡳࡳࡷࡺࠠࡧ࡫࡯ࡩ࠿ࠦࠧ஡") + str(e))
def bstack1l1ll11l11_opy_(bstack1ll11lll1l_opy_):
  global CONFIG
  bstack11lll11lll_opy_ = bstack1ll_opy_ (u"ࠪࠫ஢")
  if not bstack1ll_opy_ (u"ࠫࡵࡲࡡࡵࡨࡲࡶࡲࡹࠧண") in CONFIG:
    logger.info(bstack1ll_opy_ (u"ࠬࡔ࡯ࠡࡲ࡯ࡥࡹ࡬࡯ࡳ࡯ࡶࠤࡵࡧࡳࡴࡧࡧࠤࡺࡴࡡࡣ࡮ࡨࠤࡹࡵࠠࡨࡧࡱࡩࡷࡧࡴࡦࠢࡵࡩࡵࡵࡲࡵࠢࡩࡳࡷࠦࡒࡰࡤࡲࡸࠥࡸࡵ࡯ࠩத"))
  try:
    platform = CONFIG[bstack1ll_opy_ (u"࠭ࡰ࡭ࡣࡷࡪࡴࡸ࡭ࡴࠩ஥")][bstack1ll11lll1l_opy_]
    if bstack1ll_opy_ (u"ࠧࡰࡵࠪ஦") in platform:
      bstack11lll11lll_opy_ += str(platform[bstack1ll_opy_ (u"ࠨࡱࡶࠫ஧")]) + bstack1ll_opy_ (u"ࠩ࠯ࠤࠬந")
    if bstack1ll_opy_ (u"ࠪࡳࡸ࡜ࡥࡳࡵ࡬ࡳࡳ࠭ன") in platform:
      bstack11lll11lll_opy_ += str(platform[bstack1ll_opy_ (u"ࠫࡴࡹࡖࡦࡴࡶ࡭ࡴࡴࠧப")]) + bstack1ll_opy_ (u"ࠬ࠲ࠠࠨ஫")
    if bstack1ll_opy_ (u"࠭ࡤࡦࡸ࡬ࡧࡪࡔࡡ࡮ࡧࠪ஬") in platform:
      bstack11lll11lll_opy_ += str(platform[bstack1ll_opy_ (u"ࠧࡥࡧࡹ࡭ࡨ࡫ࡎࡢ࡯ࡨࠫ஭")]) + bstack1ll_opy_ (u"ࠨ࠮ࠣࠫம")
    if bstack1ll_opy_ (u"ࠩࡳࡰࡦࡺࡦࡰࡴࡰ࡚ࡪࡸࡳࡪࡱࡱࠫய") in platform:
      bstack11lll11lll_opy_ += str(platform[bstack1ll_opy_ (u"ࠪࡴࡱࡧࡴࡧࡱࡵࡱ࡛࡫ࡲࡴ࡫ࡲࡲࠬர")]) + bstack1ll_opy_ (u"ࠫ࠱ࠦࠧற")
    if bstack1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡔࡡ࡮ࡧࠪல") in platform:
      bstack11lll11lll_opy_ += str(platform[bstack1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡎࡢ࡯ࡨࠫள")]) + bstack1ll_opy_ (u"ࠧ࠭ࠢࠪழ")
    if bstack1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡘࡨࡶࡸ࡯࡯࡯ࠩவ") in platform:
      bstack11lll11lll_opy_ += str(platform[bstack1ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴ࡙ࡩࡷࡹࡩࡰࡰࠪஶ")]) + bstack1ll_opy_ (u"ࠪ࠰ࠥ࠭ஷ")
  except Exception as e:
    logger.debug(bstack1ll_opy_ (u"ࠫࡘࡵ࡭ࡦࠢࡨࡶࡷࡵࡲࠡ࡫ࡱࠤ࡬࡫࡮ࡦࡴࡤࡸ࡮ࡴࡧࠡࡲ࡯ࡥࡹ࡬࡯ࡳ࡯ࠣࡷࡹࡸࡩ࡯ࡩࠣࡪࡴࡸࠠࡳࡧࡳࡳࡷࡺࠠࡨࡧࡱࡩࡷࡧࡴࡪࡱࡱࠫஸ") + str(e))
  finally:
    if bstack11lll11lll_opy_[len(bstack11lll11lll_opy_) - 2:] == bstack1ll_opy_ (u"ࠬ࠲ࠠࠨஹ"):
      bstack11lll11lll_opy_ = bstack11lll11lll_opy_[:-2]
    return bstack11lll11lll_opy_
def bstack1lll1ll11l_opy_(path, bstack11lll11lll_opy_):
  try:
    import xml.etree.ElementTree as ET
    bstack1l1l11l1ll_opy_ = ET.parse(path)
    bstack1l1l11llll_opy_ = bstack1l1l11l1ll_opy_.getroot()
    bstack1l1l1111l_opy_ = None
    for suite in bstack1l1l11llll_opy_.iter(bstack1ll_opy_ (u"࠭ࡳࡶ࡫ࡷࡩࠬ஺")):
      if bstack1ll_opy_ (u"ࠧࡴࡱࡸࡶࡨ࡫ࠧ஻") in suite.attrib:
        suite.attrib[bstack1ll_opy_ (u"ࠨࡰࡤࡱࡪ࠭஼")] += bstack1ll_opy_ (u"ࠩࠣࠫ஽") + bstack11lll11lll_opy_
        bstack1l1l1111l_opy_ = suite
    bstack1lllll1ll1_opy_ = None
    for robot in bstack1l1l11llll_opy_.iter(bstack1ll_opy_ (u"ࠪࡶࡴࡨ࡯ࡵࠩா")):
      bstack1lllll1ll1_opy_ = robot
    bstack1l1llll1_opy_ = len(bstack1lllll1ll1_opy_.findall(bstack1ll_opy_ (u"ࠫࡸࡻࡩࡵࡧࠪி")))
    if bstack1l1llll1_opy_ == 1:
      bstack1lllll1ll1_opy_.remove(bstack1lllll1ll1_opy_.findall(bstack1ll_opy_ (u"ࠬࡹࡵࡪࡶࡨࠫீ"))[0])
      bstack11lllllll_opy_ = ET.Element(bstack1ll_opy_ (u"࠭ࡳࡶ࡫ࡷࡩࠬு"), attrib={bstack1ll_opy_ (u"ࠧ࡯ࡣࡰࡩࠬூ"): bstack1ll_opy_ (u"ࠨࡕࡸ࡭ࡹ࡫ࡳࠨ௃"), bstack1ll_opy_ (u"ࠩ࡬ࡨࠬ௄"): bstack1ll_opy_ (u"ࠪࡷ࠵࠭௅")})
      bstack1lllll1ll1_opy_.insert(1, bstack11lllllll_opy_)
      bstack1l1llll1ll_opy_ = None
      for suite in bstack1lllll1ll1_opy_.iter(bstack1ll_opy_ (u"ࠫࡸࡻࡩࡵࡧࠪெ")):
        bstack1l1llll1ll_opy_ = suite
      bstack1l1llll1ll_opy_.append(bstack1l1l1111l_opy_)
      bstack1ll1llll1_opy_ = None
      for status in bstack1l1l1111l_opy_.iter(bstack1ll_opy_ (u"ࠬࡹࡴࡢࡶࡸࡷࠬே")):
        bstack1ll1llll1_opy_ = status
      bstack1l1llll1ll_opy_.append(bstack1ll1llll1_opy_)
    bstack1l1l11l1ll_opy_.write(path)
  except Exception as e:
    logger.debug(bstack1ll_opy_ (u"࠭ࡅࡳࡴࡲࡶࠥ࡯࡮ࠡࡲࡤࡶࡸ࡯࡮ࡨࠢࡺ࡬࡮ࡲࡥࠡࡩࡨࡲࡪࡸࡡࡵ࡫ࡱ࡫ࠥࡸ࡯ࡣࡱࡷࠤࡷ࡫ࡰࡰࡴࡷࠫை") + str(e))
def bstack1ll11lll11_opy_(outs_dir, pabot_args, options, start_time_string, tests_root_name):
  global bstack1llll11ll1_opy_
  global CONFIG
  if bstack1ll_opy_ (u"ࠢࡱࡻࡷ࡬ࡴࡴࡰࡢࡶ࡫ࠦ௉") in options:
    del options[bstack1ll_opy_ (u"ࠣࡲࡼࡸ࡭ࡵ࡮ࡱࡣࡷ࡬ࠧொ")]
  bstack1l1l11ll1_opy_ = bstack1ll11llll1_opy_()
  for item_id in bstack1l1l11ll1_opy_.keys():
    path = os.path.join(os.getcwd(), bstack1ll_opy_ (u"ࠩࡳࡥࡧࡵࡴࡠࡴࡨࡷࡺࡲࡴࡴࠩோ"), str(item_id), bstack1ll_opy_ (u"ࠪࡳࡺࡺࡰࡶࡶ࠱ࡼࡲࡲࠧௌ"))
    bstack1lll1ll11l_opy_(path, bstack1l1ll11l11_opy_(bstack1l1l11ll1_opy_[item_id]))
  bstack1lll1llll_opy_()
  return bstack1llll11ll1_opy_(outs_dir, pabot_args, options, start_time_string, tests_root_name)
def bstack11l11l1l1_opy_(self, ff_profile_dir):
  global bstack11ll111ll_opy_
  if not ff_profile_dir:
    return None
  return bstack11ll111ll_opy_(self, ff_profile_dir)
def bstack11ll11l1_opy_(datasources, opts_for_run, outs_dir, pabot_args, suite_group):
  from pabot.pabot import QueueItem
  global CONFIG
  global bstack1l1l1ll1l1_opy_
  bstack1l1ll1111_opy_ = []
  if bstack1ll_opy_ (u"ࠫࡵࡲࡡࡵࡨࡲࡶࡲࡹ்ࠧ") in CONFIG:
    bstack1l1ll1111_opy_ = CONFIG[bstack1ll_opy_ (u"ࠬࡶ࡬ࡢࡶࡩࡳࡷࡳࡳࠨ௎")]
  return [
    QueueItem(
      datasources,
      outs_dir,
      opts_for_run,
      suite,
      pabot_args[bstack1ll_opy_ (u"ࠨࡣࡰ࡯ࡰࡥࡳࡪࠢ௏")],
      pabot_args[bstack1ll_opy_ (u"ࠢࡷࡧࡵࡦࡴࡹࡥࠣௐ")],
      argfile,
      pabot_args.get(bstack1ll_opy_ (u"ࠣࡪ࡬ࡺࡪࠨ௑")),
      pabot_args[bstack1ll_opy_ (u"ࠤࡳࡶࡴࡩࡥࡴࡵࡨࡷࠧ௒")],
      platform[0],
      bstack1l1l1ll1l1_opy_
    )
    for suite in suite_group
    for argfile in pabot_args[bstack1ll_opy_ (u"ࠥࡥࡷ࡭ࡵ࡮ࡧࡱࡸ࡫࡯࡬ࡦࡵࠥ௓")] or [(bstack1ll_opy_ (u"ࠦࠧ௔"), None)]
    for platform in enumerate(bstack1l1ll1111_opy_)
  ]
def bstack1l1l1ll11_opy_(self, datasources, outs_dir, options,
                        execution_item, command, verbose, argfile,
                        hive=None, processes=0, platform_index=0, bstack11lll11ll_opy_=bstack1ll_opy_ (u"ࠬ࠭௕")):
  global bstack1ll11l1l_opy_
  self.platform_index = platform_index
  self.bstack1l1l111l_opy_ = bstack11lll11ll_opy_
  bstack1ll11l1l_opy_(self, datasources, outs_dir, options,
                      execution_item, command, verbose, argfile, hive, processes)
def bstack1lll11l1l1_opy_(caller_id, datasources, is_last, item, outs_dir):
  global bstack1l111l111_opy_
  global bstack111l11l11_opy_
  bstack1l11ll11l_opy_ = copy.deepcopy(item)
  if not bstack1ll_opy_ (u"࠭ࡶࡢࡴ࡬ࡥࡧࡲࡥࠨ௖") in item.options:
    bstack1l11ll11l_opy_.options[bstack1ll_opy_ (u"ࠧࡷࡣࡵ࡭ࡦࡨ࡬ࡦࠩௗ")] = []
  bstack1l11llll11_opy_ = bstack1l11ll11l_opy_.options[bstack1ll_opy_ (u"ࠨࡸࡤࡶ࡮ࡧࡢ࡭ࡧࠪ௘")].copy()
  for v in bstack1l11ll11l_opy_.options[bstack1ll_opy_ (u"ࠩࡹࡥࡷ࡯ࡡࡣ࡮ࡨࠫ௙")]:
    if bstack1ll_opy_ (u"ࠪࡆࡘ࡚ࡁࡄࡍࡓࡐࡆ࡚ࡆࡐࡔࡐࡍࡓࡊࡅ࡙ࠩ௚") in v:
      bstack1l11llll11_opy_.remove(v)
    if bstack1ll_opy_ (u"ࠫࡇ࡙ࡔࡂࡅࡎࡇࡑࡏࡁࡓࡉࡖࠫ௛") in v:
      bstack1l11llll11_opy_.remove(v)
    if bstack1ll_opy_ (u"ࠬࡈࡓࡕࡃࡆࡏࡉࡋࡆࡍࡑࡆࡅࡑࡏࡄࡆࡐࡗࡍࡋࡏࡅࡓࠩ௜") in v:
      bstack1l11llll11_opy_.remove(v)
  bstack1l11llll11_opy_.insert(0, bstack1ll_opy_ (u"࠭ࡂࡔࡖࡄࡇࡐࡖࡌࡂࡖࡉࡓࡗࡓࡉࡏࡆࡈ࡜࠿ࢁࡽࠨ௝").format(bstack1l11ll11l_opy_.platform_index))
  bstack1l11llll11_opy_.insert(0, bstack1ll_opy_ (u"ࠧࡃࡕࡗࡅࡈࡑࡄࡆࡈࡏࡓࡈࡇࡌࡊࡆࡈࡒ࡙ࡏࡆࡊࡇࡕ࠾ࢀࢃࠧ௞").format(bstack1l11ll11l_opy_.bstack1l1l111l_opy_))
  bstack1l11ll11l_opy_.options[bstack1ll_opy_ (u"ࠨࡸࡤࡶ࡮ࡧࡢ࡭ࡧࠪ௟")] = bstack1l11llll11_opy_
  if bstack111l11l11_opy_:
    bstack1l11ll11l_opy_.options[bstack1ll_opy_ (u"ࠩࡹࡥࡷ࡯ࡡࡣ࡮ࡨࠫ௠")].insert(0, bstack1ll_opy_ (u"ࠪࡆࡘ࡚ࡁࡄࡍࡆࡐࡎࡇࡒࡈࡕ࠽ࡿࢂ࠭௡").format(bstack111l11l11_opy_))
  return bstack1l111l111_opy_(caller_id, datasources, is_last, bstack1l11ll11l_opy_, outs_dir)
def bstack1l1l1l1l_opy_(command, item_index):
  try:
    if bstack1ll1l1l111_opy_.get_property(bstack1ll_opy_ (u"ࠫࡧࡹࡴࡢࡥ࡮ࡣࡸ࡫ࡳࡴ࡫ࡲࡲࠬ௢")):
      os.environ[bstack1ll_opy_ (u"ࠬࡉࡕࡓࡔࡈࡒ࡙ࡥࡐࡍࡃࡗࡊࡔࡘࡍࡠࡆࡄࡘࡆ࠭௣")] = json.dumps(CONFIG[bstack1ll_opy_ (u"࠭ࡰ࡭ࡣࡷࡪࡴࡸ࡭ࡴࠩ௤")][item_index % bstack11l1lll1l1_opy_])
    global bstack111l11l11_opy_
    if bstack111l11l11_opy_:
      command[0] = command[0].replace(bstack1ll_opy_ (u"ࠧࡳࡱࡥࡳࡹ࠭௥"), bstack1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࠭ࡴࡦ࡮ࠤࡷࡵࡢࡰࡶ࠰࡭ࡳࡺࡥࡳࡰࡤࡰࠥ࠳࠭ࡣࡵࡷࡥࡨࡱ࡟ࡱ࡮ࡤࡸ࡫ࡵࡲ࡮ࡡ࡬ࡲࡩ࡫ࡸࠡࠩ௦") + str(item_index % bstack11l1lll1l1_opy_) + bstack1ll_opy_ (u"ࠩࠣ࠱࠲ࡨࡳࡵࡣࡦ࡯ࡤ࡯ࡴࡦ࡯ࡢ࡭ࡳࡪࡥࡹࠢࠪ௧") + str(
        item_index) + bstack1ll_opy_ (u"ࠪࠤࠬ௨") + bstack111l11l11_opy_, 1)
    else:
      command[0] = command[0].replace(bstack1ll_opy_ (u"ࠫࡷࡵࡢࡰࡶࠪ௩"),
                                      bstack1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮࠱ࡸࡪ࡫ࠡࡴࡲࡦࡴࡺ࠭ࡪࡰࡷࡩࡷࡴࡡ࡭ࠢ࠰࠱ࡧࡹࡴࡢࡥ࡮ࡣࡵࡲࡡࡵࡨࡲࡶࡲࡥࡩ࡯ࡦࡨࡼࠥ࠭௪") +  str(item_index % bstack11l1lll1l1_opy_) + bstack1ll_opy_ (u"࠭ࠠ࠮࠯ࡥࡷࡹࡧࡣ࡬ࡡ࡬ࡸࡪࡳ࡟ࡪࡰࡧࡩࡽࠦࠧ௫") + str(item_index), 1)
  except Exception as e:
    logger.error(bstack1ll_opy_ (u"ࠧࡆࡴࡵࡳࡷࠦ࡭ࡰࡦ࡬ࡪࡾ࡯࡮ࡨࠢࡦࡳࡲࡳࡡ࡯ࡦࠣࡪࡴࡸࠠࡱࡣࡥࡳࡹࠦࡲࡶࡰ࠽ࠤࢀࢃࠧ௬").format(str(e)))
def bstack1l1l1l11l_opy_(command, stderr, stdout, item_name, verbose, pool_id, item_index):
  global bstack11111ll1_opy_
  try:
    bstack1l1l1l1l_opy_(command, item_index)
    return bstack11111ll1_opy_(command, stderr, stdout, item_name, verbose, pool_id, item_index)
  except Exception as e:
    logger.error(bstack1ll_opy_ (u"ࠨࡇࡵࡶࡴࡸࠠࡪࡰࠣࡴࡦࡨ࡯ࡵࠢࡵࡹࡳࡀࠠࡼࡿࠪ௭").format(str(e)))
    raise e
def bstack11l1l11ll_opy_(command, stderr, stdout, item_name, verbose, pool_id, item_index, outs_dir):
  global bstack11111ll1_opy_
  try:
    bstack1l1l1l1l_opy_(command, item_index)
    return bstack11111ll1_opy_(command, stderr, stdout, item_name, verbose, pool_id, item_index, outs_dir)
  except Exception as e:
    logger.error(bstack1ll_opy_ (u"ࠩࡈࡶࡷࡵࡲࠡ࡫ࡱࠤࡵࡧࡢࡰࡶࠣࡶࡺࡴࠠ࠳࠰࠴࠷࠿ࠦࡻࡾࠩ௮").format(str(e)))
    try:
      return bstack11111ll1_opy_(command, stderr, stdout, item_name, verbose, pool_id, item_index)
    except Exception as e2:
      logger.error(bstack1ll_opy_ (u"ࠪࡉࡷࡸ࡯ࡳࠢ࡬ࡲࠥࡶࡡࡣࡱࡷࠤ࠷࠴࠱࠴ࠢࡩࡥࡱࡲࡢࡢࡥ࡮࠾ࠥࢁࡽࠨ௯").format(str(e2)))
      raise e
def bstack11l1l11111_opy_(command, stderr, stdout, item_name, verbose, pool_id, item_index, outs_dir, process_timeout):
  global bstack11111ll1_opy_
  try:
    bstack1l1l1l1l_opy_(command, item_index)
    if process_timeout is None:
      process_timeout = 3600
    return bstack11111ll1_opy_(command, stderr, stdout, item_name, verbose, pool_id, item_index, outs_dir, process_timeout)
  except Exception as e:
    logger.error(bstack1ll_opy_ (u"ࠫࡊࡸࡲࡰࡴࠣ࡭ࡳࠦࡰࡢࡤࡲࡸࠥࡸࡵ࡯ࠢ࠵࠲࠶࠻࠺ࠡࡽࢀࠫ௰").format(str(e)))
    try:
      return bstack11111ll1_opy_(command, stderr, stdout, item_name, verbose, pool_id, item_index, outs_dir)
    except Exception as e2:
      logger.error(bstack1ll_opy_ (u"ࠬࡋࡲࡳࡱࡵࠤ࡮ࡴࠠࡱࡣࡥࡳࡹࠦ࠲࠯࠳࠸ࠤ࡫ࡧ࡬࡭ࡤࡤࡧࡰࡀࠠࡼࡿࠪ௱").format(str(e2)))
      raise e
def _1lll1l1ll_opy_(bstack1lllll1l11_opy_, item_index, process_timeout, sleep_before_start, bstack1lllllllll_opy_):
  bstack1l1l1l1l_opy_(bstack1lllll1l11_opy_, item_index)
  if process_timeout is None:
    process_timeout = 3600
  if sleep_before_start and sleep_before_start > 0:
    time.sleep(min(sleep_before_start, 5))
  return process_timeout
def bstack11lll11l11_opy_(command, bstack11l1llll1_opy_, stderr, stdout, item_name, verbose, pool_id, item_index, outs_dir, process_timeout, sleep_before_start):
  global bstack11111ll1_opy_
  global bstack1lll1l111l_opy_
  global bstack111l11l11_opy_
  try:
    for env_name, bstack1lll1111ll_opy_ in bstack1lll1l111l_opy_.items():
      os.environ[env_name] = bstack1lll1111ll_opy_
    bstack111l11l11_opy_ = bstack1ll_opy_ (u"ࠨࠢ௲")
    bstack1l1l1l1l_opy_(command, item_index)
    if process_timeout is None:
      process_timeout = 3600
    if sleep_before_start and sleep_before_start > 0:
      time.sleep(min(sleep_before_start, 5))
    return bstack11111ll1_opy_(command, bstack11l1llll1_opy_, stderr, stdout, item_name, verbose, pool_id, item_index, outs_dir, process_timeout, sleep_before_start)
  except Exception as e:
    logger.error(bstack1ll_opy_ (u"ࠧࡆࡴࡵࡳࡷࠦࡩ࡯ࠢࡳࡥࡧࡵࡴࠡࡴࡸࡲࠥ࠻࠮࠱࠼ࠣࡿࢂ࠭௳").format(str(e)))
    try:
      return bstack11111ll1_opy_(command, bstack11l1llll1_opy_, stderr, stdout, item_name, verbose, pool_id, item_index, outs_dir, process_timeout)
    except Exception as e2:
      logger.error(bstack1ll_opy_ (u"ࠨࡇࡵࡶࡴࡸࠠࡪࡰࠣࡴࡦࡨ࡯ࡵࠢࡩࡥࡱࡲࡢࡢࡥ࡮࠾ࠥࢁࡽࠨ௴").format(str(e2)))
      raise e
def bstack1ll1lll111_opy_(command, stderr, stdout, item_name, verbose, pool_id, item_index, outs_dir, process_timeout, sleep_before_start):
  global bstack11111ll1_opy_
  try:
    process_timeout = _1lll1l1ll_opy_(command, item_index, process_timeout, sleep_before_start, bstack1ll_opy_ (u"ࠩ࠷࠲࠷࠭௵"))
    return bstack11111ll1_opy_(command, stderr, stdout, item_name, verbose, pool_id, item_index, outs_dir, process_timeout, sleep_before_start)
  except Exception as e:
    logger.error(bstack1ll_opy_ (u"ࠪࡉࡷࡸ࡯ࡳࠢ࡬ࡲࠥࡶࡡࡣࡱࡷࠤࡷࡻ࡮ࠡ࠶࠱࠶࠿ࠦࡻࡾࠩ௶").format(str(e)))
    try:
      return bstack11111ll1_opy_(command, stderr, stdout, item_name, verbose, pool_id, item_index, outs_dir, process_timeout)
    except Exception as e2:
      logger.error(bstack1ll_opy_ (u"ࠫࡊࡸࡲࡰࡴࠣ࡭ࡳࠦࡰࡢࡤࡲࡸࠥ࡬ࡡ࡭࡮ࡥࡥࡨࡱ࠺ࠡࡽࢀࠫ௷").format(str(e2)))
      raise e
def is_driver_active(driver):
  return True if driver and driver.session_id else False
def bstack1ll1lll1l_opy_(self, runner, quiet=False, capture=True):
  global bstack11l1ll1ll_opy_
  bstack11lll1l11l_opy_ = bstack11l1ll1ll_opy_(self, runner, quiet=quiet, capture=capture)
  if self.exception:
    if not hasattr(runner, bstack1ll_opy_ (u"ࠬ࡫ࡸࡤࡧࡳࡸ࡮ࡵ࡮ࡠࡣࡵࡶࠬ௸")):
      runner.exception_arr = []
    if not hasattr(runner, bstack1ll_opy_ (u"࠭ࡥࡹࡥࡢࡸࡷࡧࡣࡦࡤࡤࡧࡰࡥࡡࡳࡴࠪ௹")):
      runner.exc_traceback_arr = []
    runner.exception = self.exception
    runner.exc_traceback = self.exc_traceback
    runner.exception_arr.append(self.exception)
    runner.exc_traceback_arr.append(self.exc_traceback)
  return bstack11lll1l11l_opy_
def bstack1l11111l_opy_(runner, hook_name, context, element, bstack1l1ll11l1l_opy_, *args):
  try:
    if runner.hooks.get(hook_name):
      bstack1l1111l1ll_opy_.bstack11l11llll1_opy_(hook_name, element)
    bstack1l1ll11l1l_opy_(runner, hook_name, context, *args)
    if runner.hooks.get(hook_name):
      bstack1l1111l1ll_opy_.bstack11l1ll11l_opy_(element)
      if hook_name not in [bstack1ll_opy_ (u"ࠧࡣࡧࡩࡳࡷ࡫࡟ࡢ࡮࡯ࠫ௺"), bstack1ll_opy_ (u"ࠨࡣࡩࡸࡪࡸ࡟ࡢ࡮࡯ࠫ௻")] and args and hasattr(args[0], bstack1ll_opy_ (u"ࠩࡨࡶࡷࡵࡲࡠ࡯ࡨࡷࡸࡧࡧࡦࠩ௼")):
        args[0].error_message = bstack1ll_opy_ (u"ࠪࠫ௽")
  except Exception as e:
    logger.debug(bstack1ll_opy_ (u"ࠫࡋࡧࡩ࡭ࡧࡧࠤࡹࡵࠠࡩࡣࡱࡨࡱ࡫ࠠࡩࡱࡲ࡯ࡸࠦࡩ࡯ࠢࡥࡩ࡭ࡧࡶࡦ࠼ࠣࡿࢂ࠭௾").format(str(e)))
@measure(event_name=EVENTS.bstack1ll1llll11_opy_, stage=STAGE.bstack1l1lll1ll1_opy_, hook_type=bstack1ll_opy_ (u"ࠧࡨࡥࡧࡱࡵࡩࡆࡲ࡬ࠣ௿"), bstack1l1l11ll_opy_=bstack1llll1111l_opy_)
def bstack1l1111ll1l_opy_(runner, name, context, bstack1l1ll11l1l_opy_, *args):
    if runner.hooks.get(bstack1ll_opy_ (u"ࠨࡢࡦࡨࡲࡶࡪࡥࡡ࡭࡮ࠥఀ")).__name__ != bstack1ll_opy_ (u"ࠢࡣࡧࡩࡳࡷ࡫࡟ࡢ࡮࡯ࡣࡩ࡫ࡦࡢࡷ࡯ࡸࡤ࡮࡯ࡰ࡭ࠥఁ"):
      bstack1l11111l_opy_(runner, name, context, runner, bstack1l1ll11l1l_opy_, *args)
    try:
      threading.current_thread().bstackSessionDriver if bstack1l1lllll1l_opy_(bstack1ll_opy_ (u"ࠨࡤࡶࡸࡦࡩ࡫ࡔࡧࡶࡷ࡮ࡵ࡮ࡅࡴ࡬ࡺࡪࡸࠧం")) else context.browser
      runner.driver_initialised = bstack1ll_opy_ (u"ࠤࡥࡩ࡫ࡵࡲࡦࡡࡤࡰࡱࠨః")
    except Exception as e:
      logger.debug(bstack1ll_opy_ (u"ࠪࡊࡦ࡯࡬ࡦࡦࠣࡸࡴࠦࡳࡦࡶࠣࡨࡷ࡯ࡶࡦࡴࠣ࡭ࡳ࡯ࡴࡪࡣ࡯࡭ࡸ࡫ࠠࡢࡶࡷࡶ࡮ࡨࡵࡵࡧ࠽ࠤࢀࢃࠧఄ").format(str(e)))
def bstack1l111ll111_opy_(runner, name, context, bstack1l1ll11l1l_opy_, *args):
    bstack1l11111l_opy_(runner, name, context, context.feature, bstack1l1ll11l1l_opy_, *args)
    try:
      if not bstack1111l11ll_opy_:
        bstack1l1l11l1_opy_ = threading.current_thread().bstackSessionDriver if bstack1l1lllll1l_opy_(bstack1ll_opy_ (u"ࠫࡧࡹࡴࡢࡥ࡮ࡗࡪࡹࡳࡪࡱࡱࡈࡷ࡯ࡶࡦࡴࠪఅ")) else context.browser
        if is_driver_active(bstack1l1l11l1_opy_):
          if runner.driver_initialised is None: runner.driver_initialised = bstack1ll_opy_ (u"ࠧࡨࡥࡧࡱࡵࡩࡤ࡬ࡥࡢࡶࡸࡶࡪࠨఆ")
          bstack1llllll1ll_opy_ = str(runner.feature.name)
          bstack1lll111ll1_opy_(context, bstack1llllll1ll_opy_)
          bstack1l1l11l1_opy_.execute_script(bstack1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯ࡤ࡫ࡸࡦࡥࡸࡸࡴࡸ࠺ࠡࡽࠥࡥࡨࡺࡩࡰࡰࠥ࠾ࠥࠨࡳࡦࡶࡖࡩࡸࡹࡩࡰࡰࡑࡥࡲ࡫ࠢ࠭ࠢࠥࡥࡷ࡭ࡵ࡮ࡧࡱࡸࡸࠨ࠺ࠡࡽࠥࡲࡦࡳࡥࠣ࠼ࠣࠫఇ") + json.dumps(bstack1llllll1ll_opy_) + bstack1ll_opy_ (u"ࠧࡾࡿࠪఈ"))
    except Exception as e:
      logger.debug(bstack1ll_opy_ (u"ࠨࡈࡤ࡭ࡱ࡫ࡤࠡࡶࡲࠤࡸ࡫ࡴࠡࡵࡨࡷࡸ࡯࡯࡯ࠢࡱࡥࡲ࡫ࠠࡪࡰࠣࡦࡪ࡬࡯ࡳࡧࠣࡪࡪࡧࡴࡶࡴࡨ࠾ࠥࢁࡽࠨఉ").format(str(e)))
def bstack1l111ll1_opy_(runner, name, context, bstack1l1ll11l1l_opy_, *args):
    if hasattr(context, bstack1ll_opy_ (u"ࠩࡶࡧࡪࡴࡡࡳ࡫ࡲࠫఊ")):
        bstack1l1111l1ll_opy_.start_test(context)
    target = context.scenario if hasattr(context, bstack1ll_opy_ (u"ࠪࡷࡨ࡫࡮ࡢࡴ࡬ࡳࠬఋ")) else context.feature
    bstack1l11111l_opy_(runner, name, context, target, bstack1l1ll11l1l_opy_, *args)
@measure(event_name=EVENTS.bstack1ll1l11lll_opy_, stage=STAGE.bstack1l1lll1ll1_opy_, bstack1l1l11ll_opy_=bstack1llll1111l_opy_)
def bstack11lll1ll1_opy_(runner, name, context, bstack1l1ll11l1l_opy_, *args):
    if len(context.scenario.tags) == 0: bstack1l1111l1ll_opy_.start_test(context)
    bstack1l11111l_opy_(runner, name, context, context.scenario, bstack1l1ll11l1l_opy_, *args)
    threading.current_thread().a11y_stop = False
    bstack11l1l1111_opy_.bstack1lll1l1lll_opy_(context, *args)
    try:
      bstack1l1l11l1_opy_ = bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠫࡧࡹࡴࡢࡥ࡮ࡗࡪࡹࡳࡪࡱࡱࡈࡷ࡯ࡶࡦࡴࠪఌ"), context.browser)
      if is_driver_active(bstack1l1l11l1_opy_):
        bstack1lll1111l_opy_.bstack11ll1l1ll1_opy_(bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠬࡨࡳࡵࡣࡦ࡯ࡘ࡫ࡳࡴ࡫ࡲࡲࡉࡸࡩࡷࡧࡵࠫ఍"), {}))
        if runner.driver_initialised is None: runner.driver_initialised = bstack1ll_opy_ (u"ࠨࡢࡦࡨࡲࡶࡪࡥࡳࡤࡧࡱࡥࡷ࡯࡯ࠣఎ")
        if (not bstack1111l11ll_opy_):
          scenario_name = args[0].name
          feature_name = bstack1llllll1ll_opy_ = str(runner.feature.name)
          bstack1llllll1ll_opy_ = feature_name + bstack1ll_opy_ (u"ࠧࠡ࠯ࠣࠫఏ") + scenario_name
          if runner.driver_initialised == bstack1ll_opy_ (u"ࠣࡤࡨࡪࡴࡸࡥࡠࡵࡦࡩࡳࡧࡲࡪࡱࠥఐ"):
            bstack1lll111ll1_opy_(context, bstack1llllll1ll_opy_)
            bstack1l1l11l1_opy_.execute_script(bstack1ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫ࡠࡧࡻࡩࡨࡻࡴࡰࡴ࠽ࠤࢀࠨࡡࡤࡶ࡬ࡳࡳࠨ࠺ࠡࠤࡶࡩࡹ࡙ࡥࡴࡵ࡬ࡳࡳࡔࡡ࡮ࡧࠥ࠰ࠥࠨࡡࡳࡩࡸࡱࡪࡴࡴࡴࠤ࠽ࠤࢀࠨ࡮ࡢ࡯ࡨࠦ࠿ࠦࠧ఑") + json.dumps(bstack1llllll1ll_opy_) + bstack1ll_opy_ (u"ࠪࢁࢂ࠭ఒ"))
    except Exception as e:
      logger.debug(bstack1ll_opy_ (u"ࠫࡋࡧࡩ࡭ࡧࡧࠤࡹࡵࠠࡴࡧࡷࠤࡸ࡫ࡳࡴ࡫ࡲࡲࠥࡴࡡ࡮ࡧࠣ࡭ࡳࠦࡢࡦࡨࡲࡶࡪࠦࡳࡤࡧࡱࡥࡷ࡯࡯࠻ࠢࡾࢁࠬఓ").format(str(e)))
@measure(event_name=EVENTS.bstack1ll1llll11_opy_, stage=STAGE.bstack1l1lll1ll1_opy_, hook_type=bstack1ll_opy_ (u"ࠧࡨࡥࡧࡱࡵࡩࡘࡺࡥࡱࠤఔ"), bstack1l1l11ll_opy_=bstack1llll1111l_opy_)
def bstack1ll1ll1ll1_opy_(runner, name, context, bstack1l1ll11l1l_opy_, *args):
    bstack1l11111l_opy_(runner, name, context, args[0], bstack1l1ll11l1l_opy_, *args)
    try:
      bstack1l1l11l1_opy_ = threading.current_thread().bstackSessionDriver if bstack1l1lllll1l_opy_(bstack1ll_opy_ (u"࠭ࡢࡴࡶࡤࡧࡰ࡙ࡥࡴࡵ࡬ࡳࡳࡊࡲࡪࡸࡨࡶࠬక")) else context.browser
      if is_driver_active(bstack1l1l11l1_opy_):
        if runner.driver_initialised is None: runner.driver_initialised = bstack1ll_opy_ (u"ࠢࡣࡧࡩࡳࡷ࡫࡟ࡴࡶࡨࡴࠧఖ")
        bstack1l1111l1ll_opy_.bstack1ll11l1l1l_opy_(args[0])
        if runner.driver_initialised == bstack1ll_opy_ (u"ࠣࡤࡨࡪࡴࡸࡥࡠࡵࡷࡩࡵࠨగ"):
          feature_name = bstack1llllll1ll_opy_ = str(runner.feature.name)
          bstack1llllll1ll_opy_ = feature_name + bstack1ll_opy_ (u"ࠩࠣ࠱ࠥ࠭ఘ") + context.scenario.name
          bstack1l1l11l1_opy_.execute_script(bstack1ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬ࡡࡨࡼࡪࡩࡵࡵࡱࡵ࠾ࠥࢁࠢࡢࡥࡷ࡭ࡴࡴࠢ࠻ࠢࠥࡷࡪࡺࡓࡦࡵࡶ࡭ࡴࡴࡎࡢ࡯ࡨࠦ࠱ࠦࠢࡢࡴࡪࡹࡲ࡫࡮ࡵࡵࠥ࠾ࠥࢁࠢ࡯ࡣࡰࡩࠧࡀࠠࠨఙ") + json.dumps(bstack1llllll1ll_opy_) + bstack1ll_opy_ (u"ࠫࢂࢃࠧచ"))
    except Exception as e:
      logger.debug(bstack1ll_opy_ (u"ࠬࡌࡡࡪ࡮ࡨࡨࠥࡺ࡯ࠡࡵࡨࡸࠥࡹࡥࡴࡵ࡬ࡳࡳࠦ࡮ࡢ࡯ࡨࠤ࡮ࡴࠠࡣࡧࡩࡳࡷ࡫ࠠࡴࡶࡨࡴ࠿ࠦࡻࡾࠩఛ").format(str(e)))
@measure(event_name=EVENTS.bstack1ll1llll11_opy_, stage=STAGE.bstack1l1lll1ll1_opy_, hook_type=bstack1ll_opy_ (u"ࠨࡡࡧࡶࡨࡶࡘࡺࡥࡱࠤజ"), bstack1l1l11ll_opy_=bstack1llll1111l_opy_)
def bstack11l11l1ll1_opy_(runner, name, context, bstack1l1ll11l1l_opy_, *args):
  bstack1l1111l1ll_opy_.bstack11llll11l_opy_(args[0])
  try:
    step_status = args[0].status.name
    bstack1l1l11l1_opy_ = threading.current_thread().bstackSessionDriver if bstack1ll_opy_ (u"ࠧࡣࡵࡷࡥࡨࡱࡓࡦࡵࡶ࡭ࡴࡴࡄࡳ࡫ࡹࡩࡷ࠭ఝ") in threading.current_thread().__dict__.keys() else context.browser
    if is_driver_active(bstack1l1l11l1_opy_):
      if runner.driver_initialised is None:
        runner.driver_initialised  = bstack1ll_opy_ (u"ࠨ࡫ࡱࡷࡹ࡫ࡰࠨఞ")
        feature_name = bstack1llllll1ll_opy_ = str(runner.feature.name)
        bstack1llllll1ll_opy_ = feature_name + bstack1ll_opy_ (u"ࠩࠣ࠱ࠥ࠭ట") + context.scenario.name
        bstack1l1l11l1_opy_.execute_script(bstack1ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬ࡡࡨࡼࡪࡩࡵࡵࡱࡵ࠾ࠥࢁࠢࡢࡥࡷ࡭ࡴࡴࠢ࠻ࠢࠥࡷࡪࡺࡓࡦࡵࡶ࡭ࡴࡴࡎࡢ࡯ࡨࠦ࠱ࠦࠢࡢࡴࡪࡹࡲ࡫࡮ࡵࡵࠥ࠾ࠥࢁࠢ࡯ࡣࡰࡩࠧࡀࠠࠨఠ") + json.dumps(bstack1llllll1ll_opy_) + bstack1ll_opy_ (u"ࠫࢂࢃࠧడ"))
    if str(step_status).lower() == bstack1ll_opy_ (u"ࠬ࡬ࡡࡪ࡮ࡨࡨࠬఢ"):
      bstack111lll1ll_opy_ = bstack1ll_opy_ (u"࠭ࠧణ")
      bstack11l1l1ll1l_opy_ = bstack1ll_opy_ (u"ࠧࠨత")
      bstack11ll11l11_opy_ = bstack1ll_opy_ (u"ࠨࠩథ")
      try:
        import traceback
        bstack111lll1ll_opy_ = runner.exception.__class__.__name__
        bstack11llll11ll_opy_ = traceback.format_tb(runner.exc_traceback)
        bstack11l1l1ll1l_opy_ = bstack1ll_opy_ (u"ࠩࠣࠫద").join(bstack11llll11ll_opy_)
        bstack11ll11l11_opy_ = bstack11llll11ll_opy_[-1]
      except Exception as e:
        logger.debug(bstack1lll1111_opy_.format(str(e)))
      bstack111lll1ll_opy_ += bstack11ll11l11_opy_
      bstack1l111ll11l_opy_(context, json.dumps(str(args[0].name) + bstack1ll_opy_ (u"ࠥࠤ࠲ࠦࡆࡢ࡫࡯ࡩࡩࠧ࡜࡯ࠤధ") + str(bstack11l1l1ll1l_opy_)),
                          bstack1ll_opy_ (u"ࠦࡪࡸࡲࡰࡴࠥన"))
      if runner.driver_initialised == bstack1ll_opy_ (u"ࠧࡨࡥࡧࡱࡵࡩࡤࡹࡴࡦࡲࠥ఩"):
        bstack1l111111ll_opy_(getattr(context, bstack1ll_opy_ (u"࠭ࡰࡢࡩࡨࠫప"), None), bstack1ll_opy_ (u"ࠢࡧࡣ࡬ࡰࡪࡪࠢఫ"), bstack111lll1ll_opy_)
        bstack1l1l11l1_opy_.execute_script(bstack1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࡟ࡦࡺࡨࡧࡺࡺ࡯ࡳ࠼ࠣࡿࠧࡧࡣࡵ࡫ࡲࡲࠧࡀࠠࠣࡣࡱࡲࡴࡺࡡࡵࡧࠥ࠰ࠥࠨࡡࡳࡩࡸࡱࡪࡴࡴࡴࠤ࠽ࠤࢀࠨࡤࡢࡶࡤࠦ࠿࠭బ") + json.dumps(str(args[0].name) + bstack1ll_opy_ (u"ࠤࠣ࠱ࠥࡌࡡࡪ࡮ࡨࡨࠦࡢ࡮ࠣభ") + str(bstack11l1l1ll1l_opy_)) + bstack1ll_opy_ (u"ࠪ࠰ࠥࠨ࡬ࡦࡸࡨࡰࠧࡀࠠࠣࡧࡵࡶࡴࡸࠢࡾࡿࠪమ"))
      if runner.driver_initialised == bstack1ll_opy_ (u"ࠦࡧ࡫ࡦࡰࡴࡨࡣࡸࡺࡥࡱࠤయ"):
        bstack11ll11111l_opy_(bstack1l1l11l1_opy_, bstack1ll_opy_ (u"ࠬ࡬ࡡࡪ࡮ࡨࡨࠬర"), bstack1ll_opy_ (u"ࠨࡓࡤࡧࡱࡥࡷ࡯࡯ࠡࡨࡤ࡭ࡱ࡫ࡤࠡࡹ࡬ࡸ࡭ࡀࠠ࡝ࡰࠥఱ") + str(bstack111lll1ll_opy_))
    else:
      bstack1l111ll11l_opy_(context, bstack1ll_opy_ (u"ࠢࡑࡣࡶࡷࡪࡪࠡࠣల"), bstack1ll_opy_ (u"ࠣ࡫ࡱࡪࡴࠨళ"))
      if runner.driver_initialised == bstack1ll_opy_ (u"ࠤࡥࡩ࡫ࡵࡲࡦࡡࡶࡸࡪࡶࠢఴ"):
        bstack1l111111ll_opy_(getattr(context, bstack1ll_opy_ (u"ࠪࡴࡦ࡭ࡥࠨవ"), None), bstack1ll_opy_ (u"ࠦࡵࡧࡳࡴࡧࡧࠦశ"))
      bstack1l1l11l1_opy_.execute_script(bstack1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮ࡣࡪࡾࡥࡤࡷࡷࡳࡷࡀࠠࡼࠤࡤࡧࡹ࡯࡯࡯ࠤ࠽ࠤࠧࡧ࡮࡯ࡱࡷࡥࡹ࡫ࠢ࠭ࠢࠥࡥࡷ࡭ࡵ࡮ࡧࡱࡸࡸࠨ࠺ࠡࡽࠥࡨࡦࡺࡡࠣ࠼ࠪష") + json.dumps(str(args[0].name) + bstack1ll_opy_ (u"ࠨࠠ࠮ࠢࡓࡥࡸࡹࡥࡥࠣࠥస")) + bstack1ll_opy_ (u"ࠧ࠭ࠢࠥࡰࡪࡼࡥ࡭ࠤ࠽ࠤࠧ࡯࡮ࡧࡱࠥࢁࢂ࠭హ"))
      if runner.driver_initialised == bstack1ll_opy_ (u"ࠣࡤࡨࡪࡴࡸࡥࡠࡵࡷࡩࡵࠨ఺"):
        bstack11ll11111l_opy_(bstack1l1l11l1_opy_, bstack1ll_opy_ (u"ࠤࡳࡥࡸࡹࡥࡥࠤ఻"))
  except Exception as e:
    logger.debug(bstack1ll_opy_ (u"ࠪࡊࡦ࡯࡬ࡦࡦࠣࡸࡴࠦ࡭ࡢࡴ࡮ࠤࡸ࡫ࡳࡴ࡫ࡲࡲࠥࡹࡴࡢࡶࡸࡷࠥ࡯࡮ࠡࡣࡩࡸࡪࡸࠠࡴࡶࡨࡴ࠿ࠦࡻࡾ఼ࠩ").format(str(e)))
  bstack1l11111l_opy_(runner, name, context, args[0], bstack1l1ll11l1l_opy_, *args)
@measure(event_name=EVENTS.bstack1llll1l1ll_opy_, stage=STAGE.bstack1l1lll1ll1_opy_, bstack1l1l11ll_opy_=bstack1llll1111l_opy_)
def bstack11ll11ll_opy_(runner, name, context, bstack1l1ll11l1l_opy_, *args):
  bstack1l1111l1ll_opy_.end_test(args[0])
  try:
    bstack1ll1l1lll1_opy_ = args[0].status.name
    bstack1l1l11l1_opy_ = bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠫࡧࡹࡴࡢࡥ࡮ࡗࡪࡹࡳࡪࡱࡱࡈࡷ࡯ࡶࡦࡴࠪఽ"), context.browser)
    bstack11l1l1111_opy_.bstack1l1lll111_opy_(bstack1l1l11l1_opy_)
    if str(bstack1ll1l1lll1_opy_).lower() == bstack1ll_opy_ (u"ࠬ࡬ࡡࡪ࡮ࡨࡨࠬా"):
      bstack111lll1ll_opy_ = bstack1ll_opy_ (u"࠭ࠧి")
      bstack11l1l1ll1l_opy_ = bstack1ll_opy_ (u"ࠧࠨీ")
      bstack11ll11l11_opy_ = bstack1ll_opy_ (u"ࠨࠩు")
      try:
        import traceback
        bstack111lll1ll_opy_ = runner.exception.__class__.__name__
        bstack11llll11ll_opy_ = traceback.format_tb(runner.exc_traceback)
        bstack11l1l1ll1l_opy_ = bstack1ll_opy_ (u"ࠩࠣࠫూ").join(bstack11llll11ll_opy_)
        bstack11ll11l11_opy_ = bstack11llll11ll_opy_[-1]
      except Exception as e:
        logger.debug(bstack1lll1111_opy_.format(str(e)))
      bstack111lll1ll_opy_ += bstack11ll11l11_opy_
      bstack1l111ll11l_opy_(context, json.dumps(str(args[0].name) + bstack1ll_opy_ (u"ࠥࠤ࠲ࠦࡆࡢ࡫࡯ࡩࡩࠧ࡜࡯ࠤృ") + str(bstack11l1l1ll1l_opy_)),
                          bstack1ll_opy_ (u"ࠦࡪࡸࡲࡰࡴࠥౄ"))
      if runner.driver_initialised == bstack1ll_opy_ (u"ࠧࡨࡥࡧࡱࡵࡩࡤࡹࡣࡦࡰࡤࡶ࡮ࡵࠢ౅") or runner.driver_initialised == bstack1ll_opy_ (u"࠭ࡩ࡯ࡵࡷࡩࡵ࠭ె"):
        bstack1l111111ll_opy_(getattr(context, bstack1ll_opy_ (u"ࠧࡱࡣࡪࡩࠬే"), None), bstack1ll_opy_ (u"ࠣࡨࡤ࡭ࡱ࡫ࡤࠣై"), bstack111lll1ll_opy_)
        bstack1l1l11l1_opy_.execute_script(bstack1ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫ࡠࡧࡻࡩࡨࡻࡴࡰࡴ࠽ࠤࢀࠨࡡࡤࡶ࡬ࡳࡳࠨ࠺ࠡࠤࡤࡲࡳࡵࡴࡢࡶࡨࠦ࠱ࠦࠢࡢࡴࡪࡹࡲ࡫࡮ࡵࡵࠥ࠾ࠥࢁࠢࡥࡣࡷࡥࠧࡀࠧ౉") + json.dumps(str(args[0].name) + bstack1ll_opy_ (u"ࠥࠤ࠲ࠦࡆࡢ࡫࡯ࡩࡩࠧ࡜࡯ࠤొ") + str(bstack11l1l1ll1l_opy_)) + bstack1ll_opy_ (u"ࠫ࠱ࠦࠢ࡭ࡧࡹࡩࡱࠨ࠺ࠡࠤࡨࡶࡷࡵࡲࠣࡿࢀࠫో"))
      if runner.driver_initialised == bstack1ll_opy_ (u"ࠧࡨࡥࡧࡱࡵࡩࡤࡹࡣࡦࡰࡤࡶ࡮ࡵࠢౌ") or runner.driver_initialised == bstack1ll_opy_ (u"࠭ࡩ࡯ࡵࡷࡩࡵ్࠭"):
        bstack11ll11111l_opy_(bstack1l1l11l1_opy_, bstack1ll_opy_ (u"ࠧࡧࡣ࡬ࡰࡪࡪࠧ౎"), bstack1ll_opy_ (u"ࠣࡕࡦࡩࡳࡧࡲࡪࡱࠣࡪࡦ࡯࡬ࡦࡦࠣࡻ࡮ࡺࡨ࠻ࠢ࡟ࡲࠧ౏") + str(bstack111lll1ll_opy_))
    else:
      bstack1l111ll11l_opy_(context, bstack1ll_opy_ (u"ࠤࡓࡥࡸࡹࡥࡥࠣࠥ౐"), bstack1ll_opy_ (u"ࠥ࡭ࡳ࡬࡯ࠣ౑"))
      if runner.driver_initialised == bstack1ll_opy_ (u"ࠦࡧ࡫ࡦࡰࡴࡨࡣࡸࡩࡥ࡯ࡣࡵ࡭ࡴࠨ౒") or runner.driver_initialised == bstack1ll_opy_ (u"ࠬ࡯࡮ࡴࡶࡨࡴࠬ౓"):
        bstack1l111111ll_opy_(getattr(context, bstack1ll_opy_ (u"࠭ࡰࡢࡩࡨࠫ౔"), None), bstack1ll_opy_ (u"ࠢࡱࡣࡶࡷࡪࡪౕࠢ"))
      bstack1l1l11l1_opy_.execute_script(bstack1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࡟ࡦࡺࡨࡧࡺࡺ࡯ࡳ࠼ࠣࡿࠧࡧࡣࡵ࡫ࡲࡲࠧࡀࠠࠣࡣࡱࡲࡴࡺࡡࡵࡧࠥ࠰ࠥࠨࡡࡳࡩࡸࡱࡪࡴࡴࡴࠤ࠽ࠤࢀࠨࡤࡢࡶࡤࠦ࠿ౖ࠭") + json.dumps(str(args[0].name) + bstack1ll_opy_ (u"ࠤࠣ࠱ࠥࡖࡡࡴࡵࡨࡨࠦࠨ౗")) + bstack1ll_opy_ (u"ࠪ࠰ࠥࠨ࡬ࡦࡸࡨࡰࠧࡀࠠࠣ࡫ࡱࡪࡴࠨࡽࡾࠩౘ"))
      if runner.driver_initialised == bstack1ll_opy_ (u"ࠦࡧ࡫ࡦࡰࡴࡨࡣࡸࡩࡥ࡯ࡣࡵ࡭ࡴࠨౙ") or runner.driver_initialised == bstack1ll_opy_ (u"ࠬ࡯࡮ࡴࡶࡨࡴࠬౚ"):
        bstack11ll11111l_opy_(bstack1l1l11l1_opy_, bstack1ll_opy_ (u"ࠨࡰࡢࡵࡶࡩࡩࠨ౛"))
  except Exception as e:
    logger.debug(bstack1ll_opy_ (u"ࠧࡇࡣ࡬ࡰࡪࡪࠠࡵࡱࠣࡱࡦࡸ࡫ࠡࡵࡨࡷࡸ࡯࡯࡯ࠢࡶࡸࡦࡺࡵࡴࠢ࡬ࡲࠥࡧࡦࡵࡧࡵࠤ࡫࡫ࡡࡵࡷࡵࡩ࠿ࠦࡻࡾࠩ౜").format(str(e)))
  bstack1l11111l_opy_(runner, name, context, context.scenario, bstack1l1ll11l1l_opy_, *args)
  if len(context.scenario.tags) == 0: threading.current_thread().current_test_uuid = None
def bstack111l111l_opy_(runner, name, context, bstack1l1ll11l1l_opy_, *args):
    target = context.scenario if hasattr(context, bstack1ll_opy_ (u"ࠨࡵࡦࡩࡳࡧࡲࡪࡱࠪౝ")) else context.feature
    bstack1l11111l_opy_(runner, name, context, target, bstack1l1ll11l1l_opy_, *args)
    threading.current_thread().current_test_uuid = None
def bstack1l1111ll_opy_(runner, name, context, bstack1l1ll11l1l_opy_, *args):
    try:
      bstack1l1l11l1_opy_ = bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠩࡥࡷࡹࡧࡣ࡬ࡕࡨࡷࡸ࡯࡯࡯ࡆࡵ࡭ࡻ࡫ࡲࠨ౞"), context.browser)
      bstack1l111l1l_opy_ = bstack1ll_opy_ (u"ࠪࠫ౟")
      if context.failed is True:
        bstack11l1ll1l1_opy_ = []
        bstack1lllllll11_opy_ = []
        bstack11lll1lll_opy_ = []
        try:
          import traceback
          for exc in runner.exception_arr:
            bstack11l1ll1l1_opy_.append(exc.__class__.__name__)
          for exc_tb in runner.exc_traceback_arr:
            bstack11llll11ll_opy_ = traceback.format_tb(exc_tb)
            bstack1l11l11l11_opy_ = bstack1ll_opy_ (u"ࠫࠥ࠭ౠ").join(bstack11llll11ll_opy_)
            bstack1lllllll11_opy_.append(bstack1l11l11l11_opy_)
            bstack11lll1lll_opy_.append(bstack11llll11ll_opy_[-1])
        except Exception as e:
          logger.debug(bstack1lll1111_opy_.format(str(e)))
        bstack111lll1ll_opy_ = bstack1ll_opy_ (u"ࠬ࠭ౡ")
        for i in range(len(bstack11l1ll1l1_opy_)):
          bstack111lll1ll_opy_ += bstack11l1ll1l1_opy_[i] + bstack11lll1lll_opy_[i] + bstack1ll_opy_ (u"࠭࡜࡯ࠩౢ")
        bstack1l111l1l_opy_ = bstack1ll_opy_ (u"ࠧࠡࠩౣ").join(bstack1lllllll11_opy_)
        if runner.driver_initialised in [bstack1ll_opy_ (u"ࠣࡤࡨࡪࡴࡸࡥࡠࡨࡨࡥࡹࡻࡲࡦࠤ౤"), bstack1ll_opy_ (u"ࠤࡥࡩ࡫ࡵࡲࡦࡡࡤࡰࡱࠨ౥")]:
          bstack1l111ll11l_opy_(context, bstack1l111l1l_opy_, bstack1ll_opy_ (u"ࠥࡩࡷࡸ࡯ࡳࠤ౦"))
          bstack1l111111ll_opy_(getattr(context, bstack1ll_opy_ (u"ࠫࡵࡧࡧࡦࠩ౧"), None), bstack1ll_opy_ (u"ࠧ࡬ࡡࡪ࡮ࡨࡨࠧ౨"), bstack111lll1ll_opy_)
          bstack1l1l11l1_opy_.execute_script(bstack1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯ࡤ࡫ࡸࡦࡥࡸࡸࡴࡸ࠺ࠡࡽࠥࡥࡨࡺࡩࡰࡰࠥ࠾ࠥࠨࡡ࡯ࡰࡲࡸࡦࡺࡥࠣ࠮ࠣࠦࡦࡸࡧࡶ࡯ࡨࡲࡹࡹࠢ࠻ࠢࡾࠦࡩࡧࡴࡢࠤ࠽ࠫ౩") + json.dumps(bstack1l111l1l_opy_) + bstack1ll_opy_ (u"ࠧ࠭ࠢࠥࡰࡪࡼࡥ࡭ࠤ࠽ࠤࠧ࡫ࡲࡳࡱࡵࠦࢂࢃࠧ౪"))
          bstack11ll11111l_opy_(bstack1l1l11l1_opy_, bstack1ll_opy_ (u"ࠣࡨࡤ࡭ࡱ࡫ࡤࠣ౫"), bstack1ll_opy_ (u"ࠤࡖࡳࡲ࡫ࠠࡴࡥࡨࡲࡦࡸࡩࡰࡵࠣࡪࡦ࡯࡬ࡦࡦ࠽ࠤࡡࡴࠢ౬") + str(bstack111lll1ll_opy_))
          bstack1l11111l1_opy_ = bstack1ll1l11111_opy_(bstack1l111l1l_opy_, runner.feature.name, logger)
          if (bstack1l11111l1_opy_ != None):
            bstack1l11l1ll11_opy_.append(bstack1l11111l1_opy_)
      else:
        if runner.driver_initialised in [bstack1ll_opy_ (u"ࠥࡦࡪ࡬࡯ࡳࡧࡢࡪࡪࡧࡴࡶࡴࡨࠦ౭"), bstack1ll_opy_ (u"ࠦࡧ࡫ࡦࡰࡴࡨࡣࡦࡲ࡬ࠣ౮")]:
          bstack1l111ll11l_opy_(context, bstack1ll_opy_ (u"ࠧࡌࡥࡢࡶࡸࡶࡪࡀࠠࠣ౯") + str(runner.feature.name) + bstack1ll_opy_ (u"ࠨࠠࡱࡣࡶࡷࡪࡪࠡࠣ౰"), bstack1ll_opy_ (u"ࠢࡪࡰࡩࡳࠧ౱"))
          bstack1l111111ll_opy_(getattr(context, bstack1ll_opy_ (u"ࠨࡲࡤ࡫ࡪ࠭౲"), None), bstack1ll_opy_ (u"ࠤࡳࡥࡸࡹࡥࡥࠤ౳"))
          bstack1l1l11l1_opy_.execute_script(bstack1ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬ࡡࡨࡼࡪࡩࡵࡵࡱࡵ࠾ࠥࢁࠢࡢࡥࡷ࡭ࡴࡴࠢ࠻ࠢࠥࡥࡳࡴ࡯ࡵࡣࡷࡩࠧ࠲ࠠࠣࡣࡵ࡫ࡺࡳࡥ࡯ࡶࡶࠦ࠿ࠦࡻࠣࡦࡤࡸࡦࠨ࠺ࠨ౴") + json.dumps(bstack1ll_opy_ (u"ࠦࡋ࡫ࡡࡵࡷࡵࡩ࠿ࠦࠢ౵") + str(runner.feature.name) + bstack1ll_opy_ (u"ࠧࠦࡰࡢࡵࡶࡩࡩࠧࠢ౶")) + bstack1ll_opy_ (u"࠭ࠬࠡࠤ࡯ࡩࡻ࡫࡬ࠣ࠼ࠣࠦ࡮ࡴࡦࡰࠤࢀࢁࠬ౷"))
          bstack11ll11111l_opy_(bstack1l1l11l1_opy_, bstack1ll_opy_ (u"ࠧࡱࡣࡶࡷࡪࡪࠧ౸"))
          bstack1l11111l1_opy_ = bstack1ll1l11111_opy_(bstack1l111l1l_opy_, runner.feature.name, logger)
          if (bstack1l11111l1_opy_ != None):
            bstack1l11l1ll11_opy_.append(bstack1l11111l1_opy_)
    except Exception as e:
      logger.debug(bstack1ll_opy_ (u"ࠨࡈࡤ࡭ࡱ࡫ࡤࠡࡶࡲࠤࡲࡧࡲ࡬ࠢࡶࡩࡸࡹࡩࡰࡰࠣࡷࡹࡧࡴࡶࡵࠣ࡭ࡳࠦࡡࡧࡶࡨࡶࠥ࡬ࡥࡢࡶࡸࡶࡪࡀࠠࡼࡿࠪ౹").format(str(e)))
    bstack1l11111l_opy_(runner, name, context, context.feature, bstack1l1ll11l1l_opy_, *args)
@measure(event_name=EVENTS.bstack1ll1llll11_opy_, stage=STAGE.bstack1l1lll1ll1_opy_, hook_type=bstack1ll_opy_ (u"ࠤࡤࡪࡹ࡫ࡲࡂ࡮࡯ࠦ౺"), bstack1l1l11ll_opy_=bstack1llll1111l_opy_)
def bstack111ll11ll_opy_(runner, name, context, bstack1l1ll11l1l_opy_, *args):
    bstack1l11111l_opy_(runner, name, context, runner, bstack1l1ll11l1l_opy_, *args)
def bstack11l1ll11l1_opy_(self, name, context, *args):
  try:
    if bstack11l111llll_opy_:
      platform_index = int(threading.current_thread()._name) % bstack11l1lll1l1_opy_
      bstack1l1ll1ll11_opy_ = CONFIG[bstack1ll_opy_ (u"ࠪࡴࡱࡧࡴࡧࡱࡵࡱࡸ࠭౻")][platform_index]
      os.environ[bstack1ll_opy_ (u"ࠫࡈ࡛ࡒࡓࡇࡑࡘࡤࡖࡌࡂࡖࡉࡓࡗࡓ࡟ࡅࡃࡗࡅࠬ౼")] = json.dumps(bstack1l1ll1ll11_opy_)
    global bstack1l1ll11l1l_opy_
    if not hasattr(self, bstack1ll_opy_ (u"ࠬࡪࡲࡪࡸࡨࡶࡤ࡯࡮ࡪࡶ࡬ࡥࡱ࡯ࡳࡦࡦࠪ౽")):
      self.driver_initialised = None
    bstack1lll1l1l1_opy_ = {
        bstack1ll_opy_ (u"࠭ࡢࡦࡨࡲࡶࡪࡥࡡ࡭࡮ࠪ౾"): bstack1l1111ll1l_opy_,
        bstack1ll_opy_ (u"ࠧࡣࡧࡩࡳࡷ࡫࡟ࡧࡧࡤࡸࡺࡸࡥࠨ౿"): bstack1l111ll111_opy_,
        bstack1ll_opy_ (u"ࠨࡤࡨࡪࡴࡸࡥࡠࡶࡤ࡫ࠬಀ"): bstack1l111ll1_opy_,
        bstack1ll_opy_ (u"ࠩࡥࡩ࡫ࡵࡲࡦࡡࡶࡧࡪࡴࡡࡳ࡫ࡲࠫಁ"): bstack11lll1ll1_opy_,
        bstack1ll_opy_ (u"ࠪࡦࡪ࡬࡯ࡳࡧࡢࡷࡹ࡫ࡰࠨಂ"): bstack1ll1ll1ll1_opy_,
        bstack1ll_opy_ (u"ࠫࡦ࡬ࡴࡦࡴࡢࡷࡹ࡫ࡰࠨಃ"): bstack11l11l1ll1_opy_,
        bstack1ll_opy_ (u"ࠬࡧࡦࡵࡧࡵࡣࡸࡩࡥ࡯ࡣࡵ࡭ࡴ࠭಄"): bstack11ll11ll_opy_,
        bstack1ll_opy_ (u"࠭ࡡࡧࡶࡨࡶࡤࡺࡡࡨࠩಅ"): bstack111l111l_opy_,
        bstack1ll_opy_ (u"ࠧࡢࡨࡷࡩࡷࡥࡦࡦࡣࡷࡹࡷ࡫ࠧಆ"): bstack1l1111ll_opy_,
        bstack1ll_opy_ (u"ࠨࡣࡩࡸࡪࡸ࡟ࡢ࡮࡯ࠫಇ"): bstack111ll11ll_opy_
    }
    handler = bstack1lll1l1l1_opy_.get(name, bstack1l1ll11l1l_opy_)
    try:
      handler(self, name, context, bstack1l1ll11l1l_opy_, *args)
    except Exception as e:
      logger.debug(bstack1ll_opy_ (u"ࠩࡈࡶࡷࡵࡲࠡ࡫ࡱࠤࡧ࡫ࡨࡢࡸࡨࠤ࡭ࡵ࡯࡬ࠢ࡫ࡥࡳࡪ࡬ࡦࡴࠣࡿࢂࡀࠠࡼࡿࠪಈ").format(name, str(e)))
    if name in [bstack1ll_opy_ (u"ࠪࡥ࡫ࡺࡥࡳࡡࡩࡩࡦࡺࡵࡳࡧࠪಉ"), bstack1ll_opy_ (u"ࠫࡦ࡬ࡴࡦࡴࡢࡷࡨ࡫࡮ࡢࡴ࡬ࡳࠬಊ"), bstack1ll_opy_ (u"ࠬࡧࡦࡵࡧࡵࡣࡦࡲ࡬ࠨಋ")]:
      try:
        bstack1l1l11l1_opy_ = threading.current_thread().bstackSessionDriver if bstack1l1lllll1l_opy_(bstack1ll_opy_ (u"࠭ࡢࡴࡶࡤࡧࡰ࡙ࡥࡴࡵ࡬ࡳࡳࡊࡲࡪࡸࡨࡶࠬಌ")) else context.browser
        bstack1l1l1lll_opy_ = (
          (name == bstack1ll_opy_ (u"ࠧࡢࡨࡷࡩࡷࡥࡡ࡭࡮ࠪ಍") and self.driver_initialised == bstack1ll_opy_ (u"ࠣࡤࡨࡪࡴࡸࡥࡠࡣ࡯ࡰࠧಎ")) or
          (name == bstack1ll_opy_ (u"ࠩࡤࡪࡹ࡫ࡲࡠࡨࡨࡥࡹࡻࡲࡦࠩಏ") and self.driver_initialised == bstack1ll_opy_ (u"ࠥࡦࡪ࡬࡯ࡳࡧࡢࡪࡪࡧࡴࡶࡴࡨࠦಐ")) or
          (name == bstack1ll_opy_ (u"ࠫࡦ࡬ࡴࡦࡴࡢࡷࡨ࡫࡮ࡢࡴ࡬ࡳࠬ಑") and self.driver_initialised in [bstack1ll_opy_ (u"ࠧࡨࡥࡧࡱࡵࡩࡤࡹࡣࡦࡰࡤࡶ࡮ࡵࠢಒ"), bstack1ll_opy_ (u"ࠨࡩ࡯ࡵࡷࡩࡵࠨಓ")]) or
          (name == bstack1ll_opy_ (u"ࠧࡢࡨࡷࡩࡷࡥࡳࡵࡧࡳࠫಔ") and self.driver_initialised == bstack1ll_opy_ (u"ࠣࡤࡨࡪࡴࡸࡥࡠࡵࡷࡩࡵࠨಕ"))
        )
        if bstack1l1l1lll_opy_:
          self.driver_initialised = None
          if bstack1l1l11l1_opy_ and hasattr(bstack1l1l11l1_opy_, bstack1ll_opy_ (u"ࠩࡶࡩࡸࡹࡩࡰࡰࡢ࡭ࡩ࠭ಖ")):
            try:
              bstack1l1l11l1_opy_.quit()
            except Exception as e:
              logger.debug(bstack1ll_opy_ (u"ࠪࡉࡷࡸ࡯ࡳࠢࡴࡹ࡮ࡺࡴࡪࡰࡪࠤࡩࡸࡩࡷࡧࡵࠤ࡮ࡴࠠࡣࡧ࡫ࡥࡻ࡫ࠠࡩࡱࡲ࡯࠿ࠦࡻࡾࠩಗ").format(str(e)))
      except Exception as e:
        logger.debug(bstack1ll_opy_ (u"ࠫࡊࡸࡲࡰࡴࠣ࡭ࡳࠦࡡࡧࡶࡨࡶࠥ࡮࡯ࡰ࡭ࠣࡧࡱ࡫ࡡ࡯ࡷࡳࠤ࡫ࡵࡲࠡࡽࢀ࠾ࠥࢁࡽࠨಘ").format(name, str(e)))
  except Exception as e:
    logger.debug(bstack1ll_opy_ (u"ࠬࡉࡲࡪࡶ࡬ࡧࡦࡲࠠࡦࡴࡵࡳࡷࠦࡩ࡯ࠢࡥࡩ࡭ࡧࡶࡦࠢࡵࡹࡳࠦࡨࡰࡱ࡮ࠤࢀࢃ࠺ࠡࡽࢀࠫಙ").format(name, str(e)))
    try:
      bstack1l1ll11l1l_opy_(self, name, context, *args)
    except Exception as e2:
      logger.debug(bstack1ll_opy_ (u"࠭ࡅࡳࡴࡲࡶࠥ࡯࡮ࠡࡨࡤࡰࡱࡨࡡࡤ࡭ࠣࡳࡷ࡯ࡧࡪࡰࡤࡰࠥࡨࡥࡩࡣࡹࡩࠥ࡮࡯ࡰ࡭ࠣࡿࢂࡀࠠࡼࡿࠪಚ").format(name, str(e2)))
def bstack1lll111l1_opy_(config, startdir):
  return bstack1ll_opy_ (u"ࠢࡥࡴ࡬ࡺࡪࡸ࠺ࠡࡽ࠳ࢁࠧಛ").format(bstack1ll_opy_ (u"ࠣࡄࡵࡳࡼࡹࡥࡳࡕࡷࡥࡨࡱࠢಜ"))
notset = Notset()
def bstack1l1l1lll1l_opy_(self, name: str, default=notset, skip: bool = False):
  global bstack1l11lll111_opy_
  if str(name).lower() == bstack1ll_opy_ (u"ࠩࡧࡶ࡮ࡼࡥࡳࠩಝ"):
    return bstack1ll_opy_ (u"ࠥࡆࡷࡵࡷࡴࡧࡵࡗࡹࡧࡣ࡬ࠤಞ")
  else:
    return bstack1l11lll111_opy_(self, name, default, skip)
def bstack1l11ll11ll_opy_(item, when):
  global bstack1l111l1ll_opy_
  try:
    bstack1l111l1ll_opy_(item, when)
  except Exception as e:
    pass
def bstack1llllll1l1_opy_():
  return
def bstack1l11ll1l1_opy_(type, name, status, reason, bstack1lllll1lll_opy_, bstack11l1l11ll1_opy_):
  bstack1l1lll1l1l_opy_ = {
    bstack1ll_opy_ (u"ࠫࡦࡩࡴࡪࡱࡱࠫಟ"): type,
    bstack1ll_opy_ (u"ࠬࡧࡲࡨࡷࡰࡩࡳࡺࡳࠨಠ"): {}
  }
  if type == bstack1ll_opy_ (u"࠭ࡡ࡯ࡰࡲࡸࡦࡺࡥࠨಡ"):
    bstack1l1lll1l1l_opy_[bstack1ll_opy_ (u"ࠧࡢࡴࡪࡹࡲ࡫࡮ࡵࡵࠪಢ")][bstack1ll_opy_ (u"ࠨ࡮ࡨࡺࡪࡲࠧಣ")] = bstack1lllll1lll_opy_
    bstack1l1lll1l1l_opy_[bstack1ll_opy_ (u"ࠩࡤࡶ࡬ࡻ࡭ࡦࡰࡷࡷࠬತ")][bstack1ll_opy_ (u"ࠪࡨࡦࡺࡡࠨಥ")] = json.dumps(str(bstack11l1l11ll1_opy_))
  if type == bstack1ll_opy_ (u"ࠫࡸ࡫ࡴࡔࡧࡶࡷ࡮ࡵ࡮ࡏࡣࡰࡩࠬದ"):
    bstack1l1lll1l1l_opy_[bstack1ll_opy_ (u"ࠬࡧࡲࡨࡷࡰࡩࡳࡺࡳࠨಧ")][bstack1ll_opy_ (u"࠭࡮ࡢ࡯ࡨࠫನ")] = name
  if type == bstack1ll_opy_ (u"ࠧࡴࡧࡷࡗࡪࡹࡳࡪࡱࡱࡗࡹࡧࡴࡶࡵࠪ಩"):
    bstack1l1lll1l1l_opy_[bstack1ll_opy_ (u"ࠨࡣࡵ࡫ࡺࡳࡥ࡯ࡶࡶࠫಪ")][bstack1ll_opy_ (u"ࠩࡶࡸࡦࡺࡵࡴࠩಫ")] = status
    if status == bstack1ll_opy_ (u"ࠪࡪࡦ࡯࡬ࡦࡦࠪಬ"):
      bstack1l1lll1l1l_opy_[bstack1ll_opy_ (u"ࠫࡦࡸࡧࡶ࡯ࡨࡲࡹࡹࠧಭ")][bstack1ll_opy_ (u"ࠬࡸࡥࡢࡵࡲࡲࠬಮ")] = json.dumps(str(reason))
  bstack1llll11l11_opy_ = bstack1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯ࡤ࡫ࡸࡦࡥࡸࡸࡴࡸ࠺ࠡࡽࢀࠫಯ").format(json.dumps(bstack1l1lll1l1l_opy_))
  return bstack1llll11l11_opy_
def bstack1lll11l11_opy_(driver_command, response):
    if driver_command == bstack1ll_opy_ (u"ࠧࡴࡥࡵࡩࡪࡴࡳࡩࡱࡷࠫರ"):
        bstack1lll1111l_opy_.bstack1l1l1ll111_opy_({
            bstack1ll_opy_ (u"ࠨ࡫ࡰࡥ࡬࡫ࠧಱ"): response[bstack1ll_opy_ (u"ࠩࡹࡥࡱࡻࡥࠨಲ")],
            bstack1ll_opy_ (u"ࠪࡸࡪࡹࡴࡠࡴࡸࡲࡤࡻࡵࡪࡦࠪಳ"): bstack1lll1111l_opy_.current_test_uuid()
        })
def bstack111l111ll_opy_(item, call, rep):
  global bstack11lll1l111_opy_
  global bstack1llll11lll_opy_
  global bstack1111l11ll_opy_
  name = bstack1ll_opy_ (u"ࠫࠬ಴")
  try:
    if rep.when == bstack1ll_opy_ (u"ࠬࡩࡡ࡭࡮ࠪವ"):
      bstack1111l1l11_opy_ = threading.current_thread().bstackSessionId
      try:
        if not bstack1111l11ll_opy_:
          name = str(rep.nodeid)
          bstack1111l11l1_opy_ = bstack1l11ll1l1_opy_(bstack1ll_opy_ (u"࠭ࡳࡦࡶࡖࡩࡸࡹࡩࡰࡰࡑࡥࡲ࡫ࠧಶ"), name, bstack1ll_opy_ (u"ࠧࠨಷ"), bstack1ll_opy_ (u"ࠨࠩಸ"), bstack1ll_opy_ (u"ࠩࠪಹ"), bstack1ll_opy_ (u"ࠪࠫ಺"))
          threading.current_thread().bstack1l11ll1111_opy_ = name
          for driver in bstack1llll11lll_opy_:
            if bstack1111l1l11_opy_ == driver.session_id:
              driver.execute_script(bstack1111l11l1_opy_)
      except Exception as e:
        logger.debug(bstack1ll_opy_ (u"ࠫࡊࡸࡲࡰࡴࠣ࡭ࡳࠦࡳࡦࡶࡷ࡭ࡳ࡭ࠠࡴࡧࡶࡷ࡮ࡵ࡮ࡏࡣࡰࡩࠥ࡬࡯ࡳࠢࡳࡽࡹ࡫ࡳࡵ࠯ࡥࡨࡩࠦࡳࡦࡵࡶ࡭ࡴࡴ࠺ࠡࡽࢀࠫ಻").format(str(e)))
      try:
        bstack1l1111l1l1_opy_(rep.outcome.lower())
        if rep.outcome.lower() != bstack1ll_opy_ (u"ࠬࡹ࡫ࡪࡲࡳࡩࡩ಼࠭"):
          status = bstack1ll_opy_ (u"࠭ࡦࡢ࡫࡯ࡩࡩ࠭ಽ") if rep.outcome.lower() == bstack1ll_opy_ (u"ࠧࡧࡣ࡬ࡰࡪࡪࠧಾ") else bstack1ll_opy_ (u"ࠨࡲࡤࡷࡸ࡫ࡤࠨಿ")
          reason = bstack1ll_opy_ (u"ࠩࠪೀ")
          if status == bstack1ll_opy_ (u"ࠪࡪࡦ࡯࡬ࡦࡦࠪು"):
            reason = rep.longrepr.reprcrash.message
            if (not threading.current_thread().bstackTestErrorMessages):
              threading.current_thread().bstackTestErrorMessages = []
            threading.current_thread().bstackTestErrorMessages.append(reason)
          level = bstack1ll_opy_ (u"ࠫ࡮ࡴࡦࡰࠩೂ") if status == bstack1ll_opy_ (u"ࠬࡶࡡࡴࡵࡨࡨࠬೃ") else bstack1ll_opy_ (u"࠭ࡥࡳࡴࡲࡶࠬೄ")
          data = name + bstack1ll_opy_ (u"ࠧࠡࡲࡤࡷࡸ࡫ࡤࠢࠩ೅") if status == bstack1ll_opy_ (u"ࠨࡲࡤࡷࡸ࡫ࡤࠨೆ") else name + bstack1ll_opy_ (u"ࠩࠣࡪࡦ࡯࡬ࡦࡦࠤࠤࠬೇ") + reason
          bstack1l1l1lll11_opy_ = bstack1l11ll1l1_opy_(bstack1ll_opy_ (u"ࠪࡥࡳࡴ࡯ࡵࡣࡷࡩࠬೈ"), bstack1ll_opy_ (u"ࠫࠬ೉"), bstack1ll_opy_ (u"ࠬ࠭ೊ"), bstack1ll_opy_ (u"࠭ࠧೋ"), level, data)
          for driver in bstack1llll11lll_opy_:
            if bstack1111l1l11_opy_ == driver.session_id:
              driver.execute_script(bstack1l1l1lll11_opy_)
      except Exception as e:
        logger.debug(bstack1ll_opy_ (u"ࠧࡆࡴࡵࡳࡷࠦࡩ࡯ࠢࡶࡩࡹࡺࡩ࡯ࡩࠣࡷࡪࡹࡳࡪࡱࡱࠤࡨࡵ࡮ࡵࡧࡻࡸࠥ࡬࡯ࡳࠢࡳࡽࡹ࡫ࡳࡵ࠯ࡥࡨࡩࠦࡳࡦࡵࡶ࡭ࡴࡴ࠺ࠡࡽࢀࠫೌ").format(str(e)))
  except Exception as e:
    logger.debug(bstack1ll_opy_ (u"ࠨࡇࡵࡶࡴࡸࠠࡪࡰࠣ࡫ࡪࡺࡴࡪࡰࡪࠤࡸࡺࡡࡵࡧࠣ࡭ࡳࠦࡰࡺࡶࡨࡷࡹ࠳ࡢࡥࡦࠣࡸࡪࡹࡴࠡࡵࡷࡥࡹࡻࡳ࠻ࠢࡾࢁ್ࠬ").format(str(e)))
  bstack11lll1l111_opy_(item, call, rep)
def bstack11l111ll11_opy_(driver, bstack11l111lll1_opy_, test=None):
  global bstack11l1l111l_opy_
  if test != None:
    bstack11l1l1llll_opy_ = getattr(test, bstack1ll_opy_ (u"ࠩࡱࡥࡲ࡫ࠧ೎"), None)
    bstack1l1lll1ll_opy_ = getattr(test, bstack1ll_opy_ (u"ࠪࡹࡺ࡯ࡤࠨ೏"), None)
    PercySDK.screenshot(driver, bstack11l111lll1_opy_, bstack11l1l1llll_opy_=bstack11l1l1llll_opy_, bstack1l1lll1ll_opy_=bstack1l1lll1ll_opy_, bstack1ll1lll11l_opy_=bstack11l1l111l_opy_)
  else:
    PercySDK.screenshot(driver, bstack11l111lll1_opy_)
@measure(event_name=EVENTS.bstack1l1l1llll_opy_, stage=STAGE.bstack1l1lll1ll1_opy_, bstack1l1l11ll_opy_=bstack1llll1111l_opy_)
def bstack1l1l1ll1ll_opy_(driver):
  if bstack11l11l1111_opy_.bstack11l111ll1_opy_() is True or bstack11l11l1111_opy_.capturing() is True:
    return
  bstack11l11l1111_opy_.bstack11l11l1l_opy_()
  while not bstack11l11l1111_opy_.bstack11l111ll1_opy_():
    bstack11ll111l_opy_ = bstack11l11l1111_opy_.bstack1ll1ll11_opy_()
    bstack11l111ll11_opy_(driver, bstack11ll111l_opy_)
  bstack11l11l1111_opy_.bstack11l1l11l_opy_()
def bstack11ll1l1l1l_opy_(sequence, driver_command, response = None, bstack111ll1lll_opy_ = None, args = None):
    try:
      if sequence != bstack1ll_opy_ (u"ࠫࡧ࡫ࡦࡰࡴࡨࠫ೐"):
        return
      if percy.bstack11ll11lll1_opy_() == bstack1ll_opy_ (u"ࠧ࡬ࡡ࡭ࡵࡨࠦ೑"):
        return
      bstack11ll111l_opy_ = bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"࠭ࡰࡦࡴࡦࡽࡘ࡫ࡳࡴ࡫ࡲࡲࡓࡧ࡭ࡦࠩ೒"), None)
      for command in bstack11ll1lll1l_opy_:
        if command == driver_command:
          with bstack1lll11l1l_opy_:
            bstack1l11l11ll1_opy_ = bstack1llll11lll_opy_.copy()
          for driver in bstack1l11l11ll1_opy_:
            bstack1l1l1ll1ll_opy_(driver)
      bstack11l1l1l11l_opy_ = percy.bstack1l1l1111l1_opy_()
      if driver_command in bstack11111llll_opy_[bstack11l1l1l11l_opy_]:
        bstack11l11l1111_opy_.bstack1llll11l1l_opy_(bstack11ll111l_opy_, driver_command)
    except Exception as e:
      pass
def bstack1l1lllll_opy_(framework_name):
  if bstack1ll1l1l111_opy_.get_property(bstack1ll_opy_ (u"ࠧࡣࡵࡷࡥࡨࡱ࡟࡮ࡱࡧࡣࡨࡧ࡬࡭ࡧࡧࠫ೓")):
      return
  bstack1ll1l1l111_opy_.bstack111ll1ll1_opy_(bstack1ll_opy_ (u"ࠨࡤࡶࡸࡦࡩ࡫ࡠ࡯ࡲࡨࡤࡩࡡ࡭࡮ࡨࡨࠬ೔"), True)
  global bstack11l11ll111_opy_
  global bstack111lllll_opy_
  global bstack1lll111111_opy_
  bstack11l11ll111_opy_ = framework_name
  logger.info(bstack111lll11l_opy_.format(bstack11l11ll111_opy_.split(bstack1ll_opy_ (u"ࠩ࠰ࠫೕ"))[0]))
  bstack1l111l11ll_opy_()
  try:
    from selenium import webdriver
    from selenium.webdriver.common.service import Service
    from selenium.webdriver.remote.webdriver import WebDriver
    if bstack11l111llll_opy_:
      Service.start = bstack1l1l11l11_opy_
      Service.stop = bstack11111111l_opy_
      webdriver.Remote.get = bstack1l11l11111_opy_
      WebDriver.quit = bstack1ll1lll1_opy_
      webdriver.Remote.__init__ = bstack1l1l1l111_opy_
    if not bstack11l111llll_opy_:
        webdriver.Remote.__init__ = bstack1ll11l1ll1_opy_
    WebDriver.getAccessibilityResults = getAccessibilityResults
    WebDriver.get_accessibility_results = getAccessibilityResults
    WebDriver.getAccessibilityResultsSummary = getAccessibilityResultsSummary
    WebDriver.get_accessibility_results_summary = getAccessibilityResultsSummary
    WebDriver.performScan = perform_scan
    WebDriver.perform_scan = perform_scan
    WebDriver.execute = bstack1l11l1l11_opy_
    bstack111lllll_opy_ = True
  except Exception as e:
    pass
  try:
    if bstack11l111llll_opy_:
      from QWeb.keywords import browser
      browser.close_browser = bstack1ll11lll_opy_
  except Exception as e:
    pass
  bstack1l11l1l1_opy_()
  if not bstack111lllll_opy_:
    bstack1llll1ll1_opy_(bstack1ll_opy_ (u"ࠥࡔࡦࡩ࡫ࡢࡩࡨࡷࠥࡴ࡯ࡵࠢ࡬ࡲࡸࡺࡡ࡭࡮ࡨࡨࠧೖ"), bstack11l1lll11_opy_)
  if bstack111l1111_opy_():
    try:
      from selenium.webdriver.remote.remote_connection import RemoteConnection
      if hasattr(RemoteConnection, bstack1ll_opy_ (u"ࠫࡤ࡭ࡥࡵࡡࡳࡶࡴࡾࡹࡠࡷࡵࡰࠬ೗")) and callable(getattr(RemoteConnection, bstack1ll_opy_ (u"ࠬࡥࡧࡦࡶࡢࡴࡷࡵࡸࡺࡡࡸࡶࡱ࠭೘"))):
        RemoteConnection._get_proxy_url = bstack11ll111ll1_opy_
      else:
        from selenium.webdriver.remote.client_config import ClientConfig
        ClientConfig.get_proxy_url = bstack11ll111ll1_opy_
    except Exception as e:
      logger.error(bstack1ll1111ll_opy_.format(str(e)))
  if bstack1ll1lllll_opy_():
    bstack1l1lll11_opy_(CONFIG, logger)
  if (bstack1ll_opy_ (u"࠭ࡲࡰࡤࡲࡸࠬ೙") in str(framework_name).lower()):
    try:
      from robot import run_cli
      from robot.output import Output
      from robot.running.status import TestStatus
      from pabot.pabot import QueueItem
      from pabot import pabot
      try:
        if percy.bstack11ll11lll1_opy_() == bstack1ll_opy_ (u"ࠢࡵࡴࡸࡩࠧ೚"):
          bstack111l1ll1_opy_(bstack11ll1l1l1l_opy_)
        from SeleniumLibrary.keywords.webdrivertools.webdrivertools import WebDriverCreator
        WebDriverCreator._get_ff_profile = bstack11l11l1l1_opy_
        from SeleniumLibrary.keywords.webdrivertools.webdrivertools import WebDriverCache
        WebDriverCache.close = bstack1llll1l1_opy_
      except Exception as e:
        logger.warning(bstack1l11111111_opy_ + str(e))
      try:
        from AppiumLibrary.utils.applicationcache import ApplicationCache
        ApplicationCache.close = bstack1l11l111ll_opy_
      except Exception as e:
        logger.debug(bstack11l1111l11_opy_ + str(e))
    except Exception as e:
      bstack1llll1ll1_opy_(e, bstack1l11111111_opy_)
    Output.start_test = bstack1l1l11ll11_opy_
    Output.end_test = bstack1l111l1ll1_opy_
    TestStatus.__init__ = bstack1ll1l111l_opy_
    QueueItem.__init__ = bstack1l1l1ll11_opy_
    pabot._create_items = bstack11ll11l1_opy_
    try:
      from pabot import __version__ as bstack11l1l11l1l_opy_
      if version.parse(bstack11l1l11l1l_opy_) >= version.parse(bstack1ll_opy_ (u"ࠨ࠷࠱࠴࠳࠶ࠧ೛")):
        pabot._run = bstack11lll11l11_opy_
      elif version.parse(bstack11l1l11l1l_opy_) >= version.parse(bstack1ll_opy_ (u"ࠩ࠷࠲࠷࠴࠰ࠨ೜")):
        pabot._run = bstack1ll1lll111_opy_
      elif version.parse(bstack11l1l11l1l_opy_) >= version.parse(bstack1ll_opy_ (u"ࠪ࠶࠳࠷࠵࠯࠲ࠪೝ")):
        pabot._run = bstack11l1l11111_opy_
      elif version.parse(bstack11l1l11l1l_opy_) >= version.parse(bstack1ll_opy_ (u"ࠫ࠷࠴࠱࠴࠰࠳ࠫೞ")):
        pabot._run = bstack11l1l11ll_opy_
      else:
        pabot._run = bstack1l1l1l11l_opy_
    except Exception as e:
      pabot._run = bstack1l1l1l11l_opy_
    pabot._create_command_for_execution = bstack1lll11l1l1_opy_
    pabot._report_results = bstack1ll11lll11_opy_
  if bstack1ll_opy_ (u"ࠬࡨࡥࡩࡣࡹࡩࠬ೟") in str(framework_name).lower():
    try:
      from behave.runner import Runner
      from behave.model import Step
    except Exception as e:
      bstack1llll1ll1_opy_(e, bstack1l11l1l1l1_opy_)
    Runner.run_hook = bstack11l1ll11l1_opy_
    Step.run = bstack1ll1lll1l_opy_
  if bstack1ll_opy_ (u"࠭ࡰࡺࡶࡨࡷࡹ࠭ೠ") in str(framework_name).lower():
    if not bstack11l111llll_opy_:
      return
    try:
      from pytest_selenium import pytest_selenium
      from _pytest.config import Config
      pytest_selenium.pytest_report_header = bstack1lll111l1_opy_
      from pytest_selenium.drivers import browserstack
      browserstack.pytest_selenium_runtest_makereport = bstack1llllll1l1_opy_
      Config.getoption = bstack1l1l1lll1l_opy_
    except Exception as e:
      pass
    try:
      from pytest_bdd import reporting
      reporting.runtest_makereport = bstack111l111ll_opy_
    except Exception as e:
      pass
def bstack1lll11llll_opy_():
  global CONFIG
  if bstack1ll_opy_ (u"ࠧࡱࡣࡵࡥࡱࡲࡥ࡭ࡵࡓࡩࡷࡖ࡬ࡢࡶࡩࡳࡷࡳࠧೡ") in CONFIG and int(CONFIG[bstack1ll_opy_ (u"ࠨࡲࡤࡶࡦࡲ࡬ࡦ࡮ࡶࡔࡪࡸࡐ࡭ࡣࡷࡪࡴࡸ࡭ࠨೢ")]) > 1:
    logger.warning(bstack1lll1l1l11_opy_)
def bstack1l1llllll1_opy_(arg, bstack1l1ll1l11_opy_, bstack1lll1l11l_opy_=None):
  global CONFIG
  global bstack1ll111lll_opy_
  global bstack11l11l11ll_opy_
  global bstack11l111llll_opy_
  global bstack1ll1l1l111_opy_
  bstack11ll11l11l_opy_ = bstack1ll_opy_ (u"ࠩࡳࡽࡹ࡫ࡳࡵࠩೣ")
  if bstack1l1ll1l11_opy_ and isinstance(bstack1l1ll1l11_opy_, str):
    bstack1l1ll1l11_opy_ = eval(bstack1l1ll1l11_opy_)
  CONFIG = bstack1l1ll1l11_opy_[bstack1ll_opy_ (u"ࠪࡇࡔࡔࡆࡊࡉࠪ೤")]
  bstack1ll111lll_opy_ = bstack1l1ll1l11_opy_[bstack1ll_opy_ (u"ࠫࡍ࡛ࡂࡠࡗࡕࡐࠬ೥")]
  bstack11l11l11ll_opy_ = bstack1l1ll1l11_opy_[bstack1ll_opy_ (u"ࠬࡏࡓࡠࡃࡓࡔࡤࡇࡕࡕࡑࡐࡅ࡙ࡋࠧ೦")]
  bstack11l111llll_opy_ = bstack1l1ll1l11_opy_[bstack1ll_opy_ (u"࠭ࡂࡓࡑ࡚ࡗࡊࡘࡓࡕࡃࡆࡏࡤࡇࡕࡕࡑࡐࡅ࡙ࡏࡏࡏࠩ೧")]
  bstack1ll1l1l111_opy_.bstack111ll1ll1_opy_(bstack1ll_opy_ (u"ࠧࡣࡵࡷࡥࡨࡱ࡟ࡴࡧࡶࡷ࡮ࡵ࡮ࠨ೨"), bstack11l111llll_opy_)
  os.environ[bstack1ll_opy_ (u"ࠨࡄࡕࡓ࡜࡙ࡅࡓࡕࡗࡅࡈࡑ࡟ࡇࡔࡄࡑࡊ࡝ࡏࡓࡍࠪ೩")] = bstack11ll11l11l_opy_
  os.environ[bstack1ll_opy_ (u"ࠩࡅࡖࡔ࡝ࡓࡆࡔࡖࡘࡆࡉࡋࡠࡅࡒࡒࡋࡏࡇࠨ೪")] = json.dumps(CONFIG)
  os.environ[bstack1ll_opy_ (u"ࠪࡆࡗࡕࡗࡔࡇࡕࡗ࡙ࡇࡃࡌࡡࡋ࡙ࡇࡥࡕࡓࡎࠪ೫")] = bstack1ll111lll_opy_
  os.environ[bstack1ll_opy_ (u"ࠫࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡍࡘࡥࡁࡑࡒࡢࡅ࡚࡚ࡏࡎࡃࡗࡉࠬ೬")] = str(bstack11l11l11ll_opy_)
  os.environ[bstack1ll_opy_ (u"ࠬࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣࡕ࡟ࡔࡆࡕࡗࡣࡕࡒࡕࡈࡋࡑࠫ೭")] = str(True)
  if bstack1ll111l1_opy_(arg, [bstack1ll_opy_ (u"࠭࠭࡯ࠩ೮"), bstack1ll_opy_ (u"ࠧ࠮࠯ࡱࡹࡲࡶࡲࡰࡥࡨࡷࡸ࡫ࡳࠨ೯")]) != -1:
    os.environ[bstack1ll_opy_ (u"ࠨࡄࡕࡓ࡜࡙ࡅࡓࡕࡗࡅࡈࡑ࡟ࡑ࡛ࡗࡉࡘ࡚࡟ࡑࡃࡕࡅࡑࡒࡅࡍࠩ೰")] = str(True)
  if len(sys.argv) <= 1:
    logger.critical(bstack1l1l1ll11l_opy_)
    return
  bstack1l11111ll_opy_()
  global bstack1ll111lll1_opy_
  global bstack11l1l111l_opy_
  global bstack1l1l1ll1l1_opy_
  global bstack111l11l11_opy_
  global bstack1111ll11l_opy_
  global bstack1lll111111_opy_
  global bstack11lllllll1_opy_
  arg.append(bstack1ll_opy_ (u"ࠤ࠰࡛ࠧೱ"))
  arg.append(bstack1ll_opy_ (u"ࠥ࡭࡬ࡴ࡯ࡳࡧ࠽ࡑࡴࡪࡵ࡭ࡧࠣࡥࡱࡸࡥࡢࡦࡼࠤ࡮ࡳࡰࡰࡴࡷࡩࡩࡀࡰࡺࡶࡨࡷࡹ࠴ࡐࡺࡶࡨࡷࡹ࡝ࡡࡳࡰ࡬ࡲ࡬ࠨೲ"))
  arg.append(bstack1ll_opy_ (u"ࠦ࠲࡝ࠢೳ"))
  arg.append(bstack1ll_opy_ (u"ࠧ࡯ࡧ࡯ࡱࡵࡩ࠿࡚ࡨࡦࠢ࡫ࡳࡴࡱࡩ࡮ࡲ࡯ࠦ೴"))
  global bstack11ll1l1lll_opy_
  global bstack1l1111ll1_opy_
  global bstack1ll1l11ll_opy_
  global bstack11l1ll1111_opy_
  global bstack11ll111ll_opy_
  global bstack1ll11l1l_opy_
  global bstack1l111l111_opy_
  global bstack111ll111l_opy_
  global bstack1ll11l11l1_opy_
  global bstack1ll11l1111_opy_
  global bstack1l11lll111_opy_
  global bstack1l111l1ll_opy_
  global bstack11lll1l111_opy_
  try:
    from selenium import webdriver
    from selenium.webdriver.remote.webdriver import WebDriver
    bstack11ll1l1lll_opy_ = webdriver.Remote.__init__
    bstack1l1111ll1_opy_ = WebDriver.quit
    bstack111ll111l_opy_ = WebDriver.close
    bstack1ll11l11l1_opy_ = WebDriver.get
    bstack1ll1l11ll_opy_ = WebDriver.execute
  except Exception as e:
    pass
  if bstack111l1l11l_opy_(CONFIG) and bstack11ll1l11l1_opy_():
    if bstack11l11111l1_opy_() < version.parse(bstack1l11111ll1_opy_):
      logger.error(bstack11ll11111_opy_.format(bstack11l11111l1_opy_()))
    else:
      try:
        from selenium.webdriver.remote.remote_connection import RemoteConnection
        if hasattr(RemoteConnection, bstack1ll_opy_ (u"࠭࡟ࡨࡧࡷࡣࡵࡸ࡯ࡹࡻࡢࡹࡷࡲࠧ೵")) and callable(getattr(RemoteConnection, bstack1ll_opy_ (u"ࠧࡠࡩࡨࡸࡤࡶࡲࡰࡺࡼࡣࡺࡸ࡬ࠨ೶"))):
          bstack1ll11l1111_opy_ = RemoteConnection._get_proxy_url
        else:
          from selenium.webdriver.remote.client_config import ClientConfig
          bstack1ll11l1111_opy_ = ClientConfig.get_proxy_url
      except Exception as e:
        logger.error(bstack1ll1111ll_opy_.format(str(e)))
  try:
    from _pytest.config import Config
    bstack1l11lll111_opy_ = Config.getoption
    from _pytest import runner
    bstack1l111l1ll_opy_ = runner._update_current_test_var
  except Exception as e:
    logger.warning(bstack1ll_opy_ (u"ࠣࠧࡶ࠾ࠥࠫࡳࠣ೷"), bstack1111ll11_opy_, str(e))
  try:
    from pytest_bdd import reporting
    bstack11lll1l111_opy_ = reporting.runtest_makereport
  except Exception as e:
    logger.debug(bstack1ll_opy_ (u"ࠩࡓࡰࡪࡧࡳࡦࠢ࡬ࡲࡸࡺࡡ࡭࡮ࠣࡴࡾࡺࡥࡴࡶ࠰ࡦࡩࡪࠠࡵࡱࠣࡶࡺࡴࠠࡱࡻࡷࡩࡸࡺ࠭ࡣࡦࡧࠤࡹ࡫ࡳࡵࡵࠪ೸"))
  bstack1l1l1ll1l1_opy_ = CONFIG.get(bstack1ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵࡗࡹࡧࡣ࡬ࡎࡲࡧࡦࡲࡏࡱࡶ࡬ࡳࡳࡹࠧ೹"), {}).get(bstack1ll_opy_ (u"ࠫࡱࡵࡣࡢ࡮ࡌࡨࡪࡴࡴࡪࡨ࡬ࡩࡷ࠭೺"))
  bstack11lllllll1_opy_ = True
  if cli.is_enabled(CONFIG):
    if cli.bstack1ll11ll1l_opy_():
      bstack111lll1l_opy_.invoke(bstack1lll1lll_opy_.CONNECT, bstack11ll111l11_opy_())
    platform_index = int(os.environ.get(bstack1ll_opy_ (u"ࠬࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣࡕࡒࡁࡕࡈࡒࡖࡒࡥࡉࡏࡆࡈ࡜ࠬ೻"), bstack1ll_opy_ (u"࠭࠰ࠨ೼")))
  else:
    bstack1l1lllll_opy_(bstack1l1ll11lll_opy_)
  os.environ[bstack1ll_opy_ (u"ࠧࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡕࡔࡇࡕࡒࡆࡓࡅࠨ೽")] = CONFIG[bstack1ll_opy_ (u"ࠨࡷࡶࡩࡷࡔࡡ࡮ࡧࠪ೾")]
  os.environ[bstack1ll_opy_ (u"ࠩࡅࡖࡔ࡝ࡓࡆࡔࡖࡘࡆࡉࡋࡠࡃࡆࡇࡊ࡙ࡓࡠࡍࡈ࡝ࠬ೿")] = CONFIG[bstack1ll_opy_ (u"ࠪࡥࡨࡩࡥࡴࡵࡎࡩࡾ࠭ഀ")]
  os.environ[bstack1ll_opy_ (u"ࠫࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡅ࡚࡚ࡏࡎࡃࡗࡍࡔࡔࠧഁ")] = bstack11l111llll_opy_.__str__()
  from _pytest.config import main as bstack11llllll1l_opy_
  bstack11lll111l_opy_ = []
  try:
    exit_code = bstack11llllll1l_opy_(arg)
    if cli.is_enabled(CONFIG):
      cli.bstack1ll1111l_opy_()
    if bstack1ll_opy_ (u"ࠬࡨࡳࡵࡣࡦ࡯ࡤ࡫ࡲࡳࡱࡵࡣࡱ࡯ࡳࡵࠩം") in multiprocessing.current_process().__dict__.keys():
      for bstack11l1l1ll1_opy_ in multiprocessing.current_process().bstack_error_list:
        bstack11lll111l_opy_.append(bstack11l1l1ll1_opy_)
    try:
      bstack1l1llll11_opy_ = (bstack11lll111l_opy_, int(exit_code))
      bstack1lll1l11l_opy_.append(bstack1l1llll11_opy_)
    except:
      bstack1lll1l11l_opy_.append((bstack11lll111l_opy_, exit_code))
  except Exception as e:
    logger.error(traceback.format_exc())
    bstack11lll111l_opy_.append({bstack1ll_opy_ (u"࠭࡮ࡢ࡯ࡨࠫഃ"): bstack1ll_opy_ (u"ࠧࡑࡴࡲࡧࡪࡹࡳࠡࠩഄ") + os.environ.get(bstack1ll_opy_ (u"ࠨࡄࡕࡓ࡜࡙ࡅࡓࡕࡗࡅࡈࡑ࡟ࡑࡎࡄࡘࡋࡕࡒࡎࡡࡌࡒࡉࡋࡘࠨഅ")), bstack1ll_opy_ (u"ࠩࡨࡶࡷࡵࡲࠨആ"): traceback.format_exc(), bstack1ll_opy_ (u"ࠪ࡭ࡳࡪࡥࡹࠩഇ"): int(os.environ.get(bstack1ll_opy_ (u"ࠫࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡔࡑࡇࡔࡇࡑࡕࡑࡤࡏࡎࡅࡇ࡛ࠫഈ")))})
    bstack1lll1l11l_opy_.append((bstack11lll111l_opy_, 1))
def mod_behave_main(args, retries):
  try:
    from behave.configuration import Configuration
    from behave.__main__ import run_behave
    from browserstack_sdk.bstack_behave_runner import BehaveRunner
    config = Configuration(args)
    config.update_userdata({bstack1ll_opy_ (u"ࠧࡸࡥࡵࡴ࡬ࡩࡸࠨഉ"): str(retries)})
    return run_behave(config, runner_class=BehaveRunner)
  except Exception as e:
    bstack11llll111l_opy_ = e.__class__.__name__
    print(bstack1ll_opy_ (u"ࠨࠥࡴ࠼ࠣࡉࡽࡩࡥࡱࡶ࡬ࡳࡳࠦࡩ࡯ࠢࡵࡹࡳࡴࡩ࡯ࡩࠣࡦࡪ࡮ࡡࡷࡧࠣࡸࡪࡹࡴࠡࠧࡶࠦഊ") % (bstack11llll111l_opy_, e))
    return 1
def bstack11ll11l1l1_opy_(arg):
  global bstack1ll11l11_opy_
  bstack1l1lllll_opy_(bstack1ll111l11l_opy_)
  os.environ[bstack1ll_opy_ (u"ࠧࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡉࡔࡡࡄࡔࡕࡥࡁࡖࡖࡒࡑࡆ࡚ࡅࠨഋ")] = str(bstack11l11l11ll_opy_)
  retries = bstack11llll11l1_opy_.bstack1lll1l11ll_opy_(CONFIG)
  status_code = 0
  if bstack11llll11l1_opy_.bstack111l1l111_opy_(CONFIG):
    status_code = mod_behave_main(arg, retries)
  else:
    from behave.__main__ import main as bstack1ll1111lll_opy_
    status_code = bstack1ll1111lll_opy_(arg)
  if status_code != 0:
    bstack1ll11l11_opy_ = status_code
def bstack1l11ll11l1_opy_():
  logger.info(bstack1ll1l11l_opy_)
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument(bstack1ll_opy_ (u"ࠨࡵࡨࡸࡺࡶࠧഌ"), help=bstack1ll_opy_ (u"ࠩࡊࡩࡳ࡫ࡲࡢࡶࡨࠤࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭ࠣࡧࡴࡴࡦࡪࡩࠪ഍"))
  parser.add_argument(bstack1ll_opy_ (u"ࠪ࠱ࡺ࠭എ"), bstack1ll_opy_ (u"ࠫ࠲࠳ࡵࡴࡧࡵࡲࡦࡳࡥࠨഏ"), help=bstack1ll_opy_ (u"ࠬ࡟࡯ࡶࡴࠣࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬ࠢࡸࡷࡪࡸ࡮ࡢ࡯ࡨࠫഐ"))
  parser.add_argument(bstack1ll_opy_ (u"࠭࠭࡬ࠩ഑"), bstack1ll_opy_ (u"ࠧ࠮࠯࡮ࡩࡾ࠭ഒ"), help=bstack1ll_opy_ (u"ࠨ࡛ࡲࡹࡷࠦࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯ࠥࡧࡣࡤࡧࡶࡷࠥࡱࡥࡺࠩഓ"))
  parser.add_argument(bstack1ll_opy_ (u"ࠩ࠰ࡪࠬഔ"), bstack1ll_opy_ (u"ࠪ࠱࠲࡬ࡲࡢ࡯ࡨࡻࡴࡸ࡫ࠨക"), help=bstack1ll_opy_ (u"ࠫ࡞ࡵࡵࡳࠢࡷࡩࡸࡺࠠࡧࡴࡤࡱࡪࡽ࡯ࡳ࡭ࠪഖ"))
  bstack1l11llllll_opy_ = parser.parse_args()
  try:
    bstack1ll1l11l1l_opy_ = bstack1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮࠲࡬࡫࡮ࡦࡴ࡬ࡧ࠳ࡿ࡭࡭࠰ࡶࡥࡲࡶ࡬ࡦࠩഗ")
    if bstack1l11llllll_opy_.framework and bstack1l11llllll_opy_.framework not in (bstack1ll_opy_ (u"࠭ࡰࡺࡶ࡫ࡳࡳ࠭ഘ"), bstack1ll_opy_ (u"ࠧࡱࡻࡷ࡬ࡴࡴ࠳ࠨങ")):
      bstack1ll1l11l1l_opy_ = bstack1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࠮ࡧࡴࡤࡱࡪࡽ࡯ࡳ࡭࠱ࡽࡲࡲ࠮ࡴࡣࡰࡴࡱ࡫ࠧച")
    bstack11lll1ll11_opy_ = os.path.join(os.path.dirname(os.path.realpath(__file__)), bstack1ll1l11l1l_opy_)
    bstack1l1l111l1l_opy_ = open(bstack11lll1ll11_opy_, bstack1ll_opy_ (u"ࠩࡵࠫഛ"))
    bstack11ll1lll11_opy_ = bstack1l1l111l1l_opy_.read()
    bstack1l1l111l1l_opy_.close()
    if bstack1l11llllll_opy_.username:
      bstack11ll1lll11_opy_ = bstack11ll1lll11_opy_.replace(bstack1ll_opy_ (u"ࠪ࡝ࡔ࡛ࡒࡠࡗࡖࡉࡗࡔࡁࡎࡇࠪജ"), bstack1l11llllll_opy_.username)
    if bstack1l11llllll_opy_.key:
      bstack11ll1lll11_opy_ = bstack11ll1lll11_opy_.replace(bstack1ll_opy_ (u"ࠫ࡞ࡕࡕࡓࡡࡄࡇࡈࡋࡓࡔࡡࡎࡉ࡞࠭ഝ"), bstack1l11llllll_opy_.key)
    if bstack1l11llllll_opy_.framework:
      bstack11ll1lll11_opy_ = bstack11ll1lll11_opy_.replace(bstack1ll_opy_ (u"ࠬ࡟ࡏࡖࡔࡢࡊࡗࡇࡍࡆ࡙ࡒࡖࡐ࠭ഞ"), bstack1l11llllll_opy_.framework)
    file_name = bstack1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯࠳ࡿ࡭࡭ࠩട")
    file_path = os.path.abspath(file_name)
    bstack11l11lll_opy_ = open(file_path, bstack1ll_opy_ (u"ࠧࡸࠩഠ"))
    bstack11l11lll_opy_.write(bstack11ll1lll11_opy_)
    bstack11l11lll_opy_.close()
    logger.info(bstack11l1lll111_opy_)
    try:
      os.environ[bstack1ll_opy_ (u"ࠨࡄࡕࡓ࡜࡙ࡅࡓࡕࡗࡅࡈࡑ࡟ࡇࡔࡄࡑࡊ࡝ࡏࡓࡍࠪഡ")] = bstack1l11llllll_opy_.framework if bstack1l11llllll_opy_.framework != None else bstack1ll_opy_ (u"ࠤࠥഢ")
      config = yaml.safe_load(bstack11ll1lll11_opy_)
      config[bstack1ll_opy_ (u"ࠪࡷࡴࡻࡲࡤࡧࠪണ")] = bstack1ll_opy_ (u"ࠫࡵࡿࡴࡩࡱࡱ࠱ࡸ࡫ࡴࡶࡲࠪത")
      bstack111111ll1_opy_(bstack1l1l1lll1_opy_, config)
    except Exception as e:
      logger.debug(bstack1lll1lll1_opy_.format(str(e)))
  except Exception as e:
    logger.error(bstack1l1l1l11ll_opy_.format(str(e)))
def bstack111111ll1_opy_(bstack1111l111_opy_, config, bstack1l1ll1l1l1_opy_={}):
  global bstack11l111llll_opy_
  global bstack1l1lll1l1_opy_
  global bstack1ll1l1l111_opy_
  if not config:
    return
  bstack1lll1ll1l_opy_ = bstack11l11111l_opy_ if not bstack11l111llll_opy_ else (
    bstack11ll1l11_opy_ if bstack1ll_opy_ (u"ࠬࡧࡰࡱࠩഥ") in config else (
        bstack1l1111111_opy_ if config.get(bstack1ll_opy_ (u"࠭ࡴࡶࡴࡥࡳࡘࡩࡡ࡭ࡧࠪദ")) else bstack1ll1l11l11_opy_
    )
)
  bstack1l111l1lll_opy_ = False
  bstack1ll1ll1l1l_opy_ = False
  if bstack11l111llll_opy_ is True:
      if bstack1ll_opy_ (u"ࠧࡢࡲࡳࠫധ") in config:
          bstack1l111l1lll_opy_ = True
      else:
          bstack1ll1ll1l1l_opy_ = True
  bstack11l1l111ll_opy_ = bstack1ll1l1l1l_opy_.bstack1ll1111ll1_opy_(config, bstack1l1lll1l1_opy_)
  bstack1llllllll1_opy_ = bstack11ll1111_opy_()
  data = {
    bstack1ll_opy_ (u"ࠨࡷࡶࡩࡷࡔࡡ࡮ࡧࠪന"): config[bstack1ll_opy_ (u"ࠩࡸࡷࡪࡸࡎࡢ࡯ࡨࠫഩ")],
    bstack1ll_opy_ (u"ࠪࡥࡨࡩࡥࡴࡵࡎࡩࡾ࠭പ"): config[bstack1ll_opy_ (u"ࠫࡦࡩࡣࡦࡵࡶࡏࡪࡿࠧഫ")],
    bstack1ll_opy_ (u"ࠬ࡫ࡶࡦࡰࡷࡣࡹࡿࡰࡦࠩബ"): bstack1111l111_opy_,
    bstack1ll_opy_ (u"࠭ࡤࡦࡶࡨࡧࡹ࡫ࡤࡇࡴࡤࡱࡪࡽ࡯ࡳ࡭ࠪഭ"): os.environ.get(bstack1ll_opy_ (u"ࠧࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡆࡓࡃࡐࡉ࡜ࡕࡒࡌࠩമ"), bstack1l1lll1l1_opy_),
    bstack1ll_opy_ (u"ࠨࡤࡸ࡭ࡱࡪ࡟ࡩࡣࡶ࡬ࡪࡪ࡟ࡪࡦࠪയ"): bstack1ll11l111l_opy_,
    bstack1ll_opy_ (u"ࠩࡲࡴࡹ࡯࡭ࡢ࡮ࡢ࡬ࡺࡨ࡟ࡶࡴ࡯ࠫര"): bstack1ll11111ll_opy_(),
    bstack1ll_opy_ (u"ࠪࡩࡻ࡫࡮ࡵࡡࡳࡶࡴࡶࡥࡳࡶ࡬ࡩࡸ࠭റ"): {
      bstack1ll_opy_ (u"ࠫࡱࡧ࡮ࡨࡷࡤ࡫ࡪࡥࡦࡳࡣࡰࡩࡼࡵࡲ࡬ࠩല"): str(config[bstack1ll_opy_ (u"ࠬࡹ࡯ࡶࡴࡦࡩࠬള")]) if bstack1ll_opy_ (u"࠭ࡳࡰࡷࡵࡧࡪ࠭ഴ") in config else bstack1ll_opy_ (u"ࠢࡶࡰ࡮ࡲࡴࡽ࡮ࠣവ"),
      bstack1ll_opy_ (u"ࠨ࡮ࡤࡲ࡬ࡻࡡࡨࡧ࡙ࡩࡷࡹࡩࡰࡰࠪശ"): sys.version,
      bstack1ll_opy_ (u"ࠩࡵࡩ࡫࡫ࡲࡳࡧࡵࠫഷ"): bstack11ll1lll1_opy_(os.environ.get(bstack1ll_opy_ (u"ࠪࡆࡗࡕࡗࡔࡇࡕࡗ࡙ࡇࡃࡌࡡࡉࡖࡆࡓࡅࡘࡑࡕࡏࠬസ"), bstack1l1lll1l1_opy_)),
      bstack1ll_opy_ (u"ࠫࡱࡧ࡮ࡨࡷࡤ࡫ࡪ࠭ഹ"): bstack1ll_opy_ (u"ࠬࡶࡹࡵࡪࡲࡲࠬഺ"),
      bstack1ll_opy_ (u"࠭ࡰࡳࡱࡧࡹࡨࡺ഻ࠧ"): bstack1lll1ll1l_opy_,
      bstack1ll_opy_ (u"ࠧࡱࡴࡲࡨࡺࡩࡴࡠ࡯ࡤࡴ഼ࠬ"): bstack11l1l111ll_opy_,
      bstack1ll_opy_ (u"ࠨࡶࡨࡷࡹ࡮ࡵࡣࡡࡸࡹ࡮ࡪࠧഽ"): os.environ[bstack1ll_opy_ (u"ࠩࡅࡖࡔ࡝ࡓࡆࡔࡖࡘࡆࡉࡋࡠࡖࡈࡗ࡙ࡎࡕࡃࡡࡘ࡙ࡎࡊࠧാ")],
      bstack1ll_opy_ (u"ࠪࡪࡷࡧ࡭ࡦࡹࡲࡶࡰ࠭ി"): os.environ.get(bstack1ll_opy_ (u"ࠫࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡊࡗࡇࡍࡆ࡙ࡒࡖࡐ࠭ീ"), bstack1l1lll1l1_opy_),
      bstack1ll_opy_ (u"ࠬ࡬ࡲࡢ࡯ࡨࡻࡴࡸ࡫ࡗࡧࡵࡷ࡮ࡵ࡮ࠨു"): bstack111111l1_opy_(os.environ.get(bstack1ll_opy_ (u"࠭ࡂࡓࡑ࡚ࡗࡊࡘࡓࡕࡃࡆࡏࡤࡌࡒࡂࡏࡈ࡛ࡔࡘࡋࠨൂ"), bstack1l1lll1l1_opy_)),
      bstack1ll_opy_ (u"ࠧࡢࡷࡷࡳࡲࡧࡴࡪࡱࡱࡊࡷࡧ࡭ࡦࡹࡲࡶࡰ࠭ൃ"): bstack1llllllll1_opy_.get(bstack1ll_opy_ (u"ࠨࡰࡤࡱࡪ࠭ൄ")),
      bstack1ll_opy_ (u"ࠩࡤࡹࡹࡵ࡭ࡢࡶ࡬ࡳࡳࡌࡲࡢ࡯ࡨࡻࡴࡸ࡫ࡗࡧࡵࡷ࡮ࡵ࡮ࠨ൅"): bstack1llllllll1_opy_.get(bstack1ll_opy_ (u"ࠪࡺࡪࡸࡳࡪࡱࡱࠫെ")),
      bstack1ll_opy_ (u"ࠫࡧࡻࡩ࡭ࡦࡑࡥࡲ࡫ࠧേ"): config[bstack1ll_opy_ (u"ࠬࡨࡵࡪ࡮ࡧࡒࡦࡳࡥࠨൈ")] if config[bstack1ll_opy_ (u"࠭ࡢࡶ࡫࡯ࡨࡓࡧ࡭ࡦࠩ൉")] else bstack1ll_opy_ (u"ࠢࡶࡰ࡮ࡲࡴࡽ࡮ࠣൊ"),
      bstack1ll_opy_ (u"ࠨࡤࡸ࡭ࡱࡪࡉࡥࡧࡱࡸ࡮࡬ࡩࡦࡴࠪോ"): str(config[bstack1ll_opy_ (u"ࠩࡥࡹ࡮ࡲࡤࡊࡦࡨࡲࡹ࡯ࡦࡪࡧࡵࠫൌ")]) if bstack1ll_opy_ (u"ࠪࡦࡺ࡯࡬ࡥࡋࡧࡩࡳࡺࡩࡧ࡫ࡨࡶ്ࠬ") in config else bstack1ll_opy_ (u"ࠦࡺࡴ࡫࡯ࡱࡺࡲࠧൎ"),
      bstack1ll_opy_ (u"ࠬࡵࡳࠨ൏"): sys.platform,
      bstack1ll_opy_ (u"࠭ࡨࡰࡵࡷࡲࡦࡳࡥࠨ൐"): socket.gethostname(),
      bstack1ll_opy_ (u"ࠧࡴࡦ࡮ࡖࡺࡴࡉࡥࠩ൑"): bstack1ll1l1l111_opy_.get_property(bstack1ll_opy_ (u"ࠨࡵࡧ࡯ࡗࡻ࡮ࡊࡦࠪ൒"))
    }
  }
  if not bstack1ll1l1l111_opy_.get_property(bstack1ll_opy_ (u"ࠩࡶࡨࡰࡑࡩ࡭࡮ࡖ࡭࡬ࡴࡡ࡭ࠩ൓")) is None:
    data[bstack1ll_opy_ (u"ࠪࡩࡻ࡫࡮ࡵࡡࡳࡶࡴࡶࡥࡳࡶ࡬ࡩࡸ࠭ൔ")][bstack1ll_opy_ (u"ࠫ࡫࡯࡮ࡪࡵ࡫ࡩࡩࡓࡥࡵࡣࡧࡥࡹࡧࠧൕ")] = {
      bstack1ll_opy_ (u"ࠬࡸࡥࡢࡵࡲࡲࠬൖ"): bstack1ll_opy_ (u"࠭ࡵࡴࡧࡵࡣࡰ࡯࡬࡭ࡧࡧࠫൗ"),
      bstack1ll_opy_ (u"ࠧࡴ࡫ࡪࡲࡦࡲࠧ൘"): bstack1ll1l1l111_opy_.get_property(bstack1ll_opy_ (u"ࠨࡵࡧ࡯ࡐ࡯࡬࡭ࡕ࡬࡫ࡳࡧ࡬ࠨ൙")),
      bstack1ll_opy_ (u"ࠩࡶ࡭࡬ࡴࡡ࡭ࡐࡸࡱࡧ࡫ࡲࠨ൚"): bstack1ll1l1l111_opy_.get_property(bstack1ll_opy_ (u"ࠪࡷࡩࡱࡋࡪ࡮࡯ࡒࡴ࠭൛"))
    }
  if bstack1111l111_opy_ == bstack111l11lll_opy_:
    data[bstack1ll_opy_ (u"ࠫࡪࡼࡥ࡯ࡶࡢࡴࡷࡵࡰࡦࡴࡷ࡭ࡪࡹࠧ൜")][bstack1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷ࡙ࡴࡢࡥ࡮ࡇࡴࡴࡦࡪࡩࠪ൝")] = bstack111ll1l1_opy_(config)
    data[bstack1ll_opy_ (u"࠭ࡥࡷࡧࡱࡸࡤࡶࡲࡰࡲࡨࡶࡹ࡯ࡥࡴࠩ൞")][bstack1ll_opy_ (u"ࠧࡪࡵࡓࡩࡷࡩࡹࡂࡷࡷࡳࡊࡴࡡࡣ࡮ࡨࡨࠬൟ")] = percy.bstack11l111l1l_opy_
    data[bstack1ll_opy_ (u"ࠨࡧࡹࡩࡳࡺ࡟ࡱࡴࡲࡴࡪࡸࡴࡪࡧࡶࠫൠ")][bstack1ll_opy_ (u"ࠩࡳࡩࡷࡩࡹࡃࡷ࡬ࡰࡩࡏࡤࠨൡ")] = percy.percy_build_id
  if not bstack11llll11l1_opy_.bstack1l1ll1ll1l_opy_(CONFIG):
    data[bstack1ll_opy_ (u"ࠪࡩࡻ࡫࡮ࡵࡡࡳࡶࡴࡶࡥࡳࡶ࡬ࡩࡸ࠭ൢ")][bstack1ll_opy_ (u"ࠫࡹ࡫ࡳࡵࡑࡵࡧ࡭࡫ࡳࡵࡴࡤࡸ࡮ࡵ࡮ࠨൣ")] = bstack11llll11l1_opy_.bstack1l1ll1ll1l_opy_(CONFIG)
  bstack1llllll11l_opy_ = bstack1ll1l1111l_opy_.bstack11lll1111_opy_(CONFIG, logger)
  bstack1l11l1lll_opy_ = bstack11llll11l1_opy_.bstack11lll1111_opy_(config=CONFIG)
  if bstack1llllll11l_opy_ is not None and bstack1l11l1lll_opy_ is not None and bstack1l11l1lll_opy_.bstack1111lll1_opy_():
    data[bstack1ll_opy_ (u"ࠬ࡫ࡶࡦࡰࡷࡣࡵࡸ࡯ࡱࡧࡵࡸ࡮࡫ࡳࠨ൤")][bstack1l11l1lll_opy_.bstack111ll111_opy_()] = bstack1llllll11l_opy_.bstack1l1l1lllll_opy_()
  update(data[bstack1ll_opy_ (u"࠭ࡥࡷࡧࡱࡸࡤࡶࡲࡰࡲࡨࡶࡹ࡯ࡥࡴࠩ൥")], bstack1l1ll1l1l1_opy_)
  try:
    response = bstack1l111111_opy_(bstack1ll_opy_ (u"ࠧࡑࡑࡖࡘࠬ൦"), bstack1l1lll11ll_opy_(bstack1111l1111_opy_), data, {
      bstack1ll_opy_ (u"ࠨࡣࡸࡸ࡭࠭൧"): (config[bstack1ll_opy_ (u"ࠩࡸࡷࡪࡸࡎࡢ࡯ࡨࠫ൨")], config[bstack1ll_opy_ (u"ࠪࡥࡨࡩࡥࡴࡵࡎࡩࡾ࠭൩")])
    })
    if response:
      logger.debug(bstack11ll111l1_opy_.format(bstack1111l111_opy_, str(response.json())))
  except Exception as e:
    logger.debug(bstack1l1111l1_opy_.format(str(e)))
def bstack11ll1lll1_opy_(framework):
  return bstack1ll_opy_ (u"ࠦࢀࢃ࠭ࡱࡻࡷ࡬ࡴࡴࡡࡨࡧࡱࡸ࠴ࢁࡽࠣ൪").format(str(framework), __version__) if framework else bstack1ll_opy_ (u"ࠧࡶࡹࡵࡪࡲࡲࡦ࡭ࡥ࡯ࡶ࠲ࡿࢂࠨ൫").format(
    __version__)
def bstack1l11111ll_opy_():
  global CONFIG
  global bstack1ll1111l1_opy_
  if bool(CONFIG):
    return
  try:
    bstack1l11l1ll1l_opy_()
    logger.debug(bstack11ll11l111_opy_.format(str(CONFIG)))
    bstack1ll1111l1_opy_ = bstack11l1l1lll1_opy_.configure_logger(CONFIG, bstack1ll1111l1_opy_)
    bstack1l111l11ll_opy_()
  except Exception as e:
    logger.error(bstack1ll_opy_ (u"ࠨࡆࡢ࡫࡯ࡩࡩࠦࡴࡰࠢࡶࡩࡹࡻࡰ࠭ࠢࡨࡶࡷࡵࡲ࠻ࠢࠥ൬") + str(e))
    sys.exit(1)
  sys.excepthook = bstack11l1lll1_opy_
  atexit.register(bstack11lll1l11_opy_)
  signal.signal(signal.SIGINT, bstack1lll11lll1_opy_)
  signal.signal(signal.SIGTERM, bstack1lll11lll1_opy_)
def bstack11l1lll1_opy_(exctype, value, traceback):
  global bstack1llll11lll_opy_
  try:
    for driver in bstack1llll11lll_opy_:
      bstack11ll11111l_opy_(driver, bstack1ll_opy_ (u"ࠧࡧࡣ࡬ࡰࡪࡪࠧ൭"), bstack1ll_opy_ (u"ࠣࡕࡨࡷࡸ࡯࡯࡯ࠢࡩࡥ࡮ࡲࡥࡥࠢࡺ࡭ࡹ࡮࠺ࠡ࡞ࡱࠦ൮") + str(value))
  except Exception:
    pass
  logger.info(bstack1l111l1111_opy_)
  bstack1111111ll_opy_(value, True)
  sys.__excepthook__(exctype, value, traceback)
  sys.exit(1)
def bstack1111111ll_opy_(message=bstack1ll_opy_ (u"ࠩࠪ൯"), bstack1l1ll111l_opy_ = False):
  global CONFIG
  bstack1111l111l_opy_ = bstack1ll_opy_ (u"ࠪ࡫ࡱࡵࡢࡢ࡮ࡈࡼࡨ࡫ࡰࡵ࡫ࡲࡲࠬ൰") if bstack1l1ll111l_opy_ else bstack1ll_opy_ (u"ࠫࡪࡸࡲࡰࡴࠪ൱")
  try:
    if message:
      bstack1l1ll1l1l1_opy_ = {
        bstack1111l111l_opy_ : str(message)
      }
      bstack111111ll1_opy_(bstack111l11lll_opy_, CONFIG, bstack1l1ll1l1l1_opy_)
    else:
      bstack111111ll1_opy_(bstack111l11lll_opy_, CONFIG)
  except Exception as e:
    logger.debug(bstack111lll11ll_opy_.format(str(e)))
def bstack1l1l11l11l_opy_(bstack1l1l11l1l_opy_, size):
  bstack11l11111_opy_ = []
  while len(bstack1l1l11l1l_opy_) > size:
    bstack1ll1ll1111_opy_ = bstack1l1l11l1l_opy_[:size]
    bstack11l11111_opy_.append(bstack1ll1ll1111_opy_)
    bstack1l1l11l1l_opy_ = bstack1l1l11l1l_opy_[size:]
  bstack11l11111_opy_.append(bstack1l1l11l1l_opy_)
  return bstack11l11111_opy_
def bstack1l11lll1l1_opy_(args):
  if bstack1ll_opy_ (u"ࠬ࠳࡭ࠨ൲") in args and bstack1ll_opy_ (u"࠭ࡰࡥࡤࠪ൳") in args:
    return True
  return False
@measure(event_name=EVENTS.bstack11ll1l11ll_opy_, stage=STAGE.bstack11l11l1l11_opy_)
def run_on_browserstack(bstack11l111l1_opy_=None, bstack1lll1l11l_opy_=None, bstack1l1l11lll1_opy_=False):
  global CONFIG
  global bstack1ll111lll_opy_
  global bstack11l11l11ll_opy_
  global bstack1l1lll1l1_opy_
  global bstack1ll1l1l111_opy_
  bstack11ll11l11l_opy_ = bstack1ll_opy_ (u"ࠧࠨ൴")
  bstack1l1l1l1ll1_opy_(bstack11ll1ll1_opy_, logger)
  if bstack11l111l1_opy_ and isinstance(bstack11l111l1_opy_, str):
    bstack11l111l1_opy_ = eval(bstack11l111l1_opy_)
  if bstack11l111l1_opy_:
    CONFIG = bstack11l111l1_opy_[bstack1ll_opy_ (u"ࠨࡅࡒࡒࡋࡏࡇࠨ൵")]
    bstack1ll111lll_opy_ = bstack11l111l1_opy_[bstack1ll_opy_ (u"ࠩࡋ࡙ࡇࡥࡕࡓࡎࠪ൶")]
    bstack11l11l11ll_opy_ = bstack11l111l1_opy_[bstack1ll_opy_ (u"ࠪࡍࡘࡥࡁࡑࡒࡢࡅ࡚࡚ࡏࡎࡃࡗࡉࠬ൷")]
    bstack1ll1l1l111_opy_.bstack111ll1ll1_opy_(bstack1ll_opy_ (u"ࠫࡎ࡙࡟ࡂࡒࡓࡣࡆ࡛ࡔࡐࡏࡄࡘࡊ࠭൸"), bstack11l11l11ll_opy_)
    bstack11ll11l11l_opy_ = bstack1ll_opy_ (u"ࠬࡶࡹࡵࡪࡲࡲࠬ൹")
  bstack1ll1l1l111_opy_.bstack111ll1ll1_opy_(bstack1ll_opy_ (u"࠭ࡳࡥ࡭ࡕࡹࡳࡏࡤࠨൺ"), uuid4().__str__())
  logger.info(bstack1ll_opy_ (u"ࠧࡔࡆࡎࠤࡷࡻ࡮ࠡࡵࡷࡥࡷࡺࡥࡥࠢࡺ࡭ࡹ࡮ࠠࡪࡦ࠽ࠤࠬൻ") + bstack1ll1l1l111_opy_.get_property(bstack1ll_opy_ (u"ࠨࡵࡧ࡯ࡗࡻ࡮ࡊࡦࠪർ")));
  logger.debug(bstack1ll_opy_ (u"ࠩࡶࡨࡰࡘࡵ࡯ࡋࡧࡁࠬൽ") + bstack1ll1l1l111_opy_.get_property(bstack1ll_opy_ (u"ࠪࡷࡩࡱࡒࡶࡰࡌࡨࠬൾ")))
  if not bstack1l1l11lll1_opy_:
    if len(sys.argv) <= 1:
      logger.critical(bstack1l1l1ll11l_opy_)
      return
    if sys.argv[1] == bstack1ll_opy_ (u"ࠫ࠲࠳ࡶࡦࡴࡶ࡭ࡴࡴࠧൿ") or sys.argv[1] == bstack1ll_opy_ (u"ࠬ࠳ࡶࠨ඀"):
      logger.info(bstack1ll_opy_ (u"࠭ࡂࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯ࠥࡖࡹࡵࡪࡲࡲ࡙ࠥࡄࡌࠢࡹࡿࢂ࠭ඁ").format(__version__))
      return
    if sys.argv[1] == bstack1ll_opy_ (u"ࠧࡴࡧࡷࡹࡵ࠭ං"):
      bstack1l11ll11l1_opy_()
      return
  args = sys.argv
  bstack1l11111ll_opy_()
  global bstack1ll111lll1_opy_
  global bstack11l1lll1l1_opy_
  global bstack11lllllll1_opy_
  global bstack11l1l1111l_opy_
  global bstack11l1l111l_opy_
  global bstack1l1l1ll1l1_opy_
  global bstack111l11l11_opy_
  global bstack1lll11ll_opy_
  global bstack1111ll11l_opy_
  global bstack1lll111111_opy_
  global bstack1llll1ll11_opy_
  bstack11l1lll1l1_opy_ = len(CONFIG.get(bstack1ll_opy_ (u"ࠨࡲ࡯ࡥࡹ࡬࡯ࡳ࡯ࡶࠫඃ"), []))
  if not bstack11ll11l11l_opy_:
    if args[1] == bstack1ll_opy_ (u"ࠩࡳࡽࡹ࡮࡯࡯ࠩ඄") or args[1] == bstack1ll_opy_ (u"ࠪࡴࡾࡺࡨࡰࡰ࠶ࠫඅ"):
      bstack11ll11l11l_opy_ = bstack1ll_opy_ (u"ࠫࡵࡿࡴࡩࡱࡱࠫආ")
      args = args[2:]
    elif args[1] == bstack1ll_opy_ (u"ࠬࡸ࡯ࡣࡱࡷࠫඇ"):
      bstack11ll11l11l_opy_ = bstack1ll_opy_ (u"࠭ࡲࡰࡤࡲࡸࠬඈ")
      args = args[2:]
    elif args[1] == bstack1ll_opy_ (u"ࠧࡱࡣࡥࡳࡹ࠭ඉ"):
      bstack11ll11l11l_opy_ = bstack1ll_opy_ (u"ࠨࡲࡤࡦࡴࡺࠧඊ")
      args = args[2:]
    elif args[1] == bstack1ll_opy_ (u"ࠩࡵࡳࡧࡵࡴ࠮࡫ࡱࡸࡪࡸ࡮ࡢ࡮ࠪඋ"):
      bstack11ll11l11l_opy_ = bstack1ll_opy_ (u"ࠪࡶࡴࡨ࡯ࡵ࠯࡬ࡲࡹ࡫ࡲ࡯ࡣ࡯ࠫඌ")
      args = args[2:]
    elif args[1] == bstack1ll_opy_ (u"ࠫࡵࡿࡴࡦࡵࡷࠫඍ"):
      bstack11ll11l11l_opy_ = bstack1ll_opy_ (u"ࠬࡶࡹࡵࡧࡶࡸࠬඎ")
      args = args[2:]
    elif args[1] == bstack1ll_opy_ (u"࠭ࡢࡦࡪࡤࡺࡪ࠭ඏ"):
      bstack11ll11l11l_opy_ = bstack1ll_opy_ (u"ࠧࡣࡧ࡫ࡥࡻ࡫ࠧඐ")
      args = args[2:]
    else:
      if not bstack1ll_opy_ (u"ࠨࡨࡵࡥࡲ࡫ࡷࡰࡴ࡮ࠫඑ") in CONFIG or str(CONFIG[bstack1ll_opy_ (u"ࠩࡩࡶࡦࡳࡥࡸࡱࡵ࡯ࠬඒ")]).lower() in [bstack1ll_opy_ (u"ࠪࡴࡾࡺࡨࡰࡰࠪඓ"), bstack1ll_opy_ (u"ࠫࡵࡿࡴࡩࡱࡱ࠷ࠬඔ")]:
        bstack11ll11l11l_opy_ = bstack1ll_opy_ (u"ࠬࡶࡹࡵࡪࡲࡲࠬඕ")
        args = args[1:]
      elif str(CONFIG[bstack1ll_opy_ (u"࠭ࡦࡳࡣࡰࡩࡼࡵࡲ࡬ࠩඖ")]).lower() == bstack1ll_opy_ (u"ࠧࡳࡱࡥࡳࡹ࠭඗"):
        bstack11ll11l11l_opy_ = bstack1ll_opy_ (u"ࠨࡴࡲࡦࡴࡺࠧ඘")
        args = args[1:]
      elif str(CONFIG[bstack1ll_opy_ (u"ࠩࡩࡶࡦࡳࡥࡸࡱࡵ࡯ࠬ඙")]).lower() == bstack1ll_opy_ (u"ࠪࡴࡦࡨ࡯ࡵࠩක"):
        bstack11ll11l11l_opy_ = bstack1ll_opy_ (u"ࠫࡵࡧࡢࡰࡶࠪඛ")
        args = args[1:]
      elif str(CONFIG[bstack1ll_opy_ (u"ࠬ࡬ࡲࡢ࡯ࡨࡻࡴࡸ࡫ࠨග")]).lower() == bstack1ll_opy_ (u"࠭ࡰࡺࡶࡨࡷࡹ࠭ඝ"):
        bstack11ll11l11l_opy_ = bstack1ll_opy_ (u"ࠧࡱࡻࡷࡩࡸࡺࠧඞ")
        args = args[1:]
      elif str(CONFIG[bstack1ll_opy_ (u"ࠨࡨࡵࡥࡲ࡫ࡷࡰࡴ࡮ࠫඟ")]).lower() == bstack1ll_opy_ (u"ࠩࡥࡩ࡭ࡧࡶࡦࠩච"):
        bstack11ll11l11l_opy_ = bstack1ll_opy_ (u"ࠪࡦࡪ࡮ࡡࡷࡧࠪඡ")
        args = args[1:]
      else:
        os.environ[bstack1ll_opy_ (u"ࠫࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡊࡗࡇࡍࡆ࡙ࡒࡖࡐ࠭ජ")] = bstack11ll11l11l_opy_
        bstack1ll1l1lll_opy_(bstack1ll1ll111_opy_)
  os.environ[bstack1ll_opy_ (u"ࠬࡌࡒࡂࡏࡈ࡛ࡔࡘࡋࡠࡗࡖࡉࡉ࠭ඣ")] = bstack11ll11l11l_opy_
  bstack1l1lll1l1_opy_ = bstack11ll11l11l_opy_
  if cli.is_enabled(CONFIG):
    try:
      bstack1l1ll1l1_opy_ = bstack111lllll1l_opy_[bstack1ll_opy_ (u"࠭ࡐ࡚ࡖࡈࡗ࡙࠳ࡂࡅࡆࠪඤ")] if bstack11ll11l11l_opy_ == bstack1ll_opy_ (u"ࠧࡱࡻࡷࡩࡸࡺࠧඥ") and bstack1ll1l1l1ll_opy_() else bstack11ll11l11l_opy_
      bstack111lll1l_opy_.invoke(bstack1lll1lll_opy_.bstack1l1l1l1lll_opy_, bstack11ll1l1l1_opy_(
        sdk_version=__version__,
        path_config=bstack1l111l11l_opy_(),
        path_project=os.getcwd(),
        test_framework=bstack1l1ll1l1_opy_,
        frameworks=[bstack1l1ll1l1_opy_],
        framework_versions={
          bstack1l1ll1l1_opy_: bstack111111l1_opy_(bstack1ll_opy_ (u"ࠨࡔࡲࡦࡴࡺࠧඦ") if bstack11ll11l11l_opy_ in [bstack1ll_opy_ (u"ࠩࡳࡥࡧࡵࡴࠨට"), bstack1ll_opy_ (u"ࠪࡶࡴࡨ࡯ࡵࠩඨ"), bstack1ll_opy_ (u"ࠫࡷࡵࡢࡰࡶ࠰࡭ࡳࡺࡥࡳࡰࡤࡰࠬඩ")] else bstack11ll11l11l_opy_)
        },
        bs_config=CONFIG
      ))
      if cli.config.get(bstack1ll_opy_ (u"ࠧࡨࡵࡪ࡮ࡧࡍࡩ࡫࡮ࡵ࡫ࡩ࡭ࡪࡸࠢඪ"), None):
        CONFIG[bstack1ll_opy_ (u"ࠨࡢࡶ࡫࡯ࡨࡎࡪࡥ࡯ࡶ࡬ࡪ࡮࡫ࡲࠣණ")] = cli.config.get(bstack1ll_opy_ (u"ࠢࡣࡷ࡬ࡰࡩࡏࡤࡦࡰࡷ࡭࡫࡯ࡥࡳࠤඬ"), None)
    except Exception as e:
      bstack111lll1l_opy_.invoke(bstack1lll1lll_opy_.bstack1ll11111l_opy_, e.__traceback__, 1)
    if bstack11l11l11ll_opy_:
      CONFIG[bstack1ll_opy_ (u"ࠣࡣࡳࡴࠧත")] = cli.config[bstack1ll_opy_ (u"ࠤࡤࡴࡵࠨථ")]
      logger.info(bstack111lllll11_opy_.format(CONFIG[bstack1ll_opy_ (u"ࠪࡥࡵࡶࠧද")]))
  else:
    bstack111lll1l_opy_.clear()
  global bstack1l1l111l1_opy_
  global bstack111lll1l1l_opy_
  if bstack11l111l1_opy_:
    try:
      bstack11l1l1l1ll_opy_ = datetime.datetime.now()
      os.environ[bstack1ll_opy_ (u"ࠫࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡊࡗࡇࡍࡆ࡙ࡒࡖࡐ࠭ධ")] = bstack11ll11l11l_opy_
      bstack111111ll1_opy_(bstack111lll111l_opy_, CONFIG)
      cli.bstack11ll11ll1_opy_(bstack1ll_opy_ (u"ࠧ࡮ࡴࡵࡲ࠽ࡷࡩࡱ࡟ࡵࡧࡶࡸࡤࡧࡴࡵࡧࡰࡴࡹ࡫ࡤࠣන"), datetime.datetime.now() - bstack11l1l1l1ll_opy_)
    except Exception as e:
      logger.debug(bstack1ll1111111_opy_.format(str(e)))
  global bstack11ll1l1lll_opy_
  global bstack1l1111ll1_opy_
  global bstack1l1l11ll1l_opy_
  global bstack111l11l1l_opy_
  global bstack1ll11l1lll_opy_
  global bstack11ll1ll11_opy_
  global bstack11l1ll1111_opy_
  global bstack11ll111ll_opy_
  global bstack11111ll1_opy_
  global bstack1ll11l1l_opy_
  global bstack1l111l111_opy_
  global bstack111ll111l_opy_
  global bstack1l1ll11l1l_opy_
  global bstack11l1ll1ll_opy_
  global bstack1ll11l11l1_opy_
  global bstack1ll11l1111_opy_
  global bstack1l11lll111_opy_
  global bstack1l111l1ll_opy_
  global bstack1llll11ll1_opy_
  global bstack11lll1l111_opy_
  global bstack1ll1l11ll_opy_
  try:
    from selenium import webdriver
    from selenium.webdriver.remote.webdriver import WebDriver
    bstack11ll1l1lll_opy_ = webdriver.Remote.__init__
    bstack1l1111ll1_opy_ = WebDriver.quit
    bstack111ll111l_opy_ = WebDriver.close
    bstack1ll11l11l1_opy_ = WebDriver.get
    bstack1ll1l11ll_opy_ = WebDriver.execute
  except Exception as e:
    pass
  try:
    import Browser
    from subprocess import Popen
    bstack1l1l111l1_opy_ = Popen.__init__
  except Exception as e:
    pass
  try:
    from bstack_utils.helper import bstack1l1111l11_opy_
    bstack111lll1l1l_opy_ = bstack1l1111l11_opy_()
  except Exception as e:
    pass
  try:
    global bstack1lll1llll1_opy_
    from QWeb.keywords import browser
    bstack1lll1llll1_opy_ = browser.close_browser
  except Exception as e:
    pass
  if bstack111l1l11l_opy_(CONFIG) and bstack11ll1l11l1_opy_():
    if bstack11l11111l1_opy_() < version.parse(bstack1l11111ll1_opy_):
      logger.error(bstack11ll11111_opy_.format(bstack11l11111l1_opy_()))
    else:
      try:
        from selenium.webdriver.remote.remote_connection import RemoteConnection
        if hasattr(RemoteConnection, bstack1ll_opy_ (u"࠭࡟ࡨࡧࡷࡣࡵࡸ࡯ࡹࡻࡢࡹࡷࡲࠧ඲")) and callable(getattr(RemoteConnection, bstack1ll_opy_ (u"ࠧࡠࡩࡨࡸࡤࡶࡲࡰࡺࡼࡣࡺࡸ࡬ࠨඳ"))):
          RemoteConnection._get_proxy_url = bstack11ll111ll1_opy_
        else:
          from selenium.webdriver.remote.client_config import ClientConfig
          ClientConfig.get_proxy_url = bstack11ll111ll1_opy_
      except Exception as e:
        logger.error(bstack1ll1111ll_opy_.format(str(e)))
  if not CONFIG.get(bstack1ll_opy_ (u"ࠨࡦ࡬ࡷࡦࡨ࡬ࡦࡃࡸࡸࡴࡉࡡࡱࡶࡸࡶࡪࡒ࡯ࡨࡵࠪප"), False) and not bstack11l111l1_opy_:
    logger.info(bstack1l11llll1l_opy_)
  if not cli.is_enabled(CONFIG):
    if bstack1ll_opy_ (u"ࠩࡷࡹࡷࡨ࡯ࡔࡥࡤࡰࡪ࠭ඵ") in CONFIG and str(CONFIG[bstack1ll_opy_ (u"ࠪࡸࡺࡸࡢࡰࡕࡦࡥࡱ࡫ࠧබ")]).lower() != bstack1ll_opy_ (u"ࠫ࡫ࡧ࡬ࡴࡧࠪභ"):
      bstack1111ll1l_opy_()
    elif bstack11ll11l11l_opy_ != bstack1ll_opy_ (u"ࠬࡶࡹࡵࡪࡲࡲࠬම") or (bstack11ll11l11l_opy_ == bstack1ll_opy_ (u"࠭ࡰࡺࡶ࡫ࡳࡳ࠭ඹ") and not bstack11l111l1_opy_):
      bstack1lllll111l_opy_()
  if (bstack11ll11l11l_opy_ in [bstack1ll_opy_ (u"ࠧࡱࡣࡥࡳࡹ࠭ය"), bstack1ll_opy_ (u"ࠨࡴࡲࡦࡴࡺࠧර"), bstack1ll_opy_ (u"ࠩࡵࡳࡧࡵࡴ࠮࡫ࡱࡸࡪࡸ࡮ࡢ࡮ࠪ඼")]):
    try:
      from robot import run_cli
      from robot.output import Output
      from robot.running.status import TestStatus
      from pabot.pabot import QueueItem
      from pabot import pabot
      try:
        from SeleniumLibrary.keywords.webdrivertools.webdrivertools import WebDriverCreator
        from SeleniumLibrary.keywords.webdrivertools.webdrivertools import WebDriverCache
        WebDriverCreator._get_ff_profile = bstack11l11l1l1_opy_
        bstack11ll1ll11_opy_ = WebDriverCache.close
      except Exception as e:
        logger.warning(bstack1l11111111_opy_ + str(e))
      try:
        from AppiumLibrary.utils.applicationcache import ApplicationCache
        bstack1ll11l1lll_opy_ = ApplicationCache.close
      except Exception as e:
        logger.debug(bstack11l1111l11_opy_ + str(e))
    except Exception as e:
      bstack1llll1ll1_opy_(e, bstack1l11111111_opy_)
    if bstack11ll11l11l_opy_ != bstack1ll_opy_ (u"ࠪࡶࡴࡨ࡯ࡵ࠯࡬ࡲࡹ࡫ࡲ࡯ࡣ࡯ࠫල"):
      bstack1lll1llll_opy_()
    bstack1l1l11ll1l_opy_ = Output.start_test
    bstack111l11l1l_opy_ = Output.end_test
    bstack11l1ll1111_opy_ = TestStatus.__init__
    bstack11111ll1_opy_ = pabot._run
    bstack1ll11l1l_opy_ = QueueItem.__init__
    bstack1l111l111_opy_ = pabot._create_command_for_execution
    bstack1llll11ll1_opy_ = pabot._report_results
  if bstack11ll11l11l_opy_ == bstack1ll_opy_ (u"ࠫࡧ࡫ࡨࡢࡸࡨࠫ඾"):
    try:
      from behave.runner import Runner
      from behave.model import Step
    except Exception as e:
      bstack1llll1ll1_opy_(e, bstack1l11l1l1l1_opy_)
    bstack1l1ll11l1l_opy_ = Runner.run_hook
    bstack11l1ll1ll_opy_ = Step.run
  if bstack11ll11l11l_opy_ == bstack1ll_opy_ (u"ࠬࡶࡹࡵࡧࡶࡸࠬ඿"):
    try:
      from _pytest.config import Config
      bstack1l11lll111_opy_ = Config.getoption
      from _pytest import runner
      bstack1l111l1ll_opy_ = runner._update_current_test_var
    except Exception as e:
      logger.warning(bstack1ll_opy_ (u"ࠨࠥࡴ࠼ࠣࠩࡸࠨව"), bstack1111ll11_opy_, str(e))
    try:
      from pytest_bdd import reporting
      bstack11lll1l111_opy_ = reporting.runtest_makereport
    except Exception as e:
      logger.debug(bstack1ll_opy_ (u"ࠧࡑ࡮ࡨࡥࡸ࡫ࠠࡪࡰࡶࡸࡦࡲ࡬ࠡࡲࡼࡸࡪࡹࡴ࠮ࡤࡧࡨࠥࡺ࡯ࠡࡴࡸࡲࠥࡶࡹࡵࡧࡶࡸ࠲ࡨࡤࡥࠢࡷࡩࡸࡺࡳࠨශ"))
    if bstack1lll1l1l1l_opy_():
      logger.warning(bstack1ll11l11ll_opy_[bstack1ll_opy_ (u"ࠨࡕࡇࡏ࠲ࡍࡅࡏ࠯࠳࠴࠺࠭ෂ")])
  try:
    framework_name = bstack1ll_opy_ (u"ࠩࡵࡳࡧࡵࡴࠨස") if bstack11ll11l11l_opy_ in [bstack1ll_opy_ (u"ࠪࡴࡦࡨ࡯ࡵࠩහ"), bstack1ll_opy_ (u"ࠫࡷࡵࡢࡰࡶࠪළ"), bstack1ll_opy_ (u"ࠬࡸ࡯ࡣࡱࡷ࠱࡮ࡴࡴࡦࡴࡱࡥࡱ࠭ෆ")] else bstack1ll1ll11l1_opy_(bstack11ll11l11l_opy_)
    bstack1l1llll111_opy_ = {
      bstack1ll_opy_ (u"࠭ࡦࡳࡣࡰࡩࡼࡵࡲ࡬ࡡࡱࡥࡲ࡫ࠧ෇"): bstack1ll_opy_ (u"ࠧࡑࡻࡷࡩࡸࡺ࠭ࡤࡷࡦࡹࡲࡨࡥࡳࠩ෈") if bstack11ll11l11l_opy_ == bstack1ll_opy_ (u"ࠨࡲࡼࡸࡪࡹࡴࠨ෉") and bstack1ll1l1l1ll_opy_() else framework_name,
      bstack1ll_opy_ (u"ࠩࡩࡶࡦࡳࡥࡸࡱࡵ࡯ࡤࡼࡥࡳࡵ࡬ࡳࡳ්࠭"): bstack111111l1_opy_(framework_name),
      bstack1ll_opy_ (u"ࠪࡷࡩࡱ࡟ࡷࡧࡵࡷ࡮ࡵ࡮ࠨ෋"): __version__,
      bstack1ll_opy_ (u"ࠫ࡫ࡸࡡ࡮ࡧࡺࡳࡷࡱ࡟ࡶࡵࡨࡨࠬ෌"): bstack11ll11l11l_opy_
    }
    if bstack11ll11l11l_opy_ in bstack11l11lll11_opy_ + bstack1l11l1l111_opy_:
      if bstack1llll1l11_opy_.bstack1l1lll1lll_opy_(CONFIG):
        if bstack1ll_opy_ (u"ࠬࡧࡣࡤࡧࡶࡷ࡮ࡨࡩ࡭࡫ࡷࡽࡔࡶࡴࡪࡱࡱࡷࠬ෍") in CONFIG:
          os.environ[bstack1ll_opy_ (u"࠭ࡂࡓࡑ࡚ࡗࡊࡘࡓࡕࡃࡆࡏࡤ࡚ࡅࡔࡖࡢࡅࡈࡉࡅࡔࡕࡌࡆࡎࡒࡉࡕ࡛ࡢࡇࡔࡔࡆࡊࡉࡘࡖࡆ࡚ࡉࡐࡐࡢ࡝ࡒࡒࠧ෎")] = os.getenv(bstack1ll_opy_ (u"ࠧࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡔࡆࡕࡗࡣࡆࡉࡃࡆࡕࡖࡍࡇࡏࡌࡊࡖ࡜ࡣࡈࡕࡎࡇࡋࡊ࡙ࡗࡇࡔࡊࡑࡑࡣ࡞ࡓࡌࠨා"), json.dumps(CONFIG[bstack1ll_opy_ (u"ࠨࡣࡦࡧࡪࡹࡳࡪࡤ࡬ࡰ࡮ࡺࡹࡐࡲࡷ࡭ࡴࡴࡳࠨැ")]))
          CONFIG[bstack1ll_opy_ (u"ࠩࡤࡧࡨ࡫ࡳࡴ࡫ࡥ࡭ࡱ࡯ࡴࡺࡑࡳࡸ࡮ࡵ࡮ࡴࠩෑ")].pop(bstack1ll_opy_ (u"ࠪ࡭ࡳࡩ࡬ࡶࡦࡨࡘࡦ࡭ࡳࡊࡰࡗࡩࡸࡺࡩ࡯ࡩࡖࡧࡴࡶࡥࠨි"), None)
          CONFIG[bstack1ll_opy_ (u"ࠫࡦࡩࡣࡦࡵࡶ࡭ࡧ࡯࡬ࡪࡶࡼࡓࡵࡺࡩࡰࡰࡶࠫී")].pop(bstack1ll_opy_ (u"ࠬ࡫ࡸࡤ࡮ࡸࡨࡪ࡚ࡡࡨࡵࡌࡲ࡙࡫ࡳࡵ࡫ࡱ࡫ࡘࡩ࡯ࡱࡧࠪු"), None)
        bstack1l1llll111_opy_[bstack1ll_opy_ (u"࠭ࡴࡦࡵࡷࡊࡷࡧ࡭ࡦࡹࡲࡶࡰ࠭෕")] = {
          bstack1ll_opy_ (u"ࠧ࡯ࡣࡰࡩࠬූ"): bstack1ll_opy_ (u"ࠨࡵࡨࡰࡪࡴࡩࡶ࡯ࠪ෗"),
          bstack1ll_opy_ (u"ࠩࡹࡩࡷࡹࡩࡰࡰࠪෘ"): str(bstack11l11111l1_opy_())
        }
    if bstack11ll11l11l_opy_ not in [bstack1ll_opy_ (u"ࠪࡶࡴࡨ࡯ࡵ࠯࡬ࡲࡹ࡫ࡲ࡯ࡣ࡯ࠫෙ")] and not cli.is_running():
      bstack11ll1l1l11_opy_, bstack11lll1ll1l_opy_ = bstack1lll1111l_opy_.launch(CONFIG, bstack1l1llll111_opy_)
      if bstack11lll1ll1l_opy_.get(bstack1ll_opy_ (u"ࠫࡦࡩࡣࡦࡵࡶ࡭ࡧ࡯࡬ࡪࡶࡼࠫේ")) is not None and bstack1llll1l11_opy_.bstack1l1l111lll_opy_(CONFIG) is None:
        value = bstack11lll1ll1l_opy_[bstack1ll_opy_ (u"ࠬࡧࡣࡤࡧࡶࡷ࡮ࡨࡩ࡭࡫ࡷࡽࠬෛ")].get(bstack1ll_opy_ (u"࠭ࡳࡶࡥࡦࡩࡸࡹࠧො"))
        if value is not None:
            CONFIG[bstack1ll_opy_ (u"ࠧࡢࡥࡦࡩࡸࡹࡩࡣ࡫࡯࡭ࡹࡿࠧෝ")] = value
        else:
          logger.debug(bstack1ll_opy_ (u"ࠣࡐࡲࠤࡦࡩࡣࡦࡵࡶ࡭ࡧ࡯࡬ࡪࡶࡼࠤࡩࡧࡴࡢࠢࡩࡳࡺࡴࡤࠡ࡫ࡱࠤࡷ࡫ࡳࡱࡱࡱࡷࡪࠨෞ"))
  except Exception as e:
    logger.debug(bstack1111ll1l1_opy_.format(bstack1ll_opy_ (u"ࠩࡗࡩࡸࡺࡈࡶࡤࠪෟ"), str(e)))
  if bstack11ll11l11l_opy_ == bstack1ll_opy_ (u"ࠪࡴࡾࡺࡨࡰࡰࠪ෠"):
    bstack11lllllll1_opy_ = True
    if bstack11l111l1_opy_ and bstack1l1l11lll1_opy_:
      bstack1l1l1ll1l1_opy_ = CONFIG.get(bstack1ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࡘࡺࡡࡤ࡭ࡏࡳࡨࡧ࡬ࡐࡲࡷ࡭ࡴࡴࡳࠨ෡"), {}).get(bstack1ll_opy_ (u"ࠬࡲ࡯ࡤࡣ࡯ࡍࡩ࡫࡮ࡵ࡫ࡩ࡭ࡪࡸࠧ෢"))
      bstack1l1lllll_opy_(bstack111lll1ll1_opy_)
    elif bstack11l111l1_opy_:
      bstack1l1l1ll1l1_opy_ = CONFIG.get(bstack1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡓࡵࡣࡦ࡯ࡑࡵࡣࡢ࡮ࡒࡴࡹ࡯࡯࡯ࡵࠪ෣"), {}).get(bstack1ll_opy_ (u"ࠧ࡭ࡱࡦࡥࡱࡏࡤࡦࡰࡷ࡭࡫࡯ࡥࡳࠩ෤"))
      global bstack1llll11lll_opy_
      try:
        if bstack1l11lll1l1_opy_(bstack11l111l1_opy_[bstack1ll_opy_ (u"ࠨࡨ࡬ࡰࡪࡥ࡮ࡢ࡯ࡨࠫ෥")]) and multiprocessing.current_process().name == bstack1ll_opy_ (u"ࠩ࠳ࠫ෦"):
          bstack11l111l1_opy_[bstack1ll_opy_ (u"ࠪࡪ࡮ࡲࡥࡠࡰࡤࡱࡪ࠭෧")].remove(bstack1ll_opy_ (u"ࠫ࠲ࡳࠧ෨"))
          bstack11l111l1_opy_[bstack1ll_opy_ (u"ࠬ࡬ࡩ࡭ࡧࡢࡲࡦࡳࡥࠨ෩")].remove(bstack1ll_opy_ (u"࠭ࡰࡥࡤࠪ෪"))
          bstack11l111l1_opy_[bstack1ll_opy_ (u"ࠧࡧ࡫࡯ࡩࡤࡴࡡ࡮ࡧࠪ෫")] = bstack11l111l1_opy_[bstack1ll_opy_ (u"ࠨࡨ࡬ࡰࡪࡥ࡮ࡢ࡯ࡨࠫ෬")][0]
          with open(bstack11l111l1_opy_[bstack1ll_opy_ (u"ࠩࡩ࡭ࡱ࡫࡟࡯ࡣࡰࡩࠬ෭")], bstack1ll_opy_ (u"ࠪࡶࠬ෮")) as f:
            bstack1lll1lll11_opy_ = f.read()
          bstack1lllll11l_opy_ = bstack1ll_opy_ (u"ࠦࠧࠨࡦࡳࡱࡰࠤࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭ࡢࡷࡩࡱࠠࡪ࡯ࡳࡳࡷࡺࠠࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰࡥࡩ࡯࡫ࡷ࡭ࡦࡲࡩࡻࡧ࠾ࠤࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭ࡢ࡭ࡳ࡯ࡴࡪࡣ࡯࡭ࡿ࡫ࠨࡼࡿࠬ࠿ࠥ࡬ࡲࡰ࡯ࠣࡴࡩࡨࠠࡪ࡯ࡳࡳࡷࡺࠠࡑࡦࡥ࠿ࠥࡵࡧࡠࡦࡥࠤࡂࠦࡐࡥࡤ࠱ࡨࡴࡥࡢࡳࡧࡤ࡯ࡀࠐࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࡧࡩ࡫ࠦ࡭ࡰࡦࡢࡦࡷ࡫ࡡ࡬ࠪࡶࡩࡱ࡬ࠬࠡࡣࡵ࡫࠱ࠦࡴࡦ࡯ࡳࡳࡷࡧࡲࡺࠢࡀࠤ࠵࠯࠺ࠋࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࡴࡳࡻ࠽ࠎࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࡦࡸࡧࠡ࠿ࠣࡷࡹࡸࠨࡪࡰࡷࠬࡦࡸࡧࠪ࠭࠴࠴࠮ࠐࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࡪࡾࡣࡦࡲࡷࠤࡊࡾࡣࡦࡲࡷ࡭ࡴࡴࠠࡢࡵࠣࡩ࠿ࠐࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࡰࡢࡵࡶࠎࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࡲ࡫ࡤࡪࡢࠩࡵࡨࡰ࡫࠲ࡡࡳࡩ࠯ࡸࡪࡳࡰࡰࡴࡤࡶࡾ࠯ࠊࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࡔࡩࡨ࠮ࡥࡱࡢࡦࠥࡃࠠ࡮ࡱࡧࡣࡧࡸࡥࡢ࡭ࠍࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࡐࡥࡤ࠱ࡨࡴࡥࡢࡳࡧࡤ࡯ࠥࡃࠠ࡮ࡱࡧࡣࡧࡸࡥࡢ࡭ࠍࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࡐࡥࡤࠫ࠭࠳ࡹࡥࡵࡡࡷࡶࡦࡩࡥࠩࠫ࡟ࡲࠧࠨࠢ෯").format(str(bstack11l111l1_opy_))
          bstack1ll111ll1l_opy_ = bstack1lllll11l_opy_ + bstack1lll1lll11_opy_
          bstack11l111l11_opy_ = bstack11l111l1_opy_[bstack1ll_opy_ (u"ࠬ࡬ࡩ࡭ࡧࡢࡲࡦࡳࡥࠨ෰")] + bstack1ll_opy_ (u"࠭࡟ࡣࡵࡷࡥࡨࡱ࡟ࡵࡧࡰࡴ࠳ࡶࡹࠨ෱")
          with open(bstack11l111l11_opy_, bstack1ll_opy_ (u"ࠧࡸࠩෲ")):
            pass
          with open(bstack11l111l11_opy_, bstack1ll_opy_ (u"ࠣࡹ࠮ࠦෳ")) as f:
            f.write(bstack1ll111ll1l_opy_)
          import subprocess
          bstack11111l11_opy_ = subprocess.run([bstack1ll_opy_ (u"ࠤࡳࡽࡹ࡮࡯࡯ࠤ෴"), bstack11l111l11_opy_])
          if os.path.exists(bstack11l111l11_opy_):
            os.unlink(bstack11l111l11_opy_)
          os._exit(bstack11111l11_opy_.returncode)
        else:
          if bstack1l11lll1l1_opy_(bstack11l111l1_opy_[bstack1ll_opy_ (u"ࠪࡪ࡮ࡲࡥࡠࡰࡤࡱࡪ࠭෵")]):
            bstack11l111l1_opy_[bstack1ll_opy_ (u"ࠫ࡫࡯࡬ࡦࡡࡱࡥࡲ࡫ࠧ෶")].remove(bstack1ll_opy_ (u"ࠬ࠳࡭ࠨ෷"))
            bstack11l111l1_opy_[bstack1ll_opy_ (u"࠭ࡦࡪ࡮ࡨࡣࡳࡧ࡭ࡦࠩ෸")].remove(bstack1ll_opy_ (u"ࠧࡱࡦࡥࠫ෹"))
            bstack11l111l1_opy_[bstack1ll_opy_ (u"ࠨࡨ࡬ࡰࡪࡥ࡮ࡢ࡯ࡨࠫ෺")] = bstack11l111l1_opy_[bstack1ll_opy_ (u"ࠩࡩ࡭ࡱ࡫࡟࡯ࡣࡰࡩࠬ෻")][0]
          bstack1l1lllll_opy_(bstack111lll1ll1_opy_)
          sys.path.append(os.path.dirname(os.path.abspath(bstack11l111l1_opy_[bstack1ll_opy_ (u"ࠪࡪ࡮ࡲࡥࡠࡰࡤࡱࡪ࠭෼")])))
          sys.argv = sys.argv[2:]
          mod_globals = globals()
          mod_globals[bstack1ll_opy_ (u"ࠫࡤࡥ࡮ࡢ࡯ࡨࡣࡤ࠭෽")] = bstack1ll_opy_ (u"ࠬࡥ࡟࡮ࡣ࡬ࡲࡤࡥࠧ෾")
          mod_globals[bstack1ll_opy_ (u"࠭࡟ࡠࡨ࡬ࡰࡪࡥ࡟ࠨ෿")] = os.path.abspath(bstack11l111l1_opy_[bstack1ll_opy_ (u"ࠧࡧ࡫࡯ࡩࡤࡴࡡ࡮ࡧࠪ฀")])
          exec(open(bstack11l111l1_opy_[bstack1ll_opy_ (u"ࠨࡨ࡬ࡰࡪࡥ࡮ࡢ࡯ࡨࠫก")]).read(), mod_globals)
      except BaseException as e:
        try:
          traceback.print_exc()
          logger.error(bstack1ll_opy_ (u"ࠩࡆࡥࡺ࡭ࡨࡵࠢࡈࡼࡨ࡫ࡰࡵ࡫ࡲࡲ࠿ࠦࡻࡾࠩข").format(str(e)))
          for driver in bstack1llll11lll_opy_:
            bstack1lll1l11l_opy_.append({
              bstack1ll_opy_ (u"ࠪࡲࡦࡳࡥࠨฃ"): bstack11l111l1_opy_[bstack1ll_opy_ (u"ࠫ࡫࡯࡬ࡦࡡࡱࡥࡲ࡫ࠧค")],
              bstack1ll_opy_ (u"ࠬ࡫ࡲࡳࡱࡵࠫฅ"): str(e),
              bstack1ll_opy_ (u"࠭ࡩ࡯ࡦࡨࡼࠬฆ"): multiprocessing.current_process().name
            })
            bstack11ll11111l_opy_(driver, bstack1ll_opy_ (u"ࠧࡧࡣ࡬ࡰࡪࡪࠧง"), bstack1ll_opy_ (u"ࠣࡕࡨࡷࡸ࡯࡯࡯ࠢࡩࡥ࡮ࡲࡥࡥࠢࡺ࡭ࡹ࡮࠺ࠡ࡞ࡱࠦจ") + str(e))
        except Exception:
          pass
      finally:
        try:
          for driver in bstack1llll11lll_opy_:
            driver.quit()
        except Exception as e:
          pass
    else:
      percy.init(bstack11l11l11ll_opy_, CONFIG, logger)
      bstack1ll1l1l11_opy_()
      bstack1lll11llll_opy_()
      percy.bstack11ll1llll_opy_()
      bstack1l1ll1l11_opy_ = {
        bstack1ll_opy_ (u"ࠩࡩ࡭ࡱ࡫࡟࡯ࡣࡰࡩࠬฉ"): args[0],
        bstack1ll_opy_ (u"ࠪࡇࡔࡔࡆࡊࡉࠪช"): CONFIG,
        bstack1ll_opy_ (u"ࠫࡍ࡛ࡂࡠࡗࡕࡐࠬซ"): bstack1ll111lll_opy_,
        bstack1ll_opy_ (u"ࠬࡏࡓࡠࡃࡓࡔࡤࡇࡕࡕࡑࡐࡅ࡙ࡋࠧฌ"): bstack11l11l11ll_opy_
      }
      if bstack1ll_opy_ (u"࠭ࡰ࡭ࡣࡷࡪࡴࡸ࡭ࡴࠩญ") in CONFIG:
        bstack1llll1l11l_opy_ = bstack1l1lll111l_opy_(args, logger, CONFIG, bstack11l111llll_opy_, bstack11l1lll1l1_opy_)
        bstack1lll11ll_opy_ = bstack1llll1l11l_opy_.bstack1lll1ll1ll_opy_(run_on_browserstack, bstack1l1ll1l11_opy_, bstack1l11lll1l1_opy_(args))
      else:
        if bstack1l11lll1l1_opy_(args):
          bstack1l1ll1l11_opy_[bstack1ll_opy_ (u"ࠧࡧ࡫࡯ࡩࡤࡴࡡ࡮ࡧࠪฎ")] = args
          test = multiprocessing.Process(name=str(0),
                                         target=run_on_browserstack, args=(bstack1l1ll1l11_opy_,))
          test.start()
          test.join()
        else:
          bstack1l1lllll_opy_(bstack111lll1ll1_opy_)
          sys.path.append(os.path.dirname(os.path.abspath(args[0])))
          mod_globals = globals()
          mod_globals[bstack1ll_opy_ (u"ࠨࡡࡢࡲࡦࡳࡥࡠࡡࠪฏ")] = bstack1ll_opy_ (u"ࠩࡢࡣࡲࡧࡩ࡯ࡡࡢࠫฐ")
          mod_globals[bstack1ll_opy_ (u"ࠪࡣࡤ࡬ࡩ࡭ࡧࡢࡣࠬฑ")] = os.path.abspath(args[0])
          sys.argv = sys.argv[2:]
          exec(open(args[0]).read(), mod_globals)
  elif bstack11ll11l11l_opy_ == bstack1ll_opy_ (u"ࠫࡵࡧࡢࡰࡶࠪฒ") or bstack11ll11l11l_opy_ == bstack1ll_opy_ (u"ࠬࡸ࡯ࡣࡱࡷࠫณ"):
    percy.init(bstack11l11l11ll_opy_, CONFIG, logger)
    percy.bstack11ll1llll_opy_()
    try:
      from pabot import pabot
    except Exception as e:
      bstack1llll1ll1_opy_(e, bstack1l11111111_opy_)
    bstack1ll1l1l11_opy_()
    bstack1l1lllll_opy_(bstack1l11l1l11l_opy_)
    if bstack11l111llll_opy_:
      bstack1l1llll1l1_opy_(bstack1l11l1l11l_opy_, args)
      if bstack1ll_opy_ (u"࠭࠭࠮ࡲࡵࡳࡨ࡫ࡳࡴࡧࡶࠫด") in args:
        i = args.index(bstack1ll_opy_ (u"ࠧ࠮࠯ࡳࡶࡴࡩࡥࡴࡵࡨࡷࠬต"))
        args.pop(i)
        args.pop(i)
      if bstack1ll_opy_ (u"ࠨࡲ࡯ࡥࡹ࡬࡯ࡳ࡯ࡶࠫถ") not in CONFIG:
        CONFIG[bstack1ll_opy_ (u"ࠩࡳࡰࡦࡺࡦࡰࡴࡰࡷࠬท")] = [{}]
        bstack11l1lll1l1_opy_ = 1
      if bstack1ll111lll1_opy_ == 0:
        bstack1ll111lll1_opy_ = 1
      args.insert(0, str(bstack1ll111lll1_opy_))
      args.insert(0, str(bstack1ll_opy_ (u"ࠪ࠱࠲ࡶࡲࡰࡥࡨࡷࡸ࡫ࡳࠨธ")))
    if bstack1lll1111l_opy_.on():
      try:
        from robot.run import USAGE
        from robot.utils import ArgumentParser
        from pabot.arguments import _parse_pabot_args
        bstack11lllll11_opy_, pabot_args = _parse_pabot_args(args)
        opts, bstack1lllll11ll_opy_ = ArgumentParser(
            USAGE,
            auto_pythonpath=False,
            auto_argumentfile=True,
            env_options=bstack1ll_opy_ (u"ࠦࡗࡕࡂࡐࡖࡢࡓࡕ࡚ࡉࡐࡐࡖࠦน"),
        ).parse_args(bstack11lllll11_opy_)
        bstack1l1ll1lll1_opy_ = args.index(bstack11lllll11_opy_[0]) if len(bstack11lllll11_opy_) > 0 else len(args)
        args.insert(bstack1l1ll1lll1_opy_, str(bstack1ll_opy_ (u"ࠬ࠳࠭࡭࡫ࡶࡸࡪࡴࡥࡳࠩบ")))
        args.insert(bstack1l1ll1lll1_opy_ + 1, str(os.path.join(os.path.dirname(os.path.realpath(__file__)), bstack1ll_opy_ (u"࠭ࡢࡴࡶࡤࡧࡰࡥࡲࡰࡤࡲࡸࡤࡲࡩࡴࡶࡨࡲࡪࡸ࠮ࡱࡻࠪป"))))
        if bstack11llll11l1_opy_.bstack111l1l111_opy_(CONFIG):
          args.insert(bstack1l1ll1lll1_opy_, str(bstack1ll_opy_ (u"ࠧ࠮࠯࡯࡭ࡸࡺࡥ࡯ࡧࡵࠫผ")))
          args.insert(bstack1l1ll1lll1_opy_ + 1, str(bstack1ll_opy_ (u"ࠨࡔࡨࡸࡷࡿࡆࡢ࡫࡯ࡩࡩࡀࡻࡾࠩฝ").format(bstack11llll11l1_opy_.bstack1lll1l11ll_opy_(CONFIG))))
        if bstack11l11lllll_opy_(os.environ.get(bstack1ll_opy_ (u"ࠩࡅࡖࡔ࡝ࡓࡆࡔࡖࡘࡆࡉࡋࡠࡔࡈࡖ࡚ࡔࠧพ"))) and str(os.environ.get(bstack1ll_opy_ (u"ࠪࡆࡗࡕࡗࡔࡇࡕࡗ࡙ࡇࡃࡌࡡࡕࡉࡗ࡛ࡎࡠࡖࡈࡗ࡙࡙ࠧฟ"), bstack1ll_opy_ (u"ࠫࡳࡻ࡬࡭ࠩภ"))) != bstack1ll_opy_ (u"ࠬࡴࡵ࡭࡮ࠪม"):
          for bstack111llllll1_opy_ in bstack1lllll11ll_opy_:
            args.remove(bstack111llllll1_opy_)
          test_files = os.environ.get(bstack1ll_opy_ (u"࠭ࡂࡓࡑ࡚ࡗࡊࡘࡓࡕࡃࡆࡏࡤࡘࡅࡓࡗࡑࡣ࡙ࡋࡓࡕࡕࠪย")).split(bstack1ll_opy_ (u"ࠧ࠭ࠩร"))
          for bstack1ll1l1111_opy_ in test_files:
            args.append(bstack1ll1l1111_opy_)
      except Exception as e:
        logger.error(bstack1ll_opy_ (u"ࠣࡇࡵࡶࡴࡸࠠࡸࡪ࡬ࡰࡪࠦࡡࡵࡶࡤࡧ࡭࡯࡮ࡨࠢ࡯࡭ࡸࡺࡥ࡯ࡧࡵࠤ࡫ࡵࡲࠡࡽࢀ࠲ࠥࡋࡲࡳࡱࡵࠤ࠲ࠦࡻࡾࠤฤ").format(bstack11llllll11_opy_, e))
    pabot.main(args)
  elif bstack11ll11l11l_opy_ == bstack1ll_opy_ (u"ࠩࡵࡳࡧࡵࡴ࠮࡫ࡱࡸࡪࡸ࡮ࡢ࡮ࠪล"):
    try:
      from robot import run_cli
    except Exception as e:
      bstack1llll1ll1_opy_(e, bstack1l11111111_opy_)
    for a in args:
      if bstack1ll_opy_ (u"ࠪࡆࡘ࡚ࡁࡄࡍࡓࡐࡆ࡚ࡆࡐࡔࡐࡍࡓࡊࡅ࡙ࠩฦ") in a:
        bstack11l1l111l_opy_ = int(a.split(bstack1ll_opy_ (u"ࠫ࠿࠭ว"))[1])
      if bstack1ll_opy_ (u"ࠬࡈࡓࡕࡃࡆࡏࡉࡋࡆࡍࡑࡆࡅࡑࡏࡄࡆࡐࡗࡍࡋࡏࡅࡓࠩศ") in a:
        bstack1l1l1ll1l1_opy_ = str(a.split(bstack1ll_opy_ (u"࠭࠺ࠨษ"))[1])
      if bstack1ll_opy_ (u"ࠧࡃࡕࡗࡅࡈࡑࡃࡍࡋࡄࡖࡌ࡙ࠧส") in a:
        bstack111l11l11_opy_ = str(a.split(bstack1ll_opy_ (u"ࠨ࠼ࠪห"))[1])
    bstack1ll111111_opy_ = None
    bstack1lll1l11_opy_ = None
    if bstack1ll_opy_ (u"ࠩ࠰࠱ࡧࡹࡴࡢࡥ࡮ࡣ࡮ࡺࡥ࡮ࡡ࡬ࡲࡩ࡫ࡸࠨฬ") in args:
      i = args.index(bstack1ll_opy_ (u"ࠪ࠱࠲ࡨࡳࡵࡣࡦ࡯ࡤ࡯ࡴࡦ࡯ࡢ࡭ࡳࡪࡥࡹࠩอ"))
      args.pop(i)
      bstack1ll111111_opy_ = args.pop(i)
    if bstack1ll_opy_ (u"ࠫ࠲࠳ࡢࡴࡶࡤࡧࡰࡥࡰ࡭ࡣࡷࡪࡴࡸ࡭ࡠ࡫ࡱࡨࡪࡾࠧฮ") in args:
      i = args.index(bstack1ll_opy_ (u"ࠬ࠳࠭ࡣࡵࡷࡥࡨࡱ࡟ࡱ࡮ࡤࡸ࡫ࡵࡲ࡮ࡡ࡬ࡲࡩ࡫ࡸࠨฯ"))
      args.pop(i)
      bstack1lll1l11_opy_ = args.pop(i)
    if bstack1ll111111_opy_ is not None:
      global bstack1l1l1l1l1l_opy_
      bstack1l1l1l1l1l_opy_ = bstack1ll111111_opy_
    if bstack1lll1l11_opy_ is not None and int(bstack11l1l111l_opy_) < 0:
      bstack11l1l111l_opy_ = int(bstack1lll1l11_opy_)
    bstack1l1lllll_opy_(bstack1l11l1l11l_opy_)
    run_cli(args)
    if bstack1ll_opy_ (u"࠭ࡢࡴࡶࡤࡧࡰࡥࡥࡳࡴࡲࡶࡤࡲࡩࡴࡶࠪะ") in multiprocessing.current_process().__dict__.keys():
      for bstack11l1l1ll1_opy_ in multiprocessing.current_process().bstack_error_list:
        bstack1lll1l11l_opy_.append(bstack11l1l1ll1_opy_)
  elif bstack11ll11l11l_opy_ == bstack1ll_opy_ (u"ࠧࡱࡻࡷࡩࡸࡺࠧั"):
    bstack1lll11ll1_opy_ = bstack1l111ll1l_opy_(args, logger, CONFIG, bstack11l111llll_opy_)
    bstack1lll11ll1_opy_.bstack1lll1l111_opy_()
    bstack1ll1l1l11_opy_()
    bstack11l1l1111l_opy_ = True
    bstack1lll111111_opy_ = bstack1lll11ll1_opy_.bstack11ll1lll_opy_()
    bstack1lll11ll1_opy_.bstack1l1ll1l11_opy_(bstack1111l11ll_opy_)
    bstack1lll11ll1_opy_.bstack11ll1ll11l_opy_()
    bstack1lll1111l1_opy_(bstack11ll11l11l_opy_, CONFIG, bstack1lll11ll1_opy_.bstack1l1ll11111_opy_())
    bstack1ll1lllll1_opy_ = bstack1lll11ll1_opy_.bstack1lll1ll1ll_opy_(bstack1l1llllll1_opy_, {
      bstack1ll_opy_ (u"ࠨࡊࡘࡆࡤ࡛ࡒࡍࠩา"): bstack1ll111lll_opy_,
      bstack1ll_opy_ (u"ࠩࡌࡗࡤࡇࡐࡑࡡࡄ࡙࡙ࡕࡍࡂࡖࡈࠫำ"): bstack11l11l11ll_opy_,
      bstack1ll_opy_ (u"ࠪࡆࡗࡕࡗࡔࡇࡕࡗ࡙ࡇࡃࡌࡡࡄ࡙࡙ࡕࡍࡂࡖࡌࡓࡓ࠭ิ"): bstack11l111llll_opy_
    })
    try:
      bstack11lll111l_opy_, bstack1l1l11111l_opy_ = map(list, zip(*bstack1ll1lllll1_opy_))
      bstack1111ll11l_opy_ = bstack11lll111l_opy_[0]
      for status_code in bstack1l1l11111l_opy_:
        if status_code != 0:
          bstack1llll1ll11_opy_ = status_code
          break
    except Exception as e:
      logger.debug(bstack1ll_opy_ (u"࡚ࠦࡴࡡࡣ࡮ࡨࠤࡹࡵࠠࡴࡣࡹࡩࠥ࡫ࡲࡳࡱࡵࡷࠥࡧ࡮ࡥࠢࡶࡸࡦࡺࡵࡴࠢࡦࡳࡩ࡫࠮ࠡࡇࡻࡧࡪࡶࡴࡪࡱࡱࠤ࠿ࠦࡻࡾࠤี").format(str(e)))
  elif bstack11ll11l11l_opy_ == bstack1ll_opy_ (u"ࠬࡨࡥࡩࡣࡹࡩࠬึ"):
    try:
      from behave.__main__ import main as bstack1ll1111lll_opy_
      from behave.configuration import Configuration
    except Exception as e:
      bstack1llll1ll1_opy_(e, bstack1l11l1l1l1_opy_)
    bstack1ll1l1l11_opy_()
    bstack11l1l1111l_opy_ = True
    bstack111lll1lll_opy_ = 1
    if bstack1ll_opy_ (u"࠭ࡰࡢࡴࡤࡰࡱ࡫࡬ࡴࡒࡨࡶࡕࡲࡡࡵࡨࡲࡶࡲ࠭ื") in CONFIG:
      bstack111lll1lll_opy_ = CONFIG[bstack1ll_opy_ (u"ࠧࡱࡣࡵࡥࡱࡲࡥ࡭ࡵࡓࡩࡷࡖ࡬ࡢࡶࡩࡳࡷࡳุࠧ")]
    if bstack1ll_opy_ (u"ࠨࡲ࡯ࡥࡹ࡬࡯ࡳ࡯ࡶูࠫ") in CONFIG:
      bstack11l1llll1l_opy_ = int(bstack111lll1lll_opy_) * int(len(CONFIG[bstack1ll_opy_ (u"ࠩࡳࡰࡦࡺࡦࡰࡴࡰࡷฺࠬ")]))
    else:
      bstack11l1llll1l_opy_ = int(bstack111lll1lll_opy_)
    config = Configuration(args)
    bstack11ll1ll1l_opy_ = config.paths
    if len(bstack11ll1ll1l_opy_) == 0:
      import glob
      pattern = bstack1ll_opy_ (u"ࠪ࠮࠯࠵ࠪ࠯ࡨࡨࡥࡹࡻࡲࡦࠩ฻")
      bstack111l1111l_opy_ = glob.glob(pattern, recursive=True)
      args.extend(bstack111l1111l_opy_)
      config = Configuration(args)
      bstack11ll1ll1l_opy_ = config.paths
    bstack1ll11l111_opy_ = [os.path.normpath(item) for item in bstack11ll1ll1l_opy_]
    bstack11ll1ll1ll_opy_ = [os.path.normpath(item) for item in args]
    bstack1l111l11_opy_ = [item for item in bstack11ll1ll1ll_opy_ if item not in bstack1ll11l111_opy_]
    import platform as pf
    if pf.system().lower() == bstack1ll_opy_ (u"ࠫࡼ࡯࡮ࡥࡱࡺࡷࠬ฼"):
      from pathlib import PureWindowsPath, PurePosixPath
      bstack1ll11l111_opy_ = [str(PurePosixPath(PureWindowsPath(bstack1ll111ll11_opy_)))
                    for bstack1ll111ll11_opy_ in bstack1ll11l111_opy_]
    bstack1l1ll111ll_opy_ = []
    for spec in bstack1ll11l111_opy_:
      bstack1l1l1llll1_opy_ = []
      bstack1l1l1llll1_opy_ += bstack1l111l11_opy_
      bstack1l1l1llll1_opy_.append(spec)
      bstack1l1ll111ll_opy_.append(bstack1l1l1llll1_opy_)
    execution_items = []
    for bstack1l1l1llll1_opy_ in bstack1l1ll111ll_opy_:
      if bstack1ll_opy_ (u"ࠬࡶ࡬ࡢࡶࡩࡳࡷࡳࡳࠨ฽") in CONFIG:
        for index, _ in enumerate(CONFIG[bstack1ll_opy_ (u"࠭ࡰ࡭ࡣࡷࡪࡴࡸ࡭ࡴࠩ฾")]):
          item = {}
          item[bstack1ll_opy_ (u"ࠧࡢࡴࡪࠫ฿")] = bstack1ll_opy_ (u"ࠨࠢࠪเ").join(bstack1l1l1llll1_opy_)
          item[bstack1ll_opy_ (u"ࠩ࡬ࡲࡩ࡫ࡸࠨแ")] = index
          execution_items.append(item)
      else:
        item = {}
        item[bstack1ll_opy_ (u"ࠪࡥࡷ࡭ࠧโ")] = bstack1ll_opy_ (u"ࠫࠥ࠭ใ").join(bstack1l1l1llll1_opy_)
        item[bstack1ll_opy_ (u"ࠬ࡯࡮ࡥࡧࡻࠫไ")] = 0
        execution_items.append(item)
    bstack1l111ll11_opy_ = bstack1l1l11l11l_opy_(execution_items, bstack11l1llll1l_opy_)
    for execution_item in bstack1l111ll11_opy_:
      bstack111llll1_opy_ = []
      for item in execution_item:
        bstack111llll1_opy_.append(bstack111ll1l1l_opy_(name=str(item[bstack1ll_opy_ (u"࠭ࡩ࡯ࡦࡨࡼࠬๅ")]),
                                             target=bstack11ll11l1l1_opy_,
                                             args=(item[bstack1ll_opy_ (u"ࠧࡢࡴࡪࠫๆ")],)))
      for t in bstack111llll1_opy_:
        t.start()
      for t in bstack111llll1_opy_:
        t.join()
  else:
    bstack1ll1l1lll_opy_(bstack1ll1ll111_opy_)
  if not bstack11l111l1_opy_:
    bstack1lllll111_opy_()
    if(bstack11ll11l11l_opy_ in [bstack1ll_opy_ (u"ࠨࡤࡨ࡬ࡦࡼࡥࠨ็"), bstack1ll_opy_ (u"ࠩࡳࡽࡹ࡫ࡳࡵ่ࠩ")]):
      bstack1lll1l1l_opy_()
  bstack11l1l1lll1_opy_.bstack1l11l1l1ll_opy_()
def browserstack_initialize(bstack111lll1l11_opy_=None):
  logger.info(bstack1ll_opy_ (u"ࠪࡖࡺࡴ࡮ࡪࡰࡪࠤࡘࡊࡋࠡࡹ࡬ࡸ࡭ࠦࡡࡳࡩࡶ࠾้ࠥ࠭") + str(bstack111lll1l11_opy_))
  run_on_browserstack(bstack111lll1l11_opy_, None, True)
@measure(event_name=EVENTS.bstack1l111ll1ll_opy_, stage=STAGE.bstack1l1lll1ll1_opy_, bstack1l1l11ll_opy_=bstack1llll1111l_opy_)
def bstack1lllll111_opy_():
  global CONFIG
  global bstack1l1lll1l1_opy_
  global bstack1llll1ll11_opy_
  global bstack1ll11l11_opy_
  global bstack1ll1l1l111_opy_
  bstack1l11l11ll_opy_.bstack11l1l1ll_opy_()
  if cli.is_running():
    bstack111lll1l_opy_.invoke(bstack1lll1lll_opy_.bstack11llll1ll_opy_)
  else:
    bstack1l11l1lll_opy_ = bstack11llll11l1_opy_.bstack11lll1111_opy_(config=CONFIG)
    bstack1l11l1lll_opy_.bstack1l1lll1l11_opy_(CONFIG)
  if bstack1l1lll1l1_opy_ == bstack1ll_opy_ (u"ࠫࡵࡿࡴࡦࡵࡷ๊ࠫ"):
    if not cli.is_enabled(CONFIG):
      bstack1lll1111l_opy_.stop()
  else:
    bstack1lll1111l_opy_.stop()
  if not cli.is_enabled(CONFIG):
    bstack1l11111lll_opy_.bstack111111lll_opy_()
  if bstack1ll_opy_ (u"ࠬࡺࡵࡳࡤࡲࡗࡨࡧ࡬ࡦ๋ࠩ") in CONFIG and str(CONFIG[bstack1ll_opy_ (u"࠭ࡴࡶࡴࡥࡳࡘࡩࡡ࡭ࡧࠪ์")]).lower() != bstack1ll_opy_ (u"ࠧࡧࡣ࡯ࡷࡪ࠭ํ"):
    hashed_id, bstack1l111lll1_opy_ = bstack11l1l1l111_opy_()
  else:
    hashed_id, bstack1l111lll1_opy_ = get_build_link()
  bstack111lll11_opy_(hashed_id)
  logger.info(bstack1ll_opy_ (u"ࠨࡕࡇࡏࠥࡸࡵ࡯ࠢࡨࡲࡩ࡫ࡤࠡࡨࡲࡶࠥ࡯ࡤ࠻ࠩ๎") + bstack1ll1l1l111_opy_.get_property(bstack1ll_opy_ (u"ࠩࡶࡨࡰࡘࡵ࡯ࡋࡧࠫ๏"), bstack1ll_opy_ (u"ࠪࠫ๐")) + bstack1ll_opy_ (u"ࠫ࠱ࠦࡴࡦࡵࡷ࡬ࡺࡨࠠࡪࡦ࠽ࠤࠬ๑") + os.getenv(bstack1ll_opy_ (u"ࠬࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣ࡙ࡋࡓࡕࡊࡘࡆࡤ࡛ࡕࡊࡆࠪ๒"), bstack1ll_opy_ (u"࠭ࠧ๓")))
  if hashed_id is not None and bstack11l1ll111_opy_() != -1:
    sessions = bstack11ll1l1111_opy_(hashed_id)
    bstack11l11llll_opy_(sessions, bstack1l111lll1_opy_)
  if bstack1l1lll1l1_opy_ == bstack1ll_opy_ (u"ࠧࡱࡻࡷࡩࡸࡺࠧ๔") and bstack1llll1ll11_opy_ != 0:
    sys.exit(bstack1llll1ll11_opy_)
  if bstack1l1lll1l1_opy_ == bstack1ll_opy_ (u"ࠨࡤࡨ࡬ࡦࡼࡥࠨ๕") and bstack1ll11l11_opy_ != 0:
    sys.exit(bstack1ll11l11_opy_)
def bstack111lll11_opy_(new_id):
    global bstack1ll11l111l_opy_
    bstack1ll11l111l_opy_ = new_id
def bstack1ll1ll11l1_opy_(bstack1ll111l1l1_opy_):
  if bstack1ll111l1l1_opy_:
    return bstack1ll111l1l1_opy_.capitalize()
  else:
    return bstack1ll_opy_ (u"ࠩࠪ๖")
@measure(event_name=EVENTS.bstack111l1ll1l_opy_, stage=STAGE.bstack1l1lll1ll1_opy_, bstack1l1l11ll_opy_=bstack1llll1111l_opy_)
def bstack1ll1ll11ll_opy_(bstack1l1ll11ll1_opy_):
  if bstack1ll_opy_ (u"ࠪࡲࡦࡳࡥࠨ๗") in bstack1l1ll11ll1_opy_ and bstack1l1ll11ll1_opy_[bstack1ll_opy_ (u"ࠫࡳࡧ࡭ࡦࠩ๘")] != bstack1ll_opy_ (u"ࠬ࠭๙"):
    return bstack1l1ll11ll1_opy_[bstack1ll_opy_ (u"࠭࡮ࡢ࡯ࡨࠫ๚")]
  else:
    bstack1l1l11ll_opy_ = bstack1ll_opy_ (u"ࠢࠣ๛")
    if bstack1ll_opy_ (u"ࠨࡦࡨࡺ࡮ࡩࡥࠨ๜") in bstack1l1ll11ll1_opy_ and bstack1l1ll11ll1_opy_[bstack1ll_opy_ (u"ࠩࡧࡩࡻ࡯ࡣࡦࠩ๝")] != None:
      bstack1l1l11ll_opy_ += bstack1l1ll11ll1_opy_[bstack1ll_opy_ (u"ࠪࡨࡪࡼࡩࡤࡧࠪ๞")] + bstack1ll_opy_ (u"ࠦ࠱ࠦࠢ๟")
      if bstack1l1ll11ll1_opy_[bstack1ll_opy_ (u"ࠬࡵࡳࠨ๠")] == bstack1ll_opy_ (u"ࠨࡩࡰࡵࠥ๡"):
        bstack1l1l11ll_opy_ += bstack1ll_opy_ (u"ࠢࡪࡑࡖࠤࠧ๢")
      bstack1l1l11ll_opy_ += (bstack1l1ll11ll1_opy_[bstack1ll_opy_ (u"ࠨࡱࡶࡣࡻ࡫ࡲࡴ࡫ࡲࡲࠬ๣")] or bstack1ll_opy_ (u"ࠩࠪ๤"))
      return bstack1l1l11ll_opy_
    else:
      bstack1l1l11ll_opy_ += bstack1ll1ll11l1_opy_(bstack1l1ll11ll1_opy_[bstack1ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵࠫ๥")]) + bstack1ll_opy_ (u"ࠦࠥࠨ๦") + (
              bstack1l1ll11ll1_opy_[bstack1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡥࡶࡦࡴࡶ࡭ࡴࡴࠧ๧")] or bstack1ll_opy_ (u"࠭ࠧ๨")) + bstack1ll_opy_ (u"ࠢ࠭ࠢࠥ๩")
      if bstack1l1ll11ll1_opy_[bstack1ll_opy_ (u"ࠨࡱࡶࠫ๪")] == bstack1ll_opy_ (u"ࠤ࡚࡭ࡳࡪ࡯ࡸࡵࠥ๫"):
        bstack1l1l11ll_opy_ += bstack1ll_opy_ (u"࡛ࠥ࡮ࡴࠠࠣ๬")
      bstack1l1l11ll_opy_ += bstack1l1ll11ll1_opy_[bstack1ll_opy_ (u"ࠫࡴࡹ࡟ࡷࡧࡵࡷ࡮ࡵ࡮ࠨ๭")] or bstack1ll_opy_ (u"ࠬ࠭๮")
      return bstack1l1l11ll_opy_
@measure(event_name=EVENTS.bstack11ll1ll1l1_opy_, stage=STAGE.bstack1l1lll1ll1_opy_, bstack1l1l11ll_opy_=bstack1llll1111l_opy_)
def bstack11l11l1l1l_opy_(bstack11l1ll11ll_opy_):
  if bstack11l1ll11ll_opy_ == bstack1ll_opy_ (u"ࠨࡤࡰࡰࡨࠦ๯"):
    return bstack1ll_opy_ (u"ࠧ࠽ࡶࡧࠤࡨࡲࡡࡴࡵࡀࠦࡧࡹࡴࡢࡥ࡮࠱ࡩࡧࡴࡢࠤࠣࡷࡹࡿ࡬ࡦ࠿ࠥࡧࡴࡲ࡯ࡳ࠼ࡪࡶࡪ࡫࡮࠼ࠤࡁࡀ࡫ࡵ࡮ࡵࠢࡦࡳࡱࡵࡲ࠾ࠤࡪࡶࡪ࡫࡮ࠣࡀࡆࡳࡲࡶ࡬ࡦࡶࡨࡨࡁ࠵ࡦࡰࡰࡷࡂࡁ࠵ࡴࡥࡀࠪ๰")
  elif bstack11l1ll11ll_opy_ == bstack1ll_opy_ (u"ࠣࡨࡤ࡭ࡱ࡫ࡤࠣ๱"):
    return bstack1ll_opy_ (u"ࠩ࠿ࡸࡩࠦࡣ࡭ࡣࡶࡷࡂࠨࡢࡴࡶࡤࡧࡰ࠳ࡤࡢࡶࡤࠦࠥࡹࡴࡺ࡮ࡨࡁࠧࡩ࡯࡭ࡱࡵ࠾ࡷ࡫ࡤ࠼ࠤࡁࡀ࡫ࡵ࡮ࡵࠢࡦࡳࡱࡵࡲ࠾ࠤࡵࡩࡩࠨ࠾ࡇࡣ࡬ࡰࡪࡪ࠼࠰ࡨࡲࡲࡹࡄ࠼࠰ࡶࡧࡂࠬ๲")
  elif bstack11l1ll11ll_opy_ == bstack1ll_opy_ (u"ࠥࡴࡦࡹࡳࡦࡦࠥ๳"):
    return bstack1ll_opy_ (u"ࠫࡁࡺࡤࠡࡥ࡯ࡥࡸࡹ࠽ࠣࡤࡶࡸࡦࡩ࡫࠮ࡦࡤࡸࡦࠨࠠࡴࡶࡼࡰࡪࡃࠢࡤࡱ࡯ࡳࡷࡀࡧࡳࡧࡨࡲࡀࠨ࠾࠽ࡨࡲࡲࡹࠦࡣࡰ࡮ࡲࡶࡂࠨࡧࡳࡧࡨࡲࠧࡄࡐࡢࡵࡶࡩࡩࡂ࠯ࡧࡱࡱࡸࡃࡂ࠯ࡵࡦࡁࠫ๴")
  elif bstack11l1ll11ll_opy_ == bstack1ll_opy_ (u"ࠧ࡫ࡲࡳࡱࡵࠦ๵"):
    return bstack1ll_opy_ (u"࠭࠼ࡵࡦࠣࡧࡱࡧࡳࡴ࠿ࠥࡦࡸࡺࡡࡤ࡭࠰ࡨࡦࡺࡡࠣࠢࡶࡸࡾࡲࡥ࠾ࠤࡦࡳࡱࡵࡲ࠻ࡴࡨࡨࡀࠨ࠾࠽ࡨࡲࡲࡹࠦࡣࡰ࡮ࡲࡶࡂࠨࡲࡦࡦࠥࡂࡊࡸࡲࡰࡴ࠿࠳࡫ࡵ࡮ࡵࡀ࠿࠳ࡹࡪ࠾ࠨ๶")
  elif bstack11l1ll11ll_opy_ == bstack1ll_opy_ (u"ࠢࡵ࡫ࡰࡩࡴࡻࡴࠣ๷"):
    return bstack1ll_opy_ (u"ࠨ࠾ࡷࡨࠥࡩ࡬ࡢࡵࡶࡁࠧࡨࡳࡵࡣࡦ࡯࠲ࡪࡡࡵࡣࠥࠤࡸࡺࡹ࡭ࡧࡀࠦࡨࡵ࡬ࡰࡴ࠽ࠧࡪ࡫ࡡ࠴࠴࠹࠿ࠧࡄ࠼ࡧࡱࡱࡸࠥࡩ࡯࡭ࡱࡵࡁࠧࠩࡥࡦࡣ࠶࠶࠻ࠨ࠾ࡕ࡫ࡰࡩࡴࡻࡴ࠽࠱ࡩࡳࡳࡺ࠾࠽࠱ࡷࡨࡃ࠭๸")
  elif bstack11l1ll11ll_opy_ == bstack1ll_opy_ (u"ࠤࡵࡹࡳࡴࡩ࡯ࡩࠥ๹"):
    return bstack1ll_opy_ (u"ࠪࡀࡹࡪࠠࡤ࡮ࡤࡷࡸࡃࠢࡣࡵࡷࡥࡨࡱ࠭ࡥࡣࡷࡥࠧࠦࡳࡵࡻ࡯ࡩࡂࠨࡣࡰ࡮ࡲࡶ࠿ࡨ࡬ࡢࡥ࡮࠿ࠧࡄ࠼ࡧࡱࡱࡸࠥࡩ࡯࡭ࡱࡵࡁࠧࡨ࡬ࡢࡥ࡮ࠦࡃࡘࡵ࡯ࡰ࡬ࡲ࡬ࡂ࠯ࡧࡱࡱࡸࡃࡂ࠯ࡵࡦࡁࠫ๺")
  else:
    return bstack1ll_opy_ (u"ࠫࡁࡺࡤࠡࡣ࡯࡭࡬ࡴ࠽ࠣࡥࡨࡲࡹ࡫ࡲࠣࠢࡦࡰࡦࡹࡳ࠾ࠤࡥࡷࡹࡧࡣ࡬࠯ࡧࡥࡹࡧࠢࠡࡵࡷࡽࡱ࡫࠽ࠣࡥࡲࡰࡴࡸ࠺ࡣ࡮ࡤࡧࡰࡁࠢ࠿࠾ࡩࡳࡳࡺࠠࡤࡱ࡯ࡳࡷࡃࠢࡣ࡮ࡤࡧࡰࠨ࠾ࠨ๻") + bstack1ll1ll11l1_opy_(
      bstack11l1ll11ll_opy_) + bstack1ll_opy_ (u"ࠬࡂ࠯ࡧࡱࡱࡸࡃࡂ࠯ࡵࡦࡁࠫ๼")
def bstack111lll1l1_opy_(session):
  return bstack1ll_opy_ (u"࠭࠼ࡵࡴࠣࡧࡱࡧࡳࡴ࠿ࠥࡦࡸࡺࡡࡤ࡭࠰ࡶࡴࡽࠢ࠿࠾ࡷࡨࠥࡩ࡬ࡢࡵࡶࡁࠧࡨࡳࡵࡣࡦ࡯࠲ࡪࡡࡵࡣࠣࡷࡪࡹࡳࡪࡱࡱ࠱ࡳࡧ࡭ࡦࠤࡁࡀࡦࠦࡨࡳࡧࡩࡁࠧࢁࡽࠣࠢࡷࡥࡷ࡭ࡥࡵ࠿ࠥࡣࡧࡲࡡ࡯࡭ࠥࡂࢀࢃ࠼࠰ࡣࡁࡀ࠴ࡺࡤ࠿ࡽࢀࡿࢂࡂࡴࡥࠢࡤࡰ࡮࡭࡮࠾ࠤࡦࡩࡳࡺࡥࡳࠤࠣࡧࡱࡧࡳࡴ࠿ࠥࡦࡸࡺࡡࡤ࡭࠰ࡨࡦࡺࡡࠣࡀࡾࢁࡁ࠵ࡴࡥࡀ࠿ࡸࡩࠦࡡ࡭࡫ࡪࡲࡂࠨࡣࡦࡰࡷࡩࡷࠨࠠࡤ࡮ࡤࡷࡸࡃࠢࡣࡵࡷࡥࡨࡱ࠭ࡥࡣࡷࡥࠧࡄࡻࡾ࠾࠲ࡸࡩࡄ࠼ࡵࡦࠣࡥࡱ࡯ࡧ࡯࠿ࠥࡧࡪࡴࡴࡦࡴࠥࠤࡨࡲࡡࡴࡵࡀࠦࡧࡹࡴࡢࡥ࡮࠱ࡩࡧࡴࡢࠤࡁࡿࢂࡂ࠯ࡵࡦࡁࡀࡹࡪࠠࡢ࡮࡬࡫ࡳࡃࠢࡤࡧࡱࡸࡪࡸࠢࠡࡥ࡯ࡥࡸࡹ࠽ࠣࡤࡶࡸࡦࡩ࡫࠮ࡦࡤࡸࡦࠨ࠾ࡼࡿ࠿࠳ࡹࡪ࠾࠽࠱ࡷࡶࡃ࠭๽").format(
    session[bstack1ll_opy_ (u"ࠧࡱࡷࡥࡰ࡮ࡩ࡟ࡶࡴ࡯ࠫ๾")], bstack1ll1ll11ll_opy_(session), bstack11l11l1l1l_opy_(session[bstack1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࡟ࡴࡶࡤࡸࡺࡹࠧ๿")]),
    bstack11l11l1l1l_opy_(session[bstack1ll_opy_ (u"ࠩࡶࡸࡦࡺࡵࡴࠩ຀")]),
    bstack1ll1ll11l1_opy_(session[bstack1ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵࠫກ")] or session[bstack1ll_opy_ (u"ࠫࡩ࡫ࡶࡪࡥࡨࠫຂ")] or bstack1ll_opy_ (u"ࠬ࠭຃")) + bstack1ll_opy_ (u"ࠨࠠࠣຄ") + (session[bstack1ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡠࡸࡨࡶࡸ࡯࡯࡯ࠩ຅")] or bstack1ll_opy_ (u"ࠨࠩຆ")),
    session[bstack1ll_opy_ (u"ࠩࡲࡷࠬງ")] + bstack1ll_opy_ (u"ࠥࠤࠧຈ") + session[bstack1ll_opy_ (u"ࠫࡴࡹ࡟ࡷࡧࡵࡷ࡮ࡵ࡮ࠨຉ")], session[bstack1ll_opy_ (u"ࠬࡪࡵࡳࡣࡷ࡭ࡴࡴࠧຊ")] or bstack1ll_opy_ (u"࠭ࠧ຋"),
    session[bstack1ll_opy_ (u"ࠧࡤࡴࡨࡥࡹ࡫ࡤࡠࡣࡷࠫຌ")] if session[bstack1ll_opy_ (u"ࠨࡥࡵࡩࡦࡺࡥࡥࡡࡤࡸࠬຍ")] else bstack1ll_opy_ (u"ࠩࠪຎ"))
@measure(event_name=EVENTS.bstack1l1l1l1ll_opy_, stage=STAGE.bstack1l1lll1ll1_opy_, bstack1l1l11ll_opy_=bstack1llll1111l_opy_)
def bstack11l11llll_opy_(sessions, bstack1l111lll1_opy_):
  try:
    bstack1l1l1l11_opy_ = bstack1ll_opy_ (u"ࠥࠦຏ")
    if not os.path.exists(bstack1ll11l1l11_opy_):
      os.mkdir(bstack1ll11l1l11_opy_)
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), bstack1ll_opy_ (u"ࠫࡦࡹࡳࡦࡶࡶ࠳ࡷ࡫ࡰࡰࡴࡷ࠲࡭ࡺ࡭࡭ࠩຐ")), bstack1ll_opy_ (u"ࠬࡸࠧຑ")) as f:
      bstack1l1l1l11_opy_ = f.read()
    bstack1l1l1l11_opy_ = bstack1l1l1l11_opy_.replace(bstack1ll_opy_ (u"࠭ࡻࠦࡔࡈࡗ࡚ࡒࡔࡔࡡࡆࡓ࡚ࡔࡔࠦࡿࠪຒ"), str(len(sessions)))
    bstack1l1l1l11_opy_ = bstack1l1l1l11_opy_.replace(bstack1ll_opy_ (u"ࠧࡼࠧࡅ࡙ࡎࡒࡄࡠࡗࡕࡐࠪࢃࠧຓ"), bstack1l111lll1_opy_)
    bstack1l1l1l11_opy_ = bstack1l1l1l11_opy_.replace(bstack1ll_opy_ (u"ࠨࡽࠨࡆ࡚ࡏࡌࡅࡡࡑࡅࡒࡋࠥࡾࠩດ"),
                                              sessions[0].get(bstack1ll_opy_ (u"ࠩࡥࡹ࡮ࡲࡤࡠࡰࡤࡱࡪ࠭ຕ")) if sessions[0] else bstack1ll_opy_ (u"ࠪࠫຖ"))
    with open(os.path.join(bstack1ll11l1l11_opy_, bstack1ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭࠰ࡶࡪࡶ࡯ࡳࡶ࠱࡬ࡹࡳ࡬ࠨທ")), bstack1ll_opy_ (u"ࠬࡽࠧຘ")) as stream:
      stream.write(bstack1l1l1l11_opy_.split(bstack1ll_opy_ (u"࠭ࡻࠦࡕࡈࡗࡘࡏࡏࡏࡕࡢࡈࡆ࡚ࡁࠦࡿࠪນ"))[0])
      for session in sessions:
        stream.write(bstack111lll1l1_opy_(session))
      stream.write(bstack1l1l1l11_opy_.split(bstack1ll_opy_ (u"ࠧࡼࠧࡖࡉࡘ࡙ࡉࡐࡐࡖࡣࡉࡇࡔࡂࠧࢀࠫບ"))[1])
    logger.info(bstack1ll_opy_ (u"ࠨࡉࡨࡲࡪࡸࡡࡵࡧࡧࠤࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭ࠣࡦࡺ࡯࡬ࡥࠢࡤࡶࡹ࡯ࡦࡢࡥࡷࡷࠥࡧࡴࠡࡽࢀࠫປ").format(bstack1ll11l1l11_opy_));
  except Exception as e:
    logger.debug(bstack1lll11ll11_opy_.format(str(e)))
def bstack11ll1l1111_opy_(hashed_id):
  global CONFIG
  try:
    bstack11l1l1l1ll_opy_ = datetime.datetime.now()
    host = bstack1ll_opy_ (u"ࠩ࡫ࡸࡹࡶࡳ࠻࠱࠲ࡥࡵ࡯࠭ࡤ࡮ࡲࡹࡩ࠴ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯࠳ࡩ࡯࡮ࠩຜ") if bstack1ll_opy_ (u"ࠪࡥࡵࡶࠧຝ") in CONFIG else bstack1ll_opy_ (u"ࠫ࡭ࡺࡴࡱࡵ࠽࠳࠴ࡧࡰࡪ࠰ࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫࠯ࡥࡲࡱࠬພ")
    user = CONFIG[bstack1ll_opy_ (u"ࠬࡻࡳࡦࡴࡑࡥࡲ࡫ࠧຟ")]
    key = CONFIG[bstack1ll_opy_ (u"࠭ࡡࡤࡥࡨࡷࡸࡑࡥࡺࠩຠ")]
    bstack11111lll1_opy_ = bstack1ll_opy_ (u"ࠧࡢࡲࡳ࠱ࡦࡻࡴࡰ࡯ࡤࡸࡪ࠭ມ") if bstack1ll_opy_ (u"ࠨࡣࡳࡴࠬຢ") in CONFIG else (bstack1ll_opy_ (u"ࠩࡷࡹࡷࡨ࡯ࡴࡥࡤࡰࡪ࠭ຣ") if CONFIG.get(bstack1ll_opy_ (u"ࠪࡸࡺࡸࡢࡰࡵࡦࡥࡱ࡫ࠧ຤")) else bstack1ll_opy_ (u"ࠫࡦࡻࡴࡰ࡯ࡤࡸࡪ࠭ລ"))
    host = bstack11l1111l1_opy_(cli.config, [bstack1ll_opy_ (u"ࠧࡧࡰࡪࡵࠥ຦"), bstack1ll_opy_ (u"ࠨࡡࡱࡲࡄࡹࡹࡵ࡭ࡢࡶࡨࠦວ"), bstack1ll_opy_ (u"ࠢࡢࡲ࡬ࠦຨ")], host) if bstack1ll_opy_ (u"ࠨࡣࡳࡴࠬຩ") in CONFIG else bstack11l1111l1_opy_(cli.config, [bstack1ll_opy_ (u"ࠤࡤࡴ࡮ࡹࠢສ"), bstack1ll_opy_ (u"ࠥࡥࡺࡺ࡯࡮ࡣࡷࡩࠧຫ"), bstack1ll_opy_ (u"ࠦࡦࡶࡩࠣຬ")], host)
    url = bstack1ll_opy_ (u"ࠬࢁࡽ࠰ࡽࢀ࠳ࡧࡻࡩ࡭ࡦࡶ࠳ࢀࢃ࠯ࡴࡧࡶࡷ࡮ࡵ࡮ࡴ࠰࡭ࡷࡴࡴࠧອ").format(host, bstack11111lll1_opy_, hashed_id)
    headers = {
      bstack1ll_opy_ (u"࠭ࡃࡰࡰࡷࡩࡳࡺ࠭ࡵࡻࡳࡩࠬຮ"): bstack1ll_opy_ (u"ࠧࡢࡲࡳࡰ࡮ࡩࡡࡵ࡫ࡲࡲ࠴ࡰࡳࡰࡰࠪຯ"),
    }
    proxies = bstack11ll11llll_opy_(CONFIG, url)
    response = requests.get(url, headers=headers, proxies=proxies, auth=(user, key))
    if response.json():
      cli.bstack11ll11ll1_opy_(bstack1ll_opy_ (u"ࠣࡪࡷࡸࡵࡀࡧࡦࡶࡢࡷࡪࡹࡳࡪࡱࡱࡷࡤࡲࡩࡴࡶࠥະ"), datetime.datetime.now() - bstack11l1l1l1ll_opy_)
      return list(map(lambda session: session[bstack1ll_opy_ (u"ࠩࡤࡹࡹࡵ࡭ࡢࡶ࡬ࡳࡳࡥࡳࡦࡵࡶ࡭ࡴࡴࠧັ")], response.json()))
  except Exception as e:
    logger.debug(bstack1llllll111_opy_.format(str(e)))
@measure(event_name=EVENTS.bstack1l111llll1_opy_, stage=STAGE.bstack1l1lll1ll1_opy_, bstack1l1l11ll_opy_=bstack1llll1111l_opy_)
def get_build_link():
  global CONFIG
  global bstack1ll11l111l_opy_
  try:
    if bstack1ll_opy_ (u"ࠪࡦࡺ࡯࡬ࡥࡐࡤࡱࡪ࠭າ") in CONFIG:
      bstack11l1l1l1ll_opy_ = datetime.datetime.now()
      host = bstack1ll_opy_ (u"ࠫࡦࡶࡩ࠮ࡥ࡯ࡳࡺࡪࠧຳ") if bstack1ll_opy_ (u"ࠬࡧࡰࡱࠩິ") in CONFIG else bstack1ll_opy_ (u"࠭ࡡࡱ࡫ࠪີ")
      user = CONFIG[bstack1ll_opy_ (u"ࠧࡶࡵࡨࡶࡓࡧ࡭ࡦࠩຶ")]
      key = CONFIG[bstack1ll_opy_ (u"ࠨࡣࡦࡧࡪࡹࡳࡌࡧࡼࠫື")]
      bstack11111lll1_opy_ = bstack1ll_opy_ (u"ࠩࡤࡴࡵ࠳ࡡࡶࡶࡲࡱࡦࡺࡥࠨຸ") if bstack1ll_opy_ (u"ࠪࡥࡵࡶູࠧ") in CONFIG else bstack1ll_opy_ (u"ࠫࡦࡻࡴࡰ࡯ࡤࡸࡪ຺࠭")
      url = bstack1ll_opy_ (u"ࠬ࡮ࡴࡵࡲࡶ࠾࠴࠵ࡻࡾ࠼ࡾࢁࡅࢁࡽ࠯ࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࠮ࡤࡱࡰ࠳ࢀࢃ࠯ࡣࡷ࡬ࡰࡩࡹ࠮࡫ࡵࡲࡲࠬົ").format(user, key, host, bstack11111lll1_opy_)
      if cli.is_enabled(CONFIG):
        bstack1l111lll1_opy_, hashed_id = cli.bstack11111lll_opy_()
        logger.info(bstack1l1lllll11_opy_.format(bstack1l111lll1_opy_))
        return [hashed_id, bstack1l111lll1_opy_]
      else:
        headers = {
          bstack1ll_opy_ (u"࠭ࡃࡰࡰࡷࡩࡳࡺ࠭ࡵࡻࡳࡩࠬຼ"): bstack1ll_opy_ (u"ࠧࡢࡲࡳࡰ࡮ࡩࡡࡵ࡫ࡲࡲ࠴ࡰࡳࡰࡰࠪຽ"),
        }
        if bstack1ll_opy_ (u"ࠨࡤࡸ࡭ࡱࡪࡉࡥࡧࡱࡸ࡮࡬ࡩࡦࡴࠪ຾") in CONFIG:
          params = {bstack1ll_opy_ (u"ࠩࡱࡥࡲ࡫ࠧ຿"): CONFIG[bstack1ll_opy_ (u"ࠪࡦࡺ࡯࡬ࡥࡐࡤࡱࡪ࠭ເ")], bstack1ll_opy_ (u"ࠫࡧࡻࡩ࡭ࡦࡢ࡭ࡩ࡫࡮ࡵ࡫ࡩ࡭ࡪࡸࠧແ"): CONFIG[bstack1ll_opy_ (u"ࠬࡨࡵࡪ࡮ࡧࡍࡩ࡫࡮ࡵ࡫ࡩ࡭ࡪࡸࠧໂ")]}
        else:
          params = {bstack1ll_opy_ (u"࠭࡮ࡢ࡯ࡨࠫໃ"): CONFIG[bstack1ll_opy_ (u"ࠧࡣࡷ࡬ࡰࡩࡔࡡ࡮ࡧࠪໄ")]}
        proxies = bstack11ll11llll_opy_(CONFIG, url)
        response = requests.get(url, params=params, headers=headers, proxies=proxies)
        if response.json():
          bstack1l1l111111_opy_ = response.json()[0][bstack1ll_opy_ (u"ࠨࡣࡸࡸࡴࡳࡡࡵ࡫ࡲࡲࡤࡨࡵࡪ࡮ࡧࠫ໅")]
          if bstack1l1l111111_opy_:
            bstack1l111lll1_opy_ = bstack1l1l111111_opy_[bstack1ll_opy_ (u"ࠩࡳࡹࡧࡲࡩࡤࡡࡸࡶࡱ࠭ໆ")].split(bstack1ll_opy_ (u"ࠪࡴࡺࡨ࡬ࡪࡥ࠰ࡦࡺ࡯࡬ࡥࠩ໇"))[0] + bstack1ll_opy_ (u"ࠫࡧࡻࡩ࡭ࡦࡶ࠳່ࠬ") + bstack1l1l111111_opy_[
              bstack1ll_opy_ (u"ࠬ࡮ࡡࡴࡪࡨࡨࡤ࡯ࡤࠨ້")]
            logger.info(bstack1l1lllll11_opy_.format(bstack1l111lll1_opy_))
            bstack1ll11l111l_opy_ = bstack1l1l111111_opy_[bstack1ll_opy_ (u"࠭ࡨࡢࡵ࡫ࡩࡩࡥࡩࡥ໊ࠩ")]
            bstack11ll1lllll_opy_ = CONFIG[bstack1ll_opy_ (u"ࠧࡣࡷ࡬ࡰࡩࡔࡡ࡮ࡧ໋ࠪ")]
            if bstack1ll_opy_ (u"ࠨࡤࡸ࡭ࡱࡪࡉࡥࡧࡱࡸ࡮࡬ࡩࡦࡴࠪ໌") in CONFIG:
              bstack11ll1lllll_opy_ += bstack1ll_opy_ (u"ࠩࠣࠫໍ") + CONFIG[bstack1ll_opy_ (u"ࠪࡦࡺ࡯࡬ࡥࡋࡧࡩࡳࡺࡩࡧ࡫ࡨࡶࠬ໎")]
            if bstack11ll1lllll_opy_ != bstack1l1l111111_opy_[bstack1ll_opy_ (u"ࠫࡳࡧ࡭ࡦࠩ໏")]:
              logger.debug(bstack11111l1ll_opy_.format(bstack1l1l111111_opy_[bstack1ll_opy_ (u"ࠬࡴࡡ࡮ࡧࠪ໐")], bstack11ll1lllll_opy_))
            cli.bstack11ll11ll1_opy_(bstack1ll_opy_ (u"ࠨࡨࡵࡶࡳ࠾࡬࡫ࡴࡠࡤࡸ࡭ࡱࡪ࡟࡭࡫ࡱ࡯ࠧ໑"), datetime.datetime.now() - bstack11l1l1l1ll_opy_)
            return [bstack1l1l111111_opy_[bstack1ll_opy_ (u"ࠧࡩࡣࡶ࡬ࡪࡪ࡟ࡪࡦࠪ໒")], bstack1l111lll1_opy_]
    else:
      logger.warning(bstack11l11lll1l_opy_)
  except Exception as e:
    logger.debug(bstack1l111lllll_opy_.format(str(e)))
  return [None, None]
def bstack111llll1l_opy_(url, bstack11llllll1_opy_=False):
  global CONFIG
  global bstack111lllllll_opy_
  if not bstack111lllllll_opy_:
    hostname = bstack11ll1l11l_opy_(url)
    is_private = bstack1l11l1l1l_opy_(hostname)
    if (bstack1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱࡌࡰࡥࡤࡰࠬ໓") in CONFIG and not bstack11l11lllll_opy_(CONFIG[bstack1ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫ࡍࡱࡦࡥࡱ࠭໔")])) and (is_private or bstack11llllll1_opy_):
      bstack111lllllll_opy_ = hostname
def bstack11ll1l11l_opy_(url):
  return urlparse(url).hostname
def bstack1l11l1l1l_opy_(hostname):
  for bstack1llll11l1_opy_ in bstack1l11ll1ll1_opy_:
    regex = re.compile(bstack1llll11l1_opy_)
    if regex.match(hostname):
      return True
  return False
def bstack1l1lllll1l_opy_(bstack1lll11l1ll_opy_):
  return True if bstack1lll11l1ll_opy_ in threading.current_thread().__dict__.keys() else False
@measure(event_name=EVENTS.bstack1llll11ll_opy_, stage=STAGE.bstack1l1lll1ll1_opy_, bstack1l1l11ll_opy_=bstack1llll1111l_opy_)
def getAccessibilityResults(driver):
  global CONFIG
  global bstack11l1l111l_opy_
  bstack1llll1lll_opy_ = not (bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠪ࡭ࡸࡇ࠱࠲ࡻࡗࡩࡸࡺࠧ໕"), None) and bstack1l11l11l_opy_(
          threading.current_thread(), bstack1ll_opy_ (u"ࠫࡦ࠷࠱ࡺࡒ࡯ࡥࡹ࡬࡯ࡳ࡯ࠪ໖"), None))
  bstack11lll11l1l_opy_ = getattr(driver, bstack1ll_opy_ (u"ࠬࡨࡳࡵࡣࡦ࡯ࡆ࠷࠱ࡺࡕ࡫ࡳࡺࡲࡤࡔࡥࡤࡲࠬ໗"), None) != True
  bstack1111lllll_opy_ = bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"࠭ࡩࡴࡃࡳࡴࡆ࠷࠱ࡺࡖࡨࡷࡹ࠭໘"), None) and bstack1l11l11l_opy_(
          threading.current_thread(), bstack1ll_opy_ (u"ࠧࡢࡲࡳࡅ࠶࠷ࡹࡑ࡮ࡤࡸ࡫ࡵࡲ࡮ࠩ໙"), None)
  if bstack1111lllll_opy_:
    if not bstack11111ll11_opy_():
      logger.warning(bstack1ll_opy_ (u"ࠣࡐࡲࡸࠥࡧ࡮ࠡࡃࡳࡴࠥࡇࡣࡤࡧࡶࡷ࡮ࡨࡩ࡭࡫ࡷࡽࠥࡇࡵࡵࡱࡰࡥࡹ࡯࡯࡯ࠢࡶࡩࡸࡹࡩࡰࡰ࠯ࠤࡨࡧ࡮࡯ࡱࡷࠤࡷ࡫ࡴࡳ࡫ࡨࡺࡪࠦࡁࡱࡲࠣࡅࡨࡩࡥࡴࡵ࡬ࡦ࡮ࡲࡩࡵࡻࠣࡶࡪࡹࡵ࡭ࡶࡶ࠲ࠧ໚"))
      return {}
    logger.debug(bstack1ll_opy_ (u"ࠩࡓࡩࡷ࡬࡯ࡳ࡯࡬ࡲ࡬ࠦࡳࡤࡣࡱࠤࡧ࡫ࡦࡰࡴࡨࠤ࡬࡫ࡴࡵ࡫ࡱ࡫ࠥࡸࡥࡴࡷ࡯ࡸࡸ࠭໛"))
    logger.debug(perform_scan(driver, driver_command=bstack1ll_opy_ (u"ࠪࡩࡽ࡫ࡣࡶࡶࡨࡗࡨࡸࡩࡱࡶࠪໜ")))
    results = bstack1ll11l11l_opy_(bstack1ll_opy_ (u"ࠦࡷ࡫ࡳࡶ࡮ࡷࡷࠧໝ"))
    if results is not None and results.get(bstack1ll_opy_ (u"ࠧ࡯ࡳࡴࡷࡨࡷࠧໞ")) is not None:
        return results[bstack1ll_opy_ (u"ࠨࡩࡴࡵࡸࡩࡸࠨໟ")]
    logger.error(bstack1ll_opy_ (u"ࠢࡏࡱࠣࡅࡨࡩࡥࡴࡵ࡬ࡦ࡮ࡲࡩࡵࡻࠣࡖࡪࡹࡵ࡭ࡶࡶࠤࡼ࡫ࡲࡦࠢࡩࡳࡺࡴࡤ࠯ࠤ໠"))
    return []
  if not bstack1llll1l11_opy_.bstack1l111lll1l_opy_(CONFIG, bstack11l1l111l_opy_) or (bstack11lll11l1l_opy_ and bstack1llll1lll_opy_):
    logger.warning(bstack1ll_opy_ (u"ࠣࡐࡲࡸࠥࡧ࡮ࠡࡃࡦࡧࡪࡹࡳࡪࡤ࡬ࡰ࡮ࡺࡹࠡࡃࡸࡸࡴࡳࡡࡵ࡫ࡲࡲࠥࡹࡥࡴࡵ࡬ࡳࡳ࠲ࠠࡤࡣࡱࡲࡴࡺࠠࡳࡧࡷࡶ࡮࡫ࡶࡦࠢࡄࡧࡨ࡫ࡳࡴ࡫ࡥ࡭ࡱ࡯ࡴࡺࠢࡵࡩࡸࡻ࡬ࡵࡵ࠱ࠦ໡"))
    return {}
  try:
    logger.debug(bstack1ll_opy_ (u"ࠩࡓࡩࡷ࡬࡯ࡳ࡯࡬ࡲ࡬ࠦࡳࡤࡣࡱࠤࡧ࡫ࡦࡰࡴࡨࠤ࡬࡫ࡴࡵ࡫ࡱ࡫ࠥࡸࡥࡴࡷ࡯ࡸࡸ࠭໢"))
    logger.debug(perform_scan(driver))
    results = driver.execute_async_script(bstack1111l1ll1_opy_.bstack1ll111l11_opy_)
    return results
  except Exception:
    logger.error(bstack1ll_opy_ (u"ࠥࡒࡴࠦࡡࡤࡥࡨࡷࡸ࡯ࡢࡪ࡮࡬ࡸࡾࠦࡲࡦࡵࡸࡰࡹࡹࠠࡸࡧࡵࡩࠥ࡬࡯ࡶࡰࡧ࠲ࠧ໣"))
    return {}
@measure(event_name=EVENTS.bstack1l111l111l_opy_, stage=STAGE.bstack1l1lll1ll1_opy_, bstack1l1l11ll_opy_=bstack1llll1111l_opy_)
def getAccessibilityResultsSummary(driver):
  global CONFIG
  global bstack11l1l111l_opy_
  bstack1llll1lll_opy_ = not (bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠫ࡮ࡹࡁ࠲࠳ࡼࡘࡪࡹࡴࠨ໤"), None) and bstack1l11l11l_opy_(
          threading.current_thread(), bstack1ll_opy_ (u"ࠬࡧ࠱࠲ࡻࡓࡰࡦࡺࡦࡰࡴࡰࠫ໥"), None))
  bstack11lll11l1l_opy_ = getattr(driver, bstack1ll_opy_ (u"࠭ࡢࡴࡶࡤࡧࡰࡇ࠱࠲ࡻࡖ࡬ࡴࡻ࡬ࡥࡕࡦࡥࡳ࠭໦"), None) != True
  bstack1111lllll_opy_ = bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠧࡪࡵࡄࡴࡵࡇ࠱࠲ࡻࡗࡩࡸࡺࠧ໧"), None) and bstack1l11l11l_opy_(
          threading.current_thread(), bstack1ll_opy_ (u"ࠨࡣࡳࡴࡆ࠷࠱ࡺࡒ࡯ࡥࡹ࡬࡯ࡳ࡯ࠪ໨"), None)
  if bstack1111lllll_opy_:
    if not bstack11111ll11_opy_():
      logger.warning(bstack1ll_opy_ (u"ࠤࡑࡳࡹࠦࡡ࡯ࠢࡄࡴࡵࠦࡁࡤࡥࡨࡷࡸ࡯ࡢࡪ࡮࡬ࡸࡾࠦࡁࡶࡶࡲࡱࡦࡺࡩࡰࡰࠣࡷࡪࡹࡳࡪࡱࡱ࠰ࠥࡩࡡ࡯ࡰࡲࡸࠥࡸࡥࡵࡴ࡬ࡩࡻ࡫ࠠࡂࡲࡳࠤࡆࡩࡣࡦࡵࡶ࡭ࡧ࡯࡬ࡪࡶࡼࠤࡷ࡫ࡳࡶ࡮ࡷࡷࠥࡹࡵ࡮࡯ࡤࡶࡾ࠴ࠢ໩"))
      return {}
    logger.debug(bstack1ll_opy_ (u"ࠪࡔࡪࡸࡦࡰࡴࡰ࡭ࡳ࡭ࠠࡴࡥࡤࡲࠥࡨࡥࡧࡱࡵࡩࠥ࡭ࡥࡵࡶ࡬ࡲ࡬ࠦࡲࡦࡵࡸࡰࡹࡹࠠࡴࡷࡰࡱࡦࡸࡹࠨ໪"))
    logger.debug(perform_scan(driver, driver_command=bstack1ll_opy_ (u"ࠫࡪࡾࡥࡤࡷࡷࡩࡘࡩࡲࡪࡲࡷࠫ໫")))
    results = bstack1ll11l11l_opy_(bstack1ll_opy_ (u"ࠧࡸࡥࡴࡷ࡯ࡸࡘࡻ࡭࡮ࡣࡵࡽࠧ໬"))
    if results is not None and results.get(bstack1ll_opy_ (u"ࠨࡳࡶ࡯ࡰࡥࡷࡿࠢ໭")) is not None:
        return results[bstack1ll_opy_ (u"ࠢࡴࡷࡰࡱࡦࡸࡹࠣ໮")]
    logger.error(bstack1ll_opy_ (u"ࠣࡐࡲࠤࡆࡩࡣࡦࡵࡶ࡭ࡧ࡯࡬ࡪࡶࡼࠤࡗ࡫ࡳࡶ࡮ࡷࡷ࡙ࠥࡵ࡮࡯ࡤࡶࡾࠦࡷࡢࡵࠣࡪࡴࡻ࡮ࡥ࠰ࠥ໯"))
    return {}
  if not bstack1llll1l11_opy_.bstack1l111lll1l_opy_(CONFIG, bstack11l1l111l_opy_) or (bstack11lll11l1l_opy_ and bstack1llll1lll_opy_):
    logger.warning(bstack1ll_opy_ (u"ࠤࡑࡳࡹࠦࡡ࡯ࠢࡄࡧࡨ࡫ࡳࡴ࡫ࡥ࡭ࡱ࡯ࡴࡺࠢࡄࡹࡹࡵ࡭ࡢࡶ࡬ࡳࡳࠦࡳࡦࡵࡶ࡭ࡴࡴࠬࠡࡥࡤࡲࡳࡵࡴࠡࡴࡨࡸࡷ࡯ࡥࡷࡧࠣࡅࡨࡩࡥࡴࡵ࡬ࡦ࡮ࡲࡩࡵࡻࠣࡶࡪࡹࡵ࡭ࡶࡶࠤࡸࡻ࡭࡮ࡣࡵࡽ࠳ࠨ໰"))
    return {}
  try:
    logger.debug(bstack1ll_opy_ (u"ࠪࡔࡪࡸࡦࡰࡴࡰ࡭ࡳ࡭ࠠࡴࡥࡤࡲࠥࡨࡥࡧࡱࡵࡩࠥ࡭ࡥࡵࡶ࡬ࡲ࡬ࠦࡲࡦࡵࡸࡰࡹࡹࠠࡴࡷࡰࡱࡦࡸࡹࠨ໱"))
    logger.debug(perform_scan(driver))
    bstack1111l11l_opy_ = driver.execute_async_script(bstack1111l1ll1_opy_.bstack1l1lllllll_opy_)
    return bstack1111l11l_opy_
  except Exception:
    logger.error(bstack1ll_opy_ (u"ࠦࡓࡵࠠࡢࡥࡦࡩࡸࡹࡩࡣ࡫࡯࡭ࡹࡿࠠࡴࡷࡰࡱࡦࡸࡹࠡࡹࡤࡷࠥ࡬࡯ࡶࡰࡧ࠲ࠧ໲"))
    return {}
def bstack11111ll11_opy_():
  global CONFIG
  global bstack11l1l111l_opy_
  bstack111111ll_opy_ = bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠬ࡯ࡳࡂࡲࡳࡅ࠶࠷ࡹࡕࡧࡶࡸࠬ໳"), None) and bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"࠭ࡡࡱࡲࡄ࠵࠶ࡿࡐ࡭ࡣࡷࡪࡴࡸ࡭ࠨ໴"), None)
  if not bstack1llll1l11_opy_.bstack1l111lll1l_opy_(CONFIG, bstack11l1l111l_opy_) or not bstack111111ll_opy_:
        logger.warning(bstack1ll_opy_ (u"ࠢࡏࡱࡷࠤࡦࡴࠠࡂࡲࡳࠤࡆࡩࡣࡦࡵࡶ࡭ࡧ࡯࡬ࡪࡶࡼࠤࡆࡻࡴࡰ࡯ࡤࡸ࡮ࡵ࡮ࠡࡵࡨࡷࡸ࡯࡯࡯࠮ࠣࡧࡦࡴ࡮ࡰࡶࠣࡶࡪࡺࡲࡪࡧࡹࡩࠥࡸࡥࡴࡷ࡯ࡸࡸ࠴ࠢ໵"))
        return False
  return True
def bstack1ll11l11l_opy_(result_type):
    bstack11l1l1l1l1_opy_ = bstack1lll1111l_opy_.current_test_uuid() if bstack1lll1111l_opy_.current_test_uuid() else bstack1l11111lll_opy_.current_hook_uuid()
    with ThreadPoolExecutor() as executor:
        future = executor.submit(bstack11l1l11l1_opy_(bstack11l1l1l1l1_opy_, result_type))
        try:
            return future.result(timeout=bstack11ll11l1l_opy_)
        except TimeoutError:
            logger.error(bstack1ll_opy_ (u"ࠣࡖ࡬ࡱࡪࡵࡵࡵࠢࡤࡪࡹ࡫ࡲࠡࡽࢀࡷࠥࡽࡨࡪ࡮ࡨࠤ࡫࡫ࡴࡤࡪ࡬ࡲ࡬ࠦࡁࡤࡥࡨࡷࡸ࡯ࡢࡪ࡮࡬ࡸࡾࠦࡒࡦࡵࡸࡰࡹࡹࠢ໶").format(bstack11ll11l1l_opy_))
        except Exception as ex:
            logger.debug(bstack1ll_opy_ (u"ࠤࡈࡶࡷࡵࡲࠡࡴࡨࡸࡷ࡯ࡥࡷ࡫ࡱ࡫ࠥࡇࡰࡱࠢࡄࡧࡨ࡫ࡳࡴ࡫ࡥ࡭ࡱ࡯ࡴࡺࠢࡄࡹࡹࡵ࡭ࡢࡶ࡬ࡳࡳࠦࡻࡾ࠰ࠣࡉࡷࡸ࡯ࡳࠢ࠰ࠤࢀࢃࠢ໷").format(result_type, str(ex)))
    return {}
@measure(event_name=EVENTS.bstack1l1l1ll1l_opy_, stage=STAGE.bstack1l1lll1ll1_opy_, bstack1l1l11ll_opy_=bstack1llll1111l_opy_)
def perform_scan(driver, *args, **kwargs):
  global CONFIG
  global bstack11l1l111l_opy_
  bstack1llll1lll_opy_ = not (bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠪ࡭ࡸࡇ࠱࠲ࡻࡗࡩࡸࡺࠧ໸"), None) and bstack1l11l11l_opy_(
          threading.current_thread(), bstack1ll_opy_ (u"ࠫࡦ࠷࠱ࡺࡒ࡯ࡥࡹ࡬࡯ࡳ࡯ࠪ໹"), None))
  bstack1llll111l1_opy_ = not (bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠬ࡯ࡳࡂࡲࡳࡅ࠶࠷ࡹࡕࡧࡶࡸࠬ໺"), None) and bstack1l11l11l_opy_(
          threading.current_thread(), bstack1ll_opy_ (u"࠭ࡡࡱࡲࡄ࠵࠶ࡿࡐ࡭ࡣࡷࡪࡴࡸ࡭ࠨ໻"), None))
  bstack11lll11l1l_opy_ = getattr(driver, bstack1ll_opy_ (u"ࠧࡣࡵࡷࡥࡨࡱࡁ࠲࠳ࡼࡗ࡭ࡵࡵ࡭ࡦࡖࡧࡦࡴࠧ໼"), None) != True
  if not bstack1llll1l11_opy_.bstack1l111lll1l_opy_(CONFIG, bstack11l1l111l_opy_) or (bstack11lll11l1l_opy_ and bstack1llll1lll_opy_ and bstack1llll111l1_opy_):
    logger.warning(bstack1ll_opy_ (u"ࠣࡐࡲࡸࠥࡧ࡮ࠡࡃࡦࡧࡪࡹࡳࡪࡤ࡬ࡰ࡮ࡺࡹࠡࡃࡸࡸࡴࡳࡡࡵ࡫ࡲࡲࠥࡹࡥࡴࡵ࡬ࡳࡳ࠲ࠠࡤࡣࡱࡲࡴࡺࠠࡳࡷࡱࠤࡆࡩࡣࡦࡵࡶ࡭ࡧ࡯࡬ࡪࡶࡼࠤࡸࡩࡡ࡯࠰ࠥ໽"))
    return {}
  try:
    bstack111l11ll_opy_ = bstack1ll_opy_ (u"ࠩࡤࡴࡵ࠭໾") in CONFIG and CONFIG.get(bstack1ll_opy_ (u"ࠪࡥࡵࡶࠧ໿"), bstack1ll_opy_ (u"ࠫࠬༀ"))
    session_id = getattr(driver, bstack1ll_opy_ (u"ࠬࡹࡥࡴࡵ࡬ࡳࡳࡥࡩࡥࠩ༁"), None)
    if not session_id:
      logger.warning(bstack1ll_opy_ (u"ࠨࡎࡰࠢࡶࡩࡸࡹࡩࡰࡰࠣࡍࡉࠦࡦࡰࡷࡱࡨࠥ࡬࡯ࡳࠢࡧࡶ࡮ࡼࡥࡳࠤ༂"))
      return {bstack1ll_opy_ (u"ࠢࡦࡴࡵࡳࡷࠨ༃"): bstack1ll_opy_ (u"ࠣࡐࡲࠤࡸ࡫ࡳࡴ࡫ࡲࡲࠥࡏࡄࠡࡨࡲࡹࡳࡪࠢ༄")}
    if bstack111l11ll_opy_:
      try:
        bstack1ll1lll1l1_opy_ = {
              bstack1ll_opy_ (u"ࠩࡷ࡬ࡏࡽࡴࡕࡱ࡮ࡩࡳ࠭༅"): os.environ.get(bstack1ll_opy_ (u"ࠪࡆࡘࡥࡁ࠲࠳࡜ࡣࡏ࡝ࡔࠨ༆"), os.environ.get(bstack1ll_opy_ (u"ࠫࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡘࡊ࡙ࡔࡉࡗࡅࡣࡏ࡝ࡔࠨ༇"), bstack1ll_opy_ (u"ࠬ࠭༈"))),
              bstack1ll_opy_ (u"࠭ࡴࡩࡖࡨࡷࡹࡘࡵ࡯ࡗࡸ࡭ࡩ࠭༉"): bstack1lll1111l_opy_.current_test_uuid() if bstack1lll1111l_opy_.current_test_uuid() else bstack1l11111lll_opy_.current_hook_uuid(),
              bstack1ll_opy_ (u"ࠧࡢࡷࡷ࡬ࡍ࡫ࡡࡥࡧࡵࠫ༊"): os.environ.get(bstack1ll_opy_ (u"ࠨࡄࡖࡣࡆ࠷࠱࡚ࡡࡍ࡛࡙࠭་")),
              bstack1ll_opy_ (u"ࠩࡶࡧࡦࡴࡔࡪ࡯ࡨࡷࡹࡧ࡭ࡱࠩ༌"): str(int(datetime.datetime.now().timestamp() * 1000)),
              bstack1ll_opy_ (u"ࠪࡸ࡭ࡈࡵࡪ࡮ࡧ࡙ࡺ࡯ࡤࠨ།"): os.environ.get(bstack1ll_opy_ (u"ࠫࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡘࡊ࡙ࡔࡉࡗࡅࡣ࡚࡛ࡉࡅࠩ༎"), bstack1ll_opy_ (u"ࠬ࠭༏")),
              bstack1ll_opy_ (u"࠭࡭ࡦࡶ࡫ࡳࡩ࠭༐"): kwargs.get(bstack1ll_opy_ (u"ࠧࡥࡴ࡬ࡺࡪࡸ࡟ࡤࡱࡰࡱࡦࡴࡤࠨ༑"), None) or bstack1ll_opy_ (u"ࠨࠩ༒")
          }
        if not hasattr(thread_local, bstack1ll_opy_ (u"ࠩࡥࡥࡸ࡫࡟ࡢࡲࡳࡣࡦ࠷࠱ࡺࡡࡶࡧࡷ࡯ࡰࡵࠩ༓")):
            scripts = {bstack1ll_opy_ (u"ࠪࡷࡨࡧ࡮ࠨ༔"): bstack1111l1ll1_opy_.perform_scan}
            thread_local.base_app_a11y_script = scripts
        bstack1l1l111ll_opy_ = copy.deepcopy(thread_local.base_app_a11y_script)
        bstack1l1l111ll_opy_[bstack1ll_opy_ (u"ࠫࡸࡩࡡ࡯ࠩ༕")] = bstack1l1l111ll_opy_[bstack1ll_opy_ (u"ࠬࡹࡣࡢࡰࠪ༖")] % json.dumps(bstack1ll1lll1l1_opy_)
        bstack1111l1ll1_opy_.bstack1l111lll_opy_(bstack1l1l111ll_opy_)
        bstack1111l1ll1_opy_.store()
        bstack1lll11lll_opy_ = driver.execute_script(bstack1111l1ll1_opy_.perform_scan)
      except Exception as bstack1ll1111l11_opy_:
        logger.info(bstack1ll_opy_ (u"ࠨࡁࡱࡲ࡬ࡹࡲࠦࡡࡤࡥࡨࡷࡸ࡯ࡢࡪ࡮࡬ࡸࡾࠦࡳࡤࡣࡱࠤ࡫ࡧࡩ࡭ࡧࡧ࠾ࠥࠨ༗") + str(bstack1ll1111l11_opy_))
        bstack1lll11lll_opy_ = {bstack1ll_opy_ (u"ࠢࡦࡴࡵࡳࡷࠨ༘"): str(bstack1ll1111l11_opy_)}
    else:
      bstack1lll11lll_opy_ = driver.execute_async_script(bstack1111l1ll1_opy_.perform_scan, {bstack1ll_opy_ (u"ࠨ࡯ࡨࡸ࡭ࡵࡤࠨ༙"): kwargs.get(bstack1ll_opy_ (u"ࠩࡧࡶ࡮ࡼࡥࡳࡡࡦࡳࡲࡳࡡ࡯ࡦࠪ༚"), None) or bstack1ll_opy_ (u"ࠪࠫ༛")})
    return bstack1lll11lll_opy_
  except Exception as err:
    logger.error(bstack1ll_opy_ (u"࡚ࠦࡴࡡࡣ࡮ࡨࠤࡹࡵࠠࡳࡷࡱࠤࡦࡩࡣࡦࡵࡶ࡭ࡧ࡯࡬ࡪࡶࡼࠤࡸࡩࡡ࡯࠰ࠣࡿࢂࠨ༜").format(str(err)))
    return {}