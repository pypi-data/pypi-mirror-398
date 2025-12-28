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
import builtins
import logging
class bstack111l1l1l1l_opy_:
    def __init__(self, handler):
        self._11l1ll1l1l1_opy_ = builtins.print
        self.handler = handler
        self._started = False
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self._11l1ll1l11l_opy_ = {
            level: getattr(self.logger, level)
            for level in [bstack1ll_opy_ (u"ࠬ࡯࡮ࡧࡱࠪ៤"), bstack1ll_opy_ (u"࠭ࡤࡦࡤࡸ࡫ࠬ៥"), bstack1ll_opy_ (u"ࠧࡸࡣࡵࡲ࡮ࡴࡧࠨ៦"), bstack1ll_opy_ (u"ࠨࡧࡵࡶࡴࡸࠧ៧")]
        }
    def start(self):
        if self._started:
            return
        self._started = True
        builtins.print = self._11l1ll11l1l_opy_
        self._11l1ll1l111_opy_()
    def _11l1ll11l1l_opy_(self, *args, **kwargs):
        self._11l1ll1l1l1_opy_(*args, **kwargs)
        message = bstack1ll_opy_ (u"ࠩࠣࠫ៨").join(map(str, args)) + bstack1ll_opy_ (u"ࠪࡠࡳ࠭៩")
        self._11l1ll11ll1_opy_(bstack1ll_opy_ (u"ࠫࡎࡔࡆࡐࠩ៪"), message)
    def _11l1ll11ll1_opy_(self, level, msg, *args, **kwargs):
        if self.handler:
            self.handler({bstack1ll_opy_ (u"ࠬࡲࡥࡷࡧ࡯ࠫ៫"): level, bstack1ll_opy_ (u"࠭࡭ࡦࡵࡶࡥ࡬࡫ࠧ៬"): msg})
    def _11l1ll1l111_opy_(self):
        for level, bstack11l1ll11lll_opy_ in self._11l1ll1l11l_opy_.items():
            setattr(logging, level, self._11l1ll11l11_opy_(level, bstack11l1ll11lll_opy_))
    def _11l1ll11l11_opy_(self, level, bstack11l1ll11lll_opy_):
        def wrapper(msg, *args, **kwargs):
            bstack11l1ll11lll_opy_(msg, *args, **kwargs)
            self._11l1ll11ll1_opy_(level.upper(), msg)
        return wrapper
    def reset(self):
        if not self._started:
            return
        self._started = False
        builtins.print = self._11l1ll1l1l1_opy_
        for level, bstack11l1ll11lll_opy_ in self._11l1ll1l11l_opy_.items():
            setattr(logging, level, bstack11l1ll11lll_opy_)