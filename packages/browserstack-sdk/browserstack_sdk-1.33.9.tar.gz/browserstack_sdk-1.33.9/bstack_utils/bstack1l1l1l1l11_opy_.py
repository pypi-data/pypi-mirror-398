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
import threading
from collections import deque
from bstack_utils.constants import *
class bstack1l1lll11l1_opy_:
    def __init__(self):
        self._1llllll1l11l_opy_ = deque()
        self._1lllllll111l_opy_ = {}
        self._1llllll1l1ll_opy_ = False
        self._lock = threading.RLock()
    def bstack1lllllll1111_opy_(self, test_name, bstack1llllll1ll1l_opy_):
        with self._lock:
            bstack1llllll1lll1_opy_ = self._1lllllll111l_opy_.get(test_name, {})
            return bstack1llllll1lll1_opy_.get(bstack1llllll1ll1l_opy_, 0)
    def bstack1llllll1l111_opy_(self, test_name, bstack1llllll1ll1l_opy_):
        with self._lock:
            bstack1llllll1l1l1_opy_ = self.bstack1lllllll1111_opy_(test_name, bstack1llllll1ll1l_opy_)
            self.bstack1llllll11lll_opy_(test_name, bstack1llllll1ll1l_opy_)
            return bstack1llllll1l1l1_opy_
    def bstack1llllll11lll_opy_(self, test_name, bstack1llllll1ll1l_opy_):
        with self._lock:
            if test_name not in self._1lllllll111l_opy_:
                self._1lllllll111l_opy_[test_name] = {}
            bstack1llllll1lll1_opy_ = self._1lllllll111l_opy_[test_name]
            bstack1llllll1l1l1_opy_ = bstack1llllll1lll1_opy_.get(bstack1llllll1ll1l_opy_, 0)
            bstack1llllll1lll1_opy_[bstack1llllll1ll1l_opy_] = bstack1llllll1l1l1_opy_ + 1
    def bstack1llll11l1l_opy_(self, bstack1llllll1ll11_opy_, bstack1lllllll11l1_opy_):
        bstack1llllll1llll_opy_ = self.bstack1llllll1l111_opy_(bstack1llllll1ll11_opy_, bstack1lllllll11l1_opy_)
        event_name = bstack11l1l11ll1l_opy_[bstack1lllllll11l1_opy_]
        bstack1l1l1111lll_opy_ = bstack1ll_opy_ (u"ࠧࢁࡽ࠮ࡽࢀ࠱ࢀࢃࠢΉ").format(bstack1llllll1ll11_opy_, event_name, bstack1llllll1llll_opy_)
        with self._lock:
            self._1llllll1l11l_opy_.append(bstack1l1l1111lll_opy_)
    def bstack11l111ll1_opy_(self):
        with self._lock:
            return len(self._1llllll1l11l_opy_) == 0
    def bstack1ll1ll11_opy_(self):
        with self._lock:
            if self._1llllll1l11l_opy_:
                bstack1lllllll11ll_opy_ = self._1llllll1l11l_opy_.popleft()
                return bstack1lllllll11ll_opy_
            return None
    def capturing(self):
        with self._lock:
            return self._1llllll1l1ll_opy_
    def bstack11l11l1l_opy_(self):
        with self._lock:
            self._1llllll1l1ll_opy_ = True
    def bstack11l1l11l_opy_(self):
        with self._lock:
            self._1llllll1l1ll_opy_ = False