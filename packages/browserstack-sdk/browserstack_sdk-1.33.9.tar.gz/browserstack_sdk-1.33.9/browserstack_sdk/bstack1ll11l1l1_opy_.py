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
import json
import multiprocessing
import os
from bstack_utils.config import Config
class bstack1l1lll111l_opy_():
  def __init__(self, args, logger, bstack11111ll111_opy_, bstack1111111l1l_opy_, bstack1llllll1l11_opy_):
    self.args = args
    self.logger = logger
    self.bstack11111ll111_opy_ = bstack11111ll111_opy_
    self.bstack1111111l1l_opy_ = bstack1111111l1l_opy_
    self.bstack1llllll1l11_opy_ = bstack1llllll1l11_opy_
  def bstack1lll1ll1ll_opy_(self, bstack11111l11ll_opy_, bstack1l1ll1l11_opy_, bstack1llllll11ll_opy_=False):
    bstack111llll1_opy_ = []
    manager = multiprocessing.Manager()
    bstack1lllllll11l_opy_ = manager.list()
    bstack1ll1l1l111_opy_ = Config.bstack11lll1111_opy_()
    if bstack1llllll11ll_opy_:
      for index, platform in enumerate(self.bstack11111ll111_opy_[bstack1ll_opy_ (u"ࠫࡵࡲࡡࡵࡨࡲࡶࡲࡹࠧვ")]):
        if index == 0:
          bstack1l1ll1l11_opy_[bstack1ll_opy_ (u"ࠬ࡬ࡩ࡭ࡧࡢࡲࡦࡳࡥࠨზ")] = self.args
        bstack111llll1_opy_.append(multiprocessing.Process(name=str(index),
                                                    target=bstack11111l11ll_opy_,
                                                    args=(bstack1l1ll1l11_opy_, bstack1lllllll11l_opy_)))
    else:
      for index, platform in enumerate(self.bstack11111ll111_opy_[bstack1ll_opy_ (u"࠭ࡰ࡭ࡣࡷࡪࡴࡸ࡭ࡴࠩთ")]):
        bstack111llll1_opy_.append(multiprocessing.Process(name=str(index),
                                                    target=bstack11111l11ll_opy_,
                                                    args=(bstack1l1ll1l11_opy_, bstack1lllllll11l_opy_)))
    i = 0
    for t in bstack111llll1_opy_:
      try:
        if bstack1ll1l1l111_opy_.get_property(bstack1ll_opy_ (u"ࠧࡣࡵࡷࡥࡨࡱ࡟ࡴࡧࡶࡷ࡮ࡵ࡮ࠨი")):
          os.environ[bstack1ll_opy_ (u"ࠨࡅࡘࡖࡗࡋࡎࡕࡡࡓࡐࡆ࡚ࡆࡐࡔࡐࡣࡉࡇࡔࡂࠩკ")] = json.dumps(self.bstack11111ll111_opy_[bstack1ll_opy_ (u"ࠩࡳࡰࡦࡺࡦࡰࡴࡰࡷࠬლ")][i % self.bstack1llllll1l11_opy_])
      except Exception as e:
        self.logger.debug(bstack1ll_opy_ (u"ࠥࡉࡷࡸ࡯ࡳࠢࡺ࡬࡮ࡲࡥࠡࡵࡷࡳࡷ࡯࡮ࡨࠢࡦࡹࡷࡸࡥ࡯ࡶࠣࡴࡱࡧࡴࡧࡱࡵࡱࠥࡪࡥࡵࡣ࡬ࡰࡸࡀࠠࡼࡿࠥმ").format(str(e)))
      i += 1
      t.start()
    for t in bstack111llll1_opy_:
      t.join()
    return list(bstack1lllllll11l_opy_)