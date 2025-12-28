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
import os
import threading
from uuid import uuid4
from itertools import zip_longest
from collections import OrderedDict
from robot.libraries.BuiltIn import BuiltIn
from browserstack_sdk.bstack111l11l1ll_opy_ import RobotHandler
from bstack_utils.capture import bstack111l1l1l1l_opy_
from bstack_utils.bstack111l1l1ll1_opy_ import bstack111l1111ll_opy_, bstack111ll1l111_opy_, bstack111ll111l1_opy_
from bstack_utils.bstack111ll1l1l1_opy_ import bstack1l11111lll_opy_
from bstack_utils.bstack111ll111ll_opy_ import bstack1lll1111l_opy_
from bstack_utils.constants import *
from bstack_utils.helper import bstack1l11l11l_opy_, bstack1l11l1111_opy_, Result, \
    error_handler, bstack111l11ll1l_opy_
class bstack_robot_listener:
    ROBOT_LISTENER_API_VERSION = 2
    _lock = threading.Lock()
    store = {
        bstack1ll_opy_ (u"ࠩࡦࡹࡷࡸࡥ࡯ࡶࡢ࡬ࡴࡵ࡫ࡠࡷࡸ࡭ࡩ࠭ྑ"): [],
        bstack1ll_opy_ (u"ࠪ࡫ࡱࡵࡢࡢ࡮ࡢ࡬ࡴࡵ࡫ࡴࠩྒ"): [],
        bstack1ll_opy_ (u"ࠫࡹ࡫ࡳࡵࡡ࡫ࡳࡴࡱࡳࠨྒྷ"): []
    }
    bstack1111lll1l1_opy_ = []
    bstack111l1l111l_opy_ = []
    @staticmethod
    def bstack111l1lll1l_opy_(log):
        if not ((isinstance(log[bstack1ll_opy_ (u"ࠬࡳࡥࡴࡵࡤ࡫ࡪ࠭ྔ")], list) or (isinstance(log[bstack1ll_opy_ (u"࠭࡭ࡦࡵࡶࡥ࡬࡫ࠧྕ")], dict)) and len(log[bstack1ll_opy_ (u"ࠧ࡮ࡧࡶࡷࡦ࡭ࡥࠨྖ")])>0) or (isinstance(log[bstack1ll_opy_ (u"ࠨ࡯ࡨࡷࡸࡧࡧࡦࠩྗ")], str) and log[bstack1ll_opy_ (u"ࠩࡰࡩࡸࡹࡡࡨࡧࠪ྘")].strip())):
            return
        active = bstack1l11111lll_opy_.bstack111l1lllll_opy_()
        log = {
            bstack1ll_opy_ (u"ࠪࡰࡪࡼࡥ࡭ࠩྙ"): log[bstack1ll_opy_ (u"ࠫࡱ࡫ࡶࡦ࡮ࠪྚ")],
            bstack1ll_opy_ (u"ࠬࡺࡩ࡮ࡧࡶࡸࡦࡳࡰࠨྛ"): bstack111l11ll1l_opy_().isoformat() + bstack1ll_opy_ (u"࡚࠭ࠨྜ"),
            bstack1ll_opy_ (u"ࠧ࡮ࡧࡶࡷࡦ࡭ࡥࠨྜྷ"): log[bstack1ll_opy_ (u"ࠨ࡯ࡨࡷࡸࡧࡧࡦࠩྞ")],
        }
        if active:
            if active[bstack1ll_opy_ (u"ࠩࡷࡽࡵ࡫ࠧྟ")] == bstack1ll_opy_ (u"ࠪ࡬ࡴࡵ࡫ࠨྠ"):
                log[bstack1ll_opy_ (u"ࠫ࡭ࡵ࡯࡬ࡡࡵࡹࡳࡥࡵࡶ࡫ࡧࠫྡ")] = active[bstack1ll_opy_ (u"ࠬ࡮࡯ࡰ࡭ࡢࡶࡺࡴ࡟ࡶࡷ࡬ࡨࠬྡྷ")]
            elif active[bstack1ll_opy_ (u"࠭ࡴࡺࡲࡨࠫྣ")] == bstack1ll_opy_ (u"ࠧࡵࡧࡶࡸࠬྤ"):
                log[bstack1ll_opy_ (u"ࠨࡶࡨࡷࡹࡥࡲࡶࡰࡢࡹࡺ࡯ࡤࠨྥ")] = active[bstack1ll_opy_ (u"ࠩࡷࡩࡸࡺ࡟ࡳࡷࡱࡣࡺࡻࡩࡥࠩྦ")]
        bstack1lll1111l_opy_.bstack11ll1111l_opy_([log])
    def __init__(self):
        self.messages = bstack1111l11ll1_opy_()
        self._1111l1llll_opy_ = None
        self._1111lll11l_opy_ = None
        self._111l11111l_opy_ = OrderedDict()
        self.bstack111l1ll111_opy_ = bstack111l1l1l1l_opy_(self.bstack111l1lll1l_opy_)
    @error_handler(class_method=True)
    def start_suite(self, name, attrs):
        self.messages.bstack1111ll111l_opy_()
        if not self._111l11111l_opy_.get(attrs.get(bstack1ll_opy_ (u"ࠪ࡭ࡩ࠭ྦྷ")), None):
            self._111l11111l_opy_[attrs.get(bstack1ll_opy_ (u"ࠫ࡮ࡪࠧྨ"))] = {}
        bstack111l111ll1_opy_ = bstack111ll111l1_opy_(
                bstack1111lllll1_opy_=attrs.get(bstack1ll_opy_ (u"ࠬ࡯ࡤࠨྩ")),
                name=name,
                started_at=bstack1l11l1111_opy_(),
                file_path=os.path.relpath(attrs[bstack1ll_opy_ (u"࠭ࡳࡰࡷࡵࡧࡪ࠭ྪ")], start=os.getcwd()) if attrs.get(bstack1ll_opy_ (u"ࠧࡴࡱࡸࡶࡨ࡫ࠧྫ")) != bstack1ll_opy_ (u"ࠨࠩྫྷ") else bstack1ll_opy_ (u"ࠩࠪྭ"),
                framework=bstack1ll_opy_ (u"ࠪࡖࡴࡨ࡯ࡵࠩྮ")
            )
        threading.current_thread().current_suite_id = attrs.get(bstack1ll_opy_ (u"ࠫ࡮ࡪࠧྯ"), None)
        self._111l11111l_opy_[attrs.get(bstack1ll_opy_ (u"ࠬ࡯ࡤࠨྰ"))][bstack1ll_opy_ (u"࠭ࡴࡦࡵࡷࡣࡩࡧࡴࡢࠩྱ")] = bstack111l111ll1_opy_
    @error_handler(class_method=True)
    def end_suite(self, name, attrs):
        messages = self.messages.bstack111l111l11_opy_()
        self._1111l1ll11_opy_(messages)
        with self._lock:
            for bstack111l11llll_opy_ in self.bstack1111lll1l1_opy_:
                bstack111l11llll_opy_[bstack1ll_opy_ (u"ࠧࡵࡧࡶࡸࡤࡸࡵ࡯ࠩྲ")][bstack1ll_opy_ (u"ࠨࡪࡲࡳࡰࡹࠧླ")].extend(self.store[bstack1ll_opy_ (u"ࠩࡪࡰࡴࡨࡡ࡭ࡡ࡫ࡳࡴࡱࡳࠨྴ")])
                bstack1lll1111l_opy_.bstack1ll1ll111l_opy_(bstack111l11llll_opy_)
            self.bstack1111lll1l1_opy_ = []
            self.store[bstack1ll_opy_ (u"ࠪ࡫ࡱࡵࡢࡢ࡮ࡢ࡬ࡴࡵ࡫ࡴࠩྵ")] = []
    @error_handler(class_method=True)
    def start_test(self, name, attrs):
        self.bstack111l1ll111_opy_.start()
        if not self._111l11111l_opy_.get(attrs.get(bstack1ll_opy_ (u"ࠫ࡮ࡪࠧྶ")), None):
            self._111l11111l_opy_[attrs.get(bstack1ll_opy_ (u"ࠬ࡯ࡤࠨྷ"))] = {}
        driver = bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"࠭ࡢࡴࡶࡤࡧࡰ࡙ࡥࡴࡵ࡬ࡳࡳࡊࡲࡪࡸࡨࡶࠬྸ"), None)
        bstack111l1l1ll1_opy_ = bstack111ll111l1_opy_(
            bstack1111lllll1_opy_=attrs.get(bstack1ll_opy_ (u"ࠧࡪࡦࠪྐྵ")),
            name=name,
            started_at=bstack1l11l1111_opy_(),
            file_path=os.path.relpath(attrs[bstack1ll_opy_ (u"ࠨࡵࡲࡹࡷࡩࡥࠨྺ")], start=os.getcwd()),
            scope=RobotHandler.bstack111l111111_opy_(attrs.get(bstack1ll_opy_ (u"ࠩࡶࡳࡺࡸࡣࡦࠩྻ"), None)),
            framework=bstack1ll_opy_ (u"ࠪࡖࡴࡨ࡯ࡵࠩྼ"),
            tags=attrs[bstack1ll_opy_ (u"ࠫࡹࡧࡧࡴࠩ྽")],
            hooks=self.store[bstack1ll_opy_ (u"ࠬ࡭࡬ࡰࡤࡤࡰࡤ࡮࡯ࡰ࡭ࡶࠫ྾")],
            bstack111l1ll1ll_opy_=bstack1lll1111l_opy_.bstack111ll1111l_opy_(driver) if driver and driver.session_id else {},
            meta={},
            code=bstack1ll_opy_ (u"ࠨࡻࡾࠢ࡟ࡲࠥࢁࡽࠣ྿").format(bstack1ll_opy_ (u"ࠢࠡࠤ࿀").join(attrs[bstack1ll_opy_ (u"ࠨࡶࡤ࡫ࡸ࠭࿁")]), name) if attrs[bstack1ll_opy_ (u"ࠩࡷࡥ࡬ࡹࠧ࿂")] else name
        )
        self._111l11111l_opy_[attrs.get(bstack1ll_opy_ (u"ࠪ࡭ࡩ࠭࿃"))][bstack1ll_opy_ (u"ࠫࡹ࡫ࡳࡵࡡࡧࡥࡹࡧࠧ࿄")] = bstack111l1l1ll1_opy_
        threading.current_thread().current_test_uuid = bstack111l1l1ll1_opy_.bstack1111l1l1l1_opy_()
        threading.current_thread().current_test_id = attrs.get(bstack1ll_opy_ (u"ࠬ࡯ࡤࠨ࿅"), None)
        self.bstack111ll11ll1_opy_(bstack1ll_opy_ (u"࠭ࡔࡦࡵࡷࡖࡺࡴࡓࡵࡣࡵࡸࡪࡪ࿆ࠧ"), bstack111l1l1ll1_opy_)
    @error_handler(class_method=True)
    def end_test(self, name, attrs):
        self.bstack111l1ll111_opy_.reset()
        bstack1111ll1l1l_opy_ = bstack1111l1lll1_opy_.get(attrs.get(bstack1ll_opy_ (u"ࠧࡴࡶࡤࡸࡺࡹࠧ࿇")), bstack1ll_opy_ (u"ࠨࡵ࡮࡭ࡵࡶࡥࡥࠩ࿈"))
        self._111l11111l_opy_[attrs.get(bstack1ll_opy_ (u"ࠩ࡬ࡨࠬ࿉"))][bstack1ll_opy_ (u"ࠪࡸࡪࡹࡴࡠࡦࡤࡸࡦ࠭࿊")].stop(time=bstack1l11l1111_opy_(), duration=int(attrs.get(bstack1ll_opy_ (u"ࠫࡪࡲࡡࡱࡵࡨࡨࡹ࡯࡭ࡦࠩ࿋"), bstack1ll_opy_ (u"ࠬ࠶ࠧ࿌"))), result=Result(result=bstack1111ll1l1l_opy_, exception=attrs.get(bstack1ll_opy_ (u"࠭࡭ࡦࡵࡶࡥ࡬࡫ࠧ࿍")), bstack111l1lll11_opy_=[attrs.get(bstack1ll_opy_ (u"ࠧ࡮ࡧࡶࡷࡦ࡭ࡥࠨ࿎"))]))
        self.bstack111ll11ll1_opy_(bstack1ll_opy_ (u"ࠨࡖࡨࡷࡹࡘࡵ࡯ࡈ࡬ࡲ࡮ࡹࡨࡦࡦࠪ࿏"), self._111l11111l_opy_[attrs.get(bstack1ll_opy_ (u"ࠩ࡬ࡨࠬ࿐"))][bstack1ll_opy_ (u"ࠪࡸࡪࡹࡴࡠࡦࡤࡸࡦ࠭࿑")], True)
        with self._lock:
            self.store[bstack1ll_opy_ (u"ࠫࡹ࡫ࡳࡵࡡ࡫ࡳࡴࡱࡳࠨ࿒")] = []
        threading.current_thread().current_test_uuid = None
        threading.current_thread().current_test_id = None
    @error_handler(class_method=True)
    def start_keyword(self, name, attrs):
        self.messages.bstack1111ll111l_opy_()
        current_test_id = bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠬࡩࡵࡳࡴࡨࡲࡹࡥࡴࡦࡵࡷࡣ࡮ࡪࠧ࿓"), None)
        bstack1111l11l1l_opy_ = current_test_id if bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"࠭ࡣࡶࡴࡵࡩࡳࡺ࡟ࡵࡧࡶࡸࡤ࡯ࡤࠨ࿔"), None) else bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠧࡤࡷࡵࡶࡪࡴࡴࡠࡵࡸ࡭ࡹ࡫࡟ࡪࡦࠪ࿕"), None)
        if attrs.get(bstack1ll_opy_ (u"ࠨࡶࡼࡴࡪ࠭࿖"), bstack1ll_opy_ (u"ࠩࠪ࿗")).lower() in [bstack1ll_opy_ (u"ࠪࡷࡪࡺࡵࡱࠩ࿘"), bstack1ll_opy_ (u"ࠫࡹ࡫ࡡࡳࡦࡲࡻࡳ࠭࿙")]:
            hook_type = bstack1111l1ll1l_opy_(attrs.get(bstack1ll_opy_ (u"ࠬࡺࡹࡱࡧࠪ࿚")), bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"࠭ࡣࡶࡴࡵࡩࡳࡺ࡟ࡵࡧࡶࡸࡤࡻࡵࡪࡦࠪ࿛"), None))
            hook_name = bstack1ll_opy_ (u"ࠧࡼࡿࠪ࿜").format(attrs.get(bstack1ll_opy_ (u"ࠨ࡭ࡺࡲࡦࡳࡥࠨ࿝"), bstack1ll_opy_ (u"ࠩࠪ࿞")))
            if hook_type in [bstack1ll_opy_ (u"ࠪࡆࡊࡌࡏࡓࡇࡢࡅࡑࡒࠧ࿟"), bstack1ll_opy_ (u"ࠫࡆࡌࡔࡆࡔࡢࡅࡑࡒࠧ࿠")]:
                hook_name = bstack1ll_opy_ (u"ࠬࡡࡻࡾ࡟ࠣࡿࢂ࠭࿡").format(bstack1111ll1ll1_opy_.get(hook_type), attrs.get(bstack1ll_opy_ (u"࠭࡫ࡸࡰࡤࡱࡪ࠭࿢"), bstack1ll_opy_ (u"ࠧࠨ࿣")))
            bstack111l11l11l_opy_ = bstack111ll1l111_opy_(
                bstack1111lllll1_opy_=bstack1111l11l1l_opy_ + bstack1ll_opy_ (u"ࠨ࠯ࠪ࿤") + attrs.get(bstack1ll_opy_ (u"ࠩࡷࡽࡵ࡫ࠧ࿥"), bstack1ll_opy_ (u"ࠪࠫ࿦")).lower(),
                name=hook_name,
                started_at=bstack1l11l1111_opy_(),
                file_path=os.path.relpath(attrs.get(bstack1ll_opy_ (u"ࠫࡸࡵࡵࡳࡥࡨࠫ࿧")), start=os.getcwd()),
                framework=bstack1ll_opy_ (u"ࠬࡘ࡯ࡣࡱࡷࠫ࿨"),
                tags=attrs[bstack1ll_opy_ (u"࠭ࡴࡢࡩࡶࠫ࿩")],
                scope=RobotHandler.bstack111l111111_opy_(attrs.get(bstack1ll_opy_ (u"ࠧࡴࡱࡸࡶࡨ࡫ࠧ࿪"), None)),
                hook_type=hook_type,
                meta={}
            )
            threading.current_thread().current_hook_uuid = bstack111l11l11l_opy_.bstack1111l1l1l1_opy_()
            threading.current_thread().current_hook_id = bstack1111l11l1l_opy_ + bstack1ll_opy_ (u"ࠨ࠯ࠪ࿫") + attrs.get(bstack1ll_opy_ (u"ࠩࡷࡽࡵ࡫ࠧ࿬"), bstack1ll_opy_ (u"ࠪࠫ࿭")).lower()
            with self._lock:
                self.store[bstack1ll_opy_ (u"ࠫࡨࡻࡲࡳࡧࡱࡸࡤ࡮࡯ࡰ࡭ࡢࡹࡺ࡯ࡤࠨ࿮")] = [bstack111l11l11l_opy_.bstack1111l1l1l1_opy_()]
                if bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠬࡩࡵࡳࡴࡨࡲࡹࡥࡴࡦࡵࡷࡣࡺࡻࡩࡥࠩ࿯"), None):
                    self.store[bstack1ll_opy_ (u"࠭ࡴࡦࡵࡷࡣ࡭ࡵ࡯࡬ࡵࠪ࿰")].append(bstack111l11l11l_opy_.bstack1111l1l1l1_opy_())
                else:
                    self.store[bstack1ll_opy_ (u"ࠧࡨ࡮ࡲࡦࡦࡲ࡟ࡩࡱࡲ࡯ࡸ࠭࿱")].append(bstack111l11l11l_opy_.bstack1111l1l1l1_opy_())
            if bstack1111l11l1l_opy_:
                self._111l11111l_opy_[bstack1111l11l1l_opy_ + bstack1ll_opy_ (u"ࠨ࠯ࠪ࿲") + attrs.get(bstack1ll_opy_ (u"ࠩࡷࡽࡵ࡫ࠧ࿳"), bstack1ll_opy_ (u"ࠪࠫ࿴")).lower()] = { bstack1ll_opy_ (u"ࠫࡹ࡫ࡳࡵࡡࡧࡥࡹࡧࠧ࿵"): bstack111l11l11l_opy_ }
            bstack1lll1111l_opy_.bstack111ll11ll1_opy_(bstack1ll_opy_ (u"ࠬࡎ࡯ࡰ࡭ࡕࡹࡳ࡙ࡴࡢࡴࡷࡩࡩ࠭࿶"), bstack111l11l11l_opy_)
        else:
            bstack111l1l1lll_opy_ = {
                bstack1ll_opy_ (u"࠭ࡩࡥࠩ࿷"): uuid4().__str__(),
                bstack1ll_opy_ (u"ࠧࡵࡧࡻࡸࠬ࿸"): bstack1ll_opy_ (u"ࠨࡽࢀࠤࢀࢃࠧ࿹").format(attrs.get(bstack1ll_opy_ (u"ࠩ࡮ࡻࡳࡧ࡭ࡦࠩ࿺")), attrs.get(bstack1ll_opy_ (u"ࠪࡥࡷ࡭ࡳࠨ࿻"), bstack1ll_opy_ (u"ࠫࠬ࿼"))) if attrs.get(bstack1ll_opy_ (u"ࠬࡧࡲࡨࡵࠪ࿽"), []) else attrs.get(bstack1ll_opy_ (u"࠭࡫ࡸࡰࡤࡱࡪ࠭࿾")),
                bstack1ll_opy_ (u"ࠧࡴࡶࡨࡴࡤࡧࡲࡨࡷࡰࡩࡳࡺࠧ࿿"): attrs.get(bstack1ll_opy_ (u"ࠨࡣࡵ࡫ࡸ࠭က"), []),
                bstack1ll_opy_ (u"ࠩࡶࡸࡦࡸࡴࡦࡦࡢࡥࡹ࠭ခ"): bstack1l11l1111_opy_(),
                bstack1ll_opy_ (u"ࠪࡶࡪࡹࡵ࡭ࡶࠪဂ"): bstack1ll_opy_ (u"ࠫࡵ࡫࡮ࡥ࡫ࡱ࡫ࠬဃ"),
                bstack1ll_opy_ (u"ࠬࡪࡥࡴࡥࡵ࡭ࡵࡺࡩࡰࡰࠪင"): attrs.get(bstack1ll_opy_ (u"࠭ࡤࡰࡥࠪစ"), bstack1ll_opy_ (u"ࠧࠨဆ"))
            }
            if attrs.get(bstack1ll_opy_ (u"ࠨ࡮࡬ࡦࡳࡧ࡭ࡦࠩဇ"), bstack1ll_opy_ (u"ࠩࠪဈ")) != bstack1ll_opy_ (u"ࠪࠫဉ"):
                bstack111l1l1lll_opy_[bstack1ll_opy_ (u"ࠫࡰ࡫ࡹࡸࡱࡵࡨࠬည")] = attrs.get(bstack1ll_opy_ (u"ࠬࡲࡩࡣࡰࡤࡱࡪ࠭ဋ"))
            if not self.bstack111l1l111l_opy_:
                self._111l11111l_opy_[self._1111llllll_opy_()][bstack1ll_opy_ (u"࠭ࡴࡦࡵࡷࡣࡩࡧࡴࡢࠩဌ")].add_step(bstack111l1l1lll_opy_)
                threading.current_thread().current_step_uuid = bstack111l1l1lll_opy_[bstack1ll_opy_ (u"ࠧࡪࡦࠪဍ")]
            self.bstack111l1l111l_opy_.append(bstack111l1l1lll_opy_)
    @error_handler(class_method=True)
    def end_keyword(self, name, attrs):
        messages = self.messages.bstack111l111l11_opy_()
        self._1111l1ll11_opy_(messages)
        current_test_id = bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠨࡥࡸࡶࡷ࡫࡮ࡵࡡࡷࡩࡸࡺ࡟ࡪࡦࠪဎ"), None)
        bstack1111l11l1l_opy_ = current_test_id if current_test_id else bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠩࡦࡹࡷࡸࡥ࡯ࡶࡢࡷࡺ࡯ࡴࡦࡡ࡬ࡨࠬဏ"), None)
        bstack1111ll11ll_opy_ = bstack1111l1lll1_opy_.get(attrs.get(bstack1ll_opy_ (u"ࠪࡷࡹࡧࡴࡶࡵࠪတ")), bstack1ll_opy_ (u"ࠫࡸࡱࡩࡱࡲࡨࡨࠬထ"))
        bstack111l1111l1_opy_ = attrs.get(bstack1ll_opy_ (u"ࠬࡳࡥࡴࡵࡤ࡫ࡪ࠭ဒ"))
        if bstack1111ll11ll_opy_ != bstack1ll_opy_ (u"࠭ࡳ࡬࡫ࡳࡴࡪࡪࠧဓ") and not attrs.get(bstack1ll_opy_ (u"ࠧ࡮ࡧࡶࡷࡦ࡭ࡥࠨန")) and self._1111l1llll_opy_:
            bstack111l1111l1_opy_ = self._1111l1llll_opy_
        bstack111ll1l11l_opy_ = Result(result=bstack1111ll11ll_opy_, exception=bstack111l1111l1_opy_, bstack111l1lll11_opy_=[bstack111l1111l1_opy_])
        if attrs.get(bstack1ll_opy_ (u"ࠨࡶࡼࡴࡪ࠭ပ"), bstack1ll_opy_ (u"ࠩࠪဖ")).lower() in [bstack1ll_opy_ (u"ࠪࡷࡪࡺࡵࡱࠩဗ"), bstack1ll_opy_ (u"ࠫࡹ࡫ࡡࡳࡦࡲࡻࡳ࠭ဘ")]:
            bstack1111l11l1l_opy_ = current_test_id if current_test_id else bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠬࡩࡵࡳࡴࡨࡲࡹࡥࡳࡶ࡫ࡷࡩࡤ࡯ࡤࠨမ"), None)
            if bstack1111l11l1l_opy_:
                bstack111l1llll1_opy_ = bstack1111l11l1l_opy_ + bstack1ll_opy_ (u"ࠨ࠭ࠣယ") + attrs.get(bstack1ll_opy_ (u"ࠧࡵࡻࡳࡩࠬရ"), bstack1ll_opy_ (u"ࠨࠩလ")).lower()
                self._111l11111l_opy_[bstack111l1llll1_opy_][bstack1ll_opy_ (u"ࠩࡷࡩࡸࡺ࡟ࡥࡣࡷࡥࠬဝ")].stop(time=bstack1l11l1111_opy_(), duration=int(attrs.get(bstack1ll_opy_ (u"ࠪࡩࡱࡧࡰࡴࡧࡧࡸ࡮ࡳࡥࠨသ"), bstack1ll_opy_ (u"ࠫ࠵࠭ဟ"))), result=bstack111ll1l11l_opy_)
                bstack1lll1111l_opy_.bstack111ll11ll1_opy_(bstack1ll_opy_ (u"ࠬࡎ࡯ࡰ࡭ࡕࡹࡳࡌࡩ࡯࡫ࡶ࡬ࡪࡪࠧဠ"), self._111l11111l_opy_[bstack111l1llll1_opy_][bstack1ll_opy_ (u"࠭ࡴࡦࡵࡷࡣࡩࡧࡴࡢࠩအ")])
        else:
            bstack1111l11l1l_opy_ = current_test_id if current_test_id else bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠧࡤࡷࡵࡶࡪࡴࡴࡠࡪࡲࡳࡰࡥࡩࡥࠩဢ"), None)
            if bstack1111l11l1l_opy_ and len(self.bstack111l1l111l_opy_) == 1:
                current_step_uuid = bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠨࡥࡸࡶࡷ࡫࡮ࡵࡡࡶࡸࡪࡶ࡟ࡶࡷ࡬ࡨࠬဣ"), None)
                self._111l11111l_opy_[bstack1111l11l1l_opy_][bstack1ll_opy_ (u"ࠩࡷࡩࡸࡺ࡟ࡥࡣࡷࡥࠬဤ")].bstack111ll1l1ll_opy_(current_step_uuid, duration=int(attrs.get(bstack1ll_opy_ (u"ࠪࡩࡱࡧࡰࡴࡧࡧࡸ࡮ࡳࡥࠨဥ"), bstack1ll_opy_ (u"ࠫ࠵࠭ဦ"))), result=bstack111ll1l11l_opy_)
            else:
                self.bstack111l1l11ll_opy_(attrs)
            self.bstack111l1l111l_opy_.pop()
    def log_message(self, message):
        try:
            if message.get(bstack1ll_opy_ (u"ࠬ࡮ࡴ࡮࡮ࠪဧ"), bstack1ll_opy_ (u"࠭࡮ࡰࠩဨ")) == bstack1ll_opy_ (u"ࠧࡺࡧࡶࠫဩ"):
                return
            self.messages.push(message)
            logs = []
            if bstack1l11111lll_opy_.bstack111l1lllll_opy_():
                logs.append({
                    bstack1ll_opy_ (u"ࠨࡶ࡬ࡱࡪࡹࡴࡢ࡯ࡳࠫဪ"): bstack1l11l1111_opy_(),
                    bstack1ll_opy_ (u"ࠩࡰࡩࡸࡹࡡࡨࡧࠪါ"): message.get(bstack1ll_opy_ (u"ࠪࡱࡪࡹࡳࡢࡩࡨࠫာ")),
                    bstack1ll_opy_ (u"ࠫࡱ࡫ࡶࡦ࡮ࠪိ"): message.get(bstack1ll_opy_ (u"ࠬࡲࡥࡷࡧ࡯ࠫီ")),
                    **bstack1l11111lll_opy_.bstack111l1lllll_opy_()
                })
                if len(logs) > 0:
                    bstack1lll1111l_opy_.bstack11ll1111l_opy_(logs)
        except Exception as err:
            pass
    def close(self):
        bstack1lll1111l_opy_.bstack1111lll111_opy_()
    def bstack111l1l11ll_opy_(self, bstack111l1l11l1_opy_):
        if not bstack1l11111lll_opy_.bstack111l1lllll_opy_():
            return
        kwname = bstack1ll_opy_ (u"࠭ࡻࡾࠢࡾࢁࠬု").format(bstack111l1l11l1_opy_.get(bstack1ll_opy_ (u"ࠧ࡬ࡹࡱࡥࡲ࡫ࠧူ")), bstack111l1l11l1_opy_.get(bstack1ll_opy_ (u"ࠨࡣࡵ࡫ࡸ࠭ေ"), bstack1ll_opy_ (u"ࠩࠪဲ"))) if bstack111l1l11l1_opy_.get(bstack1ll_opy_ (u"ࠪࡥࡷ࡭ࡳࠨဳ"), []) else bstack111l1l11l1_opy_.get(bstack1ll_opy_ (u"ࠫࡰࡽ࡮ࡢ࡯ࡨࠫဴ"))
        error_message = bstack1ll_opy_ (u"ࠧࡱࡷ࡯ࡣࡰࡩ࠿ࠦ࡜ࠣࡽ࠳ࢁࡡࠨࠠࡽࠢࡶࡸࡦࡺࡵࡴ࠼ࠣࡠࠧࢁ࠱ࡾ࡞ࠥࠤࢁࠦࡥࡹࡥࡨࡴࡹ࡯࡯࡯࠼ࠣࡠࠧࢁ࠲ࡾ࡞ࠥࠦဵ").format(kwname, bstack111l1l11l1_opy_.get(bstack1ll_opy_ (u"࠭ࡳࡵࡣࡷࡹࡸ࠭ံ")), str(bstack111l1l11l1_opy_.get(bstack1ll_opy_ (u"ࠧ࡮ࡧࡶࡷࡦ࡭ࡥࠨ့"))))
        bstack111l111lll_opy_ = bstack1ll_opy_ (u"ࠣ࡭ࡺࡲࡦࡳࡥ࠻ࠢ࡟ࠦࢀ࠶ࡽ࡝ࠤࠣࢀࠥࡹࡴࡢࡶࡸࡷ࠿ࠦ࡜ࠣࡽ࠴ࢁࡡࠨࠢး").format(kwname, bstack111l1l11l1_opy_.get(bstack1ll_opy_ (u"ࠩࡶࡸࡦࡺࡵࡴ္ࠩ")))
        bstack1111ll11l1_opy_ = error_message if bstack111l1l11l1_opy_.get(bstack1ll_opy_ (u"ࠪࡱࡪࡹࡳࡢࡩࡨ်ࠫ")) else bstack111l111lll_opy_
        bstack1111lll1ll_opy_ = {
            bstack1ll_opy_ (u"ࠫࡹ࡯࡭ࡦࡵࡷࡥࡲࡶࠧျ"): self.bstack111l1l111l_opy_[-1].get(bstack1ll_opy_ (u"ࠬࡹࡴࡢࡴࡷࡩࡩࡥࡡࡵࠩြ"), bstack1l11l1111_opy_()),
            bstack1ll_opy_ (u"࠭࡭ࡦࡵࡶࡥ࡬࡫ࠧွ"): bstack1111ll11l1_opy_,
            bstack1ll_opy_ (u"ࠧ࡭ࡧࡹࡩࡱ࠭ှ"): bstack1ll_opy_ (u"ࠨࡇࡕࡖࡔࡘࠧဿ") if bstack111l1l11l1_opy_.get(bstack1ll_opy_ (u"ࠩࡶࡸࡦࡺࡵࡴࠩ၀")) == bstack1ll_opy_ (u"ࠪࡊࡆࡏࡌࠨ၁") else bstack1ll_opy_ (u"ࠫࡎࡔࡆࡐࠩ၂"),
            **bstack1l11111lll_opy_.bstack111l1lllll_opy_()
        }
        bstack1lll1111l_opy_.bstack11ll1111l_opy_([bstack1111lll1ll_opy_])
    def _1111llllll_opy_(self):
        for bstack1111lllll1_opy_ in reversed(self._111l11111l_opy_):
            bstack111l11l1l1_opy_ = bstack1111lllll1_opy_
            data = self._111l11111l_opy_[bstack1111lllll1_opy_][bstack1ll_opy_ (u"ࠬࡺࡥࡴࡶࡢࡨࡦࡺࡡࠨ၃")]
            if isinstance(data, bstack111ll1l111_opy_):
                if not bstack1ll_opy_ (u"࠭ࡅࡂࡅࡋࠫ၄") in data.bstack111l11ll11_opy_():
                    return bstack111l11l1l1_opy_
            else:
                return bstack111l11l1l1_opy_
    def _1111l1ll11_opy_(self, messages):
        try:
            bstack1111ll1l11_opy_ = BuiltIn().get_variable_value(bstack1ll_opy_ (u"ࠢࠥࡽࡏࡓࡌࠦࡌࡆࡘࡈࡐࢂࠨ၅")) in (bstack111l11l111_opy_.DEBUG, bstack111l11l111_opy_.TRACE)
            for message, bstack1111llll11_opy_ in zip_longest(messages, messages[1:]):
                name = message.get(bstack1ll_opy_ (u"ࠨ࡯ࡨࡷࡸࡧࡧࡦࠩ၆"))
                level = message.get(bstack1ll_opy_ (u"ࠩ࡯ࡩࡻ࡫࡬ࠨ၇"))
                if level == bstack111l11l111_opy_.FAIL:
                    self._1111l1llll_opy_ = name or self._1111l1llll_opy_
                    self._1111lll11l_opy_ = bstack1111llll11_opy_.get(bstack1ll_opy_ (u"ࠥࡱࡪࡹࡳࡢࡩࡨࠦ၈")) if bstack1111ll1l11_opy_ and bstack1111llll11_opy_ else self._1111lll11l_opy_
        except:
            pass
    @classmethod
    def bstack111ll11ll1_opy_(self, event: str, bstack1111l1l11l_opy_: bstack111l1111ll_opy_, bstack1111l1l1ll_opy_=False):
        if event == bstack1ll_opy_ (u"࡙ࠫ࡫ࡳࡵࡔࡸࡲࡋ࡯࡮ࡪࡵ࡫ࡩࡩ࠭၉"):
            bstack1111l1l11l_opy_.set(hooks=self.store[bstack1ll_opy_ (u"ࠬࡺࡥࡴࡶࡢ࡬ࡴࡵ࡫ࡴࠩ၊")])
        if event == bstack1ll_opy_ (u"࠭ࡔࡦࡵࡷࡖࡺࡴࡓ࡬࡫ࡳࡴࡪࡪࠧ။"):
            event = bstack1ll_opy_ (u"ࠧࡕࡧࡶࡸࡗࡻ࡮ࡇ࡫ࡱ࡭ࡸ࡮ࡥࡥࠩ၌")
        if bstack1111l1l1ll_opy_:
            bstack1111ll1111_opy_ = {
                bstack1ll_opy_ (u"ࠨࡧࡹࡩࡳࡺ࡟ࡵࡻࡳࡩࠬ၍"): event,
                bstack1111l1l11l_opy_.bstack111l1l1111_opy_(): bstack1111l1l11l_opy_.bstack111l111l1l_opy_(event)
            }
            with self._lock:
                self.bstack1111lll1l1_opy_.append(bstack1111ll1111_opy_)
        else:
            bstack1lll1111l_opy_.bstack111ll11ll1_opy_(event, bstack1111l1l11l_opy_)
class bstack1111l11ll1_opy_:
    def __init__(self):
        self._1111llll1l_opy_ = []
    def bstack1111ll111l_opy_(self):
        self._1111llll1l_opy_.append([])
    def bstack111l111l11_opy_(self):
        return self._1111llll1l_opy_.pop() if self._1111llll1l_opy_ else list()
    def push(self, message):
        self._1111llll1l_opy_[-1].append(message) if self._1111llll1l_opy_ else self._1111llll1l_opy_.append([message])
class bstack111l11l111_opy_:
    FAIL = bstack1ll_opy_ (u"ࠩࡉࡅࡎࡒࠧ၎")
    ERROR = bstack1ll_opy_ (u"ࠪࡉࡗࡘࡏࡓࠩ၏")
    WARNING = bstack1ll_opy_ (u"ࠫ࡜ࡇࡒࡏࠩၐ")
    bstack111l11lll1_opy_ = bstack1ll_opy_ (u"ࠬࡏࡎࡇࡑࠪၑ")
    DEBUG = bstack1ll_opy_ (u"࠭ࡄࡆࡄࡘࡋࠬၒ")
    TRACE = bstack1ll_opy_ (u"ࠧࡕࡔࡄࡇࡊ࠭ၓ")
    bstack1111l11lll_opy_ = [FAIL, ERROR]
def bstack1111l1l111_opy_(bstack1111ll1lll_opy_):
    if not bstack1111ll1lll_opy_:
        return None
    if bstack1111ll1lll_opy_.get(bstack1ll_opy_ (u"ࠨࡶࡨࡷࡹࡥࡤࡢࡶࡤࠫၔ"), None):
        return getattr(bstack1111ll1lll_opy_[bstack1ll_opy_ (u"ࠩࡷࡩࡸࡺ࡟ࡥࡣࡷࡥࠬၕ")], bstack1ll_opy_ (u"ࠪࡹࡺ࡯ࡤࠨၖ"), None)
    return bstack1111ll1lll_opy_.get(bstack1ll_opy_ (u"ࠫࡺࡻࡩࡥࠩၗ"), None)
def bstack1111l1ll1l_opy_(hook_type, current_test_uuid):
    if hook_type.lower() not in [bstack1ll_opy_ (u"ࠬࡹࡥࡵࡷࡳࠫၘ"), bstack1ll_opy_ (u"࠭ࡴࡦࡣࡵࡨࡴࡽ࡮ࠨၙ")]:
        return
    if hook_type.lower() == bstack1ll_opy_ (u"ࠧࡴࡧࡷࡹࡵ࠭ၚ"):
        if current_test_uuid is None:
            return bstack1ll_opy_ (u"ࠨࡄࡈࡊࡔࡘࡅࡠࡃࡏࡐࠬၛ")
        else:
            return bstack1ll_opy_ (u"ࠩࡅࡉࡋࡕࡒࡆࡡࡈࡅࡈࡎࠧၜ")
    elif hook_type.lower() == bstack1ll_opy_ (u"ࠪࡸࡪࡧࡲࡥࡱࡺࡲࠬၝ"):
        if current_test_uuid is None:
            return bstack1ll_opy_ (u"ࠫࡆࡌࡔࡆࡔࡢࡅࡑࡒࠧၞ")
        else:
            return bstack1ll_opy_ (u"ࠬࡇࡆࡕࡇࡕࡣࡊࡇࡃࡉࠩၟ")