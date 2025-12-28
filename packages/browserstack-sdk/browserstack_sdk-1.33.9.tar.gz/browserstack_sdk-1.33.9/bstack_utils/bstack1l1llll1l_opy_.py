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
class bstack111l1ll1_opy_:
    def __init__(self, handler):
        self._1llll1ll1111_opy_ = None
        self.handler = handler
        self._1llll1ll11l1_opy_ = self.bstack1llll1ll111l_opy_()
        self.patch()
    def patch(self):
        self._1llll1ll1111_opy_ = self._1llll1ll11l1_opy_.execute
        self._1llll1ll11l1_opy_.execute = self.bstack1llll1l1llll_opy_()
    def bstack1llll1l1llll_opy_(self):
        def execute(this, driver_command, *args, **kwargs):
            self.handler(bstack1ll_opy_ (u"ࠨࡢࡦࡨࡲࡶࡪࠨₐ"), driver_command, None, this, args)
            response = self._1llll1ll1111_opy_(this, driver_command, *args, **kwargs)
            self.handler(bstack1ll_opy_ (u"ࠢࡢࡨࡷࡩࡷࠨₑ"), driver_command, response)
            return response
        return execute
    def reset(self):
        self._1llll1ll11l1_opy_.execute = self._1llll1ll1111_opy_
    @staticmethod
    def bstack1llll1ll111l_opy_():
        from selenium.webdriver.remote.webdriver import WebDriver
        return WebDriver