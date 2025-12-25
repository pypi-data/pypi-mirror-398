import pygrib
import numpy as np
import pandas as pd
import yaml
def _load_config(config_path: str) :
    """加载YAML配置文件"""
    print(f"load config file Get configuration parameters: {config_path}")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config

import configparser
import traceback
def parse_config(path,section,option):
    cp = configparser.ConfigParser()
    try:
        cp.read(path)
        res = cp.get(section,option)
    except Exception as e:
        print(traceback.format_exc())
        exit()
    return res
"""
Path = "./application.conf"
radar_path = parse_config(Path, "JY", "radar_path")  #JY是选择部分,radar_path配置路径
"""