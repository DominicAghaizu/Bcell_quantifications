# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QDialog, QTreeWidgetItem, QFileDialog
from PyQt5.uic import loadUi

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import (NavigationToolbar2QT as NavigationToolbar)
from modules import Preprocessor
from modules import Cell
import numpy as np
import pandas as pd

class Representative_Dialog(QDialog):
    
    def __init__(self, cells):
        
        super(Representative_Dialog, self).__init__()
        loadUi("PyQT5_UI-Files/representative_dialog.ui",self)
        self.plotIndex = 0
        self.currentlyPlotted = None
        self.keyReference = None
        self.showMean = False
        self.cells = cells #a dictionary filled with lists of cell_dicts
        self.initiateMainGraph()
        self.orderedData = None
        self.axs = self.MplWidget_rep.canvas.axes
        self.createOrderedData()
        self.treeWidget_refCellTree.itemClicked.connect(self.handleTreeSelection)
        self.pushButton_forward.clicked.connect(self.forward)
        self.pushButton_backward.clicked.connect(self.backward)
        self.pushButton_refShowMean.clicked.connect(self.toggleMean)
        self.pushButton_exportTrackData.clicked.connect(self.handleExportTrack)
        self.updateMainFrame()
        self.maxIndex = len(self.orderedData)-1
        
        
        
    def calculateCellMean(self):
        datalist = []
        for key in self.cells.keys():
            for cell in self.cells[key]:
                datalist.append(cell["processed_data"])
        dataDf = pd.DataFrame(datalist)
        meanData = dataDf.mean()
        return meanData
    
    def writeToFileList(self):
        self.textEdit_refFiles.setText("\n".join([str(self.keyReference[key]) + ": " +str(key) for key in self.keyReference.keys()]))
        
    def initiateMainGraph(self):
        self.MplWidget_rep.canvas.axes = self.MplWidget_rep.canvas.figure.add_subplot(111)
        self.MplWidget_rep.canvas.axes.clear()

        self.MplWidget_rep.canvas.figure.set_facecolor("#19232d")
        self.MplWidget_rep.canvas.axes.set_facecolor("#19232d")
        self.MplWidget_rep.canvas.figure.set_edgecolor("white")
        self.MplWidget_rep.canvas.axes.tick_params(colors='white', which='both')
        
        self.MplWidget_rep.canvas.draw()
        
    def createOrderedData(self):
        tempCells = []
        meanData = self.calculateCellMean()
        self.meanData = meanData
        for key in self.cells.keys():
            for cell in self.cells[key]:
                cellData = (cell["processed_data"])
                stdData = [(a-b)**2 for a,b in zip(cellData, meanData)]
                meanStd = np.mean(stdData)
                cellDictEntry = {"cell": cell, "oldKey":key, "meanStd": meanStd}
                tempCells.append(cellDictEntry)
        self.keyReference =  {}
        for ind, key in enumerate(self.cells.keys()):
           self.keyReference[key] = ind
        
        tempDataFrame = pd.DataFrame(tempCells)
        
        
        tempDataFrame.sort_values(by="meanStd", ascending= False) 
        for indx, row in tempDataFrame.iterrows():
            cellTreeItem = QTreeWidgetItem()
            cell = row["cell"]
            cellTreeItem.setData(1,0,str(cell["Track"]))
            cellTreeItem.setData(0,0,self.keyReference[row["oldKey"]])
            cellTreeItem.setData(2,0,str(cell["tracklength"]))
            cellTreeItem.setData(3,0,row["meanStd"])
            cellTreeItem.cell = cell
            self.treeWidget_refCellTree.addTopLevelItem(cellTreeItem)
            self.treeWidget_refCellTree.sortItems(3, 0)
            self.treeWidget_refCellTree.setCurrentItem(self.treeWidget_refCellTree.topLevelItem(0))
        self.orderedData = tempDataFrame
        self.writeToFileList()
    
    def handleTreeSelection(self, item, column):
        index = self.treeWidget_refCellTree.indexOfTopLevelItem(item)
        self.plotIndex = index
        self.updateMainFrame()
        
    def updateMainFrame(self):
         
         self.axs.clear()
         self.axs.set_xlabel("time [s]")
         self.axs.set_ylabel("norm. intensity [fold change]")
         selectedItem = self.treeWidget_refCellTree.topLevelItem(self.plotIndex)
         self.treeWidget_refCellTree.setCurrentItem(selectedItem)
         self.axs.plot(selectedItem.cell["processed_data"], color = "white")
         self.currentlyPlotted = selectedItem.cell["processed_data"]
         self.axs.get_figure().suptitle("File: "+ selectedItem.cell["Path"] + "\n" + "Track: " + str(selectedItem.cell["Track"]) + "\n" + "Std: " + str(selectedItem.data(3,0)), color = "white")
         if self.showMean:
             self.axs.plot(self.meanData, "--", color = "white")
         self.MplWidget_rep.canvas.draw()
        
    def toggleMean(self):
        self.showMean = not self.showMean
        self.updateMainFrame()
         
    def forward(self):
        if self.plotIndex == self.maxIndex:
            index = 0
        else:
            index = self.plotIndex+1
        self.plotIndex = index
        self.updateMainFrame()
        
    def backward(self):
        if self.plotIndex == 0:
            index = self.maxIndex
        else:
            index = self.plotIndex-1
        self.plotIndex = index
        self.updateMainFrame()
            
    def handleExportTrack(self):
        if self.currentlyPlotted is not None:
            dlg = QFileDialog(defaultSuffix = ".csv")
            dlg.setAcceptMode(QFileDialog.AcceptSave)
            if dlg.exec_():
                savePath = dlg.selectedFiles()[0]
                saveList = []
                for i, dat in enumerate(self.currentlyPlotted):
                    saveList.append({"Frame": i+1, "fold change": dat})
                exportFrame = pd.DataFrame(saveList)
                exportFrame.to_csv(savePath, sep = ";", index = False)
    
                
        
        
                
    
        
    

        