# -*- coding: utf-8 -*-
"""
Created on Fri Apr 28 16:59:20 2023

@author: Willi
"""
from PyQt5.QtWidgets import*
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.widgets import SpanSelector
import matplotlib.colors as mcolors
from modules import selectorFactory
from modules.Datahandler import cFileGroup


class DataStatisticsHandler:
    
    def __init__(self, datahandler, MplWidgetObj_Datastats, plotUI, selectorButtonUI, MplWidgetObj_GateResults):
        self.datahandler = datahandler
        self.MplWidgetObj = MplWidgetObj_Datastats
        self.MplWidgetObj_Gateresults = MplWidgetObj_GateResults
        self.plotUI = plotUI
        
        self.plotUI["StatsAppend"].clicked.connect(self.updateMplCanvas)
        
        self.UISelectorFactory = selectorFactory.selectorFactory(selectorButtonUI, self)
        self.initiateMplCanvas()
        self.initiateMplCanvas_GateResults()
        self.connectUI()
        
        self.cellData = None
        self.cellDataList = []
        self.optionsadded = False
        self.selectedAxes = None
        
        self.sampleSelectionData = None
        
    def initiateMplCanvas(self):
        print("hi")
        self.MplWidgetObj.canvas.axes = self.MplWidgetObj.canvas.figure.subplots(2,2)
        
        self.MplWidgetObj.canvas.figure.set_facecolor("#19232d")
        self.MplWidgetObj.canvas.figure.set_edgecolor("white")
        self.MplWidgetObj.canvas.figure.subplots_adjust(top = 0.99, bottom=0.1, hspace=0.4, wspace=0.4)
        self.axes = self.MplWidgetObj.canvas.axes
        
        for ax_x in self.axes:
            for ax in ax_x:
                ax.set_facecolor("#19232d")
                ax.tick_params(colors='white', which='both')
                
                ax.activeSelector = None
        
        #self.MplWidgetObj.canvas.mpl_connect('button_release_event', self.handleAxClicked)
        self.MplWidgetObj.canvas.mpl_connect('axes_enter_event', self.handleAxEntered)
        self.MplWidgetObj.canvas.draw()
        
    def initiateMplCanvas_GateResults(self):
        
        print("hi")
        self.MplWidgetObj_Gateresults.canvas.axes = self.MplWidgetObj_Gateresults.canvas.figure.subplots(1,1)
        
        self.MplWidgetObj_Gateresults.canvas.figure.set_facecolor("#19232d")
        self.MplWidgetObj_Gateresults.canvas.figure.set_edgecolor("white")
        self.MplWidgetObj_Gateresults.canvas.figure.subplots_adjust(top = 0.99, bottom=0.2, hspace=0.5, wspace=0.5)
        self.GateResults_axes = self.MplWidgetObj_Gateresults.canvas.axes
        print(self.GateResults_axes)
      
        self.GateResults_axes.set_facecolor("#19232d")
        self.GateResults_axes.tick_params(colors='white', which='both')
                
                
        #self.MplWidgetObj.canvas.mpl_connect('button_release_event', self.handleAxClicked)
        
        self.MplWidgetObj_Gateresults.canvas.draw()
        
        
    def updateMplCanvas(self):
    
        self.files = self.datahandler.FileListItems
        self.cellDataList = []
        for file in self.files:
            if file.getActiveState():
                fileCells = file.getCells()
                for cell in fileCells:
                    if cell["haspeak"]:
                        firstPeakSeries = cell["peaks"].iloc[0]
                        toAppendSeries = pd.Series({"File": file, "hasPeak": True, "Cell": cell, "plotColor": cell["plotColor"], "distanceTraveled": cell["distanceTraveled"],"maxHeight": cell["maxHeight"],"signalMean": cell["signalMean"]})
                        
                        firstPeakSeries = pd.concat([firstPeakSeries,toAppendSeries])
                        
                        self.cellDataList.append(firstPeakSeries)
                    else:
                        toAppendSeries = pd.Series({"File": file, "hasPeak": False, "Cell": cell, "plotColor": cell["plotColor"], "distanceTraveled": cell["distanceTraveled"],"maxHeight": cell["maxHeight"], "signalMean": cell["signalMean"]})
                        self.cellDataList.append(toAppendSeries)
                        
        if len(self.cellDataList) > 0:             
            self.cellData = pd.DataFrame(self.cellDataList)
            
            for g in self.graphObjects:
                g.handleAxContent()      
            self.MplWidgetObj.canvas.draw()
    
    def connectUI(self):
        
        self.g1 = subStatsGraph(self.axes[0,0], self, self.plotUI["Stats1x"],self.plotUI["Stats1y"], self.plotUI["plotAllg1"], self.plotUI["textLabelg1"])
        self.g2 = subStatsGraph(self.axes[0,1], self, self.plotUI["Stats2x"],self.plotUI["Stats2y"], self.plotUI["plotAllg2"], self.plotUI["textLabelg2"])
        self.g3 = subStatsGraph(self.axes[1,0], self, self.plotUI["Stats3x"],self.plotUI["Stats3y"], self.plotUI["plotAllg3"], self.plotUI["textLabelg3"])
        self.g4 = subStatsGraph(self.axes[1,1], self, self.plotUI["Stats4x"],self.plotUI["Stats4y"], self.plotUI["plotAllg4"], self.plotUI["textLabelg4"])
        self.graphObjects = [self.g1,self.g2,self.g3,self.g4]
        self.plotUI["SaveG1"].clicked.connect(self.g1.exportData)

    

    def handleAxEntered(self,event):
        ax = event.inaxes
        self.gatedAxes = ax
        print(ax)
        selectorType = self.UISelectorFactory.selectorType
        if selectorType is None:
            self.selector = None
        else:
            if ax.activeSelector is None:
                ax.activeSelector = self.UISelectorFactory.getSelector(ax, self.printhappy)
            else:
                if not isinstance(ax.activeSelector, self.UISelectorFactory.selectorType):
                    ax.activeSelector = self.UISelectorFactory.getSelector(ax, self.printhappy)
                
        
    def printhappy(self,*args):
        print("happy")
        
    def handle1dSelectorReadout(self, xmin, xmax):
        
        
        print(xmin)
        print(xmax)
        xAxDataKey = self.gatedAxes.xAxContent

        gatedFractionData = []
        """ for file in self.files:
            if file.getActiveState():
                xAxData = self.cellData[self.cellData["File"] == file][xAxDataKey]
                posFractionPercentage = len([x for x in xAxData if x >= xmin and x <= xmax])/len(xAxData)
            """
        PlotData = []
        for entry in self.datahandler.UItopLevelItems:
            if entry.isGroup():
                groupData = []
                for subfile in entry.fileItems:
                    xAxData = self.cellData[self.cellData["File"] == subfile][xAxDataKey]
                    if len(xAxData) > 0:
                        posFractionPercentage = len([x for x in xAxData if x >= xmin and x <= xmax])/len(xAxData)
                        groupData.append(posFractionPercentage)
                    meanPosFraction = np.mean(groupData)
                    stdPosFraction = np.std(groupData)
            else: 
                xAxData = self.cellData[self.cellData["File"] == entry][xAxDataKey]
                if len(xAxData)> 0:
                    posFractionPercentage = len([x for x in xAxData if x >= xmin and x <= xmax])/len(xAxData)
                    meanPosFraction = posFractionPercentage
                    stdPosFraction = 0
           
            if len(xAxData):
                PlotData.append({"EntryName": entry.text(0), "meanPosFraction": meanPosFraction, "stdPosFraction": stdPosFraction, "color": str(entry.plotColor)})
            
        PlotDataFrame = pd.DataFrame(PlotData)
        self.GateResults_axes.clear()
        PlotDataFrame.plot.bar(x = "EntryName", y = "meanPosFraction", yerr = "stdPosFraction", label = "EntryName",  ax = self.GateResults_axes, color = PlotDataFrame["color"].tolist())
        self.GateResults_axes.tick_params(axis = "x",labelrotation = 0)
        self.sampleSelectionData = PlotDataFrame 
        self.MplWidgetObj_Gateresults.canvas.draw()
        
        
    def handlerectSelectorReadout(self, eclick, erelease):
        
        xClick = eclick.xdata
        yClick = eclick.ydata
        
        xRelease = erelease.xdata
        yRelease = erelease.ydata
        
        xAxDataKey = self.gatedAxes.xAxContent
        yAxDataKey = self.gatedAxes.yAxContent

        gatedFractionData = []
        """ for file in self.files:
            if file.getActiveState():
                xAxData = self.cellData[self.cellData["File"] == file][xAxDataKey]
                posFractionPercentage = len([x for x in xAxData if x >= xmin and x <= xmax])/len(xAxData)
            """
        PlotData = []
        for entry in self.datahandler.UItopLevelItems:
            if entry.isGroup():
                groupData = []
                for subfile in entry.fileItems:
                    AxData = self.cellData[self.cellData["File"] == subfile]
                    if len(AxData) > 0:
                        posFractionPercentage = len(AxData[(AxData[xAxDataKey] >= xClick) & (AxData[xAxDataKey] <= xRelease) & (AxData[yAxDataKey] >= yClick) & (AxData[yAxDataKey] <= yRelease)])/len(AxData)
                        groupData.append(posFractionPercentage)
                    meanPosFraction = np.mean(groupData)
                    stdPosFraction = np.std(groupData)
            else: 
                AxData = self.cellData[self.cellData["File"] == entry]
                if len(AxData)> 0:
                    posFractionPercentage = len(AxData[(AxData[xAxDataKey] >= xClick) & (AxData[xAxDataKey] <= xRelease) & (AxData[yAxDataKey] >= yClick) & (AxData[yAxDataKey] <= yRelease)])/len(AxData)
                    meanPosFraction = posFractionPercentage
                    stdPosFraction = 0
           
            if len(AxData):
                PlotData.append({"EntryName": entry.text(0), "meanPosFraction": meanPosFraction, "stdPosFraction": stdPosFraction, "color": str(entry.plotColor)})
            
        PlotDataFrame = pd.DataFrame(PlotData)
        self.GateResults_axes.clear()
        PlotDataFrame.plot.bar(x = "EntryName", y = "meanPosFraction", yerr = "stdPosFraction", ax = self.GateResults_axes, color = PlotDataFrame["color"].tolist())
        self.GateResults_axes.tick_params(axis = "x",labelrotation = 0)
        self.sampleSelectionData = PlotDataFrame 
        self.MplWidgetObj_Gateresults.canvas.draw()
            




class subStatsGraph:
    
    peakOptionsList = ["First Peak Height", "First Peak Frame", "First Peak Decay Duration"]
    baseOptionsList =  ["Distance traveled", "Max signal intensity", "Mean Signal"]
    baseOptionsLen = len(baseOptionsList)
    maxOptionsLen = baseOptionsLen + len(peakOptionsList) + 1
    
    def __init__(self, ax, parent_datStatHandler, xAxSelector, yAxSelector, dataCheckBox, dataLabel):
        
        self.ax = ax
        self.parent_datStatHandler = parent_datStatHandler
        
        self.xAxSelector = xAxSelector
        self.yAxSelector = yAxSelector
        
        self.dataCheckBox = dataCheckBox
        self.dataLabel = dataLabel
        
        self.optionsadded = False
        self.initiateUI()
        self.selectionStatus = 0
        self.plottedData = []
        
    def initiateUI(self):
        self.xAxSelector.addItems(subStatsGraph.baseOptionsList)
        self.yAxSelector.addItems(subStatsGraph.baseOptionsList+["hist"])
        self.dataCheckBox.stateChanged.connect(self.dataCheckboxStateChanged)
        self.dataLabel.setText("all Cells")
        
    def refreshUIOptions(self):
        
        xAxContent = self.xAxSelector.currentText()
        yAxContent = self.yAxSelector.currentText()
        
        self.xAxSelector.clear()
        self.yAxSelector.clear()
        if self.selectionStatus == 0 or self.selectionStatus == 1:
            self.xAxSelector.addItems(subStatsGraph.baseOptionsList)
            self.yAxSelector.addItems(subStatsGraph.baseOptionsList+["hist"])
        else:   
            self.xAxSelector.addItems(subStatsGraph.baseOptionsList+subStatsGraph.peakOptionsList)
            self.yAxSelector.addItems(subStatsGraph.baseOptionsList+subStatsGraph.peakOptionsList+["hist"])
            
        xAxIndex = self.xAxSelector.findText(xAxContent)
        yAxIndex = self.yAxSelector.findText(yAxContent)
        
        if xAxIndex >= 0:
            self.xAxSelector.setCurrentIndex(xAxIndex)
        if yAxIndex >= 0:
            self.yAxSelector.setCurrentIndex(yAxIndex)
        else: self.yAxSelector.setCurrentIndex(-1)
        
        
        
    
    def dataCheckboxStateChanged(self):
        currentState = self.dataCheckBox.checkState()
        if currentState == 0:
            self.dataLabel.setText("all Cells")
            self.selectionStatus = 0
        elif currentState == 1:
            self.dataLabel.setText("all divided")
            self.selectionStatus = 1
        elif currentState == 2:
            self.dataLabel.setText("peak Cells")
            self.selectionStatus = 2
        self.refreshUIOptions()

        
            
    def handleAxContent(self):
        self.ax.clear()
        #self.plottedData = {} #Needed for Data Export From Plots. Has to be fixed
        xAxContent = self.xAxSelector.currentText()
        yAxContent = self.yAxSelector.currentText()
        
        
        if not (xAxContent == "None" or yAxContent == "None"):
            if yAxContent == "hist":
                
                xAxDataKey = subStatsGraph.StringOptionstoCellParameter(xAxContent)
                self.ax.xAxContent = xAxDataKey
                
                groupedData = []
                
                for file in self.parent_datStatHandler.files:
                    if file.getActiveState():
                        tempgroup = file.group
                        dataDf = self.parent_datStatHandler.cellData
                        if self.selectionStatus <2:
                            fileData = dataDf[dataDf["File"] == file]
                            if self.selectionStatus == 1:
                                posxAxData = fileData[fileData["hasPeak"] == True][xAxDataKey]
                                negxAxData = fileData[fileData["hasPeak"] == False][xAxDataKey]
                            else:
                                xAxData = dataDf[dataDf["File"] == file][xAxDataKey]
                            
                        else:
                            filtData =  dataDf[dataDf["hasPeak"] == True]
                            xAxData = filtData[filtData["File"] == file][xAxDataKey]
                        
                        if tempgroup is None:
                            color = file.plotColor
                            if self.selectionStatus == 1:
                                self.plotAxContent(color,posxAxData)
                                self.plotAxContent(color,negxAxData, "--")
                                #self.plottedData.append({"File": file.text(0),"posAxData": posxAxData,"negsAxData": negxAxData})
                            else:
                                self.plotAxContent(color,xAxData)
                                #self.plottedData[file.text(0)] = xAxData
                            
                        else:
                            groupID = tempgroup.groupID
                            if self.selectionStatus == 1:
                                tempdict = {"groupID": groupID, "group": tempgroup, "posAxData": posxAxData,"negsAxData": negxAxData }
                                groupedData.append(tempdict)
                            else:
                                tempdict = {"groupID": groupID, "group": tempgroup, "AxData": xAxData }
                                groupedData.append(tempdict)
                    
                if len(groupedData) > 0 :     
                    self.groupedDataFrame = pd.DataFrame(groupedData)
                        
                    for groupID in self.groupedDataFrame["groupID"].unique():
                        if not self.selectionStatus == 1:
                            tempDataList = self.groupedDataFrame[self.groupedDataFrame["groupID"] == groupID]["AxData"].tolist()
                            mergedDataList = [item for subdataList in tempDataList for item in subdataList]
                            color = self.groupedDataFrame[self.groupedDataFrame["groupID"] == groupID]["group"].tolist()[0].plotColor
                            self.plotAxContent(color,mergedDataList) #carefull with the clip if values over 10000 ever ocure
                            self.plottedData[groupID] = mergedDataList
                        else:
                            color = self.groupedDataFrame[self.groupedDataFrame["groupID"] == groupID]["group"].tolist()[0].plotColor
                            postempDataList = self.groupedDataFrame[self.groupedDataFrame["groupID"] == groupID]["posAxData"].tolist()
                            negtempDataList = self.groupedDataFrame[self.groupedDataFrame["groupID"] == groupID]["negsAxData"].tolist()
                            posMergedDataList = [item for subdataList in postempDataList for item in subdataList]
                            negMergedDataList = [item for subdataList in negtempDataList for item in subdataList]
                            self.plotAxContent(color,posMergedDataList)
                            self.plotAxContent(color,negMergedDataList,"--")
                            #self.plottedData.append({"Group": group,"posAxData": posMergedDataList,"negsAxData": negMergedDataList})
                            
                self.ax.set_xlabel(xAxContent,color = "white")
                self.ax.set_ylabel("Density",color = "white")
                
            else:
                #notfinished
                xAxDataKey = subStatsGraph.StringOptionstoCellParameter(xAxContent)
                yAxDataKey = subStatsGraph.StringOptionstoCellParameter(yAxContent)
                
                self.ax.xAxContent = xAxDataKey
                self.ax.yAxContent = yAxDataKey
                
                groupedData = []
                
                for file in self.parent_datStatHandler.files:
                    if file.getActiveState():
                        tempgroup = file.group
                        dataDf = self.parent_datStatHandler.cellData
                        if self.selectionStatus <2:
                            fileData = dataDf[dataDf["File"] == file]
                            xAxData = dataDf[dataDf["File"] == file][xAxDataKey]
                            yAxData = dataDf[dataDf["File"] == file][yAxDataKey]
                        else:
                            filtData =  dataDf[dataDf["hasPeak"] == True]
                            xAxData = filtData[filtData["File"] == file][xAxDataKey]
                            yAxData = filtData[filtData["File"] == file][yAxDataKey]
                        
                        if tempgroup is None:
                            color = file.plotColor
                            self.plot2DAxContent(color, xAxData, yAxData)
                            
                        else:
                            groupID = tempgroup.groupID
                            tempdict = {"groupID": groupID, "group": tempgroup, "xAxData": xAxData,"yAxData": yAxData }
                            groupedData.append(tempdict)
                       
                    
                if len(groupedData) > 0 :     
                    self.groupedDataFrame = pd.DataFrame(groupedData)
                        
                    for groupID in self.groupedDataFrame["groupID"].unique():
                        xtempDataList = self.groupedDataFrame[self.groupedDataFrame["groupID"] == groupID]["xAxData"].tolist()
                        ytempDataList = self.groupedDataFrame[self.groupedDataFrame["groupID"] == groupID]["yAxData"].tolist()
                        xmergedDataList = [item for subdataList in xtempDataList for item in subdataList]
                        ymergedDataList = [item for subdataList in ytempDataList for item in subdataList]
                        color = self.groupedDataFrame[self.groupedDataFrame["groupID"] == groupID]["group"].tolist()[0].plotColor
                        self.plot2DAxContent(color,xmergedDataList,ymergedDataList) #carefull with the clip if values over 10000 ever ocure
  
                            
                self.ax.set_xlabel(xAxContent,color = "white")
                self.ax.set_ylabel(yAxContent,color = "white")
                
    def plotAxContent(self, color, data, blub = "-"):
        sns.kdeplot(data, linestyle = blub, color = color, ax = self.ax, clip = (0,10000), common_norm = True)
        
    def plot2DAxContent(self, color, xData, yData):
        self.ax.scatter(xData, yData, color = color)
            
    def exportData(self):
        dlg = QFileDialog()
        dlg.setAcceptMode(QFileDialog.AcceptSave)
        if dlg.exec_():
            savePath = dlg.selectedFiles()[0]
            exportFrame = pd.DataFrame.from_dict(self.plottedData,  orient='index')
            exportFrame.to_csv(savePath)
                
            
    @staticmethod
    def StringOptionstoCellParameter(Option:str):
        
        print(Option)
        match(Option):
            case "First Peak Height": 
                
                parameter = "center_value"
                
            case "First Peak Frame": 
                
                parameter = "center_frame"
            
            case "First Peak Decay Duration": 
                
                parameter = "decay_dur"
            
            case "Distance traveled":
                
                parameter = "distanceTraveled"
            
            case "Max signal intensity":
                
                parameter = "maxHeight"
                
            case "Mean Signal":
                
                parameter = "signalMean"
            
        return parameter
        