import setuptools

long_description = '''
`orto` is a package to make life easier when performing Orca calculations.\n\n

Please see the `orto` documentation for more details.
'''

# DO NOT EDIT THIS NUMBER!
# IT IS AUTOMATICALLY CHANGED BY python-semantic-release
__version__ = '1.12.0'

setuptools.setup(
    name='orto',
    version=__version__,
    author='Jon Kragskow',
    author_email='jgck20@bath.ac.uk',
    description='A package to make life easier when performing Orca calculations.', # noqa
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://orto.kragskow.group',
    project_urls={
        'Bug Tracker': 'https://gitlab.com/kragskow-group/orto/issues',
        'Documentation': 'https://orto.kragskow.group'
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
    ],
    package_dir={'': '.'},
    packages=setuptools.find_packages(),
    python_requires='>=3.10',
    install_requires=[
        'numpy>=2.1.2',
        'xyz_py>=5.19.2',
        'matplotlib>=3.9.2',
        'extto>=1.0.1',
        'pandas>=2.2.3',
        'subto>=0.1.1',
        'python-docx>=1.1.2'
    ],
    entry_points={
        'console_scripts': [
            'orto = orto.cli:main',
        ]
    }
)
