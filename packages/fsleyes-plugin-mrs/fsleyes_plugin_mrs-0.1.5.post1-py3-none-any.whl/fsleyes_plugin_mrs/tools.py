#!/usr/bin/env python
#
# tools.py - Contains the Tool-related classes for loading MRSI results
# 1) MRSFitTool class - The Tool class
# 2) MRSResultsControl class - The new Control panel in OrthoView
#
# Author: Will Clarke           <william.clarke@ndcn.ox.ac.uk>
#         Vasilis Karlaftis     <vasilis.karlaftis@ndcn.ox.ac.uk>
#

import os
from pathlib import Path
import logging

import numpy as np
import wx

import fsl.utils.settings               as fslsettings
import fsl.data.image                   as fslimage
import fsleyes.actions                  as actions
import fsleyes_widgets.utils.status     as status
from fsleyes.views.orthopanel           import OrthoPanel
import fsleyes.controls.controlpanel    as ctrlpanel
import fsleyes_props                    as props

from fsleyes_plugin_mrs.views           import MRSView

log = logging.getLogger(__name__)


##################################
# MRSFitTool - load MRSI results #
##################################
class MRSFitTool(actions.Action):
    """Load MRSI results.
    Load and display fit in the MRSView display
    Add a MRSResultsControl panel to the ortho view to allow
    easy loading of metabolite maps
    """
    def __init__(self, overlayList, displayCtx, frame):
        super().__init__(overlayList, displayCtx, self.loadResults)
        self.frame = frame

    def loadResults(self):
        """Show a dialog prompting the user for a directory to load.
        Subsequently interprets results structure, causes a MRSResultsControl
        to be created and then load the fit, baseline, and residual overlays.
        """

        msg = 'Load MRSI fit directory'
        fromDir = fslsettings.read('loadSaveOverlayDir', os.getcwd())
        dlg = wx.DirDialog(wx.GetApp().GetTopWindow(),
                           message=msg,
                           defaultPath=fromDir,
                           style=wx.FD_OPEN)

        if dlg.ShowModal() != wx.ID_OK:
            return

        dirPath = Path(dlg.GetPath())
        errtitle = 'Error loading directory'
        errmsg = 'An error occurred while loading the fit directory.'
        with status.reportIfError(errtitle, errmsg, raiseError=False):
            # Steps:
            # 1. Look through the directory and identify metabolite names
            # and things that can be loaded
            self.identifyResults(dirPath)
            # 2. Define colourscheme for Results and MRSView panels
            self.identifyColourscheme(dirPath)
            # 3. Create a panel to control the loading of the possible views
            ortho = self.createResultsPanel()
            # 4. Load the fit, baseline and residual into the MRS view.
            self.loadFit(ortho)

    def identifyResults(self, dir_path):
        """Identify the metabolites used and the images available.
        Store this information for use constructing the additional panel

        :param Path dir_path: Path selected by user in DirDialog window
        """
        # Check and read if the default_mrsi.tree file exists
        self._findTreeFile(dir_path)
        # Check if the mrsi_tree is valid based on the expected keys
        ref_key = self._checkTreeValidity()
        # Get the list of metabolites and the metabolite placeholder
        self._getListOfMetabolites(ref_key)
        # Get the list of possible overlays to display based on whether they depend on the metab_ph
        self.display_options = []
        # find all keys that correspond to tree leaves (to avoid checking directories)
        for i in self.mrsi_tree.template_keys(only_leaves=True):
            if self.mrsi_tree.metab_ph in self.mrsi_tree.fill().get_template(i).placeholders():
                self.display_options.append(i)

    def _findTreeFile(self, dir_path):
        """Identify the structure of the results directory using FileTree.

        :param Path dir_path: Path selected by user in DirDialog window
        """
        from file_tree import FileTree

        tree_files = sorted([f for f in dir_path.glob('*.tree') if not f.name.startswith(".")])
        self.mrsi_tree = None
        if len(tree_files) == 0:
            log.warning(f'No .tree file found in "{dir_path}", using default structure.')
            self.mrsi_tree = FileTree.read(Path(os.path.dirname(__file__)) /
                                           'default_mrsi.tree', top_level=dir_path)
        else:
            idx = 0
            if len(tree_files) > 1:
                log.warning(f'Multiple .tree files found in "{dir_path}", selected file #{idx+1}: \
                            "{tree_files[idx].name}".')
            self.mrsi_tree = FileTree.read(tree_files[idx], top_level=dir_path)

    def _checkTreeValidity(self):
        """Check if the mrsi_tree is valid based on the expected keys.
        If not valid, raise an error.
        This function is where we declare with are the valid mandatory keys and
        returns the reference key to be used for finding all the files dependent on placeholders.
        """
        # Check if the mrsi_tree has the mandatory keys
        mandatory_keys = ['raw-concentrations']  # , 'fit-fit', 'fit-baseline', 'fit-residual']
        ref_key = None

        for key in mandatory_keys:
            if key not in self.mrsi_tree.template_keys():
                log.error(f'The mrsi_tree does not contain the mandatory "{key}" key.')
                return None
            if self.mrsi_tree.get_template(key).required_placeholders().__len__() > 0:
                ref_key = key

        return ref_key

    def _getListOfMetabolites(self, ref_key):
        """Get the list of metabolites from the mrsi_tree.
        """
        self.mrsi_tree.metab_ph = None
        self.metab_list = []

        if ref_key is None:
            log.error('No required placeholders found in the mrsi_tree.')
            return

        # Read all files in the ref_key directory (this key is mandatory to exist)
        self.mrsi_tree.update_glob(ref_key, inplace=True)
        # Find the metabolite placeholder based on the mandatory directory and store it within the tree
        # we don't use the required_placeholders() method as that reorders the placeholders alphabetically
        required_placeholders = self.mrsi_tree.fill().get_template(ref_key).placeholders()
        required_placeholders = [i for i in required_placeholders
                                 if i not in self.mrsi_tree.fill().get_template(ref_key).optional_placeholders()]
        # if multiple placeholders are found, the last one is probably the one we want
        self.mrsi_tree.metab_ph = list(required_placeholders)[-1]
        if required_placeholders.__len__() > 1:
            log.warning(f'Multiple placeholders for key: "{ref_key}". Using the last one: {self.mrsi_tree.metab_ph}.')
        # Get the list of metabolites from the files found
        if self.mrsi_tree.metab_ph in self.mrsi_tree.placeholders.keys():
            self.metab_list = self.mrsi_tree.placeholders[self.mrsi_tree.metab_ph]

    def identifyColourscheme(self, dir_path):
        # Check and read if the *colourscheme.json file exists
        colourscheme_file = self._findColourschemeFile(dir_path)
        self._checkColourschemeValidity(colourscheme_file)

    def _findColourschemeFile(self, dir_path):
        """Find the colourscheme json file.

        :param Path dir_path: Path selected by user in DirDialog window
        """
        files = sorted(dir_path.glob('*colourscheme.json'))
        if len(files) == 0:
            log.warning(f'No *colourscheme.json file found in "{dir_path}", using default colourscheme.')
            colourscheme_file = Path(os.path.dirname(__file__)) / 'default_colourscheme.json'
        else:
            idx = 0
            if len(files) > 1:
                log.warning(f'Multiple *colourscheme.json files found in "{dir_path}", \
                            selected file #{idx+1}: "{files[idx].name}".')
            colourscheme_file = files[idx]
        return colourscheme_file

    def _checkColourschemeValidity(self, file):
        """Check if the colourscheme.json is valid format.
        If not valid, raise an appropriate error.

        :param file: the location of the colourscheme file to be read
        """
        import json
        # check input colourscheme file for appropriate format
        self.colourscheme = None
        try:
            with open(file, 'r') as f:
                self.colourscheme = json.load(f)
        except FileNotFoundError:
            log.warning(f"File {file} was not found.")
        except json.JSONDecodeError as e:
            log.warning(f"File {file} is an invalid JSON format: {e}")
        except Exception as e:
            log.warning(f"Unexpected error when reading file {file}: {e}")

    def createResultsPanel(self):
        """Activate a MRSResultsControl panel, update with the metablist and display options."""
        # TODO check if there is a way to find "inactive" OrthoPanels, i.e. opened but unused for new data
        all_orthos = self.frame.getView(OrthoPanel)
        # Check if there are OrthoPanels open but no MRS data were loaded, then keep one
        create_ortho = False
        for overlay in self.frame.overlayList:
            view = self.frame.getView(MRSView)[0]
            ps = view.getDataSeries(overlay)
            if ps is not None:
                create_ortho = True
                break
        # Note: the above inherently checks if "len(self.frame.overlayList) == 0" too
        if len(all_orthos) > 0 and create_ortho is False:
            for ortho in all_orthos[1:]:
                self.frame.removeViewPanel(ortho)
            ortho = all_orthos[0]
        else:
            # Open a new Ortho panel
            ortho = self.frame.addViewPanel(OrthoPanel)  # kwargs={'location': wx.LEFT})
            # Disable all previously loaded overlays
            for overlay in self.frame.overlayList:
                display = ortho.displayCtx.getDisplay(overlay)
                display.enabled = False

        if not ortho.isPanelOpen(MRSResultsControl):
            ortho.togglePanel(MRSResultsControl)

        # Update the properties
        ortho.getPanel(MRSResultsControl).update_choices(self.metab_list, self.display_options,
                                                         self.mrsi_tree, self.colourscheme)

        self._setUpOrtho(ortho)

        return ortho

    def _setUpOrtho(self, ortho):
        """Add colour bar to ortho panel."""
        if not isinstance(ortho, OrthoPanel):
            log.error('No Ortho panel present')
            return

        orthoOpts = ortho.sceneOpts
        orthoOpts.showColourBar = True
        orthoOpts.colourBarLocation = 'left'
        orthoOpts.colourBarLabelSide = 'top-left'
        orthoOpts.labelSize = 10

    def loadFit(self, ortho):
        """Load the fit, baseline, and residual data from the fit subdir.
        Add to the overlayList and display in the MRSView panel.

        param
        """
        # override file_tree method for returning keys
        def ordered_template_keys(tree):
            from file_tree import Template
            keys = [k for (k, v) in tree._templates.items() if isinstance(v, Template)]
            return keys
        # For each fit file, find if valid display parameters exist and then display it
        fit_files = [key for key in ordered_template_keys(self.mrsi_tree) if key.startswith('fit-')]
        for fit in fit_files:
            if fit in self.colourscheme.keys():
                self._displayFitData(ortho, fit, self.colourscheme[fit])
            else:
                log.warning(f"No matching entry in colourscheme for {fit}, using defaults.")
                self._displayFitData(ortho, fit, {})

    def _displayFitData(self, ortho, file_name, params):
        # Load and add to the overlayList
        full_path = self.mrsi_tree.get(file_name)
        if not Path(full_path).exists():
            log.warning(f'{file_name} image not found in {full_path}, skipping file.')
            return
        new_img = fslimage.Image(str(full_path))
        self.frame.overlayList.append(new_img)

        # Loop through the viewPanels. If MRSView enable overlay, otherwise disable overlay
        for panel in self.frame.viewPanels:
            display = panel.displayCtx.getDisplay(self.frame.overlayList[-1])
            if isinstance(panel, MRSView):
                display.enabled = True

                # Set colour etc.
                # Get the data series
                ps = panel.getDataSeries(self.frame.overlayList[-1])
                ps.lineStyle = '-'
                ps.alpha = 1.0
                ps.lineWidth = 1
                # use every subfield specified in the json, otherwise use defaults
                for param in params.keys():
                    if hasattr(ps, param):
                        setattr(ps, param, params[param])
                    else:
                        log.warning(f"Unknown 'ps' field '{param}' for '{file_name}'.")
            else:
                display.enabled = False
        # Re-enable display in the selected Ortho Panel
        if isinstance(ortho, OrthoPanel):
            display = ortho.displayCtx.getDisplay(self.frame.overlayList[-1])
            display.enabled = True


class MRSResultsControl(ctrlpanel.SettingsPanel):
    """Control panel for the MRSI results. Allows user to easily select overlays to plot
    """

    @staticmethod
    def title():
        """Overrides :meth:`.ControlMixin.title`. Returns a title to be used
        in FSLeyes menus.
        """
        return 'MRSI map control'

    @staticmethod
    def defaultLayout():
        """Overrides :meth:`.ControlMixin.defaultLayout`. Returns arguments
        to be passed to :meth:`.ViewPanel.defaultLayout`.
        """
        return {'location': wx.BOTTOM}

    @staticmethod
    def supportedViews():
        """Overrides :meth:`.ControlMixin.supportedViews`. The
        ``MRSResultsControl`` is only intended to be added to
        :class:`.OrthoPanel` views.
        """
        return [OrthoPanel]

    def __init__(self, parent, overlayList, displayCtx, viewPanel):
        """Create a ``MRSResultsControl``.

        :arg parent:      The :mod:`wx` parent object.
        :arg overlayList: The :class:`.OverlayList` instance.
        :arg displayCtx:  The :class:`.DisplayContext` instance.
        :arg viewPanel:   The :class:`.ViewPanel` instance.
        :arg metabolites:   A list of possible metabolites.
        :arg overlay_options:   A dict of possible overlay types to load.
        """
        super().__init__(parent, overlayList, displayCtx, viewPanel)

        class propStore(props.HasProperties):
            """Class to store properties"""
            metabolite = props.Choice()
            overlay_type = props.Choice()
            replace = props.Boolean(default=True)

        self._propStore = propStore()
        self._overlay_types = None
        self._tree = None
        self._colourscheme = None
        self._previous_overlay = None

        self.refreshWidgets()

    def destroy(self):
        """Must be called when this ``MRSResultsControl`` is no
        longer needed. calls the
        :meth:`.SettingsPanel.destroy` method.
        """
        self._propStore.getProp('metabolite').removeListener(self._propStore, 'metabolite_choice_update')
        self._propStore.getProp('overlay_type').removeListener(self._propStore, 'metabolite_choice_update')
        super().destroy()

    def _generateWidgets(self, group_name):
        '''Make the widgets required for the selection of overlays.'''

        widgetList = self.getWidgetList()

        widgets = []
        metab_sel = props.makeWidget(
                widgetList,
                self._propStore,
                'metabolite')
        widgetList.AddWidget(
                metab_sel,
                displayName='Metabolite',
                tooltip="Select metabolite",
                groupName=group_name)
        widgets.append(metab_sel)

        type_sel = props.makeWidget(
                widgetList,
                self._propStore,
                'overlay_type')
        widgetList.AddWidget(
                type_sel,
                displayName='Type',
                tooltip="Select plot type",
                groupName=group_name)
        widgets.append(type_sel)

        rep_select = props.makeWidget(
                widgetList,
                self._propStore,
                'replace')
        widgetList.AddWidget(
                rep_select,
                displayName='Replace?',
                tooltip="If selected new overlays replace old ones.",
                groupName=group_name)
        widgets.append(rep_select)

        self.__widgets = widgets

    def refreshWidgets(self):
        '''Refresh the widgets for the selection of overlays.
        Run after updating the choices (using update_choices).
        '''
        widgetList = self.getWidgetList()

        if widgetList.HasGroup('mrsi_results'):
            widgetList.RemoveGroup('mrsi_results')

        # Add listeners to the properties which will cause a
        # refresh of the Info Panel.
        prop_metab = self._propStore.getProp('metabolite')
        prop_metab.addListener(
            self._propStore,
            'metabolite_choice_update',
            self._selected_result_change,
            overwrite=True)

        prop_ot = self._propStore.getProp('overlay_type')
        prop_ot.addListener(
            self._propStore,
            'metabolite_choice_update',
            self._selected_result_change,
            overwrite=True)

        widgetList.AddGroup(
            'mrsi_results',
            'MRSI Results')

        self._generateWidgets('mrsi_results')

    def update_choices(self, metabolites, overlay_types, tree, colourscheme):
        '''Update the properties (metabolites and overlay types) in the panel.'''
        # Update the metabolite list
        metabolite = self._propStore.getProp('metabolite')
        metabolite.setChoices(metabolites, instance=self._propStore)
        # Update the overlay_types
        overlay_type = self._propStore.getProp('overlay_type')
        overlay_type.setChoices(overlay_types, instance=self._propStore)

        # Store the list defining the types of files in FileTree.
        self._overlay_types = overlay_types
        self._tree = tree
        self._colourscheme = colourscheme

        # Refresh the widgets to update the GUI
        self.refreshWidgets()

    def _selected_result_change(self, *a):
        """Method called by listeners to load the selected overlay.
        If replace is true / selected then remove the previously loaded
        overlay.
        """
        if self._overlay_types is None:
            return
        if self._tree is None:
            log.error('No FileTree has been specified.')
            return

        full_path = (self._tree.update(**{self._tree.metab_ph: self._propStore.metabolite})
                               .get(self._propStore.overlay_type))

        if not Path(full_path).exists():
            log.warning(f'{full_path} image not found, skipping file.')
            return

        # If the user has the replace checkbox selected remove any previously loaded overlay
        if self._propStore.replace and self._previous_overlay is not None:
            # Remove previous overlay
            self.overlayList.remove(self._previous_overlay)

        # Load the new overlay
        new_img = fslimage.Image(str(full_path))
        self.overlayList.append(new_img)
        for panel in self.frame.getView(OrthoPanel):
            display = panel.displayCtx.getDisplay(new_img)
            display.enabled = False
        # Re-enable display in the selected Ortho Panel
        display = self.displayCtx.getDisplay(new_img)
        display.enabled = True
        self._previous_overlay = new_img
        self._set_overlay_display(self._propStore.overlay_type)
        self.displayCtx.selectOverlay(new_img)

    def _set_overlay_display(self, type):
        '''Set the display options for the loaded overlay dependent on type.'''
        overlay = self.overlayList[-1]
        display = self.displayCtx.getDisplay(overlay)
        opts = self.displayCtx.getOpts(overlay)
        nonzero = overlay.data[np.nonzero(overlay.data)]
        # global 'fixed' plot parameters and defaults
        display.alpha = 67.0
        opts.cmap = "hot"
        min_val = np.median(nonzero) - 2 * np.std(nonzero)
        max_val = np.median(nonzero) + 2 * np.std(nonzero)
        min_val = np.maximum(min_val, 0.0)
        opts.displayRange = [min_val, max_val]

        # define local function to evaluate expressions
        def eval_param(exprs, overlay):
            data = overlay.data
            nonzero = data[np.nonzero(data)]
            context = {
                "median": np.median(nonzero),
                "std": np.std(nonzero),
                "min": np.min(nonzero),
                "max": np.max(nonzero),
                "percentile": lambda p: np.percentile(nonzero, p),
            }
            return [eval(expr, {"__builtins__": {}}, context) for expr in exprs]

        # use every subfield specified in the json, otherwise use defaults
        if self._colourscheme is not None and type in self._colourscheme.keys():
            for param in self._colourscheme[type].keys():
                if hasattr(opts, param):
                    if param in ['displayRange', 'clippingRange']:
                        # skip these parameters here to allow variables that affect their behaviour
                        # to be processed first, e.g. linkLowRanges
                        continue
                    else:
                        param_val = self._colourscheme[type][param]
                    setattr(opts, param, param_val)
                else:
                    log.warning(f"Unknown 'opts' field '{param}' for '{type}'.")
            # now set these parameters
            for param in ['displayRange', 'clippingRange']:
                if param in self._colourscheme[type].keys():
                    # decode these parameters using eval expression
                    param_val = eval_param(self._colourscheme[type][param], overlay)
                    # TODO improve this line as it might not be desired
                    param_val[0] = np.maximum(param_val[0], 0.0)
                    setattr(opts, param, param_val)
        else:
            log.warning(f"No matching entry in colourscheme for {type}, using defaults.")
