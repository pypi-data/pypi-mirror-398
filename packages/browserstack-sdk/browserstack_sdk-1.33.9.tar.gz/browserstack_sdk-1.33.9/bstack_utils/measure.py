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
from functools import wraps
from typing import Optional
from bstack_utils.constants import EVENTS, STAGE
from bstack_utils.bstack11l1l1lll1_opy_ import get_logger
from bstack_utils.bstack11ll1llll1_opy_ import bstack1lll1ll1l1l_opy_
bstack11ll1llll1_opy_ = bstack1lll1ll1l1l_opy_()
logger = get_logger(__name__)
def measure(event_name: EVENTS, stage: STAGE, hook_type: Optional[str] = None, bstack1l1l11ll_opy_: Optional[str] = None):
    bstack1ll_opy_ (u"ࠥࠦࠧࠐࠠࠡࠢࠣࡈࡪࡩ࡯ࡳࡣࡷࡳࡷࠦࡴࡰࠢ࡯ࡳ࡬ࠦࡴࡩࡧࠣࡷࡹࡧࡲࡵࠢࡷ࡭ࡲ࡫ࠠࡰࡨࠣࡥࠥ࡬ࡵ࡯ࡥࡷ࡭ࡴࡴࠠࡦࡺࡨࡧࡺࡺࡩࡰࡰࠍࠤࠥࠦࠠࡢ࡮ࡲࡲ࡬ࠦࡷࡪࡶ࡫ࠤࡪࡼࡥ࡯ࡶࠣࡲࡦࡳࡥࠡࡣࡱࡨࠥࡹࡴࡢࡩࡨ࠲ࠏࠦࠠࠡࠢࠥࠦࠧṝ")
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            label: str = event_name.value
            bstack1ll11l11l1l_opy_: str = bstack11ll1llll1_opy_.bstack11l1lllll11_opy_(label)
            start_mark: str = label + bstack1ll_opy_ (u"ࠦ࠿ࡹࡴࡢࡴࡷࠦṞ")
            end_mark: str = label + bstack1ll_opy_ (u"ࠧࡀࡥ࡯ࡦࠥṟ")
            result = None
            try:
                if stage.value == STAGE.bstack11l11l1l11_opy_.value:
                    bstack11ll1llll1_opy_.mark(start_mark)
                    result = func(*args, **kwargs)
                elif stage.value == STAGE.END.value:
                    result = func(*args, **kwargs)
                    bstack11ll1llll1_opy_.end(label, start_mark, end_mark, status=True, failure=None,hook_type=hook_type,test_name=bstack1l1l11ll_opy_)
                elif stage.value == STAGE.bstack1l1lll1ll1_opy_.value:
                    start_mark: str = bstack1ll11l11l1l_opy_ + bstack1ll_opy_ (u"ࠨ࠺ࡴࡶࡤࡶࡹࠨṠ")
                    end_mark: str = bstack1ll11l11l1l_opy_ + bstack1ll_opy_ (u"ࠢ࠻ࡧࡱࡨࠧṡ")
                    bstack11ll1llll1_opy_.mark(start_mark)
                    result = func(*args, **kwargs)
                    bstack11ll1llll1_opy_.end(label, start_mark, end_mark, status=True, failure=None, hook_type=hook_type,test_name=bstack1l1l11ll_opy_)
            except Exception as e:
                bstack11ll1llll1_opy_.end(label, start_mark, end_mark, status=False, failure=str(e), hook_type=hook_type,
                                       test_name=bstack1l1l11ll_opy_)
            return result
        return wrapper
    return decorator