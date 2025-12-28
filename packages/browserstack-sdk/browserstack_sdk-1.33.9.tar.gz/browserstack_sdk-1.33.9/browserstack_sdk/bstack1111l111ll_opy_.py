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
bstack1ll_opy_ (u"ࠨࠢࠣࠌࡓࡽࡹ࡫ࡳࡵࠢࡷࡩࡸࡺࠠࡤࡱ࡯ࡰࡪࡩࡴࡪࡱࡱࠤ࡭࡫࡬ࡱࡧࡵࠤࡺࡹࡩ࡯ࡩࠣࡨ࡮ࡸࡥࡤࡶࠣࡴࡾࡺࡥࡴࡶࠣ࡬ࡴࡵ࡫ࡴ࠰ࠍࠦࠧࠨၠ")
import pytest
import io
import os
from contextlib import redirect_stdout, redirect_stderr
import subprocess
import sys
def bstack11111lll11_opy_(bstack11111ll1ll_opy_=None, bstack11111ll1l1_opy_=None):
    bstack1ll_opy_ (u"ࠢࠣࠤࠍࠤࠥࠦࠠࡄࡱ࡯ࡰࡪࡩࡴࠡࡲࡼࡸࡪࡹࡴࠡࡶࡨࡷࡹࡹࠠࡶࡵ࡬ࡲ࡬ࠦࡰࡺࡶࡨࡷࡹ࠭ࡳࠡ࡫ࡱࡸࡪࡸ࡮ࡢ࡮ࠣࡅࡕࡏࡳ࠯ࠌࠣࠤࠥࠦࡁࡳࡩࡶ࠾ࠏࠦࠠࠡࠢࠣࠤࠥࠦࡴࡦࡵࡷࡣࡦࡸࡧࡴࠢࠫࡰ࡮ࡹࡴ࠭ࠢࡲࡴࡹ࡯࡯࡯ࡣ࡯࠭࠿ࠦࡃࡰ࡯ࡳࡰࡪࡺࡥࠡ࡮࡬ࡷࡹࠦ࡯ࡧࠢࡳࡽࡹ࡫ࡳࡵࠢࡤࡶ࡬ࡻ࡭ࡦࡰࡷࡷࠥ࡯࡮ࡤ࡮ࡸࡨ࡮ࡴࡧࠡࡲࡤࡸ࡭ࡹࠠࡢࡰࡧࠤ࡫ࡲࡡࡨࡵ࠱ࠎࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤ࡙ࡧ࡫ࡦࡵࠣࡴࡷ࡫ࡣࡦࡦࡨࡲࡨ࡫ࠠࡰࡸࡨࡶࠥࡺࡥࡴࡶࡢࡴࡦࡺࡨࡴࠢ࡬ࡪࠥࡨ࡯ࡵࡪࠣࡥࡷ࡫ࠠࡱࡴࡲࡺ࡮ࡪࡥࡥ࠰ࠍࠤࠥࠦࠠࠡࠢࠣࠤࡹ࡫ࡳࡵࡡࡳࡥࡹ࡮ࡳࠡࠪ࡯࡭ࡸࡺࠠࡰࡴࠣࡷࡹࡸࠬࠡࡱࡳࡸ࡮ࡵ࡮ࡢ࡮ࠬ࠾࡚ࠥࡥࡴࡶࠣࡪ࡮ࡲࡥࠩࡵࠬ࠳ࡩ࡯ࡲࡦࡥࡷࡳࡷࡿࠨࡪࡧࡶ࠭ࠥࡺ࡯ࠡࡥࡲࡰࡱ࡫ࡣࡵࠢࡩࡶࡴࡳ࠮ࠋࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࡆࡥࡳࠦࡢࡦࠢࡤࠤࡸ࡯࡮ࡨ࡮ࡨࠤࡵࡧࡴࡩࠢࡶࡸࡷ࡯࡮ࡨࠢࡲࡶࠥࡲࡩࡴࡶࠣࡳ࡫ࠦࡰࡢࡶ࡫ࡷ࠳ࠐࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࡊࡩࡱࡳࡷ࡫ࡤࠡ࡫ࡩࠤࡹ࡫ࡳࡵࡡࡤࡶ࡬ࡹࠠࡪࡵࠣࡴࡷࡵࡶࡪࡦࡨࡨ࠳ࠐࠠࠡࠢࠣࡖࡪࡺࡵࡳࡰࡶ࠾ࠏࠦࠠࠡࠢࠣࠤࠥࠦࡤࡪࡥࡷ࠾ࠥࡉ࡯࡭࡮ࡨࡧࡹ࡯࡯࡯ࠢࡵࡩࡸࡻ࡬ࡵࡵࠣࡻ࡮ࡺࡨࠡ࡭ࡨࡽࡸࡀࠊࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥ࠳ࠠࡴࡷࡦࡧࡪࡹࡳࠡࠪࡥࡳࡴࡲࠩࠋࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦ࠭ࠡࡥࡲࡹࡳࡺࠠࠩ࡫ࡱࡸ࠮ࠐࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤ࠲ࠦ࡮ࡰࡦࡨ࡭ࡩࡹࠠࠩ࡮࡬ࡷࡹ࠯ࠊࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥ࠳ࠠࡵࡧࡶࡸࡤ࡬ࡩ࡭ࡧࡶࠤ࠭ࡲࡩࡴࡶࠬࠎࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢ࠰ࠤࡪࡸࡲࡰࡴࠣࠬࡸࡺࡲࠪࠌࠣࠤࠥࠦࠢࠣࠤၡ")
    try:
        bstack11111ll11l_opy_ = os.getenv(bstack1ll_opy_ (u"ࠣࡒ࡜ࡘࡊ࡙ࡔࡠࡅࡘࡖࡗࡋࡎࡕࡡࡗࡉࡘ࡚ࠢၢ")) is not None
        if bstack11111ll1ll_opy_ is not None:
            args = list(bstack11111ll1ll_opy_)
        elif bstack11111ll1l1_opy_ is not None:
            if isinstance(bstack11111ll1l1_opy_, str):
                args = [bstack11111ll1l1_opy_]
            elif isinstance(bstack11111ll1l1_opy_, list):
                args = list(bstack11111ll1l1_opy_)
            else:
                args = [bstack1ll_opy_ (u"ࠤ࠱ࠦၣ")]
        else:
            args = [bstack1ll_opy_ (u"ࠥ࠲ࠧၤ")]
        if bstack11111ll11l_opy_:
            return _1111l111l1_opy_(args)
        bstack11111lll1l_opy_ = args + [
            bstack1ll_opy_ (u"ࠦ࠲࠳ࡣࡰ࡮࡯ࡩࡨࡺ࠭ࡰࡰ࡯ࡽࠧၥ"),
            bstack1ll_opy_ (u"ࠧ࠳࠭ࡲࡷ࡬ࡩࡹࠨၦ")
        ]
        class bstack1111l11l11_opy_:
            bstack1ll_opy_ (u"ࠨࠢࠣࡒࡼࡸࡪࡹࡴࠡࡲ࡯ࡹ࡬࡯࡮ࠡࡶ࡫ࡥࡹࠦࡣࡢࡲࡷࡹࡷ࡫ࡳࠡࡥࡲࡰࡱ࡫ࡣࡵࡧࡧࠤࡹ࡫ࡳࡵࠢ࡬ࡸࡪࡳࡳ࠯ࠤࠥࠦၧ")
            def __init__(self):
                self.bstack11111lllll_opy_ = []
                self.test_files = set()
                self.bstack11111llll1_opy_ = None
            def pytest_collection_finish(self, session):
                bstack1ll_opy_ (u"ࠢࠣࠤࡋࡳࡴࡱࠠࡤࡣ࡯ࡰࡪࡪࠠࡢࡨࡷࡩࡷࠦࡣࡰ࡮࡯ࡩࡨࡺࡩࡰࡰࠣ࡭ࡸࠦࡦࡪࡰ࡬ࡷ࡭࡫ࡤ࠯ࠤࠥࠦၨ")
                try:
                    for item in session.items:
                        nodeid = item.nodeid
                        self.bstack11111lllll_opy_.append(nodeid)
                        if bstack1ll_opy_ (u"ࠣ࠼࠽ࠦၩ") in nodeid:
                            file_path = nodeid.split(bstack1ll_opy_ (u"ࠤ࠽࠾ࠧၪ"), 1)[0]
                            if file_path.endswith(bstack1ll_opy_ (u"ࠪ࠲ࡵࡿࠧၫ")):
                                self.test_files.add(file_path)
                except Exception as e:
                    self.bstack11111llll1_opy_ = str(e)
        collector = bstack1111l11l11_opy_()
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            exit_code = pytest.main(bstack11111lll1l_opy_, plugins=[collector])
        if collector.bstack11111llll1_opy_:
            return {bstack1ll_opy_ (u"ࠦࡸࡻࡣࡤࡧࡶࡷࠧၬ"): False, bstack1ll_opy_ (u"ࠧࡩ࡯ࡶࡰࡷࠦၭ"): 0, bstack1ll_opy_ (u"ࠨ࡮ࡰࡦࡨ࡭ࡩࡹࠢၮ"): [], bstack1ll_opy_ (u"ࠢࡵࡧࡶࡸࡤ࡬ࡩ࡭ࡧࡶࠦၯ"): [], bstack1ll_opy_ (u"ࠣࡧࡵࡶࡴࡸࠢၰ"): bstack1ll_opy_ (u"ࠤࡆࡳࡱࡲࡥࡤࡶ࡬ࡳࡳࠦࡥࡳࡴࡲࡶ࠿ࠦࡻࡾࠤၱ").format(collector.bstack11111llll1_opy_)}
        return {
            bstack1ll_opy_ (u"ࠥࡷࡺࡩࡣࡦࡵࡶࠦၲ"): True,
            bstack1ll_opy_ (u"ࠦࡨࡵࡵ࡯ࡶࠥၳ"): len(collector.bstack11111lllll_opy_),
            bstack1ll_opy_ (u"ࠧࡴ࡯ࡥࡧ࡬ࡨࡸࠨၴ"): collector.bstack11111lllll_opy_,
            bstack1ll_opy_ (u"ࠨࡴࡦࡵࡷࡣ࡫࡯࡬ࡦࡵࠥၵ"): sorted(collector.test_files),
            bstack1ll_opy_ (u"ࠢࡦࡺ࡬ࡸࡤࡩ࡯ࡥࡧࠥၶ"): exit_code
        }
    except Exception as e:
        return {bstack1ll_opy_ (u"ࠣࡵࡸࡧࡨ࡫ࡳࡴࠤၷ"): False, bstack1ll_opy_ (u"ࠤࡦࡳࡺࡴࡴࠣၸ"): 0, bstack1ll_opy_ (u"ࠥࡲࡴࡪࡥࡪࡦࡶࠦၹ"): [], bstack1ll_opy_ (u"ࠦࡹ࡫ࡳࡵࡡࡩ࡭ࡱ࡫ࡳࠣၺ"): [], bstack1ll_opy_ (u"ࠧ࡫ࡲࡳࡱࡵࠦၻ"): bstack1ll_opy_ (u"ࠨࡕ࡯ࡧࡻࡴࡪࡩࡴࡦࡦࠣࡩࡷࡸ࡯ࡳࠢ࡬ࡲࠥࡺࡥࡴࡶࠣࡧࡴࡲ࡬ࡦࡥࡷ࡭ࡴࡴ࠺ࠡࡽࢀࠦၼ").format(e)}
def _1111l111l1_opy_(args):
    bstack1ll_opy_ (u"ࠢࠣࠤࡌࡷࡴࡲࡡࡵࡧࡧࠤࡨࡵ࡬࡭ࡧࡦࡸ࡮ࡵ࡮ࠡࡧࡻࡩࡨࡻࡴࡦࡦࠣ࡭ࡳࠦࡡࠡࡵࡨࡴࡦࡸࡡࡵࡧࠣࡔࡾࡺࡨࡰࡰࠣࡴࡷࡵࡣࡦࡵࡶࠤࡹࡵࠠࡢࡸࡲ࡭ࡩࠦ࡮ࡦࡵࡷࡩࡩࠦࡰࡺࡶࡨࡷࡹࠦࡩࡴࡵࡸࡩࡸ࠴ࠢࠣࠤၽ")
    bstack1111l1111l_opy_ = [sys.executable, bstack1ll_opy_ (u"ࠣ࠯ࡰࠦၾ"), bstack1ll_opy_ (u"ࠤࡳࡽࡹ࡫ࡳࡵࠤၿ"), bstack1ll_opy_ (u"ࠥ࠱࠲ࡩ࡯࡭࡮ࡨࡧࡹ࠳࡯࡯࡮ࡼࠦႀ"), bstack1ll_opy_ (u"ࠦ࠲࠳ࡱࡶ࡫ࡨࡸࠧႁ")]
    bstack1111l11111_opy_ = [a for a in args if a not in (bstack1ll_opy_ (u"ࠧ࠳࠭ࡤࡱ࡯ࡰࡪࡩࡴ࠮ࡱࡱࡰࡾࠨႂ"), bstack1ll_opy_ (u"ࠨ࠭࠮ࡳࡸ࡭ࡪࡺࠢႃ"), bstack1ll_opy_ (u"ࠢ࠮ࡳࠥႄ"))]
    cmd = bstack1111l1111l_opy_ + bstack1111l11111_opy_
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, env=os.environ.copy())
        stdout = proc.stdout.splitlines()
        bstack11111lllll_opy_ = []
        test_files = set()
        for line in stdout:
            line = line.strip()
            if not line or bstack1ll_opy_ (u"ࠣࠢࡦࡳࡱࡲࡥࡤࡶࡨࡨࠧႅ") in line.lower():
                continue
            if bstack1ll_opy_ (u"ࠤ࠽࠾ࠧႆ") in line:
                bstack11111lllll_opy_.append(line)
                file_path = line.split(bstack1ll_opy_ (u"ࠥ࠾࠿ࠨႇ"), 1)[0]
                if file_path.endswith(bstack1ll_opy_ (u"ࠫ࠳ࡶࡹࠨႈ")):
                    test_files.add(file_path)
        success = proc.returncode in (0, 5)
        return {
            bstack1ll_opy_ (u"ࠧࡹࡵࡤࡥࡨࡷࡸࠨႉ"): success,
            bstack1ll_opy_ (u"ࠨࡣࡰࡷࡱࡸࠧႊ"): len(bstack11111lllll_opy_),
            bstack1ll_opy_ (u"ࠢ࡯ࡱࡧࡩ࡮ࡪࡳࠣႋ"): bstack11111lllll_opy_,
            bstack1ll_opy_ (u"ࠣࡶࡨࡷࡹࡥࡦࡪ࡮ࡨࡷࠧႌ"): sorted(test_files),
            bstack1ll_opy_ (u"ࠤࡨࡼ࡮ࡺ࡟ࡤࡱࡧࡩႍࠧ"): proc.returncode,
            bstack1ll_opy_ (u"ࠥࡩࡷࡸ࡯ࡳࠤႎ"): None if success else bstack1ll_opy_ (u"ࠦࡘࡻࡢࡱࡴࡲࡧࡪࡹࡳࠡࡥࡲࡰࡱ࡫ࡣࡵ࡫ࡲࡲࠥ࡬ࡡࡪ࡮ࡨࡨࠥ࠮ࡥࡹ࡫ࡷࠤࢀࢃࠩࠣႏ").format(proc.returncode)
        }
    except Exception as e:
        return {bstack1ll_opy_ (u"ࠧࡹࡵࡤࡥࡨࡷࡸࠨ႐"): False, bstack1ll_opy_ (u"ࠨࡣࡰࡷࡱࡸࠧ႑"): 0, bstack1ll_opy_ (u"ࠢ࡯ࡱࡧࡩ࡮ࡪࡳࠣ႒"): [], bstack1ll_opy_ (u"ࠣࡶࡨࡷࡹࡥࡦࡪ࡮ࡨࡷࠧ႓"): [], bstack1ll_opy_ (u"ࠤࡨࡶࡷࡵࡲࠣ႔"): bstack1ll_opy_ (u"ࠥࡗࡺࡨࡰࡳࡱࡦࡩࡸࡹࠠࡤࡱ࡯ࡰࡪࡩࡴࡪࡱࡱࠤࡪࡸࡲࡰࡴ࠽ࠤࢀࢃࠢ႕").format(e)}