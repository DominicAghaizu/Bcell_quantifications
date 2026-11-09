# -*- coding: utf-8 -*-
"""
Created on Fri Jan 27 13:33:05 2023

@author: Willi
"""
import matplotlib.pyplot as plt
from matplotlib.markers import MarkerStyle
import numpy as np


class Statsplot():
    
    def __init__(self, ax, label, canvas):
        
        self.ax = ax
        self.canvas = canvas
        
        self.mousepos_label = label
        self.hoverfirst = True
        self.lines = self.ax.get_lines()
        self.linex, self.liney = self.lines[0].get_data()
        self.canvas_bg = self.canvas.copy_from_bbox(self.canvas.figure.bbox)


    def handle_hover(self,event):

        if event.inaxes:
            if event.inaxes == self.ax:
                
                xdata = event.xdata
                ydata = event.ydata

                x_index =  next((x_ind for x_ind in range(len(self.linex)-1) if self.linex[x_ind] <= xdata and self.linex[x_ind+1] >= xdata), 15)
                liney_value = self.liney[x_index]
                print(x_index)
                print(xdata)
                print(liney_value)
                if self.hoverfirst:
                    self.visPoint, = self.ax.plot(xdata, liney_value, marker = "o", markerfacecolor = "none", markeredgecolor = "black", animated = True)
                    self.hoverfirst = False
                    self.bm = BlitManager(self.canvas, [self.visPoint])
                else: 
                    self.visPoint.set_data([xdata],[liney_value])
                self.mousepos_label.setText("X: " + str(np.around(xdata,5)) + "Y:" + str(np.around(ydata,5)))
                self.bm.update()
                

  
#Taken from the matplotlib guide on blitting https://matplotlib.org/stable/users/explain/animations/blitting.html
class BlitManager:
    def __init__(self, canvas, animated_artists=()):
        """
        Parameters
        ----------
        canvas : FigureCanvasAgg
            The canvas to work with, this only works for sub-classes of the Agg
            canvas which have the `~FigureCanvasAgg.copy_from_bbox` and
            `~FigureCanvasAgg.restore_region` methods.

        animated_artists : Iterable[Artist]
            List of the artists to manage
        """
        self.canvas = canvas
        self._bg = None
        self._artists = []

        for a in animated_artists:
            self.add_artist(a)
        # grab the background on every draw
        self.cid = canvas.mpl_connect("draw_event", self.on_draw)

    def on_draw(self, event):
        """Callback to register with 'draw_event'."""
        cv = self.canvas
        if event is not None:
            if event.canvas != cv:
                raise RuntimeError
        self._bg = cv.copy_from_bbox(cv.figure.bbox)
        self._draw_animated()

    def add_artist(self, art):
        """
        Add an artist to be managed.

        Parameters
        ----------
        art : Artist

            The artist to be added.  Will be set to 'animated' (just
            to be safe).  *art* must be in the figure associated with
            the canvas this class is managing.

        """
        if art.figure != self.canvas.figure:
            raise RuntimeError
        art.set_animated(True)
        self._artists.append(art)

    def _draw_animated(self):
        """Draw all of the animated artists."""
        fig = self.canvas.figure
        for a in self._artists:
            fig.draw_artist(a)

    def update(self):
        """Update the screen with animated artists."""
        cv = self.canvas
        fig = cv.figure
        # paranoia in case we missed the draw event,
        if self._bg is None:
            self.on_draw(None)
        else:
            # restore the background
            cv.restore_region(self._bg)
            # draw all of the animated artists
            self._draw_animated()
            # update the GUI state
            cv.blit(fig.bbox)
        # let the GUI event loop process anything it has to do
        cv.flush_events()