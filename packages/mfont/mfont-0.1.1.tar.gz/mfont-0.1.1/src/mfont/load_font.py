from pathlib import Path

import matplotlib
from matplotlib import font_manager


FONT_DIR = Path(__file__).parent / "fonts" 

def _auto_configure(debug: bool=False):
    # font_dir_path = get_font_ttf_path()
    font_files = font_manager.findSystemFonts(fontpaths=str(FONT_DIR))
    # FONT_NAME = "LXGW WenKai GB Lite"
    FONT_NAME = "RomanSong"
    
    if debug:
        # 开发模式，打印字体名
        for fpath in font_files:
            fp = font_manager.FontProperties(fname=fpath)
            print(fp.get_name())
            font_manager.fontManager.addfont(fpath)
            FONT_NAME = fp.get_name()
    else:
        # 正式模式，只加载指定字体
        for fpath in font_files:
            font_manager.fontManager.addfont(fpath)

    
    matplotlib.rc('font', family=FONT_NAME)
    matplotlib.rc('axes', unicode_minus=False)
    
def switch(fpath: str|Path):
    fp = font_manager.FontProperties(fname=fpath)
    font_manager.fontManager.addfont(path=fpath)

    matplotlib.rc('font', family=fp.get_name())

def reset_font():
    _auto_configure()

def load_lxg():
    FONT_NAME = "LXGW WenKai GB Lite"
    matplotlib.rc('font', family=FONT_NAME)    

def load_heiti():
    FONT_NAME = "FZHei-B01S"
    matplotlib.rc('font', family=FONT_NAME)

_auto_configure()

