#!/usr/bin/env python
#
# profiles.py - Contains all Profile classes:
# 1) MRSViewProfile class
#
# Author: Will Clarke           <william.clarke@ndcn.ox.ac.uk>
#         Vasilis Karlaftis     <vasilis.karlaftis@ndcn.ox.ac.uk>
#

import wx

import fsl.data.image   as fslimage
from fsleyes.profiles   import plotprofile

from matplotlib.text    import Text


class MRSViewProfile(plotprofile.PlotProfile):
    """The ``MRSViewProfile`` is a :class:`.PlotProfile` for use with the
    :class:`.MRSView`.

    In addition to the ``panzoom`` mode provided by the :class:`.PlotProfile`
    class, the ``MRSViewProfile`` class implements a ``phasing`` mode, in
    which the user is able to click/drag on a plot to change the
    zero and first order phase for the currently selected overlay.
    """

    @staticmethod
    def supportedView():
        """Returns the :class:`.MRSView` class. """
        from fsleyes_plugin_mrs.views import MRSView
        return MRSView

    @staticmethod
    def tempModes():
        """Returns the temporary mode map for the ``MRSViewProfile``,
        which controls the use of modifier keys to temporarily enter other
        interaction modes.
        """
        return {('panzoom', wx.WXK_CONTROL): 'phasing0',
                ('panzoom', wx.WXK_SHIFT): 'phasing1',
                ('panzoom', (wx.WXK_CONTROL, wx.WXK_SHIFT)): 'phasingBoth'}

    def __init__(self, viewPanel, overlayList, displayCtx):
        """Create a ``MRSViewProfile``.

        :arg viewPanel:    A :class:`.MRSView` instance.

        :arg overlayList:  The :class:`.OverlayList` instance.

        :arg displayCtx:   The :class:`.DisplayContext` instance.
        """
        super().__init__(viewPanel,
                         overlayList,
                         displayCtx,
                         ['phasing0', 'phasing1', 'phasing'])

        self._guideText = None
        self._p0 = self._p0_start = 0
        self._p1 = self._p1_start = 0
        self._tempmodetext = None
        self._startx = 0
        self._starty = 0

    def __phasingModeCompatible(self):
        """Returns ``True`` if phasing can currently be carried out, ``False``
        otherwise.
        """

        overlay = self.displayCtx.getSelectedOverlay()

        if not isinstance(overlay, fslimage.Image):
            return False

        if not overlay.iscomplex:
            return False

        if len(overlay.shape) < 4 or overlay.shape[3] == 1:
            return False

        return True

    def __updatePhase(self, xvalue, yvalue, p0, p1):
        """Called by the ``phasing`` event handlers.
        Updates the zeroth and first order phase.
        :arg xvalue: Normalised x position (0 to 1)
        :arg yvalue: Normalised y position (0 to 1)
        :arg bool p0: If true then 0th order phase will be updated
        :arg bool p1: If true then 1st order phase will be updated
        """
        if xvalue is None or yvalue is None:
            return

        mrsPanel = self.viewPanel
        if len(mrsPanel.overlayList) == 0:
            return
        overlay = self.displayCtx.getSelectedOverlay()
        ps = mrsPanel.getDataSeries(overlay)
        if ps is None:
            return

        # Transform mouse position to phase value
        if p0:
            self._p0 = round(self._p0_start + 360 * xvalue, 1)                      # in degrees
        if p1:
            self._p1 = round(self._p1_start + ps.first_order_scaling * yvalue, 3)   # in milliseconds

        # Update selected overlay's phase
        ps.zeroOrderPhaseCorrection  = self._p0
        ps.firstOrderPhaseCorrection = self._p1

    def __updateStartPhase(self):
        mrsPanel = self.viewPanel
        if len(mrsPanel.overlayList) == 0:
            return
        overlay = self.displayCtx.getSelectedOverlay()
        ps = mrsPanel.getDataSeries(overlay)
        if ps is not None:
            self._p0 = self._p0_start = ps.zeroOrderPhaseCorrection
            self._p1 = self._p1_start = ps.firstOrderPhaseCorrection

    def __createTextString(self):
        '''Create the text for the on-screen guide'''
        return f'Mode: {self._tempmodetext}\n'\
               f'0th: {self._p0:0.1f} degrees, 1st: {self._p1:0.2f} ms\n'\
               'Use ctrl for 0th only (left/right).\n'\
               'Use shift for 1st only (up/down).\n'\
               'Use ctrl+shift for both (l/r/u/d).'

    def __createText(self, draw=True):
        """Create the on screen text guide.
        :arg bool draw: If true then draw will be called at end. Defaults to True.
        """
        text = self.__createTextString()
        # Create text, use pixel positioning.
        self._guideText = Text(20, 20, text, transform=None)

        # Add to artists and draw
        canvas = self.viewPanel.canvas
        canvas.artists.append(self._guideText)
        if draw:
            canvas.drawArtists(immediate=True)

    def __removeText(self, draw=True):
        """Remove the on screen text guide.
        :arg bool draw: If true then draw will be called at end. Defaults to True.
        """
        mpl_canvas = self.viewPanel.canvas
        if self._guideText in mpl_canvas.artists:
            mpl_canvas.artists.remove(self._guideText)
            if draw:
                mpl_canvas.drawArtists(immediate=True)

    def __updateText(self):
        """Update (remove and recreate) the on screen text guide.
        Draw not called, wait for an update.
        """
        self.__removeText(draw=False)
        self.__createText(draw=False)

    def _phasingModeLeftMouseDown(self, ev, canvas, mousePos, canvasPos):
        """On first mouse down, draws on screen text guide. """

        if not self.__phasingModeCompatible():
            return

        # Get starting mouse position
        self._startx = mousePos[0]
        self._starty = mousePos[1]
        # Update starting phase correction at the start of the event
        # as it could have been changed via the control panel
        self.__updateStartPhase()
        # Create text for first time
        self.__createText()

    def _phasingModeLeftMouseDrag(self, ev, canvas, mousePos, canvasPos, p0=True, p1=True):
        """Updates the phase of the selected overlay and on screen text guide. """
        if mousePos is None:
            xvalue, yvalue = None, None
        else:
            canvas_x, canvas_y = canvas.get_width_height()
            # GetContentScaleFactor() should be the same as GetDPIScaleFactor()
            xvalue = (mousePos[0] - self._startx) / (canvas_x * canvas.GetDPIScaleFactor())
            yvalue = (mousePos[1] - self._starty) / (canvas_y * canvas.GetDPIScaleFactor())

        self.__updatePhase(xvalue, yvalue, p0, p1)

        self.__updateText()

    def _phasingModeLeftMouseUp(self, ev, canvas, mousePos, canvasPos):
        """On final mouse up, removes on screen text guide. """
        # Clear the temp mode text
        self._tempmodetext = None

        # Remove text at end of phasing
        self.__removeText()

    # Handle all the temp mode options
    # 0th order only - phasing0
    def _phasing0ModeLeftMouseDown(self, *a, **kwa):
        self._tempmodetext = '0th order only'
        self._phasingModeLeftMouseDown(*a, **kwa)

    def _phasing0ModeLeftMouseDrag(self, *a, **kwa):
        self._phasingModeLeftMouseDrag(*a, p0=True, p1=False, **kwa)

    def _phasing0ModeLeftMouseUp(self, *a, **kwa):
        self._phasingModeLeftMouseUp(*a, **kwa)

    # 1st order only - phasing1
    def _phasing1ModeLeftMouseDown(self, *a, **kwa):
        self._tempmodetext = '1st order only'
        self._phasingModeLeftMouseDown(*a, **kwa)

    def _phasing1ModeLeftMouseDrag(self, *a, **kwa):
        self._phasingModeLeftMouseDrag(*a, p0=False, p1=True, **kwa)

    def _phasing1ModeLeftMouseUp(self, *a, **kwa):
        self._phasingModeLeftMouseUp(*a, **kwa)

    # 0th and 1st order - phasingBoth
    def _phasingBothModeLeftMouseDown(self, *a, **kwa):
        self._tempmodetext = '0th & 1st order'
        self._phasingModeLeftMouseDown(*a, **kwa)

    def _phasingBothModeLeftMouseDrag(self, *a, **kwa):
        self._phasingModeLeftMouseDrag(*a, **kwa)

    def _phasingBothModeLeftMouseUp(self, *a, **kwa):
        self._phasingModeLeftMouseUp(*a, **kwa)
