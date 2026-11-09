# -*- coding: utf-8 -*-
"""
Created on Wed Jan 11 16:23:07 2023

@author: Willi
"""

import pandas as pd

import numpy as np
from modules import Cell
import copy
from PyQt5.QtWidgets import*
from PyQt5.QtCore import Qt
import time


class Datahandler:
    
    def __init__(self):
        
        self.imported_data = {}
        self.raw_data = {}
        self.work_data = {}
        self.config = pd.DataFrame()
        self.UItopLevelItems = None
        self.FileListItems = []
        self.work_data = {}
        
    def import_files(self, paths, progressbar):
        total_paths = len(paths)
        
        
        for path_index, path in enumerate(paths):
            start = time.time()
            loadColumns = ["TRACK_ID", "FRAME", "MEAN_INTENSITY_CH1", "POSITION_X", "POSITION_Y"]
            temp_data = pd.read_csv(path, sep = ",", usecols = loadColumns,  engine='pyarrow').drop([0,1,2])
            temp_data = temp_data.astype({"TRACK_ID": np.uint16, "FRAME": np.uint16, "MEAN_INTENSITY_CH1": np.float64,"POSITION_X": np.float64, "POSITION_Y":np.float64})
            time1 = time.time()-start
            path_alias = path.split("/")[-1].replace(".csv","")
            cell_data = [Cell.Cell_Dict({"Path": path_alias,"Track": track, "Raw_Data":temp_data[temp_data["TRACK_ID"] == track].sort_values(by = "FRAME")[["MEAN_INTENSITY_CH1","POSITION_X", "POSITION_Y"]].reset_index()}) for track in temp_data["TRACK_ID"].unique()]
            
            path_item = cFile()
            path_item.setText(0,path_alias)
            path_item.setText(1,str(len(cell_data)))
            path_item.setCells(cell_data)
            
            self.FileListItems.append(path_item)
        
            self.imported_data[path_alias] = temp_data
            
            self.raw_data[path_alias] = cell_data
            
            
            path_index = path_index + 1
            progressbar.setValue(int((path_index/total_paths)*100))
            time2 = time.time()-start
            
            print(time1)
            print(time2)
        progressbar.setValue(int(0)) 
        self.filter_workdata()
    
    
    def filter_workdata(self):
        
        for key in self.raw_data.keys():
            self.work_data[key] = self.raw_data[key].copy()
            
        for key in self.work_data.keys():
            for cell in self.work_data[key]:
                
                if not cell["in_filter"]:
                    self.work_data[key].remove(cell)
                    
                
    def get_globalmax(self):
        
        maxs = [max(cell["processed_data"]) for key in self.work_data.keys() for cell in self.work_data[key]]
        return max(maxs)
    
    def get_globalmaxMean(self):
        
        maxs = [max(cell["processed_data"]) for key in self.work_data.keys() for cell in self.work_data[key]]
        return np.mean(maxs)
    
    def get_globalmaxLen(self):
        
        lens = [len(cell["processed_data"]) for key in self.work_data.keys() for cell in self.work_data[key]]
        return min(lens)
    
    
    def get_gradmax_list(self):
        grads = [max(cell["gradient_data"]) for key in self.work_data.keys() for cell in self.work_data[key]]
        return grads
    
    def get_peakmax_list(self):
        maxs = [max(cell["processed_data"]) for key in self.work_data.keys() for cell in self.work_data[key]]
        return maxs
    
    def get_combiscore_list(self, peakProcessor, gradPeakProcessor):
       
        cellPeaks = [cell.detect_peaks(peakProcessor, gradPeakProcessor, append = False) for key in self.work_data.keys() for cell in self.work_data[key]]
        print(type(cellPeaks))
        print(type(cellPeaks[0]))
        cellPeaks = [entry for entry in cellPeaks if not entry is None]
        maxCellPeaks = [cellPeakList.loc[cellPeakList["combi_score_2"].idxmax()] for cellPeakList in cellPeaks]
        cellPeakDf = pd.concat(maxCellPeaks)
        data = cellPeakDf["combi_score_2"].tolist()
        
        return data
        
    
    
    
class cFileGroup(QTreeWidgetItem):
    
    def __init__(self, *args):
        super().__init__(*args)
        self.fileItems = None
        self.plotColor = "#FFFFFF"
        self.setFlags(self.flags() | Qt.ItemIsTristate | Qt.ItemFlag.ItemIsUserCheckable)
        self.setCheckState(0, Qt.CheckState.Checked)
        self.hasPeakData = False
        self.n_noPeak = None
        self.n_onePeak = None
        self.n_multiPeak = None
        
    def isGroup(self):
        return True
    def getActiveState(self):
        return (self.checkState(0) > 0)
            
    def setfileItems(self, fileItems):
        self.fileItems = fileItems
        for fileItem in fileItems:
            fileItem.FileGroup = self
    
    def getCells(self, peakStatusFilter = None):
        if self.fileItems == None:
            return []
        else: 
            return [cell for file in self.fileItems for cell in file.getCells(peakStatusFilter)]
    
    def setPlotColor(self, color):
        self.plotColor = color
        for file in self.fileItems:
            file.setPlotColor(color)
        
    def updatePeakDisplayStats(self):
        
        noPeak = 0
        onePeak = 0
        multiPeak = 0
        for item in self.fileItems:
            itemC = item.cells
            tempframe = pd.DataFrame(itemC)
            item_noPeak = len(tempframe[tempframe["peakcount"] == 0])
            item_onePeak = len(tempframe[tempframe["peakcount"] == 1])
            item_multiPeak = len(tempframe[tempframe["peakcount"] > 1])
            noPeak = noPeak + item_noPeak
            onePeak = onePeak + item_onePeak
            multiPeak = multiPeak + item_multiPeak
        self.n_noPeak = noPeak
        self.n_onePeak = onePeak
        self.n_multiPeak = multiPeak
        self.hasPeakData = True
        
    def getFilePeakStats(self):
        
        try:
            nps = []
            mps = []
            ops = []
            mpOp = []
            lens =[]
            for item in self.fileItems:
                itemC = item.cells
                tempframe = pd.DataFrame(itemC)
                frameLength = len(tempframe)
                nps.append(len(tempframe[tempframe["haspeak"] == False])/frameLength)
                mps.append(len(tempframe[tempframe["multipeak"] == True])/frameLength)
                ops.append(len(tempframe[tempframe["peakcount"] == 1])/frameLength)
                mpOp.append(len(tempframe[tempframe["haspeak"] == True])/frameLength)
                lens.append(frameLength)
            
            overallLength = sum(lens)
            weights = [l/overallLength for l in lens]
            print(weights)
            print(nps)
            npeak,npStd = self.weightedAvgStd(nps, weights = weights)
            mpeak,mpStd = self.weightedAvgStd(mps,weights = weights)
            opeak,opStd = self.weightedAvgStd(ops,weights = weights)
            gpeak,gStd = self.weightedAvgStd(mpOp,weights = weights)
            
            
            #data = {"path_alias": self.text(0),"multiPeakCount": mpeak,"onePeakCount": opeak }
            #errors = {"path_alias": self.text(0),"multiPeakCount": mpStd,"onePeakCount": opStd, "hasPeak":gStd}
            
            data = {"path_alias": self.text(0),"hasPeak": gpeak}
            errors = {"path_alias": self.text(0),"hasPeak": gStd}
            
            return([data, errors])
                
        except NameError:
            print("No Items have been appended to cFileGroup")
    
    def weightedAvgStd(self, arr, weights):

        avg = np.average(arr, weights = weights)
        var = np.average((arr-avg)**2, weights=weights)
        stdev = np.sqrt(var)
        return(avg, stdev)
    
    def getFilePeakStatsRaw(self):
        
        try:
            dataDicts = []
            for item in self.fileItems:
                tempDict = item.getFilePeakStatsRaw(asList = False)
                tempDict["Group"] = self.text(0)
                dataDicts.append(tempDict)
            return(dataDicts)
                
        except NameError:
            print("No Items have been appended to cFileGroup")
    def getClusterStats(self):
        data = {"path_alias": self.text(0)}
        errors = {"path_alias": self.text(0)}
        clusterData = {}
        for item in self.fileItems:
            cells = item.getCells()
            tempframe = pd.DataFrame(cells)
            for name, group in tempframe.groupby("cluster"):
                if name in clusterData.keys():
                    clusterData[name].append(len(group)/len(tempframe))
                else: 
                    clusterData[name] = [len(group)/len(tempframe)]
                
        for key in clusterData.keys():
            mean = np.mean(clusterData[key])
            sdev = np.std(clusterData[key])
            data[key] = mean
            errors[key] = sdev
            
        return([data,errors])
                
                
    @staticmethod
    def createGroupName(filePaths, delimiter = "_"):
        pathComponents = [path.split(delimiter) for path in filePaths]
        groupName = pathComponents[0]
        for path in pathComponents:
            groupName = [gN_n for gN_n in groupName if gN_n in path]

        return delimiter.join(groupName)
        
class cFile(QTreeWidgetItem):
    
    def __init__(self, *args):
        super().__init__(*args)
        self.hasPeakData = False
        self.plotColor = "#FFFFFF"
        self.group = None
        self.setFlags(self.flags() | Qt.ItemIsUserCheckable)
        self.setCheckState(0, Qt.CheckState.Checked)
        self.fileItems = [self]
        self.hasPeakData = False
        self.n_noPeak = None
        self.n_onePeak = None
        self.n_multiPeak = None
      
    def isGroup(self):
        return False
    
    def setCells(self, cells):
        self.cells = cells
    
    def getActiveState(self):
        print("CheckState")
        print(self.checkState(0))
        return (self.checkState(0) > 0)
    
    def getCells(self, peakStatusFilter = None):
        if peakStatusFilter is None:
            return [cell for cell in self.cells if cell["in_filter"]]
        else:
            return [cell for cell in self.cells if cell["in_filter"] and 
                    ((peakStatusFilter["noPeak"] and not cell["haspeak"]) or
                    (peakStatusFilter["onePeak"] and cell["haspeak"] and not cell["multipeak"]) or
                    (peakStatusFilter["multiPeak"] and cell["multipeak"]))]
        
    def setPlotColor(self, color):
        self.plotColor = color
        cells = self.getCells()
        for cell in cells: cell["plotColor"] = color
        
    
    def updatePeakDisplayStats(self):
        tempframe = pd.DataFrame(self.cells)
        self.n_noPeak = len(tempframe[tempframe["peakcount"] == 0])
        self.n_onePeak = len(tempframe[tempframe["peakcount"] == 1])
        self.n_multiPeak = len(tempframe[tempframe["peakcount"] > 1])
        self.hasPeakData = True
    
        
    def getFilePeakStats(self):
    
        try:
            tempframe = pd.DataFrame(self.cells)
            npeak = len(tempframe[tempframe["haspeak"] == False])/len(tempframe)
            mpeak = len(tempframe[tempframe["multipeak"] == True])/len(tempframe)
            opeak = len(tempframe[tempframe["peakcount"] == 1])/len(tempframe)
            gpeak = len(tempframe[tempframe["haspeak"] == True])/len(tempframe)
        
            npStd = 0
            mpStd = 0
            opStd = 0
            gStd = 0
            data = {"path_alias": self.text(0),"multiPeakCount": mpeak,"onePeakCount": opeak}
            errors = {"path_alias": self.text(0),"multiPeakCount": mpStd,"onePeakCount": opStd, "hasPeak":gStd}
            return([data, errors])
        
        except NameError:
            print("No Cells have been appended to cFile")
    
    def getFilePeakStatsRaw(self, asList = True):
        
        
        try:
            tempframe = pd.DataFrame(self.cells)
            npeak = len(tempframe[tempframe["haspeak"] == False])
            mpeak = len(tempframe[tempframe["multipeak"] == True])
            opeak = len(tempframe[tempframe["peakcount"] == 1])
            gpeak = len(tempframe[tempframe["haspeak"] == True])

            data = {"Group": "None", "path_alias": self.text(0),"hasPeaks": gpeak, "noPeak": npeak, "multiPeak": mpeak, "onePeak":opeak  }
            if asList:
                return([data])
            else:
                return(data)
        
        except NameError:
            print("No Cells have been appended to cFile")
            
    def getClusterStats(self):
        data = {"path_alias": self.text(0)}
        errors = {"path_alias": self.text(0)}
        clusterData = {}
        for item in self.fileItems:
            cells = item.getCells()
            tempframe = pd.DataFrame(cells)
            for name, group in tempframe.groupby("cluster"):
                if name in clusterData.keys():
                    clusterData[name].append(len(group)/len(tempframe))
                else: 
                    clusterData[name] = [len(group)/len(tempframe)]
                
        for key in clusterData.keys():
            mean = np.mean(clusterData[key])
            sdev = np.std(clusterData[key])
            data[key] = mean
            errors[key] = sdev
            
        return([data,errors])