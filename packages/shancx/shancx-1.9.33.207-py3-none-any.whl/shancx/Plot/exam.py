from matplotlib import pyplot as plt
import numpy as np
def drawHigh_new(TSV,F1V,ACCV,outpath):
    TS_WTX = np.asarray(list(TSV.values()))
    F1_WTX = np.asarray(list(F1V.values()))
    ACC_WTX =np.asarray(list(ACCV.values()))
    time = ['1h', '2h','3h']
    TS_WTX = np.asarray(list(TSV.values()))
    plt.figure(figsize=(6, 4))
    inspect_flag = "TS"
    plt.subplot(131)
    bar_width = 0.3
    plt.bar(time,[TS_WTX[0][0],TS_WTX[1][0],TS_WTX[2][0]],  width=bar_width , label='WTX')
    plt.xlabel('Time')
    plt.ylabel(f'{inspect_flag}')
    plt.title(f'{inspect_flag}')
    plt.grid(axis="y")    
    inspect_flag = "F1"
    TS_WTX = np.asarray(list(TSV.values()))
    plt.subplot(132)
    bar_width = 0.3
    plt.bar(time,[F1_WTX[0][0],F1_WTX[1][0],F1_WTX[2][0]],  width=bar_width , label='WTX')
    plt.xlabel('Time')
    plt.ylabel(f'{inspect_flag}')
    plt.title(f'{inspect_flag}')
    plt.grid(axis="y")    
    inspect_flag = "ACC"
    TS_WTX = np.asarray(list(TSV.values()))
    plt.subplot(133)
    bar_width = 0.3
    plt.bar(time,[ACC_WTX[0][0],ACC_WTX[1][0],F1_WTX[2][0]],  width=bar_width , label='WTX')
    plt.xlabel('Time')
    plt.ylabel(f'{inspect_flag}')
    plt.title(f'{inspect_flag}')
    plt.grid(axis="y")  
    plt.tight_layout()
    plt.savefig(outpath)
    plt.close()    

def drawLow_new(POV,FARV,outpath):
    time = ['1h', '2h']
    PO_WTX = np.asarray(list(POV.values()))
    FAR_WTX = np.asarray(list(FARV.values()))
    inspect_flag = "PO"
    time = ['1h', '2h','3h']
    plt.figure(figsize=(6, 4))
    plt.subplot(121)
    bar_width = 0.3
    plt.bar(time,[PO_WTX[0][0],PO_WTX[1][0],PO_WTX[2][0]],  width=bar_width , label='WTX')
    plt.xlabel('Time')
    plt.ylabel(f'{inspect_flag}')
    plt.title(f'{inspect_flag}')
    plt.grid(axis="y")    
    plt.tight_layout()
    inspect_flag = "FAR"
    plt.subplot(122)
    bar_width = 0.3
    plt.bar(time,[FAR_WTX[0][0],FAR_WTX[1][0],FAR_WTX[2][0]],  width=bar_width , label='WTX')
    plt.xlabel('Time')
    plt.ylabel(f'{inspect_flag}')
    plt.title(f'{inspect_flag}')
    # plt.xticks(index + bar_width / 2, time) 
    plt.grid(axis="y")    
    plt.tight_layout()
    plt.savefig(outpath)
    plt.close()
"""
POV = {}
for i in range(1,4):
    F1hm =PO(df[f"PRE{i}_r"], df[f"PRE{i}_w"])
    POV[i] = [np.round(F1hm, 3)]
POV
{1: [0.45], 2: [0.67], 3: [0.778]}
"""     
    
def drawLow(POV,FARV,outpath):
    time = ['1h', '2h']
    PO_CY = np.asarray(list(POV.values()))[:,0].astype(float)
    PO_WTX = np.asarray(list(POV.values()))[:,1].astype(float)
    FAR_CY =  np.asarray(list(FARV.values()))[:,0].astype(float)
    FAR_WTX = np.asarray(list(FARV.values()))[:,1].astype(float)    
    plt.figure(figsize=(8, 4))
    bar_width = 0.35
    index = np.arange(len(time))
    x_pos = index + bar_width / 2 # 刻度标签位置
    plt.subplot(121)
    plt.bar(index, PO_CY, bar_width, label='CY')
    plt.bar(index + bar_width, PO_WTX, bar_width, label='WTX')
    plt.xlabel('Time')
    plt.ylabel('PO')
    plt.title('PO 对比')
    plt.xticks(x_pos, time)  
    plt.legend()
    plt.grid(axis="y")
    plt.subplot(122)
    plt.bar(index, FAR_CY, bar_width, label='CY')
    plt.bar(index + bar_width, FAR_WTX, bar_width, label='WTX')
    plt.xlabel('Time')
    plt.ylabel('FAR')
    plt.title('FAR 对比')
    plt.xticks(x_pos, time)  
    plt.legend()
    plt.grid(axis="y")
    plt.tight_layout()
    plt.savefig(outpath)
    plt.close()    
"""
POV = {}
for i in range(1,3):
    F1h =PO(df[f"PRE{i}_r"], df[f"PRE{i}_c"],thresholdF=thresholdF)
    F1hm =PO(df[f"PRE{i}_r"], df[f"PRE{i}_w"])
    POV[i] = [np.round(F1h, 3), np.round(F1hm, 3),f"{np.round((F1hm-F1h)/F1h*100,2)*-1}%"]
    print(f"{i}h {np.round(F1h,3)} {np.round(F1hm,3)} {np.round((F1hm-F1h)/F1h*100,2)*-1}%")
POV    CY  WTX
{1: [0.778, 0.556, '28.57%'], 2: [1.0, 0.875, '12.5%']}
"""