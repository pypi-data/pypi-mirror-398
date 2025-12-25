import numpy.linalg as la
import numpy as np
from numpy.typing import NDArray
import xyz_py as xyzp
import extto
import re
import pandas as pd
from io import StringIO
import pathlib
import copy
from abc import abstractmethod

from .exceptions import DataFormattingError
from . import constants as const


def EPRNMRDetector(file_name: str | pathlib.Path) -> bool:
    '''
    Detects if Orca output file contains an EPRNMR section
    '''
    with open(file_name, 'rb') as f:
        file_content = f.read()

    if re.search(rb'%EPRNMR', file_content):
        return True
    else:
        return False


class OrcaVersionExtractor(extto.LineExtractor):
    '''
    Extracts Orca version from Orca output file
    '''

    # Regex Start Pattern
    PATTERN = rb'Program Version\s+\d\.\d\.\d'

    MODIFIERS = [re.IGNORECASE]

    @property
    def data(self) -> list[list[int]]:
        '''
        Orca version, one per match
        Version number is stored as [major, minor, patch]
        '''
        return self._data

    @staticmethod
    def _process_block(block: str) -> list[int]:
        '''
        Converts single block into data entries described in self.data

        Parameters
        ----------
        block: str
            String block extracted from file

        Returns
        -------
        int
            Number of cores
        '''

        version = re.findall(r'(\d\.\d\.\d)', block)[0]

        version = version.replace('.', '')

        version = [int(v) for v in version]

        return version

    @classmethod
    def extract(cls, file_name: str | pathlib.Path) -> list[int]:
        '''
        Convenience method which instantiates class, extracts blocks, and
        returns processed datasets

        Parameters
        ----------
        file_name: str | pathlib.Path
            File to parse

        Returns
        -------
        list[int]
            Orca version as [major, minor, patch]
        '''
        _ext = cls()
        _ext(file_name, process=True)
        return _ext.data[0]


def get_coords(file_name: str | pathlib.Path, coord_type: str = 'init',
               index_style: str = 'per_element') -> tuple[list, NDArray]:
    '''
    Extracts cartesian coordinates and atom labels from Orca output file

    Parameters
    ----------
    file_name: str | pathlib.Path
        Orca output file to parse
    coord_type: str, {'init', 'opt'}
        Specifies which set of coordinates to extract\n
        Options are:\n
        "init" = Initial coordinates\n
        "opt" = Final optimised coordinates
    index_style: str {'per_element', 'sequential', 'sequential_orca', 'none'}
        Specifies what type of atom label indexing used for final atom labels\n
        Options are:\n
        'per_element' = Index by element e.g. Dy1, Dy2, N1, N2, etc.\n
        'sequential' = Index the atoms 1->N regardless of element\n
        'sequential_orca' = Index the atoms 0->N-1 regardless of element\n
        'none' = No label indexing

    Returns
    -------
    list
        Atomic labels
    ndarray of floats
        (n_atoms,3) array containing xyz coordinates of each atom
    '''

    labels, coords = [], []

    with open(file_name, 'r') as f:
        for line in f:
            if 'CARTESIAN COORDINATES (ANGSTROEM)' in line:
                labels, coords = [], []
                line = next(f)
                line = next(f)
                while len(line.lstrip().rstrip()):
                    labels.append(line.split()[0])
                    coords.append([float(val) for val in line.split()[1:4]])
                    line = next(f)
                if coord_type.lower() == 'init':
                    break

    if not len(labels):
        raise ValueError(f'Cannot find coordinates in {file_name}')

    if index_style in ['per_element', 'sequential']:
        labels = xyzp.add_label_indices(labels, style=index_style)
    elif index_style == 'sequential_orca':
        labels = xyzp.add_label_indices(
            labels, style='sequential', start_index=0
        )
    else:
        labels = xyzp.remove_label_indices(labels)

    return labels, np.asarray(coords)


class SusceptibilityExtractor(extto.BetweenExtractor):
    '''
    Extracts Magnetic Susceptibility as a function of temperature
    '''

    # Modifiers for line/block extraction
    MODIFIERS = [re.MULTILINE]

    # Regex Start Pattern
    START_PATTERN = rb'(?<=-{59}$\s{8}TEMPERATURE DEPENDENT MAGNETIC SUSCEPTIBILITY\s{8}-{59}[\S\s]{182})' # noqa

    # Regex End Pattern
    END_PATTERN = rb'(?=-{59}$)'

    @property
    def data(self) -> list[pd.DataFrame]:
        '''
        Processed susceptibility data, one dataframe per extracted block.\n
        For each entry, column titles are \n
         - Static Field (Gauss)\n
         - Temperature (K)\n
         - M/B: chi*T (cm3*K/mol)\n
         - chi*T (cm3*K/mol)\n
        '''
        return self._data

    @staticmethod
    def _process_block(block: str) -> pd.DataFrame:
        '''
        Converts single block into array of susceptibility as a function of
        temperature

        Parameters
        ----------
        block: str
            String block extracted from file

        Returns
        -------
        pd.DataFrame
            Susceptibility dataframe with columns described in self.data
        '''

        _ext = re.compile(
            r'\s*(\d+\.\d+)\s+(\d+\.\d+)\s+(----|\d+\.\d+)\s+(\d+\.\d+)\s*'
        )

        data = pd.DataFrame(_ext.findall(block), index=None)
        data.columns = [
            'Static Field (Gauss)',
            'Temperature (K)',
            'M/B: chi*T (cm3*K/mol)',
            'chi*T (cm3*K/mol)'
        ]
        data['M/B: chi*T (cm3*K/mol)'] = pd.to_numeric(
            data['M/B: chi*T (cm3*K/mol)'],
            errors='coerce'
        )
        data = data.astype(float)

        return data

    @classmethod
    def extract(cls, file_name: str | pathlib.Path) -> list[pd.DataFrame]:
        '''
        Convenience method which instantiates class, extracts blocks, and
        returns processed datasets

        Parameters
        ----------
        file_name: str | pathlib.Path
            File to parse

        Returns
        -------
        list[pd.DataFrame]
            Each entry contains processed data, as defined in cls.data
        '''
        _ext = cls()
        _ext(file_name, process=True)
        return _ext.data


class ExchangeCouplingExtractor(extto.BetweenExtractor):
    '''
    Extracts Exchange Coupling Constants and information (J) from Orca \n
    output file
    '''

    # Regex Start Pattern
    START_PATTERN = rb'(?<=BROKEN SYMMETRY MAGNETIC COUPLING ANALYSIS\s-{42})' # noqa

    # Regex End Pattern
    END_PATTERN = rb'(?=Ginsberg)'

    @property
    def data(self) -> list[dict[str, float]]:
        '''
        Processed Exchange coupling analysis, one dict per block
        For each list entry, keys are \n
         - S(High-Spin)\n
         - <S**2>(High-Spin)\n
         - <S**2>(BrokenSym)\n
         - E(High-Spin) (Eh)\n
         - E(BrokenSym) (Eh)\n
         - E(High-Spin)-E(BrokenSym) (cm^-1)
         - J(1) (cm^-1)
         - J(2) (cm^-1)
         - J(3) (cm^-1)
        '''
        return self._data

    @staticmethod
    def _process_block(block: str) -> dict[str, float]:
        '''
        Converts single block into array of susceptibility as a function of
        temperature

        Parameters
        ----------
        block: str
            String block extracted from file

        Returns
        -------
        dict[str, float]
            Keys described in self.data
        '''

        data = {
            'S(High-Spin)': float(re.findall(
                r'S\(High-Spin\) *= *(\d*\.\d*)',
                block
            )[0]),
            '<S**2>(High-Spin)': float(re.findall(
                r'<S\*\*2>\(High-Spin\) *= *(\d*\.\d*)',
                block
            )[0]),
            '<S**2>(BrokenSym)': float(re.findall(
                r'<S\*\*2>\(BrokenSym\) *= *(\d*\.\d*)',
                block
            )[0]),
            'E(High-Spin) (Eh)': float(re.findall(
                r'E\(High-Spin\) *= *(-\d*\.\d*) Eh',
                block
            )[0]),
            'E(BrokenSym) (Eh)': float(re.findall(
                r'E\(BrokenSym\) *= *(-\d*\.\d*) Eh',
                block
            )[0]),
            'E(High-Spin)-E(BrokenSym) (cm^-1)': float(re.findall(
                r'E\(High-Spin\)-E\(BrokenSym\)= *-?\d*.\d* eV *(-?\d*\.\d*) *cm\*\*-1', # noqa
                block
            )[0]),
            'J(1) (cm^-1)': float(re.findall(
                r'J\(1\) *= *(-?\d*\.\d*)',
                block
            )[0]),
            'J(2) (cm^-1)': float(re.findall(
                r'J\(2\) *= *(-?\d*\.\d*)',
                block
            )[0]),
            'J(3) (cm^-1)': float(re.findall(
                r'J\(3\) *= *(-?\d*\.\d*)',
                block
            )[0])
        }

        return data

    @classmethod
    def extract(cls, file_name: str | pathlib.Path) -> list[dict[str, float]]:
        '''
        Convenience method which instantiates class, extracts blocks, and
        returns processed datasets

        Parameters
        ----------
        file_name: str | pathlib.Path
            File to parse

        Returns
        -------
        list[dict[str, float]]
            Each entry contains processed data, as defined in cls.data
        '''
        _ext = cls()
        _ext(file_name, process=True)
        return _ext.data


class AILFTOrbEnergyExtractor(extto.BetweenExtractor):
    '''
    Extracts AI-LFT orbital energies from Orca output file
    '''
    # Regex Start Pattern
    START_PATTERN = rb'(?<=The ligand field one electron eigenfunctions:\s-{41})' # noqa

    # Regex End Pattern
    END_PATTERN = rb'(?=Ligand field orbitals were stored in)'

    MODIFIERS = [re.MULTILINE]

    @property
    def data(self) -> list[dict[str, NDArray]]:
        '''
        AI-LFT one electron eigenvalues and eigenfunctions, one dict per block
        For each dict, keys are \n
         - energy (cm^-1)\n
         - eigenvectors\n
         - orbitals
        and all values are numpy arrays of shape (n_orbs, n_orbs)\n
        or just n_orbs\n
        '''
        return self._data

    @staticmethod
    def _process_block(block: str) -> dict[str, NDArray]:
        '''
        Converts single block into data entries described in self.data

        Parameters
        ----------
        block: str
            String block extracted from file

        Returns
        -------
        dict[str, NDArray]
            Keys described in self.data
        '''

        energies = re.findall(
            r'\s+\d\s+\d\.\d{3}\s+(\d+\.\d)',
            block
        )
        energies = np.array([float(energy) for energy in energies])

        n_orbs = len(energies)

        vectors = re.findall(
            rf'\s+\d\s+\d\.\d{{3}}\s+\d+\.\d((?:\s+\-?\d\.\d{{6}}){{{n_orbs:d}}})', # noqa
            block
        )

        vectors = np.array([
            [float(ve) for ve in vector.split()]
            for vector in vectors
        ]).T

        names = re.findall(
            rf'Orbital\s+Energy\s+\(eV\)\s+Energy\s?\(cm-1\)((?:\s+[A-Za-z\d-]*){{{n_orbs:d}}})', # noqa
            block
        )
        names = np.array([na.rstrip().lstrip() for na in names[0].split()])

        data = {
            'energies (cm^-1)': energies,
            'eigenvectors': vectors,
            'orbitals': names
        }

        return data

    @classmethod
    def extract(cls, file_name: str | pathlib.Path) -> list[dict[str, NDArray]]: # noqa
        '''
        Convenience method which instantiates class, extracts blocks, and
        returns processed datasets

        Parameters
        ----------
        file_name: str | pathlib.Path
            File to parse

        Returns
        -------
        list[dict[str, NDArray]]
            Each entry contains processed data, as defined in cls.data
        '''
        _ext = cls()
        _ext(file_name, process=True)
        return _ext.data


class FrequencyExtractor(extto.BetweenExtractor):
    '''
    Extracts Vibrational mode energies, eigenvectors, intensities, \n
    and irreps from Orca output file
    '''

    # Regex Start Pattern
    START_PATTERN = rb'(?<=VIBRATIONAL FREQUENCIES\s-{23})'

    # Regex End Pattern
    END_PATTERN = rb'(?=The first frequency considered to be a vibration)'

    MODIFIERS = [re.MULTILINE]

    @property
    def data(self) -> list[dict[str, NDArray]]:
        '''
        Processed IR SPECTRUM data, one dict per block
        For each dict, keys are \n
         - frequency (cm^-1)\n
         - displacements - shape: (n_atoms, 3 * n_atoms, 3)\n
         - epsilon (L mol^-1 cm^-1)\n
         - IR Intensity (km mol^-1)\n
         - tx\n
         - ty\n
         - tz\n
         - irrep\n
        and all values are numpy arrays.\n
        Dimensions are n_atoms*3, 1 for all arrays other than displacements.
        '''
        return self._data

    @staticmethod
    def _process_block(block: str) -> dict[str, NDArray]:
        '''
        Converts single block into data entries described in self.data

        Parameters
        ----------
        block: str
            String block extracted from file

        Returns
        -------
        dict[str, NDArray]
            Keys described in self.data
        '''

        # Extract Frequencies (wavenumber)
        freq_pattern = re.compile(
            r' *\d*: *(-?\d*\.\d*) cm\*\*-1'
        )
        wavenumbers = np.array(
            [float(val) for val in freq_pattern.findall(block)]
        )

        # Check if symmetry is enabled by searching for
        # "Point group" in block
        if re.search(r'Point group', block):
            symmetry = True
        else:
            symmetry = False

        n_atoms = len(wavenumbers) // 3

        # Displacements section can be different depending on symmetry
        if symmetry:
            displacement_pattern = re.compile(
                r'(?: +\d+){1,10}\s(?: +\d+\-[A-Za-z]+[0-9]*[A-Za-z]*){1,10}\s((?: +\d+ +(?: +-?\d\.\d{6}){1,10}\s)*)' # noqa
            )
        else:
            displacement_pattern = re.compile(
                r'(?: +\d+){1,6} +\s((?: +\d+ +(?: +-?\d\.\d{6}){1,6}\s)*)'
            )

        # Extract Displacements
        disp_table = re.findall(
            displacement_pattern,
            block
        )

        # and combine in a single dataframe
        all_df = [
            pd.read_csv(
                StringIO(dt),
                sep=r'\s+',
                index_col=[0],
                header=None,
                skipinitialspace=True,
            )
            for dt in disp_table
        ]
        # Combine list of dataframe chunks into a single dataframe
        combined_df = pd.concat(all_df, axis=1, join='outer')

        # convert to numpy array
        disp_array = combined_df.to_numpy()
        # and reshape
        disp_x = disp_array[0::3, :]
        disp_y = disp_array[1::3, :]
        disp_z = disp_array[2::3, :]
        disp = np.zeros((n_atoms, n_atoms * 3, 3))
        disp[:, :, 0] = disp_x
        disp[:, :, 1] = disp_y
        disp[:, :, 2] = disp_z

        # Extract TX, TY, and TZ and calculate epsilon
        tx_pattern = re.compile(
            r'\(([ -]?\d\.\d{6}) *-?\d\.\d{6} *-?\d\.\d{6}\)'
        )
        ty_pattern = re.compile(
            r'\([ -]?\d\.\d{6} *(-?\d\.\d{6}) *-?\d\.\d{6}\)'
        )
        tz_pattern = re.compile(
            r'\([ -]?\d\.\d{6} *-?\d\.\d{6} *(-?\d\.\d{6})\)'
        )

        tx = np.asarray(
            [float(val) for val in tx_pattern.findall(block)]
        )
        ty = np.asarray(
            [float(val) for val in ty_pattern.findall(block)]
        )
        tz = np.asarray(
            [float(val) for val in tz_pattern.findall(block)]
        )

        # t values are missing for first n_zero modes and for imaginary modes
        n_missing = len(wavenumbers) - len(tx)
        z_arr = np.zeros(n_missing)
        tx = np.concatenate((z_arr, tx))
        ty = np.concatenate((z_arr, ty))
        tz = np.concatenate((z_arr, tz))

        # This is the T2 printed by ORCA
        # (Dipole derivative wrt to MWC)**2 * vibrational overlap**2
        # units of e^2 a0^2
        t2 = tx ** 2 + ty ** 2 + tz ** 2

        # Calculate T
        # units of e^2 a0^2
        t = np.sqrt(t2)

        # Remove vibrational overlap
        # in atomic units
        # b^2 = hbar/(2*c*nubar) --> 1/(2*nubar)
        # m_e^-1/2 a_0
        b2 = np.zeros_like(wavenumbers)
        b2[n_missing:] = 1 / (2 * const.HARTREE2INVERSE_CM * wavenumbers[n_missing:]) # noqa
        # divide by sqrt(b2)
        # to give units of e m_e^-1/2
        t[n_missing:] /= np.sqrt(b2[n_missing:])

        # Convert to SI
        # First convert electrons to coulombs
        t *= const.ELECTRON_CHARGE

        # and then reciprocal atomic mass units (m_e^-1/2) to kg^-1/2
        t *= (const.ELECTRON_MASS)**-0.5

        # Calculate A_e in units of m mol^-1
        # this is "Intensity" in Orca
        ae = np.ones_like(wavenumbers)
        ae[:n_missing] = 0
        ae *= const.AVOGADRO / (12 * const.EPSILON_0 * const.SPEED_OF_LIGHT_M_S**2) # noqa
        ae[n_missing:] *= t[n_missing:] ** 2
        # and convert to km mol^-1
        ae[n_missing:] /= 1000

        # Convert absorbance to linear
        alin = ae / np.log(10)

        # Convert to units of 1000 cm mol^-1
        eps = alin * 100

        # Get irreducible representations
        if symmetry:
            irrep_pattern = re.compile(
                r'(?: +\d+){1,10}\s((?: +\d+\-[A-Za-z]+[0-9]*[A-Za-z]*){1,10}\s)(?: +\d+ +(?: +-?\d\.\d{6}){1,10}\s)*' # noqa
            )
            irrep_blocks = re.findall(
                irrep_pattern,
                block
            )
            irreps = np.concatenate([
                [
                    irrep
                    for irrep in iblock.replace('\n', '').split()
                ]
                for iblock in irrep_blocks
            ])
        else:
            irreps = np.array([''] * len(wavenumbers))

        data = {
            'energy (cm^-1)': wavenumbers,
            'displacements': disp,
            'epsilon (L mol^-1 cm^-1)': eps,
            'IR Intensity (km mol^-1)': ae,
            't2 (a.u.^2)': t2,
            'tx (a.u.)': tx,
            'ty (a.u.)': ty,
            'tz (a.u.)': tz,
            'irrep': irreps
        }

        return data

    @classmethod
    def extract(cls, file_name: str | pathlib.Path) -> list[dict[str, NDArray]]: # noqa
        '''
        Convenience method which instantiates class, extracts blocks, and
        returns processed datasets

        Parameters
        ----------
        file_name: str | pathlib.Path
            File to parse

        Returns
        -------
        list[dict[str, NDArray]]
            Each entry contains processed data, as defined in cls.data
        '''
        _ext = cls()
        _ext(file_name, process=True)
        return _ext.data


class LoewdinPopulationExtractor(extto.BetweenExtractor):
    '''
    Extracts Loewdin Population Analysis Section from Orca output file
    '''

    # Regex Start Pattern
    START_PATTERN = rb'(?<=LOEWDIN ATOMIC CHARGES AND SPIN DENSITIES\s-{41}\s)'

    # Regex End Pattern
    END_PATTERN = rb'(?=-{50})'

    @property
    def data(self) -> list[tuple[dict[str, float], dict[str, float]]]:
        '''
        Processed Loewdin Population Analysis data\n
        Each data entry is a tuple containing two dictionaries:\n\n

        First dict is charges, second is spin density. In both cases\n
        keys are atomic symbol with (0-)index post-appended e.g "Cr0" "H22"\n
        and values are float value of charge or spin density\n
        '''
        return self._data

    @staticmethod
    def _process_block(block: str) -> tuple[dict[str, float], dict[str, float]]: # noqa
        '''
        Converts single block into data entries described in self.data

        Parameters
        ----------
        block: str
            String block extracted from file

        Returns
        -------
        tuple[dict[str, float], dict[str, float]]
            First dict is charges, second is spin density. In both cases\n
            keys are atomic symbol with (0-)index post-appended\n
                e.g "Cr0" "H22"\n
            values are float value of charge or spin density\n
        '''

        raw = re.findall(
            r'\s*(\d+)\s*([A-Za-z]*)\s*:\s+(-?\d\.\d{6})\s*(-?\d\.\d{6})',
            block
        )
        charges = {
            f'{val[1]}{val[0]}': float(val[2])
            for val in raw
        }

        spins = {
            f'{val[1]}{val[0]}': float(val[3])
            for val in raw
        }

        return (charges, spins)

    @classmethod
    def extract(cls, file_name: str | pathlib.Path) -> list[tuple[list[dict[str, float]], list[float]]]: # noqa
        '''
        Convenience method which instantiates class, extracts blocks, and
        returns processed datasets

        Parameters
        ----------
        file_name: str | pathlib.Path
            File to parse

        Returns
        -------
        list[tuple[list[dict[str, float]], list[float]]]
            Each entry contains processed data, as defined in cls.data
        '''
        _ext = cls()
        _ext(file_name, process=True)
        return _ext.data


class MullikenPopulationExtractorDensities(LoewdinPopulationExtractor):
    '''
    Extracts Mulliken Population Analysis Section with \n
    MULLIKEN ATOMIC CHARGES AND SPIN DENSITIES header\n
    from Orca output file`
    '''

    # Regex Start Pattern
    START_PATTERN = rb'(?<=MULLIKEN ATOMIC CHARGES AND SPIN DENSITIES\s-{42}\s)' # noqa

    # Regex End Pattern
    END_PATTERN = rb'(?=-{51})'


class MullikenPopulationExtractorPopulations(LoewdinPopulationExtractor):
    '''
    Extracts Mulliken Population Analysis Section with \n
    MULLIKEN ATOMIC CHARGES AND SPIN POPULATIONS header\n
    from Orca output file
    '''

    # Regex Start Pattern
    START_PATTERN = rb'(?<=MULLIKEN ATOMIC CHARGES AND SPIN POPULATIONS\s-{44}\s)' # noqa

    # Regex End Pattern
    END_PATTERN = rb'(?=-{51})'


class MullikenPopulationExtractor(MullikenPopulationExtractorDensities):
    '''
    Extracts Mulliken Population Analysis Section from Orca output file
    '''


class LoewdinCompositionExtractor(extto.BetweenExtractor):
    '''
    Extracts Loewdin Orbital-Compositions Section from Orca output file
    '''

    # Regex Start Pattern
    START_PATTERN = rb'(?<=LOEWDIN ORBITAL-COMPOSITIONS\s-{28}\s)'

    # Regex End Pattern
    END_PATTERN = rb'(?=-{28})'

    @property
    def data(self) -> tuple[pd.DataFrame, list[float], list[float]]:
        '''
        Processed Loewdin orbital data\n
        Each data entry is a tuple containing:\n
            First entry - a pandas dataframe with MO as columns\n and AO as rows\n # noqa
            Second entry - a list of occupation numbers, one float per MO\n
            Third entry - a list of orbital energies, one float per MO
        '''
        return self._data

    @staticmethod
    def _process_block(block: str) -> tuple[pd.DataFrame, list[float], list[float]]: # noqa
        '''
        Converts single block into data entries described in self.data

        Parameters
        ----------
        block: str
            String block extracted from file

        Returns
        -------
        tuple[pd.DataFrame, list[float], list[float]]
            First entry - a pandas dataframe with MO as columns\n and AO as rows\n # noqa
            Second entry - a list of occupation numbers, one float per MO\n
            Third entry - a list of orbital energies, one float per MO
        '''

        # Extract each <=5 orbital sub block
        _patt = re.compile(
            r'\n{2,}'
        )
        _sub_blocks = _patt.split(block)
        _sub_blocks = [
            sb.lstrip().rstrip()
            for sb in _sub_blocks
            if len(sb.lstrip().rstrip())
        ]

        # and process into lists
        occupancies = []
        energies = []
        all_df = []

        # Extract each <=5 orbital sub block as a table
        # and append to list of table chunks
        for _sub_block in _sub_blocks:
            [_header, _, _table] = re.split(r'\s(:?--------\s+)+', _sub_block)

            _orb_nos = [
                int(val)
                for val in _header.split('\n')[0].split()
            ]

            _df = pd.read_csv(
                StringIO(_table), sep=r'\s+',
                header=None,
                engine='python',
                index_col=None
            )

            # Change entries in dataframe to be cols of
            # atom number, atom label, and AO
            _df.rename(
                columns={
                    0: 'atom_number',
                    1: 'atom_label',
                    2: 'AO'
                },
                inplace=True
            )

            # Set these as the index cols
            _df.set_index(['atom_number', 'atom_label', 'AO'], inplace=True)

            # and title the rest with the orbital numbers
            _df.columns = _orb_nos
            # and append to the list of dataframes
            all_df.append(_df)

            # extract orbital energies
            for val in _header.split('\n')[1].split():
                energies.append(
                    float(val)
                )

            # extract orbital occupancies
            for val in _header.split('\n')[2].split():
                occupancies.append(
                    float(val)
                )

        # combine list of dataframe chunks into a single dataframe
        combined_df = pd.concat(all_df, axis=1, join='outer')
        combined_df = combined_df.fillna(0)

        return combined_df, occupancies, energies

    @classmethod
    def extract(cls, file_name: str | pathlib.Path) -> list[tuple[pd.DataFrame, list[float], list[float]]]: # noqa
        '''
        Convenience method which instantiates class, extracts blocks, and
        returns processed datasets

        Parameters
        ----------
        file_name: str | pathlib.Path
            File to parse

        Returns
        -------
        list[tuple[pd.DataFrame, list[float], list[float]]]
            Each entry contains processed data, as defined in cls.data
        '''
        _ext = cls()
        _ext(file_name, process=True)
        return _ext.data


class LoewdinOrbitalPopulationExtractor(extto.BetweenExtractor):
    '''
    Extracts Loewdin Orbital-Populations Per MO Section from output\n
    file. ONLY READS SPIN UP BLOCKS\n
    '''

    # Regex Start Pattern
    START_PATTERN = rb'(?<=LOEWDIN ORBITAL POPULATIONS PER MO\s-{34}\s)'

    # Regex End Pattern
    END_PATTERN = rb'(?=-{42})'

    @property
    def data(self) -> tuple[pd.DataFrame, list[float], list[float]]:
        '''
        Processed Loewdin orbital data\n
        Each data entry is a tuple containing:\n
            First entry - a pandas dataframe with MO as columns\n and AO as rows\n # noqa
            Second entry - a list of occupation numbers, one float per MO\n
            Third entry - a list of orbital energies, one float per MO
        '''
        return self._data

    @staticmethod
    def _process_block(block: str,
                       spin: str | None = 'UP') -> tuple[pd.DataFrame, list[float], list[float]]: # noqa
        '''
        Converts single block into data entries described in self.data

        Parameters
        ----------
        block: str
            String block extracted from file
        spin: str | None
            Spin to extract data for. Options are 'UP', 'DOWN', or None.\n
            Default is 'UP'.\n
            If 'DOWN' is selected, the spin down blocks will be extracted\n
            and the spin up blocks will be ignored.\n
            If None is selected, then only one block will be expected in the\n
            file, and the spin will be ignored (i.e. closed shell systems).\n

        Returns
        -------
        tuple[pd.DataFrame, list[float], list[float]]
            First entry - a pandas dataframe with MO as columns\n and AO as rows\n
            Second entry - a list of occupation numbers, one float per MO\n # noqa
            Third entry - a list of orbital energies, one float per MO
        '''
        # Remove first two lines from block
        block = '\n'.join(block.split('\n')[2:])

        if spin == 'UP':
            # Remove everything after the word SPIN DOWN
            block = block.split('SPIN DOWN')[0]
        elif spin == 'DOWN':
            # remove everything before the word SPIN DOWN
            block = block.split('SPIN DOWN')[1]
        elif spin is None:
            pass

        # Extract each <=5 orbital sub block
        # by splitting blocks separated by 2 or more newlines
        _patt = re.compile(
            r'\n{2,}'
        )
        _sub_blocks = _patt.split(block)
        _sub_blocks = [
            sb.lstrip().rstrip()
            for sb in _sub_blocks
            if len(sb.lstrip().rstrip())
        ]

        # and process into lists
        occupancies = []
        energies = []
        all_df = []

        # Extract each <=5 orbital sub block as a table
        # and append to list of table chunks
        for _sub_block in _sub_blocks:
            [_header, _, _table] = re.split(r'\s(:?--------\s+)+', _sub_block)

            _orb_nos = [
                int(val)
                for val in _header.split('\n')[0].split()
            ]

            _df = pd.read_csv(
                StringIO(_table), sep=r'\s+',
                header=None,
                engine='python',
                index_col=None
            )

            # Split first column into atom number and atom label
            _index_col = copy.copy(_df[0].str.split('[A-Za-z]'))
            _atomcol = _df[0].str.split('[0-9]+')

            # Change entries in dataframe to be cols of
            # atom number, atom label, and AO
            _df[0] = _index_col.str[0]
            _df.rename(columns={0: 'atom_number'}, inplace=True)
            _df.insert(1, 'atom_label', _atomcol.str[1])
            _df.rename(columns={1: 'AO'}, inplace=True)

            # Set these as the index cols
            _df.set_index(['atom_number', 'atom_label', 'AO'], inplace=True)

            # and title the rest with the orbital numbers
            _df.columns = _orb_nos

            # and append to the list of dataframes
            all_df.append(_df)

            # extract orbital energies
            for val in _header.split('\n')[1].split():
                energies.append(
                    float(val)
                )

            # extract orbital occupancies
            for val in _header.split('\n')[2].split():
                occupancies.append(
                    float(val)
                )

        # Combine list of dataframe chunks into a single dataframe
        combined_df = pd.concat(all_df, axis=1, join='outer')
        combined_df = combined_df.fillna(0)

        return combined_df, occupancies, energies

    @classmethod
    def extract(cls,
                file_name: str | pathlib.Path,
                spin: str | None = 'UP') -> list[tuple[pd.DataFrame, list[float], list[float]]]: # noqa
        '''
        Convenience method which instantiates class, extracts blocks, and
        returns processed datasets

        Parameters
        ----------
        file_name: str | pathlib.Path
            File to parse
        spin: str | None
            Spin to extract data for. Options are 'UP', 'DOWN', or None.\n
            Default is 'UP'.\n
            If 'DOWN' is selected, the spin down blocks will be extracted\n
            and the spin up blocks will be ignored.\n
            If None is selected, then only one block will be expected in the\n
            file, and the spin will be ignored (i.e. closed shell systems).\n

        Returns
        -------
        list[tuple[pd.DataFrame, list[float], list[float]]]
            Each entry contains processed data, as defined in cls.data
        '''
        _ext = cls()
        _ext(file_name, process=True, spin=spin)
        return _ext.data


class LoewdinReducedOrbitalPopulationExtractor(extto.BetweenExtractor):
    '''
    Extracts Reduced Loewdin Orbital-Populations Per MO Section from\n
    output file. ONLY READS SPIN UP BLOCKS\n
    '''

    # Regex Start Pattern
    START_PATTERN = rb'(?<=LOEWDIN REDUCED ORBITAL POPULATIONS PER MO\s-{43}\s)' # noqa

    # Regex End Pattern
    END_PATTERN = rb'(?=\*{3})'

    @property
    def data(self) -> tuple[pd.DataFrame, list[float], list[float]]: # noqa
        '''
        Processed Loewdin orbital data\n
        Each data entry is a tuple containing:\n
            First entry - a pandas dataframe with MO as columns\n and AO as rows\n
            Second entry - a list of occupation numbers, one float per MO\n # noqa
            Third entry - a list of orbital energies, one float per MO
        '''
        return self._data

    @staticmethod
    def _process_block(block: str,
                       spin: str | None = 'UP') -> tuple[pd.DataFrame, list[float], list[float]]: # noqa
        '''
        Converts single block into data entries described in self.data

        Parameters
        ----------
        block: str
            String block extracted from file
        spin: str | None
            Spin to extract data for. Options are 'UP', 'DOWN', or None.\n
            Default is 'UP'.\n
            If 'DOWN' is selected, the spin down blocks will be extracted\n
            and the spin up blocks will be ignored.\n
            If None is selected, then only one block will be expected in the\n
            file, and the spin will be ignored (i.e. closed shell systems).\n

        Returns
        -------
        tuple[pd.DataFrame, list[float], list[float]]
            First entry - a pandas dataframe with MO as columns\n and AO as rows\n # noqa
            Second entry - a list of occupation numbers, one float per MO\n
            Third entry - a list of orbital energies, one float per MO
        '''

        if spin == 'UP':
            # Remove everything after the word SPIN DOWN
            block = block.split('SPIN DOWN')[0]
            # and remove the word SPIN UP
            block = block.split('SPIN UP')[1]
        elif spin == 'DOWN':
            # remove everything before the word SPIN DOWN
            block = block.split('SPIN DOWN')[1]
            # and remove the word SPIN DOWN
            block = block.split('SPIN DOWN')[1]
        elif spin is None:
            pass

        # Remove threshold for printing line
        # using
        _patt = re.compile(r'THRESHOLD FOR PRINTING IS \d+\.\d%{1,}')
        block = _patt.sub('', block)

        # Extract each <=5 orbital sub block
        # by splitting blocks separated by 2 or more newlines
        _patt = re.compile(
            r'\n{2,}'
        )
        _sub_blocks = _patt.split(block)
        _sub_blocks = [
            sb.lstrip().rstrip()
            for sb in _sub_blocks
            if len(sb.lstrip().rstrip())
        ]

        # and process into lists
        occupancies = []
        energies = []
        all_df = []

        # Extract each <=5 orbital sub block as a table
        # and append to list of table chunks
        for _sub_block in _sub_blocks:
            [_header, _, _table] = re.split(r'\s(:?--------\s+)+', _sub_block)

            _orb_nos = [
                int(val)
                for val in _header.split('\n')[0].split()
            ]

            _df = pd.read_csv(
                StringIO(_table), sep=r'\s+',
                header=None,
                engine='python',
                index_col=None
            )

            # Change entries in dataframe to be cols of
            # atom number, atom label, and AO
            _df.rename(
                columns={
                    0: 'atom_number',
                    1: 'atom_label',
                    2: 'AO'
                },
                inplace=True
            )

            # Set these as the index cols
            _df.set_index(['atom_number', 'atom_label', 'AO'], inplace=True)

            # and title the rest with the orbital numbers
            _df.columns = _orb_nos

            # and append to the list of dataframes
            all_df.append(_df)

            # extract orbital energies
            for val in _header.split('\n')[1].split():
                energies.append(
                    float(val)
                )

            # extract orbital occupancies
            for val in _header.split('\n')[2].split():
                occupancies.append(
                    float(val)
                )

        # Combine list of dataframe chunks into a single dataframe
        combined_df = pd.concat(all_df, axis=1, join='outer')
        combined_df = combined_df.fillna(0)

        return combined_df, occupancies, energies

    @classmethod
    def extract(cls,
                file_name: str | pathlib.Path,
                spin: str | None = 'UP') -> list[tuple[pd.DataFrame, list[float], list[float]]]: # noqa
        '''
        Convenience method which instantiates class, extracts blocks, and
        returns processed datasets

        Parameters
        ----------
        file_name: str | pathlib.Path
            File to parse
        spin: str | None
            Spin to extract data for. Options are 'UP', 'DOWN', or None.\n
            Default is 'UP'.\n
            If 'DOWN' is selected, the spin down blocks will be extracted\n
            and the spin up blocks will be ignored.\n
            If None is selected, then only one block will be expected in the\n
            file, and the spin will be ignored (i.e. closed shell systems).\n

        Returns
        -------
        list[tuple[pd.DataFrame, list[float], list[float]]]
            Each entry contains processed data, as defined in cls.data
        '''
        _ext = cls()
        _ext(file_name, process=True, spin=spin)
        return _ext.data


class HessianExtractor(extto.BetweenExtractor):
    '''
    Extracts Hessian from .hess file
    '''

    # Modifiers for line/block extraction
    MODIFIERS = [re.MULTILINE]

    # Regex Start Pattern
    START_PATTERN = rb'(?<=\$hessian\n)'

    # Regex End Pattern
    END_PATTERN = rb'(?=^\s*$)'

    @property
    def data(self) -> list[NDArray]:
        '''
        Hessian matrix data, one matrix per block.\n
        Each matrix is a 3N x 3N ndarray of floats\n
        where N is the number of atoms
        '''
        return self._data

    @staticmethod
    def _process_block(block: str) -> NDArray:
        '''
        Converts single block into data entries described in self.data

        Parameters
        ----------
        block: str
            String block extracted from file

        Returns
        -------
        ndarray of floats
            Hessian matrix as 3N x 3N array of floats, where N is number of\n
            atoms
        '''

        # Extract each <=5 orbital sub block
        _patt = re.compile(
            r'(\s{15,}\d{1,4}){1,5}'
        )
        _sub_blocks = _patt.split(block)

        # Convert each {2,6} x 3N block into a list of floats and remove
        # row index
        _sub_blocks = [
            [
                [
                    float(val)
                    for it, val in enumerate(row.split())
                    if it
                ]
                for row in sb.lstrip().rstrip().split('\n')
                if len(row.split()) > 1
            ]
            for sb in _sub_blocks
            if len(sb.lstrip().rstrip().split('\n'))
        ]

        # Remove the empty lists
        _sub_blocks = [sb for sb in _sub_blocks if len(sb)]
        hessian = np.hstack(_sub_blocks, dtype=float)

        return hessian

    @classmethod
    def extract(cls, file_name: str | pathlib.Path) -> list[NDArray]:
        '''
        Convenience method which instantiates class, extracts blocks, and
        returns processed datasets

        Parameters
        ----------
        file_name: str | pathlib.Path
            File to parse

        Returns
        -------
        list[tuple[list[dict[str, float]], list[float]]]
            Each entry contains processed data, as defined in cls.data
        '''
        _ext = cls()
        _ext(file_name, process=True)
        return _ext.data


class AbsorptionExtractor(extto.BetweenExtractor):

    @property
    @abstractmethod
    def OPERATOR_TYPE() -> bytes:
        '''
        Name of operator type being extracted, e.g. 'Electric Dipole'
        '''
        raise NotImplementedError


class AbsorptionElectricDipoleExtractor(AbsorptionExtractor):
    '''
    Extracts ABSORPTION SPECTRUM VIA TRANSITION ELECTRIC DIPOLE MOMENTS table\n
    from ORCA output file for versions newer than 6.
    '''

    #: Operator Type
    OPERATOR_TYPE = 'Electric Dipole'

    # Regex Start Pattern
    START_PATTERN = rb'(?<=ABSORPTION SPECTRUM VIA TRANSITION ELECTRIC DIPOLE MOMENTS\s[\S\s]{408}\s)' # noqa

    # Regex End Pattern
    END_PATTERN = rb'(?=-{77})'

    @property
    def data(self) -> dict[str, list[str | float]]:
        '''
        Absorption spectrum data:\n
        A dictionary with keys:\n
            transition\n
            energy (cm^-1)\n
            energy (ev)\n
            wavelength (nm)\n
            fosc\n
            d2 (a.u.^2)\n
            dx (a.u.)\n
            dy (a.u.)\n
            dz (a.u.)\n
        All values are list[float], but 'transition' entries are list[str]
        '''
        return self._data

    @staticmethod
    def _process_block(block: str) -> dict[str, list[int | float]]: # noqa
        '''
        Converts single block into data entries described in self.data

        Parameters
        ----------
        block: str
            String block extracted from file

        Returns
        -------
        dict[str, list[float]]
        '''

        result = re.findall(
            r'\s+(\d+[A-Za-z]*-\d*[A-Za-z]\s+->\s+\d+[A-Za-z]*-\d*[A-Za-z])\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d\.\d{5})\s+(-*\d\.\d{5})\s+(-*\d\.\d{5})\s+(-*\d\.\d{5})', # noqa
            block
        )

        result = np.asarray(result, dtype=str).T

        fresult = result[1:].astype(float)

        data = {
            'state': result[0].tolist(),
            'energy (ev)': fresult[0].tolist(),
            'energy (cm^-1)': fresult[1].tolist(),
            'wavelength (nm)': fresult[2].tolist(),
            'fosc': fresult[3].tolist(),
            't2 (a.u.^2)': fresult[4].tolist(),
            'tx (a.u).': fresult[5].tolist(),
            'ty (a.u).': fresult[6].tolist(),
            'tz (a.u).': fresult[7].tolist()
        }

        return data

    @classmethod
    def extract(cls, file_name: str | pathlib.Path) -> dict[str, list[int | float]]: # noqa
        '''
        Convenience method which instantiates class, extracts blocks, and
        returns processed datasets

        Parameters
        ----------
        file_name: str | pathlib.Path
            File to parse

        Returns
        -------
        dict[str, list[int | float]]
            Each entry contains processed data, as defined in cls.data
        '''
        _ext = cls()
        _ext(file_name, process=True)
        return _ext.data


class AbsorptionVelocityDipoleExtractor(AbsorptionElectricDipoleExtractor):
    '''
    Extracts ABSORPTION SPECTRUM VIA TRANSITION VELOCITY DIPOLE MOMENTS table
    from ORCA output file for versions newer than 6.
    '''

    #: Operator Type
    OPERATOR_TYPE = 'Electric Dipole (Velocity)'

    # Regex Start Pattern
    START_PATTERN = rb'(?<=ABSORPTION SPECTRUM VIA TRANSITION VELOCITY DIPOLE MOMENTS\s[\S\s]{408}\s)' # noqa

    # Regex End Pattern
    END_PATTERN = rb'(?=-{77})'


class AbsorptionSemiClassicalDipoleExtractor(AbsorptionElectricDipoleExtractor): # noqa
    '''
    Extracts ABSORPTION SPECTRUM VIA FULL SEMI-CLASSICAL FORMULATION table
    from ORCA output file for versions newer than 6.
    '''

    #: Operator Type
    OPERATOR_TYPE = 'Semi-Classical'

    # Regex Start Pattern
    START_PATTERN = rb'(?<=ABSORPTION SPECTRUM VIA FULL SEMI-CLASSICAL FORMULATION\s[\S\s]{4}-{77}[\S\s]{206}\s)' # noqa

    # Regex End Pattern
    END_PATTERN = rb'(?=-{77})'

    @property
    def data(self) -> dict[str, list[str | float]]:
        '''
        Absorption spectrum data:\n
        A dictionary with keys:\n
            transition\n
            energy (cm^-1)\n
            energy (ev)\n
            wavelength (nm)\n
            fosc\n
        All values are list[float], but 'transition' entries are list[str]
        '''
        return self._data

    @staticmethod
    def _process_block(block: str) -> dict[str, list[int | float]]: # noqa
        '''
        Converts single block into data entries described in self.data

        Parameters
        ----------
        block: str
            String block extracted from file

        Returns
        -------
        dict[str, list[float]]
        '''

        result = re.findall(
            r'\s+(\d+[A-Za-z]*-\d*[A-Za-z]\s+->\s+\d+[A-Za-z]*-\d*[A-Za-z])\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)', # noqa
            block
        )

        result = np.asarray(result, dtype=str).T

        fresult = result[1:].astype(float)
        if not len(result):
            raise ValueError(
                'No data found in the block. Please check the output file.'
            )

        data = {
            'state': result[0].tolist(),
            'energy (ev)': fresult[0].tolist(),
            'energy (cm^-1)': fresult[1].tolist(),
            'wavelength (nm)': fresult[2].tolist(),
            'fosc': fresult[3].tolist(),
        }

        return data


class OldAbsorptionElectricDipoleExtractor(AbsorptionExtractor):
    '''
    Extracts ABSORPTION SPECTRUM VIA TRANSITION ELECTRIC DIPOLE MOMENTS table
    from ORCA output file for versions older than 6.
    '''

    #: Operator Type
    OPERATOR_TYPE = 'Electric Dipole (Old)'

    # Regex Start Pattern
    START_PATTERN = rb'(?<=ABSORPTION SPECTRUM VIA TRANSITION ELECTRIC DIPOLE MOMENTS\s[\S\s]{311}\s)' # noqa

    # Regex End Pattern
    END_PATTERN = rb'(?=-{77})'

    @property
    def data(self) -> dict[str, list[int | float]]:
        '''
        Absorption spectrum data:\n
        A dictionary with keys:\n
            state\n
            energy (cm^-1)\n
            energy (ev)\n
            wavelength (nm)\n
            fosc\n
            t2 (a.u.^2)\n
            tx (a.u.)\n
            ty (a.u.)\n
            tz (a.u.)\n
        All values are list[float], but 'state' entries are list[int]
        '''
        return self._data

    @staticmethod
    def _process_block(block: str) -> dict[str, list[int | float]]: # noqa
        '''
        Converts single block into data entries described in self.data

        Parameters
        ----------
        block: str
            String block extracted from file

        Returns
        -------
        dict[str, list[int | float]]
        '''

        result = re.findall(
            r'\s+(\d+)\s+(\d*\.\d)\s+(\d*\.\d)\s+(\d\.\d{9})\s+(\d\.\d{5})\s+(-*\d\.\d{5})\s+(-*\d\.\d{5})\s+(-*\d\.\d{5})', # noqa
            block
        )

        result = np.asarray(result, dtype=float).T

        data = {
            'state': result[0].tolist(),
            'energy (ev)': list(result[1] / const.EV_TO_WAVENUMBER),
            'energy (cm^-1)': result[1].tolist(),
            'wavelength (nm)': result[2].tolist(),
            'fosc': result[3].tolist(),
            't2 (a.u.^2)': result[4].tolist(),
            'tx (a.u).': result[5].tolist(),
            'ty (a.u).': result[6].tolist(),
            'tz (a.u).': result[7].tolist()
        }

        data['state'] = [int(s) for s in data['state']]
        return data

    @classmethod
    def extract(cls, file_name: str | pathlib.Path) -> dict[str, list[int | float]]: # noqa
        '''
        Convenience method which instantiates class, extracts blocks, and
        returns processed datasets

        Parameters
        ----------
        file_name: str | pathlib.Path
            File to parse

        Returns
        -------
        dict[str, list[int | float]]
            Each entry contains processed data, as defined in cls.data
        '''
        _ext = cls()
        _ext(file_name, process=True)
        return _ext.data


class XASElectricDipoleExtractor(AbsorptionExtractor):
    '''
    Extracts XAS SPECTRUM VIA TRANSITION ELECTRIC DIPOLE MOMENTS table\n
    from ORCA output file for versions newer than 6.
    '''

    #: Operator Type
    OPERATOR_TYPE = 'Electric Dipole'

    # Regex Start Pattern
    START_PATTERN = rb'(?<=ABSORPTION SPECTRUM VIA TRANSITION ELECTRIC DIPOLE MOMENTS\s[\S\s]{408}\s)' # noqa

    # Regex End Pattern
    END_PATTERN = rb'(?=-{77})'

    @property
    def data(self) -> dict[str, list[str | float]]:
        '''
        Absorption spectrum data:\n
        A dictionary with keys:\n
            transition\n
            energy (cm^-1)\n
            energy (ev)\n
            wavelength (nm)\n
            fosc\n
            d2 (a.u.^2)\n
            dx (a.u.)\n
            dy (a.u.)\n
            dz (a.u.)\n
        All values are list[float], but 'transition' entries are list[str]
        '''
        return self._data

    @staticmethod
    def _process_block(block: str) -> dict[str, list[int | float]]: # noqa
        '''
        Converts single block into data entries described in self.data

        Parameters
        ----------
        block: str
            String block extracted from file

        Returns
        -------
        dict[str, list[float]]
        '''

        result = re.findall(
            r'\s+(\d+[A-Za-z]*-\d*[A-Za-z]\s+->\s+\d+[A-Za-z]*-\d*[A-Za-z])\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d\.\d{5})\s+(-*\d\.\d{5})\s+(-*\d\.\d{5})\s+(-*\d\.\d{5})', # noqa
            block
        )

        result = np.asarray(result, dtype=str).T

        fresult = result[1:].astype(float)

        data = {
            'state': result[0].tolist(),
            'energy (ev)': fresult[0].tolist(),
            'energy (cm^-1)': fresult[1].tolist(),
            'wavelength (nm)': fresult[2].tolist(),
            'fosc': fresult[3].tolist(),
            't2 (a.u.^2)': fresult[4].tolist(),
            'tx (a.u).': fresult[5].tolist(),
            'ty (a.u).': fresult[6].tolist(),
            'tz (a.u).': fresult[7].tolist()
        }

        return data

    @classmethod
    def extract(cls, file_name: str | pathlib.Path) -> dict[str, list[int | float]]: # noqa
        '''
        Convenience method which instantiates class, extracts blocks, and
        returns processed datasets

        Parameters
        ----------
        file_name: str | pathlib.Path
            File to parse

        Returns
        -------
        dict[str, list[int | float]]
            Each entry contains processed data, as defined in cls.data
        '''
        _ext = cls()
        _ext(file_name, process=True)
        return _ext.data


class OldAbsorptionVelocityDipoleExtractor(OldAbsorptionElectricDipoleExtractor): # noqa
    '''
    Extracts ABSORPTION SPECTRUM VIA TRANSITION VELOCITY DIPOLE MOMENTS table
    from ORCA output file for versions older than 6.
    '''
    #: Operator Type
    OPERATOR_TYPE = 'Electric Dipole (Velocity, Old)'

    # Regex Start Pattern
    START_PATTERN = rb'(?<=ABSORPTION SPECTRUM VIA TRANSITION VELOCITY DIPOLE MOMENTS\s[\S\s]{311}\s)' # noqa

    # Regex End Pattern
    END_PATTERN = rb'(?=-{77})'


class XESElectricDipoleExtractor(AbsorptionElectricDipoleExtractor):
    '''
    Extracts X-RAY EMISSION SPECTRUM VIA TRANSITION ELECTRIC DIPOLE MOMENTS table\n # noqa
    from ORCA output file for versions newer than 6.
    '''

    #: Operator Type
    OPERATOR_TYPE = 'Electric Dipole'

    # Regex Start Pattern
    START_PATTERN = rb'(?<=              X-RAY   EMISSION SPECTRUM VIA TRANSITION VELOCITY DIPOLE MOMENTS\s[\S\s]{408}\s)' # noqa

    # Regex End Pattern
    END_PATTERN = rb'(?=-{77})'


class XESVelocityDipoleExtractor(AbsorptionElectricDipoleExtractor):
    '''
    Extracts X-RAY EMISSION SPECTRUM VIA TRANSITION VELOCITY DIPOLE MOMENTS table\n # noqa
    from ORCA output file for versions newer than 6.
    '''
    #: Operator Type
    OPERATOR_TYPE = 'Electric Dipole (Velocity)'

    # Regex Start Pattern
    START_PATTERN = rb'(?<=              X-RAY   EMISSION SPECTRUM VIA TRANSITION VELOCITY DIPOLE MOMENTS\s[\S\s]{415}\s)' # noqa


class SOXESElectricDipoleExtractor(XESElectricDipoleExtractor):
    '''
    Extracts SPIN-ORBIT X-RAY EMISSION SPECTRUM VIA TRANSITION ELECTRIC DIPOLE MOMENTS table\n # noqa
    from ORCA output file for versions newer than 6.
    '''

    #: Operator Type
    OPERATOR_TYPE = 'Electric Dipole'

    # Regex Start Pattern
    START_PATTERN = rb'(?<=SPIN-ORBIT X-RAY   EMISSION SPECTRUM VIA TRANSITION ELECTRIC DIPOLE MOMENTS\s[\S\s\(\)]{415}\s)' # noqa


class SOXESVelocityDipoleExtractor(XESVelocityDipoleExtractor):
    '''
    Extracts SPIN-ORBIT X-RAY EMISSION SPECTRUM VIA TRANSITION VELOCITY DIPOLE MOMENTS table\n # noqa
    from ORCA output file for versions newer than 6.
    ''' 

    #: Operator Type
    OPERATOR_TYPE = 'Electric Dipole (Velocity)'

    # Regex Start Pattern
    START_PATTERN = rb'(?<=   SPIN-ORBIT X-RAY   EMISSION SPECTRUM VIA TRANSITION VELOCITY DIPOLE MOMENTS\s[\S\s]{415}\s)' # noqa

    # Regex End Pattern
    END_PATTERN = rb'(?=-{104})'


class XESSemiClassicalDipoleExtractor(AbsorptionSemiClassicalDipoleExtractor):
    '''
    Extracts X-RAY EMISSION SPECTRUM VIA FULL SEMI-CLASSICAL FORMULATION table\n # noqa
    from ORCA output file for versions newer than 6.
    '''

    #: Operator Type
    OPERATOR_TYPE = 'Semi-Classical'

    # Regex Start Pattern
    START_PATTERN = rb'(?<=              X-RAY   EMISSION SPECTRUM VIA FULL SEMI-CLASSICAL FORMULATION\s[\S\s]{408}\s)' # noqa


class SOXESSemiClassicalDipoleExtractor(AbsorptionSemiClassicalDipoleExtractor): # noqa
    '''
    Extracts SPIN-ORBIT X-RAY EMISSION SPECTRUM VIA TRANSITION VELOCITY DIPOLE MOMENTS table\n # noqa
    from ORCA output file for versions newer than 6.
    '''

    #: Operator Type
    OPERATOR_TYPE = 'Semi-Classical'

    # Regex Start Pattern
    START_PATTERN = rb'(?<=   SPIN-ORBIT X-RAY   EMISSION SPECTRUM VIA FULL SEMI-CLASSICAL FORMULATION\s[\S\s]{408}\s)' # noqa


class HessNameInputExtractor(extto.LineExtractor):
    '''
    Extracts Hessian file name from %mtr block of input file
    '''

    # Regex pattern for line
    PATTERN = rb' *inhessname +"[A-Za-z\._0-9]*"'

    MODIFIERS = [re.IGNORECASE]

    @property
    def data(self) -> list[str]:
        '''
        Hessian file name. One entry per match
        '''
        return self._data

    @staticmethod
    def _process_block(block: str) -> str:
        '''
        Converts single block into data entries described in self.data

        Parameters
        ----------
        block: str
            String block extracted from file

        Returns
        -------
        str
            Hessian file name
        '''

        name = re.findall(r'"([A-Za-z\._0-9]*)"', block)[0]

        return name

    @classmethod
    def extract(cls, file_name: str | pathlib.Path) -> list[str]:
        '''
        Convenience method which instantiates class, extracts blocks, and
        returns processed datasets

        Parameters
        ----------
        file_name: str | pathlib.Path
            File to parse

        Returns
        -------
        list[str]
            Each entry contains processed data, as defined in cls.data
        '''
        _ext = cls()
        _ext(file_name, process=True)
        return _ext.data


class NProcsInputExtractor(extto.BetweenExtractor):
    '''
    Extracts Number of processors from input file
    '''
    # Regex Start Pattern
    START_PATTERN = rb'(?<=%PAL)'

    # Regex End Pattern
    END_PATTERN = rb'(?=END)'

    MODIFIERS = [re.IGNORECASE]

    @property
    def data(self) -> list[int]:
        '''
        Number of cores. One entry per match
        '''
        return self._data

    @staticmethod
    def _process_block(block: str) -> int:
        '''
        Converts single block into data entries described in self.data

        Parameters
        ----------
        block: str
            String block extracted from file

        Returns
        -------
        int
            Number of cores
        '''

        if block.count('%') > 1:
            raise DataFormattingError(
                '%pal block is malformed, perhaps missing END?'
            )

        n_cores = re.findall(r'(\d+)', block)[0]

        n_cores = int(n_cores)

        return n_cores

    @classmethod
    def extract(cls, file_name: str | pathlib.Path) -> list[int]:
        '''
        Convenience method which instantiates class, extracts blocks, and
        returns processed datasets

        Parameters
        ----------
        file_name: str | pathlib.Path
            File to parse

        Returns
        -------
        list[int]
            Each entry contains processed data, as defined in cls.data
        '''
        _ext = cls()
        _ext(file_name, process=True)
        return _ext.data


class MultiplicityInputExtractor(extto.LineExtractor):
    '''
    Extracts spin multiplicity from the following line of an input file

    *xyzfile charge multiplicity file_name
    '''

    # Regex pattern for line
    PATTERN = rb'\* *xyzfile *-?\d+ *\d+ *.*'

    MODIFIERS = [re.IGNORECASE]

    @property
    def data(self) -> list[int]:
        '''
        xyz file, one entry per match
        '''
        return self._data

    @staticmethod
    def _process_block(block: str) -> int:
        '''
        Converts single block into data entries described in self.data

        Parameters
        ----------
        block: str
            String block extracted from file

        Returns
        -------
        int
            Spin multiplicity (2S+1)
        '''

        mult = int(block.split()[-2])

        return mult

    @classmethod
    def extract(cls, file_name: str | pathlib.Path) -> list[int]:
        '''
        Convenience method which instantiates class, extracts blocks, and
        returns processed datasets

        Parameters
        ----------
        file_name: str | pathlib.Path
            File to parse

        Returns
        -------
        list[int]
            Each entry contains processed data, as defined in cls.data
        '''
        _ext = cls()
        _ext(file_name, process=True)
        return _ext.data


class XYZFileInputExtractor(extto.LineExtractor):
    '''
    Extracts .xyz file name from the following line of an input file

    *xyzfile charge multiplicity file_name
    '''

    # Regex pattern for line
    PATTERN = rb'\* *xyzfile *-?\d+ *\d+ *.*'

    MODIFIERS = [re.IGNORECASE]

    @property
    def data(self) -> list[str]:
        '''
        xyz file, one entry per match
        '''
        return self._data

    @staticmethod
    def _process_block(block: str) -> str:
        '''
        Converts single block into data entries described in self.data

        Parameters
        ----------
        block: str
            String block extracted from file

        Returns
        -------
        str
            xyz file name
        '''

        file = block.split()[-1]

        return file

    @classmethod
    def extract(cls, file_name: str | pathlib.Path) -> list[str]:
        '''
        Convenience method which instantiates class, extracts blocks, and
        returns processed datasets

        Parameters
        ----------
        file_name: str | pathlib.Path
            File to parse

        Returns
        -------
        list[str]
            Each entry contains processed data, as defined in cls.data
        '''
        _ext = cls()
        _ext(file_name, process=True)
        return _ext.data


class MOReadExtractor(extto.LineExtractor):
    '''
    Extracts lines containing MORead from input file

    This should (always) be the "simple input" line
    '''

    # Regex pattern for line
    PATTERN = rb'moread'

    MODIFIERS = [re.IGNORECASE]

    @property
    def data(self) -> list[str]:
        '''
        Line containing MORead, one entry per match
        '''
        return self._data

    @staticmethod
    def _process_block(block: str) -> str:
        '''
        Converts single block into data entries described in self.data

        Parameters
        ----------
        block: str
            String block extracted from file

        Returns
        -------
        str
            String block extracted from file
        '''

        return block

    @classmethod
    def extract(cls, file_name: str | pathlib.Path) -> list[str]:
        '''
        Convenience method which instantiates class, extracts blocks, and
        returns processed datasets

        Parameters
        ----------
        file_name: str | pathlib.Path
            File to parse

        Returns
        -------
        list[str]
            Each entry contains processed data, as defined in cls.data
        '''
        _ext = cls()
        _ext(file_name, process=True)
        return _ext.data


class MOInpExtractor(extto.LineExtractor):
    '''
    Extracts MOInp file from input file
    '''

    # Regex pattern for line
    PATTERN = rb'% *moinp *".*"'

    MODIFIERS = [re.IGNORECASE]

    @property
    def data(self) -> list[str]:
        '''
        Line containing input orbital file, one entry per match
        '''
        return self._data

    @staticmethod
    def _process_block(block: str) -> str:
        '''
        Converts single block into data entries described in self.data

        Parameters
        ----------
        block: str
            String block extracted from file

        Returns
        -------
        str
            String block extracted from file
        '''

        _ext = re.compile(r'"(.*\.*.*)"')

        data = _ext.findall(block)[0]

        return data

    @classmethod
    def extract(cls, file_name: str | pathlib.Path) -> list[str]:
        '''
        Convenience method which instantiates class, extracts blocks, and
        returns processed datasets

        Parameters
        ----------
        file_name: str | pathlib.Path
            File to parse

        Returns
        -------
        list[str]
            Each entry contains processed data, as defined in cls.data
        '''
        _ext = cls()
        _ext(file_name, process=True)

        return _ext.data


class XYZInputExtractor(extto.LineExtractor):
    '''
    Extracts *xyz line of an input file

    *xyz charge multiplicity
    '''

    # Regex pattern for line
    PATTERN = rb'\* *xyz *-?\d+ *\d'

    MODIFIERS = [re.IGNORECASE]

    @property
    def data(self) -> list[str]:
        '''
        *xyz line, one entry per match
        '''
        return self._data

    @staticmethod
    def _process_block(block: str) -> str:
        '''
        Converts single block into data entries described in self.data

        Parameters
        ----------
        block: str
            String block extracted from file

        Returns
        -------
        str
            String block extracted from file
        '''

        return block

    @classmethod
    def extract(cls, file_name: str | pathlib.Path) -> list[str]:
        '''
        Convenience method which instantiates class, extracts blocks, and
        returns processed datasets

        Parameters
        ----------
        file_name: str | pathlib.Path
            File to parse

        Returns
        -------
        list[str]
            Each entry contains processed data, as defined in cls.data
        '''
        _ext = cls()
        _ext(file_name, process=True)
        return _ext.data


class StructureInputExtractor(extto.BetweenExtractor):
    '''
    Extracts structure from xyz file
    '''

    # Regex Start Pattern
    START_PATTERN = rb'(?<=\*xyz )'

    # Regex End Pattern
    END_PATTERN = rb'(?=\*)'

    @property
    def data(self) -> tuple[list[str], NDArray]:
        '''
        list of atom labels and ndarray of coordinates (N, 3)
        '''
        return self._data

    @staticmethod
    def _process_block(block: str) -> tuple[list[str], NDArray]:
        '''
        Converts single block into data entries described in self.data

        Parameters
        ----------
        block: str
            String block extracted from file

        Returns
        -------
        tuple[list[str], NDArray]
        '''

        # Get labels and coordinates
        all_info = re.findall(
            r'([A-Za-z]+\s*-?\d\.\d*\s+-?\d\.\d*\s+-?\d\.\d*)',
            block
        )

        labels = re.findall(
            r'([A-Za-z]+)',
            block
        )

        coords = np.asarray([
            [float(v) for v in val.split()[1:]]
            for val in all_info
        ])

        if len(labels) != coords.shape[0]:
            raise DataFormattingError(
                'Number of atom labels does not match number of coordinates'
            )

        data = (labels, coords)

        return data

    @classmethod
    def extract(cls, file_name: str | pathlib.Path) -> tuple[list[str], NDArray]: # noqa
        '''
        Convenience method which instantiates class, extracts blocks, and
        returns processed datasets

        Parameters
        ----------
        file_name: str | pathlib.Path
            File to parse

        Returns
        -------
        tuple[list[str], NDArray]
            Each entry contains processed data, as defined in cls.data
        '''
        _ext = cls()
        _ext(file_name, process=True)
        return _ext.data


class IntInputExtractor(XYZInputExtractor):
    '''
    Extracts *int line of an input file

    *int charge multiplicity
    '''

    # Regex pattern for line
    PATTERN = rb'\* *int *-?\d+ *\d'

    MODIFIERS = [re.IGNORECASE]

    @property
    def data(self) -> list[str]:
        '''
        *int line, one entry per match
        '''
        return self._data


class MaxCoreInputExtractor(extto.LineExtractor):
    '''
    Extracts maxcore from input file\n
    i.e. the amount of memory allocated per core
    '''

    # Regex pattern for line
    PATTERN = rb'%maxcore +\d+'

    MODIFIERS = [re.IGNORECASE]

    @property
    def data(self) -> list[int]:
        '''
        Maxcore. One entry per match
        '''
        return self._data

    @staticmethod
    def _process_block(block: str) -> int:
        '''
        Converts single block into data entries described in self.data

        Parameters
        ----------
        block: str
            String block extracted from file

        Returns
        -------
        int
            Maxcore
        '''

        maxcore = re.findall(r'(\d+)', block)[0]

        maxcore = int(maxcore)

        return maxcore

    @classmethod
    def extract(cls, file_name: str | pathlib.Path) -> list[int]:
        '''
        Convenience method which instantiates class, extracts blocks, and\n
        returns processed datasets

        Parameters
        ----------
        file_name: str | pathlib.Path
            File to parse

        Returns
        -------
        list[int]
            Each entry contains processed data, as defined in cls.data
        '''
        _ext = cls()
        _ext(file_name, process=True)
        return _ext.data


class SimpleInputExtractor(extto.LineExtractor):
    '''
    Extracts simple input lines (lines beginning with !)
    from ORCA input file
    '''

    # Regex pattern for line
    PATTERN = rb'^ *!.*'

    MODIFIERS = [re.IGNORECASE, re.MULTILINE]

    @property
    def data(self) -> list[str]:
        '''
        Simple input lines (lines beginning with !). One entry per match
        '''
        return self._data

    @staticmethod
    def _process_block(block: str) -> int:
        '''
        Converts single block into data entries described in self.data

        Parameters
        ----------
        block: str
            String block extracted from file

        Returns
        -------
        str
            Simple input lines (lines beginning with !)
        '''

        return block

    @classmethod
    def extract(cls, file_name: str | pathlib.Path) -> list[int]:
        '''
        Convenience method which instantiates class, extracts blocks, and
        returns processed datasets

        Parameters
        ----------
        file_name: str | pathlib.Path
            File to parse

        Returns
        -------
        list[str]
            Each entry contains processed data, as defined in cls.data
        '''
        _ext = cls()
        _ext(file_name, process=True)
        return _ext.data


class HyperfineExtractor(extto.BetweenExtractor):
    '''
    Extracts Hyperfine coupling tensor and associated information from Orca\n
    output file
    '''

    # Regex Start Pattern
    START_PATTERN = rb'(?<=-{59}\s Nucleus)'

    # Regex End Pattern
    END_PATTERN = rb'(?=The A matrix conforms to the)'

    @property
    def data(self) -> dict[str, NDArray]:
        '''
        Hyperfine data:\n
        A dictionary with keys:\n
            nucleus\n
            element\n
            isotope\n
            matrix\n
            values\n
            vectors\n
            iso\n
            fc\n
            sd\n
            orb\n
            dia\n
        All values are ndarray of floats and have units of MHz
        '''
        return self._data

    @staticmethod
    def _process_block(block: str) -> dict[str, NDArray]:
        '''
        Converts single block into data entries described in self.data

        Parameters
        ----------
        block: str
            String block extracted from file

        Returns
        -------
        dict[str, NDArray]
        '''

        def float_triple(list_str: str) -> list[float]:
            '''
            Converts string form of three element list to list of floats

            list_str: str
                String of three float values separated by spaces

            Returns
            -------
            list[float]
                floats in list
            '''

            if list_str is None:
                list_float = []
            else:
                list_float = [
                    float(val)
                    for val in list_str.split()
                ]

            return list_float

        # Get Nucleus
        nucleus = block.split(':')[0].lstrip().rstrip()
        element = ''.join(
            [
                letter
                for letter in nucleus
                if letter not in '0123456789'
            ]
        )

        isotope = int(re.findall(r'Isotope\=\s+(\d+)', block)[0])

        # Get Matrix
        _matrix = re.findall(
            r'(\s-?\d+\.\d{4}\s+-?\d+\.\d{4}\s+-?\d+\.\d{4})',
            block
        )[:3]

        _fc = re.findall(
            r'A\(FC\)\s+(-?\d+.\d{4}\s+-?\d+.\d{4}\s+-?\d+.\d{4})',
            block
        )
        fc = float_triple(_fc[0])

        _sd = re.findall(
            r'A\(SD\)\s+(-?\d+.\d{4}\s+-?\d+.\d{4}\s+-?\d+.\d{4})',
            block
        )
        sd = float_triple(_sd[0])

        _orb = re.findall(
            r'A\(ORB\)\s+(-?\d+.\d{4}\s+-?\d+.\d{4}\s+-?\d+.\d{4})',
            block
        )
        orb = float_triple(_orb[0])

        _dia = re.findall(
            r'A\(DIA\)\s+(-?\d+.\d{4}\s+-?\d+.\d{4}\s+-?\d+.\d{4})',
            block
        )
        dia = float_triple(_dia[0])

        # Convert to matrix of floats
        matrix = np.asarray([
            [float(v) for v in val.split()]
            for val in _matrix
        ])

        if matrix.shape != (3, 3):
            raise DataFormattingError(
                'Hyperfine tensor is not the correct shape (3x3)'
            )

        # Calculate isotropic hyperfine coupling
        iso = np.trace(matrix) / 3.

        # Diagonalise tensor
        vals, vecs = la.eigh(matrix)

        # Future - pseudocontact/dipolar?
        data = {
            'nucleus': nucleus,
            'element': element,
            'isotope': isotope,
            'matrix': matrix,
            'values': vals,
            'vectors': vecs,
            'iso': iso,
            'fc': fc,
            'sd': sd,
            'dia': dia,
            'orb': orb,
        }

        return data

    @classmethod
    def extract(cls, file_name: str | pathlib.Path) -> list[dict[str, NDArray]]: # noqa
        '''
        Convenience method which instantiates class, extracts blocks, and
        returns processed datasets

        Parameters
        ----------
        file_name: str | pathlib.Path
            File to parse

        Returns
        -------
        list[dict[str, NDArray]]
            Each entry contains processed data, as defined in cls.data
        '''
        _ext = cls()
        _ext(file_name, process=True)
        return _ext.data


class GMatrixDFTExtractor(extto.BetweenExtractor):
    '''
    Extracts DFT ELECTRONIC G-MATRIX block from Orca output file
    '''

    # Regex Start Pattern
    START_PATTERN = rb'(?<=ELECTRONIC G-MATRIX\s[\S\s]{19}\s)'

    # Regex End Pattern
    END_PATTERN = rb'(?=EPR g-tensor done in)'

    @property
    def data(self) -> dict[str, NDArray]:
        '''
        G Matrix data:\n
        A dictionary with keys:\n
            matrix\n
            values\n
            vectors
        All values are ndarray of floats
        '''
        return self._data

    @staticmethod
    def _process_block(block: str) -> dict[str, NDArray]:
        '''
        Converts single block into data entries described in self.data

        Parameters
        ----------
        block: str
            String block extracted from file

        Returns
        -------
        dict[str, NDArray]
        '''

        # Trim block to lines after Orientation:

        block = block.split('The g-matrix:')[-1]

        # Get Matrix
        _matrix = re.findall(
            r'(\s-?\d\.\d{7}\s+-?\d\.\d{7}\s+-?\d\.\d{7})',
            block
        )[:3]

        # Convert to matrix of floats
        matrix = np.asarray([
            [float(v) for v in val.split()]
            for val in _matrix
        ])

        if matrix.shape != (3, 3):
            raise DataFormattingError(
                'G-matrix is not the correct shape (3x3)'
            )

        # Diagonalise g.g^T
        vals, vecs = la.eigh(matrix @ matrix.T)

        # get g values as sqrt of eigenvalues of g.g^T
        vals = np.sqrt(vals)

        data = {
            'matrix': matrix,
            'values': vals,
            'vectors': vecs
        }

        return data

    @classmethod
    def extract(cls, file_name: str | pathlib.Path) -> list[dict[str, NDArray]]: # noqa
        '''
        Convenience method which instantiates class, extracts blocks, and
        returns processed datasets

        Parameters
        ----------
        file_name: str | pathlib.Path
            File to parse

        Returns
        -------
        list[dict[str, NDArray]]
            Each entry contains processed data, as defined in cls.data
        '''
        _ext = cls()
        _ext(file_name, process=True)
        return _ext.data


class GMatrixExtractor(extto.BetweenExtractor):
    '''
    Extracts ELECTRONIC G-MATRIX block from Orca output file
    '''

    # Regex Start Pattern
    START_PATTERN = rb'(?<=ELECTRONIC G-MATRIX\s[\S\s]{20}\s)'

    # Regex End Pattern
    END_PATTERN = rb'(?=Tensor is right-handed)'

    @property
    def data(self) -> dict[str, NDArray]:
        '''
        G Matrix data:\n
        A dictionary with keys:\n
            matrix\n
            values\n
            vectors
        All values are ndarray of floats
        '''
        return self._data

    @staticmethod
    def _process_block(block: str) -> dict[str, NDArray]:
        '''
        Converts single block into data entries described in self.data

        Parameters
        ----------
        block: str
            String block extracted from file

        Returns
        -------
        dict[str, NDArray]
        '''

        # Get Matrix
        _matrix = re.findall(
            r'(\s-?\d\.\d{6}\s+-?\d\.\d{6}\s+-?\d\.\d{6})',
            block
        )[:3]

        # Convert to matrix of floats
        matrix = np.asarray([
            [float(v) for v in val.split()]
            for val in _matrix
        ])

        if matrix.shape != (3, 3):
            raise DataFormattingError(
                'G-matrix is not the correct shape (3x3)'
            )

        # Diagonalise g.g^T
        vals, vecs = la.eigh(matrix @ matrix.T)

        # get g values as sqrt of eigenvalues of g.g^T
        vals = np.sqrt(vals)

        data = {
            'matrix': matrix,
            'values': vals,
            'vectors': vecs
        }

        return data

    @classmethod
    def extract(cls, file_name: str | pathlib.Path) -> list[dict[str, NDArray]]: # noqa
        '''
        Convenience method which instantiates class, extracts blocks, and
        returns processed datasets

        Parameters
        ----------
        file_name: str | pathlib.Path
            File to parse

        Returns
        -------
        list[dict[str, NDArray]]
            Each entry contains processed data, as defined in cls.data
        '''
        _ext = cls()
        _ext(file_name, process=True)
        return _ext.data


class GMatrixEffectiveExtractor(GMatrixExtractor):
    '''
    Extracts ELECTRONIC G-MATRIX FROM EFFECTIVE HAMILTONIAN block from Orca\n
    output file
    '''
    # Regex Start Pattern
    START_PATTERN = rb'(?<=ELECTRONIC G-MATRIX FROM EFFECTIVE HAMILTONIAN\s[\S\s]{46}\s)' # noqa

    @property
    def data(self) -> dict[str, NDArray | int]:
        '''
        G Matrix data:\n
        A dictionary with keys:\n
            matrix\n
            values\n
            vectors\n
            spin_mult
        All values are ndarray of floats, other than spin_mult which is int
        '''
        return self._data

    @staticmethod
    def _process_block(block: str) -> dict[str, NDArray | int]:
        '''
        Converts single block into data entries described in self.data

        Parameters
        ----------
        block: str
            String block extracted from file

        Returns
        -------
        dict[str, NDArray | int]
        '''

        # Get spin multiplicity
        spin_mult = int(re.findall(r'Spin multiplicity = (\d*)', block)[0])

        # Get Matrix
        _matrix = re.findall(
            r'(\s-?\d\.\d{6}\s+-?\d\.\d{6}\s+-?\d\.\d{6})',
            block
        )[:3]

        # Convert to matrix of floats
        matrix = np.asarray([
            [float(v) for v in val.split()]
            for val in _matrix
        ])

        # Diagonalise g.g^T
        vals, vecs = la.eigh(matrix @ matrix.T)

        # get g values as sqrt of eigenvalues of g.g^T
        vals = np.sqrt(vals)

        data = {
            'matrix': matrix,
            'values': vals,
            'vectors': vecs,
            'spin_mult': spin_mult
        }

        return data

    @classmethod
    def extract(cls, file_name: str | pathlib.Path) -> list[dict[str, NDArray | int]]: # noqa
        '''
        Convenience method which instantiates class, extracts blocks, and
        returns processed datasets

        Parameters
        ----------
        file_name: str | pathlib.Path
            File to parse

        Returns
        -------
        list[dict[str, NDArray | int]]
            Each entry contains processed data, as defined in cls.data
        '''
        _ext = cls()
        _ext(file_name, process=True)
        return _ext.data


class GMatrixLExtractor(GMatrixExtractor):
    '''
    Extracts ELECTRONIC G-MATRIX: L contribution block from Orca\n
    output file
    '''
    # Regex Start Pattern
    START_PATTERN = rb'(?<=ELECTRONIC G-MATRIX: L contribution\s[\S\s]{47}\s)'


class GMatrixSExtractor(GMatrixExtractor):
    '''
    Extracts ELECTRONIC G-MATRIX: S contribution block from Orca\n
    output file
    '''
    # Regex Start Pattern
    START_PATTERN = rb'(?<=ELECTRONIC G-MATRIX: S contribution\s[\S\s]{47}\s)'


class SpinFreeEnergyExtractor(extto.BetweenExtractor):
    '''
    Extracts Spin-Free TRANSITION ENERGIES block from Orca output file
    '''

    # Regex Start Pattern
    START_PATTERN = rb'(?<= TRANSITION ENERGIES\s[\S\s]{30}\s)'

    # Regex End Pattern
    END_PATTERN = rb'(?=----)'

    @property
    def data(self) -> dict[str, NDArray]:
        '''
        State Energies:\n
        A dictionary with keys:\n
            root\n
            multiplicity\n
            energy (a.u.)\n
            delta energy (cm^-1)\n
        All values are ndarray of floats
        '''
        return self._data

    @staticmethod
    def _process_block(block: str) -> dict[str, NDArray]:
        '''
        Converts single block into data entries described in self.data

        Parameters
        ----------
        block: str
            String block extracted from file

        Returns
        -------
        dict[str, NDArray]
        '''

        # Get energy, root, and mult of lowest energy state
        s0e = float(re.findall(r'MULT \d*\) = \s+(-\d+\.\d+)', block)[0])
        s0r = int(re.findall(r'\(ROOT (\d*)', block)[0])
        s0m = int(re.findall(r'MULT (\d*)', block)[0])

        # Extract ROOT MULT and DE in atomic units
        result = re.findall(
            r'\s+(\d+)\s+(\d+)\s+(\d+\.\d{6})',
            block
        )
        result = np.asarray(result, dtype=str).T

        roots = [s0r] + result[0].astype(int).tolist()
        mults = [s0m] + result[1].astype(int).tolist()
        # Absolute energies in hartree
        energies = result[2].astype(float) + s0e
        energies = [s0e] + energies.tolist()

        # Calculate delta energies in cm-1
        denergies = result[2].astype(float) * 219474.63
        denergies = denergies.tolist()

        data = {
            'root': roots,
            'multiplicity': mults,
            'energy (a.u.)': energies,
            'delta energy (cm^-1)': denergies
        }

        return data

    @classmethod
    def extract(cls, file_name: str | pathlib.Path) -> list[dict[str, NDArray]]: # noqa
        '''
        Convenience method which instantiates class, extracts blocks, and
        returns processed datasets

        Parameters
        ----------
        file_name: str | pathlib.Path
            File to parse

        Returns
        -------
        list[dict[str, NDArray]]
            Each entry contains processed data, as defined in cls.data
        '''
        _ext = cls()
        _ext(file_name, process=True)
        return _ext.data


class SpinOrbitEnergyExtractor(extto.BetweenExtractor):
    '''
    Extracts Spin-Orbit Energies block from Orca output file
    '''

    # Regex Start Pattern
    START_PATTERN = rb'(?<=Lowest eigenvalue of the SOC matrix:)'

    # Regex End Pattern
    END_PATTERN = rb'(?=The threshold for printing is)'

    @property
    def data(self) -> NDArray:
        '''
        Difference in state energies relative to first state (0 Eh) as\n
        NDArray of floats
        '''
        return self._data

    @staticmethod
    def _process_block(block: str) -> NDArray:
        '''
        Converts single block into data entries described in self.data

        Parameters
        ----------
        block: str
            String block extracted from file

        Returns
        -------
        NDArray
        '''

        # Extract energies from table
        result = re.findall(
            r'\s+\d+:\s+(\d+\.\d{2})\s+\d+\.\d{4}\s+\d\.\d{2}e-+\d{2}',
            block
        )
        result = np.asarray(result, dtype=str).T.astype(float)

        return result

    @classmethod
    def extract(cls, file_name: str | pathlib.Path) -> list[dict[str, NDArray]]: # noqa
        '''
        Convenience method which instantiates class, extracts blocks, and
        returns processed datasets

        Parameters
        ----------
        file_name: str | pathlib.Path
            File to parse

        Returns
        -------
        list[dict[str, NDArray]]
            Each entry contains processed data, as defined in cls.data
        '''
        _ext = cls()
        _ext(file_name, process=True)
        return _ext.data
