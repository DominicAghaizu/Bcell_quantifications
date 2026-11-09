# -*- coding: utf-8 -*-
"""
Created on Fri Jan 13 14:48:17 2023

@author: Willi
"""
import scipy.signal as ss
import copy
import numpy as np

class Preprocessor():
    
    def __init__(self):
        
        self.smoothing_bool = True
        self.smoothing_window = 41
        self.smoothing_poly = 2
        self.crop_start = 0
        self.crop_end = 0
        self.normalize_bool = True
        self.autoCutFirst = False
        
    def preprocess(self, data, return_seperate = False ):
        temp_data = copy.deepcopy(data)
        
        tempSmoothedGradData = np.gradient(ss.savgol_filter(temp_data[:100], 21, 2))
        
        if self.crop_start == 0 and self.autoCutFirst:
            autoCropIndex = next((x[0] for x in enumerate(tempSmoothedGradData) if x[1] <= 0), 100)
            crop_start = autoCropIndex
        else:
            crop_start = self.crop_start
        if crop_start > 0:
            temp_data = temp_data[crop_start:]
        if self.crop_end > 0:
            temp_data = temp_data[:-self.crop_end]
            
        if self.normalize_bool:
            mini = temp_data[crop_start]
            temp_data = [(frame/mini) for frame in temp_data]
        
        if self.smoothing_bool:
            smoothed_data = ss.savgol_filter(temp_data, self.smoothing_window, self.smoothing_poly)
            work_data = smoothed_data
        else: work_data = temp_data
        
        
        if return_seperate:
            norm_return = copy.deepcopy(temp_data)
            
        if return_seperate:
            return norm_return, work_data
        else:
            return work_data
    
    def set_config(self, config_data):
        self.smoothing_bool = bool(config_data["smoothing_bool"])
        self.smoothing_window = int(config_data["smoothing_window"])
        self.smoothing_poly = int(config_data["smoothing_poly"])
        self.crop_start = int(config_data["crop_start"])
        self.crop_end = int(config_data["crop_end"])
        self.normalize_bool = bool(config_data["normalize_bool"])
        self.autoCutFirst = bool(config_data["autoCutFirst"])
        
    def get_config(self):
        save_dict = {
            "smoothing_window" :self.smoothing_window,
            "smoothing_bool": self.smoothing_bool,
            "smoothing_poly": self.smoothing_poly,
            "crop_start": self.crop_start,
            "crop_end": self.crop_end,
            "normalize_bool": self.normalize_bool,
            "autoCutFirst": self.autoCutFirst}
        
        return save_dict
        
        