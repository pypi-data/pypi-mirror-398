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
logger = logging.getLogger(__name__)
class BrowserStackSdk:
    def get_current_platform():
        bstack1l111l1l1l_opy_ = {}
        bstack111ll1lll1_opy_ = os.environ.get(bstack1ll_opy_ (u"ࠬࡉࡕࡓࡔࡈࡒ࡙ࡥࡐࡍࡃࡗࡊࡔࡘࡍࡠࡆࡄࡘࡆ࠭༝"), bstack1ll_opy_ (u"࠭ࠧ༞"))
        if not bstack111ll1lll1_opy_:
            return bstack1l111l1l1l_opy_
        try:
            bstack111ll1ll1l_opy_ = json.loads(bstack111ll1lll1_opy_)
            if bstack1ll_opy_ (u"ࠢࡰࡵࠥ༟") in bstack111ll1ll1l_opy_:
                bstack1l111l1l1l_opy_[bstack1ll_opy_ (u"ࠣࡱࡶࠦ༠")] = bstack111ll1ll1l_opy_[bstack1ll_opy_ (u"ࠤࡲࡷࠧ༡")]
            if bstack1ll_opy_ (u"ࠥࡳࡸࡥࡶࡦࡴࡶ࡭ࡴࡴࠢ༢") in bstack111ll1ll1l_opy_ or bstack1ll_opy_ (u"ࠦࡴࡹࡖࡦࡴࡶ࡭ࡴࡴࠢ༣") in bstack111ll1ll1l_opy_:
                bstack1l111l1l1l_opy_[bstack1ll_opy_ (u"ࠧࡵࡳࡗࡧࡵࡷ࡮ࡵ࡮ࠣ༤")] = bstack111ll1ll1l_opy_.get(bstack1ll_opy_ (u"ࠨ࡯ࡴࡡࡹࡩࡷࡹࡩࡰࡰࠥ༥"), bstack111ll1ll1l_opy_.get(bstack1ll_opy_ (u"ࠢࡰࡵ࡙ࡩࡷࡹࡩࡰࡰࠥ༦")))
            if bstack1ll_opy_ (u"ࠣࡤࡵࡳࡼࡹࡥࡳࠤ༧") in bstack111ll1ll1l_opy_ or bstack1ll_opy_ (u"ࠤࡥࡶࡴࡽࡳࡦࡴࡑࡥࡲ࡫ࠢ༨") in bstack111ll1ll1l_opy_:
                bstack1l111l1l1l_opy_[bstack1ll_opy_ (u"ࠥࡦࡷࡵࡷࡴࡧࡵࡒࡦࡳࡥࠣ༩")] = bstack111ll1ll1l_opy_.get(bstack1ll_opy_ (u"ࠦࡧࡸ࡯ࡸࡵࡨࡶࠧ༪"), bstack111ll1ll1l_opy_.get(bstack1ll_opy_ (u"ࠧࡨࡲࡰࡹࡶࡩࡷࡔࡡ࡮ࡧࠥ༫")))
            if bstack1ll_opy_ (u"ࠨࡢࡳࡱࡺࡷࡪࡸ࡟ࡷࡧࡵࡷ࡮ࡵ࡮ࠣ༬") in bstack111ll1ll1l_opy_ or bstack1ll_opy_ (u"ࠢࡣࡴࡲࡻࡸ࡫ࡲࡗࡧࡵࡷ࡮ࡵ࡮ࠣ༭") in bstack111ll1ll1l_opy_:
                bstack1l111l1l1l_opy_[bstack1ll_opy_ (u"ࠣࡤࡵࡳࡼࡹࡥࡳࡘࡨࡶࡸ࡯࡯࡯ࠤ༮")] = bstack111ll1ll1l_opy_.get(bstack1ll_opy_ (u"ࠤࡥࡶࡴࡽࡳࡦࡴࡢࡺࡪࡸࡳࡪࡱࡱࠦ༯"), bstack111ll1ll1l_opy_.get(bstack1ll_opy_ (u"ࠥࡦࡷࡵࡷࡴࡧࡵ࡚ࡪࡸࡳࡪࡱࡱࠦ༰")))
            if bstack1ll_opy_ (u"ࠦࡩ࡫ࡶࡪࡥࡨࠦ༱") in bstack111ll1ll1l_opy_ or bstack1ll_opy_ (u"ࠧࡪࡥࡷ࡫ࡦࡩࡓࡧ࡭ࡦࠤ༲") in bstack111ll1ll1l_opy_:
                bstack1l111l1l1l_opy_[bstack1ll_opy_ (u"ࠨࡤࡦࡸ࡬ࡧࡪࡔࡡ࡮ࡧࠥ༳")] = bstack111ll1ll1l_opy_.get(bstack1ll_opy_ (u"ࠢࡥࡧࡹ࡭ࡨ࡫ࠢ༴"), bstack111ll1ll1l_opy_.get(bstack1ll_opy_ (u"ࠣࡦࡨࡺ࡮ࡩࡥࡏࡣࡰࡩ༵ࠧ")))
            if bstack1ll_opy_ (u"ࠤࡳࡰࡦࡺࡦࡰࡴࡰࠦ༶") in bstack111ll1ll1l_opy_ or bstack1ll_opy_ (u"ࠥࡴࡱࡧࡴࡧࡱࡵࡱࡓࡧ࡭ࡦࠤ༷") in bstack111ll1ll1l_opy_:
                bstack1l111l1l1l_opy_[bstack1ll_opy_ (u"ࠦࡵࡲࡡࡵࡨࡲࡶࡲࡔࡡ࡮ࡧࠥ༸")] = bstack111ll1ll1l_opy_.get(bstack1ll_opy_ (u"ࠧࡶ࡬ࡢࡶࡩࡳࡷࡳ༹ࠢ"), bstack111ll1ll1l_opy_.get(bstack1ll_opy_ (u"ࠨࡰ࡭ࡣࡷࡪࡴࡸ࡭ࡏࡣࡰࡩࠧ༺")))
            if bstack1ll_opy_ (u"ࠢࡱ࡮ࡤࡸ࡫ࡵࡲ࡮ࡡࡹࡩࡷࡹࡩࡰࡰࠥ༻") in bstack111ll1ll1l_opy_ or bstack1ll_opy_ (u"ࠣࡲ࡯ࡥࡹ࡬࡯ࡳ࡯࡙ࡩࡷࡹࡩࡰࡰࠥ༼") in bstack111ll1ll1l_opy_:
                bstack1l111l1l1l_opy_[bstack1ll_opy_ (u"ࠤࡳࡰࡦࡺࡦࡰࡴࡰ࡚ࡪࡸࡳࡪࡱࡱࠦ༽")] = bstack111ll1ll1l_opy_.get(bstack1ll_opy_ (u"ࠥࡴࡱࡧࡴࡧࡱࡵࡱࡤࡼࡥࡳࡵ࡬ࡳࡳࠨ༾"), bstack111ll1ll1l_opy_.get(bstack1ll_opy_ (u"ࠦࡵࡲࡡࡵࡨࡲࡶࡲ࡜ࡥࡳࡵ࡬ࡳࡳࠨ༿")))
            if bstack1ll_opy_ (u"ࠧࡩࡵࡴࡶࡲࡱ࡛ࡧࡲࡪࡣࡥࡰࡪࡹࠢཀ") in bstack111ll1ll1l_opy_:
                bstack1l111l1l1l_opy_[bstack1ll_opy_ (u"ࠨࡣࡶࡵࡷࡳࡲ࡜ࡡࡳ࡫ࡤࡦࡱ࡫ࡳࠣཁ")] = bstack111ll1ll1l_opy_[bstack1ll_opy_ (u"ࠢࡤࡷࡶࡸࡴࡳࡖࡢࡴ࡬ࡥࡧࡲࡥࡴࠤག")]
        except Exception as error:
            logger.error(bstack1ll_opy_ (u"ࠣࡇࡻࡧࡪࡶࡴࡪࡱࡱࠤࡼ࡮ࡩ࡭ࡧࠣ࡫ࡪࡺࡴࡪࡰࡪࠤࡨࡻࡲࡳࡧࡱࡸࠥࡶ࡬ࡢࡶࡩࡳࡷࡳࠠࡥࡣࡷࡥ࠿ࠦࠢགྷ") +  str(error))
        return bstack1l111l1l1l_opy_