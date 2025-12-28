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
import time
from bstack_utils.bstack11l1lll111l_opy_ import bstack11l1lll11ll_opy_
from bstack_utils.constants import bstack11l1l1ll1ll_opy_
from bstack_utils.helper import get_host_info, bstack111ll111ll1_opy_
class bstack111l111111l_opy_:
    bstack1ll_opy_ (u"ࠨࠢࠣࠌࠣࠤࠥࠦࡈࡢࡰࡧࡰࡪࡹࠠࡵࡧࡶࡸࠥࡵࡲࡥࡧࡵ࡭ࡳ࡭ࠠࡰࡴࡦ࡬ࡪࡹࡴࡳࡣࡷ࡭ࡴࡴࠠࡸ࡫ࡷ࡬ࠥࡺࡨࡦࠢࡅࡶࡴࡽࡳࡦࡴࡖࡸࡦࡩ࡫ࠡࡵࡨࡶࡻ࡫ࡲ࠯ࠌࠣࠤࠥࠦࠢࠣࠤℇ")
    def __init__(self, config, logger):
        bstack1ll_opy_ (u"ࠢࠣࠤࠍࠤࠥࠦࠠࠡࠢࠣࠤ࠿ࡶࡡࡳࡣࡰࠤࡨࡵ࡮ࡧ࡫ࡪ࠾ࠥࡪࡩࡤࡶ࠯ࠤࡹ࡫ࡳࡵࠢࡲࡶࡨ࡮ࡥࡴࡶࡵࡥࡹ࡯࡯࡯ࠢࡦࡳࡳ࡬ࡩࡨࠌࠣࠤࠥࠦࠠࠡࠢࠣ࠾ࡵࡧࡲࡢ࡯ࠣࡳࡷࡩࡨࡦࡵࡷࡶࡦࡺࡩࡰࡰࡢࡷࡹࡸࡡࡵࡧࡪࡽ࠿ࠦࡳࡵࡴ࠯ࠤࡹ࡫ࡳࡵࠢࡲࡶࡩ࡫ࡲࡪࡰࡪࠤࡸࡺࡲࡢࡶࡨ࡫ࡾࠦ࡮ࡢ࡯ࡨࠎࠥࠦࠠࠡࠢࠣࠤࠥࠨࠢࠣ℈")
        self.config = config
        self.logger = logger
        self.bstack1llll111ll11_opy_ = bstack1ll_opy_ (u"ࠣࡶࡨࡷࡹࡵࡲࡤࡪࡨࡷࡹࡸࡡࡵ࡫ࡲࡲ࠴ࡧࡰࡪ࠱ࡹ࠵࠴ࡹࡰ࡭࡫ࡷ࠱ࡹ࡫ࡳࡵࡵࠥ℉")
        self.bstack1llll11ll11l_opy_ = None
        self.bstack1llll11l1l1l_opy_ = 60
        self.bstack1llll111l11l_opy_ = 5
        self.bstack1llll111ll1l_opy_ = 0
    def bstack1111lll11ll_opy_(self, test_files, orchestration_strategy, orchestration_metadata={}):
        bstack1ll_opy_ (u"ࠤࠥࠦࠏࠦࠠࠡࠢࠣࠤࠥࠦࡉ࡯࡫ࡷ࡭ࡦࡺࡥࡴࠢࡷ࡬ࡪࠦࡳࡱ࡮࡬ࡸࠥࡺࡥࡴࡶࡶࠤࡷ࡫ࡱࡶࡧࡶࡸࠥࡧ࡮ࡥࠢࡶࡸࡴࡸࡥࡴࠢࡷ࡬ࡪࠦࡲࡦࡵࡳࡳࡳࡹࡥࠡࡦࡤࡸࡦࠦࡦࡰࡴࠣࡴࡴࡲ࡬ࡪࡰࡪ࠲ࠏࠦࠠࠡࠢࠣࠤࠥࠦࠢࠣࠤℊ")
        self.logger.debug(bstack1ll_opy_ (u"ࠥ࡟ࡸࡶ࡬ࡪࡶࡗࡩࡸࡺࡳ࡞ࠢࡌࡲ࡮ࡺࡩࡢࡶ࡬ࡲ࡬ࠦࡳࡱ࡮࡬ࡸࠥࡺࡥࡴࡶࡶࠤࡼ࡯ࡴࡩࠢࡶࡸࡷࡧࡴࡦࡩࡼ࠾ࠥࢁࡽࠣℋ").format(orchestration_strategy))
        try:
            bstack1llll11ll111_opy_ = []
            bstack1ll_opy_ (u"ࠦࠧࠨࡗࡦࠢࡺ࡭ࡱࡲࠠ࡯ࡱࡷࠤ࡫࡫ࡴࡤࡪࠣ࡫࡮ࡺࠠ࡮ࡧࡷࡥࡩࡧࡴࡢࠢ࡬ࡷࠥࡹ࡯ࡶࡴࡦࡩࠥ࡯ࡳࠡࡶࡼࡴࡪࠦ࡯ࡧࠢࡤࡶࡷࡧࡹࠡࡣࡱࡨࠥ࡯ࡴࠨࡵࠣࡩࡱ࡫࡭ࡦࡰࡷࡷࠥࡧࡲࡦࠢࡲࡪࠥࡺࡹࡱࡧࠣࡨ࡮ࡩࡴࠋࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࡢࡦࡥࡤࡹࡸ࡫ࠠࡪࡰࠣࡸ࡭ࡧࡴࠡࡥࡤࡷࡪ࠲ࠠࡶࡵࡨࡶࠥ࡮ࡡࡴࠢࡳࡶࡴࡼࡩࡥࡧࡧࠤࡲࡻ࡬ࡵ࡫࠰ࡶࡪࡶ࡯ࠡࡵࡲࡹࡷࡩࡥࠡࡹ࡬ࡸ࡭ࠦࡦࡦࡣࡷࡹࡷ࡫ࡂࡳࡣࡱࡧ࡭ࠦࡩ࡯ࠢࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫ࠣࠤࠥℌ")
            source = orchestration_metadata[bstack1ll_opy_ (u"ࠬࡸࡵ࡯ࡡࡶࡱࡦࡸࡴࡠࡵࡨࡰࡪࡩࡴࡪࡱࡱࠫℍ")].get(bstack1ll_opy_ (u"࠭ࡳࡰࡷࡵࡧࡪ࠭ℎ"), [])
            bstack1llll11l1111_opy_ = isinstance(source, list) and all(isinstance(src, dict) and src is not None for src in source) and len(source) > 0
            if orchestration_metadata[bstack1ll_opy_ (u"ࠧࡳࡷࡱࡣࡸࡳࡡࡳࡶࡢࡷࡪࡲࡥࡤࡶ࡬ࡳࡳ࠭ℏ")].get(bstack1ll_opy_ (u"ࠨࡧࡱࡥࡧࡲࡥࡥࠩℐ"), False) and not bstack1llll11l1111_opy_:
                bstack1llll11ll111_opy_ = bstack111ll111ll1_opy_(source) # bstack1llll11l1l11_opy_-repo is handled bstack1llll111lll1_opy_
            payload = {
                bstack1ll_opy_ (u"ࠤࡷࡩࡸࡺࡳࠣℑ"): [{bstack1ll_opy_ (u"ࠥࡪ࡮ࡲࡥࡑࡣࡷ࡬ࠧℒ"): f} for f in test_files],
                bstack1ll_opy_ (u"ࠦࡴࡸࡣࡩࡧࡶࡸࡷࡧࡴࡪࡱࡱࡗࡹࡸࡡࡵࡧࡪࡽࠧℓ"): orchestration_strategy,
                bstack1ll_opy_ (u"ࠧࡵࡲࡤࡪࡨࡷࡹࡸࡡࡵ࡫ࡲࡲࡒ࡫ࡴࡢࡦࡤࡸࡦࠨ℔"): orchestration_metadata,
                bstack1ll_opy_ (u"ࠨ࡮ࡰࡦࡨࡍࡳࡪࡥࡹࠤℕ"): int(os.environ.get(bstack1ll_opy_ (u"ࠢࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡎࡐࡆࡈࡣࡎࡔࡄࡆ࡚ࠥ№")) or bstack1ll_opy_ (u"ࠣ࠲ࠥ℗")),
                bstack1ll_opy_ (u"ࠤࡷࡳࡹࡧ࡬ࡏࡱࡧࡩࡸࠨ℘"): int(os.environ.get(bstack1ll_opy_ (u"ࠥࡆࡗࡕࡗࡔࡇࡕࡗ࡙ࡇࡃࡌࡡࡗࡓ࡙ࡇࡌࡠࡐࡒࡈࡊࡥࡃࡐࡗࡑࡘࠧℙ")) or bstack1ll_opy_ (u"ࠦ࠶ࠨℚ")),
                bstack1ll_opy_ (u"ࠧࡶࡲࡰ࡬ࡨࡧࡹࡔࡡ࡮ࡧࠥℛ"): self.config.get(bstack1ll_opy_ (u"࠭ࡰࡳࡱ࡭ࡩࡨࡺࡎࡢ࡯ࡨࠫℜ"), bstack1ll_opy_ (u"ࠧࠨℝ")),
                bstack1ll_opy_ (u"ࠣࡤࡸ࡭ࡱࡪࡎࡢ࡯ࡨࠦ℞"): self.config.get(bstack1ll_opy_ (u"ࠩࡥࡹ࡮ࡲࡤࡏࡣࡰࡩࠬ℟"), os.path.basename(os.path.abspath(os.getcwd()))),
                bstack1ll_opy_ (u"ࠥࡦࡺ࡯࡬ࡥࡔࡸࡲࡎࡪࡥ࡯ࡶ࡬ࡪ࡮࡫ࡲࠣ℠"): os.environ.get(bstack1ll_opy_ (u"ࠦࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡆ࡚ࡏࡌࡅࡡࡕ࡙ࡓࡥࡉࡅࡇࡑࡘࡎࡌࡉࡆࡔࠥ℡"), bstack1ll_opy_ (u"ࠧࠨ™")),
                bstack1ll_opy_ (u"ࠨࡨࡰࡵࡷࡍࡳ࡬࡯ࠣ℣"): get_host_info(),
                bstack1ll_opy_ (u"ࠢࡱࡴࡇࡩࡹࡧࡩ࡭ࡵࠥℤ"): bstack1llll11ll111_opy_
            }
            self.logger.debug(bstack1ll_opy_ (u"ࠣ࡝ࡶࡴࡱ࡯ࡴࡕࡧࡶࡸࡸࡣࠠࡔࡧࡱࡨ࡮ࡴࡧࠡࡶࡨࡷࡹࠦࡦࡪ࡮ࡨࡷ࠿ࠦࡻࡾࠤ℥").format(payload))
            response = bstack11l1lll11ll_opy_.bstack1llll1ll1l1l_opy_(self.bstack1llll111ll11_opy_, payload)
            if response:
                self.bstack1llll11ll11l_opy_ = self._1llll11l111l_opy_(response)
                self.logger.debug(bstack1ll_opy_ (u"ࠤ࡞ࡷࡵࡲࡩࡵࡖࡨࡷࡹࡹ࡝ࠡࡕࡳࡰ࡮ࡺࠠࡵࡧࡶࡸࡸࠦࡲࡦࡵࡳࡳࡳࡹࡥ࠻ࠢࡾࢁࠧΩ").format(self.bstack1llll11ll11l_opy_))
            else:
                self.logger.error(bstack1ll_opy_ (u"ࠥ࡟ࡸࡶ࡬ࡪࡶࡗࡩࡸࡺࡳ࡞ࠢࡉࡥ࡮ࡲࡥࡥࠢࡷࡳࠥ࡭ࡥࡵࠢࡶࡴࡱ࡯ࡴࠡࡶࡨࡷࡹࡹࠠࡳࡧࡶࡴࡴࡴࡳࡦ࠰ࠥ℧"))
        except Exception as e:
            self.logger.error(bstack1ll_opy_ (u"ࠦࡠࡹࡰ࡭࡫ࡷࡘࡪࡹࡴࡴ࡟ࠣࡉࡽࡩࡥࡱࡶ࡬ࡳࡳࠦࡩ࡯ࠢࡶࡩࡳࡪࡩ࡯ࡩࠣࡸࡪࡹࡴࠡࡨ࡬ࡰࡪࡹ࠺࠻ࠢࡾࢁࠧℨ").format(e))
    def _1llll11l111l_opy_(self, response):
        bstack1ll_opy_ (u"ࠧࠨࠢࠋࠢࠣࠤࠥࠦࠠࠡࠢࡓࡶࡴࡩࡥࡴࡵࡨࡷࠥࡺࡨࡦࠢࡶࡴࡱ࡯ࡴࠡࡶࡨࡷࡹࡹࠠࡂࡒࡌࠤࡷ࡫ࡳࡱࡱࡱࡷࡪࠦࡡ࡯ࡦࠣࡩࡽࡺࡲࡢࡥࡷࡷࠥࡸࡥ࡭ࡧࡹࡥࡳࡺࠠࡧ࡫ࡨࡰࡩࡹ࠮ࠋࠢࠣࠤࠥࠦࠠࠡࠢࠥࠦࠧ℩")
        bstack11lll1ll1l_opy_ = {}
        bstack11lll1ll1l_opy_[bstack1ll_opy_ (u"ࠨࡴࡪ࡯ࡨࡳࡺࡺࠢK")] = response.get(bstack1ll_opy_ (u"ࠢࡵ࡫ࡰࡩࡴࡻࡴࠣÅ"), self.bstack1llll11l1l1l_opy_)
        bstack11lll1ll1l_opy_[bstack1ll_opy_ (u"ࠣࡶ࡬ࡱࡪࡵࡵࡵࡋࡱࡸࡪࡸࡶࡢ࡮ࠥℬ")] = response.get(bstack1ll_opy_ (u"ࠤࡷ࡭ࡲ࡫࡯ࡶࡶࡌࡲࡹ࡫ࡲࡷࡣ࡯ࠦℭ"), self.bstack1llll111l11l_opy_)
        bstack1llll111llll_opy_ = response.get(bstack1ll_opy_ (u"ࠥࡶࡪࡹࡵ࡭ࡶࡘࡶࡱࠨ℮"))
        bstack1llll11l1ll1_opy_ = response.get(bstack1ll_opy_ (u"ࠦࡹ࡯࡭ࡦࡱࡸࡸ࡚ࡸ࡬ࠣℯ"))
        if bstack1llll111llll_opy_:
            bstack11lll1ll1l_opy_[bstack1ll_opy_ (u"ࠧࡸࡥࡴࡷ࡯ࡸ࡚ࡸ࡬ࠣℰ")] = bstack1llll111llll_opy_.split(bstack11l1l1ll1ll_opy_ + bstack1ll_opy_ (u"ࠨ࠯ࠣℱ"))[1] if bstack11l1l1ll1ll_opy_ + bstack1ll_opy_ (u"ࠢ࠰ࠤℲ") in bstack1llll111llll_opy_ else bstack1llll111llll_opy_
        else:
            bstack11lll1ll1l_opy_[bstack1ll_opy_ (u"ࠣࡴࡨࡷࡺࡲࡴࡖࡴ࡯ࠦℳ")] = None
        if bstack1llll11l1ll1_opy_:
            bstack11lll1ll1l_opy_[bstack1ll_opy_ (u"ࠤࡷ࡭ࡲ࡫࡯ࡶࡶࡘࡶࡱࠨℴ")] = bstack1llll11l1ll1_opy_.split(bstack11l1l1ll1ll_opy_ + bstack1ll_opy_ (u"ࠥ࠳ࠧℵ"))[1] if bstack11l1l1ll1ll_opy_ + bstack1ll_opy_ (u"ࠦ࠴ࠨℶ") in bstack1llll11l1ll1_opy_ else bstack1llll11l1ll1_opy_
        else:
            bstack11lll1ll1l_opy_[bstack1ll_opy_ (u"ࠧࡺࡩ࡮ࡧࡲࡹࡹ࡛ࡲ࡭ࠤℷ")] = None
        if (
            response.get(bstack1ll_opy_ (u"ࠨࡴࡪ࡯ࡨࡳࡺࡺࠢℸ")) is None or
            response.get(bstack1ll_opy_ (u"ࠢࡵ࡫ࡰࡩࡴࡻࡴࡊࡰࡷࡩࡷࡼࡡ࡭ࠤℹ")) is None or
            response.get(bstack1ll_opy_ (u"ࠣࡶ࡬ࡱࡪࡵࡵࡵࡗࡵࡰࠧ℺")) is None or
            response.get(bstack1ll_opy_ (u"ࠤࡵࡩࡸࡻ࡬ࡵࡗࡵࡰࠧ℻")) is None
        ):
            self.logger.debug(bstack1ll_opy_ (u"ࠥ࡟ࡵࡸ࡯ࡤࡧࡶࡷࡤࡹࡰ࡭࡫ࡷࡣࡹ࡫ࡳࡵࡵࡢࡶࡪࡹࡰࡰࡰࡶࡩࡢࠦࡒࡦࡥࡨ࡭ࡻ࡫ࡤࠡࡰࡸࡰࡱࠦࡶࡢ࡮ࡸࡩ࠭ࡹࠩࠡࡨࡲࡶࠥࡹ࡯࡮ࡧࠣࡥࡹࡺࡲࡪࡤࡸࡸࡪࡹࠠࡪࡰࠣࡷࡵࡲࡩࡵࠢࡷࡩࡸࡺࡳࠡࡃࡓࡍࠥࡸࡥࡴࡲࡲࡲࡸ࡫ࠢℼ"))
        return bstack11lll1ll1l_opy_
    def bstack1111llll111_opy_(self):
        if not self.bstack1llll11ll11l_opy_:
            self.logger.error(bstack1ll_opy_ (u"ࠦࡠ࡭ࡥࡵࡑࡵࡨࡪࡸࡥࡥࡖࡨࡷࡹࡌࡩ࡭ࡧࡶࡡࠥࡔ࡯ࠡࡴࡨࡵࡺ࡫ࡳࡵࠢࡧࡥࡹࡧࠠࡢࡸࡤ࡭ࡱࡧࡢ࡭ࡧࠣࡸࡴࠦࡦࡦࡶࡦ࡬ࠥࡵࡲࡥࡧࡵࡩࡩࠦࡴࡦࡵࡷࠤ࡫࡯࡬ࡦࡵ࠱ࠦℽ"))
            return None
        bstack1llll111l1l1_opy_ = None
        test_files = []
        bstack1llll11l11ll_opy_ = int(time.time() * 1000) # bstack1llll11l11l1_opy_ sec
        bstack1llll111l1ll_opy_ = int(self.bstack1llll11ll11l_opy_.get(bstack1ll_opy_ (u"ࠧࡺࡩ࡮ࡧࡲࡹࡹࡏ࡮ࡵࡧࡵࡺࡦࡲࠢℾ"), self.bstack1llll111l11l_opy_))
        bstack1llll11l1lll_opy_ = int(self.bstack1llll11ll11l_opy_.get(bstack1ll_opy_ (u"ࠨࡴࡪ࡯ࡨࡳࡺࡺࠢℿ"), self.bstack1llll11l1l1l_opy_)) * 1000
        bstack1llll11l1ll1_opy_ = self.bstack1llll11ll11l_opy_.get(bstack1ll_opy_ (u"ࠢࡵ࡫ࡰࡩࡴࡻࡴࡖࡴ࡯ࠦ⅀"), None)
        bstack1llll111llll_opy_ = self.bstack1llll11ll11l_opy_.get(bstack1ll_opy_ (u"ࠣࡴࡨࡷࡺࡲࡴࡖࡴ࡯ࠦ⅁"), None)
        if bstack1llll111llll_opy_ is None and bstack1llll11l1ll1_opy_ is None:
            return None
        try:
            while bstack1llll111llll_opy_ and (time.time() * 1000 - bstack1llll11l11ll_opy_) < bstack1llll11l1lll_opy_:
                response = bstack11l1lll11ll_opy_.bstack1llll1lll1ll_opy_(bstack1llll111llll_opy_, {})
                if response and response.get(bstack1ll_opy_ (u"ࠤࡷࡩࡸࡺࡳࠣ⅂")):
                    bstack1llll111l1l1_opy_ = response.get(bstack1ll_opy_ (u"ࠥࡸࡪࡹࡴࡴࠤ⅃"))
                self.bstack1llll111ll1l_opy_ += 1
                if bstack1llll111l1l1_opy_:
                    break
                time.sleep(bstack1llll111l1ll_opy_)
                self.logger.debug(bstack1ll_opy_ (u"ࠦࡠ࡭ࡥࡵࡑࡵࡨࡪࡸࡥࡥࡖࡨࡷࡹࡌࡩ࡭ࡧࡶࡡࠥࡌࡥࡵࡥ࡫࡭ࡳ࡭ࠠࡰࡴࡧࡩࡷ࡫ࡤࠡࡶࡨࡷࡹࡹࠠࡧࡴࡲࡱࠥࡸࡥࡴࡷ࡯ࡸ࡛ࠥࡒࡍࠢࡤࡪࡹ࡫ࡲࠡࡹࡤ࡭ࡹ࡯࡮ࡨࠢࡩࡳࡷࠦࡻࡾࠢࡶࡩࡨࡵ࡮ࡥࡵ࠱ࠦ⅄").format(bstack1llll111l1ll_opy_))
            if bstack1llll11l1ll1_opy_ and not bstack1llll111l1l1_opy_:
                self.logger.debug(bstack1ll_opy_ (u"ࠧࡡࡧࡦࡶࡒࡶࡩ࡫ࡲࡦࡦࡗࡩࡸࡺࡆࡪ࡮ࡨࡷࡢࠦࡆࡦࡶࡦ࡬࡮ࡴࡧࠡࡱࡵࡨࡪࡸࡥࡥࠢࡷࡩࡸࡺࡳࠡࡨࡵࡳࡲࠦࡴࡪ࡯ࡨࡳࡺࡺࠠࡖࡔࡏࠦⅅ"))
                response = bstack11l1lll11ll_opy_.bstack1llll1lll1ll_opy_(bstack1llll11l1ll1_opy_, {})
                if response and response.get(bstack1ll_opy_ (u"ࠨࡴࡦࡵࡷࡷࠧⅆ")):
                    bstack1llll111l1l1_opy_ = response.get(bstack1ll_opy_ (u"ࠢࡵࡧࡶࡸࡸࠨⅇ"))
            if bstack1llll111l1l1_opy_ and len(bstack1llll111l1l1_opy_) > 0:
                for bstack111l1l1ll1_opy_ in bstack1llll111l1l1_opy_:
                    file_path = bstack111l1l1ll1_opy_.get(bstack1ll_opy_ (u"ࠣࡨ࡬ࡰࡪࡖࡡࡵࡪࠥⅈ"))
                    if file_path:
                        test_files.append(file_path)
            if not bstack1llll111l1l1_opy_:
                return None
            self.logger.debug(bstack1ll_opy_ (u"ࠤ࡞࡫ࡪࡺࡏࡳࡦࡨࡶࡪࡪࡔࡦࡵࡷࡊ࡮ࡲࡥࡴ࡟ࠣࡓࡷࡪࡥࡳࡧࡧࠤࡹ࡫ࡳࡵࠢࡩ࡭ࡱ࡫ࡳࠡࡴࡨࡧࡪ࡯ࡶࡦࡦ࠽ࠤࢀࢃࠢⅉ").format(test_files))
            return test_files
        except Exception as e:
            self.logger.error(bstack1ll_opy_ (u"ࠥ࡟࡬࡫ࡴࡐࡴࡧࡩࡷ࡫ࡤࡕࡧࡶࡸࡋ࡯࡬ࡦࡵࡠࠤࡊࡾࡣࡦࡲࡷ࡭ࡴࡴࠠࡪࡰࠣࡪࡪࡺࡣࡩ࡫ࡱ࡫ࠥࡵࡲࡥࡧࡵࡩࡩࠦࡴࡦࡵࡷࠤ࡫࡯࡬ࡦࡵ࠽ࠤࢀࢃࠢ⅊").format(e))
            return None
    def bstack1111lll1ll1_opy_(self):
        bstack1ll_opy_ (u"ࠦࠧࠨࠊࠡࠢࠣࠤࠥࠦࠠࠡࡔࡨࡸࡺࡸ࡮ࡴࠢࡷ࡬ࡪࠦࡣࡰࡷࡱࡸࠥࡵࡦࠡࡵࡳࡰ࡮ࡺࠠࡵࡧࡶࡸࡸࠦࡁࡑࡋࠣࡧࡦࡲ࡬ࡴࠢࡰࡥࡩ࡫࠮ࠋࠢࠣࠤࠥࠦࠠࠡࠢࠥࠦࠧ⅋")
        return self.bstack1llll111ll1l_opy_