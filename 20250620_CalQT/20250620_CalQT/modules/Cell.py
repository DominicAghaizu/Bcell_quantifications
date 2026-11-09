# -*- coding: utf-8 -*-
"""
Created on Wed Jan 11 18:36:56 2023

@author: Willi
"""
from PyQt5.QtWidgets import  QTreeWidgetItem
from pandas import DataFrame
from collections import UserDict
import numpy as np
import scipy.signal as ss
from modules import Peakprocessor

# This whole thing is probably a bad idea in in retrospective.
# It was originally created for simple observation of data usign the spyder ui, as visualisation of dictionarys is already implemented 
# Note that data is written to the Cell_Dict Objects when created on data import in the datahandler
# namely [Cell.Cell_Dict({"Path": path_alias,"Track": track, "Raw_Data":temp_data[temp_data["TRACK_ID"] == track].sort_values(by = "FRAME")[["MEAN_INTENSITY_CH1","POSITION_X", "POSITION_Y"]].reset_index()}) for track in temp_data["TRACK_ID"].unique()]
class Cell_Dict(dict):
    
    def __init__(self, data):
        super().__init__(data)
        self["tracklength"] = len(self["Raw_Data"]["MEAN_INTENSITY_CH1"])
        self["in_filter"] = True
        
        self["peaks"] = None
        self["multipeak"] = False
        self["haspeak"] = False
        
        self["tsGroup"] = None
        
        self["plotColor"] = "#FFFFFF"
        self["signalMean"] = np.mean(self["Raw_Data"]["MEAN_INTENSITY_CH1"])
        self["distanceTraveled"] = self.calculateMovement()/len(self["Raw_Data"]["MEAN_INTENSITY_CH1"])
        self["maxHeight"] = max(self["Raw_Data"]["MEAN_INTENSITY_CH1"])
        
        
    def make_TreeWidgetItem(self):
        self._cell_item = Cell_Item(self)
       
        t_id = str(self["Track"])
        
        self._cell_item.setText(0,t_id)
        self._cell_item.setText(1,str(self["tracklength"]))
        
        return self._cell_item
    
    def append_processed_data(self, cell_preprocessor):
        self["processed_data"] = self["Raw_Data"]["MEAN_INTENSITY_CH1"].copy()
        self["processed_data"] = cell_preprocessor.preprocess(self["processed_data"])
        self["maxHeight"] = max(self["processed_data"])
        self["signalMean"] = np.mean(self["processed_data"])
        
    def append_gradient_data(self):
        if "processed_data" in self.keys():
            self["gradient_data"] = self["processed_data"].copy()
            self["gradient_data"] = np.gradient(ss.savgol_filter(self["gradient_data"],101,2))
        else:
            self["gradient_data"] = self["Raw_Data"]["MEAN_INTENSITY_CH1"].copy()
            self["gradient_data"] = np.gradient(ss.savgol_filter(self["gradient_data"],101,2))
            
    def detect_peaks(self, cell_peakprocessor, cell_gradpeakprocessor, append = True):
        temp_peaks_df = cell_peakprocessor.processPeaks(self["processed_data"].tolist())
        temp_gradpeaks_df = cell_gradpeakprocessor.processPeaks(self["gradient_data"].tolist())
        
        if not temp_peaks_df is None and not temp_gradpeaks_df is None:
            temp_peaks_df = Peakprocessor.matcher.match_peaks(temp_peaks_df, temp_gradpeaks_df, self["processed_data"]) #leaving only peaks that have corresponding zero points in gradient peak analysis
            #temp_peaks_df = cell_peakprocessor.secFilter(temp_peaks_df)
            
        if temp_gradpeaks_df is None:
            temp_peaks_df = None
            
        if append:
            
            self["peaks"] = temp_peaks_df
            self["gradpeaks"] = temp_gradpeaks_df
            
            if not temp_peaks_df is None:
                self["peakcount"] = len(temp_peaks_df)
                self["multipeak"] = len(temp_peaks_df) > 1
                self["haspeak"] = len(temp_peaks_df) > 0
                
            else:
                self["peakcount"] = 0
                self["multipeak"] = False
                self["haspeak"] = False
        else: 
            if not temp_peaks_df is None:
                return(temp_peaks_df)
    def get_Data(self):
        return self["Data"]
    
    def set_filter_status(self, status):
        self["in_filter"] = status
        
    def calculateMovement(self):
        xs = self["Raw_Data"]["POSITION_X"].values
        ys = self["Raw_Data"]["POSITION_Y"].values
        distSum = 0
        for i in range(len(xs)-1):
            dist = np.sqrt((xs[i]-xs[i+1])**2 + (ys[i]-ys[i+1])**2)
            distSum += dist
        return distSum
        
class Cell_Item(QTreeWidgetItem):
    def __init__(self, parent_cell):
        super().__init__()
        self.parent_cell = parent_cell
    
    def get_Cell(self):
        return self.parent_cell