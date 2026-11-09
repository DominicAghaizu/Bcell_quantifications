# -*- coding: utf-8 -*-
"""
Created on Fri Jan 20 15:48:49 2023

@author: Willi
"""

import scipy.signal as ssignal
import copy
import numpy as np
import pandas as pd

class Peakprocessor():
    
    def __init__(self):
        
        self.th_m = 1
        self.decay_th = 0.5
        self.peak_width = 1
        self.combiTh = 0

        
    def processPeaks(self, data):
        temp_data = copy.deepcopy(data)
        return_df = None
        dicts_for_df = []
        
        peaks = ssignal.find_peaks(temp_data, width = self.peak_width)
        
        if len(peaks[0]):
            temp_peaks = []
            for i in peaks[0]: #iterating over indices of found peaks
                
                t_min = np.min(temp_data) #finding minimum of fluorescence signal in time series
                t_max = np.max(temp_data) #finding maximum of fluorescence signal in time series
                """
                if temp_data[i] > (((t_max - t_min)/2 + t_min)*self.th_m): #threshholding witgh dynamic range of the signal range. Standard peak exclusion factor: 0.5 x signal range
                    temp_peaks.append(i)
                """
                
                if temp_data[i] > self.th_m: #threshholding with fixed height value
                    temp_peaks.append(i)
                    
                    
            if len(temp_peaks):
                #getting data from prominence calculations: prominences, left bottom frame of peak, right bottom frame of peak
                prom_arr = ssignal.peak_prominences(temp_data, temp_peaks)
                proms = prom_arr[0]
                left_bs = prom_arr[1]
                right_bs = prom_arr[2]
                
                #transfering frame to values and calculating new prominences using only left or right slope, important because our peaks are often not symmetric
                #also symmetry is an important factor to distinguish between spikey peaks and peaks that are followed by plateus 
                
                for peak_index in range(len(temp_peaks)):
                    left_frame = left_bs[peak_index]
                    left_value = temp_data[left_frame]
                    
                    right_frame = right_bs[peak_index]
                    right_value = temp_data[right_frame]
                    
                    center_frame = temp_peaks[peak_index]
                    center_value = temp_data[center_frame]
                    
                    left_dif = center_value - left_value
                    right_dif = center_value - right_value
                    t_prom_mean = (left_dif + right_dif)/2
                    t_prom_std = (left_dif - right_dif)**2
                    
                    
                    
                    #decay calculation
                    pmax_decay_th = center_value * self.decay_th
                    list_da = list(temp_data)
                    decayed = True
                    decayed_frame = next((list_da.index(point) for point in list_da[center_frame:] if point <= center_value - pmax_decay_th),len(temp_data))
                    if decayed_frame == len(temp_data): decayed = False
                    decay_dur = decayed_frame - center_frame
                    
                    
                    peak_temp_dict = {"left_frame" : left_frame,
                                      "left_value": left_value,
                                      "right_frame": right_frame,
                                      "right_value": right_value,
                                      "center_frame" : center_frame,
                                      "center_value": center_value,
                                      "left_diff" : left_dif,
                                      "right_diff": right_dif,
                                      "t_prom_mean" :t_prom_mean,
                                      "t_prom_std" : t_prom_std,
                                      "decayed": decayed,
                                      "decay_dur": decay_dur,
                                      "combi_score": 0.0,
                                      "combi_score_2": 0.0,
                                      "left_diff_grad":0.0
                                      }
                    dicts_for_df.append(peak_temp_dict)
        
        if len(dicts_for_df) > 0:            
           return_df = pd.DataFrame(dicts_for_df)
        
        return(return_df)

    def secFilter(self, df):
        
        returnDf = df[df["left_diff_grad"].gt(self.th_m)]
        if returnDf.empty:
            returnDf = None
        return returnDf
        
    
    def set_config(self, config_data):
        
        self.th_m = float(config_data["threshold_ratio_mean"])
        self.decay_th = float(config_data["threshold_ratio_decay"])
        #self.peak_width = float(config_data["peak_width"])
        self.combiTh = float(config_data["threshold_combi_score"])
        
    def get_config(self):
        save_dict = {
            "peak_width": self.peak_width,
            "threshold_ratio_mean" :self.th_m ,
            "threshold_ratio_decay": self.decay_th,
            "threshold_combi_score": self.combiTh}
            
        
        return save_dict
    
    
    
    
    
class Gradpeak_Processor():
    def __init__(self):
        
        self.th_m = 1
        self.edge_ratio = 0.8


        
    def processPeaks(self, data):
        temp_data = copy.deepcopy(data)
        return_df = None
        dicts_for_df = []
        peaks = ssignal.find_peaks(temp_data,prominence = self.th_m/2)
        
        if len(peaks[0]):
            temp_peaks = []
            for i in peaks[0]: #iterating over indices of found peaks
                
                
                if temp_data[i] > self.th_m: 
                    temp_peaks.append(i)
                    
            if len(temp_peaks):
                #getting data from prominence calculations: prominences, left bottom frame of peak, right bottom frame of peak
                prom_arr = ssignal.peak_prominences(temp_data, temp_peaks)
                proms = prom_arr[0]
                left_bs = prom_arr[1]
                right_bs = prom_arr[2]
                
                #transfering frame to values and calculating new prominences using only left or right slope, important because our peaks are often not symmetric
                #also symmetrie is an important factor to distinguish between spikey peaks and peaks that are followed by plateus 
                
                for peak_index in range(len(temp_peaks)):
                    left_frame = left_bs[peak_index]
                    left_value = temp_data[left_frame]
                    
                    right_frame = right_bs[peak_index]
                    right_value = temp_data[right_frame]
                    
                    center_frame = temp_peaks[peak_index]
                    center_value = temp_data[center_frame]
                    
                    left_dif = center_value - left_value
                    right_dif = center_value - right_value
                    t_prom_mean = (left_dif + right_dif)/2
                    t_prom_std = (left_dif - right_dif)**2
                    
                    
                    
                    #find next 0 value to the right of the peak
                    subdata = temp_data[center_frame:]
                    passzero_index = next((p_index for p_index in range(len(subdata)) if subdata[p_index-1] > 0 and subdata[p_index] <= 0), False) + center_frame                     
                    
                    
                    
                    peak_temp_dict = {"left_frame" : left_frame,
                                      "left_value": left_value,
                                      "right_frame": right_frame,
                                      "right_value": right_value,
                                      "center_frame" : center_frame,
                                      "center_value": center_value,
                                      "left_diff" : left_dif,
                                      "right_diff": right_dif,
                                      "t_prom_mean" :t_prom_mean,
                                      "t_prom_std" : t_prom_std,
                                      "passzero_index": passzero_index
                                      }
                    dicts_for_df.append(peak_temp_dict)
        
        if len(dicts_for_df) > 0:            
           return_df = pd.DataFrame(dicts_for_df)
        
        return(return_df)

        
    
    def set_config(self, config_data):
        self.th_m = float(config_data["grad_edge_threshold"])
        self.edge_ratio = float(config_data["grad_edge_ratio"])
        
        
    def get_config(self):
        save_dict = {
            "grad_edge_threshold" :self.th_m ,
            "grad_edge_ratio" : self.edge_ratio,
            }
        
        return save_dict


class matcher():
    
   
    @staticmethod
    def match_peaks(peakdata, gradpeakdata, cellProcessedData):
        #peaks_from_gradzeros = gradpeakdata["passzero_index"].unique().tolist()
        #print(peaks_from_gradzeros)
        peaks_from_data = peakdata["center_frame"].tolist()
        mask = [False for p in peaks_from_data]
        
        #groups gradient peaks by their passzero index and only returns the one at the beginning/with earlyest starting frame
        gradpeakdataUnique = gradpeakdata.loc[gradpeakdata.groupby('passzero_index')['left_frame'].idxmin()] 
        
        for index, gradpeak in gradpeakdataUnique.iterrows():
            gradpeak_frame = gradpeak["passzero_index"]
            mindistpeak = np.argmin([(gradpeak_frame-peak_frame)**2 for peak_frame in peaks_from_data])
            #peakdata.iloc[int(mindistpeak)]["center_value"]-cellProcessedData[int(gradpeak["left_frame"])]
            peakdata.iloc[mindistpeak, peakdata.columns.get_loc("left_diff_grad")] = peakdata.iloc[int(mindistpeak)]["center_value"]-cellProcessedData[int(gradpeak["left_frame"])]
            peakdata.iloc[mindistpeak, peakdata.columns.get_loc("combi_score_2")] =  peakdata.iloc[int(mindistpeak)]["left_diff_grad"]*gradpeakdata.iloc[int(index)]["center_value"]
            peakdata.iloc[mindistpeak, peakdata.columns.get_loc("combi_score")] =  peakdata.iloc[int(mindistpeak)]["left_diff"]*gradpeakdata.iloc[int(index)]["center_value"]
            mask[mindistpeak] = True
        
        """                        
        for peak_frame in peakdata["center_frame"].tolist():
            if peak_frame > 0:
                
                mask.append(next((True for p in range(0,11) if peak_frame-+p in peaks_from_gradzeros), False))
            else: 
                mask.append(next((True for p in range(0,2) if peak_frame+p in peaks_from_gradzeros), False))
        """
        #print(mask)
        matching_peaks = peakdata[mask]
        
        return matching_peaks
        
class peakFilter():
    
    @staticmethod
    def filter_peaks(peakdata, filterDict):
        
        print("maspd")
    