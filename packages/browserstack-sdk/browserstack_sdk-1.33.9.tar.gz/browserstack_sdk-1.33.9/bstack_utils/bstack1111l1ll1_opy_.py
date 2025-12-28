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
from bstack_utils.bstack11l1l1lll1_opy_ import get_logger
logger = get_logger(__name__)
class bstack11l1lll1lll_opy_(object):
  bstack1l11l11l1l_opy_ = os.path.join(os.path.expanduser(bstack1ll_opy_ (u"ࠩࢁࠫឰ")), bstack1ll_opy_ (u"ࠪ࠲ࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭ࠪឱ"))
  bstack11l1llll1l1_opy_ = os.path.join(bstack1l11l11l1l_opy_, bstack1ll_opy_ (u"ࠫࡨࡵ࡭࡮ࡣࡱࡨࡸ࠴ࡪࡴࡱࡱࠫឲ"))
  commands_to_wrap = None
  perform_scan = None
  bstack1ll111l11_opy_ = None
  bstack1l1lllllll_opy_ = None
  bstack11ll11l1l1l_opy_ = None
  bstack11ll111l111_opy_ = None
  def __new__(cls):
    if not hasattr(cls, bstack1ll_opy_ (u"ࠬ࡯࡮ࡴࡶࡤࡲࡨ࡫ࠧឳ")):
      cls.instance = super(bstack11l1lll1lll_opy_, cls).__new__(cls)
      cls.instance.bstack11l1llll111_opy_()
    return cls.instance
  def bstack11l1llll111_opy_(self):
    try:
      with open(self.bstack11l1llll1l1_opy_, bstack1ll_opy_ (u"࠭ࡲࠨ឴")) as bstack11l11l111l_opy_:
        bstack11l1llll11l_opy_ = bstack11l11l111l_opy_.read()
        data = json.loads(bstack11l1llll11l_opy_)
        if bstack1ll_opy_ (u"ࠧࡤࡱࡰࡱࡦࡴࡤࡴࠩ឵") in data:
          self.bstack11ll1l11111_opy_(data[bstack1ll_opy_ (u"ࠨࡥࡲࡱࡲࡧ࡮ࡥࡵࠪា")])
        if bstack1ll_opy_ (u"ࠩࡶࡧࡷ࡯ࡰࡵࡵࠪិ") in data:
          self.bstack1l111lll_opy_(data[bstack1ll_opy_ (u"ࠪࡷࡨࡸࡩࡱࡶࡶࠫី")])
        if bstack1ll_opy_ (u"ࠫࡳࡵ࡮ࡃࡕࡷࡥࡨࡱࡉ࡯ࡨࡵࡥࡆ࠷࠱ࡺࡅ࡫ࡶࡴࡳࡥࡐࡲࡷ࡭ࡴࡴࡳࠨឹ") in data:
          self.bstack11l1lll1ll1_opy_(data[bstack1ll_opy_ (u"ࠬࡴ࡯࡯ࡄࡖࡸࡦࡩ࡫ࡊࡰࡩࡶࡦࡇ࠱࠲ࡻࡆ࡬ࡷࡵ࡭ࡦࡑࡳࡸ࡮ࡵ࡮ࡴࠩឺ")])
    except:
      pass
  def bstack11l1lll1ll1_opy_(self, bstack11ll111l111_opy_):
    if bstack11ll111l111_opy_ != None:
      self.bstack11ll111l111_opy_ = bstack11ll111l111_opy_
  def bstack1l111lll_opy_(self, scripts):
    if scripts != None:
      self.perform_scan = scripts.get(bstack1ll_opy_ (u"࠭ࡳࡤࡣࡱࠫុ"),bstack1ll_opy_ (u"ࠧࠨូ"))
      self.bstack1ll111l11_opy_ = scripts.get(bstack1ll_opy_ (u"ࠨࡩࡨࡸࡗ࡫ࡳࡶ࡮ࡷࡷࠬួ"),bstack1ll_opy_ (u"ࠩࠪើ"))
      self.bstack1l1lllllll_opy_ = scripts.get(bstack1ll_opy_ (u"ࠪ࡫ࡪࡺࡒࡦࡵࡸࡰࡹࡹࡓࡶ࡯ࡰࡥࡷࡿࠧឿ"),bstack1ll_opy_ (u"ࠫࠬៀ"))
      self.bstack11ll11l1l1l_opy_ = scripts.get(bstack1ll_opy_ (u"ࠬࡹࡡࡷࡧࡕࡩࡸࡻ࡬ࡵࡵࠪេ"),bstack1ll_opy_ (u"࠭ࠧែ"))
  def bstack11ll1l11111_opy_(self, commands_to_wrap):
    if commands_to_wrap != None and len(commands_to_wrap) != 0:
      self.commands_to_wrap = commands_to_wrap
  def store(self):
    try:
      with open(self.bstack11l1llll1l1_opy_, bstack1ll_opy_ (u"ࠧࡸࠩៃ")) as file:
        json.dump({
          bstack1ll_opy_ (u"ࠣࡥࡲࡱࡲࡧ࡮ࡥࡵࠥោ"): self.commands_to_wrap,
          bstack1ll_opy_ (u"ࠤࡶࡧࡷ࡯ࡰࡵࡵࠥៅ"): {
            bstack1ll_opy_ (u"ࠥࡷࡨࡧ࡮ࠣំ"): self.perform_scan,
            bstack1ll_opy_ (u"ࠦ࡬࡫ࡴࡓࡧࡶࡹࡱࡺࡳࠣះ"): self.bstack1ll111l11_opy_,
            bstack1ll_opy_ (u"ࠧ࡭ࡥࡵࡔࡨࡷࡺࡲࡴࡴࡕࡸࡱࡲࡧࡲࡺࠤៈ"): self.bstack1l1lllllll_opy_,
            bstack1ll_opy_ (u"ࠨࡳࡢࡸࡨࡖࡪࡹࡵ࡭ࡶࡶࠦ៉"): self.bstack11ll11l1l1l_opy_
          },
          bstack1ll_opy_ (u"ࠢ࡯ࡱࡱࡆࡘࡺࡡࡤ࡭ࡌࡲ࡫ࡸࡡࡂ࠳࠴ࡽࡈ࡮ࡲࡰ࡯ࡨࡓࡵࡺࡩࡰࡰࡶࠦ៊"): self.bstack11ll111l111_opy_
        }, file)
    except Exception as e:
      logger.error(bstack1ll_opy_ (u"ࠣࡇࡵࡶࡴࡸࠠࡸࡪ࡬ࡰࡪࠦࡳࡵࡱࡵ࡭ࡳ࡭ࠠࡤࡱࡰࡱࡦࡴࡤࡴ࠼ࠣࡿࢂࠨ់").format(e))
      pass
  def bstack111llll1l1_opy_(self, command_name):
    try:
      return any(command.get(bstack1ll_opy_ (u"ࠩࡱࡥࡲ࡫ࠧ៌")) == command_name for command in self.commands_to_wrap)
    except:
      return False
bstack1111l1ll1_opy_ = bstack11l1lll1lll_opy_()