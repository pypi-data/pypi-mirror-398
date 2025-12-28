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
from time import sleep
from datetime import datetime
from urllib.parse import urlencode
from bstack_utils.bstack11l1lll111l_opy_ import bstack11l1lll11ll_opy_
from bstack_utils.constants import *
import json
class bstack11l1l11l1_opy_:
    def __init__(self, bstack11l1l1l1l1_opy_, bstack11l1lll1111_opy_):
        self.bstack11l1l1l1l1_opy_ = bstack11l1l1l1l1_opy_
        self.bstack11l1lll1111_opy_ = bstack11l1lll1111_opy_
        self.bstack11l1ll1ll11_opy_ = None
    def __call__(self):
        bstack11l1ll1ll1l_opy_ = {}
        while True:
            self.bstack11l1ll1ll11_opy_ = bstack11l1ll1ll1l_opy_.get(
                bstack1ll_opy_ (u"ࠧ࡯ࡧࡻࡸࡤࡶ࡯࡭࡮ࡢࡸ࡮ࡳࡥࠨ៑"),
                int(datetime.now().timestamp() * 1000)
            )
            bstack11l1ll1llll_opy_ = self.bstack11l1ll1ll11_opy_ - int(datetime.now().timestamp() * 1000)
            if bstack11l1ll1llll_opy_ > 0:
                sleep(bstack11l1ll1llll_opy_ / 1000)
            params = {
                bstack1ll_opy_ (u"ࠨࡶࡨࡷࡹࡥࡲࡶࡰࡢࡹࡺ࡯ࡤࠨ្"): self.bstack11l1l1l1l1_opy_,
                bstack1ll_opy_ (u"ࠩࡷ࡭ࡲ࡫ࡳࡵࡣࡰࡴࠬ៓"): int(datetime.now().timestamp() * 1000)
            }
            bstack11l1ll1l1ll_opy_ = bstack1ll_opy_ (u"ࠥ࡬ࡹࡺࡰࡴ࠼࠲࠳ࠧ។") + bstack11l1lll11l1_opy_ + bstack1ll_opy_ (u"ࠦ࠴ࡧࡵࡵࡱࡰࡥࡹ࡫࠯ࡢࡲ࡬࠳ࡻ࠷࠯ࠣ៕")
            if self.bstack11l1lll1111_opy_.lower() == bstack1ll_opy_ (u"ࠧࡸࡥࡴࡷ࡯ࡸࡸࠨ៖"):
                bstack11l1ll1ll1l_opy_ = bstack11l1lll11ll_opy_.results(bstack11l1ll1l1ll_opy_, params)
            else:
                bstack11l1ll1ll1l_opy_ = bstack11l1lll11ll_opy_.bstack11l1ll1lll1_opy_(bstack11l1ll1l1ll_opy_, params)
            if str(bstack11l1ll1ll1l_opy_.get(bstack1ll_opy_ (u"࠭ࡳࡵࡣࡷࡹࡸ࠭ៗ"), bstack1ll_opy_ (u"ࠧ࠳࠲࠳ࠫ៘"))) != bstack1ll_opy_ (u"ࠨ࠶࠳࠸ࠬ៙"):
                break
        return bstack11l1ll1ll1l_opy_.get(bstack1ll_opy_ (u"ࠩࡧࡥࡹࡧࠧ៚"), bstack11l1ll1ll1l_opy_)