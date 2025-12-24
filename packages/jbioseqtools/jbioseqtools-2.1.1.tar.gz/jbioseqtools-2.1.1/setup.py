from setuptools import setup, find_packages
from pathlib import Path

VERSION = '2.1.1' 
DESCRIPTION = 'jbioseqtools'
LONG_DESCRIPTION = Path("README.md").read_text(encoding="utf-8")

# Setting up
setup(
        name="jbioseqtools", 
        version=VERSION,
        author="Jakub Kubis",
        author_email="jbiosystem@gmail.com",
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        long_description_content_type="text/markdown",
        packages=['jbst'],
        include_package_data=True,
        install_requires=['setuptools', 'pandas', 'tqdm', 'matplotlib', 'numpy', 'requests', 'openpyxl', 'pymsaviz==0.4.2', 'ViennaRNA==2.6.4', 'biopython==1.81', 'networkx==3.1', 'seaborn', 'scipy', 'gdown==5.2.0'],       
        keywords=['sequence', 'optimization', 'vectors', 'AAV', 'GC', 'restriction enzyme', 'therapies', 'design','genetic'],
        license = 'MIT',
        classifiers = [
            "Development Status :: 3 - Alpha",
            "Programming Language :: Python :: 3",
            "Operating System :: MacOS :: MacOS X",
            "Operating System :: Microsoft :: Windows",
            "Operating System :: POSIX :: Linux",
        ],
        python_requires='>=3.8',
)


