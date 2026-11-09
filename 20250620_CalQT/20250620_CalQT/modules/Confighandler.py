# -*- coding: utf-8 -*-
"""
Created on Fri Jan 13 16:23:49 2023

@author: Willi
"""

import configparser
from PyQt5.QtWidgets import QFileDialog, QMessageBox

class Confighandler():
    
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.loaded = 0
        
    def save_to_config(self, module, config_dict):
        self.config[module] = config_dict
    
    def save_config(self):
        save_dlg = QFileDialog()
        save_dlg.setFileMode(QFileDialog.AnyFile)
        save_dlg.setNameFilter("Config Files(*.ini)")
        if save_dlg.exec_():
            savepath  = save_dlg.selectedFiles()
            with open (savepath, "w") as configfile:
                self.config.write(configfile)
        else:
            error_message = QMessageBox()
            error_message.setIcon(QMessageBox.Critical)
            error_message.setText("No file selected, config not saved")
        
            