import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.ticker import AutoMinorLocator
import numpy as np
from numpy.typing import ArrayLike
import itertools
import pathlib

from . import utils as ut
from . import data


def plot_absorption_spectrum(abs_data: data.AbsorptionData,
                             linecolor: str = 'black',
                             stickcolour: str = 'black',
                             x_lim: list[float] = ['auto', 'auto'],
                             y_lim: list[float] = [0., 'auto'],
                             x_shift: float = 0.,
                             normalise: bool = False,
                             osc_style: str = 'separate',
                             fig: plt.Figure = None, ax: plt.Axes = None,
                             oax: plt.Axes = None, save: bool = False,
                             save_name: str = 'absorption_spectrum.png',
                             show: bool = False,
                             verbose: bool = True,
                             window_title: str = 'Absorption Spectrum',
                             legend: bool = True) -> tuple[plt.Figure, plt.Axes, plt.Axes | None]: # noqa
    '''
    Plots absorption spectrum from AbsorptionSpectrum object.\n

    Parameters
    ----------
    abs_data: data.AbsorptionData
        Data object containing absorption data and spectrum
    linecolor: str, default 'black'
        Color of the continuous spectrum line
    stickcolour: str, default 'black'
        Color of the oscillator strength sticks
    x_lim: list[float], default ['auto', 'auto']
        Minimum and maximum x-values to plot
    y_lim: list[float | str], default [0., 'auto']
        Minimum and maximum y-values to plot
    normalise: bool, default False
        If True, normalise the absorption spectrum to the maximum value.
    osc_style: str, default 'separate'
        Style of oscillator strength plots:
        - 'separate': plots oscillator strengths as stems on separate axis
        - 'combined': plots oscillator strengths on intensity axis
        - 'off': does not plot oscillator strengths
    fig: plt.Figure | None, optional
        If provided, uses this Figure object for plotting
    ax: plt.Axes | None, optional
        If provided, uses this Axis object for plotting spectrum
    oax: plt.Axes | None, optional
        If provided, uses this Axis object for plotting oscillator strengths
    save: bool, default False
        If True, plot is saved to save_name
    save_name: str | pathlib.Path, default 'absorption_spectrum.png'
        If save is True, plot is saved to this location/filename
    show: bool, default False
        If True, plot is shown on screen
    verbose: bool, default True
        If True, plot file location is written to terminal
    window_title: str, default 'UV-Visible Absorption Spectrum'
        Title of figure window, not of plot
    legend: bool, default True
        If True, a legend is added to the plot
    Returns
    -------
    plt.Figure
        Matplotlib Figure object
    list[plt.Axes]
        Matplotlib Axis object for main plot followed by\n
        Matplotlib Axis object for twinx oscillator strength axis
    '''
    save_name = pathlib.Path(save_name)

    if abs_data.spectrum is None:
        raise ValueError('AbsorptionData object does not contain spectrum')

    if fig is None or ax is None:
        width = 4
        width_cm = 10.4
        golden = (1 + np.sqrt(5))/2
        fig, ax = plt.subplots(
            1,
            1,
            num=window_title,
            figsize=(width, width / golden)
        )
    else:
        width = fig.get_size_inches()[0]
        width_cm = width * 2.54

    if oax is None and osc_style == 'separate':
        oax = ax.twinx()

    if not isinstance(x_lim, list):
        raise ValueError('`x_lim` must be a list of values')

    if x_lim[0] != x_lim[1]:
        if isinstance(x_lim[0], str):
            if x_lim[0] == 'auto':
                x_lim[0] = ax.get_ylim()[0]
            elif ut.is_floatable(x_lim[0]):
                x_lim[0] = float(x_lim[0])
            else:
                raise ValueError(f'Invalid x_lim[0] value: {x_lim[0]}')
        if isinstance(x_lim[1], str):
            if x_lim[1] == 'auto':
                x_lim[1] = ax.get_ylim()[1]
            elif ut.is_floatable(x_lim[1]):
                x_lim[1] = float(x_lim[1])
            else:
                raise ValueError(f'Invalid x_lim[1] value: {x_lim[1]}')

    # Set limits and range of continuous variable
    # ax.set_xlim([x_lim[0], x_lim[1]])

    # Normalisation of spectrum
    if normalise:
        # Normalise the spectrum to the maximum value
        _y_values = abs_data.spectrum.y_values / np.max(abs_data.spectrum.y_values) # noqa
        _osc = abs_data.osc_strengths / np.max(abs_data.osc_strengths)
        ax.set_ylabel('Normalised Absorption')
    else:
        _y_values = abs_data.spectrum.y_values
        _osc = abs_data.osc_strengths
        ax.set_ylabel(abs_data.spectrum.y_label_mathmode)

    if abs_data.spectrum.x_label.split()[0].lower() == 'wavelength':
        stick_x_values = [
            wavelength + x_shift
            for wavelength in abs_data.wavelengths
        ]
    elif abs_data.spectrum.x_label.split()[0].lower() == 'energy':
        stick_x_values = [
            energy + x_shift
            for energy in abs_data.energies
        ]
    elif abs_data.spectrum.x_label.split()[0].lower() == r'wavenumber':
        stick_x_values = [
            wavenumber + x_shift
            for wavenumber in abs_data.wavenumbers
        ]

    if abs_data.spectrum.x_reversed:
        ax.invert_xaxis()

    x_values = abs_data.spectrum.x_grid + x_shift

    # Main spectrum
    ax.plot(
        x_values,
        _y_values,
        color=linecolor,
        lw=1.1,
        label=abs_data.spectrum.comment
    )

    if osc_style == 'separate':
        # Oscillator strength twin axis
        _, stemlines, _ = oax.stem(
            stick_x_values,
            _osc,
            basefmt=' ',
            markerfmt=' ',
            linefmt=stickcolour
        )
        plt.setp(stemlines, 'linewidth', 1.1)
        oax.yaxis.set_minor_locator(AutoMinorLocator())
        if normalise:
            oax.set_ylabel(r'Normalised $f_\mathregular{osc}$')
        else:
            oax.set_ylabel(r'$f_\mathregular{osc}$')
        oax.set_ylim([0., oax.get_ylim()[1]])
    elif osc_style == 'combined':
        ax.stem(
            stick_x_values,
            abs_data.osc_strengths/np.max(abs_data.osc_strengths) * np.max(_y_values), # noqa
            basefmt=' ',
            markerfmt=' ',
            linefmt=stickcolour
        )
        oax.set_yticks([])
        oax.spines['right'].set_visible(False)
        oax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
    else:
        # No oscillator strength plot
        plt.subplots_adjust(right=0.2)
        oax.set_yticks([])
        oax.spines['right'].set_visible(False)
        oax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)

    # Set y limits if specified
    _y_lim = y_lim.copy()
    if _y_lim[0] != _y_lim[1]:
        # Lower limit either auto or specified
        if isinstance(_y_lim[0], str):
            if _y_lim[0] == 'auto':
                _y_lim[0] = ax.get_ylim()[0]
            else:
                _y_lim[0] = float(_y_lim[0])
        # Upper limit either auto or specified
        if isinstance(_y_lim[1], str):
            if _y_lim[1] == 'auto':
                _y_lim[1] = ax.get_ylim()[1]
            else:
                _y_lim[1] = float(_y_lim[1])
        # Set values
        ax.set_ylim([_y_lim[0], _y_lim[1]])

    ax.xaxis.set_minor_locator(AutoMinorLocator())
    ax.yaxis.set_minor_locator(AutoMinorLocator())

    ax.set_xlabel(abs_data.spectrum.x_label_mathmode)

    fig.tight_layout()

    if legend:
        ax.legend()

    if save:
        plt.savefig(save_name, dpi=500)
        if verbose:
            ut.cprint(
                f'\nSpectrum saved to\n {save_name}',
                'cyan'
            )
            ut.cprint(
                f'Use width={width:.1f} in. or {width_cm:.1f} cm',
                'cyan'
            )

    if show:
        plt.show()

    return fig, ax, oax


def wl_to_wn(wl: float) -> float:
    if wl == 0:
        return 0.
    else:
        return 1E7 / wl


def plot_chit(chit: ArrayLike, temps: ArrayLike, fields: ArrayLike = None,
              y_unit: str = r'cm^3\,K\,mol^{-1}', # noqa
              save: bool = False, save_name: str = 'chit_vs_t.png',
              show: bool = False, window_title: str = 'Calculated Susceptibility') -> tuple[plt.Figure, plt.Axes]: # noqa
    r'''
    Plots susceptibility*T data as a function of temperature

    Parameters
    ----------
    chit: array_like
        Susceptibility * Temperature
    temps: array_like
        Temperatures in Kelvin
    fields: array_like, optional
        If specified, splits data according to applied magnetic field.\n
        One plot, with one trace per field.
    y_unit: str, default 'cm^3\ K\ mol^{-1}'
        Mathmode y-unit which matches input chit data
    save: bool, default False
        If True, plot is saved to save_name
    save_name: str, default 'chit_vs_t.png'
        If save is True, plot is saved to this location/filename
    show: bool, default False
        If True, plot is shown on screen
    window_title: str, default 'Calculated Susceptibility'
        Title of figure window, not of plot
    Returns
    -------
    plt.Figure
        Matplotlib Figure objectwidth
    plt.Axes
        Matplotlib Axis object for plot
    ''' # noqa

    # Create figure and axes
    fig, ax = plt.subplots(
        1,
        1,
        figsize=(4 * (1 + np.sqrt(5))/2, 4),
        num=window_title
    )

    if fields is None:
        # Plot data as it is
        ax.plot(temps, chit, color='k', label='Calculated')
    else:
        # Split data by field
        ufields = np.unique(fields)

        for ufield in ufields:
            _temp = temps[fields == ufield]
            _chit = chit[fields == ufield]
            ax.plot(
                _temp,
                _chit,
                label=f'Calculated ($H$ = {ufield:.1f} Oe)'
            )
        ax.legend(frameon=False)

    ax.set_xlabel('$T$ (K)')
    ax.set_ylabel(rf'$\chi T\,\mathregular{{({y_unit})}}$')

    ax.xaxis.set_minor_locator(AutoMinorLocator())
    ax.yaxis.set_minor_locator(AutoMinorLocator())

    fig.tight_layout()

    if save:
        plt.savefig(save_name, dpi=500)

    if show:
        plt.show()

    return fig, ax


def plot_ir(wavenumbers: ArrayLike, linear_absorbance: ArrayLike,
            lineshape: str = 'lorentzian', linewidth: float = 10.,
            x_lim: list[float] = [None, None],
            save: bool = False, save_name: str = 'ir.png', show: bool = False,
            window_title: str = 'Infrared spectrum'):
    '''
    Plots Infrared Spectrum

    Parameters
    ----------
    wavenumbers: array_like
        Wavenumbers of each transition [cm^-1]
    linear_absorbance: array_like
        Absorbance of each transition
    lineshape: str {'gaussian', 'lorentzian'}
        Lineshape function to use for each transition/signal
    linewidth: float
        Linewidth used in lineshape [cm^-1]
    x_lim: list[float], default [None, None]
        Minimum and maximum x-values to plot [cm^-1]
    save: bool, default False
        If True, plot is saved to save_name
    save_name: str
        If save is True, plot is saved to this location/filename
    show: bool, default False
        If True, plot is shown on screen
    window_title: str, default 'Infrared Spectrum'
        Title of figure window, not of plot
    '''

    fig, ax = plt.subplots(1, 1, num=window_title)

    ls_func = {
        'gaussian': ut.gaussian,
        'lorentzian': ut.lorentzian
    }

    if None not in x_lim:
        x_range = np.linspace(x_lim[0], x_lim[1], 100000)
    else:
        x_range = np.linspace(0, np.max(wavenumbers) * 1.1, 100000)

    # Spectrum as sum of signals. Always computed in wavenumbers.
    spectrum = np.sum([
        ls_func[lineshape](x_range, linewidth, wavenumber, a)
        for wavenumber, a in zip(wavenumbers, linear_absorbance)
    ], axis=0)

    np.savetxt('spectrum.txt', np.vstack([x_range, spectrum]).T, fmt='%.5f')

    # Main spectrum
    ax.plot(x_range, spectrum, color='k')

    ax.set_xlim([0, np.max(x_range)])

    plt.subplots_adjust(right=0.2)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

    ax.xaxis.set_minor_locator(AutoMinorLocator())
    ax.yaxis.set_minor_locator(AutoMinorLocator())

    ax.set_xlabel(r'Wavenumber (cm$^\mathregular{-1}$)')
    ax.set_ylabel(r'$\epsilon$ (cm$^\mathregular{-1}$ mol$^\mathregular{-1}$ L)') # noqa

    fig.tight_layout()

    if save:
        plt.savefig(save_name, dpi=500)

    if show:
        plt.show()

    return fig, ax


def plot_raman(wavenumbers: ArrayLike, intensities: ArrayLike,
               lineshape: str = 'gaussian', linewidth: float = 10.,
               x_lim: list[float] = 0., x_unit: str = 'wavenumber',
               abs_type: str = 'absorption', y_lim: list[float] = 'auto',
               save: bool = False, save_name: str = 'raman.png',
               show: bool = False,
               window_title: str = 'Raman spectrum'):
    '''
    Plots Raman Spectrum
    '''

    raise NotImplementedError


def plot_cd(save: bool = False, save_name: str = 'raman.png',
            show: bool = False,
            window_title: str = 'Raman spectrum'):
    '''
    Plots circular dichroism data
    '''

    raise NotImplementedError


def plot_ailft_orb_energies(energies: ArrayLike, labels: ArrayLike = None,
                            groups: ArrayLike = None,
                            occupations: ArrayLike = None,
                            y_unit: str = r'cm^{-1}',
                            save: bool = False,
                            save_name: str = 'ai_lft_energies.png',
                            show: bool = False,
                            window_title: str = 'AI-LFT Orbital Energies',
                            verbose: bool = True) -> tuple[plt.Figure, plt.Axes]: # noqa
    '''
    Parameters
    ----------
    energies: array_like
        Energies which are in same unit as y_unit
    labels: array_like | None, optional
        If provided, labels are added next to energy levels.
    groups: array_like | None, optional
        If provided, groups orbitals together by offsetting x coordinate
    occupations: array_like | None, optional
        If provided, each orbital is populated with either 0, 1 or 2 electrons
    y_unit: str, default 'cm^{-1}'
        Mathmode y-unit which matches input chit data
    save: bool, default False
        If True, plot is saved to save_name
    save_name: str, default 'ai_lft_energies.png'
        If save is True, plot is saved to this location/filename
    show: bool, default False
        If True, plot is shown on screen
    window_title: str, default 'AI-LFT Orbital Energies'
        Title of figure window, not of plot
    verbose: bool, default True
        If True, plot file location is written to terminal

    Returns
    -------
    plt.Figure
        Matplotlib Figure object
    plt.Axes
        Matplotlib Axis object for plot
    '''

    fig, ax = plt.subplots(1, 1, figsize=(3.5, 3.5), num=window_title)
    ax.yaxis.set_minor_locator(AutoMinorLocator())

    if groups is not None:
        groups = list(groups)
        groups = ut.flatten_recursive(groups)
        if len(groups) != len(energies):
            raise ValueError('Number of groups does not match number of states') # noqa
        # Split group by differing value
        groups = [list(x) for _, x in itertools.groupby(groups)]
        # X values for each group
        xvals = [list(range(len(grp))) for grp in groups]
        # Centre each group so that the middle is zero
        xvals = [g - sum(grp)/len(grp) for grp in xvals for g in grp]
    else:
        xvals = [1] * len(energies)

    ax.plot(
        xvals,
        energies,
        lw=0,
        marker='_',
        mew=1.5,
        color='k',
        markersize=25
    )

    if occupations is not None:
        if len(occupations) != len(energies):
            raise ValueError('Number of occupation numbers does not match number of states') # noqa

        # Make spin up and spin down arrow markers
        spup = mpl.markers.MarkerStyle(marker=r'$\leftharpoondown$')
        spup._transform = spup.get_transform().rotate_deg(-90)

        spdown = mpl.markers.MarkerStyle(marker=r'$\leftharpoondown$')
        spdown._transform = spdown.get_transform().rotate_deg(90)

        # Plot each marker
        for occ, en, xval in zip(occupations, energies, xvals):
            lx = xval - 1 / 10
            rx = xval + 1 / 10
            # Up and down
            if occ == 2:
                ax.scatter(lx, en, s=400, marker=spup, color='k', linewidths=0.001) # noqa
                ax.scatter(rx, en, s=400, marker=spdown, color='k', lw=0.001)
            # up
            elif occ == 1:
                ax.scatter(lx, en, s=400, marker=spup, color='k', lw=0.001)
            # down
            elif occ == -1:
                ax.scatter(rx, en, s=400, marker=spdown, color='k', lw=0.001)

    if labels is not None:
        for xval, energy, label in zip(xvals, energies, labels):
            ax.text(
                xval * 1.05,
                energy,
                rf'${label}$'
            )

    ax.set_xticklabels([])
    ax.set_xticks([])
    _lims = ax.get_xlim()
    if groups is None:
        ax.set_xlim([_lims[0]*0.9, _lims[1]*1.2])
    else:
        ax.set_xlim([_lims[0]*1.2, _lims[1]*1.2])

    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['bottom'].set_visible(False)

    ax.set_ylabel(rf'Energy $\mathregular{{({y_unit})}}$')

    fig.tight_layout()

    if save:
        plt.savefig(save_name, dpi=500)
        if verbose:
            ut.cprint(f'\nAI-LFT orbitals saved to\n{save_name}', 'cyan')

    if show:
        plt.show()
