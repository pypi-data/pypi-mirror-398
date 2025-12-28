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
from enum import Enum
from typing import Dict, Tuple, Callable, Type, List, Any
import abc
from datetime import datetime, timezone, timedelta
from browserstack_sdk.sdk_cli.bstack1llll11l111_opy_ import bstack1llll1l1lll_opy_, bstack1llll11l1ll_opy_
import os
import threading
class bstack1lllll111l1_opy_(Enum):
    PRE = 0
    POST = 1
    def __repr__(self) -> str:
        return bstack1ll_opy_ (u"ࠥࡌࡴࡵ࡫ࡔࡶࡤࡸࡪ࠴ࡻࡾࠤტ").format(self.name)
class bstack1llll11l1l1_opy_(Enum):
    NONE = 0
    bstack1llll1l1l1l_opy_ = 1
    bstack1llll1111ll_opy_ = 3
    bstack1llll1l1111_opy_ = 4
    bstack1llll1l1ll1_opy_ = 5
    QUIT = 6
    def __eq__(self, other):
        if self.__class__ is other.__class__:
            return self.value == other.value
        return NotImplemented
    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented
    def __repr__(self) -> str:
        return bstack1ll_opy_ (u"ࠦࡆࡻࡴࡰ࡯ࡤࡸ࡮ࡵ࡮ࡇࡴࡤࡱࡪࡽ࡯ࡳ࡭ࡖࡸࡦࡺࡥ࠯ࡽࢀࠦუ").format(self.name)
class bstack1llll111ll1_opy_(bstack1llll1l1lll_opy_):
    framework_name: str
    framework_version: str
    state: bstack1llll11l1l1_opy_
    previous_state: bstack1llll11l1l1_opy_
    bstack1llll111111_opy_: datetime
    bstack1llll1lllll_opy_: datetime
    def __init__(
        self,
        context: bstack1llll11l1ll_opy_,
        framework_name: str,
        framework_version: str,
        state=bstack1llll11l1l1_opy_.NONE,
    ):
        super().__init__(context)
        self.framework_name = framework_name
        self.framework_version = framework_version
        self.state = state
        self.previous_state = bstack1llll11l1l1_opy_.NONE
        self.bstack1llll111111_opy_ = datetime.now(tz=timezone.utc)
        self.bstack1llll1lllll_opy_ = datetime.now(tz=timezone.utc)
    def bstack1llll1lll11_opy_(self, bstack1lll1lll1ll_opy_: bstack1llll11l1l1_opy_):
        bstack1llll1l11l1_opy_ = bstack1llll11l1l1_opy_(bstack1lll1lll1ll_opy_).name
        if not bstack1llll1l11l1_opy_:
            return False
        if bstack1lll1lll1ll_opy_ == self.state:
            return False
        if self.state == bstack1llll11l1l1_opy_.bstack1llll1111ll_opy_: # bstack1llll11ll1l_opy_ bstack1lllll11lll_opy_ for bstack1llll111l11_opy_ in bstack1llll1l11ll_opy_, it bstack1llll1l1l11_opy_ bstack1llll1ll111_opy_ bstack1llll111lll_opy_ times bstack1lll1llll1l_opy_ a new state
            return True
        if (
            bstack1lll1lll1ll_opy_ == bstack1llll11l1l1_opy_.NONE
            or (self.state != bstack1llll11l1l1_opy_.NONE and bstack1lll1lll1ll_opy_ == bstack1llll11l1l1_opy_.bstack1llll1l1l1l_opy_)
            or (self.state < bstack1llll11l1l1_opy_.bstack1llll1l1l1l_opy_ and bstack1lll1lll1ll_opy_ == bstack1llll11l1l1_opy_.bstack1llll1l1111_opy_)
            or (self.state < bstack1llll11l1l1_opy_.bstack1llll1l1l1l_opy_ and bstack1lll1lll1ll_opy_ == bstack1llll11l1l1_opy_.QUIT)
        ):
            raise ValueError(bstack1ll_opy_ (u"ࠧ࡯࡮ࡷࡣ࡯࡭ࡩࠦࡳࡵࡣࡷࡩࠥࡺࡲࡢࡰࡶ࡭ࡹ࡯࡯࡯࠼ࠣࠦფ") + str(self.state) + bstack1ll_opy_ (u"ࠨࠠ࠾ࡀࠣࠦქ") + str(bstack1lll1lll1ll_opy_))
        self.previous_state = self.state
        self.state = bstack1lll1lll1ll_opy_
        self.bstack1llll1lllll_opy_ = datetime.now(tz=timezone.utc)
        return True
class bstack1llll1ll1ll_opy_(abc.ABC):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    bstack1lllll111ll_opy_: Dict[str, bstack1llll111ll1_opy_] = dict()
    framework_name: str
    framework_version: str
    classes: List[Type]
    def __init__(
        self,
        framework_name: str,
        framework_version: str,
        classes: List[Type],
    ):
        self.framework_name = framework_name
        self.framework_version = framework_version
        self.classes = classes
    @abc.abstractmethod
    def bstack1lllll1111l_opy_(self, instance: bstack1llll111ll1_opy_, method_name: str, bstack1llll1lll1l_opy_: timedelta, *args, **kwargs):
        return
    @abc.abstractmethod
    def bstack1llll1111l1_opy_(
        self, method_name, previous_state: bstack1llll11l1l1_opy_, *args, **kwargs
    ) -> bstack1llll11l1l1_opy_:
        return
    @abc.abstractmethod
    def bstack1llll1ll1l1_opy_(
        self,
        target: object,
        exec: Tuple[bstack1llll111ll1_opy_, str],
        bstack1lllll11l1l_opy_: Tuple[bstack1llll11l1l1_opy_, bstack1lllll111l1_opy_],
        result: Any,
        *args,
        **kwargs,
    ) -> Callable:
        return
    def bstack1llll111l1l_opy_(self, bstack1llll11llll_opy_: List[str]):
        for clazz in self.classes:
            for method_name in bstack1llll11llll_opy_:
                bstack1lllll11111_opy_ = getattr(clazz, method_name, None)
                if not callable(bstack1lllll11111_opy_):
                    self.logger.warning(bstack1ll_opy_ (u"ࠢࡶࡰࡳࡥࡹࡩࡨࡦࡦࠣࡱࡪࡺࡨࡰࡦ࠽ࠤࠧღ") + str(method_name) + bstack1ll_opy_ (u"ࠣࠤყ"))
                    continue
                bstack1lllll1l111_opy_ = self.bstack1llll1111l1_opy_(
                    method_name, previous_state=bstack1llll11l1l1_opy_.NONE
                )
                bstack1lll1llllll_opy_ = self.bstack1llll11lll1_opy_(
                    method_name,
                    (bstack1lllll1l111_opy_ if bstack1lllll1l111_opy_ else bstack1llll11l1l1_opy_.NONE),
                    bstack1lllll11111_opy_,
                )
                if not callable(bstack1lll1llllll_opy_):
                    self.logger.warning(bstack1ll_opy_ (u"ࠤࡰࡩࡹ࡮࡯ࡥࠢࡱࡳࡹࠦࡰࡢࡶࡦ࡬ࡪࡪ࠺ࠡࡽࡰࡩࡹ࡮࡯ࡥࡡࡱࡥࡲ࡫ࡽࠡࠪࡾࡷࡪࡲࡦ࠯ࡨࡵࡥࡲ࡫ࡷࡰࡴ࡮ࡣࡳࡧ࡭ࡦࡿ࠽ࠤࠧშ") + str(self.framework_version) + bstack1ll_opy_ (u"ࠥ࠭ࠧჩ"))
                    continue
                setattr(clazz, method_name, bstack1lll1llllll_opy_)
    def bstack1llll11lll1_opy_(
        self,
        method_name: str,
        bstack1lllll1l111_opy_: bstack1llll11l1l1_opy_,
        bstack1lllll11111_opy_: Callable,
    ):
        def wrapped(target, *args, **kwargs):
            bstack11l1l1l1ll_opy_ = datetime.now()
            (bstack1lllll1l111_opy_,) = wrapped.__vars__
            bstack1lllll1l111_opy_ = (
                bstack1lllll1l111_opy_
                if bstack1lllll1l111_opy_ and bstack1lllll1l111_opy_ != bstack1llll11l1l1_opy_.NONE
                else self.bstack1llll1111l1_opy_(method_name, previous_state=bstack1lllll1l111_opy_, *args, **kwargs)
            )
            if bstack1lllll1l111_opy_ == bstack1llll11l1l1_opy_.bstack1llll1l1l1l_opy_:
                ctx = bstack1llll1l1lll_opy_.create_context(self.bstack1lll1llll11_opy_(target))
                if not self.bstack1llll1llll1_opy_() or ctx.id not in bstack1llll1ll1ll_opy_.bstack1lllll111ll_opy_:
                    bstack1llll1ll1ll_opy_.bstack1lllll111ll_opy_[ctx.id] = bstack1llll111ll1_opy_(
                        ctx, self.framework_name, self.framework_version, bstack1lllll1l111_opy_
                    )
                self.logger.debug(bstack1ll_opy_ (u"ࠦࡼࡸࡡࡱࡲࡨࡨࠥࡳࡥࡵࡪࡲࡨࠥࡩࡲࡦࡣࡷࡩࡩࡀࠠࡼࡶࡤࡶ࡬࡫ࡴ࠯ࡡࡢࡧࡱࡧࡳࡴࡡࡢࢁࠥࡳࡥࡵࡪࡲࡨࡤࡴࡡ࡮ࡧࡀࡿࡲ࡫ࡴࡩࡱࡧࡣࡳࡧ࡭ࡦࡿࠣࡪࡷࡧ࡭ࡦࡹࡲࡶࡰࡥࡳࡵࡣࡷࡩࡂࢁࡦࡳࡣࡰࡩࡼࡵࡲ࡬ࡡࡶࡸࡦࡺࡥࡾࠢࡦࡸࡽࡃࡻࡤࡶࡻ࠲࡮ࡪࡽࠡ࡫ࡱࡷࡹࡧ࡮ࡤࡧࡶࡁࠧც") + str(bstack1llll1ll1ll_opy_.bstack1lllll111ll_opy_.keys()) + bstack1ll_opy_ (u"ࠧࠨძ"))
            else:
                self.logger.debug(bstack1ll_opy_ (u"ࠨࡷࡳࡣࡳࡴࡪࡪࠠ࡮ࡧࡷ࡬ࡴࡪࠠࡪࡰࡹࡳࡰ࡫ࡤ࠻ࠢࡾࡸࡦࡸࡧࡦࡶ࠱ࡣࡤࡩ࡬ࡢࡵࡶࡣࡤࢃࠠ࡮ࡧࡷ࡬ࡴࡪ࡟࡯ࡣࡰࡩࡂࢁ࡭ࡦࡶ࡫ࡳࡩࡥ࡮ࡢ࡯ࡨࢁࠥ࡬ࡲࡢ࡯ࡨࡻࡴࡸ࡫ࡠࡵࡷࡥࡹ࡫࠽ࡼࡨࡵࡥࡲ࡫ࡷࡰࡴ࡮ࡣࡸࡺࡡࡵࡧࢀࠤ࡮ࡴࡳࡵࡣࡱࡧࡪࡹ࠽ࠣწ") + str(bstack1llll1ll1ll_opy_.bstack1lllll111ll_opy_.keys()) + bstack1ll_opy_ (u"ࠢࠣჭ"))
            instance = bstack1llll1ll1ll_opy_.bstack1llll11111l_opy_(self.bstack1lll1llll11_opy_(target))
            if bstack1lllll1l111_opy_ == bstack1llll11l1l1_opy_.NONE or not instance:
                ctx = bstack1llll1l1lll_opy_.create_context(self.bstack1lll1llll11_opy_(target))
                self.logger.warning(bstack1ll_opy_ (u"ࠣࡹࡵࡥࡵࡶࡥࡥࠢࡰࡩࡹ࡮࡯ࡥࠢࡸࡲࡹࡸࡡࡤ࡭ࡨࡨ࠿ࠦࡻ࡮ࡧࡷ࡬ࡴࡪ࡟࡯ࡣࡰࡩࢂࠦࡦࡳࡣࡰࡩࡼࡵࡲ࡬ࡡࡶࡸࡦࡺࡥ࠾ࡽࡩࡶࡦࡳࡥࡸࡱࡵ࡯ࡤࡹࡴࡢࡶࡨࢁࠥࡩࡴࡹ࠿ࡾࡧࡹࡾࡽࠡ࡫ࡱࡷࡹࡧ࡮ࡤࡧࡶࡁࠧხ") + str(bstack1llll1ll1ll_opy_.bstack1lllll111ll_opy_.keys()) + bstack1ll_opy_ (u"ࠤࠥჯ"))
                return bstack1lllll11111_opy_(target, *args, **kwargs)
            bstack1lll1lllll1_opy_ = self.bstack1llll1ll1l1_opy_(
                target,
                (instance, method_name),
                (bstack1lllll1l111_opy_, bstack1lllll111l1_opy_.PRE),
                None,
                *args,
                **kwargs,
            )
            if instance.bstack1llll1lll11_opy_(bstack1lllll1l111_opy_):
                self.logger.debug(bstack1ll_opy_ (u"ࠥࡥࡵࡶ࡬ࡪࡧࡧࠤࡸࡺࡡࡵࡧ࠰ࡸࡷࡧ࡮ࡴ࡫ࡷ࡭ࡴࡴ࠺ࠡࡽ࡬ࡲࡸࡺࡡ࡯ࡥࡨ࠲ࡵࡸࡥࡷ࡫ࡲࡹࡸࡥࡳࡵࡣࡷࡩࢂࠦ࠽࠿ࠢࡾ࡭ࡳࡹࡴࡢࡰࡦࡩ࠳ࡹࡴࡢࡶࡨࢁࠥ࠮ࡻࡵࡻࡳࡩ࠭ࡺࡡࡳࡩࡨࡸ࠮ࢃ࠮ࡼ࡯ࡨࡸ࡭ࡵࡤࡠࡰࡤࡱࡪࢃࠠࡼࡣࡵ࡫ࡸࢃࠩࠡ࡝ࠥჰ") + str(instance.ref()) + bstack1ll_opy_ (u"ࠦࡢࠨჱ"))
            result = (
                bstack1lll1lllll1_opy_(target, bstack1lllll11111_opy_, *args, **kwargs)
                if callable(bstack1lll1lllll1_opy_)
                else bstack1lllll11111_opy_(target, *args, **kwargs)
            )
            bstack1llll11l11l_opy_ = self.bstack1llll1ll1l1_opy_(
                target,
                (instance, method_name),
                (bstack1lllll1l111_opy_, bstack1lllll111l1_opy_.POST),
                result,
                *args,
                **kwargs,
            )
            self.bstack1lllll1111l_opy_(instance, method_name, datetime.now() - bstack11l1l1l1ll_opy_, *args, **kwargs)
            return bstack1llll11l11l_opy_ if bstack1llll11l11l_opy_ else result
        wrapped.__name__ = method_name
        wrapped.__vars__ = (bstack1lllll1l111_opy_,)
        return wrapped
    @staticmethod
    def bstack1llll11111l_opy_(target: object, strict=True):
        ctx = bstack1llll1l1lll_opy_.create_context(target)
        instance = bstack1llll1ll1ll_opy_.bstack1lllll111ll_opy_.get(ctx.id, None)
        if instance and instance.bstack1lllll11l11_opy_(target):
            return instance
        return instance if instance and not strict else None
    @staticmethod
    def bstack1llll1ll11l_opy_(
        ctx: bstack1llll11l1ll_opy_, state: bstack1llll11l1l1_opy_, reverse=True
    ) -> List[bstack1llll111ll1_opy_]:
        return sorted(
            filter(
                lambda t: t.state == state
                and t.context.thread_id == ctx.thread_id
                and t.context.process_id == ctx.process_id,
                bstack1llll1ll1ll_opy_.bstack1lllll111ll_opy_.values(),
            ),
            key=lambda t: t.bstack1llll111111_opy_,
            reverse=reverse,
        )
    @staticmethod
    def bstack1llll11ll11_opy_(instance: bstack1llll111ll1_opy_, key: str):
        return instance and key in instance.data
    @staticmethod
    def bstack1llll1l111l_opy_(instance: bstack1llll111ll1_opy_, key: str, default_value=None):
        return instance.data.get(key, default_value) if instance else default_value
    @staticmethod
    def bstack1llll1lll11_opy_(instance: bstack1llll111ll1_opy_, key: str, value: Any) -> bool:
        instance.data[key] = value
        bstack1llll1ll1ll_opy_.logger.debug(bstack1ll_opy_ (u"ࠧࡹࡥࡵࡡࡶࡸࡦࡺࡥ࠻ࠢ࡬ࡲࡸࡺࡡ࡯ࡥࡨࡁࢀ࡯࡮ࡴࡶࡤࡲࡨ࡫࠮ࡳࡧࡩࠬ࠮ࢃࠠ࡬ࡧࡼࡁࢀࡱࡥࡺࡿࠣࡺࡦࡲࡵࡦ࠿ࠥჲ") + str(value) + bstack1ll_opy_ (u"ࠨࠢჳ"))
        return True
    @staticmethod
    def get_data(key: str, target: object, strict=True, default_value=None):
        instance = bstack1llll1ll1ll_opy_.bstack1llll11111l_opy_(target, strict)
        return bstack1llll1ll1ll_opy_.bstack1llll1l111l_opy_(instance, key, default_value)
    @staticmethod
    def set_data(key: str, value: Any, target: object, strict=True):
        instance = bstack1llll1ll1ll_opy_.bstack1llll11111l_opy_(target, strict)
        if not instance:
            return False
        instance.data[key] = value
        return True
    def bstack1llll1llll1_opy_(self):
        return self.framework_name == bstack1ll_opy_ (u"ࠧࡱ࡮ࡤࡽࡼࡸࡩࡨࡪࡷࠫჴ")
    def bstack1lll1llll11_opy_(self, target):
        return target if not self.bstack1llll1llll1_opy_() else self.bstack1lllll11ll1_opy_()
    @staticmethod
    def bstack1lllll11ll1_opy_():
        return str(os.getpid()) + str(threading.get_ident())