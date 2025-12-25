
import matplotlib.pyplot as plt
import datetime
from hjnwtx.colormap import cmp_hjnwtx
import os
import numpy as np 

from pathlib import Path
def MDir(path):
    path_obj = Path(path)
    directory = path_obj.parent if path_obj.suffix else path_obj
    directory.mkdir(parents=True, exist_ok=True)
            
def plotRadarcoor(array_dt, temp="temp"):
    now_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    y_coords2, x_coords2 = np.where(array_dt > 0)    
    def plot_and_save(image, path):
        plt.imshow(image, vmin=0, vmax=10, cmap=cmp_hjnwtx["radar_nmc"])
        for (x, y) in zip(x_coords2, y_coords2):
            plt.plot(x, y, 'ro', markersize=25)  # Increase point size
            plt.text(x, y, f'{(image[y, x] * 6):.1f}', color='white', fontsize=12, ha='center', va='center')  # Label the corresponding value
        plt.colorbar()
        MDir(path)
        plt.savefig(path)
        plt.close()    
    if len(array_dt.shape) == 3:
        for i, img_ch_nel in enumerate(array_dt): 
            plot_and_save(img_ch_nel, f"./radar_nmc/{temp}_{now_str}.png")
    elif len(array_dt.shape) == 2:
        plt.imshow(array_dt, vmin=0, vmax=100, cmap=cmp_hjnwtx["pre_tqw"])
        plot_and_save(array_dt, f"./radar_nmc/{temp}_{now_str}.png")
