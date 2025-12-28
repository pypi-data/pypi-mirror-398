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
import tempfile
import os
import time
from datetime import datetime
from bstack_utils.bstack11l1lll111l_opy_ import bstack11l1lll11ll_opy_
from bstack_utils.constants import bstack11l1l1ll1ll_opy_, bstack11ll11l1ll_opy_
from bstack_utils.bstack1l11l1lll_opy_ import bstack11llll11l1_opy_
from bstack_utils import bstack11l1l1lll1_opy_
bstack11l11l1l11l_opy_ = 10
class bstack1lll1111l1_opy_:
    def __init__(self, bstack11ll11l11l_opy_, config, bstack11l11ll1l11_opy_=0):
        self.bstack11l11l1llll_opy_ = set()
        self.lock = threading.Lock()
        self.bstack11l11l11ll1_opy_ = bstack1ll_opy_ (u"ࠧࢁࡽ࠰ࡶࡨࡷࡹࡵࡲࡤࡪࡨࡷࡹࡸࡡࡵ࡫ࡲࡲ࠴ࡧࡰࡪ࠱ࡹ࠵࠴࡬ࡡࡪ࡮ࡨࡨ࠲ࡺࡥࡴࡶࡶࠦᭁ").format(bstack11l1l1ll1ll_opy_)
        self.bstack11l11l1ll11_opy_ = os.path.join(tempfile.gettempdir(), bstack1ll_opy_ (u"ࠨࡡࡣࡱࡵࡸࡤࡨࡵࡪ࡮ࡧࡣࢀࢃࠢᭂ").format(os.environ.get(bstack1ll_opy_ (u"ࠧࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡔࡆࡕࡗࡌ࡚ࡈ࡟ࡖࡗࡌࡈࠬᭃ"))))
        self.bstack11l11l11l11_opy_ = os.path.join(tempfile.gettempdir(), bstack1ll_opy_ (u"ࠣࡨࡤ࡭ࡱ࡫ࡤࡠࡶࡨࡷࡹࡹ࡟ࡼࡿ࠱ࡸࡽࡺ᭄ࠢ").format(os.environ.get(bstack1ll_opy_ (u"ࠩࡅࡖࡔ࡝ࡓࡆࡔࡖࡘࡆࡉࡋࡠࡖࡈࡗ࡙ࡎࡕࡃࡡࡘ࡙ࡎࡊࠧᭅ"))))
        self.bstack11l11ll1lll_opy_ = 2
        self.bstack11ll11l11l_opy_ = bstack11ll11l11l_opy_
        self.config = config
        self.logger = bstack11l1l1lll1_opy_.get_logger(__name__, bstack11ll11l1ll_opy_)
        self.bstack11l11ll1l11_opy_ = bstack11l11ll1l11_opy_
        self.bstack11l11ll11ll_opy_ = False
        self.bstack11l11ll1111_opy_ = not (
                            os.environ.get(bstack1ll_opy_ (u"ࠥࡆࡗࡕࡗࡔࡇࡕࡗ࡙ࡇࡃࡌࡡࡅ࡙ࡎࡒࡄࡠࡔࡘࡒࡤࡏࡄࡆࡐࡗࡍࡋࡏࡅࡓࠤᭆ")) and
                            os.environ.get(bstack1ll_opy_ (u"ࠦࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡒࡔࡊࡅࡠࡋࡑࡈࡊ࡞ࠢᭇ")) and
                            os.environ.get(bstack1ll_opy_ (u"ࠧࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣ࡙ࡕࡔࡂࡎࡢࡒࡔࡊࡅࡠࡅࡒ࡙ࡓ࡚ࠢᭈ"))
                        )
        if bstack11llll11l1_opy_.bstack11l11l11l1l_opy_(config):
            self.bstack11l11ll1lll_opy_ = bstack11llll11l1_opy_.bstack11l11ll1ll1_opy_(config, self.bstack11l11ll1l11_opy_)
            self.bstack11l11l1ll1l_opy_()
    def bstack11l11l11lll_opy_(self):
        return bstack1ll_opy_ (u"ࠨࡻࡾࡡࡾࢁࠧᭉ").format(self.config.get(bstack1ll_opy_ (u"ࠧࡣࡷ࡬ࡰࡩࡔࡡ࡮ࡧࠪᭊ")), os.environ.get(bstack1ll_opy_ (u"ࠨࡄࡕࡓ࡜࡙ࡅࡓࡕࡗࡅࡈࡑ࡟ࡃࡗࡌࡐࡉࡥࡒࡖࡐࡢࡍࡉࡋࡎࡕࡋࡉࡍࡊࡘࠧᭋ")))
    def bstack11l11ll11l1_opy_(self):
        try:
            if self.bstack11l11ll1111_opy_:
                return
            with self.lock:
                try:
                    with open(self.bstack11l11l11l11_opy_, bstack1ll_opy_ (u"ࠤࡵࠦᭌ")) as f:
                        bstack11l11ll111l_opy_ = set(line.strip() for line in f if line.strip())
                except FileNotFoundError:
                    bstack11l11ll111l_opy_ = set()
                bstack11l11ll1l1l_opy_ = bstack11l11ll111l_opy_ - self.bstack11l11l1llll_opy_
                if not bstack11l11ll1l1l_opy_:
                    return
                self.bstack11l11l1llll_opy_.update(bstack11l11ll1l1l_opy_)
                data = {bstack1ll_opy_ (u"ࠥࡪࡦ࡯࡬ࡦࡦࡗࡩࡸࡺࡳࠣ᭍"): list(self.bstack11l11l1llll_opy_), bstack1ll_opy_ (u"ࠦࡧࡻࡩ࡭ࡦࡑࡥࡲ࡫ࠢ᭎"): self.config.get(bstack1ll_opy_ (u"ࠬࡨࡵࡪ࡮ࡧࡒࡦࡳࡥࠨ᭏")), bstack1ll_opy_ (u"ࠨࡢࡶ࡫࡯ࡨࡗࡻ࡮ࡊࡦࡨࡲࡹ࡯ࡦࡪࡧࡵࠦ᭐"): os.environ.get(bstack1ll_opy_ (u"ࠧࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡂࡖࡋࡏࡈࡤࡘࡕࡏࡡࡌࡈࡊࡔࡔࡊࡈࡌࡉࡗ࠭᭑")), bstack1ll_opy_ (u"ࠣࡲࡵࡳ࡯࡫ࡣࡵࡐࡤࡱࡪࠨ᭒"): self.config.get(bstack1ll_opy_ (u"ࠩࡳࡶࡴࡰࡥࡤࡶࡑࡥࡲ࡫ࠧ᭓"))}
            response = bstack11l1lll11ll_opy_.bstack11l11lll111_opy_(self.bstack11l11l11ll1_opy_, data)
            if response.get(bstack1ll_opy_ (u"ࠥࡷࡹࡧࡴࡶࡵࠥ᭔")) == 200:
                self.logger.debug(bstack1ll_opy_ (u"ࠦࡘࡻࡣࡤࡧࡶࡷ࡫ࡻ࡬࡭ࡻࠣࡷࡪࡴࡴࠡࡨࡤ࡭ࡱ࡫ࡤࠡࡶࡨࡷࡹࡹ࠺ࠡࡽࢀࠦ᭕").format(data))
            else:
                self.logger.debug(bstack1ll_opy_ (u"ࠧࡌࡡࡪ࡮ࡨࡨࠥࡺ࡯ࠡࡵࡨࡲࡩࠦࡦࡢ࡫࡯ࡩࡩࠦࡴࡦࡵࡷࡷ࠿ࠦࡻࡾࠤ᭖").format(response))
        except Exception as e:
            self.logger.debug(bstack1ll_opy_ (u"ࠨࡅࡹࡥࡨࡴࡹ࡯࡯࡯ࠢࡧࡹࡷ࡯࡮ࡨࠢࡶࡩࡳࡪࡩ࡯ࡩࠣࡪࡦ࡯࡬ࡦࡦࠣࡸࡪࡹࡴࡴ࠼ࠣࡿࢂࠨ᭗").format(e))
    def bstack11l11l1l111_opy_(self):
        if self.bstack11l11ll1111_opy_:
            with self.lock:
                try:
                    with open(self.bstack11l11l11l11_opy_, bstack1ll_opy_ (u"ࠢࡳࠤ᭘")) as f:
                        bstack11l11l1l1ll_opy_ = set(line.strip() for line in f if line.strip())
                    failed_count = len(bstack11l11l1l1ll_opy_)
                except FileNotFoundError:
                    failed_count = 0
                self.logger.debug(bstack1ll_opy_ (u"ࠣࡒࡲࡰࡱ࡫ࡤࠡࡨࡤ࡭ࡱ࡫ࡤࠡࡶࡨࡷࡹࡹࠠࡤࡱࡸࡲࡹࠦࠨ࡭ࡱࡦࡥࡱ࠯࠺ࠡࡽࢀࠦ᭙").format(failed_count))
                if failed_count >= self.bstack11l11ll1lll_opy_:
                    self.logger.info(bstack1ll_opy_ (u"ࠤࡗ࡬ࡷ࡫ࡳࡩࡱ࡯ࡨࠥࡩࡲࡰࡵࡶࡩࡩࠦࠨ࡭ࡱࡦࡥࡱ࠯࠺ࠡࡽࢀࠤࡃࡃࠠࡼࡿࠥ᭚").format(failed_count, self.bstack11l11ll1lll_opy_))
                    self.bstack11l11l1lll1_opy_(failed_count)
                    self.bstack11l11ll11ll_opy_ = True
            return
        try:
            response = bstack11l1lll11ll_opy_.bstack11l11l1l111_opy_(bstack1ll_opy_ (u"ࠥࡿࢂࡅࡢࡶ࡫࡯ࡨࡓࡧ࡭ࡦ࠿ࡾࢁࠫࡨࡵࡪ࡮ࡧࡖࡺࡴࡉࡥࡧࡱࡸ࡮࡬ࡩࡦࡴࡀࡿࢂࠬࡰࡳࡱ࡭ࡩࡨࡺࡎࡢ࡯ࡨࡁࢀࢃࠢ᭛").format(self.bstack11l11l11ll1_opy_, self.config.get(bstack1ll_opy_ (u"ࠫࡧࡻࡩ࡭ࡦࡑࡥࡲ࡫ࠧ᭜")), os.environ.get(bstack1ll_opy_ (u"ࠬࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣࡇ࡛ࡉࡍࡆࡢࡖ࡚ࡔ࡟ࡊࡆࡈࡒ࡙ࡏࡆࡊࡇࡕࠫ᭝")), self.config.get(bstack1ll_opy_ (u"࠭ࡰࡳࡱ࡭ࡩࡨࡺࡎࡢ࡯ࡨࠫ᭞"))))
            if response.get(bstack1ll_opy_ (u"ࠢࡴࡶࡤࡸࡺࡹࠢ᭟")) == 200:
                failed_count = response.get(bstack1ll_opy_ (u"ࠣࡨࡤ࡭ࡱ࡫ࡤࡕࡧࡶࡸࡸࡉ࡯ࡶࡰࡷࠦ᭠"), 0)
                self.logger.debug(bstack1ll_opy_ (u"ࠤࡓࡳࡱࡲࡥࡥࠢࡩࡥ࡮ࡲࡥࡥࠢࡷࡩࡸࡺࡳࠡࡥࡲࡹࡳࡺ࠺ࠡࡽࢀࠦ᭡").format(failed_count))
                if failed_count >= self.bstack11l11ll1lll_opy_:
                    self.logger.info(bstack1ll_opy_ (u"ࠥࡘ࡭ࡸࡥࡴࡪࡲࡰࡩࠦࡣࡳࡱࡶࡷࡪࡪ࠺ࠡࡽࢀࠤࡃࡃࠠࡼࡿࠥ᭢").format(failed_count, self.bstack11l11ll1lll_opy_))
                    self.bstack11l11l1lll1_opy_(failed_count)
                    self.bstack11l11ll11ll_opy_ = True
            else:
                self.logger.error(bstack1ll_opy_ (u"ࠦࡋࡧࡩ࡭ࡧࡧࠤࡹࡵࠠࡱࡱ࡯ࡰࠥ࡬ࡡࡪ࡮ࡨࡨࠥࡺࡥࡴࡶࡶ࠾ࠥࢁࡽࠣ᭣").format(response))
        except Exception as e:
            self.logger.error(bstack1ll_opy_ (u"ࠧࡋࡸࡤࡧࡳࡸ࡮ࡵ࡮ࠡࡦࡸࡶ࡮ࡴࡧࠡࡲࡲࡰࡱ࡯࡮ࡨ࠼ࠣࡿࢂࠨ᭤").format(e))
    def bstack11l11l1lll1_opy_(self, failed_count):
        with open(self.bstack11l11l1ll11_opy_, bstack1ll_opy_ (u"ࠨࡷࠣ᭥")) as f:
            f.write(bstack1ll_opy_ (u"ࠢࡕࡪࡵࡩࡸ࡮࡯࡭ࡦࠣࡧࡷࡵࡳࡴࡧࡧࠤࡦࡺࠠࡼࡿ࡟ࡲࠧ᭦").format(datetime.now()))
            f.write(bstack1ll_opy_ (u"ࠣࡈࡤ࡭ࡱ࡫ࡤࠡࡶࡨࡷࡹࡹࠠࡤࡱࡸࡲࡹࡀࠠࡼࡿ࡟ࡲࠧ᭧").format(failed_count))
        self.logger.debug(bstack1ll_opy_ (u"ࠤࡄࡦࡴࡸࡴࠡࡄࡸ࡭ࡱࡪࠠࡧ࡫࡯ࡩࠥࡩࡲࡦࡣࡷࡩࡩࡀࠠࡼࡿࠥ᭨").format(self.bstack11l11l1ll11_opy_))
    def bstack11l11l1ll1l_opy_(self):
        def bstack11l11l111ll_opy_():
            while not self.bstack11l11ll11ll_opy_:
                time.sleep(bstack11l11l1l11l_opy_)
                self.bstack11l11ll11l1_opy_()
                self.bstack11l11l1l111_opy_()
        bstack11l11l1l1l1_opy_ = threading.Thread(target=bstack11l11l111ll_opy_, daemon=True)
        bstack11l11l1l1l1_opy_.start()