# -*- coding: utf-8 -*-
"""
Created on Tue Jan 17 12:55:33 2023

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

class Peak_Dialog(QDialog):
    
    def __init__(self, datahandler, peakprocessor, grad_peakprocessor):
    
        
        super(Peak_Dialog, self).__init__()
        
        loadUi("PyQT5_UI-Files/peak_dialog.ui",self)
        
        self.datahandler = datahandler
        self.globalmax = self.datahandler.get_globalmaxMean()*1.2
        
        self.parent_peakprocessor = peakprocessor
        self.work_peakprocessor = Peakprocessor.Peakprocessor()
        
        self.grad_parent_peakprocessor = grad_peakprocessor
        self.grad_work_peakprocessor = Peakprocessor.Gradpeak_Processor()
        self.load_from_parent_peakprocessor()
        self.load_from_parent_grad_peakprocessor()
        self.initiate_mpl_statistics()
        
        self.page = 0
        
        self.initiate_mpl_examples()
        self.connect_ui()
        
        self.statsplot_3 = None
  
    
  

    def connect_ui(self):
        
        self.button_refresh.clicked.connect(self.handle_append)
        self.button_calculate_Combi.clicked.connect(self.calculate_combi)
        self.prepro_roll.clicked.connect(self.handle_reroll_button)
        self.prepro_scroll.setMaximum(len(self.data_pages)-1)
        self.prepro_scroll.valueChanged.connect(self.change_page)
        self.dialog_buttons.button(QDialogButtonBox.Apply).clicked.connect(self.apply_changes)
        self.MplWidget_peaks1.canvas.mpl_connect("motion_notify_event", self.peak_hover)
        self.MplWidget_peaks2.canvas.mpl_connect("motion_notify_event", self.peak_hover)
        self.MplWidget_peaks3.canvas.mpl_connect("motion_notify_event", self.peak_hover)
        self.MplWidget_statistics.canvas.mpl_connect("motion_notify_event", self.statsplot.handle_hover)
        self.MplWidget_statistics_2.canvas.mpl_connect("motion_notify_event", self.statsplot_2.handle_hover)
        #self.MplWidget_statistics_2.canvas.mpl_connect("motion_notify_event", self.statsplot_3.handle_hover)
        #self.calculate_Combi.clicked.connect(self.calc_combi)

    def initiate_mpl_examples(self):
       
        self.reroll_samples()

        
        self.axes_slots = []
        
        self.axes_slots.append([self.MplWidget_peaks1.canvas.figure.add_subplot(211),self.MplWidget_peaks1.canvas.figure.add_subplot(212)])
        self.axes_slots.append([self.MplWidget_peaks2.canvas.figure.add_subplot(211),self.MplWidget_peaks2.canvas.figure.add_subplot(212)])
        self.axes_slots.append([self.MplWidget_peaks3.canvas.figure.add_subplot(211),self.MplWidget_peaks3.canvas.figure.add_subplot(212)])
        
        for axes in self.axes_slots:
            axes[0].path_details = []
            axes[1].path_details = []
        
        self.refresh_data_and_graphs()
        
    """
    def calc_combi(self):
        
        tempcelldata = self.datahandler.workdata
        for key in tempcelldata.keys():
            for cell in tempcelldata[key]:
    """          
            
   
    def initiate_mpl_statistics(self):
   
        temp_stat_ax = self.MplWidget_statistics.canvas.figure.add_subplot(111)
        tempdata = self.datahandler.get_gradmax_list()

        hist_counts, hist_bins, waste = temp_stat_ax.hist(tempdata, density = True, bins = 20)
        sns.kdeplot(tempdata,  ax = temp_stat_ax)
        self.statsplot = Statsplot.Statsplot(temp_stat_ax, self.mousePosition_label, self.MplWidget_statistics.canvas)
        
        
        
        temp_stat_ax = self.MplWidget_statistics_2.canvas.figure.add_subplot(111)
        tempdata = self.datahandler.get_peakmax_list()

        hist_counts, hist_bins, waste = temp_stat_ax.hist(tempdata, density = True, bins = 20)
        sns.kdeplot(tempdata,  ax = temp_stat_ax)
        
        self.statsplot_2 = Statsplot.Statsplot(temp_stat_ax, self.mousePosition_label, self.MplWidget_statistics_2.canvas)
        
        
    def load_from_parent_peakprocessor(self):
        
        parent_config = self.parent_peakprocessor.get_config() #getting parent-prepro config
        print(parent_config)
        self.peak_config_dict = parent_config #saving in own dict object
        self.work_peakprocessor.set_config(parent_config) #initaly applying to temp work processor
        
        #application to ui
        self.peak_init_th.setText(str(parent_config["threshold_ratio_mean"]))
        self.decay_th.setText(str(parent_config["threshold_ratio_decay"]))
        
    def load_from_parent_grad_peakprocessor(self):
        
        parent_config = self.grad_parent_peakprocessor.get_config() #getting parent-prepro config
        print(parent_config)
        self.grad_peak_config_dict = parent_config #saving in own dict object
        self.grad_work_peakprocessor.set_config(parent_config) #initaly applying to temp work processor
        
        #application to ui
        self.grad_edge_thresh.setText(str(parent_config["grad_edge_threshold"]))
        self.grad_edge_ratio.setText(str(parent_config["grad_edge_ratio"]))       
        
        
        
        
        
        
        
        
    #def append_to_preprocessor(self):
    def handle_reroll_button(self):
        self.reroll_samples()
        self.refresh_data_and_graphs()
        
    def reroll_samples(self):
        
        self.data_pages = [] #saving cells in pages
        self.peakdata_pages = []
        self.peakLine_pages = []
        self.gradpeakdata_pages = []
        work_data = self.datahandler.work_data
        
        
        #putting data to pages
        index = 0
        temp_page = []
        for key_ind, key in enumerate(work_data.keys()):
            
            if index < 3:
                temp_page.append(np.random.choice(work_data[key])) #appending cells to temp_pages
                index = index + 1
                
                   
            else:
                
                self.data_pages.append(temp_page)
                self.peakdata_pages.append([])
                self.gradpeakdata_pages.append([])
                self.peakLine_pages.append([])
                temp_page = []
                temp_page.append(np.random.choice(work_data[key]))
                index = 1
            
            if key_ind == len(work_data.keys())-1:
                self.data_pages.append(temp_page)
                self.peakdata_pages.append([])
                self.gradpeakdata_pages.append([])
                self.peakLine_pages.append([])
                
    def change_page(self,value):
        self.page = value
        self.refresh_data_and_graphs()
        
    
    def recalculate_data(self):
        data_pages_copy = self.data_pages.copy()
        for index,page in enumerate(data_pages_copy):
            self.peakdata_pages[index] = []
            self.gradpeakdata_pages[index] = []
            
            for cell in page:
                temp_peaks_df = self.work_peakprocessor.processPeaks(cell["processed_data"].tolist())
                temp_gradpeaks_df = self.grad_work_peakprocessor.processPeaks(cell["gradient_data"].tolist())
                
                if not temp_peaks_df is None and not temp_gradpeaks_df is None:
                    temp_peaks_df = Peakprocessor.matcher.match_peaks(temp_peaks_df, temp_gradpeaks_df, cell["processed_data"].tolist()) #leaving only peaks that have corresponding zero points in gradient peak analysis
                if temp_gradpeaks_df is None:
                    temp_peaks_df = None
                self.peakdata_pages[index].append(temp_peaks_df)
                self.gradpeakdata_pages[index].append(temp_gradpeaks_df)
                
                
    def refresh_data_and_graphs(self):
        
        self.recalculate_data()
        
        for ax_slot in self.axes_slots:
            for ax in ax_slot:
                ax.clear()
        
        max_value = 0
        for index, cell in enumerate(self.data_pages[self.page]):
            temp_ax = self.axes_slots[index][0]
            grad_ax = self.axes_slots[index][1]
            temp_ax.plot(cell["processed_data"])
            grad_ax.plot(cell["gradient_data"])
            
        for slot in self.axes_slots:
            slot[0].set_ylim(0,self.globalmax + 1)
        
        for index, peaks in enumerate(self.peakdata_pages[self.page]):
            temp_ax = self.axes_slots[index][0]
            temp_ax.peakLines = []
            if not peaks is None:
                for index, peak in peaks.iterrows():
                    peakLine = temp_ax.axvline(peak["center_frame"], color ="green")
                    peakLine.peakData = peak
                    peakLine.isSelected = False
                    temp_ax.peakLines.append(peakLine) #self.peakLine_pages[self.page].append(peakLine)
        
        for index, peaks in enumerate(self.gradpeakdata_pages[self.page]):
            temp_ax = self.axes_slots[index][1]
            temp_ax.peakLines = []
            if not peaks is None:
                print(type(peaks))
                for index, peak in peaks.iterrows():
                    peakLine = temp_ax.axvline(peak["center_frame"], color ="green")
                    peakLine.peakData = peak
                    peakLine.isSelected = False
                    temp_ax.peakLines.append(peakLine) #self.peakLine_pages[self.page].append(peakLine)
       
        self.draw_canvases()
    
    
    def draw_canvases(self):
        self.MplWidget_peaks1.canvas.draw()   
        self.MplWidget_peaks2.canvas.draw()   
        self.MplWidget_peaks3.canvas.draw()   
    
    def apply_ui_to_peakprocessor(self):
        
        self.work_peakprocessor.set_config(self.peak_config_dict)
        self.grad_work_peakprocessor.set_config(self.grad_peak_config_dict)

        
                
    def validate_userinput(self):
        
        temp_edge_dict = {
            "threshold_ratio_mean" :float(self.peak_init_th.text()),
            "threshold_ratio_decay" :float(self.decay_th.text()),
            #"peak_width": float(self.peakWidth_input.text()),
            "threshold_combi_score": float(self.combi_score_filter.text()),
            }
        
        temp_grad_dict = {
            "grad_edge_threshold": float(self.grad_edge_thresh.text()),
            "grad_edge_ratio" :float(self.grad_edge_ratio.text())}
        error = False

        if temp_edge_dict["threshold_ratio_decay"]:
            if temp_edge_dict["threshold_ratio_decay"] < 0 or temp_edge_dict["threshold_ratio_decay"] > 1:
                self.peak_error_label.setText("Error: decay threshold ratio has to be between 0 and 1")
                error = True
                print(error)
                
        if temp_grad_dict["grad_edge_threshold"]:
            if temp_grad_dict["grad_edge_threshold"] < 0:
                self.peak_error_label.setText("Error: Global edge threshhold has to be above 0")
                error = True
                print(error)
            
        if temp_grad_dict["grad_edge_ratio"]:
            if temp_grad_dict["grad_edge_ratio"] < 0 or temp_grad_dict["grad_edge_ratio"] > 1 :
                self.peak_error_label.setText("Error: Aditional edge ratio has to be between 0 and 1")
                error = True
                print(error)
            
                
                
        if not error:
            print("noerror")
            self.peak_error_label.setText("")
            self.peak_config_dict = temp_edge_dict
            self.grad_peak_config_dict = temp_grad_dict
            
        return (not error)
    
    def calculate_combi(self):
        
        if self.statsplot_3 is None:
            temp_stat_ax = self.MplWidget_statistics_3.canvas.figure.add_subplot(111)
            tempdata = self.datahandler.get_combiscore_list(self.work_peakprocessor, self.grad_work_peakprocessor)
            
            hist_counts, hist_bins, waste = temp_stat_ax.hist(tempdata, density = True, bins = 20)
            sns.kdeplot(tempdata,  ax = temp_stat_ax)
            
            self.statsplot_3 = Statsplot.Statsplot(temp_stat_ax, self.mousePosition_label, self.MplWidget_statistics_3.canvas)
            
            self.MplWidget_statistics_3.canvas.mpl_connect("motion_notify_event", self.statsplot_3.handle_hover)
            self.MplWidget_statistics_3.canvas.draw()
        else:
            temp_stat_ax = self.statsplot_3.ax
            temp_stat_ax.clear()
            tempdata = self.datahandler.get_combiscore_list(self.work_peakprocessor, self.grad_work_peakprocessor) 
            hist_counts, hist_bins, waste = temp_stat_ax.hist(tempdata, density = True, bins = 20)
            sns.kdeplot(tempdata,  ax = temp_stat_ax)
            self.MplWidget_statistics_3.canvas.draw()
            

###axes hover handling        
    def peak_hover(self, event):
        
        if event.inaxes:
         
            temp_ax = event.inaxes
            for line in temp_ax.peakLines: #self.peakLine_pages[self.page]:
                cont, det = line.contains(event)
                print(temp_ax)
                if cont:
                    
                    
                    
                    self.peakDetails.setText(str(line.peakData))
                    
                    if not line.isSelected:
                        print(det["ind"])
                        line.set(color = "pink", alpha = 1)
                        
                        
                        #removing old detail lines
                        ax_lines = temp_ax.get_lines()
                        for line_det in temp_ax.path_details:
                           line_det.remove()
                        #clearing detail list
                        temp_ax.path_details = []
                        
                        #creating and drawing new path detail lines
                        temp_ax.path_details.append(temp_ax.axvline(float(line.peakData["left_frame"]), c = "darkorange", alpha = 1))
                        temp_ax.path_details.append(temp_ax.axvline(float(line.peakData["right_frame"]), c = "darkorange", alpha = 1))
                        
                        if "passzero_index" in line.peakData.keys():
                            temp_ax.path_details.append(temp_ax.axvline(float(line.peakData["passzero_index"]), c = "crimson", alpha = 1))

                        
                        self.draw_canvases()
                        line.isSelected = True
                    
                else: 
                    line.set(color = "green", alpha = 0.2)
                    line.isSelected = False
                    
        else: print("notinaxs")
        
            
    def handle_append(self):
        input_correct = self.validate_userinput()
        if input_correct:
            self.apply_ui_to_peakprocessor()
            self.refresh_data_and_graphs()
        
    def apply_changes(self):
        self.parent_peakprocessor.set_config(self.peak_config_dict)
        self.grad_parent_peakprocessor.set_config(self.grad_peak_config_dict)
        print("Changes applied")
        print(self.parent_peakprocessor.get_config())
        print(self.grad_parent_peakprocessor.get_config())
        self.accept()
        
        
        