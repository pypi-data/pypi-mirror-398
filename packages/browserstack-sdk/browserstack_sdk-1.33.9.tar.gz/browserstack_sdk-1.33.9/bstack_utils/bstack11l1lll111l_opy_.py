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
import requests
from urllib.parse import urljoin, urlencode
from datetime import datetime
import os
import logging
import json
from bstack_utils.constants import bstack11l1l1ll1ll_opy_
logger = logging.getLogger(__name__)
class bstack11l1lll11ll_opy_:
    @staticmethod
    def results(builder,params=None):
        bstack1llll1ll1lll_opy_ = urljoin(builder, bstack1ll_opy_ (u"ࠨ࡫ࡶࡷࡺ࡫ࡳࠨ⁅"))
        if params:
            bstack1llll1ll1lll_opy_ += bstack1ll_opy_ (u"ࠤࡂࡿࢂࠨ⁆").format(urlencode({bstack1ll_opy_ (u"ࠪࡸࡪࡹࡴࡠࡴࡸࡲࡤࡻࡵࡪࡦࠪ⁇"): params.get(bstack1ll_opy_ (u"ࠫࡹ࡫ࡳࡵࡡࡵࡹࡳࡥࡵࡶ࡫ࡧࠫ⁈"))}))
        return bstack11l1lll11ll_opy_.bstack1llll1lll1l1_opy_(bstack1llll1ll1lll_opy_)
    @staticmethod
    def bstack11l1ll1lll1_opy_(builder,params=None):
        bstack1llll1ll1lll_opy_ = urljoin(builder, bstack1ll_opy_ (u"ࠬ࡯ࡳࡴࡷࡨࡷ࠲ࡹࡵ࡮࡯ࡤࡶࡾ࠭⁉"))
        if params:
            bstack1llll1ll1lll_opy_ += bstack1ll_opy_ (u"ࠨ࠿ࡼࡿࠥ⁊").format(urlencode({bstack1ll_opy_ (u"ࠧࡵࡧࡶࡸࡤࡸࡵ࡯ࡡࡸࡹ࡮ࡪࠧ⁋"): params.get(bstack1ll_opy_ (u"ࠨࡶࡨࡷࡹࡥࡲࡶࡰࡢࡹࡺ࡯ࡤࠨ⁌"))}))
        return bstack11l1lll11ll_opy_.bstack1llll1lll1l1_opy_(bstack1llll1ll1lll_opy_)
    @staticmethod
    def bstack1llll1lll1l1_opy_(bstack1llll1ll1ll1_opy_):
        bstack1llll1lll11l_opy_ = os.environ.get(bstack1ll_opy_ (u"ࠩࡅࡗࡤࡇ࠱࠲࡛ࡢࡎ࡜࡚ࠧ⁍"), os.environ.get(bstack1ll_opy_ (u"ࠪࡆࡗࡕࡗࡔࡇࡕࡗ࡙ࡇࡃࡌࡡࡗࡉࡘ࡚ࡈࡖࡄࡢࡎ࡜࡚ࠧ⁎"), bstack1ll_opy_ (u"ࠫࠬ⁏")))
        headers = {bstack1ll_opy_ (u"ࠬࡇࡵࡵࡪࡲࡶ࡮ࢀࡡࡵ࡫ࡲࡲࠬ⁐"): bstack1ll_opy_ (u"࠭ࡂࡦࡣࡵࡩࡷࠦࡻࡾࠩ⁑").format(bstack1llll1lll11l_opy_)}
        response = requests.get(bstack1llll1ll1ll1_opy_, headers=headers)
        bstack1llll1ll1l11_opy_ = {}
        try:
            bstack1llll1ll1l11_opy_ = response.json()
        except Exception as e:
            logger.debug(bstack1ll_opy_ (u"ࠢࡇࡣ࡬ࡰࡪࡪࠠࡵࡱࠣࡴࡦࡸࡳࡦࠢࡍࡗࡔࡔࠠࡳࡧࡶࡴࡴࡴࡳࡦ࠼ࠣࡿࢂࠨ⁒").format(e))
            pass
        if bstack1llll1ll1l11_opy_ is not None:
            bstack1llll1ll1l11_opy_[bstack1ll_opy_ (u"ࠨࡰࡨࡼࡹࡥࡰࡰ࡮࡯ࡣࡹ࡯࡭ࡦࠩ⁓")] = response.headers.get(bstack1ll_opy_ (u"ࠩࡱࡩࡽࡺ࡟ࡱࡱ࡯ࡰࡤࡺࡩ࡮ࡧࠪ⁔"), str(int(datetime.now().timestamp() * 1000)))
            bstack1llll1ll1l11_opy_[bstack1ll_opy_ (u"ࠪࡷࡹࡧࡴࡶࡵࠪ⁕")] = response.status_code
        return bstack1llll1ll1l11_opy_
    @staticmethod
    def bstack1llll1ll1l1l_opy_(bstack1llll1ll11ll_opy_, data):
        logger.debug(bstack1ll_opy_ (u"ࠦࡕࡸ࡯ࡤࡧࡶࡷ࡮ࡴࡧࠡࡔࡨࡵࡺ࡫ࡳࡵࠢࡩࡳࡷࠦࡴࡦࡵࡷࡓࡷࡩࡨࡦࡵࡷࡶࡦࡺࡩࡰࡰࡖࡴࡱ࡯ࡴࡕࡧࡶࡸࡸࠨ⁖"))
        return bstack11l1lll11ll_opy_.bstack1llll1llll11_opy_(bstack1ll_opy_ (u"ࠬࡖࡏࡔࡖࠪ⁗"), bstack1llll1ll11ll_opy_, data=data)
    @staticmethod
    def bstack1llll1lll1ll_opy_(bstack1llll1ll11ll_opy_, data):
        logger.debug(bstack1ll_opy_ (u"ࠨࡐࡳࡱࡦࡩࡸࡹࡩ࡯ࡩࠣࡖࡪࡷࡵࡦࡵࡷࠤ࡫ࡵࡲࠡࡩࡨࡸ࡙࡫ࡳࡵࡑࡵࡧ࡭࡫ࡳࡵࡴࡤࡸ࡮ࡵ࡮ࡐࡴࡧࡩࡷ࡫ࡤࡕࡧࡶࡸࡸࠨ⁘"))
        res = bstack11l1lll11ll_opy_.bstack1llll1llll11_opy_(bstack1ll_opy_ (u"ࠧࡈࡇࡗࠫ⁙"), bstack1llll1ll11ll_opy_, data=data)
        return res
    @staticmethod
    def bstack1llll1llll11_opy_(method, bstack1llll1ll11ll_opy_, data=None, params=None, extra_headers=None):
        bstack1llll1lll11l_opy_ = os.environ.get(bstack1ll_opy_ (u"ࠨࡄࡕࡓ࡜࡙ࡅࡓࡕࡗࡅࡈࡑ࡟ࡕࡇࡖࡘࡍ࡛ࡂࡠࡌ࡚ࡘࠬ⁚"), bstack1ll_opy_ (u"ࠩࠪ⁛"))
        headers = {
            bstack1ll_opy_ (u"ࠪࡥࡺࡺࡨࡰࡴ࡬ࡾࡦࡺࡩࡰࡰࠪ⁜"): bstack1ll_opy_ (u"ࠫࡇ࡫ࡡࡳࡧࡵࠤࢀࢃࠧ⁝").format(bstack1llll1lll11l_opy_),
            bstack1ll_opy_ (u"ࠬࡉ࡯࡯ࡶࡨࡲࡹ࠳ࡔࡺࡲࡨࠫ⁞"): bstack1ll_opy_ (u"࠭ࡡࡱࡲ࡯࡭ࡨࡧࡴࡪࡱࡱ࠳࡯ࡹ࡯࡯ࠩ "),
            bstack1ll_opy_ (u"ࠧࡂࡥࡦࡩࡵࡺࠧ⁠"): bstack1ll_opy_ (u"ࠨࡣࡳࡴࡱ࡯ࡣࡢࡶ࡬ࡳࡳ࠵ࡪࡴࡱࡱࠫ⁡")
        }
        if extra_headers:
            headers.update(extra_headers)
        url = bstack11l1l1ll1ll_opy_ + bstack1ll_opy_ (u"ࠤ࠲ࠦ⁢") + bstack1llll1ll11ll_opy_.lstrip(bstack1ll_opy_ (u"ࠪ࠳ࠬ⁣"))
        try:
            if method == bstack1ll_opy_ (u"ࠫࡌࡋࡔࠨ⁤"):
                response = requests.get(url, headers=headers, params=params, json=data)
            elif method == bstack1ll_opy_ (u"ࠬࡖࡏࡔࡖࠪ⁥"):
                response = requests.post(url, headers=headers, json=data)
            elif method == bstack1ll_opy_ (u"࠭ࡐࡖࡖࠪ⁦"):
                response = requests.put(url, headers=headers, json=data)
            else:
                raise ValueError(bstack1ll_opy_ (u"ࠢࡖࡰࡶࡹࡵࡶ࡯ࡳࡶࡨࡨࠥࡎࡔࡕࡒࠣࡱࡪࡺࡨࡰࡦ࠽ࠤࢀࢃࠢ⁧").format(method))
            logger.debug(bstack1ll_opy_ (u"ࠣࡑࡵࡧ࡭࡫ࡳࡵࡴࡤࡸ࡮ࡵ࡮ࠡࡴࡨࡵࡺ࡫ࡳࡵࠢࡰࡥࡩ࡫ࠠࡵࡱ࡙ࠣࡗࡒ࠺ࠡࡽࢀࠤࡼ࡯ࡴࡩࠢࡰࡩࡹ࡮࡯ࡥ࠼ࠣࡿࢂࠨ⁨").format(url, method))
            bstack1llll1ll1l11_opy_ = {}
            try:
                bstack1llll1ll1l11_opy_ = response.json()
            except Exception as e:
                logger.debug(bstack1ll_opy_ (u"ࠤࡉࡥ࡮ࡲࡥࡥࠢࡷࡳࠥࡶࡡࡳࡵࡨࠤࡏ࡙ࡏࡏࠢࡵࡩࡸࡶ࡯࡯ࡵࡨ࠾ࠥࢁࡽࠡ࠯ࠣࡿࢂࠨ⁩").format(e, response.text))
            if bstack1llll1ll1l11_opy_ is not None:
                bstack1llll1ll1l11_opy_[bstack1ll_opy_ (u"ࠪࡲࡪࡾࡴࡠࡲࡲࡰࡱࡥࡴࡪ࡯ࡨࠫ⁪")] = response.headers.get(
                    bstack1ll_opy_ (u"ࠫࡳ࡫ࡸࡵࡡࡳࡳࡱࡲ࡟ࡵ࡫ࡰࡩࠬ⁫"), str(int(datetime.now().timestamp() * 1000))
                )
                bstack1llll1ll1l11_opy_[bstack1ll_opy_ (u"ࠬࡹࡴࡢࡶࡸࡷࠬ⁬")] = response.status_code
            return bstack1llll1ll1l11_opy_
        except Exception as e:
            logger.error(bstack1ll_opy_ (u"ࠨࡏࡳࡥ࡫ࡩࡸࡺࡲࡢࡶ࡬ࡳࡳࠦࡲࡦࡳࡸࡩࡸࡺࠠࡧࡣ࡬ࡰࡪࡪ࠺ࠡࡽࢀࠤ࠲ࠦࡻࡾࠤ⁭").format(e, url))
            return None
    @staticmethod
    def bstack11l11lll111_opy_(bstack1llll1ll1ll1_opy_, data):
        bstack1ll_opy_ (u"ࠢࠣࠤࠍࠤࠥࠦࠠࠡࠢࠣࠤࡘ࡫࡮ࡥࡵࠣࡥࠥࡖࡕࡕࠢࡵࡩࡶࡻࡥࡴࡶࠣࡸࡴࠦࡳࡵࡱࡵࡩࠥࡺࡨࡦࠢࡩࡥ࡮ࡲࡥࡥࠢࡷࡩࡸࡺࡳࠋࠢࠣࠤࠥࠦࠠࠡࠢࠥࠦࠧ⁮")
        bstack1llll1lll11l_opy_ = os.environ.get(bstack1ll_opy_ (u"ࠨࡄࡕࡓ࡜࡙ࡅࡓࡕࡗࡅࡈࡑ࡟ࡕࡇࡖࡘࡍ࡛ࡂࡠࡌ࡚ࡘࠬ⁯"), bstack1ll_opy_ (u"ࠩࠪ⁰"))
        headers = {
            bstack1ll_opy_ (u"ࠪࡥࡺࡺࡨࡰࡴ࡬ࡾࡦࡺࡩࡰࡰࠪⁱ"): bstack1ll_opy_ (u"ࠫࡇ࡫ࡡࡳࡧࡵࠤࢀࢃࠧ⁲").format(bstack1llll1lll11l_opy_),
            bstack1ll_opy_ (u"ࠬࡉ࡯࡯ࡶࡨࡲࡹ࠳ࡔࡺࡲࡨࠫ⁳"): bstack1ll_opy_ (u"࠭ࡡࡱࡲ࡯࡭ࡨࡧࡴࡪࡱࡱ࠳࡯ࡹ࡯࡯ࠩ⁴")
        }
        response = requests.put(bstack1llll1ll1ll1_opy_, headers=headers, json=data)
        bstack1llll1ll1l11_opy_ = {}
        try:
            bstack1llll1ll1l11_opy_ = response.json()
        except Exception as e:
            logger.debug(bstack1ll_opy_ (u"ࠢࡇࡣ࡬ࡰࡪࡪࠠࡵࡱࠣࡴࡦࡸࡳࡦࠢࡍࡗࡔࡔࠠࡳࡧࡶࡴࡴࡴࡳࡦ࠼ࠣࡿࢂࠨ⁵").format(e))
            pass
        logger.debug(bstack1ll_opy_ (u"ࠣࡔࡨࡵࡺ࡫ࡳࡵࡗࡷ࡭ࡱࡹ࠺ࠡࡲࡸࡸࡤ࡬ࡡࡪ࡮ࡨࡨࡤࡺࡥࡴࡶࡶࠤࡷ࡫ࡳࡱࡱࡱࡷࡪࡀࠠࡼࡿࠥ⁶").format(bstack1llll1ll1l11_opy_))
        if bstack1llll1ll1l11_opy_ is not None:
            bstack1llll1ll1l11_opy_[bstack1ll_opy_ (u"ࠩࡱࡩࡽࡺ࡟ࡱࡱ࡯ࡰࡤࡺࡩ࡮ࡧࠪ⁷")] = response.headers.get(
                bstack1ll_opy_ (u"ࠪࡲࡪࡾࡴࡠࡲࡲࡰࡱࡥࡴࡪ࡯ࡨࠫ⁸"), str(int(datetime.now().timestamp() * 1000))
            )
            bstack1llll1ll1l11_opy_[bstack1ll_opy_ (u"ࠫࡸࡺࡡࡵࡷࡶࠫ⁹")] = response.status_code
        return bstack1llll1ll1l11_opy_
    @staticmethod
    def bstack11l11l1l111_opy_(bstack1llll1ll1ll1_opy_):
        bstack1ll_opy_ (u"ࠧࠨࠢࠋࠢࠣࠤࠥࠦࠠࠡࠢࡖࡩࡳࡪࡳࠡࡣࠣࡋࡊ࡚ࠠࡳࡧࡴࡹࡪࡹࡴࠡࡶࡲࠤ࡬࡫ࡴࠡࡶ࡫ࡩࠥࡩ࡯ࡶࡰࡷࠤࡴ࡬ࠠࡧࡣ࡬ࡰࡪࡪࠠࡵࡧࡶࡸࡸࠐࠠࠡࠢࠣࠤࠥࠦࠠࠣࠤࠥ⁺")
        bstack1llll1lll11l_opy_ = os.environ.get(bstack1ll_opy_ (u"࠭ࡂࡓࡑ࡚ࡗࡊࡘࡓࡕࡃࡆࡏࡤ࡚ࡅࡔࡖࡋ࡙ࡇࡥࡊࡘࡖࠪ⁻"), bstack1ll_opy_ (u"ࠧࠨ⁼"))
        headers = {
            bstack1ll_opy_ (u"ࠨࡣࡸࡸ࡭ࡵࡲࡪࡼࡤࡸ࡮ࡵ࡮ࠨ⁽"): bstack1ll_opy_ (u"ࠩࡅࡩࡦࡸࡥࡳࠢࡾࢁࠬ⁾").format(bstack1llll1lll11l_opy_),
            bstack1ll_opy_ (u"ࠪࡇࡴࡴࡴࡦࡰࡷ࠱࡙ࡿࡰࡦࠩⁿ"): bstack1ll_opy_ (u"ࠫࡦࡶࡰ࡭࡫ࡦࡥࡹ࡯࡯࡯࠱࡭ࡷࡴࡴࠧ₀")
        }
        response = requests.get(bstack1llll1ll1ll1_opy_, headers=headers)
        bstack1llll1ll1l11_opy_ = {}
        try:
            bstack1llll1ll1l11_opy_ = response.json()
            logger.debug(bstack1ll_opy_ (u"ࠧࡘࡥࡲࡷࡨࡷࡹ࡛ࡴࡪ࡮ࡶ࠾ࠥ࡭ࡥࡵࡡࡩࡥ࡮ࡲࡥࡥࡡࡷࡩࡸࡺࡳࠡࡴࡨࡷࡵࡵ࡮ࡴࡧ࠽ࠤࢀࢃࠢ₁").format(bstack1llll1ll1l11_opy_))
        except Exception as e:
            logger.debug(bstack1ll_opy_ (u"ࠨࡆࡢ࡫࡯ࡩࡩࠦࡴࡰࠢࡳࡥࡷࡹࡥࠡࡌࡖࡓࡓࠦࡲࡦࡵࡳࡳࡳࡹࡥ࠻ࠢࡾࢁࠥ࠳ࠠࡼࡿࠥ₂").format(e, response.text))
            pass
        if bstack1llll1ll1l11_opy_ is not None:
            bstack1llll1ll1l11_opy_[bstack1ll_opy_ (u"ࠧ࡯ࡧࡻࡸࡤࡶ࡯࡭࡮ࡢࡸ࡮ࡳࡥࠨ₃")] = response.headers.get(
                bstack1ll_opy_ (u"ࠨࡰࡨࡼࡹࡥࡰࡰ࡮࡯ࡣࡹ࡯࡭ࡦࠩ₄"), str(int(datetime.now().timestamp() * 1000))
            )
            bstack1llll1ll1l11_opy_[bstack1ll_opy_ (u"ࠩࡶࡸࡦࡺࡵࡴࠩ₅")] = response.status_code
        return bstack1llll1ll1l11_opy_
    @staticmethod
    def bstack1111l11ll1l_opy_(bstack11l1lll1l1l_opy_, payload):
        bstack1ll_opy_ (u"ࠥࠦࠧࠐࠠࠡࠢࠣࠤࠥࠦࠠࡎࡣ࡮ࡩࡸࠦࡡࠡࡒࡒࡗ࡙ࠦࡲࡦࡳࡸࡩࡸࡺࠠࡵࡱࠣࡸ࡭࡫ࠠࡤࡱ࡯ࡰࡪࡩࡴ࠮ࡤࡸ࡭ࡱࡪ࠭ࡥࡣࡷࡥࠥ࡫࡮ࡥࡲࡲ࡭ࡳࡺ࠮ࠋࠢࠣࠤࠥࠦࠠࠡࠢࡄࡶ࡬ࡹ࠺ࠋࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࡥ࡯ࡦࡳࡳ࡮ࡴࡴࠡࠪࡶࡸࡷ࠯࠺ࠡࡖ࡫ࡩࠥࡇࡐࡊࠢࡨࡲࡩࡶ࡯ࡪࡰࡷࠤࡵࡧࡴࡩ࠰ࠍࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࡲࡤࡽࡱࡵࡡࡥࠢࠫࡨ࡮ࡩࡴࠪ࠼ࠣࡘ࡭࡫ࠠࡳࡧࡴࡹࡪࡹࡴࠡࡲࡤࡽࡱࡵࡡࡥ࠰ࠍࠤࠥࠦࠠࠡࠢࠣࠤࡗ࡫ࡴࡶࡴࡱࡷ࠿ࠐࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࡩ࡯ࡣࡵ࠼ࠣࡖࡪࡹࡰࡰࡰࡶࡩࠥ࡬ࡲࡰ࡯ࠣࡸ࡭࡫ࠠࡂࡒࡌ࠰ࠥࡵࡲࠡࡐࡲࡲࡪࠦࡩࡧࠢࡩࡥ࡮ࡲࡥࡥ࠰ࠍࠤࠥࠦࠠࠡࠢࠣࠤࠧࠨࠢ₆")
        try:
            url = bstack1ll_opy_ (u"ࠦࢀࢃ࠯ࡼࡿࠥ₇").format(bstack11l1l1ll1ll_opy_, bstack11l1lll1l1l_opy_)
            bstack1llll1lll11l_opy_ = os.environ.get(bstack1ll_opy_ (u"ࠬࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣ࡙ࡋࡓࡕࡊࡘࡆࡤࡐࡗࡕࠩ₈"), bstack1ll_opy_ (u"࠭ࠧ₉"))
            headers = {
                bstack1ll_opy_ (u"ࠧࡢࡷࡷ࡬ࡴࡸࡩࡻࡣࡷ࡭ࡴࡴࠧ₊"): bstack1ll_opy_ (u"ࠨࡄࡨࡥࡷ࡫ࡲࠡࡽࢀࠫ₋").format(bstack1llll1lll11l_opy_),
                bstack1ll_opy_ (u"ࠩࡆࡳࡳࡺࡥ࡯ࡶ࠰ࡘࡾࡶࡥࠨ₌"): bstack1ll_opy_ (u"ࠪࡥࡵࡶ࡬ࡪࡥࡤࡸ࡮ࡵ࡮࠰࡬ࡶࡳࡳ࠭₍")
            }
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            bstack1llll1lll111_opy_ = [200, 202]
            if response.status_code in bstack1llll1lll111_opy_:
                return response.json()
            else:
                logger.error(bstack1ll_opy_ (u"ࠦࡋࡧࡩ࡭ࡧࡧࠤࡹࡵࠠࡤࡱ࡯ࡰࡪࡩࡴࠡࡤࡸ࡭ࡱࡪࠠࡥࡣࡷࡥ࠳ࠦࡓࡵࡣࡷࡹࡸࡀࠠࡼࡿ࠯ࠤࡗ࡫ࡳࡱࡱࡱࡷࡪࡀࠠࡼࡿࠥ₎").format(
                    response.status_code, response.text))
                return None
        except Exception as e:
            logger.error(bstack1ll_opy_ (u"ࠧࡋࡸࡤࡧࡳࡸ࡮ࡵ࡮ࠡ࡫ࡱࠤࡵࡵࡳࡵࡡࡦࡳࡱࡲࡥࡤࡶࡢࡦࡺ࡯࡬ࡥࡡࡧࡥࡹࡧ࠺ࠡࡽࢀࠦ₏").format(e))
            return None