#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time : 2024/10/17 上午午10:40
# @Author : shancx
# @File : __init__.py
# @email : shanhe12@163.com
from shancx import crDir
import matplotlib.pyplot as plt
import datetime
def plotGrey(img,name="plotGrey", saveDir="plotGrey",cmap='gray', title='Image'):
    now_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    img = img.squeeze()  # 去掉 batch 维度并转换为 numpy 数组
    plt.imshow(img, cmap='gray')
    plt.title(f"Image ")
    plt.axis('off')  # 不显示坐标轴
    outpath = f'./{saveDir}/{name}_{now_str}.png' if name=="plotGrey" else f"./{saveDir}/{name}.png"
    crDir(outpath)
    plt.savefig(outpath)
    plt.close()

import matplotlib.pyplot as plt
from shancx import crDir
import datetime
def plotMat(matrix,name='plotMat',saveDir="plotMat",title='Matrix Plot', xlabel='X-axis', ylabel='Y-axis', color_label='Value', cmap='viridis',aspect="equal"): #aspect='auto'
    now_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")    
    plt.imshow(matrix, cmap=cmap, origin='upper', aspect=f'{aspect}')
    plt.colorbar(label=color_label)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.tight_layout()
    outpath = f'./{saveDir}/{name}_{now_str}.png' if name=="plotMat" else f"./{saveDir}/{name}.png"
    crDir(outpath)
    plt.savefig(outpath)
    plt.close()

import matplotlib.pyplot as plt
from shancx import crDir
import datetime
def plotMatplus(matrix, name='plotMat', saveDir="plotMat", title='Matrix Plot', 
           xlabel='Longitude', ylabel='Latitude', color_label='Value', 
           cmap='viridis', extent=None):
    """
    extent: [lon_min, lon_max, lat_min, lat_max]
    """
    now_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")    
    plt.imshow(matrix, cmap=cmap, origin='upper', aspect='auto', extent=extent)
    plt.colorbar(label=color_label)
    plt.title(title)
    
    # 添加度符号和方向标识
    plt.xlabel(f'{xlabel} (°E)')  # 东经
    plt.ylabel(f'{ylabel} (°N)')  # 北纬
    
    plt.tight_layout()
    outpath = f'./{saveDir}/{name}_{now_str}.png' if name=="plotMat" else f"./{saveDir}/{name}.png"
    crDir(outpath)
    plt.savefig(outpath)
    plt.close()
"""
latlon = [10.0, 37.0, 105.0, 125.0] 
latmin, latmax, lonmin, lonmax = latlon 
plotMatplus(data,extent=[lon_min, lon_max, lat_min, lat_max]) 
"""

import datetime
from hjnwtx.colormap import cmp_hjnwtx
from shancx import crDir
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
def plotRadar(array_dt,name="plotRadar", saveDir="plotRadar",ty="CR"):
    now_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")    
    # array_dt[array_dt<=0] = np.nan 
    if len(array_dt.shape) == 2 and ty == "pre":
        fig, ax = plt.subplots()
        im = ax.imshow(array_dt, vmin=0, vmax=10, cmap=cmp_hjnwtx["pre_tqw"])        
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        plt.colorbar(im, cax=cax)   
        fig.tight_layout()     
        outpath = f"./{saveDir}/{name}_pre_{now_str}.png" if name=="plotRadar" else f"./{saveDir}/{name}.png"
        crDir(outpath)
        plt.savefig(outpath)
        plt.close()     
    else:
        fig, ax = plt.subplots()
        im = ax.imshow(array_dt, vmin=0, vmax=72, cmap=cmp_hjnwtx["radar_nmc"])        
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        plt.colorbar(im, cax=cax)   
        fig.tight_layout()     
        outpath = f"./{saveDir}/{name}_CR_{now_str}.png" if name=="plotRadar" else f"./{saveDir}/{name}.png"
        crDir(outpath)
        plt.savefig(outpath)
        plt.close()
 

import matplotlib.pyplot as plt
import numpy as np
import datetime
import os
from mpl_toolkits.axes_grid1 import make_axes_locatable
from hjnwtx.colormap import cmp_hjnwtx 
def plotA2b(a, b, name='plotA2b', saveDir="plotA2b", title='plotA2b Plot',class1 = "class",class2 = "class",ty="CR" ):
    now_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    cmap=cmp_hjnwtx["radar_nmc"] if ty == "CR" else 'summer'
    sublen = a.shape[0]
    fig, axes = plt.subplots(2, sublen, figsize=(20, 6))  
    for i in range(sublen):
        im_a = axes[0, i].imshow(a[i], cmap=cmap)
        axes[0, i].axis('off')
        axes[0, i].set_title(f'{class1}[{i}]')        
        divider_a = make_axes_locatable(axes[0, i])   
        cax_a = divider_a.append_axes("right", size="5%", pad=0.1)  
        cbar_a = fig.colorbar(im_a, cax=cax_a)   
        cbar_a.ax.tick_params(labelsize=8)   
    for i in range(sublen):
        im_b = axes[1, i].imshow(b[i], cmap=cmap)
        axes[1, i].axis('off')
        axes[1, i].set_title(f'{class2}[{i}]')        
        divider_b = make_axes_locatable(axes[1, i])   
        cax_b = divider_b.append_axes("right", size="5%", pad=0.1)   
        cbar_b = fig.colorbar(im_b, cax=cax_b)   
        cbar_b.ax.tick_params(labelsize=8)  
    plt.tight_layout()
    plt.subplots_adjust(top=0.9, bottom=0.1, hspace=0.05, wspace=0.1)  
    outpath = f'./{saveDir}/{name}_{now_str}.png'
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    plt.savefig(outpath, bbox_inches='tight', pad_inches=0.05)  
    plt.close()

import matplotlib.pyplot as plt
import os
def plotScatter(df1,saveDir="plotScatter"):
    now_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    plt.figure(figsize=(10, 8))   
    plt.scatter(
        df1["Lon"],  
        df1["Lat"],  
        s=25,        
        alpha=0.6,   
        edgecolor="black",   
        linewidth=0.5       
    )
    plt.title("Scatter Plot of Latitude vs Longitude", fontsize=14)
    plt.xlabel("Longitude", fontsize=12)
    plt.ylabel("Latitude", fontsize=12)
    plt.tight_layout()  
    os.makedirs(saveDir, exist_ok=True)
    plt.savefig(f"./{saveDir}/plotScatter_{now_str}.png", dpi=300, bbox_inches="tight")  
    plt.close()

import matplotlib.pyplot as plt
import os
def plotScatter1(true,pre,saveDir="plotScatter"):
    now_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    plt.figure(figsize=(10, 8))   
    plt.scatter(
        true,  
        pre,  
        s=25,        
        alpha=0.6,   
        edgecolor="black",   
        linewidth=0.5       
    )
    plt.title("Scatter Plot of Ture Pre", fontsize=14)
    plt.xlabel("Longitude", fontsize=12)
    plt.ylabel("Latitude", fontsize=12)
    plt.tight_layout()  
    os.makedirs(saveDir, exist_ok=True)
    plt.savefig(f"./{saveDir}/plotScatter1_{now_str}.png", dpi=300, bbox_inches="tight")  
    plt.close()

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
from shancx import crDir
import os
def plotVal( epoch=0,*datasets, title=["input","prediction","truth"], saveDir="plotVal", cmap='summer'):
    num_datasets = len(datasets)
    title = title or [f"data{i}" for i in range(num_datasets)]
    ncols = int(np.ceil(np.sqrt(num_datasets)))
    nrows = int(np.ceil(num_datasets / ncols))    
    fig, axes = plt.subplots(nrows, ncols, figsize=(12, 8))
    axes = axes.flatten()    
    for i, (data, t) in enumerate(zip(datasets, title)):
        im = axes[i].matshow(data, cmap=cmap)   #Paired  viridis  
        divider = make_axes_locatable(axes[i])
        cax = divider.append_axes("right", size="5%", pad=0.05)
        fig.colorbar(im, cax=cax)
        axes[i].set_title(t)    
    for j in range(i + 1, len(axes)):
        fig.delaxes(axes[j])    
    fig.tight_layout()
    os.makedirs(saveDir, exist_ok=True)
    filename = f"{saveDir}/epoch_{epoch}.png"
    plt.savefig(filename)
    plt.close(fig) 

    """    
        if total >= 3:
            break
    if epoch % 2 == 0:                    
       plotVal(epoch,   inputs[0]  --->example shape 为(256,256)
               inputs, 
               pre, 
               targets
               )  
    if epoch % 2 == 0: 
       plotVal(epoch,    
           data[0][0].detach().cpu().numpy().squeeze(),  # 使用 detach()
           output[0][0].detach().cpu().numpy().squeeze(),  # 使用 detach()
           label[0][0].detach().cpu().numpy().squeeze(),  # 使用 detach()
           title=["input", "prediction", "groundtruth"], 
           saveDir="plot_train_dir"
       )
    """
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
from shancx import crDir
import os

def plotValplus(epoch=0, *datasets, title=["input", "prediction", "truth"], saveDir="plotValplus", cmap='summer'):
    num_datasets = len(datasets)
    title = title or [f"data{i}" for i in range(num_datasets)]
    ncols = int(np.ceil(np.sqrt(num_datasets)))
    nrows = int(np.ceil(num_datasets / ncols))
    
    fig, axes = plt.subplots(nrows, ncols, figsize=(12, 8))
    axes = axes.flatten()
    
    for i, (data, t) in enumerate(zip(datasets, title)):
        # if np.isnan(data).any():
        #    print(f"Warning: NaN values found in dataset. Replacing NaN with 0.")
        # data = np.nan_to_num(data, nan=0.0)
        im = axes[i].matshow(data, cmap=cmap, vmin=np.nanmin(data), vmax=np.nanmax(data))
        axes[i].set_xticks([])
        axes[i].set_yticks([])
        divider = make_axes_locatable(axes[i])
        cax = divider.append_axes("right", size="5%", pad=0.05)
        cbar = fig.colorbar(im, cax=cax, ticks=np.linspace(np.nanmin(data), np.nanmax(data), 15))
        cbar.set_ticks(np.linspace(np.nanmin(data), np.nanmax(data), 15))        
        axes[i].set_title(t)    
    for j in range(i + 1, len(axes)):
        fig.delaxes(axes[j])    
    fig.tight_layout()    
    os.makedirs(saveDir, exist_ok=True)
    filename = f"{saveDir}/epoch_{epoch}.png"
    plt.savefig(filename)
    plt.close(fig)
    """    
    if total >= 3:
        break
    if epoch % 2 == 0: 
       plotValplus(epoch,    
           data[0][0].detach().cpu().numpy().squeeze(),  # 使用 detach()
           output[0][0].detach().cpu().numpy().squeeze(),  # 使用 detach()
           label[0][0].detach().cpu().numpy().squeeze(),  # 使用 detach()
           title=["input", "prediction", "groundtruth"], 
           saveDir="plot_train_dir"
       )
    """


def plotValplus1(epoch=0, *datasets, title=["input", "prediction", "truth"], saveDir="plotValplus", cmap='summer'):
    """
    Main function to plot multiple datasets in a grid layout.
    """
    plt.ioff()  
    num_datasets = len(datasets)
    title = title or [f"data{i}" for i in range(num_datasets)]
    ncols = int(np.ceil(np.sqrt(num_datasets)))
    nrows = int(np.ceil(num_datasets / ncols))    
    # Create subplots
    fig, axes = plt.subplots(nrows, ncols, figsize=(12, 8))
    axes = axes.flatten()    
    # Plot each dataset
    for i, (data, t) in enumerate(zip(datasets, title)):
        if i != 0:
            vmin, vmax = 0, 70
            cmap_used = cmp_hjnwtx["radar_nmc"]
            plot_dataset(axes[i], data, t, cmap_used, vmin, vmax)
        else:
            # vmin, vmax = 150, 300
            cmap_used = cmap  #        
            plot_dataset(axes[i], data, t, cmap_used,np.min(data),np.max(data))    
    # Remove unused subplots
    for j in range(i + 1, len(axes)):
        fig.delaxes(axes[j])    
    # Adjust layout and save the figure
    fig.tight_layout()
    os.makedirs(saveDir, exist_ok=True)
    filename = f"{saveDir}/epoch_{epoch}.png"
    plt.savefig(filename)
    plt.close(fig) 

    """    
    if total >= 3:
        break
    if epoch % 2 == 0: 
       plotValplus1(epoch,    
           data[0][0].detach().cpu().numpy().squeeze(),  # 使用 detach()
           output[0][0].detach().cpu().numpy().squeeze(),  # 使用 detach()
           label[0][0].detach().cpu().numpy().squeeze(),  # 使用 detach()
           title=["input", "prediction", "groundtruth"], 
           saveDir="plot_train_dir"
       )
    """

import numpy as np
import matplotlib
matplotlib.use("Agg") 
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
from hjnwtx.colormap import cmp_hjnwtx
from shancx import crDir
import os
def plot_dataset(ax, data, title, cmap, vmin, vmax):    #Cited methods
    """
    Helper function to plot a single dataset on a given axis.
    """
    im = ax.matshow(data, cmap=cmap, vmin=vmin, vmax=vmax)    
    # Remove axis ticks
    ax.set_xticks([])
    ax.set_yticks([])    
    # Add colorbar
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.05)
    cbar = plt.colorbar(im, cax=cax, ticks=np.linspace(vmin, vmax, 15))
    cbar.set_ticks(np.linspace(vmin, vmax, 15))    
    # Set title
    ax.set_title(title)    
    return im

import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import numpy as np
import os
import datetime
import pandas as pd 
from multiprocessing import Pool
import argparse
from itertools import product
import glob 
def calculate_colorbar_range(data):
    vmin = int(np.nanmin(data))
    vmax = int(np.nanmax(data))
    return vmin, vmax
def plotgriddata(data, titles=None,name="temp", save_dir="plots", 
                   cmap="viridis", vmin=None, vmax=None):   #Cited methods
    if not isinstance(data, np.ndarray) or data.ndim != 3:
        raise ValueError("The input data must be a three-dimensional NumPy array [num_images, height, width]")    
    num_images = data.shape[0]
    titles = titles or [f"Data {i}" for i in range(num_images)]
    ncols = int(np.ceil(np.sqrt(num_images)))
    nrows = int(np.ceil(num_images / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(ncols * 3, nrows * 3))
    axes = axes.ravel()
    for i in range(num_images):
        ax = axes[i]
        im = ax.imshow(data[i], cmap=cmap)
        ax.set_title(titles[i])
        ax.axis('off')        
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        cbar = plt.colorbar(im, cax=cax,
                          format='%.1f')   
        cbar.ax.tick_params(labelsize=6)   
    for j in range(num_images, len(axes)):
        axes[j].axis('off')
    plt.tight_layout()
    os.makedirs(save_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{name}_{timestamp}.png"
    plt.savefig(os.path.join(save_dir, filename), dpi=300)
    plt.close()
def plotDrawpic(basedata, save_dir="plotDrawpic_com", name="temp", cmap="summer"): 
    data_all = basedata[:,::2,::2]
    if isinstance(name, str):
        print("name str")
        titles = [f"channel_{i+1} {name}" for i in range(basedata.shape[0])]  
    else:
        titles = [f"{i}" for i in name.strftime("%Y%m%d%H%M%S")]
        name = name.strftime("%Y%m%d%H%M%S")[0]
    plotgriddata(
        data=data_all,
        titles=titles,
        name=name,
        save_dir=save_dir,
        cmap=cmap
    ) 

"""
drawpic_com(Data_con, save_dir="plotDrawpic_com", name=timeList )
""" 
from hjnwtx.colormap import cmp_hjnwtx
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import numpy as np
import os
import datetime
def plot_grid_data(data, titles=None, saveDir="plots", name="temp", cmap="summer"):
    if not isinstance(data, np.ndarray) or data.ndim != 3:
        raise ValueError("The input data must be a three-dimensional NumPy array [num_images, height, width]")    
    num_images = data.shape[0]
    titles = titles or [f"Data {i}" for i in range(num_images)]    
    ncols = int(np.ceil(np.sqrt(num_images)))
    nrows = int(np.ceil(num_images / ncols))    
    fig, axes = plt.subplots(nrows, ncols, figsize=(ncols * 4, nrows * 3))
    if num_images == 1:
        axes = np.array([[axes]])
    elif axes.ndim == 1:
        axes = axes.reshape(1, -1)    
    axes_flat = axes.ravel()    
    for i in range(num_images):
        ax = axes_flat[i]
        if i == num_images - 1:
            im = ax.imshow(data[i], cmap=cmp_hjnwtx["radar_nmc"])
        else:
            im = ax.imshow(data[i], cmap=cmap)        
        ax.set_title(titles[i])
        ax.axis('off')
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        plt.colorbar(im, cax=cax)
    for j in range(num_images, len(axes_flat)):
        axes_flat[j].axis('off')    
    plt.tight_layout()
    os.makedirs(saveDir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{name}_{timestamp}.png"
    plt.savefig(os.path.join(saveDir, filename), dpi=300)
    plt.close()

def plotTr(base_up, base_down, name="plotTr", saveDir="plotTr",cmap="summer"):
    data_all = np.concatenate([base_up, base_down], axis=0)
    titles = [f"Pic_{i}" for i in range(base_up.shape[0])] + [f"Pic_{i+1}" for i in range(base_down.shape[0])]    
    plot_grid_data(
        data=data_all,
        titles=titles,
        name=name,
        saveDir=saveDir,
        cmap=cmap
    )

""" 
if __name__ == "__main__":
    base_up = np.random.rand(10, 50, 50) * 70
    base_down = np.random.rand(1, 50, 50) * 70
    plotTr(base_up, base_down, name="radar_plot",cmap="summer") #   radar_mask.detach().cpu().numpy()  tensor转numpy 
"""

import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from mpl_toolkits.axes_grid1 import make_axes_locatable
def plotBorder(matrix,name='plotBorder',saveDir="plotBorder",extent=None,title='Matrix Plot', xlabel='X-axis', ylabel='Y-axis', color_label='Value', cmap='viridis'):
    # 地理范围 (lat_min, lat_max, lon_min, lon_max)  #[0,57,-132.0,-47] NA
    if extent is None:  
        lat_min, lat_max = -3, 13
        lon_min, lon_max = -0, 28
    else:
        lat_min, lat_max, lon_min, lon_max = extent
    # 创建地图
    now_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
    ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=ccrs.PlateCarree())
    im = ax.imshow(
        matrix,
        extent=[lon_min, lon_max, lat_min, lat_max],
        origin='upper',  # 卫星数据通常 origin='upper'
        cmap='viridis',  # 选择合适的 colormap
        transform=ccrs.PlateCarree()
    )
    ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
    ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.5)
    # 添加美国州边界（50m 分辨率）
    states = cfeature.NaturalEarthFeature(
        category='cultural',
        name='admin_1_states_provinces_lines',
        scale='50m',
        facecolor='none'
    )
    ax.add_feature(states, edgecolor='red', linewidth=0.5)
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.1, axes_class=plt.Axes)
    cbar = plt.colorbar(im, cax=cax, label='Data Values')
    ax.set_title('Sat data Boundaries', fontsize=14)
    plt.tight_layout()  # 优化布局
    outpath = f'./{saveDir}/{name}_{now_str}.png' if name=="plotBorder" else f"./{saveDir}/{name}.png"
    crDir(outpath)
    plt.savefig(outpath)
    plt.close()