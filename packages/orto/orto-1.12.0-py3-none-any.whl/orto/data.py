import numpy as np
from numpy.typing import NDArray, ArrayLike

from .exceptions import DataFormattingError
from . import constants as const
from . import extractor as oe
from . import utils as ut


class AbsorptionSpectrum():
    '''
    Stores absorption spectrum data

    Parameters
    ----------
    x_grid: NDArray
        Grid of x values (energies, wavelengths, or wavenumbers)
    x_unit: str
        Unit of x values: 'eV', 'nm', or 'cm^-1'
    x_label: str
        Label for x axis
    x_label_mathmode: str
        Label for x axis using LaTeX mathmode formatting
    y_unit: str
        Unit of y values, e.g. 'cm^-1 mol^-1 L'
    y_label: str
        Label for y axis
    y_label_mathmode: str
        Label for y axis using LaTeX mathmode formatting
    spectrum: NDArray
        Absorption spectrum values at each point in x_grid
    fwhm: float
        Full width at half maximum used in spectrum generation
    comment: str, default=''
        Comment or metadata for the spectrum
    x_reversed: bool, default False
        Whether the x axis is reversed (e.g. for wavelength spectra)\n
        By default, False - increasing x values from left to right

    Attributes
    ----------
    x_grid: NDArray
        Grid of x values (energies, wavelengths, or wavenumbers)
    x_unit: str
        Unit of x values: 'eV', 'nm', or 'cm^-1'
    x_label: str
        Label for x axis
    x_label_mathmode: str
        Label for x axis using LaTeX mathmode formatting
    y_unit: str
        Unit of y values, e.g. 'cm^-1 mol^-1 L'
    y_label: str
        Label for y axis
    y_label_mathmode: str
        Label for y axis using LaTeX mathmode formatting
    y_values: NDArray
        Absorption spectrum values at each point in x_grid
    fwhm: float
        Full width at half maximum used in spectrum generation
    comment: str
        Comment or metadata for the spectrum
    '''

    def __init__(self, x_grid: NDArray, x_unit: str, x_label: str,
                 x_label_mathmode: str, y_unit: str, y_label: str,
                 y_label_mathmode: str, y_values: NDArray, fwhm: float,
                 comment: str = '', x_reversed: bool = False) -> None:
        self.x_grid = x_grid
        self.x_unit = x_unit
        self.x_label = x_label
        self.x_label_mathmode = x_label_mathmode
        self.y_unit = y_unit
        self.y_label = y_label
        self.y_label_mathmode = y_label_mathmode
        self.fwhm = fwhm
        self.y_values = y_values
        self.comment = comment
        self.x_reversed = x_reversed
        return


class AbsorptionData():
    '''
    Stores absorption data for a given set of transitions

    Parameters
    ----------
    energies: array_like
        Transition energies in eV
    osc_strengths: array_like
        Oscillator strengths for each transition
    operator: str
        Type of operator used to calculate transitions

    Attributes
    ----------
    energies: list
        Transition energies in eV
    osc_strengths: list
        Oscillator strengths for each transition
    operator: str
        Type of operator used to calculate transitions
    spectrum: AbsorptionSpectrum
        Spectrum object containing spectrum curve
    wavelengths: list
        Transition wavelengths in nm
    wavenumbers: list
        Transition wavenumbers in cm^-1
    '''

    def __init__(self, energies: ArrayLike, osc_strengths: ArrayLike,
                 operator: str) -> None:
        self.energies = energies
        self.osc_strengths = osc_strengths
        self.operator = operator
        self.spectrum: None | AbsorptionSpectrum = None
        return

    @property
    def osc_strengths(self) -> list:
        '''Oscillator strengths for each transition'''
        return self._osc_strengths

    @osc_strengths.setter
    def osc_strengths(self, osc_strengths: ArrayLike) -> None:
        self._osc_strengths = list(osc_strengths)
        return

    @property
    def energies(self) -> list:
        '''Transition energies in eV'''
        return self._energies

    @energies.setter
    def energies(self, energies: ArrayLike) -> None:
        self._energies = list(energies)
        return

    @property
    def wavelengths(self) -> list:
        '''Transition wavelengths in nm'''
        return [const.EV_TO_NM / energy for energy in self.energies]

    @property
    def wavenumbers(self) -> list:
        '''Transition wavenumbers in cm^-1'''
        return [energy * const.EV_TO_WAVENUMBER for energy in self.energies]

    @property
    def spectrum(self) -> AbsorptionSpectrum:
        '''Absorption spectrum object'''
        if self._spectrum is None:
            raise ValueError(
                'Spectrum has not been generated yet\n'
                'Call generate_spectrum() first.'
            )
        return self._spectrum

    @spectrum.setter
    def spectrum(self, spectrum: AbsorptionSpectrum) -> None:
        if not isinstance(spectrum, AbsorptionSpectrum | None):
            raise TypeError('spectrum must be an AbsorptionSpectrum object')
        self._spectrum = spectrum
        return

    def trim_to_n(self, n_transitions: int) -> None:
        '''
        Trims data to given number of transitions

        Parameters
        ----------
        n_transitions: int
            Number of transitions to keep from the start of the data

        Returns
        -------
        None
        '''

        self.energies = self.energies[:n_transitions]
        self.osc_strengths = self.osc_strengths[:n_transitions]

        self.spectrum = None

        return

    @classmethod
    def from_extractor(cls, extractor: oe.AbsorptionExtractor,
                       remove_zero_osc: float = 1E-4) -> list['AbsorptionData']: # noqa
        '''
        Creates AbsorptionData object from data extractor

        Parameters
        ----------
        extractor: Extractor
            Data extractor object containing transition data
        remove_zero_osc: float, default=1E-4
            Remove transitions with oscillator strength below this value

        Returns
        -------
        list['AbsorptionData']
            AbsorptionData objects, one for each section in extractor
        '''

        all_abs_data = [
            cls.from_extractor_dataset(
                dataset,
                extractor.operator_type,
                remove_zero_osc=remove_zero_osc
            )
            for dataset in extractor.data
        ]

        return all_abs_data

    @classmethod
    def from_extractor_dataset(cls,
                               dataset: dict[str, list[int | float]],
                               operator: str,
                               remove_zero_osc: float = 1E-7) -> 'AbsorptionData': # noqa
        '''
        Creates AbsorptionData object from data extractor

        Parameters
        ----------
        dataset: dict[str, list[int | float]]
            Dataset from orto AbsorptionExtractor.data
        operator: str
            Type of operator used to calculate transitions
        remove_zero_osc: float, default=1E-7
            Remove transitions with oscillator strength below this value

        Returns
        -------
        AbsorptionData
            AbsorptionData object for dataset
        '''

        energies = dataset['energy (ev)']
        osc_strengths = dataset['fosc']

        # Remove transitions with zero oscillator strength from
        # beginning and end of spectrum
        osc_strengths = np.array(osc_strengths)

        # Find first non-zero oscillator strength
        try:
            first_nonzero = np.where(osc_strengths > remove_zero_osc)[0][0]
        except IndexError:
            raise DataFormattingError(
                'No transitions with oscillator strength above '
                f'{remove_zero_osc} found.'
            )
        # Find last non-zero oscillator strength
        last_nonzero = np.where(osc_strengths > remove_zero_osc)[0][-1]

        # Trim data
        energies = energies[first_nonzero:last_nonzero + 1]
        osc_strengths = osc_strengths[first_nonzero:last_nonzero + 1]

        return cls(energies, osc_strengths, operator)

    def generate_spectrum(self, fwhm: float, lineshape: str, x_min: float,
                          x_max: float, num_points: int,
                          x_type: str = 'energy',
                          comment: str = '',
                          x_reversed: bool = False) -> AbsorptionSpectrum:
        '''
        Generates absorption spectrum using Gaussian broadening

        Parameters
        ----------
        fwhm: float
            Full width at half maximum for Gaussian broadening\n
            in same units as x_type. Applied to each transition.
        lineshape: str
            Lineshape function to use: 'gaussian' or 'lorentzian'
        x_min: float | str
            Minimum x value for spectrum (eV, nm, or cm^-1)
        x_max: float | str
            Maximum x value for spectrum (eV, nm, or cm^-1)
        num_points: int
            Number of points in the spectrum grid
        x_type: str
            Type of x values: \n
              'energy' (eV)\n
              'wavelength' (nm)\n
              'wavenumber' (cm^-1)
        comment: str
            Comment to add to spectrum metadata
        x_reversed: bool
            Whether to reverse the x axis (e.g. for wavelength spectra)\n
            By default, False - increasing x values from left to right

        Returns
        -------
        None
        '''

        if len(self.energies) == 0 or len(self.osc_strengths) == 0:
            raise DataFormattingError(
                'No transition data available to generate spectrum.'
            )
        elif len(self.energies) != len(self.osc_strengths):
            raise DataFormattingError(
                'Energies and oscillator strengths must have the same length.'
            )

        # Set labels and x values based on x_type
        if x_type == 'energy':
            x_unit = 'eV'
            x_label = 'Energy (eV)'
            x_label_mathmode = 'Energy (eV)'
            x_vals = self.energies
        elif x_type == 'wavelength':
            x_unit = 'nm'
            x_label = 'Wavelength (nm)'
            x_label_mathmode = 'Wavelength (nm)'
            x_vals = self.wavelengths
        elif x_type == 'wavenumber':
            x_unit = 'cm^-1'
            x_label = r'Wavenumber (cm⁻¹)'
            x_label_mathmode = r'Wavenumber (cm$\mathregular{^{-1}}$)'
            x_vals = self.wavenumbers
        else:
            raise DataFormattingError(f'Invalid x_type: {x_type}')

        y_unit = 'cm mol^-1 eV^-1'
        y_label = r'ε (cm⁻¹ mol⁻¹ L))'
        y_label_mathmode = r'$\epsilon$ (cm$^\mathregular{-1}$ mol$^\mathregular{-1}$ L)'  # noqa

        # Create grid for spectrum
        x_grid = np.linspace(x_min, x_max, num_points)
        spectrum = np.zeros_like(x_grid)

        # Conversion from oscillator strength to napierian integrated
        # absorption coefficient
        # This is the value of A for a harmonically oscillating electron
        A_elec = 2.31E8
        #
        A_logs = [fosc * A_elec for fosc in self.osc_strengths]

        ls_func = {
            'gaussian': ut.gaussian,
            'lorentzian': ut.lorentzian
        }

        # Spectrum as sum of signals in given unit
        y_vals = np.sum([
            ls_func[lineshape](x_grid, fwhm, x_value, A_log)
            for x_value, A_log in zip(x_vals, A_logs)
        ], axis=0)

        # Transform y values into epsilon in cm^-1 mol^-1 L
        if x_type == 'energy':
            y_vals /= const.EV_TO_WAVENUMBER
        elif x_type == 'wavelength':
            # calc x grid in wavenumbers
            xgwn = 1E7 / x_grid
            # Calculate jacobian for non linear transformation
            jacobian = (1E7 / xgwn**2)  # d(nm)/d(cm^-1)
            # obtain y values in wavenumbers
            y_vals = y_vals * jacobian

        spectrum = AbsorptionSpectrum(
            x_grid=x_grid,
            x_unit=x_unit,
            x_label=x_label,
            x_label_mathmode=x_label_mathmode,
            y_unit=y_unit,
            y_label=y_label,
            y_label_mathmode=y_label_mathmode,
            y_values=y_vals,
            fwhm=fwhm,
            comment=comment,
            x_reversed=x_reversed
        )

        self.spectrum = spectrum

        return

    def save_spectrum_data(self, filename: str, comments: str = '') -> None:
        '''
        Saves absorption spectrum data to CSV file

        Parameters
        ----------
        filename: str
            Name of output CSV file
        comments: str
            Comments to add at the top of the file

        Returns
        -------
        None
        '''

        if self.spectrum is None:
            raise ValueError(
                'Spectrum has not been generated yet\n'
                'Call generate_spectrum() first.'
            )

        # Select x values based on x_type
        if self.spectrum.x_label.split()[0].lower() == 'energy':
            x_vals = self.spectrum.x_grid
        elif self.spectrum.x_label.split()[0].lower() == 'wavelength':
            x_vals = const.EV_TO_NM / self.spectrum.x_grid
        elif self.spectrum.x_label.split()[0].lower() == 'wavenumber':
            x_vals = self.spectrum.x_grid * const.EV_TO_WAVENUMBER

        if len(comments):
            header = comments + f'\n{self.spectrum.x_label}, ε (cm⁻¹ mol⁻¹ L))'
        else:
            header = f'{self.spectrum.x_label}, ε (cm⁻¹ mol⁻¹ L))'

        # Save to CSV
        np.savetxt(
            filename,
            np.column_stack((x_vals, self.spectrum.y_values)),
            delimiter=',',
            header=header,
            comments='#',
        )

    def save_transition_data(self, filename: str, comments: str = '') -> None:
        '''
        Saves transition data to CSV file

        Parameters
        ----------
        filename: str
            Name of output CSV file
        comments: str
            Comments to add at the top of the file

        Returns
        -------
        None
        '''

        if len(comments):
            header = comments + '\nEnergy (eV),Wavelength (nm),Wavenumber (cm⁻¹),Oscillator Strength'  # noqa
        else:
            header = 'Energy (eV),Wavelength (nm),Wavenumber (cm⁻¹),Oscillator Strength'  # noqa

        np.savetxt(
            filename,
            np.column_stack((
                self.energies,
                self.wavelengths,
                self.wavenumbers,
                self.osc_strengths
            )),
            delimiter=',',
            header=header,
            comments='#',
        )
