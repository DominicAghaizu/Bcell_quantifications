# -*- coding: utf-8 -*-
"""
Created on Fri Aug  4 14:56:50 2023

@author: Willi
"""

from PyQt5.QtWidgets import*
from PyQt5.uic import loadUi
from PyQt5.QtGui import (QBrush, QColor)
from PyQt5.QtCore import Qt
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
from modules import timeSeriesClustering
import numpy as np
import pandas as pd
import matplotlib.colors as mc
from scipy.stats import norm
from sklearn.preprocessing import normalize
from sklearn.neighbors import KernelDensity


import numpy as np
from sklearn.mixture import GaussianMixture
from scipy.stats import norm

import time
import multiprocessing as mp
from itertools import repeat

class Overlay_Dialog(QDialog):
    
    def __init__(self, datahandler, parentFileTree):

        super(Overlay_Dialog, self).__init__()
        
        loadUi("PyQT5_UI-Files/overlay_dialog.ui",self)
        self.bandwidth = float(self.input_Bandwidth.text())
        self.button_refreshOverlay.clicked.connect(self.refreshOverlay)
        self.twod_init = False
        self.centerLines = []
        
        self.datahandler = datahandler
        self.kMeans = int(self.input_kMeans.text())
        self.cropLength =  int(self.input_CropLength.text())
        
        
        self.button_kMeansModel.clicked.connect(self.setClusteringModel)
        self.button_kMeansPredict.clicked.connect(self.executePredict)
        self.button_appendClustering.clicked.connect(self.appendClustering)
        self.fileTreeLinker = {}
        self.frameStepSize = 20
        self.initiate_graph()
        self.initiateFileTree(parentFileTree)
        self.create_overlay()
        self.plotDataLengthDens()
        
        
    def refreshFromUI(self):
        self.bandwidth = float(self.input_Bandwidth.text())
        
    def initiate_graph(self):
        Mpls = [self.MplWidget_overlay, self.MplWidget_overlay_density, self.MplWidget_dataLengths]
        
        for Mpl in Mpls:
            Mpl.canvas.axes = Mpl.canvas.figure.add_subplot(111)
            Mpl.canvas.axes.clear()
    
            Mpl.canvas.figure.set_facecolor("#19232d")
            Mpl.canvas.axes.set_facecolor("#19232d")
    
            Mpl.canvas.figure.set_edgecolor("white")
            Mpl.canvas.axes.tick_params(colors='white', which='both') 
            Mpl.canvas.draw()
    
    def initiateFileTree(self, parentFileTree):
        newItems = []
        n = parentFileTree.topLevelItemCount()
        for i in range(n):
            item = parentFileTree.topLevelItem(i)
            txt = item.text(0)
            
            tempQcolor = item.plotColor
            newItem = QTreeWidgetItem(self.overlay_FileTree)
            newItem.setBackground(2, QBrush(QColor(tempQcolor)))
            newItem.setText(0, txt)
            newItem.setCheckState(0, Qt.CheckState.Checked)
            newItems.append(newItem)
            self.fileTreeLinker[txt] = item
            
        self.overlay_FileTree.addTopLevelItems(newItems)
        
    
        
        if self.comboBox_autoBandwidth.currentText() == "none":
            self.bandwidth = float(self.input_Bandwidth.text())
        else: self.bandwidth = self.comboBox_autoBandwidth.currentText()
        
        
    def appendClustering(self):
        data = self.datahandler.work_data
        datalist = []
        for key in data:
            for cell in data[key]:
                dat = cell["processed_data"]
                euclid = []
                datLen = len(dat)
                for center in self.centers:
                    centerLen = len(center)
                    if datLen == centerLen:
                        allignedDat = center
                        allignedCenter = dat
                    elif centerLen > datLen:
                        allignedCenter = center[:datLen]
                        allignedDat = dat
                    else:
                        allignedDat = dat[:centerLen]
                        allignedCenter = center
                        
                    euclid.append(np.mean([np.square(allignedCenter[i]-allignedDat[i]) for i in range(len(allignedDat))]))
                cell["cluster"] = np.argmin(euclid)
                
                
            
    def create_overlay(self):
        
        ax = self.MplWidget_overlay.canvas.axes
        data = self.datahandler.work_data
        datalist = []
        for key in data:
            for cell in data[key]:
                ax.plot(cell["processed_data"], linewidth = 1, c = "white")
                datalist.append(cell["processed_data"])
        self.overlaydata_df = pd.DataFrame(datalist)
        self.overlayVerticalCursor = overviewBlittedCursor(self.MplWidget_overlay.canvas, parent = self)

        print(self.overlaydata_df)
    
    def executePredict(self):
        #labels = self.clustering.getLabels()
        #print(labels)
        ax = self.MplWidget_overlay.canvas.axes
        if len(self.centerLines) != 0:
            for line in self.centerLines:
                line.remove()
        
        self.centerLines = []
        centers = self.clustering.getClusterCenters()
        centers = sorted(centers, key = lambda x: np.mean(x))
        self.centers = centers
        for center in centers: 
            self.centerLines.append(ax.plot(center, c = "green")[0])
        self.MplWidget_overlay.canvas.draw()
        
    def setClusteringModel(self):
        if self.radioButton_selectedData.isChecked():
            self.clustering = timeSeriesClustering.tsClustering(self.datahandler.work_data,nMeans = self.kMeans,  cropLength = self.cropLength, keys = self.activeItems, metric = self.comboBox_metric.currentText())
        else:
            self.clustering = timeSeriesClustering.tsClustering(self.datahandler.work_data,nMeans = self.kMeans,  cropLength = self.cropLength, metric = self.comboBox_metric.currentText())
        changed = False
        newCropLength = int(self.input_CropLength.text())
        newkMeans = int(self.input_kMeans.text())
        if self.cropLength != newCropLength:
            self.clustering.cropLength = newCropLength
            self.cropLength = newCropLength
            changed = True
        if self.kMeans != newkMeans:
            self.clustering.n = newkMeans
            self.kMeans = newkMeans
            
        if self.clustering.transformedData is None or changed:
            self.clustering.transformForTs()
            
        self.clustering.setModel()
            
    def plotDataLengthDens(self):
        ax = self.MplWidget_dataLengths.canvas.axes
        sns.kdeplot(data = self.overlaydata_df.count(axis = 1) , ax = ax)
        ax.set_axis_off()
        
        self.dataLengthVerticalCursor = BlittedVerticalCursor(self.MplWidget_dataLengths.canvas, self.input_CropLength)
        
        self.MplWidget_dataLengths.canvas.mpl_connect('motion_notify_event', self.dataLengthVerticalCursor.on_mouse_move)
        self.MplWidget_dataLengths.canvas.mpl_connect('button_release_event', self.dataLengthVerticalCursor.on_mouse_clicked)
        
        self.MplWidget_dataLengths.canvas.figure.tight_layout()

    
    def create_overlay_density(self):
        ax = self.MplWidget_overlay_density.canvas.axes
        ax.clear()
        
        hist_list = []
        
        """
        for index, row in self.overlaydata_df.iterrows():
            hist_list.append(np.histogram(row.dropna(), bins = 50, range = (0,200), density = False)[0])
        
        """
        cm = plt.get_cmap("viridis")
        rows = []
        temparr = []
        
        
        
        datacollection = []
        for index, row in self.overlaydata_df.T.iterrows():
            if len(rows) == self.frameStepSize:
                for i in rows:
                    temparr.append(i)
                
                
                temparr =  [p for k in temparr for p in k.dropna().to_numpy()]
                
                temparr2 = np.array(temparr).reshape(-1,1)
                
                datacollection.append(temparr2)
                rows = []
                temparr  = []
                
            else: rows.append(row)
        
        workercount = mp.cpu_count()
        
        bandwidth = self.bandwidth
        
        chunksize = int(len(datacollection)/workercount)
        datacollection_chunks = np.array_split(np.array(datacollection,dtype = object), chunksize)
        print("prepared data")
        pool = mp.Pool(processes = workercount)
        print("finished pool creation")
        hist_list = pool.starmap(calculate_model, zip(datacollection_chunks, repeat(bandwidth), repeat(cm)))
        print("finished processing")
        
        self.raw_dens = [li[1] for arr in hist_list for li in arr]
        self.ind_pdf = [li[2] for arr in hist_list for li in arr]
        hist_list = [li[0] for arr in hist_list for li in arr]
        print(hist_list)
        self.hist_list = hist_list
        print("finished singles")
        array = np.array(hist_list).T
        print("T")
        array = np.einsum("ijk->jki", array)
        print("")
        ax.imshow(array, origin = "lower", extent = (0,1000,0,500))
        self.MplWidget_overlay_density.canvas.draw()
        self.densBackground = self.MplWidget_overlay_density.canvas.copy_from_bbox(self.MplWidget_overlay_density.canvas.figure.bbox)
        
        self.create_2dcut()
        
    def createLocalOverlayDensity(self, position):
        self.refreshFromUI()
        ax = self.MplWidget_overlay_density.canvas.axes
        ax.clear()
        

        
        rows = []
        temparr = []
        
        
        
        datacollection = []
        for index, row in self.overlaydata_df.T.iterrows():
            if len(rows) == self.frameStepSize:
                for i in rows:
                    temparr.append(i)
                   
                temparr =  [p for k in temparr for p in k.dropna().to_numpy()]
                
                temparr2 = np.array(temparr).reshape(-1,1)
                
                datacollection.append(temparr2)
                rows = []
                temparr  = []
                
            else: rows.append(row)
        
        
        bandwidth = self.bandwidth
        index = int(position/self.frameStepSize)
        dataChunk = datacollection[index]
        
        cm = plt.get_cmap("viridis")
        hist_list = calculate_model([dataChunk], bandwidth, cm)
        raw_dens = [arr[1] for arr in hist_list]
        ind_pdf = [arr[2] for arr in hist_list]
        ax.plot(raw_dens[0])
        #ax.plot(ind_pdf[0])
        
        self.MplWidget_overlay_density.canvas.draw()
    
    def refreshOverlay(self):
         ax = self.MplWidget_overlay.canvas.axes
         ax.clear()
         items = [self.overlay_FileTree.topLevelItem(ind) for ind in range(self.overlay_FileTree.topLevelItemCount()) if self.overlay_FileTree.topLevelItem(ind).checkState(0)]
         itemNames = [i.text(0) for i in items]
         
         items = [self.fileTreeLinker[name] for name in itemNames]
         self.activeItems = []
         for it in items:
             if it.isGroup():
                 [self.activeItems.append(subItem.text(0)) for subItem in it.fileItems]
             else:
                 self.activeItems.append(it.text(0))
         datalist = []
         for item in items:
             for cell in item.getCells():
                 ax.plot(cell["processed_data"], linewidth = 1, c = "white")
                 datalist.append(cell["processed_data"])
         self.overlaydata_df = pd.DataFrame(datalist)
         self.MplWidget_overlay.canvas.draw()
         
        
    def create_2dcut(self):
        slider = self.frames_slider_2d
        slider.setValue(0)
        slider.setMaximum(len(self.raw_dens)-1)
        
        self.MplWidget_overlay_2dcut.canvas.axes.plot(self.raw_dens[0])
        self.MplWidget_overlay_2dcut.canvas.axes.plot(self.ind_pdf[0])
        self.MplWidget_overlay_2dcut.canvas.draw()
        self.frameLine = self.MplWidget_overlay_density.canvas.axes.axvline(0,ymax = 500, animated = True)
        
        self.twod_init = True
        
    """   
    def handleSliderMovement(self):
        if self.twod_init:
            frame = self.frames_slider_2d.value()
            
            ax = self.MplWidget_overlay_2dcut.canvas.axes
            ax.clear()
            ax.plot(self.raw_dens[frame])
            ax.plot(self.ind_pdf[frame],'--k')
            
            canvas = self.MplWidget_overlay_density.canvas
            canvas.restore_region(self.densBackground)
            self.frameLine.set_xdata([self.frameStepSize*frame,self.frameStepSize*frame])
            
            canvas.axes.draw_artist(self.frameLine)
            canvas.blit(canvas.figure.bbox)
            canvas.flush_events()
    
            self.MplWidget_overlay_2dcut.canvas.draw()
        self.MplWidget_dataLengths.canvas.draw()
      """
        
class BlittedVerticalCursor:    #adapted from https://matplotlib.org/stable/gallery/event_handling/cursor_demo.html
    """
    A cross-hair cursor using blitting for faster redraw.
    """
    def __init__(self, canvas, cursorPos = None):
        
        self.ax = canvas.axes
        canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        canvas.mpl_connect('button_release_event', self.on_mouse_clicked)
        self.cursorPos = cursorPos
        self.background = None
        self.vertical_line = self.ax.axvline(color='white', lw=0.8, ls='--')
        # text location in axes coordinates
        self.text = self.ax.text(0.1, 0.8, '', transform=self.ax.transAxes, c = "white")
        self._creating_background = False
        self.ax.figure.canvas.mpl_connect('draw_event', self.on_draw)

    def on_draw(self, event):
        self.create_new_background()

    def set_cross_hair_visible(self, visible):
        need_redraw = self.vertical_line.get_visible() != visible
        self.vertical_line.set_visible(visible)
        self.text.set_visible(visible)
        return need_redraw

    def create_new_background(self):
        if self._creating_background:
            # discard calls triggered from within this function
            return
        self._creating_background = True
        self.set_cross_hair_visible(False)
        self.ax.figure.canvas.draw()
        self.background = self.ax.figure.canvas.copy_from_bbox(self.ax.bbox)
        self.set_cross_hair_visible(True)
        self._creating_background = False

    def on_mouse_move(self, event):
        if self.background is None:
            self.create_new_background()
        if not event.inaxes is self.ax:
            need_redraw = self.set_cross_hair_visible(False)
            if need_redraw:
                self.ax.figure.canvas.restore_region(self.background)
                self.ax.figure.canvas.blit(self.ax.bbox)
        else:
            self.set_cross_hair_visible(True)
            # update the line positions
            x = event.xdata
            self.vertical_line.set_xdata([x])
            self.text.set_text(str(int(x)))

            self.ax.figure.canvas.restore_region(self.background)
            self.ax.draw_artist(self.vertical_line)
            self.ax.draw_artist(self.text)
            self.ax.figure.canvas.blit(self.ax.bbox)
        
    def on_mouse_clicked(self, event):
         if event.inaxes is self.ax:
             if not self.cursorPos is None:
                 self.cursorPos.setText(str(int(event.xdata)))
            
            
class overviewBlittedCursor(BlittedVerticalCursor):
    def __init__(self, *data, parent):
        super().__init__(*data)
        self.parentOverlayDialog = parent
        
    def on_mouse_clicked(self, event):
         if event.inaxes:
             self.parentOverlayDialog.createLocalOverlayDensity(event.xdata)
             
        
def calculate_model(data, bandwidth, cm):
    print("starting worker")
    X_plot = np.linspace(0, 25, 1000)[:,np.newaxis]
    resultslist = []
    
    for dat in data:
        kde = KernelDensity(kernel="gaussian",bandwidth = bandwidth).fit(dat)
        log_dens = kde.score_samples(X_plot)
        
        N = np.arange(1, 5)
        models = [None for i in range(len(N))]
        for i in range(len(N)):
            models[i] = GaussianMixture(N[i]).fit(dat)
        BIC = [m.bic(dat) for m in models]
        M_best = models[np.argmin(BIC)]
        logprob = M_best.score_samples(X_plot)
        responsibilities = M_best.predict_proba(X_plot)
        pdf = np.exp(logprob)
        pdf_individual = responsibilities * pdf[:, np.newaxis]
        
        dens_arr = np.exp(log_dens)
        max_dens = max(dens_arr)
        norm_dens = [dens/max_dens for dens in dens_arr]
        
        colors = cm(norm_dens)
        resultslist.append([colors,dens_arr, pdf_individual])
    return(resultslist)
        