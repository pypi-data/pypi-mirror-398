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
import json
import logging
import os
import datetime
import threading
from bstack_utils.constants import EVENTS, STAGE
from bstack_utils.helper import bstack11ll11llll1_opy_, bstack11ll11ll1ll_opy_, bstack1l111111_opy_, error_handler, bstack11l111ll11l_opy_, bstack11l11111ll1_opy_, bstack11l111llll1_opy_, bstack1l11l1111_opy_, bstack1l11l11l_opy_
from bstack_utils.measure import measure
from bstack_utils.bstack1lllll111ll1_opy_ import bstack1llll1llll1l_opy_
import bstack_utils.bstack1ll111ll1_opy_ as bstack1ll1l1l1l_opy_
from bstack_utils.bstack111ll1l1l1_opy_ import bstack1l11111lll_opy_
import bstack_utils.accessibility as bstack1llll1l11_opy_
from bstack_utils.bstack1111l1ll1_opy_ import bstack1111l1ll1_opy_
from bstack_utils.bstack111l1l1ll1_opy_ import bstack111l1111ll_opy_
from bstack_utils.constants import bstack11llllll11_opy_
bstack1lll1llll1ll_opy_ = bstack1ll_opy_ (u"ࠬ࡮ࡴࡵࡲࡶ࠾࠴࠵ࡣࡰ࡮࡯ࡩࡨࡺ࡯ࡳ࠯ࡲࡦࡸ࡫ࡲࡷࡣࡥ࡭ࡱ࡯ࡴࡺ࠰ࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫࠯ࡥࡲࡱࠬ⅌")
logger = logging.getLogger(__name__)
class bstack1lll1111l_opy_:
    bstack1lllll111ll1_opy_ = None
    bs_config = None
    bstack1l1llll111_opy_ = None
    @classmethod
    @error_handler(class_method=True)
    @measure(event_name=EVENTS.bstack11l1l11111l_opy_, stage=STAGE.bstack1l1lll1ll1_opy_)
    def launch(cls, bs_config, bstack1l1llll111_opy_):
        cls.bs_config = bs_config
        cls.bstack1l1llll111_opy_ = bstack1l1llll111_opy_
        try:
            cls.bstack1llll1111ll1_opy_()
            bstack11ll11111ll_opy_ = bstack11ll11llll1_opy_(bs_config)
            bstack11ll11l111l_opy_ = bstack11ll11ll1ll_opy_(bs_config)
            data = bstack1ll1l1l1l_opy_.bstack1lll1lllllll_opy_(bs_config, bstack1l1llll111_opy_)
            config = {
                bstack1ll_opy_ (u"࠭ࡡࡶࡶ࡫ࠫ⅍"): (bstack11ll11111ll_opy_, bstack11ll11l111l_opy_),
                bstack1ll_opy_ (u"ࠧࡩࡧࡤࡨࡪࡸࡳࠨⅎ"): cls.default_headers()
            }
            response = bstack1l111111_opy_(bstack1ll_opy_ (u"ࠨࡒࡒࡗ࡙࠭⅏"), cls.request_url(bstack1ll_opy_ (u"ࠩࡤࡴ࡮࠵ࡶ࠳࠱ࡥࡹ࡮ࡲࡤࡴࠩ⅐")), data, config)
            if response.status_code != 200:
                bstack11lll1ll1l_opy_ = response.json()
                if bstack11lll1ll1l_opy_[bstack1ll_opy_ (u"ࠪࡷࡺࡩࡣࡦࡵࡶࠫ⅑")] == False:
                    cls.bstack1llll111l111_opy_(bstack11lll1ll1l_opy_)
                    return
                cls.bstack1llll1111lll_opy_(bstack11lll1ll1l_opy_[bstack1ll_opy_ (u"ࠫࡴࡨࡳࡦࡴࡹࡥࡧ࡯࡬ࡪࡶࡼࠫ⅒")])
                cls.bstack1lll1lll1111_opy_(bstack11lll1ll1l_opy_[bstack1ll_opy_ (u"ࠬࡧࡣࡤࡧࡶࡷ࡮ࡨࡩ࡭࡫ࡷࡽࠬ⅓")])
                return None
            bstack1lll1lllll1l_opy_ = cls.bstack1lll1llll1l1_opy_(response)
            return bstack1lll1lllll1l_opy_, response.json()
        except Exception as error:
            logger.error(bstack1ll_opy_ (u"ࠨࡅࡹࡥࡨࡴࡹ࡯࡯࡯ࠢࡺ࡬࡮ࡲࡥࠡࡥࡵࡩࡦࡺࡩ࡯ࡩࠣࡦࡺ࡯࡬ࡥࠢࡩࡳࡷࠦࡔࡦࡵࡷࡌࡺࡨ࠺ࠡࡽࢀࠦ⅔").format(str(error)))
            return None
    @classmethod
    @error_handler(class_method=True)
    def stop(cls, bstack1lll1lll1l11_opy_=None):
        if not bstack1l11111lll_opy_.on() and not bstack1llll1l11_opy_.on():
            return
        if os.environ.get(bstack1ll_opy_ (u"ࠧࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡔࡆࡕࡗࡌ࡚ࡈ࡟ࡋ࡙ࡗࠫ⅕")) == bstack1ll_opy_ (u"ࠣࡰࡸࡰࡱࠨ⅖") or os.environ.get(bstack1ll_opy_ (u"ࠩࡅࡖࡔ࡝ࡓࡆࡔࡖࡘࡆࡉࡋࡠࡖࡈࡗ࡙ࡎࡕࡃࡡࡘ࡙ࡎࡊࠧ⅗")) == bstack1ll_opy_ (u"ࠥࡲࡺࡲ࡬ࠣ⅘"):
            logger.error(bstack1ll_opy_ (u"ࠫࡊࡾࡣࡦࡲࡷ࡭ࡴࡴࠠࡪࡰࠣࡷࡹࡵࡰࠡࡤࡸ࡭ࡱࡪࠠࡳࡧࡴࡹࡪࡹࡴࠡࡶࡲࠤ࡙࡫ࡳࡵࡊࡸࡦ࠿ࠦࡍࡪࡵࡶ࡭ࡳ࡭ࠠࡢࡷࡷ࡬ࡪࡴࡴࡪࡥࡤࡸ࡮ࡵ࡮ࠡࡶࡲ࡯ࡪࡴࠧ⅙"))
            return {
                bstack1ll_opy_ (u"ࠬࡹࡴࡢࡶࡸࡷࠬ⅚"): bstack1ll_opy_ (u"࠭ࡥࡳࡴࡲࡶࠬ⅛"),
                bstack1ll_opy_ (u"ࠧ࡮ࡧࡶࡷࡦ࡭ࡥࠨ⅜"): bstack1ll_opy_ (u"ࠨࡖࡲ࡯ࡪࡴ࠯ࡣࡷ࡬ࡰࡩࡏࡄࠡ࡫ࡶࠤࡺࡴࡤࡦࡨ࡬ࡲࡪࡪࠬࠡࡤࡸ࡭ࡱࡪࠠࡤࡴࡨࡥࡹ࡯࡯࡯ࠢࡰ࡭࡬࡮ࡴࠡࡪࡤࡺࡪࠦࡦࡢ࡫࡯ࡩࡩ࠭⅝")
            }
        try:
            cls.bstack1lllll111ll1_opy_.shutdown()
            data = {
                bstack1ll_opy_ (u"ࠩࡩ࡭ࡳ࡯ࡳࡩࡧࡧࡣࡦࡺࠧ⅞"): bstack1l11l1111_opy_()
            }
            if not bstack1lll1lll1l11_opy_ is None:
                data[bstack1ll_opy_ (u"ࠪࡪ࡮ࡴࡩࡴࡪࡨࡨࡤࡳࡥࡵࡣࡧࡥࡹࡧࠧ⅟")] = [{
                    bstack1ll_opy_ (u"ࠫࡷ࡫ࡡࡴࡱࡱࠫⅠ"): bstack1ll_opy_ (u"ࠬࡻࡳࡦࡴࡢ࡯࡮ࡲ࡬ࡦࡦࠪⅡ"),
                    bstack1ll_opy_ (u"࠭ࡳࡪࡩࡱࡥࡱ࠭Ⅲ"): bstack1lll1lll1l11_opy_
                }]
            config = {
                bstack1ll_opy_ (u"ࠧࡩࡧࡤࡨࡪࡸࡳࠨⅣ"): cls.default_headers()
            }
            bstack11l1lll1l1l_opy_ = bstack1ll_opy_ (u"ࠨࡣࡳ࡭࠴ࡼ࠱࠰ࡤࡸ࡭ࡱࡪࡳ࠰ࡽࢀ࠳ࡸࡺ࡯ࡱࠩⅤ").format(os.environ[bstack1ll_opy_ (u"ࠤࡅࡖࡔ࡝ࡓࡆࡔࡖࡘࡆࡉࡋࡠࡖࡈࡗ࡙ࡎࡕࡃࡡࡘ࡙ࡎࡊࠢⅥ")])
            bstack1lll1lll11l1_opy_ = cls.request_url(bstack11l1lll1l1l_opy_)
            response = bstack1l111111_opy_(bstack1ll_opy_ (u"ࠪࡔ࡚࡚ࠧⅦ"), bstack1lll1lll11l1_opy_, data, config)
            if not response.ok:
                raise Exception(bstack1ll_opy_ (u"ࠦࡘࡺ࡯ࡱࠢࡵࡩࡶࡻࡥࡴࡶࠣࡲࡴࡺࠠࡰ࡭ࠥⅧ"))
        except Exception as error:
            logger.error(bstack1ll_opy_ (u"ࠧࡋࡸࡤࡧࡳࡸ࡮ࡵ࡮ࠡ࡫ࡱࠤࡸࡺ࡯ࡱࠢࡥࡹ࡮ࡲࡤࠡࡴࡨࡵࡺ࡫ࡳࡵࠢࡷࡳ࡚ࠥࡥࡴࡶࡋࡹࡧࡀ࠺ࠡࠤⅨ") + str(error))
            return {
                bstack1ll_opy_ (u"࠭ࡳࡵࡣࡷࡹࡸ࠭Ⅹ"): bstack1ll_opy_ (u"ࠧࡦࡴࡵࡳࡷ࠭Ⅺ"),
                bstack1ll_opy_ (u"ࠨ࡯ࡨࡷࡸࡧࡧࡦࠩⅫ"): str(error)
            }
    @classmethod
    @error_handler(class_method=True)
    def bstack1lll1llll1l1_opy_(cls, response):
        bstack11lll1ll1l_opy_ = response.json() if not isinstance(response, dict) else response
        bstack1lll1lllll1l_opy_ = {}
        if bstack11lll1ll1l_opy_.get(bstack1ll_opy_ (u"ࠩ࡭ࡻࡹ࠭Ⅼ")) is None:
            os.environ[bstack1ll_opy_ (u"ࠪࡆࡗࡕࡗࡔࡇࡕࡗ࡙ࡇࡃࡌࡡࡗࡉࡘ࡚ࡈࡖࡄࡢࡎ࡜࡚ࠧⅭ")] = bstack1ll_opy_ (u"ࠫࡳࡻ࡬࡭ࠩⅮ")
        else:
            os.environ[bstack1ll_opy_ (u"ࠬࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣ࡙ࡋࡓࡕࡊࡘࡆࡤࡐࡗࡕࠩⅯ")] = bstack11lll1ll1l_opy_.get(bstack1ll_opy_ (u"࠭ࡪࡸࡶࠪⅰ"), bstack1ll_opy_ (u"ࠧ࡯ࡷ࡯ࡰࠬⅱ"))
        os.environ[bstack1ll_opy_ (u"ࠨࡄࡕࡓ࡜࡙ࡅࡓࡕࡗࡅࡈࡑ࡟ࡕࡇࡖࡘࡍ࡛ࡂࡠࡗࡘࡍࡉ࠭ⅲ")] = bstack11lll1ll1l_opy_.get(bstack1ll_opy_ (u"ࠩࡥࡹ࡮ࡲࡤࡠࡪࡤࡷ࡭࡫ࡤࡠ࡫ࡧࠫⅳ"), bstack1ll_opy_ (u"ࠪࡲࡺࡲ࡬ࠨⅴ"))
        logger.info(bstack1ll_opy_ (u"࡙ࠫ࡫ࡳࡵࡪࡸࡦࠥࡹࡴࡢࡴࡷࡩࡩࠦࡷࡪࡶ࡫ࠤ࡮ࡪ࠺ࠡࠩⅵ") + os.getenv(bstack1ll_opy_ (u"ࠬࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣ࡙ࡋࡓࡕࡊࡘࡆࡤ࡛ࡕࡊࡆࠪⅶ")));
        if bstack1l11111lll_opy_.bstack1lll1llllll1_opy_(cls.bs_config, cls.bstack1l1llll111_opy_.get(bstack1ll_opy_ (u"࠭ࡦࡳࡣࡰࡩࡼࡵࡲ࡬ࡡࡸࡷࡪࡪࠧⅷ"), bstack1ll_opy_ (u"ࠧࠨⅸ"))) is True:
            bstack1llll1lll11l_opy_, build_hashed_id, bstack1lll1lll1l1l_opy_ = cls.bstack1lll1lll111l_opy_(bstack11lll1ll1l_opy_)
            if bstack1llll1lll11l_opy_ != None and build_hashed_id != None:
                bstack1lll1lllll1l_opy_[bstack1ll_opy_ (u"ࠨࡱࡥࡷࡪࡸࡶࡢࡤ࡬ࡰ࡮ࡺࡹࠨⅹ")] = {
                    bstack1ll_opy_ (u"ࠩ࡭ࡻࡹࡥࡴࡰ࡭ࡨࡲࠬⅺ"): bstack1llll1lll11l_opy_,
                    bstack1ll_opy_ (u"ࠪࡦࡺ࡯࡬ࡥࡡ࡫ࡥࡸ࡮ࡥࡥࡡ࡬ࡨࠬⅻ"): build_hashed_id,
                    bstack1ll_opy_ (u"ࠫࡦࡲ࡬ࡰࡹࡢࡷࡨࡸࡥࡦࡰࡶ࡬ࡴࡺࡳࠨⅼ"): bstack1lll1lll1l1l_opy_
                }
            else:
                bstack1lll1lllll1l_opy_[bstack1ll_opy_ (u"ࠬࡵࡢࡴࡧࡵࡺࡦࡨࡩ࡭࡫ࡷࡽࠬⅽ")] = {}
        else:
            bstack1lll1lllll1l_opy_[bstack1ll_opy_ (u"࠭࡯ࡣࡵࡨࡶࡻࡧࡢࡪ࡮࡬ࡸࡾ࠭ⅾ")] = {}
        bstack1lll1lll1lll_opy_, build_hashed_id = cls.bstack1lll1lll11ll_opy_(bstack11lll1ll1l_opy_)
        if bstack1lll1lll1lll_opy_ != None and build_hashed_id != None:
            bstack1lll1lllll1l_opy_[bstack1ll_opy_ (u"ࠧࡢࡥࡦࡩࡸࡹࡩࡣ࡫࡯࡭ࡹࡿࠧⅿ")] = {
                bstack1ll_opy_ (u"ࠨࡣࡸࡸ࡭ࡥࡴࡰ࡭ࡨࡲࠬↀ"): bstack1lll1lll1lll_opy_,
                bstack1ll_opy_ (u"ࠩࡥࡹ࡮ࡲࡤࡠࡪࡤࡷ࡭࡫ࡤࡠ࡫ࡧࠫↁ"): build_hashed_id,
            }
        else:
            bstack1lll1lllll1l_opy_[bstack1ll_opy_ (u"ࠪࡥࡨࡩࡥࡴࡵ࡬ࡦ࡮ࡲࡩࡵࡻࠪↂ")] = {}
        if bstack1lll1lllll1l_opy_[bstack1ll_opy_ (u"ࠫࡴࡨࡳࡦࡴࡹࡥࡧ࡯࡬ࡪࡶࡼࠫↃ")].get(bstack1ll_opy_ (u"ࠬࡨࡵࡪ࡮ࡧࡣ࡭ࡧࡳࡩࡧࡧࡣ࡮ࡪࠧↄ")) != None or bstack1lll1lllll1l_opy_[bstack1ll_opy_ (u"࠭ࡡࡤࡥࡨࡷࡸ࡯ࡢࡪ࡮࡬ࡸࡾ࠭ↅ")].get(bstack1ll_opy_ (u"ࠧࡣࡷ࡬ࡰࡩࡥࡨࡢࡵ࡫ࡩࡩࡥࡩࡥࠩↆ")) != None:
            cls.bstack1llll1111111_opy_(bstack11lll1ll1l_opy_.get(bstack1ll_opy_ (u"ࠨ࡬ࡺࡸࠬↇ")), bstack11lll1ll1l_opy_.get(bstack1ll_opy_ (u"ࠩࡥࡹ࡮ࡲࡤࡠࡪࡤࡷ࡭࡫ࡤࡠ࡫ࡧࠫↈ")))
        return bstack1lll1lllll1l_opy_
    @classmethod
    def bstack1lll1lll111l_opy_(cls, bstack11lll1ll1l_opy_):
        if bstack11lll1ll1l_opy_.get(bstack1ll_opy_ (u"ࠪࡳࡧࡹࡥࡳࡸࡤࡦ࡮ࡲࡩࡵࡻࠪ↉")) == None:
            cls.bstack1llll1111lll_opy_()
            return [None, None, None]
        if bstack11lll1ll1l_opy_[bstack1ll_opy_ (u"ࠫࡴࡨࡳࡦࡴࡹࡥࡧ࡯࡬ࡪࡶࡼࠫ↊")][bstack1ll_opy_ (u"ࠬࡹࡵࡤࡥࡨࡷࡸ࠭↋")] != True:
            cls.bstack1llll1111lll_opy_(bstack11lll1ll1l_opy_[bstack1ll_opy_ (u"࠭࡯ࡣࡵࡨࡶࡻࡧࡢࡪ࡮࡬ࡸࡾ࠭↌")])
            return [None, None, None]
        logger.debug(bstack1ll_opy_ (u"ࠧࡼࡿࠣࡆࡺ࡯࡬ࡥࠢࡦࡶࡪࡧࡴࡪࡱࡱࠤࡘࡻࡣࡤࡧࡶࡷ࡫ࡻ࡬ࠢࠩ↍").format(bstack11llllll11_opy_))
        os.environ[bstack1ll_opy_ (u"ࠨࡄࡖࡣ࡙ࡋࡓࡕࡑࡓࡗࡤࡈࡕࡊࡎࡇࡣࡈࡕࡍࡑࡎࡈࡘࡊࡊࠧ↎")] = bstack1ll_opy_ (u"ࠩࡷࡶࡺ࡫ࠧ↏")
        if bstack11lll1ll1l_opy_.get(bstack1ll_opy_ (u"ࠪ࡮ࡼࡺࠧ←")):
            os.environ[bstack1ll_opy_ (u"ࠫࡈࡘࡅࡅࡇࡑࡘࡎࡇࡌࡔࡡࡉࡓࡗࡥࡃࡓࡃࡖࡌࡤࡘࡅࡑࡑࡕࡘࡎࡔࡇࠨ↑")] = json.dumps({
                bstack1ll_opy_ (u"ࠬࡻࡳࡦࡴࡱࡥࡲ࡫ࠧ→"): bstack11ll11llll1_opy_(cls.bs_config),
                bstack1ll_opy_ (u"࠭ࡰࡢࡵࡶࡻࡴࡸࡤࠨ↓"): bstack11ll11ll1ll_opy_(cls.bs_config)
            })
        if bstack11lll1ll1l_opy_.get(bstack1ll_opy_ (u"ࠧࡣࡷ࡬ࡰࡩࡥࡨࡢࡵ࡫ࡩࡩࡥࡩࡥࠩ↔")):
            os.environ[bstack1ll_opy_ (u"ࠨࡄࡖࡣ࡙ࡋࡓࡕࡑࡓࡗࡤࡈࡕࡊࡎࡇࡣࡍࡇࡓࡉࡇࡇࡣࡎࡊࠧ↕")] = bstack11lll1ll1l_opy_[bstack1ll_opy_ (u"ࠩࡥࡹ࡮ࡲࡤࡠࡪࡤࡷ࡭࡫ࡤࡠ࡫ࡧࠫ↖")]
        if bstack11lll1ll1l_opy_[bstack1ll_opy_ (u"ࠪࡳࡧࡹࡥࡳࡸࡤࡦ࡮ࡲࡩࡵࡻࠪ↗")].get(bstack1ll_opy_ (u"ࠫࡴࡶࡴࡪࡱࡱࡷࠬ↘"), {}).get(bstack1ll_opy_ (u"ࠬࡧ࡬࡭ࡱࡺࡣࡸࡩࡲࡦࡧࡱࡷ࡭ࡵࡴࡴࠩ↙")):
            os.environ[bstack1ll_opy_ (u"࠭ࡂࡔࡡࡗࡉࡘ࡚ࡏࡑࡕࡢࡅࡑࡒࡏࡘࡡࡖࡇࡗࡋࡅࡏࡕࡋࡓ࡙࡙ࠧ↚")] = str(bstack11lll1ll1l_opy_[bstack1ll_opy_ (u"ࠧࡰࡤࡶࡩࡷࡼࡡࡣ࡫࡯࡭ࡹࡿࠧ↛")][bstack1ll_opy_ (u"ࠨࡱࡳࡸ࡮ࡵ࡮ࡴࠩ↜")][bstack1ll_opy_ (u"ࠩࡤࡰࡱࡵࡷࡠࡵࡦࡶࡪ࡫࡮ࡴࡪࡲࡸࡸ࠭↝")])
        else:
            os.environ[bstack1ll_opy_ (u"ࠪࡆࡘࡥࡔࡆࡕࡗࡓࡕ࡙࡟ࡂࡎࡏࡓ࡜ࡥࡓࡄࡔࡈࡉࡓ࡙ࡈࡐࡖࡖࠫ↞")] = bstack1ll_opy_ (u"ࠦࡳࡻ࡬࡭ࠤ↟")
        return [bstack11lll1ll1l_opy_[bstack1ll_opy_ (u"ࠬࡰࡷࡵࠩ↠")], bstack11lll1ll1l_opy_[bstack1ll_opy_ (u"࠭ࡢࡶ࡫࡯ࡨࡤ࡮ࡡࡴࡪࡨࡨࡤ࡯ࡤࠨ↡")], os.environ[bstack1ll_opy_ (u"ࠧࡃࡕࡢࡘࡊ࡙ࡔࡐࡒࡖࡣࡆࡒࡌࡐ࡙ࡢࡗࡈࡘࡅࡆࡐࡖࡌࡔ࡚ࡓࠨ↢")]]
    @classmethod
    def bstack1lll1lll11ll_opy_(cls, bstack11lll1ll1l_opy_):
        if bstack11lll1ll1l_opy_.get(bstack1ll_opy_ (u"ࠨࡣࡦࡧࡪࡹࡳࡪࡤ࡬ࡰ࡮ࡺࡹࠨ↣")) == None:
            cls.bstack1lll1lll1111_opy_()
            return [None, None]
        if bstack11lll1ll1l_opy_[bstack1ll_opy_ (u"ࠩࡤࡧࡨ࡫ࡳࡴ࡫ࡥ࡭ࡱ࡯ࡴࡺࠩ↤")][bstack1ll_opy_ (u"ࠪࡷࡺࡩࡣࡦࡵࡶࠫ↥")] != True:
            cls.bstack1lll1lll1111_opy_(bstack11lll1ll1l_opy_[bstack1ll_opy_ (u"ࠫࡦࡩࡣࡦࡵࡶ࡭ࡧ࡯࡬ࡪࡶࡼࠫ↦")])
            return [None, None]
        if bstack11lll1ll1l_opy_[bstack1ll_opy_ (u"ࠬࡧࡣࡤࡧࡶࡷ࡮ࡨࡩ࡭࡫ࡷࡽࠬ↧")].get(bstack1ll_opy_ (u"࠭࡯ࡱࡶ࡬ࡳࡳࡹࠧ↨")):
            logger.debug(bstack1ll_opy_ (u"ࠧࡕࡧࡶࡸࠥࡇࡣࡤࡧࡶࡷ࡮ࡨࡩ࡭࡫ࡷࡽࠥࡈࡵࡪ࡮ࡧࠤࡨࡸࡥࡢࡶ࡬ࡳࡳࠦࡓࡶࡥࡦࡩࡸࡹࡦࡶ࡮ࠤࠫ↩"))
            parsed = json.loads(os.getenv(bstack1ll_opy_ (u"ࠨࡄࡕࡓ࡜࡙ࡅࡓࡕࡗࡅࡈࡑ࡟ࡕࡇࡖࡘࡤࡇࡃࡄࡇࡖࡗࡎࡈࡉࡍࡋࡗ࡝ࡤࡉࡏࡏࡈࡌࡋ࡚ࡘࡁࡕࡋࡒࡒࡤ࡟ࡍࡍࠩ↪"), bstack1ll_opy_ (u"ࠩࡾࢁࠬ↫")))
            capabilities = bstack1ll1l1l1l_opy_.bstack1llll11111ll_opy_(bstack11lll1ll1l_opy_[bstack1ll_opy_ (u"ࠪࡥࡨࡩࡥࡴࡵ࡬ࡦ࡮ࡲࡩࡵࡻࠪ↬")][bstack1ll_opy_ (u"ࠫࡴࡶࡴࡪࡱࡱࡷࠬ↭")][bstack1ll_opy_ (u"ࠬࡩࡡࡱࡣࡥ࡭ࡱ࡯ࡴࡪࡧࡶࠫ↮")], bstack1ll_opy_ (u"࠭࡮ࡢ࡯ࡨࠫ↯"), bstack1ll_opy_ (u"ࠧࡷࡣ࡯ࡹࡪ࠭↰"))
            bstack1lll1lll1lll_opy_ = capabilities[bstack1ll_opy_ (u"ࠨࡣࡦࡧࡪࡹࡳࡪࡤ࡬ࡰ࡮ࡺࡹࡕࡱ࡮ࡩࡳ࠭↱")]
            os.environ[bstack1ll_opy_ (u"ࠩࡅࡗࡤࡇ࠱࠲࡛ࡢࡎ࡜࡚ࠧ↲")] = bstack1lll1lll1lll_opy_
            if bstack1ll_opy_ (u"ࠥࡥࡺࡺ࡯࡮ࡣࡷࡩࠧ↳") in bstack11lll1ll1l_opy_ and bstack11lll1ll1l_opy_.get(bstack1ll_opy_ (u"ࠦࡦࡶࡰࡠࡣࡸࡸࡴࡳࡡࡵࡧࠥ↴")) is None:
                parsed[bstack1ll_opy_ (u"ࠬࡹࡣࡢࡰࡱࡩࡷ࡜ࡥࡳࡵ࡬ࡳࡳ࠭↵")] = capabilities[bstack1ll_opy_ (u"࠭ࡳࡤࡣࡱࡲࡪࡸࡖࡦࡴࡶ࡭ࡴࡴࠧ↶")]
            os.environ[bstack1ll_opy_ (u"ࠧࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡔࡆࡕࡗࡣࡆࡉࡃࡆࡕࡖࡍࡇࡏࡌࡊࡖ࡜ࡣࡈࡕࡎࡇࡋࡊ࡙ࡗࡇࡔࡊࡑࡑࡣ࡞ࡓࡌࠨ↷")] = json.dumps(parsed)
            scripts = bstack1ll1l1l1l_opy_.bstack1llll11111ll_opy_(bstack11lll1ll1l_opy_[bstack1ll_opy_ (u"ࠨࡣࡦࡧࡪࡹࡳࡪࡤ࡬ࡰ࡮ࡺࡹࠨ↸")][bstack1ll_opy_ (u"ࠩࡲࡴࡹ࡯࡯࡯ࡵࠪ↹")][bstack1ll_opy_ (u"ࠪࡷࡨࡸࡩࡱࡶࡶࠫ↺")], bstack1ll_opy_ (u"ࠫࡳࡧ࡭ࡦࠩ↻"), bstack1ll_opy_ (u"ࠬࡩ࡯࡮࡯ࡤࡲࡩ࠭↼"))
            bstack1111l1ll1_opy_.bstack1l111lll_opy_(scripts)
            commands = bstack11lll1ll1l_opy_[bstack1ll_opy_ (u"࠭ࡡࡤࡥࡨࡷࡸ࡯ࡢࡪ࡮࡬ࡸࡾ࠭↽")][bstack1ll_opy_ (u"ࠧࡰࡲࡷ࡭ࡴࡴࡳࠨ↾")][bstack1ll_opy_ (u"ࠨࡥࡲࡱࡲࡧ࡮ࡥࡵࡗࡳ࡜ࡸࡡࡱࠩ↿")].get(bstack1ll_opy_ (u"ࠩࡦࡳࡲࡳࡡ࡯ࡦࡶࠫ⇀"))
            bstack1111l1ll1_opy_.bstack11ll1l11111_opy_(commands)
            bstack11ll111l111_opy_ = capabilities.get(bstack1ll_opy_ (u"ࠪ࡫ࡴࡵࡧ࠻ࡥ࡫ࡶࡴࡳࡥࡐࡲࡷ࡭ࡴࡴࡳࠨ⇁"))
            bstack1111l1ll1_opy_.bstack11l1lll1ll1_opy_(bstack11ll111l111_opy_)
            bstack1111l1ll1_opy_.store()
        return [bstack1lll1lll1lll_opy_, bstack11lll1ll1l_opy_[bstack1ll_opy_ (u"ࠫࡧࡻࡩ࡭ࡦࡢ࡬ࡦࡹࡨࡦࡦࡢ࡭ࡩ࠭⇂")]]
    @classmethod
    def bstack1llll1111lll_opy_(cls, response=None):
        os.environ[bstack1ll_opy_ (u"ࠬࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣ࡙ࡋࡓࡕࡊࡘࡆࡤ࡛ࡕࡊࡆࠪ⇃")] = bstack1ll_opy_ (u"࠭࡮ࡶ࡮࡯ࠫ⇄")
        os.environ[bstack1ll_opy_ (u"ࠧࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡔࡆࡕࡗࡌ࡚ࡈ࡟ࡋ࡙ࡗࠫ⇅")] = bstack1ll_opy_ (u"ࠨࡰࡸࡰࡱ࠭⇆")
        os.environ[bstack1ll_opy_ (u"ࠩࡅࡗࡤ࡚ࡅࡔࡖࡒࡔࡘࡥࡂࡖࡋࡏࡈࡤࡉࡏࡎࡒࡏࡉ࡙ࡋࡄࠨ⇇")] = bstack1ll_opy_ (u"ࠪࡪࡦࡲࡳࡦࠩ⇈")
        os.environ[bstack1ll_opy_ (u"ࠫࡇ࡙࡟ࡕࡇࡖࡘࡔࡖࡓࡠࡄࡘࡍࡑࡊ࡟ࡉࡃࡖࡌࡊࡊ࡟ࡊࡆࠪ⇉")] = bstack1ll_opy_ (u"ࠧࡴࡵ࡭࡮ࠥ⇊")
        os.environ[bstack1ll_opy_ (u"࠭ࡂࡔࡡࡗࡉࡘ࡚ࡏࡑࡕࡢࡅࡑࡒࡏࡘࡡࡖࡇࡗࡋࡅࡏࡕࡋࡓ࡙࡙ࠧ⇋")] = bstack1ll_opy_ (u"ࠢ࡯ࡷ࡯ࡰࠧ⇌")
        cls.bstack1llll111l111_opy_(response, bstack1ll_opy_ (u"ࠣࡱࡥࡷࡪࡸࡶࡢࡤ࡬ࡰ࡮ࡺࡹࠣ⇍"))
        return [None, None, None]
    @classmethod
    def bstack1lll1lll1111_opy_(cls, response=None):
        os.environ[bstack1ll_opy_ (u"ࠩࡅࡖࡔ࡝ࡓࡆࡔࡖࡘࡆࡉࡋࡠࡖࡈࡗ࡙ࡎࡕࡃࡡࡘ࡙ࡎࡊࠧ⇎")] = bstack1ll_opy_ (u"ࠪࡲࡺࡲ࡬ࠨ⇏")
        os.environ[bstack1ll_opy_ (u"ࠫࡇ࡙࡟ࡂ࠳࠴࡝ࡤࡐࡗࡕࠩ⇐")] = bstack1ll_opy_ (u"ࠬࡴࡵ࡭࡮ࠪ⇑")
        os.environ[bstack1ll_opy_ (u"࠭ࡂࡓࡑ࡚ࡗࡊࡘࡓࡕࡃࡆࡏࡤ࡚ࡅࡔࡖࡋ࡙ࡇࡥࡊࡘࡖࠪ⇒")] = bstack1ll_opy_ (u"ࠧ࡯ࡷ࡯ࡰࠬ⇓")
        cls.bstack1llll111l111_opy_(response, bstack1ll_opy_ (u"ࠣࡣࡦࡧࡪࡹࡳࡪࡤ࡬ࡰ࡮ࡺࡹࠣ⇔"))
        return [None, None, None]
    @classmethod
    def bstack1llll1111111_opy_(cls, jwt, build_hashed_id):
        os.environ[bstack1ll_opy_ (u"ࠩࡅࡖࡔ࡝ࡓࡆࡔࡖࡘࡆࡉࡋࡠࡖࡈࡗ࡙ࡎࡕࡃࡡࡍ࡛࡙࠭⇕")] = jwt
        os.environ[bstack1ll_opy_ (u"ࠪࡆࡗࡕࡗࡔࡇࡕࡗ࡙ࡇࡃࡌࡡࡗࡉࡘ࡚ࡈࡖࡄࡢ࡙࡚ࡏࡄࠨ⇖")] = build_hashed_id
    @classmethod
    def bstack1llll111l111_opy_(cls, response=None, product=bstack1ll_opy_ (u"ࠦࠧ⇗")):
        if response == None or response.get(bstack1ll_opy_ (u"ࠬ࡫ࡲࡳࡱࡵࡷࠬ⇘")) == None:
            logger.error(product + bstack1ll_opy_ (u"ࠨࠠࡃࡷ࡬ࡰࡩࠦࡣࡳࡧࡤࡸ࡮ࡵ࡮ࠡࡨࡤ࡭ࡱ࡫ࡤࠣ⇙"))
            return
        for error in response[bstack1ll_opy_ (u"ࠧࡦࡴࡵࡳࡷࡹࠧ⇚")]:
            bstack111lllll1l1_opy_ = error[bstack1ll_opy_ (u"ࠨ࡭ࡨࡽࠬ⇛")]
            error_message = error[bstack1ll_opy_ (u"ࠩࡰࡩࡸࡹࡡࡨࡧࠪ⇜")]
            if error_message:
                if bstack111lllll1l1_opy_ == bstack1ll_opy_ (u"ࠥࡉࡗࡘࡏࡓࡡࡄࡇࡈࡋࡓࡔࡡࡇࡉࡓࡏࡅࡅࠤ⇝"):
                    logger.info(error_message)
                else:
                    logger.error(error_message)
            else:
                logger.error(bstack1ll_opy_ (u"ࠦࡉࡧࡴࡢࠢࡸࡴࡱࡵࡡࡥࠢࡷࡳࠥࡈࡲࡰࡹࡶࡩࡷ࡙ࡴࡢࡥ࡮ࠤࠧ⇞") + product + bstack1ll_opy_ (u"ࠧࠦࡦࡢ࡫࡯ࡩࡩࠦࡤࡶࡧࠣࡸࡴࠦࡳࡰ࡯ࡨࠤࡪࡸࡲࡰࡴࠥ⇟"))
    @classmethod
    def bstack1llll1111ll1_opy_(cls):
        if cls.bstack1lllll111ll1_opy_ is not None:
            return
        cls.bstack1lllll111ll1_opy_ = bstack1llll1llll1l_opy_(cls.bstack1lll1lll1ll1_opy_)
        cls.bstack1lllll111ll1_opy_.start()
    @classmethod
    def bstack1111lll111_opy_(cls):
        if cls.bstack1lllll111ll1_opy_ is None:
            return
        cls.bstack1lllll111ll1_opy_.shutdown()
    @classmethod
    @error_handler(class_method=True)
    def bstack1lll1lll1ll1_opy_(cls, bstack1111l1l11l_opy_, event_url=bstack1ll_opy_ (u"࠭ࡡࡱ࡫࠲ࡺ࠶࠵ࡢࡢࡶࡦ࡬ࠬ⇠")):
        config = {
            bstack1ll_opy_ (u"ࠧࡩࡧࡤࡨࡪࡸࡳࠨ⇡"): cls.default_headers()
        }
        logger.debug(bstack1ll_opy_ (u"ࠣࡲࡲࡷࡹࡥࡤࡢࡶࡤ࠾࡙ࠥࡥ࡯ࡦ࡬ࡲ࡬ࠦࡤࡢࡶࡤࠤࡹࡵࠠࡵࡧࡶࡸ࡭ࡻࡢࠡࡨࡲࡶࠥ࡫ࡶࡦࡰࡷࡷࠥࢁࡽࠣ⇢").format(bstack1ll_opy_ (u"ࠩ࠯ࠤࠬ⇣").join([event[bstack1ll_opy_ (u"ࠪࡩࡻ࡫࡮ࡵࡡࡷࡽࡵ࡫ࠧ⇤")] for event in bstack1111l1l11l_opy_])))
        response = bstack1l111111_opy_(bstack1ll_opy_ (u"ࠫࡕࡕࡓࡕࠩ⇥"), cls.request_url(event_url), bstack1111l1l11l_opy_, config)
        bstack11l1lllllll_opy_ = response.json()
    @classmethod
    def bstack1ll1ll111l_opy_(cls, bstack1111l1l11l_opy_, event_url=bstack1ll_opy_ (u"ࠬࡧࡰࡪ࠱ࡹ࠵࠴ࡨࡡࡵࡥ࡫ࠫ⇦")):
        logger.debug(bstack1ll_opy_ (u"ࠨࡳࡦࡰࡧࡣࡩࡧࡴࡢ࠼ࠣࡅࡹࡺࡥ࡮ࡲࡷ࡭ࡳ࡭ࠠࡵࡱࠣࡥࡩࡪࠠࡥࡣࡷࡥࠥࡺ࡯ࠡࡤࡤࡸࡨ࡮ࠠࡸ࡫ࡷ࡬ࠥ࡫ࡶࡦࡰࡷࡣࡹࡿࡰࡦ࠼ࠣࡿࢂࠨ⇧").format(bstack1111l1l11l_opy_[bstack1ll_opy_ (u"ࠧࡦࡸࡨࡲࡹࡥࡴࡺࡲࡨࠫ⇨")]))
        if not bstack1ll1l1l1l_opy_.bstack1lll1llll11l_opy_(bstack1111l1l11l_opy_[bstack1ll_opy_ (u"ࠨࡧࡹࡩࡳࡺ࡟ࡵࡻࡳࡩࠬ⇩")]):
            logger.debug(bstack1ll_opy_ (u"ࠤࡶࡩࡳࡪ࡟ࡥࡣࡷࡥ࠿ࠦࡎࡰࡶࠣࡥࡩࡪࡩ࡯ࡩࠣࡨࡦࡺࡡࠡࡹ࡬ࡸ࡭ࠦࡥࡷࡧࡱࡸࡤࡺࡹࡱࡧ࠽ࠤࢀࢃࠢ⇪").format(bstack1111l1l11l_opy_[bstack1ll_opy_ (u"ࠪࡩࡻ࡫࡮ࡵࡡࡷࡽࡵ࡫ࠧ⇫")]))
            return
        bstack11l1l111ll_opy_ = bstack1ll1l1l1l_opy_.bstack1llll1111l1l_opy_(bstack1111l1l11l_opy_[bstack1ll_opy_ (u"ࠫࡪࡼࡥ࡯ࡶࡢࡸࡾࡶࡥࠨ⇬")], bstack1111l1l11l_opy_.get(bstack1ll_opy_ (u"ࠬࡺࡥࡴࡶࡢࡶࡺࡴࠧ⇭")))
        if bstack11l1l111ll_opy_ != None:
            if bstack1111l1l11l_opy_.get(bstack1ll_opy_ (u"࠭ࡴࡦࡵࡷࡣࡷࡻ࡮ࠨ⇮")) != None:
                bstack1111l1l11l_opy_[bstack1ll_opy_ (u"ࠧࡵࡧࡶࡸࡤࡸࡵ࡯ࠩ⇯")][bstack1ll_opy_ (u"ࠨࡲࡵࡳࡩࡻࡣࡵࡡࡰࡥࡵ࠭⇰")] = bstack11l1l111ll_opy_
            else:
                bstack1111l1l11l_opy_[bstack1ll_opy_ (u"ࠩࡳࡶࡴࡪࡵࡤࡶࡢࡱࡦࡶࠧ⇱")] = bstack11l1l111ll_opy_
        if event_url == bstack1ll_opy_ (u"ࠪࡥࡵ࡯࠯ࡷ࠳࠲ࡦࡦࡺࡣࡩࠩ⇲"):
            cls.bstack1llll1111ll1_opy_()
            logger.debug(bstack1ll_opy_ (u"ࠦࡸ࡫࡮ࡥࡡࡧࡥࡹࡧ࠺ࠡࡃࡧࡨ࡮ࡴࡧࠡࡦࡤࡸࡦࠦࡴࡰࠢࡥࡥࡹࡩࡨࠡࡹ࡬ࡸ࡭ࠦࡥࡷࡧࡱࡸࡤࡺࡹࡱࡧ࠽ࠤࢀࢃࠢ⇳").format(bstack1111l1l11l_opy_[bstack1ll_opy_ (u"ࠬ࡫ࡶࡦࡰࡷࡣࡹࡿࡰࡦࠩ⇴")]))
            cls.bstack1lllll111ll1_opy_.add(bstack1111l1l11l_opy_)
        elif event_url == bstack1ll_opy_ (u"࠭ࡡࡱ࡫࠲ࡺ࠶࠵ࡳࡤࡴࡨࡩࡳࡹࡨࡰࡶࡶࠫ⇵"):
            cls.bstack1lll1lll1ll1_opy_([bstack1111l1l11l_opy_], event_url)
    @classmethod
    @error_handler(class_method=True)
    def bstack11ll1111l_opy_(cls, logs):
        for log in logs:
            bstack1llll11111l1_opy_ = {
                bstack1ll_opy_ (u"ࠧ࡬࡫ࡱࡨࠬ⇶"): bstack1ll_opy_ (u"ࠨࡖࡈࡗ࡙ࡥࡌࡐࡉࠪ⇷"),
                bstack1ll_opy_ (u"ࠩ࡯ࡩࡻ࡫࡬ࠨ⇸"): log[bstack1ll_opy_ (u"ࠪࡰࡪࡼࡥ࡭ࠩ⇹")],
                bstack1ll_opy_ (u"ࠫࡹ࡯࡭ࡦࡵࡷࡥࡲࡶࠧ⇺"): log[bstack1ll_opy_ (u"ࠬࡺࡩ࡮ࡧࡶࡸࡦࡳࡰࠨ⇻")],
                bstack1ll_opy_ (u"࠭ࡨࡵࡶࡳࡣࡷ࡫ࡳࡱࡱࡱࡷࡪ࠭⇼"): {},
                bstack1ll_opy_ (u"ࠧ࡮ࡧࡶࡷࡦ࡭ࡥࠨ⇽"): log[bstack1ll_opy_ (u"ࠨ࡯ࡨࡷࡸࡧࡧࡦࠩ⇾")],
            }
            if bstack1ll_opy_ (u"ࠩࡷࡩࡸࡺ࡟ࡳࡷࡱࡣࡺࡻࡩࡥࠩ⇿") in log:
                bstack1llll11111l1_opy_[bstack1ll_opy_ (u"ࠪࡸࡪࡹࡴࡠࡴࡸࡲࡤࡻࡵࡪࡦࠪ∀")] = log[bstack1ll_opy_ (u"ࠫࡹ࡫ࡳࡵࡡࡵࡹࡳࡥࡵࡶ࡫ࡧࠫ∁")]
            elif bstack1ll_opy_ (u"ࠬ࡮࡯ࡰ࡭ࡢࡶࡺࡴ࡟ࡶࡷ࡬ࡨࠬ∂") in log:
                bstack1llll11111l1_opy_[bstack1ll_opy_ (u"࠭ࡨࡰࡱ࡮ࡣࡷࡻ࡮ࡠࡷࡸ࡭ࡩ࠭∃")] = log[bstack1ll_opy_ (u"ࠧࡩࡱࡲ࡯ࡤࡸࡵ࡯ࡡࡸࡹ࡮ࡪࠧ∄")]
            cls.bstack1ll1ll111l_opy_({
                bstack1ll_opy_ (u"ࠨࡧࡹࡩࡳࡺ࡟ࡵࡻࡳࡩࠬ∅"): bstack1ll_opy_ (u"ࠩࡏࡳ࡬ࡉࡲࡦࡣࡷࡩࡩ࠭∆"),
                bstack1ll_opy_ (u"ࠪࡰࡴ࡭ࡳࠨ∇"): [bstack1llll11111l1_opy_]
            })
    @classmethod
    @error_handler(class_method=True)
    def bstack1lll1lllll11_opy_(cls, steps):
        bstack1llll111111l_opy_ = []
        for step in steps:
            bstack1lll1llll111_opy_ = {
                bstack1ll_opy_ (u"ࠫࡰ࡯࡮ࡥࠩ∈"): bstack1ll_opy_ (u"࡚ࠬࡅࡔࡖࡢࡗ࡙ࡋࡐࠨ∉"),
                bstack1ll_opy_ (u"࠭࡬ࡦࡸࡨࡰࠬ∊"): step[bstack1ll_opy_ (u"ࠧ࡭ࡧࡹࡩࡱ࠭∋")],
                bstack1ll_opy_ (u"ࠨࡶ࡬ࡱࡪࡹࡴࡢ࡯ࡳࠫ∌"): step[bstack1ll_opy_ (u"ࠩࡷ࡭ࡲ࡫ࡳࡵࡣࡰࡴࠬ∍")],
                bstack1ll_opy_ (u"ࠪࡱࡪࡹࡳࡢࡩࡨࠫ∎"): step[bstack1ll_opy_ (u"ࠫࡲ࡫ࡳࡴࡣࡪࡩࠬ∏")],
                bstack1ll_opy_ (u"ࠬࡪࡵࡳࡣࡷ࡭ࡴࡴࠧ∐"): step[bstack1ll_opy_ (u"࠭ࡤࡶࡴࡤࡸ࡮ࡵ࡮ࠨ∑")]
            }
            if bstack1ll_opy_ (u"ࠧࡵࡧࡶࡸࡤࡸࡵ࡯ࡡࡸࡹ࡮ࡪࠧ−") in step:
                bstack1lll1llll111_opy_[bstack1ll_opy_ (u"ࠨࡶࡨࡷࡹࡥࡲࡶࡰࡢࡹࡺ࡯ࡤࠨ∓")] = step[bstack1ll_opy_ (u"ࠩࡷࡩࡸࡺ࡟ࡳࡷࡱࡣࡺࡻࡩࡥࠩ∔")]
            elif bstack1ll_opy_ (u"ࠪ࡬ࡴࡵ࡫ࡠࡴࡸࡲࡤࡻࡵࡪࡦࠪ∕") in step:
                bstack1lll1llll111_opy_[bstack1ll_opy_ (u"ࠫ࡭ࡵ࡯࡬ࡡࡵࡹࡳࡥࡵࡶ࡫ࡧࠫ∖")] = step[bstack1ll_opy_ (u"ࠬ࡮࡯ࡰ࡭ࡢࡶࡺࡴ࡟ࡶࡷ࡬ࡨࠬ∗")]
            bstack1llll111111l_opy_.append(bstack1lll1llll111_opy_)
        cls.bstack1ll1ll111l_opy_({
            bstack1ll_opy_ (u"࠭ࡥࡷࡧࡱࡸࡤࡺࡹࡱࡧࠪ∘"): bstack1ll_opy_ (u"ࠧࡍࡱࡪࡇࡷ࡫ࡡࡵࡧࡧࠫ∙"),
            bstack1ll_opy_ (u"ࠨ࡮ࡲ࡫ࡸ࠭√"): bstack1llll111111l_opy_
        })
    @classmethod
    @error_handler(class_method=True)
    @measure(event_name=EVENTS.bstack1l1l1ll1_opy_, stage=STAGE.bstack1l1lll1ll1_opy_)
    def bstack1l1l1ll111_opy_(cls, screenshot):
        cls.bstack1ll1ll111l_opy_({
            bstack1ll_opy_ (u"ࠩࡨࡺࡪࡴࡴࡠࡶࡼࡴࡪ࠭∛"): bstack1ll_opy_ (u"ࠪࡐࡴ࡭ࡃࡳࡧࡤࡸࡪࡪࠧ∜"),
            bstack1ll_opy_ (u"ࠫࡱࡵࡧࡴࠩ∝"): [{
                bstack1ll_opy_ (u"ࠬࡱࡩ࡯ࡦࠪ∞"): bstack1ll_opy_ (u"࠭ࡔࡆࡕࡗࡣࡘࡉࡒࡆࡇࡑࡗࡍࡕࡔࠨ∟"),
                bstack1ll_opy_ (u"ࠧࡵ࡫ࡰࡩࡸࡺࡡ࡮ࡲࠪ∠"): datetime.datetime.utcnow().isoformat() + bstack1ll_opy_ (u"ࠨ࡜ࠪ∡"),
                bstack1ll_opy_ (u"ࠩࡰࡩࡸࡹࡡࡨࡧࠪ∢"): screenshot[bstack1ll_opy_ (u"ࠪ࡭ࡲࡧࡧࡦࠩ∣")],
                bstack1ll_opy_ (u"ࠫࡹ࡫ࡳࡵࡡࡵࡹࡳࡥࡵࡶ࡫ࡧࠫ∤"): screenshot[bstack1ll_opy_ (u"ࠬࡺࡥࡴࡶࡢࡶࡺࡴ࡟ࡶࡷ࡬ࡨࠬ∥")]
            }]
        }, event_url=bstack1ll_opy_ (u"࠭ࡡࡱ࡫࠲ࡺ࠶࠵ࡳࡤࡴࡨࡩࡳࡹࡨࡰࡶࡶࠫ∦"))
    @classmethod
    @error_handler(class_method=True)
    def bstack11ll1l1ll1_opy_(cls, driver):
        current_test_uuid = cls.current_test_uuid()
        if not current_test_uuid:
            return
        cls.bstack1ll1ll111l_opy_({
            bstack1ll_opy_ (u"ࠧࡦࡸࡨࡲࡹࡥࡴࡺࡲࡨࠫ∧"): bstack1ll_opy_ (u"ࠨࡅࡅࡘࡘ࡫ࡳࡴ࡫ࡲࡲࡈࡸࡥࡢࡶࡨࡨࠬ∨"),
            bstack1ll_opy_ (u"ࠩࡷࡩࡸࡺ࡟ࡳࡷࡱࠫ∩"): {
                bstack1ll_opy_ (u"ࠥࡹࡺ࡯ࡤࠣ∪"): cls.current_test_uuid(),
                bstack1ll_opy_ (u"ࠦ࡮ࡴࡴࡦࡩࡵࡥࡹ࡯࡯࡯ࡵࠥ∫"): cls.bstack111ll1111l_opy_(driver)
            }
        })
    @classmethod
    def bstack111ll11ll1_opy_(cls, event: str, bstack1111l1l11l_opy_: bstack111l1111ll_opy_):
        bstack1111ll1111_opy_ = {
            bstack1ll_opy_ (u"ࠬ࡫ࡶࡦࡰࡷࡣࡹࡿࡰࡦࠩ∬"): event,
            bstack1111l1l11l_opy_.bstack111l1l1111_opy_(): bstack1111l1l11l_opy_.bstack111l111l1l_opy_(event)
        }
        cls.bstack1ll1ll111l_opy_(bstack1111ll1111_opy_)
        result = getattr(bstack1111l1l11l_opy_, bstack1ll_opy_ (u"࠭ࡲࡦࡵࡸࡰࡹ࠭∭"), None)
        if event == bstack1ll_opy_ (u"ࠧࡕࡧࡶࡸࡗࡻ࡮ࡔࡶࡤࡶࡹ࡫ࡤࠨ∮"):
            threading.current_thread().bstackTestMeta = {bstack1ll_opy_ (u"ࠨࡵࡷࡥࡹࡻࡳࠨ∯"): bstack1ll_opy_ (u"ࠩࡳࡩࡳࡪࡩ࡯ࡩࠪ∰")}
        elif event == bstack1ll_opy_ (u"ࠪࡘࡪࡹࡴࡓࡷࡱࡊ࡮ࡴࡩࡴࡪࡨࡨࠬ∱"):
            threading.current_thread().bstackTestMeta = {bstack1ll_opy_ (u"ࠫࡸࡺࡡࡵࡷࡶࠫ∲"): getattr(result, bstack1ll_opy_ (u"ࠬࡸࡥࡴࡷ࡯ࡸࠬ∳"), bstack1ll_opy_ (u"࠭ࠧ∴"))}
    @classmethod
    def on(cls):
        if (os.environ.get(bstack1ll_opy_ (u"ࠧࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡔࡆࡕࡗࡌ࡚ࡈ࡟ࡋ࡙ࡗࠫ∵"), None) is None or os.environ[bstack1ll_opy_ (u"ࠨࡄࡕࡓ࡜࡙ࡅࡓࡕࡗࡅࡈࡑ࡟ࡕࡇࡖࡘࡍ࡛ࡂࡠࡌ࡚ࡘࠬ∶")] == bstack1ll_opy_ (u"ࠤࡱࡹࡱࡲࠢ∷")) and (os.environ.get(bstack1ll_opy_ (u"ࠪࡆࡘࡥࡁ࠲࠳࡜ࡣࡏ࡝ࡔࠨ∸"), None) is None or os.environ[bstack1ll_opy_ (u"ࠫࡇ࡙࡟ࡂ࠳࠴࡝ࡤࡐࡗࡕࠩ∹")] == bstack1ll_opy_ (u"ࠧࡴࡵ࡭࡮ࠥ∺")):
            return False
        return True
    @staticmethod
    def bstack1lll1ll1llll_opy_(func):
        def wrap(*args, **kwargs):
            if bstack1lll1111l_opy_.on():
                return func(*args, **kwargs)
            return
        return wrap
    @staticmethod
    def default_headers():
        headers = {
            bstack1ll_opy_ (u"࠭ࡃࡰࡰࡷࡩࡳࡺ࠭ࡕࡻࡳࡩࠬ∻"): bstack1ll_opy_ (u"ࠧࡢࡲࡳࡰ࡮ࡩࡡࡵ࡫ࡲࡲ࠴ࡰࡳࡰࡰࠪ∼"),
            bstack1ll_opy_ (u"ࠨ࡚࠰ࡆࡘ࡚ࡁࡄࡍ࠰ࡘࡊ࡙ࡔࡐࡒࡖࠫ∽"): bstack1ll_opy_ (u"ࠩࡷࡶࡺ࡫ࠧ∾")
        }
        if os.environ.get(bstack1ll_opy_ (u"ࠪࡆࡗࡕࡗࡔࡇࡕࡗ࡙ࡇࡃࡌࡡࡗࡉࡘ࡚ࡈࡖࡄࡢࡎ࡜࡚ࠧ∿"), None):
            headers[bstack1ll_opy_ (u"ࠫࡆࡻࡴࡩࡱࡵ࡭ࡿࡧࡴࡪࡱࡱࠫ≀")] = bstack1ll_opy_ (u"ࠬࡈࡥࡢࡴࡨࡶࠥࢁࡽࠨ≁").format(os.environ[bstack1ll_opy_ (u"ࠨࡂࡓࡑ࡚ࡗࡊࡘࡓࡕࡃࡆࡏࡤ࡚ࡅࡔࡖࡋ࡙ࡇࡥࡊࡘࡖࠥ≂")])
        return headers
    @staticmethod
    def request_url(url):
        return bstack1ll_opy_ (u"ࠧࡼࡿ࠲ࡿࢂ࠭≃").format(bstack1lll1llll1ll_opy_, url)
    @staticmethod
    def current_test_uuid():
        return getattr(threading.current_thread(), bstack1ll_opy_ (u"ࠨࡥࡸࡶࡷ࡫࡮ࡵࡡࡷࡩࡸࡺ࡟ࡶࡷ࡬ࡨࠬ≄"), None)
    @staticmethod
    def bstack111ll1111l_opy_(driver):
        return {
            bstack11l111ll11l_opy_(): bstack11l11111ll1_opy_(driver)
        }
    @staticmethod
    def bstack1llll1111l11_opy_(exception_info, report):
        return [{bstack1ll_opy_ (u"ࠩࡥࡥࡨࡱࡴࡳࡣࡦࡩࠬ≅"): [exception_info.exconly(), report.longreprtext]}]
    @staticmethod
    def bstack1llllll1111_opy_(typename):
        if bstack1ll_opy_ (u"ࠥࡅࡸࡹࡥࡳࡶ࡬ࡳࡳࠨ≆") in typename:
            return bstack1ll_opy_ (u"ࠦࡆࡹࡳࡦࡴࡷ࡭ࡴࡴࡅࡳࡴࡲࡶࠧ≇")
        return bstack1ll_opy_ (u"࡛ࠧ࡮ࡩࡣࡱࡨࡱ࡫ࡤࡆࡴࡵࡳࡷࠨ≈")