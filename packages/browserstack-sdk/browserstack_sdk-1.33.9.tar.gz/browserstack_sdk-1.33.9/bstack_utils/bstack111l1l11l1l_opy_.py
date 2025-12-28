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
from _pytest import fixtures
from _pytest.python import _call_with_optional_argument
from pytest import Module, Class
from bstack_utils.helper import Result, bstack111llll1l11_opy_
from browserstack_sdk.bstack11ll1ll111_opy_ import bstack1l111ll1l_opy_
def _111l1l1ll11_opy_(method, this, arg):
    arg_count = method.__code__.co_argcount
    if arg_count > 1:
        method(this, arg)
    else:
        method(this)
class bstack111l1l1lll1_opy_:
    def __init__(self, handler):
        self._111l1l1111l_opy_ = {}
        self._111l1l1l111_opy_ = {}
        self.handler = handler
        self.patch()
        pass
    def patch(self):
        pytest_version = bstack1l111ll1l_opy_.version()
        if bstack111llll1l11_opy_(pytest_version, bstack1ll_opy_ (u"ࠧ࠾࠮࠲࠰࠴ࠦᷯ")) >= 0:
            self._111l1l1111l_opy_[bstack1ll_opy_ (u"࠭ࡦࡶࡰࡦࡸ࡮ࡵ࡮ࡠࡨ࡬ࡼࡹࡻࡲࡦࠩᷰ")] = Module._register_setup_function_fixture
            self._111l1l1111l_opy_[bstack1ll_opy_ (u"ࠧ࡮ࡱࡧࡹࡱ࡫࡟ࡧ࡫ࡻࡸࡺࡸࡥࠨᷱ")] = Module._register_setup_module_fixture
            self._111l1l1111l_opy_[bstack1ll_opy_ (u"ࠨࡥ࡯ࡥࡸࡹ࡟ࡧ࡫ࡻࡸࡺࡸࡥࠨᷲ")] = Class._register_setup_class_fixture
            self._111l1l1111l_opy_[bstack1ll_opy_ (u"ࠩࡰࡩࡹ࡮࡯ࡥࡡࡩ࡭ࡽࡺࡵࡳࡧࠪᷳ")] = Class._register_setup_method_fixture
            Module._register_setup_function_fixture = self.bstack111l1l11ll1_opy_(bstack1ll_opy_ (u"ࠪࡪࡺࡴࡣࡵ࡫ࡲࡲࡤ࡬ࡩࡹࡶࡸࡶࡪ࠭ᷴ"))
            Module._register_setup_module_fixture = self.bstack111l1l11ll1_opy_(bstack1ll_opy_ (u"ࠫࡲࡵࡤࡶ࡮ࡨࡣ࡫࡯ࡸࡵࡷࡵࡩࠬ᷵"))
            Class._register_setup_class_fixture = self.bstack111l1l11ll1_opy_(bstack1ll_opy_ (u"ࠬࡩ࡬ࡢࡵࡶࡣ࡫࡯ࡸࡵࡷࡵࡩࠬ᷶"))
            Class._register_setup_method_fixture = self.bstack111l1l11ll1_opy_(bstack1ll_opy_ (u"࠭࡭ࡦࡶ࡫ࡳࡩࡥࡦࡪࡺࡷࡹࡷ࡫᷷ࠧ"))
        else:
            self._111l1l1111l_opy_[bstack1ll_opy_ (u"ࠧࡧࡷࡱࡧࡹ࡯࡯࡯ࡡࡩ࡭ࡽࡺࡵࡳࡧ᷸ࠪ")] = Module._inject_setup_function_fixture
            self._111l1l1111l_opy_[bstack1ll_opy_ (u"ࠨ࡯ࡲࡨࡺࡲࡥࡠࡨ࡬ࡼࡹࡻࡲࡦ᷹ࠩ")] = Module._inject_setup_module_fixture
            self._111l1l1111l_opy_[bstack1ll_opy_ (u"ࠩࡦࡰࡦࡹࡳࡠࡨ࡬ࡼࡹࡻࡲࡦ᷺ࠩ")] = Class._inject_setup_class_fixture
            self._111l1l1111l_opy_[bstack1ll_opy_ (u"ࠪࡱࡪࡺࡨࡰࡦࡢࡪ࡮ࡾࡴࡶࡴࡨࠫ᷻")] = Class._inject_setup_method_fixture
            Module._inject_setup_function_fixture = self.bstack111l1l11ll1_opy_(bstack1ll_opy_ (u"ࠫ࡫ࡻ࡮ࡤࡶ࡬ࡳࡳࡥࡦࡪࡺࡷࡹࡷ࡫ࠧ᷼"))
            Module._inject_setup_module_fixture = self.bstack111l1l11ll1_opy_(bstack1ll_opy_ (u"ࠬࡳ࡯ࡥࡷ࡯ࡩࡤ࡬ࡩࡹࡶࡸࡶࡪ᷽࠭"))
            Class._inject_setup_class_fixture = self.bstack111l1l11ll1_opy_(bstack1ll_opy_ (u"࠭ࡣ࡭ࡣࡶࡷࡤ࡬ࡩࡹࡶࡸࡶࡪ࠭᷾"))
            Class._inject_setup_method_fixture = self.bstack111l1l11ll1_opy_(bstack1ll_opy_ (u"ࠧ࡮ࡧࡷ࡬ࡴࡪ࡟ࡧ࡫ࡻࡸࡺࡸࡥࠨ᷿"))
    def bstack111l1l11l11_opy_(self, bstack111l1l1l1ll_opy_, hook_type):
        bstack111l1l11111_opy_ = id(bstack111l1l1l1ll_opy_.__class__)
        if (bstack111l1l11111_opy_, hook_type) in self._111l1l1l111_opy_:
            return
        meth = getattr(bstack111l1l1l1ll_opy_, hook_type, None)
        if meth is not None and fixtures.getfixturemarker(meth) is None:
            self._111l1l1l111_opy_[(bstack111l1l11111_opy_, hook_type)] = meth
            setattr(bstack111l1l1l1ll_opy_, hook_type, self.bstack111l1l1l11l_opy_(hook_type, bstack111l1l11111_opy_))
    def bstack111l1l111l1_opy_(self, instance, bstack111l1l1ll1l_opy_):
        if bstack111l1l1ll1l_opy_ == bstack1ll_opy_ (u"ࠣࡨࡸࡲࡨࡺࡩࡰࡰࡢࡪ࡮ࡾࡴࡶࡴࡨࠦḀ"):
            self.bstack111l1l11l11_opy_(instance.obj, bstack1ll_opy_ (u"ࠤࡶࡩࡹࡻࡰࡠࡨࡸࡲࡨࡺࡩࡰࡰࠥḁ"))
            self.bstack111l1l11l11_opy_(instance.obj, bstack1ll_opy_ (u"ࠥࡸࡪࡧࡲࡥࡱࡺࡲࡤ࡬ࡵ࡯ࡥࡷ࡭ࡴࡴࠢḂ"))
        if bstack111l1l1ll1l_opy_ == bstack1ll_opy_ (u"ࠦࡲࡵࡤࡶ࡮ࡨࡣ࡫࡯ࡸࡵࡷࡵࡩࠧḃ"):
            self.bstack111l1l11l11_opy_(instance.obj, bstack1ll_opy_ (u"ࠧࡹࡥࡵࡷࡳࡣࡲࡵࡤࡶ࡮ࡨࠦḄ"))
            self.bstack111l1l11l11_opy_(instance.obj, bstack1ll_opy_ (u"ࠨࡴࡦࡣࡵࡨࡴࡽ࡮ࡠ࡯ࡲࡨࡺࡲࡥࠣḅ"))
        if bstack111l1l1ll1l_opy_ == bstack1ll_opy_ (u"ࠢࡤ࡮ࡤࡷࡸࡥࡦࡪࡺࡷࡹࡷ࡫ࠢḆ"):
            self.bstack111l1l11l11_opy_(instance.obj, bstack1ll_opy_ (u"ࠣࡵࡨࡸࡺࡶ࡟ࡤ࡮ࡤࡷࡸࠨḇ"))
            self.bstack111l1l11l11_opy_(instance.obj, bstack1ll_opy_ (u"ࠤࡷࡩࡦࡸࡤࡰࡹࡱࡣࡨࡲࡡࡴࡵࠥḈ"))
        if bstack111l1l1ll1l_opy_ == bstack1ll_opy_ (u"ࠥࡱࡪࡺࡨࡰࡦࡢࡪ࡮ࡾࡴࡶࡴࡨࠦḉ"):
            self.bstack111l1l11l11_opy_(instance.obj, bstack1ll_opy_ (u"ࠦࡸ࡫ࡴࡶࡲࡢࡱࡪࡺࡨࡰࡦࠥḊ"))
            self.bstack111l1l11l11_opy_(instance.obj, bstack1ll_opy_ (u"ࠧࡺࡥࡢࡴࡧࡳࡼࡴ࡟࡮ࡧࡷ࡬ࡴࡪࠢḋ"))
    @staticmethod
    def bstack111l1l1l1l1_opy_(hook_type, func, args):
        if hook_type in [bstack1ll_opy_ (u"࠭ࡳࡦࡶࡸࡴࡤࡳࡥࡵࡪࡲࡨࠬḌ"), bstack1ll_opy_ (u"ࠧࡵࡧࡤࡶࡩࡵࡷ࡯ࡡࡰࡩࡹ࡮࡯ࡥࠩḍ")]:
            _111l1l1ll11_opy_(func, args[0], args[1])
            return
        _call_with_optional_argument(func, args[0])
    def bstack111l1l1l11l_opy_(self, hook_type, bstack111l1l11111_opy_):
        def bstack111l1l111ll_opy_(arg=None):
            self.handler(hook_type, bstack1ll_opy_ (u"ࠨࡤࡨࡪࡴࡸࡥࠨḎ"))
            result = None
            try:
                bstack1lllll11111_opy_ = self._111l1l1l111_opy_[(bstack111l1l11111_opy_, hook_type)]
                self.bstack111l1l1l1l1_opy_(hook_type, bstack1lllll11111_opy_, (arg,))
                result = Result(result=bstack1ll_opy_ (u"ࠩࡳࡥࡸࡹࡥࡥࠩḏ"))
            except Exception as e:
                result = Result(result=bstack1ll_opy_ (u"ࠪࡪࡦ࡯࡬ࡦࡦࠪḐ"), exception=e)
                self.handler(hook_type, bstack1ll_opy_ (u"ࠫࡦ࡬ࡴࡦࡴࠪḑ"), result)
                raise e.with_traceback(e.__traceback__)
            self.handler(hook_type, bstack1ll_opy_ (u"ࠬࡧࡦࡵࡧࡵࠫḒ"), result)
        def bstack111l1l11lll_opy_(this, arg=None):
            self.handler(hook_type, bstack1ll_opy_ (u"࠭ࡢࡦࡨࡲࡶࡪ࠭ḓ"))
            result = None
            exception = None
            try:
                self.bstack111l1l1l1l1_opy_(hook_type, self._111l1l1l111_opy_[hook_type], (this, arg))
                result = Result(result=bstack1ll_opy_ (u"ࠧࡱࡣࡶࡷࡪࡪࠧḔ"))
            except Exception as e:
                result = Result(result=bstack1ll_opy_ (u"ࠨࡨࡤ࡭ࡱ࡫ࡤࠨḕ"), exception=e)
                self.handler(hook_type, bstack1ll_opy_ (u"ࠩࡤࡪࡹ࡫ࡲࠨḖ"), result)
                raise e.with_traceback(e.__traceback__)
            self.handler(hook_type, bstack1ll_opy_ (u"ࠪࡥ࡫ࡺࡥࡳࠩḗ"), result)
        if hook_type in [bstack1ll_opy_ (u"ࠫࡸ࡫ࡴࡶࡲࡢࡱࡪࡺࡨࡰࡦࠪḘ"), bstack1ll_opy_ (u"ࠬࡺࡥࡢࡴࡧࡳࡼࡴ࡟࡮ࡧࡷ࡬ࡴࡪࠧḙ")]:
            return bstack111l1l11lll_opy_
        return bstack111l1l111ll_opy_
    def bstack111l1l11ll1_opy_(self, bstack111l1l1ll1l_opy_):
        def bstack111l11lllll_opy_(this, *args, **kwargs):
            self.bstack111l1l111l1_opy_(this, bstack111l1l1ll1l_opy_)
            self._111l1l1111l_opy_[bstack111l1l1ll1l_opy_](this, *args, **kwargs)
        return bstack111l11lllll_opy_