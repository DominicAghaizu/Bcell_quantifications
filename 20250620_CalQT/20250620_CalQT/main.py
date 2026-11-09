# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import*
from PyQt5.uic import loadUi
from PyQt5.QtGui import (QBrush, QColor)
import sys
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import (NavigationToolbar2QT as NavigationToolbar)
import matplotlib as mpl
import pandas as pd
import numpy as np
import random
from modules import Datahandler
from modules.Datahandler import (cFileGroup, cFile)
from modules import Cell
from modules import Preprocessor
from modules import Peakprocessor
from modules import DataStatisticsHandler
from Dialogs import prepro_dialog
from Dialogs import representative_dialog
from Dialogs import peak_dialog
from Dialogs import overlay_dialog
from plottingUtils import customPlots
import csv


plt.rc("axes", facecolor = "white", edgecolor = "white", labelcolor = "white")


class MainWindow(QMainWindow):
    
    def __init__(self):
        
        super(MainWindow, self).__init__()

        loadUi("PyQT5_UI-Files/qt_designer_main_2.ui",self)
        
        self.setWindowTitle("PyQt5 & Matplotlib Example GUI")
        
        self.initiateGraph()
        self.fractionPlotData = "cluster"
        self.datahandler = Datahandler.Datahandler()
        self.preprocessor = Preprocessor.Preprocessor()
        self.peakprocessor = Peakprocessor.Peakprocessor()
        self.grad_peakprocessor = Peakprocessor.Gradpeak_Processor()
        global cellitem_list_1
        self.cellitem_list = {}
        
        self.lastID = 0
        
        dataStatsPlotUI = {"Stats1x": self.stats1_x,
                          "Stats2x": self.stats2_x,
                          "Stats3x": self.stats3_x,
                          "Stats4x": self.stats4_x,
                          "Stats1y": self.stats1_y,
                          "Stats2y": self.stats2_y,
                          "Stats3y": self.stats3_y,
                          "Stats4y": self.stats4_y,
                          "plotAllg1" :self.checkBox_useAll_g1,
                          "plotAllg2" :self.checkBox_useAll_g2,
                          "plotAllg3" :self.checkBox_useAll_g3,
                          "plotAllg4" :self.checkBox_useAll_g4,
                          "textLabelg1": self.textLabel_g1,
                          "textLabelg2": self.textLabel_g2,
                          "textLabelg3": self.textLabel_g3,
                          "textLabelg4": self.textLabel_g4,
                          "StatsAppend": self.statsAppend_Button,
                          "SaveG1": self.pushButton_saveDataG1}
        
        
        dataStatsSelectorUI = {"spanButton": self.spanSelector_pushButton,
                               "rectButton": self.rectangleSelector_pushButton,
                               "ellipseButton": self.ellipseSelector_pushButton
            
            }
        
        self.dataStatsHandler = DataStatisticsHandler.DataStatisticsHandler(self.datahandler, self.MplWidget_Datastats, dataStatsPlotUI, dataStatsSelectorUI, self.MplWidget_GateResults) 
        global datastatsaxes
        datastatsaxes = self.dataStatsHandler.axes
        
        
        #connecting buttons
        self.fileTree.itemClicked.connect(self.handleFileTreeClicked)
        self.cellTree.itemClicked.connect(self.cellitem_showplot)
        
        self.filtertracklen_pushButton.clicked.connect(self.append_tracklen_filter)
        self.group_Button.clicked.connect(self.group_files)
        self.removeGroup_Button.clicked.connect(self.delete_group)
        self.autoColor_pushButton.clicked.connect(self.autoColor_FileTree)
        self.actionOpen.triggered.connect(self.open_files)
        self.actionPre_processing.triggered.connect(self.open_prepro)
        self.actionPeak_finding.triggered.connect(self.open_peakfinder)
        self.pushButton_saveCSV_overview.clicked.connect(self.handleOverviewSaveButton)
        self.pushButton_saveRaw.clicked.connect(self.handleOverviewSaveRaw)
        self.pushButton_saveCSV_stats.clicked.connect(self.handleStatsSaveButton)
        self.pushButton_exportProperty.clicked.connect(self.exportCellProperty)
        self.overlay_Button.clicked.connect(self.showSampleOverlay)
        self.mean_Button.clicked.connect(self.showSampleMean)
        self.button_changeFractionData.clicked.connect(self.changeFractionPlotData)
        self.pushButton_representative.clicked.connect(self.openRepresentative)
        
        self.actionTimeSeries.triggered.connect(self.open_overlay)
        self.files = []
        self.groups = []
        
        self.define_ui_details()
        #self.addToolBar(NavigationToolbar(self.MplWidget_overview.canvas, self))
        
        

    def initiateGraph(self):
        
        self.MplWidget_overview.canvas.axes = self.MplWidget_overview.canvas.figure.add_subplot(111)
        self.MplWidget_overview.canvas.axes.clear()

        self.MplWidget_overview.canvas.figure.set_facecolor("#19232d")
        self.MplWidget_overview.canvas.axes.set_facecolor("#19232d")
        self.MplWidget_overview.canvas.figure.set_edgecolor("white")
        self.MplWidget_overview.canvas.axes.tick_params(colors='white', which='both')
        
        self.MplWidget_overview.canvas.draw()
        
        
        self.toolbar_Overview = NavigationToolbar(self.MplWidget_overview.canvas)
        self.toolbar_Overview.update()
        self.toolbar_Overview.repaint()
     
        
    def changeFractionPlotData(self):
        if self.fractionPlotData == "peaks":
            self.fractionPlotData = "cluster"
        else: 
            self.fractionPlotData = "peaks"
        self.update_graph()
        
    def update_graph(self):

        topItemList = [self.fileTree.topLevelItem(ItemIndex) for ItemIndex in range(self.fileTree.topLevelItemCount())]
      
        pa_list = []
        paErrors_list = []
        individual = []
        for Item in topItemList:
            if self.fractionPlotData == "peaks":
                data, errors = Item.getFilePeakStats()
                individualPoints = Item.getFilePeakStatsRaw()
                color = {"multiPeakCount": "white", "onePeakCount": "none","hasPeak": "none"}
            else: 
                data, errors = Item.getClusterStats()
                color = "black"
            pa_list.append(data)
            paErrors_list.append(errors)
            individual.append(individualPoints)
        print(pa_list)
        global pf
        
        global pf_errors
        pf_errors = pd.DataFrame(paErrors_list).set_index("path_alias")
        print(pf_errors)
        
        pf = pd.DataFrame(pa_list)
        xs = range(len(pf["path_alias"].unique()))
        pf = pf.set_index("path_alias")
        
        self.MplWidget_overview.canvas.axes.clear()
        ax = self.MplWidget_overview.canvas.axes
        pf.plot.bar(yerr = pf_errors, ax = ax, color = color, edgecolor = "white")
        for x in xs:
            ys = [di["hasPeaks"]/(di["hasPeaks"]+di["noPeak"]) for di in individual[x]]
            pltXs = np.random.normal(x, 0.04, size=len(ys))
            ax.scatter(pltXs, ys)
        
        
        self.MplWidget_overview.canvas.axes.tick_params(axis = "x",labelrotation = 45)
        self.MplWidget_overview.calan_dataForExportProcess = pf
        
        self.MplWidget_overview.canvas.axes.set_ylabel("Fraction")
        
        self.pushButton_saveCSV_overview.setEnabled(True)
        self.MplWidget_overview.canvas.figure.tight_layout()
        self.MplWidget_overview.canvas.draw()
        
    def handleOverviewSaveButton(self):
        dlg = QFileDialog()
        dlg.setAcceptMode(QFileDialog.AcceptSave)
        if dlg.exec_():
            overviewSavePath = dlg.selectedFiles()[0]
            self.MplWidget_overview.calan_dataForExportProcess.to_csv(overviewSavePath, sep = ";")
     
    def handleOverviewSaveRaw(self):
        dlg = QFileDialog()
        dlg.setAcceptMode(QFileDialog.AcceptSave)
        if dlg.exec_():
            overviewSavePath = dlg.selectedFiles()[0]
            topItemList = [self.fileTree.topLevelItem(ItemIndex) for ItemIndex in range(self.fileTree.topLevelItemCount())]
          
            dataList = []
            for Item in topItemList:
                data = Item.getFilePeakStatsRaw()
                [dataList.append(d) for d in data]
            print(dataList)
            pd.DataFrame(dataList).to_csv(overviewSavePath)
                
    def handleStatsSaveButton(self):
        dlg = QFileDialog()
        dlg.setAcceptMode(QFileDialog.AcceptSave)
        if dlg.exec_():
            overviewSavePath = dlg.selectedFiles()[0]
            tempExpData = self.dataStatsHandler.sampleSelectionData
            if not tempExpData is None:
                tempExpData.to_csv(overviewSavePath, sep = ";")
        
    def exportCellProperty(self):
        topItemList = [self.fileTree.topLevelItem(ItemIndex) for ItemIndex in range(self.fileTree.topLevelItemCount())]
        datadictForExport = {}
        for Item in topItemList:
            cells = Item.getCells()
            tempdata = []
            for cell in cells:
                pft = cell["peaks"]
                if pft is not None:
                    pft = pft.iloc[0]["center_value"]
                    tempdata.append(pft)
            datadictForExport[Item.text(0)] = tempdata
        
        dlg = QFileDialog()
        dlg.setAcceptMode(QFileDialog.AcceptSave)
        if dlg.exec_():
            savePath = dlg.selectedFiles()[0]
            exportFrame = pd.DataFrame.from_dict(datadictForExport,  orient='index')
            exportFrame = exportFrame.transpose()
            exportFrame.to_csv(savePath, sep = ";")
            
    def closeEvent(self, event):
        event.accept()
        print('Window closed')
        
        
        
#fileopen menue handler
    def open_files(self, event):
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.ExistingFiles)
        paths= []
        if dlg.exec_():
            paths = dlg.selectedFiles()
            self.datahandler.import_files(paths,self.progressBar) 
            self.path_alias_list = []
            for path in paths:
                path_alias = path.split("/")[-1]
                self.path_alias_list.append(path_alias)
                
                
            self.fileTree.addTopLevelItems(self.datahandler.FileListItems)  
            
            self.files = self.datahandler.FileListItems
            
        topItemList = [self.fileTree.topLevelItem(ItemIndex) for ItemIndex in range(self.fileTree.topLevelItemCount())]
        for TLI in topItemList:
            TLI.setBackground(2, QBrush(QColor(255, 255, 255)))
            
        global globFileList
        globFileList = self.datahandler.FileListItems

        for i in range(3):
            self.fileTree.resizeColumnToContents(i)
        
        self.datahandler.UItopLevelItems = [self.fileTree.topLevelItem(ItemIndex) for ItemIndex in range(self.fileTree.topLevelItemCount())]
    
       
        
    def update_filetree(self):
        itemcount = self.fileTree.topLevelItemCount()
        items = self.files
        
        for item in items:
            item.updatePeakDisplayStats()
        for group in self.groups:
            group.updatePeakDisplayStats()
        self.noPeak_checkBox.setEnabled(True)      
        self.onePeak_checkBox.setEnabled(True)
        self.multiPeak_checkBox.setEnabled(True)
        
                  
#handling of preprocessing window 
    def open_prepro(self):
        preprocessing_dialog = prepro_dialog.Prepro_Dialog(self.datahandler, self.preprocessor)
        preprocessing_dialog.finished.connect(self.handle_prepro_exit)
        preprocessing_dialog.exec()
    
    def handle_prepro_exit(self, result):
        
        if result == 1:
            process_all_dialog = QMessageBox()
            process_all_dialog.setWindowTitle("Processing")
            process_all_dialog.setText("Preprocess all Data?")
            process_all_dialog.setIcon(QMessageBox.Question)
            process_all_dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

            pa_dialog_result = process_all_dialog.exec()
            if pa_dialog_result == QMessageBox.Yes:
                workdata = self.datahandler.work_data
                cell_number_total = 0
                for key in workdata.keys():
                    cell_number_total = cell_number_total + len(workdata[key])
                cell_index = 0
                for key in workdata.keys():
                    for cell in workdata[key]:
                        cell.append_processed_data(self.preprocessor)
                        cell.append_gradient_data()
                        
                        self.progressBar.setValue(int((cell_index/cell_number_total)*100))
                        cell_index = cell_index + 1
        self.progressBar.setValue(0)          
            
        
#handling of peakfinder window
    def open_peakfinder(self):
        peakfinder_dialog = peak_dialog.Peak_Dialog(self.datahandler, self.peakprocessor, self.grad_peakprocessor)
        peakfinder_dialog.finished.connect(self.handle_peakfinder_exit)
        peakfinder_dialog.exec()
    
    def handle_peakfinder_exit(self, result):
        if result == 1:
            findpeaks_all_dialog = QMessageBox()
            findpeaks_all_dialog.setWindowTitle("Peak detection")
            findpeaks_all_dialog.setText("Detect Peaks in all Files?")
            findpeaks_all_dialog.setIcon(QMessageBox.Question)
            findpeaks_all_dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            
            fp_dialog_result = findpeaks_all_dialog.exec()
            if fp_dialog_result == QMessageBox.Yes:
                workdata = self.datahandler.work_data
                
                cell_number_total = 0
                for key in workdata.keys():
                    cell_number_total = cell_number_total + len(workdata[key])
                cell_index = 0
                for key in workdata.keys():
                    for cell in workdata[key]:
                        cell.detect_peaks(self.peakprocessor, self.grad_peakprocessor)
                        
                        
                        self.progressBar.setValue(int((cell_index/cell_number_total)*100))
                        cell_index = cell_index + 1
        self.progressBar.setValue(0)
        self.update_filetree()
        self.fractionPlotData = "peaks"
        self.update_graph()
        
    
    def open_overlay(self):
        overlay_dialog_instance = overlay_dialog.Overlay_Dialog(self.datahandler, self.fileTree)
        #overlay_dialog_instance.finished.connect(self.handle_peakfinder_exit)
        overlay_dialog_instance.exec()


#getting celltree items and interaction       
    def handleFileTreeClicked(self, item, column):
        if column == 2:
            colorpicker = QColorDialog()
            pickedColor = colorpicker.getColor()
            if pickedColor.isValid():
                item.setBackground(2, QBrush(pickedColor))
                
                if isinstance(item,cFileGroup):
                    for subitem in item.fileItems:
                        print(subitem)
                        subitem.setBackground(2, QBrush(pickedColor))
                item.setPlotColor(str(pickedColor.name()))
                
        else: self.update_celltree(item)
        
    def autoColor_FileTree(self):
        n = self.fileTree.topLevelItemCount()
        cmap= mpl.colormaps["rainbow"]
        colors = [map(lambda x: int(x*255),(cmap(i/n))) for i in range(n)]
        for i in range(n):
            item = self.fileTree.topLevelItem(i)
            tempQcolor = QColor(*colors[i])
            item.setBackground(2, QBrush(tempQcolor))
            item.setPlotColor(str(tempQcolor.name()))
            if isinstance(item,cFileGroup):
                for subitem in item.fileItems:
                    subitem.setBackground(2, QBrush(tempQcolor))
                    
    def update_celltree(self,item):
        
        if isinstance(item,Datahandler.cFile) or isinstance(item, Datahandler.cFileGroup):
            
            self.cellTree.clear()
            path = item.text(0)
            temp_cells = item.getCells()
            items = [cell.make_TreeWidgetItem() for cell in temp_cells]
            self.cellTree.addTopLevelItems(items)
            
            if item.hasPeakData:
                self.noPeak_count_label.setText(str(item.n_noPeak))
                self.onePeak_count_label.setText(str(item.n_onePeak))
                self.multiPeak_count_label.setText(str(item.n_multiPeak))
            else:
                self.noPeak_count_label.setText("no data available")
                self.onePeak_count_label.setText("no data available")
                self.multiPeak_count_label.setText("no data available")
                
    
            
            

    def group_files(self):
        selectedItems = self.fileTree.selectedItems()
        if len(selectedItems) > 0:
            selectedItems = [item for item in selectedItems if isinstance(item, Datahandler.cFile)]
            pathList = [Item.text(0) for Item in selectedItems]
            
            
            groupName = cFileGroup.createGroupName(pathList, self.groupingDelimiter.itemText(self.groupingDelimiter.currentIndex()))
            
            groupItem = cFileGroup(self.fileTree)
            groupItem.groupID = self.generateUniqueID()
            groupItem.setfileItems(selectedItems)
            groupItem.setText(0, groupName)
            groupItem.setText(1, str(sum([int(sI.text(1)) for sI in selectedItems])))
            
            
            for item in selectedItems:
                item.group = groupItem
                self.fileTree.takeTopLevelItem(self.fileTree.indexOfTopLevelItem(item))
            
            if all(item.hasPeakData for item in selectedItems):
                groupItem.updatePeakDisplayStats()
            
        groupItem.addChildren(selectedItems)
        self.datahandler.UItopLevelItems = [self.fileTree.topLevelItem(ItemIndex) for ItemIndex in range(self.fileTree.topLevelItemCount())]
        self.groups.append(groupItem)
    
    def delete_group(self):
        selectedItems = self.fileTree.selectedItems()
        print(str(selectedItems))
        if len(selectedItems) > 0:
            selectedItems = [item for item in selectedItems if item.isGroup()]
            print(str(selectedItems))
            for group in selectedItems:
                print("deleting")
                items = group.takeChildren()
                print(items)
                self.fileTree.takeTopLevelItem(self.fileTree.indexOfTopLevelItem(group))
                self.fileTree.addTopLevelItems(items)
                for item in items:
                    item.group = None
                
            self.groups.remove(item)
            self.datahandler.UItopLevelItems = [self.fileTree.topLevelItem(ItemIndex) for ItemIndex in range(self.fileTree.topLevelItemCount())]  
            
    def generateUniqueID(self):
        newID = self.lastID + 1
        self.lastID = newID
        return newID
        
        
    def cellitem_showplot(self, item, column):
        fig, axs = plt.subplots()
        cell = item.get_Cell()
        
        cell["Raw_Data"]["MEAN_INTENSITY_CH1"].plot(ax = axs)
    
    def showSampleOverlay(self):
        currentItem = self.fileTree.currentItem()
        cells = currentItem.getCells(peakStatusFilter = self.getPeakCheckboxFilter())
        fig, axs = customPlots.createBlackPlot()

        tMin, tMax = self.getFigureXRange()
        globMaxInt = self.getPlotYMaxInt()
        
        if self.radioButton_fancyOverlay.isChecked():
            customPlots.densityOverlayPlot.create_overlay_density(cells, axs, globMaxInt, tMin, tMax, fancy = True)
        else:
            customPlots.densityOverlayPlot.create_overlay_density(cells, axs, globMaxInt, tMin, tMax, fancy = False)
        fig.suptitle(currentItem.text(0)+ "\n n:" + str(len(cells)) + " " + self.getPeakFilterIncludedString())
        fig.canvas.draw()
        
    def showSampleMean(self):
        tMin, tMax = self.getFigureXRange()
        
        globMaxInt = self.getPlotYMaxInt()
        
        currentItems = self.fileTree.selectedItems()
        cells = {item.text(0): item.getCells(peakStatusFilter = self.getPeakCheckboxFilter()) for item in currentItems}
        
        fig, axs = customPlots.createBlackPlot()
        
        globalmax = self.getPlotYMaxInt()
        customPlots.meanPlot.createMeanPlot(cells, axs, globalmax)
        if tMax == -1:
            tMaxLim = None
        else: tMaxLim = tMax
        axs.set_xlim(tMin, tMaxLim)
        axs.set_ylim(0, self.getPlotYMaxInt())
        fig.canvas.draw()
        
    def getFigureXRange(self):
        
        tDataMaxLen = int(self.datahandler.get_globalmaxLen())
        tMinEntry = int(self.lineEdit_overlayMinTimepoint.text())
        if tMinEntry > tDataMaxLen:
            tMin = 0
        else:
            tMin = tMinEntry
            
        tMaxEntry = int(self.lineEdit_overlayMaxTimepoint.text())
        tMax = tMaxEntry
        
        return (tMin, tMax)
    
    def getPlotYMaxInt(self):
        if self.lineEdit_overlayYmax.text() == "0":
            globalmax = self.datahandler.get_globalmaxMean()*1.5
        else:
            globalmax = float(self.lineEdit_overlayYmax.text())
        return globalmax
        
    
    def openRepresentative(self):
        
        currentItems = self.fileTree.selectedItems()
        cells = {item.text(0): item.getCells(peakStatusFilter = self.getPeakCheckboxFilter()) for item in currentItems}
        
        rep_dialog = representative_dialog.Representative_Dialog(cells)
        rep_dialog.finished.connect(self.handleRepExit)
        rep_dialog.exec()

    def handleRepExit(self):
        print("Rep Exit")
        
    def append_tracklen_filter(self):
        lower_th = int(self.minTracklen_QLine.text())
        upper_th = int(self.maxTracklen_QLine.text())
        wd = self.datahandler.work_data
        
        if upper_th == -1: 
            filter_bool = lambda tlen: tlen > lower_th
        else: 
            filter_bool = lambda tlen: tlen > lower_th and tlen < upper_th
            
            
        for file in wd:
            for cell in wd[file]:

                cell.set_filter_status(filter_bool(int(cell["tracklength"])))
                
        self.datahandler.filter_workdata()
        
        
#some ui-style details that could not be made in QT designer

    def getPeakCheckboxFilter(self):
        peakFilterDict = {}
        peakFilterDict["noPeak"] = self.noPeak_checkBox.isChecked()
        peakFilterDict["onePeak"] = self.onePeak_checkBox.isChecked()
        peakFilterDict["multiPeak"] = self.multiPeak_checkBox.isChecked()
        return peakFilterDict
    
    def getPeakFilterIncludedString(self): #get a String describing the content of a filtered Plot
        filterStatus = self.getPeakCheckboxFilter()
        included = []
        excluded = []
        for key in filterStatus:
            if filterStatus[key]:
                included.append(key)
            else:
                excluded.append(key)
                
        returnString = "Included: "
        if len(included) > 0:
            for k in included:
                returnString = returnString + k + " "
        else: returnString = returnString + "-"
        returnString = returnString + "Excluded: "
        if len(excluded) > 0:
            for k in excluded:
                returnString = returnString + k + " "
        else: returnString = returnString + "-"
                
        return returnString
    
    
    def define_ui_details(self):
        self.fileTree.header().setSectionResizeMode(0,QHeaderView.ResizeToContents)
        self.progressBar.setStyleSheet("QProgressBar"
                          "{"
                          "background-color :  rgb(25, 35, 45);"
                          "border : 1px;"
                          "margin: 5px;"
                          "}" 
                          "QProgressBar::chunk"
                          "{"
                          "background-color :  QLinearGradient( x1: 0, y1: 0,x2: 1, y2: 0, stop: 0 #471657, stop: 1 #57163d );"
   
                          "}")


if __name__ == "__main__":
    
    sys.path.insert(1, "mplWidget")
    plt.ion()
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec_())