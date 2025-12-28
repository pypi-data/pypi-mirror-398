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
import os
import threading
from bstack_utils.config import Config
from bstack_utils.constants import EVENTS, STAGE
from bstack_utils.helper import bstack111ll111111_opy_, bstack11ll1l11l_opy_, bstack1l11l11l_opy_, bstack1l11l1l1l_opy_, \
    bstack111ll1ll1ll_opy_
from bstack_utils.measure import measure
def bstack11lll1l11_opy_(bstack1llll1l1l1ll_opy_):
    for driver in bstack1llll1l1l1ll_opy_:
        try:
            driver.quit()
        except Exception as e:
            pass
@measure(event_name=EVENTS.bstack11ll1ll1l1_opy_, stage=STAGE.bstack1l1lll1ll1_opy_)
def bstack11ll11111l_opy_(driver, status, reason=bstack1ll_opy_ (u"ࠨࠩₒ")):
    bstack1ll1l1l111_opy_ = Config.bstack11lll1111_opy_()
    if bstack1ll1l1l111_opy_.bstack111111ll11_opy_():
        return
    bstack1111l11l1_opy_ = bstack1l11ll1l1_opy_(bstack1ll_opy_ (u"ࠩࡶࡩࡹ࡙ࡥࡴࡵ࡬ࡳࡳ࡙ࡴࡢࡶࡸࡷࠬₓ"), bstack1ll_opy_ (u"ࠪࠫₔ"), status, reason, bstack1ll_opy_ (u"ࠫࠬₕ"), bstack1ll_opy_ (u"ࠬ࠭ₖ"))
    driver.execute_script(bstack1111l11l1_opy_)
@measure(event_name=EVENTS.bstack11ll1ll1l1_opy_, stage=STAGE.bstack1l1lll1ll1_opy_)
def bstack1l111111ll_opy_(page, status, reason=bstack1ll_opy_ (u"࠭ࠧₗ")):
    try:
        if page is None:
            return
        bstack1ll1l1l111_opy_ = Config.bstack11lll1111_opy_()
        if bstack1ll1l1l111_opy_.bstack111111ll11_opy_():
            return
        bstack1111l11l1_opy_ = bstack1l11ll1l1_opy_(bstack1ll_opy_ (u"ࠧࡴࡧࡷࡗࡪࡹࡳࡪࡱࡱࡗࡹࡧࡴࡶࡵࠪₘ"), bstack1ll_opy_ (u"ࠨࠩₙ"), status, reason, bstack1ll_opy_ (u"ࠩࠪₚ"), bstack1ll_opy_ (u"ࠪࠫₛ"))
        page.evaluate(bstack1ll_opy_ (u"ࠦࡤࠦ࠽࠿ࠢࡾࢁࠧₜ"), bstack1111l11l1_opy_)
    except Exception as e:
        print(bstack1ll_opy_ (u"ࠧࡋࡸࡤࡧࡳࡸ࡮ࡵ࡮ࠡ࡫ࡱࠤࡸ࡫ࡴࡵ࡫ࡱ࡫ࠥࡹࡥࡴࡵ࡬ࡳࡳࠦࡳࡵࡣࡷࡹࡸࠦࡦࡰࡴࠣࡴࡱࡧࡹࡸࡴ࡬࡫࡭ࡺࠠࡼࡿࠥ₝"), e)
def bstack1l11ll1l1_opy_(type, name, status, reason, bstack1lllll1lll_opy_, bstack11l1l11ll1_opy_):
    bstack1l1lll1l1l_opy_ = {
        bstack1ll_opy_ (u"࠭ࡡࡤࡶ࡬ࡳࡳ࠭₞"): type,
        bstack1ll_opy_ (u"ࠧࡢࡴࡪࡹࡲ࡫࡮ࡵࡵࠪ₟"): {}
    }
    if type == bstack1ll_opy_ (u"ࠨࡣࡱࡲࡴࡺࡡࡵࡧࠪ₠"):
        bstack1l1lll1l1l_opy_[bstack1ll_opy_ (u"ࠩࡤࡶ࡬ࡻ࡭ࡦࡰࡷࡷࠬ₡")][bstack1ll_opy_ (u"ࠪࡰࡪࡼࡥ࡭ࠩ₢")] = bstack1lllll1lll_opy_
        bstack1l1lll1l1l_opy_[bstack1ll_opy_ (u"ࠫࡦࡸࡧࡶ࡯ࡨࡲࡹࡹࠧ₣")][bstack1ll_opy_ (u"ࠬࡪࡡࡵࡣࠪ₤")] = json.dumps(str(bstack11l1l11ll1_opy_))
    if type == bstack1ll_opy_ (u"࠭ࡳࡦࡶࡖࡩࡸࡹࡩࡰࡰࡑࡥࡲ࡫ࠧ₥"):
        bstack1l1lll1l1l_opy_[bstack1ll_opy_ (u"ࠧࡢࡴࡪࡹࡲ࡫࡮ࡵࡵࠪ₦")][bstack1ll_opy_ (u"ࠨࡰࡤࡱࡪ࠭₧")] = name
    if type == bstack1ll_opy_ (u"ࠩࡶࡩࡹ࡙ࡥࡴࡵ࡬ࡳࡳ࡙ࡴࡢࡶࡸࡷࠬ₨"):
        bstack1l1lll1l1l_opy_[bstack1ll_opy_ (u"ࠪࡥࡷ࡭ࡵ࡮ࡧࡱࡸࡸ࠭₩")][bstack1ll_opy_ (u"ࠫࡸࡺࡡࡵࡷࡶࠫ₪")] = status
        if status == bstack1ll_opy_ (u"ࠬ࡬ࡡࡪ࡮ࡨࡨࠬ₫") and str(reason) != bstack1ll_opy_ (u"ࠨࠢ€"):
            bstack1l1lll1l1l_opy_[bstack1ll_opy_ (u"ࠧࡢࡴࡪࡹࡲ࡫࡮ࡵࡵࠪ₭")][bstack1ll_opy_ (u"ࠨࡴࡨࡥࡸࡵ࡮ࠨ₮")] = json.dumps(str(reason))
    bstack1llll11l11_opy_ = bstack1ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫ࡠࡧࡻࡩࡨࡻࡴࡰࡴ࠽ࠤࢀࢃࠧ₯").format(json.dumps(bstack1l1lll1l1l_opy_))
    return bstack1llll11l11_opy_
def bstack111llll1l_opy_(url, config, logger, bstack11llllll1_opy_=False):
    hostname = bstack11ll1l11l_opy_(url)
    is_private = bstack1l11l1l1l_opy_(hostname)
    try:
        if is_private or bstack11llllll1_opy_:
            file_path = bstack111ll111111_opy_(bstack1ll_opy_ (u"ࠪ࠲ࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭ࠪ₰"), bstack1ll_opy_ (u"ࠫ࠳ࡨࡳࡵࡣࡦ࡯࠲ࡩ࡯࡯ࡨ࡬࡫࠳ࡰࡳࡰࡰࠪ₱"), logger)
            if os.environ.get(bstack1ll_opy_ (u"ࠬࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣࡑࡕࡃࡂࡎࡢࡒࡔ࡚࡟ࡔࡇࡗࡣࡊࡘࡒࡐࡔࠪ₲")) and eval(
                    os.environ.get(bstack1ll_opy_ (u"࠭ࡂࡓࡑ࡚ࡗࡊࡘࡓࡕࡃࡆࡏࡤࡒࡏࡄࡃࡏࡣࡓࡕࡔࡠࡕࡈࡘࡤࡋࡒࡓࡑࡕࠫ₳"))):
                return
            if (bstack1ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰࡒ࡯ࡤࡣ࡯ࠫ₴") in config and not config[bstack1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱࡌࡰࡥࡤࡰࠬ₵")]):
                os.environ[bstack1ll_opy_ (u"ࠩࡅࡖࡔ࡝ࡓࡆࡔࡖࡘࡆࡉࡋࡠࡎࡒࡇࡆࡒ࡟ࡏࡑࡗࡣࡘࡋࡔࡠࡇࡕࡖࡔࡘࠧ₶")] = str(True)
                bstack1llll1l1ll11_opy_ = {bstack1ll_opy_ (u"ࠪ࡬ࡴࡹࡴ࡯ࡣࡰࡩࠬ₷"): hostname}
                bstack111ll1ll1ll_opy_(bstack1ll_opy_ (u"ࠫ࠳ࡨࡳࡵࡣࡦ࡯࠲ࡩ࡯࡯ࡨ࡬࡫࠳ࡰࡳࡰࡰࠪ₸"), bstack1ll_opy_ (u"ࠬࡴࡵࡥࡩࡨࡣࡱࡵࡣࡢ࡮ࠪ₹"), bstack1llll1l1ll11_opy_, logger)
    except Exception as e:
        pass
def bstack1l1l1111ll_opy_(caps, bstack1llll1l1ll1l_opy_):
    if bstack1ll_opy_ (u"࠭ࡢࡴࡶࡤࡧࡰࡀ࡯ࡱࡶ࡬ࡳࡳࡹࠧ₺") in caps:
        caps[bstack1ll_opy_ (u"ࠧࡣࡵࡷࡥࡨࡱ࠺ࡰࡲࡷ࡭ࡴࡴࡳࠨ₻")][bstack1ll_opy_ (u"ࠨ࡮ࡲࡧࡦࡲࠧ₼")] = True
        if bstack1llll1l1ll1l_opy_:
            caps[bstack1ll_opy_ (u"ࠩࡥࡷࡹࡧࡣ࡬࠼ࡲࡴࡹ࡯࡯࡯ࡵࠪ₽")][bstack1ll_opy_ (u"ࠪࡰࡴࡩࡡ࡭ࡋࡧࡩࡳࡺࡩࡧ࡫ࡨࡶࠬ₾")] = bstack1llll1l1ll1l_opy_
    else:
        caps[bstack1ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭࠱ࡰࡴࡩࡡ࡭ࠩ₿")] = True
        if bstack1llll1l1ll1l_opy_:
            caps[bstack1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮࠲ࡱࡵࡣࡢ࡮ࡌࡨࡪࡴࡴࡪࡨ࡬ࡩࡷ࠭⃀")] = bstack1llll1l1ll1l_opy_
def bstack1lllll11lll1_opy_(bstack1111ll1l1l_opy_):
    bstack1llll1l1lll1_opy_ = bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"࠭ࡴࡦࡵࡷࡗࡹࡧࡴࡶࡵࠪ⃁"), bstack1ll_opy_ (u"ࠧࠨ⃂"))
    if bstack1llll1l1lll1_opy_ == bstack1ll_opy_ (u"ࠨࠩ⃃") or bstack1llll1l1lll1_opy_ == bstack1ll_opy_ (u"ࠩࡶ࡯࡮ࡶࡰࡦࡦࠪ⃄"):
        threading.current_thread().testStatus = bstack1111ll1l1l_opy_
    else:
        if bstack1111ll1l1l_opy_ == bstack1ll_opy_ (u"ࠪࡪࡦ࡯࡬ࡦࡦࠪ⃅"):
            threading.current_thread().testStatus = bstack1111ll1l1l_opy_