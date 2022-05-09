from e3dc import E3DC
from e3dc_direct import E3dcDirect
import os
import sys

this_path = os.path.dirname(__file__)
config_path = os.path.abspath(os.path.join(this_path, '../../e3dc_config'))
sys.path.append(config_path)

from e3dc_config import E3DC_Config


def create_e3dc():
    return E3dcDirect(E3DC(E3DC.CONNECT_LOCAL,
                           username=E3DC_Config.USERNAME,
                           password=E3DC_Config.PASSWORD,
                           ipAddress=E3DC_Config.IP,
                           key=E3DC_Config.SECRET))
