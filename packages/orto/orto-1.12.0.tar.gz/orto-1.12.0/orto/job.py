import subto.job as sjob
import copy
import pathlib


class OrcaJob():
    '''
    Class to generate submission scripts for ORCA calculation\n\n

    Submission script format is \n

    ...............\n
    SCHEDULER BLOCK\n
    ...............\n
    LOAD_BLOCK\n
    ...............\n
    PRE-ORCA_BLOCK\n
    ...............\n
    $(which orca) input_file > output_file\n
    ...............\n
    POST-ORCA_BLOCK\n
    ...............\n

    Attributes
    ----------
    input_file: pathlib.Path
        Orca input file for which a submission script is created
    output_file: pathlib.Path
        Orca output file name. Default is same as input with extension \n
        replaced by .out
    job_file: pathlib.Path
        Submission script file path. Default is same as input with extension \n
        replaced by scheduler job file extension e.g. '.slm'
    job_name: str
        Job name. Default is same as input without extension
    scheduler_name: str {'slurm'}
        Scheduler system name
    pre_orca: str
        Commands for pre-orca block
    post_orca: str
        Commands for post-orca block
    '''

    SUPPORTED_SCHEDULERS = [
        sjob.SlurmJob
    ]

    def __init__(self, input_file: str | pathlib.Path,
                 Job: sjob.Job = sjob.SlurmJob, **kwargs) -> None:

        self.input_file = input_file
        self.Job = Job

        # Set defaults
        self.output_file = self.input_file.with_suffix('.out')
        self.job_file = self.input_file.with_suffix(self.Job.EXTENSION)

        self.job_name = copy.copy(self.input_file.stem)
        self.load = ''
        self.pre_orca = ''
        self.post_orca = ''

        # If provided set attrs using kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)
        return

    @property
    def input_file(self) -> pathlib.Path:
        return self._input_file

    @input_file.setter
    def input_file(self, value: str | pathlib.Path):
        if isinstance(value, str):
            self._input_file = pathlib.Path(value).resolve()
        elif isinstance(value, pathlib.Path):
            self._input_file = value.resolve()
        else:
            raise TypeError('input_file should be of type str or Path')
        return

    @property
    def input_file_relpath(self) -> pathlib.Path:
        return self.input_file.relative_to(pathlib.Path.cwd())

    @property
    def output_file(self) -> pathlib.Path:
        return self._output_file

    @output_file.setter
    def output_file(self, value: str | pathlib.Path):
        if isinstance(value, str):
            self._output_file = pathlib.Path(value).resolve()
        elif isinstance(value, pathlib.Path):
            self._output_file = value.resolve()
        else:
            raise TypeError('output_file should be of type str or Path')
        return

    @property
    def job_file(self) -> pathlib.Path:
        '''
        The submission script file path
        '''
        return self._job_file

    @job_file.setter
    def job_file(self, value: str | pathlib.Path):
        if isinstance(value, str):
            self._job_file = pathlib.Path(value).resolve()
        elif isinstance(value, pathlib.Path):
            self._job_file = value.resolve()
        else:
            raise TypeError('job_file should be of type str or Path')
        return

    @property
    def output_file_relpath(self) -> pathlib.Path:
        return self.output_file.relative_to(pathlib.Path.cwd())

    @property
    def Job(self) -> sjob.Job:
        return self._Job

    @Job.setter
    def Job(self, value: sjob.Job):
        if value not in self.SUPPORTED_SCHEDULERS:
            raise ValueError('Unsupported Job Class provided to OrcaJob')
        else:
            self._Job = value
        return

    @property
    def pre_orca(self):
        rvalue = copy.copy(self._pre_orca)
        rvalue = rvalue.replace('<input>', self.input_file.name)
        rvalue = rvalue.replace('<output>', self.output_file.name)
        rvalue = rvalue.replace('<stem>', self.input_file.stem)
        return rvalue

    @pre_orca.setter
    def pre_orca(self, value: str):
        self._pre_orca = value

    @property
    def post_orca(self):
        rvalue = copy.copy(self._post_orca)
        rvalue = rvalue.replace('<input>', self.input_file.name)
        rvalue = rvalue.replace('<output>', self.output_file.name)
        rvalue = rvalue.replace('<stem>', self.input_file.stem)
        return rvalue

    @post_orca.setter
    def post_orca(self, value: str):
        self._post_orca = value

    @property
    def orca_command(self):
        return f'$(which orca) {self.input_file.name} >> {self.output_file.name}' # noqa

    def write_script(self, verbose: bool = True, **kwargs) -> None:
        '''
        Writes submission script to file

        Parameters
        ----------
        verbose: bool, default True
            If True, jobscript location is written to screen
        **kwargs
            Keyword arguments passed to `subto.job.Job` constructor
        '''

        if len(self.load):
            self.load += '\n\n'
        if len(self.pre_orca):
            self.pre_orca += '\n\n'
        if len(self.post_orca):
            self.post_orca = '\n' + self.post_orca + '\n\n'

        self.pre_orca += f'\ndate > {self.output_file.name}\n'
        self.pre_orca += f'hostname >> {self.output_file.name}\n\n'

        # Generate content of script
        content = '{}{}{}\n{}'.format(
            self.load,
            self.pre_orca,
            self.orca_command,
            self.post_orca
        )

        # And use scheduler object to submission system job object
        job = self.Job(
            file=self.job_file,
            job_name=self.job_name,
            content_block=content,
            **kwargs
        )

        # Write script
        job.write_script(verbose=verbose)

        return
