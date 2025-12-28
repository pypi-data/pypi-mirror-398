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
import os
import logging
from uuid import uuid4
from bstack_utils.bstack111l1l1ll1_opy_ import bstack111ll1l111_opy_, bstack111ll111l1_opy_
from bstack_utils.bstack111ll1l1l1_opy_ import bstack1l11111lll_opy_
from bstack_utils.helper import bstack1l11l11l_opy_, bstack1l11l1111_opy_, Result
from bstack_utils.bstack111ll111ll_opy_ import bstack1lll1111l_opy_
from bstack_utils.capture import bstack111l1l1l1l_opy_
from bstack_utils.constants import *
logger = logging.getLogger(__name__)
class bstack1111111l_opy_:
    def __init__(self):
        self.bstack111l1ll111_opy_ = bstack111l1l1l1l_opy_(self.bstack111l1lll1l_opy_)
        self.tests = {}
    @staticmethod
    def bstack111l1lll1l_opy_(log):
        if not (log[bstack1ll_opy_ (u"ࠩࡰࡩࡸࡹࡡࡨࡧࠪང")] and log[bstack1ll_opy_ (u"ࠪࡱࡪࡹࡳࡢࡩࡨࠫཅ")].strip()):
            return
        active = bstack1l11111lll_opy_.bstack111l1lllll_opy_()
        log = {
            bstack1ll_opy_ (u"ࠫࡱ࡫ࡶࡦ࡮ࠪཆ"): log[bstack1ll_opy_ (u"ࠬࡲࡥࡷࡧ࡯ࠫཇ")],
            bstack1ll_opy_ (u"࠭ࡴࡪ࡯ࡨࡷࡹࡧ࡭ࡱࠩ཈"): bstack1l11l1111_opy_(),
            bstack1ll_opy_ (u"ࠧ࡮ࡧࡶࡷࡦ࡭ࡥࠨཉ"): log[bstack1ll_opy_ (u"ࠨ࡯ࡨࡷࡸࡧࡧࡦࠩཊ")],
        }
        if active:
            if active[bstack1ll_opy_ (u"ࠩࡷࡽࡵ࡫ࠧཋ")] == bstack1ll_opy_ (u"ࠪ࡬ࡴࡵ࡫ࠨཌ"):
                log[bstack1ll_opy_ (u"ࠫ࡭ࡵ࡯࡬ࡡࡵࡹࡳࡥࡵࡶ࡫ࡧࠫཌྷ")] = active[bstack1ll_opy_ (u"ࠬ࡮࡯ࡰ࡭ࡢࡶࡺࡴ࡟ࡶࡷ࡬ࡨࠬཎ")]
            elif active[bstack1ll_opy_ (u"࠭ࡴࡺࡲࡨࠫཏ")] == bstack1ll_opy_ (u"ࠧࡵࡧࡶࡸࠬཐ"):
                log[bstack1ll_opy_ (u"ࠨࡶࡨࡷࡹࡥࡲࡶࡰࡢࡹࡺ࡯ࡤࠨད")] = active[bstack1ll_opy_ (u"ࠩࡷࡩࡸࡺ࡟ࡳࡷࡱࡣࡺࡻࡩࡥࠩདྷ")]
        bstack1lll1111l_opy_.bstack11ll1111l_opy_([log])
    def start_test(self, attrs):
        test_uuid = uuid4().__str__()
        self.tests[test_uuid] = {}
        self.bstack111l1ll111_opy_.start()
        driver = bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠪࡦࡸࡺࡡࡤ࡭ࡖࡩࡸࡹࡩࡰࡰࡇࡶ࡮ࡼࡥࡳࠩན"), None)
        bstack111l1l1ll1_opy_ = bstack111ll111l1_opy_(
            name=attrs.scenario.name,
            uuid=test_uuid,
            started_at=bstack1l11l1111_opy_(),
            file_path=attrs.feature.filename,
            result=bstack1ll_opy_ (u"ࠦࡵ࡫࡮ࡥ࡫ࡱ࡫ࠧཔ"),
            framework=bstack1ll_opy_ (u"ࠬࡈࡥࡩࡣࡹࡩࠬཕ"),
            scope=[attrs.feature.name],
            bstack111l1ll1ll_opy_=bstack1lll1111l_opy_.bstack111ll1111l_opy_(driver) if driver and driver.session_id else {},
            meta={},
            tags=attrs.scenario.tags
        )
        self.tests[test_uuid][bstack1ll_opy_ (u"࠭ࡴࡦࡵࡷࡣࡩࡧࡴࡢࠩབ")] = bstack111l1l1ll1_opy_
        threading.current_thread().current_test_uuid = test_uuid
        bstack1lll1111l_opy_.bstack111ll11ll1_opy_(bstack1ll_opy_ (u"ࠧࡕࡧࡶࡸࡗࡻ࡮ࡔࡶࡤࡶࡹ࡫ࡤࠨབྷ"), bstack111l1l1ll1_opy_)
    def end_test(self, attrs):
        bstack111ll11l11_opy_ = {
            bstack1ll_opy_ (u"ࠣࡰࡤࡱࡪࠨམ"): attrs.feature.name,
            bstack1ll_opy_ (u"ࠤࡧࡩࡸࡩࡲࡪࡲࡷ࡭ࡴࡴࠢཙ"): attrs.feature.description
        }
        current_test_uuid = threading.current_thread().current_test_uuid
        bstack111l1l1ll1_opy_ = self.tests[current_test_uuid][bstack1ll_opy_ (u"ࠪࡸࡪࡹࡴࡠࡦࡤࡸࡦ࠭ཚ")]
        meta = {
            bstack1ll_opy_ (u"ࠦ࡫࡫ࡡࡵࡷࡵࡩࠧཛ"): bstack111ll11l11_opy_,
            bstack1ll_opy_ (u"ࠧࡹࡴࡦࡲࡶࠦཛྷ"): bstack111l1l1ll1_opy_.meta.get(bstack1ll_opy_ (u"࠭ࡳࡵࡧࡳࡷࠬཝ"), []),
            bstack1ll_opy_ (u"ࠢࡴࡥࡨࡲࡦࡸࡩࡰࠤཞ"): {
                bstack1ll_opy_ (u"ࠣࡰࡤࡱࡪࠨཟ"): attrs.feature.scenarios[0].name if len(attrs.feature.scenarios) else None
            }
        }
        bstack111l1l1ll1_opy_.bstack111ll11lll_opy_(meta)
        bstack111l1l1ll1_opy_.bstack111l1ll1l1_opy_(bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠩࡦࡹࡷࡸࡥ࡯ࡶࡢࡸࡪࡹࡴࡠࡪࡲࡳࡰࡹࠧའ"), []))
        bstack111l1l1l11_opy_, exception = self._111ll11l1l_opy_(attrs)
        bstack111ll1l11l_opy_ = Result(result=attrs.status.name, exception=exception, bstack111l1lll11_opy_=[bstack111l1l1l11_opy_])
        self.tests[threading.current_thread().current_test_uuid][bstack1ll_opy_ (u"ࠪࡸࡪࡹࡴࡠࡦࡤࡸࡦ࠭ཡ")].stop(time=bstack1l11l1111_opy_(), duration=int(attrs.duration)*1000, result=bstack111ll1l11l_opy_)
        bstack1lll1111l_opy_.bstack111ll11ll1_opy_(bstack1ll_opy_ (u"࡙ࠫ࡫ࡳࡵࡔࡸࡲࡋ࡯࡮ࡪࡵ࡫ࡩࡩ࠭ར"), self.tests[threading.current_thread().current_test_uuid][bstack1ll_opy_ (u"ࠬࡺࡥࡴࡶࡢࡨࡦࡺࡡࠨལ")])
    def bstack1ll11l1l1l_opy_(self, attrs):
        bstack111l1l1lll_opy_ = {
            bstack1ll_opy_ (u"࠭ࡩࡥࠩཤ"): uuid4().__str__(),
            bstack1ll_opy_ (u"ࠧ࡬ࡧࡼࡻࡴࡸࡤࠨཥ"): attrs.keyword,
            bstack1ll_opy_ (u"ࠨࡵࡷࡩࡵࡥࡡࡳࡩࡸࡱࡪࡴࡴࠨས"): [],
            bstack1ll_opy_ (u"ࠩࡷࡩࡽࡺࠧཧ"): attrs.name,
            bstack1ll_opy_ (u"ࠪࡷࡹࡧࡲࡵࡧࡧࡣࡦࡺࠧཨ"): bstack1l11l1111_opy_(),
            bstack1ll_opy_ (u"ࠫࡷ࡫ࡳࡶ࡮ࡷࠫཀྵ"): bstack1ll_opy_ (u"ࠬࡶࡥ࡯ࡦ࡬ࡲ࡬࠭ཪ"),
            bstack1ll_opy_ (u"࠭ࡤࡦࡵࡦࡶ࡮ࡶࡴࡪࡱࡱࠫཫ"): bstack1ll_opy_ (u"ࠧࠨཬ")
        }
        self.tests[threading.current_thread().current_test_uuid][bstack1ll_opy_ (u"ࠨࡶࡨࡷࡹࡥࡤࡢࡶࡤࠫ཭")].add_step(bstack111l1l1lll_opy_)
        threading.current_thread().current_step_uuid = bstack111l1l1lll_opy_[bstack1ll_opy_ (u"ࠩ࡬ࡨࠬ཮")]
    def bstack11llll11l_opy_(self, attrs):
        current_test_id = bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠪࡧࡺࡸࡲࡦࡰࡷࡣࡹ࡫ࡳࡵࡡࡸࡹ࡮ࡪࠧ཯"), None)
        current_step_uuid = bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠫࡨࡻࡲࡳࡧࡱࡸࡤࡹࡴࡦࡲࡢࡹࡺ࡯ࡤࠨ཰"), None)
        bstack111l1l1l11_opy_, exception = self._111ll11l1l_opy_(attrs)
        bstack111ll1l11l_opy_ = Result(result=attrs.status.name, exception=exception, bstack111l1lll11_opy_=[bstack111l1l1l11_opy_])
        self.tests[current_test_id][bstack1ll_opy_ (u"ࠬࡺࡥࡴࡶࡢࡨࡦࡺࡡࠨཱ")].bstack111ll1l1ll_opy_(current_step_uuid, duration=int(attrs.duration)*1000, result=bstack111ll1l11l_opy_)
        threading.current_thread().current_step_uuid = None
    def bstack11l11llll1_opy_(self, name, attrs):
        try:
            bstack111ll1ll11_opy_ = uuid4().__str__()
            self.tests[bstack111ll1ll11_opy_] = {}
            self.bstack111l1ll111_opy_.start()
            scopes = []
            driver = bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"࠭ࡢࡴࡶࡤࡧࡰ࡙ࡥࡴࡵ࡬ࡳࡳࡊࡲࡪࡸࡨࡶིࠬ"), None)
            current_thread = threading.current_thread()
            if not hasattr(current_thread, bstack1ll_opy_ (u"ࠧࡤࡷࡵࡶࡪࡴࡴࡠࡶࡨࡷࡹࡥࡨࡰࡱ࡮ࡷཱིࠬ")):
                current_thread.current_test_hooks = []
            current_thread.current_test_hooks.append(bstack111ll1ll11_opy_)
            if name in [bstack1ll_opy_ (u"ࠣࡤࡨࡪࡴࡸࡥࡠࡣ࡯ࡰུࠧ"), bstack1ll_opy_ (u"ࠤࡤࡪࡹ࡫ࡲࡠࡣ࡯ࡰཱུࠧ")]:
                file_path = os.path.join(attrs.config.base_dir, attrs.config.environment_file)
                scopes = [attrs.config.environment_file]
            elif name in [bstack1ll_opy_ (u"ࠥࡦࡪ࡬࡯ࡳࡧࡢࡪࡪࡧࡴࡶࡴࡨࠦྲྀ"), bstack1ll_opy_ (u"ࠦࡦ࡬ࡴࡦࡴࡢࡪࡪࡧࡴࡶࡴࡨࠦཷ")]:
                file_path = attrs.filename
                scopes = [attrs.name]
            else:
                file_path = attrs.filename
                if hasattr(attrs, bstack1ll_opy_ (u"ࠬ࡬ࡥࡢࡶࡸࡶࡪ࠭ླྀ")):
                    scopes =  [attrs.feature.name]
            hook_data = bstack111ll1l111_opy_(
                name=name,
                uuid=bstack111ll1ll11_opy_,
                started_at=bstack1l11l1111_opy_(),
                file_path=file_path,
                framework=bstack1ll_opy_ (u"ࠨࡂࡦࡪࡤࡺࡪࠨཹ"),
                bstack111l1ll1ll_opy_=bstack1lll1111l_opy_.bstack111ll1111l_opy_(driver) if driver and driver.session_id else {},
                scope=scopes,
                result=bstack1ll_opy_ (u"ࠢࡱࡧࡱࡨ࡮ࡴࡧེࠣ"),
                hook_type=name
            )
            self.tests[bstack111ll1ll11_opy_][bstack1ll_opy_ (u"ࠣࡶࡨࡷࡹࡥࡤࡢࡶࡤཻࠦ")] = hook_data
            current_test_id = bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠤࡦࡹࡷࡸࡥ࡯ࡶࡢࡸࡪࡹࡴࡠࡷࡸ࡭ࡩࠨོ"), None)
            if current_test_id:
                hook_data.bstack111l1ll11l_opy_(current_test_id)
            if name == bstack1ll_opy_ (u"ࠥࡦࡪ࡬࡯ࡳࡧࡢࡥࡱࡲཽࠢ"):
                threading.current_thread().before_all_hook_uuid = bstack111ll1ll11_opy_
            threading.current_thread().current_hook_uuid = bstack111ll1ll11_opy_
            bstack1lll1111l_opy_.bstack111ll11ll1_opy_(bstack1ll_opy_ (u"ࠦࡍࡵ࡯࡬ࡔࡸࡲࡘࡺࡡࡳࡶࡨࡨࠧཾ"), hook_data)
        except Exception as e:
            logger.debug(bstack1ll_opy_ (u"ࠧࡋࡲࡳࡱࡵࠤࡴࡩࡣࡶࡴࡵࡩࡩࠦࡩ࡯ࠢࡶࡸࡦࡸࡴࠡࡪࡲࡳࡰࠦࡥࡷࡧࡱࡸࡸ࠲ࠠࡩࡱࡲ࡯ࠥࡴࡡ࡮ࡧ࠽ࠤࠪࡹࠬࠡࡧࡵࡶࡴࡸ࠺ࠡࠧࡶࠦཿ"), name, e)
    def bstack11l1ll11l_opy_(self, attrs):
        bstack111l1llll1_opy_ = bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"࠭ࡣࡶࡴࡵࡩࡳࡺ࡟ࡩࡱࡲ࡯ࡤࡻࡵࡪࡦྀࠪ"), None)
        hook_data = self.tests[bstack111l1llll1_opy_][bstack1ll_opy_ (u"ࠧࡵࡧࡶࡸࡤࡪࡡࡵࡣཱྀࠪ")]
        status = bstack1ll_opy_ (u"ࠣࡲࡤࡷࡸ࡫ࡤࠣྂ")
        exception = None
        bstack111l1l1l11_opy_ = None
        if hook_data.name == bstack1ll_opy_ (u"ࠤࡤࡪࡹ࡫ࡲࡠࡣ࡯ࡰࠧྃ"):
            self.bstack111l1ll111_opy_.reset()
            bstack111ll11111_opy_ = self.tests[bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠪࡦࡪ࡬࡯ࡳࡧࡢࡥࡱࡲ࡟ࡩࡱࡲ࡯ࡤࡻࡵࡪࡦ྄ࠪ"), None)][bstack1ll_opy_ (u"ࠫࡹ࡫ࡳࡵࡡࡧࡥࡹࡧࠧ྅")].result.result
            if bstack111ll11111_opy_ == bstack1ll_opy_ (u"ࠧ࡬ࡡࡪ࡮ࡨࡨࠧ྆"):
                if attrs.hook_failures == 1:
                    status = bstack1ll_opy_ (u"ࠨࡰࡢࡵࡶࡩࡩࠨ྇")
                elif attrs.hook_failures == 2:
                    status = bstack1ll_opy_ (u"ࠢࡧࡣ࡬ࡰࡪࡪࠢྈ")
            elif attrs.aborted:
                status = bstack1ll_opy_ (u"ࠣࡨࡤ࡭ࡱ࡫ࡤࠣྉ")
            threading.current_thread().before_all_hook_uuid = None
        else:
            if hook_data.name == bstack1ll_opy_ (u"ࠩࡥࡩ࡫ࡵࡲࡦࡡࡤࡰࡱ࠭ྊ") and attrs.hook_failures == 1:
                status = bstack1ll_opy_ (u"ࠥࡪࡦ࡯࡬ࡦࡦࠥྋ")
            elif hasattr(attrs, bstack1ll_opy_ (u"ࠫࡪࡸࡲࡰࡴࡢࡱࡪࡹࡳࡢࡩࡨࠫྌ")) and attrs.error_message:
                status = bstack1ll_opy_ (u"ࠧ࡬ࡡࡪ࡮ࡨࡨࠧྍ")
            bstack111l1l1l11_opy_, exception = self._111ll11l1l_opy_(attrs)
        bstack111ll1l11l_opy_ = Result(result=status, exception=exception, bstack111l1lll11_opy_=[bstack111l1l1l11_opy_])
        hook_data.stop(time=bstack1l11l1111_opy_(), duration=0, result=bstack111ll1l11l_opy_)
        bstack1lll1111l_opy_.bstack111ll11ll1_opy_(bstack1ll_opy_ (u"࠭ࡈࡰࡱ࡮ࡖࡺࡴࡆࡪࡰ࡬ࡷ࡭࡫ࡤࠨྎ"), self.tests[bstack111l1llll1_opy_][bstack1ll_opy_ (u"ࠧࡵࡧࡶࡸࡤࡪࡡࡵࡣࠪྏ")])
        threading.current_thread().current_hook_uuid = None
    def _111ll11l1l_opy_(self, attrs):
        try:
            import traceback
            bstack11llll11ll_opy_ = traceback.format_tb(attrs.exc_traceback)
            bstack111l1l1l11_opy_ = bstack11llll11ll_opy_[-1] if bstack11llll11ll_opy_ else None
            exception = attrs.exception
        except Exception:
            logger.debug(bstack1ll_opy_ (u"ࠣࡇࡵࡶࡴࡸࠠࡰࡥࡦࡹࡷࡸࡥࡥࠢࡺ࡬࡮ࡲࡥࠡࡩࡨࡸࡹ࡯࡮ࡨࠢࡦࡹࡸࡺ࡯࡮ࠢࡷࡶࡦࡩࡥࡣࡣࡦ࡯ࠧྐ"))
            bstack111l1l1l11_opy_ = None
            exception = None
        return bstack111l1l1l11_opy_, exception