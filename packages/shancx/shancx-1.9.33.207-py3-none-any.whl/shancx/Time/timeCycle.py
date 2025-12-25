
import glob
import os
import numpy as np
import traceback
from dateutil.relativedelta import relativedelta
# 获取指定路径下所有文件
paths = glob.glob("/root/data/ec_filter_npy_data/*")  

# 遍历每个文件路径
for p in paths:
    try:
        # 尝试加载.npy文件
        data = np.load(p)
    except Exception as e:
        # 如果读取失败，打印错误信息并删除文件
        print(f"Error loading {p}: {traceback.format_exc()}")
        os.remove(p)
        print(f"Deleted file: {p}")
def GetMulData(conf):
    sCST = conf[0]
    eCST = conf[0]
    sUTC = sCST+relativedelta(hours=-8)
    sCSTstr = sCST.strftime("%Y%m%d%H%M%S") 
    sUTCstr = sUTC.strftime("%Y%m%d%H%M%S") 
    path = f"/root/data/{sUTCstr[:4]}/{sUTCstr:8}/CR_{sUTCstr[:12]}00.npy"
    if os.path.exists(path):
        print(f"outpath {path} existsing ")

    else:
        print(f"outpath {path} not existsing ")
        return

from shancx import Mul_sub
import argparse
import datetime
import pandas as pd
def options():
    parser = argparse.ArgumentParser(description='examdatabasedata')
    parser.add_argument('--times', type=str, default='202411100000,202411101000') 
    config= parser.parse_args()
    print(config)
    config.times = config.times.split(",")
    if len(config.times) == 1:
        config.times = [config.times[0], config.times[0]]
    config.times = [datetime.datetime.strptime(config.times[0], "%Y%m%d%H%M"),
                    datetime.datetime.strptime(config.times[1], "%Y%m%d%H%M")]
    return config
if __name__ == '__main__':
    cfg = options()
    sCST = cfg.times[0]
    eCST = cfg.times[-1]
    timeList = pd.date_range(sCST, eCST, freq='6T')  #6T 分钟 
    print(timeList)
    Mul_sub(GetMulData,[timeList],31)

"""
for i in range(7):
    UTC = sUTC +relativedelta(hours=-8,minutes=-diffT*6)
"""

"""
import glob
import os
import numpy as np
from shancx import crDir
from shancx.NN import _loggers
logger = _loggers()
import netCDF4 as nc
import numpy as np
from shancx.Plot import plotRadar
from shancx import crDir  
import traceback
from dateutil.relativedelta import relativedelta
paths = glob.glob("/root/data/ec_filter_npy_data/*")  
basePath = f"/mnt/wtx_weather_forecast/scx/sever7/test/RADA/MQPF1109_1"
output_dirH9Npy = f"/mnt/wtx_weather_forecast/SAT/H9/sat_npy_CHN"
def GetMulData(conf):  
    sUTC = conf[0]
    sUTCstr = sUTC.strftime("%Y%m%d%H%M") 
    output_path =f"{output_dirH9Npy}/{sUTCstr[:4]}/{sUTCstr[:8]}/MSP3_PMSC_H9_GEO_FD_{sUTCstr[:12]}_00000-00000.npy"
    inputPathstr = f"{basePath}/{sUTCstr[:4]}/{sUTCstr[:8]}/*{sUTCstr[:12]}*.nc"
    inputPathL =  glob.glob(inputPathstr)
    if len(inputPathL) ==0 :  
        print(f"outpath {inputPathstr} is missing ")
        return None 
    inputPath = inputPathL[0]
    with nc.Dataset(inputPath) as dataNC:  
        CR = dataNC["CR"][:]
        lat = dataNC["lat"][:]
        lon = dataNC["lon"][:]        
    crDir(output_path)
    np.save(output_path,CR.data)
    logger.info(f"{output_path} done ") 

from shancx import Mul_sub    
import argparse
import datetime
import pandas as pd
def options():
    parser = argparse.ArgumentParser(description='examdatabasedata')
    parser.add_argument('--times', type=str, default='202507010000,202510010000') 
    config= parser.parse_args()
    print(config)
    config.times = config.times.split(",")
    if len(config.times) == 1:
        config.times = [config.times[0], config.times[0]]
    config.times = [datetime.datetime.strptime(config.times[0], "%Y%m%d%H%M"),
                    datetime.datetime.strptime(config.times[1], "%Y%m%d%H%M")]
    return config
if __name__ == '__main__':
    cfg = options()
    sUTC = cfg.times[0]
    eUTC = cfg.times[-1]
    timeList = pd.date_range(sUTC, eUTC, freq='3h')  #6T 分钟 
    print(timeList)
    Mul_sub(GetMulData,[timeList],6)
"""

"""
import glob
import os
import numpy as np
import traceback
from dateutil.relativedelta import relativedelta
import os 
from shancx.NN import Mul_TH
import argparse
import datetime
import pandas as pd
def GetMulData(conf):
    sUTC = conf[0]
    sUTCstr = sUTC.strftime("%Y%m%d%H%M") 
    commandstr = f""
    os.system(commandstr) 
def options():
    parser = argparse.ArgumentParser(description='examdatabasedata')
    parser.add_argument('--times', type=str, default='202508010000,202508010500') 
    config= parser.parse_args()
    print(config)
    config.times = config.times.split(",")
    if len(config.times) == 1:
        config.times = [config.times[0], config.times[0]]
    config.times = [datetime.datetime.strptime(config.times[0], "%Y%m%d%H%M"),
                    datetime.datetime.strptime(config.times[1], "%Y%m%d%H%M")]
    return config
if __name__ == '__main__':
    cfg = options()
    sUTC = cfg.times[0]
    eUTC = cfg.times[-1]
    timeList = pd.date_range(sUTC, eUTC, freq='10T')  #6T 分钟 
    print(timeList)
    Mul_TH(GetMulData,[timeList],3)
cd /mnt/wtx_weather_forecast/scx/sever7/SATdata/mkH9 ;timeout 1200s /home/scx/miniconda3/envs/H9/bin/python mkH9.py --time {sUTCstr[:12]}

"""

"""
from shancx import crDir
import os
from shancx import loggers as logger
# Define the original and new filenames
original_file = "CR_20241117050600.npy"
new_file = "20241117050600.npy"
rootpath ="/root/autodl-tmp"
filepath = "data/radar" 
def GetMulData(conf):
    sCST = conf[0]
    # eCST = conf[0]
    sCSTstr = sCST.strftime("%Y%m%d%H%M%S")   
    outpath = os.path.join(rootpath,filepath,f"CR_{sCSTstr}00.npy")
    if os.path.exists(outpath):
        logger.info(f"outpath {outpath} is existsing ")
        print(f"outpath {outpath} existsing ")    
    crDir(outpath)
    array = np.load(f"./{original_file}")
    np.save(outpath,array)
    logger.info(f"outpath {outpath} done ")
    print(f"outpath {outpath} done ")
from shancx import Mul_sub
import argparse
import datetime
import pandas as pd
import numpy as np
def options():
    parser = argparse.ArgumentParser(description='examdatabasedata')
    parser.add_argument('--times', type=str, default='202411101000,202411150000') 
    config= parser.parse_args()
    print(config)
    config.times = config.times.split(",")
    if len(config.times) == 1:
        config.times = [config.times[0], config.times[0]]
    config.times = [datetime.datetime.strptime(config.times[0], "%Y%m%d%H%M"),
                    datetime.datetime.strptime(config.times[1], "%Y%m%d%H%M")]
    return config
if __name__ == '__main__':
    cfg = options()
    sCST = cfg.times[0]
    eCST = cfg.times[-1]
    timeList = pd.date_range(sCST, eCST, freq='6T')  #6T 分钟 
    print(timeList)
    Mul_sub(GetMulData,[timeList],48)

------------------------------------

import glob
import os
import numpy as np
import traceback
from shancx import Mul_sub
from shancx import loggers as logger

# 获取指定路径下所有文件
paths = glob.glob("/root//autodl-tmp/data/radar/*")  #E:\

# 遍历每个文件路径
def getMul_sub(conf):
    p = conf[0]
    print(p)
    try:
        # 尝试加载.npy文件
        data = np.load(p)
        print(f"Loaded {p} with shape {data.shape}")
    except Exception as e:
        # 如果读取失败，打印错误信息并删除文件
        print(f"Error loading {p}: {traceback.format_exc()}")
        logger.error(f"Error loading {p}: {traceback.format_exc()}")
        os.remove(p)
        print(f"Deleted file: {p}")
 
if __name__ == '__main__':
    paths1 = [i for i in paths if '.npy' in i]
    Mul_sub(getMul_sub,[paths1],20)

np.tile(np.load(basedata), (8, 1, 1)).reshape((8, 4200, 6200))
"""


"""
制作特定数据

import glob
import os
import numpy as np
import traceback
from dateutil.relativedelta import relativedelta
# 获取指定路径下所有文件
import glob 
import datetime
from shancx import crDir
import netCDF4 as nc
# 遍历每个文件路径
def GetMulData(conf):
    sUTC = conf[0]
    UTCStr = sUTC.strftime("%Y%m%d%H%M%S") 
    path = f"/data2/mym/ifs_precipitation/{UTCStr[:4]}/{UTCStr[:8]}/ifs_precipitation_{UTCStr[:12]}.nc" 
    if not  os.path.exists(path):
        print(f"outpath {path} existsing ")
    else:
        with nc.Dataset(path) as dataNC:
            # 获取 'time' 变量
            latitude = dataNC.variables[list(dataNC.variables)[0]][:] 
            longitude = dataNC.variables[list(dataNC.variables)[2]][:]  
            ifs_precipitation = dataNC.variables[list(dataNC.variables)[1]][:]  
            # print(list(dataNC.variables))
    # crDir(path)
    # np.save(path,d)
    return {"min":np.min(d),"max":np.max(d)}
from shancx import Mul_sub
import argparse
import datetime
import pandas as pd
def options():
    parser = argparse.ArgumentParser(description='examdatabasedata')
    parser.add_argument('--times', type=str, default='202411100000,202411101000') 
    config= parser.parse_args()
    print(config)
    config.times = config.times.split(",")
    if len(config.times) == 1:
        config.times = [config.times[0], config.times[0]]
    config.times = [datetime.datetime.strptime(config.times[0], "%Y%m%d%H%M"),
                    datetime.datetime.strptime(config.times[1], "%Y%m%d%H%M")]
    return config
if __name__ == '__main__':
 
    cfg = options()
    sUTC = cfg.times[0]
    eUTC = cfg.times[-1]
    sUTC = datetime.datetime(2002,6,1,0,0) 
    eUTC = datetime.datetime(2004,9,1,0,0) 
    timeList = pd.date_range(sUTC, eUTC, freq='3h')  #6T 分钟 

    summer_timeList = timeList[timeList.month.isin([6, 7, 8])]
    print(timeList)
    minmax = Mul_sub(GetMulData,[summer_timeList],10)
    global_min = min(d['min'] for d in minmax)
    global_max = max(d['max'] for d in minmax)  #117
    print() 

"""

 