
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from mpl_toolkits.axes_grid1 import make_axes_locatable
import datetime
from shancx import crDir
def plotBorder(matrix,name='plotBorder',saveDir="plotBorder",extent=None,title='Matrix Plot', xlabel='X-axis', ylabel='Y-axis', color_label='Value', cmap='viridis'):
    if extent is None:  
        lat_min, lat_max = -3, 13
        lon_min, lon_max = -0, 28
    else:
        lat_min, lat_max, lon_min, lon_max = extent
    now_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
    ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=ccrs.PlateCarree())
    im = ax.imshow(
        matrix,
        extent=[lon_min, lon_max, lat_min, lat_max],
        origin='upper', 
        cmap='viridis',  
        transform=ccrs.PlateCarree()
    )
    ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
    ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.5)
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
    plt.tight_layout()   
    outpath = f'./{saveDir}/{name}_{now_str}.png' if name=="plotBorder" else f"./{saveDir}/{name}.png"
    crDir(outpath)
    plt.savefig(outpath)
    plt.close()
    
    
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
from hjnwtx.colormap import cmp_hjnwtx
import os
def plotGlobal(b, latArr1, lonArr1, cmap='summer', title='Global QPF Data Visualization',saveDir = "./plotGlobal" ):
    plt.figure(figsize=(20, 10), dpi=100)
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.add_feature(cfeature.LAND, facecolor='none')  # 陆地无色
    ax.add_feature(cfeature.OCEAN, facecolor='none')  # 海洋无色
    ax.add_feature(cfeature.COASTLINE, linewidth=0.8, edgecolor='black')  # 海岸线黑色
    ax.add_feature(cfeature.BORDERS, linestyle='-', linewidth=0.5, edgecolor='black')  # 国界线黑色
    ax.add_feature(cfeature.LAKES, alpha=0.3, facecolor='none', edgecolor='gray')  # 湖泊无色，灰色边界
    ax.add_feature(cfeature.RIVERS, edgecolor='gray', linewidth=0.5)  # 河流灰色
    lon_grid, lat_grid = np.meshgrid(lonArr1, latArr1)
    stride = 10  # 每10个点取1个
    img = ax.pcolormesh(lon_grid[::stride, ::stride], 
                       lat_grid[::stride, ::stride],
                       b[::stride, ::stride],
                       cmap=cmap, #cmp_hjnwtx["pre_tqw"],cmp_hjnwtx["radar_nmc"]
                       vmin=0, vmax=20,
                       shading='auto',
                       transform=ccrs.PlateCarree())
    cbar = plt.colorbar(img, ax=ax, orientation='vertical', pad=0.05, shrink=0.6)
    cbar.set_label('Value Scale', fontsize=12)
    ax.set_xticks(np.arange(-180, 181, 30), crs=ccrs.PlateCarree())
    ax.set_yticks(np.arange(-90, 91, 15), crs=ccrs.PlateCarree())
    ax.xaxis.set_major_formatter(LongitudeFormatter(zero_direction_label=True))
    ax.yaxis.set_major_formatter(LatitudeFormatter())
    ax.gridlines(color='gray', linestyle=':', alpha=0.5)
    ax.set_title(title, fontsize=16, pad=20)
    ax.set_global()     
    plt.tight_layout()
    os.makedirs(saveDir, exist_ok=True)
    plt.savefig(f"./{saveDir}/plotScatter_glob.png", dpi=300, bbox_inches="tight")  
    plt.close()
    
"""
plot_global_data(b, latArr1, lonArr1, 
                 cmap='jet', 
                title='Global Meteorological Data')

"""

import matplotlib as mpl 
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import geopandas as gpd
from cartopy.mpl.ticker import LongitudeFormatter,LatitudeFormatter
import numpy as np
from shancx import crDir
def plot_fig(cr,nclat,nclon,fig_title,datatype=None,savepath=None,font_path=None,shp_file=None):
    figpath = f"{savepath}/fig/{fig_title.split('_')[1][:4]}/{fig_title.split('_')[1][:8]}/{fig_title.split('_')[1][:12]}/{fig_title}.PNG"
    # if not os.path.exists(figpath):
    lonmin = np.min(nclon)
    lonmax = np.max(nclon)
    latmin = np.min(nclat)
    latmax = np.max(nclat)
    myfont = mpl.font_manager.FontProperties(fname = font_path, size = 12) 
    fig = plt.figure(figsize=(6,6))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_xticks(np.arange(lonmin, lonmax + 0.1, 15))
    ax.set_yticks(np.arange(latmin, latmax + 0.1, 10))
    ax.set_xlim([lonmin, lonmax])
    ax.set_ylim([latmin, latmax])
    ax.xaxis.set_major_formatter(LongitudeFormatter()) #刻度格式转换为经纬度样式                       
    ax.yaxis.set_major_formatter(LatitudeFormatter())
    ax.tick_params(axis = 'both',labelsize = 10)
    shp = gpd.read_file(shp_file).boundary
    shp.plot(ax=ax, edgecolor='grey', linewidth=0.7)
    ax.set_title(fig_title, fontsize = 12, loc='center',fontproperties = myfont) 
    if datatype == 'radar':
        clevels = [0,10, 20, 30, 40, 50, 60, 70]
        colors = ['#62e6eaff','#00d72eff','#fefe3fff','#ff9a29ff','#d70e15ff','#ff1cecff','#af91edff']
        # colors = ["#449ded", "#62e6ea", "#68f952", "#0000ff"]
    elif datatype == 'rain':  
        clevels = [0.1, 2.5, 8, 16,200]
        colors = ["#a6f28f", "#3dba3d", "#61b8ff", "#0000ff"]
    if datatype == 'sat':
        clevels = [150,170, 190, 210, 230, 250, 270, 290,310]
        colors = [
                '#00008B',  # 150K 深蓝
                '#0066CC',  # 170K 钴蓝
                '#00BFFF',  # 190K 深天蓝
                '#40E0D0',  # 210K 绿松石
                '#00FF00',  # 230K 亮绿
                '#FFFF00',  # 250K 黄色
                '#FFA500',  # 270K 橙色
                '#FF4500',  # 290K 橙红
                '#FF0000'   # 310K 红色
            ]
    cs = plt.contourf(nclon, nclat, cr, levels=clevels, colors=colors)    
    cb = plt.colorbar(cs, fraction=0.022)
    cb.set_ticks(clevels[:-1])
    cb.set_ticklabels([str(level) for level in clevels[:-1]],fontproperties = myfont)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(myfont)
    crDir(figpath)
    plt.savefig(figpath, dpi=300, bbox_inches='tight') 
    print(f"{fig_title.split('_')[0]}绘制完成: {figpath}")
    plt.close()
"""
font_path = './shp/微软雅黑.ttf'
myfont = mpl.font_manager.FontProperties(fname = font_path, size = 12) 
UTCstr="202508280000"
shp_file = "./shp/province_9south.shp"
savepath = f"./FY4BBIG"
fig_title = f"卫星反演雷达回波_{UTCstr}"
# base[20:1070,75:1625] = satCR
plot_fig(data,result['lats'],result['lons'],fig_title,datatype="radar")
"""


