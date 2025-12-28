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
from filelock import FileLock
import json
import os
import time
import uuid
import logging
from typing import Dict, List, Optional
from bstack_utils.bstack11l1l1lll1_opy_ import get_logger
logger = get_logger(__name__)
bstack1lllll1lllll_opy_: Dict[str, float] = {}
bstack1llllll11111_opy_: List = []
bstack1llllll1111l_opy_ = 5
bstack1lll11l11l_opy_ = os.path.join(os.getcwd(), bstack1ll_opy_ (u"࠭࡬ࡰࡩࠪῌ"), bstack1ll_opy_ (u"ࠧ࡬ࡧࡼ࠱ࡲ࡫ࡴࡳ࡫ࡦࡷ࠳ࡰࡳࡰࡰࠪ῍"))
logging.getLogger(bstack1ll_opy_ (u"ࠨࡨ࡬ࡰࡪࡲ࡯ࡤ࡭ࠪ῎")).setLevel(logging.WARNING)
lock = FileLock(bstack1lll11l11l_opy_+bstack1ll_opy_ (u"ࠤ࠱ࡰࡴࡩ࡫ࠣ῏"))
class bstack1llllll11l11_opy_:
    duration: float
    name: str
    startTime: float
    worker: int
    status: bool
    failure: str
    details: Optional[str]
    entryType: str
    platform: Optional[int]
    command: Optional[str]
    hookType: Optional[str]
    cli: Optional[bool]
    def __init__(self, duration: float, name: str, start_time: float, bstack1lllll1lll1l_opy_: int, status: bool, failure: str, details: Optional[str] = None, platform: Optional[int] = None, command: Optional[str] = None, test_name: Optional[str] = None, hook_type: Optional[str] = None, cli: Optional[bool] = False) -> None:
        self.duration = duration
        self.name = name
        self.startTime = start_time
        self.worker = bstack1lllll1lll1l_opy_
        self.status = status
        self.failure = failure
        self.details = details
        self.entryType = bstack1ll_opy_ (u"ࠥࡱࡪࡧࡳࡶࡴࡨࠦῐ")
        self.platform = platform
        self.command = command
        self.testName = test_name
        self.hookType = hook_type
        self.cli = cli
class bstack1lll1ll1l1l_opy_:
    global bstack1lllll1lllll_opy_
    @staticmethod
    def bstack1ll1111ll11_opy_(key: str):
        bstack1ll11l11l1l_opy_ = bstack1lll1ll1l1l_opy_.bstack11l1lllll11_opy_(key)
        bstack1lll1ll1l1l_opy_.mark(bstack1ll11l11l1l_opy_+bstack1ll_opy_ (u"ࠦ࠿ࡹࡴࡢࡴࡷࠦῑ"))
        return bstack1ll11l11l1l_opy_
    @staticmethod
    def mark(key: str) -> None:
        try:
            bstack1lllll1lllll_opy_[key] = time.time_ns() / 1000000
        except Exception as e:
            logger.debug(bstack1ll_opy_ (u"ࠧࡋࡲࡳࡱࡵ࠾ࠥࢁࡽࠣῒ").format(e))
    @staticmethod
    def end(label: str, start: str, end: str, status: bool, failure: Optional[str] = None, hook_type: Optional[str] = None, details: Optional[str] = None, command: Optional[str] = None, test_name: Optional[str] = None) -> None:
        try:
            bstack1lll1ll1l1l_opy_.mark(end)
            bstack1lll1ll1l1l_opy_.measure(label, start, end, status, failure, hook_type, details, command, test_name)
        except Exception as e:
            logger.debug(bstack1ll_opy_ (u"ࠨࡅࡳࡴࡲࡶࠥ࡯࡮ࠡ࡭ࡨࡽࠥࡳࡥࡵࡴ࡬ࡧࡸࡀࠠࡼࡿࠥΐ").format(e))
    @staticmethod
    def measure(label: str, start: str, end: str, status: bool, failure: Optional[str], hook_type: Optional[str] = None, details: Optional[str] = None, command: Optional[str] = None, test_name: Optional[str] = None) -> None:
        try:
            if start not in bstack1lllll1lllll_opy_ or end not in bstack1lllll1lllll_opy_:
                logger.debug(bstack1ll_opy_ (u"ࠢࡆࡴࡵࡳࡷࠦࡩ࡯ࠢࡶࡸࡦࡸࡴࠡ࡭ࡨࡽࠥࡽࡩࡵࡪࠣࡺࡦࡲࡵࡦࠢࡾࢁࠥࡵࡲࠡࡧࡱࡨࠥࡱࡥࡺࠢࡺ࡭ࡹ࡮ࠠࡷࡣ࡯ࡹࡪࠦࡻࡾࠤ῔").format(start,end))
                return
            duration: float = bstack1lllll1lllll_opy_[end] - bstack1lllll1lllll_opy_[start]
            bstack1lllll1llll1_opy_ = os.environ.get(bstack1ll_opy_ (u"ࠣࡄࡕࡓ࡜࡙ࡅࡓࡕࡗࡅࡈࡑ࡟ࡃࡋࡑࡅࡗ࡟࡟ࡊࡕࡢࡖ࡚ࡔࡎࡊࡐࡊࠦ῕"), bstack1ll_opy_ (u"ࠤࡩࡥࡱࡹࡥࠣῖ")).lower() == bstack1ll_opy_ (u"ࠥࡸࡷࡻࡥࠣῗ")
            bstack1llllll111l1_opy_: bstack1llllll11l11_opy_ = bstack1llllll11l11_opy_(duration, label, bstack1lllll1lllll_opy_[start], os.getpid(), status, failure, details, os.environ.get(bstack1ll_opy_ (u"ࠦࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡔࡑࡇࡔࡇࡑࡕࡑࡤࡏࡎࡅࡇ࡛ࠦῘ"), 0), command, test_name, hook_type, bstack1lllll1llll1_opy_)
            del bstack1lllll1lllll_opy_[start]
            del bstack1lllll1lllll_opy_[end]
            bstack1lll1ll1l1l_opy_.bstack1llllll11ll1_opy_(bstack1llllll111l1_opy_)
        except Exception as e:
            logger.debug(bstack1ll_opy_ (u"ࠧࡋࡲࡳࡱࡵࠤࡼ࡮ࡩ࡭ࡧࠣࡱࡪࡧࡳࡶࡴ࡬ࡲ࡬ࠦ࡫ࡦࡻࠣࡱࡪࡺࡲࡪࡥࡶ࠾ࠥࢁࡽࠣῙ").format(e))
    @staticmethod
    def bstack1llllll11ll1_opy_(bstack1llllll111l1_opy_):
        os.makedirs(os.path.dirname(bstack1lll11l11l_opy_)) if not os.path.exists(os.path.dirname(bstack1lll11l11l_opy_)) else None
        bstack1lll1ll1l1l_opy_.bstack1llllll111ll_opy_()
        try:
            with lock:
                with open(bstack1lll11l11l_opy_, bstack1ll_opy_ (u"ࠨࡲࠬࠤῚ"), encoding=bstack1ll_opy_ (u"ࠢࡶࡶࡩ࠱࠽ࠨΊ")) as file:
                    try:
                        data = json.load(file)
                    except json.JSONDecodeError:
                        data = []
                    data.append(bstack1llllll111l1_opy_.__dict__)
                    file.seek(0)
                    file.truncate()
                    json.dump(data, file, indent=4)
        except FileNotFoundError as bstack1llllll11l1l_opy_:
            logger.debug(bstack1ll_opy_ (u"ࠣࡈ࡬ࡰࡪࠦ࡮ࡰࡶࠣࡪࡴࡻ࡮ࡥࠢࡾࢁࠧ῜").format(bstack1llllll11l1l_opy_))
            with lock:
                with open(bstack1lll11l11l_opy_, bstack1ll_opy_ (u"ࠤࡺࠦ῝"), encoding=bstack1ll_opy_ (u"ࠥࡹࡹ࡬࠭࠹ࠤ῞")) as file:
                    data = [bstack1llllll111l1_opy_.__dict__]
                    json.dump(data, file, indent=4)
        except Exception as e:
            logger.debug(bstack1ll_opy_ (u"ࠦࡊࡾࡣࡦࡲࡷ࡭ࡴࡴࠠࡸࡪ࡬ࡰࡪࠦ࡫ࡦࡻࠣࡱࡪࡺࡲࡪࡥࡶࠤࡦࡶࡰࡦࡰࡧࠤࢀࢃࠢ῟").format(str(e)))
        finally:
            if os.path.exists(bstack1lll11l11l_opy_+bstack1ll_opy_ (u"ࠧ࠴࡬ࡰࡥ࡮ࠦῠ")):
                os.remove(bstack1lll11l11l_opy_+bstack1ll_opy_ (u"ࠨ࠮࡭ࡱࡦ࡯ࠧῡ"))
    @staticmethod
    def bstack1llllll111ll_opy_():
        attempt = 0
        while (attempt < bstack1llllll1111l_opy_):
            attempt += 1
            if os.path.exists(bstack1lll11l11l_opy_+bstack1ll_opy_ (u"ࠢ࠯࡮ࡲࡧࡰࠨῢ")):
                time.sleep(0.5)
            else:
                break
    @staticmethod
    def bstack11l1lllll11_opy_(label: str) -> str:
        try:
            return bstack1ll_opy_ (u"ࠣࡽࢀ࠾ࢀࢃࠢΰ").format(label,str(uuid.uuid4().hex)[:6])
        except Exception as e:
            logger.debug(bstack1ll_opy_ (u"ࠤࡈࡶࡷࡵࡲ࠻ࠢࡾࢁࠧῤ").format(e))