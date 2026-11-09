# -*- coding: utf-8 -*-
"""
Created on Fri Jan 13 14:40:24 2023

@author: Willi
"""
from PyQt5.QtWidgets import*
from PyQt5.uic import loadUi
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import (NavigationToolbar2QT as NavigationToolbar)
from modules import Preprocessor
from modules import Cell
import numpy as np

class Prepro_Dialog(QDialog):
    
    def __init__(self, datahandler, preprocessor):
    
        
        super(Prepro_Dialog, self).__init__()
        
        loadUi("PyQT5_UI-Files/prepro_dialog.ui",self)
        
        self.datahandler = datahandler
        
        self.parent_preprocessor = preprocessor
        self.work_preprocessor = Preprocessor.Preprocessor()
        self.load_from_parent_preprocessor()
        self.page = 0
        
        self.initiate_mpl_examples()
        self.connect_ui()
        
    
    def connect_ui(self):
        
        self.button_refresh.clicked.connect(self.handle_append)
        self.prepro_roll.clicked.connect(self.reroll_samples)
        self.prepro_scroll.setMaximum(len(self.data_pages)-1)
        self.prepro_scroll.valueChanged.connect(self.change_page)
        self.dialog_buttons.button(QDialogButtonBox.Apply).clicked.connect(self.apply_changes)
        
    def initiate_mpl_examples(self):
        #self.MplWidget_prepro.canvas.axes.clear()
        self.data_pages = []
        self.smoothdata_pages = []
        self.normdata_pages = []
        
        work_data = self.datahandler.work_data
        
        
        #putting data to pages
        index = 0
        temp_page = []
        for key_ind, key in enumerate(work_data.keys()):
            
            if index < 4:
                temp_page.append(np.random.choice(work_data[key])) #appending cells to temp_pages
                index = index + 1
                
                   
            else:
                
                self.data_pages.append(temp_page)
                self.smoothdata_pages.append([])
                self.normdata_pages.append([])
                
                temp_page = []
                temp_page.append(np.random.choice(work_data[key]))
                index = 1
            
            if key_ind == len(work_data.keys())-1:
                self.data_pages.append(temp_page)
                self.smoothdata_pages.append([])
                self.normdata_pages.append([])
        
        self.axes = []
        self.axes.append(self.MplWidget_prepro.canvas.figure.add_subplot(221))
        self.axes.append(self.MplWidget_prepro.canvas.figure.add_subplot(222))
        self.axes.append(self.MplWidget_prepro.canvas.figure.add_subplot(223))
        self.axes.append(self.MplWidget_prepro.canvas.figure.add_subplot(224))
        
        self.MplWidget_prepro.canvas.figure.set_facecolor("#19232d")
        self.MplWidget_prepro.canvas.figure.set_edgecolor("white")
        for ax in self.axes:
            ax.set_facecolor("#19232d")
            ax.tick_params(colors='white', which='both')
        self.refresh_data_and_graphs()
        
        

    
    def reroll_samples(self):
        work_data = self.datahandler.work_data
        self.data_pages = []
        
        #putting data to pages
        index = 0
        temp_page = []
        for key_ind, key in enumerate(work_data.keys()):
            
            if index < 4:
                temp_page.append(np.random.choice(work_data[key])) #appending cells to temp_pages
                index = index + 1
                
                   
            else:
                
                self.data_pages.append(temp_page)
                self.smoothdata_pages.append([])
                self.normdata_pages.append([])
                
                temp_page = []
                temp_page.append(np.random.choice(work_data[key]))
                index = 1
            
            if key_ind == len(work_data.keys())-1:
                self.data_pages.append(temp_page)
                self.smoothdata_pages.append([])
                self.normdata_pages.append([])
                
        self.refresh_data_and_graphs()
       
    def change_page(self,value):
        self.page = value
        self.refresh_data_and_graphs()
        
    
    def refresh_data_and_graphs(self):
        
        self.recalculate_data()
        
        for ax in self.axes:
            ax.clear()
        if self.normalize_bool.isChecked():
            for index, cell in enumerate(self.normdata_pages[self.page]):
                temp_original_cell = self.data_pages[self.page][index]
                temp_ax = self.axes[index]
                temp_ax.plot(cell, c = "white")
                temp_ax.set_title(str(temp_original_cell["Path"]) + " Track:" + str(temp_original_cell["Track"]),fontdict = {"fontsize": 10 }, c = "white")
        else:
            for index, cell in enumerate(self.data_pages[self.page]):
                self.axes[index].clear()
                
                temp_ax = self.axes[index]
                cell["Raw_Data"]["MEAN_INTENSITY_CH1"].plot(ax = temp_ax)
                temp_ax.set_title(str(cell["Path"]) + " Track:" + str(cell["Track"]),fontdict = {"fontsize": 10 })
        
        if self.smooth_bool.isChecked():
            for index, cell in enumerate(self.smoothdata_pages[self.page]):
                temp_ax = self.axes[index]
                temp_ax.plot(cell, c = "red")   
                
        self.MplWidget_prepro.canvas.draw()   
        
    def load_from_parent_preprocessor(self):
        
        parent_config = self.parent_preprocessor.get_config() #getting parent-prepro config
        print(parent_config)
        self.prepro_config_dict = parent_config #saving in own dict object
        self.work_preprocessor.set_config(parent_config) #initaly applying to temp work processor
        
        #application to ui
        self.smooth_window.setText(str(parent_config["smoothing_window"]))
        self.smooth_polyorder.setText(str(parent_config["smoothing_poly"]))
        self.crop_start.setText(str(parent_config["crop_start"]))
        self.crop_end.setText(str(parent_config["crop_end"]))
        self.smooth_bool.setChecked(bool(parent_config["smoothing_bool"]))
        self.normalize_bool.setChecked(bool(parent_config["normalize_bool"]))
    
    def apply_ui_to_preprocessor(self):
        self.work_preprocessor.set_config(self.prepro_config_dict)
        
    def recalculate_data(self):
        data_pages_copy = self.data_pages.copy()
        for index,page in enumerate(data_pages_copy):
            self.smoothdata_pages[index] = []
            self.normdata_pages[index] = []
            for cell in page:
                temp_normdata, temp_smoothdata = self.work_preprocessor.preprocess(cell["Raw_Data"]["MEAN_INTENSITY_CH1"].tolist(), return_seperate = True)
                
                self.smoothdata_pages[index].append(temp_smoothdata)
                self.normdata_pages[index].append(temp_normdata)
                
    def validate_userinput(self):
        
        temp_dict = {
            "smoothing_window" :int(self.smooth_window.text()),
            "smoothing_poly" :int(self.smooth_polyorder.text()),
            "smoothing_bool": self.smooth_bool.isChecked(),
            "crop_start": int(self.crop_start.text()),
            "crop_end": int(self.crop_end.text()),
            "normalize_bool": self.normalize_bool.isChecked(),
            "autoCutFirst": self.radioButton_autoCutFirst.isChecked()
            }
        error = False
        
        if temp_dict["smoothing_bool"]:
            if (temp_dict["smoothing_window"] % 2 == 0):
                self.smooth_error_label.setText("Error: Window has to be odd")
                error = True
                print(error)
            elif (temp_dict["smoothing_window"] < temp_dict["smoothing_poly"]):
                self.smooth_error_label.setText("Error: Window has to be larger than polyorder")
                error = True
                print(error)
                
        if not error:
            print("noerror")
            self.smooth_error_label.setText("")
            self.prepro_config_dict = temp_dict
            
        return (not error)
        
        
        
    def handle_append(self):
        input_correct = self.validate_userinput()
        if input_correct:
            self.apply_ui_to_preprocessor()
            self.refresh_data_and_graphs()
        
    def apply_changes(self):
        self.parent_preprocessor.set_config(self.prepro_config_dict)
        print("Changes applied")
        print(self.parent_preprocessor.get_config())
        self.accept()
        
        
        