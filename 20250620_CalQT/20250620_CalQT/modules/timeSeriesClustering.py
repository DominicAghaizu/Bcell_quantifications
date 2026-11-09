# -*- coding: utf-8 -*-
"""
Created on Mon Jul 15 15:44:50 2024

@author: Willi
"""

from tslearn.utils import to_time_series_dataset, to_time_series
from tslearn.clustering import TimeSeriesKMeans

class tsClustering():
    
    def __init__(self, data, nMeans = 2, crop = True, cropLength = 900, keys = "all", metric = "euclidean"):
        
        self.n = nMeans
        self.data = data
        self.model = None
        self.crop = crop
        self.cropLength = cropLength
        self.keys = keys
        self.transformedData = None
        self.metric = metric
        
        
        
    def transformForTs(self):
        data = self.data
        if self.keys == "all":
            tempKeys = data.keys()
        else:
            tempKeys = self.keys
        if self.crop:
            dataList = [dat["processed_data"][0:self.cropLength] for key in tempKeys for dat in data[key] if len(dat["processed_data"]) >= self.cropLength]
        else:
            dataList = [dat["processed_data"] for key in tempKeys for dat in data[key]]
        self.transformedData = to_time_series_dataset(dataList)
    
    def setModel(self):
        
        self.model = TimeSeriesKMeans(n_clusters=self.n, metric=self.metric, n_jobs = -1).fit(self.transformedData)

    def getLabels(self, singleData):
        labels = self.model.predict(singleData)
        return labels
    
    def appendLabelsToCells(self, cellData):
        if cellData is dict:
            dataList = [dat for key in cellData.keys() for dat in cellData[key]]
        else:
            dataList = [dat for dat in cellData]
            
        for dat in dataList:
            dat["tsGroup"] = self.model.predict(to_time_series(dat["processed_data"]))
            
    def appendLabelToCell(self, cell):
            cell["cluster"] = self.model.predict(to_time_series(cell["processed_data"]))
            
    def getClusterCenters(self):
        return self.model.cluster_centers_
        
        
    
    
    

    