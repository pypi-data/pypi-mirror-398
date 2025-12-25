import sys
import os
from numpy.typing import ArrayLike, NDArray
import numpy as np


def red_exit(string):
    cprint(string, 'red')
    sys.exit(-1)
    return


def platform_check(func):
    '''
    Decorator to check platform for color terminal output.\n
    Windows Anaconda prompt will not support colors by default, so
    colors are disabled for all windows machines, unless the
    orto_termcolor envvar is defined
    '''

    def check(*args):
        if 'nt' in os.name and not os.getenv('orto_termcolor'):
            print(args[0])
        else:
            func(*args)

    return check


def cstring(string: str, color: str) -> str:
    '''
    Returns colorised string

    Parameters
    ----------
    string: str
        String to print
    color: str {red, green, yellow, blue, magenta, cyan, white, black_yellowbg, white_bluebg} # noqa
        String name of color

    Returns
    -------
    None
    '''

    ccodes = {
        'red': '\u001b[31m',
        'green': '\u001b[32m',
        'yellow': '\u001b[33m',
        'blue': '\u001b[34m',
        'magenta': '\u001b[35m',
        'cyan': '\u001b[36m',
        'white': '\u001b[37m',
        'black_yellowbg': '\u001b[30;43m\u001b[K',
        'white_bluebg': '\u001b[37;44m\u001b[K',
        'black_bluebg': '\u001b[30;44m\u001b[K'
    }
    end = '\033[0m\u001b[K'

    # Count newlines at neither beginning nor end
    num_c_nl = string.rstrip('\n').lstrip('\n').count('\n')

    # Remove right new lines to count left new lines
    num_l_nl = string.rstrip('\n').count('\n') - num_c_nl
    l_nl = ''.join(['\n'] * num_l_nl)

    # Remove left new lines to count right new lines
    num_r_nl = string.lstrip('\n').count('\n') - num_c_nl
    r_nl = ''.join(['\n'] * num_r_nl)

    # Remove left and right newlines, will add in again later
    _string = string.rstrip('\n').lstrip('\n')

    _string = '{}{}{}{}{}'.format(l_nl, ccodes[color], _string, end, r_nl)

    return _string


@platform_check
def cprint(string: str, color: str, **kwargs):
    '''
    Prints colorised output to screen

    Parameters
    ----------
    string: str
        String to print
    color: str {red, green, yellow, blue, magenta, cyan, white}
        String name of color

    Returns
    -------
    None
    '''

    print(cstring(string, color), **kwargs)

    return


def get_opt_coords(file_name: str) -> tuple[list[str], list[float]]:
    '''
    Extracts coordinates from orca optimisation cycle

    Parameters
    ----------
    file_name: str
        Name of file to check

    Returns
    -------
    list[str]
        Labels
    list[float]
        Coordinates (3,n_atoms)
    bool
        True if stationary point found
    '''

    opt_yn = False

    n_cycles = 0

    with open(file_name, 'r') as f:
        for line in f:
            # Optimisation not finished
            if 'GEOMETRY OPTIMIZATION CYCLE' in line:
                n_cycles += 1
                labels = []
                coords = []
                for _ in range(5):
                    line = next(f)
                while len(line.split()) == 4:
                    labels.append(line.split()[0])
                    coords.append([float(val) for val in line.split()[1:]])
                    line = next(f)
            # Optimisation finished, read again
            if '*** FINAL ENERGY EVALUATION AT THE STATIONARY POINT ***' in line: # noqa
                labels = []
                coords = []
                opt_yn = True
                for _ in range(6):
                    line = next(f)
                while len(line.split()) == 4:
                    labels.append(line.split()[0])
                    coords.append([float(val) for val in line.split()[1:]])
                    line = next(f)

    if n_cycles == 0:
        red_exit(
            'Cannot find optimisation cycle coordinates in {}'.format(
                file_name
            )
        )

    return labels, coords, opt_yn


def get_input_section(file_name: str) -> str:
    '''
    Extracts Input section from orca output file
    '''

    input_str = ''

    with open(file_name, 'r') as f:
        for line in f:
            if 'INPUT FILE' in line:
                for _ in range(3):
                    line = next(f)
                while '****END OF INPUT****' not in line:
                    input_str += '{}'.format(line[line.index('> ') + 2:])
                    line = next(f)

    if not len(input_str):
        red_exit(
            'Cannot find input section in {}'.format(
                file_name
            )
        )

    return input_str


def gen_job_name(input_file: str) -> str:
    return os.path.splitext(os.path.split(input_file)[1])[0]


def gen_results_name(input_file: str) -> str:
    return '{}_results'.format(gen_job_name(input_file))


def check_envvar(var_str: str) -> None:
    '''
    Checks specified environment variable has been defined, exits program if
    variable is not defined

    Parameters
    ----------
    var_str : str
        String name of environment variable

    Returns
    -------
    None
    '''

    try:
        os.environ[var_str]
    except KeyError:
        if var_str == 'SPLASH_RAID':
            try:
                os.environ['CLOUD_ACC']
            except KeyError:
                sys.exit(f'Please set ${var_str} environment variable')
            cprint(
                'CLOUD_ACC is deprecated, replace with SPLASH_RAID in .bashrc',
                'black_yellowbg'
            )
        sys.exit(f'Please set ${var_str} environment variable')

    return


def get_envvar(var_str: str) -> str:
    '''
    Gets specified environment variable
    If undefined then returns empty string

    Parameters
    ----------
    var_str : str
        String name of environment variable

    Returns
    -------
    str
        Value of environment variable, or empty is not defined
    '''

    try:
        val = os.environ[var_str]
    except KeyError:
        val = ''

    return val


def flatten_recursive(to_flat: list[list]) -> list:
    '''
    Flatten a list of lists recursively.

    Parameters
    ----------
    to_flat: list

    Returns
    -------
    list
        Input list flattened to a single list
    '''

    if to_flat == []:
        return to_flat
    if isinstance(to_flat[0], list):
        return flatten_recursive(to_flat[0]) + flatten_recursive(to_flat[1:])
    return to_flat[:1] + flatten_recursive(to_flat[1:])


def orbname_to_mathmode(names: ArrayLike) -> NDArray:
    '''
    Converts Orca AI-LFT orbital names to mathmode strings
    '''

    to_math = {
        'dz2': r'\mathregular{d_{z^2}}',
        'dxy': r'\mathregular{d_{xy}}',
        'dxz': r'\mathregular{d_{xz}}',
        'dyz': r'\mathregular{d_{yz}}',
        'dx2-y2': r'\mathregular{d_{x^2-y^2}}',
        'fz3': r'\mathregular{f_{z^3}}',
        'fxyz': r'\mathregular{f_{xyz}}',
        'fxz': r'\mathregular{f_{xz}}',
        'fyz': r'\mathregular{f_{yz}}',
        'fz(x2-y2)': r'\mathregular{f_{z\left(x^2-y^2\right)}}',
        'fy(3x2-y2)': r'\mathregular{f_{y\left(3x^2-y^2\right)}}',
        'fx(x2-3y2)': r'\mathregular{f_{x\left(x^2-3y^2\right)}}',
    }

    mmode = np.array([
        to_math[name]
        for name in names
    ])

    return mmode


def check_font_envvar() -> None:
    '''
    Checks if orto_fontname environment variable is set, and if so
    sets matplotlib font to specified font
    '''

    import matplotlib.pyplot as plt

    if os.getenv('orto_fontname'):
        try:
            plt.rcParams['font.family'] = os.getenv('orto_fontname')
        except ValueError:
            red_exit(
                'Error setting font to {}'.format(
                    os.getenv('orto_fontname')
                )
            )

    return


def gaussian(p: ArrayLike, fwhm: float, b: float, area: float) -> NDArray:
    """
    Gaussian g(p) with given peak position (b), fwhm, and area

    g(p) = area/(c*sqrt(2pi)) * exp(-(p-b)**2/(2c**2))

    c = fwhm/(2*np.sqrt(2*np.log(2)))

    Parameters
    ----------
    p : array_like
        Continuous variable
    fwhm: float
        Full Width at Half-Maximum
    b : float
        Peak position
    area : float
        Area of Gaussian function

    Return
    ------
    list[float]
        g(p) at each value of p
    """

    c = fwhm / (2 * np.sqrt(2 * np.log(2)))

    a = 1. / (c * np.sqrt(2 * np.pi))

    gaus = a * np.exp(-(p - b)**2 / (2 * c**2))

    gaus *= area

    return gaus


def lorentzian(p: ArrayLike, fwhm, p0, area) -> NDArray:
    """
    Lotenztian L(p) with given peak position (b), fwhm, and area

    L(p) = (0.5*area*fwhm/pi) * 1/((p-p0)**2 + (0.5*fwhm)**2)

    Parameters
    ----------
    p : array_like
        Continuous variable
    fwhm: float
        Full Width at Half-Maximum
    p0 : float
        Peak position
    area : float
        Area of Lorentzian function

    Return
    ------
    list[float]
        L(p) at each value of p
    """

    lor = 0.5 * fwhm / np.pi
    lor *= 1. / ((p - p0)**2 + (0.5 * fwhm)**2)

    lor *= area

    return lor


def find_unique_substring(names):
    '''
    Finds unique substring in each name from list of names
    '''

    unique_names = []
    for name in names:
        for il, letter in enumerate(name):
            if all(oname[il] != letter for oname in names if oname != name):
                unique_names.append(name[il:])
                break
    return unique_names


def is_floatable(string: str) -> bool:
    '''
    Checks if string can be converted to float

    Parameters
    ----------
    string : str
        String to check

    Returns
    -------
    bool
        True if string can be converted to float, False otherwise
    '''

    try:
        float(string)
        return True
    except ValueError:
        return False
