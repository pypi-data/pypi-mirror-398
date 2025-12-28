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
import collections
import datetime
import json
import os
import platform
import re
import subprocess
import traceback
import tempfile
import multiprocessing
import threading
import sys
import logging
from math import ceil
from unittest import result
import urllib
from urllib.parse import urlparse
import copy
import zipfile
import git
import requests
from packaging import version
from bstack_utils.config import Config
from bstack_utils.constants import (bstack1l11ll1ll1_opy_, bstack1l11lll11_opy_, bstack1lll111l11_opy_,
                                    bstack11l11llll1l_opy_, bstack11l1l11llll_opy_, bstack11l1l1l1ll1_opy_, bstack11l1l1l1111_opy_)
from bstack_utils.measure import measure
from bstack_utils.messages import bstack1l1lll1111_opy_, bstack1ll1111ll_opy_
from bstack_utils.proxy import bstack11ll11llll_opy_, bstack1ll11ll11l_opy_
from bstack_utils.constants import *
from bstack_utils import bstack11l1l1lll1_opy_
from bstack_utils.bstack1llllllll_opy_ import bstack1l1lll11ll_opy_
from browserstack_sdk._version import __version__
bstack1ll1l1l111_opy_ = Config.bstack11lll1111_opy_()
logger = bstack11l1l1lll1_opy_.get_logger(__name__, bstack11l1l1lll1_opy_.bstack1ll1l11l11l_opy_())
def bstack11ll11llll1_opy_(config):
    return config[bstack1ll_opy_ (u"ࠨࡷࡶࡩࡷࡔࡡ࡮ࡧࠪ᭵")]
def bstack11ll11ll1ll_opy_(config):
    return config[bstack1ll_opy_ (u"ࠩࡤࡧࡨ࡫ࡳࡴࡍࡨࡽࠬ᭶")]
def bstack1111l1l1l_opy_():
    try:
        import playwright
        return True
    except ImportError:
        return False
def bstack11l111l11ll_opy_(obj):
    values = []
    bstack11l11l11111_opy_ = re.compile(bstack1ll_opy_ (u"ࡵࠦࡣࡉࡕࡔࡖࡒࡑࡤ࡚ࡁࡈࡡ࡟ࡨ࠰ࠪࠢ᭷"), re.I)
    for key in obj.keys():
        if bstack11l11l11111_opy_.match(key):
            values.append(obj[key])
    return values
def bstack11l1111llll_opy_(config):
    tags = []
    tags.extend(bstack11l111l11ll_opy_(os.environ))
    tags.extend(bstack11l111l11ll_opy_(config))
    return tags
def bstack11l111lll1l_opy_(markers):
    tags = []
    for marker in markers:
        tags.append(marker.name)
    return tags
def bstack11l111ll1l1_opy_(bstack11l11l111l1_opy_):
    if not bstack11l11l111l1_opy_:
        return bstack1ll_opy_ (u"ࠫࠬ᭸")
    return bstack1ll_opy_ (u"ࠧࢁࡽࠡࠪࡾࢁ࠮ࠨ᭹").format(bstack11l11l111l1_opy_.name, bstack11l11l111l1_opy_.email)
def bstack11ll11lllll_opy_():
    try:
        repo = git.Repo(search_parent_directories=True)
        bstack11l111ll1ll_opy_ = repo.common_dir
        info = {
            bstack1ll_opy_ (u"ࠨࡳࡩࡣࠥ᭺"): repo.head.commit.hexsha,
            bstack1ll_opy_ (u"ࠢࡴࡪࡲࡶࡹࡥࡳࡩࡣࠥ᭻"): repo.git.rev_parse(repo.head.commit, short=True),
            bstack1ll_opy_ (u"ࠣࡤࡵࡥࡳࡩࡨࠣ᭼"): repo.active_branch.name,
            bstack1ll_opy_ (u"ࠤࡷࡥ࡬ࠨ᭽"): repo.git.describe(all=True, tags=True, exact_match=True),
            bstack1ll_opy_ (u"ࠥࡧࡴࡳ࡭ࡪࡶࡷࡩࡷࠨ᭾"): bstack11l111ll1l1_opy_(repo.head.commit.committer),
            bstack1ll_opy_ (u"ࠦࡨࡵ࡭࡮࡫ࡷࡸࡪࡸ࡟ࡥࡣࡷࡩࠧ᭿"): repo.head.commit.committed_datetime.isoformat(),
            bstack1ll_opy_ (u"ࠧࡧࡵࡵࡪࡲࡶࠧᮀ"): bstack11l111ll1l1_opy_(repo.head.commit.author),
            bstack1ll_opy_ (u"ࠨࡡࡶࡶ࡫ࡳࡷࡥࡤࡢࡶࡨࠦᮁ"): repo.head.commit.authored_datetime.isoformat(),
            bstack1ll_opy_ (u"ࠢࡤࡱࡰࡱ࡮ࡺ࡟࡮ࡧࡶࡷࡦ࡭ࡥࠣᮂ"): repo.head.commit.message,
            bstack1ll_opy_ (u"ࠣࡴࡲࡳࡹࠨᮃ"): repo.git.rev_parse(bstack1ll_opy_ (u"ࠤ࠰࠱ࡸ࡮࡯ࡸ࠯ࡷࡳࡵࡲࡥࡷࡧ࡯ࠦᮄ")),
            bstack1ll_opy_ (u"ࠥࡧࡴࡳ࡭ࡰࡰࡢ࡫࡮ࡺ࡟ࡥ࡫ࡵࠦᮅ"): bstack11l111ll1ll_opy_,
            bstack1ll_opy_ (u"ࠦࡼࡵࡲ࡬ࡶࡵࡩࡪࡥࡧࡪࡶࡢࡨ࡮ࡸࠢᮆ"): subprocess.check_output([bstack1ll_opy_ (u"ࠧ࡭ࡩࡵࠤᮇ"), bstack1ll_opy_ (u"ࠨࡲࡦࡸ࠰ࡴࡦࡸࡳࡦࠤᮈ"), bstack1ll_opy_ (u"ࠢ࠮࠯ࡪ࡭ࡹ࠳ࡣࡰ࡯ࡰࡳࡳ࠳ࡤࡪࡴࠥᮉ")]).strip().decode(
                bstack1ll_opy_ (u"ࠨࡷࡷࡪ࠲࠾ࠧᮊ")),
            bstack1ll_opy_ (u"ࠤ࡯ࡥࡸࡺ࡟ࡵࡣࡪࠦᮋ"): repo.git.describe(tags=True, abbrev=0, always=True),
            bstack1ll_opy_ (u"ࠥࡧࡴࡳ࡭ࡪࡶࡶࡣࡸ࡯࡮ࡤࡧࡢࡰࡦࡹࡴࡠࡶࡤ࡫ࠧᮌ"): repo.git.rev_list(
                bstack1ll_opy_ (u"ࠦࢀࢃ࠮࠯ࡽࢀࠦᮍ").format(repo.head.commit, repo.git.describe(tags=True, abbrev=0, always=True)), count=True)
        }
        remotes = repo.remotes
        bstack11l111111ll_opy_ = []
        for remote in remotes:
            bstack111lll1l11l_opy_ = {
                bstack1ll_opy_ (u"ࠧࡴࡡ࡮ࡧࠥᮎ"): remote.name,
                bstack1ll_opy_ (u"ࠨࡵࡳ࡮ࠥᮏ"): remote.url,
            }
            bstack11l111111ll_opy_.append(bstack111lll1l11l_opy_)
        bstack111lll11ll1_opy_ = {
            bstack1ll_opy_ (u"ࠢ࡯ࡣࡰࡩࠧᮐ"): bstack1ll_opy_ (u"ࠣࡩ࡬ࡸࠧᮑ"),
            **info,
            bstack1ll_opy_ (u"ࠤࡵࡩࡲࡵࡴࡦࡵࠥᮒ"): bstack11l111111ll_opy_
        }
        bstack111lll11ll1_opy_ = bstack111ll1l1l11_opy_(bstack111lll11ll1_opy_)
        return bstack111lll11ll1_opy_
    except git.InvalidGitRepositoryError:
        return {}
    except Exception as err:
        print(bstack1ll_opy_ (u"ࠥࡉࡽࡩࡥࡱࡶ࡬ࡳࡳࠦࡩ࡯ࠢࡳࡳࡵࡻ࡬ࡢࡶ࡬ࡲ࡬ࠦࡇࡪࡶࠣࡱࡪࡺࡡࡥࡣࡷࡥࠥࡽࡩࡵࡪࠣࡩࡷࡸ࡯ࡳ࠼ࠣࡿࢂࠨᮓ").format(err))
        return {}
def bstack111ll111ll1_opy_(bstack111l1l1llll_opy_=None):
    bstack1ll_opy_ (u"ࠦࠧࠨࠊࠡࠢࠣࠤࡌ࡫ࡴࠡࡩ࡬ࡸࠥࡳࡥࡵࡣࡧࡥࡹࡧࠠࡴࡲࡨࡧ࡮࡬ࡩࡤࡣ࡯ࡰࡾࠦࡦࡰࡴࡰࡥࡹࡺࡥࡥࠢࡩࡳࡷࠦࡁࡊࠢࡶࡩࡱ࡫ࡣࡵ࡫ࡲࡲࠥࡻࡳࡦࠢࡦࡥࡸ࡫ࡳࠡࡨࡲࡶࠥ࡫ࡡࡤࡪࠣࡪࡴࡲࡤࡦࡴࠣ࡭ࡳࠦࡴࡩࡧࠣࡰ࡮ࡹࡴ࠯ࠌࠣࠤࠥࠦࡁࡳࡩࡶ࠾ࠏࠦࠠࠡࠢࠣࠤࠥࠦࡦࡰ࡮ࡧࡩࡷࡹࠠࠩ࡮࡬ࡷࡹ࠲ࠠࡰࡲࡷ࡭ࡴࡴࡡ࡭ࠫ࠽ࠤࠏࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣ࠱ࠥࡔ࡯࡯ࡧ࠽ࠤࡒࡵ࡮ࡰ࠯ࡵࡩࡵࡵࠠࡢࡲࡳࡶࡴࡧࡣࡩ࠮ࠣࡹࡸ࡫ࡳࠡࡥࡸࡶࡷ࡫࡮ࡵࠢࡧ࡭ࡷ࡫ࡣࡵࡱࡵࡽࠥࡡ࡯ࡴ࠰ࡪࡩࡹࡩࡷࡥࠪࠬࡡࠏࠦࠠࠡࠢࠣࠤࠥࠦࠠࠡࠢࠣ࠱ࠥࡋ࡭ࡱࡶࡼࠤࡱ࡯ࡳࡵࠢ࡞ࡡ࠿ࠦࡍࡶ࡮ࡷ࡭࠲ࡸࡥࡱࡱࠣࡥࡵࡶࡲࡰࡣࡦ࡬ࠥࡽࡩࡵࡪࠣࡲࡴࠦࡳࡰࡷࡵࡧࡪࡹࠠࡤࡱࡱࡪ࡮࡭ࡵࡳࡧࡧ࠰ࠥࡸࡥࡵࡷࡵࡲࡸ࡛ࠦ࡞ࠌࠣࠤࠥࠦࠠࠡࠢࠣࠤࠥࠦࠠ࠮ࠢࡏ࡭ࡸࡺࠠࡰࡨࠣࡴࡦࡺࡨࡴ࠼ࠣࡑࡺࡲࡴࡪ࠯ࡵࡩࡵࡵࠠࡢࡲࡳࡶࡴࡧࡣࡩࠢࡺ࡭ࡹ࡮ࠠࡴࡲࡨࡧ࡮࡬ࡩࡤࠢࡩࡳࡱࡪࡥࡳࡵࠣࡸࡴࠦࡡ࡯ࡣ࡯ࡽࡿ࡫ࠊࠡࠢࠣࠤࡗ࡫ࡴࡶࡴࡱࡷ࠿ࠐࠠࠡࠢࠣࠤࠥࠦࠠ࡭࡫ࡶࡸ࠿ࠦࡌࡪࡵࡷࠤࡴ࡬ࠠࡥ࡫ࡦࡸࡸ࠲ࠠࡦࡣࡦ࡬ࠥࡩ࡯࡯ࡶࡤ࡭ࡳ࡯࡮ࡨࠢࡪ࡭ࡹࠦ࡭ࡦࡶࡤࡨࡦࡺࡡࠡࡨࡲࡶࠥࡧࠠࡧࡱ࡯ࡨࡪࡸ࠮ࠋࠢࠣࠤࠥࠨࠢࠣᮔ")
    if bstack111l1l1llll_opy_ is None:
        bstack111l1l1llll_opy_ = [os.getcwd()]
    elif isinstance(bstack111l1l1llll_opy_, list) and len(bstack111l1l1llll_opy_) == 0:
        return []
    results = []
    for folder in bstack111l1l1llll_opy_:
        try:
            if not os.path.exists(folder):
                raise Exception(bstack1ll_opy_ (u"ࠧࡌ࡯࡭ࡦࡨࡶࠥࡪ࡯ࡦࡵࠣࡲࡴࡺࠠࡦࡺ࡬ࡷࡹࡀࠠࡼࡿࠥᮕ").format(folder))
            repo = git.Repo(folder, search_parent_directories=True)
            result = {
                bstack1ll_opy_ (u"ࠨࡰࡳࡋࡧࠦᮖ"): bstack1ll_opy_ (u"ࠢࠣᮗ"),
                bstack1ll_opy_ (u"ࠣࡨ࡬ࡰࡪࡹࡃࡩࡣࡱ࡫ࡪࡪࠢᮘ"): [],
                bstack1ll_opy_ (u"ࠤࡤࡹࡹ࡮࡯ࡳࡵࠥᮙ"): [],
                bstack1ll_opy_ (u"ࠥࡴࡷࡊࡡࡵࡧࠥᮚ"): bstack1ll_opy_ (u"ࠦࠧᮛ"),
                bstack1ll_opy_ (u"ࠧࡩ࡯࡮࡯࡬ࡸࡒ࡫ࡳࡴࡣࡪࡩࡸࠨᮜ"): [],
                bstack1ll_opy_ (u"ࠨࡰࡳࡖ࡬ࡸࡱ࡫ࠢᮝ"): bstack1ll_opy_ (u"ࠢࠣᮞ"),
                bstack1ll_opy_ (u"ࠣࡲࡵࡈࡪࡹࡣࡳ࡫ࡳࡸ࡮ࡵ࡮ࠣᮟ"): bstack1ll_opy_ (u"ࠤࠥᮠ"),
                bstack1ll_opy_ (u"ࠥࡴࡷࡘࡡࡸࡆ࡬ࡪ࡫ࠨᮡ"): bstack1ll_opy_ (u"ࠦࠧᮢ")
            }
            bstack111lll1l1ll_opy_ = repo.active_branch.name
            bstack111ll11l1l1_opy_ = repo.head.commit
            result[bstack1ll_opy_ (u"ࠧࡶࡲࡊࡦࠥᮣ")] = bstack111ll11l1l1_opy_.hexsha
            bstack11l11l1111l_opy_ = _111l1ll1lll_opy_(repo)
            logger.debug(bstack1ll_opy_ (u"ࠨࡂࡢࡵࡨࠤࡧࡸࡡ࡯ࡥ࡫ࠤ࡫ࡵࡲࠡࡥࡲࡱࡵࡧࡲࡪࡵࡲࡲ࠿ࠦࠢᮤ") + str(bstack11l11l1111l_opy_) + bstack1ll_opy_ (u"ࠢࠣᮥ"))
            if bstack11l11l1111l_opy_:
                try:
                    bstack111lll11l1l_opy_ = repo.git.diff(bstack1ll_opy_ (u"ࠣ࠯࠰ࡲࡦࡳࡥ࠮ࡱࡱࡰࡾࠨᮦ"), bstack1ll1ll111ll_opy_ (u"ࠤࡾࡦࡦࡹࡥࡠࡤࡵࡥࡳࡩࡨࡾ࠰࠱࠲ࢀࡩࡵࡳࡴࡨࡲࡹࡥࡢࡳࡣࡱࡧ࡭ࢃࠢᮧ")).split(bstack1ll_opy_ (u"ࠪࡠࡳ࠭ᮨ"))
                    logger.debug(bstack1ll_opy_ (u"ࠦࡈ࡮ࡡ࡯ࡩࡨࡨࠥ࡬ࡩ࡭ࡧࡶࠤࡧ࡫ࡴࡸࡧࡨࡲࠥࢁࡢࡢࡵࡨࡣࡧࡸࡡ࡯ࡥ࡫ࢁࠥࡧ࡮ࡥࠢࡾࡧࡺࡸࡲࡦࡰࡷࡣࡧࡸࡡ࡯ࡥ࡫ࢁ࠿ࠦࠢᮩ") + str(bstack111lll11l1l_opy_) + bstack1ll_opy_ (u"ࠧࠨ᮪"))
                    result[bstack1ll_opy_ (u"ࠨࡦࡪ࡮ࡨࡷࡈ࡮ࡡ࡯ࡩࡨࡨ᮫ࠧ")] = [f.strip() for f in bstack111lll11l1l_opy_ if f.strip()]
                    commits = list(repo.iter_commits(bstack1ll1ll111ll_opy_ (u"ࠢࡼࡤࡤࡷࡪࡥࡢࡳࡣࡱࡧ࡭ࢃ࠮࠯ࡽࡦࡹࡷࡸࡥ࡯ࡶࡢࡦࡷࡧ࡮ࡤࡪࢀࠦᮬ")))
                except Exception:
                    logger.debug(bstack1ll_opy_ (u"ࠣࡈࡤ࡭ࡱ࡫ࡤࠡࡶࡲࠤ࡬࡫ࡴࠡࡥ࡫ࡥࡳ࡭ࡥࡥࠢࡩ࡭ࡱ࡫ࡳࠡࡨࡵࡳࡲࠦࡢࡳࡣࡱࡧ࡭ࠦࡣࡰ࡯ࡳࡥࡷ࡯ࡳࡰࡰ࠱ࠤࡋࡧ࡬࡭࡫ࡱ࡫ࠥࡨࡡࡤ࡭ࠣࡸࡴࠦࡲࡦࡥࡨࡲࡹࠦࡣࡰ࡯ࡰ࡭ࡹࡹ࠮ࠣᮭ"))
                    commits = list(repo.iter_commits(max_count=10))
                    if commits:
                        result[bstack1ll_opy_ (u"ࠤࡩ࡭ࡱ࡫ࡳࡄࡪࡤࡲ࡬࡫ࡤࠣᮮ")] = _111ll1lll11_opy_(commits[:5])
            else:
                commits = list(repo.iter_commits(max_count=10))
                if commits:
                    result[bstack1ll_opy_ (u"ࠥࡪ࡮ࡲࡥࡴࡅ࡫ࡥࡳ࡭ࡥࡥࠤᮯ")] = _111ll1lll11_opy_(commits[:5])
            bstack11l1111l11l_opy_ = set()
            bstack111llll111l_opy_ = []
            for commit in commits:
                logger.debug(bstack1ll_opy_ (u"ࠦࡕࡸ࡯ࡤࡧࡶࡷ࡮ࡴࡧࠡࡥࡲࡱࡲ࡯ࡴ࠻ࠢࠥ᮰") + str(commit.message) + bstack1ll_opy_ (u"ࠧࠨ᮱"))
                bstack111llll11ll_opy_ = commit.author.name if commit.author else bstack1ll_opy_ (u"ࠨࡕ࡯࡭ࡱࡳࡼࡴࠢ᮲")
                bstack11l1111l11l_opy_.add(bstack111llll11ll_opy_)
                bstack111llll111l_opy_.append({
                    bstack1ll_opy_ (u"ࠢ࡮ࡧࡶࡷࡦ࡭ࡥࠣ᮳"): commit.message.strip(),
                    bstack1ll_opy_ (u"ࠣࡷࡶࡩࡷࠨ᮴"): bstack111llll11ll_opy_
                })
            result[bstack1ll_opy_ (u"ࠤࡤࡹࡹ࡮࡯ࡳࡵࠥ᮵")] = list(bstack11l1111l11l_opy_)
            result[bstack1ll_opy_ (u"ࠥࡧࡴࡳ࡭ࡪࡶࡐࡩࡸࡹࡡࡨࡧࡶࠦ᮶")] = bstack111llll111l_opy_
            result[bstack1ll_opy_ (u"ࠦࡵࡸࡄࡢࡶࡨࠦ᮷")] = bstack111ll11l1l1_opy_.committed_datetime.strftime(bstack1ll_opy_ (u"࡙ࠧࠫ࠮ࠧࡰ࠱ࠪࡪࠢ᮸"))
            if (not result[bstack1ll_opy_ (u"ࠨࡰࡳࡖ࡬ࡸࡱ࡫ࠢ᮹")] or result[bstack1ll_opy_ (u"ࠢࡱࡴࡗ࡭ࡹࡲࡥࠣᮺ")].strip() == bstack1ll_opy_ (u"ࠣࠤᮻ")) and bstack111ll11l1l1_opy_.message:
                bstack111l1ll1ll1_opy_ = bstack111ll11l1l1_opy_.message.strip().splitlines()
                result[bstack1ll_opy_ (u"ࠤࡳࡶ࡙࡯ࡴ࡭ࡧࠥᮼ")] = bstack111l1ll1ll1_opy_[0] if bstack111l1ll1ll1_opy_ else bstack1ll_opy_ (u"ࠥࠦᮽ")
                if len(bstack111l1ll1ll1_opy_) > 2:
                    result[bstack1ll_opy_ (u"ࠦࡵࡸࡄࡦࡵࡦࡶ࡮ࡶࡴࡪࡱࡱࠦᮾ")] = bstack1ll_opy_ (u"ࠬࡢ࡮ࠨᮿ").join(bstack111l1ll1ll1_opy_[2:]).strip()
            results.append(result)
        except Exception as err:
            logger.error(bstack1ll_opy_ (u"ࠨࡅࡹࡥࡨࡴࡹ࡯࡯࡯ࠢ࡬ࡲࠥࡶ࡯ࡱࡷ࡯ࡥࡹ࡯࡮ࡨࠢࡊ࡭ࡹࠦ࡭ࡦࡶࡤࡨࡦࡺࡡࠡࡨࡲࡶࠥࡇࡉࠡࡵࡨࡰࡪࡩࡴࡪࡱࡱࠤ࠭࡬࡯࡭ࡦࡨࡶ࠿ࠦࡻࡾࠫ࠽ࠤࢀࢃࠠ࠮ࠢࡾࢁࠧᯀ").format(
                folder,
                type(err).__name__,
                str(err)
            ))
    filtered_results = [
        result
        for result in results
        if _11l1111l111_opy_(result)
    ]
    return filtered_results
def _11l1111l111_opy_(result):
    bstack1ll_opy_ (u"ࠢࠣࠤࠍࠤࠥࠦࠠࡉࡧ࡯ࡴࡪࡸࠠࡵࡱࠣࡧ࡭࡫ࡣ࡬ࠢ࡬ࡪࠥࡧࠠࡨ࡫ࡷࠤࡲ࡫ࡴࡢࡦࡤࡸࡦࠦࡲࡦࡵࡸࡰࡹࠦࡩࡴࠢࡹࡥࡱ࡯ࡤࠡࠪࡱࡳࡳ࠳ࡥ࡮ࡲࡷࡽࠥ࡬ࡩ࡭ࡧࡶࡇ࡭ࡧ࡮ࡨࡧࡧࠤࡦࡴࡤࠡࡣࡸࡸ࡭ࡵࡲࡴࠫ࠱ࠎࠥࠦࠠࠡࠤࠥࠦᯁ")
    return (
        isinstance(result.get(bstack1ll_opy_ (u"ࠣࡨ࡬ࡰࡪࡹࡃࡩࡣࡱ࡫ࡪࡪࠢᯂ"), None), list)
        and len(result[bstack1ll_opy_ (u"ࠤࡩ࡭ࡱ࡫ࡳࡄࡪࡤࡲ࡬࡫ࡤࠣᯃ")]) > 0
        and isinstance(result.get(bstack1ll_opy_ (u"ࠥࡥࡺࡺࡨࡰࡴࡶࠦᯄ"), None), list)
        and len(result[bstack1ll_opy_ (u"ࠦࡦࡻࡴࡩࡱࡵࡷࠧᯅ")]) > 0
    )
def _111l1ll1lll_opy_(repo):
    bstack1ll_opy_ (u"ࠧࠨࠢࠋࠢࠣࠤ࡚ࠥࡲࡺࠢࡷࡳࠥࡪࡥࡵࡧࡵࡱ࡮ࡴࡥࠡࡶ࡫ࡩࠥࡨࡡࡴࡧࠣࡦࡷࡧ࡮ࡤࡪࠣࡪࡴࡸࠠࡵࡪࡨࠤ࡬࡯ࡶࡦࡰࠣࡶࡪࡶ࡯ࠡࡹ࡬ࡸ࡭ࡵࡵࡵࠢ࡫ࡥࡷࡪࡣࡰࡦࡨࡨࠥࡴࡡ࡮ࡧࡶࠤࡦࡴࡤࠡࡹࡲࡶࡰࠦࡷࡪࡶ࡫ࠤࡦࡲ࡬ࠡࡘࡆࡗࠥࡶࡲࡰࡸ࡬ࡨࡪࡸࡳ࠯ࠌࠣࠤࠥࠦࡒࡦࡶࡸࡶࡳࡹࠠࡵࡪࡨࠤࡩ࡫ࡦࡢࡷ࡯ࡸࠥࡨࡲࡢࡰࡦ࡬ࠥ࡯ࡦࠡࡲࡲࡷࡸ࡯ࡢ࡭ࡧ࠯ࠤࡪࡲࡳࡦࠢࡑࡳࡳ࡫࠮ࠋࠢࠣࠤࠥࠨࠢࠣᯆ")
    try:
        try:
            origin = repo.remotes.origin
            bstack111ll1l11ll_opy_ = origin.refs[bstack1ll_opy_ (u"࠭ࡈࡆࡃࡇࠫᯇ")]
            target = bstack111ll1l11ll_opy_.reference.name
            if target.startswith(bstack1ll_opy_ (u"ࠧࡰࡴ࡬࡫࡮ࡴ࠯ࠨᯈ")):
                return target
        except Exception:
            pass
        if repo.remotes and repo.remotes.origin.refs:
            for ref in repo.remotes.origin.refs:
                if ref.name.startswith(bstack1ll_opy_ (u"ࠨࡱࡵ࡭࡬࡯࡮࠰ࠩᯉ")):
                    return ref.name
        if repo.heads:
            return repo.heads[0].name
    except Exception:
        pass
    return None
def _111ll1lll11_opy_(commits):
    bstack1ll_opy_ (u"ࠤࠥࠦࠏࠦࠠࠡࠢࡊࡩࡹࠦ࡬ࡪࡵࡷࠤࡴ࡬ࠠࡤࡪࡤࡲ࡬࡫ࡤࠡࡨ࡬ࡰࡪࡹࠠࡧࡴࡲࡱࠥࡧࠠ࡭࡫ࡶࡸࠥࡵࡦࠡࡥࡲࡱࡲ࡯ࡴࡴ࠰ࠍࠤࠥࠦࠠࠣࠤࠥᯊ")
    bstack111lll11l1l_opy_ = set()
    try:
        for commit in commits:
            if commit.parents:
                for parent in commit.parents:
                    diff = commit.diff(parent)
                    for bstack111ll11llll_opy_ in diff:
                        if bstack111ll11llll_opy_.a_path:
                            bstack111lll11l1l_opy_.add(bstack111ll11llll_opy_.a_path)
                        if bstack111ll11llll_opy_.b_path:
                            bstack111lll11l1l_opy_.add(bstack111ll11llll_opy_.b_path)
    except Exception:
        pass
    return list(bstack111lll11l1l_opy_)
def bstack111ll1l1l11_opy_(bstack111lll11ll1_opy_):
    bstack111ll1l1111_opy_ = bstack111lll111ll_opy_(bstack111lll11ll1_opy_)
    if bstack111ll1l1111_opy_ and bstack111ll1l1111_opy_ > bstack11l11llll1l_opy_:
        bstack111llll1l1l_opy_ = bstack111ll1l1111_opy_ - bstack11l11llll1l_opy_
        bstack11l1111l1ll_opy_ = bstack111lll1l111_opy_(bstack111lll11ll1_opy_[bstack1ll_opy_ (u"ࠥࡧࡴࡳ࡭ࡪࡶࡢࡱࡪࡹࡳࡢࡩࡨࠦᯋ")], bstack111llll1l1l_opy_)
        bstack111lll11ll1_opy_[bstack1ll_opy_ (u"ࠦࡨࡵ࡭࡮࡫ࡷࡣࡲ࡫ࡳࡴࡣࡪࡩࠧᯌ")] = bstack11l1111l1ll_opy_
        logger.info(bstack1ll_opy_ (u"࡚ࠧࡨࡦࠢࡦࡳࡲࡳࡩࡵࠢ࡫ࡥࡸࠦࡢࡦࡧࡱࠤࡹࡸࡵ࡯ࡥࡤࡸࡪࡪ࠮ࠡࡕ࡬ࡾࡪࠦ࡯ࡧࠢࡦࡳࡲࡳࡩࡵࠢࡤࡪࡹ࡫ࡲࠡࡶࡵࡹࡳࡩࡡࡵ࡫ࡲࡲࠥ࡯ࡳࠡࡽࢀࠤࡐࡈࠢᯍ")
                    .format(bstack111lll111ll_opy_(bstack111lll11ll1_opy_) / 1024))
    return bstack111lll11ll1_opy_
def bstack111lll111ll_opy_(bstack1l1l11ll1_opy_):
    try:
        if bstack1l1l11ll1_opy_:
            bstack11l11111l11_opy_ = json.dumps(bstack1l1l11ll1_opy_)
            bstack111ll111lll_opy_ = sys.getsizeof(bstack11l11111l11_opy_)
            return bstack111ll111lll_opy_
    except Exception as e:
        logger.debug(bstack1ll_opy_ (u"ࠨࡓࡰ࡯ࡨࡸ࡭࡯࡮ࡨࠢࡺࡩࡳࡺࠠࡸࡴࡲࡲ࡬ࠦࡷࡩ࡫࡯ࡩࠥࡩࡡ࡭ࡥࡸࡰࡦࡺࡩ࡯ࡩࠣࡷ࡮ࢀࡥࠡࡱࡩࠤࡏ࡙ࡏࡏࠢࡲࡦ࡯࡫ࡣࡵ࠼ࠣࡿࢂࠨᯎ").format(e))
    return -1
def bstack111lll1l111_opy_(field, bstack111l1ll1111_opy_):
    try:
        bstack111ll1111l1_opy_ = len(bytes(bstack11l1l11llll_opy_, bstack1ll_opy_ (u"ࠧࡶࡶࡩ࠱࠽࠭ᯏ")))
        bstack111ll1ll1l1_opy_ = bytes(field, bstack1ll_opy_ (u"ࠨࡷࡷࡪ࠲࠾ࠧᯐ"))
        bstack111lll11lll_opy_ = len(bstack111ll1ll1l1_opy_)
        bstack111ll11l11l_opy_ = ceil(bstack111lll11lll_opy_ - bstack111l1ll1111_opy_ - bstack111ll1111l1_opy_)
        if bstack111ll11l11l_opy_ > 0:
            bstack111llllll11_opy_ = bstack111ll1ll1l1_opy_[:bstack111ll11l11l_opy_].decode(bstack1ll_opy_ (u"ࠩࡸࡸ࡫࠳࠸ࠨᯑ"), errors=bstack1ll_opy_ (u"ࠪ࡭࡬ࡴ࡯ࡳࡧࠪᯒ")) + bstack11l1l11llll_opy_
            return bstack111llllll11_opy_
    except Exception as e:
        logger.debug(bstack1ll_opy_ (u"ࠦࡊࡸࡲࡰࡴࠣࡻ࡭࡯࡬ࡦࠢࡷࡶࡺࡴࡣࡢࡶ࡬ࡲ࡬ࠦࡦࡪࡧ࡯ࡨ࠱ࠦ࡮ࡰࡶ࡫࡭ࡳ࡭ࠠࡸࡣࡶࠤࡹࡸࡵ࡯ࡥࡤࡸࡪࡪࠠࡩࡧࡵࡩ࠿ࠦࡻࡾࠤᯓ").format(e))
    return field
def bstack1ll1ll1l_opy_():
    env = os.environ
    if (bstack1ll_opy_ (u"ࠧࡐࡅࡏࡍࡌࡒࡘࡥࡕࡓࡎࠥᯔ") in env and len(env[bstack1ll_opy_ (u"ࠨࡊࡆࡐࡎࡍࡓ࡙࡟ࡖࡔࡏࠦᯕ")]) > 0) or (
            bstack1ll_opy_ (u"ࠢࡋࡇࡑࡏࡎࡔࡓࡠࡊࡒࡑࡊࠨᯖ") in env and len(env[bstack1ll_opy_ (u"ࠣࡌࡈࡒࡐࡏࡎࡔࡡࡋࡓࡒࡋࠢᯗ")]) > 0):
        return {
            bstack1ll_opy_ (u"ࠤࡱࡥࡲ࡫ࠢᯘ"): bstack1ll_opy_ (u"ࠥࡎࡪࡴ࡫ࡪࡰࡶࠦᯙ"),
            bstack1ll_opy_ (u"ࠦࡧࡻࡩ࡭ࡦࡢࡹࡷࡲࠢᯚ"): env.get(bstack1ll_opy_ (u"ࠧࡈࡕࡊࡎࡇࡣ࡚ࡘࡌࠣᯛ")),
            bstack1ll_opy_ (u"ࠨࡪࡰࡤࡢࡲࡦࡳࡥࠣᯜ"): env.get(bstack1ll_opy_ (u"ࠢࡋࡑࡅࡣࡓࡇࡍࡆࠤᯝ")),
            bstack1ll_opy_ (u"ࠣࡤࡸ࡭ࡱࡪ࡟࡯ࡷࡰࡦࡪࡸࠢᯞ"): env.get(bstack1ll_opy_ (u"ࠤࡅ࡙ࡎࡒࡄࡠࡐࡘࡑࡇࡋࡒࠣᯟ"))
        }
    if env.get(bstack1ll_opy_ (u"ࠥࡇࡎࠨᯠ")) == bstack1ll_opy_ (u"ࠦࡹࡸࡵࡦࠤᯡ") and bstack11l11lllll_opy_(env.get(bstack1ll_opy_ (u"ࠧࡉࡉࡓࡅࡏࡉࡈࡏࠢᯢ"))):
        return {
            bstack1ll_opy_ (u"ࠨ࡮ࡢ࡯ࡨࠦᯣ"): bstack1ll_opy_ (u"ࠢࡄ࡫ࡵࡧࡱ࡫ࡃࡊࠤᯤ"),
            bstack1ll_opy_ (u"ࠣࡤࡸ࡭ࡱࡪ࡟ࡶࡴ࡯ࠦᯥ"): env.get(bstack1ll_opy_ (u"ࠤࡆࡍࡗࡉࡌࡆࡡࡅ࡙ࡎࡒࡄࡠࡗࡕࡐ᯦ࠧ")),
            bstack1ll_opy_ (u"ࠥ࡮ࡴࡨ࡟࡯ࡣࡰࡩࠧᯧ"): env.get(bstack1ll_opy_ (u"ࠦࡈࡏࡒࡄࡎࡈࡣࡏࡕࡂࠣᯨ")),
            bstack1ll_opy_ (u"ࠧࡨࡵࡪ࡮ࡧࡣࡳࡻ࡭ࡣࡧࡵࠦᯩ"): env.get(bstack1ll_opy_ (u"ࠨࡃࡊࡔࡆࡐࡊࡥࡂࡖࡋࡏࡈࡤࡔࡕࡎࠤᯪ"))
        }
    if env.get(bstack1ll_opy_ (u"ࠢࡄࡋࠥᯫ")) == bstack1ll_opy_ (u"ࠣࡶࡵࡹࡪࠨᯬ") and bstack11l11lllll_opy_(env.get(bstack1ll_opy_ (u"ࠤࡗࡖࡆ࡜ࡉࡔࠤᯭ"))):
        return {
            bstack1ll_opy_ (u"ࠥࡲࡦࡳࡥࠣᯮ"): bstack1ll_opy_ (u"࡙ࠦࡸࡡࡷ࡫ࡶࠤࡈࡏࠢᯯ"),
            bstack1ll_opy_ (u"ࠧࡨࡵࡪ࡮ࡧࡣࡺࡸ࡬ࠣᯰ"): env.get(bstack1ll_opy_ (u"ࠨࡔࡓࡃ࡙ࡍࡘࡥࡂࡖࡋࡏࡈࡤ࡝ࡅࡃࡡࡘࡖࡑࠨᯱ")),
            bstack1ll_opy_ (u"ࠢ࡫ࡱࡥࡣࡳࡧ࡭ࡦࠤ᯲"): env.get(bstack1ll_opy_ (u"ࠣࡖࡕࡅ࡛ࡏࡓࡠࡌࡒࡆࡤࡔࡁࡎࡇ᯳ࠥ")),
            bstack1ll_opy_ (u"ࠤࡥࡹ࡮ࡲࡤࡠࡰࡸࡱࡧ࡫ࡲࠣ᯴"): env.get(bstack1ll_opy_ (u"ࠥࡘࡗࡇࡖࡊࡕࡢࡆ࡚ࡏࡌࡅࡡࡑ࡙ࡒࡈࡅࡓࠤ᯵"))
        }
    if env.get(bstack1ll_opy_ (u"ࠦࡈࡏࠢ᯶")) == bstack1ll_opy_ (u"ࠧࡺࡲࡶࡧࠥ᯷") and env.get(bstack1ll_opy_ (u"ࠨࡃࡊࡡࡑࡅࡒࡋࠢ᯸")) == bstack1ll_opy_ (u"ࠢࡤࡱࡧࡩࡸ࡮ࡩࡱࠤ᯹"):
        return {
            bstack1ll_opy_ (u"ࠣࡰࡤࡱࡪࠨ᯺"): bstack1ll_opy_ (u"ࠤࡆࡳࡩ࡫ࡳࡩ࡫ࡳࠦ᯻"),
            bstack1ll_opy_ (u"ࠥࡦࡺ࡯࡬ࡥࡡࡸࡶࡱࠨ᯼"): None,
            bstack1ll_opy_ (u"ࠦ࡯ࡵࡢࡠࡰࡤࡱࡪࠨ᯽"): None,
            bstack1ll_opy_ (u"ࠧࡨࡵࡪ࡮ࡧࡣࡳࡻ࡭ࡣࡧࡵࠦ᯾"): None
        }
    if env.get(bstack1ll_opy_ (u"ࠨࡂࡊࡖࡅ࡙ࡈࡑࡅࡕࡡࡅࡖࡆࡔࡃࡉࠤ᯿")) and env.get(bstack1ll_opy_ (u"ࠢࡃࡋࡗࡆ࡚ࡉࡋࡆࡖࡢࡇࡔࡓࡍࡊࡖࠥᰀ")):
        return {
            bstack1ll_opy_ (u"ࠣࡰࡤࡱࡪࠨᰁ"): bstack1ll_opy_ (u"ࠤࡅ࡭ࡹࡨࡵࡤ࡭ࡨࡸࠧᰂ"),
            bstack1ll_opy_ (u"ࠥࡦࡺ࡯࡬ࡥࡡࡸࡶࡱࠨᰃ"): env.get(bstack1ll_opy_ (u"ࠦࡇࡏࡔࡃࡗࡆࡏࡊ࡚࡟ࡈࡋࡗࡣࡍ࡚ࡔࡑࡡࡒࡖࡎࡍࡉࡏࠤᰄ")),
            bstack1ll_opy_ (u"ࠧࡰ࡯ࡣࡡࡱࡥࡲ࡫ࠢᰅ"): None,
            bstack1ll_opy_ (u"ࠨࡢࡶ࡫࡯ࡨࡤࡴࡵ࡮ࡤࡨࡶࠧᰆ"): env.get(bstack1ll_opy_ (u"ࠢࡃࡋࡗࡆ࡚ࡉࡋࡆࡖࡢࡆ࡚ࡏࡌࡅࡡࡑ࡙ࡒࡈࡅࡓࠤᰇ"))
        }
    if env.get(bstack1ll_opy_ (u"ࠣࡅࡌࠦᰈ")) == bstack1ll_opy_ (u"ࠤࡷࡶࡺ࡫ࠢᰉ") and bstack11l11lllll_opy_(env.get(bstack1ll_opy_ (u"ࠥࡈࡗࡕࡎࡆࠤᰊ"))):
        return {
            bstack1ll_opy_ (u"ࠦࡳࡧ࡭ࡦࠤᰋ"): bstack1ll_opy_ (u"ࠧࡊࡲࡰࡰࡨࠦᰌ"),
            bstack1ll_opy_ (u"ࠨࡢࡶ࡫࡯ࡨࡤࡻࡲ࡭ࠤᰍ"): env.get(bstack1ll_opy_ (u"ࠢࡅࡔࡒࡒࡊࡥࡂࡖࡋࡏࡈࡤࡒࡉࡏࡍࠥᰎ")),
            bstack1ll_opy_ (u"ࠣ࡬ࡲࡦࡤࡴࡡ࡮ࡧࠥᰏ"): None,
            bstack1ll_opy_ (u"ࠤࡥࡹ࡮ࡲࡤࡠࡰࡸࡱࡧ࡫ࡲࠣᰐ"): env.get(bstack1ll_opy_ (u"ࠥࡈࡗࡕࡎࡆࡡࡅ࡙ࡎࡒࡄࡠࡐࡘࡑࡇࡋࡒࠣᰑ"))
        }
    if env.get(bstack1ll_opy_ (u"ࠦࡈࡏࠢᰒ")) == bstack1ll_opy_ (u"ࠧࡺࡲࡶࡧࠥᰓ") and bstack11l11lllll_opy_(env.get(bstack1ll_opy_ (u"ࠨࡓࡆࡏࡄࡔࡍࡕࡒࡆࠤᰔ"))):
        return {
            bstack1ll_opy_ (u"ࠢ࡯ࡣࡰࡩࠧᰕ"): bstack1ll_opy_ (u"ࠣࡕࡨࡱࡦࡶࡨࡰࡴࡨࠦᰖ"),
            bstack1ll_opy_ (u"ࠤࡥࡹ࡮ࡲࡤࡠࡷࡵࡰࠧᰗ"): env.get(bstack1ll_opy_ (u"ࠥࡗࡊࡓࡁࡑࡊࡒࡖࡊࡥࡏࡓࡉࡄࡒࡎࡠࡁࡕࡋࡒࡒࡤ࡛ࡒࡍࠤᰘ")),
            bstack1ll_opy_ (u"ࠦ࡯ࡵࡢࡠࡰࡤࡱࡪࠨᰙ"): env.get(bstack1ll_opy_ (u"࡙ࠧࡅࡎࡃࡓࡌࡔࡘࡅࡠࡌࡒࡆࡤࡔࡁࡎࡇࠥᰚ")),
            bstack1ll_opy_ (u"ࠨࡢࡶ࡫࡯ࡨࡤࡴࡵ࡮ࡤࡨࡶࠧᰛ"): env.get(bstack1ll_opy_ (u"ࠢࡔࡇࡐࡅࡕࡎࡏࡓࡇࡢࡎࡔࡈ࡟ࡊࡆࠥᰜ"))
        }
    if env.get(bstack1ll_opy_ (u"ࠣࡅࡌࠦᰝ")) == bstack1ll_opy_ (u"ࠤࡷࡶࡺ࡫ࠢᰞ") and bstack11l11lllll_opy_(env.get(bstack1ll_opy_ (u"ࠥࡋࡎ࡚ࡌࡂࡄࡢࡇࡎࠨᰟ"))):
        return {
            bstack1ll_opy_ (u"ࠦࡳࡧ࡭ࡦࠤᰠ"): bstack1ll_opy_ (u"ࠧࡍࡩࡵࡎࡤࡦࠧᰡ"),
            bstack1ll_opy_ (u"ࠨࡢࡶ࡫࡯ࡨࡤࡻࡲ࡭ࠤᰢ"): env.get(bstack1ll_opy_ (u"ࠢࡄࡋࡢࡎࡔࡈ࡟ࡖࡔࡏࠦᰣ")),
            bstack1ll_opy_ (u"ࠣ࡬ࡲࡦࡤࡴࡡ࡮ࡧࠥᰤ"): env.get(bstack1ll_opy_ (u"ࠤࡆࡍࡤࡐࡏࡃࡡࡑࡅࡒࡋࠢᰥ")),
            bstack1ll_opy_ (u"ࠥࡦࡺ࡯࡬ࡥࡡࡱࡹࡲࡨࡥࡳࠤᰦ"): env.get(bstack1ll_opy_ (u"ࠦࡈࡏ࡟ࡋࡑࡅࡣࡎࡊࠢᰧ"))
        }
    if env.get(bstack1ll_opy_ (u"ࠧࡉࡉࠣᰨ")) == bstack1ll_opy_ (u"ࠨࡴࡳࡷࡨࠦᰩ") and bstack11l11lllll_opy_(env.get(bstack1ll_opy_ (u"ࠢࡃࡗࡌࡐࡉࡑࡉࡕࡇࠥᰪ"))):
        return {
            bstack1ll_opy_ (u"ࠣࡰࡤࡱࡪࠨᰫ"): bstack1ll_opy_ (u"ࠤࡅࡹ࡮ࡲࡤ࡬࡫ࡷࡩࠧᰬ"),
            bstack1ll_opy_ (u"ࠥࡦࡺ࡯࡬ࡥࡡࡸࡶࡱࠨᰭ"): env.get(bstack1ll_opy_ (u"ࠦࡇ࡛ࡉࡍࡆࡎࡍ࡙ࡋ࡟ࡃࡗࡌࡐࡉࡥࡕࡓࡎࠥᰮ")),
            bstack1ll_opy_ (u"ࠧࡰ࡯ࡣࡡࡱࡥࡲ࡫ࠢᰯ"): env.get(bstack1ll_opy_ (u"ࠨࡂࡖࡋࡏࡈࡐࡏࡔࡆࡡࡏࡅࡇࡋࡌࠣᰰ")) or env.get(bstack1ll_opy_ (u"ࠢࡃࡗࡌࡐࡉࡑࡉࡕࡇࡢࡔࡎࡖࡅࡍࡋࡑࡉࡤࡔࡁࡎࡇࠥᰱ")),
            bstack1ll_opy_ (u"ࠣࡤࡸ࡭ࡱࡪ࡟࡯ࡷࡰࡦࡪࡸࠢᰲ"): env.get(bstack1ll_opy_ (u"ࠤࡅ࡙ࡎࡒࡄࡌࡋࡗࡉࡤࡈࡕࡊࡎࡇࡣࡓ࡛ࡍࡃࡇࡕࠦᰳ"))
        }
    if bstack11l11lllll_opy_(env.get(bstack1ll_opy_ (u"ࠥࡘࡋࡥࡂࡖࡋࡏࡈࠧᰴ"))):
        return {
            bstack1ll_opy_ (u"ࠦࡳࡧ࡭ࡦࠤᰵ"): bstack1ll_opy_ (u"ࠧ࡜ࡩࡴࡷࡤࡰ࡙ࠥࡴࡶࡦ࡬ࡳ࡚ࠥࡥࡢ࡯ࠣࡗࡪࡸࡶࡪࡥࡨࡷࠧᰶ"),
            bstack1ll_opy_ (u"ࠨࡢࡶ࡫࡯ࡨࡤࡻࡲ࡭ࠤ᰷"): bstack1ll_opy_ (u"ࠢࡼࡿࡾࢁࠧ᰸").format(env.get(bstack1ll_opy_ (u"ࠨࡕ࡜ࡗ࡙ࡋࡍࡠࡖࡈࡅࡒࡌࡏࡖࡐࡇࡅ࡙ࡏࡏࡏࡕࡈࡖ࡛ࡋࡒࡖࡔࡌࠫ᰹")), env.get(bstack1ll_opy_ (u"ࠩࡖ࡝ࡘ࡚ࡅࡎࡡࡗࡉࡆࡓࡐࡓࡑࡍࡉࡈ࡚ࡉࡅࠩ᰺"))),
            bstack1ll_opy_ (u"ࠥ࡮ࡴࡨ࡟࡯ࡣࡰࡩࠧ᰻"): env.get(bstack1ll_opy_ (u"ࠦࡘ࡟ࡓࡕࡇࡐࡣࡉࡋࡆࡊࡐࡌࡘࡎࡕࡎࡊࡆࠥ᰼")),
            bstack1ll_opy_ (u"ࠧࡨࡵࡪ࡮ࡧࡣࡳࡻ࡭ࡣࡧࡵࠦ᰽"): env.get(bstack1ll_opy_ (u"ࠨࡂࡖࡋࡏࡈࡤࡈࡕࡊࡎࡇࡍࡉࠨ᰾"))
        }
    if bstack11l11lllll_opy_(env.get(bstack1ll_opy_ (u"ࠢࡂࡒࡓ࡚ࡊ࡟ࡏࡓࠤ᰿"))):
        return {
            bstack1ll_opy_ (u"ࠣࡰࡤࡱࡪࠨ᱀"): bstack1ll_opy_ (u"ࠤࡄࡴࡵࡼࡥࡺࡱࡵࠦ᱁"),
            bstack1ll_opy_ (u"ࠥࡦࡺ࡯࡬ࡥࡡࡸࡶࡱࠨ᱂"): bstack1ll_opy_ (u"ࠦࢀࢃ࠯ࡱࡴࡲ࡮ࡪࡩࡴ࠰ࡽࢀ࠳ࢀࢃ࠯ࡣࡷ࡬ࡰࡩࡹ࠯ࡼࡿࠥ᱃").format(env.get(bstack1ll_opy_ (u"ࠬࡇࡐࡑࡘࡈ࡝ࡔࡘ࡟ࡖࡔࡏࠫ᱄")), env.get(bstack1ll_opy_ (u"࠭ࡁࡑࡒ࡙ࡉ࡞ࡕࡒࡠࡃࡆࡇࡔ࡛ࡎࡕࡡࡑࡅࡒࡋࠧ᱅")), env.get(bstack1ll_opy_ (u"ࠧࡂࡒࡓ࡚ࡊ࡟ࡏࡓࡡࡓࡖࡔࡐࡅࡄࡖࡢࡗࡑ࡛ࡇࠨ᱆")), env.get(bstack1ll_opy_ (u"ࠨࡃࡓࡔ࡛ࡋ࡙ࡐࡔࡢࡆ࡚ࡏࡌࡅࡡࡌࡈࠬ᱇"))),
            bstack1ll_opy_ (u"ࠤ࡭ࡳࡧࡥ࡮ࡢ࡯ࡨࠦ᱈"): env.get(bstack1ll_opy_ (u"ࠥࡅࡕࡖࡖࡆ࡛ࡒࡖࡤࡐࡏࡃࡡࡑࡅࡒࡋࠢ᱉")),
            bstack1ll_opy_ (u"ࠦࡧࡻࡩ࡭ࡦࡢࡲࡺࡳࡢࡦࡴࠥ᱊"): env.get(bstack1ll_opy_ (u"ࠧࡇࡐࡑࡘࡈ࡝ࡔࡘ࡟ࡃࡗࡌࡐࡉࡥࡎࡖࡏࡅࡉࡗࠨ᱋"))
        }
    if env.get(bstack1ll_opy_ (u"ࠨࡁ࡛ࡗࡕࡉࡤࡎࡔࡕࡒࡢ࡙ࡘࡋࡒࡠࡃࡊࡉࡓ࡚ࠢ᱌")) and env.get(bstack1ll_opy_ (u"ࠢࡕࡈࡢࡆ࡚ࡏࡌࡅࠤᱍ")):
        return {
            bstack1ll_opy_ (u"ࠣࡰࡤࡱࡪࠨᱎ"): bstack1ll_opy_ (u"ࠤࡄࡾࡺࡸࡥࠡࡅࡌࠦᱏ"),
            bstack1ll_opy_ (u"ࠥࡦࡺ࡯࡬ࡥࡡࡸࡶࡱࠨ᱐"): bstack1ll_opy_ (u"ࠦࢀࢃࡻࡾ࠱ࡢࡦࡺ࡯࡬ࡥ࠱ࡵࡩࡸࡻ࡬ࡵࡵࡂࡦࡺ࡯࡬ࡥࡋࡧࡁࢀࢃࠢ᱑").format(env.get(bstack1ll_opy_ (u"࡙࡙ࠬࡔࡖࡈࡑࡤ࡚ࡅࡂࡏࡉࡓ࡚ࡔࡄࡂࡖࡌࡓࡓ࡙ࡅࡓࡘࡈࡖ࡚ࡘࡉࠨ᱒")), env.get(bstack1ll_opy_ (u"࠭ࡓ࡚ࡕࡗࡉࡒࡥࡔࡆࡃࡐࡔࡗࡕࡊࡆࡅࡗࠫ᱓")), env.get(bstack1ll_opy_ (u"ࠧࡃࡗࡌࡐࡉࡥࡂࡖࡋࡏࡈࡎࡊࠧ᱔"))),
            bstack1ll_opy_ (u"ࠣ࡬ࡲࡦࡤࡴࡡ࡮ࡧࠥ᱕"): env.get(bstack1ll_opy_ (u"ࠤࡅ࡙ࡎࡒࡄࡠࡄࡘࡍࡑࡊࡉࡅࠤ᱖")),
            bstack1ll_opy_ (u"ࠥࡦࡺ࡯࡬ࡥࡡࡱࡹࡲࡨࡥࡳࠤ᱗"): env.get(bstack1ll_opy_ (u"ࠦࡇ࡛ࡉࡍࡆࡢࡆ࡚ࡏࡌࡅࡋࡇࠦ᱘"))
        }
    if any([env.get(bstack1ll_opy_ (u"ࠧࡉࡏࡅࡇࡅ࡙ࡎࡒࡄࡠࡄࡘࡍࡑࡊ࡟ࡊࡆࠥ᱙")), env.get(bstack1ll_opy_ (u"ࠨࡃࡐࡆࡈࡆ࡚ࡏࡌࡅࡡࡕࡉࡘࡕࡌࡗࡇࡇࡣࡘࡕࡕࡓࡅࡈࡣ࡛ࡋࡒࡔࡋࡒࡒࠧᱚ")), env.get(bstack1ll_opy_ (u"ࠢࡄࡑࡇࡉࡇ࡛ࡉࡍࡆࡢࡗࡔ࡛ࡒࡄࡇࡢ࡚ࡊࡘࡓࡊࡑࡑࠦᱛ"))]):
        return {
            bstack1ll_opy_ (u"ࠣࡰࡤࡱࡪࠨᱜ"): bstack1ll_opy_ (u"ࠤࡄ࡛ࡘࠦࡃࡰࡦࡨࡆࡺ࡯࡬ࡥࠤᱝ"),
            bstack1ll_opy_ (u"ࠥࡦࡺ࡯࡬ࡥࡡࡸࡶࡱࠨᱞ"): env.get(bstack1ll_opy_ (u"ࠦࡈࡕࡄࡆࡄࡘࡍࡑࡊ࡟ࡑࡗࡅࡐࡎࡉ࡟ࡃࡗࡌࡐࡉࡥࡕࡓࡎࠥᱟ")),
            bstack1ll_opy_ (u"ࠧࡰ࡯ࡣࡡࡱࡥࡲ࡫ࠢᱠ"): env.get(bstack1ll_opy_ (u"ࠨࡃࡐࡆࡈࡆ࡚ࡏࡌࡅࡡࡅ࡙ࡎࡒࡄࡠࡋࡇࠦᱡ")),
            bstack1ll_opy_ (u"ࠢࡣࡷ࡬ࡰࡩࡥ࡮ࡶ࡯ࡥࡩࡷࠨᱢ"): env.get(bstack1ll_opy_ (u"ࠣࡅࡒࡈࡊࡈࡕࡊࡎࡇࡣࡇ࡛ࡉࡍࡆࡢࡍࡉࠨᱣ"))
        }
    if env.get(bstack1ll_opy_ (u"ࠤࡥࡥࡲࡨ࡯ࡰࡡࡥࡹ࡮ࡲࡤࡏࡷࡰࡦࡪࡸࠢᱤ")):
        return {
            bstack1ll_opy_ (u"ࠥࡲࡦࡳࡥࠣᱥ"): bstack1ll_opy_ (u"ࠦࡇࡧ࡭ࡣࡱࡲࠦᱦ"),
            bstack1ll_opy_ (u"ࠧࡨࡵࡪ࡮ࡧࡣࡺࡸ࡬ࠣᱧ"): env.get(bstack1ll_opy_ (u"ࠨࡢࡢ࡯ࡥࡳࡴࡥࡢࡶ࡫࡯ࡨࡗ࡫ࡳࡶ࡮ࡷࡷ࡚ࡸ࡬ࠣᱨ")),
            bstack1ll_opy_ (u"ࠢ࡫ࡱࡥࡣࡳࡧ࡭ࡦࠤᱩ"): env.get(bstack1ll_opy_ (u"ࠣࡤࡤࡱࡧࡵ࡯ࡠࡵ࡫ࡳࡷࡺࡊࡰࡤࡑࡥࡲ࡫ࠢᱪ")),
            bstack1ll_opy_ (u"ࠤࡥࡹ࡮ࡲࡤࡠࡰࡸࡱࡧ࡫ࡲࠣᱫ"): env.get(bstack1ll_opy_ (u"ࠥࡦࡦࡳࡢࡰࡱࡢࡦࡺ࡯࡬ࡥࡐࡸࡱࡧ࡫ࡲࠣᱬ"))
        }
    if env.get(bstack1ll_opy_ (u"ࠦ࡜ࡋࡒࡄࡍࡈࡖࠧᱭ")) or env.get(bstack1ll_opy_ (u"ࠧ࡝ࡅࡓࡅࡎࡉࡗࡥࡍࡂࡋࡑࡣࡕࡏࡐࡆࡎࡌࡒࡊࡥࡓࡕࡃࡕࡘࡊࡊࠢᱮ")):
        return {
            bstack1ll_opy_ (u"ࠨ࡮ࡢ࡯ࡨࠦᱯ"): bstack1ll_opy_ (u"ࠢࡘࡧࡵࡧࡰ࡫ࡲࠣᱰ"),
            bstack1ll_opy_ (u"ࠣࡤࡸ࡭ࡱࡪ࡟ࡶࡴ࡯ࠦᱱ"): env.get(bstack1ll_opy_ (u"ࠤ࡚ࡉࡗࡉࡋࡆࡔࡢࡆ࡚ࡏࡌࡅࡡࡘࡖࡑࠨᱲ")),
            bstack1ll_opy_ (u"ࠥ࡮ࡴࡨ࡟࡯ࡣࡰࡩࠧᱳ"): bstack1ll_opy_ (u"ࠦࡒࡧࡩ࡯ࠢࡓ࡭ࡵ࡫࡬ࡪࡰࡨࠦᱴ") if env.get(bstack1ll_opy_ (u"ࠧ࡝ࡅࡓࡅࡎࡉࡗࡥࡍࡂࡋࡑࡣࡕࡏࡐࡆࡎࡌࡒࡊࡥࡓࡕࡃࡕࡘࡊࡊࠢᱵ")) else None,
            bstack1ll_opy_ (u"ࠨࡢࡶ࡫࡯ࡨࡤࡴࡵ࡮ࡤࡨࡶࠧᱶ"): env.get(bstack1ll_opy_ (u"ࠢࡘࡇࡕࡇࡐࡋࡒࡠࡉࡌࡘࡤࡉࡏࡎࡏࡌࡘࠧᱷ"))
        }
    if any([env.get(bstack1ll_opy_ (u"ࠣࡉࡆࡔࡤࡖࡒࡐࡌࡈࡇ࡙ࠨᱸ")), env.get(bstack1ll_opy_ (u"ࠤࡊࡇࡑࡕࡕࡅࡡࡓࡖࡔࡐࡅࡄࡖࠥᱹ")), env.get(bstack1ll_opy_ (u"ࠥࡋࡔࡕࡇࡍࡇࡢࡇࡑࡕࡕࡅࡡࡓࡖࡔࡐࡅࡄࡖࠥᱺ"))]):
        return {
            bstack1ll_opy_ (u"ࠦࡳࡧ࡭ࡦࠤᱻ"): bstack1ll_opy_ (u"ࠧࡍ࡯ࡰࡩ࡯ࡩࠥࡉ࡬ࡰࡷࡧࠦᱼ"),
            bstack1ll_opy_ (u"ࠨࡢࡶ࡫࡯ࡨࡤࡻࡲ࡭ࠤᱽ"): None,
            bstack1ll_opy_ (u"ࠢ࡫ࡱࡥࡣࡳࡧ࡭ࡦࠤ᱾"): env.get(bstack1ll_opy_ (u"ࠣࡒࡕࡓࡏࡋࡃࡕࡡࡌࡈࠧ᱿")),
            bstack1ll_opy_ (u"ࠤࡥࡹ࡮ࡲࡤࡠࡰࡸࡱࡧ࡫ࡲࠣᲀ"): env.get(bstack1ll_opy_ (u"ࠥࡆ࡚ࡏࡌࡅࡡࡌࡈࠧᲁ"))
        }
    if env.get(bstack1ll_opy_ (u"ࠦࡘࡎࡉࡑࡒࡄࡆࡑࡋࠢᲂ")):
        return {
            bstack1ll_opy_ (u"ࠧࡴࡡ࡮ࡧࠥᲃ"): bstack1ll_opy_ (u"ࠨࡓࡩ࡫ࡳࡴࡦࡨ࡬ࡦࠤᲄ"),
            bstack1ll_opy_ (u"ࠢࡣࡷ࡬ࡰࡩࡥࡵࡳ࡮ࠥᲅ"): env.get(bstack1ll_opy_ (u"ࠣࡕࡋࡍࡕࡖࡁࡃࡎࡈࡣࡇ࡛ࡉࡍࡆࡢ࡙ࡗࡒࠢᲆ")),
            bstack1ll_opy_ (u"ࠤ࡭ࡳࡧࡥ࡮ࡢ࡯ࡨࠦᲇ"): bstack1ll_opy_ (u"ࠥࡎࡴࡨࠠࠤࡽࢀࠦᲈ").format(env.get(bstack1ll_opy_ (u"ࠫࡘࡎࡉࡑࡒࡄࡆࡑࡋ࡟ࡋࡑࡅࡣࡎࡊࠧᲉ"))) if env.get(bstack1ll_opy_ (u"࡙ࠧࡈࡊࡒࡓࡅࡇࡒࡅࡠࡌࡒࡆࡤࡏࡄࠣᲊ")) else None,
            bstack1ll_opy_ (u"ࠨࡢࡶ࡫࡯ࡨࡤࡴࡵ࡮ࡤࡨࡶࠧ᲋"): env.get(bstack1ll_opy_ (u"ࠢࡔࡊࡌࡔࡕࡇࡂࡍࡇࡢࡆ࡚ࡏࡌࡅࡡࡑ࡙ࡒࡈࡅࡓࠤ᲌"))
        }
    if bstack11l11lllll_opy_(env.get(bstack1ll_opy_ (u"ࠣࡐࡈࡘࡑࡏࡆ࡚ࠤ᲍"))):
        return {
            bstack1ll_opy_ (u"ࠤࡱࡥࡲ࡫ࠢ᲎"): bstack1ll_opy_ (u"ࠥࡒࡪࡺ࡬ࡪࡨࡼࠦ᲏"),
            bstack1ll_opy_ (u"ࠦࡧࡻࡩ࡭ࡦࡢࡹࡷࡲࠢᲐ"): env.get(bstack1ll_opy_ (u"ࠧࡊࡅࡑࡎࡒ࡝ࡤ࡛ࡒࡍࠤᲑ")),
            bstack1ll_opy_ (u"ࠨࡪࡰࡤࡢࡲࡦࡳࡥࠣᲒ"): env.get(bstack1ll_opy_ (u"ࠢࡔࡋࡗࡉࡤࡔࡁࡎࡇࠥᲓ")),
            bstack1ll_opy_ (u"ࠣࡤࡸ࡭ࡱࡪ࡟࡯ࡷࡰࡦࡪࡸࠢᲔ"): env.get(bstack1ll_opy_ (u"ࠤࡅ࡙ࡎࡒࡄࡠࡋࡇࠦᲕ"))
        }
    if bstack11l11lllll_opy_(env.get(bstack1ll_opy_ (u"ࠥࡋࡎ࡚ࡈࡖࡄࡢࡅࡈ࡚ࡉࡐࡐࡖࠦᲖ"))):
        return {
            bstack1ll_opy_ (u"ࠦࡳࡧ࡭ࡦࠤᲗ"): bstack1ll_opy_ (u"ࠧࡍࡩࡵࡊࡸࡦࠥࡇࡣࡵ࡫ࡲࡲࡸࠨᲘ"),
            bstack1ll_opy_ (u"ࠨࡢࡶ࡫࡯ࡨࡤࡻࡲ࡭ࠤᲙ"): bstack1ll_opy_ (u"ࠢࡼࡿ࠲ࡿࢂ࠵ࡡࡤࡶ࡬ࡳࡳࡹ࠯ࡳࡷࡱࡷ࠴ࢁࡽࠣᲚ").format(env.get(bstack1ll_opy_ (u"ࠨࡉࡌࡘࡍ࡛ࡂࡠࡕࡈࡖ࡛ࡋࡒࡠࡗࡕࡐࠬᲛ")), env.get(bstack1ll_opy_ (u"ࠩࡊࡍ࡙ࡎࡕࡃࡡࡕࡉࡕࡕࡓࡊࡖࡒࡖ࡞࠭Ნ")), env.get(bstack1ll_opy_ (u"ࠪࡋࡎ࡚ࡈࡖࡄࡢࡖ࡚ࡔ࡟ࡊࡆࠪᲝ"))),
            bstack1ll_opy_ (u"ࠦ࡯ࡵࡢࡠࡰࡤࡱࡪࠨᲞ"): env.get(bstack1ll_opy_ (u"ࠧࡍࡉࡕࡊࡘࡆࡤ࡝ࡏࡓࡍࡉࡐࡔ࡝ࠢᲟ")),
            bstack1ll_opy_ (u"ࠨࡢࡶ࡫࡯ࡨࡤࡴࡵ࡮ࡤࡨࡶࠧᲠ"): env.get(bstack1ll_opy_ (u"ࠢࡈࡋࡗࡌ࡚ࡈ࡟ࡓࡗࡑࡣࡎࡊࠢᲡ"))
        }
    if env.get(bstack1ll_opy_ (u"ࠣࡅࡌࠦᲢ")) == bstack1ll_opy_ (u"ࠤࡷࡶࡺ࡫ࠢᲣ") and env.get(bstack1ll_opy_ (u"࡚ࠥࡊࡘࡃࡆࡎࠥᲤ")) == bstack1ll_opy_ (u"ࠦ࠶ࠨᲥ"):
        return {
            bstack1ll_opy_ (u"ࠧࡴࡡ࡮ࡧࠥᲦ"): bstack1ll_opy_ (u"ࠨࡖࡦࡴࡦࡩࡱࠨᲧ"),
            bstack1ll_opy_ (u"ࠢࡣࡷ࡬ࡰࡩࡥࡵࡳ࡮ࠥᲨ"): bstack1ll_opy_ (u"ࠣࡪࡷࡸࡵࡀ࠯࠰ࡽࢀࠦᲩ").format(env.get(bstack1ll_opy_ (u"࡙ࠩࡉࡗࡉࡅࡍࡡࡘࡖࡑ࠭Ც"))),
            bstack1ll_opy_ (u"ࠥ࡮ࡴࡨ࡟࡯ࡣࡰࡩࠧᲫ"): None,
            bstack1ll_opy_ (u"ࠦࡧࡻࡩ࡭ࡦࡢࡲࡺࡳࡢࡦࡴࠥᲬ"): None,
        }
    if env.get(bstack1ll_opy_ (u"࡚ࠧࡅࡂࡏࡆࡍ࡙࡟࡟ࡗࡇࡕࡗࡎࡕࡎࠣᲭ")):
        return {
            bstack1ll_opy_ (u"ࠨ࡮ࡢ࡯ࡨࠦᲮ"): bstack1ll_opy_ (u"ࠢࡕࡧࡤࡱࡨ࡯ࡴࡺࠤᲯ"),
            bstack1ll_opy_ (u"ࠣࡤࡸ࡭ࡱࡪ࡟ࡶࡴ࡯ࠦᲰ"): None,
            bstack1ll_opy_ (u"ࠤ࡭ࡳࡧࡥ࡮ࡢ࡯ࡨࠦᲱ"): env.get(bstack1ll_opy_ (u"ࠥࡘࡊࡇࡍࡄࡋࡗ࡝ࡤࡖࡒࡐࡌࡈࡇ࡙ࡥࡎࡂࡏࡈࠦᲲ")),
            bstack1ll_opy_ (u"ࠦࡧࡻࡩ࡭ࡦࡢࡲࡺࡳࡢࡦࡴࠥᲳ"): env.get(bstack1ll_opy_ (u"ࠧࡈࡕࡊࡎࡇࡣࡓ࡛ࡍࡃࡇࡕࠦᲴ"))
        }
    if any([env.get(bstack1ll_opy_ (u"ࠨࡃࡐࡐࡆࡓ࡚ࡘࡓࡆࠤᲵ")), env.get(bstack1ll_opy_ (u"ࠢࡄࡑࡑࡇࡔ࡛ࡒࡔࡇࡢ࡙ࡗࡒࠢᲶ")), env.get(bstack1ll_opy_ (u"ࠣࡅࡒࡒࡈࡕࡕࡓࡕࡈࡣ࡚࡙ࡅࡓࡐࡄࡑࡊࠨᲷ")), env.get(bstack1ll_opy_ (u"ࠤࡆࡓࡓࡉࡏࡖࡔࡖࡉࡤ࡚ࡅࡂࡏࠥᲸ"))]):
        return {
            bstack1ll_opy_ (u"ࠥࡲࡦࡳࡥࠣᲹ"): bstack1ll_opy_ (u"ࠦࡈࡵ࡮ࡤࡱࡸࡶࡸ࡫ࠢᲺ"),
            bstack1ll_opy_ (u"ࠧࡨࡵࡪ࡮ࡧࡣࡺࡸ࡬ࠣ᲻"): None,
            bstack1ll_opy_ (u"ࠨࡪࡰࡤࡢࡲࡦࡳࡥࠣ᲼"): env.get(bstack1ll_opy_ (u"ࠢࡃࡗࡌࡐࡉࡥࡊࡐࡄࡢࡒࡆࡓࡅࠣᲽ")) or None,
            bstack1ll_opy_ (u"ࠣࡤࡸ࡭ࡱࡪ࡟࡯ࡷࡰࡦࡪࡸࠢᲾ"): env.get(bstack1ll_opy_ (u"ࠤࡅ࡙ࡎࡒࡄࡠࡋࡇࠦᲿ"), 0)
        }
    if env.get(bstack1ll_opy_ (u"ࠥࡋࡔࡥࡊࡐࡄࡢࡒࡆࡓࡅࠣ᳀")):
        return {
            bstack1ll_opy_ (u"ࠦࡳࡧ࡭ࡦࠤ᳁"): bstack1ll_opy_ (u"ࠧࡍ࡯ࡄࡆࠥ᳂"),
            bstack1ll_opy_ (u"ࠨࡢࡶ࡫࡯ࡨࡤࡻࡲ࡭ࠤ᳃"): None,
            bstack1ll_opy_ (u"ࠢ࡫ࡱࡥࡣࡳࡧ࡭ࡦࠤ᳄"): env.get(bstack1ll_opy_ (u"ࠣࡉࡒࡣࡏࡕࡂࡠࡐࡄࡑࡊࠨ᳅")),
            bstack1ll_opy_ (u"ࠤࡥࡹ࡮ࡲࡤࡠࡰࡸࡱࡧ࡫ࡲࠣ᳆"): env.get(bstack1ll_opy_ (u"ࠥࡋࡔࡥࡐࡊࡒࡈࡐࡎࡔࡅࡠࡅࡒ࡙ࡓ࡚ࡅࡓࠤ᳇"))
        }
    if env.get(bstack1ll_opy_ (u"ࠦࡈࡌ࡟ࡃࡗࡌࡐࡉࡥࡉࡅࠤ᳈")):
        return {
            bstack1ll_opy_ (u"ࠧࡴࡡ࡮ࡧࠥ᳉"): bstack1ll_opy_ (u"ࠨࡃࡰࡦࡨࡊࡷ࡫ࡳࡩࠤ᳊"),
            bstack1ll_opy_ (u"ࠢࡣࡷ࡬ࡰࡩࡥࡵࡳ࡮ࠥ᳋"): env.get(bstack1ll_opy_ (u"ࠣࡅࡉࡣࡇ࡛ࡉࡍࡆࡢ࡙ࡗࡒࠢ᳌")),
            bstack1ll_opy_ (u"ࠤ࡭ࡳࡧࡥ࡮ࡢ࡯ࡨࠦ᳍"): env.get(bstack1ll_opy_ (u"ࠥࡇࡋࡥࡐࡊࡒࡈࡐࡎࡔࡅࡠࡐࡄࡑࡊࠨ᳎")),
            bstack1ll_opy_ (u"ࠦࡧࡻࡩ࡭ࡦࡢࡲࡺࡳࡢࡦࡴࠥ᳏"): env.get(bstack1ll_opy_ (u"ࠧࡉࡆࡠࡄࡘࡍࡑࡊ࡟ࡊࡆࠥ᳐"))
        }
    return {bstack1ll_opy_ (u"ࠨࡢࡶ࡫࡯ࡨࡤࡴࡵ࡮ࡤࡨࡶࠧ᳑"): None}
def get_host_info():
    return {
        bstack1ll_opy_ (u"ࠢࡩࡱࡶࡸࡳࡧ࡭ࡦࠤ᳒"): platform.node(),
        bstack1ll_opy_ (u"ࠣࡲ࡯ࡥࡹ࡬࡯ࡳ࡯ࠥ᳓"): platform.system(),
        bstack1ll_opy_ (u"ࠤࡷࡽࡵ࡫᳔ࠢ"): platform.machine(),
        bstack1ll_opy_ (u"ࠥࡺࡪࡸࡳࡪࡱࡱ᳕ࠦ"): platform.version(),
        bstack1ll_opy_ (u"ࠦࡦࡸࡣࡩࠤ᳖"): platform.architecture()[0]
    }
def bstack11ll1l11l1_opy_():
    try:
        import selenium
        return True
    except ImportError:
        return False
def bstack11l111ll11l_opy_():
    if bstack1ll1l1l111_opy_.get_property(bstack1ll_opy_ (u"ࠬࡨࡳࡵࡣࡦ࡯ࡤࡹࡥࡴࡵ࡬ࡳࡳ᳗࠭")):
        return bstack1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯᳘ࠬ")
    return bstack1ll_opy_ (u"ࠧࡶࡰ࡮ࡲࡴࡽ࡮ࡠࡩࡵ࡭ࡩ᳙࠭")
def bstack11l11111ll1_opy_(driver):
    info = {
        bstack1ll_opy_ (u"ࠨࡥࡤࡴࡦࡨࡩ࡭࡫ࡷ࡭ࡪࡹࠧ᳚"): driver.capabilities,
        bstack1ll_opy_ (u"ࠩࡶࡩࡸࡹࡩࡰࡰࡢ࡭ࡩ࠭᳛"): driver.session_id,
        bstack1ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵ᳜ࠫ"): driver.capabilities.get(bstack1ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࡓࡧ࡭ࡦ᳝ࠩ"), None),
        bstack1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡥࡶࡦࡴࡶ࡭ࡴࡴ᳞ࠧ"): driver.capabilities.get(bstack1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡖࡦࡴࡶ࡭ࡴࡴ᳟ࠧ"), None),
        bstack1ll_opy_ (u"ࠧࡱ࡮ࡤࡸ࡫ࡵࡲ࡮ࠩ᳠"): driver.capabilities.get(bstack1ll_opy_ (u"ࠨࡲ࡯ࡥࡹ࡬࡯ࡳ࡯ࡑࡥࡲ࡫ࠧ᳡"), None),
        bstack1ll_opy_ (u"ࠩࡳࡰࡦࡺࡦࡰࡴࡰࡣࡻ࡫ࡲࡴ࡫ࡲࡲ᳢ࠬ"):driver.capabilities.get(bstack1ll_opy_ (u"ࠪࡴࡱࡧࡴࡧࡱࡵࡱ࡛࡫ࡲࡴ࡫ࡲࡲ᳣ࠬ"), None),
    }
    if bstack11l111ll11l_opy_() == bstack1ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭᳤ࠪ"):
        if bstack11ll11ll1l_opy_():
            info[bstack1ll_opy_ (u"ࠬࡶࡲࡰࡦࡸࡧࡹ᳥࠭")] = bstack1ll_opy_ (u"࠭ࡡࡱࡲ࠰ࡥࡺࡺ࡯࡮ࡣࡷࡩ᳦ࠬ")
        elif driver.capabilities.get(bstack1ll_opy_ (u"ࠧࡣࡵࡷࡥࡨࡱ࠺ࡰࡲࡷ࡭ࡴࡴࡳࠨ᳧"), {}).get(bstack1ll_opy_ (u"ࠨࡶࡸࡶࡧࡵࡳࡤࡣ࡯ࡩ᳨ࠬ"), False):
            info[bstack1ll_opy_ (u"ࠩࡳࡶࡴࡪࡵࡤࡶࠪᳩ")] = bstack1ll_opy_ (u"ࠪࡸࡺࡸࡢࡰࡵࡦࡥࡱ࡫ࠧᳪ")
        else:
            info[bstack1ll_opy_ (u"ࠫࡵࡸ࡯ࡥࡷࡦࡸࠬᳫ")] = bstack1ll_opy_ (u"ࠬࡧࡵࡵࡱࡰࡥࡹ࡫ࠧᳬ")
    return info
def bstack11ll11ll1l_opy_():
    if bstack1ll1l1l111_opy_.get_property(bstack1ll_opy_ (u"࠭ࡡࡱࡲࡢࡥࡺࡺ࡯࡮ࡣࡷࡩ᳭ࠬ")):
        return True
    if bstack11l11lllll_opy_(os.environ.get(bstack1ll_opy_ (u"ࠧࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡉࡔࡡࡄࡔࡕࡥࡁࡖࡖࡒࡑࡆ࡚ࡅࠨᳮ"), None)):
        return True
    return False
def bstack1l111111_opy_(bstack11l1111l1l1_opy_, url, data, config):
    headers = config.get(bstack1ll_opy_ (u"ࠨࡪࡨࡥࡩ࡫ࡲࡴࠩᳯ"), None)
    proxies = bstack11ll11llll_opy_(config, url)
    auth = config.get(bstack1ll_opy_ (u"ࠩࡤࡹࡹ࡮ࠧᳰ"), None)
    response = requests.request(
            bstack11l1111l1l1_opy_,
            url=url,
            headers=headers,
            auth=auth,
            json=data,
            proxies=proxies
        )
    return response
def bstack1l1l11l11l_opy_(bstack1l1l11l1l_opy_, size):
    bstack11l11111_opy_ = []
    while len(bstack1l1l11l1l_opy_) > size:
        bstack1ll1ll1111_opy_ = bstack1l1l11l1l_opy_[:size]
        bstack11l11111_opy_.append(bstack1ll1ll1111_opy_)
        bstack1l1l11l1l_opy_ = bstack1l1l11l1l_opy_[size:]
    bstack11l11111_opy_.append(bstack1l1l11l1l_opy_)
    return bstack11l11111_opy_
def bstack11l111llll1_opy_(message, bstack11l111l1ll1_opy_=False):
    os.write(1, bytes(message, bstack1ll_opy_ (u"ࠪࡹࡹ࡬࠭࠹ࠩᳱ")))
    os.write(1, bytes(bstack1ll_opy_ (u"ࠫࡡࡴࠧᳲ"), bstack1ll_opy_ (u"ࠬࡻࡴࡧ࠯࠻ࠫᳳ")))
    if bstack11l111l1ll1_opy_:
        with open(bstack1ll_opy_ (u"࠭ࡢࡴࡶࡤࡧࡰ࠳࡯࠲࠳ࡼ࠱ࠬ᳴") + os.environ[bstack1ll_opy_ (u"ࠧࡃࡕࡢࡘࡊ࡙ࡔࡐࡒࡖࡣࡇ࡛ࡉࡍࡆࡢࡌࡆ࡙ࡈࡆࡆࡢࡍࡉ࠭ᳵ")] + bstack1ll_opy_ (u"ࠨ࠰࡯ࡳ࡬࠭ᳶ"), bstack1ll_opy_ (u"ࠩࡤࠫ᳷")) as f:
            f.write(message + bstack1ll_opy_ (u"ࠪࡠࡳ࠭᳸"))
def bstack1l1ll111lll_opy_():
    return os.environ[bstack1ll_opy_ (u"ࠫࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡅ࡚࡚ࡏࡎࡃࡗࡍࡔࡔࠧ᳹")].lower() == bstack1ll_opy_ (u"ࠬࡺࡲࡶࡧࠪᳺ")
def bstack1l11l1111_opy_():
    return bstack111l11ll1l_opy_().replace(tzinfo=None).isoformat() + bstack1ll_opy_ (u"࡚࠭ࠨ᳻")
def bstack11l1111ll11_opy_(start, finish):
    return (datetime.datetime.fromisoformat(finish.rstrip(bstack1ll_opy_ (u"࡛ࠧࠩ᳼"))) - datetime.datetime.fromisoformat(start.rstrip(bstack1ll_opy_ (u"ࠨ࡜ࠪ᳽")))).total_seconds() * 1000
def bstack111l1lll111_opy_(timestamp):
    return bstack111llll11l1_opy_(timestamp).isoformat() + bstack1ll_opy_ (u"ࠩ࡝ࠫ᳾")
def bstack11l1111111l_opy_(bstack111l1lllll1_opy_):
    date_format = bstack1ll_opy_ (u"ࠪࠩ࡞ࠫ࡭ࠦࡦࠣࠩࡍࡀࠥࡎ࠼ࠨࡗ࠳ࠫࡦࠨ᳿")
    bstack111llll1lll_opy_ = datetime.datetime.strptime(bstack111l1lllll1_opy_, date_format)
    return bstack111llll1lll_opy_.isoformat() + bstack1ll_opy_ (u"ࠫ࡟࠭ᴀ")
def bstack111ll11ll1l_opy_(outcome):
    _, exception, _ = outcome.excinfo or (None, None, None)
    if exception:
        return bstack1ll_opy_ (u"ࠬ࡬ࡡࡪ࡮ࡨࡨࠬᴁ")
    else:
        return bstack1ll_opy_ (u"࠭ࡰࡢࡵࡶࡩࡩ࠭ᴂ")
def bstack11l11lllll_opy_(val):
    if val is None:
        return False
    return val.__str__().lower() == bstack1ll_opy_ (u"ࠧࡵࡴࡸࡩࠬᴃ")
def bstack111ll111l11_opy_(val):
    return val.__str__().lower() == bstack1ll_opy_ (u"ࠨࡨࡤࡰࡸ࡫ࠧᴄ")
def error_handler(bstack111lllll1l1_opy_=Exception, class_method=False, default_value=None):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except bstack111lllll1l1_opy_ as e:
                print(bstack1ll_opy_ (u"ࠤࡈࡼࡨ࡫ࡰࡵ࡫ࡲࡲࠥ࡯࡮ࠡࡨࡸࡲࡨࡺࡩࡰࡰࠣࡿࢂࠦ࠭࠿ࠢࡾࢁ࠿ࠦࡻࡾࠤᴅ").format(func.__name__, bstack111lllll1l1_opy_.__name__, str(e)))
                return default_value
        return wrapper
    def bstack11l11111lll_opy_(bstack111ll1l1lll_opy_):
        def wrapped(cls, *args, **kwargs):
            try:
                return bstack111ll1l1lll_opy_(cls, *args, **kwargs)
            except bstack111lllll1l1_opy_ as e:
                print(bstack1ll_opy_ (u"ࠥࡉࡽࡩࡥࡱࡶ࡬ࡳࡳࠦࡩ࡯ࠢࡩࡹࡳࡩࡴࡪࡱࡱࠤࢀࢃࠠ࠮ࡀࠣࡿࢂࡀࠠࡼࡿࠥᴆ").format(bstack111ll1l1lll_opy_.__name__, bstack111lllll1l1_opy_.__name__, str(e)))
                return default_value
        return wrapped
    if class_method:
        return bstack11l11111lll_opy_
    else:
        return decorator
def bstack11111l1l_opy_(bstack11111ll111_opy_):
    if os.getenv(bstack1ll_opy_ (u"ࠫࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡅ࡚࡚ࡏࡎࡃࡗࡍࡔࡔࠧᴇ")) is not None:
        return bstack11l11lllll_opy_(os.getenv(bstack1ll_opy_ (u"ࠬࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣࡆ࡛ࡔࡐࡏࡄࡘࡎࡕࡎࠨᴈ")))
    if bstack1ll_opy_ (u"࠭ࡡࡶࡶࡲࡱࡦࡺࡩࡰࡰࠪᴉ") in bstack11111ll111_opy_ and bstack111ll111l11_opy_(bstack11111ll111_opy_[bstack1ll_opy_ (u"ࠧࡢࡷࡷࡳࡲࡧࡴࡪࡱࡱࠫᴊ")]):
        return False
    if bstack1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱࡁࡶࡶࡲࡱࡦࡺࡩࡰࡰࠪᴋ") in bstack11111ll111_opy_ and bstack111ll111l11_opy_(bstack11111ll111_opy_[bstack1ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫ࡂࡷࡷࡳࡲࡧࡴࡪࡱࡱࠫᴌ")]):
        return False
    return True
def bstack1ll1l1l1ll_opy_():
    try:
        from pytest_bdd import reporting
        bstack111lll111l1_opy_ = os.environ.get(bstack1ll_opy_ (u"ࠥࡆࡗࡕࡗࡔࡇࡕࡗ࡙ࡇࡃࡌࡡࡘࡗࡊࡘ࡟ࡇࡔࡄࡑࡊ࡝ࡏࡓࡍࠥᴍ"), None)
        return bstack111lll111l1_opy_ is None or bstack111lll111l1_opy_ == bstack1ll_opy_ (u"ࠦࡵࡿࡴࡦࡵࡷ࠱ࡧࡪࡤࠣᴎ")
    except Exception as e:
        return False
def bstack111ll1111_opy_(hub_url, CONFIG):
    if bstack11l11111l1_opy_() <= version.parse(bstack1ll_opy_ (u"ࠬ࠹࠮࠲࠵࠱࠴ࠬᴏ")):
        if hub_url:
            return bstack1ll_opy_ (u"ࠨࡨࡵࡶࡳ࠾࠴࠵ࠢᴐ") + hub_url + bstack1ll_opy_ (u"ࠢ࠻࠺࠳࠳ࡼࡪ࠯ࡩࡷࡥࠦᴑ")
        return bstack1l11lll11_opy_
    if hub_url:
        return bstack1ll_opy_ (u"ࠣࡪࡷࡸࡵࡹ࠺࠰࠱ࠥᴒ") + hub_url + bstack1ll_opy_ (u"ࠤ࠲ࡻࡩ࠵ࡨࡶࡤࠥᴓ")
    return bstack1lll111l11_opy_
def bstack111lll11l11_opy_():
    return isinstance(os.getenv(bstack1ll_opy_ (u"ࠪࡆࡗࡕࡗࡔࡇࡕࡗ࡙ࡇࡃࡌࡡࡓ࡝࡙ࡋࡓࡕࡡࡓࡐ࡚ࡍࡉࡏࠩᴔ")), str)
def bstack11ll1l11l_opy_(url):
    return urlparse(url).hostname
def bstack1l11l1l1l_opy_(hostname):
    for bstack1llll11l1_opy_ in bstack1l11ll1ll1_opy_:
        regex = re.compile(bstack1llll11l1_opy_)
        if regex.match(hostname):
            return True
    return False
def bstack111ll111111_opy_(bstack11l111l11l1_opy_, file_name, logger):
    bstack1l11l11l1l_opy_ = os.path.join(os.path.expanduser(bstack1ll_opy_ (u"ࠫࢃ࠭ᴕ")), bstack11l111l11l1_opy_)
    try:
        if not os.path.exists(bstack1l11l11l1l_opy_):
            os.makedirs(bstack1l11l11l1l_opy_)
        file_path = os.path.join(os.path.expanduser(bstack1ll_opy_ (u"ࠬࢄࠧᴖ")), bstack11l111l11l1_opy_, file_name)
        if not os.path.isfile(file_path):
            with open(file_path, bstack1ll_opy_ (u"࠭ࡷࠨᴗ")):
                pass
            with open(file_path, bstack1ll_opy_ (u"ࠢࡸ࠭ࠥᴘ")) as outfile:
                json.dump({}, outfile)
        return file_path
    except Exception as e:
        logger.debug(bstack1l1lll1111_opy_.format(str(e)))
def bstack111ll1ll1ll_opy_(file_name, key, value, logger):
    file_path = bstack111ll111111_opy_(bstack1ll_opy_ (u"ࠨ࠰ࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫ࠨᴙ"), file_name, logger)
    if file_path != None:
        if os.path.exists(file_path):
            bstack11lllll111_opy_ = json.load(open(file_path, bstack1ll_opy_ (u"ࠩࡵࡦࠬᴚ")))
        else:
            bstack11lllll111_opy_ = {}
        bstack11lllll111_opy_[key] = value
        with open(file_path, bstack1ll_opy_ (u"ࠥࡻ࠰ࠨᴛ")) as outfile:
            json.dump(bstack11lllll111_opy_, outfile)
def bstack1l11lll1ll_opy_(file_name, logger):
    file_path = bstack111ll111111_opy_(bstack1ll_opy_ (u"ࠫ࠳ࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮ࠫᴜ"), file_name, logger)
    bstack11lllll111_opy_ = {}
    if file_path != None and os.path.exists(file_path):
        with open(file_path, bstack1ll_opy_ (u"ࠬࡸࠧᴝ")) as bstack11l11l111l_opy_:
            bstack11lllll111_opy_ = json.load(bstack11l11l111l_opy_)
    return bstack11lllll111_opy_
def bstack1l1l1l1ll1_opy_(file_path, logger):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        logger.debug(bstack1ll_opy_ (u"࠭ࡅࡳࡴࡲࡶࠥ࡯࡮ࠡࡦࡨࡰࡪࡺࡩ࡯ࡩࠣࡪ࡮ࡲࡥ࠻ࠢࠪᴞ") + file_path + bstack1ll_opy_ (u"ࠧࠡࠩᴟ") + str(e))
def bstack11l11111l1_opy_():
    from selenium import webdriver
    return version.parse(webdriver.__version__)
class Notset:
    def __repr__(self):
        return bstack1ll_opy_ (u"ࠣ࠾ࡑࡓ࡙࡙ࡅࡕࡀࠥᴠ")
def bstack1l1111l11l_opy_(config):
    if bstack1ll_opy_ (u"ࠩ࡬ࡷࡕࡲࡡࡺࡹࡵ࡭࡬࡮ࡴࠨᴡ") in config:
        del (config[bstack1ll_opy_ (u"ࠪ࡭ࡸࡖ࡬ࡢࡻࡺࡶ࡮࡭ࡨࡵࠩᴢ")])
        return False
    if bstack11l11111l1_opy_() < version.parse(bstack1ll_opy_ (u"ࠫ࠸࠴࠴࠯࠲ࠪᴣ")):
        return False
    if bstack11l11111l1_opy_() >= version.parse(bstack1ll_opy_ (u"ࠬ࠺࠮࠲࠰࠸ࠫᴤ")):
        return True
    if bstack1ll_opy_ (u"࠭ࡵࡴࡧ࡚࠷ࡈ࠭ᴥ") in config and config[bstack1ll_opy_ (u"ࠧࡶࡵࡨ࡛࠸ࡉࠧᴦ")] is False:
        return False
    else:
        return True
def bstack1ll111l1_opy_(args_list, bstack111lll1111l_opy_):
    index = -1
    for value in bstack111lll1111l_opy_:
        try:
            index = args_list.index(value)
            return index
        except Exception as e:
            return index
    return index
def bstack11ll1111ll1_opy_(a, b):
  for k, v in b.items():
    if isinstance(v, dict) and k in a and isinstance(a[k], dict):
        bstack11ll1111ll1_opy_(a[k], v)
    else:
        a[k] = v
class Result:
    def __init__(self, result=None, duration=None, exception=None, bstack111l1lll11_opy_=None):
        self.result = result
        self.duration = duration
        self.exception = exception
        self.exception_type = type(self.exception).__name__ if exception else None
        self.bstack111l1lll11_opy_ = bstack111l1lll11_opy_
    @classmethod
    def passed(cls):
        return Result(result=bstack1ll_opy_ (u"ࠨࡲࡤࡷࡸ࡫ࡤࠨᴧ"))
    @classmethod
    def failed(cls, exception=None):
        return Result(result=bstack1ll_opy_ (u"ࠩࡩࡥ࡮ࡲࡥࡥࠩᴨ"), exception=exception)
    def bstack1llllll1111_opy_(self):
        if self.result != bstack1ll_opy_ (u"ࠪࡪࡦ࡯࡬ࡦࡦࠪᴩ"):
            return None
        if isinstance(self.exception_type, str) and bstack1ll_opy_ (u"ࠦࡆࡹࡳࡦࡴࡷ࡭ࡴࡴࠢᴪ") in self.exception_type:
            return bstack1ll_opy_ (u"ࠧࡇࡳࡴࡧࡵࡸ࡮ࡵ࡮ࡆࡴࡵࡳࡷࠨᴫ")
        return bstack1ll_opy_ (u"ࠨࡕ࡯ࡪࡤࡲࡩࡲࡥࡥࡇࡵࡶࡴࡸࠢᴬ")
    def bstack111l1lll1ll_opy_(self):
        if self.result != bstack1ll_opy_ (u"ࠧࡧࡣ࡬ࡰࡪࡪࠧᴭ"):
            return None
        if self.bstack111l1lll11_opy_:
            return self.bstack111l1lll11_opy_
        return bstack11l111l111l_opy_(self.exception)
def bstack11l111l111l_opy_(exc):
    return [traceback.format_exception(exc)]
def bstack111l1llllll_opy_(message):
    if isinstance(message, str):
        return not bool(message and message.strip())
    return True
def bstack1l11l11l_opy_(object, key, default_value):
    if not object or not object.__dict__:
        return default_value
    if key in object.__dict__.keys():
        return object.__dict__.get(key)
    return default_value
def bstack1l1lll11_opy_(config, logger):
    try:
        import playwright
        bstack111ll1ll11l_opy_ = playwright.__file__
        bstack111lll1ll11_opy_ = os.path.split(bstack111ll1ll11l_opy_)
        bstack11l111l1l11_opy_ = bstack111lll1ll11_opy_[0] + bstack1ll_opy_ (u"ࠨ࠱ࡧࡶ࡮ࡼࡥࡳ࠱ࡳࡥࡨࡱࡡࡨࡧ࠲ࡰ࡮ࡨ࠯ࡤ࡮࡬࠳ࡨࡲࡩ࠯࡬ࡶࠫᴮ")
        os.environ[bstack1ll_opy_ (u"ࠩࡊࡐࡔࡈࡁࡍࡡࡄࡋࡊࡔࡔࡠࡊࡗࡘࡕࡥࡐࡓࡑ࡛࡝ࠬᴯ")] = bstack1ll11ll11l_opy_(config)
        with open(bstack11l111l1l11_opy_, bstack1ll_opy_ (u"ࠪࡶࠬᴰ")) as f:
            bstack1lll1lll11_opy_ = f.read()
            bstack111ll1lllll_opy_ = bstack1ll_opy_ (u"ࠫ࡬ࡲ࡯ࡣࡣ࡯࠱ࡦ࡭ࡥ࡯ࡶࠪᴱ")
            bstack111lllll1ll_opy_ = bstack1lll1lll11_opy_.find(bstack111ll1lllll_opy_)
            if bstack111lllll1ll_opy_ == -1:
              process = subprocess.Popen(bstack1ll_opy_ (u"ࠧࡴࡰ࡮ࠢ࡬ࡲࡸࡺࡡ࡭࡮ࠣ࡫ࡱࡵࡢࡢ࡮࠰ࡥ࡬࡫࡮ࡵࠤᴲ"), shell=True, cwd=bstack111lll1ll11_opy_[0])
              process.wait()
              bstack111ll1l11l1_opy_ = bstack1ll_opy_ (u"࠭ࠢࡶࡵࡨࠤࡸࡺࡲࡪࡥࡷࠦࡀ࠭ᴳ")
              bstack111ll1llll1_opy_ = bstack1ll_opy_ (u"ࠢࠣࠤࠣࡠࠧࡻࡳࡦࠢࡶࡸࡷ࡯ࡣࡵ࡞ࠥ࠿ࠥࡩ࡯࡯ࡵࡷࠤࢀࠦࡢࡰࡱࡷࡷࡹࡸࡡࡱࠢࢀࠤࡂࠦࡲࡦࡳࡸ࡭ࡷ࡫ࠨࠨࡩ࡯ࡳࡧࡧ࡬࠮ࡣࡪࡩࡳࡺࠧࠪ࠽ࠣ࡭࡫ࠦࠨࡱࡴࡲࡧࡪࡹࡳ࠯ࡧࡱࡺ࠳ࡍࡌࡐࡄࡄࡐࡤࡇࡇࡆࡐࡗࡣࡍ࡚ࡔࡑࡡࡓࡖࡔ࡞࡙ࠪࠢࡥࡳࡴࡺࡳࡵࡴࡤࡴ࠭࠯࠻ࠡࠤࠥࠦᴴ")
              bstack111l1ll11l1_opy_ = bstack1lll1lll11_opy_.replace(bstack111ll1l11l1_opy_, bstack111ll1llll1_opy_)
              with open(bstack11l111l1l11_opy_, bstack1ll_opy_ (u"ࠨࡹࠪᴵ")) as f:
                f.write(bstack111l1ll11l1_opy_)
    except Exception as e:
        logger.error(bstack1ll1111ll_opy_.format(str(e)))
def bstack1ll11111ll_opy_():
  try:
    bstack111llll1ll1_opy_ = os.path.join(tempfile.gettempdir(), bstack1ll_opy_ (u"ࠩࡲࡴࡹ࡯࡭ࡢ࡮ࡢ࡬ࡺࡨ࡟ࡶࡴ࡯࠲࡯ࡹ࡯࡯ࠩᴶ"))
    bstack111ll11111l_opy_ = []
    if os.path.exists(bstack111llll1ll1_opy_):
      with open(bstack111llll1ll1_opy_) as f:
        bstack111ll11111l_opy_ = json.load(f)
      os.remove(bstack111llll1ll1_opy_)
    return bstack111ll11111l_opy_
  except:
    pass
  return []
def bstack1l11l1lll1_opy_(bstack1l1llllll_opy_):
  try:
    bstack111ll11111l_opy_ = []
    bstack111llll1ll1_opy_ = os.path.join(tempfile.gettempdir(), bstack1ll_opy_ (u"ࠪࡳࡵࡺࡩ࡮ࡣ࡯ࡣ࡭ࡻࡢࡠࡷࡵࡰ࠳ࡰࡳࡰࡰࠪᴷ"))
    if os.path.exists(bstack111llll1ll1_opy_):
      with open(bstack111llll1ll1_opy_) as f:
        bstack111ll11111l_opy_ = json.load(f)
    bstack111ll11111l_opy_.append(bstack1l1llllll_opy_)
    with open(bstack111llll1ll1_opy_, bstack1ll_opy_ (u"ࠫࡼ࠭ᴸ")) as f:
        json.dump(bstack111ll11111l_opy_, f)
  except:
    pass
def bstack1l1lll1l_opy_(logger, bstack111ll1l111l_opy_ = False):
  try:
    test_name = os.environ.get(bstack1ll_opy_ (u"ࠬࡖ࡙ࡕࡇࡖࡘࡤ࡚ࡅࡔࡖࡢࡒࡆࡓࡅࠨᴹ"), bstack1ll_opy_ (u"࠭ࠧᴺ"))
    if test_name == bstack1ll_opy_ (u"ࠧࠨᴻ"):
        test_name = threading.current_thread().__dict__.get(bstack1ll_opy_ (u"ࠨࡲࡼࡸࡪࡹࡴࡃࡦࡧࡣࡹ࡫ࡳࡵࡡࡱࡥࡲ࡫ࠧᴼ"), bstack1ll_opy_ (u"ࠩࠪᴽ"))
    bstack111l1llll11_opy_ = bstack1ll_opy_ (u"ࠪ࠰ࠥ࠭ᴾ").join(threading.current_thread().bstackTestErrorMessages)
    if bstack111ll1l111l_opy_:
        bstack11l1l1l1_opy_ = os.environ.get(bstack1ll_opy_ (u"ࠫࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡔࡑࡇࡔࡇࡑࡕࡑࡤࡏࡎࡅࡇ࡛ࠫᴿ"), bstack1ll_opy_ (u"ࠬ࠶ࠧᵀ"))
        bstack1l11111l1_opy_ = {bstack1ll_opy_ (u"࠭࡮ࡢ࡯ࡨࠫᵁ"): test_name, bstack1ll_opy_ (u"ࠧࡦࡴࡵࡳࡷ࠭ᵂ"): bstack111l1llll11_opy_, bstack1ll_opy_ (u"ࠨ࡫ࡱࡨࡪࡾࠧᵃ"): bstack11l1l1l1_opy_}
        bstack111lllll11l_opy_ = []
        bstack111ll1lll1l_opy_ = os.path.join(tempfile.gettempdir(), bstack1ll_opy_ (u"ࠩࡳࡽࡹ࡫ࡳࡵࡡࡳࡴࡵࡥࡥࡳࡴࡲࡶࡤࡲࡩࡴࡶ࠱࡮ࡸࡵ࡮ࠨᵄ"))
        if os.path.exists(bstack111ll1lll1l_opy_):
            with open(bstack111ll1lll1l_opy_) as f:
                bstack111lllll11l_opy_ = json.load(f)
        bstack111lllll11l_opy_.append(bstack1l11111l1_opy_)
        with open(bstack111ll1lll1l_opy_, bstack1ll_opy_ (u"ࠪࡻࠬᵅ")) as f:
            json.dump(bstack111lllll11l_opy_, f)
    else:
        bstack1l11111l1_opy_ = {bstack1ll_opy_ (u"ࠫࡳࡧ࡭ࡦࠩᵆ"): test_name, bstack1ll_opy_ (u"ࠬ࡫ࡲࡳࡱࡵࠫᵇ"): bstack111l1llll11_opy_, bstack1ll_opy_ (u"࠭ࡩ࡯ࡦࡨࡼࠬᵈ"): str(multiprocessing.current_process().name)}
        if bstack1ll_opy_ (u"ࠧࡣࡵࡷࡥࡨࡱ࡟ࡦࡴࡵࡳࡷࡥ࡬ࡪࡵࡷࠫᵉ") not in multiprocessing.current_process().__dict__.keys():
            multiprocessing.current_process().bstack_error_list = []
        multiprocessing.current_process().bstack_error_list.append(bstack1l11111l1_opy_)
  except Exception as e:
      logger.warn(bstack1ll_opy_ (u"ࠣࡗࡱࡥࡧࡲࡥࠡࡶࡲࠤࡸࡺ࡯ࡳࡧࠣࡴࡾࡺࡥࡴࡶࠣࡪࡺࡴ࡮ࡦ࡮ࠣࡨࡦࡺࡡ࠻ࠢࡾࢁࠧᵊ").format(e))
def bstack11l111ll1l_opy_(error_message, test_name, index, logger):
  try:
    from filelock import FileLock
  except ImportError:
    logger.debug(bstack1ll_opy_ (u"ࠩࡩ࡭ࡱ࡫࡬ࡰࡥ࡮ࠤࡳࡵࡴࠡࡣࡹࡥ࡮ࡲࡡࡣ࡮ࡨ࠰ࠥࡻࡳࡪࡰࡪࠤࡧࡧࡳࡪࡥࠣࡪ࡮ࡲࡥࠡࡱࡳࡩࡷࡧࡴࡪࡱࡱࡷࠬᵋ"))
    try:
      bstack11l111l1111_opy_ = []
      bstack1l11111l1_opy_ = {bstack1ll_opy_ (u"ࠪࡲࡦࡳࡥࠨᵌ"): test_name, bstack1ll_opy_ (u"ࠫࡪࡸࡲࡰࡴࠪᵍ"): error_message, bstack1ll_opy_ (u"ࠬ࡯࡮ࡥࡧࡻࠫᵎ"): index}
      bstack11l111111l1_opy_ = os.path.join(tempfile.gettempdir(), bstack1ll_opy_ (u"࠭ࡲࡰࡤࡲࡸࡤ࡫ࡲࡳࡱࡵࡣࡱ࡯ࡳࡵ࠰࡭ࡷࡴࡴࠧᵏ"))
      if os.path.exists(bstack11l111111l1_opy_):
          with open(bstack11l111111l1_opy_) as f:
              bstack11l111l1111_opy_ = json.load(f)
      bstack11l111l1111_opy_.append(bstack1l11111l1_opy_)
      with open(bstack11l111111l1_opy_, bstack1ll_opy_ (u"ࠧࡸࠩᵐ")) as f:
          json.dump(bstack11l111l1111_opy_, f)
    except Exception as e:
      logger.warn(bstack1ll_opy_ (u"ࠣࡗࡱࡥࡧࡲࡥࠡࡶࡲࠤࡸࡺ࡯ࡳࡧࠣࡶࡴࡨ࡯ࡵࠢࡩࡹࡳࡴࡥ࡭ࠢࡧࡥࡹࡧ࠺ࠡࡽࢀࠦᵑ").format(e))
    return
  bstack11l111l1111_opy_ = []
  bstack1l11111l1_opy_ = {bstack1ll_opy_ (u"ࠩࡱࡥࡲ࡫ࠧᵒ"): test_name, bstack1ll_opy_ (u"ࠪࡩࡷࡸ࡯ࡳࠩᵓ"): error_message, bstack1ll_opy_ (u"ࠫ࡮ࡴࡤࡦࡺࠪᵔ"): index}
  bstack11l111111l1_opy_ = os.path.join(tempfile.gettempdir(), bstack1ll_opy_ (u"ࠬࡸ࡯ࡣࡱࡷࡣࡪࡸࡲࡰࡴࡢࡰ࡮ࡹࡴ࠯࡬ࡶࡳࡳ࠭ᵕ"))
  lock_file = bstack11l111111l1_opy_ + bstack1ll_opy_ (u"࠭࠮࡭ࡱࡦ࡯ࠬᵖ")
  try:
    with FileLock(lock_file, timeout=10):
      if os.path.exists(bstack11l111111l1_opy_):
          with open(bstack11l111111l1_opy_, bstack1ll_opy_ (u"ࠧࡳࠩᵗ")) as f:
              content = f.read().strip()
              if content:
                  bstack11l111l1111_opy_ = json.load(open(bstack11l111111l1_opy_))
      bstack11l111l1111_opy_.append(bstack1l11111l1_opy_)
      with open(bstack11l111111l1_opy_, bstack1ll_opy_ (u"ࠨࡹࠪᵘ")) as f:
          json.dump(bstack11l111l1111_opy_, f)
  except Exception as e:
    logger.warn(bstack1ll_opy_ (u"ࠤࡘࡲࡦࡨ࡬ࡦࠢࡷࡳࠥࡹࡴࡰࡴࡨࠤࡷࡵࡢࡰࡶࠣࡪࡺࡴ࡮ࡦ࡮ࠣࡨࡦࡺࡡࠡࡹ࡬ࡸ࡭ࠦࡦࡪ࡮ࡨࠤࡱࡵࡣ࡬࡫ࡱ࡫࠿ࠦࡻࡾࠤᵙ").format(e))
def bstack1ll1l11111_opy_(bstack1l111l1l_opy_, name, logger):
  try:
    bstack1l11111l1_opy_ = {bstack1ll_opy_ (u"ࠪࡲࡦࡳࡥࠨᵚ"): name, bstack1ll_opy_ (u"ࠫࡪࡸࡲࡰࡴࠪᵛ"): bstack1l111l1l_opy_, bstack1ll_opy_ (u"ࠬ࡯࡮ࡥࡧࡻࠫᵜ"): str(threading.current_thread()._name)}
    return bstack1l11111l1_opy_
  except Exception as e:
    logger.warn(bstack1ll_opy_ (u"ࠨࡕ࡯ࡣࡥࡰࡪࠦࡴࡰࠢࡶࡸࡴࡸࡥࠡࡤࡨ࡬ࡦࡼࡥࠡࡨࡸࡲࡳ࡫࡬ࠡࡦࡤࡸࡦࡀࠠࡼࡿࠥᵝ").format(e))
  return
def bstack11l1111lll1_opy_():
    return platform.system() == bstack1ll_opy_ (u"ࠧࡘ࡫ࡱࡨࡴࡽࡳࠨᵞ")
def bstack1ll1l111_opy_(bstack111ll11l111_opy_, config, logger):
    bstack11l11111111_opy_ = {}
    try:
        return {key: config[key] for key in config if bstack111ll11l111_opy_.match(key)}
    except Exception as e:
        logger.debug(bstack1ll_opy_ (u"ࠣࡗࡱࡥࡧࡲࡥࠡࡶࡲࠤ࡫࡯࡬ࡵࡧࡵࠤࡨࡵ࡮ࡧ࡫ࡪࠤࡰ࡫ࡹࡴࠢࡥࡽࠥࡸࡥࡨࡧࡻࠤࡲࡧࡴࡤࡪ࠽ࠤࢀࢃࠢᵟ").format(e))
    return bstack11l11111111_opy_
def bstack111llll1l11_opy_(bstack111ll11lll1_opy_, bstack111llllllll_opy_):
    bstack11l111ll111_opy_ = version.parse(bstack111ll11lll1_opy_)
    bstack111ll11l1ll_opy_ = version.parse(bstack111llllllll_opy_)
    if bstack11l111ll111_opy_ > bstack111ll11l1ll_opy_:
        return 1
    elif bstack11l111ll111_opy_ < bstack111ll11l1ll_opy_:
        return -1
    else:
        return 0
def bstack111l11ll1l_opy_():
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
def bstack111llll11l1_opy_(timestamp):
    return datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc).replace(tzinfo=None)
def bstack111lll1llll_opy_(framework):
    from browserstack_sdk._version import __version__
    return str(framework) + str(__version__)
def bstack11111ll1l_opy_(options, framework, config, bstack11l1l111ll_opy_={}):
    if options is None:
        return
    if getattr(options, bstack1ll_opy_ (u"ࠩࡪࡩࡹ࠭ᵠ"), None):
        caps = options
    else:
        caps = options.to_capabilities()
    bstack1lll1ll1_opy_ = caps.get(bstack1ll_opy_ (u"ࠪࡦࡸࡺࡡࡤ࡭࠽ࡳࡵࡺࡩࡰࡰࡶࠫᵡ"))
    bstack111lll1ll1l_opy_ = True
    bstack1111l1lll_opy_ = os.environ[bstack1ll_opy_ (u"ࠫࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡘࡊ࡙ࡔࡉࡗࡅࡣ࡚࡛ࡉࡅࠩᵢ")]
    bstack1l1llllllll_opy_ = config.get(bstack1ll_opy_ (u"ࠬࡧࡣࡤࡧࡶࡷ࡮ࡨࡩ࡭࡫ࡷࡽࠬᵣ"), False)
    if bstack1l1llllllll_opy_:
        bstack1ll1ll11lll_opy_ = config.get(bstack1ll_opy_ (u"࠭ࡡࡤࡥࡨࡷࡸ࡯ࡢࡪ࡮࡬ࡸࡾࡕࡰࡵ࡫ࡲࡲࡸ࠭ᵤ"), {})
        bstack1ll1ll11lll_opy_[bstack1ll_opy_ (u"ࠧࡢࡷࡷ࡬࡙ࡵ࡫ࡦࡰࠪᵥ")] = os.getenv(bstack1ll_opy_ (u"ࠨࡄࡖࡣࡆ࠷࠱࡚ࡡࡍ࡛࡙࠭ᵦ"))
        bstack11ll11l1lll_opy_ = json.loads(os.getenv(bstack1ll_opy_ (u"ࠩࡅࡖࡔ࡝ࡓࡆࡔࡖࡘࡆࡉࡋࡠࡖࡈࡗ࡙ࡥࡁࡄࡅࡈࡗࡘࡏࡂࡊࡎࡌࡘ࡞ࡥࡃࡐࡐࡉࡍࡌ࡛ࡒࡂࡖࡌࡓࡓࡥ࡙ࡎࡎࠪᵧ"), bstack1ll_opy_ (u"ࠪࡿࢂ࠭ᵨ"))).get(bstack1ll_opy_ (u"ࠫࡸࡩࡡ࡯ࡰࡨࡶ࡛࡫ࡲࡴ࡫ࡲࡲࠬᵩ"))
    if bstack111ll111l11_opy_(caps.get(bstack1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮࠲ࡺࡹࡥࡘ࠵ࡆࠫᵪ"))) or bstack111ll111l11_opy_(caps.get(bstack1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯࠳ࡻࡳࡦࡡࡺ࠷ࡨ࠭ᵫ"))):
        bstack111lll1ll1l_opy_ = False
    if bstack1l1111l11l_opy_({bstack1ll_opy_ (u"ࠢࡶࡵࡨ࡛࠸ࡉࠢᵬ"): bstack111lll1ll1l_opy_}):
        bstack1lll1ll1_opy_ = bstack1lll1ll1_opy_ or {}
        bstack1lll1ll1_opy_[bstack1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱࡓࡅࡍࠪᵭ")] = bstack111lll1llll_opy_(framework)
        bstack1lll1ll1_opy_[bstack1ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫ࡂࡷࡷࡳࡲࡧࡴࡪࡱࡱࠫᵮ")] = bstack1l1ll111lll_opy_()
        bstack1lll1ll1_opy_[bstack1ll_opy_ (u"ࠪࡸࡪࡹࡴࡩࡷࡥࡆࡺ࡯࡬ࡥࡗࡸ࡭ࡩ࠭ᵯ")] = bstack1111l1lll_opy_
        bstack1lll1ll1_opy_[bstack1ll_opy_ (u"ࠫࡧࡻࡩ࡭ࡦࡓࡶࡴࡪࡵࡤࡶࡐࡥࡵ࠭ᵰ")] = bstack11l1l111ll_opy_
        if bstack1l1llllllll_opy_:
            bstack1lll1ll1_opy_[bstack1ll_opy_ (u"ࠬࡧࡣࡤࡧࡶࡷ࡮ࡨࡩ࡭࡫ࡷࡽࠬᵱ")] = bstack1l1llllllll_opy_
            bstack1lll1ll1_opy_[bstack1ll_opy_ (u"࠭ࡡࡤࡥࡨࡷࡸ࡯ࡢࡪ࡮࡬ࡸࡾࡕࡰࡵ࡫ࡲࡲࡸ࠭ᵲ")] = bstack1ll1ll11lll_opy_
            bstack1lll1ll1_opy_[bstack1ll_opy_ (u"ࠧࡢࡥࡦࡩࡸࡹࡩࡣ࡫࡯࡭ࡹࡿࡏࡱࡶ࡬ࡳࡳࡹࠧᵳ")][bstack1ll_opy_ (u"ࠨࡵࡦࡥࡳࡴࡥࡳࡘࡨࡶࡸ࡯࡯࡯ࠩᵴ")] = bstack11ll11l1lll_opy_
        if getattr(options, bstack1ll_opy_ (u"ࠩࡶࡩࡹࡥࡣࡢࡲࡤࡦ࡮ࡲࡩࡵࡻࠪᵵ"), None):
            options.set_capability(bstack1ll_opy_ (u"ࠪࡦࡸࡺࡡࡤ࡭࠽ࡳࡵࡺࡩࡰࡰࡶࠫᵶ"), bstack1lll1ll1_opy_)
        else:
            options[bstack1ll_opy_ (u"ࠫࡧࡹࡴࡢࡥ࡮࠾ࡴࡶࡴࡪࡱࡱࡷࠬᵷ")] = bstack1lll1ll1_opy_
    else:
        if getattr(options, bstack1ll_opy_ (u"ࠬࡹࡥࡵࡡࡦࡥࡵࡧࡢࡪ࡮࡬ࡸࡾ࠭ᵸ"), None):
            options.set_capability(bstack1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯࠳ࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮ࡗࡉࡑࠧᵹ"), bstack111lll1llll_opy_(framework))
            options.set_capability(bstack1ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰ࠴ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯ࡆࡻࡴࡰ࡯ࡤࡸ࡮ࡵ࡮ࠨᵺ"), bstack1l1ll111lll_opy_())
            options.set_capability(bstack1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࠮ࡵࡧࡶࡸ࡭ࡻࡢࡃࡷ࡬ࡰࡩ࡛ࡵࡪࡦࠪᵻ"), bstack1111l1lll_opy_)
            options.set_capability(bstack1ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫࠯ࡤࡸ࡭ࡱࡪࡐࡳࡱࡧࡹࡨࡺࡍࡢࡲࠪᵼ"), bstack11l1l111ll_opy_)
            if bstack1l1llllllll_opy_:
                options.set_capability(bstack1ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬࠰ࡤࡧࡨ࡫ࡳࡴ࡫ࡥ࡭ࡱ࡯ࡴࡺࠩᵽ"), bstack1l1llllllll_opy_)
                options.set_capability(bstack1ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭࠱ࡥࡨࡩࡥࡴࡵ࡬ࡦ࡮ࡲࡩࡵࡻࡒࡴࡹ࡯࡯࡯ࡵࠪᵾ"), bstack1ll1ll11lll_opy_)
                options.set_capability(bstack1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮࠲ࡦࡩࡣࡦࡵࡶ࡭ࡧ࡯࡬ࡪࡶࡼࡓࡵࡺࡩࡰࡰࡶ࠲ࡸࡩࡡ࡯ࡰࡨࡶ࡛࡫ࡲࡴ࡫ࡲࡲࠬᵿ"), bstack11ll11l1lll_opy_)
        else:
            options[bstack1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯࠳ࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮ࡗࡉࡑࠧᶀ")] = bstack111lll1llll_opy_(framework)
            options[bstack1ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰ࠴ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯ࡆࡻࡴࡰ࡯ࡤࡸ࡮ࡵ࡮ࠨᶁ")] = bstack1l1ll111lll_opy_()
            options[bstack1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࠮ࡵࡧࡶࡸ࡭ࡻࡢࡃࡷ࡬ࡰࡩ࡛ࡵࡪࡦࠪᶂ")] = bstack1111l1lll_opy_
            options[bstack1ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫࠯ࡤࡸ࡭ࡱࡪࡐࡳࡱࡧࡹࡨࡺࡍࡢࡲࠪᶃ")] = bstack11l1l111ll_opy_
            if bstack1l1llllllll_opy_:
                options[bstack1ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬࠰ࡤࡧࡨ࡫ࡳࡴ࡫ࡥ࡭ࡱ࡯ࡴࡺࠩᶄ")] = bstack1l1llllllll_opy_
                options[bstack1ll_opy_ (u"ࠫࡧࡸ࡯ࡸࡵࡨࡶࡸࡺࡡࡤ࡭࠱ࡥࡨࡩࡥࡴࡵ࡬ࡦ࡮ࡲࡩࡵࡻࡒࡴࡹ࡯࡯࡯ࡵࠪᶅ")] = bstack1ll1ll11lll_opy_
                options[bstack1ll_opy_ (u"ࠬࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮࠲ࡦࡩࡣࡦࡵࡶ࡭ࡧ࡯࡬ࡪࡶࡼࡓࡵࡺࡩࡰࡰࡶࠫᶆ")][bstack1ll_opy_ (u"࠭ࡳࡤࡣࡱࡲࡪࡸࡖࡦࡴࡶ࡭ࡴࡴࠧᶇ")] = bstack11ll11l1lll_opy_
    return options
def bstack11l111lll11_opy_(bstack11l111l1lll_opy_, framework):
    bstack11l1l111ll_opy_ = bstack1ll1l1l111_opy_.get_property(bstack1ll_opy_ (u"ࠢࡑࡎࡄ࡝࡜ࡘࡉࡈࡊࡗࡣࡕࡘࡏࡅࡗࡆࡘࡤࡓࡁࡑࠤᶈ"))
    if bstack11l111l1lll_opy_ and len(bstack11l111l1lll_opy_.split(bstack1ll_opy_ (u"ࠨࡥࡤࡴࡸࡃࠧᶉ"))) > 1:
        ws_url = bstack11l111l1lll_opy_.split(bstack1ll_opy_ (u"ࠩࡦࡥࡵࡹ࠽ࠨᶊ"))[0]
        if bstack1ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬࠰ࡦࡳࡲ࠭ᶋ") in ws_url:
            from browserstack_sdk._version import __version__
            bstack111l1llll1l_opy_ = json.loads(urllib.parse.unquote(bstack11l111l1lll_opy_.split(bstack1ll_opy_ (u"ࠫࡨࡧࡰࡴ࠿ࠪᶌ"))[1]))
            bstack111l1llll1l_opy_ = bstack111l1llll1l_opy_ or {}
            bstack1111l1lll_opy_ = os.environ[bstack1ll_opy_ (u"ࠬࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣ࡙ࡋࡓࡕࡊࡘࡆࡤ࡛ࡕࡊࡆࠪᶍ")]
            bstack111l1llll1l_opy_[bstack1ll_opy_ (u"࠭ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯࠳ࡨࡲࡰࡹࡶࡩࡷࡹࡴࡢࡥ࡮ࡗࡉࡑࠧᶎ")] = str(framework) + str(__version__)
            bstack111l1llll1l_opy_[bstack1ll_opy_ (u"ࠧࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰ࠴ࡢࡳࡱࡺࡷࡪࡸࡳࡵࡣࡦ࡯ࡆࡻࡴࡰ࡯ࡤࡸ࡮ࡵ࡮ࠨᶏ")] = bstack1l1ll111lll_opy_()
            bstack111l1llll1l_opy_[bstack1ll_opy_ (u"ࠨࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱ࠮ࡵࡧࡶࡸ࡭ࡻࡢࡃࡷ࡬ࡰࡩ࡛ࡵࡪࡦࠪᶐ")] = bstack1111l1lll_opy_
            bstack111l1llll1l_opy_[bstack1ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫࠯ࡤࡸ࡭ࡱࡪࡐࡳࡱࡧࡹࡨࡺࡍࡢࡲࠪᶑ")] = bstack11l1l111ll_opy_
            bstack11l111l1lll_opy_ = bstack11l111l1lll_opy_.split(bstack1ll_opy_ (u"ࠪࡧࡦࡶࡳ࠾ࠩᶒ"))[0] + bstack1ll_opy_ (u"ࠫࡨࡧࡰࡴ࠿ࠪᶓ") + urllib.parse.quote(json.dumps(bstack111l1llll1l_opy_))
    return bstack11l111l1lll_opy_
def bstack1l1111l11_opy_():
    global bstack111lll1l1l_opy_
    from playwright._impl._browser_type import BrowserType
    bstack111lll1l1l_opy_ = BrowserType.connect
    return bstack111lll1l1l_opy_
def bstack11l1lllll_opy_(framework_name):
    global bstack11l11ll111_opy_
    bstack11l11ll111_opy_ = framework_name
    return framework_name
def bstack111lllll1_opy_(self, *args, **kwargs):
    global bstack111lll1l1l_opy_
    try:
        global bstack11l11ll111_opy_
        if bstack1ll_opy_ (u"ࠬࡽࡳࡆࡰࡧࡴࡴ࡯࡮ࡵࠩᶔ") in kwargs:
            kwargs[bstack1ll_opy_ (u"࠭ࡷࡴࡇࡱࡨࡵࡵࡩ࡯ࡶࠪᶕ")] = bstack11l111lll11_opy_(
                kwargs.get(bstack1ll_opy_ (u"ࠧࡸࡵࡈࡲࡩࡶ࡯ࡪࡰࡷࠫᶖ"), None),
                bstack11l11ll111_opy_
            )
    except Exception as e:
        logger.error(bstack1ll_opy_ (u"ࠣࡇࡵࡶࡴࡸࠠࡸࡪࡨࡲࠥࡶࡲࡰࡥࡨࡷࡸ࡯࡮ࡨࠢࡖࡈࡐࠦࡣࡢࡲࡶ࠾ࠥࢁࡽࠣᶗ").format(str(e)))
    return bstack111lll1l1l_opy_(self, *args, **kwargs)
def bstack111l1lll1l1_opy_(bstack111lll11111_opy_, proxies):
    proxy_settings = {}
    try:
        if not proxies:
            proxies = bstack11ll11llll_opy_(bstack111lll11111_opy_, bstack1ll_opy_ (u"ࠤࠥᶘ"))
        if proxies and proxies.get(bstack1ll_opy_ (u"ࠥ࡬ࡹࡺࡰࡴࠤᶙ")):
            parsed_url = urlparse(proxies.get(bstack1ll_opy_ (u"ࠦ࡭ࡺࡴࡱࡵࠥᶚ")))
            if parsed_url and parsed_url.hostname: proxy_settings[bstack1ll_opy_ (u"ࠬࡶࡲࡰࡺࡼࡌࡴࡹࡴࠨᶛ")] = str(parsed_url.hostname)
            if parsed_url and parsed_url.port: proxy_settings[bstack1ll_opy_ (u"࠭ࡰࡳࡱࡻࡽࡕࡵࡲࡵࠩᶜ")] = str(parsed_url.port)
            if parsed_url and parsed_url.username: proxy_settings[bstack1ll_opy_ (u"ࠧࡱࡴࡲࡼࡾ࡛ࡳࡦࡴࠪᶝ")] = str(parsed_url.username)
            if parsed_url and parsed_url.password: proxy_settings[bstack1ll_opy_ (u"ࠨࡲࡵࡳࡽࡿࡐࡢࡵࡶࠫᶞ")] = str(parsed_url.password)
        return proxy_settings
    except:
        return proxy_settings
def bstack111ll1l1_opy_(bstack111lll11111_opy_):
    bstack111l1ll11ll_opy_ = {
        bstack11l1l1l1111_opy_[bstack111ll1l1ll1_opy_]: bstack111lll11111_opy_[bstack111ll1l1ll1_opy_]
        for bstack111ll1l1ll1_opy_ in bstack111lll11111_opy_
        if bstack111ll1l1ll1_opy_ in bstack11l1l1l1111_opy_
    }
    bstack111l1ll11ll_opy_[bstack1ll_opy_ (u"ࠤࡳࡶࡴࡾࡹࡔࡧࡷࡸ࡮ࡴࡧࡴࠤᶟ")] = bstack111l1lll1l1_opy_(bstack111lll11111_opy_, bstack1ll1l1l111_opy_.get_property(bstack1ll_opy_ (u"ࠥࡴࡷࡵࡸࡺࡕࡨࡸࡹ࡯࡮ࡨࡵࠥᶠ")))
    bstack111lll1lll1_opy_ = [element.lower() for element in bstack11l1l1l1ll1_opy_]
    bstack111l1lll11l_opy_(bstack111l1ll11ll_opy_, bstack111lll1lll1_opy_)
    return bstack111l1ll11ll_opy_
def bstack111l1lll11l_opy_(d, keys):
    for key in list(d.keys()):
        if key.lower() in keys:
            d[key] = bstack1ll_opy_ (u"ࠦ࠯࠰ࠪࠫࠤᶡ")
    for value in d.values():
        if isinstance(value, dict):
            bstack111l1lll11l_opy_(value, keys)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    bstack111l1lll11l_opy_(item, keys)
def bstack1l1l1l1l11l_opy_():
    bstack111l1ll1l1l_opy_ = [os.environ.get(bstack1ll_opy_ (u"ࠧࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣࡋࡏࡌࡆࡕࡢࡈࡎࡘࠢᶢ")), os.path.join(os.path.expanduser(bstack1ll_opy_ (u"ࠨࡾࠣᶣ")), bstack1ll_opy_ (u"ࠧ࠯ࡤࡵࡳࡼࡹࡥࡳࡵࡷࡥࡨࡱࠧᶤ")), os.path.join(bstack1ll_opy_ (u"ࠨ࠱ࡷࡱࡵ࠭ᶥ"), bstack1ll_opy_ (u"ࠩ࠱ࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬ࠩᶦ"))]
    for path in bstack111l1ll1l1l_opy_:
        if path is None:
            continue
        try:
            if os.path.exists(path):
                logger.debug(bstack1ll_opy_ (u"ࠥࡊ࡮ࡲࡥࠡࠩࠥᶧ") + str(path) + bstack1ll_opy_ (u"ࠦࠬࠦࡥࡹ࡫ࡶࡸࡸ࠴ࠢᶨ"))
                if not os.access(path, os.W_OK):
                    logger.debug(bstack1ll_opy_ (u"ࠧࡍࡩࡷ࡫ࡱ࡫ࠥࡶࡥࡳ࡯࡬ࡷࡸ࡯࡯࡯ࡵࠣࡪࡴࡸࠠࠨࠤᶩ") + str(path) + bstack1ll_opy_ (u"ࠨࠧࠣᶪ"))
                    os.chmod(path, 0o777)
                else:
                    logger.debug(bstack1ll_opy_ (u"ࠢࡇ࡫࡯ࡩࠥ࠭ࠢᶫ") + str(path) + bstack1ll_opy_ (u"ࠣࠩࠣࡥࡱࡸࡥࡢࡦࡼࠤ࡭ࡧࡳࠡࡶ࡫ࡩࠥࡸࡥࡲࡷ࡬ࡶࡪࡪࠠࡱࡧࡵࡱ࡮ࡹࡳࡪࡱࡱࡷ࠳ࠨᶬ"))
            else:
                logger.debug(bstack1ll_opy_ (u"ࠤࡆࡶࡪࡧࡴࡪࡰࡪࠤ࡫࡯࡬ࡦࠢࠪࠦᶭ") + str(path) + bstack1ll_opy_ (u"ࠥࠫࠥࡽࡩࡵࡪࠣࡻࡷ࡯ࡴࡦࠢࡳࡩࡷࡳࡩࡴࡵ࡬ࡳࡳ࠴ࠢᶮ"))
                os.makedirs(path, exist_ok=True)
                os.chmod(path, 0o777)
            logger.debug(bstack1ll_opy_ (u"ࠦࡔࡶࡥࡳࡣࡷ࡭ࡴࡴࠠࡴࡷࡦࡧࡪ࡫ࡤࡦࡦࠣࡪࡴࡸࠠࠨࠤᶯ") + str(path) + bstack1ll_opy_ (u"ࠧ࠭࠮ࠣᶰ"))
            return path
        except Exception as e:
            logger.debug(bstack1ll_opy_ (u"ࠨࡆࡢ࡫࡯ࡩࡩࠦࡴࡰࠢࡶࡩࡹࠦࡵࡱࠢࡩ࡭ࡱ࡫ࠠࠨࡽࡳࡥࡹ࡮ࡽࠨ࠼ࠣࠦᶱ") + str(e) + bstack1ll_opy_ (u"ࠢࠣᶲ"))
    logger.debug(bstack1ll_opy_ (u"ࠣࡃ࡯ࡰࠥࡶࡡࡵࡪࡶࠤ࡫ࡧࡩ࡭ࡧࡧ࠲ࠧᶳ"))
    return None
@measure(event_name=EVENTS.bstack11l1l1ll111_opy_, stage=STAGE.bstack1l1lll1ll1_opy_)
def bstack1lll11lllll_opy_(binary_path, bstack1lll11l11ll_opy_, bs_config):
    logger.debug(bstack1ll_opy_ (u"ࠤࡆࡹࡷࡸࡥ࡯ࡶࠣࡇࡑࡏࠠࡑࡣࡷ࡬ࠥ࡬࡯ࡶࡰࡧ࠾ࠥࢁࡽࠣᶴ").format(binary_path))
    bstack111ll111l1l_opy_ = bstack1ll_opy_ (u"ࠪࠫᶵ")
    bstack111lllllll1_opy_ = {
        bstack1ll_opy_ (u"ࠫࡸࡪ࡫ࡠࡸࡨࡶࡸ࡯࡯࡯ࠩᶶ"): __version__,
        bstack1ll_opy_ (u"ࠧࡵࡳࠣᶷ"): platform.system(),
        bstack1ll_opy_ (u"ࠨ࡯ࡴࡡࡤࡶࡨ࡮ࠢᶸ"): platform.machine(),
        bstack1ll_opy_ (u"ࠢࡤ࡮࡬ࡣࡻ࡫ࡲࡴ࡫ࡲࡲࠧᶹ"): bstack1ll_opy_ (u"ࠨ࠲ࠪᶺ"),
        bstack1ll_opy_ (u"ࠤࡶࡨࡰࡥ࡬ࡢࡰࡪࡹࡦ࡭ࡥࠣᶻ"): bstack1ll_opy_ (u"ࠪࡴࡾࡺࡨࡰࡰࠪᶼ")
    }
    bstack111llll1111_opy_(bstack111lllllll1_opy_)
    try:
        if binary_path:
            if bstack11l1111lll1_opy_():
                bstack111lllllll1_opy_[bstack1ll_opy_ (u"ࠫࡨࡲࡩࡠࡸࡨࡶࡸ࡯࡯࡯ࠩᶽ")] = subprocess.check_output([binary_path, bstack1ll_opy_ (u"ࠧࡼࡥࡳࡵ࡬ࡳࡳࠨᶾ")]).strip().decode(bstack1ll_opy_ (u"࠭ࡵࡵࡨ࠰࠼ࠬᶿ"))
            else:
                bstack111lllllll1_opy_[bstack1ll_opy_ (u"ࠧࡤ࡮࡬ࡣࡻ࡫ࡲࡴ࡫ࡲࡲࠬ᷀")] = subprocess.check_output([binary_path, bstack1ll_opy_ (u"ࠣࡸࡨࡶࡸ࡯࡯࡯ࠤ᷁")], stderr=subprocess.DEVNULL).strip().decode(bstack1ll_opy_ (u"ࠩࡸࡸ࡫࠳࠸ࠨ᷂"))
        response = requests.request(
            bstack1ll_opy_ (u"ࠪࡋࡊ࡚ࠧ᷃"),
            url=bstack1l1lll11ll_opy_(bstack11l1l11lll1_opy_),
            headers=None,
            auth=(bs_config[bstack1ll_opy_ (u"ࠫࡺࡹࡥࡳࡐࡤࡱࡪ࠭᷄")], bs_config[bstack1ll_opy_ (u"ࠬࡧࡣࡤࡧࡶࡷࡐ࡫ࡹࠨ᷅")]),
            json=None,
            params=bstack111lllllll1_opy_
        )
        data = response.json()
        if response.status_code == 200 and bstack1ll_opy_ (u"࠭ࡵࡳ࡮ࠪ᷆") in data.keys() and bstack1ll_opy_ (u"ࠧࡶࡲࡧࡥࡹ࡫ࡤࡠࡥ࡯࡭ࡤࡼࡥࡳࡵ࡬ࡳࡳ࠭᷇") in data.keys():
            logger.debug(bstack1ll_opy_ (u"ࠣࡐࡨࡩࡩࠦࡴࡰࠢࡸࡴࡩࡧࡴࡦࠢࡥ࡭ࡳࡧࡲࡺ࠮ࠣࡧࡺࡸࡲࡦࡰࡷࠤࡧ࡯࡮ࡢࡴࡼࠤࡻ࡫ࡲࡴ࡫ࡲࡲ࠿ࠦࡻࡾࠤ᷈").format(bstack111lllllll1_opy_[bstack1ll_opy_ (u"ࠩࡦࡰ࡮ࡥࡶࡦࡴࡶ࡭ࡴࡴࠧ᷉")]))
            if bstack1ll_opy_ (u"ࠪࡆࡗࡕࡗࡔࡇࡕࡗ࡙ࡇࡃࡌࡡࡅࡍࡓࡇࡒ࡚ࡡࡘࡖࡑ᷊࠭") in os.environ:
                logger.debug(bstack1ll_opy_ (u"ࠦࡘࡱࡩࡱࡲ࡬ࡲ࡬ࠦࡢࡪࡰࡤࡶࡾࠦࡤࡰࡹࡱࡰࡴࡧࡤࠡࡣࡶࠤࡇࡘࡏࡘࡕࡈࡖࡘ࡚ࡁࡄࡍࡢࡆࡎࡔࡁࡓ࡛ࡢ࡙ࡗࡒࠠࡪࡵࠣࡷࡪࡺࠢ᷋"))
                data[bstack1ll_opy_ (u"ࠬࡻࡲ࡭ࠩ᷌")] = os.environ[bstack1ll_opy_ (u"࠭ࡂࡓࡑ࡚ࡗࡊࡘࡓࡕࡃࡆࡏࡤࡈࡉࡏࡃࡕ࡝ࡤ࡛ࡒࡍࠩ᷍")]
            bstack111l1ll1l11_opy_ = bstack111lllll111_opy_(data[bstack1ll_opy_ (u"ࠧࡶࡴ࡯᷎ࠫ")], bstack1lll11l11ll_opy_)
            bstack111ll111l1l_opy_ = os.path.join(bstack1lll11l11ll_opy_, bstack111l1ll1l11_opy_)
            os.chmod(bstack111ll111l1l_opy_, 0o777) # bstack111ll1l1l1l_opy_ permission
            return bstack111ll111l1l_opy_
    except Exception as e:
        logger.debug(bstack1ll_opy_ (u"ࠣࡇࡵࡶࡴࡸࠠࡸࡪ࡬ࡰࡪࠦࡤࡰࡹࡱࡰࡴࡧࡤࡪࡰࡪࠤࡳ࡫ࡷࠡࡕࡇࡏࠥࢁࡽ᷏ࠣ").format(e))
    return binary_path
def bstack111llll1111_opy_(bstack111lllllll1_opy_):
    try:
        if bstack1ll_opy_ (u"ࠩ࡯࡭ࡳࡻࡸࠨ᷐") not in bstack111lllllll1_opy_[bstack1ll_opy_ (u"ࠪࡳࡸ࠭᷑")].lower():
            return
        if os.path.exists(bstack1ll_opy_ (u"ࠦ࠴࡫ࡴࡤ࠱ࡲࡷ࠲ࡸࡥ࡭ࡧࡤࡷࡪࠨ᷒")):
            with open(bstack1ll_opy_ (u"ࠧ࠵ࡥࡵࡥ࠲ࡳࡸ࠳ࡲࡦ࡮ࡨࡥࡸ࡫ࠢᷓ"), bstack1ll_opy_ (u"ࠨࡲࠣᷔ")) as f:
                bstack111ll11ll11_opy_ = {}
                for line in f:
                    if bstack1ll_opy_ (u"ࠢ࠾ࠤᷕ") in line:
                        key, value = line.rstrip().split(bstack1ll_opy_ (u"ࠣ࠿ࠥᷖ"), 1)
                        bstack111ll11ll11_opy_[key] = value.strip(bstack1ll_opy_ (u"ࠩࠥࡠࠬ࠭ᷗ"))
                bstack111lllllll1_opy_[bstack1ll_opy_ (u"ࠪࡨ࡮ࡹࡴࡳࡱࠪᷘ")] = bstack111ll11ll11_opy_.get(bstack1ll_opy_ (u"ࠦࡎࡊࠢᷙ"), bstack1ll_opy_ (u"ࠧࠨᷚ"))
        elif os.path.exists(bstack1ll_opy_ (u"ࠨ࠯ࡦࡶࡦ࠳ࡦࡲࡰࡪࡰࡨ࠱ࡷ࡫࡬ࡦࡣࡶࡩࠧᷛ")):
            bstack111lllllll1_opy_[bstack1ll_opy_ (u"ࠧࡥ࡫ࡶࡸࡷࡵࠧᷜ")] = bstack1ll_opy_ (u"ࠨࡣ࡯ࡴ࡮ࡴࡥࠨᷝ")
    except Exception as e:
        logger.debug(bstack1ll_opy_ (u"ࠤࡘࡲࡦࡨ࡬ࡦࠢࡷࡳࠥ࡭ࡥࡵࠢࡧ࡭ࡸࡺࡲࡰࠢࡲࡪࠥࡲࡩ࡯ࡷࡻࠦᷞ") + e)
@measure(event_name=EVENTS.bstack11l1l11l11l_opy_, stage=STAGE.bstack1l1lll1ll1_opy_)
def bstack111lllll111_opy_(bstack111ll1ll111_opy_, bstack11l1111ll1l_opy_):
    logger.debug(bstack1ll_opy_ (u"ࠥࡈࡴࡽ࡮࡭ࡱࡤࡨ࡮ࡴࡧࠡࡕࡇࡏࠥࡨࡩ࡯ࡣࡵࡽࠥ࡬ࡲࡰ࡯࠽ࠤࠧᷟ") + str(bstack111ll1ll111_opy_) + bstack1ll_opy_ (u"ࠦࠧᷠ"))
    zip_path = os.path.join(bstack11l1111ll1l_opy_, bstack1ll_opy_ (u"ࠧࡪ࡯ࡸࡰ࡯ࡳࡦࡪࡥࡥࡡࡩ࡭ࡱ࡫࠮ࡻ࡫ࡳࠦᷡ"))
    bstack111l1ll1l11_opy_ = bstack1ll_opy_ (u"࠭ࠧᷢ")
    with requests.get(bstack111ll1ll111_opy_, stream=True) as response:
        response.raise_for_status()
        with open(zip_path, bstack1ll_opy_ (u"ࠢࡸࡤࠥᷣ")) as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
        logger.debug(bstack1ll_opy_ (u"ࠣࡈ࡬ࡰࡪࠦࡤࡰࡹࡱࡰࡴࡧࡤࡦࡦࠣࡷࡺࡩࡣࡦࡵࡶࡪࡺࡲ࡬ࡺ࠰ࠥᷤ"))
    with zipfile.ZipFile(zip_path, bstack1ll_opy_ (u"ࠩࡵࠫᷥ")) as zip_ref:
        bstack111lll1l1l1_opy_ = zip_ref.namelist()
        if len(bstack111lll1l1l1_opy_) > 0:
            bstack111l1ll1l11_opy_ = bstack111lll1l1l1_opy_[0] # bstack111llllll1l_opy_ bstack11l1l111l1l_opy_ will be bstack11l111l1l1l_opy_ 1 file i.e. the binary in the zip
        zip_ref.extractall(bstack11l1111ll1l_opy_)
        logger.debug(bstack1ll_opy_ (u"ࠥࡊ࡮ࡲࡥࡴࠢࡶࡹࡨࡩࡥࡴࡵࡩࡹࡱࡲࡹࠡࡧࡻࡸࡷࡧࡣࡵࡧࡧࠤࡹࡵࠠࠨࠤᷦ") + str(bstack11l1111ll1l_opy_) + bstack1ll_opy_ (u"ࠦࠬࠨᷧ"))
    os.remove(zip_path)
    return bstack111l1ll1l11_opy_
def get_cli_dir():
    bstack11l11111l1l_opy_ = bstack1l1l1l1l11l_opy_()
    if bstack11l11111l1l_opy_:
        bstack1lll11l11ll_opy_ = os.path.join(bstack11l11111l1l_opy_, bstack1ll_opy_ (u"ࠧࡩ࡬ࡪࠤᷨ"))
        if not os.path.exists(bstack1lll11l11ll_opy_):
            os.makedirs(bstack1lll11l11ll_opy_, mode=0o777, exist_ok=True)
        return bstack1lll11l11ll_opy_
    else:
        raise FileNotFoundError(bstack1ll_opy_ (u"ࠨࡎࡰࠢࡺࡶ࡮ࡺࡡࡣ࡮ࡨࠤࡩ࡯ࡲࡦࡥࡷࡳࡷࡿࠠࡢࡸࡤ࡭ࡱࡧࡢ࡭ࡧࠣࡪࡴࡸࠠࡵࡪࡨࠤࡘࡊࡋࠡࡤ࡬ࡲࡦࡸࡹ࠯ࠤᷩ"))
def bstack1ll1ll1ll1l_opy_(bstack1lll11l11ll_opy_):
    bstack1ll_opy_ (u"ࠢࠣࠤࡊࡩࡹࠦࡴࡩࡧࠣࡴࡦࡺࡨࠡࡨࡲࡶࠥࡺࡨࡦࠢࡅࡶࡴࡽࡳࡦࡴࡖࡸࡦࡩ࡫ࠡࡕࡇࡏࠥࡨࡩ࡯ࡣࡵࡽࠥ࡯࡮ࠡࡣࠣࡻࡷ࡯ࡴࡢࡤ࡯ࡩࠥࡪࡩࡳࡧࡦࡸࡴࡸࡹ࠯ࠤࠥࠦᷪ")
    bstack111l1ll111l_opy_ = [
        os.path.join(bstack1lll11l11ll_opy_, f)
        for f in os.listdir(bstack1lll11l11ll_opy_)
        if os.path.isfile(os.path.join(bstack1lll11l11ll_opy_, f)) and f.startswith(bstack1ll_opy_ (u"ࠣࡤ࡬ࡲࡦࡸࡹ࠮ࠤᷫ"))
    ]
    if len(bstack111l1ll111l_opy_) > 0:
        return max(bstack111l1ll111l_opy_, key=os.path.getmtime) # get bstack111ll1111ll_opy_ binary
    return bstack1ll_opy_ (u"ࠤࠥᷬ")
def bstack11ll1111l11_opy_():
  from selenium import webdriver
  return version.parse(webdriver.__version__)
def bstack1l1llllll1l_opy_(d, u):
  for k, v in u.items():
    if isinstance(v, collections.abc.Mapping):
      d[k] = bstack1l1llllll1l_opy_(d.get(k, {}), v)
    else:
      if isinstance(v, list):
        d[k] = d.get(k, []) + v
      else:
        d[k] = v
  return d
def bstack11l1111l1_opy_(data, keys, default=None):
    bstack1ll_opy_ (u"ࠥࠦࠧࠐࠠࠡࠢࠣࡗࡦ࡬ࡥ࡭ࡻࠣ࡫ࡪࡺࠠࡢࠢࡱࡩࡸࡺࡥࡥࠢࡹࡥࡱࡻࡥࠡࡨࡵࡳࡲࠦࡡࠡࡦ࡬ࡧࡹ࡯࡯࡯ࡣࡵࡽࠥࡵࡲࠡ࡮࡬ࡷࡹ࠴ࠊࠡࠢࠣࠤ࠿ࡶࡡࡳࡣࡰࠤࡩࡧࡴࡢ࠼ࠣࡘ࡭࡫ࠠࡥ࡫ࡦࡸ࡮ࡵ࡮ࡢࡴࡼࠤࡴࡸࠠ࡭࡫ࡶࡸࠥࡺ࡯ࠡࡶࡵࡥࡻ࡫ࡲࡴࡧ࠱ࠎࠥࠦࠠࠡ࠼ࡳࡥࡷࡧ࡭ࠡ࡭ࡨࡽࡸࡀࠠࡂࠢ࡯࡭ࡸࡺࠠࡰࡨࠣ࡯ࡪࡿࡳ࠰࡫ࡱࡨ࡮ࡩࡥࡴࠢࡵࡩࡵࡸࡥࡴࡧࡱࡸ࡮ࡴࡧࠡࡶ࡫ࡩࠥࡶࡡࡵࡪ࠱ࠎࠥࠦࠠࠡ࠼ࡳࡥࡷࡧ࡭ࠡࡦࡨࡪࡦࡻ࡬ࡵ࠼࡚ࠣࡦࡲࡵࡦࠢࡷࡳࠥࡸࡥࡵࡷࡵࡲࠥ࡯ࡦࠡࡶ࡫ࡩࠥࡶࡡࡵࡪࠣࡨࡴ࡫ࡳࠡࡰࡲࡸࠥ࡫ࡸࡪࡵࡷ࠲ࠏࠦࠠࠡࠢ࠽ࡶࡪࡺࡵࡳࡰ࠽ࠤ࡙࡮ࡥࠡࡸࡤࡰࡺ࡫ࠠࡢࡶࠣࡸ࡭࡫ࠠ࡯ࡧࡶࡸࡪࡪࠠࡱࡣࡷ࡬࠱ࠦ࡯ࡳࠢࡧࡩ࡫ࡧࡵ࡭ࡶࠣ࡭࡫ࠦ࡮ࡰࡶࠣࡪࡴࡻ࡮ࡥ࠰ࠍࠤࠥࠦࠠࠣࠤࠥᷭ")
    if not data:
        return default
    current = data
    try:
        for key in keys:
            if isinstance(current, dict):
                current = current[key]
            elif isinstance(current, list) and isinstance(key, int):
                current = current[key]
            else:
                return default
        return current
    except (KeyError, IndexError, TypeError):
        return default
def bstack11111l111_opy_(bstack11l111lllll_opy_, key, value):
    bstack1ll_opy_ (u"ࠦࠧࠨࠊࠡࠢࠣࠤࡘࡺ࡯ࡳࡧࠣࡇࡑࡏࠠࡦࡰࡹ࡭ࡷࡵ࡮࡮ࡧࡱࡸࠥࡼࡡࡳ࡫ࡤࡦࡱ࡫ࡳࠡ࡯ࡤࡴࡵ࡯࡮ࡨࠢ࡬ࡲࠥࡺࡨࡦࠢࡳࡶࡴࡼࡩࡥࡧࡧࠤࡩ࡯ࡣࡵ࡫ࡲࡲࡦࡸࡹ࠯ࠌࠣࠤࠥࠦࡁࡳࡩࡶ࠾ࠏࠦࠠࠡࠢࠣࠤࠥࠦࡣ࡭࡫ࡢࡩࡳࡼ࡟ࡷࡣࡵࡷࡤࡳࡡࡱ࠼ࠣࡈ࡮ࡩࡴࡪࡱࡱࡥࡷࡿࠠࡵࡱࠣࡷࡹࡵࡲࡦࠢࡨࡲࡻ࡯ࡲࡰࡰࡰࡩࡳࡺࠠࡷࡣࡵ࡭ࡦࡨ࡬ࡦࠢࡰࡥࡵࡶࡩ࡯ࡩࡶࠎࠥࠦࠠࠡࠢࠣࠤࠥࡱࡥࡺ࠼ࠣࡏࡪࡿࠠࡧࡴࡲࡱࠥࡉࡌࡊࡡࡆࡅࡕ࡙࡟ࡕࡑࡢࡇࡔࡔࡆࡊࡉࠍࠤࠥࠦࠠࠡࠢࠣࠤࡻࡧ࡬ࡶࡧ࠽ࠤ࡛ࡧ࡬ࡶࡧࠣࡪࡷࡵ࡭ࠡࡥࡲࡱࡲࡧ࡮ࡥࠢ࡯࡭ࡳ࡫ࠠࡢࡴࡪࡹࡲ࡫࡮ࡵࡵࠍࠤࠥࠦࠠࠣࠤࠥᷮ")
    if key in bstack11111l11l_opy_:
        bstack11lllll1l1_opy_ = bstack11111l11l_opy_[key]
        if isinstance(bstack11lllll1l1_opy_, list):
            for env_name in bstack11lllll1l1_opy_:
                bstack11l111lllll_opy_[env_name] = value
        else:
            bstack11l111lllll_opy_[bstack11lllll1l1_opy_] = value