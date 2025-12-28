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
import multiprocessing
import os
import json
from time import sleep
import time
import bstack_utils.accessibility as bstack1llll1l11_opy_
from browserstack_sdk.bstack1l1111lll_opy_ import *
from bstack_utils.config import Config
from bstack_utils.messages import bstack1111ll11_opy_, bstack1llllllll11_opy_
from bstack_utils.bstack1l11l1lll_opy_ import bstack11llll11l1_opy_
from bstack_utils.constants import bstack1lllllll111_opy_
from bstack_utils.bstack1llllll11l_opy_ import bstack1ll1l1111l_opy_
from bstack_utils.bstack11111l1l1l_opy_ import bstack1lllllll1ll_opy_
class bstack1l111ll1l_opy_:
    def __init__(self, args, logger, bstack11111ll111_opy_, bstack1111111l1l_opy_):
        self.args = args
        self.logger = logger
        self.bstack11111ll111_opy_ = bstack11111ll111_opy_
        self.bstack1111111l1l_opy_ = bstack1111111l1l_opy_
        self._prepareconfig = None
        self.Config = None
        self.runner = None
        self.bstack1ll11l111_opy_ = []
        self.bstack1111111lll_opy_ = []
        self.bstack1l1ll111ll_opy_ = []
        self.bstack1111111111_opy_ = self.bstack11ll1lll_opy_()
        self.bstack111lll1lll_opy_ = -1
    def bstack1l1ll1l11_opy_(self, bstack1llllll1l1l_opy_):
        self.parse_args()
        self.bstack1111111l11_opy_()
        self.bstack11111111l1_opy_(bstack1llllll1l1l_opy_)
        self.bstack111111l111_opy_()
    def bstack11ll1ll11l_opy_(self):
        bstack1llllll11l_opy_ = bstack1ll1l1111l_opy_.bstack11lll1111_opy_(self.bstack11111ll111_opy_, self.logger)
        if bstack1llllll11l_opy_ is None:
            self.logger.warn(bstack1ll_opy_ (u"ࠦࡔࡸࡣࡩࡧࡶࡸࡷࡧࡴࡪࡱࡱࠤ࡭ࡧ࡮ࡥ࡮ࡨࡶࠥ࡯ࡳࠡࡰࡲࡸࠥ࡯࡮ࡪࡶ࡬ࡥࡱ࡯ࡺࡦࡦ࠱ࠤࡘࡱࡩࡱࡲ࡬ࡲ࡬ࠦ࡯ࡳࡥ࡫ࡩࡸࡺࡲࡢࡶ࡬ࡳࡳ࠴ࠢ႖"))
            return
        bstack11111l1lll_opy_ = False
        bstack1llllll11l_opy_.bstack1lllllll1l1_opy_(bstack1ll_opy_ (u"ࠧ࡫࡮ࡢࡤ࡯ࡩࡩࠨ႗"), bstack1llllll11l_opy_.bstack1111lll1_opy_())
        start_time = time.time()
        if bstack1llllll11l_opy_.bstack1111lll1_opy_():
            test_files = self.bstack111111llll_opy_()
            bstack11111l1lll_opy_ = True
            bstack11111l1l11_opy_ = bstack1llllll11l_opy_.bstack1llllll1ll1_opy_(test_files)
            if bstack11111l1l11_opy_:
                self.bstack1ll11l111_opy_ = [os.path.normpath(item) for item in bstack11111l1l11_opy_]
                self.__111111111l_opy_()
                bstack1llllll11l_opy_.bstack111111lll1_opy_(bstack11111l1lll_opy_)
                self.logger.info(bstack1ll_opy_ (u"ࠨࡔࡦࡵࡷࡷࠥࡸࡥࡰࡴࡧࡩࡷ࡫ࡤࠡࡷࡶ࡭ࡳ࡭ࠠࡰࡴࡦ࡬ࡪࡹࡴࡳࡣࡷ࡭ࡴࡴ࠺ࠡࡽࢀࠦ႘").format(self.bstack1ll11l111_opy_))
            else:
                self.logger.info(bstack1ll_opy_ (u"ࠢࡏࡱࠣࡸࡪࡹࡴࠡࡨ࡬ࡰࡪࡹࠠࡸࡧࡵࡩࠥࡸࡥࡰࡴࡧࡩࡷ࡫ࡤࠡࡤࡼࠤࡴࡸࡣࡩࡧࡶࡸࡷࡧࡴࡪࡱࡱ࠲ࠧ႙"))
        bstack1llllll11l_opy_.bstack1lllllll1l1_opy_(bstack1ll_opy_ (u"ࠣࡶ࡬ࡱࡪ࡚ࡡ࡬ࡧࡱࡘࡴࡇࡰࡱ࡮ࡼࠦႚ"), int((time.time() - start_time) * 1000)) # bstack111111l1ll_opy_ to bstack11111l111l_opy_
    def __111111111l_opy_(self):
        bstack1ll_opy_ (u"ࠤࠥࠦࠏࠦࠠࠡࠢࠣࠤࠥࠦࡒࡦࡲ࡯ࡥࡨ࡫ࠠࡵࡧࡶࡸࠥ࡬ࡩ࡭ࡧࠣࡴࡦࡺࡨࡴࠢ࡬ࡲࠥࡉࡌࡊࠢࡩࡰࡦ࡭ࡳࠡࡹ࡬ࡸ࡭ࠦ࡯ࡳࡥ࡫ࡩࡸࡺࡲࡢࡶࡨࡨࠥ࡬ࡩ࡭ࡧࠣࡴࡦࡺࡨࡴ࠰ࠍࠤࠥࠦࠠࠡࠢࠣࠤࡔࡸࡣࡩࡧࡶࡸࡷࡧࡴࡪࡱࡱࠤࡸ࡫ࡲࡷࡧࡵࠤࡷ࡫ࡴࡶࡴࡱࡷࠥࡸࡥࡰࡴࡧࡩࡷ࡫ࡤࠡࡨ࡬ࡰࡪࠦ࡮ࡢ࡯ࡨࡷ࠱ࠦࡡ࡯ࡦࠣࡻࡪࠦࡳࡪ࡯ࡳࡰࡾࠦࡵࡱࡦࡤࡸࡪࠐࠠࠡࠢࠣࠤࠥࠦࠠࡵࡪࡨࠤࡈࡒࡉࠡࡣࡵ࡫ࡸࠦࡴࡰࠢࡸࡷࡪࠦࡴࡩࡱࡶࡩࠥ࡬ࡩ࡭ࡧࡶ࠲࡛ࠥࡳࡦࡴࠪࡷࠥ࡬ࡩ࡭ࡶࡨࡶ࡮ࡴࡧࠡࡨ࡯ࡥ࡬ࡹࠠࠩ࠯ࡰ࠰ࠥ࠳࡫ࠪࠢࡵࡩࡲࡧࡩ࡯ࠌࠣࠤࠥࠦࠠࠡࠢࠣ࡭ࡳࡺࡡࡤࡶࠣࡥࡳࡪࠠࡸ࡫࡯ࡰࠥࡨࡥࠡࡣࡳࡴࡱ࡯ࡥࡥࠢࡱࡥࡹࡻࡲࡢ࡮࡯ࡽࠥࡪࡵࡳ࡫ࡱ࡫ࠥࡶࡹࡵࡧࡶࡸࠥࡩ࡯࡭࡮ࡨࡧࡹ࡯࡯࡯࠰ࠍࠤࠥࠦࠠࠡࠢࠣࠤࠧࠨࠢႛ")
        try:
            if not self.bstack1ll11l111_opy_:
                self.logger.debug(bstack1ll_opy_ (u"ࠥࡒࡴࠦ࡯ࡳࡥ࡫ࡩࡸࡺࡲࡢࡶࡨࡨࠥ࡬ࡩ࡭ࡧࡶࠤࡵࡧࡴࡩࠢࡷࡳࠥࡹࡥࡵࠤႜ"))
                return
            bstack1llllll1lll_opy_ = []
            for flag in self.bstack1111111lll_opy_:
                if flag.startswith(bstack1ll_opy_ (u"ࠫ࠲࠭ႝ")):
                    bstack1llllll1lll_opy_.append(flag)
                    continue
                bstack11111l11l1_opy_ = False
                if bstack1ll_opy_ (u"ࠬࡀ࠺ࠨ႞") in flag:
                    bstack111111l11l_opy_ = flag.split(bstack1ll_opy_ (u"࠭࠺࠻ࠩ႟"), 1)[0]
                    if os.path.exists(bstack111111l11l_opy_):
                        bstack11111l11l1_opy_ = True
                elif os.path.exists(flag):
                    if os.path.isdir(flag) or (os.path.isfile(flag) and flag.endswith(bstack1ll_opy_ (u"ࠧ࠯ࡲࡼࠫႠ"))):
                        bstack11111l11l1_opy_ = True
                if not bstack11111l11l1_opy_:
                    bstack1llllll1lll_opy_.append(flag)
            bstack1llllll1lll_opy_.extend(self.bstack1ll11l111_opy_)
            self.bstack1111111lll_opy_ = bstack1llllll1lll_opy_
        except Exception as e:
            self.logger.error(bstack1ll_opy_ (u"ࠣࡇࡻࡧࡪࡶࡴࡪࡱࡱࠤࡼ࡮ࡩ࡭ࡧࠣࡷࡪࡺࡴࡪࡰࡪࠤࡴࡸࡣࡩࡧࡶࡸࡷࡧࡴࡦࡦࠣࡷࡪࡲࡥࡤࡶࡲࡶࡸࡀࠠࡼࡿࠥႡ").format(str(e)))
    @staticmethod
    def version():
        import pytest
        return pytest.__version__
    @staticmethod
    def bstack111111ll1l_opy_():
        return bstack1lllllll1ll_opy_(bstack1ll_opy_ (u"ࠩࡳࡽࡹ࡫ࡳࡵࡡࡶࡩࡱ࡫࡮ࡪࡷࡰࠫႢ"))
    def bstack11111111ll_opy_(self, arg):
        if arg in self.args:
            i = self.args.index(arg)
            self.args.pop(i + 1)
            self.args.pop(i)
    def parse_args(self):
        self.bstack111lll1lll_opy_ = -1
        if self.bstack1111111l1l_opy_ and bstack1ll_opy_ (u"ࠪࡴࡦࡸࡡ࡭࡮ࡨࡰࡸࡖࡥࡳࡒ࡯ࡥࡹ࡬࡯ࡳ࡯ࠪႣ") in self.bstack11111ll111_opy_:
            self.bstack111lll1lll_opy_ = int(self.bstack11111ll111_opy_[bstack1ll_opy_ (u"ࠫࡵࡧࡲࡢ࡮࡯ࡩࡱࡹࡐࡦࡴࡓࡰࡦࡺࡦࡰࡴࡰࠫႤ")])
        try:
            bstack1llllllll1l_opy_ = [bstack1ll_opy_ (u"ࠬ࠳࠭ࡥࡴ࡬ࡺࡪࡸࠧႥ"), bstack1ll_opy_ (u"࠭࠭࠮ࡲ࡯ࡹ࡬࡯࡮ࡴࠩႦ"), bstack1ll_opy_ (u"ࠧ࠮ࡲࠪႧ")]
            if self.bstack111lll1lll_opy_ >= 0:
                bstack1llllllll1l_opy_.extend([bstack1ll_opy_ (u"ࠨ࠯࠰ࡲࡺࡳࡰࡳࡱࡦࡩࡸࡹࡥࡴࠩႨ"), bstack1ll_opy_ (u"ࠩ࠰ࡲࠬႩ")])
            for arg in bstack1llllllll1l_opy_:
                self.bstack11111111ll_opy_(arg)
        except Exception as exc:
            self.logger.error(str(exc))
    def get_args(self):
        return self.args
    def bstack1111111l11_opy_(self):
        bstack1111111lll_opy_ = [os.path.normpath(item) for item in self.args]
        self.bstack1111111lll_opy_ = bstack1111111lll_opy_
        return self.bstack1111111lll_opy_
    def bstack1lll1l111_opy_(self):
        try:
            from _pytest.config import _prepareconfig
            from _pytest.config import Config
            from _pytest import runner
            if not self.bstack111111ll1l_opy_():
                self.logger.warning(bstack1llllllll11_opy_)
            self._prepareconfig = _prepareconfig
            self.Config = Config
            self.runner = runner
        except Exception as e:
            self.logger.warning(bstack1ll_opy_ (u"ࠥࠩࡸࡀࠠࠦࡵࠥႪ"), bstack1111ll11_opy_, str(e))
    def bstack11111111l1_opy_(self, bstack1llllll1l1l_opy_):
        bstack1ll1l1l111_opy_ = Config.bstack11lll1111_opy_()
        if bstack1llllll1l1l_opy_:
            self.bstack1111111lll_opy_.append(bstack1ll_opy_ (u"ࠫ࠲࠳ࡳ࡬࡫ࡳࡗࡪࡹࡳࡪࡱࡱࡒࡦࡳࡥࠨႫ"))
            self.bstack1111111lll_opy_.append(bstack1ll_opy_ (u"࡚ࠬࡲࡶࡧࠪႬ"))
        if bstack1ll1l1l111_opy_.bstack111111ll11_opy_():
            self.bstack1111111lll_opy_.append(bstack1ll_opy_ (u"࠭࠭࠮ࡵ࡮࡭ࡵ࡙ࡥࡴࡵ࡬ࡳࡳ࡙ࡴࡢࡶࡸࡷࠬႭ"))
            self.bstack1111111lll_opy_.append(bstack1ll_opy_ (u"ࠧࡕࡴࡸࡩࠬႮ"))
        self.bstack1111111lll_opy_.append(bstack1ll_opy_ (u"ࠨ࠯ࡳࠫႯ"))
        self.bstack1111111lll_opy_.append(bstack1ll_opy_ (u"ࠩࡳࡽࡹ࡫ࡳࡵࡡࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫ࡱ࡮ࡸ࡫࡮ࡴࠧႰ"))
        self.bstack1111111lll_opy_.append(bstack1ll_opy_ (u"ࠪ࠱࠲ࡪࡲࡪࡸࡨࡶࠬႱ"))
        self.bstack1111111lll_opy_.append(bstack1ll_opy_ (u"ࠫࡨ࡮ࡲࡰ࡯ࡨࠫႲ"))
        if self.bstack111lll1lll_opy_ > 1:
            self.bstack1111111lll_opy_.append(bstack1ll_opy_ (u"ࠬ࠳࡮ࠨႳ"))
            self.bstack1111111lll_opy_.append(str(self.bstack111lll1lll_opy_))
    def bstack111111l111_opy_(self):
        if bstack11llll11l1_opy_.bstack111l1l111_opy_(self.bstack11111ll111_opy_):
             self.bstack1111111lll_opy_ += [
                bstack1lllllll111_opy_.get(bstack1ll_opy_ (u"࠭ࡲࡦࡴࡸࡲࠬႴ")), str(bstack11llll11l1_opy_.bstack1lll1l11ll_opy_(self.bstack11111ll111_opy_)),
                bstack1lllllll111_opy_.get(bstack1ll_opy_ (u"ࠧࡥࡧ࡯ࡥࡾ࠭Ⴕ")), str(bstack1lllllll111_opy_.get(bstack1ll_opy_ (u"ࠨࡴࡨࡶࡺࡴ࠭ࡥࡧ࡯ࡥࡾ࠭Ⴖ")))
            ]
    def bstack111111l1l1_opy_(self):
        bstack1l1ll111ll_opy_ = []
        for spec in self.bstack1ll11l111_opy_:
            bstack1l1l1llll1_opy_ = [spec]
            bstack1l1l1llll1_opy_ += self.bstack1111111lll_opy_
            bstack1l1ll111ll_opy_.append(bstack1l1l1llll1_opy_)
        self.bstack1l1ll111ll_opy_ = bstack1l1ll111ll_opy_
        return bstack1l1ll111ll_opy_
    def bstack11ll1lll_opy_(self):
        try:
            from pytest_bdd import reporting
            self.bstack1111111111_opy_ = True
            return True
        except Exception as e:
            self.bstack1111111111_opy_ = False
        return self.bstack1111111111_opy_
    def bstack1l1ll11111_opy_(self):
        bstack1ll_opy_ (u"ࠤࠥࠦࠏࠦࠠࠡࠢࠣࠤࠥࠦࡇࡦࡶࠣࡸ࡭࡫ࠠࡤࡱࡸࡲࡹࠦ࡯ࡧࠢࡷࡩࡸࡺࡳࠡࡹ࡬ࡸ࡭ࡵࡵࡵࠢࡵࡹࡳࡴࡩ࡯ࡩࠣࡸ࡭࡫࡭ࠡࡷࡶ࡭ࡳ࡭ࠠࡱࡻࡷࡩࡸࡺࠠࡤࡱ࡯ࡰࡪࡩࡴࡪࡱࡱ࠲ࠏࠦࠠࠡࠢࠣࠤࠥࠦࡒࡦࡶࡸࡶࡳࡹ࠺ࠋࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࡩ࡯ࡶ࠽ࠤ࡙࡮ࡥࠡࡶࡲࡸࡦࡲࠠ࡯ࡷࡰࡦࡪࡸࠠࡰࡨࠣࡸࡪࡹࡴࡴࠢࡦࡳࡱࡲࡥࡤࡶࡨࡨ࠳ࠐࠠࠡࠢࠣࠤࠥࠦࠠࠣࠤࠥႷ")
        try:
            from browserstack_sdk.bstack1111l111ll_opy_ import bstack11111lll11_opy_
            bstack1111111ll1_opy_ = bstack11111lll11_opy_(bstack11111ll1ll_opy_=self.bstack1111111lll_opy_)
            if not bstack1111111ll1_opy_.get(bstack1ll_opy_ (u"ࠪࡷࡺࡩࡣࡦࡵࡶࠫႸ"), False):
                self.logger.error(bstack1ll_opy_ (u"࡙ࠦ࡫ࡳࡵࠢࡦࡳࡺࡴࡴࠡࡥࡲࡰࡱ࡫ࡣࡵ࡫ࡲࡲࠥ࡬ࡡࡪ࡮ࡨࡨ࠿ࠦࡻࡾࠤႹ").format(bstack1111111ll1_opy_.get(bstack1ll_opy_ (u"ࠬ࡫ࡲࡳࡱࡵࠫႺ"), bstack1ll_opy_ (u"࠭ࡕ࡯࡭ࡱࡳࡼࡴࠠࡦࡴࡵࡳࡷ࠭Ⴛ"))))
                return 0
            count = bstack1111111ll1_opy_.get(bstack1ll_opy_ (u"ࠧࡤࡱࡸࡲࡹ࠭Ⴜ"), 0)
            self.logger.info(bstack1ll_opy_ (u"ࠣࡖࡲࡸࡦࡲࠠࡵࡧࡶࡸࡸࠦࡣࡰ࡮࡯ࡩࡨࡺࡥࡥ࠼ࠣࡿࢂࠨႽ").format(count))
            return count
        except Exception as e:
            self.logger.error(bstack1ll_opy_ (u"ࠤࡈࡼࡨ࡫ࡰࡵ࡫ࡲࡲࠥࡽࡨࡪ࡮ࡨࠤ࡬࡫ࡴࡵ࡫ࡱ࡫ࠥࡺࡥࡴࡶࠣࡧࡴࡻ࡮ࡵ࠼ࠣࡿࢂࠨႾ").format(e))
            return 0
    def bstack1lll1ll1ll_opy_(self, bstack11111l11ll_opy_, bstack1l1ll1l11_opy_):
        bstack1l1ll1l11_opy_[bstack1ll_opy_ (u"ࠪࡇࡔࡔࡆࡊࡉࠪႿ")] = self.bstack11111ll111_opy_
        multiprocessing.set_start_method(bstack1ll_opy_ (u"ࠫࡸࡶࡡࡸࡰࠪჀ"))
        bstack111llll1_opy_ = []
        manager = multiprocessing.Manager()
        bstack1lllllll11l_opy_ = manager.list()
        if bstack1ll_opy_ (u"ࠬࡶ࡬ࡢࡶࡩࡳࡷࡳࡳࠨჁ") in self.bstack11111ll111_opy_:
            for index, platform in enumerate(self.bstack11111ll111_opy_[bstack1ll_opy_ (u"࠭ࡰ࡭ࡣࡷࡪࡴࡸ࡭ࡴࠩჂ")]):
                bstack111llll1_opy_.append(multiprocessing.Process(name=str(index),
                                                            target=bstack11111l11ll_opy_,
                                                            args=(self.bstack1111111lll_opy_, bstack1l1ll1l11_opy_, bstack1lllllll11l_opy_)))
            bstack1llllllllll_opy_ = len(self.bstack11111ll111_opy_[bstack1ll_opy_ (u"ࠧࡱ࡮ࡤࡸ࡫ࡵࡲ࡮ࡵࠪჃ")])
        else:
            bstack111llll1_opy_.append(multiprocessing.Process(name=str(0),
                                                        target=bstack11111l11ll_opy_,
                                                        args=(self.bstack1111111lll_opy_, bstack1l1ll1l11_opy_, bstack1lllllll11l_opy_)))
            bstack1llllllllll_opy_ = 1
        i = 0
        for t in bstack111llll1_opy_:
            os.environ[bstack1ll_opy_ (u"ࠨࡄࡕࡓ࡜࡙ࡅࡓࡕࡗࡅࡈࡑ࡟ࡑࡎࡄࡘࡋࡕࡒࡎࡡࡌࡒࡉࡋࡘࠨჄ")] = str(i)
            if bstack1ll_opy_ (u"ࠩࡳࡰࡦࡺࡦࡰࡴࡰࡷࠬჅ") in self.bstack11111ll111_opy_:
                os.environ[bstack1ll_opy_ (u"ࠪࡇ࡚ࡘࡒࡆࡐࡗࡣࡕࡒࡁࡕࡈࡒࡖࡒࡥࡄࡂࡖࡄࠫ჆")] = json.dumps(self.bstack11111ll111_opy_[bstack1ll_opy_ (u"ࠫࡵࡲࡡࡵࡨࡲࡶࡲࡹࠧჇ")][i % bstack1llllllllll_opy_])
            i += 1
            t.start()
        for t in bstack111llll1_opy_:
            t.join()
        return list(bstack1lllllll11l_opy_)
    @staticmethod
    def bstack1l1l11111_opy_(driver, bstack11111l1111_opy_, logger, item=None, wait=False):
        item = item or getattr(threading.current_thread(), bstack1ll_opy_ (u"ࠬࡩࡵࡳࡴࡨࡲࡹࡥࡴࡦࡵࡷࡣ࡮ࡺࡥ࡮ࠩ჈"), None)
        if item and getattr(item, bstack1ll_opy_ (u"࠭࡟ࡢ࠳࠴ࡽࡤࡺࡥࡴࡶࡢࡧࡦࡹࡥࠨ჉"), None) and not getattr(item, bstack1ll_opy_ (u"ࠧࡠࡣ࠴࠵ࡾࡥࡳࡵࡱࡳࡣࡩࡵ࡮ࡦࠩ჊"), False):
            logger.info(
                bstack1ll_opy_ (u"ࠣࡃࡸࡸࡴࡳࡡࡵࡧࠣࡸࡪࡹࡴࠡࡥࡤࡷࡪࠦࡥࡹࡧࡦࡹࡹ࡯࡯࡯ࠢ࡫ࡥࡸࠦࡥ࡯ࡦࡨࡨ࠳ࠦࡐࡳࡱࡦࡩࡸࡹࡩ࡯ࡩࠣࡪࡴࡸࠠࡢࡥࡦࡩࡸࡹࡩࡣ࡫࡯࡭ࡹࡿࠠࡵࡧࡶࡸ࡮ࡴࡧࠡ࡫ࡶࠤࡺࡴࡤࡦࡴࡺࡥࡾ࠴ࠢ჋"))
            bstack11111l1ll1_opy_ = item.cls.__name__ if not item.cls is None else None
            bstack1llll1l11_opy_.bstack111111l11_opy_(driver, item.name, item.path)
            item._a11y_stop_done = True
            if wait:
                sleep(2)
    def bstack111111llll_opy_(self):
        bstack1ll_opy_ (u"ࠤࠥࠦࠏࠦࠠࠡࠢࠣࠤࠥࠦࡒࡦࡶࡸࡶࡳࡹࠠࡵࡪࡨࠤࡱ࡯ࡳࡵࠢࡲࡪࠥࡺࡥࡴࡶࠣࡪ࡮ࡲࡥࡴࠢࡷࡳࠥࡨࡥࠡࡧࡻࡩࡨࡻࡴࡦࡦ࠱ࠎࠥࠦࠠࠡࠢࠣࠤࠥࠨࠢࠣ჌")
        try:
            from browserstack_sdk.bstack1111l111ll_opy_ import bstack11111lll11_opy_
            bstack1lllllllll1_opy_ = bstack11111lll11_opy_(bstack11111ll1ll_opy_=self.bstack1111111lll_opy_)
            if not bstack1lllllllll1_opy_.get(bstack1ll_opy_ (u"ࠪࡷࡺࡩࡣࡦࡵࡶࠫჍ"), False):
                self.logger.error(bstack1ll_opy_ (u"࡙ࠦ࡫ࡳࡵࠢࡩ࡭ࡱ࡫ࠠࡤࡱ࡯ࡰࡪࡩࡴࡪࡱࡱࠤ࡫ࡧࡩ࡭ࡧࡧ࠾ࠥࢁࡽࠣ჎").format(bstack1lllllllll1_opy_.get(bstack1ll_opy_ (u"ࠬ࡫ࡲࡳࡱࡵࠫ჏"), bstack1ll_opy_ (u"࠭ࡕ࡯࡭ࡱࡳࡼࡴࠠࡦࡴࡵࡳࡷ࠭ა"))))
                return []
            test_files = bstack1lllllllll1_opy_.get(bstack1ll_opy_ (u"ࠧࡵࡧࡶࡸࡤ࡬ࡩ࡭ࡧࡶࠫბ"), [])
            count = bstack1lllllllll1_opy_.get(bstack1ll_opy_ (u"ࠨࡥࡲࡹࡳࡺࠧგ"), 0)
            self.logger.debug(bstack1ll_opy_ (u"ࠤࡆࡳࡱࡲࡥࡤࡶࡨࡨࠥࢁࡽࠡࡶࡨࡷࡹࡹࠠࡪࡰࠣࡿࢂࠦࡦࡪ࡮ࡨࡷࠧდ").format(count, len(test_files)))
            return test_files
        except Exception as e:
            self.logger.error(bstack1ll_opy_ (u"ࠥࡉࡽࡩࡥࡱࡶ࡬ࡳࡳࠦࡤࡶࡴ࡬ࡲ࡬ࠦࡴࡦࡵࡷࠤ࡫࡯࡬ࡦࡵࠣࡧࡴࡲ࡬ࡦࡥࡷ࡭ࡴࡴ࠺ࠡࡽࢀࠦე").format(e))
            return []