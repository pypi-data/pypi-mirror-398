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
from datetime import datetime
import os
import threading
from browserstack_sdk.sdk_cli.bstack1lll1lll1l1_opy_ import (
    bstack1llll11l1l1_opy_,
    bstack1lllll111l1_opy_,
    bstack1llll1ll1ll_opy_,
    bstack1llll111ll1_opy_,
)
from browserstack_sdk.sdk_cli.bstack1lll11lll11_opy_ import bstack1ll1llll1l1_opy_
from browserstack_sdk.sdk_cli.test_framework import TestFramework, bstack1ll1ll1lll1_opy_, bstack1ll1l1ll11l_opy_, bstack1ll1l1ll111_opy_
from typing import Tuple, Dict, Any, List, Union
from browserstack_sdk import sdk_pb2 as structs
from browserstack_sdk.sdk_cli.bstack1lll11ll1l1_opy_ import bstack1ll1lll1l1l_opy_
from browserstack_sdk.sdk_cli.bstack1ll1ll1111l_opy_ import bstack1ll1l1l1lll_opy_
from browserstack_sdk.sdk_cli.bstack1ll11lll11l_opy_ import bstack1ll1ll1l11l_opy_
from browserstack_sdk.sdk_cli.bstack1ll1llll111_opy_ import bstack1ll1l1l111l_opy_
from bstack_utils.helper import bstack1l1llllll1l_opy_
from bstack_utils.measure import measure
from bstack_utils.constants import *
from bstack_utils.bstack11ll1llll1_opy_ import bstack1lll1ll1l1l_opy_
import grpc
import traceback
import json
class bstack1ll1l1ll1l1_opy_(bstack1ll1lll1l1l_opy_):
    bstack1ll111l1l1l_opy_ = False
    bstack1ll111l111l_opy_ = bstack1ll_opy_ (u"ࠢࡴࡧ࡯ࡩࡳ࡯ࡵ࡮࠰ࡺࡩࡧࡪࡲࡪࡸࡨࡶࠧᇔ")
    bstack1ll111l1ll1_opy_ = bstack1ll_opy_ (u"ࠣࡴࡨࡱࡴࡺࡥ࠯ࡹࡨࡦࡩࡸࡩࡷࡧࡵࠦᇕ")
    bstack1ll11l1ll11_opy_ = bstack1ll_opy_ (u"ࠤࡤࡧࡨ࡫ࡳࡴ࡫ࡥ࡭ࡱ࡯ࡴࡺࡡ࡬ࡲ࡮ࡺࠢᇖ")
    bstack1ll11l111l1_opy_ = bstack1ll_opy_ (u"ࠥࡥࡨࡩࡥࡴࡵ࡬ࡦ࡮ࡲࡩࡵࡻࡢ࡭ࡸࡥࡳࡤࡣࡱࡲ࡮ࡴࡧࠣᇗ")
    bstack1l1lll1llll_opy_ = bstack1ll_opy_ (u"ࠦࡩࡸࡩࡷࡧࡵࡣ࡭ࡧࡳࡠࡷࡵࡰࠧᇘ")
    scripts: Dict[str, Dict[str, str]]
    commands: Dict[str, Dict[str, Dict[str, List[str]]]]
    def __init__(self, bstack1ll1ll1l111_opy_, bstack1ll1lllllll_opy_):
        super().__init__()
        self.scripts = dict()
        self.commands = dict()
        self.accessibility = False
        self.bstack1ll111ll1ll_opy_ = False
        self.bstack1ll111l11ll_opy_ = dict()
        self.bstack1ll111ll11l_opy_ = False
        self.bstack1ll11l11ll1_opy_ = dict()
        if not self.is_enabled():
            return
        self.bstack1ll11l1l1l1_opy_ = bstack1ll1lllllll_opy_
        bstack1ll1ll1l111_opy_.bstack1ll1111l11l_opy_((bstack1llll11l1l1_opy_.bstack1llll1l1111_opy_, bstack1lllll111l1_opy_.PRE), self.bstack1ll11111111_opy_)
        TestFramework.bstack1ll1111l11l_opy_((bstack1ll1ll1lll1_opy_.TEST, bstack1ll1l1ll11l_opy_.PRE), self.bstack1ll1111111l_opy_)
        TestFramework.bstack1ll1111l11l_opy_((bstack1ll1ll1lll1_opy_.TEST, bstack1ll1l1ll11l_opy_.POST), self.bstack1ll11111l11_opy_)
    def is_enabled(self) -> bool:
        return True
    def bstack1ll1111111l_opy_(
        self,
        f: TestFramework,
        instance: bstack1ll1l1ll111_opy_,
        bstack1lllll11l1l_opy_: Tuple[bstack1ll1ll1lll1_opy_, bstack1ll1l1ll11l_opy_],
        *args,
        **kwargs,
    ):
        tags = self._1ll11111lll_opy_(instance, args)
        test_framework = f.bstack1llll1l111l_opy_(instance, TestFramework.bstack1l1lll1lll1_opy_)
        if self.bstack1ll111ll1ll_opy_:
            self.bstack1ll111l11ll_opy_[bstack1ll_opy_ (u"ࠧࡺࡥࡴࡶࡢࡶࡺࡴ࡟ࡶࡷ࡬ࡨࠧᇙ")] = f.bstack1llll1l111l_opy_(instance, TestFramework.bstack1ll111lll1l_opy_)
        if bstack1ll_opy_ (u"࠭ࡰࡺࡶࡨࡷࡹ࠳ࡢࡥࡦࠪᇚ") in instance.bstack1ll1111lll1_opy_:
            platform_index = f.bstack1llll1l111l_opy_(instance, TestFramework.bstack1l1lll1l1ll_opy_)
            self.accessibility = self.bstack1l1llllllll_opy_(tags, self.config[bstack1ll_opy_ (u"ࠧࡱ࡮ࡤࡸ࡫ࡵࡲ࡮ࡵࠪᇛ")][platform_index])
        else:
            capabilities = self.bstack1ll11l1l1l1_opy_.bstack1ll11l11111_opy_(f, instance, bstack1lllll11l1l_opy_, *args, **kwargs)
            if not capabilities:
                self.logger.debug(bstack1ll_opy_ (u"ࠣࡱࡱࡣࡧ࡫ࡦࡰࡴࡨࡣࡹ࡫ࡳࡵ࠼ࠣࡲࡴࠦࡣࡢࡲࡤࡦ࡮ࡲࡩࡵ࡫ࡨࡷࠥ࡬࡯ࡶࡰࡧࠤ࡫ࡵࡲࠡࡪࡲࡳࡰࡥࡩ࡯ࡨࡲࡁࢀ࡮࡯ࡰ࡭ࡢ࡭ࡳ࡬࡯ࡾࠢࡤࡶ࡬ࡹ࠽ࡼࡣࡵ࡫ࡸࢃࠠ࡬ࡹࡤࡶ࡬ࡹ࠽ࠣᇜ") + str(kwargs) + bstack1ll_opy_ (u"ࠤࠥᇝ"))
                return
            self.accessibility = self.bstack1l1llllllll_opy_(tags, capabilities)
        if self.bstack1ll11l1l1l1_opy_.pages and self.bstack1ll11l1l1l1_opy_.pages.values():
            bstack1ll111llll1_opy_ = list(self.bstack1ll11l1l1l1_opy_.pages.values())
            if bstack1ll111llll1_opy_ and isinstance(bstack1ll111llll1_opy_[0], (list, tuple)) and bstack1ll111llll1_opy_[0]:
                bstack1ll11111ll1_opy_ = bstack1ll111llll1_opy_[0][0]
                if callable(bstack1ll11111ll1_opy_):
                    page = bstack1ll11111ll1_opy_()
                    def bstack1ll111l11_opy_():
                        self.get_accessibility_results(page, bstack1ll_opy_ (u"ࠥࡴࡱࡧࡹࡸࡴ࡬࡫࡭ࡺࠢᇞ"))
                    def bstack1ll11111l1l_opy_():
                        self.get_accessibility_results_summary(page, bstack1ll_opy_ (u"ࠦࡵࡲࡡࡺࡹࡵ࡭࡬࡮ࡴࠣᇟ"))
                    setattr(page, bstack1ll_opy_ (u"ࠧ࡭ࡥࡵࡃࡦࡧࡪࡹࡳࡪࡤ࡬ࡰ࡮ࡺࡹࡓࡧࡶࡹࡱࡺࡳࠣᇠ"), bstack1ll111l11_opy_)
                    setattr(page, bstack1ll_opy_ (u"ࠨࡧࡦࡶࡄࡧࡨ࡫ࡳࡴ࡫ࡥ࡭ࡱ࡯ࡴࡺࡔࡨࡷࡺࡲࡴࡔࡷࡰࡱࡦࡸࡹࠣᇡ"), bstack1ll11111l1l_opy_)
        self.logger.debug(bstack1ll_opy_ (u"ࠢࡴࡪࡲࡹࡱࡪࠠࡳࡷࡱࠤࡦࡩࡣࡦࡵࡶ࡭ࡧ࡯࡬ࡪࡶࡼࠤࡻࡧ࡬ࡶࡧࡀࠦᇢ") + str(self.accessibility) + bstack1ll_opy_ (u"ࠣࠤᇣ"))
    def bstack1ll11111111_opy_(
        self,
        f: bstack1ll1llll1l1_opy_,
        driver: object,
        exec: Tuple[bstack1llll111ll1_opy_, str],
        bstack1lllll11l1l_opy_: Tuple[bstack1llll11l1l1_opy_, bstack1lllll111l1_opy_],
        result: Any,
        *args,
        **kwargs,
    ):
        try:
            bstack11l1l1l1ll_opy_ = datetime.now()
            self.bstack1ll11l111ll_opy_(f, exec, *args, **kwargs)
            instance, method_name = exec
            instance.bstack11ll11ll1_opy_(bstack1ll_opy_ (u"ࠤࡤ࠵࠶ࡿ࠺ࡪࡰ࡬ࡸࡤࡧࡣࡤࡧࡶࡷ࡮ࡨࡩ࡭࡫ࡷࡽࡤࡩ࡯࡯ࡨ࡬࡫ࠧᇤ"), datetime.now() - bstack11l1l1l1ll_opy_)
            if (
                not f.bstack1ll11l1l111_opy_(method_name)
                or f.bstack1l1lll1ll1l_opy_(method_name, *args)
                or f.bstack1l1llll111l_opy_(method_name, *args)
            ):
                return
            if not f.bstack1llll1l111l_opy_(instance, bstack1ll1l1ll1l1_opy_.bstack1ll11l1ll11_opy_, False):
                if not bstack1ll1l1ll1l1_opy_.bstack1ll111l1l1l_opy_:
                    self.logger.warning(bstack1ll_opy_ (u"ࠥ࡟ࡵࡲࡡࡵࡨࡲࡶࡲࡥࡩ࡯ࡦࡨࡼࡂࠨᇥ") + str(f.platform_index) + bstack1ll_opy_ (u"ࠦࡢࠦࡡ࠲࠳ࡼࠤࡨࡧࡰࡢࡤ࡬ࡰ࡮ࡺࡩࡦࡵࠣ࡬ࡦࡼࡥࠡࡰࡲࡸࠥࡨࡥࡦࡰࠣࡷࡪࡺࠠࡧࡱࡵࠤࡹ࡮ࡩࡴࠢࡶࡩࡸࡹࡩࡰࡰࠥᇦ"))
                    bstack1ll1l1ll1l1_opy_.bstack1ll111l1l1l_opy_ = True
                return
            bstack1l1lllllll1_opy_ = self.scripts.get(f.framework_name, {})
            if not bstack1l1lllllll1_opy_:
                platform_index = f.bstack1llll1l111l_opy_(instance, bstack1ll1llll1l1_opy_.bstack1l1lll1l1ll_opy_, 0)
                self.logger.debug(bstack1ll_opy_ (u"ࠧࡴ࡯ࠡࡣ࠴࠵ࡾࠦࡳࡤࡴ࡬ࡴࡹࡹࠠࡧࡱࡵࠤࡵࡲࡡࡵࡨࡲࡶࡲࡥࡩ࡯ࡦࡨࡼࡂࢁࡰ࡭ࡣࡷࡪࡴࡸ࡭ࡠ࡫ࡱࡨࡪࡾࡽࠡࡨࡵࡥࡲ࡫ࡷࡰࡴ࡮ࡣࡳࡧ࡭ࡦ࠿ࠥᇧ") + str(f.framework_name) + bstack1ll_opy_ (u"ࠨࠢᇨ"))
                return
            command_name = f.bstack1ll11l1llll_opy_(*args)
            if not command_name:
                self.logger.debug(bstack1ll_opy_ (u"ࠢ࡮࡫ࡶࡷ࡮ࡴࡧࠡࡥࡲࡱࡲࡧ࡮ࡥࡡࡱࡥࡲ࡫ࠠࡧࡱࡵࠤ࡫ࡸࡡ࡮ࡧࡺࡳࡷࡱ࡟࡯ࡣࡰࡩࡂࢁࡦ࠯ࡨࡵࡥࡲ࡫ࡷࡰࡴ࡮ࡣࡳࡧ࡭ࡦࡿࠣࡱࡪࡺࡨࡰࡦࡢࡲࡦࡳࡥ࠾ࠤᇩ") + str(method_name) + bstack1ll_opy_ (u"ࠣࠤᇪ"))
                return
            bstack1ll11l1ll1l_opy_ = f.bstack1llll1l111l_opy_(instance, bstack1ll1l1ll1l1_opy_.bstack1l1lll1llll_opy_, False)
            if command_name == bstack1ll_opy_ (u"ࠤࡪࡩࡹࠨᇫ") and not bstack1ll11l1ll1l_opy_:
                f.bstack1llll1lll11_opy_(instance, bstack1ll1l1ll1l1_opy_.bstack1l1lll1llll_opy_, True)
                bstack1ll11l1ll1l_opy_ = True
            if not bstack1ll11l1ll1l_opy_ and not self.bstack1ll111ll1ll_opy_:
                self.logger.debug(bstack1ll_opy_ (u"ࠥࡲࡴࠦࡕࡓࡎࠣࡰࡴࡧࡤࡦࡦࠣࡪࡷࡧ࡭ࡦࡹࡲࡶࡰࡥ࡮ࡢ࡯ࡨࡁࢀ࡬࠮ࡧࡴࡤࡱࡪࡽ࡯ࡳ࡭ࡢࡲࡦࡳࡥࡾࠢࡦࡳࡲࡳࡡ࡯ࡦࡢࡲࡦࡳࡥ࠾ࠤᇬ") + str(command_name) + bstack1ll_opy_ (u"ࠦࠧᇭ"))
                return
            scripts_to_run = self.commands.get(f.framework_name, {}).get(method_name, {}).get(command_name, [])
            if not scripts_to_run:
                self.logger.debug(bstack1ll_opy_ (u"ࠧࡴ࡯ࠡࡣ࠴࠵ࡾࠦࡳࡤࡴ࡬ࡴࡹࡹࠠࡧࡱࡵࠤ࡫ࡸࡡ࡮ࡧࡺࡳࡷࡱ࡟࡯ࡣࡰࡩࡂࢁࡦ࠯ࡨࡵࡥࡲ࡫ࡷࡰࡴ࡮ࡣࡳࡧ࡭ࡦࡿࠣࡧࡴࡳ࡭ࡢࡰࡧࡣࡳࡧ࡭ࡦ࠿ࠥᇮ") + str(command_name) + bstack1ll_opy_ (u"ࠨࠢᇯ"))
                return
            self.logger.info(bstack1ll_opy_ (u"ࠢࡳࡷࡱࡲ࡮ࡴࡧࠡࡽ࡯ࡩࡳ࠮ࡳࡤࡴ࡬ࡴࡹࡹ࡟ࡵࡱࡢࡶࡺࡴࠩࡾࠢࡶࡧࡷ࡯ࡰࡵࡵࠣࡪࡷࡧ࡭ࡦࡹࡲࡶࡰࡥ࡮ࡢ࡯ࡨࡁࢀ࡬࠮ࡧࡴࡤࡱࡪࡽ࡯ࡳ࡭ࡢࡲࡦࡳࡥࡾࠢࡦࡳࡲࡳࡡ࡯ࡦࡢࡲࡦࡳࡥ࠾ࠤᇰ") + str(command_name) + bstack1ll_opy_ (u"ࠣࠤᇱ"))
            scripts = [(s, bstack1l1lllllll1_opy_[s]) for s in scripts_to_run if s in bstack1l1lllllll1_opy_]
            for script_name, bstack1l1llll1ll1_opy_ in scripts:
                try:
                    bstack11l1l1l1ll_opy_ = datetime.now()
                    if script_name == bstack1ll_opy_ (u"ࠤࡶࡧࡦࡴࠢᇲ"):
                        result = self.perform_scan(driver, method=command_name, framework_name=f.framework_name)
                    instance.bstack11ll11ll1_opy_(bstack1ll_opy_ (u"ࠥࡥ࠶࠷ࡹ࠻ࠤᇳ") + script_name, datetime.now() - bstack11l1l1l1ll_opy_)
                    if isinstance(result, dict) and not result.get(bstack1ll_opy_ (u"ࠦࡸࡻࡣࡤࡧࡶࡷࠧᇴ"), True):
                        self.logger.warning(bstack1ll_opy_ (u"ࠧࡹ࡫ࡪࡲࠣࡩࡽ࡫ࡣࡶࡶ࡬ࡲ࡬ࠦࡲࡦ࡯ࡤ࡭ࡳ࡯࡮ࡨࠢࡶࡧࡷ࡯ࡰࡵࡵ࠽ࠤࠧᇵ") + str(result) + bstack1ll_opy_ (u"ࠨࠢᇶ"))
                        break
                except Exception as e:
                    self.logger.error(bstack1ll_opy_ (u"ࠢࡦࡴࡵࡳࡷࠦࡥࡹࡧࡦࡹࡹ࡯࡮ࡨࠢࡶࡧࡷ࡯ࡰࡵ࠿ࡾࡷࡨࡸࡩࡱࡶࡢࡲࡦࡳࡥࡾࠢࡨࡶࡷࡵࡲ࠾ࠤᇷ") + str(e) + bstack1ll_opy_ (u"ࠣࠤᇸ"))
        except Exception as e:
            self.logger.error(bstack1ll_opy_ (u"ࠤࡲࡲࡤࡨࡥࡧࡱࡵࡩࡤ࡫ࡸࡦࡥࡸࡸࡪࠦࡥࡳࡴࡲࡶࡂࠨᇹ") + str(e) + bstack1ll_opy_ (u"ࠥࠦᇺ"))
    def bstack1ll11111l11_opy_(
        self,
        f: TestFramework,
        instance: bstack1ll1l1ll111_opy_,
        bstack1lllll11l1l_opy_: Tuple[bstack1ll1ll1lll1_opy_, bstack1ll1l1ll11l_opy_],
        *args,
        **kwargs,
    ):
        tags = self._1ll11111lll_opy_(instance, args)
        capabilities = self.bstack1ll11l1l1l1_opy_.bstack1ll11l11111_opy_(f, instance, bstack1lllll11l1l_opy_, *args, **kwargs)
        self.accessibility = self.bstack1l1llllllll_opy_(tags, capabilities)
        if not self.accessibility:
            self.logger.debug(bstack1ll_opy_ (u"ࠦࡴࡴ࡟ࡢࡨࡷࡩࡷࡥࡴࡦࡵࡷ࠾ࠥࡧ࠱࠲ࡻࠣࡲࡴࡺࠠࡦࡰࡤࡦࡱ࡫ࡤࠣᇻ"))
            return
        driver = self.bstack1ll11l1l1l1_opy_.bstack1ll11l1111l_opy_(f, instance, bstack1lllll11l1l_opy_, *args, **kwargs)
        test_name = f.bstack1llll1l111l_opy_(instance, TestFramework.bstack1ll111ll111_opy_)
        if not test_name:
            self.logger.debug(bstack1ll_opy_ (u"ࠧࡵ࡮ࡠࡣࡩࡸࡪࡸ࡟ࡵࡧࡶࡸ࠿ࠦ࡭ࡪࡵࡶ࡭ࡳ࡭ࠠࡵࡧࡶࡸࠥࡴࡡ࡮ࡧࠥᇼ"))
            return
        test_uuid = f.bstack1llll1l111l_opy_(instance, TestFramework.bstack1ll111lll1l_opy_)
        if not test_uuid:
            self.logger.debug(bstack1ll_opy_ (u"ࠨ࡯࡯ࡡࡤࡪࡹ࡫ࡲࡠࡶࡨࡷࡹࡀࠠ࡮࡫ࡶࡷ࡮ࡴࡧࠡࡶࡨࡷࡹࠦࡵࡶ࡫ࡧࠦᇽ"))
            return
        if isinstance(self.bstack1ll11l1l1l1_opy_, bstack1ll1ll1l11l_opy_):
            framework_name = bstack1ll_opy_ (u"ࠧࡱ࡮ࡤࡽࡼࡸࡩࡨࡪࡷࠫᇾ")
        else:
            framework_name = bstack1ll_opy_ (u"ࠨࡵࡨࡰࡪࡴࡩࡶ࡯ࠪᇿ")
        self.bstack111111l11_opy_(driver, test_name, framework_name, test_uuid)
    def perform_scan(self, driver: object, method: Union[None, str], framework_name: str):
        bstack1ll11l11l1l_opy_ = bstack1lll1ll1l1l_opy_.bstack1ll1111ll11_opy_(EVENTS.bstack1l1l1ll1l_opy_.value)
        if not self.accessibility:
            self.logger.debug(bstack1ll_opy_ (u"ࠤࡳࡩࡷ࡬࡯ࡳ࡯ࡢࡷࡨࡧ࡮࠻ࠢࡤ࠵࠶ࡿࠠ࡯ࡱࡷࠤࡪࡴࡡࡣ࡮ࡨࡨࠥ࡬ࡲࡢ࡯ࡨࡻࡴࡸ࡫ࡠࡰࡤࡱࡪࡃࡻࡧࡴࡤࡱࡪࡽ࡯ࡳ࡭ࡢࡲࡦࡳࡥࡾࠢࠥሀ"))
            return
        bstack11l1l1l1ll_opy_ = datetime.now()
        bstack1l1llll1ll1_opy_ = self.scripts.get(framework_name, {}).get(bstack1ll_opy_ (u"ࠥࡷࡨࡧ࡮ࠣሁ"), None)
        if not bstack1l1llll1ll1_opy_:
            self.logger.debug(bstack1ll_opy_ (u"ࠦࡵ࡫ࡲࡧࡱࡵࡱࡤࡹࡣࡢࡰ࠽ࠤࡲ࡯ࡳࡴ࡫ࡱ࡫ࠥ࠭ࡳࡤࡣࡱࠫࠥࡹࡣࡳ࡫ࡳࡸࠥ࡬࡯ࡳࠢࡩࡶࡦࡳࡥࡸࡱࡵ࡯ࡤࡴࡡ࡮ࡧࡀࠦሂ") + str(framework_name) + bstack1ll_opy_ (u"ࠧࠦࠢሃ"))
            return
        if self.bstack1ll111ll1ll_opy_:
            arg = dict()
            arg[bstack1ll_opy_ (u"ࠨ࡭ࡦࡶ࡫ࡳࡩࠨሄ")] = method if method else bstack1ll_opy_ (u"ࠢࠣህ")
            arg[bstack1ll_opy_ (u"ࠣࡶ࡫ࡘࡪࡹࡴࡓࡷࡱ࡙ࡺ࡯ࡤࠣሆ")] = self.bstack1ll111l11ll_opy_[bstack1ll_opy_ (u"ࠤࡷࡩࡸࡺ࡟ࡳࡷࡱࡣࡺࡻࡩࡥࠤሇ")]
            arg[bstack1ll_opy_ (u"ࠥࡸ࡭ࡈࡵࡪ࡮ࡧ࡙ࡺ࡯ࡤࠣለ")] = self.bstack1ll111l11ll_opy_[bstack1ll_opy_ (u"ࠦࡹ࡫ࡳࡵࡪࡸࡦࡤࡨࡵࡪ࡮ࡧࡣࡺࡻࡩࡥࠤሉ")]
            arg[bstack1ll_opy_ (u"ࠧࡧࡵࡵࡪࡋࡩࡦࡪࡥࡳࠤሊ")] = self.bstack1ll111l11ll_opy_[bstack1ll_opy_ (u"ࠨࡡࡤࡥࡨࡷࡸ࡯ࡢࡪ࡮࡬ࡸࡾ࡚࡯࡬ࡧࡱࠦላ")]
            arg[bstack1ll_opy_ (u"ࠢࡵࡪࡍࡻࡹ࡚࡯࡬ࡧࡱࠦሌ")] = self.bstack1ll111l11ll_opy_[bstack1ll_opy_ (u"ࠣࡶ࡫ࡣ࡯ࡽࡴࡠࡶࡲ࡯ࡪࡴࠢል")]
            arg[bstack1ll_opy_ (u"ࠤࡶࡧࡦࡴࡔࡪ࡯ࡨࡷࡹࡧ࡭ࡱࠤሎ")] = str(int(datetime.now().timestamp() * 1000))
            bstack1ll111l11l1_opy_ = self.bstack1ll111lllll_opy_(bstack1ll_opy_ (u"ࠥࡷࡨࡧ࡮ࠣሏ"), self.bstack1ll111l11ll_opy_[bstack1ll_opy_ (u"ࠦࡹ࡫ࡳࡵࡡࡵࡹࡳࡥࡵࡶ࡫ࡧࠦሐ")])
            if bstack1ll_opy_ (u"ࠧࡩࡥ࡯ࡶࡵࡥࡱࡇࡵࡵࡪࡗࡳࡰ࡫࡮ࠣሑ") in bstack1ll111l11l1_opy_:
                bstack1ll111l11l1_opy_ = bstack1ll111l11l1_opy_.copy()
                bstack1ll111l11l1_opy_[bstack1ll_opy_ (u"ࠨࡣࡦࡰࡷࡶࡦࡲࡁࡶࡶ࡫ࡌࡪࡧࡤࡦࡴࠥሒ")] = bstack1ll111l11l1_opy_.pop(bstack1ll_opy_ (u"ࠢࡤࡧࡱࡸࡷࡧ࡬ࡂࡷࡷ࡬࡙ࡵ࡫ࡦࡰࠥሓ"))
            arg = bstack1l1llllll1l_opy_(arg, bstack1ll111l11l1_opy_)
            bstack1l1llllll11_opy_ = bstack1l1llll1ll1_opy_ % json.dumps(arg)
            driver.execute_script(bstack1l1llllll11_opy_)
            return
        instance = bstack1llll1ll1ll_opy_.bstack1llll11111l_opy_(driver)
        if instance:
            if not bstack1llll1ll1ll_opy_.bstack1llll1l111l_opy_(instance, bstack1ll1l1ll1l1_opy_.bstack1ll11l111l1_opy_, False):
                bstack1llll1ll1ll_opy_.bstack1llll1lll11_opy_(instance, bstack1ll1l1ll1l1_opy_.bstack1ll11l111l1_opy_, True)
            else:
                self.logger.info(bstack1ll_opy_ (u"ࠣࡲࡨࡶ࡫ࡵࡲ࡮ࡡࡶࡧࡦࡴ࠺ࠡࡣ࡯ࡶࡪࡧࡤࡺࠢ࡬ࡲࠥࡶࡲࡰࡩࡵࡩࡸࡹࠠࡧࡴࡤࡱࡪࡽ࡯ࡳ࡭ࡢࡲࡦࡳࡥ࠾ࡽࡩࡶࡦࡳࡥࡸࡱࡵ࡯ࡤࡴࡡ࡮ࡧࢀࠤࡲ࡫ࡴࡩࡱࡧࡁࠧሔ") + str(method) + bstack1ll_opy_ (u"ࠤࠥሕ"))
                return
        self.logger.info(bstack1ll_opy_ (u"ࠥࡴࡪࡸࡦࡰࡴࡰࡣࡸࡩࡡ࡯࠼ࠣࡪࡷࡧ࡭ࡦࡹࡲࡶࡰࡥ࡮ࡢ࡯ࡨࡁࢀ࡬ࡲࡢ࡯ࡨࡻࡴࡸ࡫ࡠࡰࡤࡱࡪࢃࠠ࡮ࡧࡷ࡬ࡴࡪ࠽ࠣሖ") + str(method) + bstack1ll_opy_ (u"ࠦࠧሗ"))
        if framework_name == bstack1ll_opy_ (u"ࠬࡶ࡬ࡢࡻࡺࡶ࡮࡭ࡨࡵࠩመ"):
            result = self.bstack1ll11l1l1l1_opy_.bstack1ll111111l1_opy_(driver, bstack1l1llll1ll1_opy_)
        else:
            result = driver.execute_async_script(bstack1l1llll1ll1_opy_, {bstack1ll_opy_ (u"ࠨ࡭ࡦࡶ࡫ࡳࡩࠨሙ"): method if method else bstack1ll_opy_ (u"ࠢࠣሚ")})
        bstack1lll1ll1l1l_opy_.end(EVENTS.bstack1l1l1ll1l_opy_.value, bstack1ll11l11l1l_opy_+bstack1ll_opy_ (u"ࠣ࠼ࡶࡸࡦࡸࡴࠣማ"), bstack1ll11l11l1l_opy_+bstack1ll_opy_ (u"ࠤ࠽ࡩࡳࡪࠢሜ"), True, None, command=method)
        if instance:
            bstack1llll1ll1ll_opy_.bstack1llll1lll11_opy_(instance, bstack1ll1l1ll1l1_opy_.bstack1ll11l111l1_opy_, False)
            instance.bstack11ll11ll1_opy_(bstack1ll_opy_ (u"ࠥࡥ࠶࠷ࡹ࠻ࡲࡨࡶ࡫ࡵࡲ࡮ࡡࡶࡧࡦࡴࠢም"), datetime.now() - bstack11l1l1l1ll_opy_)
        return result
        def bstack1ll1111l1ll_opy_(self, driver: object, framework_name, result_type: str):
            self.bstack1ll111lll11_opy_()
            req = structs.AccessibilityResultRequest()
            req.bin_session_id = self.bin_session_id
            req.bstack1ll111l1111_opy_ = self.bstack1ll111l11ll_opy_[bstack1ll_opy_ (u"ࠦࡹ࡫ࡳࡵࡡࡵࡹࡳࡥࡵࡶ࡫ࡧࠦሞ")]
            req.result_type = result_type
            req.session_id = self.bin_session_id
            try:
                r = self.bstack1ll1l11lll1_opy_.AccessibilityResult(req)
                if not r.success:
                    self.logger.debug(bstack1ll_opy_ (u"ࠧࡸࡥࡤࡧ࡬ࡺࡪࡪࠠࡧࡴࡲࡱࠥࡹࡥࡳࡸࡨࡶ࠿ࠦࠢሟ") + str(r) + bstack1ll_opy_ (u"ࠨࠢሠ"))
                else:
                    bstack1l1lll1ll11_opy_ = json.loads(r.bstack1ll1111llll_opy_.decode(bstack1ll_opy_ (u"ࠧࡶࡶࡩ࠱࠽࠭ሡ")))
                    if result_type == bstack1ll_opy_ (u"ࠨࡩࡨࡸࡗ࡫ࡳࡶ࡮ࡷࡷࠬሢ"):
                        return bstack1l1lll1ll11_opy_.get(bstack1ll_opy_ (u"ࠤࡧࡥࡹࡧࠢሣ"), [])
                    else:
                        return bstack1l1lll1ll11_opy_.get(bstack1ll_opy_ (u"ࠥࡨࡦࡺࡡࠣሤ"), {})
            except grpc.RpcError as e:
                self.logger.error(bstack1ll_opy_ (u"ࠦࡷࡶࡣ࠮ࡧࡵࡶࡴࡸࠠࡸࡪ࡬ࡰࡪࠦࡦࡦࡶࡦ࡬࡮ࡴࡧࠡࡩࡨࡸࡤࡧࡰࡱࡡࡤࡧࡨ࡫ࡳࡴ࡫ࡥ࡭ࡱ࡯ࡴࡺࡡࡵࡩࡸࡻ࡬ࡵࠢࡩࡶࡴࡳࠠࡤ࡮࡬࠾ࠥࠨሥ") + str(e) + bstack1ll_opy_ (u"ࠧࠨሦ"))
    @measure(event_name=EVENTS.bstack1llll11ll_opy_, stage=STAGE.bstack1l1lll1ll1_opy_)
    def get_accessibility_results(self, driver: object, framework_name):
        if not self.accessibility:
            self.logger.debug(bstack1ll_opy_ (u"ࠨࡧࡦࡶࡢࡥࡨࡩࡥࡴࡵ࡬ࡦ࡮ࡲࡩࡵࡻࡢࡶࡪࡹࡵ࡭ࡶࡶ࠾ࠥࡧ࠱࠲ࡻࠣࡲࡴࡺࠠࡦࡰࡤࡦࡱ࡫ࡤࠣሧ"))
            return
        if self.bstack1ll111ll1ll_opy_:
            self.logger.debug(bstack1ll_opy_ (u"ࠧࡑࡧࡵࡪࡴࡸ࡭ࡪࡰࡪࠤࡸࡩࡡ࡯ࠢࡩࡳࡷࠦࡡࡱࡲࠣࡥࡨࡩࡥࡴࡵ࡬ࡦ࡮ࡲࡩࡵࡻࠪረ"))
            self.perform_scan(driver, method=None, framework_name=framework_name)
            return self.bstack1ll1111l1ll_opy_(driver, framework_name, bstack1ll_opy_ (u"ࠣࡩࡨࡸࡗ࡫ࡳࡶ࡮ࡷࡷࠧሩ"))
        bstack1l1llll1ll1_opy_ = self.scripts.get(framework_name, {}).get(bstack1ll_opy_ (u"ࠤࡪࡩࡹࡘࡥࡴࡷ࡯ࡸࡸࠨሪ"), None)
        if not bstack1l1llll1ll1_opy_:
            self.logger.debug(bstack1ll_opy_ (u"ࠥࡱ࡮ࡹࡳࡪࡰࡪࠤࠬ࡭ࡥࡵࡔࡨࡷࡺࡲࡴࡴࠩࠣࡷࡨࡸࡩࡱࡶࠣࡪࡴࡸࠠࡧࡴࡤࡱࡪࡽ࡯ࡳ࡭ࡢࡲࡦࡳࡥ࠾ࠤራ") + str(framework_name) + bstack1ll_opy_ (u"ࠦࠧሬ"))
            return
        self.perform_scan(driver, method=None, framework_name=framework_name)
        bstack11l1l1l1ll_opy_ = datetime.now()
        if framework_name == bstack1ll_opy_ (u"ࠬࡶ࡬ࡢࡻࡺࡶ࡮࡭ࡨࡵࠩር"):
            result = self.bstack1ll11l1l1l1_opy_.bstack1ll111111l1_opy_(driver, bstack1l1llll1ll1_opy_)
        else:
            result = driver.execute_async_script(bstack1l1llll1ll1_opy_)
        instance = bstack1llll1ll1ll_opy_.bstack1llll11111l_opy_(driver)
        if instance:
            instance.bstack11ll11ll1_opy_(bstack1ll_opy_ (u"ࠨࡡ࠲࠳ࡼ࠾࡬࡫ࡴࡠࡣࡦࡧࡪࡹࡳࡪࡤ࡬ࡰ࡮ࡺࡹࡠࡴࡨࡷࡺࡲࡴࡴࠤሮ"), datetime.now() - bstack11l1l1l1ll_opy_)
        return result
    @measure(event_name=EVENTS.bstack1l111l111l_opy_, stage=STAGE.bstack1l1lll1ll1_opy_)
    def get_accessibility_results_summary(self, driver: object, framework_name):
        if not self.accessibility:
            self.logger.debug(bstack1ll_opy_ (u"ࠢࡨࡧࡷࡣࡦࡩࡣࡦࡵࡶ࡭ࡧ࡯࡬ࡪࡶࡼࡣࡷ࡫ࡳࡶ࡮ࡷࡷࡤࡹࡵ࡮࡯ࡤࡶࡾࡀࠠࡢ࠳࠴ࡽࠥࡴ࡯ࡵࠢࡨࡲࡦࡨ࡬ࡦࡦࠥሯ"))
            return
        if self.bstack1ll111ll1ll_opy_:
            self.perform_scan(driver, method=None, framework_name=framework_name)
            return self.bstack1ll1111l1ll_opy_(driver, framework_name, bstack1ll_opy_ (u"ࠨࡩࡨࡸࡗ࡫ࡳࡶ࡮ࡷࡷࡘࡻ࡭࡮ࡣࡵࡽࠬሰ"))
        bstack1l1llll1ll1_opy_ = self.scripts.get(framework_name, {}).get(bstack1ll_opy_ (u"ࠤࡪࡩࡹࡘࡥࡴࡷ࡯ࡸࡸ࡙ࡵ࡮࡯ࡤࡶࡾࠨሱ"), None)
        if not bstack1l1llll1ll1_opy_:
            self.logger.debug(bstack1ll_opy_ (u"ࠥࡱ࡮ࡹࡳࡪࡰࡪࠤࠬ࡭ࡥࡵࡔࡨࡷࡺࡲࡴࡴࡕࡸࡱࡲࡧࡲࡺࠩࠣࡷࡨࡸࡩࡱࡶࠣࡪࡴࡸࠠࡧࡴࡤࡱࡪࡽ࡯ࡳ࡭ࡢࡲࡦࡳࡥ࠾ࠤሲ") + str(framework_name) + bstack1ll_opy_ (u"ࠦࠧሳ"))
            return
        self.perform_scan(driver, method=None, framework_name=framework_name)
        bstack11l1l1l1ll_opy_ = datetime.now()
        if framework_name == bstack1ll_opy_ (u"ࠬࡶ࡬ࡢࡻࡺࡶ࡮࡭ࡨࡵࠩሴ"):
            result = self.bstack1ll11l1l1l1_opy_.bstack1ll111111l1_opy_(driver, bstack1l1llll1ll1_opy_)
        else:
            result = driver.execute_async_script(bstack1l1llll1ll1_opy_)
        instance = bstack1llll1ll1ll_opy_.bstack1llll11111l_opy_(driver)
        if instance:
            instance.bstack11ll11ll1_opy_(bstack1ll_opy_ (u"ࠨࡡ࠲࠳ࡼ࠾࡬࡫ࡴࡠࡣࡦࡧࡪࡹࡳࡪࡤ࡬ࡰ࡮ࡺࡹࡠࡴࡨࡷࡺࡲࡴࡴࡡࡶࡹࡲࡳࡡࡳࡻࠥስ"), datetime.now() - bstack11l1l1l1ll_opy_)
        return result
    @measure(event_name=EVENTS.bstack1ll1111l1l1_opy_, stage=STAGE.bstack1l1lll1ll1_opy_)
    def bstack1l1llll11ll_opy_(
        self,
        platform_index: int,
        framework_name: str,
        framework_version: str,
        hub_url: str,
    ):
        self.bstack1ll111lll11_opy_()
        req = structs.AccessibilityConfigRequest()
        req.bin_session_id = self.bin_session_id
        req.platform_index = platform_index
        req.framework_name = framework_name
        req.framework_version = framework_version
        req.hub_url = hub_url
        try:
            r = self.bstack1ll1l11lll1_opy_.AccessibilityConfig(req)
            if not r.success:
                self.logger.debug(bstack1ll_opy_ (u"ࠢࡳࡧࡦࡩ࡮ࡼࡥࡥࠢࡩࡶࡴࡳࠠࡴࡧࡵࡺࡪࡸ࠺ࠡࠤሶ") + str(r) + bstack1ll_opy_ (u"ࠣࠤሷ"))
            else:
                self.bstack1l1llll1111_opy_(framework_name, r)
            return r
        except grpc.RpcError as e:
            self.logger.error(bstack1ll_opy_ (u"ࠤࡵࡴࡨ࠳ࡥࡳࡴࡲࡶ࠿ࠦࠢሸ") + str(e) + bstack1ll_opy_ (u"ࠥࠦሹ"))
            traceback.print_exc()
            raise e
    def bstack1l1llll1111_opy_(self, framework_name: str, result: structs.AccessibilityConfigResponse) -> bool:
        if not result.success or not result.accessibility.success:
            self.logger.debug(bstack1ll_opy_ (u"ࠦࡱࡵࡡࡥࡡࡦࡳࡳ࡬ࡩࡨ࠼ࠣࡥ࠶࠷ࡹࠡࡰࡲࡸࠥ࡬࡯ࡶࡰࡧࠦሺ"))
            return False
        if result.accessibility.is_app_accessibility:
            self.bstack1ll111ll1ll_opy_ = result.accessibility.is_app_accessibility
        if result.testhub.build_hashed_id:
            self.bstack1ll111l11ll_opy_[bstack1ll_opy_ (u"ࠧࡺࡥࡴࡶ࡫ࡹࡧࡥࡢࡶ࡫࡯ࡨࡤࡻࡵࡪࡦࠥሻ")] = result.testhub.build_hashed_id
        if result.testhub.jwt:
            self.bstack1ll111l11ll_opy_[bstack1ll_opy_ (u"ࠨࡴࡩࡡ࡭ࡻࡹࡥࡴࡰ࡭ࡨࡲࠧሼ")] = result.testhub.jwt
        if result.accessibility.options:
            options = result.accessibility.options
            if options.capabilities:
                for caps in options.capabilities:
                    self.bstack1ll111l11ll_opy_[caps.name] = caps.value
            if options.scripts:
                self.scripts[framework_name] = {row.name: row.command for row in options.scripts}
            if options.commands_to_wrap and options.commands_to_wrap.commands:
                scripts_to_run = [s for s in options.commands_to_wrap.scripts_to_run]
                if not scripts_to_run:
                    return False
                bstack1ll11l11lll_opy_ = dict()
                for command in options.commands_to_wrap.commands:
                    if command.library == self.bstack1ll111l111l_opy_ and command.module == self.bstack1ll111l1ll1_opy_:
                        if command.method and not command.method in bstack1ll11l11lll_opy_:
                            bstack1ll11l11lll_opy_[command.method] = dict()
                        if command.name and not command.name in bstack1ll11l11lll_opy_[command.method]:
                            bstack1ll11l11lll_opy_[command.method][command.name] = list()
                        bstack1ll11l11lll_opy_[command.method][command.name].extend(scripts_to_run)
                self.commands[framework_name] = bstack1ll11l11lll_opy_
        return bool(self.commands.get(framework_name, None))
    def bstack1ll11l111ll_opy_(
        self,
        f: bstack1ll1llll1l1_opy_,
        exec: Tuple[bstack1llll111ll1_opy_, str],
        *args,
        **kwargs,
    ):
        instance, method_name = exec
        if isinstance(self.bstack1ll11l1l1l1_opy_, bstack1ll1ll1l11l_opy_) and method_name != bstack1ll_opy_ (u"ࠧࡤࡱࡱࡲࡪࡩࡴࠨሽ"):
            return
        if bstack1llll1ll1ll_opy_.bstack1llll11ll11_opy_(instance, bstack1ll1l1ll1l1_opy_.bstack1ll11l1ll11_opy_):
            return
        if f.bstack1l1llll11l1_opy_(method_name, *args):
            bstack1ll111111ll_opy_ = False
            desired_capabilities = f.bstack1ll111ll1l1_opy_(instance)
            if isinstance(desired_capabilities, dict):
                hub_url = f.bstack1l1lllll1l1_opy_(instance)
                platform_index = f.bstack1llll1l111l_opy_(instance, bstack1ll1llll1l1_opy_.bstack1l1lll1l1ll_opy_, 0)
                bstack1l1lllll1ll_opy_ = datetime.now()
                r = self.bstack1l1llll11ll_opy_(platform_index, f.framework_name, f.framework_version, hub_url)
                instance.bstack11ll11ll1_opy_(bstack1ll_opy_ (u"ࠣࡩࡵࡴࡨࡀࡡࡤࡥࡨࡷࡸ࡯ࡢࡪ࡮࡬ࡸࡾࡥࡣࡰࡰࡩ࡭࡬ࠨሾ"), datetime.now() - bstack1l1lllll1ll_opy_)
                bstack1ll111111ll_opy_ = r.success
            else:
                self.logger.error(bstack1ll_opy_ (u"ࠤࡰ࡭ࡸࡹࡩ࡯ࡩࠣࡨࡪࡹࡩࡳࡧࡧࠤࡨࡧࡰࡢࡤ࡬ࡰ࡮ࡺࡩࡦࡵࡀࠦሿ") + str(desired_capabilities) + bstack1ll_opy_ (u"ࠥࠦቀ"))
            f.bstack1llll1lll11_opy_(instance, bstack1ll1l1ll1l1_opy_.bstack1ll11l1ll11_opy_, bstack1ll111111ll_opy_)
    def bstack1ll11ll1_opy_(self, test_tags):
        bstack1l1llll11ll_opy_ = self.config.get(bstack1ll_opy_ (u"ࠫࡦࡩࡣࡦࡵࡶ࡭ࡧ࡯࡬ࡪࡶࡼࡓࡵࡺࡩࡰࡰࡶࠫቁ"))
        if not bstack1l1llll11ll_opy_:
            return True
        try:
            include_tags = bstack1l1llll11ll_opy_[bstack1ll_opy_ (u"ࠬ࡯࡮ࡤ࡮ࡸࡨࡪ࡚ࡡࡨࡵࡌࡲ࡙࡫ࡳࡵ࡫ࡱ࡫ࡘࡩ࡯ࡱࡧࠪቂ")] if bstack1ll_opy_ (u"࠭ࡩ࡯ࡥ࡯ࡹࡩ࡫ࡔࡢࡩࡶࡍࡳ࡚ࡥࡴࡶ࡬ࡲ࡬࡙ࡣࡰࡲࡨࠫቃ") in bstack1l1llll11ll_opy_ and isinstance(bstack1l1llll11ll_opy_[bstack1ll_opy_ (u"ࠧࡪࡰࡦࡰࡺࡪࡥࡕࡣࡪࡷࡎࡴࡔࡦࡵࡷ࡭ࡳ࡭ࡓࡤࡱࡳࡩࠬቄ")], list) else []
            exclude_tags = bstack1l1llll11ll_opy_[bstack1ll_opy_ (u"ࠨࡧࡻࡧࡱࡻࡤࡦࡖࡤ࡫ࡸࡏ࡮ࡕࡧࡶࡸ࡮ࡴࡧࡔࡥࡲࡴࡪ࠭ቅ")] if bstack1ll_opy_ (u"ࠩࡨࡼࡨࡲࡵࡥࡧࡗࡥ࡬ࡹࡉ࡯ࡖࡨࡷࡹ࡯࡮ࡨࡕࡦࡳࡵ࡫ࠧቆ") in bstack1l1llll11ll_opy_ and isinstance(bstack1l1llll11ll_opy_[bstack1ll_opy_ (u"ࠪࡩࡽࡩ࡬ࡶࡦࡨࡘࡦ࡭ࡳࡊࡰࡗࡩࡸࡺࡩ࡯ࡩࡖࡧࡴࡶࡥࠨቇ")], list) else []
            excluded = any(tag in exclude_tags for tag in test_tags)
            included = len(include_tags) == 0 or any(tag in include_tags for tag in test_tags)
            return not excluded and included
        except Exception as error:
            self.logger.debug(bstack1ll_opy_ (u"ࠦࡊࡸࡲࡰࡴࠣࡻ࡭࡯࡬ࡦࠢࡹࡥࡱ࡯ࡤࡢࡶ࡬ࡲ࡬ࠦࡴࡦࡵࡷࠤࡨࡧࡳࡦࠢࡩࡳࡷࠦࡡࡤࡥࡨࡷࡸ࡯ࡢࡪ࡮࡬ࡸࡾࠦࡢࡦࡨࡲࡶࡪࠦࡳࡤࡣࡱࡲ࡮ࡴࡧ࠯ࠢࡈࡶࡷࡵࡲࠡ࠼ࠣࠦቈ") + str(error))
        return False
    def bstack11111l1l1_opy_(self, caps):
        try:
            if self.bstack1ll111ll1ll_opy_:
                bstack1ll11l11l11_opy_ = caps.get(bstack1ll_opy_ (u"ࠧࡶ࡬ࡢࡶࡩࡳࡷࡳࡎࡢ࡯ࡨࠦ቉"))
                if bstack1ll11l11l11_opy_ is not None and str(bstack1ll11l11l11_opy_).lower() == bstack1ll_opy_ (u"ࠨࡡ࡯ࡦࡵࡳ࡮ࡪࠢቊ"):
                    bstack1l1llll1lll_opy_ = caps.get(bstack1ll_opy_ (u"ࠢࡢࡲࡳ࡭ࡺࡳ࠺ࡱ࡮ࡤࡸ࡫ࡵࡲ࡮ࡘࡨࡶࡸ࡯࡯࡯ࠤቋ")) or caps.get(bstack1ll_opy_ (u"ࠣࡲ࡯ࡥࡹ࡬࡯ࡳ࡯࡙ࡩࡷࡹࡩࡰࡰࠥቌ"))
                    if bstack1l1llll1lll_opy_ is not None and int(bstack1l1llll1lll_opy_) < 11:
                        self.logger.warning(bstack1ll_opy_ (u"ࠤࡄࡧࡨ࡫ࡳࡴ࡫ࡥ࡭ࡱ࡯ࡴࡺࠢࡄࡹࡹࡵ࡭ࡢࡶ࡬ࡳࡳࠦࡷࡪ࡮࡯ࠤࡷࡻ࡮ࠡࡱࡱࡰࡾࠦ࡯࡯ࠢࡄࡲࡩࡸ࡯ࡪࡦࠣ࠵࠶ࠦࡡ࡯ࡦࠣࡥࡧࡵࡶࡦ࠰ࠣࡇࡺࡸࡲࡦࡰࡷࠤࡵࡲࡡࡵࡨࡲࡶࡲࠦࡶࡦࡴࡶ࡭ࡴࡴࠠ࠾ࠤቍ") + str(bstack1l1llll1lll_opy_) + bstack1ll_opy_ (u"ࠥࠦ቎"))
                        return False
                return True
            bstack1l1llll1l11_opy_ = caps.get(bstack1ll_opy_ (u"ࠫࡧࡹࡴࡢࡥ࡮࠾ࡴࡶࡴࡪࡱࡱࡷࠬ቏"), {}).get(bstack1ll_opy_ (u"ࠬࡪࡥࡷ࡫ࡦࡩࡓࡧ࡭ࡦࠩቐ"), caps.get(bstack1ll_opy_ (u"࠭ࡤࡦࡸ࡬ࡧࡪ࠭ቑ"), bstack1ll_opy_ (u"ࠧࠨቒ")))
            if bstack1l1llll1l11_opy_:
                self.logger.warning(bstack1ll_opy_ (u"ࠣࡃࡦࡧࡪࡹࡳࡪࡤ࡬ࡰ࡮ࡺࡹࠡࡃࡸࡸࡴࡳࡡࡵ࡫ࡲࡲࠥࡽࡩ࡭࡮ࠣࡶࡺࡴࠠࡰࡰ࡯ࡽࠥࡵ࡮ࠡࡆࡨࡷࡰࡺ࡯ࡱࠢࡥࡶࡴࡽࡳࡦࡴࡶ࠲ࠧቓ"))
                return False
            browser = caps.get(bstack1ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡑࡥࡲ࡫ࠧቔ"), bstack1ll_opy_ (u"ࠪࠫቕ")).lower()
            if browser != bstack1ll_opy_ (u"ࠫࡨ࡮ࡲࡰ࡯ࡨࠫቖ"):
                self.logger.warning(bstack1ll_opy_ (u"ࠧࡇࡣࡤࡧࡶࡷ࡮ࡨࡩ࡭࡫ࡷࡽࠥࡇࡵࡵࡱࡰࡥࡹ࡯࡯࡯ࠢࡺ࡭ࡱࡲࠠࡳࡷࡱࠤࡴࡴ࡬ࡺࠢࡲࡲࠥࡉࡨࡳࡱࡰࡩࠥࡨࡲࡰࡹࡶࡩࡷࡹ࠮ࠣ቗"))
                return False
            bstack1l1lllll111_opy_ = bstack1ll1111ll1l_opy_
            if not self.config.get(bstack1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯ࡆࡻࡴࡰ࡯ࡤࡸ࡮ࡵ࡮ࠨቘ")) or self.config.get(bstack1ll_opy_ (u"ࠧࡵࡷࡵࡦࡴࡹࡣࡢ࡮ࡨࠫ቙")):
                bstack1l1lllll111_opy_ = bstack1ll1111l111_opy_
            browser_version = caps.get(bstack1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡘࡨࡶࡸ࡯࡯࡯ࠩቚ"))
            if not browser_version:
                browser_version = caps.get(bstack1ll_opy_ (u"ࠩࡥࡷࡹࡧࡣ࡬࠼ࡲࡴࡹ࡯࡯࡯ࡵࠪቛ"), {}).get(bstack1ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵ࡚ࡪࡸࡳࡪࡱࡱࠫቜ"), bstack1ll_opy_ (u"ࠫࠬቝ"))
            if browser_version and browser_version != bstack1ll_opy_ (u"ࠬࡲࡡࡵࡧࡶࡸࠬ቞") and int(browser_version.split(bstack1ll_opy_ (u"࠭࠮ࠨ቟"))[0]) <= bstack1l1lllll111_opy_:
                self.logger.warning(bstack1ll_opy_ (u"ࠢࡂࡥࡦࡩࡸࡹࡩࡣ࡫࡯࡭ࡹࡿࠠࡂࡷࡷࡳࡲࡧࡴࡪࡱࡱࠤࡼ࡯࡬࡭ࠢࡵࡹࡳࠦ࡯࡯࡮ࡼࠤࡴࡴࠠࡄࡪࡵࡳࡲ࡫ࠠࡣࡴࡲࡻࡸ࡫ࡲࠡࡸࡨࡶࡸ࡯࡯࡯ࠢࡪࡶࡪࡧࡴࡦࡴࠣࡸ࡭ࡧ࡮ࠡࠤበ") + str(bstack1l1lllll111_opy_) + bstack1ll_opy_ (u"ࠣ࠰ࠥቡ"))
                return False
            bstack1ll111l1lll_opy_ = caps.get(bstack1ll_opy_ (u"ࠩࡥࡷࡹࡧࡣ࡬࠼ࡲࡴࡹ࡯࡯࡯ࡵࠪቢ"), {}).get(bstack1ll_opy_ (u"ࠪࡧ࡭ࡸ࡯࡮ࡧࡒࡴࡹ࡯࡯࡯ࡵࠪባ"))
            if not bstack1ll111l1lll_opy_:
                bstack1ll111l1lll_opy_ = caps.get(bstack1ll_opy_ (u"ࠫ࡬ࡵ࡯ࡨ࠼ࡦ࡬ࡷࡵ࡭ࡦࡑࡳࡸ࡮ࡵ࡮ࡴࠩቤ"), {})
            if bstack1ll111l1lll_opy_ and bstack1ll_opy_ (u"ࠬ࠳࠭ࡩࡧࡤࡨࡱ࡫ࡳࡴࠩብ") in bstack1ll111l1lll_opy_.get(bstack1ll_opy_ (u"࠭ࡡࡳࡩࡶࠫቦ"), []):
                self.logger.warning(bstack1ll_opy_ (u"ࠢࡂࡥࡦࡩࡸࡹࡩࡣ࡫࡯࡭ࡹࡿࠠࡂࡷࡷࡳࡲࡧࡴࡪࡱࡱࠤࡼ࡯࡬࡭ࠢࡱࡳࡹࠦࡲࡶࡰࠣࡳࡳࠦ࡬ࡦࡩࡤࡧࡾࠦࡨࡦࡣࡧࡰࡪࡹࡳࠡ࡯ࡲࡨࡪ࠴ࠠࡔࡹ࡬ࡸࡨ࡮ࠠࡵࡱࠣࡲࡪࡽࠠࡩࡧࡤࡨࡱ࡫ࡳࡴࠢࡰࡳࡩ࡫ࠠࡰࡴࠣࡥࡻࡵࡩࡥࠢࡸࡷ࡮ࡴࡧࠡࡪࡨࡥࡩࡲࡥࡴࡵࠣࡱࡴࡪࡥ࠯ࠤቧ"))
                return False
            return True
        except Exception as error:
            self.logger.debug(bstack1ll_opy_ (u"ࠣࡇࡻࡧࡪࡶࡴࡪࡱࡱࠤ࡮ࡴࠠࡷࡣ࡯࡭ࡩࡧࡴࡦࠢࡤ࠵࠶ࡿࠠࡴࡷࡳࡴࡴࡸࡴࠡ࠼ࠥቨ") + str(error))
            return False
    def bstack1ll111l1l11_opy_(self, test_uuid: str, result: structs.FetchDriverExecuteParamsEventResponse):
        bstack1l1llll1l1l_opy_ = {
            bstack1ll_opy_ (u"ࠩࡷ࡬࡙࡫ࡳࡵࡔࡸࡲ࡚ࡻࡩࡥࠩቩ"): test_uuid,
        }
        bstack1ll11l1l1ll_opy_ = {}
        if result.success:
            bstack1ll11l1l1ll_opy_ = json.loads(result.accessibility_execute_params)
        return bstack1l1llllll1l_opy_(bstack1l1llll1l1l_opy_, bstack1ll11l1l1ll_opy_)
    def bstack1ll111lllll_opy_(self, script_name: str, test_uuid: str) -> dict:
        bstack1ll_opy_ (u"ࠥࠦࠧࠐࠠࠡࠢࠣࠤࠥࠦࠠࡇࡧࡷࡧ࡭ࠦࡣࡦࡰࡷࡶࡦࡲࠠࡢࡷࡷ࡬ࠥࡧࡣࡤࡧࡶࡷ࡮ࡨࡩ࡭࡫ࡷࡽࠥࡩ࡯࡯ࡨ࡬࡫ࡺࡸࡡࡵ࡫ࡲࡲࠥ࡬࡯ࡳࠢࡷ࡬ࡪࠦࡧࡪࡸࡨࡲࠥࡹࡣࡳ࡫ࡳࡸࠥࡴࡡ࡮ࡧ࠱ࠎࠥࠦࠠࠡࠢࠣࠤࠥࡘࡥࡵࡷࡵࡲࡸࠦࡣࡢࡥ࡫ࡩࡩࠦࡣࡰࡰࡩ࡭࡬ࠦࡩࡧࠢࡤࡰࡷ࡫ࡡࡥࡻࠣࡪࡪࡺࡣࡩࡧࡧ࠰ࠥࡵࡴࡩࡧࡵࡻ࡮ࡹࡥࠡ࡮ࡲࡥࡩࡹࠠࡢࡰࡧࠤࡨࡧࡣࡩࡧࡶࠤ࡮ࡺ࠮ࠋࠢࠣࠤࠥࠦࠠࠡࠢࡄࡶ࡬ࡹ࠺ࠋࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࡳࡤࡴ࡬ࡴࡹࡥ࡮ࡢ࡯ࡨ࠾ࠥࡔࡡ࡮ࡧࠣࡳ࡫ࠦࡴࡩࡧࠣࡷࡨࡸࡩࡱࡶࠣࡸࡴࠦࡦࡦࡶࡦ࡬ࠥࡩ࡯࡯ࡨ࡬࡫ࠥ࡬࡯ࡳࠌࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࡵࡧࡶࡸࡤࡻࡵࡪࡦ࠽ࠤ࡚࡛ࡉࡅࠢࡲࡪࠥࡺࡨࡦࠢࡷࡩࡸࡺࠠࡳࡷࡱࠤ࡫ࡵࡲࠡࡹ࡫࡭ࡨ࡮ࠠࡵࡱࠣࡪࡪࡺࡣࡩࠢࡦࡳࡳ࡬ࡩࡨࠌࠣࠤࠥࠦࠠࠡࠢࠣࡖࡪࡺࡵࡳࡰࡶ࠾ࠏࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࡨ࡮ࡩࡴ࠻ࠢࡆࡳࡳ࡬ࡩࡨࡷࡵࡥࡹ࡯࡯࡯ࠢࡧ࡭ࡨࡺࡩࡰࡰࡤࡶࡾ࠲ࠠࡦ࡯ࡳࡸࡾࠦࡤࡪࡥࡷࠤ࡮࡬ࠠࡦࡴࡵࡳࡷࠦ࡯ࡤࡥࡸࡶࡸࠐࠠࠡࠢࠣࠤࠥࠦࠠࠣࠤࠥቪ")
        try:
            if self.bstack1ll111ll11l_opy_:
                return self.bstack1ll11l11ll1_opy_
            self.bstack1ll111lll11_opy_()
            req = structs.FetchDriverExecuteParamsEventRequest()
            req.bin_session_id = self.bin_session_id
            req.product = bstack1ll_opy_ (u"ࠦࡦࡩࡣࡦࡵࡶ࡭ࡧ࡯࡬ࡪࡶࡼࠦቫ")
            req.script_name = script_name
            r = self.bstack1ll1l11lll1_opy_.FetchDriverExecuteParamsEvent(req)
            if r.success:
                self.bstack1ll11l11ll1_opy_ = self.bstack1ll111l1l11_opy_(test_uuid, r)
                self.bstack1ll111ll11l_opy_ = True
            else:
                self.logger.error(bstack1ll_opy_ (u"ࠧ࡬ࡥࡵࡥ࡫ࡇࡪࡴࡴࡳࡣ࡯ࡅࡺࡺࡨࡂ࠳࠴ࡽࡈࡵ࡮ࡧ࡫ࡪ࠾ࠥࡌࡡࡪ࡮ࡨࡨࠥࡺ࡯ࠡࡨࡨࡸࡨ࡮ࠠࡥࡴ࡬ࡺࡪࡸࠠࡦࡺࡨࡧࡺࡺࡥࠡࡲࡤࡶࡦࡳࡳࠡࡨࡲࡶࠥࢁࡳࡤࡴ࡬ࡴࡹࡥ࡮ࡢ࡯ࡨࢁ࠿ࠦࠢቬ") + str(r.error) + bstack1ll_opy_ (u"ࠨࠢቭ"))
                self.bstack1ll11l11ll1_opy_ = dict()
            return self.bstack1ll11l11ll1_opy_
        except Exception as e:
            self.logger.error(bstack1ll_opy_ (u"ࠢࡧࡧࡷࡧ࡭ࡉࡥ࡯ࡶࡵࡥࡱࡇࡵࡵࡪࡄ࠵࠶ࡿࡃࡰࡰࡩ࡭࡬ࡀࠠࡇࡣ࡬ࡰࡪࡪࠠࡵࡱࠣࡪࡪࡺࡣࡩࠢࡧࡶ࡮ࡼࡥࡳࠢࡨࡼࡪࡩࡵࡵࡧࠣࡴࡦࡸࡡ࡮ࡵࠣࡪࡴࡸࠠࡼࡵࡦࡶ࡮ࡶࡴࡠࡰࡤࡱࡪࢃ࠺ࠡࠤቮ") + str(traceback.format_exc()) + bstack1ll_opy_ (u"ࠣࠤቯ"))
            return dict()
    def bstack111111l11_opy_(self, driver: object, name: str, framework_name: str, test_uuid: str):
        bstack1ll11l11l1l_opy_ = None
        try:
            self.bstack1ll111lll11_opy_()
            req = structs.FetchDriverExecuteParamsEventRequest()
            req.bin_session_id = self.bin_session_id
            req.product = bstack1ll_opy_ (u"ࠤࡤࡧࡨ࡫ࡳࡴ࡫ࡥ࡭ࡱ࡯ࡴࡺࠤተ")
            req.script_name = bstack1ll_opy_ (u"ࠥࡷࡦࡼࡥࡓࡧࡶࡹࡱࡺࡳࠣቱ")
            r = self.bstack1ll1l11lll1_opy_.FetchDriverExecuteParamsEvent(req)
            if not r.success:
                self.logger.debug(bstack1ll_opy_ (u"ࠦࡷ࡫ࡣࡦ࡫ࡹࡩࡩࠦࡤࡳ࡫ࡹࡩࡷࠦࡥࡹࡧࡦࡹࡹ࡫ࠠࡱࡣࡵࡥࡲࡹࠠࡧࡴࡲࡱࠥࡹࡥࡳࡸࡨࡶ࠿ࠦࠢቲ") + str(r.error) + bstack1ll_opy_ (u"ࠧࠨታ"))
            else:
                bstack1l1llll1l1l_opy_ = self.bstack1ll111l1l11_opy_(test_uuid, r)
                bstack1l1llll1ll1_opy_ = r.script
            self.logger.debug(bstack1ll_opy_ (u"࠭ࡐࡦࡴࡩࡳࡷࡳࡩ࡯ࡩࠣࡷࡨࡧ࡮ࠡࡤࡨࡪࡴࡸࡥࠡࡵࡤࡺ࡮ࡴࡧࠡࡴࡨࡷࡺࡲࡴࡴࠩቴ") + str(bstack1l1llll1l1l_opy_))
            self.perform_scan(driver, name, framework_name=framework_name)
            if not bstack1l1llll1ll1_opy_:
                self.logger.debug(bstack1ll_opy_ (u"ࠢࡱࡧࡵࡪࡴࡸ࡭ࡠࡵࡦࡥࡳࡀࠠ࡮࡫ࡶࡷ࡮ࡴࡧࠡࠩࡶࡥࡻ࡫ࡒࡦࡵࡸࡰࡹࡹࠧࠡࡵࡦࡶ࡮ࡶࡴࠡࡨࡲࡶࠥ࡬ࡲࡢ࡯ࡨࡻࡴࡸ࡫ࡠࡰࡤࡱࡪࡃࠢት") + str(framework_name) + bstack1ll_opy_ (u"ࠣࠢࠥቶ"))
                return
            bstack1ll11l11l1l_opy_ = bstack1lll1ll1l1l_opy_.bstack1ll1111ll11_opy_(EVENTS.bstack1ll11l1l11l_opy_.value)
            self.bstack1ll11l1lll1_opy_(driver, bstack1l1llll1ll1_opy_, bstack1l1llll1l1l_opy_, framework_name)
            self.logger.info(bstack1ll_opy_ (u"ࠤࡄࡧࡨ࡫ࡳࡴ࡫ࡥ࡭ࡱ࡯ࡴࡺࠢࡷࡩࡸࡺࡩ࡯ࡩࠣࡪࡴࡸࠠࡵࡪ࡬ࡷࠥࡺࡥࡴࡶࠣࡧࡦࡹࡥࠡࡪࡤࡷࠥ࡫࡮ࡥࡧࡧ࠲ࠧቷ"))
            bstack1lll1ll1l1l_opy_.end(EVENTS.bstack1ll11l1l11l_opy_.value, bstack1ll11l11l1l_opy_+bstack1ll_opy_ (u"ࠥ࠾ࡸࡺࡡࡳࡶࠥቸ"), bstack1ll11l11l1l_opy_+bstack1ll_opy_ (u"ࠦ࠿࡫࡮ࡥࠤቹ"), True, None, command=bstack1ll_opy_ (u"ࠬࡹࡡࡷࡧࡕࡩࡸࡻ࡬ࡵࡵࠪቺ"),test_name=name)
        except Exception as bstack1l1lllll11l_opy_:
            self.logger.error(bstack1ll_opy_ (u"ࠨࡁࡤࡥࡨࡷࡸ࡯ࡢࡪ࡮࡬ࡸࡾࠦࡲࡦࡵࡸࡰࡹࡹࠠࡤࡱࡸࡰࡩࠦ࡮ࡰࡶࠣࡦࡪࠦࡰࡳࡱࡦࡩࡸࡹࡥࡥࠢࡩࡳࡷࠦࡴࡩࡧࠣࡸࡪࡹࡴࠡࡥࡤࡷࡪࡀࠠࠣቻ") + bstack1ll_opy_ (u"ࠢࡴࡶࡵࠬࡵࡧࡴࡩࠫࠥቼ") + bstack1ll_opy_ (u"ࠣࠢࡈࡶࡷࡵࡲࠡ࠼ࠥች") + str(bstack1l1lllll11l_opy_))
            bstack1lll1ll1l1l_opy_.end(EVENTS.bstack1ll11l1l11l_opy_.value, bstack1ll11l11l1l_opy_+bstack1ll_opy_ (u"ࠤ࠽ࡷࡹࡧࡲࡵࠤቾ"), bstack1ll11l11l1l_opy_+bstack1ll_opy_ (u"ࠥ࠾ࡪࡴࡤࠣቿ"), False, bstack1l1lllll11l_opy_, command=bstack1ll_opy_ (u"ࠫࡸࡧࡶࡦࡔࡨࡷࡺࡲࡴࡴࠩኀ"),test_name=name)
    def bstack1ll11l1lll1_opy_(self, driver, bstack1l1llll1ll1_opy_, bstack1l1llll1l1l_opy_, framework_name):
        if framework_name == bstack1ll_opy_ (u"ࠬࡶ࡬ࡢࡻࡺࡶ࡮࡭ࡨࡵࠩኁ"):
            self.bstack1ll11l1l1l1_opy_.bstack1ll111111l1_opy_(driver, bstack1l1llll1ll1_opy_, bstack1l1llll1l1l_opy_)
        else:
            self.logger.debug(driver.execute_async_script(bstack1l1llll1ll1_opy_, bstack1l1llll1l1l_opy_))
    def _1ll11111lll_opy_(self, instance: bstack1ll1l1ll111_opy_, args: Tuple) -> list:
        bstack1ll_opy_ (u"ࠨࠢࠣࡇࡻࡸࡷࡧࡣࡵࠢࡷࡥ࡬ࡹࠠࡣࡣࡶࡩࡩࠦ࡯࡯ࠢࡷ࡬ࡪࠦࡴࡦࡵࡷࠤ࡫ࡸࡡ࡮ࡧࡺࡳࡷࡱ࠮ࠣࠤࠥኂ")
        if bstack1ll_opy_ (u"ࠧࡱࡻࡷࡩࡸࡺ࠭ࡣࡦࡧࠫኃ") in instance.bstack1ll1111lll1_opy_:
            return args[2].tags if hasattr(args[2], bstack1ll_opy_ (u"ࠨࡶࡤ࡫ࡸ࠭ኄ")) else []
        if hasattr(args[0], bstack1ll_opy_ (u"ࠩࡲࡻࡳࡥ࡭ࡢࡴ࡮ࡩࡷࡹࠧኅ")):
            return [marker.name for marker in args[0].own_markers]
        return []
    def bstack1l1llllllll_opy_(self, tags, capabilities):
        return self.bstack1ll11ll1_opy_(tags) and self.bstack11111l1l1_opy_(capabilities)