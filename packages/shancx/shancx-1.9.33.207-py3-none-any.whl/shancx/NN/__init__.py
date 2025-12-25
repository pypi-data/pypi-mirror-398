#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
def start():
    print("import successful")
# constants
__author__ = 'shancx' 
__author_email__ = 'shanhe12@163.com'
__time__ = '20251028 21:16'
import logging
from logging.handlers import RotatingFileHandler
import os
from shancx import crDir 
def _loggers(logger_name="loggers", root="./logs", phase="project", level=logging.INFO, screen=True, max_bytes=10*1024*1024, backup_count=5, overwrite=False,handlersflag=False):
    '''set up logger with rotating file handler'''
    l = logging.getLogger(logger_name)
    if handlersflag:
        if l.handlers:
            return l
    formatter = logging.Formatter(
        "%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s", datefmt='%Y-%m-%d %H:%M:%S') 
    log_file = os.path.join(root, '{}.log'.format(phase))
    crDir(log_file)
    # Use RotatingFileHandler with 'w' mode to overwrite log file if needed
    mode = 'w' if overwrite else 'a'
    fh = RotatingFileHandler(log_file, mode=mode, maxBytes=max_bytes, backupCount=backup_count)
    fh.setFormatter(formatter)    
    l.setLevel(level)
    l.addHandler(fh)    
    if screen:
        sh = logging.StreamHandler()
        sh.setFormatter(formatter)
        l.addHandler(sh)    
    return l

"""
logger = _loggers(logger_name="test_logger", root=curpathplus, phase="test_log", overwrite=True, screen=True)
# 测试日志输出
for i in range(5):
    logger.info(f"这是日志消息 {i+1}")
    time.sleep(1)
"""


import logging
from logging.handlers import RotatingFileHandler
import os
from shancx import crDir 
import multiprocessing
def _loggersPlus(logger_name="loggers", root="./logs", phase="project", level=logging.INFO, 
             screen=True, max_bytes=10 * 1024 * 1024, backup_count=5, overwrite=False, 
             handlersflag=False, enable_rotating=None):
    l = logging.getLogger(logger_name)
    if handlersflag:
        if l.handlers:
            return l    
    formatter = logging.Formatter(
        "%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s", 
        datefmt='%Y-%m-%d %H:%M:%S'
    )    
    log_file = os.path.join(root, '{}.log'.format(phase))
    crDir(log_file)
    mode = 'w' if overwrite else 'a'    
    if enable_rotating is None:
        enable_rotating = (multiprocessing.current_process().name == 'MainProcess')
    
    if enable_rotating:
        fh = RotatingFileHandler(
            log_file, 
            mode=mode, 
            maxBytes=max_bytes, 
            backupCount=backup_count
        )
    else:
        fh = logging.FileHandler(log_file, mode=mode)
    
    fh.setFormatter(formatter)    
    l.setLevel(level)
    l.addHandler(fh)    
    
    if screen:
        sh = logging.StreamHandler()
        sh.setFormatter(formatter)
        l.addHandler(sh)  
    return l


import logging
def setlogger(level=logging.INFO):
 
    logging.basicConfig(
        level=level,  # 动态接受级别参数
        format="%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s",
        handlers=[logging.StreamHandler()],
        force=True  # 强制覆盖现有配置（Python 3.8+）
    )
    return logging.getLogger()
'''
# 使用示例
if __name__ == "__main__":
    logger = setlogger(level=logging.DEBUG)  # 设置为DEBUG级别
    logger.debug("这条日志会显示")  # 默认情况下DEBUG不显示，但因为我们设置了级别，现在会显示
    logger.info("这是一条INFO日志")
'''
import os
import glob
import logging
from datetime import datetime
from shancx import loggers as logger
def cleanupLogs(log_dir='/mnt/wtx_weather_forecast/scx/SATH9SEAStest/logs', keep_count=10, 
                 pattern='*.log', recursive=False, dry_run=False):
    stats = {'total_dirs': 0, 'deleted_files': 0, 'errors': []}    
    def _cleanup_dir(directory):
        stats['total_dirs'] += 1
        if not os.path.exists(directory):
            logging.warning(f"目录不存在: {directory}")
            return
        file_paths = glob.glob(os.path.join(directory, pattern))
        log_files = [(path, os.path.getmtime(path)) for path in file_paths]
        log_files.sort(key=lambda x: x[1], reverse=True)        
        if len(log_files) <= keep_count:
            logging.info(f"目录 {directory} 中的文件数量 ({len(log_files)}) 不超过保留数量 ({keep_count})，无需清理")
            return
        files_to_delete = log_files[keep_count:]
        for file_path, mtime in files_to_delete:
            try:
                if dry_run:
                    logging.info(f"[试运行] 将删除: {file_path} (修改时间: {datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')})")
                else:
                    os.remove(file_path)
                    logging.info(f"已删除: {file_path} (修改时间: {datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')})")
                stats['deleted_files'] += 1
            except Exception as e:
                error_msg = f"删除失败 {file_path}: {str(e)}"
                logging.error(error_msg)
                stats['errors'].append(error_msg)
    if recursive:
        for root, _, _ in os.walk(log_dir):
            _cleanup_dir(root)
    else:
        _cleanup_dir(log_dir)    
    return stats
"""
if __name__ == "__main__": 
    dir = "/mnt/wtx_weather_forecast/scx/SATH9SEAStest/logs/H9SEAS/"
    stats = cleanupLogs(dir,3, '*.log', False, False)    
    logging.info(f"清理完成: 处理目录数={stats['total_dirs']}, 删除文件数={stats['deleted_files']}, 错误数={len(stats['errors'])}")
    if stats['errors']:
        logging.error(f"错误详情: {stats['errors']}")
"""  

from itertools import product
from concurrent.futures import ProcessPoolExecutor as PoolExecutor, as_completed 
import sys
from tqdm import tqdm 
def validate_param_list(param_list):
    if len(param_list) == 0:
        raise ValueError("param_list cannot be empty.")    
    for sublist in param_list:
        if len(sublist) == 0:
            raise ValueError("Sub-lists in param_list cannot be empty.")     
def Mul_sub(task, param_list, num=6):
    print(f"Pro num {num}")
    validate_param_list(param_list)
    if len(param_list) == 1:
        product_list = [(x,) for x in param_list[0]]
    else:
        product_list = list(product(*param_list))
    with PoolExecutor(max_workers=num) as executor:
        try:           
            futures = [executor.submit(task, item) for item in product_list]
            for future in tqdm(as_completed(futures), total=len(futures), desc="Processing tasks", unit="task"):  
                future.result() 
        except KeyboardInterrupt:
            sys.exit(1)    
    print("All tasks completed")

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
            list(ex.map(task, task_args))
        except KeyboardInterrupt:
            print("\n用户中断操作")
            ex.shutdown(wait=False)
            sys.exit(1) 

import traceback
import shutil, os
def safe_del(path):
    try:
        shutil.rmtree(path) if os.path.isdir(path) else None
        print(f"{path} deleted")
    except Exception:
        print(traceback.format_exc())

"""
safe_del("./data")
"""

import os, glob
def clean_files(folder, keep=0):
    if os.path.isdir(folder):
        try:
            files = [os.path.join(folder, f) for f in os.listdir(folder) 
                    if os.path.isfile(os.path.join(folder, f))]
            if keep > 0 and len(files) > keep:
                files.sort(key=os.path.getmtime)
                [os.remove(f) for f in files[:-keep]]
            elif keep == 0:
                [os.remove(f) for f in files]
        except Exception as e:
            print(traceback.format_exc())

"""
clean_files("./logs", keep=10)   
clean_files("./temp") 
"""        

# import os
# from datetime import datetime
# from shancx.NN import _loggers
# from shancx import lock_file
# from shancx.wait import check_lock
# from shancx import crDir
# logger =_loggers()
# def check_process_data(UTC, sat_cd,basepath ="/mnt/wtx_weather_forecast/scx/test/lock_files" ): 
#     try:
#         UTCStr = UTC.strftime("%Y%m%d%H%M")
#         file = f"/mnt/wtx_weather_forecast/scx/test/lock_files/{sat_cd}/{UTCStr[:4]}/{UTCStr[:8]}/File_{UTCStr}.lock"
#         crDir(file)
#         if not lock_file(file):
#             if check_lock(file):
#                 logger.info("data is making or maked")
#                 return True ,file       
#         return False,file        
#     except Exception as e:
#         logger.error(f"Error in check_and_process_data: {str(e)}")
#         return False,file  
# """
# flag1,file = check_process_data(UTC, "H9SEAS" )
# if flag1:
#     sys.exit() 
# if os.path.exists(output_path): #配合使用
#    sys.exit()    
# """