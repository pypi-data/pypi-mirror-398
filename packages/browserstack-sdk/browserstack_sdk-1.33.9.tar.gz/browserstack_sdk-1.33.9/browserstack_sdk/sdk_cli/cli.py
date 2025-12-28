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
import subprocess
import threading
import time
import sys
import grpc
import os
from browserstack_sdk import sdk_pb2_grpc
from browserstack_sdk import sdk_pb2 as structs
from browserstack_sdk.sdk_cli.bstack1lllll1ll1l_opy_ import bstack1lllll1l1l1_opy_
from browserstack_sdk.sdk_cli.bstack1lll11ll1l1_opy_ import bstack1ll1lll1l1l_opy_
from browserstack_sdk.sdk_cli.bstack1lll111l111_opy_ import bstack1ll1l1ll1l1_opy_
from browserstack_sdk.sdk_cli.bstack1lll11111ll_opy_ import bstack1lll1l1l11l_opy_
from browserstack_sdk.sdk_cli.bstack1lll111l1ll_opy_ import bstack1ll1l111ll1_opy_
from browserstack_sdk.sdk_cli.bstack1lll1ll11l1_opy_ import bstack1ll11lll111_opy_
from browserstack_sdk.sdk_cli.bstack1ll1ll1111l_opy_ import bstack1ll1l1l1lll_opy_
from browserstack_sdk.sdk_cli.bstack1ll1l1111l1_opy_ import bstack1lll1l11111_opy_
from browserstack_sdk.sdk_cli.bstack1ll11lll11l_opy_ import bstack1ll1ll1l11l_opy_
from browserstack_sdk.sdk_cli.bstack1ll1lll11l1_opy_ import bstack1ll1l111l1l_opy_
from browserstack_sdk.sdk_cli.bstack111lll1l_opy_ import bstack111lll1l_opy_, bstack1lll1lll_opy_, bstack11ll111l11_opy_
from browserstack_sdk.sdk_cli.pytest_bdd_framework import PytestBDDFramework
from browserstack_sdk.sdk_cli.bstack1ll11llll11_opy_ import bstack1lll1lll11l_opy_
from browserstack_sdk.sdk_cli.bstack1lll11lll11_opy_ import bstack1ll1llll1l1_opy_
from browserstack_sdk.sdk_cli.bstack1lll1lll1l1_opy_ import bstack1llll1ll1ll_opy_
from browserstack_sdk.sdk_cli.bstack1ll1llll111_opy_ import bstack1ll1l1l111l_opy_
from bstack_utils.helper import Notset, bstack1lll11lllll_opy_, get_cli_dir, bstack1ll1ll1ll1l_opy_, bstack1ll1l1l1ll_opy_
from browserstack_sdk.sdk_cli.test_framework import TestFramework
from browserstack_sdk.sdk_cli.utils.bstack1lll1ll1ll1_opy_ import bstack1lll1ll1111_opy_
from browserstack_sdk.sdk_cli.utils.bstack1l1111ll11_opy_ import bstack1l11l11ll_opy_
from bstack_utils.helper import Notset, bstack1lll11lllll_opy_, get_cli_dir, bstack1ll1ll1ll1l_opy_, bstack1ll1l1l1ll_opy_, bstack1l111111_opy_, bstack1111l1l1l_opy_
from browserstack_sdk.sdk_cli.test_framework import TestFramework, bstack1ll1ll1lll1_opy_, bstack1ll1l1ll111_opy_, bstack1ll1l1ll11l_opy_, bstack1ll1l111111_opy_
from browserstack_sdk.sdk_cli.bstack1lll1lll1l1_opy_ import bstack1llll111ll1_opy_, bstack1llll11l1l1_opy_, bstack1lllll111l1_opy_
from bstack_utils.constants import *
from bstack_utils.bstack1llllllll_opy_ import bstack1l1lll11ll_opy_
from bstack_utils import bstack11l1l1lll1_opy_
from typing import Any, List, Union, Dict
import traceback
from google.protobuf.json_format import MessageToDict
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path
from functools import wraps
from bstack_utils.measure import measure
from bstack_utils.messages import bstack11ll111l1_opy_, bstack1l1111l1_opy_
logger = bstack11l1l1lll1_opy_.get_logger(__name__, bstack11l1l1lll1_opy_.bstack1ll1l11l11l_opy_())
def bstack1lll11111l1_opy_(bs_config):
    bstack1ll1ll1llll_opy_ = None
    bstack1lll11l11ll_opy_ = None
    try:
        bstack1lll11l11ll_opy_ = get_cli_dir()
        bstack1ll1ll1llll_opy_ = bstack1ll1ll1ll1l_opy_(bstack1lll11l11ll_opy_)
        bstack1lll1ll1lll_opy_ = bstack1lll11lllll_opy_(bstack1ll1ll1llll_opy_, bstack1lll11l11ll_opy_, bs_config)
        bstack1ll1ll1llll_opy_ = bstack1lll1ll1lll_opy_ if bstack1lll1ll1lll_opy_ else bstack1ll1ll1llll_opy_
        if not bstack1ll1ll1llll_opy_:
            raise ValueError(bstack1ll_opy_ (u"ࠣࡗࡱࡥࡧࡲࡥࠡࡶࡲࠤ࡫࡯࡮ࡥࠢࡖࡈࡐࡥࡃࡍࡋࡢࡆࡎࡔ࡟ࡑࡃࡗࡌࠧჵ"))
    except Exception as ex:
        logger.debug(bstack1ll_opy_ (u"ࠤࡈࡶࡷࡵࡲࠡࡹ࡫࡭ࡱ࡫ࠠࡥࡱࡺࡲࡱࡵࡡࡥ࡫ࡱ࡫ࠥࡺࡨࡦࠢ࡯ࡥࡹ࡫ࡳࡵࠢࡥ࡭ࡳࡧࡲࡺࠢࡾࢁࠧჶ").format(ex))
        bstack1ll1ll1llll_opy_ = os.environ.get(bstack1ll_opy_ (u"ࠥࡗࡉࡑ࡟ࡄࡎࡌࡣࡇࡏࡎࡠࡒࡄࡘࡍࠨჷ"))
        if bstack1ll1ll1llll_opy_:
            logger.debug(bstack1ll_opy_ (u"ࠦࡋࡧ࡬࡭࡫ࡱ࡫ࠥࡨࡡࡤ࡭ࠣࡸࡴࠦࡓࡅࡍࡢࡇࡑࡏ࡟ࡃࡋࡑࡣࡕࡇࡔࡉࠢࡩࡶࡴࡳࠠࡦࡰࡹ࡭ࡷࡵ࡮࡮ࡧࡱࡸ࠿ࠦࠢჸ") + str(bstack1ll1ll1llll_opy_) + bstack1ll_opy_ (u"ࠧࠨჹ"))
        else:
            logger.debug(bstack1ll_opy_ (u"ࠨࡎࡰࠢࡹࡥࡱ࡯ࡤࠡࡕࡇࡏࡤࡉࡌࡊࡡࡅࡍࡓࡥࡐࡂࡖࡋࠤ࡫ࡵࡵ࡯ࡦࠣ࡭ࡳࠦࡥ࡯ࡸ࡬ࡶࡴࡴ࡭ࡦࡰࡷ࠿ࠥࡹࡥࡵࡷࡳࠤࡲࡧࡹࠡࡤࡨࠤ࡮ࡴࡣࡰ࡯ࡳࡰࡪࡺࡥ࠯ࠤჺ"))
    return bstack1ll1ll1llll_opy_, bstack1lll11l11ll_opy_
bstack1ll1ll1l1l1_opy_ = bstack1ll_opy_ (u"ࠢ࠺࠻࠼࠽ࠧ჻")
bstack1ll1l11111l_opy_ = bstack1ll_opy_ (u"ࠣࡴࡨࡥࡩࡿࠢჼ")
bstack1lll1ll111l_opy_ = bstack1ll_opy_ (u"ࠤࡅࡖࡔ࡝ࡓࡆࡔࡖࡘࡆࡉࡋࡠࡅࡏࡍࡤࡈࡉࡏࡡࡖࡉࡘ࡙ࡉࡐࡐࡢࡍࡉࠨჽ")
bstack1lll11l1111_opy_ = bstack1ll_opy_ (u"ࠥࡆࡗࡕࡗࡔࡇࡕࡗ࡙ࡇࡃࡌࡡࡆࡐࡎࡥࡂࡊࡐࡢࡐࡎ࡙ࡔࡆࡐࡢࡅࡉࡊࡒࠣჾ")
bstack11l111llll_opy_ = bstack1ll_opy_ (u"ࠦࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡅ࡚࡚ࡏࡎࡃࡗࡍࡔࡔࠢჿ")
bstack1lll1l11l1l_opy_ = re.compile(bstack1ll_opy_ (u"ࡷࠨࠨࡀ࡫ࠬ࠲࠯࠮ࡂࡓࡑ࡚ࡗࡊࡘࡓࡕࡃࡆࡏࢁࡈࡓࠪ࠰࠭ࠦᄀ"))
bstack1lll1l1llll_opy_ = bstack1ll_opy_ (u"ࠨࡤࡦࡸࡨࡰࡴࡶ࡭ࡦࡰࡷࠦᄁ")
bstack1lll111lll1_opy_ = bstack1ll_opy_ (u"ࠢࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡆࡐࡔࡆࡉࡤࡌࡁࡍࡎࡅࡅࡈࡑࠢᄂ")
bstack1lll11lll1l_opy_ = [
    bstack1lll1lll_opy_.bstack1l1l1l1lll_opy_,
    bstack1lll1lll_opy_.CONNECT,
    bstack1lll1lll_opy_.bstack11llll1ll_opy_,
]
class SDKCLI:
    _1ll1l11l1ll_opy_ = None
    process: Union[None, Any]
    bstack1lll11l1lll_opy_: bool
    bstack1ll1l1l11l1_opy_: bool
    bstack1lll1l1ll11_opy_: bool
    bin_session_id: Union[None, str]
    cli_bin_session_id: Union[None, str]
    cli_listen_addr: Union[None, str]
    bstack1lll1ll1l11_opy_: Union[None, grpc.Channel]
    bstack1lll111ll1l_opy_: str
    test_framework: TestFramework
    bstack1lll1lll1l1_opy_: bstack1llll1ll1ll_opy_
    session_framework: str
    config: Union[None, Dict[str, Any]]
    bstack1ll1l1l11ll_opy_: bstack1ll1l111l1l_opy_
    accessibility: bstack1ll1l1ll1l1_opy_
    bstack1l1111ll11_opy_: bstack1l11l11ll_opy_
    ai: bstack1lll1l1l11l_opy_
    bstack1lll1l11l11_opy_: bstack1ll1l111ll1_opy_
    bstack1lll1ll11ll_opy_: List[bstack1ll1lll1l1l_opy_]
    config_testhub: Any
    config_observability: Any
    config_accessibility: Any
    bstack1ll1l11l1l1_opy_: Any
    bstack1ll11lllll1_opy_: Dict[str, timedelta]
    bstack1ll11lll1ll_opy_: str
    bstack1lllll1ll1l_opy_: bstack1lllll1l1l1_opy_
    def __new__(cls):
        if not cls._1ll1l11l1ll_opy_:
            cls._1ll1l11l1ll_opy_ = super(SDKCLI, cls).__new__(cls)
        return cls._1ll1l11l1ll_opy_
    def __init__(self):
        self.process = None
        self.bstack1lll11l1lll_opy_ = False
        self.bstack1lll1ll1l11_opy_ = None
        self.bstack1ll1l11lll1_opy_ = None
        self.cli_bin_session_id = None
        self.cli_listen_addr = os.environ.get(bstack1lll11l1111_opy_, None)
        self.bstack1ll1l11llll_opy_ = os.environ.get(bstack1lll1ll111l_opy_, bstack1ll_opy_ (u"ࠣࠤᄃ")) == bstack1ll_opy_ (u"ࠤࠥᄄ")
        self.bstack1ll1l1l11l1_opy_ = False
        self.bstack1lll1l1ll11_opy_ = False
        self.config = None
        self.config_testhub = None
        self.config_observability = None
        self.config_accessibility = None
        self.bstack1ll1l11l1l1_opy_ = None
        self.test_framework = None
        self.bstack1lll1lll1l1_opy_ = None
        self.bstack1lll111ll1l_opy_=bstack1ll_opy_ (u"ࠥࠦᄅ")
        self.session_framework = None
        self.logger = bstack11l1l1lll1_opy_.get_logger(self.__class__.__name__, bstack11l1l1lll1_opy_.bstack1ll1l11l11l_opy_())
        self.bstack1ll11lllll1_opy_ = defaultdict(lambda: timedelta(microseconds=0))
        self.bstack1lllll1ll1l_opy_ = bstack1lllll1l1l1_opy_()
        self.bstack1ll1ll1l111_opy_ = None
        self.bstack1ll1lllllll_opy_ = None
        self.bstack1ll1l1l11ll_opy_ = None
        self.accessibility = None
        self.ai = None
        self.percy = None
        self.bstack1lll1ll11ll_opy_ = []
    def bstack11111l1l_opy_(self):
        return os.environ.get(bstack11l111llll_opy_).lower().__eq__(bstack1ll_opy_ (u"ࠦࡹࡸࡵࡦࠤᄆ"))
    def is_enabled(self, config):
        if os.environ.get(bstack1lll111lll1_opy_, bstack1ll_opy_ (u"ࠬ࠭ᄇ")).lower() in [bstack1ll_opy_ (u"࠭ࡴࡳࡷࡨࠫᄈ"), bstack1ll_opy_ (u"ࠧ࠲ࠩᄉ"), bstack1ll_opy_ (u"ࠨࡻࡨࡷࠬᄊ")]:
            self.logger.debug(bstack1ll_opy_ (u"ࠤࡉࡳࡷࡩࡩ࡯ࡩࠣࡪࡦࡲ࡬ࡣࡣࡦ࡯ࠥࡳ࡯ࡥࡧࠣࡨࡺ࡫ࠠࡵࡱࠣࡆࡗࡕࡗࡔࡇࡕࡗ࡙ࡇࡃࡌࡡࡉࡓࡗࡉࡅࡠࡈࡄࡐࡑࡈࡁࡄࡍࠣࡩࡳࡼࡩࡳࡱࡱࡱࡪࡴࡴࠡࡸࡤࡶ࡮ࡧࡢ࡭ࡧࠥᄋ"))
            os.environ[bstack1ll_opy_ (u"ࠥࡆࡗࡕࡗࡔࡇࡕࡗ࡙ࡇࡃࡌࡡࡅࡍࡓࡇࡒ࡚ࡡࡌࡗࡤࡘࡕࡏࡐࡌࡒࡌࠨᄌ")] = bstack1ll_opy_ (u"ࠦࡋࡧ࡬ࡴࡧࠥᄍ")
            return False
        if bstack1ll_opy_ (u"ࠬࡺࡵࡳࡤࡲࡗࡨࡧ࡬ࡦࠩᄎ") in config and str(config[bstack1ll_opy_ (u"࠭ࡴࡶࡴࡥࡳࡘࡩࡡ࡭ࡧࠪᄏ")]).lower() != bstack1ll_opy_ (u"ࠧࡧࡣ࡯ࡷࡪ࠭ᄐ"):
            return False
        bstack1lll1l111ll_opy_ = [bstack1ll_opy_ (u"ࠣࡲࡼࡸࡪࡹࡴࠣᄑ"), bstack1ll_opy_ (u"ࠤࡳࡽࡹ࡫ࡳࡵ࠯ࡥࡨࡩࠨᄒ")]
        bstack1ll11llllll_opy_ = config.get(bstack1ll_opy_ (u"ࠥࡪࡷࡧ࡭ࡦࡹࡲࡶࡰࠨᄓ")) in bstack1lll1l111ll_opy_ or os.environ.get(bstack1ll_opy_ (u"ࠫࡋࡘࡁࡎࡇ࡚ࡓࡗࡑ࡟ࡖࡕࡈࡈࠬᄔ")) in bstack1lll1l111ll_opy_
        os.environ[bstack1ll_opy_ (u"ࠧࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣࡇࡏࡎࡂࡔ࡜ࡣࡎ࡙࡟ࡓࡗࡑࡒࡎࡔࡇࠣᄕ")] = str(bstack1ll11llllll_opy_) # bstack1ll1llll1ll_opy_ bstack1ll1ll1ll11_opy_ VAR to bstack1lll11ll11l_opy_ is binary running
        return bstack1ll11llllll_opy_
    def bstack1lll11111l_opy_(self):
        for event in bstack1lll11lll1l_opy_:
            bstack111lll1l_opy_.register(
                event, lambda event_name, *args, **kwargs: bstack111lll1l_opy_.logger.debug(bstack1ll_opy_ (u"ࠨࡻࡦࡸࡨࡲࡹࡥ࡮ࡢ࡯ࡨࢁࠥࡃ࠾ࠡࡽࡤࡶ࡬ࡹࡽࠡࠤᄖ") + str(kwargs) + bstack1ll_opy_ (u"ࠢࠣᄗ"))
            )
        bstack111lll1l_opy_.register(bstack1lll1lll_opy_.bstack1l1l1l1lll_opy_, self.__1ll1lll1111_opy_)
        bstack111lll1l_opy_.register(bstack1lll1lll_opy_.CONNECT, self.__1ll1l1llll1_opy_)
        bstack111lll1l_opy_.register(bstack1lll1lll_opy_.bstack11llll1ll_opy_, self.__1ll1l1111ll_opy_)
        bstack111lll1l_opy_.register(bstack1lll1lll_opy_.bstack1ll11111l_opy_, self.__1ll1l111l11_opy_)
    def bstack1ll11ll1l_opy_(self):
        return not self.bstack1ll1l11llll_opy_ and os.environ.get(bstack1lll1ll111l_opy_, bstack1ll_opy_ (u"ࠣࠤᄘ")) != bstack1ll_opy_ (u"ࠤࠥᄙ")
    def is_running(self):
        if self.bstack1ll1l11llll_opy_:
            return self.bstack1lll11l1lll_opy_
        else:
            return bool(self.bstack1lll1ll1l11_opy_)
    def bstack1lll11ll1ll_opy_(self, module):
        return any(isinstance(m, module) for m in self.bstack1lll1ll11ll_opy_) and cli.is_running()
    def __1lll1111111_opy_(self, bstack1ll1l1lllll_opy_=10):
        if self.bstack1ll1l11lll1_opy_:
            return
        bstack11l1l1l1ll_opy_ = datetime.now()
        cli_listen_addr = os.environ.get(bstack1lll11l1111_opy_, self.cli_listen_addr)
        self.logger.debug(bstack1ll_opy_ (u"ࠥ࡟ࠧᄚ") + str(id(self)) + bstack1ll_opy_ (u"ࠦࡢࠦࡣࡰࡰࡱࡩࡨࡺࡩ࡯ࡩࠥᄛ"))
        channel = grpc.insecure_channel(cli_listen_addr, options=[(bstack1ll_opy_ (u"ࠧ࡭ࡲࡱࡥ࠱ࡩࡳࡧࡢ࡭ࡧࡢ࡬ࡹࡺࡰࡠࡲࡵࡳࡽࡿࠢᄜ"), 0), (bstack1ll_opy_ (u"ࠨࡧࡳࡲࡦ࠲ࡪࡴࡡࡣ࡮ࡨࡣ࡭ࡺࡴࡱࡵࡢࡴࡷࡵࡸࡺࠤᄝ"), 0)])
        grpc.channel_ready_future(channel).result(timeout=bstack1ll1l1lllll_opy_)
        self.bstack1lll1ll1l11_opy_ = channel
        self.bstack1ll1l11lll1_opy_ = sdk_pb2_grpc.SDKStub(self.bstack1lll1ll1l11_opy_)
        self.bstack11ll11ll1_opy_(bstack1ll_opy_ (u"ࠢࡨࡴࡳࡧ࠿ࡩ࡯࡯ࡰࡨࡧࡹࠨᄞ"), datetime.now() - bstack11l1l1l1ll_opy_)
        self.cli_listen_addr = cli_listen_addr
        os.environ[bstack1lll11l1111_opy_] = self.cli_listen_addr
        self.logger.debug(bstack1ll_opy_ (u"ࠣ࡝ࡾ࡭ࡩ࠮ࡳࡦ࡮ࡩ࠭ࢂࡣࠠࡤࡱࡱࡲࡪࡩࡴࡦࡦ࠽ࠤ࡮ࡹ࡟ࡤࡪ࡬ࡰࡩࡥࡰࡳࡱࡦࡩࡸࡹ࠽ࠣᄟ") + str(self.bstack1ll11ll1l_opy_()) + bstack1ll_opy_ (u"ࠤࠥᄠ"))
    def __1ll1l1111ll_opy_(self, event_name):
        if self.bstack1ll11ll1l_opy_():
            self.logger.debug(bstack1ll_opy_ (u"ࠥࡧ࡭࡯࡬ࡥ࠯ࡳࡶࡴࡩࡥࡴࡵ࠽ࠤࡸࡺ࡯ࡱࡲ࡬ࡲ࡬ࠦࡃࡍࡋࠥᄡ"))
        self.__1lll11l1ll1_opy_()
    def __1ll1l111l11_opy_(self, event_name, bstack1lll1lll111_opy_ = None, exit_code=1):
        if exit_code == 1:
            self.logger.error(bstack1ll_opy_ (u"ࠦࡘࡵ࡭ࡦࡶ࡫࡭ࡳ࡭ࠠࡸࡧࡱࡸࠥࡽࡲࡰࡰࡪࠦᄢ"))
        bstack1ll1ll11ll1_opy_ = Path(bstack1ll1ll111ll_opy_ (u"ࠧࢁࡳࡦ࡮ࡩ࠲ࡨࡲࡩࡠࡦ࡬ࡶࢂ࠵ࡵ࡯ࡪࡤࡲࡩࡲࡥࡥࡇࡵࡶࡴࡸࡳ࠯࡬ࡶࡳࡳࠨᄣ"))
        if self.bstack1lll11l11ll_opy_ and bstack1ll1ll11ll1_opy_.exists():
            with open(bstack1ll1ll11ll1_opy_, bstack1ll_opy_ (u"࠭ࡲࠨᄤ"), encoding=bstack1ll_opy_ (u"ࠧࡶࡶࡩ࠱࠽࠭ᄥ")) as fp:
                data = json.load(fp)
                try:
                    bstack1l111111_opy_(bstack1ll_opy_ (u"ࠨࡒࡒࡗ࡙࠭ᄦ"), bstack1l1lll11ll_opy_(bstack1111l1111_opy_), data, {
                        bstack1ll_opy_ (u"ࠩࡤࡹࡹ࡮ࠧᄧ"): (self.config[bstack1ll_opy_ (u"ࠪࡹࡸ࡫ࡲࡏࡣࡰࡩࠬᄨ")], self.config[bstack1ll_opy_ (u"ࠫࡦࡩࡣࡦࡵࡶࡏࡪࡿࠧᄩ")])
                    })
                except Exception as e:
                    logger.debug(bstack1l1111l1_opy_.format(str(e)))
            bstack1ll1ll11ll1_opy_.unlink()
        sys.exit(exit_code)
    @measure(event_name=EVENTS.bstack1ll1lll1lll_opy_, stage=STAGE.bstack1l1lll1ll1_opy_)
    def __1ll1lll1111_opy_(self, event_name: str, data):
        from bstack_utils.bstack11ll1llll1_opy_ import bstack1lll1ll1l1l_opy_
        self.bstack1lll111ll1l_opy_, self.bstack1lll11l11ll_opy_ = bstack1lll11111l1_opy_(data.bs_config)
        os.environ[bstack1ll_opy_ (u"ࠬࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣ࡜ࡘࡉࡕࡃࡅࡐࡊࡥࡄࡊࡔࠪᄪ")] = self.bstack1lll11l11ll_opy_
        if not self.bstack1lll111ll1l_opy_ or not self.bstack1lll11l11ll_opy_:
            raise ValueError(bstack1ll_opy_ (u"ࠨࡕ࡯ࡣࡥࡰࡪࠦࡴࡰࠢࡩ࡭ࡳࡪࠠࡵࡪࡨࠤࡘࡊࡋࠡࡅࡏࡍࠥࡨࡩ࡯ࡣࡵࡽࠧᄫ"))
        if self.bstack1ll11ll1l_opy_():
            self.__1ll1l1llll1_opy_(event_name, bstack11ll111l11_opy_())
            return
        try:
            bstack1lll1ll1l1l_opy_.end(EVENTS.bstack11ll1l11ll_opy_.value, EVENTS.bstack11ll1l11ll_opy_.value + bstack1ll_opy_ (u"ࠢ࠻ࡵࡷࡥࡷࡺࠢᄬ"), EVENTS.bstack11ll1l11ll_opy_.value + bstack1ll_opy_ (u"ࠣ࠼ࡨࡲࡩࠨᄭ"), status=True, failure=None, test_name=None)
            logger.debug(bstack1ll_opy_ (u"ࠤࡆࡳࡲࡶ࡬ࡦࡶࡨࠤࡘࡊࡋࠡࡕࡨࡸࡺࡶ࠮ࠣᄮ"))
        except Exception as e:
            logger.debug(bstack1ll_opy_ (u"ࠥࡉࡽࡩࡥࡱࡶ࡬ࡳࡳࠦࡷࡩ࡫࡯ࡩࠥࡳࡡࡳ࡭࡬ࡲ࡬ࠦ࡫ࡦࡻࠣࡱࡪࡺࡲࡪࡥࡶࠤࢀࢃࠢᄯ").format(e))
        start = datetime.now()
        is_started = self.__1lll1l1111l_opy_()
        self.bstack11ll11ll1_opy_(bstack1ll_opy_ (u"ࠦࡸࡶࡡࡸࡰࡢࡸ࡮ࡳࡥࠣᄰ"), datetime.now() - start)
        if is_started:
            start = datetime.now()
            self.__1lll1111111_opy_()
            self.bstack11ll11ll1_opy_(bstack1ll_opy_ (u"ࠧࡩ࡯࡯ࡰࡨࡧࡹࡥࡴࡪ࡯ࡨࠦᄱ"), datetime.now() - start)
            start = datetime.now()
            self.__1lll1l1l1ll_opy_(data)
            self.bstack11ll11ll1_opy_(bstack1ll_opy_ (u"ࠨࡳࡵࡣࡵࡸࡤࡹࡥࡴࡵ࡬ࡳࡳࡥࡴࡪ࡯ࡨࠦᄲ"), datetime.now() - start)
    @measure(event_name=EVENTS.bstack1lll11l1l11_opy_, stage=STAGE.bstack1l1lll1ll1_opy_)
    def __1ll1l1llll1_opy_(self, event_name: str, data: bstack11ll111l11_opy_):
        if not self.bstack1ll11ll1l_opy_():
            self.logger.debug(bstack1ll_opy_ (u"ࠢࡧࡣ࡬ࡰࡪࡪࠠࡵࡱࠣࡧࡴࡴ࡮ࡦࡥࡷ࠾ࠥࡴ࡯ࡵࠢࡤࠤࡨ࡮ࡩ࡭ࡦ࠰ࡴࡷࡵࡣࡦࡵࡶࠦᄳ"))
            return
        bin_session_id = os.environ.get(bstack1lll1ll111l_opy_)
        start = datetime.now()
        self.__1lll1111111_opy_()
        self.bstack11ll11ll1_opy_(bstack1ll_opy_ (u"ࠣࡥࡲࡲࡳ࡫ࡣࡵࡡࡷ࡭ࡲ࡫ࠢᄴ"), datetime.now() - start)
        self.cli_bin_session_id = bin_session_id
        self.logger.debug(bstack1ll_opy_ (u"ࠤ࡞ࡿ࡮ࡪࠨࡴࡧ࡯ࡪ࠮ࢃ࡝ࠡࡥ࡫࡭ࡱࡪ࠭ࡱࡴࡲࡧࡪࡹࡳ࠻ࠢࡦࡳࡳࡴࡥࡤࡶࡨࡨࠥࡺ࡯ࠡࡧࡻ࡭ࡸࡺࡩ࡯ࡩࠣࡇࡑࡏࠠࠣᄵ") + str(bin_session_id) + bstack1ll_opy_ (u"ࠥࠦᄶ"))
        start = datetime.now()
        self.__1ll1llllll1_opy_()
        self.bstack11ll11ll1_opy_(bstack1ll_opy_ (u"ࠦࡸࡺࡡࡳࡶࡢࡷࡪࡹࡳࡪࡱࡱࡣࡹ࡯࡭ࡦࠤᄷ"), datetime.now() - start)
    def __1lll1l1l1l1_opy_(self):
        if not self.bstack1ll1l11lll1_opy_ or not self.cli_bin_session_id:
            self.logger.debug(bstack1ll_opy_ (u"ࠧࡩࡡ࡯ࡰࡲࡸࠥࡩ࡯࡯ࡨ࡬࡫ࡺࡸࡥࠡ࡯ࡲࡨࡺࡲࡥࡴࠤᄸ"))
            return
        bstack1ll1llll11l_opy_ = {
            bstack1ll_opy_ (u"ࠨࡰ࡭ࡣࡼࡻࡷ࡯ࡧࡩࡶࠥᄹ"): (bstack1lll1l11111_opy_, bstack1ll1ll1l11l_opy_, bstack1ll1l1l111l_opy_),
            bstack1ll_opy_ (u"ࠢࡴࡧ࡯ࡩࡳ࡯ࡵ࡮ࠤᄺ"): (bstack1ll11lll111_opy_, bstack1ll1l1l1lll_opy_, bstack1ll1llll1l1_opy_),
        }
        if not self.bstack1ll1ll1l111_opy_ and self.session_framework in bstack1ll1llll11l_opy_:
            bstack1ll1ll11l11_opy_, bstack1ll1l11ll11_opy_, bstack1ll1ll11l1l_opy_ = bstack1ll1llll11l_opy_[self.session_framework]
            bstack1lll1l1ll1l_opy_ = bstack1ll1l11ll11_opy_()
            self.bstack1ll1lllllll_opy_ = bstack1lll1l1ll1l_opy_
            self.bstack1ll1ll1l111_opy_ = bstack1ll1ll11l1l_opy_
            self.bstack1lll1ll11ll_opy_.append(bstack1lll1l1ll1l_opy_)
            self.bstack1lll1ll11ll_opy_.append(bstack1ll1ll11l11_opy_(self.bstack1ll1lllllll_opy_))
        if not self.bstack1ll1l1l11ll_opy_ and self.config_observability and self.config_observability.success: # bstack1lll1l11ll1_opy_
            self.bstack1ll1l1l11ll_opy_ = bstack1ll1l111l1l_opy_(self.bstack1ll1ll1l111_opy_, self.bstack1ll1lllllll_opy_) # bstack1ll1l11ll1l_opy_
            self.bstack1lll1ll11ll_opy_.append(self.bstack1ll1l1l11ll_opy_)
        if not self.accessibility and self.config_accessibility and self.config_accessibility.success:
            self.accessibility = bstack1ll1l1ll1l1_opy_(self.bstack1ll1ll1l111_opy_, self.bstack1ll1lllllll_opy_)
            self.bstack1lll1ll11ll_opy_.append(self.accessibility)
        if not self.ai and isinstance(self.config, dict) and self.config.get(bstack1ll_opy_ (u"ࠣࡵࡨࡰ࡫ࡎࡥࡢ࡮ࠥᄻ"), False) == True:
            self.ai = bstack1lll1l1l11l_opy_()
            self.bstack1lll1ll11ll_opy_.append(self.ai)
        if not self.percy and self.bstack1ll1l11l1l1_opy_ and self.bstack1ll1l11l1l1_opy_.success:
            self.percy = bstack1ll1l111ll1_opy_(self.bstack1ll1l11l1l1_opy_)
            self.bstack1lll1ll11ll_opy_.append(self.percy)
        for mod in self.bstack1lll1ll11ll_opy_:
            if not mod.bstack1lll111llll_opy_():
                mod.configure(self.bstack1ll1l11lll1_opy_, self.config, self.cli_bin_session_id, self.bstack1lllll1ll1l_opy_)
    def __1ll11lll1l1_opy_(self):
        for mod in self.bstack1lll1ll11ll_opy_:
            if mod.bstack1lll111llll_opy_():
                mod.configure(self.bstack1ll1l11lll1_opy_, None, None, None)
    @measure(event_name=EVENTS.bstack1ll1ll1l1ll_opy_, stage=STAGE.bstack1l1lll1ll1_opy_)
    def __1lll1l1l1ll_opy_(self, data):
        if not self.cli_bin_session_id or self.bstack1ll1l1l11l1_opy_:
            return
        self.__1lll11llll1_opy_(data)
        bstack11l1l1l1ll_opy_ = datetime.now()
        req = structs.StartBinSessionRequest()
        req.bin_session_id = self.cli_bin_session_id
        req.path_project = os.getcwd()
        req.language = bstack1ll_opy_ (u"ࠤࡳࡽࡹ࡮࡯࡯ࠤᄼ")
        req.sdk_language = bstack1ll_opy_ (u"ࠥࡴࡾࡺࡨࡰࡰࠥᄽ")
        req.path_config = data.path_config
        req.sdk_version = data.sdk_version
        req.test_framework = data.test_framework
        req.frameworks.extend(data.frameworks)
        req.framework_versions.update(data.framework_versions)
        req.env_vars.update({key: value for key, value in os.environ.items() if bool(bstack1lll1l11l1l_opy_.search(key))})
        req.cli_args.extend(sys.argv)
        try:
            self.logger.debug(bstack1ll_opy_ (u"ࠦࡠࠨᄾ") + str(id(self)) + bstack1ll_opy_ (u"ࠧࡣࠠ࡮ࡣ࡬ࡲ࠲ࡶࡲࡰࡥࡨࡷࡸࡀࠠࡴࡶࡤࡶࡹࡥࡢࡪࡰࡢࡷࡪࡹࡳࡪࡱࡱࠦᄿ"))
            r = self.bstack1ll1l11lll1_opy_.StartBinSession(req)
            self.bstack11ll11ll1_opy_(bstack1ll_opy_ (u"ࠨࡧࡳࡲࡦ࠾ࡸࡺࡡࡳࡶࡢࡦ࡮ࡴ࡟ࡴࡧࡶࡷ࡮ࡵ࡮ࠣᅀ"), datetime.now() - bstack11l1l1l1ll_opy_)
            os.environ[bstack1lll1ll111l_opy_] = r.bin_session_id
            self.__1lll111111l_opy_(r)
            self.__1lll1l1l1l1_opy_()
            self.bstack1lllll1ll1l_opy_.start()
            self.bstack1ll1l1l11l1_opy_ = True
            self.logger.debug(bstack1ll_opy_ (u"ࠢ࡜ࠤᅁ") + str(id(self)) + bstack1ll_opy_ (u"ࠣ࡟ࠣࡱࡦ࡯࡮࠮ࡲࡵࡳࡨ࡫ࡳࡴ࠼ࠣࡧࡴࡴ࡮ࡦࡥࡷࡩࡩࠨᅂ"))
        except grpc.bstack1lll11l1l1l_opy_ as bstack1lll1l1lll1_opy_:
            self.logger.error(bstack1ll_opy_ (u"ࠤ࡞ࡿ࡮ࡪࠨࡴࡧ࡯ࡪ࠮ࢃ࡝ࠡࡶ࡬ࡱࡪࡵࡥࡶࡶ࠰ࡩࡷࡸ࡯ࡳ࠼ࠣࠦᅃ") + str(bstack1lll1l1lll1_opy_) + bstack1ll_opy_ (u"ࠥࠦᅄ"))
            traceback.print_exc()
            raise bstack1lll1l1lll1_opy_
        except grpc.RpcError as e:
            self.logger.error(bstack1ll_opy_ (u"ࠦࡠࢁࡩࡥࠪࡶࡩࡱ࡬ࠩࡾ࡟ࠣࡶࡵࡩ࠭ࡦࡴࡵࡳࡷࡀࠠࠣᅅ") + str(e) + bstack1ll_opy_ (u"ࠧࠨᅆ"))
            traceback.print_exc()
            raise e
    @measure(event_name=EVENTS.bstack1lll1111ll1_opy_, stage=STAGE.bstack1l1lll1ll1_opy_)
    def __1ll1llllll1_opy_(self):
        if not self.bstack1ll11ll1l_opy_() or not self.cli_bin_session_id or self.bstack1lll1l1ll11_opy_:
            return
        bstack11l1l1l1ll_opy_ = datetime.now()
        req = structs.ConnectBinSessionRequest()
        req.bin_session_id = self.cli_bin_session_id
        req.platform_index = int(os.environ.get(bstack1ll_opy_ (u"࠭ࡂࡓࡑ࡚ࡗࡊࡘࡓࡕࡃࡆࡏࡤࡖࡌࡂࡖࡉࡓࡗࡓ࡟ࡊࡐࡇࡉ࡝࠭ᅇ"), bstack1ll_opy_ (u"ࠧ࠱ࠩᅈ")))
        try:
            self.logger.debug(bstack1ll_opy_ (u"ࠣ࡝ࠥᅉ") + str(id(self)) + bstack1ll_opy_ (u"ࠤࡠࠤࡨ࡮ࡩ࡭ࡦ࠰ࡴࡷࡵࡣࡦࡵࡶ࠾ࠥࡩ࡯࡯ࡰࡨࡧࡹࡥࡢࡪࡰࡢࡷࡪࡹࡳࡪࡱࡱࠦᅊ"))
            r = self.bstack1ll1l11lll1_opy_.ConnectBinSession(req)
            self.bstack11ll11ll1_opy_(bstack1ll_opy_ (u"ࠥ࡫ࡷࡶࡣ࠻ࡥࡲࡲࡳ࡫ࡣࡵࡡࡥ࡭ࡳࡥࡳࡦࡵࡶ࡭ࡴࡴࠢᅋ"), datetime.now() - bstack11l1l1l1ll_opy_)
            self.__1lll111111l_opy_(r)
            self.__1lll1l1l1l1_opy_()
            self.bstack1lllll1ll1l_opy_.start()
            self.bstack1lll1l1ll11_opy_ = True
            self.logger.debug(bstack1ll_opy_ (u"ࠦࡠࠨᅌ") + str(id(self)) + bstack1ll_opy_ (u"ࠧࡣࠠࡤࡪ࡬ࡰࡩ࠳ࡰࡳࡱࡦࡩࡸࡹ࠺ࠡࡥࡲࡲࡳ࡫ࡣࡵࡧࡧࠦᅍ"))
        except grpc.bstack1lll11l1l1l_opy_ as bstack1lll1l1lll1_opy_:
            self.logger.error(bstack1ll_opy_ (u"ࠨ࡛ࡼ࡫ࡧࠬࡸ࡫࡬ࡧࠫࢀࡡࠥࡺࡩ࡮ࡧࡲࡩࡺࡺ࠭ࡦࡴࡵࡳࡷࡀࠠࠣᅎ") + str(bstack1lll1l1lll1_opy_) + bstack1ll_opy_ (u"ࠢࠣᅏ"))
            traceback.print_exc()
            raise bstack1lll1l1lll1_opy_
        except grpc.RpcError as e:
            self.logger.error(bstack1ll_opy_ (u"ࠣ࡝ࡾ࡭ࡩ࠮ࡳࡦ࡮ࡩ࠭ࢂࡣࠠࡳࡲࡦ࠱ࡪࡸࡲࡰࡴ࠽ࠤࠧᅐ") + str(e) + bstack1ll_opy_ (u"ࠤࠥᅑ"))
            traceback.print_exc()
            raise e
    def __1lll111111l_opy_(self, r):
        self.bstack1ll1l11l111_opy_(r)
        if not r.bin_session_id or not r.config or not isinstance(r.config, str):
            raise ValueError(bstack1ll_opy_ (u"ࠥࡹࡳ࡫ࡸࡱࡧࡦࡸࡪࡪࠠࡴࡧࡵࡺࡪࡸࠠࡳࡧࡶࡴࡴࡴࡳࡦࠤᅒ") + str(r))
        self.config = json.loads(r.config)
        if not self.config:
            raise ValueError(bstack1ll_opy_ (u"ࠦࡪࡳࡰࡵࡻࠣࡧࡴࡴࡦࡪࡩࠣࡪࡴࡻ࡮ࡥࠤᅓ"))
        self.session_framework = r.session_framework
        self.config_testhub = r.testhub
        self.config_observability = r.observability
        self.config_accessibility = r.accessibility
        bstack1ll_opy_ (u"ࠧࠨࠢࠋࠢࠣࠤࠥࠦࠠࠡࠢࡓࡩࡷࡩࡹࠡ࡫ࡶࠤࡸ࡫࡮ࡵࠢࡲࡲࡱࡿࠠࡢࡵࠣࡴࡦࡸࡴࠡࡱࡩࠤࡹ࡮ࡥࠡࠤࡆࡳࡳࡴࡥࡤࡶࡅ࡭ࡳ࡙ࡥࡴࡵ࡬ࡳࡳ࠲ࠢࠡࡣࡱࡨࠥࡺࡨࡪࡵࠣࡪࡺࡴࡣࡵ࡫ࡲࡲࠥ࡯ࡳࠡࡣ࡯ࡷࡴࠦࡵࡴࡧࡧࠤࡧࡿࠠࡔࡶࡤࡶࡹࡈࡩ࡯ࡕࡨࡷࡸ࡯࡯࡯࠰ࠍࠤࠥࠦࠠࠡࠢࠣࠤ࡙࡮ࡥࡳࡧࡩࡳࡷ࡫ࠬࠡࡐࡲࡲࡪࠦࡨࡢࡰࡧࡰ࡮ࡴࡧࠡ࡫ࡶࠤ࡮ࡳࡰ࡭ࡧࡰࡩࡳࡺࡥࡥ࠰ࠍࠤࠥࠦࠠࠡࠢࠣࠤࠧࠨࠢᅔ")
        self.bstack1ll1l11l1l1_opy_ = getattr(r, bstack1ll_opy_ (u"࠭ࡰࡦࡴࡦࡽࠬᅕ"), None)
        self.cli_bin_session_id = r.bin_session_id
        os.environ[bstack1ll_opy_ (u"ࠧࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡔࡆࡕࡗࡌ࡚ࡈ࡟ࡋ࡙ࡗࠫᅖ")] = self.config_testhub.jwt
        os.environ[bstack1ll_opy_ (u"ࠨࡄࡕࡓ࡜࡙ࡅࡓࡕࡗࡅࡈࡑ࡟ࡕࡇࡖࡘࡍ࡛ࡂࡠࡗࡘࡍࡉ࠭ᅗ")] = self.config_testhub.build_hashed_id
    def bstack1ll1l1l1l1l_opy_(event_name: EVENTS, stage: STAGE):
        def decorator(func):
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                if self.bstack1lll11l1lll_opy_:
                    return func(self, *args, **kwargs)
                @measure(event_name=event_name, stage=stage)
                def bstack1lll11l111l_opy_(*a, **kw):
                    return func(self, *a, **kw)
                return bstack1lll11l111l_opy_(*args, **kwargs)
            return wrapper
        return decorator
    @bstack1ll1l1l1l1l_opy_(event_name=EVENTS.bstack1ll1l1l1ll1_opy_, stage=STAGE.bstack1l1lll1ll1_opy_)
    def __1lll1l1111l_opy_(self, bstack1ll1l1lllll_opy_=10):
        if self.bstack1lll11l1lll_opy_:
            self.logger.debug(bstack1ll_opy_ (u"ࠤࡶࡸࡦࡸࡴ࠻ࠢࡤࡰࡷ࡫ࡡࡥࡻࠣࡶࡺࡴ࡮ࡪࡰࡪࠦᅘ"))
            return True
        self.logger.debug(bstack1ll_opy_ (u"ࠥࡷࡹࡧࡲࡵࠤᅙ"))
        if os.getenv(bstack1ll_opy_ (u"ࠦࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡇࡑࡏ࡟ࡆࡐ࡙ࠦᅚ")) == bstack1lll1l1llll_opy_:
            self.cli_bin_session_id = bstack1lll1l1llll_opy_
            self.cli_listen_addr = bstack1ll_opy_ (u"ࠧࡻ࡮ࡪࡺ࠽࠳ࡹࡳࡰ࠰ࡵࡧ࡯࠲ࡶ࡬ࡢࡶࡩࡳࡷࡳ࠭ࠦࡵ࠱ࡷࡴࡩ࡫ࠣᅛ") % (self.cli_bin_session_id)
            self.bstack1lll11l1lll_opy_ = True
            return True
        self.process = subprocess.Popen(
            [self.bstack1lll111ll1l_opy_, bstack1ll_opy_ (u"ࠨࡳࡥ࡭ࠥᅜ")],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=dict(os.environ),
            text=True,
            universal_newlines=True, # bstack1lll1l11lll_opy_ compat for text=True in bstack1lll11l11l1_opy_ python
            encoding=bstack1ll_opy_ (u"ࠢࡶࡶࡩ࠱࠽ࠨᅝ"),
            bufsize=1,
            close_fds=True,
        )
        bstack1ll11llll1l_opy_ = threading.Thread(target=self.__1lll1111lll_opy_, args=(bstack1ll1l1lllll_opy_,))
        bstack1ll11llll1l_opy_.start()
        bstack1ll11llll1l_opy_.join()
        if self.process.returncode is not None:
            self.logger.debug(bstack1ll_opy_ (u"ࠣ࡝ࡾ࡭ࡩ࠮ࡳࡦ࡮ࡩ࠭ࢂࡣࠠࡴࡲࡤࡻࡳࡀࠠࡳࡧࡷࡹࡷࡴࡣࡰࡦࡨࡁࢀࡹࡥ࡭ࡨ࠱ࡴࡷࡵࡣࡦࡵࡶ࠲ࡷ࡫ࡴࡶࡴࡱࡧࡴࡪࡥࡾࠢࡲࡹࡹࡃࡻࡴࡧ࡯ࡪ࠳ࡶࡲࡰࡥࡨࡷࡸ࠴ࡳࡵࡦࡲࡹࡹ࠴ࡲࡦࡣࡧࠬ࠮ࢃࠠࡦࡴࡵࡁࠧᅞ") + str(self.process.stderr.read()) + bstack1ll_opy_ (u"ࠤࠥᅟ"))
        if not self.bstack1lll11l1lll_opy_:
            self.logger.debug(bstack1ll_opy_ (u"ࠥ࡟ࠧᅠ") + str(id(self)) + bstack1ll_opy_ (u"ࠦࡢࠦࡣ࡭ࡧࡤࡲࡺࡶࠢᅡ"))
            self.__1lll11l1ll1_opy_()
        self.logger.debug(bstack1ll_opy_ (u"ࠧࡡࡻࡪࡦࠫࡷࡪࡲࡦࠪࡿࡠࠤࡵࡸ࡯ࡤࡧࡶࡷࡤࡸࡥࡢࡦࡼ࠾ࠥࠨᅢ") + str(self.bstack1lll11l1lll_opy_) + bstack1ll_opy_ (u"ࠨࠢᅣ"))
        return self.bstack1lll11l1lll_opy_
    def __1lll1111lll_opy_(self, bstack1lll1111l11_opy_=10):
        bstack1lll1l1l111_opy_ = time.time()
        while self.process and time.time() - bstack1lll1l1l111_opy_ < bstack1lll1111l11_opy_:
            try:
                line = self.process.stdout.readline()
                if bstack1ll_opy_ (u"ࠢࡪࡦࡀࠦᅤ") in line:
                    self.cli_bin_session_id = line.split(bstack1ll_opy_ (u"ࠣ࡫ࡧࡁࠧᅥ"))[-1:][0].strip()
                    self.logger.debug(bstack1ll_opy_ (u"ࠤࡦࡰ࡮ࡥࡢࡪࡰࡢࡷࡪࡹࡳࡪࡱࡱࡣ࡮ࡪ࠺ࠣᅦ") + str(self.cli_bin_session_id) + bstack1ll_opy_ (u"ࠥࠦᅧ"))
                    continue
                if bstack1ll_opy_ (u"ࠦࡱ࡯ࡳࡵࡧࡱࡁࠧᅨ") in line:
                    self.cli_listen_addr = line.split(bstack1ll_opy_ (u"ࠧࡲࡩࡴࡶࡨࡲࡂࠨᅩ"))[-1:][0].strip()
                    self.logger.debug(bstack1ll_opy_ (u"ࠨࡣ࡭࡫ࡢࡰ࡮ࡹࡴࡦࡰࡢࡥࡩࡪࡲ࠻ࠤᅪ") + str(self.cli_listen_addr) + bstack1ll_opy_ (u"ࠢࠣᅫ"))
                    continue
                if bstack1ll_opy_ (u"ࠣࡲࡲࡶࡹࡃࠢᅬ") in line:
                    port = line.split(bstack1ll_opy_ (u"ࠤࡳࡳࡷࡺ࠽ࠣᅭ"))[-1:][0].strip()
                    self.logger.debug(bstack1ll_opy_ (u"ࠥࡴࡴࡸࡴ࠻ࠤᅮ") + str(port) + bstack1ll_opy_ (u"ࠦࠧᅯ"))
                    continue
                if line.strip() == bstack1ll1l11111l_opy_ and self.cli_bin_session_id and self.cli_listen_addr:
                    if os.getenv(bstack1ll_opy_ (u"࡙ࠧࡄࡌࡡࡆࡐࡎࡥࡆࡍࡃࡊࡣࡎࡕ࡟ࡔࡖࡕࡉࡆࡓࠢᅰ"), bstack1ll_opy_ (u"ࠨ࠱ࠣᅱ")) == bstack1ll_opy_ (u"ࠢ࠲ࠤᅲ"):
                        if not self.process.stdout.closed:
                            self.process.stdout.close()
                        if not self.process.stderr.closed:
                            self.process.stderr.close()
                    self.bstack1lll11l1lll_opy_ = True
                    return True
            except Exception as e:
                self.logger.debug(bstack1ll_opy_ (u"ࠣࡧࡵࡶࡴࡸ࠺ࠡࠤᅳ") + str(e) + bstack1ll_opy_ (u"ࠤࠥᅴ"))
        return False
    @measure(event_name=EVENTS.bstack1ll1lll1ll1_opy_, stage=STAGE.bstack1l1lll1ll1_opy_)
    def __1lll11l1ll1_opy_(self):
        if self.bstack1lll1ll1l11_opy_:
            self.bstack1lllll1ll1l_opy_.stop()
            start = datetime.now()
            if self.bstack1ll1lll111l_opy_():
                self.cli_bin_session_id = None
                if self.bstack1lll1l1ll11_opy_:
                    self.bstack11ll11ll1_opy_(bstack1ll_opy_ (u"ࠥࡷࡹࡵࡰࡠࡵࡨࡷࡸ࡯࡯࡯ࡡࡷ࡭ࡲ࡫ࠢᅵ"), datetime.now() - start)
                else:
                    self.bstack11ll11ll1_opy_(bstack1ll_opy_ (u"ࠦࡸࡺ࡯ࡱࡡࡶࡩࡸࡹࡩࡰࡰࡢࡸ࡮ࡳࡥࠣᅶ"), datetime.now() - start)
            self.__1ll11lll1l1_opy_()
            start = datetime.now()
            self.bstack1lll1ll1l11_opy_.close()
            self.bstack11ll11ll1_opy_(bstack1ll_opy_ (u"ࠧࡪࡩࡴࡥࡲࡲࡳ࡫ࡣࡵࡡࡷ࡭ࡲ࡫ࠢᅷ"), datetime.now() - start)
            self.bstack1lll1ll1l11_opy_ = None
        if self.process:
            self.logger.debug(bstack1ll_opy_ (u"ࠨࡳࡵࡱࡳࠦᅸ"))
            start = datetime.now()
            self.process.terminate()
            self.bstack11ll11ll1_opy_(bstack1ll_opy_ (u"ࠢ࡬࡫࡯ࡰࡤࡺࡩ࡮ࡧࠥᅹ"), datetime.now() - start)
            self.process = None
            if self.bstack1ll1l11llll_opy_ and self.config_observability and self.config_testhub and self.config_testhub.testhub_events:
                self.bstack1ll1111l_opy_()
                self.logger.info(
                    bstack1ll_opy_ (u"ࠣࡘ࡬ࡷ࡮ࡺࠠࡩࡶࡷࡴࡸࡀ࠯࠰ࡣࡸࡸࡴࡳࡡࡵ࡫ࡲࡲ࠳ࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮࠲ࡨࡵ࡭࠰ࡤࡸ࡭ࡱࡪࡳ࠰ࡽࢀࠤࡹࡵࠠࡷ࡫ࡨࡻࠥࡨࡵࡪ࡮ࡧࠤࡷ࡫ࡰࡰࡴࡷ࠰ࠥ࡯࡮ࡴ࡫ࡪ࡬ࡹࡹࠬࠡࡣࡱࡨࠥࡳࡡ࡯ࡻࠣࡱࡴࡸࡥࠡࡦࡨࡦࡺ࡭ࡧࡪࡰࡪࠤ࡮ࡴࡦࡰࡴࡰࡥࡹ࡯࡯࡯ࠢࡤࡰࡱࠦࡡࡵࠢࡲࡲࡪࠦࡰ࡭ࡣࡦࡩࠦࡢ࡮ࠣᅺ").format(
                        self.config_testhub.build_hashed_id
                    )
                )
                os.environ[bstack1ll_opy_ (u"ࠩࡅࡗࡤ࡚ࡅࡔࡖࡒࡔࡘࡥࡂࡖࡋࡏࡈࡤࡎࡁࡔࡊࡈࡈࡤࡏࡄࠨᅻ")] = self.config_testhub.build_hashed_id
        self.bstack1lll11l1lll_opy_ = False
    def __1lll11llll1_opy_(self, data):
        try:
            import selenium
            data.framework_versions[bstack1ll_opy_ (u"ࠥࡷࡪࡲࡥ࡯࡫ࡸࡱࠧᅼ")] = selenium.__version__
            data.frameworks.append(bstack1ll_opy_ (u"ࠦࡸ࡫࡬ࡦࡰ࡬ࡹࡲࠨᅽ"))
        except:
            pass
        try:
            from playwright._repo_version import __version__
            data.framework_versions[bstack1ll_opy_ (u"ࠧࡶ࡬ࡢࡻࡺࡶ࡮࡭ࡨࡵࠤᅾ")] = __version__
            data.frameworks.append(bstack1ll_opy_ (u"ࠨࡰ࡭ࡣࡼࡻࡷ࡯ࡧࡩࡶࠥᅿ"))
        except:
            pass
    def bstack1ll1l1l1111_opy_(self, hub_url: str, platform_index: int, bstack1l1ll111_opy_: Any):
        if self.bstack1lll1lll1l1_opy_:
            self.logger.debug(bstack1ll_opy_ (u"ࠢࡴ࡭࡬ࡴࡵ࡫ࡤࠡࡵࡨࡸࡺࡶࠠࡴࡧ࡯ࡩࡳ࡯ࡵ࡮࠼ࠣࡥࡱࡸࡥࡢࡦࡼࠤࡸ࡫ࡴࠡࡷࡳࠦᆀ"))
            return
        try:
            bstack11l1l1l1ll_opy_ = datetime.now()
            import selenium
            from selenium.webdriver.remote.webdriver import WebDriver
            from selenium.webdriver.common.service import Service
            framework = bstack1ll_opy_ (u"ࠣࡵࡨࡰࡪࡴࡩࡶ࡯ࠥᆁ")
            self.bstack1lll1lll1l1_opy_ = bstack1ll1llll1l1_opy_(
                cli.config.get(bstack1ll_opy_ (u"ࠤ࡫ࡹࡧ࡛ࡲ࡭ࠤᆂ"), hub_url),
                platform_index,
                framework_name=framework,
                framework_version=selenium.__version__,
                classes=[WebDriver],
                bstack1ll1l1ll1ll_opy_={bstack1ll_opy_ (u"ࠥࡧࡷ࡫ࡡࡵࡧࡢࡳࡵࡺࡩࡰࡰࡶࡣ࡫ࡸ࡯࡮ࡡࡦࡥࡵࡹࠢᆃ"): bstack1l1ll111_opy_}
            )
            def bstack1ll1ll11111_opy_(self):
                return
            if self.config.get(bstack1ll_opy_ (u"ࠦࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭ࡄࡹࡹࡵ࡭ࡢࡶ࡬ࡳࡳࠨᆄ"), True):
                Service.start = bstack1ll1ll11111_opy_
                Service.stop = bstack1ll1ll11111_opy_
            def get_accessibility_results(driver):
                if self.accessibility and self.accessibility.is_enabled():
                    return self.accessibility.get_accessibility_results(driver, framework_name=framework)
            def get_accessibility_results_summary(driver):
                if self.accessibility and self.accessibility.is_enabled():
                    return self.accessibility.get_accessibility_results_summary(driver, framework_name=framework)
            def perform_scan(driver):
                if self.accessibility and self.accessibility.is_enabled():
                    return self.accessibility.perform_scan(driver, method=None, framework_name=framework)
            WebDriver.getAccessibilityResults = get_accessibility_results
            WebDriver.get_accessibility_results = get_accessibility_results
            WebDriver.getAccessibilityResultsSummary = get_accessibility_results_summary
            WebDriver.get_accessibility_results_summary = get_accessibility_results_summary
            WebDriver.upload_attachment = staticmethod(bstack1l11l11ll_opy_.upload_attachment)
            WebDriver.set_custom_tag = staticmethod(bstack1lll1ll1111_opy_.set_custom_tag)
            WebDriver.performScan = perform_scan
            WebDriver.perform_scan = perform_scan
            self.bstack11ll11ll1_opy_(bstack1ll_opy_ (u"ࠧࡹࡥࡵࡷࡳࡣࡸ࡫࡬ࡦࡰ࡬ࡹࡲࠨᆅ"), datetime.now() - bstack11l1l1l1ll_opy_)
        except Exception as e:
            self.logger.error(bstack1ll_opy_ (u"ࠨࡦࡢ࡫࡯ࡩࡩࠦࡴࡰࠢࡶࡩࡹࡻࡰࠡࡵࡨࡰࡪࡴࡩࡶ࡯࠽ࠤࠧᆆ") + str(e) + bstack1ll_opy_ (u"ࠢࠣᆇ"))
    def bstack1ll1lll1l11_opy_(self, platform_index: int):
        try:
            from playwright.sync_api import BrowserType
            from playwright.sync_api import BrowserContext
            from playwright._impl._connection import Connection
            from playwright._repo_version import __version__
            from bstack_utils.helper import bstack111lllll1_opy_
            self.bstack1lll1lll1l1_opy_ = bstack1ll1l1l111l_opy_(
                platform_index,
                framework_name=bstack1ll_opy_ (u"ࠣࡲ࡯ࡥࡾࡽࡲࡪࡩ࡫ࡸࠧᆈ"),
                framework_version=__version__,
                classes=[BrowserType, BrowserContext, Connection],
            )
        except Exception as e:
            self.logger.error(bstack1ll_opy_ (u"ࠤࡩࡥ࡮ࡲࡥࡥࠢࡷࡳࠥࡹࡥࡵࡷࡳࠤࡵࡲࡡࡺࡹࡵ࡭࡬࡮ࡴ࠻ࠢࠥᆉ") + str(e) + bstack1ll_opy_ (u"ࠥࠦᆊ"))
            pass
    def bstack1lll111l1l1_opy_(self):
        if self.test_framework:
            self.logger.debug(bstack1ll_opy_ (u"ࠦࡸࡱࡩࡱࡲࡨࡨࠥࡹࡥࡵࡷࡳࠤࡵࡿࡴࡦࡵࡷ࠾ࠥࡧ࡬ࡳࡧࡤࡨࡾࠦࡳࡦࡶࠣࡹࡵࠨᆋ"))
            return
        if bstack1ll1l1l1ll_opy_():
            import pytest
            self.test_framework = PytestBDDFramework({ bstack1ll_opy_ (u"ࠧࡶࡹࡵࡧࡶࡸࠧᆌ"): pytest.__version__ }, [bstack1ll_opy_ (u"ࠨࡰࡺࡶࡨࡷࡹ࠳ࡢࡥࡦࠥᆍ")], self.bstack1lllll1ll1l_opy_, self.bstack1ll1l11lll1_opy_)
            return
        try:
            import pytest
            self.test_framework = bstack1lll1lll11l_opy_({ bstack1ll_opy_ (u"ࠢࡱࡻࡷࡩࡸࡺࠢᆎ"): pytest.__version__ }, [bstack1ll_opy_ (u"ࠣࡲࡼࡸࡪࡹࡴࠣᆏ")], self.bstack1lllll1ll1l_opy_, self.bstack1ll1l11lll1_opy_)
        except Exception as e:
            self.logger.error(bstack1ll_opy_ (u"ࠤࡩࡥ࡮ࡲࡥࡥࠢࡷࡳࠥࡹࡥࡵࡷࡳࠤࡵࡿࡴࡦࡵࡷ࠾ࠥࠨᆐ") + str(e) + bstack1ll_opy_ (u"ࠥࠦᆑ"))
        self.bstack1lll111l11l_opy_()
    def bstack1lll111l11l_opy_(self):
        if not self.bstack11111l1l_opy_():
            return
        bstack1l11lll111_opy_ = None
        def bstack1lll111l1_opy_(config, startdir):
            return bstack1ll_opy_ (u"ࠦࡩࡸࡩࡷࡧࡵ࠾ࠥࢁ࠰ࡾࠤᆒ").format(bstack1ll_opy_ (u"ࠧࡈࡲࡰࡹࡶࡩࡷ࡙ࡴࡢࡥ࡮ࠦᆓ"))
        def bstack1llllll1l1_opy_():
            return
        def bstack1l1l1lll1l_opy_(self, name: str, default=Notset(), skip: bool = False):
            if str(name).lower() == bstack1ll_opy_ (u"࠭ࡤࡳ࡫ࡹࡩࡷ࠭ᆔ"):
                return bstack1ll_opy_ (u"ࠢࡃࡴࡲࡻࡸ࡫ࡲࡔࡶࡤࡧࡰࠨᆕ")
            else:
                return bstack1l11lll111_opy_(self, name, default, skip)
        try:
            from pytest_selenium import pytest_selenium
            from _pytest.config import Config
            bstack1l11lll111_opy_ = Config.getoption
            pytest_selenium.pytest_report_header = bstack1lll111l1_opy_
            from pytest_selenium.drivers import browserstack
            browserstack.pytest_selenium_runtest_makereport = bstack1llllll1l1_opy_
            Config.getoption = bstack1l1l1lll1l_opy_
        except Exception as e:
            self.logger.error(bstack1ll_opy_ (u"ࠣࡈࡤ࡭ࡱ࡫ࡤࠡࡶࡲࠤࡵࡧࡴࡤࡪࠣࡴࡾࡺࡥࡴࡶࠣࡷࡪࡲࡥ࡯࡫ࡸࡱࠥ࡬࡯ࡳࠢࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫࠻ࠢࠥᆖ") + str(e) + bstack1ll_opy_ (u"ࠤࠥᆗ"))
    def bstack1ll1l111lll_opy_(self):
        bstack11lll1ll1l_opy_ = MessageToDict(cli.config_testhub, preserving_proto_field_name=True)
        if isinstance(bstack11lll1ll1l_opy_, dict):
            if cli.config_observability:
                bstack11lll1ll1l_opy_.update(
                    {bstack1ll_opy_ (u"ࠥࡳࡧࡹࡥࡳࡸࡤࡦ࡮ࡲࡩࡵࡻࠥᆘ"): MessageToDict(cli.config_observability, preserving_proto_field_name=True)}
                )
            if cli.config_accessibility:
                accessibility = MessageToDict(cli.config_accessibility, preserving_proto_field_name=True)
                if isinstance(accessibility, dict) and bstack1ll_opy_ (u"ࠦࡨࡵ࡭࡮ࡣࡱࡨࡸࡥࡴࡰࡡࡺࡶࡦࡶࠢᆙ") in accessibility.get(bstack1ll_opy_ (u"ࠧࡵࡰࡵ࡫ࡲࡲࡸࠨᆚ"), {}):
                    bstack1ll1ll11lll_opy_ = accessibility.get(bstack1ll_opy_ (u"ࠨ࡯ࡱࡶ࡬ࡳࡳࡹࠢᆛ"))
                    bstack1ll1ll11lll_opy_.update({ bstack1ll_opy_ (u"ࠢࡤࡱࡰࡱࡦࡴࡤࡴࡖࡲ࡛ࡷࡧࡰࠣᆜ"): bstack1ll1ll11lll_opy_.pop(bstack1ll_opy_ (u"ࠣࡥࡲࡱࡲࡧ࡮ࡥࡵࡢࡸࡴࡥࡷࡳࡣࡳࠦᆝ")) })
                bstack11lll1ll1l_opy_.update({bstack1ll_opy_ (u"ࠤࡤࡧࡨ࡫ࡳࡴ࡫ࡥ࡭ࡱ࡯ࡴࡺࠤᆞ"): accessibility })
        return bstack11lll1ll1l_opy_
    @measure(event_name=EVENTS.bstack1ll1l1lll1l_opy_, stage=STAGE.bstack1l1lll1ll1_opy_)
    def bstack1ll1lll111l_opy_(self, bstack1ll1lllll1l_opy_: str = None, bstack1ll1ll111l1_opy_: str = None, exit_code: int = None):
        if not self.cli_bin_session_id or not self.bstack1ll1l11lll1_opy_:
            return
        bstack11l1l1l1ll_opy_ = datetime.now()
        req = structs.StopBinSessionRequest()
        req.bin_session_id = self.cli_bin_session_id
        if exit_code:
            req.exit_code = exit_code
        if bstack1ll1lllll1l_opy_:
            req.bstack1ll1lllll1l_opy_ = bstack1ll1lllll1l_opy_
        if bstack1ll1ll111l1_opy_:
            req.bstack1ll1ll111l1_opy_ = bstack1ll1ll111l1_opy_
        try:
            r = self.bstack1ll1l11lll1_opy_.StopBinSession(req)
            SDKCLI.automate_buildlink = r.automate_buildlink
            SDKCLI.hashed_id = r.hashed_id
            self.bstack11ll11ll1_opy_(bstack1ll_opy_ (u"ࠥ࡫ࡷࡶࡣ࠻ࡵࡷࡳࡵࡥࡢࡪࡰࡢࡷࡪࡹࡳࡪࡱࡱࠦᆟ"), datetime.now() - bstack11l1l1l1ll_opy_)
            return r.success
        except grpc.RpcError as e:
            traceback.print_exc()
            raise e
    def bstack11ll11ll1_opy_(self, key: str, value: timedelta):
        tag = bstack1ll_opy_ (u"ࠦࡨ࡮ࡩ࡭ࡦ࠰ࡴࡷࡵࡣࡦࡵࡶࠦᆠ") if self.bstack1ll11ll1l_opy_() else bstack1ll_opy_ (u"ࠧࡳࡡࡪࡰ࠰ࡴࡷࡵࡣࡦࡵࡶࠦᆡ")
        self.bstack1ll11lllll1_opy_[bstack1ll_opy_ (u"ࠨ࠺ࠣᆢ").join([tag + bstack1ll_opy_ (u"ࠢ࠮ࠤᆣ") + str(id(self)), key])] += value
    def bstack1ll1111l_opy_(self):
        if not os.getenv(bstack1ll_opy_ (u"ࠣࡆࡈࡆ࡚ࡍ࡟ࡑࡇࡕࡊࠧᆤ"), bstack1ll_opy_ (u"ࠤ࠳ࠦᆥ")) == bstack1ll_opy_ (u"ࠥ࠵ࠧᆦ"):
            return
        bstack1lll111ll11_opy_ = dict()
        bstack1lllll111ll_opy_ = []
        if self.test_framework:
            bstack1lllll111ll_opy_.extend(list(self.test_framework.bstack1lllll111ll_opy_.values()))
        if self.bstack1lll1lll1l1_opy_:
            bstack1lllll111ll_opy_.extend(list(self.bstack1lll1lll1l1_opy_.bstack1lllll111ll_opy_.values()))
        for instance in bstack1lllll111ll_opy_:
            if not instance.platform_index in bstack1lll111ll11_opy_:
                bstack1lll111ll11_opy_[instance.platform_index] = defaultdict(lambda: timedelta(microseconds=0))
            report = bstack1lll111ll11_opy_[instance.platform_index]
            for k, v in instance.bstack1lll1111l1l_opy_().items():
                report[k] += v
                report[k.split(bstack1ll_opy_ (u"ࠦ࠿ࠨᆧ"))[0]] += v
        bstack1lll1l111l1_opy_ = sorted([(k, v) for k, v in self.bstack1ll11lllll1_opy_.items()], key=lambda o: o[1], reverse=True)
        bstack1ll1lll11ll_opy_ = 0
        for r in bstack1lll1l111l1_opy_:
            bstack1ll1l1l1l11_opy_ = r[1].total_seconds()
            bstack1ll1lll11ll_opy_ += bstack1ll1l1l1l11_opy_
            self.logger.debug(bstack1ll_opy_ (u"ࠧࡡࡰࡦࡴࡩࡡࠥࡩ࡬ࡪ࠼ࡾࡶࡠ࠶࡝ࡾ࠿ࠥᆨ") + str(bstack1ll1l1l1l11_opy_) + bstack1ll_opy_ (u"ࠨࠢᆩ"))
        self.logger.debug(bstack1ll_opy_ (u"ࠢ࠮࠯ࠥᆪ"))
        bstack1ll1l1lll11_opy_ = []
        for platform_index, report in bstack1lll111ll11_opy_.items():
            bstack1ll1l1lll11_opy_.extend([(platform_index, k, v) for k, v in report.items()])
        bstack1ll1l1lll11_opy_.sort(key=lambda o: o[2], reverse=True)
        bstack1l111l1l1l_opy_ = set()
        bstack1lll11ll111_opy_ = 0
        for r in bstack1ll1l1lll11_opy_:
            bstack1ll1l1l1l11_opy_ = r[2].total_seconds()
            bstack1lll11ll111_opy_ += bstack1ll1l1l1l11_opy_
            bstack1l111l1l1l_opy_.add(r[0])
            self.logger.debug(bstack1ll_opy_ (u"ࠣ࡝ࡳࡩࡷ࡬࡝ࠡࡶࡨࡷࡹࡀࡰ࡭ࡣࡷࡪࡴࡸ࡭࠮ࡽࡵ࡟࠵ࡣࡽ࠻ࡽࡵ࡟࠶ࡣࡽ࠾ࠤᆫ") + str(bstack1ll1l1l1l11_opy_) + bstack1ll_opy_ (u"ࠤࠥᆬ"))
        if self.bstack1ll11ll1l_opy_():
            self.logger.debug(bstack1ll_opy_ (u"ࠥ࠱࠲ࠨᆭ"))
            self.logger.debug(bstack1ll_opy_ (u"ࠦࡠࡶࡥࡳࡨࡠࠤࡨࡲࡩ࠻ࡥ࡫࡭ࡱࡪ࠭ࡱࡴࡲࡧࡪࡹࡳ࠾ࡽࡷࡳࡹࡧ࡬ࡠࡥ࡯࡭ࢂࠦࡴࡦࡵࡷ࠾ࡵࡲࡡࡵࡨࡲࡶࡲࡹ࠭ࡼࡵࡷࡶ࠭ࡶ࡬ࡢࡶࡩࡳࡷࡳࡳࠪࡿࡀࠦᆮ") + str(bstack1lll11ll111_opy_) + bstack1ll_opy_ (u"ࠧࠨᆯ"))
        else:
            self.logger.debug(bstack1ll_opy_ (u"ࠨ࡛ࡱࡧࡵࡪࡢࠦࡣ࡭࡫࠽ࡱࡦ࡯࡮࠮ࡲࡵࡳࡨ࡫ࡳࡴ࠿ࠥᆰ") + str(bstack1ll1lll11ll_opy_) + bstack1ll_opy_ (u"ࠢࠣᆱ"))
        self.logger.debug(bstack1ll_opy_ (u"ࠣ࠯࠰ࠦᆲ"))
    def test_orchestration_session(self, test_files: list, orchestration_strategy: str, orchestration_metadata: str):
        request = structs.TestOrchestrationRequest(
            bin_session_id=self.cli_bin_session_id,
            orchestration_strategy=orchestration_strategy,
            test_files=test_files,
            orchestration_metadata=orchestration_metadata
        )
        if not self.bstack1ll1l11lll1_opy_:
            self.logger.error(bstack1ll_opy_ (u"ࠤࡦࡰ࡮ࡥࡳࡦࡴࡹ࡭ࡨ࡫ࠠࡪࡵࠣࡲࡴࡺࠠࡪࡰ࡬ࡸ࡮ࡧ࡬ࡪࡼࡨࡨ࠳ࠦࡃࡢࡰࡱࡳࡹࠦࡰࡦࡴࡩࡳࡷࡳࠠࡵࡧࡶࡸࠥࡵࡲࡤࡪࡨࡷࡹࡸࡡࡵ࡫ࡲࡲ࠳ࠨᆳ"))
            return None
        response = self.bstack1ll1l11lll1_opy_.TestOrchestration(request)
        self.logger.debug(bstack1ll_opy_ (u"ࠥࡸࡪࡹࡴ࠮ࡱࡵࡧ࡭࡫ࡳࡵࡴࡤࡸ࡮ࡵ࡮࠮ࡵࡨࡷࡸ࡯࡯࡯࠿ࡾࢁࠧᆴ").format(response))
        if response.success:
            return list(response.ordered_test_files)
        return None
    def bstack1ll1l11l111_opy_(self, r):
        if r is not None and getattr(r, bstack1ll_opy_ (u"ࠫࡹ࡫ࡳࡵࡪࡸࡦࠬᆵ"), None) and getattr(r.testhub, bstack1ll_opy_ (u"ࠬ࡫ࡲࡳࡱࡵࡷࠬᆶ"), None):
            errors = json.loads(r.testhub.errors.decode(bstack1ll_opy_ (u"ࠨࡵࡵࡨ࠰࠼ࠧᆷ")))
            for bstack1ll1lllll11_opy_, err in errors.items():
                if err[bstack1ll_opy_ (u"ࠧࡵࡻࡳࡩࠬᆸ")] == bstack1ll_opy_ (u"ࠨ࡫ࡱࡪࡴ࠭ᆹ"):
                    self.logger.info(err[bstack1ll_opy_ (u"ࠩࡰࡩࡸࡹࡡࡨࡧࠪᆺ")])
                else:
                    self.logger.error(err[bstack1ll_opy_ (u"ࠪࡱࡪࡹࡳࡢࡩࡨࠫᆻ")])
    def bstack11111lll_opy_(self):
        return SDKCLI.automate_buildlink, SDKCLI.hashed_id
cli = SDKCLI()