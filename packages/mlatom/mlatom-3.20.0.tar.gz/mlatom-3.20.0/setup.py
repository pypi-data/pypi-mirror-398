from setuptools import setup, find_packages
from setuptools.command.install_scripts import install_scripts
from contextlib import suppress
from pathlib import Path
import os
import sys

pkg_name = "mlatom"
mlatom_script = 'mlatom'
site_pkg = ''
def modify_mlatom_script(script_path: str):
    global site_pkg
    for path in sys.path:
        with suppress(BaseException):
            for path_dir in os.listdir(path):
                if pkg_name in path_dir:
                    site_pkg = path
                    print(site_pkg)
    MLatom_py_file = os.path.join(site_pkg, pkg_name, 'MLatom.py')
    content = f"""#!/bin/bash
    export mlatom='{MLatom_py_file}'
    $mlatom "$@"
    """
    with open(script_path, 'w') as f:
        f.write(content)

def chmod_py(path):
    for py_file in Path(path).glob('*.py'):
        py_file.chmod(0o755)

class InstallScripts(install_scripts):
    def run(self):
        install_scripts.run(self)

        # Rename some script files
        for script in self.get_outputs():
            if script.endswith('mlatom'):
                modify_mlatom_script(script)

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md')) as f:
    README = f.read()

setup(
    name = pkg_name,
    version = "3.20.0",
    author = "Pavlo O. Dral",
    author_email = "admin@mlatom.com",
    license = 'MIT (modified)',
    description = "A Package for AI-enhanced computational chemistry",
    long_description = README,
    long_description_content_type = 'text/markdown',
    url = "http://mlatom.com",
    python_requires='>=3.8',
    packages = find_packages('src'),
    package_dir = {'' : 'src'},
    # scripts = ['mlatom', 'MLatomF'],
    package_data = {"": ['MLatomF', 'xtb', 'README', '*.json', '*.so', '*.cpp', '*.pt', '*.dat', '*.txt', '*.pkl', '*.inp', '*.f90', 'Makefile', 'Makefile.intel', '*.saved', '*.sh', '*.jl']},
    classifiers = [
        "Programming Language :: Python :: 3",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Fortran",
        "Topic :: Scientific/Engineering :: Chemistry",
        "Environment :: Console",
    ],
    install_requires = ['numpy', 'scipy', 'h5py', 'pyh5md', 'torch', 'torchani', 'matplotlib', 'statsmodels', 'tqdm'],
    # , 'pandas', '<scikit-learn> < <1.0.0>', 'xgboost', 'rdkit'
    entry_points = {
        'console_scripts' : ['mlatom-gui = mlatom.mlatom_gui:main',
                             'mlatom_gui = mlatom.mlatom_gui:main',
                             'mlatom = mlatom.shell_cmd:mlatom_cmd_run',
                             # 'MLatom.py = MLatom.shell_cmd:mlatom',
                             'MLatomF = mlatom.shell_cmd:MLatomF']
    }
    # cmdclass = {
    #     "install_scripts": InstallScripts
    # }
)

# bin_path = os.path.dirname(sys.executable)
# modify_mlatom_script(os.path.join(bin_path, mlatom_script))
# chmod_py(os.path.join(site_pkg, pkg_name))
