#!/usr/bin/env python
#
# views.py - Contains all View classes for the MRS plugin:
# 1) MRSView class - The main MRS view panel
#
# Author: Will Clarke           <william.clarke@ndcn.ox.ac.uk>
#         Vasilis Karlaftis     <vasilis.karlaftis@ndcn.ox.ac.uk>
#

import logging
import numpy as np
import seaborn as sns
import wx

import fsleyes.profiles.shortcuts       as fsleyes_shortcuts
import fsleyes.overlay                  as fsloverlay
import fsleyes_props                    as props
from fsleyes_widgets                    import elistbox
import fsl.data.image                   as fslimage

from fsleyes.views.powerspectrumpanel   import PowerSpectrumPanel
from fsleyes.views.orthopanel           import OrthoPanel
# TODO change this after fsleyes release
# from fsleyes.controls                   import overlaylistpanel
from fsleyes_plugin_mrs                 import overlaylistpanel

from fsleyes_plugin_mrs.profiles        import MRSViewProfile
from fsleyes_plugin_mrs.series          import MDComplexPowerSpectrumSeries
from fsleyes_plugin_mrs                 import constants

log = logging.getLogger(__name__)


# Add shortcuts to open MRS controls.
# Currently FSLeyes does not have an
# API for this, so we hack the shortcuts
# into the fsleyes.shortcuts module.
fsleyes_shortcuts.actions['MRSView.MRSToolBar'] = 'Ctrl-Alt-3'
fsleyes_shortcuts.actions['MRSView.MRSControlPanel'] = 'Ctrl-Alt-4'
fsleyes_shortcuts.actions['MRSView.MRSDimControl'] = 'Ctrl-Alt-5'


class MRSView(PowerSpectrumPanel):
    """The ``MRSView`` is a FSLeyes view panel for plotting data from MRS
    NIFTI images.
    """

    # Define here all new props that do not exist in parent View classes
    linkPhase     = props.Boolean(default=True)
    """If ``True`` the phase of all spectra will be linked together.
    """

    linkApod      = props.Boolean(default=False)
    """If ``True`` the apodization of all spectra will be linked together.
    """

    linkDim      = props.Boolean(default=False)
    """If ``True`` the NIfTI-MRS Dimensions of all spectra will be linked together.
    """

    plotReal      = props.Boolean(default=True)
    plotImaginary = props.Boolean(default=False)
    plotMagnitude = props.Boolean(default=False)
    plotPhase     = props.Boolean(default=False)
    """Series of properties that will dictate how to plot all
    visible MDComplexPowerSpectrumSeries"""

    zeroOrderPhaseCorrection = props.Real(default=0)
    """Apply zero order phase correction to all spectra, if linkPhase is enabled.
    """

    firstOrderPhaseCorrection = props.Real(default=0)
    """Apply first order phase correction to all spectra, if linkPhase is enabled.
    """

    apodizeSeries = props.Int(default=0, minval=0, maxval=100, clamped=True)
    """Apply apodization to all spectra, if linkApod is enabled.
    """

    dim_5      = props.Int(default=0, minval=0, maxval=0, clamped=True)
    dim_5_avg  = props.Boolean(default=False)
    dim_5_diff = props.Boolean(default=False)

    dim_6      = props.Int(default=0, minval=0, maxval=0, clamped=True)
    dim_6_avg  = props.Boolean(default=False)
    dim_6_diff = props.Boolean(default=False)

    dim_7      = props.Int(default=0, minval=0, maxval=0, clamped=True)
    dim_7_avg  = props.Boolean(default=False)
    dim_7_diff = props.Boolean(default=False)
    """Apply the higher order dimension controls to all spectra, if linkDim is enabled.
    """

    @staticmethod
    def title():
        """Overrides :meth:`.ViewPanel.title`. Returns a title to be used
        in FSLeyes menus.
        """
        return 'MRS'

    @staticmethod
    def controlOrder():
        """Overrides :meth:`.ViewPanel.controlOrder`. Returns a suggested
        ordering of control panels for the FSLeyes settings menu.
        """
        return ['OverlayListPanel',
                'PlotListPanel',
                'MRSToolBar',
                'MRSControlPanel',
                'MRSDimControl']

    @staticmethod
    def defaultLayout():
        """Overrides :meth:`.ViewPanel.defaultLayout`. Returns a list
        of control panels that should be added by default for new ``MRSView``
        views.
        """

        return ['OverlayListPanel',
                'PlotListPanel',
                'MRSToolBar',
                'MRSDimControl']

    def __init__(self, parent, overlayList, displayCtx, frame):
        """Create a ``MRSView``.

        :arg parent:      The :mod:`wx` parent object.
        :arg overlayList: The :class:`.OverlayList`.
        :arg displayCtx:  The :class:`.DisplayContext`.
        :arg frame:       The :class:`.FSLeyesFrame`.
        """

        # Change the default colours for the line plots
        self.realColours  = sns.color_palette('deep')

        super().__init__(parent, overlayList, displayCtx, frame)

        # Change the default colours for "Background" and "Grid"
        # this is done here and not in control so it persists
        self.canvas.gridColour = (0.5, 0.5, 0.5)
        self.canvas.bgColour   = (1, 1, 1)

        # Initialise NIfTI-MRS header extension
        self.hdr_ext  = None
        self.dim_size = None

        # Add listeners
        self._add_annotation_listener()
        for name in ['plotReal',
                     'plotImaginary',
                     'plotMagnitude',
                     'plotPhase']:
            self.addListener(name, self.name, self.draw)
        self.addListener('linkPhase', self.name, self.__applyLinkedPhase)
        self.addListener('linkApod',  self.name, self.__applyLinkedApodize)
        self.addListener('linkDim',   self.name, self.__applyLinkedDimControl)

        self.initProfile(MRSViewProfile)

    def destroy(self):
        """Must be called when this ``MRSView`` is no longer
        needed. Removes some property listeners, and calls
        :meth:`.OverlayPlotPanel.destroy`.
        """
        self.canvas.removeListener('dataSeries', self.name)
        for name in ['plotReal',
                     'plotImaginary',
                     'plotMagnitude',
                     'plotPhase']:
            self.removeListener(name, self.name)
        self.removeListener('linkPhase', self.name)
        self.removeListener('linkApod', self.name)
        self.removeListener('linkDim', self.name)

        super().destroy()

    def controlOptions(self, cpType):
        """Returns some options to be used by :meth:`.ViewPanel.togglePanel`
        for certain control panel types.
        """
        # Tell the overlay list panel to hide
        # all overlays that aren't being plotted.
        #
        # This OverlayPlotPanel will always be
        # notified about a new overlay before
        # this OverlayListPanel, so a DataSeries
        # instance will always have been created
        # by the time the list panel calls this
        # filter function.
        def listFilter(name, overlay):
            return self.getDataSeries(overlay) is not None

        if cpType is overlaylistpanel.OverlayListPanel:
            return dict(showVis=True,
                        showSave=False,
                        showGroup=False,
                        propagateSelect=True,
                        elistboxStyle=(elistbox.ELB_REVERSE      |
                                       elistbox.ELB_TOOLTIP_DOWN |
                                       elistbox.ELB_NO_ADD       |
                                       elistbox.ELB_NO_REMOVE    |
                                       elistbox.ELB_NO_MOVE),
                        location=wx.LEFT,
                        hideFilter=listFilter)
        
    def draw(self, *a):
        """Overrides :meth:`.PlotPanel.draw`. Draws some
        :class:`.PowerSpectrumSeries` using the
        :meth:`.PlotCanvas.drawDataSeries` method.
        """

        if not self or self.destroyed:
            return

        canvas = self.canvas
        pss = self.getDataSeriesToPlot()

        for ps in pss:
            with props.suppress(ps, 'label'):
                ps.label = ps.makeLabel()

        if len(pss) > 0:
            self._set_mrs_plot_scale(pss)

        canvas.drawDataSeries(extraSeries=pss)
        canvas.drawArtists()

    def createDataSeries(self, overlay):
        """Overrides :meth:`.OverlayPlotPanel.createDataSeries`. Creates a
        :class:`.PowerSpectrumSeries` instance for the given overlay.

        Overload the PowerSpectrumPanel definition to allow only complex
        fslimage.Image and implement the multi-dimensional
        ComplexPowerSpectrumSeries class (MDComplexPowerSpectrumSeries).
        """

        displayCtx = self.displayCtx
        overlayList = self.overlayList

        psargs = [overlay, overlayList, displayCtx, self]
        if isinstance(overlay, fslimage.Image) and overlay.ndim > 3:

            if overlay.iscomplex:
                ps = MDComplexPowerSpectrumSeries(*psargs)
            else:
                return None, None, None

            opts = displayCtx.getOpts(overlay)
            targets = [displayCtx, opts]
            propNames = ['location', 'volumeDim']

        else:
            return None, None, None

        ps.colour = self.getOverlayPlotColour(overlay)
        ps.lineStyle = '-'
        ps.lineWidth = 2
        ps.alpha = 1.0

        # when new dataseries are created, bound them to the global phase
        if self.linkPhase:
            ps.bindProps('zeroOrderPhaseCorrection', self)
            ps.bindProps('firstOrderPhaseCorrection', self)
        # when new dataseries are created, bound them to the global apodization
        if self.linkApod:
            ps.bindProps('apodizeSeries', self)
        # when new dataseries are created, bound them to the global dim controls
        if self.linkDim:
            for dim in range(5, min(len(self.dim_size), overlay.ndim)+1):
                if ps.hdr_ext[f'dim_{dim}'] == self.hdr_ext[f'dim_{dim}']\
                   and overlay.shape[dim-1] == self.dim_size[dim-1]:
                    ps.bindProps(f'dim_{dim}', self)
                    ps.bindProps(f'dim_{dim}_avg', self)
                    ps.bindProps(f'dim_{dim}_diff', self)
        return ps, targets, propNames

    def getOverlayPlotColour(self, overlay):
        """Overrides :meth:`.OverlayPlotPanel.getOverlayPlotColour`.

        Returns an initial colour to use for plots associated with the
        given overlay. If a colour is present in the  :attr:`plotColours`
        dictionary, it is returned. Otherwise a random colour is generated,
        added to ``plotColours``, and returned.
        """

        if isinstance(overlay, fsloverlay.ProxyImage):
            overlay = overlay.getBase()

        colour = self.plotColours.get(overlay)

        if colour is None:
            idx    = len(self.plotColours) % len(self.realColours)
            colour = self.realColours[idx]
            self.plotColours[overlay] = colour

        return colour

    def __applyLinkedPhase(self):
        # When linkPhase is toggled on, copy selected overlay's value to the global value
        if self.linkPhase and len(self.overlayList) > 0:
            overlay = self.displayCtx.getSelectedOverlay()
            ps = self.getDataSeries(overlay)
            if ps is not None:
                self.zeroOrderPhaseCorrection = ps.zeroOrderPhaseCorrection
                self.firstOrderPhaseCorrection = ps.firstOrderPhaseCorrection
        # Loop through all overlays that have dataseries and bind them to the global prop
        for overlay in self.overlayList:
            ps = self.getDataSeries(overlay)
            if ps is not None:
                ps.bindProps('zeroOrderPhaseCorrection', self, unbind=not self.linkPhase)
                ps.bindProps('firstOrderPhaseCorrection', self, unbind=not self.linkPhase)

    def __applyLinkedApodize(self):
        # When linkApod is toggled on, copy selected overlay's value to the global value
        if self.linkApod and len(self.overlayList) > 0:
            overlay = self.displayCtx.getSelectedOverlay()
            ps = self.getDataSeries(overlay)
            if ps is not None:
                self.apodizeSeries = ps.apodizeSeries
        # Loop through all overlays that have dataseries and bind them to the global prop
        for overlay in self.overlayList:
            ps = self.getDataSeries(overlay)
            if ps is not None:
                ps.bindProps('apodizeSeries', self, unbind=not self.linkApod)

    def __applyLinkedDimControl(self):
        # When linkDim is toggled on, copy selected overlay's value to the global value
        if self.linkDim and len(self.overlayList) > 0:
            overlay = self.displayCtx.getSelectedOverlay()
            ps = self.getDataSeries(overlay)
            if ps is not None:
                self.hdr_ext    = ps.hdr_ext
                self.dim_size   = overlay.shape
                for dim in range(5, min(8, overlay.ndim+1)):
                    # expand the maxval of the global prop to allow non-zero values
                    self.getProp(f'dim_{dim}').setAttribute(self, 'maxval', overlay.shape[dim - 1] - 1)
                    setattr(self, f'dim_{dim}',      getattr(ps, f'dim_{dim}'))
                    setattr(self, f'dim_{dim}_avg',  getattr(ps, f'dim_{dim}_avg'))
                    setattr(self, f'dim_{dim}_diff', getattr(ps, f'dim_{dim}_diff'))
                # rename overlay list to indicate which one is used for linkDim
                display = self.displayCtx.getDisplay(overlay)
                display.name += ' (Link Dim ref)'
            else:
                self.hdr_ext    = None

        # Loop through all overlays that have dataseries and bind/unbind them to the global prop
        # if they have the same dim tag and size
        for overlay in self.overlayList:
            ps = self.getDataSeries(overlay)
            if ps is not None and self.hdr_ext is not None:
                for dim in range(5, min(len(self.dim_size), overlay.ndim)+1):
                    if ps.hdr_ext[f'dim_{dim}'] == self.hdr_ext[f'dim_{dim}']\
                       and overlay.shape[dim-1] == self.dim_size[dim-1]:
                        ps.bindProps(f'dim_{dim}',      self, unbind=not self.linkDim)
                        ps.bindProps(f'dim_{dim}_avg',  self, unbind=not self.linkDim)
                        ps.bindProps(f'dim_{dim}_diff', self, unbind=not self.linkDim)

        # When linkDim is toggled off, then reset the global variables
        if not self.linkDim:
            self.hdr_ext    = None
            self.dim_size   = None
            for dim in range(5, 8):
                self.getProp(f'dim_{dim}_avg').enable(self)
                setattr(self, f'dim_{dim}_avg', 0)
                self.getProp(f'dim_{dim}_diff').enable(self)
                setattr(self, f'dim_{dim}_diff', 0)
                setattr(self, f'dim_{dim}', 0)
            # update overlay list names to remove any linkDim ref indication
            for overlay in self.overlayList:
                display = self.displayCtx.getDisplay(overlay)
                if display.name.endswith(' (Link Dim ref)'):
                    display.name = display.name.replace(' (Link Dim ref)', '')

        # refresh MRSView legend names
        self.canvas.draw()

    def _set_mrs_plot_scale(self, pss):
        nuclei = []
        spec_freq = []
        for ps in pss:
            if isinstance(ps, MDComplexPowerSpectrumSeries):
                nuclei.append(ps.nucleus)
                spec_freq.append(ps.spec_freq)

        # TODO improve the structure / logic by combining cases
        all_ps_match = True
        if len(nuclei) > 1:
            if nuclei[0] is None:
                all_ps_match = False
            else:
                for nn in nuclei[1:]:
                    if nn != nuclei[0]:
                        all_ps_match = False
                        # TODO add break
        if len(spec_freq) > 1:
            if spec_freq[0] is None:
                all_ps_match = False
            else:
                for sf in spec_freq[1:]:
                    if sf is not None and not np.isclose(sf, spec_freq[0], atol=1):
                        all_ps_match = False

        canvas = self.canvas
        # TODO handle what happens in the else case
        if all_ps_match and canvas.xAutoScale:
            canvas.xAutoScale = False

            # Calculate and set x scaling
            canvas.xScale = -1 / spec_freq[0]

            # Apply x offset
            known_nuclei = constants.GYRO_MAG_RATIO.keys()
            if nuclei[0] in known_nuclei:
                canvas.xOffset = constants.PPM_SHIFT[nuclei[0]]
            else:
                print(f'Unknown nucleus {nuclei[0]}.')
                canvas.xOffset = 0.0

            canvas.invertX = True
            if nuclei[0] in known_nuclei:
                extra_range = 0.1 * (constants.PPM_RANGE[nuclei[0]][1] - constants.PPM_RANGE[nuclei[0]][0])
                canvas.limits = [
                    constants.PPM_RANGE[nuclei[0]][1] + extra_range,
                    constants.PPM_RANGE[nuclei[0]][0] - extra_range,
                    canvas.limits[2],
                    canvas.limits[3]]
            else:
                # Force redraw.
                canvas.limits = canvas.limits

    # TODO restructure this listener
    def _add_annotation_listener(self):
        pcanvas = self.canvas

        ortho = self.frame.getView(OrthoPanel)
        if len(ortho) == 0:
            log.error('No Ortho panel present')
            return
        else:
            # Assume only 1 ortho panel
            ortho = ortho[0]

        xcanvas = ortho.getXCanvas()
        ycanvas = ortho.getYCanvas()
        zcanvas = ortho.getZCanvas()
        self.dsannotations = {}

        def dataSeriesColourChanged(*a):
            '''Function called to change an annotation colour if
            the dataseries colour is changed.
            '''
            # Argument 0 is the colour changed to,
            # Argument 2 is the dataseries
            colour = a[0]
            edited_ds = a[2]
            for anno in self.dsannotations[edited_ds]:
                anno.colour = colour

            xcanvas.Refresh()
            ycanvas.Refresh()
            zcanvas.Refresh()

        def dataSeriesChanged(*a):
            '''Function called to add annotations on addition of a dataseries'''
            # remove annotation for any newly removed data series
            for ds in self.dsannotations:
                if ds not in pcanvas.dataSeries:
                    xa, ya, za = self.dsannotations.pop(ds)
                    xcanvas.getAnnotations().dequeue(xa, hold=True)
                    ycanvas.getAnnotations().dequeue(ya, hold=True)
                    zcanvas.getAnnotations().dequeue(za, hold=True)

                    # 2. Remove listener for colour changes
                    ds.removeListener('colour', f'{ds.name}_colour')

                    break  # To avoid changing the dictionary size during iteration.

            # create an annotation for any newly added data series
            for ds in pcanvas.dataSeries:
                if ds not in self.dsannotations:
                    # 1. Add annotation to ortho canvases
                    xpos, ypos, zpos = self.displayCtx.location
                    xa = xcanvas.getAnnotations().ellipse(ypos, zpos, 2, 2, colour=ds.colour, hold=True)
                    ya = ycanvas.getAnnotations().ellipse(xpos, zpos, 2, 2, colour=ds.colour, hold=True)
                    za = zcanvas.getAnnotations().ellipse(xpos, ypos, 2, 2, colour=ds.colour, hold=True)
                    self.dsannotations[ds] = [xa, ya, za]

                    # 2. Add listener for colour changes
                    ds.addListener('colour', f'{ds.name}_colour', dataSeriesColourChanged, weak=False)

            xcanvas.Refresh()
            ycanvas.Refresh()
            zcanvas.Refresh()

        # Add listener for new dataseries
        pcanvas.addListener('dataSeries', self.name, dataSeriesChanged, weak=False)
