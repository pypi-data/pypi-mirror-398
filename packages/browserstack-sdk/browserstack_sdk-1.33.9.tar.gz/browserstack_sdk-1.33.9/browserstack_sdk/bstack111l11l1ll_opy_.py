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
class RobotHandler():
    def __init__(self, args, logger, bstack11111ll111_opy_, bstack1111111l1l_opy_):
        self.args = args
        self.logger = logger
        self.bstack11111ll111_opy_ = bstack11111ll111_opy_
        self.bstack1111111l1l_opy_ = bstack1111111l1l_opy_
    @staticmethod
    def version():
        import robot
        return robot.__version__
    @staticmethod
    def bstack111l111111_opy_(bstack1llllll11l1_opy_):
        bstack1lllll1llll_opy_ = []
        if bstack1llllll11l1_opy_:
            tokens = str(os.path.basename(bstack1llllll11l1_opy_)).split(bstack1ll_opy_ (u"ࠦࡤࠨნ"))
            camelcase_name = bstack1ll_opy_ (u"ࠧࠦࠢო").join(t.title() for t in tokens)
            suite_name, bstack1llllll111l_opy_ = os.path.splitext(camelcase_name)
            bstack1lllll1llll_opy_.append(suite_name)
        return bstack1lllll1llll_opy_
    @staticmethod
    def bstack1llllll1111_opy_(typename):
        if bstack1ll_opy_ (u"ࠨࡁࡴࡵࡨࡶࡹ࡯࡯࡯ࠤპ") in typename:
            return bstack1ll_opy_ (u"ࠢࡂࡵࡶࡩࡷࡺࡩࡰࡰࡈࡶࡷࡵࡲࠣჟ")
        return bstack1ll_opy_ (u"ࠣࡗࡱ࡬ࡦࡴࡤ࡭ࡧࡧࡉࡷࡸ࡯ࡳࠤრ")