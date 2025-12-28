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
import tempfile
import math
from bstack_utils import bstack11l1l1lll1_opy_
from bstack_utils.constants import bstack11ll11l1ll_opy_, bstack11l1l1lll11_opy_
from bstack_utils.helper import bstack111ll111ll1_opy_, get_host_info
from bstack_utils.bstack11l1lll111l_opy_ import bstack11l1lll11ll_opy_
import json
import re
import sys
bstack1111l1l1l11_opy_ = bstack1ll_opy_ (u"ࠦࡷ࡫ࡴࡳࡻࡗࡩࡸࡺࡳࡐࡰࡉࡥ࡮ࡲࡵࡳࡧࠥệ")
bstack1111ll11l1l_opy_ = bstack1ll_opy_ (u"ࠧࡧࡢࡰࡴࡷࡆࡺ࡯࡬ࡥࡑࡱࡊࡦ࡯࡬ࡶࡴࡨࠦỈ")
bstack11111llllll_opy_ = bstack1ll_opy_ (u"ࠨࡲࡶࡰࡓࡶࡪࡼࡩࡰࡷࡶࡰࡾࡌࡡࡪ࡮ࡨࡨࡋ࡯ࡲࡴࡶࠥỉ")
bstack1111l1llll1_opy_ = bstack1ll_opy_ (u"ࠢࡳࡧࡵࡹࡳࡖࡲࡦࡸ࡬ࡳࡺࡹ࡬ࡺࡈࡤ࡭ࡱ࡫ࡤࠣỊ")
bstack1111l1ll11l_opy_ = bstack1ll_opy_ (u"ࠣࡵ࡮࡭ࡵࡌ࡬ࡢ࡭ࡼࡥࡳࡪࡆࡢ࡫࡯ࡩࡩࠨị")
bstack1111ll11lll_opy_ = bstack1ll_opy_ (u"ࠤࡵࡹࡳ࡙࡭ࡢࡴࡷࡗࡪࡲࡥࡤࡶ࡬ࡳࡳࠨỌ")
bstack1111ll1l11l_opy_ = {
    bstack1111l1l1l11_opy_,
    bstack1111ll11l1l_opy_,
    bstack11111llllll_opy_,
    bstack1111l1llll1_opy_,
    bstack1111l1ll11l_opy_,
    bstack1111ll11lll_opy_
}
bstack1111l1ll111_opy_ = {bstack1ll_opy_ (u"ࠪࡴࡾࡺࡥࡴࡶࠪọ")}
logger = bstack11l1l1lll1_opy_.get_logger(__name__, bstack11ll11l1ll_opy_)
class bstack1111lll1111_opy_:
    def __init__(self):
        self.enabled = False
        self.name = None
    def enable(self, name):
        self.enabled = True
        self.name = name
    def disable(self):
        self.enabled = False
        self.name = None
    def bstack1111l11l1l1_opy_(self):
        return self.enabled
    def get_name(self):
        return self.name
class bstack11llll11l1_opy_:
    _1ll1l11l1ll_opy_ = None
    def __init__(self, config):
        self.bstack1111ll11ll1_opy_ = False
        self.bstack1111l111lll_opy_ = False
        self.bstack1111ll1111l_opy_ = False
        self.bstack1111lll111l_opy_ = False
        self.bstack11111llll1l_opy_ = None
        self.bstack1111ll1lll1_opy_ = bstack1111lll1111_opy_()
        self.bstack1111ll111ll_opy_ = None
        opts = config.get(bstack1ll_opy_ (u"ࠫࡹ࡫ࡳࡵࡑࡵࡧ࡭࡫ࡳࡵࡴࡤࡸ࡮ࡵ࡮ࡐࡲࡷ࡭ࡴࡴࡳࠨỎ"), {})
        self.bstack1111l1l1lll_opy_ = config.get(bstack1ll_opy_ (u"ࠬࡹ࡭ࡢࡴࡷࡗࡪࡲࡥࡤࡶ࡬ࡳࡳࡌࡥࡢࡶࡸࡶࡪࡈࡲࡢࡰࡦ࡬ࡪࡹࡅࡏࡘࠪỏ"), bstack1ll_opy_ (u"ࠨࠢỐ"))
        self.bstack1111ll1llll_opy_ = config.get(bstack1ll_opy_ (u"ࠧࡴ࡯ࡤࡶࡹ࡙ࡥ࡭ࡧࡦࡸ࡮ࡵ࡮ࡇࡧࡤࡸࡺࡸࡥࡃࡴࡤࡲࡨ࡮ࡥࡴࡅࡏࡍࠬố"), bstack1ll_opy_ (u"ࠣࠤỒ"))
        bstack1111l1ll1ll_opy_ = opts.get(bstack1111ll11lll_opy_, {})
        bstack1111l11l111_opy_ = None
        if bstack1ll_opy_ (u"ࠩࡶࡳࡺࡸࡣࡦࠩồ") in bstack1111l1ll1ll_opy_:
            bstack1111ll1ll1l_opy_ = bstack1111l1ll1ll_opy_[bstack1ll_opy_ (u"ࠪࡷࡴࡻࡲࡤࡧࠪỔ")]
            if bstack1111ll1ll1l_opy_ is None or (isinstance(bstack1111ll1ll1l_opy_, str) and bstack1111ll1ll1l_opy_.strip() == bstack1ll_opy_ (u"ࠫࠬổ")) or (isinstance(bstack1111ll1ll1l_opy_, list) and len(bstack1111ll1ll1l_opy_) == 0):
                bstack1111l11l111_opy_ = []
            elif isinstance(bstack1111ll1ll1l_opy_, list):
                bstack1111l11l111_opy_ = bstack1111ll1ll1l_opy_
            elif isinstance(bstack1111ll1ll1l_opy_, str) and bstack1111ll1ll1l_opy_.strip():
                bstack1111l11l111_opy_ = bstack1111ll1ll1l_opy_
            else:
                logger.warning(bstack1ll_opy_ (u"ࠧࡏ࡮ࡷࡣ࡯࡭ࡩࠦࡳࡰࡷࡵࡧࡪࠦࡶࡢ࡮ࡸࡩࠥ࡯࡮ࠡࡥࡲࡲ࡫࡯ࡧ࠻ࠢࡾࢁ࠳ࠦࡄࡦࡨࡤࡹࡱࡺࡩ࡯ࡩࠣࡸࡴࠦࡥ࡮ࡲࡷࡽࠥࡲࡩࡴࡶ࠱ࠦỖ").format(bstack1111ll1ll1l_opy_))
                bstack1111l11l111_opy_ = []
        self.__1111ll11l11_opy_(
            bstack1111l1ll1ll_opy_.get(bstack1ll_opy_ (u"࠭ࡥ࡯ࡣࡥࡰࡪࡪࠧỗ"), False),
            bstack1111l1ll1ll_opy_.get(bstack1ll_opy_ (u"ࠧ࡮ࡱࡧࡩࠬỘ"), bstack1ll_opy_ (u"ࠨࡴࡨࡰࡪࡼࡡ࡯ࡶࡉ࡭ࡷࡹࡴࠨộ")),
            bstack1111l11l111_opy_
        )
        self.__1111l1l11ll_opy_(opts.get(bstack11111llllll_opy_, False))
        self.__1111l1l111l_opy_(opts.get(bstack1111l1llll1_opy_, False))
        self.__1111ll1l1ll_opy_(opts.get(bstack1111l1ll11l_opy_, False))
    @classmethod
    def bstack11lll1111_opy_(cls, config=None):
        if cls._1ll1l11l1ll_opy_ is None and config is not None:
            cls._1ll1l11l1ll_opy_ = bstack11llll11l1_opy_(config)
        return cls._1ll1l11l1ll_opy_
    @staticmethod
    def bstack111l1l111_opy_(config: dict) -> bool:
        bstack1111ll1ll11_opy_ = config.get(bstack1ll_opy_ (u"ࠩࡷࡩࡸࡺࡏࡳࡥ࡫ࡩࡸࡺࡲࡢࡶ࡬ࡳࡳࡕࡰࡵ࡫ࡲࡲࡸ࠭Ớ"), {}).get(bstack1111l1l1l11_opy_, {})
        return bstack1111ll1ll11_opy_.get(bstack1ll_opy_ (u"ࠪࡩࡳࡧࡢ࡭ࡧࡧࠫớ"), False)
    @staticmethod
    def bstack1lll1l11ll_opy_(config: dict) -> int:
        bstack1111ll1ll11_opy_ = config.get(bstack1ll_opy_ (u"ࠫࡹ࡫ࡳࡵࡑࡵࡧ࡭࡫ࡳࡵࡴࡤࡸ࡮ࡵ࡮ࡐࡲࡷ࡭ࡴࡴࡳࠨỜ"), {}).get(bstack1111l1l1l11_opy_, {})
        retries = 0
        if bstack11llll11l1_opy_.bstack111l1l111_opy_(config):
            retries = bstack1111ll1ll11_opy_.get(bstack1ll_opy_ (u"ࠬࡳࡡࡹࡔࡨࡸࡷ࡯ࡥࡴࠩờ"), 1)
        return retries
    @staticmethod
    def bstack1l1ll1ll1l_opy_(config: dict) -> dict:
        bstack1111l1l1ll1_opy_ = config.get(bstack1ll_opy_ (u"࠭ࡴࡦࡵࡷࡓࡷࡩࡨࡦࡵࡷࡶࡦࡺࡩࡰࡰࡒࡴࡹ࡯࡯࡯ࡵࠪỞ"), {})
        return {
            key: value for key, value in bstack1111l1l1ll1_opy_.items() if key in bstack1111ll1l11l_opy_
        }
    @staticmethod
    def bstack1111l1l1111_opy_():
        bstack1ll_opy_ (u"ࠢࠣࠤࠍࠤࠥࠦࠠࠡࠢࠣࠤࡈ࡮ࡥࡤ࡭ࠣ࡭࡫ࠦࡴࡩࡧࠣࡥࡧࡵࡲࡵࠢࡥࡹ࡮ࡲࡤࠡࡨ࡬ࡰࡪࠦࡥࡹ࡫ࡶࡸࡸ࠴ࠊࠡࠢࠣࠤࠥࠦࠠࠡࠤࠥࠦở")
        return os.path.exists(os.path.join(tempfile.gettempdir(), bstack1ll_opy_ (u"ࠣࡣࡥࡳࡷࡺ࡟ࡣࡷ࡬ࡰࡩࡥࡻࡾࠤỠ").format(os.getenv(bstack1ll_opy_ (u"ࠤࡅࡖࡔ࡝ࡓࡆࡔࡖࡘࡆࡉࡋࡠࡖࡈࡗ࡙ࡎࡕࡃࡡࡘ࡙ࡎࡊࠢỡ")))))
    @staticmethod
    def bstack11111lll11l_opy_(test_name: str):
        bstack1ll_opy_ (u"ࠥࠦࠧࠐࠠࠡࠢࠣࠤࠥࠦࠠࡄࡪࡨࡧࡰࠦࡩࡧࠢࡷ࡬ࡪࠦࡡࡣࡱࡵࡸࠥࡨࡵࡪ࡮ࡧࠤ࡫࡯࡬ࡦࠢࡨࡼ࡮ࡹࡴࡴ࠰ࠍࠤࠥࠦࠠࠡࠢࠣࠤࠧࠨࠢỢ")
        bstack1111l1111l1_opy_ = os.path.join(tempfile.gettempdir(), bstack1ll_opy_ (u"ࠦ࡫ࡧࡩ࡭ࡧࡧࡣࡹ࡫ࡳࡵࡵࡢࡿࢂ࠴ࡴࡹࡶࠥợ").format(os.getenv(bstack1ll_opy_ (u"ࠧࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣ࡙ࡋࡓࡕࡊࡘࡆࡤ࡛ࡕࡊࡆࠥỤ"))))
        with open(bstack1111l1111l1_opy_, bstack1ll_opy_ (u"࠭ࡡࠨụ")) as file:
            file.write(bstack1ll_opy_ (u"ࠢࡼࡿ࡟ࡲࠧỦ").format(test_name))
    @staticmethod
    def bstack1111l1111ll_opy_(framework: str) -> bool:
       return framework.lower() in bstack1111l1ll111_opy_
    @staticmethod
    def bstack11l11l11l1l_opy_(config: dict) -> bool:
        bstack1111l111ll1_opy_ = config.get(bstack1ll_opy_ (u"ࠨࡶࡨࡷࡹࡕࡲࡤࡪࡨࡷࡹࡸࡡࡵ࡫ࡲࡲࡔࡶࡴࡪࡱࡱࡷࠬủ"), {}).get(bstack1111ll11l1l_opy_, {})
        return bstack1111l111ll1_opy_.get(bstack1ll_opy_ (u"ࠩࡨࡲࡦࡨ࡬ࡦࡦࠪỨ"), False)
    @staticmethod
    def bstack11l11ll1ll1_opy_(config: dict, bstack11l11ll1l11_opy_: int = 0) -> int:
        bstack1ll_opy_ (u"ࠥࠦࠧࠐࠠࠡࠢࠣࠤࠥࠦࠠࡈࡧࡷࠤࡹ࡮ࡥࠡࡨࡤ࡭ࡱࡻࡲࡦࠢࡷ࡬ࡷ࡫ࡳࡩࡱ࡯ࡨ࠱ࠦࡷࡩ࡫ࡦ࡬ࠥࡩࡡ࡯ࠢࡥࡩࠥࡧ࡮ࠡࡣࡥࡷࡴࡲࡵࡵࡧࠣࡲࡺࡳࡢࡦࡴࠣࡳࡷࠦࡡࠡࡲࡨࡶࡨ࡫࡮ࡵࡣࡪࡩ࠳ࠐࠠࠡࠢࠣࠤࠥࠦࠠࡂࡴࡪࡷ࠿ࠐࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࡨࡵ࡮ࡧ࡫ࡪࠤ࠭ࡪࡩࡤࡶࠬ࠾࡚ࠥࡨࡦࠢࡦࡳࡳ࡬ࡩࡨࡷࡵࡥࡹ࡯࡯࡯ࠢࡧ࡭ࡨࡺࡩࡰࡰࡤࡶࡾ࠴ࠊࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࡺ࡯ࡵࡣ࡯ࡣࡹ࡫ࡳࡵࡵࠣࠬ࡮ࡴࡴࠪ࠼ࠣࡘ࡭࡫ࠠࡵࡱࡷࡥࡱࠦ࡮ࡶ࡯ࡥࡩࡷࠦ࡯ࡧࠢࡷࡩࡸࡺࡳࠡࠪࡵࡩࡶࡻࡩࡳࡧࡧࠤ࡫ࡵࡲࠡࡲࡨࡶࡨ࡫࡮ࡵࡣࡪࡩ࠲ࡨࡡࡴࡧࡧࠤࡹ࡮ࡲࡦࡵ࡫ࡳࡱࡪࡳࠪ࠰ࠍࠤࠥࠦࠠࠡࠢࠣࠤࡗ࡫ࡴࡶࡴࡱࡷ࠿ࠐࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤ࡮ࡴࡴ࠻ࠢࡗ࡬ࡪࠦࡦࡢ࡫࡯ࡹࡷ࡫ࠠࡵࡪࡵࡩࡸ࡮࡯࡭ࡦ࠱ࠎࠥࠦࠠࠡࠢࠣࠤࠥࠨࠢࠣứ")
        bstack1111l111ll1_opy_ = config.get(bstack1ll_opy_ (u"ࠫࡹ࡫ࡳࡵࡑࡵࡧ࡭࡫ࡳࡵࡴࡤࡸ࡮ࡵ࡮ࡐࡲࡷ࡭ࡴࡴࡳࠨỪ"), {}).get(bstack1ll_opy_ (u"ࠬࡧࡢࡰࡴࡷࡆࡺ࡯࡬ࡥࡑࡱࡊࡦ࡯࡬ࡶࡴࡨࠫừ"), {})
        bstack1111l1lllll_opy_ = 0
        bstack11111lll1ll_opy_ = 0
        if bstack11llll11l1_opy_.bstack11l11l11l1l_opy_(config):
            bstack11111lll1ll_opy_ = bstack1111l111ll1_opy_.get(bstack1ll_opy_ (u"࠭࡭ࡢࡺࡉࡥ࡮ࡲࡵࡳࡧࡶࠫỬ"), 5)
            if isinstance(bstack11111lll1ll_opy_, str) and bstack11111lll1ll_opy_.endswith(bstack1ll_opy_ (u"ࠧࠦࠩử")):
                try:
                    percentage = int(bstack11111lll1ll_opy_.strip(bstack1ll_opy_ (u"ࠨࠧࠪỮ")))
                    if bstack11l11ll1l11_opy_ > 0:
                        bstack1111l1lllll_opy_ = math.ceil((percentage * bstack11l11ll1l11_opy_) / 100)
                    else:
                        raise ValueError(bstack1ll_opy_ (u"ࠤࡗࡳࡹࡧ࡬ࠡࡶࡨࡷࡹࡹࠠ࡮ࡷࡶࡸࠥࡨࡥࠡࡲࡵࡳࡻ࡯ࡤࡦࡦࠣࡪࡴࡸࠠࡱࡧࡵࡧࡪࡴࡴࡢࡩࡨ࠱ࡧࡧࡳࡦࡦࠣࡸ࡭ࡸࡥࡴࡪࡲࡰࡩࡹ࠮ࠣữ"))
                except ValueError as e:
                    raise ValueError(bstack1ll_opy_ (u"ࠥࡍࡳࡼࡡ࡭࡫ࡧࠤࡵ࡫ࡲࡤࡧࡱࡸࡦ࡭ࡥࠡࡸࡤࡰࡺ࡫ࠠࡧࡱࡵࠤࡲࡧࡸࡇࡣ࡬ࡰࡺࡸࡥࡴ࠼ࠣࡿࢂࠨỰ").format(bstack11111lll1ll_opy_)) from e
            else:
                bstack1111l1lllll_opy_ = int(bstack11111lll1ll_opy_)
        logger.info(bstack1ll_opy_ (u"ࠦࡒࡧࡸࠡࡨࡤ࡭ࡱࡻࡲࡦࡵࠣࡸ࡭ࡸࡥࡴࡪࡲࡰࡩࠦࡳࡦࡶࠣࡸࡴࡀࠠࡼࡿࠣࠬ࡫ࡸ࡯࡮ࠢࡦࡳࡳ࡬ࡩࡨ࠼ࠣࡿࢂ࠯ࠢự").format(bstack1111l1lllll_opy_, bstack11111lll1ll_opy_))
        return bstack1111l1lllll_opy_
    def bstack1111l11l1ll_opy_(self):
        return self.bstack1111lll111l_opy_
    def bstack1111l111111_opy_(self):
        return self.bstack11111llll1l_opy_
    def bstack1111ll11111_opy_(self):
        return self.bstack1111ll111ll_opy_
    def __1111ll11l11_opy_(self, enabled, mode, source=None):
        try:
            self.bstack1111lll111l_opy_ = bool(enabled)
            if mode not in [bstack1ll_opy_ (u"ࠬࡸࡥ࡭ࡧࡹࡥࡳࡺࡆࡪࡴࡶࡸࠬỲ"), bstack1ll_opy_ (u"࠭ࡲࡦ࡮ࡨࡺࡦࡴࡴࡐࡰ࡯ࡽࠬỳ")]:
                logger.warning(bstack1ll_opy_ (u"ࠢࡊࡰࡹࡥࡱ࡯ࡤࠡࡵࡰࡥࡷࡺࠠࡴࡧ࡯ࡩࡨࡺࡩࡰࡰࠣࡱࡴࡪࡥࠡࠩࡾࢁࠬࠦࡰࡳࡱࡹ࡭ࡩ࡫ࡤ࠯ࠢࡇࡩ࡫ࡧࡵ࡭ࡶ࡬ࡲ࡬ࠦࡴࡰࠢࠪࡶࡪࡲࡥࡷࡣࡱࡸࡋ࡯ࡲࡴࡶࠪ࠲ࠧỴ").format(mode))
                mode = bstack1ll_opy_ (u"ࠨࡴࡨࡰࡪࡼࡡ࡯ࡶࡉ࡭ࡷࡹࡴࠨỵ")
            self.bstack11111llll1l_opy_ = mode
            self.bstack1111ll111ll_opy_ = []
            if source is None:
                self.bstack1111ll111ll_opy_ = None
            elif isinstance(source, list):
                self.bstack1111ll111ll_opy_ = source
            elif isinstance(source, str) and source.endswith(bstack1ll_opy_ (u"ࠩ࠱࡮ࡸࡵ࡮ࠨỶ")):
                self.bstack1111ll111ll_opy_ = self._1111l1ll1l1_opy_(source)
            self.__11111lllll1_opy_()
        except Exception as e:
            logger.error(bstack1ll_opy_ (u"ࠥࡊࡦ࡯࡬ࡦࡦࠣࡸࡴࠦࡳࡦࡶࠣࡷࡲࡧࡲࡵࠢࡶࡩࡱ࡫ࡣࡵ࡫ࡲࡲࠥࡩ࡯࡯ࡨ࡬࡫ࡺࡸࡡࡵ࡫ࡲࡲࠥ࠳ࠠࡦࡰࡤࡦࡱ࡫ࡤ࠻ࠢࡾࢁ࠱ࠦ࡭ࡰࡦࡨ࠾ࠥࢁࡽ࠭ࠢࡶࡳࡺࡸࡣࡦ࠼ࠣࡿࢂ࠴ࠠࡆࡴࡵࡳࡷࡀࠠࡼࡿࠥỷ").format(enabled, mode, source, e))
    def bstack1111l11llll_opy_(self):
        return self.bstack1111ll11ll1_opy_
    def __1111l1l11ll_opy_(self, value):
        self.bstack1111ll11ll1_opy_ = bool(value)
        self.__11111lllll1_opy_()
    def bstack1111l11ll11_opy_(self):
        return self.bstack1111l111lll_opy_
    def __1111l1l111l_opy_(self, value):
        self.bstack1111l111lll_opy_ = bool(value)
        self.__11111lllll1_opy_()
    def bstack1111l11111l_opy_(self):
        return self.bstack1111ll1111l_opy_
    def __1111ll1l1ll_opy_(self, value):
        self.bstack1111ll1111l_opy_ = bool(value)
        self.__11111lllll1_opy_()
    def __11111lllll1_opy_(self):
        if self.bstack1111lll111l_opy_:
            self.bstack1111ll11ll1_opy_ = False
            self.bstack1111l111lll_opy_ = False
            self.bstack1111ll1111l_opy_ = False
            self.bstack1111ll1lll1_opy_.enable(bstack1111ll11lll_opy_)
        elif self.bstack1111ll11ll1_opy_:
            self.bstack1111l111lll_opy_ = False
            self.bstack1111ll1111l_opy_ = False
            self.bstack1111lll111l_opy_ = False
            self.bstack1111ll1lll1_opy_.enable(bstack11111llllll_opy_)
        elif self.bstack1111l111lll_opy_:
            self.bstack1111ll11ll1_opy_ = False
            self.bstack1111ll1111l_opy_ = False
            self.bstack1111lll111l_opy_ = False
            self.bstack1111ll1lll1_opy_.enable(bstack1111l1llll1_opy_)
        elif self.bstack1111ll1111l_opy_:
            self.bstack1111ll11ll1_opy_ = False
            self.bstack1111l111lll_opy_ = False
            self.bstack1111lll111l_opy_ = False
            self.bstack1111ll1lll1_opy_.enable(bstack1111l1ll11l_opy_)
        else:
            self.bstack1111ll1lll1_opy_.disable()
    def bstack1111lll1_opy_(self):
        return self.bstack1111ll1lll1_opy_.bstack1111l11l1l1_opy_()
    def bstack111ll111_opy_(self):
        if self.bstack1111ll1lll1_opy_.bstack1111l11l1l1_opy_():
            return self.bstack1111ll1lll1_opy_.get_name()
        return None
    def _1111l1ll1l1_opy_(self, bstack1111ll111l1_opy_):
        bstack1ll_opy_ (u"ࠦࠧࠨࠊࠡࠢࠣࠤࠥࠦࠠࠡࡒࡤࡶࡸ࡫ࠠࡋࡕࡒࡒࠥࡹ࡯ࡶࡴࡦࡩࠥࡩ࡯࡯ࡨ࡬࡫ࡺࡸࡡࡵ࡫ࡲࡲࠥ࡬ࡩ࡭ࡧࠣࡥࡳࡪࠠࡧࡱࡵࡱࡦࡺࠠࡪࡶࠣࡪࡴࡸࠠࡴ࡯ࡤࡶࡹࠦࡳࡦ࡮ࡨࡧࡹ࡯࡯࡯࠰ࠍࠤࠥࠦࠠࠡࠢࠣࠤࡆࡸࡧࡴ࠼ࠍࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࡵࡲࡹࡷࡩࡥࡠࡨ࡬ࡰࡪࡥࡰࡢࡶ࡫ࠤ࠭ࡹࡴࡳࠫ࠽ࠤࡕࡧࡴࡩࠢࡷࡳࠥࡺࡨࡦࠢࡍࡗࡔࡔࠠࡤࡱࡱࡪ࡮࡭ࡵࡳࡣࡷ࡭ࡴࡴࠠࡧ࡫࡯ࡩࠏࠦࠠࠡࠢࠣࠤࠥࠦࡒࡦࡶࡸࡶࡳࡹ࠺ࠋࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦ࡬ࡪࡵࡷ࠾ࠥࡌ࡯ࡳ࡯ࡤࡸࡹ࡫ࡤࠡ࡮࡬ࡷࡹࠦ࡯ࡧࠢࡵࡩࡵࡵࡳࡪࡶࡲࡶࡾࠦࡣࡰࡰࡩ࡭࡬ࡻࡲࡢࡶ࡬ࡳࡳࡹࠊࠡࠢࠣࠤࠥࠦࠠࠡࠤࠥࠦỸ")
        if not os.path.isfile(bstack1111ll111l1_opy_):
            logger.error(bstack1ll_opy_ (u"࡙ࠧ࡯ࡶࡴࡦࡩࠥ࡬ࡩ࡭ࡧࠣࠫࢀࢃࠧࠡࡦࡲࡩࡸࠦ࡮ࡰࡶࠣࡩࡽ࡯ࡳࡵ࠰ࠥỹ").format(bstack1111ll111l1_opy_))
            return []
        data = None
        try:
            with open(bstack1111ll111l1_opy_, bstack1ll_opy_ (u"ࠨࡲࠣỺ")) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(bstack1ll_opy_ (u"ࠢࡆࡴࡵࡳࡷࠦࡰࡢࡴࡶ࡭ࡳ࡭ࠠࡋࡕࡒࡒࠥ࡬ࡲࡰ࡯ࠣࡷࡴࡻࡲࡤࡧࠣࡪ࡮ࡲࡥࠡࠩࡾࢁࠬࡀࠠࡼࡿࠥỻ").format(bstack1111ll111l1_opy_, e))
            return []
        _1111l111l11_opy_ = None
        _1111ll1l1l1_opy_ = None
        def _11111lll1l1_opy_():
            bstack1111l1lll11_opy_ = {}
            bstack1111l111l1l_opy_ = {}
            try:
                if self.bstack1111l1l1lll_opy_.startswith(bstack1ll_opy_ (u"ࠨࡽࠪỼ")) and self.bstack1111l1l1lll_opy_.endswith(bstack1ll_opy_ (u"ࠩࢀࠫỽ")):
                    bstack1111l1lll11_opy_ = json.loads(self.bstack1111l1l1lll_opy_)
                else:
                    bstack1111l1lll11_opy_ = dict(item.split(bstack1ll_opy_ (u"ࠪ࠾ࠬỾ")) for item in self.bstack1111l1l1lll_opy_.split(bstack1ll_opy_ (u"ࠫ࠱࠭ỿ")) if bstack1ll_opy_ (u"ࠬࡀࠧἀ") in item) if self.bstack1111l1l1lll_opy_ else {}
                if self.bstack1111ll1llll_opy_.startswith(bstack1ll_opy_ (u"࠭ࡻࠨἁ")) and self.bstack1111ll1llll_opy_.endswith(bstack1ll_opy_ (u"ࠧࡾࠩἂ")):
                    bstack1111l111l1l_opy_ = json.loads(self.bstack1111ll1llll_opy_)
                else:
                    bstack1111l111l1l_opy_ = dict(item.split(bstack1ll_opy_ (u"ࠨ࠼ࠪἃ")) for item in self.bstack1111ll1llll_opy_.split(bstack1ll_opy_ (u"ࠩ࠯ࠫἄ")) if bstack1ll_opy_ (u"ࠪ࠾ࠬἅ") in item) if self.bstack1111ll1llll_opy_ else {}
            except json.JSONDecodeError as e:
                logger.error(bstack1ll_opy_ (u"ࠦࡊࡸࡲࡰࡴࠣࡴࡦࡸࡳࡪࡰࡪࠤ࡫࡫ࡡࡵࡷࡵࡩࠥࡨࡲࡢࡰࡦ࡬ࠥࡳࡡࡱࡲ࡬ࡲ࡬ࡹ࠺ࠡࡽࢀࠦἆ").format(e))
            logger.debug(bstack1ll_opy_ (u"ࠧࡌࡥࡢࡶࡸࡶࡪࠦࡢࡳࡣࡱࡧ࡭ࠦ࡭ࡢࡲࡳ࡭ࡳ࡭ࡳࠡࡨࡵࡳࡲࠦࡥ࡯ࡸ࠽ࠤࢀࢃࠬࠡࡅࡏࡍ࠿ࠦࡻࡾࠤἇ").format(bstack1111l1lll11_opy_, bstack1111l111l1l_opy_))
            return bstack1111l1lll11_opy_, bstack1111l111l1l_opy_
        if _1111l111l11_opy_ is None or _1111ll1l1l1_opy_ is None:
            _1111l111l11_opy_, _1111ll1l1l1_opy_ = _11111lll1l1_opy_()
        def bstack1111l1l1l1l_opy_(name, bstack1111l1lll1l_opy_):
            if name in _1111ll1l1l1_opy_:
                return _1111ll1l1l1_opy_[name]
            if name in _1111l111l11_opy_:
                return _1111l111l11_opy_[name]
            if bstack1111l1lll1l_opy_.get(bstack1ll_opy_ (u"࠭ࡦࡦࡣࡷࡹࡷ࡫ࡂࡳࡣࡱࡧ࡭࠭Ἀ")):
                return bstack1111l1lll1l_opy_[bstack1ll_opy_ (u"ࠧࡧࡧࡤࡸࡺࡸࡥࡃࡴࡤࡲࡨ࡮ࠧἉ")]
            return None
        if isinstance(data, dict):
            bstack1111l11lll1_opy_ = []
            bstack1111ll1l111_opy_ = re.compile(bstack1ll_opy_ (u"ࡳࠩࡡ࡟ࡆ࠳࡚࠱࠯࠼ࡣࡢ࠱ࠤࠨἊ"))
            for name, bstack1111l1lll1l_opy_ in data.items():
                if not isinstance(bstack1111l1lll1l_opy_, dict):
                    continue
                url = bstack1111l1lll1l_opy_.get(bstack1ll_opy_ (u"ࠩࡸࡶࡱ࠭Ἃ"))
                if url is None or (isinstance(url, str) and url.strip() == bstack1ll_opy_ (u"ࠪࠫἌ")):
                    logger.warning(bstack1ll_opy_ (u"ࠦࡗ࡫ࡰࡰࡵ࡬ࡸࡴࡸࡹࠡࡗࡕࡐࠥ࡯ࡳࠡ࡯࡬ࡷࡸ࡯࡮ࡨࠢࡩࡳࡷࠦࡳࡰࡷࡵࡧࡪࠦࠧࡼࡿࠪ࠾ࠥࢁࡽࠣἍ").format(name, bstack1111l1lll1l_opy_))
                    continue
                if not bstack1111ll1l111_opy_.match(name):
                    logger.warning(bstack1ll_opy_ (u"ࠧࡏ࡮ࡷࡣ࡯࡭ࡩࠦࡳࡰࡷࡵࡧࡪࠦࡩࡥࡧࡱࡸ࡮࡬ࡩࡦࡴࠣࡪࡴࡸ࡭ࡢࡶࠣࡪࡴࡸࠠࠨࡽࢀࠫ࠿ࠦࡻࡾࠤἎ").format(name, bstack1111l1lll1l_opy_))
                    continue
                if len(name) > 30 or len(name) < 1:
                    logger.warning(bstack1ll_opy_ (u"ࠨࡓࡰࡷࡵࡧࡪࠦࡩࡥࡧࡱࡸ࡮࡬ࡩࡦࡴࠣࠫࢀࢃࠧࠡ࡯ࡸࡷࡹࠦࡨࡢࡸࡨࠤࡦࠦ࡬ࡦࡰࡪࡸ࡭ࠦࡢࡦࡶࡺࡩࡪࡴࠠ࠲ࠢࡤࡲࡩࠦ࠳࠱ࠢࡦ࡬ࡦࡸࡡࡤࡶࡨࡶࡸ࠴ࠢἏ").format(name))
                    continue
                bstack1111l1lll1l_opy_ = bstack1111l1lll1l_opy_.copy()
                bstack1111l1lll1l_opy_[bstack1ll_opy_ (u"ࠧ࡯ࡣࡰࡩࠬἐ")] = name
                bstack1111l1lll1l_opy_[bstack1ll_opy_ (u"ࠨࡨࡨࡥࡹࡻࡲࡦࡄࡵࡥࡳࡩࡨࠨἑ")] = bstack1111l1l1l1l_opy_(name, bstack1111l1lll1l_opy_)
                if not bstack1111l1lll1l_opy_.get(bstack1ll_opy_ (u"ࠩࡩࡩࡦࡺࡵࡳࡧࡅࡶࡦࡴࡣࡩࠩἒ")) or bstack1111l1lll1l_opy_.get(bstack1ll_opy_ (u"ࠪࡪࡪࡧࡴࡶࡴࡨࡆࡷࡧ࡮ࡤࡪࠪἓ")) == bstack1ll_opy_ (u"ࠫࠬἔ"):
                    logger.warning(bstack1ll_opy_ (u"ࠧࡌࡥࡢࡶࡸࡶࡪࠦࡢࡳࡣࡱࡧ࡭ࠦ࡮ࡰࡶࠣࡷࡵ࡫ࡣࡪࡨ࡬ࡩࡩࠦࡦࡰࡴࠣࡷࡴࡻࡲࡤࡧࠣࠫࢀࢃࠧ࠻ࠢࡾࢁࠧἕ").format(name, bstack1111l1lll1l_opy_))
                    continue
                if bstack1111l1lll1l_opy_.get(bstack1ll_opy_ (u"࠭ࡢࡢࡵࡨࡆࡷࡧ࡮ࡤࡪࠪ἖")) and bstack1111l1lll1l_opy_[bstack1ll_opy_ (u"ࠧࡣࡣࡶࡩࡇࡸࡡ࡯ࡥ࡫ࠫ἗")] == bstack1111l1lll1l_opy_[bstack1ll_opy_ (u"ࠨࡨࡨࡥࡹࡻࡲࡦࡄࡵࡥࡳࡩࡨࠨἘ")]:
                    logger.warning(bstack1ll_opy_ (u"ࠤࡉࡩࡦࡺࡵࡳࡧࠣࡦࡷࡧ࡮ࡤࡪࠣࡥࡳࡪࠠࡣࡣࡶࡩࠥࡨࡲࡢࡰࡦ࡬ࠥࡩࡡ࡯ࡰࡲࡸࠥࡨࡥࠡࡶ࡫ࡩࠥࡹࡡ࡮ࡧࠣࡪࡴࡸࠠࡴࡱࡸࡶࡨ࡫ࠠࠨࡽࢀࠫ࠿ࠦࡻࡾࠤἙ").format(name, bstack1111l1lll1l_opy_))
                    continue
                bstack1111l11lll1_opy_.append(bstack1111l1lll1l_opy_)
            return bstack1111l11lll1_opy_
        return data
    def bstack1111llll11l_opy_(self):
        data = {
            bstack1ll_opy_ (u"ࠪࡶࡺࡴ࡟ࡴ࡯ࡤࡶࡹࡥࡳࡦ࡮ࡨࡧࡹ࡯࡯࡯ࠩἚ"): {
                bstack1ll_opy_ (u"ࠫࡪࡴࡡࡣ࡮ࡨࡨࠬἛ"): self.bstack1111l11l1ll_opy_(),
                bstack1ll_opy_ (u"ࠬࡳ࡯ࡥࡧࠪἜ"): self.bstack1111l111111_opy_(),
                bstack1ll_opy_ (u"࠭ࡳࡰࡷࡵࡧࡪ࠭Ἕ"): self.bstack1111ll11111_opy_()
            }
        }
        return data
    def bstack1111l1l11l1_opy_(self, config):
        bstack11111llll11_opy_ = {}
        bstack11111llll11_opy_[bstack1ll_opy_ (u"ࠧࡳࡷࡱࡣࡸࡳࡡࡳࡶࡢࡷࡪࡲࡥࡤࡶ࡬ࡳࡳ࠭἞")] = {
            bstack1ll_opy_ (u"ࠨࡧࡱࡥࡧࡲࡥࡥࠩ἟"): self.bstack1111l11l1ll_opy_(),
            bstack1ll_opy_ (u"ࠩࡰࡳࡩ࡫ࠧἠ"): self.bstack1111l111111_opy_()
        }
        bstack11111llll11_opy_[bstack1ll_opy_ (u"ࠪࡶࡪࡸࡵ࡯ࡡࡳࡶࡪࡼࡩࡰࡷࡶࡰࡾࡥࡦࡢ࡫࡯ࡩࡩ࠭ἡ")] = {
            bstack1ll_opy_ (u"ࠫࡪࡴࡡࡣ࡮ࡨࡨࠬἢ"): self.bstack1111l11ll11_opy_()
        }
        bstack11111llll11_opy_[bstack1ll_opy_ (u"ࠬࡸࡵ࡯ࡡࡳࡶࡪࡼࡩࡰࡷࡶࡰࡾࡥࡦࡢ࡫࡯ࡩࡩࡥࡦࡪࡴࡶࡸࠬἣ")] = {
            bstack1ll_opy_ (u"࠭ࡥ࡯ࡣࡥࡰࡪࡪࠧἤ"): self.bstack1111l11llll_opy_()
        }
        bstack11111llll11_opy_[bstack1ll_opy_ (u"ࠧࡴ࡭࡬ࡴࡤ࡬ࡡࡪ࡮࡬ࡲ࡬ࡥࡡ࡯ࡦࡢࡪࡱࡧ࡫ࡺࠩἥ")] = {
            bstack1ll_opy_ (u"ࠨࡧࡱࡥࡧࡲࡥࡥࠩἦ"): self.bstack1111l11111l_opy_()
        }
        if self.bstack111l1l111_opy_(config):
            bstack11111llll11_opy_[bstack1ll_opy_ (u"ࠩࡵࡩࡹࡸࡹࡠࡶࡨࡷࡹࡹ࡟ࡰࡰࡢࡪࡦ࡯࡬ࡶࡴࡨࠫἧ")] = {
                bstack1ll_opy_ (u"ࠪࡩࡳࡧࡢ࡭ࡧࡧࠫἨ"): True,
                bstack1ll_opy_ (u"ࠫࡲࡧࡸࡠࡴࡨࡸࡷ࡯ࡥࡴࠩἩ"): self.bstack1lll1l11ll_opy_(config)
            }
        if self.bstack11l11l11l1l_opy_(config):
            bstack11111llll11_opy_[bstack1ll_opy_ (u"ࠬࡧࡢࡰࡴࡷࡣࡧࡻࡩ࡭ࡦࡢࡳࡳࡥࡦࡢ࡫࡯ࡹࡷ࡫ࠧἪ")] = {
                bstack1ll_opy_ (u"࠭ࡥ࡯ࡣࡥࡰࡪࡪࠧἫ"): True,
                bstack1ll_opy_ (u"ࠧ࡮ࡣࡻࡣ࡫ࡧࡩ࡭ࡷࡵࡩࡸ࠭Ἤ"): self.bstack11l11ll1ll1_opy_(config)
            }
        return bstack11111llll11_opy_
    def bstack1l1lll1l11_opy_(self, config):
        bstack1ll_opy_ (u"ࠣࠤࠥࠎࠥࠦࠠࠡࠢࠣࠤࠥࡉ࡯࡭࡮ࡨࡧࡹࡹࠠࡣࡷ࡬ࡰࡩࠦࡤࡢࡶࡤࠤࡧࡿࠠ࡮ࡣ࡮࡭ࡳ࡭ࠠࡢࠢࡦࡥࡱࡲࠠࡵࡱࠣࡸ࡭࡫ࠠࡤࡱ࡯ࡰࡪࡩࡴ࠮ࡤࡸ࡭ࡱࡪ࠭ࡥࡣࡷࡥࠥ࡫࡮ࡥࡲࡲ࡭ࡳࡺ࠮ࠋࠢࠣࠤࠥࠦࠠࠡࠢࡄࡶ࡬ࡹ࠺ࠋࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࡢࡶ࡫࡯ࡨࡤࡻࡵࡪࡦࠣࠬࡸࡺࡲࠪ࠼ࠣࡘ࡭࡫ࠠࡖࡗࡌࡈࠥࡵࡦࠡࡶ࡫ࡩࠥࡨࡵࡪ࡮ࡧࠤࡹࡵࠠࡤࡱ࡯ࡰࡪࡩࡴࠡࡦࡤࡸࡦࠦࡦࡰࡴ࠱ࠎࠥࠦࠠࠡࠢࠣࠤࠥࡘࡥࡵࡷࡵࡲࡸࡀࠊࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࡪࡩࡤࡶ࠽ࠤࡗ࡫ࡳࡱࡱࡱࡷࡪࠦࡦࡳࡱࡰࠤࡹ࡮ࡥࠡࡥࡲࡰࡱ࡫ࡣࡵ࠯ࡥࡹ࡮ࡲࡤ࠮ࡦࡤࡸࡦࠦࡥ࡯ࡦࡳࡳ࡮ࡴࡴ࠭ࠢࡲࡶࠥࡔ࡯࡯ࡧࠣ࡭࡫ࠦࡦࡢ࡫࡯ࡩࡩ࠴ࠊࠡࠢࠣࠤࠥࠦࠠࠡࠤࠥࠦἭ")
        if not (config.get(bstack1ll_opy_ (u"ࠩࡩࡶࡦࡳࡥࡸࡱࡵ࡯ࠬἮ"), None) in bstack11l1l1lll11_opy_ and self.bstack1111l11l1ll_opy_()):
            return None
        bstack1111l11l11l_opy_ = os.environ.get(bstack1ll_opy_ (u"ࠪࡆࡗࡕࡗࡔࡇࡕࡗ࡙ࡇࡃࡌࡡࡗࡉࡘ࡚ࡈࡖࡄࡢ࡙࡚ࡏࡄࠨἯ"), None)
        logger.debug(bstack1ll_opy_ (u"ࠦࡠࡩ࡯࡭࡮ࡨࡧࡹࡈࡵࡪ࡮ࡧࡈࡦࡺࡡ࡞ࠢࡆࡳࡱࡲࡥࡤࡶ࡬ࡲ࡬ࠦࡢࡶ࡫࡯ࡨࠥࡪࡡࡵࡣࠣࡪࡴࡸࠠࡣࡷ࡬ࡰࡩࠦࡕࡖࡋࡇ࠾ࠥࢁࡽࠣἰ").format(bstack1111l11l11l_opy_))
        try:
            bstack11l1lll1l1l_opy_ = bstack1ll_opy_ (u"ࠧࡺࡥࡴࡶࡲࡶࡨ࡮ࡥࡴࡶࡵࡥࡹ࡯࡯࡯࠱ࡤࡴ࡮࠵ࡶ࠲࠱ࡥࡹ࡮ࡲࡤࡴ࠱ࡾࢁ࠴ࡩ࡯࡭࡮ࡨࡧࡹ࠳ࡢࡶ࡫࡯ࡨ࠲ࡪࡡࡵࡣࠥἱ").format(bstack1111l11l11l_opy_)
            payload = {
                bstack1ll_opy_ (u"ࠨࡰࡳࡱ࡭ࡩࡨࡺࡎࡢ࡯ࡨࠦἲ"): config.get(bstack1ll_opy_ (u"ࠧࡱࡴࡲ࡮ࡪࡩࡴࡏࡣࡰࡩࠬἳ"), bstack1ll_opy_ (u"ࠨࠩἴ")),
                bstack1ll_opy_ (u"ࠤࡥࡹ࡮ࡲࡤࡏࡣࡰࡩࠧἵ"): config.get(bstack1ll_opy_ (u"ࠪࡦࡺ࡯࡬ࡥࡐࡤࡱࡪ࠭ἶ"), os.path.basename(os.path.abspath(os.getcwd()))),
                bstack1ll_opy_ (u"ࠦࡧࡻࡩ࡭ࡦࡕࡹࡳࡏࡤࡦࡰࡷ࡭࡫࡯ࡥࡳࠤἷ"): os.environ.get(bstack1ll_opy_ (u"ࠧࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣࡇ࡛ࡉࡍࡆࡢࡖ࡚ࡔ࡟ࡊࡆࡈࡒ࡙ࡏࡆࡊࡇࡕࠦἸ"), bstack1ll_opy_ (u"ࠨࠢἹ")),
                bstack1ll_opy_ (u"ࠢ࡯ࡱࡧࡩࡎࡴࡤࡦࡺࠥἺ"): int(os.environ.get(bstack1ll_opy_ (u"ࠣࡄࡕࡓ࡜࡙ࡅࡓࡕࡗࡅࡈࡑ࡟ࡏࡑࡇࡉࡤࡏࡎࡅࡇ࡛ࠦἻ")) or bstack1ll_opy_ (u"ࠤ࠳ࠦἼ")),
                bstack1ll_opy_ (u"ࠥࡸࡴࡺࡡ࡭ࡐࡲࡨࡪࡹࠢἽ"): int(os.environ.get(bstack1ll_opy_ (u"ࠦࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡘࡔ࡚ࡁࡍࡡࡑࡓࡉࡋ࡟ࡄࡑࡘࡒ࡙ࠨἾ")) or bstack1ll_opy_ (u"ࠧ࠷ࠢἿ")),
                bstack1ll_opy_ (u"ࠨࡨࡰࡵࡷࡍࡳ࡬࡯ࠣὀ"): get_host_info(),
            }
            logger.debug(bstack1ll_opy_ (u"ࠢ࡜ࡥࡲࡰࡱ࡫ࡣࡵࡄࡸ࡭ࡱࡪࡄࡢࡶࡤࡡ࡙ࠥࡥ࡯ࡦ࡬ࡲ࡬ࠦࡢࡶ࡫࡯ࡨࠥࡪࡡࡵࡣࠣࡴࡦࡿ࡬ࡰࡣࡧ࠾ࠥࢁࡽࠣὁ").format(payload))
            response = bstack11l1lll11ll_opy_.bstack1111l11ll1l_opy_(bstack11l1lll1l1l_opy_, payload)
            if response:
                logger.debug(bstack1ll_opy_ (u"ࠣ࡝ࡦࡳࡱࡲࡥࡤࡶࡅࡹ࡮ࡲࡤࡅࡣࡷࡥࡢࠦࡂࡶ࡫࡯ࡨࠥࡪࡡࡵࡣࠣࡧࡴࡲ࡬ࡦࡥࡷ࡭ࡴࡴࠠࡳࡧࡶࡴࡴࡴࡳࡦ࠼ࠣࡿࢂࠨὂ").format(response))
                return response
            else:
                logger.error(bstack1ll_opy_ (u"ࠤ࡞ࡧࡴࡲ࡬ࡦࡥࡷࡆࡺ࡯࡬ࡥࡆࡤࡸࡦࡣࠠࡇࡣ࡬ࡰࡪࡪࠠࡵࡱࠣࡧࡴࡲ࡬ࡦࡥࡷࠤࡧࡻࡩ࡭ࡦࠣࡨࡦࡺࡡࠡࡨࡲࡶࠥࡨࡵࡪ࡮ࡧࠤ࡚࡛ࡉࡅ࠼ࠣࡿࢂࠨὃ").format(bstack1111l11l11l_opy_))
                return None
        except Exception as e:
            logger.error(bstack1ll_opy_ (u"ࠥ࡟ࡨࡵ࡬࡭ࡧࡦࡸࡇࡻࡩ࡭ࡦࡇࡥࡹࡧ࡝ࠡࡇࡻࡧࡪࡶࡴࡪࡱࡱࠤ࡮ࡴࠠࡤࡱ࡯ࡰࡪࡩࡴࡪࡰࡪࠤࡧࡻࡩ࡭ࡦࠣࡨࡦࡺࡡࠡࡨࡲࡶࠥࡨࡵࡪ࡮ࡧࠤ࡚࡛ࡉࡅࠢࡾࢁ࠿ࠦࡻࡾࠤὄ").format(bstack1111l11l11l_opy_, e))
            return None