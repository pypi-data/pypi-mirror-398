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
import logging
import abc
from browserstack_sdk.sdk_cli.bstack1lllll1ll1l_opy_ import bstack1lllll1l1l1_opy_
class bstack1ll1lll1l1l_opy_(abc.ABC):
    bin_session_id: str
    bstack1lllll1ll1l_opy_: bstack1lllll1l1l1_opy_
    def __init__(self):
        self.bstack1ll1l11lll1_opy_ = None
        self.config = None
        self.bin_session_id = None
        self.bstack1lllll1ll1l_opy_ = None
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
    def bstack1lll111llll_opy_(self):
        return (self.bstack1ll1l11lll1_opy_ != None and self.bin_session_id != None and self.bstack1lllll1ll1l_opy_ != None)
    def configure(self, bstack1ll1l11lll1_opy_, config, bin_session_id: str, bstack1lllll1ll1l_opy_: bstack1lllll1l1l1_opy_):
        self.bstack1ll1l11lll1_opy_ = bstack1ll1l11lll1_opy_
        self.config = config
        self.bin_session_id = bin_session_id
        self.bstack1lllll1ll1l_opy_ = bstack1lllll1ll1l_opy_
        if self.bin_session_id:
            self.logger.debug(bstack1ll_opy_ (u"ࠤ࡞ࡿ࡮ࡪࠨࡴࡧ࡯ࡪ࠮ࢃ࡝ࠡࡥࡲࡲ࡫࡯ࡧࡶࡴࡨࡨࠥࡳ࡯ࡥࡷ࡯ࡩࠥࢁࡳࡦ࡮ࡩ࠲ࡤࡥࡣ࡭ࡣࡶࡷࡤࡥ࠮ࡠࡡࡱࡥࡲ࡫࡟ࡠࡿ࠽ࠤࡧ࡯࡮ࡠࡵࡨࡷࡸ࡯࡯࡯ࡡ࡬ࡨࡂࠨከ") + str(self.bin_session_id) + bstack1ll_opy_ (u"ࠥࠦኩ"))
    def bstack1ll111lll11_opy_(self):
        if not self.bin_session_id:
            raise ValueError(bstack1ll_opy_ (u"ࠦࡧ࡯࡮ࡠࡵࡨࡷࡸ࡯࡯࡯ࡡ࡬ࡨࠥࡩࡡ࡯ࡰࡲࡸࠥࡨࡥࠡࡐࡲࡲࡪࠨኪ"))
    @abc.abstractmethod
    def is_enabled(self) -> bool:
        return False