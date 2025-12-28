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
from collections import defaultdict
from threading import Lock
from dataclasses import dataclass
import logging
import traceback
from typing import List, Dict, Any
import os
@dataclass
class bstack11ll1l1l1_opy_:
    sdk_version: str
    path_config: str
    path_project: str
    test_framework: str
    frameworks: List[str]
    framework_versions: Dict[str, str]
    bs_config: Dict[str, Any]
@dataclass
class bstack11ll111l11_opy_:
    pass
class bstack1lll1lll_opy_:
    bstack1l1l1l1lll_opy_ = bstack1ll_opy_ (u"ࠦࡧࡵ࡯ࡵࡵࡷࡶࡦࡶࠢᆼ")
    CONNECT = bstack1ll_opy_ (u"ࠧࡩ࡯࡯ࡰࡨࡧࡹࠨᆽ")
    bstack11llll1ll_opy_ = bstack1ll_opy_ (u"ࠨࡳࡩࡷࡷࡨࡴࡽ࡮ࠣᆾ")
    CONFIG = bstack1ll_opy_ (u"ࠢࡤࡱࡱࡪ࡮࡭ࠢᆿ")
    bstack1ll11ll1lll_opy_ = bstack1ll_opy_ (u"ࠣࡨࡵࡥࡲ࡫ࡷࡰࡴ࡮ࡷࠧᇀ")
    bstack1ll11111l_opy_ = bstack1ll_opy_ (u"ࠤࡨࡼ࡮ࡺࠢᇁ")
class bstack1ll11ll11ll_opy_:
    bstack1ll11ll1ll1_opy_ = bstack1ll_opy_ (u"ࠥࡦࡺ࡯࡬ࡥࡡࡶࡸࡦࡸࡴࡦࡦࠥᇂ")
    FINISHED = bstack1ll_opy_ (u"ࠦࡧࡻࡩ࡭ࡦࡢࡪ࡮ࡴࡩࡴࡪࡨࡨࠧᇃ")
class bstack1ll11ll1111_opy_:
    bstack1ll11ll1ll1_opy_ = bstack1ll_opy_ (u"ࠧࡺࡥࡴࡶࡢࡶࡺࡴ࡟ࡴࡶࡤࡶࡹ࡫ࡤࠣᇄ")
    FINISHED = bstack1ll_opy_ (u"ࠨࡴࡦࡵࡷࡣࡷࡻ࡮ࡠࡨ࡬ࡲ࡮ࡹࡨࡦࡦࠥᇅ")
class bstack1ll11ll1l11_opy_:
    bstack1ll11ll1ll1_opy_ = bstack1ll_opy_ (u"ࠢࡩࡱࡲ࡯ࡤࡸࡵ࡯ࡡࡶࡸࡦࡸࡴࡦࡦࠥᇆ")
    FINISHED = bstack1ll_opy_ (u"ࠣࡪࡲࡳࡰࡥࡲࡶࡰࡢࡪ࡮ࡴࡩࡴࡪࡨࡨࠧᇇ")
class bstack1ll11ll111l_opy_:
    bstack1ll11ll11l1_opy_ = bstack1ll_opy_ (u"ࠤࡦࡦࡹࡥࡳࡦࡵࡶ࡭ࡴࡴ࡟ࡤࡴࡨࡥࡹ࡫ࡤࠣᇈ")
class bstack1ll11ll1l1l_opy_:
    _1ll1l11l1ll_opy_ = None
    def __new__(cls):
        if not cls._1ll1l11l1ll_opy_:
            cls._1ll1l11l1ll_opy_ = super(bstack1ll11ll1l1l_opy_, cls).__new__(cls)
        return cls._1ll1l11l1ll_opy_
    def __init__(self):
        self._hooks = defaultdict(lambda: defaultdict(list))
        self._lock = Lock()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
    def clear(self):
        with self._lock:
            self._hooks = defaultdict(list)
    def register(self, event_name, callback):
        with self._lock:
            if not callable(callback):
                raise ValueError(bstack1ll_opy_ (u"ࠥࡇࡦࡲ࡬ࡣࡣࡦ࡯ࠥࡳࡵࡴࡶࠣࡦࡪࠦࡣࡢ࡮࡯ࡥࡧࡲࡥࠡࡨࡲࡶࠥࠨᇉ") + event_name)
            pid = os.getpid()
            self.logger.debug(bstack1ll_opy_ (u"ࠦࡗ࡫ࡧࡪࡵࡷࡩࡷ࡯࡮ࡨࠢࡦࡥࡱࡲࡢࡢࡥ࡮ࠤ࡫ࡵࡲࠡࡧࡹࡩࡳࡺࠠࠨࡽࡨࡺࡪࡴࡴࡠࡰࡤࡱࡪࢃࠧࠡࡹ࡬ࡸ࡭ࠦࡰࡪࡦࠣࠦᇊ") + str(pid) + bstack1ll_opy_ (u"ࠧࠨᇋ"))
            self._hooks[event_name][pid].append(callback)
    def invoke(self, event_name, *args, **kwargs):
        with self._lock:
            pid = os.getpid()
            callbacks = self._hooks.get(event_name, {}).get(pid, [])
            if not callbacks:
                self.logger.warning(bstack1ll_opy_ (u"ࠨࡎࡰࠢࡦࡥࡱࡲࡢࡢࡥ࡮ࡷࠥ࡬࡯ࡳࠢࡨࡺࡪࡴࡴࠡࠩࡾࡩࡻ࡫࡮ࡵࡡࡱࡥࡲ࡫ࡽࠨࠢࡺ࡭ࡹ࡮ࠠࡱ࡫ࡧࠤࠧᇌ") + str(pid) + bstack1ll_opy_ (u"ࠢࠣᇍ"))
                return
            self.logger.debug(bstack1ll_opy_ (u"ࠣࡋࡱࡺࡴࡱࡩ࡯ࡩࠣࡿࡱ࡫࡮ࠩࡥࡤࡰࡱࡨࡡࡤ࡭ࡶ࠭ࢂࠦࡣࡢ࡮࡯ࡦࡦࡩ࡫ࡴࠢࡩࡳࡷࠦࡥࡷࡧࡱࡸࠥ࠭ࡻࡦࡸࡨࡲࡹࡥ࡮ࡢ࡯ࡨࢁࠬࠦࡷࡪࡶ࡫ࠤࡵ࡯ࡤࠡࠤᇎ") + str(pid) + bstack1ll_opy_ (u"ࠤࠥᇏ"))
            for callback in callbacks:
                try:
                    self.logger.debug(bstack1ll_opy_ (u"ࠥࡍࡳࡼ࡯࡬ࡧࡧࠤࡨࡧ࡬࡭ࡤࡤࡧࡰࠦࡦࡰࡴࠣࡩࡻ࡫࡮ࡵࠢࠪࡿࡪࡼࡥ࡯ࡶࡢࡲࡦࡳࡥࡾࠩࠣࡻ࡮ࡺࡨࠡࡲ࡬ࡨࠥࠨᇐ") + str(pid) + bstack1ll_opy_ (u"ࠦࠧᇑ"))
                    callback(event_name, *args, **kwargs)
                except Exception as e:
                    self.logger.error(bstack1ll_opy_ (u"ࠧࡋࡲࡳࡱࡵࠤ࡮ࡴࡶࡰ࡭࡬ࡲ࡬ࠦࡣࡢ࡮࡯ࡦࡦࡩ࡫ࠡࡨࡲࡶࠥ࡫ࡶࡦࡰࡷࠤࠬࢁࡥࡷࡧࡱࡸࡤࡴࡡ࡮ࡧࢀࠫࠥࡽࡩࡵࡪࠣࡴ࡮ࡪࠠࡼࡲ࡬ࡨࢂࡀࠠࠣᇒ") + str(e) + bstack1ll_opy_ (u"ࠨࠢᇓ"))
                    traceback.print_exc()
bstack111lll1l_opy_ = bstack1ll11ll1l1l_opy_()