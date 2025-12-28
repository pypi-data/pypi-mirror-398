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
from urllib.parse import urlparse
from bstack_utils.config import Config
from bstack_utils.messages import bstack111l11111l1_opy_
bstack1ll1l1l111_opy_ = Config.bstack11lll1111_opy_()
def bstack1lllll1ll1l1_opy_(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False
def bstack1lllll1l1ll1_opy_(bstack1lllll1ll11l_opy_, bstack1lllll1lll11_opy_):
    from pypac import get_pac
    from pypac import PACSession
    from pypac.parser import PACFile
    import socket
    if os.path.isfile(bstack1lllll1ll11l_opy_):
        with open(bstack1lllll1ll11l_opy_) as f:
            pac = PACFile(f.read())
    elif bstack1lllll1ll1l1_opy_(bstack1lllll1ll11l_opy_):
        pac = get_pac(url=bstack1lllll1ll11l_opy_)
    else:
        raise Exception(bstack1ll_opy_ (u"ࠪࡔࡦࡩࠠࡧ࡫࡯ࡩࠥࡪ࡯ࡦࡵࠣࡲࡴࡺࠠࡦࡺ࡬ࡷࡹࡀࠠࡼࡿࠪῥ").format(bstack1lllll1ll11l_opy_))
    session = PACSession(pac)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((bstack1ll_opy_ (u"ࠦ࠽࠴࠸࠯࠺࠱࠼ࠧῦ"), 80))
        bstack1lllll1ll111_opy_ = s.getsockname()[0]
        s.close()
    except:
        bstack1lllll1ll111_opy_ = bstack1ll_opy_ (u"ࠬ࠶࠮࠱࠰࠳࠲࠵࠭ῧ")
    proxy_url = session.get_pac().find_proxy_for_url(bstack1lllll1lll11_opy_, bstack1lllll1ll111_opy_)
    return proxy_url
def bstack111l1l11l_opy_(config):
    return bstack1ll_opy_ (u"࠭ࡨࡵࡶࡳࡔࡷࡵࡸࡺࠩῨ") in config or bstack1ll_opy_ (u"ࠧࡩࡶࡷࡴࡸࡖࡲࡰࡺࡼࠫῩ") in config
def bstack1ll11ll11l_opy_(config):
    if not bstack111l1l11l_opy_(config):
        return
    if config.get(bstack1ll_opy_ (u"ࠨࡪࡷࡸࡵࡖࡲࡰࡺࡼࠫῪ")):
        return config.get(bstack1ll_opy_ (u"ࠩ࡫ࡸࡹࡶࡐࡳࡱࡻࡽࠬΎ"))
    if config.get(bstack1ll_opy_ (u"ࠪ࡬ࡹࡺࡰࡴࡒࡵࡳࡽࡿࠧῬ")):
        return config.get(bstack1ll_opy_ (u"ࠫ࡭ࡺࡴࡱࡵࡓࡶࡴࡾࡹࠨ῭"))
def bstack11ll11llll_opy_(config, bstack1lllll1lll11_opy_):
    proxy = bstack1ll11ll11l_opy_(config)
    proxies = {}
    if config.get(bstack1ll_opy_ (u"ࠬ࡮ࡴࡵࡲࡓࡶࡴࡾࡹࠨ΅")) or config.get(bstack1ll_opy_ (u"࠭ࡨࡵࡶࡳࡷࡕࡸ࡯ࡹࡻࠪ`")):
        if proxy.endswith(bstack1ll_opy_ (u"ࠧ࠯ࡲࡤࡧࠬ῰")):
            proxies = bstack1ll1ll11l_opy_(proxy, bstack1lllll1lll11_opy_)
        else:
            proxies = {
                bstack1ll_opy_ (u"ࠨࡪࡷࡸࡵࡹࠧ῱"): proxy
            }
    bstack1ll1l1l111_opy_.bstack111ll1ll1_opy_(bstack1ll_opy_ (u"ࠩࡳࡶࡴࡾࡹࡔࡧࡷࡸ࡮ࡴࡧࡴࠩῲ"), proxies)
    return proxies
def bstack1ll1ll11l_opy_(bstack1lllll1ll11l_opy_, bstack1lllll1lll11_opy_):
    proxies = {}
    global bstack1lllll1ll1ll_opy_
    if bstack1ll_opy_ (u"ࠪࡔࡆࡉ࡟ࡑࡔࡒ࡜࡞࠭ῳ") in globals():
        return bstack1lllll1ll1ll_opy_
    try:
        proxy = bstack1lllll1l1ll1_opy_(bstack1lllll1ll11l_opy_, bstack1lllll1lll11_opy_)
        if bstack1ll_opy_ (u"ࠦࡉࡏࡒࡆࡅࡗࠦῴ") in proxy:
            proxies = {}
        elif bstack1ll_opy_ (u"ࠧࡎࡔࡕࡒࠥ῵") in proxy or bstack1ll_opy_ (u"ࠨࡈࡕࡖࡓࡗࠧῶ") in proxy or bstack1ll_opy_ (u"ࠢࡔࡑࡆࡏࡘࠨῷ") in proxy:
            bstack1lllll1l1lll_opy_ = proxy.split(bstack1ll_opy_ (u"ࠣࠢࠥῸ"))
            if bstack1ll_opy_ (u"ࠤ࠽࠳࠴ࠨΌ") in bstack1ll_opy_ (u"ࠥࠦῺ").join(bstack1lllll1l1lll_opy_[1:]):
                proxies = {
                    bstack1ll_opy_ (u"ࠫ࡭ࡺࡴࡱࡵࠪΏ"): bstack1ll_opy_ (u"ࠧࠨῼ").join(bstack1lllll1l1lll_opy_[1:])
                }
            else:
                proxies = {
                    bstack1ll_opy_ (u"࠭ࡨࡵࡶࡳࡷࠬ´"): str(bstack1lllll1l1lll_opy_[0]).lower() + bstack1ll_opy_ (u"ࠢ࠻࠱࠲ࠦ῾") + bstack1ll_opy_ (u"ࠣࠤ῿").join(bstack1lllll1l1lll_opy_[1:])
                }
        elif bstack1ll_opy_ (u"ࠤࡓࡖࡔ࡞࡙ࠣ ") in proxy:
            bstack1lllll1l1lll_opy_ = proxy.split(bstack1ll_opy_ (u"ࠥࠤࠧ "))
            if bstack1ll_opy_ (u"ࠦ࠿࠵࠯ࠣ ") in bstack1ll_opy_ (u"ࠧࠨ ").join(bstack1lllll1l1lll_opy_[1:]):
                proxies = {
                    bstack1ll_opy_ (u"࠭ࡨࡵࡶࡳࡷࠬ "): bstack1ll_opy_ (u"ࠢࠣ ").join(bstack1lllll1l1lll_opy_[1:])
                }
            else:
                proxies = {
                    bstack1ll_opy_ (u"ࠨࡪࡷࡸࡵࡹࠧ "): bstack1ll_opy_ (u"ࠤ࡫ࡸࡹࡶ࠺࠰࠱ࠥ ") + bstack1ll_opy_ (u"ࠥࠦ ").join(bstack1lllll1l1lll_opy_[1:])
                }
        else:
            proxies = {
                bstack1ll_opy_ (u"ࠫ࡭ࡺࡴࡱࡵࠪ "): proxy
            }
    except Exception as e:
        print(bstack1ll_opy_ (u"ࠧࡹ࡯࡮ࡧࠣࡩࡷࡸ࡯ࡳࠤ "), bstack111l11111l1_opy_.format(bstack1lllll1ll11l_opy_, str(e)))
    bstack1lllll1ll1ll_opy_ = proxies
    return proxies