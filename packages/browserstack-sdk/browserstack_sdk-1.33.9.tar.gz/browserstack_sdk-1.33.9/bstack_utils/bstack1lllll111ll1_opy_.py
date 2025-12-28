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
import logging
logger = logging.getLogger(__name__)
bstack1lllll111111_opy_ = 1000
bstack1lllll111l1l_opy_ = 2
class bstack1llll1llll1l_opy_:
    def __init__(self, handler, bstack1lllll1111ll_opy_=bstack1lllll111111_opy_, bstack1llll1lllll1_opy_=bstack1lllll111l1l_opy_):
        self.queue = []
        self.handler = handler
        self.bstack1lllll1111ll_opy_ = bstack1lllll1111ll_opy_
        self.bstack1llll1lllll1_opy_ = bstack1llll1lllll1_opy_
        self.lock = threading.Lock()
        self.timer = None
        self.bstack1lllll1ll11_opy_ = None
    def start(self):
        if not (self.timer and self.timer.is_alive()):
            self.bstack1lllll111l11_opy_()
    def bstack1lllll111l11_opy_(self):
        self.bstack1lllll1ll11_opy_ = threading.Event()
        def bstack1lllll1111l1_opy_():
            self.bstack1lllll1ll11_opy_.wait(self.bstack1llll1lllll1_opy_)
            if not self.bstack1lllll1ll11_opy_.is_set():
                self.bstack1llll1llllll_opy_()
        self.timer = threading.Thread(target=bstack1lllll1111l1_opy_, daemon=True)
        self.timer.start()
    def bstack1lllll11111l_opy_(self):
        try:
            if self.bstack1lllll1ll11_opy_ and not self.bstack1lllll1ll11_opy_.is_set():
                self.bstack1lllll1ll11_opy_.set()
            if self.timer and self.timer.is_alive() and self.timer != threading.current_thread():
                self.timer.join()
        except Exception as e:
            logger.debug(bstack1ll_opy_ (u"ࠪ࡟ࡸࡺ࡯ࡱࡡࡷ࡭ࡲ࡫ࡲ࡞ࠢࡈࡼࡨ࡫ࡰࡵ࡫ࡲࡲ࠿ࠦࠧ⁀") + (str(e) or bstack1ll_opy_ (u"ࠦࡊࡾࡣࡦࡲࡷ࡭ࡴࡴࠠࡤࡱࡸࡰࡩࠦ࡮ࡰࡶࠣࡦࡪࠦࡣࡰࡰࡹࡩࡷࡺࡥࡥࠢࡷࡳࠥࡹࡴࡳ࡫ࡱ࡫ࠧ⁁")))
        finally:
            self.timer = None
    def bstack1lllll111lll_opy_(self):
        if self.timer:
            self.bstack1lllll11111l_opy_()
        self.bstack1lllll111l11_opy_()
    def add(self, event):
        with self.lock:
            self.queue.append(event)
            if len(self.queue) >= self.bstack1lllll1111ll_opy_:
                threading.Thread(target=self.bstack1llll1llllll_opy_).start()
    def bstack1llll1llllll_opy_(self, source = bstack1ll_opy_ (u"ࠬ࠭⁂")):
        with self.lock:
            if not self.queue:
                self.bstack1lllll111lll_opy_()
                return
            data = self.queue[:self.bstack1lllll1111ll_opy_]
            del self.queue[:self.bstack1lllll1111ll_opy_]
        self.handler(data)
        if source != bstack1ll_opy_ (u"࠭ࡳࡩࡷࡷࡨࡴࡽ࡮ࠨ⁃"):
            self.bstack1lllll111lll_opy_()
    def shutdown(self):
        self.bstack1lllll11111l_opy_()
        while self.queue:
            self.bstack1llll1llllll_opy_(source=bstack1ll_opy_ (u"ࠧࡴࡪࡸࡸࡩࡵࡷ࡯ࠩ⁄"))