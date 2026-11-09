# -*- coding: utf-8 -*-
"""
Created on Fri Dec  1 15:51:36 2023

@author: Willi
"""
from PyQt5.QtWidgets import*
from PyQt5.uic import loadUi
import matplotlib.pyplot as plt
from matplotlib.offsetbox import (TextArea, DrawingArea, OffsetImage,
                                  AnnotationBbox)
from matplotlib.backends.backend_qt5agg import (NavigationToolbar2QT as NavigationToolbar)
import seaborn as sns
from sklearn.preprocessing import normalize

from modules import Preprocessor
from modules import Cell
from modules import Peakprocessor
from modules import Statsplot
import numpy as np
import pandas as pd
import matplotlib.colors as mc
from scipy.stats import norm
from scipy.ndimage import gaussian_filter1d, histogram, gaussian_filter
from sklearn.preprocessing import normalize
from sklearn.neighbors import KernelDensity
from scipy import interpolate

import numpy as np
from sklearn.mixture import GaussianMixture
from scipy.stats import norm

import time
import multiprocessing as mp
from itertools import repeat



class meanPlot():
    @staticmethod
    def createMeanPlot(cells, ax, globmax):
        plotAx = ax
        for key in cells.keys():
            datalist = [cell["processed_data"] for cell in cells[key]]
            overlaydata_df = pd.DataFrame(datalist)
            meanData = overlaydata_df.mean()
            ax.plot(meanData, label = key)
            ax.set_xticks(range(0,len(meanData), 300))
            ax.set_xticklabels([int(tick/60) for tick in ax.get_xticks()])
        ax.legend()
        
class densityOverlayPlot():
    
    @staticmethod
    def create_overlay_density(cells, ax, maximum, tmin = 0, tmax = -1, frameStepSize = 20, bandwidth = 0.25, fancy = False, ):
        plotAx = ax
        datalist = []
        for cell in cells:
            if len(cell["processed_data"]) > tmax:
                datalist.append(cell["processed_data"][tmin:tmax])
            else:
                datalist.append(cell["processed_data"][tmin:-1])
        acMax = maximum + 1
        overlaydata_df = pd.DataFrame(datalist)
        overlaydata_df = overlaydata_df.T
        hist_list = []
        
        """
        for index, row in overlaydata_df.iterrows():
            hist_list.append(np.histogram(row.dropna(), bins = 50, range = (0,200), density = False)[0])
        
        """
        cm = plt.get_cmap("turbo")
        rows = []
        temparr = []
        
        
        
        datacollection = []
        for index, row in overlaydata_df.iterrows():
            if len(rows) == frameStepSize:
                for i in rows:
                    temparr.append(i)
                
                
                temparr =  [p for k in temparr for p in k.dropna().to_numpy()]
                
                temparr2 = np.array(temparr)#.reshape(-1,1)
               
                datacollection.append(temparr2)
                rows = []
                temparr  = []
                
            else: rows.append(row)
        
      
        workercount = mp.cpu_count()
        
        chunksize = int(len(datacollection)/workercount)
        datacollection_chunks = np.array_split(np.array(datacollection, dtype = object), chunksize)
        
        print("prepared data")
        #pool = mp.Pool(processes = workercount)

        print("finished pool creation")
        
        # single Process Approach, works well with "low" but very slow with normal kde model
        ar = (len(overlaydata_df)/acMax)*0.6
        if not fancy:
            data = datacollection
            resultslist = calculate_model_low(data, bandwidth, cm, acMax)
            array = np.array(resultslist).T
            colors = cm(array)
            ax.imshow(colors, origin = "lower", extent = (0,len(overlaydata_df),0,acMax), aspect = ar)
        else:
            workercount = mp.cpu_count()
            chunksize = int(len(datacollection)/workercount)
            datacollection_chunks = np.array_split(np.array(datacollection,dtype = object), chunksize)
            print("prepared data")
            pool = mp.Pool(processes = workercount)
            print("finished pool creation")
            hist_list = pool.starmap(calculate_model, zip(datacollection_chunks, repeat(bandwidth), repeat(cm), repeat(acMax)))
            print("finished processing")
            hist_list = [li for arr in hist_list for li in arr]
            print("finished singles")
            array = np.array(hist_list).T
            colors = cm(array)
            print("T")
            #array = np.einsum("ijk->jki", array)
            print("")
            
            ax.imshow(colors, origin = "lower", extent = (0,len(overlaydata_df),0,acMax),aspect = ar)
            #ax.set_yticks(range(0, int(np.ceil(acMax)), 5))
            ax.set_xticks(range(0,len(overlaydata_df), 300))
            ax.set_xticklabels([int(tick/60) for tick in ax.get_xticks()])
            ax.set_xlabel("time [min]")
            ax.set_ylabel("norm. intensity [a.u.]")
            #ax.figure.tight_layout()
            
        """ not working
        pool = mp.Pool(processes = workercount)
        #hist_list = pool.starmap(calculate_model_low, zip(datacollection_chunks, repeat(bandwidth), repeat(cm)))
        
        #multiprocessing:
        pool = mp.Pool(processes = workercount)
        resultslist = []
        for chunk in datacollection_chunks:
            p = pool.apply_async(calculate_model, (chunk, bandwidth, cm))
            resultslist.append(p)
            
        resultslist = np.array(resultslist).flatten()
        pool.close()
        pool.join()
        """

def createBlackPlot():
    with plt.rc_context({'axes.edgecolor': 'black',
                         'axes.labelcolor': 'black',
                         'xtick.color': 'black',
                         'ytick.color': 'black'}):
        fig, axs = plt.subplots()
    return (fig, axs)
    
def calculate_model(data,bandwidth, cm, acMax):
    print("starting worker")
    X_plot = np.linspace(0, acMax, 1000)[:,np.newaxis]
    
    resultslist = []
    for dat in data:
        dat = dat.reshape(-1,1)
        kde = KernelDensity(kernel="gaussian",bandwidth = bandwidth).fit(dat)
        log_dens = kde.score_samples(X_plot)
        
        dens_arr = np.exp(log_dens)
        max_dens = max(dens_arr)
        norm_dens = [dens/max_dens for dens in dens_arr]
        
        
        resultslist.append(norm_dens)
        
    return resultslist

def calculate_model_low(data,bandwidth, cm, acMax):
    print("starting worker")
    #X_plot = np.linspace(-30, 200, 1000)[:,np.newaxis]

    resultslist = []
    for dat in data:
        dat = dat.tolist()
        norm_dens = np.histogram(dat,np.arange(-1,acMax,0.5), density = True)
        histData = norm_dens[0]
        histBins = norm_dens[1]
        
        binMeans = [(histBins[i]+histBins[i+1])/2 for i in range(len(histBins)-1)]
        f = interpolate.interp1d(binMeans, histData)
        xnew = np.arange(0,acMax-1,0.05)
        norm_dens_interp = f(xnew)
        
        max_dens = max(norm_dens_interp)
        norm_dens2 = [dens/max_dens for dens in norm_dens_interp]
        
        resultslist.append(norm_dens2)
    return resultslist
    