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
import re
from enum import Enum
bstack11l11111ll_opy_ = {
  bstack1ll_opy_ (u"ࠬࡻࡳࡦࡴࡑࡥࡲ࡫ࠧ៲"): bstack1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯࠳ࡻࡳࡦࡴࠪ៳"),
  bstack1ll_opy_ (u"ࠧࡢࡥࡦࡩࡸࡹࡋࡦࡻࠪ៴"): bstack1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࠮࡬ࡧࡼࠫ៵"),
  bstack1ll_opy_ (u"ࠩࡲࡷ࡛࡫ࡲࡴ࡫ࡲࡲࠬ៶"): bstack1ll_opy_ (u"ࠪࡳࡸࡥࡶࡦࡴࡶ࡭ࡴࡴࠧ៷"),
  bstack1ll_opy_ (u"ࠫࡺࡹࡥࡘ࠵ࡆࠫ៸"): bstack1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮࠲ࡺࡹࡥࡠࡹ࠶ࡧࠬ៹"),
  bstack1ll_opy_ (u"࠭ࡰࡳࡱ࡭ࡩࡨࡺࡎࡢ࡯ࡨࠫ៺"): bstack1ll_opy_ (u"ࠧࡱࡴࡲ࡮ࡪࡩࡴࠨ៻"),
  bstack1ll_opy_ (u"ࠨࡤࡸ࡭ࡱࡪࡎࡢ࡯ࡨࠫ៼"): bstack1ll_opy_ (u"ࠩࡥࡹ࡮ࡲࡤࠨ៽"),
  bstack1ll_opy_ (u"ࠪࡷࡪࡹࡳࡪࡱࡱࡒࡦࡳࡥࠨ៾"): bstack1ll_opy_ (u"ࠫࡳࡧ࡭ࡦࠩ៿"),
  bstack1ll_opy_ (u"ࠬࡪࡥࡣࡷࡪࠫ᠀"): bstack1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯࠳ࡪࡥࡣࡷࡪࠫ᠁"),
  bstack1ll_opy_ (u"ࠧࡤࡱࡱࡷࡴࡲࡥࡍࡱࡪࡷࠬ᠂"): bstack1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࠮ࡤࡱࡱࡷࡴࡲࡥࠨ᠃"),
  bstack1ll_opy_ (u"ࠩࡱࡩࡹࡽ࡯ࡳ࡭ࡏࡳ࡬ࡹࠧ᠄"): bstack1ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬࠰ࡱࡩࡹࡽ࡯ࡳ࡭ࡏࡳ࡬ࡹࠧ᠅"),
  bstack1ll_opy_ (u"ࠫࡦࡶࡰࡪࡷࡰࡐࡴ࡭ࡳࠨ᠆"): bstack1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮࠲ࡦࡶࡰࡪࡷࡰࡐࡴ࡭ࡳࠨ᠇"),
  bstack1ll_opy_ (u"࠭ࡶࡪࡦࡨࡳࠬ᠈"): bstack1ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰ࠴ࡶࡪࡦࡨࡳࠬ᠉"),
  bstack1ll_opy_ (u"ࠨࡵࡨࡰࡪࡴࡩࡶ࡯ࡏࡳ࡬ࡹࠧ᠊"): bstack1ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫࠯ࡵࡨࡰࡪࡴࡩࡶ࡯ࡏࡳ࡬ࡹࠧ᠋"),
  bstack1ll_opy_ (u"ࠪࡸࡪࡲࡥ࡮ࡧࡷࡶࡾࡒ࡯ࡨࡵࠪ᠌"): bstack1ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭࠱ࡸࡪࡲࡥ࡮ࡧࡷࡶࡾࡒ࡯ࡨࡵࠪ᠍"),
  bstack1ll_opy_ (u"ࠬ࡭ࡥࡰࡎࡲࡧࡦࡺࡩࡰࡰࠪ᠎"): bstack1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯࠳࡭ࡥࡰࡎࡲࡧࡦࡺࡩࡰࡰࠪ᠏"),
  bstack1ll_opy_ (u"ࠧࡵ࡫ࡰࡩࡿࡵ࡮ࡦࠩ᠐"): bstack1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࠮ࡵ࡫ࡰࡩࡿࡵ࡮ࡦࠩ᠑"),
  bstack1ll_opy_ (u"ࠩࡶࡩࡱ࡫࡮ࡪࡷࡰ࡚ࡪࡸࡳࡪࡱࡱࠫ᠒"): bstack1ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬࠰ࡶࡩࡱ࡫࡮ࡪࡷࡰࡣࡻ࡫ࡲࡴ࡫ࡲࡲࠬ᠓"),
  bstack1ll_opy_ (u"ࠫࡲࡧࡳ࡬ࡅࡲࡱࡲࡧ࡮ࡥࡵࠪ᠔"): bstack1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮࠲ࡲࡧࡳ࡬ࡅࡲࡱࡲࡧ࡮ࡥࡵࠪ᠕"),
  bstack1ll_opy_ (u"࠭ࡩࡥ࡮ࡨࡘ࡮ࡳࡥࡰࡷࡷࠫ᠖"): bstack1ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰ࠴ࡩࡥ࡮ࡨࡘ࡮ࡳࡥࡰࡷࡷࠫ᠗"),
  bstack1ll_opy_ (u"ࠨ࡯ࡤࡷࡰࡈࡡࡴ࡫ࡦࡅࡺࡺࡨࠨ᠘"): bstack1ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫࠯࡯ࡤࡷࡰࡈࡡࡴ࡫ࡦࡅࡺࡺࡨࠨ᠙"),
  bstack1ll_opy_ (u"ࠪࡷࡪࡴࡤࡌࡧࡼࡷࠬ᠚"): bstack1ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭࠱ࡷࡪࡴࡤࡌࡧࡼࡷࠬ᠛"),
  bstack1ll_opy_ (u"ࠬࡧࡵࡵࡱ࡚ࡥ࡮ࡺࠧ᠜"): bstack1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯࠳ࡧࡵࡵࡱ࡚ࡥ࡮ࡺࠧ᠝"),
  bstack1ll_opy_ (u"ࠧࡩࡱࡶࡸࡸ࠭᠞"): bstack1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࠮ࡩࡱࡶࡸࡸ࠭᠟"),
  bstack1ll_opy_ (u"ࠩࡥࡪࡨࡧࡣࡩࡧࠪᠠ"): bstack1ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬࠰ࡥࡪࡨࡧࡣࡩࡧࠪᠡ"),
  bstack1ll_opy_ (u"ࠫࡼࡹࡌࡰࡥࡤࡰࡘࡻࡰࡱࡱࡵࡸࠬᠢ"): bstack1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮࠲ࡼࡹࡌࡰࡥࡤࡰࡘࡻࡰࡱࡱࡵࡸࠬᠣ"),
  bstack1ll_opy_ (u"࠭ࡤࡪࡵࡤࡦࡱ࡫ࡃࡰࡴࡶࡖࡪࡹࡴࡳ࡫ࡦࡸ࡮ࡵ࡮ࡴࠩᠤ"): bstack1ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰ࠴ࡤࡪࡵࡤࡦࡱ࡫ࡃࡰࡴࡶࡖࡪࡹࡴࡳ࡫ࡦࡸ࡮ࡵ࡮ࡴࠩᠥ"),
  bstack1ll_opy_ (u"ࠨࡦࡨࡺ࡮ࡩࡥࡏࡣࡰࡩࠬᠦ"): bstack1ll_opy_ (u"ࠩࡧࡩࡻ࡯ࡣࡦࠩᠧ"),
  bstack1ll_opy_ (u"ࠪࡶࡪࡧ࡬ࡎࡱࡥ࡭ࡱ࡫ࠧᠨ"): bstack1ll_opy_ (u"ࠫࡷ࡫ࡡ࡭ࡡࡰࡳࡧ࡯࡬ࡦࠩᠩ"),
  bstack1ll_opy_ (u"ࠬࡧࡰࡱ࡫ࡸࡱ࡛࡫ࡲࡴ࡫ࡲࡲࠬᠪ"): bstack1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯࠳ࡧࡰࡱ࡫ࡸࡱࡤࡼࡥࡳࡵ࡬ࡳࡳ࠭ᠫ"),
  bstack1ll_opy_ (u"ࠧࡤࡷࡶࡸࡴࡳࡎࡦࡶࡺࡳࡷࡱࠧᠬ"): bstack1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࠮ࡤࡷࡶࡸࡴࡳࡎࡦࡶࡺࡳࡷࡱࠧᠭ"),
  bstack1ll_opy_ (u"ࠩࡱࡩࡹࡽ࡯ࡳ࡭ࡓࡶࡴ࡬ࡩ࡭ࡧࠪᠮ"): bstack1ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬࠰ࡱࡩࡹࡽ࡯ࡳ࡭ࡓࡶࡴ࡬ࡩ࡭ࡧࠪᠯ"),
  bstack1ll_opy_ (u"ࠫࡦࡩࡣࡦࡲࡷࡍࡳࡹࡥࡤࡷࡵࡩࡈ࡫ࡲࡵࡵࠪᠰ"): bstack1ll_opy_ (u"ࠬࡧࡣࡤࡧࡳࡸࡘࡹ࡬ࡄࡧࡵࡸࡸ࠭ᠱ"),
  bstack1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯ࡘࡊࡋࠨᠲ"): bstack1ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰ࠴ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯ࡘࡊࡋࠨᠳ"),
  bstack1ll_opy_ (u"ࠨࡵࡲࡹࡷࡩࡥࠨᠴ"): bstack1ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫࠯ࡵࡲࡹࡷࡩࡥࠨᠵ"),
  bstack1ll_opy_ (u"ࠪࡦࡺ࡯࡬ࡥࡋࡧࡩࡳࡺࡩࡧ࡫ࡨࡶࠬᠶ"): bstack1ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭࠱ࡦࡺ࡯࡬ࡥࡋࡧࡩࡳࡺࡩࡧ࡫ࡨࡶࠬᠷ"),
  bstack1ll_opy_ (u"ࠬ࡮࡯ࡴࡶࡑࡥࡲ࡫ࠧᠸ"): bstack1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯࠳࡮࡯ࡴࡶࡑࡥࡲ࡫ࠧᠹ"),
  bstack1ll_opy_ (u"ࠧࡦࡰࡤࡦࡱ࡫ࡓࡪ࡯ࠪᠺ"): bstack1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࠮ࡦࡰࡤࡦࡱ࡫ࡓࡪ࡯ࠪᠻ"),
  bstack1ll_opy_ (u"ࠩࡶ࡭ࡲࡕࡰࡵ࡫ࡲࡲࡸ࠭ᠼ"): bstack1ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬࠰ࡶ࡭ࡲࡕࡰࡵ࡫ࡲࡲࡸ࠭ᠽ"),
  bstack1ll_opy_ (u"ࠫࡺࡶ࡬ࡰࡣࡧࡑࡪࡪࡩࡢࠩᠾ"): bstack1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮࠲ࡺࡶ࡬ࡰࡣࡧࡑࡪࡪࡩࡢࠩᠿ"),
  bstack1ll_opy_ (u"࠭ࡴࡦࡵࡷ࡬ࡺࡨࡂࡶ࡫࡯ࡨ࡚ࡻࡩࡥࠩᡀ"): bstack1ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰ࠴ࡴࡦࡵࡷ࡬ࡺࡨࡂࡶ࡫࡯ࡨ࡚ࡻࡩࡥࠩᡁ"),
  bstack1ll_opy_ (u"ࠨࡤࡸ࡭ࡱࡪࡐࡳࡱࡧࡹࡨࡺࡍࡢࡲࠪᡂ"): bstack1ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫࠯ࡤࡸ࡭ࡱࡪࡐࡳࡱࡧࡹࡨࡺࡍࡢࡲࠪᡃ")
}
bstack11l11lll1l1_opy_ = [
  bstack1ll_opy_ (u"ࠪࡳࡸ࠭ᡄ"),
  bstack1ll_opy_ (u"ࠫࡴࡹࡖࡦࡴࡶ࡭ࡴࡴࠧᡅ"),
  bstack1ll_opy_ (u"ࠬࡹࡥ࡭ࡧࡱ࡭ࡺࡳࡖࡦࡴࡶ࡭ࡴࡴࠧᡆ"),
  bstack1ll_opy_ (u"࠭ࡳࡦࡵࡶ࡭ࡴࡴࡎࡢ࡯ࡨࠫᡇ"),
  bstack1ll_opy_ (u"ࠧࡥࡧࡹ࡭ࡨ࡫ࡎࡢ࡯ࡨࠫᡈ"),
  bstack1ll_opy_ (u"ࠨࡴࡨࡥࡱࡓ࡯ࡣ࡫࡯ࡩࠬᡉ"),
  bstack1ll_opy_ (u"ࠩࡤࡴࡵ࡯ࡵ࡮ࡘࡨࡶࡸ࡯࡯࡯ࠩᡊ"),
]
bstack11111l11l_opy_ = {
  bstack1ll_opy_ (u"ࠪࡹࡸ࡫ࡲࡏࡣࡰࡩࠬᡋ"): [bstack1ll_opy_ (u"ࠫࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢ࡙ࡘࡋࡒࡏࡃࡐࡉࠬᡌ"), bstack1ll_opy_ (u"ࠬࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣ࡚࡙ࡅࡓࡡࡑࡅࡒࡋࠧᡍ")],
  bstack1ll_opy_ (u"࠭ࡡࡤࡥࡨࡷࡸࡑࡥࡺࠩᡎ"): bstack1ll_opy_ (u"ࠧࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡁࡄࡅࡈࡗࡘࡥࡋࡆ࡛ࠪᡏ"),
  bstack1ll_opy_ (u"ࠨࡤࡸ࡭ࡱࡪࡎࡢ࡯ࡨࠫᡐ"): bstack1ll_opy_ (u"ࠩࡅࡖࡔ࡝ࡓࡆࡔࡖࡘࡆࡉࡋࡠࡄࡘࡍࡑࡊ࡟ࡏࡃࡐࡉࠬᡑ"),
  bstack1ll_opy_ (u"ࠪࡴࡷࡵࡪࡦࡥࡷࡒࡦࡳࡥࠨᡒ"): bstack1ll_opy_ (u"ࠫࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡔࡗࡕࡊࡆࡅࡗࡣࡓࡇࡍࡆࠩᡓ"),
  bstack1ll_opy_ (u"ࠬࡨࡵࡪ࡮ࡧࡍࡩ࡫࡮ࡵ࡫ࡩ࡭ࡪࡸࠧᡔ"): bstack1ll_opy_ (u"࠭ࡂࡓࡑ࡚ࡗࡊࡘࡓࡕࡃࡆࡏࡤࡈࡕࡊࡎࡇࡣࡎࡊࡅࡏࡖࡌࡊࡎࡋࡒࠨᡕ"),
  bstack1ll_opy_ (u"ࠧࡱࡣࡵࡥࡱࡲࡥ࡭ࡵࡓࡩࡷࡖ࡬ࡢࡶࡩࡳࡷࡳࠧᡖ"): bstack1ll_opy_ (u"ࠨࡄࡕࡓ࡜࡙ࡅࡓࡕࡗࡅࡈࡑ࡟ࡑࡃࡕࡅࡑࡒࡅࡍࡕࡢࡔࡊࡘ࡟ࡑࡎࡄࡘࡋࡕࡒࡎࠩᡗ"),
  bstack1ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫ࡍࡱࡦࡥࡱ࠭ᡘ"): bstack1ll_opy_ (u"ࠪࡆࡗࡕࡗࡔࡇࡕࡗ࡙ࡇࡃࡌࡡࡏࡓࡈࡇࡌࠨᡙ"),
  bstack1ll_opy_ (u"ࠫࡷ࡫ࡲࡶࡰࡗࡩࡸࡺࡳࠨᡚ"): bstack1ll_opy_ (u"ࠬࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣࡗࡋࡒࡖࡐࡢࡘࡊ࡙ࡔࡔࠩᡛ"),
  bstack1ll_opy_ (u"࠭ࡡࡱࡲࠪᡜ"): [bstack1ll_opy_ (u"ࠧࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡁࡑࡒࡢࡍࡉ࠭ᡝ"), bstack1ll_opy_ (u"ࠨࡄࡕࡓ࡜࡙ࡅࡓࡕࡗࡅࡈࡑ࡟ࡂࡒࡓࠫᡞ")],
  bstack1ll_opy_ (u"ࠩ࡯ࡳ࡬ࡒࡥࡷࡧ࡯ࠫᡟ"): bstack1ll_opy_ (u"ࠪࡆࡗࡕࡗࡔࡇࡕࡗ࡙ࡇࡃࡌࡡࡖࡈࡐࡥࡌࡐࡉࡏࡉ࡛ࡋࡌࠨᡠ"),
  bstack1ll_opy_ (u"ࠫࡦࡻࡴࡰ࡯ࡤࡸ࡮ࡵ࡮ࠨᡡ"): bstack1ll_opy_ (u"ࠬࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣࡆ࡛ࡔࡐࡏࡄࡘࡎࡕࡎࠨᡢ"),
  bstack1ll_opy_ (u"࠭ࡴࡦࡵࡷࡓࡧࡹࡥࡳࡸࡤࡦ࡮ࡲࡩࡵࡻࠪᡣ"): [bstack1ll_opy_ (u"ࠧࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡔࡆࡕࡗࡣࡔࡈࡓࡆࡔ࡙ࡅࡇࡏࡌࡊࡖ࡜ࠫᡤ"), bstack1ll_opy_ (u"ࠨࡄࡕࡓ࡜࡙ࡅࡓࡕࡗࡅࡈࡑ࡟ࡕࡇࡖࡘࡤࡘࡅࡑࡑࡕࡘࡎࡔࡇࠨᡥ")],
  bstack1ll_opy_ (u"ࠩࡷࡹࡷࡨ࡯ࡔࡥࡤࡰࡪ࠭ᡦ"): bstack1ll_opy_ (u"ࠪࡆࡗࡕࡗࡔࡇࡕࡗ࡙ࡇࡃࡌࡡࡗ࡙ࡗࡈࡏࡔࡅࡄࡐࡊ࠭ᡧ"),
  bstack1ll_opy_ (u"ࠫࡸࡳࡡࡳࡶࡖࡩࡱ࡫ࡣࡵ࡫ࡲࡲࡋ࡫ࡡࡵࡷࡵࡩࡇࡸࡡ࡯ࡥ࡫ࡩࡸࡋࡎࡗࠩᡨ"): bstack1ll_opy_ (u"ࠬࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣࡔࡘࡃࡉࡇࡖࡘࡗࡇࡔࡊࡑࡑࡣࡘࡓࡁࡓࡖࡢࡗࡊࡒࡅࡄࡖࡌࡓࡓࡥࡆࡆࡃࡗ࡙ࡗࡋ࡟ࡃࡔࡄࡒࡈࡎࡅࡔࠩᡩ")
}
bstack1ll1ll1l1_opy_ = {
  bstack1ll_opy_ (u"࠭ࡵࡴࡧࡵࡒࡦࡳࡥࠨᡪ"): [bstack1ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰ࠴ࡵࡴࡧࡵࡣࡳࡧ࡭ࡦࠩᡫ"), bstack1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࠮ࡶࡵࡨࡶࡓࡧ࡭ࡦࠩᡬ")],
  bstack1ll_opy_ (u"ࠩࡤࡧࡨ࡫ࡳࡴࡍࡨࡽࠬᡭ"): [bstack1ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬࠰ࡤࡧࡨ࡫ࡳࡴࡡ࡮ࡩࡾ࠭ᡮ"), bstack1ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭࠱ࡥࡨࡩࡥࡴࡵࡎࡩࡾ࠭ᡯ")],
  bstack1ll_opy_ (u"ࠬࡨࡵࡪ࡮ࡧࡒࡦࡳࡥࠨᡰ"): bstack1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯࠳ࡨࡵࡪ࡮ࡧࡒࡦࡳࡥࠨᡱ"),
  bstack1ll_opy_ (u"ࠧࡱࡴࡲ࡮ࡪࡩࡴࡏࡣࡰࡩࠬᡲ"): bstack1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࠮ࡱࡴࡲ࡮ࡪࡩࡴࡏࡣࡰࡩࠬᡳ"),
  bstack1ll_opy_ (u"ࠩࡥࡹ࡮ࡲࡤࡊࡦࡨࡲࡹ࡯ࡦࡪࡧࡵࠫᡴ"): bstack1ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬࠰ࡥࡹ࡮ࡲࡤࡊࡦࡨࡲࡹ࡯ࡦࡪࡧࡵࠫᡵ"),
  bstack1ll_opy_ (u"ࠫࡵࡧࡲࡢ࡮࡯ࡩࡱࡹࡐࡦࡴࡓࡰࡦࡺࡦࡰࡴࡰࠫᡶ"): [bstack1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮࠲ࡵࡶࡰࠨᡷ"), bstack1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯࠳ࡶࡡࡳࡣ࡯ࡰࡪࡲࡳࡑࡧࡵࡔࡱࡧࡴࡧࡱࡵࡱࠬᡸ")],
  bstack1ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰࡒ࡯ࡤࡣ࡯ࠫ᡹"): bstack1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࠮࡭ࡱࡦࡥࡱ࠭᡺"),
  bstack1ll_opy_ (u"ࠩࡵࡩࡷࡻ࡮ࡕࡧࡶࡸࡸ࠭᡻"): bstack1ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬࠰ࡵࡩࡷࡻ࡮ࡕࡧࡶࡸࡸ࠭᡼"),
  bstack1ll_opy_ (u"ࠫࡦࡶࡰࠨ᡽"): bstack1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮࠲ࡦࡶࡰࠨ᡾"),
  bstack1ll_opy_ (u"࠭࡬ࡰࡩࡏࡩࡻ࡫࡬ࠨ᡿"): bstack1ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰ࠴࡬ࡰࡩࡏࡩࡻ࡫࡬ࠨᢀ"),
  bstack1ll_opy_ (u"ࠨࡣࡸࡸࡴࡳࡡࡵ࡫ࡲࡲࠬᢁ"): bstack1ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫࠯ࡣࡸࡸࡴࡳࡡࡵ࡫ࡲࡲࠬᢂ"),
  bstack1ll_opy_ (u"ࠥࡷࡲࡧࡲࡵࡕࡨࡰࡪࡩࡴࡪࡱࡱࡊࡪࡧࡴࡶࡴࡨࡆࡷࡧ࡮ࡤࡪࡨࡷࡈࡒࡉࠣᢃ"): bstack1ll_opy_ (u"ࠦࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭࠱ࡸࡪࡹࡴࡐࡴࡦ࡬ࡪࡹࡴࡳࡣࡷ࡭ࡴࡴ࠮ࡴ࡯ࡤࡶࡹ࡙ࡥ࡭ࡧࡦࡸ࡮ࡵ࡮ࡇࡧࡤࡸࡺࡸࡥࡃࡴࡤࡲࡨ࡮ࡥࡴࠤᢄ"),
}
bstack1ll11ll1l1_opy_ = {
  bstack1ll_opy_ (u"ࠬࡵࡳࡗࡧࡵࡷ࡮ࡵ࡮ࠨᢅ"): bstack1ll_opy_ (u"࠭࡯ࡴࡡࡹࡩࡷࡹࡩࡰࡰࠪᢆ"),
  bstack1ll_opy_ (u"ࠧࡴࡧ࡯ࡩࡳ࡯ࡵ࡮ࡘࡨࡶࡸ࡯࡯࡯ࠩᢇ"): [bstack1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࠮ࡴࡧ࡯ࡩࡳ࡯ࡵ࡮ࡡࡹࡩࡷࡹࡩࡰࡰࠪᢈ"), bstack1ll_opy_ (u"ࠩࡶࡩࡱ࡫࡮ࡪࡷࡰࡣࡻ࡫ࡲࡴ࡫ࡲࡲࠬᢉ")],
  bstack1ll_opy_ (u"ࠪࡷࡪࡹࡳࡪࡱࡱࡒࡦࡳࡥࠨᢊ"): bstack1ll_opy_ (u"ࠫࡳࡧ࡭ࡦࠩᢋ"),
  bstack1ll_opy_ (u"ࠬࡪࡥࡷ࡫ࡦࡩࡓࡧ࡭ࡦࠩᢌ"): bstack1ll_opy_ (u"࠭ࡤࡦࡸ࡬ࡧࡪ࠭ᢍ"),
  bstack1ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡏࡣࡰࡩࠬᢎ"): [bstack1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࠩᢏ"), bstack1ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡢࡲࡦࡳࡥࠨᢐ")],
  bstack1ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵ࡚ࡪࡸࡳࡪࡱࡱࠫᢑ"): bstack1ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࡤࡼࡥࡳࡵ࡬ࡳࡳ࠭ᢒ"),
  bstack1ll_opy_ (u"ࠬࡸࡥࡢ࡮ࡐࡳࡧ࡯࡬ࡦࠩᢓ"): bstack1ll_opy_ (u"࠭ࡲࡦࡣ࡯ࡣࡲࡵࡢࡪ࡮ࡨࠫᢔ"),
  bstack1ll_opy_ (u"ࠧࡢࡲࡳ࡭ࡺࡳࡖࡦࡴࡶ࡭ࡴࡴࠧᢕ"): [bstack1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࠮ࡢࡲࡳ࡭ࡺࡳ࡟ࡷࡧࡵࡷ࡮ࡵ࡮ࠨᢖ"), bstack1ll_opy_ (u"ࠩࡤࡴࡵ࡯ࡵ࡮ࡡࡹࡩࡷࡹࡩࡰࡰࠪᢗ")],
  bstack1ll_opy_ (u"ࠪࡥࡨࡩࡥࡱࡶࡌࡲࡸ࡫ࡣࡶࡴࡨࡇࡪࡸࡴࡴࠩᢘ"): [bstack1ll_opy_ (u"ࠫࡦࡩࡣࡦࡲࡷࡗࡸࡲࡃࡦࡴࡷࡷࠬᢙ"), bstack1ll_opy_ (u"ࠬࡧࡣࡤࡧࡳࡸࡘࡹ࡬ࡄࡧࡵࡸࠬᢚ")]
}
bstack1l1l1l111l_opy_ = [
  bstack1ll_opy_ (u"࠭ࡡࡤࡥࡨࡴࡹࡏ࡮ࡴࡧࡦࡹࡷ࡫ࡃࡦࡴࡷࡷࠬᢛ"),
  bstack1ll_opy_ (u"ࠧࡱࡣࡪࡩࡑࡵࡡࡥࡕࡷࡶࡦࡺࡥࡨࡻࠪᢜ"),
  bstack1ll_opy_ (u"ࠨࡲࡵࡳࡽࡿࠧᢝ"),
  bstack1ll_opy_ (u"ࠩࡶࡩࡹ࡝ࡩ࡯ࡦࡲࡻࡗ࡫ࡣࡵࠩᢞ"),
  bstack1ll_opy_ (u"ࠪࡸ࡮ࡳࡥࡰࡷࡷࡷࠬᢟ"),
  bstack1ll_opy_ (u"ࠫࡸࡺࡲࡪࡥࡷࡊ࡮ࡲࡥࡊࡰࡷࡩࡷࡧࡣࡵࡣࡥ࡭ࡱ࡯ࡴࡺࠩᢠ"),
  bstack1ll_opy_ (u"ࠬࡻ࡮ࡩࡣࡱࡨࡱ࡫ࡤࡑࡴࡲࡱࡵࡺࡂࡦࡪࡤࡺ࡮ࡵࡲࠨᢡ"),
  bstack1ll_opy_ (u"࠭ࡧࡰࡱࡪ࠾ࡨ࡮ࡲࡰ࡯ࡨࡓࡵࡺࡩࡰࡰࡶࠫᢢ"),
  bstack1ll_opy_ (u"ࠧ࡮ࡱࡽ࠾࡫࡯ࡲࡦࡨࡲࡼࡔࡶࡴࡪࡱࡱࡷࠬᢣ"),
  bstack1ll_opy_ (u"ࠨ࡯ࡶ࠾ࡪࡪࡧࡦࡑࡳࡸ࡮ࡵ࡮ࡴࠩᢤ"),
  bstack1ll_opy_ (u"ࠩࡶࡩ࠿࡯ࡥࡐࡲࡷ࡭ࡴࡴࡳࠨᢥ"),
  bstack1ll_opy_ (u"ࠪࡷࡦ࡬ࡡࡳ࡫࠱ࡳࡵࡺࡩࡰࡰࡶࠫᢦ"),
]
bstack11l11l1ll_opy_ = [
  bstack1ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭ࡏࡳࡨࡧ࡬ࠨᢧ"),
  bstack1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷ࡙ࡴࡢࡥ࡮ࡐࡴࡩࡡ࡭ࡑࡳࡸ࡮ࡵ࡮ࡴࠩᢨ"),
  bstack1ll_opy_ (u"࠭࡬ࡰࡥࡤࡰࡔࡶࡴࡪࡱࡱࡷᢩࠬ"),
  bstack1ll_opy_ (u"ࠧࡱࡣࡵࡥࡱࡲࡥ࡭ࡵࡓࡩࡷࡖ࡬ࡢࡶࡩࡳࡷࡳࠧᢪ"),
  bstack1ll_opy_ (u"ࠨࡲ࡯ࡥࡹ࡬࡯ࡳ࡯ࡶࠫ᢫"),
  bstack1ll_opy_ (u"ࠩ࡯ࡳ࡬ࡒࡥࡷࡧ࡯ࠫ᢬"),
  bstack1ll_opy_ (u"ࠪ࡬ࡹࡺࡰࡑࡴࡲࡼࡾ࠭᢭"),
  bstack1ll_opy_ (u"ࠫ࡭ࡺࡴࡱࡵࡓࡶࡴࡾࡹࠨ᢮"),
  bstack1ll_opy_ (u"ࠬ࡬ࡲࡢ࡯ࡨࡻࡴࡸ࡫ࠨ᢯"),
  bstack1ll_opy_ (u"࠭ࡴࡦࡵࡷࡇࡴࡴࡴࡦࡺࡷࡓࡵࡺࡩࡰࡰࡶࠫᢰ"),
  bstack1ll_opy_ (u"ࠧࡵࡧࡶࡸࡔࡨࡳࡦࡴࡹࡥࡧ࡯࡬ࡪࡶࡼࠫᢱ"),
  bstack1ll_opy_ (u"ࠨࡶࡨࡷࡹࡘࡥࡱࡱࡵࡸ࡮ࡴࡧࠨᢲ"),
  bstack1ll_opy_ (u"ࠩࡦࡹࡸࡺ࡯࡮ࡘࡤࡶ࡮ࡧࡢ࡭ࡧࡶࠫᢳ"),
  bstack1ll_opy_ (u"ࠪࡧࡺࡹࡴࡰ࡯ࡗࡥ࡬࠭ᢴ"),
  bstack1ll_opy_ (u"ࠫࡦࡻࡴࡰ࡯ࡤࡸ࡮ࡵ࡮ࠨᢵ"),
  bstack1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮ࡅࡺࡺ࡯࡮ࡣࡷ࡭ࡴࡴࠧᢶ"),
  bstack1ll_opy_ (u"࠭ࡲࡦࡴࡸࡲ࡙࡫ࡳࡵࡵࠪᢷ"),
  bstack1ll_opy_ (u"ࠧࡄࡗࡖࡘࡔࡓ࡟ࡕࡃࡊࡣ࠶࠭ᢸ"),
  bstack1ll_opy_ (u"ࠨࡅࡘࡗ࡙ࡕࡍࡠࡖࡄࡋࡤ࠸ࠧᢹ"),
  bstack1ll_opy_ (u"ࠩࡆ࡙ࡘ࡚ࡏࡎࡡࡗࡅࡌࡥ࠳ࠨᢺ"),
  bstack1ll_opy_ (u"ࠪࡇ࡚࡙ࡔࡐࡏࡢࡘࡆࡍ࡟࠵ࠩᢻ"),
  bstack1ll_opy_ (u"ࠫࡈ࡛ࡓࡕࡑࡐࡣ࡙ࡇࡇࡠ࠷ࠪᢼ"),
  bstack1ll_opy_ (u"ࠬࡉࡕࡔࡖࡒࡑࡤ࡚ࡁࡈࡡ࠹ࠫᢽ"),
  bstack1ll_opy_ (u"࠭ࡃࡖࡕࡗࡓࡒࡥࡔࡂࡉࡢ࠻ࠬᢾ"),
  bstack1ll_opy_ (u"ࠧࡄࡗࡖࡘࡔࡓ࡟ࡕࡃࡊࡣ࠽࠭ᢿ"),
  bstack1ll_opy_ (u"ࠨࡅࡘࡗ࡙ࡕࡍࡠࡖࡄࡋࡤ࠿ࠧᣀ"),
  bstack1ll_opy_ (u"ࠩࡳࡩࡷࡩࡹࠨᣁ"),
  bstack1ll_opy_ (u"ࠪࡴࡪࡸࡣࡺࡑࡳࡸ࡮ࡵ࡮ࡴࠩᣂ"),
  bstack1ll_opy_ (u"ࠫࡵ࡫ࡲࡤࡻࡆࡥࡵࡺࡵࡳࡧࡐࡳࡩ࡫ࠧᣃ"),
  bstack1ll_opy_ (u"ࠬࡪࡩࡴࡣࡥࡰࡪࡇࡵࡵࡱࡆࡥࡵࡺࡵࡳࡧࡏࡳ࡬ࡹࠧᣄ"),
  bstack1ll_opy_ (u"࠭ࡴࡶࡴࡥࡳࡘࡩࡡ࡭ࡧࠪᣅ"),
  bstack1ll_opy_ (u"ࠧࡵࡷࡵࡦࡴ࡙ࡣࡢ࡮ࡨࡓࡵࡺࡩࡰࡰࡶࠫᣆ"),
  bstack1ll_opy_ (u"ࠨࡶࡨࡷࡹࡕࡲࡤࡪࡨࡷࡹࡸࡡࡵ࡫ࡲࡲࡔࡶࡴࡪࡱࡱࡷࠬᣇ"),
  bstack1ll_opy_ (u"ࠩ࡫ࡹࡧࡘࡥࡨ࡫ࡲࡲࠬᣈ")
]
bstack11l1ll11111_opy_ = [
  bstack1ll_opy_ (u"ࠪࡹࡵࡲ࡯ࡢࡦࡐࡩࡩ࡯ࡡࠨᣉ"),
  bstack1ll_opy_ (u"ࠫࡺࡹࡥࡳࡐࡤࡱࡪ࠭ᣊ"),
  bstack1ll_opy_ (u"ࠬࡧࡣࡤࡧࡶࡷࡐ࡫ࡹࠨᣋ"),
  bstack1ll_opy_ (u"࠭ࡳࡦࡵࡶ࡭ࡴࡴࡎࡢ࡯ࡨࠫᣌ"),
  bstack1ll_opy_ (u"ࠧࡵࡧࡶࡸࡕࡸࡩࡰࡴ࡬ࡸࡾ࠭ᣍ"),
  bstack1ll_opy_ (u"ࠨࡤࡸ࡭ࡱࡪࡎࡢ࡯ࡨࠫᣎ"),
  bstack1ll_opy_ (u"ࠩࡥࡹ࡮ࡲࡤࡕࡣࡪࠫᣏ"),
  bstack1ll_opy_ (u"ࠪࡴࡷࡵࡪࡦࡥࡷࡒࡦࡳࡥࠨᣐ"),
  bstack1ll_opy_ (u"ࠫࡸ࡫࡬ࡦࡰ࡬ࡹࡲ࡜ࡥࡳࡵ࡬ࡳࡳ࠭ᣑ"),
  bstack1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡔࡡ࡮ࡧࠪᣒ"),
  bstack1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡖࡦࡴࡶ࡭ࡴࡴࠧᣓ"),
  bstack1ll_opy_ (u"ࠧ࡭ࡱࡦࡥࡱ࠭ᣔ"),
  bstack1ll_opy_ (u"ࠨࡱࡶࠫᣕ"),
  bstack1ll_opy_ (u"ࠩࡲࡷ࡛࡫ࡲࡴ࡫ࡲࡲࠬᣖ"),
  bstack1ll_opy_ (u"ࠪ࡬ࡴࡹࡴࡴࠩᣗ"),
  bstack1ll_opy_ (u"ࠫࡦࡻࡴࡰ࡙ࡤ࡭ࡹ࠭ᣘ"),
  bstack1ll_opy_ (u"ࠬࡸࡥࡨ࡫ࡲࡲࠬᣙ"),
  bstack1ll_opy_ (u"࠭ࡴࡪ࡯ࡨࡾࡴࡴࡥࠨᣚ"),
  bstack1ll_opy_ (u"ࠧ࡮ࡣࡦ࡬࡮ࡴࡥࠨᣛ"),
  bstack1ll_opy_ (u"ࠨࡴࡨࡷࡴࡲࡵࡵ࡫ࡲࡲࠬᣜ"),
  bstack1ll_opy_ (u"ࠩ࡬ࡨࡱ࡫ࡔࡪ࡯ࡨࡳࡺࡺࠧᣝ"),
  bstack1ll_opy_ (u"ࠪࡨࡪࡼࡩࡤࡧࡒࡶ࡮࡫࡮ࡵࡣࡷ࡭ࡴࡴࠧᣞ"),
  bstack1ll_opy_ (u"ࠫࡻ࡯ࡤࡦࡱࠪᣟ"),
  bstack1ll_opy_ (u"ࠬࡴ࡯ࡑࡣࡪࡩࡑࡵࡡࡥࡖ࡬ࡱࡪࡵࡵࡵࠩᣠ"),
  bstack1ll_opy_ (u"࠭ࡢࡧࡥࡤࡧ࡭࡫ࠧᣡ"),
  bstack1ll_opy_ (u"ࠧࡥࡧࡥࡹ࡬࠭ᣢ"),
  bstack1ll_opy_ (u"ࠨࡥࡸࡷࡹࡵ࡭ࡔࡥࡵࡩࡪࡴࡳࡩࡱࡷࡷࠬᣣ"),
  bstack1ll_opy_ (u"ࠩࡦࡹࡸࡺ࡯࡮ࡕࡨࡲࡩࡑࡥࡺࡵࠪᣤ"),
  bstack1ll_opy_ (u"ࠪࡶࡪࡧ࡬ࡎࡱࡥ࡭ࡱ࡫ࠧᣥ"),
  bstack1ll_opy_ (u"ࠫࡳࡵࡐࡪࡲࡨࡰ࡮ࡴࡥࠨᣦ"),
  bstack1ll_opy_ (u"ࠬࡩࡨࡦࡥ࡮࡙ࡗࡒࠧᣧ"),
  bstack1ll_opy_ (u"࠭࡬ࡰࡥࡤࡰࡎࡪࡥ࡯ࡶ࡬ࡪ࡮࡫ࡲࠨᣨ"),
  bstack1ll_opy_ (u"ࠧࡢࡥࡦࡩࡵࡺࡃࡰࡱ࡮࡭ࡪࡹࠧᣩ"),
  bstack1ll_opy_ (u"ࠨࡥࡤࡴࡹࡻࡲࡦࡅࡵࡥࡸ࡮ࠧᣪ"),
  bstack1ll_opy_ (u"ࠩࡧࡩࡻ࡯ࡣࡦࡐࡤࡱࡪ࠭ᣫ"),
  bstack1ll_opy_ (u"ࠪࡥࡵࡶࡩࡶ࡯࡙ࡩࡷࡹࡩࡰࡰࠪᣬ"),
  bstack1ll_opy_ (u"ࠫࡦࡻࡴࡰ࡯ࡤࡸ࡮ࡵ࡮ࡗࡧࡵࡷ࡮ࡵ࡮ࠨᣭ"),
  bstack1ll_opy_ (u"ࠬࡴ࡯ࡃ࡮ࡤࡲࡰࡖ࡯࡭࡮࡬ࡲ࡬࠭ᣮ"),
  bstack1ll_opy_ (u"࠭࡭ࡢࡵ࡮ࡗࡪࡴࡤࡌࡧࡼࡷࠬᣯ"),
  bstack1ll_opy_ (u"ࠧࡥࡧࡹ࡭ࡨ࡫ࡌࡰࡩࡶࠫᣰ"),
  bstack1ll_opy_ (u"ࠨࡦࡨࡺ࡮ࡩࡥࡊࡦࠪᣱ"),
  bstack1ll_opy_ (u"ࠩࡧࡩࡩ࡯ࡣࡢࡶࡨࡨࡉ࡫ࡶࡪࡥࡨࠫᣲ"),
  bstack1ll_opy_ (u"ࠪ࡬ࡪࡧࡤࡦࡴࡓࡥࡷࡧ࡭ࡴࠩᣳ"),
  bstack1ll_opy_ (u"ࠫࡵ࡮࡯࡯ࡧࡑࡹࡲࡨࡥࡳࠩᣴ"),
  bstack1ll_opy_ (u"ࠬࡴࡥࡵࡹࡲࡶࡰࡒ࡯ࡨࡵࠪᣵ"),
  bstack1ll_opy_ (u"࠭࡮ࡦࡶࡺࡳࡷࡱࡌࡰࡩࡶࡓࡵࡺࡩࡰࡰࡶࠫ᣶"),
  bstack1ll_opy_ (u"ࠧࡤࡱࡱࡷࡴࡲࡥࡍࡱࡪࡷࠬ᣷"),
  bstack1ll_opy_ (u"ࠨࡷࡶࡩ࡜࠹ࡃࠨ᣸"),
  bstack1ll_opy_ (u"ࠩࡤࡴࡵ࡯ࡵ࡮ࡎࡲ࡫ࡸ࠭᣹"),
  bstack1ll_opy_ (u"ࠪࡩࡳࡧࡢ࡭ࡧࡅ࡭ࡴࡳࡥࡵࡴ࡬ࡧࠬ᣺"),
  bstack1ll_opy_ (u"ࠫࡻ࡯ࡤࡦࡱ࡙࠶ࠬ᣻"),
  bstack1ll_opy_ (u"ࠬࡳࡩࡥࡕࡨࡷࡸ࡯࡯࡯ࡋࡱࡷࡹࡧ࡬࡭ࡃࡳࡴࡸ࠭᣼"),
  bstack1ll_opy_ (u"࠭ࡥࡴࡲࡵࡩࡸࡹ࡯ࡔࡧࡵࡺࡪࡸࠧ᣽"),
  bstack1ll_opy_ (u"ࠧࡴࡧ࡯ࡩࡳ࡯ࡵ࡮ࡎࡲ࡫ࡸ࠭᣾"),
  bstack1ll_opy_ (u"ࠨࡵࡨࡰࡪࡴࡩࡶ࡯ࡆࡨࡵ࠭᣿"),
  bstack1ll_opy_ (u"ࠩࡷࡩࡱ࡫࡭ࡦࡶࡵࡽࡑࡵࡧࡴࠩᤀ"),
  bstack1ll_opy_ (u"ࠪࡷࡾࡴࡣࡕ࡫ࡰࡩ࡜࡯ࡴࡩࡐࡗࡔࠬᤁ"),
  bstack1ll_opy_ (u"ࠫ࡬࡫࡯ࡍࡱࡦࡥࡹ࡯࡯࡯ࠩᤂ"),
  bstack1ll_opy_ (u"ࠬ࡭ࡰࡴࡎࡲࡧࡦࡺࡩࡰࡰࠪᤃ"),
  bstack1ll_opy_ (u"࠭࡮ࡦࡶࡺࡳࡷࡱࡐࡳࡱࡩ࡭ࡱ࡫ࠧᤄ"),
  bstack1ll_opy_ (u"ࠧࡤࡷࡶࡸࡴࡳࡎࡦࡶࡺࡳࡷࡱࠧᤅ"),
  bstack1ll_opy_ (u"ࠨࡨࡲࡶࡨ࡫ࡃࡩࡣࡱ࡫ࡪࡐࡡࡳࠩᤆ"),
  bstack1ll_opy_ (u"ࠩࡻࡱࡸࡐࡡࡳࠩᤇ"),
  bstack1ll_opy_ (u"ࠪࡼࡲࡾࡊࡢࡴࠪᤈ"),
  bstack1ll_opy_ (u"ࠫࡲࡧࡳ࡬ࡅࡲࡱࡲࡧ࡮ࡥࡵࠪᤉ"),
  bstack1ll_opy_ (u"ࠬࡳࡡࡴ࡭ࡅࡥࡸ࡯ࡣࡂࡷࡷ࡬ࠬᤊ"),
  bstack1ll_opy_ (u"࠭ࡷࡴࡎࡲࡧࡦࡲࡓࡶࡲࡳࡳࡷࡺࠧᤋ"),
  bstack1ll_opy_ (u"ࠧࡥ࡫ࡶࡥࡧࡲࡥࡄࡱࡵࡷࡗ࡫ࡳࡵࡴ࡬ࡧࡹ࡯࡯࡯ࡵࠪᤌ"),
  bstack1ll_opy_ (u"ࠨࡣࡳࡴ࡛࡫ࡲࡴ࡫ࡲࡲࠬᤍ"),
  bstack1ll_opy_ (u"ࠩࡤࡧࡨ࡫ࡰࡵࡋࡱࡷࡪࡩࡵࡳࡧࡆࡩࡷࡺࡳࠨᤎ"),
  bstack1ll_opy_ (u"ࠪࡶࡪࡹࡩࡨࡰࡄࡴࡵ࠭ᤏ"),
  bstack1ll_opy_ (u"ࠫࡩ࡯ࡳࡢࡤ࡯ࡩࡆࡴࡩ࡮ࡣࡷ࡭ࡴࡴࡳࠨᤐ"),
  bstack1ll_opy_ (u"ࠬࡩࡡ࡯ࡣࡵࡽࠬᤑ"),
  bstack1ll_opy_ (u"࠭ࡦࡪࡴࡨࡪࡴࡾࠧᤒ"),
  bstack1ll_opy_ (u"ࠧࡤࡪࡵࡳࡲ࡫ࠧᤓ"),
  bstack1ll_opy_ (u"ࠨ࡫ࡨࠫᤔ"),
  bstack1ll_opy_ (u"ࠩࡨࡨ࡬࡫ࠧᤕ"),
  bstack1ll_opy_ (u"ࠪࡷࡦ࡬ࡡࡳ࡫ࠪᤖ"),
  bstack1ll_opy_ (u"ࠫࡶࡻࡥࡶࡧࠪᤗ"),
  bstack1ll_opy_ (u"ࠬ࡯࡮ࡵࡧࡵࡲࡦࡲࠧᤘ"),
  bstack1ll_opy_ (u"࠭ࡡࡱࡲࡖࡸࡴࡸࡥࡄࡱࡱࡪ࡮࡭ࡵࡳࡣࡷ࡭ࡴࡴࠧᤙ"),
  bstack1ll_opy_ (u"ࠧࡦࡰࡤࡦࡱ࡫ࡃࡢ࡯ࡨࡶࡦࡏ࡭ࡢࡩࡨࡍࡳࡰࡥࡤࡶ࡬ࡳࡳ࠭ᤚ"),
  bstack1ll_opy_ (u"ࠨࡰࡨࡸࡼࡵࡲ࡬ࡎࡲ࡫ࡸࡋࡸࡤ࡮ࡸࡨࡪࡎ࡯ࡴࡶࡶࠫᤛ"),
  bstack1ll_opy_ (u"ࠩࡱࡩࡹࡽ࡯ࡳ࡭ࡏࡳ࡬ࡹࡉ࡯ࡥ࡯ࡹࡩ࡫ࡈࡰࡵࡷࡷࠬᤜ"),
  bstack1ll_opy_ (u"ࠪࡹࡵࡪࡡࡵࡧࡄࡴࡵ࡙ࡥࡵࡶ࡬ࡲ࡬ࡹࠧᤝ"),
  bstack1ll_opy_ (u"ࠫࡷ࡫ࡳࡦࡴࡹࡩࡉ࡫ࡶࡪࡥࡨࠫᤞ"),
  bstack1ll_opy_ (u"ࠬࡹ࡯ࡶࡴࡦࡩࠬ᤟"),
  bstack1ll_opy_ (u"࠭ࡳࡦࡰࡧࡏࡪࡿࡳࠨᤠ"),
  bstack1ll_opy_ (u"ࠧࡦࡰࡤࡦࡱ࡫ࡐࡢࡵࡶࡧࡴࡪࡥࠨᤡ"),
  bstack1ll_opy_ (u"ࠨࡷࡳࡨࡦࡺࡥࡊࡱࡶࡈࡪࡼࡩࡤࡧࡖࡩࡹࡺࡩ࡯ࡩࡶࠫᤢ"),
  bstack1ll_opy_ (u"ࠩࡨࡲࡦࡨ࡬ࡦࡃࡸࡨ࡮ࡵࡉ࡯࡬ࡨࡧࡹ࡯࡯࡯ࠩᤣ"),
  bstack1ll_opy_ (u"ࠪࡩࡳࡧࡢ࡭ࡧࡄࡴࡵࡲࡥࡑࡣࡼࠫᤤ"),
  bstack1ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࠬᤥ"),
  bstack1ll_opy_ (u"ࠬࡽࡤࡪࡱࡖࡩࡷࡼࡩࡤࡧࠪᤦ"),
  bstack1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯ࡘࡊࡋࠨᤧ"),
  bstack1ll_opy_ (u"ࠧࡱࡴࡨࡺࡪࡴࡴࡄࡴࡲࡷࡸ࡙ࡩࡵࡧࡗࡶࡦࡩ࡫ࡪࡰࡪࠫᤨ"),
  bstack1ll_opy_ (u"ࠨࡪ࡬࡫࡭ࡉ࡯࡯ࡶࡵࡥࡸࡺࠧᤩ"),
  bstack1ll_opy_ (u"ࠩࡧࡩࡻ࡯ࡣࡦࡒࡵࡩ࡫࡫ࡲࡦࡰࡦࡩࡸ࠭ᤪ"),
  bstack1ll_opy_ (u"ࠪࡩࡳࡧࡢ࡭ࡧࡖ࡭ࡲ࠭ᤫ"),
  bstack1ll_opy_ (u"ࠫࡸ࡯࡭ࡐࡲࡷ࡭ࡴࡴࡳࠨ᤬"),
  bstack1ll_opy_ (u"ࠬࡸࡥ࡮ࡱࡹࡩࡎࡕࡓࡂࡲࡳࡗࡪࡺࡴࡪࡰࡪࡷࡑࡵࡣࡢ࡮࡬ࡾࡦࡺࡩࡰࡰࠪ᤭"),
  bstack1ll_opy_ (u"࠭ࡨࡰࡵࡷࡒࡦࡳࡥࠨ᤮"),
  bstack1ll_opy_ (u"ࠧࡣࡷ࡬ࡰࡩࡏࡤࡦࡰࡷ࡭࡫࡯ࡥࡳࠩ᤯"),
  bstack1ll_opy_ (u"ࠨࡲ࡯ࡥࡹ࡬࡯ࡳ࡯ࠪᤰ"),
  bstack1ll_opy_ (u"ࠩࡳࡰࡦࡺࡦࡰࡴࡰࡒࡦࡳࡥࠨᤱ"),
  bstack1ll_opy_ (u"ࠪࡴࡱࡧࡴࡧࡱࡵࡱ࡛࡫ࡲࡴ࡫ࡲࡲࠬᤲ"),
  bstack1ll_opy_ (u"ࠫࡵࡧࡧࡦࡎࡲࡥࡩ࡙ࡴࡳࡣࡷࡩ࡬ࡿࠧᤳ"),
  bstack1ll_opy_ (u"ࠬࡶࡲࡰࡺࡼࠫᤴ"),
  bstack1ll_opy_ (u"࠭ࡴࡪ࡯ࡨࡳࡺࡺࡳࠨᤵ"),
  bstack1ll_opy_ (u"ࠧࡶࡰ࡫ࡥࡳࡪ࡬ࡦࡦࡓࡶࡴࡳࡰࡵࡄࡨ࡬ࡦࡼࡩࡰࡴࠪᤶ")
]
bstack11l11l111_opy_ = {
  bstack1ll_opy_ (u"ࠨࡸࠪᤷ"): bstack1ll_opy_ (u"ࠩࡹࠫᤸ"),
  bstack1ll_opy_ (u"ࠪࡪ᤹ࠬ"): bstack1ll_opy_ (u"ࠫ࡫࠭᤺"),
  bstack1ll_opy_ (u"ࠬ࡬࡯ࡳࡥࡨ᤻ࠫ"): bstack1ll_opy_ (u"࠭ࡦࡰࡴࡦࡩࠬ᤼"),
  bstack1ll_opy_ (u"ࠧࡰࡰ࡯ࡽࡦࡻࡴࡰ࡯ࡤࡸࡪ࠭᤽"): bstack1ll_opy_ (u"ࠨࡱࡱࡰࡾࡇࡵࡵࡱࡰࡥࡹ࡫ࠧ᤾"),
  bstack1ll_opy_ (u"ࠩࡩࡳࡷࡩࡥ࡭ࡱࡦࡥࡱ࠭᤿"): bstack1ll_opy_ (u"ࠪࡪࡴࡸࡣࡦ࡮ࡲࡧࡦࡲࠧ᥀"),
  bstack1ll_opy_ (u"ࠫࡵࡸ࡯ࡹࡻ࡫ࡳࡸࡺࠧ᥁"): bstack1ll_opy_ (u"ࠬࡶࡲࡰࡺࡼࡌࡴࡹࡴࠨ᥂"),
  bstack1ll_opy_ (u"࠭ࡰࡳࡱࡻࡽࡵࡵࡲࡵࠩ᥃"): bstack1ll_opy_ (u"ࠧࡱࡴࡲࡼࡾࡖ࡯ࡳࡶࠪ᥄"),
  bstack1ll_opy_ (u"ࠨࡲࡵࡳࡽࡿࡵࡴࡧࡵࠫ᥅"): bstack1ll_opy_ (u"ࠩࡳࡶࡴࡾࡹࡖࡵࡨࡶࠬ᥆"),
  bstack1ll_opy_ (u"ࠪࡴࡷࡵࡸࡺࡲࡤࡷࡸ࠭᥇"): bstack1ll_opy_ (u"ࠫࡵࡸ࡯ࡹࡻࡓࡥࡸࡹࠧ᥈"),
  bstack1ll_opy_ (u"ࠬࡲ࡯ࡤࡣ࡯ࡴࡷࡵࡸࡺࡪࡲࡷࡹ࠭᥉"): bstack1ll_opy_ (u"࠭࡬ࡰࡥࡤࡰࡕࡸ࡯ࡹࡻࡋࡳࡸࡺࠧ᥊"),
  bstack1ll_opy_ (u"ࠧ࡭ࡱࡦࡥࡱࡶࡲࡰࡺࡼࡴࡴࡸࡴࠨ᥋"): bstack1ll_opy_ (u"ࠨ࡮ࡲࡧࡦࡲࡐࡳࡱࡻࡽࡕࡵࡲࡵࠩ᥌"),
  bstack1ll_opy_ (u"ࠩ࡯ࡳࡨࡧ࡬ࡱࡴࡲࡼࡾࡻࡳࡦࡴࠪ᥍"): bstack1ll_opy_ (u"ࠪ࠱ࡱࡵࡣࡢ࡮ࡓࡶࡴࡾࡹࡖࡵࡨࡶࠬ᥎"),
  bstack1ll_opy_ (u"ࠫ࠲ࡲ࡯ࡤࡣ࡯ࡴࡷࡵࡸࡺࡷࡶࡩࡷ࠭᥏"): bstack1ll_opy_ (u"ࠬ࠳࡬ࡰࡥࡤࡰࡕࡸ࡯ࡹࡻࡘࡷࡪࡸࠧᥐ"),
  bstack1ll_opy_ (u"࠭࡬ࡰࡥࡤࡰࡵࡸ࡯ࡹࡻࡳࡥࡸࡹࠧᥑ"): bstack1ll_opy_ (u"ࠧ࠮࡮ࡲࡧࡦࡲࡐࡳࡱࡻࡽࡕࡧࡳࡴࠩᥒ"),
  bstack1ll_opy_ (u"ࠨ࠯࡯ࡳࡨࡧ࡬ࡱࡴࡲࡼࡾࡶࡡࡴࡵࠪᥓ"): bstack1ll_opy_ (u"ࠩ࠰ࡰࡴࡩࡡ࡭ࡒࡵࡳࡽࡿࡐࡢࡵࡶࠫᥔ"),
  bstack1ll_opy_ (u"ࠪࡦ࡮ࡴࡡࡳࡻࡳࡥࡹ࡮ࠧᥕ"): bstack1ll_opy_ (u"ࠫࡧ࡯࡮ࡢࡴࡼࡴࡦࡺࡨࠨᥖ"),
  bstack1ll_opy_ (u"ࠬࡶࡡࡤࡨ࡬ࡰࡪ࠭ᥗ"): bstack1ll_opy_ (u"࠭࠭ࡱࡣࡦ࠱࡫࡯࡬ࡦࠩᥘ"),
  bstack1ll_opy_ (u"ࠧࡱࡣࡦ࠱࡫࡯࡬ࡦࠩᥙ"): bstack1ll_opy_ (u"ࠨ࠯ࡳࡥࡨ࠳ࡦࡪ࡮ࡨࠫᥚ"),
  bstack1ll_opy_ (u"ࠩ࠰ࡴࡦࡩ࠭ࡧ࡫࡯ࡩࠬᥛ"): bstack1ll_opy_ (u"ࠪ࠱ࡵࡧࡣ࠮ࡨ࡬ࡰࡪ࠭ᥜ"),
  bstack1ll_opy_ (u"ࠫࡱࡵࡧࡧ࡫࡯ࡩࠬᥝ"): bstack1ll_opy_ (u"ࠬࡲ࡯ࡨࡨ࡬ࡰࡪ࠭ᥞ"),
  bstack1ll_opy_ (u"࠭࡬ࡰࡥࡤࡰ࡮ࡪࡥ࡯ࡶ࡬ࡪ࡮࡫ࡲࠨᥟ"): bstack1ll_opy_ (u"ࠧ࡭ࡱࡦࡥࡱࡏࡤࡦࡰࡷ࡭࡫࡯ࡥࡳࠩᥠ"),
  bstack1ll_opy_ (u"ࠨࡥࡸࡷࡹࡵ࡭࠮ࡴࡨࡴࡪࡧࡴࡦࡴࠪᥡ"): bstack1ll_opy_ (u"ࠩࡦࡹࡸࡺ࡯࡮ࡔࡨࡴࡪࡧࡴࡦࡴࠪᥢ")
}
bstack11l11lll1ll_opy_ = bstack1ll_opy_ (u"ࠥ࡬ࡹࡺࡰࡴ࠼࠲࠳࡬࡯ࡴࡩࡷࡥ࠲ࡨࡵ࡭࠰ࡲࡨࡶࡨࡿ࠯ࡤ࡮࡬࠳ࡷ࡫࡬ࡦࡣࡶࡩࡸ࠵࡬ࡢࡶࡨࡷࡹ࠵ࡤࡰࡹࡱࡰࡴࡧࡤࠣᥣ")
bstack11l1l11l1ll_opy_ = bstack1ll_opy_ (u"ࠦ࠴ࡶࡥࡳࡥࡼ࠳࡭࡫ࡡ࡭ࡶ࡫ࡧ࡭࡫ࡣ࡬ࠤᥤ")
bstack11l11l11l_opy_ = bstack1ll_opy_ (u"ࠧ࡮ࡴࡵࡲࡶ࠾࠴࠵ࡥࡥࡵ࠱ࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬࠰ࡦࡳࡲ࠵ࡳࡦࡰࡧࡣࡸࡪ࡫ࡠࡧࡹࡩࡳࡺࡳࠣᥥ")
bstack1lll111l11_opy_ = bstack1ll_opy_ (u"࠭ࡨࡵࡶࡳࡷ࠿࠵࠯ࡩࡷࡥ࠲ࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭࠱ࡧࡴࡳ࠯ࡸࡦ࠲࡬ࡺࡨࠧᥦ")
bstack1l11lll11_opy_ = bstack1ll_opy_ (u"ࠧࡩࡶࡷࡴ࠿࠵࠯ࡩࡷࡥ࠲ࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭࠱ࡧࡴࡳ࠺࠹࠲࠲ࡻࡩ࠵ࡨࡶࡤࠪᥧ")
bstack1l11ll111_opy_ = bstack1ll_opy_ (u"ࠨࡪࡷࡸࡵࡹ࠺࠰࠱࡫ࡹࡧ࠴ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯࠳ࡩ࡯࡮࠱ࡱࡩࡽࡺ࡟ࡩࡷࡥࡷࠬᥨ")
bstack11lll1lll1_opy_ = {
  bstack1ll_opy_ (u"ࠩࡧࡩ࡫ࡧࡵ࡭ࡶࠪᥩ"): bstack1ll_opy_ (u"ࠪ࡬ࡺࡨ࠮ࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰ࠴ࡣࡰ࡯ࠪᥪ"),
  bstack1ll_opy_ (u"ࠫࡺࡹ࠭ࡦࡣࡶࡸࠬᥫ"): bstack1ll_opy_ (u"ࠬ࡮ࡵࡣ࠯ࡸࡷࡪ࠳࡯࡯࡮ࡼ࠲ࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭࠱ࡧࡴࡳࠧᥬ"),
  bstack1ll_opy_ (u"࠭ࡵࡴࠩᥭ"): bstack1ll_opy_ (u"ࠧࡩࡷࡥ࠱ࡺࡹ࠭ࡰࡰ࡯ࡽ࠳ࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮࠲ࡨࡵ࡭ࠨ᥮"),
  bstack1ll_opy_ (u"ࠨࡧࡸࠫ᥯"): bstack1ll_opy_ (u"ࠩ࡫ࡹࡧ࠳ࡥࡶ࠯ࡲࡲࡱࡿ࠮ࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰ࠴ࡣࡰ࡯ࠪᥰ"),
  bstack1ll_opy_ (u"ࠪ࡭ࡳ࠭ᥱ"): bstack1ll_opy_ (u"ࠫ࡭ࡻࡢ࠮ࡣࡳࡷ࠲ࡵ࡮࡭ࡻ࠱ࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬࠰ࡦࡳࡲ࠭ᥲ"),
  bstack1ll_opy_ (u"ࠬࡧࡵࠨᥳ"): bstack1ll_opy_ (u"࠭ࡨࡶࡤ࠰ࡥࡵࡹࡥ࠮ࡱࡱࡰࡾ࠴ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯࠳ࡩ࡯࡮ࠩᥴ")
}
bstack11l1l111111_opy_ = {
  bstack1ll_opy_ (u"ࠧࡤࡴ࡬ࡸ࡮ࡩࡡ࡭ࠩ᥵"): 50,
  bstack1ll_opy_ (u"ࠨࡧࡵࡶࡴࡸࠧ᥶"): 40,
  bstack1ll_opy_ (u"ࠩࡺࡥࡷࡴࡩ࡯ࡩࠪ᥷"): 30,
  bstack1ll_opy_ (u"ࠪ࡭ࡳ࡬࡯ࠨ᥸"): 20,
  bstack1ll_opy_ (u"ࠫࡩ࡫ࡢࡶࡩࠪ᥹"): 10
}
bstack11ll11l1ll_opy_ = bstack11l1l111111_opy_[bstack1ll_opy_ (u"ࠬ࡯࡮ࡧࡱࠪ᥺")]
bstack111lll1ll1_opy_ = bstack1ll_opy_ (u"࠭ࡰࡺࡶ࡫ࡳࡳ࠳ࡰࡺࡶ࡫ࡳࡳࡧࡧࡦࡰࡷ࠳ࠬ᥻")
bstack1l11l1l11l_opy_ = bstack1ll_opy_ (u"ࠧࡳࡱࡥࡳࡹ࠳ࡰࡺࡶ࡫ࡳࡳࡧࡧࡦࡰࡷ࠳ࠬ᥼")
bstack1ll111l11l_opy_ = bstack1ll_opy_ (u"ࠨࡤࡨ࡬ࡦࡼࡥ࠮ࡲࡼࡸ࡭ࡵ࡮ࡢࡩࡨࡲࡹ࠵ࠧ᥽")
bstack1l1ll11lll_opy_ = bstack1ll_opy_ (u"ࠩࡳࡽࡹ࡫ࡳࡵ࠯ࡳࡽࡹ࡮࡯࡯ࡣࡪࡩࡳࡺ࠯ࠨ᥾")
bstack1111ll11_opy_ = bstack1ll_opy_ (u"ࠪࡔࡱ࡫ࡡࡴࡧࠣ࡭ࡳࡹࡴࡢ࡮࡯ࠤࡵࡿࡴࡦࡵࡷࠤࡦࡴࡤࠡࡲࡼࡸࡪࡹࡴ࠮ࡵࡨࡰࡪࡴࡩࡶ࡯ࠣࡴࡦࡩ࡫ࡢࡩࡨࡷ࠳ࠦࡠࡱ࡫ࡳࠤ࡮ࡴࡳࡵࡣ࡯ࡰࠥࡶࡹࡵࡧࡶࡸࠥࡶࡹࡵࡧࡶࡸ࠲ࡹࡥ࡭ࡧࡱ࡭ࡺࡳࡠࠨ᥿")
bstack1ll11l11ll_opy_ = {
  bstack1ll_opy_ (u"ࠫࡘࡊࡋ࠮ࡉࡈࡒ࠲࠶࠰࠶ࠩᦀ"): bstack1ll_opy_ (u"ࠬ࠰ࠪࠫࠢ࡞ࡗࡉࡑ࠭ࡈࡇࡑ࠱࠵࠶࠵࡞ࠢࡣࡴࡾࡺࡥࡴࡶ࠰ࡴࡦࡸࡡ࡭࡮ࡨࡰࡥࠦࡩࡴࠢ࡬ࡲࡸࡺࡡ࡭࡮ࡨࡨࠥ࡯࡮ࠡࡻࡲࡹࡷࠦࡥ࡯ࡸ࡬ࡶࡴࡴ࡭ࡦࡰࡷ࠲࡚ࠥࡨࡪࡵࠣࡱࡦࡿࠠࡤࡣࡸࡷࡪࠦࡣࡰࡰࡩࡰ࡮ࡩࡴࡴࠢࡺ࡭ࡹ࡮ࠠࡃࡴࡲࡻࡸ࡫ࡲࡔࡶࡤࡧࡰࠦࡓࡅࡍ࠱ࠤࡕࡲࡥࡢࡵࡨࠤࡺࡴࡩ࡯ࡵࡷࡥࡱࡲࠠࡪࡶࠣࡹࡸ࡯࡮ࡨ࠼ࠣࡴ࡮ࡶࠠࡶࡰ࡬ࡲࡸࡺࡡ࡭࡮ࠣࡴࡾࡺࡥࡴࡶ࠰ࡴࡦࡸࡡ࡭࡮ࡨࡰࠥ࠰ࠪࠫࠩᦁ")
}
bstack11l1l1111ll_opy_ = [bstack1ll_opy_ (u"࠭ࡂࡓࡑ࡚ࡗࡊࡘࡓࡕࡃࡆࡏࡤ࡛ࡓࡆࡔࡑࡅࡒࡋࠧᦂ"), bstack1ll_opy_ (u"࡚ࠧࡑࡘࡖࡤ࡛ࡓࡆࡔࡑࡅࡒࡋࠧᦃ")]
bstack11l1l1ll11l_opy_ = [bstack1ll_opy_ (u"ࠨࡄࡕࡓ࡜࡙ࡅࡓࡕࡗࡅࡈࡑ࡟ࡂࡅࡆࡉࡘ࡙࡟ࡌࡇ࡜ࠫᦄ"), bstack1ll_opy_ (u"ࠩ࡜ࡓ࡚ࡘ࡟ࡂࡅࡆࡉࡘ࡙࡟ࡌࡇ࡜ࠫᦅ")]
bstack11lllll1l_opy_ = re.compile(bstack1ll_opy_ (u"ࠪࡢࡠࡢ࡜ࡸ࠯ࡠ࠯࠿࠴ࠪࠥࠩᦆ"))
bstack1l111l1l1_opy_ = [
  bstack1ll_opy_ (u"ࠫࡦࡻࡴࡰ࡯ࡤࡸ࡮ࡵ࡮ࡏࡣࡰࡩࠬᦇ"),
  bstack1ll_opy_ (u"ࠬࡶ࡬ࡢࡶࡩࡳࡷࡳࡖࡦࡴࡶ࡭ࡴࡴࠧᦈ"),
  bstack1ll_opy_ (u"࠭ࡤࡦࡸ࡬ࡧࡪࡔࡡ࡮ࡧࠪᦉ"),
  bstack1ll_opy_ (u"ࠧ࡯ࡧࡺࡇࡴࡳ࡭ࡢࡰࡧࡘ࡮ࡳࡥࡰࡷࡷࠫᦊ"),
  bstack1ll_opy_ (u"ࠨࡣࡳࡴࠬᦋ"),
  bstack1ll_opy_ (u"ࠩࡸࡨ࡮ࡪࠧᦌ"),
  bstack1ll_opy_ (u"ࠪࡰࡦࡴࡧࡶࡣࡪࡩࠬᦍ"),
  bstack1ll_opy_ (u"ࠫࡱࡵࡣࡢ࡮ࡨࠫᦎ"),
  bstack1ll_opy_ (u"ࠬࡵࡲࡪࡧࡱࡸࡦࡺࡩࡰࡰࠪᦏ"),
  bstack1ll_opy_ (u"࠭ࡡࡶࡶࡲ࡛ࡪࡨࡶࡪࡧࡺࠫᦐ"),
  bstack1ll_opy_ (u"ࠧ࡯ࡱࡕࡩࡸ࡫ࡴࠨᦑ"), bstack1ll_opy_ (u"ࠨࡨࡸࡰࡱࡘࡥࡴࡧࡷࠫᦒ"),
  bstack1ll_opy_ (u"ࠩࡦࡰࡪࡧࡲࡔࡻࡶࡸࡪࡳࡆࡪ࡮ࡨࡷࠬᦓ"),
  bstack1ll_opy_ (u"ࠪࡩࡻ࡫࡮ࡵࡖ࡬ࡱ࡮ࡴࡧࡴࠩᦔ"),
  bstack1ll_opy_ (u"ࠫࡪࡴࡡࡣ࡮ࡨࡔࡪࡸࡦࡰࡴࡰࡥࡳࡩࡥࡍࡱࡪ࡫࡮ࡴࡧࠨᦕ"),
  bstack1ll_opy_ (u"ࠬࡵࡴࡩࡧࡵࡅࡵࡶࡳࠨᦖ"),
  bstack1ll_opy_ (u"࠭ࡰࡳ࡫ࡱࡸࡕࡧࡧࡦࡕࡲࡹࡷࡩࡥࡐࡰࡉ࡭ࡳࡪࡆࡢ࡫࡯ࡹࡷ࡫ࠧᦗ"),
  bstack1ll_opy_ (u"ࠧࡢࡲࡳࡅࡨࡺࡩࡷ࡫ࡷࡽࠬᦘ"), bstack1ll_opy_ (u"ࠨࡣࡳࡴࡕࡧࡣ࡬ࡣࡪࡩࠬᦙ"), bstack1ll_opy_ (u"ࠩࡤࡴࡵ࡝ࡡࡪࡶࡄࡧࡹ࡯ࡶࡪࡶࡼࠫᦚ"), bstack1ll_opy_ (u"ࠪࡥࡵࡶࡗࡢ࡫ࡷࡔࡦࡩ࡫ࡢࡩࡨࠫᦛ"), bstack1ll_opy_ (u"ࠫࡦࡶࡰࡘࡣ࡬ࡸࡉࡻࡲࡢࡶ࡬ࡳࡳ࠭ᦜ"),
  bstack1ll_opy_ (u"ࠬࡪࡥࡷ࡫ࡦࡩࡗ࡫ࡡࡥࡻࡗ࡭ࡲ࡫࡯ࡶࡶࠪᦝ"),
  bstack1ll_opy_ (u"࠭ࡡ࡭࡮ࡲࡻ࡙࡫ࡳࡵࡒࡤࡧࡰࡧࡧࡦࡵࠪᦞ"),
  bstack1ll_opy_ (u"ࠧࡢࡰࡧࡶࡴ࡯ࡤࡄࡱࡹࡩࡷࡧࡧࡦࠩᦟ"), bstack1ll_opy_ (u"ࠨࡣࡱࡨࡷࡵࡩࡥࡅࡲࡺࡪࡸࡡࡨࡧࡈࡲࡩࡏ࡮ࡵࡧࡱࡸࠬᦠ"),
  bstack1ll_opy_ (u"ࠩࡤࡲࡩࡸ࡯ࡪࡦࡇࡩࡻ࡯ࡣࡦࡔࡨࡥࡩࡿࡔࡪ࡯ࡨࡳࡺࡺࠧᦡ"),
  bstack1ll_opy_ (u"ࠪࡥࡩࡨࡐࡰࡴࡷࠫᦢ"),
  bstack1ll_opy_ (u"ࠫࡦࡴࡤࡳࡱ࡬ࡨࡉ࡫ࡶࡪࡥࡨࡗࡴࡩ࡫ࡦࡶࠪᦣ"),
  bstack1ll_opy_ (u"ࠬࡧ࡮ࡥࡴࡲ࡭ࡩࡏ࡮ࡴࡶࡤࡰࡱ࡚ࡩ࡮ࡧࡲࡹࡹ࠭ᦤ"),
  bstack1ll_opy_ (u"࠭ࡡ࡯ࡦࡵࡳ࡮ࡪࡉ࡯ࡵࡷࡥࡱࡲࡐࡢࡶ࡫ࠫᦥ"),
  bstack1ll_opy_ (u"ࠧࡢࡸࡧࠫᦦ"), bstack1ll_opy_ (u"ࠨࡣࡹࡨࡑࡧࡵ࡯ࡥ࡫ࡘ࡮ࡳࡥࡰࡷࡷࠫᦧ"), bstack1ll_opy_ (u"ࠩࡤࡺࡩࡘࡥࡢࡦࡼࡘ࡮ࡳࡥࡰࡷࡷࠫᦨ"), bstack1ll_opy_ (u"ࠪࡥࡻࡪࡁࡳࡩࡶࠫᦩ"),
  bstack1ll_opy_ (u"ࠫࡺࡹࡥࡌࡧࡼࡷࡹࡵࡲࡦࠩᦪ"), bstack1ll_opy_ (u"ࠬࡱࡥࡺࡵࡷࡳࡷ࡫ࡐࡢࡶ࡫ࠫᦫ"), bstack1ll_opy_ (u"࠭࡫ࡦࡻࡶࡸࡴࡸࡥࡑࡣࡶࡷࡼࡵࡲࡥࠩ᦬"),
  bstack1ll_opy_ (u"ࠧ࡬ࡧࡼࡅࡱ࡯ࡡࡴࠩ᦭"), bstack1ll_opy_ (u"ࠨ࡭ࡨࡽࡕࡧࡳࡴࡹࡲࡶࡩ࠭᦮"),
  bstack1ll_opy_ (u"ࠩࡦ࡬ࡷࡵ࡭ࡦࡦࡵ࡭ࡻ࡫ࡲࡆࡺࡨࡧࡺࡺࡡࡣ࡮ࡨࠫ᦯"), bstack1ll_opy_ (u"ࠪࡧ࡭ࡸ࡯࡮ࡧࡧࡶ࡮ࡼࡥࡳࡃࡵ࡫ࡸ࠭ᦰ"), bstack1ll_opy_ (u"ࠫࡨ࡮ࡲࡰ࡯ࡨࡨࡷ࡯ࡶࡦࡴࡈࡼࡪࡩࡵࡵࡣࡥࡰࡪࡊࡩࡳࠩᦱ"), bstack1ll_opy_ (u"ࠬࡩࡨࡳࡱࡰࡩࡩࡸࡩࡷࡧࡵࡇ࡭ࡸ࡯࡮ࡧࡐࡥࡵࡶࡩ࡯ࡩࡉ࡭ࡱ࡫ࠧᦲ"), bstack1ll_opy_ (u"࠭ࡣࡩࡴࡲࡱࡪࡪࡲࡪࡸࡨࡶ࡚ࡹࡥࡔࡻࡶࡸࡪࡳࡅࡹࡧࡦࡹࡹࡧࡢ࡭ࡧࠪᦳ"),
  bstack1ll_opy_ (u"ࠧࡤࡪࡵࡳࡲ࡫ࡤࡳ࡫ࡹࡩࡷࡖ࡯ࡳࡶࠪᦴ"), bstack1ll_opy_ (u"ࠨࡥ࡫ࡶࡴࡳࡥࡥࡴ࡬ࡺࡪࡸࡐࡰࡴࡷࡷࠬᦵ"),
  bstack1ll_opy_ (u"ࠩࡦ࡬ࡷࡵ࡭ࡦࡦࡵ࡭ࡻ࡫ࡲࡅ࡫ࡶࡥࡧࡲࡥࡃࡷ࡬ࡰࡩࡉࡨࡦࡥ࡮ࠫᦶ"),
  bstack1ll_opy_ (u"ࠪࡥࡺࡺ࡯ࡘࡧࡥࡺ࡮࡫ࡷࡕ࡫ࡰࡩࡴࡻࡴࠨᦷ"),
  bstack1ll_opy_ (u"ࠫ࡮ࡴࡴࡦࡰࡷࡅࡨࡺࡩࡰࡰࠪᦸ"), bstack1ll_opy_ (u"ࠬ࡯࡮ࡵࡧࡱࡸࡈࡧࡴࡦࡩࡲࡶࡾ࠭ᦹ"), bstack1ll_opy_ (u"࠭ࡩ࡯ࡶࡨࡲࡹࡌ࡬ࡢࡩࡶࠫᦺ"), bstack1ll_opy_ (u"ࠧࡰࡲࡷ࡭ࡴࡴࡡ࡭ࡋࡱࡸࡪࡴࡴࡂࡴࡪࡹࡲ࡫࡮ࡵࡵࠪᦻ"),
  bstack1ll_opy_ (u"ࠨࡦࡲࡲࡹ࡙ࡴࡰࡲࡄࡴࡵࡕ࡮ࡓࡧࡶࡩࡹ࠭ᦼ"),
  bstack1ll_opy_ (u"ࠩࡸࡲ࡮ࡩ࡯ࡥࡧࡎࡩࡾࡨ࡯ࡢࡴࡧࠫᦽ"), bstack1ll_opy_ (u"ࠪࡶࡪࡹࡥࡵࡍࡨࡽࡧࡵࡡࡳࡦࠪᦾ"),
  bstack1ll_opy_ (u"ࠫࡳࡵࡓࡪࡩࡱࠫᦿ"),
  bstack1ll_opy_ (u"ࠬ࡯ࡧ࡯ࡱࡵࡩ࡚ࡴࡩ࡮ࡲࡲࡶࡹࡧ࡮ࡵࡘ࡬ࡩࡼࡹࠧᧀ"),
  bstack1ll_opy_ (u"࠭ࡤࡪࡵࡤࡦࡱ࡫ࡁ࡯ࡦࡵࡳ࡮ࡪࡗࡢࡶࡦ࡬ࡪࡸࡳࠨᧁ"),
  bstack1ll_opy_ (u"ࠧࡤࡪࡵࡳࡲ࡫ࡏࡱࡶ࡬ࡳࡳࡹࠧᧂ"),
  bstack1ll_opy_ (u"ࠨࡴࡨࡧࡷ࡫ࡡࡵࡧࡆ࡬ࡷࡵ࡭ࡦࡆࡵ࡭ࡻ࡫ࡲࡔࡧࡶࡷ࡮ࡵ࡮ࡴࠩᧃ"),
  bstack1ll_opy_ (u"ࠩࡱࡥࡹ࡯ࡶࡦ࡙ࡨࡦࡘࡩࡲࡦࡧࡱࡷ࡭ࡵࡴࠨᧄ"),
  bstack1ll_opy_ (u"ࠪࡥࡳࡪࡲࡰ࡫ࡧࡗࡨࡸࡥࡦࡰࡶ࡬ࡴࡺࡐࡢࡶ࡫ࠫᧅ"),
  bstack1ll_opy_ (u"ࠫࡳ࡫ࡴࡸࡱࡵ࡯ࡘࡶࡥࡦࡦࠪᧆ"),
  bstack1ll_opy_ (u"ࠬ࡭ࡰࡴࡇࡱࡥࡧࡲࡥࡥࠩᧇ"),
  bstack1ll_opy_ (u"࠭ࡩࡴࡊࡨࡥࡩࡲࡥࡴࡵࠪᧈ"),
  bstack1ll_opy_ (u"ࠧࡢࡦࡥࡉࡽ࡫ࡣࡕ࡫ࡰࡩࡴࡻࡴࠨᧉ"),
  bstack1ll_opy_ (u"ࠨ࡮ࡲࡧࡦࡲࡥࡔࡥࡵ࡭ࡵࡺࠧ᧊"),
  bstack1ll_opy_ (u"ࠩࡶ࡯࡮ࡶࡄࡦࡸ࡬ࡧࡪࡏ࡮ࡪࡶ࡬ࡥࡱ࡯ࡺࡢࡶ࡬ࡳࡳ࠭᧋"),
  bstack1ll_opy_ (u"ࠪࡥࡺࡺ࡯ࡈࡴࡤࡲࡹࡖࡥࡳ࡯࡬ࡷࡸ࡯࡯࡯ࡵࠪ᧌"),
  bstack1ll_opy_ (u"ࠫࡦࡴࡤࡳࡱ࡬ࡨࡓࡧࡴࡶࡴࡤࡰࡔࡸࡩࡦࡰࡷࡥࡹ࡯࡯࡯ࠩ᧍"),
  bstack1ll_opy_ (u"ࠬࡹࡹࡴࡶࡨࡱࡕࡵࡲࡵࠩ᧎"),
  bstack1ll_opy_ (u"࠭ࡲࡦ࡯ࡲࡸࡪࡇࡤࡣࡊࡲࡷࡹ࠭᧏"),
  bstack1ll_opy_ (u"ࠧࡴ࡭࡬ࡴ࡚ࡴ࡬ࡰࡥ࡮ࠫ᧐"), bstack1ll_opy_ (u"ࠨࡷࡱࡰࡴࡩ࡫ࡕࡻࡳࡩࠬ᧑"), bstack1ll_opy_ (u"ࠩࡸࡲࡱࡵࡣ࡬ࡍࡨࡽࠬ᧒"),
  bstack1ll_opy_ (u"ࠪࡥࡺࡺ࡯ࡍࡣࡸࡲࡨ࡮ࠧ᧓"),
  bstack1ll_opy_ (u"ࠫࡸࡱࡩࡱࡎࡲ࡫ࡨࡧࡴࡄࡣࡳࡸࡺࡸࡥࠨ᧔"),
  bstack1ll_opy_ (u"ࠬࡻ࡮ࡪࡰࡶࡸࡦࡲ࡬ࡐࡶ࡫ࡩࡷࡖࡡࡤ࡭ࡤ࡫ࡪࡹࠧ᧕"),
  bstack1ll_opy_ (u"࠭ࡤࡪࡵࡤࡦࡱ࡫ࡗࡪࡰࡧࡳࡼࡇ࡮ࡪ࡯ࡤࡸ࡮ࡵ࡮ࠨ᧖"),
  bstack1ll_opy_ (u"ࠧࡣࡷ࡬ࡰࡩ࡚࡯ࡰ࡮ࡶ࡚ࡪࡸࡳࡪࡱࡱࠫ᧗"),
  bstack1ll_opy_ (u"ࠨࡧࡱࡪࡴࡸࡣࡦࡃࡳࡴࡎࡴࡳࡵࡣ࡯ࡰࠬ᧘"),
  bstack1ll_opy_ (u"ࠩࡨࡲࡸࡻࡲࡦ࡙ࡨࡦࡻ࡯ࡥࡸࡵࡋࡥࡻ࡫ࡐࡢࡩࡨࡷࠬ᧙"), bstack1ll_opy_ (u"ࠪࡻࡪࡨࡶࡪࡧࡺࡈࡪࡼࡴࡰࡱ࡯ࡷࡕࡵࡲࡵࠩ᧚"), bstack1ll_opy_ (u"ࠫࡪࡴࡡࡣ࡮ࡨ࡛ࡪࡨࡶࡪࡧࡺࡈࡪࡺࡡࡪ࡮ࡶࡇࡴࡲ࡬ࡦࡥࡷ࡭ࡴࡴࠧ᧛"),
  bstack1ll_opy_ (u"ࠬࡸࡥ࡮ࡱࡷࡩࡆࡶࡰࡴࡅࡤࡧ࡭࡫ࡌࡪ࡯࡬ࡸࠬ᧜"),
  bstack1ll_opy_ (u"࠭ࡣࡢ࡮ࡨࡲࡩࡧࡲࡇࡱࡵࡱࡦࡺࠧ᧝"),
  bstack1ll_opy_ (u"ࠧࡣࡷࡱࡨࡱ࡫ࡉࡥࠩ᧞"),
  bstack1ll_opy_ (u"ࠨ࡮ࡤࡹࡳࡩࡨࡕ࡫ࡰࡩࡴࡻࡴࠨ᧟"),
  bstack1ll_opy_ (u"ࠩ࡯ࡳࡨࡧࡴࡪࡱࡱࡗࡪࡸࡶࡪࡥࡨࡷࡊࡴࡡࡣ࡮ࡨࡨࠬ᧠"), bstack1ll_opy_ (u"ࠪࡰࡴࡩࡡࡵ࡫ࡲࡲࡘ࡫ࡲࡷ࡫ࡦࡩࡸࡇࡵࡵࡪࡲࡶ࡮ࢀࡥࡥࠩ᧡"),
  bstack1ll_opy_ (u"ࠫࡦࡻࡴࡰࡃࡦࡧࡪࡶࡴࡂ࡮ࡨࡶࡹࡹࠧ᧢"), bstack1ll_opy_ (u"ࠬࡧࡵࡵࡱࡇ࡭ࡸࡳࡩࡴࡵࡄࡰࡪࡸࡴࡴࠩ᧣"),
  bstack1ll_opy_ (u"࠭࡮ࡢࡶ࡬ࡺࡪࡏ࡮ࡴࡶࡵࡹࡲ࡫࡮ࡵࡵࡏ࡭ࡧ࠭᧤"),
  bstack1ll_opy_ (u"ࠧ࡯ࡣࡷ࡭ࡻ࡫ࡗࡦࡤࡗࡥࡵ࠭᧥"),
  bstack1ll_opy_ (u"ࠨࡵࡤࡪࡦࡸࡩࡊࡰ࡬ࡸ࡮ࡧ࡬ࡖࡴ࡯ࠫ᧦"), bstack1ll_opy_ (u"ࠩࡶࡥ࡫ࡧࡲࡪࡃ࡯ࡰࡴࡽࡐࡰࡲࡸࡴࡸ࠭᧧"), bstack1ll_opy_ (u"ࠪࡷࡦ࡬ࡡࡳ࡫ࡌ࡫ࡳࡵࡲࡦࡈࡵࡥࡺࡪࡗࡢࡴࡱ࡭ࡳ࡭ࠧ᧨"), bstack1ll_opy_ (u"ࠫࡸࡧࡦࡢࡴ࡬ࡓࡵ࡫࡮ࡍ࡫ࡱ࡯ࡸࡏ࡮ࡃࡣࡦ࡯࡬ࡸ࡯ࡶࡰࡧࠫ᧩"),
  bstack1ll_opy_ (u"ࠬࡱࡥࡦࡲࡎࡩࡾࡉࡨࡢ࡫ࡱࡷࠬ᧪"),
  bstack1ll_opy_ (u"࠭࡬ࡰࡥࡤࡰ࡮ࢀࡡࡣ࡮ࡨࡗࡹࡸࡩ࡯ࡩࡶࡈ࡮ࡸࠧ᧫"),
  bstack1ll_opy_ (u"ࠧࡱࡴࡲࡧࡪࡹࡳࡂࡴࡪࡹࡲ࡫࡮ࡵࡵࠪ᧬"),
  bstack1ll_opy_ (u"ࠨ࡫ࡱࡸࡪࡸࡋࡦࡻࡇࡩࡱࡧࡹࠨ᧭"),
  bstack1ll_opy_ (u"ࠩࡶ࡬ࡴࡽࡉࡐࡕࡏࡳ࡬࠭᧮"),
  bstack1ll_opy_ (u"ࠪࡷࡪࡴࡤࡌࡧࡼࡗࡹࡸࡡࡵࡧࡪࡽࠬ᧯"),
  bstack1ll_opy_ (u"ࠫࡼ࡫ࡢ࡬࡫ࡷࡖࡪࡹࡰࡰࡰࡶࡩ࡙࡯࡭ࡦࡱࡸࡸࠬ᧰"), bstack1ll_opy_ (u"ࠬࡹࡣࡳࡧࡨࡲࡸ࡮࡯ࡵ࡙ࡤ࡭ࡹ࡚ࡩ࡮ࡧࡲࡹࡹ࠭᧱"),
  bstack1ll_opy_ (u"࠭ࡲࡦ࡯ࡲࡸࡪࡊࡥࡣࡷࡪࡔࡷࡵࡸࡺࠩ᧲"),
  bstack1ll_opy_ (u"ࠧࡦࡰࡤࡦࡱ࡫ࡁࡴࡻࡱࡧࡊࡾࡥࡤࡷࡷࡩࡋࡸ࡯࡮ࡊࡷࡸࡵࡹࠧ᧳"),
  bstack1ll_opy_ (u"ࠨࡵ࡮࡭ࡵࡒ࡯ࡨࡅࡤࡴࡹࡻࡲࡦࠩ᧴"),
  bstack1ll_opy_ (u"ࠩࡺࡩࡧࡱࡩࡵࡆࡨࡦࡺ࡭ࡐࡳࡱࡻࡽࡕࡵࡲࡵࠩ᧵"),
  bstack1ll_opy_ (u"ࠪࡪࡺࡲ࡬ࡄࡱࡱࡸࡪࡾࡴࡍ࡫ࡶࡸࠬ᧶"),
  bstack1ll_opy_ (u"ࠫࡼࡧࡩࡵࡈࡲࡶࡆࡶࡰࡔࡥࡵ࡭ࡵࡺࠧ᧷"),
  bstack1ll_opy_ (u"ࠬࡽࡥࡣࡸ࡬ࡩࡼࡉ࡯࡯ࡰࡨࡧࡹࡘࡥࡵࡴ࡬ࡩࡸ࠭᧸"),
  bstack1ll_opy_ (u"࠭ࡡࡱࡲࡑࡥࡲ࡫ࠧ᧹"),
  bstack1ll_opy_ (u"ࠧࡤࡷࡶࡸࡴࡳࡓࡔࡎࡆࡩࡷࡺࠧ᧺"),
  bstack1ll_opy_ (u"ࠨࡶࡤࡴ࡜࡯ࡴࡩࡕ࡫ࡳࡷࡺࡐࡳࡧࡶࡷࡉࡻࡲࡢࡶ࡬ࡳࡳ࠭᧻"),
  bstack1ll_opy_ (u"ࠩࡶࡧࡦࡲࡥࡇࡣࡦࡸࡴࡸࠧ᧼"),
  bstack1ll_opy_ (u"ࠪࡻࡩࡧࡌࡰࡥࡤࡰࡕࡵࡲࡵࠩ᧽"),
  bstack1ll_opy_ (u"ࠫࡸ࡮࡯ࡸ࡚ࡦࡳࡩ࡫ࡌࡰࡩࠪ᧾"),
  bstack1ll_opy_ (u"ࠬ࡯࡯ࡴࡋࡱࡷࡹࡧ࡬࡭ࡒࡤࡹࡸ࡫ࠧ᧿"),
  bstack1ll_opy_ (u"࠭ࡸࡤࡱࡧࡩࡈࡵ࡮ࡧ࡫ࡪࡊ࡮ࡲࡥࠨᨀ"),
  bstack1ll_opy_ (u"ࠧ࡬ࡧࡼࡧ࡭ࡧࡩ࡯ࡒࡤࡷࡸࡽ࡯ࡳࡦࠪᨁ"),
  bstack1ll_opy_ (u"ࠨࡷࡶࡩࡕࡸࡥࡣࡷ࡬ࡰࡹ࡝ࡄࡂࠩᨂ"),
  bstack1ll_opy_ (u"ࠩࡳࡶࡪࡼࡥ࡯ࡶ࡚ࡈࡆࡇࡴࡵࡣࡦ࡬ࡲ࡫࡮ࡵࡵࠪᨃ"),
  bstack1ll_opy_ (u"ࠪࡻࡪࡨࡄࡳ࡫ࡹࡩࡷࡇࡧࡦࡰࡷ࡙ࡷࡲࠧᨄ"),
  bstack1ll_opy_ (u"ࠫࡰ࡫ࡹࡤࡪࡤ࡭ࡳࡖࡡࡵࡪࠪᨅ"),
  bstack1ll_opy_ (u"ࠬࡻࡳࡦࡐࡨࡻ࡜ࡊࡁࠨᨆ"),
  bstack1ll_opy_ (u"࠭ࡷࡥࡣࡏࡥࡺࡴࡣࡩࡖ࡬ࡱࡪࡵࡵࡵࠩᨇ"), bstack1ll_opy_ (u"ࠧࡸࡦࡤࡇࡴࡴ࡮ࡦࡥࡷ࡭ࡴࡴࡔࡪ࡯ࡨࡳࡺࡺࠧᨈ"),
  bstack1ll_opy_ (u"ࠨࡺࡦࡳࡩ࡫ࡏࡳࡩࡌࡨࠬᨉ"), bstack1ll_opy_ (u"ࠩࡻࡧࡴࡪࡥࡔ࡫ࡪࡲ࡮ࡴࡧࡊࡦࠪᨊ"),
  bstack1ll_opy_ (u"ࠪࡹࡵࡪࡡࡵࡧࡧ࡛ࡉࡇࡂࡶࡰࡧࡰࡪࡏࡤࠨᨋ"),
  bstack1ll_opy_ (u"ࠫࡷ࡫ࡳࡦࡶࡒࡲࡘ࡫ࡳࡴ࡫ࡲࡲࡘࡺࡡࡳࡶࡒࡲࡱࡿࠧᨌ"),
  bstack1ll_opy_ (u"ࠬࡩ࡯࡮࡯ࡤࡲࡩ࡚ࡩ࡮ࡧࡲࡹࡹࡹࠧᨍ"),
  bstack1ll_opy_ (u"࠭ࡷࡥࡣࡖࡸࡦࡸࡴࡶࡲࡕࡩࡹࡸࡩࡦࡵࠪᨎ"), bstack1ll_opy_ (u"ࠧࡸࡦࡤࡗࡹࡧࡲࡵࡷࡳࡖࡪࡺࡲࡺࡋࡱࡸࡪࡸࡶࡢ࡮ࠪᨏ"),
  bstack1ll_opy_ (u"ࠨࡥࡲࡲࡳ࡫ࡣࡵࡊࡤࡶࡩࡽࡡࡳࡧࡎࡩࡾࡨ࡯ࡢࡴࡧࠫᨐ"),
  bstack1ll_opy_ (u"ࠩࡰࡥࡽ࡚ࡹࡱ࡫ࡱ࡫ࡋࡸࡥࡲࡷࡨࡲࡨࡿࠧᨑ"),
  bstack1ll_opy_ (u"ࠪࡷ࡮ࡳࡰ࡭ࡧࡌࡷ࡛࡯ࡳࡪࡤ࡯ࡩࡈ࡮ࡥࡤ࡭ࠪᨒ"),
  bstack1ll_opy_ (u"ࠫࡺࡹࡥࡄࡣࡵࡸ࡭ࡧࡧࡦࡕࡶࡰࠬᨓ"),
  bstack1ll_opy_ (u"ࠬࡹࡨࡰࡷ࡯ࡨ࡚ࡹࡥࡔ࡫ࡱ࡫ࡱ࡫ࡴࡰࡰࡗࡩࡸࡺࡍࡢࡰࡤ࡫ࡪࡸࠧᨔ"),
  bstack1ll_opy_ (u"࠭ࡳࡵࡣࡵࡸࡎ࡝ࡄࡑࠩᨕ"),
  bstack1ll_opy_ (u"ࠧࡢ࡮࡯ࡳࡼ࡚࡯ࡶࡥ࡫ࡍࡩࡋ࡮ࡳࡱ࡯ࡰࠬᨖ"),
  bstack1ll_opy_ (u"ࠨ࡫ࡪࡲࡴࡸࡥࡉ࡫ࡧࡨࡪࡴࡁࡱ࡫ࡓࡳࡱ࡯ࡣࡺࡇࡵࡶࡴࡸࠧᨗ"),
  bstack1ll_opy_ (u"ࠩࡰࡳࡨࡱࡌࡰࡥࡤࡸ࡮ࡵ࡮ࡂࡲࡳᨘࠫ"),
  bstack1ll_opy_ (u"ࠪࡰࡴ࡭ࡣࡢࡶࡉࡳࡷࡳࡡࡵࠩᨙ"), bstack1ll_opy_ (u"ࠫࡱࡵࡧࡤࡣࡷࡊ࡮ࡲࡴࡦࡴࡖࡴࡪࡩࡳࠨᨚ"),
  bstack1ll_opy_ (u"ࠬࡧ࡬࡭ࡱࡺࡈࡪࡲࡡࡺࡃࡧࡦࠬᨛ"),
  bstack1ll_opy_ (u"࠭ࡤࡪࡵࡤࡦࡱ࡫ࡉࡥࡎࡲࡧࡦࡺ࡯ࡳࡃࡸࡸࡴࡩ࡯࡮ࡲ࡯ࡩࡹ࡯࡯࡯ࠩ᨜")
]
bstack1l111lll11_opy_ = bstack1ll_opy_ (u"ࠧࡩࡶࡷࡴࡸࡀ࠯࠰ࡣࡳ࡭࠲ࡩ࡬ࡰࡷࡧ࠲ࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭࠱ࡧࡴࡳ࠯ࡢࡲࡳ࠱ࡦࡻࡴࡰ࡯ࡤࡸࡪ࠵ࡵࡱ࡮ࡲࡥࡩ࠭᨝")
bstack11ll1l111l_opy_ = [bstack1ll_opy_ (u"ࠨ࠰ࡤࡴࡰ࠭᨞"), bstack1ll_opy_ (u"ࠩ࠱ࡥࡦࡨࠧ᨟"), bstack1ll_opy_ (u"ࠪ࠲࡮ࡶࡡࠨᨠ")]
bstack1l11ll111l_opy_ = [bstack1ll_opy_ (u"ࠫ࡮ࡪࠧᨡ"), bstack1ll_opy_ (u"ࠬࡶࡡࡵࡪࠪᨢ"), bstack1ll_opy_ (u"࠭ࡣࡶࡵࡷࡳࡲࡥࡩࡥࠩᨣ"), bstack1ll_opy_ (u"ࠧࡴࡪࡤࡶࡪࡧࡢ࡭ࡧࡢ࡭ࡩ࠭ᨤ")]
bstack11llllllll_opy_ = {
  bstack1ll_opy_ (u"ࠨࡥ࡫ࡶࡴࡳࡥࡐࡲࡷ࡭ࡴࡴࡳࠨᨥ"): bstack1ll_opy_ (u"ࠩࡪࡳࡴ࡭࠺ࡤࡪࡵࡳࡲ࡫ࡏࡱࡶ࡬ࡳࡳࡹࠧᨦ"),
  bstack1ll_opy_ (u"ࠪࡪ࡮ࡸࡥࡧࡱࡻࡓࡵࡺࡩࡰࡰࡶࠫᨧ"): bstack1ll_opy_ (u"ࠫࡲࡵࡺ࠻ࡨ࡬ࡶࡪ࡬࡯ࡹࡑࡳࡸ࡮ࡵ࡮ࡴࠩᨨ"),
  bstack1ll_opy_ (u"ࠬ࡫ࡤࡨࡧࡒࡴࡹ࡯࡯࡯ࡵࠪᨩ"): bstack1ll_opy_ (u"࠭࡭ࡴ࠼ࡨࡨ࡬࡫ࡏࡱࡶ࡬ࡳࡳࡹࠧᨪ"),
  bstack1ll_opy_ (u"ࠧࡪࡧࡒࡴࡹ࡯࡯࡯ࡵࠪᨫ"): bstack1ll_opy_ (u"ࠨࡵࡨ࠾࡮࡫ࡏࡱࡶ࡬ࡳࡳࡹࠧᨬ"),
  bstack1ll_opy_ (u"ࠩࡶࡥ࡫ࡧࡲࡪࡑࡳࡸ࡮ࡵ࡮ࡴࠩᨭ"): bstack1ll_opy_ (u"ࠪࡷࡦ࡬ࡡࡳ࡫࠱ࡳࡵࡺࡩࡰࡰࡶࠫᨮ")
}
bstack1l1ll111l1_opy_ = [
  bstack1ll_opy_ (u"ࠫ࡬ࡵ࡯ࡨ࠼ࡦ࡬ࡷࡵ࡭ࡦࡑࡳࡸ࡮ࡵ࡮ࡴࠩᨯ"),
  bstack1ll_opy_ (u"ࠬࡳ࡯ࡻ࠼ࡩ࡭ࡷ࡫ࡦࡰࡺࡒࡴࡹ࡯࡯࡯ࡵࠪᨰ"),
  bstack1ll_opy_ (u"࠭࡭ࡴ࠼ࡨࡨ࡬࡫ࡏࡱࡶ࡬ࡳࡳࡹࠧᨱ"),
  bstack1ll_opy_ (u"ࠧࡴࡧ࠽࡭ࡪࡕࡰࡵ࡫ࡲࡲࡸ࠭ᨲ"),
  bstack1ll_opy_ (u"ࠨࡵࡤࡪࡦࡸࡩ࠯ࡱࡳࡸ࡮ࡵ࡮ࡴࠩᨳ"),
]
bstack1l1111111l_opy_ = bstack11l11l1ll_opy_ + bstack11l1ll11111_opy_ + bstack1l111l1l1_opy_
bstack1l11ll1ll1_opy_ = [
  bstack1ll_opy_ (u"ࠩࡡࡰࡴࡩࡡ࡭ࡪࡲࡷࡹࠪࠧᨴ"),
  bstack1ll_opy_ (u"ࠪࡢࡧࡹ࠭࡭ࡱࡦࡥࡱ࠴ࡣࡰ࡯ࠧࠫᨵ"),
  bstack1ll_opy_ (u"ࠫࡣ࠷࠲࠸࠰ࠪᨶ"),
  bstack1ll_opy_ (u"ࠬࡤ࠱࠱࠰ࠪᨷ"),
  bstack1ll_opy_ (u"࠭࡞࠲࠹࠵࠲࠶ࡡ࠶࠮࠻ࡠ࠲ࠬᨸ"),
  bstack1ll_opy_ (u"ࠧ࡟࠳࠺࠶࠳࠸࡛࠱࠯࠼ࡡ࠳࠭ᨹ"),
  bstack1ll_opy_ (u"ࠨࡠ࠴࠻࠷࠴࠳࡜࠲࠰࠵ࡢ࠴ࠧᨺ"),
  bstack1ll_opy_ (u"ࠩࡡ࠵࠾࠸࠮࠲࠸࠻࠲ࠬᨻ")
]
bstack11l1lll1l11_opy_ = bstack1ll_opy_ (u"ࠪ࡬ࡹࡺࡰࡴ࠼࠲࠳ࡦࡶࡩ࠯ࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࠮ࡤࡱࡰࠫᨼ")
bstack1111l1111_opy_ = bstack1ll_opy_ (u"ࠫࡸࡪ࡫࠰ࡸ࠴࠳ࡪࡼࡥ࡯ࡶࠪᨽ")
bstack1ll1l11l11_opy_ = [ bstack1ll_opy_ (u"ࠬࡧࡵࡵࡱࡰࡥࡹ࡫ࠧᨾ") ]
bstack11ll1l11_opy_ = [ bstack1ll_opy_ (u"࠭ࡡࡱࡲ࠰ࡥࡺࡺ࡯࡮ࡣࡷࡩࠬᨿ") ]
bstack1l1111111_opy_ = [bstack1ll_opy_ (u"ࠧࡵࡷࡵࡦࡴ࡙ࡣࡢ࡮ࡨࠫᩀ")]
bstack11l11111l_opy_ = [ bstack1ll_opy_ (u"ࠨࡱࡥࡷࡪࡸࡶࡢࡤ࡬ࡰ࡮ࡺࡹࠨᩁ") ]
bstack1l1l1lll1_opy_ = bstack1ll_opy_ (u"ࠩࡖࡈࡐ࡙ࡥࡵࡷࡳࠫᩂ")
bstack111lll111l_opy_ = bstack1ll_opy_ (u"ࠪࡗࡉࡑࡔࡦࡵࡷࡅࡹࡺࡥ࡮ࡲࡷࡩࡩ࠭ᩃ")
bstack111l11lll_opy_ = bstack1ll_opy_ (u"ࠫࡘࡊࡋࡕࡧࡶࡸࡘࡻࡣࡤࡧࡶࡷ࡫ࡻ࡬ࠨᩄ")
bstack1l11111ll1_opy_ = bstack1ll_opy_ (u"ࠬ࠺࠮࠱࠰࠳ࠫᩅ")
bstack1ll11ll111_opy_ = [
  bstack1ll_opy_ (u"࠭ࡅࡓࡔࡢࡊࡆࡏࡌࡆࡆࠪᩆ"),
  bstack1ll_opy_ (u"ࠧࡆࡔࡕࡣ࡙ࡏࡍࡆࡆࡢࡓ࡚࡚ࠧᩇ"),
  bstack1ll_opy_ (u"ࠨࡇࡕࡖࡤࡈࡌࡐࡅࡎࡉࡉࡥࡂ࡚ࡡࡆࡐࡎࡋࡎࡕࠩᩈ"),
  bstack1ll_opy_ (u"ࠩࡈࡖࡗࡥࡎࡆࡖ࡚ࡓࡗࡑ࡟ࡄࡊࡄࡒࡌࡋࡄࠨᩉ"),
  bstack1ll_opy_ (u"ࠪࡉࡗࡘ࡟ࡔࡑࡆࡏࡊ࡚࡟ࡏࡑࡗࡣࡈࡕࡎࡏࡇࡆࡘࡊࡊࠧᩊ"),
  bstack1ll_opy_ (u"ࠫࡊࡘࡒࡠࡅࡒࡒࡓࡋࡃࡕࡋࡒࡒࡤࡉࡌࡐࡕࡈࡈࠬᩋ"),
  bstack1ll_opy_ (u"ࠬࡋࡒࡓࡡࡆࡓࡓࡔࡅࡄࡖࡌࡓࡓࡥࡒࡆࡕࡈࡘࠬᩌ"),
  bstack1ll_opy_ (u"࠭ࡅࡓࡔࡢࡇࡔࡔࡎࡆࡅࡗࡍࡔࡔ࡟ࡓࡇࡉ࡙ࡘࡋࡄࠨᩍ"),
  bstack1ll_opy_ (u"ࠧࡆࡔࡕࡣࡈࡕࡎࡏࡇࡆࡘࡎࡕࡎࡠࡃࡅࡓࡗ࡚ࡅࡅࠩᩎ"),
  bstack1ll_opy_ (u"ࠨࡇࡕࡖࡤࡉࡏࡏࡐࡈࡇ࡙ࡏࡏࡏࡡࡉࡅࡎࡒࡅࡅࠩᩏ"),
  bstack1ll_opy_ (u"ࠩࡈࡖࡗࡥࡎࡂࡏࡈࡣࡓࡕࡔࡠࡔࡈࡗࡔࡒࡖࡆࡆࠪᩐ"),
  bstack1ll_opy_ (u"ࠪࡉࡗࡘ࡟ࡂࡆࡇࡖࡊ࡙ࡓࡠࡋࡑ࡚ࡆࡒࡉࡅࠩᩑ"),
  bstack1ll_opy_ (u"ࠫࡊࡘࡒࡠࡃࡇࡈࡗࡋࡓࡔࡡࡘࡒࡗࡋࡁࡄࡊࡄࡆࡑࡋࠧᩒ"),
  bstack1ll_opy_ (u"ࠬࡋࡒࡓࡡࡗ࡙ࡓࡔࡅࡍࡡࡆࡓࡓࡔࡅࡄࡖࡌࡓࡓࡥࡆࡂࡋࡏࡉࡉ࠭ᩓ"),
  bstack1ll_opy_ (u"࠭ࡅࡓࡔࡢࡇࡔࡔࡎࡆࡅࡗࡍࡔࡔ࡟ࡕࡋࡐࡉࡉࡥࡏࡖࡖࠪᩔ"),
  bstack1ll_opy_ (u"ࠧࡆࡔࡕࡣࡘࡕࡃࡌࡕࡢࡇࡔࡔࡎࡆࡅࡗࡍࡔࡔ࡟ࡇࡃࡌࡐࡊࡊࠧᩕ"),
  bstack1ll_opy_ (u"ࠨࡇࡕࡖࡤ࡙ࡏࡄࡍࡖࡣࡈࡕࡎࡏࡇࡆࡘࡎࡕࡎࡠࡊࡒࡗ࡙ࡥࡕࡏࡔࡈࡅࡈࡎࡁࡃࡎࡈࠫᩖ"),
  bstack1ll_opy_ (u"ࠩࡈࡖࡗࡥࡐࡓࡑ࡛࡝ࡤࡉࡏࡏࡐࡈࡇ࡙ࡏࡏࡏࡡࡉࡅࡎࡒࡅࡅࠩᩗ"),
  bstack1ll_opy_ (u"ࠪࡉࡗࡘ࡟ࡏࡃࡐࡉࡤࡔࡏࡕࡡࡕࡉࡘࡕࡌࡗࡇࡇࠫᩘ"),
  bstack1ll_opy_ (u"ࠫࡊࡘࡒࡠࡐࡄࡑࡊࡥࡒࡆࡕࡒࡐ࡚࡚ࡉࡐࡐࡢࡊࡆࡏࡌࡆࡆࠪᩙ"),
  bstack1ll_opy_ (u"ࠬࡋࡒࡓࡡࡐࡅࡓࡊࡁࡕࡑࡕ࡝ࡤࡖࡒࡐ࡚࡜ࡣࡈࡕࡎࡇࡋࡊ࡙ࡗࡇࡔࡊࡑࡑࡣࡋࡇࡉࡍࡇࡇࠫᩚ"),
]
bstack1ll11l1l11_opy_ = bstack1ll_opy_ (u"࠭࠮࠰ࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࠭ࡢࡴࡷ࡭࡫ࡧࡣࡵࡵ࠲ࠫᩛ")
bstack11ll1ll1_opy_ = os.path.join(os.path.expanduser(bstack1ll_opy_ (u"ࠧࡿࠩᩜ")), bstack1ll_opy_ (u"ࠨ࠰ࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫ࠨᩝ"), bstack1ll_opy_ (u"ࠩ࠱ࡦࡸࡺࡡࡤ࡭࠰ࡧࡴࡴࡦࡪࡩ࠱࡮ࡸࡵ࡮ࠨᩞ"))
bstack11ll111l1ll_opy_ = bstack1ll_opy_ (u"ࠪ࡬ࡹࡺࡰࡴ࠼࠲࠳ࡦࡩࡣࡦࡵࡶ࡭ࡧ࡯࡬ࡪࡶࡼ࠲ࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭࠱ࡧࡴࡳ࠯ࡢࡲ࡬ࠫ᩟")
bstack11l11lllll1_opy_ = [ bstack1ll_opy_ (u"ࠫࡵࡿࡴࡦࡵࡷ᩠ࠫ"), bstack1ll_opy_ (u"ࠬࡸ࡯ࡣࡱࡷࠫᩡ"), bstack1ll_opy_ (u"࠭ࡰࡢࡤࡲࡸࠬᩢ"), bstack1ll_opy_ (u"ࠧࡣࡧ࡫ࡥࡻ࡫ࠧᩣ")]
bstack11l11lll11_opy_ = [ bstack1ll_opy_ (u"ࠨࡲࡼࡸࡪࡹࡴࠨᩤ"), bstack1ll_opy_ (u"ࠩࡵࡳࡧࡵࡴࠨᩥ"), bstack1ll_opy_ (u"ࠪࡴࡦࡨ࡯ࡵࠩᩦ"), bstack1ll_opy_ (u"ࠫࡧ࡫ࡨࡢࡸࡨࠫᩧ") ]
bstack1l11l1l111_opy_ = [ bstack1ll_opy_ (u"ࠬࡸ࡯ࡣࡱࡷࠫᩨ") ]
bstack11l1l1lll11_opy_ = [ bstack1ll_opy_ (u"࠭ࡰࡺࡶࡨࡷࡹ࠭ᩩ") ]
bstack11ll11l1l_opy_ = 360
bstack11l1lll11l1_opy_ = bstack1ll_opy_ (u"ࠢࡢࡲࡳ࠱ࡦࡩࡣࡦࡵࡶ࡭ࡧ࡯࡬ࡪࡶࡼ࠲ࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭࠱ࡧࡴࡳࠢᩪ")
bstack11l1l1111l1_opy_ = bstack1ll_opy_ (u"ࠣࡣࡸࡸࡴࡳࡡࡵࡧ࠲ࡥࡵ࡯࠯ࡷ࠳࠲࡭ࡸࡹࡵࡦࡵࠥᩫ")
bstack11l1l1llll1_opy_ = bstack1ll_opy_ (u"ࠤࡤࡹࡹࡵ࡭ࡢࡶࡨ࠳ࡦࡶࡩ࠰ࡸ࠴࠳࡮ࡹࡳࡶࡧࡶ࠱ࡸࡻ࡭࡮ࡣࡵࡽࠧᩬ")
bstack11ll1111111_opy_ = bstack1ll_opy_ (u"ࠥࡅࡵࡶࠠࡂࡥࡦࡩࡸࡹࡩࡣ࡫࡯࡭ࡹࡿࠠࡂࡷࡷࡳࡲࡧࡴࡪࡱࡱࠤࡹ࡫ࡳࡵࡵࠣࡥࡷ࡫ࠠࡴࡷࡳࡴࡴࡸࡴࡦࡦࠣࡳࡳࠦࡏࡔࠢࡹࡩࡷࡹࡩࡰࡰࠣࠩࡸࠦࡡ࡯ࡦࠣࡥࡧࡵࡶࡦࠢࡩࡳࡷࠦࡁ࡯ࡦࡵࡳ࡮ࡪࠠࡥࡧࡹ࡭ࡨ࡫ࡳ࠯ࠤᩭ")
bstack11ll11l11l1_opy_ = bstack1ll_opy_ (u"ࠦ࠶࠷࠮࠱ࠤᩮ")
bstack1111l1lll1_opy_ = {
  bstack1ll_opy_ (u"ࠬࡖࡁࡔࡕࠪᩯ"): bstack1ll_opy_ (u"࠭ࡰࡢࡵࡶࡩࡩ࠭ᩰ"),
  bstack1ll_opy_ (u"ࠧࡇࡃࡌࡐࠬᩱ"): bstack1ll_opy_ (u"ࠨࡨࡤ࡭ࡱ࡫ࡤࠨᩲ"),
  bstack1ll_opy_ (u"ࠩࡖࡏࡎࡖࠧᩳ"): bstack1ll_opy_ (u"ࠪࡷࡰ࡯ࡰࡱࡧࡧࠫᩴ")
}
bstack11ll1lll1l_opy_ = [
  bstack1ll_opy_ (u"ࠦ࡬࡫ࡴࠣ᩵"),
  bstack1ll_opy_ (u"ࠧ࡭࡯ࡃࡣࡦ࡯ࠧ᩶"),
  bstack1ll_opy_ (u"ࠨࡧࡰࡈࡲࡶࡼࡧࡲࡥࠤ᩷"),
  bstack1ll_opy_ (u"ࠢࡳࡧࡩࡶࡪࡹࡨࠣ᩸"),
  bstack1ll_opy_ (u"ࠣࡥ࡯࡭ࡨࡱࡅ࡭ࡧࡰࡩࡳࡺࠢ᩹"),
  bstack1ll_opy_ (u"ࠤࡶࡧࡷ࡫ࡥ࡯ࡵ࡫ࡳࡹࠨ᩺"),
  bstack1ll_opy_ (u"ࠥࡷࡺࡨ࡭ࡪࡶࡈࡰࡪࡳࡥ࡯ࡶࠥ᩻"),
  bstack1ll_opy_ (u"ࠦࡸ࡫࡮ࡥࡍࡨࡽࡸ࡚࡯ࡆ࡮ࡨࡱࡪࡴࡴࠣ᩼"),
  bstack1ll_opy_ (u"ࠧࡹࡥ࡯ࡦࡎࡩࡾࡹࡔࡰࡃࡦࡸ࡮ࡼࡥࡆ࡮ࡨࡱࡪࡴࡴࠣ᩽"),
  bstack1ll_opy_ (u"ࠨࡣ࡭ࡧࡤࡶࡊࡲࡥ࡮ࡧࡱࡸࠧ᩾"),
  bstack1ll_opy_ (u"ࠢࡢࡥࡷ࡭ࡴࡴࡳ᩿ࠣ"),
  bstack1ll_opy_ (u"ࠣࡧࡻࡩࡨࡻࡴࡦࡕࡦࡶ࡮ࡶࡴࠣ᪀"),
  bstack1ll_opy_ (u"ࠤࡨࡼࡪࡩࡵࡵࡧࡄࡷࡾࡴࡣࡔࡥࡵ࡭ࡵࡺࠢ᪁"),
  bstack1ll_opy_ (u"ࠥࡧࡱࡵࡳࡦࠤ᪂"),
  bstack1ll_opy_ (u"ࠦࡶࡻࡩࡵࠤ᪃"),
  bstack1ll_opy_ (u"ࠧࡶࡥࡳࡨࡲࡶࡲ࡚࡯ࡶࡥ࡫ࡅࡨࡺࡩࡰࡰࠥ᪄"),
  bstack1ll_opy_ (u"ࠨࡰࡦࡴࡩࡳࡷࡳࡍࡶ࡮ࡷ࡭࡙ࡵࡵࡤࡪࠥ᪅"),
  bstack1ll_opy_ (u"ࠢࡴࡪࡤ࡯ࡪࠨ᪆"),
  bstack1ll_opy_ (u"ࠣࡥ࡯ࡳࡸ࡫ࡁࡱࡲࠥ᪇")
]
bstack11l11llll11_opy_ = [
  bstack1ll_opy_ (u"ࠤࡦࡰ࡮ࡩ࡫ࠣ᪈"),
  bstack1ll_opy_ (u"ࠥࡷࡨࡸࡥࡦࡰࡶ࡬ࡴࡺࠢ᪉"),
  bstack1ll_opy_ (u"ࠦࡦࡻࡴࡰࠤ᪊"),
  bstack1ll_opy_ (u"ࠧࡳࡡ࡯ࡷࡤࡰࠧ᪋"),
  bstack1ll_opy_ (u"ࠨࡴࡦࡵࡷࡧࡦࡹࡥࠣ᪌")
]
bstack11111llll_opy_ = {
  bstack1ll_opy_ (u"ࠢࡤ࡮࡬ࡧࡰࠨ᪍"): [bstack1ll_opy_ (u"ࠣࡥ࡯࡭ࡨࡱࡅ࡭ࡧࡰࡩࡳࡺࠢ᪎")],
  bstack1ll_opy_ (u"ࠤࡶࡧࡷ࡫ࡥ࡯ࡵ࡫ࡳࡹࠨ᪏"): [bstack1ll_opy_ (u"ࠥࡷࡨࡸࡥࡦࡰࡶ࡬ࡴࡺࠢ᪐")],
  bstack1ll_opy_ (u"ࠦࡦࡻࡴࡰࠤ᪑"): [bstack1ll_opy_ (u"ࠧࡹࡥ࡯ࡦࡎࡩࡾࡹࡔࡰࡇ࡯ࡩࡲ࡫࡮ࡵࠤ᪒"), bstack1ll_opy_ (u"ࠨࡳࡦࡰࡧࡏࡪࡿࡳࡕࡱࡄࡧࡹ࡯ࡶࡦࡇ࡯ࡩࡲ࡫࡮ࡵࠤ᪓"), bstack1ll_opy_ (u"ࠢࡴࡥࡵࡩࡪࡴࡳࡩࡱࡷࠦ᪔"), bstack1ll_opy_ (u"ࠣࡥ࡯࡭ࡨࡱࡅ࡭ࡧࡰࡩࡳࡺࠢ᪕")],
  bstack1ll_opy_ (u"ࠤࡰࡥࡳࡻࡡ࡭ࠤ᪖"): [bstack1ll_opy_ (u"ࠥࡱࡦࡴࡵࡢ࡮ࠥ᪗")],
  bstack1ll_opy_ (u"ࠦࡹ࡫ࡳࡵࡥࡤࡷࡪࠨ᪘"): [bstack1ll_opy_ (u"ࠧࡺࡥࡴࡶࡦࡥࡸ࡫ࠢ᪙")],
}
bstack11l1l11ll1l_opy_ = {
  bstack1ll_opy_ (u"ࠨࡣ࡭࡫ࡦ࡯ࡊࡲࡥ࡮ࡧࡱࡸࠧ᪚"): bstack1ll_opy_ (u"ࠢࡤ࡮࡬ࡧࡰࠨ᪛"),
  bstack1ll_opy_ (u"ࠣࡵࡦࡶࡪ࡫࡮ࡴࡪࡲࡸࠧ᪜"): bstack1ll_opy_ (u"ࠤࡶࡧࡷ࡫ࡥ࡯ࡵ࡫ࡳࡹࠨ᪝"),
  bstack1ll_opy_ (u"ࠥࡷࡪࡴࡤࡌࡧࡼࡷ࡙ࡵࡅ࡭ࡧࡰࡩࡳࡺࠢ᪞"): bstack1ll_opy_ (u"ࠦࡸ࡫࡮ࡥࡍࡨࡽࡸࠨ᪟"),
  bstack1ll_opy_ (u"ࠧࡹࡥ࡯ࡦࡎࡩࡾࡹࡔࡰࡃࡦࡸ࡮ࡼࡥࡆ࡮ࡨࡱࡪࡴࡴࠣ᪠"): bstack1ll_opy_ (u"ࠨࡳࡦࡰࡧࡏࡪࡿࡳࠣ᪡"),
  bstack1ll_opy_ (u"ࠢࡵࡧࡶࡸࡨࡧࡳࡦࠤ᪢"): bstack1ll_opy_ (u"ࠣࡶࡨࡷࡹࡩࡡࡴࡧࠥ᪣")
}
bstack1111ll1ll1_opy_ = {
  bstack1ll_opy_ (u"ࠩࡅࡉࡋࡕࡒࡆࡡࡄࡐࡑ࠭᪤"): bstack1ll_opy_ (u"ࠪࡗࡺ࡯ࡴࡦࠢࡖࡩࡹࡻࡰࠨ᪥"),
  bstack1ll_opy_ (u"ࠫࡆࡌࡔࡆࡔࡢࡅࡑࡒࠧ᪦"): bstack1ll_opy_ (u"࡙ࠬࡵࡪࡶࡨࠤ࡙࡫ࡡࡳࡦࡲࡻࡳ࠭ᪧ"),
  bstack1ll_opy_ (u"࠭ࡂࡆࡈࡒࡖࡊࡥࡅࡂࡅࡋࠫ᪨"): bstack1ll_opy_ (u"ࠧࡕࡧࡶࡸ࡙ࠥࡥࡵࡷࡳࠫ᪩"),
  bstack1ll_opy_ (u"ࠨࡃࡉࡘࡊࡘ࡟ࡆࡃࡆࡌࠬ᪪"): bstack1ll_opy_ (u"ࠩࡗࡩࡸࡺࠠࡕࡧࡤࡶࡩࡵࡷ࡯ࠩ᪫")
}
bstack11l11llll1l_opy_ = 65536
bstack11l1l11llll_opy_ = bstack1ll_opy_ (u"ࠪ࠲࠳࠴࡛ࡕࡔࡘࡒࡈࡇࡔࡆࡆࡠࠫ᪬")
bstack11l1l1l1ll1_opy_ = [
      bstack1ll_opy_ (u"ࠫࡺࡹࡥࡳࡐࡤࡱࡪ࠭᪭"), bstack1ll_opy_ (u"ࠬࡧࡣࡤࡧࡶࡷࡐ࡫ࡹࠨ᪮"), bstack1ll_opy_ (u"࠭ࡨࡵࡶࡳࡔࡷࡵࡸࡺࠩ᪯"), bstack1ll_opy_ (u"ࠧࡩࡶࡷࡴࡸࡖࡲࡰࡺࡼࠫ᪰"), bstack1ll_opy_ (u"ࠨࡥࡸࡷࡹࡵ࡭ࡗࡣࡵ࡭ࡦࡨ࡬ࡦࡵࠪ᪱"),
      bstack1ll_opy_ (u"ࠩࡳࡶࡴࡾࡹࡖࡵࡨࡶࠬ᪲"), bstack1ll_opy_ (u"ࠪࡴࡷࡵࡸࡺࡒࡤࡷࡸ࠭᪳"), bstack1ll_opy_ (u"ࠫࡱࡵࡣࡢ࡮ࡓࡶࡴࡾࡹࡖࡵࡨࡶࠬ᪴"), bstack1ll_opy_ (u"ࠬࡲ࡯ࡤࡣ࡯ࡔࡷࡵࡸࡺࡒࡤࡷࡸ᪵࠭"),
      bstack1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯࠳ࡻࡳࡦࡴࡑࡥࡲ࡫᪶ࠧ"), bstack1ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰ࠴ࡡࡤࡥࡨࡷࡸࡑࡥࡺ᪷ࠩ"), bstack1ll_opy_ (u"ࠨࡣࡸࡸ࡭࡚࡯࡬ࡧࡱ᪸ࠫ")
    ]
bstack11l1l1l1111_opy_= {
  bstack1ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫ࡍࡱࡦࡥࡱ᪹࠭"): bstack1ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬ࡎࡲࡧࡦࡲ᪺ࠧ"),
  bstack1ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࡘࡺࡡࡤ࡭ࡏࡳࡨࡧ࡬ࡐࡲࡷ࡭ࡴࡴࡳࠨ᪻"): bstack1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷ࡙ࡴࡢࡥ࡮ࡐࡴࡩࡡ࡭ࡑࡳࡸ࡮ࡵ࡮ࡴࠩ᪼"),
  bstack1ll_opy_ (u"࠭࡬ࡰࡥࡤࡰࡔࡶࡴࡪࡱࡱࡷ᪽ࠬ"): bstack1ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡔࡶࡤࡧࡰࡒ࡯ࡤࡣ࡯ࡓࡵࡺࡩࡰࡰࡶࠫ᪾"),
  bstack1ll_opy_ (u"ࠨࡲࡤࡶࡦࡲ࡬ࡦ࡮ࡶࡔࡪࡸࡐ࡭ࡣࡷࡪࡴࡸ࡭ࠨᪿ"): bstack1ll_opy_ (u"ࠩࡳࡥࡷࡧ࡬࡭ࡧ࡯ࡷࡕ࡫ࡲࡑ࡮ࡤࡸ࡫ࡵࡲ࡮ᫀࠩ"),
  bstack1ll_opy_ (u"ࠪࡴࡱࡧࡴࡧࡱࡵࡱࡸ࠭᫁"): bstack1ll_opy_ (u"ࠫࡵࡲࡡࡵࡨࡲࡶࡲࡹࠧ᫂"),
  bstack1ll_opy_ (u"ࠬࡲ࡯ࡨࡎࡨࡺࡪࡲ᫃ࠧ"): bstack1ll_opy_ (u"࠭࡬ࡰࡩࡏࡩࡻ࡫࡬ࠨ᫄"),
  bstack1ll_opy_ (u"ࠧࡩࡶࡷࡴࡕࡸ࡯ࡹࡻࠪ᫅"): bstack1ll_opy_ (u"ࠨࡪࡷࡸࡵࡖࡲࡰࡺࡼࠫ᫆"),
  bstack1ll_opy_ (u"ࠩ࡫ࡸࡹࡶࡳࡑࡴࡲࡼࡾ࠭᫇"): bstack1ll_opy_ (u"ࠪ࡬ࡹࡺࡰࡴࡒࡵࡳࡽࡿࠧ᫈"),
  bstack1ll_opy_ (u"ࠫ࡫ࡸࡡ࡮ࡧࡺࡳࡷࡱࠧ᫉"): bstack1ll_opy_ (u"ࠬ࡬ࡲࡢ࡯ࡨࡻࡴࡸ࡫ࠨ᫊"),
  bstack1ll_opy_ (u"࠭ࡴࡦࡵࡷࡇࡴࡴࡴࡦࡺࡷࡓࡵࡺࡩࡰࡰࡶࠫ᫋"): bstack1ll_opy_ (u"ࠧࡵࡧࡶࡸࡈࡵ࡮ࡵࡧࡻࡸࡔࡶࡴࡪࡱࡱࡷࠬᫌ"),
  bstack1ll_opy_ (u"ࠨࡶࡨࡷࡹࡕࡢࡴࡧࡵࡺࡦࡨࡩ࡭࡫ࡷࡽࠬᫍ"): bstack1ll_opy_ (u"ࠩࡷࡩࡸࡺࡏࡣࡵࡨࡶࡻࡧࡢࡪ࡮࡬ࡸࡾ࠭ᫎ"),
  bstack1ll_opy_ (u"ࠪࡸࡪࡹࡴࡓࡧࡳࡳࡷࡺࡩ࡯ࡩࠪ᫏"): bstack1ll_opy_ (u"ࠫࡹ࡫ࡳࡵࡔࡨࡴࡴࡸࡴࡪࡰࡪࠫ᫐"),
  bstack1ll_opy_ (u"ࠬࡺࡥࡴࡶࡒࡦࡸ࡫ࡲࡷࡣࡥ࡭ࡱ࡯ࡴࡺࡑࡳࡸ࡮ࡵ࡮ࡴࠩ᫑"): bstack1ll_opy_ (u"࠭ࡴࡦࡵࡷࡓࡧࡹࡥࡳࡸࡤࡦ࡮ࡲࡩࡵࡻࡒࡴࡹ࡯࡯࡯ࡵࠪ᫒"),
  bstack1ll_opy_ (u"ࠧࡵࡧࡶࡸࡗ࡫ࡰࡰࡴࡷ࡭ࡳ࡭ࡏࡱࡶ࡬ࡳࡳࡹࠧ᫓"): bstack1ll_opy_ (u"ࠨࡶࡨࡷࡹࡘࡥࡱࡱࡵࡸ࡮ࡴࡧࡐࡲࡷ࡭ࡴࡴࡳࠨ᫔"),
  bstack1ll_opy_ (u"ࠩࡦࡹࡸࡺ࡯࡮ࡘࡤࡶ࡮ࡧࡢ࡭ࡧࡶࠫ᫕"): bstack1ll_opy_ (u"ࠪࡧࡺࡹࡴࡰ࡯࡙ࡥࡷ࡯ࡡࡣ࡮ࡨࡷࠬ᫖"),
  bstack1ll_opy_ (u"ࠫࡦࡻࡴࡰ࡯ࡤࡸ࡮ࡵ࡮ࠨ᫗"): bstack1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮ࡅࡺࡺ࡯࡮ࡣࡷ࡭ࡴࡴࠧ᫘"),
  bstack1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯ࡆࡻࡴࡰ࡯ࡤࡸ࡮ࡵ࡮ࠨ᫙"): bstack1ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰࡇࡵࡵࡱࡰࡥࡹ࡯࡯࡯ࠩ᫚"),
  bstack1ll_opy_ (u"ࠨࡴࡨࡶࡺࡴࡔࡦࡵࡷࡷࠬ᫛"): bstack1ll_opy_ (u"ࠩࡵࡩࡷࡻ࡮ࡕࡧࡶࡸࡸ࠭᫜"),
  bstack1ll_opy_ (u"ࠪࡴࡪࡸࡣࡺࠩ᫝"): bstack1ll_opy_ (u"ࠫࡵ࡫ࡲࡤࡻࠪ᫞"),
  bstack1ll_opy_ (u"ࠬࡶࡥࡳࡥࡼࡓࡵࡺࡩࡰࡰࡶࠫ᫟"): bstack1ll_opy_ (u"࠭ࡰࡦࡴࡦࡽࡔࡶࡴࡪࡱࡱࡷࠬ᫠"),
  bstack1ll_opy_ (u"ࠧࡱࡧࡵࡧࡾࡉࡡࡱࡶࡸࡶࡪࡓ࡯ࡥࡧࠪ᫡"): bstack1ll_opy_ (u"ࠨࡲࡨࡶࡨࡿࡃࡢࡲࡷࡹࡷ࡫ࡍࡰࡦࡨࠫ᫢"),
  bstack1ll_opy_ (u"ࠩࡧ࡭ࡸࡧࡢ࡭ࡧࡄࡹࡹࡵࡃࡢࡲࡷࡹࡷ࡫ࡌࡰࡩࡶࠫ᫣"): bstack1ll_opy_ (u"ࠪࡨ࡮ࡹࡡࡣ࡮ࡨࡅࡺࡺ࡯ࡄࡣࡳࡸࡺࡸࡥࡍࡱࡪࡷࠬ᫤"),
  bstack1ll_opy_ (u"ࠫࡦࡩࡣࡦࡵࡶ࡭ࡧ࡯࡬ࡪࡶࡼࠫ᫥"): bstack1ll_opy_ (u"ࠬࡧࡣࡤࡧࡶࡷ࡮ࡨࡩ࡭࡫ࡷࡽࠬ᫦"),
  bstack1ll_opy_ (u"࠭ࡡࡤࡥࡨࡷࡸ࡯ࡢࡪ࡮࡬ࡸࡾࡕࡰࡵ࡫ࡲࡲࡸ࠭᫧"): bstack1ll_opy_ (u"ࠧࡢࡥࡦࡩࡸࡹࡩࡣ࡫࡯࡭ࡹࡿࡏࡱࡶ࡬ࡳࡳࡹࠧ᫨"),
  bstack1ll_opy_ (u"ࠨࡶࡸࡶࡧࡵࡓࡤࡣ࡯ࡩࠬ᫩"): bstack1ll_opy_ (u"ࠩࡷࡹࡷࡨ࡯ࡔࡥࡤࡰࡪ࠭᫪"),
  bstack1ll_opy_ (u"ࠪࡸࡺࡸࡢࡰࡕࡦࡥࡱ࡫ࡏࡱࡶ࡬ࡳࡳࡹࠧ᫫"): bstack1ll_opy_ (u"ࠫࡹࡻࡲࡣࡱࡖࡧࡦࡲࡥࡐࡲࡷ࡭ࡴࡴࡳࠨ᫬"),
  bstack1ll_opy_ (u"ࠬࡺࡥࡴࡶࡒࡶࡨ࡮ࡥࡴࡶࡵࡥࡹ࡯࡯࡯ࡑࡳࡸ࡮ࡵ࡮ࡴࠩ᫭"): bstack1ll_opy_ (u"࠭ࡴࡦࡵࡷࡓࡷࡩࡨࡦࡵࡷࡶࡦࡺࡩࡰࡰࡒࡴࡹ࡯࡯࡯ࡵࠪ᫮"),
  bstack1ll_opy_ (u"ࠧࡱࡴࡲࡼࡾ࡙ࡥࡵࡶ࡬ࡲ࡬ࡹࠧ᫯"): bstack1ll_opy_ (u"ࠨࡲࡵࡳࡽࡿࡓࡦࡶࡷ࡭ࡳ࡭ࡳࠨ᫰")
}
bstack11l1l11l111_opy_ = [bstack1ll_opy_ (u"ࠩࡳࡽࡹ࡫ࡳࡵࠩ᫱"), bstack1ll_opy_ (u"ࠪࡶࡴࡨ࡯ࡵࠩ᫲")]
bstack111l11ll1_opy_ = (bstack1ll_opy_ (u"ࠦࡵࡿࡴࡦࡵࡷࠦ᫳"),)
bstack11l1l11lll1_opy_ = bstack1ll_opy_ (u"ࠬࡹࡤ࡬࠱ࡹ࠵࠴ࡻࡰࡥࡣࡷࡩࡤࡩ࡬ࡪࠩ᫴")
bstack11l1ll1lll_opy_ = bstack1ll_opy_ (u"ࠨࡨࡵࡶࡳࡷ࠿࠵࠯ࡢࡲ࡬࠲ࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭࠱ࡧࡴࡳ࠯ࡢࡷࡷࡳࡲࡧࡴࡦ࠯ࡷࡹࡷࡨ࡯ࡴࡥࡤࡰࡪ࠵ࡶ࠲࠱ࡪࡶ࡮ࡪࡳ࠰ࠤ᫵")
bstack1l1l1l1111_opy_ = bstack1ll_opy_ (u"ࠢࡩࡶࡷࡴࡸࡀ࠯࠰ࡩࡵ࡭ࡩ࠴ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯࠳ࡩ࡯࡮࠱ࡧࡥࡸ࡮ࡢࡰࡣࡵࡨ࠴ࡨࡵࡪ࡮ࡧࡷ࠴ࠨ᫶")
bstack1l11l1ll_opy_ = bstack1ll_opy_ (u"ࠣࡪࡷࡸࡵࡹ࠺࠰࠱ࡤࡴ࡮࠴ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯࠳ࡩ࡯࡮࠱ࡤࡹࡹࡵ࡭ࡢࡶࡨ࠱ࡹࡻࡲࡣࡱࡶࡧࡦࡲࡥ࠰ࡸ࠴࠳ࡧࡻࡩ࡭ࡦࡶ࠲࡯ࡹ࡯࡯ࠤ᫷")
class EVENTS(Enum):
  bstack11l1l1l111l_opy_ = bstack1ll_opy_ (u"ࠩࡶࡨࡰࡀ࡯࠲࠳ࡼ࠾ࡵࡸࡩ࡯ࡶ࠰ࡦࡺ࡯࡬ࡥ࡮࡬ࡲࡰ࠭᫸")
  bstack1l111ll1ll_opy_ = bstack1ll_opy_ (u"ࠪࡷࡩࡱ࠺ࡤ࡮ࡨࡥࡳࡻࡰࠨ᫹") # final bstack11l1l11l1l1_opy_
  bstack11l1l1ll1l1_opy_ = bstack1ll_opy_ (u"ࠫࡸࡪ࡫࠻ࡵࡨࡲࡩࡲ࡯ࡨࡵࠪ᫺")
  bstack111l1l11_opy_ = bstack1ll_opy_ (u"ࠬࡹࡤ࡬࠼ࡷࡹࡷࡨ࡯ࡴࡥࡤࡰࡪࡀࡰࡳ࡫ࡱࡸ࠲ࡨࡵࡪ࡮ࡧࡰ࡮ࡴ࡫ࠨ᫻") #shift post bstack11l1l1l11ll_opy_
  bstack1l111llll1_opy_ = bstack1ll_opy_ (u"࠭ࡳࡥ࡭࠽ࡥࡺࡺ࡯࡮ࡣࡷࡩ࠿ࡶࡲࡪࡰࡷ࠱ࡧࡻࡩ࡭ࡦ࡯࡭ࡳࡱࠧ᫼") #shift post bstack11l1l1l11ll_opy_
  bstack11l1l11111l_opy_ = bstack1ll_opy_ (u"ࠧࡴࡦ࡮࠾ࡹ࡫ࡳࡵࡪࡸࡦࠬ᫽") #shift
  bstack11l1l1l1l1l_opy_ = bstack1ll_opy_ (u"ࠨࡵࡧ࡯࠿ࡶࡥࡳࡥࡼ࠾ࡩࡵࡷ࡯࡮ࡲࡥࡩ࠭᫾") #shift
  bstack111l1lll_opy_ = bstack1ll_opy_ (u"ࠩࡶࡨࡰࡀࡴࡶࡴࡥࡳࡸࡩࡡ࡭ࡧ࠽࡬ࡺࡨ࠭࡮ࡣࡱࡥ࡬࡫࡭ࡦࡰࡷࠫ᫿")
  bstack1ll11l1l11l_opy_ = bstack1ll_opy_ (u"ࠪࡷࡩࡱ࠺ࡢ࠳࠴ࡽ࠿ࡹࡡࡷࡧ࠰ࡶࡪࡹࡵ࡭ࡶࡶࠫᬀ")
  bstack1l1l1ll1l_opy_ = bstack1ll_opy_ (u"ࠫࡸࡪ࡫࠻ࡣ࠴࠵ࡾࡀࡤࡳ࡫ࡹࡩࡷ࠳ࡰࡦࡴࡩࡳࡷࡳࡳࡤࡣࡱࠫᬁ")
  bstack1ll1l1llll_opy_ = bstack1ll_opy_ (u"ࠬࡹࡤ࡬࠼ࡤࡹࡹࡵ࡭ࡢࡶࡨ࠾ࡱࡵࡣࡢ࡮ࠪᬂ") #shift
  bstack1111lll11_opy_ = bstack1ll_opy_ (u"࠭ࡳࡥ࡭࠽ࡥࡵࡶ࠭ࡢࡷࡷࡳࡲࡧࡴࡦ࠼ࡤࡴࡵ࠳ࡵࡱ࡮ࡲࡥࡩ࠭ᬃ") #shift
  bstack1l1l1l1ll_opy_ = bstack1ll_opy_ (u"ࠧࡴࡦ࡮࠾ࡦࡻࡴࡰ࡯ࡤࡸࡪࡀࡣࡪ࠯ࡤࡶࡹ࡯ࡦࡢࡥࡷࡷࠬᬄ")
  bstack1l111l111l_opy_ = bstack1ll_opy_ (u"ࠨࡵࡧ࡯࠿ࡧ࠱࠲ࡻ࠽࡫ࡪࡺ࠭ࡢࡥࡦࡩࡸࡹࡩࡣ࡫࡯࡭ࡹࡿ࠭ࡳࡧࡶࡹࡱࡺࡳ࠮ࡵࡸࡱࡲࡧࡲࡺࠩᬅ") #shift
  bstack1llll11ll_opy_ = bstack1ll_opy_ (u"ࠩࡶࡨࡰࡀࡡ࠲࠳ࡼ࠾࡬࡫ࡴ࠮ࡣࡦࡧࡪࡹࡳࡪࡤ࡬ࡰ࡮ࡺࡹ࠮ࡴࡨࡷࡺࡲࡴࡴࠩᬆ") #shift
  bstack11l1l111ll1_opy_ = bstack1ll_opy_ (u"ࠪࡷࡩࡱ࠺ࡱࡧࡵࡧࡾ࠭ᬇ") #shift
  bstack1l11lllllll_opy_ = bstack1ll_opy_ (u"ࠫࡸࡪ࡫࠻ࡲࡨࡶࡨࡿ࠺ࡴࡥࡵࡩࡪࡴࡳࡩࡱࡷࠫᬈ")
  bstack11ll1ll1l1_opy_ = bstack1ll_opy_ (u"ࠬࡹࡤ࡬࠼ࡤࡹࡹࡵ࡭ࡢࡶࡨ࠾ࡸ࡫ࡳࡴ࡫ࡲࡲ࠲ࡹࡴࡢࡶࡸࡷࠬᬉ") #shift
  bstack1l111l11l1_opy_ = bstack1ll_opy_ (u"࠭ࡳࡥ࡭࠽ࡥࡺࡺ࡯࡮ࡣࡷࡩ࠿࡮ࡵࡣ࠯ࡰࡥࡳࡧࡧࡦ࡯ࡨࡲࡹ࠭ᬊ")
  bstack11l11llllll_opy_ = bstack1ll_opy_ (u"ࠧࡴࡦ࡮࠾ࡵࡸ࡯ࡹࡻ࠰ࡷࡪࡺࡵࡱࠩᬋ") #shift
  bstack11ll1l11ll_opy_ = bstack1ll_opy_ (u"ࠨࡵࡧ࡯࠿ࡹࡥࡵࡷࡳࠫᬌ")
  bstack11l1l1l1l11_opy_ = bstack1ll_opy_ (u"ࠩࡶࡨࡰࡀࡰࡦࡴࡦࡽ࠿ࡹ࡮ࡢࡲࡶ࡬ࡴࡺࠧᬍ") # not bstack11l1l111l1l_opy_ in python
  bstack1l1ll1l11l_opy_ = bstack1ll_opy_ (u"ࠪࡷࡩࡱ࠺ࡥࡴ࡬ࡺࡪࡸ࠺ࡲࡷ࡬ࡸࠬᬎ") # used in bstack11l1l111lll_opy_
  bstack1ll1l111ll_opy_ = bstack1ll_opy_ (u"ࠫࡸࡪ࡫࠻ࡦࡵ࡭ࡻ࡫ࡲ࠻ࡩࡨࡸࠬᬏ") # used in bstack11l1l111lll_opy_
  bstack1ll1llll11_opy_ = bstack1ll_opy_ (u"ࠬࡹࡤ࡬࠼࡫ࡳࡴࡱࠧᬐ")
  bstack111l1ll1l_opy_ = bstack1ll_opy_ (u"࠭ࡳࡥ࡭࠽ࡥࡺࡺ࡯࡮ࡣࡷࡩ࠿ࡹࡥࡴࡵ࡬ࡳࡳ࠳࡮ࡢ࡯ࡨࠫᬑ")
  bstack111llll111_opy_ = bstack1ll_opy_ (u"ࠧࡴࡦ࡮࠾ࡦࡻࡴࡰ࡯ࡤࡸࡪࡀࡳࡦࡵࡶ࡭ࡴࡴ࠭ࡢࡰࡱࡳࡹࡧࡴࡪࡱࡱࠫᬒ") #
  bstack1l1l1ll1_opy_ = bstack1ll_opy_ (u"ࠨࡵࡧ࡯࠿ࡵ࠱࠲ࡻ࠽ࡨࡷ࡯ࡶࡦࡴ࠰ࡸࡦࡱࡥࡔࡥࡵࡩࡪࡴࡓࡩࡱࡷࠫᬓ")
  bstack1l1l1llll_opy_ = bstack1ll_opy_ (u"ࠩࡶࡨࡰࡀࡰࡦࡴࡦࡽ࠿ࡧࡵࡵࡱ࠰ࡧࡦࡶࡴࡶࡴࡨࠫᬔ")
  bstack1ll1l11lll_opy_ = bstack1ll_opy_ (u"ࠪࡷࡩࡱ࠺ࡱࡴࡨ࠱ࡹ࡫ࡳࡵࠩᬕ")
  bstack1llll1l1ll_opy_ = bstack1ll_opy_ (u"ࠫࡸࡪ࡫࠻ࡲࡲࡷࡹ࠳ࡴࡦࡵࡷࠫᬖ")
  bstack1l1lllll1_opy_ = bstack1ll_opy_ (u"ࠬࡹࡤ࡬࠼ࡧࡶ࡮ࡼࡥࡳ࠼ࡳࡶࡪ࠳ࡩ࡯࡫ࡷ࡭ࡦࡲࡩࡻࡣࡷ࡭ࡴࡴࠧᬗ") #shift
  bstack11l111lll_opy_ = bstack1ll_opy_ (u"࠭ࡳࡥ࡭࠽ࡨࡷ࡯ࡶࡦࡴ࠽ࡴࡴࡹࡴ࠮࡫ࡱ࡭ࡹ࡯ࡡ࡭࡫ࡽࡥࡹ࡯࡯࡯ࠩᬘ") #shift
  bstack11l1l111l11_opy_ = bstack1ll_opy_ (u"ࠧࡴࡦ࡮࠾ࡦࡻࡴࡰ࠯ࡦࡥࡵࡺࡵࡳࡧࠪᬙ")
  bstack11l1l1l11l1_opy_ = bstack1ll_opy_ (u"ࠨࡵࡧ࡯࠿ࡧࡵࡵࡱࡰࡥࡹ࡫࠺ࡪࡦ࡯ࡩ࠲ࡺࡩ࡮ࡧࡲࡹࡹ࠭ᬚ")
  bstack1ll1l1l1ll1_opy_ = bstack1ll_opy_ (u"ࠩࡶࡨࡰࡀࡣ࡭࡫࠽ࡷࡹࡧࡲࡵࠩᬛ")
  bstack11l1l11l11l_opy_ = bstack1ll_opy_ (u"ࠪࡷࡩࡱ࠺ࡤ࡮࡬࠾ࡩࡵࡷ࡯࡮ࡲࡥࡩ࠭ᬜ")
  bstack11l1l1ll111_opy_ = bstack1ll_opy_ (u"ࠫࡸࡪ࡫࠻ࡥ࡯࡭࠿ࡩࡨࡦࡥ࡮࠱ࡺࡶࡤࡢࡶࡨࠫᬝ")
  bstack1ll1lll1lll_opy_ = bstack1ll_opy_ (u"ࠬࡹࡤ࡬࠼ࡦࡰ࡮ࡀ࡯࡯࠯ࡥࡳࡴࡺࡳࡵࡴࡤࡴࠬᬞ")
  bstack1lll11l1l11_opy_ = bstack1ll_opy_ (u"࠭ࡳࡥ࡭࠽ࡧࡱ࡯࠺ࡰࡰ࠰ࡧࡴࡴ࡮ࡦࡥࡷࠫᬟ")
  bstack1ll1lll1ll1_opy_ = bstack1ll_opy_ (u"ࠧࡴࡦ࡮࠾ࡨࡲࡩ࠻ࡱࡱ࠱ࡸࡺ࡯ࡱࠩᬠ")
  bstack1ll1ll1l1ll_opy_ = bstack1ll_opy_ (u"ࠨࡵࡧ࡯࠿ࡹࡴࡢࡴࡷࡆ࡮ࡴࡓࡦࡵࡶ࡭ࡴࡴࠧᬡ")
  bstack1lll1111ll1_opy_ = bstack1ll_opy_ (u"ࠩࡶࡨࡰࡀࡣࡰࡰࡱࡩࡨࡺࡂࡪࡰࡖࡩࡸࡹࡩࡰࡰࠪᬢ")
  bstack11l1l11ll11_opy_ = bstack1ll_opy_ (u"ࠪࡷࡩࡱ࠺ࡥࡴ࡬ࡺࡪࡸࡉ࡯࡫ࡷࠫᬣ")
  bstack11l11lll11l_opy_ = bstack1ll_opy_ (u"ࠫࡸࡪ࡫࠻ࡨ࡬ࡲࡩࡔࡥࡢࡴࡨࡷࡹࡎࡵࡣࠩᬤ")
  bstack1l11l11llll_opy_ = bstack1ll_opy_ (u"ࠬࡹࡤ࡬࠼ࡤࡹࡹࡵ࡭ࡢࡶ࡬ࡳࡳࡌࡲࡢ࡯ࡨࡻࡴࡸ࡫ࡊࡰ࡬ࡸࠬᬥ")
  bstack1l11l11l1ll_opy_ = bstack1ll_opy_ (u"࠭ࡳࡥ࡭࠽ࡥࡺࡺ࡯࡮ࡣࡷ࡭ࡴࡴࡆࡳࡣࡰࡩࡼࡵࡲ࡬ࡕࡷࡥࡷࡺࠧᬦ")
  bstack1ll1111l1l1_opy_ = bstack1ll_opy_ (u"ࠧࡴࡦ࡮࠾ࡦࡩࡣࡦࡵࡶ࡭ࡧ࡯࡬ࡪࡶࡼࡇࡴࡴࡦࡪࡩࠪᬧ")
  bstack11l1l1lllll_opy_ = bstack1ll_opy_ (u"ࠨࡵࡧ࡯࠿ࡵࡢࡴࡧࡵࡺࡦࡨࡩ࡭࡫ࡷࡽࡈࡵ࡮ࡧ࡫ࡪࠫᬨ")
  bstack1l1lll1l11l_opy_ = bstack1ll_opy_ (u"ࠩࡶࡨࡰࡀࡡࡪࡕࡨࡰ࡫ࡎࡥࡢ࡮ࡖࡸࡪࡶࠧᬩ")
  bstack1l1lll11l11_opy_ = bstack1ll_opy_ (u"ࠪࡷࡩࡱ࠺ࡢ࡫ࡖࡩࡱ࡬ࡈࡦࡣ࡯ࡋࡪࡺࡒࡦࡵࡸࡰࡹ࠭ᬪ")
  bstack1l1l11l1lll_opy_ = bstack1ll_opy_ (u"ࠫࡸࡪ࡫࠻ࡶࡨࡷࡹࡌࡲࡢ࡯ࡨࡻࡴࡸ࡫ࡆࡸࡨࡲࡹ࠭ᬫ")
  bstack1l1l1l11lll_opy_ = bstack1ll_opy_ (u"ࠬࡹࡤ࡬࠼ࡷࡩࡸࡺࡓࡦࡵࡶ࡭ࡴࡴࡅࡷࡧࡱࡸࠬᬬ")
  bstack1l1l1l1l1l1_opy_ = bstack1ll_opy_ (u"࠭ࡳࡥ࡭࠽ࡧࡱ࡯࠺࡭ࡱࡪࡇࡷ࡫ࡡࡵࡧࡧࡉࡻ࡫࡮ࡵࠩᬭ")
  bstack11l1l1lll1l_opy_ = bstack1ll_opy_ (u"ࠧࡴࡦ࡮࠾ࡨࡲࡩ࠻ࡧࡱࡵࡺ࡫ࡵࡦࡖࡨࡷࡹࡋࡶࡦࡰࡷࠫᬮ")
  bstack1l11l111lll_opy_ = bstack1ll_opy_ (u"ࠨࡵࡧ࡯࠿ࡧࡵࡵࡱࡰࡥࡹ࡯࡯࡯ࡈࡵࡥࡲ࡫ࡷࡰࡴ࡮ࡗࡹࡵࡰࠨᬯ")
  bstack1ll1l1lll1l_opy_ = bstack1ll_opy_ (u"ࠩࡶࡨࡰࡀ࡯࡯ࡕࡷࡳࡵ࠭ᬰ")
class STAGE(Enum):
  bstack11l11l1l11_opy_ = bstack1ll_opy_ (u"ࠪࡷࡹࡧࡲࡵࠩᬱ")
  END = bstack1ll_opy_ (u"ࠫࡪࡴࡤࠨᬲ")
  bstack1l1lll1ll1_opy_ = bstack1ll_opy_ (u"ࠬࡹࡩ࡯ࡩ࡯ࡩࠬᬳ")
bstack111lllll1l_opy_ = {
  bstack1ll_opy_ (u"࠭ࡐ࡚ࡖࡈࡗ᬴࡙࠭"): bstack1ll_opy_ (u"ࠧࡱࡻࡷࡩࡸࡺࠧᬵ"),
  bstack1ll_opy_ (u"ࠨࡒ࡜ࡘࡊ࡙ࡔ࠮ࡄࡇࡈࠬᬶ"): bstack1ll_opy_ (u"ࠩࡓࡽࡹ࡫ࡳࡵ࠯ࡦࡹࡨࡻ࡭ࡣࡧࡵࠫᬷ")
}
PLAYWRIGHT_HUB_URL = bstack1ll_opy_ (u"ࠥࡻࡸࡹ࠺࠰࠱ࡦࡨࡵ࠴ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯࠳ࡩ࡯࡮࠱ࡳࡰࡦࡿࡷࡳ࡫ࡪ࡬ࡹࡅࡣࡢࡲࡶࡁࠧᬸ")
bstack1ll1111ll1l_opy_ = 98
bstack1ll1111l111_opy_ = 100
bstack1lllllll111_opy_ = {
  bstack1ll_opy_ (u"ࠫࡷ࡫ࡲࡶࡰࠪᬹ"): bstack1ll_opy_ (u"ࠬ࠳࠭ࡳࡧࡵࡹࡳࡹࠧᬺ"),
  bstack1ll_opy_ (u"࠭ࡤࡦ࡮ࡤࡽࠬᬻ"): bstack1ll_opy_ (u"ࠧ࠮࠯ࡵࡩࡷࡻ࡮ࡴ࠯ࡧࡩࡱࡧࡹࠨᬼ"),
  bstack1ll_opy_ (u"ࠨࡴࡨࡶࡺࡴ࠭ࡥࡧ࡯ࡥࡾ࠭ᬽ"): 0
}
bstack11l1l1ll1ll_opy_ = bstack1ll_opy_ (u"ࠤ࡫ࡸࡹࡶࡳ࠻࠱࠲ࡧࡴࡲ࡬ࡦࡥࡷࡳࡷ࠳࡯ࡣࡵࡨࡶࡻࡧࡢࡪ࡮࡬ࡸࡾ࠴ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯࠳ࡩ࡯࡮ࠤᬾ")
bstack11l1l1l1lll_opy_ = bstack1ll_opy_ (u"ࠥ࡬ࡹࡺࡰࡴ࠼࠲࠳ࡺࡶ࡬ࡰࡣࡧ࠱ࡴࡨࡳࡦࡴࡹࡥࡧ࡯࡬ࡪࡶࡼ࠲ࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭࠱ࡧࡴࡳࠢᬿ")
bstack11llllll11_opy_ = bstack1ll_opy_ (u"࡙ࠦࡋࡓࡕࠢࡕࡉࡕࡕࡒࡕࡋࡑࡋࠥࡇࡎࡅࠢࡄࡒࡆࡒ࡙ࡕࡋࡆࡗࠧᭀ")