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
from bstack_utils.constants import bstack11l1lll1l11_opy_
def bstack1l1lll11ll_opy_(bstack11l1lll1l1l_opy_):
    from browserstack_sdk.sdk_cli.cli import cli
    from bstack_utils.helper import bstack11l1111l1_opy_
    host = bstack11l1111l1_opy_(cli.config, [bstack1ll_opy_ (u"ࠥࡥࡵ࡯ࡳࠣ៍"), bstack1ll_opy_ (u"ࠦࡦࡻࡴࡰ࡯ࡤࡸࡪࠨ៎"), bstack1ll_opy_ (u"ࠧࡧࡰࡪࠤ៏")], bstack11l1lll1l11_opy_)
    return bstack1ll_opy_ (u"࠭ࡻࡾ࠱ࡾࢁࠬ័").format(host, bstack11l1lll1l1l_opy_)