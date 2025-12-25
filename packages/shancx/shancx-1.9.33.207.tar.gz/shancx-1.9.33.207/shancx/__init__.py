#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time : 2024/10/17 上午午10:40
# @Author : shancx
# @File : __init__.py
# @email : shanhe12@163.com

import os
def start():
    print("import successful")
# constants
import subprocess

__author__ = 'shancx'
 
__author_email__ = 'shanhe12@163.com'

# @Time : 2023/09/27 下午8:52
# @Author : shanchangxi
# @File : util_log.py
import time
import logging  
from logging import handlers
import inspect

import time
import logging  
from logging import handlers 
loggers = logging.getLogger()
loggers.setLevel(logging.INFO) 
formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
print_handler = logging.StreamHandler()   
print_handler.setFormatter(formatter)   
loggers.addHandler(print_handler)

from pathlib import Path as PathlibPath
def crDir(path):
    path_obj = PathlibPath(path)
    directory = path_obj.parent if path_obj.suffix else path_obj
    directory.mkdir(parents=True, exist_ok=True) 

def Tim_(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        loggers.info(f"{func.__name__} took {end_time - start_time:.4f} seconds")
        return result
    return wrapper
    
def TimPlus(func):
    def wrapper(*args, **kwargs):
        func_file = inspect.getfile(func)
        func_line = inspect.getsourcelines(func)[1]
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        log_message = (
            f"{func.__name__} line {func_line} (Defined at {func_file} ) "
            f"took {elapsed_time:.4f} seconds"
        )
        loggers.info(log_message)
        return result
    return wrapper

def validate_param_list(param_list):
    if len(param_list) == 0:
        raise ValueError("param_list cannot be empty.")    
    for sublist in param_list:
        if len(sublist) == 0:
            raise ValueError("Sub-lists in param_list cannot be empty.")        

from itertools import product
from concurrent.futures import ProcessPoolExecutor as PoolExecutor, as_completed 
import sys
from tqdm import tqdm 
def Mul_sub(task, param_list, num=6):
    print(f"Pro num {num}")
    validate_param_list(param_list)
    if len(param_list) == 1:
        product_list = [(x,) for x in param_list[0]]
    else:
        product_list = list(product(*param_list))
    results = []
    with PoolExecutor(max_workers=num) as executor:
        try:           
            futures = [executor.submit(task, item) for item in product_list]
            for future in tqdm(as_completed(futures), total=len(futures), desc="Processing tasks", unit="task"):   
                results.append(future.result())  
        except KeyboardInterrupt:
            sys.exit(1)    
    return results
 
def Mul_sub_S(task, param_list, num=6):
    print(f"Pro num {num}")
    validate_param_list(param_list)
    if len(param_list) == 1:
        product_list = [(x,) for x in param_list[0]]
    else:
        product_list = list(product(*param_list))
    results = [None] * len(product_list)
    with PoolExecutor(max_workers=num) as executor:
        futures = {executor.submit(task, item): idx for idx, item in enumerate(product_list)}        
        try:
            for future in tqdm(as_completed(futures), total=len(futures), desc="Processing", unit="task"):
                idx = futures[future]
                results[idx] = future.result()
        except KeyboardInterrupt:
            sys.exit(1)       
    return results

from concurrent.futures import ProcessPoolExecutor as PoolExecutor, as_completed
import sys
from tqdm import tqdm
def Mul_subplus(task, param_lists, num=6): 
    results = []
    with PoolExecutor(max_workers=num) as executor:
        try:
            futures = [
                executor.submit(task, args)
                for args in zip(*param_lists)
            ]
            for future in tqdm(as_completed(futures), total=len(futures), desc="Processing tasks", unit="task"):
                results.append(future.result())
        except KeyboardInterrupt:
            sys.exit(1)
    return results

from concurrent.futures import ProcessPoolExecutor as PoolExecutor, as_completed
import sys
from tqdm import tqdm
def Mul_sub_Splus(task, param_lists, num=6): 
    if not all(len(lst) == len(param_lists[0]) for lst in param_lists):
        raise ValueError("All parameter lists must have the same length.")    
    results = [None] * len(param_lists[0])   
    with PoolExecutor(max_workers=num) as executor:
        try:
            futures = {
                executor.submit(task, *args): idx
                for idx, args in enumerate(zip(*param_lists))
            }
            for future in tqdm(as_completed(futures), total=len(futures), desc="Processing tasks", unit="task"):
                idx = futures[future]  
                results[idx] = future.result()   
        except KeyboardInterrupt:
            sys.exit(1)    
    return results

from concurrent.futures import ThreadPoolExecutor
from itertools import product
def Mul_TH(task, param_list, max_workers=6):
    print(f"Thread num: {max_workers}")
    validate_param_list(param_list)
    task_args = [
        (arg,) if len(param_list) == 1 else arg
        for arg in (
            param_list[0] if len(param_list) == 1 
            else product(*param_list)
        )
    ]    
    with ThreadPoolExecutor(max_workers) as ex:
        try:
            return list(ex.map(task, task_args))
        except KeyboardInterrupt:
            print("\n用户中断操作")
            ex.shutdown(wait=False)
            sys.exit(1) 

from tqdm import tqdm  
def _tqdm(train_loader,desc="Training Progress",epoch=None):
    epoch = epoch +1 if epoch is not None else None
    descdict = {"val":"Val Progress", "train":"Training Progress"}
    return tqdm(train_loader, desc=f"Epoch {epoch} {descdict.get(desc,'DESC')}", ncols=100)

import os
import datetime
from pathlib import Path
def lock_file(lock_file_path):
    if os.path.exists(lock_file_path):
        print(f" {lock_file_path} is existded ")
        return False
    try:
        os.makedirs(os.path.dirname(lock_file_path), exist_ok=True)
        with open(lock_file_path, 'w') as f:
            f.write(f"process_id:{os.getpid()},create_time:{datetime.datetime.now()}")
            return True 
    except Exception as e:
        print(f"创建锁文件失败 create lock failed : {e}")
        return False
"""
lock_file = f"{output_base_path}{sat_code}/lock_files/MSP2_WTX_AIW_QPF_L88_GLOB_{utc_time_str}.lock"    
if os.path.exists(outpath):
    print(f" 目标文件已存在，跳过处理: {outpath}")
    return True    
if os.path.exists(lock_file):
    print(f"锁文件存在，已有程序在处理时次 {utc_time_str}，跳过")
    return False 
"""
import os
import time
def is_process_alive(pid):
    try:
        os.kill(pid, 0)  
        return True
    except OSError:
        return False
def check_lock(lock_file):
    if not os.path.exists(lock_file):
        return False    
    try:
        with open(lock_file, 'r') as f:
            content = f.read().strip()        
        if 'process_id:' in content and 'create_time:' in content:
            pid_str = content.split('process_id:')[1].split(',')[0]
            pid = int(pid_str)            
            if not is_process_alive(pid):
                print(f"进程 {pid} 已消亡，清理锁文件")
                os.remove(lock_file)
                return False 
            else:
                print(f"进程 {pid} 仍在运行，跳过执行")
                return True                
    except Exception as e:
        print(f"锁文件解析错误，清理: {e}")
        os.remove(lock_file)
        return False    
    return False
"""
if  check_lock(lock_file):
    return False
"""
import multiprocessing
def set_multiprocessing(method="spawn", verbose=True):  # 补充缺失的verbose参数定义
    try:
        multiprocessing.set_start_method(method, force=True)
        if verbose:
            print(f"The startup method is: '{method}'")
        return method
    except RuntimeError as e:   
        if verbose:  
            print(f"Setup failed: {e}")
        return multiprocessing.get_start_method()
    
"""
current_method = set_multiprocessing_method()
# 输出：已设置多进程启动方式: 'spawn'
print("当前启动方式：", current_method)  # 输出：当前启动方式：spawn
"""
"""
if __name__ == '__main__':
    set_multiprocessing_method('auto')
    print("当前启动方法:", multiprocessing.get_start_method())

"""
        
"""
zoom插值
from scipy.ndimage import zoom
d = zoom(d_clip, [4201/169,6201/249], order=1)[:-1, :-1]
"""
"""
torch.cuda.empty_cache()
del 
gc.collect()
"""

'''
from multiprocessing import Pool
'''
'''
 ##定義一個streamHandler
# print_handler = logging.StreamHandler()  
# print_handler.setFormatter(formatter) 
# loggers.addHandler(print_handler)
'''
'''
# @Time : 2023/09/27 下午8:52
# @Author : shanchangxi
# @File : util_log.py
import time
import logging  
from logging import handlers
 
logger = logging.getLogger()
logger.setLevel(logging.INFO) 
log_name =  'project_tim_tor.log'
logfile = log_name
time_rotating_file_handler = handlers.TimedRotatingFileHandler(filename=logfile, when='D', encoding='utf-8')
time_rotating_file_handler.setLevel(logging.INFO)   
formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
time_rotating_file_handler.setFormatter(formatter)
logger.addHandler(time_rotating_file_handler)
print_handler = logging.StreamHandler()   
print_handler.setFormatter(formatter)   
logger.addHandler(print_handler)
'''
'''
###解决方法  pip install torch==2.4.0  torchvision    torchaudio三个同时安装  python 3.12  解决cuda启动不了的问题
Res网络
'''

"""
find /mnt/wtx_weather_forecast/scx/SpiderGLOBPNGSource -type f -name "*.png" -mtime +3 -exec rm {} \;
-mtime 选项后面的数值代表天数。
+n 表示“超过 n 天”，即查找最后修改时间在 n 天之前的文件。
"""
"""
from shancx.SN import UserManager,sendMESplus
from shancx._info import users 
M = UserManager(info=users)
user_info = M.get_user("003") 
sendMESplus("测试数据",base=user_info)
"""
"""
https://api.map.baidu.com/lbsapi/getpoint/index.html  坐标
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple   pip.conf
python setup.py sdist bdist_wheel
twine upload dist/*
"""
"""   与循环搭配使用   
    for key,value in dictflag.items():
        try:
            pac = all_df1[all_df1['PAC'].str.startswith(f'{key}')]
            acctoal,acctoalEC,matEC,mat,rate_Lift_ratiotsEC,outpath= metriacfunall(pac)
            if not len(matEC.shape) == (2,2):
               continue             
            docdataset =  mkdataset2TS(acctoal,acctoalEC,matEC,mat, rate_Lift_ratiotsEC,outpath)
    
        except Exception as e:
            print(traceback.format_exc())  
            continue
"""