# -*- coding: utf-8 -*-
"""
Created on Mon Jun  5 14:54:06 2023

@author: Willi
"""
from matplotlib.widgets import SpanSelector, EllipseSelector, RectangleSelector

class selectorFactory():
    def __init__(self, Buttons:dict, parent):
        self.parent = parent
        self.Buttons = Buttons
        self.selectorLabel =  None
        self.selectorType = None
        self.Buttons["spanButton"].clicked.connect(self.setSpanSelector)
        self.Buttons["rectButton"].clicked.connect(self.setRectSelector)
        self.Buttons["ellipseButton"].clicked.connect(self.setEllipseSelector)
        
    def getSelector(self, ax, method):
        print("hi")
        self.selectorInstance = self.buildSelector(ax, method)
        return self.selectorInstance
    
    def getSelectorType(self):
        return(self.selectorType)
        
    def buildSelector(self, ax, method):
        print("hi2")
        selectorType = self.selectorType
        if not selectorType is None:
            
            if selectorType == SpanSelector:
                Selector = selectorType( #fromMPLExample
                    ax,
                    self.parent.handle1dSelectorReadout,
                    "horizontal",
                    useblit=True,
                    props=dict(alpha=0.5, facecolor="tab:blue"),
                    interactive=True,
                    drag_from_anywhere=True
                )
                
            else:
                
                Selector = selectorType( 
                    ax, 
                    self.parent.handlerectSelectorReadout,
                    useblit=True,
                    button=[1, 3],  # disable middle button
                    minspanx=5, minspany=5,
                    spancoords='pixels',
                    interactive=True)
                
                
            return Selector
    
    
    
    def buildPolySelector(self, ax, method):
        pass
            
    
    
    def setSpanSelector(self):
        if self.Buttons["spanButton"].isChecked():
            self.selectorType = SpanSelector
            self.resetAllSelectorButtons(triggerkey = "spanButton")
        else:
            self.selectorType= None
            
    def setRectSelector(self):
        if self.Buttons["rectButton"].isChecked():
            self.selectorType = RectangleSelector
            self.resetAllSelectorButtons(triggerkey = "rectButton")
        else:
            self.selectorType = None
            
    def setEllipseSelector(self):
        if self.Buttons["ellipseButton"].isChecked():
            self.selectorType= EllipseSelector
            self.resetAllSelectorButtons(triggerkey = "ellipseButton")
        else:
            self.selectorType = None
            
    def resetAllSelectorButtons(self, triggerkey = None):
        
        for key in self.Buttons:
            if not key == triggerkey:
                self.Buttons[key].setChecked(False)
            
    
   