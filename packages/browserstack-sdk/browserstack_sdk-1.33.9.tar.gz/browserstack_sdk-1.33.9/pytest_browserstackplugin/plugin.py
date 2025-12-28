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
import atexit
import datetime
import inspect
import logging
import signal
import threading
from uuid import uuid4
from bstack_utils.measure import bstack11ll1llll1_opy_
from bstack_utils.percy_sdk import PercySDK
import pytest
from packaging import version
from browserstack_sdk.__init__ import (bstack1l1111llll_opy_, bstack11l1ll1l1l_opy_, update, bstack1l1ll111_opy_,
                                       bstack1lll111l1_opy_, bstack1llllll1l1_opy_, bstack1l1l11l11_opy_, bstack11111111l_opy_,
                                       bstack1lll1ll1l1_opy_, bstack1llll1ll1_opy_, bstack1l1111lll1_opy_,
                                       bstack111llll1ll_opy_, getAccessibilityResults, getAccessibilityResultsSummary, perform_scan, bstack111111l1l_opy_)
from browserstack_sdk.bstack11ll1ll111_opy_ import bstack1l111ll1l_opy_
from browserstack_sdk._version import __version__
from bstack_utils import bstack11l1l1lll1_opy_
from bstack_utils.capture import bstack111l1l1l1l_opy_
from bstack_utils.config import Config
from bstack_utils.percy import *
from bstack_utils.constants import bstack11ll11l1ll_opy_, bstack1l11111ll1_opy_, bstack1ll11ll111_opy_, \
    bstack1l1ll11lll_opy_
from bstack_utils.helper import bstack1l11l11l_opy_, bstack111llll11l1_opy_, bstack111l11ll1l_opy_, bstack11ll1l11l1_opy_, bstack1l1ll111lll_opy_, bstack1l11l1111_opy_, \
    bstack111ll11ll1l_opy_, \
    bstack11l111lll1l_opy_, bstack11l11111l1_opy_, bstack111ll1111_opy_, bstack111lll11l11_opy_, bstack1ll1l1l1ll_opy_, Notset, \
    bstack1l1111l11l_opy_, bstack11l1111ll11_opy_, bstack11l111l111l_opy_, Result, bstack111l1lll111_opy_, bstack111l1llllll_opy_, error_handler, \
    bstack1l11l1lll1_opy_, bstack1l1lll1l_opy_, bstack11l11lllll_opy_, bstack11l1111lll1_opy_
from bstack_utils.bstack111l1l11l1l_opy_ import bstack111l1l1lll1_opy_
from bstack_utils.messages import bstack1ll1l11l1_opy_, bstack1ll11lllll_opy_, bstack1l1ll1ll1_opy_, bstack11l1llllll_opy_, bstack1111ll11_opy_, \
    bstack1ll1111ll_opy_, bstack11ll11111_opy_, bstack11ll1l1l_opy_, bstack1llll1l1l1_opy_, bstack11llll1l11_opy_, \
    bstack11l1lll11_opy_, bstack111lll11l_opy_, bstack1111ll1l1_opy_
from bstack_utils.proxy import bstack1ll11ll11l_opy_, bstack1ll1ll11l_opy_
from bstack_utils.bstack1l111ll1l1_opy_ import bstack1lllll1l111l_opy_, bstack1lllll11ll11_opy_, bstack1lllll11ll1l_opy_, bstack1lllll1l11l1_opy_, \
    bstack1lllll1l1111_opy_, bstack1lllll1l11ll_opy_, bstack1lllll11l11l_opy_, bstack1l1111l1l1_opy_, bstack1lllll11l1ll_opy_
from bstack_utils.bstack1l1llll1l_opy_ import bstack111l1ll1_opy_
from bstack_utils.bstack11l1llll_opy_ import bstack1l11ll1l1_opy_, bstack111llll1l_opy_, bstack1l1l1111ll_opy_, \
    bstack11ll11111l_opy_, bstack1l111111ll_opy_
from bstack_utils.bstack111l1l1ll1_opy_ import bstack111ll111l1_opy_
from bstack_utils.bstack111ll1l1l1_opy_ import bstack1l11111lll_opy_
import bstack_utils.accessibility as bstack1llll1l11_opy_
from bstack_utils.bstack111ll111ll_opy_ import bstack1lll1111l_opy_
from bstack_utils.bstack1111l1ll1_opy_ import bstack1111l1ll1_opy_
from bstack_utils.bstack1l11l1lll_opy_ import bstack11llll11l1_opy_
from browserstack_sdk.__init__ import bstack11lll11ll1_opy_
from browserstack_sdk.sdk_cli.bstack1ll1lll11l1_opy_ import bstack1ll1l111l1l_opy_
from browserstack_sdk.sdk_cli.bstack111lll1l_opy_ import bstack111lll1l_opy_, bstack1lll1lll_opy_, bstack11ll111l11_opy_
from browserstack_sdk.sdk_cli.test_framework import bstack1l1111l1l1l_opy_, bstack1ll1ll1lll1_opy_, bstack1ll1l1ll11l_opy_
from browserstack_sdk.sdk_cli.cli import cli
from browserstack_sdk.sdk_cli.bstack111lll1l_opy_ import bstack111lll1l_opy_, bstack1lll1lll_opy_, bstack11ll111l11_opy_
bstack11ll1l1lll_opy_ = None
bstack1l1111ll1_opy_ = None
bstack11l1ll1111_opy_ = None
bstack11ll111ll_opy_ = None
bstack1ll11l1l_opy_ = None
bstack1l111l111_opy_ = None
bstack1ll11l1111_opy_ = None
bstack111ll111l_opy_ = None
bstack1ll11l11l1_opy_ = None
bstack1l1l111l1_opy_ = None
bstack1l11lll111_opy_ = None
bstack1l111l1ll_opy_ = None
bstack11lll1l111_opy_ = None
bstack11l11ll111_opy_ = bstack1ll_opy_ (u"ࠪࠫ⊶")
CONFIG = {}
bstack11l11l11ll_opy_ = False
bstack1ll111lll_opy_ = bstack1ll_opy_ (u"ࠫࠬ⊷")
bstack1l1l1ll1l1_opy_ = bstack1ll_opy_ (u"ࠬ࠭⊸")
bstack11lllllll1_opy_ = False
bstack1llll11lll_opy_ = []
bstack1ll1111l1_opy_ = bstack11ll11l1ll_opy_
bstack1lll1l111l1l_opy_ = bstack1ll_opy_ (u"࠭ࡰࡺࡶࡨࡷࡹ࠭⊹")
bstack111l11111_opy_ = {}
bstack1llll1111l_opy_ = None
bstack11l1l1l11_opy_ = False
logger = bstack11l1l1lll1_opy_.get_logger(__name__, bstack1ll1111l1_opy_)
store = {
    bstack1ll_opy_ (u"ࠧࡤࡷࡵࡶࡪࡴࡴࡠࡪࡲࡳࡰࡥࡵࡶ࡫ࡧࠫ⊺"): []
}
bstack1lll1l1ll1l1_opy_ = False
try:
    from playwright.sync_api import (
        BrowserContext,
        Page
    )
except:
    pass
import json
_111l11111l_opy_ = {}
current_test_uuid = None
cli_context = bstack1l1111l1l1l_opy_(
    test_framework_name=bstack111lllll1l_opy_[bstack1ll_opy_ (u"ࠨࡒ࡜ࡘࡊ࡙ࡔ࠮ࡄࡇࡈࠬ⊻")] if bstack1ll1l1l1ll_opy_() else bstack111lllll1l_opy_[bstack1ll_opy_ (u"ࠩࡓ࡝࡙ࡋࡓࡕࠩ⊼")],
    test_framework_version=pytest.__version__,
    platform_index=-1,
)
def bstack1lll111ll1_opy_(page, bstack1llllll1ll_opy_):
    try:
        page.evaluate(bstack1ll_opy_ (u"ࠥࡣࠥࡃ࠾ࠡࡽࢀࠦ⊽"),
                      bstack1ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭ࡢࡩࡽ࡫ࡣࡶࡶࡲࡶ࠿ࠦࡻࠣࡣࡦࡸ࡮ࡵ࡮ࠣ࠼ࠣࠦࡸ࡫ࡴࡔࡧࡶࡷ࡮ࡵ࡮ࡏࡣࡰࡩࠧ࠲ࠠࠣࡣࡵ࡫ࡺࡳࡥ࡯ࡶࡶࠦ࠿ࠦࡻࠣࡰࡤࡱࡪࠨ࠺ࠨ⊾") + json.dumps(
                          bstack1llllll1ll_opy_) + bstack1ll_opy_ (u"ࠧࢃࡽࠣ⊿"))
    except Exception as e:
        print(bstack1ll_opy_ (u"ࠨࡥࡹࡥࡨࡴࡹ࡯࡯࡯ࠢ࡬ࡲࠥࡶ࡬ࡢࡻࡺࡶ࡮࡭ࡨࡵࠢࡶࡩࡸࡹࡩࡰࡰࠣࡲࡦࡳࡥࠡࡽࢀࠦ⋀"), e)
def bstack1l111ll11l_opy_(page, message, level):
    try:
        page.evaluate(bstack1ll_opy_ (u"ࠢࡠࠢࡀࡂࠥࢁࡽࠣ⋁"), bstack1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࡟ࡦࡺࡨࡧࡺࡺ࡯ࡳ࠼ࠣࡿࠧࡧࡣࡵ࡫ࡲࡲࠧࡀࠠࠣࡣࡱࡲࡴࡺࡡࡵࡧࠥ࠰ࠥࠨࡡࡳࡩࡸࡱࡪࡴࡴࡴࠤ࠽ࠤࢀࠨࡤࡢࡶࡤࠦ࠿࠭⋂") + json.dumps(
            message) + bstack1ll_opy_ (u"ࠩ࠯ࠦࡱ࡫ࡶࡦ࡮ࠥ࠾ࠬ⋃") + json.dumps(level) + bstack1ll_opy_ (u"ࠪࢁࢂ࠭⋄"))
    except Exception as e:
        print(bstack1ll_opy_ (u"ࠦࡪࡾࡣࡦࡲࡷ࡭ࡴࡴࠠࡪࡰࠣࡴࡱࡧࡹࡸࡴ࡬࡫࡭ࡺࠠࡢࡰࡱࡳࡹࡧࡴࡪࡱࡱࠤࢀࢃࠢ⋅"), e)
def pytest_configure(config):
    global bstack1ll111lll_opy_
    global CONFIG
    bstack1ll1l1l111_opy_ = Config.bstack11lll1111_opy_()
    config.args = bstack1l11111lll_opy_.bstack1lll1l1lll11_opy_(config.args)
    bstack1ll1l1l111_opy_.bstack11lll1111l_opy_(bstack11l11lllll_opy_(config.getoption(bstack1ll_opy_ (u"ࠬࡹ࡫ࡪࡲࡖࡩࡸࡹࡩࡰࡰࡖࡸࡦࡺࡵࡴࠩ⋆"))))
    try:
        bstack11l1l1lll1_opy_.bstack111l111l1l1_opy_(config.inipath, config.rootpath)
    except:
        pass
    if cli.is_running():
        bstack111lll1l_opy_.invoke(bstack1lll1lll_opy_.CONNECT, bstack11ll111l11_opy_())
        cli_context.platform_index = int(os.environ.get(bstack1ll_opy_ (u"࠭ࡂࡓࡑ࡚ࡗࡊࡘࡓࡕࡃࡆࡏࡤࡖࡌࡂࡖࡉࡓࡗࡓ࡟ࡊࡐࡇࡉ࡝࠭⋇"), bstack1ll_opy_ (u"ࠧ࠱ࠩ⋈")))
        config = json.loads(os.environ.get(bstack1ll_opy_ (u"ࠣࡄࡕࡓ࡜࡙ࡅࡓࡕࡗࡅࡈࡑ࡟ࡄࡑࡑࡊࡎࡍࠢ⋉"), bstack1ll_opy_ (u"ࠤࡾࢁࠧ⋊")))
        cli.bstack1ll1l1l1111_opy_(bstack111ll1111_opy_(bstack1ll111lll_opy_, CONFIG), cli_context.platform_index, bstack1l1ll111_opy_)
    if cli.bstack1lll11ll1ll_opy_(bstack1ll1l111l1l_opy_):
        cli.bstack1lll111l1l1_opy_()
        logger.debug(bstack1ll_opy_ (u"ࠥࡇࡑࡏࠠࡪࡵࠣࡥࡨࡺࡩࡷࡧࠣࡪࡴࡸࠠࡱ࡮ࡤࡸ࡫ࡵࡲ࡮ࡡ࡬ࡲࡩ࡫ࡸ࠾ࠤ⋋") + str(cli_context.platform_index) + bstack1ll_opy_ (u"ࠦࠧ⋌"))
        cli.test_framework.track_event(cli_context, bstack1ll1ll1lll1_opy_.BEFORE_ALL, bstack1ll1l1ll11l_opy_.PRE, config)
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    when = getattr(call, bstack1ll_opy_ (u"ࠧࡽࡨࡦࡰࠥ⋍"), None)
    if cli.is_running() and when == bstack1ll_opy_ (u"ࠨࡣࡢ࡮࡯ࠦ⋎"):
        cli.test_framework.track_event(cli_context, bstack1ll1ll1lll1_opy_.LOG_REPORT, bstack1ll1l1ll11l_opy_.PRE, item, call)
    outcome = yield
    if when == bstack1ll_opy_ (u"ࠢࡤࡣ࡯ࡰࠧ⋏"):
        report = outcome.get_result()
        passed = report.passed or report.skipped or (report.failed and hasattr(report, bstack1ll_opy_ (u"ࠣࡹࡤࡷࡽ࡬ࡡࡪ࡮ࠥ⋐")))
        if not passed:
            config = json.loads(os.environ.get(bstack1ll_opy_ (u"ࠤࡅࡖࡔ࡝ࡓࡆࡔࡖࡘࡆࡉࡋࡠࡅࡒࡒࡋࡏࡇࠣ⋑"), bstack1ll_opy_ (u"ࠥࡿࢂࠨ⋒")))
            if bstack11llll11l1_opy_.bstack111l1l111_opy_(config):
                bstack111111l1ll1_opy_ = bstack11llll11l1_opy_.bstack1lll1l11ll_opy_(config)
                if item.execution_count > bstack111111l1ll1_opy_:
                    print(bstack1ll_opy_ (u"࡙ࠫ࡫ࡳࡵࠢࡩࡥ࡮ࡲࡥࡥࠢࡤࡪࡹ࡫ࡲࠡࡴࡨࡸࡷ࡯ࡥࡴ࠼ࠣࠫ⋓"), report.nodeid, os.environ.get(bstack1ll_opy_ (u"ࠬࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣ࡙ࡋࡓࡕࡊࡘࡆࡤ࡛ࡕࡊࡆࠪ⋔")))
                    bstack11llll11l1_opy_.bstack11111lll11l_opy_(report.nodeid)
            else:
                print(bstack1ll_opy_ (u"࠭ࡔࡦࡵࡷࠤ࡫ࡧࡩ࡭ࡧࡧ࠾ࠥ࠭⋕"), report.nodeid, os.environ.get(bstack1ll_opy_ (u"ࠧࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡔࡆࡕࡗࡌ࡚ࡈ࡟ࡖࡗࡌࡈࠬ⋖")))
                bstack11llll11l1_opy_.bstack11111lll11l_opy_(report.nodeid)
        else:
            print(bstack1ll_opy_ (u"ࠨࡖࡨࡷࡹࠦࡰࡢࡵࡶࡩࡩࡀࠠࠨ⋗"), report.nodeid, os.environ.get(bstack1ll_opy_ (u"ࠩࡅࡖࡔ࡝ࡓࡆࡔࡖࡘࡆࡉࡋࡠࡖࡈࡗ࡙ࡎࡕࡃࡡࡘ࡙ࡎࡊࠧ⋘")))
    if cli.is_running():
        if when == bstack1ll_opy_ (u"ࠥࡷࡪࡺࡵࡱࠤ⋙"):
            cli.test_framework.track_event(cli_context, bstack1ll1ll1lll1_opy_.BEFORE_EACH, bstack1ll1l1ll11l_opy_.POST, item, call, outcome)
        elif when == bstack1ll_opy_ (u"ࠦࡨࡧ࡬࡭ࠤ⋚"):
            cli.test_framework.track_event(cli_context, bstack1ll1ll1lll1_opy_.LOG_REPORT, bstack1ll1l1ll11l_opy_.POST, item, call, outcome)
        elif when == bstack1ll_opy_ (u"ࠧࡺࡥࡢࡴࡧࡳࡼࡴࠢ⋛"):
            cli.test_framework.track_event(cli_context, bstack1ll1ll1lll1_opy_.AFTER_EACH, bstack1ll1l1ll11l_opy_.POST, item, call, outcome)
        return # skip all existing operations
    skipSessionName = item.config.getoption(bstack1ll_opy_ (u"࠭ࡳ࡬࡫ࡳࡗࡪࡹࡳࡪࡱࡱࡒࡦࡳࡥࠨ⋜"))
    plugins = item.config.getoption(bstack1ll_opy_ (u"ࠢࡱ࡮ࡸ࡫࡮ࡴࡳࠣ⋝"))
    report = outcome.get_result()
    os.environ[bstack1ll_opy_ (u"ࠨࡒ࡜ࡘࡊ࡙ࡔࡠࡖࡈࡗ࡙ࡥࡎࡂࡏࡈࠫ⋞")] = report.nodeid
    bstack1lll1l1l1lll_opy_(item, call, report)
    if bstack1ll_opy_ (u"ࠤࡳࡽࡹ࡫ࡳࡵࡡࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫ࡱ࡮ࡸ࡫࡮ࡴࠢ⋟") not in plugins or bstack1ll1l1l1ll_opy_():
        return
    summary = []
    driver = getattr(item, bstack1ll_opy_ (u"ࠥࡣࡩࡸࡩࡷࡧࡵࠦ⋠"), None)
    page = getattr(item, bstack1ll_opy_ (u"ࠦࡤࡶࡡࡨࡧࠥ⋡"), None)
    try:
        if (driver == None or driver.session_id == None):
            driver = threading.current_thread().bstackSessionDriver
    except:
        pass
    item._driver = driver
    if (driver is not None or cli.is_running()):
        bstack1lll1l1l11l1_opy_(item, report, summary, skipSessionName)
    if (page is not None):
        bstack1lll1l1ll11l_opy_(item, report, summary, skipSessionName)
def bstack1lll1l1l11l1_opy_(item, report, summary, skipSessionName):
    if report.when == bstack1ll_opy_ (u"ࠬࡹࡥࡵࡷࡳࠫ⋢") and report.skipped:
        bstack1lllll11l1ll_opy_(report)
    if report.when in [bstack1ll_opy_ (u"ࠨࡳࡦࡶࡸࡴࠧ⋣"), bstack1ll_opy_ (u"ࠢࡵࡧࡤࡶࡩࡵࡷ࡯ࠤ⋤")]:
        return
    if not bstack1l1ll111lll_opy_():
        return
    try:
        if ((str(skipSessionName).lower() != bstack1ll_opy_ (u"ࠨࡶࡵࡹࡪ࠭⋥")) and (not cli.is_running())) and item._driver.session_id:
            item._driver.execute_script(
                bstack1ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫ࡠࡧࡻࡩࡨࡻࡴࡰࡴ࠽ࠤࢀࠨࡡࡤࡶ࡬ࡳࡳࠨ࠺ࠡࠤࡶࡩࡹ࡙ࡥࡴࡵ࡬ࡳࡳࡔࡡ࡮ࡧࠥ࠰ࠥࠨࡡࡳࡩࡸࡱࡪࡴࡴࡴࠤ࠽ࠤࢀࠨ࡮ࡢ࡯ࡨࠦ࠿ࠦࠧ⋦") + json.dumps(
                    report.nodeid) + bstack1ll_opy_ (u"ࠪࢁࢂ࠭⋧"))
        os.environ[bstack1ll_opy_ (u"ࠫࡕ࡟ࡔࡆࡕࡗࡣ࡙ࡋࡓࡕࡡࡑࡅࡒࡋࠧ⋨")] = report.nodeid
    except Exception as e:
        summary.append(
            bstack1ll_opy_ (u"ࠧ࡝ࡁࡓࡐࡌࡒࡌࡀࠠࡇࡣ࡬ࡰࡪࡪࠠࡵࡱࠣࡱࡦࡸ࡫ࠡࡵࡨࡷࡸ࡯࡯࡯ࠢࡱࡥࡲ࡫࠺ࠡࡽ࠳ࢁࠧ⋩").format(e)
        )
    passed = report.passed or report.skipped or (report.failed and hasattr(report, bstack1ll_opy_ (u"ࠨࡷࡢࡵࡻࡪࡦ࡯࡬ࠣ⋪")))
    bstack111lll1ll_opy_ = bstack1ll_opy_ (u"ࠢࠣ⋫")
    bstack1lllll11l1ll_opy_(report)
    if not passed:
        try:
            bstack111lll1ll_opy_ = report.longrepr.reprcrash
        except Exception as e:
            summary.append(
                bstack1ll_opy_ (u"࡙ࠣࡄࡖࡓࡏࡎࡈ࠼ࠣࡊࡦ࡯࡬ࡦࡦࠣࡸࡴࠦࡤࡦࡶࡨࡶࡲ࡯࡮ࡦࠢࡩࡥ࡮ࡲࡵࡳࡧࠣࡶࡪࡧࡳࡰࡰ࠽ࠤࢀ࠶ࡽࠣ⋬").format(e)
            )
        try:
            if (threading.current_thread().bstackTestErrorMessages == None):
                threading.current_thread().bstackTestErrorMessages = []
        except Exception as e:
            threading.current_thread().bstackTestErrorMessages = []
        threading.current_thread().bstackTestErrorMessages.append(str(bstack111lll1ll_opy_))
    if not report.skipped:
        passed = report.passed or (report.failed and hasattr(report, bstack1ll_opy_ (u"ࠤࡺࡥࡸࡾࡦࡢ࡫࡯ࠦ⋭")))
        bstack111lll1ll_opy_ = bstack1ll_opy_ (u"ࠥࠦ⋮")
        if not passed:
            try:
                bstack111lll1ll_opy_ = report.longrepr.reprcrash
            except Exception as e:
                summary.append(
                    bstack1ll_opy_ (u"ࠦ࡜ࡇࡒࡏࡋࡑࡋ࠿ࠦࡆࡢ࡫࡯ࡩࡩࠦࡴࡰࠢࡧࡩࡹ࡫ࡲ࡮࡫ࡱࡩࠥ࡬ࡡࡪ࡮ࡸࡶࡪࠦࡲࡦࡣࡶࡳࡳࡀࠠࡼ࠲ࢀࠦ⋯").format(e)
                )
            try:
                if (threading.current_thread().bstackTestErrorMessages == None):
                    threading.current_thread().bstackTestErrorMessages = []
            except Exception as e:
                threading.current_thread().bstackTestErrorMessages = []
            threading.current_thread().bstackTestErrorMessages.append(str(bstack111lll1ll_opy_))
        try:
            if passed:
                item._driver.execute_script(
                    bstack1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮ࡣࡪࡾࡥࡤࡷࡷࡳࡷࡀࠠࡼ࡞ࠍࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠦࡦࡩࡴࡪࡱࡱࠦ࠿ࠦࠢࡢࡰࡱࡳࡹࡧࡴࡦࠤ࠯ࠤࡡࠐࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠢࡢࡴࡪࡹࡲ࡫࡮ࡵࡵࠥ࠾ࠥࢁ࡜ࠋࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠨ࡬ࡦࡸࡨࡰࠧࡀࠠࠣ࡫ࡱࡪࡴࠨࠬࠡ࡞ࠍࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠣࡦࡤࡸࡦࠨ࠺ࠡࠩ⋰")
                    + json.dumps(bstack1ll_opy_ (u"ࠨࡰࡢࡵࡶࡩࡩࠧࠢ⋱"))
                    + bstack1ll_opy_ (u"ࠢ࡝ࠌࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࢀࡠࠏࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࡿࠥ⋲")
                )
            else:
                item._driver.execute_script(
                    bstack1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࡟ࡦࡺࡨࡧࡺࡺ࡯ࡳ࠼ࠣࡿࡡࠐࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠢࡢࡥࡷ࡭ࡴࡴࠢ࠻ࠢࠥࡥࡳࡴ࡯ࡵࡣࡷࡩࠧ࠲ࠠ࡝ࠌࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠥࡥࡷ࡭ࡵ࡮ࡧࡱࡸࡸࠨ࠺ࠡࡽ࡟ࠎࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠤ࡯ࡩࡻ࡫࡬ࠣ࠼ࠣࠦࡪࡸࡲࡰࡴࠥ࠰ࠥࡢࠊࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠧࡪࡡࡵࡣࠥ࠾ࠥ࠭⋳")
                    + json.dumps(str(bstack111lll1ll_opy_))
                    + bstack1ll_opy_ (u"ࠤ࡟ࠎࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࢂࡢࠊࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࢁࠧ⋴")
                )
        except Exception as e:
            summary.append(bstack1ll_opy_ (u"࡛ࠥࡆࡘࡎࡊࡐࡊ࠾ࠥࡌࡡࡪ࡮ࡨࡨࠥࡺ࡯ࠡࡣࡱࡲࡴࡺࡡࡵࡧ࠽ࠤࢀ࠶ࡽࠣ⋵").format(e))
def bstack1lll1l11lll1_opy_(test_name, error_message):
    try:
        bstack1lll1l11l1ll_opy_ = []
        bstack11l1l1l1_opy_ = os.environ.get(bstack1ll_opy_ (u"ࠫࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡔࡑࡇࡔࡇࡑࡕࡑࡤࡏࡎࡅࡇ࡛ࠫ⋶"), bstack1ll_opy_ (u"ࠬ࠶ࠧ⋷"))
        bstack1l11111l1_opy_ = {bstack1ll_opy_ (u"࠭࡮ࡢ࡯ࡨࠫ⋸"): test_name, bstack1ll_opy_ (u"ࠧࡦࡴࡵࡳࡷ࠭⋹"): error_message, bstack1ll_opy_ (u"ࠨ࡫ࡱࡨࡪࡾࠧ⋺"): bstack11l1l1l1_opy_}
        bstack1lll1l1l1111_opy_ = os.path.join(tempfile.gettempdir(), bstack1ll_opy_ (u"ࠩࡳࡻࡤࡶࡹࡵࡧࡶࡸࡤ࡫ࡲࡳࡱࡵࡣࡱ࡯ࡳࡵ࠰࡭ࡷࡴࡴࠧ⋻"))
        if os.path.exists(bstack1lll1l1l1111_opy_):
            with open(bstack1lll1l1l1111_opy_) as f:
                bstack1lll1l11l1ll_opy_ = json.load(f)
        bstack1lll1l11l1ll_opy_.append(bstack1l11111l1_opy_)
        with open(bstack1lll1l1l1111_opy_, bstack1ll_opy_ (u"ࠪࡻࠬ⋼")) as f:
            json.dump(bstack1lll1l11l1ll_opy_, f)
    except Exception as e:
        logger.debug(bstack1ll_opy_ (u"ࠫࡊࡸࡲࡰࡴࠣ࡭ࡳࠦࡰࡦࡴࡶ࡭ࡸࡺࡩ࡯ࡩࠣࡴࡱࡧࡹࡸࡴ࡬࡫࡭ࡺࠠࡱࡻࡷࡩࡸࡺࠠࡦࡴࡵࡳࡷࡹ࠺ࠡࠩ⋽") + str(e))
def bstack1lll1l1ll11l_opy_(item, report, summary, skipSessionName):
    if report.when in [bstack1ll_opy_ (u"ࠧࡹࡥࡵࡷࡳࠦ⋾"), bstack1ll_opy_ (u"ࠨࡴࡦࡣࡵࡨࡴࡽ࡮ࠣ⋿")]:
        return
    if (str(skipSessionName).lower() != bstack1ll_opy_ (u"ࠧࡵࡴࡸࡩࠬ⌀")):
        bstack1lll111ll1_opy_(item._page, report.nodeid)
    passed = report.passed or report.skipped or (report.failed and hasattr(report, bstack1ll_opy_ (u"ࠣࡹࡤࡷࡽ࡬ࡡࡪ࡮ࠥ⌁")))
    bstack111lll1ll_opy_ = bstack1ll_opy_ (u"ࠤࠥ⌂")
    bstack1lllll11l1ll_opy_(report)
    if not report.skipped:
        if not passed:
            try:
                bstack111lll1ll_opy_ = report.longrepr.reprcrash
            except Exception as e:
                summary.append(
                    bstack1ll_opy_ (u"࡛ࠥࡆࡘࡎࡊࡐࡊ࠾ࠥࡌࡡࡪ࡮ࡨࡨࠥࡺ࡯ࠡࡦࡨࡸࡪࡸ࡭ࡪࡰࡨࠤ࡫ࡧࡩ࡭ࡷࡵࡩࠥࡸࡥࡢࡵࡲࡲ࠿ࠦࡻ࠱ࡿࠥ⌃").format(e)
                )
        try:
            if passed:
                bstack1l111111ll_opy_(getattr(item, bstack1ll_opy_ (u"ࠫࡤࡶࡡࡨࡧࠪ⌄"), None), bstack1ll_opy_ (u"ࠧࡶࡡࡴࡵࡨࡨࠧ⌅"))
            else:
                error_message = bstack1ll_opy_ (u"࠭ࠧ⌆")
                if bstack111lll1ll_opy_:
                    bstack1l111ll11l_opy_(item._page, str(bstack111lll1ll_opy_), bstack1ll_opy_ (u"ࠢࡦࡴࡵࡳࡷࠨ⌇"))
                    bstack1l111111ll_opy_(getattr(item, bstack1ll_opy_ (u"ࠨࡡࡳࡥ࡬࡫ࠧ⌈"), None), bstack1ll_opy_ (u"ࠤࡩࡥ࡮ࡲࡥࡥࠤ⌉"), str(bstack111lll1ll_opy_))
                    error_message = str(bstack111lll1ll_opy_)
                else:
                    bstack1l111111ll_opy_(getattr(item, bstack1ll_opy_ (u"ࠪࡣࡵࡧࡧࡦࠩ⌊"), None), bstack1ll_opy_ (u"ࠦ࡫ࡧࡩ࡭ࡧࡧࠦ⌋"))
                bstack1lll1l11lll1_opy_(report.nodeid, error_message)
        except Exception as e:
            summary.append(bstack1ll_opy_ (u"ࠧ࡝ࡁࡓࡐࡌࡒࡌࡀࠠࡇࡣ࡬ࡰࡪࡪࠠࡵࡱࠣࡹࡵࡪࡡࡵࡧࠣࡷࡪࡹࡳࡪࡱࡱࠤࡸࡺࡡࡵࡷࡶ࠾ࠥࢁ࠰ࡾࠤ⌌").format(e))
def pytest_addoption(parser):
    parser.addoption(bstack1ll_opy_ (u"ࠨ࠭࠮ࡵ࡮࡭ࡵ࡙ࡥࡴࡵ࡬ࡳࡳࡔࡡ࡮ࡧࠥ⌍"), default=bstack1ll_opy_ (u"ࠢࡇࡣ࡯ࡷࡪࠨ⌎"), help=bstack1ll_opy_ (u"ࠣࡃࡸࡸࡴࡳࡡࡵ࡫ࡦࠤࡸ࡫ࡴࠡࡵࡨࡷࡸ࡯࡯࡯ࠢࡱࡥࡲ࡫ࠢ⌏"))
    parser.addoption(bstack1ll_opy_ (u"ࠤ࠰࠱ࡸࡱࡩࡱࡕࡨࡷࡸ࡯࡯࡯ࡕࡷࡥࡹࡻࡳࠣ⌐"), default=bstack1ll_opy_ (u"ࠥࡊࡦࡲࡳࡦࠤ⌑"), help=bstack1ll_opy_ (u"ࠦࡆࡻࡴࡰ࡯ࡤࡸ࡮ࡩࠠࡴࡧࡷࠤࡸ࡫ࡳࡴ࡫ࡲࡲࠥࡴࡡ࡮ࡧࠥ⌒"))
    try:
        import pytest_selenium.pytest_selenium
    except:
        parser.addoption(bstack1ll_opy_ (u"ࠧ࠳࠭ࡥࡴ࡬ࡺࡪࡸࠢ⌓"), action=bstack1ll_opy_ (u"ࠨࡳࡵࡱࡵࡩࠧ⌔"), default=bstack1ll_opy_ (u"ࠢࡤࡪࡵࡳࡲ࡫ࠢ⌕"),
                         help=bstack1ll_opy_ (u"ࠣࡆࡵ࡭ࡻ࡫ࡲࠡࡶࡲࠤࡷࡻ࡮ࠡࡶࡨࡷࡹࡹࠢ⌖"))
def bstack111l1lll1l_opy_(log):
    if not (log[bstack1ll_opy_ (u"ࠩࡰࡩࡸࡹࡡࡨࡧࠪ⌗")] and log[bstack1ll_opy_ (u"ࠪࡱࡪࡹࡳࡢࡩࡨࠫ⌘")].strip()):
        return
    active = bstack111l1lllll_opy_()
    log = {
        bstack1ll_opy_ (u"ࠫࡱ࡫ࡶࡦ࡮ࠪ⌙"): log[bstack1ll_opy_ (u"ࠬࡲࡥࡷࡧ࡯ࠫ⌚")],
        bstack1ll_opy_ (u"࠭ࡴࡪ࡯ࡨࡷࡹࡧ࡭ࡱࠩ⌛"): bstack111l11ll1l_opy_().isoformat() + bstack1ll_opy_ (u"࡛ࠧࠩ⌜"),
        bstack1ll_opy_ (u"ࠨ࡯ࡨࡷࡸࡧࡧࡦࠩ⌝"): log[bstack1ll_opy_ (u"ࠩࡰࡩࡸࡹࡡࡨࡧࠪ⌞")],
    }
    if active:
        if active[bstack1ll_opy_ (u"ࠪࡸࡾࡶࡥࠨ⌟")] == bstack1ll_opy_ (u"ࠫ࡭ࡵ࡯࡬ࠩ⌠"):
            log[bstack1ll_opy_ (u"ࠬ࡮࡯ࡰ࡭ࡢࡶࡺࡴ࡟ࡶࡷ࡬ࡨࠬ⌡")] = active[bstack1ll_opy_ (u"࠭ࡨࡰࡱ࡮ࡣࡷࡻ࡮ࡠࡷࡸ࡭ࡩ࠭⌢")]
        elif active[bstack1ll_opy_ (u"ࠧࡵࡻࡳࡩࠬ⌣")] == bstack1ll_opy_ (u"ࠨࡶࡨࡷࡹ࠭⌤"):
            log[bstack1ll_opy_ (u"ࠩࡷࡩࡸࡺ࡟ࡳࡷࡱࡣࡺࡻࡩࡥࠩ⌥")] = active[bstack1ll_opy_ (u"ࠪࡸࡪࡹࡴࡠࡴࡸࡲࡤࡻࡵࡪࡦࠪ⌦")]
    bstack1lll1111l_opy_.bstack11ll1111l_opy_([log])
def bstack111l1lllll_opy_():
    if len(store[bstack1ll_opy_ (u"ࠫࡨࡻࡲࡳࡧࡱࡸࡤ࡮࡯ࡰ࡭ࡢࡹࡺ࡯ࡤࠨ⌧")]) > 0 and store[bstack1ll_opy_ (u"ࠬࡩࡵࡳࡴࡨࡲࡹࡥࡨࡰࡱ࡮ࡣࡺࡻࡩࡥࠩ⌨")][-1]:
        return {
            bstack1ll_opy_ (u"࠭ࡴࡺࡲࡨࠫ〈"): bstack1ll_opy_ (u"ࠧࡩࡱࡲ࡯ࠬ〉"),
            bstack1ll_opy_ (u"ࠨࡪࡲࡳࡰࡥࡲࡶࡰࡢࡹࡺ࡯ࡤࠨ⌫"): store[bstack1ll_opy_ (u"ࠩࡦࡹࡷࡸࡥ࡯ࡶࡢ࡬ࡴࡵ࡫ࡠࡷࡸ࡭ࡩ࠭⌬")][-1]
        }
    if store.get(bstack1ll_opy_ (u"ࠪࡧࡺࡸࡲࡦࡰࡷࡣࡹ࡫ࡳࡵࡡࡸࡹ࡮ࡪࠧ⌭"), None):
        return {
            bstack1ll_opy_ (u"ࠫࡹࡿࡰࡦࠩ⌮"): bstack1ll_opy_ (u"ࠬࡺࡥࡴࡶࠪ⌯"),
            bstack1ll_opy_ (u"࠭ࡴࡦࡵࡷࡣࡷࡻ࡮ࡠࡷࡸ࡭ࡩ࠭⌰"): store[bstack1ll_opy_ (u"ࠧࡤࡷࡵࡶࡪࡴࡴࡠࡶࡨࡷࡹࡥࡵࡶ࡫ࡧࠫ⌱")]
        }
    return None
def pytest_runtest_logstart(nodeid, location):
    if cli.is_running():
        cli.test_framework.track_event(cli_context, bstack1ll1ll1lll1_opy_.INIT_TEST, bstack1ll1l1ll11l_opy_.PRE, nodeid, location)
def pytest_runtest_logfinish(nodeid, location):
    if cli.is_running():
        cli.test_framework.track_event(cli_context, bstack1ll1ll1lll1_opy_.INIT_TEST, bstack1ll1l1ll11l_opy_.POST, nodeid, location)
def pytest_runtest_call(item):
    if cli.is_running():
        cli.test_framework.track_event(cli_context, bstack1ll1ll1lll1_opy_.TEST, bstack1ll1l1ll11l_opy_.PRE, item)
        return
    try:
        global CONFIG
        item._1lll1l1111l1_opy_ = True
        bstack1lllll11_opy_ = bstack1llll1l11_opy_.bstack1ll11ll1_opy_(bstack11l111lll1l_opy_(item.own_markers))
        if not cli.bstack1lll11ll1ll_opy_(bstack1ll1l111l1l_opy_):
            item._a11y_test_case = bstack1lllll11_opy_
            if bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠨࡣ࠴࠵ࡾࡖ࡬ࡢࡶࡩࡳࡷࡳࠧ⌲"), None):
                driver = getattr(item, bstack1ll_opy_ (u"ࠩࡢࡨࡷ࡯ࡶࡦࡴࠪ⌳"), None)
                item._a11y_started = bstack1llll1l11_opy_.bstack1l11l111l1_opy_(driver, bstack1lllll11_opy_)
        if not bstack1lll1111l_opy_.on() or bstack1lll1l111l1l_opy_ != bstack1ll_opy_ (u"ࠪࡴࡾࡺࡥࡴࡶࠪ⌴"):
            return
        global current_test_uuid #, bstack111l1ll111_opy_
        bstack1111ll1lll_opy_ = {
            bstack1ll_opy_ (u"ࠫࡺࡻࡩࡥࠩ⌵"): uuid4().__str__(),
            bstack1ll_opy_ (u"ࠬࡹࡴࡢࡴࡷࡩࡩࡥࡡࡵࠩ⌶"): bstack111l11ll1l_opy_().isoformat() + bstack1ll_opy_ (u"࡚࠭ࠨ⌷")
        }
        current_test_uuid = bstack1111ll1lll_opy_[bstack1ll_opy_ (u"ࠧࡶࡷ࡬ࡨࠬ⌸")]
        store[bstack1ll_opy_ (u"ࠨࡥࡸࡶࡷ࡫࡮ࡵࡡࡷࡩࡸࡺ࡟ࡶࡷ࡬ࡨࠬ⌹")] = bstack1111ll1lll_opy_[bstack1ll_opy_ (u"ࠩࡸࡹ࡮ࡪࠧ⌺")]
        threading.current_thread().current_test_uuid = current_test_uuid
        _111l11111l_opy_[item.nodeid] = {**_111l11111l_opy_[item.nodeid], **bstack1111ll1lll_opy_}
        bstack1lll1l11llll_opy_(item, _111l11111l_opy_[item.nodeid], bstack1ll_opy_ (u"ࠪࡘࡪࡹࡴࡓࡷࡱࡗࡹࡧࡲࡵࡧࡧࠫ⌻"))
    except Exception as err:
        print(bstack1ll_opy_ (u"ࠫࡊࡾࡣࡦࡲࡷ࡭ࡴࡴࠠࡪࡰࠣࡴࡾࡺࡥࡴࡶࡢࡶࡺࡴࡴࡦࡵࡷࡣࡨࡧ࡬࡭࠼ࠣࡿࢂ࠭⌼"), str(err))
def pytest_runtest_setup(item):
    store[bstack1ll_opy_ (u"ࠬࡩࡵࡳࡴࡨࡲࡹࡥࡴࡦࡵࡷࡣ࡮ࡺࡥ࡮ࠩ⌽")] = item
    if cli.is_running():
        cli.test_framework.track_event(cli_context, bstack1ll1ll1lll1_opy_.BEFORE_EACH, bstack1ll1l1ll11l_opy_.PRE, item, bstack1ll_opy_ (u"࠭ࡳࡦࡶࡸࡴࠬ⌾"))
    if bstack11llll11l1_opy_.bstack1111l1l1111_opy_():
            bstack1lll1l1l11ll_opy_ = bstack1ll_opy_ (u"ࠢࡔ࡭࡬ࡴࡵ࡯࡮ࡨࠢࡷࡩࡸࡺࠠࡢࡵࠣࡸ࡭࡫ࠠࡢࡤࡲࡶࡹࠦࡢࡶ࡫࡯ࡨࠥ࡬ࡩ࡭ࡧࠣࡩࡽ࡯ࡳࡵࡵ࠱ࠦ⌿")
            logger.error(bstack1lll1l1l11ll_opy_)
            bstack1111ll1lll_opy_ = {
                bstack1ll_opy_ (u"ࠨࡷࡸ࡭ࡩ࠭⍀"): uuid4().__str__(),
                bstack1ll_opy_ (u"ࠩࡶࡸࡦࡸࡴࡦࡦࡢࡥࡹ࠭⍁"): bstack111l11ll1l_opy_().isoformat() + bstack1ll_opy_ (u"ࠪ࡞ࠬ⍂"),
                bstack1ll_opy_ (u"ࠫ࡫࡯࡮ࡪࡵ࡫ࡩࡩࡥࡡࡵࠩ⍃"): bstack111l11ll1l_opy_().isoformat() + bstack1ll_opy_ (u"ࠬࡠࠧ⍄"),
                bstack1ll_opy_ (u"࠭ࡲࡦࡵࡸࡰࡹ࠭⍅"): bstack1ll_opy_ (u"ࠧࡴ࡭࡬ࡴࡵ࡫ࡤࠨ⍆"),
                bstack1ll_opy_ (u"ࠨࡴࡨࡥࡸࡵ࡮ࠨ⍇"): bstack1lll1l1l11ll_opy_,
                bstack1ll_opy_ (u"ࠩ࡫ࡳࡴࡱࡳࠨ⍈"): [],
                bstack1ll_opy_ (u"ࠪࡪ࡮ࡾࡴࡶࡴࡨࡷࠬ⍉"): []
            }
            bstack1lll1l11llll_opy_(item, bstack1111ll1lll_opy_, bstack1ll_opy_ (u"࡙ࠫ࡫ࡳࡵࡔࡸࡲࡘࡱࡩࡱࡲࡨࡨࠬ⍊"))
            pytest.skip(bstack1lll1l1l11ll_opy_)
            return # skip all existing operations
    global bstack1lll1l1ll1l1_opy_
    threading.current_thread().percySessionName = item.nodeid
    if bstack111lll11l11_opy_():
        atexit.register(bstack11lll1l11_opy_)
        if not bstack1lll1l1ll1l1_opy_:
            try:
                bstack1lll1l11ll1l_opy_ = [signal.SIGINT, signal.SIGTERM]
                if not bstack11l1111lll1_opy_():
                    bstack1lll1l11ll1l_opy_.extend([signal.SIGHUP, signal.SIGQUIT])
                for s in bstack1lll1l11ll1l_opy_:
                    signal.signal(s, bstack1lll1l11ll11_opy_)
                bstack1lll1l1ll1l1_opy_ = True
            except Exception as e:
                logger.debug(
                    bstack1ll_opy_ (u"ࠧࡋࡲࡳࡱࡵࠤ࡮ࡴࠠࡳࡧࡪ࡭ࡸࡺࡥࡳࠢࡶ࡭࡬ࡴࡡ࡭ࠢ࡫ࡥࡳࡪ࡬ࡦࡴࡶ࠾ࠥࠨ⍋") + str(e))
        try:
            item.config.hook.pytest_selenium_runtest_makereport = bstack1lllll1l111l_opy_
        except Exception as err:
            threading.current_thread().testStatus = bstack1ll_opy_ (u"࠭ࡰࡢࡵࡶࡩࡩ࠭⍌")
    try:
        if not bstack1lll1111l_opy_.on():
            return
        uuid = uuid4().__str__()
        bstack1111ll1lll_opy_ = {
            bstack1ll_opy_ (u"ࠧࡶࡷ࡬ࡨࠬ⍍"): uuid,
            bstack1ll_opy_ (u"ࠨࡵࡷࡥࡷࡺࡥࡥࡡࡤࡸࠬ⍎"): bstack111l11ll1l_opy_().isoformat() + bstack1ll_opy_ (u"ࠩ࡝ࠫ⍏"),
            bstack1ll_opy_ (u"ࠪࡸࡾࡶࡥࠨ⍐"): bstack1ll_opy_ (u"ࠫ࡭ࡵ࡯࡬ࠩ⍑"),
            bstack1ll_opy_ (u"ࠬ࡮࡯ࡰ࡭ࡢࡸࡾࡶࡥࠨ⍒"): bstack1ll_opy_ (u"࠭ࡂࡆࡈࡒࡖࡊࡥࡅࡂࡅࡋࠫ⍓"),
            bstack1ll_opy_ (u"ࠧࡩࡱࡲ࡯ࡤࡴࡡ࡮ࡧࠪ⍔"): bstack1ll_opy_ (u"ࠨࡵࡨࡸࡺࡶࠧ⍕")
        }
        threading.current_thread().current_hook_uuid = uuid
        threading.current_thread().current_test_item = item
        store[bstack1ll_opy_ (u"ࠩࡦࡹࡷࡸࡥ࡯ࡶࡢࡸࡪࡹࡴࡠ࡫ࡷࡩࡲ࠭⍖")] = item
        store[bstack1ll_opy_ (u"ࠪࡧࡺࡸࡲࡦࡰࡷࡣ࡭ࡵ࡯࡬ࡡࡸࡹ࡮ࡪࠧ⍗")] = [uuid]
        if not _111l11111l_opy_.get(item.nodeid, None):
            _111l11111l_opy_[item.nodeid] = {bstack1ll_opy_ (u"ࠫ࡭ࡵ࡯࡬ࡵࠪ⍘"): [], bstack1ll_opy_ (u"ࠬ࡬ࡩࡹࡶࡸࡶࡪࡹࠧ⍙"): []}
        _111l11111l_opy_[item.nodeid][bstack1ll_opy_ (u"࠭ࡨࡰࡱ࡮ࡷࠬ⍚")].append(bstack1111ll1lll_opy_[bstack1ll_opy_ (u"ࠧࡶࡷ࡬ࡨࠬ⍛")])
        _111l11111l_opy_[item.nodeid + bstack1ll_opy_ (u"ࠨ࠯ࡶࡩࡹࡻࡰࠨ⍜")] = bstack1111ll1lll_opy_
        bstack1lll1l111ll1_opy_(item, bstack1111ll1lll_opy_, bstack1ll_opy_ (u"ࠩࡋࡳࡴࡱࡒࡶࡰࡖࡸࡦࡸࡴࡦࡦࠪ⍝"))
    except Exception as err:
        print(bstack1ll_opy_ (u"ࠪࡉࡽࡩࡥࡱࡶ࡬ࡳࡳࠦࡩ࡯ࠢࡳࡽࡹ࡫ࡳࡵࡡࡵࡹࡳࡺࡥࡴࡶࡢࡷࡪࡺࡵࡱ࠼ࠣࡿࢂ࠭⍞"), str(err))
def pytest_runtest_teardown(item):
    if cli.is_running():
        cli.test_framework.track_event(cli_context, bstack1ll1ll1lll1_opy_.TEST, bstack1ll1l1ll11l_opy_.POST, item)
        cli.test_framework.track_event(cli_context, bstack1ll1ll1lll1_opy_.AFTER_EACH, bstack1ll1l1ll11l_opy_.PRE, item, bstack1ll_opy_ (u"ࠫࡹ࡫ࡡࡳࡦࡲࡻࡳ࠭⍟"))
        return # skip all existing operations
    try:
        global bstack111l11111_opy_
        bstack11l1l1l1_opy_ = 0
        if bstack11lllllll1_opy_ is True:
            bstack11l1l1l1_opy_ = int(os.environ.get(bstack1ll_opy_ (u"ࠬࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣࡕࡒࡁࡕࡈࡒࡖࡒࡥࡉࡏࡆࡈ࡜ࠬ⍠")))
        if bstack1lll1lllll_opy_.bstack11ll11lll1_opy_() == bstack1ll_opy_ (u"ࠨࡴࡳࡷࡨࠦ⍡"):
            if bstack1lll1lllll_opy_.bstack1l1l1111l1_opy_() == bstack1ll_opy_ (u"ࠢࡵࡧࡶࡸࡨࡧࡳࡦࠤ⍢"):
                bstack1lll1l111l11_opy_ = bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠨࡲࡨࡶࡨࡿࡓࡦࡵࡶ࡭ࡴࡴࡎࡢ࡯ࡨࠫ⍣"), None)
                bstack1111lll1l_opy_ = bstack1lll1l111l11_opy_ + bstack1ll_opy_ (u"ࠤ࠰ࡸࡪࡹࡴࡤࡣࡶࡩࠧ⍤")
                driver = getattr(item, bstack1ll_opy_ (u"ࠪࡣࡩࡸࡩࡷࡧࡵࠫ⍥"), None)
                bstack11l1l1llll_opy_ = getattr(item, bstack1ll_opy_ (u"ࠫࡳࡧ࡭ࡦࠩ⍦"), None)
                bstack1l1lll1ll_opy_ = getattr(item, bstack1ll_opy_ (u"ࠬࡻࡵࡪࡦࠪ⍧"), None)
                PercySDK.screenshot(driver, bstack1111lll1l_opy_, bstack11l1l1llll_opy_=bstack11l1l1llll_opy_, bstack1l1lll1ll_opy_=bstack1l1lll1ll_opy_, bstack1ll1lll11l_opy_=bstack11l1l1l1_opy_)
        if not cli.bstack1lll11ll1ll_opy_(bstack1ll1l111l1l_opy_):
            if getattr(item, bstack1ll_opy_ (u"࠭࡟ࡢ࠳࠴ࡽࡤࡹࡴࡢࡴࡷࡩࡩ࠭⍨"), False):
                bstack1l111ll1l_opy_.bstack1l1l11111_opy_(getattr(item, bstack1ll_opy_ (u"ࠧࡠࡦࡵ࡭ࡻ࡫ࡲࠨ⍩"), None), bstack111l11111_opy_, logger, item)
        if not bstack1lll1111l_opy_.on():
            return
        bstack1111ll1lll_opy_ = {
            bstack1ll_opy_ (u"ࠨࡷࡸ࡭ࡩ࠭⍪"): uuid4().__str__(),
            bstack1ll_opy_ (u"ࠩࡶࡸࡦࡸࡴࡦࡦࡢࡥࡹ࠭⍫"): bstack111l11ll1l_opy_().isoformat() + bstack1ll_opy_ (u"ࠪ࡞ࠬ⍬"),
            bstack1ll_opy_ (u"ࠫࡹࡿࡰࡦࠩ⍭"): bstack1ll_opy_ (u"ࠬ࡮࡯ࡰ࡭ࠪ⍮"),
            bstack1ll_opy_ (u"࠭ࡨࡰࡱ࡮ࡣࡹࡿࡰࡦࠩ⍯"): bstack1ll_opy_ (u"ࠧࡂࡈࡗࡉࡗࡥࡅࡂࡅࡋࠫ⍰"),
            bstack1ll_opy_ (u"ࠨࡪࡲࡳࡰࡥ࡮ࡢ࡯ࡨࠫ⍱"): bstack1ll_opy_ (u"ࠩࡷࡩࡦࡸࡤࡰࡹࡱࠫ⍲")
        }
        _111l11111l_opy_[item.nodeid + bstack1ll_opy_ (u"ࠪ࠱ࡹ࡫ࡡࡳࡦࡲࡻࡳ࠭⍳")] = bstack1111ll1lll_opy_
        bstack1lll1l111ll1_opy_(item, bstack1111ll1lll_opy_, bstack1ll_opy_ (u"ࠫࡍࡵ࡯࡬ࡔࡸࡲࡘࡺࡡࡳࡶࡨࡨࠬ⍴"))
    except Exception as err:
        print(bstack1ll_opy_ (u"ࠬࡋࡸࡤࡧࡳࡸ࡮ࡵ࡮ࠡ࡫ࡱࠤࡵࡿࡴࡦࡵࡷࡣࡷࡻ࡮ࡵࡧࡶࡸࡤࡺࡥࡢࡴࡧࡳࡼࡴ࠺ࠡࡽࢀࠫ⍵"), str(err))
@pytest.hookimpl(hookwrapper=True)
def pytest_fixture_setup(fixturedef, request):
    if bstack1lllll1l11l1_opy_(fixturedef.argname):
        store[bstack1ll_opy_ (u"࠭ࡣࡶࡴࡵࡩࡳࡺ࡟࡮ࡱࡧࡹࡱ࡫࡟ࡪࡶࡨࡱࠬ⍶")] = request.node
    elif bstack1lllll1l1111_opy_(fixturedef.argname):
        store[bstack1ll_opy_ (u"ࠧࡤࡷࡵࡶࡪࡴࡴࡠࡥ࡯ࡥࡸࡹ࡟ࡪࡶࡨࡱࠬ⍷")] = request.node
    if not bstack1lll1111l_opy_.on():
        if cli.is_running():
            cli.test_framework.track_event(cli_context, bstack1ll1ll1lll1_opy_.SETUP_FIXTURE, bstack1ll1l1ll11l_opy_.PRE, fixturedef, request)
        outcome = yield
        if cli.is_running():
            cli.test_framework.track_event(cli_context, bstack1ll1ll1lll1_opy_.SETUP_FIXTURE, bstack1ll1l1ll11l_opy_.POST, fixturedef, request, outcome)
        return # skip all existing operations
    start_time = datetime.datetime.now()
    if cli.is_running():
        cli.test_framework.track_event(cli_context, bstack1ll1ll1lll1_opy_.SETUP_FIXTURE, bstack1ll1l1ll11l_opy_.PRE, fixturedef, request)
    outcome = yield
    if cli.is_running():
        cli.test_framework.track_event(cli_context, bstack1ll1ll1lll1_opy_.SETUP_FIXTURE, bstack1ll1l1ll11l_opy_.POST, fixturedef, request, outcome)
        return # skip all existing operations
    try:
        fixture = {
            bstack1ll_opy_ (u"ࠨࡰࡤࡱࡪ࠭⍸"): fixturedef.argname,
            bstack1ll_opy_ (u"ࠩࡵࡩࡸࡻ࡬ࡵࠩ⍹"): bstack111ll11ll1l_opy_(outcome),
            bstack1ll_opy_ (u"ࠪࡨࡺࡸࡡࡵ࡫ࡲࡲࠬ⍺"): (datetime.datetime.now() - start_time).total_seconds() * 1000
        }
        current_test_item = store[bstack1ll_opy_ (u"ࠫࡨࡻࡲࡳࡧࡱࡸࡤࡺࡥࡴࡶࡢ࡭ࡹ࡫࡭ࠨ⍻")]
        if not _111l11111l_opy_.get(current_test_item.nodeid, None):
            _111l11111l_opy_[current_test_item.nodeid] = {bstack1ll_opy_ (u"ࠬ࡬ࡩࡹࡶࡸࡶࡪࡹࠧ⍼"): []}
        _111l11111l_opy_[current_test_item.nodeid][bstack1ll_opy_ (u"࠭ࡦࡪࡺࡷࡹࡷ࡫ࡳࠨ⍽")].append(fixture)
    except Exception as err:
        logger.debug(bstack1ll_opy_ (u"ࠧࡆࡺࡦࡩࡵࡺࡩࡰࡰࠣ࡭ࡳࠦࡰࡺࡶࡨࡷࡹࡥࡦࡪࡺࡷࡹࡷ࡫࡟ࡴࡧࡷࡹࡵࡀࠠࡼࡿࠪ⍾"), str(err))
if bstack1ll1l1l1ll_opy_() and bstack1lll1111l_opy_.on():
    def pytest_bdd_before_step(request, step):
        if cli.is_running():
            cli.test_framework.track_event(cli_context, bstack1ll1ll1lll1_opy_.STEP, bstack1ll1l1ll11l_opy_.PRE, request, step)
            return
        try:
            _111l11111l_opy_[request.node.nodeid][bstack1ll_opy_ (u"ࠨࡶࡨࡷࡹࡥࡤࡢࡶࡤࠫ⍿")].bstack1ll11l1l1l_opy_(id(step))
        except Exception as err:
            print(bstack1ll_opy_ (u"ࠩࡈࡼࡨ࡫ࡰࡵ࡫ࡲࡲࠥ࡯࡮ࠡࡲࡼࡸࡪࡹࡴࡠࡤࡧࡨࡤࡨࡥࡧࡱࡵࡩࡤࡹࡴࡦࡲ࠽ࠤࢀࢃࠧ⎀"), str(err))
    def pytest_bdd_step_error(request, step, exception):
        if cli.is_running():
            cli.test_framework.track_event(cli_context, bstack1ll1ll1lll1_opy_.STEP, bstack1ll1l1ll11l_opy_.POST, request, step, exception)
            return
        try:
            _111l11111l_opy_[request.node.nodeid][bstack1ll_opy_ (u"ࠪࡸࡪࡹࡴࡠࡦࡤࡸࡦ࠭⎁")].bstack111ll1l1ll_opy_(id(step), Result.failed(exception=exception))
        except Exception as err:
            print(bstack1ll_opy_ (u"ࠫࡊࡾࡣࡦࡲࡷ࡭ࡴࡴࠠࡪࡰࠣࡴࡾࡺࡥࡴࡶࡢࡦࡩࡪ࡟ࡴࡶࡨࡴࡤ࡫ࡲࡳࡱࡵ࠾ࠥࢁࡽࠨ⎂"), str(err))
    def pytest_bdd_after_step(request, step):
        if cli.is_running():
            cli.test_framework.track_event(cli_context, bstack1ll1ll1lll1_opy_.STEP, bstack1ll1l1ll11l_opy_.POST, request, step)
            return
        try:
            bstack111l1l1ll1_opy_: bstack111ll111l1_opy_ = _111l11111l_opy_[request.node.nodeid][bstack1ll_opy_ (u"ࠬࡺࡥࡴࡶࡢࡨࡦࡺࡡࠨ⎃")]
            bstack111l1l1ll1_opy_.bstack111ll1l1ll_opy_(id(step), Result.passed())
        except Exception as err:
            print(bstack1ll_opy_ (u"࠭ࡅࡹࡥࡨࡴࡹ࡯࡯࡯ࠢ࡬ࡲࠥࡶࡹࡵࡧࡶࡸࡤࡨࡤࡥࡡࡶࡸࡪࡶ࡟ࡦࡴࡵࡳࡷࡀࠠࡼࡿࠪ⎄"), str(err))
    def pytest_bdd_before_scenario(request, feature, scenario):
        global bstack1lll1l111l1l_opy_
        try:
            if not bstack1lll1111l_opy_.on() or bstack1lll1l111l1l_opy_ != bstack1ll_opy_ (u"ࠧࡱࡻࡷࡩࡸࡺ࠭ࡣࡦࡧࠫ⎅"):
                return
            if cli.is_running():
                cli.test_framework.track_event(cli_context, bstack1ll1ll1lll1_opy_.TEST, bstack1ll1l1ll11l_opy_.PRE, request, feature, scenario)
                return
            driver = bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠨࡤࡶࡸࡦࡩ࡫ࡔࡧࡶࡷ࡮ࡵ࡮ࡅࡴ࡬ࡺࡪࡸࠧ⎆"), None)
            if not _111l11111l_opy_.get(request.node.nodeid, None):
                _111l11111l_opy_[request.node.nodeid] = {}
            bstack111l1l1ll1_opy_ = bstack111ll111l1_opy_.bstack1llll11lll1l_opy_(
                scenario, feature, request.node,
                name=bstack1lllll1l11ll_opy_(request.node, scenario),
                started_at=bstack1l11l1111_opy_(),
                file_path=feature.filename,
                scope=[feature.name],
                framework=bstack1ll_opy_ (u"ࠩࡓࡽࡹ࡫ࡳࡵ࠯ࡦࡹࡨࡻ࡭ࡣࡧࡵࠫ⎇"),
                tags=bstack1lllll11l11l_opy_(feature, scenario),
                bstack111l1ll1ll_opy_=bstack1lll1111l_opy_.bstack111ll1111l_opy_(driver) if driver and driver.session_id else {}
            )
            _111l11111l_opy_[request.node.nodeid][bstack1ll_opy_ (u"ࠪࡸࡪࡹࡴࡠࡦࡤࡸࡦ࠭⎈")] = bstack111l1l1ll1_opy_
            bstack1lll1l11l111_opy_(bstack111l1l1ll1_opy_.uuid)
            bstack1lll1111l_opy_.bstack111ll11ll1_opy_(bstack1ll_opy_ (u"࡙ࠫ࡫ࡳࡵࡔࡸࡲࡘࡺࡡࡳࡶࡨࡨࠬ⎉"), bstack111l1l1ll1_opy_)
        except Exception as err:
            print(bstack1ll_opy_ (u"ࠬࡋࡸࡤࡧࡳࡸ࡮ࡵ࡮ࠡ࡫ࡱࠤࡵࡿࡴࡦࡵࡷࡣࡧࡪࡤࡠࡤࡨࡪࡴࡸࡥࡠࡵࡦࡩࡳࡧࡲࡪࡱ࠽ࠤࢀࢃࠧ⎊"), str(err))
def bstack1lll1l11111l_opy_(bstack111ll1ll11_opy_):
    if bstack111ll1ll11_opy_ in store[bstack1ll_opy_ (u"࠭ࡣࡶࡴࡵࡩࡳࡺ࡟ࡩࡱࡲ࡯ࡤࡻࡵࡪࡦࠪ⎋")]:
        store[bstack1ll_opy_ (u"ࠧࡤࡷࡵࡶࡪࡴࡴࡠࡪࡲࡳࡰࡥࡵࡶ࡫ࡧࠫ⎌")].remove(bstack111ll1ll11_opy_)
def bstack1lll1l11l111_opy_(test_uuid):
    store[bstack1ll_opy_ (u"ࠨࡥࡸࡶࡷ࡫࡮ࡵࡡࡷࡩࡸࡺ࡟ࡶࡷ࡬ࡨࠬ⎍")] = test_uuid
    threading.current_thread().current_test_uuid = test_uuid
@bstack1lll1111l_opy_.bstack1lll1ll1llll_opy_
def bstack1lll1l1l1lll_opy_(item, call, report):
    logger.debug(bstack1ll_opy_ (u"ࠩ࡫ࡥࡳࡪ࡬ࡦࡡࡲ࠵࠶ࡿ࡟ࡵࡧࡶࡸࡤ࡫ࡶࡦࡰࡷ࠾ࠥࡹࡴࡢࡴࡷࠫ⎎"))
    global bstack1lll1l111l1l_opy_
    bstack1lllll1l1l_opy_ = bstack1l11l1111_opy_()
    if hasattr(report, bstack1ll_opy_ (u"ࠪࡷࡹࡵࡰࠨ⎏")):
        bstack1lllll1l1l_opy_ = bstack111l1lll111_opy_(report.stop)
    elif hasattr(report, bstack1ll_opy_ (u"ࠫࡸࡺࡡࡳࡶࠪ⎐")):
        bstack1lllll1l1l_opy_ = bstack111l1lll111_opy_(report.start)
    try:
        if getattr(report, bstack1ll_opy_ (u"ࠬࡽࡨࡦࡰࠪ⎑"), bstack1ll_opy_ (u"࠭ࠧ⎒")) == bstack1ll_opy_ (u"ࠧࡤࡣ࡯ࡰࠬ⎓"):
            logger.debug(bstack1ll_opy_ (u"ࠨࡪࡤࡲࡩࡲࡥࡠࡱ࠴࠵ࡾࡥࡴࡦࡵࡷࡣࡪࡼࡥ࡯ࡶ࠽ࠤࡸࡺࡡࡵࡧࠣ࠱ࠥࢁࡽ࠭ࠢࡩࡶࡦࡳࡥࡸࡱࡵ࡯ࠥ࠳ࠠࡼࡿࠪ⎔").format(getattr(report, bstack1ll_opy_ (u"ࠩࡺ࡬ࡪࡴࠧ⎕"), bstack1ll_opy_ (u"ࠪࠫ⎖")).__str__(), bstack1lll1l111l1l_opy_))
            if bstack1lll1l111l1l_opy_ == bstack1ll_opy_ (u"ࠫࡵࡿࡴࡦࡵࡷࠫ⎗"):
                _111l11111l_opy_[item.nodeid][bstack1ll_opy_ (u"ࠬ࡬ࡩ࡯࡫ࡶ࡬ࡪࡪ࡟ࡢࡶࠪ⎘")] = bstack1lllll1l1l_opy_
                bstack1lll1l11llll_opy_(item, _111l11111l_opy_[item.nodeid], bstack1ll_opy_ (u"࠭ࡔࡦࡵࡷࡖࡺࡴࡆࡪࡰ࡬ࡷ࡭࡫ࡤࠨ⎙"), report, call)
                store[bstack1ll_opy_ (u"ࠧࡤࡷࡵࡶࡪࡴࡴࡠࡶࡨࡷࡹࡥࡵࡶ࡫ࡧࠫ⎚")] = None
            elif bstack1lll1l111l1l_opy_ == bstack1ll_opy_ (u"ࠣࡲࡼࡸࡪࡹࡴ࠮ࡤࡧࡨࠧ⎛"):
                bstack111l1l1ll1_opy_ = _111l11111l_opy_[item.nodeid][bstack1ll_opy_ (u"ࠩࡷࡩࡸࡺ࡟ࡥࡣࡷࡥࠬ⎜")]
                bstack111l1l1ll1_opy_.set(hooks=_111l11111l_opy_[item.nodeid].get(bstack1ll_opy_ (u"ࠪ࡬ࡴࡵ࡫ࡴࠩ⎝"), []))
                exception, bstack111l1lll11_opy_ = None, None
                if call.excinfo:
                    exception = call.excinfo.value
                    bstack111l1lll11_opy_ = [call.excinfo.exconly(), getattr(report, bstack1ll_opy_ (u"ࠫࡱࡵ࡮ࡨࡴࡨࡴࡷࡺࡥࡹࡶࠪ⎞"), bstack1ll_opy_ (u"ࠬ࠭⎟"))]
                bstack111l1l1ll1_opy_.stop(time=bstack1lllll1l1l_opy_, result=Result(result=getattr(report, bstack1ll_opy_ (u"࠭࡯ࡶࡶࡦࡳࡲ࡫ࠧ⎠"), bstack1ll_opy_ (u"ࠧࡱࡣࡶࡷࡪࡪࠧ⎡")), exception=exception, bstack111l1lll11_opy_=bstack111l1lll11_opy_))
                bstack1lll1111l_opy_.bstack111ll11ll1_opy_(bstack1ll_opy_ (u"ࠨࡖࡨࡷࡹࡘࡵ࡯ࡈ࡬ࡲ࡮ࡹࡨࡦࡦࠪ⎢"), _111l11111l_opy_[item.nodeid][bstack1ll_opy_ (u"ࠩࡷࡩࡸࡺ࡟ࡥࡣࡷࡥࠬ⎣")])
        elif getattr(report, bstack1ll_opy_ (u"ࠪࡻ࡭࡫࡮ࠨ⎤"), bstack1ll_opy_ (u"ࠫࠬ⎥")) in [bstack1ll_opy_ (u"ࠬࡹࡥࡵࡷࡳࠫ⎦"), bstack1ll_opy_ (u"࠭ࡴࡦࡣࡵࡨࡴࡽ࡮ࠨ⎧")]:
            logger.debug(bstack1ll_opy_ (u"ࠧࡩࡣࡱࡨࡱ࡫࡟ࡰ࠳࠴ࡽࡤࡺࡥࡴࡶࡢࡩࡻ࡫࡮ࡵ࠼ࠣࡷࡹࡧࡴࡦࠢ࠰ࠤࢀࢃࠬࠡࡨࡵࡥࡲ࡫ࡷࡰࡴ࡮ࠤ࠲ࠦࡻࡾࠩ⎨").format(getattr(report, bstack1ll_opy_ (u"ࠨࡹ࡫ࡩࡳ࠭⎩"), bstack1ll_opy_ (u"ࠩࠪ⎪")).__str__(), bstack1lll1l111l1l_opy_))
            bstack111l1llll1_opy_ = item.nodeid + bstack1ll_opy_ (u"ࠪ࠱ࠬ⎫") + getattr(report, bstack1ll_opy_ (u"ࠫࡼ࡮ࡥ࡯ࠩ⎬"), bstack1ll_opy_ (u"ࠬ࠭⎭"))
            if getattr(report, bstack1ll_opy_ (u"࠭ࡳ࡬࡫ࡳࡴࡪࡪࠧ⎮"), False):
                hook_type = bstack1ll_opy_ (u"ࠧࡃࡇࡉࡓࡗࡋ࡟ࡆࡃࡆࡌࠬ⎯") if getattr(report, bstack1ll_opy_ (u"ࠨࡹ࡫ࡩࡳ࠭⎰"), bstack1ll_opy_ (u"ࠩࠪ⎱")) == bstack1ll_opy_ (u"ࠪࡷࡪࡺࡵࡱࠩ⎲") else bstack1ll_opy_ (u"ࠫࡆࡌࡔࡆࡔࡢࡉࡆࡉࡈࠨ⎳")
                _111l11111l_opy_[bstack111l1llll1_opy_] = {
                    bstack1ll_opy_ (u"ࠬࡻࡵࡪࡦࠪ⎴"): uuid4().__str__(),
                    bstack1ll_opy_ (u"࠭ࡳࡵࡣࡵࡸࡪࡪ࡟ࡢࡶࠪ⎵"): bstack1lllll1l1l_opy_,
                    bstack1ll_opy_ (u"ࠧࡩࡱࡲ࡯ࡤࡺࡹࡱࡧࠪ⎶"): hook_type
                }
            _111l11111l_opy_[bstack111l1llll1_opy_][bstack1ll_opy_ (u"ࠨࡨ࡬ࡲ࡮ࡹࡨࡦࡦࡢࡥࡹ࠭⎷")] = bstack1lllll1l1l_opy_
            bstack1lll1l11111l_opy_(_111l11111l_opy_[bstack111l1llll1_opy_][bstack1ll_opy_ (u"ࠩࡸࡹ࡮ࡪࠧ⎸")])
            bstack1lll1l111ll1_opy_(item, _111l11111l_opy_[bstack111l1llll1_opy_], bstack1ll_opy_ (u"ࠪࡌࡴࡵ࡫ࡓࡷࡱࡊ࡮ࡴࡩࡴࡪࡨࡨࠬ⎹"), report, call)
            if getattr(report, bstack1ll_opy_ (u"ࠫࡼ࡮ࡥ࡯ࠩ⎺"), bstack1ll_opy_ (u"ࠬ࠭⎻")) == bstack1ll_opy_ (u"࠭ࡳࡦࡶࡸࡴࠬ⎼"):
                if getattr(report, bstack1ll_opy_ (u"ࠧࡰࡷࡷࡧࡴࡳࡥࠨ⎽"), bstack1ll_opy_ (u"ࠨࡲࡤࡷࡸ࡫ࡤࠨ⎾")) == bstack1ll_opy_ (u"ࠩࡩࡥ࡮ࡲࡥࡥࠩ⎿"):
                    bstack1111ll1lll_opy_ = {
                        bstack1ll_opy_ (u"ࠪࡹࡺ࡯ࡤࠨ⏀"): uuid4().__str__(),
                        bstack1ll_opy_ (u"ࠫࡸࡺࡡࡳࡶࡨࡨࡤࡧࡴࠨ⏁"): bstack1l11l1111_opy_(),
                        bstack1ll_opy_ (u"ࠬ࡬ࡩ࡯࡫ࡶ࡬ࡪࡪ࡟ࡢࡶࠪ⏂"): bstack1l11l1111_opy_()
                    }
                    _111l11111l_opy_[item.nodeid] = {**_111l11111l_opy_[item.nodeid], **bstack1111ll1lll_opy_}
                    bstack1lll1l11llll_opy_(item, _111l11111l_opy_[item.nodeid], bstack1ll_opy_ (u"࠭ࡔࡦࡵࡷࡖࡺࡴࡓࡵࡣࡵࡸࡪࡪࠧ⏃"))
                    bstack1lll1l11llll_opy_(item, _111l11111l_opy_[item.nodeid], bstack1ll_opy_ (u"ࠧࡕࡧࡶࡸࡗࡻ࡮ࡇ࡫ࡱ࡭ࡸ࡮ࡥࡥࠩ⏄"), report, call)
    except Exception as err:
        print(bstack1ll_opy_ (u"ࠨࡇࡻࡧࡪࡶࡴࡪࡱࡱࠤ࡮ࡴࠠࡩࡣࡱࡨࡱ࡫࡟ࡰ࠳࠴ࡽࡤࡺࡥࡴࡶࡢࡩࡻ࡫࡮ࡵ࠼ࠣࡿࢂ࠭⏅"), str(err))
def bstack1lll11llllll_opy_(test, bstack1111ll1lll_opy_, result=None, call=None, bstack1111l111_opy_=None, outcome=None):
    file_path = os.path.relpath(test.fspath.strpath, start=os.getcwd())
    bstack111l1l1ll1_opy_ = {
        bstack1ll_opy_ (u"ࠩࡸࡹ࡮ࡪࠧ⏆"): bstack1111ll1lll_opy_[bstack1ll_opy_ (u"ࠪࡹࡺ࡯ࡤࠨ⏇")],
        bstack1ll_opy_ (u"ࠫࡹࡿࡰࡦࠩ⏈"): bstack1ll_opy_ (u"ࠬࡺࡥࡴࡶࠪ⏉"),
        bstack1ll_opy_ (u"࠭࡮ࡢ࡯ࡨࠫ⏊"): test.name,
        bstack1ll_opy_ (u"ࠧࡣࡱࡧࡽࠬ⏋"): {
            bstack1ll_opy_ (u"ࠨ࡮ࡤࡲ࡬࠭⏌"): bstack1ll_opy_ (u"ࠩࡳࡽࡹ࡮࡯࡯ࠩ⏍"),
            bstack1ll_opy_ (u"ࠪࡧࡴࡪࡥࠨ⏎"): inspect.getsource(test.obj)
        },
        bstack1ll_opy_ (u"ࠫ࡮ࡪࡥ࡯ࡶ࡬ࡪ࡮࡫ࡲࠨ⏏"): test.name,
        bstack1ll_opy_ (u"ࠬࡹࡣࡰࡲࡨࠫ⏐"): test.name,
        bstack1ll_opy_ (u"࠭ࡳࡤࡱࡳࡩࡸ࠭⏑"): bstack1l11111lll_opy_.bstack111l111111_opy_(test),
        bstack1ll_opy_ (u"ࠧࡧ࡫࡯ࡩࡤࡴࡡ࡮ࡧࠪ⏒"): file_path,
        bstack1ll_opy_ (u"ࠨ࡮ࡲࡧࡦࡺࡩࡰࡰࠪ⏓"): file_path,
        bstack1ll_opy_ (u"ࠩࡵࡩࡸࡻ࡬ࡵࠩ⏔"): bstack1ll_opy_ (u"ࠪࡴࡪࡴࡤࡪࡰࡪࠫ⏕"),
        bstack1ll_opy_ (u"ࠫࡻࡩ࡟ࡧ࡫࡯ࡩࡵࡧࡴࡩࠩ⏖"): file_path,
        bstack1ll_opy_ (u"ࠬࡹࡴࡢࡴࡷࡩࡩࡥࡡࡵࠩ⏗"): bstack1111ll1lll_opy_[bstack1ll_opy_ (u"࠭ࡳࡵࡣࡵࡸࡪࡪ࡟ࡢࡶࠪ⏘")],
        bstack1ll_opy_ (u"ࠧࡧࡴࡤࡱࡪࡽ࡯ࡳ࡭ࠪ⏙"): bstack1ll_opy_ (u"ࠨࡒࡼࡸࡪࡹࡴࠨ⏚"),
        bstack1ll_opy_ (u"ࠩࡦࡹࡸࡺ࡯࡮ࡔࡨࡶࡺࡴࡐࡢࡴࡤࡱࠬ⏛"): {
            bstack1ll_opy_ (u"ࠪࡶࡪࡸࡵ࡯ࡡࡱࡥࡲ࡫ࠧ⏜"): test.nodeid
        },
        bstack1ll_opy_ (u"ࠫࡹࡧࡧࡴࠩ⏝"): bstack11l111lll1l_opy_(test.own_markers)
    }
    if bstack1111l111_opy_ in [bstack1ll_opy_ (u"࡚ࠬࡥࡴࡶࡕࡹࡳ࡙࡫ࡪࡲࡳࡩࡩ࠭⏞"), bstack1ll_opy_ (u"࠭ࡔࡦࡵࡷࡖࡺࡴࡆࡪࡰ࡬ࡷ࡭࡫ࡤࠨ⏟")]:
        bstack111l1l1ll1_opy_[bstack1ll_opy_ (u"ࠧ࡮ࡧࡷࡥࠬ⏠")] = {
            bstack1ll_opy_ (u"ࠨࡨ࡬ࡼࡹࡻࡲࡦࡵࠪ⏡"): bstack1111ll1lll_opy_.get(bstack1ll_opy_ (u"ࠩࡩ࡭ࡽࡺࡵࡳࡧࡶࠫ⏢"), [])
        }
    if bstack1111l111_opy_ == bstack1ll_opy_ (u"ࠪࡘࡪࡹࡴࡓࡷࡱࡗࡰ࡯ࡰࡱࡧࡧࠫ⏣"):
        bstack111l1l1ll1_opy_[bstack1ll_opy_ (u"ࠫࡷ࡫ࡳࡶ࡮ࡷࠫ⏤")] = bstack1ll_opy_ (u"ࠬࡹ࡫ࡪࡲࡳࡩࡩ࠭⏥")
        bstack111l1l1ll1_opy_[bstack1ll_opy_ (u"࠭ࡨࡰࡱ࡮ࡷࠬ⏦")] = bstack1111ll1lll_opy_[bstack1ll_opy_ (u"ࠧࡩࡱࡲ࡯ࡸ࠭⏧")]
        bstack111l1l1ll1_opy_[bstack1ll_opy_ (u"ࠨࡨ࡬ࡲ࡮ࡹࡨࡦࡦࡢࡥࡹ࠭⏨")] = bstack1111ll1lll_opy_[bstack1ll_opy_ (u"ࠩࡩ࡭ࡳ࡯ࡳࡩࡧࡧࡣࡦࡺࠧ⏩")]
    if result:
        bstack111l1l1ll1_opy_[bstack1ll_opy_ (u"ࠪࡶࡪࡹࡵ࡭ࡶࠪ⏪")] = result.outcome
        bstack111l1l1ll1_opy_[bstack1ll_opy_ (u"ࠫࡩࡻࡲࡢࡶ࡬ࡳࡳࡥࡩ࡯ࡡࡰࡷࠬ⏫")] = result.duration * 1000
        bstack111l1l1ll1_opy_[bstack1ll_opy_ (u"ࠬ࡬ࡩ࡯࡫ࡶ࡬ࡪࡪ࡟ࡢࡶࠪ⏬")] = bstack1111ll1lll_opy_[bstack1ll_opy_ (u"࠭ࡦࡪࡰ࡬ࡷ࡭࡫ࡤࡠࡣࡷࠫ⏭")]
        if result.failed:
            bstack111l1l1ll1_opy_[bstack1ll_opy_ (u"ࠧࡧࡣ࡬ࡰࡺࡸࡥࡠࡶࡼࡴࡪ࠭⏮")] = bstack1lll1111l_opy_.bstack1llllll1111_opy_(call.excinfo.typename)
            bstack111l1l1ll1_opy_[bstack1ll_opy_ (u"ࠨࡨࡤ࡭ࡱࡻࡲࡦࠩ⏯")] = bstack1lll1111l_opy_.bstack1llll1111l11_opy_(call.excinfo, result)
        bstack111l1l1ll1_opy_[bstack1ll_opy_ (u"ࠩ࡫ࡳࡴࡱࡳࠨ⏰")] = bstack1111ll1lll_opy_[bstack1ll_opy_ (u"ࠪ࡬ࡴࡵ࡫ࡴࠩ⏱")]
    if outcome:
        bstack111l1l1ll1_opy_[bstack1ll_opy_ (u"ࠫࡷ࡫ࡳࡶ࡮ࡷࠫ⏲")] = bstack111ll11ll1l_opy_(outcome)
        bstack111l1l1ll1_opy_[bstack1ll_opy_ (u"ࠬࡪࡵࡳࡣࡷ࡭ࡴࡴ࡟ࡪࡰࡢࡱࡸ࠭⏳")] = 0
        bstack111l1l1ll1_opy_[bstack1ll_opy_ (u"࠭ࡦࡪࡰ࡬ࡷ࡭࡫ࡤࡠࡣࡷࠫ⏴")] = bstack1111ll1lll_opy_[bstack1ll_opy_ (u"ࠧࡧ࡫ࡱ࡭ࡸ࡮ࡥࡥࡡࡤࡸࠬ⏵")]
        if bstack111l1l1ll1_opy_[bstack1ll_opy_ (u"ࠨࡴࡨࡷࡺࡲࡴࠨ⏶")] == bstack1ll_opy_ (u"ࠩࡩࡥ࡮ࡲࡥࡥࠩ⏷"):
            bstack111l1l1ll1_opy_[bstack1ll_opy_ (u"ࠪࡪࡦ࡯࡬ࡶࡴࡨࡣࡹࡿࡰࡦࠩ⏸")] = bstack1ll_opy_ (u"࡚ࠫࡴࡨࡢࡰࡧࡰࡪࡪࡅࡳࡴࡲࡶࠬ⏹")  # bstack1lll1l111111_opy_
            bstack111l1l1ll1_opy_[bstack1ll_opy_ (u"ࠬ࡬ࡡࡪ࡮ࡸࡶࡪ࠭⏺")] = [{bstack1ll_opy_ (u"࠭ࡢࡢࡥ࡮ࡸࡷࡧࡣࡦࠩ⏻"): [bstack1ll_opy_ (u"ࠧࡴࡱࡰࡩࠥ࡫ࡲࡳࡱࡵࠫ⏼")]}]
        bstack111l1l1ll1_opy_[bstack1ll_opy_ (u"ࠨࡪࡲࡳࡰࡹࠧ⏽")] = bstack1111ll1lll_opy_[bstack1ll_opy_ (u"ࠩ࡫ࡳࡴࡱࡳࠨ⏾")]
    return bstack111l1l1ll1_opy_
def bstack1lll1l11l11l_opy_(test, bstack111l11l11l_opy_, bstack1111l111_opy_, result, call, outcome, bstack1lll1l1111ll_opy_):
    file_path = os.path.relpath(test.fspath.strpath, start=os.getcwd())
    hook_type = bstack111l11l11l_opy_[bstack1ll_opy_ (u"ࠪ࡬ࡴࡵ࡫ࡠࡶࡼࡴࡪ࠭⏿")]
    hook_name = bstack111l11l11l_opy_[bstack1ll_opy_ (u"ࠫ࡭ࡵ࡯࡬ࡡࡱࡥࡲ࡫ࠧ␀")]
    hook_data = {
        bstack1ll_opy_ (u"ࠬࡻࡵࡪࡦࠪ␁"): bstack111l11l11l_opy_[bstack1ll_opy_ (u"࠭ࡵࡶ࡫ࡧࠫ␂")],
        bstack1ll_opy_ (u"ࠧࡵࡻࡳࡩࠬ␃"): bstack1ll_opy_ (u"ࠨࡪࡲࡳࡰ࠭␄"),
        bstack1ll_opy_ (u"ࠩࡱࡥࡲ࡫ࠧ␅"): bstack1ll_opy_ (u"ࠪࡿࢂ࠭␆").format(bstack1lllll11ll11_opy_(hook_name)),
        bstack1ll_opy_ (u"ࠫࡧࡵࡤࡺࠩ␇"): {
            bstack1ll_opy_ (u"ࠬࡲࡡ࡯ࡩࠪ␈"): bstack1ll_opy_ (u"࠭ࡰࡺࡶ࡫ࡳࡳ࠭␉"),
            bstack1ll_opy_ (u"ࠧࡤࡱࡧࡩࠬ␊"): None
        },
        bstack1ll_opy_ (u"ࠨࡵࡦࡳࡵ࡫ࠧ␋"): test.name,
        bstack1ll_opy_ (u"ࠩࡶࡧࡴࡶࡥࡴࠩ␌"): bstack1l11111lll_opy_.bstack111l111111_opy_(test, hook_name),
        bstack1ll_opy_ (u"ࠪࡪ࡮ࡲࡥࡠࡰࡤࡱࡪ࠭␍"): file_path,
        bstack1ll_opy_ (u"ࠫࡱࡵࡣࡢࡶ࡬ࡳࡳ࠭␎"): file_path,
        bstack1ll_opy_ (u"ࠬࡸࡥࡴࡷ࡯ࡸࠬ␏"): bstack1ll_opy_ (u"࠭ࡰࡦࡰࡧ࡭ࡳ࡭ࠧ␐"),
        bstack1ll_opy_ (u"ࠧࡷࡥࡢࡪ࡮ࡲࡥࡱࡣࡷ࡬ࠬ␑"): file_path,
        bstack1ll_opy_ (u"ࠨࡵࡷࡥࡷࡺࡥࡥࡡࡤࡸࠬ␒"): bstack111l11l11l_opy_[bstack1ll_opy_ (u"ࠩࡶࡸࡦࡸࡴࡦࡦࡢࡥࡹ࠭␓")],
        bstack1ll_opy_ (u"ࠪࡪࡷࡧ࡭ࡦࡹࡲࡶࡰ࠭␔"): bstack1ll_opy_ (u"ࠫࡕࡿࡴࡦࡵࡷ࠱ࡨࡻࡣࡶ࡯ࡥࡩࡷ࠭␕") if bstack1lll1l111l1l_opy_ == bstack1ll_opy_ (u"ࠬࡶࡹࡵࡧࡶࡸ࠲ࡨࡤࡥࠩ␖") else bstack1ll_opy_ (u"࠭ࡐࡺࡶࡨࡷࡹ࠭␗"),
        bstack1ll_opy_ (u"ࠧࡩࡱࡲ࡯ࡤࡺࡹࡱࡧࠪ␘"): hook_type
    }
    bstack1ll111l1111_opy_ = bstack1111l1l111_opy_(_111l11111l_opy_.get(test.nodeid, None))
    if bstack1ll111l1111_opy_:
        hook_data[bstack1ll_opy_ (u"ࠨࡶࡨࡷࡹࡥࡲࡶࡰࡢ࡭ࡩ࠭␙")] = bstack1ll111l1111_opy_
    if result:
        hook_data[bstack1ll_opy_ (u"ࠩࡵࡩࡸࡻ࡬ࡵࠩ␚")] = result.outcome
        hook_data[bstack1ll_opy_ (u"ࠪࡨࡺࡸࡡࡵ࡫ࡲࡲࡤ࡯࡮ࡠ࡯ࡶࠫ␛")] = result.duration * 1000
        hook_data[bstack1ll_opy_ (u"ࠫ࡫࡯࡮ࡪࡵ࡫ࡩࡩࡥࡡࡵࠩ␜")] = bstack111l11l11l_opy_[bstack1ll_opy_ (u"ࠬ࡬ࡩ࡯࡫ࡶ࡬ࡪࡪ࡟ࡢࡶࠪ␝")]
        if result.failed:
            hook_data[bstack1ll_opy_ (u"࠭ࡦࡢ࡫࡯ࡹࡷ࡫࡟ࡵࡻࡳࡩࠬ␞")] = bstack1lll1111l_opy_.bstack1llllll1111_opy_(call.excinfo.typename)
            hook_data[bstack1ll_opy_ (u"ࠧࡧࡣ࡬ࡰࡺࡸࡥࠨ␟")] = bstack1lll1111l_opy_.bstack1llll1111l11_opy_(call.excinfo, result)
    if outcome:
        hook_data[bstack1ll_opy_ (u"ࠨࡴࡨࡷࡺࡲࡴࠨ␠")] = bstack111ll11ll1l_opy_(outcome)
        hook_data[bstack1ll_opy_ (u"ࠩࡧࡹࡷࡧࡴࡪࡱࡱࡣ࡮ࡴ࡟࡮ࡵࠪ␡")] = 100
        hook_data[bstack1ll_opy_ (u"ࠪࡪ࡮ࡴࡩࡴࡪࡨࡨࡤࡧࡴࠨ␢")] = bstack111l11l11l_opy_[bstack1ll_opy_ (u"ࠫ࡫࡯࡮ࡪࡵ࡫ࡩࡩࡥࡡࡵࠩ␣")]
        if hook_data[bstack1ll_opy_ (u"ࠬࡸࡥࡴࡷ࡯ࡸࠬ␤")] == bstack1ll_opy_ (u"࠭ࡦࡢ࡫࡯ࡩࡩ࠭␥"):
            hook_data[bstack1ll_opy_ (u"ࠧࡧࡣ࡬ࡰࡺࡸࡥࡠࡶࡼࡴࡪ࠭␦")] = bstack1ll_opy_ (u"ࠨࡗࡱ࡬ࡦࡴࡤ࡭ࡧࡧࡉࡷࡸ࡯ࡳࠩ␧")  # bstack1lll1l111111_opy_
            hook_data[bstack1ll_opy_ (u"ࠩࡩࡥ࡮ࡲࡵࡳࡧࠪ␨")] = [{bstack1ll_opy_ (u"ࠪࡦࡦࡩ࡫ࡵࡴࡤࡧࡪ࠭␩"): [bstack1ll_opy_ (u"ࠫࡸࡵ࡭ࡦࠢࡨࡶࡷࡵࡲࠨ␪")]}]
    if bstack1lll1l1111ll_opy_:
        hook_data[bstack1ll_opy_ (u"ࠬࡸࡥࡴࡷ࡯ࡸࠬ␫")] = bstack1lll1l1111ll_opy_.result
        hook_data[bstack1ll_opy_ (u"࠭ࡤࡶࡴࡤࡸ࡮ࡵ࡮ࡠ࡫ࡱࡣࡲࡹࠧ␬")] = bstack11l1111ll11_opy_(bstack111l11l11l_opy_[bstack1ll_opy_ (u"ࠧࡴࡶࡤࡶࡹ࡫ࡤࡠࡣࡷࠫ␭")], bstack111l11l11l_opy_[bstack1ll_opy_ (u"ࠨࡨ࡬ࡲ࡮ࡹࡨࡦࡦࡢࡥࡹ࠭␮")])
        hook_data[bstack1ll_opy_ (u"ࠩࡩ࡭ࡳ࡯ࡳࡩࡧࡧࡣࡦࡺࠧ␯")] = bstack111l11l11l_opy_[bstack1ll_opy_ (u"ࠪࡪ࡮ࡴࡩࡴࡪࡨࡨࡤࡧࡴࠨ␰")]
        if hook_data[bstack1ll_opy_ (u"ࠫࡷ࡫ࡳࡶ࡮ࡷࠫ␱")] == bstack1ll_opy_ (u"ࠬ࡬ࡡࡪ࡮ࡨࡨࠬ␲"):
            hook_data[bstack1ll_opy_ (u"࠭ࡦࡢ࡫࡯ࡹࡷ࡫࡟ࡵࡻࡳࡩࠬ␳")] = bstack1lll1111l_opy_.bstack1llllll1111_opy_(bstack1lll1l1111ll_opy_.exception_type)
            hook_data[bstack1ll_opy_ (u"ࠧࡧࡣ࡬ࡰࡺࡸࡥࠨ␴")] = [{bstack1ll_opy_ (u"ࠨࡤࡤࡧࡰࡺࡲࡢࡥࡨࠫ␵"): bstack11l111l111l_opy_(bstack1lll1l1111ll_opy_.exception)}]
    return hook_data
def bstack1lll1l11llll_opy_(test, bstack1111ll1lll_opy_, bstack1111l111_opy_, result=None, call=None, outcome=None):
    logger.debug(bstack1ll_opy_ (u"ࠩࡶࡩࡳࡪ࡟ࡵࡧࡶࡸࡤࡸࡵ࡯ࡡࡨࡺࡪࡴࡴ࠻ࠢࡄࡸࡹ࡫࡭ࡱࡶ࡬ࡲ࡬ࠦࡴࡰࠢࡪࡩࡳ࡫ࡲࡢࡶࡨࠤࡹ࡫ࡳࡵࠢࡧࡥࡹࡧࠠࡧࡱࡵࠤࡪࡼࡥ࡯ࡶࡢࡸࡾࡶࡥࠡ࠯ࠣࡿࢂ࠭␶").format(bstack1111l111_opy_))
    bstack111l1l1ll1_opy_ = bstack1lll11llllll_opy_(test, bstack1111ll1lll_opy_, result, call, bstack1111l111_opy_, outcome)
    driver = getattr(test, bstack1ll_opy_ (u"ࠪࡣࡩࡸࡩࡷࡧࡵࠫ␷"), None)
    if bstack1111l111_opy_ == bstack1ll_opy_ (u"࡙ࠫ࡫ࡳࡵࡔࡸࡲࡘࡺࡡࡳࡶࡨࡨࠬ␸") and driver:
        bstack111l1l1ll1_opy_[bstack1ll_opy_ (u"ࠬ࡯࡮ࡵࡧࡪࡶࡦࡺࡩࡰࡰࡶࠫ␹")] = bstack1lll1111l_opy_.bstack111ll1111l_opy_(driver)
    if bstack1111l111_opy_ == bstack1ll_opy_ (u"࠭ࡔࡦࡵࡷࡖࡺࡴࡓ࡬࡫ࡳࡴࡪࡪࠧ␺"):
        bstack1111l111_opy_ = bstack1ll_opy_ (u"ࠧࡕࡧࡶࡸࡗࡻ࡮ࡇ࡫ࡱ࡭ࡸ࡮ࡥࡥࠩ␻")
    bstack1111ll1111_opy_ = {
        bstack1ll_opy_ (u"ࠨࡧࡹࡩࡳࡺ࡟ࡵࡻࡳࡩࠬ␼"): bstack1111l111_opy_,
        bstack1ll_opy_ (u"ࠩࡷࡩࡸࡺ࡟ࡳࡷࡱࠫ␽"): bstack111l1l1ll1_opy_
    }
    bstack1lll1111l_opy_.bstack1ll1ll111l_opy_(bstack1111ll1111_opy_)
    if bstack1111l111_opy_ == bstack1ll_opy_ (u"ࠪࡘࡪࡹࡴࡓࡷࡱࡗࡹࡧࡲࡵࡧࡧࠫ␾"):
        threading.current_thread().bstackTestMeta = {bstack1ll_opy_ (u"ࠫࡸࡺࡡࡵࡷࡶࠫ␿"): bstack1ll_opy_ (u"ࠬࡶࡥ࡯ࡦ࡬ࡲ࡬࠭⑀")}
    elif bstack1111l111_opy_ == bstack1ll_opy_ (u"࠭ࡔࡦࡵࡷࡖࡺࡴࡆࡪࡰ࡬ࡷ࡭࡫ࡤࠨ⑁"):
        threading.current_thread().bstackTestMeta = {bstack1ll_opy_ (u"ࠧࡴࡶࡤࡸࡺࡹࠧ⑂"): getattr(result, bstack1ll_opy_ (u"ࠨࡱࡸࡸࡨࡵ࡭ࡦࠩ⑃"), bstack1ll_opy_ (u"ࠩࠪ⑄"))}
def bstack1lll1l111ll1_opy_(test, bstack1111ll1lll_opy_, bstack1111l111_opy_, result=None, call=None, outcome=None, bstack1lll1l1111ll_opy_=None):
    logger.debug(bstack1ll_opy_ (u"ࠪࡷࡪࡴࡤࡠࡪࡲࡳࡰࡥࡲࡶࡰࡢࡩࡻ࡫࡮ࡵ࠼ࠣࡅࡹࡺࡥ࡮ࡲࡷ࡭ࡳ࡭ࠠࡵࡱࠣ࡫ࡪࡴࡥࡳࡣࡷࡩࠥ࡮࡯ࡰ࡭ࠣࡨࡦࡺࡡ࠭ࠢࡨࡺࡪࡴࡴࡕࡻࡳࡩࠥ࠳ࠠࡼࡿࠪ⑅").format(bstack1111l111_opy_))
    hook_data = bstack1lll1l11l11l_opy_(test, bstack1111ll1lll_opy_, bstack1111l111_opy_, result, call, outcome, bstack1lll1l1111ll_opy_)
    bstack1111ll1111_opy_ = {
        bstack1ll_opy_ (u"ࠫࡪࡼࡥ࡯ࡶࡢࡸࡾࡶࡥࠨ⑆"): bstack1111l111_opy_,
        bstack1ll_opy_ (u"ࠬ࡮࡯ࡰ࡭ࡢࡶࡺࡴࠧ⑇"): hook_data
    }
    bstack1lll1111l_opy_.bstack1ll1ll111l_opy_(bstack1111ll1111_opy_)
def bstack1111l1l111_opy_(bstack1111ll1lll_opy_):
    if not bstack1111ll1lll_opy_:
        return None
    if bstack1111ll1lll_opy_.get(bstack1ll_opy_ (u"࠭ࡴࡦࡵࡷࡣࡩࡧࡴࡢࠩ⑈"), None):
        return getattr(bstack1111ll1lll_opy_[bstack1ll_opy_ (u"ࠧࡵࡧࡶࡸࡤࡪࡡࡵࡣࠪ⑉")], bstack1ll_opy_ (u"ࠨࡷࡸ࡭ࡩ࠭⑊"), None)
    return bstack1111ll1lll_opy_.get(bstack1ll_opy_ (u"ࠩࡸࡹ࡮ࡪࠧ⑋"), None)
@pytest.fixture(autouse=True)
def second_fixture(caplog, request):
    if cli.is_running():
        cli.test_framework.track_event(cli_context, bstack1ll1ll1lll1_opy_.LOG, bstack1ll1l1ll11l_opy_.PRE, request, caplog)
    yield
    if cli.is_running():
        cli.test_framework.track_event(cli_context, bstack1ll1ll1lll1_opy_.LOG, bstack1ll1l1ll11l_opy_.POST, request, caplog)
        return # skip all existing operations
    try:
        if not bstack1lll1111l_opy_.on():
            return
        places = [bstack1ll_opy_ (u"ࠪࡷࡪࡺࡵࡱࠩ⑌"), bstack1ll_opy_ (u"ࠫࡨࡧ࡬࡭ࠩ⑍"), bstack1ll_opy_ (u"ࠬࡺࡥࡢࡴࡧࡳࡼࡴࠧ⑎")]
        logs = []
        for bstack1lll1l111lll_opy_ in places:
            records = caplog.get_records(bstack1lll1l111lll_opy_)
            bstack1lll1l1ll111_opy_ = bstack1ll_opy_ (u"࠭ࡴࡦࡵࡷࡣࡷࡻ࡮ࡠࡷࡸ࡭ࡩ࠭⑏") if bstack1lll1l111lll_opy_ == bstack1ll_opy_ (u"ࠧࡤࡣ࡯ࡰࠬ⑐") else bstack1ll_opy_ (u"ࠨࡪࡲࡳࡰࡥࡲࡶࡰࡢࡹࡺ࡯ࡤࠨ⑑")
            bstack1lll1l1l1l11_opy_ = request.node.nodeid + (bstack1ll_opy_ (u"ࠩࠪ⑒") if bstack1lll1l111lll_opy_ == bstack1ll_opy_ (u"ࠪࡧࡦࡲ࡬ࠨ⑓") else bstack1ll_opy_ (u"ࠫ࠲࠭⑔") + bstack1lll1l111lll_opy_)
            test_uuid = bstack1111l1l111_opy_(_111l11111l_opy_.get(bstack1lll1l1l1l11_opy_, None))
            if not test_uuid:
                continue
            for record in records:
                if bstack111l1llllll_opy_(record.message):
                    continue
                logs.append({
                    bstack1ll_opy_ (u"ࠬࡺࡩ࡮ࡧࡶࡸࡦࡳࡰࠨ⑕"): bstack111llll11l1_opy_(record.created).isoformat() + bstack1ll_opy_ (u"࡚࠭ࠨ⑖"),
                    bstack1ll_opy_ (u"ࠧ࡭ࡧࡹࡩࡱ࠭⑗"): record.levelname,
                    bstack1ll_opy_ (u"ࠨ࡯ࡨࡷࡸࡧࡧࡦࠩ⑘"): record.message,
                    bstack1lll1l1ll111_opy_: test_uuid
                })
        if len(logs) > 0:
            bstack1lll1111l_opy_.bstack11ll1111l_opy_(logs)
    except Exception as err:
        print(bstack1ll_opy_ (u"ࠩࡈࡼࡨ࡫ࡰࡵ࡫ࡲࡲࠥ࡯࡮ࠡࡵࡨࡧࡴࡴࡤࡠࡨ࡬ࡼࡹࡻࡲࡦ࠼ࠣࡿࢂ࠭⑙"), str(err))
def bstack1lll11l11_opy_(sequence, driver_command, response=None, driver = None, args = None):
    global bstack11l1l1l11_opy_
    bstack11lll11l_opy_ = bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠪ࡭ࡸࡇ࠱࠲ࡻࡗࡩࡸࡺࠧ⑚"), None) and bstack1l11l11l_opy_(
            threading.current_thread(), bstack1ll_opy_ (u"ࠫࡦ࠷࠱ࡺࡒ࡯ࡥࡹ࡬࡯ࡳ࡯ࠪ⑛"), None)
    bstack111llllll_opy_ = getattr(driver, bstack1ll_opy_ (u"ࠬࡨࡳࡵࡣࡦ࡯ࡆ࠷࠱ࡺࡕ࡫ࡳࡺࡲࡤࡔࡥࡤࡲࠬ⑜"), None) != None and getattr(driver, bstack1ll_opy_ (u"࠭ࡢࡴࡶࡤࡧࡰࡇ࠱࠲ࡻࡖ࡬ࡴࡻ࡬ࡥࡕࡦࡥࡳ࠭⑝"), None) == True
    if sequence == bstack1ll_opy_ (u"ࠧࡣࡧࡩࡳࡷ࡫ࠧ⑞") and driver != None:
      if not bstack11l1l1l11_opy_ and bstack1l1ll111lll_opy_() and bstack1ll_opy_ (u"ࠨࡣࡦࡧࡪࡹࡳࡪࡤ࡬ࡰ࡮ࡺࡹࠨ⑟") in CONFIG and CONFIG[bstack1ll_opy_ (u"ࠩࡤࡧࡨ࡫ࡳࡴ࡫ࡥ࡭ࡱ࡯ࡴࡺࠩ①")] == True and bstack1111l1ll1_opy_.bstack111llll1l1_opy_(driver_command) and (bstack111llllll_opy_ or bstack11lll11l_opy_) and not bstack111111l1l_opy_(args):
        try:
          bstack11l1l1l11_opy_ = True
          logger.debug(bstack1ll_opy_ (u"ࠪࡔࡪࡸࡦࡰࡴࡰ࡭ࡳ࡭ࠠࡴࡥࡤࡲࠥ࡬࡯ࡳࠢࡾࢁࠬ②").format(driver_command))
          logger.debug(perform_scan(driver, driver_command=driver_command))
        except Exception as err:
          logger.debug(bstack1ll_opy_ (u"ࠫࡋࡧࡩ࡭ࡧࡧࠤࡹࡵࠠࡱࡧࡵࡪࡴࡸ࡭ࠡࡵࡦࡥࡳࠦࡻࡾࠩ③").format(str(err)))
        bstack11l1l1l11_opy_ = False
    if sequence == bstack1ll_opy_ (u"ࠬࡧࡦࡵࡧࡵࠫ④"):
        if driver_command == bstack1ll_opy_ (u"࠭ࡳࡤࡴࡨࡩࡳࡹࡨࡰࡶࠪ⑤"):
            bstack1lll1111l_opy_.bstack1l1l1ll111_opy_({
                bstack1ll_opy_ (u"ࠧࡪ࡯ࡤ࡫ࡪ࠭⑥"): response[bstack1ll_opy_ (u"ࠨࡸࡤࡰࡺ࡫ࠧ⑦")],
                bstack1ll_opy_ (u"ࠩࡷࡩࡸࡺ࡟ࡳࡷࡱࡣࡺࡻࡩࡥࠩ⑧"): store[bstack1ll_opy_ (u"ࠪࡧࡺࡸࡲࡦࡰࡷࡣࡹ࡫ࡳࡵࡡࡸࡹ࡮ࡪࠧ⑨")]
            })
def bstack11lll1l11_opy_():
    global bstack1llll11lll_opy_
    bstack11l1l1lll1_opy_.bstack1l11l1l1ll_opy_()
    logging.shutdown()
    bstack1lll1111l_opy_.bstack1111lll111_opy_()
    for driver in bstack1llll11lll_opy_:
        try:
            driver.quit()
        except Exception as e:
            pass
def bstack1lll1l11ll11_opy_(*args):
    global bstack1llll11lll_opy_
    bstack1lll1111l_opy_.bstack1111lll111_opy_()
    for driver in bstack1llll11lll_opy_:
        try:
            driver.quit()
        except Exception as e:
            pass
@measure(event_name=EVENTS.bstack11l111lll_opy_, stage=STAGE.bstack1l1lll1ll1_opy_, bstack1l1l11ll_opy_=bstack1llll1111l_opy_)
def bstack1ll11l1ll1_opy_(self, *args, **kwargs):
    bstack1ll111111l_opy_ = bstack11ll1l1lll_opy_(self, *args, **kwargs)
    bstack11ll11lll_opy_ = getattr(threading.current_thread(), bstack1ll_opy_ (u"ࠫࡧࡹࡴࡢࡥ࡮ࡘࡪࡹࡴࡎࡧࡷࡥࠬ⑩"), None)
    if bstack11ll11lll_opy_ and bstack11ll11lll_opy_.get(bstack1ll_opy_ (u"ࠬࡹࡴࡢࡶࡸࡷࠬ⑪"), bstack1ll_opy_ (u"࠭ࠧ⑫")) == bstack1ll_opy_ (u"ࠧࡱࡧࡱࡨ࡮ࡴࡧࠨ⑬"):
        bstack1lll1111l_opy_.bstack11ll1l1ll1_opy_(self)
    return bstack1ll111111l_opy_
@measure(event_name=EVENTS.bstack11ll1l11ll_opy_, stage=STAGE.bstack11l11l1l11_opy_, bstack1l1l11ll_opy_=bstack1llll1111l_opy_)
def bstack1l1lllll_opy_(framework_name):
    from bstack_utils.config import Config
    bstack1ll1l1l111_opy_ = Config.bstack11lll1111_opy_()
    if bstack1ll1l1l111_opy_.get_property(bstack1ll_opy_ (u"ࠨࡤࡶࡸࡦࡩ࡫ࡠ࡯ࡲࡨࡤࡩࡡ࡭࡮ࡨࡨࠬ⑭")):
        return
    bstack1ll1l1l111_opy_.bstack111ll1ll1_opy_(bstack1ll_opy_ (u"ࠩࡥࡷࡹࡧࡣ࡬ࡡࡰࡳࡩࡥࡣࡢ࡮࡯ࡩࡩ࠭⑮"), True)
    global bstack11l11ll111_opy_
    global bstack111lllll_opy_
    bstack11l11ll111_opy_ = framework_name
    logger.info(bstack111lll11l_opy_.format(bstack11l11ll111_opy_.split(bstack1ll_opy_ (u"ࠪ࠱ࠬ⑯"))[0]))
    try:
        from selenium import webdriver
        from selenium.webdriver.common.service import Service
        from selenium.webdriver.remote.webdriver import WebDriver
        if bstack1l1ll111lll_opy_():
            Service.start = bstack1l1l11l11_opy_
            Service.stop = bstack11111111l_opy_
            webdriver.Remote.get = bstack1l11l11111_opy_
            webdriver.Remote.__init__ = bstack1l1l1l111_opy_
            if not isinstance(os.getenv(bstack1ll_opy_ (u"ࠫࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡔ࡞࡚ࡅࡔࡖࡢࡔࡆࡘࡁࡍࡎࡈࡐࠬ⑰")), str):
                return
            WebDriver.quit = bstack1ll1lll1_opy_
            WebDriver.getAccessibilityResults = getAccessibilityResults
            WebDriver.get_accessibility_results = getAccessibilityResults
            WebDriver.getAccessibilityResultsSummary = getAccessibilityResultsSummary
            WebDriver.get_accessibility_results_summary = getAccessibilityResultsSummary
            WebDriver.performScan = perform_scan
            WebDriver.perform_scan = perform_scan
        elif bstack1lll1111l_opy_.on():
            webdriver.Remote.__init__ = bstack1ll11l1ll1_opy_
        bstack111lllll_opy_ = True
    except Exception as e:
        pass
    if os.environ.get(bstack1ll_opy_ (u"࡙ࠬࡅࡍࡇࡑࡍ࡚ࡓ࡟ࡐࡔࡢࡔࡑࡇ࡙ࡘࡔࡌࡋࡍ࡚࡟ࡊࡐࡖࡘࡆࡒࡌࡆࡆࠪ⑱")):
        bstack111lllll_opy_ = eval(os.environ.get(bstack1ll_opy_ (u"࠭ࡓࡆࡎࡈࡒࡎ࡛ࡍࡠࡑࡕࡣࡕࡒࡁ࡚࡙ࡕࡍࡌࡎࡔࡠࡋࡑࡗ࡙ࡇࡌࡍࡇࡇࠫ⑲")))
    if not bstack111lllll_opy_:
        bstack1llll1ll1_opy_(bstack1ll_opy_ (u"ࠢࡑࡣࡦ࡯ࡦ࡭ࡥࡴࠢࡱࡳࡹࠦࡩ࡯ࡵࡷࡥࡱࡲࡥࡥࠤ⑳"), bstack11l1lll11_opy_)
    if bstack111l1111_opy_():
        try:
            from selenium.webdriver.remote.remote_connection import RemoteConnection
            if hasattr(RemoteConnection, bstack1ll_opy_ (u"ࠨࡡࡪࡩࡹࡥࡰࡳࡱࡻࡽࡤࡻࡲ࡭ࠩ⑴")) and callable(getattr(RemoteConnection, bstack1ll_opy_ (u"ࠩࡢ࡫ࡪࡺ࡟ࡱࡴࡲࡼࡾࡥࡵࡳ࡮ࠪ⑵"))):
                RemoteConnection._get_proxy_url = bstack11ll111ll1_opy_
            else:
                from selenium.webdriver.remote.client_config import ClientConfig
                ClientConfig.get_proxy_url = bstack11ll111ll1_opy_
        except Exception as e:
            logger.error(bstack1ll1111ll_opy_.format(str(e)))
    if bstack1ll_opy_ (u"ࠪࡴࡾࡺࡥࡴࡶࠪ⑶") in str(framework_name).lower():
        if not bstack1l1ll111lll_opy_():
            return
        try:
            from pytest_selenium import pytest_selenium
            from _pytest.config import Config
            pytest_selenium.pytest_report_header = bstack1lll111l1_opy_
            from pytest_selenium.drivers import browserstack
            browserstack.pytest_selenium_runtest_makereport = bstack1llllll1l1_opy_
            Config.getoption = bstack1l1l1lll1l_opy_
        except Exception as e:
            pass
        try:
            from pytest_bdd import reporting
            reporting.runtest_makereport = bstack111l111ll_opy_
        except Exception as e:
            pass
@measure(event_name=EVENTS.bstack1l1ll1l11l_opy_, stage=STAGE.bstack1l1lll1ll1_opy_, bstack1l1l11ll_opy_=bstack1llll1111l_opy_)
def bstack1ll1lll1_opy_(self):
    global bstack11l11ll111_opy_
    global bstack1111l1l11_opy_
    global bstack1l1111ll1_opy_
    try:
        if bstack1ll_opy_ (u"ࠫࡵࡿࡴࡦࡵࡷࠫ⑷") in bstack11l11ll111_opy_ and self.session_id != None and bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠬࡺࡥࡴࡶࡖࡸࡦࡺࡵࡴࠩ⑸"), bstack1ll_opy_ (u"࠭ࠧ⑹")) != bstack1ll_opy_ (u"ࠧࡴ࡭࡬ࡴࡵ࡫ࡤࠨ⑺"):
            bstack1l1ll1l111_opy_ = bstack1ll_opy_ (u"ࠨࡲࡤࡷࡸ࡫ࡤࠨ⑻") if len(threading.current_thread().bstackTestErrorMessages) == 0 else bstack1ll_opy_ (u"ࠩࡩࡥ࡮ࡲࡥࡥࠩ⑼")
            bstack1l1lll1l_opy_(logger, True)
            if os.environ.get(bstack1ll_opy_ (u"ࠪࡔ࡞࡚ࡅࡔࡖࡢࡘࡊ࡙ࡔࡠࡐࡄࡑࡊ࠭⑽"), None):
                self.execute_script(
                    bstack1ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭ࡢࡩࡽ࡫ࡣࡶࡶࡲࡶ࠿ࠦࡻࠣࡣࡦࡸ࡮ࡵ࡮ࠣ࠼ࠣࠦࡸ࡫ࡴࡔࡧࡶࡷ࡮ࡵ࡮ࡏࡣࡰࡩࠧ࠲ࠠࠣࡣࡵ࡫ࡺࡳࡥ࡯ࡶࡶࠦ࠿ࠦࡻࠣࡰࡤࡱࡪࠨ࠺ࠡࠩ⑾") + json.dumps(
                        os.environ.get(bstack1ll_opy_ (u"ࠬࡖ࡙ࡕࡇࡖࡘࡤ࡚ࡅࡔࡖࡢࡒࡆࡓࡅࠨ⑿"))) + bstack1ll_opy_ (u"࠭ࡽࡾࠩ⒀"))
            if self != None:
                bstack11ll11111l_opy_(self, bstack1l1ll1l111_opy_, bstack1ll_opy_ (u"ࠧ࠭ࠢࠪ⒁").join(threading.current_thread().bstackTestErrorMessages))
        if not cli.bstack1lll11ll1ll_opy_(bstack1ll1l111l1l_opy_):
            item = store.get(bstack1ll_opy_ (u"ࠨࡥࡸࡶࡷ࡫࡮ࡵࡡࡷࡩࡸࡺ࡟ࡪࡶࡨࡱࠬ⒂"), None)
            if item is not None and bstack1l11l11l_opy_(threading.current_thread(), bstack1ll_opy_ (u"ࠩࡤ࠵࠶ࡿࡐ࡭ࡣࡷࡪࡴࡸ࡭ࠨ⒃"), None):
                bstack1l111ll1l_opy_.bstack1l1l11111_opy_(self, bstack111l11111_opy_, logger, item)
        threading.current_thread().testStatus = bstack1ll_opy_ (u"ࠪࠫ⒄")
    except Exception as e:
        logger.debug(bstack1ll_opy_ (u"ࠦࡊࡸࡲࡰࡴࠣࡻ࡭࡯࡬ࡦࠢࡰࡥࡷࡱࡩ࡯ࡩࠣࡷࡹࡧࡴࡶࡵ࠽ࠤࠧ⒅") + str(e))
    bstack1l1111ll1_opy_(self)
    self.session_id = None
@measure(event_name=EVENTS.bstack1l1lllll1_opy_, stage=STAGE.bstack1l1lll1ll1_opy_, bstack1l1l11ll_opy_=bstack1llll1111l_opy_)
def bstack1l1l1l111_opy_(self, command_executor,
             desired_capabilities=None, browser_profile=None, proxy=None,
             keep_alive=True, file_detector=None, options=None):
    global CONFIG
    global bstack1111l1l11_opy_
    global bstack1llll1111l_opy_
    global bstack11lllllll1_opy_
    global bstack11l11ll111_opy_
    global bstack11ll1l1lll_opy_
    global bstack1llll11lll_opy_
    global bstack1ll111lll_opy_
    global bstack1l1l1ll1l1_opy_
    global bstack111l11111_opy_
    CONFIG[bstack1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮ࡗࡉࡑࠧ⒆")] = str(bstack11l11ll111_opy_) + str(__version__)
    command_executor = bstack111ll1111_opy_(bstack1ll111lll_opy_, CONFIG)
    logger.debug(bstack11l1llllll_opy_.format(command_executor))
    proxy = bstack111llll1ll_opy_(CONFIG, proxy)
    bstack11l1l1l1_opy_ = 0
    try:
        if bstack11lllllll1_opy_ is True:
            bstack11l1l1l1_opy_ = int(os.environ.get(bstack1ll_opy_ (u"࠭ࡂࡓࡑ࡚ࡗࡊࡘࡓࡕࡃࡆࡏࡤࡖࡌࡂࡖࡉࡓࡗࡓ࡟ࡊࡐࡇࡉ࡝࠭⒇")))
    except:
        bstack11l1l1l1_opy_ = 0
    bstack1l1l111ll1_opy_ = bstack1l1111llll_opy_(CONFIG, bstack11l1l1l1_opy_)
    logger.debug(bstack11ll1l1l_opy_.format(str(bstack1l1l111ll1_opy_)))
    bstack111l11111_opy_ = CONFIG.get(bstack1ll_opy_ (u"ࠧࡱ࡮ࡤࡸ࡫ࡵࡲ࡮ࡵࠪ⒈"))[bstack11l1l1l1_opy_]
    if bstack1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱࡌࡰࡥࡤࡰࠬ⒉") in CONFIG and CONFIG[bstack1ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫ࡍࡱࡦࡥࡱ࠭⒊")]:
        bstack1l1l1111ll_opy_(bstack1l1l111ll1_opy_, bstack1l1l1ll1l1_opy_)
    if bstack1llll1l11_opy_.bstack1l111lll1l_opy_(CONFIG, bstack11l1l1l1_opy_) and bstack1llll1l11_opy_.bstack11111l1l1_opy_(bstack1l1l111ll1_opy_, options, desired_capabilities):
        threading.current_thread().a11yPlatform = True
        if not cli.bstack1lll11ll1ll_opy_(bstack1ll1l111l1l_opy_):
            bstack1llll1l11_opy_.set_capabilities(bstack1l1l111ll1_opy_, CONFIG)
    if desired_capabilities:
        bstack1l11llll_opy_ = bstack11l1ll1l1l_opy_(desired_capabilities)
        bstack1l11llll_opy_[bstack1ll_opy_ (u"ࠪࡹࡸ࡫ࡗ࠴ࡅࠪ⒋")] = bstack1l1111l11l_opy_(CONFIG)
        bstack1l11llll1_opy_ = bstack1l1111llll_opy_(bstack1l11llll_opy_)
        if bstack1l11llll1_opy_:
            bstack1l1l111ll1_opy_ = update(bstack1l11llll1_opy_, bstack1l1l111ll1_opy_)
        desired_capabilities = None
    if options:
        bstack1lll1ll1l1_opy_(options, bstack1l1l111ll1_opy_)
    if not options:
        options = bstack1l1ll111_opy_(bstack1l1l111ll1_opy_)
    if proxy and bstack11l11111l1_opy_() >= version.parse(bstack1ll_opy_ (u"ࠫ࠹࠴࠱࠱࠰࠳ࠫ⒌")):
        options.proxy(proxy)
    if options and bstack11l11111l1_opy_() >= version.parse(bstack1ll_opy_ (u"ࠬ࠹࠮࠹࠰࠳ࠫ⒍")):
        desired_capabilities = None
    if (
            not options and not desired_capabilities
    ) or (
            bstack11l11111l1_opy_() < version.parse(bstack1ll_opy_ (u"࠭࠳࠯࠺࠱࠴ࠬ⒎")) and not desired_capabilities
    ):
        desired_capabilities = {}
        desired_capabilities.update(bstack1l1l111ll1_opy_)
    logger.info(bstack1l1ll1ll1_opy_)
    bstack11ll1llll1_opy_.end(EVENTS.bstack11ll1l11ll_opy_.value, EVENTS.bstack11ll1l11ll_opy_.value + bstack1ll_opy_ (u"ࠢ࠻ࡵࡷࡥࡷࡺࠢ⒏"),
                               EVENTS.bstack11ll1l11ll_opy_.value + bstack1ll_opy_ (u"ࠣ࠼ࡨࡲࡩࠨ⒐"), True, None)
    try:
        if bstack11l11111l1_opy_() >= version.parse(bstack1ll_opy_ (u"ࠩ࠷࠲࠶࠶࠮࠱ࠩ⒑")):
            bstack11ll1l1lll_opy_(self, command_executor=command_executor,
                      options=options, keep_alive=keep_alive, file_detector=file_detector, *args, **kwargs)
        elif bstack11l11111l1_opy_() >= version.parse(bstack1ll_opy_ (u"ࠪ࠷࠳࠾࠮࠱ࠩ⒒")):
            bstack11ll1l1lll_opy_(self, command_executor=command_executor,
                      desired_capabilities=desired_capabilities, options=options,
                      browser_profile=browser_profile, proxy=proxy,
                      keep_alive=keep_alive, file_detector=file_detector)
        elif bstack11l11111l1_opy_() >= version.parse(bstack1ll_opy_ (u"ࠫ࠷࠴࠵࠴࠰࠳ࠫ⒓")):
            bstack11ll1l1lll_opy_(self, command_executor=command_executor,
                      desired_capabilities=desired_capabilities,
                      browser_profile=browser_profile, proxy=proxy,
                      keep_alive=keep_alive, file_detector=file_detector)
        else:
            bstack11ll1l1lll_opy_(self, command_executor=command_executor,
                      desired_capabilities=desired_capabilities,
                      browser_profile=browser_profile, proxy=proxy,
                      keep_alive=keep_alive)
    except Exception as bstack1l1111l111_opy_:
        logger.error(bstack1111ll1l1_opy_.format(bstack1ll_opy_ (u"ࠬࡈࡲࡰࡹࡶࡩࡷ࡙ࡴࡢࡥ࡮ࠫ⒔"), str(bstack1l1111l111_opy_)))
        raise bstack1l1111l111_opy_
    try:
        bstack1l1llllll_opy_ = bstack1ll_opy_ (u"࠭ࠧ⒕")
        if bstack11l11111l1_opy_() >= version.parse(bstack1ll_opy_ (u"ࠧ࠵࠰࠳࠲࠵ࡨ࠱ࠨ⒖")):
            bstack1l1llllll_opy_ = self.caps.get(bstack1ll_opy_ (u"ࠣࡱࡳࡸ࡮ࡳࡡ࡭ࡊࡸࡦ࡚ࡸ࡬ࠣ⒗"))
        else:
            bstack1l1llllll_opy_ = self.capabilities.get(bstack1ll_opy_ (u"ࠤࡲࡴࡹ࡯࡭ࡢ࡮ࡋࡹࡧ࡛ࡲ࡭ࠤ⒘"))
        if bstack1l1llllll_opy_:
            bstack1l11l1lll1_opy_(bstack1l1llllll_opy_)
            if bstack11l11111l1_opy_() <= version.parse(bstack1ll_opy_ (u"ࠪ࠷࠳࠷࠳࠯࠲ࠪ⒙")):
                self.command_executor._url = bstack1ll_opy_ (u"ࠦ࡭ࡺࡴࡱ࠼࠲࠳ࠧ⒚") + bstack1ll111lll_opy_ + bstack1ll_opy_ (u"ࠧࡀ࠸࠱࠱ࡺࡨ࠴࡮ࡵࡣࠤ⒛")
            else:
                self.command_executor._url = bstack1ll_opy_ (u"ࠨࡨࡵࡶࡳࡷ࠿࠵࠯ࠣ⒜") + bstack1l1llllll_opy_ + bstack1ll_opy_ (u"ࠢ࠰ࡹࡧ࠳࡭ࡻࡢࠣ⒝")
            logger.debug(bstack1ll11lllll_opy_.format(bstack1l1llllll_opy_))
        else:
            logger.debug(bstack1ll1l11l1_opy_.format(bstack1ll_opy_ (u"ࠣࡑࡳࡸ࡮ࡳࡡ࡭ࠢࡋࡹࡧࠦ࡮ࡰࡶࠣࡪࡴࡻ࡮ࡥࠤ⒞")))
    except Exception as e:
        logger.debug(bstack1ll1l11l1_opy_.format(e))
    bstack1111l1l11_opy_ = self.session_id
    if bstack1ll_opy_ (u"ࠩࡳࡽࡹ࡫ࡳࡵࠩ⒟") in bstack11l11ll111_opy_:
        threading.current_thread().bstackSessionId = self.session_id
        threading.current_thread().bstackSessionDriver = self
        threading.current_thread().bstackTestErrorMessages = []
        item = store.get(bstack1ll_opy_ (u"ࠪࡧࡺࡸࡲࡦࡰࡷࡣࡹ࡫ࡳࡵࡡ࡬ࡸࡪࡳࠧ⒠"), None)
        if item:
            bstack1lll1l1ll1ll_opy_ = getattr(item, bstack1ll_opy_ (u"ࠫࡤࡺࡥࡴࡶࡢࡧࡦࡹࡥࡠࡵࡷࡥࡷࡺࡥࡥࠩ⒡"), False)
            if not getattr(item, bstack1ll_opy_ (u"ࠬࡥࡤࡳ࡫ࡹࡩࡷ࠭⒢"), None) and bstack1lll1l1ll1ll_opy_:
                setattr(store[bstack1ll_opy_ (u"࠭ࡣࡶࡴࡵࡩࡳࡺ࡟ࡵࡧࡶࡸࡤ࡯ࡴࡦ࡯ࠪ⒣")], bstack1ll_opy_ (u"ࠧࡠࡦࡵ࡭ࡻ࡫ࡲࠨ⒤"), self)
        bstack11ll11lll_opy_ = getattr(threading.current_thread(), bstack1ll_opy_ (u"ࠨࡤࡶࡸࡦࡩ࡫ࡕࡧࡶࡸࡒ࡫ࡴࡢࠩ⒥"), None)
        if bstack11ll11lll_opy_ and bstack11ll11lll_opy_.get(bstack1ll_opy_ (u"ࠩࡶࡸࡦࡺࡵࡴࠩ⒦"), bstack1ll_opy_ (u"ࠪࠫ⒧")) == bstack1ll_opy_ (u"ࠫࡵ࡫࡮ࡥ࡫ࡱ࡫ࠬ⒨"):
            bstack1lll1111l_opy_.bstack11ll1l1ll1_opy_(self)
    bstack1llll11lll_opy_.append(self)
    if bstack1ll_opy_ (u"ࠬࡶ࡬ࡢࡶࡩࡳࡷࡳࡳࠨ⒩") in CONFIG and bstack1ll_opy_ (u"࠭ࡳࡦࡵࡶ࡭ࡴࡴࡎࡢ࡯ࡨࠫ⒪") in CONFIG[bstack1ll_opy_ (u"ࠧࡱ࡮ࡤࡸ࡫ࡵࡲ࡮ࡵࠪ⒫")][bstack11l1l1l1_opy_]:
        bstack1llll1111l_opy_ = CONFIG[bstack1ll_opy_ (u"ࠨࡲ࡯ࡥࡹ࡬࡯ࡳ࡯ࡶࠫ⒬")][bstack11l1l1l1_opy_][bstack1ll_opy_ (u"ࠩࡶࡩࡸࡹࡩࡰࡰࡑࡥࡲ࡫ࠧ⒭")]
    logger.debug(bstack11llll1l11_opy_.format(bstack1111l1l11_opy_))
@measure(event_name=EVENTS.bstack1ll1l111ll_opy_, stage=STAGE.bstack1l1lll1ll1_opy_, bstack1l1l11ll_opy_=bstack1llll1111l_opy_)
def bstack1l11l11111_opy_(self, url):
    global bstack1ll11l11l1_opy_
    global CONFIG
    try:
        bstack111llll1l_opy_(url, CONFIG, logger)
    except Exception as err:
        logger.debug(bstack1llll1l1l1_opy_.format(str(err)))
    try:
        bstack1ll11l11l1_opy_(self, url)
    except Exception as e:
        try:
            bstack11lllll1ll_opy_ = str(e)
            if any(err_msg in bstack11lllll1ll_opy_ for err_msg in bstack1ll11ll111_opy_):
                bstack111llll1l_opy_(url, CONFIG, logger, True)
        except Exception as err:
            logger.debug(bstack1llll1l1l1_opy_.format(str(err)))
        raise e
def bstack1l11ll11ll_opy_(item, when):
    global bstack1l111l1ll_opy_
    try:
        bstack1l111l1ll_opy_(item, when)
    except Exception as e:
        pass
def bstack111l111ll_opy_(item, call, rep):
    global bstack11lll1l111_opy_
    global bstack1llll11lll_opy_
    name = bstack1ll_opy_ (u"ࠪࠫ⒮")
    try:
        if rep.when == bstack1ll_opy_ (u"ࠫࡨࡧ࡬࡭ࠩ⒯"):
            bstack1111l1l11_opy_ = threading.current_thread().bstackSessionId
            skipSessionName = item.config.getoption(bstack1ll_opy_ (u"ࠬࡹ࡫ࡪࡲࡖࡩࡸࡹࡩࡰࡰࡑࡥࡲ࡫ࠧ⒰"))
            try:
                if (str(skipSessionName).lower() != bstack1ll_opy_ (u"࠭ࡴࡳࡷࡨࠫ⒱")):
                    name = str(rep.nodeid)
                    bstack1111l11l1_opy_ = bstack1l11ll1l1_opy_(bstack1ll_opy_ (u"ࠧࡴࡧࡷࡗࡪࡹࡳࡪࡱࡱࡒࡦࡳࡥࠨ⒲"), name, bstack1ll_opy_ (u"ࠨࠩ⒳"), bstack1ll_opy_ (u"ࠩࠪ⒴"), bstack1ll_opy_ (u"ࠪࠫ⒵"), bstack1ll_opy_ (u"ࠫࠬⒶ"))
                    os.environ[bstack1ll_opy_ (u"ࠬࡖ࡙ࡕࡇࡖࡘࡤ࡚ࡅࡔࡖࡢࡒࡆࡓࡅࠨⒷ")] = name
                    for driver in bstack1llll11lll_opy_:
                        if bstack1111l1l11_opy_ == driver.session_id:
                            driver.execute_script(bstack1111l11l1_opy_)
            except Exception as e:
                logger.debug(bstack1ll_opy_ (u"࠭ࡅࡳࡴࡲࡶࠥ࡯࡮ࠡࡵࡨࡸࡹ࡯࡮ࡨࠢࡶࡩࡸࡹࡩࡰࡰࡑࡥࡲ࡫ࠠࡧࡱࡵࠤࡵࡿࡴࡦࡵࡷ࠱ࡧࡪࡤࠡࡵࡨࡷࡸ࡯࡯࡯࠼ࠣࡿࢂ࠭Ⓒ").format(str(e)))
            try:
                bstack1l1111l1l1_opy_(rep.outcome.lower())
                if rep.outcome.lower() != bstack1ll_opy_ (u"ࠧࡴ࡭࡬ࡴࡵ࡫ࡤࠨⒹ"):
                    status = bstack1ll_opy_ (u"ࠨࡨࡤ࡭ࡱ࡫ࡤࠨⒺ") if rep.outcome.lower() == bstack1ll_opy_ (u"ࠩࡩࡥ࡮ࡲࡥࡥࠩⒻ") else bstack1ll_opy_ (u"ࠪࡴࡦࡹࡳࡦࡦࠪⒼ")
                    reason = bstack1ll_opy_ (u"ࠫࠬⒽ")
                    if status == bstack1ll_opy_ (u"ࠬ࡬ࡡࡪ࡮ࡨࡨࠬⒾ"):
                        reason = rep.longrepr.reprcrash.message
                        if (not threading.current_thread().bstackTestErrorMessages):
                            threading.current_thread().bstackTestErrorMessages = []
                        threading.current_thread().bstackTestErrorMessages.append(reason)
                    level = bstack1ll_opy_ (u"࠭ࡩ࡯ࡨࡲࠫⒿ") if status == bstack1ll_opy_ (u"ࠧࡱࡣࡶࡷࡪࡪࠧⓀ") else bstack1ll_opy_ (u"ࠨࡧࡵࡶࡴࡸࠧⓁ")
                    data = name + bstack1ll_opy_ (u"ࠩࠣࡴࡦࡹࡳࡦࡦࠤࠫⓂ") if status == bstack1ll_opy_ (u"ࠪࡴࡦࡹࡳࡦࡦࠪⓃ") else name + bstack1ll_opy_ (u"ࠫࠥ࡬ࡡࡪ࡮ࡨࡨࠦࠦࠧⓄ") + reason
                    bstack1l1l1lll11_opy_ = bstack1l11ll1l1_opy_(bstack1ll_opy_ (u"ࠬࡧ࡮࡯ࡱࡷࡥࡹ࡫ࠧⓅ"), bstack1ll_opy_ (u"࠭ࠧⓆ"), bstack1ll_opy_ (u"ࠧࠨⓇ"), bstack1ll_opy_ (u"ࠨࠩⓈ"), level, data)
                    for driver in bstack1llll11lll_opy_:
                        if bstack1111l1l11_opy_ == driver.session_id:
                            driver.execute_script(bstack1l1l1lll11_opy_)
            except Exception as e:
                logger.debug(bstack1ll_opy_ (u"ࠩࡈࡶࡷࡵࡲࠡ࡫ࡱࠤࡸ࡫ࡴࡵ࡫ࡱ࡫ࠥࡹࡥࡴࡵ࡬ࡳࡳࠦࡣࡰࡰࡷࡩࡽࡺࠠࡧࡱࡵࠤࡵࡿࡴࡦࡵࡷ࠱ࡧࡪࡤࠡࡵࡨࡷࡸ࡯࡯࡯࠼ࠣࡿࢂ࠭Ⓣ").format(str(e)))
    except Exception as e:
        logger.debug(bstack1ll_opy_ (u"ࠪࡉࡷࡸ࡯ࡳࠢ࡬ࡲࠥ࡭ࡥࡵࡶ࡬ࡲ࡬ࠦࡳࡵࡣࡷࡩࠥ࡯࡮ࠡࡲࡼࡸࡪࡹࡴ࠮ࡤࡧࡨࠥࡺࡥࡴࡶࠣࡷࡹࡧࡴࡶࡵ࠽ࠤࢀࢃࠧⓊ").format(str(e)))
    bstack11lll1l111_opy_(item, call, rep)
notset = Notset()
def bstack1l1l1lll1l_opy_(self, name: str, default=notset, skip: bool = False):
    global bstack1l11lll111_opy_
    if str(name).lower() == bstack1ll_opy_ (u"ࠫࡩࡸࡩࡷࡧࡵࠫⓋ"):
        return bstack1ll_opy_ (u"ࠧࡈࡲࡰࡹࡶࡩࡷ࡙ࡴࡢࡥ࡮ࠦⓌ")
    else:
        return bstack1l11lll111_opy_(self, name, default, skip)
def bstack11ll111ll1_opy_(self):
    global CONFIG
    global bstack1ll11l1111_opy_
    try:
        proxy = bstack1ll11ll11l_opy_(CONFIG)
        if proxy:
            if proxy.endswith(bstack1ll_opy_ (u"࠭࠮ࡱࡣࡦࠫⓍ")):
                proxies = bstack1ll1ll11l_opy_(proxy, bstack111ll1111_opy_())
                if len(proxies) > 0:
                    protocol, bstack11l1ll111l_opy_ = proxies.popitem()
                    if bstack1ll_opy_ (u"ࠢ࠻࠱࠲ࠦⓎ") in bstack11l1ll111l_opy_:
                        return bstack11l1ll111l_opy_
                    else:
                        return bstack1ll_opy_ (u"ࠣࡪࡷࡸࡵࡀ࠯࠰ࠤⓏ") + bstack11l1ll111l_opy_
            else:
                return proxy
    except Exception as e:
        logger.error(bstack1ll_opy_ (u"ࠤࡈࡶࡷࡵࡲࠡ࡫ࡱࠤࡸ࡫ࡴࡵ࡫ࡱ࡫ࠥࡶࡲࡰࡺࡼࠤࡺࡸ࡬ࠡ࠼ࠣࡿࢂࠨⓐ").format(str(e)))
    return bstack1ll11l1111_opy_(self)
def bstack111l1111_opy_():
    return (bstack1ll_opy_ (u"ࠪ࡬ࡹࡺࡰࡑࡴࡲࡼࡾ࠭ⓑ") in CONFIG or bstack1ll_opy_ (u"ࠫ࡭ࡺࡴࡱࡵࡓࡶࡴࡾࡹࠨⓒ") in CONFIG) and bstack11ll1l11l1_opy_() and bstack11l11111l1_opy_() >= version.parse(
        bstack1l11111ll1_opy_)
def bstack1l11ll11_opy_(self,
               executablePath=None,
               channel=None,
               args=None,
               ignoreDefaultArgs=None,
               handleSIGINT=None,
               handleSIGTERM=None,
               handleSIGHUP=None,
               timeout=None,
               env=None,
               headless=None,
               devtools=None,
               proxy=None,
               downloadsPath=None,
               slowMo=None,
               tracesDir=None,
               chromiumSandbox=None,
               firefoxUserPrefs=None
               ):
    global CONFIG
    global bstack1llll1111l_opy_
    global bstack11lllllll1_opy_
    global bstack11l11ll111_opy_
    CONFIG[bstack1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮ࡗࡉࡑࠧⓓ")] = str(bstack11l11ll111_opy_) + str(__version__)
    bstack11l1l1l1_opy_ = 0
    try:
        if bstack11lllllll1_opy_ is True:
            bstack11l1l1l1_opy_ = int(os.environ.get(bstack1ll_opy_ (u"࠭ࡂࡓࡑ࡚ࡗࡊࡘࡓࡕࡃࡆࡏࡤࡖࡌࡂࡖࡉࡓࡗࡓ࡟ࡊࡐࡇࡉ࡝࠭ⓔ")))
    except:
        bstack11l1l1l1_opy_ = 0
    CONFIG[bstack1ll_opy_ (u"ࠢࡪࡵࡓࡰࡦࡿࡷࡳ࡫ࡪ࡬ࡹࠨⓕ")] = True
    bstack1l1l111ll1_opy_ = bstack1l1111llll_opy_(CONFIG, bstack11l1l1l1_opy_)
    logger.debug(bstack11ll1l1l_opy_.format(str(bstack1l1l111ll1_opy_)))
    if CONFIG.get(bstack1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱࡌࡰࡥࡤࡰࠬⓖ")):
        bstack1l1l1111ll_opy_(bstack1l1l111ll1_opy_, bstack1l1l1ll1l1_opy_)
    if bstack1ll_opy_ (u"ࠩࡳࡰࡦࡺࡦࡰࡴࡰࡷࠬⓗ") in CONFIG and bstack1ll_opy_ (u"ࠪࡷࡪࡹࡳࡪࡱࡱࡒࡦࡳࡥࠨⓘ") in CONFIG[bstack1ll_opy_ (u"ࠫࡵࡲࡡࡵࡨࡲࡶࡲࡹࠧⓙ")][bstack11l1l1l1_opy_]:
        bstack1llll1111l_opy_ = CONFIG[bstack1ll_opy_ (u"ࠬࡶ࡬ࡢࡶࡩࡳࡷࡳࡳࠨⓚ")][bstack11l1l1l1_opy_][bstack1ll_opy_ (u"࠭ࡳࡦࡵࡶ࡭ࡴࡴࡎࡢ࡯ࡨࠫⓛ")]
    import urllib
    import json
    if bstack1ll_opy_ (u"ࠧࡵࡷࡵࡦࡴ࡙ࡣࡢ࡮ࡨࠫⓜ") in CONFIG and str(CONFIG[bstack1ll_opy_ (u"ࠨࡶࡸࡶࡧࡵࡓࡤࡣ࡯ࡩࠬⓝ")]).lower() != bstack1ll_opy_ (u"ࠩࡩࡥࡱࡹࡥࠨⓞ"):
        bstack11llllll_opy_ = bstack11lll11ll1_opy_()
        bstack11l1111l_opy_ = bstack11llllll_opy_ + urllib.parse.quote(json.dumps(bstack1l1l111ll1_opy_))
    else:
        bstack11l1111l_opy_ = bstack1ll_opy_ (u"ࠪࡻࡸࡹ࠺࠰࠱ࡦࡨࡵ࠴ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯࠳ࡩ࡯࡮࠱ࡳࡰࡦࡿࡷࡳ࡫ࡪ࡬ࡹࡅࡣࡢࡲࡶࡁࠬⓟ") + urllib.parse.quote(json.dumps(bstack1l1l111ll1_opy_))
    browser = self.connect(bstack11l1111l_opy_)
    return browser
def bstack1l11l1l1_opy_():
    global bstack111lllll_opy_
    global bstack11l11ll111_opy_
    try:
        from playwright._impl._browser_type import BrowserType
        from bstack_utils.helper import bstack111lllll1_opy_
        if not bstack1l1ll111lll_opy_():
            global bstack111lll1l1l_opy_
            if not bstack111lll1l1l_opy_:
                from bstack_utils.helper import bstack1l1111l11_opy_, bstack11l1lllll_opy_
                bstack111lll1l1l_opy_ = bstack1l1111l11_opy_()
                bstack11l1lllll_opy_(bstack11l11ll111_opy_)
            BrowserType.connect = bstack111lllll1_opy_
            return
        BrowserType.launch = bstack1l11ll11_opy_
        bstack111lllll_opy_ = True
    except Exception as e:
        pass
def bstack1lll1l1l1l1l_opy_():
    global CONFIG
    global bstack11l11l11ll_opy_
    global bstack1ll111lll_opy_
    global bstack1l1l1ll1l1_opy_
    global bstack11lllllll1_opy_
    global bstack1ll1111l1_opy_
    CONFIG = json.loads(os.environ.get(bstack1ll_opy_ (u"ࠫࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡇࡔࡔࡆࡊࡉࠪⓠ")))
    bstack11l11l11ll_opy_ = eval(os.environ.get(bstack1ll_opy_ (u"ࠬࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣࡎ࡙࡟ࡂࡒࡓࡣࡆ࡛ࡔࡐࡏࡄࡘࡊ࠭ⓡ")))
    bstack1ll111lll_opy_ = os.environ.get(bstack1ll_opy_ (u"࠭ࡂࡓࡑ࡚ࡗࡊࡘࡓࡕࡃࡆࡏࡤࡎࡕࡃࡡࡘࡖࡑ࠭ⓢ"))
    bstack1l1111lll1_opy_(CONFIG, bstack11l11l11ll_opy_)
    bstack1ll1111l1_opy_ = bstack11l1l1lll1_opy_.configure_logger(CONFIG, bstack1ll1111l1_opy_)
    if cli.bstack1ll11ll1l_opy_():
        bstack111lll1l_opy_.invoke(bstack1lll1lll_opy_.CONNECT, bstack11ll111l11_opy_())
        cli_context.platform_index = int(os.environ.get(bstack1ll_opy_ (u"ࠧࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡐࡍࡃࡗࡊࡔࡘࡍࡠࡋࡑࡈࡊ࡞ࠧⓣ"), bstack1ll_opy_ (u"ࠨ࠲ࠪⓤ")))
        cli.bstack1ll1lll1l11_opy_(cli_context.platform_index)
        cli.bstack1ll1l1l1111_opy_(bstack111ll1111_opy_(bstack1ll111lll_opy_, CONFIG), cli_context.platform_index, bstack1l1ll111_opy_)
        cli.bstack1lll111l1l1_opy_()
        logger.debug(bstack1ll_opy_ (u"ࠤࡆࡐࡎࠦࡩࡴࠢࡤࡧࡹ࡯ࡶࡦࠢࡩࡳࡷࠦࡰ࡭ࡣࡷࡪࡴࡸ࡭ࡠ࡫ࡱࡨࡪࡾ࠽ࠣⓥ") + str(cli_context.platform_index) + bstack1ll_opy_ (u"ࠥࠦⓦ"))
        return # skip all existing operations
    global bstack11ll1l1lll_opy_
    global bstack1l1111ll1_opy_
    global bstack11l1ll1111_opy_
    global bstack11ll111ll_opy_
    global bstack1ll11l1l_opy_
    global bstack1l111l111_opy_
    global bstack111ll111l_opy_
    global bstack1ll11l11l1_opy_
    global bstack1ll11l1111_opy_
    global bstack1l11lll111_opy_
    global bstack1l111l1ll_opy_
    global bstack11lll1l111_opy_
    try:
        from selenium import webdriver
        from selenium.webdriver.remote.webdriver import WebDriver
        bstack11ll1l1lll_opy_ = webdriver.Remote.__init__
        bstack1l1111ll1_opy_ = WebDriver.quit
        bstack111ll111l_opy_ = WebDriver.close
        bstack1ll11l11l1_opy_ = WebDriver.get
    except Exception as e:
        pass
    if (bstack1ll_opy_ (u"ࠫ࡭ࡺࡴࡱࡒࡵࡳࡽࡿࠧⓧ") in CONFIG or bstack1ll_opy_ (u"ࠬ࡮ࡴࡵࡲࡶࡔࡷࡵࡸࡺࠩⓨ") in CONFIG) and bstack11ll1l11l1_opy_():
        if bstack11l11111l1_opy_() < version.parse(bstack1l11111ll1_opy_):
            logger.error(bstack11ll11111_opy_.format(bstack11l11111l1_opy_()))
        else:
            try:
                from selenium.webdriver.remote.remote_connection import RemoteConnection
                if hasattr(RemoteConnection, bstack1ll_opy_ (u"࠭࡟ࡨࡧࡷࡣࡵࡸ࡯ࡹࡻࡢࡹࡷࡲࠧⓩ")) and callable(getattr(RemoteConnection, bstack1ll_opy_ (u"ࠧࡠࡩࡨࡸࡤࡶࡲࡰࡺࡼࡣࡺࡸ࡬ࠨ⓪"))):
                    bstack1ll11l1111_opy_ = RemoteConnection._get_proxy_url
                else:
                    from selenium.webdriver.remote.client_config import ClientConfig
                    bstack1ll11l1111_opy_ = ClientConfig.get_proxy_url
            except Exception as e:
                logger.error(bstack1ll1111ll_opy_.format(str(e)))
    try:
        from _pytest.config import Config
        bstack1l11lll111_opy_ = Config.getoption
        from _pytest import runner
        bstack1l111l1ll_opy_ = runner._update_current_test_var
    except Exception as e:
        logger.warning(bstack1ll_opy_ (u"ࠣࠧࡶ࠾ࠥࠫࡳࠣ⓫"), bstack1111ll11_opy_, str(e))
    try:
        from pytest_bdd import reporting
        bstack11lll1l111_opy_ = reporting.runtest_makereport
    except Exception as e:
        logger.debug(bstack1ll_opy_ (u"ࠩࡓࡰࡪࡧࡳࡦࠢ࡬ࡲࡸࡺࡡ࡭࡮ࠣࡴࡾࡺࡥࡴࡶ࠰ࡦࡩࡪࠠࡵࡱࠣࡶࡺࡴࠠࡱࡻࡷࡩࡸࡺ࠭ࡣࡦࡧࠤࡹ࡫ࡳࡵࡵࠪ⓬"))
    bstack1l1l1ll1l1_opy_ = CONFIG.get(bstack1ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵࡗࡹࡧࡣ࡬ࡎࡲࡧࡦࡲࡏࡱࡶ࡬ࡳࡳࡹࠧ⓭"), {}).get(bstack1ll_opy_ (u"ࠫࡱࡵࡣࡢ࡮ࡌࡨࡪࡴࡴࡪࡨ࡬ࡩࡷ࠭⓮"))
    bstack11lllllll1_opy_ = True
    bstack1l1lllll_opy_(bstack1l1ll11lll_opy_)
if (bstack111lll11l11_opy_()):
    bstack1lll1l1l1l1l_opy_()
@error_handler(class_method=False)
def bstack1lll1l11l1l1_opy_(hook_name, event, bstack1l1111lll1l_opy_=None):
    if hook_name not in [bstack1ll_opy_ (u"ࠬࡹࡥࡵࡷࡳࡣ࡫ࡻ࡮ࡤࡶ࡬ࡳࡳ࠭⓯"), bstack1ll_opy_ (u"࠭ࡴࡦࡣࡵࡨࡴࡽ࡮ࡠࡨࡸࡲࡨࡺࡩࡰࡰࠪ⓰"), bstack1ll_opy_ (u"ࠧࡴࡧࡷࡹࡵࡥ࡭ࡰࡦࡸࡰࡪ࠭⓱"), bstack1ll_opy_ (u"ࠨࡶࡨࡥࡷࡪ࡯ࡸࡰࡢࡱࡴࡪࡵ࡭ࡧࠪ⓲"), bstack1ll_opy_ (u"ࠩࡶࡩࡹࡻࡰࡠࡥ࡯ࡥࡸࡹࠧ⓳"), bstack1ll_opy_ (u"ࠪࡸࡪࡧࡲࡥࡱࡺࡲࡤࡩ࡬ࡢࡵࡶࠫ⓴"), bstack1ll_opy_ (u"ࠫࡸ࡫ࡴࡶࡲࡢࡱࡪࡺࡨࡰࡦࠪ⓵"), bstack1ll_opy_ (u"ࠬࡺࡥࡢࡴࡧࡳࡼࡴ࡟࡮ࡧࡷ࡬ࡴࡪࠧ⓶")]:
        return
    node = store[bstack1ll_opy_ (u"࠭ࡣࡶࡴࡵࡩࡳࡺ࡟ࡵࡧࡶࡸࡤ࡯ࡴࡦ࡯ࠪ⓷")]
    if hook_name in [bstack1ll_opy_ (u"ࠧࡴࡧࡷࡹࡵࡥ࡭ࡰࡦࡸࡰࡪ࠭⓸"), bstack1ll_opy_ (u"ࠨࡶࡨࡥࡷࡪ࡯ࡸࡰࡢࡱࡴࡪࡵ࡭ࡧࠪ⓹")]:
        node = store[bstack1ll_opy_ (u"ࠩࡦࡹࡷࡸࡥ࡯ࡶࡢࡱࡴࡪࡵ࡭ࡧࡢ࡭ࡹ࡫࡭ࠨ⓺")]
    elif hook_name in [bstack1ll_opy_ (u"ࠪࡷࡪࡺࡵࡱࡡࡦࡰࡦࡹࡳࠨ⓻"), bstack1ll_opy_ (u"ࠫࡹ࡫ࡡࡳࡦࡲࡻࡳࡥࡣ࡭ࡣࡶࡷࠬ⓼")]:
        node = store[bstack1ll_opy_ (u"ࠬࡩࡵࡳࡴࡨࡲࡹࡥࡣ࡭ࡣࡶࡷࡤ࡯ࡴࡦ࡯ࠪ⓽")]
    hook_type = bstack1lllll11ll1l_opy_(hook_name)
    if event == bstack1ll_opy_ (u"࠭ࡢࡦࡨࡲࡶࡪ࠭⓾"):
        if cli.is_running():
            cli.test_framework.track_event(cli_context, bstack1ll1ll1lll1_opy_[hook_type], bstack1ll1l1ll11l_opy_.PRE, node, hook_name)
            return
        uuid = uuid4().__str__()
        bstack111l11l11l_opy_ = {
            bstack1ll_opy_ (u"ࠧࡶࡷ࡬ࡨࠬ⓿"): uuid,
            bstack1ll_opy_ (u"ࠨࡵࡷࡥࡷࡺࡥࡥࡡࡤࡸࠬ─"): bstack1l11l1111_opy_(),
            bstack1ll_opy_ (u"ࠩࡷࡽࡵ࡫ࠧ━"): bstack1ll_opy_ (u"ࠪ࡬ࡴࡵ࡫ࠨ│"),
            bstack1ll_opy_ (u"ࠫ࡭ࡵ࡯࡬ࡡࡷࡽࡵ࡫ࠧ┃"): hook_type,
            bstack1ll_opy_ (u"ࠬ࡮࡯ࡰ࡭ࡢࡲࡦࡳࡥࠨ┄"): hook_name
        }
        store[bstack1ll_opy_ (u"࠭ࡣࡶࡴࡵࡩࡳࡺ࡟ࡩࡱࡲ࡯ࡤࡻࡵࡪࡦࠪ┅")].append(uuid)
        bstack1lll11lllll1_opy_ = node.nodeid
        if hook_type == bstack1ll_opy_ (u"ࠧࡃࡇࡉࡓࡗࡋ࡟ࡆࡃࡆࡌࠬ┆"):
            if not _111l11111l_opy_.get(bstack1lll11lllll1_opy_, None):
                _111l11111l_opy_[bstack1lll11lllll1_opy_] = {bstack1ll_opy_ (u"ࠨࡪࡲࡳࡰࡹࠧ┇"): []}
            _111l11111l_opy_[bstack1lll11lllll1_opy_][bstack1ll_opy_ (u"ࠩ࡫ࡳࡴࡱࡳࠨ┈")].append(bstack111l11l11l_opy_[bstack1ll_opy_ (u"ࠪࡹࡺ࡯ࡤࠨ┉")])
        _111l11111l_opy_[bstack1lll11lllll1_opy_ + bstack1ll_opy_ (u"ࠫ࠲࠭┊") + hook_name] = bstack111l11l11l_opy_
        bstack1lll1l111ll1_opy_(node, bstack111l11l11l_opy_, bstack1ll_opy_ (u"ࠬࡎ࡯ࡰ࡭ࡕࡹࡳ࡙ࡴࡢࡴࡷࡩࡩ࠭┋"))
    elif event == bstack1ll_opy_ (u"࠭ࡡࡧࡶࡨࡶࠬ┌"):
        if cli.is_running():
            cli.test_framework.track_event(cli_context, bstack1ll1ll1lll1_opy_[hook_type], bstack1ll1l1ll11l_opy_.POST, node, None, bstack1l1111lll1l_opy_)
            return
        bstack111l1llll1_opy_ = node.nodeid + bstack1ll_opy_ (u"ࠧ࠮ࠩ┍") + hook_name
        _111l11111l_opy_[bstack111l1llll1_opy_][bstack1ll_opy_ (u"ࠨࡨ࡬ࡲ࡮ࡹࡨࡦࡦࡢࡥࡹ࠭┎")] = bstack1l11l1111_opy_()
        bstack1lll1l11111l_opy_(_111l11111l_opy_[bstack111l1llll1_opy_][bstack1ll_opy_ (u"ࠩࡸࡹ࡮ࡪࠧ┏")])
        bstack1lll1l111ll1_opy_(node, _111l11111l_opy_[bstack111l1llll1_opy_], bstack1ll_opy_ (u"ࠪࡌࡴࡵ࡫ࡓࡷࡱࡊ࡮ࡴࡩࡴࡪࡨࡨࠬ┐"), bstack1lll1l1111ll_opy_=bstack1l1111lll1l_opy_)
def bstack1lll1l1l111l_opy_():
    global bstack1lll1l111l1l_opy_
    if bstack1ll1l1l1ll_opy_():
        bstack1lll1l111l1l_opy_ = bstack1ll_opy_ (u"ࠫࡵࡿࡴࡦࡵࡷ࠱ࡧࡪࡤࠨ┑")
    else:
        bstack1lll1l111l1l_opy_ = bstack1ll_opy_ (u"ࠬࡶࡹࡵࡧࡶࡸࠬ┒")
@bstack1lll1111l_opy_.bstack1lll1ll1llll_opy_
def bstack1lll1l1l1ll1_opy_():
    bstack1lll1l1l111l_opy_()
    if cli.is_running():
        try:
            bstack111l1l1lll1_opy_(bstack1lll1l11l1l1_opy_)
        except Exception as e:
            logger.debug(bstack1ll_opy_ (u"ࠨࡅࡹࡥࡨࡴࡹ࡯࡯࡯ࠢ࡬ࡲࠥ࡮࡯ࡰ࡭ࡶࠤࡵࡧࡴࡤࡪ࠽ࠤࢀࢃࠢ┓").format(e))
        return
    if bstack11ll1l11l1_opy_():
        bstack1ll1l1l111_opy_ = Config.bstack11lll1111_opy_()
        bstack1ll_opy_ (u"ࠧࠨࠩࠍࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࡈࡲࡶࠥࡶࡰࡱࠢࡀࠤ࠶࠲ࠠ࡮ࡱࡧࡣࡪࡾࡥࡤࡷࡷࡩࠥ࡭ࡥࡵࡵࠣࡹࡸ࡫ࡤࠡࡨࡲࡶࠥࡧ࠱࠲ࡻࠣࡧࡴࡳ࡭ࡢࡰࡧࡷ࠲ࡽࡲࡢࡲࡳ࡭ࡳ࡭ࠊࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࡌ࡯ࡳࠢࡳࡴࡵࠦ࠾ࠡ࠳࠯ࠤࡲࡵࡤࡠࡧࡻࡩࡨࡻࡴࡦࠢࡧࡳࡪࡹࠠ࡯ࡱࡷࠤࡷࡻ࡮ࠡࡤࡨࡧࡦࡻࡳࡦࠢ࡬ࡸࠥ࡯ࡳࠡࡲࡤࡸࡨ࡮ࡥࡥࠢ࡬ࡲࠥࡧࠠࡥ࡫ࡩࡪࡪࡸࡥ࡯ࡶࠣࡴࡷࡵࡣࡦࡵࡶࠤ࡮ࡪࠊࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤ࡚ࠥࡨࡶࡵࠣࡻࡪࠦ࡮ࡦࡧࡧࠤࡹࡵࠠࡶࡵࡨࠤࡘ࡫࡬ࡦࡰ࡬ࡹࡲࡖࡡࡵࡥ࡫ࠬࡸ࡫࡬ࡦࡰ࡬ࡹࡲࡥࡨࡢࡰࡧࡰࡪࡸࠩࠡࡨࡲࡶࠥࡶࡰࡱࠢࡁࠤ࠶ࠐࠠࠡࠢࠣࠤࠥࠦࠠࠨࠩࠪ└")
        if bstack1ll1l1l111_opy_.get_property(bstack1ll_opy_ (u"ࠨࡤࡶࡸࡦࡩ࡫ࡠ࡯ࡲࡨࡤࡩࡡ࡭࡮ࡨࡨࠬ┕")):
            if CONFIG.get(bstack1ll_opy_ (u"ࠩࡳࡥࡷࡧ࡬࡭ࡧ࡯ࡷࡕ࡫ࡲࡑ࡮ࡤࡸ࡫ࡵࡲ࡮ࠩ┖")) is not None and int(CONFIG[bstack1ll_opy_ (u"ࠪࡴࡦࡸࡡ࡭࡮ࡨࡰࡸࡖࡥࡳࡒ࡯ࡥࡹ࡬࡯ࡳ࡯ࠪ┗")]) > 1:
                bstack111l1ll1_opy_(bstack1lll11l11_opy_)
            return
        bstack111l1ll1_opy_(bstack1lll11l11_opy_)
    try:
        bstack111l1l1lll1_opy_(bstack1lll1l11l1l1_opy_)
    except Exception as e:
        logger.debug(bstack1ll_opy_ (u"ࠦࡊࡾࡣࡦࡲࡷ࡭ࡴࡴࠠࡪࡰࠣ࡬ࡴࡵ࡫ࡴࠢࡳࡥࡹࡩࡨ࠻ࠢࡾࢁࠧ┘").format(e))
bstack1lll1l1l1ll1_opy_()