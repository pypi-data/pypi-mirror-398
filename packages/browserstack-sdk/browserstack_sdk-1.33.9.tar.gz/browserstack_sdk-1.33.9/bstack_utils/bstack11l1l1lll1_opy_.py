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
import sys
import logging
import tarfile
import io
import os
import time
import requests
import re
from requests_toolbelt.multipart.encoder import MultipartEncoder
from bstack_utils.constants import bstack11l1l1l1lll_opy_, bstack11l1l111111_opy_, bstack11l1l1l1ll1_opy_
import tempfile
import json
bstack111l111llll_opy_ = os.getenv(bstack1ll_opy_ (u"ࠨࡂࡓࡑ࡚ࡗࡊࡘࡓࡕࡃࡆࡏࡤࡒࡏࡈࡡࡉࡍࡑࡋࠢḚ"), None) or os.path.join(tempfile.gettempdir(), bstack1ll_opy_ (u"ࠢࡣࡴࡲࡻࡸ࡫ࡲࡴࡶࡤࡧࡰ࠴ࡤࡦࡤࡸ࡫࠳ࡲ࡯ࡨࠤḛ"))
bstack111l11ll1ll_opy_ = os.path.join(bstack1ll_opy_ (u"ࠣ࡮ࡲ࡫ࠧḜ"), bstack1ll_opy_ (u"ࠩࡶࡨࡰ࠳ࡣ࡭࡫࠰ࡨࡪࡨࡵࡨ࠰࡯ࡳ࡬࠭ḝ"))
logging.Formatter.converter = time.gmtime
def get_logger(name=__name__, level=None):
  logger = logging.getLogger(name)
  if level:
    logging.basicConfig(
      level=level,
      format=bstack1ll_opy_ (u"ࠪࠩ࠭ࡧࡳࡤࡶ࡬ࡱࡪ࠯ࡳࠡ࡝ࠨࠬࡳࡧ࡭ࡦࠫࡶࡡࡠࠫࠨ࡭ࡧࡹࡩࡱࡴࡡ࡮ࡧࠬࡷࡢࠦ࠭ࠡࠧࠫࡱࡪࡹࡳࡢࡩࡨ࠭ࡸ࠭Ḟ"),
      datefmt=bstack1ll_opy_ (u"ࠫࠪ࡟࠭ࠦ࡯࠰ࠩࡩ࡚ࠥࡉ࠼ࠨࡑ࠿ࠫࡓ࡛ࠩḟ"),
      stream=sys.stdout
    )
  return logger
def bstack1ll1l11l11l_opy_():
  bstack111l11l11ll_opy_ = os.environ.get(bstack1ll_opy_ (u"ࠧࡈࡒࡐ࡙ࡖࡉࡗ࡙ࡔࡂࡅࡎࡣࡇࡏࡎࡂࡔ࡜ࡣࡉࡋࡂࡖࡉࠥḠ"), bstack1ll_opy_ (u"ࠨࡦࡢ࡮ࡶࡩࠧḡ"))
  return logging.DEBUG if bstack111l11l11ll_opy_.lower() == bstack1ll_opy_ (u"ࠢࡵࡴࡸࡩࠧḢ") else logging.INFO
def bstack1l1l1ll1111_opy_():
  global bstack111l111llll_opy_
  if os.path.exists(bstack111l111llll_opy_):
    os.remove(bstack111l111llll_opy_)
  if os.path.exists(bstack111l11ll1ll_opy_):
    os.remove(bstack111l11ll1ll_opy_)
def bstack1l11l1l1ll_opy_():
  for handler in logging.getLogger().handlers:
    logging.getLogger().removeHandler(handler)
def configure_logger(config, log_level):
  bstack111l111l11l_opy_ = log_level
  if bstack1ll_opy_ (u"ࠨ࡮ࡲ࡫ࡑ࡫ࡶࡦ࡮ࠪḣ") in config and config[bstack1ll_opy_ (u"ࠩ࡯ࡳ࡬ࡒࡥࡷࡧ࡯ࠫḤ")] in bstack11l1l111111_opy_:
    bstack111l111l11l_opy_ = bstack11l1l111111_opy_[config[bstack1ll_opy_ (u"ࠪࡰࡴ࡭ࡌࡦࡸࡨࡰࠬḥ")]]
  if config.get(bstack1ll_opy_ (u"ࠫࡩ࡯ࡳࡢࡤ࡯ࡩࡆࡻࡴࡰࡅࡤࡴࡹࡻࡲࡦࡎࡲ࡫ࡸ࠭Ḧ"), False):
    logging.getLogger().setLevel(bstack111l111l11l_opy_)
    return bstack111l111l11l_opy_
  global bstack111l111llll_opy_
  bstack1l11l1l1ll_opy_()
  bstack111l11l1ll1_opy_ = logging.Formatter(
    fmt=bstack1ll_opy_ (u"ࠬࠫࠨࡢࡵࡦࡸ࡮ࡳࡥࠪࡵࠣ࡟ࠪ࠮࡮ࡢ࡯ࡨ࠭ࡸࡣ࡛ࠦࠪ࡯ࡩࡻ࡫࡬࡯ࡣࡰࡩ࠮ࡹ࡝ࠡ࠯ࠣࠩ࠭ࡳࡥࡴࡵࡤ࡫ࡪ࠯ࡳࠨḧ"),
    datefmt=bstack1ll_opy_ (u"࡚࠭ࠥ࠯ࠨࡱ࠲ࠫࡤࡕࠧࡋ࠾ࠪࡓ࠺ࠦࡕ࡝ࠫḨ"),
  )
  bstack111l11l1lll_opy_ = logging.StreamHandler(sys.stdout)
  file_handler = logging.FileHandler(bstack111l111llll_opy_)
  file_handler.setFormatter(bstack111l11l1ll1_opy_)
  bstack111l11l1lll_opy_.setFormatter(bstack111l11l1ll1_opy_)
  file_handler.setLevel(logging.DEBUG)
  bstack111l11l1lll_opy_.setLevel(log_level)
  file_handler.addFilter(lambda r: r.name != bstack1ll_opy_ (u"ࠧࡴࡧ࡯ࡩࡳ࡯ࡵ࡮࠰ࡺࡩࡧࡪࡲࡪࡸࡨࡶ࠳ࡸࡥ࡮ࡱࡷࡩ࠳ࡸࡥ࡮ࡱࡷࡩࡤࡩ࡯࡯ࡰࡨࡧࡹ࡯࡯࡯ࠩḩ"))
  logging.getLogger().setLevel(logging.DEBUG)
  bstack111l11l1lll_opy_.setLevel(bstack111l111l11l_opy_)
  logging.getLogger().addHandler(bstack111l11l1lll_opy_)
  logging.getLogger().addHandler(file_handler)
  return bstack111l111l11l_opy_
def bstack111l111lll1_opy_(config):
  try:
    bstack111l11llll1_opy_ = set(bstack11l1l1l1ll1_opy_)
    bstack111l11ll1l1_opy_ = bstack1ll_opy_ (u"ࠨࠩḪ")
    with open(bstack1ll_opy_ (u"ࠩࡥࡶࡴࡽࡳࡦࡴࡶࡸࡦࡩ࡫࠯ࡻࡰࡰࠬḫ")) as bstack111l11l111l_opy_:
      bstack111l111l1ll_opy_ = bstack111l11l111l_opy_.read()
      bstack111l11ll1l1_opy_ = re.sub(bstack1ll_opy_ (u"ࡵࠫࡣ࠮࡜ࡴ࠭ࠬࡃࠨ࠴ࠪࠥ࡞ࡱࠫḬ"), bstack1ll_opy_ (u"ࠫࠬḭ"), bstack111l111l1ll_opy_, flags=re.M)
      bstack111l11ll1l1_opy_ = re.sub(
        bstack1ll_opy_ (u"ࡷ࠭࡞ࠩ࡞ࡶ࠯࠮ࡅࠨࠨḮ") + bstack1ll_opy_ (u"࠭ࡼࠨḯ").join(bstack111l11llll1_opy_) + bstack1ll_opy_ (u"ࠧࠪ࠰࠭ࠨࠬḰ"),
        bstack1ll_opy_ (u"ࡳࠩ࡟࠶࠿࡛ࠦࡓࡇࡇࡅࡈ࡚ࡅࡅ࡟ࠪḱ"),
        bstack111l11ll1l1_opy_, flags=re.M | re.I
      )
    def bstack111l11l11l1_opy_(dic):
      bstack111l11lll11_opy_ = {}
      for key, value in dic.items():
        if key in bstack111l11llll1_opy_:
          bstack111l11lll11_opy_[key] = bstack1ll_opy_ (u"ࠩ࡞ࡖࡊࡊࡁࡄࡖࡈࡈࡢ࠭Ḳ")
        else:
          if isinstance(value, dict):
            bstack111l11lll11_opy_[key] = bstack111l11l11l1_opy_(value)
          else:
            bstack111l11lll11_opy_[key] = value
      return bstack111l11lll11_opy_
    bstack111l11lll11_opy_ = bstack111l11l11l1_opy_(config)
    return {
      bstack1ll_opy_ (u"ࠪࡦࡷࡵࡷࡴࡧࡵࡷࡹࡧࡣ࡬࠰ࡼࡱࡱ࠭ḳ"): bstack111l11ll1l1_opy_,
      bstack1ll_opy_ (u"ࠫ࡫࡯࡮ࡢ࡮ࡦࡳࡳ࡬ࡩࡨ࠰࡭ࡷࡴࡴࠧḴ"): json.dumps(bstack111l11lll11_opy_)
    }
  except Exception as e:
    return {}
def bstack111l111l1l1_opy_(inipath, rootpath):
  log_dir = os.path.join(os.getcwd(), bstack1ll_opy_ (u"ࠬࡲ࡯ࡨࠩḵ"))
  if not os.path.exists(log_dir):
    os.makedirs(log_dir)
  bstack111l11ll111_opy_ = os.path.join(log_dir, bstack1ll_opy_ (u"࠭ࡰࡺࡶࡨࡷࡹࡥࡣࡰࡰࡩ࡭࡬ࡹࠧḶ"))
  if not os.path.exists(bstack111l11ll111_opy_):
    bstack111l11l1111_opy_ = {
      bstack1ll_opy_ (u"ࠢࡪࡰ࡬ࡴࡦࡺࡨࠣḷ"): str(inipath),
      bstack1ll_opy_ (u"ࠣࡴࡲࡳࡹࡶࡡࡵࡪࠥḸ"): str(rootpath)
    }
    with open(os.path.join(log_dir, bstack1ll_opy_ (u"ࠩࡳࡽࡹ࡫ࡳࡵࡡࡦࡳࡳ࡬ࡩࡨࡵ࠱࡮ࡸࡵ࡮ࠨḹ")), bstack1ll_opy_ (u"ࠪࡻࠬḺ")) as bstack111l11l1l1l_opy_:
      bstack111l11l1l1l_opy_.write(json.dumps(bstack111l11l1111_opy_))
def bstack111l111l111_opy_():
  try:
    bstack111l11ll111_opy_ = os.path.join(os.getcwd(), bstack1ll_opy_ (u"ࠫࡱࡵࡧࠨḻ"), bstack1ll_opy_ (u"ࠬࡶࡹࡵࡧࡶࡸࡤࡩ࡯࡯ࡨ࡬࡫ࡸ࠴ࡪࡴࡱࡱࠫḼ"))
    if os.path.exists(bstack111l11ll111_opy_):
      with open(bstack111l11ll111_opy_, bstack1ll_opy_ (u"࠭ࡲࠨḽ")) as bstack111l11l1l1l_opy_:
        bstack111l111ll11_opy_ = json.load(bstack111l11l1l1l_opy_)
      return bstack111l111ll11_opy_.get(bstack1ll_opy_ (u"ࠧࡪࡰ࡬ࡴࡦࡺࡨࠨḾ"), bstack1ll_opy_ (u"ࠨࠩḿ")), bstack111l111ll11_opy_.get(bstack1ll_opy_ (u"ࠩࡵࡳࡴࡺࡰࡢࡶ࡫ࠫṀ"), bstack1ll_opy_ (u"ࠪࠫṁ"))
  except:
    pass
  return None, None
def bstack111l11l1l11_opy_():
  try:
    bstack111l11ll111_opy_ = os.path.join(os.getcwd(), bstack1ll_opy_ (u"ࠫࡱࡵࡧࠨṂ"), bstack1ll_opy_ (u"ࠬࡶࡹࡵࡧࡶࡸࡤࡩ࡯࡯ࡨ࡬࡫ࡸ࠴ࡪࡴࡱࡱࠫṃ"))
    if os.path.exists(bstack111l11ll111_opy_):
      os.remove(bstack111l11ll111_opy_)
  except:
    pass
def bstack11ll1111l_opy_(config):
  try:
    from bstack_utils.helper import bstack1ll1l1l111_opy_, bstack11l1111l1_opy_
    from browserstack_sdk.sdk_cli.cli import cli
    global bstack111l111llll_opy_
    if config.get(bstack1ll_opy_ (u"࠭ࡤࡪࡵࡤࡦࡱ࡫ࡁࡶࡶࡲࡇࡦࡶࡴࡶࡴࡨࡐࡴ࡭ࡳࠨṄ"), False):
      return
    uuid = os.getenv(bstack1ll_opy_ (u"ࠧࡃࡔࡒ࡛ࡘࡋࡒࡔࡖࡄࡇࡐࡥࡔࡆࡕࡗࡌ࡚ࡈ࡟ࡖࡗࡌࡈࠬṅ")) if os.getenv(bstack1ll_opy_ (u"ࠨࡄࡕࡓ࡜࡙ࡅࡓࡕࡗࡅࡈࡑ࡟ࡕࡇࡖࡘࡍ࡛ࡂࡠࡗࡘࡍࡉ࠭Ṇ")) else bstack1ll1l1l111_opy_.get_property(bstack1ll_opy_ (u"ࠤࡶࡨࡰࡘࡵ࡯ࡋࡧࠦṇ"))
    if not uuid or uuid == bstack1ll_opy_ (u"ࠪࡲࡺࡲ࡬ࠨṈ"):
      return
    bstack111l11ll11l_opy_ = [bstack1ll_opy_ (u"ࠫࡷ࡫ࡱࡶ࡫ࡵࡩࡲ࡫࡮ࡵࡵ࠱ࡸࡽࡺࠧṉ"), bstack1ll_opy_ (u"ࠬࡖࡩࡱࡨ࡬ࡰࡪ࠭Ṋ"), bstack1ll_opy_ (u"࠭ࡰࡺࡲࡵࡳ࡯࡫ࡣࡵ࠰ࡷࡳࡲࡲࠧṋ"), bstack111l111llll_opy_, bstack111l11ll1ll_opy_]
    bstack111l11lll1l_opy_, root_path = bstack111l111l111_opy_()
    if bstack111l11lll1l_opy_ != None:
      bstack111l11ll11l_opy_.append(bstack111l11lll1l_opy_)
    if root_path != None:
      bstack111l11ll11l_opy_.append(os.path.join(root_path, bstack1ll_opy_ (u"ࠧࡤࡱࡱࡪࡹ࡫ࡳࡵ࠰ࡳࡽࠬṌ")))
    bstack1l11l1l1ll_opy_()
    logging.shutdown()
    output_file = os.path.join(tempfile.gettempdir(), bstack1ll_opy_ (u"ࠨࡤࡶࡸࡦࡩ࡫࠮࡮ࡲ࡫ࡸ࠳ࠧṍ") + uuid + bstack1ll_opy_ (u"ࠩ࠱ࡸࡦࡸ࠮ࡨࡼࠪṎ"))
    with tarfile.open(output_file, bstack1ll_opy_ (u"ࠥࡻ࠿࡭ࡺࠣṏ")) as archive:
      for file in filter(lambda f: os.path.exists(f), bstack111l11ll11l_opy_):
        try:
          archive.add(file,  arcname=os.path.basename(file))
        except:
          pass
      for name, data in bstack111l111lll1_opy_(config).items():
        tarinfo = tarfile.TarInfo(name)
        bstack111l1111lll_opy_ = data.encode()
        tarinfo.size = len(bstack111l1111lll_opy_)
        archive.addfile(tarinfo, io.BytesIO(bstack111l1111lll_opy_))
    bstack1l1ll1l1l_opy_ = MultipartEncoder(
      fields= {
        bstack1ll_opy_ (u"ࠫࡩࡧࡴࡢࠩṐ"): (os.path.basename(output_file), open(os.path.abspath(output_file), bstack1ll_opy_ (u"ࠬࡸࡢࠨṑ")), bstack1ll_opy_ (u"࠭ࡡࡱࡲ࡯࡭ࡨࡧࡴࡪࡱࡱ࠳ࡽ࠳ࡧࡻ࡫ࡳࠫṒ")),
        bstack1ll_opy_ (u"ࠧࡤ࡮࡬ࡩࡳࡺࡂࡶ࡫࡯ࡨ࡚ࡻࡩࡥࠩṓ"): uuid
      }
    )
    bstack111l111ll1l_opy_ = bstack11l1111l1_opy_(cli.config, [bstack1ll_opy_ (u"ࠣࡣࡳ࡭ࡸࠨṔ"), bstack1ll_opy_ (u"ࠤࡲࡦࡸ࡫ࡲࡷࡣࡥ࡭ࡱ࡯ࡴࡺࠤṕ"), bstack1ll_opy_ (u"ࠥࡹࡵࡲ࡯ࡢࡦࠥṖ")], bstack11l1l1l1lll_opy_)
    response = requests.post(
      bstack1ll_opy_ (u"ࠦࢀࢃ࠯ࡤ࡮࡬ࡩࡳࡺ࠭࡭ࡱࡪࡷ࠴ࡻࡰ࡭ࡱࡤࡨࠧṗ").format(bstack111l111ll1l_opy_),
      data=bstack1l1ll1l1l_opy_,
      headers={bstack1ll_opy_ (u"ࠬࡉ࡯࡯ࡶࡨࡲࡹ࠳ࡔࡺࡲࡨࠫṘ"): bstack1l1ll1l1l_opy_.content_type},
      auth=(config[bstack1ll_opy_ (u"࠭ࡵࡴࡧࡵࡒࡦࡳࡥࠨṙ")], config[bstack1ll_opy_ (u"ࠧࡢࡥࡦࡩࡸࡹࡋࡦࡻࠪṚ")])
    )
    os.remove(output_file)
    if response.status_code != 200:
      get_logger().debug(bstack1ll_opy_ (u"ࠨࡇࡵࡶࡴࡸࠠࡶࡲ࡯ࡳࡦࡪࠠ࡭ࡱࡪࡷ࠿ࠦࠧṛ") + response.status_code)
  except Exception as e:
    get_logger().debug(bstack1ll_opy_ (u"ࠩࡈࡼࡨ࡫ࡰࡵ࡫ࡲࡲࠥ࡯࡮ࠡࡵࡨࡲࡩ࡯࡮ࡨࠢ࡯ࡳ࡬ࡹ࠺ࠨṜ") + str(e))
  finally:
    try:
      bstack1l1l1ll1111_opy_()
      bstack111l11l1l11_opy_()
    except:
      pass