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
import re
import sys
import json
import time
import shutil
import tempfile
import requests
import subprocess
from threading import Thread
from os.path import expanduser
from bstack_utils.constants import *
from requests.auth import HTTPBasicAuth
from bstack_utils.helper import bstack1l111111_opy_
from bstack_utils.measure import measure
from bstack_utils.bstack1llllllll_opy_ import bstack1l1lll11ll_opy_
class bstack1lll1lllll_opy_:
  working_dir = os.getcwd()
  bstack11ll11ll1l_opy_ = False
  config = {}
  bstack111l1ll1l11_opy_ = bstack1ll_opy_ (u"ࠧࠨὈ")
  binary_path = bstack1ll_opy_ (u"ࠨࠩὉ")
  bstack11111l1ll11_opy_ = bstack1ll_opy_ (u"ࠩࠪὊ")
  bstack11l11l1111_opy_ = False
  bstack1llllllll1ll_opy_ = None
  bstack1111111lll1_opy_ = {}
  bstack11111l111ll_opy_ = 300
  bstack11111l1l11l_opy_ = False
  logger = None
  bstack111111lll11_opy_ = False
  bstack11l111l1l_opy_ = False
  percy_build_id = None
  bstack111111ll1l1_opy_ = bstack1ll_opy_ (u"ࠪࠫὋ")
  bstack1lllllll1lll_opy_ = {
    bstack1ll_opy_ (u"ࠫࡨ࡮ࡲࡰ࡯ࡨࠫὌ") : 1,
    bstack1ll_opy_ (u"ࠬ࡬ࡩࡳࡧࡩࡳࡽ࠭Ὅ") : 2,
    bstack1ll_opy_ (u"࠭ࡥࡥࡩࡨࠫ὎") : 3,
    bstack1ll_opy_ (u"ࠧࡴࡣࡩࡥࡷ࡯ࠧ὏") : 4
  }
  def __init__(self) -> None: pass
  def bstack11111l11lll_opy_(self):
    bstack1111111l111_opy_ = bstack1ll_opy_ (u"ࠨࠩὐ")
    bstack11111l1ll1l_opy_ = sys.platform
    bstack11111l11l1l_opy_ = bstack1ll_opy_ (u"ࠩࡳࡩࡷࡩࡹࠨὑ")
    if re.match(bstack1ll_opy_ (u"ࠥࡨࡦࡸࡷࡪࡰࡿࡱࡦࡩࠠࡰࡵࠥὒ"), bstack11111l1ll1l_opy_) != None:
      bstack1111111l111_opy_ = bstack11l11lll1ll_opy_ + bstack1ll_opy_ (u"ࠦ࠴ࡶࡥࡳࡥࡼ࠱ࡴࡹࡸ࠯ࡼ࡬ࡴࠧὓ")
      self.bstack111111ll1l1_opy_ = bstack1ll_opy_ (u"ࠬࡳࡡࡤࠩὔ")
    elif re.match(bstack1ll_opy_ (u"ࠨ࡭ࡴࡹ࡬ࡲࢁࡳࡳࡺࡵࡿࡱ࡮ࡴࡧࡸࡾࡦࡽ࡬ࡽࡩ࡯ࡾࡥࡧࡨࡽࡩ࡯ࡾࡺ࡭ࡳࡩࡥࡽࡧࡰࡧࢁࡽࡩ࡯࠵࠵ࠦὕ"), bstack11111l1ll1l_opy_) != None:
      bstack1111111l111_opy_ = bstack11l11lll1ll_opy_ + bstack1ll_opy_ (u"ࠢ࠰ࡲࡨࡶࡨࡿ࠭ࡸ࡫ࡱ࠲ࡿ࡯ࡰࠣὖ")
      bstack11111l11l1l_opy_ = bstack1ll_opy_ (u"ࠣࡲࡨࡶࡨࡿ࠮ࡦࡺࡨࠦὗ")
      self.bstack111111ll1l1_opy_ = bstack1ll_opy_ (u"ࠩࡺ࡭ࡳ࠭὘")
    else:
      bstack1111111l111_opy_ = bstack11l11lll1ll_opy_ + bstack1ll_opy_ (u"ࠥ࠳ࡵ࡫ࡲࡤࡻ࠰ࡰ࡮ࡴࡵࡹ࠰ࡽ࡭ࡵࠨὙ")
      self.bstack111111ll1l1_opy_ = bstack1ll_opy_ (u"ࠫࡱ࡯࡮ࡶࡺࠪ὚")
    return bstack1111111l111_opy_, bstack11111l11l1l_opy_
  def bstack1lllllll1ll1_opy_(self):
    try:
      bstack111111ll1ll_opy_ = [os.path.join(expanduser(bstack1ll_opy_ (u"ࠧࢄࠢὛ")), bstack1ll_opy_ (u"࠭࠮ࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰ࠭὜")), self.working_dir, tempfile.gettempdir()]
      for path in bstack111111ll1ll_opy_:
        if(self.bstack11111ll11ll_opy_(path)):
          return path
      raise bstack1ll_opy_ (u"ࠢࡖࡰࡤࡦࡱ࡫ࠠࡵࡱࠣࡨࡴࡽ࡮࡭ࡱࡤࡨࠥࡶࡥࡳࡥࡼࠤࡧ࡯࡮ࡢࡴࡼࠦὝ")
    except Exception as e:
      self.logger.error(bstack1ll_opy_ (u"ࠣࡈࡤ࡭ࡱ࡫ࡤࠡࡶࡲࠤ࡫࡯࡮ࡥࠢࡤࡺࡦ࡯࡬ࡢࡤ࡯ࡩࠥࡶࡡࡵࡪࠣࡪࡴࡸࠠࡱࡧࡵࡧࡾࠦࡤࡰࡹࡱࡰࡴࡧࡤ࠭ࠢࡈࡼࡨ࡫ࡰࡵ࡫ࡲࡲࠥ࠳ࠠࡼࡿࠥ὞").format(e))
  def bstack11111ll11ll_opy_(self, path):
    try:
      if not os.path.exists(path):
        os.makedirs(path)
      return True
    except:
      return False
  def bstack1llllllllll1_opy_(self, bstack11111ll111l_opy_):
    return os.path.join(bstack11111ll111l_opy_, self.bstack111l1ll1l11_opy_ + bstack1ll_opy_ (u"ࠤ࠱ࡩࡹࡧࡧࠣὟ"))
  def bstack1111111111l_opy_(self, bstack11111ll111l_opy_, bstack1lllllllllll_opy_):
    if not bstack1lllllllllll_opy_: return
    try:
      bstack111111l11ll_opy_ = self.bstack1llllllllll1_opy_(bstack11111ll111l_opy_)
      with open(bstack111111l11ll_opy_, bstack1ll_opy_ (u"ࠥࡻࠧὠ")) as f:
        f.write(bstack1lllllllllll_opy_)
        self.logger.debug(bstack1ll_opy_ (u"ࠦࡘࡧࡶࡦࡦࠣࡲࡪࡽࠠࡆࡖࡤ࡫ࠥ࡬࡯ࡳࠢࡳࡩࡷࡩࡹࠣὡ"))
    except Exception as e:
      self.logger.error(bstack1ll_opy_ (u"࡛ࠧ࡮ࡢࡤ࡯ࡩࠥࡺ࡯ࠡࡵࡤࡺࡪࠦࡴࡩࡧࠣࡩࡹࡧࡧ࠭ࠢࡨࡶࡷࡵࡲ࠻ࠢࡾࢁࠧὢ").format(e))
  def bstack11111111ll1_opy_(self, bstack11111ll111l_opy_):
    try:
      bstack111111l11ll_opy_ = self.bstack1llllllllll1_opy_(bstack11111ll111l_opy_)
      if os.path.exists(bstack111111l11ll_opy_):
        with open(bstack111111l11ll_opy_, bstack1ll_opy_ (u"ࠨࡲࠣὣ")) as f:
          bstack1lllllllllll_opy_ = f.read().strip()
          return bstack1lllllllllll_opy_ if bstack1lllllllllll_opy_ else None
    except Exception as e:
      self.logger.error(bstack1ll_opy_ (u"ࠢࡇࡣ࡬ࡰࡪࡪࠠ࡭ࡱࡤࡨ࡮ࡴࡧࠡࡇࡗࡥ࡬࠲ࠠࡦࡴࡵࡳࡷࡀࠠࡼࡿࠥὤ").format(e))
  def bstack11111ll1l11_opy_(self, bstack11111ll111l_opy_, bstack1111111l111_opy_):
    bstack111111l1lll_opy_ = self.bstack11111111ll1_opy_(bstack11111ll111l_opy_)
    if bstack111111l1lll_opy_:
      try:
        bstack11111l1lll1_opy_ = self.bstack1111111ll11_opy_(bstack111111l1lll_opy_, bstack1111111l111_opy_)
        if not bstack11111l1lll1_opy_:
          self.logger.debug(bstack1ll_opy_ (u"ࠣࡒࡨࡶࡨࡿࠠࡣ࡫ࡱࡥࡷࡿࠠࡪࡵࠣࡹࡵࠦࡴࡰࠢࡧࡥࡹ࡫ࠠࠩࡇࡗࡥ࡬ࠦࡵ࡯ࡥ࡫ࡥࡳ࡭ࡥࡥࠫࠥὥ"))
          return True
        self.logger.debug(bstack1ll_opy_ (u"ࠤࡑࡩࡼࠦࡐࡦࡴࡦࡽࠥࡨࡩ࡯ࡣࡵࡽࠥࡼࡥࡳࡵ࡬ࡳࡳࠦࡡࡷࡣ࡬ࡰࡦࡨ࡬ࡦ࠮ࠣࡨࡴࡽ࡮࡭ࡱࡤࡨ࡮ࡴࡧࠡࡷࡳࡨࡦࡺࡥࠣὦ"))
        return False
      except Exception as e:
        self.logger.warn(bstack1ll_opy_ (u"ࠥࡊࡦ࡯࡬ࡦࡦࠣࡸࡴࠦࡣࡩࡧࡦ࡯ࠥ࡬࡯ࡳࠢࡥ࡭ࡳࡧࡲࡺࠢࡸࡴࡩࡧࡴࡦࡵ࠯ࠤࡺࡹࡩ࡯ࡩࠣࡩࡽ࡯ࡳࡵ࡫ࡱ࡫ࠥࡨࡩ࡯ࡣࡵࡽ࠿ࠦࡻࡾࠤὧ").format(e))
    return False
  def bstack1111111ll11_opy_(self, bstack111111l1lll_opy_, bstack1111111l111_opy_):
    try:
      headers = {
        bstack1ll_opy_ (u"ࠦࡎ࡬࠭ࡏࡱࡱࡩ࠲ࡓࡡࡵࡥ࡫ࠦὨ"): bstack111111l1lll_opy_
      }
      response = bstack1l111111_opy_(bstack1ll_opy_ (u"ࠬࡍࡅࡕࠩὩ"), bstack1111111l111_opy_, {}, {bstack1ll_opy_ (u"ࠨࡨࡦࡣࡧࡩࡷࡹࠢὪ"): headers})
      if response.status_code == 304:
        return False
      return True
    except Exception as e:
      raise(bstack1ll_opy_ (u"ࠢࡆࡴࡵࡳࡷࠦࡣࡩࡧࡦ࡯࡮ࡴࡧࠡࡨࡲࡶࠥࡖࡥࡳࡥࡼࠤࡧ࡯࡮ࡢࡴࡼࠤࡺࡶࡤࡢࡶࡨࡷ࠿ࠦࡻࡾࠤὫ").format(e))
  @measure(event_name=EVENTS.bstack11l1l1l1l1l_opy_, stage=STAGE.bstack1l1lll1ll1_opy_)
  def bstack11111l1111l_opy_(self, bstack1111111l111_opy_, bstack11111l11l1l_opy_):
    try:
      bstack111111l11l1_opy_ = self.bstack1lllllll1ll1_opy_()
      bstack111111llll1_opy_ = os.path.join(bstack111111l11l1_opy_, bstack1ll_opy_ (u"ࠨࡲࡨࡶࡨࡿ࠮ࡻ࡫ࡳࠫὬ"))
      bstack11111l1llll_opy_ = os.path.join(bstack111111l11l1_opy_, bstack11111l11l1l_opy_)
      if self.bstack11111ll1l11_opy_(bstack111111l11l1_opy_, bstack1111111l111_opy_): # if bstack111111111l1_opy_, bstack1l11lllll11_opy_ bstack1lllllllllll_opy_ is bstack1111111l1l1_opy_ to bstack111ll1111ll_opy_ version available (response 304)
        if os.path.exists(bstack11111l1llll_opy_):
          self.logger.info(bstack1ll_opy_ (u"ࠤࡓࡩࡷࡩࡹࠡࡤ࡬ࡲࡦࡸࡹࠡࡨࡲࡹࡳࡪࠠࡪࡰࠣࡿࢂ࠲ࠠࡴ࡭࡬ࡴࡵ࡯࡮ࡨࠢࡧࡳࡼࡴ࡬ࡰࡣࡧࠦὭ").format(bstack11111l1llll_opy_))
          return bstack11111l1llll_opy_
        if os.path.exists(bstack111111llll1_opy_):
          self.logger.info(bstack1ll_opy_ (u"ࠥࡔࡪࡸࡣࡺࠢࡽ࡭ࡵࠦࡦࡰࡷࡱࡨࠥ࡯࡮ࠡࡽࢀ࠰ࠥࡻ࡮ࡻ࡫ࡳࡴ࡮ࡴࡧࠣὮ").format(bstack111111llll1_opy_))
          return self.bstack11111111l11_opy_(bstack111111llll1_opy_, bstack11111l11l1l_opy_)
      self.logger.info(bstack1ll_opy_ (u"ࠦࡉࡵࡷ࡯࡮ࡲࡥࡩ࡯࡮ࡨࠢࡳࡩࡷࡩࡹࠡࡤ࡬ࡲࡦࡸࡹࠡࡨࡵࡳࡲࠦࡻࡾࠤὯ").format(bstack1111111l111_opy_))
      response = bstack1l111111_opy_(bstack1ll_opy_ (u"ࠬࡍࡅࡕࠩὰ"), bstack1111111l111_opy_, {}, {})
      if response.status_code == 200:
        bstack111111l1l1l_opy_ = response.headers.get(bstack1ll_opy_ (u"ࠨࡅࡕࡣࡪࠦά"), bstack1ll_opy_ (u"ࠢࠣὲ"))
        if bstack111111l1l1l_opy_:
          self.bstack1111111111l_opy_(bstack111111l11l1_opy_, bstack111111l1l1l_opy_)
        with open(bstack111111llll1_opy_, bstack1ll_opy_ (u"ࠨࡹࡥࠫέ")) as file:
          file.write(response.content)
        self.logger.info(bstack1ll_opy_ (u"ࠤࡇࡳࡼࡴ࡬ࡰࡣࡧࡩࡩࠦࡰࡦࡴࡦࡽࠥࡨࡩ࡯ࡣࡵࡽࠥࡧ࡮ࡥࠢࡶࡥࡻ࡫ࡤࠡࡣࡷࠤࢀࢃࠢὴ").format(bstack111111llll1_opy_))
        return self.bstack11111111l11_opy_(bstack111111llll1_opy_, bstack11111l11l1l_opy_)
      else:
        raise(bstack1ll_opy_ (u"ࠥࡊࡦ࡯࡬ࡦࡦࠣࡸࡴࠦࡤࡰࡹࡱࡰࡴࡧࡤࠡࡶ࡫ࡩࠥ࡬ࡩ࡭ࡧ࠱ࠤࡘࡺࡡࡵࡷࡶࠤࡨࡵࡤࡦ࠼ࠣࡿࢂࠨή").format(response.status_code))
    except Exception as e:
      self.logger.error(bstack1ll_opy_ (u"࡚ࠦࡴࡡࡣ࡮ࡨࠤࡹࡵࠠࡥࡱࡺࡲࡱࡵࡡࡥࠢࡳࡩࡷࡩࡹࠡࡤ࡬ࡲࡦࡸࡹ࠻ࠢࡾࢁࠧὶ").format(e))
  def bstack11111l11l11_opy_(self, bstack1111111l111_opy_, bstack11111l11l1l_opy_):
    try:
      retry = 2
      bstack11111l1llll_opy_ = None
      bstack111111l1111_opy_ = False
      while retry > 0:
        bstack11111l1llll_opy_ = self.bstack11111l1111l_opy_(bstack1111111l111_opy_, bstack11111l11l1l_opy_)
        bstack111111l1111_opy_ = self.bstack111111ll11l_opy_(bstack1111111l111_opy_, bstack11111l11l1l_opy_, bstack11111l1llll_opy_)
        if bstack111111l1111_opy_:
          break
        retry -= 1
      return bstack11111l1llll_opy_, bstack111111l1111_opy_
    except Exception as e:
      self.logger.error(bstack1ll_opy_ (u"࡛ࠧ࡮ࡢࡤ࡯ࡩࠥࡺ࡯ࠡࡩࡨࡸࠥࡶࡥࡳࡥࡼࠤࡧ࡯࡮ࡢࡴࡼࠤࡵࡧࡴࡩࠤί").format(e))
    return bstack11111l1llll_opy_, False
  def bstack111111ll11l_opy_(self, bstack1111111l111_opy_, bstack11111l11l1l_opy_, bstack11111l1llll_opy_, bstack111111l1ll1_opy_ = 0):
    if bstack111111l1ll1_opy_ > 1:
      return False
    if bstack11111l1llll_opy_ == None or os.path.exists(bstack11111l1llll_opy_) == False:
      self.logger.warn(bstack1ll_opy_ (u"ࠨࡐࡦࡴࡦࡽࠥࡶࡡࡵࡪࠣࡲࡴࡺࠠࡧࡱࡸࡲࡩ࠲ࠠࡳࡧࡷࡶࡾ࡯࡮ࡨࠢࡧࡳࡼࡴ࡬ࡰࡣࡧࠦὸ"))
      return False
    bstack1lllllllll1l_opy_ = bstack1ll_opy_ (u"ࡲࠣࡠ࠱࠮ࡅࡶࡥࡳࡥࡼ࠳ࡨࡲࡩࠡ࡞ࡧ࠯ࡡ࠴࡜ࡥ࠭࡟࠲ࡡࡪࠫࠣό")
    command = bstack1ll_opy_ (u"ࠨࡽࢀࠤ࠲࠳ࡶࡦࡴࡶ࡭ࡴࡴࠧὺ").format(bstack11111l1llll_opy_)
    bstack1111111l1ll_opy_ = subprocess.check_output(command, shell=True, text=True)
    if re.match(bstack1lllllllll1l_opy_, bstack1111111l1ll_opy_) != None:
      return True
    else:
      self.logger.error(bstack1ll_opy_ (u"ࠤࡓࡩࡷࡩࡹࠡࡸࡨࡶࡸ࡯࡯࡯ࠢࡦ࡬ࡪࡩ࡫ࠡࡨࡤ࡭ࡱ࡫ࡤࠣύ"))
      return False
  def bstack11111111l11_opy_(self, bstack111111llll1_opy_, bstack11111l11l1l_opy_):
    try:
      working_dir = os.path.dirname(bstack111111llll1_opy_)
      shutil.unpack_archive(bstack111111llll1_opy_, working_dir)
      bstack11111l1llll_opy_ = os.path.join(working_dir, bstack11111l11l1l_opy_)
      os.chmod(bstack11111l1llll_opy_, 0o755)
      return bstack11111l1llll_opy_
    except Exception as e:
      self.logger.error(bstack1ll_opy_ (u"࡙ࠥࡳࡧࡢ࡭ࡧࠣࡸࡴࠦࡵ࡯ࡼ࡬ࡴࠥࡶࡥࡳࡥࡼࠤࡧ࡯࡮ࡢࡴࡼࠦὼ"))
  def bstack11111l11ll1_opy_(self):
    try:
      bstack1lllllllll11_opy_ = self.config.get(bstack1ll_opy_ (u"ࠫࡵ࡫ࡲࡤࡻࠪώ"))
      bstack11111l11ll1_opy_ = bstack1lllllllll11_opy_ or (bstack1lllllllll11_opy_ is None and self.bstack11ll11ll1l_opy_)
      if not bstack11111l11ll1_opy_ or self.config.get(bstack1ll_opy_ (u"ࠬ࡬ࡲࡢ࡯ࡨࡻࡴࡸ࡫ࠨ὾"), None) not in bstack11l1l11l111_opy_:
        return False
      self.bstack11l11l1111_opy_ = True
      return True
    except Exception as e:
      self.logger.error(bstack1ll_opy_ (u"ࠨࡕ࡯ࡣࡥࡰࡪࠦࡴࡰࠢࡧࡩࡹ࡫ࡣࡵࠢࡳࡩࡷࡩࡹ࠭ࠢࡈࡼࡨ࡫ࡰࡵ࡫ࡲࡲࠥࢁࡽࠣ὿").format(e))
  def bstack11111ll1111_opy_(self):
    try:
      bstack11111ll1111_opy_ = self.percy_capture_mode
      return bstack11111ll1111_opy_
    except Exception as e:
      self.logger.error(bstack1ll_opy_ (u"ࠢࡖࡰࡤࡦࡱ࡫ࠠࡵࡱࠣࡨࡪࡺࡥࡤࡶࠣࡴࡪࡸࡣࡺࠢࡦࡥࡵࡺࡵࡳࡧࠣࡱࡴࡪࡥ࠭ࠢࡈࡼࡨ࡫ࡰࡵ࡫ࡲࡲࠥࢁࡽࠣᾀ").format(e))
  def init(self, bstack11ll11ll1l_opy_, config, logger):
    self.bstack11ll11ll1l_opy_ = bstack11ll11ll1l_opy_
    self.config = config
    self.logger = logger
    if not self.bstack11111l11ll1_opy_():
      return
    self.bstack1111111lll1_opy_ = config.get(bstack1ll_opy_ (u"ࠨࡲࡨࡶࡨࡿࡏࡱࡶ࡬ࡳࡳࡹࠧᾁ"), {})
    self.percy_capture_mode = config.get(bstack1ll_opy_ (u"ࠩࡳࡩࡷࡩࡹࡄࡣࡳࡸࡺࡸࡥࡎࡱࡧࡩࠬᾂ"))
    try:
      bstack1111111l111_opy_, bstack11111l11l1l_opy_ = self.bstack11111l11lll_opy_()
      self.bstack111l1ll1l11_opy_ = bstack11111l11l1l_opy_
      bstack11111l1llll_opy_, bstack111111l1111_opy_ = self.bstack11111l11l11_opy_(bstack1111111l111_opy_, bstack11111l11l1l_opy_)
      if bstack111111l1111_opy_:
        self.binary_path = bstack11111l1llll_opy_
        thread = Thread(target=self.bstack1llllllll111_opy_)
        thread.start()
      else:
        self.bstack111111lll11_opy_ = True
        self.logger.error(bstack1ll_opy_ (u"ࠥࡍࡳࡼࡡ࡭࡫ࡧࠤࡵ࡫ࡲࡤࡻࠣࡴࡦࡺࡨࠡࡨࡲࡹࡳࡪࠠ࠮ࠢࡾࢁ࠱ࠦࡕ࡯ࡣࡥࡰࡪࠦࡴࡰࠢࡶࡸࡦࡸࡴࠡࡒࡨࡶࡨࡿࠢᾃ").format(bstack11111l1llll_opy_))
    except Exception as e:
      self.logger.error(bstack1ll_opy_ (u"࡚ࠦࡴࡡࡣ࡮ࡨࠤࡹࡵࠠࡴࡶࡤࡶࡹࠦࡰࡦࡴࡦࡽ࠱ࠦࡅࡹࡥࡨࡴࡹ࡯࡯࡯ࠢࡾࢁࠧᾄ").format(e))
  def bstack11111ll1ll1_opy_(self):
    try:
      logfile = os.path.join(self.working_dir, bstack1ll_opy_ (u"ࠬࡲ࡯ࡨࠩᾅ"), bstack1ll_opy_ (u"࠭ࡰࡦࡴࡦࡽ࠳ࡲ࡯ࡨࠩᾆ"))
      os.makedirs(os.path.dirname(logfile)) if not os.path.exists(os.path.dirname(logfile)) else None
      self.logger.debug(bstack1ll_opy_ (u"ࠢࡑࡷࡶ࡬࡮ࡴࡧࠡࡲࡨࡶࡨࡿࠠ࡭ࡱࡪࡷࠥࡧࡴࠡࡽࢀࠦᾇ").format(logfile))
      self.bstack11111l1ll11_opy_ = logfile
    except Exception as e:
      self.logger.error(bstack1ll_opy_ (u"ࠣࡗࡱࡥࡧࡲࡥࠡࡶࡲࠤࡸ࡫ࡴࠡࡲࡨࡶࡨࡿࠠ࡭ࡱࡪࠤࡵࡧࡴࡩ࠮ࠣࡉࡽࡩࡥࡱࡶ࡬ࡳࡳࠦࡻࡾࠤᾈ").format(e))
  @measure(event_name=EVENTS.bstack11l1l111ll1_opy_, stage=STAGE.bstack1l1lll1ll1_opy_)
  def bstack1llllllll111_opy_(self):
    bstack11111l11111_opy_ = self.bstack1lllllll1l11_opy_()
    if bstack11111l11111_opy_ == None:
      self.bstack111111lll11_opy_ = True
      self.logger.error(bstack1ll_opy_ (u"ࠤࡓࡩࡷࡩࡹࠡࡶࡲ࡯ࡪࡴࠠ࡯ࡱࡷࠤ࡫ࡵࡵ࡯ࡦ࠯ࠤࡋࡧࡩ࡭ࡧࡧࠤࡹࡵࠠࡴࡶࡤࡶࡹࠦࡰࡦࡴࡦࡽࠧᾉ"))
      return False
    bstack111111l1l11_opy_ = [bstack1ll_opy_ (u"ࠥࡥࡵࡶ࠺ࡦࡺࡨࡧ࠿ࡹࡴࡢࡴࡷࠦᾊ") if self.bstack11ll11ll1l_opy_ else bstack1ll_opy_ (u"ࠫࡪࡾࡥࡤ࠼ࡶࡸࡦࡸࡴࠨᾋ")]
    bstack111l11ll111_opy_ = self.bstack11111111lll_opy_()
    if bstack111l11ll111_opy_ != None:
      bstack111111l1l11_opy_.append(bstack1ll_opy_ (u"ࠧ࠳ࡣࠡࡽࢀࠦᾌ").format(bstack111l11ll111_opy_))
    env = os.environ.copy()
    env[bstack1ll_opy_ (u"ࠨࡐࡆࡔࡆ࡝ࡤ࡚ࡏࡌࡇࡑࠦᾍ")] = bstack11111l11111_opy_
    env[bstack1ll_opy_ (u"ࠢࡕࡊࡢࡆ࡚ࡏࡌࡅࡡࡘ࡙ࡎࡊࠢᾎ")] = os.environ.get(bstack1ll_opy_ (u"ࠨࡄࡕࡓ࡜࡙ࡅࡓࡕࡗࡅࡈࡑ࡟ࡕࡇࡖࡘࡍ࡛ࡂࡠࡗࡘࡍࡉ࠭ᾏ"), bstack1ll_opy_ (u"ࠩࠪᾐ"))
    bstack1111111llll_opy_ = [self.binary_path]
    self.bstack11111ll1ll1_opy_()
    self.bstack1llllllll1ll_opy_ = self.bstack1111111l11l_opy_(bstack1111111llll_opy_ + bstack111111l1l11_opy_, env)
    self.logger.debug(bstack1ll_opy_ (u"ࠥࡗࡹࡧࡲࡵ࡫ࡱ࡫ࠥࡎࡥࡢ࡮ࡷ࡬ࠥࡉࡨࡦࡥ࡮ࠦᾑ"))
    bstack111111l1ll1_opy_ = 0
    while self.bstack1llllllll1ll_opy_.poll() == None:
      bstack11111ll1l1l_opy_ = self.bstack11111111111_opy_()
      if bstack11111ll1l1l_opy_:
        self.logger.debug(bstack1ll_opy_ (u"ࠦࡍ࡫ࡡ࡭ࡶ࡫ࠤࡈ࡮ࡥࡤ࡭ࠣࡷࡺࡩࡣࡦࡵࡶࡪࡺࡲࠢᾒ"))
        self.bstack11111l1l11l_opy_ = True
        return True
      bstack111111l1ll1_opy_ += 1
      self.logger.debug(bstack1ll_opy_ (u"ࠧࡎࡥࡢ࡮ࡷ࡬ࠥࡉࡨࡦࡥ࡮ࠤࡗ࡫ࡴࡳࡻࠣ࠱ࠥࢁࡽࠣᾓ").format(bstack111111l1ll1_opy_))
      time.sleep(2)
    self.logger.error(bstack1ll_opy_ (u"ࠨࡆࡢ࡫࡯ࡩࡩࠦࡴࡰࠢࡶࡸࡦࡸࡴࠡࡲࡨࡶࡨࡿࠬࠡࡊࡨࡥࡱࡺࡨࠡࡅ࡫ࡩࡨࡱࠠࡇࡣ࡬ࡰࡪࡪࠠࡢࡨࡷࡩࡷࠦࡻࡾࠢࡤࡸࡹ࡫࡭ࡱࡶࡶࠦᾔ").format(bstack111111l1ll1_opy_))
    self.bstack111111lll11_opy_ = True
    return False
  def bstack11111111111_opy_(self, bstack111111l1ll1_opy_ = 0):
    if bstack111111l1ll1_opy_ > 10:
      return False
    try:
      bstack11111ll11l1_opy_ = os.environ.get(bstack1ll_opy_ (u"ࠧࡑࡇࡕࡇ࡞ࡥࡓࡆࡔ࡙ࡉࡗࡥࡁࡅࡆࡕࡉࡘ࡙ࠧᾕ"), bstack1ll_opy_ (u"ࠨࡪࡷࡸࡵࡀ࠯࠰࡮ࡲࡧࡦࡲࡨࡰࡵࡷ࠾࠺࠹࠳࠹ࠩᾖ"))
      bstack111111ll111_opy_ = bstack11111ll11l1_opy_ + bstack11l1l11l1ll_opy_
      response = requests.get(bstack111111ll111_opy_)
      data = response.json()
      self.percy_build_id = data.get(bstack1ll_opy_ (u"ࠩࡥࡹ࡮ࡲࡤࠨᾗ"), {}).get(bstack1ll_opy_ (u"ࠪ࡭ࡩ࠭ᾘ"), None)
      return True
    except:
      self.logger.debug(bstack1ll_opy_ (u"ࠦࡊࡸࡲࡰࡴࠣࡳࡨࡩࡵࡳࡴࡨࡨࠥࡽࡨࡪ࡮ࡨࠤࡵࡸ࡯ࡤࡧࡶࡷ࡮ࡴࡧࠡࡪࡨࡥࡱࡺࡨࠡࡥ࡫ࡩࡨࡱࠠࡳࡧࡶࡴࡴࡴࡳࡦࠤᾙ"))
      return False
  def bstack1lllllll1l11_opy_(self):
    bstack11111l1l1l1_opy_ = bstack1ll_opy_ (u"ࠬࡧࡰࡱࠩᾚ") if self.bstack11ll11ll1l_opy_ else bstack1ll_opy_ (u"࠭ࡡࡶࡶࡲࡱࡦࡺࡥࠨᾛ")
    bstack111111lllll_opy_ = bstack1ll_opy_ (u"ࠢࡶࡰࡧࡩ࡫࡯࡮ࡦࡦࠥᾜ") if self.config.get(bstack1ll_opy_ (u"ࠨࡲࡨࡶࡨࡿࠧᾝ")) is None else True
    bstack11l1lll1l1l_opy_ = bstack1ll_opy_ (u"ࠤࡤࡴ࡮࠵ࡡࡱࡲࡢࡴࡪࡸࡣࡺ࠱ࡪࡩࡹࡥࡰࡳࡱ࡭ࡩࡨࡺ࡟ࡵࡱ࡮ࡩࡳࡅ࡮ࡢ࡯ࡨࡁࢀࢃࠦࡵࡻࡳࡩࡂࢁࡽࠧࡲࡨࡶࡨࡿ࠽ࡼࡿࠥᾞ").format(self.config[bstack1ll_opy_ (u"ࠪࡴࡷࡵࡪࡦࡥࡷࡒࡦࡳࡥࠨᾟ")], bstack11111l1l1l1_opy_, bstack111111lllll_opy_)
    if self.percy_capture_mode:
      bstack11l1lll1l1l_opy_ += bstack1ll_opy_ (u"ࠦࠫࡶࡥࡳࡥࡼࡣࡨࡧࡰࡵࡷࡵࡩࡤࡳ࡯ࡥࡧࡀࡿࢂࠨᾠ").format(self.percy_capture_mode)
    uri = bstack1l1lll11ll_opy_(bstack11l1lll1l1l_opy_)
    try:
      response = bstack1l111111_opy_(bstack1ll_opy_ (u"ࠬࡍࡅࡕࠩᾡ"), uri, {}, {bstack1ll_opy_ (u"࠭ࡡࡶࡶ࡫ࠫᾢ"): (self.config[bstack1ll_opy_ (u"ࠧࡶࡵࡨࡶࡓࡧ࡭ࡦࠩᾣ")], self.config[bstack1ll_opy_ (u"ࠨࡣࡦࡧࡪࡹࡳࡌࡧࡼࠫᾤ")])})
      if response.status_code == 200:
        data = response.json()
        self.bstack11l11l1111_opy_ = data.get(bstack1ll_opy_ (u"ࠩࡶࡹࡨࡩࡥࡴࡵࠪᾥ"))
        self.percy_capture_mode = data.get(bstack1ll_opy_ (u"ࠪࡴࡪࡸࡣࡺࡡࡦࡥࡵࡺࡵࡳࡧࡢࡱࡴࡪࡥࠨᾦ"))
        os.environ[bstack1ll_opy_ (u"ࠫࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡔࡊࡘࡃ࡚ࠩᾧ")] = str(self.bstack11l11l1111_opy_)
        os.environ[bstack1ll_opy_ (u"ࠬࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣࡕࡋࡒࡄ࡛ࡢࡇࡆࡖࡔࡖࡔࡈࡣࡒࡕࡄࡆࠩᾨ")] = str(self.percy_capture_mode)
        if bstack111111lllll_opy_ == bstack1ll_opy_ (u"ࠨࡵ࡯ࡦࡨࡪ࡮ࡴࡥࡥࠤᾩ") and str(self.bstack11l11l1111_opy_).lower() == bstack1ll_opy_ (u"ࠢࡵࡴࡸࡩࠧᾪ"):
          self.bstack11l111l1l_opy_ = True
        if bstack1ll_opy_ (u"ࠣࡶࡲ࡯ࡪࡴࠢᾫ") in data:
          return data[bstack1ll_opy_ (u"ࠤࡷࡳࡰ࡫࡮ࠣᾬ")]
        else:
          raise bstack1ll_opy_ (u"ࠪࡘࡴࡱࡥ࡯ࠢࡑࡳࡹࠦࡆࡰࡷࡱࡨࠥ࠳ࠠࡼࡿࠪᾭ").format(data)
      else:
        raise bstack1ll_opy_ (u"ࠦࡋࡧࡩ࡭ࡧࡧࠤࡹࡵࠠࡧࡧࡷࡧ࡭ࠦࡰࡦࡴࡦࡽࠥࡺ࡯࡬ࡧࡱ࠰ࠥࡘࡥࡴࡲࡲࡲࡸ࡫ࠠࡴࡶࡤࡸࡺࡹࠠ࠮ࠢࡾࢁ࠱ࠦࡒࡦࡵࡳࡳࡳࡹࡥࠡࡄࡲࡨࡾࠦ࠭ࠡࡽࢀࠦᾮ").format(response.status_code, response.json())
    except Exception as e:
      self.logger.error(bstack1ll_opy_ (u"ࠧࡋࡸࡤࡧࡳࡸ࡮ࡵ࡮ࠡ࡫ࡱࠤࡨࡸࡥࡢࡶ࡬ࡲ࡬ࠦࡰࡦࡴࡦࡽࠥࡶࡲࡰ࡬ࡨࡧࡹࠨᾯ").format(e))
  def bstack11111111lll_opy_(self):
    bstack11111l111l1_opy_ = os.path.join(tempfile.gettempdir(), bstack1ll_opy_ (u"ࠨࡰࡦࡴࡦࡽࡈࡵ࡮ࡧ࡫ࡪ࠲࡯ࡹ࡯࡯ࠤᾰ"))
    try:
      if bstack1ll_opy_ (u"ࠧࡷࡧࡵࡷ࡮ࡵ࡮ࠨᾱ") not in self.bstack1111111lll1_opy_:
        self.bstack1111111lll1_opy_[bstack1ll_opy_ (u"ࠨࡸࡨࡶࡸ࡯࡯࡯ࠩᾲ")] = 2
      with open(bstack11111l111l1_opy_, bstack1ll_opy_ (u"ࠩࡺࠫᾳ")) as fp:
        json.dump(self.bstack1111111lll1_opy_, fp)
      return bstack11111l111l1_opy_
    except Exception as e:
      self.logger.error(bstack1ll_opy_ (u"࡙ࠥࡳࡧࡢ࡭ࡧࠣࡸࡴࠦࡣࡳࡧࡤࡸࡪࠦࡰࡦࡴࡦࡽࠥࡩ࡯࡯ࡨ࠯ࠤࡊࡾࡣࡦࡲࡷ࡭ࡴࡴࠠࡼࡿࠥᾴ").format(e))
  def bstack1111111l11l_opy_(self, cmd, env = os.environ.copy()):
    try:
      if self.bstack111111ll1l1_opy_ == bstack1ll_opy_ (u"ࠫࡼ࡯࡮ࠨ᾵"):
        bstack1lllllll1l1l_opy_ = [bstack1ll_opy_ (u"ࠬࡩ࡭ࡥ࠰ࡨࡼࡪ࠭ᾶ"), bstack1ll_opy_ (u"࠭࠯ࡤࠩᾷ")]
        cmd = bstack1lllllll1l1l_opy_ + cmd
      cmd = bstack1ll_opy_ (u"ࠧࠡࠩᾸ").join(cmd)
      self.logger.debug(bstack1ll_opy_ (u"ࠣࡔࡸࡲࡳ࡯࡮ࡨࠢࡾࢁࠧᾹ").format(cmd))
      with open(self.bstack11111l1ll11_opy_, bstack1ll_opy_ (u"ࠤࡤࠦᾺ")) as bstack111111lll1l_opy_:
        process = subprocess.Popen(cmd, shell=True, stdout=bstack111111lll1l_opy_, text=True, stderr=bstack111111lll1l_opy_, env=env, universal_newlines=True)
      return process
    except Exception as e:
      self.bstack111111lll11_opy_ = True
      self.logger.error(bstack1ll_opy_ (u"ࠥࡊࡦ࡯࡬ࡦࡦࠣࡸࡴࠦࡳࡵࡣࡵࡸࠥࡶࡥࡳࡥࡼࠤࡼ࡯ࡴࡩࠢࡦࡱࡩࠦ࠭ࠡࡽࢀ࠰ࠥࡋࡸࡤࡧࡳࡸ࡮ࡵ࡮࠻ࠢࡾࢁࠧΆ").format(cmd, e))
  def shutdown(self):
    try:
      if self.bstack11111l1l11l_opy_:
        self.logger.info(bstack1ll_opy_ (u"ࠦࡘࡺ࡯ࡱࡲ࡬ࡲ࡬ࠦࡐࡦࡴࡦࡽࠧᾼ"))
        cmd = [self.binary_path, bstack1ll_opy_ (u"ࠧ࡫ࡸࡦࡥ࠽ࡷࡹࡵࡰࠣ᾽")]
        self.bstack1111111l11l_opy_(cmd)
        self.bstack11111l1l11l_opy_ = False
    except Exception as e:
      self.logger.error(bstack1ll_opy_ (u"ࠨࡆࡢ࡫࡯ࡩࡩࠦࡴࡰࠢࡶࡸࡴࡶࠠࡴࡧࡶࡷ࡮ࡵ࡮ࠡࡹ࡬ࡸ࡭ࠦࡣࡰ࡯ࡰࡥࡳࡪࠠ࠮ࠢࡾࢁ࠱ࠦࡅࡹࡥࡨࡴࡹ࡯࡯࡯࠼ࠣࡿࢂࠨι").format(cmd, e))
  def bstack11ll1llll_opy_(self):
    if not self.bstack11l11l1111_opy_:
      return
    try:
      bstack111111111ll_opy_ = 0
      while not self.bstack11111l1l11l_opy_ and bstack111111111ll_opy_ < self.bstack11111l111ll_opy_:
        if self.bstack111111lll11_opy_:
          self.logger.info(bstack1ll_opy_ (u"ࠢࡑࡧࡵࡧࡾࠦࡳࡦࡶࡸࡴࠥ࡬ࡡࡪ࡮ࡨࡨࠧ᾿"))
          return
        time.sleep(1)
        bstack111111111ll_opy_ += 1
      os.environ[bstack1ll_opy_ (u"ࠨࡒࡈࡖࡈ࡟࡟ࡃࡇࡖࡘࡤࡖࡌࡂࡖࡉࡓࡗࡓࠧ῀")] = str(self.bstack11111l1l111_opy_())
      self.logger.info(bstack1ll_opy_ (u"ࠤࡓࡩࡷࡩࡹࠡࡵࡨࡸࡺࡶࠠࡤࡱࡰࡴࡱ࡫ࡴࡦࡦࠥ῁"))
    except Exception as e:
      self.logger.error(bstack1ll_opy_ (u"࡙ࠥࡳࡧࡢ࡭ࡧࠣࡸࡴࠦࡳࡦࡶࡸࡴࠥࡶࡥࡳࡥࡼ࠰ࠥࡋࡸࡤࡧࡳࡸ࡮ࡵ࡮ࠡࡽࢀࠦῂ").format(e))
  def bstack11111l1l111_opy_(self):
    if self.bstack11ll11ll1l_opy_:
      return
    try:
      bstack11111l1l1ll_opy_ = [platform[bstack1ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࡓࡧ࡭ࡦࠩῃ")].lower() for platform in self.config.get(bstack1ll_opy_ (u"ࠬࡶ࡬ࡢࡶࡩࡳࡷࡳࡳࠨῄ"), [])]
      bstack111111l111l_opy_ = sys.maxsize
      bstack1111111ll1l_opy_ = bstack1ll_opy_ (u"࠭ࠧ῅")
      for browser in bstack11111l1l1ll_opy_:
        if browser in self.bstack1lllllll1lll_opy_:
          bstack11111111l1l_opy_ = self.bstack1lllllll1lll_opy_[browser]
        if bstack11111111l1l_opy_ < bstack111111l111l_opy_:
          bstack111111l111l_opy_ = bstack11111111l1l_opy_
          bstack1111111ll1l_opy_ = browser
      return bstack1111111ll1l_opy_
    except Exception as e:
      self.logger.error(bstack1ll_opy_ (u"ࠢࡖࡰࡤࡦࡱ࡫ࠠࡵࡱࠣࡪ࡮ࡴࡤࠡࡤࡨࡷࡹࠦࡰ࡭ࡣࡷࡪࡴࡸ࡭࠭ࠢࡈࡼࡨ࡫ࡰࡵ࡫ࡲࡲࠥࢁࡽࠣῆ").format(e))
  @classmethod
  def bstack11ll11lll1_opy_(self):
    return os.getenv(bstack1ll_opy_ (u"ࠨࡄࡕࡓ࡜࡙ࡅࡓࡕࡗࡅࡈࡑ࡟ࡑࡇࡕࡇ࡞࠭ῇ"), bstack1ll_opy_ (u"ࠩࡉࡥࡱࡹࡥࠨῈ")).lower()
  @classmethod
  def bstack1l1l1111l1_opy_(self):
    return os.getenv(bstack1ll_opy_ (u"ࠪࡆࡗࡕࡗࡔࡇࡕࡗ࡙ࡇࡃࡌࡡࡓࡉࡗࡉ࡙ࡠࡅࡄࡔ࡙࡛ࡒࡆࡡࡐࡓࡉࡋࠧΈ"), bstack1ll_opy_ (u"ࠫࠬῊ"))
  @classmethod
  def bstack1l1l1111l1l_opy_(cls, value):
    cls.bstack11l111l1l_opy_ = value
  @classmethod
  def bstack1llllllll1l1_opy_(cls):
    return cls.bstack11l111l1l_opy_
  @classmethod
  def bstack1l1l111l111_opy_(cls, value):
    cls.percy_build_id = value
  @classmethod
  def bstack1llllllll11l_opy_(cls):
    return cls.percy_build_id