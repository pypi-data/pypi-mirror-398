#!/usr/bin/env python
#
# series.py - Contains all data series classes for the MRS plugin:
# 1) MDComplexPowerSpectrumSeries class - The Power Spectrum Series in Power Spectra View
#
# Author: Will Clarke           <william.clarke@ndcn.ox.ac.uk>
#         Vasilis Karlaftis     <vasilis.karlaftis@ndcn.ox.ac.uk>
#

import numpy as np
from numpy import fft
import json
import importlib
import colorsys

import fsleyes_props                        as props
import fsleyes.plotting.powerspectrumseries as psseries
import fsl.utils.idle                       as idle
import fsl.utils.cache                      as cache
from fsleyes_widgets.utils.typedict         import TypeDict

import inspect
import logging
log = logging.getLogger(__name__)


class MDComplexPowerSpectrumSeries(psseries.VoxelPowerSpectrumSeries):
    '''Sub class of ComplexPowerSpectrumSeries to overload the
       dataAtCurrentVoxel method'''

    dim_5      = props.Int(default=0, clamped=True)
    dim_5_avg  = props.Boolean(default=False)
    dim_5_diff = props.Boolean(default=False)

    dim_6      = props.Int(default=0, clamped=True)
    dim_6_avg  = props.Boolean(default=False)
    dim_6_diff = props.Boolean(default=False)

    dim_7      = props.Int(default=0, clamped=True)
    dim_7_avg  = props.Boolean(default=False)
    dim_7_diff = props.Boolean(default=False)
    """Higher order dimension indices."""

    # MRSControlPanel 'customDSSettings' properties.

    # slider for apodize is created with fixed limits. if needed
    # to modify dynamically, then a _set_apodize_slider_limits
    # function should be defined in MRSControlPanel
    apodizeSeries = props.Int(default=0, minval=0, maxval=100, clamped=True)
    """Apply apodization to the power spectrum of the complex data."""

    zeroOrderPhaseCorrection  = props.Real(default=0)
    """Apply zero order phase correction to the power spectrum of the complex data."""

    firstOrderPhaseCorrection = props.Real(default=0)
    """Apply first order phase correction to the power spectrum of the complex data."""

    def __init__(self, overlay, overlayList, displayCtx, plotCanvas):
        super().__init__(overlay, overlayList, displayCtx, plotCanvas)
        # Separate DataSeries for the imaginary/
        # magnitude/phase signals, returned by
        # the extraSeries method
        self.__imagps = psseries.ImaginaryPowerSpectrumSeries(
            self, overlay, overlayList, displayCtx, plotCanvas)
        self.__magps = psseries.MagnitudePowerSpectrumSeries(
            self, overlay, overlayList, displayCtx, plotCanvas)
        self.__phaseps = psseries.PhasePowerSpectrumSeries(
            self, overlay, overlayList, displayCtx, plotCanvas)
        for ps in (self.__imagps, self.__magps, self.__phaseps):
            ps.bindProps('alpha',     self)
            ps.bindProps('lineWidth', self)
            ps.bindProps('lineStyle', self)

        # Needs it's own cache or a hack around the name mangling
        self.__cache = cache.Cache(maxsize=1000)

        # read the nucleus and spectral frequency from the header info
        self._getHeaderInfo()
        # calculate first order phase correction scaling factor
        self._calcFirstOrderScaling()

        # Add colour listener
        self.addListener('colour', self.name, self.setProjColours)

    def setProjColours(self):
        multipliers = {
            'pastel': (1.5614, 1.3885, -0.0134),
            'dark':   (1.5000, 0.5298,  0.0101),
            'bright': (2.5189, 0.9058,  0.0047),
        }
        h, l, s = colorsys.rgb_to_hls(*self.colour[:3])

        colour_palette = {}
        for name, (s_mul, l_mul, hue_off) in multipliers.items():
            new_s = max(0.0, min(1.0, s * s_mul))
            new_l = max(0.0, min(1.0, l * l_mul))
            new_h = (h + hue_off) % 1.0
            r, g, b = colorsys.hls_to_rgb(new_h, new_l, new_s)
            # if colour is too close to white, then apply adjustment
            brightness = 0.299 * r + 0.587 * g + 0.114 * b
            if brightness > 0.95:
                new_s = min(1.0, new_s * 1.1)   # boost saturation
                new_l = max(0.0, new_l * 0.9)   # reduce lightness
                r, g, b = colorsys.hls_to_rgb(new_h, new_l, new_s)

            colour_palette[name] = (r, g, b)

        self.__imagps.colour  = colour_palette['pastel']
        self.__magps.colour   = colour_palette['dark']
        self.__phaseps.colour = colour_palette['bright']

    def destroy(self):
        super().destroy()
        self.removeListener('colour', self.name)

    def _getHeaderInfo(self):
        try:
            # Extract NIfTI-MRS header extensions
            curr_hdr_exts   = self.overlay.header.extensions
            hdr_ext_codes   = curr_hdr_exts.get_codes()
            hdr_ext         = json.loads(curr_hdr_exts[hdr_ext_codes.index(44)].get_content())
            # Extract Nucleus and SpectrometerFrequency
            self.nucleus    = hdr_ext['ResonantNucleus'][0]
            self.spec_freq  = hdr_ext['SpectrometerFrequency'][0]
            self.hdr_ext    = hdr_ext
        except Exception as e:
            self.nucleus    = None
            self.spec_freq  = None
            self.hdr_ext    = None
            if hasattr(self.overlay, 'name'):
                log.error(f"Error in reading header for overlay '{self.overlay.name}': {e}")
            else:
                log.error(f"Error in reading header: {e}")

    def _calcFirstOrderScaling(self):
        if self.nucleus == '1H' and self.spec_freq is not None and self.spec_freq > 0:
            self.first_order_scaling = 1000 / (2 * 2.65 * self.spec_freq)
        else:
            self.first_order_scaling = 1000 * 4 * self.sampleTime

    def extraSeries(self):
        """Returns a list of additional series to be plotted, based
        on the values of the :attr:`plotImaginary`, :attr:`plotMagnitude`
        and :attr:`plotPhase` properties.
        """
        extras = []
        if self.plotCanvas.plotImaginary: extras.append(self.__imagps)
        if self.plotCanvas.plotMagnitude: extras.append(self.__magps)
        if self.plotCanvas.plotPhase:     extras.append(self.__phaseps)
        return extras

    # TODO consider overriding this to manipulate the label format
    def makeLabelBase(self):
        """Returns a string to be used as the label prefix for this
        ``ComplexPowerSpectrumSeries`` instance, and for the imaginary,
        magnitude, and phase child series.
        """
        return psseries.VoxelPowerSpectrumSeries.makeLabel(self)

    def makeLabel(self):
        """Returns a label to use for this data series."""
        labels = TypeDict({'MDComplexPowerSpectrumSeries': 'real',
                           'ImaginaryPowerSpectrumSeries': 'imaginary',
                           'MagnitudePowerSpectrumSeries': 'magnitude',
                           'PhasePowerSpectrumSeries':     'phase'})
        return '{} ({})'.format(self.makeLabelBase(), labels[self])

    def getData(self, component='real'):
        """If :attr:`plotReal` is true, returns the real component of the power
        spectrum of the data at the current voxel. Otherwise returns ``(None,
        None)``.

        Every time this method is called, the power spectrum is retrieved (see
        the :class:`VoxelPowerSpectrumSeries` class), phase correction is
        applied if set, andthe data is normalised, if set. A tuple containing
        the ``(xdata, ydata)`` is returned, with ``ydata`` containing the
        requested ``component`` ( ``'real'``, ``'imaginary'``,
        ``'magnitude'``, or ``'phase'``).

        This method is called by the :class:`ImaginarySpectrumPowerSeries`,
        :class:`MagnitudeSpectrumPowerSeries`, and
        :class:`PhasePowerSpectrumPowerSeries` instances that are associated
        with this data series.
        """
        prop_parent = self.plotCanvas
        if ((component == 'real')      and (not prop_parent.plotReal))      or \
           ((component == 'imaginary') and (not prop_parent.plotImaginary)) or \
           ((component == 'magnitude') and (not prop_parent.plotMagnitude)) or \
           ((component == 'phase')     and (not prop_parent.plotPhase)):
            return None, None

        # See VoxelPowerSpectrumSeries - the data
        # is already fourier-transformed
        ydata = self.dataAtCurrentVoxel()

        if ydata is None:
            return None, None

        # All of the calculations below are repeated
        # for each real/imag/mag/phase series that
        # gets plotted. But keeping the code together
        # and clean is currently more important than
        # performance, as there is not really any
        # performance hit.
        overlay = self.overlay
        xdata   = psseries.calcFrequencies(overlay.shape[3],
                                           self.sampleTime,
                                           overlay.dtype)

        if self.zeroOrderPhaseCorrection  != 0 or \
           self.firstOrderPhaseCorrection != 0:
            ydata = psseries.phaseCorrection(ydata,
                                             xdata,
                                             self.zeroOrderPhaseCorrection,
                                             self.firstOrderPhaseCorrection/1000)

        # Normalise magnitude, real, imaginary
        # components with respect to magnitude.
        # Normalise phase independently.
        if self.varNorm:
            mag = psseries.magnitude(ydata)
            mr  = mag.min(), mag.max()
            if component == 'real':        ydata = psseries.normalise(ydata.real, *mr)
            elif component == 'imaginary': ydata = psseries.normalise(ydata.imag, *mr)
            elif component == 'magnitude': ydata = psseries.normalise(mag)
            elif component == 'phase':     ydata = psseries.normalise(psseries.phase(ydata))

        elif component == 'real':      ydata = ydata.real
        elif component == 'imaginary': ydata = ydata.imag
        elif component == 'magnitude': ydata = psseries.magnitude(ydata)
        elif component == 'phase':     ydata = psseries.phase(ydata)

        return xdata, ydata

    # The PlotPanel uses a new thread to access
    # data every time the displayContext location
    # changes. So we mark this method as mutually
    # exclusive to prevent multiple
    # near-simultaneous accesses to the same voxel
    # location. The first time that a voxel location
    # is accessed, its data is cached. So when
    # subsequent (blocked) accesses execute, they
    # will hit the cache instead of hitting the disk
    # (which is a good thing).
    @idle.mutex
    def dataAtCurrentVoxel(self):
        """Returns the data for the current voxel of the overlay.  This method
        is intended to be used within the :meth:`DataSeries.getData` method
        of sub-classes.

        An internal cache is used to avoid the need to retrieve data for the
        same voxel multiple times, as retrieving data from large compressed
        4D images can be time consuming.

        The location for the current voxel is calculated by the
        :meth:`currentVoxelLocation` method, and the data lookup is performed
        by the :meth:`currentVoxelData` method. These methods may be
        overridden by sub-classes.

        :returns: A ``numpy`` array containing the data at the current
                  voxel, or ``None`` if the current location is out of bounds
                  of the image.
        """

        location = self.currentVoxelLocation(with_time_dim=False)
        if location is None:
            return None
        cache_key = location + (self.apodizeSeries, )

        try:
            data = self.__cache.get(cache_key, None)
        except TypeError:
            # Handle TypeError: unhashable type: 'slice'
            data = None

        if data is None:
            data = self.currentVoxelData(self.currentVoxelLocation())
            try:
                self.__cache.put(cache_key, data)
            except TypeError:
                # Handle TypeError: unhashable type: 'slice'
                pass

        return data

    def currentVoxelLocation(self, with_time_dim=True):
        """Used by :meth:`dataAtCurrentVoxel`. Returns the current voxel
        location. This is used as a key for the voxel data cache implemented
        within the :meth:`dataAtCurrentVoxel` method, and subsequently passed
        to the :meth:`currentVoxelData` method.

        This implements the higher dimension indexing

        If with_time_dim is True (default) then a slice(None) is inserted as
        a fourth dimension.
        """

        opts = self.displayCtx.getOpts(self.overlay)
        voxel = opts.getVoxel()

        if voxel is None:
            return None

        higher_dim_idx = []
        for idx in range(5, 8):
            if getattr(self, f'dim_{idx}_avg'):
                higher_dim_idx.append(slice(None))
            elif getattr(self, f'dim_{idx}_diff'):
                higher_dim_idx.append(slice(0, 2))
            else:
                higher_dim_idx.append(getattr(self, f'dim_{idx}'))

        if with_time_dim:
            return tuple(voxel + [slice(None), ] + higher_dim_idx)
        else:
            return tuple(voxel + higher_dim_idx)

    def currentVoxelData(self, location):
        """Used by :meth:`dataAtCurrentVoxel`. Returns the data at the
        specified location.

        This method may be overridden by sub-classes.
        """

        data = self.overlay[location].copy()

        # Take mean of averaged dimensions
        reduced_loc = [x for x in location[-3:]]
        dim = 0
        for idx, loc in enumerate(reduced_loc):
            if loc == slice(None):
                if self.hdr_ext is not None and self.hdr_ext[f'dim_{idx+5}'] == 'DIM_COIL':
                    # Apply coil combine only if fsl_mrs is installed
                    if importlib.util.find_spec("fsl_mrs") is not None:
                        from fsl_mrs.utils.preproc import combine

                        # this method iterates over data higher dimensions
                        # simplified from nifti_mrs.iterate_over_dims
                        def iterate_over_dims(data, dim=1):
                            # Move FID dim to last
                            data = np.moveaxis(data, 0, -1)
                            dim -= 1
                            # Move identified dim to last (this should be the DIM_COIL dimension)
                            data = np.moveaxis(data, dim, -1)

                            # assuming iterate_over_space == True
                            iteration_skip = -2

                            for idx in np.ndindex(data.shape[:iteration_skip]):
                                yield data[idx], tuple([slice(None), ] + list(idx))

                        temp_data = data[:, 0].copy()
                        dim += 1
                        for main, idx in iterate_over_dims(data, dim):
                            temp_data[idx] = combine.combine_FIDs(main, 'svd')
                        data = np.expand_dims(temp_data, axis=dim)
                else:
                    dim += 1
                    data = np.mean(data, axis=dim, keepdims=True)
            elif loc == slice(0, 2):
                dim += 1
                data = np.diff(data, axis=dim)

        data = data.squeeze()
        # Apply apodization before calculating the spectrum
        if self.apodizeSeries != 0:
            data = apodize(data, self.sampleTime, self.apodizeSeries)

        return calcSpectrum(data)


def calcSpectrum(data):
    """Calculates a spectrum for the given one-dimensional data array.
    Includes scaling of first FID point.

    :arg data:    Numpy array containing the time series data

    :returns:     The complex spectrum is returned.
    """
    # Check if input arguments have the correct datatype
    func_name = inspect.currentframe().f_code.co_name
    if not isinstance(data, np.ndarray):
        raise TypeError(f"{func_name}: data must be a numpy array, got {type(data)}.")
    # Fourier transform on complex data
    data[0] *= 0.5
    data = fft.fft(data)
    data = fft.fftshift(data)

    return data


def apodize(FID, dwelltime, broadening):
    """ Apodize FID

    Args:
        FID (ndarray): Time domain data
        dwelltime (float): dwelltime in seconds
        broadening (float): apodisation in Hz
        filter (str,optional):'exp','l2g'

    Returns:
        FID (ndarray): Apodised FID
    """
    # Check if input arguments have the correct datatype
    func_name = inspect.currentframe().f_code.co_name
    if not isinstance(FID, np.ndarray):
        raise TypeError(f"{func_name}: FID must be a numpy array, got {type(FID)}.")
    if not isinstance(dwelltime, (float, int)):
        raise TypeError(f"{func_name}: dwelltime must be a float or int, got {type(dwelltime)}.")
    if not isinstance(broadening, (float, int)):
        raise TypeError(f"{func_name}: broadening must be a float or int, got {type(broadening)}.")
    if broadening <= 0:
        log.warning(f"{func_name}: broadening must be positive, got {broadening}. No change in input data.")
        return FID
    # Apply exponential apodization
    taxis = np.linspace(0, dwelltime * (FID.size - 1), FID.size)
    Tl = 1 / broadening
    window = np.exp(-taxis / Tl)
    return window * FID
