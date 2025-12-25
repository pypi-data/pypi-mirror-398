from pathlib import Path
import re
import numpy as np
import numpy.linalg as la
import copy
import xyz_py as xyzp

from .exceptions import DataNotFoundError, DataFormattingError
from . import extractor as oe
from . import utils as ut


def get_nbo(file_name: str | Path) -> bool:
    '''
    Check if NBO is present in the simple input line.\n

    Parameters
    ----------
    file_name: str | Path
        Orca input file as either name or Path object

    Returns
    -------
    bool
        True if NBO is present, False otherwise
    '''
    # Check for simple input line beginning with !
    try:
        simple = oe.SimpleInputExtractor.extract(file_name)
    except DataNotFoundError:
        ut.red_exit(
            'Error: Missing simple input line (or !) in input file'
        )
    # Check for NBO in simple input
    nbo_simple = re.findall(
        r'NBO',
        simple[0],
        flags=re.IGNORECASE
    )
    if len(nbo_simple):
        # Set to True if found
        if nbo_simple is None:
            _nbo = True
        else:
            _nbo = True
    else:
        _nbo = False

    return _nbo


def get_nprocs(file_name: str | Path) -> int:
    '''
    Get the number of processors from the input file.\n
    Either from the PAL keyword or the %PAL block.

    Parameters
    ----------
    file_name: str | Path
        Orca input file as either name or Path object

    Returns
    -------
    int
        Number of processors

    Raises
    ------
    DataNotFoundError
        If neither the PAL nor NProcs keyword is present in the input file
    DataFormattingError
        If both PAL and NProcs are present in the input file
    DataFormattingError
        If the PAL keyword is not a power of 2
    DataFormattingError
        If the %PAL block is malformed
    '''

    # Check for simple input line beginning with !
    try:
        simple = oe.SimpleInputExtractor.extract(file_name)
    except DataNotFoundError:
        ut.red_exit(
            'Error: Missing simple input line (or !) in input file'
        )

    # Check for PALX in simple input
    pal_simple = re.findall(
        r'PAL(\d+)',
        simple[0],
        flags=re.IGNORECASE
    )
    if len(pal_simple):
        # Set to zero if not found
        if pal_simple is None:
            _palprocs = 0
        else:
            _palprocs = int(pal_simple[0])
            # check if power of 2
            if not np.log2(_palprocs).is_integer():
                ut.red_exit(
                    'Error: For PAL<N>, <N> must be a power of 2'
                )
    else:
        _palprocs = 0

    # Check for %PAL block in input file
    try:
        n_procs = oe.NProcsInputExtractor.extract(file_name)[0]
    except DataNotFoundError:
        if _palprocs:
            n_procs = copy.copy(_palprocs)
            _palprocs = 0
        else:
            raise DataNotFoundError(
                f'Missing number of processors in {file_name}\n'
                'e.g. %pal nprocs 16 end'
            )
    except DataFormattingError:
        raise DataFormattingError(
            f'%PAL block is malformed, perhaps missing END?\n in {file_name}'
        )

    if n_procs and _palprocs:
        raise DataFormattingError(
            'Error: Both PAL and NProcs found in input file\n'
            f'PAL: {_palprocs}, NProcs: {n_procs}'
        )

    return n_procs


def get_maxcore(file_name: str | Path) -> int:
    '''
    Get the maximum core memory from the input file.\n

    Uses the %maxcore line.

    Parameters
    ----------
    file_name: str | Path
        Orca input file as either name or Path object

    Returns
    -------
    int
        Maximum core memory in MB

    Raises
    ------
    DataNotFoundError
        If %maxcore is not present in the input file
    '''

    # Load max core memory from input file
    try:
        maxcore = oe.MaxCoreInputExtractor.extract(file_name)[0]
    except DataNotFoundError:
        raise DataNotFoundError(
            f'Missing max core memory in {file_name}\n'
            'e.g. %maxcore 3000'
        )

    return maxcore


def check_coord(file_name: str | Path, skip_check) -> None:
    '''
    Check *xyz, *xyzfile, or *int line is present in input file.\n
    If xyzfile is given, then also checks if this exists and is formatted \n
    correctly.\n

    Parameters
    ----------
    file_name: str | Path
        Orca input file as either name or Path object
    skip_check: bool
        If True, skip the xyz file check

    Returns
    -------
    None

    Raises
    ------
    DataNotFoundError
        If neither *xyzfile, *xyz, nor *int are present in the input file
    DataFormattingError
        If xyz file is not formatted correctly
    '''

    # Get xyz file name and check it exists and is formatted correctly
    try:
        xyz_file = oe.XYZFileInputExtractor.extract(file_name)
    except DataNotFoundError:
        xyz_file = []

    try:
        xyzline = oe.XYZInputExtractor.extract(file_name)
    except DataNotFoundError:
        xyzline = []

    try:
        intline = oe.IntInputExtractor.extract(file_name)
    except DataNotFoundError:
        intline = []

    lens = [len(xyz_file), len(xyzline), len(intline)]

    if not sum(lens):
        ut.red_exit(
            'Error: missing or incorrect *xyzfile or *xyz line in input'
        )
    elif sum(lens) > 1:
        ut.red_exit(
            (
                'Error: multiple *xyzfile or *xyz lines in input.\n'
                'Only one can be present'
            )
        )

    if len(xyz_file):
        xyz_file = Path(xyz_file[0])
        if not xyz_file.is_file():
            ut.red_exit(
                'Error: xyz file specified in input cannot be found'
            )

        if not skip_check:
            try:
                xyzp.check_xyz(
                    xyz_file.absolute(),
                    allow_indices=False
                )
            except xyzp.XYZError as e:
                raise DataFormattingError(
                    f'{e}\n Use -sx to skip this check at your peril'
                )
    return


def check_xyz(file_name: str | Path, skip_check) -> None:
    '''
    Check *xyz or *xyzfile line is present in input file.\n
    If xyzfile is given, then also checks if this exists and is formatted \n
    correctly.\n

    Parameters
    ----------
    file_name: str | Path
        Orca input file as either name or Path object
    skip_check: bool
        If True, skip the xyz file check

    Returns
    -------
    None

    Raises
    ------
    DataNotFoundError
        If neither *xyzfile nor *xyz are present in the input file
    DataFormattingError
        If xyz file is not formatted correctly
    '''

    # Get xyz file name and check it exists and is formatted correctly
    try:
        xyz_file = oe.XYZFileInputExtractor.extract(file_name)
    except DataNotFoundError:
        xyz_file = []

    try:
        xyzline = oe.XYZInputExtractor.extract(file_name)
    except DataNotFoundError:
        xyzline = []

    if not len(xyz_file) and not len(xyzline):
        ut.red_exit(
            'Error: missing or incorrect *xyzfile or *xyz line in input'
        )

    if len(xyz_file) > 1 or len(xyzline) > 1 or len(xyz_file + xyzline) > 1: # noqa
        ut.red_exit(
            'Error: multiple *xyzfile or *xyz lines in input.\n Only one can be present' # noqa
        )

    if len(xyz_file):
        xyz_file = Path(xyz_file[0])
        if not xyz_file.is_file():
            ut.red_exit(
                'Error: xyz file specified in input cannot be found'
            )

        if not skip_check:
            try:
                xyzp.check_xyz(
                    xyz_file.absolute(),
                    allow_indices=False
                )
            except xyzp.XYZError as e:
                raise DataFormattingError(
                    f'{e}\n Use -sx to skip this check at your peril'
                )
    return


def check_structure(file_name: str | Path, threshold: float = 0.1) -> None:
    '''
    Checks that no atoms of the structure are overlapping.\n

    Parameters
    ----------
    file_name: str | Path
        Orca input file as either name or Path object
    threshold: float
        Minimum allowed distance between atoms in Angstroms

    Returns
    -------
    None

    Raises
    ------
    DataFormattingError
        If any atoms are overlapping
    '''

    # Get xyz file name and check it exists and is formatted correctly
    try:
        xyz_file = oe.XYZFileInputExtractor.extract(file_name)
    except DataNotFoundError:
        xyz_file = []

    try:
        xyzline = oe.XYZInputExtractor.extract(file_name)
    except DataNotFoundError:
        xyzline = []

    if not len(xyz_file) and not len(xyzline):
        ut.red_exit(
            'Error: missing or incorrect *xyzfile or *xyz line in input'
        )

    if len(xyz_file):
        # Load structure from xyz file
        xyz_file = Path(xyz_file[0])
        labels, coords = xyzp.load_xyz(xyz_file)
    else:
        # Extract structure from input file
        labels, coords = oe.StructureInputExtractor.extract(file_name)[0]

    # Compute pairwise differences using broadcasting
    # Broadcast to shape (N, N, 3)
    # from (N, 1, 3) and (1, N, 3)
    diffs = coords[:, np.newaxis, :] - coords[np.newaxis, :, :]

    # Compute Euclidean distances
    distances = la.norm(diffs, axis=-1)  # shape (N, N)

    # Add large value to diagonal to avoid zero self-distances
    distances += np.diag([100]*len(labels))
    # Find index of zero distances
    zero_dist = np.where(
        distances < threshold
    )
    # and report
    if len(zero_dist[0]):
        raise DataFormattingError(
            'Error: Overlapping atoms detected in structure'
            ' at atom numbers:\n' + ', '.join(
                str(i+1) for i in zero_dist[0]
            )
        )

    return


def check_moinp_moread(file_name: str | Path) -> None:
    '''
    Checks if MORead and/or MOInp are present in the input file.\n

    If so, check that the file exists, has a different stem from the input \n
    file, and has an extension.\n

    Parameters
    ----------
    file_name: str | Path
        Orca input file as either name or Path object

    Returns
    -------
    None

    Raises
    ------
    DataNotFoundError
        If only one of MORead and MOInp are present in the input file
    DataFormattingError
        If the stem of the input file and MOInp file are the same
    DataNotFoundError
        If the MOInp file cannot be found
    DataFormattingError
        If the MOInp file has no extension
    '''

    # Check if MORead and/or MOInp are present
    try:
        moread = oe.MOReadExtractor.extract(file_name)
    except DataNotFoundError:
        moread = []
    try:
        moinp = oe.MOInpExtractor.extract(file_name)
    except DataNotFoundError:
        moinp = []

    # Error if only one word present or if more than one of each word
    if len(moinp) ^ len(moread):
        raise DataFormattingError('Error: Missing one of MOInp or MORead')
    if len(moinp) + len(moread) > 2:
        raise DataFormattingError(
            'Error: Multiple MORead and/or MOInp detected'
        )

    if len(moinp):
        # Error if input orbitals have same stem as input file
        moinp = Path(moinp[0])
        if moinp.stem == file_name.stem:
            raise DataFormattingError(
                'Error: Stem of orbital and input files cannot match'
            )

        # Error if cannot find orbital file
        if not moinp.suffix:
            raise DataFormattingError(
                f'Error: Orbital file {moinp} has no extension'
            )
        if not moinp.exists():
            raise DataFormattingError(
                f'Error: Orbital file {moinp} cannot be found'
            )

    return None
