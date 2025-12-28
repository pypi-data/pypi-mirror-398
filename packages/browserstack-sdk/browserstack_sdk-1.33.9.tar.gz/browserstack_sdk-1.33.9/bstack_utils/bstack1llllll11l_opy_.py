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
from bstack_utils.constants import *
from browserstack_sdk.sdk_cli.cli import cli
from bstack_utils.bstack1111lll1l1l_opy_ import bstack111l111111l_opy_
from bstack_utils.bstack1l11l1lll_opy_ import bstack11llll11l1_opy_
from bstack_utils.helper import bstack11l11lllll_opy_
import json
class bstack1ll1l1111l_opy_:
    _1ll1l11l1ll_opy_ = None
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.bstack1111lllll11_opy_ = bstack111l111111l_opy_(self.config, logger)
        self.bstack1l11l1lll_opy_ = bstack11llll11l1_opy_.bstack11lll1111_opy_(config=self.config)
        self.bstack1111lll1lll_opy_ = {}
        self.bstack11111l1lll_opy_ = False
        self.bstack1111lll11l1_opy_ = (
            self.__111l1111111_opy_()
            and self.bstack1l11l1lll_opy_ is not None
            and self.bstack1l11l1lll_opy_.bstack1111lll1_opy_()
            and config.get(bstack1ll_opy_ (u"ࠫࡵࡸ࡯࡫ࡧࡦࡸࡓࡧ࡭ࡦࠩẫ"), None) is not None
            and config.get(bstack1ll_opy_ (u"ࠬࡨࡵࡪ࡮ࡧࡒࡦࡳࡥࠨẬ"), os.path.basename(os.getcwd())) is not None
        )
    @classmethod
    def bstack11lll1111_opy_(cls, config, logger):
        if cls._1ll1l11l1ll_opy_ is None and config is not None:
            cls._1ll1l11l1ll_opy_ = bstack1ll1l1111l_opy_(config, logger)
        return cls._1ll1l11l1ll_opy_
    def bstack1111lll1_opy_(self):
        bstack1ll_opy_ (u"ࠨࠢࠣࠌࠣࠤࠥࠦࠠࠡࠢࠣࡈࡴࠦ࡮ࡰࡶࠣࡥࡵࡶ࡬ࡺࠢࡷࡩࡸࡺࠠࡰࡴࡧࡩࡷ࡯࡮ࡨࠢࡺ࡬ࡪࡴ࠺ࠋࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤ࠲ࠦࡏ࠲࠳ࡼࠤ࡮ࡹࠠ࡯ࡱࡷࠤࡪࡴࡡࡣ࡮ࡨࡨࠏࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡ࠯ࠣࡓࡷࡪࡥࡳ࡫ࡱ࡫ࠥ࡯ࡳࠡࡰࡲࡸࠥ࡫࡮ࡢࡤ࡯ࡩࡩࠐࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢ࠰ࠤࡵࡸ࡯࡫ࡧࡦࡸࡓࡧ࡭ࡦࠢ࡬ࡷࠥࡔ࡯࡯ࡧࠍࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦ࠭ࠡࡤࡸ࡭ࡱࡪࡎࡢ࡯ࡨࠤ࡮ࡹࠠࡏࡱࡱࡩࠏࠦࠠࠡࠢࠣࠤࠥࠦࠢࠣࠤậ")
        return self.bstack1111lll11l1_opy_ and self.bstack1111llllll1_opy_()
    def bstack1111llllll1_opy_(self):
        bstack1111lllll1l_opy_ = os.getenv(bstack1ll_opy_ (u"ࠧࡇࡔࡄࡑࡊ࡝ࡏࡓࡍࡢ࡙ࡘࡋࡄࠨẮ"), self.config.get(bstack1ll_opy_ (u"ࠨࡨࡵࡥࡲ࡫ࡷࡰࡴ࡮ࠫắ"), None))
        return bstack1111lllll1l_opy_ in bstack11l1l1lll11_opy_
    def __111l1111111_opy_(self):
        bstack11l1ll1111l_opy_ = False
        for fw in bstack11l11lllll1_opy_:
            if fw in self.config.get(bstack1ll_opy_ (u"ࠩࡩࡶࡦࡳࡥࡸࡱࡵ࡯ࠬẰ"), bstack1ll_opy_ (u"ࠪࠫằ")):
                bstack11l1ll1111l_opy_ = True
        return bstack11l11lllll_opy_(self.config.get(bstack1ll_opy_ (u"ࠫࡹ࡫ࡳࡵࡑࡥࡷࡪࡸࡶࡢࡤ࡬ࡰ࡮ࡺࡹࠨẲ"), bstack11l1ll1111l_opy_))
    def bstack1111lll1l11_opy_(self):
        return (not self.bstack1111lll1_opy_() and
                self.bstack1l11l1lll_opy_ is not None and self.bstack1l11l1lll_opy_.bstack1111lll1_opy_())
    def bstack1111lllllll_opy_(self):
        if not self.bstack1111lll1l11_opy_():
            return
        if self.config.get(bstack1ll_opy_ (u"ࠬࡶࡲࡰ࡬ࡨࡧࡹࡔࡡ࡮ࡧࠪẳ"), None) is None or self.config.get(bstack1ll_opy_ (u"࠭ࡢࡶ࡫࡯ࡨࡓࡧ࡭ࡦࠩẴ"), os.path.basename(os.getcwd())) is None:
            self.logger.info(bstack1ll_opy_ (u"ࠢࡕࡧࡶࡸࠥࡘࡥࡰࡴࡧࡩࡷ࡯࡮ࡨࠢࡦࡥࡳ࠭ࡴࠡࡹࡲࡶࡰࠦࡡࡴࠢࡥࡹ࡮ࡲࡤࡏࡣࡰࡩࠥࡵࡲࠡࡲࡵࡳ࡯࡫ࡣࡵࡐࡤࡱࡪࠦࡩࡴࠢࡱࡹࡱࡲ࠮ࠡࡒ࡯ࡩࡦࡹࡥࠡࡵࡨࡸࠥࡧࠠ࡯ࡱࡱ࠱ࡳࡻ࡬࡭ࠢࡹࡥࡱࡻࡥ࠯ࠤẵ"))
        if not self.__111l1111111_opy_():
            self.logger.info(bstack1ll_opy_ (u"ࠣࡖࡨࡷࡹࠦࡒࡦࡱࡵࡨࡪࡸࡩ࡯ࡩࠣࡧࡦࡴࠧࡵࠢࡺࡳࡷࡱࠠࡢࡵࠣࡸࡪࡹࡴࡓࡧࡳࡳࡷࡺࡩ࡯ࡩࠣ࡭ࡸࠦࡤࡪࡵࡤࡦࡱ࡫ࡤ࠯ࠢࡓࡰࡪࡧࡳࡦࠢࡨࡲࡦࡨ࡬ࡦࠢ࡬ࡸࠥ࡬ࡲࡰ࡯ࠣࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬࠰ࡼࡱࡱࠦࡦࡪ࡮ࡨ࠲ࠧẶ"))
    def bstack1111llll1l1_opy_(self):
        return self.bstack11111l1lll_opy_
    def bstack111111lll1_opy_(self, bstack1111llll1ll_opy_):
        self.bstack11111l1lll_opy_ = bstack1111llll1ll_opy_
        self.bstack1lllllll1l1_opy_(bstack1ll_opy_ (u"ࠤࡤࡴࡵࡲࡩࡦࡦࠥặ"), bstack1111llll1ll_opy_)
    def bstack1llllll1ll1_opy_(self, test_files):
        try:
            if test_files is None:
                self.logger.debug(bstack1ll_opy_ (u"ࠥ࡟ࡷ࡫࡯ࡳࡦࡨࡶࡤࡺࡥࡴࡶࡢࡪ࡮ࡲࡥࡴ࡟ࠣࡒࡴࠦࡴࡦࡵࡷࠤ࡫࡯࡬ࡦࡵࠣࡴࡷࡵࡶࡪࡦࡨࡨࠥ࡬࡯ࡳࠢࡲࡶࡩ࡫ࡲࡪࡰࡪ࠲ࠧẸ"))
                return None
            orchestration_strategy = None
            orchestration_metadata = self.bstack1l11l1lll_opy_.bstack1111llll11l_opy_()
            if self.bstack1l11l1lll_opy_ is not None:
                orchestration_strategy = self.bstack1l11l1lll_opy_.bstack111ll111_opy_()
            if orchestration_strategy is None:
                self.logger.error(bstack1ll_opy_ (u"ࠦࡔࡸࡣࡩࡧࡶࡸࡷࡧࡴࡪࡱࡱࠤࡸࡺࡲࡢࡶࡨ࡫ࡾࠦࡩࡴࠢࡑࡳࡳ࡫࠮ࠡࡅࡤࡲࡳࡵࡴࠡࡲࡵࡳࡨ࡫ࡥࡥࠢࡺ࡭ࡹ࡮ࠠࡵࡧࡶࡸࠥࡵࡲࡤࡪࡨࡷࡹࡸࡡࡵ࡫ࡲࡲࠥࡹࡥࡴࡵ࡬ࡳࡳ࠴ࠢẹ"))
                return None
            self.logger.info(bstack1ll_opy_ (u"ࠧࡘࡥࡰࡴࡧࡩࡷ࡯࡮ࡨࠢࡷࡩࡸࡺࠠࡧ࡫࡯ࡩࡸࠦࡷࡪࡶ࡫ࠤࡴࡸࡣࡩࡧࡶࡸࡷࡧࡴࡪࡱࡱࠤࡸࡺࡲࡢࡶࡨ࡫ࡾࡀࠠࡼࡿࠥẺ").format(orchestration_strategy))
            if cli.is_running():
                self.logger.debug(bstack1ll_opy_ (u"ࠨࡕࡴ࡫ࡱ࡫ࠥࡉࡌࡊࠢࡩࡰࡴࡽࠠࡧࡱࡵࠤࡹ࡫ࡳࡵࠢࡩ࡭ࡱ࡫ࡳࠡࡱࡵࡧ࡭࡫ࡳࡵࡴࡤࡸ࡮ࡵ࡮࠯ࠤẻ"))
                ordered_test_files = cli.test_orchestration_session(test_files, orchestration_strategy, json.dumps(orchestration_metadata))
            else:
                self.logger.debug(bstack1ll_opy_ (u"ࠢࡖࡵ࡬ࡲ࡬ࠦࡳࡥ࡭ࠣࡪࡱࡵࡷࠡࡨࡲࡶࠥࡺࡥࡴࡶࠣࡪ࡮ࡲࡥࡴࠢࡲࡶࡨ࡮ࡥࡴࡶࡵࡥࡹ࡯࡯࡯࠰ࠥẼ"))
                self.bstack1111lllll11_opy_.bstack1111lll11ll_opy_(test_files, orchestration_strategy, orchestration_metadata)
                ordered_test_files = self.bstack1111lllll11_opy_.bstack1111llll111_opy_()
            if not ordered_test_files:
                return None
            self.bstack1lllllll1l1_opy_(bstack1ll_opy_ (u"ࠣࡷࡳࡰࡴࡧࡤࡦࡦࡗࡩࡸࡺࡆࡪ࡮ࡨࡷࡈࡵࡵ࡯ࡶࠥẽ"), len(test_files))
            self.bstack1lllllll1l1_opy_(bstack1ll_opy_ (u"ࠤࡱࡳࡩ࡫ࡉ࡯ࡦࡨࡼࠧẾ"), int(os.environ.get(bstack1ll_opy_ (u"ࠥࡆࡗࡕࡗࡔࡇࡕࡗ࡙ࡇࡃࡌࡡࡑࡓࡉࡋ࡟ࡊࡐࡇࡉ࡝ࠨế")) or bstack1ll_opy_ (u"ࠦ࠵ࠨỀ")))
            self.bstack1lllllll1l1_opy_(bstack1ll_opy_ (u"ࠧࡺ࡯ࡵࡣ࡯ࡒࡴࡪࡥࡴࠤề"), int(os.environ.get(bstack1ll_opy_ (u"ࠨࡂࡓࡑ࡚ࡗࡊࡘࡓࡕࡃࡆࡏࡤࡔࡏࡅࡇࡢࡇࡔ࡛ࡎࡕࠤỂ")) or bstack1ll_opy_ (u"ࠢ࠲ࠤể")))
            self.bstack1lllllll1l1_opy_(bstack1ll_opy_ (u"ࠣࡦࡲࡻࡳࡲ࡯ࡢࡦࡨࡨ࡙࡫ࡳࡵࡈ࡬ࡰࡪࡹࡃࡰࡷࡱࡸࠧỄ"), len(ordered_test_files))
            self.bstack1lllllll1l1_opy_(bstack1ll_opy_ (u"ࠤࡶࡴࡱ࡯ࡴࡕࡧࡶࡸࡸࡇࡐࡊࡅࡤࡰࡱࡉ࡯ࡶࡰࡷࠦễ"), self.bstack1111lllll11_opy_.bstack1111lll1ll1_opy_())
            return ordered_test_files
        except Exception as e:
            self.logger.debug(bstack1ll_opy_ (u"ࠥ࡟ࡷ࡫࡯ࡳࡦࡨࡶࡤࡺࡥࡴࡶࡢࡪ࡮ࡲࡥࡴ࡟ࠣࡉࡷࡸ࡯ࡳࠢ࡬ࡲࠥࡵࡲࡥࡧࡵ࡭ࡳ࡭ࠠࡵࡧࡶࡸࠥࡩ࡬ࡢࡵࡶࡩࡸࡀࠠࡼࡿࠥỆ").format(e))
        return None
    def bstack1lllllll1l1_opy_(self, key, value):
        self.bstack1111lll1lll_opy_[key] = value
    def bstack1l1l1lllll_opy_(self):
        return self.bstack1111lll1lll_opy_