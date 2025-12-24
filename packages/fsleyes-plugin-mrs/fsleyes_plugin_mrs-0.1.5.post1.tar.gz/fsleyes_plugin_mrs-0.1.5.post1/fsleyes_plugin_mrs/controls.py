#!/usr/bin/env python
#
# controls.py - Contains all Control classes:
# 1) MRSToolBar class
# 2) MRSControlPanel class
# 3) MRSDimControl class
#
# Author: Will Clarke           <william.clarke@ndcn.ox.ac.uk>
#         Vasilis Karlaftis     <vasilis.karlaftis@ndcn.ox.ac.uk>
#

import importlib
import os.path as op
import re
import wx

import fsleyes_props            as props
import fsleyes.tooltips         as fsltooltips
from fsleyes_plugin_mrs.views   import MRSView

# Imports for MRSToolBar
from fsleyes.controls           import plottoolbar
import fsleyes.icons            as icons
import fsleyes.actions          as actions
# Imports for MRSControlPanel
from fsleyes.controls           import plotcontrolpanel
from fsleyes_plugin_mrs.series  import MDComplexPowerSpectrumSeries
# Imports for MRSDimControl
import fsleyes.controls.controlpanel    as ctrlpanel
import fsl.data.image                   as fslimage

icon_dir = op.join(op.dirname(__file__), 'icons')


class MRSToolBar(plottoolbar.PlotToolBar):
    """The ``MRSToolBar`` is a toolbar for use with a
    :class:`.MRSView`. It extends :class:`.PlotToolBar`
    mostly replicates :class:`.PowerSpectrumToolBar`
    and adds a few controls specific to the :class:`.PoweSpectrumPanel`.
    """

    @staticmethod
    def title():
        """Overrides :meth:`.ControlMixin.title`. Returns a title to be used
        in FSLeyes menus.
        """
        return 'MRS toolbar'

    @staticmethod
    def supportedViews():
        """Overrides :meth:`.ControlMixin.supportedViews`. The
        ``MRSToolBar`` is only intended to be added to
        :class:`.MRSView` views.
        """
        return [MRSView]

    def __init__(self, parent, overlayList, displayCtx, psPanel):
        """Create a ``MRSToolBar``.

        :arg parent:      The :mod:`wx` parent object.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg psPanel:     The :class:`.PowerSpectrumPanel` instance.
        """

        super().__init__(
            parent, overlayList, displayCtx, psPanel)

        # Define local variables that control these actions
        # (otherwise actions need to be defined in MRSView)
        self.togControl = actions.ToggleControlPanelAction(
            overlayList, displayCtx, psPanel, MRSControlPanel)
        self.togDimControl = actions.ToggleControlPanelAction(
            overlayList, displayCtx, psPanel, MRSDimControl)

        # Create custom action buttons for toggling panels
        togControl = actions.ToggleActionButton(
            'togControl',
            actionKwargs={'floatPane': True},
            icon=[icons.findImageFile('spannerHighlight24'),
                  icons.findImageFile('spanner24')],
            tooltip='Show/hide the MRS control panel.')

        togDimControl = actions.ToggleActionButton(
            'togDimControl',
            icon=[op.join(icon_dir, 'nifti_mrs_icon-mrs_icon_highlight_thumb24.png'),
                  op.join(icon_dir, 'nifti_mrs_icon-mrs_icon_thumb24.png')],
            tooltip='Show/hide the NIfTI-MRS dimension control panel.')

        togOverlayList = actions.ToggleActionButton(
            'OverlayListPanel',
            icon=[icons.findImageFile('eyeHighlight24'),
                  icons.findImageFile('eye24')],
            tooltip='Show/hide the Overlay list panel.',
            actionKwargs={'location': wx.RIGHT})

        togPlotList = actions.ToggleActionButton(
            'PlotListPanel',
            icon=[icons.findImageFile('listHighlight24'),
                  icons.findImageFile('list24')],
            tooltip='Show/hide the Power Spectrum list panel.',
            actionKwargs={'location': wx.RIGHT})

        togControl = props.buildGUI(self, self, togControl)
        togDimControl = props.buildGUI(self, self, togDimControl)
        togOverlayList = props.buildGUI(self, psPanel, togOverlayList)
        togPlotList = props.buildGUI(self, psPanel, togPlotList)

        self.InsertTools([togControl, togDimControl, togOverlayList, togPlotList], 0)

        nav = [togControl, togDimControl, togOverlayList, togPlotList] + self.getCommonNavOrder()

        self.setNavOrder(nav)


class MRSControlPanel(plotcontrolpanel.PlotControlPanel):
    """Control panel for the MRS view.
    """

    @staticmethod
    def title():
        """Overrides :meth:`.ControlMixin.title`. Returns a title to be used
        in FSLeyes menus.
        """
        return 'MRS control panel'

    @staticmethod
    def supportedViews():
        """Overrides :meth:`.ControlMixin.supportedViews`. The
        ``MRSControlPanel`` is only intended to be added to
        :class:`.MRSView` views.
        """
        return [MRSView]

    def __init__(self, *args, **kwargs):
        """Create a ``MRSControlPanel``. All arguments are passed
        through to the :meth:`.PlotControlPanel.__init__` method.
        """
        super().__init__(*args, **kwargs)

    def destroy(self):
        """Must be called when this ``MRSControlPanel`` is no
        longer needed. Removes some property listeners and calls the
        :meth:`.PlotControlPanel.destroy` method.
        """
        super().destroy()

    # This creates a 'customPlotSettings' WidgetList
    def generateCustomPlotPanelWidgets(self, groupName):
        """Overrides :meth:`.PowerSpectrumControlPanel.generateCustomPlotPanelWidgets`
        and :meth:`.PlotControlPanel.generateCustomPlotPanelWidgets`.

        Adds some widgets for controlling the :class:`.PowerSpectrumPanel`.
        """

        psPanel = self.plotPanel
        widgetList = self.getWidgetList()
        widgetList.RenameGroup(groupName, 'MRS view plot settings')
        allWidgets = []

        psProps  = ['linkPhase', 'linkApod',
                    'plotReal', 'plotImaginary',
                    'plotMagnitude', 'plotPhase']
        strings  = ['Link 0th and 1st order phase',
                    'Link apodization',
                    'Plot real', 'Plot imaginary',
                    'Plot magnitude', 'Plot phase']
        tooltips = ['Deselect to unlink data phasing across all spectra.',
                    'Select to link apodization across all spectra.',
                    'Plot the real component of a complex image.',
                    'Plot the imaginary component of a complex image.',
                    'Plot the magnitude of a complex image.',
                    'Plot the phase of a complex image.']

        for prop, string, tips in zip(psProps, strings, tooltips):
            widg = props.makeWidget(widgetList, psPanel, prop)
            widgetList.AddWidget(
                widg,
                displayName=string,
                tooltip=tips,
                groupName=groupName)
            allWidgets.append(widg)

        return allWidgets

    # This creates a 'plotSettings' WidgetList
    def generatePlotPanelWidgets(self, groupName):
        # We want most of the parent classes implementation, but
        # remove the "smooth widget" from "Plot Settings"
        allWidgets = super().generatePlotPanelWidgets(groupName)
        # Get a list of all widget groups (i.e. WidgetList)
        widgetList = self.getWidgetList()
        # Find the list of widgets within the groupName
        my_widgets = widgetList._WidgetList__groups[groupName].widgets
        # Find the "smooth widget" and store its position in the list
        idx_to_delete = None
        for widg in my_widgets.keys():
            if my_widgets[widg].displayName == 'Smooth':
                idx_to_delete = list(my_widgets).index(widg)
                break
        # Remove the selected widget from the groupName
        if idx_to_delete is not None:
            widgetList.RemoveWidget(allWidgets[idx_to_delete], groupName)
        # have 'plotSettings' WidgetList minimised as default
        widgetList.Expand(groupName, expand=False)

        return allWidgets

    # This creates a 'currentDSSettings' WidgetList
    def generateDataSeriesWidgets(self, ps, groupName):
        # We want most of the parent classes implementation, but remove the "smooth widget" from "Plot Settings"
        allWidgets = super().generateDataSeriesWidgets(ps, groupName)
        # Get a list of all widget groups (i.e. WidgetList)
        widgetList = self.getWidgetList()
        # have 'currentDSSettings' WidgetList minimised as default
        widgetList.Expand(groupName, expand=False)

        return allWidgets

    # This creates a 'customDSSettings' WidgetList
    def generateCustomDataSeriesWidgets(self, ps, groupName):
        """Overrides :meth:`.PlotControlPanel.generateDataSeriesWidgets`.
        Adds some widgets for controlling :class:`.PowerSpectrumSeries`
        instances.
        """

        widgetList = self.getWidgetList()
        allWidgets = []

        # Create apodization numerical input field + slider
        if isinstance(ps, MDComplexPowerSpectrumSeries):
            widg = props.makeWidget(widgetList, ps, 'apodizeSeries',
                                    slider=True, showLimits=False)
            # add our desired increment step (done separately as the SliderSpinPanel doesn't handle it)
            apodize_step = 1
            widg.spinCtrl.SetIncrement(apodize_step)
            widgetList.AddWidget(widg,
                                 displayName='Apodize (in Hz)',
                                 tooltip='Apply apodization to FID data',
                                 groupName=groupName)
            allWidgets.append(widg)

        # Create normalisation checkbox
        widg = props.makeWidget(widgetList, ps, 'varNorm')
        widgetList.AddWidget(widg,
                             displayName='Normalise to [-1, 1]',
                             tooltip=fsltooltips.properties[ps, 'varNorm'],
                             groupName=groupName)
        allWidgets.append(widg)

        # Create phase correction input fields
        # step size changed from defaults to selected values below
        if isinstance(ps, MDComplexPowerSpectrumSeries):
            psProps    = ['zeroOrderPhaseCorrection',
                          'firstOrderPhaseCorrection']
            increments = [5,
                          round(1000*ps.sampleTime/10, 3)]
            strings    = ['Zero order phase correction (degrees)',
                          'First order phase correction (milliseconds)']
            tooltips   = ['Zero order phase correction',
                          'First order phase correction']
            for prop, inc, string, tips in zip(psProps, increments, strings, tooltips):
                widg = props.makeWidget(widgetList, ps, prop, increment=inc)
                widgetList.AddWidget(
                    widg,
                    displayName=string,
                    tooltip=tips,
                    groupName=groupName)
                allWidgets.append(widg)

        return allWidgets


class MRSDimControl(ctrlpanel.SettingsPanel):
    """Control panel for the MRS view. Controls access to higher dimensions
    of a NIfTI-MRS image.
    """

    @staticmethod
    def title():
        """Overrides :meth:`.ControlMixin.title`. Returns a title to be used
        in FSLeyes menus.
        """
        return 'MRS Dimension control'

    @staticmethod
    def defaultLayout():
        """Overrides :meth:`.ControlMixin.defaultLayout`. Returns arguments
        to be passed to :meth:`.ViewPanel.defaultLayout`.
        """
        return {'location': wx.RIGHT}

    @staticmethod
    def supportedViews():
        """Overrides :meth:`.ControlMixin.supportedViews`. The
        ``MRSDimControl`` is only intended to be added to
        :class:`.MRSView` views.
        """
        return [MRSView]

    def __init__(self, parent, overlayList, displayCtx, plotPanel):
        """Create a ``MRSDimControl``.

        :arg parent:      The :mod:`wx` parent object.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg psPanel:     The :class:`.PowerSpectrumPanel` instance.
        """
        super().__init__(parent, overlayList, displayCtx, plotPanel)

        self.__plotPanel = plotPanel

        displayCtx.addListener('selectedOverlay',
                               self.name,
                               self.__selectedOverlayChanged)
        overlayList.addListener('overlays',
                                self.name,
                                self.__selectedOverlayChanged)

        self.__selectedOverlay = None
        # TODO check if this is needed
        self.__selectedOverlayChanged()

    def destroy(self):
        """Must be called when this ``MRSDimControl`` is no
        longer needed. calls the
        :meth:`.PlotControlPanel.destroy` method.
        """
        self.displayCtx.removeListener('selectedOverlay', self.name)
        self.overlayList.removeListener('overlays', self.name)
        super().destroy()

    def generateDataSeriesWidgets(self, ds, groupName, dims):
        '''Create the required higher dimension spinner widgets in
        the dimension control panel.'''

        widgetList = self.getWidgetList()

        widgets_out = []
        # Add LinkDim widget first
        widg = props.makeWidget(widgetList, self.__plotPanel, 'linkDim')
        widgetList.AddWidget(
            widg,
            displayName='Link NIfTI-MRS Dimensions',
            tooltip='Select to link NIfTI-MRS Dimensions across all spectra.',
            groupName=groupName)
        widgets_out.append(widg)

        for idx in range(5, min(8, dims+1)):
            dim = props.makeWidget(
                widgetList,
                ds,
                f'dim_{idx}',
                slider=True,
                showLimits=False)
            widgetList.AddWidget(
                dim,
                displayName=f'DIM {idx}',
                tooltip=f"DIM {idx} index",
                groupName=groupName)
            widgets_out.append(dim)

            if ds.hdr_ext[f'dim_{idx}'] == 'DIM_COIL':
                # Show coil combine option only if fsl_mrs is installed
                if importlib.util.find_spec("fsl_mrs") is not None:
                    dim_avg = props.makeWidget(
                        widgetList,
                        ds,
                        f'dim_{idx}_avg')
                    widgetList.AddWidget(
                        dim_avg,
                        displayName=f'Coil combine DIM {idx}',
                        tooltip=f"Show combined coils of {idx}th dimension",
                        groupName=groupName)
                    widgets_out.append(dim_avg)
            else:
                dim_avg = props.makeWidget(
                    widgetList,
                    ds,
                    f'dim_{idx}_avg')
                widgetList.AddWidget(
                    dim_avg,
                    displayName=f'Average DIM {idx}',
                    tooltip=f"Show average of {idx}th dimension",
                    groupName=groupName)
                widgets_out.append(dim_avg)

            # Create the diff widget iff dim length is exactly 2 and not 'DIM_COIL'
            if ds.overlay.shape[idx - 1] == 2 and ds.hdr_ext[f'dim_{idx}'] != 'DIM_COIL':
                dim_diff = props.makeWidget(
                    widgetList,
                    ds,
                    f'dim_{idx}_diff')
                widgetList.AddWidget(
                    dim_diff,
                    displayName=f'Difference DIM {idx}',
                    tooltip=f"Show difference of {idx}th dimension",
                    groupName=groupName)
                widgets_out.append(dim_diff)

        return widgets_out

    def _set_dim_slider_limits(self):
        """Set the appropriate limits for each dimension index slider.
        If the dim_N_avg property is True then limit to zero."""
        overlay = self.displayCtx.getSelectedOverlay()

        if overlay is None:
            return

        ds = self.__plotPanel.getDataSeries(overlay)

        if ds is None:
            return

        for dim in range(5, min(8, overlay.ndim+1)):
            prop    = ds.getProp(f'dim_{dim}')
            is_avg  = getattr(ds, f'dim_{dim}_avg')
            is_diff = getattr(ds, f'dim_{dim}_diff')

            prop.setAttribute(ds, 'minval', 0)
            if dim <= overlay.ndim and not is_avg and not is_diff:
                prop.setAttribute(ds, 'maxval', overlay.shape[dim - 1] - 1)
            else:
                prop.setAttribute(ds, 'maxval', 0)
            if is_avg:
                ds.getProp(f'dim_{dim}_diff').disable(ds)
            else:
                ds.getProp(f'dim_{dim}_diff').enable(ds)
            if is_diff:
                ds.getProp(f'dim_{dim}_avg').disable(ds)
            else:
                ds.getProp(f'dim_{dim}_avg').enable(ds)

    def refreshDataSeriesWidgets(self):
        '''Enable/disable and set bounds on the dimensions spinners
        appropriate for the shape of the currently selected overlay.
        '''
        widgetList = self.getWidgetList()

        if self.__selectedOverlay is not None:
            self.__selectedOverlay = None

        if widgetList.HasGroup('niftiMRSDimensions'):
            widgetList.RemoveGroup('niftiMRSDimensions')

        overlay = self.displayCtx.getSelectedOverlay()

        if overlay is None:
            return

        ds = self.__plotPanel.getDataSeries(overlay)

        if ds is None:
            return

        # remove listeners of previous overlay
        if self.__selectedOverlay is not None:
            prev_ds = self.__plotPanel.getDataSeries(self.__selectedOverlay)
            for dim in range(5, min(8, self.__selectedOverlay.ndim+1)):
                self.removeListener(prev_ds, f'dim_{dim}_info_update')
                self.removeListener(prev_ds, f'dim_{dim}_avg_slider_update')
                self.removeListener(prev_ds, f'dim_{dim}_avg_info_update')
                self.removeListener(prev_ds, f'dim_{dim}_diff_slider_update')

        self.__selectedOverlay = overlay

        # Update prop limits now to ensure limits exist before
        # widgets are created
        self._set_dim_slider_limits()

        # Add listeners to the properties which will cause a
        # refresh of the Info Panel and slider limits
        for dim in range(5, min(8, overlay.ndim+1)):
            prop = ds.getProp(f'dim_{dim}')
            prop.addListener(
                ds,
                f'dim_{dim}_info_update',
                self._selectedIndexChanged,
                overwrite=True)

            prop = ds.getProp(f'dim_{dim}_avg')
            prop.addListener(
                ds,
                f'dim_{dim}_avg_slider_update',
                self._set_dim_slider_limits,
                overwrite=True)

            prop.addListener(
                ds,
                f'dim_{dim}_avg_info_update',
                self._selectedIndexChanged,
                overwrite=True)

            prop = ds.getProp(f'dim_{dim}_diff')
            prop.addListener(
                ds,
                f'dim_{dim}_diff_slider_update',
                self._set_dim_slider_limits,
                overwrite=True)

        # widgetList = self.getWidgetList()

        widgetList.AddGroup(
            'niftiMRSDimensions',
            'NIfTI-MRS Dimensions')

        dsWidgets = self.generateDataSeriesWidgets(
            ds,
            'niftiMRSDimensions',
            overlay.ndim)

        self.__dsWidgets = dsWidgets

    def refreshInfoPanel(self):
        '''Create / re-create the NIfTI-MRS information panel'''
        widgetList = self.getWidgetList()

        if widgetList.HasGroup('niftiMRSInfo'):
            widgetList.RemoveGroup('niftiMRSInfo')

        overlay = self.displayCtx.getSelectedOverlay()

        if overlay is None:
            return

        ds = self.__plotPanel.getDataSeries(overlay)

        if ds is None:
            return

        widgetList.AddGroup(
            'niftiMRSInfo',
            'NIfTI-MRS Information')

        def my_static_txt(text):
            st = wx.StaticText(widgetList,
                               label=text,
                               style=wx.ALIGN_LEFT)
            return st

        for dim in range(5, min(8, overlay.ndim+1)):
            tag = ds.hdr_ext[f'dim_{dim}']
            widgetList.AddWidget(
                my_static_txt(tag),
                f'DIM {dim} - Tag : \t\t\t',
                groupName='niftiMRSInfo')

            dim_size = overlay.shape[dim-1]
            widgetList.AddWidget(
                my_static_txt(f'{dim_size}'),
                f'DIM {dim} - Size : \t\t\t',
                groupName='niftiMRSInfo')

            # Optional dim headers
            if f'dim_{dim}_info' in ds.hdr_ext:
                widgetList.AddWidget(
                    my_static_txt(ds.hdr_ext[f'dim_{dim}_info']),
                    f"DIM {dim} - Info : \t\t\t",
                    groupName='niftiMRSInfo')

            # Process dynamic header fields
            def interpret_dyn_header(obj, index):
                if isinstance(obj, dict)\
                        and "Value" in obj:
                    return interpret_dyn_header(obj["Value"], index)
                elif isinstance(obj, list):
                    return str(obj[index])
                elif isinstance(obj, dict)\
                        and "start" in obj\
                        and "increment" in obj:
                    return str(obj['start']
                               + index * obj['increment'])
                else:
                    raise TypeError('Incorrect type for dynamic header.')

            d_hdr_str = f'dim_{dim}_header'
            if d_hdr_str in ds.hdr_ext:
                index = getattr(ds, f'dim_{dim}')
                for key in ds.hdr_ext[d_hdr_str]:
                    dim_hdr_value = interpret_dyn_header(
                        ds.hdr_ext[d_hdr_str][key], index)

                    tabs = '\t' * (2 if len(key) <= 10 else 1)
                    widgetList.AddWidget(
                        my_static_txt(dim_hdr_value),
                        f'DIM {dim} - {key} : {tabs}',
                        groupName='niftiMRSInfo')

        # Extract Nucleus and SpectrometerFrequency
        nucleus   = ds.nucleus
        spec_freq = ds.spec_freq
        specwidth = 1 / overlay.header['pixdim'][4]

        widgetList.AddWidget(
            my_static_txt(nucleus),
            'Nucleus : \t\t\t\t',
            groupName='niftiMRSInfo')

        widgetList.AddWidget(
            my_static_txt(f'{spec_freq:0.3f}'),
            'Frequency (MHz) : \t\t',
            groupName='niftiMRSInfo')

        widgetList.AddWidget(
            my_static_txt(f'{specwidth:0.0f}'),
            'Spectral width (Hz) : \t\t',
            groupName='niftiMRSInfo')

    # TODO review the need of this function when checking data format
    def _check_nifti_mrs(self):
        '''Check that the overlay selected is a valid NIfTI-MRS overlay'''

        overlay = self.displayCtx.getSelectedOverlay()
        if overlay is None:
            return False

        nifti_mrs_re = re.compile(r'mrs_v\d+_\d+')
        intent_str = overlay.header.get_intent()[2]

        # Check that file is NIfTI-MRS by looking for suitable intent string
        if isinstance(overlay, fslimage.Nifti)\
                and overlay.ndim > 3\
                and nifti_mrs_re.match(intent_str):
            return True
        else:
            return False

    def __selectedOverlayChanged(self, *a):
        """Called when the :attr:`.DisplayContext.selectedOverlay` or
        :class:`.OverlayList` changes.
        """

        # Double check that the selected overlay has
        # changed before refreshing the panel, as it
        # may not have (e.g. new overlay added, but
        # selected overlay stayed the same).
        if self.displayCtx.getSelectedOverlay() is not self.__selectedOverlay:
            self.refreshDataSeriesWidgets()
            self.refreshInfoPanel()

    def _selectedIndexChanged(self, *a):
        """Called when the dimension indices properties are changed.
        """
        self.refreshInfoPanel()
